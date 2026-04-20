import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const AdminHandlers = require('../src/AdminHandlers.js');

describe('AdminHandlers module', () => {
  it('exports an object', () => {
    expect(typeof AdminHandlers).toBe('object');
  });
});

describe('verifyAdminToken', () => {
  it('returns true when token matches secret exactly', () => {
    expect(AdminHandlers.verifyAdminToken('abc123', 'abc123')).toBe(true);
  });

  it('returns false when token differs', () => {
    expect(AdminHandlers.verifyAdminToken('abc123', 'abc124')).toBe(false);
  });

  it('returns false when token is shorter', () => {
    expect(AdminHandlers.verifyAdminToken('abc', 'abc123')).toBe(false);
  });

  it('returns false when token is longer', () => {
    expect(AdminHandlers.verifyAdminToken('abc123xxx', 'abc123')).toBe(false);
  });

  it('returns false for empty token', () => {
    expect(AdminHandlers.verifyAdminToken('', 'abc123')).toBe(false);
  });

  it('returns false for null/undefined token', () => {
    expect(AdminHandlers.verifyAdminToken(null, 'abc123')).toBe(false);
    expect(AdminHandlers.verifyAdminToken(undefined, 'abc123')).toBe(false);
  });

  it('returns false when secret is empty (disabled auth)', () => {
    expect(AdminHandlers.verifyAdminToken('abc123', '')).toBe(false);
  });
});

describe('filterResponses', () => {
  const rows = [
    { submission_id: 's1', facility_id: 'fac-1', status: 'stored', submitted_at_server: '2026-04-17T10:00:00.000Z' },
    { submission_id: 's2', facility_id: 'fac-2', status: 'stored', submitted_at_server: '2026-04-18T09:00:00.000Z' },
    { submission_id: 's3', facility_id: 'fac-1', status: 'rejected', submitted_at_server: '2026-04-18T14:00:00.000Z' },
    { submission_id: 's4', facility_id: 'fac-3', status: 'stored', submitted_at_server: '2026-04-19T08:00:00.000Z' },
  ];

  it('returns all rows when filters empty', () => {
    const out = AdminHandlers.filterResponses(rows, {});
    expect(out.map((r) => r.submission_id)).toEqual(['s4', 's3', 's2', 's1']);
  });

  it('filters by facility_id', () => {
    const out = AdminHandlers.filterResponses(rows, { facility_id: 'fac-1' });
    expect(out.map((r) => r.submission_id)).toEqual(['s3', 's1']);
  });

  it('filters by status', () => {
    const out = AdminHandlers.filterResponses(rows, { status: 'rejected' });
    expect(out.map((r) => r.submission_id)).toEqual(['s3']);
  });

  it('filters by date range inclusive (from YYYY-MM-DD)', () => {
    const out = AdminHandlers.filterResponses(rows, { from: '2026-04-18' });
    expect(out.map((r) => r.submission_id)).toEqual(['s4', 's3', 's2']);
  });

  it('filters by date range inclusive (to YYYY-MM-DD)', () => {
    const out = AdminHandlers.filterResponses(rows, { to: '2026-04-18' });
    expect(out.map((r) => r.submission_id)).toEqual(['s3', 's2', 's1']);
  });

  it('combines filters (facility + status + from)', () => {
    const out = AdminHandlers.filterResponses(rows, { facility_id: 'fac-1', status: 'stored', from: '2026-04-01' });
    expect(out.map((r) => r.submission_id)).toEqual(['s1']);
  });

  it('sorts newest first by submitted_at_server', () => {
    const out = AdminHandlers.filterResponses(rows, {});
    expect(out[0].submission_id).toBe('s4');
    expect(out[3].submission_id).toBe('s1');
  });

  it('returns empty array when nothing matches', () => {
    expect(AdminHandlers.filterResponses(rows, { facility_id: 'does-not-exist' })).toEqual([]);
  });
});

