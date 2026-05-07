# Survey Manual — CAPI Sections for Year 2

**Submitted by:** Carl Patrick L. Reyes, Data Programmer
**Date:** 2026-05-05
**Source:** Apr 28 draft of the *DOH UHC Year 2 Survey Manual*

This document contains the proposed Manual content for the CAPI-related sections of the UHC Year 2 Survey Manual. It is written in the same voice and structure as the Apr 28 draft and is meant to be incorporated directly into the Manual's existing sections. Two annexes accompany this document and provide operational and technical reference detail.

| Companion | Audience |
|---|---|
| **Annex 1 — Field Operations** | Field teams (enumerators, supervisors, data encoders) |
| **Annex 2 — Technical Reference** | Technical reviewers (DOH-PMSMD, SJREB, ASPSI technical staff) |

---

## §Initial Health Facility Visit

*(Add the following paragraph after the existing courtesy-call activities list.)*

All courtesy call activities — arrival, head or representative engagement, endorsement letter delivery, workstation arrangement, focal person assignment, master Healthcare Worker list capture, and departure — are documented in real time by the Field Supervisor using the **Facility Visit Log** section of the **Supervisor App**. The Supervisor App auto-stamps GPS coordinates and timestamps for every entry, creating an auditable record of every facility touchpoint that can be reconciled against scheduled visits and reserve-list draws.

---

## §Patient Listing Protocols

*(Replace the **Randomization** paragraphs in the Outpatient Protocol and Inpatient Protocol sections, and the **Refusals** bullet in §Other Situations.)*

### Outpatient Protocol — Listing window and sampling

Following the methodology used in the UHC Survey Year 1 (IDinsight, 2024), enumerators conduct continuous listing during the designated listing window, capturing every eligible patient who passes through the listing station. Enumerators do not apply per-patient time intervals between approaches; the random process is the listing window itself, with the sampling interval applied after the window closes.

Once listing is complete for the facility, the Patient Listing application designates the **first two-thirds** of the listed pool as main respondents and the **last third** as backup respondents, in the order patients were listed. Where the listed pool exceeds the per-facility target, a random start is drawn within the application and a systematic sampling interval is applied to the listed pool to achieve the target main sample.

Listing continues until either the listing window closes or the listed pool reaches the per-facility target plus the protocol-required backup oversampling, whichever occurs first.

### Inpatient Protocol — Listing window and sampling

The inpatient listing follows the same window-based approach described for the outpatient protocol. Enumerators station themselves at the discharge or billing area for the designated window and list every eligible inpatient who passes through. After the window closes, the Patient Listing application designates the first two-thirds of the listed pool as main respondents and the last third as backup respondents, in listing order. Where the pool exceeds the per-facility target, systematic sampling with a random start is applied.

### Other situations — Refusals

If a listed patient later declines to participate in the interview, the enumerator documents the refusal in the Patient Listing application. Refusals do not interrupt the listing window; the enumerator continues listing eligible patients. After the window closes, the listed pool is reordered so that refusals are excluded from the main sample, and a backup case is drawn from the last-third pool to fill the slot.

> **Note on this protocol.** This procedure follows the methodology validated in the UHC Survey Year 1 (IDinsight, 2024), which used continuous listing during a designated window with sampling applied after the window closed (first two-thirds main, last third backup). Adopting the same approach in Year 2 preserves longitudinal comparability with Year 1 and uses a random-selection mechanism that is fully implementable within the survey's data-collection software. The sampling weights at the analysis stage will be computed accordingly.

---

## §Outpatient Protocol — Eligibility check for hospital outpatients

*(Add the following sentence to the Outpatient Protocol paragraph that defines eligibility, as a clarification on the "completed consultation" criterion.)*

For hospital outpatients, eligibility is determined by patient self-report at the screening question administered by the Patient Listing application: *"Have you completed your consultation today?"* Patients who answer "yes" proceed through the listing flow; patients who answer "no" or "I don't know" are not listed. The screening question is the first item in the eligibility section of the application and is recorded with the case for later auditing.

---

