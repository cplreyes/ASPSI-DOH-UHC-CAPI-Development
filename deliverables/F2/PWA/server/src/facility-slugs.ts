/**
 * Facility slug links (design F2-Facility-Slug-Links-2026-07-16).
 *
 * One clean, readable public link per facility — `<origin>/f/<slug>` — with no
 * secret in the URL (deliberately open; integrity = Start-tap self-register,
 * admin dedup/prune, kill switch). The slug is looked up in f2_facility_slugs.
 */

/** Lowercase, 2-31 chars, starts with a letter/digit, hyphens allowed. */
export const FACILITY_SLUG_RE = /^[a-z0-9][a-z0-9-]{1,30}$/;

/** `GET /f/resolve` shadows `/f/<slug>` for this name — never a valid slug. */
export const RESERVED_FACILITY_SLUGS = new Set(['resolve']);

/** Normalise a slug from a URL/body for lookup (stored lowercase). */
export function normalizeFacilitySlug(raw: string): string {
  return raw.trim().toLowerCase();
}
