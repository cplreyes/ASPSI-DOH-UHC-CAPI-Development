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
> **Status: OPEN — needs Carl's CSPro call (PFF-supplied key vs drop empty record vs forum escalation).
> DT-01 happy-path not run (blocked by this). Tooling: `automation/csentry_drive.py` drives the repro.**

---

# F1 — Facility Head Survey  (gate #193)

## F1.A Happy path
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-01 | Enter valid case start → consent Yes(1) → walk a minimal valid path to end | Case completes, status disposition set, saved | | |

## F1.B Consent & terminators
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-02 | `CONSENT_GIVEN = No(2)` | `T` — `ENUM_RESULT_FINAL_VISIT=4` (Refused), msg, `endlevel` (interview ends) | | |
| F1-DT-03 | Tenure: `Q5_YEARS_AT_FACILITY=0`, `Q5_MONTHS_AT_FACILITY=3` (<6 mo) | `T` — "≥6 months required", coded Refused/Incomplete, `endlevel` | | |

## F1.C Range & cross-field validations
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-04 | `Q3_AGE=30`, `Q5_YEARS_AT_FACILITY=15` (>AGE−18=12) | `R` — "years at facility exceeds working-age years" | | |
| F1-DT-05 | `Q6` health-role months < `Q5` facility tenure months | `R` — "years in health < years at facility" | | |
| F1-DT-06 | `Q6_YEARS_HEALTH > Q3_AGE−18` | `R` — exceeds working-age years | | |
| F1-DT-07 | `Q52_YK_SINCE_YEAR = 2015` (<2019) | `R` — "year must be 2019..currentYear" | | |
| F1-DT-08 | `Q52_YK_SINCE_YEAR=currentYear`, `Q52_YK_SINCE_MONTH=currentMonth+1` | `R` — "accreditation date in the future" | | |
| F1-DT-09 | `Q87_REGISTERED_PATIENTS > Q86_ELIGIBLE_PATIENTS` | `R` — "registered cannot exceed eligible" | | |
| F1-DT-10 | `Q57_CAPITATION_AMT = 6000` (>5000) | `R` — "implausibly high" | | |
| F1-DT-11 | `Q57_CAPITATION_AMT = 2000` (>1700, ≤5000) | `S` — accept-confirm prompt (Yes proceeds, No reenters) | | |

## F1.D Signature branch — Q121 DOH-licensing option logic
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-12 | `Q8_SERVICE_LEVEL=1` (Primary Care) → reach Q121 | `NOINPUT` — O10/O11/O12 (hospital-only) hidden | | |
| F1-DT-13 | `Q8_SERVICE_LEVEL≠1` (hospital) → reach Q121 | `NOINPUT` — O13 (primary-care-only, public price info) hidden | | |
| F1-DT-14 | `Q121_DOH_LIC_DIFFICULT_O14 = 1` ("None of the above") | `SKIP→ Q135_NBB_CURR` (skip the why-difficult cluster) | | |
| F1-DT-15 | `Q65_ACCRED_DIFFICULT_O01=0` → reach Q66 cluster | `SKIP→` first field after Q66's cluster (gate not flagged) | | |
| F1-DT-16 | `Q121_DOH_LIC_DIFFICULT_O01=1` → reach Q122 cluster | Q122 cluster is SHOWN (gate flagged) | | |

## F1.E Routing & table-driven skips (representative)
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-17 | `Q10_HAS_PRIMARY_PKG = No(2)` | `SKIP→ Q12_PCB_LICENSING` | | |
| F1-DT-18 | `Q80_INTEND_ACCRED` = each of 1/2/3/4/5/6 | 1,2→Q84 · 3→Q82 · 4→Q83 · 5→Q81 · 6→Q85 (5-way routing) | | |
| F1-DT-19 | `Q90_COSTING_VIABLE=1` & `Q51_YK_ACCRED=1` | `SKIP→ Q91_MIN_CAP_VALUE_ACC` | | |
| F1-DT-20 | `Q102_HAS_BUCAS = I-don't-know(3)` | `SKIP→ Q108_HEARD_GAMOT` | | |
| F1-DT-21 | `Q145_MALASAKIT_PROVIDED=No(2)` | `SKIP→ Q147_NO_MALASAKIT_WHY_O01`; (Yes path skips Q147→Q148) | | |
| F1-DT-22 | `Q31_EMR_USE in 5:8 or =9` | `SKIP→ Q35_STAFFING_CHANGED` | | |

