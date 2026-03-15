#!/bin/bash
# Start all services for local development

echo "Starting LLM Inference Platform..."
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start Kafka and Zookeeper
echo "Starting Kafka and Zookeeper..."
docker-compose up -d kafka zookeeper

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
sleep 10

# Start Worker (in background)
echo "Starting Worker service..."
cd worker
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

# Start worker in background
python -m worker.main &
WORKER_PID=$!
echo "Worker started (PID: $WORKER_PID)"

cd ..

# Start Web Frontend
echo "Starting Web Frontend..."
cd web
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

# Start web server
echo ""
echo "=================================="
echo "✓ All services started!"
echo "=================================="
echo "Web UI: http://localhost:8000"
echo "Worker Health: http://localhost:8081/health"
echo "Worker Metrics: http://localhost:8080/metrics"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

python -m web.main

# Cleanup on exit
trap "kill $WORKER_PID 2>/dev/null; docker-compose down; exit" INT TERM
