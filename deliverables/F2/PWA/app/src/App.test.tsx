import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import { db, type SubmissionRow } from '@/lib/db';

/**
 * Build a fake JWT shaped like what the Worker would mint. parseClaimsUnsafe in
 * auth-context only reads `exp` to gate enrollment; signature is never verified
 * client-side, so a hand-rolled string is sufficient for tests.
 */
function makeFakeDeviceToken(overrides: Record<string, unknown> = {}): string {
  const b64url = (s: string) =>
    btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const header = b64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const claims = {
    jti: 'test-jti',
    tablet_id: 'test-tablet',
    facility_id: 'F-001',
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 86400,
    ...overrides,
  };
  const payload = b64url(JSON.stringify(claims));
  return `${header}.${payload}.fake-signature`;
}

async function seedEnrollment() {
  if (!db.isOpen()) await db.open();
  await db.facilities.clear();
  await db.enrollment.clear();
  await db.facilities.put({
    facility_id: 'F-001',
    facility_name: 'Manila General',
    facility_type: 'Hospital',
    region: 'NCR',
    province: 'Metro Manila',
    city_mun: 'Manila',
    barangay: 'Ermita',
  });
  await db.enrollment.put({
    id: 'singleton',
    hcw_id: 'HCW-1',
    facility_id: 'F-001',
    facility_type: 'Hospital',
    enrolled_at: 1,
    device_token: makeFakeDeviceToken(),
  });
}

describe('<App>', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await seedEnrollment();
  });

  it('renders Section A heading after loading', async () => {
    render(<App />);
    expect(
      await screen.findByRole('heading', {
        name: /Section A — Healthcare Worker Profile/,
      }),
    ).toBeInTheDocument();
  });

  it('renders at least one Section A question after loading', async () => {
    render(<App />);
    expect(await screen.findByLabelText(/What is your sex at birth/)).toBeInTheDocument();
  });

  it('autosaves an answer and restores it after remount', async () => {
    const user = userEvent.setup();

    const first = render(<App />);
    await screen.findByLabelText(/What is your sex at birth/);

    await user.click(screen.getByLabelText('Female'));

    await waitFor(
      async () => {
        const draftId = localStorage.getItem('f2_current_draft_id');
        expect(draftId).toBeTruthy();
        const row = await db.drafts.get(draftId!);
        expect(row?.values).toMatchObject({ Q3: 'Female' });
      },
      { timeout: 2000 },
    );

    first.unmount();

    render(<App />);
    await waitFor(() => {
      expect(screen.getByLabelText('Female')).toBeChecked();
    });
  });

  it('renders the EnrollmentScreen when no enrollment row exists', async () => {
    await db.enrollment.clear();
    render(<App />);
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /enrol|enroll/i })).toBeInTheDocument(),
    );
  });

  it('R2-#120 S.A2: persists submitted state across refresh via COMPLETED_CSID_KEY', async () => {
    // Pre-fix the tester reported "After refreshing, the form redirects
    // back to Section A" because the App init effect always created a
    // fresh draft. Now: if localStorage has f2_completed_csid, the
    // init effect short-circuits to status='submitted' and renders the
    // thank-you screen with a "Start new survey" button.
    localStorage.setItem('f2_completed_csid', 'srv-csid-test');
    render(<App />);
    expect(
      await screen.findByRole('heading', { name: /thank you/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: /Section A — Healthcare Worker Profile/ }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /start new survey/i })).toBeInTheDocument();
  });

  it('R2-#120 S.A2: "Start new survey" clears the persistence flag and returns to Section A', async () => {
    const user = userEvent.setup();
    localStorage.setItem('f2_completed_csid', 'srv-csid-test');
    render(<App />);
    await screen.findByRole('button', { name: /start new survey/i });

    await user.click(screen.getByRole('button', { name: /start new survey/i }));

    await waitFor(() =>
      expect(
        screen.getByRole('heading', { name: /Section A — Healthcare Worker Profile/ }),
      ).toBeInTheDocument(),
    );
    expect(localStorage.getItem('f2_completed_csid')).toBeNull();
  });
});

describe('App — sync integration', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
    await db.drafts.clear();
    localStorage.clear();
    await seedEnrollment();
  });

  it('renders a pending count badge when the DB has pending submissions', async () => {
    const row: SubmissionRow = {
      client_submission_id: 'csid-pending',
      hcw_id: 'h1',
      status: 'pending_sync',
      synced_at: null,
      submitted_at: Date.now(),
      spec_version: 'v',
      values: {},
      retry_count: 0,
      next_retry_at: null,
      last_error: null,
    };
    await db.submissions.put(row);
    render(<App />);
    expect(await screen.findByTestId('pending-count')).toHaveTextContent('1 pending');
  });

  it('opens the Sync page when the header "Sync" link is clicked', async () => {
    render(<App />);
    const user = userEvent.setup();
    await user.click(await screen.findByRole('button', { name: /^sync$/i }));
    expect(await screen.findByRole('heading', { name: /^sync$/i })).toBeInTheDocument();
  });
});
