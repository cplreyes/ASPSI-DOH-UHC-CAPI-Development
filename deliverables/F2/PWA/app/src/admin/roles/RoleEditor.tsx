/**
 * F2 Admin Portal — RoleEditor modal.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.24)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.12, §6.4.1)
 *
 * Single component handles create + edit. Built-in roles can be edited
 * (perms can be tweaked) but not renamed; the name field is locked in
 * edit mode regardless of is_builtin.
 *
 * Important: a successful update auto-bumps role.version on the AS side.
 * Any user currently authenticated with the prior role_version will fail
 * RBAC on their next request and be bounced to /admin/login. The modal's
 * footer makes this consequence explicit so admins don't accidentally
 * sign themselves out of an in-flight session.
 */
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

interface RoleRow {
  name: string;
  is_builtin?: boolean | string;
  version: number;
  [perm: string]: unknown;
}

const PERM_GROUPS: Array<{ label: string; perms: Array<{ key: string; label: string }> }> = [
  {
    label: 'Dashboards',
    perms: [
      { key: 'dash_data', label: 'Data' },
      { key: 'dash_report', label: 'Report' },
      { key: 'dash_apps', label: 'Apps & Settings' },
      { key: 'dash_users', label: 'Users' },
      { key: 'dash_roles', label: 'Roles' },
    ],
  },
  {
    label: 'Self-administered (PWA)',
    perms: [
      { key: 'dict_self_admin_up', label: 'Submit ↑' },
      { key: 'dict_self_admin_down', label: 'Read ↓' },
    ],
  },
  {
    label: 'Paper-encoded',
    perms: [
      { key: 'dict_paper_encoded_up', label: 'Submit ↑' },
      { key: 'dict_paper_encoded_down', label: 'Read ↓' },
    ],
  },
  {
    label: 'CAPI',
    perms: [
      { key: 'dict_capi_up', label: 'Submit ↑' },
      { key: 'dict_capi_down', label: 'Read ↓' },
    ],
  },
];

const ROLE_NAME_RE = /^[A-Za-z][A-Za-z0-9 _-]{0,63}$/;

export interface RoleEditorProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
  mode: 'create' | 'edit';
  initial?: RoleRow;
  onClose: () => void;
  onSaved: (role: RoleRow) => void;
}

function isTruthy(v: unknown): boolean {
  if (typeof v === 'boolean') return v;
  if (typeof v === 'string') {
    const s = v.trim().toLowerCase();
    return s === 'true' || s === '1' || s === 'yes';
  }
  return false;
}

export function RoleEditor(props: RoleEditorProps): JSX.Element {
  const { apiBaseUrl, fetchImpl, mode, initial, onClose, onSaved } = props;
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();

  const [name, setName] = useState(initial?.name ?? '');
  const [perms, setPerms] = useState<Record<string, boolean>>(() => {
    const out: Record<string, boolean> = {};
    for (const group of PERM_GROUPS) {
      for (const p of group.perms) {
        out[p.key] = isTruthy(initial?.[p.key]);
      }
    }
    return out;
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
    if (mode === 'create' && !ROLE_NAME_RE.test(name)) {
      setError({
        code: 'E_VALIDATION',
        message: 'Role name must start with a letter; up to 64 chars.',
      });
      return;
    }
    if (!Object.values(perms).some(Boolean)) {
      setError({ code: 'E_VALIDATION', message: 'At least one permission must be granted.' });
      return;
    }
    setError(null);
    setSubmitting(true);

    const url =
      mode === 'create'
        ? `${apiBaseUrl}/admin/api/dashboards/roles`
        : `${apiBaseUrl}/admin/api/dashboards/roles/${encodeURIComponent(name)}`;

    const body: Record<string, unknown> = { ...perms };
    if (mode === 'create') body.name = name;

    const r = await adminFetch<{ role: RoleRow }>(
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
    onSaved(r.data.role);
    onClose();
  };

  const togglePerm = (key: string) => {
    setPerms((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={mode === 'create' ? 'Create role' : `Edit role ${name}`}
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/70 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-xl border border-hairline bg-paper p-6">
        <header className="border-b border-hairline pb-3">
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            {mode === 'create' ? 'New role' : 'Edit role'}
          </p>
          <h3 className="mt-1 font-serif text-xl font-medium tracking-tight">
            {mode === 'create' ? 'Create permission set' : initial?.name}
          </h3>
          {mode === 'edit' ? (
            <p className="mt-1 font-mono text-[10px] text-muted-foreground">
              v{initial?.version} · saving auto-bumps version → users with this role re-login on
              next request
            </p>
          ) : null}
        </header>

        <form onSubmit={onSubmit} className="mt-4 flex flex-col gap-4">
          {mode === 'create' ? (
            <Field label="Name" hint="Starts with a letter; up to 64 chars [A-Za-z0-9 _-]">
              <input
                ref={firstFieldRef}
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
              />
            </Field>
          ) : null}

          {PERM_GROUPS.map((group, i) => (
            <fieldset key={group.label} className={i === 0 ? '' : 'border-t border-hairline pt-3'}>
              <legend className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                {group.label}
              </legend>
              <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3">
                {group.perms.map((p) => (
                  <label key={p.key} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={!!perms[p.key]}
                      onChange={() => togglePerm(p.key)}
                      className="h-4 w-4 accent-signal"
                    />
                    <span>{p.label}</span>
                    <span className="font-mono text-[10px] text-muted-foreground">{p.key}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          ))}

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
              {submitting ? 'Saving…' : mode === 'create' ? 'Create role' : 'Save & bump version'}
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
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
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
  if (error.code === 'E_CONFLICT')
    return error.message?.includes('users')
      ? 'Cannot delete: this role is still assigned to one or more users.'
      : 'A role with that name already exists.';
  if (error.code === 'E_NOT_FOUND') return 'That role no longer exists. Refresh the list.';
  if (error.code === 'E_PERM_DENIED') return 'Your role lacks dash_roles.';
  if (error.code === 'E_NETWORK') return 'Network unavailable. Retry when reconnected.';
  if (error.code === 'E_BACKEND') return 'Backend unavailable — Apps Script may not be reachable.';
  return error.message ?? 'Failed to save role.';
}
