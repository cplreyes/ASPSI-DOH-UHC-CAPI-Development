/**
 * F2 Admin Portal — adminSyncReport + adminMapReport tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 2.10, 2.12)
 */
import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { adminSyncReport, adminMapReport, _extractGeoKey } = require('../src/AdminReports.js');

function row(overrides) {
  return Object.assign(
    {
      submission_id: 'srv-' + Math.random().toString(36).slice(2, 8),
      submitted_at_server: '2026-05-01T00:00:00.000Z',
      facility_id: '050102001',
      hcw_id: 'hcw-1',
      submission_lat: '',
      submission_lng: '',
    },
    overrides || {},
  );
}

function makeCtx(rows) {
  return { responses: { readAll: () => rows.slice() } };
}

describe('_extractGeoKey', () => {
  it('extracts 2 chars for region, 4 for province, full for facility', () => {
    expect(_extractGeoKey('050102001', 'region')).toBe('05');
    expect(_extractGeoKey('050102001', 'province')).toBe('0501');
    expect(_extractGeoKey('050102001', 'facility')).toBe('050102001');
  });

  it('returns empty string for missing facility_id', () => {
    expect(_extractGeoKey('', 'region')).toBe('');
    expect(_extractGeoKey(null, 'region')).toBe('');
  });
});

describe('adminSyncReport', () => {
  it('aggregates by region by default', () => {
    const ctx = makeCtx([
      row({ facility_id: '050101001' }),
      row({ facility_id: '050102002' }),
      row({ facility_id: '060201001' }),
    ]);
    const r = adminSyncReport({}, ctx);
    expect(r.ok).toBe(true);
    expect(r.data.level).toBe('region');
    expect(r.data.pivot).toHaveLength(2);
    expect(r.data.pivot[0].key).toBe('05');
    expect(r.data.pivot[0].submitted).toBe(2);
    expect(r.data.pivot[1].key).toBe('06');
    expect(r.data.pivot[1].submitted).toBe(1);
    expect(r.data.totals.submitted).toBe(3);
    expect(r.data.totals.keys).toBe(2);
  });

  it('aggregates at province level when requested', () => {
    const ctx = makeCtx([
      row({ facility_id: '050101001' }),
      row({ facility_id: '050101002' }),
      row({ facility_id: '050201003' }),
    ]);
    const r = adminSyncReport({ level: 'province' }, ctx);
    expect(r.data.pivot).toHaveLength(2);
    expect(r.data.pivot[0].key).toBe('0501');
    expect(r.data.pivot[0].submitted).toBe(2);
  });

  it('records the latest submitted_at per key', () => {
    const ctx = makeCtx([
      row({ facility_id: '050101001', submitted_at_server: '2026-05-01T10:00:00.000Z' }),
      row({ facility_id: '050102002', submitted_at_server: '2026-05-03T10:00:00.000Z' }),
    ]);
    const r = adminSyncReport({}, ctx);
    expect(r.data.pivot[0].last_submitted_at).toBe('2026-05-03T10:00:00.000Z');
  });

  it('respects from/to date range', () => {
    const ctx = makeCtx([
      row({ facility_id: '050101001', submitted_at_server: '2026-04-29T00:00:00.000Z' }),
      row({ facility_id: '050102002', submitted_at_server: '2026-05-01T00:00:00.000Z' }),
      row({ facility_id: '050103003', submitted_at_server: '2026-05-03T00:00:00.000Z' }),
    ]);
    const r = adminSyncReport({ from: '2026-05-01', to: '2026-05-02' }, ctx);
    expect(r.data.totals.submitted).toBe(1);
  });

  it('expected stays null until F2_SampleFrame ships', () => {
    const ctx = makeCtx([row({ facility_id: '050101001' })]);
    const r = adminSyncReport({}, ctx);
    expect(r.data.pivot[0].expected).toBeNull();
    expect(r.data.pivot[0].percent_complete).toBeNull();
    expect(r.data.totals.expected).toBeNull();
  });
});

describe('adminMapReport', () => {
  it('returns markers only for rows with valid lat/lng; counts no_gps separately', () => {
    const ctx = makeCtx([
      row({ submission_id: 'a', submission_lat: 14.5995, submission_lng: 120.9842 }),
      row({ submission_id: 'b', submission_lat: '', submission_lng: '' }),
      row({ submission_id: 'c', submission_lat: 13.5, submission_lng: 121.5 }),
    ]);
    const r = adminMapReport({}, ctx);
    expect(r.data.markers).toHaveLength(2);
    expect(r.data.no_gps_count).toBe(1);
    expect(r.data.markers.map(m => m.submission_id).sort()).toEqual(['a', 'c']);
  });

  it('filters by region_id (2-char facility prefix)', () => {
    const ctx = makeCtx([
      row({ submission_id: 'a', facility_id: '050101001', submission_lat: 1, submission_lng: 1 }),
      row({ submission_id: 'b', facility_id: '060201001', submission_lat: 2, submission_lng: 2 }),
    ]);
    const r = adminMapReport({ region_id: '05' }, ctx);
    expect(r.data.markers).toHaveLength(1);
    expect(r.data.markers[0].submission_id).toBe('a');
  });

  it('filters by province_id (4-char facility prefix)', () => {
    const ctx = makeCtx([
      row({ submission_id: 'a', facility_id: '050101001', submission_lat: 1, submission_lng: 1 }),
      row({ submission_id: 'b', facility_id: '050201002', submission_lat: 2, submission_lng: 2 }),
    ]);
    const r = adminMapReport({ province_id: '0501' }, ctx);
    expect(r.data.markers).toHaveLength(1);
    expect(r.data.markers[0].submission_id).toBe('a');
  });

  it('respects from/to date range', () => {
    const ctx = makeCtx([
      row({ submission_id: 'a', submitted_at_server: '2026-04-29T00:00:00.000Z', submission_lat: 1, submission_lng: 1 }),
      row({ submission_id: 'b', submitted_at_server: '2026-05-02T00:00:00.000Z', submission_lat: 2, submission_lng: 2 }),
    ]);
    const r = adminMapReport({ from: '2026-05-01', to: '2026-05-03' }, ctx);
    expect(r.data.markers).toHaveLength(1);
    expect(r.data.markers[0].submission_id).toBe('b');
  });
});
