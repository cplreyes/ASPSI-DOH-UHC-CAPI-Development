import { useState } from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
  const [state, setState] = useState<UiState>({ kind: 'idle' });

  const onClick = async () => {
    setState({ kind: 'running' });
    try {
      const summary = await runSync();
      setState({ kind: 'done', summary });
    } catch (err) {
      setState({ kind: 'error', message: (err as Error).message });
    }
  };

  return (
    <div className="flex items-center gap-3">
      <Button type="button" onClick={onClick} disabled={state.kind === 'running'}>
        {state.kind === 'running' ? t('sync.runningButton') : t('sync.runButton')}
      </Button>
      {state.kind === 'done' ? (
        <span className="text-xs text-muted-foreground">
          {state.summary.synced > 0 ? t('sync.syncedSummary', { count: state.summary.synced }) : ''}
          {state.summary.retryScheduled > 0
            ? ' · ' + t('sync.retryingSummary', { count: state.summary.retryScheduled })
            : ''}
          {state.summary.failed > 0
            ? ' · ' + t('sync.rejectedSummary', { count: state.summary.failed })
            : ''}
          {state.summary.attempted === 0 ? t('sync.nothingToSync') : ''}
        </span>
      ) : null}
      {state.kind === 'error' ? (
        <span className="text-xs text-destructive">
          {state.message || t('sync.syncFailedFallback')}
        </span>
      ) : null}
    </div>
  );
}
