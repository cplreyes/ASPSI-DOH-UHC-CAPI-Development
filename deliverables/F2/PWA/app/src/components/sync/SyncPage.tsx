import { useEffect, useState } from 'react';
import { liveQuery } from 'dexie';
import { db, type SubmissionRow } from '@/lib/db';
import type { SyncRunSummary } from '@/lib/sync-orchestrator';
import { SyncButton } from './SyncButton';

interface SyncPageProps {
  runSync: () => Promise<SyncRunSummary>;
}

const STATUS_ORDER: SubmissionRow['status'][] = [
  'pending_sync',
  'syncing',
  'retry_scheduled',
  'rejected',
  'synced',
];

const STATUS_LABEL: Record<SubmissionRow['status'], string> = {
  pending_sync: 'Pending',
  syncing: 'Syncing',
  retry_scheduled: 'Retry scheduled',
  rejected: 'Rejected',
  synced: 'Synced',
};

export function SyncPage({ runSync }: SyncPageProps) {
  const [rows, setRows] = useState<SubmissionRow[] | null>(null);

  useEffect(() => {
    const sub = liveQuery(async () => {
      const all = await db.submissions.toArray();
      return all.sort((a, b) => b.submitted_at - a.submitted_at);
    }).subscribe({
      next: (data) => setRows(data),
      error: () => setRows([]),
    });
    return () => sub.unsubscribe();
  }, []);

  if (rows === null) {
    return <p className="p-6 text-sm text-muted-foreground">Loading…</p>;
  }

  if (rows.length === 0) {
    return (
      <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
        <h2 className="text-2xl font-semibold">Sync</h2>
        <p className="text-sm text-muted-foreground">No submissions yet.</p>
        <SyncButton runSync={runSync} />
      </section>
    );
  }

  const grouped = new Map<SubmissionRow['status'], SubmissionRow[]>();
  for (const s of STATUS_ORDER) grouped.set(s, []);
  for (const r of rows) grouped.get(r.status)?.push(r);

  return (
    <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
      <h2 className="text-2xl font-semibold">Sync</h2>
      <SyncButton runSync={runSync} />
      {STATUS_ORDER.map((s) => {
        const group = grouped.get(s) ?? [];
        if (group.length === 0) return null;
        return (
          <div key={s} className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-muted-foreground">
              {STATUS_LABEL[s]} ({group.length})
            </h3>
            <ul className="flex flex-col gap-1.5">
              {group.map((row) => (
                <li key={row.client_submission_id} className="rounded border p-2 text-xs">
                  <div className="font-mono">{row.client_submission_id}</div>
                  <div className="text-muted-foreground">
                    submitted {new Date(row.submitted_at).toLocaleString()}
                  </div>
                  {row.last_error ? (
                    <div className="text-destructive">
                      {row.last_error.code}: {row.last_error.message}
                    </div>
                  ) : null}
                  {row.next_retry_at ? (
                    <div className="text-muted-foreground">
                      retry at {new Date(row.next_retry_at).toLocaleString()}
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </section>
  );
}
