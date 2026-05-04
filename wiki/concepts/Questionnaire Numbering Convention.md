---
type: concept
status: proposed-recommendation-pending-decision
date_drafted: 2026-05-02
last_updated: 2026-05-02
tags: [capi, cspro, dictionary, case-id, questionnaire-numbering, working-convention, proposed]
source_count: 4
related_task: E7-DOC-001
---

# Questionnaire Numbering Convention

> **Status: PROPOSED — pending Carl's decision.** This page captures the full discussion from 2026-05-02 (research → recommendation → trade-offs → implementation impact). Nothing in `cspro_helpers.py`, the F-series generators, the F2 PWA, or the master Survey Manual has been changed. When Carl is ready to lock in (or reject) the proposal, this page becomes the canonical reference and the convention is applied across the F-series + F2.

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

## Recommendation: 11-digit decomposed scheme

**11-digit composite case ID, stored as 5 separate ID items in the dictionary.** Composite display form is `RRPPMMFFCCC` (zero-padded, no separators) — used in the manual, training, dashboards, and enumerator cards.

| ID item | Width | Range | Source / meaning |
|---|---|---|---|
| `REGION_CODE` | 2 | `01–17` | PSGC region (PSA 1Q 2026) |
| `PROVINCE_HUC_CODE` | 2 | `01–99` | PSGC province / HUC within region |
| `CITY_MUNICIPALITY_CODE` | 2 | `01–99` | PSGC city / municipality within province |
| `FACILITY_NO` | 2 | `01–99` | ASPSI sampling-frame facility index within municipality |
| `CASE_SEQ` | 3 | `001–999` | Per-instrument case sequence within facility |

`CASE_SEQ` is **scoped per instrument per facility** — F1 case 001 and F3 case 001 at the same facility are not collisions because `RECORD_TYPE` already separates the dictionaries.

### Examples per instrument

Magalang, Pampanga (the manual's worked example: `RR=03`, `PP=54`, `MM=01`), 1st sampled facility (`FF=01`):

| Instrument | Case ID | Meaning |
|---|---|---|
| **F1 — Facility Head** | `03540101001` | One facility head per facility, so `CCC=001` always |
| **F2 — Healthcare Worker** | `03540101012` | 12th HCW respondent at this facility (target 4–53/facility) |
| **F3 — Patient** | `03540101027` | 27th patient at this facility (target ≤ 67 OP + 45 IP = 112) |
| **F4 — Household** | `03540101034` | 34th household interval-walked from a patient at this facility; the parent F3 case is recorded in a separate `F4_PARENT_F3_CASE_SEQ` data item |

### Why these widths

- **Region 2 / Province 2 / Municipality 2** — PSGC's standard nested width inside each parent. The manual already uses exactly this slice (`035401` for Magalang). Don't lengthen — the full 10-digit PSA PSGC stays in the existing geo data items where it belongs (joinable with PSA / DOH datasets at full precision).
- **Facility 2** — per-municipality sampled-facility counts in Annex B/C max well below 99; verified against the per-province "Sample Health Facility" column of the manual's allocation table.
- **Case 3** — F3 ceiling per facility is 67 OP + 45 IP = 112; F4 ceiling per facility is bounded by patient-walk multipliers (well under 500); F2 is ≤ 53. 999 leaves headroom for replacements without colliding with active ranges.

### Replacement-protocol bookkeeping

The 3-digit `CASE_SEQ` cleanly handles the manual's *"refused/cancelled cases get a different number range"* rule, scoped per-facility instead of per-municipality:

- **Active range** — `001–699`, partitioned by STL across enumerators (e.g., Enumerator 1 → 001–050; Enumerator 2 → 051–100).
- **Replacement range** — `700–899`, drawn from the alternative-respondent list per [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol]].
- **Refused / forfeited range** — `900–999` for attempts that did not produce data (recorded for response-rate accounting; AAPOR disposition codes in `FIELD_CONTROL` capture the why).

### Cross-instrument linkage

