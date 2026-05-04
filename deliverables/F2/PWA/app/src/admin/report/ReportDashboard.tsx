/**
 * F2 Admin Portal — Report dashboard shell (Sync / Map tabs).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 2.21, 2.22)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.7, §7.8)
 */
import { useMemo } from 'react';
import { useRouter } from '../lib/pages-router';
import { SyncReport } from './SyncReport';
import { MapReport } from './MapReport';

type TabKey = 'sync' | 'map';

// `description` renders as the native browser tooltip + screen-reader aria-label.
// Same pattern as DataDashboard.tsx tabs.
const TABS: Array<{ key: TabKey; label: string; description: string }> = [
  {
    key: 'sync',
    label: 'Sync Report',
    description:
      'Submission counts aggregated by region / province / facility. Snapshot view of fieldwork coverage.',
  },
  {
    key: 'map',
    label: 'Map Report',
    description:
      'Geographic distribution of submissions plotted from GPS captured at submit time. Markers cluster by area; click for facility-level detail.',
  },
];

export interface ReportDashboardProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

export function ReportDashboard({ apiBaseUrl, fetchImpl }: ReportDashboardProps): JSX.Element {
  const { pathname, search, navigate } = useRouter();
  const activeTab = useMemo<TabKey>(() => {
    const params = new URLSearchParams(search);
    const t = params.get('tab');
    return TABS.some(x => x.key === t) ? (t as TabKey) : 'sync';
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
        <h2 className="mt-1 font-serif text-2xl font-medium tracking-tight">Report Dashboard</h2>
      </header>

      <nav className="flex flex-wrap gap-6 text-sm" aria-label="Report tabs">
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
        {activeTab === 'sync' ? (
          <SyncReport apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        ) : (
          <MapReport apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        )}
      </div>
    </section>
  );
}
