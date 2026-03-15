# Jenkins CI/CD Quick Start

Quick guide to set up and use Jenkins CI/CD for the LLM Platform.

## 🚀 Quick Setup (5 minutes)

### 1. Deploy Jenkins

```bash
# Deploy Jenkins to AKS
kubectl create namespace jenkins
kubectl apply -f jenkins/k8s/jenkins-deployment.yaml

# Or use setup script
bash jenkins/scripts/setup_jenkins.sh
```

### 2. Get Jenkins Access

```bash
# Get admin password
kubectl exec -it deployment/jenkins -n jenkins -- \
  cat /var/jenkins_home/secrets/initialAdminPassword

# Port forward for local access
kubectl port-forward service/jenkins 8080:80 -n jenkins

# Open: http://localhost:8080
```

### 3. Configure Jenkins (One-time)

1. **Initial Setup**
   - Enter admin password
   - Install suggested plugins
   - Create admin user

2. **Install Plugins**
   - Azure CLI Plugin
   - Kubernetes CLI Plugin
   - Docker Pipeline Plugin

3. **Add Credentials**
   - `azure-subscription-id`: Your Azure subscription ID
   - `acr-name`: Your ACR name
   - `azure-resource-group`: `llm-platform-rg`
   - `azure-ml-workspace`: `llm-ml-workspace`

4. **Create Pipeline Job**
   - New Item → Pipeline
   - Name: `llm-platform-pipeline`
   - Pipeline script from SCM
   - Repository: Your repo
   - Script Path: `jenkins/Jenkinsfile`

### 4. Run Pipeline

```bash
# Trigger build
# Go to Jenkins UI → Pipeline → Build Now

# Or via API
curl -X POST http://<jenkins-ip>/job/llm-platform-pipeline/build \
  --user admin:<password>
```

## 📊 What Happens Automatically

When you push code:

- **main branch**: Builds → Tests → Deploys to Production
- **develop/staging**: Builds → Tests → Deploys to Staging
- **feature branches**: Builds → Tests only

## 🔍 Monitor Pipeline

- View in Jenkins UI: `http://<jenkins-ip>/job/llm-platform-pipeline`
- Check build logs
- View deployment status

## 📚 Full Documentation

See [jenkins/README.md](jenkins/README.md) for complete setup guide.
