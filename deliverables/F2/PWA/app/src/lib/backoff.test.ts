import { describe, it, expect } from 'vitest';
import { backoffDelayMs, nextRetryAt } from './backoff';

describe('backoffDelayMs', () => {
  it('returns 30s for retry_count=0', () => {
    expect(backoffDelayMs(0)).toBe(30_000);
  });
  it('returns 2m for retry_count=1', () => {
    expect(backoffDelayMs(1)).toBe(120_000);
  });
  it('returns 10m for retry_count=2', () => {
    expect(backoffDelayMs(2)).toBe(600_000);
  });
  it('returns 1h for retry_count=3', () => {
    expect(backoffDelayMs(3)).toBe(3_600_000);
  });
  it('caps at 1h for any retry_count >= 3', () => {
    expect(backoffDelayMs(4)).toBe(3_600_000);
    expect(backoffDelayMs(99)).toBe(3_600_000);
  });
  it('treats negative retry_count as 0', () => {
    expect(backoffDelayMs(-1)).toBe(30_000);
  });
});

describe('nextRetryAt', () => {
  it('returns now + delay for the given retry_count', () => {
    const now = 1_700_000_000_000;
    expect(nextRetryAt(0, now)).toBe(now + 30_000);
    expect(nextRetryAt(2, now)).toBe(now + 600_000);
  });
});
