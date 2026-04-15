---
title: F2 Healthcare Worker Survey — Tooling & Access Model Decision Memo
author: Carl Patrick L. Reyes (Data Programmer)
audience: ASPSI Management Committee; Dr. Paulyn Jean A. Claro; Merlyne (Survey Manager)
date: 2026-04-15
status: Draft for ASPSI review
related:
  - "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/product-backlog]]"
  - "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire]]"
  - "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report]]"
---

# F2 — Tooling & Access Model Decision Memo

## Purpose

Lock in the tooling, respondent access model, and questionnaire-rewrite dependencies for the F2 Healthcare Worker Survey **before** specification extraction and Google Forms build begin. Each decision below is marked **DECISION NEEDED** where ASPSI input is required.

## Background

Per the Revised Inception Report, F2 is **self-administered** by healthcare workers (Google Forms primary; paper fallback in low-connectivity areas). Each respondent is given **3 days to start and complete** the form. This distinguishes F2 from F1/F3/F4, which are interviewer-administered CSPro CAPI instruments.

The F2 build follows a three-path capture model agreed internally on 2026-04-15:

1. **Primary** — HCW self-administers on Google Forms within the 3-day window.
2. **Fallback A** — HCW fills paper in low-connectivity areas; ASPSI staff encodes paper responses into the same Google Form.
3. **Fallback B (optional, deferred)** — A CSPro CAPI F2 app could be built later so ASPSI staff can encode paper responses into CSPro instead of Google Forms. Scheduled last, after F1/F3/F4 CSPro builds, and only green-lit if Google Forms F2 testing surfaces a real need for it.

## Dependency — F2 questionnaire cover-block rewrite

**Finding.** The April 8 F2 questionnaire PDF is drafted using the interviewer-administered template. The questionnaire body (Sections A onward) is suitable for self-admin, but the cover blocks are not:

- The consent form reads *"You are required to read this entire consent form aloud exactly as written"* — enumerator instruction, incompatible with self-admin.
- The narrative states *"The interview may take up to 1.5 hours"* — framed as an interview, not a form.
- The **FIELD CONTROL** block is labeled *"(to be filled in by the Enumerator)"* and captures Survey Team Leader's Name, Enumerator's Name, Field Validated by, Field Edited by, Date First Visited, Date of Final Visit, Total visits, and Result (1-Completed / 2-Postponed / 3-Refused / 4-Incomplete — AAPOR disposition codes).
- The **Health Facility and Geographic Identification** block is also labeled *"(to be filled in by the Enumerator)"*.

**Request to ASPSI.** Before F2 ships to the field, the following blocks must be rewritten for a self-administering HCW audience:

| Block | Current (interviewer-style) | Requested (self-admin style) |
|---|---|---|
| Consent form | *"You are required to read this entire consent form aloud exactly as written"* | *"Please read this consent form carefully before completing the survey"* |
| Signed verification consent | Separate signed form | Click-through acknowledgement inside the Google Form (captured as a required question) |
| Interview duration | *"The interview may take up to 1.5 hours"* | *"This survey should take about X minutes to complete"* — estimate to be confirmed after the desk test |
| FIELD CONTROL | Enumerator name, field validation, multi-visit tracking, disposition codes | Auto-captured submission metadata (timestamp, respondent email from sign-in). Most enumerator fields can be deleted. |
| Facility / Geographic ID | Enumerator fills on first visit | Either (a) pre-filled by ASPSI when distributing the unique link, or (b) asked as the first questions of the form. See Decision 4 below. |

> **DECISION NEEDED (ASPSI).** Approve the rewrite scope above. Carl can draft the replacement text and return it for Dr. Claro's review, or ASPSI can assign the rewrite to the questionnaire author. Recommended: Carl drafts, ASPSI reviews — keeps the build on its own timeline.

---

## Decision 1 — Form platform

**Recommendation: Google Forms.**

| Platform | Pros | Cons | Fit for F2 |
|---|---|---|---|
| **Google Forms** | Free; integrates with the ASPSI project mailbox and Drive; responses flow to a Google Sheet; native save-and-resume for signed-in respondents; familiar to ASPSI staff | Section-level skip logic only (no per-question branching); weak print/paper rendering; limited validation types | **Best default.** Matches the IR, the project mailbox custody model, and the 3-day save-resume requirement. |
| Microsoft Forms | Slightly richer branching; Excel integration | Requires Microsoft 365; ASPSI and project mailbox are on Google; no save-and-resume without an org account | Poor — would force a tool migration mid-project. |
| LimeSurvey (self-hosted) | Full skip logic, save/resume, paradata, multi-language | Requires server hosting; Carl must operate and secure it; longer build | Over-engineered for a 14-page self-admin survey. |
| SurveyCTO | Matches Year 1 tooling; strong offline | Paid; Year 2 stack decision is CSPro; ASPSI is moving away from SurveyCTO | Contradicts Year 2 toolchain decision. |

