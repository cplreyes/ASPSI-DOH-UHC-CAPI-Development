"""
generate_fmf.py - F3 Patient Survey CSPro Form File generator.

Emits PatientSurvey.generated.fmf - a COMPLETE, bindable CSPro 8.0 form file for
PatientSurvey.dcf. Mirrors the 32-form plan in F3-Form-Layout-Plan.md
(FIELD_CONTROL -> Geo -> capture triggers -> sections A-L -> closing).

FULL-STRUCTURE generation (2026-06-08): in addition to the visual [Form] blocks
(item membership + tab order), this now emits the logical structure CSPro requires
to open the file as a bound application without stripping items:
  [Level] -> one [Group] per form (Form=N, Max=1) -> [Field] + [Text] per item.
Auto-layout mirrors the working F1 .fmf: label at x=50, field at x=350, rows every
30px; DataCaptureType=RadioButton for value-set (coded) items, TextBox otherwise
(UseUnicodeTextBox=Yes for alpha). The id-items form and the level-1 container form
are emitted as EMPTY groups (exactly as F1 does) -- id items live in the dict id block.

This makes the file open + compile in Designer with no [Level]/[Group] warnings,
so the compile can be driven headlessly. Visual polish (split oversized sections,
capture-trigger buttons, roster grids) remains optional Designer refinement.

Run:
    python generate_fmf.py        # writes PatientSurvey.generated.fmf next to this file
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate_dcf import build_f3_dictionary
from cspro_helpers import _truncate_long_labels


DICT_LABEL = "PatientSurvey"
FF_NAME = "PATIENTSURVEY_FF"
DCF_REL_PATH = r".\PatientSurvey.dcf"
# Generated CAPI logic — read for skip sources/targets + noinput gates so the
# combined-view block plan never shares a DisplayTogether screen across a skip
# boundary (R4 bug class GH #371/#375; fix ported from F1 inject_blocks.py).
# The canonical build (cspro_compile_driver.build_instrument) runs generate_apc.py
# BEFORE generate_fmf.py, so this file is current when read here.
APC_PATH = Path(__file__).resolve().parent / "PatientSurvey.ent.apc"

DEFAULT_FONT = (
    "DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Arial"
)
ENTRY_FONT = (
    "FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Courier New"
)

# --- Auto-layout geometry (mirrors the working F1 .fmf) ---
ROW_H = 30          # vertical pitch between fields
TOP_Y = 27          # first field's top
LABEL_X = 50
LABEL_X2 = 330
FIELD_X = 350
FIELD_TEXTBOX_X2 = 760
FIELD_RADIO_X2 = 365   # radio fields are narrow; options expand below
FIELD_H = 20
TEXT_H = 16
FORM_W = 806


# Case-start form: just PATIENT_TYPE now (the OP/IP routing gate, entered before
# Sections G/H). All other case-start metadata removed 2026-06-12; LANGUAGE_USED
# is off-form (set in the QUESTIONNAIRE_NUMBER postproc).
FIELD_CONTROL_CASE_START = {
    "PATIENT_TYPE",
}
FIELD_CONTROL_CASE_END = {
    "SURVEY_TEAM_LEADER_S_NAME", "ENUMERATOR_S_NAME",
    "FIELD_VALIDATED_BY", "FIELD_EDITED_BY",
    "DATE_FIRST_VISITED", "DATE_FINAL_VISIT", "TOTAL_NUMBER_OF_VISITS",
    "ENUM_RESULT_FIRST_VISIT", "ENUM_RESULT_FINAL_VISIT",
}


FORM_PLAN = [
    ("Patient Type (Outpatient / Inpatient)",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_START})]),
    ("FC Geographic ID + F1 linkage",
     # Single-number redesign (2026-06-11): facility region/province/city are
     # derived from QUESTIONNAIRE_NUMBER (off-form); show the read-only PSGC
     # names + keep the barangay picker. Patient-home P_* cascade stays manual.
     [("FIELD_CONTROL", {"names": ["REGION_NAME", "PROVINCE_NAME", "CITY_NAME"]}),
      ("PATIENT_GEO_ID", {"exclude": ["REGION", "PROVINCE_HUC", "CITY_MUNICIPALITY"]})]),
    ("FC Facility GPS Capture",
     [("REC_FACILITY_CAPTURE", None)]),
    ("FC Patient Home GPS",
     [("REC_PATIENT_HOME_CAPTURE", None)]),
    ("A. Informed Consent (Q1 gate)",
     [("A_INFORMED_CONSENT", None)]),
    ("B. Patient Profile",
     [("B_PATIENT_PROFILE", None)]),
    ("C. UHC Awareness",
     [("C_UHC_AWARENESS", None)]),
    ("D. PhilHealth Registration",
     [("D_PHILHEALTH_REG", None)]),
    ("E. Primary Care + YAKAP/Konsulta",
     [("E_PRIMARY_CARE", None)]),
    ("F. Health-Seeking",
     [("F_HEALTH_SEEKING", None)]),
    ("G. Outpatient Care",
     [("G_OUTPATIENT_CARE", None)]),
    # Option B (pilot): the Q92 payment roster renders as its own grid form between the
    # Q92_SOURCES tick-list (end of G) and Q93 (start of G-cont).
    ("G. Cost of consultation — amount by source",
     [("Q92_PAY_ROSTER", None)]),
    ("G. Outpatient Care (cont.)",
     [("G_OUTPATIENT_CARE_2", None)]),
    ("H. Inpatient Care",
     [("H_INPATIENT_CARE", None)]),
    ("I. Financial Risk",
     [("I_FINANCIAL_RISK", None)]),
    ("J. Satisfaction",
     [("J_SATISFACTION", None)]),
    ("K. Access to Medicines",
     [("K_ACCESS_MEDICINES", None)]),
    ("L. Referrals",
     [("L_REFERRALS", None)]),
    ("Closing - case end",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_END})]),
    # Verification photo moved to the very end (2026-06-12): the enumerator
    # photographs the completed visit, and the survey no longer opens with a
    # camera prompt. GPS stays early so it auto-locks while the form is worked.
    ("Case Verification Photo",
     [("REC_CASE_VERIFICATION", None)]),
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


def _group_symbol(primary_record, used):
    """A unique, valid CSPro symbol for a form's [Group]; '_FORM' suffix avoids
    colliding with the dictionary record of the same name (F1 convention)."""
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
        # Mark the form as repeating over the roster record (ported from F4 2026-06-18).
        # Without this Repeat= line CSEntry rejects the forms<->dictionary reconcile
        # ("open in Designer, make changes, save"); the [Group] Type=Record alone is
        # not enough. Verified on F4 against the Designer-reconciled FMF.
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
    lines.append("Required=Yes")
    lines.append(f"Name={group_sym}")
    lines.append(f"Label={label}")
    lines.append(f"Form={form_one_based}")
    if roster:
        # Repeating roster group (ported from F4): Type=Record + TypeName + Max=<occ>
        # makes Designer/CSEntry render the record's fields as a grid (one row/occurrence).
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
        if it["name"] in _CHECKBOX_FIELDS:   # alpha + value set rendered as a tick-list
            capture = "CheckBox"
            field_x2 = FIELD_RADIO_X2
        text = (it["labels"][0]["text"] if it.get("labels") else it["name"]).replace("\n", " ").replace("\r", " ")
        # [Field]
        lines.append("[Field]")
        lines.append(f"Name={it['name']}")
        lines.append(f"Position={FIELD_X},{y},{field_x2},{y + FIELD_H}")
        lines.append(f"Item={it['name']},{dict_name}")
        if not coded and is_alpha:
            lines.append("UseUnicodeTextBox=Yes")
        lines.append(f"DataCaptureType={capture}")
        lines.append(f"Form={form_one_based}")
        lines.append("  ")
        # [Text] — single-language (EN) field label. CSPro does NOT auto-translate the
        # form label from the dict; per-language prompts live in the question text (.qsf).
        lines.append("[Text]")
        lines.append(f"Position={LABEL_X},{y + 3},{LABEL_X2},{y + 3 + TEXT_H}")
        lines.append(f"Text={text}")
        lines.append(" ")
        lines.append("  ")
    if not roster:   # rosters render as a grid; never auto-blocked into DisplayTogether
        _emit_blocks(lines, item_objs)
    lines.append("[EndGroup]")
    lines.append("  ")


# Blocks — Designer-verified grammar (learned from a Designer-authored save on F1
# 2026-06-11; hand-rolled blocks with wrong Position silently CRASH Designer on open):
# [Block] sections go at the END of the [Group], before [EndGroup]. Position indexes
# the group's item sequence in which each earlier block ALSO occupies one slot
# (so block 2 after a 4-field block 1 starts at 0+1+4=5, not 4). DisplayTogether=Yes
# is what combines the fields onto one screen in Android CSEntry (phone + tablet).
# Named blocks for the admin Field-Control fields (kept verbatim — Designer-verified).
NAMED_BLOCKS = [
    ("INTERVIEW_STAFF_BLOCK", "Interview Staff",
     ["SURVEY_TEAM_LEADER_S_NAME", "ENUMERATOR_S_NAME",
      "FIELD_VALIDATED_BY", "FIELD_EDITED_BY"]),
    ("VISIT_RECORD_BLOCK", "Visit Record",
     ["DATE_FIRST_VISITED", "DATE_FINAL_VISIT", "TOTAL_NUMBER_OF_VISITS",
      "ENUM_RESULT_FIRST_VISIT", "ENUM_RESULT_FINAL_VISIT"]),
]

# UI/UX combined-views (2026-06-12, "moderate" density): auto-group the survey body
# into DisplayTogether screens so related questions render together instead of one-
# field-per-screen. Records below keep their special single-screen handling and are
# NOT auto-grouped (admin uses NAMED_BLOCKS; geo cascade / GPS / photo stay as-is).
_NO_AUTOGROUP_RECORDS = {
    "FIELD_CONTROL", "PATIENT_GEO_ID",
    "REC_FACILITY_CAPTURE", "REC_PATIENT_HOME_CAPTURE", "REC_CASE_VERIFICATION",
    "Q92_PAY_ROSTER",   # Option B (pilot): emitted as a roster grid, never auto-blocked
}
_MULTISELECT_RE = re.compile(r"^(.+?)_O\d+$")
# Single alpha fields rendered as a CSPro Check Box (one-question multi-select tick-list).
# These get DataCaptureType=CheckBox and their own DisplayTogether screen (with any trailing
# _OTHER_TXT / _MEDICINES_TXT gated free-text). 2026-06-12 R4 review: Q148. 2026-06-16 (#529):
# the 13 'Patient Survey' select_all -> Check Box conversions (mirrors F1 Q49/Q50/Q53/Q58).
_CHECKBOX_FIELDS = {
    "Q148_CONDITIONS",
    "Q36_UHC_SOURCE", "Q37_UHC_UNDERSTAND", "Q46_BENEFITS", "Q65_WHY_NO_USUAL",
    "Q67_WHY_THIS_FACILITY", "Q76_KON_UNDERSTAND", "Q101_BUCAS_UNDERSTAND",
    "Q117_NBB_SOURCE", "Q118_NBB_UNDERSTAND", "Q120_ZBB_SOURCE", "Q121_ZBB_UNDERSTAND",
    "Q171_WHY_NOT", "Q177_WHY_HOSPITAL", "Q125_MAIFIP_SOURCE",   # #560
    # #635/#639/#640 Section D select_all -> Check Box (Q42/Q50/Q52 were converted in
    # generate_dcf/apc but never added to a fmf checkbox list, so optimize_capture_types
    # was demoting them to single-select DropDown — a multi-select data-loss regression).
    "Q42_DIFFICULTY", "Q50_DIFFICULTY_PAYING", "Q52_PLANS",
    # #669/#670/#671/#673 Section E/F/G select_all -> Check Box (tick-all).
    "Q59_SCHED_COMM", "Q61_CONSULT_COMM", "Q70_USUAL_TRANSPORT", "Q73_NEAREST_TRANSPORT",
    "Q75_KON_SOURCE", "Q82_KON_WHY_NOT_REG", "Q85_CONDITIONS", "Q86_VISIT_EVENTS",
    "Q87_OTHER_ACTIONS", "Q90_NOT_CONFINED", "Q93_LABS",
    # #690/#694 Section G/H select_all -> Check Box (tick-all).
    "Q100_BUCAS_SOURCE", "Q103_BUCAS_SERVICES", "Q114_NO_PH",
    # #696 Section K/L select_all -> Check Box (tick-all).
    "Q149_WHERE_BUY", "Q153_GAMOT_SOURCE", "Q154_GAMOT_UNDERSTAND", "Q157_WHERE_REST",
    "Q160_WHY_GENERIC", "Q161_WHY_BRANDED", "Q163_CARE_TYPE",
    # #481 Section I select_all -> Check Box (+ None/Other).
    "Q128_MAIFIP_OOP_ITEMS",
    # #700 Section I MAIFIP why-not-avail select_all -> Check Box.
    "Q129_WHY_NO_MAIFIP",
    # Option B (pilot): the Q92 payment-source tick-list that drives the Q92_PAY_ROSTER.
    "Q92_SOURCES",
}
_CHECKBOX_TRAILERS = ("_OTHER_TXT", "_MEDICINES_TXT")  # gated texts that share the checkbox screen
MAX_CHUNK = 5                       # cap simple-question runs at ~5 per screen
_ACTIVE_BLOCK_PLAN = []            # set per-build by build_fmf()


def _qnum(item):
    lab = (item.get("labels") or [{}])[0].get("text", "") or ""
    m = re.match(r"\s*(\d+)", lab) or re.match(r"Q(\d+)", item["name"])
    return m.group(1) if m else None


def _chunk_label(item_objs):
    qs = [q for q in (_qnum(it) for it in item_objs) if q]
    if not qs:
        return "Questions"
    return f"Q{qs[0]}" if qs[0] == qs[-1] else f"Q{qs[0]}-Q{qs[-1]}"


def _is_gated_text(name, noinput_gated=frozenset()):
    """Other-specify / specify free-text fields carry a preproc 'noinput' gate (they show
    only when their trigger option is chosen). They MUST sit on their OWN screen — on a
    combined DisplayTogether screen every member field renders regardless of the gate, so
    the specify box would always appear (R4 on-device bug, 2026-06-12). Catches *_OTHER_TXT,
    *_DONATION_TXT, *_SPECIFY, the Q148 medicines text, etc. Non-gated free-texts that also
    match are harmlessly isolated onto their own screen.

    `noinput_gated` (from parse_apc) is the F1-parity authority: any field whose .apc PROC
    carries a `noinput` gate is isolated too, even when its name lacks the _TXT/_SPECIFY
    suffix — so a renamed/non-suffixed gated field can't slip onto a shared screen."""
    return name.endswith("_TXT") or name.endswith("_SPECIFY") or name in noinput_gated


