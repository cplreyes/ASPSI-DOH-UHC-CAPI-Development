/**
 * F2 Admin Portal - Data Settings + Quota handler tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 3.4, 3.5, 3.9)
 */
import { describe, expect, it } from 'vitest';
import {
  APPS_SCRIPT_DAILY_CAP,
  handleListSettings,
  handleCreateSetting,
  handleUpdateSetting,
  handleDeleteSetting,
  handleRunNowSetting,
  handleGetQuota,
  type ListSettingsData,
  type SettingRow,
  type QuotaKv,
} from '../../../src/admin/handlers/apps';

const ACTOR = { username: 'admin-alice' };

const SAMPLE_SETTING: SettingRow = {
  setting_id: 's-abc12345',
  instrument: 'F2',
  included_columns: '[]',
  interval_minutes: 60,
  next_run_at: '2026-05-02T13:00:00.000Z',
  output_path_template: 'exports/{{date}}/{{setting_id}}.csv',
  last_run_at: '',
  last_run_status: '',
  last_run_error: '',
  enabled: true,
  created_by: 'admin-alice',
  created_at: '2026-05-01T10:00:00.000Z',
};

function asListOk(data: ListSettingsData) {
  return Promise.resolve({ ok: true as const, data });
}
function asListErr(code: string) {
  return Promise.resolve({ ok: false as const, error: { code, message: code } });
}
function asMutateOk(setting: SettingRow) {
  return Promise.resolve({ ok: true as const, data: { setting } });
}
function asMutateErr(code: string) {
  return Promise.resolve({ ok: false as const, error: { code, message: code } });
}
function asDeleteOk(setting_id: string) {
  return Promise.resolve({ ok: true as const, data: { setting_id } });
}
function asDeleteErr(code: string) {
  return Promise.resolve({ ok: false as const, error: { code, message: code } });
}

// -------------------- handleListSettings --------------------

describe('handleListSettings', () => {
  it('returns settings on AS success', async () => {
    const r = await handleListSettings(() => asListOk({ settings: [SAMPLE_SETTING], total: 1 }));
    expect(r.status).toBe(200);
    const body = (await r.json()) as ListSettingsData;
    expect(body.total).toBe(1);
  });

  it('returns 502 E_BACKEND on AS failure', async () => {
    const r = await handleListSettings(() => asListErr('E_BACKEND'));
    expect(r.status).toBe(502);
  });
});

// -------------------- handleCreateSetting --------------------

describe('handleCreateSetting', () => {
  it('forwards parsed body and stamps created_by from actor', async () => {
    let captured: Record<string, unknown> | undefined;
    const r = await handleCreateSetting(
      { interval_minutes: 60, output_path_template: 'exports/{{date}}.csv', enabled: true },
      ACTOR,
      (payload) => {
        captured = payload;
        return asMutateOk(SAMPLE_SETTING);
      },
    );
    expect(r.status).toBe(201);
    expect(captured?.created_by).toBe('admin-alice');
    expect(captured?.interval_minutes).toBe(60);
    expect(captured?.enabled).toBe(true);
  });

  it('returns 500 when actor.username is empty', async () => {
    const r = await handleCreateSetting({ interval_minutes: 60 }, { username: '' }, () =>
      asMutateOk(SAMPLE_SETTING),
    );
    expect(r.status).toBe(500);
  });

  it('forwards AS validation error as 400', async () => {
    const r = await handleCreateSetting({ interval_minutes: 1 }, ACTOR, () =>
      asMutateErr('E_VALIDATION'),
    );
    expect(r.status).toBe(400);
  });
});

// -------------------- handleUpdateSetting --------------------

describe('handleUpdateSetting', () => {
  it('rejects invalid setting_id with 400', async () => {
    const r = await handleUpdateSetting('!invalid', {}, () => asMutateOk(SAMPLE_SETTING));
    expect(r.status).toBe(400);
  });

  it('forwards setting_id and parsed mutation', async () => {
    let captured: Record<string, unknown> | undefined;
    const r = await handleUpdateSetting(
      's-abc12345',
      { enabled: false, interval_minutes: 30 },
      (payload) => {
        captured = payload;
        return asMutateOk({ ...SAMPLE_SETTING, enabled: false, interval_minutes: 30 });
      },
    );
    expect(r.status).toBe(200);
    expect(captured?.setting_id).toBe('s-abc12345');
    expect(captured?.enabled).toBe(false);
    expect(captured?.interval_minutes).toBe(30);
  });

  it('returns 404 when AS reports E_NOT_FOUND', async () => {
    const r = await handleUpdateSetting('s-abc12345', {}, () => asMutateErr('E_NOT_FOUND'));
    expect(r.status).toBe(404);
  });
});

