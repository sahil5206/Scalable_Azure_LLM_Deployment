# LLM Inference Platform - Industry Grade with Azure ML

A production-ready, industry-grade LLM inference system with **Azure Machine Learning** integration, web frontend, and Kafka-based message queuing, built for Azure deployment.

## 🚀 Industry-Grade Features

- **Azure ML Integration**: Managed endpoints, model registry, MLOps pipelines
- **Web Frontend**: Modern UI with automatic Azure ML/Kafka routing
- **Kafka-Based Architecture**: Scalable, event-driven inference system
- **Hybrid Inference**: Azure ML (primary) + Kafka workers (fallback)
- **Production Ready**: Auto-scaling, monitoring, health checks, CI/CD
- **Terraform Infrastructure**: Complete Azure deployment automation

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (Web UI)                   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Web Frontend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Intelligent Router                                  │  │
│  │  - Azure ML Endpoint (Primary) ⭐                    │  │
│  │  - Kafka Workers (Fallback)                          │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────────┐         ┌──────────────────┐
│ Azure ML         │         │ Kafka            │
│ Managed Endpoint │         │ Workers           │
│                  │         │                   │
│ ⭐ Auto-scaling  │         │ Batch Processing  │
│ ⭐ High Availability│      │ Direct Inference  │
│ ⭐ Monitoring    │         │                   │
└──────────────────┘         └──────────────────┘
```

For detailed architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 📖 Complete Deployment Guide

**For step-by-step deployment instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**

This comprehensive guide covers:
- Prerequisites and Azure setup
- Local development setup
- Azure ML workspace configuration
- Terraform infrastructure deployment
- **Jenkins CI/CD setup and configuration**
- Docker image building and pushing (manual or automated via Jenkins)
- Kubernetes deployment
- **Automated CI/CD pipeline usage**
- Configuration and testing
- Troubleshooting

## 🏃 Quick Start

### Option 1: Full Setup with Azure ML (Industry-Grade)

```bash
# 1. Set up Azure ML workspace
export AZURE_ML_SUBSCRIPTION_ID="<your-subscription-id>"
export AZURE_ML_RESOURCE_GROUP_NAME="llm-platform-rg"
export AZURE_ML_WORKSPACE_NAME="llm-ml-workspace"
python azure_ml/workspace_setup.py

# 2. Train and register model
python azure_ml/pipelines/llm_pipeline.py

# 3. Deploy to managed endpoint
python azure_ml/deployment/deploy_to_aks.py

# 4. Configure web frontend
export AZURE_ML_ENDPOINT_NAME="llm-inference-endpoint"
cd web && python -m web.main

# 5. Access web UI
open http://localhost:8000
```

### Option 2: Docker Compose (Local Development)

```bash
# Start all services (Kafka, Worker, Web Frontend)
docker-compose up -d

