variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "llm-platform"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "llm-platform-rg"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    Environment = "production"
    Project     = "LLM-Inference"
    ManagedBy   = "Terraform"
  }
}

# AKS Configuration
variable "aks_cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
  default     = "llm-aks-cluster"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "aks_system_node_count" {
  description = "Number of system nodes in AKS"
  type        = number
  default     = 2
}

variable "aks_node_vm_size" {
  description = "VM size for AKS system nodes"
  type        = string
  default     = "Standard_D4s_v3"
}

# GPU Node Pool Configuration
variable "enable_gpu_node_pool" {
  description = "Enable GPU node pool for LLM workers"
  type        = bool
  default     = false
}

variable "gpu_node_count" {
  description = "Initial number of GPU nodes"
  type        = number
  default     = 0
}

variable "gpu_node_max_count" {
  description = "Maximum number of GPU nodes"
  type        = number
  default     = 4
}

variable "gpu_node_vm_size" {
  description = "VM size for GPU nodes"
  type        = string
  default     = "Standard_NC6s_v3"
}

# Container Registry
variable "acr_name" {
  description = "Name of Azure Container Registry (must be globally unique)"
  type        = string
  default     = ""
}

# Storage
variable "storage_account_name" {
  description = "Name of storage account (must be globally unique, lowercase, alphanumeric)"
  type        = string
  default     = ""
}

# Event Hubs (Kafka alternative)
variable "use_event_hubs" {
  description = "Use Azure Event Hubs instead of Kafka on AKS"
  type        = bool
  default     = false
}

# Application Gateway
variable "enable_application_gateway" {
  description = "Enable Application Gateway for web frontend"
  type        = bool
  default     = false
}
