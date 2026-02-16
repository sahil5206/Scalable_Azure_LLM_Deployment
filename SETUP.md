# Setup Guide - LLM Worker Service (Step 1)

Complete setup instructions for the LLM Worker Service.

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- 8GB+ RAM (for model loading)
- GPU optional but recommended (CUDA-compatible)

## Step 1: Environment Setup

1. **Clone/Navigate to the repository**
   ```bash
   cd LLM_Deployement_Azure
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd worker
   pip install -r requirements.txt
   ```

## Step 2: Start Kafka

1. **Start Kafka and Zookeeper**
   ```bash
   docker-compose up -d kafka zookeeper
   ```

2. **Verify Kafka is running**
   ```bash
   docker ps
   ```

3. **Optional: Access Kafka UI**
   - Open browser to http://localhost:8080
   - View topics and messages

## Step 3: Create Kafka Topics

Topics are auto-created, but you can manually create them:

```bash
# Using Docker exec
docker exec -it kafka kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --topic llm-requests \
  --partitions 3 \
  --replication-factor 1

docker exec -it kafka kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --topic llm-responses \
  --partitions 3 \
  --replication-factor 1
```

## Step 4: Configure Environment

Create a `.env` file in the `worker/` directory (optional, defaults are provided):

```bash
# Copy example (if .env.example exists)
cp .env.example worker/.env

# Or create manually with these key settings:
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
MODEL_NAME=microsoft/phi-2
BATCH_SIZE=4
```

## Step 5: Run the Worker

1. **Run from worker directory**
   ```bash
   cd worker
   python -m worker.main
   ```

2. **Expected output**
   ```
   INFO - Initializing LLM Worker Service: worker-xxxxx
   INFO - Loading LLM model...
   INFO - Model loaded: microsoft/phi-2
   INFO - Initializing Kafka producer...
   INFO - Initializing Kafka consumer...
   INFO - Starting LLM Worker Service...
   INFO - Metrics server started on port 8080
   INFO - Health check server started on port 8081
   INFO - Subscribed to topic: llm-requests
   ```

## Step 6: Test the Worker

1. **In a new terminal, run the test script**
   ```bash
   python scripts/test_worker.py
   ```

2. **Or manually send a test message**
   ```python
   from confluent_kafka import Producer
   import json
   
   producer = Producer({'bootstrap.servers': 'localhost:9092'})
   request = {
       'request_id': 'test-123',
       'prompt': 'What is machine learning?',
       'max_new_tokens': 100
   }
   producer.produce('llm-requests', value=json.dumps(request).encode())
   producer.flush()
   ```

## Step 7: Verify Metrics

1. **Check Prometheus metrics**
   ```bash
   curl http://localhost:8080/metrics
   ```

2. **Check health endpoints**
   ```bash
   curl http://localhost:8081/health
   curl http://localhost:8081/ready
   curl http://localhost:8081/live
   ```

## Troubleshooting

### Model Loading Issues

- **Out of Memory**: Reduce `MAX_SEQUENCE_LENGTH` or use a smaller model
- **Model Download Fails**: Check internet connection, HuggingFace access
- **CUDA Errors**: Set `MODEL_DEVICE=cpu` to use CPU only

### Kafka Connection Issues

- **Connection Refused**: Ensure Kafka is running: `docker ps`
- **Topic Not Found**: Topics auto-create, but verify with `docker exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092`
- **Consumer Group Issues**: Change `KAFKA_CONSUMER_GROUP` if reusing old offsets

### Performance Issues

- **Slow Inference**: Use GPU (`MODEL_DEVICE=cuda`) or reduce `MAX_NEW_TOKENS`
- **High Memory**: Reduce `BATCH_SIZE` or `MAX_CONCURRENT_REQUESTS`
- **Kafka Lag**: Increase worker instances or reduce `BATCH_SIZE`

## Next Steps

Once the worker is running successfully:

1. Monitor metrics at http://localhost:8080/metrics
2. Test with multiple concurrent requests
3. Scale workers by running multiple instances with different `KAFKA_CONSUMER_GROUP` IDs
4. Proceed to Step 2: gRPC Gateway Service

## Model Options

Supported models (change `MODEL_NAME`):

- `microsoft/phi-2` (default, ~2.7B parameters)
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (smaller, faster)
- `microsoft/phi-1_5` (smaller alternative)
- Any HuggingFace CausalLM model

## Production Considerations

For production deployment:

1. Use GPU nodes for workers
2. Configure proper resource limits
3. Set up monitoring and alerting
4. Use managed Kafka (Azure Event Hubs, Confluent Cloud)
5. Implement proper secrets management
6. Set up log aggregation
