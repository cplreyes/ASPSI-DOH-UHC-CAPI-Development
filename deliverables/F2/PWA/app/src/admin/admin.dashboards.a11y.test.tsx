/**
 * #273 (E6-PWA-009b) — authenticated-state a11y audit, vitest-axe layer.
 *
 * #191 covered Login / HelpPage / Layout. This file extends component-level
 * axe coverage to the post-login Admin Portal surfaces #191 could not reach
 * without authenticated Lighthouse: the Data / Report / Apps / Users / Roles
 * dashboards, their tables, the file-upload + data-settings forms, the user /
 * role editors, the bulk-import + create-HCW + reissue modals, and the
 * paper-encode flow (which mounts the HCW MultiSectionForm shell).
 *
 * color-contrast stays disabled (jsdom can't resolve computed CSS — that gap is
 * owned by the Lighthouse pass) via AXE_COMPONENT_CONFIG.
 *
 * react-leaflet does not lay out under jsdom, so it is stubbed to passthrough
 * hosts: this audits MapReport's own chrome (no-GPS banner, controls, popups)
 * rather than leaflet's internals, whose a11y is leaflet's own + the Lighthouse
 * pass.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { axe, AXE_COMPONENT_CONFIG } from '@/test/axe-helpers';
import { AdminAuthProvider } from './lib/auth-context';
import { RouterProvider } from './lib/pages-router';

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
  TileLayer: () => null,
  Marker: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
  Popup: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
}));

import { DataDashboard } from './data/DataDashboard';
import { AuditTab } from './data/AuditTab';
import { DLQTab } from './data/DLQTab';
import { HCWsTab } from './data/HCWsTab';
import { ResponseDetail } from './data/ResponseDetail';
import { CreateHCWModal } from './data/CreateHCWModal';
import { ReissueTokenModal } from './data/ReissueTokenModal';
import { ReportDashboard } from './report/ReportDashboard';
import { MapReport } from './report/MapReport';
import { AppsDashboard } from './apps/AppsDashboard';
import { Files } from './apps/Files';
import { DataSettings } from './apps/DataSettings';
import { QuotaWidget } from './apps/QuotaWidget';
import { UsersDashboard } from './users/UsersDashboard';
import { UserEditor } from './users/UserEditor';
import { BulkImportModal } from './users/BulkImportModal';
import { RolesDashboard } from './roles/RolesDashboard';
import { RoleEditor } from './roles/RoleEditor';
import { EncodePage } from './encode/EncodePage';

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const ROW_RESPONSE = {
  submission_id: 'srv-a',
  client_submission_id: 'cli-a',
  submitted_at_server: '2026-05-01T12:30:00.000Z',
  submitted_at_client: '2026-05-01T12:00:00.000Z',
  source: 'pwa',
  spec_version: '1',
  app_version: '2.0.2',
  hcw_id: 'hcw-001',
  facility_id: 'fac-1',
  device_fingerprint: 'fp',
  status: 'stored',
  values_json: '{"q1":"yes"}',
  submission_lat: 14.5,
  submission_lng: 121.0,
  source_path: 'self_admin',
  encoded_by: '',
  encoded_at: '',
};

/** A fetch stand-in that routes each authenticated GET to a valid sample shape. */
function routingFetch(): typeof fetch {
  return (async (input: RequestInfo | URL) => {
    const u = String(input);
    // Detail (has an id segment after /responses/) must be checked before the list.
    if (/\/data\/responses\/[^/?]+/.test(u)) return json(ROW_RESPONSE);
    if (u.includes('/data/responses'))
      return json({ rows: [ROW_RESPONSE], total: 1, has_more: false });
    if (u.includes('/data/audit'))
      return json({
        rows: [
          {
            audit_id: 'aud-1',
            occurred_at_server: '2026-05-01T12:30:00.000Z',
            event_type: 'admin_login',
            hcw_id: '',
            facility_id: '',
            actor_username: 'kidd_admin',
            actor_role: 'Administrator',
            event_resource: '/admin/api/login',
            event_payload_json: '{"ip":"x"}',
            request_id: 'req-1',
          },
        ],
        total: 1,
        has_more: false,
      });
    if (u.includes('/data/dlq'))
      return json({
        rows: [
          {
            dlq_id: 'dlq-1',
            received_at_server: '2026-05-01T12:30:00.000Z',
            client_submission_id: 'cli-x',
            reason: 'schema drift',
            payload_json: '{"a":1}',
          },
        ],
        total: 1,
        has_more: false,
      });
    if (u.includes('/data/hcws'))
      return json({
        rows: [
          {
            hcw_id: 'hcw-001',
            facility_id: 'fac-1',
            facility_name: 'RHU One',
            status: 'enrolled',
            created_at: '2026-05-01T00:00:00.000Z',
            enrollment_token_jti: 'jti-1',
          },
        ],
        total: 1,
        has_more: false,
      });
    if (u.includes('/report/sync'))
      return json({
        level: 'region',
        pivot: [
          {
            key: 'Region I',
            submitted: 10,
            expected: 20,
            percent_complete: 50,
            last_submitted_at: '2026-05-01T12:30:00.000Z',
          },
        ],
        totals: { submitted: 10, expected: 20, keys: 1 },
      });
    if (u.includes('/report/map'))
      return json({
        markers: [
          {
            submission_id: 'srv-a',
            hcw_id: 'hcw-001',
            facility_id: 'fac-1',
            lat: 14.5,
            lng: 121.0,
            submitted_at: '2026-05-01T12:30:00.000Z',
          },
        ],
        no_gps_count: 2,
      });
    if (u.includes('/apps/version'))
      return json({
        pwa_version: '2.0.2',
        pwa_build_sha: 'abc1234',
        worker_version: '2.1.0',
        form_revisions: [],
        total_submissions: 42,
        last_pages_deploy_at: '2026-05-01T00:00:00.000Z',
      });
    if (u.includes('/apps/quota'))
      return json({ date_utc: '2026-06-02', count: 1200, cap: 20000, percent: 6 });
    if (u.includes('/apps/data-settings'))
      return json({
        settings: [
          {
            setting_id: 'set-1',
            instrument: 'F2',
            included_columns: '*',
            interval_minutes: 60,
            next_run_at: '2026-06-02T13:00:00.000Z',
            output_path_template: 'exports/f2-{date}.csv',
            enabled: true,
            last_run_status: 'ok',
          },
        ],
        total: 1,
      });
    if (u.includes('/apps/kill-switch')) return json({ kill_switch: false });
    if (u.includes('/apps/files'))
      return json({
        files: [
          {
            file_id: 'f-1',
            filename: 'roster.pdf',
            content_type: 'application/pdf',
            size_bytes: 1024,
            uploaded_by: 'kidd_admin',
            uploaded_at: '2026-05-01T00:00:00.000Z',
          },
        ],
        total: 1,
      });
    if (u.includes('/dashboards/users'))
      return json({
        users: [
          {
            username: 'kidd_admin',
            first_name: 'Kidd',
            last_name: 'Admin',
            role_name: 'Administrator',
            email: 'k@example.org',
          },
        ],
        total: 1,
      });
    if (u.includes('/dashboards/roles'))
      return json({
        roles: [{ name: 'Administrator', is_builtin: true, version: 1, dash_data: true }],
        total: 1,
      });
    return json({});
  }) as unknown as typeof fetch;
}

