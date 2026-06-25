# Supervisor App — Phase 3 (Facility Visit Log) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the DOH-Manual-named **Supervisor App** — a standalone CSEntry data-capture app (`SupervisorApp`) for the Field Supervisor to log facility touchpoints with auto GPS + timestamp, syncing to CSWeb.

**Architecture:** A new generator-built CSPro 8 entry app under `deliverables/CSPro/SV/`, mirroring the F1 model (`has_fmf_gen=False` — generators own the `.dcf`/`.ent.apc`; the `.fmf` form is Designer-bootstrapped + hand-maintained). One case per facility (keyed by the 9-digit facility code `RRPPMMMFF`): a header record, a once-per-facility courtesy-call record, and a repeating touchpoint roster whose `TP_TYPE` postproc auto-stamps GPS + timestamp (via the shared `Capture-Helpers.apc` `ReadGPSReading`/`gps()` functions, **inlined** into `PROC GLOBAL`) and protects them. Syncs to CSWeb under the FS account like any instrument.

**Tech Stack:** Python 3 generators (reuse `deliverables/CSPro/cspro_helpers.py`) · CSPro 8.0 Designer (compile + publish) · CSEntry 8.0 (Android, itel) · CSWeb 8.0.1 (`csweb.asiansocial.org`) · pytest (generator structural tests) · the build/deploy automation in `deliverables/CSPro/automation/`.

## Global Constraints

- **Iron rule:** never hand-edit `.dcf` / `.ent.apc` — edit the generator and regenerate. (The `.fmf` is the one hand/Designer-maintained file, exactly like F1.)
- **CSEntry forbids `#include` and any code before the first `PROC`.** Shared helpers (`ReadGPSReading`, `TakeVerificationPhoto`) MUST be **inlined into the single `PROC GLOBAL`** via the `_inline_shared()` pattern (verified 2026-06-08; same as F1 `generate_apc.py`).
- **Binary `Image` items cannot be placed on a form** — `VERIFICATION_PHOTO_IMAGE` is off-form; capture is driven from the on-form `CAPTURE_VERIFICATION_PHOTO` trigger. Exclude it from the `.fmf`.
- **Lenient compile vs. strict Publish:** the Designer Ctrl+L compile is lenient; the **Publish packager is the real gate**. A clean compile does NOT guarantee Publish succeeds.
- **Fixed-width codes**: `TP_TYPE` codes are single-digit `1`–`8`; the facility key is numeric length 9, zero-filled.
- **Deploy target:** `csweb.asiansocial.org` (the `auto_deploy.py` URL guard enforces this).
- **Do NOT git commit or push** — Carl handles git for all CAPI work ([[feedback_no_git]]). Each task ends by leaving a **clean, verified working tree** for Carl; "checkpoint" steps replace commits.
- **v1 scope** (from the spec): facility log only (no household Visit Sheet); typed 9-digit `FACILITY_CODE` (no PSGC cascade / external dicts in v1); one optional HCW-list photo per case (per-touchpoint photos deferred); EN-only labels (locale drop-in later); no custom question-text polish in v1 (CSEntry falls back to dcf labels; Designer bootstrap creates a valid empty `.qsf`).

---

## File Structure

| File | Responsibility | Owner |
|---|---|---|
| `deliverables/CSPro/SV/generate_dcf.py` | Build `SUPERVISORAPP_DICT` (header + courtesy-call + touchpoint roster) → `SupervisorApp.dcf` | **create** |
| `deliverables/CSPro/SV/generate_apc.py` | Emit `SupervisorApp.ent.apc` (inlined helpers + TP_TYPE auto-stamp + note gate + photo trigger) | **create** |
| `deliverables/CSPro/SV/tests/test_generate_dcf.py` | Structural assertions on the dictionary | **create** |
| `deliverables/CSPro/SV/tests/test_generate_apc.py` | Substring assertions on the generated `.apc` | **create** |
| `deliverables/CSPro/SV/SupervisorApp.dcf` | Generated dictionary | generated |
| `deliverables/CSPro/SV/SupervisorApp.ent.apc` | Generated logic | generated |
| `deliverables/CSPro/SV/SupervisorApp.ent` / `.fmf` / `.ent.qsf` / `.ent.mgf` / `.pff` | App shell (Designer-bootstrapped; `.fmf` hand-maintained) | Designer |
| `deliverables/CSPro/automation/cspro_compile_driver.py:58` | Add `"SV"` to `SPECS` | **modify** |
| `deliverables/CSPro/automation/auto_deploy.py:25` | Add `"SV"` to `INSTRUMENTS` | **modify** |
| `deliverables/CSPro/SV/README.md` + `docs/.../Supervisor-App-FS-SOP.md` | Generator README + FS field SOP | **create** |

