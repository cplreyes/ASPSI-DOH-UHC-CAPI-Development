#!/usr/bin/env python3
r"""One honest defect sweep over an instrument's ENTIRE Aug-21 write set.

The PERMANENT home of the sweep the wave ran out of `<ws>/task-N/_defect_sweep.py`
(task-17 F1 -> task-28 F4). Task 48 promoted it here, stripped of the two task-scoped
hand-review tables (`CLEARED`, `PRECISE`) that made the task copies un-reusable, and
parameterised on `--inst`, so a later wave runs the SAME detector instead of forking it
again. It also carries the row-inheritance gate this task exists to close:

    duplicate-label   two codes of one value set would carry the same translated label
                      while their ENGLISH labels differ - one option row inherited its
                      neighbour's translation. Well-formed, right language, right length,
                      so none of the value-level families below can see it: it is only
                      visible in the map the apply WOULD leave behind, which is why it is
                      a GATE over that map and not a `classify()` family.

It reads `aug21_apply_diff.json` - the report `apply_aug21.py` writes on every run,
including a DRY run - so the sweep never touches a map, a .dcf or the generator.

    python _defect_sweep.py --inst F4                    # the table + the gate
    python _defect_sweep.py --inst F3 --family truncated # dump every row in one family
    python _defect_sweep.py --inst F4 --overrides        # locale-scoped aug21-overrides rows
    python _defect_sweep.py --inst F4 --fail-on-pre      # STRICT gate (a publishing wave)
    python _defect_sweep.py --inst F4 --diff <dryrun.json> --maps-dir <restored baseline>

Exit code: 0 clean, 1 when the duplicate-label gate BLOCKS. `--fail-on-pre` widens "blocks"
from "a set this apply writes into" to "any un-ruled set over a live value set"; rulings
live in `duplicate_label_accepted.json` and each one carries a reason.

Families, in the order a reviewer cares about:

  duplicate-label     (gate, see above)
  english-furniture   an English enumerator directive, section heading, NOTE-LAYER string
                      or own-match rode into the value (extractor residual - REPORT, never
                      an override)
  local-directive     the paper's LOCAL-LANGUAGE repeat of that directive rode in instead
  truncated           the span stops mid-sentence while its English label does not
  vs-offset           the value equals a SIBLING code's translation - it would relabel an
                      answer code
  legend-code-head    the value OPENS with a roster-legend code (`0-Away Wara 1-Present`)
  legend-code-tail    the value ENDS in a legend code the dcf's value set does not define
  english-value       every word of the value is a word of the instrument's own English
  english-anchor-head the value OPENS with a NEIGHBOURING key's English label
  orphan-head         the value OPENS with an orphan `?` / `"?` / `]` glyph
  terminal-stop       the value drops the terminal stop the live value carries
  whitespace-insert   old and new differ ONLY by inserted internal whitespace
  whitespace-remove   old and new differ ONLY by removed internal whitespace
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, CSPRO)
from textnorm import norm_for_match                      # noqa: E402
import anchor_extract as AE                              # noqa: E402
from cspro_helpers import walk_labeled_nodes             # noqa: E402
from apply_aug21 import (DCF_FILE, LOCALES, dcf_english, duplicate_label_rows,   # noqa: E402
                         load_accepted_pre, print_duplicate_label_gate)

INSTRUMENTS = tuple(DCF_FILE)
DEFAULT_DIFF = os.path.join(HERE, "aug21_apply_diff.json")

if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

VAL_RE = re.compile(r"^val:(.+):([^:]+)$")

# English furniture the DIRECTIVE_PATTERNS list does not cover, quoted verbatim from the
# Aug-21 papers (F1 wave; the same boilerplate is printed on the F3/F4 papers).
ENGLISH_EXTRA = [
    (r"Tick the category that corresponds", "tick-the-category"),
    (r"\bNo\.? of [Dd]ays\b", "no-of-days-label"),
    (r"These are the requirements for YAKAP/Konsulta", "yakap-doh-note"),
    (r"Our focus is specifically on referrals", "referral-scope-note"),
]
ENGLISH_EXTRA = [(re.compile(p), tag) for p, tag in ENGLISH_EXTRA]

HEADING_MIN = 15          # a heading shorter than this is not distinctive enough


def heading_corpus(ens):
    """Every labelled dcf node whose kind is NOT an anchor kind: a heading printed between
    two questions falls inside a span with nothing to bound it.

    NOTE-LAYER English is deliberately NOT here: it is not a labelled dcf node at all
    (see `note_corpus`)."""
    return sorted({t for k, t in ens.items()
                   if k.split(":", 1)[0] not in AE.ANCHOR_KINDS and len(t) >= HEADING_MIN},
                  key=len, reverse=True)


NOTES_JSON = os.path.join(HERE, "notes.json")
# `Enumerator:` / `Enumerator Instruction (DO NOT READ ALOUD):` - the paper prints the
# label, the extractor's span may start after it, so both forms go in the corpus.
NOTE_PREFIX = re.compile(r"^\s*Enumerator(?:\s+Instruction)?\s*(?:\([^)]*\))?\s*:\s*", re.I)
FILL_ONLY = re.compile(r"^~~[^~]*~~$")          # `~~strip(Q30_NAME)~~` is a fill, not text
NOTE_WINDOW = 40        # chars of NORMALISED note text that must appear verbatim in a value


def note_corpus(inst, path=NOTES_JSON):
    """The note layer's ENGLISH: `intro:` paragraphs and `const:` enumerator directives the
    paper prints around a question but the dcf carries OUTSIDE `walk_labeled_nodes`.

    Returns `(shorts, windows)` on the `norm_for_match` projection:
      * `shorts`  - [(note key, normalised text)] for notes shorter than NOTE_WINDOW,
                    matched whole;
      * `windows` - {normalised NOTE_WINDOW-char run: note key} for longer notes, so a
                    span that carries only PART of a long intro is caught too.
    """
    try:
        raw = io.open(path, encoding="utf-8").read()
    except OSError:
        return [], {}
    block = (json.loads(raw).get(inst) or {}).get("english") or {}
    shorts, windows = [], {}
    for k, txt in block.items():
        t = (txt or "").strip()
        if not t or FILL_ONLY.match(t):
            continue
        for form in (t, NOTE_PREFIX.sub("", t)):
            n = norm_for_match(form)
            if len(n) < HEADING_MIN:
                continue
            if len(n) <= NOTE_WINDOW:
                shorts.append((k, n))
            else:
                for i in range(len(n) - NOTE_WINDOW + 1):
                    windows.setdefault(n[i:i + NOTE_WINDOW], k)
    return sorted(set(shorts), key=lambda s: -len(s[1])), windows


def note_layer_english(val, en, notes):
    """Longest note-layer English run inside `val` that its OWN English label does not
    carry, or None. Matching on the normalised projection is what makes it robust to the
    page-break artefacts a raw-substring test cannot survive."""
    shorts, windows = notes
    nv = norm_for_match(val or "")
    nen = norm_for_match(en or "")
    if not nv:
        return None
    best = None
    for k, n in shorts:                       # sorted longest-first, first hit is longest
        if n in nv and n not in nen:
            best = (k, n)
            break
    if windows:
        for i in range(len(nv) - NOTE_WINDOW + 1):
            w = nv[i:i + NOTE_WINDOW]
            k = windows.get(w)
            if k and w not in nen and (best is None or len(w) > len(best[1])):
                best = (k, w)
                break
    return f"note-layer {best[0]} {best[1][:26]!r}" if best else None


WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
CONNECTIVE = {"and", "or", "of", "the", "for", "to", "in", "on", "a", "an", "&"}
TOKEN = re.compile(r"[^\s]+")

LEGEND_TAIL = re.compile(r"\s+\d{1,2}$")
# The Aug-21 F4 roster legend also prints its codes with an EN DASH and trailing, so a
# span that runs into the next legend row ends `... ) -55 -` and one that starts inside
# one opens `8 - Mga kwalipikado ...`.
LEGEND_DASH_TAIL = re.compile(r"\s-?\d{1,3}\s*[–—-]\s*$")
LEGEND_HEAD = re.compile(r"^\d{1,2}\s*[-–—]\s*\S")
WS = re.compile(r"\s+")


def _titled(tok):
    core = tok.strip("()[].,:;?!\"'")
    return bool(core) and core[0].isupper() and core.isascii()


def _ends_sentence(tok):
    return tok.rstrip("\")]’'\"").endswith(("?", ".", "!"))


def _connective(tok):
    return tok.strip("()[].,:;?!\"'").lower() in CONNECTIVE


def english_heading_tail(val, en):
    """Longest offending Title-Case run in `val`, or None. The run must OPEN a new
    sentence (the question ended and English kept going), which is what separates a paper
    SECTION HEADING that bled in from the Title-Case opening of an ordinary option."""
    nen = norm_for_match(en or "")
    toks = TOKEN.findall(val or "")
    best = None
    i = 0
    while i < len(toks):
        if not _titled(toks[i]) or i == 0 or not _ends_sentence(toks[i - 1]):
            i += 1
            continue
        j, titled = i, 0
        while j < len(toks) and (_titled(toks[j]) or _connective(toks[j])):
            titled += 1 if _titled(toks[j]) else 0
            j += 1
        while j - 1 > i and not _titled(toks[j - 1]):
            j -= 1                                   # never end a run on a connective
        run = " ".join(toks[i:j])
        if (titled >= 3 and run.isascii() and norm_for_match(run)
                and norm_for_match(run) not in nen
                and (best is None or len(run) > len(best))):
            best = run
        i = max(j, i + 1)
    return ("english-heading " + best[:28]) if best else None


def english_own_match(val, en, en_blob):
    """True when the whole value is short ENGLISH text lifted from a DIFFERENT label."""
    v = (val or "").strip()
    if not v or len(WORD_RE.findall(v)) > 4:
        return None
    if any(ord(c) > 127 for c in v):
        return None
    nv = norm_for_match(v)
    if not nv or nv in norm_for_match(en):
        return None
    if re.search(r"(?<![A-Za-z])" + re.escape(nv) + r"(?![A-Za-z])", en_blob):
        return "english-own-match"
    return None


CAPS_RUN = re.compile(r"(?:(?<=\s)|^)(?:[A-ZÑÁÉÍÓÚ]"
                      r"[A-ZÑÁÉÍÓÚ'’/-]{1,}\s+){2,}"
                      r"[A-ZÑÁÉÍÓÚ]"
                      r"[A-ZÑÁÉÍÓÚ'’/-]{1,}")
LOCAL_IMPERATIVE = re.compile(
    r"\b(?:Dae pagbasahon|Ayaw basaha|Ayaw i-?basa|Huwag basahin|Indi basahon|"
    r"Diri basahon|Saan a basaen|Pilion an mga dapat|Piliin ang|Basahon an|Basahin ang)\b")


def whitespace_only(old, new):
    """'insert' when new only ADDS internal whitespace to old, 'remove' when it only takes
    whitespace away, else None. Wave rule: an inserted internal space is a PDF line-break
    artefact and is held; a removed stray space is a fix and is written."""
    if old is None or new is None or old == new:
        return None
    if WS.sub("", old) != WS.sub("", new):
        return None
    return "insert" if len(WS.findall(new)) > len(WS.findall(old)) else "remove"


ORPHAN_HEAD = re.compile(r'^[\s?!."”“\')\]:;,–—-]{1,6}(?=[\w(\[])')
ANCHOR_HEAD_MIN = 14      # shorter English labels open too many legitimate values
QNUM = re.compile(r"^\d+(?:\.\d+)*\.?\s*")   # `89.1. `, `21. ` - the paper omits it here


def anchor_label_head(val, en, anchor_ens):
    """The value OPENS with a DIFFERENT dcf key's full English label.

    `heading_corpus()` deliberately skips anchor labels, so `english-furniture` is
    structurally blind to this shape: the Aug-21 F4 papers print Q89.1's English above
    Q89, and the span opened there instead of at Q89's own translation."""
    v = (val or "").lstrip()
    nen = norm_for_match(en or "")
    for lab in anchor_ens:
        # The papers print the question NUMBER on the English row but the extractor's
        # span starts after it, so `89.1. What is the name of the facility?` reaches the
        # value as `What is the name of the facility?`. Match both forms.
        for form in (lab, QNUM.sub("", lab)):
            if (len(form) >= ANCHOR_HEAD_MIN and v.startswith(form) and len(v) > len(form)
                    and norm_for_match(form) not in nen):
                return form[:34]
    return None


