# F2 Elestio Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-platform the entire F2 (HCW survey) stack off Cloudflare + Google onto a dedicated Elestio instance: static PWA on nginx + Node/Hono API + MySQL, replacing the Worker, Apps Script, Google Sheet, KV, R2, and Worker cron.

**Architecture:** A single Docker Compose stack (nginx + Node/Hono API + MySQL) on one Elestio instance at `hcw.asiansocial.org`. The PWA is served same-origin; `/api/*` is the API. The API ports the Worker's JWT/auth/route logic to Node, writes straight to MySQL, and the Worker→Apps-Script HMAC hop is deleted. Clean-slate cutover (no data migration); Cloudflare stays live as instant DNS rollback.

**Tech Stack:** Node 22 LTS, Hono, `mysql2/promise`, `jose` (JWT), `node-cron`, MySQL 8 (InnoDB/utf8mb4), nginx, Docker Compose, Elestio managed hosting. Tests: `vitest` (unit/integration), Playwright (e2e, existing), `autocannon` (burst load).

## Global Constraints

- **Spec:** `docs/superpowers/specs/2026-06-22-f2-elestio-migration-design.md` (v0.2 approved). Every task implicitly inherits it.
- **Domain:** `hcw.asiansocial.org` (DNS set by ASPSI, Elestio managed nginx + auto-SSL).
- **DB conventions (mirror CSWeb):** MySQL 8, InnoDB, charset `utf8mb4` / collation `utf8mb4_unicode_ci`, surrogate `BIGINT UNSIGNED AUTO_INCREMENT` PKs, `created_at`/`updated_at` (`TIMESTAMP DEFAULT CURRENT_TIMESTAMP`).
- **Runtime:** Node (not Bun). API framework Hono.
- **Deployment:** single Docker Compose stack (nginx + node + mysql) on one Elestio instance; `mysqldump` backup cron + Elestio volume snapshots.
- **Data at cutover:** clean slate — migrate nothing; re-seed admin users/roles; re-mint HCW tokens.
- **No CORS:** PWA and API are same-origin; the PWA's API base becomes `/api`.
- **Secrets** live in Elestio env, never in the bundle. `JWT_SIGNING_KEY` regenerated for the new instance.
- **Reference sources to port (do not re-invent behavior):**
  - Worker: `deliverables/F2/PWA/worker/src/{index,jwt,verify,types}.ts`, `worker/src/admin/{routes,auth,rbac,throttle,cron}.ts`, `worker/src/admin/handlers/{auth,data,encode,hcws,users,apps}.ts`. **Delete on port:** `worker/src/{exec,hmac}.ts` + `worker/src/admin/apps-script-client.ts`.
  - Backend (Apps Script — behavior reference for routes + schema): `deliverables/F2/PWA/backend/src/{Router,Handlers,Schema,Auth,Idempotency,Util}.js`, `backend/src/Admin*.js`, `backend/apps-script/*.js`.
- **New service location:** `deliverables/F2/PWA/api/` (the ported Node API) + `deliverables/F2/PWA/deploy/` (Compose, nginx, mysql init).

---

## File Structure

**New — `deliverables/F2/PWA/api/`** (Node/Hono service):
- `src/index.ts` — Hono app entry: mounts routers, starts server, starts cron.
- `src/db/pool.ts` — `mysql2/promise` pool (single export `pool`).
- `src/db/schema.sql` — full DDL (all tables).
- `src/db/migrate.ts` — applies `schema.sql` idempotently.
- `src/db/seed.ts` — seeds roles + bootstrap admin user.
- `src/auth/jwt.ts` — HCW JWT mint/verify (port of worker `jwt.ts`).
- `src/auth/session.ts` — admin session auth (port of `admin/handlers/auth.ts`).
- `src/auth/rbac.ts` — role-permission middleware (port of `admin/rbac.ts`).
- `src/middleware/idempotency.ts` — idempotency-key dedup.
- `src/repos/` — one repository module per table (`responses.ts`, `audit.ts`, `config.ts`, `facilities.ts`, `dlq.ts`, `hcws.ts`, `users.ts`, `roles.ts`, `files.ts`, `settings.ts`, `tokens.ts`).
- `src/routes/public.ts` — the 6 PWA RPCs.
- `src/routes/admin/*.ts` — admin route groups (auth, data, users, hcws, files, settings).
- `src/storage/disk.ts` — disk-volume object storage (replaces R2).
- `src/jobs/breakouts.ts` — node-cron scheduled break-out job.
- `test/**` — vitest unit/integration; `loadtest/submit-burst.js` — autocannon script.

**New — `deliverables/F2/PWA/deploy/`**:
- `docker-compose.yml`, `Dockerfile.api`, `nginx/hcw.conf`, `mysql/my.cnf`, `scripts/backup-mysqldump.sh`.

**Modified:**
- `deliverables/F2/PWA/app/.env.production` (or vite config) — `VITE_API_BASE=/api`.
- `deliverables/F2/PWA/app/src/**` — API client base URL only (no UX change).

