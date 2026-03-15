# Kubeflow Integration for LLM Deployment

This directory contains Kubeflow components for orchestrating LLM model workflows, training, and serving on Azure Kubernetes Service (AKS).

## ⚠️ Important: Installation Required

**Kubeflow requires installation on your AKS cluster.** If you prefer a fully managed solution without installation, see **[AZURE_OPTIONS.md](AZURE_OPTIONS.md)** for Azure Machine Learning (no installation needed).

## Overview

Kubeflow integration provides:
- **Kubeflow Pipelines**: Orchestrate ML workflows (model preparation, evaluation, deployment)
- **KServe**: Model serving with autoscaling and A/B testing
- **Kafka Integration**: Connect pipelines with the existing Kafka-based inference system

## Architecture

```
Kubeflow Pipelines → Model Training/Preparation → KServe Deployment
                                              ↓
                                    Kafka (llm-requests)
                                              ↓
                                    LLM Worker Service
                                              ↓
                                    Kafka (llm-responses)
```

## Directory Structure

```
kubeflow/
├── pipelines/              # Kubeflow Pipeline definitions
│   ├── llm_pipeline.py    # Main training/deployment pipeline
│   ├── inference_pipeline.py  # Inference orchestration pipeline
│   └── kafka_component.py # Kafka integration components
├── serving/                # KServe serving configurations
│   └── kserve_inference_service.yaml
├── k8s/                    # Kubernetes manifests
│   ├── kubeflow-install.yaml
│   └── kafka-integration.yaml
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Prerequisites

> **💡 Prefer a managed solution?** Check out [AZURE_OPTIONS.md](AZURE_OPTIONS.md) for Azure Machine Learning - no installation required!

1. **Kubeflow Installation on AKS** (Required - takes 20-30 minutes)
   ```bash
   # Install Kubeflow using the official manifests
   # See: https://www.kubeflow.org/docs/started/installing-kubeflow/
   
   # Or use Azure-specific installation:
   kubectl apply -k github.com/kubeflow/manifests/example?ref=main
   ```
   
   **Note**: This requires installing Kubeflow on your AKS cluster. If you want to avoid installation, consider using Azure Machine Learning instead (see `azure_ml/` directory).

2. **KServe Installation**
   ```bash
   # Install KServe (part of Kubeflow or standalone)
   kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.11.0/kserve.yaml
   ```

3. **Kafka Running in Cluster**
   - Ensure Kafka is accessible from the `kubeflow` namespace
   - See `k8s/kafka-integration.yaml` for configuration

## Installation

### 1. Install Kubeflow Components

```bash
# Apply Kubernetes configurations
kubectl apply -f k8s/kubeflow-install.yaml
kubectl apply -f k8s/kafka-integration.yaml
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Deploy KServe Inference Service

```bash
# Update the image in serving/kserve_inference_service.yaml
# Then apply:
kubectl apply -f serving/kserve_inference_service.yaml
```

## Usage

### Running Kubeflow Pipelines

#### 1. Compile Pipeline

```bash
cd pipelines
python llm_pipeline.py
# This generates llm_pipeline.yaml
```

#### 2. Upload to Kubeflow Pipelines UI

1. Access Kubeflow Pipelines UI (usually at `http://<kubeflow-url>/pipeline`)
2. Click "Upload Pipeline"
3. Select `llm_pipeline.yaml`
4. Create a new run with parameters:
   - `model_name`: e.g., "microsoft/phi-2"
   - `namespace`: "kubeflow"

#### 3. Run Inference Pipeline

```bash
# Compile inference pipeline
python inference_pipeline.py

# Upload to Kubeflow Pipelines UI
# Or use KFP SDK:
from kfp import dsl
from kfp import compiler
import kfp

client = kfp.Client(host='http://<kubeflow-url>')

# Compile and run
compiler.Compiler().compile(
    pipeline_func=inference_pipeline,
    package_path='inference_pipeline.yaml'
)

# Create experiment
experiment = client.create_experiment(name='llm-inference')

# Run pipeline
run = client.run_pipeline(
    experiment_id=experiment.id,
    job_name='llm-inference-run',
    pipeline_package_path='inference_pipeline.yaml',
    params={
        'prompt': 'What is artificial intelligence?',
        'kafka_bootstrap_servers': 'kafka.kafka.svc.cluster.local:9092'
    }
)
```

### Using KServe for Model Serving

#### 1. Deploy Model

```bash
kubectl apply -f serving/kserve_inference_service.yaml
```

#### 2. Check Status

```bash
kubectl get inferenceservice -n kubeflow
kubectl describe inferenceservice llm-worker-phi2 -n kubeflow
```

