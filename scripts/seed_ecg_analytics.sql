-- European Camping Group (ECG) BigQuery Seed Script
-- Dataset: ecg_analytics
-- Target Project: ecg-campsite-prod (or overridable via GCP_PROJECT_ID)

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

-- Clear existing sample data before seeding
TRUNCATE TABLE `ecg_analytics.occupancy_daily`;

-- Insert Daily Occupancy & Revenue Data for July & August 2025 and 2026
-- Mediterranean South Cluster (La Sirène) - July 2026 (Current Period: 78% Occupancy, RevPAR €87.75)
INSERT INTO `ecg_analytics.occupancy_daily` (cluster_id, campsite_id, date, occupied_units, total_capacity, total_revenue, nights_sold)
SELECT
  'MEDITERRANEAN_SOUTH' AS cluster_id,
  'LA_SIRENE_06' AS campsite_id,
  day_date AS date,
  390 AS occupied_units,
  500 AS total_capacity,
  NUMERIC '43875.00' AS total_revenue,
  390 AS nights_sold
FROM UNNEST(GENERATE_DATE_ARRAY('2026-07-01', '2026-07-31', INTERVAL 1 DAY)) AS day_date;

-- Mediterranean South Cluster - July 2025 (Prior Period: 88% Occupancy, RevPAR €98.50)
INSERT INTO `ecg_analytics.occupancy_daily` (cluster_id, campsite_id, date, occupied_units, total_capacity, total_revenue, nights_sold)
SELECT
  'MEDITERRANEAN_SOUTH' AS cluster_id,
  'LA_SIRENE_06' AS campsite_id,
  day_date AS date,
  440 AS occupied_units,
  500 AS total_capacity,
  NUMERIC '49250.00' AS total_revenue,
  440 AS nights_sold
FROM UNNEST(GENERATE_DATE_ARRAY('2025-07-01', '2025-07-31', INTERVAL 1 DAY)) AS day_date;

-- Atlantic North Cluster (Dolmen Cove) - July 2026 (Current Period: 82% Occupancy, RevPAR €102.50)
INSERT INTO `ecg_analytics.occupancy_daily` (cluster_id, campsite_id, date, occupied_units, total_capacity, total_revenue, nights_sold)
SELECT
  'ATLANTIC_NORTH' AS cluster_id,
  'DOLMEN_COVE_02' AS campsite_id,
  day_date AS date,
  246 AS occupied_units,
  300 AS total_capacity,
  NUMERIC '30750.00' AS total_revenue,
  246 AS nights_sold
FROM UNNEST(GENERATE_DATE_ARRAY('2026-07-01', '2026-07-31', INTERVAL 1 DAY)) AS day_date;

-- Atlantic North Cluster - July 2025 (Prior Period: 86% Occupancy, RevPAR €105.00)
INSERT INTO `ecg_analytics.occupancy_daily` (cluster_id, campsite_id, date, occupied_units, total_capacity, total_revenue, nights_sold)
SELECT
  'ATLANTIC_NORTH' AS cluster_id,
  'DOLMEN_COVE_02' AS campsite_id,
  day_date AS date,
  258 AS occupied_units,
  300 AS total_capacity,
  NUMERIC '31500.00' AS total_revenue,
  258 AS nights_sold
FROM UNNEST(GENERATE_DATE_ARRAY('2025-07-01', '2025-07-31', INTERVAL 1 DAY)) AS day_date;

-- August 2026 Data for Mediterranean South & Atlantic North
INSERT INTO `ecg_analytics.occupancy_daily` (cluster_id, campsite_id, date, occupied_units, total_capacity, total_revenue, nights_sold)
SELECT
  'MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', day_date, 410, 500, NUMERIC '47150.00', 410
FROM UNNEST(GENERATE_DATE_ARRAY('2026-08-01', '2026-08-31', INTERVAL 1 DAY)) AS day_date;

INSERT INTO `ecg_analytics.occupancy_daily` (cluster_id, campsite_id, date, occupied_units, total_capacity, total_revenue, nights_sold)
SELECT
  'ATLANTIC_NORTH', 'DOLMEN_COVE_02', day_date, 255, 300, NUMERIC '32385.00', 255
FROM UNNEST(GENERATE_DATE_ARRAY('2026-08-01', '2026-08-31', INTERVAL 1 DAY)) AS day_date;


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

TRUNCATE TABLE `ecg_analytics.booking_segments`;

-- Segment Performance Data (Dutch NL Market 15% lag in Med South)
INSERT INTO `ecg_analytics.booking_segments` (cluster_id, campsite_id, date, segment, target_units, booked_units, unit_id, status)
SELECT 'MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', day_date, 'NL', 100, 85, NULL, 'ACTIVE'
FROM UNNEST(GENERATE_DATE_ARRAY('2026-07-01', '2026-07-31', INTERVAL 1 DAY)) AS day_date;

INSERT INTO `ecg_analytics.booking_segments` (cluster_id, campsite_id, date, segment, target_units, booked_units, unit_id, status)
SELECT 'MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', day_date, 'FR', 200, 196, NULL, 'ACTIVE'
FROM UNNEST(GENERATE_DATE_ARRAY('2026-07-01', '2026-07-31', INTERVAL 1 DAY)) AS day_date;

INSERT INTO `ecg_analytics.booking_segments` (cluster_id, campsite_id, date, segment, target_units, booked_units, unit_id, status)
SELECT 'MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', day_date, 'DE', 150, 146, NULL, 'ACTIVE'
FROM UNNEST(GENERATE_DATE_ARRAY('2026-07-01', '2026-07-31', INTERVAL 1 DAY)) AS day_date;

INSERT INTO `ecg_analytics.booking_segments` (cluster_id, campsite_id, date, segment, target_units, booked_units, unit_id, status)
SELECT 'ATLANTIC_NORTH', 'DOLMEN_COVE_02', day_date, 'NL', 80, 78, NULL, 'ACTIVE'
FROM UNNEST(GENERATE_DATE_ARRAY('2026-07-01', '2026-07-31', INTERVAL 1 DAY)) AS day_date;

INSERT INTO `ecg_analytics.booking_segments` (cluster_id, campsite_id, date, segment, target_units, booked_units, unit_id, status)
SELECT 'ATLANTIC_NORTH', 'DOLMEN_COVE_02', day_date, 'FR', 120, 110, NULL, 'ACTIVE'
FROM UNNEST(GENERATE_DATE_ARRAY('2026-07-01', '2026-07-31', INTERVAL 1 DAY)) AS day_date;

-- Held-Back Units for PMS & Yield Analytics bottleneck identification
INSERT INTO `ecg_analytics.booking_segments` (cluster_id, campsite_id, date, segment, target_units, booked_units, unit_id, status) VALUES
  ('MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', NULL, NULL, NULL, NULL, 'MH-102', 'HELD_BACK'),
  ('MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', NULL, NULL, NULL, NULL, 'MH-103', 'HELD_BACK'),
  ('MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', NULL, NULL, NULL, NULL, 'MH-104', 'HELD_BACK'),
  ('MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', NULL, NULL, NULL, NULL, 'MH-105', 'HELD_BACK'),
  ('ATLANTIC_NORTH', 'DOLMEN_COVE_02', NULL, NULL, NULL, NULL, 'MH-201', 'HELD_BACK'),
  ('ATLANTIC_NORTH', 'DOLMEN_COVE_02', NULL, NULL, NULL, NULL, 'MH-202', 'HELD_BACK');
