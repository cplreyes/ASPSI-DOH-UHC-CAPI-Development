---
type: spec
project: ASPSI-DOH-CAPI-CSPro-Development
deliverable: F4 Household Survey — CAPI logic spec
date_created: 2026-05-12
status: draft
source_questionnaire: raw/Project-Deliverable-1_Apr20-submitted/Annex F4_Household Survey Questionnaire_UHC Year 2.pdf
source_dcf: deliverables/CSPro/UHC-Survey-System/115_F4/HouseholdSurvey.dcf
predecessor: deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F4/F4-Skip-Logic-and-Validations.md
tags: [cspro, capi, skip-logic, validations, f4, rebuild]
---

# F4 Household Survey — Skip Logic and Validations Spec

Source-of-truth for CSPro CAPI logic on `HouseholdSurvey.dcf` (24 records / 659 items). All Q-numbers refer to the **Apr 20 printed Annex F4** (Q1–Q202); DCF item names follow the `Q{n}_*` convention.

> **Predecessor** — supersedes the archived pre-rebuild logic spec at `deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F4/F4-Skip-Logic-and-Validations.md`. The archived spec remains code reference for PROC patterns; this doc updates references to the post-rebuild item names, the new 12-digit case-ID block, and the Option C dual-linkage fields (`HH_LISTING_NO` + `F4_PARENT_F3_CASE_SEQ`).

## Rebuild deltas vs. the archived spec

| Topic | Pre-rebuild | Post-rebuild |
|---|---|---|
| Case ID | Single `QUESTIONNAIRE_NO` (6-digit) | 5-item 12-digit block (`REGION_CODE`, `PROVINCE_HUC_CODE`, `CITY_MUNICIPALITY_CODE`, `FACILITY_NO`, `CASE_SEQ`) via `build_id_block()` |
| F1 linkage | Implicit | Derives from the shared first 9 digits of the case-ID (RR+PP+MMM+FF) |
| F3 linkage | None | `F4_PARENT_F3_CASE_SEQ` (length 3, defaults to 999=NA) in FIELD_CONTROL |
| F4 listing-roster linkage | None | `HH_LISTING_NO` (length 4, always populated from 113_F4_listing barangay listing) in FIELD_CONTROL |
| FIELD_CONTROL | Hand-rolled | Shared `build_field_control(survey_code="F4", date_label_entity="the Household")` + Option C dual-linkage extras (above) |
| HOUSEHOLD_GEO_ID | 11 items (with embedded F4_FACILITY_ID + F4_PARENT_F3_CASE_SEQ + LATITUDE/LONGITUDE) | 6 items (CLASSIFICATION + 4 PSGC + HH_ADDRESS only). GPS lives in REC_HOUSEHOLD_CAPTURE; linkage in FIELD_CONTROL |
| C section | One record max_occurs=20 carrying Q30-Q50 mixed (HH-roster + private insurance roster mashed together) | Three records: C_HOUSEHOLD_ROSTER (max_occurs=10, Q30-Q46 only), C_PRIVATE_INSURANCE_GATE (max_occurs=1, Q47 HH-level), C_PRIVATE_INSURANCE_ROSTER (max_occurs=10, Q48-Q50) |
| Section N | Hand-rolled item-by-item | Helper-built 4-tuple quads (`_expenditure_quad()`) keep the section file readable; 4 computed totals stored as data items |

---

## 1. Sanity-check findings (Apr 20 PDF ingest)

