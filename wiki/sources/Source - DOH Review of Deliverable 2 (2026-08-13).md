---
type: source-summary
source: "Google Doc — \"Review of the Deliverable 2 Submission on UHC Survey - Year 2\", DOH HPDPB-PMSMD, sent 2026-08-13 by Chrys Paita (pmsmd@doh.gov.ph); read via the Drive connector 2026-08-25"
url: "https://docs.google.com/document/d/1UauYohVIuB-iI5puedtydkW9xvYsYRHm1P-oC_mfNp4/edit"
date_ingested: 2026-08-25
tags: [doh-review, deliverable-2, capi-manual, tool-guides, training, pretest-report, ingest-batch-aug25, capi-action-required]
---

# Source - DOH Review of Deliverable 2 (2026-08-13)

**DOH's formal review of the Deliverable 2 submission**, sent 2026-08-13 by DOH HPDPB-PMSMD in reply to
ASPSI's 2026-07-30 submission. Recovered 2026-08-25 once the UP mailbox became reachable — it had **no local
record**. The document is a live matrix with two comment columns: *Submission as of July 30* and
*Submission as of August 21*, the second tracking what the revised submission resolved.

> [!important] This is a real review, not a recap — and parts of it land in the CAPI lane
> Unlike the Read.ai meeting summaries, this is a DOH-authored document. The items below are quoted from it.
> **None have been actioned.** Verified status is stated per item.

## CAPI Manual — four items, all open

**1. Five manual titles to be renamed.** DOH quotes p.4 of the CAPI Manual and asks that the titles be
revised *and* matched in the actual manuals:

| Current | DOH asks for |
|---|---|
| Survey Operations Manual | **Survey Manual** |
| Field Enumerator's Manual *(DOH quotes it as "Survey Enumerator's Manual")* | correct the title in the actual manual to match |
| Field Supervisor's Manual | **Survey Field Supervisor's Manual** |
| CAPI Manual *(this document)* | **Survey CAPI Application Manual** |
| Training Manual | **Survey Training Manual** |

> **VERIFIED NOT DONE (2026-08-25).** The list is unchanged at `deliverables/CAPI-Manual/sections/01-introduction.md`,
> and mirrored into `CAPI-Manual.md`, `CAPI-Manual.html`, `CSWeb/capi-portal/src/csweb/capi-manual.html`,
> `CSWeb/landing/docs/capi-manual.html` and the July portal archive — **a rename touches ~6 files**, not one.

**2. End-of-day sync responsibility is unclear.** DOH wants explicit answers to: *who confirms successful
syncing? what should the enumerator do if syncing fails? when is a case considered successfully submitted?*
The manuals already say syncing is required and that cases must not be deleted on failure — the gap is the
confirmation chain.

**3. A consolidated one-page quick reference** covering: login · receive assignment · start case ·
partial save · complete case · sync · failed sync · escalation.

**4. ★ Case-key verification warning — this is an APPLICATION change, not manual text.**
> *"Because the case key is manually entered as a 12-digit identifier, consider adding a prominent
> warning/notification to verify the case key before or ending the interview. An incorrect key could result
> in data being attached to the wrong assignment."*

The 12-digit key is already PSGC-gated at field 1, but that validates *format and geography*, not whether the
enumerator typed the right facility. A wrong-but-valid key silently misattributes a case. Worth deciding
whether this becomes a confirm-screen in F1/F3/F4 or stays a manual instruction.

## Tool Guides — the Aug-21 column reveals an asymmetry

| Guide | July-30 comments | Addressed in the Aug-21 revision? |
|---|---|---|
| Facility Head | 4 items | **all 4 marked resolved** |
| Healthcare Worker | 6 items | **all 6 marked resolved** |
| Patient | 6 items | **only 2 marked resolved** — ToC alignment + point-of-discharge |
| **Household** | 2 items | **column EMPTY** |

The Patient guide's unresolved items include the **Q134 vs Q135 mismatch** (questionnaire marks Q134 as
"For inpatients only", the guide says Q135), consent instructions when an eligible patient cannot sign and
the companion is not an adult, and turnaround time for postponed/incomplete cases. The Household guide's two
open items are replacement rules (extending permission to ineligible/uninterviewable, plus FS approval
turnaround) and sync-failure recovery turnaround.

## Other CAPI-adjacent items

- **HCW consent wording** — replace *"interview"* with *"self-administered survey"*, since F2 is not
  face-to-face. An F2 PWA text change.
- **Enumerator training** — *"consider conducting a live demonstration of the CAPI system with the use of
  practical sample questions."* This independently corroborates the internal item from
  [[Source - ASPSI Subs Zoom Meeting (2026-08-14)]]; it is now a **DOH recommendation**, which raises the odds
  it is actually requested at the Sept 07 TOT. Still not prepared.
- **Questionnaires** — DOH raised two-step-question and code-revision comments but records that ASPSI already
  answered them in the Survey Tools Comment Matrix, noting the structures were retained from Year 1 for
  consistency and were not flagged by SJREB. Cross-references
  `Survey Tools_Comment Matrix (July 30, FINAL).docx`.
- **Pre-testing report** — add a Discussion section, state the site/respondent-selection basis (or attach the
  approved plan as an Annex — see [[Source - Pretesting Plan (2026-07-27)]]), add inclusion/exclusion criteria,
  clarify how the four assessment criteria were measured, and add a
  **Finding → Implication → Recommended Action → Revision Type** matrix.

Related: [[Source - DOH Meeting on Project Updates (2026-08-17)]] (the meeting whose agreements the Aug-21
revision incorporated) · [[Source - DOH Deliverable No. 2 (2026-07-31)]] (the submission being reviewed).
