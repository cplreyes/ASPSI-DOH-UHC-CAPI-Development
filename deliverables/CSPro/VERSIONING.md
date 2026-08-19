# CAPI Build Versioning

Per-instrument build versions for the F1/F3/F4 CSEntry apps. Introduced 2026-07-02 on a
tester request: a visible version number so any device can be checked for currency (pre-test
readiness), and so builds can be tracked across UAT rounds.

## Why we roll our own

**CSEntry has no native app-version concept.** The `version:` fields inside the `.ent`/`.qsf`
are *file-format* versions ("CSPro 8.0"), not application versions — which is also why
CSEntry's ⋮ → *Update Installed Applications* cannot reliably tell whether an installed build
is current. So the project maintains its own version, stamped into artifacts that ride every
CSWeb deployment.

## The scheme — Semantic Versioning

Versions follow **`MAJOR.MINOR.PATCH`** (e.g. `v1.2.3`), mapped to this project's workflow:

| Part | Bump when | Typical trigger |
|---|---|---|
| **PATCH** | a bug-fix build deploys | the common mid-round patch (skip logic, wording, gating fixes) |
| **MINOR** | functionality is added or changed | new questions/sections (e.g. the PhilHealth-reinstatement fields), new features |
| **MAJOR** | a UAT round closes, or a breaking change ships | round-close baseline; data-shape changes (e.g. checkbox conversions that alter columns) |

Each app versions independently: **F1, F3, F4, and HUB** (the Supervisor hub — LoginApp +
MenuApp share one version, added 2026-07-02).

## Where the version shows (tester-facing, device-verified 2026-07-02 on the itel P10001L)

1. **CSEntry application list** — the app entry reads
   `Patient Survey (F3) - v1.0.1 (2026-07-02)`. Mechanism: the `.pff`
   `[Run Information] Description` line, which CSEntry Android displays verbatim
   (CSPro source: `PFF.cpp` `APPDESCRIPTION = "Description"`).
2. **The in-case title bar, on every screen** (same mechanism) — so **every bug screenshot
   identifies its build** no matter where in the form it was taken.
3. **The case-key (QN) screen** — a small blue line `Build: F3 v1.0.1 (2026-07-02)` under
   the Questionnaire Number question (every language), i.e. the first screen of every case.
   (v1.0.0 had placed this on the dict-first cover question, which the F3 form puts at
   case-END — fixed in v1.0.1 by emitting the footer on the `QUESTIONNAIRE_NUMBER` id item.)

**The Supervisor hub (HUB)** shows its version in the same app-list/title-bar surfaces
(`Supervisor Hub (HUB) - v1.0.0 (2026-07-02)` + `Supervisor Hub Menu (HUB) - …`) and as a
footer line on the role menu after login (`Hub v1.0.0 (2026-07-02)`). Unlike the
instruments, the hub's `.pff`s are **generated** by `supervisor-hub/build_hub_apps.py`,
which reads `versions.json` itself and also stamps the menu-JSON footer — so
`stamp_version.py bump HUB` simply re-runs that build (never text-edits hub pffs).

Reference screenshots: `automation/shots/versioning/`.

**"Am I up to date?"** — every patch note posted to `#f1-uat` / `#f3-uat` / `#f4-uat` states
its build number. A device is current when its app list shows the version in the channel's
latest patch note. Update path: **⋮ → Update Installed Applications detected these CSWeb
redeploys in the 2026-07-02 device test** (note: an unrelated app with a broken sync config
— e.g. the CSES tutorial apps' stale Dropbox token — pops an error first; tap OK and the
update list still appears). If the app doesn't show in the update list, **remove →
Add Application → from CSWeb** remains the sure path.

## The machinery (developer-facing)

**Single source of truth: [`versions.json`](versions.json)** — per-instrument
`{app, version, date}`. Never hand-edit the two display surfaces; they are stamped from
this file:

| Surface | Stamped by |
|---|---|
| `.pff Description` | `automation/stamp_version.py` (BOM-aware; pffs are UTF-8-BOM) |
| `.qsf` build footer | each instrument's `generate_qsf.py`, which reads `versions.json` at generation time |

**Commands** (from `deliverables/CSPro/`):

```
py automation/stamp_version.py show               # versions + drift check (pff/qsf vs json)
py automation/stamp_version.py bump F3            # PATCH bump  → restamp pff + regen qsf
py automation/stamp_version.py bump F3 --minor    # MINOR bump  (new functionality)
py automation/stamp_version.py bump F3 --major    # MAJOR bump  (round close / breaking)
py automation/stamp_version.py set F3 2.0.0       # explicit version
py automation/stamp_version.py stamp F1 F3 F4     # restamp pffs from json as-is (no bump)
```

`bump`/`set` update the JSON, restamp the `.pff`, and regenerate the `.qsf` in one atomic
step, so the surfaces cannot drift. `show` must report no drift before any deploy.

## Release workflow (per patch)

1. Fix at generator level, regenerate, bind (the cspro-patch-fix loop, unchanged).
2. **`stamp_version.py bump <KEY>`** (choose patch/minor/major per the table above).
3. Run the static gates (`preflight_validate`, `verify_questions`, `fmf_block_check`).
4. Deploy — preferred: the `.csds` spec route (`automation/open_csdeploy_spec.py
   <inst>/<Base>.csds` if the dialog isn't parked, then `automation/auto_deploy.py <KEY>
   --deploy-only`). CSDeploy compiles the `.ent → .pen` fresh from disk at the Deploy click,
   so the deployed package always carries the just-stamped pff + qsf.
5. Announce in the instrument's UAT channel **stating the new version** — the patch-note
   template lives in the cspro-patch-fix skill.

## Version history

| Date | F1 | F3 | F4 | HUB | Notes |
|---|---|---|---|---|---|
| 2026-08-19 | -- | v4.0.0 | -- | -- | F3 MAJOR: Q18 income-bracket recode (11-band 50k -> Aug-17's 7-band PSA classes, DK/RF 99/98->8/9, reverses R4/#631), Q10 civil-status paper-code permutation fix, and the missing Q26 dug-well item inserted (renumbers Q26/27/28) -- all declared data-shape breaks; plus the Q1_IS_PATIENT->PATIENT_TYPE skip-retarget defect-fix (Section G/H outpatient/inpatient routing was silently broken for the Q1=Yes path on every build from v3.1.8/2026-08-15 through v3.1.14). Deployed to CSWeb (auto_deploy.py, "successfully" popup confirmed). |
| 2026-07-03 | v1.0.2 | v1.0.2 | v1.0.3 | v1.0.0 | Pretest sweep deploys via the `.csds` route: F1/F3 ship the 2026-07-02 #450-class pos() chunk-scan wave (v1.0.2); F4 v1.0.3 adds #824 Q56 no-benefits hard-exclusive + #827 Q90 skip flip (Yes→Q94; No→Q91–Q92→Q94 — reverses #652, matches skip-logic doc §I). Patch notes in all three UAT channels. |
| 2026-07-02 | v1.0.1 | v1.0.1 | v1.0.1 | v1.0.0 | HUB versioning added (app list + menu footer), deployed via the new `supervisor-hub/LoginApp.csds`, device-verified (login → menu) + announced to #supervisor-uat. |
| 2026-07-02 | v1.0.1 | v1.0.1 | v1.0.1 | — | Build footer moved to the QN (first) screen — dict-first placement had landed on F3's case-end cover block. Device-verified + announced. |
| 2026-07-02 | v1.0.0 | v1.0.0 | v1.0.0 | — | Versioning introduced; deployed + announced. Baseline for the July pre-test. |

(Keep this table current — one row per deploy day, note the trigger.)
