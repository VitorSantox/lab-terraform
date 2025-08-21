resource "google_container_cluster" "primary" {
  name = var.cluster_name
  location = var.region

  #remove o node pool padrão
  remove_default_node_pool = true
  initial_node_count = 1
  deletion_protection = false
}


#criando manualmente a config do pool de no com-pool pra diferenciar do nome do cluster
resource "google_container_node_pool" "primary_nodes" {
  name = "${var.cluster_name}-pool"
  location = var.region
  cluster = google_container_cluster.primary.name #liga este node_pool ao clsuter que criamos acima
  node_count = var.node_count

  #configuração dos no (maquina virtuais que compoes o cluster)
  node_config {
    machine_type = var.machine_type
    disk_size_gb = var.disk_size
    disk_type = var.disk_type
    #Escopo de autenticacao que os nos terao para aecssar apis na gcp
    #aqui usamos "cloud-plataform", que dá acesso amplo (bom para labs, mas em prd o ideal e restringir
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
      ]
  }
}
 
