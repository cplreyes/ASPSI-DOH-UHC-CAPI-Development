---
title: "05 — Phase 7: Testing"
category: deliverable
tags: [capi, cspro, testing, regression, trace, uhc-y2]
last_updated: 2026-05-08
status: draft
---

# Phase 7 — Testing

> Prove the application correct before any respondent ever touches it.

Phase 7 sits between the Phase 6 build (a CSEntry application that loads and walks the happy path) and the Phase 8 deployment (CSWeb sync, PFF packaging, tablet provisioning). It is the cheapest place in the workflow to find bugs — every defect caught here is a defect that does not surface during pretest, training, or main fieldwork, where the cost-per-bug is one or two orders of magnitude higher.

For UHC Year 2 (F1, F3, F4), Phase 7 is also where we close the **bench-testing integration gap** flagged in the May 6 Working File. Bench-testing was identified as one of three integration gaps; this guide turns it into a concrete, file-backed deliverable per F-series so that "we tested it" becomes a reviewable artefact set rather than a verbal claim.

This guide covers F1 (Facility Head), F3 (Patient — IP/OP), and F4 (Household). The companion deliverable for F2 (Healthcare Worker, PWA self-admin) lives under the PWA testing track and is out of scope here — see [[../F2-PWA/Phase-7-Testing-PWA]] for that track.

---

## 7.1 Phase 7 mental model

Testing for a CAPI instrument is **layered**. A bug surfaces at exactly one layer at a time, and each layer is meant to catch a different class of bug. If you skip a layer, the bugs that layer would have caught roll forward into the next one — usually into pretest, where they cost real enumerator and respondent time.

### The three layers

| Layer | Owner | Catches | Cost-per-bug |
|---|---|---|---|
| **Desk test** | Developer (Carl) | Skip-logic typos, validation tier mismatches, value-set bugs, PROC syntax errors | Minutes |
| **Bench test** | Developer + Tester (Carl + Shan) | Cross-field rules, dynamic value-set branches, roster boundaries, partial-save behaviour | Hours |
| **Pair test** | Domain expert (Paunlagui) | Question-meaning drift, awkward order, "I expected to enter X but couldn't", real-world edge cases | Days (because it requires domain context) |

For UHC Year 2:

- **Carl** runs desk test on each F-series after every dictionary regen.
- **Shan** runs bench test using the mock case set archived in `test-cases/`. Shan is also responsible for replaying the regression set after every regen.
- **Paunlagui** (Survey Manager / methodologist) runs pair test once the app is otherwise green. His feedback loops back through Phase 4 (skip-logic spec) and Phase 5 (dictionary corrections) and triggers a regen.

### Where Phase 7 sits in the lifecycle

```
Phase 5: Spec/dictionary corrections
        |
        v
Phase 6: Application build (.fmf + .apc + value sets + FIELD_CONTROL)
        |
        v
Phase 7: Testing  <--- you are here
        |
        v
Phase 8: Sync, packaging, deployment (CSWeb + PFF + tablets)
        |
        v
Phase 9: Pretest / UAT
```

Phase 7 is also a **loop entry point**: pair test routinely surfaces issues that send work back to Phase 4 (re-spec) → Phase 5 (regenerate dictionary) → Phase 6 (rebuild forms) → Phase 7 (re-test). The discipline that keeps this loop cheap is the **regression-as-data** rule in 7.3 and 7.8 — every test case is an artefact you can replay, not a verbal walkthrough you re-perform.

### Two non-negotiable rules

1. **Test before regen, not after.** Every regression run must be replayable on demand against any new dcf hash. If you can only "test" by walking the app manually, you have no regression coverage.
2. **File-based trace on Android, always.** This is the single highest-leverage lesson from the Khurshid corpus for our deployment context. See 7.5.

---

## 7.2 Desk test — CSEntry Windows walkthrough

The desk test is the **developer's first pass** in CSEntry Windows (not on tablet). Goal: verify that every code path the developer wrote actually does what they intended. This is not a tester's job — Carl runs this himself before handing off to Shan for bench test.

### Order of operations

1. Build / package the .pen via Designer.
2. Open the .pen in **CSEntry Windows**.
3. Walk the cover page (cover sheet items, GPS, interviewer ID, consent capture).
4. Walk the eligibility screen.
5. Walk every section in printed-questionnaire order.
6. After each section, force one HARD validation, one SOFT validation, and one GATE branch toggle.
7. Save partial; close; relaunch; verify resume returns you to the same field.
8. Switch language; verify UI strings translate without truncation; switch back.
9. Complete the interview to the disposition page; confirm AAPOR code lands correctly.

### Per-F-series desk-test checklist

Each line is a single verifiable step. Tick all before handing off to bench.

#### F1 — Facility Head (166 items, 1 respondent per facility)

- [ ] Cover page accepts a valid facility code; rejects an unknown code with HARD errmsg.
- [ ] Government-owned vs private-owned branch routes to correct subsections.
- [ ] UHC IS vs non-UHC IS dynamic value set populates correctly on the dependent items.
- [ ] PSGC cascade: region → province → city/municipality → barangay updates each level when the parent changes.
- [ ] Every Q with `errmsg() + reenter` rejects out-of-range numerics.
- [ ] Every Q with `accept()` warns and allows override on flagged but plausible values.
- [ ] Every GATE display condition hides + reveals correctly when its trigger flips.
- [ ] Every Other-specify alpha field captures text when "Other" is selected and is hidden otherwise.
- [ ] Every "I don't know" / "Refuse" option in a select-all is mutually exclusive with substantive options.
- [ ] Partial save mid-section + resume returns to the saved field with prior answers intact.
- [ ] Language switch (EN ↔ FIL) round-trips without losing entered values.
- [ ] Final disposition page records correct AAPOR code (Complete / Partial / Refusal / Non-contact).