**Caveat to surface now.** Google Forms skip logic is **section-based**, not per-question. When I extract the F2 spec I will need to restructure any skip logic that currently works per-question into section boundaries. Some logic may not survive the translation cleanly; in that case I will flag the affected items and propose alternatives (inline "if X, skip to section Y" instructions, or splitting sections more finely).

> **DECISION NEEDED (ASPSI).** Approve Google Forms as the F2 platform, or raise an alternative.

---

## Decision 2 — Respondent access model

**Option A — Google-signed-in respondents.**

- Respondent opens the form link while signed in to a Google account.
- Native save-and-resume across the 3-day window (Google Forms caches partial responses per signed-in user).
- One response per account (duplicate prevention built in).
- Email captured automatically.
- Reminder emails can be sent to the same Google account.

*Cons:* Some HCWs may not have or use Google accounts; friction on first access.

**Option B — Open link, no sign-in.**

- Anyone with the link can submit.
- **No save-and-resume** — a HCW who closes the tab loses their progress.
- Duplicate submissions possible; must be de-duped by a key field (email + facility).
- Easier initial access.

*Cons:* Breaks the 3-day window requirement. Most HCWs cannot realistically complete a 14-page survey in one sitting.

**Option C — Unique tokenized link per respondent (hybrid).**

