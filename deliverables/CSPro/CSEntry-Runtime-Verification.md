# CSEntry Runtime Verification Pass

**Purpose:** verify the generated CAPI logic actually *runs* in CSEntry — not just
that CSPro Designer says "Compile Successful" (which is **untrustworthy**: Designer
can report success while compiling a stale/empty in-memory app, masking real errors).
CSEntry recompiles the `.ent.apc` text on every launch and is the ground truth.

**Status (2026-06-09):** Stage 0 PASS for F1/F3/F4 after fixing a `protect()` bug
that Designer had masked (61 errors in F4). **Stage 1 PASS on F4** — case key
`010300702015` entered + saved via consent=No→`endlevel`; verified in the `.csdb`
(`cases.key`='010300702015', 12 chars; `level-1` ids 1/3/7/2/15, non-null).
**Stage 2 (partial):** driving toward Q18 surfaced + fixed a critical runtime blocker —
the PSGC geo cascade was dead in every desktest (the pff lacked an `[ExternalFiles]`
section, so `loadcase` had no PSGC data → -27 "region lookup failed"). After adding
`[ExternalFiles]` to all desktest pffs, the **full 4-level cascade works live** (drove
Region III → Bulacan → Malolos → Anilao). The GPS + photo capture forms were then made
desktop-skippable (getos guard in `Capture-Helpers.apc`). **Stage 2 first spot-check
PASS:** `scenarios/f4_q18_bracket.txt` now drives end-to-end to Q18 and the **amount↔bracket
HARD reject fires at runtime** — amount 5000 + bracket 4 → msg -419 "Income bracket does
not match the reported amount" (evidence: `shots/f4_q18_bracket/062_*.png`).
`scenarios/f4_range_and_soft.txt` then verified the other two mechanisms at Q19:
**HARD range reject** (Q19=25>20 → msg -366 "must be 1-20" + reenter — same shape as
`range_check_proc`, e.g. F3 Q58) and **SOFT warn** (Q19=12>10 → msg -370 "unusually
large", dismissable — same `errmsg`-w/o-`reenter` as the soft cross-checks). All three
validation kinds (range, cross-field-hard, soft-warn) are runtime-verified.
NOTE: Q58 + the cross-field soft checks are F3-specific (Section E / B,F,J — ~120-field
traversal). They use these identical generators and compile clean (gate PASS); their
F3-instrument runtime traversal is an optional future scenario, not yet built.

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

## Scriptable scenarios (`csentry_runner.py`)

For repeatable deep-form checks, author a scenario file and run it:
```
py automation/csentry_runner.py scenarios/<name>.txt          # auto-kills CSEntry
py automation/csentry_runner.py scenarios/<name>.txt --keep    # leave it open
```
It drives CSEntry in one process and saves a NUMBERED screenshot after every step to
`shots/<name>/` (review the trail to confirm the validation fired) plus `run.log`.
DSL: `rmdata` / `launch` / `casekey` / `type` / `key` / `click` / `wait` / `shot` / `note`.
It force-foregrounds CSEntry before every keystroke and **aborts rather than type if it
can't** (so keystrokes never leak into the wrong window). See `scenarios/f4_q18_bracket.txt`.

> **Capture fields are now desktop-skippable (2026-06-09).** After the geo cascade,
> F4 hits `CAPTURE_HH_GPS` (GPS) then `CAPTURE_VERIFICATION_PHOTO` (camera) — both need
> device hardware absent on desktop. FIXED in `shared/Capture-Helpers.apc`: the shared
> `ReadGPSReading` / `TakeVerificationPhoto` helpers now guard on **`if getos() in 10:19`**
> (Windows) → return 0 silently (no `gps(open)`/camera call → **no `-118` / camera modal**).
> Android (`getos() in 20:29`) captures normally — production unchanged. Verified: a
> Windows CSEntry run no longer raises the GPS-hardware modal. Applies to F1/F3/F4 (shared).
> NB the six GPS *data* fields (Lat/Long/Alt/Accuracy/Sat/ReadTime) + the filename field
> are still normal enterable fields (no hardware), so a scenario still tabs through them.

## Notes / gotchas (carried from 2026-06-08–09)

- **PSGC geo cascade needs `[ExternalFiles]` in the pff** (else -27 "region lookup failed").
  Each desktest pff must declare the 4 PSGC data files by dictionary name:
  `[ExternalFiles]` / `PSGC_REGION_DICT=.\..\shared\psgc_region.dat` (+ province/city/barangay).
  Without it, `loadcase` returns 0 and the whole survey body past field-control is unreachable.
  Done for F1/F3/F4 desktest + F3 WAR pffs (2026-06-09).
- **Case-key fields use full zero-padded widths** so they auto-advance cleanly (e.g. REGION_CODE
  `01` not `1`); a single digit in a 2-wide field doesn't advance and a stray `{ENTER}` then
  trips the 88889 nuisance on the next field.
- No-valueset numeric fields (FACILITY_NO, PARENT_F3_CASE_SEQ) **warn 88889 on empty `{ENTER}`** —
  type a value instead of Entering through them.
- CSEntry opens to the **case listing** when the `.csdb` already has cases (not straight to Add);
  point the pff at a fresh/empty `.csdb` to start in Add mode directly.
- Numeric fields **auto-advance on fill** — type digits with NO trailing `{ENTER}`.
- A trailing `{ENTER}` lands on the next empty field → spurious "out of range" (88889).
- SOFT warnings = `errmsg` without `reenter`; HARD = `errmsg` + `reenter`.
- HTML modals (Chromium) → dismiss by coordinate click, not keyboard.
- `.pff` `[Parameters] Language=WAR` forces the start language for translation checks.
- After any generator edit: **Stage 0 first**, then re-drive only the affected scenarios.
