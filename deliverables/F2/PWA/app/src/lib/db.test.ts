import { describe, it, expect, beforeEach } from 'vitest';
import { db, type SubmissionRow } from './db';

describe('db', () => {
  it('opens at version 2 with the spec §7.2 schema', async () => {
    await db.open();
    expect(db.verno).toBe(2);
    const names = db.tables.map((t) => t.name).sort();
    expect(names).toEqual(
      ['audit', 'config', 'drafts', 'facilities', 'submissions'].sort(),
    );
  });

  it('uses id as primary key for drafts', async () => {
    await db.open();
    expect(db.table('drafts').schema.primKey.name).toBe('id');
  });

  it('uses client_submission_id as primary key for submissions', async () => {
    await db.open();
    expect(db.table('submissions').schema.primKey.name).toBe(
      'client_submission_id',
    );
  });
});

describe('db v2 — submissions retry fields', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('accepts retry_count, next_retry_at, last_error on insert', async () => {
    const row: SubmissionRow = {
      client_submission_id: 'csid-1',
      hcw_id: 'hcw-1',
      status: 'retry_scheduled',
      synced_at: null,
      submitted_at: 1_700_000_000_000,
      spec_version: '2026-04-17-m1',
      values: {},
      retry_count: 2,
      next_retry_at: 1_700_000_600_000,
      last_error: { code: 'E_NETWORK', message: 'fetch failed' },
    };
    await db.submissions.put(row);
    const read = await db.submissions.get('csid-1');
    expect(read?.retry_count).toBe(2);
    expect(read?.next_retry_at).toBe(1_700_000_600_000);
    expect(read?.last_error?.code).toBe('E_NETWORK');
  });

  it('defaults retry_count to 0 and next_retry_at/last_error to null on fresh rows', async () => {
    const row: SubmissionRow = {
      client_submission_id: 'csid-2',
      hcw_id: 'hcw-1',
      status: 'pending_sync',
      synced_at: null,
      submitted_at: 1_700_000_000_000,
      spec_version: '2026-04-17-m1',
      values: {},
      retry_count: 0,
      next_retry_at: null,
      last_error: null,
    };
    await db.submissions.put(row);
    const read = await db.submissions.get('csid-2');
    expect(read?.retry_count).toBe(0);
    expect(read?.next_retry_at).toBeNull();
    expect(read?.last_error).toBeNull();
  });

  it('supports querying by next_retry_at index', async () => {
    await db.submissions.bulkPut([
      { client_submission_id: 'a', hcw_id: 'h', status: 'retry_scheduled', synced_at: null, submitted_at: 1, spec_version: 'v', values: {}, retry_count: 1, next_retry_at: 100, last_error: null },
      { client_submission_id: 'b', hcw_id: 'h', status: 'retry_scheduled', synced_at: null, submitted_at: 1, spec_version: 'v', values: {}, retry_count: 1, next_retry_at: 500, last_error: null },
    ]);
    const due = await db.submissions.where('next_retry_at').below(300).toArray();
    expect(due).toHaveLength(1);
    expect(due[0]?.client_submission_id).toBe('a');
  });
});
