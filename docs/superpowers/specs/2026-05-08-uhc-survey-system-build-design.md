---
title: UHC Survey Year 2 — Full System Build (CSPro CAPI + Local CSWeb)
type: design-spec
date: 2026-05-08
status: draft
author: Carl Patrick L. Reyes (with Claude)
mentor_alignment: khurshid-arshad (CAPI / Survey Research)
scope: β-3 (full system, Myra-hold overridden for spike)
follow_on: writing-plans skill (implementation plan)
---

# UHC Survey Year 2 — Full System Build (CSPro CAPI + Local CSWeb)

End-to-end CAPI build covering all paper-origin instruments (F1, F3, F4) plus their listing forms (PLF, F4 Barangay Listing) plus the chain glue (login app + role-conditional menu app), compiled to seven `.pen` packages, deployed to a local CSWeb instance on Wampserver64, sync-tested against a real Android tablet, validated through CSBatch, and exported via CSExport. Architecture aligned to Khurshid Arshad's canonical CAPI patterns. Localhost-first; VPS migration is a follow-on.

---

## 1. Goals & non-goals

**Goals**
- Produce a fully script-generated, no-Designer-required build pipeline for all 5 instruments.
- Mirror the canonical Khurshid CAPI architecture: login → menu → instrument chain.
- Implement supervisor-side sample-file pipelines so PLF feeds F3 and F4-Listing feeds F4.
- Stand up local CSWeb on Wampserver64 with a 3-layer auth model (CSWeb users + app login dict + per-env config attribute).
- Capture paradata, run CSBatch consistency, export to STATA/SPSS/CSV.
- Provision an environment-aware build (`--env=dev|uat|prod`) so the local→VPS migration is one command.
- Build expiration discipline (`publishdate()`) and per-case sync audit (`synctime()`) into every instrument.

**Non-goals**
- VPS provisioning. Localhost only for this spike; VPS is a follow-on epic.
- TLS termination, public DNS, certbot. Plain HTTP on LAN is fine for build + UAT.
- F2 Healthcare Worker Survey. F2 is the PWA track and stays out of CSPro scope.
- Production-grade Carl-substitutes-for-everyone roles. We seed minimum viable users (admin, ops, 1 supervisor, 2 RAs) for testing, not full ASPSI roster.
- Survey-Manual-Myra-pass-aware decisions. Carl explicitly overrode the Myra hold for this spike. Decisions baked here may need revisiting after Myra's pass lands; spec-decisions are flagged inline so they're easy to relitigate.

---

## 2. Architecture

```
                     Spec (markdown + Excel sources)
                              │
                              ▼
              ┌───────────────────────────────────┐
              │     Generator layer (Python)      │
              │  • generate_dcf.py per instrument │
              │  • generate_fmf.py per instrument │
              │  • generate_ent.py per instrument │
              │  • generate_apc.py per instrument │
              │  • generate_pff.py (chain glue)   │
              │  • shared/* (8 NEW modules)       │
              └───────────────────────────────────┘
                              │
            text artifacts: .dcf .fmf .ent .qsf .mgf .apc .pff .dat
                              │
                              ▼
              ┌───────────────────────────────────┐
              │   build_all.py (orchestrator)     │
              │   subprocess CSDeploy.exe ×7      │
              │   --env=dev|uat|prod              │
              └───────────────────────────────────┘
                              │
   101_login.pen  106_menu.pen  107_F1.pen  109_PLF.pen
   111_F3.pen     113_F4listing.pen        115_F4.pen
                              │
                              ▼
              ┌───────────────────────────────────┐
              │    Local CSWeb on Wampserver64    │
              │     Apache 2.4 + PHP + MySQL      │
              │   3 layers of auth:               │
              │     • CSWeb users (server)        │
              │     • app login_dict (field)      │
              │     • config csweb_url attribute  │
              │   http://<lan-ip>/cswebtest/api   │
              └───────────────────────────────────┘
                              │           ▲
                pull .pen + get │           │ put case data
                pull sample dat │           │ put images
                              ▼           │
              ┌───────────────────────────────────┐
              │ Android tablet                    │
              │ CSPro Android app                 │
              │ Entry point: 101_login.pen        │
              │  ↓                                │
              │ 106_menu.pen (role dispatch)      │
              │  ↓ (one of)                       │
              │ 107_F1 / 109_PLF / 111_F3 /       │
              │ 113_F4listing / 115_F4            │
              │  ↑ (publishdate gate per app)     │
              └───────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────────┐
              │ Validate & Export                 │
              │  • CSBatch consistency (×5)       │
              │  • CSExport STATA/SPSS/CSV (×5)   │
              │  • csweb:process-cases (CSV→DB)   │
              │  • ParadataViewer                 │
              │  • daily synctime audit report    │
              └───────────────────────────────────┘
```

