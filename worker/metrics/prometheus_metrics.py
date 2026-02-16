"""
Prometheus metrics for LLM Worker Service.

Exposes metrics for:
- Request latency
- Token generation rate
- Kafka lag
- Error rates
- Model inference metrics
"""
import time
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
import logging

logger = logging.getLogger(__name__)


class WorkerMetrics:
    """
    Prometheus metrics collector for LLM worker.
    
    Tracks key performance indicators and system health metrics.
    """
    
    def __init__(self):
        """Initialize metrics."""
        # Request metrics
        self.requests_total = Counter(
            'llm_worker_requests_total',
            'Total number of inference requests',
            ['status']  # success, error, timeout
        )
        
        self.request_duration = Histogram(
            'llm_worker_request_duration_seconds',
            'Request processing duration in seconds',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
        )
        
        self.request_latency = Histogram(
            'llm_worker_request_latency_seconds',
            'End-to-end request latency (from Kafka receive to send)',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
        )
        
        # Token generation metrics
        self.tokens_generated_total = Counter(
            'llm_worker_tokens_generated_total',
            'Total number of tokens generated'
        )
        
        self.tokens_per_second = Histogram(
            'llm_worker_tokens_per_second',
            'Token generation rate (tokens/second)',
            buckets=[1, 5, 10, 20, 50, 100, 200, 500, 1000]
        )
        
        # Kafka metrics
        self.kafka_messages_consumed = Counter(
            'llm_worker_kafka_messages_consumed_total',
            'Total number of Kafka messages consumed'
        )
        
        self.kafka_messages_produced = Counter(
            'llm_worker_kafka_messages_produced_total',
            'Total number of Kafka messages produced'
        )
        
        self.kafka_consumer_lag = Gauge(
            'llm_worker_kafka_consumer_lag',
            'Kafka consumer lag per partition',
            ['partition']
        )
        
        self.kafka_consumer_errors = Counter(
            'llm_worker_kafka_consumer_errors_total',
            'Total number of Kafka consumer errors'
        )
        
        self.kafka_producer_errors = Counter(
            'llm_worker_kafka_producer_errors_total',
            'Total number of Kafka producer errors'
        )
        
        # Model metrics
        self.model_inference_duration = Histogram(
            'llm_worker_model_inference_duration_seconds',
            'Model inference duration in seconds',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.model_batch_size = Histogram(
            'llm_worker_model_batch_size',
            'Batch size for model inference',
            buckets=[1, 2, 4, 8, 16, 32, 64]
        )
        
        # System metrics
        self.active_requests = Gauge(
            'llm_worker_active_requests',
            'Number of currently active inference requests'
        )
        
        self.worker_info = Info(
            'llm_worker_info',
            'Worker instance information'
        )
        
        logger.info("Prometheus metrics initialized")
    
    def record_request(self, status: str, duration: float, latency: Optional[float] = None):
        """
        Record a request metric.
        
        Args:
            status: Request status (success, error, timeout)
            duration: Request processing duration in seconds
            latency: End-to-end latency in seconds (optional)
        """
        self.requests_total.labels(status=status).inc()
        self.request_duration.observe(duration)
        
        if latency is not None:
            self.request_latency.observe(latency)
    
    def record_tokens(self, token_count: int, generation_time: float):
        """
        Record token generation metrics.
        
        Args:
            token_count: Number of tokens generated
            generation_time: Time taken to generate tokens in seconds
        """
        self.tokens_generated_total.inc(token_count)
        
        if generation_time > 0:
            tokens_per_sec = token_count / generation_time
            self.tokens_per_second.observe(tokens_per_sec)
    
    def record_kafka_consume(self):
        """Record a Kafka message consumption."""
        self.kafka_messages_consumed.inc()
    
    def record_kafka_produce(self):
        """Record a Kafka message production."""
        self.kafka_messages_produced.inc()
    
    def record_kafka_consumer_error(self):
        """Record a Kafka consumer error."""
        self.kafka_consumer_errors.inc()
    
    def record_kafka_producer_error(self):
        """Record a Kafka producer error."""
        self.kafka_producer_errors.inc()
    
    def update_consumer_lag(self, partition: str, lag: int):
        """
        Update Kafka consumer lag for a partition.
        
        Args:
            partition: Partition identifier
            lag: Lag value
        """
        self.kafka_consumer_lag.labels(partition=partition).set(lag)
    
    def record_model_inference(self, duration: float, batch_size: int):
        """
        Record model inference metrics.
        
        Args:
            duration: Inference duration in seconds
            batch_size: Batch size used
        """
        self.model_inference_duration.observe(duration)
        self.model_batch_size.observe(batch_size)
    
    def set_active_requests(self, count: int):
        """
        Update active requests count.
        
        Args:
            count: Number of active requests
        """
        self.active_requests.set(count)
    
    def set_worker_info(self, worker_id: str, model_name: str):
        """
        Set worker information.
        
        Args:
            worker_id: Worker instance ID
            model_name: Model name
        """
        self.worker_info.info({
            'worker_id': worker_id,
            'model_name': model_name
        })
    
    def start_metrics_server(self, port: int = 8080):
        """
        Start HTTP server for Prometheus metrics.
        
        Args:
            port: Port to serve metrics on
        """
        try:
            start_http_server(port)
            logger.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}", exc_info=True)
            raise


# Global metrics instance
metrics = WorkerMetrics()
