# Monitoring Stack - Prometheus & Grafana

Complete monitoring solution for the LLM Inference Platform using Prometheus and Grafana.

## 🎯 Features

- ✅ **Prometheus**: Metrics collection and storage
- ✅ **Grafana**: Beautiful dashboards and visualization
- ✅ **Pre-configured Dashboards**: LLM Platform-specific dashboards
- ✅ **Auto-discovery**: Automatic service discovery in Kubernetes
- ✅ **Persistent Storage**: Metrics and dashboard data persistence

## 📊 What Gets Monitored

### Application Metrics
- Request rate and latency
- Token generation rate
- Error rates
- Active requests
- Model inference duration
- Batch processing metrics

### Infrastructure Metrics
- Kubernetes node metrics
- Pod resource usage
- Service health
- Kafka consumer lag

## 🚀 Quick Start

### Deploy Monitoring Stack

**Option 1: Using Deployment Script (Recommended)**

```bash
# Linux/Mac
./monitoring/deploy.sh

# Windows PowerShell
.\monitoring\deploy.ps1
```

**Option 2: Manual Deployment**

```bash
# Create namespace
kubectl create namespace monitoring

# Deploy Prometheus
kubectl apply -f monitoring/prometheus/prometheus-config.yaml
kubectl apply -f monitoring/prometheus/prometheus-deployment.yaml

# Deploy Grafana
kubectl apply -f monitoring/grafana/dashboard-provisioning.yaml
kubectl apply -f monitoring/grafana/grafana-deployment.yaml

# Create Grafana admin password secret
kubectl create secret generic grafana-credentials \
  --from-literal=admin-password='<your-password>' \
  --namespace monitoring

# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=300s
kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=300s
```

### Access Dashboards

```bash
# Get Prometheus URL
kubectl get service prometheus -n monitoring

# Get Grafana URL
kubectl get service grafana -n monitoring

# Or use port forwarding
kubectl port-forward service/prometheus 9090:80 -n monitoring
kubectl port-forward service/grafana 3000:80 -n monitoring

# Access:
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

## 📈 Grafana Dashboards

### LLM Platform Dashboard

Pre-configured dashboard includes:

1. **Request Metrics**
   - Request rate (requests/sec)
   - Request duration (p50, p95, p99)
   - Success/Error rates

2. **Performance Metrics**
   - Token generation rate
   - Tokens per second
   - Model inference duration
   - Batch size

3. **Kafka Metrics**
   - Consumer lag
   - Messages consumed/produced
   - Consumer errors

4. **System Metrics**
   - Active requests
   - Total requests
   - Error rate

### Import Dashboard

1. Access Grafana: http://localhost:3000
2. Login: admin/admin (change password on first login)
3. Go to: **Dashboards** → **Import**
4. Upload: `monitoring/grafana/dashboards/llm-platform-dashboard.json`
5. Select Prometheus data source
6. Click Import

## 🔧 Configuration

### Prometheus Configuration

Edit `monitoring/prometheus/prometheus-config.yaml` to:
- Adjust scrape intervals
- Add custom scrape targets
- Configure alerting rules

### Grafana Configuration

Edit `monitoring/grafana/grafana-deployment.yaml` to:
- Change admin password
- Add additional data sources
- Configure authentication

## 📊 Metrics Exposed

### Worker Service Metrics

Available at: `http://<worker-pod-ip>:8080/metrics`

- `llm_worker_requests_total`: Total requests by status
- `llm_worker_request_duration_seconds`: Request processing time
- `llm_worker_tokens_generated_total`: Total tokens generated
- `llm_worker_kafka_consumer_lag`: Kafka consumer lag
- `llm_worker_model_inference_duration_seconds`: Model inference time
- `llm_worker_active_requests`: Currently active requests

### Web Frontend Metrics

Add Prometheus metrics to web frontend (see `web/metrics/` directory).

## 🔔 Alerting (Optional)

### Create Alert Rules

```yaml
# monitoring/prometheus/alerts.yaml
groups:
  - name: llm_platform
    rules:
      - alert: HighErrorRate
        expr: sum(rate(llm_worker_requests_total{status="error"}[5m])) / sum(rate(llm_worker_requests_total[5m])) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(llm_worker_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        annotations:
          summary: "High request latency detected"
      
      - alert: KafkaConsumerLag
        expr: llm_worker_kafka_consumer_lag > 1000
        for: 5m
        annotations:
          summary: "High Kafka consumer lag"
```

## 🛠️ Troubleshooting

### Prometheus Not Scraping

```bash
# Check Prometheus targets
# Access Prometheus UI → Status → Targets

# Check service discovery
kubectl get pods -n llm-platform --show-labels

# Verify Prometheus can access pods
kubectl exec -it deployment/prometheus -n monitoring -- wget -O- http://<worker-pod-ip>:8080/metrics
```

### Grafana Cannot Connect to Prometheus

```bash
# Check Prometheus service
kubectl get service prometheus -n monitoring

# Test connection from Grafana pod
kubectl exec -it deployment/grafana -n monitoring -- wget -O- http://prometheus:9090/api/v1/status/config
```

### Metrics Not Appearing

```bash
# Check worker metrics endpoint
kubectl port-forward deployment/llm-worker 8080:8080 -n llm-platform
curl http://localhost:8080/metrics

# Check Prometheus config
kubectl get configmap prometheus-config -n monitoring -o yaml
```

## 📚 Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
