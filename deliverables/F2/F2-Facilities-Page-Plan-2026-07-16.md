# F2 Admin — Facilities Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Project override:** no git commit steps — Carl handles git manually.

**Goal:** A read-only facility master list under Operate → Facilities where admins create/manage each facility's `/f/<slug>` link and watch live counts.

**Architecture:** One new composite read endpoint (`GET /admin/api/facilities` — master LEFT JOIN slugs LEFT JOIN count aggregates, Approach A); all writes reuse the existing `POST /admin/api/facility-slugs` upsert. New admin page + dialog; QN column rides along on the Responses tab; the interim `FacilitySlugModal` is removed from the HCWs tab.

**Tech Stack:** Hono + mysql2 (server), React + TS + qrcode.react (admin app), Vitest both sides.

**Spec:** `deliverables/F2/F2-Facilities-Page-Spec-2026-07-16.md` (approved 2026-07-16, Approach A). Diagram: `F2-Facilities-Page-Design-2026-07-16.png`.

## Global Constraints

- Facility master is READ-ONLY — no write path to `f2_facility_master` anywhere.
- Slug grammar `^[a-z0-9][a-z0-9-]{1,30}$`, reserved `resolve` (shared with the live slug-links feature).
- Counts: `submitted` = `f2_responses.status <> 'refusal'`; `refusals` = `= 'refusal'`; `in_progress` = `f2_hcws` with `hcw_id LIKE 'sr-%' AND status='enrolled'` (numbered-link slots deliberately excluded).
- Gate everything on `dash_users`. Standard admin envelope + `auditMutation` conventions.
- Page loads with `limit=500` (server `MAX_LIMIT` is 500); sort `region, province, facility_name` ASC.
- **No DDL.** No git commits. `tsc -b --force` before any push. Codebase: staging worktree `deliverables/F2/PWA/{server,app}`.

---

### Task 1: Server — `listFacilitiesOverview` + `GET /admin/api/facilities`

**Files:**
- Modify: `server/src/admin/store.ts` (types + interface + InMemory + MySQL impls)
- Modify: `server/src/admin/routes.ts` (route before the `admin.all('*')` catch-all)
- Test: `server/test/facilities-overview.test.ts` (new)

**Interfaces:**
- Consumes: `InMemoryStore.facilities: FacilityRow[]` (public), `base.responses` map, `hcws` array, `facilitySlugs` map; `Paged<T>`, `newestFirst`, `page`, `normLimit`, `normOffset`, `strOf`, `boolOf`, `gate`, `errBody`, `env.pwaOrigin`.
- Produces (frontend contract, Tasks 3–4):
  - `type FacilityOverviewRow = { facility_id; facility_name; facility_type; region; province; city_mun: string; slug: string; active: boolean | null; submitted; refusals; in_progress: number }`
  - `AdminStore.listFacilitiesOverview(f: FacilityOverviewFilters): Promise<Paged<FacilityOverviewRow>>`
  - `GET /admin/api/facilities?q&region&province&facility_type&has_link&limit&offset` → `{ rows: Array<FacilityOverviewRow & { url: string }>, total, has_more }` (`url:''` when no slug).

- [ ] **Step 1: Write the failing tests** — `server/test/facilities-overview.test.ts`:

