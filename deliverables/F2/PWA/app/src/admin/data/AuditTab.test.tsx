/**
 * Audit tab — filter-bar tests (2026-07-17 rollout): event-type dropdown fed
 * by /data/audit-event-types, Clear filters, URL write-back.
 */
import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuditTab } from './AuditTab';
import { AdminAuthProvider } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

/** Routes the two tab fetches; captures the /data/audit list URLs. */
function mkFetch(eventTypes: string[] = ['admin_kill_switch_set', 'admin_login']) {
  const listUrls: string[] = [];
  const fetchImpl = vi.fn(async (url: unknown) => {
    const u = String(url);
    if (u.includes('/data/audit-event-types')) {
      return jsonResponse({ rows: eventTypes, total: eventTypes.length });
    }
    listUrls.push(u);
    return jsonResponse({ rows: [], total: 0, has_more: false });
  }) as unknown as typeof fetch;
  return { fetchImpl, listUrls };
}

function renderTab(fetchImpl: typeof fetch) {
  return render(
    <AdminAuthProvider>
      <RouterProvider>
        <AuditTab apiBaseUrl="https://w.example" fetchImpl={fetchImpl} />
      </RouterProvider>
    </AdminAuthProvider>,
  );
}

describe('<AuditTab /> filter bar', () => {
  it('event-type dropdown lists live values and filters the list on select', async () => {
    window.history.replaceState({}, '', '/admin/data?tab=audit');
    const { fetchImpl, listUrls } = mkFetch();
    renderTab(fetchImpl);
    const select = await screen.findByLabelText(/^event type$/i);
    await waitFor(() =>
      expect(screen.getByRole('option', { name: 'admin_login' })).toBeInTheDocument(),
    );
    await userEvent.selectOptions(select, 'admin_login');
    await waitFor(() =>
      expect(listUrls.some((u) => u.includes('event_type=admin_login'))).toBe(true),
    );
    expect(window.location.search).toContain('tab=audit');
    window.history.replaceState({}, '', '/admin');
  });

  it('deep-linked event_type not in the live list still shows as selected', async () => {
    window.history.replaceState({}, '', '/admin/data?tab=audit&event_type=admin_retired_event');
    const { fetchImpl } = mkFetch(['admin_login']);
    renderTab(fetchImpl);
    const select = await screen.findByLabelText(/^event type$/i);
    await waitFor(() => expect((select as HTMLSelectElement).value).toBe('admin_retired_event'));
    window.history.replaceState({}, '', '/admin');
  });

  it('Clear filters resets everything and hides itself', async () => {
    window.history.replaceState({}, '', '/admin/data?tab=audit&event_type=admin_login&q=kidd');
    const { fetchImpl, listUrls } = mkFetch();
    renderTab(fetchImpl);
    const clear = await screen.findByRole('button', { name: /clear filters/i });
    await userEvent.click(clear);
    await waitFor(() => {
      const last = listUrls[listUrls.length - 1]!;
      expect(last).not.toMatch(/[?&]event_type=/);
      expect(last).not.toMatch(/[?&]q=/);
    });
    expect(screen.queryByRole('button', { name: /clear filters/i })).not.toBeInTheDocument();
    window.history.replaceState({}, '', '/admin');
  });
});
