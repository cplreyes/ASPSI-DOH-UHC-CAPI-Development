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

const facility = (over: Partial<FacilityRow> = {}): FacilityRow => ({
  facility_id: '040340210',
  facility_name: 'LPH-Bay District Hospital',
  facility_type: 'Hospital',
  region: 'Region V',
  province: 'Albay',
  city_mun: 'Bay',
  barangay: '',
  ...over,
});

const resp = (over: Partial<ResponseRow> = {}): ResponseRow => ({
  submission_id: 's-' + Math.random().toString(36).slice(2),
  client_submission_id: 'c-' + Math.random().toString(36).slice(2),
  submitted_at_server: '2026-07-16T00:00:00.000Z',
  submitted_at_client: '',
  source: 'PWA',
  spec_version: 'v',
  app_version: '1',
  hcw_id: 'sr-x',
  facility_id: '040340210',
  device_fingerprint: '',
  sync_attempt_count: '1',
  status: 'stored',
  values_json: '{}',
  submission_lat: '',
  submission_lng: '',
  gps_status: '',
  source_path: 'self_admin',
  encoded_by: '',
  encoded_at: '',
  qn: '',
  ...over,
});

async function setup() {
  const store = new InMemoryStore();
  const adminStore = new InMemoryAdminStore(store);
  const fileStore = new InMemoryFileStore();
  adminStore.roles.set('Administrator', role());
  adminStore.users.set('carl', user());
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
const authed = (token: string): RequestInit => ({ headers: { Authorization: `Bearer ${token}` } });
const list = async (app: Hono, token: string, qs = '') => {
  const res = await app.request(`/admin/api/facilities${qs}`, authed(token));
  expect(res.status).toBe(200);
  return (await res.json()) as {
    rows: Array<Record<string, unknown>>;
    total: number;
    has_more: boolean;
  };
};

describe('GET /admin/api/facilities (composite overview)', () => {
  it('lists every master row — link-less facilities appear with empty slug/url and null active', async () => {
    const { app, store } = await setup();
    store.facilities.push(
      facility(),
      facility({ facility_id: '040341130', facility_name: 'RHU Daraga I', facility_type: 'RHU', city_mun: 'Daraga' }),
    );
    const token = await loginToken(app);
    const b = await list(app, token);
    expect(b.total).toBe(2);
    const daraga = b.rows.find((r) => r.facility_id === '040341130')!;
    expect(daraga).toMatchObject({
      slug: '',
      url: '',
      active: null,
      submitted: 0,
      refusals: 0,
      in_progress: 0,
    });
  });

  it('joins the slug + composes the public url; counts follow the spec definitions', async () => {
    const { app, store, adminStore } = await setup();
    store.facilities.push(facility());
    await adminStore.upsertFacilitySlug({
      slug: 'lphbay',
      facility_id: '040340210',
      facility_name: 'LPH-Bay District Hospital',
      active: true,
      created_at: '2026-07-16T00:00:00.000Z',
      created_by: 'carl',
    });
    // 2 stored + 1 refusal responses; sr- enrolled counts as in-progress,
    // sr- submitted does not, non-sr enrolled slot does not (sr- only).
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
      slug: 'lphbay',
      active: true,
      url: 'https://uhc-hcw.asiansocial.org/f/lphbay',
      submitted: 2,
      refusals: 1,
      in_progress: 1,
    });
  });

  it('filters: q (name or id substring), region, province, facility_type, has_link', async () => {
    const { app, store, adminStore } = await setup();
    store.facilities.push(
      facility(),
      facility({ facility_id: '040341130', facility_name: 'RHU Daraga I', facility_type: 'RHU', province: 'Albay' }),
      facility({ facility_id: '051720003', facility_name: 'Bicol Medical Center', region: 'Region V', province: 'Camarines Sur' }),
    );
    await adminStore.upsertFacilitySlug({
      slug: 'lphbay',
      facility_id: '040340210',
      facility_name: 'LPH-Bay District Hospital',
      active: true,
      created_at: '2026-07-16T00:00:00.000Z',
      created_by: 'carl',
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
      slug: 'lphbay-old',
      facility_id: '040340210',
      facility_name: 'LPH-Bay District Hospital',
      active: false,
      created_at: '2026-07-15T00:00:00.000Z',
      created_by: 'carl',
    });
    await adminStore.upsertFacilitySlug({
      slug: 'lphbay',
      facility_id: '040340210',
      facility_name: 'LPH-Bay District Hospital',
      active: true,
      created_at: '2026-07-16T00:00:00.000Z',
      created_by: 'carl',
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
    const viewerToken = await loginToken(app, 'viewer');
    expect((await app.request('/admin/api/facilities', authed(viewerToken))).status).toBe(403);
  });
});
