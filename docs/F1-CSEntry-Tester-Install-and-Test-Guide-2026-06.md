# Facility Head Survey (F1) — Tester Install & Test Guide

**UAT Round 4** · **App:** Facility Head Survey (F1) on **CSEntry** (Android) · **Time:** ~20–25 minutes · **Updated:** 2026-06-12 · **Report issues in:** Slack **#f1-uat** + the GitHub form (Part F)

This guide walks you through installing the survey app, downloading the Facility Head Survey, running a few short test interviews like a real field visit, sending them to the server, and reporting anything you notice. **No technical background needed** — just follow the steps in order.

> **Already installed an earlier version?** Open CSEntry's menu (**⋮**) → **Update Installed Applications** (or remove the app and re-add it) so you get the **Round 4 build**. New in this build: the survey now **groups related questions on one screen**, **GPS fills in by itself**, and the **verification photo is the last step** (only when the visit was actually done).

## What you need
- An **Android phone or tablet**
- An **internet connection** (Wi-Fi or mobile data)
- Login details (provided separately by the team):
  - **Server address:** `https://csweb.asiansocial.org/csweb/api`
  - **Username:** `setest`
  - **Password:** _(provided by the admin — keep it private)_
- Your **tester number** (the team gives you a 3-digit number, e.g. `101`) — you'll use it in the Questionnaire Number

---

## Part A — Install the CSEntry app *(one time)*
1. Open the **Google Play Store**.
2. Search for **CSEntry**.
3. Install the app named **CSEntry** (publisher: *U.S. Census Bureau*) — it's free.
4. Open it once it finishes installing.

## Part B — Download the survey from the server
1. In CSEntry, open the menu to **add an application** (a **+** or **⋮ / menu**, usually near the top).
2. Choose to add **from a CSWeb server** ("Add Application" → "From CSWeb").
3. Enter the **Server address** exactly: `https://csweb.asiansocial.org/csweb/api`
4. **Log in:** Username **setest**, Password *(provided)*.
5. Choose **FacilityHeadSurvey** and **download / add** it.
6. Wait for it to finish — **FacilityHeadSurvey** now shows on the CSEntry home screen.

## Part C — Allow Location & Camera *(so GPS and photo work)*
When the app first needs them, your phone asks for permission:
- Tap **Allow** for **Location**
- Tap **Allow** for **Camera**

*(Tapped Deny by accident? Phone **Settings → Apps → CSEntry → Permissions**, turn on Location and Camera.)*

## Your test Questionnaire Number
The interview starts with a **12-digit Questionnaire Number**: Region(2) – Province(2) – City/Mun(3) – Facility(2) – Case(3). For testing, always use the valid test prefix **`010280001`** (a real test facility in Region I / Ilocos Norte) followed by your **3-digit tester number**:

> **`010280001` + your number** — e.g. tester 101 → **`010280001101`**.

Use a **different last 3 digits for each test case** (e.g. 101, 102, 103…) so your cases don't clash.

---

## Part D — Run the test interviews *(like a field visit)*
Please run these short scenarios. Each one is also a choice in the report form (Part F).

### TC-1 — Completed interview (the main one)
1. Tap **FacilityHeadSurvey** → start a **new interview** (**+**).
2. **Questionnaire Number:** type `010280001` + your number (e.g. `010280001101`).
   - The app checks it and **auto-fills Region / Province / City names** — confirm they appear (you can't edit them; that's intended).
   - Mistyped? You'll see *"…not found in PSGC"* — just re-enter.
3. Work through the screens with reasonable **test** values. Please check, as you go:
   - **Several questions now share one screen** (grouped by topic) — scroll within the screen and answer them all.
   - **Dates** open a **date picker** (spinner), not 8 typed digits.
   - Long answer lists open as a **scrollable drop-down**; short ones as **radio buttons** — tapping an answer **moves on by itself**.
   - **Blue instruction text** appears under some questions (guidance for the enumerator).
   - **Barangay** opens a **list to pick from** — confirm it's not empty.
   - **GPS fills in by itself**: when you reach the GPS step an **"Obtaining GPS Location"** box opens on its own (no button to tap). Near a window / outdoors gets a faster fix; the coordinates fill and lock.
   - The **Informed Consent Form** (PART I: Information about the study) shows in full — **scroll through it**, then answer **Yes** to continue.
