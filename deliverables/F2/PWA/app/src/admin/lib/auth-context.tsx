/**
 * F2 Admin Portal — auth context (admin JWT in sessionStorage).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.14)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§6.3, §10.4)
 *
 * Distinct from the existing PWA tablet auth (`src/lib/auth-context.tsx`,
 * Dexie-backed enrollment).
 *
 * **Spec §10.4 deviation (UAT R2, 2026-05-08):** the original spec held the
 * admin JWT in React state only — every page reload signed the user back out.
 * UAT R2 surfaced this as a blocker (#68/#97/#104/#105): testers refresh to
 * verify state and lose their session each time. We now persist the auth
 * record to sessionStorage instead, which:
 *
 *   - survives F5 / browser refresh,
 *   - dies on tab close (sessionStorage is scoped per top-level browsing
 *     context — a closed tab cannot revive its storage),
 *   - is bounded by the server-issued `expires_at` (any hydrated record past
 *     its TTL is dropped before it ever enters component state).
 *
 * This is weaker than the original "in-memory only" guarantee but recovers
 * refresh-survival without enabling a true persistent admin session. The
 * stronger HttpOnly refresh-cookie pattern is tracked separately for
 * Sprint 005 (E4-APRT-046).
 */
import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';

const STORAGE_KEY = 'f2admin:auth:v1';

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

function readPersisted(): AdminAuthState {
  if (typeof window === 'undefined' || typeof window.sessionStorage === 'undefined') {
    return INITIAL_STATE;
  }
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return INITIAL_STATE;
    const parsed = JSON.parse(raw) as Partial<AdminAuthState>;
    if (
      typeof parsed.token !== 'string' ||
      typeof parsed.expiresAt !== 'number' ||
      parsed.expiresAt * 1000 <= Date.now()
    ) {
      // Expired or malformed — drop it so a stale record never reaches state.
      window.sessionStorage.removeItem(STORAGE_KEY);
      return INITIAL_STATE;
    }
    return {
      token: parsed.token,
      username: typeof parsed.username === 'string' ? parsed.username : null,
      role: typeof parsed.role === 'string' ? parsed.role : null,
      roleVersion: typeof parsed.roleVersion === 'number' ? parsed.roleVersion : null,
      expiresAt: parsed.expiresAt,
      passwordMustChange: parsed.passwordMustChange === true,
    };
  } catch {
    // SessionStorage may throw under privacy modes / disabled storage.
    return INITIAL_STATE;
  }
}

function writePersisted(state: AdminAuthState): void {
  if (typeof window === 'undefined' || typeof window.sessionStorage === 'undefined') return;
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    /* best-effort persistence */
  }
}

function clearPersisted(): void {
  if (typeof window === 'undefined' || typeof window.sessionStorage === 'undefined') return;
  try {
    window.sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* best-effort */
  }
}

export function AdminAuthProvider({ children }: { children: ReactNode }): JSX.Element {
  const [state, setState] = useState<AdminAuthState>(readPersisted);

  const setAuth = useCallback((username: string, resp: AdminLoginResponse) => {
    const next: AdminAuthState = {
      token: resp.token,
      username,
      role: resp.role,
      roleVersion: resp.role_version,
      expiresAt: resp.expires_at,
      passwordMustChange: resp.password_must_change,
    };
    writePersisted(next);
    setState(next);
  }, []);

  const clearAuth = useCallback(() => {
    clearPersisted();
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
