#!/usr/bin/env python3
"""F2 PWA consent screen (chrome `consent.*`) from the seven Aug-21 F2 translated PDFs.

Anchor set = the English Part-I paragraphs in APP/src/i18n/locales/en.ts `consent`
(infoStudy / infoPrivacy / infoBenefits / infoRights / contactsHeading). Every Aug-21 F2
paper prints each English paragraph followed by its translation (verified 2026-08-26 on
all seven files), so the translation is the span between one located English paragraph and
the next located one — the same locate / reads_english / finish trio as extract_icf.py
(F1/F3/F4 ICF).

Where this differs from extract_icf.py: en.ts is a SCREEN and the paper is a read-aloud
script, so four of the five anchors diverge MID-paragraph, not just at the tail —

    en.ts     "... funded this study. The survey may take more or less than an hour to
               complete. The questions will cover ... opportunities. Your progress is saved
               automatically on this device - you can pause and continue ... before submitting."
    paper     "... funded this study. The interview may last for more or less than an hour.
               The questions will cover ... opportunities."

locate() therefore stops on a `prefix` at "... funded this study." and the paper's own
remaining English ("The interview may last ...", "The questions will cover ...") sits in
front of the translation. extract_icf._drop_anchor_tail() cannot remove it: it walks the
anchor's tail token by token and stops at the first token the paper words differently
("survey" vs "interview"), which on these papers is the very first one. _drop_english_tail()
is the F2 counterpart — it walks the leftover SENTENCE by sentence, dropping a sentence
that either still reads as English (extract_notes.looks_english) or repeats >= 60% of the
anchor's own words after the program names are removed. Those two signals separate the
paper's English variants (0.8-1.0 word overlap with the anchor) from the translation
(<= 0.1 once "Universal Health Care", "Yaman ng Kalusugan Program" etc. are stripped),
and a window whose every sentence is English is handed back unchanged so the caller drops
it as `dropped-english` rather than storing an empty paragraph.

Headings, buttons, `intro`, the raffle block and `contactsBody` (a contact TABLE printed
cell-by-cell) have no paper counterpart and stay app chrome — spec Scope Out ("F2 chrome
strings beyond the consent screen").

    python extract_icf_f2.py --source RAW/Translations --en APP/src/i18n/locales/en.ts           # report only
    python extract_icf_f2.py --source ... --en ... --out APP/src/i18n/locales/consent.aug21.ts   # write the TS patch
"""
import argparse
import io
import json
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from extract_notes import norm, looks_english, pdf_lines, PAPER_LANG, DUMP_NOISE  # noqa: E402
from extract_icf import locate, reads_english, finish, STOP, PROGRAM_NAMES  # noqa: E402
from aug21_overrides import load_overrides  # noqa: E402

CONSENT_PARAGRAPH_KEYS = ["infoStudy", "infoPrivacy", "infoBenefits", "infoRights", "contactsHeading"]
LOCALES = ["fil", "ceb", "bis", "ilo", "hil", "war", "bcl"]      # F2 order (scripts/lib/apply-translations.ts:8)
F2_NAME = re.compile(r"^F2-([A-Za-z]+)_.*\.pdf$")               # extract_notes.PAPER_NAME covers F1/F3/F4 only
# English phrases the F2 consent paragraphs keep verbatim in every locale, on top of
# extract_icf.PROGRAM_NAMES. Left in place they are the only English words in a stored
# translation, and their "and"/"for" alone can reach looks_english()'s 3-function-word bar.
EXTRA_NAMES = re.compile(r"Implementing Rules and Regulations|UHC Act|YAKAP/?KONSULTA|NBB/ZBB"
                         r"|BUCAS|GAMOT|\bIRR\b|\bDOH\b|PhP", re.I)
