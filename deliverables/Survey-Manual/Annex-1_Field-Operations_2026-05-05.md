# Annex 1 — Field Operations

This annex provides the operational reference for daily fieldwork. It is organized in three sections by audience.

| Section | Audience |
|---|---|
| 1.1 — Field Troubleshooting | Enumerators (and Field Supervisors when escalating) |
| 1.2 — Healthcare Worker Survey Operations | Field Supervisors and Data Encoders |
| 1.3 — Supervisor App Operations | Field Supervisors |

---

# Section 1.1 — Field Troubleshooting

This section is a quick reference for the most common issues encountered with the CAPI applications during fieldwork. For any issue not resolved by the steps below, contact the Field Supervisor; if unresolved, the Field Supervisor will escalate to the Data Programmer through an Issue Ticket in the Supervisor App.

## CSEntry application

**The application will not open.**
1. Confirm the tablet has at least 1 GB of free storage. Photos and old cases may need to be cleared.
2. Force-stop CSEntry through the Android settings, then reopen.
3. Restart the tablet.
4. If still failing, log the issue with the Field Supervisor. Do not uninstall and reinstall CSEntry without instruction; uninstalling deletes any unsynced cases on the device.

**A case will not save.**
1. Check that no required fields are empty. CSEntry highlights missing fields in red.
2. Confirm that storage is not full.
3. Save the case as **partial** if you cannot complete it now; the case remains on the tablet under its case identifier.

**A case will not sync to the project server.**
1. Confirm the tablet is connected to the internet by opening any web page in Chrome.
2. Confirm the tablet's date and time are correct; sync fails if the clock is wrong.
3. Tap the sync icon again. If the attempt fails, do not delete the case.
4. Show the case to the Field Supervisor before leaving the facility. The Data Programmer can recover the case from the tablet if needed.

**The "Successfully synced" message did not appear.**
1. Wait 60 seconds; a slow connection may delay the confirmation.
2. Re-open the application and check the case-listing screen — synced cases display a cloud icon.
3. If no cloud icon and no error message, log the issue with the Field Supervisor.

## GPS and location

**GPS coordinates show 0,0 or are not captured.**
1. Confirm Location is turned on in the tablet's settings.
2. Move outside or near a window — GPS does not lock indoors with thick walls or in basement levels.
3. Wait 30 to 60 seconds for the lock; the GPS indicator turns green when locked.
4. If still no lock, note this in the case's notes field and proceed. The Field Supervisor records the case as having a GPS exception in the Daily Response Monitor.

**GPS accuracy is poor (greater than 100 meters).**
The application will warn but allow you to proceed. Try to retake the GPS reading once outside or in a more open area before completing the case.

## Verification photo

**The camera will not open from the application.**
1. Confirm Camera permission is granted to CSEntry in the tablet's settings.
2. Close other camera apps that may be holding the camera.
3. Restart the tablet if needed.

**A photo will not save with the case.**
1. Confirm storage is not full.
2. Try retaking the photo; the original capture may have failed.
3. If still failing, save the case without the photo and log the issue with the Field Supervisor — the Data Programmer can attach the photo manually if you take it with the tablet's stock camera.

## Supervisor App specific

**The Daily Response Monitor is not pulling counts from the project server.**
1. Confirm internet connectivity.
2. Tap **Refresh** in the Daily Response Monitor.
3. If counts still do not load, enter the counts manually from the case-listing screens of the Facility Head Survey, Patient Listing, and Household Listing applications, and mark the entry as "manual" in the form.

**Cannot link a replacement case in the Refusal and Replacement Log.**
The original case must already be on the project server. Sync first, then link the replacement.

## Escalation

For any issue not resolved by the steps above, the Field Supervisor logs an Issue Ticket in the Supervisor App with severity Medium or higher. Tickets are reviewed daily by the Data Programmer. Severity-Blocker tickets are also pinged to the project's CAPI channel for immediate attention.

---

# Section 1.2 — Healthcare Worker Survey Operations

The Healthcare Worker Survey is a self-administered web-based survey. It is not part of CSEntry; HCWs do not need to install anything. They open the survey link or scan the QR code in any modern browser, complete the survey, and submit. Submissions sync to the project's Healthcare Worker Survey backend immediately when the device is online.

## The three capture paths

The Manual recognizes three ways for HCWs to complete the survey, in this order of preference:

