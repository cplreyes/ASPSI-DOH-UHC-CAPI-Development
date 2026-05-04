/**
 * F2 Admin Portal — top-level admin app.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.14, Steps 5-6)
 *
 * Sets up RouterProvider + AdminAuthProvider, then routes between Login
 * and Layout-wrapped pages. The 8 dashboard routes (data, report, apps,
 * users, roles, encode, …) are placeholder stubs in this shell task —
 * Sprint 2 / Sprint 3 fill them in. Unauthenticated access to any
 * route except /admin/login redirects to /admin/login.
 */
import { useEffect, type ReactNode } from 'react';
import { RouterProvider, useRouter, matchRoute } from './lib/pages-router';
import { AdminAuthProvider, useAdminAuth } from './lib/auth-context';
import { Login } from './Login';
import { Layout } from './Layout';
import { EncodeQueue } from './encode/EncodeQueue';
import { EncodePage } from './encode/EncodePage';
import { DataDashboard } from './data/DataDashboard';
import { ResponseDetail } from './data/ResponseDetail';
import { ReportDashboard } from './report/ReportDashboard';
import { UsersDashboard } from './users/UsersDashboard';
import { RolesDashboard } from './roles/RolesDashboard';
import { AppsDashboard } from './apps/AppsDashboard';
import { HelpPage } from './help/HelpPage';

interface AdminAppProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

export default function AdminApp({ apiBaseUrl, fetchImpl }: AdminAppProps): JSX.Element {
  return (
    <AdminAuthProvider>
      <RouterProvider>
        <AdminRoot apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
      </RouterProvider>
    </AdminAuthProvider>
  );
}

interface PageRoute {
  path: string;
  title: string;
  element: ReactNode;
}

const PAGES: PageRoute[] = [
  // /admin/data is dispatched directly in AdminRoot (the DataDashboard
  // tabs accept apiBaseUrl + fetchImpl props).
  // /admin/report dispatched directly in AdminRoot below.
  // /admin/apps dispatched directly in AdminRoot below.
  // /admin/users and /admin/roles dispatched directly in AdminRoot
  // (they accept apiBaseUrl + fetchImpl props and render real data).
  // /admin/encode and /admin/encode/:hcw_id are dispatched directly in
  // AdminRoot below (param-bearing routes don't fit the simple matchRoute
  // table). Listed here only so the Configuration nav highlight stays sane.
  { path: '/admin/me/change-password', title: 'Change password', element: <Placeholder title="Change password" subtitle="Required for newly-created accounts" /> },
];

