import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ResponsesTab } from './ResponsesTab';
import { AdminAuthProvider } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

/** Mock both tab fetches: /data/facility-options gets `options`, everything
 *  else (the /data/responses list) gets `list`. Captures list URLs. */
function mkFetch(list: unknown, options: Array<{ facility_id: string; facility_name: string }> = []) {
  const listUrls: string[] = [];
  const fetchImpl = vi.fn(async (url: unknown) => {
    const u = String(url);
    if (u.includes('/data/facility-options')) {
      return jsonResponse({ rows: options, total: options.length });
    }
    listUrls.push(u);
    return jsonResponse(list);
  }) as unknown as typeof fetch;
  return { fetchImpl, listUrls };
}

function renderTab(fetchImpl: typeof fetch) {
  return render(
    <AdminAuthProvider>
      <RouterProvider>
        <ResponsesTab apiBaseUrl="https://w.example" fetchImpl={fetchImpl} />
      </RouterProvider>
    </AdminAuthProvider>,
  );
}

describe('<ResponsesTab />', () => {
  it('renders the empty state when AS returns no rows', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ rows: [], total: 0, has_more: false }),
    ) as unknown as typeof fetch;
    renderTab(fetchImpl);
    await waitFor(() => {
      expect(screen.getByText(/no responses match/i)).toBeInTheDocument();
    });
  });

  it('renders rows in a hairline-divided table', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({
        rows: [
          {
            submission_id: 'srv-a',
            client_submission_id: 'cli-a',
            submitted_at_server: '2026-05-01T12:30:00.000Z',
            hcw_id: 'hcw-001',
            facility_id: 'fac-1',
            status: 'stored',
            source_path: 'self_admin',
          },
          {
            submission_id: 'srv-b',
            client_submission_id: 'cli-b',
            submitted_at_server: '2026-05-01T11:00:00.000Z',
            hcw_id: 'hcw-002',
            facility_id: 'fac-2',
            status: 'rejected',
            source_path: 'paper_encoded',
          },
        ],
        total: 2,
        has_more: false,
      }),
    ) as unknown as typeof fetch;
    renderTab(fetchImpl);
    await waitFor(() => {
      expect(screen.getByText('hcw-001')).toBeInTheDocument();
      expect(screen.getByText('hcw-002')).toBeInTheDocument();
    });
    expect(screen.getByText(/2 responses/i)).toBeInTheDocument();
    // Both rows render with an action link each — most reliable row marker.
    expect(screen.getAllByRole('link', { name: /^view$/i })).toHaveLength(2);
    // The rejected row surfaces in error red (text node has the value).
    expect(screen.getByText('rejected')).toBeInTheDocument();
  });

  it('surfaces a typed error on E_BACKEND', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ ok: false, error: { code: 'E_BACKEND', message: 'AS down' } }, 502),
    ) as unknown as typeof fetch;
    renderTab(fetchImpl);
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/backend unavailable/i);
    });
  });

  // R3 #296: date filters default EMPTY. On initial load (no URL params)
  // every response shows unfiltered — no auto-fill `from` that silently
  // hides older submissions. A `from` is only sent once the user picks one.
  it('does not attach an implicit date filter on initial load (#296)', async () => {
    const { fetchImpl, listUrls } = mkFetch({ rows: [], total: 0, has_more: false });
    renderTab(fetchImpl);
    await waitFor(() => expect(listUrls.length).toBeGreaterThan(0));
    expect(listUrls[0]).not.toMatch(/[?&]from=/);
    expect(listUrls[0]).toMatch(/limit=200/);
  });

  it('shows the QN column and renders sr- ids as "self-registered" (F2-Facilities-Page spec)', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({
        rows: [
          {
            submission_id: 'srv-a',
            client_submission_id: 'cli-a',
            submitted_at_server: '2026-07-16T07:35:00.000Z',
            hcw_id: 'sr-b9493fe6-7977-40ee-aa56-f9a711058f2a',
            facility_id: '040340210',
            status: 'stored',
            source_path: 'self_admin',
            qn: '040340210102',
          },
          {
            submission_id: 'srv-b',
            client_submission_id: 'cli-b',
            submitted_at_server: '2026-07-16T06:53:00.000Z',
            hcw_id: 'LPHBAY-HCW-01',
            facility_id: '040340210',
            status: 'refusal',
            source_path: 'self_admin',
            qn: '040340210101',
          },
        ],
        total: 2,
        has_more: false,
      }),
    ) as unknown as typeof fetch;
    renderTab(fetchImpl);
    await waitFor(() => expect(screen.getByText('040340210102')).toBeInTheDocument());
    expect(screen.getByText('self-registered')).toBeInTheDocument();
    expect(screen.queryByText(/sr-b9493fe6/)).not.toBeInTheDocument();
    expect(screen.getByText('LPHBAY-HCW-01')).toBeInTheDocument();
    expect(screen.getByText('040340210101')).toBeInTheDocument();
  });

  it('honors an explicit ?status= deep-link param (Facilities-page counts)', async () => {
    window.history.replaceState({}, '', '/admin/data?tab=responses&facility_id=040340210&status=refusal');
    const { fetchImpl, listUrls } = mkFetch({ rows: [], total: 0, has_more: false });
    renderTab(fetchImpl);
    await waitFor(() => expect(listUrls.length).toBeGreaterThan(0));
    expect(listUrls[0]).toMatch(/[?&]status=refusal/);
    expect(listUrls[0]).toMatch(/[?&]facility_id=040340210/);
    window.history.replaceState({}, '', '/admin');
  });

  it('honors an explicit ?from= URL param when present', async () => {
    window.history.replaceState({}, '', '/admin?tab=responses&from=2026-05-01');
    const { fetchImpl, listUrls } = mkFetch({ rows: [], total: 0, has_more: false });
    renderTab(fetchImpl);
    await waitFor(() => expect(listUrls.length).toBeGreaterThan(0));
    expect(listUrls[0]).toMatch(/[?&]from=2026-05-01/);
    window.history.replaceState({}, '', '/admin');
  });

  // --- 2026-07-17 filter bar: facility + status dropdowns, CAPI pill, clear ---

  const LPHBAY = { facility_id: '040340210', facility_name: 'LPH-Bay District Hospital' };
  const RHU = { facility_id: '050110001', facility_name: 'RHU Daraga I' };

  it('facility dropdown lists options by name and filters the list on select', async () => {
    const { fetchImpl, listUrls } = mkFetch({ rows: [], total: 0, has_more: false }, [LPHBAY, RHU]);
    renderTab(fetchImpl);
    const select = await screen.findByLabelText(/^facility$/i);
    await waitFor(() =>
      expect(screen.getByRole('option', { name: 'LPH-Bay District Hospital' })).toBeInTheDocument(),
    );
    await userEvent.selectOptions(select, '040340210');
    await waitFor(() =>
      expect(listUrls.some((u) => u.includes('facility_id=040340210'))).toBe(true),
    );
    window.history.replaceState({}, '', '/admin');
  });

  it('status dropdown filters and is mutually exclusive with the Errors-only pill', async () => {
    const { fetchImpl, listUrls } = mkFetch({ rows: [], total: 0, has_more: false });
    renderTab(fetchImpl);
    const select = await screen.findByLabelText(/^status$/i);
    await userEvent.selectOptions(select, 'refusal');
    await waitFor(() => expect(listUrls.some((u) => u.includes('status=refusal'))).toBe(true));
    // Errors-only wins by clearing the dropdown (never a silent precedence fight).
    await userEvent.click(screen.getByRole('button', { name: /errors only/i }));
    await waitFor(() => expect(listUrls.some((u) => u.includes('status=rejected'))).toBe(true));
    expect((select as HTMLSelectElement).value).toBe('');
    // And picking a status turns the pill back off.
    await userEvent.selectOptions(select, 'stored');
    await waitFor(() => expect(listUrls.some((u) => u.includes('status=stored'))).toBe(true));
    expect(listUrls[listUrls.length - 1]).not.toMatch(/status=rejected/);
    window.history.replaceState({}, '', '/admin');
  });

  it('deep-linked facility_id not in options still shows as a selectable value', async () => {
    window.history.replaceState({}, '', '/admin/data?tab=responses&facility_id=999999999');
    const { fetchImpl } = mkFetch({ rows: [], total: 0, has_more: false }, [LPHBAY]);
    renderTab(fetchImpl);
    const select = await screen.findByLabelText(/^facility$/i);
    await waitFor(() => expect((select as HTMLSelectElement).value).toBe('999999999'));
    expect(screen.getByRole('option', { name: '999999999' })).toBeInTheDocument();
    window.history.replaceState({}, '', '/admin');
  });

  it('Clear filters resets everything and hides itself when nothing is active', async () => {
    window.history.replaceState({}, '', '/admin/data?tab=responses&status=refusal&q=lph');
    const { fetchImpl, listUrls } = mkFetch({ rows: [], total: 0, has_more: false });
    renderTab(fetchImpl);
    const clear = await screen.findByRole('button', { name: /clear filters/i });
    await userEvent.click(clear);
    await waitFor(() => {
      const last = listUrls[listUrls.length - 1]!;
      expect(last).not.toMatch(/[?&]status=/);
      expect(last).not.toMatch(/[?&]q=/);
    });
    expect(screen.queryByRole('button', { name: /clear filters/i })).not.toBeInTheDocument();
    window.history.replaceState({}, '', '/admin');
  });
});
