"""
generate_fmf.py — F1 Facility Head Survey CSPro Form File generator
                  (UHC Survey System v1.0 rebuild — phase 4).

Emits FacilityHeadSurvey.generated.fmf — the skeleton form layout for
FacilityHeadSurvey.dcf. Mirrors the form plan in F1-Form-Layout-Plan.md
(FIELD_CONTROL -> geo -> capture triggers -> sections A-H -> secondary
stubs -> closing).

Generator-first / hybrid approach (per Form-Layout-Principles.md section 6):
this script produces form names, labels, item membership, and tab order. One
form per DCF record; the CSPro Designer pass splits oversized sections (C, D,
E, F, G) into the multi-form breakdown in F1-Form-Layout-Plan.md and applies
visual polish (field positions, sizes, control types, capture-trigger button
bindings).

The output is non-destructive — it writes to FacilityHeadSurvey.generated.fmf
and never touches a hand-finished FacilityHeadSurvey.fmf.

Run:
    python generate_fmf.py        # writes FacilityHeadSurvey.generated.fmf next to this file
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_dcf import build_dictionary_f1


DICT_NAME = "FACILITYHEADSURVEY_FF"
DICT_LABEL = "FacilityHeadSurvey"
DCF_REL_PATH = r".\FacilityHeadSurvey.dcf"

DEFAULT_FONT = (
    "DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Arial"
)
ENTRY_FONT = (
    "FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Courier New"
)
DEFAULT_SIZE = "806,300"  # Designer resizes per form density


# FIELD_CONTROL splits: case-start items open the interview on Form 1;
# case-end items (visit log, validation, disposition) migrate to the
# closing form. See F1-Form-Layout-Plan.md Forms 1 + 29.
FIELD_CONTROL_CASE_START = {
    "SURVEY_CODE", "INTERVIEWER_ID", "DATE_STARTED", "TIME_STARTED",
    "AAPOR_DISPOSITION", "CONSENT_GIVEN",
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
    # Strategy: one form per record. The Designer pass splits oversized
    # sections per F1-Form-Layout-Plan.md and wires the form-level skips
    # (consent gate, tenure terminator, Q51 YAKAP branch).
    ("FC Metadata - case start",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_START})]),

    ("FC Geographic ID (facility) - PSGC cascade + barangay",
     [("HEALTH_FACILITY_GEO", None)]),

    ("FC Facility GPS + Verification Photo",
     [("REC_FACILITY_CAPTURE", None)]),

    ("A. Facility Head Profile - split into A1 profile / A2 consent-contacts in Designer",
     [("A_FACILITY_HEAD_PROFILE", None)]),

    ("B. Facility Profile",
     [("B_FACILITY_PROFILE", None)]),

    ("C. UHC Implementation - split into C1-C5 in Designer",
     [("C_UHC_IMPLEMENTATION", None)]),

    ("D. YAKAP/Konsulta - split into D1-D4 (Q51 gate) in Designer",
     [("D_YAKAP_KONSULTA", None)]),

    ("E. BUCAS/GAMOT - split into E1 BUCAS / E2 GAMOT in Designer",
     [("E_BUCAS_GAMOT", None)]),

    ("F. DOH Licensing - split into F1 gate / F2 Q121 grid in Designer",
     [("F_DOH_LICENSING", None)]),

    ("G. Service Delivery - split into G1 NBB / G2 ZBB / G3 LGU / G4 Referral in Designer",
     [("G_SERVICE_DELIVERY", None)]),

    ("H. Human Resources",
     [("H_HUMAN_RESOURCES", None)]),

    ("Secondary Data - Hospital Census (stub - structure TBD)",
     [("SEC_HOSP_CENSUS", None)]),

    ("Secondary Data - HCW Roster (stub - structure TBD)",
     [("SEC_HCW_ROSTER", None)]),

    ("Secondary Data - YAKAP Services (stub - structure TBD)",
     [("SEC_YK_SERVICES", None)]),

    ("Secondary Data - Lab Prices (stub - structure TBD)",
     [("SEC_LAB_PRICES", None)]),

    ("Closing - case end (visit log + final disposition)",
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
    dictionary = build_dictionary_f1()
    level = dictionary["levels"][0]
    records_by_name = {r["name"]: r for r in level["records"]}
    id_item_names = [it["name"] for it in level["ids"]["items"]]

    # Sanity: every record referenced in FORM_PLAN exists in the dictionary.
    referenced = {rec for _, parts in FORM_PLAN for rec, _ in parts}
    missing = referenced - set(records_by_name)
    if missing:
        raise RuntimeError(
            f"FORM_PLAN references records missing from dict: {sorted(missing)}. "
            f"Available: {sorted(records_by_name)}"
        )

    # Track which items each record has consumed so orphans can be flagged
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

    # FORM000 - the 5-item RR-PP-MMM-FF-CCC ID block container.
    _emit_form(lines, 0, "(Id Items)", id_item_names)

    # FORM001 - top-level container record (empty form, level-1).
    _emit_form(lines, 1, "FacilityHeadSurvey Record", [])

    # FORM002.. - planned forms.
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
            f"WARNING: {len(orphans)} items not placed on any form:\n"
        )
        for o in orphans:
            sys.stderr.write(f"  {o}\n")

    return "\r\n".join(lines) + "\r\n", len(orphans)


def main():
    out_path = Path(__file__).parent / "FacilityHeadSurvey.generated.fmf"
    fmf_text, orphan_count = build_fmf()
    out_path.write_text(fmf_text, encoding="utf-8")
    sys.stderr.write(f"Wrote {out_path} ({orphan_count} orphan items)\n")


if __name__ == "__main__":
    main()
