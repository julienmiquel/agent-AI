"""Unit tests for ECG_Supervisor_Agent and StateSession."""

import pytest
from src.agents.supervisor import ECG_Supervisor_Agent, StateSession


def test_session_state_initialization():
    session = StateSession(session_id="test_123", user_id="user_julien")
    assert session.session_id == "test_123"
    assert session.user_id == "user_julien"
    assert session.get("session.target_cluster") is None
    assert session.get("session.campsite_id") is None


def test_session_state_updates():
    session = StateSession()
    session.set("session.target_cluster", "MEDITERRANEAN_SOUTH")
    assert session.get("session.target_cluster") == "MEDITERRANEAN_SOUTH"


def test_intent_classification():
    supervisor = ECG_Supervisor_Agent()

    assert supervisor.classify_intent("Analyze July occupancy for Mediterranean South cluster") == "YIELD_ANALYTICS"
    assert supervisor.classify_intent("Release mobil-homes MH-102 to sale") == "PMS_OPERATIONS"
    assert supervisor.classify_intent("Draft a 15% discount promo for Dutch guests") == "MARKETING_CAMPAIGN"
    assert supervisor.classify_intent("") == "UNKNOWN"


def test_multi_turn_session_context_retention():
    supervisor = ECG_Supervisor_Agent()
    session = StateSession()

    # Turn 1: Yield query setting cluster and market context
    res1 = supervisor.process_turn("Analyze July occupancy for Mediterranean South cluster for Dutch market", session)
    assert res1["status"] == "SUCCESS"
    assert res1["intent"] == "YIELD_ANALYTICS"
    assert session.get("session.target_cluster") == "MEDITERRANEAN_SOUTH"
    assert session.get("session.target_market") == "NL"

    # Turn 2: Subsequent request without repeating cluster/market
    res2 = supervisor.process_turn("Release mobil-homes at La Sirène to sale", session)
    assert res2["status"] == "SUCCESS"
    assert res2["intent"] == "PMS_OPERATIONS"
    # Verify previous context inherited
    assert session.get("session.target_cluster") == "MEDITERRANEAN_SOUTH"
    assert session.get("session.target_market") == "NL"
    assert session.get("session.campsite_id") == "LA_SIRENE_06"


def test_empty_prompt_handling():
    supervisor = ECG_Supervisor_Agent()
    session = StateSession()

    res = supervisor.process_turn("", session)
    assert res["status"] == "VALIDATION_ERROR"
    assert "cannot be empty" in res["message"]
