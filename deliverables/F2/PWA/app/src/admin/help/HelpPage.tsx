/**
 * F2 Admin Portal — Help / Operator Guide.
 *
 * Top-level Help dashboard. Centralized documentation surface so first-time
 * ASPSI ops users can self-train without a 30-page external doc — and so
 * tooltips on each tab don't have to carry the full conceptual load.
 *
 * Pattern: single-page markdown-shaped content rendered as JSX. Sections are
 * <article> blocks with a <header> + body. Verde Manual styling consistent
 * with the rest of the portal — mono eyebrow, serif h2/h3, body text in
 * Public Sans, hairline rules between sections.
 *
 * Editing: hand-edit this file and redeploy. There's no F2_Help sheet —
 * keeping the content version-controlled in the React app means it ships
 * with the app version and updates at deploy time. If we want operator-
 * editable docs later (without a deploy), the spec for that is in
 * docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md §7.20 (TBD).
 */
import type { ReactNode } from 'react';

export function HelpPage(): JSX.Element {
  return (
    <section className="mx-auto flex max-w-4xl flex-col gap-8 py-2">
      <header className="border-b border-hairline pb-3">
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Section</p>
        <h2 className="mt-1 font-serif text-2xl font-medium tracking-tight">Help &amp; Operator Guide</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          What this portal is, what each tab does, and how to do the common things. If you&rsquo;re
          new here, read the <strong>Quick Start</strong> below first; if you&rsquo;re looking up a
          term, jump to the <strong>Glossary</strong> at the bottom.
        </p>
      </header>

      <Article id="quick-start" title="Quick Start" eyebrow="Welcome">
        <p>
          The F2 Admin Portal is the operations console for the F2 Healthcare Worker survey. It mirrors
          the role-based dashboard pattern ASPSI uses with CSWeb on the CSPro instruments — five
          dashboards, role-aware navigation, per-instrument permission flags. If you&rsquo;ve used
          CSWeb, the shape will feel familiar.
        </p>
        <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm">
          <li>
            <strong>Data</strong> is where you&rsquo;ll spend most of your time — see what HCWs have
            submitted, who&rsquo;s enrolled, audit trail, and parked failures.
          </li>
          <li>
            <strong>Reports</strong> aggregates the same data into coverage reports + a geographic
            map.
          </li>
          <li>
            <strong>Configuration</strong> (dropdown) — Apps &amp; Settings (versioning, files,
            scheduled exports, quota), Users, Roles. Configuration changes affect the system; treat
            them with the same care you&rsquo;d treat a CSWeb admin action.
          </li>
          <li>
            <strong>Encode</strong> — only used when an HCW completed a paper questionnaire and an
            ops user is transcribing it into the system after the fact.
          </li>
        </ol>
      </Article>

      <Article id="dashboards" title="Dashboard guide" eyebrow="What's where">
        <DashboardTable />
      </Article>

      <Article id="data-tabs" title="Data dashboard sub-tabs" eyebrow="Tab-by-tab">
        <SubtabTable
          rows={[
            {
              tab: 'Responses',
              what: 'All HCW survey submissions',
              detail:
                'Filter by date range, facility ID, source path (self-admin vs paper-encoded), errors. Click a row to open ResponseDetail with the full answer set, the device fingerprint that submitted, and the audit trail.',
            },
            {
              tab: 'Audit',
              what: 'Forensic event log',
              detail:
                'Every admin action and every HCW submission writes a row here. Columns: when / event / actor / resource / detail. Use the actor and event-type filters when investigating an incident.',
            },
            {
              tab: 'DLQ',
              what: 'Dead-Letter Queue — parked failures',
              detail:
                'When a submission arrives at the backend but cannot be processed (validation fail, schema_version drift, lock timeout), the payload is written here instead of being dropped. Operators can inspect the failure reason, fix the upstream issue, and replay. Empty in normal operation.',
            },
            {
              tab: 'HCWs',
              what: 'Healthcare worker registry',
              detail:
                'One row per enrolled HCW. Token state, submission status, facility. Reissue an enrollment token here when an HCW loses their device; re-encode a paper response by clicking through to the encoder; revoke active sessions if needed.',
            },
          ]}
        />
      </Article>

      <Article id="reports-tabs" title="Reports dashboard sub-tabs" eyebrow="Tab-by-tab">
        <SubtabTable
          rows={[
            {
              tab: 'Sync Report',
              what: 'Coverage by region / province / facility',
              detail:
                'Aggregated counts of HCWs enrolled vs submitted vs pending. Snapshot view; refresh to recompute. Use during fieldwork weekly check-ins to identify under-performing facilities.',
            },
            {
              tab: 'Map Report',
              what: 'Geographic plot',
              detail:
                'Submissions plotted from GPS captured at submit time (with HCW consent per spec §9). Markers cluster by area. Hover for facility-level counts; markers without GPS are rendered separately as a "no-GPS" total in the legend.',
            },
          ]}
        />
      </Article>

      <Article id="apps-sections" title="Apps &amp; Settings sections" eyebrow="Tab-by-tab">
        <SubtabTable
          rows={[
            {
              tab: 'Versioning',
              what: 'Live build identifiers',
              detail:
                'PWA bundle SHA, Worker version, Apps Script deployment, latest spec_version seen in submissions. First place to look during incident triage — answers "what version is in front of users?".',
            },
            {
              tab: 'Files',
              what: 'Operator file uploads',
              detail:
                'Training plans, facility rosters, fieldwork checklists. Stored in Cloudflare R2 (not in Sheets). PDF / ZIP / PNG / JPEG / GIF, up to 100 MB. Visible to operators with dash_apps permission; never exposed to HCWs.',
            },
            {
              tab: 'Data Settings',
              what: 'Scheduled break-out exports',
              detail:
                'Cron-fired CSV exports of F2_Responses to R2 — per facility, per region, etc. Worker cron fires every 5 minutes and runs settings whose next_run_at has elapsed. Use "Run now" to trigger out-of-band.',
            },
            {
              tab: 'Apps Script Quota',
              what: 'Daily AS execution count',
              detail:
                'Apps Script has a 20,000-call/day hard ceiling. When this hits 100% the backend rejects writes until UTC midnight rollover. Watch this during enumerator surge windows; if approaching 80%+, start triaging non-essential scheduled jobs.',
            },
          ]}
        />
      </Article>

      <Article id="workflows" title="Common workflows" eyebrow="How to">
        <Workflow
          number={1}
          title="Reissue an enrollment token"
          when="HCW lost their device, broke their tablet, or the original token has been revoked."
          steps={[
            'Data → HCWs tab. Find the HCW (search by hcw_id or facility).',
            'Click the REISSUE button on their row.',
            'In the confirm modal, optionally add a reason (e.g., "device replaced").',
            'Click "Issue new token". Modal flips to a success state with a QR code, the enrollment URL, and the raw JWT.',
            'Hand over the URL or have the HCW scan the QR. The previous token stops working as soon as the HCW switches devices.',
          ]}
          gotcha="If two admins both click Reissue on the same HCW concurrently, only the first wins (CAS-protected on the prev_jti). The second sees a 409 conflict — refresh and retry."
        />

        <Workflow
          number={2}
          title="Triage a DLQ entry"
          when="A submission appears in Data → DLQ — backend rejected it for some reason."
          steps={[
            'Data → DLQ tab. Click the row to see the failure reason and the original payload.',
            'Read the reason field (e.g., "E_SPEC_DRIFT: client submitted spec_version=2026-04-08 below min_accepted=2026-04-17-m1").',
            'Decide: retryable (spec drift → tell HCW to refresh and resubmit), broken (corrupt payload → discard with reason logged), or escalate (unknown / first-time failure mode → ping #f2-pwa-uat).',
            'Action depends on the call: replay manually if the upstream issue is fixed, or mark resolved with a note.',
          ]}
          gotcha="DLQ entries are not auto-replayed. They sit until an operator decides what to do. Don't let the queue grow unattended past a working day; a sustained DLQ backlog usually means a real upstream regression."
        />

        <Workflow
          number={3}
          title="Encode a paper response"
          when="HCW completed the questionnaire on paper (no tablet available, internet outage, etc.) and an ops user is transcribing into the system."
          steps={[
            'Confirm the HCW is enrolled — Data → HCWs. If not, enroll them first via the seed flow.',
            'Click ENCODE on the HCW row, or navigate directly to /admin/encode/<hcw_id>.',
            'Fill the form section-by-section, matching the paper questionnaire. Autosaves between sections (IndexedDB locally; persists to F2_Responses on submit).',
            'On submit, the response lands in F2_Responses with source_path="paper_encoded" and encoded_by=<your username>.',
          ]}
          gotcha='Paper-encoded responses are visually distinct in the Responses tab (filter chip "Paper-encoded"). They count toward Sync Report totals but are NOT included in self-admin-only analyses by default — check the source_path filter in any downstream pipeline.'
        />

        <Workflow
          number={4}
          title="Bulk import users"
          when="Adding a new cohort of ASPSI ops staff at once (typically at the start of a fieldwork wave)."
          steps={[
            'Configuration → Users.',
            'Click "Bulk import" to open the CSV preview.',
            'Required columns: username, first_name, last_name, role_name, email, phone. Optional: password (autogenerated if blank, sent to email if SMTP configured).',
            'Paste your CSV. The preview validates each row — duplicates flagged, role lookups confirmed, password rules checked.',
            'Click Import. New users get password_must_change=true; first-login forces them to rotate.',
          ]}
          gotcha="Maximum 500 rows per import call. For larger cohorts, split into batches. The import is transactional within a batch — if one row fails validation, the whole batch is rejected with a list of issues."
        />

        <Workflow
          number={5}
          title="Run a scheduled break-out manually"
          when={'You need a fresh CSV export now (e.g., for a stakeholder request) instead of waiting for the next cron tick.'}
          steps={[
            'Configuration → Apps & Settings → Data Settings.',
            'Find the setting (e.g., "F2 daily break-out per region"). Click "Run now".',
            'The Worker invokes the break-out immediately; last_run_at updates to now.',
            "Output lands at the configured output_path_template in R2 (e.g., 'exports/2026-05-04/f2-daily.csv').",
            'Download from the Files tab or via wrangler r2 object get.',
          ]}
          gotcha="Run now does not change the cron schedule. The next regularly-scheduled run still happens at next_run_at; running manually is additive. If you want to advance the schedule, edit the setting's next_run_at directly."
        />
      </Article>

      <Article id="roles" title="Roles &amp; permissions" eyebrow="Quick reference">
        <p className="text-sm">
          Roles are CSWeb-style: a flag matrix across dashboards (data / report / apps / users /
          roles) and per-instrument up/down permissions (self-admin / paper-encoded / capi). Built-in
          roles cover the typical operating shapes; create custom roles for unusual access patterns.
        </p>
        <table className="mt-3 w-full table-auto text-sm">
          <thead className="border-b border-hairline">
            <tr className="text-left">
              <Th>Built-in role</Th>
              <Th>What they can do</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-hairline">
            <Tr name="Administrator" desc="Full read + write across all dashboards, including users + roles. There must always be at least one. Treat the seat with care; rotate passwords promptly when staff leaves." />
            <Tr name="Standard User" desc="Read everything except Users + Roles. Cannot mutate; safe default for new staff who need visibility but not admin power." />
            <Tr name="DataReader (custom)" desc="Read Data + Reports only. No Apps & Settings, no Users / Roles. Useful for analyst access where the analyst should never accidentally toggle a config." />
            <Tr name="Encoder (custom)" desc="Encode dashboard + read access to Responses for the HCWs they're encoding. No DLQ, no audit, no admin." />
          </tbody>
        </table>
        <p className="mt-3 text-xs text-muted-foreground">
          Editing a role bumps its <code>role_version</code>. Existing JWTs with the old version
          are invalidated on next request — the user is bounced to login with their new permission
          set. This is the mechanism that makes role changes take effect without waiting for token
          expiry.
        </p>
      </Article>

      <Article id="glossary" title="Glossary" eyebrow="Terms">
        <dl className="grid grid-cols-1 gap-x-6 gap-y-3 text-sm md:grid-cols-2">
          <Term word="HCW">
            Healthcare Worker. The respondent population for the F2 questionnaire — physicians,
            nurses, midwives, lab techs, BHWs, etc.
          </Term>
          <Term word="DLQ">
            Dead-Letter Queue. Storage for submissions that failed processing. Operators triage them
            here instead of losing the data.
          </Term>
          <Term word="JTI">
            JWT ID — the unique identifier embedded in each enrollment token. Used to revoke specific
            tokens without affecting other devices for the same HCW.
          </Term>
          <Term word="RBAC">
            Role-Based Access Control. The permission system: roles map to flags, users map to roles,
            requests are gated by the user&rsquo;s effective flags.
          </Term>
          <Term word="source_path">
            How a response entered the system. <code>self_admin</code> = HCW filled the survey on
            their own device. <code>paper_encoded</code> = ops user transcribed a paper response.
          </Term>
          <Term word="spec_version">
            The questionnaire spec version the device built against. The backend rejects submissions
            below <code>min_accepted_spec_version</code> to avoid storing data from outdated forms.
          </Term>
          <Term word="role_version">
            Counter on each role; bumps every time the role&rsquo;s permissions change. Used to
            invalidate old JWTs after a permission revocation.
          </Term>
          <Term word="break-out">
            Scheduled CSV export of F2_Responses to Cloudflare R2 — sliced by facility, region, etc.
            Configured in Data Settings.
          </Term>
          <Term word="CAS">
            Compare-And-Swap. The concurrency-safety pattern used for token reissue: the operation
            only succeeds if the current state matches what the operator saw. Two admins can&rsquo;t
            silently overwrite each other.
          </Term>
          <Term word="cron tick">
            The Worker&rsquo;s scheduled wake-up — fires every 5 minutes. Reads Data Settings rows
            whose <code>next_run_at</code> has elapsed and runs their break-outs.
          </Term>
        </dl>
      </Article>

      <Article id="support" title="Where to get support" eyebrow="If you're stuck">
        <ul className="list-disc space-y-2 pl-5 text-sm">
          <li>
            <strong>Operational issue</strong> — DLQ growing, dashboard not loading, weird audit
            entry: post in <code>#f2-pwa-uat</code> on Slack with the request_id of the affected
            request (visible in audit log + browser DevTools network tab).
          </li>
          <li>
            <strong>Bug report</strong> — file a GitHub issue at{' '}
            <code>github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development</code> with reproduction steps,
            expected vs actual, and screenshots. Tag <code>admin-portal</code>.
          </li>
          <li>
            <strong>Feature request</strong> — same issue tracker; tag <code>enhancement</code>{' '}
            instead of <code>bug</code>. Triage cadence is weekly.
          </li>
          <li>
            <strong>Security concern</strong> — never post in Slack. Email Carl directly:{' '}
            <code>clreyes6@up.edu.ph</code>. Spec §10 covers the security model in detail.
          </li>
        </ul>
      </Article>
    </section>
  );
}

