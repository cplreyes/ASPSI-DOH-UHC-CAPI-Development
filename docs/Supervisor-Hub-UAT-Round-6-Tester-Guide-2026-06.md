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
| Team | Tester | Username | Role | Instrument / EA |
|---|---|---|---|---|
| A | **Aidan** | **fs-01** | Supervisor | Assign · Collect · Relay · reports · map |
| A | Pat | se-001 | Enumerator | **F1** — Binan City Health Office |
| A | Shan | se-002 | Enumerator | **F3** — Binan RHU (target 30) |
| A | Aly | se-003 | Enumerator | **F4** — Binan Brgy Malaban (target 20) |
| A | Ms. Marriz | se-004 | Enumerator | **F1** — Binan District Hospital |
| B | **Ms. Marriz** | **fs-02** | Supervisor | Assign · Collect · Relay · reports · map |
| B | Aidan | se-005 | Enumerator | **F3** — Los Banos RHU (target 30) |
| B | Ma'am Merlyne | se-006 | Enumerator | **F4** — Los Banos Brgy Mayondon (target 20) |

> 👥 **Aidan** and **Ms. Marriz** each hold two accounts (testing both roles), on **opposite teams** so neither supervises themselves: Aidan = `fs-01` (Team A sup) + `se-005` (Team B enum); Marriz = `fs-02` (Team B sup) + `se-004` (Team A enum). Bluetooth pairs (can't pair with yourself): Team A = Aidan `fs-01` ↔ Pat / Shan / Aly / Marriz `se-004`; Team B = Marriz `fs-02` ↔ Aidan `se-005` / Merlyne `se-006`.

*(Hub login + CSWeb passwords for each row are in `supervisor-hub/config/UAT-R6-tester-credentials.md` — distributed privately, not in this guide.)*

## §3 Demo data
Use the EA assignments above; test cases use the **`0403…` Laguna** prefixes. Test data is identifiable and purgeable after the round.

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

> ⚠️ **Slack DROPS markdown `|` tables** — the first attempt rendered with empty tables (headers only, no rows). Post credentials as a **monospace code block** (below), never a markdown table. Recommended: make the channel **private** + **rotate all CSWeb passwords after the round** (the CSWeb password is the real security boundary).

🔑 **Round 6 hub credentials** — server `https://csweb.asiansocial.org/csweb/api`
Each account has **two passwords**: a **CSWeb** password (used once to install via Add Application → from CSWeb; supervisors reuse it to relay) and a **hub login** password (typed every time to open the role menu). Don't share accounts; test data, rotated after the round.

~~~
TEAM A — supervisor fs-01 (Aidan)
fs-01   Aidan    Supervisor          hub: uhc26fs01    CSWeb: zxfVR715xEcmNo
se-001  Pat      F1 Binan City HO    hub: uhc26se001   CSWeb: RMVUyf7pVACkJU
se-002  Shan     F3 Binan RHU        hub: uhc26se002   CSWeb: TvvRMFTznRHTSX
se-003  Aly      F4 Binan Malaban    hub: uhc26se003   CSWeb: hgsccdiXFBiDeA
se-004  Marriz   F1 Binan Dist Hosp  hub: uhc26se004   CSWeb: Fquy3HZrLIR96z

TEAM B — supervisor fs-02 (Ms. Marriz)
fs-02   Marriz   Supervisor          hub: uhc26fs02    CSWeb: rqn4fvGKvCZAwU
se-005  Aidan    F3 Los Banos RHU    hub: uhc26se005   CSWeb: EqMH4UwBzbY6IR
se-006  Merlyne  F4 Los Banos Mayon  hub: uhc26se006   CSWeb: SKMRbFSHhS8noU
~~~

👥 **Aidan** and **Ms. Marriz** each hold two accounts on **opposite teams** so neither supervises themselves. **Bluetooth pairs:** Team A = Aidan `fs-01` ↔ Pat/Shan/Aly/Marriz `se-004`; Team B = Marriz `fs-02` ↔ Aidan `se-005`/Merlyne `se-006`.
