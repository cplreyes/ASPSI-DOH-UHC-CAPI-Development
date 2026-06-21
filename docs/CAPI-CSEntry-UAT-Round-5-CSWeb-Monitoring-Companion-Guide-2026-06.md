# CAPI Surveys (F1 / F3 / F4) — UAT Round 5 · End-to-End Field-Day Dry-Run — CSWeb Monitoring Companion Guide

**Round:** 5 (CAPI testers' numbering) · **Type:** End-to-End Field-Day Dry-Run
**Drafted:** 2026-06-21 · **Opens:** 2026-06-22 (Mon AM) · **Closes:** 2026-06-27 (Fri PM)
**Side:** **CSWeb** monitoring console — the data team's view of fieldwork (sync, case breakout, Sync Report, Map, counts, reconciliation)
**Companion guides:** the three instrument tester guides — `docs/F1-CSEntry-Tester-Install-and-Test-Guide-Round-5-2026-06.md`, `docs/F3-…`, `docs/F4-…` (the enumerator side that *generates* the data you monitor)
**Coordinator:** Carl Patrick L. Reyes (Data Programmer / CAPI developer)
**Window:** Opens **Mon 2026-06-22** · Closes **Fri 2026-06-27** — a work-week round

> **Project context.** **CSWeb** (`csweb.asiansocial.org`, v8.0.1) is the server-side hub for the DOH UHC Survey Year 2 CAPI instruments. Enumerators sync completed F1/F3/F4 cases up to it; a 5-minute cron breaks each synced case out into the per-instrument breakout databases; the data team watches it all on the **Sync Report**, the **Map Report**, and per-stream counts. **Round 5 is an end-to-end field-day dry-run:** instead of checking CSWeb features in isolation, you operate it the way the data team will on a real field day — confirm the cohort/test setup, **watch cases land in real time** as the enumerator-side testers sync, run the incident drills (a re-sync, a duplicate Questionnaire Number, a blank-GPS desk case), and **reconcile end-of-day**. This is the stakeholder/monitor seat — the parallel to the enumerator's tablet.

> **Why this round exists.** CSWeb has been stood up, the breakout cron is live, and the Sync Report works — but the whole pipeline has **never been operated as a live monitoring console during an actual CAPI survey run**. R5 rehearses exactly that: as the F1/F3/F4 testers interview and sync, the monitor confirms each case arrives, breaks out, plots (if it has a real GPS fix), and counts correctly — and that nothing is silently lost. It is the first time the **enumerator side and the monitoring side run together, live.**

> **Scope of this guide.** Monitor-side only. The interviews that generate the data are in the three instrument tester guides. The two sides run **at the same time** — coordinate timing so you are watching real cases arrive, not just confirming an empty board. Everything here runs on the **live CSWeb** with the `040340002` test prefix segregating throwaway cases; you filter them out of any real view and purge after (teardown, §7).

---

## ⚠️ Coordinator pre-flight (Carl — do BEFORE opening, shared with the instrument guides)

1. **Deploy the R5 build ×3 to CSWeb** (F1 + F3 + F4) — the standard publish-and-deploy handoff. Confirm each app downloads cleanly on a real device once.
2. **Confirm the breakout pipeline is live:** the per-instrument breakout DBs exist and the **5-minute `csweb:process-cases` cron** is running (so synced cases break out without manual intervention). Re-apply the on-box patches if CSWeb was upgraded since the last check.
3. **Confirm the Slack channels exist** (`#f1-uat` / `#f3-uat` / `#f4-uat` + `#capi-scrum` for the monitor); add testers + STLs + the monitor; pin the relevant guide in each.
4. **Confirm the GitHub feedback form is live** (`capi_uat_feedback.yml`), the label `from-uat-round-5-2026-06` exists, and the **tracking issues `#719` (F1) · `#720` (F3) · `#721` (F4)** are open.
5. **CSWeb test users — created 2026-06-12** (§2): **Administrators `shan` + `kidd` + `marriz`** (full console **and** CSEntry sync — they test both sides) and **Field Sync `alytest` (Aly) + `aidan`** (CSEntry sync only, same role as `setest`). One account per ASPSI tester with a unique password, replacing the shared `setest` so each case + action is attributable; `setest` stays a coordinator fallback. (No separate stakeholder/read-only login — see §2.)
6. **Brief the admins:** share this guide privately + the Administrator logins (`shan` / `kidd` / `marriz`); make sure they have the console open when the round starts. A stakeholder without a login watches alongside an admin.
7. **Pre-agree timing** so the monitor is watching when the enumerators sync (the two sides run together).

> Until steps 1–6 are done, the round is a draft.

---

## 1. Quick Reference

| Item | Value |
|---|---|
| **CSWeb console** | https://csweb.asiansocial.org/csweb/ |
| **CSWeb version** | 8.0.1 |
| **Server API (used by CSEntry to sync)** | `https://csweb.asiansocial.org/csweb/api` |
| **Login (your own)** | field-sync `alytest` (Aly) / `aidan` (tablet) · **admins `shan` + `kidd` + `marriz`** (tablet **and** console) — see §2 · `setest` = coordinator fallback · passwords shared privately |
| **What you're monitoring** | F1 `FacilityHeadSurvey` · F3 `PatientSurvey` · F4 `HouseholdSurvey` |
| **Test-case prefix to filter on** | `040340002` (everything in R5 starts with this) · F1 = `…1xx`, F3 = `…5xx`, F4 = `…6xx` |
| **Breakout** | 5-min `csweb:process-cases` cron → per-instrument breakout DBs |
| **Reports** | **Sync Report** (cases in, by app) · **Map Report** (GPS pins) |
| **Bug repo** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues |
| **Feedback form** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=capi_uat_feedback.yml |
| **Bug-filing label** | `from-uat-round-5-2026-06` |
| **Slack channels** | `#f1-uat` · `#f3-uat` · `#f4-uat` (coordinate with each enumerator there) · **`#capi-scrum`** — the monitor's hub for CSWeb-specific findings + cross-instrument coordination |
| **Tracking issues** | F1 `#719` · F3 `#720` · F4 `#721` |

---

## 2. CSWeb test users + monitor roster

**Each tester and monitor logs in with their OWN CSWeb user — not the shared `setest`.** That way every synced case is attributable to the enumerator who entered it, and every monitor action is traceable. `setest` is kept only as a coordinator fallback. The coordinator creates these on CSWeb → **Users** before the round and shares each password privately.

### CSWeb test users (created 2026-06-12)

CSWeb has **two roles in use: Administrator** (full console **+** CSEntry sync) and **Field Sync** (CSEntry sync only). The accounts below are live on the server (`Users` tab):

| Username | Tester (ASPSI) | CSWeb role | Tests / can do |
|---|---|---|---|
| `shan` | **Shan** (RA) | **Administrator** | **CSEntry + CSWeb** — tablet sync **and** full console (manage apps/users · Sync Report · Map · View case) |
| `kidd` | **Kidd** (main RA) | **Administrator** | **CSEntry + CSWeb** — tablet sync **and** full console (manage apps/users · Sync Report · Map · View case) |
| `marriz` | **Marriz** (Data Manager) | **Administrator** | **CSEntry + CSWeb** — tablet sync **and** full console (live monitoring · Sync Report · Map · View case · reconcile) |
| `alytest` | **Aly** (RA) | **Field Sync** | **CSEntry** — download + sync F1 / F3 / F4 (same as `setest`) |
| `aidan` | **Aidan** (RA) | **Field Sync** | **CSEntry** — download + sync F1 / F3 / F4 (same as `setest`) |
| `setest` | — (legacy shared) | **Field Sync** | Fallback — coordinator only |

> Plus the CSWeb-built-in **`admin`** and Carl's **`cplreyes`** — both system/coordinator **Administrators** (not testers). Note Aly's username is **`alytest`** — CSWeb usernames need a **4-character minimum**, so `aly` (3 chars) wouldn't validate. No separate read-only/stakeholder login exists — a stakeholder (e.g. Dr. Myra) watches alongside an admin, or gets a read-only account if CSWeb's Roles are extended.

> **One login per tester, reused across instruments.** The four ASPSI RAs each test more than one instrument; each uses their **own** single login (`shan` / `kidd` / `alytest` / `aidan`) for whichever instrument they're syncing — the username is the person, not the instrument. Map the QN block per instrument (each guide's §3), not the user.
>
> **The two roles:**
> - **Administrators — `shan` + `kidd` + `marriz`:** full CSWeb console (manage apps/users, all reports + case views) **and** CSEntry field sync. These three test **both** sides — the tablet *and* the server — so the end-to-end pipeline is exercised by the same people who run it (mirrors how F2 testers walked both the survey side and the Admin Portal). Shan + Kidd lead from the enumerator seat and also exercise the admin console; Marriz leads live monitoring + does at least one full tablet walk to confirm sync works from an Administrator account.
> - **Field Sync — `alytest` (Aly) + `aidan`:** CSEntry only — download the apps + sync cases (same role as `setest`). No console access.
>
> Passwords are unique per user and shared privately. `setest` stays a coordinator fallback.

