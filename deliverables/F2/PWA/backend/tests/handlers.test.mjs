import { describe, it, expect, vi } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { handleSubmit } = require('../src/Handlers.js');

function makeCtx(overrides) {
  const appended = [];
  const base = {
    nowMs: () => 1700000000000,
    generateUuid: () => 'gen-uuid-fixed',
    responses: {
      findExisting: () => null,
      appendRow: (row) => { appended.push(row); return row.submission_id; },
    },
    dlq: { appendRow: (row) => {} },
    config: {
      get: (key) => {
        if (key === 'kill_switch') return 'false';
        if (key === 'min_accepted_spec_version') return '2026-04-17-m1';
        return '';
      },
    },
    _appended: appended,
  };
  return Object.assign(base, overrides || {});
}

describe('handleSubmit', () => {
  it('appends a row and returns a new submission_id for a fresh client_submission_id', () => {
    const ctx = makeCtx();
    const result = handleSubmit(
      {
        client_submission_id: 'cli-1',
        hcw_id: 'hcw-1',
        facility_id: 'fac-1',
        spec_version: '2026-04-17-m1',
        app_version: '0.1.0',
        submitted_at_client: 1700000000000,
        device_fingerprint: 'android-chrome-138',
        values: { Q2: 'Regular', Q3: 'Female' },
      },
      ctx,
    );
    expect(result.ok).toBe(true);
    expect(result.data.status).toBe('accepted');
    expect(result.data.submission_id).toBe('srv-gen-uuid-fixed');
    expect(ctx._appended).toHaveLength(1);
    expect(ctx._appended[0].client_submission_id).toBe('cli-1');
    expect(ctx._appended[0].submission_id).toBe('srv-gen-uuid-fixed');
    expect(ctx._appended[0].source).toBe('PWA');
    expect(ctx._appended[0].status).toBe('stored');
    expect(JSON.parse(ctx._appended[0].values_json)).toEqual({ Q2: 'Regular', Q3: 'Female' });
  });

  it('defaults source_path to self_admin and writes empty lat/lng when values omit them', () => {
    const ctx = makeCtx();
    handleSubmit(
      {
        client_submission_id: 'cli-no-gps',
        spec_version: '2026-04-17-m1',
        values: { Q3: 'Male' },
      },
      ctx,
    );
    expect(ctx._appended[0].source_path).toBe('self_admin');
    expect(ctx._appended[0].submission_lat).toBe('');
    expect(ctx._appended[0].submission_lng).toBe('');
    expect(ctx._appended[0].encoded_by).toBe('');
    expect(ctx._appended[0].encoded_at).toBe('');
  });

  it('reads submission_lat/lng from values dict when PWA injects them at submit time', () => {
    const ctx = makeCtx();
    handleSubmit(
      {
        client_submission_id: 'cli-gps',
        spec_version: '2026-04-17-m1',
        values: { Q3: 'Female', submission_lat: 14.5995, submission_lng: 120.9842 },
      },
      ctx,
    );
    expect(ctx._appended[0].submission_lat).toBe(14.5995);
    expect(ctx._appended[0].submission_lng).toBe(120.9842);
    expect(ctx._appended[0].source_path).toBe('self_admin');
  });

  it('drops non-numeric submission_lat (e.g. null from declined geolocation) to empty', () => {
    const ctx = makeCtx();
    handleSubmit(
      {
        client_submission_id: 'cli-null-gps',
        spec_version: '2026-04-17-m1',
        values: { Q3: 'Male', submission_lat: null, submission_lng: null },
      },
      ctx,
    );
    expect(ctx._appended[0].submission_lat).toBe('');
    expect(ctx._appended[0].submission_lng).toBe('');
  });

  it('honors top-level encoder fields over values (paper-encoded write path)', () => {
    const ctx = makeCtx();
    handleSubmit(
      {
        client_submission_id: 'cli-encoded',
        spec_version: '2026-04-17-m1',
        source_path: 'paper_encoded',
        encoded_by: 'admin-alice',
        encoded_at: 1700000005000,
        submission_lat: 12.345,
        submission_lng: 67.89,
        values: { Q3: 'Male', submission_lat: 99.99 },
      },
      ctx,
    );
    expect(ctx._appended[0].source_path).toBe('paper_encoded');
    expect(ctx._appended[0].encoded_by).toBe('admin-alice');
    expect(ctx._appended[0].encoded_at).toBe(new Date(1700000005000).toISOString());
    // Top-level lat wins over the (stale) value-dict lat.
    expect(ctx._appended[0].submission_lat).toBe(12.345);
    expect(ctx._appended[0].submission_lng).toBe(67.89);
  });

  it('returns duplicate status for a repeated client_submission_id', () => {
    const ctx = makeCtx({
      responses: {
        findExisting: () => ({ submission_id: 'srv-existing', row_number: 5 }),
        appendRow: vi.fn(() => 'unused'),
      },
    });
    const result = handleSubmit(
      {
        client_submission_id: 'cli-dup',
        hcw_id: 'hcw-1',
        facility_id: 'fac-1',
        spec_version: '2026-04-17-m1',
        submitted_at_client: 1700000000000,
        values: {},
      },
      ctx,
    );
    expect(result.ok).toBe(true);
    expect(result.data.status).toBe('duplicate');
    expect(result.data.submission_id).toBe('srv-existing');
    expect(ctx.responses.appendRow).not.toHaveBeenCalled();
  });

  it('rejects payload missing client_submission_id with E_PAYLOAD_INVALID', () => {
    const result = handleSubmit({ hcw_id: 'hcw-1', values: {} }, makeCtx());
    expect(result).toEqual({
      ok: false,
      error: { code: 'E_PAYLOAD_INVALID', message: 'Missing client_submission_id' },
    });
  });

  it('rejects payload missing values with E_PAYLOAD_INVALID', () => {
    const result = handleSubmit(
      { client_submission_id: 'cli-1', hcw_id: 'hcw-1', spec_version: '2026-04-17-m1' },
      makeCtx(),
    );
    expect(result.error.code).toBe('E_PAYLOAD_INVALID');
  });

  it('rejects payload missing spec_version with E_PAYLOAD_INVALID', () => {
    const result = handleSubmit(
      { client_submission_id: 'cli-1', hcw_id: 'hcw-1', values: {} },
      makeCtx(),
    );
    expect(result.error.code).toBe('E_PAYLOAD_INVALID');
  });

  it('rejects spec_version older than min_accepted_spec_version with E_SPEC_TOO_OLD', () => {
    const result = handleSubmit(
      {
        client_submission_id: 'cli-old',
        hcw_id: 'hcw-1',
        facility_id: 'fac-1',
        spec_version: '2026-01-01-m1',
        submitted_at_client: 1700000000000,
        values: {},
      },
      makeCtx(),
    );
    expect(result.error.code).toBe('E_SPEC_TOO_OLD');
  });

  it('writes to DLQ and returns E_VALIDATION when values is not an object', () => {
    const dlq = [];
    const ctx = makeCtx({ dlq: { appendRow: (row) => { dlq.push(row); } } });
    const result = handleSubmit(
      {
        client_submission_id: 'cli-bad',
        hcw_id: 'hcw-1',
        facility_id: 'fac-1',
        spec_version: '2026-04-17-m1',
        submitted_at_client: 1700000000000,
        values: 'not-an-object',
      },
      ctx,
    );
    expect(result.error.code).toBe('E_VALIDATION');
    expect(dlq).toHaveLength(1);
    expect(dlq[0].reason).toContain('values must be an object');
  });
});

