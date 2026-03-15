# Additional node pool for GPU workloads (LLM workers)
resource "azurerm_kubernetes_cluster_node_pool" "gpu" {
  count                 = var.enable_gpu_node_pool ? 1 : 0
  name                  = "gpu"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = var.gpu_node_vm_size
  node_count            = var.gpu_node_count
  enable_auto_scaling   = true
  min_count             = 0
  max_count             = var.gpu_node_max_count
  os_disk_size_gb       = 128
  vnet_subnet_id        = azurerm_subnet.aks.id

  node_labels = {
    workload = "gpu"
    gpu      = "true"
  }

  node_taints = [
    "gpu=true:NoSchedule"  # Only schedule GPU workloads
  ]

  tags = var.tags
}
