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

> [!warning] SUPERSEDED — the generator is the source of truth (banner added 2026-06-27, rewritten 2026-08-19 Task 2.6 for the Aug-17 instrument)
> This spec **trails the UAT-evolved generator.** For current behavior read the inline comments in `deliverables/CSPro/F1/generate_apc.py` / `generate_dcf.py` and the bound `.apc`. Do **not** "re-fix" code to match this doc — several departures are intentional UAT closures.
> **Numbering: this file was renumbered to the 2026-08-17 updated instrument (Q1–Q153) on 2026-08-19.** The frontmatter still names the Apr-20 PDF because that is the file the spec was originally written against; the Aug-17 set (`wiki/sources/Source - Updated Survey Instruments (2026-08-17).md`) is what the build now implements, and it is the authority for every Q-number below. F3 and F4's specs carry the same frontmatter/body split.
> Known drift: **F1-QC-02** — §3.2 references `Q2_DESIGNATION` + `_OTHER_TXT`; the actual field is `Q2_FACILITY_ROLE` (11 options, no Other). **Section C is now a two-step battery** (Yes/No base + a `Q<NN>_1_UHC_ATTRIB` probe, seven of them with a further `.2` detail item) — 23 pairs replacing the pre-Aug-17 nine-option "UHC9" items; every base carries a real skip, not a display group (§2). **Secondary-Data records have never existed in the dcf** — see §1 Bug #2 and ruling R22.

Source-of-truth for CSPro CAPI logic on `FacilityHeadSurvey.dcf`. Covers:

1. **Sanity-check findings** — discrepancies between the Apr 20 questionnaire and the current dcf (12 records / 664 items).
2. **Skip-logic table** — every conditional jump extracted from the questionnaire.
3. **Cross-field validations** — HARD (block save), SOFT (warn-and-confirm), GATE (display-only conditional rendering).
4. **CSPro logic templates** — paste-ready snippets for common patterns.

All Q-numbers refer to the **2026-08-17 updated questionnaire** (1–153); dcf item names follow the `Q{n}_*` convention. Sections: **A** Facility Head Profile Q1–Q6, **B** Facility Profile Q7–Q8, **C** UHC Implementation Q9–Q37, **D** YAKAP/Konsulta Q38–Q87, **E** BUCAS/GAMOT Q88–Q104, **F** DOH Licensing Q105–Q121, **G** Service Delivery Q122–Q149, **H** Human Resources for Health Q150–Q153.

> **Item-count provenance.** The Apr 08 baseline had ~126 printed items; the Apr 20 DOH-submitted revision (driven by the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G remarks]]) added ~40. The **2026-08-17 rewrite** then renumbered the whole instrument to Q1–Q153: Section C's 18 nine-option UHC9 items became a 23-pair two-step battery (base + `Q<NN>_1_UHC_ATTRIB` probe, seven with a `.2` detail item), and Sections D–H shifted by −13. The current dcf is **12 records / 320 items** (Task 2.2 rebuild) — the item count fell because the UHC9 per-option `_YES_OTHER_TXT` / `_NO_OTHER_TXT` fan-out retired with the two-step redesign. `REC_FACILITY_CAPTURE` (type Z, facility GPS + verification photo) is one of the 12. See `deliverables/CSPro/instruments-aug17-extract/maps/F1-renames.csv` for the old→new item map and `aug17-approved-divergences.md` for every registered paper-vs-build divergence.

---

## 1. Sanity-check findings (dcf vs Apr 20 questionnaire)

### A. Dispositions of the six original bugs

The original Apr 10 spec flagged six generator bugs. Five are now closed in code; two remain pending ASPSI input (tracked below). Numbering preserved for continuity with the Apr 13 LSS minutes and E2-F1-009b.

| # | Item | Status | Disposition |
|---|---|---|---|
| 1 | **Q153 PD_NURSES list** (Apr-20 Q166) | CLOSED by the Aug-17 paper | The printed Aug-17 nurse list omits "Clinical audits" / "Surgical audits", confirming the long-standing default; the `Q166_NURSES_INCLUDE_AUDITS` toggle was **retired** with that confirmation (`generate_dcf.py:1374`). The list ships from the `PD_NURSES` literal (`generate_dcf.py:1376`) as `Q153_PD_NURSES`, a Check Box with exclusivity on code 06. |
| 2 | **Secondary Data section** | OPEN — nothing built; **no stub records exist** | **Corrected 2026-08-19 (ruling R22).** This row previously claimed four empty-item records (`SEC_HOSP_CENSUS`, `SEC_HCW_ROSTER`, `SEC_YK_SERVICES`, `SEC_LAB_PRICES`) "exist in the dcf". They do not, and never did. `SECONDARY_DATA_AS_STUBS = True` and `build_secondary_data_stubs()` both exist in `generate_dcf.py` (lines 116 and 1400), but **the function is never called from the assembly** — it is dead code, and the built dictionary has 12 records, none of them `SEC_*`. The whole annex (hospital census, HCW roster by cadre × employment type, YAKAP services, procurement vs charged prices, lab markup) is an open design question for ASPSI — see §5 Dispositions. Note the ICF read aloud to every respondent still promises "secondary data such as hospital census and staffing statistics", which the instrument does not collect; that gap is on the ASPSI clarification list. |
| 3 | **Accreditation-wait label/units mismatch** (Apr-20 Q63) | CLOSED BY THE AUG-17 REWRITE | The Apr-20 item whose stem said "days" while its buckets were in months does not survive into the Aug-17 instrument, and the `Q63_USE_DAY_BUCKETS` toggle this row used to cite no longer exists in any generator. The nearest current items are the stock-out duration pair `Q101_STOCKOUT_DURATION` (day bands) and `Q102_STOCKOUT_AVG` (month bands), which are internally consistent and gated on each other (§2, Section E). |
| 4 | **EMR — `Not applicable` skip** (Apr-20 Q31, now `Q20_EMR_USE`) | CLOSED — superseded by the two-step battery | `Q20_EMR_USE` is a Yes/No base in the Aug-17 two-step battery: `= 2 (No)` skips its probe **and** the Q21–Q23 DOH-IS fan, landing on `Q24_STAFFING_CHANGED` exactly as the paper prints. The constant is `Q20_NA_SKIPS = True` (`generate_dcf.py:121`; earlier revisions of this spec cited a `Q31_NA_SKIPS` that never existed under that name). There is no longer a separate "Not applicable" branch to reconcile — only `Q12` and `Q13` retain an NA code (9), and both are handled by the battery's `in 2,9` condition. |
| 5 | **Informed-consent block** | CLOSED | No consent flag in `FIELD_CONTROL` — `CONSENT_GIVEN` was removed 2026-06-12. The ICF itself is a read-aloud script at the head of Section A (`ICF_PART1` / `ICF_PART2`), and since 2026-08-18 it carries the same 4-paragraph certificate + SJREB/ASPSI contact block as F3 and F4, byte-identical across the three instruments. `RESP_NAME` / `RESP_POSITION` / `RESP_EMAIL` / `RESP_MOBILE` live at the top of `A_FACILITY_HEAD_PROFILE`. A respondent who declines is recorded via `BREAKOFF` (see §4.14). |
| 6 | **Tenure ≥6 months pre-filter** | CLOSED-BY-DESIGN | Enforced in `PROC Q5_MONTHS_AT_FACILITY postproc` (§4.2), not as a separate screening item. Tenure below 6 months sets `ENUM_RESULT_FINAL_VISIT = 4` (Refused/Incomplete) and calls `endlevel`. |

### B. Cosmetic / acceptable as-is