```ts
/**
 * Facilities page composite read (spec F2-Facilities-Page-2026-07-16, Approach A):
 * every master row appears (LEFT JOIN), slug/active/url ride along, counts follow
 * the spec definitions, filters + paging behave like the other admin lists.
 */
import { describe, expect, it } from 'vitest';
import type { Hono } from 'hono';
import { createApp } from '../src/app.js';
import { hashPassword } from '../src/admin/auth.js';
import {
  InMemoryAdminStore,
  InMemoryFileStore,
  type AdminRoleRecord,
  type AdminUserRecord,
} from '../src/admin/store.js';
import { InMemoryStore, type FacilityRow, type ResponseRow } from '../src/store.js';

const KEY = Buffer.from('test-signing-key-32-bytes-long!!').toString('base64url');
const PASSWORD = 'correct-horse-9';
const PASS_HASH = await hashPassword(PASSWORD);

const role = (over: Partial<AdminRoleRecord> = {}): AdminRoleRecord => ({
  name: 'Administrator', is_builtin: true, version: 1,
  dash_data: true, dash_report: true, dash_apps: true, dash_users: true, dash_roles: true,
  dict_self_admin_up: true, dict_self_admin_down: true, dict_paper_encoded_up: true,
  dict_paper_encoded_down: true, dict_capi_up: true, dict_capi_down: true,
  created_at: '2026-01-01T00:00:00.000Z', created_by: 'seed', ...over,
});
const user = (over: Partial<AdminUserRecord> = {}): AdminUserRecord => ({
  username: 'carl', first_name: 'Carl', last_name: 'Reyes', role_name: 'Administrator',
  password_hash: PASS_HASH, password_must_change: false, email: '', phone: '',
  created_at: '2026-01-02T00:00:00.000Z', created_by: 'seed', last_login_at: '', ...over,
});

const facility = (over: Partial<FacilityRow> = {}): FacilityRow => ({
  facility_id: '040340210', facility_name: 'LPH-Bay District Hospital',
  facility_type: 'Hospital', region: 'Region V', province: 'Albay',
  city_mun: 'Bay', barangay: '', ...over,
});

const resp = (over: Partial<ResponseRow> = {}): ResponseRow => ({
  submission_id: 's-' + Math.random().toString(36).slice(2), client_submission_id: 'c-' + Math.random().toString(36).slice(2),
  submitted_at_server: '2026-07-16T00:00:00.000Z', submitted_at_client: '', source: 'PWA',
  spec_version: 'v', app_version: '1', hcw_id: 'sr-x', facility_id: '040340210',
  device_fingerprint: '', sync_attempt_count: '1', status: 'stored', values_json: '{}',
  submission_lat: '', submission_lng: '', source_path: 'self_admin', encoded_by: '',
  encoded_at: '', qn: '', ...over,
});

async function setup() {
  const store = new InMemoryStore();
  const adminStore = new InMemoryAdminStore(store);
  const fileStore = new InMemoryFileStore();
  adminStore.roles.set('Administrator', role());
  adminStore.users.set('carl', user());
  const app = createApp({
    jwtSigningKey: KEY, store,
    admin: { adminStore, fileStore, pwaOrigin: 'https://uhc-hcw.asiansocial.org' },
  });
  return { app, store, adminStore };
}

async function loginToken(app: Hono): Promise<string> {
  const res = await app.request('/admin/api/login', {
    method: 'POST', body: JSON.stringify({ username: 'carl', password: PASSWORD }),
  });
  expect(res.status).toBe(200);
  return ((await res.json()) as { token: string }).token;
}
const authed = (token: string): RequestInit => ({ headers: { Authorization: `Bearer ${token}` } });
const list = async (app: Hono, token: string, qs = '') => {
  const res = await app.request(`/admin/api/facilities${qs}`, authed(token));
  expect(res.status).toBe(200);
  return (await res.json()) as {
    rows: Array<Record<string, unknown>>; total: number; has_more: boolean;
  };
};

describe('GET /admin/api/facilities (composite overview)', () => {
  it('lists every master row — link-less facilities appear with empty slug/url and null active', async () => {
    const { app, store } = await setup();
    store.facilities.push(facility(), facility({ facility_id: '040341130', facility_name: 'RHU Daraga I', facility_type: 'RHU', city_mun: 'Daraga' }));
    const token = await loginToken(app);
    const b = await list(app, token);
    expect(b.total).toBe(2);
    const daraga = b.rows.find((r) => r.facility_id === '040341130')!;
    expect(daraga).toMatchObject({ slug: '', url: '', active: null, submitted: 0, refusals: 0, in_progress: 0 });
  });

  it('joins the slug + composes the public url; counts follow the spec definitions', async () => {
    const { app, store, adminStore } = await setup();
    store.facilities.push(facility());
    await adminStore.upsertFacilitySlug({
      slug: 'lphbay', facility_id: '040340210', facility_name: 'LPH-Bay District Hospital',
      active: true, created_at: '2026-07-16T00:00:00.000Z', created_by: 'carl',
    });
    // 2 stored + 1 refusal responses; sr- enrolled (counts), sr- submitted (not),
    // numbered-slot enrolled (not — sr- only).
    store.responses.set('a', resp());
    store.responses.set('b', resp());
    store.responses.set('c', resp({ status: 'refusal' }));
    await adminStore.createHcw({ hcw_id: 'sr-going', facility_id: '040340210', facility_name: '', status: 'enrolled', qn: '' });
    await adminStore.createHcw({ hcw_id: 'sr-done', facility_id: '040340210', facility_name: '', status: 'enrolled', qn: '' });
    adminStore.hcws.find((h) => h.hcw_id === 'sr-done')!.status = 'submitted';
    await adminStore.createHcw({ hcw_id: 'slot-01', facility_id: '040340210', facility_name: '', status: 'enrolled', qn: '' });
    const token = await loginToken(app);
    const row = (await list(app, token)).rows[0]!;
    expect(row).toMatchObject({
      slug: 'lphbay', active: true, url: 'https://uhc-hcw.asiansocial.org/f/lphbay',
      submitted: 2, refusals: 1, in_progress: 1,
    });
  });

  it('filters: q (name or id substring), region, facility_type, has_link', async () => {
    const { app, store, adminStore } = await setup();
    store.facilities.push(
      facility(),
      facility({ facility_id: '040341130', facility_name: 'RHU Daraga I', facility_type: 'RHU', province: 'Albay' }),
      facility({ facility_id: '051720003', facility_name: 'Bicol Medical Center', region: 'Region V', province: 'Camarines Sur' }),
    );
    await adminStore.upsertFacilitySlug({
      slug: 'lphbay', facility_id: '040340210', facility_name: 'LPH-Bay District Hospital',
      active: true, created_at: '2026-07-16T00:00:00.000Z', created_by: 'carl',
    });
    const token = await loginToken(app);
    expect((await list(app, token, '?q=daraga')).total).toBe(1);
    expect((await list(app, token, '?q=051720003')).total).toBe(1);
    expect((await list(app, token, '?facility_type=RHU')).total).toBe(1);
    expect((await list(app, token, '?province=Camarines%20Sur')).total).toBe(1);
    expect((await list(app, token, '?has_link=true')).total).toBe(1);
    expect((await list(app, token, '?has_link=false')).total).toBe(2);
  });

  it('sorts region/province/name ASC and pages with the standard shape', async () => {
    const { app, store } = await setup();
    store.facilities.push(
      facility({ facility_id: '2', facility_name: 'Zeta', region: 'Region V', province: 'Albay' }),
      facility({ facility_id: '1', facility_name: 'Alpha', region: 'Region V', province: 'Albay' }),
      facility({ facility_id: '3', facility_name: 'Mid', region: 'Region IV-A', province: 'Laguna' }),
    );
    const token = await loginToken(app);
    const b = await list(app, token, '?limit=2');
    expect(b.rows.map((r) => r.facility_name)).toEqual(['Mid', 'Alpha']);
    expect(b.has_more).toBe(true);
    expect((await list(app, token, '?limit=2&offset=2')).rows.map((r) => r.facility_name)).toEqual(['Zeta']);
  });

  it('dedups to ONE slug row per facility — prefers active, then newest', async () => {
    const { app, store, adminStore } = await setup();
    store.facilities.push(facility());
    await adminStore.upsertFacilitySlug({
      slug: 'lphbay-old', facility_id: '040340210', facility_name: 'LPH-Bay District Hospital',
      active: false, created_at: '2026-07-15T00:00:00.000Z', created_by: 'carl',
    });
    await adminStore.upsertFacilitySlug({
      slug: 'lphbay', facility_id: '040340210', facility_name: 'LPH-Bay District Hospital',
      active: true, created_at: '2026-07-16T00:00:00.000Z', created_by: 'carl',
    });
    const token = await loginToken(app);
    const b = await list(app, token);
    expect(b.total).toBe(1);
    expect(b.rows[0]).toMatchObject({ slug: 'lphbay', active: true });
  });

  it('gates on dash_users', async () => {
    const { app, adminStore } = await setup();
    adminStore.roles.set('Viewer', role({ name: 'Viewer', is_builtin: false, dash_users: false }));
    adminStore.users.set('viewer', user({ username: 'viewer', role_name: 'Viewer' }));
    const res = await app.request('/admin/api/login', {
      method: 'POST', body: JSON.stringify({ username: 'viewer', password: PASSWORD }),
    });
    const viewerToken = ((await res.json()) as { token: string }).token;
    expect((await app.request('/admin/api/facilities', authed(viewerToken))).status).toBe(403);
  });
});
```

