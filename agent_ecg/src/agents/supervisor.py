"""ECG Root Supervisor Agent & Conversational Session Scaffold.

Coordinates multi-agent intent routing, retains StateSession context across turns,
and enforces Human-in-the-Loop (HITL) interception gates for state-changing operations.
"""

import copy
import logging
import re
from typing import Any, Dict, Optional
from src.config import MODEL_SUPERVISOR
from src.agents.yield_analytics import Yield_Analytics_Agent
from src.agents.pms_operations import PMS_Operations_Agent
from src.agents.marketing_campaign import Marketing_Campaign_Agent

logger = logging.getLogger(__name__)


class StateSession:
    """Session state context retention manager.
    
    Persists multi-turn variables across agent handoffs without re-prompting.
    """

    def __init__(self, session_id: str = "default_session", user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self._state: Dict[str, Any] = {
            "session.target_cluster": None,
            "session.campsite_id": None,
            "session.unit_ids": [],
            "session.date_range": None,
            "session.target_market": None,
            "session.pending_action": None,
        }
        logger.info("Initialized StateSession session_id='%s', user_id='%s'", self.session_id, self.user_id)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a session state variable."""
        val = self._state.get(key, default)
        logger.debug("StateSession.get('%s') -> %s", key, val)
        return val

    def set(self, key: str, value: Any) -> None:
        """Store or update a session state variable."""
        logger.info("StateSession.set('%s', %s)", key, value)
        self._state[key] = value

    @property
    def unit_ids(self) -> Any:
        return self.get("session.unit_ids", [])

    @unit_ids.setter
    def unit_ids(self, values: Any) -> None:
        self.set("session.unit_ids", values)

    @property
    def campsite_id(self) -> Any:
        return self.get("session.campsite_id")

    @campsite_id.setter
    def campsite_id(self, value: Any) -> None:
        self.set("session.campsite_id", value)

    @property
    def target_cluster(self) -> Any:
        return self.get("session.target_cluster")

    @target_cluster.setter
    def target_cluster(self, value: Any) -> None:
        self.set("session.target_cluster", value)

    @property
    def target_market(self) -> Any:
        return self.get("session.target_market")

    @target_market.setter
    def target_market(self, value: Any) -> None:
        self.set("session.target_market", value)

    @property
    def pending_action(self) -> Optional[Dict[str, Any]]:
        return self.get("session.pending_action")

    @pending_action.setter
    def pending_action(self, value: Optional[Dict[str, Any]]) -> None:
        self.set("session.pending_action", value)

    def update_from_prompt(self, prompt: Any) -> None:
        """Extract and update session variables from user prompt keywords safely."""
        if not isinstance(prompt, str) or not prompt:
            return

        prompt_lower = prompt.lower()

        # Cluster detection
        if "mediterranean south" in prompt_lower or "med_south" in prompt_lower:
            self.set("session.target_cluster", "MEDITERRANEAN_SOUTH")
        elif "atlantic north" in prompt_lower:
            self.set("session.target_cluster", "ATLANTIC_NORTH")

        # Campsite detection
        if "la sirène" in prompt_lower or "la sirene" in prompt_lower:
            self.set("session.campsite_id", "LA_SIRENE_06")
        elif "dolmen cove" in prompt_lower or "dolmen_cove" in prompt_lower:
            self.set("session.campsite_id", "DOLMEN_COVE_02")

        # Target Market / Country detection with word boundary regex
        if re.search(r'\b(dutch|netherlands|nl)\b', prompt_lower):
            self.set("session.target_market", "NL")
        elif re.search(r'\b(french|france|fr)\b', prompt_lower):
            self.set("session.target_market", "FR")
        elif re.search(r'\b(german|germany|de)\b', prompt_lower):
            self.set("session.target_market", "DE")

    def to_dict(self) -> Dict[str, Any]:
        """Export session state dictionary with deepcopy to prevent reference leaks."""
        d = copy.deepcopy(self._state)
        d["session_id"] = self.session_id
        d["user_id"] = self.user_id
        return d


class ECG_Supervisor_Agent:
    """Root Supervisor Agent for European Camping Group (ECG).
    
    Routes natural language user prompts to specialized sub-agents:
    - Yield_Analytics_Agent
    - PMS_Operations_Agent
    - Marketing_Campaign_Agent
    """

    def __init__(self, model_name: str = MODEL_SUPERVISOR):
        self.model_name = model_name
        self.name = "ECG_Supervisor_Agent"
        logger.info("Initialized %s with model_name='%s'", self.name, self.model_name)

    def classify_intent(self, prompt: str) -> str:
        """Classify user prompt into sub-agent intent domain."""
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            logger.warning("Empty or invalid prompt provided to classify_intent.")
            return "UNKNOWN"

        prompt_lower = prompt.lower()

        # Operational PMS actions & Support Claim Tickets take precedence
        if any(kw in prompt_lower for kw in ["release", "unlock", "pms", "resalys", "ticket", "tickets", "réclamation", "reclamation", "claim", "maintenance"]):
            intent = "PMS_OPERATIONS"
        # Comparative Yield Analytics keywords
        elif any(kw in prompt_lower for kw in ["vs last year", "prior year", "compare", "comparative", "bottleneck", "held-back", "held back"]):
            intent = "YIELD_ANALYTICS"
        # General PMS Operations Intent (unit/mobil-home status)
        elif any(kw in prompt_lower for kw in ["unit", "mobil-home"]):
            intent = "PMS_OPERATIONS"
        # Marketing Campaign Intent
        elif any(kw in prompt_lower for kw in ["promo", "discount", "campaign", "marketing", "crm", "flash", "copywriting"]):
            intent = "MARKETING_CAMPAIGN"
        # Yield Analytics Intent (default for data analysis requests)
        elif any(kw in prompt_lower for kw in ["occupancy", "revpar", "avpn", "yield", "analyze", "lag", "booking", "cluster"]):
            intent = "YIELD_ANALYTICS"
        else:
            intent = "YIELD_ANALYTICS"

        logger.info("Classified prompt intent -> '%s'", intent)
        return intent

    def process_turn(
        self, prompt: Optional[str], session: StateSession, bq_client: Optional[Any] = None, confirmed: bool = False
    ) -> Dict[str, Any]:
        """Process a conversational turn, updating session state and routing intent with HITL interception."""
        logger.info("Processing turn for session '%s' with prompt: '%s'", session.session_id, prompt)

        if prompt is None or not str(prompt).strip():
            logger.error("Validation error: Prompt is empty or whitespace.")
            return {
                "status": "VALIDATION_ERROR",
                "message": "Prompt cannot be empty. Please provide operational instructions.",
                "routed_agent": None,
                "session_state": session.to_dict(),
            }

        prompt_str = str(prompt)
        prompt_lower = prompt_str.lower().strip()

        # 1. Check if session has a pending HITL action awaiting approval/rejection
        pending = session.pending_action
        if pending and not confirmed:
            # Rejection check FIRST (including negative phrases like "not ok", "don't")
            is_rejection = (
                any(re.search(r'\b' + kw + r'\b', prompt_lower) for kw in ["reject", "no", "cancel", "non", "annuler", "stop", "abort"])
                or "not ok" in prompt_lower
                or "don't" in prompt_lower
                or "do not" in prompt_lower
            )
            if is_rejection:
                logger.info("User REJECTED pending HITL action: %s", pending.get("intent"))
                session.pending_action = None
                rejected_card = {
                    "widget_type": "HITL_APPROVAL_CARD",
                    "status": "REJECTED",
                    "amber_border": "#f43f5e",
                    "status_color": "#f43f5e",
                    "message": "Action cancelled by user.",
                }
                return {
                    "status": "CANCELLED",
                    "intent": pending.get("intent"),
                    "routed_agent": pending.get("routed_agent"),
                    "session_state": session.to_dict(),
                    "widget": rejected_card,
                    "message": "Operation cancelled by user. Zero backend side-effects occurred.",
                }

            # Approval check next with strict word boundaries
            is_approval = any(re.search(r'\b' + kw + r'\b', prompt_lower) for kw in ["approve", "yes", "confirm", "ok", "oui", "valider"])
            if is_approval:
                logger.info("User APPROVED pending HITL action: %s", pending.get("intent"))
                session.pending_action = None
                return self.process_turn(pending.get("prompt", prompt_str), session, bq_client=bq_client, confirmed=True)

        session.update_from_prompt(prompt_str)
        intent = self.classify_intent(prompt_str)

        if intent == "YIELD_ANALYTICS":
            logger.info("Routing turn to Yield_Analytics_Agent")
            yield_agent = Yield_Analytics_Agent()
            try:
                agent_result = yield_agent.process_query(prompt_str, session, bq_client=bq_client)
            except Exception as e:
                logger.error("Yield_Analytics_Agent execution error: %s", str(e))
                return {
                    "status": "ERROR",
                    "intent": intent,
                    "routed_agent": "YIELD_ANALYTICS_AGENT",
                    "session_state": session.to_dict(),
                    "message": f"Yield Analytics execution error: {str(e)}",
                }

            if agent_result.get("status") == "SUCCESS":
                widget = agent_result.get("widget") or {}
                held_back = agent_result.get("held_back_units") or widget.get("held_back_units") or []
                if held_back and isinstance(held_back[0], dict):
                    first_hb = held_back[0]
                    u_ids = first_hb.get("unit_ids", [])
                    c_id = first_hb.get("campsite_id")
                    if u_ids:
                        session.set("session.unit_ids", u_ids)
                    if c_id:
                        session.set("session.campsite_id", c_id)

            logger.info("Yield_Analytics_Agent completed with status '%s'", agent_result.get("status"))
            return {
                "status": agent_result.get("status", "SUCCESS"),
                "intent": intent,
                "routed_agent": "YIELD_ANALYTICS_AGENT",
                "session_state": session.to_dict(),
                "agent_output": agent_result,
                "message": agent_result.get("message", "Routed to YIELD_ANALYTICS_AGENT with active session context."),
            }

        elif intent in {"PMS_OPERATIONS", "MARKETING_CAMPAIGN"}:
            # Check for HITL interception requirement
            if not confirmed:
                logger.info("Intercepting mutating call for %s -> HITL Approval Gate required", intent)
                session.pending_action = {
                    "intent": intent,
                    "routed_agent": f"{intent}_AGENT",
                    "prompt": prompt_str,
                }
                
                target_api = "PUT /pms/v1/units/status" if intent == "PMS_OPERATIONS" else "POST /marketing/v1/campaigns/draft"
                mkt = session.get("session.target_market") or "NL"
                cls = session.get("session.target_cluster") or "MEDITERRANEAN_SOUTH"

                manifest = {
                    "target_api": target_api,
                    "target_market": mkt,
                    "identity_scope": f"CloudIdentity ({session.user_id or 'julien'})",
                }

                if intent == "PMS_OPERATIONS":
                    manifest["campsite_id"] = session.campsite_id or "LA_SIRENE_06"
                    manifest["unit_ids"] = session.unit_ids or ["MH-102", "MH-103", "MH-104", "MH-105"]
                else:
                    discount_val = 15
                    m_disc = re.search(r'(\d{1,3})\s*%', prompt_str)
                    if m_disc:
                        try:
                            d_parsed = int(m_disc.group(1))
                            if 0 <= d_parsed <= 100:
                                discount_val = d_parsed
                        except ValueError:
                            pass
                    manifest["campaign_name"] = f"Flash_Promo_{mkt}_{cls}_July"
                    manifest["target_segment_id"] = f"SEG_{mkt}_PAST_GUESTS_{cls}_2025"
                    manifest["discount_percentage"] = discount_val
                    manifest["cluster"] = cls

                hitl_card = {
                    "widget_type": "HITL_APPROVAL_CARD",
                    "status": "PENDING_CONFIRMATION",
                    "amber_border": "#f59e0b",
                    "manifest": manifest,
                    "actions": ["Approve", "Reject"],
                }

                return {
                    "status": "PENDING_CONFIRMATION",
                    "intent": intent,
                    "routed_agent": f"{intent}_AGENT",
                    "session_state": session.to_dict(),
                    "widget": hitl_card,
                    "message": "State-changing action requires explicit confirmation. Please inspect the HITL Approval Card and click Approve or Reject.",
                }

            # If confirmed, dispatch tool execution
            routed_agent_name = "PMS_OPERATIONS_AGENT" if intent == "PMS_OPERATIONS" else "MARKETING_CAMPAIGN_AGENT"
            logger.info("Confirmed turn! Routing to %s", routed_agent_name)
            
            if intent == "PMS_OPERATIONS":
                agent_inst = PMS_Operations_Agent()
            else:
                agent_inst = Marketing_Campaign_Agent()

            try:
                agent_result = agent_inst.process_turn(prompt_str, session)
            except Exception as e:
                logger.error("%s execution error: %s", routed_agent_name, str(e))
                return {
                    "status": "ERROR",
                    "intent": intent,
                    "routed_agent": routed_agent_name,
                    "session_state": session.to_dict(),
                    "message": f"{routed_agent_name} execution error: {str(e)}",
                }

            confirmed_card = {
                "widget_type": "HITL_APPROVAL_CARD",
                "status": "CONFIRMED",
                "status_color": "#10b981",
                "amber_border": "#10b981",
                "message": "Operation approved and executed successfully.",
            }

            logger.info("%s completed with status '%s'", routed_agent_name, agent_result.get("status"))
            conf_detail = agent_result.get("message", f"Routed to {routed_agent_name} with active session context.")
            full_msg = f"Parfait ! L'opération a été exécutée avec succès dans Resalys PMS / CRM. {conf_detail}"
            return {
                "status": agent_result.get("status", "SUCCESS"),
                "intent": intent,
                "routed_agent": routed_agent_name,
                "session_state": session.to_dict(),
                "agent_output": agent_result,
                "widget": confirmed_card,
                "message": full_msg,
            }

        logger.info("Default turn routing for intent '%s'", intent)
        return {
            "status": "SUCCESS",
            "intent": intent,
            "routed_agent": f"{intent}_AGENT" if intent != "UNKNOWN" else None,
            "session_state": session.to_dict(),
            "message": f"Routed to {intent} with active session context.",
        }