- Dcf item names carry the printed 1–153 Aug-17 numbering. The old Apr-20 numbers survive only in `maps/F1-renames.csv`; resolve forward through item **names**, never backward through the map (Task 2.4 carry 8).
- Hospital-only / PCF-only gating inside `Q108_DOH_LIC_DIFFICULT` options **is** now encoded: `PROC Q108_DOH_LIC_DIFFICULT preproc` calls `setvalueset()` to swap between `Q108_DOH_LIC_DIFFICULT_PCF_VS1` and `_HOSP_VS1` on `Q8_SERVICE_LEVEL` (#385). The `Q121_DYNAMIC_VALUE_SET = False` fallback described in earlier revisions of this spec never existed as a constant and is not what ships.
- Respondent contact block (`RESP_NAME` / `RESP_POSITION` / `RESP_EMAIL` / `RESP_MOBILE`) lives inside Section A rather than `FIELD_CONTROL` — intentional; generator comment notes "moved out of FIELD_CONTROL so it lives with the facility-head profile it describes."

---

## 2. Skip-logic table

Format: **Trigger → Destination (skip range)**. Every row is the **build's** rule, read from
`FacilityHeadSurvey.ent.apc` (generated by `generate_apc.py`). The paper prints the same
routing in prose notation ("IF No GOTO <proceed to Q11>"); each notation divergence is
registered in `instruments-aug17-extract/aug17-approved-divergences.md` under `SKIP_DIFF`
and verified rule-by-rule in `reports/F1-tier2-matrix.md` (Task 2.6).

### Field Control (case start)

| Q | Condition | Skip to |
|---|---|---|
| BREAKOFF | = 1 Continue interview | (no skip — falls through to the geo/consent flow) |
| BREAKOFF | in 2, 3, 4 (interview started, then stopped) | ENUM_RESULT_FINAL_VISIT — sets Refused / Postponed / Incomplete and CASE_DISPOSITION = 2 |
| BREAKOFF | in 5, 6, 7 (interview never started — refused at the door, not found, ineligible) | ENUM_RESULT_FINAL_VISIT = 5 Replaced; the unit is substituted, and replacements are counted as BREAKOFF in 5,6,7 |

This is the **only** leapfrog in the case-start region: `BREAKOFF` (form 2) jumps to
`ENUM_RESULT_FINAL_VISIT` (form 11), the intended #744/#515 break-off escape. No other rule
targets forms 0–4, and there are no backward skips (Task 2.3 §11 sweep, live-confirmed in
Task 2.6's case-start reachability scenario).

### Section C — UHC Implementation (Q9–Q37): the two-step battery

The Aug-17 rewrite replaced 18 nine-option "UHC9" items with a **two-step** structure: a
Yes/No base, a `Q<NN>_1_UHC_ATTRIB` probe ("If yes, was it a result of the UHC Act enacted in
2019?"), and for seven bases a further `.2` detail question. 23 pairs in all.

**The gating is real skip logic, not display grouping.** CSEntry renders every field of a
DisplayTogether screen regardless of skip or `noinput` logic (UAT R4, GH #371/#372), so Task
2.3 put every probe on its **own screen** and Task 2.4 generated one skip rule per base
(`generate_apc.two_step_skip_rules()`). Each base's target is the **next base in printed
order** — which is what makes Q20 → Q24 fall out for free, since Q21–Q23 are the DOH-IS fan
rather than battery bases. Only Q12 and Q13 carry a "Not applicable" code (9); they are the
only two bases whose condition names a second value, and the table is checked against the
dictionary at generation time by `_assert_two_step_codes` rather than trusted.

Every row below skips that base's own probe (and its `.2` detail item, where one exists).

| Q | Condition | Skip to |
|---|---|---|
| Q10 HAS_PRIMARY_PKG | = No (2) | Q11 |
| Q11 PCB_LICENSING | = No (2) | Q12 |
| Q12 PUBLIC_HEALTH_UNIT | in 2, 9 (No or Not applicable) | Q13 |
| Q13 HEALTH_PROMO_UNIT | in 2, 9 (No or Not applicable) | Q14 |
| Q14 NEW_ROLES | = No (2) | Q15 |
| Q15 NEW_DEPTS | = No (2) | Q16 |
| Q16 NEW_BUILDINGS | = No (2) | Q17 |
| Q17 NEW_ROOMS | = No (2) | Q18 |
| Q18 INC_EQUIPMENT | = No (2) | Q19 |
| Q19 INC_SUPPLIES | = No (2) | Q20 |
| Q20 EMR_USE | = No (2) | Q24 (skip Q21, Q22, Q23 — the DOH-IS fan) |
| Q21 DATA_SUBMIT | = 4 (No, we are not submitting these data) | Q24 (skip Q22, Q23) |
| Q24 STAFFING_CHANGED | = No (2) | Q25 |
| Q25 REFERRAL_CHANGED | = No (2) | Q26 |
| Q26 MOU_MOA | = No (2) | Q27 |
| Q27 NBB | = No (2) | Q28 |
| Q28 ZBB | = No (2) | Q29 |
| Q29 NO_COPAY | = No (2) | Q30 |
| Q30 WARD_ALLOC | = No (2) | Q31 |
| Q31 CPG | = No (2) | Q32 |
| Q32 DOH_LIC_STD | = No (2) | Q33 |
| Q33 PHIC_ACCRED | = No (2) | Q34 |
| Q34 SVC_DELIVERY_PROT | = No (2) | Q35 |
| Q35 PCQM | = No (2) | Q36 |

### Section D — YAKAP / Konsulta (Q38–Q87)

`Q38_YK_ACCRED` is the section's master gate and splits it into two arms that reconverge at
Q79/Q80. **Accredited (Q38 = Yes)** walks Q39–Q65, then Q65 exits to Q72 and the costing block
Q72–Q78 runs, landing on Q80. **Not accredited (Q38 = No)** jumps straight to Q66, walks the
Q66–Q71 not-accredited block, and every tail of it lands on Q79 — which is itself
accredited-gated the other way, and after it is answered exits the whole section to Q88.

| Q | Condition | Skip to |
|---|---|---|
| Q38 YK_ACCRED | = No (2) | Q66 (skip Q39–Q65, the accredited YAKAP block) |
| Q46 KNOW_PAY_FREQ | = No (2) | Q48 (skip Q47) |
| Q48 TRANCHE_DELAY | = No (2) | Q49 — lands on the `_NUM` half of the hybrid pair, `Q49_TRANCHE_INTERVAL_NUM` |
| Q52 ACCRED_DIFFICULT | = "None of the above" (90) only | Q62 — reached by falling through the whole Q53–Q61 gate chain, not by a single jump (see below) |
| Q53 WHY_DIFF_PREVENTIVE | Q52 option 01 not ticked | Q54 |
| Q54 WHY_DIFF_LAB | Q52 option 02 not ticked | Q55 |
| Q55 WHY_DIFF_MEDS | Q52 option 03 not ticked | Q56 |
| Q56 WHY_DIFF_INFRA | Q52 option 04 not ticked | Q57 |
| Q57 WHY_DIFF_EQUIPMENT | Q52 option 05 not ticked | Q58 |
| Q58 WHY_DIFF_HR | Q52 option 06 not ticked | Q59 |
| Q59 WHY_DIFF_HIS | Q52 option 07 not ticked | Q60 |
| Q60 WHY_DIFF_DOCS | Q52 option 08 not ticked | Q61 |
| Q61 WHY_DIFF_DOH_LIC | Q52 option 09 not ticked | Q62 |
| Q64 ENROLL_CHALL | = No (2) | Q72 (skip Q65) |
| Q65 ENROLL_CHALL_LIST | Q38 = Yes (accredited) | Q72 (skip Q66–Q71, the not-accredited block) |
| Q66 NOT_ACCRED_REASON | Q38 ≠ No (belt-and-braces entry gate) | Q72 |
| Q67 INTEND_ACCRED | in 1, 2 (Yes, in process / Yes, not yet in process) | Q71 |
| Q67 INTEND_ACCRED | = 3 (No, decided not to) | Q69 |
| Q67 INTEND_ACCRED | = 4 (No, tried and failed) | Q70 |
| Q67 INTEND_ACCRED | = 5 (No, have not thought about it yet) | Q68 |
| Q67 INTEND_ACCRED | = 6 (I don't know) | Q79 — **defect-fix**: the paper sends this to Q72, which is the accredited-only block a Q67 respondent can never be in |
| Q68 KNOW_HOW_START | (unconditional — the Q67 = 5 tail) | Q79 |
| Q69 DECIDED_NOT_REASON | (unconditional — the Q67 = 3 tail) | Q79 |
| Q70 TRIED_FAILED_REASON | (unconditional — the Q67 = 4 tail) | Q79 |
| Q71 PROCESS_CHALL | (unconditional — the Q67 in 1,2 tail; the not-accredited block ends here) | Q79 |
| Q72 CATCHMENT_AREA | Q38 = No (entry gate on the accredited costing block) | Q79 |
| Q76 COSTING_DONE | = No (2) | Q78 (skip Q77) |
| Q77 COSTING_VIABLE | = No (2) | Q78 |
| Q77 COSTING_VIABLE | in 1, 3 (Yes / I don't know) | Q80 |
| Q79 MIN_CAP_VALUE_NONACC | Q38 ≠ No — entry gate; accredited facilities never see this item | Q80 |
| Q79 MIN_CAP_VALUE_NONACC | (unconditional, once answered) | Q88 — the not-accredited arm exits Section D here |
| Q80 CHARGE_ADDL_CAP | = No (2) | Q82 (skip Q81) |
| Q82 RECEIVED_PAYMENTS | in 1, 2 (all expected payments / some but not all) | Q84 (skip Q83) |
| Q84 PAYMENT_CHALL | = No (2) | Q86 (skip Q85) |

**Q52 / Q108 "None of the above" is a cascade, not a jump.** The paper prints "IF None of the
above GOTO Q62" (and Q122 for Q108). The build implements it as the *emergent* result of the
per-topic gate chain: with no difficulty ticked, `wdHit = 0` on every one of Q53–Q61, so each
self-skips to the next and the last one lands on Q62. Same routing, no separate rule.

### Section E — BUCAS / GAMOT and stock-outs (Q88–Q104)

| Q | Condition | Skip to |
|---|---|---|
| Q88 HEARD_BUCAS | = No (2) | Q95 (skip Q89–Q94, the whole BUCAS block) |
| Q89 HAS_BUCAS | = 1 (Yes) | Q91 (skip Q90) |
| Q89 HAS_BUCAS | = 3 (I don't know) | Q95 |
| Q90 NO_BUCAS_REASON | ≠ 5 (anything but "Other") | Q95 — on 5 it falls through to the specify box first, which then resumes the same skip |
| Q94 BUCAS_DECONGEST | Q89 ≠ Yes (entry gate: Q91–Q94 are for facilities that HAVE a BUCAS Center) | Q95 |
| Q95 HEARD_GAMOT | = No (2) | Q99 (skip Q96, Q97, Q98) |
| Q96 GAMOT_ACCRED | = Yes (1) | Q98 (skip Q97) |
| Q97 NO_GAMOT_REASON | ≠ 5 (anything but "Other") | Q99 — same specify-box fall-through as Q90 |
| Q99 STOCKOUT | = No (2) | Q105 (skip Q100–Q104, and with it the rest of Section E) |
| Q102 STOCKOUT_AVG | Q101 ≠ 3 — entry gate; below 60 days the month band is implied by Q101 itself | Q103 |
| Q103 ADDR_STOCKOUT | entry gate (#384): asked only when Q95 = Yes AND Q96 = Yes AND Q99 = Yes | Q105 |
| Q103 ADDR_STOCKOUT | in 2, 3 (No / Did not experience stock-outs under GAMOT) | Q105 (skip Q104) |

### Section F — DOH Licensing (Q105–Q121)

| Q | Condition | Skip to |
|---|---|---|
| Q105 DOH_LICENSED | in 2, 3, 4 (No / submitted and waiting / don't know what DOH licensing is) | Q122 (skip Q106–Q121, the whole of Section F) |
| Q108 DOH_LIC_DIFFICULT | = "None of the above" (90) only | Q122 — same cascade mechanism as Q52, via Q109–Q121 |
| Q109 WHY_DIFF_PT_RIGHTS | Q108 option 01 not ticked | Q110 |
| Q110 WHY_DIFF_PT_CARE | Q108 option 02 not ticked | Q111 |
| Q111 WHY_DIFF_LEADERSHIP | Q108 option 03 not ticked | Q112 |
| Q112 WHY_DIFF_HRM | Q108 option 04 not ticked | Q113 |
| Q113 WHY_DIFF_INFO_MGMT | Q108 option 05 not ticked | Q114 |
| Q114 WHY_DIFF_SAFE | Q108 option 06 not ticked | Q115 |
| Q115 WHY_DIFF_PERF | Q108 option 07 not ticked | Q116 |
| Q116 WHY_DIFF_PHYS_PLANT | Q108 option 08 not ticked | Q117 |
| Q117 WHY_DIFF_PRICE_INFO | Q108 option **13** not ticked (PCF-only topic — the printed tail is reordered vs the gate's codes) | Q118 |
| Q118 WHY_DIFF_EQUIPMENT | Q108 option **09** not ticked | Q119 |
| Q119 WHY_DIFF_NAT_LAWS | Q108 option **10** not ticked | Q120 |
| Q120 WHY_DIFF_EMERG_CART | Q108 option **11** not ticked (hospitals only) | Q121 |
| Q121 WHY_DIFF_ADDONS | Q108 option **12** not ticked (hospitals only) | Q122 |

The five bold codes are the F1-LOGIC-01 fix (2026-06-27, re-verified against the Aug-17 value
set in Task 2.4): the printed follow-up tail is reordered relative to the gate's option codes,
so a positional 1:1 mapping would invert the PCF-only / hospital-only gating. Q109–Q116 stay
positional (01–08). The membership test is an aligned 2-character chunk scan, not `pos()` — a
substring match across code boundaries had falsely opened the hospital-only batteries (#450).

### Section G — Service Delivery (Q122–Q149)

| Q | Condition | Skip to |
|---|---|---|
| Q122 NBB_CURR | = No (2) | Q125 (skip Q123, Q124) |
| Q125 ZBB_CURR | = No (2) | Q128 (skip Q126, Q127) |
| Q128 ALLOW_OOP_BASIC | = No (2) | Q130 (skip Q129) |
| Q132 MALASAKIT_PROVIDED | = No (2) | Q134 (skip Q133) |
| Q134 NO_MALASAKIT_WHY | Q132 = Yes — entry gate; the not-provided block does not apply | Q135 |
| Q135 LGU_SUPPORT | = No (2) | Q139 (skip Q136, Q137, Q138) |
| Q137 LGU_SATISFIED | = Yes (1) | Q139 (skip Q138) — **defect-fix**: the paper sends Yes to Q141, which orphans the Q139/Q140 PHO protocol pair for every satisfied respondent |
| Q139 PHO_PROTOCOL_CLARITY | entry gate: asked only when Q7 = Public AND Q8 in Level 1/2/3 Hospital (#386) | Q141 (skip Q140) |
| Q139 PHO_PROTOCOL_CLARITY | in 1, 2 (Very Clear / Clear) | Q141 (skip Q140) |
| Q148 REF_SATISFACTION | in 1, 2 (Very Satisfied / Satisfied) | Q150 (skip Q149) |

`Q148_REF_SATISFACTION` is built SELECT ONE despite the paper's "SELECT ALL THAT APPLY"
banner: it is a mutually-exclusive 5-point scale whose top two options carry skips, so a Check
Box base would make the skip untestable. Registered as a divergence.

### Section H — Human Resources for Health (Q150–Q153): no skips

---

## 3. Validations

Categories: **HARD** = block save / reenter, **SOFT** = warn-and-confirm, **GATE** = display-only conditional rendering.

### 3.1 Field Control & Geographic ID

| Item | Rule | Severity |
|---|---|---|
| `DATE_FIRST_VISITED_THE_FACILITY` | Valid date (YYYYMMDD); `20260101 ≤ d ≤ today + 1` | HARD |
| `DATE_OF_FINAL_VISIT_TO_THE_FACILITY` | Valid date; `≥ DATE_FIRST_VISITED_THE_FACILITY`; `≤ today + 1` | HARD |
| `TOTAL_NUMBER_OF_VISITS` | `≥ 1` when `ENUM_RESULT_FIRST_VISIT` or `ENUM_RESULT_FINAL_VISIT = Completed` | HARD |
| `BREAKOFF` | Required; defaults to `1 — Continue interview`. If ≠ Continue → terminate; sets `ENUM_RESULT_FINAL_VISIT` (2 Withdrew → 3 Refused; 3 Postponed → 2 Postponed; 4 Stop-other → 4 Incomplete; 5–7 never-started → 5 Replaced). Enumerator picklists on the Result-of-Visit fields show the paper's four codes only; `5 Replaced` is logic-assigned and swaps in via setvalueset() only on the replacement path (#1290/#1301 class extension, 2026-08-20). Sets `CASE_DISPOSITION = 2` | HARD |
| `CASE_DISPOSITION` | Auto-written by logic, never typed: 0 In progress / 1 Completed / 2 Partial / not completed | — |
| `CLASSIFICATION`, `REGION`, `PROVINCE_HUC`, `CITY_MUNICIPALITY`, `BARANGAY` | Required, non-blank; must exist in the loaded PSGC external lookup dictionaries (`shared/psgc_*.dcf`) | HARD |
| Child PSGC parent consistency | Enforced **at pick-time** by `PSGC-Cascade.apc` — `onfocus` on each child filters its value set to children of the chosen parent, so an inconsistent pair is unrepresentable | HARD — cascade enforces |
| `ENUM_RESULT_FIRST_VISIT = Completed` / `ENUM_RESULT_FINAL_VISIT = Completed` | All Section A–H mandatory items must be non-blank | HARD |

### 3.1.1 GPS capture block (`REC_FACILITY_CAPTURE`)

**Corrected 2026-08-19.** There is no `FACILITY_CAPTURE_GPS` trigger item — earlier revisions
of this spec described a button that was never built. Capture fires from
`PROC FACILITY_GPS_LATITUDE onfocus`, guarded on `FACILITY_GPS_READTIME` being empty so it
runs **once** and not on back-navigation. `ReadGPSReading()` (inlined from `Capture-Helpers.apc`
into `PROC GLOBAL`) reuses a radio that `WarmUpGPS()` opened at the case key, so a fresh fix
normally returns in 1–2 s; the 15 s budget only caps the no-signal case, and escalates to
30/45/60 s on consecutive failed retries (#1209). `ReleaseGPS()` closes the radio after this,
F1's only GPS block. On Windows desktop (`getos` 10–19) there is no radio and every field stays
blank by design — desk-test runs flow straight past.

GPS is the **last** form of the interview, after Section H. `REC_FACILITY_CAPTURE` is a type-Z
off-form record; its items are wired by `onfocus`, not placed on a data-entry form.

| Item | Rule | Severity |
|---|---|---|
| `FACILITY_GPS_LATITUDE` | Alpha; the capture trigger hangs off its `onfocus`. Protected read-only once `FACILITY_GPS_READTIME` is non-blank, so coordinates can never be typed | HARD — protect enforces |
| `FACILITY_GPS_LONGITUDE` | Alpha; written by the same capture, protected alongside it | HARD — protect enforces |
| `FACILITY_GPS_ALTITUDE` | Alpha, from `gps(altitude)`; no bounds enforced | — |
| `FACILITY_GPS_ACCURACY` | Numeric metres. `ReadGPSReading` warns (msg 1004) when the fix is worse than the 20 m target, but still returns success — the enumerator decides whether to retry | SOFT |
| `FACILITY_GPS_SATELLITES` | Numeric, from `gps(satellites)` | — |
| `FACILITY_GPS_READTIME` | Numeric timestamp; doubles as the capture-once sentinel and the protect trigger | — |
| Failed read | msg 1227 names the budget that elapsed; the radio flag is cleared but the radio is **not** closed, so a retry resumes the acquisition instead of cold-starting it | SOFT |

> **Do not re-add a "photo last" ordering assert.** GPS moved to the end of the interview
> deliberately; the older assertion that the photo is the final form was relaxed on purpose.

### 3.1.2 Verification photo (in `REC_FACILITY_CAPTURE`)

| Item | Rule | Severity |
|---|---|---|
| `CAPTURE_VERIFICATION_PHOTO` | Gated at preproc on `ENUM_RESULT_FINAL_VISIT` in {1 Completed, 4 Incomplete} — a Postponed or Refused visit is not photographed, and any stale filename is cleared. Trigger auto-resets to `notappl` after each attempt | GATE |
| `VERIFICATION_PHOTO_FILENAME` | `noinput` — display-only, filled by the camera trigger, never typed. Camera failure warns (msg 1007) rather than trapping the enumerator | SOFT |
| Filename pattern | `case-{RRPPMMMFFCCC}-verification.jpg`, built from `REGION_CODE`, `PROVINCE_HUC_CODE`, `CITY_MUNICIPALITY_CODE`, `FACILITY_NO`, `CASE_SEQ` | HARD — assigned by the PROC |
| `VERIFICATION_PHOTO_IMAGE` | The binary Image item. Photos sync to CSWeb **only** as binary Image dictionary items, off-form — the filename alone does not carry the picture | — |

### 3.2 Section A — Facility Head Profile (Q1–Q6)

| Item | Rule | Severity |
|---|---|---|
| `Q3_AGE` | `≥ 18`; msg 1056 blocks below the floor | HARD |
| `Q3_AGE` | `> 80` warns ("unusually old for an active facility head") without blocking | SOFT |
| **Tenure ≥ 6 months** | `Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY ≥ 6` (IR eligibility). Below it: msg 1075, `ENUM_RESULT_FINAL_VISIT = 4`, `endlevel` — the interview ends at Q5 | HARD — terminates the case |
| `Q5_YEARS_AT_FACILITY` | `≤ Q3_AGE − 20` — cannot have run a facility before age 20 (msg 1076) | HARD |
| `Q6_YEARS_HEALTH` | `≤ Q3_AGE − 20` (msg 1082) | HARD |
| **Tenure consistency** | `Q5_total ≤ Q6_total` — years at this facility cannot exceed total years in any health-related role (msg 1081) | HARD |
| `Q4_SEX` | Required, in {1, 2} | HARD |
| `Q2_FACILITY_ROLE` | Required; 11 options, no "Other" (drift F1-QC-02 — this spec's older revisions named a `Q2_DESIGNATION` + `_OTHER_TXT` pair that does not exist) | HARD |

### 3.3 Section B — Facility Profile (Q7–Q8)

| Item | Rule | Severity |
|---|---|---|
| `Q7_OWNERSHIP` | Required; with Q8 it drives the Q139/Q140 PHO gate | HARD |
| `Q8_SERVICE_LEVEL` | Required; drives the Q108 value-set swap and the Q117/Q120/Q121 facility-type topics | HARD |

### 3.4 Section C — UHC Implementation (Q9–Q37)

Every gate in this section is the two-step battery's own skip (§2), so the probe is
unreachable rather than merely disabled — the distinction that matters on CSEntry, where a
disabled field on a shared screen is still answerable.

| Item | Rule | Severity |
|---|---|---|
| `Q10_1_UHC_ATTRIB` and every other `Q<NN>_1_UHC_ATTRIB` probe | Reached only when its base is answered Yes; each probe sits on its own screen | GATE |
| Every `.2` detail item (Q12.2, Q13.2, Q14.2, Q15.2, Q16.2, Q17.2, Q18.2, Q19.2, Q35.2) | Reached only on its base's Yes path, immediately after the probe | GATE |
| `Q21_DATA_SUBMIT`, `Q22_DATA_FREQ`, `Q23_DATA_REPORTS_USED` | The DOH-IS fan; reached only when `Q20_EMR_USE = Yes` | GATE |
| `Q23_DATA_REPORTS_USED` | Check Box, at least one option required (msg 1251) | HARD |
| `Q35_2_PCQM_MEASURES` | Check Box, at least one option required (msg 1253) | HARD |
| `Q36_QUALITY_CHALL` | Check Box, at least one required (msg 1255); code 09 is exclusive and cannot be combined (msg 1256) | HARD |
| All `Q*_OTHER_TXT` | Required, non-blank, when the parent's "Other" code is ticked; cleared and `noinput` otherwise | HARD |

### 3.5 Section D — YAKAP / Konsulta (Q38–Q87)

| Item | Rule | Severity |
|---|---|---|
| Q39–Q65 entered | `Q38_YK_ACCRED = Yes` | GATE |
| Q66–Q71 entered | `Q38_YK_ACCRED = No` | GATE |
| Q72–Q78 entered | `Q38_YK_ACCRED = Yes` (the accredited costing block) | GATE |
| `Q79_MIN_CAP_VALUE_NONACC` entered | `Q38_YK_ACCRED = No` only | GATE |
| `Q39_YK_SINCE_YEAR` | `2019 ≤ year ≤ current_year` — the UHC Act passed in 2019 (msg 1066) | HARD |
| `Q39_YK_SINCE_MONTH` | `1 ≤ m ≤ 12` (msg 1064); and not in the future when the year is the current year (msg 1065) | HARD |
| `Q40_YK_PACKAGE` | Check Box, at least one required (msg 1261); code 09 "I don't know" exclusive (msg 1262); code 08 "All of the above" exclusive (msg 1263, #526) | HARD |
| `Q44_CAPITATION_AMT` | `≤ 5000` PHP blocks (msg 1071) | HARD |
| `Q44_CAPITATION_AMT` | `> 1700` PHP prompts "exceeds the PHP 1,700 PhilHealth max — confirm?" and re-enters on No | SOFT |
| `Q45_PERF_INDICATORS` | Check Box, at least one required (msg 1265); code 07 exclusive (msg 1266); code 05 "No requirements" also exclusive (msg 1267, #1188) | HARD |
| `Q47_PAY_FREQ` entered | `Q46_KNOW_PAY_FREQ = Yes` | GATE |
| `Q49_TRANCHE_INTERVAL_NUM` / `Q49_TRANCHE_INTERVAL` | Hybrid pair — a Q48 = No skip lands on the `_NUM` half, which is the pair's first field | GATE |
| `Q51_APPLY_REASON` | Required, non-blank (msg 1269) | HARD |
| `Q52_ACCRED_DIFFICULT` | Check Box, at least one required (msg 1271); code 90 "None of the above" exclusive (msg 1272) | HARD |
| **Q53–Q61 each** | Reached only when the matching `Q52_ACCRED_DIFFICULT` option is ticked — aligned 2-character chunk scan, not `pos()` (#450) | GATE |
| Q53–Q61 each, when reached | Check Box, at least one option required (msgs 1067, 1320, 1322, 1324, 1326, 1072, …) | HARD |
| `Q62_ENROLL_RESPONSIBILITY` | Check Box, at least one required (msg 1273); code 90 exclusive (msg 1274) | HARD |
| `Q63_ENROLL_INITIATIVES` | Check Box, at least one required (msg 1276); code 90 exclusive (msg 1277) | HARD |
| `Q65_ENROLL_CHALL_LIST` | Check Box, at least one required (msg 1079) | HARD |
| `Q66_NOT_ACCRED_REASON` | Check Box, at least one required (msg 1132) | HARD |
| **Q67 routing** | Exactly one of Q68 / Q69 / Q70 / Q71 is answered per case; every branch tail exits to Q79 | GATE |
| `Q73_ELIGIBLE_PATIENTS` | `> 500,000` warns without blocking (msg 1093) | SOFT |
| `Q74_REGISTERED_PATIENTS` | `≤ Q73_ELIGIBLE_PATIENTS` — registered cannot exceed eligible (msg 1094) | HARD |
| `Q78_MIN_CAP_VALUE_ACC` | `> 0` and `< 1700` prompts "below the PHP 1,700 PhilHealth max — confirm?" and re-enters on No (#533) | SOFT |
| `Q81_CHARGE_ADDL_CAP_REASONS` | Check Box, at least one required (msg 1280) | HARD |
| `Q83_NOT_RECEIVED_REASONS` | Check Box, at least one required (msg 1282); code 90 exclusive (msg 1283) | HARD |
| `Q85_PAYMENT_CHALL_LIST` | Check Box, at least one required (msg 1285); code 90 exclusive (msg 1286) | HARD |
| `Q86_EXPAND_NEXT` | Check Box, at least one required (msg 1288); code 90 exclusive (msg 1289) | HARD |
| `Q87_ADDL_FEATURES` | Free text gated on `Q86_EXPAND_NEXT` code 03 being ticked — cleared and `noinput` otherwise, required when it is (msg 1291). The one gated free-text item without an `_OTHER_TXT` suffix | HARD / GATE |

### 3.6 Section E — BUCAS / GAMOT (Q88–Q104)

| Item | Rule | Severity |
|---|---|---|
| Q89–Q94 entered | `Q88_HEARD_BUCAS = Yes` | GATE |
| `Q90_NO_BUCAS_REASON` entered | `Q89_HAS_BUCAS = No` | GATE |
| Q91–Q94 entered | `Q89_HAS_BUCAS = Yes` — the facility actually has a BUCAS Center | GATE |
| `Q91_BUCAS_SERVICES` | Check Box, at least one required (msg 1293) | HARD |
| `Q92_BUCAS_FACTORS` | Check Box, at least one required (msg 1295) | HARD |
| Q96–Q98 entered | `Q95_HEARD_GAMOT = Yes` | GATE |
| `Q97_NO_GAMOT_REASON` entered | `Q96_GAMOT_ACCRED = No` | GATE |
| `Q98_GAMOT_FACTORS` | Check Box, at least one required (msg 1100); entered when `Q96_GAMOT_ACCRED = Yes` | HARD / GATE |
| Q100–Q104 entered | `Q99_STOCKOUT = Yes` | GATE |
| `Q102_STOCKOUT_AVG` entered | `Q101_STOCKOUT_DURATION = 3` (more than 60 days) — below that the month band is already implied, so the item is skipped rather than asked redundantly | GATE |
| Q103, Q104 entered | `Q95 = Yes` AND `Q96 = Yes` AND `Q99 = Yes` (#384, spec 3.6 gate) | GATE |
| `Q104_ADDR_STOCKOUT_HOW` | Required, non-blank (msg 1010); entered only when `Q103_ADDR_STOCKOUT = Yes` | HARD / GATE |

> **Open clarification (ASPSI item 5).** `Q102_STOCKOUT_AVG` duplicates `Q101_STOCKOUT_DURATION`'s
> subject in month bands rather than day bands. The build's `Q101 ≠ 3` gate is the CAPI
> team's reading — that Q102 only adds information for stock-outs longer than 60 days — and is
> provisional pending ASPSI confirmation.

### 3.7 Section F — DOH Licensing (Q105–Q121)

| Item | Rule | Severity |
|---|---|---|
| Q106–Q121 entered | `Q105_DOH_LICENSED = Yes (1)` | GATE |
| `Q108_DOH_LIC_DIFFICULT` value set | Swapped at preproc on `Q8_SERVICE_LEVEL`: `Q108_DOH_LIC_DIFFICULT_PCF_VS1` for a Primary Care Facility, `_HOSP_VS1` for Level 1/2/3 hospitals (#385) | GATE |
| `Q108_DOH_LIC_DIFFICULT` | Check Box, at least one required (msg 1228); code 90 "None of the above" exclusive (msg 1229) | HARD |
| **Q109–Q121 each** | Reached only when the matching `Q108_DOH_LIC_DIFFICULT` option is ticked; Q109–Q116 map positionally to codes 01–08, Q117–Q121 map to 13, 09, 10, 11, 12 respectively (F1-LOGIC-01) | GATE |
| Q109–Q121 each, when reached | Check Box, at least one option required (msgs 1298, 1300, 1014, 1302, 1304, 1306, 1308, 1310, 1016, 1312, 1314, 1316, 1018) | HARD |
| `Q117_WHY_DIFF_PRICE_INFO` | PCF-only topic — reachable only through Q108's PCF value set | GATE |
| `Q120_WHY_DIFF_EMERG_CART`, `Q121_WHY_DIFF_ADDONS` | Hospital-only topics — reachable only through Q108's hospital value set | GATE |

### 3.8 Section G — Service Delivery (Q122–Q149)

| Item | Rule | Severity |
|---|---|---|
| Q123, Q124 entered | `Q122_NBB_CURR = Yes` | GATE |
| `Q124_NBB_BARRIERS` | Check Box, at least one required (msg 1110); code 90 exclusive (msg 1230) | HARD |
| Q126, Q127 entered | `Q125_ZBB_CURR = Yes` | GATE |
| `Q127_ZBB_BARRIERS` | Check Box, at least one required (msg 1116); code 90 exclusive (msg 1231) | HARD |
| `Q129_OOP_REASON` entered | `Q128_ALLOW_OOP_BASIC = Yes` | GATE |
| `Q131_DIFFICULT_REASON` | Required, non-blank (msg 1124) | HARD |
| `Q133_MALASAKIT_WHY` entered | `Q132_MALASAKIT_PROVIDED = Yes`; required when reached (msg 1128) | HARD / GATE |
| `Q134_NO_MALASAKIT_WHY` entered | `Q132_MALASAKIT_PROVIDED = No`; required when reached (msg 1130) | HARD / GATE |
| Q136–Q138 entered | `Q135_LGU_SUPPORT = Yes` | GATE |
| `Q136_LGU_SUPPORT_FORMS` | Check Box, at least one required (msg 1232) | HARD |
| `Q138_LGU_NOT_SAT_WHY` entered | `Q137_LGU_SATISFIED = No`; Check Box, at least one required (msg 1234); code 90 exclusive (msg 1235) | HARD / GATE |
| Q139, Q140 entered | `Q7_OWNERSHIP = Public` AND `Q8_SERVICE_LEVEL` in Level 1/2/3 Hospital (#386) | GATE |
| `Q140_UNCLEAR_PROTOCOL` entered | `Q139_PHO_PROTOCOL_CLARITY` in Unclear / Very Unclear | GATE |
| `Q142_SEND_REFERRAL_HOW` | Check Box, at least one required (msg 1237) | HARD |
| `Q143_REFERRAL_FORM_TYPE` | Check Box, at least one required (msg 1239); code 05 exclusive (msg 1240) | HARD |
| `Q146_RECEIVE_REFERRAL_HOW` | Check Box, at least one required (msg 1028) | HARD |
| `Q147_EXTERNAL_SERVICES_GO` | Check Box, at least one required (msg 1030); code 90 exclusive (msg 1242) | HARD |
| `Q149_NOT_SATISFIED_WHY` entered | `Q148_REF_SATISFACTION` not in Very Satisfied / Satisfied; required when reached (msg 1032) | HARD / GATE |

### 3.9 Section H — Human Resources for Health (Q150–Q153)

| Item | Rule | Severity |
|---|---|---|
| `Q150_HR_CHALL` | Check Box, at least one required (msg 1243). The Aug-17 printed list has 5 options and no "I don't know" — ASPSI's #1126 request for one did not survive their own rewrite (clarification item 1) | HARD |
| `Q152_PD_DOCTORS` | Check Box, at least one required (msg 1245); code 08 exclusive (msg 1246) | HARD |
| `Q153_PD_NURSES` | Check Box, at least one required (msg 1248); code 06 exclusive (msg 1249). Ships without "Clinical audits" / "Surgical audits" per §1 Bug #1 | HARD |

### 3.10 Cross-section consistency

| Rule | Severity |
|---|---|
| If `Q105_DOH_LICENSED = "I don't know what DOH licensing is"`, the `Q52_ACCRED_DIFFICULT` option "DOH licensing requirements" should not be ticked | SOFT (warn) |
| If `Q38_YK_ACCRED = Yes`, no answers should be present for Q66–Q71 or Q79 | HARD — enforced structurally by the Q65/Q66/Q79 entry gates |
| If `Q38_YK_ACCRED = No`, no answers should be present for Q39–Q65 or Q72–Q78 | HARD — enforced structurally by the Q38 and Q72 gates |
| If `Q89_HAS_BUCAS ≠ Yes`, no answers in Q91–Q94 | HARD — enforced by the Q94 entry gate |
| If `Q96_GAMOT_ACCRED = No`, no answers in Q98 | HARD |
| Secondary-data cross-checks (full-time staff who left ≤ total full-time staff) | NOT IMPLEMENTED — no secondary-data records exist; see §1 Bug #2 |

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

### 4.4 Section C — two-step battery gate (generated, one per base)

The 23 gates are **generated**, not hand-written: `generate_apc.two_step_skip_rules()` walks
`TWO_STEP_BATTERY` and emits one rule per base, targeting the next base in printed order.
Do not hand-add rows to `SKIP_RULES` for this section.

```cspro
{ Generated shape — Q10's gate. The target is Q11 because Q11 is the next base. }
PROC Q10_HAS_PRIMARY_PKG
postproc
  if Q10_HAS_PRIMARY_PKG = 2 then    { No -> skip this base's own probe }
    skip to Q11_PCB_LICENSING;
  endif;

{ Q12 and Q13 are the only two bases with a 'Not applicable' code. }
PROC Q12_PUBLIC_HEALTH_UNIT
postproc
  if Q12_PUBLIC_HEALTH_UNIT in 2,9 then   { No or Not applicable }
    skip to Q13_HEALTH_PROMO_UNIT;
  endif;

{ Q20's target is Q24, not Q21 — Q21-Q23 are the DOH-IS fan, not battery bases,
  so leaving them out of TWO_STEP_BATTERY gives the paper's Q20 -> Q24 for free. }
PROC Q20_EMR_USE
postproc
  if Q20_EMR_USE = 2 then
    skip to Q24_STAFFING_CHANGED;
  endif;
```

### 4.5 Section D — YAKAP master gate at Q38

```cspro
PROC Q38_YK_ACCRED
postproc
  if Q38_YK_ACCRED = 2 then  { Not accredited -> the Q66-Q71 arm }
    skip to Q66_NOT_ACCRED_REASON;
  endif;

{ The two arms reconverge through a pair of mirrored entry gates. }
PROC Q65_ENROLL_CHALL_LIST
postproc
  if Q38_YK_ACCRED = 1 then   { accredited: Q66-Q71 are the not-accredited block }
    skip to Q72_CATCHMENT_AREA;
  endif;

PROC Q72_CATCHMENT_AREA
preproc
  if Q38_YK_ACCRED = 2 then   { not-accredited: skip the accredited costing block }
    skip to Q79_MIN_CAP_VALUE_NONACC;
  endif;

PROC Q79_MIN_CAP_VALUE_NONACC
preproc
  if Q38_YK_ACCRED <> 2 then  { accredited: Q79 is not for them }
    skip to Q80_CHARGE_ADDL_CAP;
  endif;
postproc
  skip to Q88_HEARD_BUCAS;    { not-accredited finished -> exit Section D }
```

### 4.6 Q39 accreditation date validation

```cspro
PROC Q39_YK_SINCE_YEAR
postproc
  if Q39_YK_SINCE_YEAR < 2019 or Q39_YK_SINCE_YEAR > currentYear then
    errmsg(1066, currentYear);
    reenter;
  endif;

PROC Q39_YK_SINCE_MONTH
postproc
  if Q39_YK_SINCE_MONTH < 1 or Q39_YK_SINCE_MONTH > 12 then
    errmsg(1064);
    reenter;
  endif;
  if Q39_YK_SINCE_YEAR = currentYear and Q39_YK_SINCE_MONTH > currentMonth then
    errmsg(1065);
    reenter;
  endif;
```

### 4.7 Q73 / Q74 patient-count consistency

```cspro
PROC Q73_ELIGIBLE_PATIENTS
postproc
  if Q73_ELIGIBLE_PATIENTS > 500000 then
    errmsg(1093, Q73_ELIGIBLE_PATIENTS);   { soft — warns, does not reenter }
  endif;

PROC Q74_REGISTERED_PATIENTS
postproc
  if Q74_REGISTERED_PATIENTS > Q73_ELIGIBLE_PATIENTS then
    errmsg(1094, Q74_REGISTERED_PATIENTS, Q73_ELIGIBLE_PATIENTS);
    reenter;
  endif;
```

### 4.8 Q44 / Q78 capitation checks

```cspro
PROC Q44_CAPITATION_AMT
postproc
  if Q44_CAPITATION_AMT > 5000 then
    errmsg(1071, Q44_CAPITATION_AMT);
    reenter;
  endif;
  if Q44_CAPITATION_AMT > 1700 then
    if accept("Capitation %d exceeds the PHP 1,700 PhilHealth max. Confirm?", "Yes", "No") <> 1 then
      reenter;
    endif;
  endif;

{ #533: Q78 is the minimum the facility would ACCEPT, so the suspicious direction
  is BELOW the max, not above it. }
PROC Q78_MIN_CAP_VALUE_ACC
postproc
  if Q78_MIN_CAP_VALUE_ACC > 0 and Q78_MIN_CAP_VALUE_ACC < 1700 then
    if accept("Q78 minimum acceptable capitation is below the PHP 1,700 PhilHealth max - confirm?", "Yes", "No") <> 1 then
      reenter;
    endif;
  endif;
```

### 4.9 Section F — Q108 facility-type-aware value set

```cspro
PROC Q108_DOH_LIC_DIFFICULT
preproc
  { #385: swap the whole value set rather than hiding options after the fact. }
  if Q8_SERVICE_LEVEL = 1 then   { Primary Care Facility }
    setvalueset(Q108_DOH_LIC_DIFFICULT, Q108_DOH_LIC_DIFFICULT_PCF_VS1);
  else                           { Level 1/2/3 Hospital }
    setvalueset(Q108_DOH_LIC_DIFFICULT, Q108_DOH_LIC_DIFFICULT_HOSP_VS1);
  endif;
postproc
  if length(strip(Q108_DOH_LIC_DIFFICULT)) = 0 then
    errmsg(1228);
    reenter;
  endif;
  { 'None of the above' (90) must stand alone. }
  if pos("90", Q108_DOH_LIC_DIFFICULT) > 0 and length(strip(Q108_DOH_LIC_DIFFICULT)) > 2 then
    errmsg(1229);
    reenter;
  endif;
```

### 4.10 Generic "why-difficult" gate (Q53–Q61 on Q52, Q109–Q121 on Q108)

Both batteries' gate fields are single Check Box items, so membership is an **aligned
2-character chunk scan**, never `pos()`. `pos("10", ...)` substring-matches across code
boundaries once the list carries 2-digit codes — ticking 01 + 02 packs `"0102"`, which
contains `"10"` and falsely opened the hospitals-only batteries (#450). `do..while` +
`[p:2]` + `tonumber` are the strict-Publish-safe forms.

```cspro
PROC Q53_WHY_DIFF_PREVENTIVE
preproc
  numeric wdN; numeric wdK; numeric wdP; numeric wdHit;
  wdHit = 0;
  wdN = length(strip(Q52_ACCRED_DIFFICULT)) / 2;
  do wdK = 1 while wdK <= wdN
    wdP = (wdK - 1) * 2 + 1;
    if tonumber(Q52_ACCRED_DIFFICULT[wdP:2]) = 1 then wdHit = 1; endif;
  enddo;
  if wdHit = 0 then   { Q53 shown only if Q52 difficulty option 01 ticked }
    skip to Q54_WHY_DIFF_LAB;
  endif;
postproc
  if length(strip(Q53_WHY_DIFF_PREVENTIVE)) = 0 then
    errmsg(1067);
    reenter;
  endif;
```

The paper's "IF None of the above GOTO Q62" needs no rule of its own: with nothing ticked,
`wdHit = 0` on all nine and the chain falls through to Q62. Q108 -> Q109-Q121 -> Q122 is the
same shape, with the F1-LOGIC-01 code overrides for Q117-Q121.

### 4.11 Section G — Q137 LGU-satisfaction skip (defect-fix)

```cspro
{ The paper sends Q137 = Yes to Q141, which ORPHANS Q139/Q140 - the PHO
  protocol-clarity pair, which have nothing to do with LGU satisfaction. Under the
  printed routing the only reliable way to reach Q139 is the no-LGU-support path
  (Q135 No -> Q139), so every satisfied respondent silently loses two questions.
  Retargeting to Q139 still skips Q138 ('why not satisfied'), which is all the
  paper's skip was for. }
PROC Q137_LGU_SATISFIED
postproc
  if Q137_LGU_SATISFIED = 1 then  { Yes }
    skip to Q139_PHO_PROTOCOL_CLARITY;
  endif;
```

### 4.12 Section G — Q139 PHO gate and Q148 satisfaction skip

```cspro
PROC Q139_PHO_PROTOCOL_CLARITY
preproc
  if not (Q7_OWNERSHIP = 1 and Q8_SERVICE_LEVEL in 2,3,4) then
    skip to Q141_NUM_REFERRED_OUT;   { Q139/Q140 only for public hospitals (#386) }
  endif;
postproc
  if Q139_PHO_PROTOCOL_CLARITY in 1,2 then   { Very Clear / Clear -> skip the why-unclear detail }
    skip to Q141_NUM_REFERRED_OUT;
  endif;

PROC Q148_REF_SATISFACTION
postproc
  if Q148_REF_SATISFACTION in 1,2 then  { Very Satisfied / Satisfied }
    skip to Q150_HR_CHALL;     { Section H starts here }
  endif;
```

### 4.13 "Other (specify)" enforcement (apply to every `Q*_OTHER_TXT`)

Two shapes, depending on whether the parent is a Check Box or a single-coded item. Both
**clear and `noinput`** the box when the parent's Other code is absent, so a stale value can
never survive a back-navigation. Naming is always `Q<NN>_<STEM>_OTHER_TXT`.

```cspro
{ Check Box parent - membership test on the packed code string. }
PROC Q40_YK_PACKAGE_OTHER_TXT
preproc
  if pos("99", Q40_YK_PACKAGE) = 0 then
    Q40_YK_PACKAGE_OTHER_TXT = "";   { gated: 'Other (specify)' not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("99", Q40_YK_PACKAGE) > 0 and length(strip(Q40_YK_PACKAGE_OTHER_TXT)) = 0 then
    errmsg(1264);
    reenter;
  endif;

{ Single-coded parent - equality test, and the parent's own skip resumes afterwards. }
PROC Q90_OTHER_TXT
postproc
  if length(strip(Q90_OTHER_TXT)) = 0 then
    errmsg(1292);
    reenter;
  endif;
  skip to Q95_HEARD_GAMOT;             { specify captured -> resume the Q90 skip }
```

### 4.14 Field Control — break-off terminator and replacements

The `CONSENT_GIVEN` item was removed 2026-06-12. Early termination — including consent
refusal — runs through `BREAKOFF` at case start, which sets Result of Visit and the auto
`CASE_DISPOSITION`. Codes 5–7 are the **replacement** reasons (interview never started); the
guard must list all seven or a revisit to the field silently erases them.

```cspro
PROC BREAKOFF
preproc
  { The guard MUST list every valid code - anything outside it is silently reset to
    Continue. Widened to 1..7 on 2026-07-14; leaving it at 1..4 would have erased every
    replacement the moment the field was revisited. }
  if not (BREAKOFF in 1, 2, 3, 4, 5, 6, 7) then BREAKOFF = 1; endif;
postproc
  if BREAKOFF <> 1 then
    { 2-4: the interview STARTED and then stopped. }
    if BREAKOFF = 2 then ENUM_RESULT_FINAL_VISIT = 3; endif;   { withdrew  -> Refused }
    if BREAKOFF = 3 then ENUM_RESULT_FINAL_VISIT = 2; endif;   { Postponed }
    if BREAKOFF = 4 then ENUM_RESULT_FINAL_VISIT = 4; endif;   { Stop-other -> Incomplete }
    { 5-7: the interview NEVER STARTED. Every such unit is replaced by a substitute,
      so all three land on Replaced(5) and BREAKOFF keeps the reason.
      Postponed(3) is NOT a replacement: that unit is revisited, not substituted. }
    if BREAKOFF in 5, 6, 7 then ENUM_RESULT_FINAL_VISIT = 5; endif;   { Replaced }
    CASE_DISPOSITION = 2;   { partial / not completed }
    skip to ENUM_RESULT_FINAL_VISIT;
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

`Capture-Helpers.apc` and `PSGC-Cascade.apc` are **inlined into `PROC GLOBAL`** rather than
`#include`d: CSPro forbids `#include` inside a PROC, and CSEntry forbids code before the first
PROC. `generate_apc.py` does the inlining.

```cspro
{ Capture fires from the latitude field's onfocus - there is no separate trigger
  item. Guarded on READTIME so it captures once and not on back-navigation. }
PROC FACILITY_GPS_LATITUDE
onfocus
  if length(strip(FACILITY_GPS_READTIME)) = 0 then
    { 15 s budget: the radio has been warm since the case key (WarmUpGPS), so a
      fresh fix normally arrives in ~1-2 s; 15 s only caps the no-signal case. }
    if ReadGPSReading(15, 20) then
      FACILITY_GPS_LATITUDE   = maketext("%f", gps(latitude));
      FACILITY_GPS_LONGITUDE  = maketext("%f", gps(longitude));
      FACILITY_GPS_ALTITUDE   = maketext("%f", gps(altitude));
      FACILITY_GPS_ACCURACY   = gps(accuracy);
      FACILITY_GPS_SATELLITES = gps(satellites);
      FACILITY_GPS_READTIME   = maketext("%d", gps(readtime));
    endif;
  endif;
  { Protect ONLY once captured - protecting a blank numeric (no fix / desktop)
    triggers "protected field is out of range - value is NOTAPPL". }
  if length(strip(FACILITY_GPS_READTIME)) > 0 then
    protect(FACILITY_GPS_LATITUDE, true);
    protect(FACILITY_GPS_LONGITUDE, true);
    protect(FACILITY_GPS_ALTITUDE, true);
    protect(FACILITY_GPS_ACCURACY, true);
    protect(FACILITY_GPS_SATELLITES, true);
    protect(FACILITY_GPS_READTIME, true);
    ReleaseGPS();   { F1's only GPS block - close the radio once captured }
  endif;

{ #231 verification photo, at the END of the form. Conditional on the visit
  outcome and soft-validated (warn, don't trap, on camera failure). }
PROC CAPTURE_VERIFICATION_PHOTO
preproc
  if not (ENUM_RESULT_FINAL_VISIT in 1, 4) then
    VERIFICATION_PHOTO_FILENAME = "";   { clear any stale name if outcome changed back }
    noinput;
  endif;
onfocus
  if length(strip(VERIFICATION_PHOTO_FILENAME)) = 0 then
    string fn = "case-" + maketext("%02d%02d%03d%02d%03d", REGION_CODE, PROVINCE_HUC_CODE,
                                   CITY_MUNICIPALITY_CODE, FACILITY_NO, CASE_SEQ) + "-verification.jpg";
    if TakeVerificationPhoto(fn) then
      VERIFICATION_PHOTO_FILENAME = fn;
    else
      errmsg(1007);
    endif;
  endif;
  CAPTURE_VERIFICATION_PHOTO = notappl;
```

---

### 4.17 Case-control preproc — REMOVED

The case-control block (`SURVEY_CODE`, `DATE_STARTED`, `TIME_STARTED`, `INTERVIEWER_ID`, `AAPOR_DISPOSITION`, `AAPOR_DISPOSITION_FINAL`, `CONSENT_GIVEN`) and its preproc were **removed on 2026-06-12** — they were not on the April-20 paper Field Control form. Case outcome is carried by the real `FIELD_CONTROL` items instead: `ENUM_RESULT_FIRST_VISIT` / `ENUM_RESULT_FINAL_VISIT` (Result of Visit), `BREAKOFF`, and the auto-written `CASE_DISPOSITION` (0 In progress / 1 Completed / 2 Partial / not completed). There is no consent field — consent refusal is recorded as Result of Visit `3 — Refused`.

---

## 5. Dispositions

Carried forward from the Apr 13 LSS meeting and post-LSS E2-F1-009b, re-read against the
Aug-17 build on 2026-08-19. Generator constants are listed so the reverse lookup still works,
even where the constant is now inert.

### Needs ASPSI

1. **Secondary-data annex** (original Bug #2) — pages 30–34 of the printed instrument
   (hospital census 6mo, HCW roster by cadre × employment type, YAKAP services, procurement
   vs charged prices, lab markup) have **never been built**, in any form. `SECONDARY_DATA_AS_STUBS`
   is inert; there are no `SEC_*` records in the dictionary and never were (ruling R22,
   2026-08-19). A structural decision is needed before any module can be written: record-per-month
   vs flat, separate CSPro app vs embedded records, paper-only vs CAPI. **Route to Juvy.**
   Note that the ICF read aloud to every respondent already promises "secondary data such as
   hospital census and staffing statistics" — so today the consent script over-promises what
   the instrument collects, which is the sharper form of this ask.
2. **`Q150_HR_CHALL` lost "I don't know"** — ASPSI's #1126 (2026-08-06) explicitly asked for
   that option; the Aug-17 printed list, eleven days later, does not carry it. The paper is
   newer so it wins and the build follows the printed 5-option list. ASPSI should confirm the
   omission is intended rather than an oversight in their own rewrite.
3. **`Q102_STOCKOUT_AVG`'s gate** — see §3.6. The `Q101 ≠ 3` condition is the CAPI team's
   reading of two near-duplicate questions and is provisional.

### Spec-decision (ASPSI may override)

4. **Eligibility termination behaviour** — under 6 months tenure ends the case at Q5 postproc
   and codes `ENUM_RESULT_FINAL_VISIT = 4`. **Spec default**: terminate immediately (do not
   capture Sections B–H); the enumerator re-screens at a different facility. PROC in §4.2.
5. **`Q153_PD_NURSES` audits omission** (original Bug #1) — **closed**, not a spec default any
   more: the Aug-17 printed list confirms the omission, and the `Q166_NURSES_INCLUDE_AUDITS`
   toggle was retired with it.
6. **Q67 = "I don't know" retarget** — the paper sends it to Q72, the accredited-only costing
   block, which a Q67 respondent can never legitimately be in. The build sends it to Q79.
   Registered as a defect-fix, not a divergence to reconcile back.
7. **Q137 = Yes retarget** — see §4.11. The build sends it to Q139 rather than the paper's
   Q141, so the PHO protocol pair stays reachable on every path.
8. **Q68–Q71 exits** — under the printed routing these four Q67 branch tails had **no exit at
   all**, so a "haven't thought about it" respondent was walked through two other branches'
   questions. Each now ends with an unconditional skip to Q79.

---

## 6. Implementation order (recommended)

The build is fully generated; this order describes what to re-run, not what to hand-build.

1. **Regenerate** in dependency order — `generate_dcf.py` → `inject_scoped_option_labels.py`
   → `generate_apc.py` → `generate_fmf.py` → copy → `optimize_capture_types.py`. One command
   covers it: `py automation/cspro_compile_driver.py F1 --build`. Running `generate_apc.py`
   without the following `generate_fmf.py` leaves the form file's block plan stale, and any
   new or renamed item lands UNREACHABLE.
2. **Compile** — `py automation/cspro_compile_driver.py F1 --build --save`, then
   `py automation/csentry_verify.py F1` (a Designer "Compile Successful" alone does not prove
   CSEntry will load it).
3. **Static gates**, all four, before any device work: `preflight_validate.py`,
   `verify_questions.py F1` (reachability, dead conditions, bad skips), `skip_boundary_check.py F1`,
   `fmf_block_check.py`.
4. **Tier-1 conformance** — `py aug17-tools/aug17_diff.py F1` must exit 0 with zero
   unregistered divergences. Every intentional paper-vs-build departure needs a row in
   `aug17-approved-divergences.md`, and every skip rule needs a verified row in
   `reports/F1-tier2-matrix.md`.
5. **Desk-test** the branch-heavy paths with `automation/csentry_runner.py`: the two-step
   battery on both its Yes and No branches, the Q38 accredited / not-accredited split and its
   Q65 and Q68–Q71 exits, the GAMOT and stock-out chain, and the Q139 PHO gate.
6. **Package and deploy** — `stamp_version.py`, then `auto_deploy.py F1 --deploy`. Confirm the
   **8 PSGC files** ride with the package (`auto_deploy.add_files`), and that
   `facility_lookup.dat` / `.dcf` do **NOT**. `facility_lookup` was deliberately unbundled on
   2026-06-10: its text-repo indexing infinite-loops Android CSEntry at app start — *that* is
   the "always loading" trap, so re-adding the file re-creates the blocker rather than fixing
   it. `cspro_compile_driver._ent_json` drops it from the `.ent` externals for the same reason
   (see the comment at line 110), and the auto-fill it once served is gone with the
   single-Questionnaire-Number redesign. The two files still sit in `F1/` only because
   `data/facilities/build_facility_lookup.py` writes them there; they are not shipped.

---

*This spec describes the 2026-08-17 updated Annex F1 instrument as implemented by the current
generators. It was renumbered from the Apr-20 questionnaire on 2026-08-19 (Task 2.6 of the
Aug-17 CAPI migration). The generators remain the source of truth; update this file and
`generate_apc.py` / `generate_dcf.py` together whenever the questionnaire is revised.*
