/**
 * F2 Admin Portal — Report dashboard shell (Sync / Map tabs).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 2.21, 2.22)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.7, §7.8)
 */
import { useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { useRouter } from '../lib/pages-router';
import { CoverageReport } from './CoverageReport';
import { MapReport } from './MapReport';

type TabKey = 'coverage' | 'map';

// `description` renders as the native browser tooltip + screen-reader aria-label.
// Same pattern as DataDashboard.tsx tabs.
const TABS: Array<{ key: TabKey; label: string; description: string }> = [
  {
    key: 'coverage',
    label: 'Coverage',
    description:
      'Fieldwork progress vs facility targets by region / province / facility. Counts match the Facilities page.',
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
    // Legacy ?tab=sync bookmarks fall through to the default (Coverage).
    return TABS.some((x) => x.key === t) ? (t as TabKey) : 'coverage';
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
          <Button
            type="button"
            variant="tableAction"
            size="tableAction"
            key={key}
            onClick={() => switchTab(key)}
            aria-current={activeTab === key ? 'page' : undefined}
            title={description}
            aria-label={`${label} — ${description}`}
            className={
              activeTab === key
                ? 'border-b-2 border-signal pb-1 font-sans text-sm normal-case tracking-normal text-ink no-underline hover:no-underline'
                : 'pb-1 font-sans text-sm normal-case tracking-normal text-muted-foreground no-underline hover:text-ink hover:no-underline'
            }
          >
            {label}
          </Button>
        ))}
      </nav>

      <div className="pt-2">
        {activeTab === 'coverage' ? (
          <CoverageReport apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        ) : (
          <MapReport apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        )}
      </div>
    </section>
  );
}