def classify(key, val, en, sibs, headings, en_blob, corpus, old=None,
             anchor_ens=(), notes=((), {})):
    head = anchor_label_head(val, en, anchor_ens)
    if head:
        return "english-anchor-head", head
    m = ORPHAN_HEAD.match(val or "")
    if m:
        return "orphan-head", repr(m.group(0))
    if AE.has_directive(val):
        return "english-furniture", "DIRECTIVE_PATTERNS"
    for rx, tag in ENGLISH_EXTRA:
        if rx.search(val):
            return "english-furniture", tag
    nl = note_layer_english(val, en, notes)
    if nl:
        return "english-furniture", nl
    for h in headings:
        if h in val and h not in en:
            return "english-furniture", "section-heading " + h[:28]
    own = english_own_match(val, en, en_blob)
    if own:
        return "english-furniture", own
    tail = english_heading_tail(val, en)
    if tail:
        return "english-furniture", tail
    for m in CAPS_RUN.finditer(val):
        if m.group(0) not in en:
            return "local-directive", m.group(0)[:40]
    m = LOCAL_IMPERATIVE.search(val)
    if m:
        return "local-directive", m.group(0)
    mv = VAL_RE.match(key)
    if mv:
        n = norm_for_match(val)
        for code, sib in sibs.get(mv.group(1), {}).items():
            if code != mv.group(2) and n and norm_for_match(sib) == n:
                return "vs-offset", f"== code {code}"
    # The roster legend the paper prints without ballot boxes.
    if LEGEND_HEAD.search(val):
        return "legend-code-head", val[:12]
    if LEGEND_TAIL.search(val) and not LEGEND_TAIL.search(en or ""):
        return "legend-code-tail", val[-8:]
    if LEGEND_DASH_TAIL.search(val) and not LEGEND_DASH_TAIL.search(en or ""):
        return "legend-code-tail", val[-8:]
    if AE.own_match_is_english(val, corpus):
        return "english-value", val[:28]
    ws = whitespace_only(old, val)
    if ws:
        return f"whitespace-{ws}", repr(old)[:30]
    # Terminal-stop loss, measured against the LIVE value rather than the English label:
    # the Aug-21 page break drops the sentence's full stop (`... motubag.` -> `...
    # motubag`). Invisible to the English-length heuristics below, which only fire on a
    # value that is SHORTER than its label.
    #
    # A general "new is a proper PREFIX of old" rule was built here first and REMOVED: it
    # fires on 148 rows of which 146 are the wave's own improvements, because the live
    # June-5 values carry the next option glued on. Its two real rows are already caught
    # by `truncated` below, so the family only cost signal.
    if old is not None and val != old and old.rstrip(".!?") == val and old[-1:] in ".!?":
        return "terminal-stop", f"lost {old[-1:]!r}"
    if len(en) > 40 and en[-1:] in "?." and val[-1:] not in "?.!…»)":
        return "truncated", f"ends {val[-22:]!r}"
    if len(en) > 40 and val.count("(") != val.count(")"):
        return "truncated", "unbalanced paren"
    if len(en) > 40 and len(val) * 2 < len(en):
        return "truncated", "under half the English length"
    return None, ""


