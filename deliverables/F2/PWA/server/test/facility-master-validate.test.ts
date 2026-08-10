/**
 * Shared facility-master validator (spec F2-Facility-Master-Mgmt-2026-07-16):
 * errors block, geo mismatches only warn.
 */
import { describe, expect, it } from 'vitest';
import { validateFacilityInput, PH_REGIONS } from '../src/facility-master.js';

const known = new Set(['Laguna', 'Albay']);

const good = {
  facility_id: '040341130',
  facility_name: 'RHU Daraga I',
  facility_type: 'Rural Health Unit',
  region: 'Region V (Bicol Region)',
  province: 'Albay',
  city_mun: 'Daraga',
  barangay: '',
};

describe('validateFacilityInput', () => {
  it('accepts a fully canonical row with no errors or warnings', () => {
    expect(validateFacilityInput(good, known)).toEqual({ errors: [], warnings: [] });
  });

  it('errors: bad id, missing name, over-long fields', () => {
    expect(
      validateFacilityInput({ ...good, facility_id: '12345' }, known).errors[0],
    ).toMatch(/9 digits/);
    expect(
      validateFacilityInput({ ...good, facility_name: '  ' }, known).errors[0],
    ).toMatch(/required/);
    expect(
      validateFacilityInput({ ...good, facility_name: 'x'.repeat(256) }, known).errors[0],
    ).toMatch(/255/);
    expect(
      validateFacilityInput({ ...good, facility_type: 'x'.repeat(65) }, known).errors[0],
    ).toMatch(/facility_type/);
    expect(
      validateFacilityInput({ ...good, province: 'x'.repeat(129) }, known).errors[0],
    ).toMatch(/province/);
  });

  it('warns (never errors) on a non-canonical region name', () => {
    const r = validateFacilityInput({ ...good, region: 'Region 5' }, known);
    expect(r.errors).toEqual([]);
    expect(r.warnings[0]).toMatch(/not a canonical PSGC region/);
  });

  it('warns on a province the master has never seen', () => {
    const r = validateFacilityInput({ ...good, province: 'Camarines Sur' }, known);
    expect(r.errors).toEqual([]);
    expect(r.warnings[0]).toMatch(/new to the master/);
  });

  it('empty geo fields produce no warnings', () => {
    const r = validateFacilityInput(
      { facility_id: '040341130', facility_name: 'X' },
      known,
    );
    expect(r).toEqual({ errors: [], warnings: [] });
  });

  it('ships all 18 canonical region names', () => {
    expect(PH_REGIONS).toHaveLength(18);
    expect(PH_REGIONS).toContain('Region IV-A (CALABARZON)');
  });
});
