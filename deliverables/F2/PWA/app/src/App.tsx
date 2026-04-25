import { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { MultiSectionForm } from '@/components/survey/MultiSectionForm';
import { EnrollmentScreen } from '@/components/enrollment/EnrollmentScreen';
import { PendingCount } from '@/components/sync/PendingCount';
import { LanguageSwitcher } from '@/components/i18n/LanguageSwitcher';
import { BroadcastBanner } from '@/components/chrome/BroadcastBanner';
import { KillSwitchOverlay } from '@/components/chrome/KillSwitchOverlay';
import { SpecDriftOverlay } from '@/components/chrome/SpecDriftOverlay';
import { LocaleProvider } from '@/i18n/locale-context';
import type { FormValues } from '@/lib/skip-logic';
import { useInstallPrompt } from '@/lib/install-prompt';
import { AuthProvider, useAuth } from '@/lib/auth-context';
import {
  getOrCreateDraftId,
  loadDraft,
  saveDraft,
  submitDraft,
  LOCAL_SPEC_VERSION,
  type EnrollmentInfo,
} from '@/lib/draft';
import { getSyncEnv } from '@/lib/env';
import { hmacSha256Hex } from '@/lib/hmac';
import { isServerNewer } from '@/lib/spec-version';
import { postBatchSubmit } from '@/lib/sync-client';
import { runSync, type SyncRunSummary } from '@/lib/sync-orchestrator';
import { installSyncTriggers } from '@/lib/sync-triggers';
import { getFacilities } from '@/lib/facilities-client';
import { refreshFacilities, type RefreshResult } from '@/lib/facilities-cache';
import { getConfig, type GetConfigResponse } from '@/lib/config-client';
import { RuntimeConfigProvider, useRuntimeConfig } from '@/lib/runtime-config';

const SyncPage = lazy(() =>
  import('@/components/sync/SyncPage').then((m) => ({ default: m.SyncPage })),
);

type Status = 'loading' | 'editing' | 'submitted' | 'submit_failed';
type View = 'form' | 'sync';

const APP_VERSION = __APP_VERSION__;
const DEVICE_FINGERPRINT_KEY = 'f2_device_fingerprint';
const SYNC_INTERVAL_MS = 5 * 60 * 1000;
const CONFIG_REFRESH_INTERVAL_MS = 5 * 60 * 1000;

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
      specVersion: LOCAL_SPEC_VERSION,
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

function buildRefreshFacilities(): () => Promise<RefreshResult> {
  const env = getSyncEnv();
  return () =>
    refreshFacilities({
      fetcher: () =>
        getFacilities({
          backendUrl: env.backendUrl,
          hmacSecret: env.hmacSecret,
          hmacSign: hmacSha256Hex,
          nowMs: Date.now,
          fetchImpl: fetch.bind(globalThis),
        }),
    });
}

function buildConfigFetcher(): () => Promise<GetConfigResponse> {
  const env = getSyncEnv();
  return () =>
    getConfig({
      backendUrl: env.backendUrl,
      hmacSecret: env.hmacSecret,
      hmacSign: hmacSha256Hex,
      nowMs: Date.now,
      fetchImpl: fetch.bind(globalThis),
    });
}

const noopConfigFetcher: () => Promise<GetConfigResponse> = async () => ({
  ok: false,
  transport: true,
  error: { code: 'E_ENV', message: 'Backend env missing' },
});

function AppShell() {
  const { t } = useTranslation();
  const { canInstall, install } = useInstallPrompt();
  const { status: authStatus, enrollment } = useAuth();
  const runtimeConfig = useRuntimeConfig();
  const [status, setStatus] = useState<Status>('loading');
  const [view, setView] = useState<View>('form');
  const [draftId, setDraftId] = useState<string>('');
  const [initialValues, setInitialValues] = useState<FormValues>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [pendingValuesRef, setPendingValuesRef] = useState<FormValues | null>(null);
  const runSyncRef = useRef<() => Promise<SyncRunSummary>>(noopRunSync);

  const enrollmentInfo: EnrollmentInfo | null = useMemo(
    () =>
      enrollment
        ? {
            hcw_id: enrollment.hcw_id,
            facility_id: enrollment.facility_id,
            facility_type: enrollment.facility_type,
          }
        : null,
    [enrollment],
  );

  const specDrift = isServerNewer(LOCAL_SPEC_VERSION, runtimeConfig.min_accepted_spec_version);

  useEffect(() => {
    if (authStatus !== 'enrolled') return;
    const id = getOrCreateDraftId();
    setDraftId(id);
    void loadDraft(id).then((row) => {
      setInitialValues((row?.values as FormValues | undefined) ?? {});
      setStatus('editing');
    });
  }, [authStatus]);

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

  const refresh = useMemo<() => Promise<RefreshResult>>(() => {
    try {
      return buildRefreshFacilities();
    } catch {
      return async () => ({ ok: false, error: { code: 'E_ENV', message: 'Backend env missing' } });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleAutosave = (values: FormValues) => {
    if (!draftId || !enrollmentInfo) return;
    void saveDraft(draftId, values, enrollmentInfo);
  };

  const handleSubmit = async (values: FormValues) => {
    if (!draftId || !enrollmentInfo) {
      console.warn('[F2] submit blocked: missing draftId or enrollment');
      return;
    }
    if (runtimeConfig.kill_switch) {
      console.warn('[F2] submit blocked: kill_switch active');
      setSubmitError(t('chrome.submitBlockedKillSwitch'));
      setPendingValuesRef(values);
      setStatus('submit_failed');
      return;
    }
    if (specDrift) {
      console.warn('[F2] submit blocked: spec_version drift');
      setSubmitError(t('chrome.submitBlockedSpecDrift'));
      setPendingValuesRef(values);
      setStatus('submit_failed');
      return;
    }
    try {
      await saveDraft(draftId, values, enrollmentInfo);
      await submitDraft(draftId, enrollmentInfo);
      setSubmitError(null);
      setPendingValuesRef(null);
      setStatus('submitted');
      void runSyncRef.current();
    } catch (err) {
      console.error('[F2] submit failed:', err);
      setSubmitError(t('chrome.submitFailedBody'));
      setPendingValuesRef(values);
      setStatus('submit_failed');
    }
  };

  const handleRetrySubmit = () => {
    if (pendingValuesRef) {
      void handleSubmit(pendingValuesRef);
    }
  };

  return (
    <main className="flex min-h-screen-dvh flex-col">
      <BroadcastBanner message={runtimeConfig.broadcast_message} />
      <header className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex flex-col">
          <h1 className="text-lg font-semibold">{t('chrome.appTitle')}</h1>
          <span className="text-[10px] leading-none text-muted-foreground/60">v{APP_VERSION}</span>
        </div>
        <div className="flex items-center gap-3">
          <LanguageSwitcher />
          <PendingCount />
          {authStatus === 'enrolled' ? (
            <Button
              size="sm"
              variant={view === 'sync' ? 'default' : 'outline'}
              onClick={() => setView(view === 'sync' ? 'form' : 'sync')}
            >
              {view === 'sync' ? t('chrome.formView') : t('chrome.syncView')}
            </Button>
          ) : null}
          {canInstall ? (
            <Button size="sm" onClick={install}>
              {t('chrome.install')}
            </Button>
          ) : null}
        </div>
      </header>

      {authStatus === 'loading' ? (
        <p className="p-6 text-sm text-muted-foreground">{t('chrome.loading')}</p>
      ) : authStatus === 'unenrolled' ? (
        <EnrollmentScreen onRefresh={refresh} />
      ) : view === 'sync' ? (
        <Suspense
          fallback={<p className="p-6 text-sm text-muted-foreground">{t('chrome.loading')}</p>}
        >
          <SyncPage runSync={runSyncRef.current} />
        </Suspense>
      ) : status === 'loading' ? (
        <p className="p-6 text-sm text-muted-foreground">{t('chrome.loading')}</p>
      ) : status === 'submitted' ? (
        <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
          <h2 className="text-2xl font-semibold">{t('chrome.thankYouHeading')}</h2>
          <p className="text-sm text-muted-foreground">{t('chrome.thankYouBody')}</p>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={() => setView('sync')}>
              {t('sync.viewQueue')}
            </Button>
            <PendingCount />
          </div>
        </section>
      ) : status === 'submit_failed' ? (
        <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
          <h2 className="text-2xl font-semibold text-red-700">
            {t('chrome.submitFailedHeading')}
          </h2>
          <p className="text-sm text-muted-foreground">
            {submitError ?? t('chrome.submitFailedBody')}
          </p>
          <div className="flex items-center gap-3">
            <Button onClick={handleRetrySubmit}>{t('chrome.submitFailedRetry')}</Button>
            <Button variant="outline" onClick={() => setStatus('editing')}>
              {t('review.edit')}
            </Button>
          </div>
        </section>
      ) : (
        <MultiSectionForm
          initialValues={initialValues}
          onAutosave={handleAutosave}
          onSubmit={handleSubmit}
        />
      )}

      <KillSwitchOverlay active={runtimeConfig.kill_switch} />
      <SpecDriftOverlay
        drift={specDrift}
        localVersion={LOCAL_SPEC_VERSION}
        serverMin={runtimeConfig.min_accepted_spec_version}
      />
    </main>
  );
}

export default function App() {
  let fetcher: () => Promise<GetConfigResponse>;
  try {
    fetcher = buildConfigFetcher();
  } catch {
    fetcher = noopConfigFetcher;
  }
  return (
    <LocaleProvider>
      <RuntimeConfigProvider fetcher={fetcher} refreshIntervalMs={CONFIG_REFRESH_INTERVAL_MS}>
        <AuthProvider>
          <AppShell />
        </AuthProvider>
      </RuntimeConfigProvider>
    </LocaleProvider>
  );
}
