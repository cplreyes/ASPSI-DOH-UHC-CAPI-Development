import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import { i18n } from '@/i18n';
import { AuthProvider } from '@/lib/auth-context';
import { ChangeEnrollmentButton } from './ChangeEnrollmentButton';
import { DRAFT_ID_KEY } from '@/lib/draft';
import { db } from '@/lib/db';

function fakeDeviceToken(): string {
  const b64url = (s: string) =>
    btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const header = b64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = b64url(
    JSON.stringify({
      jti: 't',
      tablet_id: 't',
      facility_id: 'F-001',
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + 86400,
    }),
  );
  return `${header}.${payload}.fake`;
}

async function seedEnrollment() {
  if (!db.isOpen()) await db.open();
  await db.facilities.clear();
  await db.enrollment.clear();
  await db.facilities.put({
    facility_id: 'F-001',
    facility_name: 'A',
    facility_type: 'Hospital',
    region: 'r',
    province: 'p',
    city_mun: 'c',
    barangay: 'b',
  });
  await db.enrollment.put({
    id: 'singleton',
    hcw_id: 'H1',
    facility_id: 'F-001',
    facility_type: 'Hospital',
    enrolled_at: 1,
    device_token: fakeDeviceToken(),
  });
}

function wrap(ui: React.ReactNode) {
  return (
    <I18nextProvider i18n={i18n}>
      <AuthProvider>{ui}</AuthProvider>
    </I18nextProvider>
  );
}

describe('ChangeEnrollmentButton', () => {
  beforeEach(async () => {
    await seedEnrollment();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('calls unenroll after confirmation when no draft present', async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(wrap(<ChangeEnrollmentButton />));
    const btn = await screen.findByRole('button', { name: /change enrollment/i });
    await user.click(btn);
    expect(confirmSpy).toHaveBeenCalled();
    expect(confirmSpy.mock.calls[0][0]).not.toMatch(/draft/i);
  });

  it('warns about draft loss when draft exists', async () => {
    localStorage.setItem(DRAFT_ID_KEY, 'abc');
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    render(wrap(<ChangeEnrollmentButton />));
    const btn = await screen.findByRole('button', { name: /change enrollment/i });
    await user.click(btn);
    expect(confirmSpy.mock.calls[0][0]).toMatch(/draft/i);
  });

  it('does not unenroll when confirmation is cancelled', async () => {
    const user = userEvent.setup();
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    render(wrap(<ChangeEnrollmentButton />));
    const btn = await screen.findByRole('button', { name: /change enrollment/i });
    await user.click(btn);
    const row = await db.enrollment.get('singleton');
    expect(row).toBeDefined();
  });
});
