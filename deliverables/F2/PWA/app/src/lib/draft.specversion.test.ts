import { describe, expect, it } from 'vitest';
import { LOCAL_SPEC_VERSION } from './draft';

describe('LOCAL_SPEC_VERSION (Aug-21 translations)', () => {
  it('is the m4 stamp', () => {
    expect(LOCAL_SPEC_VERSION).toMatch(/^2026-08-\d{2}-m4$/);
  });
});