const { handleBatchSubmit } = require('../src/Handlers.js');

describe('handleBatchSubmit', () => {
  it('processes an array of responses and returns per-item results', () => {
    let nextId = 0;
    const ctx = {
      nowMs: () => 1700000000000,
      generateUuid: () => 'u' + (++nextId),
      responses: {
        findExisting: () => null,
        appendRow: (row) => row.submission_id,
      },
      dlq: { appendRow: () => {} },
      config: { get: (k) => (k === 'min_accepted_spec_version' ? '2026-04-17-m1' : '') },
    };
    const payload = {
      responses: [
        { client_submission_id: 'c1', hcw_id: 'h1', spec_version: '2026-04-17-m1', values: {} },
        { client_submission_id: 'c2', hcw_id: 'h1', spec_version: '2026-04-17-m1', values: {} },
      ],
    };
    const result = handleBatchSubmit(payload, ctx);
    expect(result.ok).toBe(true);
    expect(result.data.results).toHaveLength(2);
    expect(result.data.results[0].client_submission_id).toBe('c1');
    expect(result.data.results[0].status).toBe('accepted');
    expect(result.data.results[1].status).toBe('accepted');
  });

  it('rejects non-array payload with E_PAYLOAD_INVALID', () => {
    const result = handleBatchSubmit({ responses: 'not-an-array' }, {});
    expect(result.error.code).toBe('E_PAYLOAD_INVALID');
  });

  it('rejects batches over 50 items with E_BATCH_TOO_LARGE', () => {
    const responses = Array.from({ length: 51 }, (_, i) => ({
      client_submission_id: 'c' + i,
      spec_version: '2026-04-17-m1',
      values: {},
    }));
    const result = handleBatchSubmit({ responses }, {});
    expect(result.error.code).toBe('E_BATCH_TOO_LARGE');
  });

  it('returns per-item errors without aborting the batch', () => {
    let nextId = 0;
    const ctx = {
      nowMs: () => 1700000000000,
      generateUuid: () => 'u' + (++nextId),
      responses: {
        findExisting: () => null,
        appendRow: (row) => row.submission_id,
      },
      dlq: { appendRow: () => {} },
      config: { get: () => '' },
    };
    const result = handleBatchSubmit({
      responses: [
        { client_submission_id: 'c1', spec_version: '2026-04-17-m1', values: {} },
        { hcw_id: 'no-client-id', spec_version: '2026-04-17-m1', values: {} },
        { client_submission_id: 'c3', spec_version: '2026-04-17-m1', values: {} },
      ],
    }, ctx);
    expect(result.data.results).toHaveLength(3);
    expect(result.data.results[0].status).toBe('accepted');
    expect(result.data.results[1].status).toBe('rejected');
    expect(result.data.results[1].error.code).toBe('E_PAYLOAD_INVALID');
    expect(result.data.results[2].status).toBe('accepted');
  });
});

