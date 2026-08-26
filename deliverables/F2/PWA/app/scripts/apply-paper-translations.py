"""Apply Aug-21 paper translations to the F2 PWA store.

Input  = deliverables/CSPro/data/translations-official/out-aug21/F2/{loc}.json
         (anchor_extract_f2.py output, ENGLISH-TEXT-KEYED — the PWA store is flat
         English-keyed, applied by scripts/lib/apply-translations.ts at generate time).
Join   = EXACT English string against spec/english-strings.json (the six fields
         applyTranslations() localizes). Question-number joins are NOT used
         (2026-08-13 row-misalignment scar).
Rule   = overrides first: aug21-overrides.json["F2"][loc][english] = {"keep": text|null}
         -> keep text (written if it differs from the map) or null (never write).
         Otherwise Aug-21 wins: absent -> write; equal -> already_same; different -> replace.
         An override for a key the extract never produced is seeded after the extract
         loop (action "override_seeded") so a hand-corrected value is not lost just
         because the extractor missed that cell.
Residue= a bare trailing question number swept in from the paper is stripped unless the
         English string itself ends in a digit (audit-translations.py flags '\\s\\d{1,3}$'),
         and so is an 'N. NextWord' tail (the next question's number plus the start of
         its text) unless the English carries the same shape.
Retire = --retire "<English>" (repeatable) deletes a stale key from every locale map and
         records it in the report; stale keys are never hand-deleted. A locale whose extract
         file is missing is still processed (empty extract) so --retire and the override
         seeding reach every map; its report entry carries "skipped": "no extract".
Format = indent 1, ensure_ascii=False, line endings preserved as loaded (maps are CRLF
         today), trailing newline; a map is saved only when its content changed.
No _meta is written into the maps: readMap() (scripts/lib/apply-translations.ts:36)
keeps only non-empty string values and silently drops everything else, and
scripts/audit-translations.py:57 skips non-strings too — so a _meta block would be
invisible provenance at best. Provenance goes to --report instead.

  python scripts/apply-paper-translations.py            # dry run, report only
  python scripts/apply-paper-translations.py --apply    # write spec/translations/{loc}.json
"""
import argparse
import io
import json
import os
import re
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(APP, "..", "..", "..", ".."))
TDIR = os.path.join(APP, "spec", "translations")
ENGLISH_STRINGS = os.path.join(APP, "spec", "english-strings.json")
DEFAULT_EXTRACT = os.path.join(ROOT, "deliverables", "CSPro", "data", "translations-official",
                               "out-aug21", "F2")
DEFAULT_OVERRIDES = os.path.join(ROOT, "deliverables", "CSPro", "data", "translations-official",
                                 "aug21-overrides.json")
DEFAULT_REPORT = os.path.join(DEFAULT_EXTRACT, "apply-report.json")
LOCALES = ["fil", "ceb", "bis", "ilo", "hil", "war", "bcl"]
ACTIONS = ["unmatched", "override", "override_seeded", "skip_same_as_english",
           "already_same", "write", "replace", "retire"]
_RESIDUE = re.compile(r"\s+\d{1,3}(?:\.\d{1,2})?\s*$")
_DOT_TAIL = re.compile(r"\s+\d{1,3}\.\s+\S.*$")
_EN_ENDS_DIGIT = re.compile(r"\d\s*$")


def norm(s):
    return " ".join((s or "").replace("’", "'").replace("‘", "'").split())


def strip_qnum_residue(tr, en):
    """Drop the next question's number (and the start of its text) swept in after the
    translation. Each sweep is skipped when the English string carries the same shape:
    a trailing digit makes the number content ('Level 3'), and an 'N. Word' tail in the
    English means the translation's tail is content too ('Choose 1. Yes or 2. No')."""
    val = norm(tr)
    if not _DOT_TAIL.search(en or ""):
        val = _DOT_TAIL.sub("", val).rstrip()
    if not _EN_ENDS_DIGIT.search(en or ""):
        val = _RESIDUE.sub("", val).rstrip()
    return val