- [ ] **Step 2: Run to verify failure** — `cd server && npx vitest run test/facilities-overview.test.ts` → FAIL (`listFacilitiesOverview`/route missing).

- [ ] **Step 3: Types + interface** in `server/src/admin/store.ts` (after `FacilitySlugRecord`):

```ts
/** One Facilities-page row: master + its (deduped) slug + live counts. */
export type FacilityOverviewRow = {
  facility_id: string;
  facility_name: string;
  facility_type: string;
  region: string;
  province: string;
  city_mun: string;
  slug: string; // '' when the facility has no link yet
  active: boolean | null; // null when no link
  submitted: number; // f2_responses status <> 'refusal'
  refusals: number; // f2_responses status = 'refusal'
  in_progress: number; // f2_hcws sr-% AND status='enrolled'
};

export interface FacilityOverviewFilters {
  q?: string;
  region?: string;
  province?: string;
  facility_type?: string;
  has_link?: boolean;
  limit?: number;
  offset?: number;
}
```

Interface method (after `getFacilitySlug`):

```ts
  /** Facilities page: every master row + deduped slug (active first, then newest) + counts. */
  listFacilitiesOverview(f: FacilityOverviewFilters): Promise<Paged<FacilityOverviewRow>>;
```

- [ ] **Step 4: InMemory implementation** (after `getFacilitySlug` in `InMemoryAdminStore`):

