/**
 * F2 Admin Portal — Apps dashboard shell.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 3.6–3.10)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.6, §7.9)
 *
 * Lands Versioning + Files. Data Settings (cron-driven CSV exports)
 * and QuotaWidget are still placeholders pointing at the relevant
 * Sprint 3 tasks.
 */
import { Versioning } from './Versioning';
import { Files } from './Files';

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

      <ComingSoonPanel
        title="Data Settings"
        body="Scheduled break-out CSV exports configured per instrument. Lands with the cron dispatcher (Sprint 3.3, 3.4, 3.5). Generates CSVs to R2 on a per-row interval."
      />

      <ComingSoonPanel
        title="Apps Script Quota"
        body="Daily quota widget showing consumed / remaining quota across the AS deployment. Lands with Sprint 3.9 — turns red at 80% of daily limit."
      />
    </section>
  );
}

function ComingSoonPanel({ title, body }: { title: string; body: string }): JSX.Element {
  return (
    <section className="border-l-2 border-hairline pl-4">
      <h3 className="font-serif text-lg font-medium tracking-tight">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{body}</p>
    </section>
  );
}