_LIT = r"(?P<q>['\"])(?P<v>(?:\\.|(?!(?P=q)).)*)(?P=q)"
_SENT = re.compile(r"(?<=[.!?])\s+")
# A '.' that ends one of these is an abbreviation, not a sentence end. "Inc." matters:
# every locale opens its infoStudy translation with "<article> Asian Social Project
# Services, Inc. (ASPSI) ...", and splitting there would hand _drop_english_tail() a
# two-word fragment to judge instead of the sentence.
_ABBREV = re.compile(r"(?:^|\s)(?:Inc|Corp|No|Ver|St|Dr|Mr|Mrs|Ms|Sr|Jr|vs|etc|[A-Za-z])\.$")
_WORD = re.compile(r"[0-9a-z']+")
# A word the paper broke across a PDF line at its OWN hyphen ("Layunin ng pag-" / "aaral na
# ito", "mga pagbag-" / "o sa operasyon"). Joining the lines with a space would print
# "pag- aaral" on the consent screen - a rendering artefact of the wrap, not the translator's
# word. Only a hyphen with no space in FRONT of it is a broken word: norm() has already
# turned the en/em dashes into "-", and those keep their leading space (" - you can pause").
_SOFT_HYPHEN = re.compile(r"(\w)-\s+(\w)")
OVERLAP = 0.6          # share of an anchor's words a sentence must repeat to count as its English
MIN_OVERLAP_WORDS = 5  # below this a word-overlap ratio is noise


def en_consent(path):
    """{key: text} for CONSENT_PARAGRAPH_KEYS read straight from en.ts (no TS toolchain needed)."""
    src = io.open(path, encoding="utf-8").read()
    blk = src[src.index("  consent: {"):]
    out = OrderedDict()
    for k in CONSENT_PARAGRAPH_KEYS:
        m = re.search(r"^\s*" + k + r":\s*" + _LIT, blk, re.M | re.S)
        if not m:
            raise SystemExit(f"en.ts: consent.{k} not found")
        out[k] = m.group("v").replace("\\'", "'").replace('\\"', '"').replace("\\n", "\n")
    return out


def _names(s):
    """Drop the English proper names every locale keeps verbatim inside the consent text."""
    return EXTRA_NAMES.sub(" ", PROGRAM_NAMES.sub(" ", s or ""))


def _words(s):
    return _WORD.findall((s or "").lower())


def _sentences(s):
    out = []
    for piece in _SENT.split(s):
        if out and _ABBREV.search(out[-1]):
            out[-1] += " " + piece          # "... Services, Inc." + "(ASPSI) requests ..."
        else:
            out.append(piece)
    return out


def _is_english_tail(sentence, anchor_words):
    bare = _names(sentence)
    if looks_english(bare):
        return True
    w = _words(bare)
    if len(w) < MIN_OVERLAP_WORDS:
        return False
    return sum(1 for x in w if x in anchor_words) / len(w) >= OVERLAP


def _drop_english_tail(window, en):
    """Walk the paper's leftover English off the head of `window`, sentence by sentence.

    Returns `window` unchanged when EVERY sentence reads as the anchor's English — an
    echoed English paragraph, which the caller must drop as `dropped-english` rather than
    store as an empty string.
    """
    parts = _sentences(window)
    anchor_words = set(_words(_names(en)))
    for i, part in enumerate(parts):
        if not _is_english_tail(part, anchor_words):
            return " ".join(parts[i:])
    return window


def extract_consent(lines, anchors):
    """(trans {key: text}, report {key: exact|prefix|suffix|missing|dropped-*}) for one paper."""
    # Same page-furniture drop extract_notes.dump_source() applies to its text dumps: the
    # F2 consent page carries a three-line version/clearance footer that PyMuPDF emits
    # wherever it falls, which on a two-page consent lands mid-paragraph.
    blob = _SOFT_HYPHEN.sub(r"\1-\2", norm(" ".join(ln for ln in lines if not DUMP_NOISE.search(ln))))
    low = blob.lower()
    found = [(k, norm(en), locate(low, norm(en))) for k, en in anchors.items()]
    trans, report = OrderedDict(), OrderedDict()
    for n, (k, en, loc) in enumerate(found):
        if loc is None:
            report[k] = "missing"
            continue
        start, end, kind = loc
        nxt = next((l[0] for _, _, l in found[n + 1:] if l is not None and l[0] > end), len(blob))
        cand = blob[end:nxt].lstrip(" .:-)")
        m = STOP.search(cand)
        if m:
            cand = cand[:m.start()]
        cand = _drop_english_tail(cand, en)
        cand = finish(cand[:int(len(en) * 2.5) + 40])
        if len(cand) < 20:
            report[k] = "dropped-short"
        elif reads_english(_names(cand), en):
            report[k] = "dropped-english"
        else:
            trans[k] = cand
            report[k] = kind
    return trans, report