### CSWeb console roster (admins)

| Who | CSWeb user | Role | On the console |
|---|---|---|---|
| **Marriz** (ASPSI Data Manager) | `marriz` | Administrator | **Live-monitoring lead** — Sync Report / Map / counts as cases arrive; end-of-day reconciliation. Also does a full tablet walk (CSEntry). |
| **Kidd** (ASPSI main RA) | `kidd` | Administrator | Tests the **admin console** — apps/users management + reports — alongside his tablet enumeration; cross-checks his own synced cases. |
| **Shan** (ASPSI RA) | `shan` | Administrator | Tests the **admin console** alongside his tablet enumeration; cross-checks his own synced cases. |
| Carl (coordinator) | `cplreyes` / `setest` | Coordinator | Triage GitHub findings → fix → re-deploy → re-verify; runs teardown. |

> The console surfaces — **Sync Report**, **Map Report**, **View case**, and per-stream **counts** — are the heart of this dry-run. A stakeholder (e.g. Dr. Myra) sits with an admin to watch, or gets a read-only login if one is added later. Flag anything that would slow real-time monitoring of a live field day: refresh lag, an unclear count, a case that breaks out wrong, a dashboard you'd want but don't have.

---

## 3. Pre-Flight Checks (monitor, before the round)

1. Open `https://csweb.asiansocial.org/csweb/` → log in with your own **Administrator** console user (`marriz` / `kidd` / `shan`). A stakeholder without a login watches alongside an admin.
2. **Confirm the three apps are present** on the server (F1 `FacilityHeadSurvey`, F3 `PatientSurvey`, F4 `HouseholdSurvey`) and show the **current R5 build** (latest deploys: F4 Section C 06-20, break-off/disposition 06-21).
3. **Confirm the breakout DBs exist** for each instrument and the **5-min cron** is processing (a previously-synced case should already be broken out; if the breakout lag is much longer than ~5 min, note it).
4. **Open the Sync Report and Map Report** once so you know where they are before cases start arriving.
5. **Set a filter mindset:** every R5 case starts `040340002` (F1 `1xx` / F3 `5xx` / F4 `6xx`). Anything else is not part of this dry-run.

