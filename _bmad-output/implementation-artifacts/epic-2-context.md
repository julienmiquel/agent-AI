# Epic 2 Context: PMS Inventory Management & Human-in-the-Loop Release

<!-- Generated from planning artifacts. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Safely update Property Management System (Resalys) mobil-home availability stock via Apigee Gateway with identity passthrough and mandatory Human-in-the-Loop approval interception, so that inventory is unlocked securely without unapproved mutations.

## Stories

- Story 2.1: Resalys PMS Inventory Update REST Tool with Identity Passthrough
- Story 2.2: Interactive HITL Approval Card Component & Interception Gate

## Requirements & Constraints

- **Mobil-Home Inventory Status Updates:** Update mobil-home availability status in Resalys PMS to `AVAILABLE_FOR_SALE` by dispatching REST requests to `PUT /pms/v1/units/status` via Apigee API Gateway. Request payload requires `campsite_id`, `unit_type`, `unit_ids`, and `new_status`.
- **Identity Passthrough Authorization:** User OAuth2 Cloud Identity bearer tokens must be passed verbatim in the `Authorization` header (`Bearer {user_token}`) for all Apigee REST tool invocations. The agent operates strictly within the authenticated user's IAM scope without service account privilege escalation, and must handle HTTP 401/403 authorization errors gracefully.
- **Human-in-the-Loop (HITL) Interception Gate:** 100% of state-changing operations (`PUT`, `POST`, `PATCH`, `DELETE`) must be intercepted before backend tool execution. Execution pauses until explicit user authorization (`YES` / `Approve`) is granted via an interactive approval card. Rejection or session expiry aborts execution immediately with zero backend side-effects.
- **Observability & Audit Trail:** All agent reasoning traces, intent routing events, tool invocations, and HITL approval decisions must be streamed to Vertex AI Agent Observability and Cloud Logging with user ID metadata and timestamps.
- **Mocking & Integration Contracts:** Unit and evaluation test suites must mock all Apigee REST endpoints (`api.ecg.camp/pms`) using OpenAPI stubs (`httpx_mock` / `responses`) to prevent unintended backend mutations during testing.

## Technical Decisions

- **Agent Topology & Responsibility:** `PMS_Operations_Agent` operates as a specialized child agent under the root `ECG_Supervisor_Agent`. All external user requests land at the Supervisor first.
- **Model Standard:** `PMS_Operations_Agent` uses `gemini-3.5-flash` as its primary LLM backbone.
- **API Tooling:** `PMS_Operations_Agent` equips an `OpenAPITool` bound to the Resalys OpenAPI 3.0 specification (`pms_openapi.json`) deployed on Apigee API Gateway (`https://api.ecg.camp/pms/v1`).
- **Session State Retention:** Context parameters (campsite ID, unit IDs) established during multi-turn conversations are persisted across agent handoffs via `StateSession`.
- **HITL Interceptor Mechanism:** ADK tool callbacks for mutating tools (`resalys_update_unit_inventory`) trigger an ADK runner pause state, requiring explicit user approval before executing the callback.
- **Naming Conventions:** Agent name must be `PMS_Operations_Agent` (PascalCase); tool name must be `resalys_update_unit_inventory` (snake_case).

## UX & Interaction Patterns

- **HITL Approval Card Component:** Rendered inline in the conversational thread as a dark glassmorphic card framed with an amber accent border (`#f59e0b`).
- **Action Manifest Table:** Displays a clear parameter summary (Target API endpoint, Campsite ID, Unit IDs, Target Status, Identity Scope).
- **Interactive Action Controls:** Features side-by-side **Approve** (Cyan/Indigo primary gradient) and **Reject** (Rose outline) buttons.
- **Card State Transitions:**
  - *Pending:* Interactive buttons active, amber border, screen auto-scrolls to focus card.
  - *Executing:* Buttons disabled, loading spinner active, card status updates to `"Executing..."`.
  - *Confirmed:* Card background transitions to green tint (`#10b981`), status updates to `"Confirmed"`.
  - *Rejected:* Card background transitions to red tint (`#f43f5e`), cancellation logged in thread without side-effects.
- **Accessibility & Keyboard Navigation:** Full WCAG AA accessibility compliance including keyboard focus (Tab focus on `Approve` button, `Enter` key trigger) and ARIA attributes (`role="dialog"`, `aria-live="assertive"`).

## Cross-Story Dependencies

- **Story 2.1 → Story 2.2:** Story 2.1 implements the `resalys_update_unit_inventory` REST tool and bearer token authorization logic. Story 2.2 builds the HITL interception gate and interactive UI card that wraps and guards tool calls like `resalys_update_unit_inventory`.
- **Upstream Context from Epic 1:** Relies on session context (`campsite_id`, `unit_ids`) stored in `StateSession` during Epic 1 yield analytics turns.
