---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments:
  - '_bmad-output/planning-artifacts/prds/prd-agent-ecg-2026-07-20/prd.md'
  - '_bmad-output/planning-artifacts/prds/prd-agent-ecg-2026-07-20/addendum.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-agent-ecg-2026-07-20/ARCHITECTURE-SPINE.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-agent-ecg-2026-07-20/solution-design.md'
  - '_bmad-output/planning-artifacts/ux-designs/ux-agent-ecg-2026-07-20/DESIGN.md'
  - '_bmad-output/planning-artifacts/ux-designs/ux-agent-ecg-2026-07-20/EXPERIENCE.md'
---

# agent-ecg - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for agent-ecg, decomposing the requirements from the PRD, UX Design specification, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

- **FR-1:** Intent Classification & Routing (`ECG_Supervisor_Agent` routes user input to `Yield_Analytics_Agent`, `PMS_Operations_Agent`, or `Marketing_Campaign_Agent` based on domain semantics).
- **FR-2:** Conversational Session State Retention (`StateSession` persists context like campsite name, unit IDs, and target market across multi-turn handoffs).
- **FR-3:** Human-in-the-Loop (HITL) Interception Card (`ECG_Supervisor_Agent` intercepts state-changing API calls (`PUT`, `POST`, `DELETE`) before tool execution, requiring explicit user authorization).
- **FR-4:** Text-to-SQL Query Generation (`query_ecg_yield_data` tool on `Yield_Analytics_Agent` executes parameterized queries on BigQuery dataset `ecg_analytics`).
- **FR-5:** Multi-Period & Cluster Comparison (`Yield_Analytics_Agent` supports comparative analysis across date ranges and regional campsite clusters).
- **FR-6:** Unit Inventory Status Update (`resalys_update_unit_inventory` tool on `PMS_Operations_Agent` dispatches `PUT /pms/v1/units/status` via Apigee Gateway).
- **FR-7:** Identity Passthrough Authorization (`PMS_Operations_Agent` forwards user Cloud Identity OAuth bearer token in `Authorization` header for Apigee API calls).
- **FR-8:** CRM Flash Campaign Staging (`crm_create_flash_campaign` tool on `Marketing_Campaign_Agent` dispatches `POST /marketing/v1/campaigns/draft`).

### NonFunctional Requirements

- **NFR-1 (Performance / Cycle Time):** End-to-end execution time from Yield detection to stock release and campaign staging <5 minutes (SM-1).
- **NFR-2 (Accuracy / Reliability):** Text-to-SQL query syntax and metric accuracy on `ecg_analytics` >95% (SM-2).
- **NFR-3 (Security / Identity Passthrough):** User OAuth2 bearer token passed end-to-end from Google Cloud Identity through ADK runners to BigQuery and Apigee without service account elevation (§8.2, FR-7).
- **NFR-4 (Data Architecture / Zero Duplication):** Zero data duplication; analytical queries run live on BigQuery DWH without local data caching or temporary table dumps (§8.2, §5).
- **NFR-5 (Governance / HITL Security):** 100% of write/mutation operations (`PUT`, `POST`, `DELETE`) must pass through HITL confirmation card interception before backend tool execution (SM-C1, §8.3, FR-3).
- **NFR-6 (Observability & Auditability):** Full chain of thought, intent classification, sub-agent delegation, tool invocations, and generated SQL queries with user ID timestamping recorded in Vertex AI Agent Observability and Cloud Logging (§8.4).

### Additional Requirements

- **Greenfield ADK Project Architecture:** Initial repository scaffold based on Google Agent Development Kit (`google.genai.agent_development_kit`), Python 3.10+, using `gemini-2.5-pro` for root supervisor and `gemini-3.6-flash` / `gemini-2.5-flash` for high-throughput sub-agents.
- **Mocking & Integration Contracts:** Local dev & unit/eval testing must intercept all Apigee REST calls (`api.ecg.camp/pms` and `api.ecg.camp/marketing`) using OpenAPI stubs (`httpx_mock` / `responses`) to prevent unintended backend mutations.
- **Storage Bucket Integration:** Promotional image assets generated via Imagen stored in GCS bucket `gs://ecg-marketing-assets/genai/`.

### UX Design Requirements

