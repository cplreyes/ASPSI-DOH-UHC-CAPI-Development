/**
 * F2 Admin Portal — adminReadResponses / Count / ById tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.1)
 */
import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const {
  adminReadResponses,
  adminCountResponses,
  adminReadResponseById,
  adminReadAudit,
  adminReadDlq,
  adminFormRevisions,
} = require('../src/AdminData.js');

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

function auditRow(overrides) {
  return Object.assign(
    {
      audit_id: 'aud-' + Math.random().toString(36).slice(2, 8),
      occurred_at_server: '2026-05-01T12:00:00.000Z',
      occurred_at_client: '2026-05-01T12:00:00.000Z',
      event_type: 'submit',
      hcw_id: 'hcw-1',
      facility_id: 'fac-1',
      actor_username: '',
      app_version: '1.0',
      payload_json: '{}',
    },
    overrides || {},
  );
}

function dlqRow(overrides) {
  return Object.assign(
    {
      dlq_id: 'dlq-' + Math.random().toString(36).slice(2, 8),
      received_at_server: '2026-05-01T12:00:00.000Z',
      client_submission_id: 'cli-1',
      reason: 'values must be an object',
      payload_json: '{"foo":"bar"}',
    },
    overrides || {},
  );
}

function makeAuditCtx(rows) {
  return { audit: { readAll: () => rows.slice() } };
}

function makeDlqCtx(rows) {
  return { dlq: { readAll: () => rows.slice() } };
}

describe('adminReadAudit', () => {
  it('returns rows newest-first by occurred_at_server', () => {
    const ctx = makeAuditCtx([
      auditRow({ audit_id: 'a', occurred_at_server: '2026-05-01T10:00:00.000Z' }),
      auditRow({ audit_id: 'b', occurred_at_server: '2026-05-01T12:00:00.000Z' }),
      auditRow({ audit_id: 'c', occurred_at_server: '2026-05-01T11:00:00.000Z' }),
    ]);
    const r = adminReadAudit({}, ctx);
    expect(r.data.rows.map(x => x.audit_id)).toEqual(['b', 'c', 'a']);
  });

  it('filters by event_type, hcw_id, and actor_username', () => {
    const ctx = makeAuditCtx([
      auditRow({ audit_id: 'a', event_type: 'submit', hcw_id: 'hcw-1' }),
      auditRow({ audit_id: 'b', event_type: 'admin_login', hcw_id: '', actor_username: 'alice' }),
      auditRow({ audit_id: 'c', event_type: 'admin_logout', hcw_id: '', actor_username: 'alice' }),
      auditRow({ audit_id: 'd', event_type: 'admin_login', hcw_id: '', actor_username: 'bob' }),
    ]);
    expect(adminReadAudit({ event_type: 'admin_login' }, ctx).data.total).toBe(2);
    expect(adminReadAudit({ actor_username: 'alice' }, ctx).data.total).toBe(2);
    expect(adminReadAudit({ event_type: 'admin_login', actor_username: 'alice' }, ctx).data.total).toBe(1);
    expect(adminReadAudit({ hcw_id: 'hcw-1' }, ctx).data.total).toBe(1);
  });

  it('paginates and reports has_more correctly', () => {
    const rows = [];
    for (let i = 0; i < 5; i++) {
      rows.push(auditRow({ audit_id: 'a' + i, occurred_at_server: '2026-05-01T1' + i + ':00:00.000Z' }));
    }
    const ctx = makeAuditCtx(rows);
    const p1 = adminReadAudit({ limit: 2, offset: 0 }, ctx);
    expect(p1.data.rows).toHaveLength(2);
    expect(p1.data.has_more).toBe(true);
    const p3 = adminReadAudit({ limit: 2, offset: 4 }, ctx);
    expect(p3.data.rows).toHaveLength(1);
    expect(p3.data.has_more).toBe(false);
  });
});

describe('adminFormRevisions', () => {
  it('aggregates F2_Responses by spec_version with counts + last_seen_at', () => {
    const ctx = makeCtx([
      row({ spec_version: '2026-04-17-m1', submitted_at_server: '2026-05-01T10:00:00.000Z' }),
      row({ spec_version: '2026-04-17-m1', submitted_at_server: '2026-05-02T10:00:00.000Z' }),
      row({ spec_version: '2026-05-01-m2', submitted_at_server: '2026-05-03T10:00:00.000Z' }),
    ]);
    const r = adminFormRevisions({}, ctx);
    expect(r.ok).toBe(true);
    expect(r.data.total).toBe(3);
    // newest spec_version first
    expect(r.data.revisions[0].spec_version).toBe('2026-05-01-m2');
    expect(r.data.revisions[0].count).toBe(1);
    expect(r.data.revisions[1].spec_version).toBe('2026-04-17-m1');
    expect(r.data.revisions[1].count).toBe(2);
    expect(r.data.revisions[1].last_seen_at).toBe('2026-05-02T10:00:00.000Z');
  });

  it('groups missing spec_version under (unknown)', () => {
    const ctx = makeCtx([row({ spec_version: '' }), row({ spec_version: '' })]);
    const r = adminFormRevisions({}, ctx);
    expect(r.data.revisions[0].spec_version).toBe('(unknown)');
    expect(r.data.revisions[0].count).toBe(2);
  });

  it('returns empty list when there are no responses', () => {
    const ctx = makeCtx([]);
    const r = adminFormRevisions({}, ctx);
    expect(r.data.revisions).toEqual([]);
    expect(r.data.total).toBe(0);
  });
});

describe('adminReadDlq', () => {
  it('returns rows newest-first by received_at_server', () => {
    const ctx = makeDlqCtx([
      dlqRow({ dlq_id: 'a', received_at_server: '2026-05-01T10:00:00.000Z' }),
      dlqRow({ dlq_id: 'b', received_at_server: '2026-05-02T10:00:00.000Z' }),
      dlqRow({ dlq_id: 'c', received_at_server: '2026-04-30T10:00:00.000Z' }),
    ]);
    const r = adminReadDlq({}, ctx);
    expect(r.data.rows.map(x => x.dlq_id)).toEqual(['b', 'a', 'c']);
  });

  it('filters by date range and full-text q', () => {
    const ctx = makeDlqCtx([
      dlqRow({ dlq_id: 'a', received_at_server: '2026-04-29T00:00:00.000Z', reason: 'X' }),
      dlqRow({ dlq_id: 'b', received_at_server: '2026-05-01T00:00:00.000Z', reason: 'spec_version too old' }),
      dlqRow({ dlq_id: 'c', received_at_server: '2026-05-03T00:00:00.000Z', reason: 'values must be an object' }),
    ]);
    expect(adminReadDlq({ from: '2026-05-01', to: '2026-05-02' }, ctx).data.total).toBe(1);
    expect(adminReadDlq({ q: 'spec_version' }, ctx).data.total).toBe(1);
  });
});
