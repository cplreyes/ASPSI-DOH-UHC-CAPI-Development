"""Audit spec/translations/*.json against the generated English spec.

Why this exists
--------------
A row-misaligned translation import (found 2026-08-13) paired dialect strings
with the WRONG English keys. It was invisible in English and shipped to
production, where Filipino respondents saw:

    Q2  "Probationary"      as "Project"
    Q5  "Nursing assistant" as "Nutrition action officer/ coordinator ..."
    Q5  "Administrator"     as "doctor, nurse"          (Waray)

Q5 gates Sections C/D/E/G, so a mislabeled option routes a respondent through
the wrong sections. Section titles additionally absorbed note prose and
preamble tails, so the note rendered AS the heading in those locales.

The regression test `src/components/survey/real-spec-preambles.test.tsx` pins
the specific debris from that incident. THIS script is the broader sweep --
run it whenever translations are re-imported or ASPSI supplies new strings.

Usage:  python scripts/audit-translations.py
Exit:   0 = no suspects, 1 = suspects found (review each; some are stylistic)
"""

import json, io, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)
ITEMS = os.path.join(APP, "src", "generated", "items.ts")
TDIR = os.path.join(APP, "spec", "translations")

src = io.open(ITEMS, encoding="utf-8").read()
EN = set(m.group(1).replace("\\'", "'") for m in re.finditer(r"en: '((?:[^'\\]|\\.)*)'", src))
norm = lambda s: re.sub(r"\s+", " ", s.strip().lower())
EN_NORM = {norm(e): e for e in EN}

# Debris signatures. These flag STRUCTURE, not language quality -- a hit is a
# prompt to look, not proof of a bug. Lowercase-initial dialect strings are
# common and legitimate (Waray "waray" = "None"), so that check is advisory.
CHECKS = [
    ("stray marker", re.compile(r"\bNote:\s*\d|\bNone\b\s*\w*\s*\d|\bN/A\b")),
    ("trailing question number", re.compile(r"\s\d{1,3}\s*$")),
    ("trailing section letter", re.compile(r"\s[A-Z]\s*$")),
    ("stray angle bracket", re.compile(r"[<>]")),
]
EN_PROSE = re.compile(r"\b(the|and|that|with|your|from|only|please|answer|questions|following|proceed)\b", re.I)

total = 0
for fn in sorted(os.listdir(TDIR)):
    if not fn.endswith(".json"):
        continue
    loc = fn[:-5]
    d = json.load(io.open(os.path.join(TDIR, fn), encoding="utf-8"))
    rows = []

    for k, v in d.items():
        if not isinstance(v, str) or not v.strip():
            continue
        hits = [n for n, rx in CHECKS if rx.search(v)]
        if norm(k) not in EN_NORM:
            hits.append("ORPHAN key (not in the English spec)")
        nv = norm(v)
        if nv in EN_NORM and EN_NORM[nv] != k:
            hits.append("value is a DIFFERENT English string")
        if len(v) > 30 and len(EN_PROSE.findall(v)) >= 3:
            hits.append("English prose in a dialect slot")
        if hits:
            rows.append((k, v, hits))

    if rows:
        print("=" * 78)
        print("%s.json  (%d entries, %d suspect)" % (loc, len(d), len(rows)))
        print("=" * 78)
        for k, v, hits in rows:
            print("  %-42s -> %-42s" % (k[:42].encode("ascii", "replace").decode(),
                                        v[:42].encode("ascii", "replace").decode()))
            print("      %s" % "; ".join(hits))
        print()
    total += len(rows)

print("TOTAL SUSPECT ENTRIES: %d" % total)
print("\nRemoving a corrupted entry is safe: localized() falls back to English.")
print("Never invent a dialect string -- corrected text must come from ASPSI.")
sys.exit(1 if total else 0)
