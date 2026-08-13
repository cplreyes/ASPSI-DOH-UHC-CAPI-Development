/**
 * F2 Admin Portal — Facility Links modal (Model C numbered links).
 *
 * Design: deliverables/F2/F2-Model-C-Numbered-Links-Design-2026-07-16.md
 *
 * Generates one short, human-readable self-register link per HCW slot at a
 * facility — `<origin>/e/<CODE>-HCW-NN?k=<secret>`. The HCW opens their link and
 * is dropped straight into the survey, already numbered (no token paste, no
 * HCW-ID typing). Two stages: a small form (facility + short-code) → the
 * generated list with per-row copy + Copy-all + Print. Secrets are shown ONCE
 * (only their HMAC is stored server-side).
 *
 * Generating is NON-DESTRUCTIVE: slots that already have a link are left alone
 * (shown as "already issued"), so previously printed cards keep working. Minting
 * fresh secrets — which invalidates every printed card — is opt-in via the guarded
 * "Rotate all" toggle (sends rotate:true).
 */
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

interface FacilityLink {
  hcw_id: string;
  qn: string;
  slug: string;
  /** Null for an already-issued slot (its secret is never re-shown). */
  secret: string | null;
  /** Null for an already-issued slot. */
  enroll_url: string | null;
  already_issued: boolean;
}

interface FacilityLinksResponse {
  facility_id: string;
  short_code: string;
  count: number;
  /** Slots that got a fresh secret this run. */
  issued: number;
  /** Slots skipped because they already had a live link (non-rotate runs). */
  skipped: number;
  /** Whether this run rotated (invalidated) existing secrets. */
  rotated: boolean;
  links: FacilityLink[];
}

export interface FacilityLinksModalProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
  /** Prefill from the HCWs-tab facility filter, if set. */
  defaultFacilityId?: string;
  onClose: () => void;
}

const FACILITY_RE = /^\d{9}$/;
const SHORT_CODE_RE = /^[A-Za-z0-9]{2,12}$/;

export function FacilityLinksModal({
  apiBaseUrl,
  fetchImpl,
  defaultFacilityId,
  onClose,
}: FacilityLinksModalProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [facilityId, setFacilityId] = useState(defaultFacilityId ?? '');
  const [shortCode, setShortCode] = useState('');
  const [rotate, setRotate] = useState(false);
  const [state, setState] = useState<
    | { kind: 'form' }
    | { kind: 'submitting' }
    | { kind: 'generated'; data: FacilityLinksResponse }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'form' });
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && state.kind !== 'submitting') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose, state.kind]);

  const canGenerate =
    FACILITY_RE.test(facilityId.trim()) && SHORT_CODE_RE.test(shortCode.trim()) && state.kind !== 'submitting';

  const onGenerate = async () => {
    setState({ kind: 'submitting' });
    const r = await adminFetch<FacilityLinksResponse>(
      `${apiBaseUrl}/admin/api/facility-links`,
      {
        method: 'POST',
        body: JSON.stringify({
          facility_id: facilityId.trim(),
          short_code: shortCode.trim(),
          ...(rotate ? { rotate: true } : {}),
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
    if (r.ok) setState({ kind: 'generated', data: r.data });
    else setState({ kind: 'failed', error: r.error });
  };

  const copy = async (key: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(key);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      window.alert('Copy failed — select and copy manually.');
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Generate facility links"
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/70 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && state.kind !== 'submitting') onClose();
      }}
    >
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto border border-hairline bg-paper p-6">
        <header className="border-b border-hairline pb-3">
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Model C · self-register links
          </p>
          <h3 className="mt-1 font-serif text-xl font-medium tracking-tight">
            Generate numbered HCW links
          </h3>
        </header>

        {state.kind === 'form' || state.kind === 'submitting' ? (
          <FormView
            facilityId={facilityId}
            shortCode={shortCode}
            rotate={rotate}
            submitting={state.kind === 'submitting'}
            canGenerate={canGenerate}
            onFacilityId={setFacilityId}
            onShortCode={setShortCode}
            onRotate={setRotate}
            onGenerate={onGenerate}
            onCancel={onClose}
          />
        ) : state.kind === 'failed' ? (
          <FailureView error={state.error} onBack={() => setState({ kind: 'form' })} onClose={onClose} />
        ) : (
          <GeneratedView
            data={state.data}
            copied={copied}
            onCopyRow={(l) => {
              if (l.enroll_url) void copy(l.slug, l.enroll_url);
            }}
            onCopyAll={() =>
              void copy(
                '__all__',
                state.data.links
                  .filter((l) => l.enroll_url)
                  .map((l) => `${l.slug}\t${l.qn}\t${l.enroll_url}`)
                  .join('\n'),
              )
            }
            onPrint={() => window.print()}
            onClose={onClose}
          />
        )}
      </div>
    </div>
  );
}

