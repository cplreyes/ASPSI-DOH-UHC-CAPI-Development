/** Manila-day window conversion (spec F2-Coverage-Report-2026-07-17). */
import { describe, expect, it } from 'vitest';
import { mnlWindow } from '../src/admin/mnl-window.js';

describe('mnlWindow', () => {
  it('maps a bare date to the Manila half-open UTC window', () => {
    expect(mnlWindow('2026-07-16', '2026-07-16')).toEqual({
      fromUtc: '2026-07-15T16:00:00.000Z',
      toUtcExcl: '2026-07-16T16:00:00.000Z',
    });
  });

  it('a Manila-evening submission falls inside its Manila day', () => {
    // 2026-07-16T13:19:19Z = 21:19 MNL on the 16th — the prod case the old
    // string compare excluded when to=2026-07-16.
    const w = mnlWindow(undefined, '2026-07-16');
    expect('2026-07-16T13:19:19.000Z' < w.toUtcExcl!).toBe(true);
    // 2026-07-16T16:01:00Z = 00:01 MNL on the 17th — must be excluded.
    expect('2026-07-16T16:01:00.000Z' < w.toUtcExcl!).toBe(false);
  });

  it('passes full ISO timestamps through verbatim', () => {
    expect(mnlWindow('2026-07-16T05:00:00.000Z', '2026-07-16T06:00:00.000Z')).toEqual({
      fromUtc: '2026-07-16T05:00:00.000Z',
      toUtcExcl: '2026-07-16T06:00:00.000Z',
    });
  });

  it('empty inputs yield an empty window', () => {
    expect(mnlWindow()).toEqual({});
    expect(mnlWindow('', '')).toEqual({});
  });
});
