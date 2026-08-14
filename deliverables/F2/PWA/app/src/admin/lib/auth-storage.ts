/**
 * F2 Admin Portal — session persistence across page reloads.
 *
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md §6.3.1
 * (added 2026-07-24). The admin JWT was originally memory-only, so every
 * browser refresh dropped operators back to the login screen mid-task. The
 * session now survives a reload in **sessionStorage**: the same tab keeps
 * working, closing the tab or the browser still signs you out. localStorage
 * was rejected on purpose — it would leave a live 4-hour token on disk on a
 * shared field laptop, which is the shared-machine risk the original
 * memory-only rule was written to avoid.
 *
 * A restored token is not trusted beyond its stored expiry: the server still
 * rejects revoked, superseded-role, and expired tokens with 401, which every
 * page already turns into clearAuth() + redirect to login.
 *
 * Every path here is best-effort. Safari private mode and locked-down
 * enterprise profiles throw on storage access, and a corrupt record must never
 * brick the portal — any failure degrades to "no stored session", i.e. the
 * pre-2026-07-24 behaviour of showing the login screen.
 */
import type { AdminAuthState } from './auth-context';

const STORAGE_KEY = 'f2.admin.session.v1';

/**
 * Refuse to restore a token that would die mid-first-request. Landing on a
 * dashboard that instantly 401s is a worse experience than a login screen.
 */
const MIN_REMAINING_MS = 30_000;

interface PersistedSession {
  v: 1;
  token: string;
  username: string;
  role: string | null;
  roleVersion: number | null;
  /** Epoch SECONDS, matching the login response's `expires_at`. */
  expiresAt: number;
  passwordMustChange: boolean;
  permissions: Record<string, boolean> | null;
}

function storage(): Storage | null {
  try {
    if (typeof window === 'undefined') return null;
    return window.sessionStorage;
  } catch {
    // Storage access denied (private mode, blocked cookies, sandboxed iframe).
    return null;
  }
}

function isPermissionMap(value: unknown): value is Record<string, boolean> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return false;
  return Object.values(value as Record<string, unknown>).every((v) => typeof v === 'boolean');
}

function parseSession(raw: unknown): PersistedSession | null {
  if (typeof raw !== 'object' || raw === null) return null;
  const r = raw as Record<string, unknown>;
  // Version gate: a future shape must not be half-read into the current one.
  if (r.v !== 1) return null;
  if (typeof r.token !== 'string' || r.token === '') return null;
  if (typeof r.username !== 'string' || r.username === '') return null;
  if (typeof r.expiresAt !== 'number' || !Number.isFinite(r.expiresAt)) return null;
  return {
    v: 1,
    token: r.token,
    username: r.username,
    role: typeof r.role === 'string' ? r.role : null,
    roleVersion: typeof r.roleVersion === 'number' ? r.roleVersion : null,
    expiresAt: r.expiresAt,
    passwordMustChange: r.passwordMustChange === true,
    permissions: isPermissionMap(r.permissions) ? r.permissions : null,
  };
}

/**
 * Read the stored session. Returns null when there is none, when it is
 * unreadable, or when its token has expired (or is about to) — and drops the
 * record in the latter two cases so the next load doesn't re-parse garbage.
 */
export function loadPersistedAuth(nowMs: number = Date.now()): AdminAuthState | null {
  const s = storage();
  if (!s) return null;

  let raw: string | null;
  try {
    raw = s.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
  if (!raw) return null;

  let parsed: PersistedSession | null = null;
  try {
    parsed = parseSession(JSON.parse(raw));
  } catch {
    parsed = null;
  }
  if (!parsed) {
    clearPersistedAuth();
    return null;
  }

  if (parsed.expiresAt * 1000 - nowMs < MIN_REMAINING_MS) {
    clearPersistedAuth();
    return null;
  }

  return {
    token: parsed.token,
    username: parsed.username,
    role: parsed.role,
    roleVersion: parsed.roleVersion,
    expiresAt: parsed.expiresAt,
    passwordMustChange: parsed.passwordMustChange,
    permissions: parsed.permissions,
  };
}

/**
 * Write the session so a reload can pick it up. A state without a token,
 * username, or expiry is not a session — those clear the record instead of
 * writing a half-usable one.
 */
export function persistAuth(state: AdminAuthState): void {
  const s = storage();
  if (!s) return;

  if (!state.token || !state.username || typeof state.expiresAt !== 'number') {
    clearPersistedAuth();
    return;
  }

  const record: PersistedSession = {
    v: 1,
    token: state.token,
    username: state.username,
    role: state.role,
    roleVersion: state.roleVersion,
    expiresAt: state.expiresAt,
    passwordMustChange: state.passwordMustChange,
    permissions: state.permissions,
  };

  try {
    s.setItem(STORAGE_KEY, JSON.stringify(record));
  } catch {
    // Quota exceeded or storage disabled mid-session — the in-memory session
    // still works for this page view; only the reload survival is lost.
  }
}

export function clearPersistedAuth(): void {
  const s = storage();
  if (!s) return;
  try {
    s.removeItem(STORAGE_KEY);
  } catch {
    // Nothing further to do — the record is unreachable either way.
  }
}
