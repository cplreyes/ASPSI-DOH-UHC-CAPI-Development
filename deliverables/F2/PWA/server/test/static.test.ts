/**
 * P3 static serving — the CF Pages `_redirects` replacement. Real files on
 * disk (serveStatic reads fs), covering: asset hit, SPA fallback for deep
 * links (#528 cold /enroll?token=), API paths never falling through to HTML,
 * and API-only mode (P2 dark) staying pure JSON.
 */
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterAll, describe, expect, it } from 'vitest';
import { createApp } from '../src/app.js';
import { InMemoryStore } from '../src/store.js';

const KEY = Buffer.from('test-signing-key-32-bytes-long!!').toString('base64url');

const www = mkdtempSync(join(tmpdir(), 'f2-www-'));
writeFileSync(join(www, 'index.html'), '<!doctype html><title>F2 PWA</title>');
mkdirSync(join(www, 'assets'));
writeFileSync(join(www, 'assets', 'app.js'), 'console.log("bundle");');
afterAll(() => rmSync(www, { recursive: true, force: true }));

describe('static serving (P3, staticDir set)', () => {
  const app = createApp({ jwtSigningKey: KEY, store: new InMemoryStore(), staticDir: www });

  it('serves real files (asset + root index)', async () => {
    const asset = await app.request('/assets/app.js');
    expect(asset.status).toBe(200);
    expect(await asset.text()).toContain('bundle');
    const root = await app.request('/');
    expect(root.status).toBe(200);
    expect(await root.text()).toContain('F2 PWA');
  });

  it('#528: deep links fall back to index.html (cold /enroll?token=, /admin)', async () => {
    for (const path of ['/enroll?token=abc123', '/admin', '/f/lphbay', '/some/deep/route']) {
      const res = await app.request(path);
      expect(res.status).toBe(200);
      expect(res.headers.get('content-type')).toContain('text/html');
      expect(await res.text()).toContain('F2 PWA');
    }
  });

  it('API paths NEVER fall through to the SPA — JSON 404/400, not HTML', async () => {
    const unknownApi = await app.request('/api/nope');
    expect(unknownApi.status).toBe(404);
    expect(((await unknownApi.json()) as { error: { code: string } }).error.code).toBe('E_NOT_FOUND');
    const adminApi = await app.request('/admin/api/nope');
    expect(adminApi.status).toBe(404);
    expect(((await adminApi.json()) as { ok: boolean }).ok).toBe(false);
    const exec = await app.request('/exec?action=config'); // GET, no bearer
    expect(exec.status).toBe(400);
    expect(((await exec.json()) as { error: { code: string } }).error.code).toBe('E_BAD_REQUEST');
  });

  it('POST /verify-token still routes to the API (registration order holds)', async () => {
    const res = await app.request('/verify-token', { method: 'POST', body: '{}' });
    expect(res.status).toBe(400);
    expect(((await res.json()) as { error: { code: string } }).error.code).toBe('E_BAD_REQUEST');
  });
});

describe('API-only mode (P2 dark, no staticDir)', () => {
  const app = createApp({ jwtSigningKey: KEY, store: new InMemoryStore() });

  it('non-API GET is a JSON 404, not HTML', async () => {
    const res = await app.request('/enroll?token=abc');
    expect(res.status).toBe(404);
    expect(((await res.json()) as { error: { code: string } }).error.code).toBe('E_NOT_FOUND');
  });
});
