Voici la spécification d'implémentation technique basée sur le **Google Agent Development Kit (ADK)** pour le scénario **European Camping Group (ECG)**, structurée selon le framework **BMAD** (*BRIEF → MAP → ACT → DOUBLE-CHECK*).

---

# 📐 Spécification d'Implémentation ADK — Agents ECG (Format BMAD)

---

## 1. BRIEF (Business Context & Objectives)

* **Projet :** Déploiement d'agents autonomes Gemini Enterprise via l'Agent Development Kit (ADK).
* **Cas d'usage :** Décloisonnement des données Yield/Data [BigQuery](https://docs.google.com/document/d/1b_WUezeBv5-qHOSE3hl7cPu5FKIldgKFNyyOZqmAFIc/edit?usp=drivesdk&ouid=117878506396653388089) et automatisation des opérations PMS [Resalys](https://docs.google.com/document/d/1ML2onZbdy24nf6-t7nkp7XWZGjwilq2mDAaGL4KQDSE/edit?usp=drivesdk&ouid=117878506396653388089&resourcekey=0-ni9KbgZbgSYox7Jn64gXKg) / CRM Marketing.
* **Sponsors & Personas :**
* **Sponsor IT :** Amadou Baldé (Direction Système d'Information & Digital ECG).
* **Utilisateur final :** Responsable Yield & Operations Régional.


* **Valeur attendue :** Réduction du temps de réaction de l'analyse Yield à la mise en vente opérationnelle et l'activation marketing de minutes vs. jours.

---

## 2. MAP (Multi-Agent Mapping & Workflows)

### Pattern d'Architecture : **Supervisor Multi-Agent Pattern**

Un **Agent Superviseur** racine reçoit les requêtes utilisateur et orchestre 3 agents spécialisés (*Child Agents*).

```
                      ┌──────────────────────────────┐
                      │   ECG_Supervisor_Agent       │
                      │  (Root Orchestrator ADK)     │
                      └──────────────┬───────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│ Yield_Analytics_  │       │  PMS_Operations_  │       │ Marketing_Launch_ │
│       Agent       │       │       Agent       │       │       Agent       │
│  (Talk to Data)   │       │ (Resalys / Maintenance)│  │   (CRM & Assets)  │
└───────────────────┘       └───────────────────┘       └───────────────────┘

```

### Description des Agents

1. `ECG_Supervisor_Agent` : Reçoit le prompt, analyse l'intention, maintient l'état de la conversation (`StateSession`), délègue aux agents spécialisés et demande la confirmation de l'utilisateur pour les actions à impact (Human-in-the-Loop).
2. `Yield_Analytics_Agent` : Connecté à [BigQuery](https://docs.google.com/document/d/1b_WUezeBv5-qHOSE3hl7cPu5FKIldgKFNyyOZqmAFIc/edit?usp=drivesdk&ouid=117878506396653388089) via le moteur Natural Language to SQL (Data Agent ADK) pour calculer l'Occupancy Rate, l'AVPN et identifier les retards de réservation par nationalité/cluster.
3. `PMS_Operations_Agent` : Interagit via API Gateway (Apigee) avec l'API Maintenance et l'API PMS [Resalys](https://docs.google.com/document/d/1ML2onZbdy24nf6-t7nkp7XWZGjwilq2mDAaGL4KQDSE/edit?usp=drivesdk&ouid=117878506396653388089&resourcekey=0-ni9KbgZbgSYox7Jn64gXKg) pour vérifier l'état des mobil-homes et mettre à jour le stock disponible.
4. `Marketing_Campaign_Agent` : Génère les contenus (visuels via Imagen / textes) et prépare le brouillon de la campagne promo sur l'outil CRM.

---

## 3. ACT (Architecture, Tools & Implementation)

### Définition des Outillages ADK (`Tools`)

#### Tool 1 : `query_ecg_yield_data` (BigQuery Tool)

* **Description :** Exécute des requêtes SQL sécurisées sur le dataset `ecg_analytics`.
* **Input Schema :**
```json
{
  "cluster_name": "STRING",
  "period_start": "DATE",
  "period_end": "DATE",
  "metrics": ["OCCUPANCY_RATE", "AVPN", "REVPAR"],
  "group_by": ["ACCOMMODATION_TYPE", "CUSTOMER_COUNTRY"]
}

```



#### Tool 2 : `resalys_update_unit_inventory` (REST OpenAPI Tool via Apigee)

* **Endpoint :** `PUT [https://api.ecg.camp/pms/v1/units/status](https://api.ecg.camp/pms/v1/units/status)`
* **Headers :** `Authorization: Bearer {user_token}`
* **Request Body :**
```json
{
  "campsite_id": "LA_SIRENE_06",
  "unit_type": "PREMIUM_3_BEDROOMS",
  "unit_ids": ["MH-102", "MH-103", "MH-104", "MH-105"],
  "new_status": "AVAILABLE_FOR_SALE"
}

```



#### Tool 3 : `crm_create_flash_campaign` (CRM Webhook Tool)

* **Endpoint :** `POST [https://api.ecg.camp/marketing/v1/campaigns/draft](https://api.ecg.camp/marketing/v1/campaigns/draft)`
* **Request Body :**
```json
{
  "campaign_name": "Rattrapage_NL_Med_July",
  "target_segment_id": "SEG_NL_PAST_GUESTS_MED_2025",
  "discount_percentage": 15,
  "copywriting_text": "STRING",
  "image_asset_gcs_uri": "gs://ecg-marketing-assets/genai/promo_nl.png"
}

```



### Extrait de Code d'Implémentation ADK (Python)

```python
from google.genai.agent_development_kit import Agent, Tool, SupervisorAgent, Runner
from google.genai.agent_development_kit.tools import BigQueryTool, OpenAPITool

# 1. Agent Yield / Data (BigQuery)
yield_agent = Agent(
    name="Yield_Analytics_Agent",
    model="gemini-3.5-flash",
    instructions="""Tu es l'expert Yield & Data pour ECG.
    Interroge le dataset `ecg_analytics` sur BigQuery.
    Calcule l'Occupancy Rate et compare les volumes de réservation iso-jour de la semaine.""",
    tools=[BigQueryTool(dataset_id="ecg_analytics")]
)

# 2. Agent Operations / PMS (Resalys API)
pms_agent = Agent(
    name="PMS_Operations_Agent",
    model="gemini-3.5-flash",
    instructions="""Tu gères le système de réservation Resalys et les API de maintenance terrain.
    Vérifie les statuts d'intervention et remets à jour l'inventaire en vente.""",
    tools=[OpenAPITool.from_spec("https://api.ecg.camp/pms/openapi.json")]
)

# 3. Agent Marketing
marketing_agent = Agent(
    name="Marketing_Campaign_Agent",
    model="gemini-3.5-flash",
    instructions="Génère les messages promotionnels et prépare les brouillons de campagnes CRM.",
    tools=[OpenAPITool.from_spec("https://api.ecg.camp/marketing/openapi.json")]
)

# 4. Superviseur Racine
root_supervisor = SupervisorAgent(
    name="ECG_Supervisor_Agent",
    model="gemini-3.5-flash",
    sub_agents=[yield_agent, pms_agent, marketing_agent],
    instructions="""Tu es l'assistant exécutif d'ECG.
    Reçois la demande utilisateur, orchestre l'analyse de données, l'investigation PMS et la préparation marketing.
    IMPORTANT: Toute mise à jour de stock dans Resalys ou création de campagne doit faire l'objet d'une confirmation explicite à l'utilisateur."""
)

```

---

## 4. DOUBLE-CHECK (Governance, Security & Quality Gates)

### 🔒 Sécurité & IAM

* **Identity Passthrough :** L'agent réutilise le jeton Identity de l'utilisateur connecté via Google Workspace / Cloud Identity. Les droits d'accès [BigQuery](https://docs.google.com/document/d/1b_WUezeBv5-qHOSE3hl7cPu5FKIldgKFNyyOZqmAFIc/edit?usp=drivesdk&ouid=117878506396653388089) et [Resalys](https://docs.google.com/document/d/1ML2onZbdy24nf6-t7nkp7XWZGjwilq2mDAaGL4KQDSE/edit?usp=drivesdk&ouid=117878506396653388089&resourcekey=0-ni9KbgZbgSYox7Jn64gXKg) sont strictement identiques à ceux de l'humain.
* **Zéro Duplication de Données :** Les requêtes SQL s'exécutent au fil de l'eau sur le DWH sans copie temporaire.

### 🛑 Human-in-the-Loop (HITL) Gate

* Tout appel de fonction à impact d'écriture (`PUT`, `POST`, `DELETE`) bloque le runner ADK et émet une carte d'interaction demandant l'approbation explicite (`YES/NO`) avant l'exécution du callback.

### 📊 Observabilité & Télémétrie

* Traces complètes des raisonnements d'agents et des requêtes API enregistrées dans **Vertex AI Agent Observability** / **Cloud Logging**.
* Audit trail sur l'ensemble des requêtes SQL générées et exécutées.