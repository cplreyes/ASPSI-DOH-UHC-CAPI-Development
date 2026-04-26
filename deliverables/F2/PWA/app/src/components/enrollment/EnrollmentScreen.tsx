import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';
import { listFacilities, type RefreshResult } from '@/lib/facilities-cache';
import type { FacilityRow } from '@/lib/db';
import { getSyncEnv } from '@/lib/env';
import { verifyDeviceToken } from '@/lib/verify-token-client';

interface EnrollmentScreenProps {
  onRefresh: () => Promise<RefreshResult>;
}

/**
 * Two-step enrollment after the auth re-arch (spec §4.2):
 *   Step 1: paste tablet token, verify against Worker, store claims locally.
 *   Step 2: pick yourself from the facility's roster (facility is pre-locked
 *           by the token's `facility_id` claim — only the HCW ID picker is shown).
 */
export function EnrollmentScreen({ onRefresh }: EnrollmentScreenProps) {
  const { t } = useTranslation();
  const { enroll } = useAuth();

  // Step 1 state
  const [tokenInput, setTokenInput] = useState('');
  const [verifiedToken, setVerifiedToken] = useState<string | null>(null);
  const [tokenFacilityId, setTokenFacilityId] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);

  // Step 2 state
  const [facilities, setFacilities] = useState<FacilityRow[]>([]);
  const [hcwId, setHcwId] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void listFacilities().then(setFacilities);
  }, []);

  const facilityFromToken = tokenFacilityId
    ? (facilities.find((f) => f.facility_id === tokenFacilityId) ?? null)
    : null;

  const handleVerifyToken = async () => {
    setError(null);
    const token = tokenInput.trim();
    if (token.length === 0) return;
    setVerifying(true);
    try {
      const env = getSyncEnv();
      const result = await verifyDeviceToken(token, {
        proxyUrl: env.proxyUrl,
        fetchImpl: fetch.bind(globalThis),
      });
      if (!result.ok) {
        const code = result.error.code;
        const msg =
          code === 'E_TOKEN_REVOKED' ? t('enrollment.tokenRevoked') : t('enrollment.tokenInvalid');
        setError(msg);
        return;
      }
      setVerifiedToken(token);
      setTokenFacilityId(result.claims.facility_id);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setVerifying(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    try {
      const result = await onRefresh();
      if (!result.ok) {
        setError(result.error.message);
      }
      setFacilities(await listFacilities());
    } finally {
      setRefreshing(false);
    }
  };

  const handleEnroll = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!verifiedToken || !tokenFacilityId) return;
    try {
      await enroll({
        hcw_id: hcwId,
        facility_id: tokenFacilityId,
        device_token: verifiedToken,
      });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const canVerify = tokenInput.trim().length > 0 && !verifying;
  const canSubmit = !!verifiedToken && hcwId.trim().length > 0 && !refreshing;

  return (
    <form onSubmit={handleEnroll} className="mx-auto flex max-w-md flex-col gap-4 p-6">
      <h2 className="text-2xl font-semibold tracking-tight">{t('enrollment.heading')}</h2>

      {/* Step 1 — Tablet token */}
      <section className="flex flex-col gap-2 rounded-md border border-border p-4">
        <h3 className="text-sm font-semibold">{t('enrollment.tokenStep')}</h3>
        <p className="text-sm text-muted-foreground">{t('enrollment.tokenHelper')}</p>

        <label className="flex flex-col gap-1 text-sm">
          {t('enrollment.tokenLabel')}
          <textarea
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            placeholder={t('enrollment.tokenPlaceholder')}
            rows={3}
            disabled={!!verifiedToken}
            className="rounded-md border border-input px-3 py-2 font-mono text-xs"
            data-testid="enrollment-token-input"
          />
        </label>

        {!verifiedToken ? (
          <Button type="button" onClick={handleVerifyToken} disabled={!canVerify}>
            {verifying ? t('enrollment.verifyingTokenButton') : t('enrollment.verifyTokenButton')}
          </Button>
        ) : (
          <p className="text-sm text-green-700" data-testid="enrollment-token-accepted">
            {t('enrollment.tokenAccepted', {
              facility: facilityFromToken?.facility_name ?? tokenFacilityId,
            })}
          </p>
        )}
      </section>

      {/* Step 2 — Identity (only after token verified) */}
      {verifiedToken ? (
        <section className="flex flex-col gap-2 rounded-md border border-border p-4">
          <h3 className="text-sm font-semibold">{t('enrollment.identityStep')}</h3>

          <label className="flex flex-col gap-1 text-sm">
            {t('enrollment.hcwIdLabel')}
            <input
              type="text"
              value={hcwId}
              onChange={(e) => setHcwId(e.target.value)}
              className="rounded-md border border-input px-3 py-2 text-sm"
              autoComplete="off"
            />
          </label>

          {!facilityFromToken && facilities.length === 0 ? (
            <span className="text-sm text-muted-foreground">
              {t('enrollment.noFacilitiesCached')}
            </span>
          ) : null}

          <div className="flex items-center gap-3">
            <Button type="submit" disabled={!canSubmit}>
              {t('enrollment.enrollButton')}
            </Button>
            <Button type="button" variant="outline" onClick={handleRefresh} disabled={refreshing}>
              {refreshing ? t('enrollment.refreshingButton') : t('enrollment.refreshButton')}
            </Button>
          </div>
        </section>
      ) : null}

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
    </form>
  );
}
