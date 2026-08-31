#!/usr/bin/env python3
"""F2 mode of the paper extractor.

Anchors on the F2 PWA's English strings (spec/english-strings.json, produced by
`npm run dump:english`) instead of a CSPro dcf, and emits ENGLISH-TEXT-KEYED pairs
per locale because the PWA store (spec/translations/{loc}.json) is flat English-keyed.
Span rule is the anchor rule from anchor_extract.py: translation = text between one
English anchor and the next kept anchor. No line/column assumptions, so the Bicolano
inline layout extracts identically.

F2-specific rules (differ from the F1/F3/F4 extractor):
  * F2_MIN_BOUND / F2_MIN_EMIT = 2 so 'Yes'/'No'/'Male' options bound AND emit;
    an anchor shorter than SHORT_ANCHOR normalized chars counts only when the paper
    prefixes it with a box glyph (option layout), so a bare 'no' inside a translation
    never cuts a span. The MAX_OCC runaway guard counts only the hits that SURVIVE
    that box filter — capping the raw finditer list instead would silently discard
    real option boundaries on a paper where a short anchor is also a common word
    (Ilocano 'no' matches 122x raw but is box-prefixed only 40x).
  * Back-to-back hits of the SAME anchor with nothing but whitespace/box glyphs
    between them (Bicolano '☐ Administrator Administrator') collapse into ONE echo
    occurrence flagged 'echo-english' (the raw gap would otherwise read as 'empty').
  * Distinct English strings that normalize identically are reported as collisions
    and the translation is emitted under every colliding original key.

Task 21b (2026-08-26) added the Aug-21 paper LAYOUT rules. Task 16b gave this module
anchor_extract's clean_span()/qa_flags() but left Task 14's SPAN logic in place, and
Task 22 measured the result: 29% of the F2 write set defective. The rules are the F1
16b/16c round expressed in what F2 actually has — spec KINDS instead of dcf key kinds
(see `Aug-21 F2 layout` below, and the `meta=` argument of extract_text()):

  1. an OPTION label (choice.label and nothing else) counts only behind a ballot box,
     and its span never crosses one — `Professional development opportunities` is
     Q109's option and also sits inside Q107's translation, where it cut 26 values
     down to a strict prefix of the live value;
  2. a SECTION TITLE counts only behind its section letter (`C. YAKAP/Konsulta
     Package`) — the same words inside Q32's translation cut it in half and handed the
     title the SELECT-ALL directive that followed;
  3. the papers' English furniture (input labels, `(Specify …)`, the employment
     definitions block, the GPS header) ENDS a span, and is the `english-furniture` net
     if it survives; the note label (`Note:` / `Tandaan:` / `Pahinumdom:`), a trailing
     run of sub-question numbers (`71a. 71b.`) and a trailing section letter are
     stripped;
  4. value-set siblings are the choice labels sharing a parent item id: they are passed
     to qa_flags(siblings=) — the sibling net was inert on the F2 side — AND they are a
     span boundary in their own right, because the papers print the two Likert
     vocabularies as a BOX-LESS run (`Never Hindi kailanman Rarely Bihira …`) where the
     next sibling label is the only thing that ends an option's span;
  5. a label the paper printed in a LONGER form anchors on its 12-word prefix and is
     always `label-condensed`; an anchor the paper never printed becomes a
     `not-in-paper` worklist row instead of vanishing, and an anchor the paper DID print
     whose every occurrence a gate rejected is `gate-rejected` — a different worklist
     reason, because `not-in-paper` would be factually wrong about the paper.

Usage (PowerShell):
  $env:PYTHONIOENCODING='utf-8'
  python anchor_extract_f2.py --source "C:/.../raw/Survey-Instruments-2026-08-21/Translations" `
      --english-strings "C:/.../deliverables/F2/PWA/app/spec/english-strings.json" `
      --out "C:/.../deliverables/CSPro/data/translations-official/out-aug21/F2"
"""
import argparse
import importlib.util
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Prefer the committed Day-0 copy next to this file; fall back to the gitignored
# on-disk original. Explicit path, so the two can never be confused.
_CANDIDATES = [HERE / "anchor_extract.py",
               HERE.parents[1] / "translations-paper-extract" / "anchor_extract.py"]
_AE_PATH = next(p for p in _CANDIDATES if p.exists())
_spec = importlib.util.spec_from_file_location("anchor_extract", _AE_PATH)
_ae = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ae)          # safe: anchor_extract.py guards main()
pdf_text, build_norm, norm_for_match = _ae.pdf_text, _ae.build_norm, _ae.norm_for_match
clean_span, qa_flags, LANGS = _ae.clean_span, _ae.qa_flags, _ae.LANGS
cut_at_box, anchor_prefix = _ae.cut_at_box, _ae.anchor_prefix
condensed_candidate, SKIP_NOTE = _ae.condensed_candidate, _ae.SKIP_NOTE

