# Main Provider Configuration for ECG Multi-Agent System Infrastructure

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.38.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.38.0"
    }
  }

  # Uncomment and configure remote GCS backend in production
  # backend "gcs" {
  #   bucket = "ecg-terraform-state-prod"
  #   prefix = "terraform/state/agent-ecg"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required Google Cloud APIs for Agent Engine, BigQuery, Firestore, and Secret Manager
resource "google_project_service" "required_apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "run.googleapis.com",
    "iam.googleapis.com",
    "cloudtrace.googleapis.com",
    "logging.googleapis.com",
  ])

  service            = each.key
  disable_on_destroy = false
}
