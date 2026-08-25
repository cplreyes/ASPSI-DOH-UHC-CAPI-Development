#!/usr/bin/env python3
r"""#1279 - strip non-translation text out of values ALREADY stored in the maps.

The validator added earlier stops such text being WRITTEN. It never looked at what was
already stored, so defects that predate it still reach respondents. Found by byte-checking
the deployed builds:

    F3 Q147 [CEB]  "PLEASE LIST DOWN ALL MEDICINES THAT YOU TOOK FOR THE HEALTH CONDITION"
    F4 Q36  [HIL]  "... ang klase sang disabilidad? 0-No 1-Yes 0Indi 1-Oo"
    F3 Q30  [CEB]  "DO NOT READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY. Ang pasyente ba
                    miyembro sa Indigenous People (IP) community, sama sa Igorot ..."

THE MISTAKE THE FIRST VERSION MADE
----------------------------------
It cut at the FIRST marker and kept one side. But a directive usually LEADS the value, and
`DIRECTIVE_PHRASE` matches only its first few words - so cutting at "READ OPTIONS" left
"OUT LOUD. SELECT ALL THAT APPLY. Ano sa mga masunod ..." as the remainder, which still
contained markers and was therefore judged unusable. 163 values were about to be dropped to
English when most of them hold a complete, correct translation.

This version REMOVES every marker span and keeps the residue, so a translation is recovered
wherever one exists. A key is only removed when nothing survives - and removal (not an
empty string) is what makes apply_translations fall back to English; an empty value renders
blank.

Deletes only; no text is composed.

    python clean_existing.py            # dry run
    python clean_existing.py --apply
"""
import argparse
import glob
import io
import json
import os
import re
import sys

P = (r"C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development"
     r"\deliverables\CSPro\data\translations-official")
sys.path.insert(0, P)
import stem_validator as sv  # noqa: E402

CSPRO = os.path.abspath(os.path.join(P, "..", ".."))

# Instruction wordings seen in the stored values, beyond stem_validator's list. Lower-case
# forms matter because the caps-run detector cannot see them.
# A [...] or (...) span is an instruction only if it READS like one. Filipino wraps ordinary
# translations in square brackets and Ilocano in parentheses as an editorial convention
# (README, "Bracket conventions"), so "[Donasyon mula sa mga charity / NGO]" is a correct
# translation. Treating every bracket as a note deleted 4 good Filipino labels outright.
NOTE_INSIDE = re.compile(
    r"(ask|proceed|skip|only|applicable|relevant|read|select|enumerator|interviewer"
    r"|saludsod|pakiana|kun |kung |laktaw|q\s?\d{1,3}\b|\bQ\d)",
    re.I,
)


def unwrap(s):
    """Strip an editorial bracket/paren pair that wraps the WHOLE value.

    The Ilocano cells print the translation inside parentheses and Filipino inside square
    brackets. Left in place they render on screen as "(Ania ti nagan ti pasilidad?)".
    """
    s = sv.norm(s)
    for _ in range(3):
        m = re.match(r"^\(([^()]*(?:\([^()]*\)[^()]*)*)\)$", s) or re.match(r"^\[(.*)\]$", s)
        if not m:
            break
        inner = sv.norm(m.group(1))
        if not inner or NOTE_INSIDE.search(inner) and len(inner.split()) < 4:
            break
        s = inner
    return s


EXTRA_PHRASE = re.compile(
    r"(check all that apply|select all that apply|select one answer only"
    r"|pilion an dapat|pilion an mga dapat|pilia an ngatanan|pilia ang tanan"
    r"|pilii ang tanan|piliin ang lahat|pilien amin nga|ayaw basaha"
    r"|basaha og kusog|basahon nin makusog|basahin nang malakas"
    r"|laktawi kung|laktaw kung|iwasan basahon)",
    re.I,
)


