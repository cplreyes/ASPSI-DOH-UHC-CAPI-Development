/**
 * Manila-day date windows (spec F2-Coverage-Report-2026-07-17, decision 5).
 *
 * Fieldwork runs on Manila time (+08:00); timestamps are stored UTC. A bare
 * `YYYY-MM-DD` filter param means "that calendar day in Manila", so it maps to
 * the half-open UTC window [d 00:00 MNL, d+1 00:00 MNL) — i.e. `from` becomes
 * an INCLUSIVE lower bound and `to` an EXCLUSIVE upper bound. This closes the
 * Reports-tab-audit P2-7 bug where `to=<date>` (compared as a string / as
 * midnight) silently excluded its entire own day.
 *
 * Full ISO timestamps pass through verbatim (from inclusive, to exclusive) so
 * precise programmatic windows remain expressible.
 */

const MNL_OFFSET_MS = 8 * 3_600_000;
const DAY_MS = 86_400_000;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export interface UtcWindow {
  /** Inclusive UTC ISO lower bound. */
  fromUtc?: string;
  /** EXCLUSIVE UTC ISO upper bound. */
  toUtcExcl?: string;
}

export function mnlWindow(from?: string, to?: string): UtcWindow {
  const out: UtcWindow = {};
  if (from) {
    out.fromUtc = DATE_RE.test(from)
      ? new Date(Date.parse(`${from}T00:00:00Z`) - MNL_OFFSET_MS).toISOString()
      : from;
  }
  if (to) {
    out.toUtcExcl = DATE_RE.test(to)
      ? new Date(Date.parse(`${to}T00:00:00Z`) - MNL_OFFSET_MS + DAY_MS).toISOString()
      : to;
  }
  return out;
}