/* ============================================================
 * Sub-components
 * ============================================================ */

function Article({
  id,
  title,
  eyebrow,
  children,
}: {
  id: string;
  title: ReactNode;
  eyebrow: string;
  children: ReactNode;
}): JSX.Element {
  return (
    <article id={id} className="flex flex-col gap-3 border-b border-hairline pb-6 last:border-b-0">
      <header className="flex flex-col">
        <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          {eyebrow}
        </p>
        <h3 className="mt-1 font-serif text-xl font-medium tracking-tight">{title}</h3>
      </header>
      <div className="text-sm leading-relaxed text-foreground">{children}</div>
    </article>
  );
}

function DashboardTable(): JSX.Element {
  const rows: Array<{ name: string; permFlag: string; gist: string }> = [
    { name: 'Data', permFlag: 'dash_data', gist: 'Submissions, audit log, DLQ, HCWs registry. Day-to-day operations live here.' },
    { name: 'Reports', permFlag: 'dash_report', gist: 'Aggregated coverage reports + geographic map. Read-only summary views.' },
    { name: 'Apps & Settings', permFlag: 'dash_apps', gist: 'Build versions, file uploads, scheduled break-out exports, quota usage. Operations bookkeeping.' },
    { name: 'Users', permFlag: 'dash_users', gist: 'CRUD for ops staff accounts. Bulk-import for new cohorts. Force-revoke sessions.' },
    { name: 'Roles', permFlag: 'dash_roles', gist: 'Permission matrix editor. Built-in roles + custom roles. Editing a role bumps its version and invalidates existing JWTs.' },
    { name: 'Encode', permFlag: 'dict_paper_encoded_up', gist: 'Paper-response transcription flow. Only used when HCW completed the survey on paper.' },
    { name: 'Help', permFlag: '— (no perm gate)', gist: 'This guide. Always visible regardless of role.' },
  ];
  return (
    <table className="w-full table-auto text-sm">
      <thead className="border-b border-hairline">
        <tr className="text-left">
          <Th>Dashboard</Th>
          <Th>Permission flag</Th>
          <Th>What it does</Th>
        </tr>
      </thead>
      <tbody className="divide-y divide-hairline">
        {rows.map((r) => (
          <tr key={r.name}>
            <Td>
              <strong>{r.name}</strong>
            </Td>
            <Td>
              <code className="text-xs">{r.permFlag}</code>
            </Td>
            <Td className="text-muted-foreground">{r.gist}</Td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SubtabTable({
  rows,
}: {
  rows: Array<{ tab: string; what: string; detail: string }>;
}): JSX.Element {
  return (
    <table className="w-full table-auto text-sm">
      <thead className="border-b border-hairline">
        <tr className="text-left">
          <Th>Tab</Th>
          <Th>What</Th>
          <Th>Detail</Th>
        </tr>
      </thead>
      <tbody className="divide-y divide-hairline">
        {rows.map((r) => (
          <tr key={r.tab}>
            <Td>
              <strong>{r.tab}</strong>
            </Td>
            <Td>{r.what}</Td>
            <Td className="text-muted-foreground">{r.detail}</Td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Workflow({
  number,
  title,
  when,
  steps,
  gotcha,
}: {
  number: number;
  title: string;
  when: string;
  steps: string[];
  gotcha?: string;
}): JSX.Element {
  return (
    <section className="mb-6 flex flex-col gap-2 last:mb-0">
      <header className="flex items-baseline gap-3">
        <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          Workflow {number}
        </span>
        <h4 className="font-serif text-base font-medium tracking-tight">{title}</h4>
      </header>
      <p className="text-sm">
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">When</span>{' '}
        — {when}
      </p>
      <ol className="list-decimal space-y-1 pl-5 text-sm">
        {steps.map((s, i) => (
          <li key={i}>{s}</li>
        ))}
      </ol>
      {gotcha ? (
        <p className="rounded-sm border-l-2 border-warning bg-secondary/30 px-3 py-2 text-xs text-foreground">
          <span className="font-mono uppercase tracking-wider text-muted-foreground">Gotcha</span>{' '}
          — {gotcha}
        </p>
      ) : null}
    </section>
  );
}

function Th({ children }: { children: ReactNode }): JSX.Element {
  return (
    <th className="px-2 py-2 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
      {children}
    </th>
  );
}

function Td({ children, className }: { children: ReactNode; className?: string }): JSX.Element {
  return <td className={`px-2 py-2 align-top ${className ?? ''}`}>{children}</td>;
}

function Tr({ name, desc }: { name: string; desc: string }): JSX.Element {
  return (
    <tr>
      <Td>
        <strong>{name}</strong>
      </Td>
      <Td className="text-muted-foreground">{desc}</Td>
    </tr>
  );
}

function Term({ word, children }: { word: string; children: ReactNode }): JSX.Element {
  return (
    <div className="flex flex-col">
      <dt className="font-mono text-xs uppercase tracking-wider text-foreground">{word}</dt>
      <dd className="text-muted-foreground">{children}</dd>
    </div>
  );
}
