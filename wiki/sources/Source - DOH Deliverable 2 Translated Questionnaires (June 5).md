---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/DOH-Deliverable-2-2026-07-31/Data collection tools]]"
date_ingested: 2026-08-14
tags: [translations, questionnaire, capi, cspro, sjreb, deliverable-2]
---

# Source — DOH Deliverable 2 Translated Questionnaires (June 5)

The **authoritative translation reference** for the CAPI instruments: 32 PDFs covering
**8 languages × 4 instruments**, all dated **June 5, 2026**. This is the set SJREB
cleared and the one the CAPI build footer already cites as *Translated Questionnaire ver.
06/05/2026*, which makes it the correct answer to "what are the translations based on?"

Ingested verbatim on 2026-08-14 into
`deliverables/CSPro/data/translations-official/` — see its `README.md` for the extractor,
the per-file text dumps, and the limitations that matter before anything is applied to a
deployed instrument.

## What it contains

| | |
|---|---|
| Languages | English, Tagalog (=`FIL`), Bicolano (`BCL`), Bisaya (`BIS`), Cebuano (`CEB`), Hiligaynon (`HIL`), Ilocano (`ILO`), Waray (`WAR`) |
| Instruments | F1 Facility Head · F2 Healthcare Worker · F3 Patient · F4 Household |
| Numbered questions (English) | F1 167 · F2 124 · F3 184 · F4 201 |

`Bisaya` and `Cebuano` are supplied — and declared in the tool — as **separate** locales.

## Structural findings

**The translated PDFs are bilingual.** Each question repeats the English inline,
immediately followed by the translation, in one table cell. A translation therefore has
to be recovered by *difference* against the English-only PDF rather than read directly.

**`Waray_F4` is monolingual** — English appears inline in ~1% of its blocks against
53–78% for all 27 siblings. It is formatted unlike every other file in the deliverable.
Worth raising with ASPSI; see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI]].

**Question number is the reliable join key** across languages — English and Hiligaynon F3
both yield 190 numbered tokens with the same maximum (178).

## Why this matters to the build

The CAPI's `apply_translations()` matches translations to questions on the **full English
label text**. Any rewording of an English question silently orphans its translation and
the tool falls back to English with no error — the mechanism behind #1182 and #1213, and
a large part of the gap Shan's random screenshot check surfaced on 2026-08-14. Keying on
question number, as this source does, is the durable fix.

Measured against this reference, respondent-facing question coverage in the deployed
builds ran 36–62% by locale (weakest Ilocano, then Hiligaynon) — i.e. the translations
were **not** finalised in the tool, independent of whether ASPSI had finalised them on
paper.

## Related

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Dictionary Names Labels and Value Sets]]
