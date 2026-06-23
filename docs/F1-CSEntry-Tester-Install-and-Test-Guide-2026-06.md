# Facility Head Survey (F1) — UAT Round 4 · End-to-End Field-Day Dry-Run — Tester Guide

**Round:** 4 (CAPI testers' numbering) · **Type:** End-to-End Field-Day Dry-Run
**Drafted:** 2026-06-12 · **Opens:** 2026-06-12 (Fri, now) · **Closes:** 2026-06-15 (Mon, AM)
**Instrument:** F1 Facility Head Survey — CSPro **CSEntry** (Android) → **CSWeb**
**Companion guide:** `docs/CAPI-CSEntry-UAT-Round-4-CSWeb-Monitoring-Companion-Guide-2026-06.md` (the CSWeb monitoring side — your STL / data monitor walks it **live** while you interview)
**Coordinator:** Carl Patrick L. Reyes (Data Programmer / CAPI developer)
**Window:** Opens **Fri 2026-06-12** · Closes **Mon 2026-06-15 (AM)** — a weekend dry-run

> **Project context.** This is the **DOH UHC Survey Year 2 — Facility Head Survey (F1)**. Field rollout hands an Android tablet running **CSEntry** to an enumerator (Survey Enumerator), who interviews the **head of a sampled health facility**, then syncs the completed case up to **CSWeb** where the data team monitors it. **Round 4 is an end-to-end field-day dry-run** — the first time the full R4 build is walked the way fieldwork actually runs: install the app, download F1 from the server, interview like a real facility visit (offline, interruptions, GPS, photo), sync, and watch it land on CSWeb. The job is not to tick a checklist — it is to **run F1 like a real field day** and surface anything that would slow, confuse, or block a real enumerator or the monitoring team.

> **Why this round exists.** The R4 build carries a wave of changes that have **never been walked end-to-end by a tester acting like a real enumerator**: the survey now **groups related questions on one screen** (combined view, ~5–6× fewer taps), **GPS fills in by itself**, the **verification photo moved to the very end** and only appears **when the visit actually happened**, **"Other (specify)"** boxes now open **only** when "Other" is ticked, **"select all"** questions warn when you mix an exclusive option with others, and F1 picked up **range/date validations** (age 18–80, tenure, final-visit ≥ first-visit date). R4 is the rehearsal that proves the whole instrument holds together — content, flow, GPS, photo, sync — before it meets a real facility.

> **Scope of this guide.** F1 enumerator side only — what you see on the tablet. The **CSWeb monitoring** that confirms your synced cases arrive (Sync Report, map, per-stream counts) is in the companion guide; your STL / data monitor runs that **at the same time**, so coordinate timing — they should be watching your cases land as you sync.

---

## ⚠️ Coordinator pre-flight (Carl — do BEFORE opening the round)

R4 runs on the **live CSWeb** (`csweb.asiansocial.org`). The `040340002` test prefix segregates these throwaway cases from any real data; the monitor filters them out (and they can be purged after — see companion guide teardown).

1. **Deploy the R4 build ×3 to CSWeb** — F1 + F3 + F4 (the standard publish-and-deploy handoff). The F1 package carries: combined-view screens, GPS auto-fetch, photo-at-end + photo-gate, other-specify gating, exclusivity warnings, and F1 validation parity (age 18–80, tenure `age−20`, final-visit ≥ first-visit). Confirm `FacilityHeadSurvey` downloads cleanly on a real device once.
2. **Create the Slack channel** `#f1-uat` on `aspsi-doh-uhc-survey2.slack.com`; add the F1 testers + their STL + the data monitor; pin this guide.
3. **Confirm the GitHub feedback form is live** — `.github/ISSUE_TEMPLATE/capi_uat_feedback.yml` (committed/pushed). Confirm the label `from-uat-round-4-capi-2026-06` exists and the F1 tracking issue **[#368](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/368)** is open.
4. **Pre-assign each tester a Questionnaire-Number block** (last 3 digits, F1 = `1xx`) in Section 3 so cases don't collide on the server.
5. **CSWeb users are created** (§2 / §3) — `shan` / `kidd` (**Administrator**, also test the console) and `alytest` (Aly) / `aidan` (**Field Sync**) — each with a unique password. **Share** each F1 tester's **own username + password** privately (not in the public guide). Per-tester logins make every synced case attributable; keep the shared `setest` as a coordinator fallback only. (Canonical user list is in the companion guide §2; the same RA logins are reused across F1/F3/F4 — one account per person.)
6. **Tell the monitor** to open the companion guide and have CSWeb up when the round starts.

> Until steps 1–6 are done, this guide is a draft. Don't send it to testers with the assignment cells empty.

---

## 1. Quick Reference

| Item | Value |
|---|---|
| **App to install** | **CSEntry** (Android) — publisher *U.S. Census Bureau*, free, Google Play |
| **App to download from server** | **FacilityHeadSurvey** |
| **Server address (in CSEntry)** | `https://csweb.asiansocial.org/csweb/api` |
| **Server login (your own)** | your own CSWeb user — `shan` / `kidd` / `alytest` (Aly) / `aidan` (see §2 / §3) · password *(coordinator shares privately)*. **Not** the shared `setest`. |
| **Test facility prefix (always use)** | `040340002` (Region IV-A / Laguna · Cabuyao City Hospital — passes PSGC validation) |
| **Your QN block (F1)** | `040340002` + **1xx** — your assigned 3-digit block (see §3) |
| **What's new to look for** | combined screens · GPS auto-fetch · photo at the end (only if visit happened) · other-specify gating · exclusive-option warning · age/tenure/date checks |
| **Bug repo** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues |
| **Feedback form (one per finding)** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=capi_uat_feedback.yml |
| **Bug-filing label (auto-applied)** | `from-uat-round-4-capi-2026-06` |
| **Slack channel** | `#f1-uat` on `aspsi-doh-uhc-survey2.slack.com` |
| **F1 tracking issue** | [#368](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/368) |
| **Companion (monitor) guide** | `docs/CAPI-CSEntry-UAT-Round-4-CSWeb-Monitoring-Companion-Guide-2026-06.md` |

> **No technical background needed.** Just follow the steps in order and tell us what you saw. A screenshot/photo of the screen helps a lot.

---

## 2. Tester Roster

Play your role like a real field day — you are both the **enumerator** and (for the dry-run) the stand-in **facility head**.

| Tester | CSWeb username | Role | Field persona for the dry-run | Test device(s) |
|---|---|---|---|---|
| **Shan** (ASPSI RA) | `shan` | Primary enumerator + **CSWeb Admin** | Full **Completed** facility visit, start to finish — then also tests the **CSWeb console** (companion guide) | 10"+ Android tablet |
| **Kidd** (ASPSI main RA) | `kidd` | Enumerator + **CSWeb Admin** | Full visit on a **different device size** + the **Refused** path — then also tests the **CSWeb console** (companion guide) | Low-end / smaller Android phone (screen-size variety is the point) |
| **Aly** (ASPSI RA) | `alytest` | Enumerator (field user) | One full walk; pairs with the monitor (Marriz) at end-of-day | iPad / other tablet — variety |
| **Aidan** (ASPSI RA) | `aidan` | Enumerator (field user) | A second independent full walk + the offline / partial-save stress passes (5B.2–5B.4) | Another Android phone — variety |

> **Log into CSEntry with your own username above — not the shared `setest`** — so every synced case is attributable to you. `alytest` (Aly) / `aidan` are **Field Sync** logins (CSEntry only); **Shan, Kidd and Marriz are CSWeb Administrators** who also test the server/console side (companion guide), so both CSEntry and CSWeb get walked. The coordinator sets + shares passwords privately.

> **Each tester completes at least one WHOLE F1 interview (TC-1).** A dry-run is not spot-checks — it's the full instrument start to finish. Device variety (a big tablet AND a small/old phone) is how we catch combined-view layout problems before the field does. Between you, cover at least one **Completed** and one **Refused** case.

---

## 3. Your Test Questionnaire-Number Assignments

The interview opens with a **12-digit Questionnaire Number**: Region(2)–Province(2)–City/Mun(3)–Facility(2)–Case(3). Everyone uses the test prefix **`040340002`**; your **3-digit block** keeps your cases from clashing with other testers on the server.

| Tester | CSWeb username | QN block (F1 = `1xx`) | Example cases |
|---|---|---|---|
| **Shan** | `shan` | `040340002` + **`100`–`119`** | `040340002100`, `040340002101`, … |
| **Kidd** | `kidd` | `040340002` + **`120`–`139`** | `040340002120`, `040340002121`, … |
| **Aly** | `alytest` | `040340002` + **`140`–`159`** | `040340002140`, … |
| **Aidan** | `aidan` | `040340002` + **`160`–`179`** | `040340002160`, … |

> Use a **different last 3 digits for each case** you start (so a Completed and a Refused case don't overwrite each other). Coordinator fills the names + blocks above before sending. **Don't reuse another tester's block.**

> **📍 This round is set in Laguna (Cabuyao City Hospital · `040340002`).** Capture each case's GPS **where you actually are, around Los Baños / Laguna** — the test facility is in your province, so a correctly-run case now shows as **correctly located on the CSWeb Map (no "wrong area" flag)**. Keep the team testing from the **same general area** so the Map's location checks stay clean. An outdoor / near-window fix is best; an indoor desk case may leave GPS blank — that's expected, just say so.

---

## 4. Pre-Flight Checks (each tester, before testing)

1. **Android device + internet** (Wi-Fi or mobile data) ready.
2. **CSEntry installed** (Part 5A.1) and **FacilityHeadSurvey downloaded** from the server (5A.2).
3. **Already had an older version?** Open CSEntry's menu (**⋮**) → **Update Installed Applications** (or remove the app and re-add it) so you're on the **Round 4 build**. Quick way to tell you're on R4: questions are **grouped on one screen** and there's a **single 12-digit number** (not separate Region/Province/City questions).
4. **Permissions:** when first asked, tap **Allow** for **Location** and **Camera**. (Denied by accident? Phone **Settings → Apps → CSEntry → Permissions** → turn both on.)
5. **Have your own CSWeb username + password** (§2 / §3 — e.g. `shan`, *not* the shared `setest`) and your **QN block** ready.

---

## 5. The Field-Day Dry-Run

Run it as a real visit, in order: **5A → 5B → 5C → 5D → 5E** is one continuous pass. When you file a finding (Section 6), pick the matching **scenario** in the GitHub form — the `[TC-…]` tags below tell you which.

For anything that looks wrong, jot what you **expected** vs what **happened**. If it's about question **wording**, that may be a survey-design item (routed to the survey team), not a bug — flag it and say which you think it is.

### 5A — Install + download + cold start (act like Day 1 of fieldwork) · `[Install / download the app]`

**What you're rehearsing:** receiving the tablet and getting F1 onto it from a clean slate.

- **5A.1 (install CSEntry):** Play Store → search **CSEntry** → install **CSEntry** (*U.S. Census Bureau*, free) → open it.
- **5A.2 (download F1):** In CSEntry, **add an application** (a **+** / **⋮ menu**, usually near the top) → **from a CSWeb server** ("Add Application" → "From CSWeb"). Enter the server address **exactly** `https://csweb.asiansocial.org/csweb/api` → log in with **your own username** (e.g. `shan`, see §3) + password → choose **FacilityHeadSurvey** → **download / add**. It now shows on the CSEntry home screen. **Time it** — note how long the download took and whether anything was confusing.
- **5A.3 (start cold):** Tap **FacilityHeadSurvey** → start a **new interview** (**+**). Enter your QN (`040340002` + your number). Expect: the app **checks the number** and **auto-fills Region / Province / City names** — confirm they appear (you can't edit them; that's intended). Mistyped? You'll see *"…not found in PSGC"* — re-enter.

### 5B — Full interview under field conditions · `[TC-1 Completed]` `[TC-3 Partial save + resume]`

**What you're rehearsing:** a facility head interview completed in a real facility — not on perfect Wi-Fi.

- **5B.1 (full happy walk — the main one):** Work the whole interview through to the end with reasonable **test** values. Don't rush past validation — when the form blocks or warns you, confirm the message is clear and correct. As you go, confirm:
  - **Several questions share one screen** (grouped by topic) — scroll within the screen and answer them all.
  - **Dates** open a **date picker** (spinner), not 8 typed digits.
  - Long answer lists open as a **scrollable drop-down**; short ones as **radio buttons** — tapping an answer **moves on by itself**.
  - **Blue instruction text** appears under some questions (enumerator guidance).
  - **Barangay** opens a **list to pick from** — confirm it's **not empty**.
  - The **Informed Consent Form** (PART I: Information about the study) shows **in full** — scroll through it, then answer **Yes** to continue.
  - At the **end**, set **Result of Visit** to **Completed** → the **last screen is the Verification Photo** → take any test photo → **Save / complete**.
- **5B.2 (offline stretch):** Partway through, turn the device's **Wi-Fi / data OFF** (airplane mode). Keep answering. Expect: the form keeps working — no error banners, answers stay. (CSEntry is offline-first; you only need a connection to download and to sync.)
- **5B.3 (interruption + resume) `[TC-3]`:** Mid-interview, press your phone's **Back** → choose **Partial Save** in the "Stop Adding?" box. The case shows a **partial** marker in the list. **Tap it to reopen** and confirm you continue where you left off — no lost answers.
- **5B.4 (force-quit):** Once, fully **kill** CSEntry (swipe it away) and reopen. Expect: the partial case is still there and reopens cleanly.

### 5C — New-feature correctness spot-checks (the R4 build changes) · see TC tags

**What you're rehearsing:** confirming the changes that shipped in R4 actually behave right. Check these **as you reach them** during 5B — they're inline, not a separate pass.

| # | Feature | What to do | Confirm | Form scenario |
|---|---|---|---|---|
| **5C.1** | **Combined screens** | Reach any grouped screen | Related questions sit together, readable on your device, scroll within the screen works; nothing cut off | `Combined screens / date picker / drop-downs / auto-advance` |
| **5C.2** | **GPS auto-fetch** | Reach the GPS step | An **"Obtaining GPS Location"** box opens **on its own** (no button to tap); near a window/outdoors gets a faster fix; coordinates fill and **lock** | `GPS / Camera / Verification photo` |
| **5C.3** | **Photo at the end** | Finish a **Completed** case | The **verification photo is the very last step**, camera opens, you take a test photo | `GPS / Camera / Verification photo` |
| **5C.4** | **Photo gate (Refused)** `[TC-2]` | Run a **Refused** case (5C.7 below) | **No photo step at all** — proves the photo only appears for visits that happened | `TC-2 Refused / Withdrawn` |
| **5C.5** | **Other (specify) gating** `[TC-4]` | On a question with an **Other** option: tick **Other** | A **"specify" text box appears and asks you to type something**. Then **un-tick Other** → the specify box **goes away / is skipped** (you can't leave a stray "other" answer) | `TC-4 "Other (specify)" behaviour` |
| **5C.6** | **Exclusive-option warning** `[TC-5]` | On a "select all that apply" question, tick a normal option **and** an exclusive one (**"None of the above"** / **"I don't know"**) | A **gentle warning** appears that an exclusive option should be the only choice. It's a **warning, not a block** — you can still continue | `TC-5 "Select all" + exclusive-option warning` |
| **5C.7** | **Refused path** `[TC-2]` | Start a new case (next number), answer consent **No** **or** set **Result of Visit** to **Refused** | The interview **ends**, and there is **no verification-photo step** | `TC-2 Refused / Withdrawn` |
| **5C.8** | **Validation checks (F1)** | At the age/tenure/visit-date questions, try an out-of-range value | Age below 18 or a final-visit date **before** the first-visit date is caught; a very high age (>80) gives a soft confirm. Sensible combos pass | `General observation` |

> If any 5C item is **missing or misbehaving**, file it (Section 6). Wording problems are high-value — flag them even if everything "works", and note it may be a survey-design item.

### 5D — Sync + confirm it landed on CSWeb · `[Sync to the server]`

**What you're rehearsing:** the end of an interview and what the data team sees.

- **5D.1 (sync up):** Back on the FacilityHeadSurvey case list, choose **Synchronize / Sync** (circular-arrows icon) → log in with **your own username** if asked → wait for **"Sync complete / success."** Your Completed case uploads to the server.
- **5D.2 (confirm landing):** Tell your **monitor / STL** your **Questionnaire Number** + sync time. They confirm (companion guide) that it appears in **CSWeb → Sync Report**, the **View case** opens with the right answers, and — if your GPS got a real outdoor fix — a **pin shows on the Map**. This closes the loop a real field day depends on. (Indoor/desk cases may have a blank GPS — that's expected; say so.)

### 5E — Adversarial coda (the things most likely to bite in the field)

A short, sharp pass — pick the ones that fit your device.

- **5E.1 (real respondent text):** In any "Other (specify)" / open-text field, type special characters `< > & " ' /` and an emoji (🏥). Expect: preserved exactly through save + sync; no garbled display.
- **5E.2 (long text):** Paste a long (~500-char) string into an open-text field → accepted, preserved on reopen + sync.
- **5E.3 (day-later resume):** Partial-save a case, close everything, come back the next testing session, reopen → resumes at the saved point.
- **5E.4 (bad QN):** Type a number that doesn't start `040340002` → expect the *"…not found in PSGC"* rejection, with a clear way to re-enter.
- **5E.5 (language, optional):** Switch the **language** and confirm translated text appears (note anything untranslated — some locales aren't delivered yet).

---

## 6. Bug-Filing Format

For **every** finding, open a GitHub issue via the feedback form (one per finding):
**https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=capi_uat_feedback.yml**

Pick **Instrument = F1**, the matching **scenario** (the `[TC-…]` / form option from §5), the **result** (Pass / Pass-with-comment / Fail / Blocked), and describe what you saw in plain language. The form auto-applies `from-uat-round-4-capi-2026-06`. If you'd rather write it up by hand, use this shape:

```
**Round 4 (dry-run) step:** 5A / 5B / 5C.x / 5D / 5E.x
**Type:** CAPI bug  OR  survey-design/wording question (your best guess)
**Tester:** ‹your name / initials›
**Device:** Android tablet (model + Android version) / phone (model) / etc.
**Questionnaire Number:** 040340002 1xx
**Question / screen:** (e.g. "Section C grouped screen" / "GPS step" / "verification photo" / "Result of Visit")
**Expected:** [what the step says should happen]
**Actual:** [what happened]
**Reproduction steps:**
  1. ...
**Severity:** critical / high / medium / low
**Field impact:** [would this slow / confuse / block a real enumerator? how badly?]
**Screenshot / photo:** [attach — very helpful]
```

For quick discussion or anything urgent, also post in **`#f1-uat`**. Coordinator links each finding to the F1 tracking issue **#368** and triages daily.

---

## 7. Triage Cadence

- **Daily check-in:** Coordinator posts to `#f1-uat` daily ~09:00 PHT — new F1 findings, any critical blockers, fixes shipped overnight.
- **Mid-round sync:** any field-blocking critical (can't download F1, sync failing, a case lost, a wrong skip that drops questions) → same-day Slack huddle; don't wait for round close.
- **R4 close:** end of the sprint week. Coordinator reconciles **#368**; open items dispositioned (fix-now / next-sprint / route-to-survey-team / won't-fix-with-rationale). The round closes when the **exit criteria** (companion guide §8) are met and F1's open finding count is driven to **0**.

---

## 8. Why this round matters

Every R4 change was built and gate-checked in isolation — the combined-view layout, the GPS auto-fetch, the photo move, the other-specify gating, the exclusivity warnings, the new validations. What none of them has done is **survive a real interview on a real device, synced to a real server, watched by a real monitor.** A real field day doesn't test one feature at a time — it installs the app on a borrowed tablet, runs an interview with spotty signal and an interruption, fights a GPS fix by a window, takes the photo, syncs, and ends with someone on CSWeb asking "did it arrive, and does it look right?"

- **A whole F1 interview completes** end to end — not just isolated screens.
- **The combined-view layout holds on a real, possibly small/old, device** — the thing emulators and static gates can't prove.
- **GPS + photo behave in the real world** — auto-fetch by a window, photo only when the visit happened.
- **The sync → CSWeb-landing loop closes** — the moment the data team trusts the pipeline.

If F1 carries a clean field day here, it walks into the pretest confident. If it doesn't, this is the last cheap place to find out. Thanks for testing — treat it like the real day.

---

## Appendix — Quick troubleshooting

- **Can't connect / download:** check internet; type the server address exactly, with `https://` and `/csweb/api`.
- **Login fails:** re-type the username (all lowercase, no spaces) and password.
- **"Region/Province code not found in PSGC":** re-enter the number as `040340002` + your 3 digits.
- **Old-looking screens (one question per screen, separate Region/Province/City questions):** you're on an older version — **⋮ → Update Installed Applications**, or remove and re-add (5A.2).
- **GPS won't read:** move near a window / step outside; make sure **Location** is allowed and the phone's location is on. On a desk indoors it may time out and stay blank — note it and move on.
- **Camera won't open:** allow **Camera** (Settings → Apps → CSEntry → Permissions).
- **Sync fails:** confirm internet, re-enter **your own username** + password, retry. If it still fails, screenshot the error and post in `#f1-uat`.