# Families a wave HOLDS as locale-scoped overrides. english-furniture / local-directive
# are an extractor residual and the plan forbids expressing those as overrides - they are
# listed so `--overrides` can emit a candidate row, and the wave still has to decide.
HELD = ("truncated", "vs-offset", "legend-code-head", "legend-code-tail", "english-value",
        "whitespace-insert", "terminal-stop", "english-furniture", "local-directive",
        "english-anchor-head", "orphan-head")
REASON = {
    "truncated": "Aug-21 extract cuts the span at an embedded English anchor, so the value "
                 "stops mid-sentence",
    "vs-offset": "Aug-21 extract assigns a SIBLING code's translation to this code "
                 "(FINDINGS.md sec-3 value-set offset)",
    "legend-code-head": "Aug-21 roster legend prints no ballot boxes, so the span opens "
                        "inside the previous option's legend CODE",
    "legend-code-tail": "Aug-21 roster legend numbers this option with a code the dcf "
                        "value set does not define, so the code cannot be stripped",
    "english-value": "Aug-21 span is the paper's ENGLISH carrying on, not a translation",
    "whitespace-insert": "Aug-21 value differs from the live value only by an inserted "
                         "internal space (PDF line-break artefact)",
    "terminal-stop": "Aug-21 span drops the sentence's terminal stop that the live value "
                     "carries (page-break artefact)",
    "english-furniture": "Aug-21 span carries an English note / section heading / definition "
                         "block the paper prints beside the question",
    "local-directive": "Aug-21 span carries the paper's LOCAL-LANGUAGE repeat of an "
                       "enumerator directive",
    "english-anchor-head": "Aug-21 span OPENS with a neighbouring question's English label, "
                           "so the value glues that question's text to this one",
    "orphan-head": "Aug-21 span OPENS with an orphan punctuation glyph left by the paper's "
                   "line break",
}


