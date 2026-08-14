/**
 * F2 Admin Portal — Controls panel (global kill switch + broadcast message).
 *
 * Extracted from DataSettings.tsx 2026-07-17 (Apps-tab audit P2-1): these are
 * the portal's two incident controls and were buried under a sub-tab named
 * after the (now removed) scheduled-exports feature. They get first position
 * on the Apps & Settings tab.
 *
 * Propagation semantics (audit P2-2 — the old "~30 s" copy was Worker-era):
 * the server checks f2_config on every public request, so blocking is
 * immediate; respondent devices refresh config on a ~5-minute poll, so the
 * banner/overlay lags by up to that long. Visitors who tap Start before their
 * device refreshes see the paused message from the server instead.
 */
import { useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { adminFetch, type AdminFetchOptions, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

export interface ControlsProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

export function Controls({ apiBaseUrl, fetchImpl }: ControlsProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();

  const authOpts = useCallback((): AdminFetchOptions => ({
    ...(token ? { token } : {}),
    onUnauthorized: () => { clearAuth(); navigate('/admin/login'); },
    onPasswordChangeRequired: () => navigate('/admin/me/change-password'),
    ...(fetchImpl ? { fetchImpl } : {}),
  }), [token, clearAuth, navigate, fetchImpl]);

  return (
    <section className="flex flex-col gap-6">
      <KillSwitchSection apiBaseUrl={apiBaseUrl} authOpts={authOpts} />
      <BroadcastSection apiBaseUrl={apiBaseUrl} authOpts={authOpts} />
    </section>
  );
}

function friendlyError(err: ApiError, fallback: string): string {
  if (err.code === 'E_PERM_DENIED') return 'Your role lacks dash_apps. Contact an Administrator.';
  if (err.code === 'E_NETWORK') return 'Network unavailable. Try again.';
  if (err.code === 'E_BACKEND') return 'Backend unavailable — the API may be restarting. Try again shortly.';
  return err.message || fallback;
}

// ----- Kill-switch section ---------------------------------------------------

type KillSwitchState =
  | { kind: 'loading' }
  | { kind: 'on' }
  | { kind: 'off' }
  | { kind: 'error'; message: string };

function KillSwitchSection({
  apiBaseUrl,
  authOpts,
}: {
  apiBaseUrl: string;
  authOpts: () => AdminFetchOptions;
}): JSX.Element {
  const [ks, setKs] = useState<KillSwitchState>({ kind: 'loading' });
  const [toggling, setToggling] = useState(false);
  const [confirmPending, setConfirmPending] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const r = await adminFetch<{ kill_switch: boolean }>(
        `${apiBaseUrl}/admin/api/dashboards/apps/kill-switch`,
        {},
        authOpts(),
      );
      if (cancelled) return;
      if (r.ok) setKs({ kind: r.data.kill_switch ? 'on' : 'off' });
      else setKs({ kind: 'error', message: friendlyError(r.error, 'Failed to load kill-switch state.') });
    })();
    return () => { cancelled = true; };
  }, [apiBaseUrl, authOpts]);

  async function doToggle(newValue: boolean): Promise<void> {
    setConfirmPending(null);
    setToggling(true);
    try {
      const r = await adminFetch<{ kill_switch: boolean }>(
        `${apiBaseUrl}/admin/api/dashboards/apps/kill-switch`,
        { method: 'PATCH', body: JSON.stringify({ kill_switch: newValue }) },
        authOpts(),
      );
      if (r.ok) setKs({ kind: r.data.kill_switch ? 'on' : 'off' });
      else setKs({ kind: 'error', message: friendlyError(r.error, 'Toggle failed.') });
    } finally {
      setToggling(false);
    }
  }

  const isOn = ks.kind === 'on';

  return (
    <div className="flex flex-col gap-3 border-b border-hairline pb-5">
      <div className="flex items-baseline justify-between">
        <h3 className="font-serif text-lg font-medium tracking-tight">Survey Controls</h3>
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-4">
          <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground w-24">
            Kill switch
          </span>
          {ks.kind === 'loading' ? (
            <span className="text-sm text-muted-foreground">Loading...</span>
          ) : ks.kind === 'error' ? (
            <span className="text-sm text-error">{ks.message}</span>
          ) : (
            <>
              <span
                className={`font-mono text-xs font-medium ${isOn ? 'text-error' : 'text-muted-foreground'}`}
              >
                {isOn ? 'ON — submissions blocked' : 'OFF — submissions open'}
              </span>
              <Button
                type="button"
                variant="tableAction"
                size="tableAction"
                disabled={toggling}
                onClick={() => setConfirmPending(!isOn)}
                className={
                  isOn
                    ? 'text-muted-foreground no-underline hover:text-foreground hover:no-underline'
                    : 'text-error no-underline hover:text-error/80 hover:no-underline'
                }
              >
                {toggling ? 'Saving...' : isOn ? 'Turn OFF' : 'Turn ON'}
              </Button>
            </>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          When ON, the server immediately rejects every new submission and Start attempt (checked on
          each request). Respondent devices show a &quot;submissions temporarily paused&quot; banner within
          ~5 minutes, on their next config refresh; anyone who taps Start before that sees the paused
          message from the server. Use during maintenance windows or incidents.
        </p>
      </div>

      {confirmPending !== null ? (
        <KillSwitchConfirmModal
          turningOn={confirmPending}
          onConfirm={() => void doToggle(confirmPending)}
          onCancel={() => setConfirmPending(null)}
        />
      ) : null}
    </div>
  );
}

// ----- Broadcast message editor (M12d) ---------------------------------------
// Sets the app-config `broadcast_message` (shown to every respondent via
// BroadcastBanner). Mirrors the kill-switch's GET/PATCH pattern. Self-hides
// (renders null) when the route 404s — an older API build — but surfaces any
// other load failure instead of vanishing, so a transient backend error stays
// visible.

type BroadcastLoad =
  | { kind: 'loading' }
  | { kind: 'absent' } // route 404s → render null
  | { kind: 'ready'; current: string }
  | { kind: 'loadError'; message: string };

export function BroadcastSection({
  apiBaseUrl,
  authOpts,
}: {
  apiBaseUrl: string;
  authOpts: () => AdminFetchOptions;
}): JSX.Element | null {
  const [load, setLoad] = useState<BroadcastLoad>({ kind: 'loading' });
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const r = await adminFetch<{ broadcast_message?: string }>(
        `${apiBaseUrl}/admin/api/dashboards/apps/broadcast`,
        {},
        authOpts(),
      );
      if (cancelled) return;
      if (r.ok) {
        // Coerce a missing/non-string field to '' — the response is untrusted.
        const msg = r.data.broadcast_message ?? '';
        setLoad({ kind: 'ready', current: msg });
        setDraft(msg);
      } else if (r.error.code === 'E_NOT_FOUND') {
        setLoad({ kind: 'absent' });
      } else {
        // Route exists but the GET failed (perms, network, backend). Show it
        // rather than silently disappearing, the way the kill-switch does.
        setLoad({
          kind: 'loadError',
          message: friendlyError(r.error, 'Failed to load the broadcast message.'),
        });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, authOpts]);

  if (load.kind === 'loading' || load.kind === 'absent') return null;

  if (load.kind === 'loadError') {
    return (
      <div className="flex flex-col gap-2 border-b border-hairline pb-5">
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          Broadcast message
        </span>
        <p role="alert" className="text-sm text-error">
          {load.message}
        </p>
      </div>
    );
  }

  const current = load.current;
  const dirty = draft.trim() !== current.trim();

  async function save(): Promise<void> {
    setSaving(true);
    setSaved(false);
    setSaveError(null);
    try {
      const r = await adminFetch<{ broadcast_message?: string }>(
        `${apiBaseUrl}/admin/api/dashboards/apps/broadcast`,
        { method: 'PATCH', body: JSON.stringify({ broadcast_message: draft.trim() }) },
        authOpts(),
      );
      if (r.ok) {
        const msg = r.data.broadcast_message ?? '';
        setLoad({ kind: 'ready', current: msg });
        setDraft(msg);
        setSaved(true);
      } else {
        setSaveError(friendlyError(r.error, 'Save failed.'));
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-2 border-b border-hairline pb-5">
      <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        Broadcast message
      </span>
      <p className="text-xs text-muted-foreground">
        Shown as a banner to every respondent in the HCW PWA. Leave empty to hide the banner.
        Appears on devices within ~5 minutes, on their next config refresh.
      </p>
      <textarea
        value={draft}
        maxLength={280}
        rows={2}
        disabled={saving}
        onChange={(e) => {
          setDraft(e.target.value);
          setSaved(false);
        }}
        className="border border-hairline bg-transparent px-2 py-1 text-sm"
        aria-label="Broadcast message"
        placeholder="e.g. Survey closes Friday 5 PM — sync before then."
      />
      <div className="flex items-center gap-3">
        <Button
          type="button"
          variant="outline"
          disabled={saving || !dirty}
          onClick={() => void save()}
          className="border-foreground px-3 py-1 font-mono text-xs uppercase tracking-wider hover:bg-foreground hover:text-background disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save'}
        </Button>
        {saved && !dirty ? (
          <span className="font-mono text-[10px] uppercase tracking-wider text-primary">Saved</span>
        ) : null}
        <span className="ml-auto font-mono text-[10px] text-muted-foreground">{draft.length}/280</span>
      </div>
      {saveError ? (
        <p role="alert" className="text-sm text-error">
          {saveError}
        </p>
      ) : null}
    </div>
  );
}

function KillSwitchConfirmModal({
  turningOn,
  onConfirm,
  onCancel,
}: {
  turningOn: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}): JSX.Element {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="ks-confirm-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6"
    >
      <div className="max-w-sm w-full border border-border bg-background p-5 flex flex-col gap-4">
        <h4 id="ks-confirm-title" className="font-serif text-base font-medium tracking-tight">
          {turningOn ? 'Turn kill switch ON?' : 'Turn kill switch OFF?'}
        </h4>
        <p className="text-sm text-muted-foreground">
          {turningOn
            ? 'This will immediately block all HCW survey submissions and show a maintenance banner in the PWA. Confirm only during a planned maintenance window or incident.'
            : 'This will re-open HCW survey submissions immediately. Respondent devices pick up the change on their next config refresh (within ~5 minutes).'}
        </p>
        <div className="flex gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={onConfirm}
            className={`border-foreground px-3 py-1 font-mono text-xs uppercase tracking-wider hover:bg-foreground hover:text-background ${turningOn ? 'hover:bg-error hover:text-white border-error text-error' : ''}`}
          >
            {turningOn ? 'Yes, block submissions' : 'Yes, re-open submissions'}
          </Button>
          <Button
            type="button"
            variant="tableAction"
            size="tableAction"
            onClick={onCancel}
            className="text-muted-foreground no-underline hover:text-foreground hover:no-underline"
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
}
