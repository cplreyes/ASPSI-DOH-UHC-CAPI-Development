# Annex B — CAPI Field Troubleshooting Guide

**Audience:** Enumerators and Field Supervisors
**Purpose:** Quick-reference for the most common CAPI issues encountered in the field. For anything not on this list, contact the Field Supervisor; if unresolved, the Field Supervisor escalates to the Data Programmer through F0e (Issue Ticket).

---

## CSEntry application

### The application will not open

1. Confirm the tablet has at least 1 GB free storage (Settings → Storage). Photos and old cases may need to be cleared.
2. Force-stop CSEntry (Settings → Apps → CSEntry → Force Stop), then reopen.
3. Restart the tablet.
4. If still failing, log the issue in F0e and escalate to the Data Programmer; do not uninstall and reinstall CSEntry without instruction (uninstalling deletes any unsynced cases on the device).

### A case will not save

1. Check that no required fields are empty. CSEntry highlights missing fields in red.
2. Confirm storage is not full.
3. Save the case as **partial** if you cannot complete it now; the case remains on the tablet under its case ID.

### A case will not sync to CSWeb

1. Confirm the tablet is connected to the internet — open Chrome and load any web page to test.
2. Confirm the tablet's date and time are correct (sync fails if the clock is wrong).
3. Tap the sync icon again. If the sync attempt fails, do not delete the case.
4. Show the case to the Field Supervisor before leaving the facility. The Data Programmer can recover the case from the tablet if needed.

### "Successfully synced" did not appear

1. Wait 60 seconds; a slow connection may delay the confirmation.
2. Re-open the application and check the case-listing screen — synced cases show a cloud icon.
3. If no cloud icon and no error message, log F0e for the Data Programmer.

## GPS and location

### GPS coordinates show 0,0 or are not captured

1. Confirm Location is turned on (Settings → Location → On).
2. Move outside or near a window — GPS does not lock indoors with thick walls or basement levels.
3. Wait 30–60 seconds for the lock; the GPS indicator will turn green when locked.
4. If still no lock, note this in the case's notes field and proceed; the Field Supervisor records the case as having a GPS exception in F0c.

### GPS accuracy is poor (>100 m)

The application will warn but allow you to proceed. Try to retake the GPS reading once outside or in a more open area before completing the case.

## Verification photo

### The camera will not open from the application

1. Confirm Camera permission is granted to CSEntry (Settings → Apps → CSEntry → Permissions → Camera → Allow).
2. Close other camera apps that may be holding the camera.
3. Restart the tablet if needed.

### A photo will not save with the case

1. Confirm storage is not full.
2. Try retaking the photo; the original capture may have failed.
3. If still failing, save the case without the photo and log F0e — the Data Programmer can attach the photo manually if you take it with the tablet's stock camera.

## F0 Supervisor App specific

### F0c Daily Response Monitor is not pulling counts from CSWeb

1. Confirm internet connectivity.
2. Tap "Refresh" in the F0c form.
3. If counts still do not load, enter the counts manually from the case-listing screens of F1, F3a, and F4a; mark "manual entry" in the form.

### Cannot link a replacement case in F0d

The original case must already be in CSWeb. Sync first, then link the replacement.

## Escalation

For any issue not resolved by the steps above, the Field Supervisor logs an F0e Issue Ticket with severity Medium or higher. Tickets are reviewed by the Data Programmer daily; urgent (severity Blocker) issues are reached directly via Viber to the project's CAPI channel.
