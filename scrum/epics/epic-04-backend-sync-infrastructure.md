---
epic: 4
title: Backend & Sync Infrastructure
phase: per-track
status: in-progress
last_updated: 2026-05-02
---

# Epic 4 — Backend & Sync Infrastructure

Server-side and synchronization layer for both survey tracks: **Apps Script + Cloudflare Pages + Cloudflare Worker (JWT proxy)** for the F2 self-admin PWA, and **CSWeb** for the F1/F3/F4 CSPro CAPI track. Covers authentication, data ingestion, storage, and integration ETL between the two tracks.

**Ties to Product Backlog:** [[../product-backlog#Epic 4 — Backend & Sync Infrastructure|PB Epic 4]]
**Methodology:** [[../../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]]

## Task conventions

- `status::` — `todo` / `in-progress` / `done` / `blocked` / `ongoing`
- `priority::` — `critical` / `high` / `medium` / `low`
- `estimate::` — `30m` / `2h` / `1d` / etc. or `recurring`
- Task IDs: `E4-{track}-NNN` where track ∈ `PWA` / `CSWeb` / `INT` (integration)

## Tasks

### F2 PWA Track *(live in production at v1.1.1 codebase + Verde Manual visual identity since 2026-04-26)*

- [x] **E4-PWA-001** Apps Script backend scaffold (router, handlers, schema) `status::done` `priority::critical`
- [x] **E4-PWA-002** Cloudflare Pages staging + production deploy targets configured `status::done` `priority::critical`
- [x] **E4-PWA-003** HMAC-signed request handshake between PWA and Apps Script `status::done` `priority::high`
- [x] **E4-PWA-004** Sync orchestrator (queue, retry, idempotent submit) `status::done` `priority::high`
- [x] **E4-PWA-005** FacilityMasterList provisioning sheet + `?action=facilities` endpoint `status::done` `priority::high`
- [x] **E4-PWA-006** Submission audit log + de-duplication via `client_submission_id` `status::done` `priority::medium`
- [x] **E4-PWA-007** Runtime config endpoint with kill-switch + spec-drift signal `status::done` `priority::medium`
- [x] **E4-PWA-008** Auth re-arch — Cloudflare Worker JWT proxy replaces HMAC-in-bundle (PR #31) `status::done` `priority::critical`
  - Done 2026-04-26. Mitigates CRITICAL finding from 2026-04-25 `/gstack-cso` audit. Worker at `deliverables/F2/PWA/worker/`, deployed to `https://f2-pwa-worker.hcw.workers.dev`. Spec at `docs/superpowers/specs/2026-04-26-f2-pwa-auth-rearch-design.md`. Runbook at `docs/superpowers/runbooks/2026-04-26-f2-auth-cutover.md`.
- [x] **E4-PWA-009** Staging cutover executed (Phase A–E of auth re-arch runbook) `status::done` `priority::critical`
  - Done 2026-04-26 ~17:50 PHT. Worker provisioned (KV + 4 secrets + deploy), HMAC rotated in Apps Script, PR #31 merged to staging, manual `wrangler pages deploy` to staging (auto-deploy didn't fire — see #34), end-to-end smoke test passed (worker → Apps Script `batch-submit` returned 200, spreadsheet row written). Disruption window ~18 min.
- [x] **E4-PWA-012** EnrollmentScreen pre-refresh hot-fix (PR #32) `status::done` `priority::high`
  - Done 2026-04-26. PR #32 deployed manually to staging during cutover smoke test. Auto-seeds facility cache on token verify so users don't hit the catch-22 between Refresh-needs-deviceToken and Enroll-needs-facility-cache.
- [ ] **E4-PWA-013** Phase F — production cutover to Worker JWT proxy `status::blocked` `priority::critical` `estimate::1h`
  - Blocked on: ≥24 hr clean staging soak (earliest start 2026-04-27 ~17:35 PHT) + GitHub #33 (Section F/G multi-select bug) + GitHub #34 (CF Pages auto-deploy regression) resolution.
- [ ] **E4-PWA-014** Investigate Cloudflare Pages auto-deploy regression on **both** `staging` and `main` pushes (GitHub #34) `status::todo` `priority::high` `estimate::2h`
  - Confirmed 2026-04-26 evening that #34 also affects `main` pushes — PR #42 merge to main did not auto-deploy; manual `wrangler pages deploy dist --project-name=f2-pwa --branch=main --commit-hash=a1c4a3ea` was required to ship Verde Manual to production.
  - Phase F blocker if not fixed; otherwise Phase F runbook needs rewrite to make manual `wrangler pages deploy` the documented step for both branches.
  - Likely root cause to try first: disconnect/reconnect the GitHub integration in CF Pages dashboard (Settings → Builds & deployments) to refresh the webhook subscription.
- [ ] **E4-PWA-015** Lower Worker PBKDF2 default to 100k (Workers runtime cap) — GitHub #35 `status::todo` `priority::medium` `estimate::1h`
  - Two-line code change in `worker/scripts/hash-admin-password.mjs` + `worker/src/admin.ts`; add a vitest that documents the cap as test-enforced contract.
- [ ] **E4-PWA-010** Backend secrets rotation policy documented (HMAC, JWT_SIGNING_KEY, Apps Script deploy ID) `status::todo` `priority::medium` `estimate::2h`
- [ ] **E4-PWA-011** Backup + restore runbook for FacilityMasterList + submissions sheets `status::todo` `priority::medium` `estimate::3h`

### CSWeb Track *(not started)*

- [ ] **E4-CSWeb-001** CSWeb server provisioning — host selection, OS, network, TLS `status::todo` `priority::high` `estimate::1d`
- [ ] **E4-CSWeb-002** CSWeb installation + admin account setup `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-CSWeb-003** Per-survey project upload (F1, F3, F4 dictionaries + apps) `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-CSWeb-004** User management — enumerator credentials, role-based access `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-CSWeb-005** Field-tablet sync configuration — endpoint URLs, sync schedule, conflict policy `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-CSWeb-006** Backup strategy for CSWeb data (frequency, retention, restore drill) `status::todo` `priority::medium` `estimate::4h`
- [ ] **E4-CSWeb-007** Monitoring dashboard — sync health, submission counts, field-device status `status::todo` `priority::medium` `estimate::1d`

### F2 Admin Portal Track *(planning complete 2026-05-01 — CSWeb-mirror admin for the F2 PWA stack)*

> Spec: [`docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md`](../../docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md) (v0.2)
> Plan: [`docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md`](../../docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md) (4 sprints, 80 sub-tasks)
>
> Replaces the abandoned M10 plan (single-`ADMIN_SECRET` Apps-Script-HtmlService). Mirrors CSWeb's documented permission model 1:1: 5 dashboards (data/report/apps/users/roles) × 5 IR-aligned roles × 6 per-instrument flags. Adds modest F2 PWA extensions (GPS capture at submission, source_path tagging, paper-encoder workflow, F2_HCWs sheet, versioning endpoint, role-equivalence docs). One tranche, parallel build (admin portal + PWA extensions same sprint window). ~4 weeks at 1-week solo+AI Scrum cadence.

#### Sprint AP1 — foundation (week 1)

- [x] **E4-APRT-001** Wrangler R2 binding + cron trigger configured `status::done` `priority::critical` `estimate::1h`
  - Done 2026-05-02. Top-level production bindings declared in `deliverables/F2/PWA/worker/wrangler.toml` since AP1 (`F2_ADMIN_R2` → `f2-admin`/`f2-admin-preview`, cron `*/5 * * * *`). Staging mirror (`[env.staging]` block) re-enabled today after R2 was turned on for the account; staging worker redeployed with `F2_ADMIN_R2` → `f2-admin-staging`/`f2-admin-staging-preview` and matching cron. All four R2 buckets exist (APAC, Standard). Full upload/list/download/delete smoke green on staging. Prod buckets pre-provisioned; prod worker redeploy deferred to PR #54 cutover.
- [ ] **E4-APRT-002** Apps Script schema migration (5 new sheets + F2_Responses/F2_Audit column extensions) `status::todo` `priority::critical` `estimate::3h`
- [ ] **E4-APRT-003** Worker HMAC + request_id Apps Script client + AS doPost dispatcher (admin_ping round-trip) `status::todo` `priority::critical` `estimate::4h`
- [ ] **E4-APRT-004** Web Crypto PBKDF2 (600k iters) hash + verify + JWT mint/verify with role_version `status::todo` `priority::critical` `estimate::3h`
- [ ] **E4-APRT-005** Two-axis login throttle (per-username + per-IP via KV) `status::todo` `priority::high` `estimate::2h`
- [ ] **E4-APRT-006** RBAC middleware + role_version cache + revoked_jti / revoked_user honor `status::todo` `priority::critical` `estimate::3h`
- [ ] **E4-APRT-007** /admin/api/login + /logout routes wired in Worker; audit log writes `status::todo` `priority::critical` `estimate::3h`
- [ ] **E4-APRT-008** Admin + Standard User built-in roles seeded; 2 Administrators seeded interactively (Carl + ASPSI Director) `status::todo` `priority::critical` `estimate::1h`
- [ ] **E4-APRT-009** Sprint AP1 staging smoke test: login + revoked_jti round-trip end-to-end `status::todo` `priority::high` `estimate::1h`

#### Sprint AP2 — data + report dashboards + PWA GPS (week 2)

- [ ] **E4-APRT-010** Apps Script admin reads (responses/audit/dlq/hcws) with filters + pagination `status::todo` `priority::critical` `estimate::4h`
- [ ] **E4-APRT-011** Worker /admin/api/dashboards/data/* routes (responses, audit, dlq, hcws) gated by dash_data `status::todo` `priority::critical` `estimate::4h`
- [ ] **E4-APRT-012** F2 PWA Geolocation helper + consent disclosure + submit-flow integration `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-APRT-013** Apps Script writes submission_lat/lng + source_path; backfill self_admin on existing rows `status::todo` `priority::high` `estimate::2h`
- [ ] **E4-APRT-014** F2_HCWs sheet wired at enrollment + backfill from F2_Responses+F2_Audit union `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-APRT-015** Apps Script admin_sync_report + admin_map_report (PSGC region/province aggregations) `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-APRT-016** Worker /admin/api/dashboards/report/sync + /map gated by dash_report `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-APRT-017** Frontend admin shell (Login + Layout + AuthContext + role-aware nav) `status::todo` `priority::high` `estimate::1d`
- [ ] **E4-APRT-018** Frontend data dashboard (Responses/Audit/DLQ/HCWs tabs + ResponseDetail + empty states) `status::todo` `priority::high` `estimate::2d`
- [ ] **E4-APRT-019** Frontend SyncReport + MapReport (Leaflet clustering) `status::todo` `priority::high` `estimate::1d`

#### Sprint AP3 — apps + users + roles + cron break-out (week 3)

- [ ] **E4-APRT-020** Apps Script admin_files_* CRUD + R2 upload allowlist (no SVG/HTML/JS, ≤100MB) `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-APRT-021** Apps Script admin_settings_* + admin_settings_run_due (cron break-out builder) `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-APRT-022** Worker scheduled() cron dispatcher (5-min) reading next_run_at; R2 writes `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-APRT-023** Frontend apps dashboard (Versioning + Files + DataSettings + QuotaWidget) `status::todo` `priority::high` `estimate::1d`
- [ ] **E4-APRT-024** Apps Script users CRUD + bulk_create (chunked ≤500) + revoke_sessions `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-APRT-025** Worker users routes + bulk import + revoke-sessions wired to KV `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-APRT-026** Frontend users dashboard (List + Editor + BulkImport CSV preview) `status::todo` `priority::high` `estimate::1d`
- [ ] **E4-APRT-027** Apps Script roles CRUD with version auto-bump; rejects builtin delete `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-APRT-028** Worker roles routes + frontend roles dashboard with checkbox grid `status::todo` `priority::high` `estimate::1d`
- [ ] **E4-APRT-029** PWA versioning endpoint backing data (build SHA injection + Worker /version aggregator) `status::todo` `priority::medium` `estimate::2h`

#### Sprint AP4 — paper-encoder + reissue + cutover + v2.0.0 (week 4)

- [ ] **E4-APRT-030** F2 PWA Form refactored to accept onSubmit prop + mode='hcw'/'encoded' `status::todo` `priority::critical` `estimate::4h`
- [ ] **E4-APRT-031** Apps Script admin_encode_submit + Worker /admin/api/encode/:hcw_id `status::todo` `priority::critical` `estimate::3h`
- [ ] **E4-APRT-032** Frontend EncodeQueue + EncodePage with auto-advance + IndexedDB autosave `status::todo` `priority::critical` `estimate::1d`
- [ ] **E4-APRT-033** Apps Script admin_hcws_reissue_token (CAS via prev_jti); Worker /hcws/:id/reissue-token `status::todo` `priority::critical` `estimate::3h`
- [ ] **E4-APRT-034** Frontend ReissueModal with mono URL + Copy + QR + 409 handling `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-APRT-035** Cross-platform QA pass (Chrome/Firefox/Safari × Win/Mac × desktop/tablet ≥768px) `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-APRT-036** Security testing (throttle / RBAC isolation / HMAC tampering / file-upload XSS vectors) `status::todo` `priority::critical` `estimate::4h`
- [ ] **E4-APRT-037** Concurrency tests (two-admin reissue race / bulk import + role edit / cron + PWA submit) `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-APRT-038** UX gates (Anti-Slop checklist pass / `/design-review` audit / screenshot diff vs F2 PWA / keyboard-only walkthrough recorded) `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-APRT-039** M10 sunset — smoke + 7-day soak + offline backup of ADMIN_PASSWORD_HASH + secret deletion `status::todo` `priority::critical` `estimate::1h`
- [x] **E4-APRT-040** v2.0.0 release — **closed 2026-05-04 (Sprint 004 Day 1)**. Cutover sequence: package.json 1.2.0→2.0.0; CHANGELOG regenerated by postversion hook; 3 commits on f2-admin-portal (UI demo-polish, backend seed, docs/QA); staging→main fast-forward; CF Pages auto-deploy via cf-pages-deploy.yml on both branches; prod Worker deployed (`f2-pwa-worker` at 2.0.0+0f2fb0e); prod AS pushed (Code.gs with FX-006 audit columns + SeedDemo.js staging-guarded); `runAllMigrations()` ran on prod sheet (5 admin sheets created + columns extended); F2_Roles + carl_admin row seeded from staging into prod; tag v2.0.0 pushed; prod Worker `/admin/api/login` returns valid JWT for carl_admin; Versioning panel reports pwa_version=2.0.0 / worker_version=2.0.0+0f2fb0e on prod. Soak gate explicitly waived (Phase F precedent). Cross-platform QA (E4-APRT-035) + ADMIN_PASSWORD_HASH prod sunset deferred. `status::done` `priority::critical` `actual::~90m active (incl. prod sheet seeding)`
- [ ] **E4-APRT-041** Create-HCW UI in Admin Portal — surfaced 2026-05-04 during UAT Round 2 prep. Today HCW provisioning is direct-sheet-append + Reissue-Token flow; for routine ops use the Admin Portal needs a first-class Create HCW form. Location: Data dashboard → HCWs sub-tab → "+ Create HCW" button at top-right. Fields: hcw_id (text, unique), facility_id (dropdown from FacilityMasterList), facility_name (auto-fill), status (default `pending`). Layers: AS new `admin_hcws_create` RPC in AdminHCWs.js (validate + dedupe + append); Worker new POST `/admin/api/hcws` route with RBAC gate (Administrator only); frontend `CreateHCWModal.tsx` + button + handler in HCWsTab.tsx. Ship as v2.0.1 patch. `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-APRT-042** Per-tester admin user accounts on prod — UAT Round 2 testers (Shan, Kidd, +others) currently share `carl_admin`, which collapses audit attribution. Create per-tester rows in prod F2_Users via Admin Portal Users dashboard (or `seed-staging-admin.mjs` invoked against prod env vars). Carry over the staging `data_reader_test` row too. Ship as part of v2.0.1 / Sprint 005 onboarding. `status::todo` `priority::high` `estimate::1h`

### Integration ETL *(not started — feeds Epic 8 monitoring + Epic 10 cleaning)*

- [ ] **E4-INT-001** ETL spec drafted — CSWeb (F1/F3/F4) + F2 PWA backend → unified analysis store `status::todo` `priority::high` `estimate::1d`
- [ ] **E4-INT-002** Looker Studio (or equivalent) dashboard prototype over the unified store `status::todo` `priority::medium` `estimate::1d`
- [ ] **E4-INT-003** Codebook-driven harmonization (per `concepts/aspsi-data-harmonization`) wired into ETL `status::todo` `priority::medium` `estimate::TBD`

## Dependencies

- Epic 5 (Field Distribution) depends on E4-CSWeb-005 for tablet sync configuration.
- Epic 6 (Testing) depends on E4-CSWeb-001..003 for staging environment.
- Epic 8 (Fieldwork Monitoring) depends on E4-INT-001..002 for cross-track visibility.
