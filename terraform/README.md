# Terraform Infrastructure for LLM Platform

This directory contains Terraform code to deploy the LLM Inference Platform to Azure.

## 🏗️ What Gets Deployed

- **Azure Kubernetes Service (AKS)** - Container orchestration
- **Azure Container Registry (ACR)** - Docker image storage
- **Azure Storage Account** - Persistent data storage
- **Azure Log Analytics** - Monitoring and logging
- **Virtual Network** - Network isolation
- **Kafka on AKS** - Message queue (or Azure Event Hubs)
- **Kubernetes Resources** - Namespaces, ConfigMaps, Secrets

## 📋 Prerequisites

1. **Azure CLI** installed and logged in:
   ```bash
   az login
   az account set --subscription <your-subscription-id>
   ```

2. **Terraform** installed (>= 1.0):
   ```bash
   # Download from https://www.terraform.io/downloads
   # Or use package manager
   ```

3. **kubectl** installed (for Kubernetes access)

4. **Docker** installed (for building images)

## 🚀 Quick Start

### 1. Configure Variables

```bash
# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
# Important: Update acr_name and storage_account_name to unique values
```

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

### 3. Plan Deployment

```bash
terraform plan
```

### 4. Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### 5. Get AKS Credentials

```bash
# After deployment, get kubeconfig
az aks get-credentials \
  --resource-group <resource-group-name> \
  --name <aks-cluster-name>

# Verify connection
kubectl get nodes
```

## 📝 Configuration

### Required Variables

Edit `terraform.tfvars`:

```hcl
project_name         = "llm-platform"
location             = "eastus"
resource_group_name  = "llm-platform-rg"
acr_name             = "your-unique-acr-name"      # Must be globally unique
storage_account_name = "youruniquestorage"         # Must be globally unique
```

### Optional Variables

- `enable_gpu_node_pool`: Enable GPU nodes for LLM inference
- `use_event_hubs`: Use Azure Event Hubs instead of Kafka
- `enable_application_gateway`: Enable Application Gateway for web frontend

## 🏗️ Infrastructure Details

### AKS Cluster

- **System Node Pool**: 2 nodes (Standard_D4s_v3)
- **GPU Node Pool**: Optional, for LLM workers
- **Auto-scaling**: Enabled
- **Network Plugin**: Azure CNI
- **RBAC**: Enabled

### Container Registry

- **SKU**: Standard
- **Admin Enabled**: Yes (for Kubernetes pull)

### Storage

- **Account Type**: Standard LRS
- **Kind**: StorageV2

## 📦 Building and Pushing Images

After infrastructure is deployed:

```bash
# Login to ACR
az acr login --name <acr-name>

# Build and push worker image
docker build -t <acr-name>.azurecr.io/llm-worker:latest -f docker/worker/Dockerfile .
docker push <acr-name>.azurecr.io/llm-worker:latest

# Build and push web image
docker build -t <acr-name>.azurecr.io/llm-web:latest -f docker/web/Dockerfile .
docker push <acr-name>.azurecr.io/llm-web:latest
```

## 🚢 Deploying Applications

### Option 1: Using kubectl

```bash
# Update image references in k8s manifests
# Then apply:
kubectl apply -f k8s/
```

### Option 2: Using Helm (if charts exist)

```bash
helm install llm-platform ./helm/llm-platform
```

## 🔍 Monitoring

Access Log Analytics:
```bash
# View logs in Azure Portal
# Or use Azure CLI:
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "KubePodInventory | take 10"
```

## 💰 Cost Estimation

Approximate monthly costs (varies by region):

- **AKS Cluster** (2 nodes, Standard_D4s_v3): ~$200-300/month
- **ACR** (Standard): ~$5/month
- **Storage Account**: ~$1-5/month
- **Log Analytics**: ~$50-100/month (depending on data)
- **Network**: ~$10-20/month

**Total**: ~$266-430/month (without GPU nodes)

GPU nodes add significant cost:
- Standard_NC6s_v3: ~$1,000/month per node

## 🗑️ Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all resources. Make sure you have backups!

## 🔧 Troubleshooting

### Terraform fails with "name already exists"

- ACR and Storage Account names must be globally unique
- Change names in `terraform.tfvars`

### AKS deployment fails

- Check Azure quotas: `az vm list-usage --location eastus`
- Verify subscription has AKS permissions
- Check network connectivity

### Cannot connect to AKS

```bash
# Refresh credentials
az aks get-credentials --resource-group <rg> --name <cluster> --overwrite-existing

# Verify
kubectl get nodes
```

## 📚 Additional Resources

- [Terraform Azure Provider Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [AKS Documentation](https://docs.microsoft.com/en-us/azure/aks/)
- [ACR Documentation](https://docs.microsoft.com/en-us/azure/container-registry/)

## 🔐 Security Best Practices

1. **Enable RBAC** on AKS (already enabled)
2. **Use Managed Identity** (already configured)
3. **Enable Network Policies** (consider adding)
4. **Rotate ACR passwords** regularly
5. **Use Azure Key Vault** for secrets (consider adding)
6. **Enable AKS Private Cluster** for production

## 📝 Next Steps

After infrastructure is deployed:

1. Build and push Docker images to ACR
2. Deploy Kubernetes manifests (see `k8s/` directory)
3. Configure ingress for web frontend
4. Set up monitoring and alerting
5. Configure backup and disaster recovery
