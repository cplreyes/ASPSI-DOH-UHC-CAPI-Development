/**
 * F2 Admin Portal - Scheduled break-out dispatcher tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.5)
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { runDueSettings, type RunDueDeps } from '../../src/admin/cron';

interface R2Calls {
  put: Array<{ key: string; value: string }>;
}

function makeR2(opts: { putThrows?: boolean }): { r2: RunDueDeps['r2']; calls: R2Calls } {
  const calls: R2Calls = { put: [] };
  const r2: RunDueDeps['r2'] = {
    async put(key, value) {
      calls.put.push({ key, value: typeof value === 'string' ? value : '<stream>' });
      if (opts.putThrows) throw new Error('R2 put failed');
    },
  };
  return { r2, calls };
}

// Mock global fetch — callAppsScript inside cron.ts goes through fetch.
// We capture the action from the request body and respond accordingly.
function mockFetchSequence(responses: Array<{ matchAction: string; body: unknown }>): {
  fetchImpl: typeof fetch;
  calls: Array<{ action: string; payload: unknown }>;
} {
  const calls: Array<{ action: string; payload: unknown }> = [];
  let cursor = 0;
  const fetchImpl: typeof fetch = async (_url, init) => {
    const bodyStr = typeof init?.body === 'string' ? init.body : '';
    const parsed = JSON.parse(bodyStr) as { action: string; payload: unknown };
    calls.push({ action: parsed.action, payload: parsed.payload });
    const next = responses[cursor++];
    if (!next) {
      return new Response(JSON.stringify({ ok: true, data: {} }), { status: 200 });
    }
    if (next.matchAction !== parsed.action) {
      throw new Error(`fetch mock: expected ${next.matchAction}, got ${parsed.action}`);
    }
    return new Response(JSON.stringify(next.body), { status: 200 });
  };
  return { fetchImpl, calls };
}

const DEPS_BASE = {
  appsScriptUrl: 'https://script.example/exec',
  appsScriptHmac: 'test-hmac',
};

beforeEach(() => {
  // No-op console hooks so the cron logger doesn't pollute test output.
  vi.spyOn(console, 'warn').mockImplementation(() => undefined);
  vi.spyOn(console, 'error').mockImplementation(() => undefined);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('runDueSettings', () => {
  it('returns early when AS reports nothing due', async () => {
    const { fetchImpl, calls } = mockFetchSequence([
      { matchAction: 'admin_settings_run_due', body: { ok: true, data: { ran: [], errors: [] } } },
    ]);
    vi.stubGlobal('fetch', fetchImpl);
    const { r2, calls: r2Calls } = makeR2({});
    await runDueSettings({ ...DEPS_BASE, r2 });
    expect(calls).toHaveLength(1);
    expect(calls[0]?.action).toBe('admin_settings_run_due');
    expect(r2Calls.put).toHaveLength(0);
  });

  it('writes each ran CSV to R2 and marks complete', async () => {
    const ran = [
      { setting_id: 's-1', output_path: 'exports/2026-05-02/s-1.csv', csv: 'a,b\r\n1,2\r\n' },
      { setting_id: 's-2', output_path: 'exports/2026-05-02/s-2.csv', csv: 'a\r\n3\r\n' },
    ];
    const { fetchImpl, calls } = mockFetchSequence([
      { matchAction: 'admin_settings_run_due', body: { ok: true, data: { ran, errors: [] } } },
      { matchAction: 'admin_settings_mark_complete', body: { ok: true, data: {} } },
      { matchAction: 'admin_settings_mark_complete', body: { ok: true, data: {} } },
    ]);
    vi.stubGlobal('fetch', fetchImpl);
    const { r2, calls: r2Calls } = makeR2({});
    await runDueSettings({ ...DEPS_BASE, r2 });
    expect(r2Calls.put.map((c) => c.key)).toEqual([
      'exports/2026-05-02/s-1.csv',
      'exports/2026-05-02/s-2.csv',
    ]);
    // Two mark_complete calls, one per setting, both 'success'.
    const markCalls = calls.filter((c) => c.action === 'admin_settings_mark_complete');
    expect(markCalls).toHaveLength(2);
    expect((markCalls[0]?.payload as { status: string }).status).toBe('success');
    expect((markCalls[1]?.payload as { status: string }).status).toBe('success');
  });

  it('marks a setting failed when R2 put throws', async () => {
    const ran = [{ setting_id: 's-1', output_path: 's-1.csv', csv: 'x' }];
    const { fetchImpl, calls } = mockFetchSequence([
      { matchAction: 'admin_settings_run_due', body: { ok: true, data: { ran, errors: [] } } },
      { matchAction: 'admin_settings_mark_complete', body: { ok: true, data: {} } },
    ]);
    vi.stubGlobal('fetch', fetchImpl);
    const { r2 } = makeR2({ putThrows: true });
    await runDueSettings({ ...DEPS_BASE, r2 });
    const markCalls = calls.filter((c) => c.action === 'admin_settings_mark_complete');
    expect(markCalls).toHaveLength(1);
    const payload = markCalls[0]?.payload as { status: string; error_message: string };
    expect(payload.status).toBe('failed');
    expect(payload.error_message).toContain('R2 put failed');
  });

  it('marks AS-side breakout errors complete (so they do not stay running forever)', async () => {
    const errors = [{ setting_id: 's-broken', message: 'output_path_template invalid' }];
    const { fetchImpl, calls } = mockFetchSequence([
      { matchAction: 'admin_settings_run_due', body: { ok: true, data: { ran: [], errors } } },
      { matchAction: 'admin_settings_mark_complete', body: { ok: true, data: {} } },
    ]);
    vi.stubGlobal('fetch', fetchImpl);
    const { r2, calls: r2Calls } = makeR2({});
    await runDueSettings({ ...DEPS_BASE, r2 });
    expect(r2Calls.put).toHaveLength(0);
    const markCalls = calls.filter((c) => c.action === 'admin_settings_mark_complete');
    expect(markCalls).toHaveLength(1);
    const payload = markCalls[0]?.payload as { status: string; setting_id: string };
    expect(payload.status).toBe('failed');
    expect(payload.setting_id).toBe('s-broken');
  });

  it('returns silently when run_due RPC fails (no R2 writes, no mark_complete)', async () => {
    const fetchImpl: typeof fetch = async () =>
      new Response(JSON.stringify({ ok: false, error: { code: 'E_BACKEND', message: 'down' } }), {
        status: 200,
      });
    vi.stubGlobal('fetch', fetchImpl);
    const { r2, calls: r2Calls } = makeR2({});
    await expect(runDueSettings({ ...DEPS_BASE, r2 })).resolves.toBeUndefined();
    expect(r2Calls.put).toHaveLength(0);
  });
});
