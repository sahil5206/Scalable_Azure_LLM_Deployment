# Complete Deployment Guide - LLM Inference Platform

**Step-by-step guide to deploy and run the entire project from scratch.**

This guide covers everything you need to deploy the LLM Inference Platform with Azure Machine Learning integration to Azure.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure Setup](#azure-setup)
3. [Local Development Setup](#local-development-setup)
4. [Azure ML Workspace Setup](#azure-ml-workspace-setup)
5. [Infrastructure Deployment (Terraform)](#infrastructure-deployment-terraform)
6. [Jenkins CI/CD Setup](#jenkins-cicd-setup)
7. [Build and Push Docker Images](#build-and-push-docker-images)
8. [Deploy to Azure Kubernetes Service](#deploy-to-azure-kubernetes-service)
9. [Monitoring Setup (Prometheus & Grafana)](#monitoring-setup-prometheus--grafana)
10. [Configure and Test](#configure-and-test)
11. [Access the Application](#access-the-application)
12. [CI/CD Pipeline Usage](#cicd-pipeline-usage)
13. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

1. **Azure CLI** (latest version)
   ```bash
   # Windows (PowerShell)
   winget install -e --id Microsoft.AzureCLI
   
   # macOS
   brew install azure-cli
   
   # Linux
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

2. **Terraform** (>= 1.0)
   ```bash
   # Windows (chocolatey)
   choco install terraform
   
   # macOS
   brew install terraform
   
   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

3. **Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

4. **kubectl** (Kubernetes CLI)
   ```bash
   # Windows
   choco install kubernetes-cli
   
   # macOS
   brew install kubectl
   
   # Linux
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   ```

5. **Python 3.9+**
   ```bash
   # Verify installation
   python --version
   pip --version
   ```

6. **Git**
   ```bash
   # Verify installation
   git --version
   ```

### Azure Account Requirements

- Active Azure subscription
- Owner or Contributor role on the subscription
- Sufficient quota for:
  - AKS cluster (2+ nodes)
  - Container Registry
  - Storage Account
  - Azure ML workspace

---

## Azure Setup

### Step 1: Login to Azure

```bash
# Login to Azure
az login

# If you have multiple subscriptions, select the correct one
az account list --output table
az account set --subscription "<your-subscription-id>"

# Verify current subscription
az account show
```

### Step 2: Create Resource Group

```bash
# Set variables (customize as needed)
RESOURCE_GROUP_NAME="llm-platform-rg"
LOCATION="eastus"

# Create resource group
az group create \
  --name $RESOURCE_GROUP_NAME \
  --location $LOCATION

# Verify
az group show --name $RESOURCE_GROUP_NAME
```

### Step 3: Enable Required Azure Providers

```bash
# Register required providers
az provider register --namespace Microsoft.ContainerService
az provider register --namespace Microsoft.MachineLearningServices
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.ContainerRegistry

# Wait for registration (may take a few minutes)
az provider show --namespace Microsoft.ContainerService --query "registrationState"
az provider show --namespace Microsoft.MachineLearningServices --query "registrationState"
```

---

## Local Development Setup

### Step 1: Clone/Navigate to Project

```bash
# If using git
git clone <your-repo-url>
cd LLM_Deployement_Azure

# Or navigate to existing project
cd C:\Users\Dell\Documents\LLM_Deployement_Azure
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (CMD)
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
# Install worker dependencies
cd worker
pip install -r requirements.txt
cd ..

# Install web frontend dependencies
cd web
pip install -r requirements.txt
cd ..

# Install Azure ML dependencies
cd azure_ml
pip install -r requirements.txt
cd ..
```

### Step 4: Test Local Setup (Optional)

```bash
# Start Kafka locally
docker-compose up -d kafka zookeeper

# Wait for Kafka to be ready (30 seconds)
timeout /t 30  # Windows
sleep 30       # macOS/Linux

# Test worker (in one terminal)
cd worker
python -m worker.main

# Test web frontend (in another terminal)
cd web
python -m web.main

# Open browser: http://localhost:8000
# Stop with Ctrl+C when done testing
```

---

## Azure ML Workspace Setup

### Step 1: Create Azure ML Workspace

```bash
# Set variables
AZURE_ML_WORKSPACE_NAME="llm-ml-workspace"
RESOURCE_GROUP_NAME="llm-platform-rg"
LOCATION="eastus"

# Create Azure ML workspace
az ml workspace create \
  --name $AZURE_ML_WORKSPACE_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --location $LOCATION

# Verify workspace creation
az ml workspace show \
  --name $AZURE_ML_WORKSPACE_NAME \
  --resource-group $RESOURCE_GROUP_NAME
```

### Step 2: Configure Azure ML Environment Variables

```bash
# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create .env file in project root
cat > .env << EOF
# Azure ML Configuration
AZURE_ML_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
AZURE_ML_RESOURCE_GROUP_NAME=$RESOURCE_GROUP_NAME
AZURE_ML_WORKSPACE_NAME=$AZURE_ML_WORKSPACE_NAME
AZURE_ML_LOCATION=$LOCATION

# Compute Configuration
AZURE_ML_COMPUTE_CLUSTER_NAME=llm-compute-cluster
AZURE_ML_COMPUTE_VM_SIZE=Standard_NC6s_v3
AZURE_ML_COMPUTE_MIN_NODES=0
AZURE_ML_COMPUTE_MAX_NODES=4

# Endpoint Configuration
AZURE_ML_ENDPOINT_NAME=llm-inference-endpoint
AZURE_ML_ENDPOINT_INSTANCE_TYPE=Standard_NC6s_v3
AZURE_ML_ENDPOINT_INSTANCE_COUNT=2

# Model Configuration
AZURE_ML_DEFAULT_MODEL_NAME=microsoft/phi-2
EOF

# Or set environment variables directly
export AZURE_ML_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
export AZURE_ML_RESOURCE_GROUP_NAME=$RESOURCE_GROUP_NAME
export AZURE_ML_WORKSPACE_NAME=$AZURE_ML_WORKSPACE_NAME
```

### Step 3: Run Azure ML Setup Script

```bash
# Navigate to project root
cd C:\Users\Dell\Documents\LLM_Deployement_Azure

# Run setup script
python azure_ml/workspace_setup.py

# This will:
# - Verify workspace exists
# - Create compute cluster
# - Set up storage
```

### Step 4: Train and Register Model

```bash
# Run training pipeline
python azure_ml/pipelines/llm_pipeline.py

# This will:
# - Download model from HuggingFace
# - Prepare model
# - Evaluate model
# - Register model in Azure ML

# Wait for pipeline to complete (10-30 minutes depending on model size)
# Check status in Azure ML Studio: https://ml.azure.com
```

---

## Infrastructure Deployment (Terraform)

### Step 1: Configure Terraform Variables

```bash
# Navigate to terraform directory
cd terraform

# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
# IMPORTANT: Update these values to be unique:
# - acr_name: Must be globally unique (lowercase, alphanumeric, 5-50 chars)
# - storage_account_name: Must be globally unique (lowercase, alphanumeric, 3-24 chars)
# - aks_cluster_name: Must be unique in your subscription
```

**Example `terraform.tfvars`:**

```hcl
project_name         = "llm-platform"
location             = "eastus"
resource_group_name  = "llm-platform-rg"

# AKS Configuration
aks_cluster_name     = "llm-aks-cluster"
kubernetes_version   = "1.28"
aks_system_node_count = 2
aks_node_vm_size     = "Standard_D4s_v3"

# GPU Node Pool (optional, for LLM inference)
enable_gpu_node_pool = true
gpu_node_count       = 0  # Start with 0, scale up as needed
gpu_node_max_count   = 4
gpu_node_vm_size     = "Standard_NC6s_v3"

# Container Registry (MUST BE UNIQUE - change this!)
acr_name             = "llmplatformacr123"  # Change to unique name

# Storage Account (MUST BE UNIQUE - change this!)
storage_account_name = "llmplatformstg123"  # Change to unique name

# Event Hubs (optional)
use_event_hubs       = false

# Application Gateway (optional)
enable_application_gateway = false

# Tags
tags = {
  Environment = "production"
  Project     = "LLM-Inference"
  ManagedBy   = "Terraform"
}
```

### Step 2: Initialize Terraform

```bash
# Make sure you're in terraform directory
cd terraform

# Initialize Terraform
terraform init

# This downloads required providers
# Should see: "Terraform has been successfully initialized!"
```

### Step 3: Plan Terraform Deployment

```bash
# Review what will be created
terraform plan

# Review the output carefully:
# - Resource group
# - AKS cluster
# - Container Registry
# - Storage Account
# - Virtual Network
# - Log Analytics Workspace
```

### Step 4: Apply Terraform Configuration

```bash
# Deploy infrastructure
terraform apply

# Type 'yes' when prompted
# This will take 15-30 minutes

# Wait for completion
# You should see: "Apply complete!"
```

### Step 5: Get Outputs

```bash
# Get important outputs
terraform output

# Save AKS credentials
az aks get-credentials \
  --resource-group $(terraform output -raw resource_group_name) \
  --name $(terraform output -raw aks_cluster_name) \
  --overwrite-existing

# Verify AKS connection
kubectl get nodes

# You should see 2 nodes (or more if GPU pool enabled)

# Note: Save these values for Jenkins configuration
ACR_NAME=$(terraform output -raw acr_login_server | cut -d'.' -f1)
echo "ACR Name: $ACR_NAME"
echo "Save this for Jenkins credentials configuration"
```

### Step 6: Verify Infrastructure

```bash
# Check AKS cluster
az aks show \
  --resource-group llm-platform-rg \
  --name llm-aks-cluster

# Check Container Registry
az acr list --resource-group llm-platform-rg

# Check Storage Account
az storage account list --resource-group llm-platform-rg

# Save ACR name for later use
ACR_NAME=$(terraform output -raw acr_login_server | cut -d'.' -f1)
echo "ACR_NAME=$ACR_NAME" >> .env
```

---

## Jenkins CI/CD Setup

### Step 1: Deploy Jenkins to AKS

```bash
# Create Jenkins namespace
kubectl create namespace jenkins

# Deploy Jenkins
kubectl apply -f jenkins/k8s/jenkins-deployment.yaml

# Wait for Jenkins to be ready (5-10 minutes)
kubectl wait --for=condition=ready pod -l app=jenkins -n jenkins --timeout=600s

# Or use setup script
bash jenkins/scripts/setup_jenkins.sh
```

### Step 2: Get Jenkins Access Information

```bash
# Get Jenkins admin password
kubectl exec -it deployment/jenkins -n jenkins -- \
  cat /var/jenkins_home/secrets/initialAdminPassword

# Get Jenkins URL
kubectl get service jenkins -n jenkins

# Or use port forwarding for local access
kubectl port-forward service/jenkins 8080:80 -n jenkins
# Access at: http://localhost:8080
```

### Step 3: Initial Jenkins Configuration

1. **Access Jenkins UI**
   - Open Jenkins URL (LoadBalancer IP or localhost:8080 if port-forwarding)
   - Enter admin password from Step 2
   - Click "Install suggested plugins"
   - Wait for installation (5-10 minutes)
   - Create admin user or continue with admin

2. **Install Required Plugins**
   Go to: **Manage Jenkins** → **Plugins** → **Available plugins**
   
   Install:
   - Azure CLI Plugin
   - Kubernetes CLI Plugin
   - Docker Pipeline Plugin
   - Credentials Binding Plugin
   - Git Plugin (usually pre-installed)

3. **Configure Azure CLI in Jenkins**
   ```bash
   # SSH into Jenkins pod
   kubectl exec -it deployment/jenkins -n jenkins -- bash
   
   # Install Azure CLI (if not present)
   curl -sL https://aka.ms/InstallAzureCLIDeb | bash
   
   # Login to Azure
   az login
   # Follow browser login instructions
   
   # Set default subscription
   az account set --subscription "<your-subscription-id>"
   
   # Verify
   az account show
   ```

### Step 4: Configure Jenkins Credentials

Go to: **Manage Jenkins** → **Credentials** → **System** → **Global credentials (unrestricted)** → **Add Credentials**

Add the following credentials:

1. **Azure Subscription ID**
   - Kind: **Secret text**
   - Secret: `<your-subscription-id>`
   - ID: `azure-subscription-id`
   - Description: `Azure Subscription ID`

2. **ACR Name**
   - Kind: **Secret text**
   - Secret: `<your-acr-name>` (e.g., `llmplatformacr123`)
   - ID: `acr-name`
   - Description: `Azure Container Registry Name`

3. **Azure Resource Group**
   - Kind: **Secret text**
   - Secret: `llm-platform-rg`
   - ID: `azure-resource-group`
   - Description: `Azure Resource Group Name`

4. **Azure ML Workspace**
   - Kind: **Secret text**
   - Secret: `llm-ml-workspace`
   - ID: `azure-ml-workspace`
   - Description: `Azure ML Workspace Name`

### Step 5: Configure Kubernetes Access for Jenkins

```bash
# Create service account for Jenkins (if not exists)
kubectl create serviceaccount jenkins -n jenkins --dry-run=client -o yaml | kubectl apply -f -

# Grant cluster-admin permissions (for deployment)
kubectl create clusterrolebinding jenkins-cluster-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=jenkins:jenkins \
  --dry-run=client -o yaml | kubectl apply -f -

# Verify access
kubectl exec -it deployment/jenkins -n jenkins -- kubectl get nodes
```

### Step 6: Create Jenkins Pipeline Job

1. **Create New Pipeline**
   - Click "New Item" in Jenkins dashboard
   - Enter name: `llm-platform-pipeline`
   - Select "Pipeline"
   - Click OK

2. **Configure Pipeline**
   - Scroll to "Pipeline" section
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: Your repository URL (or file path if local)
   - **Credentials**: Add if repository is private
   - **Branch Specifier**: `*/main` (or your main branch)
   - **Script Path**: `jenkins/Jenkinsfile`
   - Click Save

3. **Test Pipeline**
   - Click "Build Now" on the pipeline job
   - Watch build progress
   - Check console output for any errors

### Step 7: Create Staging Namespace (for Staging Deployments)

```bash
# Create staging namespace
kubectl create namespace llm-platform-staging

# Copy secrets to staging namespace
kubectl get secret acr-secret -n llm-platform -o yaml | \
  sed 's/namespace: llm-platform/namespace: llm-platform-staging/' | \
  kubectl apply -f -

# Copy configmap to staging namespace
kubectl get configmap llm-app-config -n llm-platform -o yaml | \
  sed 's/namespace: llm-platform/namespace: llm-platform-staging/' | \
  kubectl apply -f -
```

### Step 8: Verify Jenkins Setup

```bash
# Check Jenkins pod status
kubectl get pods -n jenkins

# Check Jenkins service
kubectl get service jenkins -n jenkins

# View Jenkins logs
kubectl logs -f deployment/jenkins -n jenkins

# Test Jenkins API
curl http://<jenkins-ip>/api/json
```

---

## Build and Push Docker Images

**Note**: If using Jenkins CI/CD, this step is automated. You can skip manual build/push and let Jenkins handle it.

### Manual Build (Optional - Jenkins does this automatically)

### Step 1: Login to Azure Container Registry

```bash
# Get ACR name from Terraform output
ACR_NAME=$(terraform output -raw acr_login_server | cut -d'.' -f1)

# Login to ACR
az acr login --name $ACR_NAME

# Or use full name
az acr login --name llmplatformacr123  # Use your ACR name
```

### Step 2: Build Worker Image

```bash
# Navigate to project root
cd C:\Users\Dell\Documents\LLM_Deployement_Azure

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)

# Build worker image
docker build \
  -f docker/worker/Dockerfile \
  -t $ACR_LOGIN_SERVER/llm-worker:latest \
  -t $ACR_LOGIN_SERVER/llm-worker:v1.0.0 \
  .

# This will take 10-20 minutes (downloads model)
```

### Step 3: Build Web Frontend Image

```bash
# Build web frontend image
docker build \
  -f docker/web/Dockerfile \
  -t $ACR_LOGIN_SERVER/llm-web:latest \
  -t $ACR_LOGIN_SERVER/llm-web:v1.0.0 \
  .

# This should be faster (5-10 minutes)
```

### Step 4: Push Images to ACR

```bash
# Push worker image
docker push $ACR_LOGIN_SERVER/llm-worker:latest
docker push $ACR_LOGIN_SERVER/llm-worker:v1.0.0

# Push web frontend image
docker push $ACR_LOGIN_SERVER/llm-web:latest
docker push $ACR_LOGIN_SERVER/llm-web:v1.0.0

# Verify images
az acr repository list --name $ACR_NAME
az acr repository show-tags --name $ACR_NAME --repository llm-worker
az acr repository show-tags --name $ACR_NAME --repository llm-web
```

---

## Deploy to Azure Kubernetes Service

### Step 1: Create Kubernetes Namespace

```bash
# Create namespace
kubectl create namespace llm-platform

# Verify
kubectl get namespaces
```

### Step 2: Create Kubernetes Secrets

```bash
# Get ACR credentials
ACR_NAME=$(terraform output -raw acr_login_server | cut -d'.' -f1)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Create secret for pulling images
kubectl create secret docker-registry acr-secret \
  --docker-server=$(terraform output -raw acr_login_server) \
  --docker-username=$ACR_USERNAME \
  --docker-password=$ACR_PASSWORD \
  --namespace llm-platform

# Verify secret
kubectl get secrets -n llm-platform
```

### Step 3: Deploy Kafka (if not using Event Hubs)

```bash
# Apply Kafka deployment
kubectl apply -f terraform/kubernetes.tf  # This creates Kafka resources

# Or deploy manually:
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zookeeper
  namespace: llm-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: zookeeper
  template:
    metadata:
      labels:
        app: zookeeper
    spec:
      containers:
      - name: zookeeper
        image: confluentinc/cp-zookeeper:7.5.0
        ports:
        - containerPort: 2181
        env:
        - name: ZOOKEEPER_CLIENT_PORT
          value: "2181"
---
apiVersion: v1
kind: Service
metadata:
  name: zookeeper
  namespace: llm-platform
spec:
  selector:
    app: zookeeper
  ports:
  - port: 2181
    targetPort: 2181
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka
  namespace: llm-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
      - name: kafka
        image: confluentinc/cp-kafka:7.5.0
        ports:
        - containerPort: 9092
        env:
        - name: KAFKA_BROKER_ID
          value: "1"
        - name: KAFKA_ZOOKEEPER_CONNECT
          value: "zookeeper:2181"
        - name: KAFKA_ADVERTISED_LISTENERS
          value: "PLAINTEXT://kafka:9092"
        - name: KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR
          value: "1"
---
apiVersion: v1
kind: Service
metadata:
  name: kafka
  namespace: llm-platform
spec:
  selector:
    app: kafka
  ports:
  - port: 9092
    targetPort: 9092
EOF

# Wait for Kafka to be ready
kubectl wait --for=condition=ready pod -l app=kafka -n llm-platform --timeout=300s
```

### Step 4: Create ConfigMap for Application Configuration

```bash
# Get ACR login server
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)

# Create ConfigMap
kubectl create configmap llm-app-config \
  --from-literal=KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  --from-literal=KAFKA_REQUEST_TOPIC=llm-requests \
  --from-literal=KAFKA_RESPONSE_TOPIC=llm-responses \
  --from-literal=MODEL_NAME=microsoft/phi-2 \
  --from-literal=BATCH_SIZE=4 \
  --namespace llm-platform
```

### Step 5: Deploy Worker Service

```bash
# Get ACR login server
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)

# Create worker deployment
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-worker
  namespace: llm-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: llm-worker
  template:
    metadata:
      labels:
        app: llm-worker
    spec:
      imagePullSecrets:
      - name: acr-secret
      containers:
      - name: worker
        image: $ACR_LOGIN_SERVER/llm-worker:latest
        imagePullPolicy: Always
        envFrom:
        - configMapRef:
            name: llm-app-config
        env:
        - name: KAFKA_CONSUMER_GROUP
          value: "llm-worker-group"
        - name: METRICS_PORT
          value: "8080"
        - name: HEALTH_CHECK_PORT
          value: "8081"
        ports:
        - containerPort: 8080
          name: metrics
        - containerPort: 8081
          name: health
        resources:
          requests:
            cpu: "2"
            memory: "8Gi"
          limits:
            cpu: "4"
            memory: "16Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 120
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8081
          initialDelaySeconds: 60
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: llm-worker
  namespace: llm-platform
spec:
  selector:
    app: llm-worker
  ports:
  - port: 8080
    name: metrics
  - port: 8081
    name: health
  type: ClusterIP
EOF

# Wait for worker to be ready
kubectl wait --for=condition=ready pod -l app=llm-worker -n llm-platform --timeout=600s
```

### Step 6: Deploy Web Frontend

```bash
# Get ACR login server and Azure ML endpoint name
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)
AZURE_ML_ENDPOINT_NAME="llm-inference-endpoint"  # Or get from Azure ML

# Create web frontend deployment
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-web
  namespace: llm-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: llm-web
  template:
    metadata:
      labels:
        app: llm-web
    spec:
      imagePullSecrets:
      - name: acr-secret
      containers:
      - name: web
        image: $ACR_LOGIN_SERVER/llm-web:latest
        imagePullPolicy: Always
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:9092"
        - name: KAFKA_REQUEST_TOPIC
          value: "llm-requests"
        - name: KAFKA_RESPONSE_TOPIC
          value: "llm-responses"
        - name: PORT
          value: "8000"
        - name: AZURE_ML_ENDPOINT_NAME
          value: "$AZURE_ML_ENDPOINT_NAME"
        - name: AZURE_ML_SUBSCRIPTION_ID
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: subscription-id
        - name: AZURE_ML_RESOURCE_GROUP_NAME
          value: "llm-platform-rg"
        - name: AZURE_ML_WORKSPACE_NAME
          value: "llm-ml-workspace"
        ports:
        - containerPort: 8000
          name: http
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: llm-web
  namespace: llm-platform
spec:
  selector:
    app: llm-web
  ports:
  - port: 80
    targetPort: 8000
    name: http
  type: LoadBalancer
EOF

# Create Azure credentials secret (if using Azure ML)
kubectl create secret generic azure-credentials \
  --from-literal=subscription-id=$AZURE_ML_SUBSCRIPTION_ID \
  --namespace llm-platform
```

### Step 7: Wait for Services to be Ready

```bash
# Check pod status
kubectl get pods -n llm-platform

# Watch until all pods are Running
kubectl get pods -n llm-platform -w

# Check services
kubectl get services -n llm-platform

# Get external IP for web frontend
kubectl get service llm-web -n llm-platform
```

---

## Configure and Test

### Step 1: Verify All Services are Running

```bash
# Check all pods
kubectl get pods -n llm-platform

# Should see:
# - zookeeper-xxx (Running)
# - kafka-xxx (Running)
# - llm-worker-xxx (Running, 2 replicas)
# - llm-web-xxx (Running, 2 replicas)

# Check services
kubectl get services -n llm-platform

# Check logs if any pod is not running
kubectl logs <pod-name> -n llm-platform
```

### Step 2: Test Kafka Connection

```bash
# Test Kafka from worker pod
kubectl exec -it deployment/llm-worker -n llm-platform -- \
  python -c "from confluent_kafka import Consumer; c = Consumer({'bootstrap.servers': 'kafka:9092', 'group.id': 'test'}); print('Kafka connection OK')"
```

### Step 3: Test Worker Health

```bash
# Port forward to worker
kubectl port-forward service/llm-worker 8081:8081 -n llm-platform

# In another terminal, test health
curl http://localhost:8081/health
curl http://localhost:8081/ready

# Check metrics
curl http://localhost:8080/metrics
```

### Step 4: Test Web Frontend

```bash
# Get external IP
EXTERNAL_IP=$(kubectl get service llm-web -n llm-platform -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# If no external IP yet, wait a few minutes
# Or use port forwarding
kubectl port-forward service/llm-web 8000:80 -n llm-platform

# Test health endpoint
curl http://localhost:8000/health

# Test inference endpoint
curl -X POST http://localhost:8000/api/inference \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is machine learning?",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

---

## Access the Application

### Option 1: Using LoadBalancer External IP

```bash
# Get external IP
kubectl get service llm-web -n llm-platform

# Open in browser
# http://<EXTERNAL_IP>
```

### Option 2: Using Port Forwarding

```bash
# Port forward to web service
kubectl port-forward service/llm-web 8000:80 -n llm-platform

# Open in browser
# http://localhost:8000
```

### Option 3: Using Ingress (if configured)

```bash
# Get ingress hostname
kubectl get ingress -n llm-platform

# Access via hostname
# http://<ingress-hostname>
```

### Using the Web UI

1. Open the web interface in your browser
2. Enter a prompt (e.g., "What is machine learning?")
3. Adjust settings (max tokens, temperature)
4. Click "Generate Response"
5. Wait for response (may take 30-60 seconds first time as model loads)

---

## CI/CD Pipeline Usage

### Automatic Deployment

The Jenkins pipeline automatically:

1. **On Code Push to `main` branch**:
   - Builds Docker images
   - Pushes to ACR
   - Trains model (if enabled)
   - Deploys to production
   - Runs smoke tests

2. **On Code Push to `develop` or `staging` branch**:
   - Builds Docker images
   - Pushes to ACR
   - Deploys to staging environment
   - Runs smoke tests

### Manual Pipeline Trigger

1. **Trigger from Jenkins UI**:
   - Go to pipeline job
   - Click "Build with Parameters"
   - Select options
   - Click Build

2. **Trigger via API**:
   ```bash
   # Get Jenkins API token from: Manage Jenkins → Manage Users → Configure
   JENKINS_URL="http://<jenkins-ip>"
   JENKINS_USER="admin"
   JENKINS_TOKEN="<your-api-token>"
   
   # Trigger build
   curl -X POST \
     "$JENKINS_URL/job/llm-platform-pipeline/build" \
     --user "$JENKINS_USER:$JENKINS_TOKEN"
   ```

### Pipeline Stages

The pipeline includes these stages:

1. **Checkout**: Gets latest code
2. **Lint & Test**: Code quality checks
3. **Build Docker Images**: Builds worker and web images
4. **Push to ACR**: Pushes images to registry
5. **Azure ML Training**: Trains model (on main/develop)
6. **Deploy to Staging**: Deploys to staging (develop/staging branches)
7. **Deploy to Production**: Deploys to production (main branch)
8. **Smoke Tests**: Verifies deployment

### Monitoring Pipeline

```bash
# View pipeline status in Jenkins UI
# Or check via kubectl:
kubectl get pods -n jenkins

# View Jenkins logs
kubectl logs -f deployment/jenkins -n jenkins

# View build logs (from Jenkins UI)
# Go to: Pipeline → Build # → Console Output
```

### Pipeline Configuration

Edit `jenkins/Jenkinsfile` to customize:
- Build stages
- Deployment environments
- Test steps
- Notification settings

See [jenkins/README.md](jenkins/README.md) for detailed pipeline documentation.

---

## Monitoring Setup (Prometheus & Grafana)

### Step 1: Deploy Prometheus

```bash
# Create monitoring namespace
kubectl create namespace monitoring

# Deploy Prometheus configuration
kubectl apply -f monitoring/prometheus/prometheus-config.yaml

# Deploy Prometheus
kubectl apply -f monitoring/prometheus/prometheus-deployment.yaml

# Wait for Prometheus to be ready
kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=300s

# Get Prometheus URL
kubectl get service prometheus -n monitoring
```

### Step 2: Deploy Grafana

```bash
# Create Grafana admin password secret
kubectl create secret generic grafana-credentials \
  --from-literal=admin-password='<your-secure-password>' \
  --namespace monitoring

# Deploy Grafana
kubectl apply -f monitoring/grafana/grafana-deployment.yaml

# Wait for Grafana to be ready
kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=300s

# Get Grafana URL
kubectl get service grafana -n monitoring
```

### Step 3: Access Monitoring Dashboards

```bash
# Port forward for local access
kubectl port-forward service/prometheus 9090:80 -n monitoring
kubectl port-forward service/grafana 3000:80 -n monitoring

# Access:
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
#   Username: admin
#   Password: <password-from-secret>
```

### Step 4: Import Grafana Dashboard

1. **Access Grafana**: http://localhost:3000 (or LoadBalancer IP)
2. **Login**: admin / <your-password>
3. **Import Dashboard**:
   - Go to: **Dashboards** → **Import**
   - Upload: `monitoring/grafana/dashboards/llm-platform-dashboard.json`
   - Or paste JSON content
   - Select Prometheus data source
   - Click **Import**

### Step 5: Verify Metrics Collection

```bash
# Check Prometheus targets
# Access Prometheus UI → Status → Targets
# All targets should be "UP"

# Check metrics in Prometheus
# Go to: http://localhost:9090
# Try query: llm_worker_requests_total

# Verify Grafana can query Prometheus
# Go to: Grafana → Explore → Select Prometheus
# Try query: rate(llm_worker_requests_total[5m])
```

### Step 6: Configure Alerts (Optional)

```bash
# Add alert rules to Prometheus
kubectl create configmap prometheus-alerts \
  --from-file=alerts.yaml=monitoring/alerts/alerts.yaml \
  --namespace monitoring

# Update Prometheus deployment to include alerts
# Edit prometheus-deployment.yaml to mount alerts configmap
```

See [monitoring/README.md](monitoring/README.md) for detailed monitoring setup.

---

## Post-Deployment Configuration

### Step 1: Configure Azure ML Endpoint (if using)

```bash
# Deploy model to Azure ML managed endpoint
python azure_ml/deployment/deploy_to_aks.py

# Or use managed endpoint
python azure_ml/endpoints/managed_endpoint.py

# Update web frontend deployment with endpoint name
kubectl set env deployment/llm-web \
  AZURE_ML_ENDPOINT_NAME=llm-inference-endpoint \
  -n llm-platform

# Restart web pods to pick up new config
kubectl rollout restart deployment/llm-web -n llm-platform
```

### Step 2: Set Up Monitoring

**Prometheus & Grafana are already deployed** (see Monitoring Setup section above).

```bash
# Access Prometheus
kubectl port-forward service/prometheus 9090:80 -n monitoring
# Open: http://localhost:9090

# Access Grafana
kubectl port-forward service/grafana 3000:80 -n monitoring
# Open: http://localhost:3000

# View logs
kubectl logs -f deployment/llm-worker -n llm-platform
kubectl logs -f deployment/llm-web -n llm-platform

# View raw metrics
kubectl port-forward service/llm-worker 8080:8080 -n llm-platform
# Access: http://localhost:8080/metrics
```

### Step 3: Scale Services (if needed)

```bash
# Scale worker
kubectl scale deployment llm-worker --replicas=4 -n llm-platform

# Scale web frontend
kubectl scale deployment llm-web --replicas=3 -n llm-platform

# Verify scaling
kubectl get pods -n llm-platform
```

---

## Troubleshooting

### Issue: Terraform fails with "name already exists"

**Solution:**
```bash
# ACR and Storage Account names must be globally unique
# Update terraform.tfvars with unique names:
# - acr_name: Try adding random numbers/letters
# - storage_account_name: Try different name
```

### Issue: AKS deployment fails

**Solution:**
```bash
# Check Azure quotas
az vm list-usage --location eastus --output table

# Check subscription limits
az account show --query "{subscriptionId:id, tenantId:tenantId}"

# Verify you have Contributor or Owner role
az role assignment list --assignee $(az account show --query user.name -o tsv)
```

### Issue: Docker build fails

**Solution:**
```bash
# Check Docker is running
docker ps

# Check disk space
docker system df

# Clean up if needed
docker system prune -a

# Retry build
```

### Issue: Pods stuck in Pending

**Solution:**
```bash
# Check pod events
kubectl describe pod <pod-name> -n llm-platform

# Check node resources
kubectl top nodes

# Check if nodes are ready
kubectl get nodes

# Check resource quotas
kubectl describe quota -n llm-platform
```

### Issue: Cannot pull images from ACR

**Solution:**
```bash
# Verify ACR secret exists
kubectl get secret acr-secret -n llm-platform

# Recreate secret if needed
ACR_NAME="your-acr-name"
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)

kubectl create secret docker-registry acr-secret \
  --docker-server=$ACR_LOGIN_SERVER \
  --docker-username=$ACR_USERNAME \
  --docker-password=$ACR_PASSWORD \
  --namespace llm-platform \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Issue: Worker cannot connect to Kafka

**Solution:**
```bash
# Check Kafka is running
kubectl get pods -l app=kafka -n llm-platform

# Check Kafka service
kubectl get service kafka -n llm-platform

# Test from worker pod
kubectl exec -it deployment/llm-worker -n llm-platform -- \
  ping kafka

# Check worker logs
kubectl logs deployment/llm-worker -n llm-platform | grep -i kafka
```

### Issue: Web frontend shows errors

**Solution:**
```bash
# Check web frontend logs
kubectl logs deployment/llm-web -n llm-platform

# Check if Azure ML endpoint is configured (if using)
kubectl get deployment llm-web -n llm-platform -o yaml | grep AZURE_ML

# Test health endpoint
kubectl port-forward service/llm-web 8000:80 -n llm-platform
curl http://localhost:8000/health
```

### Issue: Jenkins pipeline fails

**Solution:**
```bash
# Check Jenkins pod status
kubectl get pods -n jenkins

# Check Jenkins logs
kubectl logs deployment/jenkins -n jenkins

# Verify credentials in Jenkins
# Go to: Manage Jenkins → Credentials → Check all credentials exist

# Test Azure CLI from Jenkins pod
kubectl exec -it deployment/jenkins -n jenkins -- az account show

# Test kubectl from Jenkins pod
kubectl exec -it deployment/jenkins -n jenkins -- kubectl get nodes

# Check Docker in Jenkins pod
kubectl exec -it deployment/jenkins -n jenkins -- docker ps
```

### Issue: Jenkins cannot deploy to AKS

**Solution:**
```bash
# Verify service account permissions
kubectl get clusterrolebinding jenkins-cluster-admin

# Test kubectl access
kubectl exec -it deployment/jenkins -n jenkins -- kubectl get namespaces

# Recreate service account if needed
kubectl delete clusterrolebinding jenkins-cluster-admin
kubectl create clusterrolebinding jenkins-cluster-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=jenkins:jenkins
```

### Issue: Model loading is slow

**Solution:**
- First request takes longer (model download and loading)
- Subsequent requests are faster
- Consider using smaller models for faster startup
- Pre-warm the model by sending a test request

### Issue: Out of memory errors

**Solution:**
```bash
# Check pod resources
kubectl top pods -n llm-platform

# Increase worker memory limits
kubectl set resources deployment llm-worker \
  --limits=memory=32Gi \
  --requests=memory=16Gi \
  -n llm-platform

# Or use GPU nodes
# Enable GPU node pool in terraform.tfvars
terraform apply
```

---

## Verification Checklist

Use this checklist to verify everything is working:

- [ ] Azure subscription active and accessible
- [ ] Resource group created
- [ ] Azure ML workspace created
- [ ] Terraform infrastructure deployed
- [ ] AKS cluster running and accessible
- [ ] Container Registry accessible
- [ ] **Jenkins deployed and accessible**
- [ ] **Jenkins plugins installed**
- [ ] **Jenkins credentials configured**
- [ ] **Jenkins pipeline job created**
- [ ] Docker images built and pushed (manual or via Jenkins)
- [ ] Kubernetes namespace created
- [ ] Secrets configured
- [ ] Kafka deployed and running
- [ ] Worker service deployed and running
- [ ] Web frontend deployed and running
- [ ] All pods in Running state
- [ ] Services have endpoints
- [ ] Web UI accessible
- [ ] Inference requests working
- [ ] Health checks passing
- [ ] Metrics accessible
- [ ] **Jenkins pipeline runs successfully**
- [ ] **CI/CD automated deployments working**
- [ ] **Prometheus deployed and scraping metrics**
- [ ] **Grafana deployed and accessible**
- [ ] **Grafana dashboard imported and showing data**
- [ ] **Alerts configured (optional)**

---

## Next Steps

After successful deployment:

1. **✅ CI/CD Setup**: Jenkins pipeline is configured and ready
   - Monitor pipeline runs
   - Configure notifications (Slack, Email)
   - Set up branch protection rules
2. **Enable Monitoring**: Set up Azure Monitor and alerts
3. **Configure Auto-scaling**: Set up HPA for automatic scaling
4. **Set up Backups**: Configure backup for models and data
5. **Security Hardening**: Enable private endpoints, network policies
6. **Cost Optimization**: Review and optimize resource usage
7. **Pipeline Optimization**: Add more test stages, security scanning

---

## Cleanup (When Done)

To remove all resources:

```bash
# Delete Kubernetes resources
kubectl delete namespace llm-platform

# Destroy Terraform infrastructure
cd terraform
terraform destroy

# Delete Azure ML workspace (optional)
az ml workspace delete \
  --name llm-ml-workspace \
  --resource-group llm-platform-rg

# Delete resource group (removes everything)
az group delete --name llm-platform-rg --yes --no-wait
```

---

## Support and Resources

- **Project Documentation**: See `README.md` and `ARCHITECTURE.md`
- **Azure ML Setup**: See `azure_ml/INDUSTRY_GRADE_SETUP.md`
- **Terraform Docs**: See `terraform/README.md`
- **Azure Documentation**: https://learn.microsoft.com/en-us/azure/
- **Kubernetes Docs**: https://kubernetes.io/docs/

---

## Quick Reference Commands

```bash
# Get AKS credentials
az aks get-credentials --resource-group llm-platform-rg --name llm-aks-cluster

# View pods
kubectl get pods -n llm-platform

# View logs
kubectl logs -f deployment/llm-worker -n llm-platform

# Port forward
kubectl port-forward service/llm-web 8000:80 -n llm-platform

# Scale deployment
kubectl scale deployment llm-worker --replicas=4 -n llm-platform

# Restart deployment
kubectl rollout restart deployment/llm-web -n llm-platform

# Get service external IP
kubectl get service llm-web -n llm-platform

# Jenkins commands
kubectl get pods -n jenkins
kubectl logs -f deployment/jenkins -n jenkins
kubectl port-forward service/jenkins 8080:80 -n jenkins
kubectl exec -it deployment/jenkins -n jenkins -- bash

# Trigger Jenkins pipeline
curl -X POST http://<jenkins-ip>/job/llm-platform-pipeline/build \
  --user admin:<api-token>
```

---

**Congratulations!** 🎉 Your LLM Inference Platform is now deployed and running on Azure!
