variable "project_id" { type = string }
variable "region" { type = string  default = "europe-west2" }
variable "cluster_name" { type = string default = "cloudops-platform" }
variable "image_repository" { type = string default = "ghcr.io/rayenx2/cloudops-platform" }
variable "image_tag" { type = string default = "latest" }
