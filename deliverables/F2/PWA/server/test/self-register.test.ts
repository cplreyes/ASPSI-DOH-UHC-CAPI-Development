/**
 * Model C — open self-register (design F2-Model-C-Self-Register-2026-07-16).
 * POST /self-register: a facility-scoped QR token (tablet_id ===
 * SELF_REGISTER_TABLET_ID) → server assigns the next 12-digit QN in the
 * facility's F2 block (reusing the admin-create assigner) → returns the case.
 */
import { describe, expect, it } from 'vitest';
import { createApp } from '../src/app.js';
import { InMemoryStore } from '../src/store.js';
import { InMemoryAdminStore, InMemoryFileStore } from '../src/admin/store.js';
import { mintJwt, SELF_REGISTER_TABLET_ID } from '../src/jwt.js';

const KEY = Buffer.from('test-signing-key-32-bytes-long!!').toString('base64url');
const nowS = () => Math.floor(Date.now() / 1000);

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

const facilityToken = (facilityId = '040340210', over: Record<string, unknown> = {}) =>
  mintJwt(
    {
      jti: 'fac-jti-' + facilityId,
      tablet_id: SELF_REGISTER_TABLET_ID,
      facility_id: facilityId,
      iat: nowS(),
      exp: nowS() + 86400,
      ...over,
    },
    KEY,
  );

const sr = (app: ReturnType<typeof createApp>, token: string) =>
  app.request('/self-register', { method: 'POST', headers: { Authorization: `Bearer ${token}` } });

describe('POST /self-register (Model C)', () => {
  it('assigns the first F2-block QN (…101) + an sr- hcw_id', async () => {
    const { app } = await setup();
    const res = await sr(app, await facilityToken());
    expect(res.status).toBe(200);
    const b = (await res.json()) as { ok: boolean; hcw_id: string; qn: string; facility_id: string };
    expect(b.ok).toBe(true);
    expect(b.facility_id).toBe('040340210');
    expect(b.hcw_id).toMatch(/^sr-/);
    expect(b.qn).toBe('040340210101');
  });

  it('assigns sequential, never-reused QNs across registrations', async () => {
    const { app } = await setup();
    const token = await facilityToken();
    const qns: string[] = [];
    for (let i = 0; i < 3; i++) qns.push(((await (await sr(app, token)).json()) as { qn: string }).qn);
    expect(qns).toEqual(['040340210101', '040340210102', '040340210103']);
    expect(new Set(qns).size).toBe(3);
  });

  it('stays in the F2 block (101+), never colliding with F3 patients (001-099)', async () => {
    const { app } = await setup();
    const b = (await (await sr(app, await facilityToken('040341130'))).json()) as { qn: string };
    expect(Number(b.qn.slice(9))).toBeGreaterThanOrEqual(101);
  });

  it('rejects a per-HCW device token (not a self-register token) with 401', async () => {
    const { app } = await setup();
    const deviceToken = await mintJwt(
      { jti: 'd1', tablet_id: 'tab-1', facility_id: '040340210', iat: nowS(), exp: nowS() + 3600 },
      KEY,
    );
    const res = await sr(app, deviceToken);
    expect(res.status).toBe(401);
    expect(((await res.json()) as { error: { code: string } }).error.code).toBe('E_TOKEN_INVALID');
  });

  it('rejects expired + revoked facility tokens', async () => {
    const { app, store } = await setup();
    const expired = await mintJwt(
      { jti: 'e1', tablet_id: SELF_REGISTER_TABLET_ID, facility_id: '040340210', iat: nowS() - 7200, exp: nowS() - 3600 },
      KEY,
    );
    expect((await sr(app, expired)).status).toBe(401);
    store.revoked.add('fac-jti-040340210');
    const revoked = await sr(app, await facilityToken());
    expect(((await revoked.json()) as { error: { code: string } }).error.code).toBe('E_TOKEN_REVOKED');
  });

  it('400 on a missing bearer', async () => {
    const { app } = await setup();
    const res = await app.request('/self-register', { method: 'POST' });
    expect(res.status).toBe(400);
  });

  it('kill_switch gates it with the AS envelope (HTTP 200)', async () => {
    const { app, store } = await setup();
    store.config.set('kill_switch', 'true');
    const res = await sr(app, await facilityToken());
    expect(res.status).toBe(200);
    expect(((await res.json()) as { ok: boolean; error: { code: string } }).error.code).toBe('E_KILL_SWITCH');
  });

  it('503 when the admin store is absent', async () => {
    const { app } = await setup(false);
    expect((await sr(app, await facilityToken())).status).toBe(503);
  });
});
