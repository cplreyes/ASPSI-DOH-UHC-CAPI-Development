import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SyncButton } from './SyncButton';
import type { SyncRunSummary } from '@/lib/sync-orchestrator';

describe('SyncButton', () => {
  it('calls runSync when clicked and shows "Syncing…" while in flight', async () => {
    let resolve: (v: SyncRunSummary) => void = () => {};
    const promise = new Promise<SyncRunSummary>((r) => (resolve = r));
    const runSync = vi.fn(() => promise);
    render(<SyncButton runSync={runSync} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /sync now/i }));
    expect(runSync).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button')).toHaveTextContent(/syncing/i);
    resolve({ attempted: 1, synced: 1, failed: 0, retryScheduled: 0, alreadyRunning: false });
    await promise;
  });

  it('shows "Synced N" after a successful run', async () => {
    const runSync = vi.fn().mockResolvedValue({ attempted: 2, synced: 2, failed: 0, retryScheduled: 0, alreadyRunning: false });
    render(<SyncButton runSync={runSync} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button'));
    expect(await screen.findByText(/synced 2/i)).toBeInTheDocument();
  });

  it('shows "Retry in X" when some rows go to retry_scheduled', async () => {
    const runSync = vi.fn().mockResolvedValue({ attempted: 3, synced: 1, failed: 0, retryScheduled: 2, alreadyRunning: false });
    render(<SyncButton runSync={runSync} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button'));
    expect(await screen.findByText(/retrying 2/i)).toBeInTheDocument();
  });

  it('shows "N rejected" when some rows were terminally rejected', async () => {
    const runSync = vi.fn().mockResolvedValue({ attempted: 2, synced: 1, failed: 1, retryScheduled: 0, alreadyRunning: false });
    render(<SyncButton runSync={runSync} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button'));
    expect(await screen.findByText(/1 rejected/i)).toBeInTheDocument();
  });
});
