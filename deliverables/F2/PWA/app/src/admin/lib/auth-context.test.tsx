import { describe, expect, it } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { AdminAuthProvider, useAdminAuth } from './auth-context';

describe('AdminAuthProvider', () => {
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
});
