# Email draft — Aug-21 translations: status note + translator worklist

Send from **clreyes6@up.edu.ph** (ASPSI comms address). This is a NEW email, not a reply on the
"ASPSI DOH UHC Survey Yr 2_Deliverable 2 Submission" thread — that thread carries DOH
(pmsmd@doh.gov.ph, Paita, Villarante, Ausisa) and the worklist is ASPSI-internal work, not a DOH
submission. Recipients below are the ASPSI-side addresses lifted from that thread; trim as you see fit.

**To:** cjrocamora@gmail.com (Juvy Chavez-Rocamora); spprt.aspsi.doh.uhc.survey2@gmail.com (Aidan); mcsilva@up.edu.ph (Myra Silva-Javier)
**Cc:** paclaro@up.edu.ph; fffaderogao@up.edu.ph; merlynepaunlagui@gmail.com; tdemaisip@gmail.com; marrizmojado@gmail.com; xyleej@gmail.com; aspsi.doh.uhc.survey2@gmail.com; assst.aspsi.doh.uhc.survey2@gmail.com; aid.aspsi.doh.uhc.survey2@gmail.com; help.aspsi.doh.uhc.survey2@gmail.com; guide.aspsi.doh.uhc.survey2@gmail.com
**Subject:** UHC Survey Yr 2 CAPI — Aug-21 translations are in all four tools; translator worklist attached (13,276 rows)

**Attachments (3):**
1. `Aug-21-translations-status-for-ASPSI-2026-08-27.docx` — the status note (what shipped, coverage, paper defects, the ask)
2. `translator-worklist-aug21.xlsx` — 13,276 rows, seven sheets (`worklist`, `held`, `accepted`, `residual`, `paper-defects`, `follow-ups`, `summary`)
3. `translator-worklist-aug21.csv` — the same rows flat, for anyone without Excel

---

Dear Juvy, Aidan and Myra,

Good afternoon. The translations from ASPSI's revised Deliverable 2 (the 28 Aug-21 translated questionnaires plus the four Aug-21 English masters) are now in all four data-collection tools, as of today:

- F1 Facility Head Survey — v4.1.1
- F2 Healthcare Worker Survey (web) — spec 2026-08-27-m5
- F3 Patient Survey — v6.1.2
- F4 Household Survey — v3.2.3

The English wording was first aligned to the Aug-21 masters, then each of the seven dialects was imported from its own paper. Translation coverage rose in every one of the 28 instrument × dialect combinations (for example F3 Hiligaynon 43% → 57%, F1 Tagalog 66% → 81%; the full table is in the attached note). The enumerator notes and the informed consent form now read in the interview language as well. No question codes, option values or saved answers changed — only the wording shown on screen — and the set submitted to PSA remains frozen and untouched. These are development-channel builds for UAT; the testers have already been given the update instructions in the UAT channels.

What is still English is, almost entirely, text that the printed questionnaires do not carry a translation for. The attached workbook lists every such cell so your translators can fill them — that is the request of this email:

1. **Fill in the `worklist` sheet** (11,682 rows: the English text, the instrument, the dialect and the reason). A returned row goes straight into the next build; nothing needs to be re-typed into the PDFs first.
2. **The `held` sheet** (789 rows): the rows marked `held:` (680) and `removed:` (35) also need the dialect text — please do not simply approve the printed span for those, because what could be read off the page is truncated, doubled, or belongs to the neighbouring question. The 74 rows marked `renders English:` are our judgement on the blue enumerator-instruction line; comment is welcome.
3. **Four defects in the printed papers** that only ASPSI can fix, and that are visible to a respondent or reviewer: (a) F1-Tagalog page 1 prints F3's English coverage sentence; (b) F3-Hiligaynon's consent page is an older English version, so two consent paragraphs stay English on the tablet; (c) F3-Tagalog's header still reads 06/05; (d) the Waray F4 paper's question numbers run one behind on Q27–Q29 and the result-of-visit grid. Re-issuing those four files is enough — no full re-delivery is needed. Three further, lower-priority paper issues are described in the note.

If the returned rows could reach me by **[Friday, 4 September]**, they can be built and re-deployed before the training week of 7 September. Partial returns are fine — a sheet per dialect, or per instrument, can go in as it arrives.

One item for your awareness, described in the note under "Update 27 Aug": a review after this morning's builds found a small number of multiple-choice options that had been carrying the neighbouring option's translation (six live instances, all corrected today, and a permanent check now prevents the class). Where the paper offers no distinct text for such a row, the English option is shown until your translators supply one; those 35 rows are in the `held` sheet as `removed:`.

For questions on any row, the instrument, dialect and key columns identify a label exactly. Runtime error messages (the out-of-range pop-ups) remain English in this build; a separate sheet of roughly 590 strings is available if ASPSI wants those translated too.

Maraming salamat.

Carl Patrick Reyes
CAPI Developer, DOH UHC Survey Year 2
clreyes6@up.edu.ph

---

*Before sending:* confirm the return date in brackets; the note's "What shipped" table already says 2026-08-27. The UAT-channel posts and the #capi-scrum announcement are already out (links in the patch notes).
