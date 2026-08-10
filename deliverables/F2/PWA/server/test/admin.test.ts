/**
 * Admin-portal parity suite (P1b) — the Worker's /admin/api/* surface served
 * by f2-api against InMemory stores. Covers login/session/RBAC, HCW create
 * (qn assignment) + reissue (CAS, qn-in-JWT), revocation, data-dashboard
 * reads, DLQ replay/delete, encode, config, users/roles CRUD, files, settings,
 * and reports. Response shapes/status codes are the frontend contract
 * (app/src/admin/** + lib/api-client.ts).
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
import { InMemoryStore, type ResponseRow } from '../src/store.js';
import { mintJwt, verifyJwt } from '../src/jwt.js';

const KEY = Buffer.from('test-signing-key-32-bytes-long!!').toString('base64url');
const PASSWORD = 'correct-horse-9';
// PBKDF2 is intentionally slow — hash once, reuse across seeded users.
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

const respRow = (over: Partial<ResponseRow> = {}): ResponseRow => ({
  submission_id: 'srv-1',
  client_submission_id: 'c1',
  submitted_at_server: '2026-07-01T00:00:00.000Z',
  submitted_at_client: '',
  source: 'PWA',
  spec_version: '2026-04-17-m1',
  app_version: '1.0.0',
  hcw_id: 'h1',
  facility_id: '040340002',
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
  return { app, store, adminStore, fileStore };
}

async function loginToken(app: Hono, username = 'carl', password = PASSWORD): Promise<string> {
  const res = await app.request('/admin/api/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  expect(res.status).toBe(200);
  return ((await res.json()) as { token: string }).token;
}

const authed = (token: string, init: RequestInit = {}): RequestInit => ({
  ...init,
  headers: { ...((init.headers as Record<string, string>) ?? {}), Authorization: `Bearer ${token}` },
});

const errCode = async (res: Response): Promise<string> =>
  ((await res.json()) as { error: { code: string } }).error.code;

// ---------------------------------------------------------------------------

describe('admin login/session', () => {
  it('login returns the Worker LoginSuccess shape + X-Request-Id', async () => {
    const { app } = await setup();
    const res = await app.request('/admin/api/login', {
      method: 'POST',
      body: JSON.stringify({ username: 'carl', password: PASSWORD }),
    });
    expect(res.status).toBe(200);
    expect(res.headers.get('X-Request-Id')).toBeTruthy();
    const body = (await res.json()) as {
      token: string;
      role: string;
      role_version: number;
      expires_at: number;
      password_must_change: boolean;
      permissions: Record<string, boolean>;
    };
    expect(body.token.split('.')).toHaveLength(3);
    expect(body.role).toBe('Administrator');
    expect(body.role_version).toBe(1);
    expect(body.password_must_change).toBe(false);
    expect(body.permissions.dash_data).toBe(true);
    expect(body.expires_at).toBeGreaterThan(Math.floor(Date.now() / 1000));
  });

  it('401 E_AUTH_INVALID on bad password / unknown user; 400 on missing fields', async () => {
    const { app } = await setup();
    const bad = await app.request('/admin/api/login', {
      method: 'POST',
      body: JSON.stringify({ username: 'carl', password: 'wrong-pass-1' }),
    });
    expect(bad.status).toBe(401);
    expect(await errCode(bad)).toBe('E_AUTH_INVALID');
    const ghost = await app.request('/admin/api/login', {
      method: 'POST',
      body: JSON.stringify({ username: 'nobody_here', password: 'whatever-1' }),
    });
    expect(ghost.status).toBe(401);
    const missing = await app.request('/admin/api/login', {
      method: 'POST',
      body: JSON.stringify({ username: 'carl' }),
    });
    expect(missing.status).toBe(400);
    expect(await errCode(missing)).toBe('E_VALIDATION');
  });

  it('throttles after 10 failed logins with 429 E_AUTH_LOCKED + Retry-After', async () => {
    const { app } = await setup();
    for (let i = 0; i < 10; i++) {
      const r = await app.request('/admin/api/login', {
        method: 'POST',
        body: JSON.stringify({ username: 'carl', password: 'wrong-pass-1' }),
      });
      expect(r.status).toBe(401);
    }
    const locked = await app.request('/admin/api/login', {
      method: 'POST',
      body: JSON.stringify({ username: 'carl', password: PASSWORD }),
    });
    expect(locked.status).toBe(429);
    expect(await errCode(locked)).toBe('E_AUTH_LOCKED');
    expect(locked.headers.get('Retry-After')).toBeTruthy();
  });

  it('logout revokes the jti: 204 then E_AUTH_EXPIRED on reuse', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const out = await app.request('/admin/api/logout', authed(token, { method: 'POST' }));
    expect(out.status).toBe(204);
    const after = await app.request('/admin/api/dashboards/users', authed(token));
    expect(after.status).toBe(401);
    expect(await errCode(after)).toBe('E_AUTH_EXPIRED');
  });

  it('rejects device (HCW) tokens on admin routes — wrong audience', async () => {
    const { app } = await setup();
    const nowS = Math.floor(Date.now() / 1000);
    const device = await mintJwt(
      { jti: 'j1', tablet_id: 't1', facility_id: '040340002', iat: nowS, exp: nowS + 3600 },
      KEY,
    );
    const res = await app.request('/admin/api/dashboards/users', authed(device));
    expect(res.status).toBe(401);
    expect(await errCode(res)).toBe('E_AUTH_EXPIRED');
    const none = await app.request('/admin/api/dashboards/users');
    expect(none.status).toBe(401);
    expect(await errCode(none)).toBe('E_AUTH_INVALID');
  });

  it('RBAC: role without the perm gets 403 E_PERM_DENIED', async () => {
    const { app, adminStore } = await setup();
    adminStore.roles.set(
      'Viewer',
      role({
        name: 'Viewer', is_builtin: false, dash_report: false, dash_apps: false,
        dash_users: false, dash_roles: false, dict_self_admin_up: false,
        dict_self_admin_down: false, dict_paper_encoded_up: false,
        dict_paper_encoded_down: false, dict_capi_up: false, dict_capi_down: false,
      }),
    );
    adminStore.users.set('viewer1', user({ username: 'viewer1', role_name: 'Viewer' }));
    const token = await loginToken(app, 'viewer1');
    const denied = await app.request('/admin/api/dashboards/users', authed(token));
    expect(denied.status).toBe(403);
    expect(await errCode(denied)).toBe('E_PERM_DENIED');
    const allowed = await app.request('/admin/api/dashboards/data/responses', authed(token));
    expect(allowed.status).toBe(200);
  });

  it('role version bump invalidates in-flight JWTs (E_AUTH_EXPIRED)', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const patch = await app.request(
      '/admin/api/dashboards/roles/Administrator',
      authed(token, { method: 'PATCH', body: JSON.stringify({ dict_capi_down: false }) }),
    );
    expect(patch.status).toBe(200);
    const body = (await patch.json()) as { role: { version: number }; changed: boolean };
    expect(body.changed).toBe(true);
    expect(body.role.version).toBe(2);
    const after = await app.request('/admin/api/dashboards/users', authed(token));
    expect(after.status).toBe(401);
    expect(await errCode(after)).toBe('E_AUTH_EXPIRED');
  });

  it('pwc flow: must-change token is barred until PATCH /me/password mints a clean one', async () => {
    const { app, adminStore } = await setup();
    adminStore.users.set('newbie', user({ username: 'newbie', password_must_change: true }));
    const res = await app.request('/admin/api/login', {
      method: 'POST',
      body: JSON.stringify({ username: 'newbie', password: PASSWORD }),
    });
    const login = (await res.json()) as { token: string; password_must_change: boolean };
    expect(login.password_must_change).toBe(true);
    const barred = await app.request('/admin/api/dashboards/users', authed(login.token));
    expect(barred.status).toBe(403);
    expect(await errCode(barred)).toBe('E_PASSWORD_CHANGE_REQUIRED');

    const change = await app.request(
      '/admin/api/me/password',
      authed(login.token, {
        method: 'PATCH',
        body: JSON.stringify({ current_password: PASSWORD, new_password: 'brand-new-pass1' }),
      }),
    );
    expect(change.status).toBe(200);
    const changed = (await change.json()) as { token: string; password_must_change: boolean };
    expect(changed.password_must_change).toBe(false);
    // Pre-change sessions are user-revoked (kv), the fresh token passes RBAC.
    expect(await adminStore.kvGet('revoked_user:newbie')).toBeTruthy();
    const ok = await app.request('/admin/api/dashboards/users', authed(changed.token));
    expect(ok.status).toBe(200);
    // And the new password logs in.
    await loginToken(app, 'newbie', 'brand-new-pass1');
  });

  it('revoke-sessions: 204, kv stamped, and older-iat tokens are rejected', async () => {
    const { app, adminStore } = await setup();
    adminStore.users.set('dave_admin', user({ username: 'dave_admin' }));
    const daveToken = await loginToken(app, 'dave_admin');
    const carlToken = await loginToken(app);
    const res = await app.request(
      '/admin/api/dashboards/users/dave_admin/revoke-sessions',
      authed(carlToken, { method: 'POST' }),
    );
    expect(res.status).toBe(204);
    expect(await adminStore.kvGet('revoked_user:dave_admin')).toBeTruthy();
    // Deterministic enforcement check (avoids same-second iat==revokedAt tie):
    await adminStore.kvPut('revoked_user:dave_admin', String(Math.floor(Date.now() / 1000) + 5));
    const after = await app.request('/admin/api/dashboards/users', authed(daveToken));
    expect(after.status).toBe(401);
    expect(await errCode(after)).toBe('E_AUTH_EXPIRED');
  });
});

// ---------------------------------------------------------------------------

describe('HCW create — qn assignment (12-digit QN, F2 block)', () => {
  // DELIBERATE DIVERGENCE from AS adminHcwsCreate, which auto-assigned from seq 001.
  // At one facility the 12-digit QN space is partitioned by instrument —
  // F1=000, F3 patients=001..099, F2 HCWs=101.. — and f2_hcws cannot see CSPro's
  // keys, so starting at 001 silently handed an HCW a PATIENT's questionnaire number.
  it('auto-assigns facility-9 + next seq in the F2 block (101+), not 001', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const r1 = await app.request(
      '/admin/api/hcws',
      authed(token, { method: 'POST', body: JSON.stringify({ hcw_id: 'hcw-a', facility_id: '040340002' }) }),
    );
    expect(r1.status).toBe(201);
    expect(await r1.json()).toMatchObject({
      hcw_id: 'hcw-a', facility_id: '040340002', qn: '040340002101', status: 'pending',
    });
    const r2 = await app.request(
      '/admin/api/hcws',
      authed(token, { method: 'POST', body: JSON.stringify({ hcw_id: 'hcw-b', facility_id: '040340002' }) }),
    );
    expect(((await r2.json()) as { qn: string }).qn).toBe('040340002102');
  });

  it('never auto-assigns into the F3 patient range (001-099) at the same facility', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    for (let i = 0; i < 5; i++) {
      const r = await app.request(
        '/admin/api/hcws',
        authed(token, {
          method: 'POST',
          body: JSON.stringify({ hcw_id: `hcw-seq-${i}`, facility_id: '040340002' }),
        }),
      );
      const { qn } = (await r.json()) as { qn: string };
      expect(qn).toHaveLength(12);
      expect(qn.startsWith('040340002')).toBe(true);
      // the collision guard: seq must clear the F3 patient block
      expect(Number(qn.slice(9))).toBeGreaterThan(99);
    }
  });

  it('slug facilities get a blank qn; duplicate active hcw_id is 409', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const r = await app.request(
      '/admin/api/hcws',
      authed(token, { method: 'POST', body: JSON.stringify({ hcw_id: 'hcw-demo', facility_id: 'demo-clinic' }) }),
    );
    expect(((await r.json()) as { qn: string }).qn).toBe('');
    const dup = await app.request(
      '/admin/api/hcws',
      authed(token, { method: 'POST', body: JSON.stringify({ hcw_id: 'hcw-demo', facility_id: 'demo-clinic' }) }),
    );
    expect(dup.status).toBe(409);
    expect(await errCode(dup)).toBe('E_CONFLICT');
  });

  it('explicit qn override: uniqueness enforced, 12-digit shape validated', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const r = await app.request(
      '/admin/api/hcws',
      authed(token, {
        method: 'POST',
        body: JSON.stringify({ hcw_id: 'hcw-x', facility_id: '040340002', qn: '040340002777' }),
      }),
    );
    expect(r.status).toBe(201);
    expect(((await r.json()) as { qn: string }).qn).toBe('040340002777');
    const clash = await app.request(
      '/admin/api/hcws',
      authed(token, {
        method: 'POST',
        body: JSON.stringify({ hcw_id: 'hcw-y', facility_id: '040340002', qn: '040340002777' }),
      }),
    );
    expect(clash.status).toBe(409);
    const short = await app.request(
      '/admin/api/hcws',
      authed(token, {
        method: 'POST',
        body: JSON.stringify({ hcw_id: 'hcw-z', facility_id: '040340002', qn: '123' }),
      }),
    );
    expect(short.status).toBe(400);
    expect(await errCode(short)).toBe('E_VALIDATION');
  });

  it('a sequence is NEVER reused — revoked rows still burn their number', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    await app.request(
      '/admin/api/hcws',
      authed(token, { method: 'POST', body: JSON.stringify({ hcw_id: 'hcw-a', facility_id: '040340002' }) }),
    );
    adminStore.hcws[0]!.status = 'revoked'; // hcw-a burned 101, then was revoked
    const r = await app.request(
      '/admin/api/hcws',
      authed(token, { method: 'POST', body: JSON.stringify({ hcw_id: 'hcw-c', facility_id: '040340002' }) }),
    );
    expect(((await r.json()) as { qn: string }).qn).toBe('040340002102');
  });
});

describe('HCW reissue-token — CAS + qn-in-JWT', () => {
  it('mints a device JWT carrying the qn claim; enroll_url from PWA_ORIGIN; audit row written', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    await app.request(
      '/admin/api/hcws',
      authed(token, { method: 'POST', body: JSON.stringify({ hcw_id: 'hcw-a', facility_id: '040340002' }) }),
    );
    const res = await app.request(
      '/admin/api/hcws/hcw-a/reissue-token',
      authed(token, { method: 'POST', body: JSON.stringify({}) }),
    );
    expect(res.status).toBe(200);
    const body = (await res.json()) as {
      hcw_id: string; facility_id: string; qn: string; old_jti: string;
      new_token: string; new_jti: string; expires_at: number; enroll_url: string;
    };
    expect(body.qn).toBe('040340002101');
    expect(body.old_jti).toBe('');
    expect(body.enroll_url.startsWith('https://uhc-hcw.asiansocial.org/enroll?token=')).toBe(true);
    const claims = await verifyJwt(body.new_token, KEY);
    expect(claims.ok).toBe(true);
    if (claims.ok) {
      expect(claims.claims.qn).toBe('040340002101');
      expect(claims.claims.facility_id).toBe('040340002');
      expect(claims.claims.jti).toBe(body.new_jti);
    }
    expect(adminStore.tokenAudits).toHaveLength(1);
    expect(adminStore.tokenAudits[0]!.jti).toBe(body.new_jti);
    expect(adminStore.hcws[0]!.enrollment_token_jti).toBe(body.new_jti);
    expect(adminStore.hcws[0]!.status).toBe('enrolled');
  });

  it('CAS: stale prev_jti gets 409 E_CAS_FAILED; matching prev_jti rotates', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    await app.request(
      '/admin/api/hcws',
      authed(token, { method: 'POST', body: JSON.stringify({ hcw_id: 'hcw-a', facility_id: '040340002' }) }),
    );
    const first = (await (
      await app.request('/admin/api/hcws/hcw-a/reissue-token', authed(token, { method: 'POST', body: '{}' }))
    ).json()) as { new_jti: string };
    const stale = await app.request(
      '/admin/api/hcws/hcw-a/reissue-token',
      authed(token, { method: 'POST', body: JSON.stringify({ prev_jti: '' }) }),
    );
    expect(stale.status).toBe(409);
    expect(await errCode(stale)).toBe('E_CAS_FAILED');
    const rotate = await app.request(
      '/admin/api/hcws/hcw-a/reissue-token',
      authed(token, { method: 'POST', body: JSON.stringify({ prev_jti: first.new_jti }) }),
    );
    expect(rotate.status).toBe(200);
    const missing = await app.request(
      '/admin/api/hcws/hcw-nope/reissue-token',
      authed(token, { method: 'POST', body: '{}' }),
    );
    expect(missing.status).toBe(404);
    expect(await errCode(missing)).toBe('E_NOT_FOUND');
  });
});

// ---------------------------------------------------------------------------

describe('data dashboards (dash_data reads)', () => {
  it('responses list: filters + newest-first + rows/total/has_more paging', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    store.responses.set('c1', respRow({ submission_id: 'srv-1', client_submission_id: 'c1', submitted_at_server: '2026-07-01T00:00:00.000Z' }));
    store.responses.set('c2', respRow({ submission_id: 'srv-2', client_submission_id: 'c2', submitted_at_server: '2026-07-02T00:00:00.000Z', status: 'refusal' }));
    store.responses.set('c3', respRow({ submission_id: 'srv-3', client_submission_id: 'c3', submitted_at_server: '2026-07-03T00:00:00.000Z', facility_id: '050110001' }));
    const all = (await (
      await app.request('/admin/api/dashboards/data/responses', authed(token))
    ).json()) as { rows: Array<{ submission_id: string }>; total: number; has_more: boolean };
    expect(all.total).toBe(3);
    expect(all.rows.map((r) => r.submission_id)).toEqual(['srv-3', 'srv-2', 'srv-1']); // newest first
    const refusals = (await (
      await app.request('/admin/api/dashboards/data/responses?status=refusal', authed(token))
    ).json()) as { rows: unknown[]; total: number };
    expect(refusals.total).toBe(1);
    const paged = (await (
      await app.request('/admin/api/dashboards/data/responses?limit=2&offset=0', authed(token))
    ).json()) as { rows: unknown[]; has_more: boolean };
    expect(paged.rows).toHaveLength(2);
    expect(paged.has_more).toBe(true);
    const byFacility = (await (
      await app.request('/admin/api/dashboards/data/responses?facility_id=050110001', authed(token))
    ).json()) as { total: number };
    expect(byFacility.total).toBe(1);
  });

  it('response by id: 200 row / 404 E_NOT_FOUND', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    store.responses.set('c1', respRow());
    const found = await app.request('/admin/api/dashboards/data/responses/srv-1', authed(token));
    expect(found.status).toBe(200);
    expect(((await found.json()) as { submission_id: string }).submission_id).toBe('srv-1');
    const missing = await app.request('/admin/api/dashboards/data/responses/srv-nope', authed(token));
    expect(missing.status).toBe(404);
    expect(await errCode(missing)).toBe('E_NOT_FOUND');
  });

  it('hcws list: Manila-day created_at window filters rows (filter bar 2026-07-17)', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    adminStore.hcws.push(
      { hcw_id: 'h-old', facility_id: '040340210', facility_name: '', enrollment_token_jti: '', token_issued_at: '', token_revoked_at: '', status: 'enrolled', created_at: '2026-07-10T02:00:00.000Z', qn: '' },
      { hcw_id: 'h-new', facility_id: '040340210', facility_name: '', enrollment_token_jti: '', token_issued_at: '', token_revoked_at: '', status: 'enrolled', created_at: '2026-07-16T02:00:00.000Z', qn: '' },
    );
    const windowed = (await (
      await app.request('/admin/api/dashboards/data/hcws?from=2026-07-16&to=2026-07-16', authed(token))
    ).json()) as { rows: Array<{ hcw_id: string }>; total: number };
    expect(windowed.total).toBe(1);
    expect(windowed.rows[0]!.hcw_id).toBe('h-new');
    const all = (await (
      await app.request('/admin/api/dashboards/data/hcws', authed(token))
    ).json()) as { total: number };
    expect(all.total).toBe(2);
  });

  it('audit-event-types: distinct sorted values, auth required', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    // The login above already wrote an admin_login audit row.
    const res = await app.request('/admin/api/dashboards/data/audit-event-types', authed(token));
    expect(res.status).toBe(200);
    const body = (await res.json()) as { rows: string[]; total: number };
    expect(body.rows).toContain('admin_login');
    expect([...body.rows].sort()).toEqual(body.rows); // sorted
    expect(new Set(body.rows).size).toBe(body.rows.length); // distinct
    const anon = await app.request('/admin/api/dashboards/data/audit-event-types');
    expect(anon.status).toBe(401);
  });

  it('facility-options: name-sorted id+name pairs, archived excluded, auth required', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    const fac = (id: string, name: string, archived = false) => ({
      facility_id: id, facility_name: name, facility_type: 'Hospital',
      region: 'REGION IV-A (CALABARZON)', province: 'LAGUNA', city_mun: 'X', barangay: '',
      archived,
    });
    store.facilities = [
      fac('050110001', 'Zeta Health Center'),
      fac('040340210', 'LPH-Bay District Hospital'),
      fac('040340999', 'Old Annex', true),
    ];
    const res = await app.request('/admin/api/dashboards/data/facility-options', authed(token));
    expect(res.status).toBe(200);
    const body = (await res.json()) as { rows: Array<{ facility_id: string; facility_name: string }>; total: number };
    expect(body.total).toBe(2); // archived row excluded
    expect(body.rows.map((r) => r.facility_name)).toEqual(['LPH-Bay District Hospital', 'Zeta Health Center']);
    expect(body.rows[0]!.facility_id).toBe('040340210');
    const anon = await app.request('/admin/api/dashboards/data/facility-options');
    expect(anon.status).toBe(401);
  });

  it('audit list surfaces admin events (login writes admin_login rows)', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const res = await app.request('/admin/api/dashboards/data/audit?event_type=admin_login', authed(token));
    expect(res.status).toBe(200);
    const body = (await res.json()) as { rows: Array<{ event_type: string; actor_username: string }>; total: number };
    expect(body.total).toBeGreaterThanOrEqual(1);
    expect(body.rows[0]!.event_type).toBe('admin_login');
    expect(body.rows[0]!.actor_username).toBe('carl');
  });

  it('hcws list includes qn and honors filters', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    await app.request('/admin/api/hcws', authed(token, { method: 'POST', body: JSON.stringify({ hcw_id: 'hcw-a', facility_id: '040340002' }) }));
    await app.request('/admin/api/hcws', authed(token, { method: 'POST', body: JSON.stringify({ hcw_id: 'hcw-b', facility_id: '050110001' }) }));
    const all = (await (
      await app.request('/admin/api/dashboards/data/hcws', authed(token))
    ).json()) as { rows: Array<{ hcw_id: string; qn: string; status: string }>; total: number };
    expect(all.total).toBe(2);
    const filtered = (await (
      await app.request('/admin/api/dashboards/data/hcws?facility_id=040340002', authed(token))
    ).json()) as { rows: Array<{ hcw_id: string; qn: string }>; total: number };
    expect(filtered.total).toBe(1);
    expect(filtered.rows[0]!.qn).toBe('040340002101');
  });

  it('DLQ: list, replay (success removes row / corrupt 502), delete', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    store.dlq.push(
      {
        dlq_id: 'd-ok',
        received_at_server: '2026-07-01T00:00:00.000Z',
        client_submission_id: 'cs-ok',
        reason: 'values must be an object',
        payload_json: JSON.stringify({
          client_submission_id: 'cs-ok',
          spec_version: '2026-04-17-m1',
          hcw_id: 'h1',
          facility_id: '040340002',
          values: { consent_given: 1 },
        }),
      },
      {
        dlq_id: 'd-bad',
        received_at_server: '2026-07-02T00:00:00.000Z',
        client_submission_id: 'cs-bad',
        reason: 'corrupt',
        payload_json: 'not-json{{',
      },
    );
    const list = (await (
      await app.request('/admin/api/dashboards/data/dlq', authed(token))
    ).json()) as { rows: Array<{ dlq_id: string }>; total: number };
    expect(list.total).toBe(2);
    expect(list.rows[0]!.dlq_id).toBe('d-bad'); // newest first

    const replay = await app.request('/admin/api/dashboards/data/dlq/d-ok/replay', authed(token, { method: 'POST' }));
    expect(replay.status).toBe(200);
    expect(await replay.json()).toMatchObject({ status: 'replayed', dlq_id: 'd-ok' });
    expect(store.dlq.map((d) => d.dlq_id)).toEqual(['d-bad']);
    expect(store.responses.has('cs-ok')).toBe(true);

    const corrupt = await app.request('/admin/api/dashboards/data/dlq/d-bad/replay', authed(token, { method: 'POST' }));
    expect(corrupt.status).toBe(502);
    expect(await errCode(corrupt)).toBe('E_DLQ_CORRUPT');

    const del = await app.request('/admin/api/dashboards/data/dlq/d-bad', authed(token, { method: 'DELETE' }));
    expect(del.status).toBe(200);
    expect(await del.json()).toMatchObject({ dlq_id: 'd-bad', status: 'deleted' });
    const delMissing = await app.request('/admin/api/dashboards/data/dlq/d-bad', authed(token, { method: 'DELETE' }));
    expect(delMissing.status).toBe(502);
    expect(await errCode(delMissing)).toBe('E_NOT_FOUND');
  });
});

// ---------------------------------------------------------------------------

describe('paper-encoder submit', () => {
  it('writes via handleSubmit with source_path=paper_encoded + encoded_by/encoded_at; qn accepted', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    const res = await app.request(
      '/admin/api/encode/hcw-9',
      authed(token, {
        method: 'POST',
        body: JSON.stringify({
          client_submission_id: 'enc-1',
          spec_version: '2026-04-17-m1',
          facility_id: '040340002',
          qn: '040340002005',
          values: { Q2: 'Regular', consent_given: 1 },
        }),
      }),
    );
    expect(res.status).toBe(200);
    const body = (await res.json()) as { submission_id: string; status: string; server_timestamp: string };
    expect(body.status).toBe('accepted');
    expect(body.submission_id).toMatch(/^srv-/);
    const row = store.responses.get('enc-1')!;
    expect(row.source_path).toBe('paper_encoded');
    expect(row.encoded_by).toBe('carl');
    expect(row.encoded_at).not.toBe('');
    expect(row.hcw_id).toBe('hcw-9');
    expect(row.qn).toBe('040340002005');
    expect(row.submitted_at_client).not.toBe(''); // server-now fallback for paper
  });

  it('400 E_VALIDATION on missing values; submit-layer failures surface as 502 + code', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    const invalid = await app.request(
      '/admin/api/encode/hcw-9',
      authed(token, { method: 'POST', body: JSON.stringify({ client_submission_id: 'e2', spec_version: 'x' }) }),
    );
    expect(invalid.status).toBe(400);
    expect(await errCode(invalid)).toBe('E_VALIDATION');
    store.config.set('min_accepted_spec_version', '2026-07-02-r6');
    const tooOld = await app.request(
      '/admin/api/encode/hcw-9',
      authed(token, {
        method: 'POST',
        body: JSON.stringify({ client_submission_id: 'e3', spec_version: '2026-04-17-m1', values: {} }),
      }),
    );
    expect(tooOld.status).toBe(502);
    expect(await errCode(tooOld)).toBe('E_SPEC_TOO_OLD');
  });
});

// ---------------------------------------------------------------------------

describe('config: kill-switch + broadcast', () => {
  it('kill-switch GET/PATCH round-trips into f2_config (respondent /exec sees it)', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    const off = await app.request('/admin/api/dashboards/apps/kill-switch', authed(token));
    expect(await off.json()).toEqual({ kill_switch: false });
    const set = await app.request(
      '/admin/api/dashboards/apps/kill-switch',
      authed(token, { method: 'PATCH', body: JSON.stringify({ kill_switch: true }) }),
    );
    expect(set.status).toBe(200);
    expect(await set.json()).toEqual({ kill_switch: true });
    expect(store.config.get('kill_switch')).toBe('true');
    const bad = await app.request(
      '/admin/api/dashboards/apps/kill-switch',
      authed(token, { method: 'PATCH', body: JSON.stringify({ kill_switch: 'yes' }) }),
    );
    expect(bad.status).toBe(400);
  });

  it('broadcast GET/PATCH with the 280-char cap', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const set = await app.request(
      '/admin/api/dashboards/apps/broadcast',
      authed(token, { method: 'PATCH', body: JSON.stringify({ broadcast_message: '  Field sync at 5pm.  ' }) }),
    );
    expect(await set.json()).toEqual({ broadcast_message: 'Field sync at 5pm.' });
    const get = await app.request('/admin/api/dashboards/apps/broadcast', authed(token));
    expect(await get.json()).toEqual({ broadcast_message: 'Field sync at 5pm.' });
    const long = await app.request(
      '/admin/api/dashboards/apps/broadcast',
      authed(token, { method: 'PATCH', body: JSON.stringify({ broadcast_message: 'x'.repeat(281) }) }),
    );
    expect(long.status).toBe(400);
  });
});

// ---------------------------------------------------------------------------

describe('users + roles CRUD', () => {
  it('create user: hash stays server-side, has_password surfaced, conflicts 409', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const res = await app.request(
      '/admin/api/dashboards/users',
      authed(token, {
        method: 'POST',
        body: JSON.stringify({
          username: 'maria_enc', password: 'password123', role_name: 'Administrator', first_name: 'Maria',
        }),
      }),
    );
    expect(res.status).toBe(200);
    const body = (await res.json()) as { user: Record<string, unknown> };
    expect(body.user).toMatchObject({
      username: 'maria_enc', role_name: 'Administrator', has_password: true, password_must_change: true,
    });
    expect(body.user.password_hash).toBeUndefined();
    const dup = await app.request(
      '/admin/api/dashboards/users',
      authed(token, {
        method: 'POST',
        body: JSON.stringify({ username: 'maria_enc', password: 'password123', role_name: 'Administrator' }),
      }),
    );
    expect(dup.status).toBe(409);
    const short = await app.request(
      '/admin/api/dashboards/users',
      authed(token, {
        method: 'POST',
        body: JSON.stringify({ username: 'pete_enc', password: 'short', role_name: 'Administrator' }),
      }),
    );
    expect(short.status).toBe(400);
  });

  it('update user (PATCH) merges fields; password reset re-arms must-change', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    const res = await app.request(
      '/admin/api/dashboards/users/carl',
      authed(token, { method: 'PATCH', body: JSON.stringify({ email: 'clreyes6@up.edu.ph', password: 'rotated-pass-1' }) }),
    );
    expect(res.status).toBe(200);
    const body = (await res.json()) as { user: { email: string; password_must_change: boolean } };
    expect(body.user.email).toBe('clreyes6@up.edu.ph');
    expect(body.user.password_must_change).toBe(true);
    expect(adminStore.users.get('carl')!.password_hash).not.toBe(PASS_HASH);
    const missing = await app.request(
      '/admin/api/dashboards/users/ghost_user',
      authed(token, { method: 'PATCH', body: JSON.stringify({ email: 'x@y.z' }) }),
    );
    expect(missing.status).toBe(404);
  });

  it('delete guards: self-delete 409, last-Administrator orphan 409, else 204', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    const self = await app.request('/admin/api/dashboards/users/carl', authed(token, { method: 'DELETE' }));
    expect(self.status).toBe(409);
    // Manager (non-admin role w/ dash_users) tries to delete the only Administrator.
    adminStore.roles.set('Manager', role({ name: 'Manager', is_builtin: false }));
    adminStore.users.set('mgr_user', user({ username: 'mgr_user', role_name: 'Manager' }));
    const mgrToken = await loginToken(app, 'mgr_user');
    const orphan = await app.request('/admin/api/dashboards/users/carl', authed(mgrToken, { method: 'DELETE' }));
    expect(orphan.status).toBe(409);
    expect(((await orphan.json()) as { error: { message: string } }).error.message).toBe(
      'cannot orphan the last Administrator',
    );
    const ok = await app.request('/admin/api/dashboards/users/mgr_user', authed(token, { method: 'DELETE' }));
    expect(ok.status).toBe(204);
    expect(adminStore.users.has('mgr_user')).toBe(false);
  });

  it('bulk import: per-row results in input order with created/rejected counts', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const res = await app.request(
      '/admin/api/dashboards/users/bulk-import',
      authed(token, {
        method: 'POST',
        body: JSON.stringify({
          rows: [
            { username: 'op_one', password: 'password123', role_name: 'Administrator' },
            { username: 'x!', password: 'password123', role_name: 'Administrator' },
            { username: 'op_one', password: 'password123', role_name: 'Administrator' },
          ],
        }),
      }),
    );
    expect(res.status).toBe(200);
    const body = (await res.json()) as {
      results: Array<{ username: string; status: string; error?: { code: string } }>;
      total: number;
      created: number;
      rejected: number;
    };
    expect(body.total).toBe(3);
    expect(body.created).toBe(1);
    expect(body.rejected).toBe(2);
    expect(body.results.map((r) => r.status)).toEqual(['created', 'rejected', 'rejected']);
    expect(body.results[2]!.error!.code).toBe('E_CONFLICT');
  });

  it('roles: create needs ≥1 perm, update bumps version once per change, delete guards', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    const empty = await app.request(
      '/admin/api/dashboards/roles',
      authed(token, { method: 'POST', body: JSON.stringify({ name: 'Nothing Role' }) }),
    );
    expect(empty.status).toBe(400);
    const created = await app.request(
      '/admin/api/dashboards/roles',
      authed(token, { method: 'POST', body: JSON.stringify({ name: 'Field Sup', dash_data: true }) }),
    );
    expect(created.status).toBe(200);
    expect(((await created.json()) as { role: { version: number; is_builtin: boolean } }).role).toMatchObject({
      version: 1,
      is_builtin: false,
    });
    const noop = await app.request(
      '/admin/api/dashboards/roles/Field Sup',
      authed(token, { method: 'PATCH', body: JSON.stringify({ dash_data: true }) }),
    );
    const noopBody = (await noop.json()) as { role: { version: number }; changed: boolean };
    expect(noopBody.changed).toBe(false);
    expect(noopBody.role.version).toBe(1);
    const builtin = await app.request('/admin/api/dashboards/roles/Administrator', authed(token, { method: 'DELETE' }));
    expect(builtin.status).toBe(400);
    adminStore.users.set('fsup_user', user({ username: 'fsup_user', role_name: 'Field Sup' }));
    const inUse = await app.request('/admin/api/dashboards/roles/Field Sup', authed(token, { method: 'DELETE' }));
    expect(inUse.status).toBe(409);
    adminStore.users.delete('fsup_user');
    const gone = await app.request('/admin/api/dashboards/roles/Field Sup', authed(token, { method: 'DELETE' }));
    expect(gone.status).toBe(204);
  });
});

// ---------------------------------------------------------------------------

describe('files (FileStore replaces R2)', () => {
  const upload = async (app: Hono, token: string, name = 'guide.pdf', type = 'application/pdf', path?: string) => {
    const form = new FormData();
    form.append('file', new File(['%PDF-1.4 test-bytes'], name, { type }));
    form.append('description', 'reference doc');
    if (path) form.append('path', path);
    return app.request('/admin/api/dashboards/apps/files', authed(token, { method: 'POST', body: form }));
  };

  it('upload → list → download → delete round-trip', async () => {
    const { app, fileStore } = await setup();
    const token = await loginToken(app);
    const up = await upload(app, token);
    expect(up.status).toBe(201);
    const { file } = (await up.json()) as { file: { file_id: string; filename: string; size_bytes: number } };
    expect(file.filename).toBe('guide.pdf');
    expect(fileStore.blobs.size).toBe(1);

    const list = (await (
      await app.request('/admin/api/dashboards/apps/files', authed(token))
    ).json()) as { files: Array<{ file_id: string }>; total: number };
    expect(list.total).toBe(1);

    const dl = await app.request(`/admin/api/dashboards/apps/files/${file.file_id}`, authed(token));
    expect(dl.status).toBe(200);
    expect(dl.headers.get('Content-Disposition')).toBe('attachment; filename="guide.pdf"');
    expect(await dl.text()).toBe('%PDF-1.4 test-bytes');

    const del = await app.request(`/admin/api/dashboards/apps/files/${file.file_id}`, authed(token, { method: 'DELETE' }));
    expect(del.status).toBe(204);
    const dl2 = await app.request(`/admin/api/dashboards/apps/files/${file.file_id}`, authed(token));
    expect(dl2.status).toBe(404);
    const list2 = (await (
      await app.request('/admin/api/dashboards/apps/files', authed(token))
    ).json()) as { total: number };
    expect(list2.total).toBe(0);
  });

  it('upload rejections: disallowed MIME 400, missing file field 400', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const bad = await upload(app, token, 'evil.html', 'text/html');
    expect(bad.status).toBe(400);
    const form = new FormData();
    form.append('description', 'no file');
    const missing = await app.request('/admin/api/dashboards/apps/files', authed(token, { method: 'POST', body: form }));
    expect(missing.status).toBe(400);
    expect(await errCode(missing)).toBe('E_VALIDATION');
  });

  // Audit P3-1: octet-stream passes the MIME allowlist (browsers report it
  // for anything they can't type), so the extension list must gate uploads.
  it('upload rejects an allowed MIME with a disallowed extension', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const exe = await upload(app, token, 'tool.exe', 'application/octet-stream');
    expect(exe.status).toBe(400);
    expect(await errCode(exe)).toBe('E_VALIDATION');
    // A real PDF whose browser only knows it as octet-stream still uploads.
    const genericPdf = await upload(app, token, 'scan.pdf', 'application/octet-stream');
    expect(genericPdf.status).toBe(201);
  });

  it('rename keeps file_id, re-validates extension; folders scope listings', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    const up = await upload(app, token);
    const { file } = (await up.json()) as { file: { file_id: string } };
    const renamed = await app.request(
      `/admin/api/dashboards/apps/files/${file.file_id}`,
      authed(token, { method: 'PATCH', body: JSON.stringify({ filename: 'renamed.pdf' }) }),
    );
    expect(renamed.status).toBe(200);
    expect(((await renamed.json()) as { file: { filename: string } }).file.filename).toBe('renamed.pdf');
    const badExt = await app.request(
      `/admin/api/dashboards/apps/files/${file.file_id}`,
      authed(token, { method: 'PATCH', body: JSON.stringify({ filename: 'evil.exe' }) }),
    );
    expect(badExt.status).toBe(400);

    const folder = await app.request(
      '/admin/api/dashboards/apps/files/folders',
      authed(token, { method: 'POST', body: JSON.stringify({ name: 'Protocols' }) }),
    );
    expect(folder.status).toBe(201);
    expect(((await folder.json()) as { folder: { is_folder: boolean } }).folder.is_folder).toBe(true);
    const dupFolder = await app.request(
      '/admin/api/dashboards/apps/files/folders',
      authed(token, { method: 'POST', body: JSON.stringify({ name: 'Protocols' }) }),
    );
    expect(dupFolder.status).toBe(409);

    await upload(app, token, 'inside.pdf', 'application/pdf', '/Protocols');
    const rootList = (await (
      await app.request('/admin/api/dashboards/apps/files', authed(token))
    ).json()) as { files: Array<{ filename: string }> };
    expect(rootList.files.map((f) => f.filename).sort()).toEqual(['Protocols', 'renamed.pdf']);
    const scoped = (await (
      await app.request('/admin/api/dashboards/apps/files?path=%2FProtocols', authed(token))
    ).json()) as { files: Array<{ filename: string }>; total: number };
    expect(scoped.total).toBe(1);
    expect(scoped.files[0]!.filename).toBe('inside.pdf');
    expect(adminStore.files).toHaveLength(3);
  });
});

// ---------------------------------------------------------------------------

describe('reports, version, apps', () => {
  it('coverage buckets master-less responses as orphans; map report splits GPS/no-GPS', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    store.responses.set('c1', respRow({ submission_id: 's1', client_submission_id: 'c1', facility_id: '040340002', submission_lat: '14.2', submission_lng: '121.1', gps_status: 'granted' }));
    store.responses.set('c2', respRow({ submission_id: 's2', client_submission_id: 'c2', facility_id: '040340002' })); // legacy '' → unknown
    store.responses.set('c3', respRow({ submission_id: 's3', client_submission_id: 'c3', facility_id: '050110001', gps_status: 'denied' }));
    // Audit P0-2: refusals must NOT count as submitted (Facilities-page parity)
    // and must NOT count toward no_gps (GPS is never requested on decline).
    store.responses.set('c4', respRow({ submission_id: 's4', client_submission_id: 'c4', facility_id: '040340002', status: 'refusal' }));
    // This fixture seeds NO master rows — every response lands in the orphan bucket.
    const cov = (await (
      await app.request('/admin/api/dashboards/report/coverage?level=region', authed(token))
    ).json()) as { level: string; rows: Array<Record<string, unknown>>; totals: Record<string, unknown> };
    expect(cov.level).toBe('region');
    expect(cov.rows).toEqual([
      expect.objectContaining({ key: '(not in master)', submitted: 3, refusals: 1, facilities: 0 }),
    ]);
    expect(cov.totals).toMatchObject({ submitted: 3, refusals: 1 });
    const map = (await (
      await app.request('/admin/api/dashboards/report/map', authed(token))
    ).json()) as { markers: Array<{ lat: number }>; no_gps_count: number; no_gps_breakdown: Record<string, number> };
    expect(map.markers).toHaveLength(1);
    expect(map.markers[0]!.lat).toBe(14.2);
    expect(map.no_gps_count).toBe(2);
    // P1-4 instrumentation: missing GPS is named, not just counted.
    expect(map.no_gps_breakdown).toEqual({ unknown: 1, denied: 1 });
  });

  it('date filters use Manila-day half-open windows (audit P2-7)', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    // 2026-07-16T13:19:19Z = 21:19 MNL on the 16th — inside the 07-16 Manila day.
    store.responses.set('c1', respRow({ submission_id: 's1', client_submission_id: 'c1', submitted_at_server: '2026-07-16T13:19:19.000Z' }));
    // 2026-07-16T16:01:00Z = 00:01 MNL on the 17th — outside it.
    store.responses.set('c2', respRow({ submission_id: 's2', client_submission_id: 'c2', submitted_at_server: '2026-07-16T16:01:00.000Z' }));
    const sameDay = (await (
      await app.request('/admin/api/dashboards/data/responses?from=2026-07-16&to=2026-07-16', authed(token))
    ).json()) as { total: number };
    expect(sameDay.total).toBe(1);
    const nextDay = (await (
      await app.request('/admin/api/dashboards/data/responses?from=2026-07-17&to=2026-07-17', authed(token))
    ).json()) as { total: number };
    expect(nextDay.total).toBe(1);
  });

  it('the retired /report/sync route 404s (replaced by /report/coverage)', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const res = await app.request('/admin/api/dashboards/report/sync?level=region', authed(token));
    expect(res.status).toBe(404);
  });

  it('version panel aggregates form revisions with the renamed API fields', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    store.responses.set('c1', respRow({ submission_id: 's1', client_submission_id: 'c1', spec_version: '2026-07-02-r6' }));
    store.responses.set('c2', respRow({ submission_id: 's2', client_submission_id: 'c2' }));
    const version = (await (
      await app.request('/admin/api/dashboards/apps/version', authed(token))
    ).json()) as { pwa_version: string; api_version: string; api_deployed_at: string | null; form_revisions: Array<{ spec_version: string; count: number }>; total_submissions: number };
    expect(version.pwa_version).toBe('unknown');
    expect(version.api_version).toBe('unknown');
    expect(version.api_deployed_at).toBeNull();
    expect(version.form_revisions[0]!.spec_version).toBe('2026-07-02-r6'); // newest first
    expect(version.total_submissions).toBe(2);
  });

  it('the retired quota + data-settings routes 404 (Apps-tab audit removals)', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const quota = await app.request('/admin/api/dashboards/apps/quota', authed(token));
    expect(quota.status).toBe(404);
    const list = await app.request('/admin/api/dashboards/apps/data-settings', authed(token));
    expect(list.status).toBe(404);
    const create = await app.request(
      '/admin/api/dashboards/apps/data-settings',
      authed(token, { method: 'POST', body: JSON.stringify({ interval_minutes: 60, output_path_template: 'f2/{{date}}.csv' }) }),
    );
    expect(create.status).toBe(404);
  });

  it('unknown /admin/api route returns the Worker notFound envelope', async () => {
    const { app } = await setup();
    const res = await app.request('/admin/api/does/not/exist');
    expect(res.status).toBe(404);
    const body = (await res.json()) as { ok: boolean; error: { code: string; message: string } };
    expect(body).toEqual({ ok: false, error: { code: 'E_NOT_FOUND', message: 'route not found' } });
    expect(res.headers.get('X-Request-Id')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Model C — facility-token mint (self-register QR)
// ---------------------------------------------------------------------------

describe('POST /admin/api/facility-token (Model C QR mint)', () => {
  it('mints a durable facility-scoped token that drives /self-register end-to-end', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const res = await app.request(
      '/admin/api/facility-token',
      authed(token, { method: 'POST', body: JSON.stringify({ facility_id: '040340210' }) }),
    );
    expect(res.status).toBe(200);
    const b = (await res.json()) as { facility_id: string; token: string; enroll_url: string };
    expect(b.facility_id).toBe('040340210');
    expect(b.enroll_url).toContain('/enroll?token=');
    // the minted token self-registers a real case with an F2-block QN.
    const reg = await app.request('/self-register', {
      method: 'POST',
      headers: { Authorization: `Bearer ${b.token}` },
    });
    expect(reg.status).toBe(200);
    expect(((await reg.json()) as { qn: string }).qn).toBe('040340210101');
  });

  it('rejects a non-9-digit facility_id', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const res = await app.request(
      '/admin/api/facility-token',
      authed(token, { method: 'POST', body: JSON.stringify({ facility_id: 'slug' }) }),
    );
    expect(res.status).toBe(400);
    expect(await errCode(res)).toBe('E_VALIDATION');
  });

  it('requires the dash_users permission (rejects no-token)', async () => {
    const { app } = await setup();
    const res = await app.request('/admin/api/facility-token', {
      method: 'POST',
      body: JSON.stringify({ facility_id: '040340210' }),
    });
    expect(res.status).toBeGreaterThanOrEqual(401);
  });
});

// ---------------------------------------------------------------------------
// Model C — numbered short-link generation (facility-links)
// ---------------------------------------------------------------------------

describe('POST /admin/api/facility-links (Model C numbered links)', () => {
  // Provision two QN-bearing slots at the facility (ascending qn).
  async function seedTwoSlots(adminStore: InMemoryAdminStore) {
    await adminStore.createHcw({
      hcw_id: 'h1', facility_id: '040340210', facility_name: 'LPH Bay', status: 'pending', qn: '040340210101',
    });
    await adminStore.createHcw({
      hcw_id: 'h2', facility_id: '040340210', facility_name: 'LPH Bay', status: 'pending', qn: '040340210102',
    });
  }

  it('stamps HCW-01..NN slugs + secrets and drives /claim end-to-end', async () => {
    const { app, adminStore } = await setup();
    await seedTwoSlots(adminStore);
    const token = await loginToken(app);
    const res = await app.request(
      '/admin/api/facility-links',
      authed(token, { method: 'POST', body: JSON.stringify({ facility_id: '040340210', short_code: 'lphbay' }) }),
    );
    expect(res.status).toBe(200);
    const b = (await res.json()) as {
      count: number;
      short_code: string;
      links: Array<{ hcw_id: string; qn: string; slug: string; secret: string; enroll_url: string }>;
    };
    expect(b.count).toBe(2);
    expect(b.short_code).toBe('LPHBAY');
    // Ascending qn → HCW-01 is the lowest-qn slot.
    expect(b.links[0]!.slug).toBe('LPHBAY-HCW-01');
    expect(b.links[0]!.qn).toBe('040340210101');
    expect(b.links[1]!.slug).toBe('LPHBAY-HCW-02');
    expect(b.links[0]!.secret).toMatch(/^[0-9a-z]{6}$/);
    expect(b.links[0]!.enroll_url).toBe(
      `https://uhc-hcw.asiansocial.org/e/LPHBAY-HCW-01?k=${b.links[0]!.secret}`,
    );
    // The generated link claims its slot: qn-bound device token comes back.
    const claim = await app.request('/claim', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug: b.links[0]!.slug, k: b.links[0]!.secret }),
    });
    expect(claim.status).toBe(200);
    const cb = (await claim.json()) as { ok: boolean; hcw_id: string; qn: string };
    expect(cb.ok).toBe(true);
    expect(cb.hcw_id).toBe('h1');
    expect(cb.qn).toBe('040340210101');
  });

  // Shared helper: generate links, optionally rotating.
  const genLinks = (
    app: Awaited<ReturnType<typeof setup>>['app'],
    token: string,
    rotate?: boolean,
  ) =>
    app
      .request(
        '/admin/api/facility-links',
        authed(token, {
          method: 'POST',
          body: JSON.stringify({
            facility_id: '040340210',
            short_code: 'LPHBAY',
            ...(rotate ? { rotate: true } : {}),
          }),
        }),
      )
      .then(
        (r) =>
          r.json() as Promise<{
            issued: number;
            skipped: number;
            rotated: boolean;
            links: Array<{ slug: string; secret: string | null; already_issued: boolean }>;
          }>,
      );

  it('is non-destructive by default: a plain re-run skips issued slots, printed card survives', async () => {
    const { app, adminStore } = await setup();
    await seedTwoSlots(adminStore);
    const token = await loginToken(app);

    const first = await genLinks(app, token);
    expect(first.issued).toBe(2);
    expect(first.skipped).toBe(0);
    const firstLink = first.links[0]!;
    expect(firstLink.secret).toMatch(/^[0-9a-z]{6}$/);

    // Second call, NO rotate flag → nothing re-minted; secrets not re-shown.
    const second = await genLinks(app, token);
    expect(second.issued).toBe(0);
    expect(second.skipped).toBe(2);
    const secondLink = second.links[0]!;
    expect(secondLink.slug).toBe(firstLink.slug); // slug stable per slot
    expect(secondLink.already_issued).toBe(true);
    expect(secondLink.secret).toBeNull();

    // The ORIGINAL secret still claims — the printed card was NOT invalidated.
    const stillGood = await app.request('/claim', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug: firstLink.slug, k: firstLink.secret }),
    });
    expect(stillGood.status).toBe(200);
  });

  it('rotate:true mints fresh secrets and invalidates the old ones', async () => {
    const { app, adminStore } = await setup();
    await seedTwoSlots(adminStore);
    const token = await loginToken(app);

    const first = (await genLinks(app, token)).links[0]!;
    const rot = await genLinks(app, token, true);
    expect(rot.rotated).toBe(true);
    expect(rot.issued).toBe(2);
    const second = rot.links[0]!;
    expect(second.slug).toBe(first.slug); // slug is stable per slot
    expect(second.secret).not.toBe(first.secret); // secret rotated

    // The OLD secret no longer claims.
    const stale = await app.request('/claim', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug: first.slug, k: first.secret }),
    });
    expect(stale.status).toBe(401);
  });

  it('404 when the facility has no provisioned slots', async () => {
    const { app } = await setup();
    const token = await loginToken(app);
    const res = await app.request(
      '/admin/api/facility-links',
      authed(token, { method: 'POST', body: JSON.stringify({ facility_id: '999999999', short_code: 'LPHBAY' }) }),
    );
    expect(res.status).toBe(404);
    expect(await errCode(res)).toBe('E_NOT_FOUND');
  });

  it('rejects a non-9-digit facility_id and a bad short_code', async () => {
    const { app, adminStore } = await setup();
    await seedTwoSlots(adminStore);
    const token = await loginToken(app);
    const badFac = await app.request(
      '/admin/api/facility-links',
      authed(token, { method: 'POST', body: JSON.stringify({ facility_id: 'slug', short_code: 'LPHBAY' }) }),
    );
    expect(badFac.status).toBe(400);
    const badCode = await app.request(
      '/admin/api/facility-links',
      authed(token, { method: 'POST', body: JSON.stringify({ facility_id: '040340210', short_code: 'a' }) }),
    );
    expect(badCode.status).toBe(400);
  });

  it('requires the dash_users permission (rejects no-token)', async () => {
    const { app } = await setup();
    const res = await app.request('/admin/api/facility-links', {
      method: 'POST',
      body: JSON.stringify({ facility_id: '040340210', short_code: 'LPHBAY' }),
    });
    expect(res.status).toBeGreaterThanOrEqual(401);
  });
});

// ---------------------------------------------------------------------------

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
    expect(rows[0]).toMatchObject({
      slug: 'lphbay',
      url: 'https://uhc-hcw.asiansocial.org/f/lphbay',
    });
  });

  it('re-upsert updates name/active but keeps created_at/created_by; inactive slug stops resolving', async () => {
    const { app, adminStore } = await setup();
    const token = await loginToken(app);
    await upsert(app, token, { slug: 'lphbay', facility_id: '040340210', facility_name: 'Old' });
    const first = await adminStore.getFacilitySlug('lphbay');
    expect((await app.request('/f/resolve?slug=lphbay')).status).toBe(200);
    await upsert(app, token, {
      slug: 'lphbay',
      facility_id: '040340210',
      facility_name: 'New',
      active: false,
    });
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
      // Strict boolean `active`: 0/'false' must 400, never silently re-activate.
      { slug: 'lphbay', facility_id: '040340210', facility_name: 'X', active: 0 },
      { slug: 'lphbay', facility_id: '040340210', facility_name: 'X', active: 'false' },
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
      (
        await upsert(app, viewerToken, {
          slug: 'x1',
          facility_id: '040340210',
          facility_name: 'X',
        })
      ).status,
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

// ---------------------------------------------------------------------------

describe('void response (#831)', () => {
  it('voids a stored row: 200 + prev_status, detail shows voided, audit rows written', async () => {
    const { app, store, adminStore } = await setup();
    const token = await loginToken(app);
    store.responses.set('c1', respRow({ submission_id: 'srv-1', client_submission_id: 'c1', hcw_id: 'h-bad', facility_id: '040340210' }));

    const res = await app.request(
      '/admin/api/dashboards/data/responses/srv-1/void',
      authed(token, { method: 'POST', body: JSON.stringify({ reason: 'encoder pasted token into HCW ID' }) }),
    );
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ submission_id: 'srv-1', status: 'voided', prev_status: 'stored' });

    const detail = (await (
      await app.request('/admin/api/dashboards/data/responses/srv-1', authed(token))
    ).json()) as { status: string };
    expect(detail.status).toBe('voided');

    // Store-level response_voided row (carries the reason) + route-level actor row.
    const audit = (await (
      await app.request('/admin/api/dashboards/data/audit?event_type=response_voided', authed(token))
    ).json()) as { rows: Array<{ payload_json: string; facility_id: string }>; total: number };
    expect(audit.total).toBe(1);
    expect(audit.rows[0]!.facility_id).toBe('040340210');
    expect(JSON.parse(audit.rows[0]!.payload_json)).toEqual({
      submission_id: 'srv-1',
      reason: 'encoder pasted token into HCW ID',
      prev_status: 'stored',
    });
    const actor = (await (
      await app.request('/admin/api/dashboards/data/audit?event_type=admin_void_response', authed(token))
    ).json()) as { rows: Array<{ actor_username: string; event_resource: string }>; total: number };
    expect(actor.total).toBe(1);
    expect(actor.rows[0]!.event_resource).toBe('srv-1');

    // Voided rows stay in the list but drop out of the lite feed (map/revisions).
    const list = (await (
      await app.request('/admin/api/dashboards/data/responses', authed(token))
    ).json()) as { total: number };
    expect(list.total).toBe(1);
    expect(await adminStore.readResponsesLite()).toHaveLength(0);
  });

  it('400s on a blank reason without mutating', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    store.responses.set('c1', respRow({ submission_id: 'srv-1', client_submission_id: 'c1' }));
    const res = await app.request(
      '/admin/api/dashboards/data/responses/srv-1/void',
      authed(token, { method: 'POST', body: JSON.stringify({ reason: '   ' }) }),
    );
    expect(res.status).toBe(400);
    expect(await errCode(res)).toBe('E_VALIDATION');
    expect(store.responses.get('c1')!.status).toBe('stored');
  });

  it('404s on an unknown id, 409s on a repeat void', async () => {
    const { app, store } = await setup();
    const token = await loginToken(app);
    store.responses.set('c1', respRow({ submission_id: 'srv-1', client_submission_id: 'c1' }));
    const missing = await app.request(
      '/admin/api/dashboards/data/responses/srv-nope/void',
      authed(token, { method: 'POST', body: JSON.stringify({ reason: 'x' }) }),
    );
    expect(missing.status).toBe(404);
    const first = await app.request(
      '/admin/api/dashboards/data/responses/srv-1/void',
      authed(token, { method: 'POST', body: JSON.stringify({ reason: 'x' }) }),
    );
    expect(first.status).toBe(200);
    const again = await app.request(
      '/admin/api/dashboards/data/responses/srv-1/void',
      authed(token, { method: 'POST', body: JSON.stringify({ reason: 'x again' }) }),
    );
    expect(again.status).toBe(409);
    expect(await errCode(again)).toBe('E_ALREADY_VOIDED');
  });

  it('requires auth', async () => {
    const { app } = await setup();
    const res = await app.request('/admin/api/dashboards/data/responses/srv-1/void', {
      method: 'POST',
      body: JSON.stringify({ reason: 'x' }),
    });
    expect(res.status).toBe(401);
  });

  it('voided rows drop out of the coverage report counts', async () => {
    const { app, store, adminStore } = await setup();
    const token = await loginToken(app);
    store.facilities = [{
      facility_id: '040340210', facility_name: 'LPH-Bay District Hospital', facility_type: 'Hospital',
      region: 'REGION IV-A (CALABARZON)', province: 'LAGUNA', city_mun: 'Bay', barangay: '',
      archived: false,
    }];
    store.responses.set('c1', respRow({ submission_id: 'srv-1', client_submission_id: 'c1', facility_id: '040340210' }));
    store.responses.set('c2', respRow({ submission_id: 'srv-2', client_submission_id: 'c2', facility_id: '040340210' }));
    await adminStore.voidResponse('srv-2', 'bad row');
    const cov = await adminStore.coverageReport({ level: 'facility' } as never);
    const row = cov.rows.find((r) => r.key === '040340210');
    expect(row?.submitted).toBe(1);
  });
});
