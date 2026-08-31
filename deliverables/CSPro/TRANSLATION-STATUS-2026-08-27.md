# Aug-21 translation import — status, 2026-08-27

Where the four instruments stand after ASPSI's revised **Aug-21** questionnaire pack
(English + seven dialects × F1/F2/F3/F4) was aligned and imported. One page, measured
numbers, and a named owner for everything that is still English.

Scope of the wave: English alignment to the Aug-21 masters and the translation import.
Runtime error messages were out of scope. The PSA submission set stays frozen at tag
`capi-psa-2026-08-20` (F1 v3.1.5 / F2 v3.0.0 / F3 v6.0.2 / F4 v3.1.3); **everything below is
the DEV channel.**

## What shipped

| instrument | build | deployed | patch note | evidence |
|---|---|---|---|---|
| F1 Facility Head Survey | **v4.1.1** `[DEV]` | 2026-08-27 | `patch-notes/2026-08-27-f1-v4.1.1-aug21-translations.md` | `docs/uat-fix-evidence/2026-08-26-aug21-translations/F1/` |
| F2 HCW Survey (PWA) | spec **2026-08-27-m5** (build `ce05b931`) | 2026-08-27 | `patch-notes/2026-08-27-f2-m5-aug21-translations.md` | `docs/uat-fix-evidence/2026-08-26-aug21-translations/F2/` |
| F4 Household Survey | **v3.2.3** `[DEV]` | 2026-08-27 | `patch-notes/2026-08-27-f4-v3.2.3-aug21-translations.md` | `docs/uat-fix-evidence/2026-08-26-aug21-translations/F4/` |
| F3 Patient Survey | **v6.1.2** `[DEV]` | 2026-08-27 | `patch-notes/2026-08-27-f3-v6.1.2-aug21-translations.md` | `docs/uat-fix-evidence/2026-08-27-aug21-translations/F3/` |

Superseded the same day and **not** what a tester should be running: F4 v3.2.0 / v3.2.1
(Waray question-number prefixes, then the Filipino bracket gloss) and v3.2.2; F1 v4.1.0;
F3 v6.1.0 and v6.1.1; F2 build `fb91241a` under the same m5 stamp. Versions come from
`versions.json`, the single source of truth for both stamped surfaces. F2 is the exception
that proves the rule: a translation-only redeploy does **not** bump `LOCAL_SPEC_VERSION`, so
m5 covers two builds and the build sha is what identifies which one PROD serves.

### Fix wave — 2026-08-27 afternoon (row inheritance)

A whole-branch review of the four first builds found a defect **class** none of the
extractor's 23 QA flags can see: an option row silently carrying the *neighbouring* row's
translation. The text is well-formed and in the right language, so it reads as a normal
translation — it is simply the wrong answer against the code the enumerator taps. Two
mechanisms, both proven from the papers (Task 48): an **adjacent-English pair**, where a
two-column option grid emits `EN EN TR TR` so the first row's span comes back empty and the
second swallows the block; and a **duplicate label**, where the paper repeats one
translation across rows (or one English label appears in two value sets) and the poisoned
occurrence wins the extractor's `most_common()` vote.

Six confirmed live instances were corrected, each by re-applying the whole wave from the
pre-wave baseline with the fixed extractor — never by hand-editing a map:

| instrument | instance | what shipped now |
|---|---|---|
| F3 `ceb` | `val:*_SOURCE_VS1:06` `LGU/Barangay` held code 02 `Legislation`'s `Balaod`, on 7 questions (Q36/Q75/Q100/Q117/Q120/Q125/Q153) | the paper's `LGU/Barangay` is **written**, under a value-pinned entry in `scan_waivers.json` (v6.1.2; v6.1.1 deleted the rows instead — same rendered text) |
| F4 `fil` | `val:Q45_2_WHY_NOT_REG_VS1:02` and `:03` held code 01's `Mahirap magparehistro` | rows **deleted** — the English option renders |
| F4 `ilo` | `val:Q45_2_WHY_NOT_REG_VS1:08` held code 07's text | row deleted |
| F4 `war` | `val:Q128_NBB_UNDERSTAND_VS1:05` and `val:Q134_ZBB_UNDERSTAND_VS1:05` held code 03's text | rows deleted |
| F1 `bcl` / `fil` | `val:Q83_NOT_RECEIVED_REASONS_VS1:03` and `val:Q45_PERF_INDICATORS_VS1:04` held their code-02/03 sibling's text | rows deleted; `bcl :02`'s clean span kept by an explicit override |
| F2 `war` | `City / LGU standard referral form` carried the `DOH standard referral form` translation glued to its tail | repaired at the extractor; one value changed in the live spec |

