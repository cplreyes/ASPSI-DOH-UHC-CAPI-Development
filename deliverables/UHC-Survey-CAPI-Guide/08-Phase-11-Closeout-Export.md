---
title: "08 — Phase 11: Closeout and Export"
category: deliverable
tags: [capi, cspro, export, stata, spss, closeout, archive, uhc-y2]
last_updated: 2026-05-08
status: draft
---

# Phase 11 — Closeout and Export

> Wrap the engagement with a clean, auditable artifact set. Three deliverables: final datasets, final documentation, lessons learned.

Phase 11 closes the UHC Year 2 engagement. The clock starts when fieldwork ends and the last case syncs from the last tablet. From that moment forward, no new data should arrive on the CSWeb server; the only operations on the database are extract, transform, archive. This guide covers F1 (Facility Head), F3 (Patient — IP/OP), and F4 (Household). The companion F2 PWA closeout lives under [[../F2-PWA/Phase-11-Closeout-PWA]] and is out of scope here.

For UHC Year 2 the contract end window is **November–December 2026**. Annex I dummy tables (51 specs) drive the analysis plan, and the CHE methodology described in Annex A is what the final dataset must support. That means the closeout deliverable set has to be analyst-ready in **Stata first, SPSS second, Excel third**, with a CSPro `.dat` snapshot retained as the canonical native format and a PDF codebook accompanying every export.

This guide is built on the workflow template ([[../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow]] Phase 11) and on Khurshid's closeout/export technique cards. Cross-refs to earlier phases use Obsidian wikilinks: [[02-Phase-0-2-Foundation]], [[05-Phase-7-Testing]], the Phase 8/10 entries when published.

---

## 11.1 Phase 11 mental model

Closeout is a **gate, not a sprint**. The engagement does not end when fieldwork ends; it ends when every reusable artifact has been harvested, every dataset has been exported in every contracted format, every credential has been revoked, and the lessons-learned row has been committed to the workflow template.

Three deliverable streams run in parallel through Phase 11:

1. **Final datasets** — one canonical CSPro `.dat`, one Stata `.dta` set, one SPSS `.sav` set, one Excel `.xlsx` set, per F-series. All exported from the same authoritative `.csdb` so the row counts reconcile across formats.
2. **Final documentation** — data dictionary (human-readable), codebook (per-variable detail), edit specifications, application source, generator source, field manuals, issue log, hot-fix log.
3. **Lessons learned** — one row in the workflow-template log table. Captures what the engagement taught that future CAPI engagements should reuse.

The **first principle** of closeout is that nothing in the deliverable bundle should require Carl's tribal knowledge to interpret. A reviewer six months from now should be able to open the codebook, the dictionary, the edit spec, and the data file, and reproduce the analysis. If a deliverable requires explanation that lives only in Carl's head, it is not closeout-ready.

The **second principle** is that closeout produces **reusable assets** for the next CAPI engagement. The PSGC cascade, the capture helpers, the validators, the hot-deck batch app, the Stata post-processing do-file — all of these should leave UHC and land in `2_Areas/IT-Standards/templates/` or the shared CAPI library. The engagement should make every subsequent engagement faster.

The **third principle** is that audit trail is non-negotiable. Every imputation gets logged. Every variable has provenance back to the questionnaire. Every value label has a documented source. The deliverable bundle is for the record, not for the convenience of the analyst.

### Where Phase 11 sits in the lifecycle

```
Phase 10: Production fieldwork support (sync monitoring, hot-fix protocol, batch QC)
        |
        v   <-- last case syncs
Phase 11: Closeout and Export   <--- you are here
        |
        |   - Final dataset export (Stata, SPSS, Excel, CSPro .dat)
        |   - Final documentation (codebook, dictionary, edit specs)
        |   - Final tagging (release tags on .pen, generator, export pipelines)
        |   - Decommission (Slack archive, credential revocation, server freeze)
        |   - Lessons-learned entry (workflow template log)
        |   - Reusable artifact harvest
        |
        v
Project moves from 1_Projects/ to 4_Archives/ (PARA convention)
```

### What "done" looks like

