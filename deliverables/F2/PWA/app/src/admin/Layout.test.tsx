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

/** Primes the auth context to an authenticated state before children render.
 * `permissions` is optional (omitted → the Worker sent none → null → show all). */
function AuthPrime({
  children,
  permissions,
}: {
  children: React.ReactNode;
  permissions?: Record<string, boolean>;
}): JSX.Element | null {
  const { setAuth, isAuthenticated } = useAdminAuth();
  useEffect(() => {
    setAuth('kidd_admin', {
      token: 'test-token',
      role: 'Administrator',
      role_version: 0,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      password_must_change: false,
      ...(permissions ? { permissions } : {}),
    });
  }, [setAuth, permissions]);
  return isAuthenticated ? <>{children}</> : null;
}

function renderAuthedLayout(permissions?: Record<string, boolean>) {
  return render(
    <AdminAuthProvider>
      <RouterProvider>
        {/* Conditional spread: under exactOptionalPropertyTypes, passing an
            explicit `undefined` to an optional prop is a type error. */}
        <AuthPrime {...(permissions ? { permissions } : {})}>
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

/** Count nav links (desktop + mobile both render under JSDOM) for an item label. */
function navLinkCount(label: string): number {
  return screen.queryAllByRole('link', { name: new RegExp(`^${label} —`) }).length;
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

describe('<Layout /> — FX-002 (#324) role-aware nav gating', () => {
  it('shows only the items the role permits, plus the always-on Help', () => {
    // A custom role granting only dash_data.
    renderAuthedLayout({ dash_data: true });
    expect(navLinkCount('Data')).toBeGreaterThanOrEqual(1);
    expect(navLinkCount('Help')).toBeGreaterThanOrEqual(1); // no requiredPerm → always
    // Everything the role lacks is hidden.
    expect(navLinkCount('Reports')).toBe(0); // dash_report
    expect(navLinkCount('Encode')).toBe(0); // dict_paper_encoded_up
    expect(navLinkCount('Apps & Settings')).toBe(0); // dash_apps
    expect(navLinkCount('Users')).toBe(0); // dash_users
    expect(navLinkCount('Roles')).toBe(0); // dash_roles
  });

  it('hides a group whose every item filters out (orphaned eyebrow header)', () => {
    // dash_data is in the Operate group, so Configure (apps/users/roles) is empty.
    renderAuthedLayout({ dash_data: true });
    expect(screen.getByText('Operate')).toBeInTheDocument();
    expect(screen.queryByText('Configure')).toBeNull();
  });

  it('shows everything when permissions are unknown (null → graceful degradation)', () => {
    // No permissions field → the Worker didn't send one; the server still
    // enforces 403, so the nav fails open (shows all) rather than hiding work.
    renderAuthedLayout();
    for (const label of ['Data', 'Reports', 'Encode', 'Apps & Settings', 'Users', 'Roles', 'Help']) {
      expect(navLinkCount(label)).toBeGreaterThanOrEqual(1);
    }
  });

  it('renders the full set for a perms map that grants everything', () => {
    renderAuthedLayout({
      dash_data: true, dash_report: true, dash_apps: true,
      dash_users: true, dash_roles: true, dict_paper_encoded_up: true,
    });
    for (const label of ['Data', 'Reports', 'Encode', 'Apps & Settings', 'Users', 'Roles', 'Help']) {
      expect(navLinkCount(label)).toBeGreaterThanOrEqual(1);
    }
  });
});