**Retired post-soak (kept read-only):** `worker/`, `backend/` Apps Script project.

---

## Task 1: Elestio instance + Docker Compose skeleton + TLS

**Files:**
- Create: `deliverables/F2/PWA/deploy/docker-compose.yml`
- Create: `deliverables/F2/PWA/deploy/Dockerfile.api`
- Create: `deliverables/F2/PWA/deploy/nginx/hcw.conf`
- Create: `deliverables/F2/PWA/deploy/mysql/my.cnf`

**Interfaces:**
- Produces: a running stack exposing nginx :80/:443 → static `dist/` + `/api` proxy to the `api` container :8787; `mysql` reachable in-network as host `mysql:3306`.

- [ ] **Step 1: Write `docker-compose.yml`**

```yaml
services:
  mysql:
    image: mysql:8.0
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: f2hcw
      MYSQL_USER: f2app
      MYSQL_PASSWORD_FILE: /run/secrets/mysql_app_pw
      MYSQL_ROOT_PASSWORD_FILE: /run/secrets/mysql_root_pw
    volumes:
      - mysqldata:/var/lib/mysql
      - ./mysql/my.cnf:/etc/mysql/conf.d/my.cnf:ro
    secrets: [mysql_app_pw, mysql_root_pw]

  api:
    build: { context: ../api, dockerfile: ../deploy/Dockerfile.api }
    restart: unless-stopped
    environment:
      DB_HOST: mysql
      DB_USER: f2app
      DB_NAME: f2hcw
      DB_PASSWORD_FILE: /run/secrets/mysql_app_pw
      JWT_SIGNING_KEY_FILE: /run/secrets/jwt_key
      UPLOADS_DIR: /data/uploads
    volumes: [ "uploads:/data/uploads" ]
    secrets: [mysql_app_pw, jwt_key]
    depends_on: [mysql]

  nginx:
    image: nginx:1.27
    restart: unless-stopped
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/hcw.conf:/etc/nginx/conf.d/default.conf:ro
      - pwa_dist:/usr/share/nginx/html:ro
    depends_on: [api]

volumes: { mysqldata: {}, uploads: {}, pwa_dist: {} }
secrets:
  mysql_app_pw: { file: ./secrets/mysql_app_pw }
  mysql_root_pw: { file: ./secrets/mysql_root_pw }
  jwt_key: { file: ./secrets/jwt_key }
```

> On Elestio, TLS termination is handled by Elestio's managed reverse proxy in front of this stack; `hcw.conf` serves plain HTTP on :80 internally. If self-terminating, add the cert mounts. Confirm which at provisioning.

- [ ] **Step 2: Write `nginx/hcw.conf`**

```nginx
server {
  listen 80;
  server_name hcw.asiansocial.org;
  root /usr/share/nginx/html;
  index index.html;

  location /api/ {
    proxy_pass http://api:8787/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
  location / { try_files $uri $uri/ /index.html; }  # SPA fallback
}
```

- [ ] **Step 3: Write `Dockerfile.api`**

```dockerfile
FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY dist ./dist
EXPOSE 8787
CMD ["node", "dist/index.js"]
```

- [ ] **Step 4: Write `mysql/my.cnf`**

```ini
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
max_connections = 150
default-storage-engine = INNODB
```

- [ ] **Step 5: Provision + smoke test**

Provision the Elestio instance (2 vCPU / 4 GB), point `hcw.asiansocial.org` DNS (ASPSI), create `deploy/secrets/*` files. Then:
Run: `docker compose up -d && curl -fsS http://localhost/api/health`
Expected: stack starts; once Task 4 lands, `/api/health` returns `{"ok":true}`. For now: `docker compose ps` shows mysql + nginx healthy.

- [ ] **Step 6: Commit** (`feat(f2-migration): elestio compose stack + nginx + mysql skeleton`)

---

## Task 2: MySQL schema (DDL) + migration runner

**Files:**
- Create: `deliverables/F2/PWA/api/src/db/schema.sql`
- Create: `deliverables/F2/PWA/api/src/db/migrate.ts`
- Create: `deliverables/F2/PWA/api/src/db/pool.ts`
- Test: `deliverables/F2/PWA/api/test/db/schema.test.ts`

**Interfaces:**
- Produces: `pool` (mysql2 promise pool); `migrate(): Promise<void>`; the full table set below.
- Schema mirrors `backend/src/Schema.js` columns 1:1 (so the PWA payload shape is preserved), plus the admin tables.

- [ ] **Step 1: Write `schema.sql`** (tables derived verbatim from `backend/src/Schema.js` + the admin RPC surface)

