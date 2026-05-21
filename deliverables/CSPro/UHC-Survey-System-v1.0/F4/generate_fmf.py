"""
generate_fmf.py — F4 Household Survey CSPro Form File generator
                  (UHC Survey System v1.0 rebuild — phase 4).

Emits HouseholdSurvey.generated.fmf — the skeleton form layout for
HouseholdSurvey.dcf (FIELD_CONTROL -> geo -> capture -> sections A-Q ->
closing).

Generator-first / hybrid approach (per Form-Layout-Principles.md): one form
per DCF record. The repeating C_HOUSEHOLD_ROSTER record gets its own form and
nothing else (Principles section 1.3 — rosters scroll alone); CSPro renders it
as a roster grid because the DCF record is repeating. The Designer pass splits
oversized sections and applies visual polish.

The output is non-destructive — it writes to HouseholdSurvey.generated.fmf and
never touches a hand-finished HouseholdSurvey.fmf.

Run:
    python generate_fmf.py        # writes HouseholdSurvey.generated.fmf next to this file
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_dcf import build_dictionary_f4


DICT_NAME = "HOUSEHOLDSURVEY_FF"
DICT_LABEL = "HouseholdSurvey"
DCF_REL_PATH = r".\HouseholdSurvey.dcf"

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
# closing form.
FIELD_CONTROL_CASE_START = {
    "SURVEY_CODE", "INTERVIEWER_ID", "DATE_STARTED", "TIME_STARTED",
    "AAPOR_DISPOSITION", "HH_LISTING_NO", "CONSENT_GIVEN",
}
FIELD_CONTROL_CASE_END = {
    "SURVEY_TEAM_LEADER_S_NAME", "ENUMERATOR_S_NAME",
    "FIELD_VALIDATED_BY", "FIELD_EDITED_BY",
    "DATE_FIRST_VISITED", "DATE_FINAL_VISIT", "TOTAL_NUMBER_OF_VISITS",
    "ENUM_RESULT_FIRST_VISIT", "ENUM_RESULT_FINAL_VISIT",
}


FORM_PLAN = [
    # (label, [(record_name, filter_spec), ...])
    ("FC Metadata - case start",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_START})]),

    ("FC Geographic ID (household) - PSGC cascade + F4->F3 linkage",
     [("HOUSEHOLD_GEO_ID", None)]),

    ("FC Household GPS Capture",
     [("REC_HOUSEHOLD_CAPTURE", None)]),

    ("FC Verification Photo",
     [("REC_CASE_VERIFICATION", None)]),

    ("A. Introduction and Informed Consent",
     [("A_INFORMED_CONSENT", None)]),

    ("B. Respondent Profile - split into B1/B2/B3 in Designer",
     [("B_RESPONDENT_PROFILE", None)]),

    ("C. Household Roster (repeating x20 - roster grid)",
     [("C_HOUSEHOLD_ROSTER", None)]),

    ("C. Household Private Insurance Gate (Q47)",
     [("C_HH_PRIVATE_INS_GATE", None)]),

    ("D. UHC Awareness",
     [("D_UHC_AWARENESS", None)]),

    ("E. YAKAP/Konsulta Awareness",
     [("E_YAKAP_KONSULTA", None)]),

    ("F. BUCAS Awareness and Utilization",
     [("F_BUCAS_AWARENESS", None)]),

    ("G. Access to Medicines - split into G1/G2 in Designer",
     [("G_ACCESS_MEDICINES", None)]),

    ("H. PhilHealth Registration - split into H1/H2 in Designer",
     [("H_PHILHEALTH_REG", None)]),

    ("I. Primary Care Utilization",
     [("I_PRIMARY_CARE", None)]),

    ("J. Household Members' Health-Seeking Behavior",
     [("J_HEALTH_SEEKING", None)]),

    ("K. Experiences and Satisfaction with Referrals - split into K1/K2 in Designer",
     [("K_REFERRALS", None)]),

    ("L. No Balance Billing (NBB) Awareness",
     [("L_NBB_AWARENESS", None)]),

    ("M. ZBB / MAIFIP / Bill Breakdown - split into M1/M2 in Designer",
     [("M_ZBB_MAIFIP_BILL", None)]),

    ("N. Household Expenditures (WHO/SHA) - split into N1-N5 in Designer",
     [("N_HOUSEHOLD_EXPENDITURES", None)]),

    ("O. Sources of Funds for Health",
     [("O_SOURCES_OF_FUNDS", None)]),

    ("P. Financial Risk Protection",
     [("P_FINANCIAL_RISK", None)]),

    ("Q. Anxiety about Household Finances",
     [("Q_FINANCIAL_ANXIETY", None)]),

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
    dictionary = build_dictionary_f4()
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
    _emit_form(lines, 1, "HouseholdSurvey Record", [])

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
    out_path = Path(__file__).parent / "HouseholdSurvey.generated.fmf"
    fmf_text, orphan_count = build_fmf()
    out_path.write_text(fmf_text, encoding="utf-8")
    sys.stderr.write(f"Wrote {out_path} ({orphan_count} orphan items)\n")


if __name__ == "__main__":
    main()
