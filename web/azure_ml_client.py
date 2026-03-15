"""
Azure ML integration for web frontend.

Allows web frontend to use Azure ML managed endpoints
as an alternative or additional inference method.
"""
import os
import requests
import logging
from typing import Optional, Dict, Any
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import ManagedOnlineEndpoint

logger = logging.getLogger(__name__)


class AzureMLEndpointClient:
    """Client for Azure ML managed endpoints."""
    
    def __init__(
        self,
        endpoint_name: str,
        subscription_id: Optional[str] = None,
        resource_group_name: Optional[str] = None,
        workspace_name: Optional[str] = None
    ):
        """
        Initialize Azure ML endpoint client.
        
        Args:
            endpoint_name: Name of the managed endpoint
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            workspace_name: Workspace name
        """
        self.endpoint_name = endpoint_name
        self.subscription_id = subscription_id or os.getenv("AZURE_ML_SUBSCRIPTION_ID")
        self.resource_group_name = resource_group_name or os.getenv("AZURE_ML_RESOURCE_GROUP_NAME")
        self.workspace_name = workspace_name or os.getenv("AZURE_ML_WORKSPACE_NAME")
        
        self.ml_client = None
        self.endpoint = None
        self.scoring_uri = None
        self.api_key = None
        
        if all([self.subscription_id, self.resource_group_name, self.workspace_name]):
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ML client and get endpoint details."""
        try:
            self.ml_client = MLClient(
                DefaultAzureCredential(),
                subscription_id=self.subscription_id,
                resource_group_name=self.resource_group_name,
                workspace_name=self.workspace_name
            )
            
            # Get endpoint
            self.endpoint = self.ml_client.online_endpoints.get(self.endpoint_name)
            self.scoring_uri = self.endpoint.scoring_uri
            
            # Get API key
            keys = self.ml_client.online_endpoints.get_keys(self.endpoint_name)
            self.api_key = keys.primary_key
            
            logger.info(f"Azure ML endpoint initialized: {self.endpoint_name}")
            logger.info(f"Scoring URI: {self.scoring_uri}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Azure ML endpoint: {e}")
            logger.warning("Falling back to Kafka-based inference")
            self.ml_client = None
    
    def is_available(self) -> bool:
        """Check if Azure ML endpoint is available."""
        return self.scoring_uri is not None and self.api_key is not None
    
    def infer(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Send inference request to Azure ML endpoint.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout: Request timeout in seconds
        
        Returns:
            Response dictionary
        """
        if not self.is_available():
            raise RuntimeError("Azure ML endpoint not available")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                self.scoring_uri,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "status": "success",
                "generated_text": result.get("generated_text", ""),
                "tokens_generated": result.get("tokens_generated", 0),
                "model": result.get("model", self.endpoint_name),
                "source": "azure_ml"
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Azure ML endpoint request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing Azure ML response: {e}")
            raise


def get_azure_ml_client() -> Optional[AzureMLEndpointClient]:
    """Get Azure ML client if configured."""
    endpoint_name = os.getenv("AZURE_ML_ENDPOINT_NAME")
    
    if not endpoint_name:
        return None
    
    try:
        client = AzureMLEndpointClient(endpoint_name=endpoint_name)
        if client.is_available():
            return client
    except Exception as e:
        logger.warning(f"Azure ML client initialization failed: {e}")
    
    return None
