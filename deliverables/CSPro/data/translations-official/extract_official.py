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
            stats.append((code, "MISSING PDF", 0, 0, 0))
            continue
        raw_text = page_text(p)
        with io.open(os.path.join(TEXT_DIR, f"{instrument}_{code}.txt"), "w",
                     encoding="utf-8") as fh:
            fh.write(raw_text)

        blocks = split_questions(raw_text)
        bilingual = is_bilingual(en_parsed, blocks)
        got = unsplit = opts_got = 0
        for n, (en_stem, en_opts) in en_parsed.items():
            if n not in blocks:
                continue
            bi_stem, bi_opts = parse_block(blocks[n])
            if bilingual:
                tr_stem = strip_english(bi_stem, en_stem)
                tr_opts = pair_options(en_opts, bi_opts)
                opt_conf = "matched"        # each option paired on its own English text
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
                      got, unsplit, opts_got))

    print(f"\n[{instrument}] {len(en_parsed)} numbered questions in the English source")
    print(f"  {'locale':<7}{'stems':>8}{'unsplit':>9}{'options':>9}  layout")
    for code, state, got, unsplit, oc in stats:
        if state == "MISSING PDF":
            print(f"  {code:<7}{state:>26}")
        else:
            flag = "" if state == "bilingual" else "   <-- different from its siblings"
            print(f"  {code:<7}{got:>8}{unsplit:>9}{oc:>9}  {state}{flag}")
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
