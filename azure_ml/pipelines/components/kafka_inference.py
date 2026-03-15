"""
Component: Send inference request via Kafka and receive response.
"""
import json
import time
import argparse
import uuid
from typing import Dict, Any


def send_kafka_request(
    bootstrap_servers: str,
    request_topic: str,
    response_topic: str,
    prompt: str,
    request_id: str,
    timeout_seconds: int = 60
) -> Dict[str, Any]:
    """
    Send inference request to Kafka and wait for response.
    
    Args:
        bootstrap_servers: Kafka broker addresses
        request_topic: Topic to send requests to
        response_topic: Topic to receive responses from
        prompt: Text prompt for inference
        request_id: Unique request identifier
        timeout_seconds: Maximum time to wait for response
    
    Returns:
        Response dictionary with generated text and status
    """
    from confluent_kafka import Producer, Consumer, KafkaError
    
    print(f"Sending inference request: {request_id}")
    print(f"Prompt: {prompt[:100]}...")
    
    # Create producer
    producer_config = {
        'bootstrap.servers': bootstrap_servers,
        'client.id': f'azure-ml-producer-{request_id}'
    }
    producer = Producer(producer_config)
    
    # Create consumer for responses
    consumer_config = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': f'azure-ml-consumer-{request_id}',
        'auto.offset.reset': 'latest',
        'enable.auto.commit': False
    }
    consumer = Consumer(consumer_config)
    consumer.subscribe([response_topic])
    
    # Prepare request message
    request_message = {
        "request_id": request_id,
        "prompt": prompt,
        "max_tokens": 512,
        "temperature": 0.7,
        "timestamp": time.time()
    }
    
    # Send request
    try:
        producer.produce(
            request_topic,
            key=request_id,
            value=json.dumps(request_message)
        )
        producer.flush()
        print(f"✓ Request sent to topic {request_topic}")
    except Exception as e:
        print(f"✗ Error sending request: {e}")
        consumer.close()
        return {"status": "error", "error": str(e), "generated_text": ""}
    
    # Wait for response
    start_time = time.time()
    response_data = None
    
    while time.time() - start_time < timeout_seconds:
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
            response_data = json.loads(msg.value().decode('utf-8'))
            
            # Check if this is our response
            if response_data.get("request_id") == request_id:
                print(f"✓ Received response for {request_id}")
                break
        except Exception as e:
            print(f"Error parsing response: {e}")
            continue
    
    consumer.close()
    
    if response_data is None:
        print(f"✗ Timeout waiting for response: {request_id}")
        return {"status": "timeout", "generated_text": ""}
    
    return {
        "status": response_data.get("status", "unknown"),
        "generated_text": response_data.get("generated_text", ""),
        "request_id": request_id
    }


def main():
    """Main function for Azure ML component."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--kafka_bootstrap_servers", type=str, required=True)
    parser.add_argument("--request_topic", type=str, default="llm-requests")
    parser.add_argument("--response_topic", type=str, default="llm-responses")
    parser.add_argument("--prompt", type=str, required=True)
    parser.add_argument("--request_id", type=str, default=None)
    parser.add_argument("--timeout_seconds", type=int, default=60)
    parser.add_argument("--output_path", type=str, required=True)
    args = parser.parse_args()
    
    # Generate request ID if not provided
    request_id = args.request_id or f"azure-ml-{uuid.uuid4().hex[:8]}"
    
    # Send request and get response
    response = send_kafka_request(
        bootstrap_servers=args.kafka_bootstrap_servers,
        request_topic=args.request_topic,
        response_topic=args.response_topic,
        prompt=args.prompt,
        request_id=request_id,
        timeout_seconds=args.timeout_seconds
    )
    
    # Save response
    import os
    os.makedirs(args.output_path, exist_ok=True)
    output_file = os.path.join(args.output_path, "response.json")
    with open(output_file, "w") as f:
        json.dump(response, f, indent=2)
    
    print(f"\n✓ Response saved to: {output_file}")
    print(f"Status: {response['status']}")
    if response.get('generated_text'):
        print(f"Generated text: {response['generated_text'][:200]}...")
    
    # Exit with error if request failed
    if response['status'] not in ['success', 'completed']:
        exit(1)


if __name__ == "__main__":
    main()
