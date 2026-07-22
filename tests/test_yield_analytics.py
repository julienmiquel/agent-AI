"""Unit tests for Yield_Analytics_Agent, query_ecg_yield_data tool, and supervisor routing integration."""

from unittest.mock import MagicMock
import pytest
from src.agents import (
    ECG_Supervisor_Agent,
    StateSession,
    Yield_Analytics_Agent,
    compare_ecg_yield_data,
    query_ecg_yield_data,
)
from src.config import MODEL_YIELD


def test_yield_analytics_agent_initialization():
    agent = Yield_Analytics_Agent()
    assert agent.name == "Yield_Analytics_Agent"
    assert agent.model_name == MODEL_YIELD


def test_parse_prompt_campsite_clusters_and_dates():
    agent = Yield_Analytics_Agent()

    # Prompt with Mediterranean South and July
    parsed1 = agent.parse_prompt("Analyze July occupancy and RevPAR for Mediterranean South campsite cluster")
    assert parsed1["cluster_id"] == "MEDITERRANEAN_SOUTH"
    assert parsed1["start_date"] == "2026-07-01"
    assert parsed1["end_date"] == "2026-07-31"

    # Prompt with Atlantic North and August
    parsed2 = agent.parse_prompt("Analyze August yield metrics for Atlantic North cluster")
    assert parsed2["cluster_id"] == "ATLANTIC_NORTH"
    assert parsed2["start_date"] == "2026-08-01"
    assert parsed2["end_date"] == "2026-08-31"

    # Prompt with explicit ISO date range
    parsed3 = agent.parse_prompt("Query metrics from 2026-07-05 to 2026-07-20 for Mediterranean South cluster")
    assert parsed3["start_date"] == "2026-07-05"
    assert parsed3["end_date"] == "2026-07-20"


def test_parse_prompt_fallback_to_session():
    agent = Yield_Analytics_Agent()
    session = StateSession()
    session.set("session.target_cluster", "ATLANTIC_NORTH")
    session.set("session.target_market", "NL")

    parsed = agent.parse_prompt("Identify lagging market segments for July", session=session)
    assert parsed["cluster_id"] == "ATLANTIC_NORTH"
    assert parsed["target_market"] == "NL"


def test_query_ecg_yield_data_success():
    res = query_ecg_yield_data(
        cluster_id="MEDITERRANEAN_SOUTH",
        start_date="2026-07-01",
        end_date="2026-07-31",
        target_market="NL",
    )

    assert res["status"] == "SUCCESS"
    assert len(res["sql_queries"]) == 2
    assert "ecg_analytics.occupancy_daily" in res["sql_queries"][0]
    assert "ecg_analytics.booking_segments" in res["sql_queries"][1]

    # Verify widget structure
    widget = res["widget"]
    assert widget["widget_type"] == "YIELD_ANALYTICS"
    assert "occupancy_rate" in widget["metrics"]
    assert "avpn_eur" in widget["metrics"]
    assert "revpar_eur" in widget["metrics"]
    assert isinstance(widget["lagging_callouts"], list)
    assert len(widget["lagging_callouts"]) > 0
    assert widget["lagging_callouts"][0]["segment"] == "NL"


def test_query_ecg_yield_data_invalid_parameters():
    # Empty cluster_id
    res1 = query_ecg_yield_data(cluster_id="")
    assert res1["status"] == "VALIDATION_ERROR"
    assert "Cluster ID cannot be empty" in res1["error"]

    # Negative date window (start_date > end_date)
    res2 = query_ecg_yield_data(
        cluster_id="MEDITERRANEAN_SOUTH",
        start_date="2026-07-31",
        end_date="2026-07-01",
    )
    assert res2["status"] == "VALIDATION_ERROR"
    assert "Invalid date window" in res2["error"]


def test_query_ecg_yield_data_with_mock_bq_client():
    mock_bq = MagicMock()

    # Mock row objects returned by BigQuery
    row_occ = MagicMock()
    row_occ.occupancy_rate = 0.85
    row_occ.avpn_eur = 130.00
    row_occ.revpar_eur = 110.50

    job_occ = MagicMock()
    job_occ.result.return_value = [row_occ]

    row_seg = MagicMock()
    row_seg.segment = "NL"
    row_seg.lag_percentage = 0.18

    job_seg = MagicMock()
    job_seg.result.return_value = [row_seg]

    mock_bq.query.side_effect = [job_occ, job_seg]

    res = query_ecg_yield_data(
        cluster_id="MEDITERRANEAN_SOUTH",
        start_date="2026-07-01",
        end_date="2026-07-31",
        bq_client=mock_bq,
    )

    assert res["status"] == "SUCCESS"
    assert res["metrics"]["occupancy_rate"] == 0.85
    assert res["metrics"]["avpn_eur"] == 130.00
    assert res["metrics"]["revpar_eur"] == 110.50
    assert res["widget"]["lagging_callouts"][0]["segment"] == "NL"
    assert res["widget"]["lagging_callouts"][0]["lag_percentage"] == 0.18
    assert mock_bq.query.call_count == 2


