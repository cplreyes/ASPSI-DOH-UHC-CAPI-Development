"""
generate_fmf.py - F1 Facility Head Survey CSPro Form File generator.

Emits FacilityHeadSurvey.generated.fmf - a COMPLETE, bindable CSPro 8.0 form file for
FacilityHeadSurvey.dcf. Ported from F3/generate_fmf.py (2026-08-19, Task 2.3 of the
Aug-17 migration), which retires the eleven hand-rolled inject_*.py post-processors F1
used while its .fmf was hand-maintained. Those scripts are kept in this folder with a
tombstone header - they are the written record of the form-order and block invariants
this file now owns.

WHY THE SWITCH (2026-08-19)
--------------------------
F1's .fmf was hand-authored and patched by post-processors that located fields by NAME
and geometry. The Aug-17 renumber (Task 2.2: 318 -> 320 items, ~112 items renamed)
invalidates nearly every Name=/Item= line those scripts anchor on, so every one of them
would either abort or silently mis-place a field. Generating the whole file from the
dictionary is the same move already proved on F3 and F4.

FULL-STRUCTURE generation: in addition to the visual [Form] blocks (item membership +
tab order), this emits the logical structure CSPro requires to open the file as a bound
application without stripping items:
  [Level] -> one [Group] per form (Form=N, Max=1) -> [Field] + [Text] per item.
Auto-layout: label at x=50, field at x=350, rows every 30px; DataCaptureType=RadioButton
for value-set (coded) items, TextBox otherwise (UseUnicodeTextBox=Yes for alpha). The
capture-type pass (automation/optimize_capture_types.py) runs after the build copies
.generated.fmf -> .fmf and promotes >=7-option fields to DropDown, dates to a picker,
and the multi-select bases to Check Box.

Form= IS A 1-BASED ORDINAL, not an id: the k-th [Group] in document order owns the k-th
[Form]. Every Form= here is computed from position, never patched by offset - the
off-by-one that inject_icf.py's docstring warns about breaks silently.

Run:
    python generate_fmf.py        # writes FacilityHeadSurvey.generated.fmf next to this file
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate_dcf import build_dictionary
from cspro_helpers import _truncate_long_labels, question_caption


DICT_LABEL = "FacilityHeadSurvey"
FF_NAME = "FACILITYHEADSURVEY_FF"
DCF_REL_PATH = r".\FacilityHeadSurvey.dcf"
# Generated CAPI logic - read for skip sources/targets + noinput gates so the combined-view
# block plan never shares a DisplayTogether screen across a skip boundary (R4 bug class
# GH #371/#372; the rule this file inherits from inject_blocks.py). The canonical build
# (cspro_compile_driver.build_instrument) runs generate_apc.py BEFORE generate_fmf.py, so
# this file is current when read here. When it is NOT current, _warn_if_apc_stale() says so
# loudly rather than letting the plan quietly lose its skip-awareness.
APC_PATH = Path(__file__).resolve().parent / "FacilityHeadSurvey.ent.apc"

DEFAULT_FONT = (
    "DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Arial"
)
ENTRY_FONT = (
    "FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Courier New"
)

# --- Auto-layout geometry (shared with F3/F4) ---
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


# The three FIELD_CONTROL items that ride the geographic form as read-only PSGC display
# names (the single-Questionnaire-Number redesign, 2026-06-10: REGION/PROVINCE_HUC/
# CITY_MUNICIPALITY are DERIVED in logic from the 12-digit key and stay off-form).
FIELD_CONTROL_GEO_NAMES = ["REGION_NAME", "PROVINCE_NAME", "CITY_NAME"]

# Closing "Field Control" form, in the order the hand-maintained .fmf shipped. This form
# was moved from the START of the instrument to the END by inject_field_control_end.py
# (#622, 2026-06-20): asking "Result of Visit" / visit dates before the interview happened
# was flagged illogical by the tester. It MUST stay immediately before the Verification
# Photo - the photo's preproc gates on ENUM_RESULT_FINAL_VISIT, so the result has to be
# entered before the camera fires. That adjacency is asserted in _assert_form_invariants().
FIELD_CONTROL_CASE_END = [
    "SURVEY_TEAM_LEADER_S_NAME", "ENUMERATOR_S_NAME",
    "FIELD_VALIDATED_BY", "FIELD_EDITED_BY",
    # #1099 added DATE_*_DISP echo fields here; #1132 removed them again at ASPSI's
    # request (four date rows for two dates read as confusing on-device). The dictionary
    # items are gone, so there is nothing to place - see the tombstones on
    # inject_date_display.py / remove_date_display.py.
    "DATE_FIRST_VISITED_THE_FACILITY", "DATE_OF_FINAL_VISIT_TO_THE_FACILITY",
    "TOTAL_NUMBER_OF_VISITS",
    "ENUM_RESULT_FIRST_VISIT", "ENUM_RESULT_FINAL_VISIT",
]

# REC_FACILITY_CAPTURE is deliberately SPLIT across two far-apart forms (it always was -
# inject_gps_end.py's "why a form move is safe" note depends on it): the GPS reading goes
# on the last form, the photo trigger on the second-to-last. Case data binds to dictionary
# items, not form positions, so the split costs nothing.
PHOTO_ITEMS = ["VERIFICATION_PHOTO_FILENAME", "CAPTURE_VERIFICATION_PHOTO"]
GPS_ITEMS = ["FACILITY_GPS_LATITUDE", "FACILITY_GPS_LONGITUDE", "FACILITY_GPS_ALTITUDE",
             "FACILITY_GPS_ACCURACY", "FACILITY_GPS_SATELLITES", "FACILITY_GPS_READTIME"]


# Each entry: (form label, [(record, filter_spec), ...], optional explicit group symbol).
FORM_PLAN = [
    # ICF SECOND, immediately after the case-key / Questionnaire-Number form (Aly,
    # 2026-08-14; inject_icf.py INSERT_AT=1). This SUPERSEDES Shan's 2026-08-13 "Suggested
    # Layout (CSEntry)", which put consent after the geographic form; F3 and F4 were moved
    # to the same slot in the same pass. Both are ASPSI - confirm with them before moving it.
    #
    # KNOWN AND ACCEPTED CONSEQUENCE: the geo form carries BREAKOFF, and PROC BREAKOFF does
    # `skip to ENUM_RESULT_FINAL_VISIT` for codes 5/6/7 (refused at door / not found /
    # ineligible), so with consent AHEAD of the break-off control the enumerator walks both
    # read-aloud consent screens before they can close out a case that never started. Carl
    # was shown a rendered comparison (deliverables/CSPro/decisions/2026-08-14-icf-placement.png)
    # and chose this over the variant that preserved the break-off escape. Do not revert
    # without asking ASPSI.
    ("Introduction and Informed Consent",
     [("A_INFORMED_CONSENT", None)], None),
    # Geographic form. Field order is CLASSIFICATION -> the three derived PSGC names ->
    # BARANGAY picker -> BREAKOFF, exactly as the hand-maintained file shipped, so the
    # record is referenced twice with `names` filters rather than once with `exclude`.
    # REGION / PROVINCE_HUC / CITY_MUNICIPALITY and FACILITY_NAME / FACILITY_ADDRESS are
    # off-form by design (derived in logic) - see _OFF_FORM_ITEMS.
    ("Health Facility and Geographic Identification",
     [("HEALTH_FACILITY_AND_GEOGRAPHIC_IDENTIFICATION", {"names": ["CLASSIFICATION"]}),
      ("FIELD_CONTROL", {"names": FIELD_CONTROL_GEO_NAMES}),
      ("HEALTH_FACILITY_AND_GEOGRAPHIC_IDENTIFICATION", {"names": ["BARANGAY"]}),
      # #744: the break-off control rides the geo form - the FIRST interactive form after
      # the case key. The enumerator can tap back to it from the case tree at any time.
      ("FIELD_CONTROL", {"names": ["BREAKOFF"]})], None),
    ("A. Facility Head Profile",
     [("A_FACILITY_HEAD_PROFILE", None)], None),
    ("B. Facility Profile",
     [("B_FACILITY_PROFILE", None)], None),
    ("C. Universal Health Care (UHC) Implementation",
     [("C_UHC_IMPLEMENTATION", None)], None),
    ("D. YAKAP/Konsulta Package",
     [("D_YAKAP_KONSULTA", None)], None),
    ("E. Awareness on Expanded Health Programs (BUCAS and GAMOT)",
     [("E_BUCAS_GAMOT", None)], None),
    ("F. DOH Licensing: Status and Barriers to Licensing",
     [("F_DOH_LICENSING", None)], None),
    ("G. Service Delivery Process",
     [("G_SERVICE_DELIVERY", None)], None),
    ("H. Human Resources for Health",
     [("H_HUMAN_RESOURCES", None)], None),
    ("Field Control",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_END})], None),
    # Verification photo second-to-last. VERIFICATION_PHOTO_IMAGE is a binary Image item
    # (off-form by rule - binary items can't be placed on a form); the on-form trigger
    # CAPTURE_VERIFICATION_PHOTO drives capture into it.
    ("Case Verification Photo",
     [("REC_FACILITY_CAPTURE", {"names": PHOTO_ITEMS})], "CASE_VERIFICATION_FORM"),
    # GPS DEAD LAST, after the photo (#157, pretest 2026-07-16). This deliberately reverses
    # the 2026-06-12 rule "GPS stays early so it auto-locks while the form is worked" -
    # indoors that assumption never held. gps(read) is SYNCHRONOUS, so an early form froze
    # the enumerator for up to 120s before consent and field teams reported they "cannot
    # proceed". Now nothing in the interview waits on a satellite fix: the enumerator
    # finishes, records the result, photographs the visit, walks out, and GPS acquires
    # outdoors. GPS has no gate of its own, so sitting after the photo is safe. Do NOT
    # re-add a "photo must be last" assertion.
    ("Facility GPS",
     [("REC_FACILITY_CAPTURE", {"names": GPS_ITEMS})], "REC_FACILITY_CAPTURE_FORM"),
]

# Computed / binary items deliberately kept OFF every form, so the orphan check below does
# not flag them. This set must stay a subset of automation/verify_questions.KNOWN_OFFFORM,
# which is the gate that enforces the same rule from the outside.
_OFF_FORM_ITEMS = {
    # Derived in the QUESTIONNAIRE_NUMBER postproc from the 12-digit case key.
    "REGION_CODE", "PROVINCE_HUC_CODE", "CITY_MUNICIPALITY_CODE", "FACILITY_NO", "CASE_SEQ",
    "REGION", "PROVINCE_HUC", "CITY_MUNICIPALITY",
    # Filled from the facility frame, never typed.
    "FACILITY_NAME", "FACILITY_ADDRESS",
    "LANGUAGE_USED",                # set in the QUESTIONNAIRE_NUMBER postproc
    "VERIFICATION_PHOTO_IMAGE",     # binary Image item - cannot be placed on a form (#713)
    "CASE_DISPOSITION",             # #561 completeness sentinel, read by the Supervisor App
}


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
    """A unique, valid CSPro symbol for a form's [Group]; '_FORM' suffix avoids colliding
    with the dictionary record of the same name (F1 convention, kept from the hand file)."""
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


# ------------------------------------------------------------------
# Pretest #1006 / DOH #888 - short ON-FORM labels for split components.
# ------------------------------------------------------------------
# Q5 and Q6 are each ONE question split into two dictionary items, and each item's label
# carries the FULL question stem. That label is consumed twice per screen (generate_qsf
# uses it as the CAPI question-bar prompt, the .fmf [Text] as the on-form field label), so
# the stem printed twice per screen and four times across the pair.
#
# Option A (chosen 2026-08-03, was inject_short_component_labels.py): shorten the ON-FORM
# label to the component name only and leave the full stem in the question bar above it.
# Option B (blocking each pair onto one DisplayTogether screen for Household parity) was
# considered and DECLINED mid-pretest - it changes Section A's entry flow and moves where
# the ">= 6 months tenure" termination check fires. Do not re-introduce it here by making
# the chunker question-aware without checking first.
#
# The DICTIONARY labels are deliberately left long - they are the variable labels in the
# exported data and the published codebook, and shortening them would leave Q5 and Q6 both
# carrying a bare "Number of Months" in the dataset. Display text and data labels diverge
# here on purpose.
#
# R25 (2026-08-19) GENERALISED THIS to every question field - cspro_helpers.question_caption
# now reduces each one to its numeral tag. What survives here is the narrower job this table
# always did: DISAMBIGUATING two items of ONE question that share a number AND a screen,
# where a bare "5." would print twice. The tag is prefixed automatically, so an entry reads
# "5. Number of Years" on device. Each entry is a MEASURED same-screen collision, found by
# deriving captions per DisplayTogether block - do not add one speculatively.
#
# A number repeated across SEPARATE screens needs no entry: only one renders per screen and
# the qsf pane discriminates.
SHORT_FORM_LABELS = {
    "Q5_YEARS_AT_FACILITY":  "Number of Years",
    "Q5_MONTHS_AT_FACILITY": "Number of Months",
    "Q6_YEARS_HEALTH":       "Number of Years",
    "Q6_MONTHS_HEALTH":      "Number of Months",
    # R25: the four remaining same-screen collisions in F1.
    "Q39_YK_SINCE_MONTH":       "Month",
    "Q39_YK_SINCE_YEAR":        "Year",
    # Each of these three is an exact free-numeric entry sitting beside its coded bracket
    # ("30 days and less" / "31-60 days" / "More than 60 days") on one screen.
    "Q49_TRANCHE_INTERVAL_NUM": "Number of days",
    "Q49_TRANCHE_INTERVAL":     "Days category",
    "Q50_ACCRED_WAIT_NUM":      "Number of days",
    "Q50_ACCRED_WAIT":          "Days category",
    "Q107_LIC_DAYS_NUM":        "Number of days",
    "Q107_LIC_DAYS":            "Days category",
}


def _emit_form(lines, form_num, label, item_names, height, roster=None):
    lines.append("[Form]")
    lines.append(f"Name=FORM{form_num:03d}")
    lines.append(f"Label={label}")
    lines.append("Level=1")
    if roster:
        # Mark the form as repeating over the roster record. Without this Repeat= line
        # CSEntry rejects the forms<->dictionary reconcile. F1 has no repeating record
        # today (verified: every record's occurrences.maximum == 1), so this path is
        # inert - it is kept for F3/F4 parity should a roster ever be added.
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
        # R25: the on-form caption is a NUMERAL TAG; the question itself lives only in the
        # qsf pane, which follows the language setting. cspro_helpers.question_caption owns
        # the rule for all three instruments.
        raw = (it["labels"][0]["text"] if it.get("labels") else it["name"])
        if roster:
            # Roster captions are GRID COLUMN HEADERS and stay out of R25's scope: a column
            # has no question pane of its own. F1 has no repeating record today, so this is
            # inert - it is kept in step with F3/F4 should a roster ever be added.
            text, kind = raw, "roster"
        else:
            text, kind = question_caption(it["name"], raw, SHORT_FORM_LABELS.get(it["name"]))
        _CAPTION_KINDS[kind] = _CAPTION_KINDS.get(kind, 0) + 1
        if kind == "keep-full":
            _KEEP_FULL_FIELDS.append(it["name"])
        text = text.replace("\n", " ").replace("\r", " ")
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
        # [Text] - single-language (EN) field label. CSPro does NOT auto-translate the form
        # label from the dict; per-language prompts live in the question text (.qsf).
        lines.append("[Text]")
        lines.append(f"Position={LABEL_X},{y + 3},{LABEL_X2},{y + 3 + TEXT_H}")
        lines.append(f"Text={text}")
        lines.append(" ")
        lines.append("  ")
    if not roster:   # rosters render as a grid; never auto-blocked into DisplayTogether
        _emit_blocks(lines, item_objs)
    lines.append("[EndGroup]")
    lines.append("  ")


# Blocks - Designer-verified grammar (learned from a Designer-authored save on F1
# 2026-06-11; hand-rolled blocks with wrong Position silently CRASH Designer on open):
# [Block] sections go at the END of the [Group], before [EndGroup]. Position indexes the
# group's item sequence in which each earlier block ALSO occupies one slot (so block 2
# after a 4-field block 1 starts at 0+1+4=5, not 4). DisplayTogether=Yes is what combines
# the fields onto one screen in Android CSEntry (phone + tablet).
#
# NOTE the #1102 issue class is DisplayTogether BLOCKS, not same-form placement: two fields
# sharing a form is harmless; two fields sharing a DisplayTogether block render together
# regardless of any skip or noinput gate between them.
NAMED_BLOCKS = [
    ("INTERVIEW_STAFF_BLOCK", "Interview Staff",
     ["SURVEY_TEAM_LEADER_S_NAME", "ENUMERATOR_S_NAME",
      "FIELD_VALIDATED_BY", "FIELD_EDITED_BY"]),
    ("VISIT_RECORD_BLOCK", "Facility Visit Record",
     ["DATE_FIRST_VISITED_THE_FACILITY", "DATE_OF_FINAL_VISIT_TO_THE_FACILITY",
      "TOTAL_NUMBER_OF_VISITS",
      "ENUM_RESULT_FIRST_VISIT", "ENUM_RESULT_FINAL_VISIT"]),
]

# Auto-group the survey body into DisplayTogether screens so related questions render
# together instead of one-field-per-screen. Records below keep their special single-screen
# handling and are NOT auto-grouped (admin uses NAMED_BLOCKS; geo cascade / GPS / photo
# stay as-is), matching the hand-maintained file, which carried DG_* blocks only on the
# A-H section groups.
_NO_AUTOGROUP_RECORDS = {
    "FIELD_CONTROL", "HEALTH_FACILITY_AND_GEOGRAPHIC_IDENTIFICATION",
    "REC_FACILITY_CAPTURE",
}
_MULTISELECT_RE = re.compile(r"^(.+?)_O\d+$")
# A sub-numbered question: Q<N>_<M>_... ("10.1", "12.2", "35.2", "48.1"). See
# _SUBQ_STARTS_SCREEN below for why these matter.
_SUBQ_RE = re.compile(r"^Q\d+_\d+_")

# Single alpha fields rendered as a CSPro Check Box (one-question multi-select tick-list).
# DERIVED FROM THE DICTIONARY rather than hard-coded: cspro_helpers.checkbox_multiselect
# emits exactly one shape - a single `alpha` item that carries a value set - and nothing
# else in F1 has that shape. Validated against F3, whose hand-maintained literal set this
# derivation reproduces exactly (51/51, no drift in either direction).
#
# WHY DERIVED. This list has historically been one of FOUR that must move together
# (generate_apc CHECKBOX_BASES, this one, fmf_checkbox_convert CONVERT, and
# automation/optimize_capture_types CHECKBOX). Missing one silently DEMOTES a multi-select
# to a single-select DropDown - a data-loss regression that has now happened twice (#529
# batch, #635/#639/#640). Two of the four are retired with the injectors; deriving this one
# from the dictionary leaves optimize_capture_types.CHECKBOX as the only copy that can
# drift, and it is the one the gates check.
_CHECKBOX_FIELDS = set()          # populated per-build by build_fmf()


def _derive_checkbox_fields(dictionary):
    """-> {names} of checkbox_multiselect bases: single alpha items carrying a value set."""
    out = set()
    for rec in dictionary["levels"][0]["records"]:
        for it in rec["items"]:
            if it.get("contentType") == "alpha" and it.get("valueSets"):
                out.add(it["name"])
    return out


# Fields that must OWN their screen for reasons other than capture type.
_OWN_SCREEN_FIELDS = {
    # The ICF read-aloud parts are one screen each by spec (Shan's layout, 2026-08-13);
    # without this they would fall into the ordinary MAX_CHUNK run and share a
    # DisplayTogether screen, collapsing the two consent screens into one.
    "ICF_PART1", "ICF_PART2",
    # Q87 (ex-Q100_ADDL_FEATURES) is a `noinput`-gated free-text with NO _TXT/_SPECIFY
    # suffix, so the suffix rule below cannot see it. It was one of only three such fields
    # in the pre-Aug-17 .apc (the other two live on the photo form, which is not
    # auto-grouped). Listed explicitly so the gate survives even when parse_apc has nothing
    # to say - see _warn_if_apc_stale().
    "Q87_ADDL_FEATURES",
}

# A sub-numbered question (Q<N>_<M>_...) always STARTS a new screen. This is the structural
# floor under the Section C two-step battery: 23 Yes/No bases each followed by a
# "<N>.1. If yes, was it a result of the UHC Act...?" probe that is gated on the base being
# Yes. On a DisplayTogether screen EVERY member field renders regardless of the gate
# (verified on-device, R4), so a base sharing a screen with its probe reproduces GH #371
# exactly - "Q10='No' still showed Q11". The apc's `skip to` source/target scan expresses
# the same rule when the apc is current; this one holds even when it is not.
_SUBQ_STARTS_SCREEN = True

_CHECKBOX_TRAILERS = ("_OTHER_TXT",)  # gated texts that would otherwise share the screen
MAX_CHUNK = 5                       # cap simple-question runs at ~5 per screen
_ACTIVE_BLOCK_PLAN = []            # set per-build by build_fmf()
# R25 caption census, reset per build. Printed by main() so the classification is auditable
# from the build log: a jump in 'keep-full' means labels lost their printed question number
# and questions are silently keeping their full stem on the form again.
_CAPTION_KINDS = {}
_KEEP_FULL_FIELDS = []


def _qnum(item):
    """-> the printed question number as a string ("36", "10.1"), or None."""
    lab = (item.get("labels") or [{}])[0].get("text", "") or ""
    m = re.match(r"\s*(\d+(?:\.\d+)?)", lab)
    if m:
        return m.group(1)
    m = re.match(r"Q(\d+)_(\d+)_", item["name"])
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = re.match(r"Q(\d+)", item["name"])
    return m.group(1) if m else None


def _chunk_label(item_objs):
    qs = [q for q in (_qnum(it) for it in item_objs) if q]
    if not qs:
        return "Questions"
    return f"Q{qs[0]}" if qs[0] == qs[-1] else f"Q{qs[0]}-Q{qs[-1]}"


def _is_gated_text(name, noinput_gated=frozenset()):
    """Other-specify / specify free-text fields carry a preproc 'noinput' gate (they show
    only when their trigger option is chosen). They MUST sit on their OWN screen - on a
    combined DisplayTogether screen every member field renders regardless of the gate, so
    the specify box would always appear (GH #372, the "cross-wired" _YES_OTHER_TXT /
    _NO_OTHER_TXT boxes). Catches *_OTHER_TXT and *_SPECIFY.

    `noinput_gated` (from parse_apc) is the authority when the .apc is current: any field
    whose PROC carries a `noinput` gate is isolated too, even when its name lacks the
    suffix - so a renamed or non-suffixed gated field can't slip onto a shared screen.
    _OWN_SCREEN_FIELDS carries the one such F1 field known from the pre-Aug-17 .apc."""
    return name.endswith("_TXT") or name.endswith("_SPECIFY") or name in noinput_gated


def parse_apc():
    """-> (skip_sources, skip_targets, noinput_gated) from the generated .ent.apc.

    Strip {...} comments, split on `^PROC <NAME>$`, collect PROCs that `skip to` (sources)
    and that carry `noinput` (gated), plus every `skip to <TARGET>` field name (targets).
    Returns empty sets if the .apc is absent (e.g. a bare `python generate_fmf.py` before
    the apc exists) - the plan then degrades to the structural rules rather than crashing;
    the canonical build always regenerates the apc first
    (cspro_compile_driver.build_instrument)."""
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


def _warn_if_apc_stale(dictionary, sources, targets, gated):
    """Say so LOUDLY when the .apc predates the dictionary.

    A stale .apc is not an error here - the fmf still generates, and the structural rules
    (gated-suffix, checkbox, sub-question, _OWN_SCREEN_FIELDS) still hold. What is lost is
    the skip-boundary awareness: a `skip to` SOURCE ending its screen and a TARGET starting
    a new one. Losing that silently is how the R4 bug class (GH #371/#372) shipped the first
    time, so it gets a banner rather than a debug line. Re-running the generator after
    generate_apc.py (which `--build` does automatically) clears it.

    -> the number of .apc names that still resolve to a real dictionary item."""
    names = {it["name"] for rec in dictionary["levels"][0]["records"] for it in rec["items"]}
    names |= {it["name"] for it in dictionary["levels"][0]["ids"]["items"]}
    seen = sources | targets | gated
    if not seen:
        sys.stderr.write(
            "  NOTE: no .ent.apc found - block plan uses the structural rules only "
            "(no skip-boundary awareness).\n")
        return 0
    live = seen & names
    if len(live) * 2 < len(seen):
        sys.stderr.write(
            "\n"
            "  ############################################################\n"
            "  # WARNING: FacilityHeadSurvey.ent.apc is STALE vs the .dcf  #\n"
            "  ############################################################\n"
            f"  only {len(live)}/{len(seen)} names referenced by the .apc still exist as\n"
            "  dictionary items, so the block plan is NOT skip-aware for this run:\n"
            f"    skip sources {len(sources & names)}/{len(sources)}   "
            f"targets {len(targets & names)}/{len(targets)}   "
            f"noinput gates {len(gated & names)}/{len(gated)}\n"
            "  Screens may span a skip boundary (GH #371/#372 bug class). REGENERATE the\n"
            "  .apc and re-run this generator (cspro_compile_driver.py F1 --build does both,\n"
            "  in order) before publishing.\n\n")
    return len(live)


def derive_block_plan(dictionary, sources=frozenset(), targets=frozenset(),
                      gated=frozenset()):
    """Auto DisplayTogether blocks for the survey body. Each multi-select option set -> one
    screen; other consecutive questions chunked at MAX_CHUNK per screen. Every on-form field
    of a processed record lands in exactly one block (contiguous, no gaps) so _emit_blocks'
    Position=start+emitted holds.

    Rules, in precedence order:
      1. Gated free-text (*_TXT / *_SPECIFY, or any field whose .apc PROC carries a preproc
         `noinput` gate) -> its OWN screen, so the gate can suppress the whole screen.
      2. Check Box tick-lists and _OWN_SCREEN_FIELDS -> their own screen.
      3. A sub-numbered question (Q<N>_<M>_) -> its own screen: it is a follow-up gated on
         its base, and a shared screen renders it regardless of the gate.
      4. Multi-select option runs (<BASE>_O01..) -> one checklist screen.
      5. Everything else chunks at MAX_CHUNK, EXCEPT: a `skip to` SOURCE ENDS its screen
         (nothing it can skip over may share the screen) and a `skip to` TARGET STARTS a new
         one (nothing skipped over may already be rendered on the target's screen).

    Rule 5's skip-awareness needs a CURRENT .apc; rules 1-4 do not. See _warn_if_apc_stale.

    Block names follow F3: DG_BLK_<n>, except the two consent screens, which are ICF_BLK_*.
    That naming was load-bearing while inject_blocks.py existed (it rebuilt "only the groups
    that already carry DG_* blocks", so DG_-named consent blocks would have been merged by
    its 5-field chunker); the script is retired, but the names are kept - they are the
    documented convention and cost nothing."""
    plan, n = [], 0
    for rec in dictionary["levels"][0]["records"]:
        if rec["name"] in _NO_AUTOGROUP_RECORDS:
            continue
        icf = rec["name"] == "A_INFORMED_CONSENT"
        icf_n = 0
        items = rec["items"]
        i = 0
        while i < len(items):
            nm = items[i]["name"]
            ms = _MULTISELECT_RE.match(nm)
            own = (_is_gated_text(nm, gated) or nm in _CHECKBOX_FIELDS
                   or nm in _OWN_SCREEN_FIELDS
                   or (_SUBQ_STARTS_SCREEN and _SUBQ_RE.match(nm)))
            if own:
                if icf:
                    bname = f"ICF_BLK_{icf_n}"
                    icf_n += 1
                else:
                    bname = f"DG_BLK_{n}"
                    n += 1
                plan.append((bname, (_qnum(items[i]) and f"Q{_qnum(items[i])}") or nm, [nm]))
                i += 1
            elif ms:                                       # multi-select OPTION run -> one screen
                base = ms.group(1)                          # (its trailing _OTHER_TXT is gated ->
                run = []                                    #  caught above, on its own screen)
                while i < len(items):
                    m2 = _MULTISELECT_RE.match(items[i]["name"])
                    if m2 and m2.group(1) == base and not _is_gated_text(items[i]["name"], gated):
                        run.append(items[i]); i += 1
                    else:
                        break
                label = (_qnum(run[0]) and f"Q{_qnum(run[0])}") or _chunk_label(run)
                plan.append((f"DG_BLK_{n}", label, [it["name"] for it in run])); n += 1
            else:                                          # chunk of up to MAX simple questions
                chunk = []
                while i < len(items) and len(chunk) < MAX_CHUNK:
                    nn = items[i]["name"]
                    if (_MULTISELECT_RE.match(nn) or nn in _CHECKBOX_FIELDS
                            or nn in _OWN_SCREEN_FIELDS or _is_gated_text(nn, gated)
                            or (_SUBQ_STARTS_SCREEN and _SUBQ_RE.match(nn))):
                        break                               # stop before the next block kind
                    if chunk and nn in targets:
                        break                               # skip TARGET starts a new screen
                    chunk.append(items[i]); i += 1
                    if nn in sources:
                        break                               # skip SOURCE ends its screen
                plan.append((f"DG_BLK_{n}", _chunk_label(chunk), [it["name"] for it in chunk]))
                n += 1
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


def _assert_form_invariants(forms):
    """The two ordering invariants the retired relocation scripts asserted, re-stated here
    so FORM_PLAN can never silently drop them.

      * Field Control immediately BEFORE the Verification Photo - the photo's preproc gates
        on ENUM_RESULT_FINAL_VISIT, so the result has to be entered before the camera fires
        (inject_field_control_end.py, #622).
      * Facility GPS DEAD LAST, after the photo (inject_gps_end.py, #157).

    Deliberately NOT asserted: "the photo is the last form". That assertion was REMOVED on
    2026-07-16 when GPS moved behind it; re-adding it would abort every build."""
    labels = [f["label"] for f in forms]

    def one(lbl):
        idx = [i for i, l in enumerate(labels) if l == lbl]
        if len(idx) != 1:
            raise RuntimeError(f"expected exactly one {lbl!r} form, found {len(idx)}")
        return idx[0]

    fc, photo, gps = one("Field Control"), one("Case Verification Photo"), one("Facility GPS")
    if photo != fc + 1:
        raise RuntimeError("Field Control must sit immediately before the Verification Photo "
                           f"(got {fc} -> {photo})")
    if gps != len(forms) - 1:
        raise RuntimeError(f"Facility GPS must be the LAST form (got {gps} of {len(forms) - 1})")
    if gps != photo + 1:
        raise RuntimeError("Facility GPS must sit immediately after the Verification Photo "
                           f"(got {photo} -> {gps})")


def build_fmf():
    dictionary = build_dictionary()
    global _CAPTION_KINDS, _KEEP_FULL_FIELDS
    _CAPTION_KINDS, _KEEP_FULL_FIELDS = {}, []   # reset: build_fmf is called by the gates too
    _truncate_long_labels(dictionary)  # match the .dcf's 255-char label cap (CSPro max)
    global _ACTIVE_BLOCK_PLAN, _CHECKBOX_FIELDS
    _CHECKBOX_FIELDS = _derive_checkbox_fields(dictionary)
    sources, targets, gated = parse_apc()
    _warn_if_apc_stale(dictionary, sources, targets, gated)
    _ACTIVE_BLOCK_PLAN = NAMED_BLOCKS + derive_block_plan(dictionary, sources, targets, gated)
    dict_name = dictionary.get("name", "FACILITYHEADSURVEY_DICT")
    level = dictionary["levels"][0]
    level_name = level.get("name", "FACILITYHEADSURVEY_LEVEL")
    records_by_name = {r["name"]: r for r in level["records"]}

    def _roster_info(record_name):
        """A repeating record (occurrences.maximum > 1) -> roster grid; else None.
        F1 has none today; kept for F3/F4 parity."""
        occ = records_by_name[record_name].get("occurrences") or {}
        mx = occ.get("maximum", 1) if isinstance(occ, dict) else 1
        return {"type_name": record_name, "max": mx} if (mx and mx > 1) else None

    referenced = {rec for _, parts, _ in FORM_PLAN for rec, _ in parts}
    missing = referenced - set(records_by_name)
    if missing:
        raise RuntimeError(f"FORM_PLAN references missing records: {sorted(missing)}")

    record_items_consumed = {name: set() for name in records_by_name}
    used_group_syms = set()

    # forms: list of dicts {num, label, group_sym, form_item_names, group_item_objs}
    forms = []
    # FORM000 - the case-key ID item (the 12-digit QUESTIONNAIRE_NUMBER), entered FIRST,
    # before consent, so a consent refusal has a valid case key to save (an empty key ->
    # "Warning 1026: All of the ID fields were not filled" at endlevel). CSPro DOES place id
    # items on the first form as ordinary [Field]s - cf. the CAPI Census "Geocodes" form; the
    # earlier "id items get stripped" note was a misdiagnosis, the empty IDS0_FORM was simply
    # never enterable. The vestigial empty level-1 container form
    # (FACILITYHEADSURVEY_REC_FORM) that inject_case_key.py had to strip is not emitted at
    # all: generate_dcf drops the record, so forms run key=0, plan=1+.
    id_objs = list(level["ids"]["items"])
    forms.append({"num": 0, "label": "Case Key (Facility Head ID)", "group_sym": "IDS0_FORM",
                  "form_item_names": [it["name"] for it in id_objs], "group_item_objs": id_objs,
                  "roster": None})
    used_group_syms.add("IDS0_FORM")
    for idx, (label, parts, group_sym) in enumerate(FORM_PLAN, start=1):
        objs = []
        for rec_name, spec in parts:
            for it in _filter_items(records_by_name[rec_name]["items"], spec):
                record_items_consumed[rec_name].add(it["name"])
                objs.append(it)
        primary = parts[0][0]
        if group_sym:
            if group_sym in used_group_syms:
                raise RuntimeError(f"duplicate group symbol {group_sym!r} in FORM_PLAN")
            used_group_syms.add(group_sym)
        else:
            group_sym = _group_symbol(primary, used_group_syms)
        forms.append({"num": idx, "label": label,
                      "group_sym": group_sym,
                      "form_item_names": [it["name"] for it in objs],
                      "group_item_objs": objs,
                      "roster": _roster_info(primary)})

    _assert_form_invariants(forms)

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

    # Logical structure: one [Level], one [Group] per form. Form= is the 1-based ORDINAL,
    # computed from position here so it can never drift out of step with the [Form] list.
    lines.append("[Level]")
    lines.append(f"Name={level_name}")
    lines.append(f"Label={DICT_LABEL} Level")
    lines.append("  ")
    for f in forms:
        _emit_group(lines, f["group_sym"], f["label"], f["num"] + 1,
                    f["group_item_objs"], dict_name, roster=f["roster"])

    # Orphan check - an item on no form is UNREACHABLE in CSEntry (the defect class
    # inject_q2_other_txt.py and inject_q163_other_txt.py existed to repair one field at a
    # time). automation/verify_questions.py is the external gate for the same rule.
    orphans = []
    for rec_name, rec in records_by_name.items():
        if rec["recordType"] == "1":
            continue
        placed = record_items_consumed[rec_name]
        for it in rec["items"]:
            if it["name"] not in placed and it["name"] not in _OFF_FORM_ITEMS:
                orphans.append(f"{rec_name}.{it['name']}")
    if orphans:
        sys.stderr.write(f"WARNING: {len(orphans)} items not placed on any form:\n")
        for o in orphans:
            sys.stderr.write(f"  {o}\n")

    n_fields = sum(len(f["group_item_objs"]) for f in forms)
    n_blocks = len(_ACTIVE_BLOCK_PLAN)
    return "\r\n".join(lines) + "\r\n", len(orphans), len(forms), n_fields, n_blocks


def main():
    out_path = Path(__file__).parent / "FacilityHeadSurvey.generated.fmf"
    fmf_text, orphan_count, n_forms, n_fields, n_blocks = build_fmf()
    # write BYTES, not text. The lines above are joined with CRLF already, and a text-mode
    # write on Windows translates every "\n" again -> "\r\r\n" on disk. CSPro tolerates
    # that, but optimize_capture_types.py then reads it back through universal newlines
    # ("\r\r\n" -> "\n\n") and rewrites it, so the bound .fmf ends up with a BLANK LINE
    # after every line and twice the size. That is exactly what happened to F3
    # (PatientSurvey.generated.fmf: 7276 CRCRLF -> PatientSurvey.fmf: 14552 CRLF, 2x).
    # F1's hand-maintained file was clean CRLF + BOM, and this keeps it that way.
    out_path.write_bytes(b"\xef\xbb\xbf" + fmf_text.encode("utf-8"))
    sys.stderr.write(f"Wrote {out_path} ({orphan_count} orphan items)\n")
    sys.stderr.write(f"  forms: {n_forms}  fields: {n_fields}  "
                     f"checkbox bases: {len(_CHECKBOX_FIELDS)}  blocks planned: {n_blocks}\n")
    census = "  ".join(f"{k}={v}" for k, v in sorted(_CAPTION_KINDS.items()))
    sys.stderr.write(f"  R25 captions: {census}\n")
    sys.stderr.write(f"  keep-full (no question number): {len(_KEEP_FULL_FIELDS)}\n")


if __name__ == "__main__":
    main()
