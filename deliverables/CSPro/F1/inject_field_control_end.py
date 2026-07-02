#!/usr/bin/env python3
r"""Relocate F1's "Field Control" form to the CLOSING position — right before the
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

The Verification Photo MUST remain the very last form: its preproc gates on
ENUM_RESULT_FINAL_VISIT (photograph only completed/incomplete visits), so the
result has to be entered before the camera fires. So Field Control lands in the
SECOND-TO-LAST position — immediately before the photo.

POST-PROCESSOR, not a hand-edit (IRON-RULE compliant). The .fmf binds each
[Group] to a [Form] by a 1-based ordinal (Form=N -> the Nth form, named
FORM{N-1:03d}); presentation order follows the [Group] order. So we move BOTH the
Field Control [Form] block and its [Group] block to just before the photo, then
RE-DERIVE every form ordinal from position (FORM Name= + every Group/Field Form=).

Idempotent: when Field Control is already right before the photo the move is a
no-op and re-derivation reproduces identical output. Run it LAST in the F1 .fmf
pipeline: fmf_checkbox_convert.py -> inject_blocks.py -> inject_case_key.py ->
inject_field_control_end.py.

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

    # --- guard: photo stays last, Field Control is now second-to-last ---
    if f"Label={PHOTO_FORM_LABEL}" not in forms[-1] or f"Name={PHOTO_GROUP_NAME}" not in groups[-1]:
        sys.exit("ERROR: Verification Photo is no longer the last form/group — aborting.")
    if f"Label={FC_FORM_LABEL}" not in forms[-2] or f"Name={FC_GROUP_NAME}" not in groups[-2]:
        sys.exit("ERROR: Field Control did not land immediately before the photo — aborting.")

    out = prefix + "".join(forms) + mid + "".join(groups)
    FMF.write_text(out, encoding="utf-8")

    print(f"Relocated 'Field Control' -> before 'Case Verification Photo' in {FMF.name}")
    print(f"  forms/groups: {len(forms)} (1:1)")
    print(f"  new tail order: ... -> {FC_FORM_LABEL} (FORM{len(forms) - 2:03d}, Form={len(forms) - 1})"
          f" -> {PHOTO_FORM_LABEL} (FORM{len(forms) - 1:03d}, Form={len(forms)})")
    print(f"  {'(was already in place — output identical, no structural change)' if already else 'moved + renumbered'}")


if __name__ == "__main__":
    main()
