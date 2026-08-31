#!/usr/bin/env python3
r"""Extract section-intro and enumerator-directive translations from the cleared PDFs.

THE GAP THIS FILLS
------------------
Section intros and enumerator directives are hardcoded ENGLISH constants in each
generate_qsf.py (an INTROS/SECTION_INTROS map and _READ_ONE/_DNR_ALL/_PROBE strings).
question_extras() prepends/appends them to EVERY locale's question text, so 299 question
screens show English regardless of the language chosen - 2,093 renderings across the seven
locales. They never enter the .dcf, so the dictionary translation pipeline cannot reach
them and the verbatim audit could not see them. Tickets #1216/#1219/#1220/#1223/#1224/#1225
are all this one defect.

HOW THE TRANSLATION IS RECOVERED
--------------------------------
The cleared PDFs print the English note and its translation adjacently, exactly like the
questions. So: find the English string in the locale's text dump, then take the text that
follows it up to the next English sentence. Verbatim - nothing is composed.

Anything that cannot be split cleanly is left EMPTY so the generator keeps English, which
is what the tablet already does. Empty is never worse than today.

    python extract_notes.py                                   # June-5 text/ dumps, report only
    python extract_notes.py --json notes.json                 # June-5 rebuild
    python extract_notes.py --source "C:/.../raw/Survey-Instruments-2026-08-21/Translations" \
        --provenance aug21 --json notes.json                  # Aug-21: dump PDFs, Aug-21-wins merge
"""
import argparse
import datetime
import io
import json
import os
import re
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
TEXT = os.path.join(HERE, "text")
LOCALES = ["FIL", "BCL", "BIS", "CEB", "WAR", "HIL", "ILO"]

# Aug-21 pack: raw/Survey-Instruments-2026-08-21/Translations/F{n}-{Language}_..._Aug21.pdf
PAPER_LANG = {"Tagalog": "FIL", "Bicolano": "BCL", "Bisaya": "BIS", "Cebuano": "CEB",
              "Waray": "WAR", "Hiligaynon": "HIL", "Ilocano": "ILO"}
PAPER_NAME = re.compile(r"^(F[134])-([A-Za-z]+)_.*\.pdf$")
# Page furniture, dropped from the DUMP only (pdf_lines stays the raw page text so the ICF
# reader can still see it). The Aug-21 paper carries a two-line footer and a bare page
# number; PyMuPDF emits them wherever they fall, which on nine notes is BETWEEN the English
# note and its translation - find_translation then ships the footer as the translation.
# Same pattern anchor_extract.pdf_text already strips from these very PDFs.
DUMP_NOISE = re.compile(r"ICF ver\.|Translated Questionnaire ver\.|PSA SSRCS Clear|^\s*\d+\s*$")


def pdf_lines(path):
    """Whole PDF as text lines (PyMuPDF), same shape as the text/ dumps."""
    import fitz
    doc = fitz.open(path)
    txt = "\n".join(p.get_text() for p in doc)
    doc.close()
    return txt.split("\n")


def dump_source(source_dir, text_dir):
    """PDF -> <INST>_<LOC>.txt under text_dir (LF, utf-8), page furniture removed.
    -> {(inst, loc): filename}."""
    os.makedirs(text_dir, exist_ok=True)
    written = OrderedDict()
    for name in sorted(os.listdir(source_dir)):
        m = PAPER_NAME.match(name)
        if not m or m.group(2) not in PAPER_LANG:
            continue
        inst, loc = m.group(1), PAPER_LANG[m.group(2)]
        lines = [ln for ln in pdf_lines(os.path.join(source_dir, name))
                 if not DUMP_NOISE.search(ln)]
        with io.open(os.path.join(text_dir, f"{inst}_{loc}.txt"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines))
        written[(inst, loc)] = name
    return written


def load_overrides(path):
    """aug21-overrides.json -> {INST: {key: {keep, reason}}}; {} when absent.
    keep == "" means: render English (empty is 'missing' to every consumer)."""
    if not path or not os.path.exists(path):
        return {}
    return json.load(io.open(path, encoding="utf-8"))


