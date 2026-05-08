---
title: "00 — Architecture"
category: deliverable
tags: [capi, cspro, csweb, csentry, architecture, uhc-y2]
last_updated: 2026-05-08
status: draft
---

# 00 — Architecture

## 1. Purpose and scope

This document is the **system map** for the UHC Survey Year 2 CAPI implementation — the F1 Facility Head, F3 Patient, and F4 Household instruments, all built on the CSPro toolchain (CSPro Designer + CSEntry Android + CSWeb). It describes how the authoring workstation, the source-of-truth artifacts, the field tablets, the CSWeb sync server, and the downstream operational and client surfaces fit together; what flows along each edge; and where the trust, storage, and versioning seams sit. It is meant to be read first, before any phase-by-phase build doc, by anyone who needs to understand what this system *is* before they start touching it: Carl as builder, Shan as QA, the CSWeb administrator, the survey team leaders monitoring fieldwork, and the project lead signing off deliverables. The phase-by-phase build instructions live in `[[02-Phase-0-2-Foundation]]` through `[[08-Phase-11-Closeout-Export]]`. The F2 Healthcare Worker instrument runs on a parallel **PWA** track (Vite + React + IndexedDB + Cloudflare Pages + Workers) and is documented in its own deliverable suite under `deliverables/F2/PWA/`; this document references F2 only at the points where the two tracks share artifacts (the 12-digit case-ID convention, ASPSI-side ops, the same DOH client) or run on shared infrastructure.

This guide is the UHC Year 2 instance of the reusable [[2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]] living-document template. Patterns marked **(Khurshid YYYY-MM-DD)** trace back to a specific tutorial in the Khurshid Arshad CAPI corpus.

---

## 2. System map

The full system spans five layers — authoring, source-of-truth, enumerator, server, and client — connected by a small number of well-defined edges. Carl (CAPI Developer) lives in the authoring layer; questionnaires and the artifacts derived from them live in the source-of-truth layer (under `1_Projects/ASPSI-DOH-CAPI-CSPro-Development/`); enumerators and STLs live in the enumerator and operational layers; the ASPSI Wampserver hosts CSWeb in the server layer; and DOH-PMSMD sits at the client edge.

```
+--------------------------------------------------------------------------------------------+
|                                                                                            |
|   AUTHORING LAYER  (Carl's workstation, Windows 10/11)                                     |
|   +----------------------------------------------------------------------------------+     |
|   |  CSPro Designer 7.7+   Python 3.x   Generator suite     Export tools             |     |
|   |  (form builder /       (generate_   (cspro_helpers.py,  (export_dcf_to_xlsx.py,  |     |
|   |   PROC editor /        dcf.py per   build_psgc_         CSBatch, CSTab)          |     |
|   |   Pen publisher /      F-series,    lookups.py)                                  |     |
|   |   PFF editor)          generate_                                                 |     |
|   |                        fmf.py)                                                   |     |
|   +-----------+----------------+--------------------+--------------+-----------------+     |
|               |                |                    |              |                       |
|               v                v                    v              v                       |
|                                                                                            |
|   SOURCE-OF-TRUTH LAYER  (1_Projects/ASPSI-DOH-CAPI-CSPro-Development/)                    |
|   +-----------------------+ +--------------------+ +---------------------------------+    |
|   | raw/                  | | wiki/sources       | | deliverables/CSPro/             |    |
|   | F1/F3/F4 PDFs +       | | Source - Annex F1, | | shared/  cspro_helpers.py       |    |
|   | text-extracts         | | F3, F4 wiki pages  | | shared/  build_psgc_lookups.py  |    |
|   | (questionnaire        | | (citable)          | | shared/  PSGC-Cascade.apc       |    |
|   |  versions: Apr 20)    | |                    | | shared/  Capture-Helpers.apc    |    |
|   +-----------------------+ +--------------------+ | shared/  psgc_*.dcf + .dat      |    |
|                                                   | F1/      generate_dcf.py        |    |
|                                                   | F1/      FacilityHeadSurvey.dcf |    |
|                                                   | F1/      F1-Skip-Logic-...md    |    |
|                                                   | F3/      generate_dcf.py        |    |
|                                                   | F3/      generate_fmf.py        |    |
|                                                   | F3/      PatientSurvey.dcf      |    |
|                                                   | F3/      *.generated.fmf        |    |
|                                                   | F4/      generate_dcf.py        |    |
|                                                   | F4/      generate_fmf.py        |    |
|                                                   | F4/      HouseholdSurvey.dcf    |    |
|                                                   | F4/      *.generated.fmf        |    |
|                                                   +-----------------+----------------+    |
|                                                                     |                     |
|                              (Designer reads .dcf + .fmf,           |                     |
|                               wires PROC, then "Publish Entry       |                     |
|                               Application" -> .pen package)         |                     |
|                                                                     v                     |
|   PACKAGED BUILD                                                                           |
|   +----------------------------------------------------------------------------------+    |
|   |  F1.pen   F3.pen   F4.pen   +   per-role .pff files   +   /Messages/*.html       |    |
|   |  (CSEntry-runnable bundles; each carries the .dcf + .fmf + .apc + lookups)       |    |
|   +-------------------------------------+--------------------------------------------+    |
|                                         |                                                 |
|                                         |   deploy via CSWeb "Apps" dashboard             |
|                                         v                                                 |
|                                                                                            |
|   ENUMERATOR LAYER  (Android tablets, ASPSI-issued)                                        |
|   +-----------------------------------------+    +----------------------------------+    |
|   |  CSEntry Android 7.7+                   |    |  Tablet local storage             |    |
|   |  (loads .pen, runs CAPI session,        |    |   - .csdb (live case database)    |    |
|   |   captures GPS via ReadGPSReading,      |--->|   - JPG verification photos       |    |
|   |   captures verification photo,          |    |   - logs / paradata               |    |
|   |   savepartial on OnStop)                |    |   - cached PSGC lookups           |    |
|   +-----------+-----------------------------+    +----------------------------------+    |
|               |                                                                            |
|               |  HTTPS sync (live IP, NOT localhost)                                       |
|               |  end of day OR hot-fix OR ad-hoc, per Protocol V2 10 PM rule               |
|               v                                                                            |
|                                                                                            |
|   SERVER LAYER  (ASPSI-hosted host running Wampserver 3.2.6 64-bit on Windows)             |
|   +----------------------------+   +----------------------+   +---------------------+    |
|   |  Apache (port 80/443)      |-->|  CSWeb 7.7 PHP app   |-->|  MySQL              |    |
|   |  TLS terminates here       |   |  (csweb in document  |   |  (CSWeb backing DB) |    |
|   |                            |   |   root)              |   |                     |    |
|   |                            |   |  - sync endpoints    |   |  cases, users,      |    |
|   |                            |   |  - dashboard         |   |  apps, files,       |    |
|   |                            |   |  - Pen + PFF host    |   |  paradata           |    |
|   +----------------------------+   +-----------+----------+   +---------+-----------+    |
|                                                |                        |                 |
|                                                v                        v                 |
|                                  +---------------------------------------------+          |
|                                  |  CSWeb dashboard (browser)                  |          |
|                                  |  data | apps | users | files | settings |   |          |
|                                  |  reports | roles                          |          |
|                                  +-----+----------------+----------------+----+          |
|                                        |                |                |               |
|                                        |                |                |               |
|                                        v                v                v               |
|                                                                                            |
|   OPERATIONAL LAYER                                                                        |
|   +-------------------+   +-------------------+   +-----------------------------------+   |
|   |  STL daily        |   |  Carl + Shan      |   |  Carl interim cross-tabs          |   |
|   |  monitoring       |   |  CSBatch nightly  |   |  CSTab progress reports           |   |
|   |  (Sync Report,    |   |  edit checks      |   |  (Phase 10 weekly)                |   |
|   |   Map Report)     |   |  (structure /     |   |                                   |   |
|   |                   |   |   validity /      |   |                                   |   |
|   |                   |   |   consistency)    |   |                                   |   |
|   +-------------------+   +-------------------+   +-----------------+-----------------+   |
|                                                                     |                     |
|                                                                     v                     |
|                                                                                            |
|   CLIENT LAYER  (DOH-PMSMD)                                                                |
|   +--------------------------------------------------------------------------------+      |
|   |  Interim deliverables: cross-tab PDFs, progress reports                        |      |
|   |  Final deliverables: STATA .dta, SPSS .sav, Excel .xlsx, CSPro .dat, codebook  |      |
|   |  Channel: deliverable submission via Juvy (Project Coordinator)                |      |
|   +--------------------------------------------------------------------------------+      |
|                                                                                            |
+--------------------------------------------------------------------------------------------+

  Edge legend:
   --->   one-shot artifact handoff (build, package, deploy, deliver)
   <-->   bidirectional sync (tablet <-> CSWeb)
   ...    operator-driven query (browser dashboard)
```