def parse_apc():
    """-> (skip_sources, skip_targets, noinput_gated) from the generated .ent.apc.

    Mirrors F1 inject_blocks.parse_apc: strip {...} comments, split on `^PROC <NAME>$`,
    collect PROCs that `skip to` (sources) and that carry `noinput` (gated), plus every
    `skip to <TARGET>` field name (targets). Returns empty sets if the .apc is absent
    (e.g. a bare `python generate_fmf.py` before the apc exists) — the plan then degrades
    to the pre-skip-aware chunking rather than crashing; the canonical build always
    regenerates the apc first (cspro_compile_driver.build_instrument)."""
    if not APC_PATH.exists():
        return set(), set(), set()
    txt = APC_PATH.read_text(encoding="utf-8")
    txt = re.sub(r"\{[^{}]*\}", " ", txt)          # strip CSPro comments
    sources, targets, gated = set(), set(), set()
    procs = re.split(r"(?m)^PROC\s+([A-Z0-9_]+)\s*$", txt)
    # procs = [preamble, name1, body1, name2, body2, ...]
    for name, body in zip(procs[1::2], procs[2::2]):
        if re.search(r"\bskip\s+to\b", body):
            sources.add(name)
        if re.search(r"\bnoinput\b", body):
            gated.add(name)
    targets.update(re.findall(r"\bskip\s+to\s+([A-Z0-9_]+)", txt))
    return sources, targets, gated


