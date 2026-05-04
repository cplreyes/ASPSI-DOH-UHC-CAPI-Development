# Survey Manual (Apr 28 draft) — with CAPI / Data Programmer edits

**Source document:** *DOH UHC Year 2 Survey Manual Apr 28.docx*
**Editor:** Carl Patrick L. Reyes, Data Programmer
**Date of edits:** 2026-05-05
**Companion documents:**
- *Inputs to Survey Manual — CAPI / Data Programmer Lane (2026-05-05)* — same edits in clean-add form for reference
- *Methodology Clarification Requests for the V2 Protocol (2026-05-05)* — items needing methodology-team decision before some Manual sections can be finalized

---

## How to read this document

This document reproduces the **affected sections only** of the Apr 28 Survey Manual draft, with proposed CAPI-technical edits applied in track-changes style. Unchanged paragraphs are reproduced verbatim from the original to preserve context. Section headings include their approximate line number in the original Apr 28 draft.

**Edit conventions (mirrors Word/Google Docs Suggesting mode):**

- ~~Strikethrough text~~ — proposed deletion
- **[INSERT]** *... text ...* **[/INSERT]** — proposed addition
- > 💬 **CAPI EDIT NOTE:** — explanatory comment (Google Docs comment equivalent)

When importing this document into Google Docs or Word with Suggesting/Track Changes turned on, the strikethroughs and **[INSERT]** spans should be re-marked as proposed deletions and proposed insertions respectively, so the final review can run in the team's standard markup environment.

---

## §Initial Health Facility Visit *(approx. line 933 of Apr 28 draft)*

> Upon arrival at the health facility, the field supervisor will approach the facility head (the hospital chief or the health officer-in-charge) for a courtesy call. As part of this visit, the field supervisor will accomplish the following:
>
> - Obtain the health facility's official letter endorsing the conduct of the survey within the facility.
> - Schedule the interview with the facility head.
> - Obtain the master list of healthcare workers in the facility ~~as a sampling frame for the healthcare worker survey, where sample respondents will be drawn~~;
> - Distribute hard copies of the questionnaire or instructions for accessing the online version to healthcare workers.
> - Schedule the patient listing day on which the survey team will record outpatients at the health facility.
> - Request a focal person from the health facility for patient listing day, securing their full name and contact details (mobile number, email address, messenger);
> - Assign a temporary workstation with a table/desk and chairs to the survey team during the patient listing.
> - Schedule the patient listing day; and
> - Discuss the process and flow of the patient listing day and interview

**[INSERT]**

> *All courtesy call activities — arrival, head/representative engagement, endorsement letter delivery, workstation arrangement, focal person assignment, master HCW list capture, and departure — are documented in real time by the Field Supervisor using **F0a Facility Visit Log** of the Supervisor App. The Supervisor App auto-stamps GPS coordinates and timestamps for every entry, creating an auditable record of every facility touchpoint that can be reconciled against scheduled visits and reserve-list draws.*

**[/INSERT]**

> 💬 **CAPI EDIT NOTE:** *Adding one paragraph that names F0a as the structured tool for capturing courtesy-call activities. Without this, supervisors fall back to paper or unstructured Viber messages — non-auditable. F0a auto-captures GPS, timestamps, and the master HCW list (which becomes the F2 60% denominator).*

---

## §Field Logistic and Procedure *(approx. line 1716 of Apr 28 draft)*

> Field Reminders: guidelines in conducting a successful interview
>
> Handling a wide-ranging questionnaire
> - Manage the pace; do not rush respondents
> - Be respectful, always
> - Do not probe if not required in the questionnaire
>
> Ask the questions exactly as they are worded
> - Do not paraphrase
> - Do not explain other than as indicated in the questionnaire
> - Encourage respondents to answer the questions according to their understanding
>
> Dealing with sensitive questions
> - Example: Income
> - Reassure confidentiality
> - Refusals are allowed and may be coded accordingly but are not encouraged
> - Recording the details of "others" responses
> - Capture verbatim response, particularly the open-ended questions
> - Use "others" response sparingly

**[INSERT]**

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

**[/INSERT]**

> 💬 **CAPI EDIT NOTE:** *Two new sub-blocks of reminders, in the same voice as the existing field reminders. The first block is for enumerators (using F1, F3a/b, F4a/b); the second block is for Field Supervisors (using F0).*

---

## §Guidelines on installing/using of CSPro *(approx. line 1765 of Apr 28 draft)*

> 💬 **CAPI EDIT NOTE:** *The Apr 28 draft is a Year 1 carryover that walks through Dropbox + the SPEED 2023 application. Replacing wholesale with a CSWeb-based flow that matches the Year 2 architecture: CSEntry on tablets, CSWeb on a project-managed VPS, no consumer cloud. The marker* `[to replace with actual screenshots once protocols are finalized]` *that appears in the Apr 28 heading is honored — screenshots will be captured by the Data Programmer once the production CSWeb URL is finalized.*

