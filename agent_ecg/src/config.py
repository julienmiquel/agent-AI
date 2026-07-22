"""Centralized Configuration for ECG Multi-Agent System.

Defines model tiers, dataset names, API endpoints, and system defaults.
"""

import logging
import os

logger = logging.getLogger(__name__)

# Model Tiers
MODEL_SUPERVISOR = os.getenv("MODEL_SUPERVISOR", "gemini-2.5-pro")
MODEL_YIELD = os.getenv("MODEL_YIELD", "gemini-2.5-pro")
MODEL_PMS = os.getenv("MODEL_PMS", "gemini-3.6-flash")
MODEL_MARKETING = os.getenv("MODEL_MARKETING", "gemini-2.5-pro")

# GCP & BigQuery Settings
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "customer-demo-01")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "ecg_analytics")

# API Endpoints (Apigee REST Gateway)
APIGEE_PMS_ENDPOINT = os.getenv("APIGEE_PMS_ENDPOINT", "https://api.ecg.camp/pms/v1")
APIGEE_MARKETING_ENDPOINT = os.getenv("APIGEE_MARKETING_ENDPOINT", "https://api.ecg.camp/marketing/v1")

# GCS Asset Storage
GCS_MARKETING_BUCKET = os.getenv("GCS_MARKETING_BUCKET", "gs://ecg-marketing-assets/genai/")

# System Operational Defaults
DEFAULT_CYCLE_TIME_SLA_SECONDS = 300  # < 5 minutes
TEXT_TO_SQL_ACCURACY_THRESHOLD = 0.95

logger.debug("Configuration loaded: Project='%s', Dataset='%s', Models=[Supervisor: %s, Yield: %s, PMS: %s, Mkt: %s]",
             GCP_PROJECT_ID, BIGQUERY_DATASET, MODEL_SUPERVISOR, MODEL_YIELD, MODEL_PMS, MODEL_MARKETING)
