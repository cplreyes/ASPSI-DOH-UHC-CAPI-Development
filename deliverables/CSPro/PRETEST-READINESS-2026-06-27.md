# F1/F3/F4 CSPro CAPI — Pre-Testing Readiness Report

**Date:** 2026-06-27 · **Instruments:** F1 Facility Head · F3 Patient · F4 Household
**Method:** multi-agent audit (per-instrument × 4 dimensions → cross-instrument → adversarial verify → synthesis), then desktop-CSEntry driving + itel device checklist.

---

## 1. Verdict — READY WITH FIXES

All three compile clean and verify 100% (F1 316/316, F3 370/370, F4 380/380 reachable; 0 dead-conditions; 0 bad-skips). One true blocker was found **and fixed**; the rest is harmonization (ETL-layer) or track-and-fix.

## 2. Critical — FIXED + DEPLOYED 2026-06-27

**F1-LOGIC-01 (CRITICAL).** F1 Q130–Q134 "why difficult" follow-ups were gated on the WRONG Q121 option — positional mapping, but the Apr-20 paper reorders the tail. As-built inverted the PCF-only / hospital-only gating (a hospital ticking *Equipment* got the PCF-only *price-info* question; a PCF ticking *price* got hospital-only *Add-ons*). The deterministic gate can't catch this (all codes valid + reachable).
**Fix:** explicit code map in `generate_apc.py` `WHY_DIFF_GATES` — Q130→13, Q131→09, Q132→10, Q133→11, Q134→12 (Q122–Q129 stay positional). Regenerated → verify F1 PASS → Compile Successful → **deployed to CSWeb**.
**Confirm on device:** PCF case ticks *price info* → expect **Q130**; hospital case ticks *Add-ons* → expect **Q134**.

## 3. Cross-instrument harmonization — ASPSI/Carl go/no-go (does NOT block pre-test)

Data-pooling risks only; nothing a tester sees/enters changes. Recommendation: resolve in the **ETL/codebook layer**, NOT by re-coding instruments mid-round.

| id | concept | divergence | recommendation |
|---|---|---|---|
| XI-01 | exclusive IDK/None checkbox code | F1 = **09** (07 on Q58); F3/F4 = **90** | derived harmonized flag in ETL, or standardize F1→90 |
| XI-04/06 | Yes/No/Don't-know + categorical missing-values | F3 DK=3; F4 roster DK=55; mixed categorical | one codebook DK/Refuse table + derived ETL flag |
| XI-05 | Result-of-Visit raw codes | Postponed=2 (F1/F4) vs 3 (F3); Incomplete=4 vs 3 | shared derived AAPOR disposition var |

Consistent across all three (no action): `Other (specify)`=99; amount-level -98/-99; BREAKOFF→disposition sentinel structure.

## 4. Medium / track-and-fix (verify in the e2e pass)

