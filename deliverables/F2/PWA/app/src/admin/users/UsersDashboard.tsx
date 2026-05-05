/**
 * F2 Admin Portal — Users dashboard (list view).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.18)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.10–7.11)
 *
 * Read-only list. Single-user CRUD modal (Task 3.19), bulk import
 * (3.20), and revoke-sessions action all land in follow-up commits.
 * For now this just surfaces the F2_Users sheet so an Administrator
 * can confirm seeded accounts exist after AP0 + seed-admins.mjs run.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';
import { UserEditor } from './UserEditor';

interface UserRow {
  username: string;
  first_name: string;
  last_name: string;
  role_name: string;
  email?: string;
  phone?: string;
  password_must_change?: boolean | string;
  has_password?: boolean;
  created_at?: string;
  created_by?: string;
  last_login_at?: string;
}

interface ListUsersData {
  users: UserRow[];
  total: number;
}

interface RoleRow {
  name: string;
}
interface ListRolesData {
  roles: RoleRow[];
  total: number;
}

export interface UsersDashboardProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

interface UiFilters {
  q: string;
  role_name: string;
}

function readFiltersFromUrl(): UiFilters {
  if (typeof window === 'undefined') return { q: '', role_name: '' };
  const p = new URLSearchParams(window.location.search);
  return { q: p.get('q') ?? '', role_name: p.get('role_name') ?? '' };
}

function buildApiQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  if (f.q) p.set('q', f.q);
  if (f.role_name) p.set('role_name', f.role_name);
  return p.toString();
}

export function UsersDashboard({ apiBaseUrl, fetchImpl }: UsersDashboardProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [filters, setFilters] = useState<UiFilters>(() => readFiltersFromUrl());
  const [state, setState] = useState<
    | { kind: 'loading' }
    | { kind: 'loaded'; data: ListUsersData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [editor, setEditor] = useState<{ kind: 'create' } | { kind: 'edit'; user: UserRow } | null>(
    null,
  );
  const [reloadTick, setReloadTick] = useState(0);

  const apiQuery = useMemo(() => buildApiQuery(filters), [filters]);

  const loadUsers = useCallback(async () => {
    const r = await adminFetch<ListUsersData>(
      `${apiBaseUrl}/admin/api/dashboards/users${apiQuery ? `?${apiQuery}` : ''}`,
      {},
      {
        ...(token ? { token } : {}),
        onUnauthorized: () => {
          clearAuth();
          navigate('/admin/login');
        },
        ...(fetchImpl ? { fetchImpl } : {}),
      },
    );
    return r;
  }, [apiQuery, apiBaseUrl, token, clearAuth, navigate, fetchImpl]);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await loadUsers();
      if (cancelled) return;
      if (r.ok) setState({ kind: 'loaded', data: r.data });
      else setState({ kind: 'failed', error: r.error });
    })();
    return () => {
      cancelled = true;
    };
  }, [loadUsers, reloadTick]);

  // Roles list for the editor's role dropdown. Pulled once and cached.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const r = await adminFetch<ListRolesData>(
        `${apiBaseUrl}/admin/api/dashboards/roles`,
        {},
        {
          ...(token ? { token } : {}),
          ...(fetchImpl ? { fetchImpl } : {}),
        },
      );
      if (cancelled || !r.ok) return;
      setRoles(r.data.roles);
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, token, fetchImpl]);

  const onDelete = async (username: string) => {
    if (!window.confirm(`Delete user ${username}? This cannot be undone.`)) return;
    const r = await adminFetch(
      `${apiBaseUrl}/admin/api/dashboards/users/${encodeURIComponent(username)}`,
      { method: 'DELETE' },
      {
        ...(token ? { token } : {}),
        onUnauthorized: () => {
          clearAuth();
          navigate('/admin/login');
        },
        ...(fetchImpl ? { fetchImpl } : {}),
      },
    );
    if (r.ok) {
      setReloadTick((n) => n + 1);
    } else {
      window.alert(`Delete failed: ${r.error.message ?? r.error.code}`);
    }
  };

  const onRevoke = async (username: string) => {
    if (
      !window.confirm(
        `Force-logout ${username}? Every JWT they currently hold stops working on its next request. Lockout lasts 24 hours.`,
      )
    ) {
      return;
    }
    const r = await adminFetch(
      `${apiBaseUrl}/admin/api/dashboards/users/${encodeURIComponent(username)}/revoke-sessions`,
      { method: 'POST' },
      {
        ...(token ? { token } : {}),
        onUnauthorized: () => {
          clearAuth();
          navigate('/admin/login');
        },
        ...(fetchImpl ? { fetchImpl } : {}),
      },
    );
    if (r.ok) {
      window.alert(`${username}'s sessions revoked. They'll be bounced to login on next request.`);
    } else {
      window.alert(`Revoke failed: ${r.error.message ?? r.error.code}`);
    }
  };

  return (
    <section className="flex flex-col gap-4 py-2">
      <header className="flex items-start justify-between border-b border-hairline pb-3">
        <div>
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Section
          </p>
          <h2 className="mt-1 font-serif text-2xl font-medium tracking-tight">Users</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Admin portal accounts. Bulk-import + revoke-sessions actions land in follow-up commits.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setEditor({ kind: 'create' })}
          className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          + Add user
        </button>
      </header>

      <div className="flex flex-wrap items-end gap-3 border-b border-hairline pb-3">
        <FilterText
          label="Search"
          value={filters.q}
          onChange={(v) => setFilters({ ...filters, q: v })}
        />
        <FilterText
          label="Role"
          value={filters.role_name}
          onChange={(v) => setFilters({ ...filters, role_name: v })}
          placeholder="Administrator"
        />
      </div>

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : state.kind === 'failed' ? (
        <ErrorBanner error={state.error} />
      ) : state.kind === 'loaded' && state.data.users.length === 0 ? (
        <EmptyBanner />
      ) : state.kind === 'loaded' ? (
        <>
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            {state.data.total} user{state.data.total === 1 ? '' : 's'}
          </p>
          <UsersTable
            rows={state.data.users}
            onEdit={(u) => setEditor({ kind: 'edit', user: u })}
            onDelete={onDelete}
            onRevoke={onRevoke}
          />
        </>
      ) : null}

      {editor ? (
        <UserEditor
          apiBaseUrl={apiBaseUrl}
          {...(fetchImpl ? { fetchImpl } : {})}
          mode={editor.kind}
          {...(editor.kind === 'edit' ? { initial: editor.user } : {})}
          roles={roles}
          onClose={() => setEditor(null)}
          onSaved={() => setReloadTick((n) => n + 1)}
        />
      ) : null}
    </section>
  );
}

function FilterText({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
      />
    </label>
  );
}

function UsersTable({
  rows,
  onEdit,
  onDelete,
  onRevoke,
}: {
  rows: UserRow[];
  onEdit: (u: UserRow) => void;
  onDelete: (username: string) => void;
  onRevoke: (username: string) => void;
}): JSX.Element {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>Username</Th>
            <Th>Name</Th>
            <Th>Role</Th>
            <Th>Email</Th>
            <Th>Last login</Th>
            <Th>Created</Th>
            <Th aria-label="actions" />
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((u) => (
            <tr key={u.username}>
              <Td mono>
                {u.username}
                {isTruthy(u.password_must_change) ? (
                  <span className="ml-2 rounded-full border border-warning bg-warning/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-warning">
                    must reset
                  </span>
                ) : null}
              </Td>
              <Td>{[u.first_name, u.last_name].filter(Boolean).join(' ') || '—'}</Td>
              <Td mono>{u.role_name || '—'}</Td>
              <Td>{u.email || '—'}</Td>
              <Td mono>{formatTs(u.last_login_at)}</Td>
              <Td mono>{formatTs(u.created_at)}</Td>
              <Td>
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => onEdit(u)}
                    className="font-mono text-xs uppercase tracking-wider text-muted-foreground underline-offset-4 hover:text-ink hover:underline"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => onRevoke(u.username)}
                    className="font-mono text-xs uppercase tracking-wider text-warning underline-offset-4 hover:underline"
                    title="Force-logout every active session for this user"
                  >
                    Revoke
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(u.username)}
                    className="font-mono text-xs uppercase tracking-wider text-error underline-offset-4 hover:underline"
                  >
                    Delete
                  </button>
                </div>
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children?: React.ReactNode }): JSX.Element {
  return (
    <th className="px-3 py-2 font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
      {children}
    </th>
  );
}

function Td({
  children,
  mono = false,
}: {
  children?: React.ReactNode;
  mono?: boolean;
}): JSX.Element {
  return <td className={`px-3 py-2 align-top ${mono ? 'font-mono text-xs' : ''}`}>{children}</td>;
}

function isTruthy(v: unknown): boolean {
  if (typeof v === 'boolean') return v;
  if (typeof v === 'string') {
    const s = v.trim().toLowerCase();
    return s === 'true' || s === '1' || s === 'yes';
  }
  return false;
}

function formatTs(iso: string | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function EmptyBanner(): JSX.Element {
  return (
    <div className="border border-hairline bg-secondary/20 px-4 py-6">
      <p className="font-serif text-lg">No admin users yet.</p>
      <p className="mt-1 text-sm text-muted-foreground">
        Run <code className="font-mono text-xs">scripts/seed-admins.mjs</code> after AP0 to seed the
        initial Administrator accounts (Task 1.13).
      </p>
    </div>
  );
}

function ErrorBanner({ error }: { error: ApiError }): JSX.Element {
  return (
    <div role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2">
      <p className="text-sm text-error">
        {error.code === 'E_PERM_DENIED'
          ? 'Your role lacks dash_users. Contact an Administrator.'
          : error.code === 'E_BACKEND'
            ? 'Backend unavailable — Apps Script staging may not be reachable yet.'
            : error.code === 'E_NETWORK'
              ? 'Network unavailable. Reload to retry.'
              : (error.message ?? 'Failed to load users.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
