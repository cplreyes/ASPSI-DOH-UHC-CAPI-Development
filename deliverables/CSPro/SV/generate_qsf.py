"""generate_qsf.py — SupervisorApp question-text (.qsf) generator.

Emits SupervisorApp.ent.qsf from SupervisorApp.dcf. EN-only (matches the dcf's single
language for v1). CSPro requires an 'entry' application to have exactly one question-text
file; each on-form item gets a <p>label</p> prompt. The off-form binary Image item is
excluded (no prompt). Iron rule: never hand-edit the .qsf — edit this generator and rerun.

Run:  python generate_qsf.py        # writes SupervisorApp.ent.qsf
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate_dcf import build_sv_dictionary
from cspro_helpers import _truncate_long_labels

OUT = Path(__file__).parent / "SupervisorApp.ent.qsf"
DICT_NAME = "SUPERVISORAPP_DICT"
OFF_FORM_ITEMS = {"VERIFICATION_PHOTO_IMAGE"}   # binary, off-form, no prompt

HEADER = """\
---
fileType: Question Text
version: CSPro 8.0
languages:
  - name: EN
    label: English
styles:
  - name: Normal
    className: normal
    css: |
      font-family: Arial;font-size: 16px;
  - name: Instruction
    className: instruction
    css: |
      font-family: Arial;font-size: 14px;color: #0000FF;
  - name: Heading 1
    className: heading1
    css: |
      font-family: Arial;font-size: 36px;
  - name: Heading 2
    className: heading2
    css: |
      font-family: Arial;font-size: 24px;
  - name: Heading 3
    className: heading3
    css: |
      font-family: Arial;font-size: 18px;
questions:"""


def _iter_items(d):
    level = d["levels"][0]
    for it in level["ids"]["items"]:
        yield it
    for rec in level["records"]:
        for it in rec["items"]:
            yield it


def build_qsf():
    d = build_sv_dictionary()
    _truncate_long_labels(d)
    lines = [HEADER]
    for it in _iter_items(d):
        if it["name"] in OFF_FORM_ITEMS:
            continue
        label = (it["labels"][0]["text"] if it.get("labels") else it["name"])
        label = label.replace("\n", " ").replace("\r", " ")
        lines.append(f"  - name: {DICT_NAME}.{it['name']}")
        lines.append("    conditions:")
        lines.append("      - questionText:")
        lines.append("          EN: |")
        lines.append(f"            <p>{label}</p>")
    return "\n".join(lines) + "\n"


def main():
    OUT.write_text("﻿" + build_qsf(), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
