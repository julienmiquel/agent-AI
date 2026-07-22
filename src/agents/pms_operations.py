"""PMS Operations Agent & Resalys API Inventory Tools.

Manages campsite unit maintenance status and inventory release for sale via Resalys PMS API.
"""

import logging
from typing import Any, Dict, List, Optional
from src.config import APIGEE_PMS_ENDPOINT, MODEL_PMS
from src.datastore import datastore

logger = logging.getLogger(__name__)


def resalys_update_unit_inventory(
    campsite_id: Optional[str] = None,
    unit_ids: Optional[Any] = None,
    new_status: str = "AVAILABLE_FOR_SALE",
    unit_type: Optional[str] = "PREMIUM_3_BEDROOMS",
    user_token: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Updates the operational status of campsite units in Resalys PMS via Apigee REST API."""
    if campsite_id is None:
        campsite_id = kwargs.get("campsiteId") or kwargs.get("campsite_id") or "LA_SIRENE_06"
    unit_ids = unit_ids if unit_ids is not None else kwargs.get("unitIds") or kwargs.get("unit_ids") or kwargs.get("unitId")
    new_status = new_status or kwargs.get("newStatus") or "AVAILABLE_FOR_SALE"
    unit_type = unit_type or kwargs.get("unitType") or "PREMIUM_3_BEDROOMS"

    logger.info("resalys_update_unit_inventory called for campsite_id='%s', units=%s, new_status='%s'",
                campsite_id, unit_ids, new_status)

    if not isinstance(campsite_id, str) or not campsite_id.strip():
        logger.error("Validation error: Campsite ID is empty or non-string.")
        return {
            "status": "VALIDATION_ERROR",
            "error": "Campsite ID cannot be empty.",
            "updated_count": 0,
            "widget": None,
        }

    valid_statuses = {"AVAILABLE_FOR_SALE", "UNDER_MAINTENANCE", "BLOCKED"}
    if not isinstance(new_status, str) or new_status not in valid_statuses:
        logger.error("Validation error: Invalid new_status '%s'. Must be one of %s", new_status, valid_statuses)
        return {
            "status": "VALIDATION_ERROR",
            "error": f"Invalid status '{new_status}'. Allowed values: {sorted(valid_statuses)}.",
            "updated_count": 0,
            "widget": None,
        }

    if not isinstance(unit_ids, (list, tuple)):
        unit_ids = [unit_ids] if unit_ids is not None else []

    clean_units = [str(u).strip() for u in unit_ids if u is not None and str(u).strip()]
    if not clean_units:
        logger.error("Validation error: Unit IDs list is empty.")
        return {
            "status": "VALIDATION_ERROR",
            "error": "Unit IDs list cannot be empty.",
            "updated_count": 0,
            "widget": None,
        }

    endpoint = f"{APIGEE_PMS_ENDPOINT}/units/status"
    auth_token = user_token or "mock_cloud_identity_token_julien"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }

    widget_payload = {
        "widget_type": "PMS_INVENTORY_UPDATE",
        "campsite_id": campsite_id,
        "unit_type": unit_type,
        "unit_ids": clean_units,
        "updated_status": new_status,
        "updated_count": len(clean_units),
        "endpoint": endpoint,
        "identity_scope": f"CloudIdentity ({auth_token})",
    }

    for uid in clean_units:
        datastore.save_pms_unit(campsite_id=campsite_id, unit_id=uid, status=new_status)

    msg = f"Successfully updated {len(clean_units)} unit(s) ({', '.join(clean_units)}) at {campsite_id} to status '{new_status}' in Resalys PMS."
    logger.info("Resalys inventory status update successful: %s", msg)

    return {
        "status": "SUCCESS",
        "campsite_id": campsite_id,
        "unit_ids": clean_units,
        "updated_count": len(clean_units),
        "new_status": new_status,
        "endpoint": endpoint,
        "headers": headers,
        "widget": widget_payload,
        "message": msg,
    }


def resalys_get_support_tickets(
    status: str = "ALL",
    campsite_id: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Retrieves customer claim support tickets (maintenance, cleanliness, billing, etc.) from Firebase Firestore DB."""
    status_filter = status or kwargs.get("status") or "ALL"
    campsite_filter = campsite_id or kwargs.get("campsiteId") or kwargs.get("campsite_id")
    tickets = datastore.get_support_tickets(status=status_filter, campsite_id=campsite_filter)

    widget_payload = {
        "widget_type": "SUPPORT_TICKETS",
        "tab": "tickets",
        "view": "tickets",
        "status": status_filter,
        "count": len(tickets),
        "url": "ui://pms-crm/claim-app.html",
    }

    msg = f"Voici la liste des {len(tickets)} ticket(s) de réclamation/maintenance (Statut: {status_filter}). Vous pouvez consulter et gérer ces tickets directement sur la page dédiée ci-dessous :\n\n🔗 [Ouvrir les Tickets de Maintenance & Réclamations](ui://pms-crm/claim-app.html)"
    logger.info("Retrieved %d support tickets", len(tickets))
    return {
        "status": "SUCCESS",
        "tickets": tickets,
        "tab": "tickets",
        "view": "tickets",
        "widget": widget_payload,
        "message": msg,
    }


class PMS_Operations_Agent:
    """Specialized Sub-Agent for PMS Operations & Resalys Inventory Management."""

    def __init__(self, model_name: str = MODEL_PMS):
        self.model_name = model_name
        self.name = "PMS_Operations_Agent"
        logger.info("Initialized %s with model_name='%s'", self.name, self.model_name)

    def process_turn(
        self, prompt: Optional[str], session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Process turn to update unit inventory status or fetch support claim tickets based on prompt or active session context."""
        logger.info("PMS_Operations_Agent processing turn for prompt: '%s'", prompt)

        campsite_id = None
        unit_ids = []
        user_token = None

        if session and hasattr(session, "get"):
            campsite_id = session.get("session.campsite_id")
            raw_units = session.get("session.unit_ids", [])
            user_token = session.get("session.user_token")
            if isinstance(raw_units, str):
                unit_ids = [raw_units]
            elif isinstance(raw_units, (list, tuple)):
                unit_ids = [str(u).strip() for u in raw_units if u is not None and str(u).strip()]
            logger.info("Retrieved session context: campsite_id='%s', unit_ids=%s", campsite_id, unit_ids)

        prompt_str = prompt or ""
        prompt_lower = prompt_str.lower()

        if "la sirène" in prompt_lower or "la sirene" in prompt_lower:
            campsite_id = "LA_SIRENE_06"
        elif "dolmen cove" in prompt_lower or "dolmen_cove" in prompt_lower:
            campsite_id = "DOLMEN_COVE_02"

        if not campsite_id:
            campsite_id = "LA_SIRENE_06"

        if any(kw in prompt_lower for kw in ["ticket", "tickets", "réclamation", "reclamation", "claim"]):
            res = resalys_get_support_tickets(campsite_id=campsite_id)
            res["agent"] = self.name
            return res

        if not unit_ids:
            import re
            found = re.findall(r"MH-\d+", prompt_str, re.IGNORECASE)
            if found:
                unit_ids = [u.upper() for u in found]

        if not unit_ids:
            logger.warning("No unit IDs specified or found in session context.")
            return {
                "status": "VALIDATION_ERROR",
                "agent": self.name,
                "error": "No mobil-home unit IDs specified or found in session context to release.",
                "message": "Please specify the unit IDs to release or execute yield analysis first.",
                "updated_count": 0,
                "widget": None,
            }

        new_status = "AVAILABLE_FOR_SALE"
        if "maintenance" in prompt_lower:
            new_status = "UNDER_MAINTENANCE"
        elif "block" in prompt_lower or "hold" in prompt_lower:
            new_status = "BLOCKED"

        logger.info("Executing Resalys update: campsite_id='%s', units=%s, status='%s'", campsite_id, unit_ids, new_status)
        res = resalys_update_unit_inventory(
            campsite_id=campsite_id,
            unit_ids=unit_ids,
            new_status=new_status,
            user_token=user_token,
        )

        res["agent"] = self.name
        return res
