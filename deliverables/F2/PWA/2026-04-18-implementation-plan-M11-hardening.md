# M11 — Hardening / Release Prep Implementation Plan

> **For agentic workers:** Execute inline per `feedback_inline_over_subagent.md` (plan has complete code blocks, no subagent orchestration needed). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the production-readiness gap between "works in happy path" (M10) and "pilot-eligible" by wiring the `/config` runtime controls, blocking submits on spec drift, covering the golden path with Playwright E2E, passing a11y audits, and polishing iOS.

**Architecture:** Three layers of work. (1) *Runtime integration* — the PWA already has the backend routes but only calls `/submit`, `/batch-submit`, `/audit`, `/facilities`. M11 wires `/config` on app open, honors `kill_switch`, surfaces `broadcast_message`, and blocks submits when local `spec_version` < server `current_spec_version`. (2) *Quality gates* — Playwright E2E scaffold + five golden-path scenarios, vitest-axe + fix violations, keyboard-nav audit, iOS safe-area polish. (3) *Release prep* — bundle analysis, Lighthouse run, QA checklist doc, NEXT.md rewrite for pilot decision.

**Tech Stack:** Existing (Vite + React + TS + Dexie + react-i18next + Vitest). New dev deps: `@playwright/test`, `vitest-axe`, `axe-core`. No new runtime deps.

---

## File Structure

**New:**
- `app/src/lib/config-client.ts` — fetch `/config` from backend, envelope handling
- `app/src/lib/runtime-config.ts` — React context + provider holding latest `{kill_switch, broadcast_message, current_spec_version, min_accepted_spec_version, spec_hash}` with 5-min refresh
- `app/src/components/chrome/BroadcastBanner.tsx` — renders `broadcast_message` at top of shell
- `app/src/components/chrome/KillSwitchOverlay.tsx` — blocks submit UI when `kill_switch=true`
- `app/src/components/chrome/SpecDriftOverlay.tsx` — blocks submit UI when local `spec_version` < server `min_accepted_spec_version`, asks user to reload
- `app/src/components/enrollment/ChangeEnrollmentButton.tsx` — wraps `useAuth().unenroll`
- `app/e2e/playwright.config.ts`
- `app/e2e/fixtures/mock-backend.ts` — in-process mock of backend routes; Playwright intercepts `fetch` via `route`
- `app/e2e/golden-path.spec.ts`
- `app/e2e/offline-retry.spec.ts`
- `app/e2e/kill-switch.spec.ts`
- `app/e2e/spec-drift.spec.ts`
- `app/e2e/a11y.spec.ts`
- `app/src/test/axe-helpers.ts` — vitest-axe wrapper with ignored rules list
- `deliverables/F2/PWA/2026-04-18-cross-platform-qa-checklist.md` — manual QA steps for iOS Safari, Android Chrome, Desktop Chrome/Firefox

**Modified:**
- `app/src/App.tsx` — wraps in `RuntimeConfigProvider`, auto-refreshes facilities on mount, mounts `BroadcastBanner` + overlays
- `app/src/lib/draft.ts` — `SPEC_VERSION_PLACEHOLDER` constant exported so overlay can compare, submit guard throws `SPEC_DRIFT` if server min > local
- `app/src/lib/sync-client.ts` — (no structural change, but `/config` client reuses its HMAC pattern)
- `app/src/components/sync/SyncPage.tsx` — renders `<ChangeEnrollmentButton />`
- `app/index.html` — `<meta name="viewport" content="... viewport-fit=cover">`
- `app/src/index.css` — `env(safe-area-inset-*)` padding, `100dvh` for `min-h-full` on shell
- `app/package.json` — add `e2e`, `e2e:ui`, `audit:bundle` scripts; add devDeps
- `app/vitest.config.ts` — (if not already) ensure `jsdom` for axe
- `app/NEXT.md` — rewrite to pilot-decision posture
- `backend/README.md` — note `/config` routes now actively consumed by the PWA

## Architectural Decisions

1. **Runtime config is fetched best-effort, not blocking.** On app open we try `/config` once; if it fails (offline, backend down), we fall back to last-cached values in `localStorage` and then to safe defaults (`kill_switch=false`, empty broadcast, spec drift disabled). We never block the user from opening the app just because config is unreachable — they may be offline, which is the whole point of a PWA.

2. **Kill-switch blocks *submits*, not *data entry*.** Users mid-interview keep typing; autosave still runs. Only the Submit button is gated. Rationale: spec §2.2 and §4.2 says data integrity over convenience, but losing a half-finished interview because ops toggled a flag is bad UX.

3. **Spec-version drift shows a forced-reload overlay.** Spec §12 row 3: "Force update + auto-migrate drafts; flag incompatibles for re-entry." For M11, "force update" = modal with `<button onClick={() => location.reload(true)}>Reload</button>` when `min_accepted_spec_version > local spec_version`. Auto-migrate drafts is M12 work — for now, drafts survive the reload because they're in IndexedDB, not memory.

4. **Facilities auto-refresh on app open, not per-session cached forever.** Current flow: user taps Refresh on enrollment screen. M11: app open fires `refreshFacilities()` once in the background, silently — if it fails, the existing cache is used.

5. **E2E uses Playwright with mocked backend routes via `page.route()`.** Not against the live Apps Script deploy — too slow, quota-sensitive, coupled to a deployed URL. Mock-fetch responses in `fixtures/mock-backend.ts`. This tests the orchestrator/state-machine behavior end-to-end but decouples from backend availability.

6. **vitest-axe lives alongside component tests, not in its own file tree.** One `axe()` call per page-level component test (EnrollmentScreen, MultiSectionForm section, SyncPage). Rules we defer (documented): `color-contrast` is checked in Lighthouse not jsdom (CSS vars resolve differently); `region` landmark checks for sub-component tests.

7. **iOS polish is CSS-only (no runtime detection).** Use `env(safe-area-inset-*)` and `100dvh` — these are no-ops on desktop and Android, so one stylesheet works everywhere.

8. **Change-enrollment goes on the Sync tab, not a menu.** Only HCWs who finished one session and want to hand the device to another HCW need it. Ops concern: if a user hits it mid-draft, we'd lose their work. So the button warns if a draft exists (`localStorage.getItem('f2_current_draft_id')`) and asks for confirmation.

