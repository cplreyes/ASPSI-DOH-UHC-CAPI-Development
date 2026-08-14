/**
 * F2 Admin Portal — auth context (admin JWT, per-tab session).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.14)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§6.3, §6.3.1)
 *
 * Distinct from the existing PWA tablet auth (`src/lib/auth-context.tsx`,
 * Dexie-backed enrollment). The token lives in
 *   1. React state (source of truth for the current tab), mirrored to
 *   2. sessionStorage via `auth-storage.ts` — so an F5/soft reload of the SAME
 *      tab keeps the operator signed in (2026-07-24, spec §6.3.1);
 *      sessionStorage is per-tab and dies with it; and
 *   3. a BroadcastChannel handoff (#1001, UAT 2026-07-28) — reviewers open
 *      responses in several tabs at once, and a freshly opened tab has empty
 *      sessionStorage. It asks its same-origin siblings for the session and
 *      adopts the first grant, so "Open link in new tab" works without
 *      re-login while any signed-in tab is open.
 * The token is still never written to localStorage or IndexedDB, so nothing
 * survives once the admin's tabs are closed — the shared-machine constraint
 * the original memory-only rule protected survives both revisions. Signing out
 * broadcasts a logout that clears EVERY tab, keeping the walk-away story at
 * least as safe as before.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { clearPersistedAuth, loadPersistedAuth, persistAuth } from './auth-storage';

export interface AdminAuthState {
  token: string | null;
  username: string | null;
  role: string | null;
  roleVersion: number | null;
  expiresAt: number | null;
  passwordMustChange: boolean;
  // FX-002 (#324): advisory perm map for nav gating. null = unknown (logged
  // out, or the Worker didn't send it) → callers treat null as "show all"
  // since the Worker still enforces 403 on the actual request.
  permissions: Record<string, boolean> | null;
}

const INITIAL_STATE: AdminAuthState = {
  token: null,
  username: null,
  role: null,
  roleVersion: null,
  expiresAt: null,
  passwordMustChange: false,
  permissions: null,
};

const CHANNEL_NAME = 'f2admin.auth';

/** expires_at arrives in epoch seconds (JWT convention; the dev-preview
 * token uses the same). Accept epoch ms defensively — anything > 1e12 can
 * only be milliseconds (epoch seconds won't reach 1e12 until year 33658). */
function isExpired(expiresAt: number | null): boolean {
  if (typeof expiresAt !== 'number') return false;
  const expMs = expiresAt > 1e12 ? expiresAt : expiresAt * 1000;
  return expMs <= Date.now();
}

/** Validate an untrusted candidate (a channel grant from a sibling tab) down
 * to a usable state, or null. Rejects missing/expired tokens. The
 * sessionStorage copy has its own, stricter gate in `auth-storage.ts`. */
function sanitizeSession(candidate: unknown): AdminAuthState | null {
  if (!candidate || typeof candidate !== 'object') return null;
  const c = candidate as Partial<AdminAuthState>;
  if (typeof c.token !== 'string' || c.token.length === 0) return null;
  if (isExpired(typeof c.expiresAt === 'number' ? c.expiresAt : null)) return null;
  return {
    token: c.token,
    username: typeof c.username === 'string' ? c.username : null,
    role: typeof c.role === 'string' ? c.role : null,
    roleVersion: typeof c.roleVersion === 'number' ? c.roleVersion : null,
    expiresAt: typeof c.expiresAt === 'number' ? c.expiresAt : null,
    passwordMustChange: c.passwordMustChange === true,
    permissions:
      c.permissions && typeof c.permissions === 'object'
        ? (c.permissions as Record<string, boolean>)
        : null,
  };
}

export interface AdminLoginResponse {
  token: string;
  role: string;
  role_version: number;
  expires_at: number;
  password_must_change: boolean;
  // Optional so an older Worker (no permissions field) degrades gracefully.
  permissions?: Record<string, boolean>;
}

