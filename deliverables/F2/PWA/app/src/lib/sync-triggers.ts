import type { SyncRunSummary } from './sync-orchestrator';

export interface TriggersDeps {
  runSync: () => Promise<SyncRunSummary>;
  intervalMs: number;
}

export interface TriggerHandle {
  stop: () => void;
}

export function installSyncTriggers(deps: TriggersDeps): TriggerHandle {
  const { runSync, intervalMs } = deps;

  const safeRun = () => {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) return;
    void runSync();
  };

  const onOnline = () => {
    safeRun();
  };
  window.addEventListener('online', onOnline);

  const interval = setInterval(safeRun, intervalMs);

  safeRun();

  return {
    stop: () => {
      window.removeEventListener('online', onOnline);
      clearInterval(interval);
    },
  };
}
