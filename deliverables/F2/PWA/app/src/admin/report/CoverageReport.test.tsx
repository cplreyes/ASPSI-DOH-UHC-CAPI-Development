/**
 * Coverage report (spec F2-Coverage-Report-2026-07-17): render, filters →
 * query + URL, drill-down hrefs, null-target rendering, orphan row, RBAC error.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CoverageReport } from './CoverageReport';
import { AdminAuthProvider } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const facRow = {
  key: '040340210',
  label: 'LPH-Bay District Hospital',
  facilities: 1,
  links_active: 1,
  target: 30,
  started: 1,
  submitted: 2,
  refusals: 1,
  refusal_rate: 33.3,
  coverage_pct: 7,
  paper_encoded: 1,
  last_activity: '2026-07-16T13:19:19.000Z',
};
const noTargetRow = {
  key: '050110001',
  label: 'RHU Daraga I',
  facilities: 1,
  links_active: 0,
  target: null,
  started: 0,
  submitted: 1,
  refusals: 0,
  refusal_rate: 0,
  coverage_pct: null,
  paper_encoded: 0,
  last_activity: '2026-07-16T10:00:00.000Z',
};
const orphanRow = {
  key: '(not in master)',
  label: '(not in master)',
  facilities: 0,
  links_active: 0,
  target: null,
  started: 0,
  submitted: 1,
  refusals: 0,
  refusal_rate: 0,
  coverage_pct: null,
  paper_encoded: 0,
  last_activity: '2026-07-16T09:00:00.000Z',
};
const totals = {
  ...facRow,
  key: 'TOTAL',
  label: 'TOTAL',
  facilities: 2,
  submitted: 4,
  target: 30,
  coverage_pct: 13,
};

function listFetch(level = 'facility') {
  const calls: string[] = [];
  const fetchImpl = vi.fn(async (url: RequestInfo | URL) => {
    calls.push(String(url));
    return jsonResponse({ level, rows: [facRow, noTargetRow, orphanRow], totals });
  }) as unknown as typeof fetch;
  return { fetchImpl, calls };
}

function renderReport(fetchImpl: typeof fetch) {
  render(
    <AdminAuthProvider>
      <RouterProvider>
        <CoverageReport apiBaseUrl="https://w.example" fetchImpl={fetchImpl} />
      </RouterProvider>
    </AdminAuthProvider>,
  );
}

describe('<CoverageReport />', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/admin/report?tab=coverage');
  });

  it('renders rows, the totals row, and "—" for null target/coverage', async () => {
    const { fetchImpl } = listFetch();
    renderReport(fetchImpl);
    await waitFor(() => expect(screen.getByTestId('coverage-row-040340210')).toBeInTheDocument());
    const a = screen.getByTestId('coverage-row-040340210');
    expect(a.textContent).toContain('LPH-Bay District Hospital');
    expect(a.textContent).toContain('7%');
    expect(a.textContent).toContain('1 (33.3%)');
    const b = screen.getByTestId('coverage-row-050110001');
    expect(b.textContent).toContain('—'); // null target renders em dash
    expect(screen.getByTestId('coverage-totals').textContent).toContain('TOTAL');
    // Orphan row surfaces with the add-to-master chip.
    expect(screen.getByTestId('coverage-row-(not in master)').textContent).toMatch(/add to master/i);
  });

  it('drill-down hrefs: facility → Responses/HCWs, orphan chip → Facilities', async () => {
    const { fetchImpl } = listFetch();
    renderReport(fetchImpl);
    await waitFor(() => expect(screen.getByTestId('coverage-geo-040340210')).toBeInTheDocument());
    expect(screen.getByTestId('coverage-geo-040340210')).toHaveAttribute(
      'href',
      '/admin/data?tab=responses&facility_id=040340210',
    );
    expect(screen.getByTestId('coverage-started-040340210')).toHaveAttribute(
      'href',
      '/admin/data?tab=hcws&facility_id=040340210&status=enrolled&q=sr-',
    );
  });

  it('region rows link to the Facilities page pre-filtered', async () => {
    const regionRow = { ...facRow, key: 'Region V (Bicol Region)', label: 'Region V (Bicol Region)' };
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ level: 'region', rows: [regionRow], totals }),
    ) as unknown as typeof fetch;
    renderReport(fetchImpl);
    await waitFor(() =>
      expect(screen.getByTestId('coverage-geo-Region V (Bicol Region)')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('coverage-geo-Region V (Bicol Region)')).toHaveAttribute(
      'href',
      '/admin/facilities?region=Region%20V%20(Bicol%20Region)',
    );
  });

  it('level pills and the archived toggle drive the fetch query and the URL', async () => {
    const { fetchImpl, calls } = listFetch();
    const user = userEvent.setup();
    renderReport(fetchImpl);
    await waitFor(() => expect(fetchImpl).toHaveBeenCalled());
    expect(calls[0]).toContain('level=region');
    await user.click(screen.getByTestId('coverage-level-facility'));
    await waitFor(() => expect(calls.some((c) => c.includes('level=facility'))).toBe(true));
    expect(window.location.search).toContain('level=facility');
    expect(window.location.search).toContain('tab=coverage'); // tab param preserved
    await user.click(screen.getByTestId('coverage-archived'));
    await waitFor(() => expect(calls.some((c) => c.includes('include_archived=true'))).toBe(true));
    expect(window.location.search).toContain('archived=1');
  });

  it('surfaces E_PERM_DENIED with the dash_report message', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ ok: false, error: { code: 'E_PERM_DENIED', message: 'denied' } }, 403),
    ) as unknown as typeof fetch;
    renderReport(fetchImpl);
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByRole('alert').textContent).toMatch(/dash_report/i);
  });
});
