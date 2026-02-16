"""
Kafka consumer for LLM inference requests.

Handles consuming requests from Kafka with proper error handling,
offset management, and consumer group coordination.
"""
import logging
import json
import asyncio
from typing import Optional, Callable, Dict, Any, Awaitable
from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient
import time

logger = logging.getLogger(__name__)


class KafkaRequestConsumer:
    """
    Kafka consumer for inference requests.
    
    Consumes messages from the request topic and processes them
    through a callback function. Handles consumer group management
    and offset commits.
    """
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = False,
        max_poll_records: int = 10,
        session_timeout_ms: int = 30000
    ):
        """
        Initialize Kafka consumer.
        
        Args:
            bootstrap_servers: Kafka broker addresses
            topic: Topic to consume from
            group_id: Consumer group ID
            auto_offset_reset: Offset reset policy
            enable_auto_commit: Enable automatic offset commits
            max_poll_records: Maximum records per poll
            session_timeout_ms: Session timeout in milliseconds
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.consumer = None
        self.running = False
        
        # Consumer configuration
        self.config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': auto_offset_reset,
            'enable.auto.commit': enable_auto_commit,
            'max.poll.records': max_poll_records,
            'session.timeout.ms': session_timeout_ms,
            'enable.partition.eof': False,
            'api.version.request': True,
        }
        
        logger.info(f"Initializing Kafka consumer for topic: {topic}")
        logger.info(f"Consumer group: {group_id}")
    
    def _create_consumer(self):
        """Create and configure Kafka consumer."""
        try:
            consumer = Consumer(self.config)
            
            # Verify topic exists
            admin_client = AdminClient({'bootstrap.servers': self.bootstrap_servers})
            metadata = admin_client.list_topics(timeout=10)
            
            if self.topic not in metadata.topics:
                logger.warning(f"Topic {self.topic} does not exist. It will be created on first message.")
            
            # Subscribe to topic
            consumer.subscribe([self.topic])
            logger.info(f"Subscribed to topic: {self.topic}")
            
            return consumer
        
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}", exc_info=True)
            raise
    
    async def start(
        self,
        message_handler: Callable[[Dict[str, Any]], Awaitable[None]],
        poll_timeout: float = 1.0
    ):
        """
        Start consuming messages.
        
        Args:
            message_handler: Async function to handle messages
            poll_timeout: Timeout for polling messages (seconds)
        """
        if self.running:
            logger.warning("Consumer is already running")
            return
        
        self.consumer = self._create_consumer()
        self.running = True
        
        logger.info("Starting Kafka consumer...")
        
        try:
            while self.running:
                # Poll for messages
                msg = self.consumer.poll(timeout=poll_timeout)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        logger.debug(f"Reached end of partition: {msg.topic()}[{msg.partition()}]")
                        continue
                    elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                        logger.error(f"Topic or partition does not exist: {msg.error()}")
                        await asyncio.sleep(5)
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        continue
                
                # Parse message
                try:
                    message_data = json.loads(msg.value().decode('utf-8'))
                    message_key = msg.key().decode('utf-8') if msg.key() else None
                    
                    # Add metadata
                    message_data['_kafka_metadata'] = {
                        'topic': msg.topic(),
                        'partition': msg.partition(),
                        'offset': msg.offset(),
                        'timestamp': msg.timestamp(),
                        'key': message_key
                    }
                    
                    # Handle message
                    await message_handler(message_data)
                    
                    # Commit offset manually if auto-commit is disabled
                    if not self.config['enable.auto.commit']:
                        self.consumer.commit(msg)
                
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                    logger.error(f"Message value: {msg.value()}")
                    # Commit offset even for invalid messages to avoid reprocessing
                    if not self.config['enable.auto.commit']:
                        self.consumer.commit(msg)
                
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Don't commit offset on processing errors to allow retry
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down consumer...")
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the consumer gracefully."""
        if not self.running:
            return
        
        self.running = False
        
        if self.consumer:
            try:
                # Commit final offsets
                self.consumer.commit()
                self.consumer.close()
                logger.info("Kafka consumer stopped")
            except Exception as e:
                logger.error(f"Error closing consumer: {e}", exc_info=True)
    
    def get_lag(self) -> Dict[str, int]:
        """
        Get consumer lag for all partitions.
        
        Returns:
            Dictionary mapping partition to lag
        """
        if not self.consumer:
            return {}
        
        try:
            # Get committed offsets
            committed = self.consumer.committed(
                [self.consumer.assignment()],
                timeout=10
            )
            
            # Get high water marks
            metadata = self.consumer.list_topics(timeout=10)
            topic_metadata = metadata.topics.get(self.topic)
            
            lag_info = {}
            if topic_metadata:
                for partition_id, partition_metadata in topic_metadata.partitions.items():
                    high_water = partition_metadata.high
                    committed_offset = committed.get(partition_id, -1)
                    lag = high_water - committed_offset if high_water > committed_offset else 0
                    lag_info[str(partition_id)] = lag
            
            return lag_info
        
        except Exception as e:
            logger.error(f"Failed to get consumer lag: {e}", exc_info=True)
            return {}
