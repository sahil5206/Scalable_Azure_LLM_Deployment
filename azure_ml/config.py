"""
Azure ML configuration management.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class AzureMLConfig(BaseSettings):
    """Azure ML workspace configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Azure ML Workspace Configuration
    subscription_id: str = Field(
        default="",
        description="Azure subscription ID"
    )
    resource_group_name: str = Field(
        default="",
        description="Azure resource group name"
    )
    workspace_name: str = Field(
        default="",
        description="Azure ML workspace name"
    )
    location: str = Field(
        default="eastus",
        description="Azure region for workspace"
    )
    
    # Compute Configuration
    compute_cluster_name: str = Field(
        default="llm-compute-cluster",
        description="Name of the compute cluster"
    )
    compute_vm_size: str = Field(
        default="Standard_NC6s_v3",  # GPU instance
        description="VM size for compute cluster"
    )
    compute_min_nodes: int = Field(
        default=0,
        description="Minimum nodes in compute cluster"
    )
    compute_max_nodes: int = Field(
        default=4,
        description="Maximum nodes in compute cluster"
    )
    
    # Model Configuration
    default_model_name: str = Field(
        default="microsoft/phi-2",
        description="Default HuggingFace model identifier"
    )
    model_registry_name: str = Field(
        default="llm-models",
        description="Model registry name"
    )
    
    # Endpoint Configuration
    endpoint_name: str = Field(
        default="llm-inference-endpoint",
        description="Managed endpoint name"
    )
    endpoint_instance_type: str = Field(
        default="Standard_NC6s_v3",
        description="Instance type for managed endpoint"
    )
    endpoint_instance_count: int = Field(
        default=1,
        description="Number of instances for managed endpoint"
    )
    
    # Kafka Integration (for connecting with existing system)
    kafka_bootstrap_servers: Optional[str] = Field(
        default=None,
        description="Kafka bootstrap servers (if using Kafka integration)"
    )
    kafka_request_topic: str = Field(
        default="llm-requests",
        description="Kafka topic for requests"
    )
    kafka_response_topic: str = Field(
        default="llm-responses",
        description="Kafka topic for responses"
    )


# Global configuration instance
azure_ml_config = AzureMLConfig()