The five layers each have one job:

- **Authoring layer** is where the application is built. CSPro Designer is the only place you visually wire forms, attach question text, and edit PROC; the Python generator suite emits the dictionaries and FMF skeletons that Designer consumes; the export tool round-trips dictionaries into reviewable Excel.
- **Source-of-truth layer** is the durable record of what the application *is*. Questionnaire PDFs in `raw/` are immutable; the Python generators in `deliverables/CSPro/F{1,3,4}/generate_dcf.py` are the canonical history of every dictionary; the skip-logic + validation specs (`F1-Skip-Logic-and-Validations.md`, etc.) are the canonical history of every routing and edit-check decision.
- **Enumerator layer** is the only place real respondent data ever lives at rest on a non-server device. Tablets hold the live `.csdb` + verification JPGs until end-of-day sync.
- **Server layer** is the only place data converges. CSWeb terminates the sync, lands cases in MySQL, and exposes the dashboards STLs and Carl use to monitor and operate.
- **Operational + client layers** are read-mostly surfaces — CSBatch and CSTab pull from the CSWeb-MySQL pair; client deliverables pull from CSBatch- and CSTab-blessed exports.

---

## 3. Component inventory

| Component | Software | Version | Role | Owner | Khurshid reference |
|---|---|---|---|---|---|
| CAPI authoring tool | CSPro Designer | 7.7+ | Form builder, dictionary editor, PROC editor, .pen publisher, PFF editor | Carl | (Khurshid 2022-03-14) install procedure |
| Tablet runtime | CSEntry Android | 7.7+ | Runs `.pen` package, captures cases, manages local `.csdb` | Field enumerators (provisioned by CSWeb admin) | (Khurshid 2022-03-31) device-bound login |
| Sync server (web) | CSWeb | 7.7 | HTTPS sync endpoints + browser dashboard (data / apps / users / files / settings / reports / roles) | CSWeb admin (ASPSI ops) | (Khurshid 2022-04-30) deployment + dashboard tour |
| Web stack | Wampserver | 3.2.6 (64-bit) | Apache + PHP + MySQL bundle for Windows; hosts CSWeb | CSWeb admin | (Khurshid 2022-03-14) install on Win10 with VC++ prerequisites |
| Database | MySQL | bundled with Wampserver 3.2.6 | CSWeb backing store: cases, users, apps, files, paradata | CSWeb admin | (Khurshid 2022-03-14) DB created in phpMyAdmin |
| DB admin | phpMyAdmin | bundled with Wampserver | Hand operations on the CSWeb DB (rare; for break-glass) | CSWeb admin | (Khurshid 2022-03-14) |
| Generator runtime | Python | 3.x | Runs the F-series generators + PSGC builder + xlsx export | Carl | — |
| Shared generator helpers | `deliverables/CSPro/cspro_helpers.py` | living | Value sets, item builders, parameterized FIELD_CONTROL / GEO_ID / dictionary assembly | Carl | — |
| F1 generator | `deliverables/CSPro/F1/generate_dcf.py` | living | Emits `FacilityHeadSurvey.dcf` (12 records / 671 items) | Carl | — |
| F3 dictionary generator | `deliverables/CSPro/F3/generate_dcf.py` | living | Emits `PatientSurvey.dcf` (18 records / 806 items) | Carl | — |
| F3 form-skeleton generator | `deliverables/CSPro/F3/generate_fmf.py` | living | Emits `PatientSurvey.generated.fmf` (19 forms, 0 orphan items) | Carl | — |
| F4 dictionary generator | `deliverables/CSPro/F4/generate_dcf.py` | living | Emits `HouseholdSurvey.dcf` (22 records / 623 items) | Carl | — |
| F4 form-skeleton generator | `deliverables/CSPro/F4/generate_fmf.py` | living | Emits `HouseholdSurvey.generated.fmf` (24 forms) | Carl | — |
| Dictionary review export | `deliverables/CSPro/export_dcf_to_xlsx.py` | living | Round-trips any `.dcf` to two-sheet xlsx (Dictionary + Value Sets) for review without CSPro | Carl | — |
| PSGC lookup builder | `deliverables/CSPro/shared/build_psgc_lookups.py` | living | Builds 4 external lookup `.dcf` + `.dat` from PSA 1Q 2026 CSVs | Carl | (Khurshid 2023-09-12) linked-value-sets pattern adapted to externalized lookups |
| PSGC region lookup | `deliverables/CSPro/shared/psgc_region.{dcf,dat}` | PSA 1Q 2026 | 18 regions, parent sentinel `0000000000`, max 20 occurrences | Carl | — |
| PSGC province lookup | `deliverables/CSPro/shared/psgc_province.{dcf,dat}` | PSA 1Q 2026 | 117 provinces/HUCs keyed by region, max 30 occurrences | Carl | — |
| PSGC city lookup | `deliverables/CSPro/shared/psgc_city.{dcf,dat}` | PSA 1Q 2026 | 1,658 cities/municipalities/SubMuns keyed by province, max 60 occurrences | Carl | — |
| PSGC barangay lookup | `deliverables/CSPro/shared/psgc_barangay.{dcf,dat}` | PSA 1Q 2026 | 42,010 barangays keyed by city, max 2,000 occurrences | Carl | — |
| Cascade logic module | `deliverables/CSPro/shared/PSGC-Cascade.apc` | living | 4 public `Fill*ValueSet` functions invoked from `onfocus` events to drive cascading dropdowns | Carl | (Khurshid 2022-04-09) `setvalueset()`; (Khurshid 2022-04-05) `loadcase()` against external dict |
| Capture helpers | `deliverables/CSPro/shared/Capture-Helpers.apc` | living | `ReadGPSReading(maxTimeSec, desiredAccuracyM)` + `TakeVerificationPhoto(filename)` | Carl | (Khurshid 2023-09-09) background GPS via paradata; (Khurshid 2022-07-06) `forcase` over external dict |
| Form-Layout Principles | `deliverables/CSPro/Form-Layout-Principles.md` | living | Project-wide rules for splitting sections into Designer forms (one section -> N forms, roster on its own form) | Carl | — |
| F1 skip-logic + validation spec | `deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md` | living | 166-question skip-logic table, hard/soft/gate validations, paste-ready PROC templates | Carl | (Khurshid 2022-06-26) `errmsg` HARD / `warning` SOFT |
| F3 skip-logic + validation spec | `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md` | living | 1,133 lines; sections A–L; 14 sanity findings; 15 PROC templates | Carl | (Khurshid 2022-06-26) |
| F4 skip-logic + validation spec | `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` | living | 904 lines; sections A–Q; 13 sanity findings; 11 PROC templates | Carl | (Khurshid 2022-06-26) |
| Packaged tablet build | `F{1,3,4}.pen` (CSPro Designer "Publish Entry Application" output) | per-build | Single-file deployable bundle CSWeb pushes to tablets | Carl publishes; CSWeb admin deploys | (Khurshid 2022-04-24) Publish Entry Application + Deploy Application packaging |
| Sync / launch parameter file | `*.pff` (one per role: enumerator / supervisor; one for sync) | per-role | Tells CSEntry which app + dict + sync URL to use | Carl + CSWeb admin | (Khurshid 2022-04-15) Build a PFF object; (Khurshid 2022-05-12) Generate sync PFF via PFF Editor |
| Batch edit runner | CSBatch | bundled with CSPro 7.7+ | Nightly structure / validity / consistency / imputation passes | Carl + Shan | (Khurshid 2022-12-31) batch-edit run-config dialog |
| Tabulation tool | CSTab | bundled with CSPro 7.7+ | Interim cross-tabs for client progress reports | Carl | (Khurshid 2023-09-28) batch-edit application as data exporter |
| Export pipeline | CSPro Tools -> Export Data + a Windows batch wrapper | living | STATA `.dta` / SPSS `.sav` / Excel `.xlsx` / `.dat` final exports; scheduled via Task Scheduler | Carl | (Khurshid 2022-05-12) generate STATA-export PFF + wrap in batch + Task Scheduler |

