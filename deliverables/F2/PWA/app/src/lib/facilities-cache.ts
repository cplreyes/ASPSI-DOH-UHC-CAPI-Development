import { db, type FacilityRow } from './db';
import type { GetFacilitiesResponse } from './facilities-client';

export interface RefreshDeps {
  fetcher: () => Promise<GetFacilitiesResponse>;
}

export type RefreshResult =
  | { ok: true; count: number }
  | { ok: false; error: { code: string; message: string } };

// Production builds filter dev-fixture facility names (e.g. "Test Facility",
// "Test Facility A") so ASPSI testers never see seed rows that may linger
// in the Apps Script facilities sheet. The canonical fix is removing those
// rows from the backend sheet; this is the client-side safety net.
//
// Pattern: any facility whose name starts with "Test " (case-insensitive).
const TEST_FACILITY_PATTERN = /^Test\b/i;

function isTestFacility(facility: FacilityRow): boolean {
  return TEST_FACILITY_PATTERN.test(facility.facility_name);
}

export async function refreshFacilities(deps: RefreshDeps): Promise<RefreshResult> {
  const response = await deps.fetcher();
  if (!response.ok) {
    return { ok: false, error: response.error };
  }
  const filtered = import.meta.env.PROD
    ? response.facilities.filter((f) => !isTestFacility(f))
    : response.facilities;
  await db.transaction('rw', db.facilities, async () => {
    await db.facilities.clear();
    if (filtered.length > 0) {
      await db.facilities.bulkPut(filtered);
    }
  });
  return { ok: true, count: filtered.length };
}

export async function listFacilities(): Promise<FacilityRow[]> {
  const all = await db.facilities.toArray();
  return all.sort((a, b) => a.facility_name.localeCompare(b.facility_name));
}

export async function getFacility(facilityId: string): Promise<FacilityRow | undefined> {
  return db.facilities.get(facilityId);
}
