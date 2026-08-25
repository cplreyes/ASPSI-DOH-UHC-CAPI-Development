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
Nothing to restore: the field is now Q150_HR_CHALL_OTHER_TXT (Aug-17 renumber) and is
an ordinary generated field. The failure mode this repaired - a Designer compile+save
silently deleting a form field it judged an orphan - cannot persist, because the .fmf
is rebuilt from the dictionary on every build.
========================================================================
Restore Q163_HR_CHALL_OTHER_TXT's form field in F1's hand-maintained .fmf.

2026-08-05 (#1037): while the dictionary was transiently missing the
Q163_HR_CHALL_OTHER_TXT item (the checkbox_multiselect specify-detection only
looked at the LAST option, and the paper-ordered Q163 put "I don't know" after
"Other (specify)"), a Designer compile+save treated the bound form field as an
orphan and silently deleted it from the .fmf. The dictionary side is fixed
(cspro_helpers detection is position-independent now); this post-processor
re-adds the form field + label, verbatim from the last committed geometry,
bound to Q163_HR_CHALL's current form ordinal.

Idempotent: no-op when the field is already present.
Run:  python inject_q163_other_txt.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FMF = HERE / "FacilityHeadSurvey.fmf"
NAME = "Q163_HR_CHALL_OTHER_TXT"
BASE = "Q163_HR_CHALL"
LABEL = "163. What challenges in human resources do you have? — Other (specify) text"


def fail(msg):
    sys.exit(f"ERROR: {msg} — refusing to write.")


def main():
    text = FMF.read_text(encoding="utf-8")
    if f"Name={NAME}" in text:
        print(f"{FMF.name}: {NAME} already present — no-op.")
        return

    # [Form] block: Item= line after the base's
    m_form = re.search(r"\[Form\](?:(?!\[EndForm\]).)*?Item=Q163_HR_CHALL\n.*?\[EndForm\]",
                       text, re.S)
    if not m_form:
        fail("form block with Item=Q163_HR_CHALL not found")
    form = m_form.group(0)
    if f"Item={NAME}\n" not in form:
        form = form.replace("Item=Q163_HR_CHALL\n",
                            f"Item=Q163_HR_CHALL\nItem={NAME}\n", 1)
    text = text[:m_form.start()] + form + text[m_form.end():]

    # the base's [Field] paragraph: ordinal + its [Text], insert the pair after
    m_base = re.search(
        rf"\[Field\]\nName={BASE}\nPosition=(\d+),(\d+),(\d+),(\d+)\n"
        rf"Item={BASE},\w+\n(?:[^\n\[]+\n)*Form=(\d+)\n", text)
    if not m_base:
        fail(f"[Field] paragraph for {BASE} not found")
    y_base = int(m_base.group(2))
    form_no = m_base.group(5)

    m_txt = re.search(
        rf"\[Text\]\nPosition=\d+,{y_base + 3},\d+,{y_base + 19}\nText=[^\n]*163[^\n]*\n",
        text)
    if not m_txt:
        fail(f"[Text] label for {BASE} (row y={y_base}) not found")
    at = m_txt.end()
    m_sep = re.match(r"(?: \n)?(?:  \n)+", text[at:])
    if m_sep:
        at += m_sep.end()

    y = y_base + 30   # committed geometry: the specify row sits one row below the base
    pair = (f"[Field]\n"
            f"Name={NAME}\n"
            f"Position=1202,{y},2172,{y + 20}\n"
            f"Item={NAME},FACILITYHEADSURVEY_DICT\n"
            f"UseUnicodeTextBox=Yes\n"
            f"DataCaptureType=TextBox\n"
            f"Form={form_no}\n"
            f"  \n"
            f"[Text]\n"
            f"Position=50,{y + 3},544,{y + 19}\n"
            f"Text={LABEL}\n"
            f" \n"
            f"  \n")
    text = text[:at] + pair + text[at:]

    if text.count(f"Name={NAME}") != 1 or text.count(f"Item={NAME}") != 2:
        fail("post-injection counts wrong")
    FMF.write_text(text, encoding="utf-8")
    print(f"Restored {NAME} (Form={form_no}, row y={y}) in {FMF.name}.")


if __name__ == "__main__":
    raise SystemExit(
        "RETIRED 2026-08-19 - superseded by F1/generate_fmf.py; this script must NOT be run.\n"
        "It anchors on pre-Aug-17 field names and geometry, so against the current instrument\n"
        "it would either abort or silently mis-place fields in a file that is now rebuilt from\n"
        "the dictionary on every build. See the module docstring for the invariant it used to\n"
        "enforce and where that invariant lives today.")
