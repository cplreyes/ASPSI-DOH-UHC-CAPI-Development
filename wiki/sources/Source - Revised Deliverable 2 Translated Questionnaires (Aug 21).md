---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Survey-Instruments-2026-08-21]]"
date_ingested: 2026-08-27
tags: [translations, questionnaire, capi, cspro, deliverable-2, aug21]
---

# Source — Revised Deliverable 2 Translated Questionnaires (Aug 21)

ASPSI's **revised** translation pack, dated **August 21, 2026**: 28 translated PDFs
(**7 dialects × 4 instruments**) plus the 4 English masters they were translated from.
It supersedes the June-5 set
([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH Deliverable 2 Translated Questionnaires (June 5)]])
as the translation reference, and it is the first translated set that matches the Aug-17
renumbering
([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Updated Survey Instruments (2026-08-17)]]).

Imported into all four instruments between 2026-08-26 and 2026-08-27 — **F1 v4.1.1,
F2 spec `2026-08-27-m5` (build `ce05b931`), F4 v3.2.3, F3 v6.1.2**, all on the **DEV**
channel. Those are the second builds: the first set (F1 v4.1.0 / F2 `2026-08-26-m4` /
F4 v3.2.2 / F3 v6.1.0) was superseded the same day by the row-inheritance repair below.
The PSA submission set stays frozen at tag `capi-psa-2026-08-20`. The one-page status, with
measured coverage for every instrument × locale cell, is
`deliverables/CSPro/TRANSLATION-STATUS-2026-08-27.md`.

## Provenance

| | |
|---|---|
| From | ASPSI (Google Drive folder **[B]**), downloaded 2026-08-25 |
| On disk | `raw/Survey-Instruments-2026-08-21/` — gitignored, **immutable**, never edited |
| Drive file ids | `raw/Survey-Instruments-2026-08-21/drive-ids.json` (one id per PDF, so any file can be re-fetched) |
| Also in the folder | `Review of Deliverable 2 - UHC Survey - Year 2_Aug21.pdf` — DOH's feedback on the **manuals**, not the instruments (see below) |

## Files

| | |
|---|---|
| Languages | English + Tagalog (`FIL`), Bicolano (`BCL`), Bisaya (`BIS`), Cebuano (`CEB`), Hiligaynon (`HIL`), Ilocano (`ILO`), Waray (`WAR`) |
| Instruments | F1 Facility Head · F2 Healthcare Worker · F3 Patient · F4 Household |
| `raw/Survey-Instruments-2026-08-21/English/` | 4 PDFs — the masters the CAPI English wording was aligned to |
| `raw/Survey-Instruments-2026-08-21/Translations/` | 28 PDFs — 7 dialects × 4 instruments, no gaps |

As in June-5, **Bisaya and Cebuano ship as separate locales** and the build treats them
as separate. Every file name carries the `_Aug21` suffix; one (`F2-Cebuano`) uses a
slightly different stem (`Healthcare Worker_Survey_`), which is why the tooling matches
on the `F<n>-<Language>` prefix rather than the whole name.

### Layout quirks, per instrument

The pack is **not** uniform, and each quirk changed how a locale had to be extracted:

- **F2-Bicolano echoes the English inline.** 57 of the 77 F2 `echo-english` rows are
  Bicolano — the Bicolano paper reprints the English string under the anchor instead of
  a translation. The extractor writes nothing for those (a translation must never be
  invented); they go to the translator worklist.
- **F1-Tagalog page 1, paragraph 2 prints F3's English coverage sentence** above the
  correct F1 Tagalog consent text. An English-side paper defect; the build is unaffected
  (the paragraph is held by an override).
- **F3-Tagalog's header still reads `06/05`** — the one paper of the set whose header was
  not re-stamped. It is still part of the Aug-21 delivery, and the CAPI clearance line
  stamps `08/21/2026` for every locale regardless. Do **not** "correct" it in the build.
- **The Tagalog F4 and F3 papers are bilingual** (English line + a bracketed Filipino
  gloss) where the other six are monolingual. That layout — not a CAPI defect — is what
  produced the bracketed Filipino labels that shipped briefly in F4 v3.2.0/v3.2.1; the
  extractor now strips the wrapper.

Compare June-5, where **every** paper was bilingual-inline and only `Waray_F4` was
monolingual. The Aug-21 pack inverts that: most papers are monolingual, so a translation
can usually be read directly rather than recovered by difference — but only where an
English anchor is still printed near it.

## How it was ingested

