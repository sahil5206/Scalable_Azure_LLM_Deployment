#!/bin/bash
# Script to install Kubeflow on Azure AKS
# This script provides a guide for installing Kubeflow components

set -e

echo "Kubeflow Installation Script for Azure AKS"
echo "==========================================="

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed. Please install it first."
    exit 1
fi

# Check if kustomize is installed
if ! command -v kustomize &> /dev/null; then
    echo "Warning: kustomize is not installed. Some installations may require it."
    echo "Install with: curl -s \"https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh\" | bash"
fi

# Set namespace
NAMESPACE="kubeflow"
echo "Using namespace: $NAMESPACE"

# Create namespace
echo "Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubeflow configurations
echo "Applying Kubeflow configurations..."
kubectl apply -f ../k8s/kubeflow-install.yaml
kubectl apply -f ../k8s/kafka-integration.yaml

# Install KServe (if not already installed)
echo "Checking KServe installation..."
if ! kubectl get crd inferenceservices.serving.kserve.io &> /dev/null; then
    echo "Installing KServe..."
    kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.11.0/kserve.yaml
    
    echo "Waiting for KServe to be ready..."
    kubectl wait --for=condition=ready pod -l control-plane=kserve-controller-manager -n kserve --timeout=300s
else
    echo "KServe is already installed"
fi

# Install Knative Serving (required for KServe)
echo "Checking Knative Serving installation..."
if ! kubectl get namespace knative-serving &> /dev/null; then
    echo "Installing Knative Serving..."
    kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.11.0/serving-core.yaml
    kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.11.0/serving-crds.yaml
    
    echo "Waiting for Knative Serving to be ready..."
    kubectl wait --for=condition=ready pod -l app=controller -n knative-serving --timeout=300s
else
    echo "Knative Serving is already installed"
fi

# Deploy KServe InferenceService
echo "Deploying LLM InferenceService..."
kubectl apply -f ../serving/kserve_inference_service.yaml

# Wait for InferenceService to be ready
echo "Waiting for InferenceService to be ready..."
kubectl wait --for=condition=ready inferenceservice llm-worker-phi2 -n $NAMESPACE --timeout=300s || true

# Display status
echo ""
echo "Installation Summary:"
echo "===================="
kubectl get inferenceservice -n $NAMESPACE
kubectl get pods -n $NAMESPACE

echo ""
echo "Next steps:"
echo "1. Install Kubeflow Pipelines (if not already installed)"
echo "2. Upload pipelines using: kubectl apply -f <pipeline-yaml>"
echo "3. Access Kubeflow UI (if installed)"
echo ""
echo "To check InferenceService status:"
echo "  kubectl get inferenceservice -n $NAMESPACE"
echo ""
echo "To view logs:"
echo "  kubectl logs -n $NAMESPACE -l serving.kserve.io/inferenceservice=llm-worker-phi2"
