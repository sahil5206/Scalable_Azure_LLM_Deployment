# Azure ML Quick Start Guide

Get started with Azure ML in 5 minutes!

## Prerequisites

- Azure subscription
- Python 3.9+
- Azure CLI (optional, for authentication)

## Step 1: Install Dependencies (1 minute)

```bash
pip install -r azure_ml/requirements.txt
```

## Step 2: Authenticate (1 minute)

```bash
# Option 1: Azure CLI (recommended)
az login

# Option 2: Will prompt for browser login if needed
# (automatic when running scripts)
```

## Step 3: Create Workspace (2 minutes)

```bash
# Set your Azure details
export AZURE_ML_SUBSCRIPTION_ID="<your-subscription-id>"
export AZURE_ML_RESOURCE_GROUP_NAME="<your-resource-group>"
export AZURE_ML_WORKSPACE_NAME="<your-workspace-name>"

# Create workspace and compute
python azure_ml/workspace_setup.py
```

**Or create via Azure Portal:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Machine Learning"
3. Create new workspace
4. Note the subscription ID, resource group, and workspace name

## Step 4: Run Your First Pipeline (1 minute)

```bash
# Training pipeline
python azure_ml/pipelines/llm_pipeline.py
```

This will:
- Download the model
- Evaluate it
- Register it in Azure ML

## Step 5: View Results

The script will output a URL like:
```
View pipeline at: https://ml.azure.com/...
```

Click the URL to see:
- Pipeline execution
- Logs and outputs
- Metrics and artifacts

## Next Steps

### Test Kafka Integration

If you have Kafka running:

```bash
# Set Kafka configuration
export KAFKA_BOOTSTRAP_SERVERS="<your-kafka-server>:9092"

# Run inference pipeline
python azure_ml/pipelines/inference_pipeline.py
```

### Deploy Managed Endpoint

```python
from azure_ml.endpoints.managed_endpoint import create_managed_endpoint
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

ml_client = MLClient(
    DefaultAzureCredential(),
    subscription_id="<subscription-id>",
    resource_group_name="<resource-group>",
    workspace_name="<workspace-name>"
)

create_managed_endpoint(
    ml_client=ml_client,
    endpoint_name="llm-endpoint",
    instance_type="Standard_NC6s_v3"
)
```

## Configuration File (Optional)

Create `.env` file in project root:

```bash
# Azure ML
AZURE_ML_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_ML_RESOURCE_GROUP_NAME=<your-resource-group>
AZURE_ML_WORKSPACE_NAME=<your-workspace-name>
AZURE_ML_LOCATION=eastus

# Compute
AZURE_ML_COMPUTE_CLUSTER_NAME=llm-compute-cluster
AZURE_ML_COMPUTE_VM_SIZE=Standard_NC6s_v3
AZURE_ML_COMPUTE_MIN_NODES=0
AZURE_ML_COMPUTE_MAX_NODES=4

# Kafka (if using)
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

## Troubleshooting

### "Subscription not found"
- Verify subscription ID: `az account show`
- Check you're logged in: `az account list`

### "Resource group not found"
- Create resource group: `az group create --name <name> --location eastus`
- Or use existing resource group

### "Workspace creation failed"
- Check permissions (need Contributor or Owner role)
- Verify resource group exists

### "Compute cluster creation failed"
- Check quota limits in Azure Portal
- Try smaller VM size: `Standard_DS3_v2`

## Cost Estimate

**Free Tier:**
- First month: Free compute hours
- Great for experimentation

**Pay-as-you-go:**
- Compute: ~$0.50-2.00/hour (depending on VM size)
- Storage: ~$0.05/GB/month
- Only pay when running pipelines

**Cost Optimization:**
- Use `min_nodes=0` (scale to zero)
- Use spot instances for training
- Delete unused resources

## Support

- Check logs in Azure ML Studio
- Review [Azure ML Documentation](https://learn.microsoft.com/en-us/azure/machine-learning/)
- See `azure_ml/README.md` for detailed documentation
