#!/usr/bin/env python3
r"""#744 — inject the BREAKOFF "interview status" control into F1's hand-maintained
FacilityHeadSurvey.fmf.

WHY THIS EXISTS (UAT R5 #744)
-----------------------------
F3/F4 build their .fmf from generate_fmf.py, where the case-start FIELD_CONTROL form
carries PATIENT_TYPE + BREAKOFF (the break-off control). F1's .fmf is hand-maintained
(has_fmf_gen=False) — no generator places fields — so BREAKOFF must be spliced in by a
post-processor. This is IRON-RULE compliant: a re-runnable, idempotent script, NOT a
manual Designer hand-edit.

PLACEMENT
---------
BREAKOFF is added as the LAST field of FORM001 ("Health Facility and Geographic
Identification") — the FIRST interactive form after the case key. The enumerator can tap
back to it from the case tree at any time; selecting a non-Continue option skips straight
to the closing Result-of-Final-Visit (PROC BREAKOFF in generate_apc.py). It rides the geo
form (no new form, so no Form= ordinal renumbering — the safe choice in a hand .fmf). The
geo block ends at y=167 (Barangay), so BREAKOFF sits at y=177, inside the form's 300-tall
canvas (no Size change needed).

The dcf item BREAKOFF is emitted by generate_dcf.py (build_field_control); CASE_DISPOSITION
is OFF-FORM (logic-only) and is intentionally NOT added here. optimize_capture_types.py runs
after this on every build and will (re)set BREAKOFF's DataCaptureType from the dcf meta — the
RadioButton here is just a sensible default that survives if optimize is skipped.

IDEMPOTENT: re-running is a no-op once BREAKOFF is present.
Run once:  python inject_breakoff.py
"""
from pathlib import Path

FMF = Path(__file__).parent / "FacilityHeadSurvey.fmf"

# --- the FORM001 visual-layout item line (form member list) ---
FORM_ITEM_ANCHOR = "Item=BARANGAY\r\n  \r\n[EndForm]"
FORM_ITEM_REPLACE = "Item=BARANGAY\r\nItem=BREAKOFF\r\n  \r\n[EndForm]"

# --- the [Field]+[Text] block, spliced before the geo [Group]'s [EndGroup] ---
GROUP_ANCHOR = "Text=Barangay\r\n \r\n[EndGroup]"
BREAKOFF_BLOCK = (
    "[Field]\r\n"
    "Name=BREAKOFF\r\n"
    "Position=177,177,360,197\r\n"
    "Item=BREAKOFF,FACILITYHEADSURVEY_DICT\r\n"
    "DataCaptureType=RadioButton\r\n"
    "Form=2\r\n"
    "  \r\n"
    "[Text]\r\n"
    "Position=50,180,170,196\r\n"
    "Text=Interview status\r\n"
    " \r\n"
)
GROUP_REPLACE = "Text=Barangay\r\n \r\n" + BREAKOFF_BLOCK + "[EndGroup]"


def main():
    # read BYTES + decode (NOT read_text — text mode translates \r\n -> \n and would
    # break the CRLF anchors below). utf-8-sig strips the BOM during decode.
    raw = FMF.read_bytes().decode("utf-8-sig")
    if "Name=BREAKOFF" in raw or "Item=BREAKOFF" in raw:
        print("BREAKOFF already present in FacilityHeadSurvey.fmf — no-op.")
        return

    if raw.count(FORM_ITEM_ANCHOR) != 1:
        raise SystemExit(f"FORM001 item anchor matched {raw.count(FORM_ITEM_ANCHOR)}x (expected 1) — aborting.")
    if raw.count(GROUP_ANCHOR) != 1:
        raise SystemExit(f"Geo-group anchor matched {raw.count(GROUP_ANCHOR)}x (expected 1) — aborting.")

    raw = raw.replace(FORM_ITEM_ANCHOR, FORM_ITEM_REPLACE, 1)
    raw = raw.replace(GROUP_ANCHOR, GROUP_REPLACE, 1)

    # re-prepend BOM; CRLF already embedded in the strings (write bytes to avoid newline xlate)
    FMF.write_bytes("﻿".encode("utf-8") + raw.encode("utf-8"))
    print("Injected BREAKOFF into FORM001 (geo form) of FacilityHeadSurvey.fmf.")


if __name__ == "__main__":
    main()
