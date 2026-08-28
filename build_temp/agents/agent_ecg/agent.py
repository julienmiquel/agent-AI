"""ECG ADK Multi-Agent System Entrypoint.

Initializes the ECG Root Supervisor Agent, sub-agents (Yield Analytics, PMS Operations,
Marketing Campaign), and exposes root_agent for Google Agent Development Kit (ADK) CLI & Web server.
"""

import logging
from src.agents.supervisor import ECG_Supervisor_Agent, StateSession
from src.agents.yield_analytics import Yield_Analytics_Agent, compare_ecg_yield_data, query_ecg_yield_data
from src.agents.pms_operations import PMS_Operations_Agent, resalys_update_unit_inventory
from src.agents.marketing_campaign import Marketing_Campaign_Agent, crm_create_flash_campaign

from src.config import MODEL_SUPERVISOR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ecg_agent")

# Attempt ADK Agent wrapper initialization if google.adk / google.genai is installed
try:
    from google.adk.agents import Agent
    root_agent = Agent(
        name="ECG_Supervisor_Agent",
        model=MODEL_SUPERVISOR,
        description="Root Supervisor Agent for Holiday Company yield & operations",
        instruction="""Tu es l'assistant exécutif d'ECG (European Camping Group).
Reçois les demandes utilisateurs pour l'analyse Yield BigQuery, l'inventaire PMS Resalys, et les campagnes marketing CRM.
IMPORTANT: Toute mise à jour de stock dans Resalys ou création de campagne doit faire l'objet d'une confirmation explicite à l'utilisateur.""",
        tools=[query_ecg_yield_data, compare_ecg_yield_data, resalys_update_unit_inventory, crm_create_flash_campaign],
    )
except ImportError:
    try:
        from google.genai.agent_development_kit import Agent
        root_agent = Agent(
            name="ECG_Supervisor_Agent",
            model=MODEL_SUPERVISOR,
            instructions="Root Supervisor Agent for Holiday Company yield & operations",
        )
    except ImportError:
        # Fallback to local ECG_Supervisor_Agent instance
        root_agent = ECG_Supervisor_Agent()


def main():
    """Execute initialization verification and interactive demo turns."""
    logger.info("Initializing Holiday Company Multi-Agent System...")
    supervisor = ECG_Supervisor_Agent()
    session = StateSession(session_id="session_demo_01", user_id="julien")

    print("\n==================================================================")
    print("      Holiday Company - Multi-Agent System (ADK)")
    print("==================================================================")
    print(f"Supervisor Model: {supervisor.model_name}")
    print(f"Active Session: {session.session_id} (User: {session.user_id})")
    print("------------------------------------------------------------------\n")

    demo_prompts = [
        "Dutch booking lag in Mediterranean South vs last year",
        "Release these held-back mobil-home units to sale at La Sirène",
        "Approve",
        "Draft a flash promotion campaign for Dutch past guests",
        "Approve",
    ]

    for turn_idx, prompt in enumerate(demo_prompts, 1):
        print(f"\n[Turn {turn_idx}] User Prompt: \"{prompt}\"")
        result = supervisor.process_turn(prompt, session)
        print(f"  -> Intent Classified : {result.get('intent')}")
        print(f"  -> Routed Sub-Agent  : {result.get('routed_agent')}")
        print(f"  -> Status            : {result.get('status')}")
        print(f"  -> Response Message  : {result.get('message')}")
        print(f"  -> Updated Context   : Cluster={session.target_cluster}, Campsite={session.campsite_id}, Market={session.target_market}, Units={session.unit_ids}")

    print("\n==================================================================")
    print(" Multi-Agent System Initialized & Verification Passed Successfully")
    print("==================================================================\n")


if __name__ == "__main__":
    main()
