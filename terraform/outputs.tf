output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.name
}

output "aks_cluster_fqdn" {
  description = "FQDN of the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.fqdn
}

output "acr_login_server" {
  description = "ACR login server URL"
  value       = azurerm_container_registry.main.login_server
}

output "acr_admin_username" {
  description = "ACR admin username"
  value       = azurerm_container_registry.main.admin_username
  sensitive   = true
}

output "acr_admin_password" {
  description = "ACR admin password"
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "storage_account_primary_key" {
  description = "Storage account primary key"
  value       = azurerm_storage_account.main.primary_access_key
  sensitive   = true
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID"
  value       = azurerm_log_analytics_workspace.main.workspace_id
}

output "event_hub_namespace" {
  description = "Event Hub namespace (if enabled)"
  value       = var.use_event_hubs ? azurerm_eventhub_namespace.main[0].name : null
}

output "kube_config_command" {
  description = "Command to get kubeconfig"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_kubernetes_cluster.main.name}"
}

output "deployment_instructions" {
  description = "Instructions for deploying the application"
  value = <<-EOT
    To deploy the application:
    
    1. Get AKS credentials:
       az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_kubernetes_cluster.main.name}
    
    2. Build and push Docker images:
       az acr login --name ${azurerm_container_registry.main.name}
       docker build -t ${azurerm_container_registry.main.login_server}/llm-worker:latest -f docker/worker/Dockerfile .
       docker build -t ${azurerm_container_registry.main.login_server}/llm-web:latest -f docker/web/Dockerfile .
       docker push ${azurerm_container_registry.main.login_server}/llm-worker:latest
       docker push ${azurerm_container_registry.main.login_server}/llm-web:latest
    
    3. Deploy using kubectl or Helm charts
  EOT
}