| # | Item | Issue | Disposition |
|---|---|---|---|
| 1 | **Q19 vs C_HOUSEHOLD_ROSTER occurrences** | PDF says "For the enumerator: please check that total number is equal to number answered in Q19". Hard consistency check: count of populated C_HOUSEHOLD_ROSTER occurrences must equal Q19_HH_SIZE | HARD consistency rule §3 |
| 2 | **Q18 amount + bracket duality** | Captures both a free-entry numeric (`Q18_INCOME_AMOUNT`) AND a ticked bracket (`Q18_INCOME_BRACKET`). Hard consistency check: amount must fall in bracket | HARD consistency rule §3 |
| 3 | **Q2.1 confirmed age vs Q2 birth year** | PDF Q2.1 is "Just to confirm, how old are you as of your last birthday (in years)?" derived from Q2 month/year. Hard consistency check: `\|Q2_1_AGE - (current_year - Q2_BIRTH_YEAR)\| <= 1` | HARD consistency rule §3 |
| 4 | **Q32 age** rows in C_HOUSEHOLD_ROSTER | "Do not ask; see answer to Q2.1" for row 1 (respondent). Auto-fill row-1 Q32 from FIELD_CONTROL.Q2_1 -- enumerator confirms not types | Auto-fill PROC §3 Section C row 1 |
| 5 | **Q33 sex** rows in C_HOUSEHOLD_ROSTER | "Do not ask; see answer to Q3" for row 1 (respondent). Auto-fill row-1 Q33 from FIELD_CONTROL.Q3 | Auto-fill PROC §3 Section C row 1 |
| 6 | **Q34 relationship to head** row 1 | "Do not ask" for row 1. If Q1_IS_HH_HEAD = Yes (1), auto-fill row-1 Q34 = "Head" (01); otherwise row 1 = respondent's actual relationship to head | Auto-fill PROC §3 Section C row 1 |
| 7 | **Q15 IP_GROUP specify** | PDF says "A list will be provided to ensure accurate details" but none is included. Retain alpha until ASPSI provides codes | Flag for ASPSI; alpha as default |
| 8 | **Q64 / Q73 medication lists** | Both `alpha(length=512)`. Monitor during pilot — if respondents routinely list >512 chars, convert to a roster record | Monitor |
| 9 | **Q67, Q95 travel time HH:MM** | Both stored as length-5 alpha. Form-handler validates the `HH:MM` regex; PROC consistency: HH ∈ [0,23], MM ∈ [0,59] | HARD range §3 |
| 10 | **Q131 conditional gate** | PDF "Ask only if they went to a DOH-retained hospital" — Q131 only when Q130 = DOH-retained (2). When Q130 = Public or Private, Q131 skipped + LIST | GATE rule §3 Section L |
| 11 | **Q135 conditional gate** | Same shape as Q131 — only when Q130 = DOH-retained (2) | GATE rule §3 Section M |
| 12 | **Q136 PDF text inconsistency** | PDF says "(SKIP iF ANSWERED MAIFIP IN Q113)" but Q113 is referral-not-visiting reasons and has no MAIFIP option. Likely transcription artifact from prior questionnaire version | > [!note] Doc-level discrepancy; revisit after Myra's edit pass. PROC treats as no-op for MVP. |
| 13 | **Q141.1 numbering style** | PDF uses "141.1" (dotted). DCF item name uses underscore: `Q141_1_NO_RECEIPT_AMOUNT` | No action — internal convention |
| 14 | **Q157 / Q177 / Q182 / Q185 computed totals** | PDF marks "[DO NOT ASK] computed automatically in CAPI". Stored as data items with PROC fill logic at quartet phase; the form's onfocus handler skips them | Auto-compute PROC §3 Section N |
| 15 | **Q200 / Q201 "end of survey" terminators** | Q200 = Refused (4) -> end; Q201 = Not worried at all (4) -> end. Set ENUM_RESULT_FINAL_VISIT accordingly | PROC §3 Section Q |
| 16 | **F4_PARENT_F3_CASE_SEQ default** | Defaults to 999 (NA per F-series convention) when F4 sampled via barangay listing (the protocol-conformant case). Populated only on the 110_F3_listing patient-interval-walk path | Init in preproc; document in concept page (done in commit 11) |
| 17 | **HH_LISTING_NO required when sampling mode is "barangay listing"** | Always populated from 113_F4_listing app's roster occurrence; CSPro `required` flag stays True | HARD required §3 FIELD_CONTROL |
| 18 | **Section H gate on respondent-row PhilHealth registration** | PDF "Answer Q79 to Q88 if the respondent is registered with PhilHealth in Q45". Q45 is per-member; the gate is the row-1 (respondent) value | Cross-record GATE §3 Section H |
| 19 | **Section F BUCAS conditional** | PDF "Q57 to Q61 are applicable only to respondents in areas with BUCAS. Otherwise, proceed to Q62". BUCAS area flag is not in the questionnaire; comes from `loadsetting()` at preproc time (read from EXT_DIC facility metadata) | Settings-driven GATE §3 Section F |
| 20 | **Section G GAMOT conditional** | PDF "Q69 to Q74, Q76 are applicable only to respondents in areas with GAMOT facility. Otherwise, proceed to Q79". Same settings-driven gate as BUCAS | Settings-driven GATE §3 Section G |

