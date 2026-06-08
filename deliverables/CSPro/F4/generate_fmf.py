"""
generate_fmf.py - F4 Household Survey CSPro Form File generator.

Emits HouseholdSurvey.generated.fmf - a COMPLETE, bindable CSPro 8.0 form file for
HouseholdSurvey.dcf. Mirrors the form plan in F4-Form-Layout-Plan.md
(FIELD_CONTROL -> Geo+GPS -> photo -> sections A-Q -> closing).

FULL-STRUCTURE generation (2026-06-08): emits the logical structure CSPro requires
to open the file as a bound application without stripping items:
  [Level] -> one [Group] per form (Form=N) -> [Field] + [Text] per item.
Auto-layout mirrors the working F1/F3 .fmf. The household roster
(C_HOUSEHOLD_ROSTER, max 20) is emitted as a ROSTER group (Required=No, Type=Record,
TypeName=<record>, Max=<occ>) per the hand-laid F4 reference; all other records are
singular groups (Required=Yes, Max=1). DataCaptureType=RadioButton for value-set
(coded) items, TextBox otherwise (UseUnicodeTextBox=Yes for alpha). The id-items form
and the level-1 container form are EMPTY groups (id items live in the dict ID block).

Run:
    python generate_fmf.py        # writes HouseholdSurvey.generated.fmf next to this file
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate_dcf import build_f4_dictionary
from cspro_helpers import _truncate_long_labels


DICT_LABEL = "HouseholdSurvey"
FF_NAME = "HOUSEHOLDSURVEY_FF"
DCF_REL_PATH = r".\HouseholdSurvey.dcf"

DEFAULT_FONT = (
    "DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Arial"
)
ENTRY_FONT = (
    "FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Courier New"
)

# --- Auto-layout geometry (mirrors the working F1 .fmf) ---
ROW_H = 30
TOP_Y = 27
LABEL_X = 50
LABEL_X2 = 330
FIELD_X = 350
FIELD_TEXTBOX_X2 = 760
FIELD_RADIO_X2 = 365
FIELD_H = 20
TEXT_H = 16
FORM_W = 806


FIELD_CONTROL_CASE_START = {
    "SURVEY_CODE", "INTERVIEWER_ID", "DATE_STARTED", "TIME_STARTED",
    "AAPOR_DISPOSITION", "CONSENT_GIVEN", "HH_LISTING_NO", "LANGUAGE_USED",
}
FIELD_CONTROL_CASE_END = {
    "SURVEY_TEAM_LEADER_S_NAME", "ENUMERATOR_S_NAME",
    "FIELD_VALIDATED_BY", "FIELD_EDITED_BY",
    "DATE_FIRST_VISITED", "DATE_FINAL_VISIT", "TOTAL_NUMBER_OF_VISITS",
    "ENUM_RESULT_FIRST_VISIT", "ENUM_RESULT_FINAL_VISIT",
}


FORM_PLAN = [
    ("FC Metadata - case start",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_START})]),
    ("FC Geographic ID + HH GPS Capture",
     [("HOUSEHOLD_GEO_ID", None)]),
    ("FC Case Verification Photo",
     [("REC_CASE_VERIFICATION", None)]),
    ("A. Informed Consent (Q1 gate)",
     [("A_INFORMED_CONSENT", None)]),
    ("B. Respondent Profile",
     [("B_RESPONDENT_PROFILE", None)]),
    ("C. Household Roster - REPEATING (one member per row)",
     [("C_HOUSEHOLD_ROSTER", None)]),
    ("C. HH Private Insurance Gate (Q47)",
     [("C_HH_PRIVATE_INS_GATE", None)]),
    ("D. UHC Awareness",
     [("D_UHC_AWARENESS", None)]),
    ("E. YAKAP / Konsulta",
     [("E_YAKAP_KONSULTA", None)]),
    ("F. BUCAS Awareness",
     [("F_BUCAS_AWARENESS", None)]),
    ("G. Access to Medicines",
     [("G_ACCESS_MEDICINES", None)]),
    ("H. PhilHealth Registration",
     [("H_PHILHEALTH_REG", None)]),
    ("I. Primary Care",
     [("I_PRIMARY_CARE", None)]),
    ("J. Health Seeking",
     [("J_HEALTH_SEEKING", None)]),
    ("K. Referrals",
     [("K_REFERRALS", None)]),
    ("L. NBB Awareness",
     [("L_NBB_AWARENESS", None)]),
    ("M. ZBB / MAIFIP / Bill-Recall",
     [("M_ZBB_MAIFIP_BILL", None)]),
    ("N. Household Expenditures",
     [("N_HOUSEHOLD_EXPENDITURES", None)]),
    ("O. Sources of Funds for Health",
     [("O_SOURCES_OF_FUNDS", None)]),
    ("P. Financial Risk",
     [("P_FINANCIAL_RISK", None)]),
    ("Q. Financial Anxiety",
     [("Q_FINANCIAL_ANXIETY", None)]),
    ("Closing - case end",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_END})]),
]


def _filter_items(items, spec):
    if spec is None:
        return list(items)
    if "names" in spec:
        keep = set(spec["names"])
        return [it for it in items if it["name"] in keep]
    if "exclude" in spec:
        skip = set(spec["exclude"])
        return [it for it in items if it["name"] not in skip]
    raise ValueError(f"Unknown filter_spec keys: {spec!r}")


def _group_symbol(primary_record, used):
    base = re.sub(r"[^A-Za-z0-9]+", "_", primary_record).strip("_").upper() + "_FORM"
    if not base[0].isalpha():
        base = "F_" + base
    sym, i = base, 2
    while sym in used:
        sym = f"{base}_{i}"
        i += 1
    used.add(sym)
    return sym


def _form_height(n_items):
    return max(300, TOP_Y + n_items * ROW_H + 40)


def _emit_form(lines, form_num, label, item_names, height, roster=None):
    lines.append("[Form]")
    lines.append(f"Name=FORM{form_num:03d}")
    lines.append(f"Label={label}")
    lines.append("Level=1")
    if roster:
        # Mark the form as repeating over the roster record. Without this Repeat=
        # line CSEntry rejects the forms<->dictionary reconcile ("open in Designer,
        # make changes, save"); the [Group] Type=Record alone is not enough.
        # Verified 2026-06-08 against the Designer-reconciled FMF.
        lines.append(f"Repeat={roster['type_name']}")
    lines.append(f"Size={FORM_W},{height}")
    lines.append("  ")
    for name in item_names:
        lines.append(f"Item={name}")
    lines.append("  ")
    lines.append("[EndForm]")
    lines.append("  ")


def _emit_group(lines, group_sym, label, form_one_based, item_objs, dict_name, roster=None):
    lines.append("[Group]")
    # The roster record is required in the dcf (occurrences.required=True), and the
    # Designer-reconciled FMF uses Required=Yes for it, so all groups are Required=Yes.
    lines.append("Required=Yes")
    lines.append(f"Name={group_sym}")
    lines.append(f"Label={label}")
    lines.append(f"Form={form_one_based}")
    if roster:
        lines.append("Type=Record")
        lines.append(f"TypeName={roster['type_name']}")
        lines.append(f"Max={roster['max']}")
    else:
        lines.append("Max=1")
    if not item_objs:
        lines.append("[EndGroup]")
        lines.append("  ")
        return
    lines.append("  ")
    for i, it in enumerate(item_objs):
        y = TOP_Y + i * ROW_H
        coded = bool(it.get("valueSets"))
        is_alpha = it.get("contentType") == "alpha"
        field_x2 = FIELD_RADIO_X2 if coded else FIELD_TEXTBOX_X2
        capture = "RadioButton" if coded else "TextBox"
        text = (it["labels"][0]["text"] if it.get("labels") else it["name"]).replace("\n", " ").replace("\r", " ")
        lines.append("[Field]")
        lines.append(f"Name={it['name']}")
        lines.append(f"Position={FIELD_X},{y},{field_x2},{y + FIELD_H}")
        lines.append(f"Item={it['name']},{dict_name}")
        if not coded and is_alpha:
            lines.append("UseUnicodeTextBox=Yes")
        lines.append(f"DataCaptureType={capture}")
        lines.append(f"Form={form_one_based}")
        lines.append("  ")
        lines.append("[Text]")
        lines.append(f"Position={LABEL_X},{y + 3},{LABEL_X2},{y + 3 + TEXT_H}")
        lines.append(f"Text={text}")
        lines.append(" ")
        lines.append("  ")
    lines.append("[EndGroup]")
    lines.append("  ")


def build_fmf():
    dictionary = build_f4_dictionary()
    _truncate_long_labels(dictionary)  # match the .dcf's 255-char label cap (CSPro max)
    dict_name = dictionary.get("name", "HOUSEHOLDSURVEY_DICT")
    level = dictionary["levels"][0]
    level_name = level.get("name", "HOUSEHOLDSURVEY_LEVEL")
    records_by_name = {r["name"]: r for r in level["records"]}
    id_item_names = [it["name"] for it in level["ids"]["items"]]

    def _roster_info(record_name):
        occ = records_by_name[record_name].get("occurrences") or {}
        mx = occ.get("maximum", 1) if isinstance(occ, dict) else 1
        return {"type_name": record_name, "max": mx} if (mx and mx > 1) else None

    referenced = {rec for _, parts in FORM_PLAN for rec, _ in parts}
    missing = referenced - set(records_by_name)
    if missing:
        raise RuntimeError(f"FORM_PLAN references missing records: {sorted(missing)}")

    record_items_consumed = {name: set() for name in records_by_name}
    used_group_syms = set()

    forms = []
    # FORM000 - case-key ID items, entered FIRST (before consent) so a consent refusal
    # has a valid case key to save (cf. F3-DT-02 + the CAPI Census "Geocodes" form).
    id_objs = list(level["ids"]["items"])
    _ = id_item_names
    forms.append({"num": 0, "label": "Case Key (Facility + Household ID)", "group_sym": "IDS0_FORM",
                  "form_item_names": [it["name"] for it in id_objs], "group_item_objs": id_objs,
                  "roster": None})
    used_group_syms.add("IDS0_FORM")
    # FORM001.. - planned forms. (The empty level-1 "container" record/form was
    # removed 2026-06-08 — it was a vestigial item-less record CSEntry never
    # populated and it BLOCKED case-key persistence; see Desk-Test matrix. Forms
    # now run key=0, plan=1+.)
    for idx, (label, parts) in enumerate(FORM_PLAN, start=1):
        objs = []
        for rec_name, spec in parts:
            for it in _filter_items(records_by_name[rec_name]["items"], spec):
                record_items_consumed[rec_name].add(it["name"])
                objs.append(it)
        primary = parts[0][0]
        forms.append({"num": idx, "label": label,
                      "group_sym": _group_symbol(primary, used_group_syms),
                      "form_item_names": [it["name"] for it in objs],
                      "group_item_objs": objs,
                      "roster": _roster_info(primary)})

    lines = []
    lines.append("[FormFile]")
    lines.append("Version=CSPro 8.0")
    lines.append(f"Name={FF_NAME}")
    lines.append(f"Label={DICT_LABEL}")
    lines.append(DEFAULT_FONT)
    lines.append(ENTRY_FONT)
    lines.append("Type=SystemControlled")
    lines.append("  ")
    lines.append("[Dictionaries]")
    lines.append(f"File={DCF_REL_PATH}")
    lines.append("  ")

    for f in forms:
        _emit_form(lines, f["num"], f["label"], f["form_item_names"],
                   _form_height(len(f["group_item_objs"])), roster=f["roster"])

    lines.append("[Level]")
    lines.append(f"Name={level_name}")
    lines.append(f"Label={DICT_LABEL} Level")
    lines.append("  ")
    for f in forms:
        _emit_group(lines, f["group_sym"], f["label"], f["num"] + 1,
                    f["group_item_objs"], dict_name, roster=f["roster"])

    orphans = []
    for rec_name, rec in records_by_name.items():
        if rec["recordType"] == "1":
            continue
        placed = record_items_consumed[rec_name]
        for it in rec["items"]:
            if it["name"] not in placed:
                orphans.append(f"{rec_name}.{it['name']}")
    if orphans:
        sys.stderr.write(f"WARNING: {len(orphans)} items not placed on any form:\n")
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
