# Aug-21 translations — status for ASPSI

Close-out note for the revised Deliverable 2 (Aug-21) translation pack. Written to be sent
from the ASPSI address as-is; the technical build record is in the four per-instrument patch
notes and in `deliverables/CSPro/TRANSLATION-STATUS-2026-08-27.md`.

Prepared 2026-08-27.

> **ANNOUNCED 2026-08-27 ~14:00 MNL in #capi-scrum** (summary + thread; the workspace is on Slack's free plan, so no canvas/file upload — the full note and the xlsx/csv go by email from clreyes6@up.edu.ph): https://aspsi-doh-uhc-survey2.slack.com/archives/C0ASSTPLX9A/p1787805738244079

---

## In one paragraph

ASPSI's revised **August 21** questionnaires — 28 translated PDFs (7 dialects × 4
instruments) plus the 4 English masters — are now in all four data-collection tools. The
English wording was first brought in line with the Aug-21 masters, then each dialect was
imported from its own paper. Coverage rose in every one of the 28 instrument × locale
combinations. What is still English is, almost entirely, text that the printed
questionnaires do not carry a translation for — the attached worklist lists every one of
those cells so your translators can fill them, and a handful of defects in the printed
papers that only ASPSI can fix.

## What shipped

| Instrument | Version | Deployed | How testers get it |
|---|---|---|---|
| **F1 Facility Head Survey** | v4.1.1 | 2026-08-27 | CSEntry → remove the app, then Add Application → from CSWeb |
| **F2 Healthcare Worker Survey** (web) | spec 2026-08-27-m5 (build ce05b93) | 2026-08-27 | reload the site; the version stamp is in the header |
| **F4 Household Survey** | v3.2.3 | 2026-08-27 | CSEntry → remove the app, then Add Application → from CSWeb |
| **F3 Patient Survey** | v6.1.2 | 2026-08-27 | CSEntry → remove the app, then Add Application → from CSWeb |

> **These are the afternoon builds of 27 August.** The morning builds (F1 4.1.0, F2 m4, F4 3.2.2, F3 6.1.0) were replaced the same day — see
> **Update 27 Aug (afternoon)** at the foot of this note for what changed and why. The rest of this
> section still applies.

All four are on the **development channel**. The set submitted to PSA is unchanged and stays
frozen (F1 v3.1.5 / F2 v3.0.0 / F3 v6.0.2 / F4 v3.1.3, tag `capi-psa-2026-08-20`) — nothing
in this note alters what PSA holds. No question codes, option values or saved answers
changed; only the wording shown on screen.

F4 v3.2.0 and v3.2.1 were replaced the same day. A tester still on either of those is one
update behind.

## Coverage, before → after

Percent of on-screen labels that now have a translation on file, per instrument and dialect.
This counts whether a translation *exists*, not how good it reads.

| Instrument | | Tagalog | Bicolano | Bisaya | Cebuano | Waray | Hiligaynon | Ilocano |
|---|---|---|---|---|---|---|---|---|
| **F1** (1,363 labels) | before | 66% | 67% | 67% | 62% | 66% | 66% | 61% |
| | **after** | **81%** | **81%** | **80%** | **77%** | **81%** | **79%** | **79%** |
| **F2** (740 labels) | before | 72% | 74% | 74% | 74% | 76% | 72% | 75% |
| | **after** | **80%** | **79%** | **77%** | **83%** | **84%** | **80%** | **83%** |
| **F3** (1,749 labels) | before | 60% | 53% | 55% | 58% | 57% | 43% | 52% |
| | **after** | **74%** | **65%** | **68%** | **71%** | **72%** | **57%** | **69%** |
| **F4** (1,403 labels) | before | 60% | 61% | 61% | 64% | 65% | 50% | 59% |
| | **after** | **65%** | **67%** | **66%** | **69%** | **70%** | **58%** | **68%** |

Every cell gained, between +3 and +18 points. Two layers outside the questionnaire body also
landed: the **enumerator notes** (26–50 notes translated per dialect) and the **informed
consent form**, which now reads in the interview language for all seven dialects (23 of 23
paragraphs everywhere except Hiligaynon, which is 21 of 23 — see defect 2 below).

Hiligaynon is the weakest column in every instrument. That is a property of the papers, not
of the build: the Hiligaynon questionnaires print fewer translated lines than the other six.

## Attached

