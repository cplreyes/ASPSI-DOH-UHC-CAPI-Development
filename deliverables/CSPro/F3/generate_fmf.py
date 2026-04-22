"""
generate_fmf.py - F3 Patient Survey CSPro Form File generator.

Emits PatientSurvey.generated.fmf - the skeleton form layout for
PatientSurvey.dcf. Mirrors the 32-form plan in F3-Form-Layout-Plan.md
(FIELD_CONTROL -> Geo -> capture triggers -> sections A-L -> closing).

Generator-first / hybrid approach (per Form-Layout-Principles.md section 6):
this script produces form names, labels, item membership, and tab order.
Visual polish (field positions, sizes, fonts, control types, capture-trigger
button bindings) is Designer work on the committed PatientSurvey.fmf.

The output is non-destructive - it writes to PatientSurvey.generated.fmf
and never touches PatientSurvey.fmf.

Run:
    python generate_fmf.py        # writes PatientSurvey.generated.fmf next to this file
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_dcf import build_f3_dictionary


DICT_NAME = "PATIENTSURVEY_FF"
DICT_LABEL = "PatientSurvey"
DCF_REL_PATH = r".\PatientSurvey.dcf"

DEFAULT_FONT = (
    "DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Arial"
)
ENTRY_FONT = (
    "FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Courier New"
)
DEFAULT_SIZE = "806,300"  # Designer resizes per form density


# Case-start items stay on Form 1; case-end items migrate to Form 32 (closing).
FIELD_CONTROL_CASE_START = {
    "SURVEY_CODE", "INTERVIEWER_ID", "DATE_STARTED", "TIME_STARTED",
    "AAPOR_DISPOSITION", "PATIENT_TYPE", "PATIENT_LISTING_NO", "CONSENT_GIVEN",
}
FIELD_CONTROL_CASE_END = {
    "SURVEY_TEAM_LEADER_S_NAME", "ENUMERATOR_S_NAME",
    "FIELD_VALIDATED_BY", "FIELD_EDITED_BY",
    "DATE_FIRST_VISITED", "DATE_FINAL_VISIT", "TOTAL_NUMBER_OF_VISITS",
    "ENUM_RESULT_FIRST_VISIT", "ENUM_RESULT_FINAL_VISIT",
}


FORM_PLAN = [
    # (label, [(record_name, filter_spec), ...])
    # filter_spec: None = all items; {"names": [...]} = explicit name list.
    #
    # Strategy: one form per record for section records. Designer splits
    # oversized sections (B, C, D, E, G, H, I) into multiple forms per
    # F3-Form-Layout-Plan.md screen-density budget, and wires form-level
    # skips (Q1 gate, Q162 terminator, Q169 routing).
    ("FC Metadata - case start",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_START})]),

    ("FC Geographic ID + F1 linkage",
     [("PATIENT_GEO_ID", None)]),

    ("FC Facility GPS Capture",
     [("REC_FACILITY_CAPTURE", None)]),

    ("FC Patient Home GPS + Verification Photo",
     [("REC_PATIENT_HOME_CAPTURE", None),
      ("REC_CASE_VERIFICATION", None)]),

    ("A. Informed Consent (Q1 gate)",
     [("A_INFORMED_CONSENT", None)]),

    ("B. Patient Profile - split into B1/B2/B3 in Designer",
     [("B_PATIENT_PROFILE", None)]),

    ("C. UHC Awareness - split into C1/C2 in Designer",
     [("C_UHC_AWARENESS", None)]),

    ("D. PhilHealth Registration - split into D1/D2 in Designer",
     [("D_PHILHEALTH_REG", None)]),

    ("E. Primary Care + YAKAP/Konsulta - split into E1/E2/E3 in Designer",
     [("E_PRIMARY_CARE", None)]),

    ("F. Health-Seeking - split into F1/F2 in Designer",
     [("F_HEALTH_SEEKING", None)]),

    ("G. Outpatient Care - split into G1/G2/G3 (Q92/Q94 matrix) in Designer",
     [("G_OUTPATIENT_CARE", None)]),

    ("H. Inpatient Care - split into H1/H2/H3 (Q107/Q109/Q112/Q113 matrix) in Designer",
     [("H_INPATIENT_CARE", None)]),

    ("I. Financial Risk - split into I1 NBB/ZBB, I2 MAIFIP, I3 distress in Designer",
     [("I_FINANCIAL_RISK", None)]),

    ("J. Satisfaction",
     [("J_SATISFACTION", None)]),

    ("K. Access to Medicines - split into K1/K2 in Designer",
     [("K_ACCESS_MEDICINES", None)]),

    ("L. Referrals - split into L1 (Q162 terminator) / L2 (Q169 routing) in Designer",
     [("L_REFERRALS", None)]),

    ("Closing - case end",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_END})]),
]


def _filter_items(items, spec):
    """Apply a filter_spec to a record's item list; preserves source order."""
    if spec is None:
        return list(items)
    if "names" in spec:
        keep = set(spec["names"])
        return [it for it in items if it["name"] in keep]
    if "exclude" in spec:
        skip = set(spec["exclude"])
        return [it for it in items if it["name"] not in skip]
    raise ValueError(f"Unknown filter_spec keys: {spec!r}")