---

## Task 1: Dictionary generator (`generate_dcf.py`)

**Files:**
- Create: `deliverables/CSPro/SV/generate_dcf.py`
- Create: `deliverables/CSPro/SV/tests/test_generate_dcf.py`
- Produces (on run): `deliverables/CSPro/SV/SupervisorApp.dcf`

**Interfaces:**
- Consumes: `cspro_helpers.{numeric, alpha, select_one, yes_no, record, _gps_fields, _photo_block, build_dictionary, write_dcf, apply_translations}` (existing).
- Produces: `build_sv_dictionary() -> dict` (full CSPro dict); `TP_TYPES` (list of `(label, code)`); a `.dcf` whose level id is `FACILITY_CODE` (numeric, length 9) and whose records are `VISIT_HEADER` (type `H`), `COURTESY_CALL` (type `C`), `TOUCHPOINT` (type `T`, repeating, `max_occurs=30`, `required=False`).

- [ ] **Step 1: Write the failing test**

Create `deliverables/CSPro/SV/tests/test_generate_dcf.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generate_dcf import build_sv_dictionary, TP_TYPES


def _items(rec):
    return {it["name"]: it for it in rec["items"]}


def test_dictionary_shape():
    d = build_sv_dictionary()
    assert d["name"] == "SUPERVISORAPP_DICT"
    level = d["levels"][0]
    # Case key = the 9-digit facility code
    ids = level["ids"]["items"]
    assert ids[0]["name"] == "FACILITY_CODE"
    assert ids[0]["length"] == 9 and ids[0]["zeroFill"] is True
    recs = {r["name"]: r for r in level["records"]}
    assert set(recs) == {"VISIT_HEADER", "COURTESY_CALL", "TOUCHPOINT"}


def test_touchpoint_roster_is_repeating_with_gps_and_timestamp():
    recs = {r["name"]: r for r in build_sv_dictionary()["levels"][0]["records"]}
    tp = recs["TOUCHPOINT"]
    assert tp["recordType"] == "T"
    assert tp["occurrences"] == {"required": False, "maximum": 30}
    items = _items(tp)
    # type, timestamp, full GPS block, line index, note
    for name in ("TP_LINE", "TP_TYPE", "TP_TIMESTAMP", "TP_GPS_LATITUDE",
                 "TP_GPS_LONGITUDE", "TP_GPS_ACCURACY", "TP_GPS_READTIME",
                 "TP_OUTCOME_NOTE"):
        assert name in items, name
    # TP_TYPE carries the 8-code value set
    vs = items["TP_TYPE"]["valueSets"][0]["values"]
    assert len(vs) == len(TP_TYPES) == 8
    assert vs[0]["pairs"][0]["value"] == "1"
    assert vs[-1]["pairs"][0]["value"] == "8"


def test_courtesy_call_block_and_offform_photo():
    recs = {r["name"]: r for r in build_sv_dictionary()["levels"][0]["records"]}
    cc = _items(recs["COURTESY_CALL"])
    for name in ("CC_ENDORSEMENT_OBTAINED", "CC_FOCAL_PERSON_NAME",
                 "CC_HCW_LIST_CAPTURED", "CC_HCW_LIST_COUNT",
                 "CC_PATIENT_LISTING_DATE", "CC_WORKSTATION_ARRANGED"):
        assert name in cc, name
    # binary photo item present (off-form; synced to CSWeb)
    assert cc["VERIFICATION_PHOTO_IMAGE"]["contentType"] == "image"
    assert "CAPTURE_VERIFICATION_PHOTO" in cc
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd deliverables/CSPro/SV && python -m pytest tests/test_generate_dcf.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'generate_dcf'`.

- [ ] **Step 3: Write the generator**

Create `deliverables/CSPro/SV/generate_dcf.py`:

```python
#!/usr/bin/env python3
"""SupervisorApp — Facility Visit Log dictionary (.dcf) generator.

Phase-3 Supervisor App (the DOH-Manual-named app). One case per facility, keyed
by the 9-digit facility code (RRPPMMMFF). Iron rule: never hand-edit the .dcf —
edit this generator and rerun.  Spec:
docs/superpowers/specs/2026-06-23-supervisor-app-phase3-facility-visit-log-design.md

Invoke:  python generate_dcf.py        # writes SupervisorApp.dcf
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import (
    numeric, alpha, select_one, yes_no, record,
    _gps_fields, _photo_block, build_dictionary, write_dcf, apply_translations,
)

# Touchpoint vocabulary (CAPI-Input §3.3.2 l.277). Single-digit fixed-width codes.
TP_TYPES = [
    ("Arrival",                  "1"),
    ("Courtesy call",            "2"),
    ("Endorsement delivery",     "3"),
    ("Workstation arrangement",  "4"),
    ("Focal person assignment",  "5"),
    ("HCW master-list capture",  "6"),
    ("Departure",                "7"),
    ("Other",                    "8"),
]


def build_header_record():
    return record("VISIT_HEADER", "Facility visit header", "H", [
        alpha("FACILITY_NAME",  "Facility name", length=80),
        alpha("FS_OPERATOR_ID", "Field Supervisor operator ID", length=20),
    ])


def build_courtesy_call_record():
    items = [
        yes_no("CC_ENDORSEMENT_OBTAINED", "Facility approval / endorsement obtained?"),
        numeric("CC_HEAD_INTERVIEW_DATE", "Facility-head interview scheduled (YYYYMMDD)",
                length=8, zero_fill=True),
        alpha("CC_FOCAL_PERSON_NAME", "Focal person name", length=80),
        alpha("CC_DISCHARGE_CUTOFF", "Usual discharge / billing cutoff time", length=40),
        yes_no("CC_HCW_LIST_CAPTURED", "Master HCW list captured?"),
        numeric("CC_HCW_LIST_COUNT", "HCW master-list count", length=4),
        yes_no("CC_QR_POSTER_POSTED", "HCW Survey QR poster posted?"),
        numeric("CC_PATIENT_LISTING_DATE", "Patient-listing day scheduled (YYYYMMDD)",
                length=8, zero_fill=True),
        yes_no("CC_WORKSTATION_ARRANGED", "Temporary workstation arranged?"),
    ]
    # Optional HCW-list photo: reuse the proven binary-Image block + the
    # TakeVerificationPhoto helper (references VERIFICATION_PHOTO_IMAGE by name,
    # so use the UNPREFIXED block). Emits the off-form binary image + filename +
    # the on-form CAPTURE_VERIFICATION_PHOTO trigger.
    items += _photo_block("")
    return record("COURTESY_CALL", "Courtesy-call outcomes (once per facility)", "C", items)


def build_touchpoint_roster():
    items = [
        numeric("TP_LINE", "Touchpoint row", length=2),
        select_one("TP_TYPE", "Touchpoint type", TP_TYPES, length=1),
        alpha("TP_TIMESTAMP", "Touchpoint timestamp (YYYYMMDD HHMM)", length=14),
    ]
    items += _gps_fields("TP_")            # TP_GPS_LATITUDE ... TP_GPS_READTIME
    items += [alpha("TP_OUTCOME_NOTE", "Outcome / note", length=120)]
    return record("TOUCHPOINT", "Facility touchpoint log (repeating)", "T",
                  items, max_occurs=30, required=False)


def build_sv_dictionary():
    records = [
        build_header_record(),
        build_courtesy_call_record(),
        build_touchpoint_roster(),
    ]
    return build_dictionary(
        dict_name="SUPERVISORAPP_DICT",
        dict_label="SupervisorApp",
        id_item_name="FACILITY_CODE",
        id_item_label="Facility Code (RRPPMMMFF)",
        id_length=9,
        records=records,
    )


def main():
    out_path = Path(__file__).parent / "SupervisorApp.dcf"
    dictionary = build_sv_dictionary()
    # Safe even when translations/ doesn't exist: apply_translations includes a
    # locale only if its <code>.json file is present, so this is EN-only for v1.
    dictionary = apply_translations(dictionary, Path(__file__).parent / "translations")
    write_dcf(dictionary, out_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd deliverables/CSPro/SV && python -m pytest tests/test_generate_dcf.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Generate the dictionary file**

Run: `cd deliverables/CSPro/SV && python generate_dcf.py`
Expected stdout: `Wrote ...SupervisorApp.dcf` / `Records: 3` / `Items: 21` (±, depending on `_photo_block`/`_gps_fields` counts).

- [ ] **Step 6: Checkpoint (no commit)**

Confirm `git status` shows the new `SV/` files untracked. Leave them in the working tree for Carl. Do NOT commit.

---

## Task 2: Logic generator (`generate_apc.py`)

**Files:**
- Create: `deliverables/CSPro/SV/generate_apc.py`
- Create: `deliverables/CSPro/SV/tests/test_generate_apc.py`
- Produces (on run): `deliverables/CSPro/SV/SupervisorApp.ent.apc`

**Interfaces:**
- Consumes: `deliverables/CSPro/shared/Capture-Helpers.apc` (read + inlined). Dictionary field names from Task 1 (`TP_TYPE`, `TP_TIMESTAMP`, `TP_GPS_*`, `TP_OUTCOME_NOTE`, `TP_LINE`, `CC_HCW_LIST_CAPTURED`, `FACILITY_CODE`, `CAPTURE_VERIFICATION_PHOTO`, `VERIFICATION_PHOTO_FILENAME`).
- Produces: `build_apc() -> str` (full `.ent.apc` text); `_inline_shared(filename) -> str`.

- [ ] **Step 1: Write the failing test**

Create `deliverables/CSPro/SV/tests/test_generate_apc.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generate_apc import build_apc


