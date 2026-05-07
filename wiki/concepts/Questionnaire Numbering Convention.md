---
type: concept
status: adopted
date_drafted: 2026-05-02
date_adopted: 2026-05-05
last_updated: 2026-05-05
tags: [capi, cspro, dictionary, case-id, questionnaire-numbering, working-convention, adopted]
source_count: 4
related_task: E7-DOC-001
---

# Questionnaire Numbering Convention

> **Status: ADOPTED 2026-05-05.** Carl approved the decomposed scheme on 2026-05-05 in response to Kidd's coding question. Width verification against PSA 1Q 2026 PSGC + Inception-Report Table 1 (same date) revised the proposal from 11 to **12 digits** because the PSGC city/municipality slot is 3 digits, not 2 — the manual's legacy `035401` example used the pre-2008 PSGC, while the F-series build is anchored on PSA 1Q 2026. The convention below reflects the adopted, verified widths. A brief for Kidd is at `deliverables/Survey-Manual/Case-ID-Convention-Brief_2026-05-05.{md,docx}`. Implementation footprint (cspro_helpers + F1/F3/F4 generators + F2 PWA case-ID issuer + manual addendum) remains pending sprint scheduling.

This document specifies the case-identifier (questionnaire-number) format for every instrument in the UHC Survey Year 2 — F1 (Facility Head, CSPro), F2 (Healthcare Worker, PWA), F3 (Patient, CSPro), F4 (Household, CSPro). It exists because the master Survey Manual (March 2026 / Apr 28 working version) prescribes a 9-digit composite that doesn't quite fit a multi-instrument health-facility survey, and because the current F-series dictionaries use a different shape (single 6-digit `QUESTIONNAIRE_NO` ID item) that under-specifies the case key.

## What the manual currently says

From `raw/DOH UHC Year 2_Survey Manual Apr 28.docx` → *Instructions for the Administration of the Questionnaire → The Survey Questionnaire → Questionnaire Number*:

> "The initial six (6) digits of the questionnaire number correspond to the numerical set representing the Region, Province, and Municipality to which the enumerator is assigned. … the enumerator records the respondent's number. For instance, if the enumerator is currently conducting their fourth interview of the day, the questionnaire number should be 035401004."

So: **9 digits = 6-digit PSGC (Region/Province/Municipality) + 3-digit per-day respondent counter**, with STLs preassigning sequence ranges to enumerators to prevent collisions.

## What the build currently has

- F1 / F3 / F4 dictionaries (`generate_dcf.py` for each) declare a single ID item:
  - `QUESTIONNAIRE_NO`, **numeric, length 6, zero-fill**
- Geographic data items (`REGION`, `PROVINCE_HUC`, `CITY_MUNICIPALITY`, `BARANGAY`) are populated at length 10 each (full PSA PSGC) via the `PSGC-Cascade.apc` shared lookup module — these are *data items* in `HEALTH_FACILITY_AND_GEOGRAPHIC_IDENTIFICATION` / `PATIENT_GEO_ID` / `HOUSEHOLD_GEO_ID`, not ID items.
- F3 carries a separate `F3_FACILITY_ID` (numeric, length 10) data item for F3↔F1 linkage.
- F2 (PWA) generates an opaque per-response identifier; not aligned with the F-series scheme.

The 6-digit `QUESTIONNAIRE_NO` doesn't map cleanly to either the manual's framing (which expects 6 PSGC + 3 sequence = 9 digits) or to the 10-digit PSGC items in the same dictionary. The current state is a workable placeholder, not an industry-aligned convention.

## Industry research summary (2026-05-02)

| Framework | Approach | Notes |
|---|---|---|
| **CSPro (US Census Bureau)** | Decomposed: ID items defined separately per conceptual level (e.g., Province / District / EA / Household), each with its own length and value set. ID items are placed first in the dictionary and appear on every record. | The MyCAPI sample app uses one ID item; multi-stage household samples typically use 4–5. Sources: CSPro 8.0 Users Guide → Data Dictionary → Identification Items (`csprousers.org/help/CSPro/identification_items.html`). |
| **DHS (Demographic and Health Surveys)** | Hybrid: HHID is a 15-character composite string for linking; decomposed components (HV001 cluster, HV002 household, HV003 line) also published in every recode file. | Composite for linking, decomposed for analysis. Source: DHS Standard Recode Manual; IPUMS-DHS HHID variable definition. |
| **MICS (UNICEF)** | Mirrors DHS shape in IPUMS-published files. No explicit single standard published. | — |
| **WHO SARA / facility surveys** | Facility code (pre-assigned by ministry of health) is the anchor, no per-respondent sequence at the case-ID level (one case per facility). | Facility surveys differ structurally from household surveys — facility is the unit, not a household roster. |

**Key insight for this survey:** UHC Year 2 is **multi-instrument and facility-anchored** — F1 is one-per-facility, F3/F2 are many-per-facility, F4 is patient-anchored interval-walked. A single 9-digit "PSGC + day-sequence" works fine for a household survey but is **insufficient here** because two F1 facilities in the same municipality collide on the 3-digit position, and there's no encoding for cross-instrument linkage at the same facility.

