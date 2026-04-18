import { describe, expect, it } from 'vitest';
import { localized, type LocalizedString } from './localized';

describe('localized()', () => {
  const greeting: LocalizedString = { en: 'Hello', fil: 'Kumusta' };

  it('returns the en value for locale=en', () => {
    expect(localized(greeting, 'en')).toBe('Hello');
  });

  it('returns the fil value for locale=fil', () => {
    expect(localized(greeting, 'fil')).toBe('Kumusta');
  });

  it('falls back to en when fil is the empty string', () => {
    const partial: LocalizedString = { en: 'Hello', fil: '' };
    expect(localized(partial, 'fil')).toBe('Hello');
  });

  it('falls back to en when fil is missing entirely', () => {
    const partial = { en: 'Hello' } as unknown as LocalizedString;
    expect(localized(partial, 'fil')).toBe('Hello');
  });
});