#### F3 — Patient (178 items, 45 OP + 30 IP per facility)

- [ ] Cover page accepts patient ID; rejects duplicate ID at facility level.
- [ ] Inpatient vs Outpatient branch routes correctly. Both branches must walk end-to-end.
- [ ] Boundary case: admission date == discharge date (zero-day stay) accepted with appropriate validation tier.
- [ ] Each diagnosis code value set populates with the correct lookup.
- [ ] Cost / payment items: PhilHealth-covered vs out-of-pocket branch handled at every cost question.
- [ ] HARD: charges total reconciles with subtotals (cross-field rule from Phase 4 spec).
- [ ] SOFT: implausible-but-possible total length-of-stay (e.g. > 30 days) warns.
- [ ] GATE: pediatric-only items hidden when patient age >= 18.
- [ ] Other-specify on every "Other" option captures alpha text.
- [ ] Partial save + resume on both IP and OP branches.

#### F4 — Household (202 items, roster-driven)

- [ ] Roster accepts 1, 5, 10, and 20 members without layout breakage.
- [ ] Roster line items (sex, age, relationship, education, employment) accept all valid values.
- [ ] Eligible-member subset (e.g. Kish-grid selection) populates correctly per roster contents.
- [ ] PhilHealth registered vs not-registered branch routes correctly per member.
- [ ] Health-seeking-behaviour Yes vs No branch routes correctly.
- [ ] HARD: member age >= 0; HoH age >= 15; spouse age >= 15.
- [ ] SOFT: tenure-in-residence > age (warn but allow override, since blended families exist).
- [ ] GATE: post-natal-care items only displayed for women aged 15–49 with a birth in the reference period.
- [ ] Multi-language switch mid-roster does not corrupt roster occurrences.
- [ ] Partial save mid-roster (e.g. after member 3 of expected 7) and resume returns to member 4.

The desk test is **fast** — typically 30 to 60 minutes per F-series once the developer has done it a few times. If it stretches past 90 minutes, you are likely catching the kind of bug bench test is meant to catch and the dictionary needs another pass.

---

## 7.3 Bench test — mock cases (Test-Case-as-Data discipline)

Bench test is the **second pass**, run by Shan with Carl observing. The goal is to walk through a pre-defined set of synthetic cases that exercise **specific dimensions of the instrument** — not the happy path, which desk test already covered, but the boundary, error, and branching paths.

The discipline that makes bench test repeatable is **Test-Case-as-Data**: every mock case is saved as a `.csdb` file. After every dictionary regeneration, the same `.csdb` files are replayed in CSEntry to confirm none of them break. A test case that exists only as "Shan walked through it once" cannot be replayed; a `.csdb` file can.

The F1 reference data file we already have, `sample042126.csdb`, is the seed for this practice — the mock case set below extends that single example into a structured library.

### The mandatory mock case set (per F-series)

Each F-series gets its own `test-cases/` directory containing the cases below. This list is not negotiable; the next dictionary revision must replay all of them green before the regen is signed off.

1. **Youngest eligible** — minimum age, minimum tenure, minimum eligibility flags. Tests lower bounds on every numeric field and the lower edge of every age-gated GATE condition.
2. **Oldest eligible** — maximum age, maximum tenure, maximum values on every bounded item. Tests upper bounds and the upper edge of every age-gated GATE condition.
3. **Refusal at every gate** — one case per gate where the respondent refuses (selects the "Refuse to answer" option). Each case verifies that the disposition code lands correctly downstream and that the refusal does not break a later cross-field rule.
4. **"None of the above" on every multi-select** — verifies the mutual-exclusion rule (selecting "None" clears any other selections, and selecting any other option clears "None").
5. **Every Other-specify path** — for every multi-select with an "Other (specify)" option, one case selects "Other" and confirms the alpha capture field appears, accepts text, and is required.
6. **Max roster size** — F4 only. Household roster at maximum occurrences (20 per project structure). Verifies layout, navigation, and partial save at the upper bound.
7. **Every dynamic value-set branch** — at minimum a representative subset: every region, two provinces per region, two cities per province. The full Cartesian product is impractical; the representative subset is the regression-test budget.
8. **Every cross-field validation triggered** — one case per rule from the Phase 4 [[03-Phase-3-5-Spec-and-Generators]] spec. Each case deliberately violates the rule, then corrects it, then verifies acceptance.
9. **Multi-language switch mid-interview** — start in English, complete two sections, switch to Filipino, complete two more sections, switch back, finish. Verifies UI does not corrupt entered data on switch.
10. **Partial-save + resume** — start a case, complete one section, force-kill the app (or use OnStop with savepartial), relaunch, verify resume lands on the next field with prior answers intact.

### Directory layout

Each F-series gets a `test-cases/` directory under its CSPro deliverable folder. The structure is identical across F1, F3, F4 so Shan can move between them without re-orienting.

