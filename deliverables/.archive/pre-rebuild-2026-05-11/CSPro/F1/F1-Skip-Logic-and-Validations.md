---
type: spec
project: ASPSI-DOH-CAPI-CSPro-Development
deliverable: F1 Facility Head Survey — CAPI logic spec
date_created: 2026-04-10
reviewed_on: 2026-04-21
status: reviewed
source_questionnaire: raw/Project-Deliverable-1_Apr20-submitted/Annex F1_Facility Head Survey Questionnaire_UHC Year 2.pdf
source_dcf: deliverables/CSPro/F1/FacilityHeadSurvey.dcf
tags: [cspro, capi, skip-logic, validations, f1]
---

# F1 Facility Head Survey — Skip Logic and Validations Spec

Source-of-truth for CSPro CAPI logic on `FacilityHeadSurvey.dcf`. Covers:

1. **Sanity-check findings** — discrepancies between the Apr 20 questionnaire and the current dcf (12 records / 664 items).
2. **Skip-logic table** — every conditional jump extracted from the questionnaire.
3. **Cross-field validations** — HARD (block save), SOFT (warn-and-confirm), GATE (display-only conditional rendering).
4. **CSPro logic templates** — paste-ready snippets for common patterns.

All Q-numbers refer to the **Apr 20 printed questionnaire** (1–166); dcf item names follow the `Q{n}_*` convention.

> **Item-count provenance.** The Apr 08 baseline had ~126 printed items. The Apr 20 DOH-submitted revision (driven by the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G remarks]]) added ~40 items — Q32–Q34 (EMR DOH IS / PhilHealth Dashboard submission + decision-making checklist), Q40–Q42 (explicit NBB / ZBB / no-copay), Section E expansion to BUCAS + GAMOT (Q101–Q117), and Section G's four named subsections (NBB Q135–137, ZBB Q138–140, LGU Q148–153, Referral Q154–162). Generator expansion (select-all per-option flags, `_OTHER_TXT` companions, secondary-data stub records) lifted the dcf to 11 records / 655 items on Apr 20. The Apr 21 GPS+photo capture pass added one further record — `REC_FACILITY_CAPTURE` (type Z, facility GPS + verification photo) — bringing the dcf to **12 records / 664 items**. See `wiki/analyses/Analysis - Apr 20 DCF Generator Audit.md` for the per-patch ledger.

---

## 1. Sanity-check findings (dcf vs Apr 20 questionnaire)

### A. Dispositions of the six original bugs

The original Apr 10 spec flagged six generator bugs. Five are now closed in code; two remain pending ASPSI input (tracked below). Numbering preserved for continuity with the Apr 13 LSS minutes and E2-F1-009b.

| # | Item | Status | Disposition |
|---|---|---|---|
| 1 | **Q166 PD_NURSES list** | PARTIAL — generator-implemented, pending ASPSI sign-off | `Q166_NURSES_INCLUDE_AUDITS = False` in `generate_dcf.py`; a dedicated `pd_nurse_options` list is emitted without "Clinical audits" / "Surgical audits". Still flagged `PENDING DESIGN` awaiting confirmation from ASPSI that the printed Q166 omission is intentional. |
| 2 | **Secondary Data section** | PARTIAL — stubs present, structure open | `SECONDARY_DATA_AS_STUBS = True`; four empty-item records exist in the dcf (`SEC_HOSP_CENSUS`, `SEC_HCW_ROSTER`, `SEC_YK_SERVICES`, `SEC_LAB_PRICES`) so the dictionary opens. The internal structure (record-per-month vs flat, roster cadre × employment type) is still pending a Juvy/Kidd decision — see §5 Dispositions. |
| 3 | **Q63 ACCRED_WAIT label/units mismatch** | OPEN — source bug, needs ASPSI | `Q63_USE_DAY_BUCKETS = False` (months kept as current default). Question stem says "days"; bucket labels are in months. Routed to Juvy/Kidd for a single-source fix to the printed questionnaire before Tranche 2. |
| 4 | **Q31 EMR — `Not applicable` skip** | CLOSED | `Q31_NA_SKIPS = True`. Handled in CAPI `PROC Q31_EMR_USE` (§4.4 pattern) — NA routes to Q35 alongside the other UHC9 NA branches. |
| 5 | **Informed-consent block** | CLOSED | `CONSENT_GIVEN` added to `FIELD_CONTROL`; `RESP_NAME` / `RESP_POSITION` / `RESP_EMAIL` / `RESP_MOBILE` live at the top of `A_FACILITY_HEAD_PROFILE` (moved out of FIELD_CONTROL so they sit next to the facility-head profile they describe). Consent=No aborts the interview. |
| 6 | **Tenure ≥6 months pre-filter** | CLOSED-BY-DESIGN | Enforced in `PROC Q5_MONTHS_AT_FACILITY postproc` (§4.2), not as a separate screening item. Tenure below 6 months terminates and sets `ENUM_RESULT = Refused/Incomplete`. |

### B. Cosmetic / acceptable as-is

- F1.txt has stray legacy prefixes like `Q40 52`, `Q43 64` — leftover from an older question-numbering scheme. Dcf correctly uses the printed 1–166 numbering. No action.
- Hospital-only / PCF-only gating inside Q121 options is not encoded as separate items in the dcf — enforced via display logic (§3 below and `Q121_DYNAMIC_VALUE_SET = False` fallback), which is the right approach.
- Respondent informed-consent contact block (`RESP_NAME` / `RESP_POSITION` / `RESP_EMAIL` / `RESP_MOBILE`) lives inside Section A rather than `FIELD_CONTROL` — intentional; generator comment notes "moved out of FIELD_CONTROL so it lives with the facility-head profile it describes."

