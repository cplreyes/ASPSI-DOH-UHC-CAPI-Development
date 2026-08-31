#!/usr/bin/env python3
r"""Find poisoned entries in the (name-scoped) translation maps.

2026-08-17 v2 — rewritten for the name-scoped map format AND extended with the
wrong-question-text detectors the render-evidence run proved necessary: the F3
Waray Q2 slot held a fluent Waray EXPENSES question — untranslated-English scans
can never see that class, only comparison against the cleared corpus can.

Detectors, per map entry (key -> value):
  DOUBLED         value contains an adjacent repeated word-run ("NBB compliance NBB compliance").
                  2026-08-31 (#1363/#1378/#1380): a run the locale's Aug-21 paper prints VERBATIM
                  (text-aug21/<inst>_<LOC>.txt) is reduplication the translator wrote ("ababa a
                  panawen, panawen, kassual", "kangrunaan a kangrunaan a mangipapaay"), not a
                  doubled extraction - remediate_scan.py already LEAVES such rows. Those rows are
                  printed under "--- paper reduplication ---" and not raised, so the per-reason
                  delta gate no longer blocks a verbatim paper value. Not a waiver: nothing is
                  cited by hand, the paper text itself is the evidence, re-checked every run.
  SELF_ECHO       value == its node's source English (untranslated, masking a gap)
  IS_OTHER_EN     value == the source English of a DIFFERENT node
  EN_FRAGMENT     value contains a >=20-char different node's English (glued/spilled English)
  WRONG_Q_CLEARED value == the CLEARED translation (same locale) of a DIFFERENT question
  GLUED_CLEARED   value == the cleared translation of its OWN question + extra junk
  STALE_KEY       key no longer matches any node of the dictionary (post-edit orphan)

English per node comes from the PRE-APPLY source dictionary (captured the same way
the migrator does), because post-apply passes (#714) rewrite built labels.

Run:  python scan_poisoned_keys.py [--apply-report out.json]
NOTE: capturing the source dictionaries runs each generate_dcf.py, so the .dcf
files are regenerated (from the current maps) as a side effect.

WAIVERS (scan_waivers.json, Task 50 fix round 1) — SELF_ECHO/IS_OTHER_EN only.
Some Aug-21 papers print an option UNTRANSLATED (a proper noun: the Cebuano for
`LGU/Barangay` is `LGU/Barangay`). Importing that paper value is correct — it is what
the respondent sees on paper — but it necessarily makes the value equal an English
label, so the detector fires and run_aug21_gates.ps1 gate 1 refuses the wave. A waiver
is the narrow exemption for exactly those rows: per instrument, per locale, per key,
per reason, and PINNED TO THE VALUE (if the map value drifts the waiver stops covering
it). No other reason may be waived — DOUBLED / EN_FRAGMENT / WRONG_Q_CLEARED /
GLUED_CLEARED / STALE_KEY are corruption classes, never "the paper says so". Waived
rows are printed under `--- waived ---` and left OUT of the --apply-report JSON, which
is what makes the per-reason delta gate pass; a waiver that matched nothing is printed
as STALE so the file cannot rot silently.
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, CSPRO)
sys.path.insert(0, HERE)
from cspro_helpers import walk_labeled_nodes  # noqa: E402
from migrate_maps_namekeys import capture_source_dict  # noqa: E402

INSTR = ["F1", "F3", "F4"]
LOCALES = ("fil", "bcl", "bis", "ceb", "war", "hil", "ilo")
OFFICIAL = os.path.join(HERE, "official_translations.json")
WAIVERS_PATH = os.path.join(HERE, "scan_waivers.json")
# Only the two "value equals an English label" reasons. A paper that prints an option
# untranslated is a real, citable state of the world; every other detector describes a
# corruption, and a waiver for one of those would be a way to publish a known defect.
WAIVABLE_REASONS = ("SELF_ECHO", "IS_OTHER_EN")
LABEL_Q = re.compile(r"^\s*(\d{1,3}(?:\.\d)?)\s*[\.\)]")
NAME_Q = re.compile(r"^Q(\d{1,3})(?:_(\d))?_")
NUM_PREFIX = re.compile(r"^\s*\d{1,3}(?:\.\d)?\s*[\.\)]\s*")


def norm(s):
    return re.sub(r"\s+", " ", NUM_PREFIX.sub("", (s or "")).strip().casefold())


def doubled_run(v):
    """The adjacent repeated run of words (normalised text) anywhere in the value, or
    None (v1 heuristic, kept verbatim: it caught 'Publikong bus Taxi Taxi' post-deploy)."""
    w = norm(v).split()
    n = len(w)
    if n < 2:
        return None
    if n % 2 == 0 and w[: n // 2] == w[n // 2:]:
        return " ".join(w[: n // 2])
    for size in range(1, n // 2 + 1):
        for i in range(n - 2 * size + 1):
            a, b = w[i:i + size], w[i + size:i + 2 * size]
            if a == b and sum(len(x) for x in a) >= 4:
                return " ".join(a)
    return None


def doubled(v):
    return doubled_run(v) is not None


_PAPER = {}


def paper_reduplicated(inst, loc, run):
    """True when `run run` (the doubled text) occurs verbatim in the locale's Aug-21 paper
    dump - reduplication the translator wrote, not an extraction artefact. Whitespace is
    collapsed (the paper wraps lines) and the comparison is casefolded like norm()."""
    key = (inst, loc.upper())
    if key not in _PAPER:
        fp = os.path.join(HERE, "text-aug21", f"{inst}_{loc.upper()}.txt")
        txt = io.open(fp, encoding="utf-8").read() if os.path.exists(fp) else ""
        _PAPER[key] = re.sub(r"\s+", " ", txt).casefold()
    return bool(run) and (run + " " + run) in _PAPER[key]


def qnum_of(key, en):
    # Label number first: it carries sub-numbers the item name flattens
    # (Q61_DELAY_REASON is labeled "61.1." — name-first misfiled it as 61).
    m = LABEL_Q.match(en or "")
    if m:
        return m.group(1)
    stem = key.split(":", 1)[1] if ":" in key else key
    m = NAME_Q.match(stem)
    if m:
        return m.group(1) + (f".{m.group(2)}" if m.group(2) else "")
    return None


def validate_waivers(data):
    """Errors in a scan_waivers.json structure. Empty list == valid.

    Shape: {"_readme": ..., "<INST>": {"<loc>": {"<name-scoped key>":
             {"value": "<the exact map value this covers>",
              "reasons": ["SELF_ECHO"|"IS_OTHER_EN", ...],
              "reason": "<why this row is not a defect, citing the paper>"}}}}
    """
    errs = []
    if not isinstance(data, dict):
        return ["top level must be an object keyed by instrument"]
    for inst, block in data.items():
        if inst.startswith("_"):
            continue                                   # _readme provenance block
        if inst not in INSTR:
            errs.append(f"{inst}: unknown instrument")
            continue
        if not isinstance(block, dict):
            errs.append(f"{inst}: block must be an object keyed by locale")
            continue
        for loc, sub in block.items():
            if not isinstance(loc, str) or loc.lower() not in LOCALES:
                errs.append(f"{inst}/{loc!r}: not a known locale")
                continue
            if not isinstance(sub, dict):
                errs.append(f"{inst}/{loc}: locale block must be an object keyed by key")
                continue
            for key, ent in sub.items():
                where = f"{inst}/{loc}/{key!r}"
                if ":" not in key:
                    errs.append(f"{where}: waiver key must be name-scoped (contain ':')")
                if not isinstance(ent, dict):
                    errs.append(f"{where}: entry must be an object with value + reasons + reason")
                    continue
                val = ent.get("value")
                if not isinstance(val, str) or not val.strip():
                    errs.append(f"{where}: 'value' must be the non-empty map value this waiver "
                                f"covers (it pins the waiver to that text)")
                reasons = ent.get("reasons")
                if not isinstance(reasons, list) or not reasons:
                    errs.append(f"{where}: 'reasons' must be a non-empty list of scan reasons")
                else:
                    for r in reasons:
                        if r not in WAIVABLE_REASONS:
                            errs.append(f"{where}: reason {r!r} is not waivable "
                                        f"(only {', '.join(WAIVABLE_REASONS)})")
                    if len(set(reasons)) != len(reasons):
                        errs.append(f"{where}: 'reasons' has duplicate entries")
                if not isinstance(ent.get("reason"), str) or not ent.get("reason", "").strip():
                    errs.append(f"{where}: 'reason' must be a non-empty string - a waiver "
                                f"without a stated reason is a silent defect carrier")
    return errs


def load_waivers(path=WAIVERS_PATH):
    """(INST, LOCALE-UPPER, key) -> entry. Missing file == no waivers; invalid file raises."""
    if not os.path.exists(path):
        return {}
    data = json.loads(io.open(path, encoding="utf-8").read())
    errs = validate_waivers(data)
    if errs:
        raise SystemExit(f"{os.path.basename(path)} invalid:\n  " + "\n  ".join(errs))
    flat = {}
    for inst, block in data.items():
        if inst.startswith("_"):
            continue
        for loc, sub in block.items():
            for key, ent in sub.items():
                flat[(inst, loc.upper(), key)] = ent
    return flat


def is_waived(waivers, inst, loc, key, reason, value):
    ent = waivers.get((inst, loc.upper(), key))
    if not ent or reason not in ent.get("reasons", ()):
        return False
    return (value or "").strip() == ent["value"].strip()


def apply_waivers(waivers, inst, loc, key, value, reasons, hits=None):
    """Split `reasons` into (kept, waived); count each firing waiver in `hits`."""
    kept, waived = [], []
    for reason in reasons:
        if is_waived(waivers, inst, loc, key, reason, value):
            waived.append(reason)
            if hits is not None:
                tag = (inst, loc.upper(), key)
                hits[tag] = hits.get(tag, 0) + 1
        else:
            kept.append(reason)
    return kept, waived


def stale_waivers(waivers, hits):
    """Waivers that covered nothing in this scan — the row was fixed, renamed or re-flagged."""
    return [tag for tag in waivers if not hits.get(tag)]


def main():
    # Rewrapping stdout is a SCRIPT concern: doing it at import time closes pytest's
    # capture buffer for the whole session (measured), and nothing but this entry point
    # needs it.
    global_out = sys.stdout
    if hasattr(global_out, "buffer"):
        sys.stdout = io.TextIOWrapper(global_out.buffer, encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply-report")
    ap.add_argument("--waivers", default=WAIVERS_PATH,
                    help="scan_waivers.json (reasoned per-key SELF_ECHO/IS_OTHER_EN exemptions)")
    a = ap.parse_args()
    waivers = load_waivers(a.waivers)
    waiver_hits = {}
    waived_rows = []
    paper_redup_rows = []      # 2026-08-31: DOUBLED runs the paper prints verbatim (not raised)

    official = json.load(io.open(OFFICIAL, encoding="utf-8"))
    findings = []
    tally = Counter()

    for inst in INSTR:
        tdir = os.path.join(CSPRO, inst, "translations")
        if not os.path.isdir(tdir):
            continue
        src = capture_source_dict(inst, "generate_dcf.py")
        key2en = {}
        for key, node in walk_labeled_nodes(src):
            labs = node.get("labels")
            if (isinstance(labs, list) and labs and isinstance(labs[0], dict)
                    and "text" in labs[0]):
                key2en[key] = labs[0]["text"]
        en_index = {}                                  # norm(EN) -> set of keys
        for k, en in key2en.items():
            en_index.setdefault(norm(en), set()).add(k)
        frag_ens = [(en.casefold(), k) for k, en in key2en.items() if len(en) >= 20]

        cleared_by_loc = {}                            # LOC -> norm(stem) -> qnum
        cleared_en = {}                                # qnum -> EN stem
        for q, per_loc in official.get(inst, {}).items():
            if per_loc.get("EN", {}).get("stem"):
                cleared_en[q] = per_loc["EN"]["stem"]
            for loc, entry in per_loc.items():
                if loc == "EN":
                    continue
                stem = entry.get("stem")
                if stem and len(norm(stem)) >= 15:
                    cleared_by_loc.setdefault(loc, {})[norm(stem)] = q
        cleared_stem = {}                              # (LOC, qnum) -> stem text
        for q, per_loc in official.get(inst, {}).items():
            for loc, entry in per_loc.items():
                if loc != "EN" and entry.get("stem"):
                    cleared_stem[(loc, q)] = entry["stem"]

        for fn in sorted(os.listdir(tdir)):
            if not fn.endswith(".json"):
                continue
            loc = fn[:-5].upper()
            m = json.load(io.open(os.path.join(tdir, fn), encoding="utf-8"))
            m.pop("_meta", None)
            for k, v in m.items():
                en = key2en.get(k)
                reasons = []
                if en is None:
                    reasons.append("STALE_KEY")
                else:
                    is_stem = k.startswith(("item:", "vs:"))
                    run = doubled_run(v)
                    if run is not None:
                        if paper_reduplicated(inst, loc, run):
                            paper_redup_rows.append({"instrument": inst, "locale": loc, "key": k,
                                                     "run": run, "value": v})
                        else:
                            reasons.append("DOUBLED")
                    if norm(v) == norm(en):
                        reasons.append("SELF_ECHO")
                    else:
                        hit = en_index.get(norm(v))
                        if hit and k not in hit and len(norm(v)) >= 8:
                            reasons.append("IS_OTHER_EN")
                    if not reasons:
                        vf = v.casefold()
                        enf = en.casefold()
                        for frag, fk in frag_ens:
                            if fk != k and frag in vf and frag not in enf:
                                reasons.append("EN_FRAGMENT")
                                break
                    if is_stem and not reasons:
                        q = qnum_of(k, en)
                        own = cleared_stem.get((loc, q)) if q else None
                        wrong = cleared_by_loc.get(loc, {}).get(norm(v))
                        # Numbering guard: CAPI and cleared numbering drift in
                        # places (the Q107 lesson), so a number mismatch alone is
                        # not wrong text — only flag when the OTHER question's
                        # ENGLISH also disagrees with this node's English.
                        if wrong and wrong != q:
                            other_en = cleared_en.get(wrong, "")
                            import difflib
                            same_q = (difflib.SequenceMatcher(
                                None, norm(en), norm(other_en)).ratio() >= 0.75)
                            if not same_q:
                                reasons.append("WRONG_Q_CLEARED")
                        elif own and v != own and norm(v) != norm(own):
                            o = own.strip()
                            vv = v.strip()
                            if (vv.startswith(o) or vv.endswith(o)) and len(vv) > len(o) + 2:
                                reasons.append("GLUED_CLEARED")
                reasons, waived = apply_waivers(waivers, inst, loc, k, v, reasons, waiver_hits)
                for reason in waived:
                    waived_rows.append({"instrument": inst, "locale": loc, "reason": reason,
                                        "key": k, "en": en, "value": v})
                for reason in reasons:
                    tally[(inst, loc, reason)] += 1
                    findings.append({"instrument": inst, "locale": loc, "reason": reason,
                                     "key": k, "en": en, "value": v})

    print(f"\n{'instrument':<11}{'locale':<8}{'reason':<16}{'count':>7}")
    for (inst, lg, reason), n in sorted(tally.items()):
        print(f"{inst:<11}{lg:<8}{reason:<16}{n:>7}")
    print(f"\nTOTAL suspect entries: {len(findings)}")

    # Waived rows are NOT suspect entries (that is the point) but they are never silent:
    # every one is printed with the reason it was waived for, and a waiver that covered
    # nothing this run is printed as STALE.
    print(f"\n--- waived ({len(waived_rows)} row(s), {len(waivers)} waiver(s) in "
          f"{os.path.basename(a.waivers)}) ---")
    for f in waived_rows:
        print(f"[{f['reason']} waived] {f['instrument']}/{f['locale']}  {f['key']}")
        print(f"   value : {f['value'][:100]}")
        print(f"   why   : {waivers[(f['instrument'], f['locale'].upper(), f['key'])]['reason'][:160]}")
    for tag in stale_waivers(waivers, waiver_hits):
        print(f"STALE WAIVER (covered nothing this run): {tag[0]}/{tag[1]} {tag[2]}")

    print(f"\n--- paper reduplication ({len(paper_redup_rows)} row(s): the repeated run is printed "
          f"verbatim in text-aug21/<inst>_<LOC>.txt, so DOUBLED is not raised) ---")
    for f in paper_redup_rows:
        print(f"[paper reduplication] {f['instrument']}/{f['locale']}  {f['key']}")
        print(f"   run   : {f['run']!r}")
        print(f"   value : {f['value'][:100]}")
    print("\n--- samples (one per reason/instrument/locale) ---")
    seen = set()
    for f in findings:
        tag = (f["reason"], f["instrument"], f["locale"])
        if tag in seen:
            continue
        seen.add(tag)
        print(f"\n[{f['reason']}] {f['instrument']}/{f['locale']}  {f['key'][:60]}")
        print(f"   en    : {(f['en'] or '')[:100]}")
        print(f"   value : {f['value'][:100]}")

    if a.apply_report:
        with io.open(a.apply_report, "w", encoding="utf-8") as fh:
            json.dump(findings, fh, ensure_ascii=False, indent=1)
        print(f"\nWrote {a.apply_report}")


if __name__ == "__main__":
    main()