```
deliverables/CSPro/F1/
  generate_dcf.py
  F1.dcf
  F1.fmf
  F1.apc
  F1.pen
  test-cases/
    cases/
      01-youngest-eligible.csdb
      02-oldest-eligible.csdb
      03-refusal-at-gate-consent.csdb
      03-refusal-at-gate-eligibility.csdb
      03-refusal-at-gate-ownership.csdb
      04-none-of-the-above-services.csdb
      04-none-of-the-above-equipment.csdb
      05-other-specify-services.csdb
      05-other-specify-payment.csdb
      07-dynamic-vs-region-1.csdb
      07-dynamic-vs-region-2.csdb
      07-dynamic-vs-region-3.csdb
      08-crossfield-tenure-le-age.csdb
      08-crossfield-charges-total.csdb
      09-language-switch-midinterview.csdb
      10-partial-save-and-resume.csdb
    regression-log.md
    regression-replay.bat
    README.md
```

For F3, add a `cases/` subdivision for IP-only and OP-only branches:

```
deliverables/CSPro/F3/test-cases/cases/
  01-youngest-eligible-op.csdb
  01-youngest-eligible-ip.csdb
  02-oldest-eligible-op.csdb
  02-oldest-eligible-ip.csdb
  ...
  06-boundary-admit-equals-discharge.csdb
```

For F4, the max-roster case is the heaviest:

```
deliverables/CSPro/F4/test-cases/cases/
  06-roster-max-20-members.csdb
  06-roster-1-member.csdb
  06-roster-5-members.csdb
  06-roster-10-members.csdb
```

### Regression-replay batch script

The script below is the regression engine. Save as `test-cases/regression-replay.bat`. It opens each `.csdb` in CSEntry, lets the operator (Shan) re-walk the case end-to-end in display mode, and logs the result manually back into `regression-log.md`. A future iteration can swap manual confirmation for an automated CSPro batch-edit pass; for now, eyes-on-screen replay is the cheapest reliable check.

```bash
@echo off
REM regression-replay.bat — replay every mock case for this F-series.
REM Run from the test-cases/ directory.
REM Prereq: CSEntry.exe on PATH (or set CSPRO_BIN to its directory).

setlocal enabledelayedexpansion

if "%CSPRO_BIN%"=="" (
  set "CSENTRY=C:\Program Files (x86)\CSPro 8.0\CSEntry.exe"
) else (
  set "CSENTRY=%CSPRO_BIN%\CSEntry.exe"
)

set "PEN=..\F1.pen"

if not exist "%CSENTRY%" (
  echo [ERROR] CSEntry.exe not found at %CSENTRY%
  echo Set CSPRO_BIN to your CSPro install dir and retry.
  exit /b 1
)

if not exist "%PEN%" (
  echo [ERROR] %PEN% not found. Build the application first.
  exit /b 1
)

echo === Regression replay started %date% %time% ===
echo === Application: %PEN% ===

for %%f in (cases\*.csdb) do (
  echo.
  echo --- Replaying %%f ---
  "%CSENTRY%" "%PEN%" /d "%%f" /m
  if errorlevel 1 (
    echo [FAIL] %%f returned errorlevel %errorlevel%.
  ) else (
    echo [OK]   %%f closed cleanly.
  )
  echo Press any key to continue to next case...
  pause >nul
)

echo.
echo === Regression replay finished %date% %time% ===
echo Update regression-log.md with PASS/FAIL per case.
endlocal
```

The `/d` flag points CSEntry at a specific data file; `/m` opens it in modify mode so the tester can re-walk every screen. After each case, the tester records the outcome in `regression-log.md` (template in 7.8).

### Why save cases at all?

Without saved cases, "regression test" reduces to "walk through the app from memory and try to remember what we did last time". The Phase 7 discipline that prevents that drift is: **a regression case is a `.csdb` file or it does not exist**. Verbal regression is not regression.

This also matches the Phase 7 exit criteria in the [[CAPI-Development-Workflow]] template: "Document test cases as data files so they can be replayed after every revision."

---

## 7.4 Pair test — domain-expert walk-through

Pair test is the **third pass**, run by a questionnaire author or senior methodologist. For UHC Year 2 this is **Paunlagui** (Survey Manager). The desk and bench tests verify that the app does what the developer intended; pair test verifies that what the developer intended is **what the questionnaire actually asks**.

### Procedure

1. Carl and Shan sit alongside Paunlagui at a tablet (CSEntry Android or CSEntry Windows simulating the tablet form factor).
2. Paunlagui walks through the instrument as if he were administering it — reading the questions out, entering answers as if he were the enumerator, navigating sections in real interview order.
3. Carl and Shan **observe and capture** without coaching. The single most useful piece of pair-test data is the moment Paunlagui hesitates, frowns, or asks "wait, am I supposed to…?".
4. After each section, pause for a short debrief: what was confusing, what felt out of order, what answer he wanted to give but couldn't.

### What to capture

The pair-test output is a structured bug list, not free-form notes. Each item gets:

- **Section / item ID** — where the issue surfaced.
- **Class** — `wording` | `skip` | `validation` | `value-set` | `layout` | `meaning-drift`.
- **Severity** — `critical` (blocks correct administration) | `high` (affects data quality) | `medium` (slows enumerator) | `low` (cosmetic).
- **Verbatim** — Paunlagui's exact phrasing where possible. ("This question feels like it should come after Q47, not before" carries more weight than a paraphrase.)
- **Proposed fix** — usually deferred to Phase 4 re-spec, but capture an initial hypothesis.

