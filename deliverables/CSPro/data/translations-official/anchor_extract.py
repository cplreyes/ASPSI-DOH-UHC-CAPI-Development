#!/usr/bin/env python3
"""anchor_extract.py — anchor-based extraction of translations from a bilingual paper PDF,
emitting NAME-SCOPED keys (item:/vs:/val:) that apply_translations() accepts directly.

Provenance: the text-prep, span and QA-flag code below is COPIED VERBATIM (2026-08-25)
from the June-5 tool at `deliverables/CSPro/translations-paper-extract/anchor_extract.py`
(:48-249, 299-308), which is gitignored — a committed tool must not import it, so it is
copied rather than imported. The June-5 flags are calibrated against 28 papers and are
untouched here; the two Aug-21 flags are APPENDED at the end of qa_flags(). That June-5
script is superseded for imports; it stays on disk only as the historical run record.

Task 16b (2026-08-25) then added the Aug-21 paper's LAYOUT rules — see "Aug-21 layout"
below and step 4a of the method. They are boundary and span-cleaning rules only: where
none of them fires the answer is what the June-5 tool always gave.

Task 16c (2026-08-26) closed the 9.3% of the write set Task 17 measured as still
defective: a ONE-WORD `val:` option label bounds a span only behind a ballot box (149
truncations), two more directive variants and the papers' English NOTES leave the span
(92 rows), and the local-language repeat of a directive is flagged `local-directive`.

Task 27 (2026-08-26) added the own-match half of that box gate (`own_match_is_english`,
flag `english-own-match`), the counting bracket/quote trims in clean_span(), and — in
fix round 1 — `strip_legend_code()`: the household-roster pages print their option lists
as an UNBOXED legend (`01-Head 02-Spouse/Partner 03-…`), so cut_at_box() has nothing to
cut at and every span kept the next option's code (`Agum 03`, 166 F4 clean rows).

Task 32b (2026-08-26) added `strip_question_number()`: the Waray papers number the LOCAL
row as well as the English one, so 154 F4 WAR values shipped in v3.2.0 opening `26. Mayda
ba …`. The number is the paper's furniture and is dropped; when it CONTRADICTS the key's
own question number the row is additionally flagged `paper-number-mismatch` and held.

Task 33b (2026-08-26) added `strip_wrapping_brackets()`: the Tagalog papers are
BILINGUAL, printing the English line and the Filipino gloss inside square brackets after
it (`Male [Lalaki]`), so 459 F4 FIL values shipped in v3.2.1 wearing the delimiter — about
half of everything an enumerator reads aloud. clean_span() drops ONE whole-value pair;
internal brackets, double wraps and orphans stay visible. F3's Tagalog paper prints 503
such lines, so the rule is Wave 4's prerequisite as much as this patch's. extract()
looks for the pair a second time after strip_legend_code()/strip_question_number(),
because those two remove furniture printed OUTSIDE the gloss and can uncover a wrap
clean_span never saw — but only when one of them fired, so at most one pair goes.

Task 40 (2026-08-26) taught it the five paper conventions Task 28 could only HOLD on F4,
plus four more the F3 papers print, all of them span-boundary or span-cleaning rules:
the GAMOT applicability note, the Q17 definition block and Q18's `Approximate amount:`
caption end a span (NOTE_PATTERNS); so do `If yes, indicate the amount spent` and
`If patient provides a receipt` on F3; `cut_at_local_directive()` ends a span at the
papers' SENTENCE-CASE local repeat of `Select all that apply` (LOCAL_SELECT_ALL — the
ALL-CAPS rule in skip_translated_directive() never saw one) and of the cost grids'
`Amount in Pesos` column header (LOCAL_AMOUNT, 198 F3 rows, guarded by the anchor's own
English so an `*_AMT` label keeps it); `Check all that apply` joins DIRECTIVE_PATTERNS;
trim_unbalanced_quotes() gains the curly pair's odd-count test; and nothing INSIDE a
fill placeholder (`[facility_name_input]`) may anchor, which is what had been cutting
every Q66/Q88 translation down to `Ang [`.

Method:
  1. Anchors = every (key, EN text) pair from cspro_helpers.walk_labeled_nodes() on the
     BUILD's English — either the written .dcf (--dcf) or, for F3 where the written file is
     post-neutralise, the generator's pre-apply dictionary (--generator F3).
  2. Normalise the PDF text with a char-offset map back to the original.
  3. Find every word-bounded occurrence of every anchor text in the normalised text.
  4. Sort by position; each anchor's candidate translation = original-text span from the
     anchor's end to the next anchor's start.
  4a. Aug-21 layout (Task 16b): a sub-MIN_BOUND option label behind a ballot box anchors
     too, no span crosses a box, interviewer directives (and their local-language repeat)
     and <...> routing notes are excised, a label the CSPro 255-char cap condensed
     anchors on its 12-word prefix, and an anchor the paper never printed is emitted as
     a `not-in-paper` worklist row instead of vanishing.
  5. clean_span + qa_flags; only unflagged pairs land in <loc>.json.

    python anchor_extract.py --source "raw/Survey-Instruments-2026-08-21/Translations" \
        --instrument F1 --dcf deliverables/CSPro/F1/FacilityHeadSurvey.dcf \
        --out deliverables/CSPro/data/translations-official/out-aug21/F1 \
        [--locales FIL,BCL] [--live-maps deliverables/CSPro/F1/translations]
    python anchor_extract.py --source ... --instrument F3 --generator F3 --out .../out-aug21/F3

--live-maps prints, per locale, how many CLEAN pairs differ from the live map's current
value (the number apply_aug21.py's replace-by-default would overwrite) and lists
"keys not in dcf" (always [] by construction — printed so the gate is explicit).
Writes <out>/<loc>.json, <out>/<loc>_flagged.json, <out>/QA-REPORT.md. NOTHING is written
into the build or the live maps — apply_aug21.py is the only writer.
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, CSPRO)
sys.path.insert(0, HERE)
from cspro_helpers import walk_labeled_nodes  # noqa: E402
from extract_notes import looks_english  # noqa: E402
from textnorm import norm_for_match  # noqa: E402

# (paper-filename language word, locale code) — Aug-21 files are F<n>-<Language>_..._Aug21.pdf
LANGS = [("Tagalog", "FIL"), ("Bicolano", "BCL"), ("Bisaya", "BIS"), ("Cebuano", "CEB"),
         ("Waray", "WAR"), ("Hiligaynon", "HIL"), ("Ilocano", "ILO")]

# Only these key kinds may anchor: dict:/level:/record: labels are page furniture
# ("UHC Year 2 Facility Head Survey", "Section A") that matches headers and footers,
# opening spurious spans that swallow the first real question of a page.
ANCHOR_KINDS = ("item", "vs", "val")

BOX = re.compile(r"[☐☑☒□■❑]")
NOISE = re.compile(r"ICF ver\.|Translated Questionnaire ver\.|^\s*\d+\s*$")
# Task 16b: the June-5 cap of 60 chars is too short for the Aug-21 routing notes
# ("<Question for facilities that are only YAKAP-accredited, otherwise proceed to Q88>").
SKIP_NOTE = re.compile(r"<[^<>]{0,200}>")
# a routing note the span cut in half: `... idadagdag mo? <Only relevant to facilities who`
# — the `>` is past the next anchor, so the note has no closing bracket to match on.
# Task 16c: only a fragment that opens with a WORD is a note. `<18 years` is an option
# label; stripping it produced a wrong value silently, and it now falls through to the
# `routing-note` flag instead.
TRAILING_NOTE = re.compile(r"<\s*[A-Za-z][^<>]*$")
ARROW_NOTE = re.compile(r"(?:→|->)\s*Q?\s*\d+(?:\.\d+)?")
# F3/F4 HH:MM items carry "— Hours" / "— Minutes" in the dcf label only (the paper prints the
# bare stem + "Time (HH:MM)"); mirror of generate_qsf._strip_component_suffix.
COMPONENT_SUFFIX_RE = re.compile(r"\s+—\s+(Hours|Minutes)\s*$")

MIN_EMIT = 8      # normalised length to emit a translation for
MIN_BOUND = 6     # normalised length to serve as a span boundary
MAX_SPAN = 420    # candidate longer than this = boundary failure
MAX_OCC = 400     # runaway guard on one anchor's occurrences (was 64 — a box-anchored
                  # "Yes"/"No" occurs ~60x per paper and must bound EVERY row it opens)
PREFIX_WORDS = 12  # normalised words of a condensed label used as a fallback anchor
SHORT_OPTION_WORDS = 2  # words up to which a `val:` label is own-match gated (Task 27)
PAIR_BLOCK_RATIO = 2.0  # normalised length beyond which the shared span of an
                        # empty-predecessor option PAIR is holding TWO translations (Task 48)
PAIR_BLOCK_MIN_EN = 20  # ... but only for an English label long enough that a
                        # doubling cannot just be a verbose rendering of one short
                        # word (`Brother` -> `Igsoon nga lalaki` is 2.4x and correct)

# ------------------------------------------------------------------ Aug-21 layout --
# Interviewer DIRECTIVES. The Aug-21 papers print these BETWEEN the English question and
# its translation, so they are not anchors and used to land inside the span: Task 17
# measured 857 F1 / 429 F3 / 42 F4 clean values carrying one. Harvested by grepping the 21
# text-aug21/*.txt dumps for recurring ALL-CAPS runs and for the mixed-case enumerator
# notes; every pattern below is present in those dumps. Case-insensitive, word-bounded.
# The instruction text itself already has a home: extract_notes.py's
# note:const:_READ_ONE/_READ_ALL/_SELECT_ONE/_DNR_ALL/_DNR_UNPROMPTED keys.
DIRECTIVE_PATTERNS = (
    r"\bDO NOT READ(?: THE)?(?: OPTIONS)?(?: OUT LOUD| ALOUD)?\b",
    r"\bREAD (?:ALL )?(?:THE )?OPTIONS(?: OUT LOUD| ALOUD)?\b",
    r"\bREAD OUT LOUD\b",
    r"\bDO NOT ASK\b",
    r"\bSELECT ONE ANSWER ONLY\b",
    r"\bSELECT ALL THAT APPLY\b",
    # Task 40: the F3 papers' spelling of the same instruction (Q70/Q71/Q93).
    r"\bCHECK ALL THAT APPLY\b",
    r"\bSELECT ALL THE ANSWER OPTIONS[^.?!]{0,60}",
    r"\bIF MORE THAN ONE, ASK FOR THE MAIN SOURCE\b",
    r"\bIF NO RECEIPT WAS PROVIDED\b",
    r"\bPROCEED TO Q?\s?\d+(?:\.\d+)?",
    r"\bSKIP TO Q?\s?\d+(?:\.\d+)?",
    r"\bSKIP THIS QUESTION WHEN[^.?!]{0,60}",
    r"\bSKIP IF ANSWERED[^.?!]{0,60}",
    # the bracketed/parenthesised aside is part of the marker, so it is bounded by its own
    # closing bracket — an open-ended [^:]{0,30} tail ate 30 chars of the FOLLOWING sentence.
    r"\bNOTE TO ENUMERATOR\b(?: ?\[[^\]]{0,40}\])? ?:",
    r"\bENUMERATOR (?:NOTE|INSTRUCTIONS?)\b(?: ?[\[(][^\])]{0,40}[\])])? ?:?",
    r"\bINTERVIEWER (?:NOTE|INSTRUCTIONS?)\b(?: ?[\[(][^\])]{0,40}[\])])? ?:?",
    r"\bFOR (?:THE )?ENUMERATOR\b(?: ?\[[^\]]{0,40}\])? ?:",
    r"\bENUMERATOR ?:",
    r"\bPROBE ?:",
    r"\bIF YES,? (?:INDICATE|SPECIFY)\b",
    r"\bAMOUNT IN PESOS\b",
    r"\bPLEASE LIST DOWN ALL MEDICINES[^.?!]{0,60}",
    # Task 16c: the two the Aug-21 F1 papers print on the day-count grids
    # (`...? No. of days: Enumerator note: Tick the category ...`) - 38 F1 rows.
    # Task 40: the F4 household pages print `Tick the INCOME category that
    # corresponds ...`, which Task 16c's pattern did not know - one word wide.
    r"\bTICK THE (?:\w+ )?CATEGORY THAT CORRESPONDS[^.?!]{0,60}",
    r"\bNo\.? of [Dd]ays\s*:?",
)
DIRECTIVES = [re.compile(p, re.I) for p in DIRECTIVE_PATTERNS]

# English NOTES (Task 16c). Not directives: the paper prints the note's LOCAL translation
# right after the English one, so excising the English half would glue the local half onto
# the question label (which is how the June-5 bcl map came to hold it). The note is
# `note:`-layer content that extract_notes.py owns, and on every one of the seven papers it
# is printed AFTER the question's translation and BEFORE the option rows - so it ENDS the
# question's span, exactly as a ballot box does.
NOTE_PATTERNS = (
    r"\bThese are the requirements for YAKAP/Konsulta\b",
    r"\bOur focus is specifically on referrals\b",
    # Task 40: the three blocks Task 28 could only HOLD on F4, each of them
    # printed between a question's translation and its option rows and each of
    # them followed by its own LOCAL half - so cutting drops both halves, where
    # excising would glue the local half onto the label. 62 held F4 rows.
    #   * the GAMOT applicability note (Q70-Q73) - note-layer content that
    #     extract_notes.py already owns as note:const:_GAMOT_FAC;
    #   * the definition block under Q17 ("This is the person who ...");
    #   * `Approximate amount:` - Q18's answer-box caption; everything the paper
    #     prints after it belongs to the enumerator, not to the respondent.
    r"\bApplicable only to respondents\b",
    r"\bThis is the person who makes decisions on health\b",
    r"\bApproximate amount\s*:",
    # The same class on the F3 papers, all seven of them, verbatim. Both blocks are
    # built out of DIRECTIVE fragments the list already knows (`IF YES, INDICATE`,
    # `SELECT ALL THAT APPLY`, `READ OPTIONS OUT LOUD`), but excising the fragments
    # leaves the rest of the sentence and the local repeat behind it inside the value
    # (` the amount spent Kung oo, ilagay ang halagang ginastos`, `If patient
    # provides `). The whole block is a note, so it ends the span instead.
    r"\bIf yes,? indicate the amount spent\b",
    r"\bIf patient provides a receipt\b",
)
NOTES = [re.compile(p, re.I) for p in NOTE_PATTERNS]

# English furniture that is NOT a span boundary, because the papers do not agree on where
# they print it: Q44's capitation gloss comes BEFORE the translation in fil/bcl/war/hil/ilo
# and AFTER it in ceb, so cutting at it would throw five real translations away. It is
# flagged `english-furniture` instead - never clean, and the worklist row still carries the
# text for the translator to salvage.
FURNITURE_PATTERNS = (
    r"\bCapitation is the amount per year\b",
)
FURNITURE = [re.compile(p, re.I) for p in NOTE_PATTERNS + FURNITURE_PATTERNS]

# The paper's LOCAL-LANGUAGE rendering of a directive (Task 16c). Where the paper prints
# only the local version, skip_translated_directive() has no English directive to hang off
# and the repeat rides into the value: 26 F1 rows across bcl/ceb/hil/ilo. Detected
# structurally (a >= 3-word ALL-CAPS run) plus the short list of mixed-case imperative
# openers the papers actually use - measured over the seven F1 and seven F2 clean maps
# (9,113 values): 40 hits, all of them real directives, no false positive.
CAPS_RUN = re.compile(r"(?:(?<=\s)|^)(?:[A-ZÑÁÉÍÓÚ][A-ZÑÁÉÍÓÚ'’/-]{1,}\s+){2,}"
                      r"[A-ZÑÁÉÍÓÚ][A-ZÑÁÉÍÓÚ'’/-]{1,}")
LOCAL_IMPERATIVE = re.compile(
    r"\b(?:Dae pagbasahon|Ayaw basaha|Ayaw i-?basa|Huwag basahin|Indi basahon|"
    r"Diri basahon|Saan a basaen|Pilion an mga dapat|Piliin ang|Basahon an|Basahin ang)\b",
    re.I)

# The papers' LOCAL rendering of `Select all that apply` (Task 40). It is the
# fourth class Task 28 could only hold: every one of the seven Aug-21 papers
# prints the repeat, all of them in SENTENCE case, so skip_translated_directive()
# — which keys on an unbroken ALL-CAPS run — never saw one, and the English
# original sits in FRONT of the translation while the repeat sits behind it, so
# there is nothing for it to hang off either. Harvested from the 14 F3/F4 dumps
# (2 repeats per F4 paper, 6 per F3 paper); the shape is invariant across the
# seven languages — a `Pili…`/`Pumili` imperative followed by the article:
#   Piliin ang lahat ng naaangkop.   Pilion an dapat.        Pili-a ang tanan nga pwede
#   Pilia ang tanan nga mo apply.    Pilia an ngatanan …     Pilien amin nga agaplikar.
#   Pilia tanang pwede.              Pilia-ang tanan …       Pumili sang tanan nga nagaangay.
# The article is what keeps it off the languages' own words: `Pilipinas` and
# `pilian` ("the options") both open `Pili` and neither is ever followed by one.
LOCAL_SELECT_ALL = re.compile(
    r"\b(?:Pili(?:in|on|en|-?a)|Pumili)\s*-?\s*(?:ang|an|amin|sang|tanang|tanan)\b",
    re.I)

# The same fact about the COST GRIDS (F3 Q92/Q94/Q96/Q97.1/Q97.2/Q107/Q109/Q112): every
# row reads `☐ <option> <translation> Amount in Pesos <Kantidad sa Peso>`. `AMOUNT IN
# PESOS` is already a directive so the English half goes, but five of the seven papers
# print a SENTENCE-CASE local repeat behind it (BCL/CEB `Kantidad sa Peso`, BIS
# `Kantidad sa pesos`, WAR `Kantidad ha Pisos`, ILO `(Kantidad iti Pesos)`; FIL and HIL
# leave the header in English only) - 198 rows of the F3 write set carried one.
LOCAL_AMOUNT = re.compile(r"\bKantidad\s+(?:sa|ha|iti)\s+P[ei]sos?\b", re.I)
# ... and the one place that header is CONTENT: an `*_AMT` item's own English label ends
# `(Amount in Pesos)`, so its translation is supposed to say it.
AMOUNT_EN = re.compile(r"\bAmount in Pesos?\b", re.I)


# ---------------------------------------------------------------- text prep --
# verbatim from translations-paper-extract/anchor_extract.py (June-5 tool)
def pdf_text(path):
    d = fitz.open(str(path))
    t = "\n".join(d[i].get_text() for i in range(len(d)))
    d.close()
    lines = [ln for ln in t.split("\n") if not NOISE.search(ln)]
    return " ".join(" ".join(lines).split())


def build_norm(text):
    """Lower-cased alnum+space projection of `text`, plus map norm-idx -> orig-idx.

    The projection MUST stay identical to textnorm.norm_for_match() (which is this
    same fold applied to a label, without the offset map) — a difference of one
    character class means an anchor can never be found in the text it came from.
    test_anchor_extract.py asserts the two agree.
    """
    norm_chars, idx = [], []
    prev_space = True
    for i, c in enumerate(text):
        cl = c.lower()
        if cl == "’" or cl == "‘":
            cl = "'"
        if cl.isalnum():
            norm_chars.append(cl); idx.append(i); prev_space = False
        else:
            if not prev_space:
                norm_chars.append(" "); idx.append(i); prev_space = True
    return "".join(norm_chars), idx


# ------------------------------------------------------------------- anchors --
def _anchors_from_dict(d):
    out = {}
    for key, node in walk_labeled_nodes(d):
        if key.split(":", 1)[0] not in ANCHOR_KINDS:
            continue
        labs = node.get("labels") or []
        if not labs:
            continue
        first = labs[0]
        if first.get("language") not in (None, "EN"):
            continue
        en = COMPONENT_SUFFIX_RE.sub("", (first.get("text") or "").strip())
        if en:
            out[key] = en
    return out


def dcf_anchors(dcf_path):
    """{name-scoped key: EN label text} for every labels-bearing node of a WRITTEN dcf.

    Uses the shared walker so keys are byte-identical to what apply_translations()
    looks up (cspro_helpers.walk_labeled_nodes). labels[0] is the English label
    (language None/EN). Right for F1/F4. NOT right for F3: PatientSurvey.dcf is
    written after _neutralise_facility_placeholder, so use generator_anchors("F3").
    """
    return _anchors_from_dict(json.load(io.open(dcf_path, encoding="utf-8")))


def generator_anchors(instrument):
    """Anchors from the generator's PRE-APPLY dictionary (placeholders intact — the text
    the qsf renders). Side effect: capture_source_dict re-runs the generator, which
    rewrites <inst>/<App>.dcf from the current translations (a no-op on a clean tree)."""
    from migrate_maps_namekeys import capture_source_dict
    return _anchors_from_dict(capture_source_dict(instrument, "generate_dcf.py"))


# ---------------------------------------------------------------- extraction --
# verbatim from translations-paper-extract/anchor_extract.py, plus two flags at the end
def has_directive(s):
    """True if `s` still carries an English interviewer directive (Task 16b)."""
    return bool(s) and any(rx.search(s) for rx in DIRECTIVES)


def has_furniture(s):
    """True if `s` still carries one of the papers' English NOTES or glosses (Task 16c)."""
    return bool(s) and any(rx.search(s) for rx in FURNITURE)


