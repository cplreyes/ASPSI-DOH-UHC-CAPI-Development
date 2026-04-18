import { describe, it, expect } from 'vitest';

describe('smoke', () => {
  it('runs Vitest in the backend workspace', () => {
    expect(1 + 1).toBe(2);
  });
});
