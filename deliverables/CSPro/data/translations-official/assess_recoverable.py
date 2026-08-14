#!/usr/bin/env python3
r"""How much of the RECOVERABLE bucket is SAFE to apply verbatim, right now?

RECOVERABLE = the deployed tool renders English while the DOH-cleared source does have a
translation. Those are pure wins - no new translation work, no wording decision, just use
what was already cleared. But the extracted corpus carries known damage, so a string is
only safe if it looks like a clean translation rather than extraction residue.

A candidate is rejected when it:
  - still contains English function words (the split failed, English came along)
  - carries page furniture ("ICF ver.", "Translated Questionnaire ver.")
  - carries an enumerator directive that belongs in the instruction note, not the prompt
  - is suspiciously long or short next to its English (bled from a neighbouring question,
    or truncated)
  - is wrapped in the source's editorial brackets and nothing else

Everything rejected is reported by reason, so the residue can be fixed rather than lost.

Run:  python assess_recoverable.py [--sample 12] [--json safe_to_apply.json]
"""
import argparse
import difflib
import io
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "verbatim_report.json")

ENGLISH_FUNC = re.compile(
    r"\b(the|of|and|or|your|you|which|what|how|please|following|were|have|has|this|"
    r"that|with|from|for|are|was|did|does|do|is|in|on|at|to|a|an|any|all|not|no)\b", re.I)
FURNITURE = re.compile(r"(ICF\s*ver|Translated\s+Questionnaire|PSA\s+SSRCS|Page\s+\d)", re.I)
DIRECTIVE = re.compile(
    r"(READ\s+OPTIONS?|DO\s+NOT\s+READ|SELECT\s+ALL|SELECT\s+ONE|ENUMERATOR|INTERVIEWER)",
    re.I)
# The same directives appear TRANSLATED in the cleared source, so an English-only pattern
# misses them: a Cebuano Q113 candidate carried "AYAW BASAHA OG KUSOG ANG MGA KAPILIAN"
# (do not read the options aloud) straight into the question prompt.
DIRECTIVE_LOCAL = re.compile(
    r"(AYAW\s+(PAG)?BASAH|DAI\s+PAGBASAH|DAE\s+PAGBASAH|HUWAG\s+BASAH|DIRI\s+BASAH"
    r"|INDI\s+BASAH|SAAN\s+A\s+BASA|BASAHON\s+AN|BASAHA\s+ANG|BASAHIN\s+ANG"
    r"|PILIA\s+ANG|PILION\s+AN|PUMILI\s+NG|PILIEN\s+TI|PILI\s+SANG)", re.I)
# PDF text extraction occasionally corrupts a character ("{hilHealth" for "PhilHealth").
# A brace/pipe/backslash inside a word is never legitimate questionnaire text.
CORRUPT_CHAR = re.compile(r"[{}\\|~^<>]|\b\w*[{}]\w*\b")
# Form-field labels welded onto a stem: "... nagsugod? Month Bulan Year Tuig"
GLUED_FIELD = re.compile(r"\b(Month|Year|Day|Hours?|Minutes?|Amount|Pesos)\b\s+\S+\s+"
                         r"\b(Month|Year|Day|Hours?|Minutes?|Amount|Pesos)\b", re.I)
# proper nouns / acronyms that legitimately stay English inside a translated string
ALLOWED = re.compile(
    r"\b(PhilHealth|GAMOT|BUCAS|YAKAP|Konsulta|UHC|HMO|NBB|ZBB|MAIFIP|LGBTQIA|OFW|PIN|"
    r"DOH|LGU|PWD|SSS|GSIS|4Ps|ID|TB|HIV|COVID|X-Ray|Tech-Voc)\b", re.I)


PLACEHOLDER = re.compile(r"\[[a-z][a-z0-9_]{3,}\]", re.I)   # e.g. [facility_name_input]

