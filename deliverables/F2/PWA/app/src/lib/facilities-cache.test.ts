import { beforeEach, describe, expect, it, vi } from 'vitest';
import { db } from './db';
import { getFacility, listFacilities, refreshFacilities } from './facilities-cache';
import type { GetFacilitiesResponse } from './facilities-client';

const fac = (id: string, type = 'Hospital'): import('./db').FacilityRow => ({
  facility_id: id,
  facility_name: `Facility ${id}`,
  facility_type: type,
  region: 'NCR',
  province: 'Metro Manila',
  city_mun: 'Manila',
  barangay: 'Ermita',
});

describe('facilities-cache', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.facilities.clear();
  });

  it('listFacilities returns rows ordered by facility_name', async () => {
    await db.facilities.bulkPut([fac('F-002'), fac('F-001'), fac('F-003')]);
    const out = await listFacilities();
    expect(out.map((f) => f.facility_id)).toEqual(['F-001', 'F-002', 'F-003']);
  });

  it('getFacility returns undefined for an unknown id', async () => {
    expect(await getFacility('F-XXX')).toBeUndefined();
  });

  it('refreshFacilities replaces the table on success', async () => {
    await db.facilities.put(fac('F-OLD'));
    const fetcher = vi
      .fn<() => Promise<GetFacilitiesResponse>>()
      .mockResolvedValue({ ok: true, facilities: [fac('F-NEW')] });
    const result = await refreshFacilities({ fetcher });
    expect(result).toEqual({ ok: true, count: 1 });
    expect(await db.facilities.toArray()).toHaveLength(1);
    expect(await getFacility('F-NEW')).toBeDefined();
    expect(await getFacility('F-OLD')).toBeUndefined();
  });

  it('refreshFacilities leaves the cache untouched on transport error', async () => {
    await db.facilities.put(fac('F-KEEP'));
    const fetcher = vi.fn<() => Promise<GetFacilitiesResponse>>().mockResolvedValue({
      ok: false,
      transport: true,
      error: { code: 'E_NETWORK', message: 'offline' },
    });
    const result = await refreshFacilities({ fetcher });
    expect(result).toEqual({ ok: false, error: { code: 'E_NETWORK', message: 'offline' } });
    expect(await getFacility('F-KEEP')).toBeDefined();
  });
});
