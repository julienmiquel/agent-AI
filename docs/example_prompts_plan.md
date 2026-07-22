# ECG Multi-Agent Example Prompt Queries Implementation Plan

## Goal Description
Create a comprehensive catalog of example natural language prompts, BigQuery SQL queries, and multi-turn conversation workflows for the European Camping Group (ECG) Multi-Agent System. This reference guide will help users, testers, and stakeholders effectively query and operate the system.

---

## Proposed Output Document
#### [NEW] `docs/example_prompts.md`
A structured markdown guide containing ready-to-use prompt queries, expected BigQuery SQL outputs, intent classifications, session context transitions, and Human-in-the-Loop (HITL) interaction cards.

---

## Overview of Prompt Categories Covered

### 1. Yield & Data Analytics (`Yield_Analytics_Agent`)
- **Single-Period Metric Queries**:
  - *"Analyze July occupancy and RevPAR for Mediterranean South campsite cluster"*
  - *"Analyze August yield metrics for Atlantic North cluster"*
  - *"Query metrics from 2026-07-05 to 2026-07-20 for Mediterranean South cluster"*
  - *"Identify lagging market segments for July for Dutch market"*
- **Comparative YoY & Held-back Bottleneck Queries**:
  - *"Dutch booking lag in Mediterranean South vs last year"*
  - *"Compare July occupancy Mediterranean South vs Atlantic North"*
  - *"Identify held-back mobil-homes causing booking lag at La Sirène"*

### 2. Operations & PMS Inventory Management (`PMS_Operations_Agent`)
- **Inventory Release & Status Update Prompts**:
  - *"Release mobil-homes MH-102, MH-103, MH-104, MH-105 at La Sirène to sale"*
  - *"Set mobil-homes MH-201 and MH-202 at Dolmen Cove to AVAILABLE_FOR_SALE"*
  - *"Unlock maintenance units at La Sirène for public booking"*

### 3. CRM Marketing Campaign Generation (`Marketing_Campaign_Agent`)
- **Flash Promotion & Asset Creation Prompts**:
  - *"Draft a 15% discount promo campaign for Dutch past guests to boost July occupancy at La Sirène"*
  - *"Create a CRM promo draft for French market in Atlantic North"*
  - *"Generate flash promotional copy and visual asset URI for German segment"*

### 4. End-to-End Multi-Turn Conversational Workflows (`ECG_Supervisor_Agent`)
- **Scenario A: Complete Yield-to-PMS-to-Marketing Loop**:
  - **Turn 1**: *"Dutch booking lag in Mediterranean South vs last year"* -> Yield Analytics & Held-back unit detection (`MH-102` to `MH-105` at `LA_SIRENE_06`).
  - **Turn 2**: *"Release these 4 held-back mobil-home units to sale at La Sirène"* -> Operational PMS release with HITL approval card.
  - **Turn 3**: *"Approve"* -> Execution of Resalys API release.
  - **Turn 4**: *"Draft a 15% discount promo for Dutch past guests"* -> Marketing campaign draft creation.
- **Scenario B: Quick Status Check & Release**:
  - **Turn 1**: *"Analyze August yield metrics for Atlantic North cluster"*
  - **Turn 2**: *"Release units MH-201 and MH-202 to sale"*

---

## Verification Plan

### Manual Verification
1. Verify each prompt query against `ECG_Supervisor_Agent.classify_intent`.
2. Test multi-turn execution via `.venv/bin/pytest` and python dry-run.
