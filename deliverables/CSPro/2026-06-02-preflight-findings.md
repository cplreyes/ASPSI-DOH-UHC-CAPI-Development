# CSPro pre-flight findings + Designer-compile runbook

**Date:** 2026-06-02 · **Instruments:** F1 (FacilityHead), F3 (Patient), F4 (Household)
**Tool:** `deliverables/CSPro/preflight_validate.py` (run: `python deliverables/CSPro/preflight_validate.py`)

## Why this exists

The CSPro **Designer compile** is a Windows-GUI operation (open the app → Designer compiles the logic → errors show in the GUI). It can't be driven headlessly from the agent session. So instead of guessing, I built a **static pre-flight validator** that cross-checks every dictionary symbol referenced in each `.ent.apc` against its `.dcf` + the `#include`d shared helpers. It catches the **compile-error class** — a `PROC` for a non-existent item, or a reference to an undefined dictionary symbol — which is exactly the item-name-drift failure mode the project keeps hitting (spec names ≠ dcf names). It is **not** a full compiler (no syntax/type/arity checking); the real Designer compile is still required.

## Result at a glance

| Instrument | Pre-flight status | Action |
|---|---|---|
| **F3** Patient | ✅ **CLEAN** (61 PROCs resolve, 0 undefined refs) | Ready for Designer app-creation + compile |
| **F4** Household | ✅ **CLEAN** (125 PROCs resolve, 0 undefined refs) | Ready for Designer app-creation + compile |
| **F1** FacilityHead | ⚠️ **8 items need questionnaire reconciliation** | See §"F1 reconciliation" — needs Carl before compile |

## Fixes applied (mechanical, dcf-grounded — capture-trigger/field name drift)

The generators had hardcoded capture-trigger / GPS-field names that didn't match each instrument's dcf. The dcf is authoritative; I corrected the generator tables and regenerated. **Never hand-edit the `.apc`** — these were fixed in `generate_apc.py` and regenerated.

| Instrument | Was (generator) | Now (dcf truth) |
|---|---|---|
| F1 | `PROC VERIFICATION_PHOTO` (+ reset line) | `PROC CAPTURE_VERIFICATION_PHOTO` |
| F3 | `PROC P_CAPTURE_HOME_GPS` (+ reset line) | `PROC P_HOME_CAPTURE_GPS` (word-order typo) |
| F4 | `PROC FACILITY_CAPTURE_GPS` + 6 `FACILITY_GPS_*` fields | `PROC CAPTURE_HH_GPS` + `LATITUDE`/`LONGITUDE`/`HH_GPS_*` (F4 captures the household location, not facility) |

These cleared F3 and F4 entirely and removed F1's photo-trigger error.

## F1 reconciliation — needs Carl (questionnaire + structure decisions)

These are **not** mechanical name typos. The F1 spec/generator was authored against a questionnaire version whose numbering/labels differ from the **current dcf** — most of the broken skip targets reference concepts that **don't exist anywhere in the current dcf**. A wrong skip target silently misroutes interviews (worse than a caught compile error), so these need your authoritative current questionnaire, not a guess.

### (a) 7 broken `skip to` targets

Each is a `skip to <TARGET>` in the generator's `SKIP_RULES` table; `<TARGET>` is not a dcf item.

| Gate (skip fires when) | Broken target (spec + gen) | dcf item at that Q# | Concept in current dcf? |
|---|---|---|---|
| `Q37_REFERRAL_CHANGED = 2` | `Q39_REFERRAL_HOW` | `Q39_MOU_MOA` | "referral_how" **absent** (referral lives at Q37/Q38) |
| `Q51_YK_ACCRED = 2` | `Q79_NOT_ACCRED_REASON` | `Q79_NOT_ACCRED_REASON_O01…O04` | **present** — likely just needs `_O01` (multi-select 1st field) |
| `Q77_ENROLL_CHALL = 2` | `Q85_OUTPATIENT_BENEFIT` | `Q85_CATCHMENT_AREA` | "outpatient_benefit" **absent entirely** |
| `Q89_COSTING_DONE = 2` | `Q91_CHARGE_BEYOND_CAP` | `Q91_MIN_CAP_VALUE_ACC` | nearest is `Q93_CHARGE_ADDL_CAP` |
| `Q97_PAYMENT_CHALL = 2` | `Q99_YK_IMPROVE` | `Q99_EXPAND_NEXT_O01…` | "yk_improve" **absent** (YK cluster is Q51–Q53) |
| `Q141_ALLOW_OOP_BASIC = 2` | `Q143_CHARGE_PF` | `Q143_DIFFICULT_BENEFIT` | "charge_pf" (prof. fee) **absent entirely** |
| `Q161_REF_SATISFACTION in 1,2` | `Q163_HR_CHALL` | `Q163_HR_CHALL_O01…O05` | **present** — likely just needs `_O01` (multi-select 1st field) |

**Likely quick wins (2):** `Q79_NOT_ACCRED_REASON → Q79_NOT_ACCRED_REASON_O01` and `Q163_HR_CHALL → Q163_HR_CHALL_O01` (the concept exists; the dcf just splits the multi-select into option fields and the skip should land on the first one). I left these for you to confirm rather than auto-apply, since the whole skip table needs one holistic reconciliation pass.

**Genuine reconciliation (5):** Q39/Q85/Q91/Q99/Q143 — the question at that number is a different topic in the current dcf. Tell me the correct current target for each (or the renumbering), and I'll update `SKIP_RULES` in `F1/generate_apc.py` and regenerate.

### (b) Q121 structural — `PROC Q121_DOH_LIC_DIFFICULT`

The generator attaches a `PROC` + dynamic `setvalueset(Q121_DOH_LIC_DIFFICULT, …)` (facility-type-dependent value set, #151) to a **single** item `Q121_DOH_LIC_DIFFICULT`. The current dcf models Q121 as a **multi-select** split into `Q121_DOH_LIC_DIFFICULT_O01…O14` — there is no single container item to attach a PROC or `setvalueset` to. Decision needed: should Q121 be a single-select with a dynamic value set (dcf → one item), or is it genuinely multi-select (generator's dynamic-valueset logic doesn't apply and needs rethinking)? Same pattern likely affects Q65 (`Q65_ACCRED_DIFFICULT_O10` is referenced as the "None" flag).

## Designer-compile runbook

**F3 and F4 are pre-flight-clean and can be compiled now.** Neither has an `.ent` app yet — that's the Designer step.

For each of **F3, F4** (in Designer):
1. New CAPI Data Entry application.
2. Input dictionary = the instrument `.dcf`; form file = the `*.generated.fmf`.
3. Set the main logic file to the instrument `.ent.apc` (it `#include`s `../shared/Capture-Helpers.apc` + `PSGC-Cascade.apc` — keep the relative paths).
4. **Compile** (F7 / build). Pre-flight says symbol resolution is clean; the compile will additionally catch syntax/type issues the static check can't.
5. Run in **CSEntry** and walk the flow. F4's **roster + Section-N expenditure** loop is the riskiest untested part (occurrence/count logic).
6. Report any compile/runtime error back; if it's a name/code mismatch, I fix the generator table and regenerate (never the `.apc`).

For **F1**: resolve the §"F1 reconciliation" items first (give me the answers, I regenerate to pre-flight-clean), **then** compile via the same steps (F1 already has its `.ent`).

## Re-running the check

After any generator edit + regenerate:
```
python deliverables/CSPro/preflight_validate.py
```
Exit 0 = every PROC target resolves. F3/F4 are at exit 0 now; F1 reaches exit 0 once the reconciliation items are applied.
