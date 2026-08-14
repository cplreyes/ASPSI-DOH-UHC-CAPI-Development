#!/usr/bin/env python3
r"""Reverse inject_date_display.py: remove the #1099 MM/DD/YYYY echo fields.

#1132 retest (2026-08-10): ASPSI's reviewer circled both echo rows on-device as
confusing (four date rows for two dates) and asked for their removal. The
dictionary items and compute PROCs are gone from generate_dcf.py /
generate_apc.py in the same change; this strips the .fmf half:

  - the two Item=DATE_*_DISP lines in the Field Control [Form] (+ Size -60)
  - the two [Field]+[Text] paragraph pairs in the FIELD_CONTROL group
  - every Position= row below each removed row shifts back up 30px

Idempotent: no-op when DATE_FIRST_VISITED_DISP is absent.
Run:  python remove_date_display.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FMF = HERE / "FacilityHeadSurvey.fmf"
DISPS = [("DATE_FIRST_VISITED_DISP", "Date First Visited (MM/DD/YYYY)"),
         ("DATE_FINAL_VISIT_DISP", "Date of Final Visit (MM/DD/YYYY)")]
ROW = 30


def fail(msg):
    sys.exit(f"ERROR: {msg} — refusing to write.")


def main():
    text = FMF.read_text(encoding="utf-8")
    if "DATE_FIRST_VISITED_DISP" not in text:
        print(f"{FMF.name}: echo fields absent — no-op.")
        return

    # ---- 1) [Form]: drop Item= lines, shrink Size ----
    for disp, _ in DISPS:
        if f"Item={disp}\n" not in text:
            fail(f"Item={disp} line not found")
        text = text.replace(f"Item={disp}\n", "", 1)
    m_form = re.search(r"\[Form\](?:(?!\[EndForm\]).)*?Label=Field Control.*?\[EndForm\]",
                       text, re.S)
    if not m_form:
        fail("Field Control [Form] block not found")
    form = m_form.group(0)
    m_size = re.search(r"(?m)^Size=(\d+),(\d+)$", form)
    if not m_size:
        fail("Field Control form Size= not found")
    form = form.replace(m_size.group(0),
                        f"Size={m_size.group(1)},{int(m_size.group(2)) - 2 * ROW}", 1)
    text = text[:m_form.start()] + form + text[m_form.end():]

    # ---- 2) group: remove pairs, shift rows back up ----
    m_grp = re.search(r"\[Group\](?:(?!\[EndGroup\]).)*?Name=FIELD_CONTROL_FORM.*?\[EndGroup\]",
                      text, re.S)
    if not m_grp:
        fail("FIELD_CONTROL_FORM [Group] block not found")
    grp = m_grp.group(0)

    removed_rows = []
    for disp, label in DISPS:
        m_f = re.search(
            rf"\[Field\]\nName={disp}\nPosition=(\d+),(\d+),(\d+),(\d+)\n"
            rf"Item={disp},\w+\nDataCaptureType=[^\n]+\nForm=\d+\n(?:  \n)?", grp)
        if not m_f:
            fail(f"[Field] paragraph for {disp} not found")
        y = int(m_f.group(2))
        grp = grp[:m_f.start()] + grp[m_f.end():]
        m_t = re.search(
            rf"\[Text\]\nPosition=\d+,{y + 3},\d+,{y + 19}\nText={re.escape(label)}\n \n(?:  \n)?", grp)
        if not m_t:
            fail(f"[Text] label for {disp} (row y={y}) not found")
        grp = grp[:m_t.start()] + grp[m_t.end():]
        removed_rows.append(y)

    # Ascending order: rows between the two removed rows move up once (-30),
    # rows below both move up twice (-60) — the exact inverse of the inject.
    def unshift(gtext, y_after):
        def rep(m):
            x1, y1, x2, y2 = (int(g) for g in m.groups())
            if y1 > y_after:
                return f"Position={x1},{y1 - ROW},{x2},{y2 - ROW}"
            return m.group(0)
        return re.sub(r"Position=(\d+),(\d+),(\d+),(\d+)", rep, gtext)

    for y in sorted(removed_rows):
        grp = unshift(grp, y - 5)

    text = text[:m_grp.start()] + grp + text[m_grp.end():]

    for disp, _ in DISPS:
        if disp in text:
            fail(f"{disp} still present after removal")

    FMF.write_text(text, encoding="utf-8")
    print(f"Removed both echo fields from {FMF.name} (rows -{ROW} each, form height -{2 * ROW}).")


if __name__ == "__main__":
    main()