---

## 4. Data flow diagrams

The system has four distinct flows. Each is small enough to read on its own, and the seams between them are the operational handoffs (Carl publishes to CSWeb; CSWeb pushes to tablets; tablets sync to CSWeb; CSWeb exports to clients).

### 4.1 Build-time flow

How a paragraph in a questionnaire PDF becomes a CAPI build. This is the flow Carl runs every time the questionnaire revs.

```
+-------------------+          +---------------------+          +----------------------+
| Annex F{1,3,4}    |  text    | raw/F{1,3,4}_clean  | summary  | wiki/sources/        |
| Apr 20.pdf        | extract  | .txt                | + cite   | Source - Annex F...  |
| (in raw/)         | ------>  | (grep-able)         | -----> | (citable per Q)      |
+-------------------+          +---------------------+          +----------+-----------+
                                                                           |
                                                                           |  drives
                                                                           v
+--------------------------------------+      +---------------------------------------------+
| Skip-Logic + Validation spec         |      | Python generator                            |
| F{1,3,4}-Skip-Logic-and-             |<---->| generate_dcf.py + cspro_helpers.py +        |
| Validations.md                       | feed | shared/build_psgc_lookups.py                |
| (hard / soft / gate per item,        | back | (one builder fn per section)                |
|  paste-ready PROC templates)         |      |                                             |
+-------------------+------------------+      +-----+----------------------------------+----+
                    |                                |                                  |
                    |                                v                                  v
                    |                      +--------------------+         +------------------------+
                    |                      | F{1,3,4}.dcf       |         | shared/psgc_*.dcf      |
                    |                      | (12-22 records,    |         | + .dat                 |
                    |                      |  600-800 items,    |         | (PSGC lookups)         |
                    |                      |  ~1 MB each)       |         |                        |
                    |                      +---------+----------+         +-----------+------------+
                    |                                |                                |
                    |                                v                                |
                    |                      +-------------------------+                |
                    |                      | generate_fmf.py         |                |
                    |                      | (F3, F4: emit form      |                |
                    |                      |  skeleton w/ form       |                |
                    |                      |  splits inline)         |                |
                    |                      +------------+------------+                |
                    |                                   |                             |
                    v                                   v                             v
+----------------------------------------------------------------------------------------+
|  CSPro Designer (Carl)                                                                 |
|  - opens .dcf + .generated.fmf                                                         |
|  - finalizes form splits (per Form-Layout-Principles.md, e.g. roster on its own form)  |
|  - wires PROC: skip-to / errmsg + reenter / accept / setvalueset / FIELD_CONTROL       |
|  - attaches PSGC-Cascade.apc + Capture-Helpers.apc as external logic files             |
|  - declares CAPI languages (English + Filipino + ... per Khurshid 2022-09-26)          |
|  - desk-tests in CSEntry Windows (Phase 7 happy path + bench mock cases)               |
+--------------------------------------+-------------------------------------------------+
                                       |
                                       |  Publish Entry Application (Khurshid 2022-04-24)
                                       v
                        +------------------------------+
                        |  F{1,3,4}.pen                |
                        |  (single-file bundle)        |
                        +------------------------------+
```

A few invariants this flow holds:

- The `.dcf` is **never** edited in Designer for content — only opened to confirm it parsed and to wire forms / PROC. Every dictionary change must round-trip through `generate_dcf.py`. This is the project-wide "generator over hand-edit" rule (D-02 below).
- The `.generated.fmf` is a *skeleton*. Carl finalizes form splits in Designer using the splits that `generate_fmf.py` already encoded as form labels. From that point onward Designer is the source of truth for the FMF (forms aren't easy to round-trip back into a generator and the layout-tweaking work is visual by nature).
- Skip logic flows in two directions: the spec markdown drives the PROC code Carl writes, and dictionary edits Carl makes in the generator round-trip back to the spec markdown so the two stay locked.
- PSGC is built once, shared across F1/F3/F4. The main dictionaries hold only a placeholder value set on each PSGC item; the real options arrive at runtime via `PSGC-Cascade.apc` (D-03).

### 4.2 Daily fieldwork flow

How a single case moves from "enumerator presses Start" to "STL sees it on the dashboard."

```
+----------------------+   tap to launch   +----------------------------+
| Enumerator's tablet  | --------------->  | CSEntry Android            |
| (ASPSI-issued)       |                   | loads F1.pen / F3.pen /    |
+----------------------+                   | F4.pen via .pff            |
                                           +-------------+--------------+
                                                         |
                                                         | enter case
                                                         v
                                       +-----------------------------------+
                                       |  CAPI session                     |
                                       |  - FIELD_CONTROL: consent +       |
                                       |    eligibility + interviewer ID   |
                                       |  - GEO ID: PSGC cascade (region   |
                                       |    -> province -> city ->         |
                                       |    barangay) via setvalueset      |
                                       |  - GPS read on entry              |
                                       |    (Capture-Helpers ReadGPS)      |
                                       |  - Sections A..H/L/Q              |
                                       |  - errmsg / accept on validations |
                                       |  - end-of-interview photo capture |
                                       |  - savepartial on every block     |
                                       |    (Khurshid 2022-09-21 OnStop)   |
                                       +-----------------+-----------------+
                                                         |
                                                         v
                                       +-----------------------------------+
                                       |  Tablet local storage             |
                                       |  - F{1,3,4}.csdb (live cases)     |
                                       |  - case-<id>-verification.jpg     |
                                       |  - paradata (timestamps, GPS)     |
                                       +-----------------+-----------------+
                                                         |
                                                         | end of day
                                                         | (Protocol V2 10 PM rule)
                                                         | OR ad-hoc (low connectivity)
                                                         v
                                       +-----------------------------------+
                                       |  CSEntry sync                     |
                                       |  - syncconnect (Khurshid          |
                                       |    2022-04-30) to live IP         |
                                       |    (NOT localhost)                |
                                       |  - HTTPS POST cases + JPG         |
                                       |    attachments                    |
                                       |  - synchronize_data binds .csdb   |
                                       |    via setfile() first            |
                                       |  - synctime() stamps each case    |
                                       |    (Khurshid 2025-02-20)          |
                                       +-----------------+-----------------+
                                                         |
                                                         |  HTTPS over cellular / hotspot
                                                         v
+--------------------------------+   POST   +---------------------------------+
| Apache (port 443)              | <------ | CSWeb 7.7 PHP sync endpoint     |
| TLS terminates                 | ------> | merges into MySQL (cases, users,|
+--------------------------------+ MySQL    | files, paradata)                |
                                            +-----------------+---------------+
                                                              |
                                                              | renders
                                                              v
                                       +-----------------------------------+
                                       |  CSWeb dashboard (browser)        |
                                       |  - Sync Report (cases by          |
                                       |    enumerator / day)              |
                                       |  - Map Report (GPS overlay,       |
                                       |    Khurshid 2022-07-06)           |
                                       |  - Data dashboard (drill into     |
                                       |    a case)                        |
                                       +-----------------------------------+
                                                              |
                                                              | viewed by
                                                              v
                                                +-------------------------------+
                                                |  STL / Field Manager / Carl   |
                                                |  (daily monitoring)           |
                                                +-------------------------------+
```

- The tablet keeps its own `.csdb` even after sync; sync is one-way push of new and modified cases. This means a tablet that loses connectivity never loses data — it just batches the upload.
- The sync URL is the **public IP** of the ASPSI Wampserver, never `localhost` (Khurshid 2022-04-30). Localhost works in Designer's desk-test only.
- `synctime()` stamps each case in MySQL with the time it was last synced (Khurshid 2025-02-20). STLs use this to spot stale-case enumerators.
- The verification JPG travels alongside the dictionary case via CSEntry's standard attachments mechanism, not as a binary dictionary item — see D-... below and the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/GPS and Photo Capture|GPS and Photo Capture concept page]].

### 4.3 Hot-fix flow

When Carl needs to push a dictionary or PROC fix to tablets already in the field.

```
+---------------------+        +-------------------------+        +-----------------------+
| field bug surfaces  |  ----> | Carl edits the          |  ----> | Carl re-runs          |
| (via STL / Slack /  | via    | GENERATOR               | edit   | python generate_dcf   |
| Shan / CSBatch)     | issue  | (NEVER the .dcf)        | locally| -> new .dcf + .fmf    |
+---------------------+        +-------------------------+        +----------+------------+
                                                                             |
                                                                             v
                                                            +-------------------------------+
                                                            | Designer review               |
                                                            | - confirm dictionary parses   |
                                                            | - update PROC if logic        |
                                                            |   changed                     |
                                                            | - bump publishdate()          |
                                                            |   (Khurshid 2022-10-08)       |
                                                            | - desk-test happy path        |
                                                            |   + the specific bug repro    |
                                                            +---------------+---------------+
                                                                            |
                                                                            v
                                                            +-------------------------------+
                                                            | Publish Entry Application     |
                                                            | -> new F{1,3,4}.pen           |
                                                            +---------------+---------------+
                                                                            |
                                                                            v
                                                            +-------------------------------+
                                                            | CSWeb admin uploads new .pen  |
                                                            | to "Apps" dashboard           |
                                                            +---------------+---------------+
                                                                            |
                                                                            | tablets pull on launch
                                                                            v
                                                            +-------------------------------+
                                                            | CSEntry on each tablet:       |
                                                            | - publishdate() check fires   |
                                                            |   (Khurshid 2022-10-08        |
                                                            |    "force enumerators to      |
                                                            |    update via expiration")    |
                                                            | - if local build < server     |
                                                            |   build -> auto-update        |
                                                            | - existing .csdb cases        |
                                                            |   preserved (D-01)            |
                                                            +-------------------------------+
```

The two preconditions that make this flow safe:

- **D-01 (`.csdb` over `.dat`)**: schema changes break `.dat` but **not** `.csdb` (Khurshid 2023-09-21). Adding an item or value to the dictionary doesn't invalidate stored cases on the tablet. *Removing* or *renaming* an item still requires Tools -> Reformat Data, see Failure Modes below.
- **publishdate()** baked into the build: tablets compare local build's publishdate to the server's and force the update on launch (Khurshid 2022-10-08).

If the change is dictionary-removing or dictionary-renaming (rare; treat as design change, not hot-fix), the flow is the **schema mid-fieldwork** failure mode in section 11, not this flow.

### 4.4 Export flow

How an authoritative CSPro dataset becomes the deliverable artifacts DOH-PMSMD analyzes against.

```
+--------------------------------+
| MySQL (CSWeb backing DB)       |
| canonical case store           |
+---------------+----------------+
                |
                | "Export" tab on
                | CSWeb dashboard
                v
+----------------------------------------------------+
| CSWeb -> CSPro .dat extract                        |
| (per dictionary: F1.dat, F3.dat, F4.dat)           |
+---------------+------------------------------------+
                |
                | Tools -> Export Data
                | (Khurshid 2022-05-12 batch-file pattern)
                | wraps a PFF in a .bat;
                | Task Scheduler runs nightly
                v
+----------------------------------------------------+
| Per-format export PFFs                             |
|  - export_F1_to_stata.pff -> F1.dta                |
|  - export_F1_to_spss.pff  -> F1.sav                |
|  - export_F1_to_excel.pff -> F1.xlsx               |
|  (same per F3, F4)                                 |
+---------------+------------------------------------+
                |
                | also runs CSBatch:
                | - structure check
                | - validity check
                | - consistency check
                | (Khurshid 2022-12-31)
                v
+----------------------------------------------------+
| Cleaned analysis-ready datasets                    |
|  F{1,3,4}.dta / .sav / .xlsx / .dat + codebook     |
+---------------+------------------------------------+
                |
                | Juvy-routed deliverable submission
                v
+----------------------------------------------------+
| DOH-PMSMD analysis cluster                         |
|  STATA / SPSS / Excel users                        |
+----------------------------------------------------+
```

CSBatch is the gate that keeps export from shipping bad data. The Phase 7 mock cases turn into the Phase 10 + Phase 11 regression set; every consistency rule that ever fired in spec-time fires again at export-time as a final guard.

---

## 5. Trust and authentication boundaries

The system has three trust boundaries: tablet -> CSWeb, CSWeb -> operator, and CSWeb -> MySQL. Plus a fourth, more subtle one: build-artifact integrity.

### 5.1 Tablet -> CSWeb

Each enumerator logs in to CSEntry on their assigned tablet using credentials provisioned through the CSWeb "Users" dashboard. The login is **bound to the tablet device ID** (Khurshid 2022-03-31 *Tutorial 2: Excel and External Dictionary*) — a credential cannot roam to an unprovisioned device without an admin re-binding it.

Enumerators are organized into **teams** with a **supervisor / enumerator team-ID convention** (Khurshid 2022-03-31): all members of one team share a team prefix in their login ID, the supervisor's ID has a distinct suffix. The Sync Report and Map Report on CSWeb filter by team ID so an STL only sees their own team's cases.

The HTTPS connection terminates at Apache; the `syncconnect` / `syncdisconnect` flow (Khurshid 2022-04-30) opens an authenticated session with the live IP (never localhost). The session credential is the same as the CSWeb user record.

### 5.2 CSWeb -> operator (dashboard access)

CSWeb ships a **two-axis permission model** documented in the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|CSWeb Users Guide]] and the *How to Sync Report, Sync Files, Add Users and Define Roles* tutorial (Khurshid 2022-05-05):

- Per-dashboard permission (data, apps, users, files, settings, reports — read or write).
- Per-dictionary permission (upload / download per F1, F3, F4).

Two built-in roles plus custom roles:

- **Administrator** — full access. Carl + Juvy + 1–2 ASPSI ops.
- **Standard User** — typical STL: read on data + sync + map dashboards, no users / settings.
- **Custom** — for QA (Shan) or external reviewers, scoped down to specific dictionaries or read-only-data.

