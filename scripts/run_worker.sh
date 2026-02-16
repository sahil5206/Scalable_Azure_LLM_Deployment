#!/bin/bash
# Script to run LLM Worker Service

set -e

echo "Starting LLM Worker Service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "worker/.deps_installed" ]; then
    echo "Installing dependencies..."
    pip install -r worker/requirements.txt
    touch worker/.deps_installed
fi

# Check if Kafka is running
if ! docker ps | grep -q kafka; then
    echo "Starting Kafka..."
    docker-compose up -d kafka zookeeper
    echo "Waiting for Kafka to be ready..."
    sleep 10
fi

# Run worker
cd worker
python -m worker.main
