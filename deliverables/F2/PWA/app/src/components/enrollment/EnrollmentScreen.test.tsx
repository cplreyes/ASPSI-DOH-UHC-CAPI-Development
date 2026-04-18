import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '@/lib/auth-context';
import { db } from '@/lib/db';
import { EnrollmentScreen } from './EnrollmentScreen';

function setup(props: Partial<React.ComponentProps<typeof EnrollmentScreen>> = {}) {
  return render(
    <AuthProvider>
      <EnrollmentScreen onRefresh={vi.fn().mockResolvedValue({ ok: true, count: 1 })} {...props} />
    </AuthProvider>,
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
  });

  it('renders the title, HCW id input, and a populated facility select', async () => {
    setup();
    expect(
      screen.getByRole('heading', { name: /enrol|enroll/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/HCW ID/i)).toBeInTheDocument();
    await waitFor(() => {
      const select = screen.getByLabelText(/Facility/i) as HTMLSelectElement;
      expect(select.options.length).toBeGreaterThanOrEqual(3);
    });
    expect(screen.getByText('Cebu Health Center')).toBeInTheDocument();
  });

  it('disables Enroll until both fields are filled', async () => {
    const user = userEvent.setup();
    setup();
    await waitFor(() => screen.getByText('Manila General'));
    const button = screen.getByRole('button', { name: /^enroll$/i });
    expect(button).toBeDisabled();

    await user.type(screen.getByLabelText(/HCW ID/i), 'HCW-42');
    expect(button).toBeDisabled();

    await user.selectOptions(screen.getByLabelText(/Facility/i), 'F-001');
    expect(button).toBeEnabled();
  });

  it('calls onRefresh when the refresh button is clicked', async () => {
    const onRefresh = vi.fn().mockResolvedValue({ ok: true, count: 2 });
    const user = userEvent.setup();
    setup({ onRefresh });
    await waitFor(() => screen.getByText('Manila General'));
    await user.click(screen.getByRole('button', { name: /refresh/i }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it('shows an empty-state message + refresh button when no facilities are cached', async () => {
    await db.facilities.clear();
    setup();
    await waitFor(() =>
      expect(screen.getByText(/no facilities/i)).toBeInTheDocument(),
    );
    expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
  });

  it('persists enrollment on submit', async () => {
    const user = userEvent.setup();
    setup();
    await waitFor(() => screen.getByText('Manila General'));
    await user.type(screen.getByLabelText(/HCW ID/i), 'HCW-42');
    await user.selectOptions(screen.getByLabelText(/Facility/i), 'F-001');
    await user.click(screen.getByRole('button', { name: /^enroll$/i }));
    await waitFor(async () => {
      const row = await db.enrollment.get('singleton');
      expect(row?.hcw_id).toBe('HCW-42');
      expect(row?.facility_id).toBe('F-001');
      expect(row?.facility_type).toBe('Hospital');
    });
  });

  it('shows an error message if enrollment fails', async () => {
    const user = userEvent.setup();
    setup();
    await waitFor(() => screen.getByText('Manila General'));
    await user.type(screen.getByLabelText(/HCW ID/i), 'HCW-42');
    await user.selectOptions(screen.getByLabelText(/Facility/i), 'F-001');
    await db.facilities.clear();
    await user.click(screen.getByRole('button', { name: /^enroll$/i }));
    await waitFor(() =>
      expect(screen.getByText(/unknown facility/i)).toBeInTheDocument(),
    );
  });
});
