import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { liveQuery } from 'dexie';
import { db, type SubmissionRow } from '@/lib/db';
import type { SyncRunSummary } from '@/lib/sync-orchestrator';
import { SyncButton } from './SyncButton';
import { ChangeEnrollmentButton } from '@/components/enrollment/ChangeEnrollmentButton';

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

function statusLabel(
  t: ReturnType<typeof useTranslation>['t'],
  status: SubmissionRow['status'],
): string {
  switch (status) {
    case 'pending_sync':
      return t('sync.statusPending');
    case 'syncing':
      return t('sync.statusSyncing');
    case 'retry_scheduled':
      return t('sync.statusRetryScheduled');
    case 'rejected':
      return t('sync.statusRejected');
    case 'synced':
      return t('sync.statusSynced');
  }
}

export function SyncPage({ runSync }: SyncPageProps) {
  const { t } = useTranslation();
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
    return <p className="p-6 text-sm text-muted-foreground">{t('chrome.loading')}</p>;
  }

  if (rows.length === 0) {
    return (
      <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
        <h2 className="font-serif text-2xl font-medium tracking-tight">{t('sync.heading')}</h2>
        <p className="text-sm text-muted-foreground">{t('sync.none')}</p>
        <SyncButton runSync={runSync} />
        <ChangeEnrollmentButton />
      </section>
    );
  }

  const grouped = new Map<SubmissionRow['status'], SubmissionRow[]>();
  for (const s of STATUS_ORDER) grouped.set(s, []);
  for (const r of rows) grouped.get(r.status)?.push(r);

  return (
    <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
      <h2 className="font-serif text-2xl font-medium tracking-tight">{t('sync.heading')}</h2>
      <SyncButton runSync={runSync} />
      <ChangeEnrollmentButton />
      {STATUS_ORDER.map((s) => {
        const group = grouped.get(s) ?? [];
        if (group.length === 0) return null;
        return (
          <div key={s} className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-muted-foreground">
              {statusLabel(t, s)} ({group.length})
            </h3>
            <ul className="flex flex-col gap-1.5">
              {group.map((row) => (
                <li key={row.client_submission_id} className="rounded border p-2 text-xs">
                  <div className="font-mono">{row.client_submission_id}</div>
                  <div className="text-muted-foreground">
                    {t('sync.submittedAt', { at: new Date(row.submitted_at).toLocaleString() })}
                  </div>
                  {row.last_error ? (
                    <div className="text-destructive">
                      {row.last_error.code}: {row.last_error.message}
                    </div>
                  ) : null}
                  {row.next_retry_at ? (
                    <div className="text-muted-foreground">
                      {t('sync.retryAt', { at: new Date(row.next_retry_at).toLocaleString() })}
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
