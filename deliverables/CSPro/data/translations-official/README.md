# Official translations — DOH Deliverable 2 (June 5 questionnaires)

**This is the authoritative reference for every non-English string in the CAPI.**
Source: `raw/DOH-Deliverable-2-2026-07-31/Data collection tools/` — 32 PDFs, 8 languages
× 4 instruments, all dated **June5**. That is the set SJREB cleared, and the one the CAPI
build footer already cites as *Translated Questionnaire ver. 06/05/2026*.

Nothing in this folder is authored. Every string is lifted from those PDFs as written.
Where a translation could not be separated from its English safely, the entry is left
**empty** rather than guessed.

## Contents

| path | what it is |
|---|---|
| `extract_official.py` | the extractor — run it to rebuild everything below |
| `text/<INSTRUMENT>_<LOCALE>.txt` | verbatim text dump of each PDF, 32 files, no interpretation |
| `official_translations.json` | structured: question number → per-locale stem + options |

Rebuild with `python extract_official.py` (needs PyMuPDF). `--probe F3` reports one
instrument only.

## How the PDFs are actually laid out

**27 of the 28 translated PDFs are bilingual** — the English line appears inline,
immediately followed by the translation, in the same table cell:

```
7. What is your sex at birth? Ano ang sekswalidad sang pasiente sang pagkabata?
[] Male Lalaki
[] Female Babaye
```

So a translation cannot be read off directly; it is recovered by **difference** against
the English-only PDF — locate the known English, keep the remainder.

**`Waray_F4` is the exception: it is monolingual Waray**, with English inline in ~1% of
blocks against 53–78% for every sibling. The extractor detects layout per file rather
than assuming one. Worth raising with ASPSI — that file is formatted unlike the other 31.

## Question number is the join key

Both the English and translated PDFs carry the same numbering (F3: 190 numbered tokens,
max 178, in every language). Number — not English sentence text — is what links a
translation to a question.

This matters beyond this folder. The CAPI's `apply_translations()` matches on the **full
English label text**, so any rewording of an English question silently orphans its
translation and the tool falls back to English with no error. That is the root cause
behind #1182, #1213, and a large share of the current coverage gap. Keying on question
number (or item name + value code) is the durable fix.

## Known limitations — read before using this to patch the tool

The extraction is a sound **reference**. It is *not* yet safe to apply wholesale:

1. **English residue in some stems.** Enumerator directives (`READ OPTIONS OUT LOUD`,
   `SELECT ALL THAT APPLY`, `<proceed to Q10>`) often survive the split because the
   source repeats them only once, in English.
2. **Bleed across question boundaries.** A few stems pick up the tail of the previous
   question where the PDF's text order does not match its visual order.
3. **Bracket conventions.** Filipino wraps some translations in `[...]`, Ilocano in
   `(...)`. Those are the PDF's editorial marks, not part of the translated string, and
   are deliberately left in rather than stripped on a guess.
4. **Options carry a confidence flag.** `option_confidence: "matched"` means the option
   was paired on its own English text — reliable. `"positional"` means index pairing was
   the only option (monolingual file) and the pairing is *unverified*. Never apply a
   `positional` option without eyeballing it: the translated PDFs do not always list
   options in the English order (F3 Q92 — English slot 5 is "Free, charge to HMO" while
   Filipino slot 5 is the PhilHealth row), so binding by position can attach a
   translation to the **wrong option code**, which is worse than leaving it in English.
5. **Some entries are legitimately English.** Acronyms and programme names (GAMOT,
   PhilHealth, HMO) appear untranslated in the source itself. An empty result means
   "could not split safely", not "no translation exists" — the two are not
   distinguished automatically.

Because of 1–4, treat this as the reference to **check against and copy from**, with a
diff reviewed before anything reaches a deployed instrument. A bulk apply on a plausible
heuristic is exactly what corrupted 25 locale values on 2026-08-12.
