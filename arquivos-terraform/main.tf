module "gke" {                                      # Módulo do GKE
  source            = "./modules/gke"                # Caminho do módulo
  project_id        = var.project_id                 # Projeto
  region            = var.region                     # Região
  cluster_name      = var.cluster_name               # Nome do cluster
  node_count        = var.node_count                 # Nós (lab: 1)
  machine_type      = var.machine_type               # Tipo de máquina
  disk_size         = var.disk_size                  # Tamanho do disco
  disk_type         = var.disk_type                  # Tipo do disco
  deletion_protection = false                        # Destrutível no lab
}

module "pubsub" {                                   # Módulo do Pub/Sub
  source            = "./modules/pubsub"             # Caminho do módulo
  project_id        = var.project_id                 # Projeto
  topic_name        = var.pubsub_topic_name          # Nome do tópico
  subscription_name = var.pubsub_subscription_name   # Nome da assinatura
}

module "sql" {                                      # Módulo do Cloud SQL
  source           = "./modules/sql"                 # Caminho do módulo
  project_id       = var.project_id                  # Projeto
  region           = var.region                      # Região
  db_instance_name = var.db_instance_name            # Nome da instância
  db_version       = var.db_version                  # Versão do Postgres
  db_tier          = var.db_tier                     # Tamanho (barato p/ lab)
  db_name          = var.db_name                     # Database lógico
  db_user          = var.db_user                     # Usuário de app
  db_password      = var.db_password                 # Senha (use TF_VAR_*)
}
