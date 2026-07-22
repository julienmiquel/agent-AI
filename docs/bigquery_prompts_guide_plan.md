# Equivalent BigQuery NL-to-SQL Agent Prompts Guide Plan

## Goal Description
Provide equivalent, highly effective natural language prompts to query any BigQuery NL-to-SQL Agent connected to the `ecg_analytics` dataset (`occupancy_daily` and `booking_segments` tables). These prompts allow any data agent (such as Google ADK BigQueryTool, Vertex AI Agent Builder, or Gemini Enterprise Data Agents) to execute accurate SQL queries and extract the exact yield metrics and operational bottlenecks.

---

## Proposed Output Document
#### [NEW] `docs/bigquery_agent_prompts.md`
A reference guide containing equivalent prompts in French and English, complete with table mapping hints, column formulas, expected generated BigQuery SQL, and expected query responses.

---

## Prompts & SQL Mapping Structure

### 1. Comparative Yield Analysis (July 2026 vs July 2025)
- **Prompt (FR)**:
  > *"Compare le taux d'occupation (SUM(occupied_units)/SUM(total_capacity)) et le RevPAR (SUM(total_revenue)/SUM(total_capacity)) du cluster MEDITERRANEAN_SOUTH pour juillet 2026 vs juillet 2025 dans `occupancy_daily`. Liste aussi les unités en retard ou bloquées ('HELD_BACK') dans `booking_segments`."*
- **Expected SQL Generated**:
  ```sql
  -- Current Period
  SELECT SAFE_DIVIDE(SUM(occupied_units), SUM(total_capacity)) AS occupancy_rate,
         SAFE_DIVIDE(SUM(total_revenue), SUM(total_capacity)) AS revpar_eur
  FROM `ecg_analytics.occupancy_daily`
  WHERE cluster_id = 'MEDITERRANEAN_SOUTH' AND date BETWEEN '2026-07-01' AND '2026-07-31';

  -- Prior Period
  SELECT SAFE_DIVIDE(SUM(occupied_units), SUM(total_capacity)) AS occupancy_rate,
         SAFE_DIVIDE(SUM(total_revenue), SUM(total_capacity)) AS revpar_eur
  FROM `ecg_analytics.occupancy_daily`
  WHERE cluster_id = 'MEDITERRANEAN_SOUTH' AND date BETWEEN '2025-07-01' AND '2025-07-31';

  -- Held-back Units
  SELECT campsite_id, unit_id, status
  FROM `ecg_analytics.booking_segments`
  WHERE cluster_id = 'MEDITERRANEAN_SOUTH' AND status = 'HELD_BACK';
  ```

### 2. Single-Period Performance & Metrics
- **Prompt (FR)**:
  > *"Donne-moi le taux d'occupation, le prix moyen par nuitée (AVPN = SUM(total_revenue)/SUM(nights_sold)) et le RevPAR pour le cluster MEDITERRANEAN_SOUTH sur juillet 2026 dans `occupancy_daily`."*

### 3. Market Segment Lag Analysis
- **Prompt (FR)**:
  > *"Calcule le pourcentage de retard de réservation par marché (segment) dans `booking_segments` pour le cluster MEDITERRANEAN_SOUTH entre le 2026-07-01 et le 2026-07-31."*

### 4. Held-Back Units & Bottlenecks
- **Prompt (FR)**:
  > *"Quelles sont les unités mobil-home actuellement identifiées avec le statut HELD_BACK pour le camping La Sirène dans `booking_segments` ?"*

---

## Verification Plan

### Manual Verification
1. Validate prompts by executing the generated SQL against `customer-demo-01.ecg_analytics` live dataset.
2. Confirm returned values match: 78% occupancy (2026) vs 88% (2025), RevPAR 87,75 € vs 98,50 €, and 4 units (`MH-102`..`MH-105`) at `LA_SIRENE_06`.