def derive_block_plan(dictionary, sources=frozenset(), targets=frozenset(),
                      gated=frozenset()):
    """Auto DisplayTogether blocks for the survey body (moderate density). Each
    multi-select option set -> one screen; other consecutive questions chunked at
    MAX_CHUNK per screen. Every on-form field of a processed record lands in exactly
    one block (contiguous, no gaps) so _emit_blocks' Position=start+emitted holds.

    Skip-awareness (ported from F1 inject_blocks.derive_plan, R4 GH #371/#375): in the
    SIMPLE-question chunk loop, a `skip to` TARGET STARTS a new screen (nothing skipped
    over may already render on the target's screen) and a `skip to` SOURCE ENDS its
    screen (nothing it can skip over may share the screen). Multi-select runs and
    Check Box fields keep their own dedicated screens unchanged."""
    plan, n = [], 0
    for rec in dictionary["levels"][0]["records"]:
        if rec["name"] in _NO_AUTOGROUP_RECORDS:
            continue
        items = rec["items"]
        i = 0
        while i < len(items):
            nm = items[i]["name"]
            ms = _MULTISELECT_RE.match(nm)
            if _is_gated_text(nm, gated) or nm in _CHECKBOX_FIELDS:   # gated specify text / Check Box -> OWN screen
                plan.append((f"DG_BLK_{n}", (_qnum(items[i]) and f"Q{_qnum(items[i])}") or nm, [nm])); n += 1; i += 1
            elif ms:                                       # multi-select OPTION run -> one screen
                base = ms.group(1)                          # (its trailing _OTHER_TXT is gated -> caught by
                run = []                                    #  the gated-text branch above, on its own screen)
                while i < len(items):
                    m2 = _MULTISELECT_RE.match(items[i]["name"])
                    if m2 and m2.group(1) == base:
                        run.append(items[i]); i += 1
                    else:
                        break
                label = (_qnum(run[0]) and f"Q{_qnum(run[0])}") or _chunk_label(run)
                plan.append((f"DG_BLK_{n}", label, [it["name"] for it in run])); n += 1
            else:                                          # chunk of up to MAX simple questions
                chunk = []
                while i < len(items) and len(chunk) < MAX_CHUNK:
                    nn = items[i]["name"]
                    if _MULTISELECT_RE.match(nn) or nn in _CHECKBOX_FIELDS or _is_gated_text(nn, gated):
                        break                               # stop before multi-select / checkbox / gated text
                    if chunk and nn in targets:
                        break                               # skip TARGET starts a new screen
                    chunk.append(items[i]); i += 1
                    if nn in sources:
                        break                               # skip SOURCE ends its screen
                plan.append((f"DG_BLK_{n}", _chunk_label(chunk), [it["name"] for it in chunk])); n += 1
    return plan


