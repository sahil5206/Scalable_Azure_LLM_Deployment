# LLM Inference Platform - Architecture & Workflow

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Web Frontend - Port 8000)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/REST API
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Web Frontend Service                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  FastAPI Server                                           │ │
│  │  - REST API Endpoints                                     │ │
│  │  - Request/Response Handling                              │ │
│  │  - Kafka Producer/Consumer                                │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Kafka Messages
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Message Queue (Kafka)                        │
│  ┌──────────────────────┐      ┌──────────────────────┐      │
│  │  Request Topic       │      │  Response Topic       │      │
│  │  (llm-requests)      │      │  (llm-responses)      │      │
│  └──────────────────────┘      └──────────────────────┘      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Consume Requests
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    LLM Worker Service                            │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Kafka Consumer                                          │ │
│  │  - Consumes from llm-requests topic                      │ │
│  │  - Batch Processing                                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Request Processor                                       │ │
│  │  - Request Batching                                      │ │
│  │  - Concurrency Control                                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  LLM Model                                               │ │
│  │  - HuggingFace Models (Phi-2, TinyLlama, etc.)         │ │
│  │  - Text Generation                                       │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Kafka Producer                                          │ │
│  │  - Produces to llm-responses topic                       │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Produce Responses
                             │
                             ▼
                    (Back to Kafka → Web Frontend)
