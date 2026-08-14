#!/usr/bin/env python3
r"""Inject the Informed Consent read-aloud form into F1's static FacilityHeadSurvey.fmf.

WHY THIS EXISTS
---------------
Shan's "Suggested Layout (CSEntry)" (2026-08-13) puts the consent script on the device
as TWO read-aloud screens per instrument. F3/F4 build their .fmf from generate_fmf.py,
so the two ICF fields land on a form automatically there. F1's .fmf is the hand-authored
static file with no generator, so its consent form has to be produced the same way every
other F1 form-level change is: a programmatic, idempotent post-processor. Same pattern
and rationale as inject_case_key.py — we never hand-edit the .fmf.

WHAT IT DOES
------------
1. Removes any previously injected ICF [Form] and [Group] (so re-running is safe and
   always rebuilds from the current dictionary rather than layering edits).
2. Inserts the ICF [Form] as the THIRD form — after FORM000 (case key) and FORM001
   (facility + geographic ID), before "A. Facility Head Profile". This matches F3/F4,
   where A_INFORMED_CONSENT sits after the geo form and before the first content
   section.
3. Inserts the matching [Group] at the same ordinal position.
4. Renumbers EVERY `Form=` in the file. A [Group]'s (and its [Field]s') `Form=N` is the
   1-BASED ORDINAL of the form section, not an id — inserting a form mid-list silently
   points every later group at the wrong form unless they are all rewritten. The k-th
   group in document order owns the k-th form (verified invariant, 13/13 before this
   change), so the ordinals are recomputed from position rather than patched by offset.

BLOCK NAMING (deliberate)
-------------------------
The two DisplayTogether blocks are named ICF_BLK_*, NOT DG_*. inject_blocks.py rebuilds
the block plan for "only the section groups that already carry auto-generated DG_*
blocks"; if these were DG_*, its 5-field chunker would merge the two consent screens
into one, which is exactly what the layout does not want. A non-DG name keeps this group
outside that pass. Position follows the same Designer-verified rule the other blocks use
(Position = start + blocks emitted before it in the group), so two single-field blocks
sit at Position 0 and 2.

Run AFTER generate_dcf.py (it needs ICF_PART1/ICF_PART2 to exist in the dictionary) and
alongside the other inject_*.py post-processors.

    python inject_icf.py            # rewrites FacilityHeadSurvey.fmf in place
    python inject_icf.py --check    # report only, exit 1 if the form is missing
"""
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
FMF = HERE / "FacilityHeadSurvey.fmf"
DCF = HERE / "FacilityHeadSurvey.dcf"
DICT_NAME = "FACILITYHEADSURVEY_DICT"

GROUP_NAME = "A_INFORMED_CONSENT_FORM"
FORM_NAME = "FORM_ICF"
FORM_LABEL = "Introduction and Informed Consent"
ICF_FIELDS = ("ICF_PART1", "ICF_PART2")
INSERT_AT = 2          # 0-based: third form, after the case-key and geo forms

# On-form field captions. The read-aloud script itself is question text (.qsf), not a
# form caption — these just name the screen. ASCII only: the .fmf is UTF-8 with a BOM
# and CRLF, and there is no reason to risk an encoding round-trip for a hyphen.
FIELD_CAPTIONS = {
    "ICF_PART1": "Informed Consent - read aloud (screen 1 of 2)",
    "ICF_PART2": "Informed Consent - read aloud (screen 2 of 2)",
}


def build_form_section():
    items = "".join(f"Item={f}\n" for f in ICF_FIELDS)
    return (f"[Form]\nName={FORM_NAME}\nLabel={FORM_LABEL}\nLevel=1\n"
            f"Size=806,300\n  \n{items}  \n[EndForm]\n  \n")


