---
title: 'Story 1.1: Root Supervisor Agent & Conversational Session Scaffold'
type: 'feature'
created: '2026-07-20'
status: 'done'
baseline_revision: 'NO_COMMITS'
final_revision: 'NO_COMMITS'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/project-context.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** The system currently lacks a root orchestrator agent and session state framework to receive user natural language inputs, route intents to sub-agents, and persist multi-turn conversational context across handoffs.

**Approach:** Implement `src/agents/supervisor.py` providing `ECG_Supervisor_Agent` using Google ADK (`google.genai.agent_development_kit`), initialize `StateSession` context retention for session variables (campsite ID, cluster ID, date window, target market), and provide unit test coverage in `tests/test_supervisor.py`.

## Boundaries & Constraints

**Always:**
- Use Google Agent Development Kit (`google.genai.agent_development_kit`) for supervisor agent instantiation and session state.
- Model selection: `gemini-2.5-pro` for root reasoning and supervisor orchestration.
- Preserve conversational context (`session.campsite_id`, `session.target_cluster`, `session.date_range`) in `StateSession` without re-prompting the user.
- Forward authenticated user identity context across turns.

**Block If:**
- ADK framework or `google-genai` SDK is unavailable in the environment.

**Never:**
- Perform direct BigQuery SQL queries or REST mutations inside the root supervisor; delegate all domain actions to sub-agents.
- Hardcode user session tokens or environment credentials.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Initial Session Turn | User prompt: "Analyze July occupancy for Mediterranean South cluster" | Supervisor initializes `StateSession` with `session.target_cluster = "MEDITERRANEAN_SOUTH"` and routes to Yield agent | Graceful prompt clarification if cluster unrecognized |
| Multi-turn Context Retention | Subsequent turn: "Release 4 units at La Sirène to sale" | Supervisor retains `session.target_cluster` and extracts campsite context for PMS operations | Re-prompts if campsite ID is ambiguous |
| Invalid / Empty Prompt | Empty or whitespace input string | Supervisor returns a polite prompt requesting operational instructions | Returns validation message without state mutation |

</intent-contract>

## Code Map

- `src/config.py` -- Centralized configuration settings (model names, dataset IDs, default parameters).
- `src/agents/supervisor.py` -- Root supervisor agent (`ECG_Supervisor_Agent`) definition, intent classification prompt, and `StateSession` initialization.
- `src/agents/__init__.py` -- Package exports for agents.
- `tests/test_supervisor.py` -- Unit tests validating supervisor intent routing, session context retention, and error handling.

## Tasks & Acceptance

**Execution:**
- [x] `src/config.py` -- Create configuration module defining Gemini model tiers and environment settings -- Establishes unified settings for ADK agents.
- [x] `src/agents/supervisor.py` -- Implement `ECG_Supervisor_Agent` and `StateSession` scaffold -- Provides root orchestrator and session state persistence.
- [x] `src/agents/__init__.py` -- Export supervisor agent -- Exposes clean package interface.
- [x] `tests/test_supervisor.py` -- Implement unit tests for intent classification and session context retention -- Validates correctness and prevents regressions.

**Acceptance Criteria:**
- Given an authenticated user session in Google Workspace Single Sign-On, when the user sends a natural language prompt, then the `ECG_Supervisor_Agent` parses intent and initializes `StateSession` context.
- Given an active session with specified campsite/cluster context, when a multi-turn request is made, then subsequent turns inherit previously specified campsite cluster or date window context without requesting it again.

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

The `ECG_Supervisor_Agent` uses ADK's `SupervisorAgent` (or `Agent` runner pattern) configured with `gemini-2.5-pro`. State keys follow namespaced notation `session.<variable_name>` stored inside the ADK `StateSession` object passed during runner execution.

## Verification

**Commands:**
- `python3 -m pytest tests/test_supervisor.py` -- expected: 5 passed in 0.01s.

## Auto Run Result

**Status:** done

### Summary of Implemented Changes
- Implemented `src/config.py` defining centralized model tiers (`MODEL_SUPERVISOR`, `MODEL_YIELD`, `MODEL_PMS`), BigQuery dataset settings (`ecg_analytics`), and Apigee endpoints.
- Implemented `src/agents/supervisor.py` containing `ECG_Supervisor_Agent` and `StateSession` for namespaced context retention (`session.target_cluster`, `session.campsite_id`, `session.target_market`).
- Implemented `src/agents/__init__.py` exporting `ECG_Supervisor_Agent` and `StateSession`.
- Implemented unit test suite in `tests/test_supervisor.py` with 5 automated test cases covering session initialization, state updates, intent classification, multi-turn context retention, and error handling.

### Files Changed
- `src/config.py` -- Centralized configuration settings and environment defaults.
- `src/agents/supervisor.py` -- Root supervisor agent and session context manager.
- `src/agents/__init__.py` -- Package exports.
- `tests/test_supervisor.py` -- Unit tests for supervisor intent routing and state retention.

### Review Findings Breakdown
- Patches applied: 0
- Items deferred: 0
- Items rejected: 0

### Verification Performed
- `python3 -m pytest tests/test_supervisor.py` -> 5 tests collected, 5 passed in 0.01s.
