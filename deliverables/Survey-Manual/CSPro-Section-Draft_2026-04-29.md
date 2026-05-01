---
type: deliverable
kind: survey-manual-section
audience: Kidd (ASPSI main RA)
prepared_by: Carl Patrick L. Reyes
source_doc: DOH UHC Year 2_Survey Manual Apr 28.docx
date_drafted: 2026-04-29
status: draft-for-review
related_task: E7-DOC-001
tags: [survey-manual, capi, cspro, kidd, e7, training-and-documentation]
---

# Survey Manual — CSPro / CAPI Section (Draft for Review)

Prepared for **Kidd** to integrate into the master Survey Manual (`DOH UHC Year 2_Survey Manual Apr 28.docx`).

---

## Cover note — what's in this draft

This file contains:

1. **Replacement for the existing "Guidelines on installing/using of CSPro" section** (currently in the master manual under *Instructions for the Administration of the Questionnaire*). The existing text is from the 2023 SPEED survey and references Dropbox + the `aspsi.database2023@gmail.com` Google account + the `Project_SPEED_2023` application — none of which apply to the UHC Survey Year 2 deployment. The replacement below uses our actual instrument names and current deployment model.
2. **Two suggested appendices** — a one-page CAPI Quick Reference Card for enumerators, and a CAPI Troubleshooting guide. Both are CAPI-specific, fit the manual's tone, and address gaps the field team will hit.
3. **Open questions / items needing ASPSI input** — short list at the end of this file.

I have kept the original section title (`Guidelines on installing/using of CSPro`) and the existing placeholder marker `(to replace with actual screenshots once protocols are finalized)` since real screenshots will only exist after the F1/F3/F4 builds reach Designer-validated state. Inline screenshot slots are marked `[Screenshot: …]` in this draft.

Tone and step-numbering match the manual's existing convention. No edits are proposed to surrounding sections.

---

## 1. Replacement: "Guidelines on installing/using of CSPro"

> *Substitute the entire current "Guidelines on installing/using of CSPro" sub-section under "Instructions for the Administration of the Questionnaire" with the text below. The section heading and placeholder marker are preserved.*

### Guidelines on installing/using of CSPro *(to replace with actual screenshots once protocols are finalized)*

The CAPI tablets used for the UHC Survey Year 2 are pre-configured by the ASPSI CAPI development team before deployment to the field. Each tablet is imaged with **CSEntry** (the CSPro data-entry application) and the survey instruments required for this fieldwork:

- **FacilityHeadSurvey** — for the facility-head interview (Form 1 / F1)
- **PatientSurvey** — for the patient-exit interview (Form 3 / F3)
- **HouseholdSurvey** — for the community/household interview (Form 4 / F4)

The Healthcare Worker survey (Form 2 / F2) is administered separately through a self-administered web link and is **not** loaded onto the enumerator's CAPI tablet by default. Refer to the F2 sub-section for distribution instructions.

Enumerators receive a ready-to-use tablet from their Survey Team Leader (STL) at the start of fieldwork. The steps below describe how to start, conduct, and complete an interview using CSEntry.

**Step 1:** Power on the tablet and confirm the lock-screen identifier matches the device assigned to you. If you are uncertain, check with your STL before proceeding. Locate the **CSEntry** icon on the home screen and tap to open.

[Screenshot: tablet home screen with the CSEntry icon highlighted]

**Step 2:** From the CSEntry main menu, tap the application that matches the questionnaire you are about to administer — **FacilityHeadSurvey**, **PatientSurvey**, or **HouseholdSurvey**. Each application opens its own case list.

[Screenshot: CSEntry main menu showing the three installed instruments]

**Step 3:** Tap the **'+'** icon at the top of the screen to begin a new case (a new respondent or facility). The application will prompt you to enter the case identifier. Use the questionnaire number assigned to you by your STL (see *Questionnaire Number* sub-section above).

[Screenshot: CSEntry case list with the '+' icon highlighted]

**Step 4:** Tap the **right arrow** (→) at the bottom right of the screen to advance to the next item. Tap the **left arrow** (←) to go back if you need to correct a prior response. Save and resume is automatic — you may pause an interview and resume the same case later by tapping it in the case list.