## Adopted convention: 12-digit decomposed scheme (PSA 1Q 2026 PSGC)

**12-digit composite case ID, stored as 5 separate ID items in the dictionary.** Composite display form is `RRPPMMMFFCCC` (zero-padded, no separators) — used in the data file. Dashed form `RR-PP-MMM-FF-CCC` is used in the manual, training, dashboards, and enumerator cards.

| ID item | Width | Range | Source / meaning |
|---|---|---|---|
| `REGION_CODE` | 2 | `01–19` | PSA 1Q 2026 PSGC region (positions 1–2 of the 10-digit PSGC) |
| `PROVINCE_HUC_CODE` | 2 | `00–99` | PSA 1Q 2026 PSGC province / HUC slot within region (positions 3–4) |
| `CITY_MUNICIPALITY_CODE` | 3 | `000–999` | PSA 1Q 2026 PSGC city / municipality slot within province (positions 5–7) |
| `FACILITY_NO` | 2 | `01–99` | ASPSI sampling-frame facility index within municipality |
| `CASE_SEQ` | 3 | `001–999` | Per-instrument case sequence within facility |

`CASE_SEQ` is **scoped per instrument per facility** — F1 case 001 and F3 case 001 at the same facility are not collisions because `RECORD_TYPE` already separates the dictionaries.

### Examples per instrument

Magalang, Pampanga in PSA 1Q 2026 PSGC: `RR=03`, `PP=05`, `MMM=411` (full mun PSGC = `0305411000`), 1st sampled facility (`FF=01`):

| Instrument | Case ID | Meaning |
|---|---|---|
| **F1 — Facility Head** | `030541101001` | One facility head per facility, so `CCC=001` always |
| **F2 — Healthcare Worker** | `030541101012` | 12th HCW respondent at this facility (target 4–53/facility) |
| **F3 — Patient** | `030541101027` | 27th patient at this facility (target ≤ 67 OP + 45 IP = 112) |
| **F4 — Household** | `030541101034` | 34th household interval-walked from a patient at this facility; the parent F3 case is recorded in a separate `F4_PARENT_F3_CASE_SEQ` data item |

### Why these widths (verified 2026-05-05)

- **Region 2** — verified: PSA 1Q 2026 has 18 active regions; max region code = 19. 2 digits sufficient.
- **Province 2** — verified: max within-region province slot = 99 (BARMM). 2 digits sufficient.
- **Municipality 3** — verified: max within-province municipality slot = 934; 73 of 80 provinces have at least one mun with slot ≥ 100. **2 digits is structurally insufficient — must be 3.** The manual's legacy `035401` example used pre-2008 nationally-sequential PSGC and does not decompose into PSA 1Q 2026; the case-ID is anchored to PSA 1Q 2026 because the F-series geographic data items already are.
- **Facility 2** — verified against Inception Report Table 1: max per-province sample = 53 (Bulacan, spread across muns); max per-HUC sample = 38 (Quezon City). Per-municipality count is bounded above by these and easily fits 2 digits. Kidd's own manual range-allocation table already uses ≤ 2-digit per-LGU ranges.
- **Case 3** — F3 ceiling per facility is 67 OP + 45 IP = 112; F4 ceiling per facility is bounded by patient-walk multipliers (well under 500); F2 is ≤ 53. 999 leaves headroom for replacements without colliding with active ranges.

### Replacement-protocol bookkeeping

The 3-digit `CASE_SEQ` cleanly handles the manual's *"refused/cancelled cases get a different number range"* rule, scoped per-facility instead of per-municipality:

- **Active range** — `001–699`, partitioned by STL across enumerators (e.g., Enumerator 1 → 001–050; Enumerator 2 → 051–100).
- **Replacement range** — `700–899`, drawn from the alternative-respondent list per [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol]].
- **Refused / forfeited range** — `900–999` for attempts that did not produce data (recorded for response-rate accounting; AAPOR disposition codes in `FIELD_CONTROL` capture the why).

### Cross-instrument linkage

