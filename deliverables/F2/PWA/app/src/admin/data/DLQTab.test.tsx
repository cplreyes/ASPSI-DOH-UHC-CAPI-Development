/**
 * DLQ tab — filter-bar tests (2026-07-17 rollout): Clear filters + URL
 * write-back (the DLQ bar stays dates + search only).
 */
import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DLQTab } from './DLQTab';
import { AdminAuthProvider } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

describe('<DLQTab /> filter bar', () => {
  it('Clear filters resets a deep-linked view, keeps tab=dlq in the URL', async () => {
    window.history.replaceState({}, '', '/admin/data?tab=dlq&from=2026-07-01&q=drift');
    const listUrls: string[] = [];
    const fetchImpl = vi.fn(async (url: unknown) => {
      listUrls.push(String(url));
      return jsonResponse({ rows: [], total: 0, has_more: false });
    }) as unknown as typeof fetch;
    render(
      <AdminAuthProvider>
        <RouterProvider>
          <DLQTab apiBaseUrl="https://w.example" fetchImpl={fetchImpl} />
        </RouterProvider>
      </AdminAuthProvider>,
    );
    const clear = await screen.findByRole('button', { name: /clear filters/i });
    await userEvent.click(clear);
    await waitFor(() => {
      const last = listUrls[listUrls.length - 1]!;
      expect(last).not.toMatch(/[?&]from=/);
      expect(last).not.toMatch(/[?&]q=/);
    });
    expect(screen.queryByRole('button', { name: /clear filters/i })).not.toBeInTheDocument();
    expect(window.location.search).toContain('tab=dlq');
    window.history.replaceState({}, '', '/admin');
  });
});
