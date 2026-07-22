---
title: 'Story 3.2: CRM Flash Campaign Webhook Staging via HITL Approval'
type: 'feature'
created: '2026-07-20'
status: 'done'
baseline_revision: 'ff662d12804c5a6c74813f396992b3a837cb3497'
final_revision: 'ff662d12804c5a6c74813f396992b3a837cb3497'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/project-context.md', '_bmad-output/implementation-artifacts/epic-3-context.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** Staging promotional flash campaigns via CRM Webhook API (`POST /marketing/v1/campaigns/draft`) must require explicit Human-In-The-Loop (HITL) authorization before pushing campaign creative payloads to Apigee gateway endpoints.

**Approach:** Verify and harden `Marketing_Campaign_Agent` integration with `ECG_Supervisor_Agent` HITL interception gate, ensuring mutating CRM campaign turns pause with an amber `#f59e0b` `HITL_APPROVAL_CARD` widget containing complete campaign manifest (Target API, Segment ID, Discount %, Copywriting text, Imagen GCS URI), and execute Apigee CRM Webhook dispatch only upon explicit user approval (`Approve`/`Yes`).

## Boundaries & Constraints

**Always:**
- Intercept 100% of CRM campaign creation requests before executing Apigee CRM Webhook API calls.
- Display `HITL_APPROVAL_CARD` widget with amber border (`#f59e0b`) containing full campaign manifest.
- Forward user identity scope (`CloudIdentity`) in request payload metadata.
- Require explicit confirmation (`Approve`, `Yes`) to execute webhook call; abort on rejection (`Reject`, `No`) with zero side-effects.

**Block If:**
- CRM Webhook call executes without HITL approval or omits campaign manifest parameters.

**Never:**
- Push unconfirmed marketing campaigns to Apigee CRM endpoints.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Marketing Campaign HITL Interception | User prompt: "Draft a flash promotion campaign for Dutch past guests" | `ECG_Supervisor_Agent` pauses execution, returns `status: PENDING_CONFIRMATION`, and renders `HITL_APPROVAL_CARD` widget | Webhook execution does not trigger |
| User Approves CRM Campaign | User prompt: "Approve" while `session.pending_action` is active | Dispatches `crm_create_flash_campaign`, returns `status: SUCCESS`, and transitions widget to `CONFIRMED` (`#10b981`) | Handles Webhook errors gracefully |
| User Rejects CRM Campaign | User prompt: "Reject" while pending action active | Cancels execution, returns `status: CANCELLED`, clears pending action, zero side-effects | Widget transitions to `REJECTED` (`#f43f5e`) |

</intent-contract>

## Code Map

- `src/config.py` -- Apigee marketing endpoint (`APIGEE_MARKETING_ENDPOINT`).
- `src/agents/supervisor.py` -- HITL interception gate for `MARKETING_CAMPAIGN` intent domain in `ECG_Supervisor_Agent.process_turn`.
- `src/agents/marketing_campaign.py` -- `crm_create_flash_campaign` tool and `Marketing_Campaign_Agent.process_turn`.
- `tests/test_marketing_campaign.py` -- End-to-end supervisor integration tests for CRM flash campaign HITL staging.

## Tasks & Acceptance

**Execution:**
- [x] `src/agents/supervisor.py` -- Ensure `MARKETING_CAMPAIGN` intent triggers `HITL_APPROVAL_CARD` widget with full campaign manifest -- Intercepts campaign staging until user approval.
- [x] `src/agents/marketing_campaign.py` -- Verify `crm_create_flash_campaign` returns structured `MARKETING_CAMPAIGN_DRAFT` widget -- Provides verified campaign draft payload.
- [x] `tests/test_marketing_campaign.py` -- Add unit and supervisor integration tests for CRM campaign HITL interception, approval execution, and rejection cancellation -- Validates end-to-end campaign staging flow.

**Acceptance Criteria:**
- Given a request to stage a flash campaign, when `Marketing_Campaign_Agent` creates the draft campaign, then the request triggers the interactive HITL Approval Card with campaign manifest, and clicking Approve dispatches the Apigee CRM Webhook payload (`POST /marketing/v1/campaigns/draft`), returning `status: SUCCESS`.

## Spec Change Log

*(No spec amendments required)*

## Review Triage Log

### 2026-07-20 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 5 (high 2, medium 3, low 0)
- defer: 0
- reject: 0
- addressed_findings:
  - `[high]` `[patch]` Dynamic prompt discount percentage extraction in `supervisor.py` for accurate HITL manifest generation.
  - `[high]` `[patch]` Added `test_marketing_campaign_hitl_interception_flow` verifying HITL interception and approval execution.
  - `[medium]` `[patch]` Updated `rejected_card` border color to `#f43f5e` to visually reflect rejection.
  - `[medium]` `[patch]` Added `identity_scope` (`CloudIdentity ({user_id})`) to CRM campaign payload metadata.
  - `[medium]` `[patch]` Added regex percentage extraction `r'(\d{1,3})\s*%'` supporting up to 100% discount.

## Verification

**Commands:**
- `python3 -m pytest tests/test_marketing_campaign.py` -- expected: all marketing campaign tests pass.
- `python3 -m pytest tests/` -- expected: full test suite passes.