def build_consent(source_dir, anchors, overrides):
    """({loc: {key: text}}, {loc: report}) across the F2 papers in `source_dir`."""
    by_loc = OrderedDict((l, OrderedDict()) for l in LOCALES)
    report = OrderedDict()
    for name in sorted(os.listdir(source_dir)):
        m = F2_NAME.match(name)
        if not m or m.group(1) not in PAPER_LANG:
            continue
        loc = PAPER_LANG[m.group(1)].lower()
        trans, rep = extract_consent(pdf_lines(os.path.join(source_dir, name)), anchors)
        ov = overrides.get("F2", {}).get(loc, {})
        for k, en in anchors.items():
            if en in ov:                                     # F2 override shape: keyed by the English string
                keep = ov[en].get("keep")
                rep[k] = "override"
                if keep:                                     # None = never write; text = pin
                    by_loc[loc][k] = keep
            elif k in trans:
                by_loc[loc][k] = trans[k]
        report[loc] = rep
    return by_loc, report


def ts_str(v):
    """Single-quoted TS literal (.prettierrc: singleQuote)."""
    return "'" + v.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"


def render_ts(by_loc):
    keys = " | ".join(f"'{k}'" for k in CONSENT_PARAGRAPH_KEYS)
    locs = " | ".join(f"'{l}'" for l in LOCALES)
    lines = [
        "// GENERATED by deliverables/CSPro/data/translations-official/extract_icf_f2.py from the",
        "// Aug-21 F2 translated PDFs (raw/Survey-Instruments-2026-08-21/Translations).",
        "// Do not edit by hand — re-run the extractor.",
        "// Each locale bundle spreads its patch LAST into `consent`, so an absent key falls back",
        "// to English. Headings, buttons, `intro`, the raffle block and the contacts TABLE have no",
        "// paper counterpart and stay app chrome.",
        "import type { EnBundle } from './en';",
        "",
        # Both type headers are past prettier's printWidth 100 on one line; emit them the
        # way `prettier --write` would, so the generated file needs no formatting pass.
        "export type ConsentAug21Patch = Partial<",
        "  Pick<",
        "    EnBundle['consent'],",
        f"    {keys}",
        "  >",
        ">;",
        "",
        "export const consentAug21: Record<",
        f"  {locs},",
        "  ConsentAug21Patch",
        "> = {",
    ]
    for loc in LOCALES:
        lines.append(f"  {loc}: {{")
        for k, v in by_loc.get(loc, {}).items():
            lit = ts_str(v)
            one = f"    {k}: {lit},"
            # prettier (printWidth 100) cannot break a string literal, so it moves an
            # over-long value onto its own indented line — match that, as en.ts does.
            lines.append(one if len(one) <= 100 else f"    {k}:\n      {lit},")
        lines.append("  },")
    lines += ["};", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="raw/Survey-Instruments-2026-08-21/Translations")
    ap.add_argument("--en", required=True, help="APP/src/i18n/locales/en.ts")
    ap.add_argument("--out", help="APP/src/i18n/locales/consent.aug21.ts (omit = report only)")
    ap.add_argument("--report", default=os.path.join(HERE, "out-aug21", "F2", "consent-report.json"))
    ap.add_argument("--overrides", default=os.path.join(HERE, "aug21-overrides.json"))
    a = ap.parse_args()
    anchors = en_consent(a.en)
    by_loc, report = build_consent(a.source, anchors, load_overrides(a.overrides))
    for loc in LOCALES:
        rep = report.get(loc, {})
        print(f"[F2 {loc}] " + "  ".join(f"{k}={rep.get(k, 'no-pdf')}" for k in CONSENT_PARAGRAPH_KEYS))
    os.makedirs(os.path.dirname(a.report), exist_ok=True)
    with io.open(a.report, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"anchors": anchors, "report": report,
                   "written": {l: list(v) for l, v in by_loc.items()},
                   "values": by_loc}, fh, ensure_ascii=False, indent=1)
    if a.out:
        with io.open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_ts(by_loc))
        print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