```ts
  async listFacilitiesOverview(f: FacilityOverviewFilters): Promise<Paged<FacilityOverviewRow>> {
    // One slug per facility: active first, then newest created_at, then slug asc
    // (mirrors the MySQL ROW_NUMBER() dedup).
    const slugByFacility = new Map<string, FacilitySlugRecord>();
    const ranked = [...this.facilitySlugs.values()].sort((a, b) => {
      if (a.active !== b.active) return a.active ? -1 : 1;
      if (a.created_at !== b.created_at) return a.created_at > b.created_at ? -1 : 1;
      return a.slug < b.slug ? -1 : 1;
    });
    for (const s of ranked) if (!slugByFacility.has(s.facility_id)) slugByFacility.set(s.facility_id, s);

    const q = f.q ? f.q.toLowerCase() : null;
    const matched: FacilityOverviewRow[] = [];
    for (const m of this.base.facilities) {
      if (f.region && m.region !== f.region) continue;
      if (f.province && m.province !== f.province) continue;
      if (f.facility_type && m.facility_type !== f.facility_type) continue;
      const s = slugByFacility.get(m.facility_id);
      if (f.has_link === true && !s) continue;
      if (f.has_link === false && s) continue;
      if (q && !`${m.facility_name} ${m.facility_id}`.toLowerCase().includes(q)) continue;
      let submitted = 0;
      let refusals = 0;
      for (const r of this.base.responses.values()) {
        if (r.facility_id !== m.facility_id) continue;
        if (r.status === 'refusal') refusals++;
        else submitted++;
      }
      const inProgress = this.hcws.filter(
        (h) => h.facility_id === m.facility_id && h.hcw_id.startsWith('sr-') && h.status === 'enrolled',
      ).length;
      matched.push({
        facility_id: m.facility_id,
        facility_name: m.facility_name,
        facility_type: m.facility_type,
        region: m.region,
        province: m.province,
        city_mun: m.city_mun,
        slug: s?.slug ?? '',
        active: s ? s.active : null,
        submitted,
        refusals,
        in_progress: inProgress,
      });
    }
    matched.sort(
      (a, b) =>
        a.region.localeCompare(b.region) ||
        a.province.localeCompare(b.province) ||
        a.facility_name.localeCompare(b.facility_name),
    );
    return page(matched, normLimit(f.limit), normOffset(f.offset));
  }
```

- [ ] **Step 5: MySQL implementation** (after `getFacilitySlug` in `MySqlAdminStore`) — MySQL 8 window-function dedup:

```ts
  async listFacilitiesOverview(f: FacilityOverviewFilters): Promise<Paged<FacilityOverviewRow>> {
    const where: string[] = [];
    const params: unknown[] = [];
    if (f.region) { where.push('m.region=?'); params.push(f.region); }
    if (f.province) { where.push('m.province=?'); params.push(f.province); }
    if (f.facility_type) { where.push('m.facility_type=?'); params.push(f.facility_type); }
    if (f.q) {
      where.push('(LOWER(m.facility_name) LIKE ? OR m.facility_id LIKE ?)');
      params.push(`%${f.q.toLowerCase()}%`, `%${f.q}%`);
    }
    if (f.has_link === true) where.push('s.slug IS NOT NULL');
    if (f.has_link === false) where.push('s.slug IS NULL');
    const w = where.length ? ' WHERE ' + where.join(' AND ') : '';
    // One slug per facility: prefer active, then newest, then slug asc.
    const slugJoin = `LEFT JOIN (
        SELECT facility_id, slug, active FROM (
          SELECT facility_id, slug, active,
                 ROW_NUMBER() OVER (PARTITION BY facility_id
                   ORDER BY active DESC, created_at DESC, slug ASC) AS rn
            FROM f2_facility_slugs) ranked WHERE rn=1
      ) s ON s.facility_id = m.facility_id`;
    const limit = normLimit(f.limit);
    const offset = normOffset(f.offset);
    const rows = await this.q(
      `SELECT m.facility_id, m.facility_name, m.facility_type, m.region, m.province, m.city_mun,
              COALESCE(s.slug,'') AS slug, s.active AS active,
              COALESCE(r.submitted,0) AS submitted, COALESCE(r.refusals,0) AS refusals,
              COALESCE(h.in_progress,0) AS in_progress
         FROM f2_facility_master m
         ${slugJoin}
         LEFT JOIN (SELECT facility_id,
                           SUM(CASE WHEN status <> 'refusal' THEN 1 ELSE 0 END) AS submitted,
                           SUM(CASE WHEN status = 'refusal' THEN 1 ELSE 0 END) AS refusals
                      FROM f2_responses GROUP BY facility_id) r ON r.facility_id = m.facility_id
         LEFT JOIN (SELECT facility_id, COUNT(*) AS in_progress
                      FROM f2_hcws WHERE hcw_id LIKE 'sr-%' AND status='enrolled'
                     GROUP BY facility_id) h ON h.facility_id = m.facility_id
         ${w}
        ORDER BY m.region ASC, m.province ASC, m.facility_name ASC
        LIMIT ? OFFSET ?`,
      [...params, limit, offset],
    );
    const count = await this.q(
      `SELECT COUNT(*) AS n FROM f2_facility_master m ${slugJoin}${w}`,
      params,
    );
    const total = Number(count[0]?.n ?? 0);
    return {
      rows: rows.map((r) => ({
        facility_id: strOf(r.facility_id),
        facility_name: strOf(r.facility_name),
        facility_type: strOf(r.facility_type),
        region: strOf(r.region),
        province: strOf(r.province),
        city_mun: strOf(r.city_mun),
        slug: strOf(r.slug),
        active: r.active == null ? null : boolOf(r.active),
        submitted: Number(r.submitted) || 0,
        refusals: Number(r.refusals) || 0,
        in_progress: Number(r.in_progress) || 0,
      })),
      total,
      has_more: offset + rows.length < total,
    };
  }
```