function AdminRoot({ apiBaseUrl, fetchImpl }: AdminAppProps): JSX.Element {
  const { isAuthenticated } = useAdminAuth();
  const { pathname, navigate } = useRouter();

  // Default landing: /admin or /admin/ → /admin/data (or /admin/login if no token).
  useEffect(() => {
    if (pathname === '/admin' || pathname === '/admin/') {
      navigate(isAuthenticated ? '/admin/data' : '/admin/login');
    }
  }, [pathname, isAuthenticated, navigate]);

  // Unauthenticated user requesting a protected page → redirect to login.
  useEffect(() => {
    if (!isAuthenticated && pathname !== '/admin/login' && pathname.startsWith('/admin')) {
      navigate('/admin/login');
    }
  }, [isAuthenticated, pathname, navigate]);

  // Help is intentionally available without auth — first-time operators
  // who haven't logged in yet should still be able to read the operator
  // guide. Render Help BEFORE the auth gate so unauthenticated visits to
  // /admin/help work.
  if (pathname === '/admin/help' || pathname === '/admin/help/') {
    return (
      <Layout>
        <HelpPage />
      </Layout>
    );
  }

  // FX-016 (2026-05-04): show Login when either on /admin/login OR
  // unauthenticated on any protected route. The previous shape returned
  // `<></>` on unauthenticated + relied on the useEffect above to navigate
  // to /admin/login — but that race lost the first event dispatch (child
  // useEffect fires before RouterProvider's listener registration in
  // pages-router.tsx, since child effects run before parent effects), so
  // the URL changed via pushState but the router state never updated and
  // AdminRoot stayed stuck on the empty fragment, producing a blank page on
  // every full-page navigation to /admin/* without auth (typed URL,
  // bookmarked deep link, fresh tab, soft reload). Driving the Login render
  // off the auth state directly removes the dependency on URL synchronization
  // and gives us deep-link-after-login as a side benefit (URL preserves the
  // protected route the user wanted; once they authenticate, AdminRoot falls
  // through to that route's render).
  if (pathname === '/admin/login' || !isAuthenticated) {
    return <Login apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />;
  }

  // Data dashboard + drilled-in response detail.
  if (pathname === '/admin/data' || pathname === '/admin/data/') {
    return (
      <Layout>
        <DataDashboard apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
      </Layout>
    );
  }
  // Report dashboard (Sync + Map tabs).
  if (pathname === '/admin/report' || pathname === '/admin/report/') {
    return (
      <Layout>
        <ReportDashboard apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
      </Layout>
    );
  }
  if (pathname === '/admin/apps' || pathname === '/admin/apps/') {
    return (
      <Layout>
        <AppsDashboard apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
      </Layout>
    );
  }
  if (pathname === '/admin/users' || pathname === '/admin/users/') {
    return (
      <Layout>
        <UsersDashboard apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
      </Layout>
    );
  }
  if (pathname === '/admin/roles' || pathname === '/admin/roles/') {
    return (
      <Layout>
        <RolesDashboard apiBaseUrl={apiBaseUrl} {...(fetchImpl ? { fetchImpl } : {})} />
      </Layout>
    );
  }
  const responseDetailMatch = /^\/admin\/data\/responses\/([^/]+)\/?$/.exec(pathname);
  if (responseDetailMatch) {
    return (
      <Layout>
        <ResponseDetail
          apiBaseUrl={apiBaseUrl}
          submissionId={decodeURIComponent(responseDetailMatch[1]!)}
          {...(fetchImpl ? { fetchImpl } : {})}
        />
      </Layout>
    );
  }

  // Encode routes carry an :hcw_id param.
  if (pathname === '/admin/encode' || pathname === '/admin/encode/') {
    return (
      <Layout>
        <EncodeQueue />
      </Layout>
    );
  }
  const encodeMatch = /^\/admin\/encode\/([^/]+)\/?$/.exec(pathname);
  if (encodeMatch) {
    return (
      <Layout>
        <EncodePage
          apiBaseUrl={apiBaseUrl}
          hcwId={decodeURIComponent(encodeMatch[1]!)}
          {...(fetchImpl ? { fetchImpl } : {})}
        />
      </Layout>
    );
  }

  const route = matchRoute(PAGES, pathname);
  return (
    <Layout>
      {route ? route.element : <NotFound />}
    </Layout>
  );
}

function Placeholder({ title, subtitle }: { title: string; subtitle: string }): JSX.Element {
  return (
    <section className="flex flex-col gap-4 py-8">
      <header className="border-b border-hairline pb-4">
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Section</p>
        <h2 className="mt-1 font-serif text-2xl font-medium tracking-tight">{title}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
      </header>
      <p className="text-sm text-muted-foreground">
        This view is being built in a later sprint. Once the backing endpoints land, this
        placeholder is replaced with the real dashboard.
      </p>
    </section>
  );
}

function NotFound(): JSX.Element {
  return (
    <section className="flex flex-col gap-4 py-8">
      <header className="border-b border-hairline pb-4">
        <h2 className="font-serif text-2xl font-medium tracking-tight">Not found</h2>
      </header>
      <p className="text-sm text-muted-foreground">
        The page you requested doesn&rsquo;t exist in the admin portal.
      </p>
    </section>
  );
}