9. **No GET /config signing reduction.** `/config` still goes through HMAC like every other route. The "best-effort" nature is about error handling, not auth relaxation.

10. **Bundle analysis is reporting, not gating.** We add `vite-bundle-visualizer` as a dev script, look at the output once, act on obvious wins (lazy-chunk the Sync page if it's pulling Dexie eagerly into the initial bundle), but don't set a CI budget — that's M12 polish.

---

## Task 1: Runtime config client

**Files:**
- Create: `app/src/lib/config-client.ts`
- Test: `app/src/lib/config-client.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { describe, expect, it } from 'vitest';
import { getConfig } from './config-client';

describe('getConfig', () => {
  const baseDeps = {
    backendUrl: 'https://example.com/exec',
    hmacSecret: 'secret',
    hmacSign: async () => 'deadbeef',
    nowMs: () => 1_700_000_000_000,
  };

  it('returns parsed config on 200 ok envelope', async () => {
    const fetchImpl = async (url: string) => {
      expect(url).toContain('action=config');
      return new Response(
        JSON.stringify({
          ok: true,
          data: {
            current_spec_version: '2026-04-17-m1',
            min_accepted_spec_version: '2026-04-17-m1',
            kill_switch: false,
            broadcast_message: '',
            spec_hash: 'abc',
          },
        }),
        { status: 200 },
      );
    };
    const r = await getConfig({ ...baseDeps, fetchImpl: fetchImpl as typeof fetch });
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.config.current_spec_version).toBe('2026-04-17-m1');
  });

  it('returns transport error on network failure', async () => {
    const fetchImpl = async () => { throw new Error('offline'); };
    const r = await getConfig({ ...baseDeps, fetchImpl: fetchImpl as typeof fetch });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.transport).toBe(true);
  });

  it('returns backend error envelope verbatim', async () => {
    const fetchImpl = async () =>
      new Response(JSON.stringify({ ok: false, error: { code: 'E_INTERNAL', message: 'boom' } }), { status: 200 });
    const r = await getConfig({ ...baseDeps, fetchImpl: fetchImpl as typeof fetch });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error.code).toBe('E_INTERNAL');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```
npm --prefix app run test -- src/lib/config-client.test.ts
```
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

```ts
// app/src/lib/config-client.ts
export interface ConfigValue {
  current_spec_version: string;
  min_accepted_spec_version: string;
  kill_switch: boolean;
  broadcast_message: string;
  spec_hash: string;
}

export interface GetConfigDeps {
  backendUrl: string;
  hmacSecret: string;
  hmacSign: (secret: string, message: string) => Promise<string>;
  nowMs: () => number;
  fetchImpl: typeof fetch;
}

export type GetConfigResponse =
  | { ok: true; config: ConfigValue }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function getConfig(deps: GetConfigDeps): Promise<GetConfigResponse> {
  const ts = deps.nowMs();
  const canonical = `GET|config|${ts}|`;
  const sig = await deps.hmacSign(deps.hmacSecret, canonical);
  const params = new URLSearchParams({ action: 'config', ts: String(ts), sig });
  const url = `${deps.backendUrl}?${params.toString()}`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, { method: 'GET' });
  } catch (err) {
    return { ok: false, transport: true, error: { code: 'E_NETWORK', message: (err as Error).message || 'Network error' } };
  }

  if (!response.ok) {
    return { ok: false, transport: true, error: { code: 'E_HTTP_' + response.status, message: `HTTP ${response.status}` } };
  }

  let parsed: unknown;
  try {
    parsed = await response.json();
  } catch {
    return { ok: false, transport: true, error: { code: 'E_PARSE', message: 'Invalid JSON from backend' } };
  }

  const env = parsed as
    | { ok: true; data: ConfigValue }
    | { ok: false; error: { code: string; message: string } };

  if (env && env.ok === true) {
    return { ok: true, config: env.data };
  }
  return {
    ok: false,
    transport: false,
    error: env && 'error' in env ? env.error : { code: 'E_UNKNOWN', message: 'Malformed backend envelope' },
  };
}
```

- [ ] **Step 4: Verify pass**

```
npm --prefix app run test -- src/lib/config-client.test.ts
```
Expected: PASS.

---

## Task 2: Runtime config context + last-known cache

**Files:**
- Create: `app/src/lib/runtime-config.tsx`
- Test: `app/src/lib/runtime-config.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { RuntimeConfigProvider, useRuntimeConfig, RUNTIME_CONFIG_CACHE_KEY } from './runtime-config';

function Probe() {
  const cfg = useRuntimeConfig();
  return <pre data-testid="cfg">{JSON.stringify(cfg)}</pre>;
}

