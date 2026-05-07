# Questionnaire Number (Case-ID) Convention — Brief for the Survey Manual

**From:** Carl Patrick L. Reyes, Data Programmer
**To:** Kidd, Lead Research Associate
**Date:** 2026-05-05
**Re:** Coding the questionnaire number for CAPI (CSPro) and the F2 PWA — proposed convention for Survey Manual integration

---

## 1. The concern you raised

You flagged that:

1. The coding needs to be set **per response** (per completed questionnaire), so that no two questionnaires can ever share an identifier.
2. Our sample list is **per facility**, but each facility produces **multiple responses** — multiple Healthcare Workers in F2, multiple patients in F3, multiple households in F4.
3. From past experience, **CAPI tends to merge responses if they are not coded**, and that's the failure mode you want to design out.

Your instinct is correct. CSPro and CSWeb merge two cases into one row if they share a case-ID. The fix is to make collisions **structurally impossible** — not just administratively prevented through a range-allocation table.

This brief proposes a convention that does that, and that fits how CSPro CAPI applications are conventionally built.

---

## 2. Proposed convention — 12-digit decomposed case-ID

**Format:** `RR-PP-MMM-FF-CCC` (stored as 12 digits, no separators; the dashed form is for human display only — training materials, dashboards, enumerator cards.)

| Position | Field | Width | Range | Source |
|---|---|---|---|---|
| 1 | `REGION_CODE` | 2 | `01–19` | PSA 1Q 2026 PSGC region |
| 2 | `PROVINCE_HUC_CODE` | 2 | `00–99` | PSA 1Q 2026 PSGC province / HUC slot within region (positions 3–4 of the 10-digit PSGC) |
| 3 | `CITY_MUNICIPALITY_CODE` | 3 | `000–999` | PSA 1Q 2026 PSGC city / municipality slot within province (positions 5–7 of the 10-digit PSGC) |
| 4 | `FACILITY_NO` | 2 | `01–99` | ASPSI sample-frame index for the facility *within the municipality* |
| 5 | `CASE_SEQ` | 3 | `001–999` | Per-facility, per-instrument case sequence assigned by the STL |

The first seven digits (`RR-PP-MMM`) are the **PSA 1Q 2026 PSGC** slice that uniquely identifies the municipality — the same value already used by the F1 cascading geographic selector and the F-series geographic data items. The convention extends the manual's existing 9-digit specification by **three digits**: one extra digit on the municipality slot (PSA 1Q 2026 uses 3 digits where the manual's legacy example used 2) and two digits for the per-municipality facility number, so multiple facilities sampled in the same municipality remain distinct.

> **Note on PSGC version.** The manual's legacy worked example (`035401` for Magalang, Pampanga) reflects an older nationally-sequential PSGC that PSA superseded. PSA 1Q 2026 uses a within-region slot for province (Pampanga = `05`, not `54`) and a 3-digit within-province slot for municipality (Magalang = `411`, not `01`). The CAPI dictionaries already use PSA 1Q 2026; the case-ID is anchored to the same source so geography in the case-ID matches geography in the data items by construction.

### How this differs from a range-allocation table per LGU

A range-allocation table (e.g., Manila = cases 001–026, Mandaluyong = cases 001–013) is workable, but introduces three risks that the decomposed scheme eliminates:

| Risk under range-allocation | Resolution under the decomposed scheme |
|---|---|
| Range exhaustion if a facility produces more cases than allocated | `CASE_SEQ` runs to 999 per facility per instrument — well above any expected count |
| Two enumerators can both type the same number and collide (depends on humans following the table) | Collision is impossible by construction — `FF` and `RECORD_TYPE` separate every case |
| The case-ID alone doesn't tell you which facility the case came from | The case-ID itself encodes geography and facility; no lookup table needed to decode it |

---

## 3. Worked example — Magalang, Pampanga (RR=03, PP=05, MMM=411)

Two sampled facilities. The table walks through F1, F2, F3, F4 cases including a replacement case and a refused case. PSGC values are PSA 1Q 2026.

