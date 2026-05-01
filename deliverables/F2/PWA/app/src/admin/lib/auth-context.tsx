/**
 * F2 Admin Portal — auth context (admin JWT in memory).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.14)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§6.3, §10.4)
 *
 * Distinct from the existing PWA tablet auth (`src/lib/auth-context.tsx`,
 * Dexie-backed enrollment). Admin JWT lives only in memory: a page reload
 * forces re-login. Spec §10.4 — admin tokens are not persisted to localStorage
 * or IndexedDB to limit blast radius if an admin walks away from a shared
 * machine.
 */
import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';

export interface AdminAuthState {
  token: string | null;
  username: string | null;
  role: string | null;
  roleVersion: number | null;
  expiresAt: number | null;
  passwordMustChange: boolean;
}

const INITIAL_STATE: AdminAuthState = {
  token: null,
  username: null,
  role: null,
  roleVersion: null,
  expiresAt: null,
  passwordMustChange: false,
};

export interface AdminLoginResponse {
  token: string;
  role: string;
  role_version: number;
  expires_at: number;
  password_must_change: boolean;
}

export interface AdminAuthApi extends AdminAuthState {
  setAuth: (username: string, resp: AdminLoginResponse) => void;
  clearAuth: () => void;
  isAuthenticated: boolean;
}

const AdminAuthContext = createContext<AdminAuthApi | null>(null);

export function AdminAuthProvider({ children }: { children: ReactNode }): JSX.Element {
  const [state, setState] = useState<AdminAuthState>(INITIAL_STATE);

  const setAuth = useCallback((username: string, resp: AdminLoginResponse) => {
    setState({
      token: resp.token,
      username,
      role: resp.role,
      roleVersion: resp.role_version,
      expiresAt: resp.expires_at,
      passwordMustChange: resp.password_must_change,
    });
  }, []);

  const clearAuth = useCallback(() => {
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
