/**
 * Facility wave CSV parser (spec F2-Facility-Master-Mgmt-2026-07-16; target
 * column added by F2-Coverage-Report-2026-07-17).
 * Hand-rolled (no dependency): quoted fields with "" escapes, CRLF/LF, blank
 * lines skipped. The header must be EXACTLY the 7-column template or the
 * 8-column one (+target_hcws) — order-sensitive so a mis-mapped column can
 * never silently land in the wrong field. 7-column rows carry NO target key,
 * so an old wave file can never clear existing targets.
 */

export const FACILITY_CSV_HEADER = [
  'facility_id',
  'facility_name',
  'facility_type',
  'region',
  'province',
  'city_mun',
  'barangay',
] as const;

/** Current template (downloads emit this one). */
export const FACILITY_CSV_HEADER_V2 = [...FACILITY_CSV_HEADER, 'target_hcws'] as const;

export interface FacilityCsvRow {
  facility_id: string;
  facility_name: string;
  facility_type: string;
  region: string;
  province: string;
  city_mun: string;
  barangay: string;
  /** Present only when the file used the 8-column header ('' = blank cell). */
  target_hcws?: string;
}

export function parseFacilityCsv(text: string): { rows: FacilityCsvRow[]; error?: string } {
  const records = splitCsv(text);
  if (records.length === 0) {
    return { rows: [], error: 'The file is empty.' };
  }
  const header = records[0]!.map((h) => h.trim()).join(',');
  const v1 = FACILITY_CSV_HEADER.join(',');
  const v2 = FACILITY_CSV_HEADER_V2.join(',');
  const hasTarget = header === v2;
  if (!hasTarget && header !== v1) {
    return {
      rows: [],
      error: `Header must be exactly: ${v2} (the trailing target_hcws column is optional)`,
    };
  }
  const rows: FacilityCsvRow[] = [];
  for (const rec of records.slice(1)) {
    if (rec.length === 1 && rec[0]!.trim() === '') continue; // blank line
    const [facility_id = '', facility_name = '', facility_type = '', region = '', province = '', city_mun = '', barangay = '', target_hcws = ''] =
      rec.map((v) => v.trim());
    rows.push({
      facility_id,
      facility_name,
      facility_type,
      region,
      province,
      city_mun,
      barangay,
      ...(hasTarget ? { target_hcws } : {}),
    });
  }
  if (rows.length === 0) return { rows: [], error: 'No data rows below the header.' };
  return { rows };
}

/** Minimal RFC-4180-ish splitter: quotes, "" escapes, CRLF/LF row breaks. */
function splitCsv(text: string): string[][] {
  const out: string[][] = [];
  let row: string[] = [];
  let field = '';
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]!;
    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
      continue;
    }
    if (ch === '"') {
      inQuotes = true;
    } else if (ch === ',') {
      row.push(field);
      field = '';
    } else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      row.push(field);
      field = '';
      out.push(row);
      row = [];
    } else {
      field += ch;
    }
  }
  if (field !== '' || row.length > 0) {
    row.push(field);
    out.push(row);
  }
  return out;
}
