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

  // Issue #46: enrollment must succeed on a fresh tablet whose facilities
  // cache is empty. The cache populates from /facilities (authenticated)
  // after enrollment completes, so requiring it pre-enroll deadlocks first
  // use. The verified JWT (already server-checked by /verify-token before
  // setEnrollment is called) is the authoritative facility_id source; the
  // local cache lookup was a soft check, not a security boundary.
  it('setEnrollment succeeds when the facility is not in the local cache (fresh-tablet path)', async () => {
    const row = await setEnrollment({
      hcw_id: 'HCW-1',
      facility_id: 'F-XXX',
      device_token: FAKE_TOKEN,
    });
    expect(row).toMatchObject({
      id: 'singleton',
      hcw_id: 'HCW-1',
      facility_id: 'F-XXX',
      device_token: FAKE_TOKEN,
    });
    // facility_type is omitted entirely when the facility isn't cached.
    expect('facility_type' in row && row.facility_type !== undefined).toBe(false);
  });

  it('setEnrollment populates facility_type when the facility IS cached', async () => {
    // F-001 is in the cache via beforeEach.
    const row = await setEnrollment({
      hcw_id: 'HCW-2',
      facility_id: 'F-001',
      device_token: FAKE_TOKEN,
    });
    expect(row.facility_type).toBe('Hospital');
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
