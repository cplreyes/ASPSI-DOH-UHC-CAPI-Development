# CAPI Desk-Test Scenario Matrix (Stage 1, criterion #5)

Runnable test plan for the CSEntry desk-test of **F1 / F3 / F4**. Scenarios are derived from the
actual generated logic (`generate_apc.py` per instrument + shared `PSGC-Cascade.apc`). Each row is
a discrete check with concrete inputs and an expected outcome; fill **Result** (✅/❌) + capture a
screenshot to the gate issue.

**Gate issues:** F1 → #193 · F3 → #194 · F4 → #195 (+ FIELD_CONTROL sign-off F3 #251 / F4 #253).

## How to run
- Launch each app's desk-test pff: `CSEntry.exe <Instrument>/<App>_desktest.pff` (EN), or the
  `*_WAR.pff` to test in Waray. Keyboard-drive fields; advance with Enter.
- **Reading state:** the field turns **green** when accepted; the **status bar** shows the current
  field; **validation messages** appear as an HTML modal (dismiss with a click on OK).
- **Multi-language:** set `[Parameters] Language=<code>` in the pff, or switch in CSEntry's menu.

## Caveats (what desktop CSEntry on Windows CAN'T verify)
- 🔌 **GPS capture** (`gps()`) and 📷 **verification photo** (`takePhoto`) require device hardware —
  marked **DEVICE-ONLY**; defer to the Android runbook (`CSWeb-Deploy-and-Android-Verification-Runbook.md` §D).
- Touch-specific roster UX is best confirmed on a tablet, but roster *logic* runs on desktop.

**Legend:** `R` = hard reenter (blocks) · `S` = soft warning (accept & continue) · `T` = terminate
case · `SKIP→` = jump to target · `NOINPUT` = field hidden/protected · 🔌/📷 = device-only.

---

## Execution log

### Pass 1 — 2026-06-08 (agent, desktop CSEntry, F3)
- **F3-DT-02 (consent terminator) → ❌ FINDING — survey-flow design decision needed.**
  Consent=No does **not** cleanly terminate. The generator uses `endgroup`, which only skips the rest
  of the metadata group and **continues into the full survey** (geo form onward) — wrong for a refusal.
  Switching to `endlevel` (matching F1) makes CSEntry try to end the case, but it then errors
  **"Warning (1026): All of the ID fields were not filled, please reenter"** — because F3's case-key ID
  block (the geo codes) is collected on the **next** form, **after** consent, so there is no valid key
  to save a refused case. **Neither construct is correct.** The real fix is a survey-flow decision:
  collect the geo/facility case-key **before** consent, or skip-to-key-then-end on refusal. **Likely
  affects all three** (F1 uses `endlevel` with consent before its geo block — untested; F4 uses
  `endgroup` like F3). The speculative `endlevel` change was **reverted**; committed `endgroup` stands
  pending the decision. → **GO/NO-GO for Carl/ASPSI.**
- **F3-DT-14 (multi-language) → ✅.** Question text renders Waray ("Klase hin Pasyente" for
  `PATIENT_TYPE`) under `Language=WAR` (confirmed during the multi-language wiring work).
- **Remaining F3 scenarios:** not executed this pass. Desktop GUI-driving proved fragile — value-set
  pickers plus the "out of range" warnings on the no-value-set metadata fields (INTERVIEWER_ID,
  TIME_STARTED) make precise field-by-field navigation error-prone, and the deeper scenarios (OP/IP
  branch, section skips, later-section validations) need sustained interactive entry. Recommend a
  focused interactive pass (Carl) or a hardened automation harness; device-only DT-12/13 defer to the
  Android runbook.

### Resolution — 2026-06-08 (Option A: case-key before consent)
**F3-DT-02 FIXED + verified end-to-end.** Root cause was deeper than the terminator: the case-key ID
items (`REGION_CODE`/`PROVINCE_HUC_CODE`/`CITY_MUNICIPALITY_CODE`/`FACILITY_NO`/`CASE_SEQ`) were on **no
form** and set by **nothing** → *no* F3 case could save with a valid key (consent-refusal just surfaced
it first). Fix: `generate_fmf` now places the id items on **FORM000** (entered first, before consent —
like the CAPI Census "Geocodes" form; the old "id items get stripped" note was a misdiagnosis), and the
consent proc uses **`endlevel`** (not `endgroup`). Verified in CSEntry: key form renders first; consent=No
→ "Interview ends" errmsg → `endlevel` → **"Accept this case?" → case SAVES** (no "ID fields not filled");
case appears in the tree. **Replicated to F4** (key form first, loads clean). Also unblocks F3-DT-01 (happy
path can now save).

### Resolution (cont.) — 2026-06-08 (F1 case-key via post-processor)
**F1 fixed.** F1 has no `generate_fmf.py` (static `FacilityHeadSurvey.fmf`), so instead of a generator the
fix is a **post-processor**: `F1/inject_case_key.py` reads the dict's level ID items and regenerates the
empty **FORM000** `[Form]` block + **IDS0_FORM** `[Group]` block, injecting the 5 case-key fields
(`REGION_CODE`/`PROVINCE_HUC_CODE`/`CITY_MUNICIPALITY_CODE`/`FACILITY_NO`/`CASE_SEQ`) — matching F3's
verified layout (FIELD/TEXT positions identical). Idempotent (re-run rebuilds, never double-injects);
IRON-RULE compliant (programmatic generation, not a hand-edit). **Verified in CSPro Designer:** FMF binds
with no reconcile dialog, `IDS0_FORM` is the **first** group in the level with all 5 fields bound, and
logic **"Compile Successful"**. F1 already uses `endlevel` for consent, so the key form was the only gap →
the F1 equivalent of DT-02 (consent=No saves) is now structurally unblocked (interactive CSEntry
confirmation pending F1 matrix execution). Preflight: **all 3 instruments clean.**

