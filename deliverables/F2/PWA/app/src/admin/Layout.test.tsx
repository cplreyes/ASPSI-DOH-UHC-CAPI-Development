/**
 * Regression tests for the F2 Admin Portal sidebar Layout.
 *
 * #328 (UAT R3, 5A.19): the sidebar username rendered as a plain <p>, so
 * clicking it only selected the text — there was no UI path to the
 * change-password screen for a user not under a forced first-login rotation.
 * These tests assert the username is now a link to /admin/me/change-password.
 */
import { describe, expect, it } from 'vitest';
import { useEffect } from 'react';
import { render, screen } from '@testing-library/react';
import { Layout } from './Layout';
import { AdminAuthProvider, useAdminAuth } from './lib/auth-context';
import { RouterProvider } from './lib/pages-router';

/** Primes the auth context to an authenticated state before children render. */
function AuthPrime({ children }: { children: React.ReactNode }): JSX.Element | null {
  const { setAuth, isAuthenticated } = useAdminAuth();
  useEffect(() => {
    setAuth('kidd_admin', {
      token: 'test-token',
      role: 'Administrator',
      role_version: 0,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      password_must_change: false,
    });
  }, [setAuth]);
  return isAuthenticated ? <>{children}</> : null;
}

function renderAuthedLayout() {
  return render(
    <AdminAuthProvider>
      <RouterProvider>
        <AuthPrime>
          <Layout>
            <section>
              <h2>Content</h2>
            </section>
          </Layout>
        </AuthPrime>
      </RouterProvider>
    </AdminAuthProvider>,
  );
}

describe('<Layout /> — #328 username change-password entry point', () => {
  it('renders the username as a link to the change-password page', () => {
    renderAuthedLayout();
    // Desktop sidebar footer + mobile header both render the username link
    // (CSS hides one per viewport; both are in the DOM under JSDOM).
    const links = screen.getAllByRole('link', { name: /kidd_admin.*change password/i });
    expect(links.length).toBeGreaterThanOrEqual(1);
    for (const link of links) {
      expect(link).toHaveAttribute('href', '/admin/me/change-password');
    }
  });

  it('keeps Sign out as a separate control', () => {
    renderAuthedLayout();
    expect(screen.getAllByRole('button', { name: /sign out/i }).length).toBeGreaterThanOrEqual(1);
  });
});
