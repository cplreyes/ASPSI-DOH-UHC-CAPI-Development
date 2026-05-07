/**
 * F2 Admin Portal — Audit tab (Data dashboard).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.16)
 *
 * Read-only audit list. Filters by event_type, hcw_id, actor_username, q,
 * date range. event_payload_json is rendered as a tiny mono preview when
 * present so admins can scan event details without expanding each row.
 */
import { useEffect, useMemo, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

interface AuditRow {
  audit_id: string;
  occurred_at_server: string;
  event_type: string;
  hcw_id: string;
  facility_id: string;
  actor_username?: string;
  actor_role?: string;
  event_resource?: string;
  event_payload_json?: string;
  request_id?: string;
}

interface ListAuditData {
  rows: AuditRow[];
  total: number;
  has_more: boolean;
}

export interface AuditTabProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

interface UiFilters {
  from: string;
  to: string;
  event_type: string;
  actor_username: string;
  q: string;
}

// UAT R2 #82: cold load no longer auto-applies a 7d filter — testers read
// it as data loss because there was no visible indicator the list was being
// trimmed. Date pickers remain available; they're opt-in. Revisit once
// production audit volume justifies a default recency window.
function readFiltersFromUrl(): UiFilters {
  if (typeof window === 'undefined') {
    return { from: '', to: '', event_type: '', actor_username: '', q: '' };
  }
  const p = new URLSearchParams(window.location.search);
  return {
    from: p.get('from') ?? '',
    to: p.get('to') ?? '',
    event_type: p.get('event_type') ?? '',
    actor_username: p.get('actor_username') ?? '',
    q: p.get('q') ?? '',
  };
}

function buildApiQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  if (f.from) p.set('from', f.from);
  if (f.to) p.set('to', f.to);
  if (f.event_type) p.set('event_type', f.event_type);
  if (f.actor_username) p.set('actor_username', f.actor_username);
  if (f.q) p.set('q', f.q);
  p.set('limit', '200');
  return p.toString();
}

export function AuditTab({ apiBaseUrl, fetchImpl }: AuditTabProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [filters, setFilters] = useState<UiFilters>(() => readFiltersFromUrl());
  const [state, setState] = useState<
    | { kind: 'loading' }
    | { kind: 'loaded'; data: ListAuditData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });

  const apiQuery = useMemo(() => buildApiQuery(filters), [filters]);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<ListAuditData>(
        `${apiBaseUrl}/admin/api/dashboards/data/audit?${apiQuery}`,
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
      if (cancelled) return;
      if (r.ok) setState({ kind: 'loaded', data: r.data });
      else setState({ kind: 'failed', error: r.error });
    })();
    return () => {
      cancelled = true;
    };
  }, [apiQuery, apiBaseUrl, token]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 border-b border-hairline pb-3">
        <FilterDate
          label="From"
          value={filters.from}
          onChange={(v) => setFilters({ ...filters, from: v })}
        />
        <FilterDate
          label="To"
          value={filters.to}
          onChange={(v) => setFilters({ ...filters, to: v })}
        />
        <FilterText
          label="Event type"
          value={filters.event_type}
          onChange={(v) => setFilters({ ...filters, event_type: v })}
          placeholder="admin_login"
        />
        <FilterText
          label="Actor"
          value={filters.actor_username}
          onChange={(v) => setFilters({ ...filters, actor_username: v })}
        />
        <FilterText
          label="Search"
          value={filters.q}
          onChange={(v) => setFilters({ ...filters, q: v })}
        />
      </div>

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : state.kind === 'failed' ? (
        <ErrorBanner error={state.error} />
      ) : state.kind === 'loaded' && state.data.rows.length === 0 ? (
        <EmptyBanner />
      ) : state.kind === 'loaded' ? (
        <>
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            {state.data.total} event{state.data.total === 1 ? '' : 's'}
            {state.data.has_more ? ' (showing first 200 — refine filters to see more)' : ''}
          </p>
          <AuditTable rows={state.data.rows} />
        </>
      ) : null}
    </div>
  );
}

// FX-014 (2026-05-03): inputs derive `name` from the label so Chrome's
// "form field should have an id or name" issue panel stays clean.
function slugifyLabel(label: string): string {
  return (
    label
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '') || 'field'
  );
}

function FilterDate({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}): JSX.Element {
  const name = slugifyLabel(label);
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="date"
        name={name}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
      />
    </label>
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
  const name = slugifyLabel(label);
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="text"
        name={name}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
      />
    </label>
  );
}

function AuditTable({ rows }: { rows: AuditRow[] }): JSX.Element {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>When</Th>
            <Th>Event</Th>
            <Th>Actor</Th>
            <Th>Resource</Th>
            {/* UAT R2 #79: Request ID column was missing from the table even
                though the AuditRow shape carries request_id from the server. */}
            <Th>Request</Th>
            <Th>Detail</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((r) => (
            <tr key={r.audit_id}>
              <Td mono>{formatTs(r.occurred_at_server)}</Td>
              <Td mono>{r.event_type}</Td>
              <Td mono>{r.actor_username ?? r.hcw_id ?? '—'}</Td>
              <Td mono>{r.event_resource ?? '—'}</Td>
              <Td>
                {r.request_id ? (
                  <span
                    className="font-mono text-[10px] text-muted-foreground"
                    title={r.request_id}
                  >
                    {r.request_id.slice(0, 8)}…
                  </span>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </Td>
              <Td>
                {/* UAT R2 #80: native <details> gives an inline-expand affordance
                    so the full payload is one click away. Lighter than a modal
                    detail panel; still accessible (keyboard + screen reader). */}
                {r.event_payload_json ? (
                  <details className="group">
                    <summary className="cursor-pointer list-none">
                      <span className="block max-w-md truncate font-mono text-xs text-muted-foreground group-open:text-ink">
                        {r.event_payload_json}
                      </span>
                    </summary>
                    <pre className="mt-2 max-w-md overflow-x-auto rounded border border-hairline bg-secondary/20 p-2 font-mono text-[10px] text-ink">
                      {prettyJson(r.event_payload_json)}
                    </pre>
                  </details>
                ) : null}
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function prettyJson(raw: string): string {
  try {
    return JSON.stringify(JSON.parse(raw), null, 2);
  } catch {
    return raw;
  }
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

function formatTs(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function EmptyBanner(): JSX.Element {
  return (
    <div className="border border-hairline bg-secondary/20 px-4 py-6">
      <p className="font-serif text-lg">No audit events match the current filters.</p>
      <p className="mt-1 text-sm text-muted-foreground">
        Audit captures admin logins, logouts, role changes, and HCW token reissues. Widen the date
        range to see more.
      </p>
    </div>
  );
}

function ErrorBanner({ error }: { error: ApiError }): JSX.Element {
  return (
    <div role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2">
      <p className="text-sm text-error">
        {error.code === 'E_PERM_DENIED'
          ? 'Your role lacks dash_data. Contact an Administrator.'
          : error.code === 'E_BACKEND'
            ? 'Backend unavailable — Apps Script staging may not be reachable yet.'
            : error.code === 'E_NETWORK'
              ? 'Network unavailable. Reload to retry.'
              : (error.message ?? 'Failed to load audit log.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
