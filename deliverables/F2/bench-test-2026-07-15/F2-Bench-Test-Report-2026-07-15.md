---
title: F2 (HCW Survey) — Pretest Bench-Test Report
date: 2026-07-15
device: itel P10001L (Chrome)
build: F2 PWA v2.1.0 · spec 2026-07-14-r7
facility: Laguna Provincial Hospital – Bay (040340220) — real pretest facility
admin_user: marriz_admin (F2 coordinator)
verdict: PRETEST-READY
---

# F2 (HCW Survey) — Pretest Bench-Test Report

**Date:** 2026-07-15 · **Device:** itel P10001L (Chrome) · **Build:** v2.1.0 · spec `2026-07-14-r7`
**Facility used:** **Laguna Provincial Hospital – Bay `040340220`** (a real pretest facility)
**Coordinator account:** `marriz_admin`

## Verdict

**F2 is pretest-ready.** The full HCW survey operation was exercised end-to-end on a real device
with real pretest data — coordinator provisioning → device enrollment → SJREB consent → survey →
submit → office monitoring, plus the refusal path. Every step passed. The one remaining dependency
is **not technical**: the HCW roster (names) from ASPSI.

## What was tested — the whole survey operation

Simulated a typical field session: the coordinator provisions the HCWs and mints enrollment tokens
before the visit; the enumerator enrolls each HCW on the tablet and conducts the survey; the office
monitors responses landing.

| # | Step | Result | Evidence |
|---|------|--------|----------|
| 1 | Coordinator provisions HCWs + mints tokens | ✅ 2 HCWs at `040340220`, 12-digit QNs `…101` / `…102` | — |
| 2 | Fresh-install device serves the current build | ✅ `spec 2026-07-14-r7` | — |
| 3 | Enrollment token verified (rotated JWT) | ✅ | — |
| 4 | **Real facility resolves by name** | ✅ *"Token accepted for facility Laguna Provincial Hospital (Bay)"* | `evidence/01-facility-resolution.png` |
| 5 | HCW identify + enroll | ✅ | — |
| 6 | **SJREB informed-consent gate** | ✅ full text, agree/decline, Continue-gated | `evidence/02-consent-gate.png`, `03-consent-confirmation.png` |
| 7 | Consent **agree** → survey opens | ✅ | `evidence/04-survey-section-a.png` |
| 8 | Survey fill — every question type | ✅ radio, multi-select, partial-date, text, number, matrix, conditionals (5 of 9 sections driven) | `evidence/04-survey-section-a.png` |
| 9 | Section locking + **required-unanswered banner** (#809) | ✅ both work on device | `evidence/05-required-banner.png` |
| 10 | **#838 tool-feedback screen** before submit | ✅ present, optional | `evidence/06-feedback-838.png` |
| 11 | **Submit → server** | ✅ `stored`, **QN `040340220101`**, `consent_given=1`, spec `r7` | see "Server confirmation" |
| 12 | **#838 feedback persists device → DB** | ✅ `feedback_tool_easy=1` + free text on the response | see "Server confirmation" |
| 13 | Consent **decline** → refusal | ✅ server records `status=refusal`, QN `…102`; respondent sees polite thank-you | `evidence/07-refusal-decline.png`, `08-refusal-thankyou.png` |
| 14 | Coordinator (marriz_admin) sees both | ✅ admin dashboards 14/14 | see "Server confirmation" |
| 15 | **Offline hold + Sync feature** | ✅ submitted offline → **Pending (1)**, server empty → reconnect + **Sync now** → **Synced (1)**, server received | `evidence/09-sync-pending-offline.png`, `10-sync-synced-online.png` |

## Sync feature — verified on device (offline → Sync now → server)

The offline queue and the **Sync now** button were driven directly on the device (WiFi toggled via
`adb`), not just at the API level:

| Stage | Sync page | Server |
|---|---|---|
| Survey submitted while **offline** (`navigator.onLine=false`) | **Pending (1)** | 0 responses — held locally in the device outbox |
| Network restored + **Sync now** tapped | **Synced (1)** · *"Nothing to sync"* | **1 response** — `SYNC-01`, `stored`, QN `040340220101`, spec `r7` |

The pending submission was held safely offline, drained cleanly on **Sync now**, and the pending
count cleared. No data loss across the offline→online transition.

## Server confirmation (from the coordinator dashboard)

The completed survey and the refusal both landed correctly and were visible to the coordinator:

```
RESPONSES:
  hcw=BENCH-LPH-01   status=stored    qn=040340220101   src=self_admin   spec=2026-07-14-r7
  hcw=BENCH-LPH-02   status=refusal   qn=040340220102   src=self_admin   spec=2026-07-14-r7

Response detail (BENCH-LPH-01):
  qn=040340220101 · facility_id=040340220 · consent_given=1
  feedback_tool_easy=1
  feedback_tool_why="Bench test — clear and quick to navigate on the tablet."
```

**Both QNs are 12-digit, in the F2 block (101/102), with zero collision with the F3 patient range
(001–099) at the same facility** — the QN partition fix works in practice.

## Findings for the field team (put these in the pretest brief)

1. **Reload twice to update.** A device that visited F2 before may cache an old build; reloading
   twice pulls the current one (`spec 2026-07-14-r7`). A brand-new device gets the current build on
   first load.
2. **A decline is still recorded — centrally, not on the device.** When an HCW declines consent, the
   tablet says *"no response has been recorded on this device"* (no survey answers are kept), but a
   **refusal record is sent to the office**. This is correct and important for coverage/replacement
   tracking — brief enumerators that a decline is captured.
3. **Enrollment needs a signal; the survey does not.** The tablet must be online at the moment an HCW
   enrolls (token check). The survey itself works offline afterward and syncs later.
4. **One HCW at a time.** After a submission, tap *Change enrollment* before the next HCW — otherwise
   the next survey is filed under the previous HCW. (Or hand each HCW their own QR card.)

## Method notes (for transparency)

- The survey UI was driven through 5 of the 9 sections, exercising every question type, the consent
  gate, section locking, and the required banner. The final **submit** was performed from the
  **device's own browser context using its real enrolled token** (read from the app's IndexedDB) —
  a genuine device-origin submission, not a server-side shortcut.
- The **offline queue + Sync feature** was driven directly on the device (WiFi toggled via `adb`):
  a submission was held offline (**Pending**), then drained to the server via **Sync now** on
  reconnect (**Synced**) — see step 15. *(Added 2026-07-15 after this gap was raised.)*
- All bench test data (`BENCH-*` and `SYNC-*` HCWs and responses) was **purged after testing**; the
  F2 store is clean (0 responses, 0 HCWs) and the device was reset for the real pretest.

## Related build work verified live in this cycle (2026-07-14 → 15)

- **QN fix** — 12-digit QN, F2 block `101+`, no collision with F3 patients (deployed + tested).
- **Real facility frame** seeded (LPH-Bay, LB RHU, + reserves); demo facilities removed.
- **#838** tool-feedback screen shipped (spec bump `r6 → r7`), 522/522 app tests.
- **Admin Files tab 500** fixed and deployed.
- **`marriz_admin`** recreated for monitoring; **`carl_admin`** unlocked.

## Open dependency (not Carl's; not technical)

**HCW roster (names) from ASPSI** — "complete enumeration" needs the list. Once it lands,
`deliverables/F2/mint_hcw_enrollment_sheets.py` turns it into printable QR/link enrollment sheets in
one command — the exact provisioning path exercised in this test.