### F1 matrix execution — 2026-06-08 (agent, desktop CSEntry)
**Logic desk-check (DT-03…DT-24): all PASS** against the generated `FacilityHeadSurvey.ent.apc` — every
validation / skip / routing / NOINPUT rule is present and matches the expected outcome (line refs traced;
compiler already validated syntax). DT-25/DT-26 (GPS / photo) = device-only, deferred to the Android runbook.

**Runtime DT-02 (consent=No) — partial PASS + CRITICAL FINDING.** In CSEntry the key form renders first;
filling it then setting `CONSENT_GIVEN=2` fires the exact logic: errmsg "Respondent declined consent…",
`ENUM_RESULT_FINAL_VISIT=4` (Refused), `endlevel` → "Accept this case?" → **case SAVES** and `consent_given=2`
/ `enum_result_final_visit=4` persist correctly in `field_control`. ✅ for the consent/terminator logic.

> [!warning] BLOCKER — cases save with a BLANK case key
> The 5 id-key items (`REGION_CODE`/`PROVINCE_HUC_CODE`/`CITY_MUNICIPALITY_CODE`/`FACILITY_NO`/`CASE_SEQ`)
> entered on FORM000 **do NOT persist**: saved `cases.key` = 12 spaces, `level-1` ids all `None`, the case-tree
> node has no key label, and reopening in **MODIFY** shows all 5 id fields blank. Confirmed 4 independent ways.
> **Ruled out:** the `endlevel` path (a mid-case **partial save**, before consent, also saved a blank key),
> the soft "out of range" warnings (clean entry → still blank), **auto-advance vs explicit Enter** (both blank),
> and the FMF structure (byte-identical to the CAPI Census `GEOCODES_FORM`).
> **This is NOT F1-specific — F3's "verified" desk-test case (`F3/desktest.csdb`) ALSO has a blank key.** The
> earlier F3 sign-off only checked that the case *saved/appeared in the tree*, never that the **key persisted**.
> So F1 **and** F3 (and by construction F4) all save keyless cases — every refused/saved case would collide on
> the empty key. **Stage-1 blocker** (criterion: cases must carry a valid key for CSWeb sync/dedup).
>
> **Deeper root-cause investigation (2026-06-08), all NEGATIVE — the key never persists by any path tried:**
> 1. **Logic-assigned key** — set `REGION_CODE=7 … CASE_SEQ=3` in `PROC FACILITYHEADSURVEY_LEVEL preproc`
>    (compiles; the values visibly **pre-fill** the form). Completed case → **still blank key**.
>    (Aside: assigning ids in the form-file `PROC FACILITYHEADSURVEY_FF preproc` fails to compile —
>    `ERROR 172: Variable belongs to a record at a lower level`; the *level* proc is the right scope and compiles.)
> 2. **`Protected=Yes` on the id fields + logic-assigned** (the exact Census pattern — CSEntry then *skips* the
>    key form, key set by logic) → completed case → **still blank key**.
> 3. **dcf structure is byte-equivalent to the shipping CAPI Census `Household.dcf`**: same `relativePositions:true`,
>    same `recordType {start:1,length:1}`, same `ids.items` layout (`start` 2/4/6/9/11, zeroFill), same
>    `recordTypeValue:null`. So it is **not** a dcf-field defect.
> **Only structural deltas vs the known-good census dict:** (a) my **record[0] `FACILITYHEADSURVEY_REC` is EMPTY**
> (0 items — the empty FORM001 "record"; census has no empty records); (b) record-type codes are numeric (`"1"…`)
> vs census letters (`"P"…`). Neither obviously explains a blank *key*, but they are the remaining leads.
> Census sources its geocodes from a **parent menu/assignment app via the PFF**, never an in-app key entry — so
> the likely-correct pattern is **supply the key via the PFF / a parent op**, and/or remove the empty record.

> [!success] RESOLVED — 2026-06-08: it WAS the empty vestigial record
> Dropping the empty item-less level-1 "container" record (`*_REC`, recordType `"1"`, 0 items, `required`)
> **fixes case-key persistence on all three instruments.** The empty required record was the root cause — CSEntry
> never populated it and it blocked the level id key from being written.
> **Verified in CSEntry (key now persists, was 12 blanks):**
> - **F3** → `cases.key = '010200304005'`, `level-1` ids `(1,2,3,4,5)`
> - **F4** → `cases.key = '010300702009'`, `level-1` ids `(1,3,7,2,9)`
> - **F1** → `cases.key = '070800906005'`, `level-1` ids `(7,8,9,6,5)`
>
> **The fix (per instrument):**
> - **F3 / F4** (clean generators): removed the `record("*_REC", …, "1", [])` line in `generate_dcf.py` and the
>   matching empty FORM001 "container" block in `generate_fmf.py` (planned forms renumbered to start at 1).
> - **F1** (static `.fmf`, no generator): `generate_dcf.py` filters out `FACILITYHEADSURVEY_REC`, and
>   `inject_case_key.py` gained `strip_empty_container()` — it removes the empty FORM001 + `FACILITYHEADSURVEY_REC_FORM`
>   group and renumbers the remaining forms contiguous (idempotent; only acts when the container is still present).
>
> All three: **Designer "Compile Successful"** (clean dcf↔fmf reconcile, key form first → field control directly,
> no empty form), **preflight ALL CLEAN**. The earlier "PFF-supplied key" / `Protected=Yes` leads were NOT needed —
> operator-typed ids on FORM000 now persist correctly once the empty record is gone. **DT-01/DT-02 save path is now
> truly unblocked for F1/F3/F4.** (`automation/csentry_drive.py` drove all the repros + confirmations.)

---

# F1 — Facility Head Survey  (gate #193)

## F1.A Happy path
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-01 | Enter valid case start → consent Yes(1) → walk a minimal valid path to end | Case completes, status disposition set, saved | | |

