/**
 * Coverage report CSV export (spec F2-Coverage-Report-2026-07-17).
 * Pure serializer — RFC-4180-ish quoting mirroring parse-csv.ts rules — so the
 * download content is unit-testable without touching the DOM.
 */

export interface CoverageCsvRow {
  key: string;
  label: string;
  facilities: number;
  links_active: number;
  target: number | null;
  started: number;
  submitted: number;
  refusals: number;
  refusal_rate: number | null;
  coverage_pct: number | null;
  paper_encoded: number;
  last_activity: string;
}

const HEADER = [
  'key',
  'label',
  'facilities',
  'links_active',
  'target',
  'started',
  'submitted',
  'refusals',
  'refusal_rate_pct',
  'coverage_pct',
  'paper_encoded',
  'last_activity',
] as const;

function cell(v: string | number | null): string {
  const s = v == null ? '' : String(v);
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function coverageCsv(rows: CoverageCsvRow[], totals: CoverageCsvRow): string {
  const lines = [HEADER.join(',')];
  for (const r of [...rows, totals]) {
    lines.push(
      [
        cell(r.key),
        cell(r.label),
        cell(r.facilities),
        cell(r.links_active),
        cell(r.target),
        cell(r.started),
        cell(r.submitted),
        cell(r.refusals),
        cell(r.refusal_rate),
        cell(r.coverage_pct),
        cell(r.paper_encoded),
        cell(r.last_activity),
      ].join(','),
    );
  }
  return lines.join('\r\n') + '\r\n';
}

/** `f2-coverage-<level>-<yyyymmdd>.csv` (local date — the operator's "today"). */
export function coverageCsvFilename(level: string, now = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `f2-coverage-${level}-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}.csv`;
}