Deletion is the honest repair where the paper carries no distinct text for the row: **an
English option beats one that repeats another option's words**, and every deleted row is on
the translator worklist as work for ASPSI. The `remove: true` override semantic
(`apply_aug21.py`, and its per-locale twin in the F2 applier) is what expresses that, and it
replays — a re-apply deletes the same keys again rather than resurrecting them.

The class cannot come back silently. `apply_aug21.py` now carries a permanent
**duplicate-label gate**: it judges the whole resulting map, and a value set where two codes
would render the same string blocks the apply (`--fail-on-pre` extends that to pre-existing
collisions; a RED gate writes nothing and exits 2). `duplicate_label_accepted.json` — the
only way to declare such a pair benign — ships **empty**. `_defect_sweep.py` reuses the same
gate so the sweep and the applier cannot disagree. Two smaller pieces of tooling landed with
it: `scan_waivers.json`, which lets a *named, value-pinned* row past a `scan_poisoned_keys`
category (7 entries, all F3/`ceb`, all the `LGU/Barangay` row) instead of loosening the
scanner for everyone, and `aug21_overrides.py`'s validation of `remove`.

Cost, measured: 76 `duplicate-label` + 4 `sibling-run` rows moved from the extract to the
worklist (F1 8, F2 2+1, F3 27+2, F4 39+1) and 0 wrong values gained. Coverage drops a point
in a few cells for exactly that reason — see the note under the table below.

## Coverage, before → after

<!-- BEGIN generated by automation/translation_coverage.py -->

Coverage = keys present in the translation map (label nodes for F1/F3/F4; label objects, 740 of them, for F2). It measures presence, not linguistic quality - the translator worklist lists what is still English and why.

`before` = the row each wave's patch note records for the build it replaced; `after` = measured by re-running this tool's sources on today's tree (F1/F3/F4: `generate_dcf.py`'s own summary line, percentage truncated; F2: `deliverables/F2/PWA/app/scripts/f2-coverage.py`, percentage rounded).

| instrument | locale | before | after | delta |
|---|---|---|---|---|
| F1 | BCL | 67% | 81% | +14 |
| F1 | BIS | 67% | 80% | +13 |
| F1 | CEB | 62% | 77% | +15 |
| F1 | FIL | 66% | 81% | +15 |
| F1 | HIL | 66% | 79% | +13 |
| F1 | ILO | 61% | 79% | +18 |
| F1 | WAR | 66% | 81% | +15 |
| F2 | bcl | 74% | 79% | +5 |
| F2 | bis | 74% | 77% | +3 |
| F2 | ceb | 74% | 83% | +9 |
| F2 | fil | 72% | 80% | +8 |
| F2 | hil | 72% | 80% | +8 |
| F2 | ilo | 75% | 83% | +8 |
| F2 | war | 76% | 84% | +8 |
| F3 | BCL | 53% | 65% | +12 |
| F3 | BIS | 55% | 68% | +13 |
| F3 | CEB | 58% | 71% | +13 |
| F3 | FIL | 60% | 74% | +14 |
| F3 | HIL | 43% | 57% | +14 |
| F3 | ILO | 52% | 69% | +17 |
| F3 | WAR | 57% | 72% | +15 |
| F4 | BCL | 61% | 67% | +6 |
| F4 | BIS | 61% | 66% | +5 |
| F4 | CEB | 64% | 69% | +5 |
| F4 | FIL | 60% | 65% | +5 |
| F4 | HIL | 50% | 58% | +8 |
| F4 | ILO | 59% | 68% | +9 |
| F4 | WAR | 65% | 70% | +5 |

### Measured counts (`after`)

- **F1** - of 1363 label nodes: FIL 1108, BCL 1113, BIS 1093, CEB 1050, WAR 1108, HIL 1086, ILO 1082
- **F3** - of 1749 label nodes: FIL 1305, BCL 1154, BIS 1194, CEB 1252, WAR 1260, HIL 1007, ILO 1211
- **F4** - of 1403 label nodes: FIL 917, BCL 949, BIS 933, CEB 978, WAR 992, HIL 827, ILO 957
- **F2** - of 740 label objects: fil 593, ceb 611, bis 570, ilo 617, hil 593, war 625, bcl 587

Two layers outside the dictionary, counted by their own modules:

- **Enumerator notes** (`notes_lookup.coverage`) - translated notes on file: FIL 50, BCL 45, BIS 45, CEB 26, WAR 46, HIL 43, ILO 37
- **ICF consent paragraphs** (`icf_content.coverage`) - differing from English / recorded: FIL 23/23, BCL 23/23, BIS 23/23, CEB 23/23, WAR 23/23, HIL 21/21, ILO 23/23

