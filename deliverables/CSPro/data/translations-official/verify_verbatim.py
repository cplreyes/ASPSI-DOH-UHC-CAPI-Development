#!/usr/bin/env python3
r"""Comprehensive verbatim check: deployed CAPI translations vs the DOH-cleared source.

Joins every translatable CAPI string to `official_translations.json` by QUESTION NUMBER
(the CAPI's own English labels carry it: "57. Based on your knowledge...") and classifies
each (item, locale) pair:

  VERBATIM      CAPI text matches the official translation
  NEAR          matches after normalising brackets/punctuation/enumerator directives
  DIVERGENT     both sides have text and they genuinely differ  <- NOT verbatim
  RECOVERABLE   CAPI renders English, but the official source HAS a translation
  NO_OFFICIAL   official source has nothing to compare against
  ENGLISH_BOTH  both sides are English (acronyms, programme names - legitimately so)

The DIVERGENT and RECOVERABLE buckets are the actionable ones: DIVERGENT means the tool
is showing something other than the cleared wording; RECOVERABLE means a cleared
translation exists that the tool is not using.

Comparison is deliberately generous before declaring DIVERGENT, because the official
corpus carries known extraction artifacts (editorial brackets, surviving English
directives). Over-reporting divergence would send ASPSI chasing ghosts.

Run:
    python verify_verbatim.py                # all instruments, summary
    python verify_verbatim.py --detail F3 HIL  # dump the divergent list
    python verify_verbatim.py --json out.json  # machine-readable, for the fix pass
"""
import argparse
import difflib
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
OFFICIAL = os.path.join(HERE, "official_translations.json")
INSTR = OrderedDict([("F1", "FacilityHeadSurvey"), ("F3", "PatientSurvey"),
                     ("F4", "HouseholdSurvey")])
LOCALES = ["FIL", "BCL", "BIS", "CEB", "WAR", "HIL", "ILO"]

LABEL_Q = re.compile(r"^\s*(\d{1,3}(?:\.\d)?)\s*[\.\)]")
NAME_Q = re.compile(r"^Q(\d{1,3})(?:_(\d))?_")

# Enumerator directives are printed once, in English, in the source PDFs; they routinely
# survive the bilingual split. Strip from BOTH sides before comparing so their presence
# or absence never by itself makes a string look divergent.
DIRECTIVES = re.compile(
    r"(READ\s+OPTIONS?\s+OUT\s+LOUD|DO\s+NOT\s+READ[^.]*|SELECT\s+ALL\s+THAT\s+APPLY"
    r"|SELECT\s+ONE\s+ANSWER\s+ONLY"
    r"|ENUMERATOR[^.]*|INTERVIEWER[^.]*)", re.I)
# Skip directives appear IN THE TRANSLATED TEXT too ("Dai <magproceed sa Q15>"), so they
# cannot be matched by English keywords. Everything inside angle brackets is navigation,
# never respondent-facing wording - drop it on both sides or "Dae" vs
# "Dai <magproceed sa Q15>" reads as divergent when one vowel actually differs.
ANGLE = re.compile(r"<[^>]*>")

# CAPI-internal capture fields, not questions. Their labels ("2. Relationship - Other
# (specify) text") are plumbing the respondent never hears, and the join would otherwise
# compare them against the PARENT question's stem and report a false gap.
NOT_A_QUESTION = re.compile(r"(_OTHER_TXT|_SPECIFY|_TXT|_MEDICINES_TXT)$")


def canon(s):
    """Aggressive canonical form for equality testing - never used as output text."""
    if not s:
        return ""
    s = (s.replace("’", "'").replace("‘", "'")
          .replace("“", '"').replace("”", '"')
          .replace("–", "-").replace("—", "-").replace("\xa0", " "))
    s = ANGLE.sub(" ", s)
    s = DIRECTIVES.sub(" ", s)
    s = re.sub(r"^\s*\d{1,3}(?:\.\d)?\s*[\.\)]\s*", "", s)   # leading question number
    s = re.sub(r"[\[\]()]", " ", s)                          # editorial brackets
    s = re.sub(r"[^0-9a-zÀ-ɏ ]+", " ", s.lower())  # keep letters incl accents
    return re.sub(r"\s+", " ", s).strip()


