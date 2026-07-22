# BigQuery Fake Data Loader & Schema Implementation Plan

## Goal Description
Create complete, realistic fake data and loading mechanisms for BigQuery tables required by `src/agents/yield_analytics.py`. This enables `Yield_Analytics_Agent` to run actual SQL queries against BigQuery (`occupancy_daily` and `booking_segments` tables in dataset `ecg_analytics`), executing single-period yield analytics and period-over-period comparative analysis without falling back to mock values.

---

## User Review Required
> [!IMPORTANT]
> **Dataset and Table Target Settings**
> - Default Project ID: `ecg-campsite-prod` (overridable via `GCP_PROJECT_ID` environment variable).
> - Default Dataset ID: `ecg_analytics` (overridable via `BIGQUERY_DATASET` environment variable).
> - Tables Created: `occupancy_daily` and `booking_segments`.

> [!NOTE]
> **Data Scope Covered in Fake Datasets**
> - **Date Windows**:
>   - Current Period: July & August 2026 (`2026-07-01` to `2026-08-31`)
>   - Prior Period: July & August 2025 (`2025-07-01` to `2025-08-31`)
> - **Clusters & Campsites**:
>   - `MEDITERRANEAN_SOUTH`: Campsite `LA_SIRENE_06`
>   - `ATLANTIC_NORTH`: Campsite `DOLMEN_COVE_02`
> - **Segments / Markets**: `NL` (Dutch), `FR` (French), `DE` (German), `UK` (British).
> - **Held-back Units**:
>   - `LA_SIRENE_06` (`MEDITERRANEAN_SOUTH`): Units `MH-102`, `MH-103`, `MH-104`, `MH-105` with status `HELD_BACK`.
>   - `DOLMEN_COVE_02` (`ATLANTIC_NORTH`): Units `MH-201`, `MH-202` with status `HELD_BACK`.

---

## Open Questions
> [!QUESTION]
> 1. Do you have active Google Cloud credentials (`gcloud auth application-default login` or service account key) configured for loading directly into GCP BigQuery, or would you prefer a dry-run local test / SQL script execution first?
> 2. Should we add `google-cloud-bigquery` to `pyproject.toml` dependencies for standard python client interaction?

---

## Proposed Changes

### 1. SQL Seed Script
#### [NEW] `scripts/seed_ecg_analytics.sql`
- Standard SQL script executable via BigQuery Console or `bq query`.
- Creates dataset `ecg_analytics` if missing.
- Defines tables `occupancy_daily` and `booking_segments` with explicit column types.
- Populates daily occupancy data and segment booking target/actual levels and held-back unit records.

```sql
-- Create Dataset if not existing
CREATE SCHEMA IF NOT EXISTS `ecg_analytics`;

-- 1. Table: occupancy_daily
CREATE TABLE IF NOT EXISTS `ecg_analytics.occupancy_daily` (
  cluster_id STRING NOT NULL,
  campsite_id STRING,
  date DATE NOT NULL,
  occupied_units INT64 NOT NULL,
  total_capacity INT64 NOT NULL,
  total_revenue NUMERIC NOT NULL,
  nights_sold INT64 NOT NULL
);

-- 2. Table: booking_segments
CREATE TABLE IF NOT EXISTS `ecg_analytics.booking_segments` (
  cluster_id STRING NOT NULL,
  campsite_id STRING,
  date DATE,
  segment STRING,
  target_units INT64,
  booked_units INT64,
  unit_id STRING,
  status STRING
);
```

---

### 2. CSV Seed Files
#### [NEW] `data/occupancy_daily.csv`
- CSV format file for `occupancy_daily` containing daily data for 2025 and 2026.

#### [NEW] `data/booking_segments.csv`
- CSV format file for `booking_segments` containing market segment targets & booked units, as well as held-back unit records.

---

### 3. Python Data Seeder & BigQuery Helper Script
#### [NEW] `scripts/seed_bigquery.py`
- Python script that loads CSV/SQL data into BigQuery using `google.cloud.bigquery.Client` or `bq` CLI.
- Handles project/dataset overrides and checks table existence before populating.

#### [MODIFY] `pyproject.toml`
- Add `google-cloud-bigquery>=3.0.0` to `dependencies` list.

---

### 4. Integration Test Script
#### [NEW] `tests/test_bigquery_live.py`
- Tests `query_ecg_yield_data` and `compare_ecg_yield_data` with a `google.cloud.bigquery.Client` instance against the populated BigQuery dataset or mock BigQuery execution.

---

## Verification Plan

### Automated Tests
1. Run existing test suite to ensure no regressions:
   ```bash
   .venv/bin/pytest tests/test_yield_analytics.py
   ```
2. Run new BigQuery live integration test:
   ```bash
   .venv/bin/pytest tests/test_bigquery_live.py
   ```

### Manual Verification
1. Execute python seed script:
   ```bash
   .venv/bin/python scripts/seed_bigquery.py --dry-run
   ```
2. Inspect generated SQL script and seed files in `scripts/seed_ecg_analytics.sql` and `data/`.
3. (If GCP auth present) Verify tables in BigQuery:
   ```bash
   bq ls ecg_analytics
   ```
