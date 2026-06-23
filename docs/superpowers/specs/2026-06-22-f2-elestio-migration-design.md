---
title: F2 Survey + Admin Portal — Migration to Elestio (full re-platform off Cloudflare/Google)
status: approved (v0.2 — open items resolved; ready for implementation plan)
date_created: 2026-06-22
last_revised: 2026-06-22
author: Carl Reyes
---

> **v0.2 (2026-06-22):** §12 open items resolved — subdomain `hcw.asiansocial.org`; single Docker Compose stack (not managed-DB service); Node runtime; cost approved.

# F2 Survey + Admin Portal — Elestio Migration Design

> **Status:** v0.1 draft pending user sign-off, then implementation plan generation via `superpowers:writing-plans`.
> **Brainstorm decisions locked (2026-06-22):** full re-platform · dedicated Elestio service · MySQL (mirror CSWeb conventions) · clean-slate cutover.

## 1. Executive Summary

Move the entire F2 (Healthcare Worker survey) stack — the PWA frontend, the Cloudflare Worker, and the Google Sheets / Apps Script data store — off Cloudflare and Google onto a **dedicated Elestio instance** under ASPSI control, mirroring the existing CSWeb deployment posture.

**Goal.** A self-hosted F2 stack that can carry real fieldwork load and stops depending on free-tier Cloudflare limits and Google consumer quotas.

**Driver.** The current path is `PWA (CF Pages) → Worker (CF) → Apps Script → Google Sheet`. Under the intended HCW load the **data layer is the binding constraint**: Google Sheets serializes writes and Apps Script caps at ~30 simultaneous executions with a 6-minute runtime, so a burst of concurrent self-administered submissions queues, times out, and piles into the dead-letter queue. The Cloudflare Worker free tier (100k req/day, KV/R2 caps) is a secondary ceiling. The survey has not yet gone to real field load, so **now is the clean window to re-platform** before data is at stake.

**Scope.** Full re-platform: static PWA on Elestio nginx + a Node/Hono API (the Worker, ported) + MySQL (replacing Sheets) + a disk volume for file uploads (replacing R2) + node-cron for scheduled break-outs (replacing the Worker cron). The Worker→Apps-Script HMAC hop is **deleted** — the API writes straight to MySQL.

**Out of scope.** No data migration (clean slate — see §7). No change to the PWA's survey content/spec, screens, or the Verde Manual design system. No change to F1/F3/F4 or the CSWeb box. No horizontal scaling / load balancers (single right-sized instance + connection pooling is sufficient at this scale).

## 2. Background

### 2.1 F2 stack today

| Layer | Tech | Role |
|---|---|---|
| Frontend | Cloudflare Pages — `f2-pwa.pages.dev` | Vite + React + TS + Tailwind + shadcn PWA; Verde Manual; IndexedDB autosave; i18n; service-worker auto-refresh |
| Edge API | Cloudflare Worker — `f2-pwa-worker` | JWT mint/verify; HMAC-signed forwarder to Apps Script; `F2_AUTH` KV (revocation + audit); `F2_ADMIN_R2` bucket (admin uploads + breakout CSVs); `*/5` cron (scheduled break-outs). Web Crypto + `nodejs_compat`. Source: `worker/src/{index,exec,hmac,jwt,verify,types}.ts` + `worker/src/admin/`. |
| Backend | Google Apps Script web app (`/exec`) | HMAC verification, idempotent RPCs, sheet I/O, admin actions. Source: `backend/src/*.js` + `backend/apps-script/*.js`. |
| Data store | Google Sheet | `F2_Responses`, `F2_Audit`, `F2_DLQ`, `F2_HCWs`, admin users/roles |

Request path: **PWA → Worker → Apps Script → Google Sheet.**

### 2.2 Intended scale (grounds the sizing)

- **~12,000–15,000 HCW respondents total.** Year 1 (IDinsight) = 11,582 HCWs across 1,135 facilities; Year 2 = **1,521 sampled facilities** at **4–53 HCWs/facility (≤53 ceiling)**.
- **1,521 facilities · 6 clusters · ~100 enumerators / 20 field supervisors**, over a ~3–4 month conduct window (Months 4–7, or the proposed Aug-train / Sep-rollout shift).
- **Average load is light** (~150–250 submissions/day). **Peak concurrency is the design driver**: F2 is self-administered, so HCWs fill the form in bursts when a field team works a facility (a 53-HCW facility group session ≈ ~50 concurrent on one site; several clusters at once → plan for **~300–500 concurrent** headroom with spiky submissions).
- The dataset is *tiny* by DB standards (~15k JSON-blob rows + some admin uploads); the engineering job is **handling burst concurrency**, not data volume.

