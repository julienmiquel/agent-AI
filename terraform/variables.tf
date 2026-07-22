# Declarative Variables for ECG Multi-Agent System Infrastructure

variable "project_id" {
  description = "Google Cloud Project ID for ECG GenAI platform deployment."
  type        = string
  default     = "customer-demo-01"
}

variable "region" {
  description = "Default Google Cloud region for compute, Vertex AI, and Cloud Run."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment lifecycle (e.g. dev, staging, prod)."
  type        = string
  default     = "prod"
}

variable "bigquery_dataset_id" {
  description = "BigQuery dataset ID for ECG yield analytics and booking segment data."
  type        = string
  default     = "ecg_analytics"
}

variable "firestore_location" {
  description = "Google Cloud region for Firestore native database instance."
  type        = string
  default     = "nam5" # US multi-region
}

variable "apigee_pms_endpoint" {
  description = "REST OpenAPI endpoint URI for Apigee Resalys PMS gateway."
  type        = string
  default     = "https://api.ecg.camp/pms/v1"
}

variable "apigee_marketing_endpoint" {
  description = "REST OpenAPI endpoint URI for Apigee CRM marketing gateway."
  type        = string
  default     = "https://api.ecg.camp/marketing/v1"
}

variable "gcs_marketing_bucket" {
  description = "Google Cloud Storage bucket name for Imagen campaign banner graphics."
  type        = string
  default     = "ecg-marketing-assets"
}
