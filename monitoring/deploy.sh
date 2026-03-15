#!/bin/bash

# Deploy Prometheus and Grafana Monitoring Stack
# Usage: ./monitoring/deploy.sh

set -e

echo "🚀 Deploying Prometheus and Grafana Monitoring Stack..."

# Create monitoring namespace
echo "📦 Creating monitoring namespace..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Deploy Prometheus
echo "📊 Deploying Prometheus..."
kubectl apply -f monitoring/prometheus/prometheus-config.yaml
kubectl apply -f monitoring/prometheus/prometheus-deployment.yaml

# Wait for Prometheus
echo "⏳ Waiting for Prometheus to be ready..."
kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=300s || true

# Deploy Grafana
echo "📈 Deploying Grafana..."

# Deploy dashboard provisioning config
kubectl apply -f monitoring/grafana/dashboard-provisioning.yaml

# Create Grafana admin password secret if it doesn't exist
if ! kubectl get secret grafana-credentials -n monitoring &>/dev/null; then
    echo "🔐 Creating Grafana admin password secret..."
    read -sp "Enter Grafana admin password (default: admin): " GRAFANA_PASSWORD
    GRAFANA_PASSWORD=${GRAFANA_PASSWORD:-admin}
    kubectl create secret generic grafana-credentials \
        --from-literal=admin-password="$GRAFANA_PASSWORD" \
        --namespace monitoring
else
    echo "✅ Grafana credentials secret already exists"
fi

kubectl apply -f monitoring/grafana/grafana-deployment.yaml

# Wait for Grafana
echo "⏳ Waiting for Grafana to be ready..."
kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=300s || true

# Get service URLs
echo ""
echo "✅ Monitoring stack deployed successfully!"
echo ""
echo "📊 Access URLs:"
echo "   Prometheus:"
PROMETHEUS_IP=$(kubectl get service prometheus -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
if [ -n "$PROMETHEUS_IP" ]; then
    echo "     http://$PROMETHEUS_IP"
else
    echo "     kubectl port-forward service/prometheus 9090:80 -n monitoring"
    echo "     Then access: http://localhost:9090"
fi

echo ""
echo "   Grafana:"
GRAFANA_IP=$(kubectl get service grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
if [ -n "$GRAFANA_IP" ]; then
    echo "     http://$GRAFANA_IP"
    echo "     Username: admin"
    echo "     Password: <from-secret>"
else
    echo "     kubectl port-forward service/grafana 3000:80 -n monitoring"
    echo "     Then access: http://localhost:3000"
    echo "     Username: admin"
    echo "     Password: <from-secret>"
fi

echo ""
echo "📈 Next Steps:"
echo "   1. Import Grafana dashboard: monitoring/grafana/dashboards/llm-platform-dashboard.json"
echo "   2. Check Prometheus targets: http://localhost:9090/targets"
echo "   3. See monitoring/README.md for detailed documentation"