def qnum_of(name, en_label):
    m = LABEL_Q.match(en_label or "")
    if m:
        return m.group(1)
    m = NAME_Q.match(name or "")
    if m:
        return m.group(1) + ("." + m.group(2) if m.group(2) else "")
    return None


def iter_strings(dcf):
    """Yield (item_name, kind, index, {lang: text}) for item labels and value labels."""
    for lvl in dcf["levels"]:
        for rec in lvl.get("records", []):
            for it in rec.get("items", []):
                labs = {l.get("language") or "EN": l.get("text", "")
                        for l in it.get("labels", [])}
                yield it["name"], "stem", -1, labs
                for vs in it.get("valueSets", []) or []:
                    for i, val in enumerate(vs.get("values", []) or []):
                        vlabs = {l.get("language") or "EN": l.get("text", "")
                                 for l in val.get("labels", [])}
                        yield it["name"], "option", i, vlabs


def best_official_option(off_opts, en_text):
    """Pick the official option whose ENGLISH matches this value label.

    EXACT match first. Fuzzy matching alone is unsafe here: "Level 3 Hospital" and
    "Level 1 Hospital" are ~94% similar, so a similarity threshold happily paired them
    and would have written the wrong label onto an option CODE. Any fuzzy fallback
    therefore also requires the two sides to contain the SAME digits - option lists in
    this instrument are full of near-identical text distinguished only by a number
    (Level 1/2/3, 1st/2nd/3rd visit, Q97.1 vs 97.2).
    """
    ce = canon(en_text)
    if not ce:
        return None
    digits = lambda s: sorted(re.findall(r"\d+", s or ""))
    de = digits(en_text)
    best, score = None, 0.0
    for pair in off_opts:
        c = canon(pair.get("en", ""))
        if not c:
            continue
        if c == ce:
            return pair.get("tr", "")
        if digits(pair.get("en", "")) != de:
            continue                       # differs by a number - never fuzzy-match it
        r = difflib.SequenceMatcher(None, ce, c).ratio()
        if r > score:
            best, score = pair.get("tr", ""), r
    return best if score >= 0.93 else None


def classify(capi, official, english):
    cc, co, ce = canon(capi), canon(official), canon(english)
    if not cc or cc == ce:
        if co and co != ce:
            return "RECOVERABLE"
        return "ENGLISH_BOTH" if ce else "NO_OFFICIAL"
    if not co:
        return "NO_OFFICIAL"
    if co == ce:
        return "ENGLISH_BOTH"
    if cc == co:
        return "VERBATIM"
    r = difflib.SequenceMatcher(None, cc, co).ratio()
    if r >= 0.92:
        return "NEAR"
    if cc in co or co in cc:
        return "NEAR"
    return "DIVERGENT"


