"""
Request processor for LLM inference.

Handles batching, processing, and response generation for inference requests.
"""
import logging
import asyncio
import uuid
import time
from typing import Dict, Any, List, Optional
from collections import deque
from worker.models.llm_model import LLMModel
from worker.kafka.producer import KafkaResponseProducer
from worker.metrics.prometheus_metrics import metrics

logger = logging.getLogger(__name__)


class RequestProcessor:
    """
    Processes inference requests with batching support.
    
    Collects requests into batches, processes them through the model,
    and produces responses to Kafka.
    """
    
    def __init__(
        self,
        model: LLMModel,
        producer: KafkaResponseProducer,
        batch_size: int = 4,
        batch_timeout: float = 0.1,
        max_concurrent: int = 10
    ):
        """
        Initialize request processor.
        
        Args:
            model: LLM model instance
            producer: Kafka response producer
            batch_size: Maximum batch size
            batch_timeout: Timeout for batching (seconds)
            max_concurrent: Maximum concurrent requests
        """
        self.model = model
        self.producer = producer
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_concurrent = max_concurrent
        
        self.request_queue = deque()
        self.processing = False
        self.active_requests = 0
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        logger.info(f"Request processor initialized: batch_size={batch_size}, max_concurrent={max_concurrent}")
    
    async def process_request(self, request: Dict[str, Any]) -> None:
        """
        Process a single inference request.
        
        Args:
            request: Request dictionary with prompt and metadata
        """
        request_id = request.get('request_id') or str(uuid.uuid4())
        prompt = request.get('prompt', '')
        kafka_metadata = request.get('_kafka_metadata', {})
        
        if not prompt:
            logger.warning(f"Empty prompt in request {request_id}")
            await self._send_error_response(
                request_id,
                "Empty prompt provided",
                kafka_metadata
            )
            return
        
        # Track request start time
        request_start_time = time.time()
        kafka_receive_time = kafka_metadata.get('timestamp', [request_start_time * 1000])[1] / 1000.0 if isinstance(kafka_metadata.get('timestamp'), list) else request_start_time
        
        async with self.semaphore:
            self.active_requests += 1
            metrics.set_active_requests(self.active_requests)
            
            try:
                logger.info(f"Processing request {request_id}: prompt_length={len(prompt)}")
                
                # Generate response
                inference_start = time.time()
                result = self.model.generate(
                    prompt=prompt,
                    max_new_tokens=request.get('max_new_tokens'),
                    temperature=request.get('temperature'),
                    top_p=request.get('top_p'),
                    do_sample=request.get('do_sample')
                )
                inference_duration = time.time() - inference_start
                
                # Record metrics
                total_duration = time.time() - request_start_time
                latency = time.time() - kafka_receive_time
                
                metrics.record_request('success', total_duration, latency)
                metrics.record_model_inference(inference_duration, 1)
                
                if 'output_length' in result:
                    metrics.record_tokens(result['output_length'], inference_duration)
                
                # Send response
                response = {
                    'request_id': request_id,
                    'status': 'success',
                    'text': result['text'],
                    'metadata': {
                        'input_length': result.get('input_length', 0),
                        'output_length': result.get('output_length', 0),
                        'generation_time': result.get('generation_time', inference_duration),
                        'total_time': total_duration
                    },
                    'timestamp': time.time()
                }
                
                await self._send_response(response, kafka_metadata)
                metrics.record_kafka_produce()
                
                logger.info(
                    f"Request {request_id} completed: "
                    f"duration={total_duration:.2f}s, "
                    f"tokens={result.get('output_length', 0)}"
                )
            
            except Exception as e:
                logger.error(f"Error processing request {request_id}: {e}", exc_info=True)
                
                total_duration = time.time() - request_start_time
                metrics.record_request('error', total_duration)
                
                await self._send_error_response(
                    request_id,
                    str(e),
                    kafka_metadata
                )
            
            finally:
                self.active_requests -= 1
                metrics.set_active_requests(self.active_requests)
    
    async def process_batch(self, requests: List[Dict[str, Any]]) -> None:
        """
        Process a batch of requests.
        
        Args:
            requests: List of request dictionaries
        """
        if not requests:
            return
        
        batch_start_time = time.time()
        logger.info(f"Processing batch of {len(requests)} requests")
        
        try:
            # Extract prompts and metadata
            prompts = [req.get('prompt', '') for req in requests]
            request_ids = [req.get('request_id') or str(uuid.uuid4()) for req in requests]
            kafka_metadata_list = [req.get('_kafka_metadata', {}) for req in requests]
            
            # Generate batch
            inference_start = time.time()
            results = self.model.generate_batch(
                prompts=prompts,
                max_new_tokens=requests[0].get('max_new_tokens') if requests else None
            )
            inference_duration = time.time() - inference_start
            
            # Record metrics
            metrics.record_model_inference(inference_duration, len(requests))
            
            total_tokens = sum(r.get('output_length', 0) for r in results)
            if total_tokens > 0:
                metrics.record_tokens(total_tokens, inference_duration)
            
            # Send responses
            for i, (request_id, result, kafka_metadata) in enumerate(zip(request_ids, results, kafka_metadata_list)):
                total_duration = time.time() - batch_start_time
                metrics.record_request('success', total_duration)
                
                response = {
                    'request_id': request_id,
                    'status': 'success',
                    'text': result['text'],
                    'metadata': {
                        'input_length': result.get('input_length', 0),
                        'output_length': result.get('output_length', 0),
                        'generation_time': inference_duration / len(requests),
                        'total_time': total_duration
                    },
                    'timestamp': time.time()
                }
                
                await self._send_response(response, kafka_metadata)
                metrics.record_kafka_produce()
            
            batch_duration = time.time() - batch_start_time
            logger.info(f"Batch completed: {len(requests)} requests in {batch_duration:.2f}s")
        
        except Exception as e:
            logger.error(f"Error processing batch: {e}", exc_info=True)
            
            # Send error responses for all requests in batch
            for req in requests:
                request_id = req.get('request_id') or str(uuid.uuid4())
                await self._send_error_response(
                    request_id,
                    str(e),
                    req.get('_kafka_metadata', {})
                )
    
    async def _send_response(self, response: Dict[str, Any], kafka_metadata: Dict[str, Any]) -> None:
        """
        Send response to Kafka.
        
        Args:
            response: Response dictionary
            kafka_metadata: Original Kafka message metadata
        """
        try:
            # Use request_id as key for partitioning
            key = response.get('request_id')
            
            # Produce to Kafka (synchronous in async context)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.producer.produce,
                response,
                key
            )
        
        except Exception as e:
            logger.error(f"Failed to send response: {e}", exc_info=True)
            metrics.record_kafka_producer_error()
    
    async def _send_error_response(
        self,
        request_id: str,
        error_message: str,
        kafka_metadata: Dict[str, Any]
    ) -> None:
        """
        Send error response to Kafka.
        
        Args:
            request_id: Request identifier
            error_message: Error message
            kafka_metadata: Original Kafka message metadata
        """
        response = {
            'request_id': request_id,
            'status': 'error',
            'error': error_message,
            'timestamp': time.time()
        }
        
        await self._send_response(response, kafka_metadata)
        metrics.record_kafka_produce()
