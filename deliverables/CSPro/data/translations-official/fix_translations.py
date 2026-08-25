#!/usr/bin/env python3
r"""Repair a translation map against the DOH-cleared June-5 questionnaire.

Generalises the three repairs proven on F1 Bicolano (shipped as F1 v2.1.3, #1233/#1277)
to any instrument x locale:

  TRIM   a stored value whose stem still has its enumerator directive glued on. Since
         notes_lookup began rendering directives separately per locale, an embedded one
         prints TWICE. That is the defect a tester filed as #1277, and it is present in
         six locales nobody has swept (#1278).
  STEM   a question stem the tablet renders in English because the map has no key for it.
  OPTION a value-set option label in the same state.

SOURCING RULE
-------------
Every character written comes from official_translations.json, i.e. the cleared June-5
PDFs. Nothing is composed, and English is never edited. The only transformation is a CUT
(removing a directive, a routing annotation, or English debris left by the PDF split) -
so whatever survives is verbatim cleared text.

THE CUTS, AND WHY EACH BOUNDARY IS SAFE
---------------------------------------
* Directive: a run of >=3 consecutive ALL-CAPS words that OPENS with a known directive
  word. The opener test is load-bearing - "3+ caps words" alone also matches an acronym
  list, and cutting there destroys content:
      "... iba pang pinagkukunan (hal. MAIFIP, DSWD, PCSO)"  ->  "... (hal."
  The cleared PDFs print the ENGLISH directive first in every language, so READ / DO NOT
  READ / SELECT catch all seven locales; the local-language openers are listed too for
  the cases where only the translated directive survived the split.
* Routing annotation: the first '<' or '('-wrapped margin note (<only for those who
  answered ... in Q65>) - a questionnaire margin note, never respondent-facing.
* English bleed: a leading fragment that appears verbatim inside the cleared ENGLISH stem
  (Q140's Bicolano begins 'billing" policy? Sa saindong pagtanaw, ...').

WHAT IS DELIBERATELY NOT WRITTEN
--------------------------------
* Options whose cleared translation IS the English (proper nouns like "NBB compliance").
  Storing English as its own translation adds noise and hides real gaps.
* option_confidence "positional" - index pairing on a monolingual source file is
  unverified and can bind a translation to the WRONG option code.
* Any option English text that two questions want to translate differently. One key is
  shared by every value set in the instrument, so the map cannot express it; those are
  reported as CONFLICT and need per-question keys (a generator change).
* "Other (specify)" boxes - captioning a free-text box with the question stem stops
  telling the enumerator what the box is for.

    python fix_translations.py --report                    # matrix across everything
    python fix_translations.py --instrument F3 --locale hil
    python fix_translations.py --instrument F3 --locale hil --apply
    python fix_translations.py --all --apply
"""
import argparse
import io
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stem_validator as sv

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
OFFICIAL = os.path.join(HERE, "official_translations.json")

sys.path.insert(0, CSPRO)
from cspro_helpers import _value_pair_key  # keys MUST match walk_labeled_nodes

BASE = {"F1": "FacilityHeadSurvey", "F3": "PatientSurvey", "F4": "HouseholdSurvey"}
LOCALES = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]

LABEL_Q = re.compile(r"^\s*(\d{1,3}(?:\.\d)?)\s*[\.\)]")
CAPWORD = re.compile(r"^[A-Z][A-Z'’/\-\.,:;()]*$")

# A label that starts with a question number is NOT necessarily that question's stem: the
# question's sub-fields inherit the number too. These markers identify them. Case-insensitive
# on purpose - the dictionaries use both "Other (specify)" and "Other (Specify)".
SUBFIELD = re.compile(
    r"(\u2014|--|\bOther \(specify\)|\btext\b|\bAmount\b|Auto-computed|\[DO NOT ASK\]"
    r"|Total value|\bPHP\b|per line|line item)",
    re.I,
)


