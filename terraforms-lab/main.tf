resource "google_container_cluster" "primary" {
  name = var.cluster_name
  location = var.region

  initial_node_count = 3

  node_config {
    machine_type = "e2-micro"
    disk_size_gb = 50
    disk_type = "pd-standard"
  }
}
 
