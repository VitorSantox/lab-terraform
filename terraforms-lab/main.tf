resource "google_container_cluster" "primary" {
  name = var.cluster_name
  location = var.region

  #remove o node pool padrão
  remove_default_node_pool = true
  initial_node_count = 1


resource "google_container_node_pool" "primary_nodes" {
  name = "${var.cluster_name}-pool"
  location = var.region
  cluster = google_container_cluster.primary.name
  node_count = car.node_count


  node_config {
    machine_type = var.machine_type
    disk_size_gb = var.disk_size
    disk_type = var.disk_type
    ouath_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
      ]
  }
}
 
