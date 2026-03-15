"""
Kubeflow Pipeline component for Kafka integration.

This component allows pipelines to send inference requests to Kafka
and receive responses, enabling integration with the LLM worker service.
"""
from typing import NamedTuple
from kfp import dsl
from kfp.dsl import component, Input, Output, Artifact


@component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "confluent-kafka>=2.3.0",
        "pydantic>=2.5.0"
    ]
)
def send_inference_request(
    kafka_bootstrap_servers: str,
    request_topic: str,
    response_topic: str,
    prompt: str,
    request_id: str,
    timeout_seconds: int = 60
) -> NamedTuple("Outputs", [("response", str), ("success", bool)]):
    """
    Send an inference request to Kafka and wait for response.
    
    Args:
        kafka_bootstrap_servers: Kafka broker addresses
        request_topic: Topic to send requests to
        response_topic: Topic to receive responses from
        prompt: Text prompt for inference
        request_id: Unique request identifier
        timeout_seconds: Maximum time to wait for response
    
    Returns:
        Response text and success status
    """
    import json
    import time
    from confluent_kafka import Producer, Consumer, KafkaError
    
    print(f"Sending inference request: {request_id}")
    
    # Create producer
    producer_config = {
        'bootstrap.servers': kafka_bootstrap_servers,
        'client.id': f'kubeflow-producer-{request_id}'
    }
    producer = Producer(producer_config)
    
    # Create consumer for responses
    consumer_config = {
        'bootstrap.servers': kafka_bootstrap_servers,
        'group.id': f'kubeflow-consumer-{request_id}',
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
        print(f"Request sent to topic {request_topic}")
    except Exception as e:
        print(f"Error sending request: {e}")
        outputs = NamedTuple("Outputs", [("response", str), ("success", bool)])
        return outputs("", False)
    
    # Wait for response
    start_time = time.time()
    response_text = ""
    success = False
    
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
                response_text = response_data.get("generated_text", "")
                success = response_data.get("status") == "success"
                print(f"Received response for {request_id}")
                break
        except Exception as e:
            print(f"Error parsing response: {e}")
            continue
    
    consumer.close()
    
    if not success:
        print(f"Timeout or error waiting for response: {request_id}")
    
    outputs = NamedTuple("Outputs", [("response", str), ("success", bool)])
    return outputs(response_text, success)


@component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "confluent-kafka>=2.3.0",
        "pydantic>=2.5.0"
    ]
)
def batch_inference_requests(
    kafka_bootstrap_servers: str,
    request_topic: str,
    response_topic: str,
    prompts: list,
    timeout_seconds: int = 120
) -> NamedTuple("Outputs", [("responses", str), ("success_count", int)]):
    """
    Send multiple inference requests in batch.
    
    Args:
        kafka_bootstrap_servers: Kafka broker addresses
        request_topic: Topic to send requests to
        response_topic: Topic to receive responses from
        prompts: List of prompts to process
        timeout_seconds: Maximum time to wait for all responses
    
    Returns:
        JSON string of all responses and success count
    """
    import json
    import uuid
    import time
    from confluent_kafka import Producer, Consumer, KafkaError
    
    print(f"Sending batch of {len(prompts)} inference requests")
    
    # Create producer
    producer_config = {
        'bootstrap.servers': kafka_bootstrap_servers,
        'client.id': 'kubeflow-batch-producer'
    }
    producer = Producer(producer_config)
    
    # Create consumer for responses
    consumer_config = {
        'bootstrap.servers': kafka_bootstrap_servers,
        'group.id': f'kubeflow-batch-consumer-{uuid.uuid4().hex[:8]}',
        'auto.offset.reset': 'latest',
        'enable.auto.commit': False
    }
    consumer = Consumer(consumer_config)
    consumer.subscribe([response_topic])
    
    # Generate request IDs and send requests
    request_ids = []
    for i, prompt in enumerate(prompts):
        request_id = f"batch-{uuid.uuid4().hex[:8]}"
        request_ids.append(request_id)
        
        request_message = {
            "request_id": request_id,
            "prompt": prompt,
            "max_tokens": 512,
            "temperature": 0.7,
            "timestamp": time.time()
        }
        
        try:
            producer.produce(
                request_topic,
                key=request_id,
                value=json.dumps(request_message)
            )
        except Exception as e:
            print(f"Error sending request {request_id}: {e}")
    
    producer.flush()
    print(f"Sent {len(request_ids)} requests")
    
    # Collect responses
    responses = {}
    start_time = time.time()
    success_count = 0
    
    while time.time() - start_time < timeout_seconds and len(responses) < len(request_ids):
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
            request_id = response_data.get("request_id")
            
            if request_id in request_ids:
                responses[request_id] = response_data
                if response_data.get("status") == "success":
                    success_count += 1
                print(f"Received response {len(responses)}/{len(request_ids)}")
        except Exception as e:
            print(f"Error parsing response: {e}")
            continue
    
    consumer.close()
    
    outputs = NamedTuple("Outputs", [("responses", str), ("success_count", int)])
    return outputs(json.dumps(responses), success_count)
