variables "project_id" {
  types = string
  description = "devops-466923"
}

variable "region" {
  type = string
  default = "us-central1"
}

variables "cluster_name"
  type = string
  default = "terraform-cluster"
}
