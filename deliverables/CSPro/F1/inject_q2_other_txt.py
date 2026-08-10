#!/usr/bin/env python3
"""Inject the Q2 "Other (specify)" free-text field into F1's static
FacilityHeadSurvey.fmf.

WHY THIS EXISTS
---------------
Pretest finding #1005 (2026-08-03): the printed Annex F1 Q2 designation grid
carries THIRTEEN options read column-major, but the build shipped only the
first ELEVEN -- it stopped one row into column 3, dropping "Rural Health
Physician" and "Other (specify)". generate_dcf.py now emits all thirteen plus a
companion Q2_OTHER_TXT alpha item, and generate_apc.py's
auto_other_specify_procs() derives the gate from the dict automatically
(preproc noinput / postproc reenter against Q2_FACILITY_ROLE = 99).

F3/F4 build their .fmf from generate_fmf.py, so a new dictionary item lands on
the form for free. F1's .fmf is a hand-authored static file with NO generator,
and inject_blocks.py only RE-BLOCKS FIELDS THAT ALREADY EXIST -- so without
this script Q2_OTHER_TXT would be an orphan (verify_questions.py: UNREACHABLE),
and the recovered "Other (specify)" option would be exactly the defect the DOH
reviewer filed 88 times: a specify option with nowhere to type the answer.

This is a POST-PROCESSOR, not a hand-edit (IRON-RULE compliant): it reads the
item's label from the .dcf and generates the [Field] + [Text] pair, placing it
immediately after Q2_FACILITY_ROLE so the enumerator types the specify text
right where they chose "Other" -- not four questions later. The profile form is
a uniform 30px grid, so every later field on that form shifts down one row and
the form box grows by the same amount.

The host form is found by searching for the roster that owns Q2_FACILITY_ROLE,
and its ordinal is read off the anchor [Field] -- never hardcoded, because
inject_gps_end.py's #157 move renumbers the forms (the profile form is FORM002
before the GPS move and FORM003 after it, or vice versa depending on order).

Idempotent: re-running is a no-op once Item=Q2_OTHER_TXT is on the form, so it
is safe to leave in the F1 .fmf pipeline. Run it BEFORE the block/end-of-form
injectors, i.e.:

    python generate_dcf.py
    python inject_case_key.py
    python inject_q2_other_txt.py      <-- here
    python inject_blocks.py
    python inject_breakoff.py
    python inject_field_control_end.py
    python inject_gps_end.py
    python generate_apc.py
    python generate_qsf.py

Run:  python inject_q2_other_txt.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DCF = HERE / "FacilityHeadSurvey.dcf"
FMF = HERE / "FacilityHeadSurvey.fmf"

ITEM = "Q2_OTHER_TXT"
ANCHOR = "Q2_FACILITY_ROLE"          # insert immediately after this field
DICT_NAME = "FACILITYHEADSURVEY_DICT"

# The host form is located by SEARCHING for the roster that owns ANCHOR, and its
# ordinal is read off the anchor [Field] itself -- never hardcoded. F1's form
# ORDER is not stable: inject_gps_end.py moves "Facility GPS" to the end (#157),
# which renumbers every form after it. A hardcoded FORM002/Form=3 silently
# targets the wrong form depending on whether the GPS move has been applied.

# Layout constants -- Form 3's existing grid (see RESP_NAME..Q6_MONTHS_HEALTH).
ROW_H = 30           # vertical pitch between fields on this form
FIELD_X = 760        # left edge of the entry control
FIELD_X2_TEXT = 1410 # right edge for a long alpha box (matches RESP_NAME/Q1_NAME)
FIELD_H = 20
LABEL_X = 50
TEXT_H = 16
TEXT_DY = 3          # label sits 3px below the field's top (50,180 vs 760,177)
PX_PER_CHAR = 6.4    # label width estimate, averaged from this form's [Text] rows


def dcf_label(item_name):
    """Read the item's EN label from the dictionary so the form text cannot
    drift from the data dictionary."""
    d = json.loads(DCF.read_text(encoding="utf-8"))

    def walk(o):
        if isinstance(o, dict):
            yield o
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)

    for node in walk(d):
        if node.get("name") == item_name:
            for lab in node.get("labels") or []:
                if lab.get("language") in (None, "EN"):
                    return lab.get("text", item_name)
    return None


def parse_pos(s):
    return [int(x) for x in s.split(",")]


def fmt_pos(v):
    return ",".join(str(x) for x in v)


def main():
    if not DCF.exists() or not FMF.exists():
        sys.exit("ERROR: run generate_dcf.py first -- .dcf/.fmf not found.")

    text = FMF.read_text(encoding="utf-8")  # keeps the BOM as a leading char
    if f"Item={ITEM}\n" in text or f"Item={ITEM}\r" in text:
        print(f"{ITEM} already present in FacilityHeadSurvey.fmf -- no-op.")
        return

    label = dcf_label(ITEM)
    if label is None:
        sys.exit(f"ERROR: {ITEM} is not in the .dcf -- run generate_dcf.py first.")

    lines = text.split("\n")

    # ---- 1. find the form whose roster owns ANCHOR; grow its box ------------
    roster_at = None
    size_at = None
    form_name = None
    cur_size = cur_name = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s == "[Form]":
            cur_size = cur_name = None
        elif s.startswith("Name=") and cur_name is None:
            cur_name = s[len("Name="):]
        elif s.startswith("Size="):
            cur_size = i
        elif s == f"Item={ANCHOR}":
            roster_at, size_at, form_name = i, cur_size, cur_name
            break
    if roster_at is None:
        sys.exit(f"ERROR: Item={ANCHOR} not found in any form roster -- .fmf changed shape.")

    if size_at is not None:
        w, h = parse_pos(lines[size_at].strip()[len("Size="):])
        lines[size_at] = f"Size={w},{h + ROW_H}"
    lines.insert(roster_at + 1, f"Item={ITEM}")

    # ---- 2. locate the anchor [Field] and the [Text] that follows it --------
    anchor_field = None
    for i, ln in enumerate(lines):
        if ln.strip() == f"Name={ANCHOR}":
            # a [Field] block, not the [Form] roster (roster lines are Item=)
            if i and lines[i - 1].strip() == "[Field]":
                anchor_field = i - 1
                break
    if anchor_field is None:
        sys.exit(f"ERROR: [Field] {ANCHOR} not found -- .fmf changed shape.")

    fy = None
    form_ordinal = None
    j = anchor_field + 1
    while j < len(lines) and lines[j].strip() != "[Text]":
        s = lines[j].strip()
        if s.startswith("Position="):
            fy = parse_pos(s[len("Position="):])
        elif s.startswith("Form="):
            form_ordinal = s[len("Form="):]
        j += 1
    if form_ordinal is None:
        sys.exit(f"ERROR: [Field] {ANCHOR} has no Form= -- .fmf changed shape.")
    # j is at the anchor's [Text]; advance to its Text= line
    while j < len(lines) and not lines[j].strip().startswith("Text="):
        j += 1
    insert_at = j + 1
    if fy is None:
        sys.exit("ERROR: anchor field has no Position= -- .fmf changed shape.")

    new_y = fy[1] + ROW_H
    label_x2 = LABEL_X + int(len(label) * PX_PER_CHAR)
    block = [
        " ",
        "  ",
        "[Field]",
        f"Name={ITEM}",
        f"Position={fmt_pos([FIELD_X, new_y, FIELD_X2_TEXT, new_y + FIELD_H])}",
        f"Item={ITEM},{DICT_NAME}",
        "UseUnicodeTextBox=Yes",
        "DataCaptureType=TextBox",
        f"Form={form_ordinal}",
        "  ",
        "[Text]",
        f"Position={fmt_pos([LABEL_X, new_y + TEXT_DY, label_x2, new_y + TEXT_DY + TEXT_H])}",
        f"Text={label}",
    ]
    lines[insert_at:insert_at] = block

    # ---- 3. shift every LATER field on this form down one row ---------------
    shifted = 0
    k = insert_at + len(block)
    while k < len(lines):
        if lines[k].strip() == "[Field]":
            # read the block; only shift if it belongs to this form
            blk_end = k + 1
            pos_at = None
            form_val = None
            while blk_end < len(lines) and not lines[blk_end].strip().startswith("["):
                s = lines[blk_end].strip()
                if s.startswith("Position="):
                    pos_at = blk_end
                elif s.startswith("Form="):
                    form_val = s[len("Form="):]
                blk_end += 1
            if form_val != form_ordinal:
                break                      # left this form -- nothing after it moves
            if pos_at is not None:
                p = parse_pos(lines[pos_at].strip()[len("Position="):])
                p[1] += ROW_H
                p[3] += ROW_H
                lines[pos_at] = f"Position={fmt_pos(p)}"
                shifted += 1
            # its [Text] label moves with it
            if blk_end < len(lines) and lines[blk_end].strip() == "[Text]":
                t = blk_end + 1
                while t < len(lines) and not lines[t].strip().startswith("["):
                    s = lines[t].strip()
                    if s.startswith("Position="):
                        p = parse_pos(s[len("Position="):])
                        p[1] += ROW_H
                        p[3] += ROW_H
                        lines[t] = f"Position={fmt_pos(p)}"
                    t += 1
                blk_end = t
            k = blk_end
        else:
            k += 1

    FMF.write_text("\n".join(lines), encoding="utf-8")
    print(f"Injected {ITEM} after {ANCHOR} on {form_name} (y={new_y}); "
          f"shifted {shifted} later field(s) down {ROW_H}px.")
    print(f"  label: {label}")


if __name__ == "__main__":
    main()