4. At the **end**, set the **Result of Visit** to **Completed**, then the **last screen is the Verification Photo** — the camera opens; take any test photo.
5. **Save / complete** the interview.

### TC-2 — Refused visit (no photo expected)
Start another case (next number, e.g. `010280001102`). At the consent question answer **No** (or set the **Result of Visit** to **Refused**). The interview should **end** and there should be **no verification-photo step**. *(This checks the photo only appears for visits that actually happened.)*

### TC-3 — Partial save + resume
Start a case, answer a few questions, then press your phone's **Back** button → choose **Partial Save** in the "Stop Adding?" box. The case shows a **partial** marker in the list. **Tap it to reopen** and confirm you continue where you left off.

### TC-4 — "Other (specify)" behaviour
On any question with an **Other** option: tick **Other** and confirm a **"specify" text box appears and asks you to type something**. Then change your answer so **Other is not ticked**, and confirm the **specify box goes away / is skipped** (you should not be able to type a stray "other" answer).

### TC-5 — "Select all that apply" + exclusive option
On a "select all that apply" question, tick a normal option **and** an exclusive one like **"None of the above"** or **"I don't know"** together. The app should show a **gentle warning** that an exclusive option should be the only choice. *(It's a warning, not a block — you can still continue.)*

*(Optional)* Try switching the **language** to check translations appear.

## Part E — Send your data to the server *(sync)*
1. Back on the FacilityHeadSurvey case list, choose **Synchronize / Sync** (circular-arrows icon).
2. Log in again with **setest** + password if asked.
3. Wait for **"Sync complete / success."** Your completed cases upload to the server.

## Part F — Report what you found
**Two ways — please use both:**
1. **GitHub form (one per finding):** open
   **`https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=capi_uat_feedback.yml`**
   Pick **Instrument = F1**, the **scenario** (TC-1…TC-5), the **result** (Pass / Pass-with-comment / Fail / Blocked), and describe what you saw in plain language. A screenshot/photo helps a lot.
2. **Slack #f1-uat:** post a quick note / screenshot for anything urgent or to discuss.

Quick checklist to mention:
- App **downloaded & opened** OK? **12-digit number** accepted + **names auto-filled**?
- **Grouped screens** readable? **Date picker / drop-downs / auto-advance** feel right?
- **Barangay list** had entries? **GPS** filled by itself? **Photo** appeared **only** on the Completed case (TC-1), **not** on the Refused one (TC-2)?
- **Other-specify** appeared only when you ticked Other? **Exclusive-option warning** showed (TC-5)?
- **Partial Save + resume** worked? **Sync** finished?
- Anything **confusing, slow, or broken**?

The team confirms on the server that your cases arrived (CSWeb monitoring).

---

## Quick troubleshooting
- **Can't connect / download:** check internet; type the server address exactly, with `https://` and `/csweb/api`.
- **Login fails:** re-type username (all lowercase, no spaces) and password.
- **"Region/Province code not found in PSGC":** re-enter the number starting `010280001` + your 3 digits.
- **Old-looking screens (one question per screen, separate Region/Province/City questions):** older version — **⋮ → Update Installed Applications**, or remove and re-add (Part B).
- **GPS won't read:** move near a window / step outside; make sure **Location** is allowed and the phone's location is on. *(On a desk/indoors it may time out and stay blank — note it and move on.)*
- **Camera won't open:** allow **Camera** (Settings → Apps → CSEntry → Permissions).

*Thank you for testing! This is a pilot run — anything that feels off is useful feedback.*
