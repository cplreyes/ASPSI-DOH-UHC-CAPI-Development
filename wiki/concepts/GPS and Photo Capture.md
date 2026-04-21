---
type: concept
tags: [cspro, dcf, capi, gps, photo-capture, verification, mvp]
source_count: 1
---

# GPS and Photo Capture

Every [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Dictionary|F-series instrument]] (F1, F3, F4) auto-captures a GPS reading and a single end-of-interview verification photo. The CAPI runtime writes the GPS metadata to a record-scoped block of items and the photo file to tablet storage, with the saved filename reflected in the dictionary.

## Why

- **GPS** — per-case geolocation feeds the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/CSWeb|CSWeb]] map tab for field-progress monitoring and post-fieldwork geospatial analysis. Complements the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets|PSGC]] administrative coding (PSGC ≠ GPS: admin boundary vs. point location).
- **Photo** — content-neutral verification artifact; protocol/training decides what the enumerator captures (facility signage, consent sheet, respondent setting — whatever the SOP prescribes). Primary purpose: audit trail for interviewer presence + field-edit QC.

## Items (per instrument)

| Instrument | GPS blocks | Photo | Linkage | Total new items |
|---|---|---|---|---|
| **F1** (Facility Head) | 1 × `FACILITY_GPS_*` | 1 | — | **9** |
| **F3** (Patient) | 2: `FACILITY_GPS_*` + `P_HOME_GPS_*` | 1 | `F3_FACILITY_ID` (→ F1) | **17** |
| **F4** (Household) | 1: `HH_GPS_*` + existing `LATITUDE`/`LONGITUDE` reused | 1 | — | **7** |

Each GPS block has the same 7 items: `{prefix}GPS_LATITUDE` (alpha 12), `{prefix}GPS_LONGITUDE` (alpha 12), `{prefix}GPS_ALTITUDE` (alpha 10), `{prefix}GPS_ACCURACY` (num 3), `{prefix}GPS_SATELLITES` (num 2), `{prefix}GPS_READTIME` (alpha 19), `{prefix}CAPTURE_GPS` (num 1 trigger).

Each photo block has 2 items: `{prefix}VERIFICATION_PHOTO_FILENAME` (alpha 120, stores the saved JPG's filename) + `{prefix}CAPTURE_VERIFICATION_PHOTO` (num 1 trigger).

## Where the pieces live

| Artifact | Path | Purpose |
|---|---|---|
| Python emitters | `deliverables/CSPro/cspro_helpers.py` — `_gps_fields(prefix)`, `_photo_block(prefix)` | Reusable item builders |
| CSPro logic module | `deliverables/CSPro/shared/Capture-Helpers.apc` | `ReadGPSReading(maxTimeSec, desiredAccuracyM)` + `TakeVerificationPhoto(filename)` |
| F1 wiring | `deliverables/CSPro/F1/generate_dcf.py` → `build_capture_record()` | Adds `REC_FACILITY_CAPTURE` (type Z) |
| F3 wiring | `deliverables/CSPro/F3/generate_dcf.py` → `build_f3_facility_capture/patient_home_capture/case_verification` | 3 new records (Z/Y/X) + `F3_FACILITY_ID` on `PATIENT_GEO_ID` |
| F4 wiring | `deliverables/CSPro/F4/generate_dcf.py` → `build_f4_geo_id` (augmented) + `build_f4_case_verification` | 5 items onto `HOUSEHOLD_GEO_ID` + `REC_CASE_VERIFICATION` (type Z) |

## Capture flow (runtime)

1. Enumerator reaches the trigger item (e.g. `FACILITY_CAPTURE_GPS`).
2. `onfocus` handler calls `ReadGPSReading(120, 20)` — opens GPS radio, reads up to 120 s with 20 m target accuracy, closes radio.
3. Handler assigns `gps(latitude)`, `gps(longitude)`, `gps(altitude)`, `gps(accuracy)`, `gps(satellites)`, `gps(readtime)` to the block's items.
4. For the photo trigger: handler calls `TakeVerificationPhoto("case-<id>-verification.jpg")` which launches the Android camera, resamples to ≤1600×1200, saves at quality 85, and returns success.
5. Handler resets the trigger to `notappl` so the button re-arms for reverse navigation.

## Why filename reference instead of a binary dictionary item

CSPro 8.0 supports four binary item types (Image, Audio, Document, Geometry), but they are flagged **experimental** (require the "Enable Binary Items (experimental)" dictionary flag, can't appear on forms, exact JSON schema undocumented in public 8.0 specs). For MVP stability we took the non-experimental path: save the photo to tablet storage via `Image.save(filename)` and record only the filename in an alpha item. CSWeb syncs the actual JPG via CSEntry's standard attachments mechanism rather than as dictionary data.

Tradeoff: binary items would have given a slightly more integrated data model (photo travels with the case JSON). Filename-reference gives us predictable behaviour, no experimental flags, and unlocks the binary-item upgrade path later without breaking stored data.

## F1 ↔ F3 linkage

F3 cases carry `F3_FACILITY_ID` (numeric 10, zero-fill, on `PATIENT_GEO_ID`) — the PSGC-compatible facility code that ties a F3 patient case back to its sampled F1 facility. For MVP the enumerator populates this from the paper [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F3b Listing Protocol|F3b listing sheet]]; a CSPro patient-listing mini-app that auto-fills it is deferred to post-MVP wishlist.

## Ethics

Per-case verification photos require SJREB ethics addendum describing:
- Purpose (QC/interviewer-presence verification, not respondent identification)
- Content scope (prescribed by fieldwork SOP, not ad-hoc)
- Storage (encrypted tablet + CSWeb, access limited to field managers + QC leads)
- Retention (aligned with UHC Year 2 DOH data retention schedule)

This is Carl's item outside the code, tracked separately.

## Out of scope (MVP cut)

- Patient-listing CSPro mini-app (auto-populate `F3_FACILITY_ID`) — paper F3b works
- CSPro 8.0 binary dictionary items — use filename reference path instead
- Audio recording — not supported in 8.0
- Video recording — not officially supported

## Related

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets|PSGC Value Sets]] — administrative geocoding (complements GPS)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Dictionary|CSPro Data Dictionary]] — where these items live
- Plan: `docs/superpowers/plans/2026-04-21-gps-photo-capture-f1-f3-f4.md`
