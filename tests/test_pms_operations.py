"""Unit tests for PMS_Operations_Agent and resalys_update_unit_inventory tool."""

import pytest
from src.agents import (
    Company_Supervisor_Agent,
    PMS_Operations_Agent,
    StateSession,
    resalys_update_unit_inventory,
)


def test_pms_operations_agent_initialization():
    agent = PMS_Operations_Agent()
    assert agent.name == "PMS_Operations_Agent"


def test_resalys_update_unit_inventory_success():
    res = resalys_update_unit_inventory(
        campsite_id="LA_SIRENE_06",
        unit_ids=["MH-102", "MH-103", "MH-104", "MH-105"],
        new_status="AVAILABLE_FOR_SALE",
    )

    assert res["status"] == "SUCCESS"
    assert res["campsite_id"] == "LA_SIRENE_06"
    assert res["unit_ids"] == ["MH-102", "MH-103", "MH-104", "MH-105"]
    assert res["updated_count"] == 4
    assert res["new_status"] == "AVAILABLE_FOR_SALE"
    assert res["widget"]["widget_type"] == "PMS_INVENTORY_UPDATE"


def test_resalys_update_unit_inventory_bearer_token():
    res = resalys_update_unit_inventory(
        campsite_id="LA_SIRENE_06",
        unit_ids=["MH-102"],
        user_token="user_token_custom_123",
    )
    assert res["status"] == "SUCCESS"
    assert res["headers"]["Authorization"] == "Bearer user_token_custom_123"
    assert "user_token_custom_123" in res["widget"]["identity_scope"]


def test_resalys_update_unit_inventory_validation_errors():
    res1 = resalys_update_unit_inventory(campsite_id="", unit_ids=["MH-102"])
    assert res1["status"] == "VALIDATION_ERROR"

    res2 = resalys_update_unit_inventory(campsite_id="LA_SIRENE_06", unit_ids=[])
    assert res2["status"] == "VALIDATION_ERROR"

    # Non-string campsite ID
    res3 = resalys_update_unit_inventory(campsite_id=12345, unit_ids=["MH-102"])
    assert res3["status"] == "VALIDATION_ERROR"

    # Invalid new_status
    res4 = resalys_update_unit_inventory(campsite_id="LA_SIRENE_06", unit_ids=["MH-102"], new_status="INVALID_STATUS")
    assert res4["status"] == "VALIDATION_ERROR"


def test_pms_operations_agent_process_turn_with_session():
    agent = PMS_Operations_Agent()
    session = StateSession()
    session.set("session.campsite_id", "LA_SIRENE_06")
    session.set("session.unit_ids", ["MH-102", "MH-103"])

    res = agent.process_turn("Release mobil-homes to sale", session=session)

    assert res["status"] == "SUCCESS"
    assert res["agent"] == "PMS_Operations_Agent"
    assert res["campsite_id"] == "LA_SIRENE_06"
    assert res["unit_ids"] == ["MH-102", "MH-103"]


def test_pms_operations_agent_process_turn_edge_cases():
    agent = PMS_Operations_Agent()

    # None prompt and empty session context returns validation error
    res1 = agent.process_turn(None)
    assert res1["status"] == "VALIDATION_ERROR"

    # Prompt with maintenance keyword updates status to UNDER_MAINTENANCE
    session = StateSession()
    session.set("session.campsite_id", "LA_SIRENE_06")
    session.set("session.unit_ids", ["MH-102"])
    res2 = agent.process_turn("Put units under maintenance", session=session)
    assert res2["status"] == "SUCCESS"
    assert res2["new_status"] == "UNDER_MAINTENANCE"
