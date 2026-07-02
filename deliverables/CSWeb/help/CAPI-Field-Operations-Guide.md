---
title: "CAPI Field-Operations Guide — Login, Menu & Survey Apps"
category: deliverable
kind: field-help
audience: Enumerators · Field/Cluster Supervisors · Field Ops / Data Manager
server: csweb.asiansocial.org (CSWeb 8.0.1, LIVE)
prepared_by: Carl Patrick L. Reyes
last_updated: 2026-06-25
tags: [csweb, csentry, field-ops, login, menu, supervisor-app, roles, help]
---

# CAPI Field-Operations Guide — Login, Menu & Survey Apps

> **Server:** `https://csweb.asiansocial.org` · **Sync API:** `https://csweb.asiansocial.org/csweb/api`
> **For:** field enumerators, field/cluster supervisors, and field-ops/data managers.
> **Covers:** the Login + Menu hub now published to CSWeb, the F1/F3/F4 survey instruments, the
> Supervisor (Facility Visit Log) app, the roles each person needs, and how the apps work together
> on the tablet and against the server.

This is a **plain-language field guide.** It is not the build/deploy documentation — it tells the
people in the field how to install, sign in, navigate, capture, and sync.

---

## 1. What is now published on CSWeb

All of these appear in CSEntry under **⋮ → Add Application → From a server** once you point CSEntry at
the project server. They install as separate apps that sit **side by side** on the tablet.

| App (in the Add-Application list) | What it is | Who uses it |
|---|---|---|
| **LoginApp** | The **hub entry point** — sign in once, then it opens the role menu. Installing LoginApp also installs **MenuApp** and the **user roster** (they ride inside the same package). | Everyone |
| **FacilityHeadSurvey** | **F1** — Facility Head survey instrument | Enumerators (+ supervisors for spot-checks) |
| **PatientSurvey** | **F3** — Patient survey instrument | Enumerators (+ supervisors) |
| **HouseholdSurvey** | **F4** — Household survey instrument | Enumerators (+ supervisors) |
| **SupervisorApp** | **Facility Visit Log** — logs every facility touchpoint with automatic GPS + timestamp | Field supervisors |

> **The hub is a convenience layer, not a wall.** LoginApp/MenuApp give you one signed-in starting
> point and a tidy menu. The survey instruments are still their own installed apps and can be opened
> directly if needed — the menu simply launches them for you and brings you back when you finish.

---

## 2. How the apps fit together

There are **three layers**, and they keep their data separate:

```
        ┌─────────────┐      sign in       ┌────────────┐    pick an action     ┌──────────────────────┐
  YOU → │  LoginApp   │ ─────────────────▶ │  MenuApp   │ ────────────────────▶ │  F1 / F3 / F4         │
        │ (identity)  │  role handed over  │ (launcher) │  launches + returns   │  survey instruments   │
        └─────────────┘                    └────────────┘                       └──────────┬───────────┘
              │  checks                          ▲   │                                      │ captures cases
              ▼  username/password               │   └──────── you finish, it returns ──────┘ into its OWN data
        ┌─────────────┐                          │
        │ User Roster │  (ships inside LoginApp)  │  Supervisors also use ─────▶ ┌──────────────────────┐
        │  enumerator │                          └──────────────────────────────│  SupervisorApp       │
        │ / supervisor│                                                          │ (Facility Visit Log) │
        └─────────────┘                                                          └──────────┬───────────┘
                                                                                            │
   All captured cases (F1/F3/F4 + the visit log) sync to  ◀────────────────────────────────┘
   csweb.asiansocial.org via CSEntry → Synchronize.
```

**Control flow (what happens when you use it):**

1. You open **LoginApp** and enter your **username + password.**
2. LoginApp checks them against the **User Roster** (the credential list bundled inside it). It also
   reads your **role** (enumerator or supervisor).
3. On success it hands your role to **MenuApp** and opens it automatically.
4. **MenuApp** shows a menu **filtered by your role** (see §3). You pick a survey.
5. MenuApp launches the **real installed instrument** (F1, F3 or F4). You capture cases as normal.
6. When you **finish/exit the instrument, you land back on the menu** — ready for the next task.

**Data flow (where the answers go):**

