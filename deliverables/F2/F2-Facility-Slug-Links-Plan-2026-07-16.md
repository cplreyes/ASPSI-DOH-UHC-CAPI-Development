# F2 — Facility Slug Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Project override:** no git commit steps — Carl handles git manually.

**Goal:** One clean public link per facility — `uhc-hcw.asiansocial.org/f/<slug>` — that self-registers any HCW into a QN-bound case at that facility, with a delivery-gated thank-you screen.

**Architecture:** New `f2_facility_slugs` table + public `GET /f/resolve` + a `{slug}` branch on `POST /self-register` that also mints a qn-bound device token (reusing the `/claim` mint). PWA adds a `FacilityStartScreen` on `/f/<slug>` and a Dexie-driven `DeliveryStatus` on the thank-you screen. Admin gets a per-facility "Facility link" modal; the numbered-links generator stays behind a legacy button.

**Tech Stack:** Hono + mysql2 (server), React + TS + Vite + Dexie + i18next + qrcode.react (app), Vitest both sides.

**Spec:** `deliverables/F2/F2-Facility-Slug-Links-Design-2026-07-16.md` (approved 2026-07-16).

## Global Constraints

- Slug grammar: `^[a-z0-9][a-z0-9-]{1,30}$`, normalized lowercase; `resolve` is reserved.
- `/f/` is **not** added to `API_PATH_RE` — `/f/<slug>` must fall through to the SPA; `GET /f/resolve` is an exact route registered before static serving.
- QN stays 12-digit facility-encoded, assigned by the existing `createHcw(qn='')` assigner (F2 block floor 100).
- Device token: same `JwtClaims` shape as `/claim`, TTL `CLAIM_TOKEN_TTL_DAYS = 90`, `tokenAudit` written.
- kill_switch parity: HTTP 200 + `{ok:false, error:{code:'E_KILL_SWITCH'}}`.
- Unknown/inactive slug: 404 `E_NOT_FOUND`, neutral message "This survey link isn't active — check with ASPSI ops."
- Legacy paths stay alive: `/claim` + `ClaimScreen` (LPH-Bay cards), facility-JWT `/self-register`, `EnrollmentScreen` behind `/enroll`.
- i18n: every new key added to `en.ts` **and** the 7 other locales (English fallback, translations pending). English wordings verbatim — translation passes never edit them.
- New admin endpoints gate on `dash_users`; mutations audit via `auditMutation` (success-gated).
- Codebase: staging worktree `deliverables/F2/PWA/{server,app}`. Run `tsc -b --force` before any push (stale build-info trap).
- No git commits by the agent — Carl handles git manually.

---

### Task 1: Server — slug grammar module + DDL

**Files:**
- Create: `server/src/facility-slugs.ts`
- Modify: `server/ddl/f2_api_tables.sql` (append after the `uq_enroll_slug` guarded ALTER block)

**Interfaces:**
- Produces: `FACILITY_SLUG_RE: RegExp`, `RESERVED_FACILITY_SLUGS: Set<string>`, `normalizeFacilitySlug(raw: string): string` — consumed by Tasks 3, 4.

- [ ] **Step 1: Write `server/src/facility-slugs.ts`**

```ts
/**
 * Facility slug links (design F2-Facility-Slug-Links-2026-07-16).
 *
 * One clean, readable public link per facility — `<origin>/f/<slug>` — with no
 * secret in the URL (deliberately open; integrity = Start-tap self-register,
 * admin dedup/prune, kill switch). The slug is looked up in f2_facility_slugs.
 */

/** Lowercase, 2-31 chars, starts with a letter/digit, hyphens allowed. */
export const FACILITY_SLUG_RE = /^[a-z0-9][a-z0-9-]{1,30}$/;

/** `GET /f/resolve` shadows `/f/<slug>` for this name — never a valid slug. */
export const RESERVED_FACILITY_SLUGS = new Set(['resolve']);

/** Normalise a slug from a URL/body for lookup (stored lowercase). */
export function normalizeFacilitySlug(raw: string): string {
  return raw.trim().toLowerCase();
}
```

- [ ] **Step 2: Append the table to `server/ddl/f2_api_tables.sql`** (idempotent — `CREATE TABLE IF NOT EXISTS`), directly after the `uq_enroll_slug` guarded-ALTER block:

```sql
-- Facility slug links (design F2-Facility-Slug-Links-2026-07-16): one clean,
-- readable public link per facility — `/f/<slug>` resolves to a facility and
-- self-registers the HCW. Bare slug, no secret; `active` is the soft per-link
-- kill (turn a facility's link off without deleting the row).
CREATE TABLE IF NOT EXISTS f2_facility_slugs (
  slug          VARCHAR(32)  NOT NULL,   -- lowercase ^[a-z0-9][a-z0-9-]{1,30}$
  facility_id   CHAR(9)      NOT NULL,   -- 9-digit PSGC facility code
  facility_name VARCHAR(160) NOT NULL,   -- shown on the StartScreen + written to the case
  active        TINYINT(1)   NOT NULL DEFAULT 1,
  created_at    DATETIME     NULL,
  created_by    VARCHAR(32)  NOT NULL DEFAULT '',
  PRIMARY KEY (slug),
  KEY ix_slug_facility (facility_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

- [ ] **Step 3: Typecheck** — `cd server && npx tsc -b --force` → clean.

---

### Task 2: Server — `FacilitySlugRecord` store methods (InMemory + MySQL)

**Files:**
- Modify: `server/src/admin/store.ts`

**Interfaces:**
- Produces (consumed by Tasks 3, 4):
  - `type FacilitySlugRecord = { slug: string; facility_id: string; facility_name: string; active: boolean; created_at: string; created_by: string }`
  - `AdminStore.upsertFacilitySlug(rec: FacilitySlugRecord): Promise<void>`
  - `AdminStore.listFacilitySlugs(): Promise<FacilitySlugRecord[]>` (newest first)
  - `AdminStore.getFacilitySlug(slug: string): Promise<FacilitySlugRecord | null>` (any active state — callers gate on `.active`)

- [ ] **Step 1: Add the type** after `EnrollLinkRow` (~line 240):

```ts
/** One facility's public link slug (design F2-Facility-Slug-Links-2026-07-16). */
export type FacilitySlugRecord = {
  slug: string;          // lowercase, PK
  facility_id: string;   // 9-digit PSGC facility code
  facility_name: string; // shown on the StartScreen + written to the case
  active: boolean;       // soft on/off without deleting
  created_at: string;    // ISO
  created_by: string;
};
```

- [ ] **Step 2: Extend the `AdminStore` interface** after `markClaimed`:

```ts
  // -- facility slug links (design F2-Facility-Slug-Links-2026-07-16) ----------
  /** Insert or replace a slug row (PK = slug). */
  upsertFacilitySlug(rec: FacilitySlugRecord): Promise<void>;
  /** All slug rows, newest first. */
  listFacilitySlugs(): Promise<FacilitySlugRecord[]>;
  /** Lookup by slug in any active state — callers gate on `.active`. */
  getFacilitySlug(slug: string): Promise<FacilitySlugRecord | null>;
