import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Login } from './Login';
import { AdminAuthProvider } from './lib/auth-context';
import { RouterProvider } from './lib/pages-router';

function jsonResponse(body: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}

function renderLogin(fetchImpl: typeof fetch) {
  return render(
    <AdminAuthProvider>
      <RouterProvider>
        <Login apiBaseUrl="https://worker.example" fetchImpl={fetchImpl} />
      </RouterProvider>
    </AdminAuthProvider>,
  );
}

describe('<Login />', () => {
  it('renders username + password inputs and a sign-in button', () => {
    const fetchImpl = vi.fn() as unknown as typeof fetch;
    renderLogin(fetchImpl);
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument();
    // password is type=password, no implicit role — find by label.
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('disables sign-in until both fields have content', () => {
    const fetchImpl = vi.fn() as unknown as typeof fetch;
    renderLogin(fetchImpl);
    expect(screen.getByRole('button', { name: /sign in/i })).toBeDisabled();
  });

  it('shows the per-tab session disclosure', () => {
    const fetchImpl = vi.fn() as unknown as typeof fetch;
    renderLogin(fetchImpl);
    expect(screen.getByText(/sessions stay open within this browser tab/i)).toBeInTheDocument();
  });

  it('surfaces a typed error message on E_AUTH_INVALID', async () => {
    const user = userEvent.setup();
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ ok: false, error: { code: 'E_AUTH_INVALID', message: 'bad' } }, 401, {
        'X-Request-Id': 'req-7',
      }),
    ) as unknown as typeof fetch;
    renderLogin(fetchImpl);

    await user.type(screen.getByRole('textbox', { name: /username/i }), 'alice');
    await user.type(screen.getByLabelText(/password/i), 'wrong');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/invalid credentials/i);
    });
    expect(screen.getByText(/req-7/i)).toBeInTheDocument();
  });

  it('surfaces a throttled message on E_AUTH_LOCKED', async () => {
    const user = userEvent.setup();
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ ok: false, error: { code: 'E_AUTH_LOCKED', message: 'locked' } }, 429),
    ) as unknown as typeof fetch;
    renderLogin(fetchImpl);

    await user.type(screen.getByRole('textbox', { name: /username/i }), 'alice');
    await user.type(screen.getByLabelText(/password/i), 'x');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/too many failed attempts/i);
    });
  });

  it('calls /admin/api/login with the provided base URL and JSON body', async () => {
    const user = userEvent.setup();
    const fetchImpl = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      expect(String(url)).toBe('https://worker.example/admin/api/login');
      expect(init?.method).toBe('POST');
      const body = JSON.parse(String(init?.body));
      expect(body).toEqual({ username: 'alice', password: 'CorrectPw1' });
      return jsonResponse({
        token: 't.t.t',
        role: 'Administrator',
        role_version: 1,
        expires_at: Math.floor(Date.now() / 1000) + 3600,
        password_must_change: false,
      });
    }) as unknown as typeof fetch;
    renderLogin(fetchImpl);

    await user.type(screen.getByRole('textbox', { name: /username/i }), 'alice');
    await user.type(screen.getByLabelText(/password/i), 'CorrectPw1');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(fetchImpl).toHaveBeenCalled());
  });

  it('preserves the deep-linked URL after re-login (UAT R2 #71 L.A2)', async () => {
    const user = userEvent.setup();
    // Simulate the user being on a protected route — AdminRoot keeps the URL
    // intact while showing Login (FX-016). Login should NOT clobber it.
    window.history.replaceState({}, '', '/admin/data/responses/HCW-42');
    const fetchImpl = vi.fn(async () =>
      jsonResponse({
        token: 't.t.t',
        role: 'Administrator',
        role_version: 1,
        expires_at: Math.floor(Date.now() / 1000) + 3600,
        password_must_change: false,
      }),
    ) as unknown as typeof fetch;
    renderLogin(fetchImpl);

    await user.type(screen.getByRole('textbox', { name: /username/i }), 'alice');
    await user.type(screen.getByLabelText(/password/i), 'CorrectPw1');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(fetchImpl).toHaveBeenCalled());
    expect(window.location.pathname).toBe('/admin/data/responses/HCW-42');
  });

  it('bounces to /admin/data when login is reached cold (no deep link)', async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, '', '/admin/login');
    const fetchImpl = vi.fn(async () =>
      jsonResponse({
        token: 't.t.t',
        role: 'Administrator',
        role_version: 1,
        expires_at: Math.floor(Date.now() / 1000) + 3600,
        password_must_change: false,
      }),
    ) as unknown as typeof fetch;
    renderLogin(fetchImpl);

    await user.type(screen.getByRole('textbox', { name: /username/i }), 'alice');
    await user.type(screen.getByLabelText(/password/i), 'CorrectPw1');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(window.location.pathname).toBe('/admin/data'));
  });
});
