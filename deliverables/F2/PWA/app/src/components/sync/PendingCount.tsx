import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { liveQuery } from 'dexie';
import { db } from '@/lib/db';

export function PendingCount() {
  const { t } = useTranslation();
  const [count, setCount] = useState<number>(0);

  useEffect(() => {
    const subscription = liveQuery(async () => {
      const pending = await db.submissions.where('status').equals('pending_sync').count();
      const retry = await db.submissions.where('status').equals('retry_scheduled').count();
      return pending + retry;
    }).subscribe({
      next: (n) => setCount(n),
      error: () => setCount(0),
    });
    return () => subscription.unsubscribe();
  }, []);

  if (count === 0) return null;
  return (
    <span
      data-testid="pending-count"
      className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800"
    >
      {t('sync.pendingBadge', { count })}
    </span>
  );
}