### The loop back to earlier phases

Pair-test findings trigger a loop:

```
Pair test surfaces a meaning-drift bug
        |
        v
Phase 4: Update [[03-Phase-3-5-Spec-and-Generators]] spec
        |
        v
Phase 5: Regenerate .dcf via generate_dcf.py
        |
        v
Phase 6: Update .fmf / .apc to match new dictionary
        |
        v
Phase 7: Re-run desk test, bench test (regression replay), pair test
```

The regression replay in 7.8 is what makes this loop affordable. Without it, every loop iteration costs another full bench-test pass. With it, the loop cost is bounded: regen → batch script → confirm green → re-pair-test only the affected section.

### Sign-off

A pair test is **closed** when:

- Every critical and high finding has either a fix in flight or an explicit deferral signed off by Paunlagui.
- Every medium / low finding has a triage decision (fix-now / fix-later / won't-fix-with-rationale).
- Paunlagui has signed off in writing (Slack message, email, or a note in `test-cases/pair-test-log.md`).

---

## 7.5 Trace function (Khurshid 2023-09-19) — THE Android rule

This is the highest-leverage technique in this guide. **(Khurshid 2023-09-19)** documents two trace modes; getting the wrong one in production means **silent debugging** on the tablet.

### The CRITICAL Android rule

**Window-based trace output is IGNORED on Android.** CSEntry on the tablet has no Designer trace window to render to. If your app calls `trace(on)` and writes events without a target file, those events go nowhere on the tablet. You will think your trace logic is silent because there are no events; in reality, the events fire and are dropped.

**Solution: file-based trace.** Route trace output to a text file on the tablet's external storage. The file can then be pulled off via USB, sync, or CSWeb file-fetch and inspected on a developer machine.

### Production-grade PROC GLOBAL setup

This block is **paste-ready**. Drop it into `F1.apc` (or F3.apc / F4.apc) at the top of `PROC GLOBAL`. It:

- Detects the runtime OS via `getos()`.
- Routes Android to a file in the CSEntry external folder.
- Routes Windows / desktop to the in-process trace window (still useful during desk test).
- Exposes a `logEvent()` helper so field PROCs do not have to know about the platform branch.

```cspro
PROC GLOBAL

string trace_path;

function setupTrace()
  if getos() = "android" then
    { Android: route to file in external folder so the trace file can be
      pulled off the tablet via USB or CSWeb sync. clear so each launch
      starts fresh; without it, the file grows unbounded. }
    trace_path = pathname(path_type_csentry_external) + "/trace.txt";
    trace(on, trace_path, clear);
  else
    { Windows / desktop: the Designer trace window is fine — and faster
      to read than tailing a file during desk test. }
    trace_path = "";
    trace(on);
  endif;
end;

function logEvent(string event_text)
  trace(event_text);
end;

function logEventF(string template, value v1)
  { Convenience overload — use maketext() for richer messages where you
    need formatted values. }
  trace(maketext(template, v1));
end;
```

Then call `setupTrace()` once in the application preproc:

```cspro
PROC F1_FF

preproc
  setupTrace();
  logEvent("F1 application start; build=2026-05-08");

postproc
  logEvent("F1 application end");
  trace(off);
```

### Where to call `logEvent()`

Use trace events sparingly during normal operation, and densely during diagnostic builds. Suggested instrumentation points:

- **Section transitions** — `logEvent("entering section S2 (services)")` at section preproc.
- **Validation triggers** — `logEvent(maketext("HARD failed: Q42 entered=%d, range=0..99", $))` inside the `errmsg` branch.
- **Sync attempts** — at the start, success, and failure of any CSWeb or Bluetooth sync call.
- **Eligibility decisions** — when the eligibility logic concludes Eligible / Ineligible / Refused.
- **Roster construction (F4)** — once per member added to the roster; once when the eligible-respondent subset is computed.
- **Dynamic value-set switches** — `logEvent(maketext("PSGC cascade: region=%d -> %d provinces", region_code, province_count))`.

### Diagnostic vs production builds

Treat trace as a **build-time toggle**:

- **Diagnostic build** — `trace(on, ...)` in setupTrace, dense `logEvent()` calls. Used for pretest, UAT, and field-issue investigation.
- **Production build** — replace `trace(on)` with `trace(off)` (or short-circuit setupTrace) once UAT is signed off and main fieldwork begins. Trace I/O on a tablet does have a measurable cost when called on every keypress; silencing it for production keeps the app responsive.

### Pulling the trace file off the tablet

Three paths, ordered by friction:

1. **USB** — connect tablet, navigate to `Android/data/<csentry-package>/files/`, copy `trace.txt`.
2. **CSWeb file-fetch** — if CSWeb is configured to fetch arbitrary files alongside the data dictionary.
3. **Manual share** — have the enumerator email the file to a developer address (rare; only when no other path is available).

The trace file is a debugging artefact, not a deliverable. Do **not** include it in the closeout dataset; it contains intermediate state that is not part of the published codebook.

### Gotchas

- **Without `clear`, the file grows unbounded across launches.** A multi-week pretest with no clear flag produces a multi-megabyte file by the end of week one. Use `clear` so each app launch starts fresh.
- **Trace in roster preproc loops fires per occurrence.** A 20-member F4 household with three trace calls per member writes 60 lines per case. That is fine for diagnostic builds; expensive for production.
- **`trace(off)` does not delete the file.** It stops writing. The previous contents remain until the next launch with `clear`.

---

## 7.6 Save-array viewer for runtime inspection (Khurshid 2022-12-16)

When a complex value set or sample-file lookup populates wrong, the question is "what is actually in the array at runtime?". The Designer debugger answers this question for scalar variables; for arrays, the answer comes from **save-arrays** **(Khurshid 2022-12-16)**.

### The mechanic

Add the `save` keyword to an array declaration in `PROC GLOBAL`. After the application runs, CSPro writes the array contents to a `<application>.sva` file next to the application. The file is plain text — open it in any text editor, or in CSPro's text viewer.

```cspro
PROC GLOBAL

{ Static lookup, initialised at declaration → 1-indexed in the viewer. }
array save psgc_region_codes(17, 2) numeric = (
   01, 100,    { Region I, expected province count 100 — placeholder }
   02, 200,
   { ... }
);

{ Runtime-built, populated in PROC → 0-indexed in the viewer.
  Press Ctrl+0 in the viewer to "Show zero indices". }
array save eligible_members(20, 5) numeric;

{ Runtime-built buffer for the F4 Kish-style respondent selection. Each
  row holds one eligible member; columns are pid / age / sex /
  relationship / kish_rank. }
```

### Constraints

- **`save` arrays can only be declared in PROC GLOBAL.** Local-scope save arrays are not allowed.
- **All `save` arrays in the application share one .sva file.** You cannot route different arrays to different files.
- **Indexing rules differ by initialisation style.** Declaration-time-initialised arrays show 1-indexed in the viewer; PROC-initialised arrays show 0-indexed and require Ctrl+0 to display the row 0 / col 0 cells.

### A UHC use case — F4 eligible-member selection

F4 needs to compute the eligible respondent for each household after the roster is collected. The selection logic builds an in-memory array of eligible members (ages 15–65, resident status = current resident, not a domestic helper), then applies a Kish-grid rank.

A bug in the selection logic is hard to debug from forms alone — you only see the final selected respondent, not the candidate list that produced them. With a save-array, the candidate list is dumped to `F4.sva` after every run:

```cspro
PROC GLOBAL

{ Up to 20 candidates × 5 cols (pid, age, sex, relationship, kish_rank). }
array save eligible_members(20, 5) numeric;

PROC HOUSEHOLD_ROSTER

postproc
  numeric ix = 0;
  do MEMBER_NUM = 1 while MEMBER_NUM <= roster_count
    if member_age(MEMBER_NUM) >= 15 and member_age(MEMBER_NUM) <= 65 and
       member_resident(MEMBER_NUM) = 1 and
       member_relationship(MEMBER_NUM) <> 14 then
      ix = ix + 1;
      eligible_members(ix, 1) = MEMBER_NUM;
      eligible_members(ix, 2) = member_age(MEMBER_NUM);
      eligible_members(ix, 3) = member_sex(MEMBER_NUM);
      eligible_members(ix, 4) = member_relationship(MEMBER_NUM);
      eligible_members(ix, 5) = 0;  { kish_rank assigned in next pass }
    endif;
  enddo;
```

After a test run, open `F4.sva` and inspect:

```
eligible_members
Row 0: 0 0 0 0 0          <- press Ctrl+0 to see this row in the viewer
Row 1: 1 42 2 1 1          <- pid=1, age=42, sex=female, rel=head, kish_rank=1
Row 2: 2 38 1 2 2          <- pid=2, age=38, sex=male, rel=spouse, kish_rank=2
Row 3: 4 16 1 3 3          <- pid=4, age=16, sex=male, rel=child, kish_rank=3
Row 4: 0 0 0 0 0
...
```

If the wrong respondent is selected, the .sva tells you whether the bug is in the eligibility filter (wrong rows in the array) or in the Kish rank computation (right rows, wrong rank).

### When to use it during Phase 7

- Anywhere the bench test reveals "the right answer didn't come out" but you cannot tell if the input array was wrong or the algorithm was wrong.
- During pair test, when Paunlagui flags an unexpected respondent selection in F4.
- During PSGC cascade debugging, when a region → province lookup returns the wrong subset.

---

## 7.7 Audit imputations with stat() (Khurshid 2022-12-31)

This section is mostly Phase 10 / 11 territory but worth flagging during testing because the **test for hot-deck or imputation logic is "did the `stat()` call land in the audit file with the correct fields"** **(Khurshid 2022-12-31)**.

### The pattern

Hot-deck imputation cleans implausible values during batch editing — for example, age values that fall outside the plausible range for a household head's relationship and sex. The `impute()` function pulls a plausible value from a save-array seeded with valid recent observations; the `stat()` function writes a row to a side data file recording the imputation.

```cspro
PROC GLOBAL

{ Hot-deck array seeded at declaration, refreshed in PROC. }
array save age_hotdeck(2, 6) numeric = (
   45, 38, 20, 18, 22, 30,    { initial male ages by relationship }
   40, 35, 18, 16, 20, 28     { initial female ages by relationship }
);

PROC AGE
  if RELATIONSHIP = 1 and SEX = 1 then
    if $ <= 10 then
      errmsg("Implausible male HoH age %d for case %s, imputing", $, key(MAIN_DICT));
      impute($, age_hotdeck(SEX, RELATIONSHIP));
      stat("AGE_IMPUTED", key(MAIN_DICT), $);
    else
      age_hotdeck(SEX, RELATIONSHIP) = $;
    endif;
  endif;
```

### What to test in Phase 7

For every hot-deck rule in the batch-edit application:

- Construct a synthetic case that triggers the rule (e.g. a male HoH aged 5).
- Run the batch-edit application.
- Open the stat file (configured in the CSBatch run-config dialog).
- Verify the row was written with the right rule name (`AGE_IMPUTED`), the right case key, and the right imputed value.

If the row is missing, either the trigger condition didn't fire (logic bug) or the `stat()` call was omitted (audit-trail bug). Both are blockers for closeout.

### Why this matters during testing

The closeout codebook is required to declare every imputation rule and the volume of imputations applied. That declaration is built from the stat file. **A missing or incorrect stat file means the codebook cannot be produced**, which blocks the closeout deliverable. Catching this in Phase 7 — by running the batch-edit application against a small synthetic dataset and verifying the stat-file output — is at least an order of magnitude cheaper than catching it during Phase 11.

---

## 7.8 Regression test discipline

This is the operational rule that ties 7.3, 7.5, and 7.6 together. **Every dictionary regeneration triggers a full regression replay.** No exceptions.

### The regression workflow

1. **Edit the spec.** Phase 4 [[03-Phase-3-5-Spec-and-Generators]] markdown gets updated with the new rule, item, or correction.
2. **Regenerate.** `python F1/generate_dcf.py` (or F3 / F4). Confirm the .dcf opens cleanly in Designer.
3. **Build the .pen.** Designer → Build → Production.
4. **Compute dcf hash.** `certutil -hashfile F1.dcf SHA256` on Windows. The hash is what makes a regression result auditable — "passed against dcf hash X" is verifiable; "passed last Tuesday" is not.
5. **Open .pen in CSEntry Windows.**
6. **Run regression-replay.bat.** Walk every `.csdb` in `test-cases/cases/` under operator control. For each case, confirm:
   - No unexpected HARD errmsg.
   - No unexpected SOFT accept warning.
   - Every previously-answered field still displays its prior value.
   - The case can be navigated end-to-end without crash.
7. **Record outcomes in `regression-log.md`** (template below). One row per case per regen.
8. **If any case fails:** investigate, fix the spec / generator / forms, regen, replay only the affected cases (and any that share machinery with the affected case).
9. **Sign off the regen** by appending a summary line to the log: `dcf SHA256: <hash> — REGRESSION PASS — <date> <time> — <tester>`.

### regression-log.md template

Save as `test-cases/regression-log.md`. Append one block per regen.

```markdown
# F1 Regression Log

Each block is one dictionary regeneration. Append, never edit history.

---

## Regen 2026-05-08T14:30+08:00

- **Trigger**: Phase 4 spec update — added Q47 cross-field rule (charges total ≥ subtotals).
- **Generator commit**: (n/a — manual log; record git hash if used)
- **dcf SHA256**: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- **.pen build**: F1.pen 2026-05-08 14:25
- **Replayed by**: Shan
- **CSEntry version**: 8.0.6
- **Platform**: Windows 11

| Case | Result | Notes |
|---|---|---|
| 01-youngest-eligible | PASS | |
| 02-oldest-eligible | PASS | |
| 03-refusal-at-gate-consent | PASS | |
| 03-refusal-at-gate-eligibility | PASS | |
| 03-refusal-at-gate-ownership | PASS | |
| 04-none-of-the-above-services | PASS | |
| 04-none-of-the-above-equipment | PASS | |
| 05-other-specify-services | PASS | |
| 05-other-specify-payment | PASS | |
| 07-dynamic-vs-region-1 | PASS | |
| 07-dynamic-vs-region-2 | PASS | |
| 07-dynamic-vs-region-3 | PASS | |
| 08-crossfield-tenure-le-age | PASS | |
| 08-crossfield-charges-total | **NEW — PASS** | First case for the new Q47 rule. |
| 09-language-switch-midinterview | PASS | |
| 10-partial-save-and-resume | PASS | |

**Summary**: 16/16 PASS. Sign-off: Shan, 14:58.

---
```

### Why a hash, not a version number?

A version number relies on developer discipline to bump on every change. A SHA256 of the .dcf file changes whenever the dictionary changes, even if someone forgets to bump. The hash is the ground-truth identifier. When a future Phase 11 audit asks "which build of F1 did regression-pass on 2026-05-08?", the answer is the hash, and the hash is reproducible from the .dcf file in the artefact set.

### Cadence

- **After every regen** — full replay. Non-negotiable.
- **Weekly during pretest / UAT** — full replay even with no regen, to catch tablet-drift issues.
- **Before any production deploy** — full replay against the exact .pen that will go to tablets.

---

## 7.9 Test plan per F-series

Different F-series have different shape; the test plan adapts.

### F1 — Facility Head

- **Items**: 166.
- **Respondents**: 1 per facility (the head of facility or designate).
- **Happy path**: 1 facility (e.g. a Bulacan provincial-level public hospital).
- **Major branches**:
  - Government-owned vs private-owned.
  - UHC IS vs non-UHC IS.
  - Service-list dynamic value sets (services offered varies by facility level).

**Mock case priorities**:

- Public provincial UHC IS facility — happy path.
- Public city primary-care facility (smaller service list).
- Private hospital (different ownership branch).
- Refusal at consent (full case = refusal disposition).
- Partial completion (half the sections, save partial, resume the next day).

### F3 — Patient

- **Items**: 178.
- **Respondents**: 45 outpatient + 30 inpatient per facility.
- **Major split**: Inpatient vs Outpatient — separate sections, separate cost calculations, separate length-of-stay logic.
- **Boundary cases**:
  - Admit-day = discharge-day (zero-day stay) — must walk both branches and confirm length-of-stay = 0 or 1 per spec.
  - Pediatric inpatient (age < 18) — pediatric-only items must display.
  - PhilHealth-only payment vs out-of-pocket only vs mixed — three cases.
  - Maximum length-of-stay (> 30 days) — SOFT warn; case completes.

**Mock case priorities**:

- Max-OP case — long visit list (e.g. multiple consultations, lab, pharmacy).
- Max-IP case — long stay, multiple procedures, mixed payment.
- Boundary admit-equals-discharge.
- Pediatric IP case.
- Refusal at consent.

### F4 — Household

- **Items**: 202.
- **Respondents**: 1 designated respondent per household, with a roster covering all members.
- **Major dimensions**:
  - Roster size: 1 / 5 / 10 / 20 members.
  - PhilHealth registered (per member) vs not.
  - Health-seeking-behaviour Yes vs No (per member).
  - Eligible-respondent selection (Kish-grid style).

**Mock case priorities**:

- Single-person household (roster = 1).
- Typical 5-member household (HoH + spouse + 3 children).
- Extended 10-member household (multi-generational).
- Maximum 20-member household.
- All-PhilHealth-registered household.
- No-PhilHealth-registered household (mostly informal-sector).
- Mixed registration.
- Refusal at consent.
- Partial completion mid-roster (resume).

The 20-member roster case is the heaviest test in the entire UHC suite — it exercises layout, navigation, partial save, save-array eligibility computation, and Kish selection all at once. It is the case most likely to surface tablet-specific layout bugs and the case Shan should run first on the actual tablet.

---

## 7.10 Cross-platform smoke

Even though F1 / F3 / F4 are tablet-bound for production, smoke-test on **three environments** during Phase 7:

### CSEntry Windows (developer environment)

- **Purpose**: fast iteration. Desk test and bench test live here.
- **What to verify**: every functional path. This is the bulk of Phase 7 work.
- **Limitation**: trace-window output works here, masking the Android trace-file rule (7.5) if you only test on Windows.

### CSEntry Android on the actual provisioned tablet model

- **Purpose**: catch tablet-specific rendering, performance, and trace-routing issues.
- **What to verify**:
  - File-based trace produces a `trace.txt` in the expected external folder.
  - Roster grids render at full 20 members without horizontal-scroll surprises.
  - Long question text wraps cleanly at the screen width of the provisioned tablet (10-inch landscape vs 8-inch portrait will look different).
  - Multi-language switching does not corrupt entered values.
  - Battery / suspend cycle: leave the app in the background for 30 minutes, reopen, verify state preserved.
- **Cadence**: at least once per regen. Once per day during pretest.
- **Critical**: the **same** tablet model that will be deployed. Do not smoke-test on a different model and assume parity.

### CSWeb sync round-trip

- **Purpose**: confirm the data path from tablet to server works for at least one case.
- **What to verify**:
  - Tablet sync uploads a completed case.
  - Server receives the case and the dictionary recognises every field.
  - Round-trip download to a developer machine produces a readable .dat file.
- **Detail**: this is mostly Phase 8 territory ([[06-Phase-8-CSWeb-and-Tablets]]) but a single round-trip during Phase 7 catches the worst surprises early — wrong dictionary on the server, schema drift between tablet and server, authentication failure.

### Smoke checklist

- [ ] One full case on CSEntry Windows.
- [ ] One full case on the actual tablet.
- [ ] One sync round-trip Windows → CSWeb → developer download.
- [ ] Trace file pulled from tablet and inspected.

---

## 7.11 Bench-testing as a deliverable

Per the **May 6 Working File** integration gap audit, bench-testing was identified as one of three integration gaps (alongside translation pipeline and cross-instrument data harmonisation). Phase 7 closes this gap by producing a concrete artefact set per F-series. This section is the closeout instruction for that audit finding.

### What gets delivered

For **each of F1, F3, F4**, produce a `test-cases/` directory containing:

```
deliverables/CSPro/{F1|F3|F4}/test-cases/
  cases/                       <- .csdb files, one per mock case from 7.3
  regression-log.md            <- regen log per template in 7.8
  regression-replay.bat        <- batch script per 7.3
  pair-test-log.md             <- Paunlagui's findings per 7.4
  README.md                    <- index of cases, purpose of each
```

### test-cases/README.md template

```markdown
# F1 Test Cases

This directory holds the regression test bed for F1 (Facility Head).
Every case is a `.csdb` file replayable in CSEntry against `F1.pen`.

## Cases

| File | Purpose | Triggers |
|---|---|---|
| 01-youngest-eligible.csdb | Lower-bound numerics, lower-edge GATE conditions. | Min age, min tenure. |
| 02-oldest-eligible.csdb | Upper-bound numerics, upper-edge GATE conditions. | Max age, max tenure. |
| 03-refusal-at-gate-consent.csdb | Refusal at the consent gate; verify disposition code. | Q1 = Refuse. |
| 03-refusal-at-gate-eligibility.csdb | Refusal mid-screen at eligibility. | Q5 = Refuse. |
| 03-refusal-at-gate-ownership.csdb | Refusal at ownership question. | Q12 = Refuse. |
| 04-none-of-the-above-services.csdb | "None of the above" exclusivity in services multi-select. | Q31 = NOTA. |
| 04-none-of-the-above-equipment.csdb | "None of the above" exclusivity in equipment multi-select. | Q44 = NOTA. |
| 05-other-specify-services.csdb | Other-specify alpha capture in services. | Q31 = Other + text. |
| 05-other-specify-payment.csdb | Other-specify alpha capture in payment methods. | Q58 = Other + text. |
| 07-dynamic-vs-region-1.csdb | PSGC cascade for Region 1. | Region = 01. |
| 07-dynamic-vs-region-2.csdb | PSGC cascade for Region 7. | Region = 07. |
| 07-dynamic-vs-region-3.csdb | PSGC cascade for ARMM. | Region = 14. |
| 08-crossfield-tenure-le-age.csdb | Tenure ≤ age − 15 cross-field rule. | Q3 = 22, Q4 = 8 (warn). |
| 08-crossfield-charges-total.csdb | Charges total = sum of subtotals. | Q47 reconciliation. |
| 09-language-switch-midinterview.csdb | EN ↔ FIL switch mid-interview. | Manual switch at section 3. |
| 10-partial-save-and-resume.csdb | OnStop savepartial, relaunch, resume. | Killed at section 4. |

## How to run regression

```bash
cd deliverables/CSPro/F1/test-cases
.\regression-replay.bat
```

## How to add a case

1. Open `F1.pen` in CSEntry Windows.
2. Walk the case end-to-end with the values that exercise the new rule.
3. Save the case under `cases/NN-short-name.csdb` (NN = next sequence number).
4. Append a row to the table above.
5. Append the case to the next regression-log.md block.
```

### Why this is a deliverable, not a workflow note

A workflow note can drift; a directory of `.csdb` files cannot. The May 6 audit finding closes when the three directories exist with their contents. The Phase 7 exit criteria below ties off this closure.

---

## 7.12 Phase 7 exit criteria

Phase 7 is **closed** when **all** of the following are true. Until they are all true, do not proceed to Phase 8.

- [ ] Every skip path traversed at least once in CSEntry Windows desk test.
- [ ] Every HARD validation triggered + cleared.
- [ ] Every SOFT validation triggered + overridden.
- [ ] Every GATE condition exercised in both visible and hidden states.
- [ ] Every Other-specify path verified to capture alpha text.
- [ ] Every "None of the above" multi-select verified for mutual exclusion.
- [ ] Every dynamic value-set branch exercised (PSGC cascade especially).
- [ ] Every cross-field validation rule from the Phase 4 spec triggered with a case in `test-cases/cases/`.
- [ ] Mock cases archived in `deliverables/CSPro/{F1,F3,F4}/test-cases/cases/`.
- [ ] `regression-log.md` shows a green replay against the latest .dcf hash.
- [ ] `regression-replay.bat` works when run by Shan with no developer present.
- [ ] Pair-test sign-off recorded in `pair-test-log.md` from Paunlagui (or designate).
- [ ] File-based trace verified working on the actual provisioned tablet — `trace.txt` pulled, inspected, and contains expected events for at least one full case.
- [ ] One CSWeb sync round-trip completed end-to-end.
- [ ] Cross-platform smoke checklist (7.10) complete.
- [ ] No critical or high open bugs.

When every box is checked, Phase 7 is signed off. The artefact set under `test-cases/` is now the **regression bed** for the rest of the engagement. Every Phase 9 pretest fix, every Phase 10 hot-fix, and every Phase 11 closeout edit must replay the regression set green before being deployed.

---

## Cross-references

- [[03-Phase-3-5-Spec-and-Generators]] — generator + dcf-hash discipline (Phase 3), every cross-field rule (Phase 4), and the regen workflow that triggers regression replay (Phase 5).
- [[04-Phase-6-Build-CAPI-App]] — the .fmf / .apc artefacts that 7.5 instruments with trace and 7.6 with save-arrays.
- [[06-Phase-8-CSWeb-and-Tablets]] — sync, packaging, deployment.
- [[../../IT-Standards/templates/CAPI-Development-Workflow]] — workflow template, Phase 7 section.
- **(Khurshid 2023-09-19)** — Tutorial on Trace Function. Source: [[../../../3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/2023-09-19_tutorial-on-trace-function_LtjiYZosfJg/techniques]].
- **(Khurshid 2022-12-16)** — Tutorial on View Array in the Save Array Viewer. Source: [[../../../3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/2022-12-16_tutorial-on-view-array-in-the-save-array-viewer_t7kcEDpGJms/techniques]].
- **(Khurshid 2022-12-31)** — Tutorial on Initialize Hot Decks Using Save Arrays. Source: [[../../../3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/2022-12-31_tutorial-on-initialize-hot-decks-using-save-arrays_1TCAWb4iwd4/techniques]].

---

Next: [[06-Phase-8-CSWeb-and-Tablets]]
