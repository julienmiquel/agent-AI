# Secure Secret Manager Storage for Apigee Gateway Tokens and API Credentials

resource "google_secret_manager_secret" "apigee_pms_token" {
  secret_id = "apigee-pms-token"
  
  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    service     = "resalys-pms"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "apigee_pms_token_val" {
  secret = google_secret_manager_secret.apigee_pms_token.id
  secret_data = "mock_cloud_identity_token_julien" # Initial placeholder; overwrite in production CI/CD
}

resource "google_secret_manager_secret" "apigee_marketing_token" {
  secret_id = "apigee-marketing-token"
  
  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    service     = "crm-marketing"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "apigee_marketing_token_val" {
  secret = google_secret_manager_secret.apigee_marketing_token.id
  secret_data = "mock_crm_webhook_bearer_secret" # Initial placeholder; overwrite in production CI/CD
}

resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  
  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    service     = "gemini-enterprise"
  }

  depends_on = [google_project_service.required_apis]
}
