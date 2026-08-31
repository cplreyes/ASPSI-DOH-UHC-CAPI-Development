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

---

## Applying this reference to the tool (added 2026-08-14)

The warning above — *"treat this as the reference to check against and copy from, with a
diff reviewed before anything reaches a deployed instrument"* — was tested and proved right.
A bulk pass proposed 1,680 repairs; an adversarial audit (13 reviewers) rejected **850 of
the 1,245 question stems, 68%**. The failures were not stylistic:

| class | what went wrong |
|---|---|
| sub-field targets | roster cells, amount boxes, Month/Year/Hours/Minutes, auto-computed totals and Other-(Specify) text boxes all inherit a label starting with the parent question's number, so they were captioned with the whole question |
| merged questions | one proposal carrying two questions, a section heading, or roster column headers |
| shared text | one text written to several genuinely different sibling questions (worst: the F3 115.1/115.2 blocks) |
| surviving directives | an enumerator directive left in the stem, which now double-prints against the notes layer |
| English debris | the tail of the English question left in front of the translation |
| destructive values | `Medical Officer` → `/`; an option → `(`; a trim that cut the `DO` of `DOH` |

### What changed

**`stem_validator.py`** — a structural gate every proposal must pass. The posture is
**precision over recall**: a translation ships only if it can be *proven* clean, and
anything else is left on English fallback, which is the documented behaviour for a missing
translation and is always safe. A smaller provably-correct set beats a larger plausible one.

`fix_translations.py` now runs every stem through `validate()` and every option through
`validate_option()`, drops any text claimed by two questions, and delegates directive
detection to the validator.

**One real bug was fixed in directive detection.** The old rule required a caps run to
*begin* with a directive word, so an acronym sitting in front hid the directive completely:

```
"... ng zero balance billing (ZBB) READ OPTIONS OUT LOUD, SELECT ALL THAT APPLY"
                              ^ run starts here, "(ZBB)" is not an opener -> missed
```

The rule now scans for the opener directly and requires three consecutive caps words *from*
it — which still refuses to fire on an acronym list (`MAIFIP, DSWD, PCSO`), the false
positive that destroys real content. Fixing this also surfaced doubled directives that had
been invisible.

### Effect

| | proposed | after validation |
|---|---|---|
| stems | 1,245 | **300** |
| options | 67 | **6** |
| trims | 368 | **5** (the rest already shipped) |

A re-audit of the validated set put the stem reject rate at roughly **4%**, down from 68%.

### The recall that is deliberately given up

Of ~2,160 skipped stems, **1,852 are sub-fields** — never legitimate targets, so not a loss
at all. The genuine gaps are ~125 questions with no cleared translation (ASPSI content, not
recoverable here), plus smaller buckets rejected for binding, English debris or ambiguity.
Those stay English on purpose.

### Still true

Everything in "Known limitations" above still applies to the *raw* extraction. The validator
does not clean the PDFs; it refuses what they got wrong. `option_confidence: "positional"`
is still never applied, and an empty entry still means "could not split safely", not "no
translation exists".

---

## Cleaning what was already stored (#1279, 2026-08-15)

The validator above stops bad text being **written**. It never looked at what was **already
in the maps**, so defects that predate it kept reaching respondents. Byte-checking the
deployed builds found them:

```
F3 Q147 [CEB]  "PLEASE LIST DOWN ALL MEDICINES THAT YOU TOOK FOR THE HEALTH CONDITION"
F4 Q36  [HIL]  "... ang klase sang disabilidad? 0-No 1-Yes 0Indi 1-Oo"
F3 Q30  [CEB]  "DO NOT READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY. Ang pasyente ba
                miyembro sa Indigenous People (IP) community ..."
F1 Q54  [ILO]  "... ti kangrunaan a kangrunaan a mangipapaay ..."   ("the main main provider")
```

`clean_existing.py` removes those spans and keeps the surviving translation. A key is
removed only when nothing survives — and **removal, not an empty string**, is what makes
`apply_translations` fall back to English; an empty value renders blank.

### Four mistakes worth remembering

The first version proposed 94 trims and **163 key removals**. Almost all of those removals
were wrong, for reasons that are easy to repeat:

1. **A directive usually LEADS the value.** Cutting at the first marker and keeping the head
   discarded the whole translation. `DIRECTIVE_PHRASE` also matches only the first words, so
   cutting at `READ OPTIONS` left `OUT LOUD. SELECT ALL THAT APPLY. Ano sa mga masunod ...`
   behind. Fix: remove **every** marker span and keep the residue.
2. **Brackets are not always notes.** Filipino wraps ordinary translations in `[...]` and
   Ilocano in `(...)` — an editorial convention this README already documented. Treating
   every bracket as a routing note deleted correct labels like
   `[Inirekomenda ng kaibigan/pamilya]` outright. A bracket is a note only when it *reads*
   like one; otherwise it is unwrapped.
3. **Option labels are not questions.** A minimum-length rule and a "must end in sentence
   punctuation" rule are right for a question stem and wrong for a value-set label, which is
   often one or two words with no punctuation. Applying both to everything threw away 83
   good Filipino option labels. The rules are now scoped by key type.
4. **An ALL-CAPS directive does not always run to the end of the string.** Assuming it did
   was only true for trailing directives.

### The audit, and what it gave back

10 reviewers audited the 261-change diff. Their most valuable output was not the rejections
but the **recoveries**: for most drops they judged needless, a reviewer supplied the exact
translation that should have been kept.

That text is **not taken on faith**. `apply_1279.py` accepts a reviewer's replacement only
if it is a pure **deletion** of the stored value — every word present, in the same order.
A paraphrase, a spelling correction or an invented phrase cannot pass, which keeps the same
guarantee the rest of the pipeline gives: nothing is composed, only removed.

---

## Aug-21 extractor (added 2026-08-25)

- `python anchor_extract.py --source raw/Survey-Instruments-2026-08-21/Translations
  --instrument F1 --dcf deliverables/CSPro/F1/FacilityHeadSurvey.dcf --out out-aug21/F1
  [--locales FIL,BCL] [--live-maps deliverables/CSPro/F1/translations]` — for **F3** use
  `--generator F3` instead of `--dcf` (the pre-apply generator dictionary, never the
  written `PatientSurvey.dcf`, which is post-`#714` neutralisation).
- Writes `out-aug21/<INST>/<loc>.json` (**name-scoped** `item:`/`vs:`/`val:` keys, flat, no
  `_meta`), `<loc>_flagged.json` (translator worklist) and `QA-REPORT.md`. All gitignored.
- Anchors on the **BUILD's English** — align the English first
  (`aug21_english_delta.py`), or an anchor simply never matches the paper. Container
  labels (`dict:`/`level:`/`record:`) are not anchored; `— Hours` / `— Minutes` component
  suffixes are stripped so the split HH/MM items anchor on the bare stem.
- Adds two flags to the June-5 set (which is otherwise untouched, calibrated against 28
  papers): `glued-short-label` (a 4-9 char option label glued inside the span — the
  2026-08-17 live spill class) and `ends-with-other-label` (grid furniture swept in).
- The extractor is read-only against the build: only `apply_aug21.py` ever writes into
  `F<n>/translations/`.
