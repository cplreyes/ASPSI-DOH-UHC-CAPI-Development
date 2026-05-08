---
status: DRAFT — opens 2026-05-12 (Tue, Sprint 005 Day 2)
round: 3
target_release: F2 PWA + Admin Portal v2.0.1
target_environment: STAGING (`https://f2-pwa-staging.pages.dev/admin`)
worker_url: https://f2-pwa-worker-staging.hcw.workers.dev
testers: Shan Lait (ASPSI RA), Kidd (ASPSI RA)
gh_label: from-uat-round-3-2026-05-12
gh_milestone: v2.0.1 — UAT Round 3
slack_channel: "#f2-pwa-uat"
plan_ref: docs/superpowers/plans/2026-05-11-sprint-005-v2-0-1-plan.md
---

# F2 Admin Portal — UAT Round 3 Tester Guide (DRAFT)

> **R3 is staging-only and Admin-Portal-only.** v2.0.1 contains no HCW Survey changes; the public survey at `f2-pwa.pages.dev` stays at v2.0.0 throughout this round. R3 tests the v2.0.1 release candidate before it cuts over to production on Fri 2026-05-15.

## Round-context table

| | Round 2 (still open) | Round 3 (this guide) |
|--|---------------------|----------------------|
| **URL** | `https://f2-pwa.pages.dev/admin` | `https://f2-pwa-staging.pages.dev/admin` |
| **Worker** | `https://f2-pwa-worker.hcw.workers.dev` | `https://f2-pwa-worker-staging.hcw.workers.dev` |
| **Version** | v2.0.0 (production) | v2.0.1-rc (rolling — staging) |
| **Surface** | HCW Survey + Admin Portal | Admin Portal only |
| **Bug label** | `from-uat-round-2-2026-05` | `from-uat-round-3-2026-05-12` |
| **Credentials (your username)** | `<your>_admin` | `<your>_admin` (same username) |
| **Credentials (password)** | (your prod password) | (your staging password — different from prod) |

**Always confirm the version banner in the app footer before filing a bug.** R2 should show `v2.0.0`. R3 should show `v2.0.1` followed by an `-rc.<N>` or commit SHA suffix.

## Pre-flight (5 min, Tuesday morning)

- [ ] Open `https://f2-pwa-staging.pages.dev/admin` in a fresh browser tab.
- [ ] Login screen renders with Verde Manual styling.
- [ ] Login as `<your>_admin` with your **staging** password (Carl will share via Viber).
- [ ] Land on default dashboard.
- [ ] Footer shows `v2.0.1-rc...` and Worker version `2.0.1-staging` (Versioning panel under Apps dashboard).
- [ ] DevTools console clean on first paint (no 4xx/5xx aside from expected unauth pings).

## Test surface — focused on v2.0.1 changes

### 1. Users dashboard — orphan-admin guard now active (E4-APRT-050)

> **R2 §5.12 step U.E1 was previously broken — guard wasn't implemented. R3 verifies the fix.**

- [ ] **U.E1 (now passing)** — Try to delete the only Administrator-role user on staging. Should be **blocked** with error: `cannot orphan the last Administrator`. The row stays.
- [ ] **U.E1.b (new)** — With multiple Administrators present (`carl_admin` + `shan_admin` + `kidd_admin`), delete one. Should succeed (count > 1). Re-create immediately to restore baseline.
- [ ] **U.E6 (new — self-delete guard)** — While logged in as `<your>_admin`, try to delete your own user row. Should be **blocked** with error: `cannot delete your own account`.

### 2. Change-password UI — placeholder replaced (E4-APRT-051 + E4-APRT-045)

