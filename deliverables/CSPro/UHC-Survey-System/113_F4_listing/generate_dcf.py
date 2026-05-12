"""
generate_dcf.py — F4 Household Listing CSPro Data Dictionary generator.

Emits F4Listing.dcf in CSPro 8.0 JSON dictionary format. The F4 listing
app is run by a barangay-listing crew *before* F4 household fieldwork
begins; each output case represents one **listing session** (one
barangay-day visit) and the roster of households enumerated during it.
F4 entry apps then loadcase() the listing dictionary at interview time
to pick households tagged F4_STATUS=0 (pending) for the home-visit
survey.

This is a sibling of 110_F3_listing — same session-scoped 20-digit ID
block (RR+PP+MMM+FF+YYYYMMDD+SSS), same one-case-per-session model,
same external-dictionary handshake. Differences:

  - Frame is barangay households (not facility patients). FACILITY_NO
    represents the assigned facility-tier for the barangay (the F4
    sampling frame anchors households to facility catchments).
  - No random-interval cadence engine — the listing crew walks a
    predefined frame (captain's list or door-to-door) rather than
    sampling on a clock.
  - No auto-tag — every listed household is F4-eligible by definition.
    The "tag" implicit in the F-series listing is replaced by a status
    item (F4_STATUS pending->in-progress->completed/refused) updated
    by the F4 entry app.
  - Frame source captured as LISTING_SOURCE (1=captain-supplied,
    2=fresh door-to-door per Carl's Q1 hybrid decision 2026-05-12).
  - 10 replacement reserves per frame (Q2 decision).
  - GPS-only capture (Q6 — no verification photo).
  - Phone optional, alpha-11 (Q5 decision).

Authority sources (in priority order):
  1. raw/2026-05-06-survey-manual-bundle/2026-05-06_Survey-Manual-Working-
     File-Kidd.docx                  Protocol V2 line 1199-1201 {.mark}
                                     (fresh-vs-existing listing question
                                     resolved here as Carl's hybrid model)
  2. wiki/concepts/F4 Listing - Hybrid Frame Model.md
                                     (build-time resolution of the {.mark})
  3. raw/Project-Deliverable-1_Apr20-submitted/Annex F4_Household Survey.pdf
                                     (paper-side reference)

Rebuild deltas vs the F-series instruments:
  - Session-scoped ID block via build_listing_id_block() — width 20,
    RR+PP+MMM+FF+YYYYMMDD+SSS. Identical shape to 110_F3_listing per
    Carl's Q3 decision (uniqueness preserved at case-key level via
    per-session SSS increment; sync path encodes BARANGAY_CODE as a
    separate segment derived from REC_LISTING_CONTROL.BARANGAY_CODE).
  - F4_STATUS = 0/1/2/3/4/9 with 9 reserved for NA.
  - LISTING_SOURCE = 1/2 — captain-supplied vs fresh door-to-door.

Run:
    python generate_dcf.py        # writes F4Listing.dcf next to this file
"""

import json
import sys
from pathlib import Path

# Import shared helpers
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from cspro_helpers import (
    numeric, alpha, record, build_dictionary as build_dictionary_from_helpers,
    _gps_fields, build_listing_id_block,
)


# ============================================================
# RECORD BUILDERS — populated commit-by-commit
# ============================================================

