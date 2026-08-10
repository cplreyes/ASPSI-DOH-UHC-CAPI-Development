/**
 * F2 Admin Portal — Facility link dialog (Facilities page).
 *
 * Spec: deliverables/F2/F2-Facilities-Page-Spec-2026-07-16.md
 *
 * Create mode (existing=null): the facility comes from the clicked row (read-only,
 * never typed); the slug is pre-filled by suggestSlug(facility_name) and editable.
 * A client-side duplicate guard blocks saving a slug that already belongs to a
 * DIFFERENT facility — the server upsert is keyed by slug, so without this a save
 * would silently repoint someone else's live link. Saving uses the EXISTING
 * POST /admin/api/facility-slugs (no new mutation endpoint).
 *
 * View mode (existing set): URL + QR + Copy/Print for an already-linked facility.
 */
import { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Button } from '@/components/ui/button';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';
import { suggestSlug } from './suggest-slug';

const SLUG_RE = /^[a-z0-9][a-z0-9-]{1,30}$/;

interface SlugUpsertResponse {
  ok: true;
  slug: string;
  facility_id: string;
  facility_name: string;
  active: boolean;
  url: string;
}

export interface FacilityLinkDialogProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
  facility: { facility_id: string; facility_name: string };
  /** Existing link → view mode; null → create mode. */
  existing: { slug: string; active: boolean; url: string } | null;
  /** slug → owning facility, for the duplicate guard (built from the page's rows). */
  takenSlugs: Map<string, { facility_id: string; facility_name: string }>;
  onSaved: () => void;
  onClose: () => void;
}

export function FacilityLinkDialog({
  apiBaseUrl,
  fetchImpl,
  facility,
  existing,
  takenSlugs,
  onSaved,
  onClose,
}: FacilityLinkDialogProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [slug, setSlug] = useState(() => (existing ? existing.slug : suggestSlug(facility.facility_name)));
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState<{ url: string } | null>(existing ? { url: existing.url } : null);
  const [error, setError] = useState<ApiError | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !saving) onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose, saving]);

  const trimmed = slug.trim();
  const owner = takenSlugs.get(trimmed);
  const duplicate = owner !== undefined && owner.facility_id !== facility.facility_id;
  const canSave = SLUG_RE.test(trimmed) && trimmed !== 'resolve' && !duplicate && !saving;

  const onSave = async () => {
    setSaving(true);
    setError(null);
    const r = await adminFetch<SlugUpsertResponse>(
      `${apiBaseUrl}/admin/api/facility-slugs`,
      {
        method: 'POST',
        body: JSON.stringify({
          slug: trimmed,
          facility_id: facility.facility_id,
          facility_name: facility.facility_name,
          active: true,
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
    setSaving(false);
    if (!r.ok) {
      setError(r.error);
      return;
    }
    setSaved({ url: r.data.url });
    onSaved();
  };

  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      window.alert('Copy failed — select and copy manually.');
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Facility link"
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/70 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !saving) onClose();
      }}
    >
      <div className="max-h-[90vh] w-full max-w-xl overflow-y-auto border border-hairline bg-paper p-6">
        <header className="border-b border-hairline pb-3">
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Facility link · /f/&lt;slug&gt;
          </p>
          <h3 className="mt-1 font-serif text-xl font-medium tracking-tight">
            {facility.facility_name}
          </h3>
          <p className="mt-1 font-mono text-xs text-muted-foreground" data-testid="dialog-facility-id">
            {facility.facility_id}
          </p>
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

          {saved ? (
            <div className="flex flex-wrap items-start gap-4">
              <div data-testid="dialog-qr" className="shrink-0 bg-white p-2">
                <QRCodeSVG value={saved.url} size={144} />
              </div>
              <div className="min-w-0 flex-1">
                <code data-testid="dialog-url" className="break-all font-mono text-sm">
                  {saved.url}
                </code>
                <p className="mt-2 text-xs text-muted-foreground">
                  Share this link (or the QR) with the facility — posters, group chat, printouts.
                  It stays valid until you deactivate it.
                </p>
                <div className="mt-3 flex flex-wrap gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => void copy(saved.url)}
                    className="h-9 border-hairline px-3 text-xs hover:bg-secondary"
                  >
                    {copied ? 'Copied' : 'Copy link'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => window.print()}
                    className="h-9 border-hairline px-3 text-xs hover:bg-secondary"
                  >
                    Print
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <>
              <label className="flex flex-col gap-1">
                <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                  Link name (slug — becomes /f/&lt;slug&gt;)
                </span>
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value.toLowerCase())}
                  placeholder="lph-bay"
                  data-testid="dialog-slug-input"
                  className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
                />
              </label>
              <p className="text-xs text-muted-foreground">
                Pre-filled from the facility name — edit before saving if you want something
                shorter or more speakable.
              </p>
              {duplicate ? (
                <p className="text-xs text-error" data-testid="dialog-dup-error">
                  This link name already belongs to {owner.facility_name}. Pick another.
                </p>
              ) : null}
            </>
          )}

          <div className="flex flex-wrap gap-3 border-t border-hairline pt-3">
            {!saved ? (
              <Button
                type="button"
                onClick={() => void onSave()}
                disabled={!canSave}
                data-testid="dialog-save"
                className="h-10"
              >
                {saving ? 'Saving…' : 'Save facility link'}
              </Button>
            ) : null}
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={saving}
              className="h-10 border-hairline hover:bg-secondary disabled:opacity-50"
            >
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function messageFor(error: ApiError): string {
  if (error.code === 'E_VALIDATION') return error.message ?? 'Check the link name.';
  if (error.code === 'E_PERM_DENIED') return 'Your role lacks dash_users.';
  if (error.code === 'E_NETWORK') return 'Network unavailable. Retry when reconnected.';
  if (error.code === 'E_BACKEND') return 'Backend unavailable. Try again shortly.';
  return error.message ?? 'Could not save the facility link.';
}