CODE_TO_LOC = {"FIL": "fil", "BCL": "bcl", "BIS": "bis", "CEB": "ceb",
               "WAR": "war", "HIL": "hil", "ILO": "ilo"}
# Report/emit order — the same order apply-paper-translations.py (Task 15) walks
# its LOCALES, so the QA table and the apply report read row-for-row.
LOCALES = ["fil", "ceb", "bis", "ilo", "hil", "war", "bcl"]
LOC_TO_PAPER = {CODE_TO_LOC[code]: paper for paper, code in LANGS}
F2_MIN_BOUND = 2       # 'No' must bound a span
F2_MIN_EMIT = 2        # ... and be emitted
SHORT_ANCHOR = 6       # below this, an anchor counts only when box-prefixed on paper
MAX_OCC = 64           # runaway guard, applied to KEPT (box-filtered) hits per anchor
_BOX_BEFORE = re.compile(r"[☐☑☒□■❑]\s*$")
_ANY_BOX = re.compile(r"[☐☑☒□■❑]")

# --- the box-less SCALE RUN (fix round 1) -------------------------------------------
# The brief's fact 4 says an option's span ends at the next box glyph OR the next sibling
# label. Only the box half was implemented, so the two Likert vocabularies — which the
# seven papers print as one box-less run, `Never Hindi kailanman Rarely Bihira Sometimes
# Minsan Often Madalas Always Lagi` (F2_FIL.txt) — had every occurrence rejected by the
# box gate: 10 scale strings x 7 locales unanchorable, and 42 rows that were clean before
# the gate turned into worklist rows. A run of siblings is trusted, and nothing else is:
F2_RUN_MIN = 3         # distinct members of ONE value set before a box-less run counts
F2_RUN_GAP = 60        # normalised chars between two members (a printed row, not prose)
# Task 48: normalised length beyond which the shared span of an empty-predecessor option
# PAIR is holding TWO translations. Same value as anchor_extract.PAIR_BLOCK_RATIO.
F2_PAIR_BLOCK_RATIO = 2.0
F2_PAIR_BLOCK_MIN_EN = 20   # ... and only for an English label long enough that a
                            # doubling cannot just be a verbose rendering of one
                            # short word (`Casual` -> `Saan a patinayon` is 2.7x)

# --------------------------------------------------------------- Aug-21 F2 layout --
# The spec KINDS that gate where an anchor may count. F2 has no CSPro value sets, so
# `choice.label` is what `val:` is on the F1 side and `section.title` is what the
# record/level labels are — page furniture that also occurs inside running text.
OPTION_KINDS = frozenset({"choice.label"})
TITLE_KINDS = frozenset({"section.title"})

# A section title counts behind its letter (`C. YAKAP/Konsulta Package`, `E2. …`).
_SECT_BEFORE = re.compile(r"(?:^|[\s>)\]])[A-Z]\d?\.\s*$")

# English FURNITURE the seven Aug-21 F2 papers print inside a question's span. Every
# pattern below was counted in all seven text-aug21/F2_*.txt dumps before it was added
# (occurrences per paper in the comment); each ENDS the span, exactly as an English
# NOTE does on the F1 side, because the paper prints it AFTER the translation.
F2_FURNITURE_PATTERNS = (
    r"\bNumber of (?:days|hours)\b",                      # 5x — the item's inputLabel
    r"\(Specify\b[^)]{0,40}\)",                           # 2-5x — `(Specify the equipment)`
    r"\bYears?(?:\(s\))?(?=[^?.!]{0,40}\bMonths?(?:\(s\))?\b)",   # 1x — `Year(s) Month(s)`
    r"\bMonth\b(?=[^?.!]{0,60}\bDay\b[^?.!]{0,60}\bYear\b)",      # 3x — `Month Day Year`
    r"\b\d\.\s*Regular Employment\s*:",                   # 1x — the definitions block
    r"\bA doctor's professional fee is\b",                # 1x — the KAP section gloss
    r"\bPlease think about your experience in this post\b",       # 2x — item preamble
    r"\bGPS Coordinates\b",                               # 1x — the facility header row
    r"\bProvince/HUC\b",                                  # 1x — same row
)
F2_FURNITURE = [re.compile(p) for p in F2_FURNITURE_PATTERNS]

