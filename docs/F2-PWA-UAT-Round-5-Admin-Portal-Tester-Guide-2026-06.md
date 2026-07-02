# F2 PWA — UAT Round 5 (Admin Portal side) — Tester Guide

**Round:** 5 (testers' numbering) · **Type:** Regression re-test (production v2.1.0)
**Drafted:** 2026-06-21 · **Opens:** 2026-06-22 (Mon AM) · **Closes:** 2026-06-27 (Fri PM)
**Side:** F2 Admin Portal (operations console — enrollment, monitoring, DLQ, reconciliation, RBAC)
**Companion guide:** `docs/F2-PWA-UAT-Round-5-HCW-Survey-Tester-Guide-2026-06.md` (HCW Survey side — all four testers walk both)
**Coordinator:** Carl Patrick L. Reyes (Data Programmer)
**Window:** Opens Mon 2026-06-22 AM · Closes Fri 2026-06-27 PM

> **⚠️ Round 5 caveats (read first).** (1) **Worker-deploy gap:** CI's version-stamped Worker deploy is currently failing — a brand-new *backend* route may not be on staging; if an admin action 404s/500s, flag it but note it may be the deploy gap, not a regression. (2) The HCW survey side runs **English-only this round** (`VITE_ENGLISH_ONLY` on; switcher hidden) — expect English submissions, not a bug.

> **Project context.** The F2 Admin Portal is the operations console ASPSI ops staff run fieldwork from. It mirrors the **CSWeb** dashboard model — 5 dashboards × 5 roles × per-instrument flags. Ops users enroll HCWs (mint tablet tokens), monitor submissions as they arrive, triage dead-letter-queue failures, manage files, schedule exports, audit actions, and onboard other ops users. **Round 5 is a regression re-test of production `v2.1.0`:** you operate the portal the way the data team will on a real field day — set up the cohort, watch submissions land in real time as the HCW-side testers complete surveys, run the incident drills (lost tablet, parked submission, emergency stop), and reconcile end-of-day. Marriz (Data Manager) drives the live-monitoring lane; Shan + Kidd run setup, incidents, and RBAC.

> **Why this round exists.** R3's admin fixes shipped in **v2.1.0** (2026-06-01) — concurrency, cross-tab session, audit completeness, RBAC, Users dashboard, Map/Sync polish. They've been fixed and verified in isolation, but the portal has never been **operated end-to-end as a live monitoring console during an actual survey run**. R5 rehearses exactly that, against the same seeded staging dataset the HCW guide uses, before the real pretest.

> **Scope of this guide.** Admin-portal-side only. The HCW enrollment + survey completion that *generates* the data you monitor is in the companion guide. The two run **together, live**: as HCW-side testers submit, Admin-side testers watch it arrive.

---

## ⚠️ Coordinator pre-flight (Carl — do BEFORE opening)

Same staging setup as the HCW guide — do it once, both guides share it:

1. Confirm **staging carries v2.1.0+** (redeploy `staging` to match `main` if behind).
2. In **`F2-PWA-Backend-Staging`** Apps Script: run `purgeDemoData()` then `seedDemoData()`. Log should show `facilities: {added:3}`, `hcws: {added:12}`, `responses: {added:9}`, `dlq: {added:1}`, `files: {added:2}`, `audit: {added:2}`. This gives the portal a story on every tab (per `docs/superpowers/runbooks/2026-05-04-seed-demo-data.md`).
3. Mint fresh enrollment URLs (Reissue) for the HCW-guide assignments; paste them there.
4. Create/confirm admin test accounts on **staging** (Section 2). Marriz's `marriz_admin` may need fresh creation on staging with Administrator role + first-login rotation.
5. Create the tracking issue `[E6-PWA-NNN] UAT Round 5 (R5)` + label **`from-uat-round-5-2026-06`**; drop the # into Section 1.
6. Announce in `#f2-pwa-uat`.

> **Staging, not prod, by design** — the dry-run dumps throwaway submissions + lets us seed a populated environment. Cleanup is `purgeDemoData()` after. If you choose prod instead, seed-demo refuses; you'd Create-HCW for tokens and accept prod pollution. Flip URLs throughout if so.

---

## 1. Quick Reference

| Item | Value |
|---|---|
| **Staging Admin Portal** | https://staging.f2-pwa.pages.dev/admin/login |
| **Help (no-auth)** | https://staging.f2-pwa.pages.dev/admin/help |
| **Worker (curl smoke)** | https://f2-pwa-worker-staging.hcw.workers.dev |
| **Target version under test** | v2.1.0 — staging must be deployed to match `main` |
| **Spec — full Admin Portal design** | `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md` |
| **Concept overview** | `wiki/concepts/F2 Admin Portal.md` |
| **Seed/cleanup runbook** | `docs/superpowers/runbooks/2026-05-04-seed-demo-data.md` |
| **Bug repo** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues |
| **Bug-filing label** | `from-uat-round-5-2026-06` |
| **Slack channel** | `#f2-pwa-uat` on `aspsi-doh-uhc-survey2.slack.com` |
| **R5 tracking issue** | `#723` — `[E6-PWA-723]` |

---

## 2. Tester Roster + Credentials (staging)

**Each tester uses their own admin credential — no shared logins.** Audit attribution depends on it.

| Tester | Username | Password | Lane in the dry-run |
|---|---|---|---|
| **Shan** (ASPSI RA) | `shan_admin` | _staging reset; ping coordinator if unknown_ | Setup (cohort enrollment, files) + RBAC + incident drills |
| **Kidd** (ASPSI main RA) | `kidd_admin` | _staging reset_ | Setup + incident drills (DLQ, reissue, kill-switch) + concurrency partner |
| **Marriz** (ASPSI Data Manager) | `marriz_admin` | _coordinator DMs initial; first login forces rotation_ | **Live monitoring lead** — Responses / Sync Report / Map / Audit as data arrives; end-of-day reconciliation |
| **Aly** (ASPSI RA, new) | `aly_admin` | _initial pw posted in `#f2-pwa-uat`; first login forces rotation_ | Setup + incident drills + RBAC; full-breadth Administrator |

### RBAC test credential (shared — only for the RBAC drill in 5E)

| Username | Password | Role | Why |
|---|---|---|---|
| `data_reader_uat` | _shared in `#f2-pwa-uat`_ | DataReader | Confirm read-only boundary holds client + server side |

> Marriz: your Data-Manager surfaces — **Data → Responses + Audit + HCWs** and **Reports → Sync Report + Map Report** — are the heart of this dry-run. Flag anything that would slow your real-time monitoring of a live field day.

---

## 3. Pre-Flight Checks (each tester)

1. Open `https://staging.f2-pwa.pages.dev/admin/login` in Chrome → Verde paper background + login form.
2. Login with your own credential → land on Data dashboard.
3. **Confirm version** (Apps & Settings → Versioning): PWA **2.1.0**, Worker matching. Sidebar footer reads `v2.1.0` (not `v0.1.0-staging`, not an older tag). Hard-refresh if stale.
4. **Confirm the seed loaded:** Data → HCWs → **12 `DEMO-HCW-*`** rows; Data → Responses (expand date filter from 2026-05-01) → **~9** submissions; Data → DLQ → **1** entry (`DEMO-SUB-012`, `E_SPEC_DRIFT`); Reports → Map → markers at QC / Infanta / Balanga.
5. `/admin/help` in incognito → only Help link + "Sign in" CTA in the sidebar (no full operator nav while signed out).
6. DevTools open (F12), Network + Console visible — capture for any bug.

---

## 4. Reference: Admin Portal layout

```
OPERATE
  Data            → Responses · Audit · DLQ · HCWs
  Reports         → Sync Report · Map Report
  Encode          → paper-encoded entry queue
CONFIGURE
  Apps & Settings → Versioning · Files · Data Settings · Apps Script Quota
  Users           → Admin user CRUD
  Roles           → Role grid (5 dashboards × per-instrument flags)
HELP
  Help            → Operator guide (no-auth)
(bottom) <username> · role badge · Sign out
```

---

## 5. The Dry-Run

Run it as a field day in four acts — **5A setup → 5B live monitoring → 5C/5D incidents + reconciliation → 5E RBAC realism**. The live-monitoring act (5B) happens **at the same time** as the HCW-side testers' 5B–5D — coordinate timing so you're watching real submissions arrive, not seeded ones only.

For anything wrong, check `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md` to classify it as a **portal bug** vs a **spec gap**. File either way; say which.

### 5A — Pre-fieldwork setup (act like the morning of the pretest)

**What you're rehearsing:** standing up a facility's cohort before enumerators go out.

- **5A.1 (Create HCW):** Data → HCWs → **Create HCW**. Mint a brand-new HCW (name + facility + role) — the first-class modal, not a sheet edit. Expect: success, fresh enrollment URL generated, audit row written. This is how a real ops user adds an HCW the sample list missed.
- **5A.2 (Reissue for the dry-run cohort):** Reissue tokens for the HCW-guide assignments (if coordinator didn't already). Confirm each reissue logs to Audit with your username + the HCW as resource, and the old token is invalidated.
- **5A.3 (Files):** Apps & Settings → Files. Upload a field-plan PDF (<1 MB) → success, appears in list, downloads byte-identical. This mirrors distributing the facility plan / roster to the team.
- **5A.4 (roster sanity):** Data → HCWs → confirm the cohort you'll monitor (the seed's 12 + any you created) is present with correct facility + role + `enrolled` status.

### 5B — Live monitoring as data arrives (Marriz leads; all watch)

**What you're rehearsing:** the data team watching a field day unfold in real time. **Run this while the HCW-side testers complete + submit (their 5B–5D).**

- **5B.1 (Responses populate):** Keep Data → Responses open, filtered to today. As each HCW-side submission lands, confirm it appears within ~30s of their submit. Click into one → ResponseDetail shows the full submission JSON; spot-check that the answers match what the HCW tester says they entered (especially their content spot-checks — Q47/Q52/Q125 etc.).
- **5B.2 (Sync Report coverage climbs):** Reports → Sync Report. As submissions arrive, confirm coverage-by-facility updates. QC-RHU should show **two** submissions once Shan + Marriz both submit (the multi-respondent-per-facility step, HCW guide 5D.3).
- **5B.3 (Map markers appear):** Reports → Map Report. New submissions with GPS plot as pins; clicking one opens the Verde popup with hcw_id / facility_id / "View full case →". Confirm the selected marker highlights (enlarged + ring — v2.0.2 fix). Note the honest "By facility prefix" grouping label on demo data.
- **5B.4 (Audit live):** Data → Audit. Confirm your own setup actions (Create HCW, Reissue, file upload) appear within seconds, with actor / resource / detail columns populated. Filter by your username → only your actions.
- **5B.5 (Marriz's monitoring verdict):** As Data Manager, narrate (in the bug/notes) anything that would slow real-time monitoring — refresh lag, unclear counts, a dashboard you'd want but don't have. This is the most valuable output of the dry-run from the ops seat.

### 5C — Incident drills (the things that WILL happen in the field)

**What you're rehearsing:** the failure cases a real field day produces.

- **5C.1 (DLQ triage):** Data → DLQ → open the seeded `DEMO-SUB-012` (`E_SPEC_DRIFT`). Read the original payload + failure reason. Confirm UTF-8 chars render. Decide what you'd do with it operationally and note it — this is the muscle the team needs when a real submission gets parked.
- **5C.2 (lost/replaced tablet → reissue):** Simulate "an enumerator's tablet died." Reissue the token for an actively-enrolled HCW. Confirm the OLD enrollment URL now fails on the HCW side (ask a HCW-side tester to try their pre-reissue URL → expect rejection) and the NEW one works. Audit logs the reissue.
- **5C.3 (kill-switch drill):** Apps & Settings → Data Settings → toggle `kill_switch` **ON** (confirmation modal → save). With a HCW-side tester's PWA open, confirm the kill-switch banner appears within ~30s and their submit attempts queue locally. Toggle **OFF** → banner clears within ~30s. Audit captures both toggles. This is the most consequential admin control — rehearse it deliberately.
- **5C.4 (spec-drift surface):** Confirm the portal shows current `spec_version` + `min_accepted_spec_version` (Data Settings) and that you understand which submissions would be rejected if the HCW PWA fell behind — the mechanism behind the seeded DLQ entry.

### 5D — End-of-day reconciliation (close the field day)

**What you're rehearsing:** proving the day's data is complete and exportable.

- **5D.1 (count reconciliation):** Compare **submissions in Responses** against **what the HCW-side testers report submitting** (they'll tell you HCW IDs + times). Every submitted survey should be accounted for as either a Response or a DLQ entry — nothing silently lost.
- **5D.2 (CSV break-out export):** Apps & Settings → Data Settings → trigger / inspect a scheduled CSV break-out export. Confirm it produces a file with the day's responses. (This is the artifact the analysis team receives.)
- **5D.3 (audit completeness):** Data → Audit → confirm the day's meaningful actions are all captured — every Create HCW, Reissue, file upload, kill-switch toggle, login — each with actor + resource + timestamp + detail. Confirm an Administrator **cannot delete** audit rows (compliance immutability).
- **5D.4 (HCWs vs Responses cross-check):** Data → HCWs → confirm enrolled-but-not-submitted HCWs (e.g. `DEMO-HCW-004`/`009` from seed, plus any dry-run incompletes) show correctly as enrolled-no-response — the list a real team chases on day 2.

### 5E — RBAC + multi-admin realism (the team isn't one person)

**What you're rehearsing:** several ops users on the console at once, and a curious low-privilege user.

- **5E.1 (concurrent reissue — CAS):** Two testers open the Reissue modal for the **same** HCW and both Confirm near-simultaneously. Expect: one succeeds, the other gets a clean `409 E_CAS_FAILED` toast — no silent overwrite, no crash.
- **5E.2 (cross-tab session):** Open the portal in two tabs (both logged in as you). Sign out in Tab A. In Tab B, try to mutate → expect 401 + redirect to login, not a stale-session crash.
- **5E.3 (DataReader boundary):** Sign out, log in as `data_reader_uat`. Confirm Users + Roles dashboards are hidden; Data sub-tabs are read-only (mutation buttons hidden/disabled). In DevTools → Network, craft a POST to `/admin/api/hcws/<id>/reissue-token` → expect **server-side 403** (client-hidden buttons aren't the only defense). Navigate directly to `/admin/users` → 403/redirect, not a partial render.
- **5E.4 (live role revocation):** Have the coordinator demote you mid-session; on your next mutation attempt, confirm the revoked permission takes effect (RBAC cache invalidation, ≤60 min TTL — should be near-immediate on role_version bump).

---

## 6. Bug-Filing Format

```
**Round 5 (dry-run) step:** 5A.x / 5B.x / 5C.x / 5D.x / 5E.x
**Type:** portal bug  OR  spec gap  OR  ops-friction note (your best guess)
**Tester:** shan_admin / kidd_admin / marriz_admin / aly_admin / data_reader_uat
**Browser/Device:** desktop Chrome / tablet (model + browser) / etc.
**Dashboard / Sub-tab:** Data → HCWs / Reports → Sync / Apps & Settings → Data Settings / etc.
**Expected:** [what the spec / step says]
**Actual:** [what happened]
**Reproduction steps:**
  1. ...
**Severity:** critical / high / medium / low
**Field impact:** [would this slow/block the data team on a real field day?]
**Screenshot / video:** [attach]
**Console errors / network failures:** [paste]
**Audit log row (if relevant):** [paste from Data → Audit]
```

Apply `from-uat-round-5-2026-06` + link to the tracking issue on every R5 finding.

---

## 7. Triage Cadence

- **Daily check-in:** Coordinator posts to `#f2-pwa-uat` daily 09:00 PHT — new R5 findings (HCW + Admin), criticals, overnight fixes.
- **Mid-round sync:** any pretest-blocking critical (enrollment/mint broken, submissions lost, kill-switch failing, RBAC leak) → same-day Slack huddle, don't wait for close.
- **R5 close:** Friday 2026-06-27 PM. Coordinator reconciles the tracking issue; opens dispositioned (fix-now / next-sprint / route / won't-fix-with-rationale).
- **Teardown:** after close, coordinator runs `purgeDemoData()` to return staging to its pre-dry-run state.

---

## 8. Why this round matters

The Admin Portal has been built, fixed, and verified dashboard by dashboard. What it hasn't done is **run a field day**. A real pretest doesn't test one feature at a time — it generates submissions, parks a few in the DLQ, loses a tablet, needs an emergency stop, and ends with someone asking "did we get everything, and can I export it?" R5 rehearses that whole arc on the same data the HCW-side testers generate live.

- **Setup → monitor → incident → reconcile** is the real workflow; this is the first time the team walks it together.
- **Live monitoring from the Data-Manager seat** (Marriz) tells us whether the dashboards actually support real-time fieldwork, not just whether they render.
- **The incident drills** (DLQ, reissue, kill-switch) build the muscle the team needs *before* the stakes are real submissions from real HCWs.
- **End-of-day reconciliation** is the moment the data team trusts — or doesn't trust — that nothing was lost.

If the portal carries a clean field day here, it'll carry the pretest. Thanks for testing — operate it like the real day.
