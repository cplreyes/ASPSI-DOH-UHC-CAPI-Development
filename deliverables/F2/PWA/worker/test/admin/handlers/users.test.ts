/**
 * F2 Admin Portal — handleDeleteUser guard tests.
 *
 * Plan: epic-04-backend-sync-infrastructure.md (E4-APRT-050)
 * Issue: #133 — Orphan-admin guard + self-delete guard on adminUsersDelete
 *
 * UAT R2 recovery incident (Sprint 004 Day 4): carl_admin was hard-deleted
 * from prod F2_Users with no guard, locking Carl out of the portal. These
 * tests cover both rejection paths at the worker layer; AS has a defense-in-
 * depth duplicate that this test file does NOT exercise (worker → AS RPC is
 * mocked).
 */
import { describe, expect, it, vi } from 'vitest';
import { handleDeleteUser, type DeleteUserAsCallable } from '../../../src/admin/handlers/users';

describe('handleDeleteUser — R2-#133 guards', () => {
  it('rejects with 409 E_CONFLICT when actor tries to delete their own account', async () => {
    const asCall = vi.fn<DeleteUserAsCallable>();
    const r = await handleDeleteUser('carl_admin', 'carl_admin', asCall);

    expect(r.status).toBe(409);
    const body = (await r.json()) as { ok: boolean; error: { code: string; message: string } };
    expect(body.error.code).toBe('E_CONFLICT');
    expect(body.error.message).toBe('cannot delete your own account');
    // Worker fails fast — AS round-trip never happens.
    expect(asCall).not.toHaveBeenCalled();
  });

  it('passes actor_username through to AS RPC payload on a normal delete', async () => {
    const asCall = vi.fn<DeleteUserAsCallable>().mockResolvedValue({
      ok: true,
      data: { username: 'bob' },
    });
    const r = await handleDeleteUser('bob', 'carl_admin', asCall);

    expect(r.status).toBe(204);
    expect(asCall).toHaveBeenCalledOnce();
    expect(asCall).toHaveBeenCalledWith({ username: 'bob', actor_username: 'carl_admin' });
  });

  it('surfaces AS orphan-admin rejection as 409 E_CONFLICT', async () => {
    const asCall = vi.fn<DeleteUserAsCallable>().mockResolvedValue({
      ok: false,
      error: { code: 'E_CONFLICT', message: 'cannot orphan the last Administrator' },
    });
    const r = await handleDeleteUser('carl_admin', 'shan_admin', asCall);

    expect(r.status).toBe(409);
    const body = (await r.json()) as { ok: boolean; error: { code: string; message: string } };
    expect(body.error.code).toBe('E_CONFLICT');
    expect(body.error.message).toBe('cannot orphan the last Administrator');
  });

  it('rejects 400 on invalid username path param without round-tripping AS', async () => {
    const asCall = vi.fn<DeleteUserAsCallable>();
    const r = await handleDeleteUser('!!bogus', 'carl_admin', asCall);

    expect(r.status).toBe(400);
    expect(asCall).not.toHaveBeenCalled();
  });
});
