---
type: deliverable
kind: survey-manual-section
audience: Kidd (ASPSI main RA)
prepared_by: Carl Patrick L. Reyes
source_doc: DOH UHC Year 2_Survey Manual Apr 28.docx
date_drafted: 2026-06-04
status: draft-for-review
related_task: E7-DOC-004
tags: [survey-manual, f2, healthcare-worker, pwa, kidd, e7, training-and-documentation]
---

# Survey Manual — F2 (Healthcare Worker Survey) Administration Sub-section (Draft for Review)

Prepared for **Kidd** to integrate into the master Survey Manual (`DOH UHC Year 2_Survey Manual Apr 28.docx`), under *Instructions for the Administration of the Questionnaire*.

---

## Cover note — what's in this draft, and the scope question

The master manual's administration instructions are written for the **interviewer-administered** instruments (F1/F3/F4) on CSPro/CSEntry. **F2 is administered differently** — it is **self-administered** by the healthcare worker through a secure web form (Progressive Web App), with a paper-encoder fallback. The draft's open-question #3 (CSPro section, 2026-04-29) flagged that a short F2-specific sub-section was needed; this is that sub-section.

> **Scope for your confirmation, Kidd.** I've written this as a **focused, respondent-and-supervisor-facing administration sub-section** — the operational "how F2 is given out, completed, and monitored" — sized to sit alongside the F1/F3/F4 administration text. The **broader technology/pipeline narrative** (stack rationale, end-to-end data flow, unified store, full QC workflow) already lives in the companion stakeholder section (`CAPI-PWA-Stakeholder-Section_2026-05-02.md`) and is **not** repeated here. If you'd rather this sub-section go deeper (or thinner), tell me the depth and I'll adjust. Tone and step-numbering match the manual's existing convention; no edits are proposed to surrounding sections.

---

## F2 — Healthcare Worker Survey: Administration of the Questionnaire

### 1. Mode of administration

The Healthcare Worker Survey (F2) is **self-administered online**. Healthcare workers complete the questionnaire themselves on their own phone, tablet, or workstation through a secure web link, at their own pace within the completion window. No enumerator reads the questions to the respondent. An enumerator-/encoder-assisted **paper fallback** is provided for facilities with poor connectivity (see §7).

This differs from F1, F3, and F4, which are interviewer-administered on a CSPro tablet with the enumerator present.

### 2. Distribution of the survey link

1. For each sampled facility, the **facility contact person** receives a per-facility survey link from the survey team.
2. The contact person distributes the link to the facility's healthcare workers through the facility's primary communication channel — **Viber, Facebook Messenger, or email**.
3. The enumerator **confirms distribution** with the facility contact person on the day of the facility visit, and records it in the daily field diary.
4. In facilities with poor or no connectivity, the enumerator **drops paper questionnaires** at the start of the facility-visit day and **collects them before departure** for later encoding (see §7).

### 3. Informed consent

1. The healthcare worker opens the link and is first shown the **on-screen informed-consent statement**, mirroring the SJREB-approved consent language (Annex H).
2. The questionnaire **remains locked until consent is given**. A respondent who declines does not proceed, and no questionnaire data is recorded for them.
3. The consent screen discloses what is collected (including the submission-time location reading) and the respondent's rights, consistent with the project Data Privacy & Security Plan.

### 4. Language

At the start, the respondent selects their **preferred language** for the questionnaire. The PWA presents the full instrument in the selected language and records the language used with the response, so the data manager can see which language each respondent completed.

### 5. Completing the questionnaire

1. The respondent answers section by section. The same **skip-logic and validation rules** used in the CSPro CAPI instruments are enforced in the web form, so routing and range/consistency errors are prevented at the point of entry.
2. **Auto-save and resume.** The form auto-saves progress on the respondent's device; the respondent may pause and **resume from the same device** without losing answers.
3. **Completion window.** The questionnaire should be completed within the **3-day window** following first access to the link.

### 6. Submission and confirmation

1. On submit, the response is sent to the project's secure backend; the server stamps the **submission timestamp and location reading** (not the respondent).
2. The respondent sees an explicit **"submitted" confirmation only after the server has acknowledged** the case — so a respondent on a flaky connection knows whether their submission actually landed.
3. Submissions are **duplicate-safe**: an accidental re-submit of the same completed questionnaire does not create a second record.

### 7. Paper fallback and the encoder workflow

1. Paper questionnaires collected from low-connectivity facilities are **encoded by ASPSI staff** through the **same web instrument**, so the data lands in the **same store** as self-completed responses.
2. Encoded responses carry a flag distinguishing **staff-encoded** from **self-completed** records, and capture **who encoded** the response, for audit.
3. The encoder workflow applies the **same validation rules** as the self-administered path.

### 8. Supervisor / data-manager monitoring

1. F2 responses join the **same Approved / On-Hold review pipeline** used for F1/F3/F4, and the same logic and consistency checks run against the unified store.
2. Field progress for F2 is monitored through the **PWA admin portal** (the F2 equivalent of the CSWeb field dashboard), which shows submission counts and supports the encoder and QC functions.
3. The admin portal is for **monitoring, encoding paper backups, and QC** — it is **not** used to edit respondents' answers.

### 9. Connectivity and offline behaviour

The PWA is **offline-capable**: a respondent on an intermittent connection can still complete the form, and the response is **queued locally and submitted when connectivity returns**, with retry handled automatically. This mirrors the offline-first discipline of the CSPro tablets (cases captured locally; sync is the moment data leaves the device, not a precondition for capture).

### 10. Data protection

F2 is operated under the project's layered protection model (informed consent; NDU; role-based server access; encryption in transit and at rest; full access audit logging), detailed in the **Data Privacy & Security Plan**. Only the data manager, assistant data managers, and the authorised programmer have server-side access to raw individual-level F2 responses.

---

## Cross-references (for Kidd, not for the manual body)

- Companion technology/pipeline section: `CAPI-PWA-Stakeholder-Section_2026-05-02.md` (§2.2 F2 flow, §5 audit artifacts, §6 sync/offline, §7 security, §8 roles).
- Protection detail: `deliverables/security/Data-Privacy-and-Security-Plan.md`.
- CSPro/CAPI administration sub-section (F1/F3/F4): `CSPro-Section-Draft_2026-04-29.md`.

## Status

- **Ready to add** as an F2 sub-section under *Instructions for the Administration of the Questionnaire*. Kidd to confirm the **depth/scope** (see cover note), assign any appendix/section numbering, and align the consent-screen reference to the final Annex H wording.
