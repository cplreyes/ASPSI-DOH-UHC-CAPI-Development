"""Read a CSPro CSV export (one instrument) into normalized, PII-light Case records.

CSPro's CSV export uses dictionary item names as column headers, so FIELD_MAP just
names the items we read per instrument. Completeness comes from the CASE_DISPOSITION
sentinel — now on all three instruments (F3/F4 shipped 2026-06-21, F1 added 2026-06-23
via #744). When CASE_DISPOSITION is blank (a case collected before the sentinel shipped),
_disposition falls back to the result code, so a mixed old/new population classifies right.

Field names below are confirmed against the live dictionaries (F1/F3/F4, 2026-06-23):
  - F4 GPS latitude item is `LATITUDE` (label "GPS Latitude") — there is no HH_GPS_LATITUDE.
  - F1's final-visit date item is `DATE_OF_FINAL_VISIT_TO_THE_FACILITY` (F3/F4 use DATE_FINAL_VISIT).
  - F1 GPS latitude is `FACILITY_GPS_LATITUDE`; F1 now carries `CASE_DISPOSITION` + `BREAKOFF` (#744).
"""
import csv
from dataclasses import dataclass

# Per-instrument item names (verified against F{1,3,4} .dcf, 2026-06-21).
FIELD_MAP = {
    "F1": {"disposition": "CASE_DISPOSITION", "result": "ENUM_RESULT_FINAL_VISIT",
           "completed_codes": {"1"}, "gps_lat": "FACILITY_GPS_LATITUDE",
           "photo": "VERIFICATION_PHOTO_FILENAME", "early": "Q1_NAME",
           "date": "DATE_OF_FINAL_VISIT_TO_THE_FACILITY", "enumerator": "ENUMERATOR_S_NAME"},
    "F3": {"disposition": "CASE_DISPOSITION", "result": "ENUM_RESULT_FINAL_VISIT",
           "completed_codes": {"1", "2", "5"}, "gps_lat": "FACILITY_GPS_LATITUDE",
           "photo": "VERIFICATION_PHOTO_FILENAME", "early": "Q1_IS_PATIENT",
           "date": "DATE_FINAL_VISIT", "enumerator": "ENUMERATOR_S_NAME"},
    "F4": {"disposition": "CASE_DISPOSITION", "result": "ENUM_RESULT_FINAL_VISIT",
           "completed_codes": {"1"}, "gps_lat": "LATITUDE",
           "photo": "VERIFICATION_PHOTO_FILENAME", "early": "Q1_IS_HH_HEAD",
           "date": "DATE_FINAL_VISIT", "enumerator": "ENUMERATOR_S_NAME"},
}


@dataclass
class Case:
    instrument: str
    case_key: str
    facility: str
    enumerator_name: str   # PII — used only for the spot-check pointer, never rendered
    disposition: str       # "complete" | "partial" | "in_progress"
    result_code: str
    has_gps: bool
    has_photo: bool
    final_visit_date: str
    answers_present: bool


def _facility_from_key(key):
    k = (key or "").strip()
    if len(k) < 12:
        return k
    return f"{k[0:2]}-{k[2:4]}-{k[4:7]}-{k[7:9]}"   # RR-PP-MMM-FF


def _disposition(row, m):
    """complete / partial / in_progress from the CASE_DISPOSITION sentinel when it is
    populated, else from the result code (handles cases collected before the sentinel
    shipped, whose CASE_DISPOSITION is blank — see module docstring)."""
    if m["disposition"]:
        d = (row.get(m["disposition"]) or "").strip()
        if d == "1":
            return "complete"
        if d == "0":
            return "in_progress"
        if d != "":            # 2 (or any other non-zero code) = partial / broke off
            return "partial"
        # d == "" -> sentinel not populated (pre-sentinel case); fall through to result code
    r = (row.get(m["result"]) or "").strip()
    if r in m["completed_codes"]:
        return "complete"
    if r == "":
        return "in_progress"
    return "partial"


def load_cases(csv_path, instrument):
    m = FIELD_MAP[instrument]
    out = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            key = (row.get("QUESTIONNAIRE_NUMBER") or "").strip()
            out.append(Case(
                instrument=instrument,
                case_key=key,
                facility=_facility_from_key(key),
                enumerator_name=(row.get(m["enumerator"]) or "").strip(),
                disposition=_disposition(row, m),
                result_code=(row.get(m["result"]) or "").strip(),
                has_gps=bool((row.get(m["gps_lat"]) or "").strip()),
                has_photo=bool((row.get(m["photo"]) or "").strip()),
                final_visit_date=(row.get(m["date"]) or "").strip(),
                answers_present=bool((row.get(m["early"]) or "").strip()),
            ))
    return out