# Access web UI
open http://localhost:8000
```

See [azure_ml/INDUSTRY_GRADE_SETUP.md](azure_ml/INDUSTRY_GRADE_SETUP.md) for complete industry-grade setup.

## 📁 Project Structure

```
├── azure_ml/         # ⭐ Azure ML Integration (Industry-Grade)
│   ├── pipelines/    # ML pipelines (training, evaluation, deployment)
│   ├── deployment/   # Production deployment scripts
│   ├── endpoints/    # Managed endpoint configurations
│   └── ci_cd/        # CI/CD pipeline definitions (GitHub Actions)
├── jenkins/          # ⭐ Jenkins CI/CD Integration
│   ├── Jenkinsfile   # Main CI/CD pipeline
│   ├── k8s/          # Jenkins deployment manifests
│   └── scripts/      # Setup scripts
├── web/              # Web frontend with Azure ML/Kafka routing
│   ├── main.py       # FastAPI server with intelligent routing
│   ├── azure_ml_client.py  # Azure ML endpoint client
│   └── templates/    # Web UI
├── worker/           # LLM inference worker service
├── terraform/        # Infrastructure as Code
└── docker/           # Docker configurations
```

## 🎯 Azure ML Features

### Model Management
- ✅ **Model Registry**: Version control for models
- ✅ **Model Versioning**: Track model iterations
- ✅ **Model Lineage**: Track data and code used

### MLOps
- ✅ **Automated Training**: CI/CD pipelines
- ✅ **Automated Deployment**: Deploy to production automatically
- ✅ **A/B Testing**: Test new models safely
- ✅ **Rollback**: Quick rollback to previous versions

### Production Inference
- ✅ **Managed Endpoints**: Auto-scaling inference
- ✅ **High Availability**: Multi-region deployment
- ✅ **Monitoring**: Real-time metrics and alerts
- ✅ **Cost Optimization**: Auto-scale to zero

### Observability
- ✅ **Experiment Tracking**: Track all experiments
- ✅ **Model Monitoring**: Monitor model performance
- ✅ **Data Drift Detection**: Detect data changes
- ✅ **Performance Metrics**: Track latency, throughput

## 🔄 Hybrid Inference System

The web frontend intelligently routes requests:

1. **Primary**: Azure ML Managed Endpoint (if configured)
   - Auto-scaling
   - High availability
   - Managed infrastructure

2. **Fallback**: Kafka-based workers (if Azure ML unavailable)
   - Direct control
   - Batch processing
   - Custom logic

## ⚙️ Configuration

### Azure ML Configuration

```bash
# Required for Azure ML
export AZURE_ML_SUBSCRIPTION_ID="<subscription-id>"
export AZURE_ML_RESOURCE_GROUP_NAME="llm-platform-rg"
export AZURE_ML_WORKSPACE_NAME="llm-ml-workspace"
export AZURE_ML_ENDPOINT_NAME="llm-inference-endpoint"
```

### Web Frontend Configuration

```bash
# Kafka (fallback)
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"

# Azure ML (primary)
export AZURE_ML_ENDPOINT_NAME="llm-inference-endpoint"
export USE_AZURE_ML_PRIMARY=true
```

## 🏗️ Azure Deployment with Terraform

Deploy the entire platform to Azure:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars

terraform init
terraform plan
terraform apply
```

See [terraform/README.md](terraform/README.md) for details.

## 📊 Monitoring

### Azure ML Monitoring
- **Endpoint Metrics**: Requests, latency, errors
- **Model Performance**: Accuracy, drift detection
- **Cost Tracking**: Compute and storage costs

### Application Monitoring
- **Web Frontend**: http://localhost:8000/health
- **Worker**: http://localhost:8081/health
- **Metrics**: http://localhost:8080/metrics (Prometheus)

## 🔄 CI/CD Pipeline

### Jenkins CI/CD (Primary)

Complete Jenkins pipeline for automated builds, tests, and deployments:

- **Automated Builds**: Builds Docker images on code changes
- **Multi-Stage Deployment**: Staging and Production environments
- **Azure ML Integration**: Automated model training
- **Smoke Tests**: Post-deployment verification

See [jenkins/README.md](jenkins/README.md) for setup and usage.

### GitHub Actions (Alternative)

GitHub Actions workflow also available:

```bash
# See azure_ml/ci_cd/github_actions.yml
# Automatically:
# 1. Trains model on code changes
# 2. Deploys to staging
# 3. Deploys to production (main branch)
```

## 📚 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete architecture and workflows
- [azure_ml/INDUSTRY_GRADE_SETUP.md](azure_ml/INDUSTRY_GRADE_SETUP.md) - Industry-grade setup guide
- [azure_ml/README.md](azure_ml/README.md) - Azure ML integration details
- [terraform/README.md](terraform/README.md) - Infrastructure deployment
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide

## 🎓 Learning Azure ML

This project is designed to help you learn and practice Azure ML:

- ✅ **Real-world scenarios**: Production-ready patterns
- ✅ **Best practices**: Industry-standard implementations
- ✅ **Complete workflows**: Training → Deployment → Monitoring
- ✅ **Hybrid architecture**: Azure ML + Kafka integration

## 🛠️ Development

### Prerequisites

- Python 3.9+
- Azure subscription
- Azure CLI installed
- Docker & Docker Compose (for local development)

### Setup

```bash
# Install Azure ML dependencies
pip install -r azure_ml/requirements.txt

# Install web dependencies
pip install -r web/requirements.txt

# Install worker dependencies
pip install -r worker/requirements.txt
```

## 📝 License

MIT

## 🤝 Contributing

Contributions are welcome! This is an industry-grade project perfect for learning Azure ML.
