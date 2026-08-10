/**
 * Sync-on-submit delivery gate (design F2-Facility-Slug-Links-2026-07-16).
 * The thank-you body reflects the submission row's real Dexie state:
 * pending → "Submitting…" (or "saved, will send" offline), synced → ✓,
 * rejected → show-to-staff. Live via Dexie liveQuery.
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { LocaleProvider } from '@/i18n/locale-context';
import { db, type SubmissionRow } from '@/lib/db';
import { COMPLETED_CSID_KEY } from '@/lib/draft';
import { DeliveryStatus } from './DeliveryStatus';

const CSID = 'csid-delivery-test';

function row(over: Partial<SubmissionRow> = {}): SubmissionRow {
  return {
    client_submission_id: CSID,
    hcw_id: 'sr-1',
    status: 'pending_sync',
    synced_at: null,
    submitted_at: Date.now(),
    spec_version: 'v',
    values: {},
    retry_count: 0,
    next_retry_at: null,
    last_error: null,
    ...over,
  };
}

function setOnline(value: boolean) {
  Object.defineProperty(window.navigator, 'onLine', { value, configurable: true });
  window.dispatchEvent(new Event(value ? 'online' : 'offline'));
}

function setup() {
  return render(
    <LocaleProvider>
      <DeliveryStatus />
    </LocaleProvider>,
  );
}

describe('<DeliveryStatus>', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
    localStorage.clear();
    setOnline(true);
  });

  it('shows "Submitting…" while the row is pending and the device is online', async () => {
    localStorage.setItem(COMPLETED_CSID_KEY, CSID);
    await db.submissions.put(row());
    setup();
    await waitFor(() => expect(screen.getByTestId('delivery-status')).toBeInTheDocument());
    expect(screen.getByTestId('delivery-status').textContent).toMatch(/submitting/i);
  });

  it('flips live to "Submitted ✓" when the sync marks the row synced', async () => {
    localStorage.setItem(COMPLETED_CSID_KEY, CSID);
    await db.submissions.put(row());
    setup();
    await waitFor(() =>
      expect(screen.getByTestId('delivery-status').textContent).toMatch(/submitting/i),
    );
    await db.submissions.update(CSID, { status: 'synced', synced_at: Date.now() });
    await waitFor(() =>
      expect(screen.getByTestId('delivery-status').textContent).toMatch(/submitted ✓/i),
    );
    expect(screen.getByTestId('delivery-status').textContent).toMatch(/close this page/i);
  });

  it('shows the saved-offline line when the device is offline', async () => {
    localStorage.setItem(COMPLETED_CSID_KEY, CSID);
    await db.submissions.put(row({ status: 'retry_scheduled' }));
    setOnline(false);
    setup();
    await waitFor(() =>
      expect(screen.getByTestId('delivery-status').textContent).toMatch(
        /send automatically when you are back online/i,
      ),
    );
    // Reconnecting flips the copy back to the in-flight line.
    setOnline(true);
    await waitFor(() =>
      expect(screen.getByTestId('delivery-status').textContent).toMatch(/submitting/i),
    );
  });

  it('surfaces a rejected row as show-this-to-staff', async () => {
    localStorage.setItem(COMPLETED_CSID_KEY, CSID);
    await db.submissions.put(row({ status: 'rejected' }));
    setup();
    await waitFor(() =>
      expect(screen.getByTestId('delivery-status').textContent).toMatch(/ASPSI staff/i),
    );
  });

  it('falls back to the static thank-you line when no completed csid is recorded', async () => {
    setup();
    await waitFor(() =>
      expect(screen.getByText(/saved on this device and will sync/i)).toBeInTheDocument(),
    );
    expect(screen.queryByTestId('delivery-status')).not.toBeInTheDocument();
  });
});
