---
type: deliverable
kind: survey-manual-section
audience: ASPSI / DOH-PMSMD / ADB / SJREB reviewers (stakeholder level)
prepared_by: Carl Patrick L. Reyes
source_doc: DOH UHC Year 2_Survey Manual Apr 28.docx
date_drafted: 2026-05-02
status: draft-for-review
related_task: E7-DOC-001
supersedes_section: "Guidelines on installing/using of CSPro" (legacy SPEED 2023 / Dropbox text)
companion_to: CSPro-Section-Draft_2026-04-29.md (enumerator-level walkthrough; complementary appendix material)
tags: [survey-manual, capi, cspro, pwa, csweb, stakeholder, e7]
---

# Survey Manual — Data Collection Technology and Processes (Stakeholder Draft)

> **Purpose of this section.** Provides the stakeholder-level description of the technology, data flows, and quality processes that underpin field data collection for the UHC Survey Year 2. It is the process-and-architecture narrative that DOH-PMSMD, ADB, SJREB, and ASPSI senior reviewers expect to see; it does not replace enumerator step-by-step instructions, which appear in [the companion enumerator draft](./CSPro-Section-Draft_2026-04-29.md) and field appendices.
>
> **Where it goes in the master manual.** Substitutes for the existing legacy "Guidelines on installing/using of CSPro" sub-section under *Instructions for the Administration of the Questionnaire* (currently still references the 2023 SPEED Dropbox model, which does not apply to UHC Year 2). The enumerator step-by-step walkthrough remains as the granular procedural complement.

---

## 1. Overview

The UHC Survey Year 2 uses a **digital-first data-collection model** anchored on industry-standard tooling, with a unified backend pipeline that feeds the same quality-control and analysis processes regardless of which instrument captures the data.

Two complementary capture channels are deployed:

- **Computer-Assisted Personal Interviewing (CAPI)** — for interviewer-administered instruments where the enumerator is physically present with the respondent (Facility Head, Patient, Household). Built on **CSPro / CSEntry**, the open-source data-collection platform maintained by the **US Census Bureau** since 1996 and used in over 160 countries (DHS, MICS, national censuses, WHO surveys).
- **Self-administered web survey (Progressive Web App, PWA)** — for the Healthcare Worker instrument, where respondents complete the questionnaire on their own device through a secure, role-aware web form. Implements the same data-quality, audit, and synchronization disciplines as CSPro, adapted for unsupervised completion and tablet/phone form factors.

Both channels write into a unified ASPSI-managed backend so that every completed case — whether captured on a CAPI tablet by an enumerator or self-completed by a healthcare worker — passes through the same Approved / On-Hold review workflow, the same logic and consistency checks, and the same aggregated dashboards used by the data manager and field supervisors.

| Survey form | Mode | Capture tool | Backend / sync target |
|---|---|---|---|
| **F1 – Facility Head** | Interviewer-administered, on-site | CSPro / CSEntry on Android tablet | CSWeb server |
| **F3 – Patient** | Interviewer-administered, on-site | CSPro / CSEntry on Android tablet | CSWeb server |
| **F4 – Household** | Interviewer-administered, on-site | CSPro / CSEntry on Android tablet | CSWeb server |
| **F2 – Healthcare Worker** | Self-administered (online) with paper-encoder fallback | Custom Progressive Web App (PWA) | Cloudflare Worker → Google Apps Script → Google Sheets (project mailbox) |

> **Note on choice of stack.** CSPro is the standard for facility/patient/household CAPI in international health surveys; selecting it for F1/F3/F4 keeps UHC Survey Year 2 aligned with DHS, MICS, and WHO methodology. The PWA stack for F2 was adopted because the F2 questionnaire is **self-administered**, distributed asynchronously through facility communication channels, and has different respondent-side ergonomics than an enumerator-mediated CAPI session — the PWA's web-form delivery, per-respondent tokenized links, and offline-capable form behaviour fit that workflow more cleanly than a tablet-bound CSPro app would.

## 2. End-to-end data flow

### 2.1 Facility Head, Patient, and Household (F1, F3, F4) — CAPI

The CAPI flow has five phases:

