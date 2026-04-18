import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { MultiSectionForm } from '@/components/survey/MultiSectionForm';
import { PendingCount } from '@/components/sync/PendingCount';
import { SyncPage } from '@/components/sync/SyncPage';
import type { FormValues } from '@/lib/skip-logic';
import { useInstallPrompt } from '@/lib/install-prompt';
import { getOrCreateDraftId, loadDraft, saveDraft, submitDraft } from '@/lib/draft';
import { getSyncEnv } from '@/lib/env';
import { hmacSha256Hex } from '@/lib/hmac';
import { postBatchSubmit } from '@/lib/sync-client';
import { runSync, type SyncRunSummary } from '@/lib/sync-orchestrator';
import { installSyncTriggers } from '@/lib/sync-triggers';

type Status = 'loading' | 'editing' | 'submitted';
type View = 'form' | 'sync';

const APP_VERSION = '0.1.0';
const DEVICE_FINGERPRINT_KEY = 'f2_device_fingerprint';
const SYNC_INTERVAL_MS = 5 * 60 * 1000;

function getOrCreateDeviceFingerprint(): string {
  const existing = localStorage.getItem(DEVICE_FINGERPRINT_KEY);
  if (existing) return existing;
  const fresh = crypto.randomUUID();
  localStorage.setItem(DEVICE_FINGERPRINT_KEY, fresh);
  return fresh;
}

function buildRunSync(): () => Promise<SyncRunSummary> {
  const env = getSyncEnv();
  const fingerprint = getOrCreateDeviceFingerprint();
  return () =>
    runSync({
      postBatchSubmit: (items) =>
        postBatchSubmit(items, {
          backendUrl: env.backendUrl,
          hmacSecret: env.hmacSecret,
          hmacSign: hmacSha256Hex,
          nowMs: Date.now,
          fetchImpl: fetch.bind(globalThis),
        }),
      nowMs: Date.now,
      batchSize: 25,
      specVersion: '2026-04-17-m1',
      appVersion: APP_VERSION,
      deviceFingerprint: fingerprint,
      stuckSyncingThresholdMs: 10 * 60 * 1000,
    });
}

const noopRunSync: () => Promise<SyncRunSummary> = async () => ({
  attempted: 0,
  synced: 0,
  failed: 0,
  retryScheduled: 0,
  alreadyRunning: false,
});

export default function App() {
  const { canInstall, install } = useInstallPrompt();
  const [status, setStatus] = useState<Status>('loading');
  const [view, setView] = useState<View>('form');
  const [draftId, setDraftId] = useState<string>('');
  const [initialValues, setInitialValues] = useState<FormValues>({});
  const runSyncRef = useRef<() => Promise<SyncRunSummary>>(noopRunSync);

  useEffect(() => {
    const id = getOrCreateDraftId();
    setDraftId(id);
    loadDraft(id).then((row) => {
      setInitialValues((row?.values as FormValues | undefined) ?? {});
      setStatus('editing');
    });
  }, []);

  useEffect(() => {
    let triggers: { stop: () => void } | null = null;
    try {
      runSyncRef.current = buildRunSync();
      triggers = installSyncTriggers({
        runSync: runSyncRef.current,
        intervalMs: SYNC_INTERVAL_MS,
      });
    } catch (err) {
      console.warn('[F2] sync disabled:', (err as Error).message);
    }
    return () => {
      triggers?.stop();
    };
  }, []);

  const handleAutosave = (values: FormValues) => {
    if (!draftId) return;
    void saveDraft(draftId, values);
  };

  const handleSubmit = async (values: FormValues) => {
    if (!draftId) return;
    await saveDraft(draftId, values);
    await submitDraft(draftId);
    setStatus('submitted');
    void runSyncRef.current();
  };

  return (
    <main className="flex min-h-full flex-col">
      <header className="flex items-center justify-between border-b px-6 py-3">
        <h1 className="text-lg font-semibold">F2 Survey</h1>
        <div className="flex items-center gap-3">
          <PendingCount />
          <Button
            size="sm"
            variant={view === 'sync' ? 'default' : 'outline'}
            onClick={() => setView(view === 'sync' ? 'form' : 'sync')}
          >
            {view === 'sync' ? 'Form' : 'Sync'}
          </Button>
          {canInstall ? (
            <Button size="sm" onClick={install}>
              Install
            </Button>
          ) : null}
        </div>
      </header>
      {view === 'sync' ? (
        <SyncPage runSync={runSyncRef.current} />
      ) : status === 'loading' ? (
        <p className="p-6 text-sm text-muted-foreground">Loading…</p>
      ) : status === 'submitted' ? (
        <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
          <h2 className="text-2xl font-semibold">Thank you</h2>
          <p className="text-sm text-muted-foreground">
            Your response is saved on this device and will sync when the app is online.
          </p>
        </section>
      ) : (
        <MultiSectionForm
          initialValues={initialValues}
          onAutosave={handleAutosave}
          onSubmit={handleSubmit}
        />
      )}
    </main>
  );
}