---

## 4. Reference: where things are on CSWeb

```
CSWeb console (csweb.asiansocial.org/csweb/)
  Applications      → FacilityHeadSurvey · PatientSurvey · HouseholdSurvey (R5 deploys)
  Sync / Cases      → synced cases per app (the raw upload)
  Breakout DBs      → per-instrument flattened cases (fed by the 5-min cron)
  Sync Report       → cases-in over time, by app / by facility
  Map Report        → GPS pins for cases with a real fix
  Users             → setest (fallback) + R5 users: alytest / aidan (Field Sync) · shan + kidd + marriz (Administrator) · admin/cplreyes (system)
```

> Exact tab labels can vary by CSWeb build — if a label here doesn't match what you see, note it (a doc fix), find the equivalent, and carry on.

---

## 5. The Dry-Run (monitor side)

Run it as a field day in four acts — **5A setup → 5B live monitoring → 5C incident drills → 5D end-of-day reconciliation**. The live-monitoring act (5B) happens **at the same time** as the enumerator-side testers' 5B–5D — coordinate so you're watching real cases arrive.

For anything wrong, decide if it's a **CSWeb / pipeline issue** (sync, breakout, report) or a **case-content issue** (the enumerator entered/branched something wrong) and file accordingly (Section 6), tagging the right instrument.

### 5A — Pre-fieldwork setup (the morning of the dry-run)

**What you're rehearsing:** confirming the board is ready before enumerators go out.

