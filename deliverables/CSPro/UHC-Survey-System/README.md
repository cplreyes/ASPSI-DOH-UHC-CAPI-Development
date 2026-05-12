# UHC Survey System Build

End-to-end CAPI build for the DOH UHC Year 2 Survey: F1 Facility Head, F3 Patient, F4 Household, plus F3 Patient Listing (`110_F3_listing` quartet) and F4 Barangay Listing, plus the login + menu chain. F2 Healthcare Worker is the parallel PWA track and lives elsewhere.

## Phase status

- **Phase 1** (this directory) — Foundation + F1 vertical slice + local CSWeb. See `docs/superpowers/plans/2026-05-08-uhc-survey-system-build-phase-1.md`.
- **Phase 2** — F3 Patient Listing (shipped as `110_F3_listing`), F3, F4_listing, F4 + supervisor flow + audit. Plan written after Phase 1 lands.

## Build

```bash
# Build all .pen for dev (localhost CSWeb)
python build_all.py --env=dev

# Iterate on a single instrument
python build_all.py --env=dev --only=F1

# Build for UAT (your laptop's LAN IP, tablets reach over Wi-Fi)
python build_all.py --env=uat
```

Outputs land in `dist/<env>/<NN>_<name>.pen`.

## Per-machine env config

`urls.yaml` (gitignored) carries this machine's URLs. Copy from `urls.example.yaml` and fill in your real LAN IP (and later, VPS hostname).

## Folder convention

Numbered subfolders follow Khurshid Arshad's signature CAPI scaffolding pattern (Tutorial 1: Create Login Application in CSPro @ 01:18). Even numbers hold app dirs; odd numbers hold their data dirs. External dicts and source spreadsheets sit in their own buckets so generators can find them by relative path.

## Spec & mentor alignment

Design spec: `docs/superpowers/specs/2026-05-08-uhc-survey-system-build-design.md`
Mentor lineage: Khurshid Arshad CAPI corpus at `3_Resources/Learning-Materials/mentors/khurshid-arshad/`