---

## 2. Skip-logic table

### Section A — Introduction and Informed Consent

| Q | Condition | Skip to |
|---|---|---|
| Q1 IS_HH_HEAD | = No (2) | **Locate-HH-head handler** before proceeding to Q2. If unable to locate, set `ENUM_RESULT_FINAL_VISIT = 4 (Refused / No HH head available)` and terminate. |
| — | `FIELD_CONTROL.CONSENT_GIVEN = No (2)` | **Terminate interview**; set `ENUM_RESULT_FINAL_VISIT = Withdraw Participation/Consent` |

### Section B — Respondent Profile

| Q | Condition | Skip to |
|---|---|---|
| Q4 LGBTQIA | = No (2) **or** Not Comfortable (3) **or** DK (4) **or** Refused (5) | **Q6** (skip Q5) |
| Q7 PWD | = No | **Q11** (skip Q8, Q9, Q10) |
| Q8 PWD_SPECIFY | = No | **Q11** (skip Q9, Q10) |
| Q9 PWD_CARD | ≠ "Yes (card presented and verified)" (1) | **Q11** (skip Q10 — GATE rule, card-gated) |
| Q14 IP | = No | **Q16** (skip Q15) |

### Section C — Household Roster + Private-Insurance Sub-Roster

| Q | Condition | Skip to |
|---|---|---|
| C_HOUSEHOLD_ROSTER occurrences | (per-row gate) `Q31_PRESENT = Away (0)` | Permitted; row still saved but `Q35-Q46` may stay blank |
| C_HOUSEHOLD_ROSTER row 1 fields | Q1_IS_HH_HEAD = Yes (1) | Auto-fill row-1 Q34 = "Head" (01); always auto-fill row-1 Q32 from Q2_1_AGE and row-1 Q33 from Q3_SEX |
| C_HOUSEHOLD_ROSTER total occurrences | (post-section consistency) | Must equal `Q19_HH_SIZE`; else SOFT warning to enumerator |
| Q47 HAS_PRIVATE_INS | = No (2) | **Q51** (skip C_PRIVATE_INSURANCE_ROSTER occurrences) |
| C_PRIVATE_INSURANCE_ROSTER row gate | Q47 = Yes (1) | Roster occurrences enabled for each HH member who has private insurance; max_occurs=10 |

### Section D — UHC Awareness

| Q | Condition | Skip to |
|---|---|---|
| Q51 HEARD_UHC | = No (2) | Continue to **Q52** (per PDF arrow) -- both Q52 and Q53 are asked regardless |

### Section E — YAKAP/Konsulta

| Q | Condition | Skip to |
|---|---|---|
| Q54 HEARD_YAKAP | = No (2) | **Q57** (skip Q55, Q56) |

### Section F — BUCAS

> [!note] Settings-driven gate: Q57-Q61 only fire when `loadsetting("F4_BUCAS_AREA")` = 1 for the case's facility. Otherwise proceed to Q62. The setting comes from the EXT_DIC facility-metadata dictionary (103_EXT_DATA) at preproc time.

| Q | Condition | Skip to |
|---|---|---|
| Q57 HEARD_BUCAS | = No (2) | **Q62** (skip Q58, Q59, Q60, Q61) |
| Q60 BUCAS_ACCESSED | = No (2) | **Q62** (skip Q61) |

### Section G — Access to Medicines

> [!note] Settings-driven gate: Q69-Q74 and Q76 only fire when `loadsetting("F4_GAMOT_AREA")` = 1 for the case's facility. Otherwise proceed to Q79. Same EXT_DIC source as the BUCAS gate.

