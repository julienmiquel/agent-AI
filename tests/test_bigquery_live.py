"""Integration test verifying BigQuery execution and fake data querying for Yield_Analytics_Agent."""

import sqlite3
from unittest.mock import MagicMock
import pytest
from src.agents import (
    Yield_Analytics_Agent,
    compare_company_yield_data,
    query_company_yield_data,
)


class SQLiteBigQueryAdapter:
    """In-memory SQLite adapter simulating BigQuery client query results for live testing."""

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.create_function(
            "SAFE_DIVIDE",
            2,
            lambda a, b: (float(a) / float(b)) if (a is not None and b is not None and float(b) != 0) else None,
        )
        self._seed_data()

    def _seed_data(self):
        cursor = self.conn.cursor()

        # Create occupancy_daily table
        cursor.execute("""
            CREATE TABLE occupancy_daily (
                cluster_id TEXT,
                campsite_id TEXT,
                date TEXT,
                occupied_units INTEGER,
                total_capacity INTEGER,
                total_revenue REAL,
                nights_sold INTEGER
            )
        """)

        # Insert Mediterranean South July 2026 data (78% occupancy, €112.50 AVPN, €87.75 RevPAR)
        for day in range(1, 32):
            cursor.execute("""
                INSERT INTO occupancy_daily VALUES (
                    'MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', ?, 390, 500, 43875.00, 390
                )
            """, (f"2026-07-{day:02d}",))

        # Insert Mediterranean South July 2025 data (88% occupancy, €111.93 AVPN, €98.50 RevPAR)
        for day in range(1, 32):
            cursor.execute("""
                INSERT INTO occupancy_daily VALUES (
                    'MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', ?, 440, 500, 49250.00, 440
                )
            """, (f"2025-07-{day:02d}",))

        # Create booking_segments table
        cursor.execute("""
            CREATE TABLE booking_segments (
                cluster_id TEXT,
                campsite_id TEXT,
                date TEXT,
                segment TEXT,
                target_units INTEGER,
                booked_units INTEGER,
                unit_id TEXT,
                status TEXT
            )
        """)

        # Segment lag data for NL (15% lag)
        for day in range(1, 32):
            cursor.execute("""
                INSERT INTO booking_segments VALUES (
                    'MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', ?, 'NL', 100, 85, NULL, 'ACTIVE'
                )
            """, (f"2026-07-{day:02d}",))

        # Held back units
        for unit_id in ["MH-102", "MH-103", "MH-104", "MH-105"]:
            cursor.execute("""
                INSERT INTO booking_segments VALUES (
                    'MEDITERRANEAN_SOUTH', 'LA_SIRENE_06', NULL, NULL, NULL, NULL, ?, 'HELD_BACK'
                )
            """, (unit_id,))

        self.conn.commit()

    def query(self, sql_query: str):
        # Convert BigQuery specific backtick tables and functions for SQLite compatibility
        sqlite_query = sql_query.replace("`customer-demo-01.company_analytics.occupancy_daily`", "occupancy_daily")
        sqlite_query = sqlite_query.replace("`customer-demo-01.company_analytics.booking_segments`", "booking_segments")
        sqlite_query = sqlite_query.replace("`company_analytics.occupancy_daily`", "occupancy_daily")
        sqlite_query = sqlite_query.replace("`company_analytics.booking_segments`", "booking_segments")
        sqlite_query = sqlite_query.replace("SAFE_DIVIDE(a, b)", "CAST(a AS REAL) / CAST(b AS REAL)")

        # Handle SAFE_DIVIDE regex replacement if present
        import re
        sqlite_query = re.sub(
            r"SAFE_DIVIDE\((SUM\([^)]+\)|[a-zA-W0-9_]+),\s*(SUM\([^)]+\)|[a-zA-W0-9_]+)\)",
            r"CAST(\1 AS REAL) / CAST(\2 AS REAL)",
            sqlite_query,
        )

        cursor = self.conn.cursor()
        cursor.execute(sqlite_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Convert rows into objects with attribute access like BigQuery Row objects
        result_rows = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            obj = type("BigQueryRow", (), row_dict)()
            result_rows.append(obj)

        job_mock = MagicMock()
        job_mock.result.return_value = result_rows
        return job_mock


def test_live_bigquery_adapter_occupancy_query():
    adapter = SQLiteBigQueryAdapter()

    res = query_company_yield_data(
        cluster_id="MEDITERRANEAN_SOUTH",
        start_date="2026-07-01",
        end_date="2026-07-31",
        target_market="NL",
        bq_client=adapter,
    )

    assert res["status"] == "SUCCESS"
    assert res["metrics"]["occupancy_rate"] == 0.78
    assert res["metrics"]["avpn_eur"] == 112.50
    assert res["metrics"]["revpar_eur"] == 87.75
    assert len(res["widget"]["lagging_callouts"]) > 0
    assert res["widget"]["lagging_callouts"][0]["segment"] == "NL"
    assert res["widget"]["lagging_callouts"][0]["lag_percentage"] == 0.15


def test_live_bigquery_adapter_comparative_query():
    adapter = SQLiteBigQueryAdapter()

    res = compare_company_yield_data(
        cluster_id="MEDITERRANEAN_SOUTH",
        current_start="2026-07-01",
        current_end="2026-07-31",
        prior_start="2025-07-01",
        prior_end="2025-07-31",
        target_market="NL",
        bq_client=adapter,
    )

    assert res["status"] == "SUCCESS"
    assert res["metrics"]["current_period"]["occupancy_rate"] == 0.78
    assert res["metrics"]["prior_period"]["occupancy_rate"] == 0.88
    assert res["metrics"]["variance"]["occupancy_rate_delta"] == -0.10
    assert res["metrics"]["variance"]["revpar_delta_eur"] == -10.75

    held_back = res["held_back_units"]
    assert held_back[0]["campsite_id"] == "LA_SIRENE_06"
    assert held_back[0]["unit_ids"] == ["MH-102", "MH-103", "MH-104", "MH-105"]
