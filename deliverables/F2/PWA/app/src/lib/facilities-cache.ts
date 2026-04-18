import { db, type FacilityRow } from './db';
import type { GetFacilitiesResponse } from './facilities-client';

export interface RefreshDeps {
  fetcher: () => Promise<GetFacilitiesResponse>;
}

export type RefreshResult =
  | { ok: true; count: number }
  | { ok: false; error: { code: string; message: string } };

export async function refreshFacilities(deps: RefreshDeps): Promise<RefreshResult> {
  const response = await deps.fetcher();
  if (!response.ok) {
    return { ok: false, error: response.error };
  }
  await db.transaction('rw', db.facilities, async () => {
    await db.facilities.clear();
    if (response.facilities.length > 0) {
      await db.facilities.bulkPut(response.facilities);
    }
  });
  return { ok: true, count: response.facilities.length };
}

export async function listFacilities(): Promise<FacilityRow[]> {
  const all = await db.facilities.toArray();
  return all.sort((a, b) => a.facility_name.localeCompare(b.facility_name));
}

export async function getFacility(facilityId: string): Promise<FacilityRow | undefined> {
  return db.facilities.get(facilityId);
}
