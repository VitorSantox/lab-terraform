variable "project_id" {               # Projeto GCP
  type = string
  description = "devops-466923"
}

variable "region" {                    # Região principal
  type    = string
  default = "southamerica-east1"
}

variable "cluster_name" {              # Nome do cluster GKE
  type    = string
  default = "terraform-cluster-lab"
}

variable "node_count" {                # Nós do pool (lab)
  type    = number
  default = 1
}

variable "machine_type" {              # Tipo de máquina do nó
  type    = string
  default = "e2-micro"
}

variable "disk_size" {                 # Disco do nó (GB)
  type    = number
  default = 30
}

variable "disk_type" {                 # Tipo de disco
  type    = string
  default = "pd-standard"
}

# Pub/Sub
variable "pubsub_topic_name" {         # Tópico
  type    = string
  default = "api-events"
}

variable "pubsub_subscription_name" {  # Assinatura
  type    = string
  default = "api-events-sub"
}

# Cloud SQL
variable "db_instance_name" {          # Nome da instância
  type    = string
  default = "lab-postgres"
}

variable "db_version" {                # Versão do Postgres
  type    = string
  default = "POSTGRES_15"
}

variable "db_tier" {                   # Tamanho da instância
  type    = string
  default = "db-f1-micro"
}

variable "db_name" {                   # Database
  type    = string
  default = "appdb"
}

variable "db_user" {                   # Usuário de app
  type    = string
  default = "appuser"
}

variable "db_password" {               # Senha do usuário (não commitar em git)
  type      = string
  sensitive = true
}
