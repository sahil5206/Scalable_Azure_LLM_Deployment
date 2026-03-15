# Deploy Prometheus and Grafana Monitoring Stack
# Usage: .\monitoring\deploy.ps1

Write-Host "🚀 Deploying Prometheus and Grafana Monitoring Stack..." -ForegroundColor Cyan

# Create monitoring namespace
Write-Host "📦 Creating monitoring namespace..." -ForegroundColor Yellow
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Deploy Prometheus
Write-Host "📊 Deploying Prometheus..." -ForegroundColor Yellow
kubectl apply -f monitoring/prometheus/prometheus-config.yaml
kubectl apply -f monitoring/prometheus/prometheus-deployment.yaml

# Wait for Prometheus
Write-Host "⏳ Waiting for Prometheus to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=300s

# Deploy Grafana
Write-Host "📈 Deploying Grafana..." -ForegroundColor Yellow

# Deploy dashboard provisioning config
kubectl apply -f monitoring/grafana/dashboard-provisioning.yaml

# Create Grafana admin password secret if it doesn't exist
$secretExists = kubectl get secret grafana-credentials -n monitoring 2>$null
if (-not $secretExists) {
    Write-Host "🔐 Creating Grafana admin password secret..." -ForegroundColor Yellow
    $password = Read-Host "Enter Grafana admin password (default: admin)" -AsSecureString
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))
    if ([string]::IsNullOrEmpty($plainPassword)) {
        $plainPassword = "admin"
    }
    kubectl create secret generic grafana-credentials `
        --from-literal=admin-password="$plainPassword" `
        --namespace monitoring
} else {
    Write-Host "✅ Grafana credentials secret already exists" -ForegroundColor Green
}

kubectl apply -f monitoring/grafana/grafana-deployment.yaml

# Wait for Grafana
Write-Host "⏳ Waiting for Grafana to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=300s

# Get service URLs
Write-Host ""
Write-Host "✅ Monitoring stack deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Access URLs:" -ForegroundColor Cyan
Write-Host "   Prometheus:"
$prometheusIP = kubectl get service prometheus -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>$null
if ($prometheusIP) {
    Write-Host "     http://$prometheusIP" -ForegroundColor White
} else {
    Write-Host "     kubectl port-forward service/prometheus 9090:80 -n monitoring" -ForegroundColor White
    Write-Host "     Then access: http://localhost:9090" -ForegroundColor White
}

Write-Host ""
Write-Host "   Grafana:"
$grafanaIP = kubectl get service grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>$null
if ($grafanaIP) {
    Write-Host "     http://$grafanaIP" -ForegroundColor White
    Write-Host "     Username: admin" -ForegroundColor White
    Write-Host "     Password: <from-secret>" -ForegroundColor White
} else {
    Write-Host "     kubectl port-forward service/grafana 3000:80 -n monitoring" -ForegroundColor White
    Write-Host "     Then access: http://localhost:3000" -ForegroundColor White
    Write-Host "     Username: admin" -ForegroundColor White
    Write-Host "     Password: <from-secret>" -ForegroundColor White
}

Write-Host ""
Write-Host "📈 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Import Grafana dashboard: monitoring/grafana/dashboards/llm-platform-dashboard.json" -ForegroundColor White
Write-Host "   2. Check Prometheus targets: http://localhost:9090/targets" -ForegroundColor White
Write-Host "   3. See monitoring/README.md for detailed documentation" -ForegroundColor White