def _emit_form(lines, form_num, label, item_names):
    lines.append("[Form]")
    lines.append(f"Name=FORM{form_num:03d}")
    lines.append(f"Label={label}")
    lines.append("Level=1")
    lines.append(f"Size={DEFAULT_SIZE}")
    lines.append("  ")
    for name in item_names:
        lines.append(f"Item={name}")
    lines.append("  ")
    lines.append("[EndForm]")
    lines.append("  ")


def build_fmf():
    dictionary = build_f3_dictionary()
    level = dictionary["levels"][0]
    records_by_name = {r["name"]: r for r in level["records"]}
    id_item_name = level["ids"]["items"][0]["name"]

    # Sanity: every record referenced in FORM_PLAN exists in the dictionary.
    referenced = {rec for _, parts in FORM_PLAN for rec, _ in parts}
    missing = referenced - set(records_by_name)
    if missing:
        raise RuntimeError(
            f"FORM_PLAN references records missing from dict: {sorted(missing)}. "
            f"Available: {sorted(records_by_name)}"
        )

    # Track which items each record has consumed so we can flag orphans
    # (skeleton must cover every non-container DCF item).
    record_items_consumed = {name: set() for name in records_by_name}

    lines = []
    lines.append("[FormFile]")
    lines.append("Version=CSPro 8.0")
    lines.append(f"Name={DICT_NAME}")
    lines.append(f"Label={DICT_LABEL}")
    lines.append(DEFAULT_FONT)
    lines.append(ENTRY_FONT)
    lines.append("Type=SystemControlled")
    lines.append("  ")
    lines.append("[Dictionaries]")
    lines.append(f"File={DCF_REL_PATH}")
    lines.append("  ")

    # FORM000 - Id Items container (QUESTIONNAIRE_NO sits at dictionary level)
    _emit_form(lines, 0, "(Id Items)", [id_item_name])

    # FORM001 - top-level container record (empty form, level-1)
    _emit_form(lines, 1, "PatientSurvey Record", [])

    # FORM002..FORM033 - planned forms
    for idx, (label, parts) in enumerate(FORM_PLAN, start=2):
        collected = []
        for rec_name, spec in parts:
            filtered = _filter_items(records_by_name[rec_name]["items"], spec)
            for it in filtered:
                record_items_consumed[rec_name].add(it["name"])
                collected.append(it["name"])
        _emit_form(lines, idx, label, collected)

    # Orphan check - any DCF item not placed on a form?
    orphans = []
    for rec_name, rec in records_by_name.items():
        if rec["recordType"] == "1":
            continue  # top-level container record
        placed = record_items_consumed[rec_name]
        for it in rec["items"]:
            if it["name"] not in placed:
                orphans.append(f"{rec_name}.{it['name']}")
    if orphans:
        sys.stderr.write(
            f"WARNING: {len(orphans)} items not placed on any form "
            "(skeleton needs Q-range refinement):\n"
        )
        for o in orphans:
            sys.stderr.write(f"  {o}\n")

    return "\r\n".join(lines) + "\r\n", len(orphans)


def main():
    out_path = Path(__file__).parent / "PatientSurvey.generated.fmf"
    fmf_text, orphan_count = build_fmf()
    out_path.write_text(fmf_text, encoding="utf-8")
    sys.stderr.write(f"Wrote {out_path} ({orphan_count} orphan items)\n")


if __name__ == "__main__":
    main()
