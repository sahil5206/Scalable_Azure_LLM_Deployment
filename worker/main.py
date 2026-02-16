"""
Main entry point for LLM Worker Service.

Initializes and runs the worker service with Kafka integration,
model loading, and metrics collection.
"""
import asyncio
import logging
import signal
import sys
import uuid
from typing import Optional, Dict, Any, Callable
from worker.config import config
from worker.models.llm_model import LLMModel
from worker.kafka.consumer import KafkaRequestConsumer
from worker.kafka.producer import KafkaResponseProducer
from worker.processor import RequestProcessor
from worker.metrics.prometheus_metrics import metrics
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configure standard logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class LLMWorkerService:
    """
    Main LLM Worker Service.
    
    Orchestrates model loading, Kafka integration, and request processing.
    """
    
    def __init__(self):
        """Initialize worker service."""
        self.worker_id = config.worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.model: Optional[LLMModel] = None
        self.consumer: Optional[KafkaRequestConsumer] = None
        self.producer: Optional[KafkaResponseProducer] = None
        self.processor: Optional[RequestProcessor] = None
        self.running = False
        
        logger.info(f"Initializing LLM Worker Service: {self.worker_id}")
        logger.info(f"Configuration: model={config.model_name}, batch_size={config.batch_size}")
    
    async def initialize(self):
        """Initialize all components."""
        try:
            # Load model
            logger.info("Loading LLM model...")
            self.model = LLMModel(
                model_name=config.model_name,
                device=config.model_device,
                dtype=config.model_dtype,
                max_sequence_length=config.max_sequence_length,
                max_new_tokens=config.max_new_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                do_sample=config.do_sample
            )
            
            model_info = self.model.get_model_info()
            logger.info(f"Model loaded: {model_info}")
            
            # Initialize Kafka producer
            logger.info("Initializing Kafka producer...")
            self.producer = KafkaResponseProducer(
                bootstrap_servers=config.kafka_bootstrap_servers,
                topic=config.kafka_response_topic
            )
            
            # Initialize Kafka consumer
            logger.info("Initializing Kafka consumer...")
            self.consumer = KafkaRequestConsumer(
                bootstrap_servers=config.kafka_bootstrap_servers,
                topic=config.kafka_request_topic,
                group_id=config.kafka_consumer_group,
                auto_offset_reset=config.kafka_auto_offset_reset,
                enable_auto_commit=config.kafka_enable_auto_commit,
                max_poll_records=config.kafka_max_poll_records,
                session_timeout_ms=config.kafka_session_timeout_ms
            )
            
            # Initialize request processor
            logger.info("Initializing request processor...")
            self.processor = RequestProcessor(
                model=self.model,
                producer=self.producer,
                batch_size=config.batch_size,
                batch_timeout=config.batch_timeout_seconds,
                max_concurrent=config.max_concurrent_requests
            )
            
            # Set worker info in metrics
            metrics.set_worker_info(self.worker_id, config.model_name)
            
            logger.info("Worker service initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize worker service: {e}", exc_info=True)
            raise
    
    async def start(self):
        """Start the worker service."""
        if self.running:
            logger.warning("Worker service is already running")
            return
        
        if not all([self.model, self.consumer, self.producer, self.processor]):
            raise RuntimeError("Service not initialized. Call initialize() first.")
        
        self.running = True
        logger.info("Starting LLM Worker Service...")
        
        # Start metrics server
        try:
            metrics.start_metrics_server(config.metrics_port)
            logger.info(f"Metrics server started on port {config.metrics_port}")
        except Exception as e:
            logger.warning(f"Failed to start metrics server: {e}")
        
        # Start health check server in background thread
        import threading
        import uvicorn
        from worker.health import app as health_app
        
        def run_health_server():
            """Run health check server in separate thread."""
            uvicorn.run(
                health_app,
                host="0.0.0.0",
                port=config.health_check_port,
                log_level="info",
                access_log=False
            )
        
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        logger.info(f"Health check server started on port {config.health_check_port}")
        
        # Start consuming messages
        async def message_handler(message: Dict[str, Any]) -> None:
            """Handle incoming Kafka messages."""
            try:
                metrics.record_kafka_consume()
                await self.processor.process_request(message)
            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)
                metrics.record_kafka_consumer_error()
        
        # Run consumer in background
        consumer_task = asyncio.create_task(
            self.consumer.start(message_handler)
        )
        
        # Wait for consumer task
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled")
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
    
    async def stop(self):
        """Stop the worker service gracefully."""
        if not self.running:
            return
        
        logger.info("Stopping LLM Worker Service...")
        self.running = False
        
        # Stop consumer
        if self.consumer:
            await self.consumer.stop()
        
        # Flush and close producer
        if self.producer:
            self.producer.flush()
            self.producer.close()
        
        logger.info("Worker service stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point."""
    service = LLMWorkerService()
    
    try:
        # Setup signal handlers
        service.setup_signal_handlers()
        
        # Initialize service
        await service.initialize()
        
        # Start service
        await service.start()
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
