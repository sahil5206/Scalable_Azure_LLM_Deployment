"""
Kubeflow Pipeline for LLM model training and deployment.

This pipeline orchestrates:
1. Model fine-tuning/preparation
2. Model evaluation
3. Model deployment to KServe
4. Integration with Kafka for inference requests
"""
from typing import NamedTuple
from kfp import dsl, compiler
from kfp.dsl import (
    component,
    Input,
    Output,
    Artifact,
    Model,
    Dataset,
    Metrics,
    ClassificationMetrics
)


@component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "transformers>=4.35.0",
        "torch>=2.0.0",
        "datasets>=2.14.0",
        "accelerate>=0.24.0",
        "huggingface-hub>=0.19.0"
    ]
)
def prepare_model(
    model_name: str,
    output_model_path: Output[Artifact]
) -> NamedTuple("Outputs", [("model_path", str), ("model_info", str)]):
    """
    Prepare and download the LLM model.
    
    Args:
        model_name: HuggingFace model identifier
        output_model_path: Output artifact path for model
    
    Returns:
        Model path and info
    """
    import os
    import json
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from huggingface_hub import snapshot_download
    
    print(f"Preparing model: {model_name}")
    
    # Download model
    model_path = snapshot_download(
        repo_id=model_name,
        cache_dir=output_model_path.path
    )
    
    # Load tokenizer to get model info
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model_info = {
        "model_name": model_name,
        "vocab_size": tokenizer.vocab_size,
        "model_path": model_path
    }
    
    # Save model info
    info_path = os.path.join(output_model_path.path, "model_info.json")
    with open(info_path, "w") as f:
        json.dump(model_info, f)
    
    outputs = NamedTuple("Outputs", [("model_path", str), ("model_info", str)])
    return outputs(model_path, json.dumps(model_info))


@component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "transformers>=4.35.0",
        "torch>=2.0.0",
        "datasets>=2.14.0",
        "accelerate>=0.24.0",
        "scikit-learn>=1.3.0"
    ]
)
def evaluate_model(
    model_path: Input[Artifact],
    test_dataset: Input[Dataset],
    metrics: Output[Metrics]
) -> NamedTuple("Outputs", [("accuracy", float), ("perplexity", float)]):
    """
    Evaluate the model on test dataset.
    
    Args:
        model_path: Input model artifact
        test_dataset: Test dataset
        metrics: Output metrics
    
    Returns:
        Accuracy and perplexity scores
    """
    import json
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    
    print(f"Evaluating model from: {model_path.path}")
    
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path.path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path.path,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None
    )
    
    # Load test dataset
    with open(test_dataset.path, "r") as f:
        test_data = json.load(f)
    
    # Simple evaluation (placeholder - implement actual evaluation logic)
    # This is a simplified example
    total_loss = 0.0
    num_samples = min(len(test_data), 10)  # Limit for demo
    
    model.eval()
    with torch.no_grad():
        for i, sample in enumerate(test_data[:num_samples]):
            text = sample.get("text", "")
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            outputs = model(**inputs, labels=inputs["input_ids"])
            total_loss += outputs.loss.item()
    
    avg_loss = total_loss / num_samples if num_samples > 0 else 0.0
    perplexity = torch.exp(torch.tensor(avg_loss)).item()
    accuracy = max(0.0, 1.0 - (avg_loss / 10.0))  # Simplified accuracy metric
    
    # Log metrics
    metrics.log_metric("perplexity", perplexity)
    metrics.log_metric("accuracy", accuracy)
    metrics.log_metric("avg_loss", avg_loss)
    
    print(f"Evaluation complete - Perplexity: {perplexity:.4f}, Accuracy: {accuracy:.4f}")
    
    outputs = NamedTuple("Outputs", [("accuracy", float), ("perplexity", float)])
    return outputs(accuracy, perplexity)


