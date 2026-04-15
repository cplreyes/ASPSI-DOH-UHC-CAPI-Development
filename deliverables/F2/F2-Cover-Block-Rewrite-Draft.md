---
title: F2 Healthcare Worker Survey — Cover Block Rewrite Draft
author: Carl Patrick L. Reyes (Data Programmer)
audience: Dr. Paulyn Jean A. Claro (ASPSI); Merlyne (Survey Manager)
date: 2026-04-15
status: Draft for ASPSI review
supersedes_blocks_in: "raw/Project-Deliverable-1/Annex F2_Healthcare Worker Survey Questionnaire_UHC Year 2_April 08.pdf"
related:
  - "[[deliverables/F2/F2-0_Tooling-and-Access-Model-Decision-Memo]]"
---

# F2 — Cover Block Rewrite Draft

## Why this document exists

The April 8, 2026 draft of the F2 Healthcare Worker Survey Questionnaire uses the **interviewer-administered cover-block template** inherited from F1/F3/F4. The questionnaire body (Sections A–J) is structurally compatible with self-administration, but the cover blocks contain enumerator instructions, a read-aloud consent script, a 1.5-hour interview framing, and a FIELD CONTROL block for a Survey Team Leader and Enumerator — none of which apply when a healthcare worker self-administers the survey on Google Forms within a 3-day window.

Per the Revised Inception Report and the 2026-04-15 scope lock-in, F2 is **self-administered** (Google Forms primary, paper fallback encoded back into the same Form, optional deferred CSPro encoder). The cover blocks need to be rewritten so they speak directly to the HCW respondent, not to an enumerator.

This draft proposes replacement text for each affected block, keeps all ethics-mandated disclosures intact, and flags items that ASPSI/Dr. Claro should explicitly confirm before the Google Form is built. Each block shows **current text (excerpted)**, **proposed rewrite**, and **rationale**.

---

## Block 1 — Title and preamble

**Current (interviewer-style):**

> UHC Survey Year 2
> Healthcare Worker Survey Questionnaire

**Proposed (self-admin):**

> UHC Survey Year 2 — Healthcare Worker Survey
>
> *Thank you for taking part in this survey. Please read the information and consent sections below before answering the questions. You may save your progress and return to this form any time within the next 3 days.*

**Rationale:** Sets expectations immediately — this is a form the HCW completes themselves, with a 3-day window to start and finish. Replaces the implicit "interviewer will guide you" framing that the current title carries when read alongside the read-aloud consent instruction.

---

## Block 2 — Consent form header

**Current:**

> Consent Form for Healthcare Workers
>
> *This informed consent form must be obtained before conducting the interview. You are required to read this entire consent form aloud exactly as written. After reading this form to the respondent, you must complete and sign the verification consent form.*

**Proposed:**

> Informed Consent — Please Read Carefully
>
> *Before answering the survey, please read the information below. If you understand and agree to participate, you will be asked to confirm your consent at the end of this section. Your consent confirmation is recorded with your survey response.*

**Rationale:** Removes the enumerator instruction entirely. Consent confirmation moves from a separately signed verification form (which makes no sense for a self-administered Google Form) into a click-through question at the end of the consent section. The respondent cannot proceed to the main questionnaire without confirming consent.

> **DECISION NEEDED (ASPSI).** Confirm that click-through consent capture (a required Google Form question with "I have read and understood the information above and agree to participate" / "I do not wish to participate") satisfies SJREB's informed consent requirements for a self-administered survey. If SJREB requires a signed document, we instead attach a downloadable consent PDF for the HCW to sign and email separately — but that adds friction and is unusual for self-admin designs.

---

## Block 3 — PART I: Information about the study

**Current (excerpt, with issues bolded):**

> The Asian Social Project Services, Inc. (ASPSI) requests your participation in a study on Universal Health Care (UHC). This study aims to generate evidence on the overall experience of the healthcare service providers and the general public to support continuous monitoring, evaluation, and learning of the implementation of the UHC Act, its Implementing Rules and Regulations (IRR), and packages of programs like Yaman ng Kalusugan Program (YAKAP), No Balance Billing (NBB), Zero Balance Billing (ZBB), Bagong Urgent Care and Ambulatory Services (BUCAS) centers, and Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT). The Department of Health funded this study. **The interview may take up to 1.5 hours.**
>
> [...privacy paragraph...]
>
> Aside from this, there are no other risks to you if you take part in this study. As a benefit of the research, the knowledge gained may help the government and DOH better support your healthcare needs. **The interview may last for more or less than an hour** and participating in this survey will also enter you into a raffle, giving you a chance to win PhP1,000 as a way of thanking you for the time you've shared with us.
>
> You are free to decline participation or to stop at any time. Choosing not to participate will not result in any penalty, and you will not have to pay anything to take part in this study.

