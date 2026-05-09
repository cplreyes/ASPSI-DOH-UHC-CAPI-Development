/**
 * F2 Admin Portal — Create HCW modal (R2-#58, E4-APRT-041).
 *
 * First-class provisioning form. Pairs with the Reissue Token flow:
 * Create here lands a row in F2_HCWs at status='pending'; an admin then
 * clicks Reissue on that row to mint the enrollment token. Done together
 * they're the full HCW provisioning lifecycle.
 *
 * Verde Manual identity matched to UserEditor / RoleEditor: hairline-
 * bordered card overlay, mono-uppercase field labels, JetBrains Mono on
 * the hcw_id and facility_id keyholes, signal-color primary CTA. Closes
 * on backdrop click or Escape; submits via POST /admin/api/hcws.
 */
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

const HCW_ID_RE = /^[A-Za-z0-9_\-]{1,64}$/;
const FACILITY_ID_RE = /^[A-Za-z0-9_\-]{1,32}$/;

export interface CreateHCWModalProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
  onClose: () => void;
  onCreated: (hcwId: string) => void;
}

export function CreateHCWModal({ apiBaseUrl, fetchImpl, onClose, onCreated }: CreateHCWModalProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();

  const [hcwId, setHcwId] = useState('');
  const [facilityId, setFacilityId] = useState('');
  const [facilityName, setFacilityName] = useState('');
  const [error, setError] = useState<ApiError | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const firstFieldRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    firstFieldRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !submitting) onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose, submitting]);

  const localValidationError = (): string | null => {
    if (!HCW_ID_RE.test(hcwId)) return 'HCW ID must be 1–64 chars [A-Za-z0-9_-]';
    if (!FACILITY_ID_RE.test(facilityId)) return 'Facility ID must be 1–32 chars [A-Za-z0-9_-]';
    return null;
  };

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (submitting) return;
    setError(null);

    const localErr = localValidationError();
    if (localErr) {
      setError({ code: 'E_VALIDATION', message: localErr });
      return;
    }

    setSubmitting(true);
    const r = await adminFetch<{ hcw_id: string; facility_id: string; status: string }>(
      `${apiBaseUrl}/admin/api/hcws`,
      {
        method: 'POST',
        body: JSON.stringify({
          hcw_id: hcwId.trim(),
          facility_id: facilityId.trim(),
          ...(facilityName.trim() ? { facility_name: facilityName.trim() } : {}),
        }),
      },
      {
        ...(token ? { token } : {}),
        onUnauthorized: () => {
          clearAuth();
          navigate('/admin/login');
        },
        onPasswordChangeRequired: () => navigate('/admin/me/change-password'),
        ...(fetchImpl ? { fetchImpl } : {}),
      },
    );
    setSubmitting(false);

    if (!r.ok) {
      setError(r.error);
      return;
    }
    onCreated(r.data.hcw_id);
    onClose();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Create HCW"
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/70 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !submitting) onClose();
      }}
    >
      <div className="w-full max-w-md border border-hairline bg-paper p-6">
        <header className="border-b border-hairline pb-3">
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">New HCW</p>
          <h3 className="mt-1 font-serif text-xl font-medium tracking-tight">Create HCW</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Lands at <code className="font-mono">status=pending</code>. Use Reissue on the row to issue the enrollment token.
          </p>
        </header>

        <form onSubmit={onSubmit} className="mt-4 flex flex-col gap-4">
          <Field label="HCW ID" hint="Unique. 1–64 chars [A-Za-z0-9_-]">
            <input
              ref={firstFieldRef}
              type="text"
              required
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              value={hcwId}
              onChange={(e) => setHcwId(e.target.value)}
              className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
            />
          </Field>

          <Field label="Facility ID" hint="From FacilityMasterList. 1–32 chars [A-Za-z0-9_-]">
            <input
              type="text"
              required
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              value={facilityId}
              onChange={(e) => setFacilityId(e.target.value)}
              className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
            />
          </Field>

          <Field label="Facility name" hint="Optional. Display only.">
            <input
              type="text"
              value={facilityName}
              onChange={(e) => setFacilityName(e.target.value)}
              className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
            />
          </Field>

          {error ? (
            <div role="alert" className="border-l-2 border-error pl-3 py-2">
              <p className="text-sm text-error">{messageFor(error)}</p>
              {error.requestId ? (
                <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
              ) : null}
            </div>
          ) : null}

          <div className="mt-2 flex flex-wrap gap-3">
            <Button type="submit" disabled={submitting} className="h-10">
              {submitting ? 'Creating…' : 'Create HCW'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={submitting}
              className="h-10 border-hairline hover:bg-secondary disabled:opacity-50"
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      {children}
      {hint ? <span className="font-mono text-[10px] text-muted-foreground">{hint}</span> : null}
    </label>
  );
}

function messageFor(error: ApiError): string {
  if (error.code === 'E_VALIDATION') return error.message ?? 'Some fields are invalid.';
  if (error.code === 'E_CONFLICT') return error.message ?? 'An HCW with that ID is already enrolled.';
  if (error.code === 'E_PERM_DENIED') return 'Your role lacks dash_users.';
  if (error.code === 'E_NETWORK') return 'Network unavailable. Retry when reconnected.';
  if (error.code === 'E_BACKEND') return 'Backend unavailable — Apps Script may not be reachable.';
  return error.message ?? 'Failed to create HCW.';
}
