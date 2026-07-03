---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/psa-cspro-capi-reference/github/dhs-data-processing]]"
date_ingested: 2026-07-03
tags: [benchmark, dhs-program, cspro, capi, supervisor-app, field-operations, versioning, ingest-psa-research]
---

# Source — DHS-Data-Processing: The DHS Program's standard CSPro CAPI suite

Full working tree of [DHSProgram/DHS-Data-Processing](https://github.com/DHSProgram/DHS-Data-Processing)
(master, 836 files, 238 MB, last upstream update 2026-01), mirrored at
`raw/psa-cspro-capi-reference/github/dhs-data-processing/`. This is **the standard application
package The DHS Program adapts for every DHS survey worldwide** — including the **2022 Philippine
NDHS run by PSA**, making it the closest professional benchmark to our F1/F3/F4 + Supervisor Hub
build. Ingested as the benchmark for assessing *how a mature NSO-grade CAPI system is developed*.

## System architecture (what runs in the field)

**Four-role, menu-driven, micro-app architecture.** Each role gets a menu application that
launches single-purpose CSPro apps via PFF manipulation (write parameters into the target's
`.pff`, then launch — same `execpff` pattern as our hub):

| Role | Menu | Micro-apps (each its own .ent/.apc/.qsf/.mgf) |
|---|---|---|
| Interviewer | `Entry/DCMenu` (53 KB apc) | CollectHH, CollectIN (the questionnaires), ListElig, WrkElig, FixResult (result-of-visit), ListNotes, LstQuest, ChkHHDup |
| Supervisor | `Superv/SupMenu` | **AssignHH** (case assignment), CheckID, ChkBIDup/ChkINDup, **FCT** (field-check tables — in-field quality tabulations), SelectHH, re-interview apps (ListRi, RemeasSel) |
| Biomarker tech | BioMenu | CollectBIO, HHEligible, ListEligBIO, BarcUsed, remeasure apps |
| Central office | `Central/CentralMenu` | FldCk8 (field-check batch), HHEdit8/INEdit8 (editing batches), LstClust |

A hard-coded **24-app registry** (name → role) in `Library/UpgradeRoutines.apc` routes update
payloads per role. ~26 **auxiliary dictionaries** (`Dicts/`) carry the operational state:
Menu.dcf (dummy menu dict), Control/ContSup, Transmit, Clusters, EligIndv, HHListing, GPS,
SCReport (sync reporting), Weights, WealthIndex — the same pattern as our
UserRoster/Assignment/AS_*.dat, at larger scale.

**Shared runtime library** (`Library/`): includable `.apc` modules — EntryFunctions,
HTMLFunctions, SyncReportLib (56 KB, versioned header "Version 1.0.5 — 2022-04-26"),
TableFunctions + TablesStyle.css, UpgradeRoutines, DPCollect, RecodeFunctions, Anthrop
(589 KB anthropometry z-scores). Their reuse mechanism is **runtime include**; ours is
**generation-time Python helpers** (`cspro_helpers.py`).

**Transport:** device-to-device **Android Bluetooth** for supervisor↔interviewer case flow
(assignments out, completed cases + upgrades back) — validated by our own C2 Bluetooth spike —
plus `Utility/BTServerPC` (PC as Bluetooth server), and **SyncCloud/CSWeb** upward to HQ
(`Utility/SyncCloud setup/` has the Conduit server + data-pipeline docs). GPS capture is
built into CollectHH.

## How it is developed (the assessment target)

1. **Template-adaptation, not generation.** Countries copy the standard package into a country
   folder and hand-modify: dictionary first, then forms, then logic. `DPP 02 — Preparing the
   CAPI Data Entry System` (in `Docs/`) is the 60-page procedure: grep for `!!!` markers =
   "adjust here", update country functions (ValRelat, LevelYears), delete optional modules,
   run the **A2Q** tool on application files, maintain a survey **`.IN` parameter file**.
   Contrast: our build **generates** dcf/apc/fmf/qsf from Python per instrument — no
   hand-adaptation surface, no `!!!` markers to miss.
2. **Hand-written logic at scale, with documented conventions.** Big single .apc per app
   (DCMenu 53 KB; FCT.ent.apc 79 KB), heavy inline comments, a written "Good Programming
   Practices" section (indentation, commenting) inside DPP 02. No tests beyond an
   `Entry/Test.bch` batch app and "Testing your Programs" as a manual procedure.
3. **Multi-language via CSPro-native mechanisms**: `.mgf` message files per app + QSF
   question text; runtime `SetLanguage()` from a userbar "Lang" button (we do the same via
   the build switcher; their messages are also translated, ours partially).
4. **Upgrade/versioning machinery** (`Library/UpgradeRoutines.apc` + `Utility/upgradePC`):
   plain **integer build numbers** in text files — `UserVersionCtrl.txt` on device vs
   `CSWebVersionCtrl.txt` on server; payloads are compiled `.pen`/`.mgf`/`.dat` files copied
   into role-appropriate folders by the app registry; CC81NEW allows **non-contiguous
   upgrades** (5→7 without 6). Distribution rides the supervisor: HQ → supervisor → Bluetooth
   → interviewers. *Ours is richer semantically (SemVer + tester-visible surfaces) but theirs
   closes the loop mechanically — the menu itself checks & applies upgrades in-app, no
   manual ⋮-Update step.*
5. **Generational refresh in-repo:** `CC81NEW/` (CSPro 8.1 era) documents the modernization:
   micro-apps absorbed INTO the menus (WrkElig, dup-checkers gone as standalone apps),
   assignment-overwrite races fixed, interviewer sees ONE unified case list (no separate
   new/partial/modify options), supervisor-driven re-interviews added. **The same
   consolidation instinct as our hub** — fewer apps, more logic in the menu.
6. **Documentation as a first-class deliverable** (`Docs/`, 79 MB): CAPI Interviewer /
   Supervisor / Biomarker / HH-Listing manuals, **CAPI Central Office System**, and the
   numbered **DPP 00–06 procedure series** (tablet setup → prepare entry system → data
   finalization → recode validation → batch tables → tables editor). Plus the
   **Standard-8 Master Trainer Package** (120 MB): a 9-module CAPI training curriculum with
   example tests and a QuizApp — training materials ship WITH the system.
7. **Full lifecycle in one repo:** collection (Entry/Superv) → field QA (FCT) → central
   editing (HHEdit8/INEdit8) → Recode (standard recode + validation) → Tables (batch CSPro
   tables) → Wealth index → exports. Our equivalent spans CSPro + CSWeb breakout ETL +
   Stata do-files.

## Benchmark deltas (first pass — for the upcoming assessment)

**They have, we don't (candidates to adopt):**
- **FCT (field-check tables)**: supervisor runs quality tabulations on-device mid-fieldwork —
  age heaping, response rates, eligibility counts — catching interviewer problems in-cluster.
  We have nothing equivalent (our Sync Report is HQ-side, not supervisor-side).
- **Menu-integrated upgrade check/apply** (no reliance on CSEntry's flaky ⋮-Update).
- **Supervisor-driven re-interview workflow** (ListRi) + **household sharing** between
  interviewers mid-cluster.
- **DataRepairAndroid** utility; duplicate-case repair procedures (trainer Module 7).
- Training curriculum + QuizApp packaged with the system.

**We have, they don't (validated choices):**
- **Generator-first build** (their DPP-02 adaptation pain — hand-editing logic per survey —
  is exactly what our Python generators eliminate).
- **Semantic, tester-visible versioning** (their integer counters are internal-only; nothing
  shows the build on-screen — our pff-Description title bars + QN-screen footer are ahead).
- **Styled htmldialog UI** (hub menu) vs their native value-set menus + userbar.
- **Automated deploy pipeline** (.csds route, drift checks, compile drivers) — their deploys
  are manual procedures in Word docs.
- Web dashboards (Sync Dashboard, Map Report) on-box at CSWeb.

**Same pattern, independently arrived at:** roster/login-gated role menus; PFF-parameter
app launching; auxiliary dicts for operational state; Bluetooth supervisor relay;
result-of-visit/disposition capture (their FixResult ≈ our break-off + CASE_DISPOSITION);
partial-save handling; per-cluster close-out discipline.

## Pointers

- Repo mirror: `raw/psa-cspro-capi-reference/github/dhs-data-processing/`
- Haul manifest: `raw/psa-cspro-capi-reference/README.md`
- Related: [[Source - CSPro Android CAPI Getting Started]], [[Source - CSPro Android Data Transfer Guide]],
  [[Source - CSWeb Users Guide]] · NDHS 2022 Final Report (CAPI methodology): `raw/psa-cspro-capi-reference/ndhs-2022/`
