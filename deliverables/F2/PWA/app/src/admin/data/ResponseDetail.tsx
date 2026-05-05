/**
 * F2 Admin Portal — Response Detail page.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.19)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.1)
 *
 * Fetches GET /admin/api/dashboards/data/responses/:id and renders the
 * full submission broken out by F2 questionnaire sections. Reuses the
 * generated `sections` array (same source of truth as the survey form)
 * so any item added to the codebook automatically appears in the
 * detail view without a separate config change.
 *
 * Provenance bar at the top mirrors the Responses table columns
 * (submitted_at, hcw_id, facility, source_path, status) plus
 * encoded_by + encoded_at when source_path=paper_encoded, plus a
 * mono-rendered submission_id for trace.
 */
import { useEffect, useState } from 'react';
import { LocaleProvider, useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Section as SectionModel, Item } from '@/types/survey';
import { sections as ALL_SECTIONS } from '@/generated/items';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { Link, useRouter } from '../lib/pages-router';

interface ResponseRow {
  submission_id: string;
  client_submission_id: string;
  submitted_at_server: string;
  submitted_at_client: string | number;
  source: string;
  spec_version: string;
  app_version: string;
  hcw_id: string;
  facility_id: string;
  device_fingerprint: string;
  status: string;
  values_json: string;
  submission_lat: number | string;
  submission_lng: number | string;
  source_path: string;
  encoded_by: string;
  encoded_at: string;
}

export interface ResponseDetailProps {
  apiBaseUrl: string;
  submissionId: string;
  fetchImpl?: typeof fetch;
}

export function ResponseDetail({
  apiBaseUrl,
  submissionId,
  fetchImpl,
}: ResponseDetailProps): JSX.Element {
  return (
    <LocaleProvider>
      <ResponseDetailInner
        apiBaseUrl={apiBaseUrl}
        submissionId={submissionId}
        {...(fetchImpl ? { fetchImpl } : {})}
      />
    </LocaleProvider>
  );
}

function ResponseDetailInner({
  apiBaseUrl,
  submissionId,
  fetchImpl,
}: ResponseDetailProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [state, setState] = useState<
    { kind: 'loading' } | { kind: 'loaded'; row: ResponseRow } | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<ResponseRow>(
        `${apiBaseUrl}/admin/api/dashboards/data/responses/${encodeURIComponent(submissionId)}`,
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
      if (r.ok) setState({ kind: 'loaded', row: r.data });
      else setState({ kind: 'failed', error: r.error });
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, submissionId, token]);

  return (
    <section className="flex flex-col gap-6 py-2">
      <header className="border-b border-hairline pb-3">
        <Link
          to="/admin/data"
          className="font-mono text-xs uppercase tracking-wider text-muted-foreground underline-offset-4 hover:text-ink hover:underline"
        >
          ← Data Dashboard
        </Link>
        <h2 className="mt-2 font-serif text-2xl font-medium tracking-tight">Response Detail</h2>
        <p className="mt-1 font-mono text-xs text-muted-foreground">{submissionId}</p>
      </header>

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : state.kind === 'failed' ? (
        <ErrorPanel error={state.error} />
      ) : (
        <DetailBody row={state.row} />
      )}
    </section>
  );
}

function DetailBody({ row }: { row: ResponseRow }): JSX.Element {
  const { locale } = useLocale();
  const values = parseValues(row.values_json);

  return (
    <>
      <ProvenanceBlock row={row} />

      <div className="flex flex-col gap-8">
        {ALL_SECTIONS.map((section) => (
          <SectionDetail key={section.id} section={section} values={values} locale={locale} />
        ))}
      </div>

      <details className="border-t border-hairline pt-4">
        <summary className="cursor-pointer font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-ink">
          Raw values_json
        </summary>
        <pre className="mt-2 max-h-96 overflow-auto border border-hairline bg-secondary/20 p-3 font-mono text-xs text-muted-foreground">
          {JSON.stringify(values, null, 2)}
        </pre>
      </details>
    </>
  );
}