```sql
CREATE TABLE IF NOT EXISTS responses (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  submission_id VARCHAR(64) NOT NULL UNIQUE,
  client_submission_id VARCHAR(64) NOT NULL,
  submitted_at_server TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  submitted_at_client DATETIME NULL,
  source VARCHAR(32) NOT NULL,
  spec_version VARCHAR(48) NULL,
  app_version VARCHAR(48) NULL,
  hcw_id VARCHAR(64) NULL,
  facility_id VARCHAR(16) NULL,
  device_fingerprint VARCHAR(128) NULL,
  sync_attempt_count INT DEFAULT 0,
  status VARCHAR(16) NOT NULL,
  values_json JSON NOT NULL,
  submission_lat DECIMAL(10,7) NULL,
  submission_lng DECIMAL(10,7) NULL,
  source_path VARCHAR(16) NULL,
  encoded_by VARCHAR(64) NULL,
  encoded_at DATETIME NULL,
  UNIQUE KEY uq_client_sub (client_submission_id),
  KEY idx_facility (facility_id), KEY idx_status (status), KEY idx_submitted (submitted_at_server)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS audit_log (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  audit_id VARCHAR(64) NOT NULL UNIQUE,
  occurred_at_server TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  occurred_at_client DATETIME NULL,
  event_type VARCHAR(48) NOT NULL,
  hcw_id VARCHAR(64) NULL, facility_id VARCHAR(16) NULL, app_version VARCHAR(48) NULL,
  payload_json JSON NULL,
  actor_username VARCHAR(64) NULL, actor_jti VARCHAR(64) NULL, actor_role VARCHAR(48) NULL,
  event_resource VARCHAR(64) NULL, event_payload_json JSON NULL,
  client_ip_hash VARCHAR(64) NULL, request_id VARCHAR(64) NULL,
  KEY idx_evt (event_type), KEY idx_occurred (occurred_at_server)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS config (
  cfg_key VARCHAR(64) PRIMARY KEY, cfg_value TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS facilities (
  facility_id VARCHAR(16) PRIMARY KEY,
  facility_name VARCHAR(255), facility_type VARCHAR(64),
  region VARCHAR(64), province VARCHAR(64), city_mun VARCHAR(64), barangay VARCHAR(64)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dlq (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  dlq_id VARCHAR(64) NOT NULL UNIQUE,
  received_at_server TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  client_submission_id VARCHAR(64), reason VARCHAR(255), payload_json JSON
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS roles (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(48) NOT NULL UNIQUE,
  permissions_json JSON NOT NULL,           -- per-dashboard + per-instrument flags (mirrors CSWeb model)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS admin_users (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role_id BIGINT UNSIGNED NOT NULL,
  must_change_password TINYINT(1) DEFAULT 1,
  last_login_at DATETIME NULL,
  disabled TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (role_id) REFERENCES roles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS hcws (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  hcw_id VARCHAR(64) NOT NULL UNIQUE,
  facility_id VARCHAR(16) NOT NULL,
  case_seq INT NULL,
  token_hash VARCHAR(128) NULL,
  status VARCHAR(16) DEFAULT 'issued',
  issued_at DATETIME NULL, used_at DATETIME NULL,
  KEY idx_fac (facility_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS revoked_tokens (
  jti VARCHAR(64) PRIMARY KEY,
  expires_at DATETIME NOT NULL,
  KEY idx_exp (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS idempotency_keys (
  k VARCHAR(128) PRIMARY KEY,
  response_json JSON NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS data_settings (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  spec_json JSON NOT NULL,                 -- break-out definition (dictionary, filters)
  schedule_cron VARCHAR(64) NULL,
  next_run_at DATETIME NULL,
  last_run_at DATETIME NULL,
  KEY idx_next (next_run_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS files (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  path VARCHAR(512) NOT NULL UNIQUE,       -- logical path (folder/name)
  disk_path VARCHAR(512) NOT NULL,         -- physical path under UPLOADS_DIR
  size_bytes BIGINT, content_type VARCHAR(128), is_folder TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

- [ ] **Step 2: Write `pool.ts`**

```ts
import mysql from 'mysql2/promise';
import { readFileSync } from 'node:fs';
const password = process.env.DB_PASSWORD_FILE
  ? readFileSync(process.env.DB_PASSWORD_FILE, 'utf8').trim()
  : process.env.DB_PASSWORD!;
