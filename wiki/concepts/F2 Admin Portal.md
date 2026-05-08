---
type: concept
tags: [f2, pwa, admin-portal, capi, cloudflare, apps-script, rbac, csweb-mirror, sprint-ap]
source_count: 0
---

# F2 Admin Portal

The F2 Admin Portal is the **operations console** for the F2 PWA stack — admin-only routes layered on top of the existing PWA at `f2-pwa.pages.dev`. It mirrors [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb]]'s permission model 1:1 so the F2 backend has the same governance shape as the CSPro F1/F3/F4 stack served by CSWeb. The portal replaces the abandoned **M10 single-`ADMIN_SECRET` Apps-Script-HtmlService** approach.

> **Branch:** `f2-admin-portal` (PR #54 merged to `main` 2026-05-04; v2.0.0 cut to prod the same evening, soak waived)
> **Spec:** `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md` (v0.2)
> **Plan:** `docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md` — 4 sprints, 80 sub-tasks
> **Tracked under:** Epic 4 (`scrum/epics/epic-04-backend-sync-infrastructure.md` → "F2 Admin Portal Track", task IDs `E4-APRT-001..051`)
> **Sprint 005 v2.0.1 plan:** `docs/superpowers/plans/2026-05-11-sprint-005-v2-0-1-plan.md` (drafted 2026-05-07 Sprint 004 Day 4)

## Why a portal (and not just M10)

- M10 was a single shared `ADMIN_SECRET` exposed via Apps Script HtmlService — fine for one-off operator actions, **wrong** for multi-user role-based access, audit trails, session revocation, or anything DOH-facing.
- CSWeb already documents a battle-tested model the F-series stack will rely on for F1/F3/F4 (5 dashboards × per-dictionary up/down × Administrator + Standard User + custom roles). Mirroring that shape on the F2 side keeps governance coherent across all four instruments.
- Versioning, paper-encoder workflow, HCW token reissue, and submission GPS were all blocked or hand-rolled under M10; the portal turns them into first-class admin operations.

## Permission model (CSWeb mirror)

- **5 dashboards:** `data`, `report`, `apps`, `users`, `roles`
- **5 IR-aligned roles** (seedable, with 2 built-ins — Administrator + Standard User — that cannot be deleted)
- **6 per-instrument flags** for fine-grained access (e.g. F2-only Standard User vs full-stack Administrator)
- **Role versioning** with auto-bump on update — every Worker request validates JWT against current `role_version`, so a role change instantly invalidates all sessions for users carrying that role
- Force-revoke session (`revoked_jti` + `revoked_user` lists in KV) — see commit `14ad3f8 feat(admin): force-revoke user sessions (KV + RBAC + UI)`

## Protocol-mandated HCW response-rate gate

[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH Survey Protocol V2 (30 April)|Protocol V2]] (L1565, L1584–L1591) mandates a **60% per-facility HCW response threshold** against the master HCW list captured at the courtesy call (the master list is the formal denominator per the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Manual Working File (2026-05-06 Kidd)|Working File]] L1225–L1227). Operational rules from the protocol:

- **40% midpoint trigger** — if response rate ≤40% at the midpoint of the data-collection window, follow-up procedures initiate.
- **One-time 3-working-day extension** permitted if the facility is below threshold but trending up.
- **60% gate** — if the facility remains below 60% after extension, the Principal Investigator is notified; the facility is flagged for exclusion or weight adjustment with PI/DOH coordination.

The portal currently captures the master HCW list at enrollment (Sprint AP3 Files dashboard, F2_HCWs sheet) but does **not yet surface a per-facility response-rate widget** that hits the 40%/60% thresholds or routes the PI/DOH escalation. When response-rate monitoring becomes a sprint commitment, the protocol is the authority — match its thresholds + escalation routing rather than designing fresh.

## Architecture — 4-tier

