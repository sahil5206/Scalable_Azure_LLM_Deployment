"""
Kubeflow Pipeline for LLM inference via Kafka.

This pipeline demonstrates how to use Kubeflow Pipelines
to orchestrate inference requests through the Kafka-based LLM worker.
"""
from kfp import dsl, compiler
from kfp.dsl import pipeline
from kafka_component import (
    send_inference_request,
    batch_inference_requests
)


@pipeline(
    name="llm-inference-pipeline",
    description="Pipeline for LLM inference via Kafka"
)
def inference_pipeline(
    kafka_bootstrap_servers: str = "kafka.kafka.svc.cluster.local:9092",
    request_topic: str = "llm-requests",
    response_topic: str = "llm-responses",
    prompt: str = "What is machine learning?",
    batch_prompts: str = "[]"  # JSON string of prompts list
):
    """
    Main inference pipeline.
    
    Args:
        kafka_bootstrap_servers: Kafka broker addresses
        request_topic: Topic for requests
        response_topic: Topic for responses
        prompt: Single prompt for inference
        batch_prompts: List of prompts for batch inference
    """
    import uuid
    
    # Single inference request
    single_inference = send_inference_request(
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        request_topic=request_topic,
        response_topic=response_topic,
        prompt=prompt,
        request_id=f"pipeline-{uuid.uuid4().hex[:8]}",
        timeout_seconds=60
    )
    single_inference.set_display_name("Single Inference Request")
    single_inference.set_cpu_limit("1")
    single_inference.set_memory_limit("2Gi")
    
    # Batch inference (if prompts provided)
    import json
    try:
        prompts_list = json.loads(batch_prompts) if batch_prompts else []
        if prompts_list:
            batch_inference = batch_inference_requests(
                kafka_bootstrap_servers=kafka_bootstrap_servers,
                request_topic=request_topic,
                response_topic=response_topic,
                prompts=prompts_list,
                timeout_seconds=120
            )
            batch_inference.set_display_name("Batch Inference Requests")
            batch_inference.set_cpu_limit("2")
            batch_inference.set_memory_limit("4Gi")
            batch_inference.after(single_inference)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse batch_prompts: {batch_prompts}")


if __name__ == "__main__":
    # Compile pipeline
    compiler.Compiler().compile(
        pipeline_func=inference_pipeline,
        package_path="inference_pipeline.yaml"
    )
    print("Inference pipeline compiled to inference_pipeline.yaml")