- ASPSI pre-generates a unique Google Form link per HCW (via Apps Script: one prefilled link per respondent with their facility pre-populated).
- Still no save-and-resume unless combined with Option A.
- Enables per-respondent tracking (who opened, who submitted, who didn't) without requiring sign-in for tracking purposes.
- Compatible with Option A (tokenized + signed-in = best of both).

**Recommendation: Option A + Option C combined.**

- Require Google sign-in (for save/resume).
- Distribute tokenized/prefilled links per HCW (for facility pre-population and per-respondent tracking).
- For HCWs without Google accounts, the paper fallback (Fallback A: staff encodes into the same Form) absorbs that edge case.

> **DECISION NEEDED (ASPSI).** Confirm that requiring Google sign-in is acceptable for the HCW population, OR accept that non-signed-in HCWs use the paper-and-encode fallback path.

---

## Decision 3 — Reminder and follow-up cadence

Given the 3-day window:

| Day | Action | Sender |
|---|---|---|
| Day 0 | Distribute unique link + instructions | ASPSI field coordinator |
| Day 1 (end of day) | First reminder to non-starters | Auto (Apps Script) or manual |
| Day 2 (end of day) | Second reminder to non-completers | Auto or manual |
| Day 3 (midday) | Final reminder | Manual (field coordinator) |
| Day 3 (end of day) | Window closes; non-completers flagged for paper-and-encode fallback | ASPSI field coordinator |

The reminder mechanism can be Apps Script-driven (reads the response Sheet, identifies non-completers, sends email) or manual (coordinator reviews the Sheet and sends reminders). Apps Script is trivially cheap to add if Decision 2 lands on Option A.

> **DECISION NEEDED (ASPSI).** Confirm the reminder cadence above, OR adjust. Confirm whether reminders should be automated (Apps Script) or manual (field coordinator).

---

## Decision 4 — Facility identification: pre-filled vs. asked

F2 respondents are tied to specific health facilities (102 UHC-IS + 17 non-UHC-IS). The facility must be captured on every response.

**Option A — Pre-filled per link.** ASPSI generates one unique link per facility (or per HCW at a facility) with facility fields pre-populated. Respondent never types facility info; errors minimized; eliminates one section from the HCW's workload.

**Option B — Respondent enters.** The first section of the form asks the HCW to select or type their facility. Risk of typos, mis-selection, or missing data.

**Recommendation: Option A (pre-filled).** Reduces HCW burden, guarantees clean facility IDs, aligns with Option C link distribution in Decision 2.

> **DECISION NEEDED (ASPSI).** Approve pre-filled facility IDs, and confirm who generates and distributes the per-facility links (ASPSI field team vs. Carl provides a script ASPSI runs).

---

## Decision 5 — PSGC value sets

Per the existing project memory, PSGC value sets (REGION / PROVINCE_HUC / CITY_MUNICIPALITY / BARANGAY) are pending ASPSI for F1, and F2–F4 inherit the same blocker. If F2 captures geographic identifiers at all (likely yes — facility is in a region/province/city/barangay), those dropdowns need the PSGC value sets before the Form can be finalized.

**Mitigation.** If Decision 4 lands on pre-filled facility IDs, PSGC dropdowns may not be needed in F2 at all — the facility ID implicitly encodes the geography, and ASPSI's facility master list can carry the PSGC mapping separately. This would un-block F2 from the PSGC dependency.

> **DECISION NEEDED (ASPSI).** Confirm whether F2 needs its own PSGC dropdowns, or whether pre-filled facility IDs carry the geography implicitly.

---

## Decision 6 — Paper fallback version

Fallback A requires a printable paper version of F2 for low-connectivity areas. Options:

| Option | Pros | Cons |
|---|---|---|
| **Google Doc mirror** (generated from the same spec) | Single source of truth (spec → Form + Doc); re-generatable on revision | Forms' own print view is unusable; Google Doc formatting requires manual styling |
| **Word / PDF from existing F2 questionnaire** | ASPSI already has the April 8 PDF | Will diverge from the Google Form over revisions; maintenance burden |
| **LaTeX / typst** | Beautiful; version-controlled | Overkill; no one on the team will maintain it |

**Recommendation: Google Doc mirror, generated from the same spec** used to build the Google Form. When the spec changes, both the Form and the Doc are re-generated. The April 8 PDF gets archived as the source-of-record for Deliverable 1 but is no longer the maintained paper version.

> **DECISION NEEDED (ASPSI).** Approve the paper-version approach.

---

## Decision 7 — Paper-to-Form encoding workflow (Fallback A)

When ASPSI staff encodes paper responses into the Google Form, they need a way to distinguish "HCW self-submitted" from "staff-encoded from paper" in the response Sheet (for audit and QA purposes).

**Recommendation.** Add a hidden or auto-captured field: `response_source = self | staff_encoded`. When staff use the Form as an encoding UI, they mark the source accordingly. For Fallback A specifically, consider a separate "staff encoder" copy of the Form prefilled with `response_source = staff_encoded` so encoders don't forget to mark it.

> **DECISION NEEDED (ASPSI).** Approve the source-tracking field, and confirm whether staff encoders use the same Form or a dedicated encoder copy.

---

## Decision 8 — Response destination and custody

- Google Form responses land in a Google Sheet in the project mailbox's Drive.
- The Sheet is the ASPSI-custody response of record; the local repo mirrors it for Carl's analysis.
- Per the NDU, responses must follow the existing data privacy and retention rules for the project.

> **DECISION NEEDED (ASPSI).** Confirm response custody in the project mailbox Drive, and confirm no DOH-direct response routing (DOH is not in the mailbox multi-user access list).

---

## Summary of ASPSI decisions requested

| # | Decision | Recommended default |
|---|---|---|
| 0 | Questionnaire cover-block rewrite (consent, duration, FIELD CONTROL, facility ID) | Carl drafts, ASPSI reviews |
| 1 | Form platform | Google Forms |
| 2 | Respondent access model | Google-signed-in + tokenized prefilled links |
| 3 | Reminder cadence | Day 1 / Day 2 / Day 3 + window-close flag; Apps Script automated |
| 4 | Facility ID capture | Pre-filled per link |
| 5 | PSGC dropdowns in F2 | Not needed if Decision 4 lands on pre-filled |
| 6 | Paper fallback version | Google Doc mirror from same spec |
| 7 | Paper-to-Form encoding workflow | `response_source` field; dedicated encoder Form copy |
| 8 | Response custody | Google Sheet in project mailbox Drive |

## Next steps

Once ASPSI returns approval on the decisions above:

1. Carl drafts the F2 cover-block rewrite text → sends to Dr. Claro for review (parallelizes with ASPSI decision turnaround).
2. Carl extracts the F2 specification (`F2-1.1`) from the questionnaire body (Sections A onward).
3. Sean (QA Tester) reviews the spec before build.
4. Carl authors the Google Apps Script generator (`F2-2.1`).
5. Carl runs a 3-day internal dry-run test before field deployment.

## Open items flagged for separate follow-up

- **Product Backlog edits** at next sprint close: Epic 2 F2 row, Epic 3 sequencing note, per-instrument table, F2 risk row. The PB currently treats F2 as flowing through the CSPro Design → CSPro Build pipeline; this memo documents why F2 is a special case with an optional late CSPro track.
