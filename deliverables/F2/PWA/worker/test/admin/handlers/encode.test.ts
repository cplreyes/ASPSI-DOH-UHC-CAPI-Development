/**
 * F2 Admin Portal — handleEncodeSubmit tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 4.2)
 */
import { describe, expect, it } from 'vitest';
import {
  handleEncodeSubmit,
  type EncodeAsCallable,
  type EncodeRequestBody,
  type EncodeSuccess,
} from '../../../src/admin/handlers/encode';

function asOk(data: EncodeSuccess): ReturnType<EncodeAsCallable> {
  return Promise.resolve({ ok: true, data });
}

function asErr(code: string, message: string): ReturnType<EncodeAsCallable> {
  return Promise.resolve({ ok: false, error: { code, message } });
}

const ACTOR = { username: 'admin-alice' };

const VALID_BODY: EncodeRequestBody = {
  client_submission_id: 'cli-encoder-1',
  spec_version: '2026-04-17-m1',
  values: { Q3: 'Female', Q4: 25 },
};

describe('handleEncodeSubmit', () => {
  it('returns 400 when hcw_id path param is empty', async () => {
    const r = await handleEncodeSubmit('', VALID_BODY, ACTOR, () => asOk({ submission_id: 's', status: 'accepted', server_timestamp: '' }));
    expect(r.status).toBe(400);
  });

  it('returns 400 when client_submission_id missing', async () => {
    const r = await handleEncodeSubmit(
      'hcw-1',
      { spec_version: '2026-04-17-m1', values: {} } as EncodeRequestBody,
      ACTOR,
      () => asOk({ submission_id: 's', status: 'accepted', server_timestamp: '' }),
    );
    expect(r.status).toBe(400);
  });

  it('returns 400 when values is not a JSON object', async () => {
    const r = await handleEncodeSubmit(
      'hcw-1',
      { ...VALID_BODY, values: 'not-an-object' as unknown as Record<string, unknown> },
      ACTOR,
      () => asOk({ submission_id: 's', status: 'accepted', server_timestamp: '' }),
    );
    expect(r.status).toBe(400);
  });

  it('forwards the enriched payload (hcw_id from path + encoded_by from actor) to AS', async () => {
    const captured: Record<string, unknown>[] = [];
    const asCall: EncodeAsCallable = (payload) => {
      captured.push(payload);
      return asOk({ submission_id: 'srv-42', status: 'accepted', server_timestamp: '2026-05-01T00:00:00Z' });
    };
    const r = await handleEncodeSubmit('hcw-from-path', VALID_BODY, ACTOR, asCall);
    expect(r.status).toBe(200);
    const body = (await r.json()) as EncodeSuccess;
    expect(body.submission_id).toBe('srv-42');
    expect(captured).toHaveLength(1);
    const sent = captured[0]!;
    expect(sent.hcw_id).toBe('hcw-from-path');
    expect(sent.encoded_by).toBe('admin-alice');
    expect(sent.client_submission_id).toBe('cli-encoder-1');
    expect(sent.values).toEqual({ Q3: 'Female', Q4: 25 });
  });

  it('returns 502 E_BACKEND when AS errors', async () => {
    const r = await handleEncodeSubmit(
      'hcw-1',
      VALID_BODY,
      ACTOR,
      () => asErr('E_BACKEND', 'AS quota exceeded'),
    );
    expect(r.status).toBe(502);
    const body = (await r.json()) as { error: { code: string } };
    expect(body.error.code).toBe('E_BACKEND');
  });

  it('passes through duplicate status from AS', async () => {
    const r = await handleEncodeSubmit(
      'hcw-1',
      VALID_BODY,
      ACTOR,
      () => asOk({ submission_id: 'srv-existing', status: 'duplicate', server_timestamp: '2026-05-01T00:00:00Z' }),
    );
    expect(r.status).toBe(200);
    const body = (await r.json()) as EncodeSuccess;
    expect(body.status).toBe('duplicate');
    expect(body.submission_id).toBe('srv-existing');
  });

  it('returns 500 when actor.username is empty', async () => {
    const r = await handleEncodeSubmit(
      'hcw-1',
      VALID_BODY,
      { username: '' },
      () => asOk({ submission_id: 's', status: 'accepted', server_timestamp: '' }),
    );
    expect(r.status).toBe(500);
  });
});
