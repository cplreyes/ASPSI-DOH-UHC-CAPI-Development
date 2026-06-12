# Household Survey (F4) — Tester Install & Test Guide

**UAT Round 4** · **App:** Household Survey (F4) on **CSEntry** (Android) · **Time:** ~25–30 minutes · **Updated:** 2026-06-12 · **Report issues in:** Slack **#f4-uat** + the GitHub form (Part F)

This guide walks you through installing the survey app, downloading the Household Survey, running a few short test interviews like a real household visit (including a **household roster** of members), sending them to the server, and reporting anything you notice. **No technical background needed** — follow the steps in order.

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
3. Choose **HouseholdSurvey** → **download / add**. It now shows on the CSEntry home screen.

## Part C — Allow Location & Camera
Tap **Allow** for **Location** and **Camera** when asked. *(Denied by accident? Settings → Apps → CSEntry → Permissions.)*

## Your test Questionnaire Number
The 12-digit number is Region(2)–Province(2)–City/Mun(3)–Facility(2)–Case(3). Use the valid test prefix **`010280001`** + your **3-digit tester number**. For F4, please use numbers in the **600s** to keep cases separate from the other surveys:

> **`010280001` + 6_ _** — e.g. **`010280001601`**, then `010280001602`, `010280001603`…

---

## Part D — Run the test interviews *(like a household visit)*

### TC-1 — Completed interview with a household roster (the main one)
1. Tap **HouseholdSurvey** → **new interview** (**+**).
2. **Questionnaire Number:** `010280001` + your number (e.g. `010280001601`). The app **auto-fills Region / Province / City names** — confirm they appear (read-only, intended). Pick the **Barangay** from the list.
3. **GPS fills in by itself** — when you reach the household GPS step an **"Obtaining GPS Location"** box opens on its own (no button). Near a window / outdoors is faster.
4. The **Informed Consent Form** (PART I: Information about the study) shows in full — **scroll through it**, then answer **Yes** to continue.
5. **Household roster** *(the important part to test):* enter the **number of household members**, then the app asks the member questions **once per member** (a repeating roster). Please:
   - Add **at least 3 members** (e.g. a 4-person household) and confirm it asks each member's details **in turn** (member 1, member 2, …).
   - Confirm the roster **stops at the number you entered** (doesn't keep asking forever, doesn't stop early).
   - Note whether moving **between members** feels clear.
6. Continue through the rest with reasonable **test** values. Please check:
   - **Several questions share one screen** (grouped) — scroll and answer them all.
   - **Date picker** for dates; **drop-downs** for long lists / **radio buttons** for short ones, with **auto-advance**.
   - **Blue instruction text** under some questions.
7. At the **end**, set the **Result of Visit** to **Completed**, then the **last screen is the Verification Photo** — take any test photo. **Save / complete.**

### TC-2 — Refused / withdrawn (no photo expected)
Start another case (e.g. `010280001602`). Answer consent **No**, or set **Result of Visit** to **Refused / Withdraw Participation/Consent**. The interview should **end** with **no photo step**.

### TC-3 — Partial save + resume *(mid-roster is a good test)*
Start a case, begin the roster, then press **Back** → **Partial Save**. Confirm the case shows a **partial** marker and you can **reopen and continue the roster** where you left off.

### TC-4 — "Other (specify)" behaviour
Tick **Other** on any question → confirm the **"specify" box appears and is required**. Untick Other → confirm the box **goes away / is skipped**.

### TC-5 — "Select all that apply" + exclusive option
Tick a normal option **and** an exclusive one (**"None of the above"**, **"I don't know"**, **"Not applicable"**) → confirm a **gentle warning** appears (warning, not a block).

*(Optional)* Try switching **language** to check translations.

## Part E — Send your data to the server *(sync)*
Back on the HouseholdSurvey case list → **Synchronize / Sync** → log in if asked → wait for **"Sync complete / success."**

## Part F — Report what you found
1. **GitHub form (one per finding):**
   **`https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=capi_uat_feedback.yml`**
   Pick **Instrument = F4**, the **scenario** (TC-1…TC-5), the **result**, and describe what you saw (screenshots help).
2. **Slack #f4-uat:** quick notes / screenshots / discussion.

Checklist to mention:
- **12-digit number** accepted + **names auto-filled**? **Barangay list** had entries?
- **Roster:** did it ask **once per member**, **stop at the right count**, and feel clear to move between members (TC-1)? Did **Partial Save resume mid-roster** (TC-3)?
- **GPS** filled by itself? **Consent text** displayed fully? **Grouped screens / date picker / drop-downs / auto-advance** OK?
- **Photo** appeared **only** on Completed (TC-1), **not** on Refused/Withdraw (TC-2)?
- **Other-specify** gated correctly (TC-4)? **Exclusive-option warning** showed (TC-5)?
- **Sync** finished? Anything **confusing/slow/broken**?

---

## Quick troubleshooting
- **Can't connect / download:** check internet; type the server address exactly (`https://…/csweb/api`).
- **Login fails:** re-type username (lowercase, no spaces) + password.
- **"…not found in PSGC":** re-enter the number starting `010280001` + your 3 digits (600s).
- **Roster keeps asking / stops early:** note the number of members you entered vs how many it asked, and tell us — that's exactly the kind of thing we're testing.
- **Old-looking screens (one question per screen):** older version — **⋮ → Update Installed Applications**, or remove and re-add (Part B).
- **GPS won't read / Camera won't open:** allow **Location** / **Camera** (Settings → Apps → CSEntry → Permissions); GPS may time out indoors — note it and move on.

*Thank you for testing! This is a pilot run — anything that feels off is useful feedback.*