def local_directive(en, tr):
    """True if `tr` carries the LOCAL-LANGUAGE rendering of an interviewer directive.

    The ALL-CAPS test is guarded by the anchor's own English: a real acronym run
    ("Have you heard of BUCAS GAMOT NBB?") is three capitalised words too, but it is also
    in the English label, and a directive never is. EVERY caps run is tested, not just the
    first: a value can open with the question's own acronym run and still carry a real
    directive later ("... sa BUCAS GAMOT NBB? PILIA ANG TANAN NGA APLIKADO").
    """
    if not tr:
        return False
    if any(m.group(0) not in en for m in CAPS_RUN.finditer(tr)):
        return True
    # Task 40: the net under cut_at_local_directive(), exactly as `directive-bleed`
    # is the net under strip_directives() — a rendering the cut did not reach
    # (one the paper printed in FRONT of the translation, or inside a span the
    # box rules had already ended) must never be clean.
    if LOCAL_IMPERATIVE.search(tr) or LOCAL_SELECT_ALL.search(tr):
        return True
    return bool(LOCAL_AMOUNT.search(tr)) and not AMOUNT_EN.search(en or "")


_TOKEN = re.compile(r"\S+")
_EDGE = "()[]{}.,:;/-–—“”\"'!?"


def _shouty(tok):
    """True = an ALL-CAPS word, False = an ordinary word, None = punctuation/digits only."""
    core = tok.strip(_EDGE)
    if not core or not any(c.isalpha() for c in core):
        return None
    if not any(c.islower() for c in core):
        return True
    # PyMuPDF reflow glitch seen in the Ilocano papers: "AGaplikar" for "AG aplikar"
    return bool(re.match(r"[^\Wa-z_]{2,}[a-z]", core))