#### 3. Test Inference

```bash
# Get inference URL
INGRESS_HOST=$(kubectl get ingress -n kubeflow -o jsonpath='{.items[0].spec.rules[0].host}')
SERVICE_HOSTNAME=$(kubectl get inferenceservice llm-worker-phi2 -n kubeflow -o jsonpath='{.status.url}')

# Send inference request
curl -v -H "Host: ${SERVICE_HOSTNAME}" \
  http://${INGRESS_HOST}/v1/models/llm-worker-phi2:predict \
  -d '{"prompt": "Hello, how are you?"}'
```

## Pipeline Components

### LLM Pipeline (`llm_pipeline.py`)

Orchestrates:
1. **Model Preparation**: Downloads and prepares the LLM model
2. **Model Evaluation**: Evaluates model performance (optional)
3. **KServe Deployment**: Deploys model to KServe for serving

### Inference Pipeline (`inference_pipeline.py`)

Orchestrates:
1. **Single Inference**: Sends a single inference request via Kafka
2. **Batch Inference**: Sends multiple inference requests in batch

### Kafka Components (`kafka_component.py`)

- `send_inference_request`: Send single inference request
- `batch_inference_requests`: Send batch inference requests

## Configuration

### Environment Variables

Set in `k8s/kubeflow-install.yaml` ConfigMap:

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `KAFKA_REQUEST_TOPIC`: Topic for inference requests
- `KAFKA_RESPONSE_TOPIC`: Topic for inference responses
- `DEFAULT_MODEL_NAME`: Default model to use
- `MODEL_STORAGE_PATH`: Path for model storage

### KServe Configuration

Edit `serving/kserve_inference_service.yaml`:

- Update `image` with your container registry
- Adjust `resources` based on model requirements
- Configure `env` variables for worker configuration

## Integration with Existing System

The Kubeflow integration works alongside the existing Kafka-based architecture:

1. **Kubeflow Pipelines** can trigger model training/deployment
2. **KServe** serves models and can consume from Kafka
3. **Existing LLM Worker** continues to process Kafka messages
4. **Both systems** can run in parallel for different use cases

## Monitoring

### Kubeflow Pipelines

- Access Pipelines UI: `http://<kubeflow-url>/pipeline`
- View pipeline runs, logs, and artifacts
- Monitor pipeline execution metrics

### KServe

```bash
# View InferenceService status
kubectl get inferenceservice -n kubeflow

# View pods
kubectl get pods -n kubeflow -l serving.kserve.io/inferenceservice=llm-worker-phi2

# View logs
kubectl logs -n kubeflow -l serving.kserve.io/inferenceservice=llm-worker-phi2
```

## Troubleshooting

### Pipeline Fails to Connect to Kafka

1. Verify Kafka is accessible from `kubeflow` namespace:
   ```bash
   kubectl run -it --rm debug --image=confluentinc/cp-kafka:7.5.0 \
     --restart=Never --namespace=kubeflow -- \
     kafka-broker-api-versions --bootstrap-server kafka.kafka.svc.cluster.local:9092
   ```

2. Check Kafka service:
   ```bash
   kubectl get svc -n kafka
   ```

### KServe Deployment Fails

1. Check KServe installation:
   ```bash
   kubectl get pods -n knative-serving
   kubectl get pods -n kserve
   ```

2. Check InferenceService events:
   ```bash
   kubectl describe inferenceservice llm-worker-phi2 -n kubeflow
   ```

### Model Not Loading

1. Verify model storage PVC:
   ```bash
   kubectl get pvc -n kubeflow
   ```

2. Check container logs:
   ```bash
   kubectl logs -n kubeflow -l serving.kserve.io/inferenceservice=llm-worker-phi2
   ```

## Next Steps

1. **Customize Pipelines**: Modify pipeline components for your specific workflows
2. **Add Model Versioning**: Implement model versioning with KServe
3. **A/B Testing**: Use KServe to run A/B tests between model versions
4. **Monitoring**: Integrate with Prometheus/Grafana for pipeline metrics
5. **CI/CD**: Integrate pipelines with Jenkins/GitHub Actions

## Resources

- [Kubeflow Documentation](https://www.kubeflow.org/docs/)
- [KServe Documentation](https://kserve.github.io/website/)
- [Kubeflow Pipelines SDK](https://www.kubeflow.org/docs/components/pipelines/sdk/)
- [Azure AKS with Kubeflow](https://docs.microsoft.com/en-us/azure/architecture/example-scenario/ai-machine-learning/kubeflow-on-azure)