def test_query_ecg_yield_data_bq_client_error():
    mock_bq = MagicMock()
    mock_bq.query.side_effect = Exception("BigQuery Connection Error")

    res = query_ecg_yield_data(
        cluster_id="MEDITERRANEAN_SOUTH",
        bq_client=mock_bq,
    )

    assert res["status"] == "ERROR"
    assert "BigQuery query execution failed" in res["error"]


def test_yield_analytics_agent_process_query():
    agent = Yield_Analytics_Agent()
    session = StateSession()

    res = agent.process_query(
        prompt="Analyze July occupancy and RevPAR for Mediterranean South campsite cluster",
        session=session,
    )

    assert res["status"] == "SUCCESS"
    assert res["agent"] == "Yield_Analytics_Agent"
    assert res["widget"]["widget_type"] == "YIELD_ANALYTICS"
    assert "Yield analytics calculated for cluster MEDITERRANEAN_SOUTH" in res["message"]


def test_supervisor_yield_analytics_routing():
    supervisor = ECG_Supervisor_Agent()
    session = StateSession()

    res = supervisor.process_turn(
        prompt="Analyze July occupancy and RevPAR for Mediterranean South campsite cluster",
        session=session,
    )

    assert res["status"] == "SUCCESS"
    assert res["intent"] == "YIELD_ANALYTICS"
    assert res["routed_agent"] == "YIELD_ANALYTICS_AGENT"
    assert "agent_output" in res
    assert res["agent_output"]["widget"]["widget_type"] == "YIELD_ANALYTICS"
    assert res["agent_output"]["metrics"]["occupancy_rate"] == 0.78


def test_compare_ecg_yield_data_success_and_yoy_variance():
    res = compare_ecg_yield_data(
        cluster_id="MEDITERRANEAN_SOUTH",
        current_start="2026-07-01",
        current_end="2026-07-31",
        prior_start="2025-07-01",
        prior_end="2025-07-31",
        target_market="NL",
    )

    assert res["status"] == "SUCCESS"
    assert len(res["sql_queries"]) == 4
    assert "ecg_analytics.occupancy_daily" in res["sql_queries"][0]
    assert "ecg_analytics.occupancy_daily" in res["sql_queries"][1]
    assert "ecg_analytics.booking_segments" in res["sql_queries"][2]
    assert "ecg_analytics.booking_segments" in res["sql_queries"][3]

    # Verify metrics & YoY variance
    metrics = res["metrics"]
    assert metrics["current_period"]["occupancy_rate"] == 0.78
    assert metrics["prior_period"]["occupancy_rate"] == 0.88
    assert metrics["variance"]["occupancy_rate_delta"] == -0.10
    assert metrics["variance"]["revpar_delta_eur"] == -10.75

    # Verify held-back unit extraction
    held_back = res["held_back_units"]
    assert len(held_back) == 1
    assert held_back[0]["campsite_id"] == "LA_SIRENE_06"
    assert held_back[0]["campsite_name"] == "La Sirène"
    assert held_back[0]["unit_ids"] == ["MH-102", "MH-103", "MH-104", "MH-105"]
    assert held_back[0]["count"] == 4

    # Verify widget structure
    widget = res["widget"]
    assert widget["widget_type"] == "YIELD_COMPARATIVE_ANALYTICS"
    assert widget["cluster_id"] == "MEDITERRANEAN_SOUTH"
    assert widget["variance"]["occupancy_rate_delta"] == -0.10


def test_compare_ecg_yield_data_validation_errors():
    # Empty cluster_id
    res1 = compare_ecg_yield_data(cluster_id="")
    assert res1["status"] == "VALIDATION_ERROR"
    assert "Cluster ID cannot be empty" in res1["error"]

    # Invalid current date window
    res2 = compare_ecg_yield_data(
        cluster_id="MEDITERRANEAN_SOUTH",
        current_start="2026-07-31",
        current_end="2026-07-01",
    )
    assert res2["status"] == "VALIDATION_ERROR"
    assert "Invalid current date window" in res2["error"]

    # Invalid prior date window
    res3 = compare_ecg_yield_data(
        cluster_id="MEDITERRANEAN_SOUTH",
        prior_start="2025-07-31",
        prior_end="2025-07-01",
    )
    assert res3["status"] == "VALIDATION_ERROR"
    assert "Invalid prior date window" in res3["error"]


