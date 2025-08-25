output "instance_connection_name" {        # string <project>:<region>:<instance>
  value = google_sql_database_instance.db.connection_name
}

output "public_ip" {                        # IP público da instância (lab)
  value = google_sql_database_instance.db.public_ip_address
}

output "database" {                         # Nome do database criado
  value = google_sql_database.app.name
}

output "db_user" {                          # Usuário de app
  value = google_sql_user.appuser.name
  sensitive = false
}
