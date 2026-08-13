/**
 * Parity suite — the same cases the AS backend's handlers.test.mjs covers,
 * plus the /exec HTTP surface. If these pass, the PWA's sync-client sees an
 * identical backend.
 */
import { describe, expect, it } from 'vitest';
import { createApp } from '../src/app.js';
import { handleBatchSubmit, handleSubmit } from '../src/handlers.js';
import { InMemoryStore } from '../src/store.js';
import { mintJwt } from '../src/jwt.js';

const KEY = Buffer.from('test-signing-key-32-bytes-long!!').toString('base64url');
const nowS = () => Math.floor(Date.now() / 1000);

const mkPayload = (over: Record<string, unknown> = {}) => ({
  client_submission_id: 'csid-1',
  spec_version: '2026-04-17-m1',
  hcw_id: 'hcw-1',
  facility_id: '040340002',
  qn: '040340002001',
  values: { Q2: 'Regular', consent_given: 1 },
  ...over,
});

describe('handleSubmit (AS parity)', () => {
  it('accepts a fresh submission with srv- id + ISO server_timestamp, persists qn', async () => {
    const store = new InMemoryStore();
    const r = await handleSubmit(mkPayload(), store);
    expect(r.ok).toBe(true);
    const d = (r as { data: { submission_id: string; status: string; server_timestamp: string } }).data;
    expect(d.status).toBe('accepted');
    expect(d.submission_id).toMatch(/^srv-/);
    expect(new Date(d.server_timestamp).toString()).not.toBe('Invalid Date');
    expect(store.responses.get('csid-1')!.qn).toBe('040340002001');
    expect(store.responses.get('csid-1')!.status).toBe('stored');
  });

  it('returns duplicate with the ORIGINAL submission_id on a repeated csid', async () => {
    const store = new InMemoryStore();
    const first = await handleSubmit(mkPayload(), store);
    const firstId = (first as { data: { submission_id: string } }).data.submission_id;
    const again = await handleSubmit(mkPayload(), store);
    expect((again as { data: { submission_id: string; status: string } }).data).toMatchObject({
      submission_id: firstId,
      status: 'duplicate',
    });
  });

  it('rejects E_PAYLOAD_INVALID for missing csid / spec_version / values', async () => {
    const store = new InMemoryStore();
    for (const bad of [
      { ...mkPayload(), client_submission_id: undefined },
      { ...mkPayload(), spec_version: undefined },
      { ...mkPayload(), values: undefined },
    ]) {
      const r = await handleSubmit(bad, store);
      expect(r.ok).toBe(false);
      expect((r as { error: { code: string } }).error.code).toBe('E_PAYLOAD_INVALID');
    }
  });

  it('rejects E_SPEC_TOO_OLD below min_accepted_spec_version (lexical compare)', async () => {
    const store = new InMemoryStore();
    store.config.set('min_accepted_spec_version', '2026-07-02-r6');
    const r = await handleSubmit(mkPayload({ spec_version: '2026-04-17-m1' }), store);
    expect((r as { error: { code: string } }).error.code).toBe('E_SPEC_TOO_OLD');
  });

  it('DLQs + rejects E_VALIDATION when values is an array', async () => {
    const store = new InMemoryStore();
    const r = await handleSubmit(mkPayload({ values: [1, 2] }), store);
    expect((r as { error: { code: string } }).error.code).toBe('E_VALIDATION');
    expect(store.dlq).toHaveLength(1);
    expect(store.dlq[0]!.reason).toBe('values must be an object');
  });

  it('#825: consent_given=0 stores status=refusal and forward-only tags the HCW', async () => {
    const store = new InMemoryStore();
    store.hcwStatus.set('hcw-1', 'enrolled');
    store.hcwStatus.set('hcw-2', 'submitted');
    await handleSubmit(mkPayload({ values: { consent_given: 0 } }), store);
    expect(store.responses.get('csid-1')!.status).toBe('refusal');
    expect(store.hcwStatus.get('hcw-1')).toBe('refusal');
    await handleSubmit(
      mkPayload({ client_submission_id: 'csid-2', hcw_id: 'hcw-2', values: { consent_given: 0 } }),
      store,
    );
    expect(store.hcwStatus.get('hcw-2')).toBe('submitted'); // never demoted
  });

  it('successful submit forward-only tags the HCW submitted (closes "In progress")', async () => {
    const store = new InMemoryStore();
    store.hcwStatus.set('sr-abc', 'enrolled');
    store.hcwStatus.set('hcw-refused', 'refusal');
    await handleSubmit(mkPayload({ hcw_id: 'sr-abc' }), store);
    expect(store.responses.get('csid-1')!.status).toBe('stored');
    expect(store.hcwStatus.get('sr-abc')).toBe('submitted');
    // Forward-only: a refusal-tagged case is never promoted by a later submit.
    await handleSubmit(mkPayload({ client_submission_id: 'csid-2', hcw_id: 'hcw-refused' }), store);
    expect(store.hcwStatus.get('hcw-refused')).toBe('refusal');
    // A duplicate re-send tags nothing (early return before the tag branch).
    store.hcwStatus.set('sr-abc', 'enrolled');
    await handleSubmit(mkPayload({ hcw_id: 'sr-abc' }), store);
    expect(store.hcwStatus.get('sr-abc')).toBe('enrolled');
  });

  it('gps_status: whitelisted values persist, junk sanitizes, paper-encode defaults (P1-4)', async () => {
    const store = new InMemoryStore();
    await handleSubmit(mkPayload({ values: { consent_given: 1, gps_status: 'denied' } }), store);
    expect(store.responses.get('csid-1')!.gps_status).toBe('denied');
    // Junk never lands in the column.
    await handleSubmit(
      mkPayload({ client_submission_id: 'csid-2', values: { consent_given: 1, gps_status: '<script>x' } }),
      store,
    );
    expect(store.responses.get('csid-2')!.gps_status).toBe('');
    // Paper-encode path never asks for GPS → not_requested by default.
    await handleSubmit(
      mkPayload({ client_submission_id: 'csid-3', source_path: 'paper_encoded' }),
      store,
    );
    expect(store.responses.get('csid-3')!.gps_status).toBe('not_requested');
  });

  it('legacy payload without qn stores qn as empty (backward compatible)', async () => {
    const store = new InMemoryStore();
    const p = mkPayload();
    delete (p as Record<string, unknown>).qn;
    await handleSubmit(p, store);
    expect(store.responses.get('csid-1')!.qn).toBe('');
  });
});

