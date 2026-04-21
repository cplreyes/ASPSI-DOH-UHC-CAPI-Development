---
type: spec
project: ASPSI-DOH-CAPI-CSPro-Development
deliverable: F4 Household Survey — CAPI logic spec
date_created: 2026-04-21
status: draft
source_questionnaire: raw/Project-Deliverable-1_Apr20-submitted/Annex F4_Household Survey Questionnaire_UHC Year 2.pdf
source_dcf: deliverables/CSPro/F4/HouseholdSurvey.dcf
tags: [cspro, capi, skip-logic, validations, f4, household]
---

# F4 Household Survey — Skip Logic and Validations Spec

Source-of-truth for CSPro CAPI logic on `HouseholdSurvey.dcf`. Covers:

1. **Sanity-check findings** — schema gaps and discrepancies between the Apr 20 questionnaire (Q1–Q202, 17 sections) and the current dcf (21 records / 611 items).
2. **Skip-logic table** — every conditional jump extracted from the questionnaire, section by section A–Q.
3. **Cross-field validations** — HARD (block save), SOFT (warn-and-confirm), GATE (display-only conditional rendering).
4. **CSPro logic templates** — paste-ready snippets for Field Control, PSGC cascade, household-roster loop, WHO expenditure grid, financial bill-recall chain, distress financing.
5. **Open questions routing** — dispositioned per F3 convention (genuine ASPSI asks vs spec-decisions).
6. **Implementation order** — recommended build sequence.

All Q-numbers refer to the **Apr 20 printed questionnaire** (1–202); dcf item names follow the `Q{n}_*` convention. This spec mirrors the shape of `deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md` and `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md`.

> **Item-count provenance.** The Apr 20 F4 DCF is 21 records / 611 items capturing 202 numbered source questions. Expansion from source → dcf is driven by the same patterns as F3: payment/consumption matrices explode each row into flag + amount pairs, select-all items get per-option `_O01..On` flag items plus an `_OTHER_TXT` companion, and a separate `FIELD_CONTROL` + `HOUSEHOLD_GEO_ID` pair captures survey logistics and PSGC cascade. See `wiki/analyses/Analysis - Apr 20 DCF Generator Audit.md` for the per-chunk rewrite ledger (chunks 1–8, commits `fe3b567` → `001b796`).

---

## 1. Sanity-check findings (dcf vs Apr 20 questionnaire)

### A. Schema gaps — must be fixed in `generate_dcf.py` before CAPI build