function FormView({
  facilityId,
  shortCode,
  rotate,
  submitting,
  canGenerate,
  onFacilityId,
  onShortCode,
  onRotate,
  onGenerate,
  onCancel,
}: {
  facilityId: string;
  shortCode: string;
  rotate: boolean;
  submitting: boolean;
  canGenerate: boolean;
  onFacilityId: (v: string) => void;
  onShortCode: (v: string) => void;
  onRotate: (v: boolean) => void;
  onGenerate: () => void;
  onCancel: () => void;
}): JSX.Element {
  return (
    <div className="mt-4 flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        Stamps a link onto every provisioned HCW slot at this facility (create the HCWs first).
        Each HCW opens their link and lands straight in the survey, already numbered.
      </p>
      <Field label="Facility ID (9-digit)">
        <input
          type="text"
          inputMode="numeric"
          value={facilityId}
          onChange={(e) => onFacilityId(e.target.value)}
          placeholder="040340210"
          className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
        />
      </Field>
      <Field label="Short code (2–12 letters/digits — shown in the link)">
        <input
          type="text"
          value={shortCode}
          onChange={(e) => onShortCode(e.target.value)}
          placeholder="LPHBAY"
          className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm uppercase outline-none focus:border-signal"
        />
      </Field>
      <p className="text-xs text-muted-foreground">
        Generating is safe to repeat: slots that already have a link keep it (shown as “already
        issued”), so printed cards stay valid. It only issues links for slots that don’t have one yet.
      </p>
      <label
        className={`flex items-start gap-2 border-l-2 pl-3 ${
          rotate ? 'border-error' : 'border-hairline'
        }`}
      >
        <input
          type="checkbox"
          checked={rotate}
          onChange={(e) => onRotate(e.target.checked)}
          className="mt-0.5"
        />
        <span className="text-xs text-muted-foreground">
          <span className={rotate ? 'font-medium text-error' : 'font-medium'}>Rotate all secrets</span>{' '}
          — mint fresh links for <span className="font-medium">every</span> slot. This{' '}
          <span className="font-medium">invalidates every previously printed card.</span> Only for a
          full reprint + redistribute.
        </span>
      </label>
      <div className="mt-2 flex flex-wrap gap-3">
        <Button
          type="button"
          onClick={onGenerate}
          disabled={!canGenerate}
          className={`h-10 ${rotate ? 'bg-error hover:bg-error/90' : ''}`}
        >
          {submitting
            ? rotate
              ? 'Rotating…'
              : 'Generating…'
            : rotate
              ? 'Rotate + reissue all'
              : 'Generate links'}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={submitting}
          className="h-10 border-hairline hover:bg-secondary disabled:opacity-50"
        >
          Cancel
        </Button>
      </div>
    </div>
  );
}

