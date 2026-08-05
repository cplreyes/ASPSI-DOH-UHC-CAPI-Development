/**
 * Tests for the Controls panel (kill switch + broadcast message), extracted
 * from DataSettings 2026-07-17 (Apps-tab audit P2-1). The kill switch is the
 * portal's emergency stop — the confirm-before-toggle flow and the PATCH
 * payloads are the load-bearing behavior.
 */
import { describe, expect, it } from 'vitest';
import { useEffect } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Controls } from './Controls';
import { AdminAuthProvider, useAdminAuth } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

const TOKEN = 'test-token';

interface Call {
  url: string;
  method: string;
  init: RequestInit | undefined;
}

function makeFetch(opts: { killSwitch?: boolean; broadcast?: string; broadcastStatus?: number } = {}): {
  fetch: typeof fetch;
  calls: Call[];
} {
  const { killSwitch = false, broadcast = '', broadcastStatus = 200 } = opts;
  const calls: Call[] = [];
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
  const impl = (async (url: string | URL, init?: RequestInit) => {
    const u = String(url);
    const method = (init?.method ?? 'GET').toUpperCase();
    calls.push({ url: u, method, init });
    if (u.includes('/apps/kill-switch')) {
      if (method === 'PATCH') {
        const body = JSON.parse(init!.body as string) as { kill_switch: boolean };
        return json({ kill_switch: body.kill_switch });
      }
      return json({ kill_switch: killSwitch });
    }
    if (u.includes('/apps/broadcast')) {
      if (broadcastStatus === 404) {
        return json({ ok: false, error: { code: 'E_NOT_FOUND', message: 'not found' } }, 404);
      }
      if (broadcastStatus !== 200) {
        return json({ ok: false, error: { code: 'E_BACKEND', message: 'backend down' } }, broadcastStatus);
      }
      if (method === 'PATCH') {
        const body = JSON.parse(init!.body as string) as { broadcast_message: string };
        return json({ broadcast_message: body.broadcast_message });
      }
      return json({ broadcast_message: broadcast });
    }
    return json({ ok: false, error: { code: 'E_NOT_FOUND', message: 'unmatched' } }, 404);
  }) as unknown as typeof fetch;
  return { fetch: impl, calls };
}

function AuthPrime({ children }: { children: React.ReactNode }): JSX.Element | null {
  const { setAuth, isAuthenticated } = useAdminAuth();
  useEffect(() => {
    setAuth('shan_admin', {
      token: TOKEN,
      role: 'Administrator',
      role_version: 0,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      password_must_change: false,
    });
  }, [setAuth]);
  return isAuthenticated ? <>{children}</> : null;
}

function renderControls(fetchImpl: typeof fetch) {
  return render(
    <AdminAuthProvider>
      <RouterProvider>
        <AuthPrime>
          <Controls apiBaseUrl="https://api.example" fetchImpl={fetchImpl} />
        </AuthPrime>
      </RouterProvider>
    </AdminAuthProvider>,
  );
}

describe('<Controls /> — kill switch', () => {
  it('turning ON requires the confirm modal, then PATCHes with the token', async () => {
    const user = userEvent.setup();
    const { fetch: mockFetch, calls } = makeFetch();
    renderControls(mockFetch);

    await screen.findByText(/OFF — submissions open/);
    await user.click(screen.getByRole('button', { name: 'Turn ON' }));

    // No PATCH yet — the confirm dialog gates it.
    expect(calls.some((c) => c.method === 'PATCH')).toBe(false);
    const dialog = await screen.findByRole('dialog');
    expect(dialog).toHaveTextContent(/block all HCW survey submissions/i);

    await user.click(screen.getByRole('button', { name: 'Yes, block submissions' }));
    await screen.findByText(/ON — submissions blocked/);

    const patch = calls.find((c) => c.method === 'PATCH' && c.url.includes('/apps/kill-switch'));
    expect(patch).toBeTruthy();
    expect(JSON.parse(patch!.init!.body as string)).toEqual({ kill_switch: true });
    const headers = new Headers(patch!.init?.headers);
    expect(headers.get('Authorization')).toBe(`Bearer ${TOKEN}`);
  });

  it('cancelling the confirm modal sends no PATCH', async () => {
    const user = userEvent.setup();
    const { fetch: mockFetch, calls } = makeFetch();
    renderControls(mockFetch);

    await screen.findByText(/OFF — submissions open/);
    await user.click(screen.getByRole('button', { name: 'Turn ON' }));
    await user.click(await screen.findByRole('button', { name: 'Cancel' }));

    expect(screen.queryByRole('dialog')).toBeNull();
    expect(calls.some((c) => c.method === 'PATCH')).toBe(false);
    await screen.findByText(/OFF — submissions open/);
  });
});

describe('<Controls /> — broadcast message', () => {
  it('saves the trimmed draft via PATCH and shows Saved', async () => {
    const user = userEvent.setup();
    const { fetch: mockFetch, calls } = makeFetch({ broadcast: '' });
    renderControls(mockFetch);

    const box = await screen.findByRole('textbox', { name: 'Broadcast message' });
    await user.type(box, '  Survey closes Friday 5 PM.  ');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await screen.findByText('Saved');
    const patch = calls.find((c) => c.method === 'PATCH' && c.url.includes('/apps/broadcast'));
    expect(patch).toBeTruthy();
    expect(JSON.parse(patch!.init!.body as string)).toEqual({
      broadcast_message: 'Survey closes Friday 5 PM.',
    });
  });

  it('hides entirely when the broadcast route 404s, kill switch still renders', async () => {
    const { fetch: mockFetch } = makeFetch({ broadcastStatus: 404 });
    renderControls(mockFetch);

    await screen.findByText(/OFF — submissions open/);
    await waitFor(() =>
      expect(screen.queryByRole('textbox', { name: 'Broadcast message' })).toBeNull(),
    );
  });

  it('surfaces a non-404 load failure instead of vanishing', async () => {
    const { fetch: mockFetch } = makeFetch({ broadcastStatus: 502 });
    renderControls(mockFetch);

    await screen.findByText(/OFF — submissions open/);
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/backend unavailable/i);
  });
});