# Trailing enumerator/routing text the cleared cell carries but the CAPI keeps in a
# separate instruction paragraph. Not part of the question, so ignore it when proving
# the two documents mean the same question by a given number.
_JOIN_TAIL = re.compile(
    r"(READ\s+OPTIONS?|DO\s+NOT\s+READ|SELECT\s+ALL|SELECT\s+ONE|ENUMERATOR\s+INSTRUCTION"
    r"|INTERVIEWER|ASKED\s+ONLY|IF\s+MORE\s+THAN|PLEASE\s+COUNT|IT\s+IS\s+FINE|<).*$",
    re.I | re.S)


def _jc(s):
    s = re.sub(r"^\s*\d{1,3}(?:\.\d)?\s*[\.\)]\s*", "", s or "")
    s = _JOIN_TAIL.sub(" ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def join_agrees(capi_en, cleared_en, threshold=0.60):
    """Do the CAPI and the cleared questionnaire mean the same question by this number?"""
    a, b = _jc(capi_en), _jc(cleared_en)
    if not a or not b:
        return False
    if a == b or a.startswith(b) or b.startswith(a) or a in b or b in a:
        return True
    n = min(len(a), len(b))
    return difflib.SequenceMatcher(None, a[:n], b[:n]).ratio() >= threshold


def clean_for_apply(s):
    """Undo the source's editorial wrapping so the string is fit to write into the tool.

    The Ilocano PDF wraps whole translations in parentheses and Filipino sometimes in
    square brackets - "(No adda teleconsultation, nagballigikayo kadi...)". Those are the
    document's own convention marking "this is the translation", not part of the sentence,
    so an unmatched-safe unwrap is applied. Nothing else about the string is touched.
    """
    s = (s or "").strip()
    for _ in range(3):
        if len(s) > 2 and ((s[0] == "(" and s[-1] == ")") or (s[0] == "[" and s[-1] == "]")):
            inner = s[1:-1]
            if (inner.count("(") == inner.count(")")
                    and inner.count("[") == inner.count("]")):
                s = inner.strip()
                continue
        break
    return re.sub(r"\s+([.?!,])", r"\1", s).strip()


def english_residue(s):
    """Count English function words remaining, ignoring allowed proper nouns."""
    return len(ENGLISH_FUNC.findall(ALLOWED.sub(" ", s or "")))


def assess(english, official):
    o = (official or "").strip()
    if not o:
        return "empty"
    if o.startswith("|") or o.startswith("-") or "|" in o:
        return "page furniture"        # table-cell pipe survived the text extraction
    if FURNITURE.search(o):
        return "page furniture"
    if DIRECTIVE.search(o) or DIRECTIVE_LOCAL.search(o):
        return "enumerator directive embedded"
    if CORRUPT_CHAR.search(o):
        return "corrupt character"
    if GLUED_FIELD.search(o):
        return "glued form labels"
    n = english_residue(o)
    if n >= 3:
        return "English residue"
    if n >= 1 and len(o.split()) <= 6:
        return "English residue"
    if re.fullmatch(r"[\[\(].*[\]\)]", o) and len(o.split()) <= 2:
        return "bracket-only fragment"
    le, lo = len(english or ""), len(o)
    if le and lo > 3.0 * le:
        return "too long vs English (likely bled)"
    if le > 40 and lo < 0.30 * le:
        return "too short vs English (likely truncated)"
    return "SAFE"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=10)
    ap.add_argument("--json")
    a = ap.parse_args()

    rep = json.loads(io.open(REPORT, encoding="utf-8").read())
    per_locale = {}
    safe_out = {}
    samples = {}

    # Row-offset guard. When the PDF block boundaries slip, a question inherits its
    # NEIGHBOUR's translation - F3 Q107 ("Which of the following did you use to pay...")
    # was handed Q106's "Pila ang kabug-osan nga bill sang imo confinement?" ("How much
    # is the total bill?"). Shipping that puts a different question on screen. The tell is
    # that one cleared STEM ends up claimed by two question numbers, so index those and
    # refuse every one of them - the correct owner cannot be decided mechanically.
    # Index the FULL cleared corpus, not just the findings: the neighbour that a stem was
    # stolen from is usually already correct in the tool, so it never appears as a
    # finding and the duplication is invisible from this side. F3 Q107 inheriting Q106's
    # stem was missed exactly that way.
    official = json.loads(io.open(os.path.join(HERE, "official_translations.json"),
                                  encoding="utf-8").read())
    nrm = lambda s: re.sub(r"\s+", " ", (s or "").strip().lower())
    shared_stem = {}
    for inst, questions in official.items():
        per_lg = {}
        for qn, entry in questions.items():
            for lg, d in entry.items():
                if lg == "EN":
                    continue
                stem = nrm((d or {}).get("stem", ""))
                if stem:
                    per_lg.setdefault(lg, {}).setdefault(stem, set()).add(qn)
        for lg, seen in per_lg.items():
            shared_stem[(inst, lg)] = {k for k, qs in seen.items() if len(qs) > 1}

    for inst, data in rep.items():
        for lg, findings in data["findings"].items():
            c = per_locale.setdefault(lg, Counter())
            for f in findings:
                if f["verdict"] != "RECOVERABLE":
                    continue
                if (f["kind"] == "stem"
                        and re.sub(r"\s+", " ", f["official"].strip().lower())
                        in shared_stem.get((inst, lg), ())):
                    c["shared with another question"] += 1
                    continue
                # Per-item join proof: the two documents must agree that this NUMBER means
                # this QUESTION. F3's Q107 is "Which of the following did you use to pay
                # for the total bill?" in the CAPI but "How much was the total bill?" in
                # the cleared questionnaire, so number-matching alone would have written
                # the wrong prompt onto the screen.
                if f["kind"] == "stem" and not join_agrees(f.get("english"),
                                                           f.get("official_en")):
                    c["question numbering differs"] += 1
                    continue
                verdict = assess(f["english"], f["official"])
                c[verdict] += 1
                if verdict == "SAFE":
                    safe_out.setdefault(inst, {}).setdefault(lg, []).append({
                        "item": f["item"], "kind": f["kind"], "index": f["index"],
                        "q": f["q"],
                        # "english" is the translation-map KEY and must be the COMPLETE
                        # label - apply_translations matches the whole string.
                        "english": f["english"],
                        "apply": clean_for_apply(f["official"]),
                    })
                    samples.setdefault(lg, []).append(f)

    reasons = ["SAFE", "English residue", "enumerator directive embedded",
               "shared with another question", "question numbering differs", "corrupt character", "glued form labels",
               "page furniture", "too long vs English (likely bled)",
               "too short vs English (likely truncated)", "bracket-only fragment", "empty"]
    print(f"{'locale':<7}" + "".join(f"{r[:13]:>15}" for r in reasons) + f"{'safe%':>8}")
    tot = Counter()
    for lg in sorted(per_locale):
        c = per_locale[lg]
        for r in reasons:
            tot[r] += c[r]
        n = sum(c.values())
        print(f"{lg:<7}" + "".join(f"{c[r]:>15}" for r in reasons)
              + f"{(100.0 * c['SAFE'] / n if n else 0):>7.0f}%")
    n = sum(tot.values())
    print(f"\n{'ALL':<7}" + "".join(f"{tot[r]:>15}" for r in reasons)
          + f"{(100.0 * tot['SAFE'] / n if n else 0):>7.0f}%")
    print(f"\nSAFE to apply verbatim right now: {tot['SAFE']:,} of {n:,} recoverable strings")

    for lg in sorted(samples):
        print(f"\n--- {lg}: examples that would be filled ---")
        for f in samples[lg][:a.sample // 2 or 3]:
            print(f"  Q{f['q']} {f['item']}")
            print(f"    EN    : {f['english'][:78]}")
            print(f"    APPLY : {f['official'][:78]}")

    if a.json:
        with io.open(a.json, "w", encoding="utf-8") as fh:
            json.dump(safe_out, fh, ensure_ascii=False, indent=1)
        print(f"\nWrote {a.json}")


if __name__ == "__main__":
    main()
