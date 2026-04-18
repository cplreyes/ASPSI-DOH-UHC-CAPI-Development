import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';
import { listFacilities, type RefreshResult } from '@/lib/facilities-cache';
import type { FacilityRow } from '@/lib/db';

interface EnrollmentScreenProps {
  onRefresh: () => Promise<RefreshResult>;
}

export function EnrollmentScreen({ onRefresh }: EnrollmentScreenProps) {
  const { t } = useTranslation();
  const { enroll } = useAuth();
  const [facilities, setFacilities] = useState<FacilityRow[]>([]);
  const [hcwId, setHcwId] = useState('');
  const [facilityId, setFacilityId] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void listFacilities().then(setFacilities);
  }, []);

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
    try {
      await enroll({ hcw_id: hcwId, facility_id: facilityId });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const canSubmit = hcwId.trim().length > 0 && facilityId.length > 0 && !refreshing;

  return (
    <form onSubmit={handleEnroll} className="mx-auto flex max-w-md flex-col gap-4 p-6">
      <h2 className="text-2xl font-semibold tracking-tight">{t('enrollment.heading')}</h2>
      <p className="text-sm text-muted-foreground">{t('enrollment.helper')}</p>

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

      <label className="flex flex-col gap-1 text-sm">
        {t('enrollment.facilityLabel')}
        {facilities.length === 0 ? (
          <span className="text-sm text-muted-foreground">
            {t('enrollment.noFacilitiesCached')}
          </span>
        ) : (
          <select
            value={facilityId}
            onChange={(e) => setFacilityId(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">{t('enrollment.facilityPlaceholder')}</option>
            {facilities.map((f) => (
              <option key={f.facility_id} value={f.facility_id}>
                {f.facility_name}
              </option>
            ))}
          </select>
        )}
      </label>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={!canSubmit}>
          {t('enrollment.enrollButton')}
        </Button>
        <Button type="button" variant="outline" onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? t('enrollment.refreshingButton') : t('enrollment.refreshButton')}
        </Button>
      </div>
    </form>
  );
}
