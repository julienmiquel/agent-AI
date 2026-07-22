---
title: 'Story 2.2: Interactive HITL Approval Card Component & Interception Gate'
type: 'feature'
created: '2026-07-20'
status: 'done'
baseline_revision: 'ff662d12804c5a6c74813f396992b3a837cb3497'
final_revision: 'ff662d12804c5a6c74813f396992b3a837cb3497'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/project-context.md', '_bmad-output/implementation-artifacts/epic-2-context.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** State-changing API operations (`PUT`, `POST`, `DELETE`) such as PMS inventory releases or CRM flash campaign drafts currently execute immediately without requiring user authorization, violating mandatory Human-In-The-Loop (HITL) safety governance.

**Approach:** Implement HITL interception gate and interactive approval card payload in `src/agents/supervisor.py` and sub-agents (`PMS_Operations_Agent`, `Marketing_Campaign_Agent`), pausing execution on mutating tool calls (`resalys_update_unit_inventory`, `crm_create_flash_campaign`), rendering a dark glassmorphic card with amber border (`#f59e0b`), and requiring explicit user approval (`YES`/`Approve`) before executing backend mutations.

## Boundaries & Constraints

**Always:**
- Intercept 100% of state-changing mutation operations (`PUT`, `POST`, `DELETE`) before backend tool execution.
- Render dark glassmorphic HITL Approval Card with amber border (`#f59e0b`), parameter manifest table (Target API endpoint, Campsite ID, Unit IDs, New Status, Identity Scope), and Approve / Reject controls.
- Require explicit confirmation (`Approve`, `Yes`, `Confirm`) to execute backend tool; abort execution on rejection (`Reject`, `No`, `Cancel`) with zero side-effects.
- Preserve session state and pending action context in `StateSession` while awaiting confirmation.

**Block If:**
- Mutation confirmation workflow bypasses HITL gate or executes backend side-effects without explicit authorization.

**Never:**
- Execute unconfirmed `PUT`, `POST`, or `DELETE` API mutations on initial intent classification without pausing for HITL confirmation.
- Hardcode approved states without user interaction.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Mutating Tool Interception | User prompt: "Release these held-back units at La Sirène" without prior approval | `ECG_Supervisor_Agent` pauses execution, returns `status: PENDING_CONFIRMATION`, and renders `HITL_APPROVAL_CARD` widget | Tool execution does not trigger |
| User Approves Mutation | User prompt: "Approve" while `StateSession` has pending action `resalys_update_unit_inventory` | `ECG_Supervisor_Agent` executes `resalys_update_unit_inventory`, returns `status: SUCCESS`, and transitions card to confirmed state (`#10b981`) | Handles tool execution errors gracefully |
| User Rejects Mutation | User prompt: "Reject" while `StateSession` has pending action | Aborts execution, returns `status: CANCELLED`, clears pending action, zero side-effects | Card transitions to rejected state (`#f43f5e`) |

</intent-contract>

## Code Map

- `src/agents/supervisor.py` -- HITL interception gate logic in `ECG_Supervisor_Agent.process_turn`, pending action retention in `StateSession`, and approval/rejection handling.
- `src/agents/pms_operations.py` -- Support `requires_confirmation` status check in `PMS_Operations_Agent.process_turn`.
- `src/agents/marketing_campaign.py` -- Support `requires_confirmation` status check in `Marketing_Campaign_Agent.process_turn`.
- `tests/test_supervisor.py` -- Unit tests validating HITL interception, pending state persistence, approval execution, and rejection handling.

## Tasks & Acceptance

**Execution:**
- [x] `src/agents/supervisor.py` -- Implement HITL interception gate in `ECG_Supervisor_Agent` -- Pauses mutating tool calls, generates `HITL_APPROVAL_CARD` widget, and handles approval/rejection turns.
- [x] `src/agents/pms_operations.py` -- Update `PMS_Operations_Agent` to respect HITL interception gate -- Prevents auto-execution of Resalys inventory updates without prior approval.
- [x] `src/agents/marketing_campaign.py` -- Update `Marketing_Campaign_Agent` to respect HITL interception gate -- Prevents auto-execution of CRM campaign creation without prior approval.
- [x] `tests/test_supervisor.py` -- Add unit tests for HITL interception, pending state retention, approval execution, and rejection cancellation -- Verifies NFR-5 governance compliance.

**Acceptance Criteria:**
- Given a pending mutating tool call, when `ECG_Supervisor_Agent` intercepts the call, then execution pauses, returns `status: PENDING_CONFIRMATION` with amber `#f59e0b` HITL Approval Card widget, and executes only when explicitly approved.

## Spec Change Log

*(No spec amendments required)*

## Review Triage Log

### 2026-07-20 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 6 (high 3, medium 3, low 0)
- defer: 0
- reject: 0
- addressed_findings:
  - `[high]` `[patch]` Prevented prompt keyword bypass by requiring programmatic `confirmed=True` flag for tool execution.
  - `[high]` `[patch]` Reordered rejection check before approval check and added negative phrase detection (`"not ok"`, `"don't"`) with word boundary regex.
  - `[high]` `[patch]` Replaced naive country substring matching (`"nl"`, `"fr"`, `"de"`) in `StateSession.update_from_prompt` with word boundary regex `r'\b(dutch|netherlands|nl)\b'`.
  - `[medium]` `[patch]` Added `widget` state transition payload (`card_state: "CONFIRMED"`, green tint `#10b981`) upon successful approval execution.
  - `[medium]` `[patch]` Added `copy.deepcopy()` in `StateSession.to_dict()` to prevent nested state reference leaks.
  - `[medium]` `[patch]` Wrapped sub-agent turn invocations in `try...except Exception as e:` returning `status: ERROR`.

## Design Notes

HITL Approval Card Widget Payload Structure:
```json
{
  "widget_type": "HITL_APPROVAL_CARD",
  "pending_action": "resalys_update_unit_inventory",
  "amber_border": "#f59e0b",
  "manifest": {
    "target_api": "PUT /pms/v1/units/status",
    "campsite_id": "LA_SIRENE_06",
    "unit_ids": ["MH-102", "MH-103", "MH-104", "MH-105"],
    "new_status": "AVAILABLE_FOR_SALE",
    "identity_scope": "CloudIdentity (mock_cloud_identity_token_julien)"
  },
  "actions": ["Approve", "Reject"]
}
```

## Verification

**Commands:**
- `python3 -m pytest tests/test_supervisor.py` -- expected: all supervisor tests pass including HITL interception.
- `python3 -m pytest tests/` -- expected: full test suite passes.
