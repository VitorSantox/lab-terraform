resource "google_container_cluster" "primary" {   # Recurso do cluster GKE
  name                     = var.cluster_name     # Nome do cluster
  location                 = var.region           # Região (cluster regional)
  remove_default_node_pool = true                 # Remove o pool padrão (evita criar 3 nós)
  initial_node_count       = 1                    # Valor exigido pela API; não cria nós
  deletion_protection      = var.deletion_protection # Permite destroy no lab
}

resource "google_container_node_pool" "primary_nodes" {  # Node pool gerenciado por nós
  name       = "${var.cluster_name}-pool"                # Nome do pool
  location   = var.region                                # Mesma região do cluster
  cluster    = google_container_cluster.primary.name     # Liga ao cluster criado
  node_count = var.node_count                            # Quantidade de nós desejada

  node_config {                                          # Config dos nós (VMs)
    machine_type = var.machine_type                      # Tipo de máquina (e2-micro p/ lab)
    disk_size_gb = var.disk_size                         # Tamanho do disco
    disk_type    = var.disk_type                         # Tipo do disco (pd-standard)
    oauth_scopes = var.oauth_scopes                      # Permissões amplas (lab)
  }
}
