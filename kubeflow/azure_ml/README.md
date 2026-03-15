# Azure Machine Learning Integration

This directory contains **Azure ML** versions of the pipelines - **no installation required!**

## Why Azure ML?

- ✅ **Fully managed** - No installation or infrastructure management
- ✅ **Quick setup** - Get started in 5 minutes
- ✅ **Auto-scaling** - Automatic resource scaling
- ✅ **Integrated** - Works seamlessly with Azure services
- ✅ **Cost-effective** - Pay only for what you use

## Quick Start

### 1. Install Azure ML SDK

```bash
pip install azure-ai-ml azure-identity
```

### 2. Create Azure ML Workspace

```bash
# Via Azure CLI
az ml workspace create \
  --name my-ml-workspace \
  --resource-group my-resource-group \
  --location eastus

# Or via Azure Portal:
# 1. Go to Azure Portal
# 2. Search for "Machine Learning"
# 3. Create new workspace
```

### 3. Run Pipeline

```python
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from azure_ml_pipeline import llm_pipeline_azure_ml

# Connect to workspace
ml_client = MLClient(
    DefaultAzureCredential(),
    subscription_id="<your-subscription>",
    resource_group_name="<your-rg>",
    workspace_name="<your-workspace>"
)

# Submit pipeline (no installation needed!)
pipeline_job = ml_client.jobs.create_or_update(
    llm_pipeline_azure_ml(
        model_name="microsoft/phi-2",
        endpoint_name="llm-worker-phi2"
    )
)

print(f"Pipeline running: {pipeline_job.studio_url}")
```

## Comparison with Kubeflow

| Feature | Azure ML | Kubeflow |
|---------|----------|----------|
| Setup Time | 5 minutes | 20-30 minutes |
| Installation | None | Required |
| Management | Azure | You |
| Cost | Pay-per-use | Fixed cluster |

## Integration with Kafka

Azure ML pipelines can still integrate with your Kafka-based system:

```python
from azure.ai.ml import command

@dsl.pipeline()
def inference_pipeline_azure_ml():
    # Send inference request to Kafka
    send_request = command(
        name="send_kafka_request",
        code="./",
        command="python send_kafka_request.py --prompt 'Hello'",
        environment="azureml:python:3.11"
    )
    
    # Process response
    process_response = command(
        name="process_kafka_response",
        code="./",
        command="python process_kafka_response.py",
        environment="azureml:python:3.11"
    )
    process_response.after(send_request)
```

## Managed Endpoints (Alternative to KServe)

Azure ML provides **Managed Endpoints** which are similar to KServe:

```python
from azure.ai.ml.entities import ManagedOnlineEndpoint, ManagedOnlineDeployment
from azure.ai.ml import MLClient

# Create managed endpoint
endpoint = ManagedOnlineEndpoint(
    name="llm-worker-phi2",
    description="LLM inference endpoint",
    auth_mode="key"
)
ml_client.online_endpoints.begin_create_or_update(endpoint)

# Deploy model
deployment = ManagedOnlineDeployment(
    name="blue",
    endpoint_name="llm-worker-phi2",
    model=model,
    instance_type="Standard_DS3_v2",
    instance_count=1,
    environment=env
)
ml_client.online_deployments.begin_create_or_update(deployment)
```

## Next Steps

1. **Choose Azure ML** if you want managed service (recommended)
2. **Use Kubeflow** if you need full control and customization
3. **Hybrid approach**: Use Azure ML for pipelines, keep Kafka workers on AKS

## Resources

- [Azure ML Documentation](https://learn.microsoft.com/en-us/azure/machine-learning/)
- [Azure ML Pipelines](https://learn.microsoft.com/en-us/azure/machine-learning/concept-ml-pipelines)
- [Managed Endpoints](https://learn.microsoft.com/en-us/azure/machine-learning/concept-endpoints)
