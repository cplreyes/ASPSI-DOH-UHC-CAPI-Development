/**
 * F2 Admin Portal — DLQ tab (Data dashboard).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.17)
 *
 * Dead-letter queue surfaces submission attempts that AS rejected as
 * malformed (per Handlers.js the dlq is appended when payload.values
 * isn't an object, etc). Operations folks scan this tab to spot
 * client-side bugs or schema drift between PWA bundles.
 */
import { useEffect, useMemo, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

interface DlqRow {
  dlq_id: string;
  received_at_server: string;
  client_submission_id: string;
  reason: string;
  payload_json: string;
}

interface ListDlqData {
  rows: DlqRow[];
  total: number;
  has_more: boolean;
}

export interface DLQTabProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

interface UiFilters {
  from: string;
  to: string;
  q: string;
}

function defaultFromIso(): string {
  return new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

function readFiltersFromUrl(): UiFilters {
  if (typeof window === 'undefined') {
    return { from: defaultFromIso(), to: '', q: '' };
  }
  const p = new URLSearchParams(window.location.search);
  return {
    from: p.get('from') ?? defaultFromIso(),
    to: p.get('to') ?? '',
    q: p.get('q') ?? '',
  };
}

function buildApiQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  if (f.from) p.set('from', f.from);
  if (f.to) p.set('to', f.to);
  if (f.q) p.set('q', f.q);
  p.set('limit', '200');
  return p.toString();
}

export function DLQTab({ apiBaseUrl, fetchImpl }: DLQTabProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [filters, setFilters] = useState<UiFilters>(() => readFiltersFromUrl());
  const [state, setState] = useState<
    | { kind: 'loading' }
    | { kind: 'loaded'; data: ListDlqData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });

  const apiQuery = useMemo(() => buildApiQuery(filters), [filters]);
  // R2-#84: bump on successful replay/delete to refetch the list.
  const [refreshKey, setRefreshKey] = useState(0);
  const [actionMsg, setActionMsg] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<ListDlqData>(
        `${apiBaseUrl}/admin/api/dashboards/data/dlq?${apiQuery}`,
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
  }, [apiQuery, apiBaseUrl, token, refreshKey]);

  // R2-#84: Replay re-attempts the submit through the AS handleSubmit
  // path. If the underlying validation issue has been fixed (e.g., the
  // PWA bundle was patched and the original payload is now valid), the
  // row moves to F2_Responses and the DLQ entry is deleted server-side.
  // If replay still fails, the DLQ row stays put and we surface the
  // error in actionMsg so operators can inspect.
  const handleReplay = async (dlqId: string) => {
    setBusyId(dlqId);
    setActionMsg(null);
    const r = await adminFetch<{ submission_id: string | null; status: string; dlq_id: string }>(
      `${apiBaseUrl}/admin/api/dashboards/data/dlq/${encodeURIComponent(dlqId)}/replay`,
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
    setBusyId(null);
    if (r.ok) {
      setActionMsg({ kind: 'ok', text: `Replayed ${dlqId.slice(0, 8)}… → ${r.data.submission_id ?? '(no id)'}` });
      setRefreshKey((k) => k + 1);
    } else {
      setActionMsg({ kind: 'err', text: `Replay failed: ${r.error.message ?? r.error.code}` });
    }
  };

  // R2-#84: Hard-delete a DLQ row after operator confirmation. Used when
  // the source data is unrecoverable or the row is genuinely stale.
  const handleDelete = async (dlqId: string) => {
    if (typeof window !== 'undefined' && !window.confirm(`Delete DLQ row ${dlqId}? This is irreversible.`)) return;
    setBusyId(dlqId);
    setActionMsg(null);
    const r = await adminFetch<{ dlq_id: string; status: string }>(
      `${apiBaseUrl}/admin/api/dashboards/data/dlq/${encodeURIComponent(dlqId)}`,
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
    setBusyId(null);
    if (r.ok) {
      setActionMsg({ kind: 'ok', text: `Deleted ${dlqId.slice(0, 8)}…` });
      setRefreshKey((k) => k + 1);
    } else {
      setActionMsg({ kind: 'err', text: `Delete failed: ${r.error.message ?? r.error.code}` });
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 border-b border-hairline pb-3">
        <FilterDate label="From" value={filters.from} onChange={(v) => setFilters({ ...filters, from: v })} />
        <FilterDate label="To" value={filters.to} onChange={(v) => setFilters({ ...filters, to: v })} />
        <FilterText label="Search" value={filters.q} onChange={(v) => setFilters({ ...filters, q: v })} />
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
            {state.data.total} dead-letter row{state.data.total === 1 ? '' : 's'}
            {state.data.has_more ? ' (showing first 200)' : ''}
          </p>
          {actionMsg ? (
            <p
              className={`font-mono text-xs ${actionMsg.kind === 'ok' ? 'text-primary' : 'text-error'}`}
              role="status"
            >
              {actionMsg.text}
            </p>
          ) : null}
          <DlqTable rows={state.data.rows} busyId={busyId} onReplay={handleReplay} onDelete={handleDelete} />
        </>
      ) : null}
    </div>
  );
}

