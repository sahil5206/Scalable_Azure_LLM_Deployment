#!/bin/bash
# Script to set up Jenkins on AKS

set -e

echo "=========================================="
echo "Jenkins Setup for LLM Platform"
echo "=========================================="

# Configuration
NAMESPACE="jenkins"
RESOURCE_GROUP="llm-platform-rg"
AKS_CLUSTER_NAME="llm-aks-cluster"

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: kubectl is not configured"
    echo "Run: az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME"
    exit 1
fi

# Create namespace
echo "Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy Jenkins
echo "Deploying Jenkins..."
kubectl apply -f jenkins/k8s/jenkins-deployment.yaml

# Wait for Jenkins to be ready
echo "Waiting for Jenkins to be ready..."
kubectl wait --for=condition=ready pod -l app=jenkins -n $NAMESPACE --timeout=300s

# Get Jenkins admin password
echo ""
echo "=========================================="
echo "Jenkins Setup Complete!"
echo "=========================================="
echo ""
echo "Jenkins Admin Password:"
kubectl exec -it deployment/jenkins -n $NAMESPACE -- cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || \
echo "Password will be available after Jenkins pod is fully started"

echo ""
echo "Jenkins URL:"
JENKINS_IP=$(kubectl get service jenkins -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending...")
if [ "$JENKINS_IP" != "Pending..." ]; then
    echo "  http://$JENKINS_IP"
else
    echo "  Waiting for LoadBalancer IP..."
    echo "  Check with: kubectl get service jenkins -n $NAMESPACE"
fi

echo ""
echo "To access Jenkins:"
echo "  1. Get admin password: kubectl exec -it deployment/jenkins -n $NAMESPACE -- cat /var/jenkins_home/secrets/initialAdminPassword"
echo "  2. Port forward: kubectl port-forward service/jenkins 8080:80 -n $NAMESPACE"
echo "  3. Open: http://localhost:8080"
echo ""
echo "Next steps:"
echo "  1. Complete Jenkins initial setup"
echo "  2. Install required plugins"
echo "  3. Configure credentials (see jenkins/README.md)"
echo "  4. Create pipeline job pointing to jenkins/Jenkinsfile"
