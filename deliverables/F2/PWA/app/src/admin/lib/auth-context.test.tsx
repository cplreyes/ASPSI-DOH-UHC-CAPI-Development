import { beforeEach, describe, expect, it } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { AdminAuthProvider, useAdminAuth } from './auth-context';

const LIVE_SESSION = {
  token: 'tok.tok.tok',
  role: 'Administrator',
  role_version: 1,
  expires_at: Math.floor(Date.now() / 1000) + 4 * 60 * 60,
  password_must_change: false,
};

describe('AdminAuthProvider', () => {
  beforeEach(() => sessionStorage.clear());

  function wrapper({ children }: { children: React.ReactNode }) {
    return <AdminAuthProvider>{children}</AdminAuthProvider>;
  }

  it('starts unauthenticated', () => {
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
        expires_at: 1730000000,
        password_must_change: false,
      });
    });
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.username).toBe('alice');
    expect(result.current.role).toBe('Administrator');
    expect(result.current.roleVersion).toBe(1);
    expect(result.current.passwordMustChange).toBe(false);
  });

  it('clearAuth resets to initial state', () => {
    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    act(() => {
      result.current.setAuth('alice', {
        token: 't',
        role: 'Administrator',
        role_version: 1,
        expires_at: 0,
        password_must_change: false,
      });
    });
    act(() => result.current.clearAuth());
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.token).toBeNull();
  });

  it('preserves password_must_change flag', () => {
    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    act(() => {
      result.current.setAuth('newbie', {
        token: 't',
        role: 'Standard User',
        role_version: 1,
        expires_at: 0,
        password_must_change: true,
      });
    });
    expect(result.current.passwordMustChange).toBe(true);
  });

  // 2026-07-24: a browser refresh used to sign operators out mid-task. Each
  // remount below stands in for that reload — the provider is rebuilt from
  // scratch and has only sessionStorage to go on.
  it('restores the session on remount, so a reload keeps the operator signed in', () => {
    const first = renderHook(() => useAdminAuth(), { wrapper });
    act(() => first.result.current.setAuth('se_001', LIVE_SESSION));
    first.unmount();

    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.token).toBe('tok.tok.tok');
    expect(result.current.username).toBe('se_001');
    expect(result.current.role).toBe('Administrator');
  });

  it('restores the permission map so nav gating survives a reload', () => {
    const first = renderHook(() => useAdminAuth(), { wrapper });
    act(() =>
      first.result.current.setAuth('se_001', {
        ...LIVE_SESSION,
        permissions: { dash_data: true, dash_users: false },
      }),
    );
    first.unmount();

    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    expect(result.current.permissions).toEqual({ dash_data: true, dash_users: false });
  });

  it('does not restore after clearAuth — sign-out and 401 both stay signed out', () => {
    const first = renderHook(() => useAdminAuth(), { wrapper });
    act(() => first.result.current.setAuth('se_001', LIVE_SESSION));
    act(() => first.result.current.clearAuth());
    first.unmount();

    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.token).toBeNull();
  });

  it('does not restore an expired session', () => {
    const first = renderHook(() => useAdminAuth(), { wrapper });
    act(() =>
      first.result.current.setAuth('se_001', {
        ...LIVE_SESSION,
        expires_at: Math.floor(Date.now() / 1000) - 60,
      }),
    );
    first.unmount();

    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('is authenticated on the very first render, not after an effect', () => {
    const first = renderHook(() => useAdminAuth(), { wrapper });
    act(() => first.result.current.setAuth('se_001', LIVE_SESSION));
    first.unmount();

    // Guards the no-flash requirement: AdminRoot reads isAuthenticated during
    // render, so a hydration that landed one render late would bounce the
    // reloaded deep link to /admin/login before the token arrived.
    const seen: boolean[] = [];
    renderHook(
      () => {
        const auth = useAdminAuth();
        seen.push(auth.isAuthenticated);
        return auth;
      },
      { wrapper },
    );
    expect(seen[0]).toBe(true);
  });
});