describe('RuntimeConfigProvider', () => {
  it('uses defaults when no cache and fetcher fails', async () => {
    localStorage.removeItem(RUNTIME_CONFIG_CACHE_KEY);
    const fetcher = vi.fn().mockResolvedValue({ ok: false, transport: true, error: { code: 'E_NETWORK', message: '' } });
    render(
      <RuntimeConfigProvider fetcher={fetcher} refreshIntervalMs={60_000}>
        <Probe />
      </RuntimeConfigProvider>,
    );
    await waitFor(() => expect(fetcher).toHaveBeenCalled());
    const cfg = JSON.parse(screen.getByTestId('cfg').textContent || '{}');
    expect(cfg.kill_switch).toBe(false);
    expect(cfg.broadcast_message).toBe('');
  });

  it('hydrates from cache on mount then refreshes', async () => {
    const cached = {
      current_spec_version: '2026-04-17-m1',
      min_accepted_spec_version: '2026-04-17-m1',
      kill_switch: false,
      broadcast_message: 'hi',
      spec_hash: 'x',
    };
    localStorage.setItem(RUNTIME_CONFIG_CACHE_KEY, JSON.stringify(cached));
    const fetcher = vi.fn().mockResolvedValue({ ok: true, config: { ...cached, broadcast_message: 'fresh' } });
    render(
      <RuntimeConfigProvider fetcher={fetcher} refreshIntervalMs={60_000}>
        <Probe />
      </RuntimeConfigProvider>,
    );
    await waitFor(() => {
      const cfg = JSON.parse(screen.getByTestId('cfg').textContent || '{}');
      expect(cfg.broadcast_message).toBe('fresh');
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```
npm --prefix app run test -- src/lib/runtime-config.test.tsx
```
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

```tsx
// app/src/lib/runtime-config.tsx
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import type { ConfigValue, GetConfigResponse } from './config-client';

export const RUNTIME_CONFIG_CACHE_KEY = 'f2_runtime_config_v1';

export const DEFAULT_CONFIG: ConfigValue = {
  current_spec_version: '',
  min_accepted_spec_version: '',
  kill_switch: false,
  broadcast_message: '',
  spec_hash: '',
};

const RuntimeConfigContext = createContext<ConfigValue>(DEFAULT_CONFIG);

function readCache(): ConfigValue | null {
  try {
    const raw = localStorage.getItem(RUNTIME_CONFIG_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') return { ...DEFAULT_CONFIG, ...parsed };
    return null;
  } catch {
    return null;
  }
}

function writeCache(cfg: ConfigValue) {
  try {
    localStorage.setItem(RUNTIME_CONFIG_CACHE_KEY, JSON.stringify(cfg));
  } catch {
    /* quota exceeded — non-fatal */
  }
}

interface Props {
  fetcher: () => Promise<GetConfigResponse>;
  refreshIntervalMs: number;
  children: ReactNode;
}

export function RuntimeConfigProvider({ fetcher, refreshIntervalMs, children }: Props) {
  const [config, setConfig] = useState<ConfigValue>(() => readCache() ?? DEFAULT_CONFIG);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  useEffect(() => {
    let cancelled = false;
    const refresh = async () => {
      const r = await fetcherRef.current();
      if (cancelled) return;
      if (r.ok) {
        setConfig(r.config);
        writeCache(r.config);
      }
    };
    void refresh();
    const id = window.setInterval(refresh, refreshIntervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [refreshIntervalMs]);

  return <RuntimeConfigContext.Provider value={config}>{children}</RuntimeConfigContext.Provider>;
}

export function useRuntimeConfig(): ConfigValue {
  return useContext(RuntimeConfigContext);
}
```

- [ ] **Step 4: Verify pass**

Expected: both tests PASS.

---

## Task 3: Broadcast banner + kill-switch overlay + spec-drift overlay

**Files:**
- Create: `app/src/components/chrome/BroadcastBanner.tsx`
- Create: `app/src/components/chrome/KillSwitchOverlay.tsx`
- Create: `app/src/components/chrome/SpecDriftOverlay.tsx`
- Test: `app/src/components/chrome/chrome.test.tsx`
- Modify: `app/src/lib/draft.ts` — export `SPEC_VERSION_PLACEHOLDER` as `LOCAL_SPEC_VERSION`

- [ ] **Step 1: Export LOCAL_SPEC_VERSION**

```ts
// app/src/lib/draft.ts — change line 4:
export const LOCAL_SPEC_VERSION = '2026-04-17-m1';
```

And replace internal uses (`SPEC_VERSION_PLACEHOLDER` at line 58) with `LOCAL_SPEC_VERSION`.

- [ ] **Step 2: Write the failing test**

```tsx
// app/src/components/chrome/chrome.test.tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BroadcastBanner } from './BroadcastBanner';
import { KillSwitchOverlay } from './KillSwitchOverlay';
import { SpecDriftOverlay } from './SpecDriftOverlay';

describe('chrome', () => {
  it('BroadcastBanner renders nothing when empty', () => {
    const { container } = render(<BroadcastBanner message="" />);
    expect(container.textContent).toBe('');
  });

  it('BroadcastBanner renders message when non-empty', () => {
    render(<BroadcastBanner message="Maintenance tonight 8pm." />);
    expect(screen.getByRole('status')).toHaveTextContent('Maintenance');
  });

  it('KillSwitchOverlay renders when active', () => {
    render(<KillSwitchOverlay active={true} />);
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  });

  it('KillSwitchOverlay renders nothing when inactive', () => {
    const { container } = render(<KillSwitchOverlay active={false} />);
    expect(container.textContent).toBe('');
  });

  it('SpecDriftOverlay shows reload button when drift=true', () => {
    render(<SpecDriftOverlay drift={true} localVersion="a" serverMin="b" />);
    expect(screen.getByRole('button', { name: /reload/i })).toBeInTheDocument();
  });

  it('SpecDriftOverlay renders nothing when drift=false', () => {
    const { container } = render(<SpecDriftOverlay drift={false} localVersion="a" serverMin="a" />);
    expect(container.textContent).toBe('');
  });
});
```

- [ ] **Step 3: Implement the three components**

```tsx
// app/src/components/chrome/BroadcastBanner.tsx
interface Props { message: string; }
export function BroadcastBanner({ message }: Props) {
  if (!message) return null;
  return (
    <div role="status" className="border-b bg-amber-50 px-6 py-2 text-sm text-amber-900">
      {message}
    </div>
  );
}
```

```tsx
// app/src/components/chrome/KillSwitchOverlay.tsx
import { useTranslation } from 'react-i18next';
interface Props { active: boolean; }
export function KillSwitchOverlay({ active }: Props) {
  const { t } = useTranslation();
  if (!active) return null;
  return (
    <div role="alertdialog" aria-labelledby="kill-switch-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-6">
      <div className="max-w-md rounded bg-white p-6 shadow-lg">
        <h2 id="kill-switch-title" className="mb-2 text-lg font-semibold">{t('chrome.killSwitchTitle')}</h2>
        <p className="text-sm text-muted-foreground">{t('chrome.killSwitchBody')}</p>
      </div>
    </div>
  );
}
```

```tsx
// app/src/components/chrome/SpecDriftOverlay.tsx
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
interface Props { drift: boolean; localVersion: string; serverMin: string; }
export function SpecDriftOverlay({ drift, localVersion, serverMin }: Props) {
  const { t } = useTranslation();
  if (!drift) return null;
  return (
    <div role="alertdialog" aria-labelledby="spec-drift-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-6">
      <div className="max-w-md rounded bg-white p-6 shadow-lg">
        <h2 id="spec-drift-title" className="mb-2 text-lg font-semibold">{t('chrome.specDriftTitle')}</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          {t('chrome.specDriftBody', { localVersion, serverMin })}
        </p>
        <Button onClick={() => window.location.reload()}>{t('chrome.reload')}</Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Add i18n strings**

In `app/src/i18n/locales/en.ts` add to `chrome` namespace:
```ts
killSwitchTitle: 'Submissions temporarily paused',
killSwitchBody: 'The administrator has paused submissions. Your progress is saved locally.',
specDriftTitle: 'Update required',
specDriftBody: 'Your form version ({{localVersion}}) is older than the server requires ({{serverMin}}). Reload to get the latest.',
reload: 'Reload',
```

Mirror in `fil.ts` (placeholder values ok per M9 tech debt note).

- [ ] **Step 5: Verify all tests pass**

```
npm --prefix app run test -- src/components/chrome src/lib/draft
```
Expected: PASS.

---

## Task 4: Wire chrome + runtime config into App.tsx

**Files:**
- Modify: `app/src/App.tsx`
- Test: update `app/src/App.test.tsx` if present to wrap in mock provider

- [ ] **Step 1: Extend App.tsx**

Add imports:
```tsx
import { RuntimeConfigProvider, useRuntimeConfig } from '@/lib/runtime-config';
import { BroadcastBanner } from '@/components/chrome/BroadcastBanner';
import { KillSwitchOverlay } from '@/components/chrome/KillSwitchOverlay';
import { SpecDriftOverlay } from '@/components/chrome/SpecDriftOverlay';
import { LOCAL_SPEC_VERSION } from '@/lib/draft';
import { getConfig } from '@/lib/config-client';
```

Add a builder (near `buildRefreshFacilities`):
```tsx
function buildConfigFetcher(): () => Promise<ReturnType<typeof getConfig>> {
  const env = getSyncEnv();
  return () =>
    getConfig({
      backendUrl: env.backendUrl,
      hmacSecret: env.hmacSecret,
      hmacSign: hmacSha256Hex,
      nowMs: Date.now,
      fetchImpl: fetch.bind(globalThis),
    });
}
```

In `AppShell`, consume runtime config:
```tsx
const runtimeConfig = useRuntimeConfig();
const specDrift = runtimeConfig.min_accepted_spec_version !== '' && runtimeConfig.min_accepted_spec_version > LOCAL_SPEC_VERSION;
```

Gate `handleSubmit`:
```tsx
const handleSubmit = async (values: FormValues) => {
  if (!draftId || !enrollmentInfo) return;
  if (runtimeConfig.kill_switch) return;
  if (specDrift) return;
  await saveDraft(draftId, values, enrollmentInfo);
  await submitDraft(draftId, enrollmentInfo);
  setStatus('submitted');
  void runSyncRef.current();
};
```

Auto-refresh facilities on mount (new effect):
```tsx
useEffect(() => {
  void refresh();
}, [refresh]);
```

In the rendered tree, place chrome above `<header>` and overlays at end of `<main>`:
```tsx
return (
  <main className="flex min-h-full flex-col">
    <BroadcastBanner message={runtimeConfig.broadcast_message} />
    <header ... />
    ...existing body...
    <KillSwitchOverlay active={runtimeConfig.kill_switch} />
    <SpecDriftOverlay drift={specDrift} localVersion={LOCAL_SPEC_VERSION} serverMin={runtimeConfig.min_accepted_spec_version} />
  </main>
);
```

Wrap the default export in `RuntimeConfigProvider`:
```tsx
const noopConfigFetcher = async () => ({ ok: false, transport: true, error: { code: 'E_ENV', message: '' } } as const);

export default function App() {
  let fetcher: ReturnType<typeof buildConfigFetcher>;
  try { fetcher = buildConfigFetcher(); } catch { fetcher = noopConfigFetcher; }
  return (
    <LocaleProvider>
      <RuntimeConfigProvider fetcher={fetcher} refreshIntervalMs={5 * 60 * 1000}>
        <AuthProvider>
          <AppShell />
        </AuthProvider>
      </RuntimeConfigProvider>
    </LocaleProvider>
  );
}
```

- [ ] **Step 2: Update App.test.tsx**

Read the existing test file (`app/src/App.test.tsx`) and ensure it mocks `getConfig` via module factory or renders `<AppShell />` directly without the Provider wrapping. If the current test renders `<App />` directly, add:
```tsx
vi.mock('@/lib/config-client', () => ({
  getConfig: vi.fn().mockResolvedValue({ ok: false, transport: true, error: { code: 'E_NETWORK', message: '' } }),
}));
```

- [ ] **Step 3: Verify**

```
npm --prefix app run test -- src/App src/lib/runtime-config
```
Expected: PASS.

---

## Task 5: Change-enrollment affordance on sync page

**Files:**
- Create: `app/src/components/enrollment/ChangeEnrollmentButton.tsx`
- Test: `app/src/components/enrollment/ChangeEnrollmentButton.test.tsx`
- Modify: `app/src/components/sync/SyncPage.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '@/lib/auth-context';
import { ChangeEnrollmentButton } from './ChangeEnrollmentButton';

vi.mock('@/lib/enrollment', () => ({
  getEnrollment: vi.fn().mockResolvedValue({ id: 'singleton', hcw_id: 'x', facility_id: 'f', facility_type: 'A', enrolled_at: 0 }),
  clearEnrollment: vi.fn().mockResolvedValue(undefined),
}));

describe('ChangeEnrollmentButton', () => {
  it('calls unenroll after confirmation when no draft present', async () => {
    localStorage.removeItem('f2_current_draft_id');
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<AuthProvider><ChangeEnrollmentButton /></AuthProvider>);
    const btn = await screen.findByRole('button', { name: /change enrollment/i });
    await user.click(btn);
    expect(confirmSpy).toHaveBeenCalled();
  });

  it('warns about draft loss when draft exists', async () => {
    localStorage.setItem('f2_current_draft_id', 'abc');
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    render(<AuthProvider><ChangeEnrollmentButton /></AuthProvider>);
    const btn = await screen.findByRole('button', { name: /change enrollment/i });
    await user.click(btn);
    expect(confirmSpy.mock.calls[0][0]).toMatch(/draft/i);
  });
});
```

- [ ] **Step 2: Implement**

```tsx
// app/src/components/enrollment/ChangeEnrollmentButton.tsx
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';

export function ChangeEnrollmentButton() {
  const { t } = useTranslation();
  const { unenroll } = useAuth();

  const handleClick = async () => {
    const hasDraft = !!localStorage.getItem('f2_current_draft_id');
    const msg = hasDraft ? t('enrollment.changeConfirmWithDraft') : t('enrollment.changeConfirm');
    if (!window.confirm(msg)) return;
    await unenroll();
  };

  return (
    <Button variant="outline" size="sm" onClick={handleClick}>
      {t('enrollment.changeButton')}
    </Button>
  );
}
```

Add i18n strings (`en.ts` under `enrollment`):
```ts
changeButton: 'Change enrollment',
changeConfirm: 'Sign out of this device? You can re-enroll afterward.',
changeConfirmWithDraft: 'You have an unfinished draft. Changing enrollment will discard it. Continue?',
```

- [ ] **Step 3: Mount in SyncPage**

In `app/src/components/sync/SyncPage.tsx`, import and render below the `SyncButton`:
```tsx
import { ChangeEnrollmentButton } from '@/components/enrollment/ChangeEnrollmentButton';
// ... in JSX, after <SyncButton /> in both empty and populated branches:
<ChangeEnrollmentButton />
```

- [ ] **Step 4: Verify**

```
npm --prefix app run test -- src/components/enrollment src/components/sync
```
Expected: PASS.

---

## Task 6: a11y audit scaffold (vitest-axe)

**Files:**
- Create: `app/src/test/axe-helpers.ts`
- Create: `app/src/a11y.test.tsx`
- Modify: `app/package.json` — add `vitest-axe` and `axe-core`

- [ ] **Step 1: Install deps**

```
npm --prefix app install --save-dev vitest-axe axe-core
```

- [ ] **Step 2: Create helper**

```ts
// app/src/test/axe-helpers.ts
import { axe, toHaveNoViolations } from 'vitest-axe';
import { expect } from 'vitest';

expect.extend(toHaveNoViolations);

// color-contrast relies on computed CSS which jsdom doesn't resolve; check in Lighthouse instead.
// region only applies to full-page contexts; component-level tests don't need a landmark.
export const AXE_COMPONENT_CONFIG = {
  rules: {
    'color-contrast': { enabled: false },
    region: { enabled: false },
  },
};

export { axe };
```

- [ ] **Step 3: Write the failing test**

```tsx
// app/src/a11y.test.tsx
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { axe, AXE_COMPONENT_CONFIG } from './test/axe-helpers';
import { BroadcastBanner } from '@/components/chrome/BroadcastBanner';
import { KillSwitchOverlay } from '@/components/chrome/KillSwitchOverlay';
import { SpecDriftOverlay } from '@/components/chrome/SpecDriftOverlay';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n';

function wrap(ui: React.ReactNode) { return <I18nextProvider i18n={i18n}>{ui}</I18nextProvider>; }

describe('a11y', () => {
  it('broadcast banner has no violations', async () => {
    const { container } = render(wrap(<BroadcastBanner message="hi" />));
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('kill-switch overlay has no violations', async () => {
    const { container } = render(wrap(<KillSwitchOverlay active={true} />));
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('spec-drift overlay has no violations', async () => {
    const { container } = render(wrap(<SpecDriftOverlay drift={true} localVersion="a" serverMin="b" />));
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });
});
```

- [ ] **Step 4: Run and fix any violations that surface**

```
npm --prefix app run test -- a11y
```
Expected: PASS. If axe flags an issue, address it (common fixes: add `aria-labelledby`, ensure buttons have accessible name, add `role=status` to live regions). Each fix goes back into the component file from Task 3 or 5.

---

## Task 7: a11y audit — EnrollmentScreen + MultiSectionForm + SyncPage

**Files:**
- Modify: `app/src/a11y.test.tsx`

- [ ] **Step 1: Extend a11y test**

```tsx
import { EnrollmentScreen } from '@/components/enrollment/EnrollmentScreen';
import { SyncPage } from '@/components/sync/SyncPage';
import { AuthProvider } from '@/lib/auth-context';

describe('a11y pages', () => {
  it('enrollment screen has no violations', async () => {
    const { container } = render(wrap(<AuthProvider><EnrollmentScreen onRefresh={async () => ({ ok: true, facilities: [] })} /></AuthProvider>));
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('sync page empty state has no violations', async () => {
    const { container } = render(wrap(<AuthProvider><SyncPage runSync={async () => ({ attempted: 0, synced: 0, failed: 0, retryScheduled: 0, alreadyRunning: false })} /></AuthProvider>));
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });
});
```

- [ ] **Step 2: Run. For any violation, fix at source**

Likely findings and fixes:
- Missing `<label htmlFor=>` on facility search input → add `id` + `htmlFor`.
- Missing `<main>` landmark on a tested component → wrap in `<main>` in the shell (already done) and suppress `region` in component tests (already done in helper).
- Color contrast in Tailwind classes → skipped in jsdom; log to manual QA checklist.

After fixes, tests pass.

---

## Task 8: Keyboard navigation audit

**Files:**
- Create: `app/src/keyboard-nav.test.tsx`

- [ ] **Step 1: Write focus-order tests**

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n';
import { AuthProvider } from '@/lib/auth-context';
import { EnrollmentScreen } from '@/components/enrollment/EnrollmentScreen';

describe('keyboard nav', () => {
  it('Tab reaches HCW input, facility search, and enroll button in order', async () => {
    const user = userEvent.setup();
    render(
      <I18nextProvider i18n={i18n}>
        <AuthProvider>
          <EnrollmentScreen onRefresh={async () => ({ ok: true, facilities: [] })} />
        </AuthProvider>
      </I18nextProvider>,
    );
    await user.tab();
    expect(document.activeElement?.tagName).toBe('INPUT');
  });
});
```

- [ ] **Step 2: Run and fix tabindex issues**

If the first `<input>` reached is wrong, inspect the DOM order and remove explicit `tabindex` attributes unless necessary.

---

## Task 9: iOS polish — viewport, safe-area, dvh

**Files:**
- Modify: `app/index.html`
- Modify: `app/src/index.css`

- [ ] **Step 1: Update viewport meta**

In `app/index.html`, replace the existing viewport meta:
```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
```

- [ ] **Step 2: Add safe-area CSS**

Append to `app/src/index.css`:
```css
@supports (padding: env(safe-area-inset-top)) {
  body {
    padding-top: env(safe-area-inset-top);
    padding-bottom: env(safe-area-inset-bottom);
    padding-left: env(safe-area-inset-left);
    padding-right: env(safe-area-inset-right);
  }
}

/* dvh falls back to vh on older browsers */
.min-h-screen-dvh {
  min-height: 100vh;
  min-height: 100dvh;
}
```

- [ ] **Step 3: Apply dvh to app shell**

In `app/src/App.tsx` change `<main className="flex min-h-full flex-col">` to `<main className="flex min-h-screen-dvh flex-col">`.

- [ ] **Step 4: Manual verification**

Run `npm --prefix app run build && npm --prefix app run preview`. Open in iOS Safari (or Chrome DevTools iPhone simulation). Confirm content clears the notch and home-indicator. Log outcome in the QA checklist doc (Task 15).

---

## Task 10: Bundle analysis + lazy route chunks

**Files:**
- Modify: `app/package.json` — add `vite-bundle-visualizer` devDep and `audit:bundle` script
- Modify: `app/src/App.tsx` — lazy-load `SyncPage`

- [ ] **Step 1: Install analyzer**

```
npm --prefix app install --save-dev vite-bundle-visualizer
```

Add script to `package.json`:
```json
"audit:bundle": "vite-bundle-visualizer -o dist/bundle.html"
```

- [ ] **Step 2: Lazy-load SyncPage**

In `app/src/App.tsx`:
```tsx
import { lazy, Suspense } from 'react';
const SyncPage = lazy(() => import('@/components/sync/SyncPage').then((m) => ({ default: m.SyncPage })));
```

Wrap usage:
```tsx
{view === 'sync' ? (
  <Suspense fallback={<p className="p-6 text-sm text-muted-foreground">{t('chrome.loading')}</p>}>
    <SyncPage runSync={runSyncRef.current} />
  </Suspense>
) : ...}
```

Remove the static `import { SyncPage } from '@/components/sync/SyncPage'`.

- [ ] **Step 3: Build, run analyzer, eyeball output**

```
npm --prefix app run build
npm --prefix app run audit:bundle
```

Open `dist/bundle.html`. If `dexie` appears in the initial chunk, consider lazy-loading it too (but only if initial bundle > ~250KB gzipped — otherwise skip; YAGNI).

- [ ] **Step 4: Confirm tests still pass**

```
npm --prefix app run test
```

---

## Task 11: Playwright scaffold + mock-backend fixture

**Files:**
- Create: `app/e2e/playwright.config.ts`
- Create: `app/e2e/fixtures/mock-backend.ts`
- Modify: `app/package.json` — add `@playwright/test`, `e2e` scripts

- [ ] **Step 1: Install Playwright**

```
npm --prefix app install --save-dev @playwright/test
npx --prefix app playwright install chromium
```

Add scripts to `package.json`:
```json
"e2e": "playwright test",
"e2e:ui": "playwright test --ui"
```

- [ ] **Step 2: Config**

```ts
// app/e2e/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:4173',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run build && npm run preview -- --port 4173',
    url: 'http://localhost:4173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

- [ ] **Step 3: Mock-backend fixture**

```ts
// app/e2e/fixtures/mock-backend.ts
import type { Page, Route } from '@playwright/test';

export interface MockState {
  facilities: Array<{ facility_id: string; facility_name: string; facility_type: string; region: string; province: string; city_mun: string; barangay: string; }>;
  config: {
    current_spec_version: string;
    min_accepted_spec_version: string;
    kill_switch: boolean;
    broadcast_message: string;
    spec_hash: string;
  };
  submissions: Array<{ client_submission_id: string; submission_id: string }>;
  failSubmitOnce?: boolean;
}

export function installMockBackend(page: Page, state: MockState) {
  const handler = async (route: Route) => {
    const url = new URL(route.request().url());
    const action = url.searchParams.get('action') ?? '';
    const method = route.request().method();

    if (action === 'facilities' && method === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, data: { facilities: state.facilities } }) });
      return;
    }
    if (action === 'config' && method === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, data: state.config }) });
      return;
    }
    if ((action === 'submit' || action === 'batch-submit') && method === 'POST') {
      if (state.failSubmitOnce) {
        state.failSubmitOnce = false;
        await route.fulfill({ status: 500, body: 'transient' });
        return;
      }
      const body = JSON.parse(route.request().postData() ?? '{}');
      if (action === 'submit') {
        const id = `srv-${body.client_submission_id}`;
        state.submissions.push({ client_submission_id: body.client_submission_id, submission_id: id });
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, data: { submission_id: id, status: 'accepted', server_timestamp: new Date().toISOString() } }) });
      } else {
        const results = (body.responses ?? []).map((r: { client_submission_id: string }) => {
          const id = `srv-${r.client_submission_id}`;
          state.submissions.push({ client_submission_id: r.client_submission_id, submission_id: id });
          return { client_submission_id: r.client_submission_id, submission_id: id, status: 'accepted' };
        });
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, data: { results } }) });
      }
      return;
    }
    if (action === 'audit' && method === 'POST') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, data: { audit_id: 'a' } }) });
      return;
    }
    await route.fallback();
  };

  return page.route(/.*\/exec\?.*/, handler);
}