| Path | When used | Who acts |
|---|---|---|
| **Online, self-administered** | Default. The HCW has a personal device and internet access. | HCW alone |
| **Offline, on a facility-staged device** | The facility has poor connectivity, or the HCW has no personal device. | HCW uses the Field Supervisor's tablet, which has the Healthcare Worker Survey pre-installed for offline use |
| **Paper-to-portal encoded** | The HCW prefers paper, or no device is available. | HCW completes a paper form; the Data Encoder enters responses into the survey portal after fieldwork |

## Field Supervisor responsibilities

**Before posting access materials.** During the courtesy call, capture the facility's master Healthcare Worker list in the Healthcare Worker Master List section of the Supervisor App. The list excludes Barangay Health Workers. This list is the formal denominator for the 60-percent response threshold.

**Posting access materials.** Post the printed Healthcare Worker Survey QR code poster in a visible area of the facility (the staff lounge, nursing station, or HR bulletin board). Confirm with the facility focal person where the supervisor's tablet will be staged for HCWs without personal devices. Distribute paper copies of the survey through the facility focal person.

**During the data collection window.** Monitor response counts daily on the Healthcare Worker Survey administration portal. If facility response is below 40% at the midpoint of the data collection window, follow up with the focal person to encourage participation; document the follow-up in the Daily Response Monitor. If facility response remains below 60% by the close of the window, request a one-time three-day extension through the supervising Research Associate.

**Closing the facility.** Collect any paper forms still at the facility. Note the final response count in the Daily Response Monitor. If response is still below 60%, escalate to the Project Lead through an Issue Ticket.

## Data Encoder responsibilities (paper-to-portal path only)

1. Receive paper forms from the Field Supervisor at the close of fieldwork at the facility.
2. Open the Healthcare Worker Survey administration portal and select **Encode Paper Submission**.
3. Enter the facility identifier, the encoder code, and the paper form's fields exactly as written.
4. The portal validates each field and flags any inconsistencies with the form's logic. Resolve flags before submitting.
5. Mark the paper form as "Encoded" with the date and your initials, and file it with the project's data-retention archive.

## The administration portal

The Field Supervisor's portal access is read-only and limited to facilities under the supervisor's coverage. The portal shows the real-time response count per facility (with the master list as the denominator), the completion timestamps for each submission, the data-quality flags for incomplete or duplicate submissions, and per-question response distributions for early monitoring.

The Data Encoder's portal access additionally allows the Encode Paper Submission action.

## When the survey portal is unreachable

The Healthcare Worker Survey portal is hosted with global redundancy and outages are rare. If the portal loads slowly or returns errors, refresh the browser. If still unreachable from multiple devices for more than 30 minutes, switch to the paper-to-portal path; encoders enter responses once the portal is reachable again. The Field Supervisor escalates a sustained outage through an Issue Ticket with severity High.

## Privacy and data retention

The Healthcare Worker Survey is built to project Data Privacy Act compliance standards. Paper forms are physically secured at ASPSI after encoding and held per the project's retention schedule. HCW responses are pseudonymized in the analytic dataset; no facility management or supervisor ever sees individual responses.

---

# Section 1.3 — Supervisor App Operations

The Supervisor App is a CAPI application that runs in CSEntry on the Field Supervisor's tablet, alongside the Facility Head Survey, Patient Listing, Patient Interview, Household Listing, and Household Interview applications. It captures all structured supervisor work and syncs to the same project server as the enumerator-administered applications. The Supervisor App contains five sections, each opened as a separate case type within the application.

| Section | Trigger | Purpose |
|---|---|---|
| Facility Visit Log | Each time you visit a facility | Captures arrival, courtesy call, endorsement letters, workstation arrangement, focal person, and departure |
| Healthcare Worker Master List | Embedded within the Facility Visit Log | Roster of eligible HCWs at the facility, excluding Barangay Health Workers; used as the response-rate denominator |
| Daily Response Monitor | End of every field day | Per-facility response counts versus target; flags facilities below the midpoint trigger |
| Refusal and Replacement Log | Whenever a refusal, ineligibility, or replacement occurs | Audit chain for sampling weight adjustments |
| Issue Ticket | Whenever an issue must be escalated | Technical, methodological, ethical, or logistical issues |

## Facility Visit Log

Open this section when you arrive at the facility for the courtesy call.