| Q | Condition | Skip to |
|---|---|---|
| Q62 PURCHASE_FREQUENCY | = Never (5) | **Q69** (skip Q63-Q68) |
| Q69 HEARD_GAMOT | = No (2) | **Q75** (skip Q70-Q74) |
| Q72 GAMOT_OBTAINED | = No (2) | **Q75** (skip Q73, Q74) |
| Q76 MED_TYPE_PURCHASED | = Branded (1) | **Q78** (skip Q77) |
| Q76 MED_TYPE_PURCHASED | = Don't know the difference (4) **or** Not applicable (5) | **Q79** (skip Q77, Q78) |
| Q77 GENERIC_REASON | Q76 = Branded (1) | not asked |
| Q78 BRANDED_REASON | Q76 = Generic (2) | not asked |

### Section H — PhilHealth Registration

> [!note] Cross-record gate: Q79-Q88 only fire when `C_HOUSEHOLD_ROSTER[1].Q45_PHILHEALTH_REG = Yes (01)`. The PDF says "Answer Q79 to Q88 if the respondent is registered with PhilHealth in Q45". Row 1 of the household roster is the respondent.

| Q | Condition | Skip to |
|---|---|---|
| Q81 HAD_DIFFICULTIES | = No (2) | **Q83** (skip Q82) |
| Q87 DIFFICULT_TO_PAY | = No (2) | **Q89** (skip Q88; end of section H) |

### Section I — Primary Care Utilization

| Q | Condition | Skip to |
|---|---|---|
| Q89 HAS_USUAL_FACILITY | = No (2) **or** DK (3) | **Q93** (skip Q90, Q91, Q92, Q89.1 facility name) |
| Q90 IS_USUAL_FOR_GENERAL | = No (2) | **Q96** (skip Q91, Q92, Q93, Q94, Q95) |
| Q93 NO_USUAL_REASON | (asked only when Q89 = No or DK) | Continue |

### Section J — Health-Seeking Behavior

| Q | Condition | Skip to |
|---|---|---|
| Q105 CHOSE_NOT_TO_SEE | = No (2) | **Q107** (skip Q106) |

### Section K — Referrals

| Q | Condition | Skip to |
|---|---|---|
| Q108 REFERRED | = No (2) | **Q126** (skip Q109-Q125; entire body of section K bypassed) |
| Q112 VISITED | = Yes (1) | **Q114** (skip Q113) |
| Q112 VISITED | = Not yet, planning to (3) | **Q114** (skip Q113) |
| Q112 VISITED | = No, not planning (2) | **Q113** then **Q119** (skip Q114-Q118) |
| Q117 FOLLOWUP | Q112 = Yes (1) gate | else not asked |
| Q118 SAT_REFERRAL | Q112 = Yes (1) gate | else not asked |
| Q119 PCP_REFERRAL | = No (2) | **Q121** (skip Q120) |

### Section L — NBB

| Q | Condition | Skip to |
|---|---|---|
| Q126 HEARD_NBB | = No (2) **or** DK (3) | **Q132** (skip Q127-Q131) |
| Q129 HOSPITALIZED_6MO | = No (2) **or** DK (3) | **Q132** (skip Q130, Q131) |
| Q130 HOSPITAL_TYPE | = Public (1) | **Q132** (skip Q131) |
| Q130 HOSPITAL_TYPE | = Private (3) | **Q132** (skip Q131) |
| Q131 OOP_NBB | Q130 = DOH-retained (2) gate | else not asked |

### Section M — ZBB / MAIFIP / Bill detail

| Q | Condition | Skip to |
|---|---|---|
| Q132 HEARD_ZBB | = No (2) **or** DK (3) | **Q137** (skip Q133, Q134; Q135 also skipped if Q130 ≠ 2) |
| Q135 OOP_ZBB | Q130 = DOH-retained (2) gate | else not asked |
| Q136 HEARD_MAIFIP | = No (2) **or** DK (3) | **Q138** (skip Q137) |
| Q140 RECALL_BREAKDOWN | = No (2) | **Q142** (skip Q141, Q141.1) |
| Q142 RECALL_HOW_PAID | = No (2) | **Q144** (skip Q143) |

### Section N — Household Expenditures

