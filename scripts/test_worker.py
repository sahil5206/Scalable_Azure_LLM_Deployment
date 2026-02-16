"""
Test script for LLM Worker Service.

Sends test requests to Kafka and verifies responses.
"""
import json
import time
from confluent_kafka import Producer, Consumer, KafkaError
import uuid

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
REQUEST_TOPIC = "llm-requests"
RESPONSE_TOPIC = "llm-responses"


def produce_test_request():
    """Produce a test request to Kafka."""
    producer = Producer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'acks': 'all'
    })
    
    request_id = str(uuid.uuid4())
    request = {
        'request_id': request_id,
        'prompt': 'What is machine learning?',
        'max_new_tokens': 100,
        'temperature': 0.7
    }
    
    producer.produce(
        REQUEST_TOPIC,
        value=json.dumps(request).encode('utf-8'),
        key=request_id.encode('utf-8')
    )
    producer.flush()
    
    print(f"Sent request: {request_id}")
    return request_id


def consume_response(request_id, timeout=60):
    """Consume response from Kafka."""
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': f'test-consumer-{uuid.uuid4()}',
        'auto.offset.reset': 'latest'
    })
    
    consumer.subscribe([RESPONSE_TOPIC])
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        msg = consumer.poll(timeout=1.0)
        
        if msg is None:
            continue
        
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(f"Consumer error: {msg.error()}")
                break
        
        try:
            response = json.loads(msg.value().decode('utf-8'))
            if response.get('request_id') == request_id:
                print(f"Received response: {json.dumps(response, indent=2)}")
                consumer.close()
                return response
        except Exception as e:
            print(f"Error parsing response: {e}")
    
    consumer.close()
    print(f"Timeout waiting for response: {request_id}")
    return None


if __name__ == "__main__":
    print("Testing LLM Worker Service...")
    request_id = produce_test_request()
    response = consume_response(request_id)
    
    if response:
        print("Test completed successfully!")
    else:
        print("Test failed: No response received")