- **`translator-worklist-aug21.xlsx`** — 13,276 rows, one workbook, **seven sheets**: the six
  below plus a `summary` sheet that counts the rows per instrument.
  - `worklist` (11,682) — every label that is still English, with the English text, the
    instrument, the dialect and the reason it could not be taken from the paper;
  - `held` (789) — labels left English because what we could read off the paper was not
    usable as it stood, each with the reason. Three different things sit in this sheet:
    - **680 extraction failures.** The printed translation is there, but our reader could
      not lift it out cleanly — the span stops mid-sentence at an English word inside the
      question (160), stops mid-phrase on an English anchor such as *primary care
      provider* / *PhilHealth* / *Barangay* (129), carries the *next* option's text out of
      the satisfaction grid (70) or off a roster legend printed without ballot boxes (57),
      opens on an orphan `?` or `]` left by a line break (51), runs past the end of the
      option row into the following question (35), or picks up a neighbouring ADMIN/ID
      field (26). Importing these would put corrupted or wrong-question text on the tablet,
      so nothing was written. **These are text we still need from you** — see the ask.
    - **74 judgement calls, all on the blue enumerator-instruction line** (never on text a
      respondent hears): the F4 section-144 intro in all seven dialects, the two printed F4
      gates, and the *read one / read all / do not read / select all / receipt / amount*
      directives. The paper prints these inline with the question, so only a fragment or a
      half-directive could be captured, and a half-directive misleads the enumerator more
      than English does. These read English on purpose;
    - **35 rows removed on 27 August** (they start `removed:`). Each one had been carrying a
      *neighbouring* option's translation — see *Update 27 Aug (afternoon)* below. The
      printed papers offer no distinct text for them, so the label was deleted and the
      English renders. **These are text we need from you**, exactly like the 680 above;
  - `accepted` (113) — labels where a flagged paper span was accepted after review;
  - `residual` (301) — labels that *were* imported but still read with a stray quote, an
    unbalanced bracket, a missing full stop or a cut-off ending;
  - `paper-defects` (385) — the defects in the printed questionnaires, listed below;
  - `follow-ups` (6) — work already scheduled on our side, so nobody re-reports it.
  - `translator-worklist-aug21.csv` is the same rows flat, for anyone who prefers a
    spreadsheet-free tool.
- Runtime error messages (the pop-ups an enumerator sees when an entry is out of range) stay
  **English** in this build. They were out of scope. A translator sheet for them — roughly
  590 strings — is available on request.

## Defects in the printed questionnaires — ASPSI's to fix

None of these is fixable in the software; they are properties of the Aug-21 PDFs.

1. **F1-Tagalog, page 1, paragraph 2** prints *F3's* English coverage sentence above the
   correct F1 Tagalog text. English-side error in the paper; the build is unaffected.
2. **F3-Hiligaynon's consent page is an older English version** — it carries an extra
   privacy clause, it is missing the Php 100 token-of-appreciation sentence, and the
   "Nothing bad will happen…" paragraph is absent. Two consent paragraphs therefore stay
   English on the tablet in Hiligaynon.
3. **F3-Tagalog's header still reads `06/05`.** It is the only paper in the pack that was
   not re-stamped. The tools stamp `08/21/2026` for every language regardless, so this is
   cosmetic on the paper only — but the next issue should carry the right date.
4. **The Waray F4 paper's question numbers run one behind the tool's** on Q27, Q28, Q29 and
   the result-of-visit grid. Seven rows were left English rather than risk attaching a
   translation to the wrong question. Ten further Waray/Hiligaynon values still carry a
   printed question number inside the answer text.
5. **Repeated words and internal inconsistency.** Hiligaynon F1 option 4 of Q10.1–Q35.1
   repeats `sa masunod`; Ilocano F3 Q54/Q55/Q57 repeat `kangrunaan a`; Waray F3 Q16 prints
   its whole question twice; Bicolano and Hiligaynon F3 spell the same rating scale two ways
   (`Kotento` / `Kontento`) within one page.
6. **Missing sentence-final punctuation** in Bicolano F1, Bicolano F4 and Ilocano F3/F4
   paragraphs; one Bicolano F1 paragraph also stops short of what the English says.
