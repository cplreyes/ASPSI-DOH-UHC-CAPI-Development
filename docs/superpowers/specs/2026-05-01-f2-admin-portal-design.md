---
title: F2 Admin Portal — CSWeb-Mirror Design Specification
status: draft (v0.2 — review findings incorporated)
date_created: 2026-05-01
last_revised: 2026-05-01
author: Carl Reyes
brainstorm_session: .superpowers/brainstorm/1297-1777612314/
---

# F2 Admin Portal — CSWeb-Mirror Design Specification

> **Status:** v0.2 draft pending user sign-off, then implementation plan generation via `superpowers:writing-plans`.
> **Revision history:** v0.1 (initial) → v0.2 (incorporates parallel eng-review + design-review findings: 8 BLOCKERs, 25 MAJORs, 15 MINORs).

## 1. Executive Summary

This spec defines a CSWeb-equivalent admin portal for the F2 (Healthcare Worker) survey, plus the modest extensions to the existing F2 PWA App needed to support full feature parity with the F1/F3/F4 CSWeb deployment.

**Goal.** Give the project a single, consistent operational backplane: ASPSI's data manager team uses CSWeb for F1/F3/F4 (CSPro CAPI) and a feature-equivalent F2 Admin Portal for F2 (PWA), governed by the same role taxonomy and the same conceptual permission model.

**Driver.** Today F2 has no admin portal; the M10 plan from 2026-04-18 stalled at the AdminHandlers.js scaffold. ASPSI's daily monitoring and weekly QC cadence requires something at parity with CSWeb's `data` / `report` / `apps` / `users` / `roles` dashboards.

**Scope.** Replace the abandoned M10 plan with a Cloudflare Pages + Worker portal that mirrors CSWeb's documented feature surface 1:1, plus 7 modest F2 PWA extensions (GPS capture, source-path tagging, paper-encoder workflow, versioning endpoints, token reissue glue, HCW lookup sheet, role documentation).

**Phasing.** One tranche, parallel build (admin portal + PWA extensions same sprint window). ~4 weeks at the project's 1-week solo+AI Scrum cadence.

