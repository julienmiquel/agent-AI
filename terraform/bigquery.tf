# BigQuery Dataset & Schema Declarations for ECG Yield Analytics

resource "google_bigquery_dataset" "ecg_analytics" {
  dataset_id                  = var.bigquery_dataset_id
  friendly_name               = "ECG Yield Analytics & Booking Segments"
  description                 = "Data warehouse tables for European Camping Group campsite occupancy and pacing analysis."
  location                    = "US"
  default_table_expiration_ms = null

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    domain      = "yield-analytics"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_bigquery_table" "occupancy_daily" {
  dataset_id          = google_bigquery_dataset.ecg_analytics.dataset_id
  table_id            = "occupancy_daily"
  description         = "Daily accommodation capacity, occupied units, and revenue metrics by campsite cluster."
  deletion_protection = false

  schema = <<EOF
[
  {"name": "date", "type": "DATE", "mode": "REQUIRED", "description": "Calendar date of occupancy."},
  {"name": "cluster_id", "type": "STRING", "mode": "REQUIRED", "description": "Campsite cluster name (e.g. MEDITERRANEAN_SOUTH)."},
  {"name": "campsite_id", "type": "STRING", "mode": "REQUIRED", "description": "Specific campsite ID."},
  {"name": "accommodation_type", "type": "STRING", "mode": "REQUIRED", "description": "Mobil-home category."},
  {"name": "total_capacity", "type": "INTEGER", "mode": "REQUIRED", "description": "Total units available in inventory."},
  {"name": "occupied_units", "type": "INTEGER", "mode": "REQUIRED", "description": "Units booked for the night."},
  {"name": "nights_sold", "type": "INTEGER", "mode": "REQUIRED", "description": "Total room nights sold."},
  {"name": "total_revenue", "type": "NUMERIC", "mode": "REQUIRED", "description": "Total gross revenue generated in Euros."}
]
EOF
}

resource "google_bigquery_table" "booking_segments" {
  dataset_id          = google_bigquery_dataset.ecg_analytics.dataset_id
  table_id            = "booking_segments"
  description         = "Booking pacing and inventory status by customer nationality and segment."
  deletion_protection = false

  schema = <<EOF
[
  {"name": "date", "type": "DATE", "mode": "REQUIRED", "description": "Observation date."},
  {"name": "cluster_id", "type": "STRING", "mode": "REQUIRED", "description": "Campsite cluster name."},
  {"name": "campsite_id", "type": "STRING", "mode": "REQUIRED", "description": "Specific campsite ID."},
  {"name": "segment", "type": "STRING", "mode": "REQUIRED", "description": "Customer market code (NL, FR, DE, UK)."},
  {"name": "unit_id", "type": "STRING", "mode": "NULLABLE", "description": "Specific mobil-home identifier."},
  {"name": "status", "type": "STRING", "mode": "REQUIRED", "description": "Operational inventory status (AVAILABLE_FOR_SALE, HELD_BACK, BLOCKED)."},
  {"name": "target_units", "type": "INTEGER", "mode": "REQUIRED", "description": "Target sales quota for segment."},
  {"name": "booked_units", "type": "INTEGER", "mode": "REQUIRED", "description": "Actual units booked."}
]
EOF
}
