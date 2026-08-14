/**
 * Remember where an unauthenticated visitor was headed, so Login can send them
 * back there instead of dropping everyone on /admin/data.
 *
 * Why this exists: the auth guard in App.tsx redirected to /admin/login and
 * discarded the attempted route, and Login then navigated to a hardcoded
 * /admin/data. So a deep link — e.g. the Sync Dashboard's link to
 * /admin/data/responses/<submission_id> — signed you in and then showed you the
 * responses LIST, never the case you asked for. Reported by Carl 2026-07-30
 * ("one login to the F2 Admin portal, then the case is not viewed").
 *
 * sessionStorage, not a query parameter: the target never belongs in a URL that
 * could be copied, logged by a proxy, or bookmarked, and it dies with the tab.
 */

const KEY = 'f2admin.returnTo';

/**
 * Only same-origin admin paths are ever stored or returned. The check rejects
 * protocol-relative ("//evil.example") and absolute ("https://…") values, so a
 * poisoned storage entry cannot become an open redirect. /admin/login is
 * refused too, or a bounced login would return to itself in a loop.
 */
function isSafeAdminPath(p: string | null | undefined): p is string {
  if (!p) return false;
  if (!p.startsWith('/admin/')) return false;
  if (p.startsWith('//')) return false;
  if (p.includes('://') || p.includes('\\')) return false;
  const path = p.split('?')[0].replace(/\/+$/, '');
  return path !== '/admin/login';
}

/** Called by the auth guard just before it redirects to the login screen. */
export function rememberReturnTo(pathAndSearch: string): void {
  try {
    if (isSafeAdminPath(pathAndSearch)) sessionStorage.setItem(KEY, pathAndSearch);
  } catch {
    /* Storage can be unavailable (private mode, blocked cookies). Losing the
       return path is a degraded experience, never a failed login. */
  }
}

/**
 * Called by Login after a successful sign-in. Consumes the stored path so a
 * later sign-in on the same tab cannot silently reuse a stale destination.
 * Falls back to the dashboard the portal has always opened on.
 */
export function takeReturnTo(fallback = '/admin/data'): string {
  try {
    const stored = sessionStorage.getItem(KEY);
    sessionStorage.removeItem(KEY);
    if (isSafeAdminPath(stored)) return stored;
  } catch {
    /* ignore — fall through to the default landing page */
  }
  return fallback;
}
