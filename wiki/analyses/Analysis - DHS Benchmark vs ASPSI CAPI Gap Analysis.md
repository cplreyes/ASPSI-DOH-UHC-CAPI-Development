---
type: analysis
date: 2026-07-03
inputs: "[[Source - DHS-Data-Processing CSPro CAPI Benchmark]]"
tags: [benchmark, gap-analysis, dhs-program, supervisor-app, field-qa, versioning, roadmap]
---

# Analysis — DHS Benchmark vs ASPSI CAPI: Comparison & Gap Analysis

Comparison of **The DHS Program's standard CSPro suite** (`DHS-Data-Processing`, the system
behind PSA's NDHS 2022 — 40 years of program maturity, adapted to 90+ countries) against the
**ASPSI UHC Year-2 CAPI system** (F1/F3/F4 + Supervisor Hub + F2 PWA, built Mar–Jul 2026,
one developer + AI). Evidence = the mirrored repo at
`raw/psa-cspro-capi-reference/github/dhs-data-processing/` (file paths cited inline).

The framing matters: DHS optimizes for **reusability across countries** (hence a template
adapted by hand per survey); we optimize for **one survey built fast and regenerated cheaply**
(hence generators). Several "gaps" below are DHS solving problems we don't have — and vice
versa. Emphasis is on what's worth adopting for **Aug training / Sep rollout**.

## 1. Side-by-side comparison

