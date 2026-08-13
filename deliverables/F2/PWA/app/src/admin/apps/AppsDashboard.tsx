/**
 * F2 Admin Portal — Apps & Settings dashboard shell with sub-tabs.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 3.6–3.10)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.6, §7.9)
 *
 * Reworked 2026-07-17 (Apps-tab audit): the Data Settings and Apps Script
 * Quota sub-tabs were removed — scheduled exports never had an executor on
 * this stack and the AS quota gauge measured a retired system. The global
 * kill switch + broadcast message moved out of Data Settings into a
 * first-position Controls sub-tab (they are the portal's incident controls).
 * Legacy ?tab=data-settings / ?tab=quota deep links fall back to Controls.
 */
import { useMemo, type ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { useRouter } from '../lib/pages-router';
import { Controls } from './Controls';
import { Versioning } from './Versioning';
import { Files } from './Files';

type TabKey = 'controls' | 'versioning' | 'files';

// `description` renders as the native browser tooltip + screen-reader aria-label
// (same pattern as DataDashboard / ReportDashboard).
const TABS: Array<{ key: TabKey; label: string; description: string }> = [
  {
    key: 'controls',
    label: 'Controls',
    description:
      'Global survey controls: the kill switch (immediately blocks all submissions server-side) and the broadcast banner shown to every respondent.',
  },
  {
    key: 'versioning',
    label: 'Versioning',
    description:
      'Live build identifiers (PWA bundle + SHA, API version, last deploy) and per-spec response counts. First place to look during incident triage.',
  },
  {
    key: 'files',
    label: 'Files',
    description:
      'Operator-uploaded files (training plans, facility rosters, fieldwork checklists) stored on the survey server. PDF / ZIP / PNG / JPEG / GIF, up to 100 MB.',
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
    // Unknown keys (incl. legacy data-settings / quota links) fall back to Controls.
    return TABS.some((x) => x.key === t) ? (t as TabKey) : 'controls';
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
          Survey controls, build versions, file uploads.
        </p>
      </header>

      <nav className="flex flex-wrap gap-6 text-sm" aria-label="Apps & Settings tabs">
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
        {activeTab === 'controls' ? (
          <Controls apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        ) : activeTab === 'versioning' ? (
          <Versioning apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
        ) : activeTab === 'files' ? (
          <Files apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
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