# A caps run only starts a directive if it opens with one of these. English first,
# because the cleared PDFs always print the English directive ahead of the translation.
DIRECTIVE_OPENERS = {
    "READ", "DO", "SELECT", "ASK", "PROBE", "SHOW", "NOTE", "ENUMERATOR", "INTERVIEWER",
    "RESPONDENT", "IF", "ONLY",
    # Bikol / Tagalog / Bisaya / Cebuano / Waray / Hiligaynon / Ilocano
    "BASAHON", "BASAHAON", "BASAHIN", "BASAHA", "BASAEN", "BASAHUN",
    "DAI", "DAE", "PILION", "PLION", "PILIION",
    "HUWAG", "HINDI", "PILIIN", "AYAW", "PILIA", "PILIEN", "SAAN", "PILII",
    "KUNG", "ISA", "PUMILI",
}

# Explicit start offsets where the PDF split left English debris the generic rule cannot
# see, because the debris word is missing from the English side it would be matched
# against. Naming them is honest and checkable; the text kept after is still verbatim.
BLEED_PREFIX = {("F1", "140", "BCL"): 'billing" policy?'}


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def clean(s):
    """Drop the PDF's column rule, which the text run carries into the value."""
    return norm(re.sub(r"\s*\|\s*", " ", s or ""))


