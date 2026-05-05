/**
 * F2 Admin Portal — UserEditor modal.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.19)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.10)
 *
 * Single component handles both create and edit. In create mode the
 * password field is required and the new account is automatically
 * marked password_must_change=true (worker handles); in edit mode the
 * password field is optional and only sets a new password when typed.
 *
 * Renders as a centered overlay with a hairline-bordered card. Closes
 * on backdrop click, Escape, or Cancel. Submits via POST or PATCH to
 * the worker; on success calls onSaved(updatedUser) so the parent can
 * refresh the list.
 */
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

interface UserRow {
  username: string;
  first_name: string;
  last_name: string;
  role_name: string;
  email?: string;
  phone?: string;
  password_must_change?: boolean | string;
}

interface RoleRow {
  name: string;
}

export interface UserEditorProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
  mode: 'create' | 'edit';
  initial?: UserRow;
  roles: RoleRow[];
  onClose: () => void;
  onSaved: (user: UserRow) => void;
}

export function UserEditor(props: UserEditorProps): JSX.Element {
  const { apiBaseUrl, fetchImpl, mode, initial, roles, onClose, onSaved } = props;
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();

  const [form, setForm] = useState({
    username: initial?.username ?? '',
    first_name: initial?.first_name ?? '',
    last_name: initial?.last_name ?? '',
    role_name: initial?.role_name ?? roles[0]?.name ?? '',
    email: initial?.email ?? '',
    phone: initial?.phone ?? '',
    password: '',
  });
  const [error, setError] = useState<ApiError | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const firstFieldRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    firstFieldRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitting(true);

    const url =
      mode === 'create'
        ? `${apiBaseUrl}/admin/api/dashboards/users`
        : `${apiBaseUrl}/admin/api/dashboards/users/${encodeURIComponent(form.username)}`;

    const body: Record<string, unknown> = {
      first_name: form.first_name,
      last_name: form.last_name,
      role_name: form.role_name,
      email: form.email,
      phone: form.phone,
    };
    if (mode === 'create') body.username = form.username;
    if (form.password) body.password = form.password;

    const r = await adminFetch<{ user: UserRow }>(
      url,
      { method: mode === 'create' ? 'POST' : 'PATCH', body: JSON.stringify(body) },
      {
        ...(token ? { token } : {}),
        onUnauthorized: () => {
          clearAuth();
          navigate('/admin/login');
        },
        ...(fetchImpl ? { fetchImpl } : {}),
      },
    );
    setSubmitting(false);

    if (!r.ok) {
      setError(r.error);
      return;
    }
    onSaved(r.data.user);
    onClose();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={mode === 'create' ? 'Create user' : `Edit user ${form.username}`}
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/70 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-md border border-hairline bg-paper p-6">
        <header className="border-b border-hairline pb-3">
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            {mode === 'create' ? 'New user' : 'Edit user'}
          </p>
          <h3 className="mt-1 font-serif text-xl font-medium tracking-tight">
            {mode === 'create' ? 'Create admin account' : form.username}
          </h3>
        </header>

        <form onSubmit={onSubmit} className="mt-4 flex flex-col gap-4">
          {mode === 'create' ? (
            <Field label="Username" hint="3–32 chars; letters, numbers, underscore">
              <input
                ref={firstFieldRef}
                type="text"
                required
                autoCapitalize="none"
                autoCorrect="off"
                spellCheck={false}
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
              />
            </Field>
          ) : null}

          <div className="flex gap-3">
            <Field label="First name" className="flex-1">
              <input
                ref={mode === 'edit' ? firstFieldRef : undefined}
                type="text"
                value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
              />
            </Field>
            <Field label="Last name" className="flex-1">
              <input
                type="text"
                value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
              />
            </Field>
          </div>

          <Field label="Role">
            <select
              value={form.role_name}
              onChange={(e) => setForm({ ...form, role_name: e.target.value })}
              className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
            >
              {roles.map((r) => (
                <option key={r.name} value={r.name}>
                  {r.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Email">
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
            />
          </Field>

          <Field label="Phone">
            <input
              type="tel"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
            />
          </Field>

          <Field
            label={mode === 'create' ? 'Initial password' : 'Reset password'}
            hint={
              mode === 'create'
                ? 'Min 8 chars. User will be forced to change on first login.'
                : 'Leave blank to keep current. New password forces password_must_change.'
            }
          >
            <input
              type="password"
              required={mode === 'create'}
              minLength={mode === 'create' ? 8 : 0}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
            />
          </Field>

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

          <div className="mt-2 flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground"
            >
              {submitting ? 'Saving…' : mode === 'create' ? 'Create user' : 'Save changes'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="inline-flex h-10 items-center justify-center rounded-md border border-hairline px-4 text-sm hover:bg-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({
  label,
  hint,
  children,
  className,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
  className?: string;
}): JSX.Element {
  return (
    <label className={`flex flex-col gap-1 ${className ?? ''}`}>
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      {children}
      {hint ? <span className="font-mono text-[10px] text-muted-foreground">{hint}</span> : null}
    </label>
  );
}

function errorMessageFor(error: ApiError): string {
  if (error.code === 'E_VALIDATION') return error.message ?? 'Some fields are invalid.';
  if (error.code === 'E_CONFLICT') return 'A user with that username already exists.';
  if (error.code === 'E_NOT_FOUND') return 'That user no longer exists. Refresh the list.';
  if (error.code === 'E_PERM_DENIED') return 'Your role lacks dash_users.';
  if (error.code === 'E_NETWORK') return 'Network unavailable. Retry when reconnected.';
  if (error.code === 'E_BACKEND') return 'Backend unavailable — Apps Script may not be reachable.';
  return error.message ?? 'Failed to save user.';
}
