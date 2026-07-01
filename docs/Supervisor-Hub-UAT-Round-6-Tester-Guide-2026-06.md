# Supervisor & Enumerator Hub — UAT Round 6 Tester Guide

**Round:** 6 · **App:** Supervisor & Enumerator hub (`LoginApp` → `MenuApp`)
**Window:** Opens **2026-06-30** · Closes **2026-07-05** *(target — starts once your CSWeb account is active)*
**Server:** `https://csweb.asiansocial.org/csweb/api` · **Tracking issue:** #807
**Full how-to (with screenshots):** https://csweb.asiansocial.org/docs/hub-guide.html

> 📋 This round tests the **hub** — the one app that logs you in, shows your role's menu, moves
> assignments and finished interviews between tablets over **Bluetooth**, relays to CSWeb, and shows
> live coverage + an offline map. The F1/F3/F4 questionnaires themselves were signed off in Round 5;
> here we're testing the *wrapper around them*.

> 🤝 **Bluetooth is a two-tablet flow.** Test as a **supervisor + enumerator pair**. A solo tester can
> still do login, Conduct F1/F3/F4, reports, and the map — but Assign/Collect/Send/Receive need a pair.

> ⏱️ **Mid-round fixes ship fast.** Findings are fixed in the generator, redeployed, and you refresh via
> **Add Application → CSWeb → Update** (no reinstall, no round restart).

