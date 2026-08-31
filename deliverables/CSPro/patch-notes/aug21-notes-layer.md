# Aug-21 notes layer (section intros + enumerator directives)

**Date:** 2026-08-25 · **Tool:** `data/translations-official/extract_notes.py` · **Channel:** DEV

```
python data/translations-official/extract_notes.py \
    --source "raw/Survey-Instruments-2026-08-21/Translations" --provenance aug21 --json data/translations-official/notes.json
```

Dumped 21 PDFs (F1/F3/F4 x 7 locales) to `data/translations-official/text-aug21/` (gitignored).

## Merge result

```
[F1] 13 English notes  |  FIL 13  BCL 13  BIS 11  CEB 11  WAR 12  HIL 12  ILO 12
[F3] 25 English notes  |  FIL 24  BCL 18  BIS 23  CEB 18  WAR 23  HIL 17  ILO 20
[F4] 27 English notes  |  FIL 23  BCL 18  BIS 21  CEB 11  WAR 22  HIL 21  ILO 18
aug21 merge: written 5, replaced 0, overridden 111, kept_prior 7
```

`notes_lookup.coverage()` (translated notes available per locale):

| | FIL | BCL | BIS | CEB | WAR | HIL | ILO |
|---|---|---|---|---|---|---|---|
| BEFORE | 51 | 45 | 45 | 28 | 48 | 45 | 38 |
| AFTER  | 51 | 46 | 46 | 27 | 47 | 44 | 38 |

## What actually changed on the tablet

Coverage counts hide content changes, so the table above is not the whole story. Diffing
the June-5 and Aug-21 `notes.json` **keyed by English string** — the way `notes_lookup`
addresses a note at runtime, not by `intro:`/`const:` key — gives the honest picture:

| | count | what |
|---|---|---|
| gained | 5 | F4 GAMOT-package intro (FIL/BIS), F4 "last few sections" intro (BIS/ILO), F3 `const:_GAMOT_AREA` (BCL) |
| lost | 6 | F1 `const:_PROBE`, six locales — **retired** in `F1/generate_qsf.py`, so these were stale rows nothing could render |
| degraded | 0 | ten were caught by the merge and held back (below) |
| unchanged | 310 | `intro:` values the Aug-21 paper re-extracted byte-identical, plus the 101 `const:` values held at their June-5 text |

315 renderable (English, locale) pairs after the pass; 316 before.

Nothing renderable was lost and nothing got worse. That was **not** true of the first pass
of this task — see the next section.

## The ten degradations the first pass shipped, and why the merge missed them

F1's section intros were re-keyed by the Aug-17/Aug-21 renumbering
(`intro:51/101/118/135/163` -> `intro:38/88/105/122/150`) with the English text unchanged.
`merge_notes()` originally resolved the prior value by **key**, so a re-key looked like a
brand-new note: the Aug-21 value was counted `written`, and the "review every `replaced`"
gate never fired. Ten locale strings shipped worse than their June-5 predecessors:

