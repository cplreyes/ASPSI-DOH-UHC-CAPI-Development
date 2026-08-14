/**
 * Model C — numbered short-link claim (design F2-Model-C-Numbered-Links-2026-07-16).
 * POST /claim: slug (a pre-provisioned HCW slot) + secret `k` → mints a per-HCW
 * device token bound to that slot's QN (same shape as a reissued token), so
 * enrollment/submit/refusal/sync are inherited unchanged.
 */
import { describe, expect, it } from 'vitest';
import { createApp } from '../src/app.js';
import { InMemoryStore } from '../src/store.js';
import { InMemoryAdminStore, InMemoryFileStore } from '../src/admin/store.js';
import { secretHmac } from '../src/enroll-links.js';
import { verifyJwt } from '../src/jwt.js';

const KEY = Buffer.from('test-signing-key-32-bytes-long!!').toString('base64url');

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

/** Seed one provisioned slot with a known slug + secret. */
async function seedSlot(
  adminStore: InMemoryAdminStore,
  opts: Partial<{ hcwId: string; facilityId: string; qn: string; status: string; slug: string; secret: string }> = {},
) {
  const s = {
    hcwId: 'h1',
    facilityId: '040340210',
    qn: '040340210119',
    status: 'pending',
    slug: 'LPHBAY-HCW-19',
    secret: 'a9f3kd',
    ...opts,
  };
  await adminStore.createHcw({
    hcw_id: s.hcwId,
    facility_id: s.facilityId,
    facility_name: 'LPH Bay',
    status: s.status,
    qn: s.qn,
  });
  await adminStore.assignEnrollLink({ hcw_id: s.hcwId, slug: s.slug, secret_hmac: secretHmac(s.secret, KEY) });
  return s;
}

const claim = (app: ReturnType<typeof createApp>, slug: string, k: string) =>
  app.request('/claim', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slug, k }),
  });

const errCode = async (res: Response): Promise<string> =>
  ((await res.json()) as { error: { code: string } }).error.code;

describe('POST /claim (Model C numbered links)', () => {
  it('claims a slot: mints a qn-bound device token', async () => {
    const { app, adminStore } = await setup();
    const s = await seedSlot(adminStore);
    const res = await claim(app, s.slug, s.secret);
    expect(res.status).toBe(200);
    const b = (await res.json()) as {
      ok: boolean;
      token: string;
      hcw_id: string;
      qn: string;
      facility_id: string;
    };
    expect(b.ok).toBe(true);
    expect(b.hcw_id).toBe('h1');
    expect(b.qn).toBe('040340210119');
    expect(b.facility_id).toBe('040340210');
    // The device token verifies and carries the QN + facility (submit inherits it).
    const v = await verifyJwt(b.token, KEY);
    expect(v.ok).toBe(true);
    if (v.ok) {
      expect(v.claims.qn).toBe('040340210119');
      expect(v.claims.facility_id).toBe('040340210');
      expect(v.claims.tablet_id).not.toBe('__self_register__');
    }
  });

  it('is case-insensitive on the slug', async () => {
    const { app, adminStore } = await setup();
    const s = await seedSlot(adminStore);
    expect((await claim(app, 'lphbay-hcw-19', s.secret)).status).toBe(200);
  });

  it('is re-openable until submit (idempotent claim)', async () => {
    const { app, adminStore } = await setup();
    const s = await seedSlot(adminStore);
    expect((await claim(app, s.slug, s.secret)).status).toBe(200);
    expect((await claim(app, s.slug, s.secret)).status).toBe(200);
  });

  it('rejects a wrong secret with the SAME 401 as an unknown slug', async () => {
    const { app, adminStore } = await setup();
    const s = await seedSlot(adminStore);
    const wrong = await claim(app, s.slug, 'wrong0');
    expect(wrong.status).toBe(401);
    expect(await errCode(wrong)).toBe('E_TOKEN_INVALID');
    const unknown = await claim(app, 'NOPE-HCW-01', 'a9f3kd');
    expect(unknown.status).toBe(401);
    expect(await errCode(unknown)).toBe('E_TOKEN_INVALID');
  });

  it('rejects a malformed slug or missing secret with 401', async () => {
    const { app, adminStore } = await setup();
    await seedSlot(adminStore);
    expect((await claim(app, 'not a slug', 'a9f3kd')).status).toBe(401);
    expect((await claim(app, 'LPHBAY-HCW-19', '')).status).toBe(401);
  });

  it('409 when the slot is already submitted / refusal / revoked', async () => {
    for (const status of ['submitted', 'refusal', 'revoked']) {
      const { app, adminStore } = await setup();
      const s = await seedSlot(adminStore, { status });
      const res = await claim(app, s.slug, s.secret);
      expect(res.status).toBe(409);
      expect(await errCode(res)).toBe('E_CONFLICT');
    }
  });

  it('kill_switch gates it with the AS envelope (HTTP 200)', async () => {
    const { app, store, adminStore } = await setup();
    const s = await seedSlot(adminStore);
    store.config.set('kill_switch', 'true');
    const res = await claim(app, s.slug, s.secret);
    expect(res.status).toBe(200);
    expect(await errCode(res)).toBe('E_KILL_SWITCH');
  });

  it('503 when the admin store is absent', async () => {
    const { app } = await setup(false);
    expect((await claim(app, 'LPHBAY-HCW-19', 'a9f3kd')).status).toBe(503);
  });
});
