# BigQuery Scenario Verification & Confirmation Plan

## Goal Description
Verify and confirm that BigQuery dataset `customer-demo-01.ecg_analytics` (`occupancy_daily` and `booking_segments` tables) matches the requested comparative yield scenario for cluster `MEDITERRANEAN_SOUTH` (July 2026 vs July 2025).

---

## Scenario Metrics & Alignment Matrix

| Parameter / Metric | Expected Value (User Scenario) | BigQuery Live Output | Alignment Status |
| :--- | :--- | :--- | :--- |
| **Cluster** | `MEDITERRANEAN_SOUTH` | `MEDITERRANEAN_SOUTH` | ✅ Matched |
| **Current Period (July 2026) Occupancy** | **78 %** (`0.78`) | **78.00 %** (`0.78`) | ✅ Matched |
| **Current Period (July 2026) RevPAR** | **87,75 €** | **87,75 €** | ✅ Matched |
| **Prior Period (July 2025) Occupancy** | **88 %** (`0.88`) | **88.00 %** (`0.88`) | ✅ Matched |
| **Prior Period (July 2025) RevPAR** | **98,50 €** | **98,50 €** | ✅ Matched |
| **Occupancy Delta** | **-10 %** (-10 points) | **-10.00 %** (`-0.10`) | ✅ Matched |
| **RevPAR Delta** | **-10,75 €** | **-10,75 €** | ✅ Matched |
| **Campsite & Held-Back Units** | **4 mobil-homes at La Sirène (`LA_SIRENE_06`)** | `LA_SIRENE_06`: `["MH-102", "MH-103", "MH-104", "MH-105"]` | ✅ Matched |

---

## Verification Strategy
Execute live query via `Yield_Analytics_Agent` connected to `customer-demo-01.ecg_analytics`:
```bash
uv run python3 -c "from google.cloud import bigquery; from src.agents.yield_analytics import Yield_Analytics_Agent; agent = Yield_Analytics_Agent(); client = bigquery.Client(project='customer-demo-01'); print(agent.process_query('Dutch booking lag in Mediterranean South vs last year', bq_client=client))"
```