~~Guidelines on installing/using of CSPro [(to replace with actual screenshots once protocols are finalized)]~~

~~**Step 1:** Connect the tablet to the internet via Wi-Fi or mobile data. Open Google Play Store in your tablet. Search **Dropbox: Secure Cloud Storage** then click **Install**.~~

~~**Step 2:** Search and install also ***CSEntry CSPro Data Entry*.**~~

~~**Step 3:** After installing CSPro, open the application and click the **Accept** button to proceed with the installation process.~~

~~**Step 4:** Select '**Allow**' to let the **CSEntry** application access the files in the tablet.~~

~~**Step 5:** Click the three dots menu on the upper right corner of the tablet's screen and select **Add Application**.~~

~~**Step 6:** Choose **Dropbox** to download the CAPI application and **Sign in with Google** using the following information:~~ ~~Email: **aspsi.database2023@gmail.com**~~ ~~Password: **DBAspsi#23**~~

~~**Step 7:** Allow Dropbox to access the Google account used for this survey.~~

~~**Step 8:** Click '**Allow**' to give CSPro permission to access Dropbox account. Make sure it's connected to **aspsi.database2023@gmail.com**~~

~~**Step 9:** Wait until the application is completely downloaded from Dropbox and press '**INSTALL**' to add the **Project_SPEED_2023.**~~

~~**Step 10:** Press **Project_SPEED_2023** to start the interview.~~

~~**Step 11:** Click the **'+'** sign to add a new case/ respondent. Click on the **right arrow** to proceed to the next question.~~

~~**Step 12:** Enter all the data needed until the last question. Make sure the **GPS location** icon is enabled to capture GPS coordinates of the respondent's location. Select '**Yes**' when prompted to accept the completed case.~~

~~**Step 13:** Check again if the tablet is connected to the internet before synchronizing the completed case/s. Click the synchronize icon to upload the case/s to Dropbox and wait until '**Successfully synced**' message appears on the screen.~~

**[INSERT]**

> ### Guidelines on installing and using CSEntry
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
>
> ### Guidelines on the F2 Healthcare Worker Survey
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

**[/INSERT]**

---

## §Data transfer and extraction *(approx. line 2173 of Apr 28 draft)*

> # QUALITY CONTROL
>
> ## Data transfer and extraction
>
> Using CAPI, several activities will be performed before the actual data processing. The tasks will include the following:

~~**Transfer of Data.** Survey enumerators will be instructed to sync or upload data to the server daily before 10 PM to monitor fieldwork progress each morning.~~

~~**Data Extraction.** Interim data shall be extracted and submitted within the first full week of data collection for an initial review to assess completeness, the accuracy of the survey's programmed quality-control checks, and other issues affecting data quality. Data will also be extracted weekly for checking the number of completed interviews and for quality control. Observed outliers, if any, will be subject to further verification. Once fieldwork is complete, the full dataset will be extracted for final validation and cleaning before processing.~~

**[INSERT]**

> ***Transfer of Data.*** *Completed CAPI cases sync from each enumerator's tablet to the project's CSWeb server, hosted on a secure ASPSI-managed virtual private server. Field Supervisor records (F0a–F0e) sync from the supervisor's tablet to the same server. Synchronization happens at three points: at the end of each interview when a network is available, at the end of each field day at the team's lodging, and on demand by the Field Supervisor. The Data Programmer monitors the CSWeb dashboard daily for transmission gaps and missing cases, and resolves any issues with the field team within 24 hours.*
>
> ***Data Extraction.*** *Interim data shall be extracted from the CSWeb server and submitted within the first full week of data collection for an initial review to assess completeness, the accuracy of the survey's programmed quality-control checks, and other issues affecting data quality. Data will also be extracted weekly thereafter for monitoring of completed interviews and for quality control. Observed outliers, if any, will be subject to further verification. Once fieldwork is complete, the full dataset will be extracted for final validation and cleaning before processing.*
>
> *Detailed sync architecture and back-up procedures are documented in **Annex [N+2]: Data Transmission and Storage**.*

**[/INSERT]**

> 💬 **CAPI EDIT NOTE:** *Replaces the Year 1 "sync to server before 10 PM" rule with the Year 2 three-point sync model (per-case, end-of-day, on-demand). Names CSWeb-on-VPS as the sync target — replaces any implicit reference to consumer cloud storage. The Data Extraction paragraph is preserved nearly verbatim from the original; only "the server" was clarified to "the CSWeb server."*

---

