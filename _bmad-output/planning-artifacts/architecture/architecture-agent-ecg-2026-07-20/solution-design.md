# Solution Design Document: ECG Multi-Agent Yield & Operations System

**Version:** 1.0.0  
**Date:** 2026-07-20  
**Author:** AI Systems Architecture Team  
**Target Audience:** DSI / Enterprise IT, Lead Developers, Yield Operations Team  

---

## 1. Executive Summary & Business Context

Holiday company operates over 300 outdoor holiday resorts across Europe. Managing yield (occupancy rate, average value per night, RevPAR) requires constant monitoring of booking trends, physical accommodation readiness, and rapid marketing activation.

Currently, data silos between the BigQuery Data Warehouse, the Resalys Property Management System (PMS), and CRM marketing tools lead to a 24–48 hour lag between identifying an underperforming campsite cluster and launching a recovery promotion.

The **ECG Multi-Agent Yield & Operations System** leverages Google's **Agent Development Kit (ADK)** and **Gemini Enterprise models** to unify these domains into an interactive natural language assistant. By deploying a **Supervisor Multi-Agent Pattern**, the system empowers yield managers to query real-time analytics, release mobil-home stock, and stage targeted flash marketing campaigns in under 5 minutes, backed by strict **Human-in-the-Loop (HITL)** governance and **Identity Passthrough** security.

---

## 2. System Architecture & C4 Views

### 2.1 C4 System Context View

```mermaid
C4Context
    title C4 System Context — ECG Multi-Agent Yield & Operations System

    Person(user, "Yield & Operations Manager", "Regional business operator analyzing yield and managing campsite stock.")
    
    System(adk_system, "ECG Multi-Agent System", "ADK Supervisor & Child Agents handling natural language queries, inventory updates, and campaign drafting.")

    System_Ext(bigquery, "BigQuery DWH", "Stores raw and aggregated booking analytics in ecg_analytics dataset.")
    System_Ext(apigee, "Apigee API Gateway", "Manages REST endpoints for Resalys PMS and maintenance services.")
    System_Ext(crm, "CRM Marketing Tool", "Stages and executes targeted promotional marketing campaigns.")
    System_Ext(cloud_identity, "Google Cloud Identity", "Provides SSO authentication and user OAuth tokens.")
    System_Ext(vertex_obs, "Vertex AI Observability", "Logs distributed traces, reasoning chains, and SQL queries.")

    Rel(user, adk_system, "Interacts via Gemini Enterprise App Chat UI", "HTTPS / WebSockets / Extension Cards")
    Rel(user, cloud_identity, "Authenticates SSO", "OAuth2 / OIDC")
    Rel(adk_system, bigquery, "Executes Text-to-SQL", "BigQuery API (User IAM)")
    Rel(adk_system, apigee, "Invokes PMS Status REST API", "HTTPS / Bearer Token")
    Rel(adk_system, crm, "Posts Draft Campaign Webhook", "HTTPS / JSON Payload")
    Rel(adk_system, vertex_obs, "Streams Reasoning Traces & Audit Logs", "gRPC / Cloud Logging")
```

> **Note on UI Host Container:** The conversational UI runs natively inside the **Gemini Enterprise Application** (Discovery Engine / Agent Builder). The system leverages custom Extension Cards and Structured Action Cards for HITL approvals embedded within the Gemini chat stream.

---

## 3. Multi-Agent Component Design

The system consists of one **Root Supervisor Agent** and three **Domain Child Agents**:

```mermaid
graph TD
    subgraph Client_Layer [Client & Security Layer]
        UI[Chat Interface / Web App]
        Auth[Cloud Identity Token Provider]
    end

    subgraph Supervisor_Layer [Root Supervisor Layer]
        Supervisor[ECG_Supervisor_Agent\nModel: Gemini 3.5 Flash]
        State[ADK StateSession]
        HITL[HITL Interceptor Card]
    end

    subgraph Child_Agent_Layer [Specialized Domain Agents]
        YieldAgent[Yield_Analytics_Agent\nModel: Gemini 3.5 Flash]
        PMSAgent[PMS_Operations_Agent\nModel: Gemini 3.5 Flash]
        MktgAgent[Marketing_Campaign_Agent\nModel: Gemini 3.5 Flash]
    end

    subgraph External_Integrations [External APIs & Datastores]
        BQ[(BigQuery: ecg_analytics)]
        Apigee[Apigee API Gateway]
        Resalys[Resalys PMS]
        GCS[Google Cloud Storage Assets]
        CRM[CRM Webhook Endpoint]
    end

    UI -->|Prompt + Bearer Token| Supervisor
    Supervisor -->|Maintain Session| State
    Supervisor -->|Intercept Mutations| HITL
    HITL -->|Approved Action| YieldAgent
    HITL -->|Approved Action| PMSAgent
    HITL -->|Approved Action| MktgAgent

    YieldAgent -->|SQL Execution| BQ
    PMSAgent -->|PUT /pms/v1/units/status| Apigee
    Apigee --> Resalys
    MktgAgent -->|Store Generated Images| GCS
    MktgAgent -->|POST /marketing/v1/campaigns/draft| CRM
```

### 3.1 Agent Responsibilities

1. **`ECG_Supervisor_Agent`**:
   - Parses intent and extracts context (campsite ID, date ranges, target segments).
   - Manages session memory in `StateSession`.
   - Intercepts mutating actions (`PUT`, `POST`, `DELETE`) with an interactive HITL card.
   - Delegates sub-tasks to child agents.