1. **Frontend** — admin shell mounted under `src/admin/` of the F2 PWA app (`Login.tsx`, `Layout.tsx`, role-aware nav, dashboards for each of the 5 axes).
2. **Cloudflare Worker** (`apps/worker/`) — JWT mint/verify (HS256, role_version-stamped), RBAC middleware, throttle (per-username + per-IP via KV), `/admin/api/*` route fan-out, 5-minute `scheduled()` cron dispatcher for cron break-out builder.
3. **Apps Script backend** — HMAC-authenticated `doPost` dispatcher; CRUD over Google Sheets-backed tables (Users, Roles, Audit, DLQ, F2_Responses, F2_Audit, F2_HCWs, Files, Settings, Apps).
4. **R2 + KV** — R2 for app/file uploads (bound via wrangler), KV for sessions / throttle counters / revocation lists / role-version cache.

## Sprint breakdown (4 weeks at 1-week solo + AI Scrum cadence)

| Sprint | Theme | Tasks | Notable scope |
|---|---|---|---|
| **AP1** — foundation | week 1 | E4-APRT-001..009 | Wrangler R2 binding + cron, schema migration, Worker HMAC + AS doPost dispatcher, PBKDF2 (600k iters) + JWT mint/verify, two-axis throttle, RBAC middleware, login/logout routes, audit log, 2 Administrators seeded |
| **AP2** — data + report dashboards + PWA GPS | week 2 | E4-APRT-010..019 | Apps Script admin reads, Worker `/admin/api/dashboards/data/*`, F2 PWA Geolocation helper + consent disclosure, F2_HCWs sheet wired at enrollment, sync_report + map_report (PSGC region/province aggregations), Leaflet clustering |
| **AP3** — apps + users + roles + cron break-out | week 3 | E4-APRT-020..029 | Files CRUD + R2 upload allowlist, settings + cron break-out builder, scheduled() dispatcher, Versioning + Files + DataSettings + QuotaWidget, Users CRUD + bulk_create + revoke_sessions, Roles CRUD with auto-version-bump, PWA versioning endpoint |
| **AP4** — paper-encoder + reissue + cutover + v2.0.0 | week 4 | E4-APRT-030..040 | F2 PWA Form refactor for `mode='hcw'/'encoded'`, encode submit, EncodeQueue + EncodePage with autosave, **HCW token reissue with CAS** (prev_jti), ReissueModal with QR + 409 handling, cross-platform QA, security testing, concurrency tests, UX gates, M10 sunset (7-day soak + secret deletion), v2.0.0 release |

## Build state (2026-05-04 — v2.0.0 live in prod)

