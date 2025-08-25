terraform {                                         # Bloco Terraform
  required_version = ">= 1.6.0"                     # Versão mínima do Terraform

  required_providers {                              # Providers usados
    google = {                                      # Provider Google
      source  = "hashicorp/google"                  # Origem oficial
      version = "~> 5.0"                            # Faixa de versão estável
    }
  }
}

provider "google" {                                 # Configura o provider Google
  project = var.project_id                          # Projeto alvo
  region  = var.region                              # Região padrão
}
