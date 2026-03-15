"""
Azure ML Pipeline for LLM model training and deployment.

No installation required - fully managed by Azure!
"""
from azure.ai.ml import MLClient, dsl, Input, Output, command
from azure.ai.ml.entities import Environment
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential
from pathlib import Path
import os


# Define custom environment for LLM workloads
def get_llm_environment(ml_client: MLClient) -> Environment:
    """Create or get LLM environment."""
    try:
        env = ml_client.environments.get("llm-environment", version="1")
        return env
    except Exception:
        # Create new environment
        env = Environment(
            name="llm-environment",
            version="1",
            description="Environment for LLM model training and inference",
            conda_file="azure_ml/environments/llm_environment.yml",
            image="mcr.microsoft.com/azureml/openmpi4.1.0-cuda11.8-cudnn8-ubuntu22.04:latest"
        )
        return ml_client.environments.create_or_update(env)


@dsl.pipeline(
    name="llm-training-deployment-pipeline",
    description="Azure ML Pipeline for LLM model preparation, evaluation, and deployment"
)
def llm_pipeline(
    model_name: str = "microsoft/phi-2",
    compute_cluster_name: str = "llm-compute-cluster"
):
    """
    Main Azure ML pipeline for LLM model workflow.
    
    Args:
        model_name: HuggingFace model identifier
        compute_cluster_name: Name of compute cluster
    """
    # Get code path (relative to project root)
    code_path = Path(__file__).parent.parent.parent
    
    # Step 1: Prepare Model
    prepare_model_step = command(
        name="prepare_model",
        display_name="Prepare LLM Model",
        description="Download and prepare LLM model from HuggingFace",
        code=str(code_path),
        command="python azure_ml/pipelines/components/prepare_model.py --model_name ${{inputs.model_name}} --output_path ${{outputs.model_path}}",
        environment="azureml:pytorch-2.0-cuda11.8:1",  # Use Azure ML curated environment
        compute=compute_cluster_name,
        inputs={
            "model_name": model_name
        },
        outputs={
            "model_path": Output(type=AssetTypes.URI_FOLDER)
        }
    )
    
    # Step 2: Evaluate Model (optional)
    evaluate_model_step = command(
        name="evaluate_model",
        display_name="Evaluate Model",
        description="Evaluate model performance",
        code=str(code_path),
        command="python azure_ml/pipelines/components/evaluate_model.py --model_path ${{inputs.model_path}} --output_path ${{outputs.metrics_path}}",
        environment="azureml:pytorch-2.0-cuda11.8:1",
        compute=compute_cluster_name,
        inputs={
            "model_path": prepare_model_step.outputs.model_path
        },
        outputs={
            "metrics_path": Output(type=AssetTypes.URI_FOLDER)
        }
    )
    evaluate_model_step.after(prepare_model_step)
    
    return {
        "model_path": prepare_model_step.outputs.model_path,
        "metrics_path": evaluate_model_step.outputs.metrics_path
    }


def submit_pipeline(
    subscription_id: str,
    resource_group_name: str,
    workspace_name: str,
    model_name: str = "microsoft/phi-2",
    compute_cluster_name: str = "llm-compute-cluster"
):
    """
    Submit pipeline to Azure ML.
    
    Args:
        subscription_id: Azure subscription ID
        resource_group_name: Resource group name
        workspace_name: Workspace name
        model_name: Model name
        compute_cluster_name: Compute cluster name
    """
    # Connect to workspace
    ml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name
    )
    
    # Create pipeline
    pipeline_job = llm_pipeline(
        model_name=model_name,
        compute_cluster_name=compute_cluster_name
    )
    
    # Submit pipeline
    print("Submitting pipeline to Azure ML...")
    submitted_job = ml_client.jobs.create_or_update(pipeline_job)
    
    print(f"✓ Pipeline submitted successfully!")
    print(f"  Job name: {submitted_job.name}")
    print(f"  Job ID: {submitted_job.id}")
    print(f"  Status: {submitted_job.status}")
    print(f"\nView pipeline at:")
    print(f"  {submitted_job.studio_url}")
    
    return submitted_job


if __name__ == "__main__":
    import sys
    from azure_ml.config import azure_ml_config
    
    # Get configuration
    config = azure_ml_config
    
    if not config.subscription_id:
        print("⚠️  Azure ML configuration not found!")
        print("Please set environment variables or update .env file:")
        print("  AZURE_ML_SUBSCRIPTION_ID")
        print("  AZURE_ML_RESOURCE_GROUP_NAME")
        print("  AZURE_ML_WORKSPACE_NAME")
        sys.exit(1)
    
    # Submit pipeline
    submit_pipeline(
        subscription_id=config.subscription_id,
        resource_group_name=config.resource_group_name,
        workspace_name=config.workspace_name,
        model_name=config.default_model_name,
        compute_cluster_name=config.compute_cluster_name
    )
