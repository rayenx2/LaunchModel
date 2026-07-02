terraform {
  required_providers {
    kubernetes = { source = "hashicorp/kubernetes", version = ">= 2.29.0" }
    helm       = { source = "hashicorp/helm",       version = ">= 2.13.0" }
    google     = { source = "hashicorp/google",     version = ">= 5.40.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_client_config" "default" {}
data "google_container_cluster" "cluster" {
  name     = var.cluster_name
  location = var.region
}

provider "kubernetes" {
  host                   = "https://${data.google_container_cluster.cluster.endpoint}"
  cluster_ca_certificate = base64decode(data.google_container_cluster.cluster.master_auth[0].cluster_ca_certificate)
  token                  = data.google_client_config.default.access_token
}

provider "helm" {
  kubernetes {
    host                   = "https://${data.google_container_cluster.cluster.endpoint}"
    cluster_ca_certificate = base64decode(data.google_container_cluster.cluster.master_auth[0].cluster_ca_certificate)
    token                  = data.google_client_config.default.access_token
  }
}

resource "helm_release" "kube_prom" {
  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = "monitoring"
  create_namespace = true
}

resource "helm_release" "app" {
  name       = "capstone"
  chart      = "${path.module}/../../deploy/helm/app"
  namespace  = "mlops"
  create_namespace = true
  set {
    name  = "image.repository"
    value = var.image_repository
  }
  set {
    name  = "image.tag"
    value = var.image_tag
  }
}
