import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ResponseDetail } from './ResponseDetail';
import { AdminAuthProvider } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

/**
 * aug17 migration (maps/F2-renames.csv): Section J items Q109-Q125 (Apr-20
 * ids) shifted down to Q108-Q124 when the PDF's Q108 numbering gap closed.
 * Submissions recorded before the cutover deploy hold values_json keyed by
 * the OLD id, so ResponseDetail must fall back to `item.legacyId` for old
 * submissions to stay readable. See collectRows in ResponseDetail.tsx.
 */
const OLD_SUBMISSION_ROW = {
  submission_id: 'srv-legacy',
  client_submission_id: 'cli-legacy',
  submitted_at_server: '2026-08-01T12:30:00.000Z',
  submitted_at_client: '2026-08-01T12:00:00.000Z',
  source: 'pwa',
  spec_version: '2026-04-20-m1',
  app_version: '2.0.2',
  hcw_id: 'hcw-legacy',
  facility_id: 'fac-1',
  device_fingerprint: 'fp',
  status: 'stored',
  // Pre-cutover payload: paragraph question submitted under its Apr-20 id
  // Q109 (now Q108), and a multi-select "Other" answer submitted under its
  // Apr-20 id Q110 (now Q109).
  values_json: JSON.stringify({
    Q109: 'Housing allowance and transportation subsidy.',
    Q110: ['Other (specify)'],
    Q110_other: 'Telemedicine equipment',
  }),
  submission_lat: 14.5,
  submission_lng: 121.0,
  source_path: 'self_admin',
  encoded_by: '',
  encoded_at: '',
};

function fetchFor(row: unknown): typeof fetch {
  return (async () => json(row)) as unknown as typeof fetch;
}

function renderDetail(row: unknown) {
  return render(
    <AdminAuthProvider>
      <RouterProvider>
        <ResponseDetail apiBaseUrl="https://w.example" submissionId="srv-legacy" fetchImpl={fetchFor(row)} />
      </RouterProvider>
    </AdminAuthProvider>,
  );
}

describe('<ResponseDetail /> legacy-id fallback', () => {
  it('renders a pre-cutover single-value answer stored under its Apr-20 id', async () => {
    renderDetail(OLD_SUBMISSION_ROW);
    expect(await screen.findByText('Housing allowance and transportation subsidy.')).toBeInTheDocument();
  });

  it('renders a pre-cutover "Other (specify)" answer stored under its Apr-20 id', async () => {
    renderDetail(OLD_SUBMISSION_ROW);
    expect(await screen.findByText('Telemedicine equipment')).toBeInTheDocument();
  });

  it('still renders current-id answers directly for post-cutover submissions', async () => {
    const row = {
      ...OLD_SUBMISSION_ROW,
      submission_id: 'srv-current',
      spec_version: '2026-08-17-m1',
      values_json: JSON.stringify({ Q108: 'Meal and rice subsidy.' }),
    };
    renderDetail(row);
    expect(await screen.findByText('Meal and rice subsidy.')).toBeInTheDocument();
  });
});