Name-scoped, not text-keyed. June-5 was joined to the build on the **full English label
text**, which silently orphans a translation the moment an English question is reworded
(#1182 / #1213). The Aug-21 pipeline keys on the dictionary **name** instead
(`item:` / `vs:` / `val:` — "name-scoped-v2"), anchored to the paper by question number:

1. `deliverables/CSPro/data/translations-official/aug21_english_delta.py` — build-vs-paper
   English delta, re-run before every extraction so no import lands on stale English.
2. `deliverables/CSPro/data/translations-official/anchor_extract.py` — pulls each
   translation out of the PDF text between two anchors, and flags what it could not
   trust (`not-in-paper`, `empty`, `label-condensed`, `directive-bleed`, `echo-english`,
   `truncated-tail`, …). F2 has its own extractor,
   `deliverables/CSPro/data/translations-official/anchor_extract_f2.py`, because the PWA
   stores strings in a flat English-keyed store rather than a dictionary.
3. `deliverables/CSPro/data/translations-official/apply_aug21.py` — merges the extract
   into the live maps. **Aug-21 wins on every key except** the ones listed in
   `deliverables/CSPro/data/translations-official/aug21-overrides.json`, each of which
   carries a written reason and is scoped to the locales it applies to. Dry run is the
   default; `--apply` writes. F2's merge is
   `deliverables/F2/PWA/app/scripts/apply-paper-translations.py`.
4. `deliverables/CSPro/data/translations-official/run_aug21_gates.ps1` — the pre/post
   gates (doubling, glued options, bridge B/C) that must be clean before a build.
5. The generators —
   `deliverables/CSPro/F1/generate_dcf.py`,
   `deliverables/CSPro/F3/generate_dcf.py`,
   `deliverables/CSPro/F4/generate_dcf.py` — rebuild the dictionaries from the maps. No
   `.dcf` / `.apc` / `.fmf` / `.qsf` is ever hand-edited.

Two layers ride alongside the dictionary: the enumerator **notes**
(`deliverables/CSPro/data/translations-official/extract_notes.py`) and the **ICF consent**
paragraphs per language
(`deliverables/CSPro/data/translations-official/extract_icf.py`), both merged Aug-21-wins.

Wave notes, one per instrument (each carries its first build **and** the repair below):
`deliverables/CSPro/patch-notes/2026-08-27-f1-v4.1.1-aug21-translations.md`,
`deliverables/CSPro/patch-notes/2026-08-27-f2-m5-aug21-translations.md`,
`deliverables/CSPro/patch-notes/2026-08-27-f4-v3.2.3-aug21-translations.md`,
`deliverables/CSPro/patch-notes/2026-08-27-f3-v6.1.2-aug21-translations.md`. Day-0 tooling
notes are in `deliverables/CSPro/patch-notes/aug21-day0.md`.

## The row-inheritance defect class (2026-08-27)

A review of all four first builds found a defect **class** none of the extractor's QA flags
could see: an option row silently carrying its **neighbour's** translation. The text is
well-formed and in the right language, so it reads as a normal translation — it is simply
the wrong answer against the code the enumerator taps, which is why coverage, byte-verify
and the device frames all passed over it. Two page layouts produce it: an **adjacent-English
pair**, where a two-column option grid emits `EN EN TR TR` so the first row's span comes
back empty and the second swallows the whole block; and a **duplicate label**, where the
paper repeats one translation across rows (or one English label appears in two value sets)
and the poisoned occurrence wins the extractor's majority vote. Six live instances were
corrected — F3 `ceb` `LGU/Barangay` on seven questions, F4 `fil`/`ilo`/`war` option rows,
two F1 rows, and one F2 `war` value — each by re-applying the whole wave from the pre-wave
baseline with the fixed extractor, never by hand-editing a map. Where the paper carries no
distinct text for the row the row is **deleted** (`remove: true`) so the English option
renders: an English label beats one that repeats another option's words, and the deleted row
goes to the translator worklist. The class cannot return silently, because `apply_aug21.py`
now carries a permanent **duplicate-label gate** — a value set in which two codes would
render the same string blocks the apply, `--fail-on-pre` extends that to pre-existing
collisions, and `duplicate_label_accepted.json`, the only way to declare such a pair benign,
ships empty. Cost: 76 `duplicate-label` and 4 `sibling-run` rows moved from the import to the
worklist, and no wrong value gained. Evidence index:
`docs/uat-fix-evidence/2026-08-27-aug21-translations/README.md`.

## Known defects in the source

Paper-side, for ASPSI to fix in the next pack — none of them is fixable in CAPI:

1. **F1-Tagalog page 1 paragraph 2** carries F3's English coverage sentence.
2. **F3-Hiligaynon's consent page is an older English variant** — an extra privacy
   clause, no Php 100 token-of-appreciation sentence, and the "Nothing bad will happen…"
   paragraph missing. Two ICF paragraphs therefore stay English on-device (HIL 21/23).
3. **F3-Tagalog's header still reads `06/05`.**
4. **The Waray F4 paper's question numbering runs one behind the CAPI's** on Q27/Q28/Q29
   and the result-of-visit grid (7 held rows); ten Waray/Hiligaynon values still carry a
   printed question number with no clean Aug-21 replacement.
5. **Stutters and self-inconsistency**: HIL F1 Q10.1–Q35.1 option 4 repeats `sa masunod`;
   ILO F3 Q54/Q55/Q57 repeat `kangrunaan a`; WAR F3 Q16 prints its whole question twice;
   BCL/HIL F3 Q131–Q135 spell the same scale two ways (`Kotento` / `Kontento`).
6. **Missing sentence-final punctuation** on F1-Bicolano, F4-Bicolano and F3/F4-Ilocano
   paragraphs; F1-Bicolano also stops short of the English.
7. **`echo-english` cells** — F1 10, F2 77 (57 of them Bicolano), F3 99, F4 44 rows where
   the paper reprints the English under the anchor.
8. **One translation printed against two option rows** — the paper-side half of the
   row-inheritance class below (e.g. the Tagalog F2 agree/disagree grid, the Tagalog F4
   Q45.2 reasons). Those rows render English until ASPSI supplies distinct text.

An untranslated cell is **not** a build defect: where the paper prints no translation,
the instrument renders English on purpose.

## Where it landed

| instrument | build | deployed | coverage after (FIL … ILO) |
|---|---|---|---|
| F1 Facility Head | **v4.1.1** `[DEV]` | 2026-08-27 | 81 / 81 / 80 / 77 / 81 / 79 / 79 % of 1,363 label nodes |
| F2 HCW (PWA) | spec **2026-08-27-m5** (build `ce05b931`) | 2026-08-27 | 80 / 79 / 77 / 83 / 84 / 80 / 83 % of 740 label objects |
| F4 Household | **v3.2.3** `[DEV]` | 2026-08-27 | 65 / 67 / 66 / 69 / 70 / 58 / 68 % of 1,403 label nodes |
| F3 Patient | **v6.1.2** `[DEV]` | 2026-08-27 | 74 / 65 / 68 / 71 / 72 / 57 / 69 % of 1,749 label nodes |

(Locale order: FIL, BCL, BIS, CEB, WAR, HIL, ILO. Every one of the 28 cells gained,
+3 to +18 points. Coverage counts key *presence*, not linguistic quality. Three cells read
one point lower than the first builds' patch notes — F3 BCL, F4 HIL, F4 WAR — because the
repair deleted the rows that were carrying a neighbour's translation; a key that renders the
*wrong* option was never coverage.)

- Maps: `deliverables/CSPro/F1/translations/`, `deliverables/CSPro/F3/translations/`,
  `deliverables/CSPro/F4/translations/`; F2's store is
  `deliverables/F2/PWA/app/spec/translations/`.
- Status page: `deliverables/CSPro/TRANSLATION-STATUS-2026-08-27.md`.
- Translator worklist for the untranslated remainder:
  `deliverables/CSPro/translator-worklist-aug21.xlsx` (and `.csv`), 13,276 rows over seven
  sheets, re-exported after the repair.
- Device/render evidence:
  `docs/uat-fix-evidence/2026-08-26-aug21-translations/` (F1, F2, F4) and
  `docs/uat-fix-evidence/2026-08-27-aug21-translations/` (F3), indexed by the latter's
  `README.md`.

### Not part of this import

- **Runtime error messages** stay English — a separate ~590-string sheet, on request.
- **F2 chrome beyond the consent screen** (headings, buttons, the raffle block).
- **F3's 115.1 / 115.2 matrix row labels**, which the papers print in the English column
  only; a generator-side label composition is the follow-up.
- **The DOH `Review of Deliverable 2` PDF in this folder is manuals feedback** — it
  raises no instrument or translation item, and is routed to the manuals lane rather
  than to the CAPI build. Its August predecessor is
  [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH Review of Deliverable 2 (2026-08-13)]].

## Related

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH Deliverable 2 Translated Questionnaires (June 5)]] — the set this supersedes
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Updated Survey Instruments (2026-08-17)]] — the English renumbering these translations finally match
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI]] — supplier of the pack, owner of the paper-side defects
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro]] — the name-scoped import pipeline
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Multi-Language Applications]] — how CSPro carries the labels
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal]] — F2's PWA store, imported by its own tooling
