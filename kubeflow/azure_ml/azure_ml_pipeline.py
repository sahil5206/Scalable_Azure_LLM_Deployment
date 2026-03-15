"""
Azure Machine Learning Pipeline for LLM workflows.

This is the Azure ML equivalent of the Kubeflow pipeline.
No installation required - Azure ML is fully managed!
"""
from azure.ai.ml import MLClient, dsl, Input, Output
from azure.ai.ml.entities import Environment, Code
from azure.identity import DefaultAzureCredential
from azure.ai.ml.constants import AssetTypes


def prepare_model_job(model_name: str, output_path: Output):
    """
    Prepare and download the LLM model using Azure ML job.
    
    Args:
        model_name: HuggingFace model identifier
        output_path: Output path for model
    """
    from azure.ai.ml import command
    
    return command(
        name="prepare_model",
        display_name="Prepare Model",
        description="Download and prepare LLM model",
        code="./",  # Path to your code
        command="python -c \"from transformers import AutoTokenizer; from huggingface_hub import snapshot_download; import os; model_path = snapshot_download('{model_name}'); print(f'Model saved to: {{model_path}}')\"".format(model_name=model_name),
        environment="azureml:pytorch-2.0-cuda11.8:1",
        compute="cpu-cluster",  # Or your compute target
        outputs={"model_path": output_path}
    )


def evaluate_model_job(model_path: Input, metrics_path: Output):
    """
    Evaluate the model using Azure ML job.
    
    Args:
        model_path: Input model path
        metrics_path: Output path for metrics
    """
    from azure.ai.ml import command
    
    return command(
        name="evaluate_model",
        display_name="Evaluate Model",
        description="Evaluate model performance",
        code="./",
        command="python evaluate_model.py --model_path ${{inputs.model_path}} --output ${{outputs.metrics_path}}",
        environment="azureml:pytorch-2.0-cuda11.8:1",
        compute="cpu-cluster",
        inputs={"model_path": model_path},
        outputs={"metrics_path": metrics_path}
    )


def deploy_to_managed_endpoint_job(model_path: Input, endpoint_name: str):
    """
    Deploy model to Azure ML Managed Endpoint (similar to KServe).
    
    Args:
        model_path: Input model path
        endpoint_name: Name for the managed endpoint
    """
    from azure.ai.ml import command
    
    return command(
        name="deploy_model",
        display_name="Deploy to Managed Endpoint",
        description="Deploy model to Azure ML managed endpoint",
        code="./",
        command="python deploy_model.py --model_path ${{inputs.model_path}} --endpoint_name {endpoint_name}".format(endpoint_name=endpoint_name),
        environment="azureml:pytorch-2.0-cuda11.8:1",
        compute="cpu-cluster",
        inputs={"model_path": model_path}
    )


@dsl.pipeline(
    name="llm-training-deployment-pipeline-aml",
    description="Azure ML Pipeline for LLM model preparation, evaluation, and deployment",
    compute="cpu-cluster"  # Default compute for all steps
)
def llm_pipeline_azure_ml(
    model_name: str = "microsoft/phi-2",
    endpoint_name: str = "llm-worker-phi2"
):
    """
    Main Azure ML pipeline for LLM model workflow.
    
    No Kubeflow installation needed - this runs on Azure ML!
    
    Args:
        model_name: HuggingFace model identifier
        endpoint_name: Name for the managed endpoint
    """
    # Step 1: Prepare model
    prepare_task = prepare_model_job(
        model_name=model_name,
        output_path=Output(type=AssetTypes.URI_FOLDER)
    )
    
    # Step 2: Evaluate model (optional)
    # evaluate_task = evaluate_model_job(
    #     model_path=prepare_task.outputs.model_path,
    #     metrics_path=Output(type=AssetTypes.URI_FILE)
    # )
    
    # Step 3: Deploy to Azure ML Managed Endpoint
    deploy_task = deploy_to_managed_endpoint_job(
        model_path=prepare_task.outputs.model_path,
        endpoint_name=endpoint_name
    )
    deploy_task.after(prepare_task)
    
    return {
        "model_path": prepare_task.outputs.model_path,
        "endpoint_name": endpoint_name
    }


# Example usage:
if __name__ == "__main__":
    # Connect to Azure ML workspace
    # No installation needed - just credentials!
    ml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id="<your-subscription-id>",
        resource_group_name="<your-resource-group>",
        workspace_name="<your-workspace-name>"
    )
    
    # Submit pipeline
    pipeline_job = ml_client.jobs.create_or_update(
        llm_pipeline_azure_ml(
            model_name="microsoft/phi-2",
            endpoint_name="llm-worker-phi2"
        )
    )
    
    print(f"Pipeline submitted: {pipeline_job.name}")
    print(f"View at: {pipeline_job.studio_url}")
