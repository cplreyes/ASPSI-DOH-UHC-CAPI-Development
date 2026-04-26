import { beforeEach, describe, expect, it } from 'vitest';
import { db } from './db';
import { clearEnrollment, getEnrollment, setEnrollment } from './enrollment';

/** Hand-rolled JWT-shaped string; setEnrollment only requires non-empty `device_token`. */
const FAKE_TOKEN = 'eyJ.eyJ.fake-sig';

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

  it('setEnrollment persists hcw_id, facility_id, facility_type, and device_token', async () => {
    const before = Date.now();
    const row = await setEnrollment({
      hcw_id: 'HCW-42',
      facility_id: 'F-001',
      device_token: FAKE_TOKEN,
    });
    expect(row).toMatchObject({
      id: 'singleton',
      hcw_id: 'HCW-42',
      facility_id: 'F-001',
      facility_type: 'Hospital',
      device_token: FAKE_TOKEN,
    });
    expect(row.enrolled_at).toBeGreaterThanOrEqual(before);
    const reloaded = await getEnrollment();
    expect(reloaded).toEqual(row);
  });

  it('setEnrollment throws if the facility_id is unknown to the cache', async () => {
    await expect(
      setEnrollment({ hcw_id: 'HCW-1', facility_id: 'F-XXX', device_token: FAKE_TOKEN }),
    ).rejects.toThrow(/facility F-XXX/i);
  });

  it('setEnrollment throws on empty hcw_id', async () => {
    await expect(
      setEnrollment({ hcw_id: '   ', facility_id: 'F-001', device_token: FAKE_TOKEN }),
    ).rejects.toThrow(/hcw_id is required/i);
  });

  it('setEnrollment throws on empty device_token', async () => {
    await expect(
      setEnrollment({ hcw_id: 'HCW-1', facility_id: 'F-001', device_token: '   ' }),
    ).rejects.toThrow(/device_token is required/i);
  });

  it('clearEnrollment removes the singleton row', async () => {
    await setEnrollment({ hcw_id: 'HCW-1', facility_id: 'F-001', device_token: FAKE_TOKEN });
    await clearEnrollment();
    expect(await getEnrollment()).toBeNull();
  });
});