- **F3 → F1** — derived structurally from the shared `REGION_CODE + PROVINCE_HUC_CODE + CITY_MUNICIPALITY_CODE + FACILITY_NO`. The current `F3_FACILITY_ID` (10-digit) data item becomes redundant and can be retired (or kept as a denormalized convenience field — leaning retire to avoid drift).
- **F2 → F1** — same: shared first 9 digits identify the facility.
- **F4 → F3** — not derivable from the case ID alone (F4 households aren't anchored on facility geography in the same way). Capture parent F3 patient sequence as a dedicated data item `F4_PARENT_F3_CASE_SEQ` (numeric, length 3) inside `HOUSEHOLD_GEO_ID`. This is exactly how DHS handles HHID → cluster/HH/line decomposition.

## Manual addendum (one paragraph)

Drops into *The Survey Questionnaire → Questionnaire Number*, replacing the existing 9-digit text:

> The questionnaire number is a **12-digit numeric identifier** anchored to the **Philippine Standard Geographic Code (PSGC), 1Q 2026 publication**. The first seven digits are the PSGC code (Region 2 + Province/HUC slot within region 2 + City/Municipality slot within province 3), the next two digits are the facility number assigned by ASPSI within that municipality, and the last three digits are the per-facility, per-instrument case sequence assigned by the STL. Example: `030541101012` = Region III (`03`), Pampanga (`05`), Magalang (`411`), 1st sampled facility (`01`), 12th case at that facility (`012`). Within each facility, sequence ranges 001–699 are used for active cases (sub-allocated by the STL across enumerators), 700–899 for replacement cases, and 900–999 for refused or forfeited cases.

## What changes under the adopted convention

| Today | After |
|---|---|
| `QUESTIONNAIRE_NO` (single 6-digit ID item) on F1 / F3 / F4 | 5 ID items totalling 12 digits on F1 / F3 / F4; the F2 PWA generates the same 12-digit form per response |
| `F3_FACILITY_ID` (10-digit data item) | Retired — facility identity is now in the ID item block |
| Geographic items `REGION` / `PROVINCE_HUC` / `CITY_MUNICIPALITY` / `BARANGAY` at 10 digits each (full PSA PSGC) | **Keep** — these stay as data items for joining with PSA / DOH datasets at full precision; the 2/2/3-digit ID items are the *within-parent* PSA 1Q 2026 codes derived from the same PSGC source |
| Manual specifies 9 digits (legacy 6-digit PSGC + 3 sequence) | Manual addendum: 12 digits (PSA 1Q 2026 7-digit PSGC + 2 facility + 3 case) — replaces the legacy PSGC slice entirely |

## Implementation footprint (pending sprint scheduling)

Adopted; not yet executed. When scheduled:

1. **`deliverables/CSPro/cspro_helpers.py`** — add `build_id_block()` returning the 5 ID items; extend `build_dictionary()` to accept an `id_items=` list (replacing the current `id_item_name` / `id_length` single-item path).
2. **`deliverables/CSPro/F1/generate_dcf.py`** — replace `id_item_name="QUESTIONNAIRE_NO" / id_length=6` with `id_items=build_id_block()`. Regenerate `FacilityHeadSurvey.dcf`.
3. **`deliverables/CSPro/F3/generate_dcf.py`** — same replacement; drop `F3_FACILITY_ID` from `PATIENT_GEO_ID` extras (or keep as denormalized convenience). Regenerate `PatientSurvey.dcf`.
4. **`deliverables/CSPro/F4/generate_dcf.py`** — same replacement; add `F4_PARENT_F3_CASE_SEQ` (numeric, length 3) to `HOUSEHOLD_GEO_ID`. Regenerate `HouseholdSurvey.dcf`.
5. **F2 PWA** — case-ID issuer at submission time concatenates the same 5 fields (facility is known per token; PWA assigns `CASE_SEQ` from the F2_HCWs roster index). Update `apps-script/` writer + Worker schema accordingly.
6. **Manual addendum** — paste the one-paragraph addendum (above) into the master manual; update `deliverables/Survey-Manual/CSPro-Section-Draft_2026-04-29.md` Section 4 open question #1 to point at this concept page; update `deliverables/Survey-Manual/CAPI-PWA-Stakeholder-Section_2026-05-02.md` §5 / §10 case-identifier mention.
7. **Logic ramifications** — verify F1/F3/F4 PROC code references to `QUESTIONNAIRE_NO` (search for the literal string); replace where needed.

Estimated effort: ~4–6 hours including regen + spot-check Designer open + PWA test.

## Decisions made on adoption (2026-05-05)

- **PSGC anchor:** PSA 1Q 2026 (matches the F-series build's geographic value sets). The Survey Manual's legacy `035401` worked example is superseded.
- **Width:** 12 digits (`RR-PP-MMM-FF-CCC`), not 11. The 3-digit municipality slot was confirmed against the actual PSA 1Q 2026 city/municipality CSV — 73 of 80 provinces have at least one mun with slot ≥ 100.
- **Storage shape:** 5 separate ID items, not 1 composite. Matches CSPro convention; enables Designer / CSWeb filtering by structural level.
- **`FACILITY_NO` scoping:** per-municipality (FF=2 digits), justified by Inception-Report Table 1 ceilings (max per-province sample = 53; max HUC = 38; per-mun strictly bounded by these).
- **`F3_FACILITY_ID`:** retired in favour of the ID-item block, to avoid drift.

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual]] — manual's existing 9-digit specification
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Dictionary]] — ID-item structure reference
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets]] — full 10-digit PSA PSGC source for the within-parent decomposition
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions]] — sibling project-internal coding rule (NA at highest code at field width)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol]] — replacement-protocol policy that the case-sequence range allocation operationalizes
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]] — CSPro decomposed ID convention