- Each instrument keeps its **own case data** on the tablet. The hub only *launches* the instruments —
  it never touches or moves their data, so there is **no risk of split or duplicated cases.**
- **LoginApp and MenuApp do not sync** anything — they are sign-in/launcher utilities.
- **Cases reach the server** through **CSEntry → Synchronize** (per instrument), authenticated by your
  **CSWeb account** (see §7). The **SupervisorApp** visit log syncs the same way.

---

## 3. Two kinds of "role" — keep them straight

This is the part people mix up. Every field person actually has **two** role settings, on two
different layers, and **both must match their job:**

| | **A. CSWeb account role** | **B. Hub app role** |
|---|---|---|
| **Where it lives** | On the server, in the CSWeb **Users / Roles** dashboards | On the tablet, in the **User Roster** inside LoginApp |
| **What it controls** | Whether you can log into the CSWeb website, and **which data you can sync** | What the **MenuApp** shows you after you sign in |
| **Is it security?** | **Yes** — this is the real access control (checked at sync time) | **No** — it is only a menu filter / convenience. Anyone with the tablet creds gets the menu; the *data* is still gated by the CSWeb account |
| **Values** | `field-sync`, `supervisor-monitor`, `supervisor-qa`, `data-manager`, `account-admin`, `Administrator` (see §4) | `enumerator` or `supervisor` |

**How they pair up.** They use the **same username** so identities line up for audit
(e.g. `se-014`, `fs-03`):

- An **enumerator** has a `field-sync` **CSWeb account** *and* an `enumerator` **roster row** → the
  menu shows only **F1 / F3 / F4.**
- A **field supervisor** has a `supervisor-monitor` (or `supervisor-qa`) **CSWeb account** *and* a
  `supervisor` **roster row** → the menu shows **all six** items.

> **Plain version:** the *CSWeb account* decides what data the server lets you touch; the *roster role*
> decides what buttons you see on the tablet. Give a person the matching pair for their job.

---

## 4. Roles needed (who gets what)

### CSWeb account roles (server-side — the real access control)

Six custom roles, least-privilege (from the CSWeb User-Management & RBAC pack):

| Job | CSWeb role | Web dashboards | Can sync F1/F3/F4? | Logs into website? |
|---|---|---|---|---|
| **Enumerator (SE)** | `field-sync` | *(none)* | ✅ send | **No** — CSEntry only |
| **Field / Cluster Supervisor** | `supervisor-monitor` | `report` | ❌ no down-sync | Yes |
| **Designated Field-QA Supervisor** | `supervisor-qa` | `report` | ✅ send + pull | Yes |
| **Data Manager** | `data-manager` | `data` · `report` · `apps` | ✅ | Yes |
| **Account Admin** | `account-admin` | `users` · `roles` | ❌ | Yes |
| **Server Administrator** | built-in `Administrator` | all | all | Yes (break-glass only) |

Key points:
- **Enumerators never see the website** — they only sync from CSEntry. That is how bulk PII is kept off
  the web UI (CSWeb has no "my cases only" filter, so the protection is *withholding the `data`
  dashboard*).
- **Most supervisors get `report` only** (coverage counts + map, no full-PII rows, no case down-sync).
- Only the **designated `supervisor-qa`** holders can pull (down-sync) full case data for the on-site QA
  review — kept to a named few, not all supervisors.

### Hub app roles (on the tablet — the menu filter)

| Roster role | Menu shows | Notes |
|---|---|---|
| `enumerator` | **1.** F1 · **2.** F3 · **3.** F4 | The three survey instruments only |
| `supervisor` | 1–3 above **+ 4.** Collect from enumerators · **5.** Relay to CSWeb · **6.** Run QA report | Items 4–6 are supervisor tools (see §6) |

---

## 5. Using it in the field — Enumerator

### One-time setup (per tablet)