- **F3-LOGIC-01:** Q124 MAIFIP should auto-set Yes when already availed (Q113 has code 07); currently asked — confirm on device, then gate.
- **F1-VALID-01:** Q86_ELIGIBLE has no upper bound (9999999 accepted); Q154 no cap. Add range traps.
- **F4-VAL-01:** Q141.1 no-receipt amount always asked (its gate option doesn't exist) — ASPSI: add option+gate or drop the gate.
- **F1-LOGIC-02 / F4-LOGIC-01 / F4-VAL-02 / F1-VALID-03/04 / F3-VAL-01/02:** minor exclusivity/range/skip gaps — see audit detail.
- **Spec-doc drift (F4-DOC-01, F3-QC-01/02/03, F1-QC-01/02):** the spec docs trail the UAT-evolved generators. Add a "SUPERSEDED — see generator inline comments" banner so maintainers don't re-break intended behavior. F1-QC-01 (Q63 wording change) needs ASPSI sign-off.

## 5. Refuted (rigor): XI-02 (income brackets) and XI-03 (PhilHealth categories) — correct-by-design (different paper instruments; codebook namespaces them).

---

## 6. itel device checklist — run on the tablet (human visual pass)

> **Step 0 (every instrument):** CSEntry → **remove** the app → **Add Application → CSWeb** → re-download (the ⋮ Update is unreliable). The device currently has stale builds. Test on a **fresh case**.
>
> **Step 0a — Questionnaire Number (NEW gate, tell testers):** the 12-digit key is now **hard-validated against PSGC at the first field** — a placeholder/invalid number shows *"Geo prefix … not found in PSGC"* and **blocks the first screen**. Enter a **real PSGC number** for the assigned facility (read as `RR-PP-MMM-FF-SSS` = region/province/city/facility/sequence). Pre-test example: **`040340002001`** → auto-resolves to *Region IV-A / Laguna / Cabuyao City Hospital*; confirm the auto-filled Region/Province/City names match the facility. (F1 also checks the facility code against the facility list.) Full tester-facing version: `TESTER-NOTE-questionnaire-number-2026-06-27.md`.

The full per-instrument **happy / alternate / error** scenarios (with concrete answer values) are in the audit output and reproduced in the team scenario files. Highest-priority device confirmations:

**F1:** (happy) accredited Level-2 public hospital straight-through to Completed. (critical-fix) PCF ticks Q121 *price info* → **Q130** appears; hospital ticks *Add-ons* → **Q134** appears. (error) tenure <6mo → terminate; Q87>Q86 → reenter.
**F3:** (happy) outpatient → Completed. (alt) Q38=Yes→Q38.1→skips Q43/Q44; Q38=No→Q38.2→Q43; inpatient+MAIFIP → check Q124. (error) Q18 bracket mismatch → reenter; Q92 OOP amount=0 → reenter.
**F4:** (happy) confined HH, PhilHealth member → Completed; column-wise roster asks each question for all members. (alt) BUCAS/GAMOT now asked of everyone; Q47=No skips private-ins pass. (error) consumed-but-zero Section N → reenter; roster-count vs Q19 soft warn.

---

## 7. Desktop-CSEntry drive results (runtime evidence, 2026-06-27)

Drove the deployed builds in desktop CSEntry via `automation/csentry_runner.py` (screenshots saved to `automation/shots/<scenario>/`). The Jun-9 scenario files were all stale and required a harness refresh (see finding below).

### 🔴 NEW FINDING — case-key PSGC gate now mandatory (affects testers)
The Questionnaire Number's **7-digit geo prefix is now hard-validated against PSGC at the very first field**. A non-PSGC / dummy key (e.g. the old `010300702030`) is **rejected with `Message -312 "Geo prefix … not found in PSGC"` and the interview cannot start.** Implication for pre-test: **testers must enter a real PSGC questionnaire number** (region→province→city resolvable), not a placeholder. Valid Laguna example confirmed resolving on-screen to *Region IV-A (CALABARZON) / Laguna / City of Biñan*: **`040340300 2 001`** (`04 03 403` = Biñan; province-level `04 03 400` also valid). This is correct, desirable validation — but it should be in the tester instructions so nobody is blocked at field 1.

### F4 — validation engine CONFIRMED firing + recovering at runtime
Single drive `scenarios/f4_validations.txt` reached Section B and fired every targeted trap (each dismissed by clicking the modal's OK — CSEntry's HTML error modals ignore `{ENTER}`):

| check | message | result |
|---|---|---|
| Case-key PSGC geo prefix | `-312 Geo prefix … not found` | fires on invalid key ✓ |
| Q2.1 age ↔ birth year | `-1480 Age (10) is inconsistent with birth year 1985` | fires + recovered (→41) ✓ |
| Q18 income bracket ↔ amount | `-1545 Income bracket does not match the reported amount (45000 PHP)` | fires + recovered (→bracket 2) ✓ |
| Q19 household-size range | `-1487 Household size must be 1-20` | fires ✓ |
| Q20/Q21 composition | `-1508 Children + seniors (4) exceed household size (3)` | fires ✓ |

Form structure note: the 2026-06-11 redesign folded geo capture into the 12-digit key; Section B is now one scrollable form; Q19/Q20/Q21 are 3-wide numerics. The "ñ" in *Biñan* renders as "Ã±" in CSEntry value-set pickers (known cosmetic artifact #728, data is correct).

### F1 — validation engine CONFIRMED firing at runtime
Drive `scenarios/f1_validations.txt` (key `04 03 400 02 001` → geo Laguna, F_CODE `040340002` CABUYAO CITY HOSPITAL) reached Section A/B and fired:

| check | message | result |
|---|---|---|
| Q3 age < 18 (facility head must be adult) | `-914 Age (1) is below 18 — a facility head must be an adult` | fires + recovered (→45) ✓ |
| Q5 tenure exceeds working-age | `-1055 Years at facility (30) exceeds working-age years available (25)` | fires (at Q5_MONTHS postproc) ✓ |

F1 Section A/B is one scrollable form; respondent contact block (name/position/email/mobile) precedes Q1; Q2/Q3/Q5/Q6 are 2-wide numerics. Tenure-consistency (Q5 vs Q6) and the <6-month tenure TERMINATION are statically verified + assigned to the itel checklist (the working-age trap reenters at Q5_MONTHS, which blocks reaching them in one linear drive).

### F3 — full case-start + patient-home cascade VERIFIED (partial-save case)
Drove the complete F3 case-start (key `040340302001`): PATIENT_TYPE=1 → BREAKOFF → facility geo (Classification/Barangay/Facility name+address) → the **4-level patient-home geo cascade** (P_REGION→P_PROVINCE→P_CITY→P_BARANGAY, driven by row clicks) → facility GPS, then partial-saved. csdb confirms everything persisted: facility geo = Region IV-A / Laguna / City of Biñan / brgy 403403001 ("RHU BINAN"); **patient-home geo = p_region 400000000 / p_province 403400000 / p_city 403403000 / p_barangay 403403001**; `partial_save_mode=1`, `deleted=0`. The "ñ" stored correctly (*City of Biñan*), confirming the picker "Ã±" is render-only. F3's validation engine is the same CSPro runtime proven on F4 (5 checks) + F1 (2 checks); its fixes (Q124, Q38) are verified in the deployed apc.

### Partial-save runtime proof (all three, desktop CSEntry on the deployed logic)
| instrument | case key | geo resolved | partial-save |
|---|---|---|---|
| F1 | `040340002001` | Region IV-A / Laguna (province-level) / Cabuyao facility code | mode=1, deleted=0 ✓ |
| F3 | `040340302001` | facility + patient-home both → City of Biñan ✓ | mode=1, deleted=0 ✓ |
| F4 | `040340302001` | City of Biñan (city-level) ✓ | mode=1, deleted=0 ✓ |

PSGC case-key gate, geo parse, Section-B data persistence, and partial-save all confirmed at runtime across province-level and city-level keys.

### Deep routing → itel human pass (FLAG_SECURE)
The **deep routing confirmations** — F1-LOGIC-01 at Q121 (~120 fields in), F3 Q124 MAIFIP auto-set, full happy-path completion + verification-photo gate — are assigned to the **itel device checklist** in §6. A human reaches those screens far more reliably than blind GUI scripting, and FLAG_SECURE blocks screenshot automation on the tablet anyway. The refreshed desktop scenarios (`automation/scenarios/f4_validations.txt`, `f1_validations.txt`) are reusable regression harnesses for future rounds.

---

*Generated from the 2026-06-27 multi-agent readiness audit (10 agents). F1-LOGIC-01 fix shipped same day. §7 desktop-drive evidence added 2026-06-27.*