CSV bulk import of users is supported (per the CSWeb Users Guide); preferred over per-row data entry once the team grows.

### 5.3 CSWeb -> MySQL

CSWeb writes to MySQL using a single bundled DB user provisioned at install time (Khurshid 2022-03-14 *How to Install Wampserver, CSPro and CSWeb server*). That credential lives in the CSWeb config file on the server filesystem.

**Credential rotation policy**: rotate the MySQL CSWeb user password on every of (a) enumerator-team turnover, (b) end of fieldwork, (c) CSWeb major version upgrade. Document the rotation in the CSWeb admin runbook and update the CSWeb config file in the same change.

Direct phpMyAdmin access is admin-only and reserved for break-glass DB operations. STLs and enumerators never have phpMyAdmin credentials.

### 5.4 Build-artifact integrity

The integrity rule for build artifacts is: **every `.dcf` is regenerable from a checked-in generator**. The Python generators in `deliverables/CSPro/F{1,3,4}/generate_dcf.py` (and the helpers in `deliverables/CSPro/cspro_helpers.py`) are the canonical history; the `.dcf` files committed alongside them are regeneration outputs that must reproduce byte-stable when the generator is run.

The single packaged build is the `.pen` published by Designer. Tablets do not run dictionaries or FMFs as separate files — they run a `.pen`. This means *the trust boundary for "what is this tablet running"* is the `.pen` checksum (and its embedded `publishdate()`), not the dictionary file.

---

## 6. Storage decisions (with rationale)

The following decisions are pre-committed; phase docs assume them and don't re-litigate them.

### D-01: `.csdb` over `.dat` for live data

Tablet-side and server-side live storage uses the CSPro `.csdb` SQLite-backed format, not the legacy fixed-width `.dat` format.

**Why**: schema changes break `.dat` files but not `.csdb` files (Khurshid 2023-09-21 *Tutorial on: Data Reformatting*). On a CAPI engagement that runs months and pushes hot-fixes during fieldwork, `.dat` would force a full Data Reformatting pass on every change; `.csdb` survives most schema additions transparently. `.dat` is reserved for export — it's the input shape STATA / SPSS converters expect.

### D-02: Single source of truth = the Python generator + spec markdown, never the dcf directly

Every dictionary edit lands in `generate_dcf.py` (or `cspro_helpers.py` for cross-instrument items). The `.dcf` is regenerated; the regenerated file is the artifact that opens in Designer.

**Why**: questionnaires *always* change. Hand-edits in Designer are silent and untraceable; generator edits are diff-able and the reasoning lives next to the code. This is the project's first design rule, codified in `[[2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]]` ("Generator over hand-edit").

### D-03: PSGC externalized to lookup DCFs, not baked into main dictionaries

PSGC (Region / Province / City / Barangay) lives in four **external lookup dictionaries** under `deliverables/CSPro/shared/`. The main F1 / F3 / F4 dictionaries hold only a 1-entry placeholder value set on each PSGC item; the real options are loaded at runtime via `loadcase()` + `setvalueset()` invoked from `onfocus` events ((Khurshid 2023-09-12) linked-value-sets pattern adapted; (Khurshid 2022-04-09) `setvalueset()` runtime swap).

**Why**:

| Concern | Before (baked) | After (external lookup) |
|---|---|---|
| F1 `.dcf` size | 17.2 MB | ~0.9 MB |
| F3 `.dcf` size | ~33 MB (doubled: facility + patient home) | ~1.0 MB |
| F4 `.dcf` size | ~17 MB | ~0.8 MB |
| PSGC duplication | 3x (once per F-series form) | 1x (single `shared/` source of truth) |
| Cascading dropdowns | infeasible | first-class via `setvalueset()` |
| Tablet UX | 42k-barangay single dropdown | filtered to ~25 barangays per parent city |

The pattern mirrors the **Popstan Census CAPI reference app** (CSPro 8.0 examples, the US Census Bureau's canonical demonstration of external-lookup geographic hierarchies).

Full pipeline + parent-code schema is in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets|PSGC Value Sets]].

### D-04: MySQL on Wampserver for CSWeb

Server-side persistence is MySQL, bundled in Wampserver 3.2.6 (64-bit) on Windows. CSWeb 7.7 deploys to the Wampserver document root; phpMyAdmin is the break-glass DB tool.

**Why**: this is the deployment baseline Khurshid teaches end-to-end (Khurshid 2022-03-14 *How to Install Wampserver, CSPro and CSWeb server*) and is the path of least operational surprise for a Windows-hosted ASPSI environment. Alternatives (cloud-hosted CSWeb, separate Linux + Apache + MariaDB stack) are open TODOs (section 12).

### D-05: Tablet-side data minimization and end-of-day sync

Tablets store the live `.csdb` + verification JPGs locally. The OS provides per-app sandboxing; we do not implement per-case application-level encryption at MVP.

**Why**: CSPro 8.0 doesn't provide a first-party at-rest encryption hook. Per Protocol V2, the daily 10 PM sync rule limits how much data is ever at rest on any single tablet to one day's worth of cases (typically <10). Combined with Android Verified Boot + per-app sandboxing + tablet device-ID binding (5.1 above), the residual exposure window is acceptable for MVP. Any future "encryption-at-rest standard" mandated by Protocol V2 is an open TODO (section 12).

### D-06 (implicit, recorded): Verification photo via filename reference, not binary dictionary item

CSPro 8.0 supports four binary item types (Image, Audio, Document, Geometry) but they are flagged **experimental**. Each F-series instrument records the verification photo as a filename-reference pair (`{prefix}VERIFICATION_PHOTO_FILENAME` alpha 120 + `{prefix}CAPTURE_VERIFICATION_PHOTO` num 1 trigger). The actual JPG ships via CSEntry's standard attachments mechanism.

**Why**: predictable behavior, no experimental flags, no risk of an undocumented schema change between CSPro point releases. Upgrade path to first-class binary items remains open.

### D-07 (working convention): Form layout principles

Form splits within a section follow `deliverables/CSPro/Form-Layout-Principles.md`:

- One questionnaire section -> one or more Designer forms (never less; F3 = 19 forms across 12 sections).
- Roster lives on its own form (e.g., F4 `C_HOUSEHOLD_ROSTER` `max_occurs=20` is alone on a form, never mixed with non-roster items).
- Section dividers map to form labels emitted by `generate_fmf.py`; Carl confirms in Designer.

This is encoded in `generate_fmf.py` and confirmed by the F3 / F4 form-skeleton outputs (19 / 24 forms, 0 orphan items).

---

## 7. Case ID architecture

The case identifier is a **12-digit decomposed PSGC-anchored code**, anchored on PSA 1Q 2026 PSGC, stored as **5 separate ID items** in the CSPro dictionary. The composite display form is `RRPPMMMFFCCC`; the dashed form `RR-PP-MMM-FF-CCC` is used in the manual, training cards, and dashboards.

```
   12 digits total
   |
   +-- RR  (2 digits)  REGION_CODE              01..19  PSA 1Q 2026 region (positions 1-2 of full 10-digit PSGC)
   |
   +-- PP  (2 digits)  PROVINCE_HUC_CODE        00..99  province / HUC slot within region (positions 3-4)
   |
   +-- MMM (3 digits)  CITY_MUNICIPALITY_CODE  000..999 city / mun slot within province (positions 5-7)
   |
   +-- FF  (2 digits)  FACILITY_NO              01..99  ASPSI sampling-frame facility index within municipality
   |
   +-- CCC (3 digits)  CASE_SEQ                001..999 per-instrument case sequence within facility
                                                           001-699  active
                                                           700-899  replacement (per Annex D)
                                                           900-999  refused / forfeited
```

