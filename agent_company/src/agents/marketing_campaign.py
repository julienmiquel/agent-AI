"""Marketing Campaign Agent & CRM Flash Promo Tools.

Drafts marketing campaign copy, generates promotional assets, and registers drafts in CRM.
"""

import logging
import re
from typing import Any, Dict, Optional
from src.config import APIGEE_MARKETING_ENDPOINT, GCS_MARKETING_BUCKET, MODEL_MARKETING
from src.datastore import datastore

logger = logging.getLogger(__name__)


def generate_promotional_copy(
    target_market: Any = "NL",
    cluster: Any = "MEDITERRANEAN_SOUTH",
    discount_percentage: int = 15,
) -> str:
    """Generates localized promotional copywriting tailored to target market.

    Args:
        target_market: Market country code ('NL', 'FR', 'DE', etc.).
        cluster: Target cluster identifier ('MEDITERRANEAN_SOUTH', etc.).
        discount_percentage: Discount percentage integer (e.g. 15).

    Returns:
        Localized promo copy text string.
    """
    raw_mkt = str(target_market or "NL").strip().upper()
    if any(k in raw_mkt for k in ["FR", "VOYAGEUR", "FAMILLE", "FRENCH", "SOLEIL"]):
        mkt = "FR"
    elif any(k in raw_mkt for k in ["DE", "GERMAN", "URLAUB"]):
        mkt = "DE"
    elif any(k in raw_mkt for k in ["NL", "DUTCH", "KORTING"]):
        mkt = "NL"
    else:
        mkt = raw_mkt[:2] if len(raw_mkt) >= 2 else "NL"

    if mkt == "NL":
        return (
            f"Profiteer van {discount_percentage}% korting op uw zomervakantie in Zuid-Frankrijk! "
            f"Boek nu uw Premium stacaravan op La Sirène."
        )
    elif mkt == "DE":
        return (
            f"Sichern Sie sich {discount_percentage}% Rabatt auf Ihren Sommerurlaub in Südfrankreich! "
            f"Buchen Sie jetzt Ihr Premium Mobilheim."
        )
    elif mkt == "FR":
        return (
            f"Profitez de {discount_percentage}% de réduction sur vos vacances d'été en Méditerranée ! "
            f"Réservez dès maintenant votre mobil-home Premium."
        )
    else:
        return (
            f"Enjoy a {discount_percentage}% discount on your summer holiday in the South of France! "
            f"Book your Premium mobil-home now."
        )


def resolve_imagen_asset_uri(
    target_market: Any = "NL",
    cluster: Any = "MEDITERRANEAN_SOUTH",
) -> str:
    """Resolves or simulates Google Cloud Storage Imagen asset URI for campaign creatives.

    Args:
        target_market: Target market code (e.g. 'NL').
        cluster: Target cluster identifier (e.g. 'MEDITERRANEAN_SOUTH').

    Returns:
        GCS URI string formatted as 'gs://company-marketing-assets/genai/banners/{market}_{cluster}_july.png'.
    """
    mkt = str(target_market or "nl").strip().lower()
    cls = str(cluster or "mediterranean_south").strip().lower().replace(" ", "_")
    return f"{GCS_MARKETING_BUCKET}banners/{mkt}_{cls}_july.png"


def calculate_dynamic_discount(
    revenue_loss: float = 13950.0,
    lag_percentage: float = 0.15,
) -> int:
    """Calculates discount percentage automatically based on the loss of unmade sales / held-back inventory.

    Args:
        revenue_loss: Estimated revenue loss in Euros from unmade sales (default: 13950.0).
        lag_percentage: Booking pacing lag percentage (default: 0.15 for 15%).

    Returns:
        Recommended promotional discount integer percentage (e.g. 10, 15, or 25).
    """
    if revenue_loss >= 20000 or lag_percentage >= 0.20:
        return 25
    elif revenue_loss >= 10000 or lag_percentage >= 0.15:
        return 15
    elif revenue_loss >= 5000 or lag_percentage >= 0.10:
        return 10
    return 10