- [ ] **Step 6: Route** in `server/src/admin/routes.ts`, directly after the `admin.post('/facility-slugs', …)` block:

```ts
  // Facilities page (spec F2-Facilities-Page-2026-07-16, Approach A): every
  // master row + its deduped slug + live counts, in one composite read. The
  // master list is READ-ONLY — there is deliberately no write route for it.
  admin.get('/facilities', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const qp = (k: string) => c.req.query(k)?.trim() || '';
    const hasLinkRaw = qp('has_link');
    const limitN = Number(c.req.query('limit'));
    const offsetN = Number(c.req.query('offset'));
    const pageData = await env.adminStore.listFacilitiesOverview({
      ...(qp('q') ? { q: qp('q') } : {}),
      ...(qp('region') ? { region: qp('region') } : {}),
      ...(qp('province') ? { province: qp('province') } : {}),
      ...(qp('facility_type') ? { facility_type: qp('facility_type') } : {}),
      ...(hasLinkRaw === 'true' ? { has_link: true } : hasLinkRaw === 'false' ? { has_link: false } : {}),
      ...(limitN > 0 ? { limit: limitN } : {}),
      ...(offsetN > 0 ? { offset: offsetN } : {}),
    });
    return c.json({
      rows: pageData.rows.map((r) => ({
        ...r,
        url: r.slug ? `${env.pwaOrigin}/f/${r.slug}` : '',
      })),
      total: pageData.total,
      has_more: pageData.has_more,
    });
  });
```

Import addition in routes.ts: none needed (types flow through `env.adminStore`).

- [ ] **Step 7: Run tests** — `npx vitest run test/facilities-overview.test.ts` → PASS; then `npx vitest run` (full server suite green) and `npm run typecheck`.

---

### Task 2: App — `suggestSlug` utility

**Files:**
- Create: `app/src/admin/facilities/suggest-slug.ts`
- Test: `app/src/admin/facilities/suggest-slug.test.ts`

**Interfaces:**
- Produces: `suggestSlug(name: string): string` — consumed by Task 3.

- [ ] **Step 1: Failing tests:**

```ts
import { describe, expect, it } from 'vitest';
import { suggestSlug } from './suggest-slug';

describe('suggestSlug', () => {
  it('lowercases and hyphenates non-alphanumeric runs', () => {
    expect(suggestSlug('RHU Daraga I')).toBe('rhu-daraga-i');
    expect(suggestSlug('LPH-Bay District Hospital')).toBe('lph-bay-district-hospital');
    expect(suggestSlug('St. Niño (Annex) #2')).toBe('st-ni-o-annex-2');
  });

  it('trims leading/trailing hyphens', () => {
    expect(suggestSlug('  (Main) Hospital  ')).toBe('main-hospital');
  });

  it('truncates to 31 chars, cutting back to the last word boundary', () => {
    // 38 chars sanitized → cut at 31 lands mid-"provincial" → back to boundary.
    expect(suggestSlug('Camarines Sur Provincial Health Office')).toBe('camarines-sur-provincial');
    // Exactly-31 stays whole.
    expect(suggestSlug('abcde-fghij-klmno-pqrst-uvwxy-z')).toBe('abcde-fghij-klmno-pqrst-uvwxy-z');
  });

  it("returns '' for degenerate or reserved results (admin types manually)", () => {
    expect(suggestSlug('R')).toBe('');
    expect(suggestSlug('!!!')).toBe('');
    expect(suggestSlug('Resolve')).toBe('');
  });
});
```

- [ ] **Step 2: Run to verify failure** — `cd app && npx vitest run src/admin/facilities/suggest-slug.test.ts` → FAIL.

- [ ] **Step 3: Implementation:**

```ts
/**
 * Deterministic slug suggestion from a facility name (spec
 * F2-Facilities-Page-2026-07-16): lowercase → hyphenate non-alphanumeric runs →
 * trim → truncate to 31 chars at a word boundary. '' means "no usable
 * suggestion — admin types one" (grammar min 2 chars; 'resolve' is reserved).
 */
export function suggestSlug(name: string): string {
  let s = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  if (s.length > 31) {
    let cut = s.slice(0, 31);
    if (s[31] !== '-') {
      const lastHyphen = cut.lastIndexOf('-');
      if (lastHyphen > 1) cut = cut.slice(0, lastHyphen);
    }
    s = cut.replace(/-+$/g, '');
  }
  if (s.length < 2 || s === 'resolve') return '';
  return s;
}
```