1. **Tablet preparation** — ASPSI's CAPI development team pre-configures every survey tablet before it leaves Los Baños: latest CSEntry version installed, the three CAPI applications (FacilityHeadSurvey, PatientSurvey, HouseholdSurvey) deployed with their data dictionaries, and the synchronization endpoint pointed at the project's CSWeb server. Enumerators receive ready-to-use devices from their Survey Team Leader (STL); they do not download or update applications themselves.
2. **In-field capture** — at the facility (F1) or with the respondent (F3, F4), the enumerator opens the relevant CSEntry application, starts a new case using the case identifier assigned by the STL, and works through the questionnaire. Skip-logic, range checks, and consistency rules built into the data dictionary fire as the enumerator advances, preventing common entry errors at the point of capture. Each case automatically captures a GPS reading and a single end-of-interview verification photograph, both used for audit and field-edit quality control.
3. **End-of-day synchronization** — when the survey team has internet access (Wi-Fi or mobile data), every tablet uploads its completed cases to the project's central CSWeb server. The protocol requires synchronization **before 10 PM each day**, so that field progress is visible to ASPSI by the next morning. Cases that fail to upload remain stored on the tablet and re-attempt on the next sync; no data is lost if connectivity is intermittent.
4. **Server-side reception** — CSWeb stores every received case in its relational data store, exposes the live count of completed cases on the project dashboard, and writes a sync log entry the field supervisor can use to reconcile against the enumerator's daily diary. Each case is tagged with its source tablet, sync timestamp, and enumerator identity.
5. **Review and analysis flow** — once cases land on CSWeb, they enter the Approved / On-Hold workflow described in §4 below.

### 2.2 Healthcare Worker (F2) — Self-administered PWA

The F2 flow has four phases:

1. **Distribution** — for each sampled facility, the assigned facility contact person receives a per-facility survey link, which they distribute to healthcare workers through the facility's primary communication channel (Viber, Facebook Messenger, or email). In facilities with poor connectivity, paper questionnaires are dropped at the start of the facility visit day and collected by the enumerator before departure for later encoding through the same PWA via the **paper-encoder workflow** (operated by ASPSI staff using the same instrument so that the data lands in the same store with a `source_path` flag distinguishing self-completed from staff-encoded).
2. **Completion** — the healthcare worker opens the link on their phone, tablet, or workstation, reads the embedded informed-consent screen, and completes the questionnaire at their own pace within the **3-day completion window** following first access. The PWA enforces the same skip-logic and validation rules as CSPro CAPI, plus an auto-save mechanism that lets the respondent pause and resume from the same device.
3. **Submission and backend pipeline** — on submit, the PWA posts the response through a Cloudflare Worker (which validates the token, stamps a timestamp and submission GPS, and signs the request to the Apps Script backend) and finally lands the row in the project Google Sheets store under the ASPSI mailbox.
4. **Review and analysis flow** — F2 responses join the same Approved / On-Hold review pipeline used for F1/F3/F4 cases, with the data manager running the same logic and consistency checks against the unified store.

### 2.3 Unified analysis-ready store

After review, F1/F3/F4 (CSPro) and F2 (PWA) data converge into a single analysis dataset. CSPro data is exported from CSWeb in standard statistical formats (SPSS, Stata, CSV); F2 PWA data is exported from Google Sheets. The data manager harmonises field names and value sets according to the codebook so that downstream tabulation, weighting, and analysis can treat all four instruments as one coordinated dataset linked through shared identifiers (facility code for F1↔F3, household-line linkages for F4).

## 3. Built-in data quality controls

The following controls fire **at the point of capture**, before any data leaves the device. They are the first and most cost-effective layer of data quality, replacing the manual error-checking that paper-based surveys leave to data-entry clerks.

| Control | What it prevents | Applied to |
|---|---|---|
| **Skip-logic enforcement** | Inconsistent routing through the questionnaire (e.g., asking a follow-up question to respondents who answered "No" to its gate) | All four instruments |
| **Range / format validation** | Out-of-range numerics, malformed dates, invalid PSGC codes | All four instruments |
| **Hard / soft / gate validations** | Hard: blocks progress on impossible values; Soft: warns and asks for confirmation; Gate: terminates the interview when a critical eligibility criterion fails (e.g., respondent age below 18) | All four instruments |
| **Cross-field consistency rules** | Logical contradictions across fields (e.g., a respondent whose tenure exceeds their age) | All four instruments |
| **Required-field enforcement** | Missing answers on items that are not legitimately skippable | All four instruments |
| **Geographic-cascade lookups** | Mismatched region/province/city/barangay combinations (PSGC validity is enforced from the PSA 1Q 2026 dataset) | F1, F3, F4 (CSPro shared lookup) |
| **Auto-captured metadata** | Manual transcription errors on enumerator/timestamp/GPS metadata | All four instruments |
| **Verification photograph** | Interviewer-presence fraud and inability to audit visit context | F1, F3, F4 |