<!-- END generated by automation/translation_coverage.py -->

Every one of the 28 cells gained. Coverage counts key *presence*: a cell could only have
fallen if an override had deleted a key.

Which is exactly what the fix wave did, so the block above is **re-measured after it** and
three cells read one point lower than the first builds' patch notes record — F3 `bcl` 66 → 65,
F4 `hil` 59 → 58, F4 `war` 71 → 70 — with smaller node-count drops elsewhere (F1 `fil`
1109 → 1108 and `bcl` 1114 → 1113 are the two deleted F1 rows). Those points are the deleted
row-inheritance rows: a key that renders the *wrong* option is not coverage. F2's `fil` count
is 593 and not 594 for the same reason — one Q95 option key was deleted in the m5 fix round
because the Aug-21 Tagalog paper prints a single string against both rows of that grid;
593/740 still rounds to the 80 % in the table.

Two further things the table does not say on its own:

* **F4's denominator here is 1403, the F4 patch note's is 1401.** The note counts against the
  Aug-21 English *key set* (`task-30/_coverage_delta.py`) so its before/after rows are
  strictly comparable; this table is the generator's own line, which sees two more label
  nodes, translated in every locale. Every F4 percentage is identical either way.
* **The F3 note prints three coverage tables**, each superseding the one above it. The row
  that matches this block is the last one (the v6.1.1/v6.1.2 section), not the round-0 table
  or the `### Coverage (supersedes the table above)` fix-round-1 table: wave-4b fix round 1
  traded 13 labels to remove 36 dangling-tail values, and the fix wave then removed 28 more
  row-inheritance rows.

## Overrides — the keys the import must not write

`data/translations-official/aug21-overrides.json`. Aug-21 wins on every key **except** these;
each carries a `reason`, and F1/F3/F4 entries are locale-scoped so a one-paper defect never
suppresses the same key in the other six maps.

| instrument | entries | held (`keep: null`) | renders English (`keep: ""`) | accepted text | deleted (`remove: true`) | of which `note:` / `icf:` |
|---|---|---|---|---|---|---|
| F1 | 73 | 29 | 19 | 23 | 2 | 39 / 2 |
| F3 | 205 | 143 | 20 | 27 | 15 | 37 / 3 |
| F4 | 157 | 82 | 35 | 27 | 13 | 56 / 2 |
| F2 | 41 (across 7 locales) | 4 | — | 36 | 1 | — (English-string keys) |

`remove: true` is the fix wave's addition: the key is **deleted** from the map during
`--apply`, so the English label renders. It is for rows whose only paper candidate is wrong —
never a way to mask poisoned extractor output, which is an extractor defect. Like every other
override it is locale-scopable and it replays: a re-apply deletes the same keys again.

Validate with `python data/translations-official/aug21_overrides.py`.

## What is still English, and why

The flagged worklists on disk (`data/translations-official/out-aug21/<INST>/{loc}_flagged.json`,
measured 2026-08-27) are what Task 45 exports for ASPSI's translators:

| instrument | flagged rows | per locale (low–high) | dominant flags |
|---|---|---|---|
| F1 | 2,318 | fil 310 – bcl 364 | `not-in-paper` 1215, `empty` 440, `label-condensed` 367 |
| F2 | 813 | war 99 – hil 167 | `empty` 433, `not-in-paper` 170, `echo-english` 77 |
| F3 | 4,341 | war 529 – hil 802 | `not-in-paper` 2224, `empty` 1109, `length-ratio` 268 |
| F4 | 3,531 | ilo 443 – hil 548 | `not-in-paper` 1865, `empty` 718, `length-ratio` 386 |

The fix wave added 80 rows to those totals: the 76 `duplicate-label` and 4 `sibling-run` rows
the extractor now refuses to import (F1 8, F2 2 + 1, F3 27 + 2, F4 39 + 1). They are the rows
whose translation belongs to a neighbour, and they now reach ASPSI as work rather than the
tablet as a wrong answer.

`not-in-paper` and `empty` together are most of every column: the paper prints no translation
under that anchor. **An untranslated cell is not a build defect** — nothing may be invented.