```

- [ ] **Step 3: `InMemoryAdminStore`** — field `facilitySlugs = new Map<string, FacilitySlugRecord>();` + methods after `markClaimed`:

```ts
  // -- facility slug links -----------------------------------------------------
  async upsertFacilitySlug(rec: FacilitySlugRecord) {
    this.facilitySlugs.set(rec.slug, { ...rec });
  }

  async listFacilitySlugs() {
    return newestFirst(
      [...this.facilitySlugs.values()].map((r) => ({ ...r })),
      (r) => r.created_at,
    );
  }

  async getFacilitySlug(slug: string) {
    const r = this.facilitySlugs.get(slug);
    return r ? { ...r } : null;
  }
```

- [ ] **Step 4: `MySqlAdminStore`** — mapper next to `mapDbHcw` and methods after its `markClaimed`:

```ts
function mapDbFacilitySlug(r: Row): FacilitySlugRecord {
  return {
    slug: strOf(r.slug),
    facility_id: strOf(r.facility_id),
    facility_name: strOf(r.facility_name),
    active: boolOf(r.active),
    created_at: dtToIso(r.created_at),
    created_by: strOf(r.created_by),
  };
}
```

```ts
  // -- facility slug links -----------------------------------------------------
  async upsertFacilitySlug(rec: FacilitySlugRecord) {
    await this.pool.query(
      `INSERT INTO f2_facility_slugs (slug, facility_id, facility_name, active, created_at, created_by)
       VALUES (?,?,?,?,?,?)
       ON DUPLICATE KEY UPDATE facility_id=VALUES(facility_id),
         facility_name=VALUES(facility_name), active=VALUES(active)`,
      [rec.slug, rec.facility_id, rec.facility_name, rec.active ? 1 : 0, isoToDt(rec.created_at), rec.created_by],
    );
  }

  async listFacilitySlugs() {
    const rows = await this.q('SELECT * FROM f2_facility_slugs ORDER BY created_at DESC, slug ASC');
    return rows.map(mapDbFacilitySlug);
  }

  async getFacilitySlug(slug: string) {
    const rows = await this.q('SELECT * FROM f2_facility_slugs WHERE slug=? LIMIT 1', [slug]);
    return rows.length ? mapDbFacilitySlug(rows[0]!) : null;
  }
```

- [ ] **Step 5: Typecheck** — `cd server && npx tsc -b --force` → clean (tests come with the routes in Tasks 3–4).

---

### Task 3: Server — public `GET /f/resolve` + `POST /self-register {slug}` branch

**Files:**
- Modify: `server/src/app.ts`
- Test: `server/test/facility-slugs.test.ts` (new — public half), `server/test/static.test.ts` (one line)

**Interfaces:**
- Consumes: Task 1 grammar, Task 2 store methods, existing `mintJwt`/`JwtClaims`/`CLAIM_TOKEN_TTL_DAYS`/`createHcw`/`tokenAudit`/`writeAudit`.
- Produces (frontend contract, Task 6):
  - `GET /f/resolve?slug=<slug>` → `{ ok:true, facility_id, facility_name }` | 404 `E_NOT_FOUND` | 503 `E_UNAVAILABLE`
  - `POST /self-register {slug}` → `{ ok:true, token, hcw_id, qn, facility_id, facility_name }` | 404 | kill-switch envelope. No Authorization header needed on the slug path; a request without `slug` follows the legacy facility-JWT path unchanged.

- [ ] **Step 1: Write the failing tests** — `server/test/facility-slugs.test.ts`:

```ts
/**
 * Facility slug links (design F2-Facility-Slug-Links-2026-07-16) — public half:
 * GET /f/resolve (StartScreen lookup) + POST /self-register {slug} (Start tap →
 * sr- case + facility-block QN + qn-bound device token). Admin management
 * endpoints are covered in admin.test.ts.
 */
import { describe, expect, it } from 'vitest';
import { createApp } from '../src/app.js';
import { InMemoryStore } from '../src/store.js';
import {
  InMemoryAdminStore,
  InMemoryFileStore,
  type FacilitySlugRecord,
} from '../src/admin/store.js';

const KEY = Buffer.from('test-signing-key-32-bytes-long!!').toString('base64url');

const slugRow = (over: Partial<FacilitySlugRecord> = {}): FacilitySlugRecord => ({
  slug: 'lphbay',
  facility_id: '040340210',
  facility_name: 'LPH-Bay District Hospital',
  active: true,
  created_at: '2026-07-16T00:00:00.000Z',
  created_by: 'carl',
  ...over,
});

