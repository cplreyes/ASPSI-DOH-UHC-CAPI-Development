---
type: deliverable
kind: enumerator-field-guide
audience: Field enumerators (CAPI) — first-time CSEntry users
instruments: [F1 Facility Head, F3 Patient, F4 Household]
status: scaffold — screenshots pending emulator capture (see "Screenshot plan")
date: 2026-06-07
related: [deliverables/training/2026-06-02-capi-enumerator-training-deck.md, deliverables/CSWeb/Field-Tablet-Sync-Configuration.md]
tags: [training, csentry, enumerator, field-guide, e7]
---

# CSEntry on Your Tablet — A Step-by-Step Guide for Enumerators

> Plain-language, screenshot-driven walkthrough of using the **CSEntry** app to collect the DOH UHC
> Year-2 survey on an Android tablet. No technical background needed — follow the pictures.
>
> **Companion to** the CAPI Enumerator Training Deck. This guide is the *"how do I actually tap through
> the app"* reference enumerators keep on hand in the field.

> [!note] Build status (2026-06-07)
> Written scaffold + **screenshot pipeline proven**. A headless Android **Pixel-Tablet emulator** (API 34,
> CSEntry **8.0.1** installed) is set up and `adb screencap` captures real 2560×1600 tablet screens. The
> **generic getting-started screens are captured** (`deliverables/training/csentry-screenshots/`:
> terms-of-service, empty home). The **survey-specific** `📷 [SCREENSHOT: …]` slots stay placeholders until
> the app is **compiled (S009)** and **uploaded to CSWeb** (E4-CSWeb-003) — then CSEntry syncs it from
> `csweb.asiansocial.org` and the remaining screens batch-capture into their slots.

---

## 0. What you need before you start
- An Android tablet issued by the field team (charged, with mobile data or Wi-Fi).
- The **CSEntry** app installed (Section 1).
- Your **sync username + password** (given by your supervisor — keep it private).
- The **CSWeb server address**: `csweb.asiansocial.org`.

📷 [SCREENSHOT: tablet home screen with the CSEntry icon visible]

---

## 1. Installing CSEntry (one time)
1. Open the **Google Play Store**.
2. Search **"CSEntry"** (by the U.S. Census Bureau).
3. Tap **Install**, wait for it to finish, then **Open**.

📷 [SCREENSHOT: Play Store CSEntry listing — Install button]
✅ [CAPTURED: `csentry-screenshots/01-csentry-terms-of-service.png` — first launch shows the Terms of Service; tap **ACCEPT**, then **Allow** the location/camera/storage permissions when prompted]
✅ [CAPTURED: `csentry-screenshots/02-csentry-home-no-apps.png` — the CSEntry home before any survey is added ("There are no applications on your device")]

> If your tablet was pre-configured by the field team, CSEntry may already be installed — skip to §2.

---

## 2. Connecting your tablet to the survey server (one time)
This tells CSEntry where to download the survey from.
1. In CSEntry, open the menu (☰) → **Sync**  → **Add server** (or **CSWeb settings**).
2. Server URL: type `https://csweb.asiansocial.org/csweb`.
3. Enter your **username** and **password**.
4. Tap **Save / Connect**. A success message confirms the connection.

📷 [SCREENSHOT: CSEntry sync-server settings with the CSWeb URL filled in]
📷 [SCREENSHOT: login fields (username/password)]
📷 [SCREENSHOT: "connected successfully" confirmation]

---

## 3. Downloading the survey to your tablet (sync down)
1. Menu (☰) → **Sync**.
2. Choose the survey you're assigned to: **Facility Head (F1)**, **Patient (F3)**, or **Household (F4)**.
3. Tap **Get Application / Download**. CSEntry downloads the questionnaire.
4. When it finishes, the survey appears on your CSEntry home screen.

📷 [SCREENSHOT: sync screen listing the available applications]
📷 [SCREENSHOT: download-complete state]
📷 [SCREENSHOT: CSEntry home now showing the survey(s)]

---

## 4. Choosing your language
The survey runs in **English** plus the local dialects that have been translated (Cebuano, Bisaya,
Waray, Bicolano — and Hiligaynon for F1). You can switch any time during an interview.
1. Open the survey → menu → **Language**.
2. Pick the language you'll use with this respondent.

📷 [SCREENSHOT: language picker showing the available languages]
📷 [SCREENSHOT: same question shown in English vs a dialect (side by side in the guide)]

> If a question hasn't been translated yet, it shows in **English** — that's expected; just read it as-is.

---

