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
    numeric, alpha, record, build_dictionary as build_dictionary_from_helpers,
)


# ============================================================
# RECORD BUILDERS — populated commit-by-commit
# ============================================================

def build_listing_control():
    """REC_LISTING_CONTROL — listing-session header items.

    One occurrence per listing session (= one facility-day). Captures the
    enumerator who ran the session, the supervisor on-site, the
    FACILITY_TARGET (configured per-facility by STL via the user_roster
    Excel and exposed at runtime through loadsetting()), and the
    BACKUP_TARGET (= ceil(0.5 * FACILITY_TARGET), minimum 1; computed in
    preproc and stored here for audit). The session also captures the
    intended cadence min/max for the random-interval engine — see commit 3
    for the per-event log record.

    Field-width discipline (project-wide):
      - DATE items use the standard YYYYMMDD width-8 numeric.
      - TIME items use HHMMSS width-6 numeric.
      - SESSION_STATUS NA code = 9 (the highest value at width 1).
    """
    SESSION_STATUS_OPTIONS = [
        ("In progress",                    "1"),
        ("Closed — target met",            "2"),
        ("Closed — facility-day ended",    "3"),
        ("Aborted — operator",             "4"),
        ("Aborted — error",                "5"),
        ("Not applicable",                 "9"),
    ]

    items = [
        # --- Identity of the listing-session run ----------------------
        # SURVEY_CODE is "F3L" (listing) — distinct from "F3" so paradata
        # collators can route listing sessions separately from F3 cases.
        alpha("SURVEY_CODE",            "Survey Instrument Code (F3L)",       length=3),
        numeric("DATE_SESSION",         "Date of Listing Session (YYYYMMDD)", length=8),
        numeric("TIME_SESSION_START",   "Session Start Time (HHMMSS)",        length=6),
        numeric("TIME_SESSION_END",     "Session End Time (HHMMSS)",          length=6),

        # --- Staff IDs (login-issued by 101_login menu app) -----------
        # Width-4 zero-fill mirrors the FIELD_CONTROL.INTERVIEWER_ID width
        # used in F1/F3/F4 (see shared.cspro_helpers._case_control_items).
        numeric("ENUMERATOR_ID",        "Enumerator ID",                       length=4,
                zero_fill=True),
        numeric("SUPERVISOR_ID",        "Survey Team Leader / Supervisor ID",  length=4,
                zero_fill=True),

        # --- Targets (set via loadsetting() at session start) ---------
        # FACILITY_TARGET upper-bounds at 999 — accommodates large-volume
        # facility-days (tertiary OPD) without ballooning width.
        numeric("FACILITY_TARGET",      "Patients to list at this facility today",
                length=3),
        # BACKUP_TARGET computed in preproc as ceil(0.5 * FACILITY_TARGET),
        # minimum 1. Stored here for audit / replacement-protocol bookkeeping.
        numeric("BACKUP_TARGET",        "Backup-target sample size",           length=3),

        # --- Random-interval cadence configuration --------------------
        # Min/max are in MINUTES. Default values are set per-facility-tier
        # in the menu app via loadsetting(); they appear here so the
        # audit trail records *what cadence was configured for this session*
        # even if the operator later overrides at runtime.
        numeric("CADENCE_MIN_MIN",      "Random-interval minimum (minutes)",   length=3),
        numeric("CADENCE_MAX_MIN",      "Random-interval maximum (minutes)",   length=3),

        # --- Running counters (maintained by APC during the session) --
        numeric("LISTED_COUNT",         "Patients listed so far",              length=3),
        numeric("REFUSED_COUNT",        "Patients who refused listing",        length=3),
        numeric("EXCLUDED_COUNT",       "Patients excluded (ineligible)",      length=3),

        # --- Session disposition --------------------------------------
        numeric("SESSION_STATUS",       "Session Disposition",                 length=1,
                value_set_options=SESSION_STATUS_OPTIONS),
        alpha("SESSION_NOTES",          "Free-text notes from the enumerator", length=240),
    ]
    return record("REC_LISTING_CONTROL", "Listing Session Control", "A", items)


def build_random_interval_log():
    """REC_RANDOM_INTERVAL_LOG — one occurrence per random-interval draw.

    Used to audit the cadence engine: every time the listing app draws a
    new random wait interval between listing events, an occurrence is
    appended here. The log lets a desk reviewer verify that the engine
    actually used random intervals (and within the configured bounds), not
    convenient round numbers an enumerator could fake.

    Occurrence semantics:
      - Each occurrence covers ONE wait-and-list cycle.
      - INTERVAL_SEC is the value drawn (random in [CADENCE_MIN_MIN*60,
        CADENCE_MAX_MIN*60], inclusive).
      - The OUTCOME captures what happened at the END of this cycle.
      - SEED_USED records the pseudorandom seed value rolled into this
        draw (session timestamp + ENUMERATOR_ID + cycle index, hashed).
        Audit-only — no security claim; tamper resistance comes from
        the sync to CSWeb shortly after each draw.

    Max occurrences: 999. A facility-day with >999 draws is operationally
    implausible (the median target is ~30, with backup-target padding).
    """
    RI_OUTCOME_OPTIONS = [
        ("Listed",                          "1"),
        ("Refused",                         "2"),
        ("Excluded (ineligible)",           "3"),
        ("Timeout — no patient observed",   "4"),
    ]

    items = [
        # Sequence within this listing session — 1-based, set by APC.
        numeric("RI_CYCLE_NO",       "Cycle number within this session",       length=3,
                zero_fill=True),
        # When the engine *started* waiting (after the previous listing).
        numeric("RI_WAIT_START",     "Wait-start time (HHMMSS)",               length=6),
        # The interval drawn from [min, max] for this cycle, in SECONDS.
        # Width 5 -> max 99999 sec = 27.7 hours, comfortably above any
        # plausible cadence-max for a facility-day session.
        numeric("RI_INTERVAL_SEC",   "Random interval drawn (seconds)",        length=5),
        # When the engine *signaled* the enumerator to list the next patient.
        numeric("RI_TRIGGER_TIME",   "Trigger time = wait-start + interval (HHMMSS)",
                length=6),
        # Outcome at the end of the cycle.
        numeric("RI_OUTCOME",        "Outcome of this listing cycle",          length=1,
                value_set_options=RI_OUTCOME_OPTIONS),
        # Audit hook — links this log occurrence to the roster occurrence
        # it produced (if any). Set to 0 if no patient was listed
        # (RI_OUTCOME in {2,3,4}).
        numeric("RI_ROSTER_OCC",     "Patient roster occurrence produced (0 if none)",
                length=3, zero_fill=True),
        # Pseudorandom seed snapshot for desk audit. Width 10 holds a
        # 32-bit unsigned mod 10^10.
        numeric("RI_SEED_USED",      "Seed used for this draw",                length=10,
                zero_fill=True),
    ]
    return record("REC_RANDOM_INTERVAL_LOG", "Random-Interval Cadence Log",
                  "I", items, max_occurs=999, required=False)


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