## §Patient Survey Eligibility

*(No change to the existing Apr 28 draft.)*

The Apr 28 Manual's eligibility text — requiring inpatients to be residents of the same province as the health facility for at least the past six months — is retained for Year 2. This continues the eligibility rule used in the UHC Survey Year 1 and preserves longitudinal comparability between Year 1 and Year 2 patient-side analyses. The Patient Listing application captures the residency criterion at the listing stage.

---

## §Field Logistic and Procedure — additional reminders

*(Add the following two sub-blocks after the existing reminders.)*

### Working with the CAPI applications (Enumerators)

- Always check the GPS indicator before starting the first question.
- Do not switch tablets mid-interview — your enumerator code is bound to your tablet.
- Sync completed cases at the end of each facility visit and again at the team's lodging at the end of the day.
- If a case will not sync, do not delete it. Show it to the Field Supervisor; the Data Programmer can recover it from the tablet if needed.
- Refusals and ineligibilities are recorded inside the application — do not skip the non-response form.

### Working with the Supervisor App (Field Supervisors)

- Document every facility visit in the Facility Visit Log — including arrival, courtesy call outcome, and departure — before leaving the facility.
- Capture the master Healthcare Worker list in the Healthcare Worker Master List section at the courtesy call, not later. The list is the official denominator for response-rate monitoring.
- Review the Daily Response Monitor at the end of every field day; do not close the tablet until your daily summary syncs to the project server.
- All non-response cases must be logged in the Refusal and Replacement Log the same day they occur, with at least the first contact attempt recorded.
- Use the Issue Ticket section to escalate any technical, methodological, ethical, or logistical issue. Do not rely on Viber or SMS as the official record.

---

## §Guidelines on Installing and Using CSEntry

*(Replace the existing §Guidelines on installing/using of CSPro section, which describes the Year 1 Dropbox + Project_SPEED_2023 procedure.)*

Each enumerator's tablet is provisioned with the CSEntry application before deployment. The following steps walk through how to install the survey applications, conduct an interview, and synchronize completed cases to the project's secure server.

**Step 1.** Connect the tablet to the internet via Wi-Fi or mobile data. Open the Google Play Store, search for **CSEntry CSPro Data Entry**, and tap **Install**.
*[Screenshot: Play Store CSEntry install page]*

**Step 2.** Open the CSEntry app, tap **Accept** to agree to the terms, and **Allow** when prompted for storage and location permissions.
*[Screenshot: CSEntry Accept screen and Permissions dialog]*

**Step 3.** Tap the three-dots menu in the upper right and choose **Add Application**. Select **From server**, then enter the project's secure server address provided to you during training.
*[Screenshot: Add Application menu and Server URL entry]*

**Step 4.** Sign in using the username and password issued to you during training. Each enumerator and Field Supervisor has a unique account. Do not share credentials.
*[Screenshot: Server login dialog]*

**Step 5.** Select and install the survey applications assigned to your role. Enumerators install the **Facility Head Survey**, **Patient Listing**, **Patient Interview**, and where applicable the **Household Listing** and **Household Interview**. Field Supervisors install the same set in monitoring mode plus the **Supervisor App**. Wait for each to download fully.
*[Screenshot: Application list — Field Supervisor view with Supervisor App visible]*

**Step 6.** To begin a new interview, open the relevant application and tap the **+** icon to add a new case. Make sure the **GPS location** indicator is active before you start the first question. Use the **right arrow** to move forward; the application will skip questions that do not apply based on earlier answers.
*[Screenshot: Application list, case-listing screen with + icon, first question with GPS indicator]*

**Step 7.** Where the questionnaire requires a verification photo, tap the camera icon and follow the on-screen prompt. For facilities, take a photo of the facility signage or main entrance; for households, take a photo at your discretion that documents the visit, avoiding any image of the respondent's face.
*[Screenshot: Photo capture screen]*

**Step 8.** Continue through every question. When all required fields are complete, the application will prompt you to accept the case. Tap **Yes** to mark it complete.
*[Screenshot: End-of-case prompt]*