def test_apc_inlines_helper_into_single_proc_global():
    apc = build_apc()
    # Exactly one PROC GLOBAL (helper inlined, not #included)
    assert apc.count("PROC GLOBAL") == 1
    assert "#include" not in apc
    # The inlined GPS + photo helper functions are present
    assert "function ReadGPSReading" in apc
    assert "function TakeVerificationPhoto" in apc


def test_apc_auto_stamps_and_protects_on_tp_type():
    apc = build_apc()
    assert "PROC TP_TYPE" in apc
    assert "ReadGPSReading(120, 20)" in apc
    assert 'sysdate("YYYYMMDD")' in apc and 'systime("HHMM")' in apc
    # captured-once guard + protect of the stamped fields
    assert "if length(strip(TP_TIMESTAMP)) = 0 then" in apc
    assert "protect(TP_GPS_LATITUDE, true)" in apc
    assert "protect(TP_TIMESTAMP, true)" in apc


def test_apc_line_index_and_other_note_gate_and_photo():
    apc = build_apc()
    assert "PROC TP_LINE" in apc and "TP_LINE = curocc();" in apc
    assert "PROC TP_OUTCOME_NOTE" in apc and "TP_TYPE = 8" in apc and "reenter;" in apc
    assert "PROC CAPTURE_VERIFICATION_PHOTO" in apc and "TakeVerificationPhoto(fn)" in apc
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd deliverables/CSPro/SV && python -m pytest tests/test_generate_apc.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'generate_apc'`.

- [ ] **Step 3: Write the generator**

Create `deliverables/CSPro/SV/generate_apc.py`:

```python
#!/usr/bin/env python3
"""SupervisorApp — CAPI logic (.ent.apc) generator.

Emits SupervisorApp.ent.apc. The shared GPS + photo helpers are INLINED
into the single PROC GLOBAL (CSEntry forbids #include and any code before the
first PROC — verified 2026-06-08; same mechanism as F1 generate_apc._inline_shared).
Iron rule: never hand-edit the .ent.apc — edit this generator and rerun.

Invoke:  python generate_apc.py        # writes SupervisorApp.ent.apc
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED_DIR = HERE.parent / "shared"
OUT = HERE / "SupervisorApp.ent.apc"


def _inline_shared(filename):
    """Return a shared helper module's body with its own 'PROC GLOBAL' header
    stripped, for pasting INSIDE the host's single PROC GLOBAL."""
    text = (SHARED_DIR / filename).read_text(encoding="utf-8")
    body, seen_global = [], False
    for ln in text.splitlines():
        if not seen_global:
            if ln.strip() == "PROC GLOBAL":
                seen_global = True
            continue
        body.append(ln)
    if not seen_global:
        raise RuntimeError(f"{filename}: expected a 'PROC GLOBAL' line to strip")
    return "\n".join(body)


