# Epic 3 Context: CRM Flash Campaign Staging & Marketing Activation

<!-- Generated from planning artifacts. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Enable Regional Marketing Operators to generate targeted Dutch promotional copy, resolve generated visual assets, and stage a 15% discount flash campaign draft in the CRM system via Human-in-the-Loop (HITL) approval confirmation, completing the yield-to-market recovery loop in under 5 minutes without direct customer broadcasts.

## Stories

- Story 3.1: Promotional Copywriting & Imagen Asset URI Resolution
- Story 3.2: CRM Flash Campaign Webhook Staging via HITL Approval

## Requirements & Constraints

- **CRM Campaign Draft Staging:** The system must construct and dispatch webhook payloads to `POST https://api.ecg.camp/marketing/v1/campaigns/draft` using the marketing tool `crm_create_flash_campaign`.
- **No Direct Customer Broadcasts:** Campaigns must strictly be staged as *drafts* in the CRM for final marketing sign-off; direct automated customer email or SMS broadcasts are prohibited.
- **Asset Storage & Resolution:** Visual marketing assets generated via Imagen 3 must be saved to Cloud Storage under `gs://ecg-marketing-assets/genai/` and referenced via valid GCS URIs in campaign staging payloads.
- **Human-in-the-Loop Interception:** Staging requests (`POST`) must pause execution and present an interactive HITL approval card detailing campaign parameters. Execution occurs only upon explicit user approval (`YES`); rejection aborts execution with zero side-effects.
- **Identity Passthrough Authorization:** Webhook calls must forward the user's Cloud Identity OAuth bearer token in the `Authorization` header without service account privilege escalation.
- **Execution SLA:** End-to-end execution from yield anomaly detection to staged campaign draft must complete in under 5 minutes.
- **Observability & Auditing:** Reasoning traces, asset URIs, campaign parameters, and user HITL approval timestamps must be logged to Cloud Logging and Vertex AI Agent Observability.

## Technical Decisions

- **Agent Architecture:** `Marketing_Campaign_Agent` is a specialized child agent under `ECG_Supervisor_Agent`, running on `gemini-3.5-flash`.
- **Session Context Retention:** `Marketing_Campaign_Agent` inherits conversational session context (such as target campsite cluster and customer nationality) from `StateSession` across multi-turn handoffs.
- **Webhook Payload Schema:** `POST /marketing/v1/campaigns/draft` requires:
  - `campaign_name` (string, e.g. `"Rattrapage_NL_Med_July"`)
  - `target_segment_id` (string, e.g. `"SEG_NL_PAST_GUESTS_MED_2025"`)
  - `discount_percentage` (integer/number, e.g. `15`)
  - `copywriting_text` (string, localized Dutch marketing message)
  - `image_asset_gcs_uri` (string, GCS path e.g. `"gs://ecg-marketing-assets/genai/promo_nl.png"`)
- **Tool Binding & Mocking:** Interacts with the CRM OpenAPI spec (`crm_openapi.json`). Local dev and unit tests must intercept `api.ecg.camp/marketing` calls using OpenAPI stubs to prevent unapproved external API mutations.

## UX & Interaction Patterns

- **Host Environment:** Renders inline within the Gemini Enterprise Application chat stream.
- **HITL Approval Card Component:** Framed in dark glassmorphism with a prominent amber border (`#f59e0b`). Displays structured action manifest (Campaign Name, Target Segment ID, Discount %, Copywriting preview, Asset GCS URI) with side-by-side **Approve** (Cyan/Indigo gradient) and **Reject** (Rose outline) action buttons.
- **Card State Progression:** Clicking **Approve** updates card state to `"Approved — Executing..."` with a spinner, resolving into a green confirmed state (`#10b981`) showing draft ID `Rattrapage_NL_Med_July`. Clicking **Reject** transitions card to red (`#f43f5e`) with cancellation logged.
- **Accessibility (a11y):** Supports keyboard navigation (`Tab` focus on **Approve**, `Enter` key trigger) and ARIA attributes (`role="dialog"`, `aria-live="assertive"`).

## Cross-Story Dependencies

- **Story 3.1 → Story 3.2:** Story 3.1 produces the localized Dutch copywriting text and resolves the validated GCS image URI (`gs://ecg-marketing-assets/genai/promo_nl.png`). Story 3.2 consumes these outputs to construct the payload for `crm_create_flash_campaign` and trigger the HITL confirmation gate before dispatching the draft staging webhook.
- **Upstream Context:** Relies on `ECG_Supervisor_Agent` session state initialized in Epic 1 (Story 1.1) to preserve cluster identity (e.g. Mediterranean South) and target market segment context.
