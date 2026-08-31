#!/usr/bin/env python3
"""aug21_english_delta.py — does each build's numbered English match the Aug-21 paper?

Re-runs the 2026-08-25 measurement as a REPORT (not a gate — see Pre-flight
rulings below): for F1/F3/F4 the dcf item labels that start with a question
number; for F2 the `label: { en: ... }` of every top-level `id: 'Qn'` /
`id: 'Qn_m'` item in items.ts (nested subFields are NOT items). Paper side =
every "N. ..." / "N.m ..." line of the Aug-21 English PDF (PyMuPDF), ALL
occurrences kept because the papers re-use question numbers for option lists
and definitions.
Match = ANY paper occurrence starts with the build stem (both normalised).
Writes <out>/<inst>_english_delta.json and prints one table. Nothing is modified.

    python aug21_english_delta.py                 # all four — F3 uses the generator dict
    python aug21_english_delta.py --only F3 --out out-delta
    python aug21_english_delta.py --only F3 --generator F3   # same as above, explicit

Wave tasks (16, 25, 38) re-run this before every extraction (spec Risks row 3).

Pre-flight ruling (2026-08-25): F3 is measured on the pre-neutralise GENERATOR
dictionary (migrate_maps_namekeys.capture_source_dict — the same call Task 1's
extractor uses), never on the written PatientSurvey.dcf, because
generate_dcf.py's post-apply pass (#714 facility-placeholder neutralisation)
rewrites the built labels. F1/F4 keep the written-dcf path.

Fix round 1 (2026-08-25, finding 1): F3 now measures the generator dict by
DEFAULT — the reconciled interface says "F3 anchors: always --generator F3,
never the written PatientSurvey.dcf", so the bare `python
aug21_english_delta.py` baseline the brief's Step 5 runs must not silently
fall back to the wrong (written-dcf) measurement. `--generator F3` is still
accepted (for explicit/self-documenting invocations) but no longer FILTERS
the instrument list down to F3 alone — passing it used to make F1/F2/F4
vanish from the run entirely, so no single command could produce a correct
four-instrument table. It is now purely a (redundant, since F3 already
defaults this way) measurement-method selector, never a `--only` filter.

This tool never exits non-zero except on missing inputs (a diff count is
signal for the wave note, not a failing build).
"""
import argparse
import io
import json
import os
import re
import sys

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(CSPRO, "..", ".."))
sys.path.insert(0, CSPRO)
sys.path.insert(0, HERE)
from cspro_helpers import walk_labeled_nodes  # noqa: E402
from textnorm import norm  # noqa: E402

ENGLISH_DIR = os.path.join(REPO, "raw", "Survey-Instruments-2026-08-21", "English")
BUILDS = {
    "F1": os.path.join(CSPRO, "F1", "FacilityHeadSurvey.dcf"),
    "F2": os.path.join(REPO, "deliverables", "F2", "PWA", "app", "src", "generated", "items.ts"),
    "F3": os.path.join(CSPRO, "F3", "PatientSurvey.dcf"),
    "F4": os.path.join(CSPRO, "F4", "HouseholdSurvey.dcf"),
}
# instrument -> generator script whose pre-apply source dict this tool ALWAYS measures
# instead of the written .dcf (bypasses post-apply rewrites like F3's facility-placeholder
# neutralisation). F3 only — F1/F4 keep the written-dcf path per the Task 0 pre-flight
# ruling. Membership here (not the --generator CLI flag) decides the method (fix round 1).
GENERATORS = {"F3": "generate_dcf.py"}
QNUM_LABEL = re.compile(r"^\s*(\d{1,3}(?:\.\d)?)\.?\s+(.*)$")
# integers need the dot ("1. What…"); decimals may omit it ("97.1 Other…" vs "115.1. Other…")
QNUM_LINE_INT = re.compile(r"^(\d{1,3})\.\s+(\S.*)$")
QNUM_LINE_DEC = re.compile(r"^(\d{1,3}\.\d)\.?\s+(\S.*)$")
# top-level items only: `section:` follows the id (after an optional displayNumber);
# nested subFields carry no `section:` and are skipped by construction. Letter-suffixed
# top-level ids (Q71a, Q71b — items.ts:139-140; real questions, `section: 'G'`, NOT
# subFields) also fall outside `\d{1,3}(?:_\d)?` and are excluded here too, but for a
# different reason than subFields (fix round 1, finding 2 — the exclusion is correct,
# the original patch-note rationale calling them "subFields" was not): the Aug-21 paper
# itself renders "71a."/"71b." as un-numbered sub-labels folded into Q71's own paper
# occurrence ("71. If yes, what are the implications? / 71a. <For those who answered
# 'Yes' in Q69> / 71b. <...Q70>") — there is no independently-numbered paper entry to
# gate Q71a/Q71b against either, so they are out of the numbered-English gate by design
# on both sides, not a coverage gap this regex should be widened to close.
ITEM_RE = re.compile(
    r"\{ id: 'Q(\d{1,3}(?:_\d)?)',(?: displayNumber: '[^']*',)? section: '[A-Z]'"
    r".*?label: \{ en: '((?:[^'\\]|\\.)*)'", re.S)


