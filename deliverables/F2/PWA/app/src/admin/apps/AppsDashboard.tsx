/**
 * F2 Admin Portal — Apps dashboard shell.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 3.6–3.10)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.6, §7.9)
 *
 * Lands Versioning + Files + Data Settings + Quota. All Sprint 3 Apps
 * dashboard sub-tasks are now wired; cron + AS still need AP0 to
 * round-trip end-to-end, but the UI surface is complete.
 */
import { Versioning } from './Versioning';
import { Files } from './Files';
import { DataSettings } from './DataSettings';
import { QuotaWidget } from './QuotaWidget';

export interface AppsDashboardProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

export function AppsDashboard({ apiBaseUrl, fetchImpl }: AppsDashboardProps): JSX.Element {
  return (
    <section className="flex flex-col gap-8 py-2">
      <header className="border-b border-hairline pb-3">
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Section</p>
        <h2 className="mt-1 font-serif text-2xl font-medium tracking-tight">Apps & Settings</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Build versions, file uploads, scheduled break-out exports, quota usage.
        </p>
      </header>

      <Versioning apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />

      <Files apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />

      <DataSettings apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />

      <QuotaWidget apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
    </section>
  );
}
