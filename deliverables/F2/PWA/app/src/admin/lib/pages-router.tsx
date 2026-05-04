/**
 * F2 Admin Portal — minimal pathname-based router.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.14)
 *
 * Custom router (not react-router) per the plan's `lib/pages-router.tsx`
 * decision: ~30 LOC vs ~15 KB gzipped of dep, and we only need exact-match
 * + prefix-match for ~10 admin routes. No params decoder is needed yet —
 * the one route that takes an ID (/admin/data/responses/:id) parses the
 * tail segment in the page component.
 *
 * Navigation uses history.pushState + a custom "pathchange" event so
 * Link clicks and programmatic navigate() calls update without a full
 * page reload. popstate (browser back/forward) is also wired up.
 */
import React, { createContext, useContext, useEffect, useState, type ReactNode, type MouseEvent } from 'react';

const PATH_CHANGE_EVENT = 'f2admin:pathchange';

interface RouterCtx {
  pathname: string;
  /** URL search portion incl. leading "?" (or "" if none). Re-renders on tab/filter changes. */
  search: string;
  navigate: (to: string) => void;
}

const RouterContext = createContext<RouterCtx | null>(null);

export function RouterProvider({ children }: { children: ReactNode }): JSX.Element {
  const [pathname, setPathname] = useState<string>(() =>
    typeof window !== 'undefined' ? window.location.pathname : '/',
  );
  const [search, setSearch] = useState<string>(() =>
    typeof window !== 'undefined' ? window.location.search : '',
  );

  useEffect(() => {
    const onChange = () => {
      setPathname(window.location.pathname);
      setSearch(window.location.search);
    };
    window.addEventListener('popstate', onChange);
    window.addEventListener(PATH_CHANGE_EVENT, onChange);
    return () => {
      window.removeEventListener('popstate', onChange);
      window.removeEventListener(PATH_CHANGE_EVENT, onChange);
    };
  }, []);

  const navigate = (to: string) => {
    // Compare against the full URL (pathname + search) so tab/filter
    // navigations like /admin/data?tab=audit aren't bailed out of just
    // because the pathname matches.
    const current = window.location.pathname + window.location.search;
    if (to === current) return;
    window.history.pushState({}, '', to);
    window.dispatchEvent(new Event(PATH_CHANGE_EVENT));
  };

  return <RouterContext.Provider value={{ pathname, search, navigate }}>{children}</RouterContext.Provider>;
}

export function useRouter(): RouterCtx {
  const ctx = useContext(RouterContext);
  if (!ctx) throw new Error('useRouter must be used inside RouterProvider');
  return ctx;
}

/**
 * Find the best route match for a pathname. Tries exact match first,
 * then longest-prefix match (so /admin/data/responses/123 matches a
 * route registered as /admin/data). Returns null if nothing matches.
 */
export function matchRoute<T extends { path: string }>(routes: T[], pathname: string): T | null {
  const exact = routes.find(r => r.path === pathname);
  if (exact) return exact;
  const prefixCandidates = routes
    .filter(r => pathname === r.path || pathname.startsWith(r.path + '/'))
    .sort((a, b) => b.path.length - a.path.length);
  return prefixCandidates[0] ?? null;
}

// LinkProps extends the standard anchor attributes (title, aria-label,
// aria-current, etc.) so Layout can pass tooltip + a11y labels through
// without each consumer having to redeclare the prop surface. `to` replaces
// `href`; everything else flows through to the underlying <a>.
type LinkProps = Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, 'href' | 'onClick'> & {
  to: string;
  children: ReactNode;
};

export function Link({ to, children, ...rest }: LinkProps): JSX.Element {
  const { navigate } = useRouter();
  const onClick = (e: MouseEvent<HTMLAnchorElement>) => {
    // Respect new-tab / cmd-click intent.
    if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    navigate(to);
  };
  return (
    <a href={to} onClick={onClick} {...rest}>
      {children}
    </a>
  );
}