[Screenshot: data-entry screen showing the item, response field, and navigation arrows]

**Step 5:** Where the questionnaire requires a verification photograph (one per case), tap the **camera** prompt to capture the photo using the rear camera of the tablet. Re-take if the image is blurry or the subject is not clearly visible. The application records the photo file reference along with the case data.

[Screenshot: photo-capture prompt with the camera icon]

**Step 6:** GPS coordinates are captured automatically at a designated point in the questionnaire. Before starting the interview, ensure the **Location** service icon is enabled in the tablet's notification bar. If it is disabled, swipe down from the top of the screen and tap **Location** to enable it. If GPS does not lock within one (1) minute, step outside or near a window and try again.

[Screenshot: tablet notification bar with the Location icon enabled]

**Step 7:** When you reach the last item, the application will prompt **"Accept this case?"** Tap **Yes** to mark the case as complete. The case will move from the in-progress list to the completed list.

[Screenshot: the "Accept this case?" prompt]

**Step 8:** At the end of the workday, when the tablet has reliable Wi-Fi or mobile-data connectivity, perform a synchronization to upload all completed cases to the central CSPro server (CSWeb).

- Tap the **synchronize** icon (two arrows in a circle) on the application's top bar.
- Wait until the message **"Sync successful"** appears. Do not close the application during sync.
- If sync fails, retry once more after confirming connectivity. If it continues to fail, flag the issue to your STL — completed cases remain stored on the tablet and will sync once the issue is resolved.

[Screenshot: sync icon and the "Sync successful" message]

**Step 9:** After a successful sync, completed cases are safely stored on the central server and visible to the data manager for review. You may continue with new cases or hand the tablet over to your STL for end-of-day review.

> **Note on data security:** Do not share your tablet or login with anyone outside your survey team. Do not delete cases or applications on the tablet without explicit instruction from your STL or the ASPSI CAPI team. If a tablet is lost, damaged, or stolen, notify your STL immediately so a replacement can be issued (refer to the Field Replacement Protocol).

---

## 2. Suggested addition — Appendix: CAPI Quick Reference Card

> *Suggested as a new appendix. Designed as a single-page card to be printed, laminated, and clipped to the enumerator's tablet case. Provides at-a-glance steps for the most common CAPI actions.*

### Appendix [\*\*]: CAPI Quick Reference Card

**Before starting an interview**

- Tablet is charged (≥ 50%) and Location service is enabled.
- Open **CSEntry** and select the correct instrument: **FacilityHeadSurvey** (F1), **PatientSurvey** (F3), or **HouseholdSurvey** (F4).
- Use the questionnaire number assigned to you by your STL.

**During the interview**

- Tap **'+'** to start a new case.
- Use **→** to advance and **←** to go back. The app saves automatically.
- Take the **verification photo** when prompted. Re-take if blurry.
- The **GPS** captures automatically — Location must be ON.

**To finish a case**

- Answer all items until the **"Accept this case?"** prompt.
- Tap **Yes** to complete. The case moves to the completed list.

**End of day**

- Connect to Wi-Fi or mobile data.
- Tap the **synchronize** icon (↻).
- Wait for **"Sync successful"** before closing the app.

**If something goes wrong**

- Sync failed → retry once; if it still fails, flag your STL.
- GPS won't lock → step outside or near a window; wait one minute.
- App freezes → close and reopen; cases are auto-saved.
- Tablet lost or damaged → notify your STL immediately.

**Contacts:** STL — [\*\*] / Field Supervisor — [\*\*] / Cluster RA — [\*\*]

---

## 3. Suggested addition — Appendix: CAPI Troubleshooting

> *Suggested as a new appendix. Lists common field issues with brief field-actionable resolutions, ordered by frequency. Issues that the enumerator cannot resolve are explicitly escalated to the STL or the CAPI team.*

### Appendix [\*\*]: CAPI Troubleshooting Guide

The table below lists common issues encountered during CAPI fieldwork and the field-level resolution. Issues marked **[Escalate]** must be flagged to the STL or the ASPSI CAPI team — do not attempt to resolve them yourself, as you may unintentionally affect data integrity.

