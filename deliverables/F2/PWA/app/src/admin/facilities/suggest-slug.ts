/**
 * Deterministic slug suggestion from a facility name (spec
 * F2-Facilities-Page-2026-07-16): lowercase → hyphenate non-alphanumeric runs →
 * trim → truncate to 31 chars at a word boundary. '' means "no usable
 * suggestion — admin types one" (grammar min 2 chars; 'resolve' is reserved).
 */
export function suggestSlug(name: string): string {
  let s = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  if (s.length > 31) {
    let cut = s.slice(0, 31);
    if (s[31] !== '-') {
      const lastHyphen = cut.lastIndexOf('-');
      if (lastHyphen > 1) cut = cut.slice(0, lastHyphen);
    }
    s = cut.replace(/-+$/g, '');
  }
  if (s.length < 2 || s === 'resolve') return '';
  return s;
}
