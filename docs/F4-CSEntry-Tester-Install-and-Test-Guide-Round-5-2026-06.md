# Household Survey (F4) — UAT Round 5 · End-to-End Field-Day Dry-Run — Tester Guide

**Round:** 5 (CAPI testers' numbering) · **Type:** End-to-End Field-Day Dry-Run
**Drafted:** 2026-06-21 · **Opens:** 2026-06-22 (Mon AM) · **Closes:** 2026-06-27 (Fri PM)
**Instrument:** F4 Household Survey — CSPro **CSEntry** (Android) → **CSWeb**
**Companion guide:** `docs/CAPI-CSEntry-UAT-Round-5-CSWeb-Monitoring-Companion-Guide-2026-06.md` (the CSWeb monitoring side — your STL / data monitor walks it **live** while you interview)
**Coordinator:** Carl Patrick L. Reyes (Data Programmer / CAPI developer)
**Window:** Opens **Mon 2026-06-22** · Closes **Fri 2026-06-27** — a work-week round

> **Project context.** This is the **DOH UHC Survey Year 2 — Household Survey (F4)**. Field rollout hands an Android tablet running **CSEntry** to an enumerator, who visits a **sampled household**, lists its members, and interviews about the household, then syncs the case up to **CSWeb** where the data team monitors it. F4's signature is the **household roster** — a repeating block that asks member questions **once per household member**. **Round 5 is an end-to-end field-day dry-run** — the first full walk of the R5 build the way fieldwork actually runs: install, download F4, interview like a real household visit (roster, offline, interruptions, GPS, photo), sync, and watch it land on CSWeb. Run F4 like a real field day and surface anything that would slow, confuse, or block a real enumerator or the monitoring team.

> **Why this round exists.** The R5 build carries changes that have **never been walked end-to-end by a tester acting like a real enumerator**: the survey now **groups related questions on one screen** (combined view, ~5–6× fewer taps), **GPS fills in by itself**, the **verification photo moved to the very end** and only appears **when the visit actually happened**, **"Other (specify)"** boxes open **only** when "Other" is ticked, and **"select all"** questions warn when you mix an exclusive option with others. On top of that, F4's **household roster** — the repeating member block — needs a real run to prove it asks the right number of times and resumes correctly mid-roster. R5 is the rehearsal that proves the whole instrument holds together before it meets a real household.

> **Scope of this guide.** F4 enumerator side only — what you see on the tablet. The **CSWeb monitoring** that confirms your synced cases arrive (Sync Report, map, per-stream counts, roster members in the case) is in the companion guide; your STL / data monitor runs that **at the same time**, so coordinate timing.

---

## ⚠️ Coordinator pre-flight (Carl — do BEFORE opening the round)

R5 runs on the **live CSWeb** (`csweb.asiansocial.org`). The `040340002` test prefix segregates these throwaway cases from real data; the monitor filters them out (and they can be purged after — see companion guide teardown).

1. **Deploy the R5 build ×3 to CSWeb** — F1 + F3 + F4. The F4 package carries: combined-view screens, GPS auto-fetch, photo-at-end + photo-gate, other-specify gating, exclusivity warnings, and the household-roster block. Confirm `HouseholdSurvey` downloads cleanly on a real device once.
2. **Confirm the Slack channel** `#f4-uat` on `aspsi-doh-uhc-survey2.slack.com`; add the F4 testers + their STL + the data monitor; pin this guide.
3. **Confirm the GitHub feedback form is live** — `.github/ISSUE_TEMPLATE/capi_uat_feedback.yml`. Confirm the label `from-uat-round-5-2026-06` exists and the F4 tracking issue **`#721`** is open.
4. **Pre-assign each tester a Questionnaire-Number block** (F4 = `6xx`) in Section 3.
5. **CSWeb users are created** (§2 / §3) — `shan` / `kidd` (**Administrator**, also test the console) and `alytest` (Aly) / `aidan` (**Field Sync**) — each with a unique password. **Share** each F4 tester's **own username + password** privately (not in the public guide). Per-tester logins make every synced case attributable; keep `setest` as a coordinator fallback only. (Canonical user list is in the companion guide §2; the same RA logins are reused across F1/F3/F4 — one account per person.)
6. **Tell the monitor** to open the companion guide and have CSWeb up when the round starts.

> Until steps 1–6 are done, this guide is a draft. Don't send it with the assignment cells empty.

---

## 1. Quick Reference

| Item | Value |
|---|---|
| **App to install** | **CSEntry** (Android) — publisher *U.S. Census Bureau*, free, Google Play |
| **App to download from server** | **HouseholdSurvey** |
| **Server address (in CSEntry)** | `https://csweb.asiansocial.org/csweb/api` |
| **Server login (your own)** | your own CSWeb user — `shan` / `kidd` / `alytest` (Aly) / `aidan` (see §2 / §3) · password *(coordinator shares privately)*. **Not** the shared `setest`. |
| **Test facility prefix (always use)** | `040340002` (Region IV-A / Laguna · Cabuyao City Hospital — passes PSGC validation) |
| **Your QN block (F4)** | `040340002` + **6xx** — your assigned 3-digit block (see §3) |
| **What's new to look for** | combined screens · GPS auto-fetch · photo at the end (only if visit happened) · other-specify gating · exclusive-option warning · **household roster** (repeating members) |
| **Bug repo** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues |
| **Feedback form (one per finding)** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=capi_uat_feedback.yml |
| **Bug-filing label (auto-applied)** | `from-uat-round-5-2026-06` |
| **Slack channel** | `#f4-uat` on `aspsi-doh-uhc-survey2.slack.com` |
| **F4 tracking issue** | `#721` |
| **Companion (monitor) guide** | `docs/CAPI-CSEntry-UAT-Round-5-CSWeb-Monitoring-Companion-Guide-2026-06.md` |

> **No technical background needed.** Follow the steps in order and tell us what you saw; a screenshot helps a lot.

---

## 2. Tester Roster

Play your role like a real field day — you are both the **enumerator** and the stand-in **household respondent**. F4's catch: the **roster** must be walked with a realistic multi-member household.

| Tester | CSWeb username | Role | Field persona for the dry-run | Test device(s) |
|---|---|---|---|---|
| **Shan** (ASPSI RA) | `shan` | Primary enumerator + **CSWeb Admin** | A full **Completed** household visit with a **4–5 member roster** — then also tests the **CSWeb console** (companion guide) | 10"+ Android tablet |
| **Kidd** (ASPSI main RA) | `kidd` | Enumerator + **CSWeb Admin** | A full visit with a **different household size** (e.g. 2 members) + the **Refused** path — then also tests the **CSWeb console** (companion guide) | Low-end / smaller Android phone |
| **Aly** (ASPSI RA) | `alytest` | Enumerator (field user) | One full walk (incl. mid-roster partial save); pairs with the monitor (Marriz) at end-of-day | iPad / other tablet — variety |
| **Aidan** (ASPSI RA) | `aidan` | Enumerator (field user) | A second full walk with a **different roster size** + offline / partial-save mid-roster | Another Android phone — variety |

> **Log into CSEntry with your own username above — not the shared `setest`** — so every synced case is attributable to you. `alytest` (Aly) / `aidan` are **Field Sync** logins (CSEntry only); **Shan, Kidd and Marriz are CSWeb Administrators** who also test the server/console side (companion guide), so both CSEntry and CSWeb get walked. The coordinator sets + shares passwords privately.

> **Each tester completes at least one WHOLE F4 interview with a roster.** Between you, cover **different household sizes** (small and large), one **Refused** case, and at least one **partial-save mid-roster** (5B.3). Device variety (a big tablet AND a small/old phone) is how we catch combined-view + roster layout problems before the field does.

---

## 3. Your Test Questionnaire-Number Assignments

The interview opens with a **12-digit Questionnaire Number**: Region(2)–Province(2)–City/Mun(3)–Facility(2)–Case(3). Everyone uses the test prefix **`040340002`**; your **3-digit block** (F4 = `6xx`) keeps your cases from clashing.

| Tester | CSWeb username | QN block (F4 = `6xx`) | Example cases |
|---|---|---|---|
| **Shan** | `shan` | `040340002` + **`600`–`619`** | `040340002600`, `040340002601`, … |
| **Kidd** | `kidd` | `040340002` + **`620`–`639`** | `040340002620`, … |
| **Aly** | `alytest` | `040340002` + **`640`–`659`** | `040340002640`, … |
| **Aidan** | `aidan` | `040340002` + **`660`–`679`** | `040340002660`, … |

> Use a **different last 3 digits for each case**. Coordinator fills the names + blocks above before sending. **Don't reuse another tester's block.**

> **📍 This round is set in Laguna (Cabuyao City Hospital · `040340002`).** Capture each case's GPS **where you actually are, around Los Baños / Laguna** — the test facility is in your province, so a correctly-run case now shows as **correctly located on the CSWeb Map (no "wrong area" flag)**. Keep the team testing from the **same general area** so the Map's location checks stay clean. An outdoor / near-window fix is best; an indoor desk case may leave GPS blank — that's expected, just say so.

---

## 4. Pre-Flight Checks (each tester, before testing)

1. **Android device + internet** ready.
2. **CSEntry installed** (5A.1) and **HouseholdSurvey downloaded** from the server (5A.2).
3. **Already had an older version?** **⋮ → Update Installed Applications** (or remove + re-add) so you're on the **Round 5 build**. Tell-tale of R5: questions **grouped on one screen** and a **single 12-digit number**.
4. **Permissions:** tap **Allow** for **Location** and **Camera** when asked. (Denied? Settings → Apps → CSEntry → Permissions.)
5. **Have your own CSWeb username + password** (§2 / §3 — e.g. `shan`, *not* the shared `setest`) and your **QN block** ready.

---

## 5. The Field-Day Dry-Run

Run it as a real household visit, in order: **5A → 5B → 5C → 5D → 5E** is one continuous pass. When you file a finding (Section 6), pick the matching **scenario** in the GitHub form — the `[TC-…]` tags tell you which.

For anything wrong, jot **expected** vs **actual**. Wording issues may be survey-design items (routed to the survey team), not bugs — flag and say which.

### 5A — Install + download + cold start (act like Day 1) · `[Install / download the app]`

- **5A.1 (install CSEntry):** Play Store → **CSEntry** (*U.S. Census Bureau*, free) → open.
- **5A.2 (download F4):** CSEntry → **add application** (**+** / **⋮**) → **from a CSWeb server** → server `https://csweb.asiansocial.org/csweb/api` → log in with **your own username** (e.g. `shan`, see §3) + password → **HouseholdSurvey** → **download / add**. **Time it.**
- **5A.3 (start cold):** Tap **HouseholdSurvey** → **new interview** (**+**) → enter QN (`040340002` + your number). Expect **auto-filled Region / Province / City names** (read-only, intended); pick the **Barangay** from the list. Mistyped → *"…not found in PSGC"* → re-enter.

### 5B — Full interview under field conditions · `[TC-1 Completed]` `[TC-3 Partial save + resume]` `[Household roster]`

**What you're rehearsing:** a household completing the whole survey in a real home — not on perfect Wi-Fi.

- **5B.1 (full happy walk with a roster — the main one):** Complete the whole interview with reasonable **test** values. As you go, confirm:
  - **GPS auto-fetch:** at the household GPS step an **"Obtaining GPS Location"** box opens **on its own** (no button); near a window/outdoors is faster; coordinates fill + lock.
  - **Informed Consent Form** (PART I) shows **in full** — scroll, then answer **Yes**.
  - **Household roster** `[Household roster]` *(the important part to test):* enter the **number of household members**, then the app asks the member questions **once per member** (a repeating block). Please:
    - Add **at least 3–4 members** and confirm it asks each member's details **in turn** (member 1, member 2, …).
    - Confirm the roster **stops at the number you entered** — it doesn't keep asking forever, and doesn't stop early.
    - Note whether moving **between members** feels clear (which member am I on?).
  - **Combined screens / date picker / drop-downs / auto-advance / blue instruction text** behave (see 5C).
  - At the **end**, set **Result of Visit** to **Completed** → **last screen is the Verification Photo** → take a test photo → **Save / complete**.
- **5B.2 (offline stretch):** Partway through (mid-roster is a good moment), turn **Wi-Fi / data OFF**. Keep answering — no error banners, answers stay.
- **5B.3 (interruption + resume, mid-roster) `[TC-3]`:** **In the middle of the roster** (e.g. after member 2), press **Back** → **Partial Save** → case shows a **partial** marker → **reopen** and confirm you **continue the roster** where you left off — earlier members' answers intact.
- **5B.4 (force-quit):** Once, fully **kill** CSEntry and reopen → partial case still there, reopens cleanly.

### 5C — New-feature correctness spot-checks (the R5 build changes) · see TC tags

Check these **as you reach them** during 5B.

| # | Feature | What to do | Confirm | Form scenario |
|---|---|---|---|---|
| **5C.1** | **Combined screens** | Reach any grouped screen | Related questions readable on your device, scroll works, nothing cut off | `Combined screens / …` |
| **5C.2** | **Household roster** `[Roster]` | Enter N members, walk the block | Asks **once per member**, **stops at N**, moving between members is clear | `Household roster — repeating members (F4 only)` |
| **5C.3** | **GPS auto-fetch** | Reach the household GPS step | The **"Obtaining GPS Location"** box opens **on its own**; coordinates fill + lock | `GPS / Camera / Verification photo` |
| **5C.4** | **Photo at the end** | Finish a **Completed** case | Verification photo is the **very last step** | `GPS / Camera / Verification photo` |
| **5C.5** | **Photo gate (Refused)** `[TC-2]` | Run a **Refused/Withdraw** case (5C.8) | **No photo step at all** | `TC-2 Refused / Withdrawn` |
| **5C.6** | **Other (specify) gating** `[TC-4]` | Tick **Other** on any such question | A **"specify" box appears + is required**; **un-tick Other** → box **goes away / is skipped** | `TC-4 "Other (specify)" behaviour` |
| **5C.7** | **Exclusive-option warning** `[TC-5]` | Tick a normal option **and** an exclusive one (**"None of the above"** / **"I don't know"** / **"Not applicable"**) | A **gentle warning** appears; it's a **warning, not a block** | `TC-5 "Select all" + exclusive-option warning` |
| **5C.8** | **Refused/Withdraw path** `[TC-2]` | New case, consent **No** **or** **Result of Visit = Refused / Withdraw** | Interview **ends**, **no photo step** | `TC-2 Refused / Withdrawn` |

> If any 5C item is **missing or misbehaving**, file it (Section 6). The roster behaviour (count, mid-roster resume) is the highest-value F4 check — be precise about how many members you entered vs how many it asked.

### 5D — Sync + confirm it landed on CSWeb · `[Sync to the server]`

- **5D.1 (sync up):** HouseholdSurvey case list → **Synchronize / Sync** → log in with **your own username** if asked → wait for **"Sync complete / success."**
- **5D.2 (confirm landing):** Tell your **monitor / STL** your **QN** + household size + sync time. They confirm (companion guide) it appears in **CSWeb → Sync Report**, the **View case** opens with the right answers **and the right number of roster members**, the per-stream **counts** move, and — if a GPS got a real outdoor fix — a **pin shows on the Map**. (Indoor/desk cases may be blank — say so.)

### 5E — Adversarial coda

- **5E.1 (real respondent text):** In an "Other (specify)" / open-text field, type `< > & " ' /` + emoji (🏥) → preserved through save + sync.
- **5E.2 (long text):** Paste ~500 chars → accepted, preserved on reopen + sync.
- **5E.3 (roster edge):** Try a **1-member** household and (if the instrument allows) a **larger** one — confirm the count drives the block correctly at both ends.
- **5E.4 (day-later resume):** Partial-save mid-roster, close everything, come back next session, reopen → resumes mid-roster.
- **5E.5 (bad QN / language):** Number not starting `040340002` → *"…not found in PSGC"* with a clear re-enter path. Optionally switch **language** → translated text appears (note anything untranslated).

---

## 6. Bug-Filing Format

For **every** finding, open a GitHub issue via the feedback form (one per finding):
**https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=capi_uat_feedback.yml**

Pick **Instrument = F4**, the matching **scenario** from §5, the **result** (Pass / Pass-with-comment / Fail / Blocked), and describe it plainly. Auto-label: `from-uat-round-5-2026-06`. By-hand shape:

```
**Round 5 (dry-run) step:** 5A / 5B / 5C.x / 5D / 5E.x
**Type:** CAPI bug  OR  survey-design/wording question (your best guess)
**Tester:** ‹your name / initials›
**Device:** Android tablet (model + Android version) / phone (model) / etc.
**Questionnaire Number:** 040340002 6xx
**Household size entered:** N members
**Question / screen:** (e.g. "roster member 3" / "members count" / "household GPS" / "Result of Visit")
**Expected:** [what the step says should happen]
**Actual:** [what happened]
**Reproduction steps:**
  1. ...
**Severity:** critical / high / medium / low
**Field impact:** [would this slow / confuse / block a real enumerator? how badly?]
**Screenshot / photo:** [attach — very helpful]
```

For quick discussion or anything urgent, post in **`#f4-uat`**. Coordinator links each finding to **`#721`** and triages daily.

---

## 7. Triage Cadence

- **Daily check-in:** Coordinator posts to `#f4-uat` daily ~09:00 PHT — new F4 findings, criticals, overnight fixes.
- **Mid-round sync:** any field-blocking critical (can't download F4, sync failing, roster asking wrong count / losing members, a case lost) → same-day Slack huddle.
- **R5 close:** end of the sprint week. Coordinator reconciles **`#721`**; opens dispositioned (fix-now / next-sprint / route-to-survey-team / won't-fix-with-rationale). Round closes when the **exit criteria** (companion guide §8) are met and F4's open finding count is **0**.

---

## 8. Why this round matters

Every R5 change was built and gate-checked in isolation. What none of them has done is **survive a real household visit on a real device, synced to a real server, watched by a real monitor.** F4's roster is the highest-risk piece — a repeating block that has to ask exactly the right number of times and resume correctly when an interview is interrupted, which is exactly what real household visits do.

- **A whole F4 interview completes** with a realistic roster — not just isolated screens.
- **The roster asks the right number of times and resumes mid-roster** — on a real device, with a real interruption.
- **The combined-view layout holds on a real, possibly small/old, device.**
- **GPS + photo behave in the real world**, and the **sync → CSWeb-landing loop closes** with the right member count visible to the data team.

If F4 carries a clean field day here, it walks into the pretest confident. If it doesn't, this is the last cheap place to find out. Thanks for testing — treat it like the real day.

---

## Appendix — Quick troubleshooting

- **Can't connect / download:** check internet; type the server address exactly (`https://…/csweb/api`).
- **Login fails:** re-type the username (lowercase, no spaces) + password.
- **"…not found in PSGC":** re-enter the number as `040340002` + your 3 digits (600s).
- **Roster keeps asking / stops early:** note the number of members you entered vs how many it asked, and tell us — that's exactly the kind of thing we're testing.
- **Old-looking screens (one question per screen):** older version — **⋮ → Update Installed Applications**, or remove and re-add (5A.2).
- **GPS won't read / Camera won't open:** allow **Location** / **Camera** (Settings → Apps → CSEntry → Permissions); GPS may time out indoors — note it and move on.
- **Sync fails:** confirm internet, re-enter **your own username** + password, retry; if it still fails, screenshot the error and post in `#f4-uat`.