async function setup(withAdmin = true) {
  const store = new InMemoryStore();
  const adminStore = new InMemoryAdminStore(store);
  const fileStore = new InMemoryFileStore();
  const app = createApp({
    jwtSigningKey: KEY,
    store,
    ...(withAdmin
      ? { admin: { adminStore, fileStore, pwaOrigin: 'https://uhc-hcw.asiansocial.org' } }
      : {}),
  });
  return { app, store, adminStore };
}

const sr = (app: ReturnType<typeof createApp>, slug: string) =>
  app.request('/self-register', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ slug }),
  });

describe('GET /f/resolve', () => {
  it('resolves an active slug to its facility', async () => {
    const { app, adminStore } = await setup();
    await adminStore.upsertFacilitySlug(slugRow());
    const res = await app.request('/f/resolve?slug=lphbay');
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({
      ok: true,
      facility_id: '040340210',
      facility_name: 'LPH-Bay District Hospital',
    });
  });

  it('normalises case — ?slug=LphBay still resolves', async () => {
    const { app, adminStore } = await setup();
    await adminStore.upsertFacilitySlug(slugRow());
    expect((await app.request('/f/resolve?slug=LphBay')).status).toBe(200);
  });

  it('404 E_NOT_FOUND for unknown, inactive, and malformed slugs — same body', async () => {
    const { app, adminStore } = await setup();
    await adminStore.upsertFacilitySlug(slugRow({ slug: 'offbay', active: false }));
    for (const q of ['?slug=nope', '?slug=offbay', '?slug=-bad-', '']) {
      const res = await app.request(`/f/resolve${q}`);
      expect(res.status).toBe(404);
      expect(((await res.json()) as { error: { code: string } }).error.code).toBe('E_NOT_FOUND');
    }
  });

  it('503 when the admin store is absent, and never falls through to the SPA', async () => {
    const { app } = await setup(false);
    expect((await app.request('/f/resolve?slug=lphbay')).status).toBe(503);
  });
});

describe('POST /self-register {slug}', () => {
  it('creates an sr- case in the slug facility QN block and mints a working qn-bound token', async () => {
    const { app, adminStore } = await setup();
    await adminStore.upsertFacilitySlug(slugRow());
    const res = await sr(app, 'lphbay');
    expect(res.status).toBe(200);
    const b = (await res.json()) as {
      ok: boolean; token: string; hcw_id: string; qn: string;
      facility_id: string; facility_name: string;
    };
    expect(b.ok).toBe(true);
    expect(b.hcw_id).toMatch(/^sr-/);
    expect(b.qn).toBe('040340210101');
    expect(b.facility_id).toBe('040340210');
    expect(b.facility_name).toBe('LPH-Bay District Hospital');
    // The token is a real device token: /verify-token accepts it, qn-bound.
    const vt = await app.request('/verify-token', {
      method: 'POST',
      body: JSON.stringify({ token: b.token }),
    });
    expect(vt.status).toBe(200);
    const claims = ((await vt.json()) as { claims: { qn: string; facility_id: string } }).claims;
    expect(claims.qn).toBe('040340210101');
    expect(claims.facility_id).toBe('040340210');
  });

  it('assigns sequential QNs across taps + writes the slug audit + token audit', async () => {
    const { app, adminStore } = await setup();
    await adminStore.upsertFacilitySlug(slugRow());
    const q1 = ((await (await sr(app, 'lphbay')).json()) as { qn: string }).qn;
    const q2 = ((await (await sr(app, 'lphbay')).json()) as { qn: string }).qn;
    expect([q1, q2]).toEqual(['040340210101', '040340210102']);
    const audits = adminStore.auditRows.filter((r) => r.event_type === 'admin_self_register_slug');
    expect(audits).toHaveLength(2);
    expect(audits[0]!.facility_id).toBe('040340210');
    expect(audits[0]!.event_resource).toBe('lphbay');
    expect(adminStore.tokenAudits.filter((t) => t.tablet_label === 'slug lphbay')).toHaveLength(2);
  });

  it('404 E_NOT_FOUND for unknown + inactive slugs (neutral body, nothing created)', async () => {
    const { app, adminStore } = await setup();
    await adminStore.upsertFacilitySlug(slugRow({ active: false }));
    for (const s of ['lphbay', 'nope']) {
      const res = await sr(app, s);
      expect(res.status).toBe(404);
      expect(((await res.json()) as { error: { code: string } }).error.code).toBe('E_NOT_FOUND');
    }
    expect(adminStore.hcws).toHaveLength(0);
  });

  it('kill_switch gates the slug path with the AS envelope (HTTP 200)', async () => {
    const { app, store, adminStore } = await setup();
    await adminStore.upsertFacilitySlug(slugRow());
    store.config.set('kill_switch', 'true');
    const res = await sr(app, 'lphbay');
    expect(res.status).toBe(200);
    expect(((await res.json()) as { error: { code: string } }).error.code).toBe('E_KILL_SWITCH');
  });

  it('a body without slug still follows the legacy facility-JWT path (400 without bearer)', async () => {
    const { app } = await setup();
    const res = await app.request('/self-register', { method: 'POST', body: '{}' });
    expect(res.status).toBe(400);
  });
});
```

- [ ] **Step 2: Run to verify failure** — `cd server && npx vitest run test/facility-slugs.test.ts` → FAIL (routes missing).

- [ ] **Step 3: Implement in `server/src/app.ts`:**
  1. Import: `import { FACILITY_SLUG_RE, normalizeFacilitySlug } from './facility-slugs.js';`
  2. Register `GET /f/resolve` after the `/claim` route (before `/exec`; exact route wins over the later `app.get('*')` static handlers):

```ts
  // Facility slug links (design F2-Facility-Slug-Links-2026-07-16) — public,
  // read-only StartScreen lookup. Exact route: it wins over the /f/<slug> SPA
  // fallback below; "resolve" is a reserved slug. Unknown/inactive/malformed
  // all return the SAME neutral 404 (don't reveal which).
  app.get('/f/resolve', async (c) => {
    const admin = env.admin;
    if (!admin) return c.json(errJson('E_UNAVAILABLE', 'Resolve requires the admin store.'), 503);
    const slug = normalizeFacilitySlug(c.req.query('slug') ?? '');
    const miss = () =>
      c.json(errJson('E_NOT_FOUND', "This survey link isn't active — check with ASPSI ops."), 404);
    if (!FACILITY_SLUG_RE.test(slug)) return miss();
    const rec = await admin.adminStore.getFacilitySlug(slug);
    if (!rec || !rec.active) return miss();
    return c.json({ ok: true, facility_id: rec.facility_id, facility_name: rec.facility_name });
  });