# The note LABEL, in English and in the renderings the papers use (Note: 17x, Tandaan: 1x,
# Pahinumdom: 2x over the seven dumps). It is layout, not content: the live maps hold
# `Ayon sa DOLE, …`, not `Tandaan: Ayon sa DOLE, …`.
_NOTE_LABEL = r"(?:Note|Tandaan|Pahinumdom|Paalala|Pahimangno)"
_LEADING_NOTE = re.compile(r"^\W{0,2}" + _NOTE_LABEL + r"\s*:\s*", re.I)
_TRAILING_NOTE = re.compile(r"(?:\s|^)" + _NOTE_LABEL + r"\s*:\s*$", re.I)
_ANY_NOTE = re.compile(r"\(?\b" + _NOTE_LABEL + r"\s*:", re.I)
# `… ano ang mga implikasyon? 71a. 71b.` and `… ng iyong sagot. A.` — the paper's next
# row number / next section letter, swept up because neither is an anchor.
_TRAILING_QNUMS = re.compile(r"(?:\s*\b\d{1,3}[a-z]?\.)+\s*$")
_TRAILING_SECTION = re.compile(r"(?:\s|^)[A-Z]\d?\.\s*$")

# The mixed-case local renderings of a SELECT directive the F2 papers print without an
# ALL-CAPS form for anchor_extract.CAPS_RUN to catch. Harvested from the seven dumps:
# every other rendering is ALL CAPS (`PILIA ANG TANAN NGA MO APPLY`, `PUMILI NG LAHAT NA
# NAAANGKOP`, `PILION AN MGA KASIMBAGAN`) and local_directive() already sees those.
F2_LOCAL_IMPERATIVE = re.compile(
    r"\b(?:Pilion an|Basahon asin Pilion|Saro lang an pillion)\b", re.I)


