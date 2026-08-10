/**
 * F2 Admin Portal — Add/Edit facility dialog (spec F2-Facility-Master-Mgmt-2026-07-16).
 *
 * create: editable 9-digit id; edit: id frozen (immutable — QNs embed it).
 * Region/province offer <datalist> autocompletes (canonical PSGC regions +
 * provinces already on file) but stay free text — geo mismatches WARN on save
 * (server-computed), never block. Warnings keep the dialog open so the admin
 * actually sees them; a clean save closes immediately.
 */
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';
import { PH_REGIONS } from './ph-regions';

const FACILITY_ID_RE = /^\d{9}$/;

export interface FacilityFormValues {
  facility_id: string;
  facility_name: string;
  facility_type: string;
  region: string;
  province: string;
  city_mun: string;
  barangay: string;
  /** Coverage target quota, kept as raw text — the server parses/validates
   *  (junk 400s; blank clears). Never Number()-coerced client-side: NaN would
   *  JSON-serialize to null and silently clear instead of erroring. */
  target_hcws: string;
}

export interface FacilityEditDialogProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
  mode: 'create' | 'edit';
  /** Pre-fill (edit mode: the row; create mode: usually empty). */
  initial: Partial<Omit<FacilityFormValues, 'target_hcws'>> & { target_hcws?: number | null };
  /** Provinces already on file — datalist suggestions. */
  knownProvinces: string[];
  onSaved: () => void;
  onClose: () => void;
}

