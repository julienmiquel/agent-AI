"""Unit tests for Yield_Analytics_Agent, query_ecg_yield_data tool, and supervisor routing integration."""

from unittest.mock import MagicMock
import pytest
from src.agents import ECG_Supervisor_Agent, StateSession, Yield_Analytics_Agent, query_ecg_yield_data
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
