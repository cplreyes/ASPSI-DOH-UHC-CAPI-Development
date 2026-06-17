"""
generate_fmf.py - F4 Household Survey CSPro Form File generator.

Emits HouseholdSurvey.generated.fmf - a COMPLETE, bindable CSPro 8.0 form file for
HouseholdSurvey.dcf. Mirrors the form plan in F4-Form-Layout-Plan.md
(FIELD_CONTROL -> Geo+GPS -> sections A-Q -> closing -> verification photo).

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
APC_PATH = Path(__file__).resolve().parent / "HouseholdSurvey.ent.apc"

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


# Case-start metadata form removed 2026-06-12 — all its items (interviewer ID,
# timestamps, AAPOR, consent, HH listing) deleted; LANGUAGE_USED is off-form
# (set in the QUESTIONNAIRE_NUMBER postproc). The FORM_PLAN no longer emits it.
FIELD_CONTROL_CASE_END = {
    "SURVEY_TEAM_LEADER_S_NAME", "ENUMERATOR_S_NAME",
    "FIELD_VALIDATED_BY", "FIELD_EDITED_BY",
    "DATE_FIRST_VISITED", "DATE_FINAL_VISIT", "TOTAL_NUMBER_OF_VISITS",
    "ENUM_RESULT_FIRST_VISIT", "ENUM_RESULT_FINAL_VISIT",
}


FORM_PLAN = [
    ("FC Geographic ID + HH GPS Capture",
     # Single-number redesign (2026-06-11): household region/province/city are
     # derived from QUESTIONNAIRE_NUMBER (off-form); show the read-only PSGC
     # names + keep the barangay picker.
     [("FIELD_CONTROL", {"names": ["REGION_NAME", "PROVINCE_NAME", "CITY_NAME"]}),
      ("HOUSEHOLD_GEO_ID", {"exclude": ["REGION", "PROVINCE_HUC", "CITY_MUNICIPALITY"]})]),
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
    # Verification photo moved to the very end (2026-06-12): the enumerator
    # photographs the completed visit, and the survey no longer opens with a
    # camera prompt. HH GPS stays early so it auto-locks while the form is worked.
    ("Case Verification Photo",
     [("REC_CASE_VERIFICATION", None)]),
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
        if it["name"] in _CHECKBOX_FIELDS:   # alpha + value set rendered as a tick-list (#529)
            capture = "CheckBox"
            field_x2 = FIELD_RADIO_X2
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
    if not roster:
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

# UI/UX combined-views (2026-06-12, "moderate" density) — same auto-deriver as F3.
# Admin uses NAMED_BLOCKS; geo / GPS / photo and the repeating C_HOUSEHOLD_ROSTER
# (emitted as a roster, never blocked) are NOT auto-grouped.
_NO_AUTOGROUP_RECORDS = {
    "FIELD_CONTROL", "HOUSEHOLD_GEO_ID", "REC_CASE_VERIFICATION", "C_HOUSEHOLD_ROSTER",
}
_MULTISELECT_RE = re.compile(r"^(.+?)_O\d+$")
# Single alpha fields rendered as a CSPro Check Box (one-question multi-select tick-list).
# These get DataCaptureType=CheckBox and their own DisplayTogether screen (with any trailing
# gated _OTHER_TXT free-text on its own screen). 2026-06-16 (#529): the 17 'Household Survey'
# select_all -> Check Box conversions (mirrors F3's _CHECKBOX_FIELDS / F1 Q49/Q50/Q53/Q58).
_CHECKBOX_FIELDS = {
    "Q52_UHC_SOURCE", "Q53_UHC_UNDERSTAND", "Q55_YAKAP_SOURCE", "Q56_YAKAP_UNDERSTAND",
    "Q58_BUCAS_SOURCE", "Q59_BUCAS_UNDERSTAND", "Q61_BUCAS_SERVICES",
    "Q65_CONDITIONS", "Q66_WHERE_BUY", "Q85_BENEFITS", "Q91_WHY_WENT",
    "Q93_WHY_NOT", "Q94_TRANSPORT", "Q113_WHY_NOT", "Q121_WHY_HOSPITAL",
    "Q127_NBB_SOURCE", "Q128_NBB_UNDERSTAND", "Q133_ZBB_SOURCE", "Q134_ZBB_UNDERSTAND",
    "Q137_MAIFIP_SOURCE",
    "Q70_GAMOT_SOURCE", "Q71_GAMOT_UNDERSTAND",   # #573/#574
    # #577-585/#588/#590-591: 10 more select_all -> Check Box (tick-all-that-apply)
    "Q74_WHERE_REST", "Q77_WHY_GENERIC", "Q78_WHY_BRANDED", "Q82_DIFFICULTY_REASONS",
    "Q88_DIFF_PAYING", "Q102_VISIT_REASON", "Q103_CARE_TYPE", "Q106_FORGONE_WHY",
    "Q107_OTHER_ACTIONS", "Q109_TYPE",
    "Q141_BILL_ITEMS", "Q143_HOW_PAID",   # #615/#616 Section M bill
}
MAX_CHUNK = 5
_RUN_BLOCK_CAP = 22     # a real multi-select up to ~22 options is one checklist screen;
                        # an amount matrix (run has _AMT siblings) or a longer run is chunked.
_ACTIVE_BLOCK_PLAN = []


def _qnum(item):
    lab = (item.get("labels") or [{}])[0].get("text", "") or ""
    m = re.match(r"\s*(\d+)", lab) or re.match(r"Q(\d+)", item["name"])
    return m.group(1) if m else None


def _chunk_label(item_objs):
    qs = [q for q in (_qnum(it) for it in item_objs) if q]
    if not qs:
        return "Questions"
    return f"Q{qs[0]}" if qs[0] == qs[-1] else f"Q{qs[0]}-Q{qs[-1]}"


def parse_apc():
    """-> (skip_sources, skip_targets, noinput_gated) from the generated .ent.apc.

    Mirrors F1/inject_blocks.py parse_apc (the reference fix for UAT R4 GH #371/#375).
    On a DisplayTogether screen CSEntry renders EVERY member field regardless of skip /
    noinput logic, so a skip SOURCE (a field whose PROC does 'skip to') must END its
    screen and a skip TARGET ('skip to <FIELD>') must START a fresh screen. We also
    collect PROCs carrying a preproc 'noinput' gate so _is_gated_text can isolate them
    authoritatively (suffix match alone misses non-_TXT/_SPECIFY gated fields)."""
    if not APC_PATH.exists():
        # Defensive: if the .apc has not been regenerated yet, fall back to the
        # suffix-only gating (the orchestrator runs generate_apc.py BEFORE this,
        # so in the normal pipeline the file is always present).
        sys.stderr.write(f"WARNING: {APC_PATH.name} not found — skip-aware screen "
                         f"breaks DISABLED (suffix-only gating)\n")
        return set(), set(), set()
    txt = APC_PATH.read_text(encoding="utf-8-sig")
    txt = re.sub(r"\{[^{}]*\}", " ", txt)              # strip CSPro {…} comments
    sources, targets, gated = set(), set(), set()
    # procs = [preamble, name1, body1, name2, body2, ...]
    procs = re.split(r"(?m)^PROC\s+([A-Z0-9_]+)\s*$", txt)
    for name, body in zip(procs[1::2], procs[2::2]):
        if re.search(r"\bskip\s+to\b", body):
            sources.add(name)
        if re.search(r"\bnoinput\b", body):
            gated.add(name)
    # 'skip to next' / 'skip to <field>' — only uppercase-starting tokens are dict
    # fields; the CSPro keyword 'next' is lowercase and correctly NOT captured.
    targets.update(re.findall(r"\bskip\s+to\s+([A-Z0-9_]+)", txt))
    return sources, targets, gated


def _is_gated_text(name, noinput_gated=frozenset()):
    """Other-specify / specify free-text fields carry a preproc 'noinput' gate (they show
    only when their trigger option is chosen). They MUST sit on their OWN screen — on a
    combined DisplayTogether screen EVERY member field renders regardless of the gate, so
    the specify box would always appear (R4 on-device bug, 2026-06-12). Catches *_OTHER_TXT,
    *_SPECIFY, etc.; the .apc 'noinput' scan (noinput_gated, F1-parity) is authoritative for
    any gated field the suffix check would miss. NOTE: *_AMT (amount-matrix) fields are NOT
    gated text — they stay in the multi-select run so the matrix chunking below still applies."""
    return name.endswith("_TXT") or name.endswith("_SPECIFY") or name in noinput_gated


def derive_block_plan(dictionary, sources=frozenset(), targets=frozenset(), gated=frozenset()):
    """Auto DisplayTogether blocks for the survey body (moderate density). Each clean
    multi-select option set -> one screen; amount matrices (run has _AMT) and longer
    runs -> chunked at MAX_CHUNK; gated specify-text fields -> their OWN screen so the
    noinput gate hides them when not applicable; other consecutive questions -> chunked.
    Skip-awareness (sources/targets from the .apc, F1 GH #371/#375 fix) applies ONLY in
    the simple-question chunk loop: a skip TARGET starts a fresh screen, a skip SOURCE
    ends its screen — so a gated field can never share a DisplayTogether screen with the
    field it skips over / into. Every on-form field of a processed record lands in one
    contiguous block (Position=start+emitted)."""
    plan = []
    counter = [0]

    def emit(item_objs, label=None):
        plan.append((f"DG_BLK_{counter[0]}", label or _chunk_label(item_objs),
                     [it["name"] for it in item_objs]))
        counter[0] += 1

    for rec in dictionary["levels"][0]["records"]:
        if rec["name"] in _NO_AUTOGROUP_RECORDS:
            continue
        items = rec["items"]
        i = 0
        while i < len(items):
            nm = items[i]["name"]
            if nm.endswith("_SUBTOTAL_TOTAL_PHP"):
                # #617 (Critical): a protect()ed computed subtotal (Q157/Q177/Q182/Q185) must
                # NOT sit in a DisplayTogether block. In a DG block CSEntry only lets you focus
                # ENTERABLE fields, so a protected member is never visited -> its compute preproc
                # never runs -> it stays notappl -> CSEntry hard-errors "out of range - value is
                # NOTAPPL" on block exit, blocking the whole interview at Q157. A 1-field DG block
                # whose only field is protected has nothing enterable either, so own-screen-as-DG
                # does not help. Leave it UNBLOCKED -> it renders as a standalone linear [Field];
                # CSPro's normal field flow DOES pass through protected fields (runs preproc, shows
                # the value read-only, auto-advances), so the total is computed before its range is
                # validated. The chunk-break below keeps neighbours off the same screen as it.
                i += 1
                continue
            ms = _MULTISELECT_RE.match(nm)
            if _is_gated_text(nm, gated) or nm in _CHECKBOX_FIELDS:
                # gated specify text / Check Box (#529) -> its OWN screen so the noinput gate
                # hides it when not applicable.
                emit([items[i]], (_qnum(items[i]) and f"Q{_qnum(items[i])}") or nm)
                i += 1
            elif ms and not nm.endswith("_TXT"):              # multi-select OPTION run (matrix-aware)
                base = ms.group(1)                             # gated _OTHER_TXT is excluded here and
                run = []                                       # picked up by the gated-text branch above
                while i < len(items) and items[i]["name"].startswith(base + "_O") \
                        and not _is_gated_text(items[i]["name"], gated):
                    run.append(items[i]); i += 1
                is_matrix = any(it["name"].endswith("_AMT") for it in run)
                if not is_matrix and len(run) <= _RUN_BLOCK_CAP:
                    emit(run, (_qnum(run[0]) and f"Q{_qnum(run[0])}"))
                else:                                          # amount matrix / huge run -> chunk
                    for j in range(0, len(run), MAX_CHUNK):
                        emit(run[j:j + MAX_CHUNK])
            else:                                              # chunk of simple questions
                chunk = []
                while i < len(items) and len(chunk) < MAX_CHUNK:
                    nn = items[i]["name"]
                    mm = _MULTISELECT_RE.match(nn)
                    if (mm and not nn.endswith("_TXT")) or nn in _CHECKBOX_FIELDS or _is_gated_text(nn, gated) \
                            or nn.endswith("_SUBTOTAL_TOTAL_PHP"):
                        break                                  # stop before multi-select / checkbox (#529) / gated text / #617 subtotal
                    if chunk and nn in targets:
                        break                                  # skip TARGET starts a fresh screen
                    chunk.append(items[i]); i += 1
                    if nn in sources:
                        break                                  # skip SOURCE ends its screen
                emit(chunk)
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
    dictionary = build_f4_dictionary()
    _truncate_long_labels(dictionary)  # match the .dcf's 255-char label cap (CSPro max)
    global _ACTIVE_BLOCK_PLAN
    # Skip-awareness reads the CURRENT .ent.apc — the orchestrator (cspro_compile_driver.py
    # build_instrument) runs generate_apc.py BEFORE generate_fmf.py, so the .apc on disk is
    # in lock-step with the .dcf the plan is derived from (see GENERATION ORDER note).
    skip_sources, skip_targets, noinput_gated = parse_apc()
    _ACTIVE_BLOCK_PLAN = NAMED_BLOCKS + derive_block_plan(
        dictionary, skip_sources, skip_targets, noinput_gated)
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