def build_apc():
    return """\
{ ============================================================================
  SupervisorApp — CAPI logic   (AUTOGENERATED by generate_apc.py)
  Do NOT hand-edit: edit generate_apc.py and rerun.
  Phase-3 Supervisor App (Facility Visit Log). Spec:
  docs/superpowers/specs/2026-06-23-supervisor-app-phase3-facility-visit-log-design.md
  ============================================================================ }

PROC GLOBAL

{ Shared GPS + photo helpers inlined here (CSEntry forbids #include and any code
  before the first PROC; inlining into PROC GLOBAL is the only arrangement the
  Designer compiler and the CSEntry loader both accept — verified 2026-06-08). }
""" + _inline_shared("Capture-Helpers.apc") + """

PROC TP_LINE
preproc
  { Occurrence index, auto-set; not entered. }
  TP_LINE = curocc();
  noinput;

PROC TP_TYPE
postproc
  { Auto-stamp GPS + timestamp ONCE per touchpoint, right after the FS picks the
    type, then protect so the row is tamper-evident. TP_TIMESTAMP is the
    captured-once sentinel (it is always set, even when GPS fails on desktop /
    no signal, so the row still carries a time). Desktop has no GPS radio:
    ReadGPSReading returns 0 (getos 10:19 guard) and flows past with no modal. }
  if length(strip(TP_TIMESTAMP)) = 0 then
    if ReadGPSReading(120, 20) then
      TP_GPS_LATITUDE   = maketext("%f", gps(latitude));
      TP_GPS_LONGITUDE  = maketext("%f", gps(longitude));
      TP_GPS_ALTITUDE   = maketext("%f", gps(altitude));
      TP_GPS_ACCURACY   = gps(accuracy);
      TP_GPS_SATELLITES = gps(satellites);
      TP_GPS_READTIME   = maketext("%d", gps(readtime));
    endif;
    TP_TIMESTAMP = maketext("%s %s", sysdate("YYYYMMDD"), systime("HHMM"));
    protect(TP_GPS_LATITUDE, true);
    protect(TP_GPS_LONGITUDE, true);
    protect(TP_GPS_ALTITUDE, true);
    protect(TP_GPS_ACCURACY, true);
    protect(TP_GPS_SATELLITES, true);
    protect(TP_GPS_READTIME, true);
    protect(TP_TIMESTAMP, true);
  endif;

PROC TP_OUTCOME_NOTE
postproc
  { An 'Other' (code 8) touchpoint must carry a note describing what it was. }
  if TP_TYPE = 8 and length(strip(TP_OUTCOME_NOTE)) = 0 then
    errmsg("Please describe the 'Other' touchpoint in the note.");
    reenter;
  endif;

PROC CAPTURE_VERIFICATION_PHOTO
onfocus
  { Optional HCW master-list photo. Reuses the proven binary-Image helper so the
    JPG bytes sync to CSWeb (#713). Only when the FS captured the HCW list. }
  if CC_HCW_LIST_CAPTURED = 1 then
    string fn = maketext("facility-%09d-hcwlist.jpg", FACILITY_CODE);
    if TakeVerificationPhoto(fn) then
      VERIFICATION_PHOTO_FILENAME = fn;
    endif;
  endif;
  CAPTURE_VERIFICATION_PHOTO = notappl;
"""


def main():
    text = build_apc()
    OUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT}  ({len(text.splitlines())} lines)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd deliverables/CSPro/SV && python -m pytest tests/test_generate_apc.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Generate the logic file + run the full suite**

Run: `cd deliverables/CSPro/SV && python generate_apc.py && python -m pytest -q`
Expected: `Wrote ...SupervisorApp.ent.apc` then `6 passed`.

- [ ] **Step 6: Checkpoint (no commit)** — leave files in the working tree for Carl.

---

## Task 3: Register the app in the build + deploy automation

**Files:**
- Modify: `deliverables/CSPro/automation/cspro_compile_driver.py:58` (the `SPECS` dict)
- Modify: `deliverables/CSPro/automation/auto_deploy.py:25` (the `INSTRUMENTS` dict)

**Interfaces:**
- Consumes: the existing `SPECS` / `INSTRUMENTS` registries.
- Produces: a `"SV"` key resolvable by both drivers (`base="SupervisorApp"`, `ent_name="SUPERVISORAPP"`, `has_fmf_gen=False`).

- [ ] **Step 1: Add `SV` to the compile driver's `SPECS`**

In `cspro_compile_driver.py`, the `SPECS` dict currently reads:

```python
SPECS = {
    "F1": {"dir": "F1", "base": "FacilityHeadSurvey", "ent_name": "FACILITYHEADSURVEY", "has_fmf_gen": False},
    "F3": {"dir": "F3", "base": "PatientSurvey",       "ent_name": "PATIENTSURVEY",      "has_fmf_gen": True},
    "F4": {"dir": "F4", "base": "HouseholdSurvey",     "ent_name": "HOUSEHOLDSURVEY",    "has_fmf_gen": True},
```

