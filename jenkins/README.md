# Jenkins CI/CD Integration

Complete Jenkins CI/CD pipeline for automated building, testing, and deployment of the LLM Inference Platform.

## 🎯 Features

- ✅ **Automated Builds**: Build Docker images on code changes
- ✅ **Automated Testing**: Lint checks and unit tests
- ✅ **Multi-Stage Deployment**: Staging and Production environments
- ✅ **Azure ML Integration**: Automated model training and deployment
- ✅ **Rolling Updates**: Zero-downtime deployments
- ✅ **Smoke Tests**: Automated post-deployment verification

## 📋 Pipeline Stages

1. **Checkout**: Get latest code from repository
2. **Lint & Test**: Code quality checks and unit tests
3. **Build Docker Images**: Build worker and web images
4. **Push to ACR**: Push images to Azure Container Registry
5. **Azure ML Training**: Train and register models (on main/develop branches)
6. **Deploy to Staging**: Deploy to staging environment (develop/staging branches)
7. **Deploy to Production**: Deploy to production (main branch)
8. **Smoke Tests**: Verify deployment health

## 🚀 Setup Instructions

### Prerequisites

- Jenkins server (on AKS or standalone)
- Azure CLI configured
- kubectl configured
- Docker installed on Jenkins agent
- Azure Container Registry access

### Step 1: Deploy Jenkins to AKS

```bash
# Create Jenkins namespace
kubectl create namespace jenkins

# Deploy Jenkins
kubectl apply -f jenkins/k8s/jenkins-deployment.yaml

# Wait for Jenkins to be ready
kubectl wait --for=condition=ready pod -l app=jenkins -n jenkins --timeout=300s

# Get Jenkins admin password
kubectl exec -it deployment/jenkins -n jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword

# Get Jenkins URL
kubectl get service jenkins -n jenkins
```

### Step 2: Configure Jenkins

1. **Access Jenkins UI**
   - Open Jenkins URL (from LoadBalancer IP)
   - Enter admin password
   - Install suggested plugins

2. **Install Required Plugins**
   - Azure CLI Plugin
   - Kubernetes CLI Plugin
   - Docker Pipeline Plugin
   - Credentials Binding Plugin

3. **Configure Credentials**

   Go to: **Manage Jenkins** → **Credentials** → **System** → **Global credentials**

   Add the following credentials:

   - **azure-subscription-id** (Secret text)
     - Value: Your Azure subscription ID
   
   - **acr-name** (Secret text)
     - Value: Your ACR name (e.g., `llmplatformacr123`)
   
   - **azure-resource-group** (Secret text)
     - Value: `llm-platform-rg`
   
   - **azure-ml-workspace** (Secret text)
     - Value: `llm-ml-workspace`

4. **Configure Azure CLI**

   ```bash
   # SSH into Jenkins pod
   kubectl exec -it deployment/jenkins -n jenkins -- bash
   
   # Login to Azure
   az login
   
   # Set default subscription
   az account set --subscription <your-subscription-id>
   ```

### Step 3: Create Jenkins Pipeline

1. **Create New Pipeline Job**
   - Click "New Item"
   - Enter name: `llm-platform-pipeline`
   - Select "Pipeline"
   - Click OK

2. **Configure Pipeline**
   - **Pipeline Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: Your repository URL
   - **Credentials**: Add if repository is private
   - **Branch**: `*/main` (or your main branch)
   - **Script Path**: `jenkins/Jenkinsfile`

3. **Save and Build**
   - Click Save
   - Click "Build Now"

### Step 4: Configure Kubernetes Access

```bash
# Create service account for Jenkins
kubectl create serviceaccount jenkins -n jenkins

# Grant permissions
kubectl create clusterrolebinding jenkins-cluster-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=jenkins:jenkins

# Get token for Jenkins
kubectl create token jenkins -n jenkins
```

Add Kubernetes credentials in Jenkins:
- **Manage Jenkins** → **Credentials** → **Add Credentials**
- Kind: **Kubernetes configuration**
- Add kubeconfig or service account token

## 🔧 Pipeline Configuration

### Environment Variables

The pipeline uses these environment variables (configured in Jenkinsfile):

- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID
- `AZURE_RESOURCE_GROUP`: Resource group name
- `AZURE_ML_WORKSPACE`: Azure ML workspace name
- `AKS_CLUSTER_NAME`: AKS cluster name
- `ACR_NAME`: Azure Container Registry name
- `KUBERNETES_NAMESPACE`: Kubernetes namespace

### Branch Strategy

- **main**: Deploys to production
- **develop/staging**: Deploys to staging
- **feature/***: Builds and tests only

### Manual Parameters

You can add manual parameters:

```groovy
parameters {
    booleanParam(name: 'TRAIN_MODEL', defaultValue: false, description: 'Train model in Azure ML')
    choice(name: 'ENVIRONMENT', choices: ['staging', 'production'], description: 'Deployment environment')
}
```

## 📊 Pipeline Stages Explained

### 1. Checkout Stage
- Checks out code from repository
- Sets build tags and commit info

### 2. Lint & Test Stage
- Runs Python linting (flake8)
- Runs unit tests (when available)
- Runs in parallel for speed

### 3. Build Docker Images Stage
- Builds worker Docker image
- Builds web Docker image
- Runs in parallel
- Tags with build number and latest

### 4. Push to ACR Stage
- Logs into Azure Container Registry
- Pushes both images
- Tags with version numbers

### 5. Azure ML Training Stage
- Runs only on main/develop branches
- Trains model using Azure ML pipeline
- Registers model in Azure ML

### 6. Deploy to Staging Stage
- Deploys to staging namespace
- Updates deployment images
- Waits for rollout completion

### 7. Deploy to Production Stage
- Deploys to production namespace
- Updates deployment images
- Deploys Azure ML endpoint
- Waits for rollout completion

### 8. Smoke Tests Stage
- Tests health endpoints
- Tests inference API
- Verifies deployment success

## 🔄 Continuous Deployment

### Automatic Deployment

The pipeline automatically deploys:
- **Staging**: On push to `develop` or `staging` branch
- **Production**: On push to `main` branch

### Manual Deployment

You can trigger manual builds:
1. Go to pipeline job
2. Click "Build with Parameters"
3. Select options
4. Click Build

## 🛠️ Troubleshooting

### Jenkins Cannot Access AKS

```bash
# Verify service account permissions
kubectl get clusterrolebinding jenkins-cluster-admin

# Test access from Jenkins pod
kubectl exec -it deployment/jenkins -n jenkins -- kubectl get nodes
```

### Docker Build Fails

```bash
# Check Docker is available in Jenkins agent
kubectl exec -it deployment/jenkins -n jenkins -- docker ps

# Check disk space
kubectl exec -it deployment/jenkins -n jenkins -- df -h
```

### Azure Login Fails

```bash
# Login from Jenkins pod
kubectl exec -it deployment/jenkins -n jenkins -- az login

# Verify credentials
kubectl exec -it deployment/jenkins -n jenkins -- az account show
```

### Deployment Fails

```bash
# Check deployment status
kubectl get deployments -n llm-platform

# Check pod logs
kubectl logs -f deployment/llm-worker -n llm-platform
kubectl logs -f deployment/llm-web -n llm-platform

# Check events
kubectl get events -n llm-platform --sort-by='.lastTimestamp'
```

## 📈 Monitoring Pipeline

### View Pipeline Status

- Go to Jenkins dashboard
- Click on pipeline job
- View build history
- Click on build to see details

### Pipeline Notifications

Configure notifications (Slack, Email, etc.) in the `post` section of Jenkinsfile.

## 🔐 Security Best Practices

1. **Use Credentials**: Store secrets in Jenkins credentials, not in code
2. **RBAC**: Use service accounts with minimal required permissions
3. **Image Scanning**: Add image vulnerability scanning stage
4. **Secrets Management**: Use Azure Key Vault for sensitive data
5. **Network Policies**: Restrict network access for Jenkins

## 📚 Additional Resources

- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Jenkins Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Azure Jenkins Plugin](https://plugins.jenkins.io/azure-cli/)
- [Kubernetes Jenkins Plugin](https://plugins.jenkins.io/kubernetes-cli/)
