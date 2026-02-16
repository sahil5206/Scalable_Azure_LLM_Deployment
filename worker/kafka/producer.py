"""
Kafka producer for LLM inference responses.

Handles producing responses to Kafka with proper error handling,
retry logic, and delivery guarantees.
"""
import logging
import json
from typing import Dict, Any, Optional
from confluent_kafka import Producer, KafkaError
from confluent_kafka.admin import AdminClient
import time

logger = logging.getLogger(__name__)


class KafkaResponseProducer:
    """
    Kafka producer for inference responses.
    
    Produces messages to the response topic with delivery callbacks
    and error handling.
    """
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        acks: str = "all",
        retries: int = 3,
        max_in_flight_requests_per_connection: int = 5,
        enable_idempotence: bool = True,
        compression_type: str = "snappy"
    ):
        """
        Initialize Kafka producer.
        
        Args:
            bootstrap_servers: Kafka broker addresses
            topic: Topic to produce to
            acks: Number of acknowledgments required (all, 1, 0)
            retries: Number of retry attempts
            max_in_flight_requests_per_connection: Max in-flight requests
            enable_idempotence: Enable idempotent producer
            compression_type: Compression algorithm
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        
        # Producer configuration
        self.config = {
            'bootstrap.servers': bootstrap_servers,
            'acks': acks,
            'retries': retries,
            'max.in.flight.requests.per.connection': max_in_flight_requests_per_connection,
            'enable.idempotence': enable_idempotence,
            'compression.type': compression_type,
            'linger.ms': 10,  # Batch messages for better throughput
            'batch.size': 16384,  # 16KB batch size
        }
        
        self.producer = None
        self._delivery_callback_count = 0
        self._delivery_errors = []
        
        logger.info(f"Initializing Kafka producer for topic: {topic}")
    
    def _create_producer(self):
        """Create and configure Kafka producer."""
        try:
            producer = Producer(self.config)
            
            # Verify topic exists
            admin_client = AdminClient({'bootstrap.servers': self.bootstrap_servers})
            metadata = admin_client.list_topics(timeout=10)
            
            if self.topic not in metadata.topics:
                logger.warning(f"Topic {self.topic} does not exist. It will be created on first message.")
            
            logger.info("Kafka producer created successfully")
            return producer
        
        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {e}", exc_info=True)
            raise
    
    def _delivery_callback(self, err, msg):
        """
        Delivery callback for produced messages.
        
        Called asynchronously when message delivery is confirmed or fails.
        """
        if err is not None:
            error_msg = f"Message delivery failed: {err}"
            logger.error(error_msg)
            self._delivery_errors.append({
                'error': str(err),
                'timestamp': time.time()
            })
        else:
            self._delivery_callback_count += 1
            logger.debug(
                f"Message delivered to {msg.topic()}[{msg.partition()}] "
                f"at offset {msg.offset()}"
            )
    
    def produce(
        self,
        message: Dict[str, Any],
        key: Optional[str] = None,
        partition: Optional[int] = None
    ) -> bool:
        """
        Produce a message to Kafka.
        
        Args:
            message: Message payload as dictionary
            key: Optional message key for partitioning
            partition: Optional partition number
        
        Returns:
            True if message was queued successfully
        """
        if not self.producer:
            self.producer = self._create_producer()
        
        try:
            # Serialize message
            message_value = json.dumps(message, ensure_ascii=False)
            
            # Produce message
            self.producer.produce(
                self.topic,
                value=message_value.encode('utf-8'),
                key=key.encode('utf-8') if key else None,
                partition=partition,
                callback=self._delivery_callback,
                timestamp=int(time.time() * 1000)  # Milliseconds
            )
            
            # Trigger delivery callbacks
            self.producer.poll(0)
            
            return True
        
        except BufferError:
            logger.warning("Producer queue is full, flushing...")
            self.flush()
            # Retry after flush
            return self.produce(message, key, partition)
        
        except Exception as e:
            logger.error(f"Failed to produce message: {e}", exc_info=True)
            return False
    
    def flush(self, timeout: float = 10.0):
        """
        Flush pending messages.
        
        Args:
            timeout: Maximum time to wait for flush (seconds)
        """
        if self.producer:
            try:
                remaining = self.producer.flush(timeout=timeout)
                if remaining > 0:
                    logger.warning(f"{remaining} messages were not delivered after flush timeout")
                else:
                    logger.debug("All messages flushed successfully")
            except Exception as e:
                logger.error(f"Error flushing producer: {e}", exc_info=True)
    
    def close(self):
        """Close the producer gracefully."""
        if self.producer:
            try:
                # Flush remaining messages
                self.flush()
                self.producer = None
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing producer: {e}", exc_info=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get producer statistics."""
        if not self.producer:
            return {}
        
        try:
            stats = self.producer.list_topics(timeout=5)
            return {
                'delivered_messages': self._delivery_callback_count,
                'delivery_errors': len(self._delivery_errors),
                'recent_errors': self._delivery_errors[-10:] if self._delivery_errors else []
            }
        except Exception as e:
            logger.error(f"Failed to get producer stats: {e}", exc_info=True)
            return {
                'delivered_messages': self._delivery_callback_count,
                'delivery_errors': len(self._delivery_errors)
            }
