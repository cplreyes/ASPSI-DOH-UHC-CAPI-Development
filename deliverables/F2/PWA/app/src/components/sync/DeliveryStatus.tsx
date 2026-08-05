import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { liveQuery } from 'dexie';
import { db } from '@/lib/db';
import { COMPLETED_CSID_KEY } from '@/lib/draft';

/**
 * Delivery gate for the thank-you screen (design F2-Facility-Slug-Links-2026-07-16,
 * "Sync-on-submit"). The self-register device is one-and-done — nobody runs a
 * manual sync — so make delivery VISIBLE: "Submitting…" until the server ack
 * lands in Dexie (the immediate post-submit sync flips the row to 'synced'),
 * then "Submitted ✓ — you can close this". Offline, the queued row + the
 * on-reconnect trigger deliver it, and the copy says so. The response is
 * durably queued the instant Submit succeeds, so no state here risks data —
 * this only makes "did it actually send?" visible to a user who won't return.
 */
export function DeliveryStatus() {
  const { t } = useTranslation();
  const [rowStatus, setRowStatus] = useState<string | null>(null);
  const [online, setOnline] = useState(
    typeof navigator === 'undefined' ? true : navigator.onLine,
  );
  const csid =
    typeof localStorage !== 'undefined' ? localStorage.getItem(COMPLETED_CSID_KEY) : null;

  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => {
      window.removeEventListener('online', on);
      window.removeEventListener('offline', off);
    };
  }, []);

  useEffect(() => {
    if (!csid) return;
    const sub = liveQuery(() => db.submissions.get(csid)).subscribe({
      next: (row) => setRowStatus(row ? row.status : 'missing'),
      error: () => setRowStatus(null),
    });
    return () => sub.unsubscribe();
  }, [csid]);

  // No csid (pre-gate sessions), row gone (pruned), or Dexie unavailable —
  // fall back to the original static line rather than guess.
  if (!csid || rowStatus === null || rowStatus === 'missing') {
    return <p className="text-sm text-muted-foreground">{t('chrome.thankYouBody')}</p>;
  }
  if (rowStatus === 'synced') {
    return (
      <p data-testid="delivery-status" className="text-sm font-medium text-signal">
        {t('chrome.deliveredBody')}
      </p>
    );
  }
  if (rowStatus === 'rejected') {
    return (
      <p data-testid="delivery-status" className="text-sm text-destructive">
        {t('chrome.deliveryFailed')}
      </p>
    );
  }
  // pending_sync | syncing | retry_scheduled — delivery in flight or queued.
  return (
    <p data-testid="delivery-status" className="text-sm text-muted-foreground">
      {online ? t('chrome.delivering') : t('chrome.deliveryOffline')}
    </p>
  );
}
