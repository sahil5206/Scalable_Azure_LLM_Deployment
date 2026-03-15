"""
Azure ML Pipeline for LLM inference via Kafka.

Integrates with existing Kafka-based LLM worker system.
"""
from azure.ai.ml import MLClient, dsl, Input, Output, command
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential
from pathlib import Path


@dsl.pipeline(
    name="llm-inference-pipeline",
    description="Azure ML Pipeline for LLM inference via Kafka"
)
def inference_pipeline(
    kafka_bootstrap_servers: str,
    request_topic: str = "llm-requests",
    response_topic: str = "llm-responses",
    prompt: str = "What is machine learning?",
    compute_cluster_name: str = "llm-compute-cluster"
):
    """
    Inference pipeline that sends requests via Kafka.
    
    Args:
        kafka_bootstrap_servers: Kafka broker addresses
        request_topic: Topic for requests
        response_topic: Topic for responses
        prompt: Text prompt for inference
        compute_cluster_name: Compute cluster name
    """
    code_path = Path(__file__).parent.parent.parent
    
    # Single inference request via Kafka
    inference_step = command(
        name="kafka_inference",
        display_name="Kafka Inference Request",
        description="Send inference request via Kafka and receive response",
        code=str(code_path),
        command="python azure_ml/pipelines/components/kafka_inference.py "
                "--kafka_bootstrap_servers ${{inputs.kafka_bootstrap_servers}} "
                "--request_topic ${{inputs.request_topic}} "
                "--response_topic ${{inputs.response_topic}} "
                "--prompt ${{inputs.prompt}} "
                "--output_path ${{outputs.response_path}}",
        environment="azureml:python:3.11",  # Lightweight environment for Kafka
        compute=compute_cluster_name,
        inputs={
            "kafka_bootstrap_servers": kafka_bootstrap_servers,
            "request_topic": request_topic,
            "response_topic": response_topic,
            "prompt": prompt
        },
        outputs={
            "response_path": Output(type=AssetTypes.URI_FOLDER)
        }
    )
    
    return {
        "response_path": inference_step.outputs.response_path
    }


def submit_inference_pipeline(
    subscription_id: str,
    resource_group_name: str,
    workspace_name: str,
    kafka_bootstrap_servers: str,
    prompt: str = "What is machine learning?",
    compute_cluster_name: str = "llm-compute-cluster"
):
    """
    Submit inference pipeline to Azure ML.
    
    Args:
        subscription_id: Azure subscription ID
        resource_group_name: Resource group name
        workspace_name: Workspace name
        kafka_bootstrap_servers: Kafka broker addresses
        prompt: Inference prompt
        compute_cluster_name: Compute cluster name
    """
    ml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name
    )
    
    pipeline_job = inference_pipeline(
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        prompt=prompt,
        compute_cluster_name=compute_cluster_name
    )
    
    print("Submitting inference pipeline...")
    submitted_job = ml_client.jobs.create_or_update(pipeline_job)
    
    print(f"✓ Pipeline submitted!")
    print(f"  Job: {submitted_job.name}")
    print(f"  View at: {submitted_job.studio_url}")
    
    return submitted_job


if __name__ == "__main__":
    import sys
    from azure_ml.config import azure_ml_config
    
    config = azure_ml_config
    
    if not config.subscription_id or not config.kafka_bootstrap_servers:
        print("⚠️  Configuration missing!")
        print("Required: AZURE_ML_SUBSCRIPTION_ID, AZURE_ML_RESOURCE_GROUP_NAME,")
        print("         AZURE_ML_WORKSPACE_NAME, KAFKA_BOOTSTRAP_SERVERS")
        sys.exit(1)
    
    submit_inference_pipeline(
        subscription_id=config.subscription_id,
        resource_group_name=config.resource_group_name,
        workspace_name=config.workspace_name,
        kafka_bootstrap_servers=config.kafka_bootstrap_servers,
        prompt="What is artificial intelligence?"
    )
