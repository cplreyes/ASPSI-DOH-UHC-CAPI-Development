---
type: concept
tags: [cspro, dcf, capi, gps, photo-capture, verification, mvp]
source_count: 1
---

# GPS and Photo Capture

> [!info] As-built revision (2026-06-12)
> The original design used manual trigger items (`*_CAPTURE_GPS`, `*_CAPTURE_VERIFICATION_PHOTO`) with re-arm on reverse navigation. As shipped 2026-06-12: GPS is fully automatic (`ReadGPSReading` fires `onfocus` of the first GPS field; trigger items removed from the dictionaries) and the verification photo moved to a dedicated end-of-survey `REC_CASE_VERIFICATION` form, outcome-gated per instrument. The tables and flow below reflect the shipped design. (Source: log.md entry 2026-06-12)

Every [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Dictionary|F-series instrument]] (F1, F3, F4) auto-captures a GPS reading and a single end-of-interview verification photo. The CAPI runtime writes the GPS metadata to a record-scoped block of items and the photo file to tablet storage, with the saved filename reflected in the dictionary.

## Why

- **GPS** — per-case geolocation feeds the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]] map tab for field-progress monitoring and post-fieldwork geospatial analysis. Complements the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets|PSGC]] administrative coding (PSGC ≠ GPS: admin boundary vs. point location).
- **Photo** — content-neutral verification artifact; protocol/training decides what the enumerator captures (facility signage, consent sheet, respondent setting — whatever the SOP prescribes). Primary purpose: audit trail for interviewer presence + field-edit QC.

## Items (per instrument)

| Instrument | GPS blocks | Photo | Linkage | Total new items |
|---|---|---|---|---|
| **F1** (Facility Head) | 1 × `FACILITY_GPS_*` | 1 | — | **7** |
| **F3** (Patient) | 2: `FACILITY_GPS_*` + `P_HOME_GPS_*` | 1 | `F3_FACILITY_ID` (→ F1) | **14** |
| **F4** (Household) | 1: `HH_GPS_*` + existing `LATITUDE`/`LONGITUDE` reused | 1 | — | **5** |

Each GPS block has the same 6 items: `{prefix}GPS_LATITUDE` (alpha 12), `{prefix}GPS_LONGITUDE` (alpha 12), `{prefix}GPS_ALTITUDE` (alpha 10), `{prefix}GPS_ACCURACY` (num 3), `{prefix}GPS_SATELLITES` (num 2), `{prefix}GPS_READTIME` (alpha 19). The former `{prefix}CAPTURE_GPS` (num 1) trigger items were removed from the dictionaries when GPS auto-fetch shipped (2026-06-12).

The photo block is a single item: `{prefix}VERIFICATION_PHOTO_FILENAME` (alpha 120, stores the saved JPG's filename), living on the dedicated end-of-survey `REC_CASE_VERIFICATION` form. The former `{prefix}CAPTURE_VERIFICATION_PHOTO` trigger item is likewise gone — capture fires once `onfocus` (see flow below).

## Where the pieces live

| Artifact | Path | Purpose |
|---|---|---|
| Python emitters | `deliverables/CSPro/cspro_helpers.py` — `_gps_fields(prefix)`, `_photo_block(prefix)` | Reusable item builders |
| CSPro logic module | `deliverables/CSPro/shared/Capture-Helpers.apc` | `ReadGPSReading(maxTimeSec, desiredAccuracyM)` + `TakeVerificationPhoto(filename)` |
| F1 wiring | `deliverables/CSPro/F1/generate_dcf.py` → `build_capture_record()` | Adds `REC_FACILITY_CAPTURE` (type Z) |
| F3 wiring | `deliverables/CSPro/F3/generate_dcf.py` → `build_f3_facility_capture/patient_home_capture/case_verification` | 3 new records (Z/Y/X) + `F3_FACILITY_ID` on `PATIENT_GEO_ID` |
| F4 wiring | `deliverables/CSPro/F4/generate_dcf.py` → `build_f4_geo_id` (augmented) + `build_f4_case_verification` | 4 items onto `HOUSEHOLD_GEO_ID` + `REC_CASE_VERIFICATION` (type Z) |

## Capture flow (runtime, as-built 2026-06-12)

**GPS — auto-fetch, no enumerator trigger:**

1. `onfocus` of the **first GPS field** in each block auto-fires `ReadGPSReading(120, 20)` — opens GPS radio, reads up to 120 s with 20 m target accuracy, closes radio.
2. Handler assigns `gps(latitude)`, `gps(longitude)`, `gps(altitude)`, `gps(accuracy)`, `gps(satellites)`, `gps(readtime)` to the block's items and `protect()`s the GPS fields.
3. The protect is applied **once, guarded on `READTIME`**: fields only lock after a reading exists, so a blank/no-fix block stays enterable and re-focusing retries the read instead of trapping empty fields.

**Photo — dedicated end-of-survey verification form:**

4. The verification photo lives on a dedicated END-of-survey form (`REC_CASE_VERIFICATION`), skip-gated on per-instrument `ENUM_RESULT_FINAL_VISIT` outcome sets — F1 {1, 4}, F3 {1, 2, 4, 5}, F4 {1, 3}. Cases with other final-visit outcomes skip the photo form entirely.
5. Capture fires **once on `onfocus`**: `TakeVerificationPhoto()` launches the Android camera, resamples to ≤1600×1200, saves at quality 85 under the filename `case-<12-digit QN>.jpg` (the case's 12-digit [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|QUESTIONNAIRE_NUMBER]]). A failed capture raises a soft `errmsg` — it never traps, so the interview can always be completed.

## Why filename reference instead of a binary dictionary item

CSPro 8.0 supports four binary item types (Image, Audio, Document, Geometry), but they are flagged **experimental** (require the "Enable Binary Items (experimental)" dictionary flag, can't appear on forms, exact JSON schema undocumented in public 8.0 specs). For MVP stability we took the non-experimental path: save the photo to tablet storage via `Image.save(filename)` and record only the filename in an alpha item. CSWeb syncs the actual JPG via CSEntry's standard attachments mechanism rather than as dictionary data.

Tradeoff: binary items would have given a slightly more integrated data model (photo travels with the case JSON). Filename-reference gives us predictable behaviour, no experimental flags, and unlocks the binary-item upgrade path later without breaking stored data.

## F1 ↔ F3 linkage

F3 cases carry `F3_FACILITY_ID` (numeric 10, zero-fill, on `PATIENT_GEO_ID`) — the PSGC-compatible facility code that ties a F3 patient case back to its sampled F1 facility. For MVP the enumerator populates this from the paper [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol|F3b listing sheet]]; a CSPro patient-listing mini-app that auto-fills it is deferred to post-MVP wishlist.

**Status (2026-06-12):** `F3_FACILITY_ID` is the as-built linkage as of 2026-06-12; it is slated for retirement under the shipped single-[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|Questionnaire Number]] design.

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
- Audio recording — out of MVP scope (Audio binary items are experimental in 8.0; same non-experimental rationale as the photo filename decision)
- Video recording — not officially supported

## Related

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets|PSGC Value Sets]] — administrative geocoding (complements GPS)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Dictionary|CSPro Data Dictionary]] — where these items live
- Plan: `docs/superpowers/plans/2026-04-21-gps-photo-capture-f1-f3-f4.md`
