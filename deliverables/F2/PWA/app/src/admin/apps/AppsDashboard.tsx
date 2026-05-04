/**
 * F2 Admin Portal — Apps & Settings dashboard shell with sub-tabs.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 3.6–3.10)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.6, §7.9)
 *
 * Refactored 2026-05-04 from a single stacked page to a tabbed layout
 * matching DataDashboard / ReportDashboard. Versioning / Files / Data
 * Settings / Apps Script Quota are now four sub-tabs instead of vertically
 * stacked sections — operators can deep-link into any of them and the
 * dashboard shows one focused view at a time.
 */
import { useMemo, type ReactNode } from 'react';
import { useRouter } from '../lib/pages-router';
import { Versioning } from './Versioning';
import { Files } from './Files';
import { DataSettings } from './DataSettings';
import { QuotaWidget } from './QuotaWidget';

type TabKey = 'versioning' | 'files' | 'data-settings' | 'quota';

// `description` renders as the native browser tooltip + screen-reader aria-label
// (same pattern as DataDashboard / ReportDashboard).
const TABS: Array<{ key: TabKey; label: string; description: string }> = [
  {
    key: 'versioning',
    label: 'Versioning',
    description:
      'Live build identifiers (PWA bundle, Worker, Apps Script) and per-spec submission counts. First place to look during incident triage.',
  },
  {
    key: 'files',
    label: 'Files',
    description:
      'Operator-uploaded files (training plans, facility rosters, fieldwork checklists) stored in Cloudflare R2. PDF / ZIP / PNG / JPEG / GIF, up to 100 MB.',
  },
  {
    key: 'data-settings',
    label: 'Data Settings',
    description:
      'Scheduled break-out exports of F2_Responses to R2. Worker cron fires every 5 minutes and runs settings whose next_run_at has elapsed.',
  },
  {
    key: 'quota',
    label: 'Apps Script Quota',
    description:
      'Daily Apps Script execution count vs the 20,000-call limit. Hard ceiling — when this hits 100% the backend rejects writes until UTC rollover.',
  },
];

export interface AppsDashboardProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

export function AppsDashboard({ apiBaseUrl, fetchImpl }: AppsDashboardProps): JSX.Element {
  const { pathname, search, navigate } = useRouter();
  const activeTab = useMemo<TabKey>(() => {
    const params = new URLSearchParams(search);
    const t = params.get('tab');
    return TABS.some((x) => x.key === t) ? (t as TabKey) : 'versioning';
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
        <h2 className="mt-1 font-serif text-2xl font-medium tracking-tight">Apps &amp; Settings</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Build versions, file uploads, scheduled break-out exports, quota usage.
        </p>
      </header>

      <nav className="flex flex-wrap gap-6 text-sm" aria-label="Apps & Settings tabs">
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
        {activeTab === 'versioning' ? (
          <Versioning apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        ) : activeTab === 'files' ? (
          <Files apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        ) : activeTab === 'data-settings' ? (
          <DataSettings apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        ) : activeTab === 'quota' ? (
          <QuotaWidget apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
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
      The <strong>{name}</strong> tab lands with a later sprint.
    </p>
  );
}
