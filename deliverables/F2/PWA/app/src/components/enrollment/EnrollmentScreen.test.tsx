/**
 * Tests for the two-step enrollment flow (spec §4.2):
 *   Step 1: paste tablet token, verify against the Worker.
 *   Step 2: enter HCW ID, click Enroll.
 *
 * The facility is locked by the token's `facility_id` claim, so there's no
 * facility picker after the auth re-arch.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '@/lib/auth-context';
import { LocaleProvider } from '@/i18n/locale-context';
import { db } from '@/lib/db';
import { EnrollmentScreen } from './EnrollmentScreen';
import * as verifyClient from '@/lib/verify-token-client';

const FAKE_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJ0In0.fake-sig';

function mockVerifyOk(facilityId = 'F-001') {
  return vi.spyOn(verifyClient, 'verifyDeviceToken').mockResolvedValue({
    ok: true,
    claims: {
      facility_id: facilityId,
      exp: Math.floor(Date.now() / 1000) + 86400,
      tablet_id: 'test-tablet',
    },
  });
}

function setup(props: Partial<React.ComponentProps<typeof EnrollmentScreen>> = {}) {
  return render(
    <LocaleProvider>
      <AuthProvider>
        <EnrollmentScreen
          onRefresh={vi.fn().mockResolvedValue({ ok: true, count: 1 })}
          {...props}
        />
      </AuthProvider>
    </LocaleProvider>,
  );
}

describe('<EnrollmentScreen>', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.enrollment.clear();
    await db.facilities.clear();
    await db.facilities.bulkPut([
      {
        facility_id: 'F-001',
        facility_name: 'Manila General',
        facility_type: 'Hospital',
        region: 'NCR',
        province: 'Metro Manila',
        city_mun: 'Manila',
        barangay: 'Ermita',
      },
      {
        facility_id: 'F-002',
        facility_name: 'Cebu Health Center',
        facility_type: 'RHU',
        region: 'Region VII',
        province: 'Cebu',
        city_mun: 'Cebu City',
        barangay: 'Lahug',
      },
    ]);
    vi.restoreAllMocks();
  });

  it('starts on Step 1 with only the token input visible', () => {
    setup();
    expect(screen.getByRole('heading', { name: /enrol|enroll/i })).toBeInTheDocument();
    expect(screen.getByTestId('enrollment-token-input')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /verify token/i })).toBeInTheDocument();
    // Step 2 inputs should NOT be visible yet.
    expect(screen.queryByLabelText(/HCW ID/i)).not.toBeInTheDocument();
  });

  it('Verify is disabled until the user types a token', async () => {
    const user = userEvent.setup();
    setup();
    expect(screen.getByRole('button', { name: /verify token/i })).toBeDisabled();
    await user.type(screen.getByTestId('enrollment-token-input'), FAKE_TOKEN);
    expect(screen.getByRole('button', { name: /verify token/i })).toBeEnabled();
  });

  it('on successful verify, advances to Step 2 (HCW input + Enroll button)', async () => {
    mockVerifyOk('F-001');
    const user = userEvent.setup();
    setup();
    await user.type(screen.getByTestId('enrollment-token-input'), FAKE_TOKEN);
    await user.click(screen.getByRole('button', { name: /verify token/i }));
    await waitFor(() => expect(screen.getByTestId('enrollment-token-accepted')).toBeInTheDocument());
    expect(screen.getByLabelText(/HCW ID/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^enroll$/i })).toBeInTheDocument();
    // The accepted message names the facility from the token's claim.
    expect(screen.getByTestId('enrollment-token-accepted').textContent).toMatch(/Manila General/);
  });

  it('on rejected token, stays on Step 1 and shows an error', async () => {
    vi.spyOn(verifyClient, 'verifyDeviceToken').mockResolvedValue({
      ok: false,
      transport: false,
      error: { code: 'E_TOKEN_INVALID', message: 'Token rejected (bad-signature).' },
    });
    const user = userEvent.setup();
    setup();
    await user.type(screen.getByTestId('enrollment-token-input'), FAKE_TOKEN);
    await user.click(screen.getByRole('button', { name: /verify token/i }));
    await waitFor(() =>
      expect(screen.getByText(/Token rejected\. Contact ASPSI ops/)).toBeInTheDocument(),
    );
    expect(screen.queryByLabelText(/HCW ID/i)).not.toBeInTheDocument();
  });

  it('on revoked token, shows the revocation-specific copy', async () => {
    vi.spyOn(verifyClient, 'verifyDeviceToken').mockResolvedValue({
      ok: false,
      transport: false,
      error: { code: 'E_TOKEN_REVOKED', message: 'Token has been revoked.' },
    });
    const user = userEvent.setup();
    setup();
    await user.type(screen.getByTestId('enrollment-token-input'), FAKE_TOKEN);
    await user.click(screen.getByRole('button', { name: /verify token/i }));
    await waitFor(() =>
      expect(screen.getByText(/This tablet has been revoked/)).toBeInTheDocument(),
    );
  });

  it('Enroll is disabled until HCW ID is filled in Step 2', async () => {
    mockVerifyOk('F-001');
    const user = userEvent.setup();
    setup();
    await user.type(screen.getByTestId('enrollment-token-input'), FAKE_TOKEN);
    await user.click(screen.getByRole('button', { name: /verify token/i }));
    await waitFor(() => screen.getByLabelText(/HCW ID/i));
    expect(screen.getByRole('button', { name: /^enroll$/i })).toBeDisabled();
    await user.type(screen.getByLabelText(/HCW ID/i), 'HCW-42');
    expect(screen.getByRole('button', { name: /^enroll$/i })).toBeEnabled();
  });

  it('persists enrollment with hcw_id, facility_id from token claim, and the device_token', async () => {
    mockVerifyOk('F-001');
    const user = userEvent.setup();
    setup();
    await user.type(screen.getByTestId('enrollment-token-input'), FAKE_TOKEN);
    await user.click(screen.getByRole('button', { name: /verify token/i }));
    await waitFor(() => screen.getByLabelText(/HCW ID/i));
    await user.type(screen.getByLabelText(/HCW ID/i), 'HCW-42');
    await user.click(screen.getByRole('button', { name: /^enroll$/i }));
    await waitFor(async () => {
      const row = await db.enrollment.get('singleton');
      expect(row?.hcw_id).toBe('HCW-42');
      expect(row?.facility_id).toBe('F-001');
      expect(row?.facility_type).toBe('Hospital');
      expect(row?.device_token).toBe(FAKE_TOKEN);
    });
  });

  it('calls onRefresh when the refresh button is clicked (after token verify)', async () => {
    mockVerifyOk('F-001');
    const onRefresh = vi.fn().mockResolvedValue({ ok: true, count: 2 });
    const user = userEvent.setup();
    setup({ onRefresh });
    await user.type(screen.getByTestId('enrollment-token-input'), FAKE_TOKEN);
    await user.click(screen.getByRole('button', { name: /verify token/i }));
    await waitFor(() => screen.getByLabelText(/HCW ID/i));
    await user.click(screen.getByRole('button', { name: /refresh/i }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