2. **`Yield_Analytics_Agent`**:
   - Equips `BigQueryTool` targeting dataset `ecg_analytics`.
   - Translates natural language questions into valid, optimized BigQuery SQL.
   - Computes Occupancy Rate, AVPN, and RevPAR; compares metrics against prior period iso-days.

3. **`PMS_Operations_Agent`**:
   - Equips `OpenAPITool` pointing to Apigee Resalys OpenAPI spec (`pms_openapi.json`).
   - Checks mobil-home maintenance/readiness status.
   - Updates stock status (`PUT /pms/v1/units/status`) to `AVAILABLE_FOR_SALE`.

4. **`Marketing_Campaign_Agent`**:
   - Generates promotional text and visual assets via Imagen 3 (saved to GCS).
   - Stages draft flash campaigns in the CRM (`POST /marketing/v1/campaigns/draft`).

---

## 4. End-to-End Sequence Diagram (Yield-to-Market Workflow)

```mermaid
sequenceDiagram
    autonumber
    actor Manager as Yield Manager (Marc)
    participant UI as Chat UI
    participant Sup as ECG_Supervisor_Agent
    participant Yield as Yield_Analytics_Agent
    participant BQ as BigQuery DWH
    participant PMS as PMS_Operations_Agent
    participant Apigee as Apigee Gateway
    participant Mktg as Marketing_Campaign_Agent
    participant CRM as CRM Webhook

    Manager->>UI: "Analyze July occupancy for Mediterranean South cluster"
    UI->>Sup: Send prompt + OAuth Identity Token
    Sup->>Yield: Delegate Yield query task
    Yield->>BQ: Execute NL-to-SQL (Occupancy, AVPN, RevPAR)
    BQ-->>Yield: SQL Result (Occupancy 72%, Dutch lag 15%, 4 units held at La Sirène)
    Yield-->>Sup: Summarized Yield Report
    Sup-->>UI: Display Yield Report & lag breakdown

    Manager->>UI: "Release mobil-homes MH-102 to MH-105 at La Sirène to sale"
    UI->>Sup: Send inventory unlock instruction
    Sup->>Sup: Intercept mutating PUT request (HITL Gate)
    Sup-->>UI: Render HITL Approval Card (Campsite: LA_SIRENE_06, Units: MH-102..105)
    Manager->>UI: Click "Approve"
    UI->>Sup: Confirmation event (YES)
    Sup->>PMS: Delegate inventory status update
    PMS->>Apigee: PUT /pms/v1/units/status (Authorization: Bearer Token)
    Apigee-->>PMS: 200 OK (Status: AVAILABLE_FOR_SALE)
    PMS-->>Sup: Inventory update confirmed
    Sup-->>UI: Display PMS Inventory Updated Card

    Manager->>UI: "Create a 15% promo draft for Dutch past guests"
    UI->>Sup: Send campaign creation request
    Sup->>Mktg: Delegate campaign draft staging
    Mktg->>Mktg: Generate copy & Imagen visual asset
    Mktg->>Sup: Intercept mutating POST request (HITL Gate)
    Sup-->>UI: Render HITL Approval Card (Segment: Dutch Guests, Discount: 15%)
    Manager->>UI: Click "Approve"
    UI->>Sup: Confirmation event (YES)
    Sup->>Mktg: Execute draft staging
    Mktg->>CRM: POST /marketing/v1/campaigns/draft
    CRM-->>Mktg: 201 Created (Campaign ID: Rattrapage_NL_Med_July)
    Mktg-->>Sup: Draft campaign staged
    Sup-->>UI: Display Campaign Staged Confirmation (Total time: < 4 mins)
```

---

## 5. Security, Identity & Governance

### 5.1 Identity Passthrough Model
- **No Service Account Escalation:** The ADK runner does not use a super-user service account. Instead, it extracts the `Authorization: Bearer {user_token}` from the incoming HTTP request.
- **BigQuery Access Control:** Queries run under the authenticated user's BigQuery IAM role (`roles/bigquery.dataViewer` or specific dataset grants).
- **Apigee API Authorization:** Apigee validates the bearer token against Cloud Identity scopes (`pms.inventory.write`, `marketing.campaign.write`).

### 5.2 Human-in-the-Loop (HITL) Enforcement Card
- All mutating calls (`PUT`, `POST`, `PATCH`, `DELETE`) trigger an ADK tool callback pause.
- The UI displays an immutable action manifest (Target System, Endpoint, Payload, User Identity).
- If the user clicks `Reject` or the token expires, the transaction is immediately rolled back without execution.

---

## 6. Observability, Telemetry & Operational SLA

### 6.1 Telemetry Metrics & Logs
- **Distributed Traces:** OpenTelemetry traces capturing latency breakdown across Supervisor delegation, sub-agent execution, SQL queries, and REST calls.
- **Audit Logs:** Full prompt/response pairs, generated SQL queries, and HITL approval timestamps recorded in Cloud Logging under `ecg-agent-audit-log`.

### 6.2 Service Level Agreements (SLAs)
- **Yield Query Latency:** < 3.5 seconds (BigQuery query execution + NL translation).
- **PMS Status Update Latency:** < 1.2 seconds via Apigee.
- **End-to-End Workflow Completion:** < 5 minutes total human + agent cycle time.
