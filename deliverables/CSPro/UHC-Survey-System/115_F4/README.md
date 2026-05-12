# 115_F4 — F4 Household Survey CAPI app

CAPI instrument for the **Household Survey** of UHC Year 2. Captures one case per sampled household, with one household-respondent answering on behalf of the unit plus a per-household-member roster (Section C, max 10 occurrences) and PhilHealth + private-insurance sub-rosters.

Source-of-truth instruments:
- `raw/Project-Deliverable-1_Apr20-submitted/Annex F4_Household Survey Questionnaire_UHC Year 2.pdf` (Apr 20 2026 Revised Inception Report submission). 202 numbered items, sections A–Q.
- `raw/2026-05-06-survey-manual-bundle/2026-05-06_Survey-Manual-Working-File-Kidd.docx` §3.4.2 (Household Survey field protocol; awaiting Myra's edit pass).
- `deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F4/generate_dcf.py` — archived pre-rebuild generator; code reference only — item labels re-verified against the Apr 20 PDF on each ingest into this rebuild.

## Position in the F-series pipeline

```
   F1 (facility head)     F3 (patient exit)
        |                       |
        +-----------+-----------+
                    |
                    v
              SAME FACILITY (RR+PP+MMM+FF shared)
                    |
                    v
   F4 sampling — two paths into the same case:
                    |
       (a) Barangay listing (PIDS sampling per Protocol V2 §3.4.2)
             via 113_F4_listing — emits HH_LISTING_NO per HH
                    |
       (b) F3 patient interval-walk (LISTING_TAG=2 path)
             via 110_F3_listing — emits parent F3 CASE_SEQ per HH
                    |
                    v
               115_F4 (this app)
                    |
                    v
             sync to CSWeb
```

## Cross-form linkage (Option C — dual fields)

F4's `FIELD_CONTROL` carries **both** linkage anchors so the entry app can handle either sampling path without retrofit:

| Field | Width | Source | Default when absent | Why both |
|---|---|---|---|---|
| `HH_LISTING_NO` | 4 (zero-fill) | 113_F4_listing barangay-listing app | always populated | Primary listing-roster anchor for PIDS barangay sampling (the protocol-conformant case for nearly all households). |
| `F4_PARENT_F3_CASE_SEQ` | 3 (zero-fill) | 110_F3_listing patient interval-walk (LISTING_TAG=2) | `999` (NA per F-series convention) | Optional F3 patient parent when F4 was reached via interval-walk. Future-proofs for the parallel sampling mode without DCF surgery later. |

F4 → F1 facility linkage falls out structurally from the shared first 9 digits of the case-ID (`RR+PP+MMM+FF`) — no separate `F4_FACILITY_ID` data item.

The dual-field architecture is documented in detail in `wiki/concepts/Questionnaire Numbering Convention.md` §"Cross-instrument linkage" so future agents do not re-litigate.

## Generator chain

```
generate_dcf.py   ->  HouseholdSurvey.dcf
generate_ent.py   ->  HouseholdSurvey.ent
generate_fmf.py   ->  HouseholdSurvey.fmf    (Designer-owned post-publish)
generate_apc.py   ->  HouseholdSurvey.apc    (logic; emitted to .ent.apc by Designer)
```

Run via `python ../build_all.py --env=dev --only=F4` once the entry is added to the `INSTRUMENTS` list in `build_all.py` (see end-of-phase wire-in commit).

## Section layout (17 top-level sections, 202 items)

| § | Title | Item range | Record type | Occurrences |
|---|---|---|---|---|
| A | Introduction and Informed Consent | Q1–Q28 (gating + respondent profile) | `C` | 1 |
| B | Respondent Profile | (continues through B-block) | `D` | 1 |
| C | Household Roster and Characteristics (C1–C5) | Q30–Q46 | `E` | up to 10 (per-member) |
|   | Private-Insurance HH gate (Q47) | Q47 | `T` | 1 |
|   | Private-Insurance roster (Q48–Q50) | Q48–Q50 | `U` | up to 10 |
| D | Awareness on Universal Health Care (UHC) | Q51 onward | `F` | 1 |
| E | YAKAP/Konsulta Awareness | per PDF | `G` | 1 |
| F | BUCAS Awareness and Utilization | per PDF | `H` | 1 |
| G | Access to Medicines | per PDF | `I` | 1 |
| H | PhilHealth Registration and Health Insurance | per PDF | `J` | 1 |
| I | Primary Care Utilization | per PDF | `K` | 1 |
| J | Household members' Health-Seeking Behavior and Outcomes | per PDF | `L` | 1 |
| K | Experiences and Satisfaction with Referrals | per PDF | `M` | 1 |
| L | NBB Awareness and Utilization | per PDF | `N` | 1 |
| M | ZBB Awareness and Utilization | per PDF | `O` | 1 |
| N | Household Expenditures (food, non-food, health products/services) | Q144–Q176 | `P` | 1 (roster-style items as fixed list) |
| O | Sources of Funds for Health | per PDF | `Q` | 1 |
| P | Financial Risk Protection: Incidence of Reduced/Delayed Care | per PDF | `R` | 1 |
| Q | Anxiety about Household Finances | per PDF | `S` | 1 |

Record types use uppercase letters A-Z; A–B reserved for FIELD_CONTROL + HOUSEHOLD_GEO_ID. GPS/photo capture records consume types `Z` / `X` / `Y` per the shared `_gps_fields()` / `_photo_block()` convention.

## "Do not ask" computed totals

Q177, Q182, Q185 are computed sums in CAPI ("computed automatically in CAPI" per the PDF). They appear as CSPro **derived items** in the DCF with a noteworthy spec comment; the PROC wiring lands at the F4 quartet phase (`generate_apc.py`).

## Case-ID block

5-item 12-digit decomposed case-ID per the adopted 2026-05-05 Questionnaire Numbering Convention. F4 uses `shared.cspro_helpers.build_id_block()` like F1 and F3. `CASE_SEQ` is scoped per-instrument per-facility, so F4 case 001 and F1 case 001 at the same facility do not collide — the dictionaries are separate.

## Line endings

See `.gitattributes` — Designer-owned binaries (.dcf, .fmf, .ent.apc, .ent.mgf, .ent.qsf) are pinned CRLF; generator-emitted sources (.py, .ent, .pff, .md) are pinned LF. Pattern parity with 107_F1, 110_F3_listing, and 111_F3.

## Status

Scaffolded 2026-05-12 per commit 1 of the F4 core DCF rebuild. Subsequent commits land DCF base records, then section pairs A–Q (split for cohesive review), then logic-pass spec doc, then build_all.py wire-in + smoke pass.