---

## 2. Skip-logic table

Format: **Trigger → Destination (skip range)**. Where the source has multiple "No / NA / I don't know / no plans" branches all going to the same target, they are collapsed into a single row.

### Section C — UHC Implementation

| Q | Condition | Skip to |
|---|---|---|
| Q10 HAS_PRIMARY_PKG | = No (2) | Q12 (skip Q11) |
| Q13 PUBLIC_HEALTH_UNIT | = No (2) **or** NA | Q16 (skip Q14, Q15) |
| Q14 PHU_CREATED | ∈ {No-planned, No-no-plans, No-other, IDK, NA} (5–9) | Q16 (skip Q15) |
| Q16 HEALTH_PROMO_UNIT | = No **or** NA | Q19 (skip Q17, Q18) |
| Q17 HPU_CREATED | ∈ {5–9} | Q19 (skip Q18) |
| Q19 NEW_ROLES | ∈ {5–9} | Q21 (skip Q20) |
| Q21 NEW_DEPTS | ∈ {5–9} | Q23 (skip Q22) |
| Q23 NEW_BUILDINGS | ∈ {5–9} | Q25 (skip Q24) |
| Q25 NEW_ROOMS | ∈ {5–9} | Q27 (skip Q26) |
| Q27 INC_EQUIPMENT | ∈ {5–9} | Q29 (skip Q28) |
| Q29 INC_SUPPLIES | ∈ {5–9} | Q31 (skip Q30) |
| Q31 EMR_USE | ∈ {5–8} (and NA per Bug #4) | Q35 (skip Q32, Q33, Q34) |
| Q32 DATA_SUBMIT | = "No, not submitting" (4) | Q35 (skip Q33, Q34) |
| Q35 STAFFING_CHANGED | = No | Q37 (skip Q36) |
| Q37 REFERRAL_CHANGED | = No | Q39 (skip Q38) |

### Section D — YAKAP / Konsulta

| Q | Condition | Skip to |
|---|---|---|
| **Q51 YK_ACCRED** | = No | **Q79** (skip Q52–Q78; non-accredited path) |
| Q59 KNOW_PAY_FREQ | = No | Q61 (skip Q60) |
| Q61 TRANCHE_DELAY | = No | Q62 (skip Q61.1 reason text) |
| Q65 ACCRED_DIFFICULT | = "None of the above" only | Q75 (skip Q66–Q74) |
| Q66–Q74 | Each is gated on the corresponding option being selected in Q65 (not a jump skip — display-time gate; see §3) | — |
| Q77 ENROLL_CHALL | = No | Q85 (skip Q78) |
| **Q79–Q84** | Only entered if Q51 = No | — |
| Q80 INTEND_ACCRED | = "Yes, in process" / "Yes, not in process" (1, 2) | Q84 |
|  | = "No, decided not to" (3) | Q82 |
|  | = "No, tried and failed" (4) | Q83 |
|  | = "No, haven't thought about it" (5) | Q81 |
|  | = "I don't know" (6) | Q85 |
| Q89 COSTING_DONE | = No | Q91 (skip Q90) |
| Q90 COSTING_VIABLE | = Yes AND Q51 = Yes | Q91 |
|  | = No AND Q51 = No | Q92 |
|  | = I don't know | Q93 |
| Q93 CHARGE_ADDL_CAP | = No | Q95 (skip Q94) |
| Q95 RECEIVED_PAYMENTS | ∈ {Yes-all, Yes-some} | Q97 (skip Q96) |
| Q97 PAYMENT_CHALL | = No | Q99 (skip Q98) |
| Q99, Q100 | Only if Q51 = Yes; otherwise → Q101 | — |

### Section E — BUCAS / GAMOT

| Q | Condition | Skip to |
|---|---|---|
| **Q101 HEARD_BUCAS** | = No | **Q108** (skip Q102–Q107) |
| Q102 HAS_BUCAS | = Yes | Q104 (skip Q103) |
|  | = No | Q103 then Q108 (skip Q104–Q107) |
|  | = I don't know | Q108 |
| Q103 NO_BUCAS_REASON | (any answer) | Q108 |
| Q104–Q107 | Only entered if Q102 = Yes | — |
| Q107 BUCAS_DECONGEST | Only relevant if BUCAS center exists in area (Q102 = Yes) | — |
| **Q108 HEARD_GAMOT** | = No | **Q112** (skip Q109–Q111) |
| Q109 GAMOT_ACCRED | = Yes | Q111 (skip Q110) |
|  | = No | Q110 then Q112 (skip Q111) |
| Q110 NO_GAMOT_REASON | (any answer) | Q112 |
| Q112 STOCKOUT | = No | Q118 (skip Q113–Q117) |
| Q116 ADDR_STOCKOUT | Gated on Q108 = Yes AND Q109 = Yes | — |
|  | = No or "Did not experience" | Q118 (skip Q117) |
| Q117 ADDR_STOCKOUT_HOW | Gated on Q108 = Yes AND Q109 = Yes | — |

### Section F — DOH Licensing

| Q | Condition | Skip to |
|---|---|---|
| **Q118 DOH_LICENSED** | = No / Submitted-waiting / Don't know what licensing is (2, 3, 4) | **Q135** (skip Q119–Q134) |
| Q121 DOH_LIC_DIFFICULT | = "None of the above" only | Q135 (skip Q122–Q134) |
| Q122–Q134 | Each gated on corresponding option in Q121 | — |
| **Q132, Q133, Q134** | Hospital-only — gated on Q8 SERVICE_LEVEL ∈ {Level 1, 2, 3 Hospital} AND corresponding Q121 option | — |
| **Q130** | Primary-care-only — gated on Q8 = Primary Care Facility AND Q121 price-info option | — |

### Section G — Service Delivery

| Q | Condition | Skip to |
|---|---|---|
| Q135 NBB_CURR | = No | Q138 (skip Q136, Q137) |
| Q138 ZBB_CURR | = No | Q141 (skip Q139, Q140) |
| Q141 ALLOW_OOP_BASIC | = No | Q143 (skip Q142) |
| Q145 MALASAKIT_PROVIDED | = Yes | Q146 → Q148 (skip Q147) |
|  | = No | Q147 (skip Q146) |
| Q148 LGU_SUPPORT | = No | Q152 (skip Q149, Q150, Q151) |
| Q150 LGU_SATISFIED | = Yes | Q154 (skip Q151) |
| Q152 PHO_PROTOCOL_CLARITY | ∈ {Very Clear, Clear} | Q154 (skip Q153) — *implied; confirm with ASPSI* |
| Q161 REF_SATISFACTION | ∈ {Very Satisfied, Satisfied} | Q163 (skip Q162) |

### Section H — no skips

---

## 3. Validations

Categories: **HARD** = block save / reenter, **SOFT** = warn-and-confirm, **GATE** = display-only conditional rendering.

### 3.1 Field Control & Geographic ID

| Item | Rule | Severity |
|---|---|---|
| `DATE_FIRST_VISITED_THE_FACILITY` | Valid date (YYYYMMDD); `20260101 ≤ d ≤ today + 1` | HARD |
| `DATE_OF_FINAL_VISIT_TO_THE_FACILITY` | Valid date; `≥ DATE_FIRST_VISITED_THE_FACILITY`; `≤ today + 1` | HARD |
| `TOTAL_NUMBER_OF_VISITS` | `≥ 1` when `ENUM_RESULT_FIRST_VISIT` or `ENUM_RESULT_FINAL_VISIT = Completed` | HARD |
| `CONSENT_GIVEN` | Required; if = No → terminate with `ENUM_RESULT = Refused` | HARD |
| `CLASSIFICATION`, `REGION`, `PROVINCE_HUC`, `CITY_MUNICIPALITY`, `BARANGAY` | Required, non-blank; must exist in the loaded PSGC external lookup dictionaries (`shared/psgc_*.dcf`) | HARD |
| Child PSGC parent consistency | Enforced **at pick-time** by `PSGC-Cascade.apc` — `onfocus` on each child filters its value set to children of the chosen parent, so an inconsistent pair is unrepresentable | HARD — cascade enforces |
| `ENUM_RESULT_FIRST_VISIT = Completed` / `ENUM_RESULT_FINAL_VISIT = Completed` | All Section A–H mandatory items must be non-blank | HARD |

### 3.1.1 GPS capture block (`REC_FACILITY_CAPTURE`)

Populated by `ReadGPSReading()` from `shared/Capture-Helpers.apc`; enumerator taps the capture-trigger item to fire the read. `REC_FACILITY_CAPTURE` is a type-Z off-form record — items are wired via `onfocus` in the .app, not placed on a data-entry form.

| Item | Rule | Severity |
|---|---|---|
| `FACILITY_CAPTURE_GPS` | Trigger; auto-resets to blank after each successful read (so the button re-arms for retry) | — |
| `FACILITY_GPS_LATITUDE` | Alpha; after capture, `tonumber()` must be in `[4.5, 21.5]` (Philippine bounding box) | HARD |
| `FACILITY_GPS_LONGITUDE` | After capture, `tonumber()` in `[116.5, 127.0]` | HARD |
| `FACILITY_GPS_ALTITUDE` | Alpha; captured from `gps(altitude)`; no bounds enforced | — |
| `FACILITY_GPS_ACCURACY` | Numeric, metres. Warn if `> 30` — re-read outdoors recommended | SOFT |
| `FACILITY_GPS_SATELLITES` | Numeric. Warn if `< 4` (fix is below minimum for reliable lat/lon) | SOFT |
| `FACILITY_GPS_READTIME` | Alpha UTC timestamp; must parse and be within `±24 h` of `DATE_OF_FINAL_VISIT_TO_THE_FACILITY` | SOFT |
| `FACILITY_GPS_*` non-blank required | When `ENUM_RESULT_FINAL_VISIT = Completed` | HARD |

### 3.1.2 Verification photo (in `REC_FACILITY_CAPTURE`)

| Item | Rule | Severity |
|---|---|---|
| `CAPTURE_VERIFICATION_PHOTO` | Trigger; auto-resets to blank after each successful capture | — |
| `VERIFICATION_PHOTO_FILENAME` | Non-blank when `ENUM_RESULT_FINAL_VISIT = Completed`; 120-char alpha populated by `TakeVerificationPhoto()` | HARD |
| Filename pattern | Matches `case-{QUESTIONNAIRE_NO}-verification.jpg` (enforced by the PROC that assigns it) | HARD |
| File reachability | CSEntry attachment must sync to CSWeb before the case can be marked final; enforced by sync workflow, not dictionary validation | — |

### 3.2 Section A — Facility Head Profile

| Item | Rule | Severity |
|---|---|---|
| `Q3_AGE` | `18 ≤ age ≤ 90` | HARD |
| `Q3_AGE > 75` | Warn ("Unusually old for an active facility head — confirm") | SOFT |
| `Q5_YEARS_AT_FACILITY` | `0 ≤ y ≤ 60` | HARD |
| `Q5_MONTHS_AT_FACILITY` | `0 ≤ m ≤ 11` | HARD |
| **Tenure ≥ 6 months** | `Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY ≥ 6` (per IR eligibility) | HARD — terminate interview if violated |
| `Q5_YEARS_AT_FACILITY ≤ Q3_AGE − 18` | Can't have started working before age 18 | HARD |
| `Q6_YEARS_HEALTH` | `0 ≤ y ≤ 70` | HARD |
| `Q6_YEARS_HEALTH ≤ Q3_AGE − 18` | Same age-floor rule | HARD |
| **Tenure consistency** | `Q5_total ≤ Q6_total` (years at this facility cannot exceed total years in any health-related role) | HARD |
| `Q4_SEX` | Required, ∈ {1, 2} | HARD |
| `Q2_DESIGNATION = "Other"` | `Q2_DESIGNATION_OTHER_TXT` is required, non-blank | HARD |

### 3.3 Section B — Facility Profile

| Item | Rule | Severity |
|---|---|---|
| `Q7_OWNERSHIP` | Required | HARD |
| `Q8_SERVICE_LEVEL` | Required; drives Q121 / Q130 / Q132–134 gates | HARD |

### 3.4 Section C — UHC Implementation

| Item | Rule | Severity |
|---|---|---|
| Q11 enabled | Q10 = Yes | GATE |
| Q14, Q15 enabled | Q13 = Yes | GATE |
| Q15 enabled | Q14 ∈ {1–4} ("Yes" branches) | GATE |
| Q17, Q18 enabled | Q16 = Yes | GATE |
| Q18 enabled | Q17 ∈ {1–4} | GATE |
| Q20 enabled | Q19 ∈ {1–4} | GATE |
| Q22 enabled | Q21 ∈ {1–4} | GATE |
| Q24 enabled | Q23 ∈ {1–4} | GATE |
| Q26 enabled | Q25 ∈ {1–4} | GATE |
| Q28 enabled | Q27 ∈ {1–4} | GATE |
| Q30 enabled | Q29 ∈ {1–4} | GATE |
| Q33, Q34 enabled | Q32 ∈ {1, 2, 3} | GATE |
| Q36 enabled | Q35 = Yes | GATE |
| Q38 enabled | Q37 = Yes | GATE |
| Q49, Q50 select-all | Cannot combine "I don't know" with substantive options | HARD |
| Q49, Q50 select-all | Cannot combine "Other" without `_OTHER_TXT` filled | HARD |
| All `Q*_OTHER_TXT` | Required if "Other" option selected | HARD |
| All `Q*_YES_OTHER_TXT` | Required if main = 4 ("Yes, other reason") | HARD |
| All `Q*_NO_OTHER_TXT` | Required if main = 7 ("No, other reason") | HARD |

### 3.5 Section D — YAKAP / Konsulta

| Item | Rule | Severity |
|---|---|---|
| Q52–Q78 entered | Q51 = Yes | GATE |
| Q79–Q84 entered | Q51 = No | GATE |
| `Q52_YK_SINCE_YEAR` | `2019 ≤ year ≤ current_year` (UHC Act passed 2019) | HARD |
| `Q52_YK_SINCE_MONTH` | `1 ≤ m ≤ 12` | HARD |
| `Q52` not in future | `(year, month) ≤ (current_year, current_month)` | HARD |
| Q52 vs head's career | Accreditation date should be after head turned 18 — `current_year - Q52_YK_SINCE_YEAR ≤ Q3_AGE - 18` | SOFT |
| `Q57_CAPITATION_AMT` | `0 < amt ≤ 5000` (PHP) | HARD |
| `Q57_CAPITATION_AMT > 1700` | Warn ("Above PhilHealth max — confirm") | SOFT |
| Q60 enabled | Q59 = Yes | GATE |
| Q61 reason text | Q61 = Yes | GATE |
| **Q66–Q74 each** | Q65 has the corresponding option selected | GATE |
| Q78 enabled | Q77 = Yes | GATE |
| **Q80 routing** | See skip table; only one of Q81/Q82/Q83/Q84 should be answered per case | HARD |
| `Q86_ELIGIBLE_PATIENTS` | `0 ≤ n ≤ 1,000,000` | HARD |
| `Q87_REGISTERED_PATIENTS` | `0 ≤ n ≤ Q86_ELIGIBLE_PATIENTS` (registered cannot exceed eligible) | HARD |
| `Q87 / Q86 > 1.0` | Block with reentry | HARD |
| Q90 enabled | Q89 = Yes | GATE |
| `Q91_MIN_CAP_VALUE_ACC` | `0 < amt ≤ 50000`; warn if `> 5000` | HARD / SOFT |
| `Q92_MIN_CAP_VALUE_NONACC` | `0 < amt ≤ 50000`; warn if `> 5000` | HARD / SOFT |
| Q94 enabled | Q93 = Yes | GATE |
| Q96 enabled | Q95 ∈ {3, 4} (No options) | GATE |
| Q98 enabled | Q97 = Yes | GATE |
| Q99, Q100 enabled | Q51 = Yes | GATE |

### 3.6 Section E — BUCAS / GAMOT

| Item | Rule | Severity |
|---|---|---|
| Q102–Q107 enabled | Q101 = Yes | GATE |
| Q103 enabled | Q102 = No | GATE |
| Q104–Q107 enabled | Q102 = Yes | GATE |
| Q109–Q111 enabled | Q108 = Yes | GATE |
| Q110 enabled | Q109 = No | GATE |
| Q111 enabled | Q109 = Yes | GATE |
| Q113–Q117 enabled | Q112 = Yes | GATE |
| Q116, Q117 enabled | Q108 = Yes AND Q109 = Yes AND Q112 = Yes | GATE |
| `Q114_STOCKOUT_DURATION` vs `Q115_STOCKOUT_AVG` | If `Q114 = "More than 60 days"`, `Q115` should not be `"Less than a month"` (contradiction) | HARD |

### 3.7 Section F — DOH Licensing

| Item | Rule | Severity |
|---|---|---|
| Q119–Q134 enabled | Q118 = Yes (1) | GATE |
| Q122–Q134 enabled | Corresponding Q121 option selected | GATE |
| **Q132, Q133, Q134** enabled | Q8 ∈ {Level 1, 2, 3 Hospital} AND corresponding Q121 option | GATE |
| **Q130** enabled | Q8 = Primary Care Facility AND Q121 price-info option | GATE |
| Q121 hospital-only options selectable | Only if Q8 ∈ hospital levels | GATE |
| Q121 PCF-only option selectable | Only if Q8 = Primary Care Facility | GATE |

### 3.8 Section G — Service Delivery

| Item | Rule | Severity |
|---|---|---|
| Q136, Q137 enabled | Q135 = Yes | GATE |
| Q139, Q140 enabled | Q138 = Yes | GATE |
| Q142 enabled | Q141 = Yes | GATE |
| Q146 enabled | Q145 = Yes | GATE |
| Q147 enabled | Q145 = No | GATE |
| Q149–Q151 enabled | Q148 = Yes | GATE |
| Q151 enabled | Q150 = No | GATE |
| Q153 enabled | Q152 ∈ {Unclear, Very Unclear} | GATE |
| `Q154_NUM_REFERRED_OUT` | `0 ≤ n ≤ 100,000` (over 6 months); warn if `> 10,000` | HARD / SOFT |
| Q162 enabled | Q161 ∈ {Neither, Dissatisfied, Very Dissatisfied} | GATE |

### 3.9 Cross-section consistency

| Rule | Severity |
|---|---|
| If `Q118 = "I don't know what DOH licensing is"`, the Q65 option "DOH licensing requirements" should not be selected | SOFT (warn) |
| If `Q51 = Yes`, no answers should be present for Q79–Q84 | HARD |
| If `Q51 = No`, no answers should be present for Q52–Q78 | HARD |
| If `Q102 = No`, no answers in Q104–Q107 | HARD |
| If `Q109 = No`, no answers in Q111 | HARD |
| Secondary data — full-time staff who left ≤ total full-time staff count (when secondary data record is added per Bug #2) | HARD |

---

## 4. CSPro logic templates

Drop these into the corresponding `PROC` blocks in CSPro Designer. Item names match `generate_dcf.py`.

### 4.1 Helper: current date

```cspro
PROC GLOBAL
numeric currentYYYYMMDD;
numeric currentYear;
numeric currentMonth;

PROC FACILITYHEADSURVEY_FF       { application-level entry }
preproc
  currentYYYYMMDD = systemdate("YYYYMMDD");
  currentYear  = int(currentYYYYMMDD / 10000);
  currentMonth = int(currentYYYYMMDD / 100) % 100;
endpreproc
```

### 4.2 Eligibility gate at Q5/Q6 (terminate non-eligible respondents)

```cspro
PROC Q5_MONTHS_AT_FACILITY
postproc
  if (Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY) < 6 then
    errmsg("Respondent must have ≥ 6 months in current position. End interview and code as Refused/Incomplete.");
    move to ENUM_RESULT;
  endif;

  if Q5_YEARS_AT_FACILITY > (Q3_AGE - 18) then
    errmsg("Years at facility (%d) exceeds working-age years available (%d). Reenter.",
           Q5_YEARS_AT_FACILITY, Q3_AGE - 18);
    reenter;
  endif;
```

### 4.3 Tenure consistency at Q6

```cspro
PROC Q6_MONTHS_HEALTH
postproc
  numeric tenureMos;
  numeric healthMos;
  tenureMos = Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY;
  healthMos = Q6_YEARS_HEALTH * 12 + Q6_MONTHS_HEALTH;

  if healthMos < tenureMos then
    errmsg("Years in any health-related role (%d mos) cannot be less than years at this facility (%d mos).",
           healthMos, tenureMos);
    reenter;
  endif;

  if Q6_YEARS_HEALTH > (Q3_AGE - 18) then
    errmsg("Years in health (%d) exceeds working-age years available (%d).",
           Q6_YEARS_HEALTH, Q3_AGE - 18);
    reenter;
  endif;
```

### 4.4 Section C — generic UHC9 skip pattern (apply to Q11–Q48 sub-questions)

```cspro
{ Example: Q14 controls whether Q15 (PHU role) is asked. }
PROC Q14_PHU_CREATED
postproc
  if Q14_PHU_CREATED in 5:9 then    { 5..9 = all No / IDK / NA branches }
    skip to Q16_HEALTH_PROMO_UNIT;
  endif;
```

For dichotomous yes/no skips:

```cspro
PROC Q10_HAS_PRIMARY_PKG
postproc
  if Q10_HAS_PRIMARY_PKG = 2 then    { No }
    skip to Q12_PCB_LICENSING;
  endif;

PROC Q13_PUBLIC_HEALTH_UNIT
postproc
  if Q13_PUBLIC_HEALTH_UNIT in 2,9 then  { No or NA }
    skip to Q16_HEALTH_PROMO_UNIT;
  endif;
```

### 4.5 Section D — YAKAP master gate at Q51

```cspro
PROC Q51_YK_ACCRED
postproc
  if Q51_YK_ACCRED = 2 then  { Not accredited }
    skip to Q79_NOT_ACCRED_REASON;
  endif;
```

### 4.6 Q52 accreditation date validation

```cspro
PROC Q52_YK_SINCE_YEAR
postproc
  if Q52_YK_SINCE_YEAR < 2019 or Q52_YK_SINCE_YEAR > currentYear then
    errmsg("YAKAP accreditation year must be between 2019 and %d.", currentYear);
    reenter;
  endif;

PROC Q52_YK_SINCE_MONTH
postproc
  if Q52_YK_SINCE_MONTH < 1 or Q52_YK_SINCE_MONTH > 12 then
    errmsg("Month must be 1–12.");
    reenter;
  endif;
  if Q52_YK_SINCE_YEAR = currentYear and Q52_YK_SINCE_MONTH > currentMonth then
    errmsg("Accreditation date is in the future. Reenter.");
    reenter;
  endif;
```

### 4.7 Q86/Q87 consistency

```cspro
PROC Q87_REGISTERED_PATIENTS
postproc
  if Q87_REGISTERED_PATIENTS > Q86_ELIGIBLE_PATIENTS then
    errmsg("Registered patients (%d) cannot exceed eligible patients (%d).",
           Q87_REGISTERED_PATIENTS, Q86_ELIGIBLE_PATIENTS);
    reenter;
  endif;
```

### 4.8 Q57 capitation soft warning

```cspro
PROC Q57_CAPITATION_AMT
postproc
  if Q57_CAPITATION_AMT > 5000 then
    errmsg("Capitation %d PHP is implausibly high. Reenter or confirm.", Q57_CAPITATION_AMT);
    reenter;
  endif;
  if Q57_CAPITATION_AMT > 1700 then
    if not accept("Capitation %d exceeds the PHP 1,700 PhilHealth max. Confirm?", "Yes", "No") = 1 then
      reenter;
    endif;
  endif;
```

### 4.9 Section F — Q121 facility-type-aware gating

```cspro
PROC Q121_DOH_LIC_DIFFICULT
preproc
  { Hide hospital-only options for non-hospital facilities }
  if Q8_SERVICE_LEVEL = 1 then  { Primary Care Facility }
    setvalueset(Q121_DOH_LIC_DIFFICULT, vs_q121_pcf);
  else
    setvalueset(Q121_DOH_LIC_DIFFICULT, vs_q121_hospital);
  endif;
postproc
  { "None of the above" → skip the why-difficult cluster }
  if Q121_O14_NONE = 1 then
    skip to Q135_NBB_CURR;
  endif;
```

### 4.10 Generic "why-difficult" gate (Q66–Q74, Q122–Q134)

```cspro
PROC Q66_WHY_DIFF_66
preproc
  { Skip Q66 entirely if Q65 didn't flag this area }
  if Q65_O01_ABILITY_TO_CONDUCT_PRE = 0 then
    skip to next;
  endif;
```

### 4.11 Section G — Q150 → Q154 jump

```cspro
PROC Q150_LGU_SATISFIED
postproc
  if Q150_LGU_SATISFIED = 1 then  { Yes }
    skip to Q154_NUM_REFERRED_OUT;
  endif;
```

### 4.12 Section G — Q161 satisfaction skip

```cspro
PROC Q161_REF_SATISFACTION
postproc
  if Q161_REF_SATISFACTION in 1,2 then  { Very Satisfied / Satisfied }
    skip to Q163_HR_CHALL;     { Section H starts here }
  endif;
```

### 4.13 "Other (specify)" enforcement (apply to every `Q*_OTHER_TXT`)

```cspro
PROC Q11_OTHER_TXT
postproc
  if Q11_PRIMARY_PKG_STATUS = 5 and length(strip(Q11_OTHER_TXT)) = 0 then
    errmsg("'Other' was selected for Q11. Please specify.");
    reenter;
  endif;
```

For UHC9 items (`*_YES_OTHER_TXT` / `*_NO_OTHER_TXT`):

```cspro
PROC Q12_YES_OTHER_TXT
postproc
  if Q12_PCB_LICENSING = 4 and length(strip(Q12_YES_OTHER_TXT)) = 0 then
    errmsg("'Yes, other reason' was selected. Please specify.");
    reenter;
  endif;

PROC Q12_NO_OTHER_TXT
postproc
  if Q12_PCB_LICENSING = 7 and length(strip(Q12_NO_OTHER_TXT)) = 0 then
    errmsg("'No, other reason' was selected. Please specify.");
    reenter;
  endif;
```

### 4.14 Field Control — consent terminator

```cspro
PROC CONSENT_GIVEN
postproc
  if CONSENT_GIVEN = 2 then              { No — respondent withdraws }
    ENUM_RESULT_FINAL_VISIT = 3;         { Refused }
    errmsg("Consent not given. Close the questionnaire and code as Refused.");
    endgroup;                            { terminate — do not enter Section A }
  endif;
```

### 4.15 Geographic ID — PSGC cascading value sets

Include `PSGC-Cascade.apc` in the form's .app:

```cspro
#include "../shared/PSGC-Cascade.apc"
```

Each PSGC item filters its own value set on focus, using the parent picked upstream. `loadcase()` reads from the external PSGC lookup dictionaries under `shared/psgc_*.dcf`; see CSPro 8.0 Users Guide p.188 Logic Tip #4 for the `setvalueset()` + `loadcase()` pattern.

```cspro
PROC REGION
onfocus
  FillRegionValueSet(REGION);

PROC PROVINCE_HUC
onfocus
  FillProvinceValueSet(PROVINCE_HUC, REGION);

PROC CITY_MUNICIPALITY
onfocus
  FillCityValueSet(CITY_MUNICIPALITY, PROVINCE_HUC);

PROC BARANGAY
onfocus
  FillBarangayValueSet(BARANGAY, CITY_MUNICIPALITY);
```

### 4.16 GPS capture and verification photo

Include `Capture-Helpers.apc` in the form's .app:

```cspro
#include "../shared/Capture-Helpers.apc"
```

```cspro
{ Facility GPS — fired on the capture-trigger item. }
PROC FACILITY_CAPTURE_GPS
onfocus
  if ReadGPSReading(120, 20) then
    FACILITY_GPS_LATITUDE   = maketext("%f", gps(latitude));
    FACILITY_GPS_LONGITUDE  = maketext("%f", gps(longitude));
    FACILITY_GPS_ALTITUDE   = maketext("%f", gps(altitude));
    FACILITY_GPS_ACCURACY   = gps(accuracy);
    FACILITY_GPS_SATELLITES = gps(satellites);
    FACILITY_GPS_READTIME   = gps(readtime);
  endif;
  FACILITY_CAPTURE_GPS = notappl;   { reset trigger so button re-arms }

{ Post-capture sanity checks — run on the lat/lon items themselves, not on the trigger. }
PROC FACILITY_GPS_LATITUDE
postproc
  numeric lat;
  lat = tonumber(FACILITY_GPS_LATITUDE);
  if lat <> notappl and (lat < 4.5 or lat > 21.5) then
    errmsg("Facility latitude %f is outside the Philippine bounding box — re-capture.", lat);
    move to FACILITY_CAPTURE_GPS;
  endif;

PROC FACILITY_GPS_LONGITUDE
postproc
  numeric lon;
  lon = tonumber(FACILITY_GPS_LONGITUDE);
  if lon <> notappl and (lon < 116.5 or lon > 127.0) then
    errmsg("Facility longitude %f is outside the Philippine bounding box — re-capture.", lon);
    move to FACILITY_CAPTURE_GPS;
  endif;

{ Verification photo — fired on the capture-trigger. }
PROC CAPTURE_VERIFICATION_PHOTO
onfocus
  string fn = "case-" + maketext("%06d", QUESTIONNAIRE_NO) + "-verification.jpg";
  if TakeVerificationPhoto(fn) then
    VERIFICATION_PHOTO_FILENAME = fn;
  endif;
  CAPTURE_VERIFICATION_PHOTO = notappl;

PROC VERIFICATION_PHOTO_FILENAME
postproc
  if ENUM_RESULT_FINAL_VISIT = 1 and length(strip(VERIFICATION_PHOTO_FILENAME)) = 0 then
    errmsg("Verification photo is required when the case is marked Completed.");
    move to CAPTURE_VERIFICATION_PHOTO;
  endif;
```

---

### 4.17 Case-control preproc (SURVEY_CODE, DATE_STARTED, TIME_STARTED, AAPOR_DISPOSITION)

Added 2026-04-21 as part of the case-control extension (cross-instrument scope — same block in F3/F4 with `survey_code` set per instrument). These five items live at the top of `FIELD_CONTROL`: `SURVEY_CODE`, `INTERVIEWER_ID`, `DATE_STARTED`, `TIME_STARTED`, `AAPOR_DISPOSITION`.

All four auto-set fields are prefilled on the first visit to the case; `INTERVIEWER_ID` is the only one the enumerator types. `AAPOR_DISPOSITION` is reassigned at well-defined transition points (consent refusal, eligibility termination, and CLOSING postproc).

```
PROC FIELD_CONTROL
preproc
  { Prefill the case-control block on first visit. visualvalue() returns
    the case's current value — when blank, this is a fresh case. }
  if visualvalue(SURVEY_CODE) = "" then
    SURVEY_CODE       = "F1";                         { per-instrument literal }
    DATE_STARTED      = tonumber(sysdate("YYYYMMDD"));
    TIME_STARTED      = tonumber(systime("HHMMSS"));
    AAPOR_DISPOSITION = 0;                            { 000 = In Progress }
  endif;

PROC CONSENT_GIVEN
postproc
  { Consent refusal → final disposition 210 (respondent refusal), jump to closing. }
  if CONSENT_GIVEN = 2 then
    AAPOR_DISPOSITION = 210;
    skip to AAPOR_DISPOSITION_FINAL;  { CLOSING form field }
  endif;
```

**Notes:**
- `sysdate("YYYYMMDD")` and `systime("HHMMSS")` are CSPro 8.0 system functions; `tonumber()` strips any formatting. Store as numeric so range/consistency checks are straightforward downstream.
- The AAPOR `210` code used on consent refusal is AAPOR 2023 "Refusal — respondent" (see `cspro_helpers.py` `AAPOR_DISPOSITION_OPTIONS`). The eligibility terminator at §4.2 should similarly reassign (`230` for eligible non-interview / tenure < 6mo fails re-screen).
- `INTERVIEWER_ID` is left blank — enumerator enters manually. Don't prefill from `fieldvar()` even if available, because enumerator assignments may rotate mid-day (two enumerators sharing one tablet).
- `AAPOR_DISPOSITION` on the CLOSING form is rewritten in `postproc` to the final code per AAPOR 2023 rules. Complete → `110`; Partial → `120`; Non-contact → `220`; etc.

---

## 5. Dispositions — Apr 13 LSS meeting + post-LSS E2-F1-009b

The six items previously held "open" are now dispositioned. Two still need ASPSI; four are closed in spec (generator constants listed so the reverse lookup works).

### Needs ASPSI

1. **Q63 ACCRED_WAIT days vs months** (original Bug #3) — Printed stem says "days"; bucket labels are in months. **Route to Juvy/Kidd** before Tranche 2: either (a) ASPSI rewrites labels to day buckets (`<30`, `31–60`, `>60`) or (b) edits the question stem to months. Default if no response before bench-test: keep months (`Q63_USE_DAY_BUCKETS = False`).
2. **Secondary data section structure** (original Bug #2) — Pages 30–34 (hospital census 6mo, HCW roster by cadre × employment type, YAKAP services, procurement vs charged prices, lab markup) still need a structural decision: record-per-month vs flat; separate CSPro app vs embedded records; paper-only collection vs CAPI. **Route to Juvy**. Default: empty stub records ship in the dcf (`SECONDARY_DATA_AS_STUBS = True`) so the dictionary opens and bench-test can proceed without the secondary-data path.

### Spec-decision (ASPSI may override)

3. **Eligibility termination behaviour** — `<6 months tenure` terminates the questionnaire at Q5 postproc and codes `ENUM_RESULT = Refused/Incomplete`. **Spec default**: terminate immediately (do not capture Sections B–H); enumerator re-screens at a different facility. PROC coded in §4.2.
4. **Q31 EMR NA-skip** (original Bug #4) — `Q31_NA_SKIPS = True`. **Spec default**: NA routes to Q35 alongside the other UHC9 NA branches; treat the source omission as a printing bug and enforce parity in CAPI logic. Flag in field manual.
5. **Q166 PD_NURSES audits omission** (original Bug #1) — `Q166_NURSES_INCLUDE_AUDITS = False`. **Spec default**: honour source; nurses' PD list ships without "Clinical audits" / "Surgical audits". Flag to ASPSI only if they surface it during Tranche 2 review.
6. **Q121 hospital-only options** — `Q121_DYNAMIC_VALUE_SET = False`. **Spec default**: single shared value set; facility-type enforcement happens via GATE rules on Q130 (PCF-only) and Q132–Q134 (hospital-only). If pilot reveals enumerator confusion from irrelevant options appearing, revisit with `setvalueset()` at Q121 preproc (pattern documented in §4.9).

---

## 6. Implementation order (recommended)

1. **Dispositioned bugs in §1** — all six are already landed or stubbed in `generate_dcf.py`; current build (12 records / 664 items) is bench-testable without further generator work. Revisit Bug #2 (secondary-data structure) and Bug #3 (Q63 units) only after ASPSI response.
2. **Open `FacilityHeadSurvey.dcf` in CSPro Designer**, validate the dictionary loads cleanly; inspect record layout (11 data records + root header, including the 4 `SEC_*` stubs and `REC_FACILITY_CAPTURE`).
3. **Build the Form file** (`.fmf`) — one form per record A–H; skip the `SEC_*` stubs and the off-form `REC_FACILITY_CAPTURE` (its items are wired via `onfocus` triggers, not placed on a data-entry form).
4. **Add PROC code** in this order:
   1. Field Control consent terminator (§4.14) + PSGC cascade (§4.15) + GPS/photo capture (§4.16)
   2. Section A eligibility at Q5 (§4.2) + tenure consistency at Q6 (§4.3)
   3. Section C generic UHC9 skip pattern (§4.4)
   4. Section D Q51 master gate (§4.5) + Q52 date (§4.6) + Q86/Q87 consistency (§4.7) + Q57 capitation (§4.8)
   5. Section F Q121 facility-type gating (§4.9) + generic why-difficult gate (§4.10)
   6. Section G skips (§4.11, §4.12)
   7. Other-specify enforcement generics (§4.13)
5. **Bench-test** with paper-walkthrough of 3 mock facility responses: one accredited Level-2 hospital, one non-accredited PCF, one terminated-on-tenure case. Verify the capture triggers fire correctly and the verification-photo filename lands next to the case data.
6. **Pretest readiness** — bundle as PFF for CSEntry Android distribution. Confirm `shared/PSGC-Cascade.apc`, `shared/Capture-Helpers.apc`, and the PSGC external lookup dictionaries (`shared/psgc_*.dcf`) are packaged alongside the .app.

---

*This spec is generated from the Apr 20 2026 Annex F1 PDF and the Apr 21 dcf (12 records / 671 items, post-GPS/photo capture pass + case-control extension). Update both this file and `generate_dcf.py` whenever the questionnaire is revised.*
