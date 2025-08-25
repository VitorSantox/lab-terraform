variable "project_id" {               # Projeto GCP
  type = string
}

variable "region" {                   # Região do banco (ex.: southamerica-east1)
  type = string
}

variable "db_instance_name" {         # Nome da instância Cloud SQL
  type = string
}

variable "db_version" {               # Versão do Postgres (ex.: POSTGRES_15)
  type    = string
  default = "POSTGRES_15"
}

variable "db_tier" {                  # Tamanho da instância (lab: db-f1-micro)
  type    = string
  default = "db-f1-micro"
}

variable "db_name" {                  # Nome do database lógico
  type = string
}

variable "db_user" {                  # Usuário de app
  type = string
}

variable "db_password" {              # Senha do usuário (armazenar via TF_VAR_*)
  type      = string
  sensitive = true
}
