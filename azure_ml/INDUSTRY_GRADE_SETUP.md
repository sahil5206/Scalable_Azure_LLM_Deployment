# Industry-Grade Azure ML Integration Setup

This guide helps you set up Azure Machine Learning as a core component of this project, making it industry-grade with production best practices.

## 🎯 Industry-Grade Features

### 1. Model Management
- ✅ Model Registry: Version control for models
- ✅ Model Versioning: Track model iterations
- ✅ Model Lineage: Track data and code used

### 2. MLOps Pipeline
- ✅ Automated Training: CI/CD for model training
- ✅ Automated Deployment: Deploy to production automatically
- ✅ A/B Testing: Test new models safely
- ✅ Rollback: Quick rollback to previous versions

### 3. Production Inference
- ✅ Managed Endpoints: Auto-scaling inference
- ✅ High Availability: Multi-region deployment
- ✅ Monitoring: Real-time metrics and alerts
- ✅ Cost Optimization: Auto-scale to zero

### 4. Observability
- ✅ Experiment Tracking: Track all experiments
- ✅ Model Monitoring: Monitor model performance
- ✅ Data Drift Detection: Detect data changes
- ✅ Performance Metrics: Track latency, throughput

## 🏗️ Architecture with Azure ML

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                           │
│                  (Web Frontend)                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Web Frontend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Inference Router                                     │  │
│  │  - Azure ML Endpoint (Primary)                        │  │
│  │  - Kafka Workers (Fallback)                           │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────────┐         ┌──────────────────┐
│ Azure ML         │         │ Kafka            │
│ Managed Endpoint │         │ (Fallback)       │
│                  │         │                  │
│ - Auto-scaling   │         │ - Direct workers │
│ - High availability│       │ - Batch processing│
│ - Monitoring     │         │                  │
└──────────────────┘         └──────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│              Azure ML Workspace                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Model Registry                                       │  │
│  │  - Versioned Models                                   │  │
│  │  - Model Metadata                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ML Pipelines                                         │  │
│  │  - Training Pipeline                                  │  │
│  │  - Evaluation Pipeline                                │  │
│  │  - Deployment Pipeline                                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Experiment Tracking                                  │  │
│  │  - Metrics & Logs                                     │  │
│  │  - Artifacts                                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Step-by-Step Setup

### Step 1: Create Azure ML Workspace

```bash
# Install Azure CLI if not already installed
az login

# Create resource group
az group create \
  --name llm-platform-rg \
  --location eastus

# Create Azure ML workspace
az ml workspace create \
  --name llm-ml-workspace \
  --resource-group llm-platform-rg \
  --location eastus
```

### Step 2: Set Up Environment

```bash
# Install dependencies
pip install -r azure_ml/requirements.txt

# Set environment variables
export AZURE_ML_SUBSCRIPTION_ID="<your-subscription-id>"
export AZURE_ML_RESOURCE_GROUP_NAME="llm-platform-rg"
export AZURE_ML_WORKSPACE_NAME="llm-ml-workspace"

# Or create .env file
cat > .env << EOF
AZURE_ML_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_ML_RESOURCE_GROUP_NAME=llm-platform-rg
AZURE_ML_WORKSPACE_NAME=llm-ml-workspace
AZURE_ML_ENDPOINT_NAME=llm-inference-endpoint
EOF
```

### Step 3: Run Setup Script

```bash
python azure_ml/workspace_setup.py
```

This creates:
- Azure ML workspace
- Compute cluster for training
- Storage for models

### Step 4: Train and Register Model

```bash
# Run training pipeline
python azure_ml/pipelines/llm_pipeline.py

# This will:
# 1. Download and prepare model
# 2. Evaluate model
# 3. Register model in Azure ML
```

### Step 5: Deploy to Managed Endpoint

```bash
# Deploy model to production endpoint
python azure_ml/deployment/deploy_to_aks.py

# Or use managed endpoint
python azure_ml/endpoints/managed_endpoint.py
```

### Step 6: Configure Web Frontend

```bash
# Add Azure ML endpoint configuration
export AZURE_ML_ENDPOINT_NAME="llm-inference-endpoint"

# Web frontend will automatically use Azure ML if available
# Falls back to Kafka if Azure ML is not configured
```

### Step 7: Test Integration

```bash
# Start web frontend
cd web
python -m web.main

# Open browser
open http://localhost:8000

# Send inference request
# Web frontend will use Azure ML endpoint automatically
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Azure ML Pipeline

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  train-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r azure_ml/requirements.txt
      
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Run Training Pipeline
        run: |
          python azure_ml/pipelines/llm_pipeline.py
        env:
          AZURE_ML_SUBSCRIPTION_ID: ${{ secrets.AZURE_ML_SUBSCRIPTION_ID }}
          AZURE_ML_RESOURCE_GROUP_NAME: ${{ secrets.AZURE_ML_RESOURCE_GROUP_NAME }}
          AZURE_ML_WORKSPACE_NAME: ${{ secrets.AZURE_ML_WORKSPACE_NAME }}
      
      - name: Deploy to Production
        run: |
          python azure_ml/deployment/deploy_to_aks.py
```

## 📊 Monitoring and Observability