def test_compare_ecg_yield_data_with_mock_bq_client():
    mock_bq = MagicMock()

    # Current period row
    row_curr = MagicMock()
    row_curr.occupancy_rate = 0.80
    row_curr.revpar_eur = 90.00
    job_curr = MagicMock()
    job_curr.result.return_value = [row_curr]

    # Prior period row
    row_prior = MagicMock()
    row_prior.occupancy_rate = 0.90
    row_prior.revpar_eur = 100.00
    job_prior = MagicMock()
    job_prior.result.return_value = [row_prior]

    # Segment row
    row_seg = MagicMock()
    row_seg.segment = "NL"
    row_seg.lag_percentage = 0.15
    job_seg = MagicMock()
    job_seg.result.return_value = [row_seg]

    mock_bq.query.side_effect = [job_curr, job_prior, job_seg]

    res = compare_ecg_yield_data(
        cluster_id="MEDITERRANEAN_SOUTH",
        bq_client=mock_bq,
    )

    assert res["status"] == "SUCCESS"
    assert res["metrics"]["variance"]["occupancy_rate_delta"] == -0.10
    assert res["metrics"]["variance"]["revpar_delta_eur"] == -10.00


def test_compare_ecg_yield_data_missing_prior_data_fallback():
    mock_bq = MagicMock()

    row_curr = MagicMock()
    row_curr.occupancy_rate = 0.78
    row_curr.revpar_eur = 87.75
    job_curr = MagicMock()
    job_curr.result.return_value = [row_curr]

    # Empty prior period result (missing historical data)
    job_prior = MagicMock()
    job_prior.result.return_value = []

    job_seg = MagicMock()
    job_seg.result.return_value = []

    mock_bq.query.side_effect = [job_curr, job_prior, job_seg]

    res = compare_ecg_yield_data(
        cluster_id="MEDITERRANEAN_SOUTH",
        bq_client=mock_bq,
    )

    assert res["status"] == "SUCCESS"
    # Zero variance fallback when prior data missing
    assert res["metrics"]["variance"]["occupancy_rate_delta"] == 0.0
    assert res["metrics"]["variance"]["revpar_delta_eur"] == 0.0


def test_comparative_prompt_parsing():
    agent = Yield_Analytics_Agent()

    # Prompt with comparative keywords
    parsed = agent.parse_prompt("Dutch booking lag in Mediterranean South vs last year")
    assert parsed["cluster_id"] == "MEDITERRANEAN_SOUTH"
    assert parsed["target_market"] == "NL"
    assert parsed["is_comparative"] is True
    assert parsed["current_start"] == "2026-07-01"
    assert parsed["prior_start"] == "2025-07-01"

    # Multi-cluster comparative prompt
    parsed2 = agent.parse_prompt("Compare July occupancy Mediterranean South vs Atlantic North")
    assert parsed2["is_comparative"] is True
    assert parsed2["cluster_id"] == "MEDITERRANEAN_SOUTH"


def test_comparative_process_query_and_session_retention():
    supervisor = ECG_Supervisor_Agent()
    session = StateSession()

    # Turn 1: Comparative prompt
    prompt1 = "Dutch booking lag in Mediterranean South vs last year"
    res1 = supervisor.process_turn(prompt1, session)

    assert res1["status"] == "SUCCESS"
    assert res1["intent"] == "YIELD_ANALYTICS"
    assert res1["routed_agent"] == "YIELD_ANALYTICS_AGENT"
    assert res1["agent_output"]["widget"]["widget_type"] == "YIELD_COMPARATIVE_ANALYTICS"

    # Verify held-back unit IDs and campsite ID persisted in StateSession
    assert session.get("session.unit_ids") == ["MH-102", "MH-103", "MH-104", "MH-105"]
    assert session.unit_ids == ["MH-102", "MH-103", "MH-104", "MH-105"]
    assert session.get("session.campsite_id") == "LA_SIRENE_06"
    assert session.campsite_id == "LA_SIRENE_06"

    # Turn 2: Downstream PMS turn pauses for HITL confirmation
    prompt2 = "Release these held-back mobil-home units to sale"
    res2 = supervisor.process_turn(prompt2, session)

    assert res2["status"] == "PENDING_CONFIRMATION"
    assert res2["intent"] == "PMS_OPERATIONS"
    assert res2["session_state"]["session.unit_ids"] == ["MH-102", "MH-103", "MH-104", "MH-105"]
    assert res2["session_state"]["session.campsite_id"] == "LA_SIRENE_06"

    # Turn 3: User approves action -> execution completes successfully
    res3 = supervisor.process_turn("Approve", session)
    assert res3["status"] == "SUCCESS"
    assert res3["routed_agent"] == "PMS_OPERATIONS_AGENT"