| # | Item | Issue | Fix |
|---|---|---|---|
| 1 | **`C_HOUSEHOLD_ROSTER` not repeating** | Currently `occurrences.maximum = 1` — captures one household member only. Source (Annex F4 Section C) is an explicit roster keyed by member line number; Section J health-seeking is designed to loop over it. | Patch `generate_dcf.py` so `C_HOUSEHOLD_ROSTER` is written with `occurrences.maximum = 20` (reasonable upper bound; tuneable), and `MEMBER_LINE_NO` becomes the id-item of a nested sub-level — or keep the roster as a single-level repeating record with an id suffix. Blocks Section J looping. |
| 2 | **`J_HEALTH_SEEKING` not per-member** | Source: "looping over household members for health-seeking items" (36 items Q101–Q107). Currently a flat single-occurrence record. Either one health-seeking block per member (repeating) or one per-household (flat) — the former is what the source ordered. | Patch `generate_dcf.py` to make `J_HEALTH_SEEKING` repeating keyed by `MEMBER_LINE_NO`. Alternatively, confirm with ASPSI whether Section J applies to the respondent-only; honor source as printed otherwise. Linked to finding #1. |
| 3 | **Q47 placement** | `Q47_HH_HAS_PRIVATE_INS` lives in its own `C_HH_PRIVATE_INS_GATE` record between `C_HOUSEHOLD_ROSTER` and `D_UHC_AWARENESS`. Q47 is the household-level "does anyone in the HH have private insurance" gate — Q49/Q50 per-member insurance lives inside the roster. | Acceptable as-is: isolating the HH-level gate from the per-member loop keeps the roster schema clean. Document the split. |
| 4 | **Q2 birth date ↔ Q2.1 age** | Q2 captures `BIRTH_MONTH` + `BIRTH_YEAR`; Q2.1 captures `AGE`. Source asks "age on last birthday" — needs consistency rule: `AGE` must equal the computed year difference from BIRTH_YEAR given today's date (±1 for pre/post-birthday bracket). | HARD consistency rule in §3.2. |
| 5 | **Q18 amount + bracket duality** | Same pattern as F3 Q18. Q18_INCOME_AMOUNT + Q18_INCOME_BRACKET captured together — needs consistency check (amount falls in bracket). | HARD consistency rule in §3.2. |
| 6 | **Q15 IP_GROUP coded list** | Source says "A list will be provided" but Annex F4 ships free-text only (identical to F3 Q31). | Route to ASPSI (§5, item #1). Keep alpha as default. |
| 7 | **Q19 vs roster count** | `Q19_HH_SIZE_TOTAL` is the self-reported HH size; roster occurrences should equal Q19 (or Q19 − 1 if respondent is listed separately). Without the roster being repeating (finding #1), this check can't be enforced. | HARD post-roster rule once finding #1 is fixed: `count(C_HOUSEHOLD_ROSTER) = Q19_HH_SIZE_TOTAL`. |
| 8 | **Section N per-item "consumed" gate pattern** | 42 expenditure items use the three-column pattern `{Q}_CONSUMED` → `{Q}_PURCHASED_PHP` → `{Q}_INKIND_PHP`. Needs uniform gate: if `_CONSUMED = No`, both `_PURCHASED_PHP` and `_INKIND_PHP` must be 0 or blank. | Spec as HARD gate + PROC template in §4.9. |
| 9 | **Section N subtotals** | Q157, Q177, Q182, Q185 are `_SUBTOTAL_TOTAL_PHP` auto-compute items. Must be computed (not entered) from their panel's `_PURCHASED_PHP + _INKIND_PHP` sum. | HARD: item is auto-set, enumerator cannot edit. PROC template in §4.9. |
| 10 | **Section M bill-recall chain** | Q140_RECALL_BREAKDOWN + Q141_BILL_ITEMS + Q141.1_NO_RECEIPT_AMT + Q142_RECALL_PAYMENT + Q143_HOW_PAID form a recall chain: if Q140 = No, skip Q141/Q141.1; if Q142 = No, skip Q143. Also Q129 gates whether Section M applies at all (only HHs with confinement experience answer bill-recall). | Spec as skip-logic §2 Section M + PROC §4.8. |
| 11 | **Section M gate item is Q129 (in Section L)** | The HH-confinement gate that decides whether ZBB/MAIFIP/Bill questions apply lives at Q129 inside Section L (not at the top of M). Straightforward cross-section routing but must be explicit. | Spec in §2 routing preamble. |
| 12 | **Q199 WTP open-ended amount** | Source captures "willingness-to-pay for consultation" as a PHP amount plus an "other" specify. | HARD: Q199 ≥ 0; `Q199_WTP_OTHER_TXT` required only when "Other" option ticked. |
| 13 | **Q202 worry reasons — select-all capacity** | Only 3 options in dcf (`O01`–`O03`) plus `_OTHER_TXT`. Verify source has only 3; if more, generator needs to expand. | Verify against source PDF; flag if mismatch. |

### B. Cosmetic / acceptable as-is

- Informed-consent metadata (witness name, address, tel) lives in `FIELD_CONTROL` via `build_field_control()` — parallel to F1/F3 treatment. No Section A dcf duplicate needed.
- Long select-all lists (Q65 20 options, Q74 10 options, Q82 8 options) render fine on tablets in CSEntry 8.0.
- Q11_EDUCATION, Q12_EMPLOYMENT use full verbatim DOH labels — intentional per the verbatim-labels rule.

---

## 2. Skip-logic table

### Routing preamble (whole-instrument)

- **Consent terminator.** `FIELD_CONTROL.CONSENT_GIVEN = No` at the top of the interview → terminate with `ENUM_RESULT_FIRST_VISIT = Withdraw Participation/Consent`. Entire questionnaire (A–Q) is suppressed.
- **Respondent-is-HH-head gate (Q1).** Q1 captures whether the respondent is the household head. Per source, if the respondent is not the HH head, some items may still be asked but flagged; no hard skip — handle as SOFT validation in §3.1.
- **HH-confinement gate (Q129, Section L).** Q129 = Yes → Section M (ZBB/MAIFIP/Bill) fully asked. Q129 = No → Section M items Q132–Q143 are skipped (ZBB/MAIFIP awareness still asked per printed form; bill-recall chain Q138–Q143 is the confinement-dependent part). See Section M table below for the precise split.
- **Roster expansion (Section C).** After B is complete, enumerator enters the roster loop for `count = Q19_HH_SIZE_TOTAL` members. Section J (Health-Seeking) also loops over the same roster per source — see sanity finding #2.

### Section A — Introduction and Informed Consent

| Q | Condition | Skip to |
|---|---|---|
| — | `FIELD_CONTROL.CONSENT_GIVEN = No` | **Terminate interview** with `ENUM_RESULT_FIRST_VISIT = Withdraw Participation/Consent` |
| Q1 IS_HH_HEAD | = No | **Continue to Q2** (SOFT warn to enumerator: "Respondent is not the HH head — confirm they are a household decision-maker per sampling protocol") |

### Section B — Respondent Profile

| Q | Condition | Skip to |
|---|---|---|
| Q4 LGBTQIA | — | No skip; captured for profile only |
| Q7 IS_PWD | = No | **Q11** (skip Q8–Q10 disability detail) |
| Q9 PWD_CARD | = No | **Q11** (skip Q10 — disability type only captured when card verified, same pattern as F3 Q14) |
| Q14 IP_MEMBER | = No | **Q16** (skip Q15 IP group specify) |
| Q22 ELECTRICITY | — | No skip; socio-economic class battery continues |
| Q23 WATER_SOURCE | Piped/faucet options | Q24 asked; other sources → **Q25** (skip Q24 faucet-share) |
| Q23 WATER_SOURCE | Dug well / tube well / spring options | Q25 asked; other sources → **Q26** (skip Q25 tube-share) |

### Section C — Household Roster (per-member loop; repeats for each of Q19 members)

> Roster is keyed by `MEMBER_LINE_NO = 1..Q19_HH_SIZE_TOTAL`. Rules below apply to each member iteration independently.

| Q | Condition | Skip to |
|---|---|---|
| Q31 PRESENT | = No (not present at time of visit) | Per source, still capture Q32–Q50 from the HH head's knowledge; no skip |
| Q35 HAS_DISABILITY | = No | **Q39** (skip Q36 specify, Q37 card, Q38 type) |
| Q37 PWD_CARD | = No | **Q39** (skip Q38 disability-type — same as Section B) |
| Q41 EMPLOYMENT | Per source | No skip; GSIS/SSS/Pag-IBIG follow regardless |
| Q45 PHILHEALTH_REG | = No | **Q48** (skip Q46 member-category, Q46 other-specify) |
| Q49 PRIVATE_INS | = No / No private insurance | **End of member-iteration** (skip Q50 other-specify) |

**Then Q47 (gate in `C_HH_PRIVATE_INS_GATE`)**: after roster loop completes, `Q47_HH_HAS_PRIVATE_INS` captured once at household level. If the roster already shows any member with Q49 = Yes, Q47 auto-computes to Yes (SOFT verify).

### Section D — UHC Awareness

| Q | Condition | Skip to |
|---|---|---|
| Q51 UHC_HEARD | = No / Don't know | **Q54** (skip Q52 sources, Q53 understanding — entire Section D tail) |

### Section E — YAKAP/Konsulta Awareness

| Q | Condition | Skip to |
|---|---|---|
| Q54 YAKAP_HEARD | = No / Don't know | **Q57** (skip Q55 sources, Q56 understanding) |

### Section F — BUCAS Awareness and Utilization

| Q | Condition | Skip to |
|---|---|---|
| Q57 BUCAS_HEARD | = No / Don't know | **Q62** (skip Q58 sources, Q59 understanding, Q60 accessed, Q61 services) |
| Q60 BUCAS_ACCESSED | = No | **Q62** (skip Q61 services) |

### Section G — Access to Medicines

| Q | Condition | Skip to |
|---|---|---|
| Q62 PURCHASE_FREQ | = Never (5) | **Q69** (skip Q63–Q68 — never purchases → skip Rx/conditions/where/travel/ease) |
| Q69 GAMOT_HEARD | = No | **Q75** (skip Q70–Q74 — never heard of GAMOT) |
| Q72 GAMOT_OBTAINED | = No | **Q75** (skip Q73 meds list, Q74 where-rest) |
| Q75 BRAND_GEN_KNOWS | = No | **Q79** (skip Q76–Q78 — exit Section G) |
| Q76 BRAND_OR_GEN | = Branded only | **Q78** (skip Q77 why-generic) |
| Q76 BRAND_OR_GEN | = Generic only | **Q79** (skip Q78 why-branded; after Q77) |
| Q76 BRAND_OR_GEN | = Don't know / Not applicable | **Q79** (exit Section G) |

### Section H — PhilHealth Registration and Health Insurance

> Section H applies when at least one HH member has `Q45_PHILHEALTH_REG = Yes` in the roster. If no members are PhilHealth-registered, skip entire Section H.

| Q | Condition | Skip to |
|---|---|---|
| Q79 REG_SOURCE | captured | No skip |
| Q81 REG_DIFFICULTY | = No / No difficulty | **Q83** (skip Q82 difficulty reasons) |
| Q83 KNOWS_ASSIST | = No | **Q85** (skip Q84 where-assist) |
| Q86 PREMIUM_PAY | = No (not a premium-paying member category) | **Q89** (skip Q87, Q88 — only premium payers answer pay-difficulty) |
| Q87 PREMIUM_DIFFICULT | = No | **Q89** (skip Q88 diff-paying reasons) |

### Section I — Primary Care

| Q | Condition | Skip to |
|---|---|---|
| Q89 HAS_USUAL_FACILITY | = Yes | Q89.1 facility name captured, proceed to Q90 |
| Q89 HAS_USUAL_FACILITY | = No | **Q93** (skip Q89.1, Q90, Q91, Q92 — no usual facility → go straight to why-not reasons) |
| Q90 IS_USUAL_FOR_GENERAL | = Yes | **Q94** (skip Q91 why-went, Q92 facility type, Q93 why-not — they use usual facility for general care, proceed to transport) |
| Q90 IS_USUAL_FOR_GENERAL | = No | Q91, Q92 asked; Q93 skipped |
| Q97 KNOWS_BOOKING | = No | **Q100** (skip Q98, Q99 phone advice — doesn't know booking → phone questions moot) |

### Section J — Household members' Health-Seeking (loops per member; see sanity #2)

> Per source, Section J loops over the household roster. Until `J_HEALTH_SEEKING` is made repeating (schema gap #2), treat this section as single-respondent-scope and add a pilot-time note.

| Q | Condition | Skip to |
|---|---|---|
| Q101 CHECKUP_FREQ | = Never / Don't know | **Q105** (skip Q102 visit reason, Q103 care type, Q104 preventive) |
| Q104 PREVENTIVE | — | No skip |
| Q105 FORGONE_CARE | = No / No forgone care | **End of member-iteration** (skip Q106 forgone-why, Q107 other-actions) |

### Section K — Referrals

| Q | Condition | Skip to |
|---|---|---|
| Q108 REFERRED | = No | **Q126** (skip Q109–Q125 — jumps straight to Section L NBB) |
| Q112 VISITED | = Yes | **Q114** (skip Q113 why-not) |
| Q112 VISITED | = No, not planning **or** Not yet, planning | Q113 asked; after Q113 → **Q114** |
| Q117 SPECIALIST_FOLLOWUP | = No | **Q119** (skip Q118 sat-referral-process) |
| Q119 PCF_REFERRAL | = Yes | **Q120** PCP-knows, then Q122 discussed-places (skip Q121 why-hospital) |
| Q119 PCF_REFERRAL | = No | **Q121** (skip Q120 — not PCP referral → why-hospital asked) |
| Q124 PCP_WROTE_INFO | completed | **Q125** (close Section K) |

### Section L — NBB Awareness

| Q | Condition | Skip to |
|---|---|---|
| Q126 NBB_HEARD | = No / Don't know | **Q129** (skip Q127 sources, Q128 understanding) |
| Q129 HH_CONFINED | = No | **Q144** (skip Q130, Q131 NBB utilization; skip Q132–Q143 bill-recall tail of Section M — proceed straight to Section N) |
| Q130 HOSPITAL_TYPE | = Public (per source) | Q131 NBB_OOP asked (NBB applies to public only per program design) |
| Q130 HOSPITAL_TYPE | = Private | **Q132** (skip Q131 — NBB doesn't apply to private) |

### Section M — ZBB / MAIFIP / Bill Recall

> Section M only runs when `Q129_HH_CONFINED = Yes`. The ZBB awareness sub-block (Q132–Q134) is asked regardless of confinement per source; bill-recall (Q138–Q143) is strictly confinement-dependent.

| Q | Condition | Skip to |
|---|---|---|
| Q132 ZBB_HEARD | = No / Don't know | **Q136** (skip Q133 sources, Q134 understanding, Q135 ZBB-OOP) |
| Q135 ZBB_OOP | captured only if ZBB-eligible facility visited | Per source note — enumerator gate |
| Q136 MAIFIP_HEARD | = No / Don't know | **Q138** (skip Q137 sources) |
| Q138 MOST_EXPENSIVE | captured | No skip |
| Q140 RECALL_BREAKDOWN | = No | **Q142** (skip Q141 bill-items, Q141.1 no-receipt-amount) |
| Q141 BILL_ITEMS | select-all | No skip; Q141.1 conditional on presence of "no receipt" option |
| Q142 RECALL_PAYMENT | = No | **Q144** (skip Q143 how-paid — end of Section M) |

### Section N — Household Expenditures (WHO/SHA module)

> 42 consumption items, each with three-column pattern `_CONSUMED` → `_PURCHASED_PHP` → `_INKIND_PHP`. Four auto-computed subtotals (Q157 food, Q177 health 12-month, Q182 health 6-month, Q185 health 1-month).

| Q | Condition | Skip to |
|---|---|---|
| `{Q}_CONSUMED` | = No | Next consumption item (skip `_PURCHASED_PHP`, `_INKIND_PHP` for this row) |
| Q157 FOOD_SUBTOTAL | — | Auto-compute; enumerator cannot enter |
| Q177/Q182/Q185 HEALTH_SUBTOTAL | — | Auto-compute |

### Section O — Sources of Funds for Health

> Q186–Q194 are yes/no per-source flags (9 sources). If HH had no health expenditure (Section N health totals = 0), Section O is technically moot but still asked for population-level coverage.

| Q | Condition | Skip to |
|---|---|---|
| Q186–Q194 | each yes/no | No skip between sources |
| Q194 OTHER_SOURCE | = Yes | `Q194_OTHER_TXT` required |
| Q195 INCOME_PCT | captured as % | No skip |
| Q196 FOREGONE | select-all | No skip; `Q196_OTHER_TXT` if "Other" ticked |

### Section P — Financial Risk Protection

| Q | Condition | Skip to |
|---|---|---|
| Q197 DELAYED_CARE | yes/no/N/A | No skip |
| Q198 NOT_FOLLOWED | yes/no/N/A | No skip |
| Q199 WTP_CONSULT | PHP amount | No skip; `Q199_WTP_OTHER_TXT` if "Other" option ticked |

### Section Q — Financial Anxiety

| Q | Condition | Skip to |
|---|---|---|
| Q200 REDUCED_SPEND | yes/no | No skip |
| Q201 WORRIED | yes/no/sometimes | No skip |
| Q202 WORRY_REASONS | select-all | **End of questionnaire** — set `ENUM_RESULT_FINAL_VISIT = Completed` |

---

## 3. Validations

HARD = block save; SOFT = warn-and-confirm; GATE = display-only (items rendered conditionally, don't validate when suppressed).

### 3.1 Field Control and Geographic ID

| Item | Rule | Severity |
|---|---|---|
| `SURVEY_TEAM_LEADER_S_NAME`, `ENUMERATOR_S_NAME` | Required, non-blank | HARD |
| `DATE_FIRST_VISITED`, `DATE_FINAL_VISIT` | Required, valid date ≤ today | HARD |
| `DATE_FIRST_VISITED ≤ DATE_FINAL_VISIT` | Temporal ordering | HARD |
| `TOTAL_NUMBER_OF_VISITS` | `1 ≤ n ≤ 10` (warn if > 3) | HARD + SOFT |
| `ENUM_RESULT_FIRST_VISIT`, `ENUM_RESULT_FINAL_VISIT` | Required, ∈ value set | HARD |
| `CONSENT_GIVEN` | Required, ∈ {Yes, No}; if No → terminate | HARD |
| `HH_LISTING_NO` | Required, matches F3b listing form entry | HARD |
| `REGION` → `PROVINCE_HUC` → `CITY_MUNICIPALITY` → `BARANGAY` | PSGC cascade; each level must match a child of the prior level | HARD (per-level) |
| `LATITUDE`, `LONGITUDE` | Within Philippine bounding box if captured; optional | SOFT |
| `HH_ADDRESS` | Required, non-blank | HARD |
| `CLASSIFICATION` | ∈ {Urban, Rural} — matches barangay classification from PSA | HARD |

### 3.2 Section A — Informed Consent

| Item | Rule | Severity |
|---|---|---|
| `Q1_IS_HH_HEAD` | Required, ∈ {Yes, No}; if No → SOFT warn "Confirm respondent is HH decision-maker per protocol" | HARD + SOFT |

### 3.3 Section B — Respondent Profile

| Item | Rule | Severity |
|---|---|---|
| `RESPONDENT_NAME` | Required, non-blank | HARD |
| `Q2_BIRTH_MONTH` | `1 ≤ m ≤ 12` | HARD |
| `Q2_BIRTH_YEAR` | `1900 ≤ y ≤ current_year` | HARD |
| `Q2_1_AGE` | `0 ≤ age ≤ 120` | HARD |
| Q2 ↔ Q2.1 consistency | `abs(current_year − Q2_BIRTH_YEAR − Q2_1_AGE) ≤ 1` | HARD |
| `Q3_SEX` | Required, ∈ {Male, Female, Other} | HARD |
| `Q4_LGBTQIA` | Required, ∈ value set | HARD |
| `Q5_GROUP = Other` | `Q5_GROUP_OTHER_TXT` required | HARD |
| `Q6_CIVIL_STATUS` | Required, ∈ value set | HARD |
| `Q7_IS_PWD` | Required, ∈ {Yes, No} | HARD |
| Q8–Q10 enabled | `Q7_IS_PWD = Yes` | GATE |
| Q10 enabled | `Q7_IS_PWD = Yes` **and** `Q9_PWD_CARD = Yes` | GATE |
| `Q10_DISABILITY_TYPE = Other` | `Q10_DISABILITY_OTHER_TXT` required | HARD |
| `Q11_EDUCATION` | Required, ∈ value set | HARD |
| `Q11_EDUCATION = Other` | `Q11_EDUCATION_OTHER_TXT` required | HARD |
| `Q12_EMPLOYMENT` | Required, ∈ value set | HARD |
| `Q13_INCOME_SOURCE` | Required, non-blank | HARD |
| `Q14_IP_MEMBER` | Required, ∈ {Yes, No} | HARD |
| Q15 enabled | `Q14_IP_MEMBER = Yes` | GATE |
| `Q15_IP_GROUP` | Required when enabled, non-blank (pending coded list — see §5 #1) | HARD |
| `Q16_4PS` | Required, ∈ {Yes, No} | HARD |
| `Q17_DECISION_MAKER` | Required, ∈ value set | HARD |
| `Q17_DECISION_MAKER = Other` | `Q17_DECISION_MAKER_OTHER_TXT` required | HARD |
| `Q18_INCOME_AMOUNT` | `0 ≤ amt ≤ 99,999,999` | HARD |
| `Q18_INCOME_BRACKET` | Required, ∈ value set | HARD |
| Q18 consistency | `Q18_INCOME_AMOUNT` falls within `Q18_INCOME_BRACKET` | HARD |
| `Q19_HH_SIZE_TOTAL` | `1 ≤ n ≤ 20` (warn if > 10) | HARD + SOFT |
| `Q20_HH_CHILDREN` | `0 ≤ n ≤ Q19_HH_SIZE_TOTAL` | HARD |
| `Q21_HH_SENIORS` | `0 ≤ n ≤ Q19_HH_SIZE_TOTAL` | HARD |
| Q19 vs Q20+Q21 | `Q20 + Q21 ≤ Q19` (children + seniors ≤ total) | HARD |
| `Q22_ELECTRICITY` | Required, ∈ {Yes, No} | HARD |
| `Q23_WATER_SOURCE` | Required, ∈ value set | HARD |
| `Q23 = Other` | `Q23_WATER_OTHER_TXT` required | HARD |
| Q24 enabled | `Q23_WATER_SOURCE ∈ {piped, faucet}` codes | GATE |
| Q25 enabled | `Q23_WATER_SOURCE ∈ {dug well, tube, spring}` codes | GATE |
| `Q26_REFRIGERATOR`, `Q27_TELEVISION`, `Q28_WASHING_MACHINE` | Required, ∈ {Yes, No} | HARD |
| `Q29_SOCIOECONOMIC_CLASS` | Auto-classified from Q22–Q28 (enumerator confirms) | SOFT |

### 3.4 Section C — Household Roster (per-member; see sanity #1 before build)

| Item (per member iteration) | Rule | Severity |
|---|---|---|
| `MEMBER_LINE_NO` | Auto-incremented; unique per iteration | HARD |
| `Q30_NAME` | Required, non-blank | HARD |
| `Q31_PRESENT` | Required, ∈ {Yes, No} | HARD |
| `Q32_AGE` | `0 ≤ age ≤ 120` | HARD |
| `Q33_SEX` | Required, ∈ value set | HARD |
| `Q34_RELATIONSHIP` | Required, ∈ value set; first iteration should be `Self` or `Head` | HARD + SOFT |
| `Q35_HAS_DISABILITY` | Required, ∈ {Yes, No} | HARD |
| Q36–Q38 enabled | `Q35_HAS_DISABILITY = Yes` | GATE |
| Q38 enabled | `Q35 = Yes` **and** `Q37_PWD_CARD = Yes` | GATE |
| `Q38_DISABILITY_TYPE = Other` | `Q38_DISABILITY_OTHER_TXT` required | HARD |
| `Q39_CIVIL_STATUS` | Required, ∈ value set | HARD |
| Q39 vs Q32 | If `Q32_AGE < 15` and `Q39 ≠ Single`, SOFT warn (plausibility) | SOFT |
| `Q40_EDUCATION` | Required, ∈ value set | HARD |
| `Q41_EMPLOYMENT` | Required, ∈ value set | HARD |
| `Q42_GSIS`, `Q43_SSS`, `Q44_PAGIBIG` | Required, ∈ {Yes, No, Don't know} | HARD |
| `Q45_PHILHEALTH_REG` | Required, ∈ value set | HARD |
| Q46 enabled | `Q45_PHILHEALTH_REG = Yes` | GATE |
| `Q46_MEMBER_CATEGORY = Other` | `Q46_MEMBER_OTHER_TXT` required | HARD |
| `Q48_NAME_FIRST` | Required when `Q45 = Yes`, non-blank | HARD |
| `Q49_PRIVATE_INS` | Required, ∈ value set | HARD |
| `Q49 = Other` | `Q50_PRIVATE_INS_OTHER_TXT` required | HARD |
| Post-roster: `count(C_HOUSEHOLD_ROSTER) = Q19_HH_SIZE_TOTAL` | Blocks save if mismatch (tunable ±1 for respondent-in-roster convention) | HARD |
| Post-roster: `Q47_HH_HAS_PRIVATE_INS` | Auto-set to Yes if any `Q49_PRIVATE_INS = Yes` in roster; enumerator confirms | SOFT |

### 3.5 Section D — UHC Awareness

| Item | Rule | Severity |
|---|---|---|
| `Q51_UHC_HEARD` | Required, ∈ {Yes, No, Don't know} | HARD |
| Q52, Q53 enabled | `Q51_UHC_HEARD = Yes` | GATE |
| `Q52_UHC_SOURCE` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q52_UHC_SOURCE` "I don't know" equivalent | Cannot be combined with any other option | HARD |
| `Q52 = Other` | `Q52_UHC_SOURCE_OTHER_TXT` required | HARD |
| `Q53_UHC_UNDERSTAND` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q53 = Other` | `Q53_UHC_UNDERSTAND_OTHER_TXT` required | HARD |

### 3.6 Section E — YAKAP/Konsulta (mirrors §3.5 shape)

| Item | Rule | Severity |
|---|---|---|
| `Q54_YAKAP_HEARD` | Required, ∈ {Yes, No, Don't know} | HARD |
| Q55, Q56 enabled | `Q54_YAKAP_HEARD = Yes` | GATE |
| `Q55_YAKAP_SOURCE` / `Q56_YAKAP_UNDERSTAND` select-all | ≥ 1 option ticked when enabled; "Don't know" mutex; `_OTHER_TXT` required on Other | HARD |

### 3.7 Section F — BUCAS Awareness and Utilization

| Item | Rule | Severity |
|---|---|---|
| `Q57_BUCAS_HEARD` | Required, ∈ {Yes, No, Don't know} | HARD |
| Q58, Q59 enabled | `Q57_BUCAS_HEARD = Yes` | GATE |
| `Q58_BUCAS_SOURCE` / `Q59_BUCAS_UNDERSTAND` | Select-all; "Don't know" mutex; `_OTHER_TXT` on Other | HARD |
| `Q60_BUCAS_ACCESSED` | Required when `Q57 = Yes`, ∈ {Yes, No} | HARD |
| Q61 enabled | `Q60_BUCAS_ACCESSED = Yes` | GATE |
| `Q61_BUCAS_SERVICES` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q61 = Other` | `Q61_BUCAS_SERVICES_OTHER_TXT` required | HARD |

### 3.8 Section G — Access to Medicines

| Item | Rule | Severity |
|---|---|---|
| `Q62_PURCHASE_FREQ` | Required, ∈ {1–5} | HARD |
| Q63–Q68 enabled | `Q62_PURCHASE_FREQ ≠ 5 (Never)` | GATE |
| `Q63_PRESCRIPTION_TYPE` | Required when enabled, ∈ value set | HARD |
| `Q64_MEDICATIONS_LIST` | Required when enabled, non-blank; ≤ 240 chars (monitor per F3 note) | HARD |
| `Q65_CONDITIONS` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q65 = "No condition — regular check-up only"` | Cannot combine with any other option | HARD |
| `Q65 = Other` | `Q65_CONDITIONS_OTHER_TXT` required | HARD |
| `Q66_WHERE_BUY` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q66 = Other` | `Q66_WHERE_BUY_OTHER_TXT` required | HARD |
| `Q67_TIME_TO_PHARMACY` | `0 ≤ t ≤ 1440` minutes (24h cap) | HARD |
| `Q68_PHARMACY_ACCESS` | Required when enabled, ∈ value set | HARD |
| `Q69_GAMOT_HEARD` | Required, ∈ {Yes, No} | HARD |
| Q70–Q74 enabled | `Q69_GAMOT_HEARD = Yes` | GATE |
| `Q70_GAMOT_SOURCE` / `Q71_GAMOT_UNDERSTAND` | Select-all; "Don't know" mutex; `_OTHER_TXT` on Other | HARD |
| `Q72_GAMOT_OBTAINED` | Required when enabled, ∈ {Yes, No} | HARD |
| Q73, Q74 enabled | `Q72_GAMOT_OBTAINED = Yes` | GATE |
| `Q73_GAMOT_MEDS_LIST` | Required when enabled, non-blank; ≤ 240 chars | HARD |
| `Q74_WHERE_REST` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q74 = Other` | `Q74_WHERE_REST_OTHER_TXT` required | HARD |
| `Q75_BRAND_GEN_KNOWS` | Required, ∈ {Yes, No} | HARD |
| Q76–Q78 enabled | `Q75_BRAND_GEN_KNOWS = Yes` | GATE |
| `Q76_BRAND_OR_GEN` | Required when enabled, ∈ value set | HARD |
| Q77 enabled | `Q76_BRAND_OR_GEN ∈ {Generic, Both}` | GATE |
| Q78 enabled | `Q76_BRAND_OR_GEN ∈ {Branded, Both}` | GATE |
| `Q77_WHY_GENERIC` / `Q78_WHY_BRANDED` | Select-all; "Don't know" mutex; `_OTHER_TXT` on Other | HARD |

### 3.9 Section H — PhilHealth Registration (HH-level)

| Item | Rule | Severity |
|---|---|---|
| Section H enabled | At least one roster member has `Q45_PHILHEALTH_REG = Yes` | GATE |
| `Q79_REG_SOURCE` | Required, ∈ value set | HARD |
| `Q79 = Other` | `Q79_REG_SOURCE_OTHER_TXT` required | HARD |
| `Q80_ASSIST` | Required, ∈ value set | HARD |
| `Q80 = Other` | `Q80_ASSIST_OTHER_TXT` required | HARD |
| `Q81_REG_DIFFICULTY` | Required, ∈ {Yes, No} | HARD |
| Q82 enabled | `Q81 = Yes` | GATE |
| `Q82_DIFFICULTY_REASONS` select-all | ≥ 1 option when enabled | HARD |
| `Q82 = Other` | `Q82_DIFFICULTY_REASONS_OTHER_TXT` required | HARD |
| `Q83_KNOWS_ASSIST` | Required, ∈ {Yes, No} | HARD |
| Q84 enabled | `Q83 = Yes` | GATE |
| `Q84_WHERE_ASSIST` | Required when enabled, non-blank | HARD |
| `Q85_BENEFITS` select-all | ≥ 1 option ticked | HARD |
| `Q85 = Other` | `Q85_BENEFITS_OTHER_TXT` required | HARD |
| `Q86_PREMIUM_PAY` | Required, ∈ {Yes, No}; `= Yes` only if roster shows a premium-paying category | HARD + SOFT |
| Q87, Q88 enabled | `Q86_PREMIUM_PAY = Yes` | GATE |
| `Q87_PREMIUM_DIFFICULT` | Required when enabled, ∈ {Yes, No} | HARD |
| Q88 enabled | `Q87 = Yes` | GATE |
| `Q88_DIFF_PAYING` select-all | ≥ 1 option when enabled; `_OTHER_TXT` on Other | HARD |

### 3.10 Section I — Primary Care

| Item | Rule | Severity |
|---|---|---|
| `Q89_HAS_USUAL_FACILITY` | Required, ∈ {Yes, No} | HARD |
| Q89.1, Q90 enabled | `Q89 = Yes` | GATE |
| `Q89_1_FACILITY_NAME` | Required when enabled, non-blank | HARD |
| `Q90_IS_USUAL_FOR_GENERAL` | Required when enabled, ∈ {Yes, No} | HARD |
| Q91, Q92 enabled | `Q89 = Yes` **and** `Q90 = No` | GATE |
| Q93 enabled | `Q89 = No` | GATE |
| `Q91_WHY_WENT` / `Q93_WHY_NOT` select-all | ≥ 1 option; `_OTHER_TXT` on Other | HARD |
| `Q92_FACILITY_TYPE` | Required when enabled, ∈ value set; `Other` → `_OTHER_TXT` | HARD |
| `Q94_TRANSPORT` select-all | ≥ 1 option; `_OTHER_TXT` on Other | HARD |
| `Q95_TRAVEL_TIME_MIN` | `0 ≤ t ≤ 1440` minutes | HARD |
| `Q96_TRAVEL_COST_PHP` | `0 ≤ amt ≤ 99,999` | HARD |
| `Q97_KNOWS_BOOKING` | Required, ∈ {Yes, No} | HARD |
| Q98, Q99 enabled | `Q97 = Yes` | GATE |
| `Q98_PHONE_ADVICE_OPEN`, `Q99_PHONE_ADVICE_CLOSED` | Required when enabled, ∈ value set | HARD |
| `Q100_LEAVE_WORK_SCHOOL` | Required, ∈ {Yes, No} | HARD |

### 3.11 Section J — Health-Seeking (per-member iteration; see sanity #2)

| Item | Rule | Severity |
|---|---|---|
| `Q101_CHECKUP_FREQ` | Required, ∈ value set | HARD |
| `Q101 = Other` | `Q101_CHECKUP_FREQ_OTHER_TXT` required | HARD |
| Q102, Q103, Q104 enabled | `Q101 ∉ {Never, Don't know}` | GATE |
| `Q102_VISIT_REASON` select-all | ≥ 1 option when enabled; `_OTHER_TXT` on Other | HARD |
| `Q103_CARE_TYPE` select-all | ≥ 1 option when enabled; `_OTHER_TXT` on Other | HARD |
| `Q104_PREVENTIVE` | Required when enabled, ∈ {Yes, No} | HARD |
| `Q105_FORGONE_CARE` | Required, ∈ {Yes, No} | HARD |
| Q106, Q107 enabled | `Q105 = Yes` | GATE |
| `Q106_FORGONE_WHY` / `Q107_OTHER_ACTIONS` select-all | ≥ 1 option when enabled; `_OTHER_TXT` on Other | HARD |

### 3.12 Section K — Referrals

| Item | Rule | Severity |
|---|---|---|
| `Q108_REFERRED` | Required, ∈ {Yes, No} | HARD |
| Q109–Q125 enabled | `Q108 = Yes` | GATE |
| `Q109_TYPE` select-all | ≥ 1 option when enabled; `_OTHER_TXT` on Other | HARD |
| `Q110_SPECIALIST` | Required when enabled, ∈ value set; `Other` → `_OTHER_TXT` | HARD |
| `Q111_METHOD` | Required when enabled, ∈ value set; `Other` → `_OTHER_TXT` | HARD |
| `Q112_VISITED` | Required when enabled, ∈ value set | HARD |
| Q113 enabled | `Q112 ∈ {Not planning, Not yet}` | GATE |
| `Q113_WHY_NOT` select-all | ≥ 1 option when enabled; `_OTHER_TXT` on Other | HARD |
| `Q114_DISCUSSED_PLACES`, `Q115_HELPED_APPT`, `Q116_WROTE_INFO` | Required when enabled, ∈ {Yes, No} | HARD |
| `Q117_SPECIALIST_FOLLOWUP` | Required when enabled, ∈ {Yes, No} | HARD |
| Q118 enabled | `Q117 = Yes` | GATE |
| `Q118_SAT_REFERRAL_PROCESS` | Required when enabled, ∈ satisfaction codes | HARD |
| `Q119_PCF_REFERRAL` | Required when enabled, ∈ {Yes, No} | HARD |
| Q120, Q122, Q123, Q124 enabled | `Q119 = Yes` | GATE |
| Q121 enabled | `Q119 = No` | GATE |
| `Q120_PCP_KNOWS` | Required when enabled, ∈ value set | HARD |
| `Q121_WHY_HOSPITAL` select-all | ≥ 1 option when enabled; "Don't know" mutex; `_OTHER_TXT` on Other | HARD |
| `Q122_PCP_DISCUSSED_PLACES`, `Q123_PCP_HELPED_APPT`, `Q124_PCP_WROTE_INFO` | Required when enabled, ∈ {Yes, No} | HARD |
| `Q125_SAT_REFERRAL_EXP` | Required when `Q108 = Yes`, ∈ satisfaction codes | HARD |

### 3.13 Section L — NBB Awareness

| Item | Rule | Severity |
|---|---|---|
| `Q126_NBB_HEARD` | Required, ∈ {Yes, No, Don't know} | HARD |
| Q127, Q128 enabled | `Q126 = Yes` | GATE |
| `Q127_NBB_SOURCE` / `Q128_NBB_UNDERSTAND` | Select-all; "Don't know" mutex; `_OTHER_TXT` on Other | HARD |
| `Q129_HH_CONFINED` | Required, ∈ {Yes, No} | HARD |
| Q130, Q131 enabled | `Q129 = Yes` | GATE |
| `Q130_HOSPITAL_TYPE` | Required when enabled, ∈ value set | HARD |
| Q131 enabled | `Q129 = Yes` **and** `Q130 = Public` | GATE |
| `Q131_NBB_OOP` | Required when enabled, ∈ value set | HARD |

### 3.14 Section M — ZBB / MAIFIP / Bill

| Item | Rule | Severity |
|---|---|---|
| `Q132_ZBB_HEARD` | Required, ∈ {Yes, No, Don't know} | HARD |
| Q133, Q134 enabled | `Q132 = Yes` | GATE |
| `Q133_ZBB_SOURCE` / `Q134_ZBB_UNDERSTAND` | Select-all; "Don't know" mutex; `_OTHER_TXT` on Other | HARD |
| Q135 enabled | `Q129 = Yes` (HH had confinement) **and** `Q132 = Yes` | GATE |
| `Q135_ZBB_OOP` | Required when enabled, ∈ value set | HARD |
| `Q136_MAIFIP_HEARD` | Required, ∈ {Yes, No, Don't know} | HARD |
| Q137 enabled | `Q136 = Yes` | GATE |
| `Q137_MAIFIP_SOURCE` | Select-all; "Don't know" mutex; `_OTHER_TXT` on Other | HARD |
| **Bill-recall chain (Q138–Q143)** — all enabled only when `Q129_HH_CONFINED = Yes` | | GATE |
| `Q138_MOST_EXPENSIVE` | Required when enabled, non-blank (free-text description of most expensive confinement) | HARD |
| `Q139_FINAL_AMOUNT_PHP` | `0 ≤ amt ≤ 999,999,999` when enabled | HARD |
| `Q140_RECALL_BREAKDOWN` | Required when enabled, ∈ {Yes, No} | HARD |
| Q141, Q141.1 enabled | `Q140 = Yes` | GATE |
| `Q141_BILL_ITEMS` select-all | ≥ 1 option when enabled; `_OTHER_TXT` on Other | HARD |
| Q141.1 enabled | `Q141_BILL_ITEMS` includes "no receipt" row | GATE |
| `Q141_1_NO_RECEIPT_AMT_PHP` | `0 ≤ amt ≤ Q139_FINAL_AMOUNT_PHP` when enabled | HARD |
| `Q142_RECALL_PAYMENT` | Required when `Q129 = Yes`, ∈ {Yes, No} | HARD |
| Q143 enabled | `Q142 = Yes` | GATE |
| `Q143_HOW_PAID` select-all | ≥ 1 option when enabled; `_OTHER_TXT` on Other | HARD |

### 3.15 Section N — Household Expenditures (WHO/SHA)

| Item (pattern — applies to Q144–Q156, Q158–Q176, Q178–Q184) | Rule | Severity |
|---|---|---|
| `{Q}_CONSUMED` | Required, ∈ {Yes, No} | HARD |
| `{Q}_PURCHASED_PHP`, `{Q}_INKIND_PHP` | Required when `_CONSUMED = Yes`, `≥ 0`; MUST be 0 or blank when `_CONSUMED = No` | HARD |
| `{Q}_PURCHASED_PHP + {Q}_INKIND_PHP > 0` | When `_CONSUMED = Yes`, at least one amount > 0 | HARD |

**Panel subtotals (auto-computed, read-only):**

| Item | Computation | Severity |
|---|---|---|
| `Q157_FOOD_SUBTOTAL_TOTAL_PHP` | Sum of `{Q144..Q156}_PURCHASED_PHP + {Q144..Q156}_INKIND_PHP` | HARD (auto; no edit) |
| `Q177_HEALTH_12M_SUBTOTAL_TOTAL_PHP` | Sum of `{Q173..Q176}_PURCHASED_PHP + _INKIND_PHP` | HARD (auto) |
| `Q182_HEALTH_6M_SUBTOTAL_TOTAL_PHP` | Sum of `{Q178..Q181}_PURCHASED_PHP + _INKIND_PHP` | HARD (auto) |
| `Q185_HEALTH_1M_SUBTOTAL_TOTAL_PHP` | Sum of `{Q183..Q184}_PURCHASED_PHP + _INKIND_PHP` | HARD (auto) |

**Cross-section sanity:**

| Check | Severity |
|---|---|
| If `Q129_HH_CONFINED = Yes` but `Q175_INPATIENT_PURCHASED_PHP + Q175_INPATIENT_INKIND_PHP = 0`, SOFT warn | SOFT |
| If any health-expenditure subtotal > `3 × Q18_INCOME_AMOUNT`, SOFT warn (catastrophic-expenditure plausibility) | SOFT |

### 3.16 Section O — Sources of Funds

| Item | Rule | Severity |
|---|---|---|
| `Q186_CURRENT_INCOME`, `Q187_SAVINGS`, `Q188_SOLD_ASSETS`, `Q189_BORROW_FAMILY`, `Q190_BORROW_INST`, `Q191_REMITTANCE`, `Q192_GOVT_ASSIST`, `Q193_LGU_DONATION`, `Q194_OTHER_SOURCE` | Required, ∈ {Yes, No} | HARD |
| `Q194 = Yes` | `Q194_OTHER_TXT` required | HARD |
| `Q195_INCOME_PCT` | `0 ≤ pct ≤ 100` (percentage of current income spent on health) | HARD |
| `Q196_FOREGONE` select-all | ≥ 1 option when foregone any; `_OTHER_TXT` on Other | HARD |
| Source-of-funds vs. Q195 sanity | If all Q186–Q194 = No but `Q195_INCOME_PCT > 0`, SOFT warn | SOFT |

### 3.17 Section P — Financial Risk Protection

| Item | Rule | Severity |
|---|---|---|
| `Q197_DELAYED_CARE` | Required, ∈ value set {Yes, No, N/A} | HARD |
| `Q198_NOT_FOLLOWED` | Required, ∈ value set | HARD |
| `Q199_WTP_CONSULT` | `0 ≤ amt ≤ 99,999` (WTP amount in PHP) | HARD |
| `Q199` "Other" ticked | `Q199_WTP_OTHER_TXT` required | HARD |
| Q199 vs Q18 sanity | If `Q199 > 0.5 × Q18_INCOME_AMOUNT`, SOFT warn | SOFT |

### 3.18 Section Q — Financial Anxiety

| Item | Rule | Severity |
|---|---|---|
| `Q200_REDUCED_SPEND` | Required, ∈ value set | HARD |
| `Q201_WORRIED` | Required, ∈ value set | HARD |
| Q202 enabled | `Q201 ∈ {Yes, Sometimes}` | GATE |
| `Q202_WORRY_REASONS` select-all | ≥ 1 option when enabled; `_OTHER_TXT` on Other | HARD |
| Q202 completion | Set `ENUM_RESULT_FINAL_VISIT = Completed` | HARD (PROC) |

---

## 4. CSPro logic templates

Item names match `generate_dcf.py`. Paste into the corresponding `PROC` blocks in CSPro Designer. Shared helpers (`is_don_code`, select-all mutex, PSGC cascade) follow the same shapes as F3 `§4.1`–`§4.3`; repeated here only where F4 has a unique pattern.

### 4.1 Helper: global preproc

```cspro
PROC GLOBAL
numeric currentYYYYMMDD;
numeric currentYear;
numeric currentMonth;
numeric currentDay;
numeric rosterIdx;

PROC HOUSEHOLDSURVEY_DICT
preproc
  currentYYYYMMDD = sysdate();
  currentYear  = int(currentYYYYMMDD / 10000);
  currentMonth = int(mod(currentYYYYMMDD, 10000) / 100);
  currentDay   = mod(currentYYYYMMDD, 100);
```

### 4.2 Field Control + consent terminator

```cspro
PROC FIELD_CONTROL
postproc
  if CONSENT_GIVEN = 2 then           { 2 = No }
    ENUM_RESULT_FIRST_VISIT = 5;      { Withdraw Participation/Consent — confirm code }
    endgroup;                         { close interview; no data past here }
  endif;
```

### 4.3 PSGC cascade gate

(Identical to F3 §4.3 — REGION → PROVINCE_HUC → CITY_MUNICIPALITY → BARANGAY each validated against the PSA-loaded value sets. Copy from the F3 spec.)

### 4.4 Section A + B consistency

```cspro
PROC Q1_IS_HH_HEAD
postproc
  if Q1_IS_HH_HEAD = 2 then           { Not HH head }
    errmsg("Confirm respondent is a household decision-maker per sampling protocol (continue if yes)", soft);
  endif;

PROC Q2_1_AGE
postproc
  { Birth-year ↔ age consistency }
  numeric computedAge;
  computedAge = currentYear - Q2_BIRTH_YEAR;
  if Q2_BIRTH_MONTH > currentMonth then computedAge = computedAge - 1; endif;
  if abs(Q2_1_AGE - computedAge) > 1 then
    errmsg("Age %d doesn't match birth year %d (expected ~%d). Verify.", Q2_1_AGE, Q2_BIRTH_YEAR, computedAge);
    reenter;
  endif;

PROC Q18_INCOME_BRACKET
postproc
  { Amount must fall in bracket — brackets are value-set specific; template only }
  if not amount_in_bracket(Q18_INCOME_AMOUNT, Q18_INCOME_BRACKET) then
    errmsg("Income amount %d does not fall in bracket %s", Q18_INCOME_AMOUNT, getLabel(Q18_INCOME_BRACKET));
    reenter;
  endif;

PROC Q19_HH_SIZE_TOTAL
postproc
  { HH composition sanity }
  if Q19_HH_SIZE_TOTAL < 1 or Q19_HH_SIZE_TOTAL > 20 then
    errmsg("Household size must be 1–20 (got %d)", Q19_HH_SIZE_TOTAL);
    reenter;
  endif;
  if Q19_HH_SIZE_TOTAL > 10 then
    errmsg("Unusually large household (%d). Verify.", Q19_HH_SIZE_TOTAL, soft);
  endif;
```

### 4.5 Roster loop — gate + per-member skips (depends on sanity #1 fix)

```cspro
{ Assumes C_HOUSEHOLD_ROSTER is repeating. Until the schema patch lands, }
{ this template documents intended behavior. }

PROC C_HOUSEHOLD_ROSTER
preproc
  { Iteration index is 1..Q19_HH_SIZE_TOTAL }
  if curocc() = 1 then
    { First member — SOFT warn if relationship ≠ Self/Head }
    { (Rule enforced in Q34 postproc below) }
  endif;

PROC Q34_RELATIONSHIP
postproc
  if curocc() = 1 and Q34_RELATIONSHIP not in (1, 2) then  { 1=Self, 2=Head — adjust codes }
    errmsg("First roster entry is typically the respondent (Self) or HH head. Confirm.", soft);
  endif;

PROC Q35_HAS_DISABILITY
postproc
  if Q35_HAS_DISABILITY = 2 then      { No }
    skip to Q39_CIVIL_STATUS;
  endif;

PROC Q37_PWD_CARD
postproc
  if Q37_PWD_CARD = 2 then            { No card }
    skip to Q39_CIVIL_STATUS;
  endif;

PROC Q45_PHILHEALTH_REG
postproc
  if Q45_PHILHEALTH_REG = 2 then      { Not registered }
    skip to Q48_NAME_FIRST;           { or skip roster member entirely — adjust per Q45 value set }
  endif;

PROC Q49_PRIVATE_INS
postproc
  if Q49_PRIVATE_INS = 2 then         { No private insurance }
    endocc;                           { close this roster occurrence }
  endif;

PROC C_HOUSEHOLD_ROSTER
postproc
  { Roster-count sanity: fires when roster close attempt is made }
  if count(C_HOUSEHOLD_ROSTER) <> Q19_HH_SIZE_TOTAL then
    errmsg("Roster has %d members but Q19 says %d. Reconcile.",
           count(C_HOUSEHOLD_ROSTER), Q19_HH_SIZE_TOTAL);
    reenter;
  endif;

PROC Q47_HH_HAS_PRIVATE_INS
preproc
  { Auto-set if any roster member has private insurance }
  numeric anyPrivate = 0;
  do numeric i = 1 while i <= count(C_HOUSEHOLD_ROSTER)
    if C_HOUSEHOLD_ROSTER(i).Q49_PRIVATE_INS = 1 then
      anyPrivate = 1;
    endif;
    i = i + 1;
  enddo;
  if anyPrivate = 1 then
    Q47_HH_HAS_PRIVATE_INS = 1;
    errmsg("Auto-set to Yes because roster shows a member with private insurance. Confirm.", soft);
  endif;
```

### 4.6 Section D–F awareness blocks — generic pattern

```cspro
{ Pattern applies to Section D (Q51→Q52/Q53), E (Q54→Q55/Q56), F (Q57→Q58/Q59) }

PROC Q51_UHC_HEARD      { repeat for Q54_YAKAP_HEARD, Q57_BUCAS_HEARD }
postproc
  if Q51_UHC_HEARD in 2,3 then        { No / Don't know }
    skip to Q54_YAKAP_HEARD;          { jump to next section's gate }
  endif;

PROC Q60_BUCAS_ACCESSED
postproc
  if Q60_BUCAS_ACCESSED = 2 then      { Not accessed }
    skip to Q62_PURCHASE_FREQ;        { skip Q61 services }
  endif;
```

### 4.7 Section I primary-care routing

```cspro
PROC Q89_HAS_USUAL_FACILITY
postproc
  if Q89_HAS_USUAL_FACILITY = 2 then  { No usual facility }
    skip to Q93_WHY_NOT_O01;          { skip Q89.1, Q90, Q91, Q92 → go to why-not }
  endif;

PROC Q90_IS_USUAL_FOR_GENERAL
postproc
  if Q90_IS_USUAL_FOR_GENERAL = 1 then { Yes — usual is used for general care }
    skip to Q94_TRANSPORT_O01;          { skip Q91, Q92, Q93 }
  endif;

PROC Q97_KNOWS_BOOKING
postproc
  if Q97_KNOWS_BOOKING = 2 then       { No }
    skip to Q100_LEAVE_WORK_SCHOOL;
  endif;
```

### 4.8 Section M bill-recall chain (gated on Q129)

```cspro
PROC Q129_HH_CONFINED
postproc
  if Q129_HH_CONFINED = 2 then        { No confinement in HH }
    skip to Q144_CEREALS_CONSUMED;    { skip Section M entirely → go to Section N }
  endif;

PROC Q140_RECALL_BREAKDOWN
postproc
  if Q140_RECALL_BREAKDOWN = 2 then   { No breakdown }
    skip to Q142_RECALL_PAYMENT;      { skip Q141 bill items, Q141.1 }
  endif;

PROC Q141_1_NO_RECEIPT_AMT_PHP
postproc
  { Cap at Q139 final amount }
  if Q141_1_NO_RECEIPT_AMT_PHP > Q139_FINAL_AMOUNT_PHP then
    errmsg("No-receipt amount (%d) exceeds total bill (%d). Verify.",
           Q141_1_NO_RECEIPT_AMT_PHP, Q139_FINAL_AMOUNT_PHP);
    reenter;
  endif;

PROC Q142_RECALL_PAYMENT
postproc
  if Q142_RECALL_PAYMENT = 2 then     { No payment recall }
    skip to Q144_CEREALS_CONSUMED;    { end Section M → Section N }
  endif;
```

### 4.9 Section N expenditure-grid pattern + auto-subtotals

```cspro
{ Pattern for all 42 consumption items. Apply per item. }

PROC Q144_CEREALS_CONSUMED            { repeat for Q145..Q184 CONSUMED }
postproc
  if Q144_CEREALS_CONSUMED = 2 then   { Not consumed }
    Q144_CEREALS_PURCHASED_PHP = 0;
    Q144_CEREALS_INKIND_PHP    = 0;
    skip to Q145_PULSES_CONSUMED;
  endif;

PROC Q144_CEREALS_PURCHASED_PHP
postproc
  { Within-row sanity: at least one amount > 0 when consumed }
  if Q144_CEREALS_CONSUMED = 1
     and Q144_CEREALS_PURCHASED_PHP = 0
     and Q144_CEREALS_INKIND_PHP    = 0 then
    errmsg("Consumed but both amounts are 0. Enter purchased, in-kind, or set consumed=No.", soft);
  endif;

PROC Q157_FOOD_SUBTOTAL_TOTAL_PHP
preproc
  Q157_FOOD_SUBTOTAL_TOTAL_PHP =
      Q144_CEREALS_PURCHASED_PHP + Q144_CEREALS_INKIND_PHP
    + Q145_PULSES_PURCHASED_PHP  + Q145_PULSES_INKIND_PHP
    + Q146_VEGETABLES_PURCHASED_PHP + Q146_VEGETABLES_INKIND_PHP
    + Q147_FRUITS_PURCHASED_PHP  + Q147_FRUITS_INKIND_PHP
    + Q148_FISH_PURCHASED_PHP    + Q148_FISH_INKIND_PHP
    + Q149_MEAT_PURCHASED_PHP    + Q149_MEAT_INKIND_PHP
    + Q150_EGGS_PURCHASED_PHP    + Q150_EGGS_INKIND_PHP
    + Q151_MILK_PURCHASED_PHP    + Q151_MILK_INKIND_PHP
    + Q152_FATS_PURCHASED_PHP    + Q152_FATS_INKIND_PHP
    + Q153_SUGAR_PURCHASED_PHP   + Q153_SUGAR_INKIND_PHP
    + Q154_CONDIMENTS_PURCHASED_PHP + Q154_CONDIMENTS_INKIND_PHP
    + Q155_WATER_NA_PURCHASED_PHP + Q155_WATER_NA_INKIND_PHP
    + Q156_ALCOHOL_PURCHASED_PHP + Q156_ALCOHOL_INKIND_PHP;
  protect(Q157_FOOD_SUBTOTAL_TOTAL_PHP);

{ Analogous subtotal blocks for Q177, Q182, Q185 — same pattern, different item lists }
```

### 4.10 Catastrophic expenditure sanity

```cspro
PROC Q_FINANCIAL_ANXIETY
preproc
  { Catastrophic health expenditure plausibility check }
  numeric healthTotal;
  healthTotal = Q177_HEALTH_12M_SUBTOTAL_TOTAL_PHP
              + Q182_HEALTH_6M_SUBTOTAL_TOTAL_PHP
              + Q185_HEALTH_1M_SUBTOTAL_TOTAL_PHP;
  if Q18_INCOME_AMOUNT > 0 and healthTotal > 3 * Q18_INCOME_AMOUNT then
    errmsg("Total health expenditure (%d) is >3× reported monthly income (%d). Verify.",
           healthTotal, Q18_INCOME_AMOUNT, soft);
  endif;
```

### 4.11 Section Q terminator

```cspro
PROC Q202_WORRY_REASONS_O01           { or last item of Q202 }
postproc
  { End of questionnaire }
  ENUM_RESULT_FINAL_VISIT = 1;        { Completed }
```

---

## 5. Open questions — routing

Disposition following the F3 pattern: genuine ASPSI asks vs spec-decisions.

### Needs ASPSI

1. **Q15 IP_GROUP coded list** — Source promises "A list will be provided" but Annex F4 ships only free-text (identical to F3 Q31). **Route to Juvy** alongside the F3 question — single ask covers both instruments. Default if no response: keep alpha.
2. **Section C roster repeating-record confirmation** — Current schema has C_HOUSEHOLD_ROSTER as flat; source describes it as "repeating keyed by member line number." **Route to ASPSI/DOH-PMSMD** if they want a specific max-occurrences cap (default proposal: 20) and whether the respondent is row 1 of the roster or tracked separately in Section B.
3. **Section J per-member looping confirmation** — Source says "loops over household members for health-seeking items." **Route to ASPSI** to confirm whether Section J asks per member or only the respondent. Default: honor source (per-member loop), pending response.

### Spec-decision (ASPSI may override)

4. **Q129 gates Section M bill-recall chain only, not ZBB/MAIFIP awareness** — Source prints ZBB awareness Q132–Q134 without an explicit gate; bill-recall Q138–Q143 is confinement-dependent by design. **Spec default**: ZBB/MAIFIP awareness asked regardless; bill chain gated on Q129 = Yes.
5. **Q135 ZBB_OOP enumerator gate** — Source note limits Q135 to patients who visited a ZBB-eligible facility. No dcf flag captures "facility eligibility." **Spec default**: enumerator leaves Q135 blank if not applicable; PROC accepts blank.
6. **Q130 hospital-type gate on Q131** — Source: NBB applies to public hospitals only. **Spec default**: if Q130 = Private, skip Q131. PROC coded in §4 (Section L).
7. **Q141.1 NO_RECEIPT_AMT cap** — Capping at Q139 total bill is a consistency guardrail; source doesn't specify. **Spec default**: HARD cap at `Q141_1 ≤ Q139`.
8. **Catastrophic-expenditure SOFT warn threshold (3×)** — 3× monthly income is a common CHE plausibility threshold (SDG 3.8.2 uses 10% and 25% of capacity-to-pay). **Spec default**: SOFT warn at 3× for enumerator verification; not a CHE measurement — computed separately in analysis.

---

## 6. Implementation order (recommended)

1. **Fix schema gaps #1 and #2 in `generate_dcf.py`** — make `C_HOUSEHOLD_ROSTER` and (per source) `J_HEALTH_SEEKING` repeating records with `MEMBER_LINE_NO` as id. This is the only regenerator blocker; once patched, the dcf goes from 611 to something higher (adds `occurrenceLabel` metadata; items unchanged). Re-run the generator, diff the dcf, verify items are unchanged and only record structure changed.
2. **Route ASPSI questions** (§5 items 1–3) in the same message — one batch, one reply expected. Default behaviors documented so the build isn't blocked pending response.
3. **Open `HouseholdSurvey.dcf` in CSPro Designer**, validate the dictionary loads cleanly; inspect record layout (11 data records + header + field control + geo + consent gate + roster + per-section blocks).
4. **Build the Form file** (`.fmf`) — one form per section A–Q + Field Control + Geographic ID; roster form gets its own scrolling behavior (per `CSPro CAPI Strategies`: roster scrolls alone). Tab-order aligned with Q-number sequence.
5. **Add PROC code** in this order:
   1. Field Control + consent terminator (§4.2) + PSGC cascade (§4.3)
   2. Section A–B consistency (§4.4) — age-birth-year, income bracket, HH-size sanity
   3. Roster loop (§4.5) — including post-loop count check and Q47 auto-set
   4. Awareness-block generics (§4.6) applied to D, E, F
   5. Section G generics (skip patterns match F3 Section K)
   6. Section H PhilHealth gating (§4 Section H) — depends on roster Q45
   7. Section I primary-care routing (§4.7)
   8. Section J per-member skips (§4 Section J) — depends on roster fix
   9. Section K referral tree (§4 Section K) — mirrors F3 Section L
   10. Section L NBB (§4 Section L) including Q129 hospital-type gate
   11. Section M bill-recall chain (§4.8) — confinement-gated
   12. Section N expenditure grid (§4.9) + subtotals
   13. Section O sources-of-funds + Q196 select-all
   14. Section P financial risk + Q199 WTP sanity
   15. Section Q anxiety + terminator (§4.11)
6. **Bench-test** with paper walk-through of 4 mock households: HH with confined member + PhilHealth coverage, HH with no PhilHealth and no confinement, HH with many members (test roster ≥ 5), HH where respondent is not HH head.
7. **Pretest readiness** — bundle as PFF for CSEntry Android distribution alongside F1/F3 when all three are Build-ready.

---

*This spec is generated from the Apr 20 2026 Annex F4 PDF and the Apr 20 dcf (21 records / 611 items). Update both this file and `generate_dcf.py` whenever the questionnaire is revised. Mirrors the shape of `F1-Skip-Logic-and-Validations.md` and `F3-Skip-Logic-and-Validations.md`.*
