# Kubernetes provider configuration
provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.main.kube_config.0.host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.main.kube_config.0.client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.main.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.main.kube_config.0.cluster_ca_certificate)
}

# Namespace for LLM platform
resource "kubernetes_namespace" "llm" {
  metadata {
    name = "llm-platform"
    labels = {
      app = "llm-platform"
    }
  }
}

# Kafka deployment (using Strimzi operator or Bitnami Kafka)
resource "kubernetes_deployment" "kafka" {
  count = var.use_event_hubs ? 0 : 1
  
  metadata {
    name      = "kafka"
    namespace = kubernetes_namespace.llm.metadata[0].name
    labels = {
      app = "kafka"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "kafka"
      }
    }

    template {
      metadata {
        labels = {
          app = "kafka"
        }
      }

      spec {
        container {
          name  = "kafka"
          image = "confluentinc/cp-kafka:7.5.0"

          port {
            container_port = 9092
          }

          env {
            name  = "KAFKA_BROKER_ID"
            value = "1"
          }

          env {
            name  = "KAFKA_ZOOKEEPER_CONNECT"
            value = "zookeeper:2181"
          }

          env {
            name  = "KAFKA_ADVERTISED_LISTENERS"
            value = "PLAINTEXT://kafka:9092"
          }

          env {
            name  = "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR"
            value = "1"
          }

          resources {
            requests = {
              cpu    = "500m"
              memory = "1Gi"
            }
            limits = {
              cpu    = "2"
              memory = "2Gi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "kafka" {
  count = var.use_event_hubs ? 0 : 1
  
  metadata {
    name      = "kafka"
    namespace = kubernetes_namespace.llm.metadata[0].name
  }

  spec {
    selector = {
      app = "kafka"
    }

    port {
      port        = 9092
      target_port = 9092
    }

    type = "ClusterIP"
  }
}

# Zookeeper for Kafka
resource "kubernetes_deployment" "zookeeper" {
  count = var.use_event_hubs ? 0 : 1
  
  metadata {
    name      = "zookeeper"
    namespace = kubernetes_namespace.llm.metadata[0].name
    labels = {
      app = "zookeeper"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "zookeeper"
      }
    }

    template {
      metadata {
        labels = {
          app = "zookeeper"
        }
      }

      spec {
        container {
          name  = "zookeeper"
          image = "confluentinc/cp-zookeeper:7.5.0"

          port {
            container_port = 2181
          }

          env {
            name  = "ZOOKEEPER_CLIENT_PORT"
            value = "2181"
          }

          resources {
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "1"
              memory = "1Gi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "zookeeper" {
  count = var.use_event_hubs ? 0 : 1
  
  metadata {
    name      = "zookeeper"
    namespace = kubernetes_namespace.llm.metadata[0].name
  }

  spec {
    selector = {
      app = "zookeeper"
    }

    port {
      port        = 2181
      target_port = 2181
    }

    type = "ClusterIP"
  }
}

# ConfigMap for application configuration
resource "kubernetes_config_map" "app_config" {
  metadata {
    name      = "llm-app-config"
    namespace = kubernetes_namespace.llm.metadata[0].name
  }

  data = {
    KAFKA_BOOTSTRAP_SERVERS = var.use_event_hubs ? "${azurerm_eventhub_namespace.main[0].name}.servicebus.windows.net:9093" : "kafka:9092"
    KAFKA_REQUEST_TOPIC     = "llm-requests"
    KAFKA_RESPONSE_TOPIC    = "llm-responses"
    MODEL_NAME              = "microsoft/phi-2"
    BATCH_SIZE              = "4"
  }
}

# Secret for ACR credentials
resource "kubernetes_secret" "acr" {
  metadata {
    name      = "acr-secret"
    namespace = kubernetes_namespace.llm.metadata[0].name
  }

  type = "kubernetes.io/dockerconfigjson"

  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "${azurerm_container_registry.main.login_server}" = {
          username = azurerm_container_registry.main.admin_username
          password = azurerm_container_registry.main.admin_password
          auth     = base64encode("${azurerm_container_registry.main.admin_username}:${azurerm_container_registry.main.admin_password}")
        }
      }
    })
  }
}