- **5A.1 (apps + version):** Confirm all three R5 apps are deployed and downloadable (ask an enumerator-side tester to add one from the server — that's their 5A.2; you confirm it served).
- **5A.2 (clean baseline):** Note the **current case count per instrument** before the round so you can tell new R5 cases from anything pre-existing. Everything new should carry the `040340002` prefix.
- **5A.3 (breakout heartbeat):** Confirm the 5-min cron is alive (a freshly-synced case breaks out within ~5–10 min). If it's stalled, that's a pre-round blocker — flag to coordinator before opening.

### 5B — Live monitoring as cases arrive (the monitor leads; stakeholders watch)

**What you're rehearsing:** the data team watching a field day unfold in real time. **Run this while the enumerator-side testers complete + sync (their 5B–5D).**

- **5B.1 (cases land):** As each enumerator syncs, confirm the case appears on the **Sync Report** (allow for the sync + the ≤5-min breakout). Note the lag from their "Sync complete" to it showing on your board.
- **5B.2 (View case is correct):** Open the **View case** for an arrived case and spot-check the answers against what the enumerator tester says they entered — especially the **new-feature** items (other-specify text present only when Other was ticked; the exclusive-option choices; F3 the **right patient-type branch**; F4 the **right number of roster members**).
- **5B.3 (counts move correctly):** Confirm per-stream **counts** update — and for **F3**, that **Outpatient vs Inpatient** tally correctly as the two patient-type cases arrive.
- **5B.4 (Map Report — location + field-QA):** Open the **Map Report** (`/docs/map.html`). Cases **with a real outdoor GPS fix** plot a pin, **coloured by status** (green Completed / gold Partial); **desk/indoor cases have blank GPS and no pin — expected** (they're counted in the "no GPS fix" badge, not lost). **This round's headline check:** because R5 testers use the **Laguna** test facility (`040340002`) and capture GPS in Laguna, their cases should plot as **correctly located with NO "wrong area" flag** — set **Data quality → Wrong area** and confirm it stays **empty** for the test cases. If a case *does* flag **wrong area** (GPS outside its declared province) or **displacement** (home far from facility / a facility point off its cluster), that's the field-QA signal working — note it and check with the tester. Toggle the **F3 patient-home** layer + **Connect F3 pairs** to see F3's two-point capture.
- **5B.5 (Sync Dashboard):** Open the **Sync Dashboard** (`/docs/dashboard.html`). Confirm the day's cases roll up by **instrument · region · status (Completed/Partial) · visit date** as they sync, with the filters recomputing. Both the dashboard and the map **auto-refresh ~every 15 min** (or hard-refresh to pull the latest).
- **5B.6 (monitor's verdict):** Narrate (in a finding / note) anything that would slow real-time monitoring on a real field day — refresh lag, an unclear or wrong count, a case that broke out with missing fields, a view you wish you had. **This is the most valuable output of the dry-run from the monitoring seat.**

### 5C — Incident drills (the things that WILL happen in the field)

**What you're rehearsing:** the failure cases a real field day produces.

- **5C.1 (re-sync / idempotency):** Have an enumerator **sync the same case twice** (or edit-and-re-sync). Confirm CSWeb handles it sanely — the case **updates, not duplicates** — and the Sync Report doesn't double-count it. (If it duplicates, that's a high-value finding.)
- **5C.2 (duplicate Questionnaire Number):** Have two testers (by mistake-on-purpose) sync the **same QN**. Confirm what CSWeb does — reject, overwrite, or keep both — and **document it**, because real enumerators will occasionally collide. (This is why testers get distinct QN blocks; the drill is to know the failure mode.)
- **5C.3 (blank-GPS desk case):** Confirm a **Completed** case with **no GPS fix** (a desk test) still **syncs and breaks out** cleanly — it just has no map pin. The data shouldn't be rejected for a missing optional GPS.
- **5C.4 (partial / interrupted case):** Confirm a case that was **partial-saved then completed and synced** lands as a single complete case (no orphan partial on the server). For F4, confirm the **roster members all arrive** for a case that was interrupted mid-roster then resumed.

### 5D — End-of-day reconciliation (close the field day)

**What you're rehearsing:** proving the day's data is complete and trustworthy.

- **5D.1 (count reconciliation):** Compare **cases on CSWeb** against **what the enumerator-side testers report syncing** (they'll tell you their QNs + sync times). **Every synced case should be accounted for** — nothing silently lost. Do it per instrument (F1 `1xx`, F3 `5xx`, F4 `6xx`).
- **5D.2 (breakout completeness):** Confirm every arrived case **broke out** into its per-instrument DB (the flattened form the analysis team consumes) — none stuck un-processed.
- **5D.3 (content cross-check):** For one case per instrument, open **View case** and confirm the answers match the tester's notes end-to-end — including the R5 features (photo present on Completed / absent on Refused; F3 branch; F4 member count).
- **5D.4 (the trust question):** As a stakeholder would, answer out loud: *"Did we get everything, and does it look right?"* If yes, the pipeline carried a clean field day. If not, the gap is the finding that matters most.

---

## 6. Bug-Filing Format

For **every** finding, open a GitHub issue via the feedback form:
**https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=capi_uat_feedback.yml**

Pick the **Instrument** the case belongs to (F1/F3/F4), and for the **scenario** use `Sync to the server` or `General observation` (monitor-side findings), then describe it. Auto-label: `from-uat-round-5-2026-06`. By-hand shape:

```
**Round 5 (dry-run) — monitor step:** 5A / 5B.x / 5C.x / 5D.x
**Type:** CSWeb / pipeline issue  OR  case-content issue  OR  monitoring-friction note
**Instrument:** F1 / F3 / F4
**Monitor:** ‹your name / initials›
**Where on CSWeb:** Sync Report / Map Report / View case / breakout DB / counts
**Case (QN):** 040340002 _ _ _
**Expected:** [what should show / happen]
**Actual:** [what showed / happened]
**Reproduction steps / timing:** [include the sync time + when it appeared, if it's a lag/loss issue]
**Severity:** critical / high / medium / low
**Field impact:** [would this slow / block the data team on a real field day?]
**Screenshot:** [attach — very helpful]
```

Tag the instrument's tracking issue (**`#719` / `#720` / `#721`**). Coordinator triages daily.

---

## 7. Triage Cadence + Teardown

- **Daily check-in:** Coordinator posts to each instrument channel ~09:00 PHT — new findings (enumerator + monitor side), criticals, overnight fixes.
- **Mid-round sync:** any pipeline-blocking critical (sync failing, breakout stalled, cases duplicating or lost, a wrong patient-type branch reaching the server) → same-day Slack huddle; don't wait for close.
- **R5 close:** end of the sprint week. Coordinator reconciles **`#719` / `#720` / `#721`**; opens dispositioned (fix-now / next-sprint / route-to-survey-team / won't-fix-with-rationale).
- **Teardown:** after close, coordinator removes the `040340002` test cases from CSWeb (and the breakout DBs) so the dry-run data doesn't pollute real fieldwork. Until then, **filter `040340002` out** of any real view.

---

## 8. Exit criteria (the round closes when)

- **Every enumerator** completed at least **TC-1 (Completed) + TC-2 (Refused)** on their instrument and **synced successfully**.
- **Each instrument's Completed case is visible + correct on CSWeb** — on the Sync Report, with correct counts, **broken out** into its DB, and with a **map pin for at least one real-outdoor case**.
- **F3 patient-type routing** (Outpatient AND Inpatient both walked + correctly branched) and **F4 roster** (right member count, mid-roster resume) confirmed on a real device and visible in the synced case.
- **Reconciliation is clean** — every synced case accounted for, nothing silently lost; the duplicate-QN and blank-GPS failure modes are **documented**.
- **All filed findings are dispositioned** — fixed-and-verified, or deferred with a reason / routed to the survey team — and each instrument's open finding count is driven to **0**.

---

## 9. Why this round matters

CSWeb has been stood up dashboard by dashboard, the breakout cron runs, and the Sync Report shows cases. What it hasn't done is **run a field day.** A real pretest doesn't test one feature at a time — enumerators sync a wave of cases, one collides on a QN, one has no GPS because it was a desk test, one was interrupted mid-roster, and the day ends with a stakeholder asking *"did we get everything, and can we trust it?"* R5 rehearses that whole arc with the enumerator side generating the data live.

- **Setup → monitor → incident → reconcile** is the real workflow; this is the first time the data team walks it together with the field side.
- **Live monitoring from the data seat** tells us whether the Sync Report + Map + counts actually support real-time fieldwork, not just whether they render.
- **The incident drills** (re-sync, duplicate QN, blank GPS, interrupted roster) build the muscle the team needs *before* the cases are real.
- **End-of-day reconciliation** is the moment the data team trusts — or doesn't trust — that nothing was lost between the tablet and the server.

If CSWeb carries a clean field day here, it carries the pretest. Thanks for monitoring — operate it like the real day.