- **UX-DR1 (Host Environment Embedding):** Interface embeds natively inside Gemini Enterprise Application (Discovery Engine / Agent Builder chat interface shell).
- **UX-DR2 (HITL Approval Card Component):** Prominently framed with amber border (`#f59e0b`), showing structured manifest table (Target API, Campsite ID, Unit IDs, Status, Identity Scope).
- **UX-DR3 (HITL Action Buttons):** Side-by-side **Approve** (Cyan/Indigo primary gradient) and **Reject** (Rose outline) buttons with real-time state changes (`"Executing..."` -> Confirmed green tint).
- **UX-DR4 (Yield Analytics Widget Component):** Circular gauge for Occupancy Rate paired with AVPN / RevPAR key metric cards and lagging market callouts.
- **UX-DR5 (Accessibility & Keyboard Support):** Full keyboard navigation (Tab stop focus on `Approve` button, `Enter` key shortcut) and ARIA screen reader attributes (`role="dialog"`, `aria-live="assertive"`).

### FR Coverage Map

- **FR-1:** Epic 1 - Story 1.1 (Intent Classification & Routing)
- **FR-2:** Epic 1 - Story 1.1 & 1.3 (Conversational Session State Retention)
- **FR-3:** Epic 2 - Story 2.2 (Human-in-the-Loop Interception Card)
- **FR-4:** Epic 1 - Story 1.2 (Text-to-SQL Query Generation on `ecg_analytics`)
- **FR-5:** Epic 1 - Story 1.3 (Multi-Period & Cluster Comparison)
- **FR-6:** Epic 2 - Story 2.1 (Mobil-Home Unit Inventory Status Update)
- **FR-7:** Epic 2 - Story 2.1 (Identity Passthrough Authorization)
- **FR-8:** Epic 3 - Story 3.2 (CRM Flash Campaign Staging)

---

## Epic List

### Epic 1: Natural Language Yield Analytics & Supervisor Orchestration
*Goal:* As a Regional Yield Manager, I want to query campsite cluster occupancy, RevPAR, and AVPN metrics using natural language, so that I can instantly detect booking deficits without manual SQL or data export.
**FRs covered:** FR-1, FR-2, FR-4, FR-5

### Epic 2: PMS Inventory Management & Human-in-the-Loop Release
*Goal:* As a Regional Operations Manager, I want to release held-back mobil-home units to sale via Resalys PMS with identity passthrough and interactive HITL approval confirmation, so that inventory is unlocked securely without unapproved mutations.
**FRs covered:** FR-3, FR-6, FR-7

### Epic 3: CRM Flash Campaign Staging & Marketing Activation
*Goal:* As a Regional Marketing Operator, I want to generate targeted Dutch promotional copy and stage a 15% discount campaign in the CRM via HITL confirmation, so that I can close the commercial recovery loop in under 5 minutes.
**FRs covered:** FR-8

---

## Epic 1: Natural Language Yield Analytics & Supervisor Orchestration

**Goal:** Provide natural language query capabilities over the `ecg_analytics` BigQuery dataset, coordinated by a Root Supervisor Agent maintaining multi-turn conversational session context.

### Story 1.1: Root Supervisor Agent & Conversational Session Scaffold

As a Regional Yield Manager,  
I want a root `ECG_Supervisor_Agent` and `StateSession` session context runner,  
So that my multi-turn prompts and campsite context are retained across conversation turns without re-prompting.

**Acceptance Criteria:**

**Given** an authenticated user session in Google Workspace Single Sign-On  
**When** the user sends a natural language prompt  
**Then** the `ECG_Supervisor_Agent` parses intent and initializes `StateSession` context  
**And** subsequent turns inherit previously specified campsite cluster or date window context without requesting it again.

---

### Story 1.2: Yield Analytics Agent & BigQuery NL-to-SQL Execution

As a Regional Yield Manager,  
I want to ask questions about occupancy rate, AVPN, and RevPAR in natural language,  
So that the `Yield_Analytics_Agent` executes parameterized SQL queries against `ecg_analytics` and displays a Yield Analytics UI Widget.

**Acceptance Criteria:**

**Given** a prompt requesting July occupancy and RevPAR for Mediterranean South campsite cluster  
**When** `ECG_Supervisor_Agent` routes the request to `Yield_Analytics_Agent`  
**Then** the agent generates parameterized SQL querying BigQuery dataset `ecg_analytics` on-the-fly without data caching  
**And** renders a Yield Analytics Widget displaying circular occupancy gauges and lagging market segment callouts (e.g. 15% Dutch lag).