def f2_labels(path):
    """spec/english-strings.json -> {EN text: {}} (same shape as dcf_labels())."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return {s["text"]: {} for s in d["strings"] if s.get("text")}


def f2_meta(path):
    """spec/english-strings.json -> {EN text: {"kinds": [...], "ids": [...]}}.

    The layout rules need to know WHAT a string is (an option row, a section title) and
    which item it belongs to. english-strings.json has carried both since Task 13 —
    `ids` on a choice.label entry is the PARENT item's id — so nothing in
    dump-english-strings.ts had to change; f2_labels() keeps its Task-14 shape because
    it is the anchor set, and this is the metadata beside it.
    """
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return {s["text"]: {"kinds": list(s.get("kinds") or []),
                        "ids": list(s.get("ids") or [])}
            for s in d["strings"] if s.get("text")}


def f2_option_groups(meta):
    """{parent item id: frozenset(normalised choice-label EN)} — the F2 value sets.

    The F2 stand-in for a CSPro value set: choice labels that share a parent item id.
    Both sibling rules read it — the qa_flags(siblings=) net and the box-less scale run.
    """
    by_item = defaultdict(set)
    for text, m in meta.items():
        if "choice.label" not in (m.get("kinds") or ()):
            continue
        ne = norm_for_match(text)
        if not ne:
            continue
        for i in m.get("ids") or ():
            by_item[i].add(ne)
    return {i: frozenset(nes) for i, nes in by_item.items()}


def f2_siblings(meta):
    """{normalised option EN: the normalised EN of the OTHER options of the same item}.

    Feeds qa_flags(siblings=), which is how a one-line option row that swept its
    neighbour's text is caught (the 2026-08-13 scar class).
    """
    sib = defaultdict(set)
    for nes in f2_option_groups(meta).values():
        for ne in nes:
            sib[ne] |= nes - {ne}
    return sib


def sibling_run_occurrences(rejected, groups, boxed=(), linked=None,
                            gap=F2_RUN_GAP, min_members=F2_RUN_MIN):
    """The box-less occurrences a SCALE RUN rescues, out of the ones the gates rejected.

    `rejected` is [(nstart, nend, ne), ...] in normalised-text coordinates: every
    occurrence of an option label that no ballot box preceded. Sorted per value set, a
    printed scale row is a tight chain — each member followed by its translation and then
    the next member — so members of one value set within `gap` normalised chars of each
    other form a chain, and a chain carrying `min_members` DISTINCT members is a row, not
    prose. Below that floor nothing is rescued: a `Yes o No` quoted inside a sentence is
    two members (the value set has only two), and three option words spread through a
    paragraph are past the gap.

    Two guards keep the rule off the BOXED grids, where the box gate already works and a
    reflowed row is the 2026-08-13 mis-anchoring scar:

      * `boxed` — the anchors that DID survive the gate somewhere on this paper. If any
        member of a value set is in it, the paper prints that set as a box row and the
        set is skipped entirely. The two Likert vocabularies are the case this rule is
        for precisely because they have no boxed occurrence anywhere.
      * `linked(prev_end, cur_start)` — false when the paper printed a ballot box between
        two members, which a scale row never does. `☐ LGU/Barangay LGU/Barangay ☐ Social
        Media Social Media` (F2_CEB.txt Q42) is three box-less sibling occurrences within
        the gap — the option grid's ECHO translations, not a run.

    Returns the set of occurrences to accept.
    """
    by_ne = defaultdict(list)
    for s, e, ne in rejected:
        by_ne[ne].append((s, e))
    boxed = frozenset(boxed)
    keep = set()

    def _take(chain):
        if len({ne for _s, _e, ne in chain}) >= min_members:
            keep.update(chain)

    for members in {frozenset(m) for m in groups.values()}:
        if members & boxed:
            continue
        occs = sorted((s, e, ne) for ne in members for (s, e) in by_ne.get(ne, ()))
        if len(occs) < min_members:
            continue
        chain = [occs[0]]
        for o in occs[1:]:
            if (o[0] - chain[-1][1] <= gap
                    and (linked is None or linked(chain[-1][1], o[0]))):
                chain.append(o)
                continue
            _take(chain)
            chain = [o]
        _take(chain)
    return keep


def _f2_empty_pair_span(text, idx, prev, cur):
    """True when prev's span — prev's end to cur's start — carries no translation.

    False for OVERLAPPING entries, as on the F1 side: a zero-length gap between two
    occurrences of the same words is not a row the paper printed nothing for. F2's
    _dedupe_overlaps() should make that unreachable; the guard costs one comparison and
    keeps the function honest if it ever stops being true.
    """
    if prev[1] > cur[0]:
        return False
    a = idx[prev[1] - 1] + 1 if prev[1] - 1 < len(idx) else len(text)
    b = idx[cur[0]] if cur[0] < len(idx) else len(text)
    return not clean_span(cut_at_box(text[a:b] if b > a else "")).strip()


def _f2_option_pair(prev, cur, sib):
    """True when two merged entries are DIFFERENT choices of the same item, and the first
    is not an ECHO (an echo's empty span means the paper repeated the English, which leaves
    no translation unclaimed and says nothing about the row that follows)."""
    return not prev[4] and prev[2] != cur[2] and prev[2] in sib.get(cur[2], ())


def f2_sibling_run(text, idx, merged, i, sib):
    """True when merged[i]'s span is a BLOCK shared with the choice row before it.

    The F2 half of Task 48, and the same rule as anchor_extract.sibling_run() — see its
    docstring for the mechanism and for why each guard is there. The Aug-21 F2 papers
    print some option grids as a PAIR of boxed ENGLISH rows followed by BOTH translations
    as one block:

        ☐ DOH standard referral form ☐ City / LGU standard referral form
        Syudad / LGU surundon nga porma han pagrefer DOH nga surundon nga porma han …

    That row — `City / LGU standard referral form` in war.json — is LIVE in production
    carrying the DOH row's translation glued to its own tail, while the DOH row extracted
    `empty`. The block prints the two translations in the REVERSE order of their English
    rows, so no half of it can be assigned.

    Only the `block-size` signature applies here: the F1/F3/F4 `block-echo` case (the span
    bounded by another occurrence of the same anchor) cannot arise in this extractor,
    because extract_text() already collapses an anchor's own echo into the entry before it
    and emits the verbatim English.
    """
    if i == 0:
        return False
    prev, cur = merged[i - 1], merged[i]
    if not _f2_option_pair(prev, cur, sib):
        return False
    if not (_box_prefixed(text, idx[prev[0]]) and _box_prefixed(text, idx[cur[0]])):
        return False
    if not _f2_empty_pair_span(text, idx, prev, cur):
        return False
    if i >= 2 and _f2_option_pair(merged[i - 2], prev, sib) \
            and _box_prefixed(text, idx[merged[i - 2][0]]) \
            and _f2_empty_pair_span(text, idx, merged[i - 2], prev):
        return False
    return True


def f2_duplicate_label_labels(clean, groups):
    """The English labels of `clean` that two choices of ONE item would label identically.

    The F2 half of the duplicate-label rule (Task 48). Two choices of the same item that
    render the same string are two choices the respondent cannot tell apart, whether the
    paper repeated the translation itself or the wrong occurrence won the count — so
    neither is written. F2 has no code aliases (a label IS the key), so a value that two
    choices share is always a defect.
    """
    by_ne = defaultdict(list)
    for en in clean:
        by_ne[norm_for_match(en)].append(en)
    out = set()
    for members in {frozenset(m) for m in groups.values()}:
        by_tr = defaultdict(list)
        for ne in members:
            for en in by_ne.get(ne, ()):
                if (clean.get(en) or "").strip():
                    by_tr[norm_for_match(clean[en])].append((ne, en))
        for group in by_tr.values():
            if len({ne for ne, _en in group}) > 1:
                out.update(en for _ne, en in group)
    return sorted(out)


def find_paper(source_dir, paper_name):
    """Aug-21 naming is instrument-first: F2-{Language}_*.pdf."""
    cands = sorted(Path(source_dir).glob(f"F2-{paper_name}_*.pdf"))
    return cands[0] if cands else None


def _group_by_norm(labels):
    """{normalised EN: [original EN, ...]} in label order."""
    by_norm = defaultdict(list)
    for en in labels:
        ne = norm_for_match(en)
        if ne:
            by_norm[ne].append(en)
    return by_norm


def _collisions_of(by_norm):
    return {ne: ens for ne, ens in by_norm.items() if len(ens) > 1}


def label_collisions(labels):
    """Distinct spec strings that normalise identically — a property of the anchor
    set alone, so it is computed ONCE per run, not once per locale."""
    return _collisions_of(_group_by_norm(labels))


def _kinds_by_norm(by_norm, meta):
    """{normalised EN: frozenset(kinds)} — the union over the colliding originals."""
    out = {}
    for ne, ens in by_norm.items():
        ks = set()
        for en in ens:
            ks.update((meta.get(en) or {}).get("kinds") or ())
        out[ne] = frozenset(ks)
    return out


def _is_option(kinds):
    """True when every spec kind this English text carries is `choice.label` — the F2
    equivalent of anchor_extract's "belongs to nothing but val: keys". A string that is
    also an item label (F2 reuses a few) is NOT gated."""
    return bool(kinds) and frozenset(kinds) <= OPTION_KINDS


def _is_title(kinds):
    return bool(kinds) and frozenset(kinds) <= TITLE_KINDS


def _box_prefixed(text, orig_start):
    return bool(_BOX_BEFORE.search(text[max(0, orig_start - 4):orig_start]))


def _section_prefixed(text, orig_start):
    """True when the occurrence sits right behind a section letter (`C. `, `E2. `)."""
    return bool(_SECT_BEFORE.search(text[max(0, orig_start - 8):orig_start]))


def has_f2_furniture(s):
    """True if `s` still carries one of the papers' English furniture phrases — the net
    under cut_at_f2_furniture(), as `directive-bleed` is the net under strip_directives()."""
    return bool(s) and any(rx.search(s) for rx in F2_FURNITURE)


def own_english_inside(en, tr):
    """True when the value carries the anchor's OWN English as a proper part of itself.

    The F2 papers reflow a two-column option grid into `☐ News ☐ Health center/facility
    Balita Health center/facility ☐ Legislation` — both labels first, both translations
    after. The span that opens on the SECOND label then holds the FIRST label's
    translation plus its own English, and nothing else in qa_flags() can see it: the
    value is not an echo, not a sibling's English, not a directive. It shipped `Balita`
    as ceb `Health center/facility`, which is the 2026-08-13 row-misalignment scar.
    """
    ne, nt = norm_for_match(en), norm_for_match(tr)
    return bool(ne) and nt != ne and f" {ne} " in f" {nt} "


def cut_at_f2_furniture(span):
    """Truncate a span at the first recognised English furniture phrase."""
    hits = [m.start() for m in (rx.search(span) for rx in F2_FURNITURE) if m]
    return span[:min(hits)] if hits else span


def cut_at_inner_note(span):
    """End a span at a note LABEL that is not the span's own opening.

    Hiligaynon prints only the LOCAL half of the DOLE note, so there is no English
    `According to DOLE …` anchor to bound Q11 and the whole note rides into the
    question's translation. A note label at the very start of the span is the note's own
    row and is stripped by _LEADING_NOTE instead — cutting there would throw the note's
    translation away in the six papers that DO print the English half.
    """
    for m in _ANY_NOTE.finditer(span):
        if norm_for_match(span[:m.start()]):
            return span[:m.start()]
    return span


# Task 27 moved this trim into anchor_extract.clean_span() — F1/F3/F4's Ilocano paper
# leaves the same orphan bracket. One copy, imported here so f2_clean_span() keeps
# working on a span clean_span() already trimmed (the trim is idempotent).
trim_unbalanced_parens = _ae.trim_unbalanced_parens


def trim_paper_rows(span):
    """Drop the paper's row furniture from the END of a span: the note label, a run of
    sub-question numbers, the next section's letter. Applied BEFORE clean_span() so the
    trailing dots the numbering needs are still there."""
    prev = None
    while prev != span:
        prev = span
        span = _TRAILING_QNUMS.sub(" ", span)
        span = _TRAILING_SECTION.sub(" ", span)
        span = _TRAILING_NOTE.sub(" ", span)
    return span


_RESTORABLE = ".:"


def restore_terminal_stop(tr, raw):
    """Put back the sentence-final `.` / `:` that clean_span() trims as layout residue.

    clean_span() ends with `.strip(" .:;,-")`, which is right on an option row — a
    trailing dot there is the row's furniture. On a full sentence it is the sentence's
    own full stop, and on a stem-and-list item (`I have worked overtime for:`) the colon
    is part of the string. Measured with this rule neutered and everything else in place:
    312 write rows, 160 of them a STRICT PREFIX of the value already in the live map
    (`… sa akong trabaho.` replaced by `… sa akong trabaho`); with it, 239 and 5. Nothing
    is invented — the character is put back only when the paper's own span ended in it,
    boxes ignored because the grid glyph is printed after the sentence on the Likert rows.
    """
    if not tr or tr[-1] in ".?!:":
        return tr
    tail = _ae.BOX.sub(" ", raw).rstrip()
    return tr + tail[-1] if tail[-1:] in _RESTORABLE else tr


def f2_clean_span(raw, is_option=False):
    """The F2 span pipeline: furniture cuts, then anchor_extract's clean_span()."""
    if is_option:
        raw = cut_at_box(raw)               # an option's span never crosses the next box
    raw = cut_at_f2_furniture(raw)
    raw = cut_at_inner_note(raw)
    raw = SKIP_NOTE.sub(" ", raw)           # so the row numbers behind a note are reachable
    raw = trim_paper_rows(raw)
    tr = trim_unbalanced_parens(clean_span(raw))
    tr = _LEADING_NOTE.sub("", tr).strip()
    if not norm_for_match(tr):
        return ""
    return restore_terminal_stop(tr, raw)