## 4. Server-side review and quality control

Once cases reach the central servers, ASPSI's data team runs a layered review:

- **Initial review per case (Approved / On-Hold).** Every completed interview is classified **Approved** (passes the integrated checks and is ready for the analysis dataset) or **On-Hold** (requires clarification or correction by the enumerator). On-Hold cases are returned to the enumerator with a note explaining what needs to be reviewed; the case can be amended and re-submitted, after which it re-enters the review queue.
- **Logic and consistency checks (≥ 2× per week).** In addition to the in-CAPI / in-PWA logic, the data manager runs supplementary frequency tabulations and cross-tabulations to surface issues that only become visible across the dataset as a whole — outliers in continuous variables, illogical combinations missed by within-form rules, suspiciously short or long interview durations, anomalous frequency distributions, and missing-value patterns.
- **Suspicious-data follow-up.** When the data manager flags a case, the field supervisor cross-references the enumerator's diary; if the discrepancy persists, the respondent is contacted for clarification (subject to consent and the same SJREB-approved contact procedures used during the original interview).
- **Random site visits by the consulting team.** The ASPSI consulting team conducts random site visits during fieldwork to verify that data-collection protocols are being followed and interviews conducted according to procedure.
- **Final batch cleaning.** After all field interviews are complete and all server records are tagged Approved, the dataset undergoes a second pass of batch-level cleaning to identify extreme values that only become apparent at the aggregate level. This is the last gate before the dataset is released to analysis.

## 5. Verification artifacts and audit trail

Every case carries a non-tamperable audit trail that supports both QC and post-survey defensibility of the dataset:

- **Case identifier** — a unique numerical ID assigned per the questionnaire-numbering scheme (see *Questionnaire Number* sub-section); STLs preassign respondent-number ranges to enumerators to prevent collisions.
- **Enumerator / Survey Team Leader identity** — captured automatically with each case.
- **Timestamps** — start, end, and (for F2) submission timestamps are stamped server-side, not by the enumerator.
- **GPS coordinates** — for F1/F3/F4, captured automatically at the interview site; for F2 PWA self-administered cases, submission-time GPS is captured (with respondent consent disclosure on the consent screen).
- **Verification photograph** — for F1/F3/F4 (one per case), per the SOP-defined content (e.g., facility signage, consent sheet, respondent setting) — used as evidence of interviewer presence and visit context, not for respondent identification.
- **AAPOR disposition code** — first-visit and final-visit dispositions captured separately for response-rate accounting and for distinguishing real refusals from temporary unavailability.
- **Audit log** — every status change (case created, accepted, on-hold, re-approved) is recorded with timestamp and actor identity; the log is read-only from the field side.

## 6. Synchronization, connectivity, and offline behaviour

The system is designed to tolerate intermittent connectivity, which is unavoidable in a nationwide survey covering Class A municipalities, GIDA areas, and BARMM:

- **Offline-first capture.** Every CAPI tablet stores all in-progress and completed cases locally; the synchronization step is the moment data leaves the device, not a precondition for capturing it.
- **Daily sync expected before 10 PM.** Field supervisors monitor next-morning dashboards to confirm that yesterday's cases have landed; un-synced tablets are escalated within the cluster.
- **Encrypted in transit.** All synchronization runs over HTTPS; on the server side, data is stored on ASPSI-managed infrastructure under access controls described in §7.
- **Retry logic.** Failed sync attempts retry on the next connectivity window without enumerator intervention. Cases are not deleted from the tablet until sync confirmation.
- **F2 PWA equivalent.** For respondents on flaky connections, the PWA auto-saves locally and submits when connectivity returns; respondents see an explicit "submitted" confirmation only after the server has acknowledged the case.

## 7. Security, confidentiality, and respondent protection

The data-collection technology is operated under a layered protection model:

- **ASPSI is registered with the National Privacy Commission** under registration number **PIC-000-358-2021** and operates two appointed Data Protection Officers (DPOs).
- **Informed consent** is presented and recorded for every interview, mirroring the SJREB-approved language in Annex H. F2 PWA respondents see the consent text on-screen before the questionnaire is unlocked.
- **Non-Disclosure Undertaking (NDU)** signed by every Survey Team Leader and enumerator — confidential information, fieldwork materials, and data-collection devices may only be used for project purposes.
- **Role-based access** — only the data manager, assistant data managers, and the project's authorised programmer have server-side access to raw individual-level data; field supervisors and STLs see aggregated counts and case-level QC flags, not full responses.
- **Tablet device hygiene** — each device is identified, tracked, and returned to ASPSI at fieldwork close. Lost or damaged devices are reported immediately; the project's CAPI team can revoke a device's sync access if needed without compromising already-uploaded data.
- **At-rest encryption** of the central server's database; periodic backups with retention sufficient to meet DOH and SJREB record-keeping requirements.
- **Auditability of access** — every server-side data-access action is logged for review.

## 8. Roles and responsibilities in the data pipeline

Each role in the data pipeline contributes a defined quality function:

| Role | Quality contribution |
|---|---|
| **ASPSI CAPI development team** | Build and maintain the four data-collection instruments, embedded logic and validation rules, and synchronization infrastructure; provision tablets; resolve technical issues during fieldwork |
| **Data manager (with assistant data managers)** | Review cases for Approved/On-Hold classification; run logic and consistency checks at least twice weekly; coordinate clarifications with field supervisors; run the final batch cleaning |
| **ASPSI consulting team** | Random site visits to verify protocol fidelity; spot-check interview conduct |
| **Cluster supervising RAs** | Field-side oversight; daily reconciliation against the CSWeb dashboard |
| **Survey Team Leaders (STLs)** | Pre-assign questionnaire numbers; supervise enumerators; check completed cases for completeness before sync; cross-reference flagged cases against enumerator diaries |
| **Survey enumerators (SEs)** | Conduct interviews per protocol; capture data accurately within the CAPI/PWA tools; sync daily before 10 PM; respond to On-Hold returns within the agreed window |
| **Facility contact persons (F2)** | Distribute the F2 self-administered survey link via the facility's primary communication channel; confirm distribution with the enumerator on the day of visit |

## 9. Outputs

The data-collection technology produces, per fieldwork window, the following analysis-ready outputs:

- **Per-instrument datasets** (F1, F2, F3, F4) — each in standard statistical formats with full variable labels and value sets matching the dictionary.
- **Linked cross-instrument dataset** — F3 patients linked to their F1 facility; F4 households linked to their F3 patient sampling frame; F2 healthcare-worker responses linked to their facility.
- **Field-progress dashboards** — live during fieldwork (CSWeb dashboards for F1/F3/F4, PWA admin portal for F2), archived at fieldwork close.
- **Audit log** — chronological record of every case's lifecycle from creation to final approval, supporting any post-hoc verification request from DOH-PMSMD, SJREB, or ADB.
- **GPS map artefact** — geographic distribution of completed cases per region, cluster, and instrument, useful for sampling-coverage QA and for the eventual analysis report.
- **Verification photograph corpus** (F1/F3/F4) — held under the same access controls as the response data; used for QC sampling, never for analysis.

## 10. Items pending finalization

These will be confirmed during pretest and locked before main fieldwork; the section above describes the model. Specifics are filled in once protocols are validated:

- **Final case-identifier scheme** — locked in the master manual once decided (see open question 1 in the companion enumerator draft).
- **CSWeb server URL** — replaces the `(CSWeb)` placeholder above once provisioned (Epic 4 backlog).
- **F2 PWA URL** — currently the staging instance at `f2-pwa.pages.dev` (Phase F production cutover landed 2026-05-01).
- **Tablet model and quantity** — pending procurement decision (3-tier specification submitted to ASPSI on 2026-04-29).
- **Final list of instruments installed per tablet** — confirmed by Designer-validated `.dcf` for F1/F3/F4 ahead of training.

---

## Companion materials

- **Enumerator step-by-step walkthrough** — see [`CSPro-Section-Draft_2026-04-29.md`](./CSPro-Section-Draft_2026-04-29.md). Granular procedural complement (step 1 through step 9, in-field actions). Suggested placement: as a separate sub-section or as Appendix B/C of the master manual.
- **CAPI Quick Reference Card** and **CAPI Troubleshooting Guide** — proposed appendices in the same companion file. Designed for printing and inclusion in the enumerator field kit.