Add one line after the `F4` entry (SV mirrors F1's hand-maintained-fmf model):

```python
    "SV": {"dir": "SV", "base": "SupervisorApp", "ent_name": "SUPERVISORAPP", "has_fmf_gen": False},
```

- [ ] **Step 2: Add `SV` to the deploy driver's `INSTRUMENTS`**

In `auto_deploy.py`, the `INSTRUMENTS` dict currently reads:

```python
INSTRUMENTS = {
    "F1": "FacilityHeadSurvey",
    "F3": "PatientSurvey",
    "F4": "HouseholdSurvey",
}
```

Add the SV mapping (the value is the CSWeb **Package name** the driver matches):

```python
INSTRUMENTS = {
    "F1": "FacilityHeadSurvey",
    "F3": "PatientSurvey",
    "F4": "HouseholdSurvey",
    "SV": "SupervisorApp",
}
```

- [ ] **Step 3: Verify the registries resolve**

Run: `cd deliverables/CSPro/automation && python auto_deploy.py --check`
Expected: it lists/checks `SV` among the instruments without a `KeyError` (it will report "no dialog with Package name 'SupervisorApp'" — expected, nothing is published yet).

- [ ] **Step 4: Checkpoint (no commit)** — leave the two edits in the working tree.

---

## Task 4: Bootstrap the app shell in CSPro Designer (one-time)

**Files (Designer-created, then generator-owned where noted):**
- Create via Designer: `deliverables/CSPro/SV/SupervisorApp.ent`, `.fmf`, `.ent.qsf`, `.ent.mgf`, `.pff`
- Overwrite with the generated logic: `SupervisorApp.ent.apc` (Task 2 output)

**Why Designer here:** a brand-new app needs its `.ent`/`.fmf`/`.qsf`/`.mgf` created once. Designer's "new entry application from a dictionary" auto-lays-out a default form per record and writes valid shells specific to this dict (the compile driver only auto-templates a `.qsf`/`.mgf` from F1 boilerplate, which would carry F1's fields — wrong here). After this, generators own `.dcf`/`.ent.apc`; the `.fmf` is hand-maintained like F1.

- [ ] **Step 1: Open the generated dictionary in Designer**

Run: `& "C:\Program Files\CSPro 8.0\CSPro.exe" "C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro\SV\SupervisorApp.dcf"`
Expected: CSPro Designer opens the dictionary with `VISIT_HEADER`, `COURTESY_CALL`, `TOUCHPOINT` records visible.

- [ ] **Step 2: Create the Data Entry Application**

In Designer: **File → New → Data Entry Application**, name `SupervisorApp`, save into `deliverables/CSPro/SV/`, and select the existing `SupervisorApp.dcf` as the input dictionary. Accept "generate forms" so Designer lays out a default form per record. This writes `SupervisorApp.ent`, `.fmf`, `.ent.qsf`, `.ent.mgf`, and `.pff`.

- [ ] **Step 3: Arrange the forms + exclude the binary image**

- Confirm three forms: header, courtesy-call, touchpoint roster (the `TOUCHPOINT` record renders as a roster grid).
- **Remove `VERIFICATION_PHOTO_IMAGE` from any form** (binary Image items cannot sit on a form — drag it off / delete the field box; keep `CAPTURE_VERIFICATION_PHOTO` and `VERIFICATION_PHOTO_FILENAME` on the courtesy-call form).
- Ensure `TP_GPS_*` and `TP_TIMESTAMP` are on the touchpoint form (they display read-only after capture) and `CAPTURE_VERIFICATION_PHOTO` is on the courtesy-call form.
- Save (Ctrl+S).

- [ ] **Step 4: Point the app at the generated logic**

The generated `SupervisorApp.ent.apc` (Task 2) is the source of truth for logic. In Designer's logic view, confirm the app's main logic file is `SupervisorApp.ent.apc`; if Designer created an empty one, close Designer and re-run `python generate_apc.py` to overwrite it, then reopen. (The `.ent` references `SupervisorApp.ent.apc` by path — confirm in the `.ent` JSON `"code"` block.)

- [ ] **Step 5: Confirm the CSWeb sync property on the `.ent`**