def f2_flags(en, tr, nlabels, siblings=()):
    """anchor_extract.qa_flags() plus the two F2-only nets."""
    flags = qa_flags(en, tr, nlabels, siblings)
    if tr and "english-furniture" not in flags and (has_f2_furniture(tr)
                                                    or own_english_inside(en, tr)):
        flags.append("english-furniture")
    if tr and "local-directive" not in flags and F2_LOCAL_IMPERATIVE.search(tr):
        flags.append("local-directive")
    return flags


def _dedupe_overlaps(occ):
    """Overlapping occurrences -> the longest anchor at each spot (`occ` must be sorted).

    `☐ Agree but for medical tasks only` is a boxed hit of BOTH that label and of the
    bare `Agree` option; only the longer one is real. Pulled out of extract_text() so the
    scale-run rule can ask the same question before it decides whether a value set is one
    the paper prints behind boxes.
    """
    kept = []
    for s, e, ne, pref in occ:
        if kept and s < kept[-1][1]:
            if (e - s) > (kept[-1][1] - kept[-1][0]):
                kept[-1] = (s, e, ne, pref)
            continue
        kept.append((s, e, ne, pref))
    return kept


def _finditer(ntext, needle):
    pat = re.compile(r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])")
    return list(pat.finditer(ntext))


