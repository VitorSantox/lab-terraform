provider "google" {
  project = var.project.id
  region = var.region
}

terraform {
  required_pviders {
    google = {
      source = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.0"
}
