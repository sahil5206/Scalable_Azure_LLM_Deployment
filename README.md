# Production-Grade LLM Inference Platform on Azure AKS

A scalable, event-driven LLM inference system built for Azure Kubernetes Service (AKS) with Kafka, gRPC, and comprehensive observability.

## Architecture Overview

```
Client → gRPC Gateway → Kafka (request topic)
                      ↓
                 LLM Worker
                      ↓
              Kafka (response topic) → gRPC Gateway → Client
```

## Project Structure

```
├── gateway/          # gRPC API Gateway service
├── worker/           # LLM inference worker service
├── proto/            # Protocol Buffer definitions
├── k8s/              # Kubernetes manifests
├── jenkins/          # CI/CD pipeline definitions
├── scripts/          # Utility scripts
└── docker/           # Docker-related files
```

## Step 1: LLM Worker Service

The LLM worker service is the core inference engine that:
- Loads and manages LLM models (TinyLlama/Phi-2)
- Consumes inference requests from Kafka
- Processes requests with batching support
- Produces responses to Kafka
- Exposes Prometheus metrics

### Quick Start (Local Development)

1. **Prerequisites**
   ```bash
   Python 3.9+
   Docker & Docker Compose
   ```

2. **Install Dependencies**
   ```bash
   cd worker
   pip install -r requirements.txt
   ```

3. **Start Kafka (Docker Compose)**
   ```bash
   docker-compose up -d kafka zookeeper
   ```

4. **Run Worker**
   ```bash
   python -m worker.main
   ```

### Configuration

Worker configuration is managed via environment variables:

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses (default: localhost:9092)
- `KAFKA_REQUEST_TOPIC`: Topic for incoming requests (default: llm-requests)
- `KAFKA_RESPONSE_TOPIC`: Topic for responses (default: llm-responses)
- `KAFKA_CONSUMER_GROUP`: Consumer group ID (default: llm-worker-group)
- `MODEL_NAME`: HuggingFace model identifier (default: microsoft/phi-2)
- `BATCH_SIZE`: Request batching size (default: 4)
- `MAX_SEQUENCE_LENGTH`: Maximum token sequence length (default: 512)
- `METRICS_PORT`: Prometheus metrics port (default: 8080)
- `LOG_LEVEL`: Logging level (default: INFO)

## Next Steps

- Step 2: gRPC Gateway Service
- Step 3: Kubernetes Deployment
- Step 4: Jenkins CI/CD Pipeline
- Step 5: Observability & Monitoring

## License

MIT
