import { useState } from 'react';
import { Button } from '@/components/ui/button';
import type { SyncRunSummary } from '@/lib/sync-orchestrator';

interface SyncButtonProps {
  runSync: () => Promise<SyncRunSummary>;
}

type UiState =
  | { kind: 'idle' }
  | { kind: 'running' }
  | { kind: 'done'; summary: SyncRunSummary }
  | { kind: 'error'; message: string };

export function SyncButton({ runSync }: SyncButtonProps) {
  const [state, setState] = useState<UiState>({ kind: 'idle' });

  const onClick = async () => {
    setState({ kind: 'running' });
    try {
      const summary = await runSync();
      setState({ kind: 'done', summary });
    } catch (err) {
      setState({ kind: 'error', message: (err as Error).message || 'Sync failed' });
    }
  };

  return (
    <div className="flex items-center gap-3">
      <Button type="button" onClick={onClick} disabled={state.kind === 'running'}>
        {state.kind === 'running' ? 'Syncing…' : 'Sync now'}
      </Button>
      {state.kind === 'done' ? (
        <span className="text-xs text-muted-foreground">
          {state.summary.synced > 0 ? `Synced ${state.summary.synced}` : ''}
          {state.summary.retryScheduled > 0 ? ` · Retrying ${state.summary.retryScheduled}` : ''}
          {state.summary.failed > 0 ? ` · ${state.summary.failed} rejected` : ''}
          {state.summary.attempted === 0 ? 'Nothing to sync' : ''}
        </span>
      ) : null}
      {state.kind === 'error' ? (
        <span className="text-xs text-destructive">{state.message}</span>
      ) : null}
    </div>
  );
}
