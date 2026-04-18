import { beforeEach, describe, expect, it } from 'vitest';
import { db } from './db';
import { clearEnrollment, getEnrollment, setEnrollment } from './enrollment';

describe('enrollment store', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.enrollment.clear();
    await db.facilities.clear();
    await db.facilities.put({
      facility_id: 'F-001',
      facility_name: 'Manila General',
      facility_type: 'Hospital',
      region: 'NCR',
      province: 'Metro Manila',
      city_mun: 'Manila',
      barangay: 'Ermita',
    });
  });

  it('getEnrollment returns null when not enrolled', async () => {
    expect(await getEnrollment()).toBeNull();
  });

  it('setEnrollment persists hcw_id, facility_id, and resolved facility_type', async () => {
    const before = Date.now();
    const row = await setEnrollment({ hcw_id: 'HCW-42', facility_id: 'F-001' });
    expect(row).toMatchObject({
      id: 'singleton',
      hcw_id: 'HCW-42',
      facility_id: 'F-001',
      facility_type: 'Hospital',
    });
    expect(row.enrolled_at).toBeGreaterThanOrEqual(before);
    const reloaded = await getEnrollment();
    expect(reloaded).toEqual(row);
  });

  it('setEnrollment throws if the facility_id is unknown to the cache', async () => {
    await expect(setEnrollment({ hcw_id: 'HCW-1', facility_id: 'F-XXX' })).rejects.toThrow(
      /facility F-XXX/i,
    );
  });

  it('setEnrollment throws on empty hcw_id', async () => {
    await expect(setEnrollment({ hcw_id: '   ', facility_id: 'F-001' })).rejects.toThrow(
      /hcw_id is required/i,
    );
  });

  it('clearEnrollment removes the singleton row', async () => {
    await setEnrollment({ hcw_id: 'HCW-1', facility_id: 'F-001' });
    await clearEnrollment();
    expect(await getEnrollment()).toBeNull();
  });
});