def skip_translated_directive(s, k):
    """Index past the LOCAL-LANGUAGE rendering of the directive that starts at `s[k:]`.

    Every paper prints the instruction twice: `READ OPTIONS OUT LOUD. SELECT ALL THAT
    APPLY. AYAW BASAHA ANG MGA PILIAN OG KUSOG.` (Cebuano, bare) or `... SELECT ALL THAT
    APPLY. (BASAEN TI OPTIONS ITI NAIPAAY. PILIEN AMIN NGA AGaplikar.)` (Ilocano,
    parenthesised). Both renderings are ALL CAPS while a question's translation is
    sentence case, so an unbroken run of >= 3 capitalised words right after an English
    directive is the translated directive — and nothing else in these papers is.
    """
    alpha, last_alpha_end = 0, k
    for m in _TOKEN.finditer(s, k):
        sh = _shouty(m.group(0))
        if sh is False:
            break
        if sh is True:
            alpha += 1
            last_alpha_end = m.end()
    return last_alpha_end if alpha >= 3 else k


def _next_directive(s, i):
    best = None
    for rx in DIRECTIVES:
        m = rx.search(s, i)
        if m and (best is None or m.start() < best.start()
                  or (m.start() == best.start() and m.end() > best.end())):
            best = m
    return best


def strip_directives(s):
    """Excise every interviewer directive (and the translated directive that follows it)
    from a span, keeping the text on BOTH sides.

    The brief's rule was "the candidate is the text AFTER the last directive match", which
    is right for the Tagalog/Cebuano layout (`English? DIRECTIVE. Ano ang ...?`) but wrong
    for the Ilocano one, where the translation comes FIRST and the directive last:

        52. Which of the following requirements were difficult ...? (Ania kadagiti
        sumaganad a kasapulan ...?) READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY.
        (BASAEN TI OPTIONS ITI NAIPAAY. PILIEN AMIN NGA AGaplikar.)

    Worse, EVERY paper repeats the instruction in the local language, in ALL CAPS, so
    "after the last match" lands on that repeat rather than on the translation: re-running
    the whole F1 extract with the brief's rule puts it in at least 332 of the seven
    locales' clean values (FIL 70, BCL 52, BIS 66, CEB 64, WAR 66, HIL 6, ILO 8 — a lower
    bound, counting only values that end up fully uppercase). A new defect in place of the
    old one. Excising instead of cutting handles both layouts, because the directive is
    furniture wherever it sits; skip_translated_directive() removes the repeat.
    """
    out, i = [], 0
    while i < len(s):
        m = _next_directive(s, i)
        if m is None:
            out.append(s[i:])
            break
        out.append(s[i:m.start()])
        i = skip_translated_directive(s, m.end())
    return " ".join(out)


def cut_at_box(span):
    """Truncate a span at the first ballot box: the translation of a question stem is
    printed BEFORE its option row, and an option's translation before the next box. No
    span may cross a box glyph (Task 16b — the `Yes Oo No Hindi` grid-bleed class)."""
    m = BOX.search(span)
    return span[:m.start()] if m else span


def cut_at_note(span):
    """Truncate a span at the first recognised English NOTE (Task 16c).

    All seven Aug-21 papers print `<question> <translation> <English note> <local note>
    <directives> <option rows>`, so the note is the end of the question's translation.
    Excising it instead would keep the local half and glue it onto the label."""
    hits = [m.start() for m in (rx.search(span) for rx in NOTES) if m]
    return span[:min(hits)] if hits else span


def cut_at_local_directive(span, en=""):
    """Truncate a span at the papers' LOCAL repeat of an interviewer directive (Task 40).

    Same argument as cut_at_box() and cut_at_note(): the repeat is printed after
    the thing it belongs to and before the next row, on every paper that prints
    one, so it ends the span. Cutting rather than excising is what recovers the
    option rows too — the repeat is glued to the LAST thing the paper printed
    before the box, which on F4 Q66/Q74 is the question stem and on the F3 cost
    grids is an option label.

    Two families, and only the second needs the anchor's own English: `Select all
    that apply` is an instruction and is never the answer text, but `Amount in
    Pesos` IS the label of every `*_AMT` item, so a value that is supposed to say
    it is left alone.
    """
    families = [LOCAL_SELECT_ALL]
    if not AMOUNT_EN.search(en or ""):
        families.append(LOCAL_AMOUNT)
    hits = [m.start() for m in (rx.search(span or "") for rx in families) if m]
    return span[:min(hits)] if hits else span


def behind_box(text, idx, nstart):
    """True if the occurrence starting at normalised index `nstart` is preceded (ignoring
    spaces) by a ballot box in the ORIGINAL text.

    This is the gate that lets a sub-MIN_BOUND option label ("Yes"/"No") anchor at all.
    It has to be the layout, not the word: Ilocano `no` means "if" — the F1 ILO paper has
    154 word-bounded `no`, only 67 of them behind a box. Anchoring the bare word would
    chop 87 real translations mid-sentence.
    """
    if nstart >= len(idx):
        return False
    i = idx[nstart] - 1
    while i >= 0 and text[i].isspace():
        i -= 1
    return i >= 0 and bool(BOX.match(text[i]))


# The CAPI's own FILL placeholder, printed verbatim on the papers
# (`66. Is [facility_name_input] the facility you usually go to …`). It is a fill, not
# text anyone translated, and F3's dictionary carries an ID-block item labelled
# `Facility Name` — which, normalised, sits INSIDE `facility name input`. That anchor
# therefore bounded a span in the middle of the placeholder and cut every Q66/Q88
# translation down to `Ang [` on all seven papers. Nothing inside a placeholder is an
# anchor occurrence.
FILL_PLACEHOLDER = re.compile(r"\[[A-Za-z0-9_]*_input\]", re.I)


def placeholder_spans(text):
    """[(start, end)] of every fill placeholder in the ORIGINAL text."""
    return [(m.start(), m.end()) for m in FILL_PLACEHOLDER.finditer(text)]


def inside_placeholder(spans, o_start, o_end):
    return any(s <= o_start and o_end <= e for s, e in spans)


def anchor_prefix(en):
    """The first PREFIX_WORDS normalised words of a label, or None when the label is not
    longer than that.

    Q75's class: the dcf label is a CSPro-255-cap condensation of a longer paper
    paragraph, so the verbatim anchor is never found and the key used to be emitted
    NOWHERE — neither clean nor flagged — while the PREVIOUS anchor's span ran on into
    Q75's English. A prefix that short is only meaningful for a label the cap actually
    bit into, hence the length guard.
    """
    words = norm_for_match(en).split()
    if len(words) <= PREFIX_WORDS:
        return None
    return " ".join(words[:PREFIX_WORDS])