def build_listing_control():
    """REC_LISTING_CONTROL — listing-session header items.

    One occurrence per listing session (= one barangay-day visit).
    Captures the enumerator who ran the session, the supervisor on-site,
    the FRAME_TARGET (configured per-barangay by STL via the user_roster
    Excel and exposed at runtime through loadsetting()), and the
    LISTING_SOURCE (1 = captain-supplied list primary path, 2 = fresh
    door-to-door fallback per Carl's Q1 hybrid decision).

    BARANGAY_CODE is captured as a regular data item (NOT in the session
    ID block — Carl's Q3 decision keeps the 20-digit listing ID shape
    identical to 110_F3_listing). The 10-digit PSGC barangay code is
    used by the F4 sync push to encode the barangay path segment.

    Field-width discipline (project-wide):
      - DATE items: YYYYMMDD width-8 numeric.
      - TIME items: HHMMSS width-6 numeric.
      - SESSION_STATUS NA code = 9 (highest value at width 1).
      - LISTING_SOURCE NA code = 9 (highest value at width 1).
    """
    SESSION_STATUS_OPTIONS = [
        ("In progress",                       "1"),
        ("Closed — frame complete",           "2"),
        ("Closed — barangay-day ended",       "3"),
        ("Aborted — operator",                "4"),
        ("Aborted — error",                   "5"),
        ("Not applicable",                    "9"),
    ]

    LISTING_SOURCE_OPTIONS = [
        ("Captain-supplied list (primary path)",                 "1"),
        ("Fresh door-to-door enumeration (captain list missing)", "2"),
        ("Not applicable",                                       "9"),
    ]

    items = [
        # --- Identity of the listing-session run ----------------------
        # SURVEY_CODE is "F4L" (listing) — distinct from "F4" so paradata
        # collators can route F4 listing sessions separately from F4 cases.
        alpha("SURVEY_CODE",            "Survey Instrument Code (F4L)",       length=3),
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

        # --- Barangay scope (captured as data item per Q3 decision) ---
        # 10-digit PSGC barangay code — NOT in the session ID block.
        # The F4 sync push uses this value to encode the barangay path
        # segment (see SYNC.md). PSGC value set is populated at runtime
        # via setvalueset() once the operator confirms the LGU prefix.
        numeric("BARANGAY_CODE",        "Barangay (10-digit PSGC)",            length=10,
                zero_fill=True,
                value_set_options=[("(set at runtime)", "0" * 10)]),
        alpha("BARANGAY_NAME",          "Barangay Name (for operator confirmation)",
              length=100),

        # --- Frame configuration --------------------------------------
        numeric("LISTING_SOURCE",       "Source of household frame",           length=1,
                value_set_options=LISTING_SOURCE_OPTIONS),
        # FRAME_TARGET = number of households the protocol expects this
        # barangay to contribute (per F4 sampling matrix). Width 3 ->
        # max 999, ample for any realistic barangay-day frame.
        numeric("FRAME_TARGET",         "Households to list in this barangay today",
                length=3),
        # REPLACEMENT_RESERVES = additional rows beyond FRAME_TARGET held
        # against refusals / non-contacts. Set to 10 per Carl's Q2 decision
        # (matches my design recommendation).
        numeric("REPLACEMENT_RESERVES", "Replacement reserves (default 10)",   length=3),

        # --- Running counters (maintained by APC during the session) --
        numeric("LISTED_COUNT",         "Households listed so far",            length=3),
        numeric("REFUSED_COUNT",        "Households who refused listing",      length=3),
        numeric("EXCLUDED_COUNT",       "Households excluded (ineligible)",    length=3),

        # --- Session disposition --------------------------------------
        numeric("SESSION_STATUS",       "Session Disposition",                 length=1,
                value_set_options=SESSION_STATUS_OPTIONS),
        alpha("FRAME_NOTES",            "Free-text notes from the enumerator (frame source, deviations, captain status)",
              length=240),
    ]
    return record("REC_LISTING_CONTROL", "Listing Session Control", "A", items)


