/**
 * F2 Admin Portal — auth context (admin JWT, per-tab session).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.14)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§6.3, §6.3.1)
 *
 * Distinct from the existing PWA tablet auth (`src/lib/auth-context.tsx`,
 * Dexie-backed enrollment). The admin JWT is mirrored to sessionStorage
 * (see `auth-storage.ts`) so a browser refresh keeps the operator signed in;
 * it is still never written to localStorage or IndexedDB, so closing the tab
 * ends the session — the shared-machine constraint the original memory-only
 * rule protected survives the 2026-07-24 revision (spec §6.3.1).
 */
import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';
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

export function AdminAuthProvider({ children }: { children: ReactNode }): JSX.Element {
  // Lazy initializer, not an effect: hydration has to be synchronous with the
  // first render or AdminRoot sees isAuthenticated=false and flashes the login
  // screen (and navigates away from the deep link the user reloaded).
  const [state, setState] = useState<AdminAuthState>(() => loadPersistedAuth() ?? INITIAL_STATE);

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