export function FacilityEditDialog({
  apiBaseUrl,
  fetchImpl,
  mode,
  initial,
  knownProvinces,
  onSaved,
  onClose,
}: FacilityEditDialogProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [values, setValues] = useState<FacilityFormValues>({
    facility_id: initial.facility_id ?? '',
    facility_name: initial.facility_name ?? '',
    facility_type: initial.facility_type ?? '',
    region: initial.region ?? '',
    province: initial.province ?? '',
    city_mun: initial.city_mun ?? '',
    barangay: initial.barangay ?? '',
    target_hcws: initial.target_hcws == null ? '' : String(initial.target_hcws),
  });
  const [saving, setSaving] = useState(false);
  const [warnings, setWarnings] = useState<string[] | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !saving) onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose, saving]);

  const set = (k: keyof FacilityFormValues) => (v: string) =>
    setValues((prev) => ({ ...prev, [k]: v }));

  const canSave =
    !saving &&
    values.facility_name.trim().length > 0 &&
    values.facility_name.trim().length <= 255 &&
    (mode === 'edit' || FACILITY_ID_RE.test(values.facility_id.trim()));

  const onSave = async () => {
    setSaving(true);
    setError(null);
    const opts = {
      ...(token ? { token } : {}),
      onUnauthorized: () => {
        clearAuth();
        navigate('/admin/login');
      },
      onPasswordChangeRequired: () => navigate('/admin/me/change-password'),
      ...(fetchImpl ? { fetchImpl } : {}),
    };
    // Blank target = clear (explicit null); non-blank rides as a string for the
    // server to parse (junk → E_VALIDATION shown here, never a silent null).
    const targetWire = values.target_hcws.trim() === '' ? null : values.target_hcws.trim();
    const r =
      mode === 'create'
        ? await adminFetch<{ ok: true; warnings: string[] }>(
            `${apiBaseUrl}/admin/api/facilities`,
            { method: 'POST', body: JSON.stringify({ ...values, target_hcws: targetWire }) },
            opts,
          )
        : await adminFetch<{ ok: true; warnings: string[] }>(
            `${apiBaseUrl}/admin/api/facilities/${encodeURIComponent(values.facility_id)}`,
            {
              method: 'PATCH',
              body: JSON.stringify({
                facility_name: values.facility_name,
                facility_type: values.facility_type,
                region: values.region,
                province: values.province,
                city_mun: values.city_mun,
                barangay: values.barangay,
                target_hcws: targetWire,
              }),
            },
            opts,
          );
    setSaving(false);
    if (!r.ok) {
      setError(r.error);
      return;
    }
    onSaved();
    if (r.data.warnings.length > 0) {
      // Keep the dialog open so the geo warnings are actually seen.
      setWarnings(r.data.warnings);
    } else {
      onClose();
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={mode === 'create' ? 'Add facility' : 'Edit facility'}
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/70 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !saving) onClose();
      }}
    >
      <div className="max-h-[90vh] w-full max-w-xl overflow-y-auto border border-hairline bg-paper p-6">
        <header className="border-b border-hairline pb-3">
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Facility master
          </p>
          <h3 className="mt-1 font-serif text-xl font-medium tracking-tight">
            {mode === 'create' ? 'Add facility' : 'Edit facility'}
          </h3>
        </header>

        <div className="mt-4 flex flex-col gap-4">
          {error ? (
            <div role="alert" className="border-l-2 border-error py-2 pl-3">
              <p className="text-sm text-error">{messageFor(error)}</p>
              {error.requestId ? (
                <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
              ) : null}
            </div>
          ) : null}

          {warnings ? (
            <div className="border-l-2 border-warning py-2 pl-3" data-testid="edit-warnings">
              <p className="font-mono text-xs uppercase tracking-wider text-warning">
                Saved, with warnings
              </p>
              {warnings.map((w) => (
                <p key={w} className="mt-1 text-sm text-warning">
                  {w}
                </p>
              ))}
              <div className="mt-3">
                <Button type="button" onClick={onClose} className="h-9 px-3 text-xs">
                  Close
                </Button>
              </div>
            </div>
          ) : (
            <>
              <Field label="Facility ID (9-digit — immutable once created)">
                {mode === 'create' ? (
                  <input
                    type="text"
                    inputMode="numeric"
                    value={values.facility_id}
                    onChange={(e) => set('facility_id')(e.target.value)}
                    placeholder="040341130"
                    data-testid="edit-facility-id"
                    className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
                  />
                ) : (
                  <span className="py-1 font-mono text-sm text-muted-foreground" data-testid="edit-facility-id-frozen">
                    {values.facility_id}
                  </span>
                )}
              </Field>
              <Field label="Facility name">
                <input
                  type="text"
                  value={values.facility_name}
                  onChange={(e) => set('facility_name')(e.target.value)}
                  placeholder="RHU Daraga I"
                  data-testid="edit-facility-name"
                  className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
                />
              </Field>
              <Field label="Type">
                <input
                  type="text"
                  value={values.facility_type}
                  onChange={(e) => set('facility_type')(e.target.value)}
                  placeholder="Rural Health Unit"
                  data-testid="edit-facility-type"
                  className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
                />
              </Field>
              <Field label="Region (canonical PSGC name — mismatches warn)">
                <input
                  type="text"
                  list="fm-regions"
                  value={values.region}
                  onChange={(e) => set('region')(e.target.value)}
                  placeholder="Region IV-A (CALABARZON)"
                  data-testid="edit-region"
                  className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
                />
                <datalist id="fm-regions">
                  {PH_REGIONS.map((r) => (
                    <option key={r} value={r} />
                  ))}
                </datalist>
              </Field>
              <Field label="Province">
                <input
                  type="text"
                  list="fm-provinces"
                  value={values.province}
                  onChange={(e) => set('province')(e.target.value)}
                  placeholder="Laguna"
                  data-testid="edit-province"
                  className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
                />
                <datalist id="fm-provinces">
                  {knownProvinces.map((p) => (
                    <option key={p} value={p} />
                  ))}
                </datalist>
              </Field>
              <Field label="Target HCWs (coverage quota — blank = none)">
                <input
                  type="text"
                  inputMode="numeric"
                  value={values.target_hcws}
                  onChange={(e) => set('target_hcws')(e.target.value)}
                  placeholder="25"
                  data-testid="edit-target"
                  className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
                />
              </Field>
              <div className="flex gap-4">
                <Field label="City / Municipality">
                  <input
                    type="text"
                    value={values.city_mun}
                    onChange={(e) => set('city_mun')(e.target.value)}
                    data-testid="edit-city-mun"
                    className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
                  />
                </Field>
                <Field label="Barangay">
                  <input
                    type="text"
                    value={values.barangay}
                    onChange={(e) => set('barangay')(e.target.value)}
                    data-testid="edit-barangay"
                    className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
                  />
                </Field>
              </div>
              <div className="flex flex-wrap gap-3 border-t border-hairline pt-3">
                <Button
                  type="button"
                  onClick={() => void onSave()}
                  disabled={!canSave}
                  data-testid="edit-save"
                  className="h-10"
                >
                  {saving ? 'Saving…' : mode === 'create' ? 'Add facility' : 'Save changes'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={onClose}
                  disabled={saving}
                  className="h-10 border-hairline hover:bg-secondary disabled:opacity-50"
                >
                  Cancel
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }): JSX.Element {
  return (
    <label className="flex min-w-0 flex-1 flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}

function messageFor(error: ApiError): string {
  if (error.code === 'E_VALIDATION') return error.message ?? 'Check the fields.';
  if (error.code === 'E_CONFLICT') return error.message ?? 'This facility ID already exists.';
  if (error.code === 'E_PERM_DENIED') return 'Your role lacks dash_users.';
  if (error.code === 'E_NETWORK') return 'Network unavailable. Retry when reconnected.';
  if (error.code === 'E_BACKEND') return 'Backend unavailable. Try again shortly.';
  return error.message ?? 'Could not save the facility.';
}