function GeneratedView({
  data,
  copied,
  onCopyRow,
  onCopyAll,
  onPrint,
  onClose,
}: {
  data: FacilityLinksResponse;
  copied: string | null;
  onCopyRow: (l: FacilityLink) => void;
  onCopyAll: () => void;
  onPrint: () => void;
  onClose: () => void;
}): JSX.Element {
  return (
    <div className="mt-4 flex flex-col gap-4">
      <div className={`border-l-2 pl-3 ${data.rotated ? 'border-error' : 'border-signal'}`}>
        <p
          className={`font-mono text-xs uppercase tracking-wider ${
            data.rotated ? 'text-error' : 'text-signal'
          }`}
        >
          {data.rotated ? 'Rotated · ' : ''}
          {data.issued} issued
          {data.skipped > 0 ? ` · ${data.skipped} already issued` : ''} · {data.short_code}
        </p>
        <p className="mt-1 text-sm">
          {data.rotated ? (
            <>
              Every previously printed card is now <span className="font-medium">invalid</span> —
              reprint and redistribute the whole set.
            </>
          ) : data.issued === 0 ? (
            <>
              Nothing new to issue — existing cards are still valid. Reprint from your saved sheet.
            </>
          ) : (
            <>
              Hand each HCW their own link (or QR of it). New secrets are shown{' '}
              <span className="font-medium">once</span> — print or copy now.
            </>
          )}
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button type="button" variant="outline" onClick={onCopyAll} className="h-9 border-hairline px-3 text-xs hover:bg-secondary">
          {copied === '__all__' ? 'Copied all' : 'Copy all (TSV)'}
        </Button>
        <Button type="button" variant="outline" onClick={onPrint} className="h-9 border-hairline px-3 text-xs hover:bg-secondary">
          Print sheet
        </Button>
      </div>

      <div className="overflow-x-auto border border-hairline">
        <table className="w-full text-sm">
          <thead className="border-b border-hairline text-left">
            <tr>
              <Th>Slug</Th>
              <Th>QN</Th>
              <Th>Link</Th>
              <Th>
                <span className="sr-only">Copy</span>
              </Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-hairline">
            {data.links.map((l) => (
              <tr key={l.slug}>
                <td className="px-3 py-2 align-top font-mono text-xs">{l.slug}</td>
                <td className="px-3 py-2 align-top font-mono text-xs">{l.qn}</td>
                <td className="px-3 py-2 align-top">
                  {l.enroll_url ? (
                    <code className="break-all font-mono text-[10px] leading-tight text-muted-foreground">
                      {l.enroll_url}
                    </code>
                  ) : (
                    <span className="text-[10px] italic text-muted-foreground">
                      already issued — reprint from your saved sheet
                    </span>
                  )}
                </td>
                <td className="px-3 py-2 align-top">
                  {l.enroll_url ? (
                    <Button
                      type="button"
                      variant="tableAction"
                      size="tableAction"
                      onClick={() => onCopyRow(l)}
                    >
                      {copied === l.slug ? 'Copied' : 'Copy'}
                    </Button>
                  ) : (
                    <span className="text-[10px] text-muted-foreground">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-2">
        <Button type="button" variant="outline" onClick={onClose} className="h-10 border-hairline hover:bg-secondary">
          Done
        </Button>
      </div>
    </div>
  );
}

function FailureView({
  error,
  onBack,
  onClose,
}: {
  error: ApiError;
  onBack: () => void;
  onClose: () => void;
}): JSX.Element {
  return (
    <div className="mt-4 flex flex-col gap-4">
      <div role="alert" className="border-l-2 border-error pl-3 py-2">
        <p className="text-sm text-error">{messageFor(error)}</p>
        {error.requestId ? (
          <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-3">
        <Button type="button" onClick={onBack} className="h-10">
          Back
        </Button>
        <Button type="button" variant="outline" onClick={onClose} className="h-10 border-hairline hover:bg-secondary">
          Close
        </Button>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}

function Th({ children }: { children?: React.ReactNode }): JSX.Element {
  return (
    <th className="px-3 py-2 font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
      {children}
    </th>
  );
}

function messageFor(error: ApiError): string {
  if (error.code === 'E_NOT_FOUND') {
    return 'No provisioned HCW slots at this facility. Create the HCWs first, then generate links.';
  }
  if (error.code === 'E_VALIDATION') return error.message ?? 'Check the facility ID and short code.';
  if (error.code === 'E_PERM_DENIED') return 'Your role lacks dash_users.';
  if (error.code === 'E_NETWORK') return 'Network unavailable. Retry when reconnected.';
  if (error.code === 'E_BACKEND') return 'Backend unavailable. Try again shortly.';
  return error.message ?? 'Could not generate links.';
}
