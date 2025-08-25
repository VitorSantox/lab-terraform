resource "google_sql_database_instance" "db" {    # Instância Cloud SQL
  name                = var.db_instance_name      # Nome da instância
  database_version    = var.db_version            # Postgres versão
  region              = var.region                # Região do banco
  deletion_protection = false                     # Permite destruir no lab

  settings {                                       # Configurações da instância
    tier = var.db_tier                             # Tamanho (barato p/ lab)

    ip_configuration {                             # Rede/IP
      authorized_networks = {                      # Libera acesso (LAB APENAS)
          name  = "open-lab"                       # Rótulo da regra
          value = "0.0.0.0/0"                      # ⚠️ Aberto ao mundo (não faça em prod)
    }
  }
}

resource "google_sql_database" "app" {             # Banco (schema lógico) para a app
  name     = var.db_name                           # Nome do database
  instance = google_sql_database_instance.db.name  # Liga à instância
}

resource "google_sql_user" "appuser" {             # Usuário de aplicação
  name     = var.db_user                           # Nome do usuário
  instance = google_sql_database_instance.db.name  # Instância alvo
  password = var.db_password                       # Senha do usuário (sensível)
}