@component(
    base_image="python:3.11-slim",
    packages_to_install=["kubernetes>=28.0.0", "requests>=2.31.0"]
)
def deploy_to_kserve(
    model_path: Input[Artifact],
    model_name: str,
    namespace: str = "kubeflow"
) -> str:
    """
    Deploy model to KServe for serving.
    
    Args:
        model_path: Model artifact path
        model_name: Name for the deployed model
        namespace: Kubernetes namespace
    
    Returns:
        Inference service URL
    """
    import json
    import yaml
    from kubernetes import client, config
    
    print(f"Deploying model {model_name} to KServe")
    
    # Load kubeconfig (assumes running in cluster or kubeconfig available)
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
    
    api_client = client.ApiClient()
    custom_api = client.CustomObjectsApi(api_client)
    
    # Create InferenceService manifest
    inference_service = {
        "apiVersion": "serving.kserve.io/v1beta1",
        "kind": "InferenceService",
        "metadata": {
            "name": model_name,
            "namespace": namespace,
            "annotations": {
                "serving.kserve.io/deploymentMode": "Serverless"
            }
        },
        "spec": {
            "predictor": {
                "containers": [{
                    "name": "kserve-container",
                    "image": "your-registry/llm-worker:latest",  # Update with your image
                    "env": [
                        {"name": "MODEL_NAME", "value": model_name},
                        {"name": "MODEL_PATH", "value": model_path.path},
                        {"name": "KAFKA_BOOTSTRAP_SERVERS", "value": "kafka:29092"}
                    ],
                    "resources": {
                        "requests": {
                            "cpu": "2",
                            "memory": "8Gi"
                        },
                        "limits": {
                            "cpu": "4",
                            "memory": "16Gi"
                        }
                    }
                }]
            }
        }
    }
    
    # Apply InferenceService
    try:
        custom_api.create_namespaced_custom_object(
            group="serving.kserve.io",
            version="v1beta1",
            namespace=namespace,
            plural="inferenceservices",
            body=inference_service
        )
        print(f"InferenceService {model_name} created successfully")
    except Exception as e:
        print(f"Error creating InferenceService: {e}")
        # Try to update if exists
        try:
            custom_api.patch_namespaced_custom_object(
                group="serving.kserve.io",
                version="v1beta1",
                namespace=namespace,
                plural="inferenceservices",
                name=model_name,
                body=inference_service
            )
            print(f"InferenceService {model_name} updated successfully")
        except Exception as e2:
            print(f"Error updating InferenceService: {e2}")
            raise
    
    # Return inference URL (construct based on your setup)
    inference_url = f"http://{model_name}.{namespace}.svc.cluster.local/v1/models/{model_name}:predict"
    return inference_url


@dsl.pipeline(
    name="llm-training-deployment-pipeline",
    description="Pipeline for LLM model preparation, evaluation, and deployment"
)
def llm_pipeline(
    model_name: str = "microsoft/phi-2",
    namespace: str = "kubeflow"
):
    """
    Main pipeline for LLM model workflow.
    
    Args:
        model_name: HuggingFace model identifier
        namespace: Kubernetes namespace for deployment
    """
    # Step 1: Prepare model
    prepare_task = prepare_model(model_name=model_name)
    prepare_task.set_display_name("Prepare Model")
    prepare_task.set_cpu_limit("4")
    prepare_task.set_memory_limit("16Gi")
    
    # Step 2: Evaluate model (placeholder - would need actual test dataset)
    # For now, we'll skip evaluation or make it optional
    # evaluate_task = evaluate_model(
    #     model_path=prepare_task.outputs["output_model_path"],
    #     test_dataset=test_dataset
    # )
    
    # Step 3: Deploy to KServe
    deploy_task = deploy_to_kserve(
        model_path=prepare_task.outputs["output_model_path"],
        model_name=model_name.replace("/", "-").lower(),
        namespace=namespace
    )
    deploy_task.set_display_name("Deploy to KServe")
    deploy_task.after(prepare_task)


if __name__ == "__main__":
    # Compile pipeline
    compiler.Compiler().compile(
        pipeline_func=llm_pipeline,
        package_path="llm_pipeline.yaml"
    )
    print("Pipeline compiled to llm_pipeline.yaml")
