---
type: source-summary
source: "Google Drive folder 'PSA_CAPI Screenshots' (id 1lHrnFSSB-dfZ2lGkk75L9ZLJCCOe0XEg, owner spprt.aspsi.doh.uhc.survey2@gmail.com, created 2026-07-21) → [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/PSA-CAPI-Screenshots-2026-07/]]"
date_ingested: 2026-07-21
tags: [capi, screenshots, psa-ssrcs, doh-review, papi-vs-capi, f1-facility, f2-hcw, f3-patient, f4-household, evidence-pack]
---

# Source — PSA CAPI Screenshots (2026-07)

A Drive folder of **four PDF exports of the live CAPI interface — one per instrument — rendered screen by screen**. Owned by the ASPSI support account (`spprt.aspsi.doh.uhc.survey2@gmail.com`), assembled 2026-07-21. Carl surfaced it as *"the basis of Xylee's review"* — and that is confirmed: these are exactly the **CAPI interface screenshots** that (a) **PSA required** for statistical clearance and (b) **Xylee Javier's screenshot-based PAPI-vs-CAPI review** was built against.

> [!note] Where it came from
> The folder lives under Carl's UP account (`clreyes6@up.edu.ph` / `/u/1/`); the connected Drive account is `carlpatricklreyes@gmail.com`, which can read it (it's shared through the ASPSI support account). The four files are **image-heavy PDFs** (8–9 MB for F1/F3/F4) — the Drive connector streams the small one fine but the large three expire the session (see archival status below).

## The two jobs this set does

1. **PSA-required CAPI/CAWI interface screenshots.** The PSA SSRCS completeness check (Transaction 26SSRCS06-068, 2026-06-09) explicitly asked for CAPI/CAWI interface screenshots as part of statistical clearance (see [[Source - PSA SSRCS Completeness Check (26SSRCS06-068 2026-06-09)]]). This folder is that deliverable.
2. **The basis of XJ's review.** [[Xylee Javier (XJ)]] reviewed the CAPI **from screenshots, without test-environment access** (the framing behind the whole triage — see [[Analysis - XJ PAPI-vs-CAPI Reviews vs Current CAPI Build]]). This is the screenshot set her PAPI-vs-CAPI comparison sits on top of. It directly explains the recurring "not observed / no screenshot" findings — they are gaps in *this* capture, not in the build.

## The four files

| File (Drive title) | Instrument | Size | Pages | Binary in `raw/`? |
|---|---|---|---|---|
| `CAPI_Form No. 1 … Facility Head Survey Questionnaire.pdf` | **F1** Facility Head (CSPro) | 8.3 MB | 80 | ✅ `CAPI-Form1-Facility-Head-F1.pdf` |
| `CAPI_Form No. 2 … Healthcare Worker Survey Questionnaire.pdf` | **F2** HCW (PWA) | 1.24 MB | 33 | ✅ `CAPI-Form2-Healthcare-Worker-F2.pdf` |
| `CAPI_Form No. 3 … Patient Survey Questionnaire.pdf` | **F3** Patient (CSPro) | 7.75 MB | 102 | ✅ `CAPI-Form3-Patient-F3.pdf` |
| `CAPI_Form No. 4 … Household Survey Questionnaire.pdf` | **F4** Household (CSPro) | 9.4 MB | 87 | ✅ `CAPI-Form4-Household-F4.pdf` |

**Two different capture styles**, which itself explains several review comments: **F2** is a *rendered export of the PWA* (vector, has a text layer, one page per screen). **F1 / F3 / F4** are *real Android tablet screenshots of CSEntry* — image-only, no text layer, **two device screens side-by-side per page**, complete with the Android status bar, the CSEntry title bar (`FacilityHeadSurvey` / `PatientSurvey` / `HouseholdSurvey`, edit / search / ⋮ icons), the ‹ › field-navigation arrows, and the Android nav bar.

> [!warning] Numbering differs from XJ's review docs
> This set numbers **Form 1 = Facility, 2 = HCW, 3 = Patient, 4 = Household**. XJ's review `.docx` files number them **1 = HH, 2 = Patient, 3 = Facility, 4 = HCW** ([[Source - PAPI vs CAPI Household Review (XJ 2026-07)]] et al.). Same four instruments, different file-prefix order — don't cross-wire them.

## What Form 2 (HCW) actually shows — viewed 2026-07-21

Verified by rendering the saved F2 PDF (the one binary in hand): **33 pages**, a clean capture of the **F2 PWA at v2.1.0 · spec 2026-04-17-m1**. Each screen shows the real interface — title bar with **Sync / Save Draft**, a **"SECTION n OF 6"** progress bar + hamburger navigation, section intros, and live controls (radio lists, Last/First/Middle name boxes, Year(s)/Month(s) inputs, red-asterisk required marks, "Other (specify)" options). Sections captured: **A** Profile · **B** UHC Awareness · **C** YAKAP/Konsulta · **D** NBB/ZBB · **E** BUCAS/GAMOT · **F** Referrals & Satisfaction · **G** KAP · **H** Task Sharing · **I** Facility Support · **J** Job Satisfaction.

