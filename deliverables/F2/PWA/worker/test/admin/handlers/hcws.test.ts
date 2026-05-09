/**
 * F2 Admin Portal — handleCreateHcw tests (R2-#58, E4-APRT-041).
 *
 * Worker-side validation + AS-passthrough coverage. The reissue handler has
 * its own integration tests via routes.test.ts; this file is just the
 * Create-HCW path.
 */
import { describe, expect, it, vi } from 'vitest';
import { handleCreateHcw, type CreateHcwAsCallable } from '../../../src/admin/handlers/hcws';

describe('handleCreateHcw — R2-#58', () => {
  it('rejects 400 E_VALIDATION when hcw_id is missing', async () => {
    const asCall = vi.fn<CreateHcwAsCallable>();
    const r = await handleCreateHcw({ facility_id: 'fac-1' }, asCall);
    expect(r.status).toBe(400);
    expect(asCall).not.toHaveBeenCalled();
  });

  it('rejects 400 E_VALIDATION when facility_id is missing', async () => {
    const asCall = vi.fn<CreateHcwAsCallable>();
    const r = await handleCreateHcw({ hcw_id: 'hcw-001' }, asCall);
    expect(r.status).toBe(400);
    expect(asCall).not.toHaveBeenCalled();
  });

  it('rejects 400 E_VALIDATION on illegal hcw_id characters', async () => {
    const asCall = vi.fn<CreateHcwAsCallable>();
    const r = await handleCreateHcw({ hcw_id: 'hcw 001!', facility_id: 'fac-1' }, asCall);
    expect(r.status).toBe(400);
    expect(asCall).not.toHaveBeenCalled();
  });

  it('forwards valid payload to AS with status=pending forced (R2-#58 spec)', async () => {
    const asCall = vi.fn<CreateHcwAsCallable>().mockResolvedValue({
      ok: true,
      data: { hcw_id: 'hcw-001' },
    });
    const r = await handleCreateHcw(
      { hcw_id: 'hcw-001', facility_id: 'fac-1', facility_name: 'Demo Health Center' },
      asCall,
    );
    expect(r.status).toBe(201);
    expect(asCall).toHaveBeenCalledOnce();
    const arg = asCall.mock.calls[0]![0]!;
    expect(arg.hcw_id).toBe('hcw-001');
    expect(arg.facility_id).toBe('fac-1');
    expect(arg.facility_name).toBe('Demo Health Center');
    // Worker forces status=pending — issue spec calls for the lifecycle
    // Create → Reissue → enrolled, with Reissue clearing 'pending'.
    expect(arg.status).toBe('pending');
  });

  it('surfaces AS E_CONFLICT (duplicate hcw_id) as HTTP 409', async () => {
    const asCall = vi.fn<CreateHcwAsCallable>().mockResolvedValue({
      ok: false,
      error: { code: 'E_CONFLICT', message: 'hcw_id hcw-001 already enrolled' },
    });
    const r = await handleCreateHcw(
      { hcw_id: 'hcw-001', facility_id: 'fac-1' },
      asCall,
    );
    expect(r.status).toBe(409);
    const body = (await r.json()) as { error: { code: string; message: string } };
    expect(body.error.code).toBe('E_CONFLICT');
    expect(body.error.message).toMatch(/already enrolled/);
  });

  it('omits facility_name from AS payload when blank', async () => {
    const asCall = vi.fn<CreateHcwAsCallable>().mockResolvedValue({
      ok: true,
      data: { hcw_id: 'hcw-002' },
    });
    await handleCreateHcw({ hcw_id: 'hcw-002', facility_id: 'fac-2' }, asCall);
    const arg = asCall.mock.calls[0]![0]!;
    expect(arg.facility_name).toBeUndefined();
  });
});
