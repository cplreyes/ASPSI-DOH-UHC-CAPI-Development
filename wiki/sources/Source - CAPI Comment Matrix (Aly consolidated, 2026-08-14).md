---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Email-Ingest-2026-08-25/CAPI_Comment-Matrix_2026-08-14.docx]]"
date_ingested: 2026-08-25
tags: [doh-review, xylee, comment-matrix, f1-facility, f2-hcw, f3-patient, f4-household, ingest-batch-aug25]
---

# Source - CAPI Comment Matrix (Aly consolidated, 2026-08-14)

**This is Aly's consolidated bug-report document** — the Google Doc that has been cited across the project
as the source of the **#1005–#1067** wave but was never archivable, because the Drive connector could not
reach it. Shared to Carl's personal Gmail 2026-08-14 by Aly (`help.aspsi.doh.uhc.survey2@gmail.com`),
downloaded and archived **2026-08-25**. The header reads *"From Ms. Xylee's comments"* — so the content is
XJ's review, consolidated by Aly.

> [!important] Not new findings — this closes an archival gap, not a work gap
> `deliverables/DOH-Reviews/DOH-Comments-and-Pretest-Findings_Fixes-Filled_2026-08-14.xlsx` already exists and
> describes itself as a *"Row-for-row companion to Aly's Google [Doc]"*, with each sheet noting *"Rows mirror
> Aly's consolidated document"*. Same four columns, same date, matching counts (**95 xlsx data rows**
> vs ~94 status values in the doc). **The findings were already triaged and shipped.** What changed on
> 2026-08-25 is that the source document itself is now in `raw/` rather than living only in Drive.

## Shape

Four instrument sections (F1 / F2 / F3 / F4), 8 tables, columns **Question · Comments · Category of bug · Fixes**.

| Status in the Fixes column | Count |
|---|---|
| Fixed in build | 81 |
| Not applicable | 8 |
| **Parked — DOH decision** | **3** |
| Already in build | 2 |

## The 3 parked rows are one issue, repeated per instrument

All three read *"**All question text appears to be displayed twice**. In addition, the section titles,
introductory statements, and instructions..."* — the repeating-text problem.

> [!note] Status has moved since this document was written
> The matrix is dated **2026-08-14**. The repeating-text fix shipped as **F1 v3.0.1 on 2026-08-19**
> ("each question now appears once, in the language you've set; form rows show short tags instead of
> repeating the full English question"), with F3/F4 twins. So *"Parked — DOH decision"* was accurate when
> written and is **stale now** — don't re-open it from this document. Tester follow-ups on the same theme
> were still arriving as GitHub comments on 08-20 (#1306 F1, #1307 F4, #1309 F3), which is the thread to
> check rather than this row.

## The open gap it confirms

Two F3 rows are flagged **"Missing option definitions"** and are *not* marked fixed:

- **Q54** — "Who is your main primary care provider?"
- **Q86** — "Which of the following happened during the patient's most recent visit?"

> [!warning] **CORRECTED 2026-08-25 — these are NOT open in the CAPI.**
> An earlier reading of this note said both rows needed definition text from ASPSI before they could be built.
> **That was wrong.** Verified in `F3/generate_dcf.py`: **Q54** carries inline definitions from **#787 (R5)**
> and **Q86** from **#1052 (2026-08-04)** — the Q86 text matches the reviewer's requested wording verbatim.
> ASPSI told DOH *"the CAPI version has been corrected"* and that is accurate
> ([[Source - Survey Tools Comment Matrix (July 30 FINAL)]]).
>
> **These rows describe the PAPI questionnaire, not the CAPI.** Any remaining gap is on the paper tool and is
> not in Carl's lane.

Related: [[Source - Updated Survey Instruments (2026-08-17)]] · [[Source - DOH Meeting on Project Updates (2026-08-17)]]
