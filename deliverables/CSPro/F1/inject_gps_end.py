#!/usr/bin/env python3
r"""Relocate F1's "Facility GPS" form to DEAD LAST — after the Case Verification
Photo — in the hand-maintained FacilityHeadSurvey.fmf.

WHY THIS EXISTS (#157, pretest 2026-07-16)
------------------------------------------
Field teams hit a bottleneck during the live pretest: there is no GPS signal
inside hospitals, so they reported they "cannot proceed" with interviews.

The real mechanism is narrower than a block. shared/Capture-Helpers.apc's
ReadGPSReading(120, 20) calls gps(read, maxTimeSec=120, ...), which is
SYNCHRONOUS: indoors with no fix it stalls the enumerator on the field for a
full 120 seconds, then raises errmsg and leaves the GPS fields blank. Nothing
hard-blocks (no retry loop, no required-field trap) — but the tablet looks
frozen, so the field reads it as blocked. And F1's "Facility GPS" sat at
FORM002, the THIRD form: before consent, before Section A.

Moving GPS behind the photo makes it the last thing in the case, so nothing in
the interview waits on a satellite fix. The enumerator finishes, records the
result, photographs the visit, walks out — and GPS acquires outdoors, which is
the natural workflow.

Be honest about what this does NOT do: the 120s stall is RELOCATED, not
removed. If the enumerator stays indoors at case-close it still stalls — but by
then the respondent is done. A "GPS unavailable" reason code is the follow-up
(deferred until the pretest window closes; it needs a .dcf change).

This deliberately reverses the 2026-06-12 rule recorded in F3/F4's
generate_fmf.py ("GPS stays early so it auto-locks while the form is worked").
Indoors, that assumption never held.

ORDERING INVARIANT (changed by this script — read before touching either)
-------------------------------------------------------------------------
inject_field_control_end.py used to assert "the Verification Photo MUST remain
the very last form". That is no longer true: GPS is last, photo second-to-last.
The invariant that actually matters is unchanged and still enforced there:
Field Control (which collects ENUM_RESULT_FINAL_VISIT) must sit immediately
BEFORE the photo, whose preproc gates on that value. GPS has no gate of its
own, so it is safe after the photo.

WHY A FORM MOVE IS SAFE (no dictionary change)
----------------------------------------------
Form order is already decoupled from .dcf item order across these instruments.
F1's own REC_FACILITY_CAPTURE record already splits across two far-apart forms:
GPS (items 1-6) on the "Facility GPS" form, photo (items 7-9) on the "Case
Verification Photo" form. So no item moves, no start position shifts, and
synced + in-progress cases are unaffected — case data binds to dictionary
items, not form positions.

POST-PROCESSOR, not a hand-edit (IRON-RULE compliant). The .fmf binds each
[Group] to a [Form] by a 1-based ordinal (Form=N -> the Nth form, named
FORM{N-1:03d}); presentation order follows the [Group] order. So we move BOTH
the Facility GPS [Form] block and its [Group] block to just after the photo,
then RE-DERIVE every form ordinal from position (FORM Name= + every
Group/Field Form=).

Moving a whole [Form]+[Group] pair intact does not disturb inject_blocks.py's
[Block] Position math: Position = start_field_index + count_of_prior_blocks is
computed WITHIN a group, and the group's internals are untouched here.

Idempotent: when GPS is already last the move is a no-op and re-derivation
reproduces identical output. Run it LAST in the F1 .fmf pipeline:
fmf_checkbox_convert.py -> inject_blocks.py -> inject_case_key.py ->
inject_field_control_end.py -> inject_gps_end.py.

Run:  python inject_gps_end.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FMF = HERE / "FacilityHeadSurvey.fmf"

GPS_FORM_LABEL = "Facility GPS"                  # the Facility GPS [Form] Label=
PHOTO_FORM_LABEL = "Case Verification Photo"
GPS_GROUP_NAME = "REC_FACILITY_CAPTURE_FORM"     # the Facility GPS [Group] Name=
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


def _move_after(blocks, src_idx, anchor_needle):
    """Pop block at src_idx and reinsert it immediately AFTER the block that
    contains anchor_needle (recomputed after the pop)."""
    block = blocks.pop(src_idx)
    anchor = [i for i, b in enumerate(blocks) if anchor_needle in b][0]
    blocks.insert(anchor + 1, block)
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

    gps_form = _find_one(forms, f"Label={GPS_FORM_LABEL}", "Facility GPS form")
    ph_form = _find_one(forms, f"Label={PHOTO_FORM_LABEL}", "Verification Photo form")
    gps_grp = _find_one(groups, f"Name={GPS_GROUP_NAME}", "Facility GPS group")
    ph_grp = _find_one(groups, f"Name={PHOTO_GROUP_NAME}", "Verification Photo group")
    already = (gps_form == ph_form + 1) and (gps_grp == ph_grp + 1)

    forms = _move_after(forms, gps_form, f"Label={PHOTO_FORM_LABEL}")
    groups = _move_after(groups, gps_grp, f"Name={PHOTO_GROUP_NAME}")

    # --- re-derive every ordinal from final position ---
    for i, b in enumerate(forms):
        forms[i] = re.sub(r"(?m)^Name=FORM\d+", f"Name=FORM{i:03d}", b, count=1)
    for i, b in enumerate(groups):
        # every "^Form=N" in a group block (the [Group] header + each [Field])
        # links to that group's form; they all become i+1.
        groups[i] = re.sub(r"(?m)^Form=\d+", f"Form={i + 1}", b)

    # --- guard: GPS is now last, photo immediately before it ---
    if f"Label={GPS_FORM_LABEL}" not in forms[-1] or f"Name={GPS_GROUP_NAME}" not in groups[-1]:
        sys.exit("ERROR: Facility GPS did not land as the last form/group — aborting.")
    if f"Label={PHOTO_FORM_LABEL}" not in forms[-2] or f"Name={PHOTO_GROUP_NAME}" not in groups[-2]:
        sys.exit("ERROR: Verification Photo is not immediately before the GPS form — aborting.")

    out = prefix + "".join(forms) + mid + "".join(groups)
    FMF.write_text(out, encoding="utf-8")

    print(f"Relocated '{GPS_FORM_LABEL}' -> after '{PHOTO_FORM_LABEL}' in {FMF.name}")
    print(f"  forms/groups: {len(forms)} (1:1)")
    print(f"  new tail order: ... -> {PHOTO_FORM_LABEL} (FORM{len(forms) - 2:03d}, Form={len(forms) - 1})"
          f" -> {GPS_FORM_LABEL} (FORM{len(forms) - 1:03d}, Form={len(forms)})")
    print(f"  {'(was already in place — output identical, no structural change)' if already else 'moved + renumbered'}")


if __name__ == "__main__":
    main()
