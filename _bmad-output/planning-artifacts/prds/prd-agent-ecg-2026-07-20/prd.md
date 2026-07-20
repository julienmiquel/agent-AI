---
title: 'ECG Multi-Agent Yield & Operations System PRD'
status: 'final'
created: '2026-07-20'
updated: '2026-07-20'
---

# PRD: ECG Multi-Agent Yield & Operations System

## 0. Document Purpose

This Product Requirement Document (PRD) defines the operational, functional, and governance requirements for the European Camping Group (ECG) Multi-Agent System built on the Google Agent Development Kit (ADK). It bridges business strategy, IT architecture, and downstream agent development by specifying intent routing, natural language data analysis, property management system (PMS) inventory unlocking, and marketing campaign automation. Technical payload schemas, REST API specs, and reference Python implementation code are preserved in [addendum.md](file:///Users/julienmiquel/dev/agent-ecg/_bmad-output/planning-artifacts/prds/prd-agent-ecg-2026-07-20/addendum.md).

## 1. Vision

The ECG Multi-Agent Yield & Operations System transforms campsite yield management by eliminating data silos between data warehouse analytics, property management operations, and marketing activation channels. Today, identifying a lagging booking trend, verifying physical mobil-home readiness, releasing stock to sale, and launching targeted promotional campaigns requires manual coordination across separate teams over multiple days.

By deploying an autonomous Gemini Enterprise multi-agent network coordinated by a Supervisor Agent, ECG enables regional managers to perform complex cross-domain workflows in minutes through natural language interactions. The system empowers business operators with instantaneous insights while enforcing strict enterprise security, zero data duplication, and explicit Human-in-the-Loop approval gates for all state-changing actions.

## 2. Target User

### 2.1 Sponsors & Personas

- **IT Sponsor:** Amadou Baldé (Direction Système d'Information & Digital, ECG) — requires secure, scalable agent architecture complying with Cloud Identity passthrough and API governance standards.
- **Primary Business Operator:** Regional Yield & Operations Manager (e.g., Marc) — responsible for occupancy optimization, RevPAR targets, and inventory availability across assigned campsite clusters.

### 2.2 Key User Journeys

- **UJ-1. Marc detects an occupancy deficit and analyzes booking lags by nationality.**
  - **Persona + context:** Marc, Regional Yield Manager for Mediterranean campsite clusters, checking weekly performance.
  - **Entry state:** Authenticated via Google Workspace single sign-on on the agent chat interface.
  - **Path:** Marc asks the agent to analyze July occupancy for the Mediterranean South cluster. The `ECG_Supervisor_Agent` delegates to `Yield_Analytics_Agent`, which queries BigQuery via natural language SQL to calculate Occupancy Rate, AVPN, and RevPAR broken down by customer country. The report reveals a 15% lag in Dutch guest bookings.
  - **Climax:** Marc receives an instant breakdown showing 4 unreleased premium mobil-homes at *La Sirène* and an underperforming Dutch market segment.
  - **Resolution:** Marc decides to unlock the inventory and trigger a targeted Dutch flash promotion.

- **UJ-2. Marc unlocks held-back mobil-home inventory with HITL confirmation.**
  - **Persona + context:** Marc, acting on the yield insight from UJ-1 to increase available sales stock.
  - **Entry state:** Continuing active chat session in the agent interface (`StateSession` active).
  - **Path:** Marc instructs the agent to set mobil-homes MH-102 through MH-105 at *La Sirène* to available status in Resalys. The `ECG_Supervisor_Agent` delegates to `PMS_Operations_Agent`. The agent prepares the API request and triggers an interactive HITL approval card showing exact campsite ID, unit IDs, and target status `AVAILABLE_FOR_SALE`. Marc clicks **Approve**.
  - **Climax:** The agent executes the `PUT` request via Apigee API Gateway using Marc's user token and returns a confirmation card.
  - **Resolution:** Resalys inventory is live for sale within seconds.

- **UJ-3. Marc generates and stages a marketing flash campaign for Dutch guests.**
  - **Persona + context:** Marc, completing the commercial recovery loop for Dutch bookings.
  - **Entry state:** Active session post-inventory unlock.
  - **Path:** Marc asks the agent to draft a 15% discount promo campaign for Dutch past guests. `ECG_Supervisor_Agent` delegates to `Marketing_Campaign_Agent`, which generates Dutch copywriting text and an asset visual (via Imagen stored in GCS), then stages a draft campaign. Marc approves the staged campaign through a second HITL confirmation card.
  - **Climax:** The webhook executes `POST /marketing/v1/campaigns/draft` and returns campaign ID `Rattrapage_NL_Med_July`.
  - **Resolution:** Marketing team receives the ready-to-send draft in the CRM, completing the yield-to-market cycle in under 5 minutes.

## 3. Glossary

- **ADK (Agent Development Kit):** Google's framework for orchestrating Gemini agents, sub-agents, tools, and multi-agent workflows.
- **Root Supervisor (`ECG_Supervisor_Agent`):** Top-level ADK orchestrator agent responsible for user intent classification, session state management (`StateSession`), delegation, and HITL gate enforcement.
- **Yield Analytics Agent (`Yield_Analytics_Agent`):** Specialized child agent executing text-to-SQL queries on BigQuery dataset `ecg_analytics`.
- **PMS Operations Agent (`PMS_Operations_Agent`):** Specialized child agent interfacing with Resalys PMS and maintenance APIs via Apigee REST endpoints.
- **Marketing Campaign Agent (`Marketing_Campaign_Agent`):** Specialized child agent generating promotional copy, visual assets, and staging CRM campaign webhooks.
- **Resalys:** ECG's core Property Management System (PMS) managing mobil-home inventory and booking availability.
- **Apigee:** Enterprise API Gateway managing authentication, rate limiting, and REST tool routing for ECG backend APIs.
- **HITL (Human-in-the-Loop):** Governance mechanism blocking write/impact execution until an interactive user confirmation (`YES/NO`) is granted.
- **AVPN:** Average Value Per Night metric across booked accommodations.
- **RevPAR:** Revenue Per Available Room (or available unit) performance metric.
- **Occupancy Rate:** Percentage of total available mobil-home units booked over a specified window.

## 4. Features & Functional Requirements

### 4.1 Supervisor Orchestration & Intent Routing

**Description:** The `ECG_Supervisor_Agent` acts as the single conversational entry point. It parses incoming user requests, maintains context across multi-turn sessions using `StateSession`, delegates tasks to specialized child agents, and intercepts mutating operations with HITL confirmation cards. Realizes UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-1: Intent Classification & Routing
The `ECG_Supervisor_Agent` must classify user input and route sub-tasks to `Yield_Analytics_Agent`, `PMS_Operations_Agent`, or `Marketing_Campaign_Agent` based on domain semantics. Realizes UJ-1.
**Consequences (testable):**
- Requests regarding occupancy, revenue, or BigQuery metrics route to `Yield_Analytics_Agent`.
- Requests regarding mobil-home status, Resalys inventory, or maintenance route to `PMS_Operations_Agent`.
- Requests regarding promotions, copy generation, or CRM drafts route to `Marketing_Campaign_Agent`.

#### FR-2: Conversational Session State Retention
The system must persist multi-turn conversational context in `StateSession` across agent handoffs so user context (e.g., selected campsite, unit IDs, target country) is preserved without re-prompting. Realizes UJ-2, UJ-3.
**Consequences (testable):**
- Context set in a Yield query (e.g., campsite *La Sirène*) is automatically inherited by subsequent PMS or Marketing commands in the same session.

#### FR-3: Human-in-the-Loop (HITL) Interception Card
The `ECG_Supervisor_Agent` must intercept all state-changing API operations (`PUT`, `POST`, `DELETE`) before tool execution, rendering an interactive approval card displaying action details and requiring explicit user authorization. Realizes UJ-2, UJ-3.
**Consequences (testable):**
- Tool callbacks for `resalys_update_unit_inventory` or `crm_create_flash_campaign` pause until the user clicks `Approve`. Clicking `Reject` aborts tool execution with zero backend mutation.

---

### 4.2 Natural Language Yield Analytics

**Description:** Provides natural language query capabilities over the `ecg_analytics` BigQuery dataset, converting user questions into optimized SQL queries to return performance metrics and operational bottlenecks. Realizes UJ-1.

**Functional Requirements:**

#### FR-4: Text-to-SQL Query Generation (`query_ecg_yield_data`)
The `Yield_Analytics_Agent` must accept natural language parameter requests and execute parameterized BigQuery queries targeting dataset `ecg_analytics`. Realizes UJ-1.
**Consequences (testable):**
- Validates queries return Occupancy Rate, AVPN, and RevPAR grouped by `ACCOMMODATION_TYPE` or `CUSTOMER_COUNTRY`.
- Query execution runs directly on BigQuery DWH with zero local data caching or duplication.

#### FR-5: Multi-Period & Cluster Comparison
The `Yield_Analytics_Agent` must support comparative analysis across date ranges (iso-day of week) and regional campsite clusters. Realizes UJ-1.
**Consequences (testable):**
- Prompting for "Dutch booking lag in Mediterranean South vs last year" returns comparative variance metrics.

---

### 4.3 PMS Inventory & Operations Automation

**Description:** Interacts with Resalys PMS and maintenance APIs via Apigee API Gateway to inspect mobil-home status and update availability stock. Realizes UJ-2.

**Functional Requirements:**

#### FR-6: Unit Inventory Status Update (`resalys_update_unit_inventory`)
The `PMS_Operations_Agent` must format and submit REST payload requests to `PUT /pms/v1/units/status` via Apigee to update designated mobil-home status to `AVAILABLE_FOR_SALE`. Realizes UJ-2.
**Consequences (testable):**
- Payload must include `campsite_id`, `unit_type`, `unit_ids`, and `new_status`. Successful execution updates Resalys stock state immediately.

#### FR-7: Identity Passthrough Authorization
The `PMS_Operations_Agent` must forward the user's Cloud Identity OAuth bearer token in the `Authorization` header for all Apigee REST tool invocations [ASSUMPTION: Apigee enforces OAuth2 Bearer token validation matching user IAM scope]. Realizes UJ-2.
**Consequences (testable):**
- Unauthenticated or unauthorized user tokens result in HTTP 401/403 responses gracefully handled by the agent.

---

### 4.4 Marketing Campaign Generation & Draft Staging

**Description:** Generates localized promotional copywriting, resolves visual marketing assets via Imagen/GCS, and creates draft campaign records in the CRM system. Realizes UJ-3.

**Functional Requirements:**

#### FR-8: CRM Flash Campaign Staging (`crm_create_flash_campaign`)
The `Marketing_Campaign_Agent` must construct and dispatch webhook payloads to `POST /marketing/v1/campaigns/draft` containing target segment ID, discount percentage, generated copywriting, and asset GCS URI. Realizes UJ-3.
**Consequences (testable):**
- Successful call returns draft campaign ID (e.g., `Rattrapage_NL_Med_July`) and stages campaign for final review in the CRM portal.

---

## 5. Non-Goals (Explicit)

- **No Direct Database Writes:** The system will not perform direct SQL `INSERT`, `UPDATE`, or `DELETE` statements against BigQuery or transactional databases; all mutations occur strictly via validated API endpoints.
- **No Fully Autonomous Mutating Execution:** The system will not execute state-changing actions (`PUT`, `POST`, `DELETE`) without real-time human approval (HITL).
- **No Data Replication or Local Caching:** The system will not maintain external data replicas or shadow databases; all analytics queries run live against the BigQuery DWH.
- **No Direct Customer Broadcasts:** The system will not send emails or SMS messages directly to customers; campaigns are staged as *drafts* in the CRM for final marketing sign-off.

---

## 6. MVP Scope

### 6.1 In Scope for MVP
- `ECG_Supervisor_Agent` root orchestration with 3 sub-agents (`Yield_Analytics_Agent`, `PMS_Operations_Agent`, `Marketing_Campaign_Agent`).
- Natural language to SQL query execution on `ecg_analytics` BigQuery dataset.
- Resalys mobil-home inventory status update via Apigee REST API (`PUT /pms/v1/units/status`).
- CRM flash campaign draft creation (`POST /marketing/v1/campaigns/draft`).
- Interactive HITL approval card interception for all write/mutation requests.
- Identity passthrough using Google Workspace / Cloud Identity tokens.
- Observability and audit logging in Cloud Logging and Vertex AI Agent Observability.

### 6.2 Out of Scope for MVP
- Automated customer dynamic pricing algorithm adjustments (deferred to v2).
- Direct integration with maintenance IoT sensors or physical smart lock APIs (deferred to v2).
- Multi-language voice interface (v1 is text-based chat interface only).

---

## 7. Success Metrics

### 7.1 Primary Metrics
- **SM-1 (Workflow Cycle Time):** Reduce end-to-end execution time from Yield detection to inventory release and campaign staging from >24 hours to <5 minutes. Validates FR-1 through FR-8.
- **SM-2 (Text-to-SQL Query Accuracy):** Achieve >95% correct SQL query syntax and metric retrieval accuracy on `ecg_analytics`. Validates FR-4, FR-5.

### 7.2 Secondary Metrics
- **SM-3 (Operational Stock Release):** Percentage of underperforming mobil-homes successfully identified and released to sale within 1 hour of maintenance clearance. Validates FR-6.

### 7.3 Counter-Metrics (Do Not Optimize)
- **SM-C1 (Zero Unapproved Mutations):** 100% of write/mutation operations must pass through HITL confirmation. Target: 0 bypasses or unapproved API calls. Counterbalances workflow speed optimization in SM-1.

---

## 8. Enterprise Adapt-In Sections

### 8.1 Integration & Dependencies
- **BigQuery DWH:** Target dataset `ecg_analytics` accessed via ADK `BigQueryTool`.
- **Apigee API Gateway:** Entry point for Resalys PMS REST services (`https://api.ecg.camp/pms/v1`).
- **CRM Webhook Gateway:** Staging endpoint for marketing campaigns (`https://api.ecg.camp/marketing/v1`).
- **Google Cloud Storage (GCS):** Storage bucket `gs://ecg-marketing-assets/genai/` for Imagen generated promotional assets.

### 8.2 Security, IAM & Governance
- **Identity Passthrough:** User OAuth2 token is passed end-to-end from Google Cloud Identity through ADK runners to BigQuery and Apigee.
- **Least Privilege Access:** Agent capabilities strictly inherit the authenticated human user's IAM permissions; no elevated service account privilege escalation.
- **Zero Data Duplication:** Analytical queries run on DWH live without temporary tables or local data dumps.

### 8.3 Human-in-the-Loop (HITL) Gate
- Every REST tool carrying HTTP methods `PUT`, `POST`, `PATCH`, or `DELETE` triggers a pause state in the ADK runner.
- Approval payload requires explicit `YES/NO` interaction with clear parameter summaries before backend callback execution.

### 8.4 Observability, Telemetry & Audit Trail
- **Trace Logging:** Full chain of thought, intent classification, sub-agent delegation, and tool invocations recorded in **Vertex AI Agent Observability** and **Cloud Logging**.
- **SQL Audit:** Every generated SQL query and its execution metadata logged with user ID timestamping for compliance auditing.

---

## 9. Open Questions

1. **[OPEN ITEM - Engineering]:** Confirm exact Apigee OAuth token expiration and refresh token handling behavior during long multi-turn agent sessions.
2. **[OPEN ITEM - Product]:** Define whether campaign draft notifications should alert the marketing team via Slack/Teams webhook in addition to CRM draft creation.

---

## 10. Assumptions Index

- **[ASSUMPTION - §4.3 (FR-7)]**: Apigee API Gateway enforces standard OAuth2 Bearer token validation matching Cloud Identity user IAM scopes.
- **[ASSUMPTION - §8.1]**: The BigQuery `ecg_analytics` dataset contains schema fields `ACCOMMODATION_TYPE`, `CUSTOMER_COUNTRY`, `OCCUPANCY_RATE`, `AVPN`, and `REVPAR`.