def build_group_section(form_ordinal):
    out = [f"[Group]\nRequired=Yes\nName={GROUP_NAME}\nLabel={FORM_LABEL}\n"
           f"Form={form_ordinal}\nMax=1\n  \n  \n"]
    for i, f in enumerate(ICF_FIELDS):
        top = 27 + i * 30
        out.append(
            f"[Field]\nName={f}\nPosition=354,{top},369,{top + 20}\n"
            f"Item={f},{DICT_NAME}\nDataCaptureType=RadioButton\n"
            f"Form={form_ordinal}\n  \n"
            f"[Text]\nPosition=50,{top + 3},317,{top + 19}\n"
            f"Text={FIELD_CAPTIONS[f]}\n \n  \n")
    # one screen per consent part: Position = start + blocks already emitted
    for i, f in enumerate(ICF_FIELDS):
        out.append(f"[Block]\nName=ICF_BLK_{i}\nLabel={f}\nDisplayTogether=Yes\n"
                   f"Position={i * 2}\nLength=1\n  \n")
    out.append("[EndGroup]\n  \n")
    return "".join(out)


def split_sections(text, start_tag, end_tag):
    """-> (prefix, [section, ...], suffix) over repeated start_tag..end_tag runs."""
    first = text.find(start_tag)
    last = text.rfind(end_tag) + len(end_tag)
    body = text[first:last]
    parts, pos = [], 0
    while True:
        s = body.find(start_tag, pos)
        if s < 0:
            break
        e = body.find(end_tag, s) + len(end_tag)
        parts.append(body[s:e])
        pos = e
    return text[:first], parts, text[last:]


def main():
    check_only = "--check" in sys.argv
    text = io.open(FMF, encoding="utf-8-sig").read()

    dictionary = json.loads(io.open(DCF, encoding="utf-8-sig").read())
    names = {it["name"] for lvl in dictionary["levels"]
             for r in lvl.get("records", []) for it in r.get("items", [])}
    missing = [f for f in ICF_FIELDS if f not in names]
    if missing:
        sys.exit(f"ERROR: {missing} not in the dictionary — run generate_dcf.py first.")

    if check_only:
        have = all(f"Name={f}\n" in text for f in ICF_FIELDS)
        print(f"ICF form present: {have}")
        sys.exit(0 if have else 1)

    head, forms, mid_and_rest = split_sections(text, "[Form]", "[EndForm]\n")
    mid, groups, tail = split_sections(mid_and_rest, "[Group]", "[EndGroup]\n")

    before = (len(forms), len(groups))
    # 1. drop any previous injection so this is a rebuild, not a layering
    forms = [f for f in forms if f"Name={FORM_NAME}\n" not in f]
    groups = [g for g in groups if f"Name={GROUP_NAME}\n" not in g]
    removed = (before[0] - len(forms), before[1] - len(groups))

    if len(forms) != len(groups):
        sys.exit(f"ERROR: {len(forms)} forms vs {len(groups)} groups — "
                 "the k-th-group-owns-the-k-th-form invariant does not hold; "
                 "refusing to renumber.")

    # 2/3. insert at the same ordinal in both lists
    forms.insert(INSERT_AT, build_form_section())
    groups.insert(INSERT_AT, build_group_section(INSERT_AT + 1))

    # 4. recompute every Form= from position (never patch by offset)
    groups = [re.sub(r"(?m)^Form=\d+$", f"Form={k + 1}", g)
              for k, g in enumerate(groups)]

    out = head + "".join(forms) + mid + "".join(groups) + tail
    with io.open(FMF, "w", encoding="utf-8-sig", newline="\r\n") as fh:
        fh.write(out)

    print(f"Rewrote {FMF.name}")
    print(f"  removed prior injection: {removed[0]} form(s), {removed[1]} group(s)")
    print(f"  forms {before[0]} -> {len(forms)}; ICF at ordinal {INSERT_AT + 1} "
          f"({FORM_LABEL})")
    print(f"  renumbered Form= across {len(groups)} groups")


if __name__ == "__main__":
    main()