def run(args):
    official = json.loads(io.open(OFFICIAL, encoding="utf-8").read())
    report = OrderedDict()

    for inst, base in INSTR.items():
        dcf = json.loads(io.open(os.path.join(CSPRO, inst, base + ".dcf"),
                                 encoding="utf-8-sig").read())
        off_inst = official.get(inst, {})
        counts = {lg: Counter() for lg in LOCALES}
        findings = {lg: [] for lg in LOCALES}

        # A question number can front SEVERAL CAPI stem items: a payment matrix splits
        # Q92 into a tick-list plus grid columns, and Q5 becomes birth-month + birth-year.
        # The official source has ONE stem for the question, so attribute it to the single
        # best-matching CAPI item and treat the rest as sub-fields - otherwise every extra
        # column reports a bogus missing translation.
        rows = list(iter_strings(dcf))
        primary = {}
        for name, kind, idx, labs in rows:
            if kind != "stem" or NOT_A_QUESTION.search(name):
                continue
            en = labs.get("EN", "")
            qn = qnum_of(name, en)
            if not qn or qn not in off_inst:
                continue
            off_en = canon(off_inst[qn].get("EN", {}).get("stem", ""))
            score = difflib.SequenceMatcher(None, canon(en), off_en).ratio() if off_en else 0
            if qn not in primary or score > primary[qn][1]:
                primary[qn] = (name, score)
        primary_name = {qn: v[0] for qn, v in primary.items()}

        for name, kind, idx, labs in rows:
            en = labs.get("EN", "")
            qn = qnum_of(name, en)
            if kind == "stem" and (NOT_A_QUESTION.search(name)
                                   or primary_name.get(qn) != name):
                for lg in LOCALES:
                    counts[lg]["NOT_COMPARED"] += 1   # capture field or matrix sub-field
                continue
            if not qn or qn not in off_inst:
                for lg in LOCALES:
                    counts[lg]["NO_OFFICIAL"] += 1
                continue
            entry = off_inst[qn]
            en_off = entry.get("EN", {})
            for lg in LOCALES:
                off = entry.get(lg)
                if not off:
                    counts[lg]["NO_OFFICIAL"] += 1
                    continue
                if kind == "stem":
                    off_text = off.get("stem", "")
                else:
                    pairs = [{"en": e, "tr": t} for e, t in
                             zip(en_off.get("options", []), off.get("options", []))]
                    off_text = best_official_option(pairs, en) or ""
                verdict = classify(labs.get(lg, ""), off_text, en)
                counts[lg][verdict] += 1
                if verdict in ("DIVERGENT", "RECOVERABLE"):
                    # FULL strings, never truncated: these become translation-map KEYS,
                    # and apply_translations matches on the complete English label. A
                    # clipped key silently matches nothing and the fix no-ops - the exact
                    # failure behind #1233's Q49.
                    findings[lg].append({
                        "item": name, "kind": kind, "index": idx, "q": qn,
                        "english": en, "capi": labs.get(lg, ""),
                        "official": off_text, "verdict": verdict,
                        # the CLEARED side's ENGLISH for this question - the only way to
                        # prove, per item, that both documents mean the same question by
                        # that number. F3 numbers Q107 differently from the cleared
                        # questionnaire, so without this the wrong stem gets applied.
                        "official_en": (en_off.get("stem", "") if kind == "stem" else ""),
                        # for options the map key is the BARE option text (see
                        # cspro_helpers._value_set), which is shared instrument-wide
                        "key": en if kind == "stem" else en,
                    })
        report[inst] = {"counts": {lg: dict(counts[lg]) for lg in LOCALES},
                        "findings": findings}

    ORDER = ["VERBATIM", "NEAR", "DIVERGENT", "RECOVERABLE", "ENGLISH_BOTH",
             "NO_OFFICIAL", "NOT_COMPARED"]
    tot = Counter()
    for inst, data in report.items():
        print(f"\n{'=' * 92}\n{inst}\n{'=' * 92}")
        print(f"{'locale':<7}" + "".join(f"{k:>13}" for k in ORDER) + f"{'verbatim%':>11}")
        for lg in LOCALES:
            c = data["counts"][lg]
            for k in ORDER:
                tot[k] += c.get(k, 0)
            comparable = c.get("VERBATIM", 0) + c.get("NEAR", 0) + c.get("DIVERGENT", 0)
            pct = 100.0 * (c.get("VERBATIM", 0) + c.get("NEAR", 0)) / comparable if comparable else 0
            print(f"{lg:<7}" + "".join(f"{c.get(k, 0):>13}" for k in ORDER) + f"{pct:>10.1f}%")

    comparable = tot["VERBATIM"] + tot["NEAR"] + tot["DIVERGENT"]
    print(f"\n{'=' * 92}\nALL INSTRUMENTS x 7 LOCALES\n{'=' * 92}")
    for k in ORDER:
        print(f"  {k:<14}{tot[k]:>8}")
    if comparable:
        print(f"\n  Of strings that CAN be compared ({comparable:,}): "
              f"{100.0 * (tot['VERBATIM'] + tot['NEAR']) / comparable:.1f}% verbatim, "
              f"{100.0 * tot['DIVERGENT'] / comparable:.1f}% divergent")
    print(f"  RECOVERABLE (tool shows English, cleared translation exists): {tot['RECOVERABLE']:,}")

    if args.detail:
        inst, lg = args.detail
        print(f"\n{'=' * 92}\nDETAIL {inst} / {lg}\n{'=' * 92}")
        for f in report[inst]["findings"][lg][:args.limit]:
            print(f"\n  [{f['verdict']}] Q{f['q']} {f['item']} ({f['kind']})")
            print(f"    EN       : {f['english'][:120]}")
            print(f"    CAPI     : {f['capi'][:120] or '(English fallback)'}")
            print(f"    OFFICIAL : {f['official'][:120] or '(none)'}")

    if args.json:
        with io.open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", nargs=2, metavar=("INSTRUMENT", "LOCALE"))
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--json")
    run(ap.parse_args())
