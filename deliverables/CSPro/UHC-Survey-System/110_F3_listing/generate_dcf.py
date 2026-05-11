"""
generate_dcf.py — F3 Patient Listing CSPro Data Dictionary generator.

Emits PatientListing.dcf in CSPro 8.0 JSON dictionary format. The listing
app is run by enumerators *before* an F3 patient survey session begins;
each output case represents one **listing session** (one facility-day) and
the roster of patients enumerated during it. F3 / F4 entry apps then
loadcase() the listing dictionary at interview time to pick patients
tagged LISTING_TAG=1 / LISTING_TAG=2 respectively.

Authority sources (in priority order):
  1. raw/Project-Deliverable-1_Apr20-submitted/Annex F3b_Patient Listing
     Protocol_UHC Year 2.pdf                                       (printed)
  2. raw/2026-05-06-survey-manual-bundle/2026-05-06_Survey-Manual-Working-
     File-Kidd.docx                                §3.4.1.7 + §3a (pending)
  3. wiki/sources/Source - Survey Manual 2026-05-06 - Section 3a.md
     (records the §3a gap + Candidate A — Distance-gated auto-tag rule
      chosen as the working default; see wiki for rationale)
  4. raw/2026-05-06-survey-manual-bundle/2026-05-06_Appendix-F_Patient-
     Listing-Form.docx                            (paper-side reference)

Rebuild deltas vs the F-series instruments:
  - Session-scoped ID block built via build_listing_id_block() (added
    in commit 8 of this build). Width 16: RR+PP+MMM+FF+YYYYMMDD+SSS.
    Distinct from the F1/F3/F4 12-digit case-ID — the listing session
    is *not* an F-series questionnaire and does not collide with the
    1-699 / 700-899 / 900-999 CASE_SEQ partitions.
  - LISTING_TAG = 1 / 2 / 3 / 9 with 9 reserved for NA (project-wide
    NA-at-highest-value convention; see wiki feedback memory).
  - TRANSPORT_MODE multi-response per the 12-mode F3 Q70/Q73 enumeration.

Run:
    python generate_dcf.py        # writes PatientListing.dcf next to this file

This file is a scaffold stub for commit 1. Subsequent commits land
REC_LISTING_CONTROL (commit 2), REC_RANDOM_INTERVAL_LOG (commit 3),
REC_PATIENT_ROSTER (commit 4), REC_LISTING_FACILITY_CAPTURE +
REC_LISTING_PHOTO (commit 5). Until those land, build_dictionary()
emits an opening-only DCF with the root record so CSPro Designer can
open the file at every intermediate state for code review.
"""

import json
import sys
from pathlib import Path

# Import shared helpers
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from cspro_helpers import (
    record, build_dictionary as build_dictionary_from_helpers,
)


# ============================================================
# RECORD BUILDERS — populated commit-by-commit
# ============================================================

def build_listing_control():
    """REC_LISTING_CONTROL — landed in commit 2. Stub for commit 1."""
    return record("REC_LISTING_CONTROL", "Listing Session Control", "A", [])


def build_random_interval_log():
    """REC_RANDOM_INTERVAL_LOG — landed in commit 3. Stub for commit 1."""
    return record("REC_RANDOM_INTERVAL_LOG", "Random-Interval Cadence Log",
                  "I", [], max_occurs=999, required=False)


def build_patient_roster():
    """REC_PATIENT_ROSTER — landed in commit 4. Stub for commit 1."""
    return record("REC_PATIENT_ROSTER", "Patient Listing Roster", "P",
                  [], max_occurs=999, required=False)


def build_listing_facility_capture():
    """REC_LISTING_FACILITY_CAPTURE — landed in commit 5. Stub for commit 1."""
    return record("REC_LISTING_FACILITY_CAPTURE",
                  "Facility GPS Capture (listing session)", "Z", [])


def build_listing_photo():
    """REC_LISTING_PHOTO — landed in commit 5. Stub for commit 1."""
    return record("REC_LISTING_PHOTO", "Listing Session Verification Photo",
                  "X", [])


# ============================================================
# ID BLOCK — listing session, distinct from F-series 12-digit case-ID
# ============================================================

def build_listing_id_block_stub():
    """Single-item placeholder ID block until build_listing_id_block() lands
    in shared/cspro_helpers.py (commit 8). For commit 1 we use a temporary
    16-digit composite ID item so the DCF opens in Designer without errors.
    The real decomposed 6-item block replaces this in commit 8."""
    return [{
        "name":        "LISTING_SESSION_ID",
        "labels":      [{"text": "Listing Session Composite ID (stub)"}],
        "contentType": "numeric",
        "start":       2,
        "length":      16,
        "zeroFill":    True,
        "decimal":     0,
        "decimalChar": False,
    }]


# ============================================================
# ASSEMBLE
# ============================================================

def build_dictionary():
    """Assemble the PatientListing dictionary.

    Commit 1 emits an opening-only structure: a root record (recordType "1"),
    plus empty stubs for the records that subsequent commits populate.
    The stubs let CSPro Designer open the .dcf at every intermediate state,
    which makes the commit-by-commit diff reviewable.
    """
    records = [
        # Root record (recordType "1") — required by CSPro hierarchy
        record("PATIENTLISTING_REC", "PatientListing Record", "1", []),
        build_listing_control(),
        build_random_interval_log(),
        build_patient_roster(),
        build_listing_facility_capture(),
        build_listing_photo(),
    ]

    return build_dictionary_from_helpers(
        dict_name="PATIENTLISTING_DICT",
        dict_label="PatientListing",
        id_items=build_listing_id_block_stub(),
        records=records,
    )


def main():
    out_path = Path(__file__).parent / "PatientListing.dcf"
    dictionary = build_dictionary()
    out_path.write_text(json.dumps(dictionary, indent=2), encoding="utf-8")

    record_count = len(dictionary["levels"][0]["records"])
    item_count = sum(len(r["items"]) for r in dictionary["levels"][0]["records"])
    print(f"Wrote {out_path}")
    print(f"  Records: {record_count}")
    print(f"  Items:   {item_count}")


if __name__ == "__main__":
    main()
