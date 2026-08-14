/**
 * Canonical PSGC region names — client mirror of server/src/facility-master.ts
 * (byte-identical to deliverables/CSPro/data/psgc/psgc_region.csv). Feeds the
 * region <datalist> in the facility edit dialog; the server re-validates.
 */
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