In Designer: **Options → Synchronization** → set Simple Synchronization server to `https://csweb.asiansocial.org` (matches the instruments; the compile driver also bakes this in). Enable **partial save** (Options → Partial Save → operator-enabled) so a multi-day visit log can be resumed. Save.

- [ ] **Step 6: Checkpoint (no commit)** — leave the new shell files in the working tree.

---

## Task 5: Compile gate (Designer lenient compile)

**Files:** none changed — this runs the build/bind/compile pipeline.

- [ ] **Step 1: Build + compile via the driver**

Run: `cd deliverables/CSPro/automation && python cspro_compile_driver.py SV --build --save`
What it does (per its header): regenerate dcf/apc (`has_fmf_gen=False` → no fmf regen) → bind the `.ent` → launch CSPro on `SupervisorApp.ent` → Ctrl+L → screenshot.

- [ ] **Step 2: Read the compile result**

Read `deliverables/CSPro/automation/shots/SV_compile.png` (vision).
Expected: "Compile Successful at HH:MM:SS" in the Compiler Output pane; the full form tree (header / courtesy-call / touchpoint roster) rendered.

- [ ] **Step 3: Fix any compile errors at the generator**

If the Compiler Output shows an `ERROR(field, line): ...`, fix it in `generate_dcf.py` or `generate_apc.py` (never hand-edit the `.dcf`/`.apc`), rerun the generator + Step 1. Common: a field-name typo between the apc and the dcf, or an `alpha <> numeric` comparison.

- [ ] **Step 4: Checkpoint (no commit).**

---

## Task 6: Strict Publish gate (the real compiler)

**Files:** none — this is the strict packager pass.

- [ ] **Step 1: Publish in Designer**

With `SupervisorApp.ent` open in Designer (from Task 5): **File → Publish and Deploy** (Alt+F, then the Publish-and-Deploy item). If a "save changes?" modal appears, click **Yes**.

- [ ] **Step 2: Confirm the strict compile passed**

Expected: the **"CSPro Deploy Application"** dialog opens (Package name = `SupervisorApp`).
If instead a **"Compile Failed!"** modal appears: dismiss it, screenshot the Compiler Output pane, read the real `ERROR(...)`, fix it in the generator, rerun Task 5, and retry. (The Publish parser is stricter than Ctrl+L — e.g. it rejects constructs the lenient compile accepted.)

- [ ] **Step 3: Checkpoint (no commit).**

---

## Task 7: Deploy to CSWeb

**Files:** none — CSWeb-side registration + deploy.

- [ ] **Step 1: Register the dictionary on CSWeb (one-time)**

In the CSWeb admin (`csweb.asiansocial.org`), add the `SupervisorApp` application/dictionary so FS accounts can sync it (mirror how F1/F3/F4 dictionaries are registered). Confirm the FS role/account has sync permission for it.

- [ ] **Step 2: Deploy from the open dialog**

With the "CSPro Deploy Application" dialog open (Task 6) and Package name `SupervisorApp`:
Run: `cd deliverables/CSPro/automation && python auto_deploy.py SV --deploy`
What it does: locks onto the dialog whose Package name == `SupervisorApp` (refuses any mismatch), verifies the CSWeb URL == `csweb.asiansocial.org`, clicks Deploy, waits for "Application Deployed Successfully", then dismisses the popup + re-minimizes the dialog.

- [ ] **Step 2 note (v1 has no PSGC externals):** SV's `.ent` declares no PSGC external dictionaries (typed `FACILITY_CODE`), so — unlike F1/F3/F4 — there are **no 8 PSGC files to add** in the deploy dialog. If `auto_deploy.py` expects them, run the deploy directly from the dialog's Deploy button instead; capture the result screenshot either way.

- [ ] **Step 3: Confirm deploy success**

Read `deliverables/CSPro/automation/shots/deploy/auto_SV_deploy_1.png` (vision).
Expected: "Application Deployed Successfully" to `csweb.asiansocial.org`.

- [ ] **Step 4: Checkpoint (no commit).**

---

## Task 8: itel device verification

**Files:** none — on-device acceptance. adb at `C:\Users\analy\AppData\Local\Android\Sdk\platform-tools\adb.exe` (itel `itel_P10001L`, 800x1280).

- [ ] **Step 1: Install under an FS account**

