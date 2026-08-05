/**
 * HCWs tab — filter-bar tests (2026-07-17 rollout): facility dropdown,
 * created-date window, Clear filters, URL write-back.
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HCWsTab } from './HCWsTab';
import { AdminAuthProvider } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

const LPHBAY = { facility_id: '040340210', facility_name: 'LPH-Bay District Hospital' };

/** Routes the two tab fetches; captures the /data/hcws list URLs. */
function mkFetch(list: unknown = { rows: [], total: 0, has_more: false }) {
  const listUrls: string[] = [];
  const fetchImpl = vi.fn(async (url: unknown) => {
    const u = String(url);
    if (u.includes('/data/facility-options')) {
      return jsonResponse({ rows: [LPHBAY], total: 1 });
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
        <HCWsTab apiBaseUrl="https://w.example" fetchImpl={fetchImpl} />
      </RouterProvider>
    </AdminAuthProvider>,
  );
}

describe('<HCWsTab /> filter bar', () => {
  it('facility dropdown filters the list; date range lands in the API query', async () => {
    window.history.replaceState({}, '', '/admin/data?tab=hcws');
    const { fetchImpl, listUrls } = mkFetch();
    renderTab(fetchImpl);
    const select = await screen.findByLabelText(/^facility$/i);
    await waitFor(() =>
      expect(screen.getByRole('option', { name: 'LPH-Bay District Hospital' })).toBeInTheDocument(),
    );
    await userEvent.selectOptions(select, '040340210');
    await waitFor(() =>
      expect(listUrls.some((u) => u.includes('facility_id=040340210'))).toBe(true),
    );
    fireEvent.change(screen.getByLabelText(/^from$/i), { target: { value: '2026-07-16' } });
    await waitFor(() => expect(listUrls.some((u) => u.includes('from=2026-07-16'))).toBe(true));
    // Shareable URL write-back keeps the tab param.
    expect(window.location.search).toContain('tab=hcws');
    expect(window.location.search).toContain('facility_id=040340210');
    window.history.replaceState({}, '', '/admin');
  });

  it('Clear filters resets a deep-linked view and hides itself', async () => {
    window.history.replaceState({}, '', '/admin/data?tab=hcws&facility_id=040340210&status=enrolled&q=sr-');
    const { fetchImpl, listUrls } = mkFetch();
    renderTab(fetchImpl);
    const clear = await screen.findByRole('button', { name: /clear filters/i });
    await userEvent.click(clear);
    await waitFor(() => {
      const last = listUrls[listUrls.length - 1]!;
      expect(last).not.toMatch(/[?&]status=/);
      expect(last).not.toMatch(/[?&]q=/);
      expect(last).not.toMatch(/[?&]facility_id=/);
    });
    expect(screen.queryByRole('button', { name: /clear filters/i })).not.toBeInTheDocument();
    window.history.replaceState({}, '', '/admin');
  });
});
