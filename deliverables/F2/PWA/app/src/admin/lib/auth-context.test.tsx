import { beforeEach, describe, expect, it } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AdminAuthProvider, useAdminAuth } from './auth-context';

// Epoch-seconds expiry comfortably in the future (year ~2286) / past.
const FUTURE_EXP = 9999999999;
const PAST_EXP = 1000000000;

const LIVE_SESSION = {
  token: 'tok.tok.tok',
  role: 'Administrator',
  role_version: 1,
  expires_at: Math.floor(Date.now() / 1000) + 4 * 60 * 60,
  password_must_change: false,
};

describe('AdminAuthProvider', () => {
  // Sessions persist in sessionStorage (#1001 / 2026-07-24) — isolate every test.
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

  // #1001: a same-tab reload (fresh provider, same sessionStorage) keeps the
  // session instead of forcing a re-login.
  it('#1001: hydrates a live session from sessionStorage on mount', () => {
    const first = renderHook(() => useAdminAuth(), { wrapper });
    act(() => {
      first.result.current.setAuth('alice', {
        token: 'tok.tok.tok',
        role: 'Administrator',
        role_version: 2,
        expires_at: FUTURE_EXP,
        password_must_change: false,
      });
    });
    first.unmount();

    const second = renderHook(() => useAdminAuth(), { wrapper });
    expect(second.result.current.isAuthenticated).toBe(true);
    expect(second.result.current.username).toBe('alice');
    expect(second.result.current.roleVersion).toBe(2);
  });

  it('#1001: does NOT hydrate an expired stored session', () => {
    const first = renderHook(() => useAdminAuth(), { wrapper });
    act(() => {
      first.result.current.setAuth('alice', {
        token: 'tok.tok.tok',
        role: 'Administrator',
        role_version: 1,
        expires_at: PAST_EXP,
        password_must_change: false,
      });
    });
    first.unmount();

    const second = renderHook(() => useAdminAuth(), { wrapper });
    expect(second.result.current.isAuthenticated).toBe(false);
  });

  it('#1001: clearAuth drops the stored session (no hydration after logout)', () => {
    const first = renderHook(() => useAdminAuth(), { wrapper });
    act(() => {
      first.result.current.setAuth('alice', {
        token: 't',
        role: 'Administrator',
        role_version: 1,
        expires_at: FUTURE_EXP,
        password_must_change: false,
      });
    });
    act(() => first.result.current.clearAuth());
    first.unmount();

    const second = renderHook(() => useAdminAuth(), { wrapper });
    expect(second.result.current.isAuthenticated).toBe(false);
  });

  // BroadcastChannel handoff — the "open in new tab keeps me signed in" path.
  // Skipped when the test env's jsdom has no BroadcastChannel.
  const hasBC = typeof BroadcastChannel !== 'undefined';

  it.skipIf(!hasBC)('#1001: a fresh provider adopts a sibling tab\'s session via BroadcastChannel', async () => {
    const tabA = renderHook(() => useAdminAuth(), { wrapper });
    act(() => {
      tabA.result.current.setAuth('alice', {
        token: 'tok.tok.tok',
        role: 'Administrator',
        role_version: 3,
        expires_at: FUTURE_EXP,
        password_must_change: false,
      });
    });
    // A real new tab starts with EMPTY sessionStorage; simulate that so the
    // adoption must ride the channel, not the storage.
    sessionStorage.clear();

    const tabB = renderHook(() => useAdminAuth(), { wrapper });
    expect(tabB.result.current.isAuthenticated).toBe(false);
    await waitFor(() => {
      expect(tabB.result.current.isAuthenticated).toBe(true);
    });
    expect(tabB.result.current.username).toBe('alice');
    expect(tabB.result.current.roleVersion).toBe(3);
  });

  it.skipIf(!hasBC)('#1001: logout broadcasts to sibling tabs', async () => {
    const tabA = renderHook(() => useAdminAuth(), { wrapper });
    act(() => {
      tabA.result.current.setAuth('alice', {
        token: 'tok.tok.tok',
        role: 'Administrator',
        role_version: 1,
        expires_at: FUTURE_EXP,
        password_must_change: false,
      });
    });
    const tabB = renderHook(() => useAdminAuth(), { wrapper });
    await waitFor(() => {
      expect(tabB.result.current.isAuthenticated).toBe(true);
    });

    act(() => tabB.result.current.clearAuth());
    await waitFor(() => {
      expect(tabA.result.current.isAuthenticated).toBe(false);
    });
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
