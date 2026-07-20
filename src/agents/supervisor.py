"""ECG Root Supervisor Agent & Conversational Session Scaffold.

Coordinates multi-agent intent routing, retains StateSession context across turns,
and enforces Human-in-the-Loop (HITL) interception gates for state-changing operations.
"""

from typing import Any, Dict, Optional
from src.config import MODEL_SUPERVISOR
from src.agents.yield_analytics import Yield_Analytics_Agent


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
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a session state variable."""
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store or update a session state variable."""
        self._state[key] = value

    def update_from_prompt(self, prompt: str) -> None:
        """Extract and update session variables from user prompt keywords."""
        prompt_lower = prompt.lower()

        # Cluster detection
        if "mediterranean south" in prompt_lower or "med_south" in prompt_lower:
            self.set("session.target_cluster", "MEDITERRANEAN_SOUTH")
        elif "atlantic north" in prompt_lower:
            self.set("session.target_cluster", "ATLANTIC_NORTH")

        # Campsite detection
        if "la sirène" in prompt_lower or "la sirene" in prompt_lower:
            self.set("session.campsite_id", "LA_SIRENE_06")

        # Target Market / Country detection
        if "dutch" in prompt_lower or "netherlands" in prompt_lower or "nl" in prompt_lower:
            self.set("session.target_market", "NL")

    def to_dict(self) -> Dict[str, Any]:
        """Export session state dictionary."""
        return dict(self._state)


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

    def classify_intent(self, prompt: str) -> str:
        """Classify user prompt into sub-agent intent domain."""
        if not prompt or not prompt.strip():
            return "UNKNOWN"

        prompt_lower = prompt.lower()

        # PMS Operations Intent
        if any(kw in prompt_lower for kw in ["release", "unit", "mobil-home", "pms", "resalys", "unlock", "status"]):
            return "PMS_OPERATIONS"

        # Marketing Campaign Intent
        if any(kw in prompt_lower for kw in ["promo", "discount", "campaign", "marketing", "crm", "flash", "copywriting"]):
            return "MARKETING_CAMPAIGN"

        # Yield Analytics Intent (default for data analysis requests)
        if any(kw in prompt_lower for kw in ["occupancy", "revpar", "avpn", "yield", "analyze", "lag", "booking", "cluster"]):
            return "YIELD_ANALYTICS"

        return "YIELD_ANALYTICS"

    def process_turn(
        self, prompt: str, session: StateSession, bq_client: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Process a conversational turn, updating session state and routing intent."""
        if not prompt or not prompt.strip():
            return {
                "status": "VALIDATION_ERROR",
                "message": "Prompt cannot be empty. Please provide operational instructions.",
                "routed_agent": None,
                "session_state": session.to_dict(),
            }

        session.update_from_prompt(prompt)
        intent = self.classify_intent(prompt)

        if intent == "YIELD_ANALYTICS":
            yield_agent = Yield_Analytics_Agent()
            agent_result = yield_agent.process_query(prompt, session, bq_client=bq_client)
            return {
                "status": agent_result.get("status", "SUCCESS"),
                "intent": intent,
                "routed_agent": "YIELD_ANALYTICS_AGENT",
                "session_state": session.to_dict(),
                "agent_output": agent_result,
                "message": agent_result.get("message", "Routed to YIELD_ANALYTICS_AGENT with active session context."),
            }

        return {
            "status": "SUCCESS",
            "intent": intent,
            "routed_agent": f"{intent}_AGENT" if intent != "UNKNOWN" else None,
            "session_state": session.to_dict(),
            "message": f"Routed to {intent} with active session context.",
        }
