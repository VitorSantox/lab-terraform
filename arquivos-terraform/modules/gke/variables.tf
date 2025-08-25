variable "project_id" {               # ID do projeto GCP
  type = string
}

variable "region" {                   # Região do cluster (ex.: southamerica-east1)
  type = string
}

variable "cluster_name" {             # Nome do cluster GKE
  type = string
}

variable "node_count" {               # Quantidade de nós no node pool (para lab: 1)
  type    = number
  default = 1
}

variable "machine_type" {             # Tipo de máquina (ex.: e2-micro)
  type = string
}

variable "disk_size" {                # Tamanho do disco da VM (GB)
  type = number
}

variable "disk_type" {                # Tipo de disco (pd-standard para evitar quota SSD)
  type = string
}

variable "oauth_scopes" {             # Escopos de API para os nós (amplo para lab)
  type    = list(string)
  default = ["https://www.googleapis.com/auth/cloud-platform"]
}

variable "deletion_protection" {      # Permite destruir o cluster no lab
  type    = bool
  default = false
}
