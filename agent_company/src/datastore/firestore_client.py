"""Firebase Cloud Firestore Data Store Interface for European Camping Company (Company).

Provides collection storage for Session Contexts, PMS Resalys Unit Inventory, and CRM Flash Campaigns.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Attempt importing google.cloud.firestore
try:
    from google.cloud import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False


class CompanyDatastore:
    """Firebase Firestore Datastore manager with graceful fallback memory caching."""

    def __init__(self, database_id: str = "(default)", project_id: Optional[str] = None):
        self.database_id = database_id
        self.project_id = project_id or os.getenv("GCP_PROJECT", "company-genai-analytics")
        self.db = None
        self._memory_store: Dict[str, Dict[str, Dict[str, Any]]] = {
            "sessions": {},
            "pms_inventory": {},
            "crm_campaigns": {},
            "support_tickets": {},
        }

        if FIRESTORE_AVAILABLE:
            try:
                # Initialize Firestore client
                self.db = firestore.Client(project=self.project_id, database=self.database_id)
                logger.info("Initialized Firebase Firestore client for project '%s'", self.project_id)
            except Exception as e:
                logger.warning("Could not initialize live Firestore Client (%s). Using Datastore Memory Mode.", str(e))
                self.db = None
        else:
            logger.info("google-cloud-firestore not loaded. Operating in Datastore Memory Mode.")

    # ---------------------------------------------------------------------------
    # Collection 1: Sessions
    # ---------------------------------------------------------------------------
    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update session state document in Firestore 'sessions' collection."""
        doc_data = {
            "session_id": session_id,
            **session_data,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if self.db:
            try:
                doc_ref = self.db.collection("sessions").document(session_id)
                doc_ref.set(doc_data, merge=True)
                logger.info("Saved session '%s' to Firebase Firestore", session_id)
            except Exception as e:
                logger.debug("Firestore save session fallback to memory: %s", str(e))

        # Always update memory store
        self._memory_store["sessions"][session_id] = doc_data
        return doc_data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session state document from Firestore 'sessions' collection."""
        if self.db:
            try:
                doc_ref = self.db.collection("sessions").document(session_id)
                doc = doc_ref.get()
                if doc.exists:
                    return doc.to_dict()
            except Exception as e:
                logger.debug("Firestore get session fallback to memory: %s", str(e))

        return self._memory_store["sessions"].get(session_id)

    # ---------------------------------------------------------------------------
    # Collection 2: PMS Inventory
    # ---------------------------------------------------------------------------
    def save_pms_unit(self, campsite_id: str, unit_id: str, status: str, nightly_rate: float = 120.0) -> Dict[str, Any]:
        """Save or update mobil-home unit status in Firestore 'pms_inventory' collection."""
        doc_id = f"{campsite_id}_{unit_id}"
        doc_data = {
            "doc_id": doc_id,
            "campsite_id": campsite_id,
            "unit_id": unit_id,
            "status": status,
            "nightly_rate": nightly_rate,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if self.db:
            try:
                doc_ref = self.db.collection("pms_inventory").document(doc_id)
                doc_ref.set(doc_data, merge=True)
                logger.info("Saved PMS unit '%s' (%s) to Firebase Firestore", unit_id, status)
            except Exception as e:
                logger.debug("Firestore save PMS unit fallback to memory: %s", str(e))

        self._memory_store["pms_inventory"][doc_id] = doc_data
        return doc_data

    def get_pms_units(self, campsite_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of PMS mobil-home units filtered by campsite_id."""
        units: List[Dict[str, Any]] = []

        if self.db:
            try:
                query = self.db.collection("pms_inventory")
                if campsite_id:
                    query = query.filter("campsite_id", "==", campsite_id)
                docs = query.stream()
                for doc in docs:
                    units.append(doc.to_dict())
                if units:
                    return units
            except Exception as e:
                logger.debug("Firestore get PMS units fallback to memory: %s", str(e))

        # Fallback to memory store
        for item in self._memory_store["pms_inventory"].values():
            if not campsite_id or item.get("campsite_id") == campsite_id:
                units.append(item)

        return units

    # ---------------------------------------------------------------------------
    # Collection 3: CRM Campaigns
    # ---------------------------------------------------------------------------
    def save_crm_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update staged CRM flash campaign in Firestore 'crm_campaigns' collection."""
        campaign_name = campaign_data.get("campaign_name", f"Campaign_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
        doc_data = {
            "campaign_name": campaign_name,
            **campaign_data,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if self.db:
            try:
                doc_ref = self.db.collection("crm_campaigns").document(campaign_name)
                doc_ref.set(doc_data, merge=True)
                logger.info("Saved CRM campaign '%s' to Firebase Firestore", campaign_name)
            except Exception as e:
                logger.debug("Firestore save CRM campaign fallback to memory: %s", str(e))

        self._memory_store["crm_campaigns"][campaign_name] = doc_data
        return doc_data

    def get_crm_campaigns(self) -> List[Dict[str, Any]]:
        """Get all staged CRM campaigns from Firestore 'crm_campaigns' collection."""
        campaigns: List[Dict[str, Any]] = []

        if self.db:
            try:
                docs = self.db.collection("crm_campaigns").stream()
                for doc in docs:
                    campaigns.append(doc.to_dict())
                if campaigns:
                    return campaigns
            except Exception as e:
                logger.debug("Firestore get CRM campaigns fallback to memory: %s", str(e))

        return list(self._memory_store["crm_campaigns"].values())

    # ---------------------------------------------------------------------------
    # Collection 4: Support Tickets
    # ---------------------------------------------------------------------------
    def save_support_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update customer claim support ticket in Firestore 'support_tickets' collection."""
        ticket_id = ticket_data.get("ticket_id") or f"TCK-{datetime.now(timezone.utc).strftime('%S%f')[:6]}"
        doc_data = {
            "ticket_id": ticket_id,
            "status": "OPEN",
            **ticket_data,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if "created_at" not in doc_data:
            doc_data["created_at"] = doc_data["updated_at"]

        if self.db:
            try:
                doc_ref = self.db.collection("support_tickets").document(ticket_id)
                doc_ref.set(doc_data, merge=True)
                logger.info("Saved support ticket '%s' to Firebase Firestore", ticket_id)
            except Exception as e:
                logger.debug("Firestore save support ticket fallback to memory: %s", str(e))

        self._memory_store.setdefault("support_tickets", {})[ticket_id] = doc_data
        return doc_data

    def get_support_tickets(
        self, status_filter: Optional[str] = None, campsite_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of support tickets filtered by status or campsite_id."""
        tickets: List[Dict[str, Any]] = []

        if self.db:
            try:
                query = self.db.collection("support_tickets")
                if status_filter and status_filter != "ALL":
                    query = query.filter("status", "==", status_filter)
                if campsite_id:
                    query = query.filter("campsite_id", "==", campsite_id)
                docs = query.stream()
                for doc in docs:
                    tickets.append(doc.to_dict())
                if tickets:
                    return tickets
            except Exception as e:
                logger.debug("Firestore get support tickets fallback to memory: %s", str(e))

        for item in self._memory_store.get("support_tickets", {}).values():
            if status_filter and status_filter != "ALL" and item.get("status") != status_filter:
                continue
            if campsite_id and item.get("campsite_id") != campsite_id:
                continue
            tickets.append(item)

        return tickets


# Global Datastore Instance
datastore = CompanyDatastore()