1. Install **CSEntry** (from the device's app store / provided APK).
2. In CSEntry, tap **⋮ → Add Application → From a server**, point it at the project server, and sign in
   with **your own CSWeb username + password** (`se-NNN`).
3. Install **LoginApp** *and* the survey instruments you are assigned (**FacilityHeadSurvey**,
   **PatientSurvey**, **HouseholdSurvey**).
4. Set the **sync server**: CSEntry → **Sync → CSWeb → Add server** → URL
   `https://csweb.asiansocial.org/csweb`. (Always the **production domain** — never `localhost`.)
5. Do **one mock case** end-to-end (capture → Sync → confirm it shows in CSWeb → delete the mock) before
   going live.

### Every fieldwork day

1. Open **LoginApp** → type your **username** and **password** → advance.
   - *Wrong password* or *unknown username* → it tells you and lets you retry.
2. The **menu** opens showing your role at the top (e.g. *"Logged-in role: enumerator"*) and the
   **F1 / F3 / F4** choices.
3. Pick the survey for your assignment → capture cases exactly as in training.
4. When you **finish or exit a case, you return to the menu** — pick the next survey if needed.
5. **By 22:00 each day:** CSEntry → open each instrument → **Synchronize** → wait for
   **"Successfully synced."** Read the message — do not assume.

---

## 6. Using it in the field — Field Supervisor

### Setup

Same as §5, but also install **SupervisorApp** (the Facility Visit Log), and sign in with your
**`fs-NN`** account.

### The supervisor menu (all six items)

After signing in, MenuApp shows the full menu:

| # | Item | What it does today |
|---|---|---|
| 1–3 | **F1 / F3 / F4** | Open a survey instrument — used for **read-only spot-checks** of your team's interviews |
| 4 | **Collect from enumerators** | **Guidance prompt:** *"CSEntry → Sync → Bluetooth from each enumerator."* |
| 5 | **Relay to CSWeb** | **Guidance prompt:** *"CSEntry → Sync → CSWeb (supervisor-qa account)."* |
| 6 | **Run QA report** | **Guidance prompt:** *"Export collected data, run the supervisor QA report."* |

> **Items 4–6 are on-screen reminders, not automated actions yet.** They point you to the manual steps.
> The fully-automated Bluetooth "collect → relay → QA" hub is a planned Phase-2 capability and is **not
> built into this version.** For now, supervision runs through the CSWeb website (coverage on the
> `report` dashboard) and the desktop QA report.

### Facility Visit Log (SupervisorApp) — at each facility

1. Open **SupervisorApp** → add (or reopen) the case for this facility → enter the **9-digit facility
   code** (`RRPPMMMFF` — the facility part of the survey case key) + facility name + your operator ID.
2. **Log each touchpoint as it happens** on the Touchpoint screen — add a row and pick the type:
   *Arrival, Courtesy call, Endorsement delivery, Workstation, Focal person, HCW-list, Departure,*
   or *Other (+ note)*. The **time and GPS stamp themselves automatically** and lock read-only.
3. On the **first visit**, fill the **Courtesy-Call** screen (endorsement obtained, focal person,
   discharge cutoff, scheduled interview/listing dates, workstation, QR poster, HCW master-list count —
   tick "captured" and optionally photograph the printed list).
4. It **saves as you go** (partial save on) — stop and resume the same case across visit days.
5. **Sync nightly** (and at the facility if you have signal): Synchronize → *"Successfully synced."*
   Your visit log reconciles against the planned visit schedule on the server.

---

## 7. Sync — endpoint, direction, schedule

| Item | Value |
|---|---|
| **Server** | `https://csweb.asiansocial.org` (CSWeb 8.0.1) |
| **CSEntry sync URL** | `https://csweb.asiansocial.org/csweb` (CSEntry adds `/api` itself) |
| **Transport** | HTTPS only |
| **Auth** | Your **CSWeb username + password**, entered at sync time |
| **Mechanism** | **CSEntry built-in Synchronize**, manual (you tap it), one dictionary per instrument |

- **Direction:** enumerators **send** (push only). `supervisor-qa` accounts can **send + pull** (pull a
  team's cases for review). `supervisor-monitor` accounts **do not** sync case data — they watch the
  `report` dashboard.
- **Smart-sync:** only new/changed cases move — bandwidth-frugal over cellular.
- **Schedule:** at least one **successful sync by 22:00** each fieldwork day. Supervisors check the
  **Sync Report** afterward and chase gaps.
- **No conflicts by design:** each enumerator owns distinct facilities, so two tablets never mint the
  same case key (`RR-PP-MMM-FF-CCC`). A re-synced edit is last-write-wins on that one case.

> **"My synced cases aren't showing in the report yet."** The **Data tab** is real-time; the **Sync
> Report / dashboards refresh on a short cron and lag a few minutes.** Trust the Data tab for the live
> count — the report catches up. This is a display delay, **not** lost data.

---

## 8. Installing & updating the apps

- **Install / update = remove + re-add.** CSEntry's **⋮ → Update Installed Applications** is unreliable
  for CSWeb redeploys (it can say "no update" while a newer build is live). To be sure you have the
  **current** version: **remove the app, then Add Application → From a server again,** and test on a
  **fresh case.**
- Because LoginApp bundles MenuApp + the roster, re-adding **LoginApp** refreshes the whole hub at once.
- The survey instruments (F1/F3/F4) and SupervisorApp are **separate installs** — update each the same
  way when a new build is announced.

---

## 9. Login reference (the User Roster)

The roster bundled inside LoginApp holds one row per person:

| Field | Meaning |
|---|---|
| **Username** | The field ID — also the CSWeb account name (`se-NNN`, `fs-NN`) |
| **Password** | Sign-in password for the hub |
| **Role** | `enumerator` or `supervisor` (drives the menu — see §3) |
| **Operator ID** | Stamped through to the work for provenance |
| **Cluster** | The person's cluster code |

> ⚠️ **This published version ships placeholder credentials** (the `changeme…` seed roster used for
> testing). **Before real field rollout,** the roster must be replaced with the confirmed personnel
> list (real usernames + strong passwords + correct roles), and the matching **CSWeb accounts** must be
> provisioned (RBAC pack §3–4). Until then, treat the hub as a working demonstration, not a live
> credential store.

---

## 10. Troubleshooting

| Symptom | Most likely cause → what to do |
|---|---|
| *"Incorrect password."* | Typo, or your roster row differs → retype; if it persists, ops re-checks your roster entry. |
| *"Unknown username."* | You are not in the bundled roster, or the hub build is stale → **remove + re-add LoginApp**; if still missing, ops adds you to the roster and redeploys. |
| *"No role found from login…"* on the menu | The role didn't hand over (rare) → close and sign in again via **LoginApp** (don't open MenuApp directly). |
| Picking a survey does nothing / drops to the app list | That **instrument isn't installed** on this tablet → Add Application → install **FacilityHeadSurvey / PatientSurvey / HouseholdSurvey**, then retry from the menu. |
| Synced cases "not showing" in a report | **Reporting-layer lag** — check the **Data tab** (real-time); the report catches up in minutes. Not data loss. |
| A retest still shows an old bug | **Stale build** — you tested an old copy → **remove + re-add** the app and retest on a fresh case. |
| Sync fails in the field but "worked in the office" | A **`localhost`** sync URL was left on the tablet → set it to `https://csweb.asiansocial.org/csweb`. |

---

## 11. Status & what is not yet automated

- **The Login + Menu hub is published and working** (sign in → role menu → launch F1/F3/F4 → return to
  menu), and the **role-filtered menu** and **return-to-menu** behaviours are device-confirmed.
- **SupervisorApp (Facility Visit Log) is live** with auto GPS + timestamp.
- **Not yet automated (planned Phase-2):** the supervisor **Collect / Relay / Run-QA** actions are
  guidance prompts only — the Bluetooth "one supervisor collects many enumerators, then relays to CSWeb"
  hub is not built. Supervision today uses the CSWeb `report` dashboard + the desktop QA report.
- **Pending before live rollout (ASPSI input):** the **real personnel roster** (replacing the
  placeholder credentials) and the matching **CSWeb account provisioning** + per-role dictionary-sync.

---

*Prepared by Carl Patrick L. Reyes · ASPSI | DOH UHC CAPI · last updated 2026-06-25. Source of truth for
the apps: the generators under `deliverables/CSPro/` (LoginApp/MenuApp = `supervisor-hub/build_hub_apps.py`,
SupervisorApp = `SV/`). Roles: `deliverables/CSWeb/CSWeb-User-Management-and-RBAC-Provisioning-Pack.md`.
Sync: `deliverables/CSWeb/Field-Tablet-Sync-Configuration.md`.*
