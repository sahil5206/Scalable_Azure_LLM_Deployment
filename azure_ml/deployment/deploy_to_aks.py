"""
Deploy Azure ML models to AKS for production inference.

This script deploys trained models from Azure ML to AKS,
integrating with the existing Kafka-based infrastructure.
"""
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    Model,
    Environment,
    Code,
    KubernetesOnlineEndpoint,
    KubernetesOnlineDeployment
)
from azure.identity import DefaultAzureCredential
from azure_ml.config import azure_ml_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def deploy_model_to_aks(
    ml_client: MLClient,
    model_name: str,
    model_version: str = None,
    endpoint_name: str = None,
    compute_target: str = None,
    instance_count: int = 2,
    instance_type: str = "Standard_NC6s_v3"
):
    """
    Deploy model from Azure ML to AKS for production.
    
    Args:
        ml_client: MLClient instance
        model_name: Name of registered model
        model_version: Model version (latest if None)
        endpoint_name: Endpoint name
        compute_target: AKS compute target name
        instance_count: Number of instances
        instance_type: VM instance type
    """
    endpoint_name = endpoint_name or f"{model_name}-endpoint"
    
    logger.info(f"Deploying model {model_name} to AKS endpoint: {endpoint_name}")
    
    # Get model
    if model_version:
        model = ml_client.models.get(model_name, version=model_version)
    else:
        model = ml_client.models.get(model_name)
    
    logger.info(f"Using model: {model.name} (version {model.version})")
    
    # Create or get endpoint
    try:
        endpoint = ml_client.online_endpoints.get(endpoint_name)
        logger.info(f"Endpoint {endpoint_name} already exists")
    except Exception:
        logger.info(f"Creating new endpoint: {endpoint_name}")
        endpoint = ManagedOnlineEndpoint(
            name=endpoint_name,
            description=f"Production endpoint for {model_name}",
            auth_mode="key"
        )
        endpoint = ml_client.online_endpoints.begin_create_or_update(endpoint).result()
        logger.info(f"✓ Endpoint created: {endpoint.scoring_uri}")
    
    # Create environment
    env = Environment(
        name="llm-inference-env",
        conda_file="azure_ml/environments/llm_environment.yml",
        image="mcr.microsoft.com/azureml/openmpi4.1.0-cuda11.8-cudnn8-ubuntu22.04:latest"
    )
    env = ml_client.environments.create_or_update(env)
    
    # Create deployment
    deployment_name = "blue"
    deployment = ManagedOnlineDeployment(
        name=deployment_name,
        endpoint_name=endpoint_name,
        model=model,
        environment=env,
        code_configuration=Code(
            code="worker",
            scoring_script="main.py"
        ),
        instance_type=instance_type,
        instance_count=instance_count
    )
    
    deployment = ml_client.online_deployments.begin_create_or_update(deployment).result()
    logger.info(f"✓ Deployment created: {deployment_name}")
    
    # Set as default
    ml_client.online_endpoints.begin_update_traffic(
        endpoint_name=endpoint_name,
        traffic={deployment_name: 100}
    )
    
    logger.info(f"✓ Model deployed successfully!")
    logger.info(f"  Endpoint: {endpoint.scoring_uri}")
    logger.info(f"  Instances: {instance_count}")
    logger.info(f"  Instance Type: {instance_type}")
    
    return endpoint, deployment


def deploy_to_kubernetes(
    ml_client: MLClient,
    model_name: str,
    kubernetes_name: str,
    instance_count: int = 2
):
    """
    Deploy model to Kubernetes (AKS) compute target.
    
    Args:
        ml_client: MLClient instance
        model_name: Name of registered model
        kubernetes_name: Kubernetes compute target name
        instance_count: Number of replicas
    """
    logger.info(f"Deploying to Kubernetes: {kubernetes_name}")
    
    # Get Kubernetes compute
    compute = ml_client.compute.get(kubernetes_name)
    
    # Get model
    model = ml_client.models.get(model_name)
    
    # Create Kubernetes endpoint
    endpoint = KubernetesOnlineEndpoint(
        name=f"{model_name}-k8s-endpoint",
        compute=compute.name,
        description=f"Kubernetes endpoint for {model_name}"
    )
    
    # Create deployment
    deployment = KubernetesOnlineDeployment(
        name="blue",
        endpoint_name=endpoint.name,
        model=model,
        instance_count=instance_count,
        environment=Environment(
            name="llm-inference-env",
            conda_file="azure_ml/environments/llm_environment.yml"
        )
    )
    
    endpoint = ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    deployment = ml_client.online_deployments.begin_create_or_update(deployment).result()
    
    logger.info(f"✓ Deployed to Kubernetes: {endpoint.name}")
    return endpoint, deployment


if __name__ == "__main__":
    from azure_ml.config import azure_ml_config
    
    config = azure_ml_config
    
    if not config.subscription_id:
        logger.error("Azure ML configuration missing!")
        exit(1)
    
    ml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id=config.subscription_id,
        resource_group_name=config.resource_group_name,
        workspace_name=config.workspace_name
    )
    
    # Deploy model
    deploy_model_to_aks(
        ml_client=ml_client,
        model_name="llm-model",
        endpoint_name=config.endpoint_name,
        instance_count=config.endpoint_instance_count,
        instance_type=config.endpoint_instance_type
    )
