# Least-Privilege IAM Roles and Service Accounts for Vertex AI Agent Engine and MCP Cloud Run

resource "google_service_account" "agent_runner" {
  account_id   = "agent-ecg-runner"
  display_name = "ECG Multi-Agent System Runner SA"
  description  = "Service account used by Vertex AI Reasoning Engine for executing supervisor and domain agents."
}

resource "google_service_account" "mcp_server" {
  account_id   = "agent-ecg-mcp"
  display_name = "ECG Interactive MCP UI Server SA"
  description  = "Service account for hosting the interactive MCP UI Web widget on Cloud Run."
}

# Bind required least-privilege roles to the agent runner service account
resource "google_project_iam_member" "agent_runner_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_runner.email}"
}

resource "google_project_iam_member" "agent_runner_bigquery" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.agent_runner.email}"
}

resource "google_project_iam_member" "agent_runner_bigquery_job" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.agent_runner.email}"
}

resource "google_project_iam_member" "agent_runner_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.agent_runner.email}"
}

resource "google_secret_manager_secret_iam_member" "agent_runner_pms_secret" {
  secret_id = google_secret_manager_secret.apigee_pms_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_runner.email}"
}

resource "google_secret_manager_secret_iam_member" "agent_runner_mkt_secret" {
  secret_id = google_secret_manager_secret.apigee_marketing_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_runner.email}"
}