- [ ] **CP.A1** — Login with a fresh test account that has `password_must_change=true`. App should redirect to `/admin/me/change-password` and show a **real form** (current pw + new pw + confirm + show/hide toggle), not the placeholder.
- [ ] **CP.A2** — Submit the form with valid inputs. Success message; redirected to dashboard; `password_must_change` cleared in next user-list refresh.
- [ ] **CP.E1** — Submit with current pw wrong. Reject `E_AUTH` "current password incorrect"; form stays.
- [ ] **CP.E2** — Submit with new pw < 8 chars. Reject "password must be ≥8 characters".
- [ ] **CP.E3** — Submit with new pw matching confirm-pw mismatch. Reject "new password and confirmation do not match".
- [ ] **CP.E4 (server-enforce — E4-APRT-045)** — While `password_must_change=true`, try to call any other admin API endpoint (e.g., `GET /admin/api/dashboards/users`) via DevTools console fetch. Should reject with `E_PASSWORD_CHANGE_REQUIRED`.

### 3. last_login_at populates (E4-APRT-048)

- [ ] **LL.A1** — Note the `Last login` value for your row in Users dashboard before login.
- [ ] **LL.A2** — Log out, log back in.
- [ ] **LL.A3** — Refresh Users dashboard. Your row's `Last login` value should now show the recent login time (within seconds of step LL.A2).
- [ ] **LL.A4** — Check Audit dashboard. New row with `event_type=admin_login`, ACTOR = your username, RESOURCE = your username.

### 4. Create-HCW UI (E4-APRT-041)

- [ ] **CH.A1** — Data dashboard → HCWs sub-tab. New `+ Create HCW` button visible top-right.
- [ ] **CH.A2** — Click button. Modal opens with form: `hcw_id`, `facility_id` (dropdown from FacilityMasterList), `facility_name` (auto-fills from facility_id), `status` (default `pending`).
- [ ] **CH.A3** — Submit valid form. New row appears in HCWs list. Audit row written.
- [ ] **CH.E1** — Submit with `hcw_id` that already exists. Reject `E_CONFLICT` "hcw_id already exists".
- [ ] **CH.E2** — Submit with empty `hcw_id`. Reject "hcw_id required".
- [ ] **CH.E3** — Submit while logged in as a non-Administrator role. Reject `E_FORBIDDEN`.

### 5. Per-tester admin accounts (E4-APRT-042)

- [ ] **PT.A1** — Confirm your `<your>_admin` row exists with `role_name=Administrator` in Users dashboard.
- [ ] **PT.A2** — Audit dashboard rows attributed to **you**, not to `carl_admin`, when you make a mutation.

## Regression sweep (10 min — re-test from R2 baseline)

Quick re-runs of areas not changed in v2.0.1 to confirm we didn't break anything:

- [ ] **Login flow** — bad pw 3× → throttle warning; correct pw → JWT; logout → cleared.
- [ ] **Data dashboard** — Responses tab loads; Audit tab renders FX-006 columns (Actor / Resource / Detail) populated.
- [ ] **Apps dashboard** — Files panel uploads + downloads + deletes a sample file; Versioning shows v2.0.1-rc.
- [ ] **Reissue token** — Force-revoke a test HCW; reissue; QR + mono URL render.
- [ ] **Roles dashboard** — view-only is fine; don't mutate (would affect testers).

## Filing bugs

- GH label: **`from-uat-round-3-2026-05-12`** (NOT `from-uat-round-2-2026-05`)
- Title prefix: `[R3]`
- Body: env (always staging for R3) + version banner contents + repro steps + screenshot
- Severity: CRITICAL (blocks v2.0.1 ship) / HIGH (must fix before ship) / MEDIUM (defer to v2.0.2 OK) / LOW (polish)

## Sign-off

When you've completed all items + filed all bugs, comment in `#f2-pwa-uat`:

> R3 sign-off — `<your>_admin`. Findings filed under label `from-uat-round-3-2026-05-12`. Critical/High count: <N>.

Carl reviews + decides on v2.0.1 cutover Friday.

---

*Draft authored 2026-05-07 (Sprint 004 Day 4). Will be renamed `F2-PWA-UAT-Round-3-Admin-Portal-Tester-Guide-2026-05-12.md` and published Tuesday morning when R3 opens.*
