# Annex C — F2 PWA Field Operations Guide

**Audience:** Field Supervisors and Data Encoders
**Purpose:** Operational reference for the F2 Healthcare Worker Survey, delivered as a Progressive Web App (PWA), with paper-form fallback and offline-on-device support.
**Production URL:** `https://f2-pwa.pages.dev` (subject to change to a project subdomain prior to fieldwork).

---

## What the F2 PWA is

The F2 PWA is a self-administered web survey accessed by HCWs via QR code or direct link. It is **not** part of CSEntry; HCWs do not need to install anything. They open the link in any modern browser (Chrome, Safari, Edge), complete the survey, and submit. Submissions sync to the F2 backend (the Worker JWT proxy) immediately when the device is online.

## Three capture paths

The Protocol allows three ways for HCWs to complete F2:

| Path | When used | Who acts |
|---|---|---|
| **Path 1 — Online self-administered** | Default. HCW has a personal device with internet. | HCW only |
| **Path 2 — Offline-on-device** | Facility has poor connectivity, or HCW has no personal device. | HCW uses a facility-staged tablet running the F2 PWA in offline mode |
| **Path 3 — Paper-to-PWA encoded** | HCW prefers paper, or no device available. | HCW fills a paper form; Data Encoder enters responses into F2 PWA after fieldwork |

## Field Supervisor responsibilities

### Before posting F2 materials at the facility

1. Capture the facility's master HCW list in **F0b — HCW Master List** during the courtesy call. The list excludes Barangay Health Workers (Protocol §VIII).
2. Confirm HCW count and roles are recorded; this list is the formal denominator for the 60% response threshold.

### Posting F2 access materials

1. Post the printed F2 QR code poster in a visible area of the facility (staff lounge, nursing station, HR bulletin board).
2. Confirm with the facility focal person where the supervisor's tablet (Path 2) will be staged for HCWs without personal devices.
3. Distribute paper copies (Path 3) of the F2 questionnaire through the facility focal person.

### During the data collection window

1. Monitor response counts daily on the F2 admin portal.
2. If facility response is **≤ 40% at the midpoint** of the data collection window, follow up with the focal person to encourage participation. Document the follow-up in F0c (Daily Response Monitor).
3. If facility response remains **< 60% by the close of the window**, request a one-time three-day extension through the supervising Research Associate (per Protocol §XII).

### Closing the facility

1. Collect any paper forms still at the facility.
2. Note the final response count in F0c; if < 60%, escalate to the PI through F0e.

## Data Encoder responsibilities (Path 3 only)

1. Receive paper forms from the Field Supervisor at the end of fieldwork at the facility.
2. Open the F2 PWA admin portal and select **Encode Paper Submission**.
3. Enter the facility ID, encoder code, and the paper form's fields exactly as written.
4. The PWA validates each field and flags any inconsistencies with the form's logic. Resolve flags before submitting.
5. Mark the paper form as "Encoded" with date and encoder initials, and file it with the project's data-retention archive.

## F2 Admin Portal

The Field Supervisor's portal access is read-only and limited to facilities under the supervisor's coverage. The portal shows:

- Real-time response count per facility (denominator from F0b)
- Completion timestamps per submission
- Data quality flags (incomplete sessions, duplicate submissions)
- Per-question response distributions (for monitoring early)

The Data Encoder's portal access additionally allows the **Encode Paper Submission** action.

## When the PWA is unreachable

The F2 PWA is hosted on Cloudflare Pages with global redundancy; outages are rare but possible.

1. If the PWA loads slowly or returns errors, refresh the browser.
2. If still unreachable from multiple devices at the same facility, switch to **Path 3 — paper forms**. Encoders enter responses once the PWA is reachable again.
3. The Field Supervisor escalates a sustained outage (> 30 minutes) through F0e with severity High.

## Privacy and data retention

The F2 PWA is built to project Data Privacy Act compliance standards. Paper forms are physically secured at ASPSI after encoding and held per the project's retention schedule. HCW responses are pseudonymized in the analytic dataset; no facility-management or supervisor sees individual responses.