```

  3. Restructure `POST /self-register`: hoist the `admin` guard to the top, parse the body once, branch on `slug`:

```ts
  app.post('/self-register', async (c) => {
    const admin = env.admin;
    if (!admin) {
      return c.json(errJson('E_UNAVAILABLE', 'Self-register requires the admin store.'), 503);
    }
    const body = (await c.req.json().catch(() => ({}))) as { slug?: unknown };
    const slug = typeof body.slug === 'string' ? normalizeFacilitySlug(body.slug) : '';

    // Facility slug path (design F2-Facility-Slug-Links-2026-07-16): the bare
    // public slug names the facility — no credential in the URL. The explicit
    // Start tap POSTs here; the server creates the sr- case, assigns the next
    // QN in the facility block, AND mints a qn-bound device token (same shape
    // as /claim) so the phone drops straight into consent → survey.
    if (slug) {
      const miss = () =>
        c.json(errJson('E_NOT_FOUND', "This survey link isn't active — check with ASPSI ops."), 404);
      if (!FACILITY_SLUG_RE.test(slug)) return miss();
      // kill_switch parity with /exec (HTTP 200 + error envelope).
      if ((await env.store.getConfig('kill_switch')) === 'true') {
        return c.json(errJson('E_KILL_SWITCH', 'Backend is temporarily unavailable'));
      }
      const rec = await admin.adminStore.getFacilitySlug(slug);
      if (!rec || !rec.active) return miss();
      const hcwId = 'sr-' + randomUUID();
      const r = await admin.adminStore.createHcw({
        hcw_id: hcwId,
        facility_id: rec.facility_id,
        facility_name: rec.facility_name,
        status: 'enrolled',
        qn: '',
      });
      if (!r.ok) {
        const status = r.code === 'E_VALIDATION' ? 400 : r.code === 'E_CONFLICT' ? 409 : 502;
        return c.json(errJson(r.code, r.message), status);
      }
      const nowS = Math.floor(Date.now() / 1000);
      const exp = nowS + CLAIM_TOKEN_TTL_DAYS * 86400;
      const jti = randomUUID();
      const claims: JwtClaims = {
        jti,
        tablet_id: randomUUID(),
        facility_id: rec.facility_id,
        iat: nowS,
        exp,
        ...(r.qn ? { qn: r.qn } : {}),
      };
      const token = await mintJwt(claims, env.jwtSigningKey);
      await admin.adminStore.tokenAudit({
        jti,
        tablet_id: claims.tablet_id,
        tablet_label: 'slug ' + slug,
        facility_id: rec.facility_id,
        issued_at: nowS,
        expires_at: exp,
      });
      // Forensic trail: which slug spawned which case (spec: admin_self_register_slug).
      await admin.adminStore.writeAudit({
        event_type: 'admin_self_register_slug',
        hcw_id: r.hcw_id,
        facility_id: rec.facility_id,
        event_resource: slug,
      });
      return c.json({
        ok: true,
        token,
        hcw_id: r.hcw_id,
        qn: r.qn,
        facility_id: rec.facility_id,
        facility_name: rec.facility_name,
      });
    }

    // Legacy facility-JWT path (facility-QR handout) — unchanged below, minus
    // its own (now hoisted) admin-store guard.
    …existing token verification / kill_switch / createHcw / response…
  });
```

  4. `server/test/static.test.ts`: add `'/f/lphbay'` to the deep-link fallback list in the `#528` test.

- [ ] **Step 4: Run tests** — `npx vitest run test/facility-slugs.test.ts test/self-register.test.ts test/static.test.ts` → PASS (legacy suite must stay green untouched).

---

### Task 4: Server — admin `GET|POST /admin/api/facility-slugs`

**Files:**
- Modify: `server/src/admin/routes.ts` (insert before the `admin.all('*')` 404 catch-all)
- Test: `server/test/admin.test.ts` (new describe block)

**Interfaces:**
- Consumes: Tasks 1–2; existing `gate`/`auditMutation`/`errBody`/`env.pwaOrigin`.
- Produces (admin frontend contract, Task 5):
  - `GET /admin/api/facility-slugs` (gate `dash_users`) → `{ slugs: Array<FacilitySlugRecord & { url: string }> }`
  - `POST /admin/api/facility-slugs` (gate `dash_users`) body `{ slug, facility_id, facility_name, active? }` → `{ ok:true, slug, facility_id, facility_name, active, url }`; 400 `E_VALIDATION` on bad slug/facility/name; audit `admin_facility_slug_upsert`.

- [ ] **Step 1: Write the failing tests** — append to `server/test/admin.test.ts`:

```ts
describe('admin facility slug links (design F2-Facility-Slug-Links-2026-07-16)', () => {
  const upsert = (app: Hono, token: string, body: Record<string, unknown>) =>
    app.request(
      '/admin/api/facility-slugs',
      authed(token, { method: 'POST', body: JSON.stringify(body) }),
    );

  it('upserts a slug (lowercased) and lists it with the public /f/ URL', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const res = await upsert(app, token, {
      slug: 'LphBay',
      facility_id: '040340210',
      facility_name: 'LPH-Bay District Hospital',
    });
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({
      ok: true,
      slug: 'lphbay',
      active: true,
      url: 'https://uhc-hcw.asiansocial.org/f/lphbay',
    });
    const list = await app.request('/admin/api/facility-slugs', authed(token));
    const rows = ((await list.json()) as { slugs: Array<{ slug: string; url: string }> }).slugs;
    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({ slug: 'lphbay', url: 'https://uhc-hcw.asiansocial.org/f/lphbay' });
  });

  it('re-upsert updates name/active but keeps created_at/created_by', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    await upsert(app, token, { slug: 'lphbay', facility_id: '040340210', facility_name: 'Old' });
    const first = await adminStore.getFacilitySlug('lphbay');
    await upsert(app, token, { slug: 'lphbay', facility_id: '040340210', facility_name: 'New', active: false });
    const second = await adminStore.getFacilitySlug('lphbay');
    expect(second).toMatchObject({
      facility_name: 'New',
      active: false,
      created_at: first!.created_at,
      created_by: first!.created_by,
    });
    // The public surfaces now refuse it.
    expect((await app.request('/f/resolve?slug=lphbay')).status).toBe(404);
  });

  it('validates slug grammar, the reserved name, facility_id, and facility_name', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const bad = [
      { slug: '-bad', facility_id: '040340210', facility_name: 'X' },
      { slug: 'has space', facility_id: '040340210', facility_name: 'X' },
      { slug: 'resolve', facility_id: '040340210', facility_name: 'X' },
      { slug: 'lphbay', facility_id: '123', facility_name: 'X' },
      { slug: 'lphbay', facility_id: '040340210', facility_name: '' },
    ];
    for (const b of bad) {
      const res = await upsert(app, token, b);
      expect(res.status).toBe(400);
      expect(await errCode(res)).toBe('E_VALIDATION');
    }
  });

  it('gates on dash_users and audits the upsert', async () => {
    const { app, adminStore } = await setup();
    adminStore.roles.set('Viewer', role({ name: 'Viewer', is_builtin: false, dash_users: false }));
    adminStore.users.set('viewer', user({ username: 'viewer', role_name: 'Viewer' }));
    const viewerToken = await loginToken(app, 'viewer');
    expect(
      (await upsert(app, viewerToken, { slug: 'x1', facility_id: '040340210', facility_name: 'X' })).status,
    ).toBe(403);
    expect((await app.request('/admin/api/facility-slugs', authed(viewerToken))).status).toBe(403);
    const token = await loginToken(app);
    await upsert(app, token, { slug: 'lphbay', facility_id: '040340210', facility_name: 'LPH-Bay' });
    const audits = adminStore.auditRows.filter((r) => r.event_type === 'admin_facility_slug_upsert');
    expect(audits).toHaveLength(1);
    expect(audits[0]!.event_resource).toBe('lphbay→040340210');
  });

  it('end-to-end: admin upsert → public resolve → Start-tap self-register at that facility', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    await upsert(app, token, { slug: 'lphbay', facility_id: '040340210', facility_name: 'LPH-Bay' });
    expect((await app.request('/f/resolve?slug=lphbay')).status).toBe(200);
    const reg = await app.request('/self-register', {
      method: 'POST',
      body: JSON.stringify({ slug: 'lphbay' }),
    });
    expect(reg.status).toBe(200);
    const b = (await reg.json()) as { qn: string; token: string };
    expect(b.qn).toBe('040340210101');
    expect(typeof b.token).toBe('string');
  });
});
```

- [ ] **Step 2: Run to verify failure** — `npx vitest run test/admin.test.ts` → new block FAILS, everything else green.

- [ ] **Step 3: Implement in `server/src/admin/routes.ts`:**
  1. Import: `import { FACILITY_SLUG_RE, normalizeFacilitySlug, RESERVED_FACILITY_SLUGS } from '../facility-slugs.js';`
  2. Routes before the catch-all:

```ts
  // ----- facility slug links (design F2-Facility-Slug-Links-2026-07-16) ------
  // One public link per facility: /f/<slug>. Upsert-only management — renaming
  // a facility's link = upsert the new slug, then toggle the old row inactive.
  // dash_users gate, same as facility-links / HCW create.

  admin.get('/facility-slugs', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const rows = await env.adminStore.listFacilitySlugs();
    return c.json({ slugs: rows.map((r) => ({ ...r, url: `${env.pwaOrigin}/f/${r.slug}` })) });
  });

  admin.post('/facility-slugs', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as {
      slug?: unknown; facility_id?: unknown; facility_name?: unknown; active?: unknown;
    };
    const slug = typeof body.slug === 'string' ? normalizeFacilitySlug(body.slug) : '';
    const facilityId = typeof body.facility_id === 'string' ? body.facility_id.trim() : '';
    const facilityName = typeof body.facility_name === 'string' ? body.facility_name.trim() : '';
    const active = body.active !== false; // default true
    if (!FACILITY_SLUG_RE.test(slug) || RESERVED_FACILITY_SLUGS.has(slug)) {
      return c.json(
        errBody('E_VALIDATION', 'slug must be 2-31 chars of a-z 0-9 hyphen, not "resolve"'),
        400,
      );
    }
    if (!/^\d{9}$/.test(facilityId)) {
      return c.json(errBody('E_VALIDATION', 'facility_id must be a real 9-digit facility code'), 400);
    }
    if (!facilityName || facilityName.length > 160) {
      return c.json(errBody('E_VALIDATION', 'facility_name is required (max 160 chars)'), 400);
    }
    // Upsert keeps the original provenance (created_at/created_by survive edits).
    const existing = await env.adminStore.getFacilitySlug(slug);
    await env.adminStore.upsertFacilitySlug({
      slug,
      facility_id: facilityId,
      facility_name: facilityName,
      active,
      created_at: existing?.created_at || new Date().toISOString(),
      created_by: existing?.created_by || g.payload.sub,
    });
    const res = c.json({
      ok: true,
      slug,
      facility_id: facilityId,
      facility_name: facilityName,
      active,
      url: `${env.pwaOrigin}/f/${slug}`,
    });
    auditMutation(c, res, g.payload, 'admin_facility_slug_upsert', `${slug}→${facilityId}`);
    return res;
  });
```

