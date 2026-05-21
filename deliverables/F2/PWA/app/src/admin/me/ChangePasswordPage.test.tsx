/**
 * Regression tests for ChangePasswordPage.
 *
 * #328: the page renders chrome-less (no sidebar). A user who reaches it
 * voluntarily (via the sidebar username link) needs an escape hatch — the
 * "Cancel — back to portal" link. A forced first-login rotation
 * (password_must_change) must NOT show the escape hatch.
 */
import { describe, expect, it } from 'vitest';
import { useEffect } from 'react';
import { render, screen } from '@testing-library/react';
import { ChangePasswordPage } from './ChangePasswordPage';
import { AdminAuthProvider, useAdminAuth } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

/** Primes the auth context, optionally with password_must_change set. */
function AuthPrime({
  mustChange,
  children,
}: {
  mustChange: boolean;
  children: React.ReactNode;
}): JSX.Element | null {
  const { setAuth, isAuthenticated } = useAdminAuth();
  useEffect(() => {
    setAuth('kidd_admin', {
      token: 'test-token',
      role: 'Administrator',
      role_version: 0,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      password_must_change: mustChange,
    });
  }, [setAuth, mustChange]);
  return isAuthenticated ? <>{children}</> : null;
}

function renderPage(mustChange: boolean) {
  const noopFetch = (() => Promise.reject(new Error('not used'))) as unknown as typeof fetch;
  return render(
    <AdminAuthProvider>
      <RouterProvider>
        <AuthPrime mustChange={mustChange}>
          <ChangePasswordPage apiBaseUrl="https://worker.example" fetchImpl={noopFetch} />
        </AuthPrime>
      </RouterProvider>
    </AdminAuthProvider>,
  );
}

describe('<ChangePasswordPage /> — #328 escape hatch', () => {
  it('shows a Cancel link back to the portal for a voluntary visit', () => {
    renderPage(false);
    const cancel = screen.getByRole('link', { name: /cancel.*back to portal/i });
    expect(cancel).toHaveAttribute('href', '/admin/data');
  });

  it('hides the Cancel link under a forced password_must_change rotation', () => {
    renderPage(true);
    expect(screen.queryByRole('link', { name: /cancel/i })).not.toBeInTheDocument();
    // Forced-mode copy still renders.
    expect(screen.getByText(/requires a password change/i)).toBeInTheDocument();
  });
});
