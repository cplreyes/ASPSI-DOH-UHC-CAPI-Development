#!/usr/bin/env python3
r"""Move F3/F4's Informed Consent form to the SECOND slot, right after the case key.

WHY THIS EXISTS
---------------
Aly asked on 2026-08-14 for the ICF to sit immediately after the Questionnaire
Number. generate_fmf.py's FORM_PLAN was reordered for that, which fixes the
GENERATED file — but the file the build and the .pen actually use is the live
PatientSurvey.fmf / HouseholdSurvey.fmf, which is the generated output PLUS
Designer layout polish (F3: ~7KB more than its generated twin, same 39 forms).
No script writes those, so a generator-only change does not reach the device
until somebody re-imports in Designer, and re-importing throws the polish away.

So the form order is moved the same way every other F1 form-level change is
made: a programmatic, idempotent post-processor. Same pattern and rationale as
F1's inject_icf.py — we never hand-edit the .fmf.

WHAT IT DOES
------------
1. Splits the file into [Form] and [Group] sections, each block carrying its own
   trailing whitespace so a rejoin is byte-lossless. (F1's split_sections drops
   inter-block text; harmless there, avoided here.)
2. Verifies the invariant this rewrite depends on: len(forms) == len(groups), and
   the k-th group owns the k-th form. Refuses to touch the file otherwise.
3. Moves the ICF form AND its A_INFORMED_CONSENT_FORM group to index 1.
4. Renumbers EVERY `Form=` from position. A group's `Form=N` is the 1-BASED
   ORDINAL of the form section, not an id, so moving a form silently points every
   later group at the wrong form unless all are rewritten.

Idempotent: if the ICF is already second, it reports and changes nothing.

KNOWN AND ACCEPTED CONSEQUENCE
------------------------------
PROC BREAKOFF does `skip to ENUM_RESULT_FINAL_VISIT` for codes 5/6/7 (refused at
door / not found / ineligible), so a case that never started used to jump the ICF
entirely. With consent ahead of that control the enumerator now walks both
read-aloud consent screens before closing out such a case. Carl chose this over
keeping the break-off escape — see decisions/2026-08-14-icf-placement.png.

    python reorder_icf_form.py            # rewrites both .fmf files in place
    python reorder_icf_form.py --check    # report only, exit 1 if not yet second
"""
import io
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

TARGETS = [
    ("F3", BASE / "F3" / "PatientSurvey.fmf"),
    ("F4", BASE / "F4" / "HouseholdSurvey.fmf"),
]

GROUP_NAME = "A_INFORMED_CONSENT_FORM"
FORM_LABEL_HINT = "Informed Consent"
TARGET_INDEX = 1          # 0-based: second form, immediately after the case key


def split_blocks(text, start_tag, end_tag):
    """-> (prefix, [block, ...], suffix), lossless.

    Each block runs from its start_tag to the NEXT start_tag, so whitespace
    between sections travels with the block it follows and "".join() round-trips.
    """
    first = text.find(start_tag)
    if first < 0:
        return text, [], ""
    last = text.rfind(end_tag) + len(end_tag)
    body, starts = text[first:last], []
    pos = 0
    while True:
        s = body.find(start_tag, pos)
        if s < 0:
            break
        starts.append(s)
        pos = s + len(start_tag)
    blocks = [body[starts[i]: starts[i + 1] if i + 1 < len(starts) else len(body)]
              for i in range(len(starts))]
    return text[:first], blocks, text[last:]


def process(inst, path, check_only):
    raw = io.open(path, encoding="utf-8-sig").read()

    head, forms, mid_and_rest = split_blocks(raw, "[Form]", "[EndForm]")
    mid, groups, tail = split_blocks(mid_and_rest, "[Group]", "[EndGroup]")

    if len(forms) != len(groups):
        print(f"  {inst}: FAIL {len(forms)} forms vs {len(groups)} groups — "
              "k-th-group-owns-k-th-form does not hold; refusing to renumber.")
        return False

    fi = next((i for i, f in enumerate(forms) if FORM_LABEL_HINT in f), None)
    gi = next((i for i, g in enumerate(groups) if f"Name={GROUP_NAME}" in g), None)
    if fi is None or gi is None:
        print(f"  {inst}: FAIL ICF form/group not found (form={fi}, group={gi})")
        return False
    if fi != gi:
        print(f"  {inst}: FAIL ICF form at {fi} but its group at {gi} — "
              "the ordinal invariant is already broken; refusing to touch it.")
        return False

    if fi == TARGET_INDEX:
        print(f"  {inst}: already second — no change")
        return True
    if check_only:
        print(f"  {inst}: ICF at form {fi + 1}, expected {TARGET_INDEX + 1}")
        return False

    forms.insert(TARGET_INDEX, forms.pop(fi))
    groups.insert(TARGET_INDEX, groups.pop(gi))
    # NOTE the anchor: `^Form=\d+$`, never `^Form=\d+\s*$`. In multiline mode `\s`
    # matches NEWLINES, so the \s* variant swallows the blank lines that follow
    # each match — and there are ~398 Form= lines per file, because every [Field]
    # carries its group's ordinal too. That cost F3 1,116 lines the first time.
    groups = [re.sub(r"(?m)^Form=\d+$", f"Form={k + 1}", g)
              for k, g in enumerate(groups)]

    out = head + "".join(forms) + mid + "".join(groups) + tail
    # CSPro .fmf files are CRLF. The read above uses universal newlines, so the
    # in-memory text is LF-only; writing with newline="" would emit LF and strip
    # every \r in the file (caught as a -1834 byte delta on F3 the first time).
    # newline="\r\n" translates back on the way out, exactly as inject_icf.py does.
    with io.open(path, "w", encoding="utf-8-sig", newline="\r\n") as fh:
        fh.write(out)

    print(f"  {inst}: moved ICF from form {fi + 1} -> {TARGET_INDEX + 1}; "
          f"renumbered Form= across {len(groups)} groups")
    return True


def main():
    check_only = "--check" in sys.argv
    print("ICF form position (target: form 2, straight after the case key / QN)")
    ok = True
    for inst, path in TARGETS:
        if not path.exists():
            print(f"  {inst}: FAIL missing {path.name}")
            ok = False
            continue
        ok &= process(inst, path, check_only)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
