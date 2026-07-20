---
title: 'Story 1.2: Yield Analytics Agent & BigQuery NL-to-SQL Execution'
type: 'feature'
created: '2026-07-20'
status: 'done'
baseline_revision: 'b4fe0a9227ac62bd55fb141efd37b4f77f68c118'
final_revision: 'de7b6afc2962dbbb91f18c189dde56f2a7c62f31'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/project-context.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** Regional Yield Managers need to query campsite occupancy rate, AVPN (Average Value Per Night), and RevPAR (Revenue Per Available Room) in natural language, but currently lack a dedicated sub-agent to generate and execute parameterized SQL against the `ecg_analytics` BigQuery dataset without local data caching.

**Approach:** Implement `Yield_Analytics_Agent` and `query_ecg_yield_data` tool in `src/agents/yield_analytics.py` using Google ADK (`google.genai.agent_development_kit`), integrate routing from `ECG_Supervisor_Agent`, and return structured Yield Analytics Widget data (occupancy circular gauge, AVPN/RevPAR metric cards, lagging market segment callouts) backed by unit tests in `tests/test_yield_analytics.py`.

## Boundaries & Constraints

**Always:**
- Execute BigQuery SQL directly on `ecg_analytics` live DWH without local caching or temporary table dumps.
- Bind `query_ecg_yield_data` tool to `Yield_Analytics_Agent` following snake_case tool naming conventions.
- Return structured output containing metric aggregations (occupancy rate %, AVPN €, RevPAR €) and lagging market segment callouts (e.g., Dutch market lagging).
- Model selection: `gemini-2.5-pro` (`MODEL_YIELD`) for SQL query synthesis and analytics reasoning.

**Block If:**
- `ecg_analytics` dataset schema is incompatible or BigQuery execution environment is unavailable without mock fallbacks.

**Never:**
- Hardcode SQL results or dump analytical tables locally to file system.
- Perform PMS inventory status updates or CRM marketing mutations within `Yield_Analytics_Agent`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Mediterranean South Occupancy Query | User prompt: "Analyze July occupancy and RevPAR for Mediterranean South campsite cluster" | `Yield_Analytics_Agent` generates parameterized BigQuery SQL querying `ecg_analytics.occupancy_daily`, returns metrics & widget payload | Returns error message if SQL query fails or dataset unreachable |
| Lagging Market Segment Detection | User prompt: "Identify lagging market segments for July" | Queries segment performance, highlights lagging segment (e.g. 15% Dutch lag) in widget callout | Handles missing segment data gracefully with zero division safety |
| Invalid / Malformed Query Parameters | Query with negative date window or empty cluster ID | Validates parameters before BigQuery dispatch | Returns structured validation error without executing invalid SQL |

</intent-contract>

## Code Map

- `src/config.py` -- Centralized configuration (MODEL_YIELD, BIGQUERY_DATASET, TEXT_TO_SQL_ACCURACY_THRESHOLD).
- `src/agents/yield_analytics.py` -- `Yield_Analytics_Agent` definition, `query_ecg_yield_data` BigQuery NL-to-SQL tool implementation, and widget payload builder.
- `src/agents/supervisor.py` -- Updated `ECG_Supervisor_Agent` to route `YIELD_ANALYTICS` prompts directly to `Yield_Analytics_Agent`.
- `src/agents/__init__.py` -- Package exports for `Yield_Analytics_Agent` and `query_ecg_yield_data`.
- `tests/test_yield_analytics.py` -- Unit tests validating NL-to-SQL generation, BigQuery tool execution, widget rendering payload, and supervisor routing integration.

## Tasks & Acceptance

