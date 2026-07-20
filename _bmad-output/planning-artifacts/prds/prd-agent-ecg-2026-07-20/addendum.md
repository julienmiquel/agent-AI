# Technical Addendum: ECG Multi-Agent System Implementation Details

This addendum preserves technical specifications, API schemas, and reference code snippets supporting the **ECG Multi-Agent Yield & Operations System PRD**.

---

## 1. Tool Input/Output Schemas

### 1.1 Tool 1: `query_ecg_yield_data` (BigQuery Tool)
* **Type:** Data Agent ADK / BigQuery Native Tool
* **Target Dataset:** `ecg_analytics`
* **JSON Input Schema:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "cluster_name": {
      "type": "string",
      "description": "Name of the regional campsite cluster (e.g., 'MEDITERRANEAN_SOUTH')"
    },
    "period_start": {
      "type": "string",
      "format": "date",
      "description": "Start date for analysis window (YYYY-MM-DD)"
    },
    "period_end": {
      "type": "string",
      "format": "date",
      "description": "End date for analysis window (YYYY-MM-DD)"
    },
    "metrics": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["OCCUPANCY_RATE", "AVPN", "REVPAR"]
      },
      "description": "Metrics to calculate"
    },
    "group_by": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["ACCOMMODATION_TYPE", "CUSTOMER_COUNTRY"]
      },
      "description": "Dimensions for grouping"
    }
  },
  "required": ["cluster_name", "period_start", "period_end", "metrics"]
}
```

---

### 1.2 Tool 2: `resalys_update_unit_inventory` (REST OpenAPI Tool via Apigee)
* **Endpoint:** `PUT https://api.ecg.camp/pms/v1/units/status`
* **Headers:** `Authorization: Bearer {user_token}`
* **JSON Request Payload:**
```json
{
  "campsite_id": "LA_SIRENE_06",
  "unit_type": "PREMIUM_3_BEDROOMS",
  "unit_ids": ["MH-102", "MH-103", "MH-104", "MH-105"],
  "new_status": "AVAILABLE_FOR_SALE"
}
```

---

### 1.3 Tool 3: `crm_create_flash_campaign` (CRM Webhook Tool)
* **Endpoint:** `POST https://api.ecg.camp/marketing/v1/campaigns/draft`
* **JSON Request Payload:**
```json
{
  "campaign_name": "Rattrapage_NL_Med_July",
  "target_segment_id": "SEG_NL_PAST_GUESTS_MED_2025",
  "discount_percentage": 15,
  "copywriting_text": "Specially generated marketing copy targeting Dutch guests for July Mediterranean stays.",
  "image_asset_gcs_uri": "gs://ecg-marketing-assets/genai/promo_nl.png"
}
```

---

## 2. ADK Reference Implementation (Python)

```python
from google.genai.agent_development_kit import Agent, Tool, SupervisorAgent, Runner
from google.genai.agent_development_kit.tools import BigQueryTool, OpenAPITool

# 1. Yield / Data Agent (BigQuery NL-to-SQL)
yield_agent = Agent(
    name="Yield_Analytics_Agent",
    model="gemini-3.5-flash",
    instructions="""Tu es l'expert Yield & Data pour ECG.
    Interroge le dataset `ecg_analytics` sur BigQuery.
    Calcule l'Occupancy Rate, l'AVPN et le RevPAR et compare les volumes de réservation iso-jour de la semaine.""",
    tools=[BigQueryTool(dataset_id="ecg_analytics")]
)

# 2. Operations / PMS Agent (Resalys API via Apigee)
pms_agent = Agent(
    name="PMS_Operations_Agent",
    model="gemini-3.5-flash",
    instructions="""Tu gères le système de réservation Resalys et les API de maintenance terrain.
    Vérifie les statuts d'intervention et remets à jour l'inventaire en vente.""",
    tools=[OpenAPITool.from_spec("https://api.ecg.camp/pms/openapi.json")]
)

# 3. Marketing Agent (CRM & Asset Generation)
marketing_agent = Agent(
    name="Marketing_Campaign_Agent",
    model="gemini-3.5-flash",
    instructions="Génère les messages promotionnels et prépare les brouillons de campagnes CRM.",
    tools=[OpenAPITool.from_spec("https://api.ecg.camp/marketing/openapi.json")]
)

# 4. Root Supervisor Agent
root_supervisor = SupervisorAgent(
    name="ECG_Supervisor_Agent",
    model="gemini-3.5-flash",
    sub_agents=[yield_agent, pms_agent, marketing_agent],
    instructions="""Tu es l'assistant exécutif d'ECG.
    Reçois la demande utilisateur, orchestre l'analyse de données, l'investigation PMS et la préparation marketing.
    IMPORTANT: Toute mise à jour de stock dans Resalys ou création de campagne doit faire l'objet d'une confirmation explicite à l'utilisateur (Human-in-the-Loop)."""
)
```
