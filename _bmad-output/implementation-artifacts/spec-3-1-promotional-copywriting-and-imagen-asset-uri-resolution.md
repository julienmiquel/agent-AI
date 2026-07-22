---
title: 'Story 3.1: Promotional Copywriting & Imagen Asset URI Resolution'
type: 'feature'
created: '2026-07-20'
status: 'done'
baseline_revision: 'ff662d12804c5a6c74813f396992b3a837cb3497'
final_revision: 'ff662d12804c5a6c74813f396992b3a837cb3497'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/project-context.md', '_bmad-output/implementation-artifacts/epic-3-context.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** Regional Operations Managers currently lack automated localized promo copywriting (in Dutch, French, German) and resolved Imagen asset GCS URIs when staging marketing campaigns for lagging market segments.

**Approach:** Implement `generate_promotional_copy` and `resolve_imagen_asset_uri` in `src/agents/marketing_campaign.py`, generating localized ad copy (Dutch, French, German) based on session context (`target_market`, `target_cluster`), attaching valid GCS Imagen asset URIs (`gs://ecg-marketing-assets/genai/banners/{market}_{cluster}_july.png`), and integrating these into `crm_create_flash_campaign` and `Marketing_Campaign_Agent.process_turn`.

## Boundaries & Constraints

**Always:**
- Generate localized ad copy for target market codes (`NL`: Dutch, `FR`: French, `DE`: German, Default: English/French).
- Resolve valid GCS Imagen asset URIs formatted as `gs://ecg-marketing-assets/genai/banners/{market}_{cluster}_july.png`.
- Model selection: `gemini-2.5-pro` (`MODEL_MARKETING`) for copywriting assembly.
- Preserve session state (`target_market`, `target_cluster`, `campsite_id`).

**Block If:**
- Target market code or GCS URI format is invalid or empty.

**Never:**
- Hardcode generic unlocalized French fallback text when session target market is explicitly specified (e.g., `NL` or `DE`).
- Fail to return structured `MARKETING_CAMPAIGN_DRAFT` widget payload.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Dutch Promo Copywriting Generation | `target_market: "NL"`, `cluster: "MEDITERRANEAN_SOUTH"` | Returns Dutch ad text ("Profiteer van 15% korting...") and GCS URI `gs://ecg-marketing-assets/genai/banners/nl_mediterranean_south_july.png` | Fallback to English/French if market unknown |
| German Promo Copywriting Generation | `target_market: "DE"`, `cluster: "MEDITERRANEAN_SOUTH"` | Returns German ad text ("Sichern Sie sich 15% Rabatt...") and GCS URI `gs://ecg-marketing-assets/genai/banners/de_mediterranean_south_july.png` | Handles unhandled market gracefully |
| Null Prompt / Empty Market | `prompt: ""` or missing `target_market` | Uses default `NL` market context or returns structured validation error | Returns structured validation payload |

</intent-contract>

## Code Map

- `src/config.py` -- GCS marketing bucket configuration (`GCS_MARKETING_BUCKET`, `MODEL_MARKETING`).
- `src/agents/marketing_campaign.py` -- `generate_promotional_copy`, `resolve_imagen_asset_uri`, `crm_create_flash_campaign`, and `Marketing_Campaign_Agent.process_turn`.
- `tests/test_marketing_campaign.py` -- Unit tests validating localized promo copywriting, Imagen GCS URI resolution, parameter validation, and supervisor session routing.

## Tasks & Acceptance

**Execution:**
- [x] `src/agents/marketing_campaign.py` -- Implement `generate_promotional_copy` and `resolve_imagen_asset_uri` helper functions -- Enables localized copywriting and GCS Imagen URI resolution.
- [x] `src/agents/marketing_campaign.py` -- Integrate localized copy and Imagen URI into `crm_create_flash_campaign` tool and `Marketing_Campaign_Agent.process_turn` -- Stagers flash campaigns with assembled assets.
- [x] `tests/test_marketing_campaign.py` -- Add unit tests for localized copywriting (NL, FR, DE), Imagen asset URI resolution, and CRM widget payloads -- Verifies copywriting and asset resolution.

**Acceptance Criteria:**
- Given a request to stage a flash campaign for Dutch past guests in Mediterranean South, when `Marketing_Campaign_Agent` is invoked, then the agent generates localized Dutch promo copy ("Profiteer van 15% korting...") and attaches resolved Imagen GCS asset URI (`gs://ecg-marketing-assets/genai/banners/nl_mediterranean_south_july.png`).

## Spec Change Log

*(No spec amendments required)*

## Review Triage Log

### 2026-07-20 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 4 (high 2, medium 2, low 0)
- defer: 0
- reject: 0
- addressed_findings:
  - `[high]` `[patch]` Added `str()` and `.strip()` type safety guards in `generate_promotional_copy()` and `resolve_imagen_asset_uri()`.
  - `[high]` `[patch]` Extracted discount percentage from user prompt in `Marketing_Campaign_Agent.process_turn()`.
  - `[medium]` `[patch]` Added `discount_percentage` bounds validation (`0 <= discount <= 100`) in `crm_create_flash_campaign()`.
  - `[medium]` `[patch]` Added space-to-underscore replacement in `resolve_imagen_asset_uri()` for valid GCS URIs.

## Verification

**Commands:**
- `python3 -m pytest tests/test_marketing_campaign.py` -- expected: all marketing campaign unit tests pass.
- `python3 -m pytest tests/` -- expected: full test suite passes.
