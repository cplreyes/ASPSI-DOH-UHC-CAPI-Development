# Patient Survey (F3) — Tester Install & Test Guide

**UAT Round 4** · **App:** Patient Survey (F3) on **CSEntry** (Android) · **Time:** ~25–30 minutes · **Updated:** 2026-06-12 · **Report issues in:** Slack **#f3-uat** + the GitHub form (Part F)

This guide walks you through installing the survey app, downloading the Patient Survey, running a few short test interviews like a real patient-exit interview, sending them to the server, and reporting anything you notice. **No technical background needed** — just follow the steps in order.

> **Already installed an earlier version?** Open CSEntry's menu (**⋮**) → **Update Installed Applications** (or remove and re-add) so you get the **Round 4 build**. New in this build: related questions are now **grouped on one screen**, **GPS fills in by itself**, and the **verification photo is the last step** (only when the visit was actually done).

## What you need
- An **Android phone or tablet**, an **internet connection**
- Login details (provided separately):
  - **Server address:** `https://csweb.asiansocial.org/csweb/api`
  - **Username:** `setest` · **Password:** _(from the admin — keep it private)_
- Your **tester number** (a 3-digit number from the team)

---

## Part A — Install the CSEntry app *(one time)*
1. Open **Google Play Store** → search **CSEntry** → install **CSEntry** (publisher *U.S. Census Bureau*, free) → open it.

## Part B — Download the survey from the server
1. In CSEntry, **add an application** (**+** / **⋮**) → **from a CSWeb server**.
2. Server address: `https://csweb.asiansocial.org/csweb/api` → **log in** (**setest** + password).
3. Choose **PatientSurvey** → **download / add**. It now shows on the CSEntry home screen.

## Part C — Allow Location & Camera
Tap **Allow** for **Location** and **Camera** when asked. *(Denied by accident? Settings → Apps → CSEntry → Permissions.)*

## Your test Questionnaire Number
The 12-digit number is Region(2)–Province(2)–City/Mun(3)–Facility(2)–Case(3). Use the valid test prefix **`010280001`** + your **3-digit tester number**. For F3, please use numbers in the **500s** to keep cases separate from the other surveys:

> **`010280001` + 5_ _** — e.g. **`010280001501`**, then `010280001502`, `010280001503`…

---

## Part D — Run the test interviews *(like a patient-exit interview)*

### TC-1 — Completed interview (the main one)
1. Tap **PatientSurvey** → **new interview** (**+**).
2. **Questionnaire Number:** `010280001` + your number (e.g. `010280001501`). The app **auto-fills Region / Province / City names** — confirm they appear (read-only, intended).
3. **Patient Type:** choose **Outpatient** or **Inpatient** — this routes the interview to the right section later (Outpatient → Section G; Inpatient → Section H). *(Run TC-1 once as Outpatient and, if you have time, once as Inpatient — see TC-6.)*
4. **Geographic ID:** confirm the facility names auto-filled, and pick the facility **Barangay** from the list.
5. **Patient's home address:** choose the patient's **home Region → Province → City → Barangay** from the drop-downs — confirm each list **populates after you pick the one above it** (the lists narrow down step by step).
6. **GPS fills in by itself** — there are **two** GPS steps (the **facility** and the **patient's home**); each opens an **"Obtaining GPS Location"** box on its own (no button). Near a window / outdoors is faster.
7. The **Informed Consent Form** (PART I: Information about the study) shows in full — **scroll through it**, then answer **Yes** to continue.
8. Work through the questions with reasonable **test** values. Please check:
   - **Several questions share one screen** (grouped) — scroll and answer them all.
   - **Date picker** for dates; **drop-downs** for long lists, **radio buttons** for short ones, with **auto-advance** after you tap.
   - **Blue instruction text** under some questions.
9. At the **end**, set the **Result of Visit** to a **Completed** option, then the **last screen is the Verification Photo** — take any test photo. **Save / complete.**

### TC-2 — Refused / withdrawn (no photo expected)
Start another case (e.g. `010280001502`). Answer consent **No**, or set the **Result of Visit** to **Refused / Withdraw Participation/Consent**. The interview should **end** with **no photo step**.

### TC-3 — Partial save + resume
Answer a few questions, press **Back** → **Partial Save**. Confirm the case shows a **partial** marker and you can **reopen and continue**.

### TC-4 — "Other (specify)" behaviour
Tick **Other** on any question → confirm a **"specify" box appears and is required**. Untick Other → confirm the box **goes away / is skipped**.

### TC-5 — "Select all that apply" + exclusive option
Tick a normal option **and** an exclusive one (**"None"**, **"I don't know"**, **"There are no benefits…"**) → confirm a **gentle warning** appears (it's a warning, not a block).

### TC-6 — Patient-type routing *(if time allows)*
Run one **Outpatient** and one **Inpatient** case and confirm each reaches the **right care section** (Outpatient questions vs Inpatient questions), and you're **not** asked the other type's questions.

*(Optional)* Try switching **language** to check translations.

## Part E — Send your data to the server *(sync)*
Back on the PatientSurvey case list → **Synchronize / Sync** → log in if asked → wait for **"Sync complete / success."**

## Part F — Report what you found
1. **GitHub form (one per finding):**
   **`https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=capi_uat_feedback.yml`**
   Pick **Instrument = F3**, the **scenario** (TC-1…TC-6), the **result**, and describe what you saw (screenshots help).
2. **Slack #f3-uat:** quick notes / screenshots / discussion.

Checklist to mention:
- **12-digit number** accepted + **names auto-filled**? **Patient Type** routed correctly (TC-6)?
- **Patient-home address** drop-downs narrowed down step by step? **Both GPS** filled by themselves?
- **Consent text** displayed fully? **Grouped screens / date picker / drop-downs / auto-advance** OK?
- **Photo** appeared **only** on Completed (TC-1), **not** on Refused/Withdraw (TC-2)?
- **Other-specify** gated correctly (TC-4)? **Exclusive-option warning** showed (TC-5)?
- **Partial Save + resume** (TC-3)? **Sync** finished? Anything **confusing/slow/broken**?

---

## Quick troubleshooting
- **Can't connect / download:** check internet; type the server address exactly (`https://…/csweb/api`).
- **Login fails:** re-type username (lowercase, no spaces) + password.
- **"…not found in PSGC":** re-enter the number starting `010280001` + your 3 digits (500s).
- **Home-address list is empty:** make sure you picked the level above it first (Region → Province → City → Barangay, in order).
- **Old-looking screens (one question per screen):** older version — **⋮ → Update Installed Applications**, or remove and re-add (Part B).
- **GPS won't read / Camera won't open:** allow **Location** / **Camera** (Settings → Apps → CSEntry → Permissions); GPS may time out indoors — note it and move on.

*Thank you for testing! This is a pilot run — anything that feels off is useful feedback.*