def loose(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def directive_at(s):
    """-> word index where an enumerator directive starts, or None.

    Delegated to stem_validator, which scans for the OPENER directly. The version that
    lived here only tested the first word of a caps run, so an acronym in front of the
    directive hid it entirely - "... billing (ZBB) READ OPTIONS OUT LOUD ..." started its
    run at "(ZBB)" and the directive was never found. That bug suppressed real trims as
    well as leaving directives in proposed stems.
    """
    return sv.directive_at(s)


def head(s):
    """The option text before its first bracketed qualifier.

    The dictionary and the cleared PDF write the same editorial note differently:

        .dcf   "Emergency cart contents (hospitals only)"
        PDF    "Emergency cart contents <This is a licensing requirement only for
                hospitals. Not applicable to primary care facilities>"

    loose() compares the whole string, so those never match and the option is filed as
    "not present in cleared set" even though its translation was extracted correctly.
    Comparing the heads joins them - guarded, at the call site, by a uniqueness test on
    BOTH sides so a head shared by two options can never bind the wrong translation.
    """
    return loose(re.split(r"[<(\[]", s or "", 1)[0])


def cut(text):
    """-> the stem portion of a cleared string, verbatim, or '' if nothing survives."""
    s = clean(text).lstrip("| ").strip()
    if not s:
        return ""
    ends = []
    lt = s.find("<")
    if lt > 0:
        ends.append(lt)
    at = directive_at(s)
    if at is not None and at > 0:
        ends.append(len(" ".join(s.split()[:at])))
    if ends:
        s = s[:min(ends)]
    return norm(s).strip()


def drop_english_bleed(s, en_stem):
    """Drop a leading fragment that is really the TAIL of the English question."""
    en_l = norm(en_stem).lower()
    if not en_l:
        return s
    for _ in range(3):
        m = re.match(r"^([^?]{0,60}\?)\s*(.+)$", s, re.S)
        if not m:
            break
        head, rest = m.group(1).strip(), m.group(2).strip()
        if len(head) >= 4 and head.lower().strip(" ?\"'") in en_l and rest:
            s = rest
        else:
            break
    return s


def lab(node, code):
    for l in node.get("labels") or []:
        if l.get("language") == code:
            return l.get("text", "")
    return ""


def scan_dcf(inst, code):
    """-> (stems, options) each [(qnum, item, english)] for labels shown in English."""
    path = os.path.join(CSPRO, inst, BASE[inst] + ".dcf")
    d = json.loads(io.open(path, encoding="utf-8-sig").read())
    stems, options, seen = [], [], set()

    def visit(node, cur_q=None, cur_item=None):
        if isinstance(node, dict):
            nm = node.get("name")
            if nm and node.get("labels"):
                en, loc = lab(node, "EN"), lab(node, code)
                m = LABEL_Q.match(en or "")
                if m:
                    cur_q, cur_item = m.group(1), nm
                    if en == loc and en not in seen:
                        seen.add(en)
                        stems.append((cur_q, nm, en))
            for vs in node.get("valueSets") or []:
                for v in vs.get("values") or []:
                    en, loc = lab(v, "EN"), lab(v, code)
                    if cur_q and en and en == loc:
                        options.append((cur_q, cur_item, en))
            for k, v in node.items():
                if k not in ("labels", "valueSets"):
                    visit(v, cur_q, cur_item)
        elif isinstance(node, list):
            for it in node:
                visit(it, cur_q, cur_item)

    visit(d)
    return stems, options


# Proposals a human review PARKED - never auto-applied, however many times plan() re-runs.
PARKED_OPTIONS = {
    # 2026-08-17 three-lens panel: F3 Hiligaynon "No" -> "Wala/Indi" is verbatim-cleared
    # but a bare option key binds to EVERY value set carrying "No" (77 in F3); parked
    # until per-value-set adjudication.
    ("F3", "hil", "No"),
}

# Stems the 2026-08-17 three-lens panel REJECTED (contamination, wrong binding, meaning
# drift, or directive residue - see the #1250/#1263/#1264/#1269 closing notes). plan()
# keeps proposing them (the report is a worklist), but --stems must never ship them.
PARKED_STEMS = {
    ("F1", "fil", "66"), ("F1", "bis", "127"),
    ("F1", "ceb", "71"), ("F1", "ceb", "73"), ("F1", "ceb", "74"), ("F1", "ceb", "151"),
    ("F1", "ilo", "56"), ("F1", "ilo", "129"), ("F1", "ilo", "131"),
    ("F3", "bcl", "92"), ("F3", "ilo", "93"), ("F4", "bcl", "91"),
}


def dcf_key_index(inst):
    """-> (stem_keys, opt_keys, en_by_key) for the 2026-08-17 name-scoped map format.

    stem_keys: EN label -> [item:/vs: keys];  opt_keys: EN value label -> [val: keys];
    en_by_key: name-scoped key -> EN label (so guards written for text keys keep
    working on migrated maps). Key shapes come from cspro_helpers.walk_labeled_nodes
    via _value_pair_key - the one shared contract."""
    path = os.path.join(CSPRO, inst, BASE[inst] + ".dcf")
    d = json.loads(io.open(path, encoding="utf-8-sig").read())
    stem_keys, opt_keys, en_by_key = defaultdict(list), defaultdict(list), {}

    def visit(node):
        if isinstance(node, dict):
            nm = node.get("name")
            if nm and node.get("labels"):
                en = lab(node, "EN")
                if en:
                    stem_keys[en].append("item:" + nm)
                    en_by_key["item:" + nm] = en
            for vs in node.get("valueSets") or []:
                vsn, en_vs = vs.get("name"), lab(vs, "EN")
                if vsn and en_vs:
                    stem_keys[en_vs].append("vs:" + vsn)
                    en_by_key["vs:" + vsn] = en_vs
                for v in vs.get("values") or []:
                    en_v = lab(v, "EN")
                    if vsn and en_v:
                        k = f"val:{vsn}:{_value_pair_key(v)}"
                        opt_keys[en_v].append(k)
                        en_by_key[k] = en_v
            for k, v in node.items():
                if k not in ("labels", "valueSets"):
                    visit(v)
        elif isinstance(node, list):
            for it in node:
                visit(it)

    visit(d)
    return stem_keys, opt_keys, en_by_key


def name_scope(p):
    """Convert a plan's ENGLISH-keyed adds to name-scoped keys before writing.

    apply_translations (2026-08-17) hard-rejects text keys, so the legacy apply path
    shipped nothing but a broken build. Existing non-English values are never
    overwritten - the plan was built against the same map, but re-checking here makes
    the write idempotent."""
    stem_keys, opt_keys, _ = dcf_key_index(p["inst"])
    cur = json.loads(io.open(p["path"], encoding="utf-8").read())

    def convert(adds, index):
        out = {}
        for en, val in adds.items():
            for key in index.get(en, []):
                if cur.get(key) not in (None, "", en, key):
                    continue
                out[key] = val
        return out

    p["stem_adds"] = convert(p["stem_adds"], stem_keys)
    p["opt_adds"] = convert(p["opt_adds"], opt_keys)
    return p


def plan(inst, loc):
    """-> dict describing every change proposed for one instrument x locale."""
    code = loc.upper()
    mpath = os.path.join(CSPRO, inst, "translations", loc + ".json")
    if not os.path.exists(mpath):
        return None
    cur = json.loads(io.open(mpath, encoding="utf-8").read())
    off = json.loads(io.open(OFFICIAL, encoding="utf-8").read()).get(inst, {})
    _, _, en_by_key = dcf_key_index(inst)

    trims = {}
    for k, v in cur.items():
        if not isinstance(v, str):
            continue
        # If the ENGLISH LABEL itself carries the directive, the directive is part of the
        # approved label and the translation is right to mirror it - the qsf layer only
        # re-emits directives for question stems, so nothing is doubled and trimming would
        # simply delete an enumerator instruction. Found on the value-set option
        # "Refuse to answer (DO NOT READ OUT LOUD)".
        en_of_k = en_by_key.get(k, k) if ":" in k else k
        if directive_at(norm(en_of_k)) is not None:
            continue
        at = directive_at(norm(v))
        if at is None or at == 0:
            continue
        kept = norm(" ".join(norm(v).split()[:at])).strip()
        if kept and kept != norm(v):
            trims[k] = kept

    dcf_stems, dcf_opts = scan_dcf(inst, code)

    stem_adds, stem_skips = {}, []
    for q, item, en in dcf_stems:
        if SUBFIELD.search(en):
            # Roster cells, amount boxes, auto-computed totals and Other-(Specify) text
            # fields all inherit a label beginning with the PARENT question's number.
            # Writing the question stem onto them captions a one-line input with a whole
            # question and stops telling the enumerator what the field is.
            stem_skips.append((q, item, "sub-field of the question, not the stem"))
            continue
        rec = off.get(q) or {}
        raw = cut((rec.get(code) or {}).get("stem") or "")
        pre = BLEED_PREFIX.get((inst, q, code))
        if pre and raw.startswith(pre):
            raw = raw[len(pre):].strip()
        en_stem = cut((rec.get("EN") or {}).get("stem") or "")
        val = sv.strip_paren_debris(drop_english_bleed(raw, en_stem))
        if not val:
            stem_skips.append((q, item, "no cleared translation"))
        elif en_stem and loose(val) == loose(en_stem):
            stem_skips.append((q, item, "cleared translation is the English"))
        elif cur.get("item:" + item) not in (None, "", en):
            stem_skips.append((q, item, "map already holds a value"))
        else:
            # A blank previous cell in this locale means the PDF rows shifted up, so
            # this entry is probably the neighbour's text (F4 Q143 got Q142's question).
            prev_blank = False
            try:
                prev_q = str(int(float(q)) - 1)
                prev = (off.get(prev_q) or {}).get(code) or {}
                prev_blank = not norm(prev.get("stem") or "")
            except (TypeError, ValueError):
                prev_blank = False
            ok, why = sv.validate(en, val, en_stem, q, prev_locale_blank=prev_blank)
            if ok and (inst, loc, q) in PARKED_STEMS:
                ok, why = False, "parked by review - see PARKED_STEMS"
            if ok:
                stem_adds[en] = val
            else:
                stem_skips.append((q, item, why))

    stem_adds, stem_dupes = sv.dedupe_across_questions(stem_adds)
    for k, why in stem_dupes.items():
        stem_skips.append(("?", k[:40], why))

    proposals, where, opt_skips = defaultdict(set), defaultdict(set), []
    for q, item, en in dcf_opts:
        if (inst, loc, en) in PARKED_OPTIONS:
            opt_skips.append((q, en, "parked by review - see PARKED_OPTIONS"))
            continue
        where[en].add(q)
        rec = off.get(q) or {}
        b, e = rec.get(code) or {}, rec.get("EN") or {}
        if b.get("option_confidence") != "matched":
            opt_skips.append((q, en, "positional pairing - unverified"))
            continue
        eo_list, bo_list = e.get("options") or [], b.get("options") or []
        if len(eo_list) != len(bo_list):
            opt_skips.append((q, en, "cleared option counts differ"))
            continue
        hit = None
        for eo, bo in zip(eo_list, bo_list):
            if loose(eo) == loose(en):
                hit = cut(bo) or clean(bo)
                break
        if hit is None:
            # Fall back to the option head, for the note-rendering mismatch described on
            # head(). Only when the head identifies exactly ONE option on each side - in
            # the cleared set AND among this question's dictionary options - so an
            # ambiguous head is skipped rather than guessed.
            he = head(en)
            if he:
                cands = [(eo, bo) for eo, bo in zip(eo_list, bo_list) if head(eo) == he]
                # Count DISTINCT dictionary labels, not rows. A question can carry the
                # same option in more than one value set (Q121 lists each licensing row
                # twice); identical labels are not an ambiguity, they take the same
                # translation. Counting rows made the guard reject exactly the case it
                # was written to allow.
                same_dcf = {loose(x[2]) for x in dcf_opts
                            if x[0] == q and head(x[2]) == he}
                if len(cands) == 1 and len(same_dcf) == 1:
                    hit = cut(cands[0][1]) or clean(cands[0][1])
        if hit is None:
            opt_skips.append((q, en, "not present in cleared set"))
        elif not hit or loose(hit) == loose(en):
            opt_skips.append((q, en, "cleared translation is the English"))
        else:
            ok, why = sv.validate_option(en, hit)
            if ok:
                proposals[en].add(hit)
            else:
                opt_skips.append((q, en, why))

    opt_adds, conflicts = {}, []
    for en, vals in proposals.items():
        # per-key already-translated filtering happens in name_scope() at apply time

        if len(vals) > 1:
            conflicts.append((en, sorted(where[en]), sorted(vals)))
        else:
            opt_adds[en] = next(iter(vals))

    return {
        "inst": inst, "locale": loc, "path": mpath, "keys": len(cur),
        "trims": trims, "stem_adds": stem_adds, "opt_adds": opt_adds,
        "conflicts": conflicts, "stem_skips": stem_skips, "opt_skips": opt_skips,
    }


def apply_plan(p):
    obj = json.loads(io.open(p["path"], encoding="utf-8").read())
    obj.update(p["trims"])
    obj.update(p["stem_adds"])
    obj.update(p["opt_adds"])
    with io.open(p["path"], "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    return len(p["trims"]) + len(p["stem_adds"]) + len(p["opt_adds"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instrument", choices=list(BASE))
    ap.add_argument("--locale")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--stems", action="store_true",
                    help="also apply question stems. OFF by default: the 2026-08-14 audit "
                         "rejected 68%% of proposed stems because the cleared-PDF extraction "
                         "is not clean enough at scale (multi-question blobs, section "
                         "headings, roster headers). Trims and options are unaffected.")
    ap.add_argument("--json", help="write the full plan to this path")
    a = ap.parse_args()

    combos = []
    if a.all or a.report:
        combos = [(i, l) for i in BASE for l in LOCALES]
    elif a.instrument and a.locale:
        combos = [(a.instrument, a.locale)]
    else:
        ap.error("give --instrument and --locale, or --all / --report")

    plans, total = [], 0
    print(f"{'inst/locale':<14}{'trims':>7}{'stems':>7}{'options':>9}{'conflict':>10}{'keys':>7}")
    for inst, loc in combos:
        p = plan(inst, loc)
        if p is None:
            continue
        plans.append(p)
        n = len(p["trims"]) + len(p["stem_adds"]) + len(p["opt_adds"])
        total += n
        print(f"{inst + '/' + loc:<14}{len(p['trims']):>7}{len(p['stem_adds']):>7}"
              f"{len(p['opt_adds']):>9}{len(p['conflicts']):>10}{p['keys']:>7}")
    print(f"\nTOTAL changes proposed: {total}")

    if a.json:
        with io.open(a.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump([{k: v for k, v in p.items() if k != "path"} for p in plans],
                      fh, ensure_ascii=False, indent=1)
        print(f"plan -> {a.json}")

    if a.apply:
        for p in plans:
            if not a.stems:
                p["stem_adds"] = {}
            name_scope(p)
            n = apply_plan(p)
            print(f"  applied {n:>4} -> {p['inst']}/{p['locale']}.json")


if __name__ == "__main__":
    main()