| # | Case ID | Decoded | Instrument | Facility | Respondent / unit | Notes |
|---|---|---|---|---|---|---|
| 1 | `030541101001` | 03-05-411-01-001 | F1 Facility Head | Magalang RHU | The facility head | F1 always uses `CCC=001` (one head per facility) |
| 2 | `030541101001` | 03-05-411-01-001 | F2 Healthcare Worker | Magalang RHU | 1st HCW respondent | Same numeric ID as F1 row 1, but `RECORD_TYPE` separates the two instruments — they live in different dictionaries and do not collide |
| 3 | `030541101007` | 03-05-411-01-007 | F2 Healthcare Worker | Magalang RHU | 7th HCW respondent | Active range |
| 4 | `030541101023` | 03-05-411-01-023 | F3 Patient | Magalang RHU | 23rd patient (outpatient) | Active range |
| 5 | `030541101055` | 03-05-411-01-055 | F3 Patient | Magalang RHU | 55th patient (inpatient) | Active range |
| 6 | `030541101012` | 03-05-411-01-012 | F4 Household | Magalang RHU | 12th household interval-walked from a sampled patient | Linked to F3 case `023` via the `F4_PARENT_F3_CASE_SEQ` data item (see §6) |
| 7 | `030541101701` | 03-05-411-01-701 | F3 Patient | Magalang RHU | 1st replacement patient | Replacement range (700–899) — drawn after a refusal; see §4 |
| 8 | `030541101901` | 03-05-411-01-901 | F2 Healthcare Worker | Magalang RHU | 1st refused HCW attempt | Refused range (900–999) — recorded for response-rate accounting; AAPOR disposition is captured in the `FIELD_CONTROL` block |
| 9 | `030541102001` | 03-05-411-02-001 | F1 Facility Head | Magalang District Hosp. | Facility head at the 2nd sampled facility | `FF=02` distinguishes from row 1 — same municipality, different facility |
| 10 | `030541102015` | 03-05-411-02-015 | F3 Patient | Magalang District Hosp. | 15th patient at the 2nd facility | Shares `RR-PP-MMM` with row 5 but differs in `FF` — no merge |
| 11 | `138060001008` | 13-80-600-01-008 | F2 Healthcare Worker | (City of Manila example) | 8th HCW at the 1st sampled Manila facility | Manila PSGC `1380600000` → RR=13, PP=80, MMM=600. Different geographic prefix entirely; included to show how the scheme decomposes across regions |

Rows 5, 7, and 10 jointly demonstrate the design's value. Three F3 cases that *would* have looked similar under range-allocation (case "023", case "701", case "015") are structurally distinct here because the `FF` field and the active/replacement/refused band keep them apart at the level of the case-ID itself.

---

## 4. `CASE_SEQ` range partitioning per facility per instrument

The 3-digit `CASE_SEQ` is partitioned to operationalize the manual's existing replacement-protocol rule that *"refused or cancelled cases are assigned a different number range"*:

| Range | Use | Notes |
|---|---|---|
| `001–699` | **Active cases** | Sub-allocated by the STL across enumerators (e.g., Enumerator 1: 001–050; Enumerator 2: 051–100) |
| `700–899` | **Replacement cases** | Drawn from the alternative-respondent list per the Annex D Replacement Protocol |
| `900–999` | **Refused / forfeited cases** | For attempts that did not produce data — recorded for response-rate accounting; AAPOR disposition codes captured in `FIELD_CONTROL` |

The partitioning is per facility and per instrument. So F3 at Magalang RHU has its own 001–699 / 700–899 / 900–999 set, distinct from F3 at Magalang District Hospital, distinct from F2 at either facility.

---

## 5. What enumerators actually do in the field

The 12-digit case-ID is **generated by the application**, not typed by the enumerator. Enumerators do not memorize or type 12 digits. The flow is:

1. **Open a new case in CSPro CAPI (or the F2 PWA).**
2. **Select the facility** from a cascading geographic lookup: Region → Province/HUC → City/Municipality → Facility. The lookup is pre-loaded with the ASPSI sample-frame master facility list.
3. **The application auto-populates `RR`, `PP`, `MM`, and `FF`** from that selection — four of the five ID items are filled in by lookup.
4. **The application auto-increments `CCC`** within the active sub-range pre-assigned to that enumerator by the STL. For replacement or refused cases, the enumerator selects the case type and the application picks the next number from the 700–899 or 900–999 band instead.
5. **The full 12-digit case-ID is displayed for the enumerator's reference** on the case header, and is recorded on the printed case envelope for paper backup.

