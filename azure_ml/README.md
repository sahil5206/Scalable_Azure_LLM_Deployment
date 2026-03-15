# Azure Machine Learning Integration

**Fully managed ML workflows - no installation required!**

This directory contains Azure ML integration for orchestrating LLM model workflows, training, and serving. Unlike Kubeflow, Azure ML is a fully managed service that requires no installation or infrastructure management.

## ✨ Key Benefits

- ✅ **No Installation** - Fully managed by Azure
- ✅ **Quick Setup** - Get started in 5 minutes
- ✅ **Auto-scaling** - Automatic resource management
- ✅ **Cost-effective** - Pay only for what you use
- ✅ **Integrated** - Works seamlessly with Azure services
- ✅ **Kafka Integration** - Connects with your existing Kafka-based system

## Quick Start

### 1. Install Dependencies

```bash
pip install -r azure_ml/requirements.txt
```

### 2. Set Up Azure ML Workspace

```bash
# Set environment variables
export AZURE_ML_SUBSCRIPTION_ID="<your-subscription-id>"
export AZURE_ML_RESOURCE_GROUP_NAME="<your-resource-group>"
export AZURE_ML_WORKSPACE_NAME="<your-workspace-name>"

# Or create .env file:
# AZURE_ML_SUBSCRIPTION_ID=<your-subscription-id>
# AZURE_ML_RESOURCE_GROUP_NAME=<your-resource-group>
# AZURE_ML_WORKSPACE_NAME=<your-workspace-name>

# Run setup script
python azure_ml/workspace_setup.py
```

### 3. Run Pipelines

```bash
# Training/Deployment Pipeline
python azure_ml/pipelines/llm_pipeline.py

# Inference Pipeline (via Kafka)
python azure_ml/pipelines/inference_pipeline.py
```

## Directory Structure

```
azure_ml/
├── __init__.py
├── config.py                    # Configuration management
├── workspace_setup.py           # Workspace creation script
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── pipelines/                   # Azure ML Pipelines
│   ├── llm_pipeline.py         # Model training/deployment pipeline
│   ├── inference_pipeline.py   # Inference via Kafka pipeline
│   └── components/             # Pipeline components
│       ├── prepare_model.py    # Model preparation component
│       ├── evaluate_model.py   # Model evaluation component
│       └── kafka_inference.py  # Kafka inference component
├── endpoints/                   # Managed endpoints
│   └── managed_endpoint.py     # Endpoint creation and deployment
└── environments/                # Environment definitions
    └── llm_environment.yml      # Conda environment for LLM workloads
```

## Features

### 1. Model Training Pipeline

Orchestrates:
- Model download and preparation
- Model evaluation
- Model registration

```python
from azure_ml.pipelines.llm_pipeline import submit_pipeline

submit_pipeline(
    subscription_id="<subscription-id>",
    resource_group_name="<resource-group>",
    workspace_name="<workspace-name>",
    model_name="microsoft/phi-2"
)
```

### 2. Inference Pipeline (Kafka Integration)

Sends inference requests via Kafka and receives responses:

```python
from azure_ml.pipelines.inference_pipeline import submit_inference_pipeline

submit_inference_pipeline(
    subscription_id="<subscription-id>",
    resource_group_name="<resource-group>",
    workspace_name="<workspace-name>",
    kafka_bootstrap_servers="kafka:9092",
    prompt="What is machine learning?"
)
```

### 3. Managed Endpoints

Deploy models to Azure ML managed endpoints (alternative to KServe):

```python
from azure_ml.endpoints.managed_endpoint import create_managed_endpoint
from azure.ai.ml import MLClient

ml_client = MLClient(...)
endpoint = create_managed_endpoint(
    ml_client=ml_client,
    endpoint_name="llm-inference-endpoint",
    model_path="path/to/model",
    instance_type="Standard_NC6s_v3"
)
```

## Configuration

Configuration is managed via environment variables or `.env` file:

```bash
# Azure ML Workspace
AZURE_ML_SUBSCRIPTION_ID=<subscription-id>
AZURE_ML_RESOURCE_GROUP_NAME=<resource-group>
AZURE_ML_WORKSPACE_NAME=<workspace-name>
AZURE_ML_LOCATION=eastus

# Compute Configuration
AZURE_ML_COMPUTE_CLUSTER_NAME=llm-compute-cluster
AZURE_ML_COMPUTE_VM_SIZE=Standard_NC6s_v3
AZURE_ML_COMPUTE_MIN_NODES=0
AZURE_ML_COMPUTE_MAX_NODES=4

# Model Configuration
AZURE_ML_DEFAULT_MODEL_NAME=microsoft/phi-2

# Endpoint Configuration
AZURE_ML_ENDPOINT_NAME=llm-inference-endpoint
AZURE_ML_ENDPOINT_INSTANCE_TYPE=Standard_NC6s_v3
AZURE_ML_ENDPOINT_INSTANCE_COUNT=1

# Kafka Integration (optional)
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_REQUEST_TOPIC=llm-requests
KAFKA_RESPONSE_TOPIC=llm-responses
```

## Integration with Existing System

Azure ML pipelines integrate seamlessly with your existing Kafka-based LLM worker:

1. **Training Pipeline** → Prepares and evaluates models
2. **Inference Pipeline** → Sends requests via Kafka to your workers
3. **Managed Endpoints** → Alternative serving option (can also use Kafka)

Both systems can run in parallel:
- Use Azure ML for orchestration and experimentation
- Use Kafka workers for production inference
- Or use Azure ML managed endpoints for serving

## Authentication

Azure ML uses Azure Identity for authentication. Options:

1. **DefaultAzureCredential** (recommended):
   - Tries multiple authentication methods
   - Works with Azure CLI, Managed Identity, etc.

2. **Interactive Browser**:
   - Falls back to browser login if needed

3. **Service Principal**:
   ```python
   from azure.identity import ClientSecretCredential
   
   credential = ClientSecretCredential(
       tenant_id="<tenant-id>",
       client_id="<client-id>",
       client_secret="<client-secret>"
   )
   ```

## Cost Optimization

- **Compute Clusters**: Auto-scale from 0 (pay only when running)
- **Managed Endpoints**: Scale to zero when not in use
- **Free Tier**: Available for experimentation
- **Spot Instances**: Use for cost-effective training

## Monitoring

Access Azure ML Studio:
- View pipeline runs and logs
- Monitor compute usage
- Track experiments and metrics
- Manage models and endpoints

```python
# Get pipeline job URL
print(f"View at: {submitted_job.studio_url}")
```

## Troubleshooting

### Authentication Issues

```bash
# Login via Azure CLI
az login

# Verify credentials
az account show
```

### Compute Not Available

```bash
# Check compute cluster status
python azure_ml/workspace_setup.py
```

### Pipeline Fails

- Check logs in Azure ML Studio
- Verify compute cluster is running
- Check environment dependencies

## Next Steps

1. **Set up workspace**: Run `workspace_setup.py`
2. **Run training pipeline**: Test model preparation
3. **Test inference**: Send requests via Kafka
4. **Deploy endpoint**: Create managed endpoint for serving
5. **Monitor**: Use Azure ML Studio for monitoring

## Resources

- [Azure ML Documentation](https://learn.microsoft.com/en-us/azure/machine-learning/)
- [Azure ML Pipelines](https://learn.microsoft.com/en-us/azure/machine-learning/concept-ml-pipelines)
- [Managed Endpoints](https://learn.microsoft.com/en-us/azure/machine-learning/concept-endpoints)
- [Azure ML Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ml/)