## §Bench Testing of CAPI Applications *(NEW — to insert before §Post-survey activities, approx. line 2192)*

**[INSERT]**

> ## Bench Testing of CAPI Applications
>
> *Before any CAPI application is deployed to the field, it undergoes structured bench testing at the ASPSI office. This applies equally to enumerator modules (F1, F3a, F3b, F4a, F4b) and the Field Supervisor module (F0). For each module, at least two research associates simulate respondents independently, exercising every question path, every skip-pattern branch, every numeric range boundary, and every value-set option that triggers routing. The Data Programmer is present throughout and applies fixes as discrepancies are identified. Each finding is logged by question ID with a description of the issue, the fix applied, and the re-test result.*
>
> *The bench test is signed off only when all skip patterns route correctly, all range checks behave as intended, all rosters execute, and a completed test record successfully syncs to CSWeb. Detailed bench testing procedures and the log template are provided in **Annex [N+3]: Bench Testing Protocol**.*

**[/INSERT]**

> 💬 **CAPI EDIT NOTE:** *New section under §QUALITY CONTROL, sitting between §Data transfer and extraction and §Post-survey activities. Operationalizes Protocol §XI's bench testing requirement.*

---

## §Survey Team Leaders *(approx. line 2293 of Apr 28 draft)*

> ## **2.5 DUTIES AND RESPONSIBILITIES**
>
> ### Survey Team Leaders

**[INSERT]**

> *Each Survey Team Leader (Field Supervisor) is provisioned with a CAPI tablet running CSEntry with the **Supervisor App (F0)** as their primary tool. F0 is used to log facility visits, capture the master HCW list, monitor daily response rates, document non-response and replacements, and escalate field issues. Detailed operating procedures are in **Annex [N+4]: F0 Field Supervisor App Operations Guide**.*

**[/INSERT]**

> The STL is expected to perform the following:
>
> 1.  Participate in the training on the use of the survey instrument and the survey manual, which would include familiarity with the content of the questionnaire, effective styles of interviewing, timeline, replacement of sample respondents if needed, and other administrative concerns;
> 2.  Recruit local enumerators and assist in the conduct of the survey;
> 3.  Provide the list of respondents and replacements for enumerators based on ASPSI data.
> 4.  Check survey questionnaires (CAPI) to ensure completeness and accuracy of the data collected;
> 5.  Coordinate with ASPSI Project Coordinator and assigned Research Associate for the organization and coordination of the data gathering activities of the survey enumerators, including proper disbursement of payments/reimbursements and filling up of required survey forms. This shall also include the regular updating of the survey activity using the provided monitoring form for STLs.
> 6.  Ensure data are cleaned before questionnaires are encoded in CAPi at the end of each day;
> 7.  Other than survey questionnaires, collate and ensure completeness of forms such as enumerators' list of respondents and diary, enumerators' agreements, as well as the STLs' diary (**Appendix C**), which shall be submitted to ASPSI upon completion of the survey. The STL shall also ensure that the identification cards of STL and enumerators provided shall only be used for the purpose of the survey and to be returned to ASPSI upon completion of the assignment; and
> 8.  Liquidate the cash advance provided by ASPSI using the required form with proper supporting documents attached/ Additional survey-related expenses not included in this initial agreement shall be coursed first to ASPSI for approval

> 💬 **CAPI EDIT NOTE:** *One paragraph inserted at the start of §Survey Team Leaders, before the existing numbered list of duties. The paragraph names F0 (Supervisor App) as the STL's primary tool and points to the operations annex. The numbered list of duties is preserved verbatim.*

---

## Annex inventory *(referenced from edited Manual)*

The following annexes are referenced by the edits above. Where the annex exists, the Manual should link to it; where it does not, the Data Programmer will draft.

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

## Items NOT addressed in this edit pack

These items were identified during the CAPI implementation review but are out of scope for the Survey Manual; they are tracked in the companion *Methodology Clarification Requests for the V2 Protocol* document and require methodology-team decision before the corresponding Manual sections can be finalized:

- **M1** Patient intercept procedure (Protocol §IX) — affects §Patient Listing Protocols (lines 1424–1543 of Apr 28 draft)
- **M2** Inpatient residency requirement (Protocol §VIII, §IX) — affects §Patient Eligibility
- **M3** Replacement rate exceedance handling (Protocol §IX, §XII) — affects §Quality Control / Replacement
- **M4** Hospital OPD "completed consultation" eligibility check (Protocol §VIII) — affects §Outpatient Listing
- **M5** HCW master list as the formal 60% denominator (Protocol §IX) — affects §HCW Survey
- **M6** GPS and verification photo as paradata (Protocol §XII) — affects §Quality Control

Once those decisions are recorded, this edit pack will be revised to include the corresponding Manual sections.
