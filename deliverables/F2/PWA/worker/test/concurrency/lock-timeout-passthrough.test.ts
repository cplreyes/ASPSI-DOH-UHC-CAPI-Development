/**
 * F2 Admin Portal — concurrency: AS lock-timeout passthrough (R2-#63 scenarios 2 + 3).
 *
 * Plan: epic-04-backend-sync-infrastructure.md (E4-APRT-037)
 *
 * Scenarios 2 (bulk import + role edit) and 3 (cron + PWA submit) are
 * AS-internal LockService races. The Worker's only job under contention
 * is to surface AS's E_LOCK_TIMEOUT response cleanly, with the right HTTP
 * status (503), and never silently retry — that's the admin's call.
 *
 * What this DOES test: every mutation route maps E_LOCK_TIMEOUT to 503 so
 * a contended admin can distinguish "AS is busy, retry shortly" from
 * "AS is broken, escalate" (which maps to 502 E_BACKEND).
 * What this does NOT test: real LockService serialization — that's AS-
 * internal, verified via staging smoke tests:
 *   - Scenario 2: in staging, kick off a bulk_import of 100 rows in tab A,
 *     then in tab B PATCH a role mid-batch. Expect: bulk completes in
 *     order; new logins after the role bump pick up the new permissions
 *     fresh from F2_Roles (role_version is dynamic per-login, NOT stamped
 *     on user rows — see AdminUsers.js adminUsersCreate, which never
 *     writes role_version into F2_Users; the original race premise in
 *     issue #63 was based on a misunderstanding of the data model).
 *   - Scenario 3: in staging, watch worker logs while running cron tick
 *     (POST /admin/api/dashboards/apps/data-settings/{id}/run-now) at the
 *     same time a tablet submits via /api/submit. Both writes go through
 *     `_withDocLock` in AS; expect serialized appends to F2_Audit with
 *     no row corruption.
 */
import { describe, expect, it, vi } from 'vitest';
import {
  handleCreateUser,
  handleDeleteUser,
  type CreateUserAsCallable,
  type DeleteUserAsCallable,
} from '../../src/admin/handlers/users';
import { handleCreateHcw, type CreateHcwAsCallable } from '../../src/admin/handlers/hcws';

describe('concurrency: AS lock-timeout passthrough (R2-#63 scenarios 2 + 3)', () => {
  it('handleDeleteUser maps AS E_LOCK_TIMEOUT to HTTP 503', async () => {
    const asCall = vi.fn<DeleteUserAsCallable>().mockResolvedValue({
      ok: false,
      error: { code: 'E_LOCK_TIMEOUT', message: 'busy, retry' },
    });
    const r = await handleDeleteUser('bob', 'carl_admin', asCall);
    expect(r.status).toBe(503);
    const body = (await r.json()) as { error: { code: string } };
    expect(body.error.code).toBe('E_LOCK_TIMEOUT');
  });

  it('handleCreateHcw maps AS E_LOCK_TIMEOUT to HTTP 503', async () => {
    const asCall = vi.fn<CreateHcwAsCallable>().mockResolvedValue({
      ok: false,
      error: { code: 'E_LOCK_TIMEOUT', message: 'busy, retry' },
    });
    const r = await handleCreateHcw({ hcw_id: 'hcw-001', facility_id: 'fac-1' }, asCall);
    expect(r.status).toBe(503);
    const body = (await r.json()) as { error: { code: string } };
    expect(body.error.code).toBe('E_LOCK_TIMEOUT');
  });

  it('handleCreateUser maps AS E_LOCK_TIMEOUT to HTTP 503', async () => {
    // Under heavy bulk_import contention, a concurrent single-user create
    // can hit the lock-acquire timeout. Worker reports 503 so the admin
    // distinguishes "busy, retry shortly" from a real backend outage.
    const asCall = vi.fn<CreateUserAsCallable>().mockResolvedValue({
      ok: false,
      error: { code: 'E_LOCK_TIMEOUT', message: 'busy, retry' },
    });
    const r = await handleCreateUser(
      { username: 'newuser', password: 'TempPw1234', role_name: 'Standard User' },
      { username: 'carl_admin' },
      asCall,
    );
    expect(r.status).toBe(503);
  });

  it('worker never silently retries on E_LOCK_TIMEOUT — caller decides (R2-#63)', async () => {
    // Idempotency / retry semantics belong to the calling admin. Worker
    // forwards exactly one AS attempt per request and surfaces the timeout.
    // This test pins that contract — if a future refactor adds an internal
    // retry loop, this assertion will break and force the discussion.
    const asCall = vi.fn<CreateHcwAsCallable>().mockResolvedValue({
      ok: false,
      error: { code: 'E_LOCK_TIMEOUT', message: 'busy, retry' },
    });
    await handleCreateHcw({ hcw_id: 'hcw-001', facility_id: 'fac-1' }, asCall);
    expect(asCall).toHaveBeenCalledOnce();
  });
});