- `F1 note:intro:38:*` (all seven locales) — the YAKAP/Konsulta intro lost two of its three
  sentences ("...package. Mangyaring sagutin ayon sa iyong kaalaman. Maaari kang sumagot ng
  'Hindi ko alam' kung ikaw ay hindi sigurado." -> "...package"). The English still carries
  all three, so the tablet showed a full English instruction beside a truncated translation.
- `F1 note:intro:105:CEB` / `:ILO` — the licensing intro picked up a stray section letter
  from the reflowed line ("...sa lisensya **F**", "...panaglisensia.) **F**").
- `F4 note:intro:51:BIS` — the Bisaya UHC-awareness intro gained a truncated **English**
  enumerator note the enumerator would read aloud ("...Universal Health Care (UHC) Note to
  enumerator [do not read]: This section is for").

Fixed in two places:

1. `merge_notes()` now resolves the prior by the note's **English text**
   (`extract_notes.canon_english()`, same normalisation as `notes_lookup._canon`), so a
   re-key is reported as `replaced` and reviewed. It also carries a renumbered note's prior
   forward when the Aug-21 paper cannot re-extract it, instead of dropping it to English.
2. The ten values are held at their June-5 text by ten `note:intro:*` rows in
   `aug21-overrides.json`, each carrying the layout reason above.

With both in place the pass reports `replaced 0`: every Aug-21 value that differs from its
June-5 predecessor has been looked at.

## One imperfection deliberately accepted

`F4 note:intro:144:BIS` is a **gain** (there was no June-5 Bisaya value) but it carries
English reflow debris from the preceding sentence: `"take- aways. Naa na kita sa katapusang
pipila ka seksyon sa survey questionnaire"`. `polish()` strips a single lowercase English
leftover token, not a hyphen-split two-token one. It is kept because the alternative is the
full English fallback; if it reads badly on device, add
`F4 / "note:intro:144:BIS": {"keep": ""}` to `aug21-overrides.json` to force English back.

## Why 101 overrides — the Aug-21 paper glues the directive to the question stem

June-5 paper printed each enumerator directive on **its own line**, with the translated
directive on the next line, which is what `find_translation()` relies on:

```
15. What is the main role of the public health unit?
Ano ang pangunahing tungkulin ng yunit ng pampublikong kalusugan?
READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY.
BASAHIN ANG PAGPIPILIAN NANG MALAKAS. PUMILI NG ISANG SAGOT LAMANG.
```

Aug-21 paper reflowed the directive **inline, after the question stem**:

```
21. Does your facility currently submit ...? READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY.
Kasalukuyan bang nagsusumite ...? BASAHIN ANG PAGPIPILIAN NANG MALAKAS. PUMILI NG ISANG SAGOT LAMANG.
```

The text that follows the English directive is therefore the **translated question**, not
the translated directive. Every `const:` candidate the Aug-21 pass produced is a question
("Ano an pinaka role kan public health unit?") or a stem fragment ("MGA OPSYON"), so all
101 of them are held back in `aug21-overrides.json` — `keep: <June-5 value>` where one
exists, `keep: ""` (render English) where none does.

Two smaller classes are folded into the same override block, with their own reasons:
`_GAMOT_FAC` / `_IF_YES_AMOUNT` (Aug-21 candidate = the June-5 value with an English
leftover word — "facility ...", "spent ..." — glued on), and the three new `_RECEIPT`
candidates that carry only the first of the directive's two sentences.

`F3 const:_GAMOT_AREA BCL` is the one `const:` value that came through complete and correct
and is **not** overridden.

Total `aug21-overrides.json` note rows: **111** (F1 39 / F3 37 / F4 35) — 101 `const:` +
the 10 `intro:` rows above.

## Extractor change

`dump_source()` drops page furniture (`ICF ver.`, `Translated Questionnaire ver.`,
`PSA SSRCS Clear...`, bare page numbers) from the text dump — the same lines
`anchor_extract.pdf_text()` already strips from these PDFs. Without it the Aug-21 footer
lands *between* an English note and its translation on nine notes and is shipped as the
translation. `pdf_lines()` itself still returns the raw page text.

## Task 11: per-language consent wired into `generate_qsf.py`

**Date:** 2026-08-25 · **Files:** `F1/generate_qsf.py`, `F3/generate_qsf.py`, `F4/generate_qsf.py`

`OVERRIDES["ICF_PART1"/"ICF_PART2"]` switched from `icf_content.build_screen_html(inst, part,
_LOGO_HTML)` (one English-only string) to `icf_content.screens_html_by_lang(inst, part,
_LOGO_HTML)` (`{lang: html}`, EN + the 7 ICF_LANGS). Each generator's per-language render loop
now indexes `ov[lnm]` instead of using the same `ov` string for every language. Header
comments that used to read "emitted identically for every declared language (English fallback
until SJREB-approved ICF translations arrive)" now read "Per language since the Aug-21 import:
icf_content.screens_for() falls back to English per paragraph."

**Only F1's `.qsf` was regenerated in this task** (`generate_dcf.py` + `generate_qsf.py`, then
`automation/verify_questions.py F1` -> PASS). F3's and F4's `generate_qsf.py` now carry the
same per-language wiring in source, but their `.qsf` files stay intentionally stale until
Wave 2/Wave 1 (Tasks 28 and 41 respectively) regenerate them alongside those waves' other
changes.

