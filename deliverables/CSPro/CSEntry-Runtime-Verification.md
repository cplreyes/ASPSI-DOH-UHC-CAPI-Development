# CSEntry Runtime Verification Pass

**Purpose:** verify the generated CAPI logic actually *runs* in CSEntry — not just
that CSPro Designer says "Compile Successful" (which is **untrustworthy**: Designer
can report success while compiling a stale/empty in-memory app, masking real errors).
CSEntry recompiles the `.ent.apc` text on every launch and is the ground truth.

**Status (2026-06-09):** Stage 0 PASS for F1/F3/F4 after fixing a `protect()` bug
that Designer had masked (61 errors in F4). Stages 1–2 are the field-behaviour pass.

---

## Stage 0 — Compile gate (automated, run after EVERY generator change)

```
py deliverables/CSPro/automation/csentry_verify.py            # all three
py deliverables/CSPro/automation/csentry_verify.py F4         # one
```

For each instrument it deletes any stale `<base>.ent.err`, launches CSEntry on the
desktest `.pff` (CSEntry auto-compiles), then reports **PASS** (no `.err`, entry
started) or **FAIL** (prints `<base>.ent.err` — the file/field/line/message to fix
in the generator). Exit 0 = all pass.

> **Do NOT use `cspro_compile_driver.py` (Designer Ctrl+K) as the gate.** It gave
> false "Compile Successful" for an entire session. It's fine for *opening* an app
> to eyeball forms, not for verifying logic. The oracle is `csentry_verify.py` /
> `.ent.err`.

**Current result:** F1 PASS · F3 PASS · F4 PASS.

---

## Stage 1 — Case-key persistence (the critical data-integrity check)

The blank-case-key bug (empty vestigial record) is fixed, but re-verify after any
dcf/fmf change because a blank key collides every case on CSWeb sync.

**Drive (stepwise, vision-read each shot at `automation/shots/csentry.png`):**
```
py automation/csentry_drive.py launch ../F4/HouseholdSurvey_desktest.pff
py automation/csentry_drive.py type 1        # REGION_CODE   (auto-advances on fill)
py automation/csentry_drive.py type 3        # PROVINCE_HUC_CODE
py automation/csentry_drive.py type 007      # CITY_MUNICIPALITY_CODE
py automation/csentry_drive.py type 02       # FACILITY_NO
py automation/csentry_drive.py type 009      # CASE_SEQ
... (complete the case to save) ...
```
**Expected:** key fields turn green; on save the case key = the 12-digit composite
(here `010300702009`). **Verify in the .csdb, not just "it saved":**
```
py - <<'PY'
import sqlite3; c=sqlite3.connect(r'F4/desktest.csdb')
print(c.execute("select key from cases").fetchall())
PY
```
`cases.key` must be the 12 digits (not 12 spaces) and `level-1` ids non-null.
Known-good keys already verified: F3 `010200304005`, F4 `010300702009`, F1 `070800906005`.

---

## Stage 2 — Validation & skip spot-checks (the new logic layer)

Drive to the target field and confirm the rule fires. HARD rules block + reenter;
SOFT rules show a dismissable warning (HTML modal — dismiss by **coordinate click**
~`(1180,575)` scaled, NOT Enter, because `htmlDialogs:True` renders in Chromium).

| # | Instrument · field | Enter | Expect |
|---|---|---|---|
| R1 | F3 `Q58_WAIT_DAYS` | `400` | HARD reject "must be between 0 and 365" |
| R2 | F3 `Q69_USUAL_TRAVEL_MM` | `75` | HARD reject "0 and 59" |
| R3 | F3 `Q92_PAY_01`=Yes then `Q92_PAY_01_AMT` | `0` | HARD reject "enter its amount (> 0)" |
| R4 | F4 `Q18_INCOME_AMOUNT`=`5000`, `Q18_INCOME_BRACKET`=`4` | — | HARD "bracket does not match amount" |
| R5 | F4 `TOTAL_NUMBER_OF_VISITS` | `15` | HARD reject "1 and 10" |
| S1 | F3 `Q143_RECOMMEND`=Yes, `Q144_QUALITY`=`5` | — | SOFT warn (recommend vs dissatisfied) |
| S2 | F3 `Q84_SERVICE_TYPE`=`2` w/ `PATIENT_TYPE`=Outpatient | — | SOFT warn routing mismatch |
| S3 | F4 `Q19_HH_SIZE_TOTAL` | `12` | SOFT "unusually large" |
| K1 | F3 `Q53_HAS_PCP`=No | — | skips Q54–Q62 (cursor lands past them) |
| K2 | F4 `Q62_PURCHASE_FREQ`=Never(5) | — | skips Rx/where/travel block |
| N1 | F4 Section N (after a panel's items) | amounts | subtotal field auto-fills + is read-only (`protect`) |

(Full per-rule list: `Desk-Test-Scenario-Matrix.md`. Deep sections G/H/J/K require
traversing most of the form — budget for an interactive sitting or the Android pass.)

---

## Notes / gotchas (carried from 2026-06-08–09)

- Numeric fields **auto-advance on fill** — type digits with NO trailing `{ENTER}`.
- A trailing `{ENTER}` lands on the next empty field → spurious "out of range" (88889).
- SOFT warnings = `errmsg` without `reenter`; HARD = `errmsg` + `reenter`.
- HTML modals (Chromium) → dismiss by coordinate click, not keyboard.
- `.pff` `[Parameters] Language=WAR` forces the start language for translation checks.
- After any generator edit: **Stage 0 first**, then re-drive only the affected scenarios.
