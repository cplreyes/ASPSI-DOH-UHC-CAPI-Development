/**
 * F2 Admin Portal — Versioning panel.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.6)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§9.4)
 *
 * Top: PWA + API build identifiers (f2-api reads them from container env
 * vars stamped by deploy_model_c_full.sh). Below: form_revisions table
 * aggregating F2_Responses by spec_version so admins can see how many
 * responses land on each questionnaire revision and when the most recent
 * one arrived.
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
  api_version: string;
  form_revisions: FormRevision[];
  total_submissions: number;
  api_deployed_at: string | null;
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
          onPasswordChangeRequired: () => navigate("/admin/me/change-password"),
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
  }, [apiBaseUrl, token, clearAuth, navigate, fetchImpl]);

  return (
    <section className="flex flex-col gap-3">
      <header className="flex flex-col">
        <h3 className="font-serif text-lg font-medium tracking-tight">Versioning</h3>
        <p className="text-xs text-muted-foreground">
          Live build identifiers (PWA bundle + SHA, API version, last deploy) and per-spec
          response counts. First place to look during incident triage — answers “what version is
          in front of users right now?”
        </p>
      </header>

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
      <Field label="PWA version" mono>
        {data.pwa_version}
      </Field>
      <Field label="PWA build SHA" mono>
        {shortSha(data.pwa_build_sha)}
      </Field>
      <Field label="API version" mono>
        {data.api_version}
      </Field>
      <Field label="Last API deploy" mono>
        {data.api_deployed_at ? formatTs(data.api_deployed_at) : '—'}
      </Field>
    </dl>
  );
}

function RevisionsTable({ rows, total }: { rows: FormRevision[]; total: number }): JSX.Element {
  if (rows.length === 0) {
    return (
      <div className="border border-hairline bg-secondary/20 px-4 py-4">
        <p className="text-sm text-muted-foreground">
          No responses on record yet. Once F2 responses start landing, this table groups them by
          questionnaire <code className="font-mono text-xs">spec_version</code>.
        </p>
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      {/* "Responses", not "submissions" — this count includes refusals, unlike
          the Coverage report's submitted column (audit P3-2). */}
      <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {total} response{total === 1 ? '' : 's'} (incl. refusals) across {rows.length} revision
        {rows.length === 1 ? '' : 's'}
      </p>
      <table className="mt-2 w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>Spec version</Th>
            <Th>Responses</Th>
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

function Field({
  label,
  children,
  mono = false,
}: {
  label: string;
  children: React.ReactNode;
  mono?: boolean;
}): JSX.Element {
  return (
    <div className="flex flex-col">
      <dt className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        {label}
      </dt>
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

function Td({
  children,
  mono = false,
}: {
  children?: React.ReactNode;
  mono?: boolean;
}): JSX.Element {
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
            ? 'Backend unavailable — the API may be restarting. Try again shortly.'
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