## 5. Starting a new interview (a "case")
1. On the survey home, tap **Add / New case**.
2. Fill the **ID block** in order — these identify the facility and the interview:
   `Region → Province/HUC → City/Municipality → Facility No. → Case sequence`.
   Each choice narrows the next (pick a region and only its provinces appear — the **PSGC cascade**).

📷 [SCREENSHOT: "Add new case" button]
📷 [SCREENSHOT: Region dropdown]
📷 [SCREENSHOT: Province list filtered by the chosen region (cascade)]
📷 [SCREENSHOT: completed ID block]

---

## 6. Answering questions & how the app moves
- **One question per screen.** Tap your answer (or type a number), then **Next (→)** to continue.
- **Back (←)** returns to the previous question if you need to fix an answer.
- **Skip logic is automatic:** the app only shows questions that apply. If a question disappears or is
  skipped, that's correct — don't worry that you "missed" it.
- **Single-choice** = pick one. **Multi-choice** = tap all that apply, then Next.
- **"None of the above" / "I don't know"** behave specially on some questions (they clear other choices).

📷 [SCREENSHOT: a single-choice question]
📷 [SCREENSHOT: a multi-select question with several ticked]
📷 [SCREENSHOT: a numeric-entry question with the keypad]

---

## 7. Special screens you'll meet
- **Consent:** if the respondent declines, choose the refuse option — the app ends the interview cleanly.
- **GPS:** at the facility, the app captures location automatically — allow it a moment to get a fix.
- **Photo (F1):** take the verification photo when prompted.
- **Roster (F4 Household):** add one row per household member; you can edit or remove members.
- **Expenditure grid (F4):** enter the peso amounts in each box.

📷 [SCREENSHOT: consent screen]
📷 [SCREENSHOT: GPS capture in progress]
📷 [SCREENSHOT: photo capture prompt]
📷 [SCREENSHOT: F4 roster — list of members + add button]
📷 [SCREENSHOT: F4 expenditure grid]

---

## 8. When the app warns you
- **Soft warning** (yellow): the value looks unusual — check it; you *can* continue if it's correct.
- **Hard stop** (red): the value isn't allowed (e.g., age out of range) — you must fix it to continue.

📷 [SCREENSHOT: a soft-warning message]
📷 [SCREENSHOT: a hard-stop validation message]

---

## 9. Pausing & resuming
- CSEntry **auto-saves** as you go. To stop mid-interview, just go **Back** to the case list — your
  answers are kept.
- To resume: open the survey, tap the **partial case**, and continue where you left off.

📷 [SCREENSHOT: case list showing a partial (in-progress) case]

---

## 10. Finishing an interview
1. Answer the last question → the app asks to **save** the case.
2. Confirm the **disposition** (completed / refused / etc.) if prompted.
3. The case is now marked done on your case list.

📷 [SCREENSHOT: end-of-case save prompt]
📷 [SCREENSHOT: case list with a completed case]

---

## 11. Sending your work to the server (sync up) — **do this daily**
1. Connect to Wi-Fi or mobile data.
2. Menu (☰) → **Sync** → **Send data / Upload**.
3. Wait for "sync complete." Your completed cases are now safely on the server.

📷 [SCREENSHOT: sync-up screen]
📷 [SCREENSHOT: "sync complete" confirmation]

> **Why daily:** syncing backs up your work and lets supervisors see progress. If your tablet is lost
> or breaks, anything you've synced is safe.

---

## 12. If something goes wrong
| Problem | What to do |
|---|---|
| Sync fails / "cannot reach server" | Check internet; confirm the server URL `csweb.asiansocial.org/csweb`; try again. Your data is safe locally meanwhile. |
| Forgot password | Contact your supervisor — don't share or guess. |
| GPS won't get a fix | Step outside / near a window; wait 30–60s; allow location permission. |
| App froze | Close and reopen CSEntry — auto-saved answers are kept. |
| Wrong language | Menu → Language → switch. |

---

## Do's and Don'ts
✅ Sync up at the end of every day. ✅ Keep your login private. ✅ Trust the skip logic.
❌ Don't share the tablet login. ❌ Don't force answers past a red hard-stop. ❌ Don't delete a case unless your supervisor says so.

---

## Screenshot plan (internal — remove before field release)
Capture source: **Android emulator running CSEntry**, app synced from `csweb.asiansocial.org`, on F1
first (then F3/F4 for the instrument-specific shots). Method: `adb exec-out screencap -p > NN.png`,
named to the `📷` markers above. **Gated on:** S009 Designer compile + E4-CSWeb-003 (app uploaded to
CSWeb). Until then this guide ships as text-only draft for review.