Named holds, per instrument (full text in each patch note's *Held this build* section):

* **F1** — HIL Q10.1–Q35.1 option 4 (19 sibling value sets: the Hiligaynon paper stutters
  `sa masunod` on the option row); `val:Q62_ENROLL_RESPONSIBILITY_VS1:02` (the extractor
  own-matched the cover title and emitted `Head`); `item:Q140_UNCLEAR_PROTOCOL` and Q75
  (no paper span bounds them); the Ilocano paper prints Q74 and Q91 in English.
* **F2** — Tagalog Section A `Q2` (the Tagalog paper prints the question in English only);
  `hil` is the weak locale at 167 flagged rows because whole option rows are printed in
  local with no English to anchor on; the ballot-box option lists are English in all seven
  papers *by design*.
* **F3** — the 115.1 / 115.2 matrix row labels ship English in all seven locales, and the
  115.2 gate stem in BCL/CEB/HIL: the papers print those rows in the English column only
  (accepted explicitly, see *Coverage hold ACCEPTED* in the F3 note); the satisfaction grids
  (Q131–Q135, Q144, Q178) contaminate 105 rows; `val:Q94_LAB_PAY_VS1:01` English on five
  locales.
* **F4** — the Section-N intro (`intro:144`) and the four printed gates (Q117/Q118/Q131/Q135)
  render English deliberately (a 4–9 % fragment of an 865-character read-aloud script is
  worse than the English); 7 Waray paper-number-mismatch rows; `val:Q88_DIFF_PAYING_VS1:04`
  trails into `intro:89` in all seven maps (pre-existing).

## Source-side defects — for ASPSI, not fixable in CAPI

1. **F1-Tagalog page 1, paragraph 2** prints *F3's* English coverage sentence above the
   correct F1 Tagalog. English-side paper defect; the build is unaffected (override seeded).
2. **F3-Hiligaynon consent page** carries an older English variant — an extra privacy clause,
   no Php 100 token-of-appreciation sentence, and the "Nothing bad will happen…" paragraph
   missing. Two paragraphs stay English on-device (HIL ICF 21/23).
3. **F3-Tagalog header still reads `06/05`** — the one paper of the 21 whose header was not
   re-stamped in the Aug-21 pack. It is still part of the Aug-21 delivery; the CAPI clearance
   line stamps `08/21/2026` for every locale. Do not "correct" it in the build.
4. **The Aug-21 Tagalog F4 and F3 papers are bilingual** (English line + bracketed Filipino
   gloss) where the other six are monolingual — the layout that produced the FIL brackets
   v3.2.0/v3.2.1 shipped. The extractor now drops the wrapper; the paper is unchanged.
5. **The Waray F4 paper's question numbering runs one behind the CAPI's** on Q27/Q28/Q29 and
   the result-of-visit grid (the 7 held rows), and ten Waray/Hiligaynon values still carry a
   printed question number with no clean Aug-21 replacement.
6. **Paper-side stutters and inconsistencies**: HIL F1 Q10.1–Q35.1 option 4; ILO F3 Q54/Q55/Q57
   (`kangrunaan a kangrunaan a`); WAR F3 Q16 prints its whole question twice; BCL/HIL F3
   Q131–Q135 scale wording differs from itself (`Kotento` / `Kontento`).
7. **Missing sentence-final punctuation** on F1-Bicolano 2:1, F4-Bicolano 2:1, F3/F4-Ilocano
   1:0; F1-Bicolano 2:1 also stops short of the English.
8. **`echo-english` cells** — the paper reprints the English under the anchor instead of a
   translation. **F1 10, F2 77, F3 99, F4 44** (measured 2026-08-27 over
   `out-aug21/<INST>/<loc>_flagged.json`). The heaviest single papers are F2-Bicolano (57 of
   F2's 77), F3-Cebuano (42) and F3-Tagalog (37), and F4-Bicolano (26); F1's ten are
   bcl 5 / bis 2 / ceb 3. Nothing can be imported from those cells.

## Follow-ups already recorded (not in this wave)

| item | owner | note |
|---|---|---|
| **F4 3.2.3** — re-import the 74 hold rows the Task-40 extractor now clears | build | measured, maps untouched |
| **F1 4.1.1** — re-import the 68 rows Task 27's extractor now changes: 7 × `val:Q62_…:02` (six recover `Pasilidad`) + 61 orphan-glyph rows | build | F1 shipped on the older extractor |
| 85 dangling-tail values live in the F1/F4 maps (113 remain in F3) | build | same re-import |
| **F3 115.x** generator-side label composition (14 keys × 7 + `Q1142_HAS_OTHER` × 3) | build | compose stem + option from translated parts |
| PROC `Q1141_OTHER_TXT` gates on row 1 instead of row 6 (errmsg 1177) | UAT ticket **#1315** (filed 2026-08-27) | pre-existing, found in Task 39 |
| `val:PATIENT_TYPE_VS1:1/2` fragments in 6/7 F3 locales (routing field) + HIL `item:Q7_SEX` | UAT ticket **#1316** (filed 2026-08-27) | pre-existing June-5 text; fix = locale-scoped `keep: null` + extractor rule |

## The exported worklist

`export_worklist.py` turns everything above into two files ASPSI's translators can work
from - `translator-worklist-aug21.xlsx` (one sheet per section, plus a `summary` sheet -
**seven** in all) and `translator-worklist-aug21.csv` (the same rows flat; `status` tells
the sections apart). **13,276 rows**, re-exported 2026-08-27 after the fix wave, from the
re-run extracts in `data/translations-official/out-aug21/`:

| sheet | rows | F1 | F2 | F3 | F4 | what it holds |
|---|---:|---:|---:|---:|---:|---|
| `worklist` | 11,682 | 2,430 | 813 | 4,635 | 3,804 | every flagged row, plus the 679 dictionary anchors no paper span was found under |
| `held` | 789 | 50 | 5 | 459 | 275 | every `keep: null` / `keep: ""` / `remove: true` override, one row per locale it governs, with the reason |
| `accepted` | 113 | 23 | 36 | 27 | 27 | the override rows that DO carry text, with the reason they were kept |
| `residual` | 301 | 92 | 55 | 93 | 61 | imported rows that read with a stray glyph, an unbalanced bracket or a dangling tail |
| `paper-defects` | 385 | 26 | 6 | 327 | 24 | 14 named defects in the printed questionnaires (2 further rows are cross-instrument) |
| `follow-ups` | 6 | 1 | - | 3 | 1 | the table above, so a translator does not re-report it |

The `worklist` sheet now carries the fix wave's 76 `duplicate-label` and 4 `sibling-run`
rows (F1 8, F2 2 + 1, F3 27 + 2, F4 39 + 1): the rows the extractor refuses to import
because their only paper candidate is a neighbouring row's translation. The `held` sheet
distinguishes the three kinds of override in its `flags` column - `held:` (680 rows: the
map keeps whatever it had), `renders English:` (74) and **`removed:` (35 rows: F1 2, F2 1,
F3 19, F4 13)**, the `remove: true` rows the fix wave deleted from the maps. A `removed:`
row is real translator work; a `held:` row usually is not.

The `residual` sheet is the one nothing else covers: those rows passed the extractor's QA
gate, so they are absent from every `_flagged.json`, but they still read with a stray
leading quote or parenthesis, an unbalanced bracket, a missing full stop or a dangling
tail. They are cosmetic - the text is correct - and the F1 4.1.1 / F4 3.2.3 re-imports
clear most of them.

Two of those five shapes - the missing full stop and the dangling tail - can only be judged
against the English, so the exporter resolves each key's English from three indexes in
order: the paper anchors, then every labelled node of the written `.dcf` (which is what
adds the `record:` keys), then the English the extractor recorded on the flagged rows.
Whatever survives all three is a **stale map key**: the run reports them on stdout - `F1:
225 keys had no English label - punctuation/tail checks skipped`, F3 27, F4 38 - and none
of the 290 still exists in the live dictionary, which is why no English for them exists
anywhere. 46 of them (F1 40, F4 6) also read with a stray glyph or an unbalanced bracket,
so they reach the `residual` sheet; those 46 rows carry a `no-english-label` reason, which
is what keeps a blank English cell from being a silent one.

Regenerate (read-only - no `.dcf` / `.apc` / `.fmf` / `.qsf` is written):

```
python data/translations-official/apply_aug21.py --unmatched \
       --report data/translations-official/aug21_apply_diff.json
python data/translations-official/export_worklist.py \
       --xlsx translator-worklist-aug21.xlsx --csv translator-worklist-aug21.csv \
       --report data/translations-official/aug21_apply_diff.json
```

Run from `deliverables/CSPro/`. The first command refreshes the `unmatched` column and
writes nothing else; the second prints the per-instrument row counts above.

## How to re-measure

```
python automation/translation_coverage.py --before automation/aug21_coverage_baseline.json --out TRANSLATION-STATUS-2026-08-27.md
```

Run from `deliverables/CSPro/`. It rebuilds each dictionary in memory, runs
`apply_translations()` and reads the generator's own summary line, shells out to
`deliverables/F2/PWA/app/scripts/f2-coverage.py` for F2, and rewrites **only** the generated
block above — the hand-written sections of this file survive. No `.dcf` / `.apc` / `.fmf` /
`.qsf` is written, so `git status --short F1 F3 F4` is unchanged by the run.
