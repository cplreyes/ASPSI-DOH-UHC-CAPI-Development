import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from './auth-context';
import { db } from './db';
import * as enrollmentModule from './enrollment';

/** Hand-rolled JWT for tests; auth-context only reads `exp` via parseClaimsUnsafe. */
function fakeDeviceToken(expEpochS = Math.floor(Date.now() / 1000) + 86400): string {
  const b64url = (s: string) => btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const header = b64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = b64url(
    JSON.stringify({
      jti: 'test-jti',
      tablet_id: 'test-tablet',
      facility_id: 'F-001',
      iat: Math.floor(Date.now() / 1000),
      exp: expEpochS,
    }),
  );
  return `${header}.${payload}.fake-sig`;
}

function Probe() {
  const { status, enrollment, enroll, unenroll } = useAuth();
  return (
    <div>
      <span data-testid="status">{status}</span>
      <span data-testid="hcw">{enrollment?.hcw_id ?? '-'}</span>
      <button
        onClick={() =>
          void enroll({ hcw_id: 'HCW-1', facility_id: 'F-001', device_token: fakeDeviceToken() })
        }
      >
        enroll
      </button>
      <button onClick={() => void unenroll()}>unenroll</button>
    </div>
  );
}

describe('<AuthProvider>', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.enrollment.clear();
    await db.facilities.clear();
    await db.facilities.put({
      facility_id: 'F-001',
      facility_name: 'Manila General',
      facility_type: 'Hospital',
      region: 'NCR',
      province: 'Metro Manila',
      city_mun: 'Manila',
      barangay: 'Ermita',
    });
  });

  it('boots into "unenrolled" when no row exists', async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('unenrolled'));
    expect(screen.getByTestId('hcw').textContent).toBe('-');
  });

  it('boots into "enrolled" when a row exists', async () => {
    await db.enrollment.put({
      id: 'singleton',
      hcw_id: 'HCW-PRE',
      facility_id: 'F-001',
      facility_type: 'Hospital',
      enrolled_at: 1,
      device_token: fakeDeviceToken(),
    });
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('enrolled'));
    expect(screen.getByTestId('hcw').textContent).toBe('HCW-PRE');
  });

  it('enroll() updates context state', async () => {
    const user = userEvent.setup();
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('unenrolled'));
    await user.click(screen.getByRole('button', { name: 'enroll' }));
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('enrolled'));
    expect(screen.getByTestId('hcw').textContent).toBe('HCW-1');
  });

  it('falls back to "unenrolled" when getEnrollment rejects', async () => {
    const spy = vi
      .spyOn(enrollmentModule, 'getEnrollment')
      .mockRejectedValueOnce(new Error('dexie boom'));
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('unenrolled'));
    expect(spy).toHaveBeenCalled();
    expect(errorSpy).toHaveBeenCalled();
    spy.mockRestore();
    errorSpy.mockRestore();
  });

  it('unenroll() resets context state', async () => {
    await db.enrollment.put({
      id: 'singleton',
      hcw_id: 'HCW-PRE',
      facility_id: 'F-001',
      facility_type: 'Hospital',
      enrolled_at: 1,
      device_token: fakeDeviceToken(),
    });
    const user = userEvent.setup();
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('enrolled'));
    await user.click(screen.getByRole('button', { name: 'unenroll' }));
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('unenrolled'));
  });
});