function FilterDate({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
      />
    </label>
  );
}

function FilterText({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
      />
    </label>
  );
}

interface DlqTableProps {
  rows: DlqRow[];
  busyId: string | null;
  onReplay: (dlqId: string) => void;
  onDelete: (dlqId: string) => void;
}

function DlqTable({ rows, busyId, onReplay, onDelete }: DlqTableProps): JSX.Element {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>Received</Th>
            <Th>Client ID</Th>
            <Th>Reason</Th>
            <Th>Payload</Th>
            <Th>Actions</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((r) => {
            const busy = busyId === r.dlq_id;
            return (
              <tr key={r.dlq_id}>
                <Td mono>{formatTs(r.received_at_server)}</Td>
                <Td mono>{r.client_submission_id}</Td>
                <Td>
                  <span className="text-error">{r.reason}</span>
                </Td>
                <Td>
                  <code className="block max-w-md truncate font-mono text-xs text-muted-foreground">
                    {r.payload_json}
                  </code>
                </Td>
                <Td>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      className="rounded border border-hairline px-2 py-1 font-mono text-xs uppercase tracking-wider text-foreground transition-colors hover:bg-muted disabled:opacity-50"
                      disabled={busy}
                      onClick={() => onReplay(r.dlq_id)}
                      aria-label={`Replay DLQ row ${r.dlq_id}`}
                    >
                      {busy ? '…' : 'Replay'}
                    </button>
                    <button
                      type="button"
                      className="rounded border border-hairline px-2 py-1 font-mono text-xs uppercase tracking-wider text-foreground transition-colors hover:bg-muted disabled:opacity-50"
                      disabled={busy || !r.payload_json}
                      onClick={() => downloadPayload(`dlq-${r.dlq_id}.json`, r.payload_json)}
                      aria-label={`Download DLQ payload ${r.dlq_id}`}
                    >
                      Download
                    </button>
                    <button
                      type="button"
                      className="rounded border border-hairline px-2 py-1 font-mono text-xs uppercase tracking-wider text-error transition-colors hover:bg-error/10 disabled:opacity-50"
                      disabled={busy}
                      onClick={() => onDelete(r.dlq_id)}
                      aria-label={`Delete DLQ row ${r.dlq_id}`}
                    >
                      {busy ? '…' : 'Delete'}
                    </button>
                  </div>
                </Td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// R2-#102 sub-bug 3: emit the row's payload_json as a downloadable .json
// file. Pretty-printed if the value parses; otherwise falls back to the
// raw string.
function downloadPayload(filename: string, payloadJson: string): void {
  if (typeof window === 'undefined') return;
  let body = payloadJson;
  try {
    body = JSON.stringify(JSON.parse(payloadJson), null, 2);
  } catch {
    /* keep raw — admin still gets the source string */
  }
  const blob = new Blob([body], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function Th({ children }: { children?: React.ReactNode }): JSX.Element {
  return (
    <th className="px-3 py-2 font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
      {children}
    </th>
  );
}

function Td({ children, mono = false }: { children?: React.ReactNode; mono?: boolean }): JSX.Element {
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
      <p className="font-serif text-lg">No dead-letter rows in this window.</p>
      <p className="mt-1 text-sm text-muted-foreground">
        That&rsquo;s good — every PWA submission accepted by the server made it to F2_Responses.
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
              : (error.message ?? 'Failed to load DLQ.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
