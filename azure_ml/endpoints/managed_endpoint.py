"""
Azure ML Managed Endpoint for LLM model serving.

Alternative to KServe - fully managed by Azure!
"""
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    Model,
    Environment,
    Code
)
from azure.identity import DefaultAzureCredential
from azure_ml.config import azure_ml_config


def create_managed_endpoint(
    ml_client: MLClient,
    endpoint_name: str,
    model_path: str = None,
    instance_type: str = "Standard_NC6s_v3",
    instance_count: int = 1
):
    """
    Create or update managed endpoint for LLM model.
    
    Args:
        ml_client: MLClient instance
        endpoint_name: Endpoint name
        model_path: Path to model (if deploying)
        instance_type: VM instance type
        instance_count: Number of instances
    """
    print(f"Creating managed endpoint: {endpoint_name}")
    
    # Create endpoint
    endpoint = ManagedOnlineEndpoint(
        name=endpoint_name,
        description="LLM inference endpoint",
        auth_mode="key"
    )
    
    try:
        endpoint = ml_client.online_endpoints.get(endpoint_name)
        print(f"✓ Endpoint '{endpoint_name}' already exists")
    except Exception:
        print(f"Creating new endpoint '{endpoint_name}'...")
        endpoint = ml_client.online_endpoints.begin_create_or_update(endpoint).result()
        print(f"✓ Endpoint created")
    
    # Deploy model if path provided
    if model_path:
        deploy_model_to_endpoint(
            ml_client=ml_client,
            endpoint_name=endpoint_name,
            model_path=model_path,
            instance_type=instance_type,
            instance_count=instance_count
        )
    
    return endpoint


def deploy_model_to_endpoint(
    ml_client: MLClient,
    endpoint_name: str,
    model_path: str,
    instance_type: str = "Standard_NC6s_v3",
    instance_count: int = 1,
    deployment_name: str = "blue"
):
    """
    Deploy model to managed endpoint.
    
    Args:
        ml_client: MLClient instance
        endpoint_name: Endpoint name
        model_path: Path to model
        instance_type: VM instance type
        instance_count: Number of instances
        deployment_name: Deployment name (for A/B testing)
    """
    print(f"Deploying model to endpoint: {endpoint_name}")
    
    # Register model
    print("Registering model...")
    model = Model(
        path=model_path,
        name="llm-model",
        description="LLM model for inference"
    )
    registered_model = ml_client.models.create_or_update(model)
    print(f"✓ Model registered: {registered_model.name}")
    
    # Create environment (using worker code)
    print("Creating environment...")
    env = Environment(
        name="llm-inference-env",
        conda_file="worker/requirements.txt",  # Use worker requirements
        image="mcr.microsoft.com/azureml/openmpi4.1.0-cuda11.8-cudnn8-ubuntu22.04:latest"
    )
    env = ml_client.environments.create_or_update(env)
    print(f"✓ Environment created")
    
    # Create deployment
    print(f"Creating deployment '{deployment_name}'...")
    deployment = ManagedOnlineDeployment(
        name=deployment_name,
        endpoint_name=endpoint_name,
        model=registered_model,
        environment=env,
        code_configuration=Code(
            code="worker",  # Use worker code
            scoring_script="main.py"  # Entry point
        ),
        instance_type=instance_type,
        instance_count=instance_count
    )
    
    deployment = ml_client.online_deployments.begin_create_or_update(deployment).result()
    print(f"✓ Deployment created")
    
    # Set as default
    ml_client.online_endpoints.begin_update_traffic(
        endpoint_name=endpoint_name,
        traffic={deployment_name: 100}
    )
    print(f"✓ Deployment set as default")
    
    return deployment


def test_endpoint(
    ml_client: MLClient,
    endpoint_name: str,
    prompt: str = "What is machine learning?"
):
    """
    Test managed endpoint with a sample request.
    
    Args:
        ml_client: MLClient instance
        endpoint_name: Endpoint name
        prompt: Test prompt
    """
    print(f"Testing endpoint: {endpoint_name}")
    
    endpoint = ml_client.online_endpoints.get(endpoint_name)
    
    # Get scoring URI
    scoring_uri = endpoint.scoring_uri
    print(f"Scoring URI: {scoring_uri}")
    
    # Get key
    keys = ml_client.online_endpoints.get_keys(endpoint_name)
    api_key = keys.primary_key
    
    # Send request
    import requests
    import json
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "prompt": prompt,
        "max_tokens": 100
    }
    
    response = requests.post(scoring_uri, headers=headers, json=payload)
    
    if response.status_code == 200:
        print(f"✓ Request successful")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"✗ Request failed: {response.status_code}")
        print(f"Response: {response.text}")


if __name__ == "__main__":
    from azure_ml.config import azure_ml_config
    
    config = azure_ml_config
    
    if not config.subscription_id:
        print("⚠️  Configuration missing!")
        exit(1)
    
    ml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id=config.subscription_id,
        resource_group_name=config.resource_group_name,
        workspace_name=config.workspace_name
    )
    
    # Create endpoint
    endpoint = create_managed_endpoint(
        ml_client=ml_client,
        endpoint_name=config.endpoint_name,
        instance_type=config.endpoint_instance_type,
        instance_count=config.endpoint_instance_count
    )
    
    print(f"\n✓ Endpoint ready: {endpoint.scoring_uri}")
