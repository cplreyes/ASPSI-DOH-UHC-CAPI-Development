#!/usr/bin/env python3
r"""Insert the #1099 MM/DD/YYYY echo fields into F1's hand-maintained .fmf.

F3/F4 build their .fmf from generate_fmf.py, so their DATE_*_DISP echo fields
(read-only MM/DD/YYYY, computed in logic — Carl 2026-08-05) land automatically.
F1's .fmf is hand-maintained: this post-processor adds the two fields under the
visit dates on the Field Control form —

    DATE_FIRST_VISITED_THE_FACILITY      -> + DATE_FIRST_VISITED_DISP
    DATE_OF_FINAL_VISIT_TO_THE_FACILITY  -> + DATE_FINAL_VISIT_DISP

Mechanics: each insertion adds a [Field]+[Text] paragraph pair one row (30px)
below its date, shifts every later Position= row in the FIELD_CONTROL [Group]
down by 30, grows the Field Control [Form] Size by 60 and appends the Item=
lines. The dictionary items + the noinput compute PROCs come from
generate_dcf.py / generate_apc.py (BESPOKE_PROCS).

Idempotent: exits as a no-op when DATE_FIRST_VISITED_DISP is already present.
Pipeline order: after inject_field_control_end.py (position-independent — it
locates everything by name and renumbering leaves Form= consistent).

Run:  python inject_date_display.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FMF = HERE / "FacilityHeadSurvey.fmf"

DATE1 = "DATE_FIRST_VISITED_THE_FACILITY"
DATE2 = "DATE_OF_FINAL_VISIT_TO_THE_FACILITY"
DISP1 = "DATE_FIRST_VISITED_DISP"
DISP2 = "DATE_FINAL_VISIT_DISP"
LABEL1 = "Date First Visited (MM/DD/YYYY)"
LABEL2 = "Date of Final Visit (MM/DD/YYYY)"
ROW = 30


def fail(msg):
    sys.exit(f"ERROR: {msg} — refusing to write.")


def main():
    text = FMF.read_text(encoding="utf-8")
    if DISP1 in text:
        print(f"{FMF.name}: echo fields already present — no-op.")
        return

    # ---- 1) Field Control [Form] block: Item= lines + Size ----
    m_form = re.search(r"\[Form\](?:(?!\[EndForm\]).)*?Label=Field Control.*?\[EndForm\]",
                       text, re.S)
    if not m_form:
        fail("Field Control [Form] block not found")
    form = m_form.group(0)
    for date, disp in ((DATE1, DISP1), (DATE2, DISP2)):
        if f"Item={date}\n" not in form:
            fail(f"Item={date} missing from the Field Control form")
        form = form.replace(f"Item={date}\n", f"Item={date}\nItem={disp}\n", 1)
    m_size = re.search(r"(?m)^Size=(\d+),(\d+)$", form)
    if not m_size:
        fail("Field Control form Size= not found")
    form = form.replace(m_size.group(0),
                        f"Size={m_size.group(1)},{int(m_size.group(2)) + 2 * ROW}", 1)
    text = text[:m_form.start()] + form + text[m_form.end():]

    # ---- 2) FIELD_CONTROL [Group]: insert field/text pairs + shift rows ----
    m_grp = re.search(r"\[Group\](?:(?!\[EndGroup\]).)*?Name=FIELD_CONTROL_FORM.*?\[EndGroup\]",
                      text, re.S)
    if not m_grp:
        fail("FIELD_CONTROL_FORM [Group] block not found")
    grp = m_grp.group(0)

    def field_para(name):
        m = re.search(
            rf"\[Field\]\nName={name}\nPosition=(\d+),(\d+),(\d+),(\d+)\n"
            rf"Item={name},\w+\nDataCaptureType=[^\n]+\nForm=(\d+)\n", grp)
        if not m:
            fail(f"[Field] paragraph for {name} not found in the group")
        return m

    inserts = []
    for date, disp, label in ((DATE1, DISP1, LABEL1), (DATE2, DISP2, LABEL2)):
        f = field_para(date)
        x1, y1, form_no = int(f.group(1)), int(f.group(2)), f.group(5)
        # the date's [Text] label paragraph (same row, label column)
        m_txt = re.search(rf"\[Text\]\nPosition=\d+,{y1 + 3},\d+,{y1 + 19}\nText=[^\n]*\n", grp)
        if not m_txt:
            fail(f"[Text] label for {date} (row y={y1}) not found")
        insert_at_end = m_txt.end()
        # skip the paragraph separator that follows the label so the pair stays whole
        m_sep = re.match(r"(?: \n)?(?:  \n)+", grp[insert_at_end:])
        if m_sep:
            insert_at_end += m_sep.end()
        pair = (f"[Field]\n"
                f"Name={disp}\n"
                f"Position={x1},{y1 + ROW},{x1 + 140},{y1 + ROW + 20}\n"
                f"Item={disp},FACILITYHEADSURVEY_DICT\n"
                f"DataCaptureType=TextBox\n"
                f"Form={form_no}\n"
                f"  \n"
                f"[Text]\n"
                f"Position=50,{y1 + ROW + 3},340,{y1 + ROW + 19}\n"
                f"Text={label}\n"
                f" \n"
                f"  \n")
        inserts.append((insert_at_end, y1, pair))

    # shift every Position row BELOW each insertion point by ROW (cumulative),
    # then splice the new paragraphs in (later offset first so indexes hold).
    def shift(gtext, y_after):
        def rep(m):
            x1, y1, x2, y2 = (int(g) for g in m.groups())
            if y1 > y_after:
                return f"Position={x1},{y1 + ROW},{x2},{y2 + ROW}"
            return m.group(0)
        return re.sub(r"Position=(\d+),(\d+),(\d+),(\d+)", rep, gtext)

    # Descending-row order: each shift's threshold is an ORIGINAL row y; shifting
    # bottom-up means a row between the two dates moves exactly once (+30) and
    # rows below both move twice (+60). Ascending order would double-shift the
    # second date itself. Threshold +25: a row's [Text] label sits at field-y+3,
    # so the cutoff must clear the whole field+label pair or the pair tears.
    for _, y_row, _ in sorted(inserts, key=lambda t: -t[1]):
        grp = shift(grp, y_row + 25)
    # re-locate insertion anchors AFTER shifting (labels moved): recompute from names
    for date, disp, label in ((DATE2, DISP2, LABEL2), (DATE1, DISP1, LABEL1)):
        f = field_para(date)
        x1, y1, form_no = int(f.group(1)), int(f.group(2)), f.group(5)
        m_txt = re.search(rf"\[Text\]\nPosition=\d+,{y1 + 3},\d+,{y1 + 19}\nText=[^\n]*\n", grp)
        if not m_txt:
            fail(f"[Text] label for {date} not re-found after shift")
        at = m_txt.end()
        m_sep = re.match(r"(?: \n)?(?:  \n)+", grp[at:])
        if m_sep:
            at += m_sep.end()
        pair = (f"[Field]\n"
                f"Name={disp}\n"
                f"Position={x1},{y1 + ROW},{x1 + 140},{y1 + ROW + 20}\n"
                f"Item={disp},FACILITYHEADSURVEY_DICT\n"
                f"DataCaptureType=TextBox\n"
                f"Form={form_no}\n"
                f"  \n"
                f"[Text]\n"
                f"Position=50,{y1 + ROW + 3},340,{y1 + ROW + 19}\n"
                f"Text={label}\n"
                f" \n"
                f"  \n")
        grp = grp[:at] + pair + grp[at:]

    text = text[:m_grp.start()] + grp + text[m_grp.end():]

    # ---- guards ----
    for disp in (DISP1, DISP2):
        if text.count(f"Name={disp}") != 1:
            fail(f"expected exactly one Name={disp} after injection")
        if text.count(f"Item={disp}") != 2:  # form Item= list + group [Field] Item=
            fail(f"expected exactly two Item={disp} lines after injection")

    FMF.write_text(text, encoding="utf-8")
    print(f"Injected {DISP1} + {DISP2} into {FMF.name} "
          f"(rows +{ROW} each, Field Control form height +{2 * ROW}).")


if __name__ == "__main__":
    main()
