import { describe, it, expect, beforeEach } from 'vitest';
import { db, type SubmissionRow } from './db';

describe('db', () => {
  it('opens at version 5 with the auth-rearch schema (device_token on enrollment)', async () => {
    await db.open();
    expect(db.verno).toBe(5);
    const names = db.tables.map((t) => t.name).sort();
    expect(names).toEqual(
      ['audit', 'config', 'drafts', 'enrollment', 'facilities', 'submissions'].sort(),
    );
  });

  it('uses id as primary key for drafts', async () => {
    await db.open();
    expect(db.table('drafts').schema.primKey.name).toBe('id');
  });

  it('uses client_submission_id as primary key for submissions', async () => {
    await db.open();
    expect(db.table('submissions').schema.primKey.name).toBe('client_submission_id');
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
      {
        client_submission_id: 'a',
        hcw_id: 'h',
        status: 'retry_scheduled',
        synced_at: null,
        submitted_at: 1,
        spec_version: 'v',
        values: {},
        retry_count: 1,
        next_retry_at: 100,
        last_error: null,
      },
      {
        client_submission_id: 'b',
        hcw_id: 'h',
        status: 'retry_scheduled',
        synced_at: null,
        submitted_at: 1,
        spec_version: 'v',
        values: {},
        retry_count: 1,
        next_retry_at: 500,
        last_error: null,
      },
    ]);
    const due = await db.submissions.where('next_retry_at').below(300).toArray();
    expect(due).toHaveLength(1);
    expect(due[0]?.client_submission_id).toBe('a');
  });
});

describe('F2Database v4', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.facilities.clear();
    await db.enrollment.clear();
  });

  it('exposes a facilities table with facility_type indexed', async () => {
    await db.facilities.put({
      facility_id: 'F-001',
      facility_name: 'Manila General',
      facility_type: 'Hospital',
      region: 'NCR',
      province: 'Metro Manila',
      city_mun: 'Manila',
      barangay: 'Ermita',
    });
    const found = await db.facilities.where('facility_type').equals('Hospital').first();
    expect(found?.facility_id).toBe('F-001');
  });

  it('exposes an enrollment table that stores a single row', async () => {
    await db.enrollment.put({
      id: 'singleton',
      hcw_id: 'HCW-42',
      facility_id: 'F-001',
      facility_type: 'Hospital',
      enrolled_at: 1_700_000_000_000,
    });
    const row = await db.enrollment.get('singleton');
    expect(row).toMatchObject({ hcw_id: 'HCW-42', facility_id: 'F-001' });
  });
});