Sprints AP1–AP4 **functionally complete, end-to-end verified on staging, and cut to production 2026-05-04 evening** (PR #54 merged 15:49 PHT; v2.0.0 cutover same evening, 7-day soak explicitly waived). UAT Round 2 opened to Shan + Kidd with embedded prod-signed enrollment URLs and per-tester admin credentials. ~60 commits, ~19k LOC across the merged branch.

```
beee13e docs(runbook): production cutover runbook
f6ca9b3 fix(apps-script): adminEncodeSubmit accepts payload.encoded_by
9818169 fix(admin): equalize verifyPassword timing for non-existent users (S2)
8254546 fix(apps-script): build script no longer truncates bundle on comment trap
595036d fix(admin): close username-enumeration throttle bypass (S1)
… (~55 more)
796e51a feat(apps-script): admin RPC dispatcher (Task 1.5 — keystone)
```

**Source-of-truth dirs**
- Frontend admin: `deliverables/F2/PWA/app/src/admin/` (Layout, Login, App, per-dashboard subdirs `apps/`, `data/`, `encode/`, `report/`, `roles/`, `users/`, shared `lib/`)
- Worker: `deliverables/F2/PWA/worker/src/admin/` (`routes.ts`, `auth.ts`, `rbac.ts`, `cron.ts`, `apps-script-client.ts`, `throttle.ts`, `handlers/`)
- Apps Script source: `deliverables/F2/PWA/backend/src/Admin*.js` (12 modules including the new `AdminDispatch.js`)
- Bundled to: `deliverables/F2/PWA/backend/dist/Code.gs` (~116k chars)

## Staging stack (live)

- **Sheet:** `15CWE9uQtKXKLYzPLxec9dfMTp2YsdBUOGXebZ626DBU` (workbook "F2 PWA Backend — Staging")
- **AS project:** `F2-PWA-Backend-Staging` deployed at `https://script.google.com/macros/s/AKfycbws8vvypU0WGd9jZ0QZFKYSGFPf-PN9YWtRPOgsgmzV0HMlfPOFmew0VS-Axj9sIYuW/exec`
- **Worker:** `https://f2-pwa-worker-staging.hcw.workers.dev` (re-deployed 2026-05-02 with R2 binding + 5-min cron)
- **KV staging:** `4235ee802d3546b8a20dffa7a5af5ad3` (binding `F2_AUTH`)
- **R2 staging:** `f2-admin-staging` + `f2-admin-staging-preview` (binding `F2_ADMIN_R2`, APAC, created 2026-05-02)
- **Bootstrap admin:** `carl_admin` (Administrator role)
- **Test fixtures still on staging:** `DataReader` role (with `dash_apps:true` from RBAC PATCH test), user `data_reader_test`, HCW `HCW-TEST-001` (paper-encoded test response), data setting `s-346535ac`

## End-to-end smoke proven on staging (all green)

- Login + JWT mint with role-version stamping
- RBAC perm isolation (5/5 routes — DataReader denied admin, Administrator passes)
- Force-revoke (KV `revoked_user:<sub>` checked every request; old JWT → 401 E_AUTH_EXPIRED)
- Throttle: real user AND non-existent user both 401×10 → 429 (after S1 fix)
- Timing equalization: bad-username avg 3389ms ≈ bad-password avg 3681ms (after S2 fix)
- HMAC tampering: bogus / missing / stale-ts / wrong-action all rejected
- Cron break-out: AS run_due → R2 fail caught → mark_complete advances next_run_at
- Quota counter: `as_quota:<UTC-date>` increments per AS call; QuotaWidget reads it
- Encode flow + idempotency: paper-encoded write + duplicate detection
- Reissue token + CAS: first issuance OK; concurrent stale prev_jti → 409 E_CAS_FAILED

## Bugs surfaced and fixed during AP0 dogfood

Mocks couldn't catch any of these — all surfaced only on the live stack:

1. `getActiveSpreadsheet()` null in standalone AS → `getF2Spreadsheet()` helper (20 sites)
2. `LockService.getDocumentLock()` null in standalone AS → `getScriptLock()` (11 sites)
3. Login crash because `admin_users_list` strips password_hash → HMAC-gated `include_password_hash` flag
4. Field name mismatch (`role` vs `role_name`) → handler reads either with `??`
5. Verde Manual color aliases (paper/ink/hairline/signal/error) silently dropping → wired in `tailwind.config.ts`
6. `adminFetch` overrode multipart Content-Type → file upload 400 → skip JSON default for FormData/Blob
7. Build script's regex matched a doc-comment substring, truncating every function after it
8. ScheduledEvent → ScheduledController in cron handler signature
9. AdminEncoder demanded `ctx.actor_username` but dispatcher doesn't propagate → accept `payload.encoded_by` fallback

## Security findings (both fixed)

- **S1** — username-enumeration throttle bypass: `recordFailedLogin` skipped on bad-username → bumps now fire on both paths.
- **S2** — username-enumeration timing oracle (~100ms PBKDF2 delta) → lazy-cached dummy hash; both paths run exactly one PBKDF2.

## Outstanding (NOT coding tasks)

- ~~**Cloudflare R2 plan**~~ — **CLEARED 2026-05-02.** R2 enabled on `Aspsi.doh.uhc.survey2.data@gmail.com's Account` (`b0887ce8ba4e531c00abfe0127b4bc5b`); four buckets created (`f2-admin-staging`, `f2-admin-staging-preview`, `f2-admin`, `f2-admin-preview`); staging worker redeployed with R2 + cron bindings; full upload/list/download/delete cycle smoke-tested green on `f2-pwa-worker-staging`.
- ~~**Production cutover**~~ — **DONE 2026-05-04.** Runbook at `docs/superpowers/runbooks/2026-05-02-f2-admin-portal-prod-cutover.md` executed; PR #54 merged to `main` 15:49 PHT and v2.0.0 cut to prod the same evening with 7-day staging soak explicitly waived (Carl's call, given UAT R2 demo timing).
- ~~**Cross-platform QA**~~ (Sprint 4 Task 4.6 / E4-APRT-035) — **CLOSED 2026-05-05.** All 9 outstanding FX-* findings dispositioned ✅ on E1 Chrome (FX-016 source fix in `src/admin/App.tsx` shipped same day as filing); E2 Firefox / E3 Edge cross-engine pass deferred to Sprint 005 polish (architecturally-clean code; remaining cross-engine risk is visual). FX-017 logged as MEDIUM tablet polish, not a v2.0.0 blocker.
- **M10 sunset** (Sprint 4 Task 4.9) — staging `ADMIN_PASSWORD_HASH` deleted 2026-05-04 (E4-APRT-039 closed). **Production secret pending Sprint 005 (E4-APRT-043)**, scheduled after Carl's hands-on rotation window. (ID re-issued 2026-05-06 because the original E4-APRT-040 was consumed by the v2.0.0 release pulled forward Sprint 004 Day 1.) Sunset = delete (not rotate); `src/admin.ts` legacy routes remain to be removed alongside.
- ~~**v2.0.0 release**~~ (Sprint 4 Task 4.10) — **DONE 2026-05-04 evening.** Tagged + cut; live at `f2-pwa.pages.dev`.

## Sprint 005 polish backlog (10 items, 8 GH issues #56–67 filed + 050/051 to be filed)

The Sprint 005 plan doc at `docs/superpowers/plans/2026-05-11-sprint-005-v2-0-1-plan.md` re-classifies these into **Tier 1 (security + lockout, MUST land in v2.0.1)**, **Tier 2 (visible UX gaps, want in v2.0.1)**, and **Tier 3 (polish, deferrable to v2.0.2)**. Items are listed below by ID for cross-reference; tier mapping in the plan doc.

- **E4-APRT-037** (#63, **Tier 3**) — concurrency tests (two-admin reissue race / bulk import + role edit / cron + PWA submit). Deferred from Sprint AP4 cross-platform QA. Estimate 3h.
- **E4-APRT-041** (#58, **Tier 2**) — Create-HCW UI in Admin Portal (v2.0.1 patch). Surfaced 2026-05-04 during UAT Round 2 prep. Estimate 3h.
- **E4-APRT-042** (#64, **Tier 2**) — per-tester admin user accounts on prod (separate Shan/Kidd from `carl_admin`). Estimate 1h.
- **E4-APRT-043** (#65, **Tier 1**) — production `ADMIN_PASSWORD_HASH` deletion + `src/admin.ts` cleanup (priority HIGH; gated on Carl's hands-on window). ID re-issued 2026-05-06 because original E4-APRT-040 consumed by v2.0.0. Estimate 30m.
- **E4-APRT-044** (#56, **Tier 1**) — RBAC role-version cache stale-entry fix (HIGH, conf 9/10 from /cso): `worker/src/admin/rbac.ts:22-40,103-115` evict cached `name:v1` entries on role version bump. Estimate 1h.
- **E4-APRT-045** (#57, **Tier 1**) — `password_must_change=true` server-side enforcement (MEDIUM, conf 9/10 from /cso): currently client-side only; Worker mints fully-privileged 4h JWT regardless of flag. Pairs with E4-APRT-051 to replace the placeholder change-password UI with a real form. Estimate 1.5h.
- **E4-APRT-048** (#66, **Tier 2**) — Users `last_login_at` write path (half-built bug surfaced 2026-05-06 PO review): schema + UI exist but no write on successful login. Confirmed still unfixed 2026-05-07 — API response from carl_admin password rotation showed `"last_login_at":""` despite recent login. Estimate 30m.
- **E4-APRT-049** umbrella (#59 H-2 / #60 H-3 / #61 M-1 / #62 M-3 / #67 M-4, **Tier 3**) — design-review deferred findings sweep from E4-APRT-038. 5-fix bundle: button focus rings, input focus rings, `rounded-full` cleanup, QuotaWidget `--warning` token, ReissueModal Escape-key. Total ~40 min sweep.
- **E4-APRT-050** (GH issue TBD, **Tier 1**) — orphan-admin guard + self-delete guard on `adminUsersDelete`. **Surfaced 2026-05-07 (Sprint 004 Day 4) by UAT Round 2 incident**: Shan executed step U.E1 of `docs/F2-PWA-UAT-Round-2-Admin-Portal-Tester-Guide-2026-05-04.md` §5.12 (delete carl_admin → expected guard "cannot orphan the last Administrator"). Both Worker (`worker/src/admin/handlers/users.ts:220-236`) and Apps Script (`backend/src/AdminUsers.js:231-248`) lack the guard entirely; row was hard-deleted from prod F2_Users; Carl was locked out. Recovery via shan_admin recreating the row + Worker API two-step PATCH. **Fix:** AS adds `_countAdmins()` helper; rejects with `E_CONFLICT` "cannot orphan the last Administrator" when target.role_name=Administrator and admin-count ≤ 1; also rejects `username == actor.username` with `E_CONFLICT` "cannot delete your own account"; Worker passes `actor.username` through; integration tests both rejection paths. Estimate 1.5h.
- **E4-APRT-051** (GH issue TBD, **Tier 1**) — change-password UI for `/admin/me/change-password`. **Surfaced 2026-05-07 (Sprint 004 Day 4) during recovery from E4-APRT-050 incident.** Route exists but renders placeholder copy ("This view is being built in a later sprint."). Pairs with E4-APRT-045. Once both land, server enforces flag + placeholder is replaced with working form. Frontend form (current pw + new pw + confirm) replacing placeholder; new Worker `PATCH /admin/api/me/password` route with timing-safe current-pw verify; AS `admin_users_change_own_password` RPC; mints fresh JWT after change. Estimate 2h.

**Total Sprint 005 commit ~14h** (Tier 1 = 6.5h: 050/051/045/044/043; Tier 2 = 4.5h: 048/041/042; Tier 3 = ~3h pull-from-headroom: 037/049 if time permits, otherwise carry to v2.0.2 / Sprint 006). Carl's solo capacity ~25h → ~11h headroom for R2/R3 bug-fix capacity + Tier 3 pulls.

## CSWeb-mirror parity backlog (unscheduled — surfaced 2026-05-06 PO review)

- **E4-APRT-046** — Files dashboard Create Folder feature. R2 doesn't natively support folders; impl pattern uses `folder_path` column on F2_Files sheet + tree-style breadcrumbs in FilesPanel. Open design Q: flat (1-level) vs nested. Estimate 5h.
- **E4-APRT-047** — Files dashboard Rename feature. Renames `original_filename` (display) only; `file_id` (R2 key) stays stable so download links don't break. Estimate 1.5h.

## Operational gotchas (captured from AP0)

- **Standalone vs bound AS:** the `getF2Spreadsheet()` helper falls back to `openById(SPREADSHEET_ID)` when the script isn't bound to a workbook. Both modes work.
- **PowerShell + wrangler secret put** silently adds a UTF-8 BOM. Always pipe via `cmd.exe /c "type <utf8-no-bom-file> | wrangler secret put NAME"`. The BOM breaks `atob()`, `fetch()`, and HMAC parsing downstream.
- **AS Web App freeze-at-deploy** — editor save isn't enough. Must Deploy → Manage deployments → New version to update what the URL serves.
- **Cron UTC clock** — `*/5` fires from UTC midnight, not local. Next tick is up to 5 min away.

## Relationship to other concepts

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb]] — the permission model the portal mirrors (5 dashboards + per-dictionary axes; Administrator + Standard User built-ins).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Google Forms Track]] — the abandoned earlier F2 capture path; the admin portal lives on top of the **PWA** that replaced it.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/gstack F2 PWA Workflow]] — adopted gstack skill subset under which the admin portal is being built.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual]] — the HCW protocol whose paper-encoder fallback is implemented as Sprint AP4 of the portal.