- [ ] **Step 4: Run tests** → PASS.

---

### Task 3: App — `FacilityLinkDialog` (create + view modes)

**Files:**
- Create: `app/src/admin/facilities/FacilityLinkDialog.tsx`
- Test: `app/src/admin/facilities/FacilityLinkDialog.test.tsx`

**Interfaces:**
- Consumes: `suggestSlug` (Task 2), `adminFetch`, `useAdminAuth`, `useRouter`, `QRCodeSVG` from `qrcode.react`, existing `POST /admin/api/facility-slugs`.
- Produces (consumed by Task 4):

```ts
export interface FacilityLinkDialogProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
  facility: { facility_id: string; facility_name: string };
  /** Existing link → view mode; null → create mode. */
  existing: { slug: string; active: boolean; url: string } | null;
  /** slug → owning facility, for the duplicate guard (built from the page's rows). */
  takenSlugs: Map<string, { facility_id: string; facility_name: string }>;
  onSaved: () => void;
  onClose: () => void;
}
export function FacilityLinkDialog(props: FacilityLinkDialogProps): JSX.Element;
```

- [ ] **Step 1: Failing tests** (conventions: `jsonResponse` helper + `AdminAuthProvider`/`RouterProvider` wrappers, exactly like `ResponsesTab.test.tsx`):

```tsx
// FacilityLinkDialog.test.tsx — 6 tests:
// 1. create mode pre-fills the slug input with suggestSlug(facility_name)
//    ("RHU Daraga I" → "rhu-daraga-i") and shows the facility read-only.
// 2. Save POSTs {slug, facility_id, facility_name, active:true} to
//    /admin/api/facility-slugs and then renders dialog-url + dialog-qr (svg).
// 3. duplicate guard: typing a slug present in takenSlugs under ANOTHER
//    facility_id disables Save and shows dialog-dup-error naming that facility
//    ("This link name already belongs to LPH-Bay District Hospital…").
// 4. same-facility slug (rename/reactivate path) stays allowed — Save enabled.
// 5. invalid slug (grammar fail / 'resolve') disables Save.
// 6. view mode (existing != null): no Save; renders existing.url + QR + Copy.
```

Full test code follows the FacilitySlugModal.test.tsx shapes this replaces — `vi.fn()` fetchImpl capturing POST bodies, `data-testid` queries (`dialog-slug-input`, `dialog-save`, `dialog-url`, `dialog-qr`, `dialog-dup-error`), `userEvent` for typing. (That file is deleted in Task 6 — port its POST-capture helper here first.)

- [ ] **Step 2: Run to verify failure.**

- [ ] **Step 3: Implement** — dialog scaffold copied from the shipped `FacilitySlugModal` (fixed overlay, hairline card, Escape/backdrop close), with:
  - Header: `Facility link` + facility name/id shown read-only (mono) — never typed.
  - Create mode: slug input initialised `useState(() => suggestSlug(facility.facility_name))`, live-lowercased; validation `SLUG_RE = /^[a-z0-9][a-z0-9-]{1,30}$/`, `slug !== 'resolve'`, plus duplicate guard:

```ts
  const owner = takenSlugs.get(slug.trim());
  const duplicate = owner !== undefined && owner.facility_id !== facility.facility_id;
  const canSave = SLUG_RE.test(slug.trim()) && slug.trim() !== 'resolve' && !duplicate && !saving;
```

  - `duplicate` renders `data-testid="dialog-dup-error"`: `This link name already belongs to {owner.facility_name}. Pick another.`
  - Save → `adminFetch POST ${apiBaseUrl}/admin/api/facility-slugs` body `{slug, facility_id, facility_name, active:true}` → on success `onSaved()` + switch to the saved view (URL + `<QRCodeSVG value={url} size={144} />` + Copy + Print buttons — same block as the old modal's saved view).
  - View mode (`existing`): straight to the URL + QR + Copy + Print block, no slug input, no Save.
  - Error mapping: reuse the old modal's `messageFor` (`E_VALIDATION`/`E_PERM_DENIED`/`E_NETWORK`/`E_BACKEND`).

- [ ] **Step 4: Run tests** → PASS.

---

### Task 4: App — `FacilitiesPage` + route + nav

**Files:**
- Create: `app/src/admin/facilities/FacilitiesPage.tsx`
- Test: `app/src/admin/facilities/FacilitiesPage.test.tsx`
- Modify: `app/src/admin/App.tsx` (route branch), `app/src/admin/Layout.tsx` (nav item + icon)

**Interfaces:**
- Consumes: Task 1 endpoint, Task 3 dialog, `adminFetch`, ResponsesTab filter/URL conventions.
- Produces: `FacilitiesPage({ apiBaseUrl, fetchImpl? })` mounted at `/admin/facilities`.

- [ ] **Step 1: Failing tests:**

```tsx
// FacilitiesPage.test.tsx — 7 tests (jsonResponse + provider wrappers as in ResponsesTab.test.tsx):
// 1. renders rows: facility name+id, /f/<slug> link text, ACTIVE chip, counts columns.
// 2. link-less row shows "no link yet" + a create button (facility-create-<id>).
// 3. first load requests /admin/api/facilities with limit=500 and NO filter params.
// 4. typing in search + picking region updates the fetch query (?q=…&region=…)
//    and the URL search string; "no link yet" toggle sends has_link=false.
// 5. create button opens FacilityLinkDialog with the row's facility and the
//    takenSlugs map (assert the dialog's read-only facility name renders).
// 6. Deactivate action POSTs /admin/api/facility-slugs with active:false and
//    the row's slug/facility unchanged, then refetches the list.
// 7. E_PERM_DENIED renders the shared error banner (role lacks dash_users).
```

- [ ] **Step 2: Run to verify failure.**

- [ ] **Step 3: Implement the page** — structure clones ResponsesTab's skeleton (URL-synced `UiFilters`, `useEffect` fetch on `apiQuery` change, `loading/loaded/failed` state union, hairline table with local `Th`/`Td`):
  - `UiFilters = { q, region, province, facility_type, no_link: boolean }`; URL param names identical (`no_link` → `has_link=false` in the API query); API query always sets `limit=500`.
  - Select options: `const [options, setOptions] = useState<{regions:string[]; provinces:string[]; types:string[]}|null>(null);` — populated from a response ONLY when no filters are active (first unfiltered load), so options never shrink to the filtered set.
  - Row: name + mono id / link (`/f/slug` mono, or muted `— no link yet`) / status chip (`ACTIVE` green solid · `OFF` blue dashed · `—`) / three mono count cells / actions:
    - no slug → `+ Create link` (`data-testid="facility-create-<facility_id>"`) → dialog `existing=null`;
    - slug → `QR` (dialog view mode) · `Copy` (clipboard.writeText(url)) · `Deactivate`/`Activate`:

```ts
  const toggle = async (row: OverviewRow) => {
    await adminFetch(`${apiBaseUrl}/admin/api/facility-slugs`, {
      method: 'POST',
      body: JSON.stringify({
        slug: row.slug, facility_id: row.facility_id,
        facility_name: row.facility_name, active: !row.active,
      }),
    }, fetchOpts());
    reload();
  };
```

  - `takenSlugs` built once per loaded list: `new Map(rows.filter(r => r.slug).map(r => [r.slug, { facility_id: r.facility_id, facility_name: r.facility_name }]))`.
  - Footer note: `master list is read-only here — new facilities are loaded from the sampling frame`.

- [ ] **Step 4: Route branch** in `app/src/admin/App.tsx` (import + after the `/admin/roles` branch):

```tsx
import { FacilitiesPage } from './facilities/FacilitiesPage';
…
  if (pathname === '/admin/facilities' || pathname === '/admin/facilities/') {
    return (
      <Layout>
        <FacilitiesPage apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
      </Layout>
    );
  }
```

- [ ] **Step 5: Nav item** in `app/src/admin/Layout.tsx` — insert into the Operate group between Data and Reports:

```ts
      {
        to: '/admin/facilities',
        label: 'Facilities',
        description: 'Facility master list — create and manage each facility\'s /f/ survey link.',
        icon: IconBuilding,
        requiredPerm: 'dash_users',
      },
```

Icon (16×16 grid, next to the other `Icon*` functions):

```tsx
function IconBuilding(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <IconBase {...props}>
      <rect x="3" y="2" width="10" height="12" rx="1" />
      <path d="M6 5h1.5M8.5 5H10M6 8h1.5M8.5 8H10M6 14v-3h4v3" />
    </IconBase>
  );
}
```

- [ ] **Step 6: Run** — `npx vitest run src/admin/facilities` → PASS; also `npx vitest run src/admin` (Layout/a11y suites still green — if an a11y snapshot enumerates nav items, add Facilities to its expectation).

---

### Task 5: App — Responses tab QN column + `self-registered` label

**Files:**
- Modify: `app/src/admin/data/ResponsesTab.tsx`
- Test: `app/src/admin/data/ResponsesTab.test.tsx` (extend)

**Interfaces:**
- Consumes: server rows already carry `qn` (server `ResponseRow.qn` — passes through the list endpoint untouched).

- [ ] **Step 1: Failing test** (append to ResponsesTab.test.tsx):

```tsx
  it('shows the QN column and renders sr- ids as "self-registered" (F2-Facilities-Page spec)', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({
        rows: [
          { submission_id: 'srv-a', client_submission_id: 'cli-a',
            submitted_at_server: '2026-07-16T07:35:00.000Z',
            hcw_id: 'sr-b9493fe6-7977-40ee-aa56-f9a711058f2a',
            facility_id: '040340210', status: 'stored', source_path: 'self_admin',
            qn: '040340210102' },
          { submission_id: 'srv-b', client_submission_id: 'cli-b',
            submitted_at_server: '2026-07-16T06:53:00.000Z',
            hcw_id: 'LPHBAY-HCW-01', facility_id: '040340210', status: 'refusal',
            source_path: 'self_admin', qn: '040340210101' },
        ],
        total: 2, has_more: false,
      }),
    ) as unknown as typeof fetch;
    renderTab(fetchImpl);
    await waitFor(() => expect(screen.getByText('040340210102')).toBeInTheDocument());
    expect(screen.getByText('self-registered')).toBeInTheDocument();
    expect(screen.queryByText(/sr-b9493fe6/)).not.toBeInTheDocument();
    expect(screen.getByText('LPHBAY-HCW-01')).toBeInTheDocument();
    expect(screen.getByText('040340210101')).toBeInTheDocument();
  });
```

- [ ] **Step 2: Run to verify failure.**

- [ ] **Step 3: Implement** — `ResponsesTab.tsx`:
  1. `interface ResponseRow` gains `qn?: string;`.
  2. Header row: insert `<Th>QN</Th>` after `<Th>HCW</Th>`.
  3. Body row: replace `<Td mono>{r.hcw_id}</Td>` with:

```tsx
              <Td mono>
                {r.hcw_id.startsWith('sr-') ? (
                  <span className="italic text-muted-foreground" title={r.hcw_id}>
                    self-registered
                  </span>
                ) : (
                  r.hcw_id
                )}
              </Td>
              <Td mono>{r.qn || '—'}</Td>
```

(The full `sr-` UUID stays reachable: hover title here, and the Response detail view already shows `hcw_id` verbatim.)

- [ ] **Step 4: Run** — `npx vitest run src/admin/data/ResponsesTab.test.tsx` → PASS.

---

### Task 6: App — HCWs tab cleanup (modal relocation complete)

**Files:**
- Modify: `app/src/admin/data/HCWsTab.tsx`
- Delete: `app/src/admin/data/FacilitySlugModal.tsx`, `app/src/admin/data/FacilitySlugModal.test.tsx`

**Interfaces:**
- Consumes: Task 4 shipped (the page fully replaces the modal). "Numbered links (legacy)" stays untouched.

- [ ] **Step 1: Edit `HCWsTab.tsx`** — remove: the `FacilitySlugModal` import, the `slugOpen` state, the `Facility link` button, and the `{slugOpen ? <FacilitySlugModal … /> : null}` block. (All four were added 2026-07-16; the surrounding "Numbered links (legacy)" and "+ Create HCW" buttons stay.)

- [ ] **Step 2: Delete the two modal files** (`FacilitySlugModal.tsx`, `FacilitySlugModal.test.tsx`) — Task 3's dialog + tests carry the coverage forward.

- [ ] **Step 3: Sweep for stragglers** — `grep -rn "FacilitySlugModal" app/src` → no hits; `npx vitest run src/admin` → green.

---

### Task 7: Full verification + deploy

- [ ] `cd server && npx vitest run && npm run typecheck` → all green.
- [ ] `cd app && npx vitest run --max-workers=2 && npx tsc -b --force && npx eslint .` → all green.
- [ ] `cd app && VITE_F2_PROXY_URL="https://uhc-hcw.asiansocial.org" npm run build` → clean (secrets/budget/contrast).
- [ ] Deploy via `pretest-2026-07-16/deploy_model_c_full.sh` (standing autodeploy; the DDL step is a no-op — nothing new to apply).
- [ ] Smoke: `GET /admin/api/facilities` unauthenticated → 401 JSON (route live + gated); log into `/admin` → Facilities nav item renders the LPH-Bay row with its `lphbay` link, ACTIVE chip, and non-zero counts; Responses tab shows the QN column.
- [ ] Update the spec status → DEPLOYED; update memory (`project_aspsi_f2_facility_slug_links` gains the Facilities-page note).

## Self-Review

- **Spec coverage:** composite endpoint + filters + counts + dedup (T1); suggestSlug rule (T2); dialog with duplicate guard + QR/copy/print (T3); page, nav, route, options-from-unfiltered-load, toggle, footer note (T4); QN column + sr- label (T5); modal relocation + legacy button untouched (T6); no-DDL deploy (T7). Read-only master: no write route exists anywhere (T1 comment). ✔
- **Placeholders:** Task 3 Step 1 and Task 4 Step 1 specify tests as numbered behavioural contracts with named testids rather than full listings — accepted for this project (plan author = executor, conventions cited to exact model files); all implementation steps carry complete code.
- **Type consistency:** `FacilityOverviewRow` fields match the route's spread + `url` composition and the page/dialog consumption; `takenSlugs` map shape identical in T3 props and T4 construction; `suggestSlug` name/signature consistent across T2–T3.
