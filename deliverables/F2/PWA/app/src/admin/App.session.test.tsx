/**
 * Reload survival for the admin portal (2026-07-24).
 *
 * Operators reported being signed out by every browser refresh. These tests
 * exercise the whole shell rather than the auth context alone, because the
 * regression risk is in the render path: AdminRoot decides between Login and
 * the requested page during the first render, so a session that hydrates one
 * render late still loses the user's deep link.
 *
 * Rendering AdminApp fresh with a pre-seeded sessionStorage is the closest
 * jsdom equivalent of a page reload — same origin, same URL, brand new React
 * tree with no in-memory state carried over.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import AdminApp from './App';

const STORAGE_KEY = 'f2.admin.session.v1';

function seedSession(overrides: Record<string, unknown> = {}): void {
  sessionStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      v: 1,
      token: 'tok.tok.tok',
      username: 'se_001',
      role: 'Administrator',
      roleVersion: 1,
      expiresAt: Math.floor(Date.now() / 1000) + 4 * 60 * 60,
      passwordMustChange: false,
      permissions: null,
      ...overrides,
    }),
  );
}

// Every admin list endpoint answers with the same empty envelope — these tests
// assert on which screen renders, not on any panel's contents.
const emptyFetch = vi.fn(async () =>
  new Response(JSON.stringify({ rows: [], total: 0 }), {
    status: 200,
    headers: { 'content-type': 'application/json' },
  }),
) as unknown as typeof fetch;

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<AdminApp apiBaseUrl="https://test.invalid" fetchImpl={emptyFetch} />);
}

describe('admin portal session across a reload', () => {
  beforeEach(() => {
    sessionStorage.clear();
    window.history.pushState({}, '', '/admin');
  });

  it('keeps the operator on their page after a refresh', async () => {
    seedSession();
    renderAt('/admin/data');

    // Sidebar and mobile header both carry the brand — findAll, not find.
    expect((await screen.findAllByText('HCW Survey Console')).length).toBeGreaterThan(0);
    expect(screen.queryByRole('heading', { name: /^sign in$/i })).not.toBeInTheDocument();
  });

  it('keeps a deep link after a refresh instead of bouncing to login', async () => {
    seedSession();
    renderAt('/admin/facilities');

    expect((await screen.findAllByText('HCW Survey Console')).length).toBeGreaterThan(0);
    expect(window.location.pathname).toBe('/admin/facilities');
  });

  it('shows the login screen when there is no stored session', async () => {
    renderAt('/admin/data');

    expect(await screen.findByRole('heading', { name: /^sign in$/i })).toBeInTheDocument();
  });

  it('shows the login screen when the stored session has expired', async () => {
    seedSession({ expiresAt: Math.floor(Date.now() / 1000) - 60 });
    renderAt('/admin/data');

    expect(await screen.findByRole('heading', { name: /^sign in$/i })).toBeInTheDocument();
    expect(sessionStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it('sends a restored session that still owes a password rotation to the rotation page', async () => {
    // Before persistence this was unreachable: login routed these users
    // straight to the change-password page. A restored session can now land
    // anywhere, and every gated endpoint would 403 until they rotate.
    seedSession({ passwordMustChange: true });
    renderAt('/admin/data');

    expect(await screen.findByRole('heading', { name: /change password/i })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/admin/me/change-password');
  });
});