describe('handleBatchSubmit (AS parity)', () => {
  it('returns per-item results for a mixed batch', async () => {
    const store = new InMemoryStore();
    await handleSubmit(mkPayload({ client_submission_id: 'dup-1' }), store);
    const r = await handleBatchSubmit(
      {
        responses: [
          mkPayload({ client_submission_id: 'new-1' }),
          mkPayload({ client_submission_id: 'dup-1' }),
          { spec_version: '2026-04-17-m1', values: {} }, // missing csid
        ],
      },
      store,
    );
    expect(r.ok).toBe(true);
    const results = (r as { data: { results: Array<{ status: string; client_submission_id: string | null; error?: { code: string } }> } }).data.results;
    expect(results.map((x) => x.status)).toEqual(['accepted', 'duplicate', 'rejected']);
    expect(results[2]!.client_submission_id).toBeNull();
    expect(results[2]!.error!.code).toBe('E_PAYLOAD_INVALID');
  });

  it('rejects >50 with E_BATCH_TOO_LARGE and {} body with E_PAYLOAD_INVALID', async () => {
    const store = new InMemoryStore();
    const big = { responses: Array.from({ length: 51 }, (_, i) => mkPayload({ client_submission_id: 'c' + i })) };
    expect(((await handleBatchSubmit(big, store)) as { error: { code: string } }).error.code).toBe('E_BATCH_TOO_LARGE');
    expect(((await handleBatchSubmit({}, store)) as { error: { code: string } }).error.code).toBe('E_PAYLOAD_INVALID');
  });
});

