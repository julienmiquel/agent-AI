# Infrastructure Outputs for ECG Multi-Agent System

output "project_id" {
  description = "Deployed Google Cloud Project ID."
  value       = var.project_id
}

output "bigquery_dataset_uri" {
  description = "Fully-qualified BigQuery dataset reference for data agent connection."
  value       = "projects/${var.project_id}/datasets/${google_bigquery_dataset.ecg_analytics.dataset_id}"
}

output "firestore_database_id" {
  description = "Firestore database ID for stateful session persistence."
  value       = google_firestore_database.default.name
}

output "agent_runner_sa_email" {
  description = "Service Account email used by Vertex AI Agent Engine and Cloud Run."
  value       = google_service_account.agent_runner.email
}

output "secret_manager_pms_token_id" {
  description = "Secret Manager resource ID for Apigee PMS OAuth bearer token."
  value       = google_secret_manager_secret.apigee_pms_token.secret_id
}
