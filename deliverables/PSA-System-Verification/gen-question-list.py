#!/usr/bin/env python3
"""Generate a complete, SECTIONED question list per CAPI instrument straight from
its CSPro data dictionary (.dcf) — the source of truth for what the *deployed* app
asks. Emits Markdown (for the guides) and an HTML fragment (for the web doc).

Usage:  python gen-question-list.py            # writes all instruments
Outputs (in this folder):
  <KEY>-Full-Question-List.md   and   _qlist_<KEY>.html
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DCF_BASE = HERE.parent / "CSPro"

INSTRUMENTS = {
    "F1": ("F1/FacilityHeadSurvey.dcf", "F1 — Facility Head Survey"),
    "F3": ("F3/PatientSurvey.dcf", "F3 — Patient Survey"),
    "F4": ("F4/HouseholdSurvey.dcf", "F4 — Household Survey"),
}

QNUM = re.compile(r"^Q(\d+)")
OPTFLAG = re.compile(r"_O\d+$")
DASH = re.compile(r"\s+[—–]\s+")  # em / en dash separating "base — option"


def en(o):
    for l in (o.get("labels") or []):
        if l.get("language") == "EN":
            return (l.get("text") or "").strip()
    ls = o.get("labels") or [{}]
    return (ls[0].get("text") or "").strip()


def base(label):
    return DASH.split(label, 1)[0].strip()


def opt(label):
    p = DASH.split(label, 1)
    return p[1].strip() if len(p) == 2 else None


def qkey(name):
    m = QNUM.match(name)
    return "Q" + m.group(1) if m else None


def group_items(items):
    """Group consecutive items sharing a Q-number; non-Q items stand alone."""
    groups = []
    for it in items:
        k = qkey(it["name"])
        if k and groups and groups[-1]["key"] == k:
            groups[-1]["items"].append(it)
        else:
            groups.append({"key": k, "items": [it]})
    return groups


def describe(group):
    its = group["items"]
    flags = [x for x in its if OPTFLAG.search(x["name"])]
    main = (flags or its)[0]
    text = base(en(main))
    if flags:                       # select-all: one item per option
        choices = [opt(en(x)) for x in flags if opt(en(x))]
        return text, "select all that apply", choices
    vs = main.get("valueSets")
    if vs:                          # single-choice value set
        return text, "select one", [en(v) for v in vs[0].get("values", [])]
    ct = main.get("contentType")
    if ct == "numeric":
        return text, "number", []
    return text, "text", []


def records(key):
    path, _ = INSTRUMENTS[key]
    d = json.load(open(DCF_BASE / path, encoding="utf-8"))
    return d["levels"][0]["records"]


def md_for(key):
    _, title = INSTRUMENTS[key]
    lines = [f"# {title} — Complete Question List", "",
             "Every question the deployed app asks, in order, grouped by section — "
             "generated directly from the CSPro data dictionary so it matches the live "
             "instrument exactly. Question numbers follow the official questionnaire.", ""]
    nq = 0
    for rec in records(key):
        items = rec.get("items", [])
        if not items:
            continue
        lines.append(f"## {en(rec)}")
        lines.append("")
        for g in group_items(items):
            text, qtype, choices = describe(g)
            nq += 1
            row = f"- **{text}**  _({qtype})_"
            if choices:
                row += "\n  - " + " · ".join(choices)
            lines.append(row)
        lines.append("")
    lines.append(f"*Total: {nq} questions/fields across the instrument.*")
    return "\n".join(lines) + "\n", nq


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def html_for(key):
    _, title = INSTRUMENTS[key]
    parts = []
    nq = 0
    for rec in records(key):
        items = rec.get("items", [])
        if not items:
            continue
        parts.append(f'<details><summary>{esc(en(rec))}</summary><ul class="qlist">')
        for g in group_items(items):
            text, qtype, choices = describe(g)
            nq += 1
            li = f'<li><strong>{esc(text)}</strong> <span class="qt">({esc(qtype)})</span>'
            if choices:
                li += '<div class="qopts">' + " · ".join(esc(c) for c in choices) + "</div>"
            li += "</li>"
            parts.append(li)
        parts.append("</ul></details>")
    return "\n".join(parts), nq


if __name__ == "__main__":
    summary = []
    for key in INSTRUMENTS:
        md, nq = md_for(key)
        (HERE / f"{key}-Full-Question-List.md").write_text(md, encoding="utf-8")
        html, _ = html_for(key)
        (HERE / f"_qlist_{key}.html").write_text(html, encoding="utf-8")
        summary.append(f"{key}: {nq} questions/fields -> {key}-Full-Question-List.md + _qlist_{key}.html")
    print("\n".join(summary))
