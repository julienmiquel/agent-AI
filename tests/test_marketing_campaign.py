"""Unit tests for Marketing_Campaign_Agent, localized copywriting, and GCS Imagen asset URIs."""

import pytest
from src.agents import (
    Company_Supervisor_Agent,
    Marketing_Campaign_Agent,
    StateSession,
    crm_create_flash_campaign,
)
from src.agents.marketing_campaign import (
    generate_promotional_copy,
    resolve_imagen_asset_uri,
)


def test_marketing_campaign_agent_initialization():
    agent = Marketing_Campaign_Agent()
    assert agent.name == "Marketing_Campaign_Agent"


def test_localized_promotional_copywriting():
    copy_nl = generate_promotional_copy("NL", "MEDITERRANEAN_SOUTH", 15)
    assert "Profiteer van 15% korting" in copy_nl
    assert "La Sirène" in copy_nl

    copy_de = generate_promotional_copy("DE", "MEDITERRANEAN_SOUTH", 20)
    assert "Sichern Sie sich 20% Rabatt" in copy_de

    copy_fr = generate_promotional_copy("FR", "MEDITERRANEAN_SOUTH", 10)
    assert "Profitez de 10% de réduction" in copy_fr


def test_resolve_imagen_asset_uri():
    uri_nl = resolve_imagen_asset_uri("NL", "MEDITERRANEAN_SOUTH")
    assert uri_nl == "gs://company-marketing-assets/genai/banners/nl_mediterranean_south_july.png"

    uri_de = resolve_imagen_asset_uri("DE", "ATLANTIC_NORTH")
    assert uri_de == "gs://company-marketing-assets/genai/banners/de_atlantic_north_july.png"


def test_crm_create_flash_campaign_success():
    res = crm_create_flash_campaign(
        campaign_name="Rattrapage_NL_Med_July",
        target_segment_id="SEG_NL_PAST_GUESTS_MED_2025",
        discount_percentage=15,
        target_market="NL",
        cluster="MEDITERRANEAN_SOUTH",
    )

    assert res["status"] == "SUCCESS"
    assert res["campaign_name"] == "Rattrapage_NL_Med_July"
    assert res["target_segment_id"] == "SEG_NL_PAST_GUESTS_MED_2025"
    assert res["discount_percentage"] == 15
    assert "Profiteer van 15% korting" in res["copywriting_text"]
    assert res["image_asset_gcs_uri"] == "gs://company-marketing-assets/genai/banners/nl_mediterranean_south_july.png"
    assert res["widget"]["widget_type"] == "MARKETING_CAMPAIGN_DRAFT"


def test_crm_create_flash_campaign_validation_errors():
    res1 = crm_create_flash_campaign(campaign_name="", target_segment_id="SEG_NL")
    assert res1["status"] == "VALIDATION_ERROR"

    res2 = crm_create_flash_campaign(campaign_name="Test", target_segment_id="")
    assert res2["status"] == "VALIDATION_ERROR"

    res3 = crm_create_flash_campaign(campaign_name="Test", target_segment_id="SEG_NL", discount_percentage=-10)
    assert res3["status"] == "VALIDATION_ERROR"

    res4 = crm_create_flash_campaign(campaign_name="Test", target_segment_id="SEG_NL", discount_percentage=150)
    assert res4["status"] == "VALIDATION_ERROR"


def test_non_string_type_safety():
    copy = generate_promotional_copy(target_market=None, cluster=None, discount_percentage=15)
    assert "Profiteer van 15% korting" in copy

    uri = resolve_imagen_asset_uri(target_market=123, cluster="MEDITERRANEAN SOUTH")
    assert uri == "gs://company-marketing-assets/genai/banners/123_mediterranean_south_july.png"


def test_marketing_campaign_agent_process_turn_with_session():
    agent = Marketing_Campaign_Agent()
    session = StateSession()
    session.set("session.target_market", "NL")
    session.set("session.target_cluster", "MEDITERRANEAN_SOUTH")

    res = agent.process_turn("Draft 20% flash promo for Dutch market", session=session)

    assert res["status"] == "SUCCESS"
    assert res["agent"] == "Marketing_Campaign_Agent"
    assert "Flash_Promo_NL_MEDITERRANEAN_SOUTH" in res["campaign_name"]
    assert "Profiteer van 20% korting" in res["copywriting_text"]
    assert res["discount_percentage"] == 20
    assert res["image_asset_gcs_uri"] == "gs://company-marketing-assets/genai/banners/nl_mediterranean_south_july.png"


def test_marketing_campaign_hitl_interception_flow():
    supervisor = Company_Supervisor_Agent()
    session = StateSession()
    session.set("session.target_market", "NL")
    session.set("session.target_cluster", "MEDITERRANEAN_SOUTH")

    # Turn 1: Marketing campaign turn pauses for HITL approval
    res1 = supervisor.process_turn("Draft a flash promotion campaign for Dutch past guests", session)
    assert res1["status"] == "PENDING_CONFIRMATION"
    assert res1["intent"] == "MARKETING_CAMPAIGN"
    assert res1["widget"]["widget_type"] == "HITL_APPROVAL_CARD"
    assert res1["widget"]["manifest"]["target_api"] == "POST /marketing/v1/campaigns/draft"
    assert res1["widget"]["manifest"]["target_market"] == "NL"
    assert session.pending_action is not None

    # Turn 2: User approves -> execution succeeds
    res_approve = supervisor.process_turn("Approve", session)
    assert res_approve["status"] == "SUCCESS"
    assert res_approve["routed_agent"] == "MARKETING_CAMPAIGN_AGENT"
    assert res_approve["widget"]["status"] == "CONFIRMED"
    assert session.pending_action is None
