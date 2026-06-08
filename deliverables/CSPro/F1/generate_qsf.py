#!/usr/bin/env python3
"""
F1 Facility Head Survey — question-text (.qsf) generator.

Multi-language CAPI prompts. CSPro form field labels ([Text] in the .fmf) are
single-language and CSPro does NOT auto-translate them; the per-language channel is
the QUESTION TEXT (.qsf), shown in the question-text bar above the form. This reads
the generated FacilityHeadSurvey.dcf (which already carries every declared language
and its translated labels, via generate_dcf.py's apply_translations) and emits one
question per item with the prompt in every language. English is the fallback.

CSPro 8.0 .qsf: each language maps directly to the HTML text (block scalar); the
{format, text} sub-map is an 8.1+ schema and trips "yaml-cpp: bad conversion" on 8.0.

Invoke:  python generate_qsf.py    # writes FacilityHeadSurvey.ent.qsf  (run after generate_dcf.py)
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
DCF = HERE / "FacilityHeadSurvey.dcf"
OUT = HERE / "FacilityHeadSurvey.ent.qsf"

STYLES = """styles:
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
      font-family: Arial;font-size: 18px;"""


def _html(text):
    t = (text or "").replace("\n", " ").replace("\r", " ").strip()
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<p>{t}</p>"


def main():
    d = json.loads(DCF.read_text(encoding="utf-8"))
    dict_name = d.get("name", "FACILITYHEADSURVEY_DICT")
    langs = [(l["name"], l.get("label", l["name"]))
             for l in (d.get("languages") or [{"name": "EN", "label": "English"}])]

    lines = ["---", "fileType: Question Text", "version: CSPro 8.0", "languages:"]
    for nm, lb in langs:
        lines += [f"  - name: {nm}", f"    label: {lb}"]
    lines.append(STYLES)
    lines.append("questions:")

    seen, n = set(), 0
    for lvl in d["levels"]:
        for rec in lvl.get("records", []):
            for it in rec.get("items", []):
                nm = it["name"]
                if nm in seen:
                    continue
                seen.add(nm)
                labmap = {l.get("language"): l.get("text", "") for l in (it.get("labels") or [])}
                en = labmap.get("EN") or nm
                lines += [f"  - name: {dict_name}.{nm}", "    conditions:", "      - questionText:"]
                for lnm, _ in langs:
                    lines += [f"          {lnm}: |", f"            {_html(labmap.get(lnm) or en)}"]
                n += 1
    lines.append("...")
    OUT.write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({n} questions x {len(langs)} languages)")


if __name__ == "__main__":
    main()
