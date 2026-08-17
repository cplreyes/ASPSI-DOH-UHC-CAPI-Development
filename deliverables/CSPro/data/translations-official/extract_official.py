#!/usr/bin/env python3
r"""Extract the DOH-cleared translated questionnaires VERBATIM into machine-readable form.

SOURCE OF TRUTH
---------------
raw/DOH-Deliverable-2-2026-07-31/Data collection tools/ - 32 PDFs, 8 languages x 4
instruments, all dated June5. This is the set SJREB cleared, and the one the CAPI footer
already cites as "Translated Questionnaire ver. 06/05/2026". Nothing here is authored:
every string is lifted from those PDFs exactly as written.

WHAT THE PDFS LOOK LIKE
-----------------------
The translated PDFs are BILINGUAL - each question shows the English line immediately
followed by the translation, in the same table cell:

    7. What is your sex at birth? Ano ang sekswalidad sang pasiente sang pagkabata?
    [] Male Lalaki
    [] Female Babaye

So the translation cannot simply be read off; it has to be separated from the English it
is glued to. That is done by DIFFERENCE against the English-only PDF: locate the known
English inside the bilingual block and keep the remainder. This stays verbatim - we never
compose or tidy a translated string, we only cut the English away from it. Where the two
cannot be separated safely the entry is left EMPTY rather than guessed.

Question NUMBER is the join key across languages (verified: English and Hiligaynon F3
both yield 190 numbered tokens, max 178). That is also the durable key the CAPI should
have used from the start - matching on full English text is what silently orphans a
translation whenever the English is reworded.

raw/ lives only in the main checkout, so SRC points there even when this runs from a
worktree. Outputs land next to this script.

Run:
    python extract_official.py             # writes text/ + official_translations.json
    python extract_official.py --probe F3  # alignment stats for one instrument only
"""
import io
import json
import os
import re
import sys
from collections import OrderedDict

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
# .../<repo>/deliverables/CSPro/data/translations-official  (repo may be a worktree)
_repo = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
_marker = os.path.join(".claude", "worktrees")
MAIN = _repo.split(_marker)[0].rstrip("\\/") if _marker in _repo else _repo
if _marker in _repo:                       # .../<main>/.claude/worktrees/<name>
    MAIN = os.path.dirname(os.path.dirname(os.path.dirname(_repo)))
SRC = os.path.join(MAIN, "raw", "DOH-Deliverable-2-2026-07-31", "Data collection tools")
TEXT_DIR = os.path.join(HERE, "text")
OUT_JSON = os.path.join(HERE, "official_translations.json")

# PDF language word -> CAPI locale code. "Tagalog" is the CAPI's FIL; Bisaya and Cebuano
# stay distinct because ASPSI supplies (and the tool declares) both.
LANGS = OrderedDict([
    ("English", "EN"), ("Tagalog", "FIL"), ("Bicolano", "BCL"), ("Bisaya", "BIS"),
    ("Cebuano", "CEB"), ("Hiligaynon", "HIL"), ("Ilocano", "ILO"), ("Waray", "WAR"),
])
INSTRUMENTS = ["F1", "F2", "F3", "F4"]

Q_START = re.compile(r"(?m)^\s*(\d{1,3}(?:\.\d)?)\s*\.?\s+(?=\S)")
OPTION = re.compile(r"[☐☑☒□]\s*")   # ballot / empty-box glyphs

# Running page furniture. PyMuPDF returns it inline, so without this it gets glued into
# whatever option happens to straddle a page break (seen: WAR F3 Q112 option 2 came out
# as "ICF ver.07/25/2026 | Translated Questionnaire ver.06/05/2026 Libre/ waray bayad").
FURNITURE = re.compile(
    r"(ICF\s*ver\.?\s*[\d/]+|Translated\s+Questionnaire\s+ver\.?\s*[\d/]+"
    r"|PSA\s+SSRCS[^\n|]*|Page\s+\d+\s*(of\s*\d+)?)", re.I)

# Routing tokens welded onto answer labels by the PDF layout - "Dai <magproceed sa Q15>",
# "<padayon sa Q83?", "<Katapusan sa survey>", "<proceed to Q43>". They are skip logic,
# never respondent-facing wording, and the per-locale audit found this ONE pattern
# accounts for roughly half of all corrupted extractions (~188 of 375 classes). The
# closing form varies because the PDFs contain broken brackets, so accept ">", "?" or
# ")" as the terminator.
ROUTING = re.compile(r"<[^<>]{0,80}?[>?)]")
# PDF line-break hyphenation: "kamag- anak" -> "kamaganak", "in- admit" -> "inadmit".
# A genuine compound has no space after the hyphen ("Tech-Voc"), so this is unambiguous.
HYPHEN_SPLIT = re.compile(r"(\w)-\s+(\w)")