---

### Story 1.3: Multi-Period & Campsite Cluster Comparative Analysis

As a Regional Yield Manager,  
I want to compare current booking performance against historical iso-day of week windows across regional campsite clusters,  
So that I can pinpoint specific unreleased inventory bottlenecks (e.g. 4 held-back mobil-homes at *La Sirène*).

**Acceptance Criteria:**

**Given** a prompt asking for "Dutch booking lag in Mediterranean South vs last year"  
**When** `Yield_Analytics_Agent` runs comparative SQL aggregations  
**Then** the response displays comparative variance tables and highlights held-back mobil-home unit IDs.

---

## Epic 2: PMS Inventory Management & Human-in-the-Loop Release

**Goal:** Safely update Property Management System (Resalys) mobil-home availability stock via Apigee Gateway with identity passthrough and mandatory Human-in-the-Loop approval interception.

### Story 2.1: Resalys PMS Inventory Update REST Tool with Identity Passthrough

As a Regional Operations Manager,  
I want the `PMS_Operations_Agent` to format REST payloads for `PUT /pms/v1/units/status` via Apigee Gateway forwarding my Cloud Identity bearer token,  
So that inventory status changes are authenticated under my IAM scope.

**Acceptance Criteria:**

**Given** a request to release mobil-homes MH-102 to MH-105 at *La Sirène*  
**When** `PMS_Operations_Agent` constructs the payload (`campsite_id`, `unit_type`, `unit_ids`, `new_status: AVAILABLE_FOR_SALE`)  
**Then** the request forwards the user's OAuth bearer token in the `Authorization` header  
**And** handles HTTP 401/403 authorization errors gracefully.

---

### Story 2.2: Interactive HITL Approval Card Component & Interception Gate

As a Regional Operations Manager,  
I want state-changing API operations (`PUT`, `POST`, `DELETE`) to pause and display an interactive amber HITL Approval Card,  
So that I can inspect the target API payload parameters and explicitly click **Approve** or **Reject** before any backend mutation occurs.

**Acceptance Criteria:**

**Given** a pending `resalys_update_unit_inventory` tool call  
**When** `ECG_Supervisor_Agent` intercepts the mutating call  
**Then** tool execution pauses and renders a dark glassmorphic HITL Approval Card framed with an amber border (`#f59e0b`) displaying the action manifest table  
**And** clicking **Approve** executes the API call, updating card status to `"Confirmed"` with a green success tint (`#10b981`), while clicking **Reject** cancels execution with zero backend side-effects  
**And** the card supports WCAG AA accessibility (`role="dialog"`, `aria-live="assertive"`, Tab focus on **Approve**, `Enter` key trigger).

---

## Epic 3: CRM Flash Campaign Staging & Marketing Activation

**Goal:** Generate targeted promotional copy, resolve Imagen/GCS assets, and stage draft marketing campaigns in the CRM via HITL confirmation.

### Story 3.1: Promotional Copywriting & Imagen Asset URI Resolution

As a Regional Marketing Operator,  
I want the `Marketing_Campaign_Agent` to generate Dutch promotional copywriting and resolve GCS asset URIs (`gs://ecg-marketing-assets/genai/promo_nl.png`),  
So that localized flash campaign materials are prepared automatically.

**Acceptance Criteria:**

**Given** an instruction to create a 15% discount promo for Dutch guests  
**When** `Marketing_Campaign_Agent` processes copywriting text and visual assets  
**Then** it produces structured campaign content paired with the validated GCS image URI.

---

### Story 3.2: CRM Flash Campaign Webhook Staging via HITL Approval

As a Regional Marketing Operator,  
I want to stage campaign drafts to `POST /marketing/v1/campaigns/draft` using a staged HITL confirmation card,  
So that draft campaigns are published to the CRM for final team sign-off in under 5 minutes without direct customer broadcasts.

**Acceptance Criteria:**

**Given** generated campaign details (`campaign_name`, `target_segment_id`, `discount_percentage`, `copywriting_text`, `image_asset_gcs_uri`)  
**When** `Marketing_Campaign_Agent` prepares the CRM webhook call  
**Then** an interactive HITL Approval Card requires user confirmation before dispatching the `POST` request  
**And** upon approval, the webhook returns campaign draft ID `Rattrapage_NL_Med_July` and updates the thread.