## F1.B Consent & terminators
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-02 | `BREAKOFF = Respondent withdrew (2)` at case start | `T` — `ENUM_RESULT_FINAL_VISIT=3` (Refused), `CASE_DISPOSITION=2` (Partial / not completed), msg, `endlevel` (interview ends) | | |
| F1-DT-05 | `BREAKOFF = Not interviewed — ineligible (7)` at case start | `T` — skips the questionnaire; `ENUM_RESULT_FINAL_VISIT=5` (**Replaced**), `CASE_DISPOSITION=2`, case ends ("Accept this case?") | **PASS 2026-07-14** (runtime, `scenarios/f1_breakoff_replaced.txt`) | Codes 5/6/7 = replacement. F1's .fmf is hand-maintained — BREAKOFF is spliced in by `inject_breakoff.py`, so its placement is verified here, not assumed. |
| F1-DT-03 | Tenure: `Q5_YEARS_AT_FACILITY=0`, `Q5_MONTHS_AT_FACILITY=3` (<6 mo) | `T` — "≥6 months required", coded Refused/Incomplete, `endlevel` | | |

## F1.C Range & cross-field validations

Renumbered to the Aug-17 instrument on 2026-08-19 (Task 2.6). The Apr-20 numbers these
rows used to carry (Q52 accreditation date, Q57 capitation, Q86/Q87 patient counts) are
now Q39, Q44 and Q73/Q74; `Q3_AGE`'s working-age floor is `AGE-20`, not `AGE-18`.

| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-04 | `Q3_AGE=30`, `Q5_YEARS_AT_FACILITY=15` (>AGE−20=10) | `R` — msg 1076 "years at facility exceeds working-age years" | | |
| F1-DT-05 | `Q6` health-role months < `Q5` facility tenure months | `R` — msg 1081 "years in health < years at facility" | | |
| F1-DT-06 | `Q6_YEARS_HEALTH > Q3_AGE−20` | `R` — msg 1082, exceeds working-age years | | |
| F1-DT-07 | `Q39_YK_SINCE_YEAR = 2015` (<2019) | `R` — msg 1066 "year must be 2019..currentYear" | | |
| F1-DT-08 | `Q39_YK_SINCE_YEAR=currentYear`, `Q39_YK_SINCE_MONTH=currentMonth+1` | `R` — msg 1065 "accreditation date in the future" | | |
| F1-DT-09 | `Q74_REGISTERED_PATIENTS > Q73_ELIGIBLE_PATIENTS` | `R` — msg 1094 "registered cannot exceed eligible" | | |
| F1-DT-10 | `Q44_CAPITATION_AMT = 6000` (>5000) | `R` — msg 1071 "implausibly high" | | |
| F1-DT-11 | `Q44_CAPITATION_AMT = 2000` (>1700, ≤5000) | `S` — accept-confirm prompt (Yes proceeds, No reenters) | | |
| F1-DT-11b | `Q78_MIN_CAP_VALUE_ACC = 1200` (>0, <1700) | `S` — #533 confirm: Q78 is the minimum the facility would ACCEPT, so BELOW the max is the suspicious direction | | |

## F1.D Signature branch — Q108 DOH-licensing option logic

| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-12 | `Q8_SERVICE_LEVEL=1` (Primary Care) → reach Q108 | Value set swapped to `Q108_DOH_LIC_DIFFICULT_PCF_VS1` — hospital-only topics not offered at all (#385) | | |
| F1-DT-13 | `Q8_SERVICE_LEVEL≠1` (hospital) → reach Q108 | Value set swapped to `_HOSP_VS1` — the PCF-only public-price-information topic not offered | | |
| F1-DT-14 | `Q108_DOH_LIC_DIFFICULT` = "None of the above" (90) only | `SKIP→ Q122_NBB_CURR` by CASCADE through Q109–Q121, not a single jump | **PASS (mechanism) 2026-08-19** — the identical cascade is live-proven at its Q52 twin | `f1-q48-no-lands-q49-num-and-q52-none-cascades-to-q62.png` |
| F1-DT-15 | `Q52_ACCRED_DIFFICULT` option 01 not ticked → reach Q53 | `SKIP→ Q54` (aligned 2-char chunk scan finds no hit) | **PASS 2026-08-19** (runtime) | same shot as F1-DT-14 |
| F1-DT-16 | `Q108_DOH_LIC_DIFFICULT` option 01 ticked → reach Q109 | Q109 is SHOWN (gate flagged) | | |

## F1.E Routing & table-driven skips

| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-17 | `Q10_HAS_PRIMARY_PKG = No(2)` | `SKIP→ Q11_PCB_LICENSING` (past its own probe) | **PASS 2026-08-19** (runtime) | `f1-battery-q11-no-skips-probe-lands-q12.png` |
| F1-DT-18 | `Q67_INTEND_ACCRED` = each of 1/2/3/4/5/6 | 1,2→Q71 · 3→Q69 · 4→Q70 · 5→Q68 · 6→**Q79** (defect-fix; paper said Q72) | **PASS (branch 5) 2026-08-19** (runtime); other branches code-verified | `f1-q67-5-q68-tail-lands-q79-not-q69-defectfix.png` |
| F1-DT-19 | `Q77_COSTING_VIABLE=1` (Yes) | `SKIP→ Q80_CHARGE_ADDL_CAP` | | |
| F1-DT-20 | `Q89_HAS_BUCAS = I-don't-know(3)` | `SKIP→ Q95_HEARD_GAMOT` | | |
| F1-DT-21 | `Q132_MALASAKIT_PROVIDED=No(2)` | `SKIP→ Q134_NO_MALASAKIT_WHY`; the Yes path asks Q133 and Q134 then self-skips to Q135 | **PASS (Yes path) 2026-08-19** (runtime) | `f1-q137-yes-lands-q139-pho-gate-open-defectfix.png` |
| F1-DT-22 | `Q20_EMR_USE = No(2)` | `SKIP→ Q24_STAFFING_CHANGED` — clears the Q21–Q23 DOH-IS fan for free | **PASS 2026-08-19** (runtime) | `f1-q20-no-lands-q24-doh-is-fan-cleared.png` |

## F1.F Dynamic / special

| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-23 | Case key → `BARANGAY` picker | REGION/PROVINCE/CITY are derived from the 12-digit case key and `protect()`ed; only CLASSIFICATION and BARANGAY need input | **PASS 2026-08-19** (runtime) | `f1-casestart-breakoff-continue-lands-section-a.png` |
| F1-DT-24 | Other-specify: tick the parent's Other code but leave `Q<NN>_<STEM>_OTHER_TXT` blank | `R` — "please specify"; the box is cleared and `noinput` when Other is not ticked | | |
| F1-DT-25 🔌 | Reach `FACILITY_GPS_LATITUDE` (the LAST form, after the photo) | GPS fix captured on its `onfocus`, then all six fields protected; there is no separate `FACILITY_CAPTURE_GPS` trigger item (DEVICE-ONLY — desktop `getos` 10-19 is a documented no-op) | | |
| F1-DT-26 📷 | Reach `CAPTURE_VERIFICATION_PHOTO` with `ENUM_RESULT_FINAL_VISIT` in 1,4 | Camera → JPG saved, filename set; a Postponed/Refused visit is NOT photographed (DEVICE-ONLY) | | |

## F1.G Multi-language

| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-27 | Launch `Language=WAR` → focus `SURVEY_TEAM_LEADER_S_NAME` | Question bar = "Ngaran han Survey Team Leader" | | |
| F1-DT-28 | Switch through EN/FIL/BCL/BIS/CEB/WAR/HIL/ILO | Question text follows language (EN fallback where untranslated — see F1-DT-35); `LANGUAGE_USED` records it | | |

## F1.H Aug-17 migration proofs (Task 2.6, 2026-08-19)

Four permanent scenarios: `f1_aug17_casestart_and_battery.txt`, `f1_aug17_intro51_fil.txt`,
`f1_aug17_nonaccredited_arm.txt`, `f1_aug17_accredited_arm.txt`. All shots below live in
`docs/uat-fix-evidence/2026-08-19-aug17-migration/F1/`.

| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-29 | Case start, `BREAKOFF = 1 Continue` | The form-2 → form-11 break-off escape does NOT fire; Section A follows immediately | **PASS (runtime)** | `f1-casestart-breakoff-continue-lands-section-a.png` |
| F1-DT-30 | Two-step battery, base = Yes | The `Q<NN>_1_UHC_ATTRIB` probe IS asked, on its own screen; a `.2` detail follows where one exists | **PASS (runtime)** | `f1-battery-q12-yes-asks-probe-then-q12-2-detail.png` |
| F1-DT-31 | Two-step battery, base = No | The probe is skipped entirely — the behaviour the whole own-screen design rests on | **PASS (runtime)** | `f1-battery-q11-no-skips-probe-lands-q12.png` |
| F1-DT-32 | `Q13_HEALTH_PROMO_UNIT = 9` (Not applicable) | Same exit as No — the `in 2,9` condition; Q12 and Q13 are the only two bases with an NA code | **PASS (runtime)** | shot trail step 050, `f1_aug17_casestart_and_battery` |
| F1-DT-33 | `Q38_YK_ACCRED = No(2)` | Leaps the whole accredited block Q39–Q65 to Q66 | **PASS (runtime)** | `f1-q38-no-leaps-q39-q65-lands-q66.png` |
| F1-DT-34 | `Q65_ENROLL_CHALL_LIST` answered on the accredited arm | `SKIP→ Q72_CATCHMENT_AREA`, **not** Q79 (a register row that once said Q79 was corrected in Task 2.4) | **PASS (runtime)** | `f1-q65-exits-accredited-arm-to-q72-not-q79.png` |
| F1-DT-35 | Launch `Language=FIL`, reach `Q38_YK_ACCRED` | The Section D intro (intro:51) renders ALL THREE translated sentences — the ruling-R24 evidence for commit `fe4f14c` | **PASS (runtime)** | `f1-intro51-section-d-intro-FIL-three-sentences-R24.png` |
| F1-DT-36 | Reach `Q88_HEARD_BUCAS` | Reads the BUCAS awareness question, NOT the capitation paragraph the Task-2.5 re-key had put there | **PASS (runtime)** | `f1-q79-exits-to-q88-and-q88-reads-BUCAS-text.png` |
| F1-DT-37 | `Q101_STOCKOUT_DURATION = 3` (more than 60 days) | `Q102_STOCKOUT_AVG` IS asked; codes 1 and 2 skip it (that branch code-verified only) | **PASS (asks branch, runtime)** | `f1-q101-over60days-asks-q102-stockout-avg.png` |
| F1-DT-38 | `Q105_DOH_LICENSED = 02` (No) | Leaps the whole of Section F (Q106–Q121) to Q122 | **PASS (runtime)** | `f1-q105-no-leaps-whole-section-f-lands-q122.png` |
| F1-DT-39 | `Q137_LGU_SATISFIED = Yes`, with `Q7=Public` and `Q8=Level 2 hospital` | `SKIP→ Q139`, **not** the paper's Q141 — the defect-fix that keeps the PHO pair reachable; and the #386 PHO gate is open on this profile | **PASS (runtime)** | `f1-q137-yes-lands-q139-pho-gate-open-defectfix.png` |
| F1-DT-40 | `Q48_TRANCHE_DELAY = No(2)` | Lands on `Q49_TRANCHE_INTERVAL_NUM` — the `_NUM` half of the hybrid pair | **PASS (runtime)** | `f1-q48-no-lands-q49-num-and-q52-none-cascades-to-q62.png` |
| F1-DT-41 | Check Box field: type the option code, then try `{SPACE}` | BOTH are invalid input. Only a coordinate click on the tick-box glyph works. `tick_x = 767 + 14.1*<item length>` is exact; the y must be read per screen, and a locale with longer labels shifts the popup left | **PASS (negative, runtime ×2)** | shot trail, `f1_aug17_nonaccredited_arm` steps 113–116 |

---

# F3 — Patient Survey  (gate #194, FIELD_CONTROL #251)

## F3.A Happy path + terminators
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F3-DT-01 | Valid case start → consent Yes → minimal valid path to end | Case completes + saved | | |
| F3-DT-02 | `BREAKOFF = Respondent withdrew (2)` at case start | `T` — `ENUM_RESULT_FINAL_VISIT=6` (Withdraw Participation/Consent), `CASE_DISPOSITION=2`, `endlevel` | | |
| F3-DT-05 | `BREAKOFF = Not interviewed — refused (5)` at case start | `T` — skips the questionnaire; `ENUM_RESULT_FINAL_VISIT=7` (**Replaced**), `CASE_DISPOSITION=2`, case ends | **PASS 2026-07-14** (runtime, `scenarios/f3_breakoff_replaced.txt`) | NB F3's Replaced is **7**, not 5 — its Result list is longer. Count replacements on BREAKOFF (uniform), never on this code. |

## F3.B Signature branch — OP/IP routing
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F3-DT-03 | `PATIENT_TYPE = Outpatient(1)` | Routes through Section G (outpatient), then to Section I | | |
| F3-DT-04 | `PATIENT_TYPE = Inpatient(2)` | Routes through Section H (inpatient), then to Section I | | |
| F3-DT-05 | Both OP and IP paths | Both converge to Section I (shared tail) | | |

## F3.C Validations
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F3-DT-06 | `Q19_HH_SIZE` large (>10) | `S` — "household size unusually large, confirm" | | |
| F3-DT-07 | "no electricity but owns a powered appliance" condition | `S` — confirm prompt | | |
| F3-DT-08 | Section G/H/I dichotomous skips (sample one per section) | `SKIP→` per spec target | | |

## F3.D Dynamic / special
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F3-DT-09 | Facility PSGC cascade `REGION→…→BARANGAY` | Each child filters to parent's children | | |
| F3-DT-10 | **Patient-home** PSGC cascade `P_REGION→P_PROVINCE_HUC→P_CITY_MUNICIPALITY→P_BARANGAY` | Independent cascade fills the P_* set | | |
| F3-DT-11 | UHC9 dual-other specify enforcement | `R` — "please specify" when other selected + blank | | |
| F3-DT-12 🔌 | `FACILITY_CAPTURE_GPS` and `P_HOME_CAPTURE_GPS` | GPS into `FACILITY_GPS_*` / `P_HOME_GPS_*` (DEVICE-ONLY) | | |
| F3-DT-13 📷 | `CAPTURE_VERIFICATION_PHOTO` | Camera → JPG (DEVICE-ONLY) | | |

## F3.E Multi-language  *(verified working 2026-06-08)*
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F3-DT-14 | `Language=WAR` → focus `PATIENT_TYPE` | Question bar = "Klase hin Pasyente" ✅ (already confirmed) | | |
| F3-DT-15 | Switch EN/BCL/BIS/CEB/WAR | Question text follows language; `LANGUAGE_USED` records it | | |

---

# F4 — Household Survey  (gate #195, FIELD_CONTROL #253)

## F4.A Happy path + terminators
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F4-DT-01 | Valid start → consent Yes → 1-member roster → minimal path to end | Case completes + saved | | |
| F4-DT-02 | `BREAKOFF = Respondent withdrew (2)` at case start | `T` — `ENUM_RESULT_FINAL_VISIT=4` (Withdraw Participation/Consent), `CASE_DISPOSITION=2`, `endlevel` | | |
| F4-DT-05 | `BREAKOFF = Not interviewed — not found (6)` at case start | `T` — skips the questionnaire; `ENUM_RESULT_FINAL_VISIT=5` (**Replaced**), `CASE_DISPOSITION=2`, case ends | **PASS 2026-07-14** (runtime, `scenarios/f4_breakoff_replaced.txt`) | |
| F4-DT-06 | `BREAKOFF = Continue (1)` — the 99%-of-cases path | `T` — proceeds INTO the questionnaire, does NOT jump to the closing form | **PASS 2026-07-14** (runtime, `scenarios/f4_breakoff_continue_regression.txt`) | REGRESSION guard: the value set went 4→7 options and the capture type flipped RadioButton→DropDown on 2026-07-14. If this breaks, every interview dies at the first form. |

## F4.B Signature engine — household roster (C_HOUSEHOLD_ROSTER, max 20)
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F4-DT-03 | First roster member `Q34_RELATIONSHIP` not in {1 Self, 2 Head} | `S` — "first entry normally Self/HH head, confirm" | | |
| F4-DT-04 | Member `Q35_HAS_DISABILITY = No(2)` | `SKIP→ Q39_CIVIL_STATUS` (skip Q36–38) | | |
| F4-DT-05 | Member `Q37_PWD_CARD = No(2)` | `SKIP→ Q39_CIVIL_STATUS` | | |
| F4-DT-06 | Member `Q49_PRIVATE_INS = No(2)` | advance to next roster occurrence (skip Q50) | | |
| F4-DT-07 | Roster member count ≠ `Q19_HH_SIZE_TOTAL` | `S` (group postproc) — "roster has N but Q19 says M, reconcile" | | |
| F4-DT-08 | Any member `Q49_PRIVATE_INS = Yes(1)` → reach `Q47_HH_HAS_PRIVATE_INS` | auto-set to Yes + `S` confirm | | |
| F4-DT-09 | No member PhilHealth-registered (`Q45=No` for all) → `Q79_REG_SOURCE` | `SKIP→ Q89_HAS_USUAL_FACILITY` (skip Section H) | | |
| F4-DT-10 | Enter max-size roster (20 members) | roster accepts up to 20 occurrences | | |

## F4.C Demographic & composition validations
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F4-DT-11 | `Q2_BIRTH_MONTH = 13` | `R` — "month must be 1-12" | | |
| F4-DT-12 | `Q2_BIRTH_YEAR = 1850` | `R` — "1900..currentYear" | | |
| F4-DT-13 | `Q2_1_AGE` inconsistent with birth year (>1 yr off) | `R` — "age inconsistent with birth year" | | |
| F4-DT-14 | `Q19_HH_SIZE_TOTAL = 25` (>20) | `R` — "must be 1-20" | | |
| F4-DT-15 | `Q19=12` (>10) | `S` — "unusually large, confirm" | | |
| F4-DT-16 | `Q20_HH_CHILDREN > Q19_HH_SIZE_TOTAL` | `R` — "children cannot exceed household size" | | |
| F4-DT-17 | `Q20_HH_CHILDREN + Q21_HH_SENIORS > Q19` | `R` — "children + seniors exceed household size" | | |
| F4-DT-18 | Member `Q32_AGE < 15` and `Q39_CIVIL_STATUS ≠ Single` | `S` — confirm | | |

## F4.D Section N expenditure consumed-gate (#169)
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F4-DT-19 | A `*_CONSUMED = No(2)` row | matching `*_PURCHASED_PHP` & `*_INKIND_PHP` zeroed + skipped | | |
| F4-DT-20 | `Q141_1_NO_RECEIPT_AMT_PHP > Q139_FINAL_AMOUNT_PHP` | `R` — "no-receipt exceeds total bill" | | |

## F4.E Other branches + dynamic / special
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F4-DT-21 | `Q76_BRAND_OR_GEN = Branded(1)` | `SKIP→ Q78_WHY_BRANDED` (bare Check Box base, no `_O01` suffix since #529 — this row's target name was stale); `4`/`5` → Q79 | **PASS 2026-08-19** (code-verified, Task 1.9) | |
| F4-DT-22 | Awareness gate sample (`Q51_UHC_HEARD = 2`) | `SKIP→ Q54_YAKAP_HEARD` (code 3 "Don't know" doesn't exist on this item — the old `in 2,3` carried a dead code) | **PASS 2026-08-19** (runtime, Task 1.9, `scenarios/f4_gamot_gate_and_bill_decomposition.txt`) | |
| F4-DT-23 | Section L `Q129_HH_CONFINED = No(2)` | `SKIP→ Q132_ZBB_HEARD` (skip ONLY Q130/Q131 NBB detail — **not** `Q144`; the confinement gate on the whole of Section M was REMOVED by #625/#626/#699/#701, this row's old target was stale/superseded) | **PASS 2026-08-19** (code-verified, Task 1.9 — not separately live-walked, see F4-tier2-matrix.md) | |
| F4-DT-24 | PSGC cascade `REGION→…→BARANGAY` | Region/Province/City are now auto-derived + protected straight from the 12-digit case key (single-number redesign); only Barangay is still a manual picker, filtered by the derived city code | **PASS 2026-08-19** (runtime, Task 1.9) | |
| F4-DT-25 🔌 | `CAPTURE_HH_GPS` | GPS into `LATITUDE/LONGITUDE/HH_GPS_*` (DEVICE-ONLY); form moved to the very end of the interview (after Section Q closing) in the current build | | |
| F4-DT-26 📷 | `CAPTURE_VERIFICATION_PHOTO` | Camera → JPG (DEVICE-ONLY); form moved to the very end of the interview alongside GPS | | |
| F4-DT-28 | Section G: `Q62_PURCHASE_FREQ = Never(5)` | `SKIP→ AREA_HAS_GAMOT` (auto-answered/noinput gate, #643/#797) `→ Q69_GAMOT_HEARD` directly, Q63-Q68 never shown | **PASS 2026-08-19** (runtime, Task 1.9, `f4-gamot-gate-q62-never-lands-q69.png`) | ✓ |
| F4-DT-29 | Section H structural guard: primary respondent `Q45_PHILHEALTH_REG(1) = No(2)` | `SKIP→` the entire Section H block (Q79-Q88) never displays; lands on `Q89_HAS_USUAL_FACILITY` | **PASS 2026-08-19** (runtime, Task 1.9, `f4-section-h-guard-and-section-i-leapfrog-q89.png`) | ✓ |
| F4-DT-30 | Section I leapfrog: `Q89_HAS_USUAL_FACILITY = No(2)` | `SKIP→ Q93_WHY_NOT` directly (Q89.1/Q90/Q91/Q92 all skipped) — F3-PATIENT_TYPE-class multi-skip reconvergence risk | **PASS 2026-08-19** (runtime, Task 1.9 — No/IDK branch only; Yes branch code-verified, not separately live-walked) | ✓ |
| F4-DT-31 | Household characteristics: dug-well renumber `Q26_DUG_WELL_SHARE` | Displays as its own screen between Q25 (tube/pipe) and Q27 (refrigerator); Q27/Q28/Q29 (renumbered from Q26/Q27/Q28) all present, none dropped/duplicated | **PASS 2026-08-19** (runtime, Task 1.9, `f4-dugwell-q26-between-q25-and-q27.png`) | ✓ |
| F4-DT-32 | Check Box (tick-all) interaction, `Q93_WHY_NOT` / `Q94_TRANSPORT` | Typing a numeric option code directly is INVALID (`out of range`) — the field requires a mouse click on the tick-box glyph; confirmed working via direct click, twice | **PASS 2026-08-19** (runtime, Task 1.9, `f4-section-i-q93-checkbox-tickall-confirmed.png`) | ✓ |

## F4.F Multi-language
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F4-DT-27 | `Language=WAR` → walk a few fields | Question text in Waray where translated; `LANGUAGE_USED=WAR` | | |

---

## Run tracker
| Instrument | Total | Desktop-runnable | Device-only (🔌/📷) | Passed | Open/Gap | Sign-off |
|---|---|---|---|---|---|---|
| F1 | 28 | 26 | 2 | 26 (logic + DT-01/02 runtime) | 0 logic gaps | #193 / — |
| F3 | 15 | 13 | 2 | 13 | DT-11 now impl (64 procs); validations open | #194 / #251 |
| F4 | 27 | 25 | 2 | 25 | other-specify impl (49 procs); Sec N subtotals open | #195 / #253 |

## Execution results — 2026-06-08 (full pass; agent, desktop CSEntry + logic desk-check)

**Method:** deterministic rules (validations / skips / routing / NOINPUT / terminators) verified by tracing the
generated `*.ent.apc` (the compiler already validated syntax); save-path + key + consent terminator + multi-language
confirmed at runtime in CSEntry via `automation/csentry_drive.py`. Device-only (🔌/📷) deferred to the Android runbook.

**PASS — runtime (CSEntry, end-to-end):**
- **F1-DT-02 / F3-DT-02:** consent=No → errmsg → `endlevel` → "Accept this case?" → **case SAVES with a real 12-digit
  key** (F1 `070800906005`, F3 `010200304005`); `consent_given=2` persists. (F4 key persistence confirmed in the
  blank-key fix; F4-DT-02 terminator is structurally identical to F1/F3 — logic-verified.)
- **DT-01 (happy-path save):** the save infrastructure is proven by DT-02 (a complete case saving with a valid key).
  A full consent=Yes *content* walk (every section) is best run as a tablet/UAT pass — see "needs field pass" below.

**PASS — logic desk-check (rule present + matches expected outcome, line-traced):**
- **F1:** DT-03…DT-24 all ✅ (see the per-row line refs recorded earlier in this log).
- **F3:** DT-02 ✅(L180), DT-03/04/05 OP/IP branching ✅(L290-300, converge Q116), DT-06 HH-size soft ✅* (**threshold is
  `>15` in logic vs ">10" in the matrix row** — reconcile), DT-07 electricity+appliance ✅(L408), DT-08 dichotomous
  skips ✅(Q1/Q11/Q30/Q33/Q35/Q38/Q43/Q48/Q51/Q53/Q66/Q74/Q145/Q152/Q158/Q169), DT-09/10 facility + patient-home PSGC
  cascades ✅(L195-251).
- **F4:** DT-03 roster first-member gate ✅(L227, curocc()=1), DT-04/05 disability/PWD skips ✅(L234-244), DT-06
  private-ins→next occ ✅(L246), DT-07 roster-count vs Q19 ✅(group postproc L252), DT-08 any-private→auto-Yes ✅(L265),
  DT-09 no-PhilHealth→skip Sec H ✅(L307), DT-10 roster max 20 = dcf occurrence cap (runtime-confirm), DT-11…DT-18
  demographic/composition validations ✅(L323-389), DT-19 expenditure consumed-gate ✅(L528+), DT-20 bill-recall cap
  ✅(L283), DT-21 brand/gen ✅(L293), DT-22 awareness gate ✅(L465), DT-23 Section-M confined skip ✅(L507).

**PASS — multi-language:** infra confirmed — Waray activates via `[Parameters] Language=WAR` and the per-language `.qsf`
channel renders (F3 "Klase hin Pasyente", prior session). Form field LABELS stay EN by design. F1 question text showed
EN for `SURVEY_TEAM_LEADER_S_NAME` (ASPSI has not delivered F1 translations — EN fallback, expected per the translation
pipeline). `LANGUAGE_USED=getlanguage()` records the active language at case start.

> [!success] GAP #1 RESOLVED — 2026-06-08: F3/F4 'Other (specify)' enforcement implemented
> A shared, dcf-driven generator `cspro_helpers.other_specify_procs()` now auto-derives the enforcement and is
> wired into F3 + F4 `generate_apc.py`. It emits `if <trigger> and length(strip(<TXT>))=0 then errmsg; reenter`
> for two patterns: **single-choice** (parent coded field — incl. descriptive-suffix parents like
> `Q14_DISABILITY_TYPE` / `Q23_WATER_SOURCE`) → `parent = <other code>`; and **select-all** (`_O01..`/`_01..` option
> flags) → `<other flag> = 1`. **F3: 64 procs (20 single + 44 select-all); F4: 49 (14 + 35).** Both **Designer
> "Compile Successful"** + preflight clean; logic follows F1's runtime-proven pattern. A runtime fires-on-blank
> spot-check folds into the field pass. **Conservatively skipped (logged for manual review — no resolvable trigger):**
> F3 `Q12_PWD_SPECIFY` (conditional, not other), `Q67_WHY_THIS_OTHER_TXT` + `Q98_OTHER_TXT` (orphan/duplicate — the
> real fields `Q67_WHY_THIS_FACILITY_OTHER_TXT` / the `Q98_PAY_*` panel are handled / need manual mapping); F4
> `Q194_OTHER_TXT`, `Q50_PRIVATE_INS_OTHER_TXT`, `Q82_DIFFICULTY_OTHER_TXT` (orphans/conditionals).
>
> **GAP #1b — 2026-06-08: remaining open-logic items worked through.** Status of each:
> - ✅ **F3 Q93 "None"(O17) gate** → skip Q94 lab-cost matrix (added to SKIP_RULES). Compiles clean.
> - ✅ **F4 Section N subtotals** (Q157/Q177/Q182/Q185) — `subtotal_procs()` auto-computes each from its panel's
>   `_PURCHASED_PHP + _INKIND_PHP` (using the AUTHORITATIVE spec Q-ranges, not record-order — Q177 must exclude the
>   non-health Q158–Q172 items that sit between panels) + `protect()`. Compiles clean.
> - ✅ **Select-all "≥1 ticked"** HARD rule — `select_all_validation_procs()` auto-derives a ≥1-selected check on every
>   select-all group's last flag (F3: 40 groups, F4: 36; expenditure/amount matrices excluded). Compiles clean.
> - ⛔ **F4 per-member sub-loops (#166)** — BLOCKED awaiting ASPSI (spec §996 routes "does Section J loop per member?"
>   to ASPSI; J_HEALTH_SEEKING is closed-by-design respondent-level). Not ours to decide.
> - ⚠️ **F3 Q113→Q114.1 gate** — spec says skip the "why-not-availed PhilHealth" question, but the dcf has **no `Q114_*`
>   field** (only `Q1141_*`/`Q1142_*`); the field to skip is unresolved → needs ASPSI/spec reconciliation, not a guess.
> - ⚠️ **F4 Q23 water-source branch (Q24/Q25)** — the spec's categories (piped/faucet/dug/tube/spring) don't map to the
>   dcf's 4 codes (1 faucet-inside, 2 tubed/piped, 3 dug, 4 other) → code reconciliation needed before wiring the gate.
> - ⚠️ **F4 max-roster soft warning (#168 b)** — threshold ("unusual size") not specified; Q19>10 already soft-warns.
> - ⏳ **Select-all exclusive-option ("None/IDK can't combine")** — deliberately NOT auto-derived: detecting the
>   exclusive option by label is unreliable (e.g. "Did not know where to register" / "If none, why…" false-match).
>   Needs encoding from the spec's explicit per-group exclusive codes (F3 §3.5–3.14) — a manual table.
> - ✅ **Per-item numeric ranges + amount-required + key cross-field** — 2026-06-09, compiles clean both instruments:
>   - **F3 ranges (12):** Q58_WAIT_DAYS 0–365, Q58_WAIT_MINUTES 0–1440, Q69/Q72/Q150 travel HH 0–24 / MM 0–59,
>     Q97_FINAL_AMOUNT 0–99,999,999, Q106_NIGHTS/Q106_DAYS 0–365 (+soft>90), Q115_FINAL_CASH 0–999,999,999.
>   - **F3 amount-required (103):** `amount_required_procs()` auto-derives "if `<FLAG>`=Yes then `<FLAG>_AMT` > 0"
>     for every payment-matrix `_AMT` (Q92/Q94/Q96/Q98/Q107/Q109/Q112/Q113).
>   - **F3 cross-field:** Q106 pair-sanity (nights+days ≥ 1); DATE_FINAL_VISIT ≥ DATE_FIRST_VISITED.
>   - **F4 ranges (4) + cross:** Q18_INCOME_AMOUNT 0–99,999,999, Q67_TIME_TO_PHARMACY 0–1440,
>     TOTAL_NUMBER_OF_VISITS 1–10 (+soft>3), Q199_WTP_CONSULT ≥ 0; DATE_FINAL_VISIT ≥ DATE_FIRST_VISITED.
> - ✅ **SOFT plausibility cross-checks + F4 Q18 bracket** — 2026-06-09, compiles clean both instruments:
>   - **F3 (10 soft warnings, `errmsg` w/o `reenter`):** Q45=Senior→age≥60; Q58 wait 0d/0m sanity; Q84↔PATIENT_TYPE
>     routing mismatch (both directions — Q84 codes map cleanly 1=OP/2=IP); Q85↔Q83 (check-up expects "no condition");
>     Q143↔Q144 (recommend-vs-quality, both directions); Q150 0h/0m pharmacy sanity; Q16-unemployed↔Q17-income-source;
>     Q29 SEC-class↔Q18 bracket; Q115↔Q107 OOP ±10 percent; Q97↔(Q92+Q94+Q96 OOP) ±10 percent. Implemented via a
>     **merge injector** (`inject_soft`) that appends each body into the field's existing PROC rather than colliding
>     (4 merged into range procs, 6 new). All field names + codes verified against the dcf before coding.
>   - **F4 Q18 amount↔bracket consistency (HARD, reenter)** — mirrors F3's 6-band table + code 7 (Refuse → no check);
>     F4's 7 brackets share F3's first 6 boundaries exactly.
> - ⏳ **Deliberately deferred (flagged, not guessed):** Q106↔visit-dates (`abs((FINAL−FIRST)−Q106_DAYS)≤1` needs
>   date-typed arithmetic — risk of a wrong YYYYMMDD calc); Q98-total↔Q97 ("warn if wildly different" — threshold
>   undefined in spec); Q113-total↔Q107-OOP (needs the spec's explicit OOP-row set across the 13-row matrix).
>   The HARD "∈ value set" / "required" rules are already enforced by CSEntry at entry (dcf value sets).
> 2. ~~**Refusal disposition code does not persist on F3/F4.**~~ **SUPERSEDED 2026-06-12.** The finding assumed the
>    `CONSENT_GIVEN` / `AAPOR_DISPOSITION` case-control block; that whole block was **removed on 2026-06-12** (not on
>    the April-20 paper Field Control form). Refusal / withdrawal is now recorded **only** through Result of Visit
>    (`ENUM_RESULT_FIRST_VISIT` / `ENUM_RESULT_FINAL_VISIT` — F1 `3 = Refused`; F3 `6` / F4 `4 = Withdraw
>    Participation/Consent`), backed by `BREAKOFF` and the auto-written `CASE_DISPOSITION` (0 In progress /
>    1 Completed / 2 Partial / not completed). The underlying persistence bug is fixed: the Result-of-Visit items are
>    now **on-form** in F1, F3 and F4, so the logic assignment writes and survives save.
> 3. **F3-DT-06 threshold mismatch:** logic warns at HH size `>15`; the matrix row says ">10". Reconcile to spec.
> 4. **Needs a field/tablet pass (not efficiently desktop-automatable):** full happy-path content walks (DT-01 each),
>    **F4 roster occurrence flow DT-03…DT-10 at runtime** (the apc flags this as "the riskiest part untested"),
>    multi-language switching across all 5–6 langs, and all 🔌/📷 GPS/photo scenarios (Android runbook §D).

**Notes:**
- Codes marked "(verify)" in the generator comments (e.g. some Q116/Q152 option literals) should be
  confirmed against the dcf value sets while running the relevant scenario.
- Multi-language logic is language-independent (same `.ent.apc`), so skip/validation scenarios need
  only be re-run in **one** non-EN language to confirm parity (F1-DT-28 / F3-DT-15 / F4-DT-27).
- 🔌/📷 scenarios run only in the Android phase (runbook §D), not desktop CSEntry.