Closeout is done when **every item in [[#11.13 Phase 11 exit criteria]] is checked**. Not "mostly done", not "client signed off so we can wrap up later". The exit-criteria list is the contract between the engagement and the next engagement that will reuse UHC's artifacts.

---

## 11.2 Final dataset export — three formats minimum

The workflow template (Phase 11 line 330) calls for delivering in multiple formats. UHC Year 2's analysis plan implies the following minimum set per F-series:

| Format | Extension | Audience | Tooling |
|---|---|---|---|
| **CSPro native** | `.dat` + `.dcf` | Future re-runs in CSPro; canonical reference | CSPro Tools → Export Data, format = CSPro |
| **Stata** | `.dta` | ASPSI/DOH primary analysis | CSPro Tools → Export Data, format = STATA |
| **SPSS** | `.sav` | DOH alternate analysis | CSPro Tools → Export Data, format = SPSS |
| **Excel** | `.xlsx` | Client review; dummy-tables population | CSPro batch-edit application **(Khurshid 2023-09-28)** |
| **Codebook** | `.pdf` | Human-readable reference | Generated from `.dcf` via Python utility |

The Stata pipeline gets its own subsection (§11.3) because it is the most operationally heavy: it is automated through Task Scheduler during the closeout window so analysts wake up to fresh exports. SPSS and Excel pipelines (§11.4, §11.5) are simpler — they run on demand after fieldwork closes.

### Reconciliation rule

Every format export, for every F-series, must reconcile on **case count, record count, and variable count** against the canonical `.csdb`. A mismatch in any cell of that 3×N matrix (where N = formats) is a closeout-blocker. Document the reconciliation in `EXPORT-RECONCILIATION.md` next to the final exports.

```
F-series | .csdb cases | .dat cases | .dta cases | .sav cases | .xlsx cases | OK?
F1       | 1234        | 1234       | 1234       | 1234       | 1234        | yes
F3       | 4567        | 4567       | 4567       | 4567       | 4567        | yes
F4       | 2345        | 2345       | 2345       | 2345       | 2345        | yes
```

If `.xlsx` cases lag because of multi-record flattening, document the expected delta and re-reconcile per record level.

### Naming convention for the deliverable bundle

```
deliverables/
  UHC-Y2-Final-Datasets/
    F1/
      F1-final-v1.0.0.csdb         { canonical CSPro DB }
      F1-final-v1.0.0.dat          { CSPro flat export }
      F1-final-v1.0.0.dcf          { dictionary }
      F1-final-v1.0.0_stata/
        F1-facility.dta
        F1-roster.dta
      F1-final-v1.0.0_spss/
        F1-facility.sav
        F1-roster.sav
      F1-final-v1.0.0.xlsx
      F1-codebook-v1.0.0.pdf
      EXPORT-RECONCILIATION.md
    F3/
      ... (same shape)
    F4/
      ... (same shape)
```

The `vX.Y.Z` suffix matches the release tag (§11.9). If a post-fieldwork correction is required (e.g. a labeling fix discovered during analysis), bump to `v1.0.1` and re-export the full bundle for that F-series. Never edit a final file in place.

---

## 11.3 Stata export pipeline (Khurshid 2022-05-12)

Khurshid's *Use the Batch File to Download the Data from the CSWeb Server* video **(Khurshid 2022-05-12)** describes a three-step pipeline: build a Stata-export PFF, wrap it in a batch file, schedule it via Task Scheduler. The pipeline runs **weekly during fieldwork** (per the Section 10.1 monitoring rhythm) and **daily during the last 2 weeks of fieldwork** to prep closeout. After fieldwork ends, it runs once more on the final `.csdb` to produce the deliverable Stata files.

### Step 1 — Generate the Stata-export PFF via Tools → Export Data

Per **(Khurshid 2022-05-12)**, the export PFF is built through the CSPro IDE rather than written by hand:

1. **CSPro → Tools → Export Data** → select the F-series dictionary (e.g. `F1.dcf`).
2. **Output options**: choose **Multiple files** (one file per record level) and **As separate record** for multi-record handling. Khurshid: *"'Multiple files / As separate record' is what flattens nested records into joinable STATA tables."*
3. **Format**: STATA.
4. Save the export specification as `F1-export-stata.exf`.
5. CSPro generates a paired `.pff` (the runnable specification).

A paste-ready PFF — F1 example, adapt path/dictionary names per F-series:

```
[Run Information]
Version=CSPro 7.7.1
ApplicationType=ExportData

[Files]
ExportSpecification=C:\UHC-Y2\closeout\F1\F1-export-stata.exf
InputData=C:\UHC-Y2\closeout\F1\F1-final.csdb
OutputData=C:\UHC-Y2\closeout\F1\F1-final-v1.0.0_stata\F1.dta

[Parameters]
Silent=yes
```

**Gotcha** **(Khurshid 2022-05-12)**: Single-file output puts everything in one wide row, which usually isn't what analysts want. Always use Multiple files / As separate record for UHC since F1 and F4 both have rosters.

For F3 (single-respondent patient), single-file output is acceptable but multi-file output is still preferred for consistency with F1/F4.

### Step 2 — Wrap PFF execution in a Windows batch file

Per **(Khurshid 2022-05-12)**, the batch wrapper is four lines. Khurshid's literal pattern (changing two levels up, then asserting drive, then absolute path):

```bat
cd ..\..
c:
cd c:\wamp64\www
F1-export-stata.pff
```

For UHC Year 2, the production wrapper combines a sync (download from CSWeb) and a Stata export so the analyst's local copy is fresh on every run:

```bat
@echo off
REM ============================================================
REM UHC Y2 — F1 nightly Stata export
REM 1. Pull latest cases from CSWeb
REM 2. Export to Stata
REM ============================================================

c:
cd C:\UHC-Y2\closeout\F1

REM --- Step 1: download the latest data from CSWeb ---
F1-download.pff
if errorlevel 1 (
    echo [%date% %time%] CSWeb sync FAILED >> C:\UHC-Y2\closeout\logs\F1-export.log
    exit /b 1
)

REM --- Step 2: export to Stata ---
F1-export-stata.pff
if errorlevel 1 (
    echo [%date% %time%] Stata export FAILED >> C:\UHC-Y2\closeout\logs\F1-export.log
    exit /b 1
)

echo [%date% %time%] F1 nightly export OK >> C:\UHC-Y2\closeout\logs\F1-export.log
exit /b 0
```

**Khurshid's gotcha** **(Khurshid 2022-05-12)**: *"Drive letter (c:) must be on its own line before the cd to absolute path; otherwise Windows just changes directory on whichever drive is current. Test interactively before scheduling."* Run the batch file by double-click first; only schedule it after it succeeds interactively.

Save as `C:\UHC-Y2\closeout\F1\F1-export-nightly.bat`. Repeat for F3 and F4 (substituting names) so each F-series has its own batch file. Do **not** combine them into one batch — when one fails, the remaining ones should still run.

### Step 3 — Schedule unattended sync + export with Task Scheduler

Per **(Khurshid 2022-05-12)**, Task Scheduler invokes the batch file on a daily trigger. Khurshid's example pattern: *"Download at 1:30 AM, export at 1:31 AM, so analysts wake up to fresh STATA files."*

UHC Year 2 schedule (closeout window):

| Task name | Trigger | Action |
|---|---|---|
| `UHC-Y2-F1-export-nightly` | Daily at 02:00 | Run `F1-export-nightly.bat` |
| `UHC-Y2-F3-export-nightly` | Daily at 02:30 | Run `F3-export-nightly.bat` |
| `UHC-Y2-F4-export-nightly` | Daily at 03:00 | Run `F4-export-nightly.bat` |

GUI registration via **Task Scheduler → Task Scheduler Library → Create Task**:
- **General** tab: name = `UHC-Y2-F1-export-nightly`; run with highest privileges; configured for Windows 10/11.
- **Triggers**: New → Daily → start 02:00, recur every 1 day.
- **Actions**: New → Start a program → Program/script = `C:\UHC-Y2\closeout\F1\F1-export-nightly.bat`. Leave Add arguments blank.
- **Conditions**: uncheck "Start the task only if the computer is on AC power" if running on a workstation that may be on battery (rare for CAPI ops machines, but check).
- **Settings**: allow task to be run on demand; if the task fails, restart every 1 minute, attempt up to 3 times.

Paste-ready PowerShell registration (preferred — version-controllable):

```powershell
$action = New-ScheduledTaskAction `
    -Execute "C:\UHC-Y2\closeout\F1\F1-export-nightly.bat"

$trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At "02:00"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERNAME" `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName "UHC-Y2-F1-export-nightly" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "UHC Y2 F1 nightly Stata export — built per Khurshid 2022-05-12"
```

Equivalent Task Scheduler XML (for reference / audit):

```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>UHC Y2 F1 nightly Stata export — built per Khurshid 2022-05-12</Description>
    <URI>\UHC-Y2-F1-export-nightly</URI>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-11-01T02:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Settings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
    <StartWhenAvailable>true</StartWhenAvailable>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
  </Settings>
  <Actions>
    <Exec>
      <Command>C:\UHC-Y2\closeout\F1\F1-export-nightly.bat</Command>
    </Exec>
  </Actions>
</Task>
```

Save as `F1-export-nightly.xml` and import via:

```powershell
Register-ScheduledTask `
    -Xml (Get-Content "C:\UHC-Y2\closeout\F1\F1-export-nightly.xml" -Raw) `
    -TaskName "UHC-Y2-F1-export-nightly"
```

**Khurshid's gotcha** **(Khurshid 2022-05-12)**: *"If the download takes more than the gap between tasks, the export will run on stale data. Either set a longer gap or chain the export inside the same batch file (download.pff then export.pff on consecutive lines)."* The UHC schedule above chains both inside a single batch file per F-series, sidestepping the gap problem entirely.

### Cadence

- **During fieldwork** (~Sep–Nov 2026): weekly Stata export (Sundays at 02:00) for the Phase 10 monitoring rhythm.
- **Last 2 weeks of fieldwork**: daily Stata export to prep closeout — analysts can see the dataset taking final shape.
- **Closeout window** (post-fieldwork): one-time final Stata export per F-series on the frozen `.csdb`, tagged `v1.0.0`. Disable the scheduled task once the final export ships.

---

## 11.4 SPSS export pipeline

SPSS export is operationally simpler than Stata because the deliverable does not need automation — it ships once at closeout. Same three-format philosophy, but one-shot.

### Step 1 — CSPro Tools → Export Data → SPSS .sav

Same dialog as Stata, format = **SPSS**. Multiple files / As separate record. Save as `F1-export-spss.exf` and the paired `.pff`. Run via the IDE or via the same batch-wrapper pattern as Stata if you prefer command-line consistency.

```
[Run Information]
Version=CSPro 7.7.1
ApplicationType=ExportData

[Files]
ExportSpecification=C:\UHC-Y2\closeout\F1\F1-export-spss.exf
InputData=C:\UHC-Y2\closeout\F1\F1-final.csdb
OutputData=C:\UHC-Y2\closeout\F1\F1-final-v1.0.0_spss\F1.sav

[Parameters]
Silent=yes
```

CSPro emits a `.sav` per record level with numeric codes and value labels already attached from the dictionary's value sets. **In most cases this is sufficient** — the rest of this section is needed only when CSPro emitted some variables as strings (e.g. "Other (specify)" alpha fields, or any variable whose value-set was incomplete) and the analysis plan needs them as labeled numerics.

### Step 2 — SPSS post-processing: auto-recode strings to labeled numerics

Per **(Khurshid 2023-01-21)** *Auto Recode in SPSS*: the SPSS equivalent of Stata's `encode`. Converts a string variable into a labeled numeric variable, assigning numeric codes alphabetically by source string. Frequencies are preserved.

GUI: **Transform → Automatic Recode** → select string variable → enter new name → **Add new name** → OK.

Syntax form (paste-ready):

```spss
* Auto-recode every "Other (specify)" string field to a labeled numeric.
* Substitute the actual variable names from F1 dictionary.

AUTORECODE VARIABLES = q05_other q11_other q22_other
   /INTO q05_other_n q11_other_n q22_other_n
   /PRINT.
EXECUTE.
```

**Khurshid's gotcha** **(Khurshid 2023-01-21)**: *"The alphabetical default ordering may not match a desired code scheme. For deterministic ordering, build a value-labels syntax block manually instead of relying on auto-recode."* For UHC, only auto-recode "Other (specify)" fields where the alphabetical order doesn't matter for analysis. For any field the analyst will use as a categorical predictor, build the value labels manually.

### Step 3 — SPSS post-processing: value labels and missing values

Per **(Khurshid 2023-03-20)** *Adding value labels and handling missing data in SPSS*:

```spss
* --------------------------------------------------------------
* UHC Y2 — F1 SPSS post-processing
* Value labels + missing values for closeout deliverable
* --------------------------------------------------------------

* --- Value labels for sex variable (representative pattern) ---
VALUE LABELS sex
   1 'Male'
   2 'Female'.
EXECUTE.

* --- Multi-variable form: slash-separated, period at end ---
VALUE LABELS marital_status
   1 'Single / never married'
   2 'Married'
   3 'Widowed'
   4 'Divorced / separated'
   9 'Refused'
   /facility_type
   1 'Hospital'
   2 'Rural Health Unit'
   3 'Barangay Health Station'
   4 'Private clinic'
   5 'Other'
   /q19_response
   1 'Yes'
   2 'No'
   8 "Don't know"
   9 'Refused'.
EXECUTE.

* --- Missing values: discrete codes ---
MISSING VALUES q19_response (8 9).

* --- Missing values: range plus discrete code ---
MISSING VALUES age (98 THRU 99, 999).

* --- Missing values for string variable ---
MISSING VALUES q05_other ('NR' 'DK').
EXECUTE.
```

**Khurshid's gotchas** **(Khurshid 2023-03-20)**:
- *"End the multi-variable form with one period at the end of all blocks, not after each variable. Each variable starts with a /."*
- *"Empty data fields or fields with invalid entries in numeric data are converted to system missing which is identified by a single period."* — system-missing (the `.`) is automatic; user-defined missing values you set with `MISSING VALUES` are on top of that. Both are excluded from analysis.

**Demonstrated impact** **(Khurshid 2023-03-20)**: before declaring `999` as missing on age, the mean was 248.58 (skewed by 999 codes). After setting `999` as missing, the mean dropped to 46.54 (the real population mean). **Always declare missing values before publishing any descriptive statistics.**

For UHC: assemble the per-F-series value-labels syntax block from the dictionary value sets (regenerate it from the `.dcf` via Python rather than typing it by hand — same generator-over-hand-edit principle as the rest of the workflow). Save as `F1-spss-postprocess.sps`, `F3-spss-postprocess.sps`, `F4-spss-postprocess.sps` next to the exports.

---

## 11.5 Excel export pipeline (Khurshid 2023-09-28)

Per **(Khurshid 2023-09-28)** *Tutorial on: Applying Batch Application for Data Export with or without labels*: the **batch-edit application as a controlled data exporter** to Excel. More flexible than Tools → Export Data because the batch app can include cleaning logic, conditional row filtering, and computed columns alongside the export.

### Step 1 — Create the batch-edit application

**File → New → Batch Edit Application** → name + folder → choose dictionary → save. For UHC: one batch app per F-series, named `F1-export-excel.bch`, `F3-export-excel.bch`, `F4-export-excel.bch`.

The batch-edit application does **not** need any PROC logic for a pure-export use case — the export behavior is controlled entirely by the run-time attribute string. Save the empty `.bch` and proceed to Step 2.

### Step 2 — Configure the run dialog with attribute string

Per **(Khurshid 2023-09-28)**: in the Run dialog, **input data** = your `.csdb` or `.dat`; **source type** = `excel`; **output data** = path for the `.xlsx`. **Then comes the attribute string** — appended after the output file path with a pipe separator.

Three key attributes documented:
- `values=codes` — output numeric codes only.
- `values=labels` — output value-set labels only.
- `values=codes--labels` — output **both** in adjacent columns.
- `m%attribute_name=record=person` — restrict export to the named record only.
- `m%attribute_name=header=names` — header row uses item names (uppercase).
- `m%attribute_name=header=labels` — header row uses item labels.
- `m%attribute_name=header=names--labels` — header row uses **both** in two adjacent rows.

**Khurshid's note** **(Khurshid 2023-09-28)**: *"It is important to note that the attributes order does not matter here, but make sure to use the M% symbol to separate attributes."*

### Step 3 — Production-grade paste-ready batch app for F1

**Two output configurations** ship for each F-series:

**(a) Codebook-friendly** — codes only, item names as header. For analysts who will write their own labeling.

```
C:\UHC-Y2\closeout\F1\F1-final-v1.0.0_codes.xlsx|values=codes|m%attribute_name=header=names
```

**(b) Analysis-friendly** — codes and labels in adjacent columns, names and labels in adjacent header rows. For client review and dummy-tables population.

```
C:\UHC-Y2\closeout\F1\F1-final-v1.0.0_full.xlsx|values=codes--labels|m%attribute_name=header=names--labels
```

Wrap the run in a PFF for repeatable closeout runs:

```
[Run Information]
Version=CSPro 7.7.1
ApplicationType=BatchEdit

[Files]
Application=C:\UHC-Y2\closeout\F1\F1-export-excel.bch
InputData=C:\UHC-Y2\closeout\F1\F1-final.csdb
OutputData=C:\UHC-Y2\closeout\F1\F1-final-v1.0.0_full.xlsx|values=codes--labels|m%attribute_name=header=names--labels

[Parameters]
Silent=yes
```

**Khurshid's gotcha** **(Khurshid 2023-09-28)**: *"Same syntax works for both CSDB and DAT inputs — `source type = text` for DAT, `csdb` for CSDB. The pipe-separated attribute string is finicky; one typo and the export silently degrades to defaults."* Always open the output `.xlsx` after a run and confirm: header row(s) are what you expect, codes/labels columns are paired, no silent fallback to defaults.

For UHC: the analysis-friendly `_full.xlsx` is what the dummy-tables population step (the 51 Annex I specs) consumes. The codebook-friendly `_codes.xlsx` is what the codebook PDF generator references for variable-name verification.

### Per-record export (large rosters)

F1 and F4 both have rosters that flatten to thousands of rows when exported all-records. For roster-only exports (e.g. F4 person-roster for household composition analysis), restrict to the single record with the per-record attribute:

```
C:\UHC-Y2\closeout\F4\F4-roster-v1.0.0.xlsx|values=codes--labels|m%attribute_name=record=person|m%attribute_name=header=names--labels
```

Document the per-record exports in `EXPORT-RECONCILIATION.md` so reviewers know which sheet contains which record level.

---

## 11.6 Stata post-processing patterns (Khurshid corpus)

Once the `.dta` files exist, the next step is to make them analyst-ready. Five patterns from the Khurshid corpus close the gap between "CSPro emitted Stata files" and "an analyst can run a regression":

1. `encode` — convert string variables to labeled numerics.
2. `frames` — keep multiple datasets in memory simultaneously and link them.
3. `frlink` / `frval` / `frget` — cross-frame variable access.
4. `rename _all` + `lower` — bulk variable-name case standardization.
5. Multi-language datasets via `label language` + `label define`.

### 11.6.1 encode — string to labeled numeric

Per **(Khurshid 2023-03-14)** *How to use encode in STATA — Urdu Language* (and the English equivalent referenced in 2023-03-15): converts a string-typed variable into a numeric variable with **value labels** preserving the original string text. Same use case as SPSS auto-recode (§11.4).

```stata
encode <string_var>, gen(<new_numeric_var>)
```

After this, `<new_numeric_var>` holds 1, 2, 3, … and `tabulate` shows the original string as the label.

**Khurshid's note** **(Khurshid 2023-03-14)**: *"Both the frequencies are the same"* — encoded categorical vs original string produces identical frequency counts.

For UHC: drop the original string after confirming the encoded version is correct, so the dataset doesn't carry redundant data.

```stata
encode marital_status_str, gen(marital_status)
drop marital_status_str
```

### 11.6.2 frames — multiple datasets in memory

Per **(Khurshid 2023-02-25)** *Working with Multiple Datasets in Memory*: Stata's `frame` system keeps multiple datasets in memory at the same time, switches between them, and links them — analogous to multiple SQL tables open at once. **Solves the problem where opening a new file normally closes the current one.**

For UHC the killer use case is opening F1 (facility), F3 (patient — IP/OP), and F4 (household) **simultaneously** and linking them via shared case ID for cross-instrument analysis (e.g. "patient experiences (F3) crossed with the facility-level capacity score from F1").

```stata
* Open F4 (household) into the default frame
use "F4-final-v1.0.0.dta", clear
frame rename default fr_f4_household

* Create a frame for F3 (patient)
frame create fr_f3_patient
frame change fr_f3_patient
use "F3-final-v1.0.0.dta", clear

* Create a frame for F1 (facility)
frame create fr_f1_facility
frame change fr_f1_facility
use "F1-final-v1.0.0.dta", clear

* Switch back to F4 for analysis
frame change fr_f4_household
```

**Khurshid's note** **(Khurshid 2023-02-25)**: *"A frame and data file are two different entities. When we say frame name we call `fr_person` and we say data person the name is used."* The frame is the in-memory container; the data file is the on-disk source.

Per **(Khurshid 2023-03-15)** *Use Frame Dir in STATA — English*: list all frames currently in memory.

```stata
frames dir
* Output columns: name | # vars | # obs | filename
```

Useful for debugging "why isn't `frval` finding the variable?" — usually because the frame isn't loaded.

### 11.6.3 frlink / frval / frget — cross-frame access

Per **(Khurshid 2023-02-25)** continued: `frlink` establishes a many-to-one link between frames based on shared ID variables (foreign-key relationship without merging). `frval()` references a value from the linked frame inline (lazy). `frget` copies a variable from the linked frame into the current frame (materialized).

For UHC the link variable is the **12-digit case ID** (PSGC + facility/household sequence + person sequence). Adopt the case-ID convention as a standard so all three F-series can be linked transparently.

```stata
* While in fr_f4_household, link to fr_f1_facility (m:1, many households per facility)
frame change fr_f4_household
frlink m:1 case_id_facility, frame(fr_f1_facility)

* Inline reference: read facility_type from the linked frame
gen facility_type = frval(fr_f1_facility, facility_type)

* Or materialize: copy facility_score into the current frame
frget facility_score, from(fr_f1_facility)
```

**Khurshid's gotcha** **(Khurshid 2023-02-25)**: *"ID variable names + types must match exactly in both frames; mismatched types (numeric vs string) produce silent unmatched rows."* The 12-digit case ID is a **string** in CSPro (it has leading zeros for PSGC); cast consistently before `frlink` or unmatched rows appear silent.

```stata
* Defensive: confirm types before linking
describe case_id_facility
frame fr_f1_facility: describe case_id_facility
* If types differ, cast both to string
tostring case_id_facility, replace force format(%012.0f)
frame fr_f1_facility: tostring case_id_facility, replace force format(%012.0f)
```

**Khurshid's note** **(Khurshid 2023-02-25)** on `frval` vs `frget`: *"frval recalculates on each access (lazy); frget materializes once. Pick frget if the analysis will reference the variable in many subsequent commands — Stata is faster on materialized columns."*

### 11.6.4 rename _all — bulk case standardization

Per **(Khurshid 2023-02-17)** *Using rename and varcase change the variable case to upper / lower*: standardize variable case across an entire dataset using `rename _all`.

For UHC: variable names from CSPro come out **uppercase** (e.g. `Q05_PROVINCE`, `R_AGE`); standardize to lowercase before merging with F2 PWA exports (which come out from Apps Script with mixed case). Lowercase is the conventional Stata norm.

```stata
rename _all, lower
```

**Khurshid's gotcha** **(Khurshid 2023-02-17)** on `varcase`: *"When using varcase, lowercase variables will become uppercase and uppercase variables will become lowercase."* If you have mixed-case input, the result is unstable. **Use `rename _all` for any deterministic case conversion**; reserve `varcase` for the rare toggle use case.

### 11.6.5 Multi-language datasets

Stata supports multiple **label languages** on a single dataset. The pattern: label the dataset in English first, then `label language` to a new language identifier, redefine the labels in Filipino, switch back as needed. UHC contractual requirement: deliver labeled datasets in **English + Filipino**.

```stata
* --- Default: English labels ---
label language en, new
label define yesno_en 1 "Yes" 2 "No" 8 "Don't know" 9 "Refused"
label values q19_response yesno_en
label variable q19_response "Q19: Has the facility experienced a stockout in the past 30 days?"

* --- Add Filipino labels ---
label language fl, new
label define yesno_fl 1 "Oo" 2 "Hindi" 8 "Hindi alam" 9 "Tumanggi sumagot"
label values q19_response yesno_fl
label variable q19_response "Q19: Nakaranas ba ang pasilidad ng stockout sa nakaraang 30 araw?"

* --- Switch language ---
label language en      // back to English
tab q19_response
label language fl      // Filipino
tab q19_response
```

The same `.dta` file now answers both audiences. Persist via `save F1-final-v1.0.0.dta, replace`.

For UHC: regenerate the value-labels syntax from the dictionary value sets (one helper per language). Same generator-over-hand-edit principle: do not maintain a 600-line `do` file by hand when the dictionary already encodes everything you need.

### 11.6.6 Paste-ready Stata do-file (UHC closeout merge)

End-to-end pattern: opens F1, F3, F4 in three frames, links F4 (household) to F3 (patient) via case ID and F4 to F1 (facility) via facility ID, standardizes variable names to lowercase, applies value labels in English, exports a merged analysis dataset.

```stata
* ============================================================
* UHC Y2 — Closeout merge do-file
* Author: Carl Patrick Reyes
* Built per Khurshid corpus (2023-02-17, 2023-02-25, 2023-03-14, 2023-03-15)
* ============================================================

clear all
set more off
cd "C:\UHC-Y2\closeout"

* --- 1. Open F4 (household) into the default frame ---
use "F4\F4-final-v1.0.0_stata\F4.dta", clear
frame rename default fr_f4_household

* --- 2. Open F3 (patient) into a new frame ---
frame create fr_f3_patient
frame change fr_f3_patient
use "F3\F3-final-v1.0.0_stata\F3.dta", clear

* --- 3. Open F1 (facility) into a new frame ---
frame create fr_f1_facility
frame change fr_f1_facility
use "F1\F1-final-v1.0.0_stata\F1.dta", clear

* --- 4. Confirm all three are loaded ---
frames dir

* --- 5. Standardize variable names to lowercase across all frames ---
frame fr_f4_household:  rename _all, lower
frame fr_f3_patient:    rename _all, lower
frame fr_f1_facility:   rename _all, lower

* --- 6. Cast case IDs to string with leading-zero format ---
frame fr_f4_household:  tostring case_id_facility case_id_household, replace force format(%012.0f)
frame fr_f3_patient:    tostring case_id_facility case_id_household, replace force format(%012.0f)
frame fr_f1_facility:   tostring case_id_facility, replace force format(%012.0f)

* --- 7. Encode any string categoricals (one example shown) ---
frame fr_f4_household:  encode marital_status_str, gen(marital_status)
frame fr_f4_household:  drop marital_status_str

* --- 8. Apply English value labels (regenerated from dictionary) ---
frame fr_f4_household {
    label language en, new
    do "labels\F4-labels-en.do"
}
frame fr_f3_patient {
    label language en, new
    do "labels\F3-labels-en.do"
}
frame fr_f1_facility {
    label language en, new
    do "labels\F1-labels-en.do"
}

* --- 9. Link F4 (household) to F1 (facility) via facility case ID ---
frame change fr_f4_household
frlink m:1 case_id_facility, frame(fr_f1_facility)

* --- 10. Materialize selected facility-level variables onto F4 ---
frget facility_type facility_score province_psgc, from(fr_f1_facility)

* --- 11. Link F3 (patient) to F4 (household) via household case ID ---
frame change fr_f3_patient
frlink m:1 case_id_household, frame(fr_f4_household)

* --- 12. Materialize selected household-level variables onto F3 ---
frget hh_size poverty_index facility_score, from(fr_f4_household)

* --- 13. Save the merged analysis dataset ---
frame change fr_f3_patient
save "merged\UHC-Y2-F3-with-F4-and-F1-context-v1.0.0.dta", replace

* --- 14. Done ---
display "Closeout merge complete. Three frames loaded; merged F3 dataset saved."
frames dir
```

Save as `closeout-merge.do`. Run via `do closeout-merge.do` from the closeout directory. The do-file is a **harvest candidate** for §11.12 — generic enough to ship to the next CAPI engagement.

---

## 11.7 Hot-deck imputation for missing data (Khurshid 2022-12-31)

Per **(Khurshid 2022-12-31)** *Tutorial on Initialize Hot Decks Using Save Arrays*: a **statistical edit method** for cleaning implausible/missing values by imputing from a "hot deck" — a save-array storing recent valid values by demographic stratum. When a bad value is detected, `impute()` pulls a plausible value from the matching bucket; when a valid value is observed, it refreshes the bucket. **Aligns with the UN Handbook on Population and Housing Census Edits** guidance.

For UHC: the F4 expenditure block likely has missing values (households often refuse or don't know individual line items). Hot-deck imputation by demographic strata before final export is the closeout-grade fix. The audit trail is mandatory — every imputation gets logged to a `stat()` side data file.

### 11.7.1 Implement as a batch-edit application

Hot-deck imputation is a **batch-edit** application (not a data-entry app). **File → New → Batch Edit Application** → name `F4-hotdeck-impute.bch` → choose F4 dictionary → save.

PROC GLOBAL initializes the save-array. PROC on the target item runs the impute logic per case.

```cspro
PROC GLOBAL
{ Initialize hot deck for monthly out-of-pocket health expenditure (F4) by:
    rows = income quintile (1..5)
    cols = household size bucket (1, 2, 3-4, 5-6, 7+) -> 5 columns
  Initial values are sensible national medians; arrays refresh as valid cases stream through. }
array save oop_hotdeck(5, 5) numeric = (
    100, 200, 350, 500,  800,    { Q1 income, by HH size bucket }
    150, 300, 500, 700, 1100,    { Q2 }
    200, 400, 700, 950, 1500,    { Q3 }
    300, 600,1000,1400, 2200,    { Q4 }
    500,1000,1700,2400, 3700     { Q5 }
);

PROC OOP_MONTHLY
numeric income_q, hh_bucket;
income_q  = INCOME_QUINTILE;
hh_bucket = recode(HH_SIZE,
                   1 => 1,
                   2 => 2,
                   3:4 => 3,
                   5:6 => 4,
                   7:high => 5);

if $ = notappl or $ = 9999998 or $ = 9999999 then
   { missing or refused -> impute }
   errmsg("OOP missing for case %s (Q=%d, HHbucket=%d), imputing", key(MAIN_DICT), income_q, hh_bucket);
   impute($, oop_hotdeck(income_q, hh_bucket));
   stat("OOP_IMPUTED", key(MAIN_DICT), $);
else
   { valid value -> refresh hot deck }
   oop_hotdeck(income_q, hh_bucket) = $;
endif;
```

The `impute()` function assigns a value from the hot-deck array to the data item. The `stat()` call writes a row to a side data file recording each imputation for audit.

**Khurshid's gotcha** **(Khurshid 2022-12-31)**: *"Hot-deck imputation is a statistical edit method; document every imputation rule and review the rate before publication. For a more detailed explanation of what hot-decks are, refer to the United Nations Handbook on Population and Housing Census Edits."*

### 11.7.2 Audit imputations with stat() into a side data file

Per **(Khurshid 2022-12-31)** continued: `stat()` writes per-case audit rows to a "stat file" whenever an imputation occurs. After the run, that file contains one row per imputation: `rule_name | case_key | new_value`.

```cspro
stat("OOP_IMPUTED", key(MAIN_DICT), $);
```

Then in the batch-edit run dialog, configure the **stat file name** in the run-config form. After the run, that file contains one row per imputation.

**Khurshid's gotcha** **(Khurshid 2022-12-31)**: *"Without stat() calls in your edit logic, you have no audit trail and reviewers cannot reproduce or trust the cleaned dataset."* The **audit-trail rule for UHC**: every imputation gets logged. No silent imputation is acceptable in a closeout deliverable.

### 11.7.3 Run from CSBatch with the run-config dialog

Per **(Khurshid 2022-12-31)**: click **Run** in CSBatch. The dialog has rows for:

1. **Input data file** — `F4-final-pre-impute.csdb` (the original, potentially dirty CSPro DB).
2. **Output data file** — `F4-final-post-impute.csdb` (where cleaned cases land).
3. **Stat file** — `F4-impute-audit.dat` (pre-populated by default; tracks imputations).
4. **Array file** — `F4-hotdeck-state.sva` (persists hot-deck state across runs).

Click OK. The console shows file names + run timestamp + a summary block (records read, cases, error messages issued) + per-case process messages.

**Khurshid's gotcha** **(Khurshid 2022-12-31)**: *"Keep input + output as separate files — running with input == output overwrites your source data and removes the ability to re-run with different rules."*

### 11.7.4 PFF for repeatable imputation runs

```
[Run Information]
Version=CSPro 7.7.1
ApplicationType=BatchEdit

[Files]
Application=C:\UHC-Y2\closeout\F4\F4-hotdeck-impute.bch
InputData=C:\UHC-Y2\closeout\F4\F4-final-pre-impute.csdb
OutputData=C:\UHC-Y2\closeout\F4\F4-final-post-impute.csdb
StatFile=C:\UHC-Y2\closeout\F4\F4-impute-audit.dat
ArrayFile=C:\UHC-Y2\closeout\F4\F4-hotdeck-state.sva

[Parameters]
Silent=yes
```

### 11.7.5 Imputation rate review

Before publication, review the imputation rate per rule:

```
Rule           | Cases imputed | Total cases | Rate
OOP_IMPUTED    | 234           | 2345        | 9.98%
```

If the rate exceeds a pre-defined threshold (e.g. 15% for any single rule), pause and review. High imputation rates are a **methodological flag** — they indicate either a systematically bad question (re-design for next year) or a data-collection problem (debrief the field team) or a hot-deck cell that lacks initial seed values (re-tune the array).

Document the per-rule rate in `F4-impute-audit-summary.md` next to the audit file.

### 11.7.6 What gets imputed for UHC

Run hot-deck only on items where the methodology approves it. Candidate items for F4:

- Out-of-pocket monthly health expenditure (`OOP_MONTHLY`).
- Catastrophic-health-expenditure threshold flag (`CHE_FLAG`) — derived; do **not** impute, recompute from imputed inputs.
- Indirect-cost components (transport, food, lost wages) — by stratum.

Do **not** run hot-deck on:

- Outcome variables of primary analysis (would bias the result).
- Identifier variables.
- Any variable specifically called out in Annex A as exclusion-on-missing.

Document the imputation policy in `F4-imputation-policy.md` before running. Get sign-off from Paunlagui (Survey Manager) before the imputation pass goes into the deliverable bundle.

---

## 11.8 Final documentation deliverables

The deliverable bundle's documentation set per F-series:

### 11.8.1 Data dictionary (human-readable)

The final `.dcf` rendered into a workbook readable by non-CSPro audiences. Use the project's `export_dcf_to_xlsx.py` utility to generate. Columns:

- Record name
- Item name
- Item label
- Type (Numeric / Alpha)
- Length
- Decimals
- Value-set name
- Notes

Filename: `F1-data-dictionary-v1.0.0.xlsx`.

### 11.8.2 Codebook (per-variable detail)

One page per variable, generated from the `.dcf` via the project's Python utility. Each variable lists:

- Variable name (CSPro item name)
- Variable label (item label)
- Type and length
- Value labels (full enumeration for categorical)
- Missing-value codes (e.g. 8 = Don't know, 9 = Refused, system-missing = blank)
- Source question (questionnaire page + question number)
- Skip-in conditions (display gates from `.apc`)
- Cross-field validation rules (HARD/SOFT references to the edit spec)
- Notes (any imputation rule that applies; any "Other (specify)" pairing)

Filename: `F1-codebook-v1.0.0.pdf`. Include a cover page with the engagement metadata (project, year, version, generation timestamp, generator commit hash).

### 11.8.3 Edit specifications

The final Skip-Logic-and-Validations spec per F-series — the Phase 4 deliverable, frozen at the closeout version. Filename: `F1-Skip-Logic-and-Validations-v1.0.0.md`. This is the document that explains *why* the data looks the way it does — every skip path, every HARD/SOFT/GATE rule, every cross-field consistency check.

### 11.8.4 Application source

The final CSPro application bundle per F-series:

```
F1-app-v1.0.0/
  F1.dcf                  { dictionary }
  F1.fmf                  { form file }
  F1.apc                  { application logic }
  F1.pen                  { packaged executable for CSEntry }
  shared/
    PSGC-Cascade.apc      { shared APC: PSGC dropdown cascade }
    Capture-Helpers.apc   { shared APC: capture-type helpers }
    Validators.apc        { shared APC: cross-field validators }
    Resume-Handlers.apc   { shared APC: partial-save / resume logic }
```

The `.pen` is the **deployable artifact** — what the field team's CSEntry tablets ran. The `.dcf` + `.fmf` + `.apc` are the **source artifacts** — what a future engagement opens in CSPro Designer to fork from.

### 11.8.5 Generator source

The Python generators + helpers, frozen at closeout:

```
generators-v1.0.0/
  F1/
    generate_dcf.py        { F1 DCF generator }
    config.py              { F1-specific value sets, naming overrides }
  F3/
    generate_dcf.py
    config.py
  F4/
    generate_dcf.py
    config.py
  shared/
    cspro_helpers.py       { numeric(), alpha(), yes_no_item(), select_one(), ... }
    build_psgc_lookups.py  { PSGC value-set generator from PSA reference data }
    export_dcf_to_xlsx.py  { dictionary -> workbook }
    export_dcf_to_codebook_pdf.py  { dictionary -> codebook PDF }
```

Tag the generator at `gen-final-v1.0.0` so the final dictionary can be reproduced exactly.

### 11.8.6 Field manuals

The final survey manual + cluster-specific addenda. These are typically authored by the methodology team (Paunlagui) but the closeout bundle has to include them so the deliverable set is self-contained. Confirm with Paunlagui at the start of the closeout window which version of the manual is the deliverable version.

Filenames:
- `UHC-Y2-Survey-Manual-v1.0.0.pdf`
- `UHC-Y2-Cluster-Addenda-NCR-v1.0.0.pdf`
- `UHC-Y2-Cluster-Addenda-Visayas-v1.0.0.pdf`
- `UHC-Y2-Cluster-Addenda-Mindanao-v1.0.0.pdf`

### 11.8.7 Issue log

`ISSUE-LOG.md` with every fieldwork anomaly + resolution. One row per issue:

| ID | Date opened | F-series | Location | Severity | Description | Resolution | Date closed | Affected case IDs |
|---|---|---|---|---|---|---|---|---|

Resolutions either say "fixed in hot-fix vX.Y.Z" or "no fix required, documented in codebook". Don't close an issue without a resolution category.

### 11.8.8 Hot-fix log

`HOTFIXES.md` with every mid-fieldwork patch — what changed, why, what cases were affected, what the post-fieldwork reconciliation step is.

| Hot-fix | Date | F-series | Trigger issue | Change | Affected case IDs | Post-fieldwork reconciliation |
|---|---|---|---|---|---|---|

For UHC: the hot-fix log is what tells the analyst "if you see weird values for case IDs X..Y in F1.q19, it's because the validation tier was inverted before hot-fix v1.0.3 — drop those cases or treat them as missing." Without the hot-fix log, those records look like noise.

### 11.8.9 Documentation bundle layout

```
deliverables/
  UHC-Y2-Final-Documentation/
    F1/
      F1-data-dictionary-v1.0.0.xlsx
      F1-codebook-v1.0.0.pdf
      F1-Skip-Logic-and-Validations-v1.0.0.md
      F1-app-v1.0.0/                    { application source }
      F1-impute-audit-summary.md        { if hot-deck ran }
    F3/
      ... (same shape)
    F4/
      F4-data-dictionary-v1.0.0.xlsx
      F4-codebook-v1.0.0.pdf
      F4-Skip-Logic-and-Validations-v1.0.0.md
      F4-app-v1.0.0/
      F4-imputation-policy.md
      F4-impute-audit-summary.md
      F4-hotdeck-impute.bch             { the imputation batch app, archived }
    generators-v1.0.0/                  { shared across F-series }
    UHC-Y2-Survey-Manual-v1.0.0.pdf
    UHC-Y2-Cluster-Addenda-*-v1.0.0.pdf
    ISSUE-LOG.md
    HOTFIXES.md
    EXPORT-RECONCILIATION.md            { from §11.2 }
```

---

## 11.9 Final release tagging

Tag the closeout artifacts so a researcher coming back in 2028 can reproduce the exact build that ran fieldwork. (Carl handles git operations manually per vault convention; this section just lists what gets tagged.)

| Tag | What it points at | Why |
|---|---|---|
| `f1-final-v1.0.0` | F1.dcf + F1.fmf + F1.apc + F1.pen + shared APCs | The exact application that produced F1 data |
| `f3-final-v1.0.0` | F3 application bundle | Same, for F3 |
| `f4-final-v1.0.0` | F4 application bundle | Same, for F4 |
| `gen-final-v1.0.0` | Python generators + helpers | Reproduce the dictionaries from spec |
| `export-stata-v1.0.0` | Stata export PFFs + batch wrappers | Reproduce the Stata exports |
| `export-spss-v1.0.0` | SPSS export PFFs + post-process syntax | Reproduce the SPSS exports |
| `export-excel-v1.0.0` | Excel batch-edit apps + attribute strings | Reproduce the Excel exports |
| `hotdeck-v1.0.0` | F4 hot-deck batch app + initial array values | Reproduce the imputation pass |
| `closeout-merge-v1.0.0` | Stata closeout-merge do-file | Reproduce the merged analysis dataset |

If a post-fieldwork correction ships, bump the patch version on the affected tag. The deliverable bundle's `vX.Y.Z` suffix (§11.2) **must match** the tag of the artifact that produced it.

---

## 11.10 Decommission

Once the final exports ship and the documentation bundle is signed off, decommission the running infrastructure. **Do this in the order listed** — credentials revoked before server stopped, server backed up before frozen, channels archived only after final analyst questions are answered.

### 11.10.1 Slack channels

Archive the operational Slack channels — they go read-only but stay searchable. Keep them archived rather than deleted; the conversation history is part of the engagement's institutional memory.

- `#capi-fieldwork-ops` → archive.
- `#capi-fieldwork-uat` → archive.
- `#f2-pwa-uat` → archive (handled by the PWA closeout, but cross-reference here for audit completeness).

### 11.10.2 CSWeb credentials

Revoke ephemeral credentials. Retain only the post-fieldwork analyst accounts.

| Credential class | Action |
|---|---|
| Per-enumerator (e.g. `enum-ncr-001`, `enum-ncr-002`, …) | **Revoke**. They have no business logging in after fieldwork ends. |
| Per-STL (Survey Team Leader) | **Revoke**. Same reasoning. |
| `ASPSI_ADMIN` | **Retain**. Required for any post-fieldwork operations and for analyst questions. |
| `DOH_VIEWER` | **Retain**. DOH analysts need read access during the analysis window. Convert to read-only if not already. |

Document the revocation pass in `CREDENTIALS-DECOMMISSION.md` with a date stamp and the executor's name.

### 11.10.3 Wampserver / CSWeb server

- Stop Wampserver auto-update so the server config doesn't drift after closeout.
- Freeze the server config: snapshot the `apache/conf`, `mysql/my.ini`, and the CSWeb application files. Save into the documentation bundle so a future researcher can rebuild the server from a known-good config.
- Backup the CSWeb database to a portable SQL dump:

```bash
mysqldump --user=root --password csweb > C:\UHC-Y2\closeout\backups\csweb-final-2026-12-XX.sql
```

Verify the dump by loading it into a clean MySQL instance and confirming row counts match the source. Without this verification step, you have a backup file but no proof the backup is restorable.

- Compress and archive: `csweb-final-2026-12-XX.sql.gz` lives in the documentation bundle.

### 11.10.4 Tablets

If ASPSI is keeping the tablets, leave the CSEntry app in place but mark the deployment as inactive (rename PFF to `*-inactive.pff` so a tablet that wakes up doesn't try to sync to a stopped server). If ASPSI is returning or repurposing tablets, the off-boarding includes a factory reset after one final sync — document the reset checklist in `TABLET-OFFBOARDING.md`.

### 11.10.5 PARA archive move

After **final client sign-off** (this is the gate; do not move before sign-off), move the project per PARA convention:

```
1_Projects/ASPSI-DOH-CAPI-CSPro-Development/
  ↓
4_Archives/ASPSI-DOH-CAPI-CSPro-Development-2026/
```

The `-2026` suffix on the archive name distinguishes UHC Year 2 from any future ASPSI-DOH engagement. The wiki, deliverables, and raw folder all stay intact; only the parent path changes.

Update `index.md` at the vault level to point at the new archive location. Existing wikilinks continue to resolve because they're path-based.

---

## 11.11 Lessons-learned entry

The workflow template ([[../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow]]) ends with a **Living-document log** table. Append a row at the end of the engagement.

Format: `Date | Project | Refinement`.

What to capture:
- Which Khurshid patterns were adopted (and how).
- Which audit gaps were closed (e.g. the May 6 Working File integration gaps — bench testing as a reviewable artefact, hot-deck audit trail discipline).
- What the May 6 Working File integration-gap pass taught about the workflow (gaps surface late if they're not deliverable-shaped early).
- Any new patterns the UHC engagement surfaced (e.g. the 12-digit case-ID convention as a CAPI standard; the closeout-merge do-file as a reusable template).

### Template row Carl writes at end of contract

```markdown
| 2026-12-XX | ASPSI-DOH UHC Y2 | Closeout pass codified from F1/F3/F4 (CSPro CAPI). Adopted Khurshid pipeline for unattended Stata exports (PFF + batch + Task Scheduler), Khurshid batch-app pattern for Excel exports with code/label control, Khurshid hot-deck imputation pattern for F4 expenditure missingness with `stat()` audit trail. Established the **12-digit case-ID convention** as a CAPI standard so F1/F3/F4 can be linked across instruments via `frlink`. Closeout-merge do-file template added for multi-frame Stata workflows (`frames dir`, `frlink`, `frval`/`frget`). Established **EXPORT-RECONCILIATION.md** as a closeout artifact reconciling case/record/variable counts across .csdb, .dat, .dta, .sav, .xlsx for every F-series. Established the audit-trail rule: every imputation gets logged via `stat()`, no silent imputation is acceptable in closeout. Hardened decommission discipline: credentials revoked before server stopped, MySQL dump verified by re-load before archive. Confirmed the SPSS post-process pattern (`AUTORECODE` + `VALUE LABELS` + `MISSING VALUES`) closes the gap between CSPro-emitted `.sav` and analyst-ready `.sav` when string fields slip through. Reusable artifact harvest produced: `cspro_helpers.py`, PSGC-Cascade.apc, Capture-Helpers.apc, Validators.apc, Resume-Handlers.apc, `build_psgc_lookups.py`, hot-deck batch app template, closeout-merge do-file. |
```

After appending, commit the workflow template (Carl handles this manually). The next CAPI engagement starts the cycle again with one more row of accumulated wisdom.

---

## 11.12 Reusable artifact harvest

What gets pulled out of UHC into reusable assets for the next CAPI engagement. These move from `1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/` into `2_Areas/IT-Standards/templates/` (or the shared CAPI library, where one exists).

### 11.12.1 Python helpers

- `cspro_helpers.py` — numeric(), alpha(), yes_no_item(), select_one(), select_all(), composite item shapes. Refine + commit to `2_Areas/IT-Standards/templates/cspro/`.
- `build_psgc_lookups.py` — generic enough to publish; works for any Philippine survey that needs PSGC dropdowns.
- `export_dcf_to_xlsx.py` — dictionary → workbook utility. Generic.
- `export_dcf_to_codebook_pdf.py` — dictionary → codebook PDF. Generic.

### 11.12.2 Shared APCs

- `PSGC-Cascade.apc` — province → city/municipality → barangay dropdown cascade. Commit to shared CAPI library.
- `Capture-Helpers.apc` — capture-type helpers (number pad, date, drop-down). Commit.
- `Validators.apc` — cross-field validators (age vs tenure, none-of-the-above exclusivity, mutually exclusive option groups). Commit.
- `Resume-Handlers.apc` — partial-save / resume / block-navigation. Commit.

### 11.12.3 Closeout templates

- `closeout-merge.do` from §11.6.6 — Stata multi-frame merge template.
- `F4-hotdeck-impute.bch` skeleton — hot-deck imputation batch app template (without the F4-specific array values; those go in a config file).
- `F1-export-stata.exf`, `F1-export-spss.exf`, `F1-export-excel.bch` skeletons — export specifications without F-series specifics.
- `F1-export-nightly.bat` template — batch wrapper for unattended exports.
- `UHC-Y2-F1-export-nightly.ps1` — Task Scheduler registration template.

### 11.12.4 Phase 10 HTML report templates

The Phase 10 monitoring deliverable (covered separately in [[07-Phase-9-10-Pretest-Fieldwork]]) produces HTML status reports. The templates are reusable as-is for any CAPI engagement that needs sync monitoring dashboards.

### 11.12.5 Conventions

- The **12-digit case-ID convention** as a CAPI standard. Document in `2_Areas/IT-Standards/standards/Case-ID-Convention.md`. Schema:
  - 6-digit PSGC barangay code (province + municipality + barangay)
  - 3-digit facility/household sequence within barangay
  - 3-digit person sequence within facility/household
- The **EXPORT-RECONCILIATION.md** schema as a closeout-deliverable standard.
- The **audit-trail rule**: every imputation gets logged via `stat()`. Document in the workflow template.

### 11.12.6 Harvest checklist

Before moving the project to `4_Archives/`, walk this checklist:

- [ ] `cspro_helpers.py` copied to `2_Areas/IT-Standards/templates/cspro/`, with UHC-specific bits genericized.
- [ ] `build_psgc_lookups.py` copied; PSGC reference data path made configurable.
- [ ] `export_dcf_to_xlsx.py` and `export_dcf_to_codebook_pdf.py` copied.
- [ ] `PSGC-Cascade.apc`, `Capture-Helpers.apc`, `Validators.apc`, `Resume-Handlers.apc` copied to shared CAPI library.
- [ ] `closeout-merge.do` template copied.
- [ ] Hot-deck batch app skeleton copied.
- [ ] Export PFF/EXF/BAT/PS1 skeletons copied.
- [ ] `Case-ID-Convention.md` created in `2_Areas/IT-Standards/standards/`.
- [ ] Audit-trail rule documented in workflow template.

---

## 11.13 Phase 11 exit criteria

The engagement is closed when **every** item below is checked. Partial completion is not closeout.

### Datasets

- [ ] Final CSPro `.csdb` frozen per F-series; `.dat` exported; reconciliation OK.
- [ ] Final Stata `.dta` exported per F-series; reconciliation OK.
- [ ] Final SPSS `.sav` exported per F-series; reconciliation OK.
- [ ] Final Excel `.xlsx` exported per F-series (codebook-friendly + analysis-friendly); reconciliation OK.
- [ ] `EXPORT-RECONCILIATION.md` shipped per F-series.
- [ ] If hot-deck ran on F4: post-impute dataset replaces pre-impute as the canonical; pre-impute archived alongside; impute-audit file shipped; impute-audit-summary.md shipped.

### Documentation

- [ ] Data dictionary (xlsx) shipped per F-series.
- [ ] Codebook (pdf) shipped per F-series.
- [ ] Edit specifications (md) shipped per F-series.
- [ ] Application source (`.dcf` + `.fmf` + `.apc` + `.pen` + shared APCs) shipped per F-series.
- [ ] Generator source shipped (one tag covers all three F-series).
- [ ] Field manuals + cluster addenda shipped.
- [ ] `ISSUE-LOG.md` finalized.
- [ ] `HOTFIXES.md` finalized with post-fieldwork reconciliation notes.

### Tags

- [ ] `f1-final-v1.0.0`, `f3-final-v1.0.0`, `f4-final-v1.0.0` tags applied.
- [ ] `gen-final-v1.0.0` tag applied.
- [ ] `export-stata-v1.0.0`, `export-spss-v1.0.0`, `export-excel-v1.0.0` tags applied.
- [ ] `hotdeck-v1.0.0` tag applied (if hot-deck ran).
- [ ] `closeout-merge-v1.0.0` tag applied.

### Decommission

- [ ] Slack channels archived (read-only).
- [ ] Per-enumerator and per-STL CSWeb credentials revoked.
- [ ] `ASPSI_ADMIN` and `DOH_VIEWER` retained for analysis window.
- [ ] Wampserver auto-update stopped; server config snapshotted.
- [ ] CSWeb MySQL dump produced AND verified by re-load.
- [ ] `CREDENTIALS-DECOMMISSION.md` shipped.
- [ ] Tablet off-boarding completed (where applicable); `TABLET-OFFBOARDING.md` shipped.

### Reusable harvest

- [ ] `cspro_helpers.py`, `build_psgc_lookups.py`, `export_dcf_to_xlsx.py`, `export_dcf_to_codebook_pdf.py` copied to `2_Areas/IT-Standards/templates/cspro/`.
- [ ] Shared APCs (`PSGC-Cascade`, `Capture-Helpers`, `Validators`, `Resume-Handlers`) copied to shared CAPI library.
- [ ] `closeout-merge.do` template copied.
- [ ] Hot-deck batch app skeleton copied.
- [ ] Export pipeline skeletons (PFF, BAT, PS1, EXF, BCH) copied.
- [ ] `Case-ID-Convention.md` created in `2_Areas/IT-Standards/standards/`.

### Workflow template

- [ ] Lessons-learned row appended to the workflow-template living-document log.
- [ ] Audit-trail rule (every imputation gets logged) documented in the workflow template.

### Sign-off and PARA move

- [ ] Final client sign-off received (email or signed document; archive in `deliverables/UHC-Y2-Final-Signoff/`).
- [ ] Project moved from `1_Projects/ASPSI-DOH-CAPI-CSPro-Development/` to `4_Archives/ASPSI-DOH-CAPI-CSPro-Development-2026/`.
- [ ] Vault `index.md` updated to point at the archive location.

When every box is checked, the engagement is closed. The next CAPI engagement starts in `1_Projects/` with the harvested templates and one more row of accumulated wisdom.

---

## Next

- [[99-Quick-Reference]] — single-page reference for the whole CAPI guide; commands, file paths, and Khurshid citations indexed.
- [[index]] — guide table of contents.
