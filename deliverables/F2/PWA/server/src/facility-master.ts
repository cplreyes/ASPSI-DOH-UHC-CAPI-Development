/**
 * Facility master management (spec F2-Facility-Master-Mgmt-2026-07-16).
 *
 * ONE validation core shared by the create, patch, and import routes so the
 * form path and the CSV path can never disagree. Geo checks WARN, never block
 * (Carl's call): region against the canonical PSGC region names (byte-identical
 * to deliverables/CSPro/data/psgc/psgc_region.csv — the unified dashboard joins
 * areas BY NAME), province advisorily against the provinces already on file.
 */

/** The 18 canonical PSGC region names CSWeb's F1/F3/F4 use (byte-identical). */
export const PH_REGIONS = [
  'National Capital Region (NCR)',
  'Cordillera Administrative Region (CAR)',
  'Region I (Ilocos Region)',
  'Region II (Cagayan Valley)',
  'Region III (Central Luzon)',
  'Region IV-A (CALABARZON)',
  'MIMAROPA Region',
  'Region V (Bicol Region)',
  'Region VI (Western Visayas)',
  'Negros Island Region (NIR)',
  'Region VII (Central Visayas)',
  'Region VIII (Eastern Visayas)',
  'Region IX (Zamboanga Peninsula)',
  'Region X (Northern Mindanao)',
  'Region XI (Davao Region)',
  'Region XII (SOCCSKSARGEN)',
  'Region XIII (Caraga)',
  'Bangsamoro Autonomous Region In Muslim Mindanao (BARMM)',
] as const;

const REGION_SET: ReadonlySet<string> = new Set(PH_REGIONS);

export type FacilityMasterInput = {
  facility_id: string;
  facility_name: string;
  facility_type?: string;
  region?: string;
  province?: string;
  city_mun?: string;
  barangay?: string;
  /** Coverage target quota; null/undefined = no target. NaN (bad wire value) fails validation. */
  target_hcws?: number | null;
};

/** Immutable-once-created 9-digit PSGC-derived facility key. */
export const FACILITY_ID_RE = /^\d{9}$/;

/**
 * Shared validation. `errors` block the row; `warnings` surface but never block
 * (warn-but-allow geo policy). `knownProvinces` = distinct provinces already in
 * the master (advisory spelling check).
 */
export function validateFacilityInput(
  input: FacilityMasterInput,
  knownProvinces: Set<string>,
): { errors: string[]; warnings: string[] } {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!FACILITY_ID_RE.test(input.facility_id ?? '')) {
    errors.push('facility_id must be exactly 9 digits');
  }
  const name = (input.facility_name ?? '').trim();
  if (!name) errors.push('facility_name is required');
  else if (name.length > 255) errors.push('facility_name must be at most 255 characters');

  if ((input.facility_type ?? '').length > 64) {
    errors.push('facility_type must be at most 64 characters');
  }
  for (const k of ['region', 'province', 'city_mun', 'barangay'] as const) {
    if ((input[k] ?? '').length > 128) errors.push(`${k} must be at most 128 characters`);
  }

  if (input.target_hcws != null) {
    const t = input.target_hcws;
    if (!Number.isInteger(t) || t < 0 || t > 9999) {
      errors.push('target_hcws must be an integer between 0 and 9999');
    }
  }

  const region = (input.region ?? '').trim();
  if (region && !REGION_SET.has(region)) {
    warnings.push(
      `region "${region}" is not a canonical PSGC region name — dashboard by-name joins may miss`,
    );
  }
  const province = (input.province ?? '').trim();
  if (province && !knownProvinces.has(province)) {
    warnings.push(`province "${province}" is new to the master — check spelling against CSWeb`);
  }

  return { errors, warnings };
}
