import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from './auth-context';
import { db } from './db';

function Probe() {
  const { status, enrollment, enroll, unenroll } = useAuth();
  return (
    <div>
      <span data-testid="status">{status}</span>
      <span data-testid="hcw">{enrollment?.hcw_id ?? '-'}</span>
      <button onClick={() => void enroll({ hcw_id: 'HCW-1', facility_id: 'F-001' })}>enroll</button>
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

  it('unenroll() resets context state', async () => {
    await db.enrollment.put({
      id: 'singleton',
      hcw_id: 'HCW-PRE',
      facility_id: 'F-001',
      facility_type: 'Hospital',
      enrolled_at: 1,
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