## Coordinator pre-flight (ASPSI / Carl)
- [x] CSWeb roles exist: **`Supervisor QA`** (Reports + F1/F3/F4 Upload+Download) ✅ created 2026-06-29; **`Field Sync`** (no dashboard; F1/F3/F4 Upload+Download) — verify it still carries the three dicts.
- [ ] CSWeb accounts imported from `supervisor-hub/config/uat-r6-csweb-users.csv` (real names filled in).
- [ ] Slack channel created (**recommend private**) — agent then posts kickoff + the full credentials table (Carl's R6 call: no DMs; drafts at the bottom of this guide). Pin the credentials post.
- [ ] Plan a CSWeb password rotation after the round (the credentials are posted in-channel).

## §1 Quick reference — the two credentials
| Used for | Which credential | When |
|---|---|---|
| **Install / update the hub** | your **CSWeb** account (username + CSWeb password) | once, via Add Application → CSWeb |
| **Open the role menu** | your **hub login** (username + hub password, e.g. `uhc26se001`) | every time you start the app |
| **Relay to CSWeb** (supervisors) | your **CSWeb** account again | when you tap "Relay Collected Interviews to CSWeb" (prompts once, then caches) |

## §2 Tester roster — 2 teams
*Real pre-test EAs (Los Baños, municipality `040341`) — updated 2026-07-01 from the RA "Unique Question Number for Pre-testing" list. Each facility enumerator does the **F1 Facility Head + the 10 F3 patients** at their facility; the two barangays are F4 (both operated by Aly).*

| Team | Tester | Username | Role | Instrument / EA |
|---|---|---|---|---|
| A | **Aidan** | **fs-01** | Supervisor | Assign · Collect · Relay · reports · map |
| A | Pat | se-001 | Enumerator | **F1 head + F3** — Los Banos Doctors Hospital (F1×1, F3×10) |
| A | Shan | se-002 | Enumerator | **F1 head + F3** — Laguna Provincial Hospital, Bay (F1×1, F3×10) |
| A | Marriz | se-004 | Enumerator | **F1 head + F3** — Los Banos RHU I (F1×1, F3×10) |
| A | Aly | se-003 | Enumerator | **F4** — Brgy. Bayog (target 20) |
| B | **Ms. Marriz** | **fs-02** | Supervisor | Assign · Collect · Relay · reports · map |
| B | Aidan | se-005 | Enumerator | **F1 head + F3** — St. Jude Hospital (F1×1, F3×10) |
| B | Aly | se-006 | Enumerator | **F4** — Brgy. Mayondon (target 20) |

> 👥 **Dual accounts** (testing both roles / covering two areas), on **opposite teams** so no one supervises themselves: Aidan = `fs-01` (Team A sup) + `se-005` (Team B enum); Marriz = `fs-02` (Team B sup) + `se-004` (Team A enum); **Aly operates both `se-003` (Bayog) and `se-006` (Mayondon)**. Bluetooth pairs (can't pair with yourself): Team A = Aidan `fs-01` ↔ Pat / Shan / Marriz `se-004` / Aly `se-003`; Team B = Marriz `fs-02` ↔ Aidan `se-005` / Aly `se-006`.

> 📄 **Exact QNs:** each enumerator's 12-digit case keys are on their **printed assignment sheet** (`supervisor-hub/assignments/out/assignment-sheets.html`); the full list is `assignments/pretest-qn-list.csv`. Type the keys exactly — the tablet rejects a wrong PSGC prefix.

*(Hub login + CSWeb passwords for each account are in the **Credentials** section below.)*

## §3 Demo data
Use the EA assignments above; all pre-test QNs are **`040341…` (Los Baños, Laguna)** — 4 facility-head (F1) + 40 patient (F3) + 40 household (F4) = **84 cases**. Test data is identifiable and purgeable after the round.

## §4 Pre-flight (each tester)
1. CSEntry installed; tablet date/time **automatic**; **Location ON**; **Bluetooth ON** (for the pair flows).
2. Install/Update the hub: **Add Application → from CSWeb →** sign in with your **CSWeb** account → install/Update **LoginApp**.
3. Open **LoginApp** → tap ➕ → enter your **username** + **hub login password** → your role menu appears.

## §5 The field-day arc
- **5A — Sign in & menu:** confirm the menu header shows your name + role and the right grouped items.
- **5B — Conduct:** open your assigned instrument (F1/F3/F4) from the menu, complete a case, exit → back at the menu.
- **5C — Assignment (pair):** supervisor **Assign Enumeration Area** (Bluetooth host) → enumerator **Receive Assigned Data** → confirm your EA/target shows.
- **5D — Collect & relay (pair):** enumerator **Send My Interviews to Supervisor** → supervisor **Collect Interviews from Enumerators** → supervisor **Relay Collected Interviews to CSWeb** → confirm success.
- **5E — Reports & map:** **View my report / Survey report** (live counts) · **View EA on Map** (turn Wi-Fi off — it should still render).

## §6 Filing a bug
New issue → **"CAPI UAT feedback"** form → add labels **`epic:hub`** + **`from-uat-round-6-2026-06`** → note **"Supervisor Hub"** + the exact menu item/step. Attach a screen recording if you can. Everything rolls up under **#807**.

## §7 Triage cadence
Findings are triaged, fixed in `build_hub_apps.py`, redeployed to CSWeb, and posted back as a short patch note. You update via **Add Application → CSWeb → Update on LoginApp**.

## §8 Why it matters
The hub is how a field team works **with no signal** — assignments and finished interviews move tablet-to-tablet over Bluetooth, then one supervisor relays the whole team's work to the server when a connection is available. R6 proves that choreography end-to-end before the pretest.

---

## Channel posts (ready to paste — agent posts after Carl's go + channel exists)

**KICKOFF**
> 📣 **UAT Round 6 is open — Supervisor & Enumerator Hub** (2026-06-30 → 07-05)
> We're testing the hub: login → role menu → Bluetooth assign/collect/send/receive → relay to CSWeb → live reports → offline map. (The F1/F3/F4 questionnaires were signed off in R5.)
> • **Guide:** https://csweb.asiansocial.org/docs/hub-guide.html
> • **Install:** CSEntry → Add Application → from CSWeb → install/Update **LoginApp**
> • **Teams:** A = fs-01 + se-001/002/003/004 · B = fs-02 + se-005/006
> • 🤝 Bluetooth needs a **supervisor + enumerator pair** on two tablets
> • **File bugs:** New issue → "CAPI UAT feedback" → labels `epic:hub` + `from-uat-round-6-2026-06` → rolls up to #807
> Your accounts + both passwords are in the **📌 pinned credentials post** in this channel. Happy testing! 🎯

**CREDENTIALS (channel — full list, per Carl's R6 call: no DMs)** — POSTED to #supervisor-uat (`C0BENS7D4E4`) 2026-06-29.

> ⚠️ **Slack DROPS markdown `|` tables** — post credentials as a **monospace code block** (below), never a markdown table. **Rotate all CSWeb passwords after the round** (the CSWeb password is the real security boundary).

🔑 **Round 6 hub credentials** — server `https://csweb.asiansocial.org/csweb/api`
Each account has **two passwords**: a **CSWeb** password (used once to install via Add Application → from CSWeb; supervisors reuse it to relay) and a **hub login** password (typed every time to open the role menu). Don't share accounts; test data, rotated after the round. *(EA labels below match the Los Baños pre-test roster in §2.)*

~~~
TEAM A — supervisor fs-01 (Aidan)
fs-01   Aidan    Supervisor                hub: uhc26fs01    CSWeb: zxfVR715xEcmNo
se-001  Pat      F1 head + F3 LB Doctors   hub: uhc26se001   CSWeb: RMVUyf7pVACkJU
se-002  Shan     F1 head + F3 Laguna Bay   hub: uhc26se002   CSWeb: TvvRMFTznRHTSX
se-003  Aly      F4 Brgy Bayog             hub: uhc26se003   CSWeb: hgsccdiXFBiDeA
se-004  Marriz   F1 head + F3 LB RHU I     hub: uhc26se004   CSWeb: Fquy3HZrLIR96z

TEAM B — supervisor fs-02 (Ms. Marriz)
fs-02   Marriz   Supervisor                hub: uhc26fs02    CSWeb: rqn4fvGKvCZAwU
se-005  Aidan    F1 head + F3 St. Jude     hub: uhc26se005   CSWeb: EqMH4UwBzbY6IR
se-006  Aly      F4 Brgy Mayondon          hub: uhc26se006   CSWeb: SKMRbFSHhS8noU
~~~

👥 **Aidan** and **Ms. Marriz** each hold two accounts on **opposite teams** so neither supervises themselves; **Aly** operates both `se-003` (Bayog) and `se-006` (Mayondon). **Bluetooth pairs:** Team A = Aidan `fs-01` ↔ Pat/Shan/Marriz `se-004`/Aly `se-003`; Team B = Marriz `fs-02` ↔ Aidan `se-005`/Aly `se-006`.
