# Firestore Database & Composite Indexes for Stateful Multi-Turn Session Retention

resource "google_firestore_database" "default" {
  provider    = google-beta
  project     = var.project_id
  name        = "(default)"
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"

  concurrency_mode            = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"

  depends_on = [google_project_service.required_apis]
}

# Composite index for filtering support tickets by campsite_id and status
resource "google_firestore_index" "support_tickets_status_campsite" {
  provider   = google-beta
  project    = var.project_id
  database   = google_firestore_database.default.name
  collection = "support_tickets"

  fields {
    field_path = "status"
    order      = "ASCENDING"
  }

  fields {
    field_path = "campsite_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "updated_at"
    order      = "DESCENDING"
  }
}

# Composite index for querying PMS inventory units by campsite and status
resource "google_firestore_index" "pms_inventory_campsite_status" {
  provider   = google-beta
  project    = var.project_id
  database   = google_firestore_database.default.name
  collection = "pms_inventory"

  fields {
    field_path = "campsite_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "status"
    order      = "ASCENDING"
  }
}