def canon_english(s):
    """Note identity as every CONSUMER sees it: notes_lookup._canon keys the whole notes
    layer by the full English string, never by the intro:/const: key. Merging by key alone
    therefore mis-reads a RE-KEY as a brand-new note: the F1 renumbering moved
    intro:51 -> intro:38 and intro:118 -> intro:105 with the English byte-identical, the
    merge saw no prior, counted the Aug-21 value as `written`, and the Step-5 "review every
    `replaced`" gate never fired on nine values that got shorter. Same normalisation as
    notes_lookup._canon (curly quotes + dashes + whitespace) so the two agree on what
    "same note" means - the dash fold was added 2026-08-26 after the divergent pair
    (norm() folded en/em dashes, _canon did not) hid F4 intro:144 from every locale.
    It is a no-op on values that already went through norm(); it exists so a future
    caller that passes RAW generator text cannot re-open that gap."""
    s = (s or "").replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("\xa0", " ")
    return " ".join(s.split())


def merge_notes(existing, fresh, overrides, provenance):
    """Aug-21-wins on the full English string; override keys note:<key>:<LOC> keep prior.
    A fresh EMPTY never clears a prior value (kept_prior). When the English of a key was
    reworded since the prior file, the prior translations are STALE and are dropped, but
    the fresh ones are still written. When the English is UNCHANGED but the key moved
    (renumbering), the prior is recovered by English text so the change is still reviewed
    as `replaced`."""
    counts = {"written": 0, "replaced": 0, "overridden": 0, "kept_prior": 0}
    merged = OrderedDict()
    for inst in ("F1", "F3", "F4"):
        old = existing.get(inst, {}) or {}
        new = fresh.get(inst, {}) or {}
        if not old and not new:
            continue                       # instrument absent from both sides
        old_english = old.get("english") or {}
        english = OrderedDict(new.get("english") or old_english)
        # Prior values addressed the way the runtime addresses them: by English text.
        # First writer wins per locale, exactly like notes_lookup._load.
        prior_by_english = {}
        for okey, oen in old_english.items():
            slot = prior_by_english.setdefault(canon_english(oen), OrderedDict())
            for lg, txt in ((old.get("translations") or {}).get(okey) or {}).items():
                if txt and lg not in slot:
                    slot[lg] = txt
        trans = OrderedDict()
        # ... plus any surviving English whose prior lives under a RETIRED key, so a
        # renumbering that the Aug-21 paper could not re-extract keeps its June-5 value
        # instead of quietly dropping to English.
        ov = overrides.get(inst, {})
        keys = list(dict.fromkeys(list((old.get("translations") or {}))
                                  + list((new.get("translations") or {}))
                                  + [k for k in english
                                     if canon_english(english[k]) in prior_by_english]
                                  # 2026-08-27: reviewer keep text reaches a key no locale extracted
                                  + [k for k in english
                                     if any(isinstance((ov.get(f"note:{k}:{lg}") or {}).get("keep"), str)
                                            and (ov.get(f"note:{k}:{lg}") or {})["keep"].strip()
                                            for lg in LOCALES)]))
        for key in keys:
            if key not in english:
                continue                   # note no longer exists in the generator
            prior = dict((old.get("translations") or {}).get(key, {}))
            if key in old_english and canon_english(old_english[key]) != canon_english(english[key]):
                prior = {}                 # reworded English: prior values are stale
            if not prior:                  # re-keyed note: same English, new key
                prior = dict(prior_by_english.get(canon_english(english[key]), {}))
            cand = (new.get("translations") or {}).get(key, {})
            row = OrderedDict(prior)
            for lg in LOCALES:
                val = (cand.get(lg) or "").strip()
                okey = f"note:{key}:{lg}"
                if not val:
                    # 2026-08-27: reviewer keep TEXT does not depend on the extractor
                    # having found a candidate (def:<q> rows, #1335/#1338/#1345)
                    okeep = (ov.get(okey) or {}).get("keep")
                    if isinstance(okeep, str) and okeep.strip():
                        row[lg] = okeep
                        counts["overridden"] += 1
                        continue
                    if prior.get(lg):
                        counts["kept_prior"] += 1
                    continue
                if okey in ov:
                    row[lg] = ov[okey].get("keep", prior.get(lg, val))
                    counts["overridden"] += 1
                elif prior.get(lg):
                    if norm(prior[lg]) != norm(val):
                        counts["replaced"] += 1
                    row[lg] = val
                else:
                    row[lg] = val
                    counts["written"] += 1
            if row:
                trans[key] = row
        merged[inst] = OrderedDict([("english", english), ("translations", trans)])
    merged["_provenance"] = OrderedDict(existing.get("_provenance", {}))
    merged["_provenance"]["aug21"] = OrderedDict(
        [("date", provenance["date"]), ("source", provenance["source"]),
         ("files", provenance.get("files", {})),
         ("n_written", counts["written"]), ("n_replaced", counts["replaced"]),
         ("n_overridden", counts["overridden"]), ("n_kept_prior", counts["kept_prior"])])
    return merged, counts


