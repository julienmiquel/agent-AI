"""Unit tests for ECG Firebase Cloud Firestore Datastore module."""

import pytest
from src.datastore import ECGDatastore, datastore
from src.agents import StateSession, resalys_update_unit_inventory, crm_create_flash_campaign


def test_firestore_datastore_initialization():
    ds = ECGDatastore(project_id="ecg-test-project")
    assert ds.project_id == "ecg-test-project"
    assert "sessions" in ds._memory_store
    assert "pms_inventory" in ds._memory_store
    assert "crm_campaigns" in ds._memory_store


def test_session_state_datastore_persistence():
    session = StateSession(session_id="test_firebase_session_01", user_id="julien")
    session.set("session.target_market", "DE")
    session.set("session.campsite_id", "HIPOCAMP_07")

    saved_session = datastore.get_session("test_firebase_session_01")
    assert saved_session is not None
    assert saved_session["session_id"] == "test_firebase_session_01"
    assert saved_session["session.target_market"] == "DE"
    assert saved_session["session.campsite_id"] == "HIPOCAMP_07"


def test_pms_unit_inventory_firestore_persistence():
    res = resalys_update_unit_inventory(
        campsite_id="LA_SIRENE_06",
        unit_ids=["MH-102", "MH-103"],
        new_status="AVAILABLE_FOR_SALE",
    )
    assert res["status"] == "SUCCESS"

    units = datastore.get_pms_units(campsite_id="LA_SIRENE_06")
    assert len(units) >= 2
    u102 = next((u for u in units if u["unit_id"] == "MH-102"), None)
    assert u102 is not None
    assert u102["status"] == "AVAILABLE_FOR_SALE"


def test_crm_flash_campaign_firestore_persistence():
    res = crm_create_flash_campaign(
        campaign_name="Flash_Promo_NL_Med_Firebase",
        target_segment_id="SEG_NL_PAST_GUESTS_2025",
        discount_percentage=20,
        target_market="NL",
        cluster="MEDITERRANEAN_SOUTH",
    )
    assert res["status"] == "SUCCESS"

    campaigns = datastore.get_crm_campaigns()
    assert len(campaigns) >= 1
    cmp = next((c for c in campaigns if c["campaign_name"] == "Flash_Promo_NL_Med_Firebase"), None)
    assert cmp is not None
    assert cmp["discount_percentage"] == 20
    assert cmp["target_segment_id"] == "SEG_NL_PAST_GUESTS_2025"
