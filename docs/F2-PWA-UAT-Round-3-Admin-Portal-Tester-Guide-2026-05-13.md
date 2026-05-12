# F2 PWA — UAT Round 3 (Admin Portal side) — Tester Guide

**Round:** 3 (testers' numbering)
**Drafted:** 2026-05-11 · **Opens:** 2026-05-13 (Wed AM)
**Side:** F2 Admin Portal (operations console — login, dashboards, Reissue, DLQ, RBAC)
**Companion guide:** `docs/F2-PWA-UAT-Round-3-HCW-Survey-Tester-Guide-2026-05-13.md` (HCW Survey side — Shan + Kidd both walk)
**Coordinator:** Carl Patrick L. Reyes (Data Programmer)
**Window:** Opens Wed 2026-05-13 AM · Closes Fri 2026-05-15 PM (sprint close)

> **Project context.** The F2 Admin Portal is the operations console ASPSI ops users run from. It mirrors the **CSWeb** dashboard model — same shape, 5 dashboards × 5 roles × per-instrument flags. An ops user enrolls HCWs (mints tablet tokens), monitors submissions, triages dead-letter-queue entries, manages files (training plans, rosters), schedules CSV break-out exports, audits actions, and onboards other ops users. Round 3's job is twofold: **(a) regression-check** that the 33 admin-side R2 fixes (closed 2026-05-09) plus the v2.0.1 patch bundle (PR #136 — 9 E4-APRT-04x patches) still hold on current prod (v2.0.2 — covers v2.0.0 base + v2.0.1 patches + 2026-05-12 polish slate), and **(b) stress-test** what Round 2 didn't cover — concurrent multi-admin actions, RBAC edge cases, cross-tab session, kill-switch/spec-drift admin response, audit log completeness, FX-017 deferred touch-targets, large-data scenarios.

> **Why this round exists.** Round 2 closed cleanly with 33 admin-side issues fixed; v2.0.1 patches (Create-HCW UI, RBAC cache fix, JWT pwc enforce, design 5-fix sweep, concurrency, last_login_at, orphan-admin guards, user-self password rotation) shipped AFTER R2 closed and never had explicit tester walks. R3 is the first cycle to (a) confirm R2 + v2.0.1 fixes haven't regressed and (b) explore admin-specific scenario classes R2's nominal-flow walk didn't touch.

> **Scope of this guide.** Admin-portal-side only — every dashboard, every sub-tab, every workflow an ops user touches. HCW-side (PWA enrollment + survey completion) is in the companion guide above.

---

## 1. Quick Reference

| Item | Value |
|---|---|
| **Production Admin Portal** | https://f2-pwa.pages.dev/admin/login |
| **Help (no-auth)** | https://f2-pwa.pages.dev/admin/help |
| **Worker (curl smoke)** | https://f2-pwa-worker.hcw.workers.dev |
| **Current prod version** | v2.0.2 (header `v2.0.2 · spec 2026-04-17-m1`) — covers v2.0.0 base + v2.0.1 patch bundle (PR #136) + 2026-05-12 polish slate (PRs #274/#276/#279/#281/#283/#285/#288/#291) |
| **Spec — full Admin Portal design** | `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md` |
| **Concept overview** | `wiki/concepts/F2 Admin Portal.md` |
| **Bug repo** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues |
| **Bug-filing label** | `from-uat-round-3-2026-05` |
| **Slack channel (blockers + daily check-in)** | `#f2-pwa-uat` on `aspsi-doh-uhc-survey2.slack.com` |
| **Release notes** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v2.0.2 (latest) · [v2.0.1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v2.0.1) · [v2.0.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v2.0.0) |
| **R3 sprint card** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271 |

---

## 2. Tester Roster + Credentials

**Each tester uses their own admin credential — no shared logins.** Audit columns must show who clicked what; sharing a single login collapses attribution.

### Primary roster

| Tester | Username | Password | Notes |
|---|---|---|---|
| **Shan** (ASPSI RA) | `shan_admin` | _your reset password from R2_ | Administrator |
| **Kidd** (ASPSI main RA) | `kidd_admin` | _your reset password from R2_ | Administrator |
| **Marriz** (ASPSI Data Manager) | `marriz_admin` | _coordinator hands off your initial password out-of-band (Slack DM); first login forces a rotation_ | Administrator (for R3 test breadth); her day-to-day surfaces are **Data → Responses + Audit + HCWs** and **Reports → Sync Report + Map Report** — pay extra attention to those flows |

> Shan + Kidd: if you forgot your R2 password, ping coordinator in `#f2-pwa-uat` for a reset (admin user reset is now in v2.0.1 — `E4-APRT-051`).
> Marriz: your `marriz_admin` account is created at R3 open with Administrator role for full test coverage; coordinator (Carl) sends initial credentials via Slack DM. Change-on-first-login is enforced by the `password_must_change` flag; pick a new password ≥ 8 chars after first login. As a Data Manager, your perspective on the Sync Report / Map Report / Audit / Responses dashboards is especially valuable — flag anything that would slow down your real day-to-day monitoring of submitted entries.

### RBAC test credential (shared — only for Section 5A.11 + 5B.2 RBAC scenarios)

| Username | Password | Role | Why |
|---|---|---|---|
| `data_reader_uat` | _shared in `#f2-pwa-uat`_ | DataReader | Login as DataReader; confirm Users / Roles dashboards are hidden, mutations blocked. |

---

## 3. Pre-Flight Checks (do these before testing)

1. **Open `https://f2-pwa.pages.dev/admin/login`** in Chrome. Page loads with the Verde paper background and login form.
2. **Login with your dedicated credential** (your R2-reset password). Land on Data dashboard.
3. **Confirm version.** Apps & Settings → Versioning should read **PWA: 2.0.2** + **Worker: 2.0.0+** (Worker version pinned via wrangler.toml; package.json bump to 2.0.2 is PWA-side only).
4. **Sidebar shows your username + role badge** ("Administrator") at the bottom-left. Version footer below should read **`v2.0.2`** (NOT `v0.1.0-staging` — that was a hardcoded literal regression fixed 2026-05-12 in PR #279; not `v2.0.0` or `v2.0.1` either — bumped in PR #291). If you still see an older value, hard-refresh the page to pull the new bundle.
5. **Open `https://f2-pwa.pages.dev/admin/help` in incognito** (no auth). Help page renders, the URL bar stays at `/admin/help`, **and the sidebar shows ONLY the Help link + a "Sign in" CTA** (the full operator nav is hidden for unauthenticated users — fixed in PR #281). If you see the full nav with all 7 dashboard links + a "Sign out" button while not signed in, hard-refresh.
6. **Confirm seed data exists** — Data → HCWs sub-tab → 12 `DEMO-HCW-*` rows visible.
7. **DevTools open** (F12) — Network + Console tabs visible. Capture screenshots of these for any bug.

---

## 4. Reference: Admin Portal layout

Sidebar nav (left side, anchored):

```
OPERATE
  Data            (table icon)  → Responses · Audit · DLQ · HCWs sub-tabs
  Reports         (chart icon)  → Sync Report · Map Report sub-tabs
  Encode          (edit icon)   → paper-encoded entry queue

CONFIGURE
  Apps & Settings (sliders)     → Versioning · Files · Data Settings · Apps Script Quota
  Users           (users icon)  → Admin user CRUD
  Roles           (shield)      → Role grid (5 dashboards × per-instrument flags)

HELP
  Help            (book)        → Operator guide (no-auth)

(bottom)
  <username>      role badge
  Sign out
```

---

## 5. Test Scenarios

Two parts: **5A — R2 + v2.0.1 fix regression** confirms the 33 admin R2 closures + 9 v2.0.1 patches still hold; **5B — New scenarios** stress-tests scenario classes Round 2 didn't cover.

For every bug you find, open the spec at the cited section to confirm whether it's a **portal bug** (deployed code diverges from spec) or a **spec bug** (spec is wrong) — the fix path is different.

### 5A. R2 + v2.0.1 Fix Regression

Re-walk the bug paths from Round 2's 33 admin-side closures + v2.0.1 patches. For each scenario, confirm the fix still holds on current prod. File regression bugs as `Regression of #N` so triage can quickly distinguish from new R3 finds.

| # | R2 Issue(s) / Patch | Dashboard / Area | Quick regression check |
|---|---|---|---|
| **5A.1** | [#69](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/69), [#70](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/70), [#71](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/71), [#72](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/72) | Login + session | Login with bad password → throttle visible. Login with good → forced redirect to Data. Sign out → returns to /admin/login (NOT a blank page). Try to access `/admin/data` while logged out → redirected back to login. |
| **5A.2** | [#78](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/78) | Data — Responses sub-tab | Open Responses. Filter by date / facility / role. Click a row → ResponseDetail panel opens with full submission JSON. Pagination + sort columns work. |
| **5A.3** | [#79](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/79), [#80](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/80), [#82](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/82) | Data — Audit sub-tab | Open Audit. Confirm columns show Actor / Resource / Detail (FX-006 fix). Filter by actor (try your own username) — only your actions appear. Filter by event type. Verify a recent action you performed (e.g., login) appears in the log within seconds. |
| **5A.4** | [#83](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/83), [#84](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/84) | Data — DLQ sub-tab | Open DLQ. If empty, that's expected on fresh demo data. If entries exist (1 from seed): open detail, see the original payload + failure reason. UTF-8 chars in DLQ entries render correctly (#93 fix carried). |
| **5A.5** | [#85](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/85), [#86](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/86), [#87](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/87), [#88](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/88) | Data — HCWs sub-tab + Reissue Token | Open HCWs. 12 demo HCW rows visible. Click "Reissue token" on `DEMO-HCW-001` → modal opens. Confirm reissue → success toast. Verify in Audit log: action logged with your username + DEMO-HCW-001 as resource. The OLD token for that HCW is now invalidated (its prev_jti rotated). |
| **5A.6** | [#89](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/89), [#90](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/90) | Reports — Map Report sub-tab | Open Reports → Map Report. Carto Positron tiles load with PH bounds. Verde-styled pins on 12 demo HCW locations across 3 facilities. Click a pin → Verde popup with hcw_id / facility_id / "View full case →" link. Click link → ResponseDetail page loads. |
| **5A.7** | [#91](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/91), [#92](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/92), [#93](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/93) | Apps & Settings — Files sub-tab | Open Files. Existing demo files visible (2 from seed). Upload a small (<1 MB) PDF — success toast, file appears in list. Download it → bytes match. Delete it → confirmation modal, then row removed. R2 storage operations should be silent (no console errors). |
| **5A.8** | [#94](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/94), [#95](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/95), [#96](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/96) | Apps & Settings — Data Settings sub-tab | Open Data Settings. View current spec_version + min_accepted_spec_version. Toggle kill_switch ON → confirmation modal → save. Verify HCW PWA (companion guide) shows kill-switch banner. Toggle kill_switch OFF → banner disappears within ~30 seconds (config refresh interval). |
| **5A.9** | [#97](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/97) | Apps & Settings — Apps Script Quota sub-tab | Open Apps Script Quota. Quota meter renders with current usage % and reset time. If usage <80%, color is normal. (Threshold-warning color uses `--warning` token per #62 fix.) |
| **5A.10** | [#98](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/98), [#99](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/99), [#100](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/100) | Users dashboard | Open Users. See yourself + the other tester + `data_reader_uat` + `carl_admin`. Try to delete yourself → blocked (orphan-admin guard, `E4-APRT-050` v2.0.1 patch). Edit another user's role → success, audit logged. Bulk-import 2 fake users via CSV → success or graceful error. |
| **5A.11** | [#102](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/102), [#103](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/103), [#104](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/104) | RBAC + persona switching | **Sign out + login as `data_reader_uat`.** Confirm: Users + Roles dashboards HIDDEN in sidebar. Try to navigate `/admin/users` directly → 403 / redirect. Try to mutate (e.g., reissue a token) → blocked client-side AND server-side (test in Network tab). Sign out + login back as your admin. |
| **5A.12** | [#105](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/105), [#68](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/68) | Sub-tab pattern + sidebar layout | Click each top-nav item (Data / Reports / Encode / Apps & Settings / Users / Roles). Sub-tab nav appears with `?tab=...` URL deep-link. Click each sub-tab — active state shows underline + bold ink (Verde signal-color border-b-2). Sidebar stays anchored on scroll; only main content scrolls. |
| **5A.13** | [#106](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/106), [#107](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/107) | Encode dashboard (paper-encoded path) | Open Encode. Queue shows pending paper-encoded HCWs (if any). Pick one HCW → form opens in encoder mode (no GPS consent banner per Sprint 4 Task 4.3). Submit → routes through `/admin/api/encode/:hcw_id` (NOT the regular PWA submit path). Audit log shows you as encoder. |
| **5A.14 v2.0.1** | E4-APRT-041 patch | Data → HCWs → Create HCW | Click "Create HCW" button. First-class modal opens (NOT a hand-edited sheet row). Fill in HCW details + facility → save. Fresh enrollment URL minted. Audit logged. (This patch supplanted Round 2's "no UI for creating HCWs" workaround.) |
| **5A.15 v2.0.1** | E4-APRT-044 patch | RBAC role-version cache | Have a SECOND admin (or coordinator) revoke your role mid-session. Within 60 minutes (cache TTL, was infinite before fix), your portal should reflect the revoked permissions on next mutation attempt. Test: ask coordinator to demote you to DataReader, then try to mutate something → blocked. (Pre-fix, you'd retain Administrator until full logout.) |
| **5A.16 v2.0.1** | E4-APRT-045 patch | JWT password_must_change | Coordinator creates a fresh test admin with `password_must_change=true`. You log in as them. Try to call any admin API endpoint directly via DevTools → Network → expect server-side 403 demanding password change first (was client-side-only check before fix; this patch enforces server-side). |
| **5A.17 v2.0.1** | E4-APRT-048 patch | Users — last_login_at write | Login. Open Users dashboard. Find your user row → `last_login_at` column should show current timestamp (within seconds). Sign out + log back in → timestamp updates again. (Pre-fix this column wasn't being written.) |
| **5A.18 v2.0.1** | E4-APRT-049 patch | Design 5-fix sweep | Confirm: button focus rings visible (Tab through forms — focus indicator clear). NO `rounded-full` shapes on filter pills/badges. ReissueTokenModal closes on Escape key. QuotaWidget warning at 80% uses warm-amber color (NOT red). |
| **5A.19 v2.0.1** | E4-APRT-051 patch | User-self password rotation | Click your username at sidebar bottom → menu → "Change password." Modal opens. Set new password (≥8 chars). Sign out + log in with new password → success. Old password no longer works. Audit logged. |

### 5B. New scenarios (R2 + v2.0.1 didn't cover)

Round 2 walked the nominal admin flow on desktop Chrome. These scenarios stress-test what real ops use will actually hit.

#### 5B.1 — Concurrent multi-admin actions

**What to verify:** Two admins acting at once don't corrupt state.

- **5B.1.H1:** You + the other tester both open the Reissue Token modal for the SAME HCW (e.g., DEMO-HCW-005). Both click Confirm at roughly the same moment. Expect: only ONE succeeds; the other gets a clean 409 E_CAS_FAILED error toast (NOT a silent overwrite, NOT a server crash).
- **5B.1.H2:** You bulk-import 5 admin users via CSV while the other tester edits their own role mid-batch. Expect: bulk-import completes; new accounts get the role version effective at-completion-time (NOT at-batch-start-time).
- **5B.1.A1:** You toggle kill_switch ON while the other tester has the HCW PWA open mid-form. Expect: HCW PWA shows kill-switch banner within ~30s; their submit attempts queue locally.

#### 5B.2 — RBAC edge cases

**What to verify:** DataReader role can't escape its scope; permission boundaries are tight.

- **5B.2.H1:** Login as `data_reader_uat`. Try every Data sub-tab (Responses / Audit / DLQ / HCWs) — all should be READ-ONLY. Mutation buttons (Reissue Token, Delete, etc.) hidden OR disabled.
- **5B.2.H2:** As DataReader, open DevTools → Network → manually craft a POST to `/admin/api/hcws/<id>/reissue-token`. Expect: server-side 403 (NOT 200; client-hidden buttons are not the only defense).
- **5B.2.E1:** As DataReader, try to navigate `/admin/users` directly (URL bar). Expect: 403 OR redirect to allowed page. NOT a partial render of the Users dashboard with hidden mutations.
- **5B.2.E2:** As DataReader, try `/admin/roles`. Same expected behavior.

#### 5B.3 — Cross-tab session

**What to verify:** Session state stays consistent across tabs.

- **5B.3.H1:** Open admin portal in Tab A (logged in). Open same URL in Tab B (also logged in). Both work normally.
- **5B.3.H2:** In Tab A, click Sign out. Switch to Tab B. Try to mutate (e.g., reissue a token). Expect: 401 from server; portal redirects Tab B to login (NOT a stale-session crash).
- **5B.3.A1:** In Tab A, change your password (E4-APRT-051 flow). Switch to Tab B. Try to mutate. Expect: server rejects with a clear "session invalidated" message; redirect to login.

#### 5B.4 — Kill-switch + spec-drift admin response

**What to verify:** Admin can quickly invoke + reverse emergency states without breaking the portal.

- **5B.4.H1:** Toggle kill_switch ON. Confirmation modal appears. Save. Verify HCW PWA (open in another tab/window) shows banner within ~30s. Audit log captures the toggle with timestamp + your username.
- **5B.4.H2:** Toggle kill_switch OFF. Same flow in reverse.
- **5B.4.E1:** With kill_switch ON, try to "submit" via DevTools curl to the Worker submit endpoint. Expect: server-side rejection (NOT just client-side gating).

#### 5B.5 — Audit log completeness

**What to verify:** Every meaningful action is captured for compliance.

- **5B.5.H1:** Perform 5 distinct actions (login, reissue token, edit user role, upload file, toggle kill-switch). Open Audit log. Confirm ALL 5 appear with: actor (you), resource (the thing affected), action verb (login / reissue / edit_role / upload / toggle_killswitch), timestamp (within seconds of action), and a `detail` JSON column with action-specific data.
- **5B.5.E1:** Confirm Audit entries CANNOT be deleted by Administrator role (audit immutability is a compliance requirement).

#### 5B.6 — FX-017 deferred touch targets (tablet view)

**What to verify:** Admin Portal works on tablet (not just desktop) for ops users in the field.

- **5B.6.H1:** Open admin portal on a real tablet (Android tablet or iPad), portrait orientation. Sidebar collapses to top horizontal strip (mobile fallback). Main content scrolls. All interactive elements (buttons, sub-tabs, table rows) tappable.
- **5B.6.E1:** Filter chips, table-row buttons, sub-tab nav buttons — measure tap targets on tablet. FX-017 noted these were ~24-26px (below 44px minimum). Document any that are still <44px in your bug report.

#### 5B.7 — Large-data scenarios

**What to verify:** Pagination, search, and sort hold up under realistic data volumes.

- **5B.7.H1:** If demo data only has 12 HCWs, ask coordinator to seed 100+ via the seed-demo helper. Open HCWs tab — pagination + sort + filter work.
- **5B.7.H2:** Same for Audit log (likely already has hundreds of rows from seed + R2/R3 testing).
- **5B.7.A1:** On a slow Chrome device (Network throttling: Slow 3G), open HCWs tab. Loading state visible; no infinite spinner.

---

## 6. Bug-Filing Format

For every bug you find, open a GitHub Issue at the bug repo. Use this template:

```
**Round 3 scenario:** 5A.x (R2/v2.0.1 regression — include `Regression of #N`) OR 5B.x.X1 (new scenario)
**Tester:** Shan / Kidd
**Browser/Device:** desktop Chrome / tablet (model + browser) / etc.
**Admin user:** shan_admin / kidd_admin / data_reader_uat
**Dashboard / Sub-tab:** Data → HCWs / Users / Reports → Map / etc.
**Expected:** [what the spec / scenario says should happen]
**Actual:** [what happened]
**Reproduction steps:**
  1. ...
  2. ...
**Severity:** critical / high / medium / low
**Screenshot / video:** [attach if visual]
**Console errors / network failures:** [paste from DevTools if any]
**Audit log row (if relevant):** [paste from Data → Audit]
```

Apply the label `from-uat-round-3-2026-05` to every R3 bug. Coordinator triages daily.

---

## 7. Triage Cadence

- **Daily check-in:** Coordinator posts a short status to `#f2-pwa-uat` daily 09:00 PHT (Wed/Thu/Fri) — count of new R3 bugs filed (HCW + Admin), critical blockers, fixes-shipped overnight.
- **Sync-up call:** If 5+ open R3 admin bugs by Thu EOD, coordinator schedules a 15-min Slack huddle Fri AM.
- **R3 close:** Friday 2026-05-15 PM. Coordinator marks #271 closed; remaining open R3 bugs are dispositioned (fix-this-sprint / fix-Sprint-006 / won't-fix-with-rationale).

---

## 8. Why this round matters

Round 2 found and fixed 33 admin-side issues in a focused 4-day sweep. Right after R2 closed, the v2.0.1 patch bundle (PR #136) shipped 9 more admin patches (Create-HCW UI, RBAC cache, JWT pwc, design 5-fix sweep, concurrency tests, last_login_at, orphan guards, user-self password rotation) — none of which had explicit tester walks. R3's 5A regression is the first time those patches see real ops-user eyes.

R3's 5B new-scenarios bundle covers the gaps R2's nominal-flow walk didn't touch:
- **Concurrency** is real — multiple ASPSI ops users will work simultaneously during fieldwork
- **RBAC defense-in-depth** matters — DataReader access boundaries WILL be tested by curious users
- **Cross-tab session** is normal — admins multitask
- **Kill-switch** is the most consequential admin control — failure here means submissions burn or stall
- **Audit completeness** is a compliance requirement, not a nice-to-have
- **Tablet support** matters because field-deployed ops users may not have laptops
- **Large-data scenarios** matter because real fieldwork generates 1000s of submissions

Round 3 is your last cheap chance to find admin-side blockers before pretest pilot.

Thanks for testing!