# ASCII-ish signature of an English sentence, used to find where the translation stops.
ENGLISH_LINE = re.compile(
    r"^\s*(?:[A-Z][A-Za-z' ,()/-]{12,}|READ |DO NOT |SELECT |ENUMERATOR|INTERVIEWER)")


def norm(s):
    s = (s or "").replace("’", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


# Module-level ENGLISH constant in a generate_qsf.py: _NAME = "..." (implicitly
# concatenated string parts allowed). Digits belong in the NAME - the Task 25/29 gate
# constants are _GATE_Q1xx, and ^(_[A-Z_]+) would have skipped every one of them.
_CONST_RE = re.compile(r"^(_[A-Z0-9_]+)\s*=\s*\(?((?:\s*\"[^\"]*\")+)", re.M)


def english_notes(inst):
    """Pull the English intro/directive strings straight out of the generator."""
    src = io.open(os.path.join(CSPRO, inst, "generate_qsf.py"), encoding="utf-8").read()
    out = OrderedDict()

    m = re.search(r"(?:SECTION_)?INTROS\s*=\s*\{(.*?)\n\}", src, re.S)
    if m:
        for qm in re.finditer(r"(\d{1,3})\s*:\s*(\(?)((?:\s*\"[^\"]*\")+)", m.group(1)):
            txt = " ".join(re.findall(r"\"([^\"]*)\"", qm.group(3)))
            out[f"intro:{qm.group(1)}"] = norm(txt)

    for cm in _CONST_RE.finditer(src):
        txt = " ".join(re.findall(r"\"([^\"]*)\"", cm.group(2)))
        if len(txt) > 15 and not txt.startswith("<"):
            out[f"const:{cm.group(1)}"] = norm(txt)
    # 2026-08-27 (#1335/#1338/#1345): the hand-held per-question rows of INSTRUCTIONS
    # (a definition or preamble, optionally "+ _CONST") are notes too - translate_note
    # resolves them by their full English string like every other note - but they were
    # never registered, so no locale could ever carry them. Registered as def:<q>.
    m = re.search(r"\nINSTRUCTIONS\s*=\s*\{(.*?)\n\}", src, re.S)
    if m:
        for qm in re.finditer(r"\n\s+(\d{1,3})\s*:\s*\(((?:\s*\"[^\"]*\")+)"
                              r"(?:\s*\+\s*(_[A-Z_]+))?\s*\)", m.group(1)):
            txt = " ".join(re.findall(r"\"([^\"]*)\"", qm.group(2)))
            if qm.group(3):
                txt = txt + " " + out.get(f"const:{qm.group(3)}", "")
            if len(txt) > 15:
                out[f"def:{qm.group(1)}"] = norm(txt)
        # 2026-08-31 (#1377/#1382, F3 Q17/Q34): the mirror-image row `_CONST + ("...")` -
        # directive first, per-question sentence after - was invisible to the pattern above,
        # so those notes could never carry a locale either. Same def:<q> key; a row whose
        # string part is blank (`_A + " " + _B`) is two constants, not a definition: skipped.
        for qm in re.finditer(r"\n\s+(\d{1,3})\s*:\s*(_[A-Z_]+)\s*\+\s*\(?((?:\s*\"[^\"]*\")+)\s*\)?",
                              m.group(1)):
            part = " ".join(re.findall(r"\"([^\"]*)\"", qm.group(3)))
            if f"def:{qm.group(1)}" in out or not part.strip():
                continue
            txt = out.get(f"const:{qm.group(2)}", "") + " " + part
            if len(txt.strip()) > 15:
                out[f"def:{qm.group(1)}"] = norm(txt)
    # 2026-08-31 (#1365, F3 Q18 bracket note): INSTRUCTIONS_BY_NAME rows are notes too -
    # translate_note resolves them by their English string exactly like the number-keyed
    # rows - but were never registered. Registered as def:<ITEM_NAME>.
    m = re.search(r"\nINSTRUCTIONS_BY_NAME\s*=\s*\{(.*?)\n\}", src, re.S)
    if m:
        for qm in re.finditer(r"\n\s+\"([A-Z0-9_]+)\"\s*:\s*\(?((?:\s*\"[^\"]*\")+)\s*\)?", m.group(1)):
            txt = " ".join(re.findall(r"\"([^\"]*)\"", qm.group(2)))
            if len(txt) > 15:
                out[f"def:{qm.group(1)}"] = norm(txt)
    return out


ENGLISH_FUNC = re.compile(
    r"\b(the|of|and|your|you|which|what|how|please|following|were|have|has|this|that|"
    r"with|from|for|are|was|will|would|about|some|ask|asking|survey|questions)\b", re.I)
ALLOWED_EN = re.compile(r"\b(UHC|PhilHealth|YAKAP|Konsulta|BUCAS|GAMOT|NBB|ZBB|MAIFIP"
                        r"|DOH|LGU|PWD|OFW|HMO|health facility|survey)\b", re.I)


def looks_english(s):
    """A candidate that still reads as English is the English sentence, not a translation."""
    return len(ENGLISH_FUNC.findall(ALLOWED_EN.sub(" ", s or ""))) >= 3


def find_translation(hay_lines, english):
    """Take the text that FOLLOWS the complete English note.

    The earlier version matched only the first seven words and returned the remainder of
    the SAME English sentence as the "translation" ("your personal information relevant to
    the survey."). The whole English string has to be consumed first, so match on a
    normalised single-line blob and slice after the match.
    """
    en = norm(english)
    if len(en) < 12:
        return ""
    blob = norm(" ".join(hay_lines))
    low, enl = blob.lower(), en.lower()

    pos, used = low.find(enl), len(enl)
    if pos < 0:                      # PDF reflow: fall back to the longest matching prefix
        words = enl.split()
        for k in range(len(words), max(5, int(len(words) * 0.6)) - 1, -1):
            probe = " ".join(words[:k])
            pos = low.find(probe)
            if pos >= 0:
                used = len(probe)
                break
        if pos < 0:
            return ""

    after = blob[pos + used:].lstrip(" .:-)")
    if not after:
        return ""
    # An enumerator directive is printed immediately above its OPTION LIST, so the text
    # after it runs straight into the ballot boxes. 18 of 368 notes shipped carrying
    # option text ("MASUNOD NA PLION SANA AN SIMBAG [] Health promotion and education
    # ..."), which reads worse on screen than plain English. Everything from the first
    # ballot glyph on belongs to the options, never to the note.
    box = re.search(r"[☐☑☒□]", after)
    if box:
        after = after[:box.start()].rstrip()
        if len(after) < 10:
            return ""
    # A translated note is one sentence and runs to roughly the length of its English.
    # Hunting for "where English resumes" over-captured (it ran past the note into the
    # next block), so cut deterministically: first sentence terminator at least 15 chars
    # in, and never longer than 1.6x the English.
    limit = min(len(after), int(len(en) * 1.6) + 20)
    window = after[:limit]
    m = re.search(r"[.?!](?=\s|$)", window[15:])
    cut = (15 + m.end()) if m else limit
    cand = norm(window[:cut])
    cand = re.sub(r"\s*\d{1,3}\s*\.\s*$", "", cand)
    cand = polish(cand)
    if len(cand) < 10 or looks_english(cand) or cand.lower() == enl:
        return ""
    return cand


# Words that end a clause rather than a sentence - a candidate ending on one was cut off
# mid-phrase by the page break and must not be shipped as a complete note.
DANGLING = {"sa", "ng", "ang", "an", "ti", "iti", "han", "hin", "kan", "nga", "na",
            "ug", "og", "kag", "asin", "para", "sang", "in", "a", "ken"}


def polish(s):
    """Trim the reflow debris that clings to a note pulled out of a two-column PDF."""
    s = (s or "").strip()
    # leading English tail of the sentence we just consumed ("information Bago...",
    # "(UHC) Magtatanong...") - drop bracketed acronyms and lowercase English leftovers
    for _ in range(3):
        m = re.match(r"^\(?[A-Za-z/]+\)?\s+", s)
        if not m:
            break
        first = m.group(0).strip()
        if (first.startswith("(") or first.islower()) and looks_english(first + " of the"):
            s = s[m.end():]
            continue
        if re.fullmatch(r"\(?[A-Z]{2,}\)?", first):      # stray "(UHC)"
            s = s[m.end():]
            continue
        break
    # trailing stray initial of the next English word ("... sa survey. A")
    s = re.sub(r"[\s.]+[A-Za-z]$", "", s).strip(" .:-")
    if s.split() and s.split()[-1].lower() in DANGLING:
        return ""                                        # truncated mid-phrase
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--source", help="folder of F{n}-{Language}_..._Aug21.pdf; dumps text first")
    ap.add_argument("--provenance", choices=["june5", "aug21"], default="june5")
    ap.add_argument("--text-dir", help="default: text/ (june5) or text-aug21/ (aug21)")
    ap.add_argument("--date", default=datetime.date.today().isoformat(),
                    help="provenance date stamp (default: today)")
    ap.add_argument("--overrides", default=os.path.join(HERE, "aug21-overrides.json"))
    ap.add_argument("--merge-into", default=os.path.join(HERE, "notes.json"),
                    help="prior notes.json to merge onto (aug21 only)")
    a = ap.parse_args()

    text_dir = a.text_dir or (os.path.join(HERE, "text-aug21") if a.provenance == "aug21" else TEXT)
    files = {}
    if a.source:
        files = {f"{i}_{l}": n for (i, l), n in dump_source(a.source, text_dir).items()}
        print(f"dumped {len(files)} PDFs -> {text_dir}")

    result = {}
    for inst in ("F1", "F3", "F4"):
        notes = english_notes(inst)
        result[inst] = {"english": notes, "translations": {}}
        got = {lg: 0 for lg in LOCALES}
        for lg in LOCALES:
            p = os.path.join(text_dir, f"{inst}_{lg}.txt")
            if not os.path.exists(p):
                continue
            lines = io.open(p, encoding="utf-8").read().split("\n")
            for key, en in notes.items():
                if key.startswith("def:"):
                    continue      # 2026-08-27: def rows come from note:def:<q>:<LOC> overrides only
                tr = find_translation(lines, en)
                if tr:
                    result[inst]["translations"].setdefault(key, {})[lg] = tr
                    got[lg] += 1
        print(f"[{inst}] {len(notes)} English notes  |  "
              + "  ".join(f"{lg} {got[lg]}" for lg in LOCALES))

    if a.provenance == "aug21":
        prior = json.load(io.open(a.merge_into, encoding="utf-8")) if os.path.exists(a.merge_into) else {}
        result, counts = merge_notes(prior, result, load_overrides(a.overrides),
                                     {"date": a.date, "source": a.source or text_dir,
                                      "files": files})
        print("aug21 merge: " + ", ".join(f"{k} {v}" for k, v in counts.items()))

    if a.json:
        # newline="" is required to SEE the prior file's line endings: universal-newline
        # translation hides the CRLF and every line of the tracked notes.json would flip
        # to LF on a rewrite.
        raw_prior = (io.open(a.merge_into, encoding="utf-8", newline="").read()
                     if os.path.exists(a.merge_into) else "")
        nl = "\r\n" if "\r\n" in raw_prior else "\n"
        with io.open(a.json, "w", encoding="utf-8", newline=nl) as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"\nWrote {a.json}")


if __name__ == "__main__":
    main()
