---
title: UHC Phase 1 — F1 + CSPro Android Native Sync
type: design-spec
date: 2026-05-11
status: draft
author: Carl Patrick L. Reyes (with Claude)
mentor_alignment: khurshid-arshad (CAPI / Survey Research) — CSPro 8.0 adapted
scope: Phase 1 — F1 only, native sync, no chain
supersedes_sections: 2026-05-08-uhc-survey-system-build-design.md (sync architecture only — chain architecture preserved for Phase 2+)
follow_on: writing-plans skill (Phase 1 implementation plan)
closes: E3-F1-088 (UHC Phase 1 sync mechanic resolution)
---

# UHC Phase 1 — F1 + CSPro Android Native Sync

## Context

The 2026-05-08 full-system design specified a 7-app chain (`login` → `menu` → 5 questionnaires) with custom `syncdata` logic. The chain architecture is sound; the **sync architecture** built around custom `syncdata(PUT, dict)` ran into repeated CSPro 8.0 constraints during Sprint 004 Day 5 + Sprint 005 Day 1:

- v1 (sync from F1's level postproc): `Invalid function call (external dictionary name expected)` — CSPro 8.0 syncdata won't accept the app's own primary dict as a direct identifier
- v2 (separate `109_sync` entry app + F1 as external dict + polymorphic `dictname` param): `'dict' is not a declared variable` — CSPro 8.0 removed the polymorphic `dictname` parameter idiom
- v3 (drop param, inline `syncdata(PUT, FACILITYHEADSURVEY_DICT)` against external dict declaration): compiles clean, but `The datasource to FACILITYHEADSURVEY_DICT does not support the sync features used in the program` at runtime — external dict defaults to flat `.dat` datasource, not CSDB
- v4 (add `setfile(FACILITYHEADSURVEY_DICT, "..\107_F1\F1.csdb")` to bind CSDB format): runtime says `The data file does not exist` — F1.csdb is being written somewhere CSPro Android can't read back; further investigation revealed CSPro Android partial-save persistence is inconsistent with the launching PFF's InputData path resolution.

After 4 fixes failed (matching the systematic-debugging skill's "question the architecture at 3+ failures" trigger), this spec resets the sync mechanism to a tested, supported alternative: **CSPro Android's built-in `Synchronize → Send data` UI**. F1's logic carries zero sync code. Sync transport is entirely CSPro Android's responsibility.

The chain architecture (login + menu + multi-questionnaire) is preserved for Phase 2+. Phase 1 collapses scope to **F1 as a standalone deployable**, proving the build-pipeline + CSPro-Android-sync round-trip in the simplest possible form.

## 1. Goals & non-goals

### Goals

- F1 entry app deployable to CSWeb and pullable to Android tablet via standard CSPro Android sync
- F1 case data captures correctly into local `F1.csdb` on the tablet
- Cases push to CSWeb via **CSPro Android's native Synchronize → Send data** UI — no custom syncdata code anywhere
- Close `E3-F1-088` (Sprint 005 Goal A anchor) with a minimum viable architecture
- Build pipeline (`build_all.py` + per-instrument `generate_*.py`) continues as source of truth — generators canonical, regenerable, no Designer hand-edits

### Non-goals (deferred to later phases)

| Item | Deferred to |
|---|---|
| Login app (`101_login`) | Phase 2 |
| Menu app (`106_menu`) | Phase 2 |
| Multi-app PFF chain | Phase 2 |
| Custom in-app sync menu choice (Approach B) | Phase 2 |
| Auto-sync on case end (Approach C) | Phase 2 |
| PLF + sample-pipeline | Phase 2 / 3 |
| F3, F4_listing, F4 questionnaires | Phase 2 / 3 |
| Supervisor flow / role-conditional menus | Phase 2 |
| EA boundary fence | Phase 3 |
| Daily synctime audit | Phase 2 (supervisor feature) |
| VPS migration | Separate epic |
| Multi-language (Filipino, etc.) | Phase 3 |

## 2. Architecture

```
              ┌─────────────────────────────────────┐
              │ deliverables/CSPro/                 │
              │   UHC-Survey-System/                │
              │   ├── build_all.py                  │  INSTRUMENTS = [F1 only]
              │   ├── shared/                       │
              │   │   ├── cspro_helpers.py          │
              │   │   ├── form_layout_engine.py     │
              │   │   ├── env_loader.py             │
              │   │   └── ent_template.py           │  (no Sync-Helpers.apc — deleted)
              │   ├── 107_F1/                       │
              │   │   ├── generate_dcf.py           │
              │   │   ├── generate_ent.py           │
              │   │   ├── generate_fmf.py           │
              │   │   ├── generate_apc.py           │  (minimal — no sync code)
              │   │   └── FacilityHeadSurvey.{...}  │
              │   ├── 101_login/   (parked)         │
              │   ├── 106_menu/    (parked)         │
              │   ├── urls.yaml                     │
              │   └── urls.example.yaml             │
              └─────────────────────────────────────┘
                          │
            python build_all.py --env=uat
                          │
                          ▼
              FacilityHeadSurvey.ent emitted with
              csweb_url=http://192.168.1.168/csweb8.0.1/api
              spliced into userSettings
                          │
            CSPro Designer → F7 (Publish Entry Application)
                          │
                          ▼
              FacilityHeadSurvey.pen
                          │
            Tools → CSPro Deploy Application → CSWeb
                          │
                          ▼
              ┌─────────────────────────────────────┐
              │ CSWeb (Wampserver64)                │
              │ http://192.168.1.168/               │
              │   csweb8.0.1/api                    │
              │ Package: UHC_Survey_Phase1          │
              │   (or single-app naming TBD)        │
              └─────────────────────────────────────┘
                          │
            CSPro Android: Synchronize → Get applications
                          │
                          ▼
              ┌─────────────────────────────────────┐
              │ Android tablet                      │
              │ CSPro Android                       │
              │ FacilityHeadSurvey.pen installed    │
              │                                     │
              │ Enumerator workflow:                │
              │   1. Tap F1 app icon                │
              │   2. Enter case (671 items max)     │
              │   3. End Case (X icon)              │
              │   4. Repeat for multiple cases      │
              │   5. End of day: Synchronize →      │
              │      Send data  ← NATIVE SYNC UI    │
              └─────────────────────────────────────┘
                          │
                          ▼
              Cases land in CSWeb MySQL backend
              Carl verifies via CSWeb admin Cases tab
```

**Key architectural decision:** F1's `.apc` carries **zero** sync code. Sync transport is entirely CSPro Android's responsibility, using credentials cached at package-install time. F1 is pure data entry.

### Why this architecture beats the v1–v4 attempts

| v1–v4 problem | Native-sync resolution |
|---|---|
| `Invalid function call (external dictionary name expected)` | No `syncdata` call exists; problem disappears |
| `dictname` polymorphic param removed in CSPro 8.0 | No user-defined sync function; problem disappears |
| External dict datasource defaults to flat `.dat` | CSPro Android handles the dict's CSDB binding internally |
| `setfile` path resolution mismatch with CSPro Android | CSPro Android knows where it wrote F1.csdb; no manual path binding needed |
| Bootstrap chicken-egg (menu_app startup requires F1.csdb) | No menu_app in Phase 1; F1 stands alone |

## 3. Components

### Component inventory

| Component | Current state | Phase 1 action |
|---|---|---|
| `shared/cspro_helpers.py` | Existing, working | Keep as-is |
| `shared/form_layout_engine.py` | Existing, working | Keep as-is |
| `shared/env_loader.py` | Existing, working | Keep as-is |
| `shared/ent_template.py` | Existing, working | Keep as-is |
| `shared/Sync-Helpers.apc` | Orphan from CSPro 7.x era; 0 callers | **DELETE** |
| `107_F1/generate_dcf.py` | Existing | Keep |
| `107_F1/generate_ent.py` | Existing | Keep (no changes — F1 ent doesn't need sync flags) |
| `107_F1/generate_fmf.py` | Existing | Keep |
| `107_F1/generate_apc.py` | Minimal (post Day-5 sync strip) | Keep as-is — already perfect for native sync |
| `107_F1/FacilityHeadSurvey.{dcf,ent,fmf,apc}` | Generated outputs | Regenerated by build_all.py |
| `109_sync/` (entire directory + 4 generators + outputs) | Failed B1 experiment | **DELETE** |
| `101_login/` | Existing | Keep on disk; remove from Phase 1 INSTRUMENTS |
| `106_menu/` | Existing, plus `launch_sync_F1` addition from B1 | Keep on disk; **revert `generate_apc.py`** to single-F1-choice version; remove from Phase 1 INSTRUMENTS |
| `build_all.py` | 4 instruments incl. 109_sync | **Edit:** `INSTRUMENTS = [("107", "F1", "107_F1", "FacilityHeadSurvey")]` |
| `urls.yaml` / `urls.example.yaml` | Existing, UAT LAN IP intact | Keep |

### F1 entry app — content

The generated `FacilityHeadSurvey.ent.apc` after the Phase 1 build:

```cspro
{ Application 'FacilityHeadSurvey' logic file generated by CSPro }
{ Phase 1: minimal — pure data entry. Sync handled natively by CSPro
  Android's Synchronize → Send data UI. All sync transport, auth,
  retry, and case selection is CSPro Android's responsibility.
  Skip-logic + validations + GPS + photo + PSGC cascade all deferred
  to Phase 2 spec-driven build. }

PROC GLOBAL


PROC FACILITYHEADSURVEY_LEVEL
```

This is the current state of `107_F1/generate_apc.py`'s emitted output. No further changes needed.

### Build pipeline reduction

`build_all.py` INSTRUMENTS list collapses to:

```python
INSTRUMENTS = [
    ("107", "F1", "107_F1", "FacilityHeadSurvey"),
]
```

Login + menu directories stay on disk but are not part of the Phase 1 build. The shape of `INSTRUMENTS` is unchanged from the existing list — just one entry — so when Phase 2 reintroduces login and menu, the addition is purely additive.

## 4. Data flow / Workflow

### Build time (Carl's machine)

1. `python build_all.py --env=uat`
   - Regenerates F1's `.dcf` / `.ent` / `.fmf` / `.apc` from `107_F1/generate_*.py`
   - Splices LAN IP into `userSettings.csweb_url` (from `urls.yaml[uat]`)
2. Open `FacilityHeadSurvey.ent` in CSPro Designer → **F7 (Publish Entry Application)** → produces `FacilityHeadSurvey.pen`
3. **Tools → CSPro Deploy Application** wizard → upload `.pen` to CSWeb:
   - Server URL: `http://192.168.1.168/csweb8.0.1/api`
   - Credentials: CSWeb admin user
   - Package Name: `UHC_Survey_Phase1` (or `FacilityHeadSurvey` if single-app naming preferred for Phase 1 — TBD by Carl at deploy time)

### Field time (tablet)

4. CSPro Android → **Synchronize → Get applications** → pulls `FacilityHeadSurvey.pen`
5. Enumerator taps the F1 app icon → form opens → enters case data (any subset, up to 671 items)
6. **End Case (X icon)** at top right → case persisted to `F1.csdb` on tablet
7. Repeat for multiple facilities through the day
8. End of day (or when Wi-Fi available): CSPro Android → **Synchronize → Send data** → native UI pushes all F1.csdb cases to CSWeb

### Verification

9. Open `http://localhost/csweb8.0.1/` (or the configured CSWeb URL) → admin UI → **Cases** tab → confirm test cases visible with correct `QUESTIONNAIRE_NO` IDs

## 5. Error handling

| Failure mode | Detection | Recovery |
|---|---|---|
| Network unreachable during sync | CSPro Android native UI shows error dialog | Cases held in F1.csdb on tablet; enumerator retries Send data when Wi-Fi available |
| CSWeb auth fails | CSPro Android prompts for credentials | Enumerator re-enters credentials in CSPro Android → Settings → Sync server |
| F1.pen out-of-date relative to server version | User pulls newer .pen via Synchronize → Get applications | Standard CSPro Android upgrade flow; cases survive .pen upgrade |
| Tablet's LAN IP changed from what's in F1.ent userSettings | Sync fails with "host unreachable" | Rebuild .pen with current LAN IP via `build_all.py --env=uat` → re-F7 → re-deploy |
| F7 publish fails at build time | Designer error pane | Fix .apc / .dcf source → regenerate via build_all.py → re-F7 |
| F1.csdb partial-save case doesn't appear on F1 re-launch | (Observed during Sprint 005 Day 1 attempts) | Use **End Case (X)** instead of Suspend/back arrow; End Case forcibly commits to .csdb regardless of validation state. Partial saves via back arrow not supported in Phase 1 — operator partial save is a Phase 2 polish item. |
| CSWeb-side errors (storage full, MySQL down) | CSPro Android sync returns server error | Carl investigates via CSWeb logs + Wampserver Apache/MySQL status |

## 6. Testing strategy

**Layer 1 — Generator unit tests:** Existing `tests/unit/test_*.py` for `env_loader.py`, `form_layout_engine.py`, etc. Run via `pytest tests/unit/`. Must stay green; no new tests required for Phase 1 since generators don't change.

**Layer 2 — Build pipeline smoke (scripted):** `python build_all.py --env=uat` produces `FacilityHeadSurvey.ent` cleanly with no Python exceptions, and the emitted `.ent` JSON has `csweb_url=http://192.168.1.168/csweb8.0.1/api` correctly spliced into `userSettings`. Verified by reading the emitted file.

**Layer 3 — CSPro Designer F7 publish (manual):** Open `FacilityHeadSurvey.ent` in Designer → F7 → produces `FacilityHeadSurvey.pen` with no compile errors. If errors surface, capture exact text and iterate on `.apc` or `.dcf` source (never hand-edit Designer outputs).

**Layer 4 — Tablet round-trip (manual, the actual E3-F1-088 close):**

1. Deploy `FacilityHeadSurvey.pen` to CSWeb via Designer's Tools → CSPro Deploy Application wizard
2. Tablet → CSPro Android → Synchronize → Get applications → confirm F1 appears in installed apps
3. Launch F1 → enter dummy case (`QUESTIONNAIRE_NO=000001` + a couple FIELD_CONTROL fields per dummy data values from spec) → End Case (X)
4. CSPro Android → Synchronize → **Send data** → native sync UI completes successfully
5. Open CSWeb admin (`http://localhost/csweb8.0.1/` or LAN equivalent) → Cases tab → verify test case landed with `QUESTIONNAIRE_NO=000001`

If Layer 4 succeeds → **E3-F1-088 closes**.

### Test data fixture

Phase 1 needs exactly one dummy case for the Layer 4 round-trip:

| Field | Value |
|---|---|
| QUESTIONNAIRE_NO | `000001` |
| SURVEY_CODE | `F1` |
| INTERVIEWER_ID | `0001` |
| DATE_STARTED | `20260511` (or current date YYYYMMDD) |
| TIME_STARTED | `HHMMSS` (current time, 6-digit) |
| AAPOR_DISPOSITION | `120` (Partial — appropriate since we're not completing all 671 items) |

Any additional fields can be filled with plausible dummy values or left empty per CSPro's default behavior.

## 7. Cleanup tasks

Executed as a single commit on the `feature/uhc-survey-system-build` worktree before any new build work:

| Action | Target | Rationale |
|---|---|---|
| Delete | `deliverables/CSPro/UHC-Survey-System/109_sync/` (entire directory) | Failed B1 experiment; all 4 generators + their generated outputs |
| Delete | `deliverables/CSPro/UHC-Survey-System/shared/Sync-Helpers.apc` | Orphan from CSPro 7.x era; uses `synchronize_data` (renamed in 8.0) + `"csweb"` string literal (now bare `CSWeb` identifier); zero callers anywhere in the codebase |
| Revert | `deliverables/CSPro/UHC-Survey-System/106_menu/generate_apc.py` | Remove `launch_sync_F1()` function + 2nd menu choice. Restore single F1-launch choice. Phase 2 will rebuild this anyway when menu is reactivated. |
| Edit | `deliverables/CSPro/UHC-Survey-System/build_all.py` | Reduce `INSTRUMENTS` list to `[("107", "F1", "107_F1", "FacilityHeadSurvey")]`. Login + menu parked. |
| Keep as-is | `deliverables/CSPro/UHC-Survey-System/107_F1/generate_apc.py` | Already minimal post-Day-5 strip; no sync code; perfect for Approach A. |
| Keep as-is | All other `shared/` files and `107_F1/generate_*.py` files | Working, no changes needed |
| Keep on disk | `101_login/`, `106_menu/` directories (post-revert) | Parked for Phase 2 reactivation; brought back when chain is rebuilt |

After cleanup, working tree has F1 + shared helpers + build pipeline + parked login/menu source. Nothing else active.

## 8. Phase 2 considerations (documented here for forward continuity, NOT built in Phase 1)

### Custom in-app sync (Approach B)

Once Phase 1 proves the data round-trip via native sync, Phase 2 can add a custom "Sync now" button inside F1 (or the menu app once chain is rebuilt). This requires resolving the CSPro 8.0 syncdata constraints we hit. Likely investigation paths:

- Test whether F1's primary dict needs a `"syncable": true` flag in the `.ent` JSON
- Try Khurshid's exact CSPro-8.0-adapted incantation (we'd need a verified-working CSPro 8.0 reference video or repository)
- Test whether `setfile` + external-dict approach works when the data file path is bound at PFF launch time via an `[ExternalFiles]` PFF section, not at runtime via setfile

Reuse of a refreshed `Sync-Helpers.apc` (rewritten for 8.0 syntax) becomes possible once we have a working pattern.

### Auto-sync on case end (Approach C)

Builds on Approach B. Once custom sync works from a button, the same call goes into the level postproc to fire automatically at End Case. Requires error handling for the silent-failure case (network drop mid-sync, server error, etc.).

### Login app + menu app reactivation

When the second questionnaire arrives (likely PLF or F3), reactivate `101_login/` and `106_menu/` per the 2026-05-08 design's chain architecture. Add them back to `build_all.py` INSTRUMENTS. Decide menu's role at that time (custom sync menu choice vs delegate to CSPro Android native).

### PLF + sample-pipeline + EA fence + supervisor audit

Per the 2026-05-08 design sections 4.2, 3.7, 4.3. These are downstream features that depend on multi-questionnaire chain being live.

## 9. Success criteria

`E3-F1-088` closes when ALL of these are demonstrably true:

- [ ] `python build_all.py --env=uat` produces `FacilityHeadSurvey.ent` cleanly with no Python errors
- [ ] F7-publish in CSPro Designer produces `FacilityHeadSurvey.pen` with no compile errors
- [ ] Deploy Application wizard uploads the `.pen` to CSWeb (package `UHC_Survey_Phase1` or fresh package — operator decision at deploy time)
- [ ] CSPro Android pulls the `.pen` via Synchronize → Get applications and F1 appears in the installed-apps list
- [ ] Tablet enumerator enters a test case (`QUESTIONNAIRE_NO=000001`) and End-Cases it
- [ ] CSPro Android Synchronize → Send data succeeds (native UI shows completion or equivalent green state)
- [ ] Test case appears in CSWeb admin Cases tab with correct `QUESTIONNAIRE_NO`
- [ ] Smoke evidence recorded in worktree `log.md` (commit hash, timestamp, screenshots if available)

## 10. Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| CSPro Android native sync needs configuration we haven't done | Medium | Medium | Test on tablet early; tablet sideload runbook (`2026-05-08-tablet-sideload-runbook.md`) already covers CSPro Android sync server setup; do "Test connection" smoke first |
| F1.csdb persistence still issues (case tree empty on re-launch) — observed during Sprint 005 Day 1 attempts | Low (with End Case path) | High | Use **End Case (X icon)** rather than Suspend/back arrow. End Case forcibly commits to .csdb regardless of validation state. Partial saves via back arrow are a Phase 2 polish item — Phase 1 requires explicit End Case. |
| Laptop's LAN IP changes between build and deploy | Medium | Low | `Get-NetIPAddress` check before deploy; rebuild `.pen` with current IP via `build_all.py --env=uat` if mismatch |
| CSWeb auth on tablet not yet configured | Medium | Medium | CSPro Android Settings → Sync server → "Test connection" smoke before any sync attempt; runbook covers this |
| F1 spec changes from Myra's edit pass mid-Phase-1 | Low | Low | Generators are source of truth (per `feedback_f1_dcf_generator_source_of_truth` memory); spec changes regenerate cleanly via generator updates |
| CSPro Android version mismatch with .pen format | Low | High | Tablet is on CSPro 8.0.x (matches build); document version in smoke notes |
| Cleanup commit accidentally deletes something needed | Low | Medium | Cleanup is in a single labeled commit on worktree branch; revertable; nothing pushed to main until E3-F1-088 closes |

## 11. Out of scope (explicitly NOT in Phase 1)

- Multi-tablet concurrent sync testing
- Production-grade ASPSI RA roster (single test enumerator for Phase 1 smoke)
- TLS / public DNS / VPS
- CSPro Android APK distribution (existing tablet has CSPro Android installed)
- Fieldwork training materials (covered separately by Epic 7)
- Data quality / consistency rules (Phase 1 proves transport; data quality is Phase 3+)
- Photo capture, GPS capture, PSGC cascade (all Phase 2/3)

## 12. Follow-on hand-off

After approval, this spec is consumed by the `superpowers:writing-plans` skill to produce a Phase 1 implementation plan with:

1. **Cleanup tasks** (single commit deleting 109_sync, Sync-Helpers.apc, reverting menu_app generate_apc.py, editing build_all.py)
2. **Build verification** (run build_all.py --env=uat, confirm clean output)
3. **F7 publish** (manual Designer step)
4. **CSWeb deploy** (manual Designer Deploy Application wizard)
5. **Tablet sideload** (CSPro Android Synchronize → Get applications)
6. **Smoke test** (Layer 4 round-trip)
7. **Evidence recording** (log.md entry, commit hash, screenshots)
8. **E3-F1-088 close** (sprint-current.md DoD update + sprint-005-plan.md + Project #8 issue status)

The plan is the artifact that drives execution; this spec is the artifact that gates the plan.