describe('filterAudit', () => {
  const rows = [
    { audit_id: 'a1', event_type: 'enroll', hcw_id: 'hcw-1', occurred_at_server: '2026-04-17T10:00:00.000Z' },
    { audit_id: 'a2', event_type: 'submit', hcw_id: 'hcw-2', occurred_at_server: '2026-04-18T09:00:00.000Z' },
    { audit_id: 'a3', event_type: 'enroll', hcw_id: 'hcw-1', occurred_at_server: '2026-04-18T14:00:00.000Z' },
  ];

  it('returns all rows when filters empty (newest first)', () => {
    const out = AdminHandlers.filterAudit(rows, {});
    expect(out.map((r) => r.audit_id)).toEqual(['a3', 'a2', 'a1']);
  });

  it('filters by event_type', () => {
    const out = AdminHandlers.filterAudit(rows, { event_type: 'enroll' });
    expect(out.map((r) => r.audit_id)).toEqual(['a3', 'a1']);
  });

  it('filters by hcw_id', () => {
    const out = AdminHandlers.filterAudit(rows, { hcw_id: 'hcw-2' });
    expect(out.map((r) => r.audit_id)).toEqual(['a2']);
  });

  it('filters by date range', () => {
    const out = AdminHandlers.filterAudit(rows, { from: '2026-04-18', to: '2026-04-18' });
    expect(out.map((r) => r.audit_id)).toEqual(['a3', 'a2']);
  });
});

describe('listDlq', () => {
  const rows = [
    { dlq_id: 'd1', received_at_server: '2026-04-17T10:00:00.000Z', reason: 'values must be an object' },
    { dlq_id: 'd2', received_at_server: '2026-04-18T09:00:00.000Z', reason: 'missing client_submission_id' },
    { dlq_id: 'd3', received_at_server: '2026-04-18T14:00:00.000Z', reason: 'values must be an object' },
  ];

  it('returns all rows, newest first', () => {
    const out = AdminHandlers.listDlq(rows);
    expect(out.map((r) => r.dlq_id)).toEqual(['d3', 'd2', 'd1']);
  });

  it('returns an empty array for empty input', () => {
    expect(AdminHandlers.listDlq([])).toEqual([]);
  });
});

describe('rowsToCsv', () => {
  it('emits header row + data rows with CRLF line endings', () => {
    const csv = AdminHandlers.rowsToCsv(['a', 'b'], [{ a: '1', b: '2' }, { a: '3', b: '4' }]);
    expect(csv).toBe('a,b\r\n1,2\r\n3,4\r\n');
  });

  it('emits just the header when rows are empty', () => {
    expect(AdminHandlers.rowsToCsv(['a', 'b'], [])).toBe('a,b\r\n');
  });

  it('quotes fields containing commas', () => {
    const csv = AdminHandlers.rowsToCsv(['a'], [{ a: 'x,y' }]);
    expect(csv).toBe('a\r\n"x,y"\r\n');
  });

  it('quotes and doubles internal quotes', () => {
    const csv = AdminHandlers.rowsToCsv(['a'], [{ a: 'hello "world"' }]);
    expect(csv).toBe('a\r\n"hello ""world"""\r\n');
  });

  it('quotes fields containing newlines', () => {
    const csv = AdminHandlers.rowsToCsv(['a'], [{ a: 'line1\nline2' }]);
    expect(csv).toBe('a\r\n"line1\nline2"\r\n');
  });

  it('coerces null/undefined to empty string', () => {
    const csv = AdminHandlers.rowsToCsv(['a', 'b'], [{ a: null, b: undefined }]);
    expect(csv).toBe('a,b\r\n,\r\n');
  });

  it('coerces numbers and booleans to strings', () => {
    const csv = AdminHandlers.rowsToCsv(['a', 'b'], [{ a: 42, b: true }]);
    expect(csv).toBe('a,b\r\n42,true\r\n');
  });

  it('omits columns not present on a row (empty string)', () => {
    const csv = AdminHandlers.rowsToCsv(['a', 'b'], [{ a: '1' }]);
    expect(csv).toBe('a,b\r\n1,\r\n');
  });
});