export interface AdminAuthApi extends AdminAuthState {
  setAuth: (username: string, resp: AdminLoginResponse) => void;
  clearAuth: () => void;
  isAuthenticated: boolean;
}

const AdminAuthContext = createContext<AdminAuthApi | null>(null);

type ChannelMessage =
  | { type: 'request' }
  | { type: 'grant'; state: AdminAuthState }
  | { type: 'logout' };

export function AdminAuthProvider({ children }: { children: ReactNode }): JSX.Element {
  // Lazy initializer, not an effect: hydration has to be synchronous with the
  // first render or AdminRoot sees isAuthenticated=false and flashes the login
  // screen (and navigates away from the deep link the user reloaded).
  const [state, setState] = useState<AdminAuthState>(() => loadPersistedAuth() ?? INITIAL_STATE);
  // The channel handler needs the CURRENT state without re-subscribing on
  // every auth change; a ref sidesteps the stale-closure problem.
  const stateRef = useRef(state);
  stateRef.current = state;
  const channelRef = useRef<BroadcastChannel | null>(null);

  useEffect(() => {
    if (typeof BroadcastChannel === 'undefined') return undefined;
    let channel: BroadcastChannel;
    try {
      channel = new BroadcastChannel(CHANNEL_NAME);
    } catch {
      return undefined;
    }
    channelRef.current = channel;
    channel.onmessage = (ev: MessageEvent) => {
      const msg = ev.data as ChannelMessage | null;
      if (!msg || typeof msg !== 'object') return;
      if (msg.type === 'request') {
        // A new tab is asking for the session; answer only if we hold a
        // live token. Every signed-in tab replies — grants are idempotent.
        if (stateRef.current.token && !isExpired(stateRef.current.expiresAt)) {
          channel.postMessage({ type: 'grant', state: stateRef.current });
        }
      } else if (msg.type === 'grant') {
        // Adopt a sibling tab's session, but never clobber one we already
        // have (first grant wins; the rest are no-ops).
        if (!stateRef.current.token) {
          const session = sanitizeSession(msg.state);
          if (session) {
            persistAuth(session);
            setState(session);
          }
        }
      } else if (msg.type === 'logout') {
        clearPersistedAuth();
        setState(INITIAL_STATE);
      }
    };
    // Fresh tab with no session of its own → ask the siblings.
    if (!stateRef.current.token) {
      channel.postMessage({ type: 'request' });
    }
    return () => {
      channelRef.current = null;
      channel.close();
    };
  }, []);

  const setAuth = useCallback((username: string, resp: AdminLoginResponse) => {
    const next: AdminAuthState = {
      token: resp.token,
      username,
      role: resp.role,
      roleVersion: resp.role_version,
      expiresAt: resp.expires_at,
      passwordMustChange: resp.password_must_change,
      permissions: resp.permissions ?? null,
    };
    persistAuth(next);
    setState(next);
  }, []);

  const clearAuth = useCallback(() => {
    // Order matters: the stored copy goes first so a reload racing a 401
    // logout can never resurrect the dead token.
    clearPersistedAuth();
    // Sign out EVERYWHERE — one logout click must not leave a live session
    // in a background tab on a shared machine.
    try {
      channelRef.current?.postMessage({ type: 'logout' });
    } catch {
      /* channel may already be closed — local logout still proceeds */
    }
    setState(INITIAL_STATE);
  }, []);

  const value: AdminAuthApi = {
    ...state,
    setAuth,
    clearAuth,
    isAuthenticated: state.token !== null,
  };

  return <AdminAuthContext.Provider value={value}>{children}</AdminAuthContext.Provider>;
}

export function useAdminAuth(): AdminAuthApi {
  const ctx = useContext(AdminAuthContext);
  if (!ctx) throw new Error('useAdminAuth must be used inside AdminAuthProvider');
  return ctx;
}