def load_map(path):
    """-> (OrderedDict, crlf_flag). Line-ending style is detected so save_map can keep it."""
    with io.open(path, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    if raw.startswith("﻿"):
        raw = raw[1:]
    crlf = "\r\n" in raw
    data = json.loads(raw, object_pairs_hook=OrderedDict) if raw.strip() else OrderedDict()
    return data, crlf


def save_map(path, data, crlf):
    with io.open(path, "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def load_english_set(path=None):
    d = json.load(io.open(path or ENGLISH_STRINGS, encoding="utf-8"))
    return {s["text"] for s in d["strings"] if s.get("text")}


def load_f2_overrides(path, loc):
    """The F2 section of aug21-overrides.json for one locale (extract_notes.py owns the
    name load_overrides). Missing file / missing F2 key / missing locale -> {}."""
    if not os.path.exists(path):
        return {}
    d = json.load(io.open(path, encoding="utf-8"))
    return (d.get("F2") or {}).get(loc) or {}


def decide(en, tr, current, english_set, overrides_loc):
    if en not in english_set:
        return "unmatched", None
    if en in overrides_loc:                       # overrides win over every other rule
        return "override", overrides_loc[en].get("keep")
    val = strip_qnum_residue(tr, en)
    if not val or val.casefold() == norm(en).casefold():
        return "skip_same_as_english", None
    cur = current.get(en)
    if cur is not None and norm(cur) == val:
        return "already_same", None
    if cur is None:
        return "write", val
    return "replace", val


def apply_locale(extract, current, english_set, overrides_loc, retire=()):
    new = OrderedDict(current)
    counts = {a: 0 for a in ACTIONS}
    rows = []
    for en, tr in extract.items():
        action, val = decide(en, tr, current, english_set, overrides_loc)
        counts[action] += 1
        if action in ("write", "replace"):
            rows.append({"en": en, "action": action, "was": current.get(en), "now": val})
            new[en] = val
        elif action == "override":
            rows.append({"en": en, "action": action, "was": current.get(en), "now": val,
                         "reason": overrides_loc[en].get("reason")})
            if val and val.strip() and new.get(en) != val:
                new[en] = val                    # hand-corrected keep is applied
            # keep null/"" -> never write this key (readMap drops "" anyway); leave map as-is

    # Overrides for English keys the extract never produced: a hand-corrected value must
    # not be lost because the extractor missed that cell. keep:null still never writes.
    for en, ent in (overrides_loc or {}).items():
        if en in extract:
            continue
        keep = ent.get("keep")
        if not keep or not keep.strip():         # null/"" -> never write
            continue
        if en not in english_set:                # would create an audit ORPHAN key
            counts["unmatched"] += 1
            continue
        counts["override_seeded"] += 1
        rows.append({"en": en, "action": "override_seeded", "was": current.get(en),
                     "now": keep, "reason": ent.get("reason")})
        if new.get(en) != keep:
            new[en] = keep

    for en in retire or ():                      # explicit operator intent wins over everything
        if en in new:
            counts["retire"] += 1
            rows.append({"en": en, "action": "retire", "was": new.get(en), "now": None})
            del new[en]
    return new, counts, rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract-dir", default=DEFAULT_EXTRACT)
    ap.add_argument("--overrides", default=DEFAULT_OVERRIDES)
    ap.add_argument("--report", default=DEFAULT_REPORT)
    ap.add_argument("--retire", action="append", default=None, metavar="EN",
                    help="English key to delete from every locale map (repeatable)")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    retire = a.retire or []
    english_set = load_english_set()
    report = {"source": "raw/Survey-Instruments-2026-08-21/Translations", "provenance": "aug21",
              "mode": "APPLY" if a.apply else "DRY RUN", "retire": retire, "locales": {}}
    print(f"{'APPLIED' if a.apply else 'DRY RUN'}  anchors={len(english_set)}")
    print("locale  unmatched  override  seeded  same-as-en  already  write  replace  retire  saved")
    for loc in LOCALES:
        src = os.path.join(a.extract_dir, f"{loc}.json")
        skipped = None
        if os.path.exists(src):
            extract, _ = load_map(src)
        else:
            # No Aug-21 extract for this locale, but --retire and the override seeding are
            # operator intent that must still reach every locale map (and every locale must
            # still appear in the report, marked so the provenance is not silently wrong).
            extract, skipped = OrderedDict(), "no extract"
        path = os.path.join(TDIR, f"{loc}.json")
        current, crlf = load_map(path) if os.path.exists(path) else (OrderedDict(), True)
        new, counts, rows = apply_locale(extract, current, english_set,
                                         load_f2_overrides(a.overrides, loc), retire)
        changed = new != current
        c = counts
        print(f"{loc:6}  {c['unmatched']:9}  {c['override']:8}  {c['override_seeded']:6}  "
              f"{c['skip_same_as_english']:10}  {c['already_same']:7}  {c['write']:5}  "
              f"{c['replace']:7}  {c['retire']:6}  "
              f"{'yes' if (a.apply and changed) else ('would' if changed else 'no')}"
              f"{'  (no extract)' if skipped else ''}")
        report["locales"][loc] = {"counts": counts, "rows": rows, "changed": changed,
                                  "retired": [r["en"] for r in rows if r["action"] == "retire"],
                                  "unmatched": sorted(k for k in extract if k not in english_set)}
        if skipped:
            report["locales"][loc]["skipped"] = skipped
        if a.apply and changed:
            save_map(path, new, crlf)
    os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
    with io.open(a.report, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(f"report -> {a.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