`CASE_SEQ` is **scoped per instrument per facility** — F1 case `001` and F3 case `001` at the same facility are not collisions because the two instruments live in separate `.dcf` files with separate `RECORD_TYPE`. F4 cases are anchored on the F3 patient that produced them via a separate `F4_PARENT_F3_CASE_SEQ` data item (numeric 3) inside `HOUSEHOLD_GEO_ID`.

### Width verification (2026-05-05)

- Region 2 — PSA 1Q 2026 has 18 active regions; max region code = 19. 2 digits sufficient.
- Province 2 — max within-region province slot = 99 (BARMM). 2 digits sufficient.
- Municipality 3 — max within-province municipality slot = 934; 73 of 80 provinces have ≥1 mun with slot ≥ 100. **2 digits is structurally insufficient — must be 3.**
- Facility 2 — Inception Report Table 1: max per-province sample = 53 (Bulacan); max per-HUC sample = 38 (Quezon City). Per-municipality count is bounded above by these and easily fits 2 digits.
- Case 3 — F3 ceiling per facility is 67 OP + 45 IP = 112; F4 ceiling ~ patient-walk × low multiplier; F2 is ≤ 53 HCWs/facility. 999 leaves ample headroom for the 700–899 / 900–999 partitions.

### Trade-off vs Khurshid's `uuid()` recommendation

Khurshid (2022-09-21 *Working with Blocks*) recommends `uuid()` for "guaranteed-unique case IDs". A UUID gives uniqueness for free but is **not human-readable in the field**. STLs need to be able to look at a case ID on a tablet and say "that's Pampanga, Magalang, facility 01, the 12th patient" without a lookup table; enumerators need to be able to dictate a case ID over a phone call. The 12-digit decomposed scheme gives that for free, but **uniqueness is not free** — it requires:

- **Per-(facility, instrument) sequence enforcement**. A new case at a facility must claim the next free `CASE_SEQ` in the active range, the active range must already be sub-allocated to the right enumerator by the STL, and a tablet that's been offline must reconcile its sequence allocations on next sync.
- **Cross-tablet collision avoidance**. If two enumerators on the same team work at the same facility on the same day, each must hold a non-overlapping slice of the 001–699 active range. This is an STL-driven planning task, not an automatic system property.

**Where the enforcement lives**:

- The 5 ID-item block is generated by `cspro_helpers.build_id_block()` (see `[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|Questionnaire Numbering Convention]]` for the implementation footprint).
- Form-level guards (an `errmsg` + `reenter` on `CASE_SEQ` if the same `(REGION_CODE, PROVINCE_HUC_CODE, CITY_MUNICIPALITY_CODE, FACILITY_NO, CASE_SEQ)` tuple already exists in the local `.csdb`, plus the same tuple checked in the relevant external lookup if the STL uploaded the day's allocation file).
- STL-side allocation policy in the survey manual ("Enumerator 1: 001–050, Enumerator 2: 051–100, …").

The convention is documented in full at [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|Questionnaire Numbering Convention]] including the divergence flag against the Working File body's `RR-PP-MMM-FF-CC-CCC` variant — that's a Survey Manual reconciliation, not an architecture decision.

### Examples (Magalang, Pampanga; full mun PSGC = `0305411000`; 1st sampled facility)

| Instrument | Case ID | Meaning |
|---|---|---|
| F1 — Facility Head | `030541101001` | One facility head per facility, so `CCC=001` always |
| F2 — Healthcare Worker | `030541101012` | 12th HCW respondent at this facility (target 4–53 / facility) |
| F3 — Patient | `030541101027` | 27th patient at this facility (target ≤ 67 OP + 45 IP = 112) |
| F4 — Household | `030541101034` | 34th household interval-walked from a patient at this facility; parent F3 sequence in `F4_PARENT_F3_CASE_SEQ` |

---

## 8. Network topology

```
                            +----------------------------------------------+
                            |                Public Internet               |
                            +----+--------------------+---------------------+
                                 ^                    ^
                                 |                    |
                                 |                    | HTTPS (443)
                                 |                    | sync data + JPG attachments
                                 |                    |
                          HTTPS  |                    |
                          ops    |                    |
                          (443)  |                    |
                                 |                    |
                                 |                +---+------------------------+
                                 |                |  Field tablets             |
                                 |                |  (cellular / hotspot)      |
                                 |                |                            |
                                 |                |  +----------------------+  |
                                 |                |  | tablet 1 (team A,    |  |
                                 |                |  |  enumerator A1)      |  |
                                 |                |  +----------------------+  |
                                 |                |  +----------------------+  |
                                 |                |  | tablet 2 (team A,    |  |
                                 |                |  |  enumerator A2)      |  |
                                 |                |  +----------------------+  |
                                 |                |  +----------------------+  |
                                 |                |  | tablet N             |  |
                                 |                |  +----------------------+  |
                                 |                +----------------------------+
                                 |
                                 |
+--------------------------------v---------------------------------+
|                ASPSI office network (Manila)                     |
|                                                                  |
|  +------------------------------+    +-------------------------+ |
|  | Carl's workstation (Win10/11)|    |   ASPSI server          | |
|  | - CSPro Designer 7.7+        |    |   - Wampserver 3.2.6    | |
|  | - Python 3 + generators      |    |     (Apache + PHP +     | |
|  | - CSBatch / CSTab            |    |      MySQL)             | |
|  | - browser -> CSWeb dashboard |    |   - CSWeb 7.7           | |
|  | - VS Code / Obsidian vault   |    |   - phpMyAdmin (admin   | |
|  +--------------+---------------+    |     only)               | |
|                 |                    |   - public IP / port    | |
|                 |  internal HTTPS    |     80/443              | |
|                 |  (or LAN HTTP if   |                         | |
|                 |   Carl is on-prem) |                         | |
|                 +-------------------->                         | |
|                                      +----------+--------------+ |
|                                                 |                |
+-------------------------------------------------+----------------+
                                                  |
                                                  | exports
                                                  v
                                  +-------------------------------------+
                                  | Carl runs CSBatch + CSTab           |
                                  | Carl runs Tools -> Export Data via  |
                                  | scheduled .bat (Khurshid 2022-05-12)|
                                  | Outputs:                            |
                                  |   F{1,3,4}.dta / .sav / .xlsx /     |
                                  |   .dat                              |
                                  +-----------------+-------------------+
                                                    |
                                                    | Juvy-routed deliverable
                                                    | submission per ASPSI
                                                    | comms protocol
                                                    v
                                           +--------------------+
                                           |   DOH-PMSMD        |
                                           |   (client)         |
                                           +--------------------+


  Backup / fallback channels (decision favors CSWeb per Protocol V2):

      tablet  ----Bluetooth----> nearby tablet (peer-to-peer, last-resort)
      tablet  ------SD card----> ASPSI office (manual courier)
      tablet  ------Dropbox----> ASPSI office (cloud share, fallback)
      tablet  --------FTP-----> ASPSI office (legacy, fallback)
```

The CSWeb sync URL on every tablet is the **public IP of the ASPSI server** — Khurshid 2022-04-30 calls this out explicitly: "Tablet sync URL must be the live IP, not localhost." In Designer's desk-test (where Carl tests on his own workstation), `localhost` works; the moment a `.pen` ships to a tablet, it must point at the public IP.

Backup channels (Bluetooth / SD card / Dropbox / FTP) are documented in the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android Data Transfer Guide|CSPro Android Data Transfer Guide]] and remain available, but **Protocol V2 designates CSWeb as the primary path with a 10 PM daily upload mandate**. Fallback channels are used only when CSWeb is unreachable for >24 hours (see Failure Modes).

---

## 9. Multi-language architecture

