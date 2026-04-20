import { describe, it, expect } from 'vitest';
import { isServerNewer } from './spec-version';

describe('isServerNewer', () => {
  it('returns false when serverMin is empty', () => {
    expect(isServerNewer('2026-04-17-m1', '')).toBe(false);
  });

  it('returns false when versions are equal', () => {
    expect(isServerNewer('2026-04-17-m1', '2026-04-17-m1')).toBe(false);
  });

  it('returns true when server milestone is higher on same date', () => {
    expect(isServerNewer('2026-04-17-m1', '2026-04-17-m2')).toBe(true);
  });

  it('handles double-digit milestones correctly (regression: lexicographic compare)', () => {
    expect(isServerNewer('2026-04-17-m2', '2026-04-17-m10')).toBe(true);
    expect(isServerNewer('2026-04-17-m10', '2026-04-17-m2')).toBe(false);
    expect(isServerNewer('2026-04-17-m9', '2026-04-17-m10')).toBe(true);
  });

  it('returns true when server date is later', () => {
    expect(isServerNewer('2026-04-17-m5', '2026-05-01-m1')).toBe(true);
  });

  it('returns false when server date is earlier', () => {
    expect(isServerNewer('2026-05-01-m1', '2026-04-17-m99')).toBe(false);
  });

  it('falls back to string compare for non-matching formats', () => {
    expect(isServerNewer('v1', 'v2')).toBe(true);
    expect(isServerNewer('v2', 'v1')).toBe(false);
  });
});
