import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { db, type SubmissionRow } from '@/lib/db';
import { SyncPage } from './SyncPage';

function mkSub(overrides: Partial<SubmissionRow>): SubmissionRow {
  return {
    client_submission_id: 'id',
    hcw_id: 'h1',
    status: 'pending_sync',
    synced_at: null,
    submitted_at: Date.UTC(2026, 3, 18, 1, 0, 0),
    spec_version: 'v',
    values: {},
    retry_count: 0,
    next_retry_at: null,
    last_error: null,
    ...overrides,
  };
}

describe('SyncPage', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('renders an empty-state message when no submissions exist', async () => {
    render(<SyncPage runSync={vi.fn().mockResolvedValue({ attempted: 0, synced: 0, failed: 0, retryScheduled: 0, alreadyRunning: false })} />);
    await waitFor(() => {
      expect(screen.getByText(/no submissions yet/i)).toBeInTheDocument();
    });
  });

  it('lists submissions grouped by status and shows last_error for rejected', async () => {
    await db.submissions.bulkPut([
      mkSub({ client_submission_id: 'a', status: 'pending_sync' }),
      mkSub({ client_submission_id: 'b', status: 'synced', synced_at: Date.UTC(2026, 3, 18, 2, 0, 0) }),
      mkSub({ client_submission_id: 'c', status: 'rejected', last_error: { code: 'E_VALIDATION', message: 'bad field' } }),
      mkSub({ client_submission_id: 'd', status: 'retry_scheduled', next_retry_at: Date.UTC(2026, 3, 18, 3, 0, 0), last_error: { code: 'E_NETWORK', message: 'offline' } }),
    ]);
    render(<SyncPage runSync={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('a')).toBeInTheDocument();
      expect(screen.getByText('b')).toBeInTheDocument();
      expect(screen.getByText(/E_VALIDATION/)).toBeInTheDocument();
      expect(screen.getByText(/E_NETWORK/)).toBeInTheDocument();
    });
  });
});