UHC Year 2 fieldwork ships in 7 dialects per the ASPSI 2026-05-04 meeting (the canonical list is being maintained in the survey manual). At minimum, English + Filipino are first-class; the additional 5 are field-localized variants (Cebuano, Hiligaynon, Ilocano, Bicolano, Waray are typical for Philippine national surveys, but the canonical list lives in the manual, not here).

The CSPro multi-language model has **three independent stacks** (Khurshid 2022-09-26 *Multi Languages for CAPI and Valuesets*); each gets one entry per locale:

```
   Stack 1 — Dictionary labels (the columns enumerators see in the
             item list / data viewer)
              English label  |  Filipino label  |  Bicolano label  |  ...

   Stack 2 — CAPI question text (what enumerators read aloud)
              English question text  |  Filipino question text  |  ...

   Stack 3 — Messages tab (errmsg + accept dialog text + system
             messages overridden via OnSystemMessage)
              MSG_001  EN: "Age must be between 18 and 99"
              MSG_001  FI: "Ang edad ay dapat..."
              MSG_001  BI: "..."
```

### Per-language value sets

Each item that has a value set holds a **set of value sets**, one per language (Khurshid 2022-09-26 *Multi Languages for CAPI and Valuesets*). The naming convention is `<item>_vs1_<lang>`:

```
   ITEM Q23_FACILITY_TYPE
     value sets:
       Q23_FACILITY_TYPE_vs1_en  (1=Hospital, 2=RHU, 3=BHS, ...)
       Q23_FACILITY_TYPE_vs1_fi  (1=Ospital, 2=RHU, 3=BHS, ...)
       Q23_FACILITY_TYPE_vs1_bi  (...)
```

At runtime, `setvalueset()` switches the active value set on the item to match the current language (Khurshid 2022-04-09 *CSPro: User and Configuration Settings*).

### Language switch flow

```
   App start
       |
       v
   loadsetting("preferred_language")   (Khurshid 2022-04-09)
       |
       v
   setlanguage(<preferred>)            (Khurshid 2022-04-05)
       |
       v
   OnChangeLanguage global fires       (Khurshid 2022-04-05)
       |
       v
   For each item with multi-language vs:
       setvalueset(item, "<item>_vs1_<lang>")
       |
       v
   Dictionary labels, question text,
   and messages all switch in lockstep
```

User-driven mid-interview switch:

```
   Enumerator picks language from menu
       |
       v
   savesetting("preferred_language", choice)
       |
       v
   setlanguage(choice)
       |
       v
   OnChangeLanguage fires the same swap as on app start
```

### What this means for the build

- The Python generator must emit one value-set entry per language for every value-set'd item. `cspro_helpers.py` exposes the value-set constants (`YES_NO`, `YES_NO_DK`, etc.); each constant is keyed by language, and the generator iterates over the active locale list.
- Question text per item is held in the `.dcf` and is also language-keyed.
- The Messages tab is one big externalized table of numbered IDs (Khurshid 2022-06-22 *Error Message Function*), with `tr()` / `maketext()` calls referencing them by ID. ID swaps happen automatically at language change.
- Translations are not yet delivered by ASPSI as of this writing (per the project memory note on the ASPSI translation pipeline). The build accepts drop-in locales — the language-set list in Designer + the per-language value-set blocks in the generator + the Messages tab IDs are the only places the new locale must land.

---

## 10. Versioning and audit trail

### Build version

Every published `.pen` carries a `publishdate()` timestamp baked in by Designer at Publish Entry Application (Khurshid 2022-10-08 *Tutorial on PublishDate() Function*). On launch, CSEntry compares the local `.pen`'s publishdate to the server-pushed `.pen`'s publishdate; if local is older, CSEntry forces an update before allowing a new case.

Human-readable version strings (e.g., `F1.v1.0.0`, `F1.v1.0.1-hotfix`) are carried in:

- A static text element on the cover form (visible to the enumerator).
- A dictionary item `BUILD_VERSION` (alpha 16) on the FIELD_CONTROL block, so every case is stamped with the build that captured it. Useful for later analysis when a hot-fix changes a code book mid-fieldwork.

### Per-case audit metadata

Every saved case carries a small audit block, stored in either FIELD_CONTROL or the GEO ID record depending on instrument:

| Field | Source | Khurshid reference |
|---|---|---|
| GPS lat/lon/alt/accuracy/satellites/readtime | `Capture-Helpers.ReadGPSReading()` | (Khurshid 2023-09-09) background GPS via paradata |
| Verification photo filename | `Capture-Helpers.TakeVerificationPhoto()` | (Khurshid 2025-06-27) help text + camera launch idiom |
| Sync timestamp | `synctime()` populated server-side after each sync | (Khurshid 2025-02-20) |
| Enumerator login ID | inherited from CSEntry session | (Khurshid 2022-03-31) device-bound login |
| Tablet device ID | inherited from CSEntry session via `getos()` + device-id read | (Khurshid 2022-04-05) `getos()` |
| Build version | static + the `BUILD_VERSION` field above | — |

This block is the complete answer to "who captured this case, where, when, on what tablet, with which build".

### Canonical history

The canonical history for the CAPI build itself is the GitHub repo `cplreyes/ASPSI-DOH-UHC-CAPI-Development` plus the Obsidian wiki under `1_Projects/ASPSI-DOH-CAPI-CSPro-Development/`. The Python generators + spec markdown are the source-of-truth — each commit message records the rationale, each spec markdown bug-list close is dated, each ASPSI / DOH meeting that drove a change has its own wiki source page (`Source - ASPSI Team Meeting 2026-04-13`, etc.).

Carl handles versioning manually; this document describes the audit trail, not the workflow.

---

## 11. Failure modes and recovery

For each failure, the recovery technique is a Khurshid-cited pattern.

### F-01: Tablet dies mid-interview (battery, OS-kill, app crash)

