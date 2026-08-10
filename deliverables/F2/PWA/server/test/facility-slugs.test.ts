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

  it('503 when the admin store is absent', async () => {
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
      ok: boolean;
      token: string;
      hcw_id: string;
      qn: string;
      facility_id: string;
      facility_name: string;
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