7. **English reprinted instead of a translation** — **F1 10, F2 77, F3 99, F4 44 places**,
   where the paper repeats the English sentence under the question rather than giving the
   dialect. The heaviest single papers are F2-Bicolano (57 of F2's 77), F3-Cebuano (42),
   F3-Tagalog (37) and F4-Bicolano (26); F1's ten are Bicolano 5, Bisaya 2, Cebuano 3.
   Nothing can be imported from those cells.

The four worth fixing first, because they are visible to a respondent or a reviewer, are
**1, 2, 3 and 4**.

## Not in this build

- **Runtime error messages** stay English (see *Attached*). Separate request.
- **F2 chrome beyond the consent screen** — headings, buttons and the raffle block are still
  English by design. Only the questions, the option text and the Part-I consent paragraphs
  were in scope.
- **F3 questions 115.1 and 115.2** (the "other items in the bill" matrix) keep English row
  labels in all seven dialects: the papers print those rows in the English column only. The
  fix is on our side — building each row label from its translated parts — and is scheduled,
  not blocked on ASPSI.
- **DOH's Aug-21 *Review of Deliverable 2*.** We read it. It raises **no instrument and no
  translation item** — it is feedback on the manuals — so it has been routed to the manuals
  lane rather than acted on in the tools.

## The ask

1. **Fill in the worklist.** The `worklist` sheet is the one that matters; each row has the
   English, the dialect and the reason. A returned row goes straight into the next build —
   nothing needs to be re-typed into the PDFs first.
2. **Fix defects 1–4 in the next issue of the papers**, and re-issue those four files. We do
   not need a full re-delivery for them.
3. **The `held` sheet — two different asks, split by the `flags` column.**
   - The **680 rows that start `held:`** are extraction failures, not preferences: the
     printed span could not be lifted off the paper cleanly, so we hold no trustworthy text
     for them. Please treat them like `worklist` rows and **supply the correct dialect
     text** — do not approve the printed span, because what we read off the page is
     truncated, doubled, or belongs to the neighbouring question. Where the row's reason
     points at the paper itself (the Hiligaynon `sa masunod` stutter, the ballot-box-free F4
     roster legends), fixing the paper fixes the row.
   - The **35 rows that start `removed:`** are the labels deleted on 27 August because they
     were carrying a neighbouring option's translation (*Update 27 Aug (afternoon)*). Treat
     them exactly like the 680: **we need the dialect text**, and until it arrives the
     English option renders.
   - The **74 rows that start `renders English:`** are our judgement, and comment is
     welcome: enumerator directives, the two printed F4 gates and the F4 section-144 intro
     read English on the blue instruction line because only a fragment of the printed
     dialect version was capturable. If your translators would rather see that fragment, or
     can give us the directive as a standalone line, say so and we will import it.

Questions on any row: reply with the instrument, dialect and key from the worklist — those
three identify a label exactly.

---

## Update 27 Aug (afternoon)

A review of the whole translated branch, run after the four builds above went out, found one
defect **class** that our automated checks could not see — and it is the one that matters
most, because it is invisible on screen. On a handful of multiple-choice questions an option
row was carrying the **neighbouring row's** translation. The dialect text reads perfectly
well; it is simply the wrong answer against the code the enumerator taps. Six live instances
were found and corrected, and every one of the four tools was rebuilt from its pre-import
baseline with the corrected reader — nothing was patched by hand.

### What a tester should be running now

| Instrument | Version | Deployed | How testers get it |
|---|---|---|---|
| **F1 Facility Head Survey** | **v4.1.1** | 2026-08-27 | CSEntry → remove the app, then Add Application → from CSWeb |
| **F2 Healthcare Worker Survey** (web) | spec **2026-08-27-m5** (build `ce05b931`) | 2026-08-27 | reload the site; the version stamp is in the header |
| **F4 Household Survey** | **v3.2.3** | 2026-08-27 | CSEntry → remove the app, then Add Application → from CSWeb |
| **F3 Patient Survey** | **v6.1.2** | 2026-08-27 | CSEntry → remove the app, then Add Application → from CSWeb |

Still the development channel, and the PSA-submitted set (F1 v3.1.5 / F2 v3.0.0 / F3 v6.0.2 /
F4 v3.1.3) is still untouched. Again: no question codes, no option values and no saved answer
changed — only the wording on screen. F2 keeps the same `2026-08-27-m5` stamp because a
translation-only redeploy does not bump it; the build reference `ce05b931` is what identifies
the current one.

### What was corrected

| Instrument | Dialect | Question | What it had been showing |
|---|---|---|---|
| F3 | Cebuano | the *Where did you hear this?* option list, on Q36 / Q75 / Q100 / Q117 / Q120 / Q125 / Q153 | the **LGU / Barangay** option was printing the **Legislation** option's Cebuano text (`Balaod`). Corrected to the paper's own `LGU/Barangay` wording |
| F4 | Tagalog | Q45.2 *Why is the household not registered?*, options 2 and 3 | both were printing option 1's text (*Mahirap magparehistro*). Deleted — the English options render |
| F4 | Ilocano | Q45.2, option 8 | was printing option 7's text. Deleted |
| F4 | Waray | Q128 and Q134 *(understanding of the benefit package)*, option 5 | both were printing option 3's text. Deleted |
| F1 | Bicolano / Tagalog | Q83 *reasons not received* option 3, Q45 *performance indicators* option 4 | each was printing the option above it. Deleted |
| F2 | Waray | the *City / LGU standard referral form* option | carried the *DOH standard referral form* translation glued onto its end. Repaired |

Where the row is marked **deleted**, the printed questionnaire carries no distinct
translation for it — its only candidate on the page *is* the neighbouring option's words. An
English option a respondent can read beats a dialect option that repeats another answer, so
the label was removed and the English shows until you send us the text. All 35 such rows are
in the workbook's `held` sheet with a `removed:` reason, and they are part of the ask above.

### What stops it happening again

The importer now refuses, permanently, to write a value list in which two different answers
would render the same string — the exact shape this class produces. The reader also learned
to recognise the two page layouts that cause it (a two-column option grid that prints both
English rows before both translations, and a page that repeats one translation across rows).
**80 more rows** moved out of the import and onto your worklist as a result: they are rows
whose only candidate belonged to a neighbour, and they now reach you as work rather than the
tablet as a wrong answer.

### Effect on the attached workbook

The workbook was regenerated from the corrected reader on 27 August: **13,276 rows**, seven
sheets. Three coverage cells read one point lower than the table above because the deleted
rows are no longer counted — F3-Bicolano 66 → **65**, F4-Hiligaynon 59 → **58**, F4-Waray
71 → **70** (the coverage table earlier in this note already shows the corrected figures). A
label that renders the *wrong* option was never real coverage.

The counts in *Attached* are the regenerated ones. Nothing else in this note changes.
