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

    python extract_notes.py                 # report coverage
    python extract_notes.py --json notes.json
"""
import argparse
import io
import json
import os
import re
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
TEXT = os.path.join(HERE, "text")
LOCALES = ["FIL", "BCL", "BIS", "CEB", "WAR", "HIL", "ILO"]

# ASCII-ish signature of an English sentence, used to find where the translation stops.
ENGLISH_LINE = re.compile(
    r"^\s*(?:[A-Z][A-Za-z' ,()/-]{12,}|READ |DO NOT |SELECT |ENUMERATOR|INTERVIEWER)")


def norm(s):
    s = (s or "").replace("’", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def english_notes(inst):
    """Pull the English intro/directive strings straight out of the generator."""
    src = io.open(os.path.join(CSPRO, inst, "generate_qsf.py"), encoding="utf-8").read()
    out = OrderedDict()

    m = re.search(r"(?:SECTION_)?INTROS\s*=\s*\{(.*?)\n\}", src, re.S)
    if m:
        for qm in re.finditer(r"(\d{1,3})\s*:\s*(\(?)((?:\s*\"[^\"]*\")+)", m.group(1)):
            txt = " ".join(re.findall(r"\"([^\"]*)\"", qm.group(3)))
            out[f"intro:{qm.group(1)}"] = norm(txt)

    for cm in re.finditer(r"^(_[A-Z_]+)\s*=\s*\(?((?:\s*\"[^\"]*\")+)", src, re.M):
        txt = " ".join(re.findall(r"\"([^\"]*)\"", cm.group(2)))
        if len(txt) > 15 and not txt.startswith("<"):
            out[f"const:{cm.group(1)}"] = norm(txt)
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
    a = ap.parse_args()

    result = {}
    for inst in ("F1", "F3", "F4"):
        notes = english_notes(inst)
        result[inst] = {"english": notes, "translations": {}}
        got = {lg: 0 for lg in LOCALES}
        for lg in LOCALES:
            p = os.path.join(TEXT, f"{inst}_{lg}.txt")
            if not os.path.exists(p):
                continue
            lines = io.open(p, encoding="utf-8").read().split("\n")
            for key, en in notes.items():
                tr = find_translation(lines, en)
                if tr:
                    result[inst]["translations"].setdefault(key, {})[lg] = tr
                    got[lg] += 1
        print(f"[{inst}] {len(notes)} English notes  |  "
              + "  ".join(f"{lg} {got[lg]}" for lg in LOCALES))

    if a.json:
        with io.open(a.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
        print(f"\nWrote {a.json}")
        for inst in result:
            for key, m in list(result[inst]["translations"].items())[:2]:
                print(f"\n  {inst} {key}")
                print(f"    EN : {result[inst]['english'][key][:90]}")
                for lg in list(m)[:2]:
                    print(f"    {lg}: {m[lg][:90]}")


if __name__ == "__main__":
    main()
