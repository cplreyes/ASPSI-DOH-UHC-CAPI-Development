import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';
import { getSyncEnv } from '@/lib/env';
import { claimBySlug, parseClaimUrl } from '@/lib/claim-client';

/**
 * Model C — numbered short-link claim (design F2-Model-C-Numbered-Links-2026-07-16).
 *
 * Rendered when an unenrolled device opens `/e/<slug>?k=<secret>`. There is no
 * token box and no HCW-ID picker: the URL IS the credential. On mount we POST the
 * slug+secret to `/claim`; on success we enroll device-bound to the returned QN,
 * which flips auth status to 'enrolled' and hands off to the normal consent →
 * survey flow. On failure we show a plain message + Retry.
 */
export function ClaimScreen() {
  const { t } = useTranslation();
  const { enroll } = useAuth();
  const [phase, setPhase] = useState<'claiming' | 'error'>('claiming');
  const [errorMsg, setErrorMsg] = useState('');
  const ran = useRef(false);

  const runClaim = async () => {
    setPhase('claiming');
    setErrorMsg('');
    const parsed = parseClaimUrl(window.location);
    if (!parsed || !parsed.slug || !parsed.k) {
      setPhase('error');
      setErrorMsg(t('claim.invalidLink'));
      return;
    }
    try {
      const env = getSyncEnv();
      const result = await claimBySlug({
        proxyUrl: env.proxyUrl,
        slug: parsed.slug,
        k: parsed.k,
        fetchImpl: fetch.bind(globalThis),
      });
      if (!result.ok) {
        setPhase('error');
        const code = result.error.code;
        setErrorMsg(
          code === 'E_NETWORK'
            ? t('claim.offline')
            : code === 'E_CONFLICT'
              ? t('claim.alreadyDone')
              : code === 'E_KILL_SWITCH'
                ? t('claim.unavailable')
                : t('claim.invalidLink'),
        );
        return;
      }
      // Bind the device to the claimed slot — same shape as any enrollment, so
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
    // StrictMode double-invokes effects in dev; guard so we claim exactly once.
    if (ran.current) return;
    ran.current = true;
    void runClaim();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section className="mx-auto flex max-w-md flex-col gap-4 p-6">
      <h2 className="font-serif text-2xl font-medium tracking-tight">{t('claim.heading')}</h2>
      {phase === 'claiming' ? (
        <p className="text-sm text-muted-foreground" data-testid="claim-progress">
          {t('claim.claiming')}
        </p>
      ) : (
        <>
          <p className="text-sm text-destructive" data-testid="claim-error">
            {errorMsg}
          </p>
          <div>
            <Button type="button" onClick={() => void runClaim()} data-testid="claim-retry">
              {t('claim.retry')}
            </Button>
          </div>
        </>
      )}
    </section>
  );
}