On the itel: CSEntry → ⋮ → **Add Application → From server** → sign in with an **FS account** → install **SupervisorApp**. (If it doesn't appear, confirm Task 7 Step 1 granted that account sync access.)

- [ ] **Step 2: Log a facility visit**

Add a new case → enter a 9-digit `FACILITY_CODE` (use a real facility code, e.g. derived from test key `138010002015` → facility `138010002`) + facility name + FS id. On the touchpoint roster, add a row and pick **Arrival**.
Expected: `TP_TIMESTAMP` auto-fills (YYYYMMDD HHMM), the `TP_GPS_*` fields auto-fill, and all are **read-only (protected)**. Add Courtesy call / HCW-list / Departure rows.

- [ ] **Step 3: Capture the HCW-list photo**

On the courtesy-call form set `CC_HCW_LIST_CAPTURED = Yes`, trigger `CAPTURE_VERIFICATION_PHOTO` → take a photo → it displays for confirmation.

- [ ] **Step 4: Sync to CSWeb + confirm server-side**

Sync the case. In the CSWeb Data Viewer for `SupervisorApp`, confirm: the case lands, the touchpoint roster rows carry GPS + timestamps, and the HCW photo thumbnail is downloadable (binary Image synced).
Capture an adb screenshot of the on-device roster as evidence: `adb exec-out screencap -p > shots/SV_device_roster.png`.

- [ ] **Step 5: Record the result**

If all pass → v1 is device-confirmed. If anything fails (GPS doesn't stamp, photo doesn't sync, field editable when it should be protected), root-cause at the generator, rerun Tasks 5–7, retest. Do NOT fan out / announce until device-confirmed.

- [ ] **Step 6: Checkpoint (no commit).**

---

## Task 9: FS SOP + generator README

**Files:**
- Create: `deliverables/CSPro/SV/README.md`
- Create: `docs/Supervisor-App-FS-SOP.md` (or the project's runbook location)

- [ ] **Step 1: Write the generator README**

Create `deliverables/CSPro/SV/README.md` documenting: what the app is (the DOH-Manual Facility Visit Log), the iron rule (edit `generate_dcf.py`/`generate_apc.py`, never the `.dcf`/`.apc`; `.fmf` is hand-maintained like F1), the build commands (`generate_dcf.py` → `generate_apc.py` → `cspro_compile_driver.py SV --build --save` → Publish → `auto_deploy.py SV --deploy`), and the data model (one case/facility; header + courtesy-call + touchpoint roster; GPS+timestamp auto-stamped+protected).

- [ ] **Step 2: Write the FS SOP**

Create `docs/Supervisor-App-FS-SOP.md`: install under your own FS account (remove + re-add from CSWeb to refresh); at each facility, open the case for that facility code and add a touchpoint row per event (Arrival on arrival, … Departure on leaving) — GPS + time stamp automatically; fill the courtesy-call block on the first visit (incl. HCW-list count + optional photo); sync nightly.

- [ ] **Step 3: Checkpoint (no commit)** — leave docs in the working tree for Carl.

---

## Self-Review (done at plan-writing time)

**Spec coverage:** Goal/touchpoint log → Tasks 1–2,8; courtesy-call block → Task 1; auto GPS+timestamp+protect → Task 2,8 (D4); one-case-per-facility key → Task 1 (D3); sync to CSWeb → Tasks 4–7 (D5); facility-log-only → scoped in Task 1 (D6); reconciliation = fast-follow (D7, out of v1) → noted, not a task; login = FS account (D8) → Task 8 Step 1; generator-built / iron rule (D2) → Tasks 1–2 + Global Constraints; HCW master-list capture → Task 1 + Task 8 Step 3; naming correction → spec-level (memory updated), not a build task. All spec sections map to a task or an explicit out-of-v1 note.

**Placeholder scan:** generator code is complete (no TBDs); GUI/device tasks give exact commands + expected output. The two Designer/CSWeb-admin steps (Task 4 new-entry-app; Task 7 dict registration) are inherently interactive GUI actions stated as precise click-paths — not placeholders.

**Type consistency:** field names match across Tasks 1↔2↔8 (`TP_TYPE`, `TP_TIMESTAMP`, `TP_GPS_LATITUDE/LONGITUDE/ALTITUDE/ACCURACY/SATELLITES/READTIME`, `TP_OUTCOME_NOTE`, `TP_LINE`, `CC_HCW_LIST_CAPTURED`, `FACILITY_CODE`, `CAPTURE_VERIFICATION_PHOTO`, `VERIFICATION_PHOTO_FILENAME`); record types `H`/`C`/`T`; `TP_TYPE` code `8` = Other used consistently in the dcf value set and the apc note gate.