**Proposed:**

> The Asian Social Project Services, Inc. (ASPSI) invites you to participate in a study on Universal Health Care (UHC). This study aims to generate evidence on the overall experience of healthcare service providers and the general public to support continuous monitoring, evaluation, and learning of the implementation of the UHC Act, its Implementing Rules and Regulations (IRR), and packages of programs like the Yaman ng Kalusugan Program (YAKAP), No Balance Billing (NBB), Zero Balance Billing (ZBB), Bagong Urgent Care and Ambulatory Services (BUCAS) centers, and Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT). The Department of Health funded this study. **This survey should take about [X] minutes to complete. You have up to 3 days from the time you open the form to start and finish. You can save your progress and return to the form at any point within that window as long as you are signed in to the same Google account.**
>
> We are committed to protecting your privacy. If you choose to participate, we will never share your information outside of the study team. We will never include your name in information shared with the government or in any reports. Your name will be kept separately from your answers in a private, secure location. For this survey, we also ask that you respect the privacy of your colleagues and patients and do not share anything you discuss here. With all research, there is a small chance that someone else might get to see your data. We try our best to prevent that, but if it happens, we will tell you as soon as possible.
>
> Aside from this, there are no other risks to you if you take part in this study. As a benefit of the research, the knowledge gained may help the government and DOH better support your healthcare needs. **Participating in this survey will also enter you into a raffle, giving you a chance to win PhP 1,000 as a way of thanking you for the time you have shared with us.**
>
> You are free to decline participation, to skip any question you do not wish to answer, or to stop at any time before submitting the form. Choosing not to participate will not result in any penalty, and you will not have to pay anything to take part in this study.

**Rationale:**