No section-level skip routing. Every Q144-Q185 row is asked in order. Within each row, the form's onfocus handler shows/hides the amount columns based on `Q{n}_CONSUMED` (Yes shows; No skips the amount fields and zeros the total). The computed-total items (Q157, Q177, Q182, Q185) are filled in PROC at the moment the relevant input items are exited; the operator does not touch them.

| Computed total | Fill rule |
|---|---|
| Q157_TOTAL | sum of Q144_TOTAL .. Q156_TOTAL |
| Q177_TOTAL | sum of Q175_TOTAL + Q176_TOTAL |
| Q182_TOTAL | sum of Q178_TOTAL + Q179_TOTAL + Q180_TOTAL + Q181_TOTAL |
| Q185_TOTAL | sum of Q183_TOTAL + Q184_TOTAL |

Each `Q{n}_TOTAL` itself is the row's sum: `Q{n}_TOTAL = Q{n}_AMOUNT_PURCHASED + Q{n}_AMOUNT_INKIND` when `Q{n}_CONSUMED = Yes`; else `0`.

### Section O — Sources of Funds for Health

| Q | Condition | Skip to |
|---|---|---|
| Q195 PORTION_FOR_HEALTH | = None (1) | continue to **Q196** |
| Q195 PORTION_FOR_HEALTH | = Less than 1% (2), 1-3% (3), 4-6% (4), More than 6% (5), DK (6) | **Q197** (skip Q196) |

### Section P — Financial Risk Protection

No internal skips. Q197, Q198, Q199 all asked.

### Section Q — Financial Anxiety

| Q | Condition | Skip to |
|---|---|---|
| Q200 REDUCED_SPENDING | = Refused (4) | **END OF SURVEY** (skip Q201, Q202); set `ENUM_RESULT_FINAL_VISIT` appropriately |
| Q201 WORRIED_FINANCES | = Not worried at all (4) | **END OF SURVEY** (skip Q202); set `ENUM_RESULT_FINAL_VISIT = Completed` |

---

## 3. Validations and edit rules

### Cross-field consistency (HARD edits)

| Rule | Items |
|---|---|
| **Age vs birth year** | `\|Q2_1_AGE - (current_year - Q2_BIRTH_YEAR)\| <= 1` |
| **Income amount vs bracket** | `Q18_INCOME_AMOUNT` falls in `Q18_INCOME_BRACKET` range |
| **HH size vs roster occurrences** | `count(C_HOUSEHOLD_ROSTER occurrences) == Q19_HH_SIZE` |
| **PWD card gating** | `Q10_DISABILITY_TYPE` populated only when `Q9_PWD_CARD = 1 (Yes, presented and verified)` |
| **Q131 gate** | populated only when `Q130_HOSPITAL_TYPE = 2 (DOH-retained)` |
| **Q135 gate** | populated only when `Q130_HOSPITAL_TYPE = 2 (DOH-retained)` |
| **HH_LISTING_NO required** | `FIELD_CONTROL.HH_LISTING_NO > 0` always (never 0 or 9999=NA) |
| **F4_PARENT_F3_CASE_SEQ optional** | `FIELD_CONTROL.F4_PARENT_F3_CASE_SEQ ∈ [001, 699, 700-899, 900-999, 999]`; 999 = NA when sampling mode = barangay listing |
| **Section H gate** | Q79-Q88 populated only when `C_HOUSEHOLD_ROSTER[1].Q45_PHILHEALTH_REG = 01 (Yes)` |
| **Row 1 = respondent** | `C_HOUSEHOLD_ROSTER[1].Q32_AGE == Q2_1_AGE`; `C_HOUSEHOLD_ROSTER[1].Q33_SEX == Q3_SEX` |
| **Q34 head exclusivity** | exactly one row in `C_HOUSEHOLD_ROSTER` has `Q34_RELATIONSHIP = 01 (Head)` |

### Range checks (HARD edits)

