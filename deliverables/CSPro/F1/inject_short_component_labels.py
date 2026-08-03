#!/usr/bin/env python3
"""Shorten the ON-FORM labels of split month/year components in F1's static
FacilityHeadSurvey.fmf.  (Pretest finding #1006, Option A.)

WHY THIS EXISTS
---------------
Q5 and Q6 are each split into two dictionary items, and each item's label
carries the FULL question stem:

    Q5_YEARS_AT_FACILITY   "5. In your current position, how many months/years
                            have you worked at this health facility?
                            Number of Years"
    Q5_MONTHS_AT_FACILITY  "5. ...same stem... Number of Months"

That one label is consumed TWICE on screen: generate_qsf.py uses it as the CAPI
question-bar prompt, and the .fmf [Text] uses it as the on-form field label. So
the stem printed twice per screen and four times across the pair -- the tester's
report ("the full question text for each component is repeating", #1006), and
the same root cause as the DOH reviewer's "question text displayed twice" (#888).

Option A (chosen 2026-08-03): shorten the ON-FORM label to just the component
name and leave the full stem in the question bar above it. The stem then appears
ONCE per screen, with "Number of Years" / "Number of Months" sitting directly
over the entry box -- the layout in the tester's reference screenshots.

Deliberately NOT changed: the DICTIONARY labels. Those are the variable labels
in the exported data and the published codebook; shortening them would leave Q5
and Q6 both carrying an ambiguous "Number of Months" in the dataset. Display
text and data labels diverge here on purpose.

Option B (blocking each pair onto one screen for true Household parity) was
considered and declined mid-pretest -- it changes Section A's entry flow and
moves where the ">= 6 months tenure" termination check fires.

This is a POST-PROCESSOR, not a hand-edit (IRON-RULE compliant): it rewrites the
[Text] that follows each named [Field], and re-fits the label box width. F1's
.fmf is hand-authored with no generator, so on-form text has to be set here.

Idempotent: re-running is a no-op once every label already matches. Run it in
the F1 .fmf pipeline after the field-level injectors:

    python generate_dcf.py
    python inject_case_key.py
    python inject_q2_other_txt.py
    python inject_short_component_labels.py    <-- here
    python inject_blocks.py
    ...

Run:  python inject_short_component_labels.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FMF = HERE / "FacilityHeadSurvey.fmf"

# field name -> the short on-form label that replaces the full stem
SHORT_LABELS = {
    "Q5_YEARS_AT_FACILITY":  "Number of Years",
    "Q5_MONTHS_AT_FACILITY": "Number of Months",
    "Q6_YEARS_HEALTH":       "Number of Years",
    "Q6_MONTHS_HEALTH":      "Number of Months",
}

LABEL_X = 50
PX_PER_CHAR = 6.4    # averaged from this form's existing [Text] rows


def parse_pos(s):
    return [int(x) for x in s.split(",")]


def main():
    if not FMF.exists():
        sys.exit("ERROR: FacilityHeadSurvey.fmf not found.")

    text = FMF.read_text(encoding="utf-8")  # keeps the BOM as a leading char
    lines = text.split("\n")

    changed = []
    for name, short in SHORT_LABELS.items():
        # locate the [Field] block for this item (not the [Form] roster line)
        field_at = None
        for i, ln in enumerate(lines):
            if ln.strip() == f"Name={name}" and i and lines[i - 1].strip() == "[Field]":
                field_at = i
                break
        if field_at is None:
            sys.exit(f"ERROR: [Field] {name} not found -- .fmf changed shape.")

        # advance to the [Text] block that follows it
        j = field_at
        while j < len(lines) and lines[j].strip() != "[Text]":
            if lines[j].strip() == "[Field]" and j > field_at:
                sys.exit(f"ERROR: {name} has no [Text] label block.")
            j += 1
        pos_at = txt_at = None
        k = j + 1
        while k < len(lines) and not lines[k].strip().startswith("["):
            s = lines[k].strip()
            if s.startswith("Position=") and pos_at is None:
                pos_at = k
            elif s.startswith("Text=") and txt_at is None:
                txt_at = k
            k += 1
        if txt_at is None:
            sys.exit(f"ERROR: {name}'s [Text] block has no Text= line.")

        if lines[txt_at] == f"Text={short}":
            continue                                   # already short -- no-op
        changed.append((name, lines[txt_at][len("Text="):], short))
        lines[txt_at] = f"Text={short}"
        if pos_at is not None:                         # re-fit the label box
            p = parse_pos(lines[pos_at].strip()[len("Position="):])
            p[2] = LABEL_X + int(len(short) * PX_PER_CHAR)
            lines[pos_at] = "Position=" + ",".join(str(x) for x in p)

    if not changed:
        print("All component labels already short -- no-op.")
        return

    FMF.write_text("\n".join(lines), encoding="utf-8")
    print(f"Shortened {len(changed)} on-form label(s):")
    for name, old, new in changed:
        print(f"  {name}")
        print(f"    was: {old}")
        print(f"    now: {new}")
    print("Dictionary labels untouched -- question bar + codebook keep the full stem.")


if __name__ == "__main__":
    main()