function wrap(ui: React.ReactNode): React.ReactElement {
  return (
    <AdminAuthProvider>
      <RouterProvider>{ui}</RouterProvider>
    </AdminAuthProvider>
  );
}

/** Render, wait for the loaded surface, then assert zero axe violations. */
async function auditClean(ui: React.ReactNode, ready?: () => Promise<unknown>): Promise<void> {
  const { container } = render(wrap(ui));
  if (ready) await ready();
  else await waitFor(() => expect(screen.queryByText(/Loading/)).toBeNull());
  expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
}

const noop = (): void => undefined;
const api = 'https://w.example';

describe('admin authenticated-state a11y (#273)', () => {
  // ---- Data dashboard + tabs ----
  it('Data dashboard shell (Responses default tab)', async () => {
    await auditClean(<DataDashboard apiBaseUrl={api} fetchImpl={routingFetch()} />, () =>
      screen.findByText('hcw-001'),
    );
  });

  it('Audit tab', async () => {
    await auditClean(<AuditTab apiBaseUrl={api} fetchImpl={routingFetch()} />, () =>
      screen.findByText('admin_login'),
    );
  });

  it('DLQ tab', async () => {
    await auditClean(<DLQTab apiBaseUrl={api} fetchImpl={routingFetch()} />, () =>
      screen.findByText('schema drift'),
    );
  });

  it('HCWs tab', async () => {
    await auditClean(<HCWsTab apiBaseUrl={api} fetchImpl={routingFetch()} />, () =>
      screen.findByText('RHU One'),
    );
  });

  it('Response detail', async () => {
    await auditClean(
      <ResponseDetail apiBaseUrl={api} submissionId="srv-a" fetchImpl={routingFetch()} />,
      () => screen.findAllByText('hcw-001'),
    );
  });

  it('Create HCW modal', async () => {
    await auditClean(
      <CreateHCWModal apiBaseUrl={api} fetchImpl={routingFetch()} onClose={noop} onCreated={noop} />,
      () => screen.findByRole('dialog'),
    );
  });

  it('Reissue token modal', async () => {
    await auditClean(
      <ReissueTokenModal apiBaseUrl={api} fetchImpl={routingFetch()} hcwId="hcw-001" onClose={noop} />,
      () => screen.findByRole('dialog'),
    );
  });

  // ---- Report dashboard + tabs ----
  it('Report dashboard shell (Sync default tab)', async () => {
    await auditClean(<ReportDashboard apiBaseUrl={api} fetchImpl={routingFetch()} />, () =>
      screen.findByText('Region I'),
    );
  });

  it('Map report (leaflet stubbed)', async () => {
    await auditClean(<MapReport apiBaseUrl={api} fetchImpl={routingFetch()} />);
  });

  // ---- Apps & Settings dashboard + sub-tabs ----
  it('Apps & Settings shell (Versioning default tab)', async () => {
    await auditClean(<AppsDashboard apiBaseUrl={api} fetchImpl={routingFetch()} />, () =>
      screen.findByText('abc1234'),
    );
  });

  it('Files panel', async () => {
    await auditClean(<Files apiBaseUrl={api} fetchImpl={routingFetch()} />, () =>
      screen.findByText('roster.pdf'),
    );
  });

  it('Data Settings panel', async () => {
    await auditClean(<DataSettings apiBaseUrl={api} fetchImpl={routingFetch()} />, () =>
      screen.findByText(/exports\/f2-\{date\}\.csv/),
    );
  });

  it('Quota widget', async () => {
    await auditClean(<QuotaWidget apiBaseUrl={api} fetchImpl={routingFetch()} />);
  });

  // ---- Users dashboard + editors ----
  it('Users dashboard', async () => {
    await auditClean(<UsersDashboard apiBaseUrl={api} fetchImpl={routingFetch()} />, () =>
      screen.findByText('kidd_admin'),
    );
  });

  it('User editor (create)', async () => {
    await auditClean(
      <UserEditor
        apiBaseUrl={api}
        fetchImpl={routingFetch()}
        mode="create"
        roles={[{ name: 'Administrator' }]}
        onClose={noop}
        onSaved={noop}
      />,
      () => screen.findByRole('dialog'),
    );
  });

  it('Bulk import modal', async () => {
    await auditClean(
      <BulkImportModal apiBaseUrl={api} fetchImpl={routingFetch()} onClose={noop} onImported={noop} />,
      () => screen.findByRole('dialog'),
    );
  });

  // ---- Roles dashboard + editor ----
  it('Roles dashboard', async () => {
    await auditClean(<RolesDashboard apiBaseUrl={api} fetchImpl={routingFetch()} />, () =>
      screen.findAllByText(/Administrator/),
    );
  });

  it('Role editor (create)', async () => {
    await auditClean(
      <RoleEditor
        apiBaseUrl={api}
        fetchImpl={routingFetch()}
        mode="create"
        onClose={noop}
        onSaved={noop}
      />,
      () => screen.findByRole('dialog'),
    );
  });

  // ---- Encode flow (mounts the HCW MultiSectionForm shell) ----
  it('Encode page (paper-encoder + MultiSectionForm shell)', async () => {
    await auditClean(<EncodePage apiBaseUrl={api} hcwId="hcw-001" fetchImpl={routingFetch()} />, () =>
      screen.findByText(/Encoding for HCW/),
    );
  });
});
