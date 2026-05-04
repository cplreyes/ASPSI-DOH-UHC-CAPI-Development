# Inputs to Survey Manual — CAPI / Data Programmer Lane

**From:** Carl Patrick L. Reyes, Data Programmer
**Date:** 2026-05-05
**Re:** Apr 28 draft of the *DOH UHC Year 2 Survey Manual* — CAPI-technical inputs
**Scope:** CAPI-technical operational procedures only. Defers to the V2 Protocol on methodology, sampling design, ethics, tokens, and pre-test sites.
**Companion document:** *Methodology Clarification Requests for the V2 Protocol* (separate document) — covers items where CAPI implementation surfaced methodology questions that need the methodology team's decision.
**Format:** Edits and additions organized by existing Survey Manual sections, in the Manual's existing voice. Screenshot placeholders included; technical detail pushed to annexes.

---

## Edit 1 — Replace §"Guidelines on installing/using of CSPro" (line 1765 of Apr 28 draft)

The current section walks through Dropbox + the Year 1 `Project_SPEED_2023` application. Replace with a CSWeb-based flow.

> **Guidelines on installing and using CSEntry**
>
> *Each enumerator's tablet is provisioned with the CSEntry application before deployment. The following steps walk through how to install the survey applications, conduct an interview, and synchronize completed cases to the project's secure server.*
>
> **Step 1.** *Connect the tablet to the internet via Wi-Fi or mobile data. Open the Google Play Store, search for **CSEntry CSPro Data Entry**, and tap **Install**.*
> **[SCREENSHOT 1: Play Store CSEntry install page]**
>
> **Step 2.** *Open the CSEntry app, tap **Accept** to agree to the terms, and **Allow** when prompted for storage and location permissions.*
> **[SCREENSHOT 2: CSEntry Accept screen]** **[SCREENSHOT 3: Permissions dialog]**
>
> **Step 3.** *Tap the three-dots menu in the upper right and choose **Add Application**. Select **From server**, then enter the project's CSWeb address: `https://[CSWEB_URL_TBD]`.*
> **[SCREENSHOT 4: Add Application menu]** **[SCREENSHOT 5: Server URL entry]**
>
> **Step 4.** *Sign in using the username and password issued to you during training. Each enumerator and Field Supervisor has a unique account. Do not share credentials.*
> **[SCREENSHOT 6: CSWeb login dialog]**
>
> **Step 5.** *Select and install the survey applications assigned to your role. Enumerators install **F1 — Facility Head Survey**, **F3a — Patient Listing**, **F3b — Patient Interview**, and where applicable **F4a/b — Household Listing/Interview**. Field Supervisors install the same set in monitoring mode plus **F0 — Field Supervisor App**. Wait for each to download fully.*
> **[SCREENSHOT 7: Application list — supervisor view with F0 visible]**
>
> **Step 6.** *To begin a new interview, open the relevant application and tap the **+** icon to add a new case. Make sure the **GPS location** indicator is active before you start the first question. Use the **right arrow** to move forward; the application will skip questions that do not apply based on earlier answers.*
> **[SCREENSHOT 8: Application list]** **[SCREENSHOT 9: Case-listing screen with + icon]** **[SCREENSHOT 10: First question with GPS indicator]**
>
> **Step 7.** *Where the questionnaire requires a verification photo, tap the camera icon and follow the on-screen prompt. For facilities, take a photo of the facility signage or main entrance; for households, take a photo at your discretion that documents the visit, avoiding any image of the respondent's face.*
> **[SCREENSHOT 11: Photo capture screen]**
>
> **Step 8.** *Continue through every question. When all required fields are complete, the application will prompt you to accept the case. Tap **Yes** to mark it complete.*
> **[SCREENSHOT 12: End-of-case prompt]**
>
> **Step 9.** *Verify the tablet is connected to the internet, then tap the **synchronize** icon to upload completed cases to the project server. Wait until **Successfully synced** appears.*
> **[SCREENSHOT 13: Sync icon highlighted]** **[SCREENSHOT 14: Successfully synced confirmation]**
>
> **Step 10.** *If you cannot complete an interview in one sitting, the case is automatically saved as a partial. Tap the case from the case-listing screen to resume from the last completed question.*
> **[SCREENSHOT 15: Partial case in case-listing]**
>
> *For installation problems, sync failures, or any application error, contact the Field Supervisor immediately. Detailed troubleshooting steps are provided in **Annex [N]: CAPI Field Troubleshooting Guide**.*

