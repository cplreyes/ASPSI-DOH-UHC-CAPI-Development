# CAPI final version set — 2026-08-20 (PSA submission)

The version set ASPSI is sending to PSA. **This is the reference build.** Anything after
this is development and must not be presented as the submitted instrument.

| Instrument | Version | Identity |
|---|---|---|
| F1 — Facility Head Survey | **v3.1.5** (2026-08-20) | `F1-FacilityHeadSurvey-v3.1.5.zip` |
| F2 — Healthcare Worker Survey (PWA) | **v3.0.0** | commit `4128969`, spec `2026-08-20-m2` |
| F3 — Patient Survey | **v6.0.2** (2026-08-20) | `F3-PatientSurvey-v6.0.2.zip` |
| F4 — Household Survey | **v3.1.3** (2026-08-20) | `F4-HouseholdSurvey-v3.1.3.zip` |

## What the .zip files are

Byte-for-byte the packages CSWeb was serving at capture time — the same file a tester or
PSA downloads via **Add Application → from CSWeb**. Each contains the `.pen` (the compiled
application), its `.pff`, and the 8 PSGC lookup files. `manifest.json` carries md5 and
sha256 for each, plus entry counts and the version-stamp count found inside the `.pen`.

They are stored here rather than rebuilt on demand because a rebuild is only *probably*
identical: it depends on the generator sources, the CSPro Designer version, and the
translation state on the day. These are the actual bytes.

## F2 is different

F2 is a web app, so it has no downloadable package — its identity is the deployed commit
(`4128969`) plus the live `build-info.json` at <https://uhc-hcw.asiansocial.org>. To go
back to it, redeploy that commit; the deploy script's Guard 2 re-verifies the built
artifact before anything is uploaded.

## How to restore a CSPro instrument

The fastest route back is the package itself — no rebuild required:

1. Take the `.zip` for the instrument you want.
2. Publish it to CSWeb through the Deploy Application dialog (Package name must match, as
   `automation/auto_deploy.py` enforces), **or** unzip it straight onto a tablet under
   `.../csentry/<AppFolder>/` for a local check.
3. Confirm the version in the CSEntry app list before trusting it.

To restore the *sources* that produced these, see the git tag noted below — the release
branch holds the generator state as of this build.

## Verification at capture time

- `verify_questions`: F1 321/321 · F3 375/375 · F4 333/333 reachable, 0 dead-conditions, 0 bad-skips
- `preflight_validate`: ALL CLEAN
- `csentry_verify`: F1/F3/F4 PASS
- CSPro Designer compile: Successful for all three, title bar checked
- Served packages: F1 12 entries / 8 PSGC · F3 12 / 8 · F4 13 / 8, version stamps present in every locale

## What is in this build

Everything from UAT Round 7, closed 2026-08-20: the Aug-17 instrument migration, the
cover/ICF title ruling (#1304), F3's printed section order restored (#1305), F3 Q88
converted to a tick-list (ANA-324), and the repeating-text de-duplication across all three
instruments (#1306/#1307/#1309) including roster fields and the verification-photo option.

## After this point

Development continues on **non-production versions** so the submitted set stays
unambiguous. See `deliverables/CSPro/versions.json` for the scheme in force.
