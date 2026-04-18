const SCHEDULE_MS = [30_000, 120_000, 600_000, 3_600_000] as const;

export function backoffDelayMs(retryCount: number): number {
  const n = Math.max(0, retryCount);
  const idx = Math.min(n, SCHEDULE_MS.length - 1);
  return SCHEDULE_MS[idx]!;
}

export function nextRetryAt(retryCount: number, now: number): number {
  return now + backoffDelayMs(retryCount);
}
