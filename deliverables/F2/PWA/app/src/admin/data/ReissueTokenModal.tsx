/**
 * F2 Admin Portal — Token Reissue modal.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 4.4)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.5)
 *
 * Two-stage modal: confirmation prompt → POST to worker → renders the
 * new token + enrollment URL with copy buttons + a scannable QR. The HCW
 * scans the QR on their device, or pastes the URL/token manually.
 *
 * FX-008 (2026-05-03): wired QRCodeSVG so admins don't have to bounce
 * the URL through a third-party QR generator (operational risk: token
 * exposure to external service).
 */
import { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Button } from '@/components/ui/button';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

interface ReissueResponse {
  hcw_id: string;
  facility_id: string;
  old_jti: string;
  new_token: string;
  new_jti: string;
  expires_at: number;
  enroll_url: string;
}

export interface ReissueTokenModalProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
  hcwId: string;
  facilityName?: string;
  prevJti?: string;
  onClose: () => void;
}

export function ReissueTokenModal({
  apiBaseUrl,
  fetchImpl,
  hcwId,
  facilityName,
  prevJti,
  onClose,
}: ReissueTokenModalProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [state, setState] = useState<
    | { kind: 'confirm' }
    | { kind: 'submitting' }
    | { kind: 'issued'; data: ReissueResponse }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'confirm' });
  const [copied, setCopied] = useState<'token' | 'url' | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && state.kind !== 'submitting') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose, state.kind]);

  const onConfirm = async () => {
    setState({ kind: 'submitting' });
    const r = await adminFetch<ReissueResponse>(
      `${apiBaseUrl}/admin/api/hcws/${encodeURIComponent(hcwId)}/reissue-token`,
      {
        method: 'POST',
        body: JSON.stringify(prevJti ? { prev_jti: prevJti } : {}),
      },
      {
        ...(token ? { token } : {}),
        onUnauthorized: () => {
          clearAuth();
          navigate('/admin/login');
        },
        ...(fetchImpl ? { fetchImpl } : {}),
      },
    );
    if (r.ok) {
      setState({ kind: 'issued', data: r.data });
    } else {
      setState({ kind: 'failed', error: r.error });
    }
  };

  const copyText = async (kind: 'token' | 'url', text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(kind);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      window.alert('Copy failed — select and copy manually.');
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Reissue token for ${hcwId}`}
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/70 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && state.kind !== 'submitting') onClose();
      }}
    >
      <div className="w-full max-w-lg border border-hairline bg-paper p-6">
        <header className="border-b border-hairline pb-3">
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Reissue token
          </p>
          <h3 className="mt-1 font-serif text-xl font-medium tracking-tight">
            <span className="font-mono">{hcwId}</span>
            {facilityName ? (
              <span className="ml-2 text-muted-foreground">· {facilityName}</span>
            ) : null}
          </h3>
        </header>

        {state.kind === 'confirm' || state.kind === 'submitting' ? (
          <Confirm
            hcwId={hcwId}
            submitting={state.kind === 'submitting'}
            onConfirm={onConfirm}
            onCancel={onClose}
          />
        ) : state.kind === 'failed' ? (
          <FailureView error={state.error} onCancel={onClose} />
        ) : (
          <SuccessView
            data={state.data}
            copied={copied}
            onCopyToken={() => void copyText('token', state.data.new_token)}
            onCopyUrl={() => void copyText('url', state.data.enroll_url)}
            onClose={onClose}
          />
        )}
      </div>
    </div>
  );
}

function Confirm({
  hcwId,
  submitting,
  onConfirm,
  onCancel,
}: {
  hcwId: string;
  submitting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}): JSX.Element {
  return (
    <div className="mt-4 flex flex-col gap-4">
      <p className="text-sm">
        Issue a new enrollment token for <span className="font-mono">{hcwId}</span>?
      </p>
      <ul className="border-l-2 border-hairline pl-3 text-sm text-muted-foreground">
        <li>The previous token stops working as soon as the HCW switches devices.</li>
        <li>F2_HCWs.token_issued_at is updated; the prior jti is recorded in token_revoked_at.</li>
        <li>If two admins reissue concurrently, only the first one wins (CAS-protected).</li>
      </ul>
      <div className="mt-2 flex flex-wrap gap-3">
        <Button type="button" onClick={onConfirm} disabled={submitting} className="h-10">
          {submitting ? 'Issuing…' : 'Issue new token'}
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

function SuccessView({
  data,
  copied,
  onCopyToken,
  onCopyUrl,
  onClose,
}: {
  data: ReissueResponse;
  copied: 'token' | 'url' | null;
  onCopyToken: () => void;
  onCopyUrl: () => void;
  onClose: () => void;
}): JSX.Element {
  return (
    <div className="mt-4 flex flex-col gap-4">
      <div className="border-l-2 border-signal pl-3">
        <p className="font-mono text-xs uppercase tracking-wider text-signal">Token issued</p>
        <p className="mt-1 text-sm">
          Have the HCW scan the QR below, or hand them the URL or token. Expires{' '}
          <span className="font-mono">{formatExpiry(data.expires_at)}</span>.
        </p>
      </div>

      <div className="flex justify-center border border-hairline bg-paper p-4">
        <QRCodeSVG
          value={data.enroll_url}
          size={192}
          level="M"
          marginSize={2}
          aria-label={`Enrollment QR code for ${data.hcw_id}`}
        />
      </div>

      <Field label="Enrollment URL">
        <div className="flex items-start gap-2">
          <code className="flex-1 break-all rounded border border-hairline bg-secondary/20 p-2 font-mono text-xs">
            {data.enroll_url}
          </code>
          <Button
            type="button"
            variant="outline"
            onClick={onCopyUrl}
            className="h-9 shrink-0 border-hairline px-3 text-xs hover:bg-secondary"
          >
            {copied === 'url' ? 'Copied' : 'Copy URL'}
          </Button>
        </div>
      </Field>

      <Field label="Token (for manual paste)">
        <div className="flex items-start gap-2">
          <code className="flex-1 break-all rounded border border-hairline bg-secondary/20 p-2 font-mono text-[10px] leading-tight">
            {data.new_token}
          </code>
          <Button
            type="button"
            variant="outline"
            onClick={onCopyToken}
            className="h-9 shrink-0 border-hairline px-3 text-xs hover:bg-secondary"
          >
            {copied === 'token' ? 'Copied' : 'Copy'}
          </Button>
        </div>
      </Field>

      <div className="mt-2">
        <Button
          type="button"
          variant="outline"
          onClick={onClose}
          className="h-10 border-hairline hover:bg-secondary"
        >
          Done
        </Button>
      </div>
    </div>
  );
}

function FailureView({ error, onCancel }: { error: ApiError; onCancel: () => void }): JSX.Element {
  return (
    <div className="mt-4 flex flex-col gap-4">
      <div role="alert" className="border-l-2 border-error pl-3 py-2">
        <p className="text-sm text-error">{messageFor(error)}</p>
        {error.requestId ? (
          <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
        ) : null}
      </div>
      <div>
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          className="h-10 border-hairline hover:bg-secondary"
        >
          Close
        </Button>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      {children}
    </label>
  );
}

function messageFor(error: ApiError): string {
  if (error.code === 'E_CONFLICT' || (error as { code?: string }).code === 'E_CAS_FAILED') {
    return 'Another admin reissued this token first. Refresh and retry if you still need to.';
  }
  if (error.code === 'E_NOT_FOUND') return 'HCW not found in F2_HCWs. Did backfillHcws run?';
  if (error.code === 'E_PERM_DENIED') return 'Your role lacks dash_users.';
  if (error.code === 'E_NETWORK') return 'Network unavailable. Retry when reconnected.';
  if (error.code === 'E_BACKEND') return 'Backend unavailable — Apps Script may not be reachable.';
  return error.message ?? 'Reissue failed.';
}

function formatExpiry(unix: number): string {
  const d = new Date(unix * 1000);
  if (isNaN(d.getTime())) return '—';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
