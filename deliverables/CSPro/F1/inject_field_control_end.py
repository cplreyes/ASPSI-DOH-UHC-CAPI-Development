#!/usr/bin/env python3
r"""
RETIRED 2026-08-19 - superseded by generate_fmf.py; kept for history.
========================================================================
F1's .fmf was hand-maintained, and this script was one of eleven idempotent post-processors
that patched it by locating fields by NAME and geometry. The Aug-17 instrument renumber
(Task 2.2) renamed ~112 of 320 dictionary items, invalidating those anchors, so F1 adopted
the F3/F4 generator (Task 2.3). Do NOT run this file; do not delete it either - the WHY
recorded below is the reason each invariant is worth preserving.

WHERE THIS SCRIPT'S INVARIANT LIVES NOW
---------------------------------------
FORM_PLAN's order (Field Control -> Case Verification Photo -> Facility GPS), and
generate_fmf._assert_form_invariants(), which fails the build if Field Control is
not immediately before the photo. As here, there is deliberately NO 'photo must be
last' assertion - GPS sits after it since #157.
========================================================================
Relocate F1's "Field Control" form to the CLOSING position — right before the
Case Verification Photo — in the hand-maintained FacilityHeadSurvey.fmf.

WHY THIS EXISTS (UAT R4 #622, 2026-06-20)
-----------------------------------------
F3/F4 build their .fmf from generate_fmf.py, where the field-control block is
already the closing form (FORM_PLAN: ... -> "Closing - case end" -> "Case
Verification Photo"). F1's .fmf is hand-maintained with NO generator: its Field
Control form sits at the START (FORM001, right after the case key), so the
enumerator is asked for "Result of Visit" / "Total Number of Visits" / visit
dates BEFORE the interview happens — flagged illogical by the tester (#622).

This moves the whole Field Control form (team-leader / enumerator / validator
names + visit dates + total visits + result-of-visit) to the END, matching
F3/F4's "all field control at case-end" convention.

Field Control MUST land immediately BEFORE the Verification Photo: the photo's
preproc gates on ENUM_RESULT_FINAL_VISIT (photograph only completed/incomplete
visits), so the result has to be entered before the camera fires. That
adjacency is the invariant this script enforces.

The photo is NO LONGER required to be the very last form (changed 2026-07-16,
#157): "Facility GPS" now sits after it — see inject_gps_end.py, which runs
after this script. GPS has no gate of its own, so it is safe there. Do not
re-add a "photo must be last" assertion; it would abort the pipeline on every
re-run once GPS has been moved.

POST-PROCESSOR, not a hand-edit (IRON-RULE compliant). The .fmf binds each
[Group] to a [Form] by a 1-based ordinal (Form=N -> the Nth form, named
FORM{N-1:03d}); presentation order follows the [Group] order. So we move BOTH the
Field Control [Form] block and its [Group] block to just before the photo, then
RE-DERIVE every form ordinal from position (FORM Name= + every Group/Field Form=).

Idempotent: when Field Control is already right before the photo the move is a
no-op and re-derivation reproduces identical output. Run it in the F1 .fmf
pipeline: fmf_checkbox_convert.py -> inject_blocks.py -> inject_case_key.py ->
inject_field_control_end.py -> inject_gps_end.py.

Run:  python inject_field_control_end.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FMF = HERE / "FacilityHeadSurvey.fmf"

FC_FORM_LABEL = "Field Control"            # the Field Control [Form] Label=
PHOTO_FORM_LABEL = "Case Verification Photo"
FC_GROUP_NAME = "FIELD_CONTROL_FORM"       # the Field Control [Group] Name=
PHOTO_GROUP_NAME = "CASE_VERIFICATION_FORM"


def _split_blocks(region, tag):
    """Split a region of consecutive [tag]...[Endtag] blocks (each carrying its
    trailing whitespace separator) into a list. Asserts the pieces reconstruct
    the region byte-for-byte, so nothing is silently dropped."""
    blocks = re.findall(rf"\[{tag}\].*?\[End{tag}\]\s*", region, re.DOTALL)
    if "".join(blocks) != region:
        sys.exit(f"ERROR: [{tag}] split is lossy — refusing to write.")
    return blocks


def _find_one(blocks, needle, what):
    idx = [i for i, b in enumerate(blocks) if needle in b]
    if len(idx) != 1:
        sys.exit(f"ERROR: expected exactly one {what} matching '{needle}', found {len(idx)}.")
    return idx[0]


def _move_before(blocks, src_idx, anchor_needle):
    """Pop block at src_idx and reinsert it immediately before the block that
    contains anchor_needle (recomputed after the pop)."""
    block = blocks.pop(src_idx)
    anchor = [i for i, b in enumerate(blocks) if anchor_needle in b][0]
    blocks.insert(anchor, block)
    return blocks


def main():
    text = FMF.read_text(encoding="utf-8")  # keeps the BOM as a leading char

    # --- carve: prefix | [Form]* | [Level]-header (mid) | [Group]* ---
    # "[Form]" does not match the "[FormFile]" header (no closing ']' after "Form").
    f0 = text.index("[Form]")
    lvl = text.index("[Level]")
    g0 = text.index("[Group]", lvl)
    prefix = text[:f0]
    forms = _split_blocks(text[f0:lvl], "Form")
    mid = text[lvl:g0]
    groups = _split_blocks(text[g0:], "Group")

    if len(forms) != len(groups):
        sys.exit(f"ERROR: {len(forms)} [Form] vs {len(groups)} [Group] blocks — 1:1 expected.")

    fc_form = _find_one(forms, f"Label={FC_FORM_LABEL}", "Field Control form")
    ph_form = _find_one(forms, f"Label={PHOTO_FORM_LABEL}", "Verification Photo form")
    fc_grp = _find_one(groups, f"Name={FC_GROUP_NAME}", "Field Control group")
    ph_grp = _find_one(groups, f"Name={PHOTO_GROUP_NAME}", "Verification Photo group")
    already = (fc_form == ph_form - 1) and (fc_grp == ph_grp - 1)

    forms = _move_before(forms, fc_form, f"Label={PHOTO_FORM_LABEL}")
    groups = _move_before(groups, fc_grp, f"Name={PHOTO_GROUP_NAME}")

    # --- re-derive every ordinal from final position ---
    for i, b in enumerate(forms):
        forms[i] = re.sub(r"(?m)^Name=FORM\d+", f"Name=FORM{i:03d}", b, count=1)
    for i, b in enumerate(groups):
        # every "^Form=N" in a group block (the [Group] header + each [Field])
        # links to that group's form; they all become i+1.
        groups[i] = re.sub(r"(?m)^Form=\d+", f"Form={i + 1}", b)

    # --- guard: Field Control sits immediately before the photo ---
    # Position-independent on purpose: since #157 (2026-07-16) the photo is NOT the
    # last form — inject_gps_end.py moves "Facility GPS" after it. The invariant that
    # matters is the ADJACENCY (FC collects ENUM_RESULT_FINAL_VISIT; the photo's
    # preproc gates on it), not where the pair sits in the file.
    fc_i = _find_one(forms, f"Label={FC_FORM_LABEL}", "Field Control form")
    ph_i = _find_one(forms, f"Label={PHOTO_FORM_LABEL}", "Verification Photo form")
    fc_g = _find_one(groups, f"Name={FC_GROUP_NAME}", "Field Control group")
    ph_g = _find_one(groups, f"Name={PHOTO_GROUP_NAME}", "Verification Photo group")
    if ph_i != fc_i + 1:
        sys.exit("ERROR: Field Control did not land immediately before the photo form — aborting.")
    if ph_g != fc_g + 1:
        sys.exit("ERROR: Field Control did not land immediately before the photo group — aborting.")

    out = prefix + "".join(forms) + mid + "".join(groups)
    FMF.write_text(out, encoding="utf-8")

    print(f"Relocated 'Field Control' -> before 'Case Verification Photo' in {FMF.name}")
    print(f"  forms/groups: {len(forms)} (1:1)")
    print(f"  order: {FC_FORM_LABEL} (FORM{fc_i:03d}, Form={fc_i + 1})"
          f" -> {PHOTO_FORM_LABEL} (FORM{ph_i:03d}, Form={ph_i + 1})"
          f"{'' if ph_i == len(forms) - 1 else f'  [+{len(forms) - 1 - ph_i} form(s) after the photo — expected: Facility GPS]'}")
    print(f"  {'(was already in place — output identical, no structural change)' if already else 'moved + renumbered'}")


if __name__ == "__main__":
    raise SystemExit(
        "RETIRED 2026-08-19 - superseded by F1/generate_fmf.py; this script must NOT be run.\n"
        "It anchors on pre-Aug-17 field names and geometry, so against the current instrument\n"
        "it would either abort or silently mis-place fields in a file that is now rebuilt from\n"
        "the dictionary on every build. See the module docstring for the invariant it used to\n"
        "enforce and where that invariant lives today.")