```

## 📊 Component Details

### 1. Web Frontend Service

**Technology**: FastAPI (Python)

**Responsibilities**:
- Serve web UI (HTML/CSS/JavaScript)
- Provide REST API endpoints
- Send inference requests to Kafka
- Receive and return responses to users
- Handle request/response correlation

**Key Components**:
- `web/main.py`: FastAPI application
- `web/config.py`: Configuration management
- `web/templates/index.html`: Web UI

**Endpoints**:
- `GET /`: Web interface
- `POST /api/inference`: Synchronous inference
- `POST /api/inference/async`: Asynchronous inference
- `GET /api/inference/{request_id}`: Get result
- `GET /health`: Health check

### 2. Kafka Message Queue

**Technology**: Apache Kafka (via Docker or AKS)

**Topics**:
- **llm-requests**: Incoming inference requests
  - Partitioned for parallel processing
  - Consumer groups for load balancing
- **llm-responses**: Generated responses
  - Matched to requests via request_id

**Configuration**:
- Auto-create topics enabled
- 3 partitions per topic (configurable)
- Replication factor: 1 (dev) / 3 (production)

### 3. LLM Worker Service

**Technology**: Python (Transformers, PyTorch)

**Responsibilities**:
- Load and manage LLM models
- Process inference requests in batches
- Generate text responses
- Handle errors and retries
- Expose metrics and health checks

**Key Components**:
- `worker/main.py`: Main service entry point
- `worker/models/llm_model.py`: Model loading and inference
- `worker/processor.py`: Request processing and batching
- `worker/kafka/consumer.py`: Kafka consumer
- `worker/kafka/producer.py`: Kafka producer
- `worker/metrics/prometheus_metrics.py`: Metrics collection

**Features**:
- Batch processing for efficiency
- Concurrency control (semaphore)
- Automatic model loading
- GPU/CPU support
- Health checks (liveness, readiness)

## 🔄 Workflows

### Workflow 1: User Inference Request (Synchronous)

```
1. User opens web UI (http://localhost:8000)
   └─> Web frontend serves HTML interface

2. User enters prompt and clicks "Generate Response"
   └─> JavaScript sends POST /api/inference

3. Web Frontend receives request
   ├─> Validates input
   ├─> Generates unique request_id
   └─> Sends message to Kafka (llm-requests topic)
       Message: {
         "request_id": "web-abc123",
         "prompt": "What is machine learning?",
         "max_tokens": 512,
         "temperature": 0.7,
         "timestamp": 1234567890
       }

4. Web Frontend subscribes to Kafka (llm-responses topic)
   └─> Waits for response with matching request_id

5. LLM Worker consumes message from Kafka
   ├─> Adds to batch queue
   ├─> Processes batch when ready
   └─> Generates text using LLM model

6. LLM Worker produces response to Kafka
   Message: {
     "request_id": "web-abc123",
     "status": "success",
     "generated_text": "Machine learning is...",
     "tokens_generated": 150,
     "timestamp": 1234567900
   }

7. Web Frontend receives response
   ├─> Matches request_id
   ├─> Formats response
   └─> Returns to user via HTTP response

8. User sees generated text in web UI
```

### Workflow 2: Asynchronous Inference

```
1. User sends async request
   └─> POST /api/inference/async

2. Web Frontend immediately returns request_id
   └─> {"request_id": "web-xyz789", "status": "submitted"}

3. User polls for result
   └─> GET /api/inference/web-xyz789

4. Background processing continues (same as Workflow 1)
   └─> Response available when ready
```

### Workflow 3: Batch Processing in Worker

```
1. Multiple requests arrive at Kafka
   └─> Worker consumer polls messages

2. Request Processor batches requests
   ├─> Collects up to BATCH_SIZE requests
   ├─> Or waits BATCH_TIMEOUT seconds
   └─> Creates batch

3. Batch Processing
   ├─> Prepares inputs for model
   ├─> Runs model inference (batch)
   └─> Processes outputs

4. Individual Responses
   ├─> Extracts response for each request
   ├─> Produces to Kafka (llm-responses)
   └─> Commits Kafka offsets
```

### Workflow 4: Deployment to Azure

```
1. Infrastructure Provisioning (Terraform)
   ├─> Create Resource Group
   ├─> Create AKS Cluster
   ├─> Create Container Registry
   ├─> Create Storage Account
   └─> Create Network Resources

2. Build Docker Images
   ├─> Build worker image
   ├─> Build web frontend image
   └─> Push to Azure Container Registry

3. Deploy to AKS
   ├─> Create Kubernetes namespace
   ├─> Deploy Kafka (or use Event Hubs)
   ├─> Deploy Worker service
   ├─> Deploy Web Frontend service
   └─> Configure ingress/load balancer

4. Service Discovery
   ├─> Services discover Kafka via DNS
   ├─> Web frontend accessible via LoadBalancer
   └─> Health checks verify readiness
```

## 🔀 Data Flow

### Request Flow

```
User Input
    │
    ▼
Web UI (Browser)
    │
    ▼
FastAPI Server
    │
    ├─> Validate Request
    ├─> Generate request_id
    └─> Produce to Kafka
        │
        ▼
    Kafka Topic (llm-requests)
        │
        ▼
    Worker Consumer
        │
        ├─> Add to Batch Queue
        └─> Process Batch
            │
            ▼
        LLM Model
            │
            ├─> Tokenize Input
            ├─> Generate Tokens
            └─> Decode Output
                │
                ▼
            Response Processor
                │
                └─> Produce to Kafka
                    │
                    ▼
                Kafka Topic (llm-responses)
                    │
                    ▼
                Web Frontend Consumer
                    │
                    ├─> Match request_id
                    └─> Return to User
```

### Response Flow

```
LLM Model Output
    │
    ▼
Response Processor
    │
    ├─> Format Response
    ├─> Add Metadata
    └─> Create Response Message
        │
        ▼
    Kafka Producer
        │
        ▼
    Kafka Topic (llm-responses)
        │
        ▼
    Web Frontend Consumer
        │
        ├─> Match by request_id
        ├─> Extract generated_text
        └─> Return HTTP Response
            │
            ▼
        Web UI (Browser)
            │
            ▼
        User Sees Response
```

## 🛠️ Technology Stack

### Frontend
- **Web UI**: HTML5, CSS3, JavaScript (Vanilla)
- **API Server**: FastAPI (Python)
- **Templating**: Jinja2

### Backend
- **Worker Service**: Python 3.11
- **ML Framework**: PyTorch, Transformers (HuggingFace)
- **Models**: Phi-2, TinyLlama (configurable)

### Message Queue
- **Kafka**: Apache Kafka 7.5.0
- **Alternative**: Azure Event Hubs (optional)

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes (AKS)
- **IaC**: Terraform
- **Registry**: Azure Container Registry

### Monitoring & Observability
- **Metrics**: Prometheus
- **Logging**: Structured JSON logs
- **Health Checks**: HTTP endpoints
- **Azure Monitoring**: Log Analytics

## 📈 Scalability

### Horizontal Scaling

1. **Web Frontend**
   - Multiple instances behind load balancer
   - Stateless design (no session storage)
   - Auto-scaling based on CPU/memory

2. **Worker Service**
   - Multiple worker instances
   - Same consumer group (load balancing)
   - Kafka partitions enable parallel processing
   - GPU node pool for compute-intensive workloads

3. **Kafka**
   - Multiple partitions per topic
   - Multiple brokers (production)
   - Replication for high availability

### Vertical Scaling

- **Worker Nodes**: GPU-enabled VMs for model inference
- **Kafka**: Larger VMs for higher throughput
- **Database**: N/A (stateless design)

## 🔒 Security

### Network Security
- Virtual Network isolation
- Network policies (Kubernetes)
- Private endpoints (optional)

### Authentication & Authorization
- Azure AD integration (AKS)
- RBAC for Kubernetes
- API keys for managed services

### Data Security
- Encryption at rest (Azure Storage)
- Encryption in transit (TLS)
- Secrets management (Kubernetes Secrets)

## 📊 Monitoring & Metrics

### Prometheus & Grafana Stack

The project includes a complete monitoring stack:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Pre-configured Dashboards**: LLM Platform-specific metrics
- **Alerting**: Configurable alert rules

**Deployment:**
```bash
# Quick deploy
./monitoring/deploy.sh  # or .\monitoring\deploy.ps1 on Windows

# Manual deploy
kubectl apply -f monitoring/prometheus/
kubectl apply -f monitoring/grafana/
```

See [monitoring/README.md](monitoring/README.md) for complete setup.

### Metrics Exposed

**Worker Service** (Prometheus format):
- `llm_worker_requests_total`: Total requests by status
- `llm_worker_request_duration_seconds`: Processing time
- `llm_worker_tokens_generated_total`: Tokens generated
- `llm_worker_kafka_consumer_lag`: Consumer lag
- `llm_worker_model_inference_duration_seconds`: Model inference time
- `llm_worker_active_requests`: Currently active requests
- `llm_worker_kafka_messages_consumed_total`: Kafka messages consumed
- `llm_worker_kafka_messages_produced_total`: Kafka messages produced

**Web Frontend**:
- Request count and latency
- Error rates
- Kafka connection status

### Health Checks

- **Web Frontend**: `GET /health`
- **Worker Service**: 
  - `GET /health`: Liveness
  - `GET /ready`: Readiness (model loaded, Kafka connected)
  - `GET /live`: Process running

## 🚀 Deployment Options

### Option 1: Local Development
```
Docker Compose
├─> Kafka + Zookeeper
├─> Worker Service
└─> Web Frontend
```

### Option 2: Azure Kubernetes Service with Jenkins CI/CD
```
Terraform
├─> AKS Cluster
├─> Container Registry
├─> Storage Account
└─> Network Resources

Kubernetes
├─> Jenkins (CI/CD)
├─> Kafka Deployment
├─> Worker Deployment
└─> Web Frontend Deployment

Jenkins Pipeline (Automated)
├─> Build Docker Images
├─> Push to ACR
├─> Deploy to Staging/Production
└─> Run Smoke Tests
```

### Option 3: Azure ML Integration
```
Azure ML Workspace
├─> ML Pipelines
├─> Model Registry
└─> Managed Endpoints

(Optional: Use instead of direct Kafka workers)
```

## 🔄 CI/CD Pipeline (Jenkins)

### Pipeline Architecture

```
Code Push (Git)
    │
    ▼
Jenkins Pipeline
    │
    ├─> Checkout Code
    ├─> Lint & Test
    ├─> Build Docker Images
    ├─> Push to ACR
    ├─> Azure ML Training (optional)
    ├─> Deploy to Staging (develop/staging branches)
    ├─> Deploy to Production (main branch)
    └─> Smoke Tests
```

### Deployment Flow

1. **Developer pushes code** to repository
2. **Jenkins detects change** (webhook or polling)
3. **Pipeline runs automatically**:
   - Builds images
   - Runs tests
   - Deploys to appropriate environment
4. **Smoke tests verify** deployment
5. **Notification sent** (if configured)

### Branch Strategy

- **main**: Deploys to production
- **develop/staging**: Deploys to staging
- **feature/***: Builds and tests only

## 🔄 State Management

### Stateless Design
- No session storage required
- Request/response correlation via request_id
- Horizontal scaling without state sharing

### Persistent Data
- Model files: Cached in container or Azure Storage
- Kafka offsets: Managed by Kafka
- Logs: Azure Log Analytics
- Jenkins data: Persistent volume in AKS

## 🎯 Key Design Decisions

1. **Event-Driven Architecture**: Kafka enables decoupling and scalability
2. **Batch Processing**: Improves throughput and GPU utilization
3. **Stateless Services**: Enables easy horizontal scaling
4. **Async by Default**: Non-blocking I/O for better performance
5. **Health Checks**: Kubernetes-ready for production deployments
6. **Observability**: Comprehensive metrics and logging

## 📝 Configuration Management

### Environment Variables

**Web Frontend**:
- `KAFKA_BOOTSTRAP_SERVERS`
- `PORT`
- `CORS_ORIGINS`

**Worker Service**:
- `KAFKA_BOOTSTRAP_SERVERS`
- `MODEL_NAME`
- `BATCH_SIZE`
- `MAX_CONCURRENT_REQUESTS`

### Configuration Files
- `worker/config.py`: Pydantic-based config
- `web/config.py`: Pydantic-based config
- `terraform/terraform.tfvars`: Infrastructure config

## 🔍 Error Handling

### Request Failures
- Retry logic in worker
- Error responses via Kafka
- User-friendly error messages in UI

### System Failures
- Health checks trigger restarts
- Kafka consumer groups handle failures
- Circuit breakers (optional)

## 📚 Next Steps

1. **Add Authentication**: OAuth2, JWT tokens
2. **Rate Limiting**: Protect against abuse
3. **Caching**: Cache common responses
4. **A/B Testing**: Multiple model versions
5. **Streaming Responses**: Real-time token streaming
6. **Multi-tenancy**: Isolated namespaces per tenant