def condensed_candidate(span, en):
    """Drop the leading English of a prefix-anchored span.

    After a prefix anchor the span opens with the REST of the paper's English paragraph
    (the part the dcf label condensed away), then the translation. pdf_text() has already
    collapsed the page to one line, so "skip leading English lines" is applied per
    sentence: drop leading sentences that read as English (extract_notes.looks_english)
    or that are literally part of the anchor's own label — the label's tail
    ("Based on your practice, is this enough?") is short enough to score below
    looks_english's three-function-word bar.
    """
    nen = norm_for_match(en)
    segs = [s for s in re.split(r"(?<=[.?!])\s+", span.strip()) if s.strip()]
    i = 0
    while i < len(segs):
        nseg = norm_for_match(segs[i])
        if nseg and (looks_english(segs[i]) or nseg in nen):
            i += 1
            continue
        break
    return " ".join(segs[i:]).strip()


_EMPTY_GROUP = re.compile(r"\(\s*\)\s*$")


def trim_unbalanced_parens(s):
    """Drop the bracket a cut paren group left behind (the Ilocano layout).

    Written for F2 by Task 21b and moved here by Task 27, which met the same fact on
    F1: every Ilocano translation is printed inside ( ), and when the span boundary
    falls inside one, clean_span()'s Task-16c rules cannot help — they need the string
    to have no partner bracket AT ALL, and a NESTED pair (`(Ania ti naganmo? (Apellido,
    Ext)`) always leaves one. Counting decides which end is the orphan.
    """
    prev = None
    while prev != s:
        prev = s
        s = s.strip()
        if s.endswith("("):                          # an opener with nothing after it
            s = s[:-1].rstrip()
        s = _EMPTY_GROUP.sub("", s).rstrip()
        if s.startswith("(") and s.count("(") > s.count(")"):
            s = s[1:].lstrip()
        elif s.endswith(")") and s.count(")") > s.count("("):
            s = s[:-1].rstrip()
    return s


def trim_unbalanced_quotes(s):
    """Drop the double quote a cut quotation left behind at either end (Task 27).

    12 of the 19 orphan-glyph rows Task 17 shipped opened with `" ` — the CLOSING quote
    of an English label that is itself quoted (`"Patients are always referred
    appropriately"`), left at the head of the span. A balanced pair is the paper's own
    quotation and is content, so only an odd count is trimmed; a lone curly quote is an
    orphan whichever way it points.
    """
    prev = None
    while prev != s:
        prev = s
        s = s.strip()
        if s[:1] == "”":                        # a closing curly quote opens nothing
            s = s[1:].lstrip()
        elif s[-1:] == "“":                     # an opening curly quote closes nothing
            s = s[:-1].rstrip()
        # Task 40: the curly pair gets the same odd-count test the straight pair
        # has always had. The HIL paper closes Q28/Q29 with a `”` that opens
        # nowhere on the page, so the glyph is at the TAIL and the two tests
        # above — which only know a quote pointing the wrong way — left it on 4
        # F4 rows. A balanced pair is the paper's own quotation and is content.
        elif s.count("“") != s.count("”"):
            if s[-1:] == "”" and s.count("”") > s.count("“"):
                s = s[:-1].rstrip()
            elif s[:1] == "“" and s.count("“") > s.count("”"):
                s = s[1:].lstrip()
        elif s.count('"') % 2:
            if s[:1] == '"':
                s = s[1:].lstrip()
            elif s[-1:] == '"':
                s = s[:-1].rstrip()
    return s


def strip_wrapping_brackets(s):
    """Drop ONE pair of square brackets that wraps the WHOLE value (Task 33b).

    The Aug-21 Tagalog papers print the Filipino gloss inside brackets after the
    English (`Male [Lalaki]`), so the delimiter rides into the span. It is the
    paper's furniture exactly as the Waray question number is, and it is a
    convention of the PAPER rather than of one instrument, so the rule lives here
    where every extract gets it.

    Three deliberate limits:
      * the opening bracket's PARTNER must be the final character — `[A] at [B]`
        opens and closes with a bracket and balances, but is two glosses, not one
        wrap, and counting `[` against `]` cannot tell the two apart;
      * exactly one pair goes, so `[[Lalaki]]` still shows a bracket instead of
        being silently repaired into a shape no paper printed;
      * an unbalanced value is left alone — a cut span is a worklist matter, and
        trim_unbalanced_parens/quotes deliberately do not know brackets either.

    Parentheses are NOT this function's business: clean_span's own loop already
    unwraps a whole balanced paren group (the Ilocano layout, Task 16c/27), and the
    ILO directive constants legitimately keep their `( … )`.
    """
    t = s.strip()
    if not (t.startswith("[") and t.endswith("]")):
        return s
    depth = 0
    for i, ch in enumerate(t):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth < 0:
                return s
            if depth == 0:
                if i != len(t) - 1:           # the head's partner closes early
                    return s
                return t[1:-1].strip() or s   # nothing inside is not a translation
    return s                                   # never closed: unbalanced


def clean_span(span):
    s = BOX.sub(" ", span)
    s = SKIP_NOTE.sub(" ", s)
    s = TRAILING_NOTE.sub(" ", s)
    s = ARROW_NOTE.sub(" ", s)
    s = strip_directives(s)
    s = " ".join(s.split()).strip(" .:;,-")
    # residue of the anchor's own trailing punctuation ("? (", ") /" when the
    # anchor's normalised form ends before a closing paren, slashes, dashes)
    s = s.lstrip("?!.:;,)/- ").strip()
    # Ilocano layout: the whole candidate is one balanced paren group ... and when the
    # span cut one half of that group away, the surviving bracket is layout residue, not
    # content (Task 16c). Task 27 replaced 16c's two one-sided bracket tests with the
    # counting trims, which also see the orphan next to a BALANCED group, and made the
    # pair a loop — an orphan `"` in front of a parenthesised Ilocano translation hides
    # the whole-group unwrap from it until the quote is gone.
    prev = None
    unwrapped = False
    while prev != s:
        prev = s
        if s.startswith("(") and s.endswith(")") and s.count("(") == s.count(")"):
            inner = s[1:-1].strip()
            if inner:
                s = inner
        if not unwrapped:
            # Task 33b: the Tagalog gloss delimiter. ONCE, but inside the loop, so
            # whatever the pair was wrapping still gets the paren/quote trims.
            t = strip_wrapping_brackets(s)
            unwrapped = t != s
            s = t
        s = trim_unbalanced_quotes(trim_unbalanced_parens(s))
    # Task 16c: a candidate with no alphanumerics at all is not a translation - it becomes
    # an `empty` worklist row instead of shipping a lone glyph as a value.
    if not norm_for_match(s):
        return ""
    return s


def digits_of(s, strip_qnum=True):
    if strip_qnum:
        s = re.sub(r"^\s*\d+(\.\d+)?\s*\.", "", s)
    return Counter(re.findall(r"\d+", s))


def value_set_siblings(anchors):
    """{normalised option EN: the normalised EN of the OTHER options in its value set}.

    The key carries the value set (`val:<VS>:<code>`), so the siblings of a one-line
    option row are known without looking at the paper. They are the boundaries that
    `Yes`/`No` never provided (both are below MIN_BOUND).
    """
    groups = defaultdict(set)
    for key, en in anchors.items():
        parts = key.split(":")
        if parts[0] == "val" and len(parts) >= 3:
            ne = norm_for_match(en)
            if ne:
                groups[parts[1]].add(ne)
    sib = defaultdict(set)
    for nes in groups.values():
        for ne in nes:
            sib[ne] |= nes - {ne}
    return sib


def english_words(anchors):
    """Every normalised WORD the instrument's own English labels use (Task 27).

    The extractor has no dictionary of English; it has the dcf, and the dcf is written
    in the language the papers put on the left of every row. That corpus is enough to
    say whether a span is a translation or the paper's English carrying on.
    """
    return {w for en in anchors.values() for w in norm_for_match(en).split()}


def short_option_anchor(ne, keys):
    """True for a `val:`-only anchor of at most SHORT_OPTION_WORDS words.

    These are the option labels the papers also print as the OPENING of a longer English
    phrase — `☐ Facility Head` in the F1 ICF respondent-type list against the Q62 option
    `Facility`. A label that is also an item label, or one long enough that no longer
    English phrase starts with it, keeps the plain span rule.
    """
    return bool(ne) and len(ne.split()) <= SHORT_OPTION_WORDS and \
        all(k.startswith("val:") for k in keys)


def own_match_is_english(tr, corpus):
    """True when the span a short option anchor opened is itself ENGLISH (Task 27).

    Task 16c's box gate decides whether such a label may BOUND a span; it says nothing
    about the span that opens behind the box, and `☐ Facility Head` is as boxed as
    `☐ Facility Pasilidad`. This is the own-match half: a value every word of which is a
    word of the dictionary's own English is the paper's English continuing, not this
    option's translation. It shipped `Head` into all seven F1 maps (Task 17, held).
    """
    nt = norm_for_match(tr)
    if not nt or not tr.isascii():
        return False
    return all(w in corpus for w in nt.split())


def value_set_codes(anchors):
    """{value-set name: {the codes it defines}} — the roster CODES legend, from the keys.

    Task 27 fix round 1. The household-roster pages print an option list as a legend
    (`01-Head 02-Spouse/Partner 03-Son/Daughter …`) rather than as boxed rows, so a span
    that ends at the next option's English carries that option's CODE. Which numbers are
    codes is knowable without the paper: they are in the `val:<VS>:<code>` keys.
    """
    out = defaultdict(set)
    for key in anchors:
        parts = key.split(":")
        if parts[0] == "val" and len(parts) >= 3:
            out[parts[1]].add(parts[2])
    return dict(out)


def _between(text, idx, prev_end, cur_start):
    """The ORIGINAL text lying between two occurrences given in NORMALISED coordinates."""
    a = idx[prev_end - 1] + 1 if prev_end - 1 < len(idx) else len(text)
    b = idx[cur_start] if cur_start < len(idx) else len(text)
    return text[a:b] if b > a else ""


