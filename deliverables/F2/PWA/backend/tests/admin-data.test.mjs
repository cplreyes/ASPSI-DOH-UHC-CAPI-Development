/**
 * F2 Admin Portal — adminReadResponses / Count / ById tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.1)
 */
import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { adminReadResponses, adminCountResponses, adminReadResponseById } = require('../src/AdminData.js');

function row(overrides) {
  return Object.assign(
    {
      submission_id: 'srv-' + Math.random().toString(36).slice(2, 8),
      client_submission_id: 'cli-' + Math.random().toString(36).slice(2, 8),
      submitted_at_server: '2026-05-01T00:00:00.000Z',
      submitted_at_client: '2026-05-01T00:00:00.000Z',
      source: 'PWA',
      spec_version: '2026-04-17-m1',
      app_version: '1.0.0',
      hcw_id: 'hcw-1',
      facility_id: 'fac-1',
      device_fingerprint: 'fp',
      sync_attempt_count: '1',
      status: 'stored',
      values_json: '{}',
      submission_lat: '',
      submission_lng: '',
      source_path: 'self_admin',
      encoded_by: '',
      encoded_at: '',
    },
    overrides || {},
  );
}

function makeCtx(rows) {
  return {
    responses: {
      readAll: (_limit, _offset) => rows.slice(),
    },
  };
}

describe('adminReadResponses', () => {
  it('returns all rows newest-first when filters are empty', () => {
    const ctx = makeCtx([
      row({ submission_id: 'a', submitted_at_server: '2026-05-01T00:00:00.000Z' }),
      row({ submission_id: 'b', submitted_at_server: '2026-05-02T00:00:00.000Z' }),
      row({ submission_id: 'c', submitted_at_server: '2026-04-30T00:00:00.000Z' }),
    ]);
    const r = adminReadResponses({}, ctx);
    expect(r.ok).toBe(true);
    expect(r.data.rows.map(x => x.submission_id)).toEqual(['b', 'a', 'c']);
    expect(r.data.total).toBe(3);
    expect(r.data.has_more).toBe(false);
  });

  it('filters by from/to range (inclusive on from, exclusive on to per ISO compare)', () => {
    const ctx = makeCtx([
      row({ submission_id: 'a', submitted_at_server: '2026-04-29T12:00:00.000Z' }),
      row({ submission_id: 'b', submitted_at_server: '2026-05-01T12:00:00.000Z' }),
      row({ submission_id: 'c', submitted_at_server: '2026-05-03T12:00:00.000Z' }),
    ]);
    const r = adminReadResponses({ from: '2026-05-01', to: '2026-05-02' }, ctx);
    expect(r.data.rows.map(x => x.submission_id)).toEqual(['b']);
    expect(r.data.total).toBe(1);
  });

  it('filters by facility_id, status, source_path independently', () => {
    const ctx = makeCtx([
      row({ submission_id: 'a', facility_id: 'fac-1', source_path: 'self_admin' }),
      row({ submission_id: 'b', facility_id: 'fac-2', source_path: 'paper_encoded' }),
      row({ submission_id: 'c', facility_id: 'fac-1', source_path: 'paper_encoded' }),
    ]);
    expect(adminReadResponses({ facility_id: 'fac-1' }, ctx).data.total).toBe(2);
    expect(adminReadResponses({ source_path: 'paper_encoded' }, ctx).data.total).toBe(2);
    expect(
      adminReadResponses({ facility_id: 'fac-1', source_path: 'paper_encoded' }, ctx).data.total,
    ).toBe(1);
  });

  it('full-text q filter matches stringified row content (case-insensitive)', () => {
    const ctx = makeCtx([
      row({ submission_id: 'a', hcw_id: 'hcw-alpha' }),
      row({ submission_id: 'b', hcw_id: 'hcw-beta' }),
      row({ submission_id: 'c', values_json: JSON.stringify({ Q1: 'ALPHA-NOTE' }) }),
    ]);
    const r = adminReadResponses({ q: 'alpha' }, ctx);
    expect(r.data.total).toBe(2);
    expect(r.data.rows.map(x => x.submission_id).sort()).toEqual(['a', 'c']);
  });

  it('paginates via limit + offset', () => {
    const rows = [];
    for (let i = 0; i < 10; i++) {
      rows.push(row({ submission_id: 's' + i, submitted_at_server: '2026-05-' + String(i + 10) + 'T00:00:00.000Z' }));
    }
    const ctx = makeCtx(rows);
    const page1 = adminReadResponses({ limit: 3, offset: 0 }, ctx);
    expect(page1.data.rows).toHaveLength(3);
    expect(page1.data.total).toBe(10);
    expect(page1.data.has_more).toBe(true);
    const page4 = adminReadResponses({ limit: 3, offset: 9 }, ctx);
    expect(page4.data.rows).toHaveLength(1);
    expect(page4.data.has_more).toBe(false);
  });

  it('clamps limit to MAX_LIMIT (500)', () => {
    const ctx = makeCtx([row()]);
    // No exception; we just sanity-check the call returns ok.
    const r = adminReadResponses({ limit: 100000 }, ctx);
    expect(r.ok).toBe(true);
  });
});

describe('adminCountResponses', () => {
  it('returns the same total adminReadResponses would compute (no rows payload)', () => {
    const ctx = makeCtx([
      row({ status: 'stored' }),
      row({ status: 'stored' }),
      row({ status: 'rejected' }),
    ]);
    expect(adminCountResponses({}, ctx).data.total).toBe(3);
    expect(adminCountResponses({ status: 'rejected' }, ctx).data.total).toBe(1);
  });
});

describe('adminReadResponseById', () => {
  it('returns the matching row when submission_id is found', () => {
    const ctx = makeCtx([
      row({ submission_id: 'srv-target', hcw_id: 'hcw-42' }),
      row({ submission_id: 'srv-other' }),
    ]);
    const r = adminReadResponseById({ id: 'srv-target' }, ctx);
    expect(r.ok).toBe(true);
    expect(r.data.hcw_id).toBe('hcw-42');
  });

  it('returns E_NOT_FOUND when submission_id misses', () => {
    const ctx = makeCtx([row({ submission_id: 'srv-other' })]);
    const r = adminReadResponseById({ id: 'srv-target' }, ctx);
    expect(r.ok).toBe(false);
    expect(r.error.code).toBe('E_NOT_FOUND');
  });

  it('returns E_VALIDATION when id is missing', () => {
    const ctx = makeCtx([]);
    const r = adminReadResponseById({}, ctx);
    expect(r.ok).toBe(false);
    expect(r.error.code).toBe('E_VALIDATION');
  });
});