- [ ] **Step 4: Full server suite** — `npx vitest run` → all green (was 81; now 81 + new). `npx tsc -b --force` + `npx eslint .` clean.

---

### Task 5: Admin UI — "Facility link" modal + HCWs-tab wiring

**Files:**
- Create: `app/src/admin/data/FacilitySlugModal.tsx`
- Test: `app/src/admin/data/FacilitySlugModal.test.tsx`
- Modify: `app/src/admin/data/HCWsTab.tsx` (buttons + modal state)

**Interfaces:**
- Consumes: Task 4 endpoints; existing `adminFetch`, `useAdminAuth`, `useRouter`, `QRCodeSVG` (qrcode.react, already a dep), `Button`.
- Produces: `FacilitySlugModal({ apiBaseUrl, fetchImpl?, defaultFacilityId?, onClose })`.

- [ ] **Step 1: Component** — same dialog scaffold/classes as `FacilityLinksModal` (Verde Manual: hairlines, mono microcopy, no cards). Behaviour:
  - On mount: `GET /admin/api/facility-slugs` → list.
  - Form: slug (lowercase live-normalised), facility ID (9-digit), facility name → Save → `POST` → on success re-load the list and show the saved link as a "hero" block: full `/f/<slug>` URL + `<QRCodeSVG value={url} size={160} />` + Copy + Print (`window.print()`).
  - List rows: slug · facility · active badge → actions: Copy URL, Activate/Deactivate (re-POST with `active` flipped, other fields unchanged from the row).
  - Errors via the shared `ApiError` mapping (reuse the `messageFor` pattern: `E_VALIDATION`, `E_PERM_DENIED`, `E_NETWORK`, `E_BACKEND`).
  - data-testids: `slug-input`, `facility-id-input`, `facility-name-input`, `slug-save`, `slug-url`, `slug-qr`, `slug-row-<slug>`, `slug-toggle-<slug>`, `slug-copy-<slug>`, `slug-error`.

- [ ] **Step 2: Tests (write first, then the component until green):**

```tsx
// FacilitySlugModal.test.tsx — mock fetchImpl; assert:
// 1. mount lists existing slugs from GET /admin/api/facility-slugs
// 2. Save POSTs {slug (lowercased), facility_id, facility_name} and renders url + QR
// 3. invalid form (bad slug / bad facility id / empty name) keeps Save disabled
// 4. Deactivate re-POSTs the row with active:false
// 5. E_PERM_DENIED renders the role-lacks message
```
(Full test code mirrors `ClaimScreen.test.tsx` + `ResponsesTab.test.tsx` conventions: `vi.fn()` fetch returning `Response.json(...)`, `render` with required providers — the modal needs `AdminAuthProvider`-equivalent stubbing exactly as `ResponsesTab.test.tsx` does.)

- [ ] **Step 3: `HCWsTab.tsx`** — add `const [slugOpen, setSlugOpen] = useState(false);`; button row becomes: **"Facility link"** (opens `FacilitySlugModal`, title "One public self-register link per facility — /f/<slug>") · **"Numbered links (legacy)"** (existing `FacilityLinksModal`, unchanged behaviour) · **"+ Create HCW"**. Render both modals conditionally, `defaultFacilityId` prefilled from the facility filter for both.

- [ ] **Step 4: Run** — `cd app && npx vitest run src/admin/data/FacilitySlugModal.test.tsx` → PASS.

---

### Task 6: PWA — `facility-start-client.ts` + `FacilityStartScreen` + routing + i18n

**Files:**
- Create: `app/src/lib/facility-start-client.ts`, `app/src/components/enrollment/FacilityStartScreen.tsx`
- Test: `app/src/lib/facility-start-client.test.ts`, `app/src/components/enrollment/FacilityStartScreen.test.tsx`, `app/src/App.test.tsx` (routing updates)
- Modify: `app/src/App.tsx`, `app/src/i18n/locales/{en,fil,bcl,bis,ceb,hil,ilo,war}.ts`

**Interfaces:**
- Consumes: Task 3 endpoints; `useAuth().enroll` (same call shape as `ClaimScreen`), `getSyncEnv`.
- Produces:
  - `parseFacilityUrl(loc: { pathname: string }): { slug: string } | null`
  - `resolveFacilitySlug({ proxyUrl, slug, fetchImpl })` → `{ ok:true, facility_id, facility_name } | { ok:false, transport, error }`
  - `selfRegisterBySlug({ proxyUrl, slug, fetchImpl })` → `{ ok:true, token, hcw_id, qn, facility_id, facility_name } | { ok:false, transport, error }`
  - `<FacilityStartScreen />` — self-contained (reads `window.location`), enrolls on Start.

- [ ] **Step 1: `facility-start-client.ts`** — same fetch/envelope discipline as `claim-client.ts` (transport vs HTTP vs kill-switch envelope), plus:

```ts
/** Parse `/f/<slug>` from the current location. null when not a facility URL. */
export function parseFacilityUrl(loc: { pathname: string }): { slug: string } | null {
  const m = /^\/f\/([a-z0-9][a-z0-9-]{1,30})\/?$/i.exec(loc.pathname);
  if (!m) return null;
  const slug = m[1]!.toLowerCase();
  return slug === 'resolve' ? null : { slug };
}
```

- [ ] **Step 2: `FacilityStartScreen.tsx`** — phases `resolving | ready | starting | error`; mount-guarded resolve (StrictMode `ran` ref, like `ClaimScreen`); Start button → `selfRegisterBySlug` → `enroll({ hcw_id, facility_id, ...(qn ? { qn } : {}), device_token: token })`; error mapping `E_NETWORK→offline`, `E_KILL_SWITCH→unavailable`, `E_NOT_FOUND→inactive`, else `inactive`; Retry re-resolves. data-testids: `facility-start-progress`, `facility-start-name`, `facility-start-button`, `facility-start-error`, `facility-start-retry`. Copy from the `facilityStart` i18n block; layout mirrors `ClaimScreen` (max-w-md section, serif heading, muted body).

- [ ] **Step 3: i18n** — `en.ts` gets (verbatim copy below); the 7 other locales get the same keys with English fallback values + the standard "translations pending" comment:

```ts
  facilityStart: {
    resolvingHeading: 'Opening the survey…',
    resolving: 'Checking this link — one moment.',
    heading: '{{facility}} — HCW Survey',
    intro: 'Your answers are voluntary and anonymous. Tap Start to begin on this phone.',
    start: 'Start the survey',
    starting: 'Setting up your questionnaire…',
    inactive: "This survey link isn't active. Please check with ASPSI ops.",
    offline: "You're offline. Check your connection and tap Retry.",
    unavailable: 'The survey is temporarily unavailable. Please try again shortly.',
    retry: 'Retry',
    noLinkHeading: 'Open your facility survey link',
    noLinkBody:
      'This survey opens from a facility link that looks like uhc-hcw.asiansocial.org/f/your-facility. Ask ASPSI staff for your facility link.',
  },
```

- [ ] **Step 4: `App.tsx` routing** — compute once per load next to `claimTarget`:

```ts
  const facilityTarget = typeof window !== 'undefined' ? parseFacilityUrl(window.location) : null;
  const legacyEnroll = typeof window !== 'undefined' && window.location.pathname.startsWith('/enroll');
```

Unenrolled branch becomes (precedence `/e/` → `/f/` → `/enroll` → no-link message):

```tsx
      ) : authStatus === 'unenrolled' ? (
        claimTarget ? (
          <ClaimScreen />
        ) : facilityTarget ? (
          <FacilityStartScreen />
        ) : legacyEnroll ? (
          <EnrollmentScreen />
        ) : (
          <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
            <h2 className="font-serif text-2xl font-medium tracking-tight">
              {t('facilityStart.noLinkHeading')}
            </h2>
            <p className="text-sm text-muted-foreground">{t('facilityStart.noLinkBody')}</p>
          </section>
        )
      ) : view === 'sync' ? (
```

- [ ] **Step 5: Tests**
  - `facility-start-client.test.ts`: parse (hit, trailing slash, case-fold, `/f/resolve` → null, non-/f/ → null); resolve + selfRegister envelope handling (ok / HTTP 404 / network throw / kill-switch 200-with-error).
  - `FacilityStartScreen.test.tsx` (model: `ClaimScreen.test.tsx`): resolves on mount and shows facility name + Start; Start → self-register → `db.enrollment` singleton has token/qn/facility; inactive (E_NOT_FOUND) shows inactive copy without a Start button; offline error + Retry re-resolves; no server call when the path is not a valid slug.
  - `App.test.tsx`: update "renders the EnrollmentScreen when no enrollment row exists" to set the URL to `/enroll` first (`window.history.pushState({}, '', '/enroll')`) and add: `/f/lphbay` (unenrolled) renders the facility start progress; `/` (unenrolled) renders the no-link heading; also reset the URL to `/` in `beforeEach` so existing tests keep passing.

- [ ] **Step 6: Run** — `npx vitest run src/lib/facility-start-client.test.ts src/components/enrollment/FacilityStartScreen.test.tsx src/App.test.tsx` → PASS.

---

### Task 7: PWA — sync-on-submit delivery gate (`DeliveryStatus`)

**Files:**
- Create: `app/src/components/sync/DeliveryStatus.tsx`
- Test: `app/src/components/sync/DeliveryStatus.test.tsx`
- Modify: `app/src/App.tsx` (thank-you body), `app/src/i18n/locales/*.ts` (4 chrome keys)

**Interfaces:**
- Consumes: `db.submissions` row states (`pending_sync | syncing | retry_scheduled | synced | rejected`), `COMPLETED_CSID_KEY`, Dexie `liveQuery`.
- Produces: `<DeliveryStatus />` — drop-in replacement for the static thank-you body line.

- [ ] **Step 1: i18n (en, mirrored to the 7 others as English fallback):**

```ts
    // Sync-on-submit delivery gate (design F2-Facility-Slug-Links-2026-07-16):
    delivering: 'Submitting…',
    deliveredBody: 'Submitted ✓ — your response is in. You can close this page.',
    deliveryOffline: 'Saved on this phone — it will send automatically when you are back online.',
    deliveryFailed:
      'Your response is saved on this device but could not be sent automatically. Please show this screen to ASPSI staff.',
```

- [ ] **Step 2: Component:**

