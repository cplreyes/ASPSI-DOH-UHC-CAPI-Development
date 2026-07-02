#!/usr/bin/env python3
"""SupervisorApp — Facility Visit Log dictionary (.dcf) generator.

Phase-3 Supervisor App (the DOH-Manual-named app). One case per facility, keyed
by the 9-digit facility code (RRPPMMMFF). Iron rule: never hand-edit the .dcf —
edit this generator and rerun.  Spec:
docs/superpowers/specs/2026-06-23-supervisor-app-phase3-facility-visit-log-design.md

Invoke:  python generate_dcf.py        # writes SupervisorVisitLog.dcf
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