- Replaced "The interview may take up to 1.5 hours" + "The interview may last for more or less than an hour" with a single self-admin duration statement plus the 3-day window rule. The duration placeholder `[X]` needs a realistic estimate from the desk test before the Form is published.
- Reworded "interview" → "survey" throughout.
- Kept the raffle incentive wording intact (it's contractually/ethically committed).
- Added "skip any question you do not wish to answer" — a normal self-admin accommodation that was implicit in the interviewer version (enumerator would move past refusals).

> **DECISION NEEDED (ASPSI).** (a) Confirm the estimated completion time after desk test. (b) Confirm the raffle mechanism still applies when the form is self-administered — same eligibility, same PhP 1,000 amount, same drawing procedure. (c) Confirm that "skip any question" is acceptable, or if certain questions must be required (e.g., demographics, consent confirmation). I recommend: consent is required; demographics and all substantive items are permitted to skip, with a soft reminder at the end of each section that skipped questions will remain blank in the data.

---

## Block 4 — Contact information for concerns

**Current:**

> If you have concerns or questions about your rights as a participant, you can contact:
>
>     Single Joint Research Ethics Board (SJREB) at the Philippines Department of Health
>         Email: sjreb.doh@gmail.com
>         National Tel: (02) 651-7800 local 1328
>         Tel: +63 936 992 5513
>
>     Department of Health
>         Name: Lindsley Jeremiah D. Villarante
>         Email: ldvillarante@doh.gov.ph
>         Tel: +63 (02) 8651-7800 local 1432
>
>     Asian Social Project Services, Inc.
>         Name: Paulyn Jean A. Claro
>         Email: aspsiglobal@gmail.com
>         Tel: + 63 917 819 6884

**Proposed:** *Keep as-is. No rewrite needed — contact list is the same for self-admin.*

**Rationale:** Contact information for ethics concerns is identical regardless of mode. Retain verbatim.

---

## Block 5 — PART II: Certificate of Consent

**Current:**

> If you have understood the information above, please give your permission to answer the survey questionnaire by signing this form. Please email this consent form to: ______________________________________
>
> ______________________________    ________________________  ____________________
> Name and Signature of Respondent      Email Address           Mobile Number
>
> _____________________________
>          Position, Office

**Proposed (replace the entire block with an in-form consent question):**

> **Consent confirmation**
>
> *Please confirm whether you have read and understood the information above and whether you agree to participate in this survey. You must confirm to proceed.*
>
> ( ) I have read and understood the information above. I voluntarily agree to participate in this survey.
> ( ) I do not wish to participate.
>
> *If the respondent chooses "I do not wish to participate," the form submits a declined record and thanks them for their time. The main questionnaire is not shown.*

**Rationale:**

- The current block requires the HCW to sign a paper form and email it separately. This is incompatible with self-admin on Google Forms — it would mean every respondent has to download, sign, scan/photograph, and email a consent form before they can answer the survey, which introduces so much friction it will depress the response rate.
- Replace with an in-form required question. The respondent's consent is timestamped and tied to their Google-signed-in identity and email (captured automatically), which provides audit trail equivalent to a signature for research-ethics purposes in self-admin designs.
- The "I do not wish to participate" branch routes to a thank-you page — respondents who decline should be counted (for disposition/response-rate reporting) but should never see the main questionnaire.

> **DECISION NEEDED (ASPSI/SJREB).** Confirm that an in-form click-through consent with timestamp + Google-authenticated email satisfies SJREB's documentation requirements. If not, fallback: keep a downloadable consent PDF alongside the form and require the respondent to acknowledge they have read it before the click-through (two required steps).

---

## Block 6 — Questionnaire number + FIELD CONTROL block (to be removed)

**Current:**

> Questionnaire No: ______
>
> **FIELD CONTROL (to be filled in by the Enumerator)**
>
>     Survey Team Leader's Name: ______
>     Enumerator's Name: ______
>     Field Validated by: ______
>     Field Edited by: ______
>     Date First Visited the Facility: ______ (Month, Day, Year)
>     Date of Final Visit to the Facility: ______ (Month, Day, Year)
>     Result [First Visit]: ______
>     Result [Final Visit]: ______
>     Codes: 1 - Completed   2 - Postponed   3 - Refused   4 - Incomplete
>     Total number of visits: ______

**Proposed: remove entirely from the respondent-facing form. Replace with auto-captured metadata.**

The following will be captured automatically by the Google Form and stored in the response Sheet — **the respondent never sees or fills any of these**:

| Field | How it is captured |
|---|---|
| `questionnaire_no` | Auto-generated unique ID per response (Apps Script appends a sequential number + timestamp to the Sheet row) |
| `respondent_email` | Captured from Google sign-in (required per the decision memo) |
| `submission_started_at` | Captured by Apps Script on first form open (tracked via a prefilled link opened timestamp) |
| `submission_completed_at` | Captured automatically on form submit |
| `facility_id` | Pre-filled from the unique link (see Block 7) |
| `response_source` | Auto-set to `self` for HCW-submitted responses, or `staff_encoded` when ASPSI staff encode a paper response into the staff encoder variant of the form |
| `disposition` | Derived after the window closes: `completed` (submitted), `partial` (opened but not submitted), `declined` (consent = No), `no_response` (link never opened) |

**Rationale:**

- The FIELD CONTROL block is a field-operations log for enumerator-administered work. None of it applies to self-admin. The facility is visited once at distribution; there's no "first visit / final visit" duality for an online form.
- The AAPOR-style disposition codes (1-Completed, 2-Postponed, 3-Refused, 4-Incomplete) are still relevant for response-rate reporting, but they're **derived after the window closes** from the response Sheet, not entered by a respondent or enumerator. Apps Script computes them from the combination of form-open timestamp, consent choice, and submit timestamp.
- `Survey Team Leader's Name` / `Field Validated by` / `Field Edited by` / `Total number of visits` have no analogue in a self-admin Google Form and should be deleted outright.

> **DECISION NEEDED (ASPSI).** (a) Confirm that removing the FIELD CONTROL block from the respondent view is acceptable. (b) Confirm whether ASPSI still wants an enumerator-like "distributor" record per facility — e.g., who handed out the link to each HCW, on what date. If yes, this becomes a separate ASPSI-internal distribution log (not part of the HCW-facing form). I recommend: yes, keep a distribution log, but as a separate Google Sheet that ASPSI field coordinators fill, not as a block inside the HCW form.

---

## Block 7 — HEALTH FACILITY AND GEOGRAPHIC IDENTIFICATION (to be pre-filled)

**Current:**

> **HEALTH FACILITY AND GEOGRAPHIC IDENTIFICATION (to be filled in by the Enumerator)**
>
>     Area Classification: ( ) UHC IS  ( ) non-UHC IS
>     Name of Health Facility: ______
>     Facility type of ownership: ( ) Public  ( ) DOH-retained Hospital  ( ) Private
>     Facility's capital service level: ( ) Primary Care Facility  ( ) Level 1  ( ) Level 2  ( ) Level 3
>     Region: ______              Province/HUC: ______
>     City/Municipality: ______   Barangay: ______
>     GPS Coordinates: Latitude ______   Longitude ______

**Proposed: remove from respondent view. Pre-fill all fields from the unique link per facility.**

Per the Tooling & Access Model Decision Memo (Decision 4), ASPSI maintains a master list of the 102 UHC-IS + 17 non-UHC-IS facilities. Apps Script generates one **unique prefilled Google Form link per facility** from that list; every HCW at a given facility uses the link for that facility. The form opens with the facility fields already answered (and hidden from the respondent, so they cannot edit or see them).

**What the respondent sees instead:** nothing in this block. The form jumps directly from the consent confirmation to Section A (Healthcare Worker Profile).

**What is captured in the response Sheet:**

| Field | Pre-filled value source |
|---|---|
| `area_classification` | Facility master list column "UHC_IS_STATUS" |
| `facility_name` | Facility master list column "FACILITY_NAME" |
| `facility_ownership` | Facility master list column "OWNERSHIP" |
| `facility_service_level` | Facility master list column "SERVICE_LEVEL" |
| `region` | Facility master list column "REGION" |
| `province_huc` | Facility master list column "PROVINCE_HUC" |
| `city_municipality` | Facility master list column "CITY_MUNICIPALITY" |
| `barangay` | Facility master list column "BARANGAY" |
| `gps_latitude` | Facility master list column "LATITUDE" (if available) |
| `gps_longitude` | Facility master list column "LONGITUDE" (if available) |

**Rationale:**

- A self-administering HCW at a given facility has no reason to re-type their own facility's metadata — they know where they work, and ASPSI already has the facility record from sampling. Asking them to fill it introduces typos, mis-selection, and attrition.
- Pre-filling via unique link eliminates that entire section from the HCW's workload and guarantees clean, audited facility IDs on every response.
- **This also absorbs the F1 PSGC blocker** for F2. Because REGION / PROVINCE_HUC / CITY_MUNICIPALITY / BARANGAY are pulled from the facility master list rather than asked as PSGC dropdowns, F2 does not need the PSGC value sets that ASPSI still owes for F1.
- GPS coordinates are dropped as a respondent-entered field (HCWs cannot meaningfully report their facility's GPS coordinates from a browser, and the facility master list already has them from sampling).

> **DECISION NEEDED (ASPSI).** (a) Confirm that the facility master list has the columns above, or identify the gaps. (b) Confirm who provides the master list to Carl (Merlyne? Dr. Claro? ASPSI sampling team?). (c) Confirm who distributes the per-facility links to individual HCWs (ASPSI field coordinator contacting each facility directly, or facility head forwarding to their staff).

---

## Block 8 — Transition into the main questionnaire

**Current:**

> The following questions ask about your profile. Please put your answer/s in the space provided or check the box of your answer.
>
>         A. Healthcare Worker Profile

**Proposed:**

> Thank you for agreeing to participate. The following questions ask about your professional profile, your work at this facility, and your knowledge and experience of Universal Health Care programs. Please answer honestly — there are no right or wrong answers. You can use the **Back** button at any time to change a previous answer, and you can save and return to this form within the 3-day window using the same link.
>
> **Section A. Healthcare Worker Profile**

**Rationale:** Short orientation that reassures the respondent, reminds them of the back-button and save-resume behavior, and frames the tone (honest answers, no right/wrong). The "Please put your answer/s in the space provided or check the box of your answer" instruction is automatic in a Google Form and can be deleted.

---

## Summary of changes requested from ASPSI

| # | Block | Action | ASPSI decision needed |
|---|---|---|---|
| 1 | Title and preamble | Rewrite | None — stylistic |
| 2 | Consent form header | Rewrite | Click-through vs signed PDF acceptable to SJREB? |
| 3 | PART I: Information | Rewrite | (a) completion time estimate, (b) raffle still applies self-admin, (c) skip-any acceptable |
| 4 | Contact information | Keep as-is | None |
| 5 | PART II: Certificate of Consent | Replace with in-form question | In-form consent with Google-auth email acceptable to SJREB? |
| 6 | FIELD CONTROL | Remove entirely; auto-capture metadata | Keep separate ASPSI distribution log? |
| 7 | Facility & Geographic ID | Remove entirely; pre-fill via unique link | Master list availability, ownership, link distribution workflow |
| 8 | Transition to main questionnaire | Rewrite | None — stylistic |

## Open items for follow-up

- **Filipino translation.** This draft is English only. The F2 Google Form will be bilingual (English + Filipino) per the PB scope. Once ASPSI approves the English rewrite, I will translate (or ask Merlyne/ASPSI to translate) each block into Filipino and wire both into the Form as a language switcher.
- **SJREB protocol update.** If SJREB has already cleared F2 under the interviewer-administered wording, this rewrite is a protocol amendment and SJREB needs to re-clear it. Please confirm with the SJREB liaison before the Google Form ships.
- **Dr. Claro review.** This draft should be reviewed by Dr. Claro (and Merlyne for methodology sanity) before the Google Form is published. Build work on Sections A–J proceeds in parallel so this review is not on the critical path for spec extraction.
- **Questionnaire body unchanged.** This draft covers only the cover blocks (title, consent, FIELD CONTROL, facility ID, transition). The substantive questionnaire body (Sections A–J: Healthcare Worker Profile through the end) is not touched and will be extracted verbatim into the F2 spec per the project's verbatim-labels rule.
