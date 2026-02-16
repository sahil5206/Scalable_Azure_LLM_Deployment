#!/bin/bash
# Script to create Kafka topics for LLM inference platform

KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}

echo "Creating Kafka topics..."

# Create request topic
kafka-topics.sh --create \
  --bootstrap-server $KAFKA_BOOTSTRAP_SERVERS \
  --topic llm-requests \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=86400000 \
  --if-not-exists

# Create response topic
kafka-topics.sh --create \
  --bootstrap-server $KAFKA_BOOTSTRAP_SERVERS \
  --topic llm-responses \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=86400000 \
  --if-not-exists

echo "Topics created successfully!"