def crm_create_flash_campaign(
    campaign_name: Optional[str] = None,
    target_segment_id: Optional[str] = None,
    discount_percentage: Optional[Any] = None,
    estimated_revenue_loss_eur: float = 13950.0,
    copywriting_text: Optional[str] = None,
    image_asset_gcs_uri: Optional[str] = None,
    target_market: Optional[str] = None,
    cluster: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Drafts a flash promotion marketing campaign via CRM Webhook API.

    Args:
        campaign_name: Optional campaign title string.
        target_segment_id: Optional target audience CRM segment identifier.
        discount_percentage: Optional promotional discount percentage integer or string.
        estimated_revenue_loss_eur: Estimated revenue loss in Euros from unmade sales (default: 13950.0).
        copywriting_text: Optional localized advertising copy string.
        image_asset_gcs_uri: Optional Google Cloud Storage URI for campaign banner graphic.
        target_market: Optional market country code (e.g. 'NL', 'FR', 'DE').
        cluster: Optional target campsite cluster name.
        **kwargs: Additional keyword arguments for camelCase alias support from UI frontend.

    Returns:
        Structured response containing execution status, generated campaign ID, applied parameters,
        and interactive CRM Flash Campaign widget payload.
    """
    # Resolve camelCase parameter aliases from Gemini Enterprise UI
    if campaign_name is None:
        campaign_name = kwargs.get("campaignName") or kwargs.get("campaign_name") or "Offre Spéciale Été 2026"

    if not isinstance(campaign_name, str) or not campaign_name.strip():
        logger.error("Validation error: Campaign name is empty.")
        return {
            "status": "VALIDATION_ERROR",
            "error": "Campaign name cannot be empty.",
            "widget": None,
        }

    if target_segment_id is None:
        target_segment_id = kwargs.get("targetSegmentId") or kwargs.get("target_segment_id")
        if target_segment_id is None:
            mkt_code = str(target_market or "NL").strip().upper()[:10]
            target_segment_id = f"SEG_{mkt_code}_RETARGETING_2026"
            logger.info("Auto-generated default target_segment_id: '%s'", target_segment_id)

    if not isinstance(target_segment_id, str) or not target_segment_id.strip():
        logger.error("Validation error: Target segment ID is empty.")
        return {
            "status": "VALIDATION_ERROR",
            "error": "Target segment ID cannot be empty.",
            "widget": None,
        }

    if discount_percentage is None or str(discount_percentage).strip() in ("", "None", "auto", "0"):
        discount_val = calculate_dynamic_discount(revenue_loss=estimated_revenue_loss_eur)
        logger.info("Auto-calculated discount percentage based on revenue loss (€%.2f): %d%%",
                    estimated_revenue_loss_eur, discount_val)
    else:
        try:
            discount_val = int(discount_percentage)
            if not (0 <= discount_val <= 100):
                logger.error("Validation error: Invalid discount_percentage '%s'", discount_percentage)
                return {
                    "status": "VALIDATION_ERROR",
                    "error": "Discount percentage must be an integer between 0 and 100.",
                    "widget": None,
                }
        except (ValueError, TypeError):
            discount_val = calculate_dynamic_discount(revenue_loss=estimated_revenue_loss_eur)

    copy_text = copywriting_text if (copywriting_text is not None and copywriting_text != "") else generate_promotional_copy(target_market, cluster, discount_val)
    image_uri = image_asset_gcs_uri if (image_asset_gcs_uri is not None and image_asset_gcs_uri != "") else resolve_imagen_asset_uri(target_market, cluster)
    endpoint = f"{APIGEE_MARKETING_ENDPOINT}/campaigns/draft"

    widget_payload = {
        "widget_type": "MARKETING_CAMPAIGN_DRAFT",
        "campaign_name": campaign_name,
        "target_segment_id": target_segment_id,
        "discount_percentage": discount_val,
        "target_market": target_market,
        "cluster": cluster,
        "image_asset_gcs_uri": image_uri,
        "endpoint": endpoint,
    }

    msg = f"Successfully created draft campaign '{campaign_name}' targeting segment '{target_segment_id}' ({discount_val}% discount)."
    logger.info("CRM flash campaign creation successful: %s", msg)

    res_payload = {
        "status": "SUCCESS",
        "campaign_name": campaign_name,
        "target_segment_id": target_segment_id,
        "discount_percentage": discount_val,
        "copywriting_text": copy_text,
        "image_asset_gcs_uri": image_uri,
        "endpoint": endpoint,
        "widget": widget_payload,
        "message": msg,
    }

    datastore.save_crm_campaign(res_payload)
    return res_payload


class Marketing_Campaign_Agent:
    """Specialized Sub-Agent for CRM Marketing Campaigns & Asset Generation."""

    def __init__(self, model_name: str = MODEL_MARKETING):
        self.model_name = model_name
        self.name = "Marketing_Campaign_Agent"
        logger.info("Initialized %s with model_name='%s'", self.name, self.model_name)

    def process_turn(
        self, prompt: str, session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Process turn to draft marketing flash campaign based on prompt or session context.

        Args:
            prompt: Natural language user prompt string.
            session: Optional active StateSession instance containing target market and cluster.

        Returns:
            Dictionary containing campaign creation outcome, copywriting text, banner GCS URI,
            and interactive CRM Flash Campaign widget payload.
        """
        logger.info("Marketing_Campaign_Agent processing turn for prompt: '%s'", prompt)

        target_market = "NL"
        cluster = "MEDITERRANEAN_SOUTH"
        discount = 15

        if prompt:
            m = re.search(r'(\d{1,2})\s*%', prompt)
            if m:
                try:
                    discount = int(m.group(1))
                except ValueError:
                    pass

        if session and hasattr(session, "get"):
            target_market = session.get("session.target_market") or "NL"
            cluster = session.get("session.target_cluster") or "MEDITERRANEAN_SOUTH"
            logger.info("Retrieved session context: target_market='%s', cluster='%s'", target_market, cluster)

        campaign_name = f"Flash_Promo_{target_market}_{cluster}_July"
        segment_id = f"SEG_{target_market}_PAST_GUESTS_{cluster}_2025"

        copy_text = generate_promotional_copy(target_market, cluster, discount_percentage=discount)
        image_uri = resolve_imagen_asset_uri(target_market, cluster)

        logger.info("Creating CRM campaign: campaign_name='%s', segment_id='%s'", campaign_name, segment_id)
        res = crm_create_flash_campaign(
            campaign_name=campaign_name,
            target_segment_id=segment_id,
            discount_percentage=discount,
            copywriting_text=copy_text,
            image_asset_gcs_uri=image_uri,
            target_market=target_market,
            cluster=cluster,
        )

        res["agent"] = self.name
        return res
