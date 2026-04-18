import { describe, it, expect, beforeEach, vi } from 'vitest';
import { db, type SubmissionRow } from './db';
import { runSync, type OrchestratorDeps } from './sync-orchestrator';

function mkSubmission(overrides: Partial<SubmissionRow> = {}): SubmissionRow {
  return {
    client_submission_id: overrides.client_submission_id ?? 'csid-' + Math.random().toString(36).slice(2),
    hcw_id: 'hcw-1',
    status: 'pending_sync',
    synced_at: null,
    submitted_at: 1_700_000_000_000,
    spec_version: '2026-04-17-m1',
    values: { Q2: 'Regular' },
    retry_count: 0,
    next_retry_at: null,
    last_error: null,
    ...overrides,
  };
}

function baseDeps(overrides: Partial<OrchestratorDeps> = {}): OrchestratorDeps {
  return {
    postBatchSubmit: vi.fn().mockResolvedValue({ ok: true, results: [] }),
    nowMs: () => 1_700_000_000_000,
    batchSize: 25,
    specVersion: '2026-04-17-m1',
    appVersion: '0.1.0',
    deviceFingerprint: 'test-fp',
    stuckSyncingThresholdMs: 600_000,
    ...overrides,
  };
}

describe('runSync — happy path', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
    await db.config.clear();
  });

  it('drains pending_sync rows to synced on all-accepted response', async () => {
    await db.submissions.bulkPut([
      mkSubmission({ client_submission_id: 'a' }),
      mkSubmission({ client_submission_id: 'b' }),
    ]);
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: true,
        results: [
          { client_submission_id: 'a', submission_id: 'srv-a', status: 'accepted' },
          { client_submission_id: 'b', submission_id: 'srv-b', status: 'accepted' },
        ],
      }),
    });
    const summary = await runSync(deps);
    expect(summary.attempted).toBe(2);
    expect(summary.synced).toBe(2);
    expect(summary.failed).toBe(0);
    const rows = await db.submissions.orderBy('client_submission_id').toArray();
    expect(rows.every((r) => r.status === 'synced')).toBe(true);
    expect(rows.every((r) => r.synced_at === 1_700_000_000_000)).toBe(true);
  });

  it('treats duplicate status as synced (already on server)', async () => {
    await db.submissions.put(mkSubmission({ client_submission_id: 'a' }));
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: true,
        results: [{ client_submission_id: 'a', submission_id: 'srv-a', status: 'duplicate' }],
      }),
    });
    await runSync(deps);
    const row = await db.submissions.get('a');
    expect(row?.status).toBe('synced');
  });

  it('returns synced=0, failed=0 when nothing is pending', async () => {
    const summary = await runSync(baseDeps());
    expect(summary.attempted).toBe(0);
    expect(summary.synced).toBe(0);
  });
});

describe('runSync — rejections', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
    await db.config.clear();
  });

  it('marks per-item E_VALIDATION as rejected with last_error populated', async () => {
    await db.submissions.put(mkSubmission({ client_submission_id: 'a' }));
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: true,
        results: [{ client_submission_id: 'a', status: 'rejected', error: { code: 'E_VALIDATION', message: 'bad' } }],
      }),
    });
    await runSync(deps);
    const row = await db.submissions.get('a');
    expect(row?.status).toBe('rejected');
    expect(row?.last_error?.code).toBe('E_VALIDATION');
  });

  it('sets config.update_available=true when any item returns E_SPEC_TOO_OLD', async () => {
    await db.submissions.bulkPut([
      mkSubmission({ client_submission_id: 'a' }),
      mkSubmission({ client_submission_id: 'b' }),
    ]);
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: true,
        results: [
          { client_submission_id: 'a', status: 'rejected', error: { code: 'E_SPEC_TOO_OLD', message: 'old' } },
          { client_submission_id: 'b', submission_id: 'srv-b', status: 'accepted' },
        ],
      }),
    });
    await runSync(deps);
    const flag = await db.config.get('update_available');
    expect(flag?.value).toBe(true);
  });
});