def extract_text(text, labels, meta=None):
    """labels: {EN text: {}} (the anchor set). meta: {EN text: {kinds, ids}} from
    f2_meta(); without it NOTHING is gated and the Task-14 span rules stand."""
    meta = meta or {}
    ntext, idx = build_norm(text)
    by_norm = _group_by_norm(labels)              # norm form -> [original EN, ...]
    collisions = _collisions_of(by_norm)
    kinds = _kinds_by_norm(by_norm, meta)
    groups = f2_option_groups(meta)
    sib = f2_siblings(meta)
    occ = []                                      # (start, end, ne, is_prefix)
    seen = set()
    occurred = set()                              # anchors the paper prints, gate aside
    rejected_opt = []                             # box-less option hits, for the run rule
    for ne in by_norm:
        if len(ne) < F2_MIN_BOUND:
            continue
        short = len(ne) < SHORT_ANCHOR
        is_option = _is_option(kinds.get(ne))
        is_title = _is_title(kinds.get(ne))
        n_kept = n_rej = 0
        for m in _finditer(ntext, ne):
            occurred.add(ne)
            o = idx[m.start()]
            # an OPTION label is printed behind a ballot box; its other occurrences are
            # that phrase used inside a sentence, where bounding a span cuts a real
            # translation in half (the `Ako ay nasisiyahan sa` class). The one exception
            # is a box-less row of its own SIBLINGS — the Likert scale — which
            # sibling_run_occurrences() rescues below.
            if (short or is_option) and not _box_prefixed(text, o):
                if is_option and n_rej < MAX_OCC:
                    rejected_opt.append((m.start(), m.end(), ne))
                    n_rej += 1
                continue
            # a SECTION TITLE is printed behind its section letter (a box is allowed too,
            # for a paper that lists a section as an option row); everywhere else it is
            # the same words inside a question or its translation.
            if is_title and not (_section_prefixed(text, o) or _box_prefixed(text, o)):
                continue
            occ.append((m.start(), m.end(), ne, False))
            seen.add(ne)
            n_kept += 1
            if n_kept >= MAX_OCC:                 # runaway guard on the KEPT hits only
                break
    # fact 4, second half: a sibling label bounds an option's span exactly as a box does,
    # so a box-less scale row still pairs each label with its own translation.
    def _no_box_between(prev_end, cur_start):
        a = idx[prev_end - 1] + 1 if prev_end else 0
        b = idx[cur_start] if cur_start < len(idx) else len(text)
        return b <= a or not _ANY_BOX.search(text[a:b])

    occ.sort()
    boxed = {ne for _s, _e, ne, _p in _dedupe_overlaps(occ)}
    for s, e, ne in sorted(sibling_run_occurrences(rejected_opt, groups, boxed=boxed,
                                                   linked=_no_box_between)):
        occ.append((s, e, ne, False))
        seen.add(ne)
    # a label the paper printed in a LONGER form than the spec string: fall back to its
    # 12-word prefix, ONCE, so a repeated stem cannot open a second bogus span.
    for ne in by_norm:
        if ne in seen:
            continue
        pref = anchor_prefix(by_norm[ne][0])
        if not pref or len(pref) < SHORT_ANCHOR or pref in by_norm:
            continue
        hits = _finditer(ntext, pref)
        if len(hits) != 1:
            continue
        occ.append((hits[0].start(), hits[0].end(), ne, True))
        seen.add(ne)
    occ.sort()
    kept = _dedupe_overlaps(occ)                # de-overlap: keep the longest anchor
    merged = []                                 # collapse echoes: (s, e, ne, pref, echo)
    for s, e, ne, pref in kept:
        if merged and merged[-1][2] == ne and not ntext[merged[-1][1]:s].strip():
            ps, _pe, _ne, ppref, _ = merged[-1]
            merged[-1] = (ps, e, ne, ppref, True)
            continue
        merged.append((s, e, ne, pref, False))
    cands = defaultdict(list)                   # ne -> [(tr, extra flags), ...]
    for i, (s, e, ne, is_prefix, echo) in enumerate(merged):
        if len(ne) < F2_MIN_EMIT:
            continue                            # bounds spans but does not emit
        if echo:
            cands[ne].append((by_norm[ne][0], ()))   # verbatim EN -> qa_flags: echo-english
            continue
        nxt = merged[i + 1][0] if i + 1 < len(merged) else len(ntext)
        start = idx[e - 1] + 1
        end = idx[nxt] if nxt < len(idx) else len(text)
        raw, en0 = text[start:end], by_norm[ne][0]
        extra = ()
        if is_prefix:
            raw = condensed_candidate(raw, en0)
            extra = ("label-condensed",)
        span = f2_clean_span(raw, _is_option(kinds.get(ne)))
        # Task 48: this span is the shared block of an adjacent-English PAIR — whatever it
        # holds belongs to the row before this one as much as to this one. `block-size` is
        # measured on the cleaned span, so the test comes after f2_clean_span().
        if len(ne) >= F2_PAIR_BLOCK_MIN_EN \
                and len(norm_for_match(span)) > F2_PAIR_BLOCK_RATIO * len(ne) \
                and f2_sibling_run(text, idx, merged, i, sib):
            extra = tuple(extra) + ("sibling-run",)
        cands[ne].append((span, extra))
    nset = set(by_norm)
    clean, flagged = {}, []
    for ne, spans in cands.items():
        en0 = by_norm[ne][0]
        scored = []
        for tr, extra in spans:
            # a layout flag already states WHY there is nothing to import; `empty`
            # ("nothing between this anchor and the next") would contradict it.
            fl = list(extra) if (extra and not tr) else \
                list(extra) + [f for f in f2_flags(en0, tr, nset, sib.get(ne, ()))
                               if f not in extra]
            scored.append((tr, fl))
        ok = [tr for tr, fl in scored if not fl]
        for en in by_norm[ne]:                  # emit under every colliding original
            if ok:
                clean[en] = Counter(ok).most_common(1)[0][0]
            else:
                tr, fl = scored[0]
                flagged.append({"en": en, "tr": tr, "flags": fl})
    # Task 48: two choices of one item may not carry the same label. Judged on the
    # FINISHED clean set — the two candidates come from different anchors, and neither
    # loop above can see the other's answer.
    for en in f2_duplicate_label_labels(clean, groups):
        flagged.append({"en": en, "tr": clean.pop(en), "flags": ["duplicate-label"]})
    # anchors with no surviving occurrence: a worklist row, not a silent drop (Task 45).
    # TWO reasons, and they are not the same fact about the paper — `not-in-paper` says
    # the words are nowhere on the page, `gate-rejected` says they ARE on the page but
    # every occurrence failed the box / section-letter gate (the phrase only ever appears
    # inside running text). Reporting the second as the first told Task 45 something
    # false about 77 of 247 rows.
    for ne in sorted(by_norm):
        if ne in cands or len(ne) < F2_MIN_EMIT:
            continue
        why = "gate-rejected" if ne in occurred else "not-in-paper"
        for en in by_norm[ne]:
            flagged.append({"en": en, "tr": "", "flags": [why]})
    return {"anchored": len(merged), "clean": clean, "flagged": flagged,
            "collisions": collisions}