def build_household_roster():
    """REC_LISTING_BRGY_FRAME — one occurrence per listed household.

    This is the record the F4 entry app consumes at interview time via
    loadcase() on the external F4LISTING_DICT reference. Each occurrence
    is one fully-enumerated household in the barangay frame.

    Item groups:
      1. Per-household bookkeeping (LISTING_NO, status flags).
      2. Minimum-necessary household identifiers per Carl's Q5 decision
         (phone optional, alpha-11). HEAD_NAME + ADDRESS + MOBILE.
      3. Eligibility signals: HH_ELIGIBLE flag for desk-review.

    Item-width and NA-code discipline (project-wide):
      - F4_STATUS NA=9 at width 1 (status is required; NA=9 reserved).
      - HH_ELIGIBLE NA=9 at width 1.

    Max occurrences: 999 — Carl's Q4 default. A barangay-day with >999
    listed households is operationally implausible.
    """

    F4_STATUS_OPTIONS = [
        ("Pending — not yet attempted",       "0"),
        ("Completed",                         "1"),
        ("In progress",                       "2"),
        ("Refused at F4",                     "3"),
        ("Postponed",                         "4"),
        ("Not applicable",                    "9"),
    ]

    HH_ELIGIBLE_OPTIONS = [
        ("Yes — household meets F4 eligibility",  "1"),
        ("No — household ineligible",             "2"),
        ("Not applicable",                        "9"),
    ]

    items = [
        # --- Per-household bookkeeping -------------------------------
        # LISTING_NO is the 1-based occurrence index within this session.
        # NOT the F-series CASE_SEQ. F-series CASE_SEQ is allocated by F4
        # preproc when F4 consumes this roster. LISTING_NO is the value
        # stamped into F4.FIELD_CONTROL.HH_LISTING_NO (Option C dual-
        # linkage rule — see 115_F4 quartet build, FIELD_CONTROL extras).
        numeric("LISTING_NO",            "Listing roster sequence",            length=4,
                zero_fill=True),
        # F4 interview status — maintained downstream by F4 (starts at 0).
        numeric("F4_STATUS",             "F4 interview status",                length=1,
                value_set_options=F4_STATUS_OPTIONS),
        # F4 CASE_SEQ slot — populated by F4.preproc upon consumption.
        # Width-3 zero-fill matches build_id_block()'s slot 5.
        numeric("ASSIGNED_F4_CASE_SEQ",  "F4 CASE_SEQ once F4 consumes this row",
                length=3, zero_fill=True),
        # Replacement-reserve flag — set when this row is drawn from the
        # 10-row reserve pool rather than the primary FRAME_TARGET. The
        # supervisor dashboard uses this to enforce the 5-10% replacement
        # rate cap (Annex D — supervisor-side enforcement, not CSPro).
        numeric("FROM_RESERVE_POOL",     "Drawn from replacement reserve pool",
                length=1,
                value_set_options=[
                    ("Yes", "1"),
                    ("No",  "2"),
                    ("Not applicable", "9"),
                ]),

        # --- Listed household PII (minimum-necessary) ----------------
        alpha("HEAD_LAST_NAME",          "Household head last name",           length=40),
        alpha("HEAD_FIRST_NAME",         "Household head first name",          length=40),
        alpha("HEAD_MIDDLE_INIT",        "Household head middle initial (or hyphen if none)",
              length=5),
        alpha("HEAD_NAME_EXT",           "Household head name extension (e.g., Jr., III)",
              length=10),
        alpha("HH_ADDRESS",              "Household address (street / sitio / purok)",
              length=200),

        # --- Contact (Q5 decision: optional, alpha-11) --------------
        # Phone optional; alpha-11 holds Philippine mobile (09xxxxxxxxx)
        # without forcing numeric type (allows "" blank for "no phone").
        # Validation in APC checks regex ^09\d{9}$ OR empty.
        alpha("MOBILE",                  "Household contact mobile (09xxxxxxxxx; blank if none)",
              length=11),

        # --- Eligibility ---------------------------------------------
        numeric("HH_ELIGIBLE",           "Household meets F4 eligibility criteria",
                length=1, value_set_options=HH_ELIGIBLE_OPTIONS),
        alpha("INELIGIBLE_REASON",       "If ineligible, brief reason (free text)",
              length=120),
    ]

    return record("REC_LISTING_BRGY_FRAME", "Barangay Household Listing Frame", "P",
                  items, max_occurs=999, required=False)


def build_listing_barangay_gps():
    """REC_LISTING_BARANGAY_GPS — barangay GPS for the listing session.

    One occurrence per session. Per Carl's Q6 decision: GPS only, no
    verification photo. The enumerator captures GPS at the session start
    point (e.g., barangay hall) so the desk reviewer can confirm the
    listing crew actually visited the assigned barangay.

    Items emitted by shared._gps_fields() — see shared/Capture-Helpers.apc
    for the capture handler. Record-type 'Z' matches F1's
    REC_FACILITY_CAPTURE / F3-listing's REC_LISTING_FACILITY_CAPTURE
    conventions.

    F4 listing has only GPS audit (no photo audit) per Q6.
    """
    return record(
        "REC_LISTING_BARANGAY_GPS",
        "Barangay GPS Capture (listing session)", "Z",
        items=_gps_fields(prefix="BARANGAY_"),
    )


# ============================================================
# ASSEMBLE
# ============================================================

def build_dictionary():
    """Assemble the F4Listing dictionary.

    Uses the same 6-item listing-session ID block from
    shared/cspro_helpers.py::build_listing_id_block() (Carl's Q3 decision
    — reuse F3-listing's 20-digit shape; per-session SSS increment
    preserves uniqueness; sync path encodes BARANGAY_CODE as a separate
    segment derived from REC_LISTING_CONTROL.BARANGAY_CODE).
    """
    records = [
        # Root record (recordType "1") — required by CSPro hierarchy
        record("F4LISTING_REC", "F4Listing Record", "1", []),
        build_listing_control(),
        build_household_roster(),
        build_listing_barangay_gps(),
    ]

    return build_dictionary_from_helpers(
        dict_name="F4LISTING_DICT",
        dict_label="F4Listing",
        id_items=build_listing_id_block(),
        records=records,
    )


def main():
    out_path = Path(__file__).parent / "F4Listing.dcf"
    dictionary = build_dictionary()
    out_path.write_text(json.dumps(dictionary, indent=2), encoding="utf-8")

    record_count = len(dictionary["levels"][0]["records"])
    item_count = sum(len(r["items"]) for r in dictionary["levels"][0]["records"])
    print(f"Wrote {out_path}")
    print(f"  Records: {record_count}")
    print(f"  Items:   {item_count}")


if __name__ == "__main__":
    main()