The Survey Manual should describe this flow in the *Initial Health Facility Visit* and *Survey Questionnaire* sections so enumerators understand what the case-ID is and why they should not attempt to enter or modify it manually.

---

## 6. Cross-instrument linkage

Because the first 9 digits of every case-ID at a given facility are identical, the case-ID itself functions as the join key across instruments at the same facility:

| Instrument | Example case ID | Shared facility key (first 9 digits) | Tail (`CCC`) |
|---|---|---|---|
| F1 Facility Head | `030541101001` | `030541101` | `001` |
| F2 Healthcare Worker (1st) | `030541101001` | `030541101` | `001` |
| F2 Healthcare Worker (12th) | `030541101012` | `030541101` | `012` |
| F3 Patient (27th) | `030541101027` | `030541101` | `027` |
| F4 Household (34th) | `030541101034` | `030541101` | `034` (linked to F3 case `027` via `F4_PARENT_F3_CASE_SEQ`) |

To find every case at this facility across all 4 instruments at analysis time, an analyst filters on `LEFT(case_id, 9) = '030541101'`. No external lookup table is required.

The F4↔F3 link (which household was interval-walked from which patient) is **not derivable from the case-ID alone**, because F4 households are not anchored on the facility's geography in the same way. Instead, F4 carries a dedicated 3-digit data item, `F4_PARENT_F3_CASE_SEQ`, which records the `CCC` of the parent F3 patient at the same facility. This is exactly how DHS handles the equivalent linkage in its standard recode files.

---

## 7. Drop-in addendum for the Survey Manual

The following paragraph can be inserted directly into the *Survey Questionnaire → Questionnaire Number* section of the master Survey Manual, replacing the existing 9-digit text:

> The questionnaire number is a **12-digit numeric identifier** anchored to the **Philippine Standard Geographic Code (PSGC), 1Q 2026 publication**. The first seven digits are the PSGC code (Region, 2 digits; Province or HUC slot within region, 2 digits; City or Municipality slot within province, 3 digits), the next two digits are the facility number assigned by ASPSI within that municipality, and the last three digits are the per-facility, per-instrument case sequence assigned by the STL. Example: `030541101012` = Region III (`03`), Pampanga (`05`), Magalang (`411`), 1st sampled facility (`01`), 12th case at that facility (`012`). Within each facility, sequence ranges 001–699 are reserved for active cases (sub-allocated by the STL across enumerators), 700–899 for replacement cases drawn from the alternative-respondent list, and 900–999 for refused or forfeited attempts. The questionnaire number is generated automatically by the CAPI application from the facility selection and the case type — enumerators do not type the questionnaire number manually.

---

## 8. Items that need your input

A few decisions are sensible for ASPSI's field-operations team to weigh in on, rather than the Data Programmer deciding unilaterally:

1. **`CASE_SEQ` band sizes.** The proposed split is 001–699 / 700–899 / 900–999. Are these reasonable for the expected per-facility case volumes (F2 target 4–53/facility; F3 ceiling ≈ 67 OP + 45 IP; F4 driven by patient-walk multipliers), or do you want a different cut point?
2. **STL sub-allocation policy.** Within the 001–699 active range, how should the STL pre-divide the band across enumerators at a facility? The convention supports any partitioning (e.g., 50 per enumerator, equal share, or proportional to expected effort) — the ASPSI field-operations team owns this rule.
3. **Refused-case disposition.** Should every refused attempt get a `CCC` in the 900–999 band, or only those with completed AAPOR disposition codes? This is a small operational choice that affects how response rates are computed.
4. **Survey Manual placement.** The drop-in addendum in §7 is written for the *Survey Questionnaire → Questionnaire Number* section. Let me know if you'd prefer it placed elsewhere (e.g., in a dedicated *CAPI Conventions* annex), and I'll adjust the framing.

---

## 9. Implementation status

The CAPI dictionaries (F1, F3, F4) and the F2 PWA case-ID issuer will be updated to match this convention once the open items in §8 are resolved. The change is contained — the existing geographic data items and PSGC value sets remain unchanged — and is expected to be completed within the current sprint. The Survey Manual addendum in §7 can be incorporated independently of the CAPI build update; both will be in place before the next pilot.

Please send any questions or comments by reply on Viber or by message in the CAPI Viber group.