1. Tap **+** in the Facility Visit Log's case-listing screen. The application auto-fills your supervisor code and the date, then prompts for the facility identifier (look up from the facility list).
2. Confirm the facility profile (region, province, city or municipality, barangay, type, ownership, integration status). These fields are pre-populated from the master facility list.
3. Wait for the GPS lock before tapping **Start**. The application captures the arrival timestamp and coordinates automatically.
4. Conduct the courtesy call. As you go, record the outcome (approved with head present, approved with authorized representative, refused, rescheduled), the head's name, position, tenure (which must be at least six months), and contact details, the endorsement letters delivered (DOH, SJREB, PSA, ASPSI), the workstation arrangement, and the focal person's name, position, contact, and channel.
5. Open the Healthcare Worker Master List as a roster within the Facility Visit Log. Enter one row per eligible HCW. Confirm BHWs are excluded.
6. Confirm the Healthcare Worker Survey distribution: where the QR poster is posted, how many paper forms are left at the facility, and whether the supervisor's tablet is staged.
7. Take the verification photo of the facility signage or main entrance.
8. Before leaving, tap **End Visit**. The application captures the departure timestamp and coordinates and computes the total visit duration.

## Healthcare Worker Master List

Captured inline within the Facility Visit Log. One row per HCW. Required fields are the roster number, role (physician, nurse, midwife, pharmacist, and so on), employment type (regular, contractual, job order, and so on), and contact channel. The total count must match the facility's plantilla or staff log.

The Healthcare Worker Survey administration portal reads this list as the denominator for response-rate calculations.

## Daily Response Monitor

Open this section at the end of every field day at the team's lodging.

1. Select the facility (or facilities) covered today.
2. The form pulls case counts from the project server when online — for the Facility Head Survey, Patient Listing, Patient Interview, Household Listing, and Household Interview. If offline, enter counts manually from the enumerators' tablet case-listing screens.
3. Add the Healthcare Worker Survey response count from the administration portal.
4. Compare against the per-facility targets. The form flags facilities below the midpoint trigger (40%) and below the close-of-window threshold (60% for the Healthcare Worker Survey).
5. For each flagged facility, record the action taken: no action, follow-up with the focal person, extension requested, or escalated to the Project Lead.
6. Sync to the project server before closing the tablet.

## Refusal and Replacement Log

Open this section for every refusal, ineligibility, or replacement encountered.

1. Select the original case (facility, type, listing position).
2. Choose the reason category: refused listing, refused interview, ineligible, unreachable, infectious or grave (for patients), or other.
3. Record up to three contact attempts (date, method, outcome).
4. If a replacement is being drawn, link the new case to the original.
5. The Data Programmer's daily replacement report is generated from this log.

The replacement rate is monitored facility by facility and cluster by cluster. When a facility approaches 8%, the Field Supervisor escalates to the Survey Manager and Project Lead through an Issue Ticket.

## Issue Ticket

Open this section for any issue you cannot resolve in the field.

Required fields: type (technical, methodological, ethical, logistical), severity (low, medium, high, blocker), affected facility, module, and case identifier, description (free text), and assignee (Data Programmer, Project Lead, Survey Manager, or DOH-PMSMD focal person).

Tickets are reviewed daily by the Data Programmer. Severity-Blocker tickets are also pinged to the project's CAPI channel for immediate attention.

## Daily sync workflow

**Morning.** Open the Daily Response Monitor and confirm yesterday's counts synced. Note any unsynced cases.

**At each facility.** Work in the Facility Visit Log from arrival to departure. Sync after each facility visit when network is available.

**End of field day at the lodging.** Open the Daily Response Monitor and complete the daily monitor. Resolve any unsynced enumerator cases on the team's tablets. Sync everything before closing the tablet.

## Escalation flow

| Trigger | Action |
|---|---|
| HCW response below 40% at midpoint | Daily Response Monitor records follow-up; supervisor contacts focal person |
| HCW response below 60% at window close | Daily Response Monitor records; supervisor requests one-time three-day extension through supervising Research Associate |
| HCW response still below 60% after extension | Issue Ticket to Project Lead; Project Lead and DOH-PMSMD focal person decide retention with weighting or exclusion |
| Replacement rate at or above 8% per facility | Issue Ticket to Survey Manager and Project Lead |
| Replacement rate at or above 10% per facility | Issue Ticket to Project Lead; data flagged for downweighting or exclusion |
| Technical issue blocking work | Issue Ticket with severity Blocker; ping to project CAPI channel |