const { handleFacilities, handleConfig, handleSpecHash, handleAudit } = require('../src/Handlers.js');

describe('handleFacilities', () => {
  it('returns the facility master list as an array of objects', () => {
    const ctx = {
      facilities: {
        readAll: () => [
          { facility_id: 'F001', facility_name: 'RHU Laguna', region: 'IV-A', province: 'Laguna', city_mun: 'Los Baños', barangay: 'Batong Malake', facility_type: 'RHU' },
          { facility_id: 'F002', facility_name: 'Provincial Hospital', region: 'IV-A', province: 'Laguna', city_mun: 'Sta Cruz', barangay: 'Poblacion', facility_type: 'Hospital' },
        ],
      },
    };
    const r = handleFacilities(ctx);
    expect(r.ok).toBe(true);
    expect(r.data.facilities).toHaveLength(2);
    expect(r.data.facilities[0].facility_id).toBe('F001');
  });

  it('returns empty array when sheet is empty', () => {
    const r = handleFacilities({ facilities: { readAll: () => [] } });
    expect(r.data.facilities).toEqual([]);
  });
});

describe('handleConfig', () => {
  it('returns all config key/value pairs as an object, coercing bool/number strings', () => {
    const ctx = {
      config: {
        readAll: () => [
          ['current_spec_version', '2026-04-17-m1'],
          ['min_accepted_spec_version', '2026-04-17-m1'],
          ['kill_switch', 'false'],
          ['broadcast_message', 'Hello'],
          ['spec_hash', 'abc123'],
        ],
      },
    };
    const r = handleConfig(ctx);
    expect(r.ok).toBe(true);
    expect(r.data).toEqual({
      current_spec_version: '2026-04-17-m1',
      min_accepted_spec_version: '2026-04-17-m1',
      kill_switch: false,
      broadcast_message: 'Hello',
      spec_hash: 'abc123',
    });
  });

  it('coerces kill_switch=true correctly', () => {
    const r = handleConfig({
      config: { readAll: () => [['kill_switch', 'true']] },
    });
    expect(r.data.kill_switch).toBe(true);
  });
});

describe('handleSpecHash', () => {
  it('returns spec_hash and current_spec_version from config', () => {
    const ctx = {
      config: {
        get: (k) => {
          if (k === 'spec_hash') return 'abc123';
          if (k === 'current_spec_version') return '2026-04-17-m1';
          return '';
        },
      },
    };
    const r = handleSpecHash(ctx);
    expect(r).toEqual({
      ok: true,
      data: { spec_hash: 'abc123', current_spec_version: '2026-04-17-m1' },
    });
  });
});

describe('handleAudit', () => {
  it('appends an audit row and returns the audit_id', () => {
    const appended = [];
    const ctx = {
      nowMs: () => 1700000000000,
      generateUuid: () => 'aud-fixed',
      audit: { appendRow: (row) => { appended.push(row); return row.audit_id; } },
    };
    const r = handleAudit(
      {
        event_type: 'app_install',
        occurred_at_client: 1699999999000,
        hcw_id: 'hcw-1',
        facility_id: 'fac-1',
        app_version: '0.1.0',
        payload: { source: 'beforeinstallprompt' },
      },
      ctx,
    );
    expect(r.ok).toBe(true);
    expect(r.data.audit_id).toBe('aud-fixed');
    expect(appended).toHaveLength(1);
    expect(appended[0].event_type).toBe('app_install');
    expect(JSON.parse(appended[0].payload_json)).toEqual({ source: 'beforeinstallprompt' });
  });

  it('rejects payload missing event_type with E_PAYLOAD_INVALID', () => {
    const r = handleAudit({}, {
      nowMs: () => 1,
      generateUuid: () => 'x',
      audit: { appendRow: () => {} },
    });
    expect(r.error.code).toBe('E_PAYLOAD_INVALID');
  });
});