| Item | Range |
|---|---|
| `Q2_BIRTH_MONTH` | `1..12` |
| `Q2_BIRTH_YEAR` | `1900..current_year` |
| `Q2_1_AGE` | `0..130` |
| `Q19_HH_SIZE` | `1..30` |
| `Q20_HH_CHILDREN` | `0..Q19_HH_SIZE` |
| `Q21_HH_SENIORS` | `0..Q19_HH_SIZE` |
| `Q32_AGE` (each row) | `0..130` |
| `Q67_TIME_TO_PHARMACY` HH | `0..23` |
| `Q67_TIME_TO_PHARMACY` MM | `0..59` |
| `Q95_TRAVEL_TIME_ONE_WAY` HH | `0..23` |
| `Q95_TRAVEL_TIME_ONE_WAY` MM | `0..59` |
| `Q96_TRAVEL_COST_ONE_WAY` | `0..99999` (cap matches len=7 with peso assumption) |
| `Q139_FINAL_AMOUNT_PAID` | `0..9999999999` (len 10) |
| `Q141_1_NO_RECEIPT_AMOUNT` | `0..9999999999` (len 10) |
| every `Q{n}_AMOUNT_*` in Section N | `0..9999999999` (len 10) |
| every `Q{n}_TOTAL` in Section N | `0..99999999999` (len 11) |

### Soft warnings (SOFT)

| Rule | Trigger |
|---|---|
| HH size sanity | `Q19_HH_SIZE > 15` |
| Roster row count mismatch | `count(C_HOUSEHOLD_ROSTER) != Q19_HH_SIZE` -- ask enumerator to confirm |
| Old senior | any `Q32_AGE > 110` -- ask to verify |
| Travel time to pharmacy | `Q67 > 2h00m` -- ask to verify |
| Travel cost outlier | `Q96 > 500` pesos one-way -- ask to verify |
| Expenditure outliers | any `Q{n}_AMOUNT_PURCHASED > 1,000,000` -- ask to verify (likely typo) |

---

## 4. PROC implementation pointers

The skip-logic table above maps 1:1 to handler functions in `generate_apc.py` (forthcoming at the F4 quartet phase). Naming convention mirrors F3:

```
PROC Q{n}_*
  ! Pre-eval: should this question be asked?
  if not should_ask_Q{n}() then skip end;
  ! Post-eval: enforce range / consistency
  validate_Q{n}();
  ! Routing
  next_q := route_after_Q{n}();
end;
```

Shared helpers from `shared/Capture-Helpers.apc` (GPS, photo) and `shared/PSGC-Cascade.apc` (cascading PSGC value sets on HOUSEHOLD_GEO_ID) are wired identically to F1/F3. The `loadsetting()` calls for BUCAS / GAMOT area flags reference `103_EXT_DATA/facility_metadata.dcf`; the column names land in PROC at the quartet phase.

## 5. Open questions for Myra / Kidd (held for upstream review)

Per `feedback_defer_clarifications_during_upstream_review.md`, the following clarifications are documented but **not** sent to Kidd as a separate brief — Myra's Survey Manual edit pass should resolve or supersede them:

1. **Q136 MAIFIP cross-reference to Q113** — Q113 has no MAIFIP option; PDF text appears to be a transcription artifact. Confirm intended skip-rule.
2. **Q15 IP group list** — PDF references "a list will be provided" but none included. Confirm value set or accept free-text alpha.
3. **BUCAS / GAMOT area flags** — confirm the source field in 103_EXT_DATA/facility_metadata for `F4_BUCAS_AREA` and `F4_GAMOT_AREA`. Default assumption: per-facility boolean columns; values currently unknown until the EXT_DIC bundle ships.
4. **Q1 = No (not HH head) routing** — confirm the locate-HH-head fallback behaviour (revisit later, terminate, or interview anyone present).

---

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention]] — 12-digit case-ID block, replacement-protocol ranges, and the F4 dual-linkage rationale (HH_LISTING_NO + F4_PARENT_F3_CASE_SEQ).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions]] — NA-at-highest-value rule (9 / 99 / 999) and special-code reserves.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/GPS and Photo Capture]] — REC_HOUSEHOLD_CAPTURE + REC_CASE_VERIFICATION patterns.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol]] — CASE_SEQ partitioning that informs replacement bookkeeping.
- [`deliverables/CSPro/UHC-Survey-System/111_F3/F3-Skip-Logic-and-Validations.md`](../111_F3/F3-Skip-Logic-and-Validations.md) — F3 sibling spec (referral and demographic skip-rule conventions reused here).
