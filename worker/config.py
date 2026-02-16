"""
Configuration management for LLM Worker Service.

Uses Pydantic Settings for type-safe configuration with environment variable support.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class WorkerConfig(BaseSettings):
    """Worker service configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers (comma-separated)"
    )
    kafka_request_topic: str = Field(
        default="llm-requests",
        description="Kafka topic for incoming inference requests"
    )
    kafka_response_topic: str = Field(
        default="llm-responses",
        description="Kafka topic for outgoing inference responses"
    )
    kafka_consumer_group: str = Field(
        default="llm-worker-group",
        description="Kafka consumer group ID for worker instances"
    )
    kafka_auto_offset_reset: str = Field(
        default="earliest",
        description="Kafka auto offset reset policy"
    )
    kafka_enable_auto_commit: bool = Field(
        default=False,
        description="Disable auto-commit for manual offset management"
    )
    kafka_max_poll_records: int = Field(
        default=10,
        description="Maximum records to poll in one batch"
    )
    kafka_session_timeout_ms: int = Field(
        default=30000,
        description="Kafka session timeout in milliseconds"
    )
    
    # Model Configuration
    model_name: str = Field(
        default="microsoft/phi-2",
        description="HuggingFace model identifier"
    )
    model_device: str = Field(
        default="auto",
        description="Device for model inference (auto, cpu, cuda)"
    )
    model_dtype: str = Field(
        default="float16",
        description="Model data type (float32, float16, bfloat16)"
    )
    max_sequence_length: int = Field(
        default=512,
        description="Maximum token sequence length"
    )
    max_new_tokens: int = Field(
        default=256,
        description="Maximum number of new tokens to generate"
    )
    temperature: float = Field(
        default=0.7,
        description="Sampling temperature for generation"
    )
    top_p: float = Field(
        default=0.9,
        description="Nucleus sampling parameter"
    )
    do_sample: bool = Field(
        default=True,
        description="Enable sampling for generation"
    )
    
    # Batching Configuration
    batch_size: int = Field(
        default=4,
        description="Batch size for processing requests"
    )
    batch_timeout_seconds: float = Field(
        default=0.1,
        description="Timeout for batching requests (seconds)"
    )
    
    # Service Configuration
    metrics_port: int = Field(
        default=8080,
        description="Port for Prometheus metrics endpoint"
    )
    health_check_port: int = Field(
        default=8081,
        description="Port for health check endpoint"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Worker Configuration
    worker_id: Optional[str] = Field(
        default=None,
        description="Unique worker instance ID (auto-generated if not provided)"
    )
    max_concurrent_requests: int = Field(
        default=10,
        description="Maximum concurrent inference requests"
    )
    request_timeout_seconds: int = Field(
        default=300,
        description="Timeout for individual inference requests (seconds)"
    )
    
    # Retry Configuration
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed requests"
    )
    retry_backoff_seconds: float = Field(
        default=1.0,
        description="Backoff time between retries (seconds)"
    )


# Global configuration instance
config = WorkerConfig()
