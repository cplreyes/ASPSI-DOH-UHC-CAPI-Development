/**
 * F2 Admin Portal — concurrency: two-admin reissue race (R2-#63 scenario 1).
 *
 * Plan: epic-04-backend-sync-infrastructure.md (E4-APRT-037)
 *
 * Two admins POST /admin/api/hcws/:id/reissue-token simultaneously, each
 * carrying the same prev_jti. Apps Script's CAS guard (`prev_jti must match
 * what's currently on the row`) ensures only one wins; the loser sees
 * E_CAS_FAILED → 409 at the worker layer.
 *
 * Mock topology: a stateful AS callable that mirrors the real AS behavior —
 * holds the current jti in closure, accepts the first request whose
 * prev_jti matches, rejects subsequent requests with E_CAS_FAILED until
 * their prev_jti matches the latest committed value.
 *
 * What this DOES test: worker correctly surfaces E_CAS_FAILED as 409 + the
 * winner mints a real JWT while the loser does NOT mint anything.
 * What this does NOT test: real LockService serialization inside Apps
 * Script — that's AS-internal. Verified via staging smoke test instead.
 */
import { describe, expect, it } from 'vitest';
import { handleReissueToken, type ReissueAsCallable } from '../../src/admin/handlers/hcws';

interface FakeKV {
  put(key: string, value: string, opts?: { expirationTtl?: number }): Promise<void>;
}
function makeKv(): FakeKV {
  return { async put() {} };
}

function fakeKey(): string {
  const bytes = new Uint8Array(32);
  for (let i = 0; i < bytes.length; i++) bytes[i] = i;
  let s = '';
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]!);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
const KEY = fakeKey();

/**
 * AS-shaped CAS callable. Holds the row's current jti in closure; accepts
 * the request iff prev_jti matches and atomically commits new_jti.
 */
function makeStatefulAs(initialJti: string): ReissueAsCallable {
  let currentJti = initialJti;
  let issuedAt = 'unset';
  return async ({ hcw_id, new_jti, prev_jti }) => {
    if (prev_jti !== currentJti) {
      return {
        ok: false,
        error: { code: 'E_CAS_FAILED', message: 'token already reissued by another admin; refresh and retry' },
      };
    }
    const old = currentJti;
    currentJti = new_jti;
    issuedAt = new Date().toISOString();
    return {
      ok: true,
      data: {
        hcw_id,
        facility_id: 'fac-1',
        new_jti,
        old_jti: old,
        token_issued_at: issuedAt,
      },
    };
  };
}

describe('concurrency: two-admin reissue race (R2-#63 scenario 1)', () => {
  it('only the winning admin mints a token; the loser sees 409 E_CAS_FAILED', async () => {
    const as = makeStatefulAs('original-jti');

    // Both admins fire in parallel against the same starting state. Each
    // generates its own new_jti via crypto.randomUUID inside handleReissueToken,
    // so the second resolver hitting AS sees prev_jti='original-jti' but
    // currentJti is whatever the first wrote.
    const reqBody = { prev_jti: 'original-jti' };
    const [resp1, resp2] = await Promise.all([
      handleReissueToken('hcw-001', reqBody, KEY, 'https://pwa.example', as, makeKv()),
      handleReissueToken('hcw-001', reqBody, KEY, 'https://pwa.example', as, makeKv()),
    ]);

    const statuses = [resp1.status, resp2.status].sort();
    // One winner (200) + one loser (409 E_CAS_FAILED).
    expect(statuses).toEqual([200, 409]);

    const winner = resp1.status === 200 ? resp1 : resp2;
    const loser = resp1.status === 409 ? resp1 : resp2;

    // Winner gets a real JWT.
    const winnerBody = (await winner.json()) as { new_token: string; new_jti: string };
    expect(winnerBody.new_token).toMatch(/.+\..+\..+/);
    expect(winnerBody.new_jti).toMatch(/^[0-9a-f-]{36}$/);

    // Loser sees the structured CAS error.
    const loserBody = (await loser.json()) as { error: { code: string; message: string } };
    expect(loserBody.error.code).toBe('E_CAS_FAILED');
    expect(loserBody.error.message).toMatch(/already reissued/);
  });

  it('a third admin retrying after the race with the FRESH prev_jti succeeds', async () => {
    // Models the recovery flow: loser refreshes, reads the new jti from the
    // HCW row, retries with prev_jti = winning new_jti. AS accepts.
    const as = makeStatefulAs('original-jti');

    const first = await handleReissueToken(
      'hcw-001',
      { prev_jti: 'original-jti' },
      KEY,
      'https://pwa.example',
      as,
      makeKv(),
    );
    expect(first.status).toBe(200);
    const firstBody = (await first.json()) as { new_jti: string };

    // Loser refreshes and retries with the new jti.
    const retry = await handleReissueToken(
      'hcw-001',
      { prev_jti: firstBody.new_jti },
      KEY,
      'https://pwa.example',
      as,
      makeKv(),
    );
    expect(retry.status).toBe(200);
  });

  it('ten concurrent admins → exactly one wins, nine see 409', async () => {
    // Stress shape — the CAS contract should hold under arbitrary fan-in.
    const as = makeStatefulAs('original-jti');
    const reqs = Array.from({ length: 10 }, () =>
      handleReissueToken('hcw-001', { prev_jti: 'original-jti' }, KEY, 'https://pwa.example', as, makeKv()),
    );
    const responses = await Promise.all(reqs);
    const statuses = responses.map((r) => r.status);
    const wins = statuses.filter((s) => s === 200).length;
    const losses = statuses.filter((s) => s === 409).length;
    expect(wins).toBe(1);
    expect(losses).toBe(9);
  });
});
