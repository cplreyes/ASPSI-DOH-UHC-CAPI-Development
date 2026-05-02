/**
 * F2 Admin Portal - Scheduled break-out dispatcher.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.5)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (sec 7.6)
 *
 * Wrangler cron fires every 5 minutes. The handler asks AS for due
 * F2_DataSettings rows, writes each returned CSV to R2 at the
 * AS-rendered output_path, then calls AS back to mark the setting
 * complete which advances next_run_at by interval_minutes.
 *
 * Design choices:
 * - AS owns scheduling: the worker doesn't track any state across
 *   invocations. If a tick is missed (Cloudflare deploys, etc.),
 *   the next tick simply finds an even larger backlog of due rows.
 * - R2 writes use the AS-rendered output_path verbatim. AS rendered
 *   it deterministically (UTC date + setting_id) so reprocessing
 *   the same row idempotently overwrites the same key.
 * - Per-setting failures are isolated: one failing CSV doesn't stop
 *   the others. The mark-complete call records the failure on the
 *   row, advances next_run_at anyway so a poison row doesn't burn
 *   AS quota in a tight loop, and the admin sees last_run_status =
 *   'failed' in the Settings UI.
 */
import type { Env } from '../types';
import { callAppsScript } from './apps-script-client';

interface RanItem {
  setting_id: string;
  output_path: string;
  csv: string;
}

interface RunDueData {
  ran: RanItem[];
  errors: Array<{ setting_id: string; message: string }>;
}

interface CronR2 {
  put(
    key: string,
    value: ReadableStream | ArrayBuffer | string,
    options?: { httpMetadata?: { contentType?: string } },
  ): Promise<unknown>;
}

export interface RunDueDeps {
  appsScriptUrl: string;
  appsScriptHmac: string;
  r2: CronR2;
}

/**
 * Default-export-friendly entry. Exported for testability with a mocked
 * fetch + R2; the production scheduled() in index.ts builds the deps
 * from env.
 */
export async function runDueSettings(deps: RunDueDeps): Promise<void> {
  const requestId = `cron-${crypto.randomUUID()}`;
  const due = await callAppsScript<RunDueData>(
    deps.appsScriptUrl,
    deps.appsScriptHmac,
    'admin_settings_run_due',
    {},
    requestId,
  );
  if (!due.ok || !due.data) {
    console.warn('[cron] admin_settings_run_due failed', due.error);
    return;
  }
  if (due.data.ran.length === 0 && due.data.errors.length === 0) return;

  for (const item of due.data.ran) {
    let status: 'success' | 'failed' = 'success';
    let errorMessage = '';
    try {
      await deps.r2.put(item.output_path, item.csv, {
        httpMetadata: { contentType: 'text/csv' },
      });
    } catch (err) {
      status = 'failed';
      errorMessage = err instanceof Error ? err.message : String(err);
      console.error('[cron] R2 put failed', item.setting_id, errorMessage);
    }
    const ack = await callAppsScript(
      deps.appsScriptUrl,
      deps.appsScriptHmac,
      'admin_settings_mark_complete',
      { setting_id: item.setting_id, status, error_message: errorMessage },
      requestId,
    );
    if (!ack.ok) {
      console.warn('[cron] mark_complete failed', item.setting_id, ack.error);
    }
  }

  // Settings whose CSV building failed AS-side still need to be marked
  // complete or they'll be picked up forever (running flag stays set).
  for (const err of due.data.errors) {
    const ack = await callAppsScript(
      deps.appsScriptUrl,
      deps.appsScriptHmac,
      'admin_settings_mark_complete',
      { setting_id: err.setting_id, status: 'failed', error_message: err.message },
      requestId,
    );
    if (!ack.ok) {
      console.warn('[cron] mark_complete after AS error failed', err.setting_id, ack.error);
    }
  }
}

export function depsFromEnv(env: Env): RunDueDeps {
  return {
    appsScriptUrl: env.APPS_SCRIPT_URL,
    appsScriptHmac: env.APPS_SCRIPT_HMAC,
    r2: env.F2_ADMIN_R2,
  };
}