### 2.3 Why this fixes the problem

A MySQL-backed API handles hundreds of concurrent short writes trivially (proper transactional concurrency + connection pooling), removing both the Sheets write-serialization bottleneck and the Apps Script execution cap. Cloudflare free-tier ceilings disappear because the instance's CPU/RAM is ours to size.

## 3. Target Architecture

```
                 hcw.asiansocial.org   (Elestio managed nginx + auto-SSL; DNS via ASPSI)
                          │
   ┌──────────────────────┴───────────────────────────────────┐
   │  Dedicated Elestio service — 2 vCPU / 4 GB RAM            │
   │                                                            │
   │   nginx ──► static PWA (dist/)        [was CF Pages]       │
   │     │                                                      │
   │     └── /api/* ──► Node/Hono API      [was the Worker]     │
   │                      │                                      │
   │                      ├─ MySQL (InnoDB, utf8mb4)  [was Sheets]   │
   │                      ├─ /data/uploads volume      [was R2]      │
   │                      └─ node-cron (break-outs)    [was CF cron] │
   └────────────────────────────────────────────────────────────┘

   CSWeb box (csweb.asiansocial.org) — UNTOUCHED, separate instance.
```

**Key property:** PWA and API are same-origin → **no CORS**, and there is no cross-service hop. Everything F2 lives on one isolated instance whose load can never threaten the live CSWeb monitoring hub.

