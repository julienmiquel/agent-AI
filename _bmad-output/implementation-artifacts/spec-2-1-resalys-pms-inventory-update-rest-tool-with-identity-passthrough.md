---
title: 'Story 2.1: Resalys PMS Inventory Update REST Tool with Identity Passthrough'
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

**Problem:** Regional Operations Managers need to release held-back mobil-home units to sale via Resalys PMS authenticated under their specific Google Cloud Identity IAM scope, but currently lack a dedicated REST tool on `PMS_Operations_Agent` that passes identity authorization tokens to Apigee API Gateway.

**Approach:** Implement `resalys_update_unit_inventory` tool and `PMS_Operations_Agent` in `src/agents/pms_operations.py`, incorporating user OAuth bearer token passthrough in HTTP `Authorization` headers, session context retrieval (`campsite_id`, `unit_ids`), error handling for 401/403 errors, and unit test coverage in `tests/test_pms_operations.py`.

## Boundaries & Constraints

**Always:**
- Forward user OAuth bearer token in `Authorization` header (`Bearer {user_token}`) without service account privilege escalation.
- Return structured `PMS_INVENTORY_UPDATE` widget payload containing `campsite_id`, `unit_ids`, `updated_status`, `updated_count`, `endpoint`, and `identity_scope`.
- Validate input parameters (`campsite_id` and non-empty `unit_ids`) before dispatching API calls.
- Model selection: `gemini-3.6-flash` (`MODEL_PMS`) for operational PMS inventory handling.

**Block If:**
- Resalys PMS endpoint schema changes or authentication requires elevated service account scopes.

**Never:**
- Perform unauthenticated inventory status mutations or default fallbacks without explicit unit selection or session context.
- Hardcode inventory updates without returning structured PMS widget payload.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Release Mobil-Homes at La Sirène | User prompt: "Release these held-back mobil-home units to sale at La Sirène" + `StateSession` containing `unit_ids: ['MH-102', 'MH-103', 'MH-104', 'MH-105']` | `PMS_Operations_Agent` invokes `resalys_update_unit_inventory`, returns `status: SUCCESS`, `updated_count: 4`, and `PMS_INVENTORY_UPDATE` widget | Handles empty unit_ids with structured `VALIDATION_ERROR` |
| Identity Bearer Token Passthrough | Call `resalys_update_unit_inventory` with `user_token: "token_abc"` | Request payload headers include `Authorization: Bearer token_abc` | Handles missing token with fallback mock identity scope |
| Empty Campsite ID | Call `resalys_update_unit_inventory` with `campsite_id: ""` | Returns `VALIDATION_ERROR` with error message "Campsite ID cannot be empty." | Returns structured validation payload |

</intent-contract>

## Code Map

- `src/config.py` -- Centralized configuration (`APIGEE_PMS_ENDPOINT`, `MODEL_PMS`).
- `src/agents/pms_operations.py` -- `resalys_update_unit_inventory` implementation and `PMS_Operations_Agent.process_turn`.
- `src/agents/supervisor.py` -- Routing intent classification (`PMS_OPERATIONS`) and `StateSession` context propagation.
- `src/agents/__init__.py` -- Package exports for `PMS_Operations_Agent` and `resalys_update_unit_inventory`.
- `tests/test_pms_operations.py` -- Unit tests validating inventory status updates, identity token headers, parameter validation, and supervisor session routing.

## Tasks & Acceptance

**Execution:**
- [x] `src/agents/pms_operations.py` -- Implement `resalys_update_unit_inventory` tool and `PMS_Operations_Agent.process_turn` with bearer token passthrough -- Enables authenticated Resalys inventory releases.
- [x] `src/agents/supervisor.py` -- Configure routing and context retention for `PMS_Operations_Agent` -- Supports multi-turn handoffs from yield analytics to PMS release.
- [x] `src/agents/__init__.py` -- Export `PMS_Operations_Agent` and `resalys_update_unit_inventory` -- Exposes PMS agent and tool in package exports.
- [x] `tests/test_pms_operations.py` -- Add unit tests for inventory updates, bearer token headers, validation errors, and supervisor routing -- Verifies correct tool behavior and prevents regressions.

**Acceptance Criteria:**
- Given a request to release mobil-homes MH-102 to MH-105 at La Sirène, when `PMS_Operations_Agent` constructs the payload, then the request forwards the user's OAuth bearer token in the `Authorization` header and updates status to `AVAILABLE_FOR_SALE`.

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
  - `[high]` `[patch]` Removed hardcoded default unit IDs fallback in `PMS_Operations_Agent.process_turn()`, returning `VALIDATION_ERROR` if no unit IDs exist in session or prompt.
  - `[high]` `[patch]` Fixed hardcoded status override in `PMS_Operations_Agent.process_turn()`, extracting target status (`AVAILABLE_FOR_SALE`, `UNDER_MAINTENANCE`, `BLOCKED`) from user prompt.
  - `[medium]` `[patch]` Added `user_token` identity passthrough support in `PMS_Operations_Agent.process_turn()` and `StateSession`.
  - `[medium]` `[patch]` Added input type checks for `campsite_id` and whitelist validation for `new_status` in `resalys_update_unit_inventory()`.
  - `[medium]` `[patch]` Added `prompt=None` null checks and extended edge-case unit tests in `tests/test_pms_operations.py`.

## Design Notes

`resalys_update_unit_inventory` constructs the REST request payload and widget:
```json
{
  "widget_type": "PMS_INVENTORY_UPDATE",
  "campsite_id": "LA_SIRENE_06",
  "unit_type": "PREMIUM_3_BEDROOMS",
  "unit_ids": ["MH-102", "MH-103", "MH-104", "MH-105"],
  "updated_status": "AVAILABLE_FOR_SALE",
  "updated_count": 4,
  "endpoint": "https://api.ecg.camp/pms/v1/units/status",
  "identity_scope": "CloudIdentity (mock_cloud_identity_token_julien)"
}
```

## Verification

**Commands:**
- `python3 -m pytest tests/test_pms_operations.py` -- expected: all 4 unit tests pass.
- `python3 -m pytest tests/` -- expected: full test suite passes (30 tests).
