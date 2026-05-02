/**
 * Sentinel rejection tests.
 *
 * Load-bearing assertion: admin-session JWTs MUST be rejected by both
 * /verify-token (verify.ts:23) and /exec (exec.ts:45). They share the same
 * JWT_SIGNING_KEY so signatures match; only the `tablet_id` sentinel separates
 * the two token types. If either check is removed in a refactor, a stolen
 * admin session cookie becomes a usable device token.
 *
 * Spec §7.1 (admin/device distinction).
 */
import { describe, expect, it } from 'vitest';
import { handleVerifyToken } from '../src/verify';
import { handleExec } from '../src/exec';
import { mintJwt } from '../src/jwt';
import type { Env, JwtClaims } from '../src/types';

const TEST_KEY = 'YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWE';

function makeEnv(): Env {
  const kv = {
    get: async () => null,
    put: async () => undefined,
    delete: async () => undefined,
    list: async () => ({ keys: [], list_complete: true, cursor: '' }),
  } as unknown as KVNamespace;
  const r2 = {
    put: async () => undefined,
    get: async () => null,
    delete: async () => undefined,
  } as unknown as R2Bucket;
  return {
    JWT_SIGNING_KEY: TEST_KEY,
    APPS_SCRIPT_HMAC: 'unused-in-sentinel-path',
    APPS_SCRIPT_URL: 'http://unreachable.invalid/',
    ADMIN_PASSWORD_HASH: 'unused',
    F2_AUTH: kv,
    F2_ADMIN_R2: r2,
  };
}

async function mintAdminSessionJwt(): Promise<string> {
  const nowS = Math.floor(Date.now() / 1000);
  const claims: JwtClaims = {
    jti: 'admin-jti-test',
    tablet_id: '__admin_session__',
    facility_id: 'admin',
    iat: nowS,
    exp: nowS + 3600,
  };
  return mintJwt(claims, TEST_KEY);
}

async function mintDeviceJwt(): Promise<string> {
  const nowS = Math.floor(Date.now() / 1000);
  const claims: JwtClaims = {
    jti: 'device-jti-test',
    tablet_id: 'tablet-uuid-1',
    facility_id: 'F-001',
    iat: nowS,
    exp: nowS + 3600,
  };
  return mintJwt(claims, TEST_KEY);
}

describe('sentinel rejection: admin-session JWT cannot be used as device token', () => {
  it('handleVerifyToken rejects admin-session JWT with E_TOKEN_INVALID/401', async () => {
    const adminToken = await mintAdminSessionJwt();
    const req = new Request('http://worker.test/verify-token', {
      method: 'POST',
      body: JSON.stringify({ token: adminToken }),
    });
    const resp = await handleVerifyToken(req, makeEnv());
    expect(resp.status).toBe(401);
    const body = (await resp.json()) as { ok: boolean; error: { code: string } };
    expect(body.ok).toBe(false);
    expect(body.error.code).toBe('E_TOKEN_INVALID');
  });

  it('handleExec rejects admin-session JWT with E_TOKEN_INVALID/401', async () => {
    const adminToken = await mintAdminSessionJwt();
    const req = new Request('http://worker.test/exec?action=submit', {
      method: 'POST',
      headers: { Authorization: `Bearer ${adminToken}` },
      body: '{}',
    });
    const resp = await handleExec(req, makeEnv());
    expect(resp.status).toBe(401);
    const body = (await resp.json()) as { ok: boolean; error: { code: string } };
    expect(body.ok).toBe(false);
    expect(body.error.code).toBe('E_TOKEN_INVALID');
  });

  // Positive control: a real device token gets past the sentinel check.
  // (It will then fail at the upstream Apps Script fetch — that's fine, we're
  // only proving the sentinel doesn't reject legitimate device tokens.)
  it('handleVerifyToken accepts a real device JWT (sentinel does not over-reject)', async () => {
    const deviceToken = await mintDeviceJwt();
    const req = new Request('http://worker.test/verify-token', {
      method: 'POST',
      body: JSON.stringify({ token: deviceToken }),
    });
    const resp = await handleVerifyToken(req, makeEnv());
    expect(resp.status).toBe(200);
    const body = (await resp.json()) as { ok: boolean; claims: { facility_id: string } };
    expect(body.ok).toBe(true);
    expect(body.claims.facility_id).toBe('F-001');
  });
});