### 2.1 Three-tier app chain on the device

| Tier | App | Role |
|---|---|---|
| 1 | `101_login.pen` | Front door for everyone (RA / supervisor / ops). Validates credentials against `user_roster.dcf`; `savesetting`s `login_id`, `login_roll`, `supervisor_id`; PFF-launches menu. |
| 2 | `106_menu.pen` | Role-conditional menu via `accept()`. Reads `loadsetting("login_roll")`. Renders Supervisor menu (6 choices) or Enumerator menu (5 choices). PFF-launches selected instrument. Houses sample-file pipeline functions. |
| 3 | `107_F1`, `109_PLF`, `111_F3`, `113_F4_listing`, `115_F4` | Per-instrument data entry apps. Each carries `publishdate()` expiration guard, sync helpers, GPS+photo capture, and (for F4) optional EA polygon check. |

Khurshid pattern citations:
- PFF chain: [Tutorial 1: Create PFF and Menu Application @ 04:34](https://www.youtube.com/watch?v=b3V_8U3Em4Q&t=274s)
- Role-conditional menu via `accept()`: [Tutorial 2: Create PFF and Menu @ 04:15](https://www.youtube.com/watch?v=CknS2q5Z_6s&t=255s)
- savesetting / loadsetting handoff: [Tutorial 1 @ 04:18](https://www.youtube.com/watch?v=b3V_8U3Em4Q&t=258s)

### 2.2 Folder convention

```
deliverables/CSPro/UHC-Survey-System/
├── urls.yaml                      [gitignored]   per-machine env URLs
├── urls.example.yaml              [committed]    template
├── build_all.py                   orchestrator
├── shared/                        cross-instrument generators + .apc templates
├── 101_login/                     login app + spec + generators
├── 102_EXT_DIC/                   external dictionaries (generated)
├── 103_EXT_DATA/                  external data (regenerable)
├── 104_excel/                     source spreadsheets (canonical)
├── 105_polygon/                   EA boundary KML files
├── 106_menu/                      menu app + spec + generators
├── 107_F1/                        F1 Facility Head Survey (existing dir; regenerated)
├── 108_F1_data/                   F1 case storage
├── 109_PLF/                       NEW — Patient Listing Form
├── 110_PLF_data/                  PLF listing files
├── 111_F3/                        F3 Patient Survey (existing dir; regenerated)
├── 112_F3_data/                   F3 cases + patient_sample files
├── 113_F4_listing/                NEW — Barangay Listing
├── 114_F4_listing_data/           barangay listing files
├── 115_F4/                        F4 Household Survey (existing dir; regenerated)
├── 116_F4_data/                   F4 cases + hh_sample files
├── 117_images/                    GPS verification photos staging
└── 118_csbatch/                   consistency rules + edit reports per instrument
```

Numbered subfolders are Khurshid's signature pattern: [Tutorial 1: Create Login Application @ 01:18](https://www.youtube.com/watch?v=HjtqgsCppV4&t=78s).

---

## 3. Components

### 3.1 Generator layer

```
shared/
├── cspro_helpers.py           [extend]   parsing + emission utilities
├── form_layout_engine.py      [NEW]      [Field]+[Text] positions, control types per Form-Layout-Principles.md §4
├── question_text_loader.py    [NEW]      verbatim Q-text from spec MD (memory: feedback_verbatim_questionnaire_labels)
├── pff_chain_builder.py       [NEW]      PFF objects for login→menu→instrument
├── env_loader.py              [NEW]      reads urls.yaml, sets user-config attrs in .ent
├── build_username_dict.py     [NEW]      generates user_roster.dcf+.dat from Excel
├── build_polygon_dict.py      [NEW]      KML→Excel→polygon_dict.dcf+.dat (EA fence)
├── build_ea_master.py         [NEW]      EA master list dict for sample pipelines
├── build_psgc_lookups.py      [exists]   PSGC value sets (already working)
├── PSGC-Cascade.apc           [exists]   cascade logic
├── Capture-Helpers.apc        [exists]   GPS + photo helpers
├── Sync-Helpers.apc           [NEW]      syncconnect/synchronize_data wrappers
├── Expiration-Guard.apc       [NEW]      publishdate()+datediff template
├── Polygon-Check.apc          [NEW]      point-in-polygon EA fence template
└── Sample-Pipeline.apc        [NEW]      5-function sample builder template
```

Per instrument:
```
NN_<instrument>/
├── <name>.spec.md             spec input (item list, skip logic, validations, form plan)
├── generate_dcf.py            data dictionary
├── generate_fmf.py            forms ([Form] + [Field] + [Text] blocks, positions/sizes)
├── generate_ent.py            entry app (.ent + .ent.qsf + .ent.mgf)
└── generate_apc.py            logic (skip logic + validations + sync + expiration)
```

### 3.2 Build orchestrator — `build_all.py`

```bash
python build_all.py --env=dev          # all 7 .pen → dist/dev/
python build_all.py --env=dev --only=F1 # iterate on F1 alone
python build_all.py --env=uat          # → dist/uat/ for tablet upload
python build_all.py --env=prod         # post-VPS, when ready
```

Per-instrument loop:
1. Run all `generate_*.py` for that instrument (dcf → fmf → ent → apc)
2. Splice env-specific user-config attributes (`csweb_url`, `expiration_days`) into the `.ent`
3. Subprocess `CSDeploy.exe <name>.ent --out dist/<env>/<NN>_<name>.pen`
4. Hash + log the artifact

Single command, idempotent, exits non-zero on any failure.

### 3.3 Environment configuration via `urls.yaml`

`urls.example.yaml` (committed):

```yaml
dev:
  csweb_url: "http://localhost/cswebtest/api"
  expiration_days: 30          # generous during dev

uat:
  csweb_url: "http://192.168.1.42/cswebtest/api"   # YOUR LAPTOP'S LAN IP
  expiration_days: 7

prod:
  csweb_url: "https://uhc-sync.example.com/cswebtest/api"   # VPS, when ready
  expiration_days: 3           # tight during fieldwork
```

`urls.yaml` (gitignored): same shape, real values for the developer's machine.

`env_loader.py` reads `urls.yaml[env]` and mutates the `.ent`'s `userSettings` block before `CSDeploy.exe` packages it. Inside the instrument code, Khurshid's canonical pattern still holds:

```
PROC GLOBAL
config csweb_url csweb_url;       { variable name = attribute name, REQUIRED }
config expiration_days exp_days;
```

(See [Deploy an Application @ 07:55](https://www.youtube.com/watch?v=hil_SpX_fsA&t=475s).)

### 3.4 Local CSWeb (Wampserver64)

Three-layer auth:

| Layer | Lives where | Authenticates whom |
|---|---|---|
| **A. CSWeb users** | Server (MySQL) | Server-level — who can deploy, download, view reports |
| **B. App-level login** | `102_EXT_DIC/user_roster.dcf` | Field — who is using the tablet |
| **C. `config` attribute** | User and Configuration Settings (per-env URL) | Build-time binding of sync URL |

Seed CSWeb users (Khurshid pattern: [Sync Files @ 00:24](https://www.youtube.com/watch?v=QU-XNX8_Aqc&t=24s)):

| Username | Role | Permissions |
|---|---|---|
| `carl_admin` | Administrator | All |
| `aspsi_ops` | Standard | Upload/download, no admin |
| `team_lead_uat` | Custom: `field_lead` | Reports + Sync Data |
| `analyst_readonly` | Custom: `view_reports` | Reports only |

Seed app-level users (`user_roster.xlsx` → `.dcf`):

```
RA_ID | RA_NAME            | PASSWORD_HASH | ROLE | SUPERVISOR_ID | REGION_CODE
1001  | Test Supervisor    | <hash>        | 1    | (self)        | 13
2001  | Test RA Alpha      | <hash>        | 2    | 1001          | 13
2002  | Test RA Bravo      | <hash>        | 2    | 1001          | 13
9001  | Carl (Ops)         | <hash>        | 3    | (self)        | -
```

CSWeb provisioning:
1. Download CSWeb PHP package
2. Drop in `C:\wamp64\www\cswebtest\`
3. MySQL: create `cswebtest` DB + `csweb_app` user
4. Run bundled SQL schema
5. Edit `config.php`: DB connection + admin credentials
6. `curl http://localhost/cswebtest/api/ping` smoke test
7. Open Windows Firewall on port 80 for tablet LAN access

### 3.5 Tablet entry flow

```
1. Open CSPro Android app
2. Tap "101_login" (the only icon they should see as default)
3. Enter RA_ID + password   → login_app validates against user_roster.dcf
4. savesetting("login_id" / "login_roll" / "supervisor_id")
5. login_app launches 106_menu via PFF chain
6. menu_app reads loadsetting("login_roll") and renders:

   ENUMERATOR menu (5 choices):           SUPERVISOR menu (6 choices):
     1. Start patient listing (PLF)         1. Assign EA / facility to RA
     2. Conduct facility interview (F1)     2. Receive listing data
     3. Conduct patient interview (F3)      3. Create patient sample (PLF→F3)
     4. Start barangay listing              4. Create household sample (F4-list→F4)
     5. Conduct household interview (F4)    5. Send all data to server
                                            6. View daily synctime audit

7. Selected choice launches the instrument .pen via PFF chain
8. On instrument exit, OnExit returns to 106_menu
9. Menu choice "logout" or escape → returns to 101_login
```

### 3.6 Validate + export

| Tool | Per-instrument output |
|---|---|
| `CSBatch.exe` | Edit reports from skip-logic spec — runs every night against synced data |
| `CSExport.exe` | `.dta` (STATA) + `.sav` (SPSS) + `.csv` per instrument |
| `php bin\console csweb:process-cases` | Relational MySQL tables for ad-hoc SQL queries (Khurshid: [Deploy @ 12:58](https://www.youtube.com/watch?v=hil_SpX_fsA&t=778s)) |
| `ParadataViewer.exe` | Per-case timing, edit history, sync events |
| `daily_audit.py` | Reads `synctime()` output → "RA-X has 3 cases unsynced" Slack post to `#capi-scrum` |

### 3.7 EA boundary fence (bonus, F4-mandatory)

`105_polygon/<bgy_code>.kml` per barangay → `build_polygon_dict.py` ingests all → emits `polygon_dict.dcf` + `.dat` → F4 calls `Polygon-Check.apc` on GPS capture; if outside, error + reenter + visual-KML so RA sees *why*. F1/F3 inherit if a flag is flipped in their generator config.

Pattern: [Restrict an Enumerator from Working Outside the EA Boundary @ 00:00](https://www.youtube.com/watch?v=cKnsiMp-kq4&t=0s).

---

## 4. Data flow

### 4.1 Case-ID generation across instruments

Every case carries the 12-digit `RR-PP-MMM-FF-CCC` (memory: `project_questionnaire_numbering_parked`) plus a per-enumerator suffix. Two anchor flows: facility-anchored (F1 → PLF → F3) and barangay-anchored (F4_listing → F4).

```
F1 (Facility Head)          ← anchors at facility
   case_id = RR PP MMM FF CCC                     ← from supervisor's assignment file
   loadsetting login_id, supervisor_id            ← stamped on every record
   publishdate() / synctime() / GPS captured here

PLF (Patient Listing Form)  ← lives within the F1 visit
   plf_case_id = F1.case_id + LISTING_SR (1..N)
   exits to file: plf_<F1.case_id>.csdb           ← per-facility

F3 (Patient Survey)         ← downstream of supervisor's sample pipeline
   loadcase(PATIENT_SAMPLE_DICT, F1.case_id, PATIENT_SR)
   F3.case_id = F1.case_id + PATIENT_SR (+ visit-qualifier if multi-visit added later)
   F3_FACILITY_ID = F1.case_id   ← linkage memory rule

F4_listing (Barangay Listing) ← anchors at barangay (no F1 dependency)
   bgy_case_id = RR PP MMM BBB
   exits to file: bgy_listing_<bgy_case_id>.csdb

F4 (Household Survey)       ← downstream of supervisor's sample pipeline
   loadcase(HH_SAMPLE_DICT, bgy_case_id, HH_SR)
   F4.case_id = bgy_case_id + HH_SR
```

### 4.2 Sample-file pipelines

`Sample-Pipeline.apc` is parameterized; the same template instantiates twice:

```
PLF→F3 path        : concat per-facility PLF files → mark eligible patients →
                     interval-N sample → assign IDs → write patient_sample_<F1.case_id>.csdb
F4-Listing→F4 path : concat per-barangay listing files → mark eligible HHs →
                     interval-N sample → assign IDs → write hh_sample_<bgy>.csdb
```

Khurshid pattern (5-function pipeline): [Create a Sample File for Household Interview @ 17:43](https://www.youtube.com/watch?v=YShBTXD2of0&t=1063s).

Random number for interval sampling pre-stored in `random_number_dict.dcf` per supervisor — required for reproducibility (so re-runs produce same sample).

### 4.3 Sync session shapes

| Menu choice | Direction | Dictionaries touched | Files | Frequency |
|---|---|---|---|---|
| Enum: "Send data on server" | put | F1, PLF, F3, F4_LISTING, F4 (whichever have unsynced cases) | photos via `synchronize_file` | Daily 10 PM (memory: protocol mandate) |
| Enum: "Receive sample" | get | PATIENT_SAMPLE_DICT, HH_SAMPLE_DICT | none | After supervisor signals sample is ready |
| Sup: "Receive listing" | get | PLF_DICT, BGY_LISTING_DICT | none | Once per RA after their PLF/listing run |
| Sup: "Send data on server" | put | PATIENT_SAMPLE_DICT, HH_SAMPLE_DICT | sample reports | After running pipelines |
| Sup: "View daily synctime audit" | local read | all 5 dicts via `synctime(...)` | none | Anytime; supervisor diagnostic |

Universal sync envelope (Khurshid: [Deploy @ 07:25](https://www.youtube.com/watch?v=hil_SpX_fsA&t=445s)):

```
if syncconnect("csweb", csweb_url) then
    synchronize_data(put|get, <DICT>);
    syncdisconnect();
else
    errmsg("Could not reach the sync server");
endif;
```

---

## 5. Error handling

| Failure mode | Detection | Recovery |
|---|---|---|
| Sync server unreachable | `syncconnect()` returns false | `errmsg` + cases held locally; idempotent retry next sync |
| App expired (publishdate window exceeded) | `Expiration-Guard.apc` in level-preproc | `errmsg + stop(1)`; RA pulls fresh `.pen` via `synchronize_file(get, ...)` |
| GPS unavailable | `Capture-Helpers.apc::ReadGPSReading()` returns `notappl` accuracy | Manual lat/lon override with supervisor sign-off field |
| Out-of-EA boundary (F4) | `Polygon-Check.apc` `find_n = 0` | `errmsg + reenter`; auto-generate `map.kml` showing assigned polygon + current GPS point |
| Sample not yet generated | F3/F4 menu choice preproc: `not fileexists(sample_path)` | `errmsg("Sample not yet received from supervisor")` + return |
| Login dict out of date | RA can't authenticate | Supervisor pushes `user_roster` as `synchronize_file` payload mid-cycle |
| Concurrent edits (server-side change) | Server-timestamp conflict on case re-open | `errmsg("Case edited on server since last sync. Sync first.")` |
| Photo upload failure | `synchronize_file()` returns false | Retry 3× with exponential backoff; failed photos kept in `_failed/`, supervisor sees in audit |
| Disk full on tablet | Pre-sync `getfilesize()` > threshold | Warn supervisor, force sync; optional 7-day-old purge |

---

## 6. Testing strategy

Four layers:

**Layer 1 — Generator unit tests** (Python, fast)
Per generator function: emit artifact, parse it back, assert structural invariants. Runs on every `python build_all.py`.

**Layer 2 — CSPro syntax integration** (Windows CSEntry, semi-fast)
After `CSDeploy.exe` produces `.pen`, `runpff.exe` opens it headless with `--validate`. Catches: undeclared variables, type mismatches in `loadcase()`, missing `endif`, broken cross-references.

**Layer 3 — Synthetic case end-to-end** (Windows CSEntry, scripted)
Per instrument, scripted PFF walks a happy-path case + skip-logic-heavy case + edge-validation case. Sample-pipeline tests load fixture PLF data → run supervisor pipeline → assert `patient_sample_*.csdb` has expected count + IDs. EA fence test: fixture GPS inside polygon → pass; outside → reenter. Expiration test: fixture publishdate 10 days ago → `stop(1)`.

**Layer 4 — Real tablet, real CSWeb, real Wi-Fi** (manual)
Login → menu → F1 → finish → sync → CSWeb dashboard shows new case. Supervisor flow: receive listing → run sample pipeline → send sample → enumerator pulls → F3 case opens with prefilled patient ID. Concurrent test: two tablets (or 2× CSEntry-Windows simulating tablets) + supervisor laptop, sync overlap, verify no data loss.

**Test data fixtures** in `tests/fixtures/`:
- 1 facility roster (5 facilities)
- 1 EA polygon set (3 barangays, KML)
- 1 user roster (4 RAs + 2 supervisors + 1 ops)
- Per-instrument: 3 cases each (happy / skip-logic-heavy / edge-validation)

CSBatch consistency rules generated from `F{1,3,4}-Skip-Logic-and-Validations.md` run nightly against fixtures during dev; carry forward to fieldwork.

---

## 7. Spec-decisions overridden from Myra hold

For traceability when Myra's edit pass lands. Each item below was `held` per memory `project_survey_manual_bundle_ingest_2026_05_07`; baked here for the spike with the noted assumption.

| Decision | Spike assumption | Risk if Myra disagrees |
|---|---|---|
| **F3 listing app architecture (PLF)** | Standalone `109_PLF` app; emits `plf_<F1.case_id>.csdb`; supervisor pipeline produces `patient_sample_<F1.case_id>.csdb`; F3 `loadcase`s. | Architecture rewrite likely localized to `109_PLF/` and the supervisor pipeline function; F3 entry point unaffected if shape holds. |
| **Case-ID final form** | 12-digit `RR-PP-MMM-FF-CCC` per memory; F3 case_id = F1 case_id + PATIENT_SR + ENUM_VISIT_NO; F4 case_id = bgy_case_id + HH_SR. | If digit count or component changes, `cspro_helpers.py` gets one update; DCFs regenerate. |
| **F4 barangay listing** | Standalone `113_F4_listing` app; emits `bgy_listing_<bgy>.csdb`; supervisor pipeline produces `hh_sample_<bgy>.csdb`. | Same containment as PLF — change localized. |
| **EA fence enabled for F4** | F4 mandatory; F1/F3 optional behind a config flag. | Easy to disable per instrument. |
| **Daily 10 PM sync as protocol mandate** | Honored via supervisor-side daily synctime audit + `Expiration-Guard.apc` 3-day window in prod. | If protocol relaxes, expiration window widens. |
| **HCW 60% threshold** (F2) | Out of CSPro scope; F2 is PWA. No spike action. | None for this spike. |

---

## 8. Risks & mitigations specific to Approach β-3 (full system)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Generator FMF output rendering ugly enough to need Designer | Medium | Medium | Layer 4 testing on real tablet catches before fieldwork; if hit, fall back to per-instrument Designer pass — pipeline still works |
| Sample pipeline math wrong (off-by-one in interval sampling) | Low | High | Reproducible random-number seed (Khurshid pattern); compare two runs against same fixture must be identical |
| CSWeb provisioning on Wampserver hits MySQL/PHP version pin | Medium | High | Provision early (Layer 4 first instrument-only test); if blocked, narrow scope to single-user flow |
| `publishdate()` expiration accidentally locks Carl out mid-spike | Low | Medium | Dev env has 30-day window; only UAT/prod have tight windows |
| F1 regenerated FMF inferior to Carl's existing Designer-laid-out one | Medium | Medium | Keep `FacilityHeadSurvey.fmf.bak`; diff old vs new; can revert per instrument |
| Myra's edit pass invalidates a baked spec-decision | High (eventual) | Medium | §7 catalogs every overridden decision for fast relitigation |
| Tablet sideload + Android sync setup not in mentor corpus | Certain | Low | Operational SOP gap; document as we go |

---

## 9. Out of scope (explicitly)

- F2 Healthcare Worker Survey (PWA track, separate)
- VPS provisioning, TLS, public DNS
- ASPSI's full RA roster (seed minimum users only)
- CSPro Android APK distribution beyond Carl's tablet
- Fieldwork training materials (covered separately by `UHC-Survey-CAPI-Guide`)
- SJREB submission paperwork

---

## 10. Success criteria

- [ ] `python build_all.py --env=dev` produces 7 valid `.pen` files in `dist/dev/` with no manual Designer step.
- [ ] Local CSWeb on Wampserver64 reachable at `http://localhost/cswebtest/api/ping`.
- [ ] Real Android tablet: APK sideloaded via USB (one-time), then on same Wi-Fi as laptop authenticates via `101_login.pen`, loads `106_menu.pen`, completes a synthetic F1 case, syncs to CSWeb over LAN; case visible in phpMyAdmin.
- [ ] Supervisor menu's "Create patient sample" successfully runs the 5-function pipeline against PLF fixture data.
- [ ] F3 launched after sample pipeline pre-fills patient_id from `loadcase()`.
- [ ] CSBatch consistency report runs against synced data, produces `edit_report_F1.txt`.
- [ ] CSExport produces `F1.dta` (STATA) + `F1.sav` (SPSS) + `F1.csv`.
- [ ] `daily_audit.py` runs against fixture, identifies 1 unsynced case, posts to `#capi-scrum`.
- [ ] Build a fresh `.pen` with `--env=uat` and confirm only the `csweb_url` differs in the embedded settings — proves the local→VPS migration is one command.

---

## 11. Out of band — what this spec deliberately does NOT design

- The implementation order. That's the writing-plans skill's job, next.
- Test fixture content (specific item values per instrument). Captured in tests/fixtures/ during implementation.
- Specific CSBatch consistency rules (those are derived from skip-logic spec MDs at build time).
- VPS host selection, sizing, OS, backup cadence. All in the future "VPS migration" follow-on epic.

---

## 12. Follow-on hand-off

After approval, this spec is consumed by `superpowers:writing-plans` to produce the implementation plan with: ordered tasks, dependency graph, time estimates, test gates, and rollback points per phase. The plan is the artifact that drives execution; this spec is the artifact that gates the plan.
