/**
 * Facility master management routes (spec F2-Facility-Master-Mgmt-2026-07-16):
 * create / patch (archive-only, id immutable) / batch import with dry-run.
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
import { InMemoryStore, type FacilityRow } from '../src/store.js';

const KEY = Buffer.from('test-signing-key-32-bytes-long!!').toString('base64url');
const PASSWORD = 'correct-horse-9';
const PASS_HASH = await hashPassword(PASSWORD);

const role = (over: Partial<AdminRoleRecord> = {}): AdminRoleRecord => ({
  name: 'Administrator',
  is_builtin: true,
  version: 1,
  dash_data: true,
  dash_report: true,
  dash_apps: true,
  dash_users: true,
  dash_roles: true,
  dict_self_admin_up: true,
  dict_self_admin_down: true,
  dict_paper_encoded_up: true,
  dict_paper_encoded_down: true,
  dict_capi_up: true,
  dict_capi_down: true,
  created_at: '2026-01-01T00:00:00.000Z',
  created_by: 'seed',
  ...over,
});
const user = (over: Partial<AdminUserRecord> = {}): AdminUserRecord => ({
  username: 'carl',
  first_name: 'Carl',
  last_name: 'Reyes',
  role_name: 'Administrator',
  password_hash: PASS_HASH,
  password_must_change: false,
  email: '',
  phone: '',
  created_at: '2026-01-02T00:00:00.000Z',
  created_by: 'seed',
  last_login_at: '',
  ...over,
});

const lphbay: FacilityRow = {
  facility_id: '040340210',
  facility_name: 'LPH-Bay District Hospital',
  facility_type: 'District Hospital',
  region: 'Region IV-A (CALABARZON)',
  province: 'Laguna',
  city_mun: 'Bay',
  barangay: '',
};

async function setup() {
  const store = new InMemoryStore();
  const adminStore = new InMemoryAdminStore(store);
  const fileStore = new InMemoryFileStore();
  adminStore.roles.set('Administrator', role());
  adminStore.users.set('carl', user());
  store.facilities.push({ ...lphbay });
  const app = createApp({
    jwtSigningKey: KEY,
    store,
    admin: { adminStore, fileStore, pwaOrigin: 'https://uhc-hcw.asiansocial.org' },
  });
  return { app, store, adminStore };
}

async function loginToken(app: Hono, username = 'carl'): Promise<string> {
  const res = await app.request('/admin/api/login', {
    method: 'POST',
    body: JSON.stringify({ username, password: PASSWORD }),
  });
  expect(res.status).toBe(200);
  return ((await res.json()) as { token: string }).token;
}
const authed = (token: string, init: RequestInit = {}): RequestInit => ({
  ...init,
  headers: { ...((init.headers as Record<string, string>) ?? {}), Authorization: `Bearer ${token}` },
});

const daragaInput = {
  facility_id: '040341130',
  facility_name: 'RHU Daraga I',
  facility_type: 'Rural Health Unit',
  region: 'Region V (Bicol Region)',
  province: 'Albay',
  city_mun: 'Daraga',
};

describe('POST /admin/api/facilities (create)', () => {
  it('creates a facility and returns the row + geo warnings', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const res = await app.request(
      '/admin/api/facilities',
      authed(token, { method: 'POST', body: JSON.stringify(daragaInput) }),
    );
    expect(res.status).toBe(200);
    const b = (await res.json()) as { ok: boolean; row: Record<string, unknown>; warnings: string[] };
    expect(b.ok).toBe(true);
    expect(b.row).toMatchObject({ facility_id: '040341130', archived: false });
    // Albay is new to a Laguna-only master → advisory province warning, no block.
    expect(b.warnings.some((w) => w.includes('new to the master'))).toBe(true);
  });

  it('400s on validation errors and 409s on duplicates (archived duplicates say unarchive)', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    const bad = await app.request(
      '/admin/api/facilities',
      authed(token, { method: 'POST', body: JSON.stringify({ facility_id: '123', facility_name: 'X' }) }),
    );
    expect(bad.status).toBe(400);
    const dup = await app.request(
      '/admin/api/facilities',
      authed(token, { method: 'POST', body: JSON.stringify({ ...daragaInput, facility_id: '040340210' }) }),
    );
    expect(dup.status).toBe(409);
    await adminStore.updateFacility('040340210', { archived: true });
    const dupArchived = await app.request(
      '/admin/api/facilities',
      authed(token, { method: 'POST', body: JSON.stringify({ ...daragaInput, facility_id: '040340210' }) }),
    );
    expect(dupArchived.status).toBe(409);
    expect(((await dupArchived.json()) as { error: { message: string } }).error.message).toMatch(
      /unarchive/,
    );
  });
});

describe('PATCH /admin/api/facilities/:id', () => {
  it('edits fields, keeps id immutable, 404s on unknown', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const ok = await app.request(
      '/admin/api/facilities/040340210',
      authed(token, { method: 'PATCH', body: JSON.stringify({ facility_name: 'LPH-Bay DH (renamed)' }) }),
    );
    expect(ok.status).toBe(200);
    expect(((await ok.json()) as { row: { facility_name: string } }).row.facility_name).toBe(
      'LPH-Bay DH (renamed)',
    );
    const immutable = await app.request(
      '/admin/api/facilities/040340210',
      authed(token, { method: 'PATCH', body: JSON.stringify({ facility_id: '999999999' }) }),
    );
    expect(immutable.status).toBe(400);
    expect(((await immutable.json()) as { error: { message: string } }).error.message).toMatch(
      /immutable/,
    );
    expect(
      (
        await app.request(
          '/admin/api/facilities/999999999',
          authed(token, { method: 'PATCH', body: JSON.stringify({ facility_name: 'X' }) }),
        )
      ).status,
    ).toBe(404);
  });

  it('archives + unarchives with distinct audit events; archived leaves readFacilities', async () => {
    const { app, store, adminStore } = await setup();
    const token = await loginToken(app);
    const arch = await app.request(
      '/admin/api/facilities/040340210',
      authed(token, { method: 'PATCH', body: JSON.stringify({ archived: true }) }),
    );
    expect(((await arch.json()) as { row: { archived: boolean } }).row.archived).toBe(true);
    expect(await store.readFacilities()).toHaveLength(0);
    const unarch = await app.request(
      '/admin/api/facilities/040340210',
      authed(token, { method: 'PATCH', body: JSON.stringify({ archived: false }) }),
    );
    expect(((await unarch.json()) as { row: { archived: boolean } }).row.archived).toBe(false);
    expect(await store.readFacilities()).toHaveLength(1);
    const events = adminStore.auditRows.map((r) => r.event_type);
    expect(events).toContain('admin_facility_archive');
    expect(events).toContain('admin_facility_unarchive');
    // Strict boolean archived.
    expect(
      (
        await app.request(
          '/admin/api/facilities/040340210',
          authed(token, { method: 'PATCH', body: JSON.stringify({ archived: 1 }) }),
        )
      ).status,
    ).toBe(400);
  });

  it('archived rows leave the default overview but appear with include_archived', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    await adminStore.updateFacility('040340210', { archived: true });
    const def = await app.request('/admin/api/facilities', authed(token));
    expect(((await def.json()) as { total: number }).total).toBe(0);
    const inc = await app.request('/admin/api/facilities?include_archived=true', authed(token));
    const b = (await inc.json()) as { total: number; rows: Array<{ archived: boolean }> };
    expect(b.total).toBe(1);
    expect(b.rows[0]!.archived).toBe(true);
  });
});

describe('POST /admin/api/facilities/import', () => {
  const importReq = (app: Hono, token: string, mode: string, rows: unknown[]) =>
    app.request(
      '/admin/api/facilities/import',
      authed(token, { method: 'POST', body: JSON.stringify({ mode, rows }) }),
    );

  it('dry-run classifies create / update / unchanged / error without persisting', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    const rows = [
      daragaInput, // create
      { ...lphbay, facility_name: 'LPH-Bay DH (from wave)' }, // update (name change)
      { ...lphbay }, // unchanged
      { facility_id: 'abc', facility_name: 'Bad' }, // error
    ];
    const res = await importReq(app, token, 'dry_run', rows);
    expect(res.status).toBe(200);
    const b = (await res.json()) as {
      summary: Record<string, number>;
      verdicts: Array<{ action: string; changes?: string[] }>;
    };
    expect(b.summary).toMatchObject({ creates: 1, updates: 1, unchanged: 1, errors: 1 });
    expect(b.verdicts.map((v) => v.action)).toEqual(['create', 'update', 'unchanged', 'error']);
    expect(b.verdicts[1]!.changes).toEqual(['facility_name']);
    // Dry run persisted nothing.
    expect(store.facilities).toHaveLength(1);
    expect(store.facilities[0]!.facility_name).toBe('LPH-Bay District Hospital');
  });

  it('apply persists creates + updates, tolerates error rows, audits the batch', async () => {
    const { app, store, adminStore } = await setup();
    const token = await loginToken(app);
    const rows = [
      daragaInput,
      { ...lphbay, facility_name: 'LPH-Bay DH (from wave)' },
      { facility_id: 'abc', facility_name: 'Bad' },
    ];
    const res = await importReq(app, token, 'apply', rows);
    const b = (await res.json()) as { summary: Record<string, number> };
    expect(b.summary).toMatchObject({ creates: 1, updates: 1, errors: 1 });
    expect(store.facilities).toHaveLength(2);
    expect(store.facilities.find((f) => f.facility_id === '040340210')!.facility_name).toBe(
      'LPH-Bay DH (from wave)',
    );
    const audit = adminStore.auditRows.find((r) => r.event_type === 'admin_facility_import');
    expect(audit?.event_resource).toBe('creates=1 updates=1 errors=1');
  });

  it('warns on rows updating an archived facility; validates mode and the 2000-row cap', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    await adminStore.updateFacility('040340210', { archived: true });
    const res = await importReq(app, token, 'dry_run', [{ ...lphbay, facility_name: 'New name' }]);
    const b = (await res.json()) as { verdicts: Array<{ warnings: string[] }> };
    expect(b.verdicts[0]!.warnings.some((w) => w.includes('archived facility'))).toBe(true);
    expect((await importReq(app, token, 'nope', [daragaInput])).status).toBe(400);
    expect((await importReq(app, token, 'dry_run', [])).status).toBe(400);
    expect(
      (await importReq(app, token, 'dry_run', new Array(2001).fill(daragaInput))).status,
    ).toBe(400);
  });
});

describe('RBAC', () => {
  it('all three routes gate on dash_users', async () => {
    const { app, adminStore } = await setup();
    adminStore.roles.set('Viewer', role({ name: 'Viewer', is_builtin: false, dash_users: false }));
    adminStore.users.set('viewer', user({ username: 'viewer', role_name: 'Viewer' }));
    const t = await loginToken(app, 'viewer');
    expect(
      (await app.request('/admin/api/facilities', authed(t, { method: 'POST', body: '{}' }))).status,
    ).toBe(403);
    expect(
      (
        await app.request(
          '/admin/api/facilities/040340210',
          authed(t, { method: 'PATCH', body: '{}' }),
        )
      ).status,
    ).toBe(403);
    expect(
      (
        await app.request(
          '/admin/api/facilities/import',
          authed(t, { method: 'POST', body: '{}' }),
        )
      ).status,
    ).toBe(403);
  });
});

describe('target_hcws (spec F2-Coverage-Report-2026-07-17)', () => {
  it('create stores a target; patch edits and clears it (null)', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const created = (await (
      await app.request(
        '/admin/api/facilities',
        authed(token, { method: 'POST', body: JSON.stringify({ ...daragaInput, target_hcws: 25 }) }),
      )
    ).json()) as { row: { target_hcws: number | null } };
    expect(created.row.target_hcws).toBe(25);

    const patched = (await (
      await app.request(
        '/admin/api/facilities/040341130',
        authed(token, { method: 'PATCH', body: JSON.stringify({ target_hcws: 40 }) }),
      )
    ).json()) as { row: { target_hcws: number | null } };
    expect(patched.row.target_hcws).toBe(40);

    const cleared = (await (
      await app.request(
        '/admin/api/facilities/040341130',
        authed(token, { method: 'PATCH', body: JSON.stringify({ target_hcws: null }) }),
      )
    ).json()) as { row: { target_hcws: number | null } };
    expect(cleared.row.target_hcws).toBeNull();
  });

  it('rejects non-integer / out-of-range / junk targets', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    for (const bad of [3.5, -1, 10000, 'abc']) {
      const res = await app.request(
        '/admin/api/facilities',
        authed(token, { method: 'POST', body: JSON.stringify({ ...daragaInput, target_hcws: bad }) }),
      );
      expect(res.status).toBe(400);
      const b = (await res.json()) as { error: { message: string } };
      expect(b.error.message).toContain('target_hcws');
    }
  });

  it('import: a row without a target never clears an existing one; a specified target updates', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    store.facilities[0]!.target_hcws = 30; // pre-existing quota on LPH-Bay
    // 7-col-style row (no target key): metadata change only — target untouched.
    const noTarget = (await (
      await app.request(
        '/admin/api/facilities/import',
        authed(token, {
          method: 'POST',
          body: JSON.stringify({
            mode: 'apply',
            rows: [{ ...lphbay, facility_type: 'Provincial Hospital' }],
          }),
        }),
      )
    ).json()) as { verdicts: Array<{ action: string; changes?: string[] }> };
    expect(noTarget.verdicts[0]!.action).toBe('update');
    expect(noTarget.verdicts[0]!.changes).not.toContain('target_hcws');
    const after = (await (
      await app.request('/admin/api/facilities?include_archived=true&limit=500', authed(token))
    ).json()) as { rows: Array<{ facility_id: string; target_hcws: number | null }> };
    expect(after.rows.find((r) => r.facility_id === '040340210')!.target_hcws).toBe(30);

    // 8-col row with a target: detected as a change and applied.
    const withTarget = (await (
      await app.request(
        '/admin/api/facilities/import',
        authed(token, {
          method: 'POST',
          body: JSON.stringify({
            mode: 'apply',
            rows: [{ ...lphbay, facility_type: 'Provincial Hospital', target_hcws: '45' }],
          }),
        }),
      )
    ).json()) as { verdicts: Array<{ action: string; changes?: string[] }> };
    expect(withTarget.verdicts[0]!.action).toBe('update');
    expect(withTarget.verdicts[0]!.changes).toContain('target_hcws');
    const after2 = (await (
      await app.request('/admin/api/facilities?include_archived=true&limit=500', authed(token))
    ).json()) as { rows: Array<{ facility_id: string; target_hcws: number | null }> };
    expect(after2.rows.find((r) => r.facility_id === '040340210')!.target_hcws).toBe(45);
  });
});
