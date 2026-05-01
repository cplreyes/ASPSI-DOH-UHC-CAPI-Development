import { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import AdminApp from '@/admin/App';
import { MultiSectionForm } from '@/components/survey/MultiSectionForm';
import { EnrollmentScreen } from '@/components/enrollment/EnrollmentScreen';
import { PendingCount } from '@/components/sync/PendingCount';
import { LanguageSwitcher } from '@/components/i18n/LanguageSwitcher';
import { BroadcastBanner } from '@/components/chrome/BroadcastBanner';
import { KillSwitchOverlay } from '@/components/chrome/KillSwitchOverlay';
import { SpecDriftOverlay } from '@/components/chrome/SpecDriftOverlay';
import { LocaleProvider, useLocale } from '@/i18n/locale-context';
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
import { getDeviceToken } from '@/lib/enrollment';
import { getGeolocation } from '@/lib/geolocation';
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

function buildRunSync(deviceToken: string): () => Promise<SyncRunSummary> {
  const env = getSyncEnv();
  const fingerprint = getOrCreateDeviceFingerprint();
  return () =>
    runSync({
      postBatchSubmit: (items) =>
        postBatchSubmit(items, {
          proxyUrl: env.proxyUrl,
          deviceToken,
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

function buildRefreshFacilities(deviceToken: string): () => Promise<RefreshResult> {
  const env = getSyncEnv();
  return () =>
    refreshFacilities({
      fetcher: () =>
        getFacilities({
          proxyUrl: env.proxyUrl,
          deviceToken,
          fetchImpl: fetch.bind(globalThis),
        }),
    });
}

/**
 * Config fetcher reads the latest device token from Dexie on each call. This avoids
 * the chicken-and-egg of needing the token at App-mount time (when AuthProvider
 * hasn't loaded enrollment yet) and naturally pauses config polls until a tablet
 * is enrolled.
 */
function buildConfigFetcher(): () => Promise<GetConfigResponse> {
  const env = getSyncEnv();
  return async () => {
    const tokenInfo = await getDeviceToken();
    if (!tokenInfo) {
      return { ok: false, transport: false, error: { code: 'E_ENV', message: 'No device token' } };
    }
    return getConfig({
      proxyUrl: env.proxyUrl,
      deviceToken: tokenInfo.token,
      fetchImpl: fetch.bind(globalThis),
    });
  };
}

const noopConfigFetcher: () => Promise<GetConfigResponse> = async () => ({
  ok: false,
  transport: true,
  error: { code: 'E_ENV', message: 'Backend env missing' },
});

function AppShell() {
  const { t } = useTranslation();
  const { locale } = useLocale();
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
            // facility_type is optional on EnrollmentRow (Issue #46); only
            // include the field if populated so exactOptionalPropertyTypes
            // is happy.
            ...(enrollment.facility_type ? { facility_type: enrollment.facility_type } : {}),
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

  const deviceToken = enrollment?.device_token ?? '';

  useEffect(() => {
    let triggers: { stop: () => void } | null = null;
    if (!deviceToken) {
      runSyncRef.current = noopRunSync;
      return () => {};
    }
    try {
      runSyncRef.current = buildRunSync(deviceToken);
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
  }, [deviceToken]);

  const refresh = useMemo<() => Promise<RefreshResult>>(() => {
    if (!deviceToken) {
      return async () => ({ ok: false, error: { code: 'E_ENV', message: 'No device token' } });
    }
    try {
      return buildRefreshFacilities(deviceToken);
    } catch {
      return async () => ({ ok: false, error: { code: 'E_ENV', message: 'Backend env missing' } });
    }
  }, [deviceToken]);

  useEffect(() => {
    if (deviceToken) void refresh();
  }, [refresh, deviceToken]);

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
      // Auto-inject the active locale so the harmonization ETL can stratify
      // by language without needing the user to declare it explicitly. See
      // codebook §13 (survey_language) and §15.E.
      const valuesWithMeta: FormValues = { ...values, survey_language: locale };
      await saveDraft(draftId, valuesWithMeta, enrollmentInfo);
      // Capture GPS at the click moment (5s timeout, all failures map to null).
      // Per spec §9 the disclosure is shown on the review screen near submit.
      // Submission rides through with null coords if the user declines or the
      // browser doesn't support geolocation — admin Map Report tolerates it.
      const coords = await getGeolocation();
      await submitDraft(draftId, enrollmentInfo, coords);
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
    <main className="mx-auto flex min-h-screen-dvh w-full max-w-screen-xl flex-col">
      <BroadcastBanner message={runtimeConfig.broadcast_message} />
      <header className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex flex-col">
          <h1 className="font-serif text-3xl font-medium tracking-tight">{t('chrome.appTitle')}</h1>
          <span className="font-mono text-xs leading-none text-muted-foreground">
            v{APP_VERSION} · spec {LOCAL_SPEC_VERSION}
          </span>
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
        <EnrollmentScreen />
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
          <h2 className="font-serif text-2xl font-medium tracking-tight">
            {t('chrome.thankYouHeading')}
          </h2>
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
          <h2 className="font-serif text-2xl font-medium tracking-tight text-destructive">
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
  // Delegate /admin/* to the admin portal (Task 2.14). Shares the Pages
  // domain but uses a separate provider tree — admin auth is JWT-in-memory,
  // not the Dexie-backed tablet enrollment used by the PWA below.
  if (typeof window !== 'undefined' && window.location.pathname.startsWith('/admin')) {
    let proxyUrl = '';
    try {
      proxyUrl = getSyncEnv().proxyUrl;
    } catch {
      // VITE_F2_PROXY_URL unset — admin will surface E_NETWORK on login.
    }
    return <AdminApp apiBaseUrl={proxyUrl} />;
  }

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