## F1.F Dynamic / special
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-23 | Focus `REGION` → pick a region → `PROVINCE_HUC` → `CITY_MUNICIPALITY` → `BARANGAY` | PSGC cascade — each child value set filters to children of the chosen parent | | |
| F1-DT-24 | UHC9 dual-other: select code 4/7 but leave `*_OTHER_TXT` blank | `R` — "please specify" | | |
| F1-DT-25 🔌 | Trigger `FACILITY_CAPTURE_GPS` | GPS fix into `FACILITY_GPS_*` (DEVICE-ONLY) | | |
| F1-DT-26 📷 | Trigger `CAPTURE_VERIFICATION_PHOTO` | Camera → JPG saved, filename set (DEVICE-ONLY) | | |

## F1.G Multi-language
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F1-DT-27 | Launch `Language=WAR` → focus `SURVEY_TEAM_LEADER_S_NAME` | Question bar = "Ngaran han Survey Team Leader" | | |
| F1-DT-28 | Switch through EN/BCL/BIS/CEB/WAR/HIL | Question text follows language (EN fallback where untranslated); `LANGUAGE_USED` records it | | |

---

# F3 — Patient Survey  (gate #194, FIELD_CONTROL #251)

## F3.A Happy path + terminators
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F3-DT-01 | Valid case start → consent Yes → minimal valid path to end | Case completes + saved | | |
| F3-DT-02 | `CONSENT_GIVEN = No(2)` | `T` — `ENUM_RESULT_FIRST_VISIT=4`, `endgroup` | | |

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
| F4-DT-02 | `CONSENT_GIVEN = No(2)` | `T` — `endgroup` | | |

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
| F4-DT-21 | `Q76_BRAND_OR_GEN = Branded(1)` | `SKIP→ Q78_WHY_BRANDED_O01` (skip Q77); 3/4 → Q79 | | |
| F4-DT-22 | Awareness gate sample (`Q51_UHC_HEARD in 2,3`) | `SKIP→ Q54_YAKAP_HEARD` | | |
| F4-DT-23 | Section M `Q129_HH_CONFINED = No(2)` | `SKIP→ Q144_CEREALS_CONSUMED` (skip Section M) | | |
| F4-DT-24 | PSGC cascade `REGION→…→BARANGAY` | child value sets filter to parent | | |
| F4-DT-25 🔌 | `CAPTURE_HH_GPS` | GPS into `LATITUDE/LONGITUDE/HH_GPS_*` (DEVICE-ONLY) | | |
| F4-DT-26 📷 | `CAPTURE_VERIFICATION_PHOTO` | Camera → JPG (DEVICE-ONLY) | | |

## F4.F Multi-language
| ID | Setup → Input | Expected | Result | Shot |
|---|---|---|---|---|
| F4-DT-27 | `Language=WAR` → walk a few fields | Question text in Waray where translated; `LANGUAGE_USED=WAR` | | |

---

## Run tracker
| Instrument | Total | Desktop-runnable | Device-only (🔌/📷) | Passed | Failed | Sign-off |
|---|---|---|---|---|---|---|
| F1 | 28 | 26 | 2 | | | #193 / — |
| F3 | 15 | 13 | 2 | | | #194 / #251 |
| F4 | 27 | 25 | 2 | | | #195 / #253 |

**Notes:**
- Codes marked "(verify)" in the generator comments (e.g. some Q116/Q152 option literals) should be
  confirmed against the dcf value sets while running the relevant scenario.
- Multi-language logic is language-independent (same `.ent.apc`), so skip/validation scenarios need
  only be re-run in **one** non-EN language to confirm parity (F1-DT-28 / F3-DT-15 / F4-DT-27).
- 🔌/📷 scenarios run only in the Android phase (runbook §D), not desktop CSEntry.
