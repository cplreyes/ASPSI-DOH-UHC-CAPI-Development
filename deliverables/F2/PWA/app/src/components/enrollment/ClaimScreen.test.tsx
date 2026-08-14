/**
 * Tests for the Model C numbered-link claim flow (design
 * F2-Model-C-Numbered-Links-2026-07-16). Opening `/e/<slug>?k=<secret>` on an
 * unenrolled device auto-claims the slot: no token box, no HCW-ID picker — on
 * success the device is enrolled device-bound to the returned QN.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '@/lib/auth-context';
import { LocaleProvider } from '@/i18n/locale-context';
import { db } from '@/lib/db';
import { ClaimScreen } from './ClaimScreen';
import * as claimClient from '@/lib/claim-client';

function setUrl(path: string) {
  window.history.pushState({}, '', path);
}

function mockClaimOk(over: Partial<{ hcw_id: string; qn: string; facility_id: string; token: string }> = {}) {
  return vi.spyOn(claimClient, 'claimBySlug').mockResolvedValue({
    ok: true,
    token: over.token ?? 'device.jwt.token',
    hcw_id: over.hcw_id ?? 'h1',
    qn: over.qn ?? '040340210119',
    facility_id: over.facility_id ?? '040340210',
  });
}

function setup() {
  return render(
    <LocaleProvider>
      <AuthProvider>
        <ClaimScreen />
      </AuthProvider>
    </LocaleProvider>,
  );
}

describe('<ClaimScreen>', () => {
  // Unmount BEFORE clearing, not after. ClaimScreen's mount effect chain
  // (runClaim -> enroll) and AuthProvider's own mount effect keep writing after
  // waitFor() has already seen the row it was waiting for; if the previous test's
  // component is still mounted, those late writes land after the clear and the
  // next test inherits an enrollment row it never created. That is what made the
  // E_CONFLICT case flaky — it found the previous test's `hcw_id: 'h1'` row.
  beforeEach(async () => {
    cleanup();
    if (!db.isOpen()) await db.open();
    await db.enrollment.clear();
    vi.restoreAllMocks();
    setUrl('/e/LPHBAY-HCW-19?k=a9f3kd');
  });

  afterEach(async () => {
    cleanup();
    await db.enrollment.clear();
  });

  it('auto-claims on mount with the slug + secret parsed from the URL', async () => {
    const spy = mockClaimOk();
    setup();
    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1));
    expect(spy.mock.calls[0]?.[0]?.slug).toBe('LPHBAY-HCW-19');
    expect(spy.mock.calls[0]?.[0]?.k).toBe('a9f3kd');
  });

  it('enrolls device-bound to the claimed QN on success', async () => {
    mockClaimOk();
    setup();
    await waitFor(async () => {
      const row = await db.enrollment.get('singleton');
      expect(row?.hcw_id).toBe('h1');
      expect(row?.facility_id).toBe('040340210');
      expect(row?.qn).toBe('040340210119');
      expect(row?.device_token).toBe('device.jwt.token');
    });
  });

  it('shows the completed message on E_CONFLICT (already submitted)', async () => {
    vi.spyOn(claimClient, 'claimBySlug').mockResolvedValue({
      ok: false,
      transport: false,
      error: { code: 'E_CONFLICT', message: 'done' },
    });
    setup();
    await waitFor(() => expect(screen.getByTestId('claim-error')).toBeInTheDocument());
    expect(screen.getByTestId('claim-error').textContent).toMatch(/already been completed/i);
    // No enrollment written on failure.
    expect(await db.enrollment.get('singleton')).toBeUndefined();
  });

  it('shows the offline message on E_NETWORK and Retry re-runs the claim', async () => {
    const spy = vi
      .spyOn(claimClient, 'claimBySlug')
      .mockResolvedValueOnce({ ok: false, transport: true, error: { code: 'E_NETWORK', message: 'off' } })
      .mockResolvedValueOnce({
        ok: true,
        token: 'device.jwt.token',
        hcw_id: 'h1',
        qn: '040340210119',
        facility_id: '040340210',
      });
    const user = userEvent.setup();
    setup();
    await waitFor(() => expect(screen.getByTestId('claim-error')).toBeInTheDocument());
    expect(screen.getByTestId('claim-error').textContent).toMatch(/offline/i);
    await user.click(screen.getByTestId('claim-retry'));
    await waitFor(async () => {
      expect(spy).toHaveBeenCalledTimes(2);
      expect((await db.enrollment.get('singleton'))?.qn).toBe('040340210119');
    });
  });

  it('rejects a claim URL missing the secret without calling the server', async () => {
    const spy = mockClaimOk();
    setUrl('/e/LPHBAY-HCW-19');
    setup();
    await waitFor(() => expect(screen.getByTestId('claim-error')).toBeInTheDocument());
    expect(spy).not.toHaveBeenCalled();
    expect(screen.getByTestId('claim-error').textContent).toMatch(/invalid|expired/i);
  });
});
