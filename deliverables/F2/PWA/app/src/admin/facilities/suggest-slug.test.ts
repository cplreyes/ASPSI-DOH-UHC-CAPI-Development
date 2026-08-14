import { describe, expect, it } from 'vitest';
import { suggestSlug } from './suggest-slug';

describe('suggestSlug', () => {
  it('lowercases and hyphenates non-alphanumeric runs', () => {
    expect(suggestSlug('RHU Daraga I')).toBe('rhu-daraga-i');
    expect(suggestSlug('LPH-Bay District Hospital')).toBe('lph-bay-district-hospital');
    expect(suggestSlug('St. Niño (Annex) #2')).toBe('st-ni-o-annex-2');
  });

  it('trims leading/trailing hyphens', () => {
    expect(suggestSlug('  (Main) Hospital  ')).toBe('main-hospital');
  });

  it('truncates to 31 chars, cutting back to the last word boundary', () => {
    // "…provincial-health|-office": char 31 IS a boundary → keep the whole word.
    expect(suggestSlug('Camarines Sur Provincial Health Office')).toBe(
      'camarines-sur-provincial-health',
    );
    // Cut landing mid-word backs up to the previous hyphen.
    expect(suggestSlug('Camarines Sur Provincial Healthcare')).toBe('camarines-sur-provincial');
    // Exactly-31 stays whole.
    expect(suggestSlug('abcde-fghij-klmno-pqrst-uvwxy-z')).toBe('abcde-fghij-klmno-pqrst-uvwxy-z');
  });

  it("returns '' for degenerate or reserved results (admin types manually)", () => {
    expect(suggestSlug('R')).toBe('');
    expect(suggestSlug('!!!')).toBe('');
    expect(suggestSlug('Resolve')).toBe('');
  });
});