**Step 9.** Verify the tablet is connected to the internet, then tap the **synchronize** icon to upload completed cases to the project server. Wait until **Successfully synced** appears.
*[Screenshot: Sync icon highlighted, Successfully synced confirmation]*

**Step 10.** If you cannot complete an interview in one sitting, the case is automatically saved as a partial. Tap the case from the case-listing screen to resume from the last completed question.
*[Screenshot: Partial case in the case-listing screen]*

For installation problems, sync failures, or any application error, contact the Field Supervisor immediately. Detailed troubleshooting steps are in **Annex 1, Section 1.1 — Field Troubleshooting**.

---

## §Guidelines on the Healthcare Worker Survey

*(Add this as a new subsection immediately after §Guidelines on Installing and Using CSEntry.)*

The Healthcare Worker Survey is self-administered by HCWs themselves through a web-based survey accessed by QR code or direct link. Enumerators do not interview HCWs directly. Instead, the team posts the survey access materials at the facility and supports HCWs who request help.

Before posting the survey access materials, the Field Supervisor captures the facility's master Healthcare Worker list in the Healthcare Worker Master List section of the Supervisor App during the courtesy call. This list, generated from the facility's plantilla or staff log, is the official denominator used to compute facility-level response rates against the 60-percent threshold. Barangay Health Workers are excluded from the master list.

**Step 1.** During the courtesy call, request a list of all eligible health workers from the facility focal person. The Field Supervisor records this in the Supervisor App.

**Step 2.** Post the printed Healthcare Worker Survey QR code poster in a visible area of the facility (typically the staff lounge, nursing station, or HR bulletin board). The poster includes the survey link and a brief explanation.
*[Screenshot: QR code poster sample]*

**Step 3.** For HCWs without their own device, the Field Supervisor's tablet has the Healthcare Worker Survey pre-installed and can be loaned out for survey completion. Confirm with the facility focal person where this device should be staged.
*[Screenshot: Healthcare Worker Survey landing page]*

**Step 4.** For HCWs unable or unwilling to use the digital form, distribute paper copies of the Healthcare Worker Survey through the facility focal person. Collect completed forms before leaving the facility. The Data Encoder will enter paper responses into the digital survey after fieldwork.

**Step 5.** Monitor response counts on the Healthcare Worker Survey administration portal during the data collection window. The Field Supervisor will provide daily updates. If facility response is below 40% at the midpoint of the data collection window, follow up with the focal person to encourage participation.
*[Screenshot: Administration portal — facility response rate view]*

Detailed survey navigation, paper-form encoding instructions, and administration portal usage are documented in **Annex 1, Section 1.2 — Healthcare Worker Survey Operations**.

---

## §Quality Control — Data Transfer and Extraction

*(Replace the existing **Transfer of Data** and **Data Extraction** paragraphs.)*

**Transfer of Data.** Completed CAPI cases sync from each enumerator's tablet to the project's secure server, hosted on a virtual private server managed by ASPSI. Field Supervisor records sync from the supervisor's tablet to the same server. Synchronization happens at three points: at the end of each interview when a network is available, at the end of each field day at the team's lodging, and on demand by the Field Supervisor. The Data Programmer monitors the dashboard daily for transmission gaps and missing cases, and resolves any issues with the field team within 24 hours.

**Data Extraction.** Interim data shall be extracted from the project server and submitted within the first full week of data collection for an initial review to assess completeness, the accuracy of the survey's programmed quality-control checks, and other issues affecting data quality. Data will also be extracted weekly thereafter for monitoring of completed interviews and for quality control. Observed outliers, if any, will be subject to further verification. Once fieldwork is complete, the full dataset will be extracted for final validation and cleaning before processing.

Detailed sync architecture and back-up procedures are documented in **Annex 2, Section 2.1 — Data Transmission and Storage**.

---

## §Quality Control — Bench Testing of CAPI Applications

*(Add this as a new subsection under §QUALITY CONTROL, before §Post-survey activities.)*

