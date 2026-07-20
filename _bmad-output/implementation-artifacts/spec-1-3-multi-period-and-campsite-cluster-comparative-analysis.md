---
title: 'Story 1.3: Multi-Period & Campsite Cluster Comparative Analysis'
type: 'feature'
created: '2026-07-20'
status: 'done'
baseline_revision: '57023e85f2d12d8c648f0a199fca1fc494cf5c47'
final_revision: 'f2d1aba557cf79b8476e5538d03ae6136f1f177f'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/project-context.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** Regional Yield Managers need to compare current campsite booking metrics against historical iso-day windows (e.g., vs last year) across campsite clusters to pinpoint unreleased mobil-home inventory bottlenecks, but currently lack comparative SQL aggregation capabilities in `Yield_Analytics_Agent`.

**Approach:** Extend `src/agents/yield_analytics.py` with `compare_ecg_yield_data` tool and updated `Yield_Analytics_Agent` logic to execute comparative SQL aggregations across date windows and clusters, identify unreleased mobil-home unit IDs (e.g., held-back units at La Sirène), and populate `StateSession` context backed by unit tests in `tests/test_yield_analytics.py`.

## Boundaries & Constraints

**Always:**
- Execute comparative SQL queries live on `ecg_analytics` BigQuery tables without data caching or temporary table staging.
- Return structured comparative variance payload containing period-over-period metric deltas (occupancy rate delta, RevPAR delta) and specific held-back unit IDs.
- Store identified held-back unit IDs (`session.unit_ids`) in `StateSession` for seamless multi-turn handoffs to PMS Operations.
- Model selection: `gemini-2.5-pro` (`MODEL_YIELD`) for comparative query synthesis and analytics reasoning.

**Block If:**
- `ecg_analytics` comparative schema is unavailable or date windows are misaligned without iso-day matching.

**Never:**
- Perform PMS inventory status mutations (`PUT /pms/v1/units/status`) inside `Yield_Analytics_Agent`.
- Hardcode comparative variance tables without dynamic calculation.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Year-over-Year Mediterranean South Comparison | User prompt: "Dutch booking lag in Mediterranean South vs last year" | `Yield_Analytics_Agent` runs comparative SQL aggregations for 2026 vs 2025, displays variance table, highlights 4 held-back units (`MH-102` to `MH-105`) at La Sirène | Handles missing prior-year historical data with zero variance fallback |
| Multi-Cluster Comparative Variance | User prompt: "Compare July occupancy Mediterranean South vs Atlantic North" | Compares metrics across clusters, returns comparative variance widget payload | Validates both cluster IDs before BigQuery dispatch |
| Invalid Comparative Window | User prompt: "Compare July 2026 vs invalid date string" | Validates date formatting and window alignment | Returns structured validation error without executing invalid SQL |

</intent-contract>

## Code Map

- `src/config.py` -- Centralized configuration (MODEL_YIELD, BIGQUERY_DATASET, DEFAULT_CYCLE_TIME_SLA_SECONDS).
- `src/agents/yield_analytics.py` -- `compare_ecg_yield_data` implementation, `Yield_Analytics_Agent.parse_prompt` comparative detection, and comparative widget payload builder.
- `src/agents/supervisor.py` -- `StateSession` updates for persisting `session.unit_ids` and `session.campsite_id` during comparative analysis turns.
- `src/agents/__init__.py` -- Package exports for `compare_ecg_yield_data`.
- `tests/test_yield_analytics.py` -- Unit tests validating comparative SQL aggregations, YoY variance calculations, held-back unit extraction, and supervisor session state persistence.

## Tasks & Acceptance

**Execution:**
- [x] `src/agents/yield_analytics.py` -- Implement `compare_ecg_yield_data` and comparative prompt parsing in `Yield_Analytics_Agent` -- Enables YoY and multi-cluster variance analysis with held-back unit identification.
- [x] `src/agents/supervisor.py` -- Ensure `StateSession` context persists identified unit IDs (`session.unit_ids`) during comparative turns -- Supports seamless context retention for downstream PMS operations.
- [x] `src/agents/__init__.py` -- Export `compare_ecg_yield_data` -- Exposes comparative analytics tool in package exports.
- [x] `tests/test_yield_analytics.py` -- Add unit tests for comparative SQL execution, YoY variance, held-back unit extraction, and session retention -- Verifies >95% accuracy and prevents regressions.

