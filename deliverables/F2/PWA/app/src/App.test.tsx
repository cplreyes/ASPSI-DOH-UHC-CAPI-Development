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

/**
 * #808: the per-case ConsentScreen now gates Section A. Click through it —
 * agree + continue — the way a consenting respondent would. #1002: the agree
 * path now shows an optional raffle phone field; fill it so Continue advances
 * without the blank-number confirm (which has its own dedicated test).
 */
async function passConsent(user: ReturnType<typeof userEvent.setup>) {
  await screen.findByTestId('consent-agree');
  await user.click(screen.getByTestId('consent-agree'));
  await user.type(screen.getByTestId('consent-raffle-phone'), '09171234567');
  await user.click(screen.getByTestId('consent-continue'));
}

describe('<App>', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await seedEnrollment();
    // #808: consent state rides in the draft (consent_given) and the draft id
    // rides in localStorage; clear both so every test starts at the consent
    // gate deterministically.
    await db.drafts.clear();
    // #825: refusal tests assert the submissions queue — start empty.
    await db.submissions.clear();
    localStorage.clear();
    // Routing (F2-Facility-Slug-Links): the path decides the unenrolled screen,
    // so pin every test to the root unless it sets its own URL.
    window.history.replaceState({}, '', '/');
  });

  it('renders Section A heading after loading (post-consent — #808)', async () => {
    const user = userEvent.setup();
    render(<App />);
    await passConsent(user);
    expect(
      await screen.findByRole('heading', {
        name: /Section A — Healthcare Worker Profile/,
      }),
    ).toBeInTheDocument();
  });

  it('#1002: agreeing with a blank raffle phone asks for confirmation, then proceeds', async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByTestId('consent-agree');
    await user.click(screen.getByTestId('consent-agree'));
    // Phone field is optional but blank → Continue opens the confirm panel
    // instead of advancing.
    await user.click(screen.getByTestId('consent-continue'));
    expect(await screen.findByTestId('consent-blank-phone-confirm')).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: /Section A — Healthcare Worker Profile/ }),
    ).not.toBeInTheDocument();
    // "Go back" returns to the form without advancing.
    await user.click(screen.getByTestId('consent-blank-phone-back'));
    expect(screen.queryByTestId('consent-blank-phone-confirm')).not.toBeInTheDocument();
    // Re-confirm and proceed without a number.
    await user.click(screen.getByTestId('consent-continue'));
    await user.click(screen.getByTestId('consent-blank-phone-proceed'));
    expect(
      await screen.findByRole('heading', { name: /Section A — Healthcare Worker Profile/ }),
    ).toBeInTheDocument();
  });

  it('#808: consent gate appears before Section A; declining shows the declined screen', async () => {
    const user = userEvent.setup();
    render(<App />);
    expect(await screen.findByTestId('consent-agree')).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: /Section A — Healthcare Worker Profile/ }),
    ).not.toBeInTheDocument();
    await user.click(screen.getByTestId('consent-decline'));
    await user.click(screen.getByTestId('consent-continue'));
    expect(
      await screen.findByRole('heading', { name: /thank you for your time/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: /Section A — Healthcare Worker Profile/ }),
    ).not.toBeInTheDocument();
  });

  it('#825: declining queues a refusal submission (consent_given = 0) for sync', async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByTestId('consent-decline');
    await user.click(screen.getByTestId('consent-decline'));
    await user.click(screen.getByTestId('consent-continue'));
    await screen.findByRole('heading', { name: /thank you for your time/i });
    // The refusal rides the normal offline queue; sync may already be
    // retrying against the (absent) test proxy, so assert identity fields
    // only — not the transient sync status.
    await waitFor(async () => {
      const rows: SubmissionRow[] = await db.submissions.toArray();
      expect(rows).toHaveLength(1);
      expect(rows[0].values.consent_given).toBe(0);
      expect(typeof rows[0].values.consent_timestamp).toBe('number');
      expect(rows[0].hcw_id).toBe('HCW-1');
      expect(rows[0].values.submission_lat).toBeNull();
    });
    // The draft is consumed — Start over must mint a fresh case.
    expect(await db.drafts.count()).toBe(0);
    expect(localStorage.getItem('f2_current_draft_id')).toBeNull();
  });

  it('#808: agreeing records consent_given + consent_timestamp into the draft', async () => {
    const user = userEvent.setup();
    render(<App />);
    await passConsent(user);
    await screen.findByLabelText(/What is your sex at birth/);
    await waitFor(async () => {
      const draftId = localStorage.getItem('f2_current_draft_id');
      expect(draftId).toBeTruthy();
      const row = await db.drafts.get(draftId!);
      expect(row?.values).toMatchObject({ consent_given: 1 });
      expect(typeof row?.values['consent_timestamp']).toBe('number');
    });
  });

  it('renders at least one Section A question after loading', async () => {
    const user = userEvent.setup();
    render(<App />);
    await passConsent(user);
    expect(await screen.findByLabelText(/What is your sex at birth/)).toBeInTheDocument();
  });

  it('autosaves an answer and restores it after remount', async () => {
    const user = userEvent.setup();

    const first = render(<App />);
    await passConsent(user);
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

  // F2-Facility-Slug-Links: the token-paste EnrollmentScreen moved behind
  // /enroll (enumerator-assisted use); /f/<slug> is the primary way in and the
  // bare root shows a "get your facility link" pointer instead of a form.
  it('renders the EnrollmentScreen at /enroll when no enrollment row exists', async () => {
    await db.enrollment.clear();
    window.history.replaceState({}, '', '/enroll');
    render(<App />);
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /enrol|enroll/i })).toBeInTheDocument(),
    );
  });

  it('renders the FacilityStartScreen at /f/<slug> when unenrolled', async () => {
    await db.enrollment.clear();
    window.history.replaceState({}, '', '/f/lphbay');
    render(<App />);
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /opening the survey/i })).toBeInTheDocument(),
    );
  });

  it('on a /f/<slug> device, "Start new survey" unenrolls back to the facility start screen (fresh QN per respondent)', async () => {
    // The enrollment token is bound to respondent A's QN; respondent B reusing
    // it would put two people's answers under one 12-digit case key. The
    // thank-you button must route B through a fresh self-register instead.
    window.history.replaceState({}, '', '/f/lphbay');
    localStorage.setItem('f2_completed_csid', 'srv-csid-test');
    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole('button', { name: /start new survey/i });
    await user.click(screen.getByRole('button', { name: /start new survey/i }));
    // Unenrolled + /f/<slug> → FacilityStartScreen (its resolve begins).
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /opening the survey/i })).toBeInTheDocument(),
    );
    expect(await db.enrollment.get('singleton')).toBeUndefined();
    expect(localStorage.getItem('f2_completed_csid')).toBeNull();
  });

  it('renders the facility-link pointer (no enrollment form) at the bare root when unenrolled', async () => {
    await db.enrollment.clear();
    render(<App />);
    await waitFor(() =>
      expect(
        screen.getByRole('heading', { name: /open your facility survey link/i }),
      ).toBeInTheDocument(),
    );
    expect(screen.queryByRole('heading', { name: /enrol|enroll/i })).not.toBeInTheDocument();
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

    // #808: a new case re-consents before Section A.
    await passConsent(user);

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