export function defaultState(): MockState {
  return {
    facilities: [
      { facility_id: 'F001', facility_name: 'Test Facility A', facility_type: 'Urban Health Center', region: 'NCR', province: 'Metro Manila', city_mun: 'Manila', barangay: 'B1' },
    ],
    config: {
      current_spec_version: '2026-04-17-m1',
      min_accepted_spec_version: '2026-04-17-m1',
      kill_switch: false,
      broadcast_message: '',
      spec_hash: 'h',
    },
    submissions: [],
  };
}
```

- [ ] **Step 4: Verify config loads**

Also add `.env.local` values that point `VITE_F2_BACKEND_URL` at a fake `/exec` endpoint. The mock intercepts any URL ending in `/exec?...`, so any value works — e.g., `VITE_F2_BACKEND_URL=http://fake.test/exec`, `VITE_F2_HMAC_SECRET=test`.

Create `app/.env.test` with these values, and add a `dotenv` arg to the preview command in the Playwright config if needed.

Simpler: document in the e2e README that running `npm run e2e` expects `.env.local` to contain test values. (We won't auto-create — user can copy `.env.example`.)

---

## Task 12: E2E — golden path

**Files:**
- Create: `app/e2e/golden-path.spec.ts`

- [ ] **Step 1: Write test**

```ts
import { test, expect } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';

test('enrollment → form → submit → sync', async ({ page }) => {
  const state = defaultState();
  await installMockBackend(page, state);

  await page.goto('/');
  // Enrollment
  await page.getByLabel(/hcw id/i).fill('HCW-001');
  await page.getByRole('button', { name: /refresh/i }).click();
  await page.getByRole('combobox', { name: /facility/i }).selectOption({ label: /Test Facility A/ });
  await page.getByRole('button', { name: /enroll|confirm/i }).click();

  // Form (fill a minimum set — specific selectors depend on generated form)
  await expect(page.getByRole('heading', { name: /form|questionnaire/i })).toBeVisible();
  // Submit (walk through sections using Next until Submit appears)
  while (await page.getByRole('button', { name: /next/i }).isVisible()) {
    await page.getByRole('button', { name: /next/i }).click();
  }
  await page.getByRole('button', { name: /submit/i }).click();

  // Thank-you screen
  await expect(page.getByRole('heading', { name: /thank you/i })).toBeVisible();

  // Switch to Sync view and verify row reached "synced" status
  await page.getByRole('button', { name: /sync/i }).click();
  await expect(page.getByText(/synced \(/i)).toBeVisible({ timeout: 10_000 });
  expect(state.submissions.length).toBe(1);
});
```

- [ ] **Step 2: Run**

```
npm --prefix app run e2e -- golden-path
```

If selectors mismatch (likely — test IDs will need adjustment to actual DOM), open the trace and update selectors. Add `data-testid` attributes to the form shell and submit button as needed for stability.

---

## Task 13: E2E — offline retry + kill-switch + spec-drift

**Files:**
- Create: `app/e2e/offline-retry.spec.ts`
- Create: `app/e2e/kill-switch.spec.ts`
- Create: `app/e2e/spec-drift.spec.ts`

- [ ] **Step 1: Offline retry**

```ts
// offline-retry.spec.ts
import { test, expect } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';

test('submit retries after transient failure', async ({ page }) => {
  const state = defaultState();
  state.failSubmitOnce = true;
  await installMockBackend(page, state);

  await page.goto('/');
  // ... enrollment + form fill (reuse golden-path steps — in real impl, extract to helper) ...
  // Submit — first attempt fails (500), PWA should queue and retry automatically.
  // Assert via Sync view that row appears under retry_scheduled then moves to synced.
  await page.getByRole('button', { name: /submit/i }).click();
  await page.getByRole('button', { name: /sync/i }).click();
  await expect(page.getByText(/retry|synced/i)).toBeVisible({ timeout: 15_000 });
  // Eventually reaches synced.
  await expect(page.getByText(/synced \(1\)/i)).toBeVisible({ timeout: 30_000 });
});
```

- [ ] **Step 2: Kill switch**

```ts
// kill-switch.spec.ts
import { test, expect } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';

test('kill_switch=true blocks submit UI', async ({ page }) => {
  const state = defaultState();
  state.config.kill_switch = true;
  await installMockBackend(page, state);

  await page.goto('/');
  // Enrollment first...
  // After enrollment, kill-switch overlay should appear.
  await expect(page.getByRole('alertdialog', { name: /paused/i })).toBeVisible();
});
```

- [ ] **Step 3: Spec drift**

```ts
// spec-drift.spec.ts
import { test, expect } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';

test('min_accepted_spec_version > local triggers forced-update modal', async ({ page }) => {
  const state = defaultState();
  state.config.min_accepted_spec_version = '2099-01-01-final';
  await installMockBackend(page, state);

  await page.goto('/');
  await expect(page.getByRole('alertdialog', { name: /update required/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /reload/i })).toBeVisible();
});
```

- [ ] **Step 4: Run all e2e**

```
npm --prefix app run e2e
```

Adjust selectors as needed. Common issue: the runtime config fetcher takes an interval before the overlay appears; add `await page.waitForTimeout(500)` or wait on the specific locator with timeout.

---

## Task 14: Cross-platform QA checklist

**Files:**
- Create: `deliverables/F2/PWA/2026-04-18-cross-platform-qa-checklist.md`

- [ ] **Step 1: Write the checklist**

```markdown
# F2 PWA — Cross-Platform QA Checklist (M11)

Run through this before declaring a build pilot-eligible. Manual, single-pass. Check each item on each platform.

## Platforms

- [ ] iOS Safari 16+ on iPhone (real device if possible; otherwise DevTools responsive mode with "iPhone 14")
- [ ] Android Chrome latest on Pixel-class device (or DevTools)
- [ ] Desktop Chrome latest
- [ ] Desktop Firefox latest

## Golden path

Per platform:

- [ ] App opens at root URL; registers service worker without error (check DevTools Application → Service Workers).
- [ ] No console errors on first paint.
- [ ] Enrollment screen shows, "Refresh" button pulls facilities list, dropdown populates.
- [ ] Completing enrollment navigates to the form.
- [ ] All sections render; skip logic hides irrelevant sections.
- [ ] Autosave fires (observe via DevTools → IndexedDB → f2-db → drafts, updated_at advances).
- [ ] Submit triggers thank-you screen.
- [ ] Sync view shows the row under `synced (1)` within 10s.

## Offline behavior

- [ ] Toggle DevTools offline. Submit a response. Row appears under `pending_sync`.
- [ ] Toggle online. Within 30s, row moves to `synced`.

## Runtime config

- [ ] Set `kill_switch=true` in the backend Config sheet; reopen app; overlay appears; Submit button visible but inert.
- [ ] Revert; set `broadcast_message="Test"`; reopen; banner appears.
- [ ] Bump `min_accepted_spec_version` to a future value; reload; forced-update modal appears; Reload button reloads the page.

## iOS polish

- [ ] Content does not hide under the notch or home indicator.
- [ ] "Add to Home Screen" installs the app; launching from home-screen icon shows standalone chrome (no Safari tab bar).
- [ ] Rotating landscape ↔ portrait preserves form state.

## a11y (manual)

- [ ] Tab order is sensible throughout enrollment + form + sync.
- [ ] Focus is visible on every interactive element.
- [ ] VoiceOver (iOS) / TalkBack (Android) reads form labels correctly.

## Perf

- [ ] Lighthouse PWA score ≥ 90 (run `npm run audit:pwa`).
- [ ] Lighthouse Performance ≥ 80 (manual Lighthouse run).
- [ ] Initial bundle < 300KB gzipped (from `npm run audit:bundle`).

## Release sign-off

- [ ] All items above green.
- [ ] `npm test` across `app/` and `backend/` — green.
- [ ] `npm --prefix app run e2e` — green.
- [ ] `npm --prefix app run typecheck` — green.
- [ ] Backend `dist/Code.gs` + `dist/Admin.html` + `dist/appsscript.json` redeployed to the Apps Script project.
- [ ] Admin dashboard loads and all three tabs populate.
```

- [ ] **Step 2: No automated test** — this is a manual artifact. Confirm the file saves and opens in the editor.

---

## Task 15: Rewrite NEXT.md for pilot-decision posture

**Files:**
- Modify: `app/NEXT.md`

- [ ] **Step 1: Rewrite**

```markdown
# Next step (future-Carl)

**Last milestone shipped:** M11 — Hardening / release prep. Runtime config (`/config`) is polled every 5 min and on app open; `kill_switch` blocks submit via a modal overlay; `broadcast_message` shows as a top banner; spec-version drift (server `min_accepted_spec_version` > local `LOCAL_SPEC_VERSION`) forces a reload modal. Facilities auto-refresh on app open. Sync page has a "Change enrollment" button that warns on unsaved draft. Playwright E2E covers golden-path + offline-retry + kill-switch + spec-drift scenarios. vitest-axe guards a11y at component + page level. iOS safe-area + `100dvh` polish applied. `SyncPage` lazy-loaded. Cross-platform QA checklist at `../2026-04-18-cross-platform-qa-checklist.md`.

**Next decision (not a milestone):** Pilot readiness per spec §11.2 checkpoint row M11. Three options:

1. **Run the pilot now.** 5–10 HCWs, one facility, 2-week dry-run. Ship `dist/` + deploy Apps Script + redeploy Cloudflare Pages. Collect feedback. File new milestones from observations (not speculative work).
2. **Close deferred M11 items first** (below) before pilot.
3. **Move to M12 (F3/F4 parity)** if ASPSI says PWA-Plan-B is gated behind PWA supporting more instruments.

**Deferred from M11 (slot in only if pilot feedback demands):**

- **Per-HCW enrollment tokens** (spec §13 row 4). Current: static enrollment — any HCW ID works once a facility is selected. Threat-model change if real deployments show cross-HCW data bleed.
- **Auto-migrate drafts across spec versions** (spec §12 row 3). Current: drift modal forces reload; drafts survive because they're in IndexedDB, but if schema shifts in a breaking way, the draft may fail validation on next save.
- **iOS push notifications for deadline reminders** (spec §13 row 5).
- **Admin dashboard mutations** (kill-switch toggle, broadcast_message editor, requeue-from-DLQ) — ops team can edit the Config sheet directly for now.

**M8/M9 tech debt still outstanding** (unchanged from prior NEXT.md):

- `facility_has_bucas` / `facility_has_gamot` flags; `response_source` per-respondent capture.
- Filipino instrument + chrome translations.

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build && npm run e2e`
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build`
- Redeploy `dist/Code.gs` + `dist/Admin.html` + `dist/appsscript.json` to Apps Script if backend changed.
- Copy `.env.example` → `.env.local` and fill both vars.
- `npm run dev`, walk the golden path. Open Admin URL and confirm login.
- Work through `../2026-04-18-cross-platform-qa-checklist.md` on at least iOS Safari + Desktop Chrome before declaring pilot-ready.
```

- [ ] **Step 2: Done. No test — this is a narrative doc.**

---

## Self-Review Checklist

- [ ] Every task has complete code, no placeholders.
- [ ] Every task has a test step (or explicit "manual artifact" note for docs).
- [ ] Spec §11.1 M11 requirements mapped: E2E ✓ (Tasks 11–13), cross-platform QA ✓ (Task 14), iOS polish ✓ (Task 9), a11y ✓ (Tasks 6–8), perf ✓ (Task 10). "Production-eligible" → Task 15 NEXT.md rewrite frames pilot-decision.
- [ ] NEXT.md integration gaps covered: `/config` + `kill_switch` + `broadcast_message` (Tasks 1–4), auto-refresh facilities (Task 4), change-enrollment (Task 5), spec-drift UI (Tasks 3–4).
- [ ] Spec §12 decisions honored: spec-version strictness = force update (Task 3 SpecDriftOverlay). Auto-migrate drafts flagged as deferred in NEXT.md, consistent with spec §12 language.
- [ ] Spec §13 open questions: row 3 (admin nice upgrade), row 4 (per-HCW tokens), row 5 (iOS push) explicitly deferred in Task 15.
- [ ] File paths consistent: `app/src/lib/config-client.ts`, `app/src/lib/runtime-config.tsx`, `app/src/components/chrome/*.tsx`, `app/e2e/*`, `backend/README.md` referenced correctly.
- [ ] Type names consistent: `ConfigValue`, `GetConfigResponse`, `RuntimeConfigProvider`, `useRuntimeConfig`, `LOCAL_SPEC_VERSION` appear the same way across tasks.
- [ ] No half-finished implementations. Each task ends in green tests or a concrete manual artifact.
- [ ] Scope is single-subsystem (the F2 PWA frontend + backend integration), so one plan is appropriate.
