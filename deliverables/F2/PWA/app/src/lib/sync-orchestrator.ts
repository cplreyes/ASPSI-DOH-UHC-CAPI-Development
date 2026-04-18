import { db, type SubmissionRow } from './db';
import { nextRetryAt } from './backoff';
import type { BatchSubmitItem, BatchSubmitResponse } from './sync-client';

export interface OrchestratorDeps {
  postBatchSubmit: (items: BatchSubmitItem[]) => Promise<BatchSubmitResponse>;
  nowMs: () => number;
  batchSize: number;
  specVersion: string;
  appVersion: string;
  deviceFingerprint: string;
  stuckSyncingThresholdMs: number;
}

export interface SyncRunSummary {
  attempted: number;
  synced: number;
  failed: number;
  retryScheduled: number;
  alreadyRunning: boolean;
}

let isRunning = false;

export async function runSync(deps: OrchestratorDeps): Promise<SyncRunSummary> {
  if (isRunning) {
    return { attempted: 0, synced: 0, failed: 0, retryScheduled: 0, alreadyRunning: true };
  }
  isRunning = true;
  try {
    await reclaimStuck(deps);
    const ready = await findReady(deps);
    if (ready.length === 0) {
      return { attempted: 0, synced: 0, failed: 0, retryScheduled: 0, alreadyRunning: false };
    }
    await markSyncing(ready);
    const items = ready.map((r) => toBatchItem(r, deps));
    const response = await deps.postBatchSubmit(items);
    return await applyResponse(ready, response, deps);
  } finally {
    isRunning = false;
  }
}

async function findReady(deps: OrchestratorDeps): Promise<SubmissionRow[]> {
  const now = deps.nowMs();
  const pending = await db.submissions.where('status').equals('pending_sync').toArray();
  const retry = await db.submissions
    .where('status')
    .equals('retry_scheduled')
    .filter((r) => r.next_retry_at != null && r.next_retry_at <= now)
    .toArray();
  return [...pending, ...retry].slice(0, deps.batchSize);
}

async function reclaimStuck(deps: OrchestratorDeps): Promise<void> {
  const now = deps.nowMs();
  const cutoff = now - deps.stuckSyncingThresholdMs;
  await db.submissions
    .where('status')
    .equals('syncing')
    .filter((r) => r.submitted_at <= cutoff)
    .modify({ status: 'pending_sync' });
}

async function markSyncing(rows: SubmissionRow[]): Promise<void> {
  const ids = rows.map((r) => r.client_submission_id);
  await db.submissions.where('client_submission_id').anyOf(ids).modify({ status: 'syncing' });
}

function toBatchItem(row: SubmissionRow, deps: OrchestratorDeps): BatchSubmitItem {
  return {
    client_submission_id: row.client_submission_id,
    hcw_id: row.hcw_id,
    facility_id: (row.values['facility_id'] as string | undefined) ?? '',
    spec_version: row.spec_version || deps.specVersion,
    app_version: deps.appVersion,
    submitted_at_client: row.submitted_at,
    device_fingerprint: deps.deviceFingerprint,
    values: row.values,
  };
}

async function applyResponse(
  rows: SubmissionRow[],
  response: BatchSubmitResponse,
  deps: OrchestratorDeps,
): Promise<SyncRunSummary> {
  const now = deps.nowMs();
  let synced = 0;
  let failed = 0;
  let retryScheduled = 0;

  if (!response.ok && response.transport) {
    for (const row of rows) {
      const nextCount = row.retry_count + 1;
      await db.submissions.update(row.client_submission_id, {
        status: 'retry_scheduled',
        retry_count: nextCount,
        next_retry_at: nextRetryAt(nextCount - 1, now),
        last_error: response.error,
      });
      retryScheduled += 1;
    }
    return { attempted: rows.length, synced, failed, retryScheduled, alreadyRunning: false };
  }

  if (!response.ok) {
    for (const row of rows) {
      await db.submissions.update(row.client_submission_id, {
        status: 'rejected',
        last_error: response.error,
      });
      failed += 1;
    }
    return { attempted: rows.length, synced, failed, retryScheduled, alreadyRunning: false };
  }

  let anySpecTooOld = false;
  const resultsByCsid = new Map<string, (typeof response.results)[number]>();
  for (const r of response.results) {
    if (r.client_submission_id) resultsByCsid.set(r.client_submission_id, r);
  }

  for (const row of rows) {
    const r = resultsByCsid.get(row.client_submission_id);
    if (!r) {
      const nextCount = row.retry_count + 1;
      await db.submissions.update(row.client_submission_id, {
        status: 'retry_scheduled',
        retry_count: nextCount,
        next_retry_at: nextRetryAt(nextCount - 1, now),
        last_error: { code: 'E_MISSING_RESULT', message: 'No matching per-item result' },
      });
      retryScheduled += 1;
      continue;
    }
    if (r.status === 'accepted' || r.status === 'duplicate') {
      await db.submissions.update(row.client_submission_id, {
        status: 'synced',
        synced_at: now,
        last_error: null,
      });
      synced += 1;
    } else {
      if (r.error?.code === 'E_SPEC_TOO_OLD') anySpecTooOld = true;
      await db.submissions.update(row.client_submission_id, {
        status: 'rejected',
        last_error: r.error ?? { code: 'E_UNKNOWN', message: 'Unknown rejection' },
      });
      failed += 1;
    }
  }

  if (anySpecTooOld) {
    await db.config.put({ key: 'update_available', value: true });
  }

  return { attempted: rows.length, synced, failed, retryScheduled, alreadyRunning: false };
}