def _sibling_option_pair(prev, cur, sib, by_norm):
    """True when two kept occurrences are DIFFERENT `val:` options of the SAME value set."""
    pne, ne = prev[2], cur[2]
    return (pne != ne and pne in sib.get(ne, ())
            and all(k.startswith("val:") for k in by_norm.get(ne, ()))
            and all(k.startswith("val:") for k in by_norm.get(pne, ())))


def _empty_option_span(text, idx, prev, cur):
    """True when prev's span — prev's end to cur's start — carries no translation.

    False for OVERLAPPING occurrences: `No` and `No, but have submitted requirements …`
    start at the same offset and the de-overlap keeps both, so the gap between them is
    zero because they are the same words, not because the paper printed nothing.
    """
    if prev[1] > cur[0]:
        return False
    between = _between(text, idx, prev[1], cur[0])
    return not clean_span(cut_at_local_directive(cut_at_note(cut_at_box(between)))).strip()


def sibling_run(text, idx, kept, i, sib, by_norm, tr):
    """True when kept[i]'s span is a BLOCK shared with the option row before it.

    Task 48 — the row-inheritance class the final whole-branch review found. Some option
    grids are printed as a PAIR of boxed ENGLISH rows followed by BOTH translations as one
    un-boxed block, because the PDF lays the page out in two columns and the text comes
    out column by column:

        ☐ Legislation ☐ LGU/ Barangay Balaod LGU/Barangay        (F3_CEB.txt, Q36)
        ☐ DOH standard referral form ☐ City / LGU standard referral form
        Syudad / LGU surundon nga porma han pagrefer DOH nga surundon nga …  (F2_WAR.txt)

    The first row's span is box-to-box and therefore EMPTY, which leaves the whole block to
    the second row's span. What the second row then takes is not its own translation:
    either the neighbour's alone (where the trailing row is untranslated on the paper, so
    the anchor re-matches on its own echo and bounds the span there — `Balaod`, code 02's
    text, shipped as code 06 on seven F3 CEB questions) or both glued (the F2 WAR row live
    in production). Nothing on the page says which half is whose — the F2 block prints the
    two translations in the REVERSE order of their English rows — so the block is held, not
    split: this candidate is flagged `sibling-run` and the row before it stays `empty`.

    An empty predecessor is NOT on its own evidence of a block, and this is the guard that
    matters most: the papers routinely leave ONE option row untranslated and translate the
    next one (`☐ Annulled ☐ Widowed Balo`, `☐ E-referral ☐ Referring facility calls
    receiving facility Tumatawag …`). Measured over the 28 papers, firing on the empty
    predecessor alone moved ~230 CORRECT values to the worklist. So the pair must also
    carry one of the two signatures a shared block leaves behind:

      block-echo   the span ENDS at another occurrence of THIS anchor. The trailing row's
                   own "translation" is its English repeated (`LGU/ Barangay` ->
                   `LGU/Barangay`), so everything the span holds is the neighbour's.
      block-size   the span is more than PAIR_BLOCK_RATIO times its own English, and that
                   English is at least PAIR_BLOCK_MIN_EN long. Two translations do not fit
                   in one row's worth of text; the F2 WAR block is 2.6x its label, while
                   the untranslated-neighbour rows above are 0.6-1.6x. The length floor is
                   what keeps the test off a SHORT label, where one verbose rendering is
                   over the ratio on its own (`Brother` -> `Igsoon nga lalaki`, 2.4x).

    The pair itself is checked by three further guards, each measured:
      * BOTH rows behind a ballot box — the grid signature (it is the box-to-box span that
        comes out empty), and on the PREVIOUS row it is what keeps the rule off the row
        AFTER a block, where the predecessor is the trailing row's own un-boxed ECHO;
      * the two occurrences do not OVERLAP — `☐ No, but have submitted requirements …` is
        a hit of the option `No` and of the long option at the same offset and the
        de-overlap keeps both, so their zero-length gap is not an empty span (20 correct
        F1 values);
      * the predecessor is a PAIR partner, not a list — where the row before it is also an
        empty-span boxed sibling the paper left that whole option list in English (`☐ Pap
        smear ☐ Mammogram … ☐ All of the above Tanan nga giingon`) and the single
        translation after the last row is that row's own.
    """
    if i == 0:
        return False
    prev, cur = kept[i - 1], kept[i]
    if not _sibling_option_pair(prev, cur, sib, by_norm):
        return False
    if not (behind_box(text, idx, prev[0]) and behind_box(text, idx, cur[0])):
        return False
    if not _empty_option_span(text, idx, prev, cur):
        return False
    if i >= 2 and _sibling_option_pair(kept[i - 2], prev, sib, by_norm) \
            and behind_box(text, idx, kept[i - 2][0]) \
            and _empty_option_span(text, idx, kept[i - 2], prev):
        return False
    block_echo = i + 1 < len(kept) and kept[i + 1][2] == cur[2]
    block_size = (len(cur[2]) >= PAIR_BLOCK_MIN_EN
                  and len(norm_for_match(tr)) > PAIR_BLOCK_RATIO * len(cur[2]))
    return block_echo or block_size


def duplicate_label_keys(clean, anchors):
    """The `val:` keys of `clean` that two codes of ONE value set would label identically.

    Task 48, the second half of the row-inheritance class. A value set whose codes 01, 02
    and 03 all read `Mahirap magparehistro` gives the respondent three choices it is
    impossible to tell apart, and the enumerator no way to record what was meant. It
    happens where the PAPER itself repeats one translation across option rows (F4 FIL
    Q45.2) and where one English label lives in two value sets and the poisoned occurrence
    won the count (F4 WAR Q128/Q134 code 05). Neither row can be trusted, so both go to
    the worklist.

    Codes that share the SAME English are aliases, not a defect: the zero-padded `01`/`1`
    pair and the legacy `8`/`99` "Other (specify)" pair MUST carry the same translation.
    """
    by_vs = defaultdict(list)
    for key, tr in clean.items():
        parts = key.split(":")
        if parts[0] == "val" and len(parts) >= 3 and (tr or "").strip():
            by_vs[parts[1]].append(key)
    out = []
    for keys in by_vs.values():
        by_tr = defaultdict(list)
        for key in keys:
            by_tr[norm_for_match(clean[key])].append(key)
        for group in by_tr.values():
            if len(group) > 1 and len({norm_for_match(anchors.get(k, "")) for k in group}) > 1:
                out.extend(group)
    return sorted(out)


def _legend_codes_for(keys, vs_codes):
    """(legend codes reachable from these keys, the anchor's OWN codes), as ints.

    A `val:`/`vs:` key names its value set; an `item:` key names none, so its legend is
    the union of the value sets written as `<ITEM>_VS…` — the shape every F1/F3/F4
    dictionary uses.
    """
    legend, own = set(), set()
    for key in keys:
        parts = key.split(":")
        if parts[0] == "val" and len(parts) >= 3:
            names = [parts[1]]
            if parts[2].isdigit():
                own.add(int(parts[2]))
        elif parts[0] == "vs" and len(parts) >= 2:
            names = [parts[1]]
        elif parts[0] == "item" and len(parts) >= 2:
            names = [n for n in vs_codes if n.startswith(parts[1] + "_VS")]
        else:
            names = []
        for n in names:
            legend |= {int(c) for c in vs_codes.get(n, ()) if c.isdigit()}
    return legend, own


LEGEND_TAIL = re.compile(r"\s+(\d{1,2})$")


def strip_legend_code(tr, en, keys, vs_codes):
    """Drop the NEXT option's roster-legend code from the tail of a span (Task 27 fix 1).

    `☐ Yes Oo` is a boxed row and Task 16b's `cut_at_box` ends the span at the next box;
    a LEGEND row has no boxes to cut at, so the span runs to the next option's English
    and clean_span() hands back `Agum 03`. 154-166 F4 clean rows shipped that tail, 48
    of them over a DIFFERENT live value.

    The tail is dropped only when every one of these holds — anything else is left
    exactly as it was, so the "no rule, no change" invariant survives:
      * the value ends in 1-2 digits after whitespace and something survives them;
      * that number is a code of a value set THIS anchor's key names, and is not the
        anchor's own code (`Level 3` under code 3 keeps its 3);
      * the English label does not itself end in that number.
    """
    m = LEGEND_TAIL.search(tr or "")
    if not m:
        return tr
    head = tr[:m.start()].rstrip()
    if not norm_for_match(head):
        return tr
    code = int(m.group(1))
    if re.search(r"(?<!\d)" + str(code) + r"$", (en or "").strip()):
        return tr
    legend, own = _legend_codes_for(keys, vs_codes)
    if code in own or code not in legend:
        return tr
    return head


# Task 32b: the paper's own question number, printed in front of the LOCAL row.
# `27. `, `71a. `, `45.1. ` — a number, an optional sub-number, an optional letter, a
# full stop and at least one space. Whitespace after the stop is what separates the
# token from content: `1.5 kilometro` and `27.Mayda` are never touched.
QNUM_HEAD = re.compile(r"^(\d{1,3})(?:\.(\d{1,2}))?[a-z]?\.\s+(?=\S)")
# The CAPI's own number, read off the key: `item:Q27_…` / `vs:Q27_…_VS1` /
# `val:Q140_…_VS1:04`, and the sub-numbered `item:Q45_1_PIN_REG_WHEN` = 45.1.
KEY_QNUM = re.compile(r"^(?:item|vs|val):Q(\d{1,3})(?:_(\d{1,2}))?(?![0-9])")


def key_question_numbers(keys):
    """{(question, sub-question or None)} the KEYS name, as ints — the CAPI's numbering.

    An anchor is shared by every key with the same English (an item label and its
    value-set label), so the answer is a set: the printed number is right if it is any
    one of them.
    """
    out = set()
    for key in keys:
        m = KEY_QNUM.match(key)
        if m:
            out.add((int(m.group(1)), int(m.group(2)) if m.group(2) else None))
    return out