- **F3 → F1** — derived structurally from the shared `REGION_CODE + PROVINCE_HUC_CODE + CITY_MUNICIPALITY_CODE + FACILITY_NO`. The current `F3_FACILITY_ID` (10-digit) data item becomes redundant and can be retired (or kept as a denormalized convenience field — leaning retire to avoid drift).
- **F2 → F1** — same: shared first 8 digits identify the facility.
- **F4 → F3** — not derivable from the case ID alone (F4 households aren't anchored on facility geography in the same way). Capture parent F3 patient sequence as a dedicated data item `F4_PARENT_F3_CASE_SEQ` (numeric, length 3) inside `HOUSEHOLD_GEO_ID`. This is exactly how DHS handles HHID → cluster/HH/line decomposition.

## Manual addendum (one paragraph)

Drops into *The Survey Questionnaire → Questionnaire Number*, replacing the existing 9-digit text:

> The questionnaire number is an **11-digit numeric identifier**: the first six digits are the PSGC code (Region 2 + Province/HUC 2 + City/Municipality 2), the next two digits are the facility number assigned by ASPSI within that municipality, and the last three digits are the per-facility case sequence assigned by the STL. Example: `03540101012` = Region III, Pampanga, Magalang, 1st sampled facility, 12th case at that facility. Within each facility, sequence ranges 001–699 are used for active cases (sub-allocated by the STL across enumerators), 700–899 for replacement cases, and 900–999 for refused or forfeited cases.

## What changes if this is adopted

| Today | After |
|---|---|
| `QUESTIONNAIRE_NO` (single 6-digit ID item) on F1 / F3 / F4 | 5 ID items totalling 11 digits on F1 / F3 / F4; the F2 PWA generates the same 11-digit form per response |
| `F3_FACILITY_ID` (10-digit data item) | Retired — facility identity is now in the ID item block |
| Geographic items `REGION` / `PROVINCE_HUC` / `CITY_MUNICIPALITY` / `BARANGAY` at 10 digits each (full PSA PSGC) | **Keep** — these stay as data items for joining with PSA / DOH datasets at full precision; the 2-digit ID items are the *within-parent* codes derived from the same PSGC source |
| Manual specifies 9 digits (6 PSGC + 3 sequence) | Manual addendum: extend to 11 digits (6 PSGC + 2 facility + 3 case) — a 2-digit insertion, not a redesign |

## Implementation footprint (not done)

If/when Carl says go:

1. **`deliverables/CSPro/cspro_helpers.py`** — add `build_id_block()` returning the 5 ID items; extend `build_dictionary()` to accept an `id_items=` list (replacing the current `id_item_name` / `id_length` single-item path).
2. **`deliverables/CSPro/F1/generate_dcf.py`** — replace `id_item_name="QUESTIONNAIRE_NO" / id_length=6` with `id_items=build_id_block()`. Regenerate `FacilityHeadSurvey.dcf`.
3. **`deliverables/CSPro/F3/generate_dcf.py`** — same replacement; drop `F3_FACILITY_ID` from `PATIENT_GEO_ID` extras (or keep as denormalized convenience). Regenerate `PatientSurvey.dcf`.
4. **`deliverables/CSPro/F4/generate_dcf.py`** — same replacement; add `F4_PARENT_F3_CASE_SEQ` (numeric, length 3) to `HOUSEHOLD_GEO_ID`. Regenerate `HouseholdSurvey.dcf`.
5. **F2 PWA** — case-ID issuer at submission time concatenates the same 5 fields (facility is known per token; PWA assigns `CASE_SEQ` from the F2_HCWs roster index). Update `apps-script/` writer + Worker schema accordingly.
6. **Manual addendum** — paste the one-paragraph addendum (above) into the master manual; update `deliverables/Survey-Manual/CSPro-Section-Draft_2026-04-29.md` Section 4 open question #1 to point at this concept page; update `deliverables/Survey-Manual/CAPI-PWA-Stakeholder-Section_2026-05-02.md` §5 / §10 case-identifier mention.
7. **Logic ramifications** — verify F1/F3/F4 PROC code references to `QUESTIONNAIRE_NO` (search for the literal string); replace where needed.

Estimated effort: ~4–6 hours including regen + spot-check Designer open + PWA test.

## Open trade-offs (for Carl's decision)

- **9-digit (manual literal) vs 11-digit (recommended)** — adopting the manual literal preserves zero ASPSI-side rework but caps the survey at one facility per municipality, breaks F1↔F3↔F2 linkage encoding, and locks in a household-survey shape on a facility-anchored survey. Cost of the 11-digit upgrade is one paragraph of manual addendum + the dictionary regen; gain is correct multi-instrument behaviour and CSPro/DHS alignment.
- **5 separate ID items vs 1 composite ID item** — separate items (recommended) match CSPro convention and enable Designer / CSWeb filtering by structural level; a single 11-digit composite ID item works but loses metadata. CSPro inflates every record with all 5 fields, which is the right model (small storage cost; large queryability gain).
- **Retire `F3_FACILITY_ID` vs keep as denormalized field** — retiring is cleaner; keeping is defensive against analysts who want a single-column facility key without joining on 4 ID columns. Lean retire.

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual]] — manual's existing 9-digit specification
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Dictionary]] — ID-item structure reference
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets]] — full 10-digit PSA PSGC source for the within-parent decomposition
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions]] — sibling project-internal coding rule (NA at highest code at field width)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol]] — replacement-protocol policy that the case-sequence range allocation operationalizes
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]] — CSPro decomposed ID convention
