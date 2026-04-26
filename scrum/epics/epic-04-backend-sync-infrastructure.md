---
epic: 4
title: Backend & Sync Infrastructure
phase: per-track
status: in-progress
last_updated: 2026-04-26
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

### Integration ETL *(not started — feeds Epic 8 monitoring + Epic 10 cleaning)*

- [ ] **E4-INT-001** ETL spec drafted — CSWeb (F1/F3/F4) + F2 PWA backend → unified analysis store `status::todo` `priority::high` `estimate::1d`
- [ ] **E4-INT-002** Looker Studio (or equivalent) dashboard prototype over the unified store `status::todo` `priority::medium` `estimate::1d`
- [ ] **E4-INT-003** Codebook-driven harmonization (per `concepts/aspsi-data-harmonization`) wired into ETL `status::todo` `priority::medium` `estimate::TBD`

## Dependencies

- Epic 5 (Field Distribution) depends on E4-CSWeb-005 for tablet sync configuration.
- Epic 6 (Testing) depends on E4-CSWeb-001..003 for staging environment.
- Epic 8 (Fieldwork Monitoring) depends on E4-INT-001..002 for cross-track visibility.
