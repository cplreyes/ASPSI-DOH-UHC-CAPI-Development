import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { clearPersistedAuth, loadPersistedAuth, persistAuth } from './auth-storage';
import type { AdminAuthState } from './auth-context';

const KEY = 'f2.admin.session.v1';
const HOUR_MS = 60 * 60 * 1000;

function sessionAt(expiresAtMs: number): AdminAuthState {
  return {
    token: 'tok.tok.tok',
    username: 'se_001',
    role: 'Administrator',
    roleVersion: 3,
    expiresAt: Math.floor(expiresAtMs / 1000),
    passwordMustChange: false,
    permissions: { dash_data: true, dash_users: false },
  };
}

describe('admin auth storage', () => {
  beforeEach(() => sessionStorage.clear());
  afterEach(() => vi.restoreAllMocks());

  it('round-trips a live session', () => {
    const now = Date.now();
    persistAuth(sessionAt(now + 4 * HOUR_MS));
    const restored = loadPersistedAuth(now);
    expect(restored).not.toBeNull();
    expect(restored?.token).toBe('tok.tok.tok');
    expect(restored?.username).toBe('se_001');
    expect(restored?.role).toBe('Administrator');
    expect(restored?.roleVersion).toBe(3);
    expect(restored?.permissions).toEqual({ dash_data: true, dash_users: false });
  });

  it('returns null when nothing is stored', () => {
    expect(loadPersistedAuth()).toBeNull();
  });

  it('uses sessionStorage, never localStorage — closing the tab must end the session', () => {
    persistAuth(sessionAt(Date.now() + HOUR_MS));
    expect(sessionStorage.getItem(KEY)).not.toBeNull();
    expect(localStorage.getItem(KEY)).toBeNull();
  });

  it('drops an expired session instead of restoring it', () => {
    const now = Date.now();
    persistAuth(sessionAt(now - 60_000));
    expect(loadPersistedAuth(now)).toBeNull();
    expect(sessionStorage.getItem(KEY)).toBeNull();
  });

  it('drops a session that would expire mid-first-request', () => {
    const now = Date.now();
    // 10s of life left — inside the 30s guard band.
    persistAuth(sessionAt(now + 10_000));
    expect(loadPersistedAuth(now)).toBeNull();
  });

  it('keeps a session with comfortably more than the guard band left', () => {
    const now = Date.now();
    persistAuth(sessionAt(now + 120_000));
    expect(loadPersistedAuth(now)).not.toBeNull();
  });

  it('discards a corrupt record rather than throwing', () => {
    sessionStorage.setItem(KEY, '{not json');
    expect(loadPersistedAuth()).toBeNull();
    expect(sessionStorage.getItem(KEY)).toBeNull();
  });

  it('discards a record missing a token', () => {
    sessionStorage.setItem(
      KEY,
      JSON.stringify({ v: 1, username: 'se_001', expiresAt: Math.floor(Date.now() / 1000) + 3600 }),
    );
    expect(loadPersistedAuth()).toBeNull();
  });

  it('discards a record written by a future schema version', () => {
    sessionStorage.setItem(
      KEY,
      JSON.stringify({
        v: 2,
        token: 't',
        username: 'se_001',
        expiresAt: Math.floor(Date.now() / 1000) + 3600,
      }),
    );
    expect(loadPersistedAuth()).toBeNull();
  });

  it('normalizes a non-boolean permission map to null rather than trusting it', () => {
    const now = Date.now();
    sessionStorage.setItem(
      KEY,
      JSON.stringify({
        v: 1,
        token: 't',
        username: 'se_001',
        role: 'Administrator',
        roleVersion: 1,
        expiresAt: Math.floor((now + HOUR_MS) / 1000),
        passwordMustChange: false,
        permissions: { dash_data: 'yes' },
      }),
    );
    // null means "unknown" to the nav gate, which degrades to showing all
    // items and letting the worker enforce 403 — safe. A truthy string would
    // instead be read as a granted permission.
    expect(loadPersistedAuth(now)?.permissions).toBeNull();
  });

  it('clearPersistedAuth removes the record', () => {
    persistAuth(sessionAt(Date.now() + HOUR_MS));
    clearPersistedAuth();
    expect(sessionStorage.getItem(KEY)).toBeNull();
  });

  it('refuses to write a tokenless state', () => {
    persistAuth({ ...sessionAt(Date.now() + HOUR_MS), token: null });
    expect(sessionStorage.getItem(KEY)).toBeNull();
  });

  it('survives a storage backend that throws on write', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('QuotaExceededError');
    });
    expect(() => persistAuth(sessionAt(Date.now() + HOUR_MS))).not.toThrow();
  });

  it('survives a storage backend that throws on read', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('SecurityError');
    });
    expect(loadPersistedAuth()).toBeNull();
  });
});