// -------------------- handleDeleteSetting --------------------

describe('handleDeleteSetting', () => {
  it('returns 204 on success', async () => {
    const r = await handleDeleteSetting('s-abc12345', () => asDeleteOk('s-abc12345'));
    expect(r.status).toBe(204);
  });

  it('rejects invalid setting_id with 400', async () => {
    const r = await handleDeleteSetting('!invalid', () => asDeleteOk('!invalid'));
    expect(r.status).toBe(400);
  });

  it('forwards AS error as 404 E_NOT_FOUND', async () => {
    const r = await handleDeleteSetting('s-abc12345', () => asDeleteErr('E_NOT_FOUND'));
    expect(r.status).toBe(404);
  });
});

// -------------------- handleRunNowSetting --------------------

describe('handleRunNowSetting', () => {
  it('returns 200 with the updated setting on success', async () => {
    const r = await handleRunNowSetting('s-abc12345', () => asMutateOk(SAMPLE_SETTING));
    expect(r.status).toBe(200);
  });

  it('returns 409 when AS reports E_CONFLICT (already running)', async () => {
    const r = await handleRunNowSetting('s-abc12345', () => asMutateErr('E_CONFLICT'));
    expect(r.status).toBe(409);
  });

  it('rejects invalid setting_id with 400 (no AS round-trip)', async () => {
    let called = false;
    const r = await handleRunNowSetting('!bad', () => {
      called = true;
      return asMutateOk(SAMPLE_SETTING);
    });
    expect(r.status).toBe(400);
    expect(called).toBe(false);
  });
});

// -------------------- handleGetQuota --------------------

describe('handleGetQuota', () => {
  function makeKv(map: Record<string, string>): QuotaKv {
    return {
      get: async (key) => (key in map ? map[key]! : null),
    };
  }

  it('returns 0 when KV is empty', async () => {
    const r = await handleGetQuota(makeKv({}), new Date(Date.UTC(2026, 4, 2, 12)));
    const body = (await r.json()) as {
      date_utc: string;
      count: number;
      cap: number;
      percent: number;
    };
    expect(body.date_utc).toBe('2026-05-02');
    expect(body.count).toBe(0);
    expect(body.cap).toBe(APPS_SCRIPT_DAILY_CAP);
    expect(body.percent).toBe(0);
  });

  it('returns the parsed count from KV', async () => {
    const r = await handleGetQuota(
      makeKv({ 'as_quota:2026-05-02': '5000' }),
      new Date(Date.UTC(2026, 4, 2, 12)),
    );
    const body = (await r.json()) as { count: number; percent: number };
    expect(body.count).toBe(5000);
    expect(body.percent).toBe(25);
  });

  it('caps percent at 100 even if count > cap', async () => {
    const r = await handleGetQuota(
      makeKv({ 'as_quota:2026-05-02': '50000' }),
      new Date(Date.UTC(2026, 4, 2, 12)),
    );
    const body = (await r.json()) as { count: number; percent: number };
    expect(body.count).toBe(50000);
    expect(body.percent).toBe(100);
  });

  it('treats non-numeric KV value as 0', async () => {
    const r = await handleGetQuota(
      makeKv({ 'as_quota:2026-05-02': 'NaN' }),
      new Date(Date.UTC(2026, 4, 2, 12)),
    );
    const body = (await r.json()) as { count: number };
    expect(body.count).toBe(0);
  });

  it('uses UTC date key', async () => {
    // 2026-05-03 03:00 UTC = 2026-05-02 23:00 in UTC-4. Verify we pick UTC.
    const r = await handleGetQuota(
      makeKv({ 'as_quota:2026-05-03': '7' }),
      new Date(Date.UTC(2026, 4, 3, 3, 0)),
    );
    const body = (await r.json()) as { date_utc: string; count: number };
    expect(body.date_utc).toBe('2026-05-03');
    expect(body.count).toBe(7);
  });
});
