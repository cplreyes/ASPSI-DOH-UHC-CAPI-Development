/**
 * F2 Admin Portal — login screen.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.14, Step 3)
 * Design: deliverables/F2/PWA/app/DESIGN.md — Verde Manual.
 *
 * No card. Hairline border-bottom on inputs. Newsreader serif heading.
 * Signal-color CTA. Inline error banner using --error token. Disclosure
 * about session policy (in-memory token → reload re-prompts) at the
 * bottom in muted mono per the field-manual aesthetic.
 */
import { useState, type FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { useAdminAuth, type AdminLoginResponse } from './lib/auth-context';
import { adminFetch, type ApiError } from './lib/api-client';
import { useRouter } from './lib/pages-router';

export interface LoginProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

export function Login({ apiBaseUrl, fetchImpl }: LoginProps): JSX.Element {
  const { setAuth, isAuthenticated } = useAdminAuth();
  const { navigate } = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<ApiError | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // If already authenticated (e.g., user navigated to /admin/login by
  // accident with an active session), bounce to the operations dashboard.
  if (isAuthenticated) {
    navigate('/admin/data');
  }

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitting(true);

    const r = await adminFetch<AdminLoginResponse>(
      `${apiBaseUrl}/admin/api/login`,
      {
        method: 'POST',
        body: JSON.stringify({ username: username.trim(), password }),
      },
      fetchImpl ? { fetchImpl } : {},
    );
    setSubmitting(false);

    if (!r.ok) {
      setError(r.error);
      return;
    }

    setAuth(username.trim(), r.data);
    if (r.data.password_must_change) {
      navigate('/admin/me/change-password');
    } else {
      navigate('/admin/data');
    }
  };

  return (
    <main className="mx-auto flex min-h-screen-dvh w-full max-w-md flex-col justify-center px-6 py-12">
      <header className="mb-10">
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          F2 Admin
        </p>
        <h1 className="mt-1 font-serif text-3xl font-medium tracking-tight">Sign in</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Restricted to authorized ASPSI personnel.
        </p>
      </header>

      <form onSubmit={onSubmit} className="flex flex-col gap-6" noValidate>
        <label className="flex flex-col gap-1">
          <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Username
          </span>
          <input
            type="text"
            name="username"
            autoComplete="username"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="border-0 border-b border-hairline bg-transparent py-2 text-base outline-none focus:border-signal focus:ring-0"
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Password
          </span>
          <input
            type="password"
            name="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="border-0 border-b border-hairline bg-transparent py-2 text-base outline-none focus:border-signal focus:ring-0"
          />
        </label>

        {error ? (
          <div role="alert" className="border-l-2 border-error pl-3 py-2">
            <p className="text-sm text-error">{errorMessageFor(error)}</p>
            {error.requestId ? (
              <p className="mt-1 font-mono text-xs text-muted-foreground">
                ref {error.requestId}
              </p>
            ) : null}
          </div>
        ) : null}

        <Button type="submit" disabled={submitting || !username || !password}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>

      <footer className="mt-16 border-t border-hairline pt-4">
        <p className="font-mono text-xs leading-relaxed text-muted-foreground">
          Sessions are held in memory. Closing the tab or reloading signs you out.
        </p>
      </footer>
    </main>
  );
}

function errorMessageFor(error: ApiError): string {
  switch (error.code) {
    case 'E_AUTH_INVALID':
      return 'Username or password is incorrect.';
    case 'E_AUTH_LOCKED':
      return 'Too many failed attempts. Try again in a few minutes.';
    case 'E_VALIDATION':
      return 'Please enter both a username and a password.';
    case 'E_NETWORK':
      return 'Network unavailable. Check your connection and retry.';
    case 'E_BACKEND':
      return 'The service is temporarily unavailable. Retry shortly.';
    default:
      return error.message || 'Sign-in failed. Retry or contact admin.';
  }
}
