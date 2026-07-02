terraform {
  required_providers {
    google = { source = "hashicorp/google", version = ">= 5.40.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_container_cluster" "autopilot" {
  name     = var.cluster_name
  location = var.region
  enable_autopilot = true
  release_channel { channel = "REGULAR" }
  ip_allocation_policy {}
}

output "cluster_name" { value = google_container_cluster.autopilot.name }
output "location"     { value = google_container_cluster.autopilot.location }