def strip_question_number(tr, en, keys):
    """(value without the paper's leading question number, wrong-number?) — Task 32b.

    The Waray Aug-21 papers number the LOCAL row as well as the English one
    (`27. Does the family own a refrigerator/freezer? 26. Mayda ba refrigerator …`), so
    the span opens with a number that the CAPI already prints from the English label.
    154 F4 WAR values shipped it in v3.2.0; the other six locales' papers number only
    the English row, so stripping it also puts WAR back in step with them.

    The number is dropped either way — it is the paper's furniture, never translated
    text — but it is only dropped SILENTLY when it agrees with the key's own question
    number. Seven v3.2.0 rows printed a number that contradicts the key (Q27 -> `26.`,
    Q64 -> `67.`): the text may answer a different question than the key it lands on, so
    the row is flagged `paper-number-mismatch` and reaches the worklist instead of a map.
    A key that carries no `Qnn` at all (`val:ENUM_RESULT_FINAL_VISIT_VS1:4`) cannot
    confirm the number and is flagged for the same reason.

    Left exactly as it was — the "no rule, no change" invariant — when: the head is not
    a question-number token; nothing survives the strip; or the remainder is this
    anchor's OWN English with its number removed, which is an `echo-english` worklist
    row that stripping would hide from qa_flags().
    """
    m = QNUM_HEAD.match(tr or "")
    if not m:
        return tr, False
    rest = tr[m.end():].strip()
    if not norm_for_match(rest):
        return tr, False
    if norm_for_match(rest) == norm_for_match(QNUM_HEAD.sub("", en or "", count=1)):
        return tr, False
    num = int(m.group(1))
    sub = int(m.group(2)) if m.group(2) else None
    agrees = any(q == num and (sub is None or s is None or s == sub)
                 for q, s in key_question_numbers(keys))
    return rest, not agrees


def option_anchor_ok(ne):
    """A sub-MIN_BOUND option label may anchor only if it is a word (`Yes`, `No`, `None`),
    never a bare code or a single character."""
    return len(ne) >= 2 and any(c.isalpha() for c in ne)


YES_NO = re.compile(r"\byes\b.*\bno\b", re.I)


def _other_label_in(padded, ne, candidates, min_len=0, max_len=None, at_end=False):
    """True if any OTHER label in `candidates` sits word-bounded inside `padded`.

    `padded` is " <normalised translation> "; `ne` is this anchor's own normalised English.
    The three Aug-21 sibling scans in qa_flags() below (`glued-short-label`,
    `ends-with-other-label`, `grid-bleed`) had drifted into three near-copies of this loop,
    so they are one helper. The self-guard is WORD-bounded (" male " sits inside
    " male nurse " but NOT inside " female "; a plain substring guard silently suppressed
    11 real F1 collisions, including the 2026-08-17 live spill itself). The June-5
    `contains-other-label` scan keeps its own substring guard and is left verbatim.
    """
    for other in candidates:
        if not other or other == ne or len(other) < min_len:
            continue
        if max_len is not None and len(other) >= max_len:
            continue
        if f" {other} " in f" {ne} ":
            continue
        if padded.endswith(f" {other} ") if at_end else (f" {other} " in padded):
            return True
    return False


# ------------------------------------------------ truncated-tail (Task 40, fix 1) --
# An English anchor can sit MID-PHRASE inside a DIFFERENT question. `Primary care
# provider` is an option label of F3 Q39/Q40/Q44, so its occurrence inside Q53's stem
# ("Do you have a primary care provider?") and inside Q68's option row
# ("YAKAP/Konsulta or primary care provider") bounds the span there too, and the
# translation is cut where the English restarts. Those cuts landed in the CLEAN extract -
# no flag saw them - and shipped, replacing complete June-5 translations with fragments
# (`Igwa ba kamo ki primary care provider?` -> `Igwa ba kamo ki`). The only length test
# that existed lives in the wave's defect sweep and fires at "under half the English
# length", which most of them are not.
#
# What every one of them has in common is the TAIL: a proclitic - a case marker,
# article, linker or preposition - that cannot end a phrase in any of the seven
# languages. The set below is closed-class proclitics ONLY. Enclitics that legitimately
# end a phrase are deliberately absent (Hiligaynon/Tagalog `na` "already" - `Retiro na`
# is a complete translation of "Retired"; `ka`, `ba`, `kadi`, `man`), because holding a
# good value costs coverage.
PROCLITIC_TAIL = frozenset("""
    a an the of to in on for and or with from at by into upon per
    ang ng nang sa si ni kay kina sina nina mga at para o
    an nin ki kan kang asin kun sarong
    og ug
    sang kag sing
    han ha hin ngan san
    ti iti ken dagiti kenni kadagiti wenno
    nga
""".split())
# A value that ends on one of these ended a SENTENCE - the proclitic is the paper's own
# last word, not a cut (`... ang pasilidad para sa?`).
TERMINAL_STOPS = "?.!…:;)]}»”\"'"


def truncated_tail(en, tr):
    """Reason string when `tr` stops mid-phrase, else None (Task 40 fix round 1).

    Two shapes, both measured on the F3 write set (`task-40/_tail_probe.py`):

      * the last token is a `PROCLITIC_TAIL` word and the value does NOT end on a
        terminal stop - the span was cut at an embedded English anchor
        ("YAKAP/Konsulta o", "Trabahador ti Salun-at ti", "Libre, singir iti");
      * the value ends on a LONE CAPITAL LETTER - the paper's English definition block
        restarted right behind the translation and only its article came through
        ("Mayda ka ba panguna nga nag-aataman? A").

    Both tests are guarded by the anchor's OWN English: a label that itself ends on that
    word ("Not yet, but I'm planning **to**") or on a lone capital ("Vitamin A") makes
    the same tail evidence of nothing.
    """
    toks = (tr or "").strip().split()
    if not toks:
        return None
    etoks = (en or "").strip().split()
    elast = etoks[-1] if etoks else ""
    last = toks[-1]
    if len(last) == 1 and last.isalpha() and last.isupper():
        if len(elast) == 1 and elast.isalpha() and elast.isupper():
            return None
        return f"ends on a lone capital {last!r}"
    if last[-1] in TERMINAL_STOPS:
        return None
    w = last.strip(_EDGE).lower()
    if w in PROCLITIC_TAIL and elast.strip(_EDGE).lower() != w:
        return f"ends on the proclitic {w!r}"
    return None