| Dimension | DHS standard suite | ASPSI UHC Y2 | Verdict |
|---|---|---|---|
| **Roles** | 4: interviewer, supervisor, biomarker, central office | 3: enumerator, supervisor (hub roles), HQ via CSWeb | Parity (no biomarkers in UHC Y2) |
| **App topology** | Role menus (DCMenu/SupMenu/BioMenu/CentralMenu) + ~24 single-purpose micro-apps launched via PFF params (`Library/UpgradeRoutines.apc` registry) | Hub (LoginApp→MenuApp htmldialog) + 3 instruments via `execpff` sibling pffs | Same pattern, independently converged |
| **App-list UX** | Only the menu is visible — child pffs carry `ShowInApplicationListing=Never` + `OnExit=` chains back to the menu (`CC81NEW/Superv/SupMenu.apc`) | Hub AND all 3 instruments visible in CSEntry's list | **Their win** — cleaner operator surface (G3) |
| **Development model** | Template-adaptation: copy standard package, hand-edit dictionary→forms→logic at `!!!` markers; 60-page DPP-02 procedure | Generator-first: Python emits dcf/apc/fmf/qsf; static gates (preflight, verify_questions, fmf_block_check) | **Our win** — regeneration beats re-adaptation |
| **Logic reuse** | Runtime include library (`Library/*.apc`: EntryFunctions, SyncReportLib, UpgradeRoutines…) | Generation-time `cspro_helpers.py` | Equivalent, different layer |
| **Versioning** | Internal integer counters in text files (`UserVersionCtrl.txt` device vs `CSWebVersionCtrl.txt` server); invisible to fieldworkers | SemVer in `versions.json` SSOT, tester-visible on 3 surfaces (app list, title bar, QN screen), VERSIONING.md | **Our win** on semantics/visibility |
| **Update distribution** | **Menu-integrated**: "5 Receive system updates from supervisor" (`CC81NEW/Entry/DCMenu.apc`); .pen/.mgf/.dat payloads zipped (7za), relayed HQ→supervisor→Bluetooth→interviewer, routed per-role by the app registry; non-contiguous numbers OK | CSWeb redeploy + CSEntry ⋮-Update (unreliable — Dropbox-token crash, stale-build false negatives) or remove+re-add, instructed via patch notes | **Their win** on mechanics (G2) |
| **Case assignment** | `Superv/AssignHH` + household **sharing between interviewers**; assignment-overwrite races fixed in CC81NEW | Assignment dict + AS_*.dat per enumerator, roster-gated | Parity core; sharing = gap (G5) |
| **Re-interview / QC** | Supervisor-driven re-interview workflow (`ListRi`, RemeasSel) | None | Gap (G4) |
| **Field QA / monitoring** | **FCT field-check tables run BY THE SUPERVISOR on-device**: SQL over the CSPro **paradata** log (`message_event JOIN event`), durations vs per-questionnaire norms (short/long × members/sections), age-displacement checks at eligibility bounds (FAGE15/FAGE50), response rates (ARESULT/AHRESULT), transmit dates (`Superv/FCT.ent.apc`) | HQ-side only: CSWeb Sync Dashboard + Map Report (15-min cron); nothing in the supervisor's hands | **Their win — biggest gap (G1)** |
| **Paradata** | Captured and queried operationally | Not enabled | Gap, prerequisite for G1 (G7) |
| **Disposition / result-of-visit** | `FixResult` app + result codes feeding FCT response rates | Break-off → Result-of-Visit + off-form CASE_DISPOSITION (#515/#561) | Parity |
| **Transport** | Android Bluetooth in menu logic (syncconnect/syncserver in CC81NEW menus) + SyncCloud/CSWeb upward; `Utility/BTServerPC` | CSWeb direct per device; device-to-device Bluetooth spiked (C2, 2026-06-25) but not in production flow | Parity-capable; theirs is production-hardened |
| **Multi-language** | `.mgf` message files + QSF text; userbar "Lang" button | QSF multi-language via build switcher; translations partially delivered (ASPSI lane) | Parity mechanism; content pending |
| **Docs & training** | Role manuals + numbered DPP 00–06 procedures + **9-module Master Trainer package with example tests and a QuizApp** (`Standard-8/`) | CAPI Manual (17 sections, PDF), tester install/test guides, hub guide | Their training packaging is richer (G8) |
| **Central-office processing** | In-suite: HHEdit8/INEdit8 editing batches, standard Recode + validation, batch Tables, Wealth index | CSWeb breakout ETL + Codebook + Stata 12 do-file harness (197-table plan) | Covered differently — ours matches PSA's actual output commitments |
| **Deploy/ops automation** | Manual: Word procedures + .bat helpers (`Utility/upgradePC`) | Automated: .csds spec route, `auto_deploy.py`, Designer compile drivers, `stamp_version.py` drift checks | **Our win** |
| **UI layer** | Native CSPro value-set menus + userbar | Styled htmldialog (dual-bridge CSPro.*/CS.UI), role-filtered | **Our win** (modernity), theirs wins on zero-maintenance |
| **Extra capture** | GPS in CollectHH; biomarker double-entry validation | Verification photos (binary dict items), PSGC case-key hard gate | Different needs; PSGC gate is ours alone |

## 2. Gap register — what the benchmark has that we lack

| # | Gap | Evidence | Impact for UHC Y2 | Effort | When |
|---|---|---|---|---|---|
| **G1** | **Supervisor-side field-check tables** (FCT): durations vs norms, response rates, age displacement, per-interviewer | `Superv/FCT.ent.apc` (79 KB) | **HIGH** — this is in-field data quality during Aug–Sep collection, and feeds the monitoring-dashboard commitment (extension basis, 2026-06-22 mtg). Supervisors catch problem interviews in-cluster instead of HQ noticing days later | Medium — hub already has `report.html` + Sync-Report plumbing; needs G7 first | Build in **Aug training window** |
| **G2** | **Menu-integrated update check** ("Receive system updates" as a hub menu action) | `CC81NEW/Entry/DCMenu.apc`, `Library/UpgradeRoutines.apc` | HIGH — kills the ⋮-Update reliability pain. Honest scoping: a **check-and-prompt** (hub compares device build vs server `versions.json`, tells the user exactly which apps to update) is cheap; full auto-apply is harder because our apps are CSWeb-package-installed, not file-deployed .pens like DHS's | Low (check+prompt) / High (auto-apply) | Check+prompt for **Sep rollout** |
| **G3** | **App-list hygiene**: `ShowInApplicationListing=Never` on instruments + `OnExit=` chain back to the hub menu | pff blocks generated in `CC81NEW/Superv/SupMenu.apc` | Medium — production polish: fieldworkers see ONE entry (the hub), can't launch instruments outside the login/assignment flow. Caveat: during UAT testers deliberately launch instruments standalone — this is a **production-mode toggle**, not a UAT change | **Low** (pff keys in `build_hub_apps.py` / instrument pffs) | Decide at rollout cutover |
| **G4** | Supervisor-driven **re-interview workflow** (QC re-interviews of completed households) | `Superv/ListRi`, CC81NEW readme | Medium — standard NSO QC; SSRCS-grade fieldwork usually spot-reinterviews | Medium | Rollout, if ASPSI wants it in the QC protocol |
| **G5** | **Case sharing / reassignment between enumerators** mid-cluster | CC81NEW readme ("households received from other interviewers") | Medium — absence bites when an enumerator drops out mid-facility/EA | Medium — Assignment dict partially supports; needs hub UX + data-merge rules | Rollout |
| **G6** | **Data-repair utility** for damaged device data | `Utility/DataRepairAndroid/DataRepair.apc` | Low-Med — our current answer is clean-reinstall (#733/#735); a repair path preserves partial work | Medium | As-needed; rollout support kit |
| **G7** | **Paradata capture not enabled** (timestamps, events) | FCT queries `message_event`/`event` tables | Enabler for G1 + duration norms; also post-hoc interview-quality evidence | **Low** (pff/app setting + storage check) | **Enable at pretest** — pretest data calibrates the duration norms G1 needs |
| **G8** | **Training curriculum packaging** (modules, example tests, QuizApp — trainees quiz on-device, supervisors receive updated quizzes) | `Standard-8/`, "Receive updated quiz" menu item | Medium — Aug training is contractual; a hands-on module set beats lecture slides | Content-heavy, low-tech | Aug training prep; pairs with full-Survey-Manual scope |
| **G9** | Interview **duration norms** (expected short/long per questionnaire) | FCT norm constants | Small but sharp QC lever; norms must be measured, not guessed | Trivial once G7 pretest paradata exists | Derive from pretest |

Not applicable: biomarker double-entry (no biomarkers), wealth-index batch (not in scope),
central editing batches (covered by ETL+Stata down our pipeline).

## 3. Reverse gaps — what we have that the benchmark lacks

Validation of our build (and the honest answer to "are we behind a 40-year system?" — no,
we're differently shaped): **generator pipeline with static gates** (their DPP-02 hand-adaptation
is the exact failure surface we deleted) · **tester-visible SemVer** (their versions are internal
integers; nothing on their screens says what build is running — our title-bar/QN-footer surfaces
are ahead of the benchmark) · **automated deploy** (.csds route + drivers vs Word procedures) ·
**styled htmldialog UI** · **HQ web dashboards** (Sync Dashboard, Map Report) · **PSGC case-key
hard validation at entry** · **a PWA instrument** (F2) with its own CI · **automated UAT triage
loop** with versioned patch-note comms.

## 4. The CC81NEW refactor — techniques worth benchmarking (deep-read 2026-07-03)

`CC81NEW/` is the DHS team's **own refactor** of their standard system (the "Android Menu
System", CSPro 8.1 era) — i.e., what *they* decided was worth fixing after years of field use.
Headline: **the interviewer side collapsed from 9 apps to 3** (DCMenu + LstQuest + quizapp);
WrkElig, dup-checkers, FixResult et al. were absorbed into menu logic — the same
consolidation our hub made on day one. The concrete techniques inside:

| # | Technique | How they do it | What it's worth to us |
|---|---|---|---|
| **T1** | **`publishdate()` as an un-fakeable build stamp** | Their refactor ALSO added version display: `getversion()`/`ShowPubDate()` show `publishdate()/100` (the deployed .pen's publish timestamp); SupMenu logs publishdate + upgrade numbers on update | Complements our SemVer: `publishdate()` is intrinsic to the deployed .pen, so it can't drift from what's actually installed. A hub diagnostics line "vX.Y.Z · pen published <date>" would catch a deploy-without-bump or stale-build instantly. Cheap, high trust value |
| **T2** | **Unified case list with owner/status selectors** | `forcase` over an operational eligibility dict (owner, result, completion status) merged with incoming assignments (`loadcase` probe = "assigned but not begun"), one `showarray` picker; selector modes: my-open / my-completed / shared-from-others / all | The pattern for our assignment→case flow: enumerator sees ONE list of their assigned QNs with live status, taps to open. Kills the new-vs-modify navigation and the "which case was I on?" confusion |
| **T3** | **Runtime PFF generation with per-launch parameters** | Menus `filewrite` the child .pff at launch (~200+ writes/menu): `[DataEntryInit]` OperatorID=, StartMode=ADD vs MODIFY chosen per case selection | We generate pffs at build time (fine for static launches), but runtime generation enables **launching an instrument directly INTO a case** — e.g., F3 opens with the assignment's QN prefilled instead of the enumerator typing 12 digits (a known error source, PSGC gate notwithstanding). Pairs with T2 |
| **T4** | **Bluetooth pairing discipline by device name** | `checkBTId`: `setbluetoothname(edit("9999", workercode))` — every device's BT name IS its fieldworker code; syncserver/syncconnect target by name, so you can't sync with the wrong team's tablet | If the C2 Bluetooth spike ever productionizes, adopt this first — it's the difference between a demo and a field-safe transfer protocol |
| **T5** | **Paradata logistics at cluster close** | SupMenu: `paradata(concat, …)` merges all interviewers' `.cslog` per cluster → `compress` → `SyncFile(PUT, …, CSWeb)` | The missing half of our G7: capturing paradata is a setting, but *collecting* it needs a path. Theirs: supervisor concatenates + pushes to CSWeb — works verbatim with our stack |
| **T6** | **Self-service data-repair in the menu library** | `MenuFunctions.apc`: `CleanIndex` (delete `*.csidx`), `fixdata` (strip corrupt/blank lines + invalid record IDs against a whitelist), `FindDups(autodelete)` + `viewtext` report | `CleanIndex` speaks directly to our #733/#735 partial-save lifecycle bug — their standard fix for index corruption is a menu action, not a reinstall. A hub "repair data" action = lighter-weight than our clean-reinstall path |
| **T7** | **On-device styled HTML reports** | `TableFunctions.apc` + `TablesStyle.css` shipped in Entry; `viewtext()` renders generated HTML/text reports in-menu | Confirms the implementation path for G1: generate the field-check tables as styled HTML shown from the hub — exactly the plumbing our `report.html` already has |

Also notable: the new menus dropped `savesetting/getsetting` for state (operational dicts +
files instead), and the update flow ("Receive system updates from supervisor") only copies
files **newer than the device's counter**, tolerating skipped versions — robustness details
worth copying if we build G2.

## 5. The Khurshid benchmark — adoption status (cross-check 2026-07-03)

The third reference system: **Arshad Khurshid's "101 - Applications"** (CSPro 7.7) — his
teaching-grade modernization of the same DHS login→menu→sync pattern, ingested 2026-06-27
(`supervisor-hub/reference/khurshid-101-applications.md`, source vendored alongside). Where
CC81NEW is the DHS team's *operational* refactor (consolidation, paradata, updates), Khurshid's
is the *mechanism* refactor — modern CSPro idioms replacing the old machinery. Status of his
ranked adoption list against the as-built hub:

**Adopted since the ingest (the whole high-value tier):**
- ⭐ **CSWeb relay in logic** (`config` + `syncconnect(CSWeb) → syncdata(PUT)`) — built into
  MenuApp's "Relay to CSWeb" (credited to him in the apc comments), device-confirmed 2026-06-27.
- ⭐ **`InputData=|type=None`** — both hub pffs carry it (no case list; login opens straight
  to the username field).
- **HTMLDialogs** — adopted and surpassed: his `choice.html` bridge became our styled
  `menu.html`/`report.html`, upgraded to the 8.1 dual-bridge (CSPro.*/CS.UI + accessTokens),
  which his 7.7 material predates.

**Still unadopted (the production-hardening tier — the live Khurshid benchmark items):**

| # | Item | His mechanism | When it matters |
|---|---|---|---|
| **K1** | **Encrypted roster** | `SecurityOptions` on the roster dcf/csdb vs our plaintext `.dat` (now carrying real `uhc26*` creds in the deployed bundle) | Rollout hardening — do before real fieldworker creds ship at scale |
| **K2** | **Device-bound login** | `getdeviceid() = DEVICE_ID` roster check on Android (Windows exempt) — turns our UX-only login (D4) into real security | ASPSI go/no-go once tablets are assigned to named fieldworkers |
| **K3** | **`SUPERVISOR_ID` in the roster** | explicit enumerator→supervisor link (we model teams only) | When ASPSI's real roster lands; feeds per-team views (pairs with G1) |
| **K4** | **Excel→CSPro roster import** (`104/105_Excel`, `.xl2cs`) | tooling to build the roster from a spreadsheet | Same trigger — ASPSI still owes the real-names roster; this is the import path |
| K5 | Per-login data files (`HH_<id>.csdb`) | isolate each enumerator's cases pre-merge | Low priority — our key-based `syncdata` merge is proven |

No newer "Khurshid refactor" exists to mine: 101-Applications *is* his refactor of the DHS
pattern, and the hub has already absorbed its mechanism layer. His corpus (74 transcripts,
Learning System) is teaching narration of the same system, not a newer codebase.

## 6. Per-CSPro-tool structure — refactoring candidates for OUR build (2026-07-03)

Carl's framing: not "what features do they have", but **how the system is developed and
structured per CSPro tool** — is our development model structured the way the benchmarks
(DHS, Khurshid, and the official CSPro 8 examples) structure theirs, and where is a refactor
warranted? Verified against the artifacts, tool by tool:

| CSPro tool | Benchmark practice | Ours today | Verdict |
|---|---|---|---|
| **App spec (.ent)** | Multi-file logic: DHS 7.x `[AppCode] Include=..\Library\*.apc`; **official CSPro 8 CAPI Census example**: `"code": [{main}, {"type":"external","path":"../External-Logic/Sync.apc"}, …]` | Single `"code": [{main}]` — one monolithic generated .apc per app | **Refactor R1** (below) |
| **Logic (.apc)** | Shared runtime **Library/** (MenuFunctions, UpgradeRoutines, SyncReportLib…) included by every app; hand code lives in real .apc files | Generation-time reuse via `cspro_helpers.py` (our win — keep); BUT hand-written logic lives in **`EXTRA_PROCS` triple-quoted Python strings** inside the generators (F3 `generate_apc.py:943`) — no CSPro syntax highlighting, hard to lint/diff/review | **Refactor R1a/R1b** |
| **Messages (.mgf)** | Real numbered, **multi-language** message files (DHS DCMenu.mgf = 19 KB of numbered messages; CheckID.mgf same) | 67-byte generated **stubs**; all runtime messages are inline English literals — F3 alone has **236 `errmsg("…")` calls** | **Refactor R2 — the big one** |
| **Dictionaries (.dcf)** | Central `Dicts/` shared by relative path across apps; ~26 operational dicts | Per-instrument generated dcfs + `shared/` PSGC + hub snapshot copies (deployment-forced — instrument pffs on device resolve siblings; snapshots regenerated by `build_hub_apps.py`, drift-managed) | Keep — copies are a deployment reality, not structure debt |
| **Forms (.fmf)** | Hand-maintained per app (their weakest tool — no benchmark lesson to take) | F3/F4 generated + optimize pass; **F1 hand-fmf + inject_blocks.py** (the known asymmetry); skip-boundary rule lives only in F1's plan rules; `fmf_block_check` has the Section-N false-positive gap | **Refactor R3** (internal consistency, benchmark-independent) |
| **Question text (.qsf)** | Hand-edited / QSF editor + macros | Generated from versioned sources, multi-language, build-footer stamped | Keep — ahead of all three benchmarks |
| **PFFs** | Runtime-generated with per-launch params; `ShowInApplicationListing`/`OnExit` hygiene | Build-time generated/stamped | Already covered as T3/G3 |
| **Batch (.bch) / tables (CSTab)** | In-suite editing batches, FCT, batch tables | Python static gates + ETL + Stata do-files (PSA-committed outputs) | Keep — deliberate; FCT arrives via T7 HTML, not CSTab |
| **Deployment (.csds/CSWeb)** | Manual Word procedures | Automated spec route + drivers + drift checks | Keep — ahead |
| **Repo layout** | Role/tool-centric (Entry/ Superv/ Dicts/ Library/ Utility/) | Instrument-centric (F1/ F3/ F4/ supervisor-hub/ shared/ automation/) — matches our deploy unit (one CSWeb package per instrument) | Keep instrument-centric; add the one missing shared home: `library/` (R1b) |

### The refactor register

| # | Refactor | What changes | Why / risk | When |
|---|---|---|---|---|
| **R1a** | **Hand procs out of Python heredocs** | `EXTRA_PROCS` bodies move from triple-quoted strings in `generate_apc.py` to real `.apc` fragment files (e.g. `F3/procs/q148_conditions.apc`) that the generator reads and splices verbatim | Pure build-time change — generated output byte-identical, so ZERO CSPro/deploy risk; hand logic becomes editable/diffable/reviewable as CSPro code | Anytime, even during freeze (output-identical = provable by diff) |
| **R1b** | **Shared external-logic library** | New `deliverables/CSPro/library/*.apc` wired as `"type":"external"` code entries (the official 8.x CAPI Census pattern) for the **hand-written operational layer**: hub menu functions, and the incoming G1 (field-check), G2 (update-check), T1 (publishdate line), T6 (CleanIndex) code — shared between hub and instruments without duplication | Follows the Census Bureau's own 8.x structure; keeps generated per-instrument logic generated (our win) while giving the growing hand-written layer a real home | Set up when G1/G2 builds start (Aug) — don't retrofit existing generated procs |
| **R2** | **Numbered multi-language messages** | Generators emit `errmsg(NNN)` + a real `.mgf` with numbered messages instead of 236+ inline English literals; translations ride the same pipeline as the qsf | **Field-facing**: enumerators currently get translated questions but ENGLISH validation/error messages — fil/ilo/hil messages need this refactor first. Incremental path: number new messages first, migrate sections opportunistically | Start post-pretest; complete before the translation pipeline finalizes |
| **R3** | **Normalize the FMF story** | Port F1's skip-boundary plan rule into the F3/F4 `generate_fmf.py` derivers (known latent gap); reconcile `fmf_block_check`'s Section-N rule (26 standing false positives desensitize the gate); longer-term: fold F1's inject_blocks into a real generator | Internal consistency — our only tool where the three instruments diverge structurally; a desensitized gate is a real QA risk | Post-pretest; before the next fmf-touching feature |

Priority: **R2 > R1a > R1b > R3**. R2 is the only one testers/enumerators will ever *see*;
R1a is free and improves every future patch; R1b rides the Aug feature work; R3 clears
standing debt before it bites.

> **Status 2026-07-03 — Option B data layer + R1a BUILT** (Carl's go, same day):
> `deliverables/CSPro/data/` now holds the four dataset pipelines — `psgc/` (PSA 1Q-2026
> xlsx + parse + build, PSGC-VERSION.md provenance, 18/117/1,658/42,010 rows), `roster/`
> (gitignored `roster-source.csv` — credentials OUT of `build_hub_apps.py`; template +
> K4 `import_roster.py`), `assignments/` (tracked R6 fixtures CSV), `facilities/` (DOH
> masterlist xlsx rescued from Downloads into a gitignored `source/`, builder relocated
> from automation/). Hub build reads the CSVs (single-writer preserved). **R1a done:**
> F1 `CONTROL_PROCS` + F3/F4 `EXTRA_PROCS` extracted to `F<n>/procs/*.apc` fragments.
> **Every deployed artifact verified byte-identical** (psgc ×8, facility ×2, hub full-tree
> hash, apc ×3); gates green; `stamp_version show` = no drift → no bump, nothing deployed
> (pretest freeze holds). Still open: R2, R1b (Aug), R3, K1 (Sep).

## 7. Recommendations (timeline-aware)

1. **Nothing changes before the pretest gate** (fleet is frozen pretest-ready; gate ~Jul 5).
2. **At pretest: enable paradata (G7)** on one or all devices — zero questionnaire impact,
   and pretest becomes the calibration set for duration norms (G9).
3. **Aug training window: build the supervisor field-check layer (G1)** into the hub
   (report.html extension or CSPro-tables page): response rates by result code, duration
   outliers vs pretest norms, per-enumerator completion, last-transmit. This is also the
   strongest concrete answer to the "monitoring dashboard as extension basis" expectation.
   Implementation path proven by the benchmark: T7 (styled HTML via TableFunctions-style
   generation) + T5 (supervisor-side paradata concat → CSWeb). Package training as
   modules + quiz (G8) alongside the manual. If assignment-UX friction shows up in
   training, T2+T3 (unified case list + case-prefilled instrument launch) is the fix.
4. **Sep rollout: hub "check for updates" action (G2, check+prompt form)** + decide the
   production-mode app-list hygiene toggle (G3) + the trivial T1 diagnostics line
   (`vX.Y.Z · pen published <date>` via `publishdate()`) + **K1 encrypted roster** before
   real fieldworker credentials ship at scale. Case-sharing (G5), re-interview (G4),
   data-repair (G6, or the lighter T6 CleanIndex action), and K2 device-bound login go in
   only if ASPSI's QC/security protocol calls for them — surface as go/no-go.
5. **When ASPSI delivers the real fieldworker roster**: K3 (`SUPERVISOR_ID` hierarchy) +
   K4 (spreadsheet→roster import tooling) ride that import.
6. Keep ignoring what DHS solves that we don't have: template adaptation, biomarkers,
   multi-country parameterization.
