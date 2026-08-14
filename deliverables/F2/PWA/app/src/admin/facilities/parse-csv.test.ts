import { describe, expect, it } from 'vitest';
import { parseFacilityCsv } from './parse-csv';

const HEADER = 'facility_id,facility_name,facility_type,region,province,city_mun,barangay';

describe('parseFacilityCsv', () => {
  it('parses plain rows', () => {
    const r = parseFacilityCsv(`${HEADER}\n040341130,RHU Daraga I,RHU,Region V (Bicol Region),Albay,Daraga,`);
    expect(r.error).toBeUndefined();
    expect(r.rows).toEqual([
      {
        facility_id: '040341130',
        facility_name: 'RHU Daraga I',
        facility_type: 'RHU',
        region: 'Region V (Bicol Region)',
        province: 'Albay',
        city_mun: 'Daraga',
        barangay: '',
      },
    ]);
  });

  it('handles quoted commas + escaped quotes + CRLF + blank lines', () => {
    const r = parseFacilityCsv(
      `${HEADER}\r\n"040341140","St. Jude ""Main"", Annex",Hospital,,,Los Banos,\r\n\r\n`,
    );
    expect(r.error).toBeUndefined();
    expect(r.rows).toHaveLength(1);
    expect(r.rows[0]!.facility_name).toBe('St. Jude "Main", Annex');
  });

  it('rejects a wrong header, an empty file, and a header-only file', () => {
    expect(parseFacilityCsv('id,name\n1,X').error).toMatch(/Header must be exactly/);
    expect(parseFacilityCsv('').error).toMatch(/empty/i);
    expect(parseFacilityCsv(`${HEADER}\n`).error).toMatch(/No data rows/);
  });

  it('8-column header carries target_hcws; 7-column rows omit the key entirely', () => {
    const v2 = parseFacilityCsv(
      `${HEADER},target_hcws\n040341130,RHU Daraga I,RHU,Region V (Bicol Region),Albay,Daraga,,25\n040341140,RHU Daraga II,RHU,,,,,`,
    );
    expect(v2.error).toBeUndefined();
    expect(v2.rows[0]!.target_hcws).toBe('25');
    expect(v2.rows[1]!.target_hcws).toBe(''); // blank cell = unspecified (never clears)
    const v1 = parseFacilityCsv(`${HEADER}\n040341130,RHU Daraga I,RHU,,,,`);
    expect(v1.error).toBeUndefined();
    expect('target_hcws' in v1.rows[0]!).toBe(false); // 7-col file: no key at all
  });
});