def qa_flags(en, tr, nlabels, siblings=()):
    flags = []
    if not tr:
        return ["empty"]
    ne, nt = norm_for_match(en), norm_for_match(tr)
    if nt == ne:
        flags.append("echo-english")
    if len(tr) > MAX_SPAN:
        flags.append("overlong-span")
    ratio = len(nt) / max(len(ne), 1)
    if ratio < 0.25 or ratio > 4.0:
        flags.append("length-ratio")
    # catastrophic: the "translation" IS another English label verbatim
    # ("Physician" -> "Nurse" when the next option had no anchored translation)
    if nt != ne and nt in nlabels:
        flags.append("is-other-label")
    # boundary bleed: candidate contains some OTHER known label (word-bounded)
    padded = f" {nt} "
    for other in nlabels:
        if other == ne or len(other) < 10 or other in ne:
            continue
        if f" {other} " in padded:
            flags.append("contains-other-label")
            break
    # table-row bleed: Yes/No + amount furniture swept up from a grid
    if " yes " in padded and " no " in padded and len(nt) < 90:
        flags.append("table-bleed")
    if "amount in pesos" in padded:
        flags.append("table-bleed")
    de, dt = digits_of(en), digits_of(tr, strip_qnum=False)
    if de and dt and de != dt and (de - dt or dt - de):
        # digits present on both sides but different sets -> e.g. Level 3 -> Level 1
        if set(de) != set(dt):
            flags.append("digit-mismatch")
    if nt.startswith(ne[: max(10, len(ne) // 2)]) and len(nt) > len(ne):
        flags.append("starts-with-english")
    # span opens mid-English-sentence: the dcf label was truncated relative to
    # the paper wording, so the span begins with the English tail, not a translation
    first = nt.split(" ", 1)[0] if nt else ""
    if first in {"to", "of", "and", "for", "in", "the", "with", "from", "are",
                 "is", "was", "has", "have", "that", "by", "on", "or", "date"}:
        flags.append("starts-mid-english")
    # ---- Aug-21 additions (2026-08-25) — appended, June-5 flags above untouched ----
    # glued-short-label: a SHORT other anchor (4-9 chars, below contains-other-label's
    # floor and often below MIN_BOUND so it never bounded the span) sits inside the span:
    # the ")  Male (Lalaki" class that rendered live on 2026-08-17.
    # Both new loops skip an anchor that is part of the span's OWN English, and that
    # test is WORD-BOUNDED (" male " sits inside " male nurse " but NOT inside
    # " female "). A plain `other in ne` substring test suppressed the flag for exactly
    # the pairs it exists to catch - on the real F1 dictionary it silently killed 11
    # collisions including ("male", "female"), the 2026-08-17 spill itself.
    if _other_label_in(padded, ne, nlabels, min_len=4, max_len=10):
        flags.append("glued-short-label")
    # ends-with-other-label: the span's last word(s) are another anchor's English
    # (Yes/No/Oo grid furniture, a following option's English swept in).
    if _other_label_in(padded, ne, nlabels, min_len=3, at_end=True):
        flags.append("ends-with-other-label")
    # ---- Aug-21 LAYOUT additions (Task 16b, 2026-08-25) ----
    # directive-bleed: an English interviewer directive survived clean_span(). By design
    # strip_directives() should have removed it, so this is the net that catches a
    # directive variant DIRECTIVE_PATTERNS does not yet know — it must never be clean.
    if has_directive(tr):
        flags.append("directive-bleed")
    # routing-note: an unbalanced <…> the note stripper could not close.
    if "<" in tr or ">" in tr:
        flags.append("routing-note")
    # grid-bleed: a one-line option row swept a SIBLING option's English into the value
    # ("Oo No Hindi"), or an English Yes…No pair rode in from the grid.
    # Task 16c: a 1-2 char sibling only bleeds into a one-line option row, and a one-line
    # option row is what the sub-MIN_BOUND anchors ARE. On a longer option label such a
    # sibling is a word of the language - Ilocano `no` means "if".
    sib_floor = 0 if len(ne) < MIN_BOUND else 3
    if YES_NO.search(nt) or _other_label_in(padded, ne, siblings, min_len=sib_floor):
        flags.append("grid-bleed")
    # local-directive: the paper's LOCAL rendering of an interviewer directive, with no
    # English original in front of it for skip_translated_directive() to hang off.
    if local_directive(en, tr):
        flags.append("local-directive")
    # english-furniture: a recognised English NOTE survived the span cut - the net under
    # cut_at_note(), exactly as `directive-bleed` is the net under strip_directives().
    if has_furniture(tr):
        flags.append("english-furniture")
    # ---- Aug-21 layout flag (Task 40 fix round 1) ----
    # truncated-tail: the span was cut at an anchor that sits MID-PHRASE inside another
    # question, so the value stops on a proclitic or on a lone capital letter. The
    # mirror image of `starts-mid-english` above, and the class that shipped 35
    # fragments over seven F3 maps before it existed.
    if truncated_tail(en, tr):
        flags.append("truncated-tail")
    return flags


def find_paper(source_dir, instrument, paper_name):
    """Aug-21 naming: F<n>-<Language>_<title>_Aug21.pdf (instrument FIRST — the June-5
    glob '<Language>*<Fn>*.pdf' does not match these files)."""
    cands = sorted(Path(source_dir).glob(f"{instrument}-{paper_name}*.pdf")) or \
        sorted(Path(source_dir).glob(f"{paper_name}*{instrument}*.pdf"))
    return cands[0] if cands else None


def extract(pdf_path, anchors, text=None):
    """anchors: {key: EN}. Same span algorithm as the June-5 extract(), but the
    occurrence list carries the KEY, so identical English on two nodes (an item label and
    its vs: label, or the same option under two value sets) yields one pair per key.

    Task 16b adds the five Aug-21 paper LAYOUT rules on top, all of them span-boundary or
    span-cleaning rules — where none of them fires the answer is what it always was:
      1. an interviewer directive between the English and the translation is cut away
         (clean_span -> strip_directives); nothing left = `directive-only`;
      2. no span crosses a ballot box, and a sub-MIN_BOUND option label anchors when it
         sits behind one, so `<box> Yes Oo <box> No Hindi` yields `Oo` and `Hindi`;
      3. <...> / -> Qn routing notes are cut away; residue = `routing-note`;
      4. a label the CSPro 255-char cap condensed anchors on its 12-word prefix, which
         also ends the PREVIOUS anchor's span; the pair is always `label-condensed`;
      5. an anchor found nowhere in the paper is emitted as `not-in-paper` instead of
         vanishing.

    Task 16c adds two more, and a `text=` seam: pass the page text directly and no PDF is
    read, so the box rules can be tested without a symbol font installed.
      6. a ONE-WORD `val:` option label bounds a span only where it sits behind a box —
         `PhilHealth`, `Public`, `Facility`, `Monthly` are above MIN_BOUND and occur
         inside translated sentences, where they used to cut 149 F1 values in half;
      7. a recognised English NOTE ends the question's span (cut_at_note).
    """
    if text is None:
        text = pdf_text(pdf_path)
    ntext, idx = build_norm(text)

    # group keys by normalised English so each distinct text is searched once
    by_norm = defaultdict(list)
    for key, en in anchors.items():
        by_norm[norm_for_match(en)].append(key)
    sib = value_set_siblings(anchors)
    corpus = english_words(anchors)
    vs_codes = value_set_codes(anchors)

    def _finditer(needle):
        pat = re.compile(r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])")
        return list(pat.finditer(ntext))[:MAX_OCC]

    occ = []          # (start_norm, end_norm, norm_en, is_prefix)
    seen_full = set()
    fills = placeholder_spans(text)

    def _in_fill(m):
        """True if this normalised occurrence lies wholly inside a fill placeholder."""
        if not fills or m.start() >= len(idx):
            return False
        return inside_placeholder(fills, idx[m.start()],
                                  (idx[m.end() - 1] + 1) if m.end() - 1 < len(idx)
                                  else len(text))
    for ne in by_norm:
        short_option = len(ne) < MIN_BOUND and ne in sib and option_anchor_ok(ne)
        # Task 16c: a label that is ONE WORD and belongs to nothing but `val:` keys is an
        # option label, and an option label is printed behind a ballot box. Its other
        # occurrences are that word used in a sentence ("... para sa PhilHealth?"), where
        # bounding a span cuts a real translation in half. Multi-word option labels are
        # NOT gated: "Single, never married" never turns up mid-sentence, and plenty of
        # papers print option rows with no box at all.
        one_word_val = " " not in ne and all(k.startswith("val:") for k in by_norm[ne])
        if len(ne) < MIN_BOUND and not short_option:
            continue
        # NO small cap here: frequent option labels ("Others (specify)", the Yes-
        # variants) must bound EVERY span they open, or spans bleed into the next
        # English option. MAX_OCC is a runaway guard, not a working limit.
        for m in _finditer(ne):
            if (short_option or one_word_val) and not behind_box(text, idx, m.start()):
                continue
            if _in_fill(m):
                continue
            occ.append((m.start(), m.end(), ne, False))
            seen_full.add(ne)
    # condensed labels: the verbatim anchor is nowhere on the paper, so fall back to its
    # 12-word prefix — ONCE, so a repeated stem cannot open a second bogus span.
    for ne in by_norm:
        if ne in seen_full:
            continue
        pref = anchor_prefix(anchors[by_norm[ne][0]])
        if not pref or len(pref) < MIN_BOUND or pref in by_norm:
            continue
        hits = _finditer(pref)
        if len(hits) != 1:
            continue
        occ.append((hits[0].start(), hits[0].end(), ne, True))
    occ.sort()

    # de-overlap: keep the longest anchor at each position
    kept = []
    last_end = -1
    for s, e, ne, pref in occ:
        if s < last_end:
            if e <= last_end:
                continue
        kept.append((s, e, ne, pref))
        last_end = max(last_end, e)

    results = defaultdict(list)
    nlabels = set(by_norm)
    sub_min_emit = set()
    for i, (s, e, ne, is_prefix) in enumerate(kept):
        if len(ne) < MIN_EMIT and not (ne in sib and option_anchor_ok(ne)):
            sub_min_emit.add(ne)
            continue
        nxt = kept[i + 1][0] if i + 1 < len(kept) else len(ntext)
        o_start = idx[e - 1] + 1 if e - 1 < len(idx) else len(text)
        o_end = idx[nxt] if nxt < len(idx) else len(text)
        en = anchors[by_norm[ne][0]]
        raw = cut_at_local_directive(cut_at_note(cut_at_box(text[o_start:o_end])), en)
        extra = ()
        if is_prefix:
            raw = condensed_candidate(raw, en)
            extra = ("label-condensed",)
        # Task 27 fix 1: a legend row has no box for cut_at_box to end the span at,
        # so the span carries the NEXT option's code (`Agum 03`). Drop it here,
        # BEFORE the own-match gate and qa_flags, so both judge the real value.
        cleaned = clean_span(raw)
        tr = strip_legend_code(cleaned, en, by_norm[ne], vs_codes)
        # Task 32b: the Waray papers print the paper's question number in front of the
        # LOCAL row too, so the span opens `26. Mayda ba …`. Drop it here, in the same
        # slot and for the same reason as the legend code — the own-match gate and
        # qa_flags must judge the translation, not the paper's furniture.
        tr, wrong_number = strip_question_number(tr, en, by_norm[ne])
        # Task 33b: the legend code and the question number are printed OUTSIDE the
        # Tagalog gloss (`[Mahirap magparehistro] 01`), so while they were still
        # attached the value was not wholly wrapped and clean_span could not see the
        # pair. Look again — but ONLY if one of them actually fired, so a genuine
        # double wrap still loses exactly one pair. 10 F4 FIL legend rows.
        if tr != cleaned:
            tr = strip_wrapping_brackets(tr)
        if wrong_number:
            extra = tuple(extra) + ("paper-number-mismatch",)
        # Task 48: this span is the shared block of an adjacent-English PAIR — whatever it
        # holds belongs to the row before this one as much as to this one. Judged on the
        # cleaned `tr`, because one of the two block signatures is its LENGTH.
        if sibling_run(text, idx, kept, i, sib, by_norm, tr):
            extra = tuple(extra) + ("sibling-run",)
        # Task 27: the own-match half of the box gate. The occurrence is behind a box,
        # but the box was another row's — flag the candidate so the SAME anchor's other
        # occurrences get their turn, and so a label the paper never translated reaches
        # the worklist with the reason instead of shipping English.
        if tr and short_option_anchor(ne, by_norm[ne]) and own_match_is_english(tr, corpus):
            extra = tuple(extra) + ("english-own-match",)
        # Task 16c: `directive-only` claims the paper printed NO translation, so it may
        # only be set when the cleaned residue is empty. A sub-MIN_EMIT residue is not
        # nothing — a routing-note tail keeps `routing-note` and says so itself.
        if not extra and has_directive(raw) and not tr:
            extra = ("directive-only",)
        results[ne].append((tr, extra))

    clean, flagged = {}, []
    for ne, cands_tr in results.items():
        keys = by_norm[ne]
        en = anchors[keys[0]]
        best, best_flags = None, None
        counted = Counter(c for c in cands_tr if c[0] or c[1])
        for (tr, extra), _n in counted.most_common():
            # a layout flag already states WHY there is nothing to import; "empty"
            # ("nothing between this anchor and the next") would contradict it.
            fl = list(extra) if (extra and not tr) else \
                list(extra) + [f for f in qa_flags(en, tr, nlabels, sib.get(ne, ()))
                               if f not in extra]
            if not fl:
                best, best_flags = tr, []
                break
            if best is None:
                best, best_flags = tr, fl
        for key in keys:
            if best is None:
                flagged.append({"key": key, "en": en, "tr": "", "flags": ["empty"]})
            elif best_flags:
                flagged.append({"key": key, "en": en, "tr": best, "flags": best_flags})
            else:
                clean[key] = best
    # Task 48: two codes of one value set may not carry the same label. Judged on the
    # FINISHED clean set, because the two candidates come from different `ne` groups
    # (different English) and neither loop above can see the other's answer.
    for key in duplicate_label_keys(clean, anchors):
        flagged.append({"key": key, "en": anchors[key], "tr": clean.pop(key),
                        "flags": ["duplicate-label"]})
    # anchors the paper never printed: a worklist row, not a silent drop (Task 45)
    for ne, keys in sorted(by_norm.items()):
        if ne in results or ne in sub_min_emit or not ne:
            continue
        if len(ne) < MIN_EMIT and not (ne in sib and option_anchor_ok(ne)):
            sub_min_emit.add(ne)
            continue
        for key in keys:
            flagged.append({"key": key, "en": anchors[key], "tr": "", "flags": ["not-in-paper"]})
    return {"file": Path(pdf_path).name, "anchored": len(results), "clean": clean,
            "flagged": flagged, "sub_min_emit": len(sub_min_emit)}


# -------------------------------------------------------------------- output --
MEAN = {"is-other-label": "the 'translation' is verbatim another English label — worst class, never import",
        "starts-mid-english": "span opens mid-English (dcf label truncated vs the paper wording)",
        "table-bleed": "Yes/No or amount-grid furniture swept into the span",
        "echo-english": "translation is identical to the English (left untranslated on paper)",
        "starts-with-english": "span starts by repeating the English (run-together layout residue)",
        "contains-other-label": "span bleeds into the next question (boundary failure)",
        "overlong-span": "span too long — an un-anchored stretch follows",
        "length-ratio": "translation implausibly short/long vs the English",
        "digit-mismatch": "numbers differ between English and translation (e.g. Level 3 vs Level 1)",
        "empty": "nothing between this anchor and the next (paper copy identical to the English, or blank)",
        "glued-short-label": "a short option label (Male/Yes/None…) is glued inside the span — the 2026-08-17 live spill class",
        "ends-with-other-label": "span ends with another label's English (grid furniture / next option swept in)",
        # ---- Aug-21 layout flags (Task 16b) ----
        "directive-only": "the paper printed the interviewer directive and NO translation for this label",
        "directive-bleed": "an English interviewer directive survived cleaning — a directive variant DIRECTIVE_PATTERNS does not know yet",
        "grid-bleed": "a one-line option row swept a sibling option's English (Yes/No furniture) into the value",
        "routing-note": "an unbalanced <…> routing note is still inside the value",
        "label-condensed": "the dcf label is a CSPro-cap condensation of a longer paper paragraph — anchored on its 12-word prefix, so the translator must confirm which English this answers",
        "not-in-paper": "this anchor appears nowhere in the locale's paper — no translation exists to import",
        # ---- Aug-21 layout flags (Task 16c) ----
        "local-directive": "the paper's LOCAL-LANGUAGE rendering of an interviewer directive rode into the value (no English original in front of it to strip)",
        "english-furniture": "an English note or gloss from the paper is still inside the value — never import it as a translation",
        # ---- Aug-21 layout flag (Task 27) ----
        "english-own-match": "a short option label matched a box that was another row's, so the span is the paper's ENGLISH carrying on ('Facility' -> 'Head') — never import it",
        # ---- Aug-21 layout flag (Task 32b) ----
        "paper-number-mismatch": "the paper printed a question number in front of the translation that CONTRADICTS the key's own Q number (or the key carries none to check against) — the number is stripped and the row held, because the text may answer a different question",
        # ---- Aug-21 layout flags (Task 48, row-inheritance class) ----
        "sibling-run": "the paper printed this option row and the one before it as a run of ENGLISH rows followed by their translations as ONE block, so this span holds the neighbour's translation (alone, or glued to this row's) — the page does not say which half is whose, so neither row is written",
        "duplicate-label": "another code of the SAME value set would carry this exact translation while its English differs — two choices a respondent cannot tell apart, so neither is written",
        # ---- Aug-21 layout flag (Task 40 fix round 1) ----
        "truncated-tail": "the span was cut at an English anchor that sits MID-PHRASE inside another question, so the value stops on a proclitic ('Igwa ba kamo ki') or on the lone capital of a restarting English definition — a fragment, never import it"}

LAYOUT_FLAGS = ("directive-only", "directive-bleed", "grid-bleed", "routing-note",
                "label-condensed", "not-in-paper", "local-directive", "english-furniture",
                "english-own-match", "paper-number-mismatch", "truncated-tail",
                "sibling-run", "duplicate-label")


def differ_from_live(clean, live_path):
    """(differ, same, new) counts of CLEAN pairs vs the live map at live_path."""
    if not live_path or not os.path.exists(live_path):
        return None
    live = json.load(io.open(live_path, encoding="utf-8"))
    live.pop("_meta", None)
    differ = same = new = 0
    for k, v in clean.items():
        if k not in live:
            new += 1
        elif live[k] == v:
            same += 1
        else:
            differ += 1
    return {"differ": differ, "same": same, "new": new}


def write_outputs(results, out_dir, instrument, live_dir=None):
    """results: {locale code: extract() result or None}. Returns the QA-REPORT.md path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = ["# Paper-translation extraction — QA report", "",
              f"Instrument: **{instrument}**. Anchors: the build's English via walk_labeled_nodes().",
              "Keys are name-scoped (item:/vs:/val:). Nothing has been written into the build.", "",
              "| locale | file | anchored | clean pairs | flagged | differ from live | same | new |",
              "|---|---|---|---|---|---|---|---|"]
    fc, samples, per_loc = Counter(), defaultdict(list), OrderedDict()
    for code, r in results.items():
        if r is None:
            report.append(f"| {code} | — | — | — | no paper file | | | |")
            continue
        per_loc[code] = Counter()
        with io.open(out_dir / f"{code.lower()}.json", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(r["clean"], fh, ensure_ascii=False, indent=1); fh.write("\n")
        with io.open(out_dir / f"{code.lower()}_flagged.json", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(r["flagged"], fh, ensure_ascii=False, indent=1); fh.write("\n")
        dl = differ_from_live(r["clean"], os.path.join(live_dir, f"{code.lower()}.json")) if live_dir else None
        dcols = f"{dl['differ']} | {dl['same']} | {dl['new']}" if dl else " | | "
        report.append(f"| {code} | {r['file']} | {r['anchored']} | {len(r['clean'])} | {len(r['flagged'])} | {dcols} |")
        per_loc[code]["sub-min-emit"] = r.get("sub_min_emit", 0)
        for row in r["flagged"]:
            for fl in row["flags"]:
                fc[fl] += 1
                per_loc[code][fl] += 1
                if len(samples[fl]) < 2:
                    samples[fl].append((code, row["key"], row["en"][:70], row["tr"][:70]))
    if per_loc:
        cols = list(LAYOUT_FLAGS) + ["sub-min-emit"]
        report += ["", "## Aug-21 layout flags per locale (Task 16b)", "",
                   "| locale | " + " | ".join(f"`{c}`" for c in cols) + " |",
                   "|---" * (len(cols) + 1) + "|"]
        for code, cnt in per_loc.items():
            report.append(f"| {code} | " + " | ".join(str(cnt.get(c, 0)) for c in cols) + " |")
        report.append("")
        report.append("`sub-min-emit` counts anchors whose English is shorter than "
                      f"MIN_EMIT ({MIN_EMIT} normalised chars) — skipped by design, no worklist row.")
    report += ["", "## Flag digest (why pairs were held back)", "", "| flag | count | meaning |", "|---|---|---|"]
    for fl, n in fc.most_common():
        report.append(f"| `{fl}` | {n} | {MEAN.get(fl, '')} |")
    report.append("")
    for fl in ("digit-mismatch", "contains-other-label", "is-other-label", "glued-short-label", "ends-with-other-label"):
        if samples.get(fl):
            report.append(f"### `{fl}` samples")
            for code, key, en, tr in samples[fl]:
                report.append(f"- **{code} {key}** — EN: “{en}” → “{tr}”")
            report.append("")
    path = out_dir / "QA-REPORT.md"
    path.write_text("\n".join(report), encoding="utf-8")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="folder holding the bilingual PDFs")
    ap.add_argument("--instrument", required=True, help="F1 | F3 | F4 (filename prefix)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--dcf", help="a WRITTEN .dcf to anchor on (F1/F4)")
    src.add_argument("--generator", help="anchor on this instrument's PRE-APPLY generator dictionary (F3)")
    ap.add_argument("--out", required=True, help="output folder (gitignored)")
    ap.add_argument("--locales", default=",".join(c for _, c in LANGS),
                    help="comma list of locale codes, default all seven")
    ap.add_argument("--live-maps", help="<inst>/translations dir — print differ-from-live per locale")
    a = ap.parse_args(argv)
    want = {c.strip().upper() for c in a.locales.split(",") if c.strip()}
    anchors = generator_anchors(a.generator) if a.generator else dcf_anchors(a.dcf)
    bad = [k for k in anchors if ":" not in k]
    print(f"{a.instrument}: {len(anchors)} anchors from {a.generator or a.dcf}; keys not in dcf: {bad[:5]}")
    if bad:
        return 1
    results = {}
    print("%-4s %8s %8s %8s %8s  %s" % ("loc", "anchored", "clean", "flagged", "differ", "file"))
    for paper, code in LANGS:
        if code not in want:
            continue
        pdf = find_paper(a.source, a.instrument, paper)
        if pdf is None:
            results[code] = None
            print("%-4s %8s %8s %8s %8s  %s" % (code, "-", "-", "-", "-", "no paper file"))
            continue
        r = extract(pdf, anchors)
        results[code] = r
        dl = differ_from_live(r["clean"], os.path.join(a.live_maps, f"{code.lower()}.json")) if a.live_maps else None
        print("%-4s %8d %8d %8d %8s  %s" % (code, r["anchored"], len(r["clean"]), len(r["flagged"]),
                                           dl["differ"] if dl else "-", r["file"]))
    print("wrote", write_outputs(results, a.out, a.instrument, a.live_maps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
