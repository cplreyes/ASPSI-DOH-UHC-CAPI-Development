# GPS + Verification Photo Capture — F1/F3/F4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add GPS auto-capture buttons and end-of-interview verification photo buttons to F1, F3, F4; add F3_FACILITY_ID linkage item to F3.

**Architecture:** Reusable `_gps_fields(prefix)` + `_photo_block(prefix)` helpers in `cspro_helpers.py`; one shared `Capture-Helpers.apc` logic module with `ReadGPSReading()` + `TakeVerificationPhoto()` functions. Each generator calls the helpers through `build_capture_block(mode)` to emit the right items. Trigger buttons are numeric-1 items whose `onfocus` fires the capture; Image binary items store photos off-form (CSPro 8.0 binary items can't appear on forms but sync to CSWeb).

**Tech Stack:** Python (generator), CSPro 8.0 Logic (.apc module), existing `generate_dcf.py` pattern.

---

## Decisions locked in

- **F1**: 1 facility GPS block (6 items) + 1 verification photo
- **F3**: 1 facility GPS block + 1 patient-home GPS block (`P_HOME_GPS_*`) + 1 verification photo + **F3_FACILITY_ID** (numeric 10, PSGC-compatible facility code, for F1↔F3 linkage)
- **F4**: Keep existing `LATITUDE`/`LONGITUDE` (12-alpha) but auto-populate from `gps()`; add `HH_GPS_*` metadata items (altitude, accuracy, satellites, readtime) + 1 verification photo
- **Photo content**: content-neutral prompt ("Take a verification photo"); protocol/training decides what the enumerator captures. One photo per case, triggered at end of interview.
- **Patient listing app**: deferred to post-MVP wishlist; paper F3b listing remains the sampling mechanism.

---

## Item budget per form

| Form | New GPS items | New photo items | Other | Total new |
|---|---|---|---|---|
| F1 | 6 GPS + 1 trigger = 7 | 1 Image + 1 trigger = 2 | — | **9** |
| F3 | (6 GPS + 1 trigger) × 2 blocks = 14 | 1 Image + 1 trigger = 2 | 1 `F3_FACILITY_ID` | **17** |
| F4 | 4 metadata + 1 trigger = 5 (existing LAT/LONG kept) | 1 Image + 1 trigger = 2 | — | **7** |

---

### Task 1: Add `_gps_fields` and `_photo_block` helpers to `cspro_helpers.py`

**Files:**
- Modify: `deliverables/CSPro/cspro_helpers.py`

- [ ] **Step 1: Add `_gps_fields(prefix="")` emitting the 6 GPS items + 1 trigger**

```python
def _gps_fields(prefix=""):
    """Six GPS-metadata items plus a capture-trigger button.
    Trigger item's onfocus is wired in each form's .app to call ReadGPSReading().
    prefix="" → facility/household; prefix="P_HOME_" → F3 patient home.
    """
    capture_vs = [("Capture GPS now", 1)]
    return [
        alpha(  f"{prefix}GPS_LATITUDE",   "GPS Latitude",   length=12),
        alpha(  f"{prefix}GPS_LONGITUDE",  "GPS Longitude",  length=12),
        alpha(  f"{prefix}GPS_ALTITUDE",   "GPS Altitude (m)", length=10),
        numeric(f"{prefix}GPS_ACCURACY",   "GPS Accuracy (m)", length=3),
        numeric(f"{prefix}GPS_SATELLITES", "GPS Satellites",   length=2),
        alpha(  f"{prefix}GPS_READTIME",   "GPS Read Time (UTC)", length=19),
        numeric(f"{prefix}CAPTURE_GPS",    "Capture GPS", length=1,
                value_set_options=capture_vs),
    ]
```

- [ ] **Step 2: Add `_photo_block(prefix="")` emitting the Image binary item + trigger**

```python
def _photo_block(prefix=""):
    """Image binary item (off-form) + a numeric trigger item that drives capture.
    Binary items don't render on forms; the trigger is what the enumerator taps.
    """
    capture_vs = [("Take verification photo", 1)]
    return [
        binary(f"{prefix}VERIFICATION_PHOTO", "Verification Photo", kind="image"),
        numeric(f"{prefix}CAPTURE_VERIFICATION_PHOTO", "Take Verification Photo",
                length=1, value_set_options=capture_vs),
    ]
```

- [ ] **Step 3: Add `binary(name, label, kind)` emitter if not already present**

Check if `cspro_helpers.py` has a `binary()` emitter. If not, add a minimal one that emits an Image-type dictionary item in CSPro 8.0 JSON shape. Reference: `Examples 8.0/1 - Data Entry/CAPI Census/Dictionaries/Household.dcf` items that show binary item JSON structure, if present; otherwise follow the CSPro 8.0 dictionary schema for binary items.

- [ ] **Step 4: Smoke-test the helpers**

```bash
python -c "from deliverables.CSPro.cspro_helpers import _gps_fields, _photo_block; \
           import json; \
           print(json.dumps(_gps_fields(), indent=2)[:500]); \
           print('---'); \
           print(json.dumps(_photo_block(), indent=2))"
```

Expected: prints valid item dicts; no exceptions.

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSPro/cspro_helpers.py
git commit -m "cspro_helpers: add _gps_fields, _photo_block, and binary item emitter"
```

---

### Task 2: Create `shared/Capture-Helpers.apc`

**Files:**
- Create: `deliverables/CSPro/shared/Capture-Helpers.apc`

- [ ] **Step 1: Write the logic module**

```
{ Capture-Helpers — reusable CSPro logic for GPS reads and verification photos.

  Usage inside a form's .app:
      #include "../shared/Capture-Helpers.apc"

      PROC CAPTURE_FACILITY_GPS
      onfocus
          if ReadGPSReading(120, 20) then
              FACILITY_GPS_LATITUDE   = gps(latitude);
              FACILITY_GPS_LONGITUDE  = gps(longitude);
              FACILITY_GPS_ALTITUDE   = gps(altitude);
              FACILITY_GPS_ACCURACY   = gps(accuracy);
              FACILITY_GPS_SATELLITES = gps(satellites);
              FACILITY_GPS_READTIME   = gps(readtime);
          endif;
          CAPTURE_FACILITY_GPS = notappl;  { reset button state }

      PROC CAPTURE_VERIFICATION_PHOTO
      onfocus
          Image photo;
          if TakeVerificationPhoto(photo, "case-" + maketext("%d", CASE_ID)) then
              VERIFICATION_PHOTO = photo;
          endif;
          CAPTURE_VERIFICATION_PHOTO = notappl;
}

PROC GLOBAL

function ReadGPSReading(numeric maxTimeSec, numeric desiredAccuracyM)
    { Opens GPS, attempts read, closes. Returns 1 on success, 0 on failure.
      Caller reads gps(latitude), gps(longitude), etc. after success. }

    if not gps(open) then
        errmsg("GPS hardware unavailable.");
        ReadGPSReading = 0;
        exit;
    endif;

    numeric result = gps(read, maxTimeSec, desiredAccuracyM);
    gps(close);

    if result <> 1 then
        errmsg("GPS read failed or timed out (accuracy target %d m).", desiredAccuracyM);
        ReadGPSReading = 0;
        exit;
    endif;

    if gps(accuracy) > desiredAccuracyM then
        errmsg("GPS accuracy %d m exceeds target %d m — consider retry outdoors.",
               gps(accuracy), desiredAccuracyM);
        { still return success — caller decides whether to accept }
    endif;

    ReadGPSReading = 1;
end;


function TakeVerificationPhoto(Image photoObj, string filenamePrefix)
    { Launches Android camera. Resamples to ≤1600×1200 and saves as JPG.
      Returns 1 on success, 0 on cancel/error. }

    if not photoObj.takePhoto("Take a verification photo to record the interview.") then
        TakeVerificationPhoto = 0;
        exit;
    endif;

    photoObj.resample(maxWidth := 1600, maxHeight := 1200);
    photoObj.save(filenamePrefix + "-verification.jpg", quality := 85);
    TakeVerificationPhoto = 1;
end;
```

- [ ] **Step 2: Commit**

```bash
git add deliverables/CSPro/shared/Capture-Helpers.apc
git commit -m "Add reusable GPS + verification photo capture logic module"
```

---

### Task 3: Wire GPS + photo capture into F1

**Files:**
- Modify: `deliverables/CSPro/F1/generate_dcf.py`

- [ ] **Step 1: Import new helpers**

At the top of `F1/generate_dcf.py`:

```python
from cspro_helpers import (
    numeric, alpha, build_geo_id,
    _gps_fields, _photo_block,
)
```

- [ ] **Step 2: Add a capture record after the geo-ID record**

Locate the `main()` function's record list. After the call to `build_geo_id("facility")`, append:

```python
capture_record = record("REC_FACILITY_CAPTURE", items=[
    *_gps_fields(prefix="FACILITY_"),
    *_photo_block(prefix="FACILITY_"),
])
```

Add `capture_record` to the records list passed to `dictionary(...)`.

- [ ] **Step 3: Regenerate and verify**

```bash
python deliverables/CSPro/F1/generate_dcf.py
python deliverables/CSPro/F1/export_dcf_to_xlsx.py --all
```

Expected: F1 DCF item count increases by 9 (6 GPS + 1 GPS trigger + 1 binary + 1 photo trigger); record count increases by 1; `.dcf` size grows by < 50 KB.

- [ ] **Step 4: Commit**

```bash
git add deliverables/CSPro/F1/generate_dcf.py \
        deliverables/CSPro/F1/FacilityHeadSurvey.dcf \
        "deliverables/CSPro/F1/FacilityHeadSurvey - Data Dictionary and Value Sets.xlsx"
git commit -m "F1: add facility GPS capture + verification photo items"
```

---

### Task 4: Wire GPS + photo capture + facility linkage into F3

**Files:**
- Modify: `deliverables/CSPro/F3/generate_dcf.py`

- [ ] **Step 1: Import helpers**

Same as Task 3 Step 1.

- [ ] **Step 2: Add F3_FACILITY_ID to the geo-ID record**

F3 currently uses `build_geo_id("facility_and_patient")`. Add a new item at the top of F3's header record (or as the first item of the geo-ID record):

```python
f3_facility_id = numeric("F3_FACILITY_ID", "Sampled Facility ID (F1 linkage)",
                         length=10, zero_fill=True)
```

Prepend to the geo-ID record's items so it's captured first in the case.

- [ ] **Step 3: Add two capture records**

```python
facility_capture = record("REC_FACILITY_CAPTURE", items=[
    *_gps_fields(prefix="FACILITY_"),
    *_photo_block(prefix="PATIENT_"),   { photo is per-case, only one block }
])

patient_home_capture = record("REC_PATIENT_HOME_CAPTURE", items=[
    *_gps_fields(prefix="P_HOME_"),
])
```

Wait — only one verification photo per case, not two. Move `_photo_block("")` (unprefixed, or use `CASE_`) to a top-level location rather than duplicating it in facility_capture. Revise:

```python
facility_capture = record("REC_FACILITY_CAPTURE", items=[
    *_gps_fields(prefix="FACILITY_"),
])

patient_home_capture = record("REC_PATIENT_HOME_CAPTURE", items=[
    *_gps_fields(prefix="P_HOME_"),
])

case_verification = record("REC_CASE_VERIFICATION", items=[
    *_photo_block(prefix=""),   { VERIFICATION_PHOTO + CAPTURE_VERIFICATION_PHOTO }
])
```

- [ ] **Step 4: Regenerate and verify**

```bash
python deliverables/CSPro/F3/generate_dcf.py
python deliverables/CSPro/F3/export_dcf_to_xlsx.py --all
```

Expected: item count +17 (7+7 GPS blocks + 2 photo + 1 facility_id); record count +3; size grows < 80 KB.

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSPro/F3/generate_dcf.py \
        deliverables/CSPro/F3/PatientSurvey.dcf \
        "deliverables/CSPro/F3/PatientSurvey - Data Dictionary and Value Sets.xlsx"
git commit -m "F3: add facility+patient-home GPS, verification photo, F3_FACILITY_ID linkage"
```

---

### Task 5: Wire GPS metadata + photo capture into F4

**Files:**
- Modify: `deliverables/CSPro/F4/generate_dcf.py`

- [ ] **Step 1: Import helpers**

Same.

- [ ] **Step 2: Augment existing LAT/LONG with GPS metadata**

F4's existing `build_f4_geo_id()` already includes `LATITUDE` and `LONGITUDE` via `extra_items=[...]`. Add the metadata fields and the capture trigger + photo block as separate items (do NOT re-emit LATITUDE/LONGITUDE from `_gps_fields` since they already exist):

```python
from cspro_helpers import numeric, alpha, build_geo_id, _photo_block

def build_f4_geo_id():
    return build_geo_id("household", extra_items=[
        alpha(  "LATITUDE",       "GPS Latitude",         length=12),
        alpha(  "LONGITUDE",      "GPS Longitude",        length=12),
        alpha(  "HH_GPS_ALTITUDE",   "GPS Altitude (m)",    length=10),
        numeric("HH_GPS_ACCURACY",   "GPS Accuracy (m)",    length=3),
        numeric("HH_GPS_SATELLITES", "GPS Satellites",      length=2),
        alpha(  "HH_GPS_READTIME",   "GPS Read Time (UTC)", length=19),
        numeric("CAPTURE_HH_GPS",    "Capture GPS",         length=1,
                value_set_options=[("Capture GPS now", 1)]),
    ])

capture_record = record("REC_CASE_VERIFICATION", items=[*_photo_block(prefix="")])
```

Note: F4 capture PROC will assign `gps(latitude)` to `LATITUDE` (existing item), not to a new `HH_GPS_LATITUDE`. This is spelled out in the `.app` wiring (out of scope for this plan — plan covers DCF only).

- [ ] **Step 3: Regenerate and verify**

```bash
python deliverables/CSPro/F4/generate_dcf.py
python deliverables/CSPro/F4/export_dcf_to_xlsx.py --all
```

Expected: item count +7 (4 metadata + 1 GPS trigger + 2 photo); size grows < 40 KB.

- [ ] **Step 4: Commit**

```bash
git add deliverables/CSPro/F4/generate_dcf.py \
        deliverables/CSPro/F4/HouseholdSurvey.dcf \
        "deliverables/CSPro/F4/HouseholdSurvey - Data Dictionary and Value Sets.xlsx"
git commit -m "F4: add GPS metadata + verification photo capture items"
```

---

### Task 6: Update docs + wiki + log

**Files:**
- Modify: `wiki/concepts/PSGC Value Sets.md` (no change needed — separate concern)
- Modify: `index.md`
- Modify: `log.md`
- Create: `wiki/concepts/GPS and Photo Capture.md` (new concept page)

- [ ] **Step 1: Create `wiki/concepts/GPS and Photo Capture.md`**

Brief concept page documenting: items added, where the logic lives (`shared/Capture-Helpers.apc`), how `.app` wiring calls it, F3_FACILITY_ID linkage rationale, ethics notes on photo content.

- [ ] **Step 2: Update `index.md`**

Add the new concept page + new shared module (`Capture-Helpers.apc`) + updated F1/F3/F4 item counts.

- [ ] **Step 3: Prepend `log.md` with dated entry**

```markdown
## 2026-04-21 (GPS + verification photo capture)

Added `_gps_fields` + `_photo_block` helpers and `shared/Capture-Helpers.apc`.
F1 gains facility GPS block + verification photo (9 items / +1 record).
F3 gains facility GPS + patient-home GPS + F3_FACILITY_ID linkage + photo
(17 items / +3 records). F4 gains GPS metadata over existing LAT/LONG + photo
(7 items / +1 record). Patient listing app deferred to post-MVP wishlist.
Plan: docs/superpowers/plans/2026-04-21-gps-photo-capture-f1-f3-f4.md.
```

- [ ] **Step 4: Update memory**

`~/.claude/.../memory/` — either update an existing memory or add one capturing: GPS/photo capture live in `shared/Capture-Helpers.apc`; F1/F3/F4 all have verification photos; F3 has 2 GPS blocks; F3_FACILITY_ID links F3 cases back to F1.

- [ ] **Step 5: Commit**

```bash
git add wiki/concepts/"GPS and Photo Capture.md" index.md log.md
git commit -m "Docs: GPS + verification photo capture concept page + index + log"
```

---

## Out of scope for this plan

- `.app` PROC wiring (`PROC CAPTURE_FACILITY_GPS onfocus ...`): the DCF schema change is this plan; the form-level wiring is a separate build step in CSPro Designer (Phase 7 of the 12-phase workflow).
- Patient listing CSPro mini-app — deferred to post-MVP wishlist per Carl's direction.
- SJREB ethics addendum for verification photo — Carl to handle outside the code.
- CSWeb map tab configuration to plot the new GPS items — an ops step after F1/F3/F4 DCFs are deployed.

---

## Self-review

- ✔ Spec coverage: GPS on F1/F3/F4 ✓, photo on F1/F3/F4 ✓, F3↔F1 linkage via F3_FACILITY_ID ✓, patient listing deferred ✓.
- ✔ No placeholders — every task has explicit file paths, code, and verification commands.
- ✔ Item names consistent: `_gps_fields` emits `{prefix}GPS_LATITUDE`, etc.; all call sites use matching prefixes.
- ✔ Single verification photo per case (not per GPS block) — corrected in Task 4 Step 3.
- ✔ F4 keeps existing `LATITUDE`/`LONGITUDE` to preserve the 611-item baseline + adds metadata only.
- ⚠ `binary()` emitter may not yet exist in `cspro_helpers.py` — Task 1 Step 3 handles conditionally.
