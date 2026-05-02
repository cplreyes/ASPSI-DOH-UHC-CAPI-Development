/**
 * F2 Admin Portal — adminEncodeSubmit tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 4.2)
 *
 * adminEncodeSubmit reuses handleSubmit; tests confirm the three injected
 * fields (source_path, encoded_by, encoded_at) override anything the
 * client might send, while validation + dedup behavior carries over.
 */
import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { handleSubmit } = require('../src/Handlers.js');
const { adminEncodeSubmit } = require('../src/AdminEncoder.js');

function makeCtx(overrides) {
  const appended = [];
  const base = {
    nowMs: () => 1700000000000,
    generateUuid: () => 'gen-uuid-fixed',
    actor_username: 'admin-alice',
    submit: handleSubmit,
    responses: {
      findExisting: () => null,
      appendRow: (row) => { appended.push(row); return row.submission_id; },
    },
    dlq: { appendRow: () => {} },
    config: {
      get: (key) => {
        if (key === 'min_accepted_spec_version') return '2026-04-17-m1';
        return '';
      },
    },
    _appended: appended,
  };
  return Object.assign(base, overrides || {});
}

describe('adminEncodeSubmit', () => {
  it('rejects payload without hcw_id', () => {
    const r = adminEncodeSubmit({ values: {} }, makeCtx());
    expect(r.ok).toBe(false);
    expect(r.error.code).toBe('E_VALIDATION');
    expect(r.error.message).toMatch(/hcw_id/);
  });

  it('rejects when neither ctx.actor_username nor payload.encoded_by is set', () => {
    const r = adminEncodeSubmit(
      { hcw_id: 'hcw-1', client_submission_id: 'cli-1', spec_version: '2026-04-17-m1', values: {} },
      makeCtx({ actor_username: undefined }),
    );
    expect(r.ok).toBe(false);
    expect(r.error.code).toBe('E_VALIDATION');
  });

  it('accepts payload.encoded_by when ctx.actor_username is missing (production path)', () => {
    const r = adminEncodeSubmit(
      {
        hcw_id: 'hcw-1',
        client_submission_id: 'cli-pe-1',
        spec_version: '2026-04-17-m1',
        values: { Q1: 'a' },
        encoded_by: 'admin-bob',
      },
      makeCtx({ actor_username: undefined }),
    );
    expect(r.ok).toBe(true);
  });

  it('appends a row with source_path=paper_encoded and encoder identity', () => {
    const ctx = makeCtx();
    const r = adminEncodeSubmit(
      {
        client_submission_id: 'cli-encoder-1',
        hcw_id: 'hcw-42',
        facility_id: 'fac-1',
        spec_version: '2026-04-17-m1',
        values: { Q3: 'Female', Q4: 25 },
      },
      ctx,
    );
    expect(r.ok).toBe(true);
    expect(r.data.status).toBe('accepted');
    expect(ctx._appended).toHaveLength(1);
    expect(ctx._appended[0].source_path).toBe('paper_encoded');
    expect(ctx._appended[0].encoded_by).toBe('admin-alice');
    expect(ctx._appended[0].encoded_at).toBe(new Date(1700000000000).toISOString());
    expect(ctx._appended[0].hcw_id).toBe('hcw-42');
    // values_json round-trips the survey answers untouched.
    expect(JSON.parse(ctx._appended[0].values_json)).toEqual({ Q3: 'Female', Q4: 25 });
  });

  it('overrides any client-supplied source_path / encoded_by / encoded_at', () => {
    const ctx = makeCtx();
    adminEncodeSubmit(
      {
        client_submission_id: 'cli-2',
        hcw_id: 'hcw-99',
        spec_version: '2026-04-17-m1',
        source_path: 'self_admin',          // client tries to lie
        encoded_by: 'someone-else',          // client tries to lie
        encoded_at: '1999-01-01T00:00:00Z',  // client tries to lie
        values: {},
      },
      ctx,
    );
    expect(ctx._appended[0].source_path).toBe('paper_encoded');
    expect(ctx._appended[0].encoded_by).toBe('admin-alice');
    expect(ctx._appended[0].encoded_at).toBe(new Date(1700000000000).toISOString());
  });

  it('defaults submitted_at_client to server now when omitted (paper has no client clock)', () => {
    const ctx = makeCtx();
    adminEncodeSubmit(
      {
        client_submission_id: 'cli-3',
        hcw_id: 'hcw-100',
        spec_version: '2026-04-17-m1',
        values: {},
      },
      ctx,
    );
    expect(ctx._appended[0].submitted_at_client).toBe(new Date(1700000000000).toISOString());
  });

  it('honors explicit submitted_at_client when the encoder client supplies one', () => {
    const ctx = makeCtx();
    adminEncodeSubmit(
      {
        client_submission_id: 'cli-4',
        hcw_id: 'hcw-101',
        spec_version: '2026-04-17-m1',
        submitted_at_client: 1690000000000,
        values: {},
      },
      ctx,
    );
    expect(ctx._appended[0].submitted_at_client).toBe(new Date(1690000000000).toISOString());
  });

  it('returns duplicate status when the same client_submission_id is replayed', () => {
    const ctx = makeCtx({
      responses: {
        findExisting: () => ({ submission_id: 'srv-existing', row_number: 7 }),
        appendRow: () => 'unused',
      },
    });
    const r = adminEncodeSubmit(
      {
        client_submission_id: 'cli-dup',
        hcw_id: 'hcw-200',
        spec_version: '2026-04-17-m1',
        values: {},
      },
      ctx,
    );
    expect(r.ok).toBe(true);
    expect(r.data.status).toBe('duplicate');
    expect(r.data.submission_id).toBe('srv-existing');
  });
});
