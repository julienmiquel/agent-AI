# Guide des Prompts Équivalents pour Agent BigQuery NL-to-SQL

Ce guide fournit les prompts en langage naturel (en Français et en Anglais) équivalents pour interroger **n'importe quel Agent BigQuery NL-to-SQL générique** (ex: `BigQueryTool` ADK, Vertex AI Agent Builder, Gemini Enterprise Data Agent) branché sur le dataset `ecg_analytics` (`occupancy_daily` et `booking_segments`).

---

## 📊 1. Analyse Comparative Yield (Juillet 2026 vs Juillet 2025)

### Prompts en Français (FR)

#### Prompt Naturel (Direct)
> *"Fais une analyse comparative du taux d'occupation et du RevPAR pour le cluster MEDITERRANEAN_SOUTH entre juillet 2026 et juillet 2025 dans `occupancy_daily`. Identifie également les mobil-homes bloqués ('HELD_BACK') dans `booking_segments`."*

#### Prompt Explicite (Incertitude Schéma / Formules)
> *"À partir des tables `occupancy_daily` et `booking_segments` du dataset `ecg_analytics` :*
> *1. Calcule le taux d'occupation (SUM(occupied_units)/SUM(total_capacity)) et le RevPAR (SUM(total_revenue)/SUM(total_capacity)) pour le cluster_id 'MEDITERRANEAN_SOUTH' entre 2026-07-01 et 2026-07-31.*
> *2. Calcule les mêmes métriques pour la période 2025-07-01 à 2025-07-31.*
> *3. Calcule la différence (delta).*
> *4. Affiche les unit_id et campsite_id pour les enregistrements avec status = 'HELD_BACK' pour ce cluster."*

---

### Prompts en Anglais (EN)

#### Natural Prompt
> *"Run a period-over-period comparative yield analysis for the MEDITERRANEAN_SOUTH cluster comparing July 2026 to July 2025 using `occupancy_daily`. Include occupancy rate, RevPAR, and list any held-back mobil-home units (`status = 'HELD_BACK'`) from `booking_segments`."*

---

### Requêtes BigQuery SQL Générées par l'Agent

```sql
-- Query 1: Période Actuelle (Juillet 2026)
SELECT
  SAFE_DIVIDE(SUM(occupied_units), SUM(total_capacity)) AS occupancy_rate,
  SAFE_DIVIDE(SUM(total_revenue), SUM(total_capacity)) AS revpar_eur
FROM `ecg_analytics.occupancy_daily`
WHERE cluster_id = 'MEDITERRANEAN_SOUTH'
  AND date BETWEEN '2026-07-01' AND '2026-07-31';

-- Query 2: Période Précédente (Juillet 2025)
SELECT
  SAFE_DIVIDE(SUM(occupied_units), SUM(total_capacity)) AS occupancy_rate,
  SAFE_DIVIDE(SUM(total_revenue), SUM(total_capacity)) AS revpar_eur
FROM `ecg_analytics.occupancy_daily`
WHERE cluster_id = 'MEDITERRANEAN_SOUTH'
  AND date BETWEEN '2025-07-01' AND '2025-07-31';

-- Query 3: Unités Bloquées / Bottleneck
SELECT campsite_id, unit_id, status
FROM `ecg_analytics.booking_segments`
WHERE cluster_id = 'MEDITERRANEAN_SOUTH'
  AND status = 'HELD_BACK';
```

---

## 📈 2. Métriques Yield Période Simple (Occupancy, AVPN, RevPAR)

### Prompt (FR)
> *"Calcule le taux d'occupation moyen, le prix moyen par nuitée vendue (AVPN = SUM(total_revenue)/SUM(nights_sold)) et le RevPAR pour le cluster MEDITERRANEAN_SOUTH sur la période du 1er au 31 juillet 2026 dans `occupancy_daily`."*

### Prompt (EN)
> *"Compute overall occupancy rate, average rate per night sold (AVPN), and RevPAR for cluster MEDITERRANEAN_SOUTH between 2026-07-01 and 2026-07-31 from `occupancy_daily`."*

```sql
SELECT
  SAFE_DIVIDE(SUM(occupied_units), SUM(total_capacity)) AS occupancy_rate,
  SAFE_DIVIDE(SUM(total_revenue), SUM(nights_sold)) AS avpn_eur,
  SAFE_DIVIDE(SUM(total_revenue), SUM(total_capacity)) AS revpar_eur
FROM `ecg_analytics.occupancy_daily`
WHERE cluster_id = 'MEDITERRANEAN_SOUTH'
  AND date BETWEEN '2026-07-01' AND '2026-07-31';
```

---

## 🎯 3. Analyse du Retard de Réservation par Marché (Segment Lag)

### Prompt (FR)
> *"À partir de la table `booking_segments`, calcule le pourcentage de retard de réservation ((SUM(target_units) - SUM(booked_units)) / SUM(target_units)) par marché (segment) pour le cluster MEDITERRANEAN_SOUTH en juillet 2026."*

### Prompt (EN)
> *"Using `booking_segments`, calculate the booking lag percentage grouped by market segment for cluster MEDITERRANEAN_SOUTH in July 2026."*

```sql
SELECT
  segment,
  SAFE_DIVIDE(SUM(target_units) - SUM(booked_units), SUM(target_units)) AS lag_percentage
FROM `ecg_analytics.booking_segments`
WHERE cluster_id = 'MEDITERRANEAN_SOUTH'
  AND date BETWEEN '2026-07-01' AND '2026-07-31'
GROUP BY segment;
```

---

## 🔒 4. Détection des Mobil-homes Bloqués en Maintenance (Resalys PMS Bottleneck)

### Prompt (FR)
> *"Liste l'ensemble des mobil-homes (unit_id et campsite_id) bloqués à la vente avec le statut 'HELD_BACK' dans `booking_segments` pour le cluster MEDITERRANEAN_SOUTH."*

### Prompt (EN)
> *"List all mobil-home unit IDs and campsite IDs with status 'HELD_BACK' from `booking_segments` for cluster MEDITERRANEAN_SOUTH."*

```sql
SELECT campsite_id, unit_id, status
FROM `ecg_analytics.booking_segments`
WHERE cluster_id = 'MEDITERRANEAN_SOUTH'
  AND status = 'HELD_BACK';
```

---

## 💡 Conseils pour Optimiser les Réponses d'un Agent BigQuery

1. **Expliciter les Noms de Tables** : Mentionner `occupancy_daily` ou `booking_segments` dans le prompt aide l'agent LLM à cibler les bonnes tables immédiatement sans métadonnées ambiguës.
2. **Formules d'Agrégation** : Pour les agrégats de ratios (`RevPAR`, `Occupancy`), rappeler d'utiliser `SUM(num)/SUM(denom)` au lieu de `AVG(ratio)` évite les biais de moyenne pondérée.
3. **Filtres Temporels** : Utiliser le format ISO `YYYY-MM-DD` (ex: `2026-07-01` à `2026-07-31`) garantit un filtre SQL exact sur le champ `date`.
