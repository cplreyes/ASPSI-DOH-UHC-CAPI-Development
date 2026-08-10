/**
 * Facility slug link start screen (design F2-Facility-Slug-Links-2026-07-16).
 * Opening `/f/<slug>` on an unenrolled device resolves the facility read-only
 * and shows a Start button; only the explicit Start tap self-registers and
 * enrolls the device qn-bound.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '@/lib/auth-context';
import { LocaleProvider } from '@/i18n/locale-context';
import { db } from '@/lib/db';
import { FacilityStartScreen } from './FacilityStartScreen';
import * as client from '@/lib/facility-start-client';

function setUrl(path: string) {
  window.history.pushState({}, '', path);
}

function mockResolveOk() {
  return vi.spyOn(client, 'resolveFacilitySlug').mockResolvedValue({
    ok: true,
    facility_id: '040340210',
    facility_name: 'LPH-Bay District Hospital',
  });
}

function mockRegisterOk() {
  return vi.spyOn(client, 'selfRegisterBySlug').mockResolvedValue({
    ok: true,
    token: 'device.jwt.token',
    hcw_id: 'sr-abc',
    qn: '040340210101',
    facility_id: '040340210',
    facility_name: 'LPH-Bay District Hospital',
  });
}

function setup() {
  return render(
    <LocaleProvider>
      <AuthProvider>
        <FacilityStartScreen />
      </AuthProvider>
    </LocaleProvider>,
  );
}

describe('<FacilityStartScreen>', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.enrollment.clear();
    vi.restoreAllMocks();
    setUrl('/f/lphbay');
  });

  it('resolves on mount and shows the facility name + Start (creates nothing)', async () => {
    const resolveSpy = mockResolveOk();
    const registerSpy = mockRegisterOk();
    setup();
    await waitFor(() => expect(screen.getByTestId('facility-start-name')).toBeInTheDocument());
    expect(resolveSpy).toHaveBeenCalledTimes(1);
    expect(resolveSpy.mock.calls[0]?.[0]?.slug).toBe('lphbay');
    expect(screen.getByTestId('facility-start-name').textContent).toMatch(/LPH-Bay/);
    expect(screen.getByTestId('facility-start-button')).toBeInTheDocument();
    // Page load must NOT self-register — Start is the explicit gate.
    expect(registerSpy).not.toHaveBeenCalled();
    expect(await db.enrollment.get('singleton')).toBeUndefined();
  });

  it('Start self-registers and enrolls device-bound to the returned QN + token', async () => {
    mockResolveOk();
    const registerSpy = mockRegisterOk();
    const user = userEvent.setup();
    setup();
    await screen.findByTestId('facility-start-button');
    await user.click(screen.getByTestId('facility-start-button'));
    await waitFor(async () => {
      const row = await db.enrollment.get('singleton');
      expect(row?.hcw_id).toBe('sr-abc');
      expect(row?.facility_id).toBe('040340210');
      expect(row?.qn).toBe('040340210101');
      expect(row?.device_token).toBe('device.jwt.token');
    });
    expect(registerSpy).toHaveBeenCalledTimes(1);
    expect(registerSpy.mock.calls[0]?.[0]?.slug).toBe('lphbay');
  });

  it('shows the inactive message (no Start button) on E_NOT_FOUND', async () => {
    vi.spyOn(client, 'resolveFacilitySlug').mockResolvedValue({
      ok: false,
      transport: false,
      error: { code: 'E_NOT_FOUND', message: 'inactive' },
    });
    setup();
    await waitFor(() => expect(screen.getByTestId('facility-start-error')).toBeInTheDocument());
    expect(screen.getByTestId('facility-start-error').textContent).toMatch(/isn't active/i);
    expect(screen.queryByTestId('facility-start-button')).not.toBeInTheDocument();
  });

  it('transient failures (bad JSON from a proxy error page, 5xx) say "try again", never "inactive"', async () => {
    vi.spyOn(client, 'resolveFacilitySlug').mockResolvedValue({
      ok: false,
      transport: true,
      error: { code: 'E_PARSE', message: 'Invalid JSON from server' },
    });
    setup();
    await waitFor(() => expect(screen.getByTestId('facility-start-error')).toBeInTheDocument());
    expect(screen.getByTestId('facility-start-error').textContent).toMatch(/temporarily unavailable/i);
    expect(screen.getByTestId('facility-start-error').textContent).not.toMatch(/isn't active/i);
  });

  it('offline resolve shows the offline message and Retry re-resolves', async () => {
    const spy = vi
      .spyOn(client, 'resolveFacilitySlug')
      .mockResolvedValueOnce({
        ok: false,
        transport: true,
        error: { code: 'E_NETWORK', message: 'off' },
      })
      .mockResolvedValueOnce({
        ok: true,
        facility_id: '040340210',
        facility_name: 'LPH-Bay District Hospital',
      });
    const user = userEvent.setup();
    setup();
    await waitFor(() => expect(screen.getByTestId('facility-start-error')).toBeInTheDocument());
    expect(screen.getByTestId('facility-start-error').textContent).toMatch(/offline/i);
    await user.click(screen.getByTestId('facility-start-retry'));
    await waitFor(() => expect(screen.getByTestId('facility-start-name')).toBeInTheDocument());
    expect(spy).toHaveBeenCalledTimes(2);
  });

  it('a failed Start surfaces the error and Retry recovers back to ready', async () => {
    mockResolveOk();
    vi.spyOn(client, 'selfRegisterBySlug').mockResolvedValue({
      ok: false,
      transport: false,
      error: { code: 'E_KILL_SWITCH', message: 'paused' },
    });
    const user = userEvent.setup();
    setup();
    await screen.findByTestId('facility-start-button');
    await user.click(screen.getByTestId('facility-start-button'));
    await waitFor(() => expect(screen.getByTestId('facility-start-error')).toBeInTheDocument());
    expect(screen.getByTestId('facility-start-error').textContent).toMatch(/temporarily unavailable/i);
    // No enrollment was written on failure.
    expect(await db.enrollment.get('singleton')).toBeUndefined();
    await user.click(screen.getByTestId('facility-start-retry'));
    await waitFor(() => expect(screen.getByTestId('facility-start-button')).toBeInTheDocument());
  });

  it('shows the inactive error without calling the server when the path is not a slug URL', async () => {
    const resolveSpy = mockResolveOk();
    setUrl('/f/');
    setup();
    await waitFor(() => expect(screen.getByTestId('facility-start-error')).toBeInTheDocument());
    expect(resolveSpy).not.toHaveBeenCalled();
  });
});
