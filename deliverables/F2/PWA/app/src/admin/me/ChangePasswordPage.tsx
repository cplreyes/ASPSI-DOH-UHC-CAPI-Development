/**
 * F2 Admin Portal — user-self password rotation (R2-#134).
 *
 * Plan: epic-04-backend-sync-infrastructure.md (E4-APRT-051)
 *
 * Replaces the placeholder at `/admin/me/change-password`. Required when a
 * newly-created or admin-reset account lands here on first login (the login
 * flow redirects when `password_must_change` is true). Form mirrors Login's
 * Verde Manual identity: hairline-bordered inputs, mono labels, signal-color
 * primary CTA, no card chrome.
 *
 * On success: re-calls setAuth with the fresh JWT (same shape as login
 * response, with `password_must_change=false`) and navigates to /admin so
 * the user lands in the operations dashboard without a re-login round trip.
 */
import { useState, type FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth, type AdminLoginResponse } from '../lib/auth-context';
import { Link, useRouter } from '../lib/pages-router';

export interface ChangePasswordPageProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

const NEW_PASSWORD_MIN = 8;

export function ChangePasswordPage({ apiBaseUrl, fetchImpl }: ChangePasswordPageProps): JSX.Element {
  const { token, username, setAuth, passwordMustChange } = useAdminAuth();
  const { navigate } = useRouter();

  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const localValidationError = (): string | null => {
    if (!currentPw || !newPw || !confirmPw) return null;
    if (newPw.length < NEW_PASSWORD_MIN) {
      return `New password must be at least ${NEW_PASSWORD_MIN} characters.`;
    }
    if (newPw === currentPw) {
      return 'New password must differ from current password.';
    }
    if (newPw !== confirmPw) {
      return 'New password and confirmation do not match.';
    }
    return null;
  };

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (submitting) return;
    setError(null);

    const localErr = localValidationError();
    if (localErr) {
      setError(localErr);
      return;
    }
    if (!username) {
      setError('Session expired. Sign in again.');
      return;
    }

    setSubmitting(true);
    const r = await adminFetch<AdminLoginResponse>(
      `${apiBaseUrl}/admin/api/me/password`,
      {
        method: 'PATCH',
        body: JSON.stringify({ current_password: currentPw, new_password: newPw }),
      },
      {
        ...(token ? { token } : {}),
        ...(fetchImpl ? { fetchImpl } : {}),
      },
    );
    setSubmitting(false);

    if (!r.ok) {
      setError(messageFor(r.error));
      return;
    }

    setAuth(username, r.data);
    navigate('/admin');
  };

  return (
    <main className="mx-auto flex min-h-screen-dvh w-full max-w-md flex-col justify-center px-6 py-12">
      <header className="mb-10">
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">F2 Admin</p>
        <h1 className="mt-1 font-serif text-3xl font-medium tracking-tight">Change password</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {passwordMustChange
            ? 'Your account requires a password change before continuing.'
            : 'Rotate your admin password.'}
        </p>
      </header>

      <form onSubmit={onSubmit} className="flex flex-col gap-6" noValidate>
        <Field label="Current password" htmlFor="current_password">
          <input
            id="current_password"
            type="password"
            name="current_password"
            autoComplete="current-password"
            required
            value={currentPw}
            onChange={(e) => setCurrentPw(e.target.value)}
            className="border-0 border-b border-hairline bg-transparent py-2 font-mono text-base outline-none focus:border-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal focus:ring-0"
          />
        </Field>

        <Field
          label="New password"
          htmlFor="new_password"
          hint={`Minimum ${NEW_PASSWORD_MIN} characters. Must differ from current.`}
        >
          <input
            id="new_password"
            type="password"
            name="new_password"
            autoComplete="new-password"
            required
            minLength={NEW_PASSWORD_MIN}
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            className="border-0 border-b border-hairline bg-transparent py-2 font-mono text-base outline-none focus:border-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal focus:ring-0"
          />
        </Field>

        <Field label="Confirm new password" htmlFor="confirm_password">
          <input
            id="confirm_password"
            type="password"
            name="confirm_password"
            autoComplete="new-password"
            required
            minLength={NEW_PASSWORD_MIN}
            value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)}
            className="border-0 border-b border-hairline bg-transparent py-2 font-mono text-base outline-none focus:border-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal focus:ring-0"
          />
        </Field>

        {error ? (
          <div role="alert" className="border-l-2 border-error pl-3 py-2">
            <p className="text-sm text-error">{error}</p>
          </div>
        ) : null}

        <Button type="submit" disabled={submitting || !currentPw || !newPw || !confirmPw}>
          {submitting ? 'Saving…' : 'Update password'}
        </Button>

        {/* #328: this page renders chrome-less (no sidebar). When the user
            arrived here voluntarily (via the sidebar username link, not the
            forced first-login redirect) they need an escape hatch — otherwise
            the only way off the page is submitting a password change. Hidden
            under password_must_change: a forced rotation has no opt-out. */}
        {!passwordMustChange ? (
          <Link
            to="/admin/data"
            className="self-start font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
          >
            Cancel — back to portal
          </Link>
        ) : null}
      </form>

      <footer className="mt-16 border-t border-hairline pt-4">
        <p className="font-mono text-xs leading-relaxed text-muted-foreground">
          Your active session will continue with the new credential. No re-login required.
        </p>
      </footer>
    </main>
  );
}

function Field({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <label htmlFor={htmlFor} className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      {children}
      {hint ? <span className="font-mono text-[10px] text-muted-foreground">{hint}</span> : null}
    </label>
  );
}

function messageFor(error: ApiError): string {
  if (error.code === 'E_VALIDATION') return error.message ?? 'Some fields are invalid.';
  if (error.code === 'E_AUTH_INVALID') {
    if (error.message?.toLowerCase().includes('current_password')) {
      return 'Current password is incorrect.';
    }
    return 'Session expired. Sign in again.';
  }
  if (error.code === 'E_AUTH_EXPIRED') return 'Session expired. Sign in again.';
  if (error.code === 'E_NETWORK') return 'Network unavailable. Retry when reconnected.';
  if (error.code === 'E_BACKEND') return 'Backend unavailable — Apps Script may not be reachable.';
  return error.message ?? 'Failed to update password.';
}
