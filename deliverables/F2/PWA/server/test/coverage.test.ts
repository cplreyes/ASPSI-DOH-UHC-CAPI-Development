/**
 * Coverage report (spec F2-Coverage-Report-2026-07-17): geo-name rollups,
 * orphan bucket, archived toggle, Manila windows, target math, and — the
 * load-bearing one — parity with the Facilities overview counts.
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
  region: 'Region IV-A (CALABARZON)',
  province: 'Laguna',
  city_mun: 'Bay',
  barangay: '',
  ...over,
});

let seq = 0;
const resp = (over: Partial<ResponseRow> = {}): ResponseRow => ({
  submission_id: `s-${++seq}`,
  client_submission_id: `c-${seq}`,
  submitted_at_server: '2026-07-16T13:19:19.000Z',
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

/** Full-fixture setup: 2 live facilities + 1 archived + orphan responses. */
async function setup() {
  const store = new InMemoryStore();
  const adminStore = new InMemoryAdminStore(store);
  const fileStore = new InMemoryFileStore();
  adminStore.roles.set('Administrator', role());
  adminStore.users.set('carl', user());

  store.facilities.push(
    facility({ target_hcws: 30 }), // A: Laguna, target 30, will get an active link
    facility({
      facility_id: '050110001',
      facility_name: 'RHU Daraga I',
      region: 'Region V (Bicol Region)',
      province: 'Albay',
      city_mun: 'Daraga',
    }), // B: Albay, no target, no link
    facility({
      facility_id: '050110002',
      facility_name: 'Albay CHO',
      region: 'Region V (Bicol Region)',
      province: 'Albay',
      city_mun: 'Legazpi',
      archived: true,
      target_hcws: 20,
    }), // C: archived
  );

  // A: 2 submitted (1 paper) + 1 refusal + 1 in-progress sr- + active slug.
  store.responses.set('a1', resp());
  store.responses.set('a2', resp({ source_path: 'paper_encoded' }));
  store.responses.set('a3', resp({ status: 'refusal' }));
  await adminStore.createHcw({ hcw_id: 'sr-going', facility_id: '040340210', facility_name: '', status: 'enrolled', qn: '' });
  await adminStore.upsertFacilitySlug({
    slug: 'lphbay',
    facility_id: '040340210',
    facility_name: 'LPH-Bay District Hospital',
    active: true,
    created_at: '2026-07-16T00:00:00.000Z',
    created_by: 'carl',
  });
  // B: 1 submitted. C (archived): 1 submitted.
  store.responses.set('b1', resp({ facility_id: '050110001' }));
  store.responses.set('c1', resp({ facility_id: '050110002' }));
  // Orphan: a response whose facility_id has no master row.
  store.responses.set('o1', resp({ facility_id: '999999999' }));

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

interface Row {
  key: string;
  label: string;
  facilities: number;
  links_active: number;
  target: number | null;
  started: number;
  submitted: number;
  refusals: number;
  refusal_rate: number | null;
  coverage_pct: number | null;
  paper_encoded: number;
  last_activity: string;
}
const coverage = async (app: Hono, token: string, qs = 'level=region') => {
  const res = await app.request(`/admin/api/dashboards/report/coverage?${qs}`, authed(token));
  expect(res.status).toBe(200);
  return (await res.json()) as { level: string; rows: Row[]; totals: Row };
};

describe('GET /admin/api/dashboards/report/coverage', () => {
  it('facility level: full column math on the fixture', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const b = await coverage(app, token, 'level=facility');
    const a = b.rows.find((r) => r.key === '040340210')!;
    expect(a).toMatchObject({
      label: 'LPH-Bay District Hospital',
      facilities: 1,
      links_active: 1,
      target: 30,
      started: 1,
      submitted: 2,
      refusals: 1,
      refusal_rate: 33.3, // 1/3, 1 dp
      coverage_pct: 7, // 2/30 → 6.67 → 7
      paper_encoded: 1,
      last_activity: '2026-07-16T13:19:19.000Z',
    });
    const bRow = b.rows.find((r) => r.key === '050110001')!;
    expect(bRow).toMatchObject({ target: null, coverage_pct: null, submitted: 1, refusals: 0, refusal_rate: 0 });
    // Orphan bucket always sorts last.
    expect(b.rows[b.rows.length - 1]).toMatchObject({ key: '(not in master)', submitted: 1 });
    expect(b.totals).toMatchObject({ key: 'TOTAL', facilities: 2, links_active: 1, target: 30, submitted: 4, refusals: 1 });
  });

  it('region/province levels roll up by master NAMES, not id prefixes', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const reg = await coverage(app, token, 'level=region');
    expect(reg.rows.map((r) => r.key)).toEqual([
      'Region IV-A (CALABARZON)',
      'Region V (Bicol Region)',
      '(not in master)', // orphan bucket always last
    ]);
    const prov = await coverage(app, token, 'level=province');
    const albay = prov.rows.find((r) => r.key === 'Albay')!;
    // Archived Albay CHO excluded by default: 1 facility, 1 submitted, no target.
    expect(albay).toMatchObject({ facilities: 1, submitted: 1, target: null });
  });

  it('blank region groups under "(unspecified)"', async () => {
    const { app, store } = await setup();
    store.facilities.push(facility({ facility_id: '060000001', facility_name: 'No-Geo Clinic', region: '', province: '' }));
    const token = await loginToken(app);
    const reg = await coverage(app, token, 'level=region');
    expect(reg.rows.some((r) => r.key === '(unspecified)' && r.facilities === 1)).toBe(true);
  });

  it('include_archived pulls archived facilities into rows and denominators', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const prov = await coverage(app, token, 'level=province&include_archived=true');
    const albay = prov.rows.find((r) => r.key === 'Albay')!;
    expect(albay).toMatchObject({ facilities: 2, submitted: 2, target: 20, coverage_pct: 10 }); // 2/20
  });

  it('Manila-day window scopes response counts but leaves started/target intact', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    // All fixture responses are 2026-07-16 MNL; a 07-17 window empties counts.
    const b = await coverage(app, token, 'level=facility&from=2026-07-17&to=2026-07-17');
    const a = b.rows.find((r) => r.key === '040340210')!;
    expect(a).toMatchObject({ submitted: 0, refusals: 0, started: 1, target: 30, last_activity: '' });
    // The orphan's responses are also outside the window → no orphan row at all.
    expect(b.rows.some((r) => r.key === '(not in master)')).toBe(false);
    // And the same-day window keeps everything (21:19 MNL is inside 07-16).
    const sameDay = await coverage(app, token, 'level=facility&from=2026-07-16&to=2026-07-16');
    expect(sameDay.totals.submitted).toBe(4);
  });

  it('PARITY: facility-level coverage counts equal the Facilities overview counts', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const cov = await coverage(app, token, 'level=facility');
    const overview = (await (
      await app.request('/admin/api/facilities?limit=500', authed(token))
    ).json()) as { rows: Array<{ facility_id: string; submitted: number; refusals: number; in_progress: number }> };
    for (const o of overview.rows) {
      const c = cov.rows.find((r) => r.key === o.facility_id)!;
      expect({ submitted: c.submitted, refusals: c.refusals, started: c.started }).toEqual({
        submitted: o.submitted,
        refusals: o.refusals,
        started: o.in_progress,
      });
    }
  });

  it('RBAC: requires dash_report', async () => {
    const { app, adminStore } = await setup();
    adminStore.roles.set('NoReports', role({ name: 'NoReports', is_builtin: false, dash_report: false }));
    adminStore.users.set('nr', user({ username: 'nr', role_name: 'NoReports' }));
    const t = await loginToken(app, 'nr');
    const res = await app.request('/admin/api/dashboards/report/coverage', authed(t));
    expect(res.status).toBe(403);
  });
});
