import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';
import { getSyncEnv } from '@/lib/env';
import {
  parseFacilityUrl,
  resolveFacilitySlug,
  selfRegisterBySlug,
} from '@/lib/facility-start-client';

/**
 * Facility slug links (design F2-Facility-Slug-Links-2026-07-16).
 *
 * Rendered when an unenrolled device opens `/f/<slug>` (e.g. /f/lphbay). The
 * page load only RESOLVES the slug (read-only) and shows the facility name —
 * nothing is created for casual/bot opens. An explicit Start tap self-registers:
 * the server assigns the next QN in the facility's block and mints a qn-bound
 * device token, and the phone enrolls straight into consent → survey.
 */
export function FacilityStartScreen() {
  const { t } = useTranslation();
  const { enroll } = useAuth();
  const [phase, setPhase] = useState<'resolving' | 'ready' | 'starting' | 'error'>('resolving');
  const [facilityName, setFacilityName] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const ran = useRef(false);

  // Only a definite E_NOT_FOUND means the link is dead — every transient
  // failure (5xx, bad JSON from a proxy error page, kill switch) must say
  // "try again shortly", not tell field HCWs an active link is inactive.
  const messageFor = (code: string): string =>
    code === 'E_NETWORK'
      ? t('facilityStart.offline')
      : code === 'E_NOT_FOUND'
        ? t('facilityStart.inactive')
        : t('facilityStart.unavailable');

  const runResolve = async () => {
    setPhase('resolving');
    setErrorMsg('');
    const parsed = parseFacilityUrl(window.location);
    if (!parsed) {
      setPhase('error');
      setErrorMsg(t('facilityStart.inactive'));
      return;
    }
    try {
      const env = getSyncEnv();
      const result = await resolveFacilitySlug({
        proxyUrl: env.proxyUrl,
        slug: parsed.slug,
        fetchImpl: fetch.bind(globalThis),
      });
      if (!result.ok) {
        setPhase('error');
        setErrorMsg(messageFor(result.error.code));
        return;
      }
      setFacilityName(result.facility_name);
      setPhase('ready');
    } catch (err) {
      setPhase('error');
      setErrorMsg((err as Error).message);
    }
  };

  const runStart = async () => {
    const parsed = parseFacilityUrl(window.location);
    if (!parsed) return;
    setPhase('starting');
    setErrorMsg('');
    try {
      const env = getSyncEnv();
      const result = await selfRegisterBySlug({
        proxyUrl: env.proxyUrl,
        slug: parsed.slug,
        fetchImpl: fetch.bind(globalThis),
      });
      if (!result.ok) {
        setPhase('error');
        setErrorMsg(messageFor(result.error.code));
        return;
      }
      // Bind the device to the fresh case — same shape as any enrollment, so
      // consent/survey/submit/refusal/sync are all inherited. Status flips to
      // 'enrolled' and AppShell swaps this screen out for the survey.
      await enroll({
        hcw_id: result.hcw_id,
        facility_id: result.facility_id,
        ...(result.qn ? { qn: result.qn } : {}),
        device_token: result.token,
      });
    } catch (err) {
      setPhase('error');
      setErrorMsg((err as Error).message);
    }
  };

  useEffect(() => {
    // StrictMode double-invokes effects in dev; guard so we resolve exactly once.
    if (ran.current) return;
    ran.current = true;
    void runResolve();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section className="mx-auto flex max-w-md flex-col gap-4 p-6">
      {phase === 'resolving' ? (
        <>
          <h2 className="font-serif text-2xl font-medium tracking-tight">
            {t('facilityStart.resolvingHeading')}
          </h2>
          <p className="text-sm text-muted-foreground" data-testid="facility-start-progress">
            {t('facilityStart.resolving')}
          </p>
        </>
      ) : phase === 'error' ? (
        <>
          <h2 className="font-serif text-2xl font-medium tracking-tight">
            {t('facilityStart.resolvingHeading')}
          </h2>
          <p className="text-sm text-destructive" data-testid="facility-start-error">
            {errorMsg}
          </p>
          <div>
            <Button type="button" onClick={() => void runResolve()} data-testid="facility-start-retry">
              {t('facilityStart.retry')}
            </Button>
          </div>
        </>
      ) : (
        <>
          <h2
            className="font-serif text-2xl font-medium tracking-tight"
            data-testid="facility-start-name"
          >
            {t('facilityStart.heading', { facility: facilityName })}
          </h2>
          <p className="text-sm text-muted-foreground">{t('facilityStart.intro')}</p>
          <div>
            <Button
              type="button"
              size="lg"
              onClick={() => void runStart()}
              disabled={phase === 'starting'}
              data-testid="facility-start-button"
            >
              {phase === 'starting' ? t('facilityStart.starting') : t('facilityStart.start')}
            </Button>
          </div>
        </>
      )}
    </section>
  );
}
