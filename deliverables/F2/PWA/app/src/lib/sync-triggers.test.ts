import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { installSyncTriggers } from './sync-triggers';
import type { SyncRunSummary } from './sync-orchestrator';

describe('installSyncTriggers', () => {
  let runSync: ReturnType<typeof vi.fn<() => Promise<SyncRunSummary>>>;
  let handle: { stop: () => void } | null;

  beforeEach(() => {
    vi.useFakeTimers();
    runSync = vi.fn<() => Promise<SyncRunSummary>>().mockResolvedValue({
      attempted: 0,
      synced: 0,
      failed: 0,
      retryScheduled: 0,
      alreadyRunning: false,
    });
    handle = null;
  });

  afterEach(() => {
    handle?.stop();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('runs sync immediately on install when navigator.onLine is true', () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    handle = installSyncTriggers({ runSync, intervalMs: 60_000 });
    expect(runSync).toHaveBeenCalledTimes(1);
  });

  it('does not run on install when offline', () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false);
    handle = installSyncTriggers({ runSync, intervalMs: 60_000 });
    expect(runSync).not.toHaveBeenCalled();
  });

  it('runs sync when the window online event fires', () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false);
    handle = installSyncTriggers({ runSync, intervalMs: 60_000 });
    expect(runSync).not.toHaveBeenCalled();
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    window.dispatchEvent(new Event('online'));
    expect(runSync).toHaveBeenCalledTimes(1);
  });

  it('runs sync on the interval while online', () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    handle = installSyncTriggers({ runSync, intervalMs: 60_000 });
    expect(runSync).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(60_000);
    expect(runSync).toHaveBeenCalledTimes(2);
    vi.advanceTimersByTime(60_000);
    expect(runSync).toHaveBeenCalledTimes(3);
  });

  it('stop() removes the online listener and clears the interval', () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    const h = installSyncTriggers({ runSync, intervalMs: 60_000 });
    expect(runSync).toHaveBeenCalledTimes(1);
    h.stop();
    vi.advanceTimersByTime(180_000);
    window.dispatchEvent(new Event('online'));
    expect(runSync).toHaveBeenCalledTimes(1);
  });
});
