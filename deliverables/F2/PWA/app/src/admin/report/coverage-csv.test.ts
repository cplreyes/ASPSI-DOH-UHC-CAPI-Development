/** Coverage CSV serializer (spec F2-Coverage-Report-2026-07-17). */
import { describe, expect, it } from 'vitest';
import { coverageCsv, coverageCsvFilename, type CoverageCsvRow } from './coverage-csv';

const row = (over: Partial<CoverageCsvRow> = {}): CoverageCsvRow => ({
  key: '040340210',
  label: 'LPH-Bay District Hospital',
  facilities: 1,
  links_active: 1,
  target: 30,
  started: 1,
  submitted: 2,
  refusals: 1,
  refusal_rate: 33.3,
  coverage_pct: 7,
  paper_encoded: 1,
  last_activity: '2026-07-16T13:19:19.000Z',
  ...over,
});

describe('coverageCsv', () => {
  it('emits header, rows, totals; quotes commas and doubles embedded quotes', () => {
    const tricky = row({
      key: 'Region IV-A (CALABARZON)',
      label: 'St. "Mary", Annex',
      target: null,
      coverage_pct: null,
    });
    const csv = coverageCsv([tricky], row({ key: 'TOTAL', label: 'TOTAL' }));
    const lines = csv.trimEnd().split('\r\n');
    expect(lines).toHaveLength(3);
    expect(lines[0]).toBe(
      'key,label,facilities,links_active,target,started,submitted,refusals,refusal_rate_pct,coverage_pct,paper_encoded,last_activity',
    );
    expect(lines[1]).toContain('"St. ""Mary"", Annex"');
    expect(lines[1]).toContain(',,'); // null target/coverage → empty cells
    expect(lines[2]).toMatch(/^TOTAL,TOTAL,/);
  });

  it('names the file by level and local date', () => {
    expect(coverageCsvFilename('facility', new Date(2026, 6, 17))).toBe(
      'f2-coverage-facility-20260717.csv',
    );
  });
});