---

## Edit 2 — Insert new subsection after the CSEntry guidelines

> **Guidelines on the F2 Healthcare Worker Survey**
>
> *The Healthcare Worker Survey is self-administered by HCWs themselves through a web-based survey called the **F2 PWA** (Progressive Web App). Enumerators do not interview HCWs directly. Instead, the team posts the survey access materials at the facility and supports HCWs who request help.*
>
> *Before posting F2 access materials, the Field Supervisor captures the facility's master Healthcare Worker list inside the **Supervisor App (F0b — HCW Master List)**. This list, generated during the courtesy call from the facility's plantilla or staff log, is the official denominator used by the F2 Admin Portal to compute facility-level response rates against the 60% threshold described in the Protocol. Barangay Health Workers are excluded from the master list per Protocol §VIII.*
>
> **Step 1.** *During the courtesy call, request a list of all eligible health workers from the facility focal person. The Field Supervisor records this in F0b.*
>
> **Step 2.** *Post the printed F2 QR code poster in a visible area of the facility (typically the staff lounge, nursing station, or HR bulletin board). The poster includes the survey link and a brief explanation.*
> **[SCREENSHOT 16: F2 QR poster sample]**
>
> **Step 3.** *For HCWs without their own device, the Field Supervisor's tablet has the F2 PWA pre-installed and can be loaned out for survey completion. Confirm with the facility focal person where this device should be staged.*
> **[SCREENSHOT 17: F2 PWA landing page]**
>
> **Step 4.** *For HCWs unable or unwilling to use the digital form, distribute paper copies of the F2 questionnaire through the facility focal person. Collect completed forms before leaving the facility. The Data Encoder will enter paper responses into the F2 PWA after fieldwork.*
>
> **Step 5.** *Monitor response counts on the F2 admin portal during the data collection window. The Field Supervisor will provide daily updates. If facility response is below 40% at the midpoint of the data collection window, follow up with the focal person to encourage participation.*
> **[SCREENSHOT 18: F2 admin portal — facility response rate view]**
>
> *Detailed F2 PWA navigation, paper-form encoding instructions, and admin portal usage are documented in **Annex [N+1]: F2 PWA Field Operations Guide**.*

---

## Edit 3 — Append to §Initial Health Facility Visit (line 933 of Apr 28 draft)

After the existing bulleted list of courtesy-call activities, add:

> *All courtesy call activities — arrival, head/representative engagement, endorsement letter delivery, workstation arrangement, focal person assignment, master HCW list capture, and departure — are documented in real time by the Field Supervisor using **F0a Facility Visit Log** of the Supervisor App. The Supervisor App auto-stamps GPS coordinates and timestamps for every entry, creating an auditable record of every facility touchpoint that can be reconciled against scheduled visits and reserve-list draws.*

---

## Edit 4 — Add to §Field Logistic and Procedure (line 1716 of Apr 28 draft)

After the existing reminders ("Field Reminders: guidelines in conducting a successful interview"), add two new sub-blocks:

> **Working with the CAPI applications (Enumerators)**
>
> - *Always check the GPS indicator before starting the first question.*
> - *Do not switch tablets mid-interview — your enumerator code is bound to your tablet.*
> - *Sync completed cases at the end of each facility visit and again at the team's lodging at the end of the day.*
> - *If a case will not sync, do not delete it. Show it to the Field Supervisor; the Data Programmer can recover it from the tablet if needed.*
> - *Refusals and ineligibilities are recorded inside the application — do not skip the non-response form.*
>
> **Working with the Supervisor App (Field Supervisors)**
>
> - *Document every facility visit in F0a — including arrival, courtesy call outcome, and departure — before leaving the facility.*
> - *Capture the master HCW list in F0b at the courtesy call, not later — the list is the denominator for F2 monitoring.*
> - *Review F0c — Daily Response Monitor at the end of every field day; do not close the tablet until your daily summary syncs to CSWeb.*
> - *All non-response cases must be logged in F0d the same day they occur, with at least the first contact attempt recorded.*
> - *Use F0e to escalate any technical, methodological, ethical, or logistical issue. Do not rely on Viber or SMS as the official record.*

---

## Edit 5 — Replace §Data transfer and extraction (line 2173 of Apr 28 draft)

Replace the existing two paragraphs (Transfer of Data + Data Extraction) with:

> *Completed CAPI cases sync from each enumerator's tablet to the project's CSWeb server, hosted on a secure ASPSI-managed virtual private server. Field Supervisor records (F0a–F0e) sync from the supervisor's tablet to the same server. Synchronization happens at three points: at the end of each interview when a network is available, at the end of each field day at the team's lodging, and on demand by the Field Supervisor. The Data Programmer monitors the CSWeb dashboard daily for transmission gaps and missing cases, and resolves any issues with the field team within 24 hours.*
>
> ***Data Extraction.*** *Interim data shall be extracted from the CSWeb server and submitted within the first full week of data collection for an initial review to assess completeness, the accuracy of the survey's programmed quality-control checks, and other issues affecting data quality. Data will also be extracted weekly thereafter for monitoring of completed interviews and for quality control. Observed outliers, if any, will be subject to further verification. Once fieldwork is complete, the full dataset will be extracted for final validation and cleaning before processing.*
>
> *Detailed sync architecture and back-up procedures are documented in **Annex [N+2]: Data Transmission and Storage**.*

---

## Edit 6 — Add §Bench Testing under §QUALITY CONTROL (insert before line 2192 §Post-survey activities)

> ## Bench Testing of CAPI Applications
>
> *Before any CAPI application is deployed to the field, it undergoes structured bench testing at the ASPSI office. This applies equally to enumerator modules (F1, F3a, F3b, F4a, F4b) and the Field Supervisor module (F0). For each module, at least two research associates simulate respondents independently, exercising every question path, every skip-pattern branch, every numeric range boundary, and every value-set option that triggers routing. The Data Programmer is present throughout and applies fixes as discrepancies are identified. Each finding is logged by question ID with a description of the issue, the fix applied, and the re-test result.*
>
> *The bench test is signed off only when all skip patterns route correctly, all range checks behave as intended, all rosters execute, and a completed test record successfully syncs to CSWeb. Detailed bench testing procedures and the log template are provided in **Annex [N+3]: Bench Testing Protocol**.*

---

## Edit 7 — Insert at start of §Survey Team Leaders (line 2293 of Apr 28 draft)

Insert as the first paragraph of the section, before the numbered list of duties:

> *Each Survey Team Leader (Field Supervisor) is provisioned with a CAPI tablet running CSEntry with the **Supervisor App (F0)** as their primary tool. F0 is used to log facility visits, capture the master HCW list, monitor daily response rates, document non-response and replacements, and escalate field issues. Detailed operating procedures are in **Annex [N+4]: F0 Field Supervisor App Operations Guide**.*

---

## Annex inventory

The following annexes should be added or referenced by the Survey Manual. Where the annex exists, link to it; where it does not, the Data Programmer will draft.

| Annex | Contents | Status |
|---|---|---|
| CAPI Tablet Specifications | Hardware spec, OS version, CSEntry version | ✅ Drafted (sent to Ma'am Juvy 2026-04-29) |
| CAPI Field Troubleshooting Guide | Common error codes, sync failures, GPS issues, photo capture failures | To draft |
| F2 PWA Field Operations Guide | PWA login, offline mode, paper-to-PWA encoding, admin portal navigation | To draft (F2 PWA already in production) |
| F0 Field Supervisor App Operations Guide | F0a–F0e walkthroughs, daily sync workflow, escalation flow | To draft (F0 build queued) |
| Data Transmission and Storage | CSWeb VPS architecture, sync schedule, backup, retention, access controls | To draft |
| Bench Testing Protocol | Pre-deployment QA procedure, log template, sign-off criteria | To draft |
| CAPI Versioning and Amendment Log | Version-stamping, change categories, amendment authorization, log template | To draft |
| Refusal and Replacement Logging | Reason codes, replacement chain, daily report format | To draft |
| CAPI Application Architecture Reference | F0/F1/F3a/F3b/F4a/F4b/F2 module map, data flow diagram, identifier scheme | To draft |

---

## Screenshot capture list

18 screenshots referenced above. The Data Programmer will capture from the production setup once CSWeb on VPS is live. If sending Manual inputs before VPS stand-up, screenshot placeholders remain with `[CSWEB_URL_TBD]`; ASPSI replaces them when production CSWeb URL is finalized.

---

## How to read this document

This document lists *additions to and replacements within* the Apr 28 Survey Manual draft. Each numbered Edit corresponds to one section of the Apr 28 draft, identified by its current heading and approximate line number. Companion document — *Methodology Clarification Requests for the V2 Protocol* — covers items where CAPI implementation surfaced methodology questions that need the methodology team's decision before the corresponding Manual sections can be finalized.
