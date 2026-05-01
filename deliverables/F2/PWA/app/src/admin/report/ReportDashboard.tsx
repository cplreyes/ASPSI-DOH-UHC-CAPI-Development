/**
 * F2 Admin Portal — Report dashboard shell (Sync / Map tabs).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 2.21, 2.22)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.7, §7.8)
 */
import { useMemo, type ReactNode } from 'react';
import { useRouter } from '../lib/pages-router';
import { SyncReport } from './SyncReport';

type TabKey = 'sync' | 'map';

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: 'sync', label: 'Sync Report' },
  { key: 'map', label: 'Map Report' },
];

export interface ReportDashboardProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

export function ReportDashboard({ apiBaseUrl, fetchImpl }: ReportDashboardProps): JSX.Element {
  const { pathname, navigate } = useRouter();
  const activeTab = useMemo<TabKey>(() => {
    const params = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '');
    const t = params.get('tab');
    return TABS.some(x => x.key === t) ? (t as TabKey) : 'sync';
  }, [pathname]);

  const switchTab = (key: TabKey) => {
    const params = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '');
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
        {TABS.map(({ key, label }) => (
          <button
            type="button"
            key={key}
            onClick={() => switchTab(key)}
            aria-current={activeTab === key ? 'page' : undefined}
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
          <MapComingSoon />
        )}
      </div>
    </section>
  );
}

function MapComingSoon(): ReactNode {
  return (
    <div className="border border-hairline bg-secondary/20 px-4 py-6">
      <p className="font-serif text-lg">Map Report</p>
      <p className="mt-1 text-sm text-muted-foreground">
        The submission map (lat/lng marker clustering at the national / regional level) lands with
        a follow-up Sprint 2 task. The Sync Report tab is live above with real region-level pacing.
      </p>
    </div>
  );
}
