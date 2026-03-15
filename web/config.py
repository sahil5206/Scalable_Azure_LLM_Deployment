"""
Web frontend configuration.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class WebConfig(BaseSettings):
    """Web frontend configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        description="Server port"
    )
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers"
    )
    kafka_request_topic: str = Field(
        default="llm-requests",
        description="Kafka topic for requests"
    )
    kafka_response_topic: str = Field(
        default="llm-responses",
        description="Kafka topic for responses"
    )
    kafka_consumer_group: str = Field(
        default="web-frontend-group",
        description="Kafka consumer group for web frontend"
    )
    
    # Request Configuration
    request_timeout_seconds: int = Field(
        default=120,
        description="Timeout for inference requests"
    )
    max_tokens: int = Field(
        default=512,
        description="Maximum tokens to generate"
    )
    temperature: float = Field(
        default=0.7,
        description="Sampling temperature"
    )
    
    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    
    # Azure ML Configuration (optional)
    azure_ml_endpoint_name: Optional[str] = Field(
        default=None,
        description="Azure ML managed endpoint name (if using Azure ML)"
    )
    azure_ml_subscription_id: Optional[str] = Field(
        default=None,
        description="Azure subscription ID for Azure ML"
    )
    azure_ml_resource_group_name: Optional[str] = Field(
        default=None,
        description="Resource group name for Azure ML"
    )
    azure_ml_workspace_name: Optional[str] = Field(
        default=None,
        description="Workspace name for Azure ML"
    )
    use_azure_ml_primary: bool = Field(
        default=True,
        description="Use Azure ML as primary inference method (if available)"
    )


# Global configuration instance
config = WebConfig()