function ProvenanceBlock({ row }: { row: ResponseRow }): JSX.Element {
  const isEncoded = row.source_path === 'paper_encoded';
  return (
    <dl className="grid grid-cols-1 gap-y-2 border-l-2 border-hairline pl-4 text-sm sm:grid-cols-2 sm:gap-x-6">
      <Field label="Submitted (server)" mono>
        {formatTs(row.submitted_at_server)}
      </Field>
      <Field label="HCW" mono>
        {row.hcw_id || '—'}
      </Field>
      <Field label="Facility" mono>
        {row.facility_id || '—'}
      </Field>
      <Field label="Source path" mono>
        {row.source_path || '—'}
      </Field>
      <Field label="Status">
        <span className={row.status === 'rejected' ? 'text-error' : 'text-muted-foreground'}>
          {row.status || '—'}
        </span>
      </Field>
      <Field label="Spec / App" mono>
        {row.spec_version} · {row.app_version || '—'}
      </Field>
      {row.submission_lat ? (
        <Field label="Location" mono>
          {String(row.submission_lat)}, {String(row.submission_lng)}
        </Field>
      ) : null}
      {isEncoded ? (
        <Field label="Encoded by" mono>
          {row.encoded_by || '—'}{' '}
          <span className="text-muted-foreground">@ {formatTs(row.encoded_at)}</span>
        </Field>
      ) : null}
    </dl>
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

function SectionDetail({
  section,
  values,
  locale,
}: {
  section: SectionModel;
  values: Record<string, unknown>;
  locale: string;
}): JSX.Element | null {
  const rows = collectRows(section.items, values, locale);
  if (rows.length === 0) return null;

  return (
    <section className="flex flex-col gap-2">
      <header className="flex items-baseline gap-3">
        <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          Section {section.id}
        </span>
        <h3 className="font-serif text-lg font-medium tracking-tight">
          {localized(section.title, locale as 'en' | 'fil')}
        </h3>
      </header>
      <dl className="divide-y divide-hairline border-y border-hairline">
        {rows.map((r) => (
          <div key={r.key} className="grid grid-cols-3 gap-3 py-2 text-sm">
            <dt className="col-span-2 text-muted-foreground">
              <span className="font-mono text-xs">{r.id}</span> {r.label}
            </dt>
            <dd className="font-mono text-xs">{r.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function collectRows(
  items: Item[],
  values: Record<string, unknown>,
  locale: string,
): Array<{ key: string; id: string; label: string; value: string }> {
  const out: Array<{ key: string; id: string; label: string; value: string }> = [];
  const lc = locale as 'en' | 'fil';
  for (const item of items) {
    if (item.type === 'multi-field' && item.subFields) {
      for (const sf of item.subFields) {
        const val = formatValue(values[sf.id]);
        if (val !== '') {
          out.push({
            key: sf.id,
            id: item.id,
            label: localized(sf.label, lc),
            value: val,
          });
        }
      }
    } else {
      const primary = formatValue(values[item.id]);
      if (primary !== '') {
        out.push({
          key: item.id,
          id: item.id,
          label: localized(item.label, lc),
          value: primary,
        });
      }
      const otherKey = `${item.id}_other`;
      const otherVal = formatValue(values[otherKey]);
      if (otherVal !== '') {
        out.push({
          key: otherKey,
          id: `${item.id} other`,
          label: '(specify)',
          value: otherVal,
        });
      }
    }
  }
  return out;
}

function formatValue(v: unknown): string {
  if (v === null || v === undefined || v === '') return '';
  if (Array.isArray(v)) return v.join(', ');
  return String(v);
}

function parseValues(raw: string): Record<string, unknown> {
  if (!raw) return {};
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : {};
  } catch {
    return {};
  }
}

function formatTs(iso: string | number): string {
  if (!iso) return '';
  const d = typeof iso === 'number' ? new Date(iso) : new Date(iso);
  if (isNaN(d.getTime())) return String(iso);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function ErrorPanel({ error }: { error: ApiError }): JSX.Element {
  if (error.code === 'E_NOT_FOUND') {
    return (
      <div className="border border-hairline bg-secondary/20 px-4 py-6">
        <p className="font-serif text-lg">Submission not found</p>
        <p className="mt-1 text-sm text-muted-foreground">
          The ID may be stale or the submission was rejected before reaching F2_Responses. Check the
          DLQ tab for malformed submissions.
        </p>
      </div>
    );
  }
  return (
    <div role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2">
      <p className="text-sm text-error">
        {error.code === 'E_PERM_DENIED'
          ? 'Your role lacks dash_data. Contact an Administrator.'
          : error.code === 'E_BACKEND'
            ? 'Backend unavailable — Apps Script staging may not be reachable yet.'
            : error.code === 'E_NETWORK'
              ? 'Network unavailable. Reload to retry.'
              : (error.message ?? 'Failed to load submission.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