def directive_span(s):
    """-> (start, end) of an ALL-CAPS directive run, or None.

    The run ENDS at the last consecutive capitalised word, not at the end of the string -
    the first version assumed end-of-string, which is only true when the directive trails.
    """
    at = sv.directive_at(s)
    if at is None:
        return None
    words = s.split()
    j = at
    while j < len(words) and sv.is_caps(words[j]):
        j += 1
    start = len(" ".join(words[:at])) + (1 if at else 0)
    end = len(" ".join(words[:j]))
    return start, end


def marker_spans(s):
    """-> the earliest marker span (start, end, what), or None."""
    cands = []
    d = directive_span(s)
    if d:
        cands.append((d[0], d[1], "ALL-CAPS directive"))
    m = sv.BRACKET_NOTE.search(s)
    if m and NOTE_INSIDE.search(m.group(0)):
        # A [...] span is only a NOTE when it reads like one. Filipino wraps ordinary
        # translations in square brackets and Ilocano in parentheses as an editorial
        # convention (see README) - "[Donasyon mula sa mga charity / NGO]" is a correct
        # translation, not an instruction, and treating it as one deleted it outright.
        cands.append((m.start(), m.end(), "bracketed note"))
    for rx, what in ((sv.DIRECTIVE_PHRASE, "instruction"),
                     (EXTRA_PHRASE, "instruction")):
        m = rx.search(s)
        if m:
            # extend an instruction to the end of its sentence, so "READ OPTIONS" does not
            # leave "OUT LOUD. SELECT ALL THAT APPLY." behind
            end = m.end()
            nxt = s.find(".", end)
            if nxt != -1 and nxt - end < 60:
                end = nxt + 1
            cands.append((m.start(), end, what))
    m = sv.ANSWER_CODES.search(s)
    if m:
        run = re.compile(r"(\s*\b\d\s*-?\s*[A-Za-zÀ-ɏ]+)+").match(s, m.start())
        cands.append((m.start(), run.end() if run else m.end(), "answer codes"))
    if not cands:
        return None
    return min(cands)


# An extraction stutter: the same content word repeated across a linker, so the Ilocano
# "ti kangrunaan a kangrunaan a mangipapaay" reads "the main main provider". Deleting the
# duplicate is a deletion, not a rewrite; the linker and both neighbours are untouched.
DUP_PHRASE = re.compile(r"\b(\w{5,})\s+(a|nga|ti|ang|an)\s+\1\b", re.I)

LEAD_JUNK = re.compile(r"^[\s.,;:)\]\-–—|]+")
NUM_LEAD = re.compile(r"^\s*\d{1,3}(\.\d)?\s*[.)]\s*")

DANGLING = {
    "han", "an", "sa", "kan", "ng", "ang", "sang", "nga", "ti", "iti", "dagiti", "ken",
    "ug", "og", "para", "ha", "hin", "in", "a", "na", "no", "kag", "o", "ni", "si",
}


def caps_run_len(s):
    """Longest run of consecutive ALL-CAPS words.

    A single caps word is an acronym the source uses on purpose (DOH, MAIFIP, UHC, GAMOT).
    Two or more in a row is a directive fragment the span removal did not fully consume -
    "PILI-A ANG TANAN NGA NAGAKA-", "DAPAT NA KASIMBAGAN", "SKIP THIS".
    """
    best = run = 0
    for w in s.split():
        if sv.is_caps(w):
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def is_question_key(k):
    """A map key is a QUESTION if it is numbered or ends in a question mark.

    Everything else is a value-set OPTION label - short, often one or two words, and never
    ending in punctuation. Judging both by the same rules is what made the first pass throw
    away 83 perfectly good Filipino option labels like "[Inirekomenda ng kaibigan/pamilya]":
    they failed a minimum-length test and a terminal-punctuation test that only questions
    should have to pass.
    """
    k = (k or "").strip()
    return bool(re.match(r"^\d{1,3}(\.\d)?\s*[.)]", k)) or k.endswith("?")


