variable "project_id" {
  type = string
  description = "devops-466923"
}

variable "region" {
  type = string
  default = "southamerica-east1"
}

variable "cluster_name" {
  type = string
  default = "terraform-cluster-4"
}

variable "node_count" {
  type = number
  default = 1
}

variable "machine_type" {
  type = string
  default = "e2-micro"
}

variable "disk_size"
  type = number
  default = 30
}

variable "disk_type" {
  type = string
  default = "pd-standard"
}