def extract_pdf(pdf_path, labels, meta=None):
    r = extract_text(pdf_text(str(pdf_path)), labels, meta)
    r["file"] = Path(pdf_path).name
    return r


def _write(path, text):
    """LF endings everywhere — the PWA store and the apply script are LF-only."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


LAYOUT_FLAGS = ("directive-only", "directive-bleed", "grid-bleed", "routing-note",
                "label-condensed", "not-in-paper", "gate-rejected", "local-directive",
                "english-furniture", "sibling-run", "duplicate-label")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--english-strings", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    labels = f2_labels(a.english_strings)
    meta = f2_meta(a.english_strings)
    collisions = label_collisions(labels)       # once per run, from the anchor set
    rows, per_loc = [], {}
    for loc in LOCALES:
        pdf = find_paper(a.source, LOC_TO_PAPER[loc])
        if pdf is None:
            rows.append((loc, "NO PDF", 0, 0, 0, 0))
            continue
        r = extract_pdf(pdf, labels, meta)
        echoes = sum(1 for f in r["flagged"] if "echo-english" in f["flags"])
        _write(out / f"{loc}.json",
               json.dumps(r["clean"], ensure_ascii=False, indent=1) + "\n")
        _write(out / f"{loc}_flagged.json",
               json.dumps(r["flagged"], ensure_ascii=False, indent=1) + "\n")
        rows.append((loc, r["file"], r["anchored"], len(r["clean"]), len(r["flagged"]), echoes))
        cnt = Counter()
        for f in r["flagged"]:
            for fl in f["flags"]:
                cnt[fl] += 1
        per_loc[loc] = cnt
    lines = ["# F2 Aug-21 paper extract — QA report", "",
             f"anchors (unique English strings): {len(labels)}",
             f"span helpers from: {_AE_PATH}",
             f"thresholds: F2_MIN_BOUND={F2_MIN_BOUND} F2_MIN_EMIT={F2_MIN_EMIT} "
             f"SHORT_ANCHOR={SHORT_ANCHOR} (box-prefix rule)", "",
             "| locale | file | anchored | clean | flagged | of which echo-english |",
             "|---|---|---|---|---|---|"]
    lines += [f"| {l} | {f} | {an} | {c} | {fl} | {ec} |" for l, f, an, c, fl, ec in rows]
    if per_loc:
        lines += ["", "## Aug-21 layout flags per locale (Task 21b)", "",
                  "| locale | " + " | ".join(f"`{c}`" for c in LAYOUT_FLAGS) + " |",
                  "|---" * (len(LAYOUT_FLAGS) + 1) + "|"]
        for loc, cnt in per_loc.items():
            lines.append(f"| {loc} | "
                         + " | ".join(str(cnt.get(c, 0)) for c in LAYOUT_FLAGS) + " |")
    lines += ["", f"## Normalized-key collisions ({len(collisions)})", ""]
    lines += [f"- `{ne}` <- {ens}" for ne, ens in sorted(collisions.items())] or ["- none"]
    _write(out / "QA-REPORT.md", "\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