**Symptom**: enumerator is partway through a case (e.g., 60% into F4's 22-record household roster) when CSEntry exits unexpectedly.

**Recovery**: `OnStop` global with `savepartial` (Khurshid 2022-09-21 *Working with Blocks*) preserves the in-progress case to the local `.csdb` on every block exit and on app stop. CSEntry resumes the partial case on relaunch via the PFF flag-and-modify-mode pattern (Khurshid 2022-10-23 *Tutorial on: Forcase Statement*) — `forcase` with `case_status` filter to enumerate partial cases and present the resume picker.

**Prerequisite**: every block-level exit must run through OnStop; the global is registered in PROC GLOBAL of each F-series application.

### F-02: Tablet lost, stolen, or destroyed

**Symptom**: enumerator reports tablet missing; the `.csdb` is gone.

**Recovery**:

1. **Limit exposure**: end-of-day sync rule (Protocol V2 10 PM mandate) means no more than one day's cases (~5–10) are at risk per tablet.
2. **Replacement tablet**: provision a fresh tablet, install CSEntry, install the live `.pen` from CSWeb, configure sync URL.
3. **Restore-from-backup flow** (Khurshid 2022-10-18 *Tutorial on: How to Restore Data from Backup*): if the tablet was using the SD-card-before-launch backup pattern (Khurshid 2022-10-12), pick the last backup folder, decompress, move-all to the new tablet's CSEntry data directory.
4. **Invalidate the old credential**: CSWeb admin disables the old enumerator login + tablet device-ID binding so a found tablet can't sync.

**Open**: SD-card-before-launch backup is a project-wide convention that needs Carl's PROC implementation in each F-series PROC GLOBAL (file copy + compress + delete csdb to fresh start, Khurshid 2022-10-12). The pattern is documented; the implementation is not yet baked in.

### F-03: Schema-changing bug found mid-fieldwork

**Symptom**: a bug requires *removing* or *renaming* a dictionary item — not just a new value or a logic tweak. Cases already in the field have data shaped to the old dictionary.

**Recovery**: `Tools -> Reformat Data` in CSPro with old + new dictionaries side-by-side (Khurshid 2023-09-21 *Tutorial on: Data Reformatting*).

**CRITICAL precondition (Khurshid 2023-09-21)**: do **not** enter new cases with the new dictionary before reformatting. Once the new build is live and an enumerator captures a case, the old data file becomes the unified data file and the reformatting tool can no longer match the old shape. The order is strict:

1. Hold all field tablets at the old build (don't push the new `.pen` yet).
2. Sync everything from the field to CSWeb.
3. On Carl's workstation: open Reformat Data, point it at the old + new dictionaries, run it. Verify the output.
4. Replace the server-side `.csdb` with the reformatted version.
5. Push the new `.pen` to tablets.

Alternative softer pattern (Khurshid 2023-09-21): keep both old and new items in the dictionary; drop the old item from the form. This avoids a Reformat run entirely at the cost of a slightly noisier dictionary. Use this pattern when the change is removal-only and the renamed-in-form / kept-in-dict trade is acceptable.

### F-04: CSWeb server down

**Symptom**: tablets cannot sync; STL dashboards return errors.

**Recovery**:

1. **Wampserver service-recovery**: restart Apache + MySQL services on the ASPSI server (`net stop wampapache64` / `net start wampapache64`, same for `wampmysqld64`). 90% of CSWeb outages are a stuck Wampserver service.
2. **MySQL integrity check**: phpMyAdmin -> CSWeb DB -> Check / Repair Tables. If MySQL crashed mid-write, the CSWeb cases table can be left in an inconsistent state.
3. **Disk-full check**: CSWeb's logs + the MySQL data directory are the usual disk-fill culprits. Clear logs, archive old paradata.
4. **Fallback channel**: if CSWeb is down >24 hours, instruct the field via Slack to use **Dropbox fallback** (case files copied to a per-enumerator Dropbox folder via the SD-card-before-launch backup, then ingested into CSWeb on recovery via `synchronize_file()` (Khurshid 2022-05-05) + a manual ingest script).

**Decision**: the fallback channel is documented but **not preferred**. Protocol V2 designates CSWeb as the primary path. Field guidance: "wait one cycle; if 24 hours gone, fall back."

### F-05: Sync conflict

**Symptom**: two enumerators on the same team accidentally captured the same case ID (e.g., the STL's day-allocation overlapped or an enumerator copied a tablet image after partial sync).

**Recovery**:

- **Detection**: `synctime()` (Khurshid 2025-02-20) timestamps every case server-side; a case ID with two distinct `synctime` rows in MySQL is the alert signal.
- **Server-side conflict policy for case data**: **last-write-wins** by `synctime`, with the loser archived in a `cases_archive` table by an admin-run script. The archive is for traceability; analytic exports use the winner.
- **Server-side policy for user records**: admin-only updates; enumerators cannot edit user records, so user-record conflicts shouldn't happen. If they do (e.g., two admins edit the same user), it's an ops error and the resolution is by hand.
- **Prevention**: enforce STL day-allocation (`CASE_SEQ` ranges per enumerator per facility) so the case ID space is partitioned at issue-time. Form-level guards on `CASE_SEQ` (Section 7) catch the common case before sync.

### F-06: GPS unavailable / inaccurate

**Symptom**: `Capture-Helpers.ReadGPSReading(120, 20)` returns after 120 s with no fix or `accuracy > 20m`.

**Recovery**: the helper writes the best available reading + sets a `GPS_QUALITY` flag (`good` / `degraded` / `none`). The case still saves; QC flags `degraded` / `none` cases for follow-up. Enumerator can re-trigger the GPS capture on the form (the trigger item resets to `notappl` after each capture per Khurshid's `Capture-Helpers` pattern — see `[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/GPS and Photo Capture|GPS and Photo Capture]]`).

### F-07: Verification photo capture cancelled

**Symptom**: enumerator hits the photo trigger, the camera opens, they cancel.

**Recovery**: helper returns failure; trigger resets so they can re-arm. A case with `VERIFICATION_PHOTO_FILENAME` blank at end-of-interview blocks save via an `errmsg` on the FIELD_CONTROL block (HARD validation per Khurshid 2022-06-26).

---

## 12. Decisions still open (TODOs)

The architecture above is committed; the following decisions are not yet final and will be resolved before main fieldwork.

| TODO | What's not decided | Who decides | When |
|---|---|---|---|
| Concrete CSWeb host | ASPSI office static IP vs. cloud VPS (e.g., DigitalOcean Manila region or AWS ap-southeast-1). Static IP gives the lowest latency for ASPSI ops but exposes the office network; cloud gives clean separation but adds a per-month cost. | ASPSI ops + Carl | Before Phase 8 build (target: end of May 2026) |
| Encryption-at-rest standard | Protocol V2 has "encryption-at-rest" as a placeholder. Options: (a) tablet-level Android Encrypted Storage default (existing); (b) per-app SQLCipher wrapper around `.csdb`; (c) full-disk encryption mandate per tablet + remote-wipe MDM. | DOH-PMSMD (data-protection officer) + ASPSI | Before SJREB submission |
| Tablet model + spec | Flagged to Juvy on 2026-05-04; spec must hit GPS accuracy + camera + battery + Android version (must run CSEntry 7.7+) + screen size for roster forms. | Juvy (procurement) + Carl (technical review) | Before training Aug 1st week |
| Backup-to-Dropbox policy | Whether to keep Dropbox as a documented fallback, or delete the channel entirely once CSWeb is proven stable. Argument for keeping: cheap insurance. Argument for deleting: every fallback is a security surface; one channel is easier to audit. | Carl + ASPSI ops | Mid-fieldwork retro |
| 7-dialect translation drop-in | ASPSI's Filipino + 5 dialect translations are not yet delivered (per the ASPSI translation pipeline memory). Build accepts drop-in locales but the locale list is a placeholder. | ASPSI translation team | Before Phase 9 pretest |
| Patient-listing CSPro mini-app | F3 currently uses paper F3b listing -> enumerator hand-types `F3_FACILITY_ID`. A CSPro mini-app that auto-fills it from a sampled patient roster is post-MVP wishlist. | Carl (post-MVP) | After main fieldwork |
| `F3_FACILITY_ID` retention | Once the 12-digit case-ID convention lands, `F3_FACILITY_ID` becomes redundant (the first 9 digits of every F3 case ID *are* the facility ID). Decision: retire vs. keep as a denormalized convenience field. Leaning retire to avoid drift. | Carl | At case-ID convention implementation sprint |
| Working-File case-ID variant | The Survey Manual Working File (Kidd, 2026-05-06) decomposes the last 5 digits as `FF-CC-CCC` (respondent type 2 + sequence 3) using `11/22/33/44` doubled-digit codes; Carl's brief + Appendix D use `FF-CCC` (facility 2 + sequence 3 with the active/replacement/refused partition). Reconciliation pending. | Kidd (manual owner) | Before training |

When any of these resolve, update this document's `last_updated` and edit the relevant section to lock in the decision (and the open-question entry retires).

---

## Next

- Read [[01-Roles-and-Handoffs]] for who does what across phases (RACI per phase, handoff matrix, escalation paths, ASPSI comms protocol).
- Read [[02-Phase-0-2-Foundation]] for project scaffolding, source ingestion, and the tool-knowledge baseline.
- For the per-build runbook (forms, PROC, FIELD_CONTROL, GPS+photo, durable resume, dynamic value sets), jump to [[04-Phase-6-Build-CAPI-App]].
- For server provisioning, tablet bring-up, and PFF packaging, see [[06-Phase-8-CSWeb-and-Tablets]].
