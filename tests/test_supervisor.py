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


def test_substring_market_collision():
    session = StateSession()
    session.update_from_prompt("Check online booking status from France frame")
    # "online" should not set NL; "France" should set FR
    assert session.get("session.target_market") == "FR"


def test_intent_classification():
    supervisor = ECG_Supervisor_Agent()

    assert supervisor.classify_intent("Analyze July occupancy for Mediterranean South cluster") == "YIELD_ANALYTICS"
    assert supervisor.classify_intent("Release mobil-homes MH-102 to sale") == "PMS_OPERATIONS"
    assert supervisor.classify_intent("Draft a 15% discount promo for Dutch guests") == "MARKETING_CAMPAIGN"
    assert supervisor.classify_intent("") == "UNKNOWN"


def test_hitl_interception_approval_and_rejection_flow():
    supervisor = ECG_Supervisor_Agent()
    session = StateSession()

    # Setup session context
    session.set("session.campsite_id", "LA_SIRENE_06")
    session.set("session.unit_ids", ["MH-102", "MH-103"])

    # 1. Turn 1: Mutating request pauses execution and returns HITL Approval Card
    res1 = supervisor.process_turn("Release these held-back mobil-homes to sale", session)
    assert res1["status"] == "PENDING_CONFIRMATION"
    assert res1["intent"] == "PMS_OPERATIONS"
    assert res1["widget"]["widget_type"] == "HITL_APPROVAL_CARD"
    assert res1["widget"]["amber_border"] == "#f59e0b"
    assert session.pending_action is not None

    # 2. Turn 2: User rejects action -> execution cancelled without side-effects
    res_reject = supervisor.process_turn("Reject", session)
    assert res_reject["status"] == "CANCELLED"
    assert session.pending_action is None

    # 3. Turn 3: New mutating request pauses execution again
    res3 = supervisor.process_turn("Release these held-back mobil-homes to sale", session)
    assert res3["status"] == "PENDING_CONFIRMATION"

    # 4. Turn 4: User approves action -> execution succeeds with CONFIRMED card state
    res_approve = supervisor.process_turn("Approve", session)
    assert res_approve["status"] == "SUCCESS"
    assert res_approve["routed_agent"] == "PMS_OPERATIONS_AGENT"
    assert res_approve["widget"]["status"] == "CONFIRMED"
    assert res_approve["widget"]["amber_border"] == "#10b981"
    assert session.pending_action is None


def test_hitl_negative_phrasing_with_ok():
    supervisor = ECG_Supervisor_Agent()
    session = StateSession()
    session.set("session.campsite_id", "LA_SIRENE_06")
    session.set("session.unit_ids", ["MH-102"])

    # Start pending action
    supervisor.process_turn("Release these units to sale", session)
    assert session.pending_action is not None

    # Respond with negative phrasing containing "ok" ("Not ok, don't confirm")
    res = supervisor.process_turn("Not ok, don't confirm", session)
    assert res["status"] == "CANCELLED"
    assert session.pending_action is None


def test_multi_turn_session_context_retention():
    supervisor = ECG_Supervisor_Agent()
    session = StateSession()

    # Turn 1: Comparative yield query setting cluster, market, and unit_ids context
    res1 = supervisor.process_turn("Dutch booking lag in Mediterranean South vs last year", session)
    assert res1["status"] == "SUCCESS"
    assert res1["intent"] == "YIELD_ANALYTICS"
    assert session.get("session.target_cluster") == "MEDITERRANEAN_SOUTH"
    assert session.get("session.target_market") == "NL"
    assert session.get("session.unit_ids") == ["MH-102", "MH-103", "MH-104", "MH-105"]

    # Turn 2: Subsequent mutating request pauses for HITL confirmation with context inherited
    res2 = supervisor.process_turn("Release these held-back mobil-home units at La Sirène to sale", session)
    assert res2["status"] == "PENDING_CONFIRMATION"
    assert res2["intent"] == "PMS_OPERATIONS"
    assert session.get("session.target_cluster") == "MEDITERRANEAN_SOUTH"
    assert session.get("session.target_market") == "NL"
    assert session.get("session.campsite_id") == "LA_SIRENE_06"

    # Turn 3: Approval dispatches execution
    res3 = supervisor.process_turn("Approve", session)
    assert res3["status"] == "SUCCESS"
    assert res3["routed_agent"] == "PMS_OPERATIONS_AGENT"


def test_empty_or_whitespace_prompt_handling():
    supervisor = ECG_Supervisor_Agent()
    session = StateSession()

    res1 = supervisor.process_turn("", session)
    assert res1["status"] == "VALIDATION_ERROR"

    res2 = supervisor.process_turn("   \t\n", session)
    assert res2["status"] == "VALIDATION_ERROR"
    assert "cannot be empty" in res2["message"]