**What's explicitly out of scope:** automated alerts (not documented in CSWeb User's Guide), DOH observer access (Carl's scope decision), HCW self-service portal view (data subjects authenticate via JWT to F2 PWA, not the admin portal).

**Design system commitment.** The admin portal binds to the existing F2 PWA's Verde Manual design system. "Mirror CSWeb" applies to features and permissions, not to CSWeb's gov-form aesthetic. See §3.4.

## 2. Background

### 2.1 F2 stack today (post-Phase F, 2026-05-01)

| Layer | Tech | Role |
|---|---|---|
| Frontend | Cloudflare Pages — `f2-pwa.pages.dev` | React PWA, Verde Manual design system, IndexedDB autosave, multi-language (i18n M9), service worker auto-refresh |
| Auth proxy | Cloudflare Worker — `f2-pwa-worker` | Mints + verifies per-HCW JWTs, KV-backed revocation list (`F2_AUTH` namespace), HMAC-signed forwarder to Apps Script |
| Backend | Apps Script Web App | HMAC verification, sheet I/O, reminders, OnSubmit triggers |
| Data store | Google Sheets | `F2_Responses` (submissions), `F2_Audit` (event log), `F2_DLQ` (dead letter queue) |
| Capture paths | Three | (a) PWA self-admin (primary), (b) paper → Forms encoding fallback, (c) optional CSPro CAPI build |

### 2.2 CSWeb's verified permission model

Two permission axes, no others (per [csprousers.org/help/CSWeb](https://www.csprousers.org/help/CSWeb/), ingested 2026-05-01 to `raw/Documentations/CSWeb-help/`):

1. **Dashboard permissions** — five binary checkboxes: `data`, `report`, `apps`, `users`, `roles`.
2. **Dictionary permissions** — per-dictionary up/download (binary, applies across CSEntry / Batch / Data Manager).

Two built-in roles: **Administrator** (full) and **Standard User** (no dashboards, all dictionary up/down via CSEntry; default fallback when a custom role is deleted). Custom roles combine any subset of the two axes (≥1 perm; name immutable).

CSWeb has **no** row-level filtering, **no** time-window perms, **no** alert-config perms, **no** "limited dataset" perms. The CSWeb User's Guide does **not** document an automated alerts feature — earlier project comms about "automated alerts" were aspirational, not built-in.

### 2.3 The IR Fig. 4 organizational chart maps to 5 effective roles

| # | Role label | Org-chart titles | CSWeb permission shape |
|---|---|---|---|
| 1 | Administrator | Project Director, Survey Manager | Full admin |
| 2 | Data Manager | Data Manager, Field Manager, Project Coordinator | Data observer |
| 3 | Monitor | 3× Assistant Data Manager (primary daily users) | Data observer |
| 4 | Operator | 6× Research Associate, 4× Project Assistant | Operator (data only) |
| 5 | Field Supervisor | 20× Field Supervisor | Data observer (regional convention) |

### 2.4 What this spec replaces

The 2026-04-18 M10 plan (`deliverables/F2/PWA/2026-04-18-implementation-plan-M10-admin-dashboard.md`) is **superseded**. Its single-`ADMIN_SECRET` + Apps-Script-HtmlService approach is replaced by per-user accounts + Worker-based RBAC. The pure-function module (`deliverables/F2/PWA/backend/src/AdminHandlers.js`) shipped 2026-04-20 remains useful and is salvaged where applicable (`filterResponses`, CSV serialization).

## 3. Scope

### 3.1 In scope

**F2 Admin Portal (new build):**
- Auth: per-user accounts, password ≥8 chars, two-axis throttle (per-username + per-IP), admin JWT in memory.
- 5 dashboards: `data`, `report`, `apps`, `users`, `roles`, plus a sub-page under `data` for HCW lookup (see §7.14).
- 5 admin roles + built-in Standard User stub (vestigial, documents equivalence).
- Per-instrument permissions across 3 F2 "dictionaries" (`f2_self_admin`, `f2_paper_encoded`, `f2_capi_optional`).
- Sync Report (cases × geography pivot using PSGC value sets); default region-level with target counts.
- Map Report (case-level GPS markers from F2 PWA capture; click → View Case; clustering at low zoom).
- File uploads to R2 (`apps` dashboard) — allowlisted MIME, ≤100 MB, served as attachments.
- Data Settings + scheduled break-out (CSV export to R2 on configurable interval).
- Bulk CSV user import matching CSWeb's exact format.

**F2 PWA App extensions:**
1. GPS capture at submission via Geolocation API.
2. `source_path` column on F2_Responses.
3. Paper-encoder workflow (admin route reuses PWA form component via `onSubmit` prop injection).
4. Versioning endpoints.
5. Token reissue glue (verify EnrollmentScreen handles cleanly).
6. New `F2_HCWs` sheet for HCW lookup.
7. Documentation of Standard User ≡ HCW equivalence.

**Apps Script extensions:**
- New `?action=admin_*` RPCs (auth-gated by Worker HMAC + propagated `request_id`).
- New sheets: `F2_Users`, `F2_Roles`, `F2_FileMeta`, `F2_DataSettings`, `F2_HCWs`.
- Schema migrations: F2_Responses gets `submission_lat`, `submission_lng`, `source_path`, `encoded_by`, `encoded_at`. F2_Audit gets `actor_username`, `actor_jti`, `actor_role`, `event_type`, `event_resource`, `event_payload_json`, `client_ip_hash`, `request_id` (admin context); pre-existing rows have these columns null.
- All admin write RPCs wrapped in `LockService.getDocumentLock().waitLock(30000)`.

### 3.2 Out of scope (explicit, with rationale)

| Item | Why out |
|---|---|
| Automated alerts | Not documented in CSWeb User's Guide; aspirational language in IR. |
| DOH observer / read-only access | Carl's explicit decision (out of comms scope). |
| HCW self-service portal view | HCWs are data subjects, not portal users. |
| Row-level filtering by region | CSWeb's primitives don't support it. |
| Real-time push dashboards | CSWeb doesn't have it; daily monitoring is human-driven. |
| OAuth / Cloudflare Access | Doesn't match CSWeb's username/password UX (1:1 alignment broken). |
| D1 / SQLite cache | Over-engineered at 13K-case scale. |
| Mobile phone (<768px) target | Admin portal is desktop-first with tablet read-only for data + report (see §6.7). |
| Multi-hue heatmaps / chart styling drift | Verde Manual constraint: `--signal` is reserved for primary CTAs/active state, not chart fills. |

### 3.3 Cross-system alignment principles

1. **F2 PWA App ≡ CSEntry** — data collection client.
2. **F2 Admin Portal ≡ CSWeb** — admin/monitoring server.
3. **HCW ≡ CSEntry user with Standard User role** — different credential primitive (JWT vs username/password), equivalent permission shape.
4. **F2 instrument paths ≡ CSWeb dictionaries** — three F2 capture paths get separate per-instrument permission flags.

### 3.4 Design system alignment (binding)

The admin portal **binds to Verde Manual** as defined in `deliverables/F2/PWA/app/DESIGN.md`. Constraints, not suggestions:

1. **No cards / shadows / `rounded-lg`** anywhere. Tables sit on `--paper` with 1px `--hairline` row separators; no zebra striping; no card containers.
2. **JetBrains Mono for all IDs, timestamps, counts, status codes**, hashed values, and any data with structural meaning. Public Sans for body copy. Newsreader for dashboard titles (`text-3xl+`).
3. **`--signal` is reserved** for primary CTAs and active-state indicators — **never** for table headers, table backgrounds, chart fills, or status backgrounds.
4. **Sentence case** for all button labels and headings ("Send new link", not "Send New Link" or "SEND NEW LINK").
5. **Color is never the only signal.** Status uses both color and the literal status word; error rows in DLQ use `--error` text **plus** an "Error" badge.
6. **Anti-Slop checklist applies to admin too** — no decorative chrome, no entrance animations on form fields, no shimmer/pulse on loading states.

UI copy not specified here defaults to the F2 PWA's existing Verde Manual register. See §6.6 for translation register from CSWeb terminology to portal terminology.

## 4. Architecture Overview

### 4.1 System diagram

```
                            ┌──────────────────────────────────────────────┐
                            │  Browser — admin operator (Carl/Kidd/Sean)   │
                            │  React app · Verde Manual tokens · TanStack  │
                            └──────────────────┬───────────────────────────┘
                                               │ HTTPS · admin JWT in mem
                                               ▼
                            ┌──────────────────────────────────────────────┐
                            │   Cloudflare Pages — f2-pwa.pages.dev/admin  │
                            │   (sibling route on existing F2 PWA project) │
                            └──────────────────┬───────────────────────────┘
                                               │ fetch /admin/api/*
                                               ▼
                            ┌──────────────────────────────────────────────┐
                            │   Cloudflare Worker — f2-pwa-worker          │
                            │   ┌───────────┐ ┌───────────┐ ┌───────────┐  │
                            │   │  AuthGate │ │  RBAC     │ │  Cron     │  │
                            │   │  /login   │ │  middleware│ │  dispatcher│  │
                            │   │  PBKDF2   │ │  (req_id) │ │  */5 *    │  │
                            │   │  + JWT    │ │           │ │  reads    │  │
                            │   │  + 2-axis │ │           │ │  next_run │  │
                            │   │  throttle │ │           │ │  _at      │  │
                            │   └─────┬─────┘ └─────┬─────┘ └─────┬─────┘  │
                            └─────────┼─────────────┼─────────────┼────────┘
                                      │             │             │
                  ┌───────────────────┘             │             └──────────┐
                  ▼                                  ▼                        ▼
        ┌──────────────────┐              ┌──────────────────┐    ┌──────────────────┐
        │ KV: F2_AUTH      │              │ Apps Script      │    │ R2: f2-admin     │
        │ (existing)       │              │ ?action=admin_*  │    │                  │
        │                  │              │ HMAC + req_id    │    │ /files/<uuid>   │
        │ + admin JWT jti  │              │ LockService      │    │ /breakout/      │
        │   revocation set │              │   on writes      │    │  YYYY-MM-DD/   │
        │ + per-username   │              │                  │    │   <instrument>/ │
        │   throttle       │              │ readResponses    │    │     responses.csv│
        │ + per-IP throttle│              │ readAudit        │    │     audit.csv    │
        │ + revoked_user   │              │ readDlq          │    │     by-question.csv│
        │   (force-revoke) │              │ users CRUD       │    │                  │
        │ + as_quota count │              │ roles CRUD       │    └──────────────────┘
        └──────────────────┘              │ files CRUD       │
                                          │ settings CRUD    │
                                          └─────────┬────────┘
                                                    │
                                                    ▼
                                          ┌──────────────────────┐
                                          │  Google Sheets       │
                                          │  (source of truth)   │
                                          │                      │
                                          │  F2_Responses *      │
                                          │  F2_Audit *          │
                                          │  F2_DLQ              │
                                          │  F2_Users    (NEW)   │
                                          │  F2_Roles    (NEW)   │
                                          │  F2_FileMeta (NEW)   │
                                          │  F2_DataSettings(NEW)│
                                          │  F2_HCWs     (NEW)   │
                                          │                      │
                                          │  * schema extended   │
                                          └──────────────────────┘
```

### 4.2 Layer responsibilities

| Layer | Tech | Owns |
|---|---|---|
| Frontend | Pages route `/admin` on the existing project; React + TanStack Query; Verde Manual tokens | Login, 5 dashboards, role/user/HCW editors, file upload, Data Settings UI. JWT in memory only. |
| API gateway | Worker (Hono router) | AuthGate (PBKDF2 verify, JWT mint/verify), RBAC middleware (`role_version`-keyed perm cache), file uploads to R2 (allowlisted MIME), single-fixed cron dispatcher reading per-row `next_run_at`, two-axis login throttle, `request_id` propagation. |
| Data RPCs | Apps Script — new `?action=admin_*` branches | All Sheet I/O. HMAC-signed by Worker with `request_id`. All write RPCs wrapped in `LockService.getDocumentLock().waitLock(30000)`. |
| Source of truth | Google Sheets | Existing 3 sheets + 5 new. |
| Blob store | Cloudflare R2 (new bucket `f2-admin`) | Two prefixes: `/files/<uuid>` for admin uploads (Worker-streamed, MIME-allowlisted), `/breakout/YYYY-MM-DD/<instrument>/*.csv` for scheduled exports. |
| Identity | Worker KV (existing `F2_AUTH` namespace) | JWT revocation set; per-username + per-IP throttle counters; `revoked_user:` force-revoke set; `as_quota:` daily-count counters. |

### 4.3 Five non-obvious architectural choices

1. **Worker never touches Sheets directly** — preserves existing data-write contract; all I/O via Apps Script HMAC RPCs.
2. **Admin JWT separate from HCW JWT** — `aud=admin` vs `aud=hcw`; shared revocation set keyed by `jti`.
3. **Frontend holds JWT in memory only** — reload = re-login. Reduces XSS blast radius.
4. **Cron is a single fixed dispatcher** (`*/5 * * * *`) reading per-row `next_run_at` from F2_DataSettings; admins control schedules without redeploys.
5. **R2 path layout is admin-readable** — `/breakout/2026-05-15/f2_self_admin/responses.csv`. Stable patterns let downstream BI consume reliably.

## 5. Data Model

### 5.1 Existing sheet — F2_Responses (schema extended)

| Column | Type | New? | Notes |
|---|---|---|---|
| `submission_id` | string (UUID) | existing | PK |
| `hcw_id` | string | existing | FK to F2_HCWs (will be new) |
| `facility_id` | string | existing | PSGC-derived |
| `submitted_at_server` | ISO 8601 string | existing | server-assigned |
| `submitted_at_client` | ISO 8601 string | existing | client-assigned |
| `status` | enum | existing | `submitted` / `partial` / `error` |
| `values_json` | string | existing | full submission payload |
| `submission_lat` | number\|null | **NEW** | Geolocation API `coords.latitude`; null if denied |
| `submission_lng` | number\|null | **NEW** | Geolocation API `coords.longitude`; null if denied |
| `source_path` | enum | **NEW** | `self_admin` / `paper_encoded` / `capi`; default `self_admin` for backfill |
| `encoded_by` | string\|null | **NEW** | username of admin operator if `source_path=paper_encoded` |
| `encoded_at` | ISO 8601 string\|null | **NEW** | timestamp encoder hit submit |

### 5.2 Existing sheet — F2_Audit (schema extended for admin context)

Existing PWA event columns retained. Adds admin-context columns (NEW); rows pre-extension have these as null.

| Column | Type | New? | Notes |
|---|---|---|---|
| (existing PWA columns) | — | existing | Pre-existing schema for HCW PWA events |
| `actor_username` | string\|null | **NEW** | admin username on admin actions; null for PWA events |
| `actor_jti` | string\|null | **NEW** | JWT `jti` of the actor's session |
| `actor_role` | string\|null | **NEW** | role at time of action |
| `event_type` | string | (clarified) | existing column gains `admin_*` values: `admin_login`, `admin_user_created`, `admin_role_updated`, `admin_token_reissued`, `admin_file_uploaded`, `admin_export_csv`, etc. |
| `event_resource` | string\|null | **NEW** | resource ID acted on (username, role name, hcw_id, file_id, submission_id) |
| `event_payload_json` | string\|null | **NEW** | structured detail; for exports, `{row_count: N}`; for role updates, perms diff |
| `client_ip_hash` | string\|null | **NEW** | sha256 of client IP for privacy-preserving correlation |
| `request_id` | string | **NEW** | UUID propagated from Worker edge through Apps Script |

### 5.3 Existing sheet — F2_DLQ (no schema changes)

Dead letter queue for failed submissions; surfaced read-only on the data dashboard.

### 5.4 NEW — F2_Users

| Column | Type | Required | Notes |
|---|---|---|---|
| `username` | string | yes | PK; alphanumeric + underscore; ≥3 chars |
| `first_name` | string | yes | letters only (CSWeb constraint) |
| `last_name` | string | yes | letters only |
| `role_name` | string | yes | FK to F2_Roles.name |
| `password_hash` | string | yes | format: `<saltB64url>:<iterations>:<hashB64url>` (PBKDF2-SHA256 — see §10.1 for iteration rationale) |
| `password_must_change` | boolean | yes | true on admin-created accounts; cleared after self-changed password (see §7.1.1) |
| `email` | string\|null | optional | |
| `phone` | string\|null | optional | |
| `created_at` | ISO 8601 string | yes | |
| `created_by` | string | yes | username of admin who created (or `system` for first-run seed) |
| `last_login_at` | ISO 8601 string\|null | optional | server-set on successful login |

### 5.5 NEW — F2_Roles

| Column | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | PK; immutable per CSWeb constraint |
| `is_builtin` | boolean | yes | true for Administrator + Standard User (cannot be deleted) |
| `version` | integer | yes | bumped on every PATCH; JWT carries this for cache invalidation (§6.3) |
| `dash_data` | boolean | yes | |
| `dash_report` | boolean | yes | |
| `dash_apps` | boolean | yes | |
| `dash_users` | boolean | yes | |
| `dash_roles` | boolean | yes | |
| `dict_self_admin_up` | boolean | yes | |
| `dict_self_admin_down` | boolean | yes | |
| `dict_paper_encoded_up` | boolean | yes | |
| `dict_paper_encoded_down` | boolean | yes | |
| `dict_capi_up` | boolean | yes | |
| `dict_capi_down` | boolean | yes | |
| `created_at` | ISO 8601 string | yes | |
| `created_by` | string | yes | |

**Constraint:** ≥1 permission must be true (matches CSWeb).

### 5.6 NEW — F2_HCWs

Materialized view of HCW identities; today implicit in F2_Responses + F2_Audit only.

| Column | Type | Required | Notes |
|---|---|---|---|
| `hcw_id` | string | yes | PK; UUID generated at enrollment |
| `facility_id` | string | yes | FK to PSGC value set |
| `facility_name` | string | yes | denormalized for display |
| `enrollment_token_jti` | string | yes | current JWT's `jti` |
| `token_issued_at` | ISO 8601 string | yes | |
| `token_revoked_at` | ISO 8601 string\|null | optional | non-null when reissued |
| `status` | enum | yes | `enrolled` / `submitted` / `revoked` |
| `created_at` | ISO 8601 string | yes | |

### 5.7 NEW — F2_FileMeta

| Column | Type | Required | Notes |
|---|---|---|---|
| `file_id` | string (UUID) | yes | PK; matches R2 path `/files/<file_id>` |
| `filename` | string | yes | display name |
| `content_type` | string | yes | MIME, allowlisted (§7.9) |
| `size_bytes` | number | yes | ≤100 MB |
| `uploaded_by` | string | yes | admin username |
| `uploaded_at` | ISO 8601 string | yes | |
| `description` | string\|null | optional | admin-supplied note |
| `deleted_at` | ISO 8601 string\|null | optional | soft delete |

### 5.8 NEW — F2_DataSettings

| Column | Type | Required | Notes |
|---|---|---|---|
| `setting_id` | string (UUID) | yes | PK |
| `instrument` | enum | yes | `f2_self_admin` / `f2_paper_encoded` / `f2_capi_optional` |
| `included_columns` | JSON array | yes | which F2_Responses columns to export |
| `interval_minutes` | enum | yes | `5` / `15` / `60` / `360` / `1440` (replaces ad-hoc cron expressions) |
| `next_run_at` | ISO 8601 string | yes | computed by Worker after each successful run |
| `output_path_template` | string | yes | default `/breakout/{YYYY-MM-DD}/{instrument}/responses.csv` |
| `last_run_at` | ISO 8601 string\|null | optional | |
| `last_run_status` | enum\|null | optional | `success` / `error` / `running` |
| `last_run_error` | string\|null | optional | |
| `enabled` | boolean | yes | |
| `created_by` | string | yes | |
| `created_at` | ISO 8601 string | yes | |

### 5.9 R2 path layout (bucket: `f2-admin`)

```
/files/<file_id>                                        — admin-uploaded files
/breakout/<YYYY-MM-DD>/<instrument>/responses.csv       — scheduled break-out per instrument
/breakout/<YYYY-MM-DD>/<instrument>/audit.csv           — paired audit context
/breakout/<YYYY-MM-DD>/<instrument>/by-question.csv     — pivoted long-format
```

### 5.10 KV namespace `F2_AUTH` (existing, extended)

| Key pattern | Value | Purpose |
|---|---|---|
| `revoked_jti:<jti>` | timestamp | JWT revocation set (HCW + admin); TTL = remaining `exp` + 60s |
| `revoked_user:<username>:<since_iso>` | `1` | Force-revoke all sessions for a user where `iat < since` |
| `throttle:login:user:<username>:<window_start>` | counter | Per-user login throttle (10 / 15 min) |
| `throttle:login:ip:<ip_hash>:<window_start>` | counter | Per-IP login throttle (50 / 15 min) |
| `as_quota:<YYYY-MM-DD>` | counter | Daily Apps Script call count for budget enforcement |

## 6. API Contracts

### 6.1 Worker routes — admin

All routes prefixed `/admin/api/`. JSON request/response except CSV exports. Admin JWT required except `/login`. Every route emits a `request_id` (UUID) propagated to Apps Script and audit log; surfaced via `X-Request-Id` response header.

| Method | Path | Body | Returns | Permission |
|---|---|---|---|---|
| POST | `/login` | `{ username, password }` | `{ token, role, role_version, expires_at, password_must_change }` | (none — public) |
| POST | `/logout` | — | 204; adds `jti` to revocation KV | any authenticated |
| GET | `/me` | — | `{ username, role, perms, password_must_change }` | any authenticated |
| POST | `/me/change-password` | `{ old, new }` | 204; clears `password_must_change` | any authenticated |
| GET | `/dashboards/data/responses` | `from`, `to`, `facility_id`, `status`, `source_path`, `q`, `limit`, `offset` | `{ rows, total, has_more }` | `dash_data` |
| GET | `/dashboards/data/responses/:id` | — | `{ submission, sections }` (sectioned per PWA form) | `dash_data` |
| GET | `/dashboards/data/audit` | filters | `{ rows, total, has_more }` | `dash_data` |
| GET | `/dashboards/data/dlq` | filters | `{ rows, total, has_more }` | `dash_data` |
| GET | `/dashboards/data/hcws` | filters | `{ rows, total, has_more }` | `dash_data` (see §7.14) |
| GET | `/dashboards/data/hcws/:hcw_id` | — | `{ hcw, recent_submissions }` | `dash_data` |
| GET | `/dashboards/data/export.csv` | filters + `instrument` | streaming CSV | `dash_data` AND `dict_<instrument>_down` |
| POST | `/dashboards/data/export.csv/preflight` | filters + `instrument` | `{ row_count, would_succeed }` | `dash_data` AND `dict_<instrument>_down` |
| POST | `/hcws/:hcw_id/reissue-token` | `{ prev_jti }` (CAS precondition) | `{ new_token, new_url, old_jti }` | `dash_users` (Administrator only — see §7.5) |
| GET | `/dashboards/report/sync` | `from`, `to`, `level` (region/province/facility), `instrument` | `{ pivot_table, totals }` | `dash_report` |
| GET | `/dashboards/report/map` | `from`, `to`, `instrument`, `region_id`, `province_id` | `{ markers, no_gps_count }` | `dash_report` |
| GET | `/dashboards/apps/version` | — | `{ pwa_version, pwa_build_sha, worker_secret_version, form_revisions, last_pages_deploy_at }` | `dash_apps` |
| POST | `/dashboards/apps/files` | multipart: file (≤100 MB, allowlisted MIME) | `{ file_id, url }` | `dash_apps` |
| GET | `/dashboards/apps/files` | — | `{ files }` | `dash_apps` |
| DELETE | `/dashboards/apps/files/:id` | — | 204 (soft delete) | `dash_apps` |
| GET | `/dashboards/apps/files/:id/download` | — | streaming binary with `Content-Disposition: attachment` | `dash_apps` |
| GET | `/dashboards/apps/data-settings` | — | `{ settings }` | `dash_apps` |
| POST | `/dashboards/apps/data-settings` | full record | `{ setting }` | `dash_apps` |
| PATCH | `/dashboards/apps/data-settings/:id` | partial | `{ setting }` | `dash_apps` |
| DELETE | `/dashboards/apps/data-settings/:id` | — | 204 | `dash_apps` |
| POST | `/dashboards/apps/data-settings/:id/run-now` | — | 202; sets `next_run_at = now` (rejects if `running`) | `dash_apps` |
| GET | `/dashboards/apps/quota` | — | `{ apps_script_calls_today, budget, percent }` | `dash_apps` |
| GET | `/dashboards/users` | — | `{ users }` | `dash_users` |
| POST | `/dashboards/users` | full record | `{ user }` | `dash_users` |
| PATCH | `/dashboards/users/:username` | partial | `{ user }` | `dash_users` |
| DELETE | `/dashboards/users/:username` | — | 204 | `dash_users` |
| POST | `/dashboards/users/:username/revoke-sessions` | — | 204; writes `revoked_user:` to KV | `dash_users` |
| POST | `/dashboards/users/import` | multipart: CSV | `{ created, errors }` | `dash_users` |
| GET | `/dashboards/roles` | — | `{ roles }` | `dash_roles` |
| POST | `/dashboards/roles` | full record | `{ role }` | `dash_roles` |
| PATCH | `/dashboards/roles/:name` | partial perms (bumps `version`) | `{ role }` | `dash_roles` |
| DELETE | `/dashboards/roles/:name` | — | 204 (rejects `is_builtin=true`) | `dash_roles` |
| POST | `/encode/:hcw_id` | full submission | `{ submission_id }` | `dict_paper_encoded_up` |
| GET | `/encode/queue` | filters (facility, region, status) | `{ hcws_pending }` | `dict_paper_encoded_up` |
| GET | `/jobs/:id` | — | `{ status, progress, result_url }` | varies — only for owner of the job |

### 6.2 Apps Script RPCs (HMAC-protected, called by Worker only)

All RPCs accept `{ action, payload, ts, request_id, hmac }`. HMAC signed with `APPS_SCRIPT_HMAC` (existing secret) over `${action}.${ts}.${request_id}.${stable_json_payload}`.

Apps Script logs every call with its `request_id` and writes to F2_Audit when applicable.

| Action | Payload | Returns | Lock? |
|---|---|---|---|
| `admin_read_responses` | filters | `{ rows, total }` | no (read) |
| `admin_count_responses` | filters | `{ total }` | no |
| `admin_read_audit` | filters | `{ rows, total }` | no |
| `admin_read_dlq` | filters | `{ rows, total }` | no |
| `admin_read_response_by_id` | `{ id }` | `{ submission }` | no |
| `admin_users_list` | — | `{ users }` | no |
| `admin_users_create` | user | `{ user }` | yes |
| `admin_users_update` | partial | `{ user }` | yes |
| `admin_users_delete` | `{ username }` | `{ ok }` | yes |
| `admin_users_bulk_create` | rows ≤500 per call | `{ created, errors }` | yes |
| `admin_roles_list` | — | `{ roles }` | no |
| `admin_roles_create` | role | `{ role }` | yes |
| `admin_roles_update` | partial (auto-bumps `version`) | `{ role }` | yes |
| `admin_roles_delete` | `{ name }` | `{ ok }` | yes |
| `admin_files_list` | — | `{ files }` | no |
| `admin_files_create` | metadata | `{ file }` | yes |
| `admin_files_delete` | `{ file_id }` | `{ ok }` | yes |
| `admin_settings_list` | — | `{ settings }` | no |
| `admin_settings_upsert` | setting | `{ setting }` | yes |
| `admin_settings_run_due` | — | `{ ran: [setting_ids], errors }` | yes (per-row) |
| `admin_hcws_lookup` | `{ hcw_id }` | `{ hcw }` | no |
| `admin_hcws_list` | filters | `{ hcws }` | no |
| `admin_hcws_reissue_token` | `{ hcw_id, prev_jti, new_jti, issued_at }` | `{ ok, current_jti }` (CAS-checked) | yes |
| `admin_form_revisions` | — | `{ revisions }` | no (5-min cache) |
| `admin_sync_report` | filters | `{ pivot, totals }` | no |
| `admin_map_report` | filters | `{ markers, no_gps_count }` | no |

### 6.2.1 Concurrency model

- **All write RPCs** (table marked "yes" above) wrap their sheet I/O in `LockService.getDocumentLock().waitLock(30000)`. Lock release is in a `finally` block.
- **Bulk imports** (`admin_users_bulk_create`) chunk in batches of ≤500 rows; Worker pages the import across multiple RPCs to stay well under Apps Script's 6-min execution limit.
- **Concurrent reissues on the same HCW** are CAS-checked: `admin_hcws_reissue_token` accepts `prev_jti`; if F2_HCWs row's current `enrollment_token_jti != prev_jti`, returns `E_CONFLICT` (HTTP 409) and Worker surfaces "another administrator just reissued — refresh and try again."
- **Lock timeouts** return `E_LOCK_TIMEOUT` (HTTP 503) with `Retry-After: 5`.
- **Cron break-out** acquires the lock per-row (one F2_DataSettings row at a time) so it never blocks user-facing writes.

### 6.3 Admin JWT structure

```json
{
  "iss": "f2-pwa-worker",
  "aud": "admin",
  "sub": "<username>",
  "role": "<role_name>",
  "role_version": 7,
  "iat": 1740096000,
  "exp": 1740110400,
  "jti": "<uuid>"
}
```

- `role_version` carries F2_Roles.version at login. Worker RBAC middleware caches `(role, version) → perms` in Worker memory (LRU, ~50 entries, 1h TTL).
- On role PATCH, F2_Roles.version is bumped. Worker RBAC compares JWT's `role_version` against cached current version on each request; if stale, returns `E_AUTH_EXPIRED` with `reason=role_changed` so the client redirects to login.
- `revoked_user:<username>:<since>` set in KV invalidates all sessions where `iat < since` regardless of `jti` — used for force-revoke.
- `exp` = 4 hours after `iat`.
- HS256 signed with `JWT_SIGNING_KEY` (existing secret; admin uses same secret as HCW with separate `aud` claim).

### 6.5 Dashboard layouts (wireframes)

All layouts use Verde Manual constraints from §3.4. Top nav splits into two zones: **Operations** (Data, Reports — primary) and **Configuration** (Files & Settings, Users, Roles — right-side dropdown). User menu in top-right corner with Change password, Sign out, About.

#### data dashboard

```
┌──────────────────────────────────────────────────────────────────────────┐
│ F2 Admin     Data ●  Reports        Configuration ▾    User: kidd_g ▾   │
├──────────────────────────────────────────────────────────────────────────┤
│ Submissions   Audit   DLQ   HCWs                                         │
│                                                                          │
│ [Last 24h] [Last 7d] [All time]    Filters: facility ▾  status ▾  +     │
│                                                                          │
│ Showing 1-50 of 2,847   [error: 12]  ◄ Show only errors                  │
│                                                                          │
│ submission_id   hcw_id    facility_name        submitted_at   status     │
│ ─────────────── ───────── ───────────────────  ──────────────  ────────── │
│ 04f9-…-3a2b     hcw_142   Bislig City RHU      2026-05-01 18:32  ✓ subm  │
│ 1b2e-…-cc01     hcw_088   Pasay GH             2026-05-01 17:15  ✗ error │
│ ...                                                                      │
│                                                                          │
│ [Export CSV ▾]                                       [⟵] [⟶] Page 1/57   │
└──────────────────────────────────────────────────────────────────────────┘
```

- 1px `--hairline` row separators; no zebra striping.
- IDs in JetBrains Mono.
- Status uses both color (`--success` / `--error`) and the literal status word.
- "Show only errors" pill toggles a filter; URL is shareable.
- Export CSV dropdown lists permitted instruments only.

#### report dashboard

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Sync Report   Map Report                                                 │
│                                                                          │
│ Level: ●Region ○Province ○Facility    Instrument: All ▾   [Last 7d ▾]   │
│                                                                          │
│ Region                       Expected  Submitted   %       Last activity │
│ ───────────────────────────  ─────────  ─────────  ────    ────────────  │
│ NCR                              1,840        623   34%    2 hours ago   │
│ CAR                                612         98   16%    11 hours ago  │
│ Region I (Ilocos)                  925        512   55%    1 hour ago    │
│ ...                                                                      │
│ TOTALS                          12,876      6,143   48%                  │
│                                                                          │
│ [Export pivot CSV]                                                       │
└──────────────────────────────────────────────────────────────────────────┘
```

Map Report tab: full-width Leaflet map, sidebar list of regions with submission counts (clickable to zoom), date-range filter shared with data dashboard via URL params, marker clustering at zoom <12, "X cases without GPS — view list" link.

#### apps dashboard

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Versioning                                                               │
│   PWA: v1.3.0 (build abc1234)  Last deploy: 2026-05-01 08:00 UTC         │
│   Worker secret: v3-2026-04-30                                           │
│   Form revisions: en rev_xxx   fil rev_yyy   ...                         │
│                                                                          │
│ Files (5)                                                                │
│   training-manual-2026.pdf    23 MB   uploaded 2026-04-28 by carl    🗑  │
│   ...                                                                    │
│   [Upload new file]                                                      │
│                                                                          │
│ Scheduled exports                                                        │
│   f2_self_admin    every 60 min   last: success 17:00   [Run now]        │
│   f2_paper_encoded every 60 min   last: success 17:00   [Run now]        │
│   ...                                                                    │
│                                                                          │
│ Apps Script quota today: 7,238 / 20,000 (36%)  [last reset: midnight UTC]│
└──────────────────────────────────────────────────────────────────────────┘
```

#### users dashboard

Single table; row actions Edit / Delete / Revoke sessions. "Add user" + "Bulk import" buttons top-right. Role column links to roles dashboard filtered to that role.

#### roles dashboard

Single list of roles. Click role → opens editor with checkbox grid for perms. Built-in roles (Administrator, Standard User) show as read-only. "Add role" button top-right.

### 6.6 UI copy register (CSWeb terminology → portal terminology)

User-facing copy uses portal terminology. URL paths and DB columns retain technical names.

| CSWeb / technical term | Portal copy |
|---|---|
| Dashboards (in nav) | Section names alone (Data, Reports) — never "Dashboard" |
| Dictionaries | Survey forms |
| Reissue token | Send new link to HCW |
| Run now | Generate now |
| Break-out CSV | Scheduled export |
| DLQ | Failed submissions |
| Audit log | Activity log |
| Permissions | Access |
| HCW | Healthcare worker |
| Sync Report | Submission progress |
| Map Report | Submission map |

All button labels use sentence case ("Send new link", not "Send New Link"). Filipino translations for the 10 highest-frequency labels deferred to v2.1 (out of scope for the initial 4-week tranche).

### 6.7 Responsive scope

Desktop-first; tablet (≥768px) is supported read-only for data + report dashboards. Mobile phone (<768px) is not a target.

| Dashboard | Desktop | Tablet (≥768px) | Mobile (<768px) |
|---|---|---|---|
| data | full | read-only, list-detail | not supported |
| report (Sync) | full | read-only, h-scroll on pivot | not supported |
| report (Map) | full | full | not supported |
| apps | full | not supported | not supported |
| users | full | not supported | not supported |
| roles | full | not supported | not supported |
| encode | full | not supported | not supported |

Reuse the F2 PWA's existing breakpoint tokens.

## 7. Use Case Specifications

### 7.0 Daily ADM monitoring (the 80% flow)

**Actor:** Monitor (ADM) — the highest-frequency operator.

**Goal:** "Has anything broken since yesterday? What's our submission rate today?"

**Flow:**
1. Open `/admin` → log in.
2. Land on `/admin/data` with default filter `submitted_at_server >= now - 24h`, sort newest first.
3. Glance at top-right error-count badge in nav (e.g., "12" in `--error`). If non-zero, click "Show only errors" pill.
4. Filter by facility or status as needed. URL is shareable for Slack handoff.
5. Switch to `/admin/report` → Sync Report defaults to region-level pacing vs target.
6. Total time: ~2 minutes. No data entry, all reading.

**Defaults documented:** Last-24h filter, newest-first sort, error-count nav badge, persistent "Last 24h / Last 7d / All time" pill, shareable URL.

### 7.0.1 Empty / loading / error states

| Surface | Empty | Loading | Error |
|---|---|---|---|
| data dashboard | "No submissions yet in this date range. Try widening to All time, or check enrollment status [link to HCWs]." | Hairline-divided skeleton rows (no shimmer/pulse) | Inline banner: "Could not load submissions. Try again." [Retry button] + small mono error code |
| Sync Report | "No data for the selected filters." | Skeleton pivot | Banner with retry |
| Map Report | "No submissions with GPS yet. X cases without GPS — view list [link]." | Map renders with loading overlay | Banner with retry |
| Apps dashboard | (versioning always populated; files may be empty) "No files uploaded yet. [Upload new file]" | Hairline skeleton | Banner |
| Users / Roles | (always at least seeded built-ins) | Hairline skeleton | Banner |
| Encode queue | "No HCWs awaiting encoding for these filters." | Hairline skeleton | Banner |
| DLQ | "No failed submissions. ✓" | Skeleton | Banner |

### 7.1 Login

**Actor:** any Admin User.
**Preconditions:** valid username + password; not currently locked out.

**Flow:**
1. User enters credentials on `/admin/login`.
2. Frontend POSTs `/admin/api/login`.
3. Worker checks two-axis throttle: per-username (10 attempts / 15 min) AND per-IP (50 / 15 min). If either exceeded → 429 with `Retry-After`.
4. Worker calls Apps Script `admin_users_list`, finds user, retrieves `password_hash` + `password_must_change`.
5. Worker performs PBKDF2 verify; if fail, increments BOTH throttle counters, returns 401.
6. Worker calls `admin_roles_list`, finds role, mints JWT with `role` + `role_version`.
7. Worker returns `{ token, role, role_version, expires_at, password_must_change }`.
8. Frontend stores JWT in memory; if `password_must_change=true`, redirects to `/admin/me/change-password` (forced); otherwise lands on the role's default landing (§8.5).
9. Apps Script async-updates `last_login_at`; F2_Audit row written with `event_type=admin_login`.

### 7.1.1 First login (forced password change)

**Actor:** any user with `password_must_change=true` (admin-created accounts).

**Flow:**
1. After successful login, frontend forces redirect to `/admin/me/change-password`.
2. User enters old (admin-set) password + new password ≥8 chars + confirmation.
3. Worker verifies old password, hashes new, calls `admin_users_update` clearing `password_must_change`.
4. Frontend redirects to "What you can do here" panel: one-screen list of permitted dashboards in plain-language ("Browse submissions" not "Data dashboard access"). Dismissible with "Don't show again" checkbox stored in F2_Users (or simply session-local).
5. Then proceeds to default landing (§8.5).

### 7.2 Browse submissions (data dashboard)

**Actor:** any user with `dash_data`.

**Flow:** GET `/admin/api/dashboards/data/responses` with default filters (last 24h, newest first); render virtualized table; filters in URL (shareable).

### 7.3 View case detail

**Actor:** any user with `dash_data`.

**Flow:** GET `/admin/api/dashboards/data/responses/:id`. Server returns `{submission, sections}` where `sections` mirrors the F2 PWA form section structure. Frontend renders sections (Newsreader title per section, hairline divider between, label/value pairs with mono for IDs/timestamps).

### 7.4 Download CSV (per-instrument-permitted)

**Actor:** user with `dash_data` AND `dict_<instrument>_down`.

**Flow:**
1. User clicks Export CSV; frontend selects instrument from dropdown (filtered to user's permitted instruments).
2. Frontend POSTs `/admin/api/dashboards/data/export.csv/preflight` with filters + instrument.
3. Worker calls `admin_count_responses`; if count > 100,000 → returns 413 + `E_EXPORT_TOO_LARGE` with the actual row count. Frontend shows modal "Result is X rows; please tighten filters to ≤100,000 rows."
4. If ≤100,000, frontend GETs `/admin/api/dashboards/data/export.csv` with same params.
5. Worker pages Apps Script `admin_read_responses` in 5,000-row chunks; streams CSV through `TransformStream`.
6. Response sets `Content-Disposition: attachment; filename="f2-<instrument>-<YYYY-MM-DD>.csv"`.
7. F2_Audit row written with `event_type=admin_export_csv`, `event_payload_json={row_count: N, instrument}`.

### 7.5 Reissue HCW token

**Actor:** Administrator only (`dash_users` perm).

**Rationale:** Earlier drafts assumed Operator/Monitor/Data Manager could reissue "own queue" tokens, but CSWeb's permission model has no row-level enforcement (see §8.4). Reissuing is identity management, parallel to user-account management; the honest mapping gates it on `dash_users`. Field staff who need a reissue request it from an Administrator out-of-band.

**Worker-orchestrated flow (pinned):**
1. Administrator locates HCW via `/admin/data/hcws` or directly on a submission row's "Reissue token" action.
2. Frontend POSTs `/admin/api/hcws/:hcw_id/reissue-token` with `{ prev_jti }` (last-seen JWT `jti` for CAS).
3. Worker generates `new_jti` and `new_token`.
4. Worker calls Apps Script `admin_hcws_reissue_token` with `{ hcw_id, prev_jti, new_jti, issued_at }`. Apps Script under LockService: if `F2_HCWs.enrollment_token_jti == prev_jti`, atomic update + return success; else return `E_CONFLICT` (HTTP 409 surfaces to user).
5. On Apps Script ACK: Worker writes `revoked_jti:<old_jti>` to KV with TTL = remaining `exp` of old token + 60s.
6. On Apps Script failure post-mint: Worker writes `revoked_jti:<new_jti>` to roll forward (better to invalidate the unsynced new token than leave both live). F2_Audit row written either way.
7. Worker returns `{ new_token, new_url, old_jti }` to frontend.

**UX (modal):**
- Title: "Send new link for HCW {first} {last}"
- Body: new URL in a mono code block with single Copy button (visible feedback: "Copied" badge appears for 2s); QR code rendered client-side from URL; plain-language instructions in English ("Send this link to the HCW. The previous link will stop working immediately.").
- Modal can be re-opened from the HCW row for 10 minutes; after that, must reissue again (security).
- Audit log entry visible immediately in `data → audit` tab.

### 7.6 Configure Data Settings (break-out)

**Actor:** user with `dash_apps`.

**Flow:** UI on apps dashboard. CRUD over F2_DataSettings sheet. "Generate now" sets `next_run_at = now`; if `last_run_status=running` AND `last_run_at < 6 minutes ago`, returns 409 ("run already in progress"); otherwise force-clears `running` flag (assume stuck) and proceeds.

### 7.7 View Sync Report

**Actor:** user with `dash_report`.

**Default:** `level=region`, last 7 days. Columns: Region, Expected (from PSGC sample frame), Submitted, % complete, Days since last submission. Each cell hyperlinks to data dashboard filtered to that region. Top-right CSV export.

### 7.8 View Map Report

**Actor:** user with `dash_report`.

**Flow + UX:**
- Initial map bounds = Philippines national.
- Sidebar list of regions with submission counts (clickable → zoom to region's PSGC bbox).
- Marker clustering at zoom <12 (Leaflet.markercluster). 13K markers without clustering would lock the page.
- Click marker → inline popover with `hcw_id`, facility name, submitted_at, "View full case" CTA navigating to `/admin/data/responses/:id`.
- Date-range filter shared with data dashboard via URL params.
- Marker color: `--signal` only (no multi-hue heatmaps — Verde Manual constraint).
- Cases without GPS shown as count badge: "X cases without GPS — view list" linking to data dashboard with `submission_lat IS NULL` filter.

### 7.9 Upload file (apps dashboard)

**Actor:** user with `dash_apps`.

**Flow:**
1. User selects file on apps dashboard.
2. Frontend POSTs multipart to `/admin/api/dashboards/apps/files` (Worker streams to R2; pre-signed URLs not used — they would bypass MIME check).
3. Worker enforces: `Content-Length ≤ 100 MB`; allowlisted MIME types only (`application/pdf`, `application/zip`, `application/octet-stream`, `image/png`, `image/jpeg`, `image/gif`); reject `text/html`, `application/javascript`, `image/svg+xml` (SVG XSS vector).
4. Worker writes blob to R2 at `/files/<file_id>`; calls `admin_files_create` for metadata.
5. Downloads via `/admin/api/dashboards/apps/files/:id/download` always serve `Content-Disposition: attachment` (never inline render).

### 7.10 Add user (single)

**Actor:** user with `dash_users`.

**Flow:**
1. UI presents form matching CSWeb fields.
2. POST `/admin/api/dashboards/users` with full record.
3. Worker validates: name letters-only, username uniqueness, password ≥8 chars, role exists.
4. Worker hashes password (PBKDF2-SHA256 — see §10.1 for iter count rationale); sets `password_must_change=true`.
5. Worker calls `admin_users_create`.

### 7.11 Bulk import users (CSV)

**Actor:** user with `dash_users`.

**Flow:**
1. UI accepts CSV upload; matches CSWeb format exactly: `username, first name, last name, user role, password, email, phone`.
2. POST multipart to `/admin/api/dashboards/users/import`.
3. Worker parses CSV, validates each row, hashes passwords, batches Apps Script writes via `admin_users_bulk_create` in chunks of ≤500 rows.
4. Returns `{ created: N, errors: [{ row_num, message }] }` for partial-success display.

### 7.12 Add / Edit / Delete role

**Actor:** user with `dash_roles`.

Standard CRUD; checkbox grid editor (5 dashboard checkboxes + 6 dictionary checkboxes). Edit auto-bumps `version` (invalidates active sessions on next request). Delete rejects `is_builtin=true`.

### 7.13 Encode paper form (Operator daily flow)

**Actor:** Operator (or any user with `dict_paper_encoded_up`).

**Worklist flow:**
1. User navigates to `/admin/encode/queue` — list of HCWs filtered by "enrolled, no submission yet"; can pin filter (facility, region) so it persists across encodes.
2. Click HCW → loads form at `/admin/encode/:hcw_id`.
3. Form component is the PWA form, reused via `onSubmit` prop injection: caller passes a function that POSTs to `/admin/api/encode/:hcw_id` (admin JWT in Authorization header), not the existing PWA submit endpoint.
4. Form component receives `mode='encoded'` prop; hides HCW-only "thank you" copy; shows "Encoding for: {hcw name}" header.
5. IndexedDB autosave preserves draft across session expiry; on re-login, draft is restored.
6. On submit, Worker stamps `source_path=paper_encoded`, `encoded_by=<username>`, `encoded_at=<now>`; writes via `admin_users_*` (wrong — fix: writes via existing PWA submission write path with admin metadata; routed through Apps Script with HMAC).
7. Success toast: "Encoded for {hcw_name}. Next: {next_hcw_name}" with "Open next" CTA. Auto-advance optional (Operator can disable in settings).

**Form component contract (from §9.3):** the F2 PWA form is refactored to accept `onSubmit: (payload) => Promise<{submission_id}>` prop. The PWA caller passes its existing HCW-JWT submit fn; the admin caller passes the admin-JWT-flavored fn pointing at `/admin/api/encode/:hcw_id`.

### 7.14 HCW search and lookup

**Actor:** any user with `dash_data`.

**Flow:** `/admin/data/hcws` — sub-page on data dashboard listing F2_HCWs entries. Columns: hcw_id (mono), facility_name, status (enrolled/submitted/revoked), enrollment_date, last_activity. Row actions: "View submission" (deep-link to data filtered to that HCW); "Reissue token" (visible to Administrator only — gated on `dash_users`).

## 8. Permission Model

### 8.1 Default perm matrix (5 roles × dashboards)

| Role | data | report | apps | users | roles |
|---|---|---|---|---|---|
| Administrator | ✓ | ✓ | ✓ | ✓ | ✓ |
| Data Manager | ✓ | ✓ | ✗ | ✗ | ✗ |
| Monitor | ✓ | ✓ | ✗ | ✗ | ✗ |
| Operator | ✓ | ✗ | ✗ | ✗ | ✗ |
| Field Supervisor | ✓ | ✓ | ✗ | ✗ | ✗ |

### 8.2 Default perm matrix (5 roles × dictionaries)

| Role | self_admin up | self_admin down | paper_encoded up | paper_encoded down | capi up | capi down |
|---|---|---|---|---|---|---|
| Administrator | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Data Manager | ✗ | ✓ | ✗ | ✓ | ✗ | ✓ |
| Monitor | ✗ | ✓ | ✗ | ✓ | ✗ | ✓ |
| Operator | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ |
| Field Supervisor | ✗ | ✓ | ✗ | ✓ | ✗ | ✓ |

### 8.3 Standard User (built-in, vestigial)

All checkboxes false. Documents the equivalence "F2 PWA App ≡ CSEntry; HCWs map to CSWeb's Standard User role with JWT credential primitive instead of username/password." Cannot be deleted.

### 8.4 Permission enforcement points

1. **Worker route handler** — every route declares required perm(s); middleware decodes JWT, checks `(role, role_version)` against cached perms, gates accordingly.
2. **Apps Script RPC** — every action validates the calling Worker's HMAC + propagated `request_id`; trusts Worker's perm decision (no double-check).
3. **Frontend** — UI **hides** controls the user lacks perm for (does not disable). Server is authoritative.
4. **R2 / file URLs** — `apps` dashboard files are not directly addressable; downloads go through Worker which checks perm.

### 8.5 Default landing per role

After successful login (and after any forced password change), users land on:

| Role | Default landing |
|---|---|
| Administrator | `/admin/data?range=24h` |
| Data Manager | `/admin/data?range=24h` |
| Monitor | `/admin/data?range=24h` |
| Field Supervisor | `/admin/data?range=24h` |
| Operator | `/admin/encode/queue` if user has `dict_paper_encoded_up`; else `/admin/data?range=24h` |
| Custom role with no dashboard perms but `dict_*_up` | `/admin/encode/queue` if encoder perm; else fallback |
| Custom role with no dashboard or encoder perms | "No permissions assigned" landing screen with `/admin/me` and Sign out only |

Deep-links via `?return=<url>` after session-expiry redirect resume the user where they were.

## 9. F2 PWA Extensions (detailed)

### 9.1 GPS capture at submission

**Files:** `app/src/api/submit.ts`, `app/src/EnrollmentScreen.tsx`, consent screen.

**Design:**
- `getGeolocation()` helper returns `Promise<{lat, lng} | null>`. 5-second timeout; returns null on deny / timeout.
- Called at moment of submit, before POST.
- Disclosure on consent screen + tooltip near submit button — i18n in 5 supported languages.
- No background tracking; one-shot at submit.

### 9.2 source_path tagging

Worker submit handler tags `source_path` (`self_admin` for PWA path, `paper_encoded` for admin encoder path, `capi` for future). Existing rows backfilled to `self_admin`.

### 9.3 Paper-encoder workflow

**Files:** `app/src/Form.tsx` (refactor to accept `onSubmit` prop), new `admin/EncodePage.tsx`.

**Design:**
- Form component extracted to accept `onSubmit: (payload) => Promise<{submission_id}>` and `mode: 'hcw' | 'encoded'` props.
- PWA caller passes existing HCW-JWT submit fn; admin caller passes admin-JWT fn POSTing to `/admin/api/encode/:hcw_id`.
- Encoder sees worklist, picks HCW, fills form, submits, auto-advances.

### 9.4 Versioning endpoints

**Files:** Worker `GET /admin/api/dashboards/apps/version`; Apps Script `admin_form_revisions`; PWA build embeds `version.ts` exposing build SHA.

### 9.5 Token reissue glue

**Files:** `app/src/EnrollmentScreen.tsx` (verify reissued token works on first navigate — PR #53 should already cover; add unit test); Worker route uses existing JWT mint code with new `jti`.

### 9.6 F2_HCWs sheet + lookup

**Files:** Apps Script `admin_hcws_*`; existing enrollment flow updated to write F2_HCWs row when minting a new HCW JWT; one-time backfill from F2_Responses + F2_Audit union at deploy.

### 9.7 Standard User documentation

**Files:** `deliverables/F2/PWA/app/CLAUDE.md` — add note about role equivalence; this spec §3.3.

## 10. Security Model

### 10.1 Threat model

| # | Threat | Mitigation |
|---|---|---|
| 1 | Credential brute force | Two-axis throttle (per-username 10/15min, per-IP 50/15min); PBKDF2-SHA256 with iterations chosen per below |
| 2 | Session hijack | JWT in memory only; HTTPS-only; 4h expiry; `aud=admin` claim binding |
| 3 | Permission escalation post-demotion | `role_version` invalidates JWTs on role change; `revoked_user:` set for force-revoke |
| 4 | CSRF | JWT in `Authorization` header (not cookie); CORS limited to admin origin |
| 5 | Stored XSS via uploaded files | MIME allowlist (no SVG, no HTML, no JS); `Content-Disposition: attachment` always |
| 6 | Reflected XSS in admin UI | React auto-escaping; user-supplied content rendered via React's default text path or `textContent`; DOMPurify dep included for any future rich-text fields |
| 7 | Data exfiltration via export | Both `dash_data` AND per-instrument `dict_*_down` checked; F2_Audit row written with row count |
| 8 | Token reissue race | CAS-style `prev_jti` precondition in Apps Script |
| 9 | M10 sunset disaster | Backed-up `ADMIN_PASSWORD_HASH` offline; 7-day post-cutover wait (§13.3 step 5) |

**PBKDF2 iteration choice:** OWASP 2023+ recommends ≥600k for PBKDF2-SHA256. Web Crypto `crypto.subtle.deriveBits` is native and runs ~600k in <100ms even in V8 isolates — fits the Worker CPU budget. **Choice: 600k iterations using Web Crypto.** Rationale documented in F2_Users `password_hash` format spec (§5.4).

### 10.2 Secret inventory

| Secret | Where | Rotation |
|---|---|---|
| `JWT_SIGNING_KEY` | Worker (existing) | Quarterly; rotation forces re-login |
| `APPS_SCRIPT_HMAC` | Worker + Apps Script (existing) | Quarterly, coordinated |
| `ADMIN_PASSWORD_HASH` (M10 single-secret) | Worker (existing) | **Removed at cutover + 7d**; backed up offline |
| Per-user `password_hash` | Apps Script F2_Users | User-driven (change-password) or admin-driven |
| `R2_ACCESS_KEY` | Worker | Quarterly |

### 10.3 Audit logging

Every admin action emits a row to F2_Audit with `event_type=admin_*` and the actor + JWT `jti` + `request_id`. Schema is in §5.2. Includes login/logout, user CRUD, role CRUD, token reissue, file upload/delete, Data Settings change, break-out trigger, CSV export (with row count).

### 10.4 Admin portal accessibility

- All table data text uses `--ink` (not `--muted`) for readability; mono labels in headers may use `--muted`.
- Keyboard nav: `j/k` for table row nav, `enter` to open detail, `esc` to close modals, `/` to focus filter input.
- Screen reader: tables have `<th scope>` headers; status icons have `aria-label`.
- Focus-visible 2px `--signal` outline (matches PWA).
- Color is never the only signal — error rows in DLQ use `--error` text plus an "Error" badge; status pills use both color and the literal status word.

## 11. Error Handling

### 11.1 Error catalog

| Code | HTTP | Where | Meaning |
|---|---|---|---|
| `E_AUTH_INVALID` | 401 | Worker | Login failed; both throttle counters incremented |
| `E_AUTH_LOCKED` | 429 | Worker | Per-username OR per-IP throttle exceeded |
| `E_AUTH_EXPIRED` | 401 | Worker | JWT expired, revoked, or `role_version` stale |
| `E_PERM_DENIED` | 403 | Worker | JWT lacks required perm |
| `E_VALIDATION` | 400 | Worker | Body validation; field-level details |
| `E_NOT_FOUND` | 404 | Worker / AS | Resource missing |
| `E_CONFLICT` | 409 | Worker / AS | Username taken; role name taken; CAS reissue conflict; "run already in progress" |
| `E_LOCK_TIMEOUT` | 503 | AS | LockService.waitLock timeout; client retry advised |
| `E_RATE_LIMIT` | 429 | Worker | Apps Script daily quota ≥80%; `Retry-After` to midnight UTC |
| `E_BACKEND` | 502 | Worker | Apps Script error/timeout |
| `E_HMAC_INVALID` | (internal) | AS | Worker→AS HMAC failed; logged; caller sees 502 |
| `E_EXPORT_TOO_LARGE` | 413 | Worker | CSV export > 100k rows |

### 11.2 Retry policy

- Worker → Apps Script: 3 retries with exponential backoff (200ms, 800ms, 3.2s) on 502.
- UI shows subtle "Retrying…" indicator after 1.5s of pending state. Buttons go disabled (not hidden) during retry. Final failure surfaces error toast with the actual error code (small mono).
- Cron break-out: on partial-write failure, leaves status=`error` + error message; next run retries.
- R2 writes: 3 retries; on final fail, log to F2_Audit + surface in apps dashboard with red badge.

### 11.3 Observability

- Worker emits `request_id` at edge; included in all log lines, HMAC payload to AS, `X-Request-Id` response header, F2_Audit row.
- Cloudflare Worker observability (existing) shows error rates.
- F2_Audit shows admin action audit.
- New: admin-portal apps dashboard widget shows last cron break-out status + Apps Script daily quota usage.

### 11.4 Long-running operations + error display contract

**Long-running (≥5s):**
Before any operation expected to take >5s (CSV export, bulk import, run-now break-out), Worker checks `exp - now > 60s`. If insufficient time, frontend silently re-prompts login or redirects to `/admin/login?return=<current-url>&reason=session-expired`. Streaming responses use `Content-Disposition: attachment` so partial download lands on disk.

**Session-expiry preserve:** `?return=<url>` always preserved across login redirect.

**Error UX:**

| Error code | UI |
|---|---|
| `E_AUTH_EXPIRED` / `E_AUTH_LOCKED` | Full-page redirect to login with reason |
| `E_PERM_DENIED` on navigation | Page-level banner: "You don't have permission to view this. Contact your Administrator." (role name shown) |
| `E_PERM_DENIED` on button click | Should not happen — buttons are hidden when perm absent (server still enforces) |
| `E_VALIDATION` | Field-level inline error with `--error` token |
| `E_BACKEND` / `E_RATE_LIMIT` | Toast: "Something went wrong on the server. Try again in a few seconds." [Retry] + small mono error code |
| `E_EXPORT_TOO_LARGE` | Modal with actual row count + filter narrowing suggestions |
| `E_CONFLICT` (reissue) | Toast: "Another administrator just reissued this token. Refresh and try again." |
| `E_LOCK_TIMEOUT` | Toast: "The system is busy. Try again in a few seconds." [Retry] |

## 12. Testing Strategy

### 12.1 Unit tests (Vitest)

Coverage target: 90% on pure logic.

- `worker/src/auth.ts` — Web Crypto PBKDF2 hash/verify, JWT mint/verify with role_version, two-axis throttle.
- `worker/src/rbac.ts` — perm check given role + route requirement; force-revoke handling.
- `worker/src/csv-stream.ts` — RFC 4180 escaping (salvaged from `AdminHandlers.js`); chunk paging.
- `worker/src/sync-report.ts` — pivot generation; region/province/facility levels.
- `worker/src/data-settings.ts` — `next_run_at` calc per `interval_minutes`; due-row selection.
- `worker/src/file-upload.ts` — MIME allowlist; size cap; SVG/HTML/JS rejection.
- `apps-script/admin_*.js` — schema validation; lock acquisition error path.

### 12.2 Integration tests

- Worker ↔ Apps Script HMAC + request_id round-trip in local emulator (or against a staging Apps Script deployment).
- Login flow end-to-end with seeded F2_Users.
- CSV export with 1k synthetic rows → verify content + filters.
- CSV export with 90k synthetic rows → verify streaming + Content-Disposition + completion.
- CSV preflight with 150k matching rows → verify 413 returned.

### 12.3 E2E tests (Playwright)

For each of the 5 dashboards: smoke test (login → navigate → render expected element). For paper-encoder: full submission round-trip with auto-advance. For map report: render without GPS data; render with 100 synthetic markers + clustering.

### 12.4 Cross-platform QA

Reuse existing F2 PWA cross-platform QA checklist; add admin portal entries (Chrome/Firefox/Safari × Win/Mac × desktop/tablet ≥768px).

### 12.5 Security testing

- Login throttle: scripted brute force on one username should hit 429 within ~11 attempts; per-IP test confirms NAT-coexistence.
- Permission isolation: each role's JWT used against routes it lacks perm for; expect 403 every time.
- HMAC tampering: malformed Worker→AS request rejected and logged.
- CSV export with disabled `dict_*_down` perm: expect 403.
- File upload with `image/svg+xml`, `text/html`, `application/javascript`: expect 400.
- File upload >100 MB: expect 413.

### 12.6 Concurrency & race tests

- Two admins reissuing same HCW concurrently: one succeeds with new `jti`, other gets 409 `E_CONFLICT`.
- Bulk CSV import (1k rows) running while admin edits a role: both complete; no corruption; lock contention surfaces no `E_LOCK_TIMEOUT` under normal load.
- Cron break-out running while HCW submits via PWA: both complete; no corruption.
- Worker→Apps Script timeout mid-write: F2_Audit shows partial; retry resolves; no double-write.

## 13. Deployment

### 13.1 Topology

| Environment | URL | Trigger |
|---|---|---|
| Local | `localhost:8787` Worker, `localhost:5173` Pages | dev script |
| Staging | `f2-pwa-staging.pages.dev` + `f2-pwa-worker-staging.workers.dev` | push to `staging` |
| Production | `f2-pwa.pages.dev` + `f2-pwa-worker.workers.dev` | merge `staging` → `main` |

### 13.2 Secret management

- Worker secrets: `wrangler secret put` per env.
- Apps Script Properties: `setupBackend()` script seeds + rotates.
- KV (`F2_AUTH`): existing namespace; no new bindings.
- R2 bucket (`f2-admin`): create per env via wrangler.

### 13.3 Migrations (ordered)

1. **Sheets schema add** (non-destructive): F2_Responses gets new columns; F2_Audit gets admin-context columns; create new sheets (Users/Roles/HCWs/FileMeta/DataSettings).
2. **Backfill**: F2_Responses rows get `source_path='self_admin'`; F2_HCWs populated from F2_Responses + F2_Audit union.
3. **Seed two Administrators**: interactive script writes F2_Users with Carl + 1 ASPSI Project Director nominee as Administrators (passwords prompted; both set `password_must_change=false` for these initial accounts since the prompter chose the password).
4. **Seed built-in roles**: script writes Administrator + Standard User to F2_Roles with `is_builtin=true`, `version=1`.
4.5. **Smoke test new login**: Carl logs in via new portal, performs each dashboard load, verifies F2_Audit captured events, exports a small CSV, reissues a test HCW token.
5. **Sunset M10**: `ADMIN_PASSWORD_HASH` Worker secret value backed up offline (1Password / sealed envelope) BEFORE any further action. Wait **7 days post-cutover** with new portal in production. Then delete the secret.

### 13.4 Rollback

- Frontend: revert deploy on Pages.
- Worker: revert deploy.
- Schema: column adds are non-breaking; rows can stay.
- Admin auth disaster: re-add `ADMIN_PASSWORD_HASH` from offline backup (§13.3 step 5) and revert routes.

### 13.5 Release process

- Per existing F2 PWA release-notes workflow (CHANGELOG + version bump).
- Lands as v2.0.0 (major bump justified by dual-portal architecture: HCW contract back-compat but project surface-area scope doubles).

## 14. Operational Runbook

### 14.1 Daily monitoring (Monitor / ADM)

- Login → data dashboard. Default: last 24h, newest first. Glance at error-count badge.
- "Show only errors" → investigate.
- Sync Report tab: confirm submission rate aligns with expected enrollment rate.
- Map Report tab: spot-check geographic distribution.

### 14.2 Weekly QC

A "Weekly QC" sub-tab on data dashboard pre-fills filters: (a) submissions with `status=error` last 7d, (b) admin actions in last 7d filtered to user/role CRUD, (c) cron break-out failures last 7d, (d) HCWs reissued last 7d. Each section shows count + "Review" link.

### 14.3 Common issues

| Issue | Likely cause | Resolution |
|---|---|---|
| Login fails for known user | Password forgotten or wrong; throttle | Administrator resets password OR waits out throttle |
| Token reissue link doesn't work | KV propagation delay (<60s) | Wait + retry |
| Map Report missing markers | HCWs declined geolocation | Check GPS-null count in data dashboard |
| Break-out CSV stale | Cron failed | Apps dashboard widget shows error; click "Generate now" or fix Apps Script error |
| CSV export blocked | Per-instrument download perm missing | Administrator updates role |
| Apps Script quota near limit | Heavy admin polling | Worker reduces cache TTL aggressively; alert in apps dashboard widget |

### 14.4 Rotation cadences

- `JWT_SIGNING_KEY`: quarterly. Forces re-login.
- `APPS_SCRIPT_HMAC`: quarterly, coordinated.
- Per-user passwords: optional, encouraged annually.

### 14.5 Escalation paths

- Cloudflare Worker outage: Cloudflare status page; failover not in scope (4h SLA acceptable).
- Apps Script quota exceeded: increase Google Workspace quota OR throttle admin export concurrency.
- Sheets corruption: restore from Drive version history; F2_Audit allows reconstruction.

## 15. Open Questions / Risks

### 15.1 Open questions

| # | Question | Default if unanswered |
|---|---|---|
| OQ1 | "Remember me" / longer session? | No — match CSWeb 4h reset |
| OQ2 | Apps dashboard quota: total vs admin-attributable? | Admin-attributable only |
| OQ3 | `admin_form_revisions` live or 5-min cache? | Cache 5 min |
| OQ4 | Break-out supports "all instruments" combined CSV? | Per-instrument only |
| OQ5 | Encoder partial saves / autosave? | Yes — same component, IndexedDB autosave |
| OQ6 | Filipino translations for portal copy in v2.0? | Out of scope for 4-week tranche; v2.1+ |

### 15.2 Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Apps Script daily quota (Workspace ~20K calls/day) under heavy polling | Quantitative budget: 5 admins × 5 dashboards × (8h × 3600 / 60s cache) ≈ 12K calls/day with 60s TTL → fits within 80% budget. Worker tracks `as_quota:<date>` in KV; returns `E_RATE_LIMIT` at 80% |
| R2 | Sheets row growth | At 13K cases × ~50 cols + 5 new sheets ≈ ~700K cells — well under 10M Sheets limit. Monitor at 70% |
| R3 | Cron break-out misses runs during CF outages | Retry policy + apps dashboard widget surfaces failures |
| R4 | HCW privacy concern over GPS | Disclosure in consent flow; deny is silent (matches CSWeb) |
| R5 | Schema drift Worker ↔ Apps Script | Shared zod schema; CI enforces |
| R6 | M10 `AdminHandlers.js` salvage hidden assumptions | Code review during integration; rewrite if needed |
| R7 | Operator queue UX assumes encoders work serially | Worklist filter is pinned per-Operator; auto-advance is opt-out |

## 16. Acceptance Criteria

### 16.1 Definition of done — per use case

1. Worker route exists with handler + RBAC middleware + tests.
2. Apps Script RPC exists with HMAC + LockService + tests.
3. Frontend component exists with i18n strings (English-only acceptable for admin chrome; embedded PWA form retains 5-language support per §9.3) + render test.
4. End-to-end happy path tested manually.
5. Permission-denied case tested manually.
6. Audit log entry visible in F2_Audit with correct actor + request_id.
7. CHANGELOG entry written.

### 16.2 Definition of done — milestone

- All 14 use cases (§7) pass acceptance.
- All 7 PWA extensions (§9) merged.
- All sheets seeded (§13.3).
- Cross-platform QA pass (§12.4).
- Security tests pass (§12.5).
- Concurrency tests pass (§12.6).
- Operational runbook (§14) reviewed by Carl.
- M10 `ADMIN_PASSWORD_HASH` removed (§13.3 step 5; +7d gate).
- v2.0.0 published with release notes.
- **UX gates:**
  - Anti-Slop checklist (`DESIGN.md`) passes for every admin screen.
  - `/design-review` skill audit pass with Carl sign-off.
  - Screenshot diff vs F2 PWA: same paper background, same hairline rules, same Newsreader/Public Sans/Mono triad.
  - Keyboard-only walkthrough of daily ADM flow recorded.

### 16.3 Quality gates

- 90%+ test coverage on Worker logic.
- All Worker routes return correct status codes per error catalog.
- No `console.log` / debug code in production build.
- No hardcoded secrets; all via wrangler secrets.
- CHANGELOG entries for every milestone.

## 17. Implementation Order (preview — full plan in writing-plans output)

Sprints at 1-week cadence (parallel α phasing):

**Sprint 1 — foundation**
- Sheet schema migrations (additive only) + F2_Audit admin-context columns.
- F2_Users + F2_Roles seeded with Administrator + Standard User.
- Worker `/admin/api/login` + Web Crypto PBKDF2 + JWT with role_version + two-axis throttle.
- RBAC middleware with `(role, role_version) → perms` cache.
- Apps Script LockService wrapper + HMAC + request_id.
- F2 PWA: `source_path` column wired; backfill migration.

**Sprint 2 — dashboards: data + report + HCW lookup**
- Data dashboard (Submissions / Audit / DLQ / HCWs sub-tabs) frontend + Worker + AS RPCs.
- Report dashboard (Sync + Map with clustering).
- F2 PWA: GPS capture + consent disclosure.
- F2 PWA: F2_HCWs sheet + lookup endpoints.

**Sprint 3 — dashboards: apps + users + roles + cron**
- Apps dashboard (versioning, file uploads with MIME allowlist, Data Settings UI, quota widget).
- Users dashboard (CRUD + bulk CSV in 500-row chunks + force-revoke-sessions).
- Roles dashboard (CRUD + checkbox grid + version bump).
- Cron dispatcher reading `next_run_at`; per-row break-out; R2 writes.
- F2 PWA: versioning endpoints.

**Sprint 4 — paper-encoder + polish + cutover**
- Paper-encoder workflow (queue, form-onSubmit injection, auto-advance).
- Token reissue (CAS + modal with QR).
- Empty/loading/error states across dashboards.
- Cross-platform QA pass (desktop + tablet read-only).
- Security + concurrency testing.
- M10 sunset gate (smoke test → 7d wait → secret deletion).
- v2.0.0 release.

---

**Document version:** 0.2 — review-incorporated draft.

**Next steps:** user sign-off; transition to `superpowers:writing-plans` for implementation plan generation.