**Execution:**
- [x] `src/agents/yield_analytics.py` -- Implement `Yield_Analytics_Agent` and `query_ecg_yield_data` BigQuery tool -- Provides NL-to-SQL query generation and yield metrics calculation.
- [x] `src/agents/supervisor.py` -- Integrate `Yield_Analytics_Agent` routing into `ECG_Supervisor_Agent` -- Enables seamless supervisor-to-subagent delegation.
- [x] `src/agents/__init__.py` -- Export `Yield_Analytics_Agent` and `query_ecg_yield_data` -- Exposes yield analytics components in package root.
- [x] `tests/test_yield_analytics.py` -- Implement unit tests for NL-to-SQL query execution, widget data formatting, and routing -- Ensures >95% accuracy and prevents regressions.

**Acceptance Criteria:**
- Given a prompt requesting July occupancy and RevPAR for Mediterranean South campsite cluster, when `ECG_Supervisor_Agent` routes the request to `Yield_Analytics_Agent`, then the agent generates parameterized SQL querying BigQuery dataset `ecg_analytics` on-the-fly without data caching and renders a Yield Analytics Widget displaying circular occupancy gauges and lagging market segment callouts (e.g. 15% Dutch lag).

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

`query_ecg_yield_data` formats parameterized SQL against `ecg_analytics.occupancy_daily` and `ecg_analytics.booking_segments`. Key metrics computed:
- Occupancy Rate = `SUM(occupied_units) / SUM(total_capacity)`
- AVPN (Average Value Per Night) = `SUM(total_revenue) / SUM(nights_sold)`
- RevPAR (Revenue Per Available Room) = `SUM(total_revenue) / SUM(total_capacity)`
Widget payload structure:
```json
{
  "widget_type": "YIELD_ANALYTICS",
  "metrics": {
    "occupancy_rate": 0.78,
    "avpn_eur": 112.50,
    "revpar_eur": 87.75
  },
  "lagging_callouts": [
    {"segment": "NL", "lag_percentage": 0.15, "description": "15% lag in Dutch market bookings"}
  ]
}
```

## Verification

**Commands:**
- `python3 -m pytest tests/test_yield_analytics.py` -- expected: all tests pass.
- `python3 -m pytest tests/` -- expected: full test suite passes including supervisor integration.

## Auto Run Result

**Status:** done

### Summary of Implemented Changes
- Implemented `src/agents/yield_analytics.py` containing `Yield_Analytics_Agent` and `query_ecg_yield_data` BigQuery NL-to-SQL tool.
- Supported natural language prompt parameter extraction (cluster IDs like `MEDITERRANEAN_SOUTH` / `ATLANTIC_NORTH`, date ranges, target market segments).
- `query_ecg_yield_data` generates parameterized BigQuery SQL queries on `ecg_analytics.occupancy_daily` and `ecg_analytics.booking_segments`, computing Occupancy Rate %, AVPN (€), RevPAR (€), and lagging market segment callouts (e.g. 15% Dutch lag).
- Updated `ECG_Supervisor_Agent` in `src/agents/supervisor.py` to route `YIELD_ANALYTICS` prompts directly to `Yield_Analytics_Agent`.
- Exported `Yield_Analytics_Agent` and `query_ecg_yield_data` in `src/agents/__init__.py`.
- Implemented unit test suite in `tests/test_yield_analytics.py` with 9 test cases covering agent execution, SQL query formatting, validation error handling, BigQuery client mocking, and supervisor routing.

### Files Changed
- `src/agents/yield_analytics.py` -- Yield Analytics Agent & BigQuery NL-to-SQL query tool implementation.
- `src/agents/supervisor.py` -- Integrated routing for Yield Analytics sub-agent.
- `src/agents/__init__.py` -- Package exports.
- `tests/test_yield_analytics.py` -- Unit tests for Yield Analytics Agent and query tool.

### Review Findings Breakdown
- Patches applied: 0
- Items deferred: 0
- Items rejected: 0

### Verification Performed
- `python3 -m pytest tests/test_yield_analytics.py` -> 9 passed in 0.01s.
- `python3 -m pytest tests/` -> 14 passed in 0.01s.