`notes_lookup.coverage()` BEFORE/AFTER (BEFORE = Task 8 Step 5 values, captured above under
"Merge result"; AFTER = re-run after this task's F1 regen — notes are qsf-side text unaffected
by dcf regen, so these numbers are unchanged from the table above):

| | FIL | BCL | BIS | CEB | WAR | HIL | ILO |
|---|---|---|---|---|---|---|---|
| BEFORE | 51 | 45 | 45 | 28 | 48 | 45 | 38 |
| AFTER  | 51 | 46 | 46 | 27 | 47 | 44 | 38 |

`icf_content.coverage()` AFTER (BEFORE = `{}` — no `icf.json` existed until Task 10):

| locale | differs | stored |
|---|---|---|
| FIL | 23 | 23 |
| BCL | 23 | 23 |
| BIS | 23 | 23 |
| CEB | 23 | 23 |
| WAR | 23 | 23 |
| HIL | 21 | 21 |
| ILO | 23 | 23 |

**Override keys landed for the ICF layer** (full reasons in `aug21-overrides.json` and in
`patch-notes/aug21-icf-layer.md`'s "Seeded overrides" table): `F1 icf:1:1:FIL` (F1-Tagalog
paper prints F3's English coverage sentence, so the anchor matches only a prefix — the
Tagalog paragraph itself is correct and is seeded verbatim); `F3 icf:2:3:BIS` / `F3
icf:2:4:BIS` (two paragraphs ran together on the paper, split back apart); `F1 icf:2:1:BCL` /
`F4 icf:2:1:BCL` / `F3 icf:1:0:ILO` / `F4 icf:1:0:ILO` (missing sentence-final punctuation,
restored). No `"keep": ""` English-forcing entries exist in the `icf:` override rows — the
`"keep": ""` rows in `aug21-overrides.json` are all in the `note:const:*` block (enumerator
directives with no Aug-21-recoverable value), not the ICF layer.

Probe confirming the wiring on the regenerated F1 `.qsf` (`FacilityHeadSurvey.ent.qsf`,
`ICF_PART1` block): `FIL differs from EN: True | Kamusta in FIL: True | 08/21/2026: True | FIL
para 2 translated: True` — the last one confirms the `icf:1:1:FIL` override rendered.

**Tester-visible sentence (one line, for each wave's patch note):**

> The consent screens and the section intros now read in the selected language (Aug-21
> cleared translations); paragraphs without a cleared translation stay English.

## Open item for the controller (Tasks 25 / 29)

Task 25 adds four new F4 gate constants and Task 29 re-runs this command for them. Under
the Aug-21 layout the `const:` family **cannot** be recovered by "take the text after the
English", so those constants will extract questions too and will need the same override
treatment (`keep: ""`), unless `find_translation()` is taught the new layout first — e.g.
by requiring the candidates from a note's multiple occurrences to agree (a directive
repeats verbatim; a question does not). A prototype of that guard also changes 41 June-5
values, so it is a design decision, not a drop-in.

## Task 29 closed the open item above

Task 25's two F4 gate constants (`_GATE_ANSWER_ONLY_IF_YES`, `_GATE_DOH_RETAINED` — four
items: Q117/Q118/Q131/Q135) went the way this section predicted. Every Aug-21 F4 paper is
bilingual-inline and prints both English gates, but the reflow puts the ENGLISH QUESTION
directly after the gate and the dialect gate only after that question, so
`find_translation()` recovers the question. Measured, not assumed: an unheld import wrote
`"After you went to the specialist or special service, did they"` into all seven locales of
`const:_GATE_ANSWER_ONLY_IF_YES`; `const:_GATE_DOH_RETAINED` recovered nothing anywhere.

15 `keep: ""` rows were seeded (7 + 7 gate rows, plus `note:intro:144:BIS`, which closes the
"accepted imperfection" named earlier in this note — the `take- aways.` reflow debris). The
merge then reported `written 0, replaced 0, overridden 119, kept_prior 7`, and all four
items render the English bracketed gate in every language while Q118's second instruction
paragraph (`_READ_ONE`) still translates on its own. The extractor was **not** changed.

Notes coverage moves only by the deliberate BIS hold:
`FIL 51 · BCL 46 · CEB 27 · WAR 47 · HIL 44 · ILO 38 · BIS 46 -> 45`.