**Acceptance Criteria:**
- Given a prompt asking for "Dutch booking lag in Mediterranean South vs last year", when `Yield_Analytics_Agent` runs comparative SQL aggregations, then the response displays comparative variance tables and highlights held-back mobil-home unit IDs (e.g. MH-102 to MH-105 at La Sirène) while updating `StateSession` context.

## Spec Change Log

*(No spec amendments required)*

## Review Triage Log

### 2026-07-20 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 0
- defer: 0
- reject: 0
- addressed_findings:
  - none

## Design Notes

`compare_ecg_yield_data` executes dual-period queries on `ecg_analytics.occupancy_daily` and `ecg_analytics.booking_segments` (current period vs prior year iso-day window).
Comparative Widget payload structure:
```json
{
  "widget_type": "YIELD_COMPARATIVE_ANALYTICS",
  "cluster_id": "MEDITERRANEAN_SOUTH",
  "current_period": {"start_date": "2026-07-01", "end_date": "2026-07-31", "occupancy_rate": 0.78, "revpar_eur": 87.75},
  "prior_period": {"start_date": "2025-07-01", "end_date": "2025-07-31", "occupancy_rate": 0.88, "revpar_eur": 98.50},
  "variance": {"occupancy_rate_delta": -0.10, "revpar_delta_eur": -10.75},
  "held_back_units": [
    {"campsite_id": "LA_SIRENE_06", "campsite_name": "La Sirène", "unit_ids": ["MH-102", "MH-103", "MH-104", "MH-105"], "count": 4}
  ]
}
```

## Verification

**Commands:**
- `python3 -m pytest tests/test_yield_analytics.py` -- expected: all unit tests pass including comparative queries.
- `python3 -m pytest tests/` -- expected: full test suite passes.

## Auto Run Result

**Status:** done

### Summary of Implemented Changes
- Implemented `compare_ecg_yield_data` tool function in `src/agents/yield_analytics.py` supporting comparative period-over-period queries across date windows (iso-day current vs prior year) and campsite clusters.
- Added YoY variance delta computation (`occupancy_rate_delta`, `revpar_delta_eur`) and unreleased mobil-home unit extraction (`MH-102` to `MH-105` at *La Sirène*).
- Updated `Yield_Analytics_Agent.parse_prompt` and `process_query` to detect comparative intent keywords (`"vs last year"`, `"prior year"`, `"compare"`, `"bottleneck"`, `"held-back"`, `"lag"`) and output comparative widget payloads (`widget_type: "YIELD_COMPARATIVE_ANALYTICS"`).
- Extended `StateSession` and `ECG_Supervisor_Agent` in `src/agents/supervisor.py` to persist identified unit IDs (`session.unit_ids`) and campsite ID (`session.campsite_id`) for downstream PMS operations handoff across conversational turns.
- Exported `compare_ecg_yield_data` in `src/agents/__init__.py`.
- Added unit tests in `tests/test_yield_analytics.py` covering comparative SQL queries, YoY metric deltas, held-back unit identification, missing prior data fallback, and multi-turn state retention.

### Files Changed
- `src/agents/yield_analytics.py` -- Comparative yield analytics tool & agent prompt parsing updates.
- `src/agents/supervisor.py` -- Session state context retention for unit IDs and campsite IDs.
- `src/agents/__init__.py` -- Package exports.
- `tests/test_yield_analytics.py` -- Unit test suite expansion (15 tests for yield analytics, 20 tests total).

### Review Findings Breakdown
- Patches applied: 0
- Items deferred: 0
- Items rejected: 0

### Verification Performed
- `python3 -m pytest tests/test_yield_analytics.py` -> 15 passed in 0.01s.
- `python3 -m pytest tests/` -> 20 passed in 0.02s.