def numbered_labels_dict(d):
    """{qnum: first labels[0].text} from an already-loaded CSPro dictionary object."""
    out = {}
    for key, node in walk_labeled_nodes(d):
        if not key.startswith("item:") or key.endswith("_TXT"):
            continue
        labs = node.get("labels") or []
        if not labs:
            continue
        m = QNUM_LABEL.match(labs[0].get("text") or "")
        if m and m.group(1) not in out:
            out[m.group(1)] = labs[0]["text"].strip()
    return out


def numbered_labels_dcf(dcf_path):
    d = json.load(io.open(dcf_path, encoding="utf-8"))
    return numbered_labels_dict(d)


def numbered_labels_generator(inst):
    """Pre-apply source dictionary captured from a live generator run — see
    module docstring. Reuses migrate_maps_namekeys.capture_source_dict exactly
    as Task 1's extractor does, so both tools measure the same dictionary."""
    import migrate_maps_namekeys as mmn
    d = mmn.capture_source_dict(inst, GENERATORS[inst])
    return numbered_labels_dict(d)


def numbered_labels_items_ts(path):
    src = io.open(path, encoding="utf-8").read()
    out = {}
    for m in ITEM_RE.finditer(src):
        q = m.group(1).replace("_", ".")
        if q not in out:
            out[q] = m.group(2).replace("\\'", "'").replace("\\n", " ")
    return out


def paper_numbered(pdf_path):
    """{qnum: [text of every occurrence, in page order]}."""
    doc = fitz.open(str(pdf_path))
    lines = []
    for page in doc:
        lines.extend(page.get_text().split("\n"))
    doc.close()
    out, cur = {}, None
    for ln in lines:
        ln = " ".join(ln.split())
        m = QNUM_LINE_DEC.match(ln) or QNUM_LINE_INT.match(ln)
        if m:
            cur = m.group(1)
            out.setdefault(cur, []).append(m.group(2))
        elif cur and ln:
            out[cur][-1] = out[cur][-1] + " " + ln
    return {q: [" ".join(t.split()) for t in ts] for q, ts in out.items()}


def compare(build, paper):
    diffs, match = [], 0
    for q, label in sorted(build.items(), key=lambda kv: float(kv[0])):
        stem = norm(re.sub(r"^\s*\d{1,3}(?:\.\d)?\.?\s*", "", label))
        stem = re.split(r" (?:hours|minutes|specify text)$", stem)[0]
        occ = paper.get(q)
        if not occ:
            diffs.append({"q": q, "build": label, "paper": None})
            continue
        if any(norm(p).startswith(stem[:60]) for p in occ):
            match += 1
        else:
            diffs.append({"q": q, "build": label, "paper": [p[:240] for p in occ]})
    paper_only = sorted((q for q in paper if q not in build), key=float)
    return {"match": match, "total": len(build), "diffs": diffs, "paper_only": paper_only}


def english_pdf(inst):
    names = sorted(n for n in os.listdir(ENGLISH_DIR) if n.startswith(f"{inst}-English") and n.endswith(".pdf"))
    return os.path.join(ENGLISH_DIR, names[0]) if names else None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=sorted(BUILDS))
    ap.add_argument("--generator", choices=sorted(GENERATORS),
                     help="F3 always measures its pre-apply GENERATOR dictionary, with "
                          "or without this flag (fix round 1); accepted for explicit/"
                          "self-documenting invocations, but it selects the measurement "
                          "METHOD for that instrument only — it does not filter --only")
    ap.add_argument("--out", default=os.path.join(HERE, "out-delta"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    print("%-4s %6s %6s %6s %10s" % ("inst", "match", "total", "diffs", "paper-only"))
    rc = 0
    insts = (a.only,) if a.only else sorted(BUILDS)
    for inst in insts:
        pdf = english_pdf(inst)
        if pdf is None:
            print(f"{inst:<4} no Aug-21 English PDF under {ENGLISH_DIR}"); rc = 1; continue
        # F3 ALWAYS measures the pre-apply generator dict (GENERATORS membership decides
        # this, not the --generator flag) so the bare, no-flag baseline is never wrong;
        # the flag is accepted but no longer filters the instrument list (fix round 1).
        use_generator = inst in GENERATORS
        if inst == "F2":
            build = numbered_labels_items_ts(BUILDS[inst])
        elif use_generator:
            build = numbered_labels_generator(inst)
        else:
            build = numbered_labels_dcf(BUILDS[inst])
        r = compare(build, paper_numbered(pdf))
        r["build"] = f"{BUILDS[inst]} (generator: {GENERATORS[inst]})" if use_generator else BUILDS[inst]
        r["paper"] = pdf
        with io.open(os.path.join(a.out, f"{inst.lower()}_english_delta.json"), "w", encoding="utf-8",
                     newline="\n") as fh:
            json.dump(r, fh, ensure_ascii=False, indent=1)
        print("%-4s %6d %6d %6d %10d" % (inst, r["match"], r["total"], len(r["diffs"]), len(r["paper_only"])))
        for x in r["diffs"]:
            first = (x["paper"] or [""])[0] if isinstance(x["paper"], list) else (x["paper"] or "")
            print(f"   Q{x['q']}: build={x['build'][:80]!r}\n         paper={first[:80]!r}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
