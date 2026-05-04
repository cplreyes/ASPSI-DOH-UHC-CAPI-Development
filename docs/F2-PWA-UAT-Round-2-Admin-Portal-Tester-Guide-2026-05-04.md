# F2 PWA — UAT Round 2 (Admin Portal side) — Tester Guide

**Round:** 2 (testers' numbering)
**Drafted:** 2026-05-04
**Side:** F2 Admin Portal (operations console — login, dashboards, Reissue, DLQ, RBAC)
**Companion guide:** `docs/F2-PWA-UAT-Round-2-HCW-Survey-Tester-Guide-2026-05-04.md` (HCW Survey side, for Shan)
**Coordinator:** Carl Patrick L. Reyes (Data Programmer)
**Window:** Opens 2026-05-04 evening · No hard close (rolling; daily triage)

> **Project context.** The F2 Admin Portal is the operations console ASPSI ops users run from. It mirrors the **CSWeb** dashboard model — same shape, 5 dashboards × 5 roles × per-instrument flags. An ops user enrolls HCWs (mints tablet tokens), monitors submissions, triages dead-letter-queue entries, manages files (training plans, rosters), schedules CSV break-out exports, audits actions, and onboards other ops users. Round 2's job is to break the **admin-facing flow** before the field rollout begins.

> **Scope of this guide.** Admin-portal-side only — every dashboard, every sub-tab, every workflow an ops user touches. HCW-side (PWA enrollment + survey completion) is in the companion guide above.

---

## 1. Quick Reference

| Item | Value |
|---|---|
| **Production Admin Portal** | https://f2-pwa.pages.dev/admin/login |
| **Help (no-auth)** | https://f2-pwa.pages.dev/admin/help |
| **Worker (curl smoke)** | https://f2-pwa-worker.hcw.workers.dev |
| **Spec — full Admin Portal design** | `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md` |
| **Concept overview** | `wiki/concepts/F2 Admin Portal.md` |
| **Bug repo** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues |
| **Bug-filing label** | `from-uat-round-2-2026-05` |
| **Slack channel (blockers only)** | `#f2-pwa-uat` on `aspsi-doh-uhc-survey2.slack.com` |
| **Release notes** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v2.0.0 |

---

## 2. Tester Roster + Credentials

**Each tester gets their own admin credential — no shared logins.** Audit columns must show who clicked what; sharing a single login collapses attribution.

### Primary roster

| Tester | Role | Username | Initial password |
|---|---|---|---|
| **Kidd** (ASPSI main RA) | Admin Portal exhaustive pass — primary tester | `kidd_admin` | _DM from coordinator_ |
| _additional admin testers TBD_ | _Carl to fill_ | _e.g., `<name>_admin`_ | _coordinator provisions + DMs_ |

### RBAC test credential (shared — only used for Section 5.13 RBAC scenarios)

| Username | Password | Role | Why |
|---|---|---|---|
| `data_reader_uat` | _DM from coordinator_ | DataReader | Use this to exercise the RBAC story — login as DataReader, confirm Users / Roles dashboards are hidden, mutations are blocked. |

> All 3 accounts have `password_must_change=true` — on first login, the portal forces you to set a new password (≥8 chars). After your first reset, the initial password is dead.

> **First-login flow.** All three accounts are created with `password_must_change=true`. On your first successful login, the portal forces you to set a new password (≥8 chars). Pick something memorable but not guessable; coordinator never sees your working password after handoff.

---

## 3. Pre-Flight Checks (do these before testing)

1. **Open `https://f2-pwa.pages.dev/admin/login`** in Chrome. Page loads with the Verde paper background and login form.
2. **Login with your dedicated credential** (username from this guide, initial password from the coordinator's DM). Forced to set a new password (≥8 chars); do so. Log back in.
3. **Land on Data dashboard.** Sidebar shows your username + role badge ("Administrator" / "DataReader") at the bottom-left.
4. **Apps & Settings → Versioning** should read **PWA: 2.0.0** + **Worker: 2.0.0+0f2fb0e** or later.
5. **Open `https://f2-pwa.pages.dev/admin/help` in incognito** (no auth). Help page renders without redirect to login.
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

Main panel: section heading at top, sub-tab nav (where applicable), single active component.

URLs use `?tab=<key>` to deep-link sub-tabs. Refresh preserves the active sub-tab.

---

## 5. Test Scenarios

Walk every dashboard, every sub-tab. Test the RBAC story by switching personas mid-session.

### 5.1 Login + session

#### Happy

- **L.H1** — Login with `kidd_admin` + initial password (from coordinator DM). Forced to set a new password (≥8 chars). Re-login with new password — succeeds.
- **L.H2** — On second login, land on Data dashboard. Sidebar shows username + role.
- **L.H3** — Logout via sidebar bottom button. Land on login screen. Subsequent attempt to access `/admin/data` redirects to `/admin/login`.

#### Alternative

- **L.A1** — Login in tab 1, navigate `/admin/data/responses?id=DEMO-HCW-001-resp-1` directly in tab 2. Same session shared, deep link works.
- **L.A2** — Mid-workflow refresh (e.g., on Data → Audit). Re-prompted to login (admin tokens are in-memory only by design — spec §10.4). After re-login, deep-link is preserved.
- **L.A3** — Wait for token TTL expiry (4h per spec §6.3) by leaving a tab idle. On next action, prompted to re-login.

#### Error

- **L.E1** — Login with wrong password → "Invalid credentials" message; counter increments.
- **L.E2** — N consecutive wrong passwords (try 5–10). Throttle / lockout kicks in (specific N is in spec §6.1; report what you observe).
- **L.E3** — Login with username that doesn't exist → same "Invalid credentials" message (don't leak whether the username exists).
- **L.E4** — Use DevTools to tamper with the JWT (modify a byte). Refresh. Token rejected, redirect to login.
- **L.E5** — Login with the *initial* password after you've reset it → rejected.

### 5.2 Data dashboard — Responses sub-tab

> **Project context:** Lists every F2 HCW survey submission. Operators triage for completeness, drill into individual responses to verify content, filter by date / facility / source_path.

- **R.H1** — List view loads; sortable columns; pagination if >20 rows; current count of seeded responses (~9) visible.
- **R.H2** — Click a `DEMO-HCW-*` submission. ResponseDetail page shows per-question answers, metadata (timestamps, geolocation if any), source_path.
- **R.H3** — Verbatim question text matches `deliverables/F2/F2-Spec.md` exactly (no paraphrasing).
- **R.A1** — Filter by date range / facility / source_path. Combinations should work.
- **R.A2** — Sort by submitted_at_server descending; most recent first.
- **R.E1** — Filter to a range with no rows → empty state ("No matches"), not a crash.
- **R.E2** — Click into a deleted submission (if any) → graceful 404 page.
- **R.E3** — Try to edit a Response from this page (not currently allowed) → confirm there's no Edit button (read-only by spec).

### 5.3 Data dashboard — Audit sub-tab

> **Project context:** Forensic event log. Every PWA submit, every admin action, every HMAC-signed Worker→Apps Script call. Operators check this when investigating data anomalies.

- **A.H1** — Audit log loads with chronological events; most recent first.
- **A.H2** — Find your most recent `admin_login` row. Verify:
  - **Actor** column = your username (e.g., `kidd_admin`)
  - **Resource** column = populated where applicable (or `—` for login)
  - **Detail** / **Event Payload** column = JSON snippet
  - **Request ID** column = UUID present
- **A.A1** — Click a row → full payload JSON visible in detail panel.
- **A.A2** — Filter by event_type (e.g., `admin_hcws_reissue_token`); confirm filter works.
- **A.E1** — Any column rendering as `—` when sheet has data → file as recurrence of FX-006.
- **A.E2** — Try to delete an audit row (not allowed) → confirm there's no Delete affordance.

### 5.4 Data dashboard — DLQ sub-tab

> **Project context:** Dead-Letter Queue — submissions that failed processing and gave up retrying. Manual replay UI. Critical operational safety net.

- **D.H1** — DLQ list loads. Seed has 1 demo entry; click into it.
- **D.H2** — DLQ row shows: timestamp, hcw_id, reason, payload preview.
- **D.A1** — If a Replay button exists, click it; confirm it re-queues. (May be Sprint 005; if not present, note.)
- **D.E1** — DLQ row payload not readable → bug.
- **D.E2** — Try to delete a DLQ entry → confirm whether allowed; if so, audit row should track the deletion.

### 5.5 Data dashboard — HCWs sub-tab + Reissue Token flow

> **Project context:** HCW enrollment registry — one row per HCW who can submit. Operators use this to enroll new HCWs (currently sheet-append; UI ships in v2.0.1) and to re-issue tokens when HCWs lose their device or token expires.

#### Happy

- **H.H1** — HCW list loads with 12 `DEMO-HCW-*` rows.
- **H.H2** — Click any row → **Reissue Token** modal opens within ~2s.
- **H.H3** — Modal shows: mono URL + Copy URL button; QR code (192×192); Copy Token button; "Issue new token" confirmation.
- **H.H4** — URL starts with `https://f2-pwa.pages.dev/...` (NOT `staging.`).
- **H.H5** — QR scans correctly with a phone camera.

#### Alternative

- **H.A1** — Click Reissue Token twice on same HCW. Each click mints a new token; the prior token is revoked.
- **H.A2** — Two admin users (you + coordinator) click Reissue at near-same time on same HCW. One wins, the other gets a 409 / "conflict, please refresh" message. (This is intentional CAS protection — coordinate with another tester.)
- **H.A3** — Filter by facility_id; subset list loads.

#### Error

- **H.E1** — URL printed in modal points at `staging.f2-pwa.pages.dev` from prod admin → bug (cross-env URL bleed).
- **H.E2** — QR code missing or corrupt → bug.
- **H.E3** — Reissue fails silently with no error toast → bug.
- **H.E4** — Reissue an HCW with an in-flight session → behavior should match spec §11 (revoke + re-issue, not silent overwrite).

### 5.6 Reports — Sync Report sub-tab

> **Project context:** Submission counts grouped by spec_version + facility. Operators verify field rollout coverage matches expectations.

- **SR.H1** — Sync Report loads with submission counts.
- **SR.H2** — Numbers match what you can count manually in F2_Responses (filter to DEMO-HCW-*; should be ~9).
- **SR.A1** — Filter by date range; counts adjust.
- **SR.E1** — Empty state when no submissions match → graceful message.

### 5.7 Reports — Map Report sub-tab

> **Project context:** Submissions plotted on a Leaflet + Carto Positron tile map of the Philippines. Operators verify geographic coverage and spot outliers (submissions outside expected sampling regions).

- **M.H1** — Map renders with PH-only bounds (Luzon top, Mindanao bottom).
- **M.H2** — Verde-styled emerald pins visible at the 3 demo facilities (NCR, IV-A, III).
- **M.H3** — Click a pin → Verde-styled popup with `hcw_id`, `facility_id`, timestamp, "View full case →" link to ResponseDetail.
- **M.H4** — At PH zoom, "West Philippine Sea" appears in labels (not "South China Sea" overlay).
- **M.A1** — Zoom in to a single facility → individual pins remain clickable.
- **M.A2** — Pan the map → bounds prevent panning beyond PH+EEZ borders.
- **M.E1** — Pins invisible / transparent → bug (likely CSS regression).
- **M.E2** — Map zooms outside PH (HK / Taiwan / SCS prominent) → bug.
- **M.E3** — Click pin, popup link → broken navigation → bug.

### 5.8 Apps & Settings — Versioning sub-tab

> **Project context:** "Which build is in front of users right now?" Critical for UAT triage — confirms whether a reported bug is on the current build.

- **V.H1** — Panel shows: PWA build SHA, Worker version, Apps Script ID; per-spec submission counts.
- **V.H2** — PWA version reads `2.0.0` (or later); pwa_build_sha = `0f2fb0e` (or later).
- **V.E1** — Any field reads `unknown` → bug (vars not threaded through to runtime).

### 5.9 Apps & Settings — Files sub-tab

> **Project context:** Operator-uploaded files (training plans, facility rosters) backed by Cloudflare R2. PDF / ZIP / PNG / JPEG / GIF, ≤100 MB.

- **F.H1** — File list loads; demo seed has 2 files.
- **F.H2** — Upload a small PDF (≤5 MB). Appears in list within ~5s; downloadable; deletable.
- **F.A1** — Drag-drop upload (instead of file picker) → same result.
- **F.A2** — Upload a file with the same name as an existing one → confirm whether suffix-disambiguated or rejected.
- **F.E1** — Try to upload an SVG / HTML / JS file → rejected by allowlist.
- **F.E2** — Try to upload a >100 MB file → rejected by size limit.
- **F.E3** — Delete a file then try to download it → 404.
- **F.E4** — Upload a file with non-ASCII filename (e.g., "Plano-Q1-Niño.pdf") → preserved correctly through download.

### 5.10 Apps & Settings — Data Settings sub-tab

> **Project context:** Scheduled CSV break-out exports of F2_Responses to R2. Worker cron fires every 5 minutes; settings whose `next_run_at` has elapsed run.

- **DS.H1** — List loads; demo seed has 0 settings (empty state).
- **DS.H2** — Create a Data Setting (instrument: F2; included_columns: subset; interval: 5 min). Saves; visible in list.
- **DS.A1** — Edit interval → next_run_at recalculates.
- **DS.A2** — Disable a setting → no longer fires.
- **DS.E1** — Create with empty fields → validation errors.
- **DS.E2** — Create with `included_columns` containing fields not in F2_Responses → reject with clear message.
- **DS.E3** — Wait 5 minutes; check the R2 break-out CSV appears in the configured `output_path_template` location (coordinator can verify R2 buckets directly).

### 5.11 Apps & Settings — Apps Script Quota sub-tab

> **Project context:** Daily Apps Script execution count against the 20,000-call ceiling. Hard limit — when it hits 100%, backend rejects writes until UTC rollover.

- **Q.H1** — Quota widget shows daily call count + 20,000 ceiling.
- **Q.A1** — Refresh → number increments (each admin RPC bumps the counter).
- **Q.E1** — Number reads 0 indefinitely → bug (counter not wired).

### 5.12 Users dashboard

> **Project context:** Admin user CRUD. Onboard new ASPSI ops users without writing code — give them a role, not a custom build.

- **U.H1** — User list loads. You see yourself + `carl_admin` + other testers + `data_reader_uat`.
- **U.H2** — Click **Create User** → fill form → submit → new row appears in list.
- **U.A1** — Edit your own first_name → persists.
- **U.A2** — Use **Bulk Import** CSV → preview UI shows valid rows + rejection reasons for invalid; confirm only valid rows import.
- **U.A3** — Use **Force-revoke sessions** on a user → next time they hit the API, their JWT is rejected; they must re-login.
- **U.E1** — Try to delete `carl_admin` (the only original Administrator) → blocked: "cannot orphan the last Administrator".
- **U.E2** — Try to set yourself to a non-existent role → rejected.
- **U.E3** — Bulk Import with all-invalid rows → nothing imports; clear error report.
- **U.E4** — Try to create a user with a username that already exists → reject "username taken".
- **U.E5** — Set a password <8 chars → reject "password must be ≥8 chars".

### 5.13 Roles dashboard

> **Project context:** 5 dashboards × per-instrument up/down flags. Built-in roles (Administrator + DataReader) are immutable; custom roles can be created.

- **RL.H1** — Roles list loads. `Administrator` + `DataReader` marked is_builtin.
- **RL.A1** — Create a new role `MyTestRole` with partial flags (e.g., dash_data only). Shows in list.
- **RL.A2** — Edit `MyTestRole` flags → version increments → users with this role get force-revoked on next call.
- **RL.E1** — Try to delete `Administrator` → rejected ("cannot delete built-in").
- **RL.E2** — Try to delete a role that has users assigned → rejected ("would orphan N users").
- **RL.E3** — Try to delete `DataReader` → rejected.

### 5.14 RBAC + persona switching (the spec story)

> **Project context:** Same backend, different role, capability surface adapts. This is the spec's core value prop — **test it explicitly**.

- **RB.H1** — While logged in as `kidd_admin` (Administrator), confirm all 5 dashboards visible: Data / Reports / Encode / Apps & Settings / Users / Roles. All Reissue / Create / Delete actions enabled.
- **RB.H2** — Logout. Login as `data_reader_uat` (initial password from coordinator DM; reset on first login).
- **RB.H3** — As `data_reader_uat`, confirm:
  - **Visible** dashboards: Data, Reports, Encode (read-only), Apps & Settings (read-only).
  - **Hidden** dashboards: Users, Roles.
  - **Hidden / disabled** actions: Reissue Token (HCWs tab), Create User, Delete Role, Edit Data Setting.
  - **Visible** actions: download files, view audit, view DLQ payloads.
- **RB.E1** — As `data_reader_uat`, hit `/admin/users` directly via URL bar. Expect: redirect to Data dashboard or 403 page; NOT silent display of the dashboard.
- **RB.E2** — As `data_reader_uat`, send a POST to `/admin/api/dashboards/users` directly via curl with your JWT. Expect: 403 / E_NOT_PERMITTED.

### 5.15 Help tab no-auth access

- **HP.H1** — Open `https://f2-pwa.pages.dev/admin/help` in incognito → renders without redirect to login.
- **HP.H2** — Navigate every section: Quick Start, Dashboard guide, Data sub-tabs, Reports sub-tabs, Apps & Settings sections, 5 Workflows, Roles & permissions, Glossary, Support.
- **HP.E1** — Help page redirects to login → bug (intentional no-auth).

### 5.16 Sub-tab pattern + sidebar

- **N.H1** — Walk every sub-tab on every dashboard (Data 4 / Reports 2 / Apps & Settings 4). Active tab highlighted with border-b-2 + bold ink.
- **N.H2** — Refresh on each sub-tab → URL preserves `?tab=<key>`; same sub-tab loads.
- **N.A1** — Resize window <768px → sidebar collapses to horizontal nav strip at top.
- **N.E1** — Sidebar scrolls with main content (should stay anchored) → bug.
- **N.E2** — Active tab styling inconsistent across dashboards → bug.

### 5.17 Encode dashboard (paper-encoded path)

> **Project context:** When a HCW fills the survey on paper (offline), an ASPSI ops user "encodes" the answers into the system via the Encode dashboard. Carries `source_path = paper_encoded`.

- **E.H1** — Encode dashboard loads with a list of HCWs eligible for encoding (e.g., enrolled but not submitted).
- **E.H2** — Click an HCW → encode form opens; same shape as the HCW survey, but pre-filled with HCW context.
- **E.H3** — Submit → row appears in F2_Responses with `source_path = paper_encoded` and `encoded_by = <your username>`.
- **E.E1** — Try to encode an HCW who has already submitted via PWA → confirm whether allowed (override) or blocked.
- **E.E2** — Encode partial → save partial → return later → values restore.

---

## 6. Bug Filing Protocol

**One bug per issue.** File on GitHub Issues with the label below. For **blockers** (admin can't login, RBAC fails open, audit attribution wrong, data lost), ALSO ping `#f2-pwa-uat` Slack so it surfaces faster than the daily triage cycle.

### Issue title format

`[F2 UAT R2 Admin] <short title>` — e.g., `[F2 UAT R2 Admin] Audit Actor column blank for admin_login rows`

### Issue body template

```markdown
**Tester:** Kidd
**Date / time (PHT):** 2026-05-XX HH:MM
**Browser + OS:** Chrome 124 / Win11 (or whatever)
**Severity:** blocker | high | medium | low
**Scenario ID:** A.H2 (from Section 5 of this guide)
**Logged-in as:** kidd_admin (Administrator)

**Steps to reproduce:**
1. …
2. …
3. …

**Expected:** (cite spec line if applicable — e.g., `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md` §11.3)

**Actual:**

**Screenshot / video:** (attach)

**Console / Network evidence:** (paste relevant errors, request IDs, response codes)

**Request ID:** (paste from Audit row or Network response)
```

### Label

`from-uat-round-2-2026-05`

### Severity guidance

| Severity | Definition | Channel |
|---|---|---|
| **Blocker** | Admin can't login · RBAC fails open · audit attribution wrong · data lost · prod down | GitHub + Slack `#f2-pwa-uat` |
| **High** | Major flow broken with workaround · visibly incorrect data · wrong-actor on audit | GitHub |
| **Medium** | Inconvenient bug · wrong copy · missing tooltip · cross-browser visual diff | GitHub |
| **Low** | Cosmetic · polish · low-frequency · UX nit | GitHub |

> **Spec divergence:** if the deployed admin portal contradicts `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md`, that's a **portal bug**. If the portal matches the spec but the spec feels wrong, that's a **spec bug** — file separately and tag the coordinator.

---

## 7. Cadence

- **Daily triage** — coordinator reviews new issues each morning at standup; tags severity, assigns owner, sets target ship.
- **Blockers** — same-day patches; you'll be asked to re-test on staging before patch hits prod.
- **High** — next-day patches.
- **Medium / Low** — queue for Sprint 005 unless trivial (≤30 min fix).
- **Round closes** — when issue list drained or coordinator declares cutover.

---

## 8. After Round 2 Closes

- Coordinator sweeps `from-uat-round-2-2026-05`-labeled issues; one-page summary at `deliverables/F2/PWA/qa-reports/uat-round-2-summary-2026-05-XX.md`.
- All `DEMO-*`-tagged seed data removed via `purgeDemoData()` on prod AS.
- Per-tester admin accounts stay; revoke as needed.
- v2.0.1 patch ships with the bundle of fixes; Round 3 uses an updated guide.

---

*Drafted 2026-05-04 by Carl Patrick L. Reyes. Test scenario inventory adapted from `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md` (Admin Portal spec) + `wiki/concepts/F2 Admin Portal.md` (concept overview) + `deliverables/F2/PWA/qa-reports/qa-report-cross-platform-admin-portal-2026-05-02.md` (Round 1 known findings to confirm fixed). File issues against the GitHub repo with the label above; coordinator monitors daily.*
