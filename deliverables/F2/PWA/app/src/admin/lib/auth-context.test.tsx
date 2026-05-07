import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { AdminAuthProvider, useAdminAuth } from './auth-context';

const STORAGE_KEY = 'f2admin:auth:v1';
const FUTURE_EXPIRES = Math.floor(Date.now() / 1000) + 3600;
const PAST_EXPIRES = Math.floor(Date.now() / 1000) - 3600;

describe('AdminAuthProvider', () => {
  function wrapper({ children }: { children: React.ReactNode }) {
    return <AdminAuthProvider>{children}</AdminAuthProvider>;
  }

  beforeEach(() => {
    window.sessionStorage.clear();
  });
  afterEach(() => {
    window.sessionStorage.clear();
  });

  it('starts unauthenticated when storage is empty', () => {
    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.token).toBeNull();
    expect(result.current.username).toBeNull();
  });

  it('flips to authenticated after setAuth', () => {
    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    act(() => {
      result.current.setAuth('alice', {
        token: 'tok.tok.tok',
        role: 'Administrator',
        role_version: 1,
        expires_at: FUTURE_EXPIRES,
        password_must_change: false,
      });
    });
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.username).toBe('alice');
    expect(result.current.role).toBe('Administrator');
    expect(result.current.roleVersion).toBe(1);
    expect(result.current.passwordMustChange).toBe(false);
  });

  it('clearAuth resets to initial state and wipes storage', () => {
    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    act(() => {
      result.current.setAuth('alice', {
        token: 't',
        role: 'Administrator',
        role_version: 1,
        expires_at: FUTURE_EXPIRES,
        password_must_change: false,
      });
    });
    expect(window.sessionStorage.getItem(STORAGE_KEY)).not.toBeNull();
    act(() => result.current.clearAuth());
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.token).toBeNull();
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it('preserves password_must_change flag', () => {
    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    act(() => {
      result.current.setAuth('newbie', {
        token: 't',
        role: 'Standard User',
        role_version: 1,
        expires_at: FUTURE_EXPIRES,
        password_must_change: true,
      });
    });
    expect(result.current.passwordMustChange).toBe(true);
  });

  it('persists the auth record to sessionStorage on setAuth (UAT R2 #68)', () => {
    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    act(() => {
      result.current.setAuth('alice', {
        token: 'tok.tok.tok',
        role: 'Administrator',
        role_version: 2,
        expires_at: FUTURE_EXPIRES,
        password_must_change: false,
      });
    });
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    expect(raw).not.toBeNull();
    const parsed = JSON.parse(raw!);
    expect(parsed).toMatchObject({
      token: 'tok.tok.tok',
      username: 'alice',
      role: 'Administrator',
      roleVersion: 2,
      expiresAt: FUTURE_EXPIRES,
      passwordMustChange: false,
    });
  });

  it('hydrates from sessionStorage on mount when the record is fresh', () => {
    window.sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        token: 'persisted.tok',
        username: 'shan',
        role: 'Administrator',
        roleVersion: 3,
        expiresAt: FUTURE_EXPIRES,
        passwordMustChange: false,
      }),
    );
    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.username).toBe('shan');
    expect(result.current.role).toBe('Administrator');
    expect(result.current.roleVersion).toBe(3);
    expect(result.current.token).toBe('persisted.tok');
  });

  it('does NOT hydrate an expired record and clears storage', () => {
    window.sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        token: 'stale.tok',
        username: 'shan',
        role: 'Administrator',
        roleVersion: 3,
        expiresAt: PAST_EXPIRES,
        passwordMustChange: false,
      }),
    );
    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(false);
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it('ignores malformed sessionStorage records', () => {
    window.sessionStorage.setItem(STORAGE_KEY, '{not json');
    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(false);
  });
});