| # | Issue | What to do |
|---|-------|-----------|
| 1 | Tablet won't power on | Plug into charger for at least 10 minutes, then try again. If still unresponsive — **[Escalate]** |
| 2 | CSEntry won't open or crashes immediately | Restart the tablet. If the app still won't open — **[Escalate]** (do not reinstall) |
| 3 | GPS does not lock within 1 minute | Confirm Location service is ON; step outside or near a window; wait another minute |
| 4 | Verification photo is blurry | Re-take the photo. The new photo replaces the old one |
| 5 | Mistakenly tapped wrong answer | Use the **←** arrow to go back; tap the correct response |
| 6 | Case appears in the in-progress list when you expected it complete | Open the case, tap → through to the end, accept the case at the prompt |
| 7 | Sync icon shows an error | Check Wi-Fi / mobile data; retry once; if it still fails — **[Escalate]** to STL |
| 8 | Case unexpectedly disappeared from the list | Do not start a new case for the same respondent. **[Escalate]** to STL — the case may still exist on the server |
| 9 | App displays a message you do not recognize | Take a clear photo of the screen and **[Escalate]** to STL or the CAPI team. Do not tap any prompt you don't understand |
| 10 | Tablet is running out of storage | **[Escalate]** to STL — sync may resolve it; do not delete files manually |
| 11 | Tablet lost, stolen, or damaged | **[Escalate]** to STL immediately so a replacement can be issued |

**Escalation contacts:**

- **First contact:** Survey Team Leader (STL) — refer to your cluster's STL contact card.
- **CAPI / technical issues:** ASPSI CAPI Team — [contact placeholder; insert email / Viber group reference once finalized].

---

## 4. Open questions / items needing ASPSI input

These came up while drafting; flagging them for your review, Kidd:

1. **Questionnaire Number scheme.** The current manual (under *The Survey Questionnaire → Questionnaire Number*) describes a 6-digit Region/Province/Municipality code + 3-digit case number (e.g., `035401004` for Magalang, Pampanga). Our F1 data dictionary uses the **9-digit PSGC code** (region + province + city/municipality + barangay) for the geography fields. The two schemes need to be reconciled — either the manual is updated to 9-digit, or the case-ID rule is documented as a separate identifier from the geography fields. I'd suggest the latter (case-ID stays human-friendly; PSGC is captured separately as full geo).
2. **CAPI vs PAPI.** The manual's introduction says "either using CAPI or PAPI". For UHC Survey Year 2, are we standing behind PAPI as a real fallback, or is that legacy text from the prior manual that should be removed? If PAPI is in scope, we'll need a paper-form deployment plan that's separate from CAPI.
3. **F2 (Healthcare Worker) handling in the manual.** The current draft only references "the survey questionnaire" generically. F2 is administered very differently from F1/F3/F4 (self-administered web link, optional interviewer-admin fallback). Suggest adding a short F2-specific sub-section to *Instructions for the Administration of the Questionnaire* — happy to draft if useful.
4. **Cluster headcount.** Manual says 6 supervising RAs + 20 FSs + 100 SEs. We sized the tablet procurement at ~126 units + 10–15% spares (email sent to Juvy on 2026-04-29). Please flag if the headcount has shifted so we can update procurement.
5. **Sync server reference.** The Quality Control section says "designated CSPro server" — once CSWeb is provisioned (Epic 4 backlog), the manual should reference it by its actual server name / URL. Holding placeholder `(CSWeb)` in the draft above for now.
6. **Appendix numbers.** I used `Appendix [\*\*]` placeholders to match the manual's existing convention. You'll want to assign final letters/numbers when the appendix list is locked.

---

## 5. Status

- **Section 1 (CSPro replacement):** ready to substitute into the master manual. Kidd to copy-paste, then update the section's appendix references and screenshot placeholders once F1/F3/F4 builds reach Designer-validated state.
- **Sections 2 & 3 (suggested appendices):** ready to add as new appendices. Kidd to assign appendix letters/numbers and adjust the contact placeholders.
- **Section 4 (open questions):** awaiting Kidd's review and ASPSI input where flagged.
