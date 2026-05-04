/**
 * F2 Admin Portal — Data dashboard shell (Responses / Audit / DLQ / HCWs tabs).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.15)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.0, §7.1)
 */
import { useMemo, type ReactNode } from 'react';
import { useRouter } from '../lib/pages-router';
import { ResponsesTab } from './ResponsesTab';
import { AuditTab } from './AuditTab';
import { DLQTab } from './DLQTab';
import { HCWsTab } from './HCWsTab';

type TabKey = 'responses' | 'audit' | 'dlq' | 'hcws';

// `description` is rendered as the native browser tooltip on hover/focus
// (also announced by screen readers) — first-time operators don't have to
// guess what each tab does. Pattern mirrors HCWsTab.tsx's REISSUE button
// title= usage. Kept short — full operator docs live in the spec.
const TABS: Array<{ key: TabKey; label: string; description: string }> = [
  {
    key: 'responses',
    label: 'Responses',
    description:
      'All HCW survey submissions. Filter by date / facility / source path. Click a row to see the full answer set.',
  },
  {
    key: 'audit',
    label: 'Audit',
    description:
      'Forensic event log. Every admin action and HCW submission writes a row here — actor, resource, request_id traceable.',
  },
  {
    key: 'dlq',
    label: 'DLQ',
    description:
      'Dead-Letter Queue. Submissions that failed processing (validation, schema drift, lock timeout) are parked here for triage + replay instead of dropped.',
  },
  {
    key: 'hcws',
    label: 'HCWs',
    description:
      'Healthcare worker enrollment registry. One row per HCW with token state and submission status. Reissue tokens, re-encode paper responses from here.',
  },
];

export interface DataDashboardProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

export function DataDashboard({ apiBaseUrl, fetchImpl }: DataDashboardProps): JSX.Element {
  const { pathname, search, navigate } = useRouter();
  const activeTab = useMemo<TabKey>(() => {
    const params = new URLSearchParams(search);
    const t = params.get('tab');
    return TABS.some((x) => x.key === t) ? (t as TabKey) : 'responses';
  }, [search]);

  const switchTab = (key: TabKey) => {
    const params = new URLSearchParams(search);
    params.set('tab', key);
    navigate(`${pathname}?${params.toString()}`);
  };

  return (
    <section className="flex flex-col gap-4 py-2">
      <header className="border-b border-hairline pb-3">
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Section</p>
        <h2 className="mt-1 font-serif text-2xl font-medium tracking-tight">Data Dashboard</h2>
      </header>

      <nav className="flex flex-wrap gap-6 text-sm" aria-label="Data dashboard tabs">
        {TABS.map(({ key, label, description }) => (
          <button
            type="button"
            key={key}
            onClick={() => switchTab(key)}
            aria-current={activeTab === key ? 'page' : undefined}
            title={description}
            aria-label={`${label} — ${description}`}
            className={
              activeTab === key
                ? 'border-b-2 border-signal pb-1 text-ink'
                : 'pb-1 text-muted-foreground hover:text-ink'
            }
          >
            {label}
          </button>
        ))}
      </nav>

      <div className="pt-2">
        {activeTab === 'responses' ? (
          <ResponsesTab apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        ) : activeTab === 'audit' ? (
          <AuditTab apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        ) : activeTab === 'dlq' ? (
          <DLQTab apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        ) : activeTab === 'hcws' ? (
          <HCWsTab apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        ) : (
          <TabComingSoon name={TABS.find((t) => t.key === activeTab)!.label} />
        )}
      </div>
    </section>
  );
}

function TabComingSoon({ name }: { name: string }): ReactNode {
  return (
    <p className="text-sm text-muted-foreground">
      The <strong>{name}</strong> tab lands with a later Sprint 2 task. The Responses tab is live
      above; switch back to see real data once the backend is reachable.
    </p>
  );
}