def find_pdf(lang_word, instrument):
    """Filenames are inconsistent (spaces vs hyphens, a stray 'Ilocano_ F1'), so match on
    the language prefix + instrument token rather than an exact name."""
    want = lang_word.lower()
    for fn in sorted(os.listdir(SRC)):
        low = fn.lower()
        if not low.endswith(".pdf") or not low.startswith(want):
            continue
        if re.search(rf"[_\- ]{instrument.lower()}[_\- ]", low):
            return os.path.join(SRC, fn)
    return None


def page_text(path):
    doc = fitz.open(path)
    try:
        return "\n".join(p.get_text() for p in doc)
    finally:
        doc.close()


def normalise(s):
    """Collapse whitespace and unify the quote/dash characters Word scatters through the
    PDFs, so the English can be located inside a bilingual block reliably."""
    s = (s.replace("’", "'").replace("‘", "'")
          .replace("“", '"').replace("”", '"')
          .replace("–", "-").replace("—", "-").replace("\xa0", " "))
    s = FURNITURE.sub(" ", s)
    s = ROUTING.sub(" ", s)
    s = HYPHEN_SPLIT.sub(r"\1\2", s)
    return re.sub(r"\s+", " ", s).strip(" |")


def unwrap(s):
    """Strip the source's editorial wrapper so a string is fit to reuse.

    Every Ilocano value is parenthesised ("(Kurang ti panagsanay)") and Filipino uses
    square brackets in places ("[Kaibigan/Pamilya]"). Those mark "this is the
    translation"; they are not part of the sentence, and pasting them would print literal
    brackets in a value set. Only unwraps when the brackets enclose the WHOLE string and
    are balanced inside, so parenthetical asides survive untouched.
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


def split_questions(text):
    """-> OrderedDict qnum -> raw block text for the QUESTIONNAIRE BODY.

    A number can appear several times in one document: a cover/field-control table uses
    1-6 BEFORE the body, and F1's secondary-data annex reuses 1-6 AFTER it. Neither
    "first wins" nor "last wins" is right - first-wins takes F3's cover block, last-wins
    takes F1's annex (which is how F1 Q1 came to be matched against "B. Patient Load for
    the past 6 months").

    A longest-increasing-subsequence over all marks does NOT work: it happily weaves
    through the cover table on its way up, which mapped F1 Q1 to the result-code list
    ("Completed"). The body is instead the one run that REACHES THE HIGHEST number, so
    anchor on the last occurrence of the maximum and walk backwards, taking for each
    lower number its latest occurrence that still precedes the one already chosen. Cover
    and annex occurrences sit outside that chain and are dropped.
    """
    marks = [(m.group(1), m.start(), m.end()) for m in Q_START.finditer(text)]
    if not marks:
        return OrderedDict()

    by_num = {}
    for i, (n, _, _) in enumerate(marks):
        by_num.setdefault(float(n), []).append(i)

    nums_desc = sorted(by_num, reverse=True)
    keep = set()
    limit = len(marks)                     # index ceiling: chosen marks must precede this
    for n in nums_desc:
        cands = [i for i in by_num[n] if i < limit]
        if not cands:
            continue                       # number absent from the body run
        pick = max(cands)
        keep.add(pick)
        limit = pick

    out = OrderedDict()
    for i, (num, s, e) in enumerate(marks):
        if i not in keep:
            continue
        end = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        block = text[e:end]
        if len(block.strip()) >= 3:
            out[num] = block
    return out


def parse_block(block):
    """-> (stem, [options]) for one question block."""
    parts = OPTION.split(block)
    return normalise(parts[0]), [o for o in (normalise(p) for p in parts[1:]) if o]


def strip_english(bilingual, english):
    """Remove the English portion from a bilingual string, verbatim-safely.

    Returns the remainder (the translation), or "" when the two are effectively the same
    string - which legitimately happens where the source PDF left an item in English
    (acronyms, programme names, numeric answers). Never invents or reorders words.
    """
    b, e = normalise(bilingual), normalise(english)
    if not e or not b or b == e:
        return ""
    i = b.lower().find(e.lower())
    if i >= 0:
        return re.sub(r"\s+", " ", (b[:i] + " " + b[i + len(e):])).strip()
    # English not present as one run (a line break split it): drop the longest leading
    # run of matching words, and only trust it if it is a real prefix.
    ew, bw = e.split(), b.split()
    k = 0
    while k < len(ew) and k < len(bw) and ew[k].lower() == bw[k].lower():
        k += 1
    return " ".join(bw[k:]).strip() if k >= 3 else ""


def is_bilingual(en_parsed, blocks):
    """Do the translated blocks repeat their English inline?

    Nearly all of them do; F4 Waray does not - it is a Waray-only document. Difference-
    against-English silently yields nothing for such a file, so detect the layout instead
    of assuming one. Worth reporting to ASPSI: that file is formatted unlike its siblings.

    The test must be the SAME operation extraction performs - "does strip_english get a
    result?" - not the stricter "is the full English stem a literal substring?". The
    strict form reports F1 as monolingual even though strip_english succeeds on 161/167
    of its blocks (line breaks split the English, which strip_english tolerates and a
    substring test does not). Treating a bilingual file as monolingual would copy the
    English INTO the translation - precisely the corruption this whole exercise is
    meant to undo - so the detector is deliberately aligned with the extractor.
    """
    ok = checked = 0
    for n, (en_stem, _) in en_parsed.items():
        if n not in blocks or len(en_stem) < 25:
            continue
        checked += 1
        if strip_english(parse_block(blocks[n])[0], en_stem):
            ok += 1
    return bool(checked) and (ok / checked) > 0.40


def pair_options(en_opts, bi_opts):
    """Pair each English option with the bilingual option that CONTAINS it.

    Index pairing is WRONG here: the translated PDFs do not always list options in the
    English order (F3 Q92 - English slot 5 is "Free, charge to HMO" while Filipino slot 5
    is the PhilHealth row). Pairing by position would bind a translation to the wrong
    option CODE, which is worse than leaving it in English, so match on content instead.
    Longest English first, so "Free, charge to PhilHealth" claims its row before "Free".
    An option that finds no container is left empty rather than guessed.
    """
    out = [""] * len(en_opts)
    norm_bi = [normalise(b).lower() for b in bi_opts]
    used = set()
    for i in sorted(range(len(en_opts)), key=lambda k: -len(en_opts[k])):
        e = normalise(en_opts[i]).lower()
        if not e:
            continue
        for j, nb in enumerate(norm_bi):
            if j in used or not nb:
                continue
            if e in nb:
                out[i] = strip_english(bi_opts[j], en_opts[i])
                used.add(j)
                break
    return out


# ---------------------------------------------------------------------------
# RECOVERY PASS
# ---------------------------------------------------------------------------
# The pairing above requires the whole English option to sit inside the bilingual block as
# ONE contiguous run. Three properties of the PDFs break that, and between them they left
# thousands of cells empty even though the translation was present:
#
#   1. LONG EDITORIAL NOTES. ROUTING strips "<...>" notes but caps them at 80 characters.
#      The licensing notes run to 93:
#          <This is a licensing requirement only for hospitals. Not applicable to primary
#           care facilities>
#      so the note survives on both sides - and since the translated PDF puts the
#      translation BETWEEN the option and its note, the English is no longer contiguous.
#   2. INTERLEAVING. Where the PDF alternates English/translation more than once inside one
#      option or stem, no single run covers the English. "Why not? Ngata ta dai? DO NOT
#      READ OPTIONS OUT LOUD." is the English stem wrapped around its own translation.
#   3. SPACE LOSS AT LINE WRAP. The bilingual PDFs lose spaces where a line breaks, so the
#      English embedded in a translated block is not textually the English from the
#      English-only PDF: "promotionactivities", "collaboratingand", "programcoordinators".
#
# This pass runs AFTER the normal one and only ever fills a cell the normal one left EMPTY.
# It cannot change or remove an existing value, so the worst case of a bad rule here is
# that a cell stays English - which is the current behaviour and always safe.
#
# The verbatim guarantee is unchanged. A match is located in a whitespace-free projection
# of the string, mapped back to a span of the ORIGINAL, and that span is DELETED. Output is
# always a subsequence of the source block; nothing is composed, reordered or corrected.

MIN_RUN = 3                      # words; below this, borrowed English is indistinguishable
WIDE_ROUTING = re.compile(r"<[^<>]{0,400}?[>?)]")
EXCLUSIONS_JSON = os.path.join(HERE, "recovery_exclusions.json")


def _load_exclusions():
    """Cells adversarial review threw out. Keyed INSTRUMENT|LOCALE|QNUM|OPTION_INDEX.

    The gate below is mechanical and cannot see everything: a value can be verbatim,
    balanced and the right length and still be bound to the wrong option, carry a
    neighbouring row's English, or be a locale's text sitting under another locale's
    heading. Those were found by reading the PDFs and are listed here so that
    regenerating can never quietly put one back.
    """
    try:
        with io.open(EXCLUSIONS_JSON, encoding="utf-8") as fh:
            return set(json.load(fh).get("exclusions", {}))
    except (OSError, ValueError):
        return set()


EXCLUDED = _load_exclusions()


def _compress(s):
    """-> (whitespace-free lowercase projection, map from projected index -> index in s)"""
    buf, idx = [], []
    for i, ch in enumerate(s):
        if ch.isspace():
            continue
        buf.append(ch.lower())
        idx.append(i)
    return "".join(buf), idx


def _delete_run(hay, needle):
    """Delete the first occurrence of `needle` from `hay`, ignoring whitespace."""
    if not needle.strip():
        return hay
    ch, cmap = _compress(hay)
    cn, _ = _compress(needle)
    if not cn:
        return hay
    p = ch.find(cn)
    if p < 0:
        return hay
    return hay[:cmap[p]] + " " + hay[cmap[p + len(cn) - 1] + 1:]


def _norm_wide(s):
    """normalise() with the wider routing strip, so long <editorial notes> go too.

    Only the recovery pass uses this. normalise() itself is left exactly as it was, so the
    baseline values this pass builds on are bit-for-bit unchanged.
    """
    global ROUTING
    keep = ROUTING
    ROUTING = WIDE_ROUTING
    try:
        return normalise(s)
    finally:
        ROUTING = keep


def cut_english_multi(bilingual, english, anchor_prefix=False):
    """Delete EVERY run of the English from the bilingual block. Deletion only."""
    b, e = _norm_wide(bilingual), _norm_wide(english)
    if not e or not b or _compress(b)[0] == _compress(e)[0]:
        return ""                       # source repeated the English: no translation here
    ew = e.split()
    out = _delete_run(b, e)             # the whole thing first, at any length
    if _compress(out)[0] != _compress(b)[0]:
        # The whole English was there and is now gone. STOP - decomposing further would
        # start deleting the English the TRANSLATION legitimately borrows. Q137's Bikol is
        # "Kulang an PhilHealth support value"; carrying on and cutting the 3-word run
        # "PhilHealth support value" a second time reduced it to "Kulang an".
        pass
    else:
        runs = []
        for s in range(len(ew)):
            for t in range(len(ew), s + MIN_RUN - 1, -1):
                runs.append(" ".join(ew[s:t]))
        runs.sort(key=len, reverse=True)
        for r in runs:
            if len(r.split()) >= MIN_RUN:
                out = _delete_run(out, r)
    if anchor_prefix:
        # A short English stem never reaches the MIN_RUN floor - "Why not?" is two words,
        # so the English line survived in front of its own translation. Delete the longest
        # leading run of the English that the remainder still STARTS with. Anchored at the
        # start and matched against the English's own opening words, so it cannot bite into
        # a translation that merely borrows English further in.
        for k in range(min(8, len(ew)), 0, -1):
            pref = _compress(" ".join(ew[:k]))[0]
            if pref and _compress(out)[0].startswith(pref):
                out = _delete_run(out, " ".join(ew[:k]))
                break
    return re.sub(r"\s+", " ", out).strip(" |,;:.-")


def recovery_ok(cand, english, siblings=()):
    """-> (accept, reason). Precision over recall: withhold anything questionable.

    A withheld cell falls back to English, which is safe and is what happens today. A
    wrongly accepted one puts wording in front of a respondent that the DOH never cleared.
    """
    c = (cand or "").strip()
    if not c:
        return False, "empty"
    ce = _compress(c)[0]
    en = _norm_wide(english)
    ee = _compress(en)[0]
    if not ce:
        return False, "empty"
    if ce == ee:
        return False, "identical-to-english"
    # Only a surviving copy of the WHOLE English counts as contamination. These languages
    # borrow English nouns freely - "Mga laog kan emergency cart" and "Akses sa public
    # price information" are correct Bikol, and a rule keyed on any two consecutive English
    # words throws them away.
    if len(ee) >= 6 and ee in ce:
        return False, "english-residue"
    if re.search(r"[{}<>|]", c):
        return False, "pdf-artifact"
    if c.count("(") != c.count(")") or c.count("[") != c.count("]"):
        return False, "unbalanced-brackets"
    if FURNITURE.search(c):
        return False, "page-furniture"
    if re.search(r"(READ OPTIONS|SELECT ALL|SELECT ONE|DO NOT READ|PROCEED TO)", c, re.I):
        return False, "directive"
    n_c, n_e = len(ce), len(ee)
    if n_e >= 12 and not (0.25 <= n_c / n_e <= 3.5):
        return False, "length-ratio"
    # An option label is short. When parse_block lets a following section intro run on into
    # the last option, the "option" becomes a paragraph and what gets recovered is the
    # intro's translation rather than the label - F1 Q8's "Level 3 Hospital" carries the
    # whole Section B preamble, and every locale recovered the preamble.
    if len(en.split()) > 25:
        return False, "option-absorbed-intro"
    # Word-order sanity. A cut landing mid-phrase leaves a stray English token at the front
    # ("facility Kakulangan sa ...", "year Diri, waray pa ..."). There is deliberately NO
    # mirror rule on the last token: these languages often END on a borrowed English noun
    # ("Paglikom nin mga resources asin fundraising" is correct Bikol).
    punct = ".,;:()[]\"'"
    ew_low = [w.strip(punct).lower() for w in en.split()]
    cw = [w.strip(punct).lower() for w in c.split()]
    if cw and ew_low:
        first = cw[0]
        if first and first in ew_low and first not in set(ew_low[:3]):
            return False, "leading-english-out-of-order"
        if (2 <= len(first) <= 6 and first not in ew_low
                and any(t.startswith(first) and t != first for t in ew_low)):
            return False, "truncated-token"     # "Ac" out of "Act", "year" out of "years"

    # A NEIGHBOUR's English inside this value means the block held more than one option and
    # the cut kept the wrong part. F1 Q140 lists two near-identical options; the recovery
    # for the shorter one came back carrying "insufficient other sources (e.g., MAIFIP,
    # DSWD, PCSO)" - the longer one's English - and every other rule waved it through.
    for sib in siblings:
        sw = _norm_wide(sib).split()
        if len(sw) < 3:
            continue
        for i in range(len(sw) - 2):
            frag = _compress(" ".join(sw[i:i + 3]))[0]
            if len(frag) >= 9 and frag in ce and frag not in ee:
                return False, "sibling-option-english"
    return True, "ok"


def recover_options(en_opts, bi_opts, baseline):
    """-> {index: value} for cells EMPTY in baseline that can be filled safely."""
    out = {}
    used = set()
    comp_bi = [_compress(_norm_wide(b))[0] for b in bi_opts]
    for v in baseline:                  # never reuse a block a baseline value came from
        if (v or "").strip():
            cv = _compress(v)[0]
            for j, cb in enumerate(comp_bi):
                if j not in used and cv and cv in cb:
                    used.add(j)
                    break
    for i in sorted(range(len(en_opts)), key=lambda k: -len(en_opts[k])):
        if i < len(baseline) and (baseline[i] or "").strip():
            continue
        e = _norm_wide(en_opts[i])
        if not e:
            continue
        ce, ew = _compress(e)[0], e.split()
        hit = -1
        for j, cb in enumerate(comp_bi):
            if j not in used and cb and ce and ce in cb:
                hit = j
                break
        if hit < 0:                     # else the longest leading run a block still holds
            best = 0
            for j, cb in enumerate(comp_bi):
                if j in used or not cb:
                    continue
                k = len(ew)
                while k >= MIN_RUN:
                    if _compress(" ".join(ew[:k]))[0] in cb:
                        break
                    k -= 1
                if k >= MIN_RUN and k > best:
                    best, hit = k, j
        if hit < 0:
            continue
        used.add(hit)
        cand = unwrap(cut_english_multi(bi_opts[hit], en_opts[i]))
        sibs = [o for k, o in enumerate(en_opts) if k != i and o]
        ok, _ = recovery_ok(cand, en_opts[i], sibs)
        if ok:
            out[i] = cand
    return out


def build(instrument):
    en_path = find_pdf("English", instrument)
    if not en_path:
        print(f"  [{instrument}] no English PDF - skipped")
        return None
    en_parsed = {n: parse_block(b)
                 for n, b in split_questions(page_text(en_path)).items()}

    result = OrderedDict()
    for n, (stem, opts) in en_parsed.items():
        result[n] = {"EN": {"stem": stem, "options": opts}}

    os.makedirs(TEXT_DIR, exist_ok=True)
    with io.open(os.path.join(TEXT_DIR, f"{instrument}_EN.txt"), "w",
                 encoding="utf-8") as fh:
        fh.write(page_text(en_path))

    stats = []
    for lang_word, code in LANGS.items():
        if code == "EN":
            continue
        p = find_pdf(lang_word, instrument)
        if not p:
            stats.append((code, "MISSING PDF", 0, 0, 0, 0, 0))
            continue
        raw_text = page_text(p)
        with io.open(os.path.join(TEXT_DIR, f"{instrument}_{code}.txt"), "w",
                     encoding="utf-8") as fh:
            fh.write(raw_text)

        blocks = split_questions(raw_text)
        bilingual = is_bilingual(en_parsed, blocks)
        got = unsplit = opts_got = 0
        n_rec_stem = n_rec_opt = 0
        for n, (en_stem, en_opts) in en_parsed.items():
            if n not in blocks:
                continue
            bi_stem, bi_opts = parse_block(blocks[n])
            if bilingual:
                tr_stem = strip_english(bi_stem, en_stem)
                tr_opts = pair_options(en_opts, bi_opts)
                opt_conf = "matched"        # each option paired on its own English text
                # Additive recovery: fill ONLY what the pairing above left empty. Nothing
                # already extracted is looked at again, so this cannot regress a value.
                # The translated enumerator directive is deliberately left attached here -
                # extraction stays verbatim, and fix_translations does the trimming.
                if not tr_stem:
                    cand = cut_english_multi(bi_stem, en_stem, anchor_prefix=True)
                    if recovery_ok(cand, en_stem)[0]:
                        tr_stem = cand
                        n_rec_stem += 1
                for _i, _v in recover_options(en_opts, bi_opts, tr_opts).items():
                    if f"{instrument}|{code}|{n}|{_i}" in EXCLUDED:
                        continue
                    tr_opts[_i] = _v
                    n_rec_opt += 1
            else:
                # No English to cut away: the block IS the translation. Options cannot be
                # content-matched, so they fall back to positional pairing - record that
                # as lower confidence rather than passing it off as verified.
                tr_stem = normalise(bi_stem)
                tr_opts = [normalise(o) for o in bi_opts[:len(en_opts)]]
                tr_opts += [""] * (len(en_opts) - len(tr_opts))
                opt_conf = "positional"
            tr_stem = unwrap(tr_stem)
            tr_opts = [unwrap(t) for t in tr_opts]
            opts_got += sum(1 for t in tr_opts if t)
            if tr_stem:
                got += 1
            else:
                unsplit += 1
            result[n][code] = {"stem": tr_stem, "options": tr_opts,
                               "option_confidence": opt_conf}
        stats.append((code, "bilingual" if bilingual else "MONOLINGUAL",
                      got, unsplit, opts_got, n_rec_stem, n_rec_opt))

    print(f"\n[{instrument}] {len(en_parsed)} numbered questions in the English source")
    print(f"  {'locale':<7}{'stems':>8}{'unsplit':>9}{'options':>9}"
          f"{'+stems':>8}{'+opts':>7}  layout")
    for code, state, got, unsplit, oc, rs, ro in stats:
        if state == "MISSING PDF":
            print(f"  {code:<7}{state:>26}")
        else:
            flag = "" if state == "bilingual" else "   <-- different from its siblings"
            print(f"  {code:<7}{got:>8}{unsplit:>9}{oc:>9}{rs:>8}{ro:>7}  {state}{flag}")
    return result


def main():
    if "--probe" in sys.argv:
        build(sys.argv[sys.argv.index("--probe") + 1])
        return
    allout = OrderedDict()
    for inst in INSTRUMENTS:
        r = build(inst)
        if r:
            allout[inst] = r
    with io.open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(allout, fh, ensure_ascii=False, indent=1)
    print(f"\nWrote {OUT_JSON}")
    print(f"  {len(allout)} instruments, "
          f"{sum(len(v) for v in allout.values())} questions total")
    print(f"  verbatim text dumps in {TEXT_DIR}")


if __name__ == "__main__":
    main()
