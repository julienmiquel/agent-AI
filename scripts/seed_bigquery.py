#!/usr/bin/env python3
"""BigQuery Seeder Script for European Camping Company (Company) Yield Analytics.

Loads DDL and DML data into BigQuery dataset `company_analytics` (`occupancy_daily` and `booking_segments`).
Supports dry-run verification mode and active Google Cloud BigQuery execution.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.config import BIGQUERY_DATASET, GCP_PROJECT_ID
except ImportError:
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "customer-demo-01")
    BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "company_analytics")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_seeder(project_id: str, dataset_id: str, dry_run: bool = False) -> bool:
    """Executes or prints BigQuery seeding DDL and DML scripts."""
    sql_file = PROJECT_ROOT / "scripts" / "seed_company_analytics.sql"
    if not sql_file.exists():
        logger.error("SQL file not found at '%s'", sql_file)
        return False

    sql_content = sql_file.read_text(encoding="utf-8")

    # Replace default dataset/project placeholders if customized
    sql_content = sql_content.replace("`company_analytics`", f"`{dataset_id}`")
    sql_content = sql_content.replace("`company_analytics.", f"`{project_id}.{dataset_id}.")

    if dry_run:
        logger.info("=== DRY-RUN MODE: Prepared SQL for Project '%s', Dataset '%s' ===", project_id, dataset_id)
        print(f"\n--- SQL Script Preview ({len(sql_content.splitlines())} lines) ---")
        print(sql_content[:800] + "\n... [truncated] ...\n")
        logger.info("Dry-run verification completed successfully.")
        return True

    # Check for google-cloud-bigquery client
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=project_id)
        logger.info("Connected to BigQuery client for project '%s'. Executing queries...", project_id)

        # Split statements by semicolon and execute non-empty statements
        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
        for idx, statement in enumerate(statements, 1):
            logger.info("Executing statement %d/%d...", idx, len(statements))
            query_job = client.query(statement)
            query_job.result()  # Wait for completion

        logger.info("Successfully seeded BigQuery dataset '%s.%s'!", project_id, dataset_id)
        return True

    except Exception as exc:
        logger.warning("Could not execute via google-cloud-bigquery client (%s).", exc)
        logger.info("Attempting execution via command-line 'bq query'...")

        import subprocess
        try:
            cmd = ["bq", "query", "--use_legacy_sql=false", f"--project_id={project_id}", sql_content]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                logger.info("Successfully executed SQL via 'bq query' CLI!")
                return True
            else:
                logger.error("bq query failed with error: %s", res.stderr)
                return False
        except Exception as bq_err:
            logger.error("Failed to run 'bq query' CLI: %s", bq_err)
            return False


def main():
    parser = argparse.ArgumentParser(description="Seed BigQuery tables for Company Yield Analytics.")
    parser.add_argument("--project", default=GCP_PROJECT_ID, help="GCP Project ID")
    parser.add_argument("--dataset", default=BIGQUERY_DATASET, help="BigQuery Dataset ID")
    parser.add_argument("--dry-run", action="store_true", help="Print prepared SQL without executing")

    args = parser.parse_args()
    success = run_seeder(project_id=args.project, dataset_id=args.dataset, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
