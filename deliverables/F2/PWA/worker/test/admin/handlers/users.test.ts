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
import {
  handleDeleteUser,
  handleBulkImportUsers,
  type DeleteUserAsCallable,
  type BulkImportAsCallable,
} from '../../../src/admin/handlers/users';

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

// ----- Bulk import — regression for the double-wrap fix ----------------------
// The success body must be the raw { results, total, created, rejected } object;
// BulkImportModal reads those off r.data directly. The earlier { ok, data } wrap
// made the import-summary counts read as undefined.
describe('handleBulkImportUsers — unwrapped success body', () => {
  it('returns the raw result object on the all-rejected path (no hashing / AS call)', async () => {
    const body = { rows: [{ username: 'alice', password: 'short', role_name: 'Administrator' }] };
    const neverCalled: BulkImportAsCallable = () => {
      throw new Error('asCallable must not run when every row fails client validation');
    };
    const r = await handleBulkImportUsers(body, { username: 'admin' }, neverCalled);
    expect(r.status).toBe(200);
    const out = (await r.json()) as Record<string, unknown>;
    expect(out).toEqual({
      results: [
        {
          username: 'alice',
          status: 'rejected',
          error: { code: 'E_VALIDATION', message: 'password must be at least 8 characters' },
        },
      ],
      total: 1,
      created: 0,
      rejected: 1,
    });
    expect(out.ok).toBeUndefined();
    expect(out.data).toBeUndefined();
  });

  it('threads the AS created/results through unwrapped on the happy path', async () => {
    const body = {
      rows: [{ username: 'bob_admin', password: 'longenough8', role_name: 'Administrator' }],
    };
    const asCall: BulkImportAsCallable = async () => ({
      ok: true,
      data: {
        results: [{ username: 'bob_admin', status: 'created' }],
        total: 1,
        created: 1,
        rejected: 0,
      },
    });
    const r = await handleBulkImportUsers(body, { username: 'admin' }, asCall);
    expect(r.status).toBe(200);
    const out = (await r.json()) as { created: number; results: unknown[] } & Record<string, unknown>;
    expect(out.created).toBe(1);
    expect(out.results).toHaveLength(1);
    expect(out.data).toBeUndefined();
  });
});