### 1. Model Performance Monitoring

```python
from azure.ai.ml import MLClient
from azure.ai.ml.monitoring import ModelMonitor

# Set up model monitoring
monitor = ModelMonitor(
    compute="monitoring-cluster",
    target=endpoint,
    baseline_dataset=baseline_data,
    signals=[
        DataDriftSignal(),
        PredictionDriftSignal(),
        FeatureAttributionDriftSignal()
    ]
)
```

### 2. Experiment Tracking

```python
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Experiment

# Create experiment
experiment = ml_client.experiments.create_or_update(
    Experiment(
        name="llm-training-experiment",
        description="LLM model training experiments"
    )
)

# Log metrics
ml_client.experiments.log_metric(
    experiment_name="llm-training-experiment",
    run_id=run.id,
    metric_name="accuracy",
    value=0.95
)
```

### 3. Endpoint Monitoring

```python
# Get endpoint metrics
metrics = ml_client.online_endpoints.get_metrics(
    endpoint_name="llm-inference-endpoint",
    metric_names=["requests_per_minute", "latency", "error_rate"]
)
```

## 🎯 Production Best Practices

### 1. Model Versioning

```python
# Register model with version
model = Model(
    path="./model",
    name="llm-model",
    version="1.0.0",
    description="Production model v1.0.0"
)
ml_client.models.create_or_update(model)
```

### 2. A/B Testing

```python
# Deploy multiple versions
deployment_v1 = ManagedOnlineDeployment(
    name="v1",
    model=model_v1,
    traffic_percent=50
)

deployment_v2 = ManagedOnlineDeployment(
    name="v2",
    model=model_v2,
    traffic_percent=50
)
```

### 3. Auto-scaling

```python
# Configure auto-scaling
deployment = ManagedOnlineDeployment(
    name="blue",
    model=model,
    instance_count=2,
    scale_settings={
        "min_instances": 1,
        "max_instances": 10,
        "target_utilization": 70
    }
)
```

### 4. Health Checks

```python
# Configure health checks
deployment = ManagedOnlineDeployment(
    name="blue",
    model=model,
    liveness_probe={
        "initial_delay_seconds": 60,
        "period_seconds": 10,
        "timeout_seconds": 5,
        "failure_threshold": 3
    }
)
```

## 🔐 Security

### 1. Managed Identity

```python
# Use managed identity for authentication
from azure.identity import ManagedIdentityCredential

credential = ManagedIdentityCredential()
ml_client = MLClient(credential, ...)
```

### 2. Private Endpoints

```python
# Create private endpoint
endpoint = ManagedOnlineEndpoint(
    name="llm-endpoint",
    public_network_access="disabled"  # Private only
)
```

### 3. Key Vault Integration

```python
# Store secrets in Key Vault
from azure.keyvault.secrets import SecretClient

secret_client = SecretClient(
    vault_url="https://your-vault.vault.azure.net/",
    credential=DefaultAzureCredential()
)

api_key = secret_client.get_secret("ml-endpoint-key").value
```

## 💰 Cost Optimization

### 1. Auto-scale to Zero

```python
# Scale to zero when not in use
deployment = ManagedOnlineDeployment(
    name="blue",
    model=model,
    scale_settings={
        "min_instances": 0,  # Scale to zero
        "max_instances": 10
    }
)
```

### 2. Spot Instances for Training

```python
# Use spot instances for training
compute = AmlCompute(
    name="training-cluster",
    vm_size="Standard_NC6s_v3",
    min_instances=0,
    max_instances=4,
    low_priority_nodes=4  # Use spot instances
)
```

### 3. Reserved Instances

- Purchase reserved instances for predictable workloads
- Use Azure Hybrid Benefit for cost savings

## 📈 Performance Optimization

### 1. Model Optimization

```python
# Quantize model for faster inference
from transformers import AutoModelForCausalLM
import torch

model = AutoModelForCausalLM.from_pretrained("microsoft/phi-2")
model = torch.quantization.quantize_dynamic(
    model, {torch.nn.Linear}, dtype=torch.qint8
)
```

### 2. Batch Inference

```python
# Use batch inference for multiple requests
batch_endpoint = BatchEndpoint(
    name="llm-batch-endpoint",
    compute="batch-cluster"
)
```

### 3. Caching

```python
# Cache common responses
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_inference(prompt_hash):
    return model.infer(prompt)
```

## 🚀 Next Steps

1. **Set up CI/CD**: Automate training and deployment
2. **Enable Monitoring**: Set up alerts and dashboards
3. **Implement A/B Testing**: Test new models safely
4. **Optimize Costs**: Use auto-scaling and spot instances
5. **Add Security**: Implement private endpoints and Key Vault

## 📚 Resources

- [Azure ML Documentation](https://learn.microsoft.com/en-us/azure/machine-learning/)
- [MLOps with Azure ML](https://learn.microsoft.com/en-us/azure/machine-learning/concept-mlops)
- [Model Management](https://learn.microsoft.com/en-us/azure/machine-learning/concept-model-management-and-deployment)
- [Best Practices](https://learn.microsoft.com/en-us/azure/machine-learning/concept-best-practices)
