import { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';

// Lazy-load the admin portal so HCW respondents — the dominant traffic class —
// don't pay for the admin chunk on first paint. Closes #275 in combination
// with the manualChunks split in vite.config.ts; together they take the HCW
// initial-load JS from ~930 KB raw (single chunk) down to index + vendor only.
const AdminApp = lazy(() => import('@/admin/App'));
import { MultiSectionForm } from '@/components/survey/MultiSectionForm';
import { EnrollmentScreen } from '@/components/enrollment/EnrollmentScreen';
import { ClaimScreen } from '@/components/enrollment/ClaimScreen';
import { FacilityStartScreen } from '@/components/enrollment/FacilityStartScreen';
import { parseClaimUrl } from '@/lib/claim-client';
import { parseFacilityUrl } from '@/lib/facility-start-client';
import { ConsentScreen } from '@/components/survey/ConsentScreen';
import { PendingCount } from '@/components/sync/PendingCount';
import { DeliveryStatus } from '@/components/sync/DeliveryStatus';
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
  COMPLETED_CSID_KEY,
  DRAFT_ID_KEY,
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

type Status = 'loading' | 'consent' | 'editing' | 'declined' | 'submitted' | 'submit_failed';
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
  const { status: authStatus, enrollment, unenroll } = useAuth();
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
            ...(enrollment.qn ? { qn: enrollment.qn } : {}),
            // facility_type is optional on EnrollmentRow (Issue #46); only
            // include the field if populated so exactOptionalPropertyTypes
            // is happy.
            ...(enrollment.facility_type ? { facility_type: enrollment.facility_type } : {}),
          }
        : null,
    [enrollment],
  );

  const specDrift = isServerNewer(LOCAL_SPEC_VERSION, runtimeConfig.min_accepted_spec_version);

  // Model C — a `/e/<slug>?k=…` deep link is a numbered self-register claim: an
  // unenrolled device auto-claims its pre-assigned QN slot instead of showing the
  // token-paste enrollment. Computed once per load (the URL doesn't change here).
  const claimTarget = typeof window !== 'undefined' ? parseClaimUrl(window.location) : null;
  // Facility slug links (design F2-Facility-Slug-Links-2026-07-16): `/f/<slug>`
  // is the per-facility public start page — the PRIMARY way in. The token-paste
  // EnrollmentScreen stays reachable behind /enroll for enumerator-assisted use.
  const facilityTarget = typeof window !== 'undefined' ? parseFacilityUrl(window.location) : null;
  const legacyEnroll =
    typeof window !== 'undefined' && window.location.pathname.startsWith('/enroll');

  useEffect(() => {
    if (authStatus !== 'enrolled') return;
    // R2-#120 S.A2: persist submitted state across refresh. After a
    // successful submit, COMPLETED_CSID_KEY is written to localStorage.
    // On refresh, short-circuit to status='submitted' so the user lands
    // back on the thank-you screen (not Section A) until they click
    // "Start new survey".
    if (typeof localStorage !== 'undefined' && localStorage.getItem(COMPLETED_CSID_KEY)) {
      setStatus('submitted');
      return;
    }
    const id = getOrCreateDraftId();
    setDraftId(id);
    void loadDraft(id).then((row) => {
      const values = (row?.values as FormValues | undefined) ?? {};
      setInitialValues(values);
      // #808: consent is a per-case gate. Resumed drafts that already carry
      // consent_given skip it (a mid-survey refresh must not re-prompt);
      // fresh cases land on the ConsentScreen before Section A.
      setStatus(values['consent_given'] === 1 ? 'editing' : 'consent');
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
      // §15.B: consent_given (+ consent_timestamp) now arrives in `values`,
      // written by the ConsentScreen gate before Section A opens (#808) — no
      // longer assumed at submit time.
      const valuesWithMeta: FormValues = { ...values, survey_language: locale };
      await saveDraft(draftId, valuesWithMeta, enrollmentInfo);
      // Capture GPS at the click moment (5s timeout). Per spec §9 the
      // disclosure is shown on the review screen near submit. Submission rides
      // through with null coords if the user declines or the browser doesn't
      // support geolocation — and the OUTCOME (granted/denied/timeout/…) is
      // recorded so the admin Map Report can explain missing GPS (audit P1-4).
      const { coords, status: gpsStatus } = await getGeolocation();
      const submission = await submitDraft(draftId, enrollmentInfo, coords, gpsStatus);
      // R2-#120 S.A2: persist the submitted state across refresh.
      // The thank-you screen reads COMPLETED_CSID_KEY on next mount.
      try {
        localStorage.setItem(COMPLETED_CSID_KEY, submission.client_submission_id);
      } catch {
        // localStorage can throw in private-mode Safari etc.; the
        // in-memory status='submitted' below still renders the thank-
        // you screen for the current session, just without refresh
        // persistence. Non-blocking.
      }
      setSubmitError(null);
      setPendingValuesRef(null);
      setStatus('submitted');
      // Immediate delivery push — but only when not definitely offline. An
      // offline run would just burn the row into retry_scheduled (+30s), and
      // a reconnect inside that window finds nothing ready (findReady skips
      // unelapsed retries), stranding a one-and-done phone until the 5-min
      // interval. Left pending_sync, the 'online' trigger sends it instantly.
      if (typeof navigator === 'undefined' || navigator.onLine !== false) {
        void runSyncRef.current();
      }
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

  // R2-#120 S.A2: clear the submitted-persistence flag and start a
  // fresh survey. Also clears DRAFT_ID_KEY so getOrCreateDraftId
  // mints a new draft id; otherwise the previous draft id (already
  // submitted, so its draft was deleted) would resolve to nothing
  // and the form would still render but empty.
  const handleStartNewSurvey = () => {
    try {
      localStorage.removeItem(COMPLETED_CSID_KEY);
    } catch {
      /* private-mode Safari etc. — non-blocking */
    }
    // Facility-slug devices (opened via /f/<slug>) are one-case-per-
    // registration: this enrollment's token is bound to THIS respondent's QN,
    // so a second respondent must NOT reuse it (two people would share one
    // 12-digit case key). Unenroll instead — enroll() cleared per-case state,
    // AppShell falls back to the FacilityStartScreen, and the next respondent's
    // Start tap self-registers a fresh sr- case with its own QN.
    if (facilityTarget) {
      try {
        localStorage.removeItem(DRAFT_ID_KEY);
      } catch {
        /* non-blocking */
      }
      void unenroll();
      return;
    }
    const id = getOrCreateDraftId();
    setDraftId(id);
    setInitialValues({});
    setSubmitError(null);
    setPendingValuesRef(null);
    // #808: every new case (a new respondent on the same enrolled device)
    // re-consents before Section A.
    setStatus('consent');
  };

  // #808: record affirmative consent into the case values before Section A
  // opens. consent_given=1 keeps audit parity with the F1/F3/F4 CONSENT_GIVEN
  // field; consent_timestamp (epoch ms) documents when the respondent agreed.
  const handleConsentAgree = () => {
    const withConsent: FormValues = {
      ...initialValues,
      consent_given: 1,
      consent_timestamp: Date.now(),
    };
    setInitialValues(withConsent);
    if (draftId && enrollmentInfo) void saveDraft(draftId, withConsent, enrollmentInfo);
    setStatus('editing');
  };

  // #825: a decline is DATA, not a dead end — queue a refusal submission
  // (consent_given=0) through the normal offline-safe pipeline so the Admin
  // page can tag the respondent "Refusal". No geolocation: location is never
  // requested from someone who just declined. Fire-and-forget: the declined
  // screen shows regardless; the Dexie queue + sync backoff handle offline
  // and transient failures. submitDraft clears DRAFT_ID_KEY, so Start-over
  // mints a fresh case (per-case semantics, #808).
  const handleConsentDecline = async () => {
    try {
      if (draftId && enrollmentInfo) {
        const refusalValues: FormValues = {
          ...initialValues,
          consent_given: 0,
          consent_timestamp: Date.now(),
          survey_language: locale,
        };
        await saveDraft(draftId, refusalValues, enrollmentInfo);
        // GPS is never requested from someone who just declined consent —
        // recorded as 'not_requested' (the submitDraft default).
        await submitDraft(draftId, enrollmentInfo, null, 'not_requested');
        // Same offline guard as handleSubmit: keep the row pending_sync so the
        // on-reconnect trigger delivers it immediately.
        if (typeof navigator === 'undefined' || navigator.onLine !== false) {
          void runSyncRef.current();
        }
      }
    } catch (err) {
      console.error('[F2] refusal queue failed (non-blocking):', err);
    }
    setStatus('declined');
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
        claimTarget ? (
          <ClaimScreen />
        ) : facilityTarget ? (
          <FacilityStartScreen />
        ) : legacyEnroll ? (
          <EnrollmentScreen />
        ) : (
          <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
            <h2 className="font-serif text-2xl font-medium tracking-tight">
              {t('facilityStart.noLinkHeading')}
            </h2>
            <p className="text-sm text-muted-foreground">{t('facilityStart.noLinkBody')}</p>
          </section>
        )
      ) : view === 'sync' ? (
        <Suspense
          fallback={<p className="p-6 text-sm text-muted-foreground">{t('chrome.loading')}</p>}
        >
          <SyncPage runSync={runSyncRef.current} />
        </Suspense>
      ) : status === 'loading' ? (
        <p className="p-6 text-sm text-muted-foreground">{t('chrome.loading')}</p>
      ) : status === 'consent' ? (
        <ConsentScreen onAgree={handleConsentAgree} onDecline={() => void handleConsentDecline()} />
      ) : status === 'declined' ? (
        <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
          <h2 className="font-serif text-2xl font-medium tracking-tight">
            {t('consent.declinedHeading')}
          </h2>
          <p className="text-sm text-muted-foreground">{t('consent.declinedBody')}</p>
          <div>
            <Button onClick={handleStartNewSurvey}>{t('consent.startOver')}</Button>
          </div>
        </section>
      ) : status === 'submitted' ? (
        <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
          <h2 className="font-serif text-2xl font-medium tracking-tight">
            {t('chrome.thankYouHeading')}
          </h2>
          {/* Sync-on-submit delivery gate: "Submitting…" → "Submitted ✓" (or the
              offline "saved, will send" line) instead of a static promise. */}
          <DeliveryStatus />
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={handleStartNewSurvey}>{t('chrome.startNewSurvey')}</Button>
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
    return (
      <Suspense
        fallback={
          <div className="flex min-h-screen items-center justify-center bg-paper text-sm text-muted-foreground">
            Loading admin portal…
          </div>
        }
      >
        <AdminApp apiBaseUrl={proxyUrl} />
      </Suspense>
    );
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
