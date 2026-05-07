import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ResponsesTab } from './ResponsesTab';
import { AdminAuthProvider } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
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

  it('does NOT auto-apply a date filter on cold load (UAT R2 #78)', async () => {
    let captured: string | null = null;
    const fetchImpl = vi.fn(async (url) => {
      captured = String(url);
      return jsonResponse({ rows: [], total: 0, has_more: false });
    }) as unknown as typeof fetch;
    renderTab(fetchImpl);
    await waitFor(() => expect(fetchImpl).toHaveBeenCalled());
    expect(captured).not.toMatch(/from=\d{4}-\d{2}-\d{2}/);
    expect(captured).toMatch(/limit=200/);
  });
});
