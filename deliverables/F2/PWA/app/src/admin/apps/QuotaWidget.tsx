/**
 * F2 Admin Portal - Apps Script daily quota widget.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.9)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (sec 7.6)
 *
 * Reads /admin/api/dashboards/apps/quota which returns
 * { date_utc, count, cap, percent }. Renders an inline progress bar;
 * crosses to a warn color above 80% (the standard AS-quota tripwire).
 */
import { useEffect, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

interface QuotaData {
  date_utc: string;
  count: number;
  cap: number;
  percent: number;
}

export interface QuotaWidgetProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

type State =
  | { kind: 'loading' }
  | { kind: 'loaded'; data: QuotaData }
  | { kind: 'failed'; error: ApiError };

export function QuotaWidget({ apiBaseUrl, fetchImpl }: QuotaWidgetProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [state, setState] = useState<State>({ kind: 'loading' });

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const r = await adminFetch<QuotaData>(
        `${apiBaseUrl}/admin/api/dashboards/apps/quota`,
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
    <section className="flex flex-col gap-2">
      <h3 className="font-serif text-lg font-medium tracking-tight">Apps Script Quota</h3>
      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : state.kind === 'failed' ? (
        <p role="alert" className="text-sm text-error">
          Failed to read quota{state.error.message ? ` - ${state.error.message}` : ''}.
        </p>
      ) : (
        <QuotaBar data={state.data} />
      )}
    </section>
  );
}

function QuotaBar({ data }: { data: QuotaData }): JSX.Element {
  const warn = data.percent >= 80;
  return (
    <div className="border-l-2 border-hairline pl-4">
      <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        {data.date_utc} UTC
      </p>
      <p className="mt-1 font-mono text-sm">
        {data.count.toLocaleString()} / {data.cap.toLocaleString()}{' '}
        <span className={warn ? 'text-error' : 'text-muted-foreground'}>
          ({data.percent}%)
        </span>
      </p>
      <div className="mt-2 h-1 w-full overflow-hidden bg-hairline/40" aria-hidden="true">
        <div
          className={`h-full ${warn ? 'bg-error' : 'bg-foreground'}`}
          style={{ width: `${Math.min(100, data.percent)}%` }}
        />
      </div>
    </div>
  );
}
