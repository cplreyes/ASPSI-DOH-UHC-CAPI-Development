/**
 * F2 Admin Portal — Versioning panel.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.6)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§9.4)
 *
 * Top: PWA + Worker build identifiers (worker reads from env at deploy
 * time). Below: form_revisions table aggregating F2_Responses by
 * spec_version so admins can see how many submissions land on each
 * questionnaire revision and when the most recent one arrived.
 */
import { useEffect, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

interface FormRevision {
  spec_version: string;
  count: number;
  last_seen_at: string;
}

interface VersionData {
  pwa_version: string;
  pwa_build_sha: string;
  worker_version: string;
  form_revisions: FormRevision[];
  total_submissions: number;
  last_pages_deploy_at: string | null;
}

export interface VersioningProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

export function Versioning({ apiBaseUrl, fetchImpl }: VersioningProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [state, setState] = useState<
    | { kind: 'loading' }
    | { kind: 'loaded'; data: VersionData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<VersionData>(
        `${apiBaseUrl}/admin/api/dashboards/apps/version`,
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
  }, [apiBaseUrl, token]);

  return (
    <section className="flex flex-col gap-3">
      <h3 className="font-serif text-lg font-medium tracking-tight">Versioning</h3>

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : state.kind === 'failed' ? (
        <ErrorBanner error={state.error} />
      ) : (
        <>
          <BuildIdentifiers data={state.data} />
          <RevisionsTable rows={state.data.form_revisions} total={state.data.total_submissions} />
        </>
      )}
    </section>
  );
}

function BuildIdentifiers({ data }: { data: VersionData }): JSX.Element {
  return (
    <dl className="grid grid-cols-1 gap-y-2 border-l-2 border-hairline pl-4 sm:grid-cols-2 sm:gap-x-6">
      <Field label="PWA version" mono>{data.pwa_version}</Field>
      <Field label="PWA build SHA" mono>{shortSha(data.pwa_build_sha)}</Field>
      <Field label="Worker version" mono>{data.worker_version}</Field>
      <Field label="Last Pages deploy" mono>{data.last_pages_deploy_at ?? '—'}</Field>
    </dl>
  );
}

function RevisionsTable({ rows, total }: { rows: FormRevision[]; total: number }): JSX.Element {
  if (rows.length === 0) {
    return (
      <div className="border border-hairline bg-secondary/20 px-4 py-4">
        <p className="text-sm text-muted-foreground">
          No submissions on record yet. Once F2 responses start landing, this table groups them by
          questionnaire <code className="font-mono text-xs">spec_version</code>.
        </p>
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {total} submission{total === 1 ? '' : 's'} across {rows.length} revision
        {rows.length === 1 ? '' : 's'}
      </p>
      <table className="mt-2 w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>Spec version</Th>
            <Th>Submissions</Th>
            <Th>Last seen</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((r) => (
            <tr key={r.spec_version}>
              <Td mono>{r.spec_version}</Td>
              <Td mono>{r.count}</Td>
              <Td mono>{formatTs(r.last_seen_at)}</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Field({ label, children, mono = false }: { label: string; children: React.ReactNode; mono?: boolean }): JSX.Element {
  return (
    <div className="flex flex-col">
      <dt className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</dt>
      <dd className={mono ? 'font-mono text-xs' : ''}>{children}</dd>
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

function Td({ children, mono = false }: { children?: React.ReactNode; mono?: boolean }): JSX.Element {
  return <td className={`px-3 py-2 align-top ${mono ? 'font-mono text-xs' : ''}`}>{children}</td>;
}

function shortSha(sha: string): string {
  if (!sha || sha === 'unknown') return sha;
  return sha.length > 8 ? sha.slice(0, 8) : sha;
}

function formatTs(iso: string): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function ErrorBanner({ error }: { error: ApiError }): JSX.Element {
  return (
    <div role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2">
      <p className="text-sm text-error">
        {error.code === 'E_PERM_DENIED'
          ? 'Your role lacks dash_apps. Contact an Administrator.'
          : error.code === 'E_BACKEND'
            ? 'Backend unavailable — Apps Script staging may not be reachable yet.'
            : error.code === 'E_NETWORK'
              ? 'Network unavailable. Reload to retry.'
              : (error.message ?? 'Failed to load versioning info.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
