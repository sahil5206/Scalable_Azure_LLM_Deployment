# LLM Worker Service

Production-grade LLM inference worker service with Kafka integration and observability.

## Features

- **Model Loading**: Supports HuggingFace models (TinyLlama, Phi-2, etc.)
- **Kafka Integration**: Async request/response processing via Kafka
- **Batching**: Efficient batch processing for throughput optimization
- **Metrics**: Prometheus metrics for observability
- **Error Handling**: Robust error handling and retry logic
- **Health Checks**: Kubernetes-ready health endpoints

## Architecture

```
Kafka (llm-requests) → Worker → Model Inference → Kafka (llm-responses)
```

## Configuration

See `config.py` for all configuration options. Key settings:

- `MODEL_NAME`: HuggingFace model identifier
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `BATCH_SIZE`: Request batching size
- `MAX_CONCURRENT_REQUESTS`: Maximum concurrent requests

## Running Locally

1. **Start Kafka**:
   ```bash
   docker-compose up -d kafka zookeeper
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Worker**:
   ```bash
   python -m worker.main
   ```

4. **Test**:
   ```bash
   python scripts/test_worker.py
   ```

## Metrics

Prometheus metrics available on port 8080:

- `llm_worker_requests_total`: Total requests by status
- `llm_worker_request_duration_seconds`: Request processing time
- `llm_worker_tokens_generated_total`: Total tokens generated
- `llm_worker_kafka_consumer_lag`: Kafka consumer lag
- `llm_worker_model_inference_duration_seconds`: Model inference time

## Health Checks

- `/health`: Basic health check
- `/ready`: Readiness check (model loaded, Kafka connected)
- `/live`: Liveness check (process running)

## Docker

Build and run:

```bash
docker build -f docker/worker/Dockerfile -t llm-worker:latest .
docker run -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 llm-worker:latest
```
