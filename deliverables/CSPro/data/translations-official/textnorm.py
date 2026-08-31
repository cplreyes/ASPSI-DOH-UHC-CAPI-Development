#!/usr/bin/env python3
"""textnorm.py — the text-normalisation functions shared across the Aug-21
translation import tooling.

Extracted (Task 0, 2026-08-25) so aug21_english_delta.py and anchor_extract.py
(Task 1) normalise build vs. paper text the SAME way — smart quotes, bracketed
fill placeholders, and casing/punctuation all fold identically on both sides of
every comparison, otherwise the two tools would silently disagree on what
counts as a match.

Fix round 1 (2026-08-25, finding 3): a MID-sentence bracket
(``Is [facility_name] the facility...``) is a template fill placeholder — the
build and the paper spell the same fill with different tokens
(``[facility_name_input]`` vs ``[facility_name]``), so folding both away is
correct normalisation. A LEADING bracket (``[Answer only "yes" in Q112] After
you went...``) is a real interviewer instruction that the build may not carry
anywhere — stripping it away made the build's plain question text falsely
equal the paper's instruction-plus-question text, hiding a genuine content gap
(verified against F4 Q117/131/135, whose build text has no such instruction at
all). So only a bracket with non-whitespace text before it is stripped; a
leading bracket is left as literal words, which will fail to prefix-match a
build stem that lacks them, correctly surfacing the diff.
"""
import re


def norm(s):
    """Fold a label to a comparable stem: curly quotes -> straight, a
    MID-sentence bracketed fill (``[facility_name_input]``) stripped, a
    LEADING bracketed instruction (``[Answer only ...]``) left as literal
    words, then lower-cased with punctuation collapsed to single spaces."""
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"(?<=\S)\s*\[[^\]]{0,80}\]", " ", s)  # mid-sentence [facility_name_input] only
    return " ".join(re.sub(r"[^a-z0-9' ]", " ", s.lower()).split())


def norm_for_match(s):
    """Fold a label to the projection anchor_extract.py searches the PAPER in.

    Task 1 (2026-08-25) moved this here verbatim from the June-5 tool
    (deliverables/CSPro/translations-paper-extract/anchor_extract.py) so the
    anchoring projection is defined once. It is deliberately NOT `norm()`:

      * it keeps every Unicode alnum, so ``Biñan`` stays one token — `norm()`
        would fold ``ñ`` to a space and split the word;
      * it drops the apostrophe to a space, so ``Doctor's Professional Fee``
        folds the same way the PDF-text projection folds it — `norm()` keeps
        the apostrophe as a character, which no paper projection ever
        produces, and the anchor could never be found;
      * it leaves brackets as literal words, because a paper anchor must match
        the paper's own characters, not a comparison stem.

    It MUST stay the exact character-for-character twin of
    anchor_extract.build_norm()'s projection (which additionally returns the
    norm-index -> original-index map); test_anchor_extract.py asserts that.
    `norm()` stays the build-vs-paper COMPARISON stem used by
    aug21_english_delta.py. Two jobs, two functions, one home.
    """
    out, prev = [], True
    for c in s.lower().replace("’", "'").replace("‘", "'"):
        if c.isalnum():
            out.append(c); prev = False
        elif not prev:
            out.append(" "); prev = True
    return "".join(out).strip()