Before any CAPI application is deployed to the field, it undergoes structured bench testing at the ASPSI office. This applies equally to the enumerator-administered modules — the Facility Head Survey, Patient Listing, Patient Interview, Household Listing, and Household Interview — and to the Supervisor App used by Field Supervisors. For each module, at least two research associates simulate respondents independently, exercising every question path, every skip-pattern branch, every numeric range boundary, and every value-set option that triggers routing. The Data Programmer is present throughout and applies fixes as discrepancies are identified. Each finding is logged by question identifier with a description of the issue, the fix applied, and the re-test result.

The bench test is signed off only when all skip patterns route correctly, all range checks behave as intended, all rosters execute, and a completed test record successfully syncs to the project server. Detailed bench testing procedures and the log template are in **Annex 2, Section 2.2 — Bench Testing Protocol**.

---

## §Quality Control — Replacement Rate Monitoring and Escalation

*(Add this as a new subsection under §QUALITY CONTROL, immediately after Bench Testing.)*

The Field Supervisor monitors the running replacement rate per facility daily through the Daily Response Monitor of the Supervisor App. When a facility approaches the 8-percent replacement rate, the Field Supervisor escalates to the Survey Manager and Project Lead through an Issue Ticket in the Supervisor App. When the 10-percent protocol cap is exceeded, the facility's data is flagged for either downweighting or exclusion from the analysis, with the decision made jointly by the Project Lead, Survey Manager, and the DOH-PMSMD focal person. All such decisions are documented in the project's amendment log.

Detailed reason codes, replacement chain documentation, and the daily report format are in **Annex 2, Section 2.4 — Refusal and Replacement Logging**.

---

## §Quality Control — Paradata Anchor

*(Add this as a new subsection under §QUALITY CONTROL.)*

Each completed CAPI case is auto-stamped with GPS coordinates at start and end and includes one verification photo. For facility visits, the photo is of the facility signage or main entrance; for household visits, the photo is taken at the enumerator's discretion to document the visit, with no image of the respondent's face. Together, the GPS coordinates and verification photo form a *paradata anchor* used for case authenticity audits and back-checks. Cases failing GPS lock or photo capture are flagged in the daily quality report and reviewed by the Data Programmer with the Field Supervisor.

---

## §Survey Team Leaders

*(Insert as the first paragraph of §Survey Team Leaders, before the existing numbered list of duties.)*

Each Survey Team Leader (Field Supervisor) is provisioned with a CAPI tablet running CSEntry with the **Supervisor App** as their primary tool. The Supervisor App is used to log facility visits, capture the master Healthcare Worker list, monitor daily response rates, document non-response and replacements, and escalate field issues. Detailed operating procedures are in **Annex 1, Section 1.3 — Supervisor App Operations**.

---

## Notes for the team

A small number of these proposed sections involve operational refinements to procedures stated in the V2 Protocol. Where this is the case, the section above is written so that the Manual is internally consistent and operationally implementable; the Protocol may need a corresponding minor amendment so the Protocol and Manual remain aligned. Specifically:

- The **Patient Listing Protocols** procedure follows the Year 1 IDinsight method (continuous listing within a window, with first-two-thirds-main and last-third-backup designation after the window closes). Protocol §IX should be updated to match.
- The **Patient Survey Eligibility** retains the Year 1 residency requirement (six months in the same province). Protocol §VIII should be updated to re-add this rule, which is currently absent from the V2 draft.
- The **Replacement Rate Monitoring and Escalation** thresholds (8% warning, 10% cap) and decision body (Project Lead, Survey Manager, DOH-PMSMD focal person) operationalize Protocol §IX and §XII.
- The **Outpatient eligibility check** for hospital outpatients (self-report at screening) operationalizes Protocol §VIII.
- The **Healthcare Worker Master List** is named as the formal denominator for the 60-percent threshold, closing an operational ambiguity between Protocol §IX and §XII.
- The **Paradata Anchor** (GPS plus verification photo) is promoted from established CAPI practice to a Manual-level Quality Control commitment. The Informed Consent Forms should add a one-line mention of photo capture for transparency.

The Data Programmer is available throughout for any technical context the team needs during review.