def load_map(maps_dir, loc):
    path = os.path.join(maps_dir, f"{loc}.json")
    m = json.loads(io.open(path, encoding="utf-8").read())
    m.pop("_meta", None)
    return m


def duplicate_label_gate(inst, diff, maps_dir, english):
    """The gate rows for the map each locale's apply WOULD leave behind.

    Same judgement as `apply_aug21.run()`, from the DIFF instead of from a live merge, so
    the sweep can be pointed at any dry-run report (a restored-baseline rehearsal included)
    without re-running the merge."""
    gate = []
    for loc in LOCALES:
        blk = diff.get(loc)
        if blk is None:
            continue
        writes = blk.get("writes") or {}
        after = load_map(maps_dir, loc)
        after.update(writes)
        for key in blk.get("removed") or []:     # Task 49: `remove: true` deletes the row
            after.pop(key, None)
        for row in duplicate_label_rows(after, english, writes):
            row["locale"] = loc
            gate.append(row)
    return gate


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--inst", required=True, choices=INSTRUMENTS)
    ap.add_argument("--diff", default=DEFAULT_DIFF,
                    help="apply_aug21.py --report JSON (default aug21_apply_diff.json)")
    ap.add_argument("--maps-dir",
                    help="translation-map dir to judge (default F<n>/translations) - point "
                         "it at the restored baseline a wave rehearses on")
    ap.add_argument("--family", help="dump every row of ONE family")
    ap.add_argument("--overrides", action="store_true",
                    help="emit locale-scoped aug21-overrides.json rows for the HELD families")
    ap.add_argument("--fail-on-pre", action="store_true",
                    help="STRICT duplicate-label gate: an un-ruled PRE-EXISTING collision "
                         "over a live value set blocks too (see duplicate_label_accepted.json)")
    a = ap.parse_args(argv)

    inst = a.inst
    maps_dir = a.maps_dir or os.path.join(CSPRO, inst, "translations")
    dcf_path = os.path.join(CSPRO, inst, DCF_FILE[inst])
    doc = json.loads(io.open(a.diff, encoding="utf-8").read())
    if inst not in doc:
        raise SystemExit(f"{a.diff} carries no {inst} block "
                         f"(it has {', '.join(sorted(doc)) or 'nothing'})")
    diff = doc[inst]

    ens = dcf_english(inst)                       # reads the BUILT .dcf; no generator run
    headings = heading_corpus(ens)
    en_blob = " | ".join(norm_for_match(t) for t in ens.values())
    corpus = AE.english_words(AE.dcf_anchors(dcf_path))
    anchor_ens = sorted({t for k, t in ens.items()
                         if k.split(":", 1)[0] in AE.ANCHOR_KINDS and len(t) >= ANCHOR_HEAD_MIN},
                        key=len, reverse=True)
    notes = note_corpus(inst)
    print(f"{inst}  note-layer corpus: {len(notes[0])} short note(s) + "
          f"{len(notes[1])} {NOTE_WINDOW}-char window(s) from notes.json[{inst}]")

    was = {(loc, r["key"]): r["was"] for loc, b in diff.items() for r in b.get("replaced", [])}
    fam, tag_tally, per_loc, rows = Counter(), defaultdict(Counter), defaultdict(Counter), []
    total = 0
    for loc, blk in diff.items():
        cur = load_map(maps_dir, loc)
        sibs = defaultdict(dict)
        for k, v in cur.items():
            m = VAL_RE.match(k)
            if m:
                sibs[m.group(1)][m.group(2)] = v
        for key, val in (blk.get("writes") or {}).items():
            total += 1
            f, tag = classify(key, val, ens.get(key, ""), sibs, headings, en_blob,
                              corpus, was.get((loc, key)), anchor_ens, notes)
            if f:
                fam[f] += 1
                tag_tally[f][tag] += 1
                per_loc[loc][f] += 1
                rows.append((f, tag, loc, key, ens.get(key, ""), was.get((loc, key)), val))
    print(f"values --apply would write: {total}")
    print(f"values carrying a defect:   {sum(fam.values())}\n")
    for f, n in fam.most_common():
        print(f"  {f:<20}{n:>5}   new-key rows: "
              f"{sum(1 for r in rows if r[0] == f and r[5] is None)}")
        for tag, c in tag_tally[f].most_common(6):
            print(f"      {tag[:52]:<54}{c}")
    fams = [f for f, _ in fam.most_common()]
    if fams:
        print(f"\n  {'locale':<7}" + "".join(f"{f[:16]:>18}" for f in fams))
        for loc in diff:
            print(f"  {loc:<7}" + "".join(f"{per_loc[loc][f]:>18}" for f in fams))

    # The row-inheritance gate. It judges the POST-apply map, not the write set, because a
    # collision needs BOTH sides and the extractor only ever sees one of them.
    gate = duplicate_label_gate(inst, diff, maps_dir, ens)
    blocked = print_duplicate_label_gate(inst, gate, load_accepted_pre(), a.fail_on_pre)

    if a.overrides:
        # Locale-scoped: the defect is in ONE paper, so holding the key for all seven maps
        # would suppress the correct writes the same key carries elsewhere.
        by_key = defaultdict(lambda: {"locs": set(), "fams": set(), "tags": set()})
        for f, tag, loc, key, _en, _w, _val in rows:
            if f not in HELD:
                continue
            e = by_key[key]
            e["locs"].add(loc)
            e["fams"].add(f)
            e["tags"].add(tag)
        out = {}
        for key, e in sorted(by_key.items()):
            fams_ = sorted(e["fams"])
            out[key] = {
                "keep": None,
                "locales": sorted(e["locs"], key=LOCALES.index),
                "reason": "; ".join(REASON[f] for f in fams_)
                          + " [" + ", ".join(sorted(e["tags"])[:3]) + "]"
                          + f" - held (never written), {inst} defect sweep"}
        print(json.dumps(out, ensure_ascii=False, indent=1))
    elif a.family:
        print()
        for f, tag, loc, key, en, w, val in rows:
            if f == a.family:
                print(f"[{loc}] {key}   <{tag}>")
                print(f"     en: {en[:200]!r}")
                print(f"    was: {(w or '<new key>')[:200]!r}")
                print(f"    now: {val[:200]!r}")

    if blocked:
        print(f"\n{inst} duplicate-label gate BLOCKS - see the RED rows above.")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
