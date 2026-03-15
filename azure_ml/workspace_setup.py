"""
Azure ML Workspace Setup Script.

Creates Azure ML workspace and compute resources.
No installation needed - just run this script!
"""
import sys
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Workspace, ComputeInstance, AmlCompute
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.core.exceptions import ResourceNotFoundError
from azure_ml.config import azure_ml_config


def create_workspace(
    subscription_id: str,
    resource_group_name: str,
    workspace_name: str,
    location: str = "eastus"
) -> MLClient:
    """
    Create or get Azure ML workspace.
    
    Args:
        subscription_id: Azure subscription ID
        resource_group_name: Resource group name
        workspace_name: Workspace name
        location: Azure region
    
    Returns:
        MLClient connected to workspace
    """
    print(f"Setting up Azure ML workspace: {workspace_name}")
    
    # Try to authenticate
    try:
        credential = DefaultAzureCredential()
        credential.get_token("https://management.azure.com/.default")
    except Exception:
        print("Using interactive browser authentication...")
        credential = InteractiveBrowserCredential()
    
    # Create MLClient
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name
    )
    
    # Try to get existing workspace
    try:
        workspace = ml_client.workspaces.get(workspace_name)
        print(f"✓ Workspace '{workspace_name}' already exists")
        print(f"  Location: {workspace.location}")
        print(f"  Workspace URL: {workspace.discovery_url}")
    except ResourceNotFoundError:
        print(f"Creating new workspace '{workspace_name}'...")
        workspace = Workspace(
            name=workspace_name,
            location=location,
            display_name=workspace_name,
            description="Azure ML workspace for LLM deployment"
        )
        ml_client.workspaces.begin_create(workspace).wait()
        print(f"✓ Workspace '{workspace_name}' created successfully")
    
    return ml_client


def create_compute_cluster(
    ml_client: MLClient,
    cluster_name: str,
    vm_size: str = "Standard_NC6s_v3",
    min_nodes: int = 0,
    max_nodes: int = 4
) -> AmlCompute:
    """
    Create or get compute cluster.
    
    Args:
        ml_client: MLClient instance
        cluster_name: Compute cluster name
        vm_size: VM size
        min_nodes: Minimum nodes
        max_nodes: Maximum nodes
    
    Returns:
        AmlCompute instance
    """
    print(f"\nSetting up compute cluster: {cluster_name}")
    
    try:
        compute = ml_client.compute.get(cluster_name)
        print(f"✓ Compute cluster '{cluster_name}' already exists")
        return compute
    except ResourceNotFoundError:
        print(f"Creating compute cluster '{cluster_name}'...")
        print(f"  VM Size: {vm_size}")
        print(f"  Nodes: {min_nodes}-{max_nodes}")
        
        compute = AmlCompute(
            name=cluster_name,
            size=vm_size,
            min_instances=min_nodes,
            max_instances=max_nodes,
            idle_time_before_scale_down=120,  # Scale down after 2 minutes idle
        )
        ml_client.compute.begin_create_or_update(compute).wait()
        print(f"✓ Compute cluster '{cluster_name}' created successfully")
        return compute


def setup_azure_ml():
    """Main setup function."""
    print("=" * 60)
    print("Azure ML Workspace Setup")
    print("=" * 60)
    
    # Get configuration
    config = azure_ml_config
    
    if not config.subscription_id:
        print("\n⚠️  Azure ML configuration not found!")
        print("Please set the following environment variables or update .env file:")
        print("  AZURE_ML_SUBSCRIPTION_ID=<your-subscription-id>")
        print("  AZURE_ML_RESOURCE_GROUP_NAME=<your-resource-group>")
        print("  AZURE_ML_WORKSPACE_NAME=<your-workspace-name>")
        print("\nOr run with parameters:")
        print("  python workspace_setup.py <subscription-id> <resource-group> <workspace-name>")
        sys.exit(1)
    
    # Create workspace
    ml_client = create_workspace(
        subscription_id=config.subscription_id,
        resource_group_name=config.resource_group_name,
        workspace_name=config.workspace_name,
        location=config.location
    )
    
    # Create compute cluster
    compute = create_compute_cluster(
        ml_client=ml_client,
        cluster_name=config.compute_cluster_name,
        vm_size=config.compute_vm_size,
        min_nodes=config.compute_min_nodes,
        max_nodes=config.compute_max_nodes
    )
    
    print("\n" + "=" * 60)
    print("✓ Azure ML setup complete!")
    print("=" * 60)
    print(f"\nWorkspace: {config.workspace_name}")
    print(f"Resource Group: {config.resource_group_name}")
    print(f"Compute Cluster: {config.compute_cluster_name}")
    print(f"\nYou can now run pipelines using:")
    print(f"  python azure_ml/pipelines/llm_pipeline.py")
    print(f"\nOr access the workspace at:")
    print(f"  https://ml.azure.com/")
    
    return ml_client


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 4:
        # Use command line arguments
        subscription_id = sys.argv[1]
        resource_group_name = sys.argv[2]
        workspace_name = sys.argv[3]
        location = sys.argv[4] if len(sys.argv) > 4 else "eastus"
        
        # Temporarily update config
        azure_ml_config.subscription_id = subscription_id
        azure_ml_config.resource_group_name = resource_group_name
        azure_ml_config.workspace_name = workspace_name
        azure_ml_config.location = location
    
    setup_azure_ml()
