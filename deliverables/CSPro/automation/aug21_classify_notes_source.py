#!/usr/bin/env python3
"""Classify each Aug-21 translated paper as bilingual-inline or monolingual for the notes layer.

    python automation/aug21_classify_notes_source.py F4
    python automation/aug21_classify_notes_source.py F4 --keys const:_GATE_DOH_RETAINED

WHY
---
data/translations-official/extract_notes.py anchors on the ENGLISH note inside the
TRANSLATED paper and takes the text that follows it, so it can only recover a note where
that paper prints the note bilingually. A paper that prints a note only in the dialect
(or is monolingual, like the June-5 Waray F4) is a SOURCE limit, not an extractor bug, and
has to be recorded as such BEFORE the extractor runs - otherwise the missing rows read as
a regression. This is Task 29 Step 0, kept as a script so the classification is repeatable.

WHAT IT REPORTS
---------------
Per locale: how many of the instrument's English note anchors appear verbatim in that
paper (bilingual-inline when > 0), plus a present/absent column for every key named with
--keys (default: the `const:_GATE_*` family, the anchors Task 29 cares about).

Reads the text-aug21/ dumps extract_notes.py writes - the exact bytes find_translation()
searches; a locale with no dump is reported as NO DUMP. Informational: exit 0 unless the
dump directory or a named note key does not exist.
"""
import argparse
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.dirname(HERE)
OFFICIAL = os.path.join(CSPRO, "data", "translations-official")
sys.path.insert(0, OFFICIAL)

import extract_notes as en  # noqa: E402  (lives in data/translations-official)


def paper_text(inst, loc, text_dir):
    """The blob find_translation() searches, or None when that paper was not dumped."""
    dump = os.path.join(text_dir, f"{inst}_{loc}.txt")
    if not os.path.exists(dump):
        return None
    return en.norm(io.open(dump, encoding="utf-8").read())


def classify(notes, keys, text_dir, inst):
    missing_keys = [k for k in keys if k not in notes]
    if missing_keys:
        raise SystemExit(f"{inst}: no such note key(s) in generate_qsf.py: "
                         + ", ".join(missing_keys))
    rows = []
    for loc in en.LOCALES:
        blob = paper_text(inst, loc, text_dir)
        if blob is None:
            rows.append((loc, None, {}))
            continue
        low = blob.lower()
        found = sum(1 for txt in notes.values() if en.norm(txt).lower() in low)
        per_key = {k: (en.norm(notes[k]).lower() in low) for k in keys}
        rows.append((loc, found, per_key))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inst", choices=("F1", "F3", "F4"))
    ap.add_argument("--keys", nargs="*", default=None,
                    help="note keys to report individually (default: every const:_GATE_* key)")
    ap.add_argument("--text-dir", default=os.path.join(OFFICIAL, "text-aug21"))
    a = ap.parse_args()

    if not os.path.isdir(a.text_dir):
        raise SystemExit(f"no dump directory {a.text_dir} - run extract_notes.py --source first")

    notes = en.english_notes(a.inst)
    keys = a.keys if a.keys is not None else [k for k in notes if k.startswith("const:_GATE_")]
    rows = classify(notes, keys, a.text_dir, a.inst)

    head = f"{'LOC':<5}{'anchors':>9}{'/':^3}{'total':<7}  layout"
    print(f"[{a.inst}] English note anchors found in each Aug-21 translated paper")
    print(head)
    print("-" * len(head))
    limited = []
    for loc, found, _per_key in rows:
        if found is None:
            print(f"{loc:<5}{'-':>9}{'/':^3}{len(notes):<7}  NO DUMP")
            limited.append(loc)
            continue
        layout = "bilingual-inline" if found else "monolingual (source-limited)"
        if not found:
            limited.append(loc)
        print(f"{loc:<5}{found:>9}{'/':^3}{len(notes):<7}  {layout}")

    for key in keys:
        print(f"\n{key}  ->  {en.norm(notes[key])}")
        for loc, found, per_key in rows:
            if found is None:
                print(f"  {loc:<5} NO DUMP")
            else:
                seen = "English anchor PRESENT" if per_key[key] else "NO English anchor"
                print(f"  {loc:<5} {seen}")

    print("\nsource-limited locales: " + (", ".join(limited) if limited else "none"))


if __name__ == "__main__":
    main()
