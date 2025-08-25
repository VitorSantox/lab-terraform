output "cluster_name" {                        # Exibe o nome do cluster
  value = google_container_cluster.primary.name
}

output "endpoint" {                            # Endpoint da API do cluster
  value = google_container_cluster.primary.endpoint
}

output "ca_certificate" {                      # CA para configurar kubectl (se precisar)
  value = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
}

output "node_pool_name" {                      # Nome do node pool criado
  value = google_container_node_pool.primary_nodes.name
}

output "node_count" {                          # Quantidade de nós efetivos
  value = google_container_node_pool.primary_nodes.node_count
}
