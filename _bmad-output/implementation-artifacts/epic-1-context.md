# Epic 1 Context: Natural Language Yield Analytics & Supervisor Orchestration

<!-- Generated from planning artifacts. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Enable Regional Yield Managers to query campsite cluster occupancy, RevPAR, and AVPN metrics using natural language, coordinated by a Root Supervisor Agent that retains multi-turn session context. This allows rapid detection of booking deficits and inventory bottlenecks without requiring manual SQL queries or data exports.

## Stories

- Story 1.1: Root Supervisor Agent & Conversational Session Scaffold
- Story 1.2: Yield Analytics Agent & BigQuery NL-to-SQL Execution
- Story 1.3: Multi-Period & Campsite Cluster Comparative Analysis

## Requirements & Constraints

- Intent Routing: The root supervisor agent must classify user intent and route analytics prompts to the Yield Analytics agent.
- Session State Persistence: Session state must retain context (e.g., campsite name, cluster ID, date range, target market) across multi-turn handoffs without requiring user re-prompting.
- Natural Language to SQL: Converts natural language queries into parameterized SQL executing on the `ecg_analytics` BigQuery dataset to calculate Occupancy Rate, Average Value Per Night (AVPN), and Revenue Per Available Room (RevPAR).
- Aggregation Dimensions: Aggregation must support grouping by accommodation type and customer nationality/country.
- Comparative Analysis: Enables comparative variance analysis across date ranges (iso-day of week matching) and regional campsite clusters to pinpoint specific unreleased inventory bottlenecks.
- Zero Data Duplication: Analytical queries must run live on BigQuery without caching, shadow tables, or local data dumps.
- Performance & Accuracy: Query generation and execution SLA <3.5 seconds with text-to-SQL accuracy >95%.
- Audit Logging: All agent reasoning traces, intent classification events, and executed SQL queries must stream to Vertex AI Observability and Cloud Logging with user ID timestamps.

## Technical Decisions

- Architecture Topology: Supervisor Multi-Agent Pattern using Google Agent Development Kit (`google-genai`). All client interactions enter via `ECG_Supervisor_Agent`.
- Model Backbone: Standardized on `gemini-3.5-flash` for `ECG_Supervisor_Agent` and `Yield_Analytics_Agent`.
- Tool Binding: `Yield_Analytics_Agent` equips `BigQueryTool` bound directly to the `ecg_analytics` dataset. Tool naming convention uses snake_case (`query_ecg_yield_data`), while agents use PascalCase.
- State Architecture: Session context is persisted in `StateSession` using namespaced keys (`session.campsite_id`, `session.target_cluster`).
- Data Conventions: Date parameters formatted in ISO-8601 (`YYYY-MM-DD`); metric names strictly uppercase (`OCCUPANCY_RATE`, `AVPN`, `REVPAR`).

## UX & Interaction Patterns

- Host Environment Embedding: Embedded inside Gemini Enterprise Application chat shell.
- Thinking Indicator: Displays an animated pulse indicator (`"Yield Analytics Agent is querying BigQuery..."`) during query execution.
- Yield Analytics Widget: Renders structured visual widget with circular gauges for Occupancy Rate, metric cards for AVPN/RevPAR, and warning callouts for lagging market segments.
- Code Containers: Generated SQL queries render in copyable monospace block containers.

## Cross-Story Dependencies

- Story 1.1 lays the foundational `ECG_Supervisor_Agent` and `StateSession` scaffold needed before Story 1.2 and Story 1.3 can maintain context.
- Story 1.2 builds the core NL-to-SQL BigQuery execution engine used and extended by Story 1.3 for complex comparative aggregations.
- Conversational state established in Epic 1 (e.g., identified campsite and unit IDs) feeds directly into downstream PMS inventory operations in Epic 2.
