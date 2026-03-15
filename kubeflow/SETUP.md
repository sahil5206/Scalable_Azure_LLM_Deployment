# Kubeflow Setup Guide

Step-by-step guide to set up Kubeflow integration for the LLM Deployment project.

## Prerequisites

1. **Azure AKS Cluster**
   - AKS cluster with at least 4 nodes (recommended: 8+ nodes)
   - Node size: Standard_D4s_v3 or larger (for GPU support: Standard_NC6s_v3)
   - Kubernetes version: 1.24 or higher

2. **kubectl configured**
   ```bash
   az aks get-credentials --resource-group <resource-group> --name <cluster-name>
   kubectl get nodes
   ```

3. **Kafka Running in Cluster**
   - Kafka should be deployed in the `kafka` namespace
   - Accessible via service: `kafka.kafka.svc.cluster.local:9092`

## Installation Steps

### Step 1: Install Kubeflow on AKS

#### Option A: Using Kubeflow Manifests (Recommended)

```bash
# Clone Kubeflow manifests
git clone https://github.com/kubeflow/manifests.git
cd manifests

# Install Kubeflow (this may take 20-30 minutes)
kubectl apply -k example

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod -l app=ml-pipeline -n kubeflow --timeout=600s
```

#### Option B: Using Azure Marketplace

1. Go to Azure Portal
2. Search for "Kubeflow" in Marketplace
3. Deploy Kubeflow to your AKS cluster
4. Follow the setup wizard

### Step 2: Install KServe

```bash
# Install KServe CRDs
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.11.0/kserve.yaml

# Verify installation
kubectl get pods -n kserve
```

### Step 3: Install Knative Serving (Required for KServe)

```bash
# Install Knative Serving
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.11.0/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.11.0/serving-core.yaml

# Wait for Knative to be ready
kubectl wait --for=condition=ready pod -l app=controller -n knative-serving --timeout=300s
```

### Step 4: Apply Project Configurations

```bash
# Navigate to kubeflow directory
cd kubeflow

# Apply Kubernetes configurations
kubectl apply -f k8s/kubeflow-install.yaml
kubectl apply -f k8s/kafka-integration.yaml

# Verify
kubectl get configmap -n kubeflow
kubectl get service -n kubeflow
```

### Step 5: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 6: Build and Push Container Image

```bash
# Build the worker image
cd ..
docker build -f docker/worker/Dockerfile -t <your-registry>/llm-worker:latest .

# Update the image in serving/kserve_inference_service.yaml
# Replace 'your-registry/llm-worker:latest' with your actual registry

# Push to registry
docker push <your-registry>/llm-worker:latest
```

### Step 7: Deploy KServe InferenceService

```bash
# Update serving/kserve_inference_service.yaml with your image
# Then apply:
kubectl apply -f serving/kserve_inference_service.yaml

# Check status
kubectl get inferenceservice -n kubeflow
kubectl describe inferenceservice llm-worker-phi2 -n kubeflow
```

### Step 8: Compile and Upload Pipelines

```bash
cd pipelines

# Compile LLM pipeline
python llm_pipeline.py

# Compile inference pipeline
python inference_pipeline.py
```

#### Upload via UI:

1. Access Kubeflow Pipelines UI:
   ```bash
   # Port forward to access UI
   kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
   ```
2. Open browser: http://localhost:8080
3. Click "Upload Pipeline"
4. Select `llm_pipeline.yaml` or `inference_pipeline.yaml`
5. Create a new run with appropriate parameters

#### Upload via SDK:

```python
import kfp

# Connect to Kubeflow
client = kfp.Client(host='http://<kubeflow-url>/pipeline')

# Create experiment
experiment = client.create_experiment(name='llm-experiments')

# Run pipeline
run = client.run_pipeline(
    experiment_id=experiment.id,
    job_name='llm-training-run',
    pipeline_package_path='llm_pipeline.yaml',
    params={
        'model_name': 'microsoft/phi-2',
        'namespace': 'kubeflow'
    }
)
```

## Verification

### Check Kubeflow Components

```bash
# Check namespaces
kubectl get namespaces | grep kubeflow

# Check pods
kubectl get pods -n kubeflow
kubectl get pods -n kserve
kubectl get pods -n knative-serving

# Check InferenceService
kubectl get inferenceservice -n kubeflow
```

### Test Kafka Connection

```bash
# Test from kubeflow namespace
kubectl run -it --rm kafka-test --image=confluentinc/cp-kafka:7.5.0 \
  --restart=Never --namespace=kubeflow -- \
  kafka-broker-api-versions --bootstrap-server kafka.kafka.svc.cluster.local:9092
```

### Test Inference Service

```bash
# Get service URL
INGRESS_HOST=$(kubectl get ingress -n kubeflow -o jsonpath='{.items[0].spec.rules[0].host}' 2>/dev/null || echo "localhost")
SERVICE_HOSTNAME=$(kubectl get inferenceservice llm-worker-phi2 -n kubeflow -o jsonpath='{.status.url}')

# Send test request (if ingress is configured)
curl -v -H "Host: ${SERVICE_HOSTNAME}" \
  http://${INGRESS_HOST}/v1/models/llm-worker-phi2:predict \
  -d '{"prompt": "Hello, how are you?"}'
```

## Troubleshooting

### Issue: Kubeflow pods not starting

```bash
# Check pod status
kubectl get pods -n kubeflow
kubectl describe pod <pod-name> -n kubeflow

# Check events
kubectl get events -n kubeflow --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n kubeflow
```

### Issue: KServe not working

```bash
# Check KServe controller
kubectl get pods -n kserve
kubectl logs -n kserve -l control-plane=kserve-controller-manager

# Check InferenceService events
kubectl describe inferenceservice llm-worker-phi2 -n kubeflow
```

### Issue: Cannot connect to Kafka

```bash
# Verify Kafka service exists
kubectl get svc -n kafka

# Test connectivity
kubectl run -it --rm debug --image=confluentinc/cp-kafka:7.5.0 \
  --restart=Never --namespace=kubeflow -- \
  kafka-broker-api-versions --bootstrap-server kafka.kafka.svc.cluster.local:9092

# Check network policies
kubectl get networkpolicies -n kafka
kubectl get networkpolicies -n kubeflow
```

### Issue: Pipeline compilation fails

```bash
# Check Python dependencies
pip list | grep kfp

# Verify imports
python -c "from kfp import dsl, compiler; print('OK')"

# Check pipeline syntax
python -m py_compile pipelines/llm_pipeline.py
```

## Next Steps

1. **Customize Pipelines**: Modify pipeline components for your specific use cases
2. **Configure Autoscaling**: Adjust KServe autoscaling parameters
3. **Set Up Monitoring**: Integrate with Prometheus/Grafana
4. **CI/CD Integration**: Connect pipelines with Jenkins/GitHub Actions
5. **Model Versioning**: Implement model versioning strategy

## Resources

- [Kubeflow Documentation](https://www.kubeflow.org/docs/)
- [KServe Documentation](https://kserve.github.io/website/)
- [Azure AKS Documentation](https://docs.microsoft.com/en-us/azure/aks/)
- [Kubeflow on Azure Guide](https://docs.microsoft.com/en-us/azure/architecture/example-scenario/ai-machine-learning/kubeflow-on-azure)