**It corroborates XJ directly:** the capture jumps **Q5 → Q7** (Q6 is not shown) — which is precisely her *"Q6 has no screenshot"* comment. So that finding is a **screenshot gap, not a missing field** (bucket A/C), confirmable straight from this file. The **spec date 2026-04-17** also confirms XJ's "reviewing April screenshots" framing.

## What F1 / F3 / F4 show — viewed 2026-07-21

CSEntry captures on an Android tablet. All three open **identically**: screen 1 is the **12-digit Questionnaire Number**, labelled verbatim `Questionnaire Number (12-digit: RR-PP-MMM-FF-CCC)`; screen 2 is the first classifier — **F1** `Classification` (UHC IS / Non-UHC IS), **F3** `Type of Patient` (Outpatient / Inpatient), **F4** `Classification` (UHC IS / Non-UHC IS). Three things these captures settle against XJ's comments:

- **The 12-digit QN is the very first field**, with its structure spelled out on screen — the concrete artifact behind her "9-digit PAPI vs 12-digit CAPI" comment ([[Questionnaire Numbering Convention]]).
- **Navigation controls are plainly visible** (‹ › arrows + ⋮ menu in the CSEntry chrome). Her *"navigation controls not shown"* is an observation gap — they're in the captured chrome, just never called out.
- **The repeated question text is real, visible, and uniform across all three CSPro instruments.** Every screen renders the label twice — `Classification` as the block heading *and* again as the field label (F1 and F4), `Type of Patient` likewise (F3). This is exactly her *"question text displayed twice"* finding, confirmed on the first capture of each instrument, and it is the CSPro prompt-plus-field render (a presentation/bucket-D item, not a data problem) — so any fix is a shared generator change, not a per-instrument patch.

> [!info] Relevance to the scheduled remediation
> The bucket-C answer in the triage is "supply current screenshots + a test login." This folder is the **April-spec** screenshot pack; the post-pretest remediation should refresh it to a **current-build** capture (and pair it with the skip/validation matrix + test account). See the scheduled milestone in [[Analysis - XJ PAPI-vs-CAPI Reviews vs Current CAPI Build]].

## Archival status (raw/)

`raw/PSA-CAPI-Screenshots-2026-07/` — **complete: 4 of 4 archived and verified** (2026-07-21). Every byte-size matches the Drive original exactly:

- ✅ **F1** `CAPI-Form1-Facility-Head-F1.pdf` — 8,293,716 B, `%PDF-1.7`, 80 pp (via local Downloads).
- ✅ **F2** `CAPI-Form2-Healthcare-Worker-F2.pdf` — 1,236,984 B, `%PDF-1.4`, 33 pp (pulled via the Drive connector).
- ✅ **F3** `CAPI-Form3-Patient-F3.pdf` — 7,751,601 B, `%PDF-1.7`, 102 pp (via local Downloads).
- ✅ **F4** `CAPI-Form4-Household-F4.pdf` — 9,445,088 B, `%PDF-1.7`, 87 pp (via local Downloads).

> [!bug] Connector limitation worth remembering
> The Drive connector's `download_file_content` **reliably expires the MCP session on the 8–9 MB image PDFs** (three retries each) while metadata calls and the 1.2 MB F2 succeed; `read_file_content` returns **empty** for them (image-only, no server-side text layer). Large Drive binaries therefore need the **local Downloads route**. Locally, PyMuPDF (`fitz`) renders and reads them fine — `pdftoppm`/poppler is not installed on this machine, so the Read tool cannot open PDFs directly.

## Cross-references

- [[Analysis - XJ PAPI-vs-CAPI Reviews vs Current CAPI Build]] · [[Source - PAPI vs CAPI Household Review (XJ 2026-07)]] · [[Source - PAPI vs CAPI HCW Review (XJ 2026-07)]] · [[PAPI-to-CAPI Translation Review Criteria]] — the review these screenshots underpin.
- [[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19]] — the parked-then-scheduled posture governing the response.
- [[Source - PSA SSRCS Completeness Check (26SSRCS06-068 2026-06-09)]] — the PSA ask these screenshots satisfy.
- [[Source - Annex F1 Facility Head Survey Questionnaire]] · [[Source - Annex F3 Patient Survey Questionnaire]] · [[Source - Annex F4 Household Survey Questionnaire]] — the paper (PAPI) side each CAPI capture is compared against.
- [[F2 Admin Portal]] · [[Source - Dictionary Names Labels and Value Sets]] — the F2 PWA and the CSPro dictionaries the captured screens render.