**Instance sizing.** 2 vCPU / 4 GB RAM, 20–40 GB disk. Carries several × the realistic peak; Elestio resize is a slider if real fieldwork proves heavier. (Contrast the CSWeb box's ~1.7 GB free headroom — the reason for isolation.)

**Deployment shape (resolved v0.2).** A **single Docker Compose stack** on the Elestio instance — nginx + Node API + MySQL together — mirroring how the CSWeb box is deployed (Docker stack with its own MySQL). App↔DB on localhost (simplest, lowest-latency, fewest moving parts). MySQL mirrors the CSWeb box conventions (InnoDB, `utf8mb4`/`utf8mb4_unicode_ci`). Backups: a **`mysqldump` cron** (matching CSWeb's practice) in addition to Elestio volume snapshots, so the data store has DB-native dumps, not only full-VM snapshots. (A separate Elestio managed-MySQL service was considered and rejected for now — operational parity with CSWeb + a single unit to manage outweigh hands-off DB patching at this scale.)

## 4. Component Design

### 4.1 Static PWA hosting (was Cloudflare Pages)

- The PWA build output (`app/dist/`) is served by Elestio nginx as static files with SPA fallback (`try_files … /index.html`).
- Service-worker `registerType: 'prompt'` and cache headers preserved; existing installs get the standard "Update available" prompt.
- **Only frontend change:** the API base URL. Today the app calls the cross-origin Worker URL; after migration it calls **same-origin `/api`** (a single env var, e.g. `VITE_API_BASE`). No screen, spec, or design-system change.

### 4.2 API service — Node + Hono (the Worker, ported)

- **Why Hono:** the Worker already uses Fetch-style handlers + Web Crypto. Hono runs that same handler code on Node with a near-direct port, and can still target Workers — so the port is low-risk and reversible.
- **Ports as-is:** `jwt.ts` (mint/verify; Web Crypto → `node:crypto` webcrypto or `jose`), `verify.ts`, request validation, the route surface (the 6 PWA RPCs + admin actions).
- **Deleted entirely:** `exec.ts`, `hmac.ts`, and the admin-HMAC envelope in `index.ts` — the Worker→Apps-Script signing layer has no reason to exist once the API owns its own database. This is a net simplification.
- **New:** a thin data-access layer (repository functions) over MySQL, replacing the Apps Script RPC client. Each former RPC (`submit`, admin `users/roles/files/breakout/reports/...`) becomes an API route backed by a SQL transaction.
- **Connection pooling:** a small app-side pool (10–20 connections, e.g. `mysql2/promise` pool) so a submission burst cannot exhaust DB connections. Requests are short; no ProxySQL needed.

### 4.3 Data layer — MySQL (was Google Sheets)

CSWeb-style conventions: InnoDB, `utf8mb4`, surrogate `BIGINT` PKs, `created_at`/`updated_at`. Proposed tables (refined at plan time):

| Table | Replaces | Purpose |
|---|---|---|
| `hcw_responses` | `F2_Responses` | One row per submission: `case_id` (12-digit QN), `facility_id`, `status` (completed/partial), `payload` (JSON), `lang`, `source_path` (pwa/paper), `submitted_at`, `idempotency_key` (unique) |
| `hcws` | `F2_HCWs` | Enrollment roster: `token_hash`, `facility_id`, `case_seq`, `status`, `issued_at`, `used_at` |
| `admin_users` | sheet | `username`, `password_hash`, `role_id`, `must_change_password`, `last_login_at` |
| `roles` | sheet | Role defs + per-dashboard / per-instrument permission flags (mirrors the CSWeb 5-dashboard model the Admin Portal already implements) |
| `audit_log` | `F2_Audit` | Event log (`request_id`, actor, action, ts, detail) |
| `revoked_tokens` | `F2_AUTH` KV | JWT revocation list + TTL cleanup |
| `idempotency_keys` | `Idempotency.js` | Request dedup (unique key + first-result cache) |
| `data_settings` | breakout config | `next_run_at` rows the cron scans for scheduled break-out CSV writes |
| `files` | R2 metadata | Upload metadata + on-disk path |

- The survey response stays a **JSON document** (`payload`) — same shape the PWA already submits — plus relational columns for the dimensions that need indexed querying (facility, status, date, source). This keeps parity with the current Sheet rows while making concurrent writes safe and queries fast.
- The **DLQ shrinks in importance**: with a transactional DB the write either commits or returns a real error to retry; a small `dlq` table can be retained for belt-and-suspenders.

### 4.4 Object storage — disk volume (was R2)

- Admin file uploads + scheduled break-out CSVs write to a mounted **`/data/uploads`** volume; `files` table holds metadata; the API streams downloads with auth checks.
- Elestio snapshots the volume on its backup cadence. MinIO (S3-compatible) is **not** introduced now — YAGNI at this file volume; revisit only if true object semantics are later needed.

### 4.5 Scheduled break-outs — node-cron (was Worker cron)

- The `*/5 * * * *` Worker trigger becomes a `node-cron` job (or an Elestio scheduled task) inside the API that scans `data_settings` for `next_run_at <= now` and writes break-out CSVs to `/data/uploads`. Same dispatch logic, different scheduler.

### 4.6 Auth model

- **HCW session JWTs unchanged** — mint/verify ports directly; enrollment-token flow preserved.
- **Admin auth unchanged** in behavior (username/password → session), now reading `admin_users`/`roles` from MySQL instead of the sheet.
- The **HMAC trust boundary between Worker and Apps Script is removed** — there is no second service to sign to. Server-side authorization (role checks) moves into the API middleware.

## 5. Cloudflare/Google → Elestio mapping (summary)

| Today | Becomes |
|---|---|
| PWA on CF Pages | static `dist/` on Elestio nginx |
| Worker (`f2-pwa-worker`) | Node/Hono API (`/api`) |
| Worker→Apps-Script HMAC | **deleted** |
| Apps Script + Google Sheet | MySQL |
| `F2_AUTH` KV | `revoked_tokens` + `audit_log` tables |
| `F2_ADMIN_R2` bucket | `/data/uploads` volume + `files` table |
| Worker `*/5` cron | node-cron job |
| CF Pages bandwidth + Worker 100k/day | instance CPU/RAM (ours to size) |

## 6. Security Considerations

- **TLS:** Elestio managed nginx auto-SSL on `hcw.asiansocial.org` (same mechanism as CSWeb; DNS via ASPSI).
- **Secrets:** `JWT_SIGNING_KEY` regenerated for the new instance; DB credentials in Elestio env/secret store, never in the bundle. (The existing build-time secret checks `check-bundle-secrets.mjs` still run.)
- **Isolation:** dedicated instance means an F2 compromise or load spike cannot reach the CSWeb box.
- **Authorization:** role checks enforced server-side in API middleware (parity with the Admin Portal's RBAC model), not relying on the removed HMAC hop.
- **Backups:** Elestio scheduled DB + volume snapshots; retention matched to the CSWeb box policy.
- **PII:** F2 holds HCW responses — same data-privacy posture as today; the move to a single ASPSI-controlled instance arguably tightens custody vs. Google Sheets.

## 7. Data at Cutover — Clean Slate

- **Migrate nothing.** Current survey responses are throwaway UAT/dev data.
- **Re-seed** admin users + roles on the new MySQL (a seed script mirroring the current role taxonomy).
- **Re-mint** HCW enrollment tokens on the new system (the PWA enrollment flow + Admin Portal token issuance).
- No ETL, no dual-write window, no consistency risk.

## 8. Cutover & Rollback Plan

1. **Build** the Elestio service (nginx + API + MySQL) in parallel with the live Cloudflare stack. No production impact.
2. **Validate** on the raw Elestio URL: golden-path enrollment → sections → submit; admin login + RBAC; file upload/download; scheduled break-out; burst-concurrency smoke test.
3. **Re-seed** admin/roles + **re-mint** tokens.
4. **Flip DNS** `hcw.asiansocial.org` → Elestio once green. Cloudflare deployment stays live.
5. **Rollback = flip DNS back** to Cloudflare (instant), available until confidence is established.
6. **Decommission** the Worker + Pages + Apps Script project after a soak period; archive the Apps Script/Sheet read-only for audit.

## 9. Testing Strategy

- **Port the existing tests:** Worker `vitest` suite (`worker/test/`) and the PWA e2e golden-path (`app/e2e/golden-path.spec.ts`) re-pointed at the new API.
- **New DB-layer tests:** repository functions against a disposable MySQL (transactions, idempotency-key dedup, concurrent-write correctness).
- **Burst-concurrency load test:** simulate a 50–100-concurrent submission spike (e.g. `k6`/`autocannon`) to confirm the pool + MySQL hold — the exact failure mode of the old stack.
- **Cutover rehearsal:** run the full §8 sequence against the staging Elestio service before the production DNS flip.

## 10. Existing-Codebase Changes (inventory)

- **`app/`** (frontend): API base URL → same-origin `/api` (env var); build/deploy target nginx instead of CF Pages. No survey/UX change.
- **`worker/`** → **new `api/`** service: port `jwt`/`verify`/routes to Hono+Node; **delete** `exec.ts`/`hmac.ts`/admin-HMAC; add MySQL repositories + pool + node-cron.
- **`backend/`** (Apps Script): retired post-soak (kept read-only for audit). Its RPC/handler logic is the reference for the new API routes + schema.
- **New:** Elestio service definition (Docker Compose / managed-DB config), nginx config, MySQL schema + seed scripts, `/data/uploads` volume.

## 11. Out of Scope / YAGNI

- Data migration (clean slate).
- Horizontal scaling, load balancers, ProxySQL, MinIO — single right-sized instance + app-side pool is sufficient; revisit only on evidence.
- Any change to F1/F3/F4, CSWeb, or the PWA survey content/design system.
- Co-hosting on the CSWeb box (explicitly rejected for blast-radius isolation).

## 12. Resolved Decisions (v0.2, 2026-06-22)

- **Subdomain:** `hcw.asiansocial.org` (ASPSI sets DNS, same as `csweb.asiansocial.org`).
- **Deployment mechanism:** single Docker Compose stack (nginx + Node API + MySQL) on one Elestio instance; `mysqldump` backup cron + Elestio volume snapshots. See §3.
- **Runtime:** Node (not Bun).
- **Cost:** approved — new instance follows the same Juvy/ASPSI approval path as the first CSWeb Elestio invoice.

## 13. Sequencing Sketch (detailed plan via writing-plans)

1. Provision the Elestio instance + managed MySQL; nginx + TLS on the subdomain.
2. MySQL schema + seed scripts (admin/roles).
3. API skeleton (Hono+Node) + connection pool; port JWT/auth; health check.
4. Port the PWA submit + the admin route surface onto MySQL repositories.
5. Object-storage (uploads volume) + node-cron break-outs.
6. Point the PWA at `/api`; serve `dist/` from nginx.
7. Port tests + burst-concurrency load test; cutover rehearsal on staging.
8. Re-seed/re-mint; DNS flip; soak; decommission Cloudflare/Apps Script.