def clean_value(v, key=""):
    """-> residue with every marker span removed, or '' when nothing usable survives."""
    # keep ONE copy: "kangrunaan a kangrunaan a mangipapaay" -> "kangrunaan a mangipapaay"
    s = DUP_PHRASE.sub(lambda m: m.group(1), unwrap(sv.norm(v)))
    for _ in range(10):
        sp = marker_spans(s)
        if not sp:
            break
        start, end, _w = sp
        s = sv.norm(s[:start] + " " + s[end:])
    # tidy what the removals exposed
    for _ in range(3):
        before = s
        s = LEAD_JUNK.sub("", s)
        s = NUM_LEAD.sub("", s)
        s = sv.strip_paren_debris(s)
        s = unwrap(sv.norm(s))
        if s == before:
            break
    question = is_question_key(key)

    # A question ends at its question mark. Anything short trailing after the last one is
    # answer-option or column debris the grid dragged in ("... tigadumanan? Walk Lakaw").
    if question and "?" in s:
        head, _, tail = s.rpartition("?")
        if tail.strip() and len(tail.split()) <= 5:
            s = sv.norm(head + "?")

    min_words = 3 if question else 1
    if len(s.split()) < min_words or not sv.parens_balanced(s) or marker_spans(s):
        return ""

    # An English fragment left at the head - "to respondents in areas with GAMOT facility
    # (Naala yo kadi ...)" - is the tail of an instruction the span removal only partly ate.
    lead = re.findall(r"[A-Za-zÀ-ɏ]{3,}", s)[:6]
    if lead and sum(1 for w in lead if w.lower() in sv.ENGLISH_LEAD) / len(lead) >= 0.5:
        return ""
    # residue quality: no directive fragment left, and not cut before its object
    if caps_run_len(s) >= 2:
        return ""
    words = s.split()
    if words[-1].strip(".,;:").lower() in DANGLING:
        return ""

    # A complete QUESTION ends on sentence-final punctuation. Option labels do not, so the
    # rule is scoped to questions. This one rule replaces an
    # endless list of language-specific checks: it catches residues cut mid-clause
    # ("... sa imong pangunahing"), leftover English fragments ("... to respondents in
    # areas with GAMOT") and half-eaten directives ("... hospital/clinic. dapat na
    # kasimbagan") in every locale at once. Anything failing it is dropped to English
    # fallback rather than shown half-finished.
    if question and s[-1] not in "?.!)":
        return ""
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dump", help="write the full diff to this JSON path")
    a = ap.parse_args()

    trims = drops = 0
    diff = []
    for inst in ("F1", "F3", "F4"):
        for path in sorted(glob.glob(os.path.join(CSPRO, inst, "translations", "*.json"))):
            obj = json.loads(io.open(path, encoding="utf-8").read())
            loc = os.path.basename(path)[:3]
            todo = {}
            for k, v in obj.items():
                if not isinstance(v, str) or not v.strip():
                    continue
                # the marker is part of the approved ENGLISH label -> the translation is
                # right to mirror it
                if marker_spans(sv.norm(k)):
                    continue
                # Two reasons to touch a value: it carries a marker, or it is wrapped in
                # the source's editorial bracket/paren pair, which renders on screen.
                nv = sv.norm(v)
                if not marker_spans(nv) and unwrap(nv) == nv and not DUP_PHRASE.search(nv):
                    continue
                kept = clean_value(v, k)
                todo[k] = kept
                diff.append({"instrument": inst, "locale": loc, "key": k,
                             "was": sv.norm(v), "now": kept,
                             "action": "trim" if kept else "drop"})
            if not todo:
                continue
            nt = sum(1 for x in todo.values() if x)
            nd = len(todo) - nt
            trims += nt
            drops += nd
            print(f"{inst}/{loc}: trim {nt}, drop {nd}")
            if a.apply:
                for k, kept in todo.items():
                    if kept:
                        obj[k] = kept
                    else:
                        obj.pop(k, None)
                with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(obj, fh, ensure_ascii=False, indent=1)

    print(f"\n{'APPLIED' if a.apply else 'WOULD APPLY'}: {trims} trims, {drops} key removals")
    if a.dump:
        json.dump(diff, io.open(a.dump, "w", encoding="utf-8", newline="\n"),
                  ensure_ascii=False, indent=1)
        print(f"diff -> {a.dump}")


if __name__ == "__main__":
    main()