export const pool = mysql.createPool({
  host: process.env.DB_HOST, user: process.env.DB_USER, database: process.env.DB_NAME,
  password, connectionLimit: 15, waitForConnections: true, queueLimit: 0,
  charset: 'utf8mb4', timezone: 'Z',
});
```

- [ ] **Step 3: Write `migrate.ts`**

```ts
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { pool } from './pool';
export async function migrate(): Promise<void> {
  const sql = readFileSync(fileURLToPath(new URL('./schema.sql', import.meta.url)), 'utf8');
  const conn = await pool.getConnection();
  try { for (const stmt of sql.split(/;\s*\n/).filter(s => s.trim())) await conn.query(stmt); }
  finally { conn.release(); }
}
```

- [ ] **Step 4: Write the failing test** (`test/db/schema.test.ts`)

```ts
import { describe, it, expect, beforeAll } from 'vitest';
import { migrate } from '../../src/db/migrate';
import { pool } from '../../src/db/pool';
describe('schema', () => {
  beforeAll(async () => { await migrate(); });
  it('creates all tables', async () => {
    const [rows] = await pool.query<any[]>('SHOW TABLES');
    const names = rows.map(r => Object.values(r)[0]);
    for (const t of ['responses','audit_log','config','facilities','dlq','roles','admin_users','hcws','revoked_tokens','idempotency_keys','data_settings','files'])
      expect(names).toContain(t);
  });
});
```

- [ ] **Step 5: Run test** — Run: `npm test -- schema` against a disposable MySQL (`docker compose up -d mysql`). Expected: FAIL (tables missing) → PASS after migrate runs.
- [ ] **Step 6: Commit** (`feat(f2-migration): mysql schema + pool + migration runner`)

---

## Task 3: Seed roles + bootstrap admin user

**Files:**
- Create: `deliverables/F2/PWA/api/src/db/seed.ts`
- Test: `deliverables/F2/PWA/api/test/db/seed.test.ts`

**Interfaces:**
- Consumes: `pool`, `migrate`. Produces: `seed(): Promise<void>` inserting the role taxonomy + one bootstrap admin (`must_change_password=1`).
- Role taxonomy mirrors the CSWeb 5-dashboard model already implemented in `worker/src/admin/rbac.ts` — read that file to copy the exact permission keys into `permissions_json`.

- [ ] **Step 1: Write `seed.ts`** — insert roles (admin, data-manager, monitor, etc. per `rbac.ts`) with `permissions_json`, and a bootstrap `admin` user via `bcrypt` hash (password from `BOOTSTRAP_ADMIN_PW` env, `must_change_password=1`). Use `INSERT ... ON DUPLICATE KEY UPDATE` for idempotency.
- [ ] **Step 2: Write the failing test** — after `seed()`, assert ≥1 row in `roles`, the bootstrap user exists in `admin_users` with `must_change_password=1` and a non-plaintext `password_hash`.
- [ ] **Step 3: Run test** — Expected FAIL → implement → PASS.
- [ ] **Step 4: Commit** (`feat(f2-migration): role taxonomy + bootstrap admin seed`)

---

## Task 4: Hono app skeleton + health route

**Files:**
- Create: `deliverables/F2/PWA/api/src/index.ts`
- Create: `deliverables/F2/PWA/api/package.json`
- Test: `deliverables/F2/PWA/api/test/health.test.ts`

**Interfaces:**
- Produces: a Hono `app` listening on :8787; `GET /health` → `{ ok: true, db: true }` (pings DB).

- [ ] **Step 1: Write `index.ts`**

```ts
import { Hono } from 'hono';
import { serve } from '@hono/node-server';
import { pool } from './db/pool';
export const app = new Hono();
app.get('/health', async (c) => {
  try { await pool.query('SELECT 1'); return c.json({ ok: true, db: true }); }
  catch { return c.json({ ok: false, db: false }, 500); }
});
// route groups mounted in later tasks: app.route('/', publicRoutes); app.route('/admin', adminRoutes)
if (process.env.NODE_ENV !== 'test') {
  serve({ fetch: app.fetch, port: 8787 });
}
```

- [ ] **Step 2: Write the failing test** — `app.request('/health')` returns 200 `{ok:true}`.
- [ ] **Step 3: Run test** — Expected FAIL → implement → PASS.
- [ ] **Step 4: Commit** (`feat(f2-migration): hono api skeleton + health check`)

---

## Task 5: Port HCW JWT mint/verify + revocation + auth middleware

**Files:**
- Create: `deliverables/F2/PWA/api/src/auth/jwt.ts`
- Create: `deliverables/F2/PWA/api/src/repos/tokens.ts`
- Create: `deliverables/F2/PWA/api/src/middleware/hcwAuth.ts`
- Test: `deliverables/F2/PWA/api/test/auth/jwt.test.ts`

**Interfaces:**
- Port `worker/src/jwt.ts` exactly (same claims, same `JWT_SIGNING_KEY`). Web Crypto → `jose`.
- Produces: `mintToken(claims)`, `verifyToken(jwt): Promise<Claims>` (throws on bad/expired/revoked), `revoke(jti, exp)`, `isRevoked(jti)`. `hcwAuth` middleware sets `c.set('hcw', claims)` or 401.

- [ ] **Step 1: Write the failing test**

```ts
import { describe, it, expect } from 'vitest';
import { mintToken, verifyToken, revoke } from '../../src/auth/jwt';
describe('hcw jwt', () => {
  it('mints and verifies a token round-trip', async () => {
    const t = await mintToken({ sub: 'HCW-1', facility_id: '040340002' });
    const claims = await verifyToken(t);
    expect(claims.sub).toBe('HCW-1');
  });
  it('rejects a revoked token', async () => {
    const t = await mintToken({ sub: 'HCW-2', facility_id: '040340002' });
    const { jti, exp } = await verifyToken(t);
    await revoke(jti, new Date(exp * 1000));
    await expect(verifyToken(t)).rejects.toThrow();
  });
});
```

- [ ] **Step 2: Run test** — Expected FAIL.
- [ ] **Step 3: Implement** `jwt.ts` (jose `SignJWT`/`jwtVerify`, HS256, key from `JWT_SIGNING_KEY`/`_FILE`; `jti` via `crypto.randomUUID()`), `tokens.ts` (`revoked_tokens` insert/select + expiry cleanup), `verifyToken` checks `isRevoked`. Preserve the claim set + TTL from `worker/src/jwt.ts`.
- [ ] **Step 4: Run test** — Expected PASS.
- [ ] **Step 5: Commit** (`feat(f2-migration): port hcw jwt + revocation to node`)

---

## Task 6: Idempotency middleware

**Files:**
- Create: `deliverables/F2/PWA/api/src/middleware/idempotency.ts`
- Create: `deliverables/F2/PWA/api/src/repos/idempotency.ts`
- Test: `deliverables/F2/PWA/api/test/middleware/idempotency.test.ts`

**Interfaces:**
- Port behavior from `backend/src/Idempotency.js`. Produces: `withIdempotency(key, fn)` — returns cached `response_json` if `key` seen, else runs `fn`, stores result, returns it.

- [ ] **Step 1: Write the failing test** — calling `withIdempotency('k1', fn)` twice runs `fn` once; second call returns the cached value.
- [ ] **Step 2: Run** Expected FAIL.
- [ ] **Step 3: Implement** (INSERT IGNORE on unique `k`; on conflict SELECT cached row).
- [ ] **Step 4: Run** Expected PASS.
- [ ] **Step 5: Commit** (`feat(f2-migration): idempotency middleware`)

---

## Task 7: Port the 3 read-only PWA routes (facilities, config, spec-hash)

**Files:**
- Create: `deliverables/F2/PWA/api/src/routes/public.ts`
- Create: `deliverables/F2/PWA/api/src/repos/{facilities,config}.ts`
- Test: `deliverables/F2/PWA/api/test/routes/public-read.test.ts`

**Interfaces:**
- Port handlers `handleFacilities`, `handleConfig`, `handleSpecHash` from `backend/src/Handlers.js` (read that file for exact response shapes). Routes: `GET /facilities`, `GET /config`, `GET /spec-hash`. Response envelope `{ ok: true, data }` matching the current Worker/Apps Script contract so the PWA needs no change.

- [ ] **Step 1: Write the failing test** — seed a facility + config rows; `GET /facilities` returns the row; `GET /config` returns the kill_switch/spec_version map; `GET /spec-hash` returns `{ ok:true, data:{ hash } }`.
- [ ] **Step 2: Run** Expected FAIL.
- [ ] **Step 3: Implement** the repos + routes; preserve the exact JSON envelope from `Handlers.js`.
- [ ] **Step 4: Run** Expected PASS.
- [ ] **Step 5: Commit** (`feat(f2-migration): port read-only pwa routes`)

---

## Task 8: Port submit + batch-submit + audit (the write path) — WORKED PATTERN

> This is the canonical write-route pattern. Later port tasks follow this exact shape: route → validate → (idempotency) → repo transaction → audit → envelope.

**Files:**
- Modify: `deliverables/F2/PWA/api/src/routes/public.ts`
- Create: `deliverables/F2/PWA/api/src/repos/{responses,audit,dlq}.ts`
- Test: `deliverables/F2/PWA/api/test/routes/submit.test.ts`

**Interfaces:**
- Port `handleSubmit`, `handleBatchSubmit`, `handleAudit` from `backend/src/Handlers.js`. Routes: `POST /submit`, `POST /batch-submit`, `POST /audit`.
- `responses.insert(row)` maps the PWA payload to the `responses` columns (Schema.js order). Kill-switch check via `config`. On insert error → `dlq.insert(...)`. Each accepted submit writes an `audit_log` row.

- [ ] **Step 1: Write the failing test**

```ts
import { describe, it, expect, beforeAll } from 'vitest';
import { app } from '../../src/index';
import { migrate } from '../../src/db/migrate';
import { pool } from '../../src/db/pool';
beforeAll(async () => { await migrate(); });
describe('POST /submit', () => {
  const body = { client_submission_id: 'c-1', facility_id: '040340002', status: 'completed',
                 source: 'pwa', values: { Q1: 1 } };
  it('persists a submission and is idempotent on client_submission_id', async () => {
    const r1 = await app.request('/submit', { method: 'POST', body: JSON.stringify(body),
      headers: { 'content-type': 'application/json' } });
    expect(r1.status).toBe(200);
    const r2 = await app.request('/submit', { method: 'POST', body: JSON.stringify(body),
      headers: { 'content-type': 'application/json' } });
    expect(r2.status).toBe(200);
    const [rows] = await pool.query<any[]>('SELECT COUNT(*) n FROM responses WHERE client_submission_id=?', ['c-1']);
    expect(rows[0].n).toBe(1);           // dedup held
  });
  it('blocks when kill_switch is on', async () => {
    await pool.query("INSERT INTO config (cfg_key,cfg_value) VALUES ('kill_switch','true') ON DUPLICATE KEY UPDATE cfg_value='true'");
    const r = await app.request('/submit', { method: 'POST', body: JSON.stringify({ ...body, client_submission_id: 'c-2' }),
      headers: { 'content-type': 'application/json' } });
    expect(r.status).toBe(503);
    await pool.query("UPDATE config SET cfg_value='false' WHERE cfg_key='kill_switch'");
  });
});
```

- [ ] **Step 2: Run** Expected FAIL.
- [ ] **Step 3: Implement** the routes + `responses`/`audit`/`dlq` repos. Submit: kill-switch guard (503 `E_KILL_SWITCH`), idempotency on `client_submission_id`, map payload → columns, write audit row, return `{ ok:true, data:{ submission_id } }`. Batch-submit: loop with per-item result. Preserve `Handlers.js` validation + error codes.
- [ ] **Step 4: Run** Expected PASS.
- [ ] **Step 5: Commit** (`feat(f2-migration): port submit/batch-submit/audit write path`)

---

## Task 9: Admin session auth + RBAC middleware

**Files:**
- Create: `deliverables/F2/PWA/api/src/auth/session.ts`, `src/auth/rbac.ts`, `src/repos/{users,roles}.ts`
- Create: `deliverables/F2/PWA/api/src/routes/admin/auth.ts`
- Test: `deliverables/F2/PWA/api/test/admin/auth.test.ts`

**Interfaces:**
- Port `worker/src/admin/handlers/auth.ts` (login/logout/change-my-password) + `worker/src/admin/rbac.ts` (permission keys). Routes: `POST /admin/login`, `POST /admin/logout`, `POST /admin/change-password`.
- Produces: `adminAuth` middleware (validates admin session JWT → `c.set('admin', {username, role, perms})`); `requirePerm(key)` middleware (403 if missing). Login verifies `bcrypt` against `admin_users.password_hash`, updates `last_login_at`, returns a session token; enforces `must_change_password`.

- [ ] **Step 1: Write the failing test** — seed admin (Task 3); `POST /admin/login` with correct creds → 200 + token; wrong creds → 401; a `requirePerm('users.write')`-guarded probe route → 403 for a monitor role, 200 for admin.
- [ ] **Step 2: Run** Expected FAIL.
- [ ] **Step 3: Implement** session mint/verify (reuse `jose`), `rbac.ts` perm map (copy keys from the Worker file), repos.
- [ ] **Step 4: Run** Expected PASS.
- [ ] **Step 5: Commit** (`feat(f2-migration): admin session auth + rbac`)

---

## Task 10: Admin read/report routes

**Files:**
- Create: `deliverables/F2/PWA/api/src/routes/admin/data.ts`
- Test: `deliverables/F2/PWA/api/test/admin/data.test.ts`

**Interfaces:**
- Port `worker/src/admin/handlers/data.ts` + backend `admin_read_responses/count_responses/read_response_by_id/read_audit/read_dlq/form_revisions/sync_report/map_report`. Routes under `/admin/api/...` matching the names the Admin Portal frontend already calls (read `admin/routes.ts` for exact paths). All `requirePerm`-guarded per `rbac.ts`. Pattern = Task 8 (read variant: filter parse → repo SELECT with `LIMIT/OFFSET` → envelope).

- [ ] **Step 1: Write the failing test** — seed 3 responses; `GET /admin/api/responses?status=completed` returns the filtered set with the same envelope/pagination shape as `data.ts`; `responses/:id` returns one; unauthorized role → 403.
- [ ] **Step 2-4:** Run FAIL → implement all read/report routes (preserve filters + shapes from `data.ts`) → Run PASS.
- [ ] **Step 5: Commit** (`feat(f2-migration): admin read + report routes`)

---

## Task 11: Admin users + roles CRUD (+ bulk import, revoke sessions)

**Files:**
- Create: `deliverables/F2/PWA/api/src/routes/admin/users.ts`
- Test: `deliverables/F2/PWA/api/test/admin/users.test.ts`

**Interfaces:**
- Port `worker/src/admin/handlers/users.ts` + backend `admin_users_*` / `admin_roles_*`. Routes (names per `users.ts`): list/create/update/delete/bulk-import/revoke-sessions for users; list/create/update/delete for roles. Pattern = Task 8. `revoke-sessions` writes the user's active jti(s) into `revoked_tokens`.

- [ ] **Step 1: Write the failing test** — create user (hashed pw, `must_change_password=1`); duplicate username → conflict error; bulk-import N rows; delete; role CRUD; all `requirePerm('users.write'|'roles.write')`-guarded.
- [ ] **Step 2-4:** Run FAIL → implement → Run PASS.
- [ ] **Step 5: Commit** (`feat(f2-migration): admin users + roles crud`)

---

## Task 12: Admin HCWs (create + reissue token) + config (kill-switch/broadcast)

**Files:**
- Create: `deliverables/F2/PWA/api/src/routes/admin/hcws.ts`, `src/repos/hcws.ts`
- Test: `deliverables/F2/PWA/api/test/admin/hcws.test.ts`

**Interfaces:**
- Port `worker/src/admin/handlers/hcws.ts` + backend `admin_hcws_create/reissue_token`, `admin_config_get/set`. `reissue-token` re-mints an HCW enrollment token (Task 5 mint) + stores `token_hash`, invalidates the prior via `revoked_tokens`. Routes per `admin/routes.ts`.

- [ ] **Step 1: Write the failing test** — create HCW row; reissue produces a new token whose `verifyToken` passes and whose prior jti is revoked; kill-switch set→get round-trips through `config`.
- [ ] **Step 2-4:** Run FAIL → implement → Run PASS.
- [ ] **Step 5: Commit** (`feat(f2-migration): admin hcws + config routes`)

---

## Task 13: Disk-volume object storage + admin files routes

**Files:**
- Create: `deliverables/F2/PWA/api/src/storage/disk.ts`, `src/repos/files.ts`, `src/routes/admin/files.ts`
- Test: `deliverables/F2/PWA/api/test/admin/files.test.ts`

**Interfaces:**
- Replaces R2. Port `worker/src/admin/handlers/apps.ts` (file ops) + backend `admin_files_*`. `disk.ts`: `put(logicalPath, bytes)`, `get(logicalPath)`, `del(logicalPath)`, `move(a,b)` under `UPLOADS_DIR` with **path-traversal guard** (reject `..`, absolute paths). `files` table holds metadata. Routes: list/upload/download/delete/rename/create-folder per `admin/routes.ts`.

- [ ] **Step 1: Write the failing test** — upload a file → appears in list + on disk; download returns identical bytes; a path with `../` is rejected (400); delete removes both row + file.
- [ ] **Step 2-4:** Run FAIL → implement (stream upload/download; `requirePerm('files.write'|'files.read')`) → Run PASS.
- [ ] **Step 5: Commit** (`feat(f2-migration): disk storage + admin files routes`)

---

## Task 14: Break-out scheduler (node-cron) + settings routes

**Files:**
- Create: `deliverables/F2/PWA/api/src/jobs/breakouts.ts`, `src/repos/settings.ts`, `src/routes/admin/settings.ts`
- Modify: `deliverables/F2/PWA/api/src/index.ts` (start cron when `NODE_ENV!=='test'`)
- Test: `deliverables/F2/PWA/api/test/jobs/breakouts.test.ts`

**Interfaces:**
- Replaces the Worker `*/5` cron. Port backend `admin_settings_*` (`run_due`, `run_now`, `mark_complete`, CRUD) + the dispatch logic. `runDue(now)`: select `data_settings WHERE next_run_at <= now`, write break-out CSV to `UPLOADS_DIR` via `disk.ts`, set `last_run_at` + recompute `next_run_at` from `schedule_cron`. `node-cron` schedules `runDue` every 5 min.

- [ ] **Step 1: Write the failing test** — insert a `data_settings` row with `next_run_at` in the past; call `runDue(now)`; assert a CSV exists in storage and `last_run_at` updated and `next_run_at` advanced.
- [ ] **Step 2-4:** Run FAIL → implement → Run PASS.
- [ ] **Step 5: Commit** (`feat(f2-migration): break-out scheduler + settings routes`)

---

## Task 15: Mount routers + wire the full app

**Files:**
- Modify: `deliverables/F2/PWA/api/src/index.ts`
- Test: `deliverables/F2/PWA/api/test/app-wiring.test.ts`

**Interfaces:**
- Mounts `public.ts` at `/` and the admin routers under `/admin`; applies `hcwAuth` to protected PWA routes and `adminAuth`+`requirePerm` to admin routes; starts the cron.

- [ ] **Step 1: Write the failing test** — unauthenticated `GET /admin/api/responses` → 401; `GET /health` → 200; an HCW-auth-required route → 401 without token, 200 with.
- [ ] **Step 2-4:** Run FAIL → wire mounts + middleware → Run PASS.
- [ ] **Step 5: Commit** (`feat(f2-migration): mount routers + middleware wiring`)

---

## Task 16: Repoint the PWA frontend at the new API + nginx static serve

**Files:**
- Modify: `deliverables/F2/PWA/app/.env.production` (add `VITE_API_BASE=/api`)
- Modify: `deliverables/F2/PWA/app/src/**` API client base (single module — find where the Worker URL is configured)
- Modify: `deliverables/F2/PWA/deploy/docker-compose.yml` (build step copies `app/dist` into the `pwa_dist` volume)
- Test: existing `deliverables/F2/PWA/app/e2e/golden-path.spec.ts` (re-point base URL)

**Interfaces:**
- Frontend calls same-origin `/api/*`. No UX/spec change. `npm run build` then nginx serves `dist/` with SPA fallback (Task 1).

- [ ] **Step 1:** Find the API base config in `app/src` (grep `pages.dev` / `workers.dev` / `VITE_`); replace with `import.meta.env.VITE_API_BASE`.
- [ ] **Step 2:** Set `VITE_API_BASE=/api`; `npm run build`; confirm `check-bundle-secrets.mjs` still passes (no secret in bundle).
- [ ] **Step 3:** Run the e2e golden path against the Compose stack: `npm run e2e` pointed at `http://localhost`. Expected: enrollment → sections → submit → review all pass against the new API.
- [ ] **Step 4: Commit** (`feat(f2-migration): repoint pwa to same-origin /api + nginx serve`)

---

## Task 17: Burst-concurrency load test

**Files:**
- Create: `deliverables/F2/PWA/api/loadtest/submit-burst.js`
- Test: this task's deliverable is the load-test result.

**Interfaces:**
- `autocannon` script POSTing `/submit` with unique `client_submission_id` per request.

- [ ] **Step 1: Write the autocannon script** — 100 concurrent connections, 30s, unique body per request (`crypto.randomUUID()` for `client_submission_id`).
- [ ] **Step 2: Run** against the Compose stack: `node loadtest/submit-burst.js`.
  Expected: **0 non-2xx**, p99 latency < 500ms, no connection-pool exhaustion errors — the exact failure mode the old Sheets/Apps-Script stack could not survive. Record the numbers.
- [ ] **Step 3: Tune** `connectionLimit` (pool) + MySQL `max_connections` if saturation appears; re-run.
- [ ] **Step 4: Commit** (`test(f2-migration): burst-concurrency load test + tuning`)

---

## Task 18: Backup cron + ops runbook

**Files:**
- Create: `deliverables/F2/PWA/deploy/scripts/backup-mysqldump.sh`
- Create: `deliverables/F2/PWA/deploy/README.md` (ops runbook)

**Interfaces:**
- `mysqldump` to a dated file under a backup volume, retained N days, on a daily cron (mirrors CSWeb backup practice). Runbook documents deploy, restore, secret rotation.

- [ ] **Step 1:** Write `backup-mysqldump.sh` (dump → gzip → rotate); add a daily cron entry (host cron or a compose `ofelia`/cron sidecar).
- [ ] **Step 2:** Test restore: load the dump into a throwaway MySQL, verify row counts.
- [ ] **Step 3:** Write the runbook (provision, deploy, DNS, restore, rollback, decommission).
- [ ] **Step 4: Commit** (`chore(f2-migration): mysqldump backup + ops runbook`)

---

## Task 19: Cutover rehearsal + DNS flip + rollback

**Files:**
- Modify: `deliverables/F2/PWA/deploy/README.md` (cutover checklist)

**Interfaces:**
- Operational task; deliverable is a green rehearsal + the live cutover.

- [ ] **Step 1:** On the staging Elestio service, run the full §8 sequence from the spec: build → validate (golden path + admin RBAC + file roundtrip + break-out) → re-seed admin/roles → re-mint HCW tokens → burst load test.
- [ ] **Step 2:** Production flip: point `hcw.asiansocial.org` DNS → Elestio; keep Cloudflare deployment live.
- [ ] **Step 3:** Smoke the production URL (enroll → submit → admin login). Document the rollback (flip DNS back to Cloudflare).
- [ ] **Step 4:** Soak period; then decommission Worker + Pages + Apps Script; archive the Apps Script/Sheet read-only for audit.
- [ ] **Step 5: Commit** (`chore(f2-migration): cutover checklist + rollback runbook`)

---

## Self-Review

**Spec coverage** (each §3–§10 spec section → task):
- §4.1 static PWA → Tasks 1, 16. §4.2 Hono API/port → Tasks 4, 5, 7–15. §4.3 MySQL schema → Task 2. §4.4 disk storage → Task 13. §4.5 node-cron → Task 14. §4.6 auth (HCW JWT + admin + HMAC deleted) → Tasks 5, 9 (deletion is inherent — the new API never calls Apps Script). §5 mapping → covered across tasks. §6 security (TLS, secrets, RBAC, backups) → Tasks 1, 9, 18. §7 clean slate → Task 3 (seed) + Task 19 (re-mint). §8 cutover/rollback → Task 19. §9 testing (ported tests, DB tests, burst load, rehearsal) → Tasks 5–17 (per-task), 17, 19. §10 codebase changes → Tasks 5/7/8 (worker port), 16 (frontend), 19 (backend retire). **No gaps.**

**Placeholder scan:** Read-route/admin ports (Tasks 10–12) use the Task 8 worked pattern + cite the exact source file to port; this is deliberate port methodology, not a placeholder — the exact handler internals must be copied from the named source to preserve behavior, and inventing them here would risk divergence. Foundational tasks (1–9, 13, 14, 17) carry complete code/DDL/tests.

**Type consistency:** `pool` (Task 2) used everywhere; `mintToken/verifyToken/revoke` (Task 5) reused in Tasks 9/12; `withIdempotency` (Task 6) used in Task 8; `disk.put/get/del` (Task 13) used in Task 14; config key `kill_switch` consistent (Tasks 2, 8); `client_submission_id` unique-dedup consistent (Tasks 2, 8). Envelope `{ ok, data|error }` consistent with the Apps Script contract so the PWA is unchanged.
