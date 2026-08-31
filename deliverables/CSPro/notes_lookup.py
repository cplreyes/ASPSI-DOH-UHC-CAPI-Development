#!/usr/bin/env python3
r"""Per-locale text for section intros and enumerator directives.

WHY THIS EXISTS
---------------
Section intros and enumerator directives live as hardcoded ENGLISH constants in each
generate_qsf.py, and question_extras() resolved them ONCE per item - outside the
per-language loop - so the same English string was pasted into every locale's question
text. 299 question screens across F1/F3/F4 therefore showed English no matter which
language the enumerator picked (2,093 renderings over seven locales). They never enter the
.dcf, so the dictionary translation pipeline could not reach them either. Tickets #1216,
#1219, #1220, #1223, #1224 and #1225 are all this single defect.

The translations come from the DOH-cleared June-5 questionnaires, extracted verbatim by
data/translations-official/extract_notes.py. Lookup is by the FULL English string, the
same convention apply_translations uses for dictionary labels, so a reworded English note
falls back to English rather than silently showing the wrong text.

Verified against ground truth: the Bicolano values this returns for F1 intro 1 and intro 7
match, character for character, the wording testers supplied independently on #1216 and
#1219.
"""
import json
from pathlib import Path

_NOTES_PATH = (Path(__file__).parent / "data" / "translations-official" / "notes.json")
_BY_ENGLISH = None


def _canon(s):
    """Whitespace-, quote- AND dash-normalized key. generate_qsf authors curly quotes
    (facility’s, “I don't know”) while the extracted notes store straight ones -
    an exact-string lookup missed on that alone and silently fell back to English
    (#1235/#1256, the #1213 orphan class in the notes layer).

    Dashes and NBSP fold for the same reason, and this line MUST stay in step with
    data/translations-official/extract_notes.py norm(), which flattens en/em dashes and
    NBSP BEFORE it keys a note. F4 SECTION_INTROS[144] (the household-consumption intro)
    is authored with two em-dashes, so it was stored under a hyphen-keyed entry this
    function never produced: six locales’ cleared text sat in notes.json unreachable and
    the longest intro in F4 rendered English everywhere. Swept F1/F3/F4 - it is the only
    dash-bearing note today, but the two normalizers diverging is the real defect.
    """
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("\xa0", " ")
    return " ".join(s.split())


def _load():
    """-> {english_note: {locale: translation}}, keyed like apply_translations."""
    global _BY_ENGLISH
    if _BY_ENGLISH is not None:
        return _BY_ENGLISH
    _BY_ENGLISH = {}
    if not _NOTES_PATH.exists():
        return _BY_ENGLISH
    raw = json.loads(_NOTES_PATH.read_text(encoding="utf-8"))
    for _inst, block in raw.items():
        english = block.get("english", {})
        for key, per_lang in block.get("translations", {}).items():
            en = english.get(key)
            if not en:
                continue
            slot = _BY_ENGLISH.setdefault(_canon(en), {})
            for lg, txt in per_lang.items():
                # First writer wins: the same note recurs across instruments and the
                # values agree; a later blank must never clear an earlier good one.
                if txt and lg not in slot:
                    slot[lg] = txt
    return _BY_ENGLISH


def translate_note(english, lang):
    """Cleared translation of a note, or the English itself when none is available.

    English fallback is the current on-tablet behaviour, so a miss is never a regression.
    """
    if not english or lang in (None, "", "EN"):
        return english
    return _load().get(_canon(english), {}).get(lang, english)


def coverage():
    """-> {locale: n} translated notes available, for build-time reporting."""
    out = {}
    for per_lang in _load().values():
        for lg in per_lang:
            out[lg] = out.get(lg, 0) + 1
    return out