def _emit_blocks(lines, item_objs):
    names = [it["name"] for it in item_objs]
    emitted = 0
    for bname, blabel, fields in _ACTIVE_BLOCK_PLAN:
        if not all(f in names for f in fields):
            continue
        start = names.index(fields[0])
        if names[start:start + len(fields)] != fields:   # must be a consecutive run
            continue
        lines.append("[Block]")
        lines.append(f"Name={bname}")
        lines.append(f"Label={blabel}")
        lines.append("DisplayTogether=Yes")
        lines.append(f"Position={start + emitted}")
        lines.append(f"Length={len(fields)}")
        lines.append("  ")
        emitted += 1


def build_fmf():
    dictionary = build_f3_dictionary()
    _truncate_long_labels(dictionary)  # match the .dcf's 255-char label cap (CSPro max)
    global _ACTIVE_BLOCK_PLAN
    sources, targets, gated = parse_apc()
    _ACTIVE_BLOCK_PLAN = NAMED_BLOCKS + derive_block_plan(dictionary, sources, targets, gated)
    dict_name = dictionary.get("name", "PATIENTSURVEY_DICT")
    level = dictionary["levels"][0]
    level_name = level.get("name", "PATIENTSURVEY_LEVEL")
    records_by_name = {r["name"]: r for r in level["records"]}
    id_item_names = [it["name"] for it in level["ids"]["items"]]

    def _roster_info(record_name):
        """A repeating record (occurrences.maximum > 1) -> roster grid; else None."""
        occ = records_by_name[record_name].get("occurrences") or {}
        mx = occ.get("maximum", 1) if isinstance(occ, dict) else 1
        return {"type_name": record_name, "max": mx} if (mx and mx > 1) else None

    referenced = {rec for _, parts in FORM_PLAN for rec, _ in parts}
    missing = referenced - set(records_by_name)
    if missing:
        raise RuntimeError(f"FORM_PLAN references missing records: {sorted(missing)}")

    record_items_consumed = {name: set() for name in records_by_name}
    used_group_syms = set()

    # forms: list of dicts {num, label, group_sym, form_item_names, group_item_objs}
    forms = []
    # FORM000 - case-key ID items, entered FIRST (before consent) so a consent refusal
    # has a valid case key to save (desk-test F3-DT-02: an empty key -> "ID fields not
    # filled" at endlevel). CSPro DOES place id items on the first form as normal
    # [Field]s (cf. the CAPI Census "Geocodes" form GEOCODES_FORM); the earlier
    # "strip" note was a misdiagnosis. Enumerator types the codes from the sampling frame.
    id_objs = list(level["ids"]["items"])
    _ = id_item_names
    forms.append({"num": 0, "label": "Case Key (Facility + Patient ID)", "group_sym": "IDS0_FORM",
                  "form_item_names": [it["name"] for it in id_objs], "group_item_objs": id_objs,
                  "roster": None})
    used_group_syms.add("IDS0_FORM")
    # FORM001.. - planned forms. (The empty level-1 "container" record/form was
    # removed 2026-06-08 — it was a vestigial item-less record that CSEntry never
    # populated; suspected in the blank-case-key bug. Forms now run key=0, plan=1+.)
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

    # Visual [Form] blocks
    for f in forms:
        _emit_form(lines, f["num"], f["label"], f["form_item_names"],
                   _form_height(len(f["group_item_objs"])), roster=f["roster"])

    # Logical structure: one [Level], one [Group] per form
    lines.append("[Level]")
    lines.append(f"Name={level_name}")
    lines.append(f"Label={DICT_LABEL} Level")
    lines.append("  ")
    for f in forms:
        _emit_group(lines, f["group_sym"], f["label"], f["num"] + 1,
                    f["group_item_objs"], dict_name, roster=f["roster"])

    # Orphan check
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
    out_path = Path(__file__).parent / "PatientSurvey.generated.fmf"
    fmf_text, orphan_count = build_fmf()
    out_path.write_text(fmf_text, encoding="utf-8")
    sys.stderr.write(f"Wrote {out_path} ({orphan_count} orphan items)\n")


if __name__ == "__main__":
    main()