describe('/exec HTTP surface (Worker parity)', () => {
  const setup = async () => {
    const store = new InMemoryStore();
    const app = createApp({ jwtSigningKey: KEY, store });
    const token = await mintJwt(
      { jti: 'jti-1', tablet_id: 'tab-1', facility_id: '040340002', iat: nowS(), exp: nowS() + 3600, qn: '040340002001' },
      KEY,
    );
    return { store, app, token };
  };

  it('batch-submit end-to-end: sync-client envelope {ok:true,data:{results}}', async () => {
    const { app, token, store } = await setup();
    const res = await app.request('/exec?action=batch-submit', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'text/plain' },
      body: JSON.stringify({ responses: [mkPayload()] }),
    });
    expect(res.status).toBe(200);
    const env = (await res.json()) as { ok: boolean; data: { results: Array<{ status: string }> } };
    expect(env.ok).toBe(true);
    expect(env.data.results[0]!.status).toBe('accepted');
    expect(store.responses.size).toBe(1);
  });

  it('401 E_TOKEN_EXPIRED / E_TOKEN_REVOKED / 400 no-bearer / 400 no-action', async () => {
    const { app, store, token } = await setup();
    const expired = await mintJwt(
      { jti: 'j2', tablet_id: 't2', facility_id: 'f', iat: nowS() - 7200, exp: nowS() - 3600 },
      KEY,
    );
    const r1 = await app.request('/exec?action=batch-submit', { method: 'POST', headers: { Authorization: `Bearer ${expired}` }, body: '{}' });
    expect(r1.status).toBe(401);
    expect(((await r1.json()) as { error: { code: string } }).error.code).toBe('E_TOKEN_EXPIRED');
    store.revoked.add('jti-1');
    const r2 = await app.request('/exec?action=batch-submit', { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: '{}' });
    expect(((await r2.json()) as { error: { code: string } }).error.code).toBe('E_TOKEN_REVOKED');
    const r3 = await app.request('/exec?action=batch-submit', { method: 'POST', body: '{}' });
    expect(r3.status).toBe(400);
    // fresh token — jti-1 was revoked above, and revocation fires BEFORE the action check (Worker parity)
    const fresh = await mintJwt({ jti: 'j5', tablet_id: 't5', facility_id: 'f', iat: nowS(), exp: nowS() + 3600 }, KEY);
    const r4 = await app.request('/exec', { method: 'POST', headers: { Authorization: `Bearer ${fresh}` }, body: '{}' });
    expect(((await r4.json()) as { error: { code: string } }).error.code).toBe('E_BAD_REQUEST');
  });

  it('config + facilities actions serve the AS envelopes', async () => {
    const { app, token, store } = await setup();
    store.facilities.push({ facility_id: '040340002', facility_name: 'Cabuyao City Hospital', facility_type: 'hospital', region: 'Region IV-A (CALABARZON)', province: 'Laguna', city_mun: 'Cabuyao', barangay: 'Marinig' });
    const cfg = (await (await app.request('/exec?action=config', { method: 'GET', headers: { Authorization: `Bearer ${token}` } })).json()) as { ok: boolean; data: Record<string, unknown> };
    expect(cfg.ok).toBe(true);
    expect(cfg.data.kill_switch).toBe(false); // 'false' coerced to boolean, AS parity
    const fac = (await (await app.request('/exec?action=facilities', { method: 'GET', headers: { Authorization: `Bearer ${token}` } })).json()) as { ok: boolean; data: { facilities: Array<{ barangay: string }> } };
    expect(fac.data.facilities).toHaveLength(1);
    expect(fac.data.facilities[0]!.barangay).toBe('Marinig'); // 7-col AS parity (Schema.js FACILITY_MASTER_LIST_COLUMNS)
  });

  it('kill_switch gates every /exec action with the AS envelope (Router.js:27 parity)', async () => {
    const { app, token, store } = await setup();
    store.config.set('kill_switch', 'true');
    for (const req of [
      { path: '/exec?action=submit', method: 'POST', body: '{}' },
      { path: '/exec?action=batch-submit', method: 'POST', body: '{}' },
      { path: '/exec?action=config', method: 'GET' },
      { path: '/exec?action=facilities', method: 'GET' },
    ]) {
      const r = await app.request(req.path, { method: req.method, headers: { Authorization: `Bearer ${token}` }, ...(req.body ? { body: req.body } : {}) });
      expect(r.status).toBe(200); // AS returns the error envelope with HTTP 200 (ContentService)
      const env = (await r.json()) as { ok: boolean; error: { code: string } };
      expect(env.ok).toBe(false);
      expect(env.error.code).toBe('E_KILL_SWITCH');
    }
    store.config.set('kill_switch', 'false');
    const ok = await app.request('/exec?action=config', { method: 'GET', headers: { Authorization: `Bearer ${token}` } });
    expect(((await ok.json()) as { ok: boolean }).ok).toBe(true);
  });

  it('/verify-token returns claims incl. qn; blank for pre-qn tokens', async () => {
    const { app } = await setup();
    const withQn = await mintJwt({ jti: 'j3', tablet_id: 't3', facility_id: '040340002', iat: nowS(), exp: nowS() + 3600, qn: '040340002007' }, KEY);
    const preQn = await mintJwt({ jti: 'j4', tablet_id: 't4', facility_id: 'fac-legacy', iat: nowS(), exp: nowS() + 3600 }, KEY);
    const a = (await (await app.request('/verify-token', { method: 'POST', body: JSON.stringify({ token: withQn }) })).json()) as { claims: { qn: string } };
    expect(a.claims.qn).toBe('040340002007');
    const b = (await (await app.request('/verify-token', { method: 'POST', body: JSON.stringify({ token: preQn }) })).json()) as { claims: { qn: string } };
    expect(b.claims.qn).toBe('');
  });
});