describe('runSync — transport failures trigger retry_scheduled with backoff', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('on whole-batch transport error, flips rows to retry_scheduled with backoff', async () => {
    await db.submissions.put(mkSubmission({ client_submission_id: 'a', retry_count: 0 }));
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: false,
        transport: true,
        error: { code: 'E_NETWORK', message: 'down' },
      }),
    });
    await runSync(deps);
    const row = await db.submissions.get('a');
    expect(row?.status).toBe('retry_scheduled');
    expect(row?.retry_count).toBe(1);
    expect(row?.next_retry_at).toBe(1_700_000_000_000 + 30_000);
    expect(row?.last_error?.code).toBe('E_NETWORK');
  });

  it('backend-level non-transport failure (ok=false, transport=false) flips rows to rejected', async () => {
    await db.submissions.put(mkSubmission({ client_submission_id: 'a' }));
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: false,
        transport: false,
        error: { code: 'E_KILL_SWITCH', message: 'off' },
      }),
    });
    await runSync(deps);
    const row = await db.submissions.get('a');
    expect(row?.status).toBe('rejected');
    expect(row?.last_error?.code).toBe('E_KILL_SWITCH');
  });
});

describe('runSync — retry eligibility', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('includes retry_scheduled rows whose next_retry_at has passed', async () => {
    await db.submissions.put(mkSubmission({
      client_submission_id: 'ready',
      status: 'retry_scheduled',
      retry_count: 1,
      next_retry_at: 1_699_999_900_000,
    }));
    const postBatchSubmit = vi.fn().mockResolvedValue({
      ok: true,
      results: [{ client_submission_id: 'ready', submission_id: 'srv', status: 'accepted' }],
    });
    await runSync(baseDeps({ postBatchSubmit }));
    expect(postBatchSubmit).toHaveBeenCalled();
    const row = await db.submissions.get('ready');
    expect(row?.status).toBe('synced');
  });

  it('excludes retry_scheduled rows whose next_retry_at is in the future', async () => {
    await db.submissions.put(mkSubmission({
      client_submission_id: 'notyet',
      status: 'retry_scheduled',
      retry_count: 1,
      next_retry_at: 1_700_000_100_000,
    }));
    const postBatchSubmit = vi.fn().mockResolvedValue({ ok: true, results: [] });
    await runSync(baseDeps({ postBatchSubmit }));
    expect(postBatchSubmit).not.toHaveBeenCalled();
  });

  it('reclaims rows stuck in syncing for longer than stuckSyncingThresholdMs', async () => {
    await db.submissions.put(mkSubmission({
      client_submission_id: 'stuck',
      status: 'syncing',
      submitted_at: 1_700_000_000_000 - 700_000,
    }));
    const postBatchSubmit = vi.fn().mockResolvedValue({
      ok: true,
      results: [{ client_submission_id: 'stuck', submission_id: 'srv', status: 'accepted' }],
    });
    await runSync(baseDeps({ postBatchSubmit }));
    const row = await db.submissions.get('stuck');
    expect(row?.status).toBe('synced');
  });
});

describe('runSync — reentrancy guard', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('second concurrent call returns already-running summary without calling the client twice', async () => {
    await db.submissions.put(mkSubmission({ client_submission_id: 'a' }));
    let resolveFetch: (v: unknown) => void = () => {};
    const slow = new Promise((r) => (resolveFetch = r));
    const postBatchSubmit = vi.fn().mockImplementation(async () => {
      await slow;
      return { ok: true, results: [{ client_submission_id: 'a', submission_id: 'x', status: 'accepted' }] };
    });
    const first = runSync(baseDeps({ postBatchSubmit }));
    const second = await runSync(baseDeps({ postBatchSubmit }));
    expect(second.alreadyRunning).toBe(true);
    resolveFetch({});
    await first;
    expect(postBatchSubmit).toHaveBeenCalledTimes(1);
  });
});
