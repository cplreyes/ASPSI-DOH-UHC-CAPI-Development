/**
 * F2 Admin Portal — Data dashboard handler tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.2)
 */
import { describe, expect, it } from 'vitest';
import {
  handleListResponses,
  handleGetResponseById,
  handleBroadcastGet,
  handleBroadcastSet,
  BROADCAST_MAX_LEN,
  type ListResponsesData,
  type ResponseRow,
} from '../../../src/admin/handlers/data';
import type { AppsScriptResponse } from '../../../src/admin/apps-script-client';

function asOk<T>(data: T): Promise<AppsScriptResponse<T>> {
  return Promise.resolve({ ok: true, data });
}
function asErr(code: string, message: string): Promise<AppsScriptResponse<never>> {
  return Promise.resolve({ ok: false, error: { code, message } });
}

const ROW: ResponseRow = {
  submission_id: 'srv-1',
  client_submission_id: 'cli-1',
  submitted_at_server: '2026-05-01T00:00:00.000Z',
  submitted_at_client: '2026-05-01T00:00:00.000Z',
  source: 'PWA',
  spec_version: '2026-04-17-m1',
  app_version: '1.0',
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
};

describe('handleListResponses', () => {
  it('parses query params into filter shape and forwards to AS', async () => {
    let captured: unknown = null;
    const url = new URL('https://x/admin/api/dashboards/data/responses?from=2026-05-01&to=2026-05-02&facility_id=fac-1&status=stored&source_path=self_admin&q=alpha&limit=20&offset=10');
    const r = await handleListResponses(url, async (filters) => {
      captured = filters;
      return asOk<ListResponsesData>({ rows: [ROW], total: 1, has_more: false });
    });
    expect(r.status).toBe(200);
    expect(captured).toEqual({
      from: '2026-05-01',
      to: '2026-05-02',
      facility_id: 'fac-1',
      status: 'stored',
      source_path: 'self_admin',
      q: 'alpha',
      limit: 20,
      offset: 10,
    });
  });

  it('passes empty filters when no query params provided', async () => {
    let captured: unknown = null;
    const url = new URL('https://x/admin/api/dashboards/data/responses');
    await handleListResponses(url, async (filters) => {
      captured = filters;
      return asOk<ListResponsesData>({ rows: [], total: 0, has_more: false });
    });
    expect(captured).toEqual({});
  });

  it('ignores non-numeric limit/offset (defensive)', async () => {
    let captured: { limit?: number; offset?: number } | null = null;
    const url = new URL('https://x/admin/api/dashboards/data/responses?limit=abc&offset=xyz');
    await handleListResponses(url, async (filters) => {
      captured = filters;
      return asOk<ListResponsesData>({ rows: [], total: 0, has_more: false });
    });
    expect(captured!.limit).toBeUndefined();
    expect(captured!.offset).toBeUndefined();
  });

  it('returns 502 E_BACKEND when AS errors', async () => {
    const url = new URL('https://x/admin/api/dashboards/data/responses');
    const r = await handleListResponses(url, () => asErr('E_BACKEND', 'AS down'));
    expect(r.status).toBe(502);
  });

  it('forwards the AS body shape unchanged on success', async () => {
    const url = new URL('https://x/admin/api/dashboards/data/responses');
    const r = await handleListResponses(url, () =>
      asOk<ListResponsesData>({ rows: [ROW, ROW], total: 100, has_more: true }),
    );
    expect(r.status).toBe(200);
    const body = await r.json() as ListResponsesData;
    expect(body.total).toBe(100);
    expect(body.has_more).toBe(true);
    expect(body.rows).toHaveLength(2);
  });
});

describe('handleGetResponseById', () => {
  it('returns the row on success', async () => {
    const r = await handleGetResponseById('srv-1', () => asOk(ROW));
    expect(r.status).toBe(200);
    const body = await r.json() as ResponseRow;
    expect(body.submission_id).toBe('srv-1');
  });

  it('returns 404 when AS reports E_NOT_FOUND', async () => {
    const r = await handleGetResponseById('srv-missing', () => asErr('E_NOT_FOUND', 'no such row'));
    expect(r.status).toBe(404);
    const body = await r.json() as { error: { code: string } };
    expect(body.error.code).toBe('E_NOT_FOUND');
  });

  it('returns 502 for other AS errors', async () => {
    const r = await handleGetResponseById('srv-x', () => asErr('E_BACKEND', 'AS down'));
    expect(r.status).toBe(502);
  });

  it('returns 400 when id is empty', async () => {
    const r = await handleGetResponseById('', () => asOk(ROW));
    expect(r.status).toBe(400);
  });
});

// ----- Broadcast message (M12d) ---------------------------------------------

describe('handleBroadcastGet', () => {
  it('returns the current broadcast_message from config', async () => {
    const r = await handleBroadcastGet(() =>
      asOk({ config: { broadcast_message: 'Sync by 5 PM', kill_switch: 'false' } }),
    );
    expect(r.status).toBe(200);
    const body = await r.json();
    expect(body).toEqual({ broadcast_message: 'Sync by 5 PM' });
  });

  it('defaults to an empty string when the key is absent', async () => {
    const r = await handleBroadcastGet(() => asOk({ config: {} }));
    const body = (await r.json()) as { broadcast_message: string };
    expect(body.broadcast_message).toBe('');
  });

  it('502s when Apps Script is unavailable', async () => {
    const r = await handleBroadcastGet(() => asErr('E_BACKEND', 'down'));
    expect(r.status).toBe(502);
  });
});

describe('handleBroadcastSet', () => {
  function req(body: unknown): Request {
    return new Request('https://x/admin/api/dashboards/apps/broadcast', {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }

  it('sets broadcast_message via the generic config-set and echoes the trimmed value', async () => {
    let captured: { key: string; value: string } | null = null;
    const r = await handleBroadcastSet(req({ broadcast_message: '  Survey closes Friday  ' }), (p) => {
      captured = p;
      return asOk({ key: p.key, value: p.value });
    });
    expect(r.status).toBe(200);
    expect(captured).toEqual({ key: 'broadcast_message', value: 'Survey closes Friday' });
    const body = (await r.json()) as { broadcast_message: string };
    expect(body.broadcast_message).toBe('Survey closes Friday');
  });

  it('allows clearing the banner with an empty string', async () => {
    let captured: { key: string; value: string } | null = null;
    const r = await handleBroadcastSet(req({ broadcast_message: '' }), (p) => {
      captured = p;
      return asOk({ key: p.key, value: p.value });
    });
    expect(r.status).toBe(200);
    expect(captured).toEqual({ key: 'broadcast_message', value: '' });
  });

  it('400s when broadcast_message is not a string', async () => {
    const r = await handleBroadcastSet(req({ broadcast_message: 123 }), () =>
      asOk({ key: '', value: '' }),
    );
    expect(r.status).toBe(400);
  });

  it('400s when broadcast_message exceeds the length cap', async () => {
    const r = await handleBroadcastSet(req({ broadcast_message: 'x'.repeat(BROADCAST_MAX_LEN + 1) }), () =>
      asOk({ key: '', value: '' }),
    );
    expect(r.status).toBe(400);
  });

  it('502s when Apps Script rejects the write', async () => {
    const r = await handleBroadcastSet(req({ broadcast_message: 'hi' }), () => asErr('E_BACKEND', 'down'));
    expect(r.status).toBe(502);
  });
});