**Handed to the controller, and closed in Task 29 fix round 1 (2026-08-26):**
`extract_notes.norm()` flattens en/em dashes before it keys a note; `notes_lookup._canon()`
did not. `F4 SECTION_INTROS[144]` carries two em-dashes, so that intro never resolved and
rendered English in all seven locales. See the next section.

## Task 29 fix round 1: the em-dash key mismatch, and what it exposed

**Date:** 2026-08-26 · **Files:** `notes_lookup.py`, `data/translations-official/extract_notes.py`,
`data/translations-official/aug21-overrides.json`, `data/translations-official/notes.json`

### The defect

Three normalisers decide what "the same note" means: `extract_notes.norm()` on the write
side, `extract_notes.canon_english()` on the merge side, and `notes_lookup._canon()` at
render time. `norm()` folded en/em dashes and NBSP; `_canon()` folded only quotes and
whitespace. Any note authored with a dash was therefore **stored under a key the runtime
could never build**, and the lookup fell back to English without a word of complaint.

`F4 SECTION_INTROS[144]` — the 865-character household-consumption script, the longest
intro in the instrument — carries two em-dashes. Swept every note anchor in F1/F3/F4: it is
the only dash-bearing one, so this was one note, not a class, but the mechanism was general.

`_canon()` (and `canon_english()`, which documents itself as matching it) now fold
`–`, `—` and NBSP. The fold is a no-op on anything that already went through `norm()`; it
exists so a caller passing RAW generator text cannot re-open the gap.

### What the fix exposed: the values were 4-9% fragments

With the intro reachable, the six stored translations turned out to be truncated captures,
not usable text:

| | EN | FIL | BCL | CEB | HIL | WAR | ILO |
|---|---|---|---|---|---|---|---|
| characters | 865 | 36 | 45 | 60 | 68 | 71 | 78 |
| ratio | — | 0.04 | 0.05 | 0.07 | 0.08 | 0.08 | 0.09 |

`SECTION_INTROS[144]` is two English paragraphs in the generator; the paper prints them as
separate blocks, so `find_translation()` cuts the dialect text at the first English-reading
line and keeps only the opening clause — `"Nasa huling bahagi na tayo ng survey"` — dropping
the entire script: *exclude restaurant meals*, *do not include items bought for business,
resale, or for making other products*. A ratio sweep of all 314 stored note translations
puts these six in the bottom six rows; the next-worst is 0.22. It is an outlier.

Reading that fragment aloud is worse than reading the English the tablets show today, so
**all seven locales are held** (`note:intro:144:{FIL,BCL,CEB,WAR,HIL,ILO}` added at
`keep: ""` beside the existing `:BIS` row). Truncated extractor output is a defect, never an
accepted `keep`, and repairing `find_translation()` to span a multi-paragraph intro re-keys
every note in F1/F3/F4 — F1 is live — so that is a wave-level change, not a fix round.

### Result

`aug21-overrides.json` F4 note rows 134 -> 140. The merge reports
`written 0, replaced 0, overridden 125, kept_prior 7` and replays to a byte-identical
`notes.json`. `F4/HouseholdSurvey.ent.qsf` regenerates **byte-identical**
(`155d2cff203c26769dc230ab1e9fb62d`) — no artefact change, nothing to deploy for this fix.
F1 and F3 are untouched: the blast-radius sweep over all 67 note anchors found `intro:144`
the only one whose rendering the fold can change.

`notes_lookup.coverage()` — six deliberate -1s, all the intro:144 hold:

| | FIL | BCL | BIS | CEB | WAR | HIL | ILO |
|---|---|---|---|---|---|---|---|
| before fix round | 51 | 46 | 45 | 27 | 47 | 44 | 38 |
| after  fix round | 50 | 45 | 45 | 26 | 46 | 43 | 37 |

### Still open for the controller

`find_translation()` cannot capture a dialect intro that the generator assembles from more
than one English paragraph. `F4 intro:144` is the only note held for this reason today, but
the next multi-paragraph intro will hit it silently — the symptom is a stored value a small
fraction of its English. A length-ratio warning in the extractor would surface the class.