```tsx
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { liveQuery } from 'dexie';
import { db } from '@/lib/db';
import { COMPLETED_CSID_KEY } from '@/lib/draft';

/**
 * Delivery gate for the thank-you screen (design F2-Facility-Slug-Links-2026-07-16,
 * "Sync-on-submit"). The self-register device is one-and-done — nobody runs a
 * manual sync — so make delivery VISIBLE: "Submitting…" until the server ack
 * lands in Dexie (status flips to 'synced' via the immediate post-submit sync),
 * then "Submitted ✓ — you can close this". Offline: the queued row + the
 * on-reconnect trigger deliver it, and the copy says so.
 */
export function DeliveryStatus() {
  const { t } = useTranslation();
  const [rowStatus, setRowStatus] = useState<string | null>(null);
  const [online, setOnline] = useState(typeof navigator === 'undefined' ? true : navigator.onLine);
  const csid = typeof localStorage !== 'undefined' ? localStorage.getItem(COMPLETED_CSID_KEY) : null;

  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => {
      window.removeEventListener('online', on);
      window.removeEventListener('offline', off);
    };
  }, []);

  useEffect(() => {
    if (!csid) return;
    const sub = liveQuery(() => db.submissions.get(csid)).subscribe({
      next: (row) => setRowStatus(row ? row.status : 'missing'),
      error: () => setRowStatus(null),
    });
    return () => sub.unsubscribe();
  }, [csid]);

  // No csid (pre-gate sessions) or Dexie unavailable → the original static line.
  if (!csid || rowStatus === null || rowStatus === 'missing') {
    return <p className="text-sm text-muted-foreground">{t('chrome.thankYouBody')}</p>;
  }
  if (rowStatus === 'synced') {
    return (
      <p data-testid="delivery-status" className="text-sm font-medium text-signal">
        {t('chrome.deliveredBody')}
      </p>
    );
  }
  if (rowStatus === 'rejected') {
    return (
      <p data-testid="delivery-status" className="text-sm text-destructive">
        {t('chrome.deliveryFailed')}
      </p>
    );
  }
  // pending_sync | retry_scheduled | syncing — delivery is in flight or queued.
  return (
    <p data-testid="delivery-status" className="text-sm text-muted-foreground">
      {online ? t('chrome.delivering') : t('chrome.deliveryOffline')}
    </p>
  );
}
```

- [ ] **Step 3: `App.tsx`** — in the `status === 'submitted'` section replace `<p className="text-sm text-muted-foreground">{t('chrome.thankYouBody')}</p>` with `<DeliveryStatus />` (+ import).

- [ ] **Step 4: Tests** — `DeliveryStatus.test.tsx` (fake-indexeddb already in the vitest setup):
  1. pending row + online → "Submitting…"
  2. row updated to `synced` → flips live to the ✓ copy (liveQuery reactivity)
  3. pending row + `navigator.onLine=false` (defineProperty + `offline` event) → saved-offline copy
  4. `rejected` → failed copy
  5. no `COMPLETED_CSID_KEY` → falls back to `chrome.thankYouBody`

- [ ] **Step 5: Run** — `npx vitest run src/components/sync/DeliveryStatus.test.tsx src/App.test.tsx` → PASS.

---

### Task 8: Full verification

- [ ] `cd server && npx vitest run` → all green
- [ ] `cd server && npx tsc -b --force && npx eslint .` → clean
- [ ] `cd app && npx vitest run` → all green (528 + new)
- [ ] `cd app && npx tsc -b --force && npx eslint .` → clean
- [ ] `cd app && npm run build` → production build clean (bundle-secrets / budget / contrast checks pass; QR + new screens ride the existing chunks)
- [ ] Ultracode adversarial review of the full diff (Workflow: multi-lens finders → refuting verifiers with OUTPUT DISCIPLINE + required `line_or_symbol`), fix confirmed findings, re-run affected suites.

### Task 9: Deploy + migrate (cut over now — spec "Migration")

- [ ] Deploy backend + DDL + frontend via `pretest-2026-07-16/deploy_model_c_full.sh` (standing autodeploy for the active UAT round; DDL is additive/idempotent; frontend live-swaps `/opt/app/f2-www`).
- [ ] Create the first slug via the real admin endpoint (script modeled on `link_regen.mjs`, se_001 login, password from `pretest-users.csv` — never printed): `POST /admin/api/facility-slugs {slug:'lphbay', facility_id:'040340210', facility_name:'LPH-Bay District Hospital'}`.
- [ ] Smoke: `GET /f/resolve?slug=lphbay` → 200 + facility JSON; `GET /f/lphbay` → SPA HTML; `GET /f/resolve?slug=nope` → 404 JSON; legacy `/claim` still 401-gated.
- [ ] Announce `uhc-hcw.asiansocial.org/f/lphbay` to `#f2-pwa-uat` (replaces the numbered cards; the 25 printed cards keep working as fallback). Carl relays to Viber.
- [ ] Update the design doc status → DEPLOYED; update memory (`project_aspsi_f2_model_c_numbered_links` + PWA state).

## Self-Review

- **Spec coverage:** slug table ✔ (T1), resolve ✔ (T3), self-register slug branch + token mint + audit ✔ (T3), admin surface + legacy affordance ✔ (T4–T5), StartScreen + routing + i18n ✔ (T6), no-link default + `/enroll` legacy ✔ (T6), delivery gate ✔ (T7), migration/cut-over ✔ (T9), `/claim` untouched ✔.
- **Placeholders:** Task 5 Step 2 test code is summarized by contract (5 named behaviours) rather than inline — acceptable because the executing agent is the plan author with the modal conventions in context; all other steps carry complete code.
- **Type consistency:** `FacilitySlugRecord` field names match DDL columns; client response types match server JSON keys (`facility_name` included in self-register response); `parseFacilityUrl` regex = server `FACILITY_SLUG_RE` + case-fold.
