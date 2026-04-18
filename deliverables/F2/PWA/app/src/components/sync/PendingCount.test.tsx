import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { db, type SubmissionRow } from '@/lib/db';
import { PendingCount } from './PendingCount';

function mkSub(id: string, status: SubmissionRow['status']): SubmissionRow {
  return {
    client_submission_id: id,
    hcw_id: 'h1',
    status,
    synced_at: null,
    submitted_at: 1,
    spec_version: 'v',
    values: {},
    retry_count: 0,
    next_retry_at: null,
    last_error: null,
  };
}

describe('PendingCount', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('renders nothing when there are zero pending/retry rows', async () => {
    render(<PendingCount />);
    await waitFor(() => {
      expect(screen.queryByTestId('pending-count')).toBeNull();
    });
  });

  it('shows the count of pending_sync + retry_scheduled rows', async () => {
    await db.submissions.bulkPut([
      mkSub('a', 'pending_sync'),
      mkSub('b', 'retry_scheduled'),
      mkSub('c', 'synced'),
      mkSub('d', 'pending_sync'),
    ]);
    render(<PendingCount />);
    await waitFor(() => {
      expect(screen.getByTestId('pending-count')).toHaveTextContent('3 pending');
    });
  });

  it('updates live when a new pending row is inserted', async () => {
    render(<PendingCount />);
    await waitFor(() => expect(screen.queryByTestId('pending-count')).toBeNull());
    await db.submissions.put(mkSub('z', 'pending_sync'));
    await waitFor(() => {
      expect(screen.getByTestId('pending-count')).toHaveTextContent('1 pending');
    });
  });
});
