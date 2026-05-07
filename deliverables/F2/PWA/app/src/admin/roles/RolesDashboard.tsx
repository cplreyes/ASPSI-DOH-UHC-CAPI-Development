/**
 * F2 Admin Portal — Roles dashboard (matrix view).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.24)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§8)
 *
 * Renders the perm matrix as a table: roles down the left, permissions
 * across the top. Built-in roles are pinned first. Edit (RoleEditor)
 * and create/delete actions land in follow-up commits; this is the
 * read-only matrix view.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';
import { RoleEditor } from './RoleEditor';

interface RoleRow {
  name: string;
  is_builtin?: boolean | string;
  version: number;
  [perm: string]: unknown;
}

interface ListRolesData {
  roles: RoleRow[];
  total: number;
}

const PERM_COLUMNS: Array<{ key: string; label: string; group: 'dash' | 'dict' }> = [
  { key: 'dash_data', label: 'Data', group: 'dash' },
  { key: 'dash_report', label: 'Report', group: 'dash' },
  { key: 'dash_apps', label: 'Apps', group: 'dash' },
  { key: 'dash_users', label: 'Users', group: 'dash' },
  { key: 'dash_roles', label: 'Roles', group: 'dash' },
  { key: 'dict_self_admin_up', label: 'Self ↑', group: 'dict' },
  { key: 'dict_self_admin_down', label: 'Self ↓', group: 'dict' },
  { key: 'dict_paper_encoded_up', label: 'Paper ↑', group: 'dict' },
  { key: 'dict_paper_encoded_down', label: 'Paper ↓', group: 'dict' },
  { key: 'dict_capi_up', label: 'CAPI ↑', group: 'dict' },
  { key: 'dict_capi_down', label: 'CAPI ↓', group: 'dict' },
];

export interface RolesDashboardProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

export function RolesDashboard({ apiBaseUrl, fetchImpl }: RolesDashboardProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [state, setState] = useState<
    | { kind: 'loading' }
    | { kind: 'loaded'; data: ListRolesData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });
  const [editor, setEditor] = useState<{ kind: 'create' } | { kind: 'edit'; role: RoleRow } | null>(
    null,
  );
  const [reloadTick, setReloadTick] = useState(0);

  const load = useCallback(async () => {
    return adminFetch<ListRolesData>(
      `${apiBaseUrl}/admin/api/dashboards/roles`,
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
  }, [apiBaseUrl, token, fetchImpl, clearAuth, navigate]);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await load();
      if (cancelled) return;
      if (r.ok) setState({ kind: 'loaded', data: r.data });
      else setState({ kind: 'failed', error: r.error });
    })();
    return () => {
      cancelled = true;
    };
  }, [load, reloadTick]);

  const onDelete = async (name: string) => {
    if (!window.confirm(`Delete role "${name}"? This cannot be undone.`)) return;
    const r = await adminFetch(
      `${apiBaseUrl}/admin/api/dashboards/roles/${encodeURIComponent(name)}`,
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
    } else if (r.error.code === 'E_CONFLICT') {
      window.alert('Cannot delete: this role is still assigned to one or more users.');
    } else {
      window.alert(`Delete failed: ${r.error.message ?? r.error.code}`);
    }
  };

  return (
    <section className="flex flex-col gap-4 py-2">
      <header className="flex items-start justify-between border-b border-hairline pb-3">
        <div>
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Section
          </p>
          <h2 className="mt-1 font-serif text-2xl font-medium tracking-tight">Roles</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Permission matrix. Built-in roles pinned first. Saving an edit auto-bumps version and
            forces affected users to re-login.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setEditor({ kind: 'create' })}
          className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          + Add role
        </button>
      </header>

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : state.kind === 'failed' ? (
        <ErrorBanner error={state.error} />
      ) : state.kind === 'loaded' && state.data.roles.length === 0 ? (
        <EmptyBanner />
      ) : state.kind === 'loaded' ? (
        <>
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            {state.data.total} role{state.data.total === 1 ? '' : 's'}
          </p>
          <RoleMatrix
            roles={state.data.roles}
            onEdit={(r) => setEditor({ kind: 'edit', role: r })}
            onDelete={onDelete}
          />
        </>
      ) : null}

      {editor ? (
        <RoleEditor
          apiBaseUrl={apiBaseUrl}
          {...(fetchImpl ? { fetchImpl } : {})}
          mode={editor.kind}
          {...(editor.kind === 'edit' ? { initial: editor.role } : {})}
          onClose={() => setEditor(null)}
          onSaved={() => setReloadTick((n) => n + 1)}
        />
      ) : null}
    </section>
  );
}

function RoleMatrix({
  roles,
  onEdit,
  onDelete,
}: {
  roles: RoleRow[];
  onEdit: (r: RoleRow) => void;
  onDelete: (name: string) => void;
}): JSX.Element {
  const dashCols = useMemo(() => PERM_COLUMNS.filter((c) => c.group === 'dash'), []);
  const dictCols = useMemo(() => PERM_COLUMNS.filter((c) => c.group === 'dict'), []);

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-hairline">
            <th className="px-3 py-2 text-left font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Role
            </th>
            <th className="px-3 py-2 text-left font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Version
            </th>
            <th
              colSpan={dashCols.length}
              className="border-l border-hairline px-3 py-2 text-left font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground"
            >
              Dashboards
            </th>
            <th
              colSpan={dictCols.length}
              className="border-l border-hairline px-3 py-2 text-left font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground"
            >
              Instrument access (↑ write / ↓ read)
            </th>
            <th className="border-l border-hairline px-3 py-2 text-left font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Actions
            </th>
          </tr>
          <tr className="border-b border-hairline">
            <th />
            <th />
            {dashCols.map((c, i) => (
              <th
                key={c.key}
                className={`px-2 py-1 text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground ${i === 0 ? 'border-l border-hairline' : ''}`}
              >
                {c.label}
              </th>
            ))}
            {dictCols.map((c, i) => (
              <th
                key={c.key}
                className={`px-2 py-1 text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground ${i === 0 ? 'border-l border-hairline' : ''}`}
              >
                {c.label}
              </th>
            ))}
            <th className="border-l border-hairline" />
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {roles.map((r) => {
            const builtin = isTruthy(r.is_builtin);
            return (
              <tr key={r.name}>
                <td className="px-3 py-2">
                  <span className="font-mono text-xs">{r.name}</span>
                  {builtin ? (
                    <span className="ml-2 rounded-full border border-hairline px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                      built-in
                    </span>
                  ) : null}
                </td>
                <td className="px-3 py-2 font-mono text-xs text-muted-foreground">v{r.version}</td>
                {dashCols.map((c, i) => (
                  <td
                    key={c.key}
                    className={`px-2 py-2 text-center ${i === 0 ? 'border-l border-hairline' : ''}`}
                  >
                    <PermDot active={isTruthy(r[c.key])} />
                  </td>
                ))}
                {dictCols.map((c, i) => (
                  <td
                    key={c.key}
                    className={`px-2 py-2 text-center ${i === 0 ? 'border-l border-hairline' : ''}`}
                  >
                    <PermDot active={isTruthy(r[c.key])} />
                  </td>
                ))}
                <td className="border-l border-hairline px-3 py-2">
                  <div className="flex flex-wrap gap-3">
                    <button
                      type="button"
                      onClick={() => onEdit(r)}
                      className="font-mono text-xs uppercase tracking-wider text-muted-foreground underline-offset-4 hover:text-ink hover:underline"
                    >
                      Edit
                    </button>
                    {builtin ? (
                      <span
                        className="font-mono text-xs uppercase tracking-wider text-muted-foreground/50"
                        title="Built-in roles cannot be deleted"
                      >
                        Delete
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => onDelete(r.name)}
                        className="font-mono text-xs uppercase tracking-wider text-error underline-offset-4 hover:underline"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function PermDot({ active }: { active: boolean }): JSX.Element {
  if (active) {
    return (
      <span
        aria-label="granted"
        title="granted"
        className="inline-block h-2 w-2 rounded-full bg-signal"
      />
    );
  }
  return (
    <span
      aria-label="denied"
      title="denied"
      className="inline-block h-2 w-2 rounded-full border border-hairline"
    />
  );
}

function isTruthy(v: unknown): boolean {
  if (typeof v === 'boolean') return v;
  if (typeof v === 'string') {
    const s = v.trim().toLowerCase();
    return s === 'true' || s === '1' || s === 'yes';
  }
  return false;
}

function EmptyBanner(): JSX.Element {
  return (
    <div className="border border-hairline bg-secondary/20 px-4 py-6">
      <p className="font-serif text-lg">No roles defined yet.</p>
      <p className="mt-1 text-sm text-muted-foreground">
        Run <code className="font-mono text-xs">scripts/seed-roles.mjs</code> after AP0 to seed
        Administrator + Standard User (Task 1.13).
      </p>
    </div>
  );
}

function ErrorBanner({ error }: { error: ApiError }): JSX.Element {
  return (
    <div role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2">
      <p className="text-sm text-error">
        {error.code === 'E_PERM_DENIED'
          ? 'Your role lacks dash_roles. Contact an Administrator.'
          : error.code === 'E_BACKEND'
            ? 'Backend unavailable — Apps Script staging may not be reachable yet.'
            : error.code === 'E_NETWORK'
              ? 'Network unavailable. Reload to retry.'
              : (error.message ?? 'Failed to load roles.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
