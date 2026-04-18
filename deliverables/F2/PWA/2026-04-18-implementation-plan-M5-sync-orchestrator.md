# M5 — Sync Orchestrator End-to-End Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the loop between the PWA (M3) and the Apps Script backend (M4) so that submitted surveys drain from IndexedDB to the live Google Sheet end-to-end, with HMAC-signed requests, the full `pending_sync → syncing → synced | rejected | retry_scheduled` state machine, exponential backoff, a "Sync now" affordance, and a visible pending-count indicator. This is the first demo-able vertical slice of the F2 PWA.

**Architecture:** Three layers. (1) A pure **sync client** (`src/lib/sync-client.ts`) owns the HTTP call: build the signed URL, POST the JSON body, parse the `{ok, data|error}` envelope. (2) A pure **sync orchestrator** (`src/lib/sync-orchestrator.ts`) owns the state machine: read `pending_sync`/ready-to-retry submissions from Dexie, call the client, apply per-result transitions back to Dexie, and surface a summary. (3) A thin **triggers layer** (`src/lib/sync-triggers.ts`) decides *when* to run the orchestrator — window `online` event, 5-minute interval while the app is open, and a manual button. Web Crypto (`crypto.subtle`) does the HMAC-SHA256 signing in the browser. Backoff is a pure function (`src/lib/backoff.ts`) used by the orchestrator, not the triggers. A Dexie v2 migration adds `retry_count`, `next_retry_at`, and `last_error` to `SubmissionRow` so the state machine has a place to persist. The UI is two components — `PendingCount` header badge and `SyncButton` — plus a minimal `SyncPage` list view of all submissions.

**Tech Stack:** TypeScript 5.6 + React 18 + Vite 5 + Dexie 4 + vite-plugin-pwa 1.2 + Vitest 4 + @testing-library/react 16 + jsdom + fake-indexeddb (existing app stack). Web Crypto (built-in, available in jsdom). No new runtime deps.

---

## File Structure

**New files in `deliverables/F2/PWA/app/`:**

```
.env.example                                   # Documents VITE_F2_BACKEND_URL + VITE_F2_HMAC_SECRET
src/lib/
├── backoff.ts                                 # Pure fn: retry_count → delay_ms
├── backoff.test.ts
├── hmac.ts                                    # Web Crypto HMAC-SHA256 → hex
├── hmac.test.ts
├── sync-client.ts                             # signed POST to /batch-submit
├── sync-client.test.ts
├── sync-orchestrator.ts                       # runSync() — state machine
├── sync-orchestrator.test.ts
├── sync-triggers.ts                           # online + interval + manual wiring
└── sync-triggers.test.ts
src/components/sync/
├── PendingCount.tsx                           # header badge "3 pending"
├── PendingCount.test.tsx
├── SyncButton.tsx                             # "Sync now" button + inline status
├── SyncButton.test.tsx
├── SyncPage.tsx                               # per-submission list view
└── SyncPage.test.tsx
```

**Modified files:**

```
src/lib/db.ts                                  # Dexie v2 migration
src/lib/db.test.ts                             # v2 migration test
src/App.tsx                                    # Wire SyncButton + PendingCount, host SyncPage behind toggle
src/App.test.tsx                               # App-level assertion: pending count visible after submit
app/NEXT.md                                    # Point to M6 after M5 ships
```

**Responsibility boundaries:**

- `backoff.ts`, `hmac.ts` — pure, no React, no Dexie, no `window`. Trivial unit tests.
- `sync-client.ts` — touches `fetch`, but receives `hmacSign`, `backendUrl`, `hmacSecret` as args. No Dexie.
- `sync-orchestrator.ts` — touches Dexie (`db.submissions`) and the sync-client. No `window`, no React. Returns a `SyncRunResult` summary.
- `sync-triggers.ts` — the only file that touches `window.addEventListener('online')`, `setInterval`, and the optional `navigator.serviceWorker`/Background Sync API. Dependency-injects the orchestrator.
- `components/sync/*` — React components. Reads live counts via a small custom hook `useLiveSubmissions` defined inside `PendingCount.tsx` (small enough not to warrant a separate file).

---

## Architectural Decisions (locked in)

1. **HMAC input canonicalization** (must match M4 backend verbatim): `${METHOD}|${action}|${ts}|${body}` — uppercase method, integer-ms `ts` as string, raw body string. Signature is **lowercase hex** SHA-256.
2. **Env vars are build-time.** `VITE_F2_BACKEND_URL` and `VITE_F2_HMAC_SECRET` are read via `import.meta.env`. Missing either → orchestrator throws at first call and logs a clear error. Values live in `.env.local` (gitignored already via default Vite gitignore).
3. **Batch size = 25.** Spec allows 50, but we cap at 25 to stay well under the Apps Script 6-minute execution budget for slow shared cells. If future sheets grow, revisit.
4. **Retry backoff schedule:** `[30_000, 120_000, 600_000, 3_600_000]` ms — 30s, 2m, 10m, 1h (spec §7.3). After 4th failure, the next delay stays at 1h (no infinite escalation).
5. **retry_scheduled dequeue policy:** a row is eligible when `status === 'pending_sync'` OR (`status === 'retry_scheduled'` AND `next_retry_at <= Date.now()`).
6. **Optimistic status write:** orchestrator flips rows to `syncing` in a Dexie transaction *before* the HTTP call. If the tab crashes mid-flight, a recovery pass on next `runSync` reclaims anything stuck in `syncing` for >10 minutes back to `pending_sync`.
7. **Spec-too-old handling:** a single `E_SPEC_TOO_OLD` anywhere in a batch flips `config.key='update_available'` to `true` in Dexie. UI shows a persistent banner; SW update is driven by vite-plugin-pwa's existing prompt, not M5.
8. **Rejected rows don't auto-retry.** `E_VALIDATION`, `E_PAYLOAD_INVALID`, `E_SPEC_TOO_OLD` → terminal `status='rejected'` with `last_error` populated. Only transport failures or 5xx/network errors → `retry_scheduled`.
9. **No locking of Dexie.** Dexie's transaction scoping is adequate; the orchestrator serializes its own runs via an in-module `isRunning` boolean. Concurrent triggers coalesce to a single run.
10. **Background Sync API is a stretch.** If the env supports it (Android Chrome), we register the tag but still rely on the foreground loop for correctness. No task depends on it working.

---

## Task 1: Scaffold env config + runtime guard

**Files:**
- Create: `deliverables/F2/PWA/app/.env.example`
- Create: `deliverables/F2/PWA/app/src/lib/env.ts`
- Create: `deliverables/F2/PWA/app/src/lib/env.test.ts`

- [ ] **Step 1: Create `.env.example`**

Write `deliverables/F2/PWA/app/.env.example`:

```
# Copy to .env.local (gitignored) and fill in the real values after deploying M4.
# Both are required for sync to function.

# Apps Script Web App /exec URL. No trailing slash.
VITE_F2_BACKEND_URL=https://script.google.com/macros/s/REPLACE_ME/exec

# 64-char hex secret from backend ScriptProperties. Treated as build-time const.
VITE_F2_HMAC_SECRET=REPLACE_ME
```

- [ ] **Step 2: Write failing test for `getSyncEnv`**

Write `src/lib/env.test.ts`:

```ts
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

describe('getSyncEnv', () => {
  const originalEnv = { ...import.meta.env };

  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    Object.assign(import.meta.env, originalEnv);
  });

  it('returns the URL and secret when both env vars are set', async () => {
    import.meta.env.VITE_F2_BACKEND_URL = 'https://example.com/exec';
    import.meta.env.VITE_F2_HMAC_SECRET = 'deadbeef';
    const { getSyncEnv } = await import('./env');
    expect(getSyncEnv()).toEqual({
      backendUrl: 'https://example.com/exec',
      hmacSecret: 'deadbeef',
    });
  });

  it('throws with a clear message when VITE_F2_BACKEND_URL is missing', async () => {
    import.meta.env.VITE_F2_BACKEND_URL = '';
    import.meta.env.VITE_F2_HMAC_SECRET = 'x';
    const { getSyncEnv } = await import('./env');
    expect(() => getSyncEnv()).toThrow(/VITE_F2_BACKEND_URL/);
  });

  it('throws with a clear message when VITE_F2_HMAC_SECRET is missing', async () => {
    import.meta.env.VITE_F2_BACKEND_URL = 'https://x/exec';
    import.meta.env.VITE_F2_HMAC_SECRET = '';
    const { getSyncEnv } = await import('./env');
    expect(() => getSyncEnv()).toThrow(/VITE_F2_HMAC_SECRET/);
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd deliverables/F2/PWA/app && npm test -- src/lib/env.test.ts`
Expected: FAIL — `Cannot find module './env'`.

- [ ] **Step 4: Create `src/lib/env.ts`**

```ts
export interface SyncEnv {
  backendUrl: string;
  hmacSecret: string;
}

export function getSyncEnv(): SyncEnv {
  const backendUrl = import.meta.env.VITE_F2_BACKEND_URL;
  const hmacSecret = import.meta.env.VITE_F2_HMAC_SECRET;

  if (!backendUrl) {
    throw new Error(
      'VITE_F2_BACKEND_URL is not set. Copy .env.example to .env.local and fill in the Apps Script /exec URL.',
    );
  }
  if (!hmacSecret) {
    throw new Error(
      'VITE_F2_HMAC_SECRET is not set. Copy .env.example to .env.local and paste the HMAC secret from the backend ScriptProperties.',
    );
  }
  return { backendUrl, hmacSecret };
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npm test -- src/lib/env.test.ts`
Expected: PASS — 3 assertions.

- [ ] **Step 6: Commit**

*(Per user preference — no git command suggestions. Pause, let the human commit manually, then proceed.)*

---

## Task 2: Backoff helper

**Files:**
- Create: `deliverables/F2/PWA/app/src/lib/backoff.ts`
- Create: `deliverables/F2/PWA/app/src/lib/backoff.test.ts`

- [ ] **Step 1: Write failing tests**

Write `src/lib/backoff.test.ts`:

```ts
import { describe, it, expect } from 'vitest';
import { backoffDelayMs, nextRetryAt } from './backoff';

describe('backoffDelayMs', () => {
  it('returns 30s for retry_count=0', () => {
    expect(backoffDelayMs(0)).toBe(30_000);
  });
  it('returns 2m for retry_count=1', () => {
    expect(backoffDelayMs(1)).toBe(120_000);
  });
  it('returns 10m for retry_count=2', () => {
    expect(backoffDelayMs(2)).toBe(600_000);
  });
  it('returns 1h for retry_count=3', () => {
    expect(backoffDelayMs(3)).toBe(3_600_000);
  });
  it('caps at 1h for any retry_count >= 3', () => {
    expect(backoffDelayMs(4)).toBe(3_600_000);
    expect(backoffDelayMs(99)).toBe(3_600_000);
  });
  it('treats negative retry_count as 0', () => {
    expect(backoffDelayMs(-1)).toBe(30_000);
  });
});

describe('nextRetryAt', () => {
  it('returns now + delay for the given retry_count', () => {
    const now = 1_700_000_000_000;
    expect(nextRetryAt(0, now)).toBe(now + 30_000);
    expect(nextRetryAt(2, now)).toBe(now + 600_000);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/lib/backoff.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `src/lib/backoff.ts`**

```ts
const SCHEDULE_MS = [30_000, 120_000, 600_000, 3_600_000] as const;

export function backoffDelayMs(retryCount: number): number {
  const n = Math.max(0, retryCount);
  const idx = Math.min(n, SCHEDULE_MS.length - 1);
  return SCHEDULE_MS[idx]!;
}

export function nextRetryAt(retryCount: number, now: number): number {
  return now + backoffDelayMs(retryCount);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/lib/backoff.test.ts`
Expected: PASS — 8 assertions.

- [ ] **Step 5: Commit**

*(Pause for manual commit.)*

---

## Task 3: HMAC signing via Web Crypto

**Files:**
- Create: `deliverables/F2/PWA/app/src/lib/hmac.ts`
- Create: `deliverables/F2/PWA/app/src/lib/hmac.test.ts`

- [ ] **Step 1: Write failing tests**

Write `src/lib/hmac.test.ts`:

```ts
import { describe, it, expect } from 'vitest';
import { hmacSha256Hex, canonicalString } from './hmac';

// RFC 4231-style known-answer — verified against Node's crypto.
// secret='key', msg='The quick brown fox jumps over the lazy dog'
// expected: f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8
const KNOWN = {
  secret: 'key',
  msg: 'The quick brown fox jumps over the lazy dog',
  expected: 'f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8',
};

describe('hmacSha256Hex', () => {
  it('produces lowercase hex output for the RFC-style fixture', async () => {
    const result = await hmacSha256Hex(KNOWN.secret, KNOWN.msg);
    expect(result).toBe(KNOWN.expected);
  });

  it('returns different signatures for different messages', async () => {
    const a = await hmacSha256Hex('secret', 'a');
    const b = await hmacSha256Hex('secret', 'b');
    expect(a).not.toBe(b);
    expect(a).toMatch(/^[0-9a-f]{64}$/);
  });

  it('returns different signatures for different secrets', async () => {
    const a = await hmacSha256Hex('s1', 'msg');
    const b = await hmacSha256Hex('s2', 'msg');
    expect(a).not.toBe(b);
  });
});

describe('canonicalString', () => {
  it('joins method, action, ts, body with pipes', () => {
    expect(canonicalString('POST', 'submit', 1_700_000_000_000, '{"x":1}'))
      .toBe('POST|submit|1700000000000|{"x":1}');
  });

  it('uppercases the method', () => {
    expect(canonicalString('post', 'x', 1, '')).toBe('POST|x|1|');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/lib/hmac.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `src/lib/hmac.ts`**

```ts
export function canonicalString(
  method: string,
  action: string,
  ts: number | string,
  body: string,
): string {
  return `${method.toUpperCase()}|${action}|${ts}|${body}`;
}

export async function hmacSha256Hex(secret: string, message: string): Promise<string> {
  const enc = new TextEncoder();
  const keyBytes = enc.encode(secret);
  const msgBytes = enc.encode(message);
  const key = await crypto.subtle.importKey(
    'raw',
    keyBytes,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const sigBuffer = await crypto.subtle.sign('HMAC', key, msgBytes);
  return bytesToHex(new Uint8Array(sigBuffer));
}

function bytesToHex(bytes: Uint8Array): string {
  let out = '';
  for (let i = 0; i < bytes.length; i++) {
    const v = bytes[i]!;
    out += v < 16 ? '0' + v.toString(16) : v.toString(16);
  }
  return out;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/lib/hmac.test.ts`
Expected: PASS — 5 assertions. Note: jsdom 29 exposes `crypto.subtle` via Node's `webcrypto`; no polyfill needed.

- [ ] **Step 5: Commit**

---

## Task 4: Dexie v2 migration — retry_count, next_retry_at, last_error

**Files:**
- Modify: `deliverables/F2/PWA/app/src/lib/db.ts`
- Modify: `deliverables/F2/PWA/app/src/lib/db.test.ts`

- [ ] **Step 1: Append failing migration test**

Append to `src/lib/db.test.ts` (or create if missing — open the file first to confirm; this step assumes the file exists from M2 and ends cleanly):

```ts
import { describe, it, expect, beforeEach } from 'vitest';
import { db } from './db';
import type { SubmissionRow } from './db';

describe('db v2 — submissions retry fields', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('accepts retry_count, next_retry_at, last_error on insert', async () => {
    const row: SubmissionRow = {
      client_submission_id: 'csid-1',
      hcw_id: 'hcw-1',
      status: 'retry_scheduled',
      synced_at: null,
      submitted_at: 1_700_000_000_000,
      spec_version: '2026-04-17-m1',
      values: {},
      retry_count: 2,
      next_retry_at: 1_700_000_600_000,
      last_error: { code: 'E_NETWORK', message: 'fetch failed' },
    };
    await db.submissions.put(row);
    const read = await db.submissions.get('csid-1');
    expect(read?.retry_count).toBe(2);
    expect(read?.next_retry_at).toBe(1_700_000_600_000);
    expect(read?.last_error?.code).toBe('E_NETWORK');
  });

  it('defaults retry_count to 0 and next_retry_at/last_error to null on fresh rows', async () => {
    const row: SubmissionRow = {
      client_submission_id: 'csid-2',
      hcw_id: 'hcw-1',
      status: 'pending_sync',
      synced_at: null,
      submitted_at: 1_700_000_000_000,
      spec_version: '2026-04-17-m1',
      values: {},
      retry_count: 0,
      next_retry_at: null,
      last_error: null,
    };
    await db.submissions.put(row);
    const read = await db.submissions.get('csid-2');
    expect(read?.retry_count).toBe(0);
    expect(read?.next_retry_at).toBeNull();
    expect(read?.last_error).toBeNull();
  });

  it('supports querying by next_retry_at index', async () => {
    await db.submissions.bulkPut([
      { client_submission_id: 'a', hcw_id: 'h', status: 'retry_scheduled', synced_at: null, submitted_at: 1, spec_version: 'v', values: {}, retry_count: 1, next_retry_at: 100, last_error: null },
      { client_submission_id: 'b', hcw_id: 'h', status: 'retry_scheduled', synced_at: null, submitted_at: 1, spec_version: 'v', values: {}, retry_count: 1, next_retry_at: 500, last_error: null },
    ]);
    const due = await db.submissions.where('next_retry_at').below(300).toArray();
    expect(due).toHaveLength(1);
    expect(due[0]?.client_submission_id).toBe('a');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/lib/db.test.ts`
Expected: FAIL — `retry_count` missing from `SubmissionRow`, or `next_retry_at` not indexed.

- [ ] **Step 3: Modify `src/lib/db.ts` — add fields and v2 migration**

Replace the entire contents of `src/lib/db.ts` with:

```ts
import Dexie, { type Table } from 'dexie';

export type SubmissionStatus =
  | 'pending_sync'
  | 'syncing'
  | 'synced'
  | 'rejected'
  | 'retry_scheduled';

export interface DraftRow {
  id: string;
  hcw_id: string;
  updated_at: number;
  values: Record<string, unknown>;
}

export interface LastError {
  code: string;
  message: string;
}

export interface SubmissionRow {
  client_submission_id: string;
  hcw_id: string;
  status: SubmissionStatus;
  synced_at: number | null;
  submitted_at: number;
  spec_version: string;
  values: Record<string, unknown>;
  retry_count: number;
  next_retry_at: number | null;
  last_error: LastError | null;
}

export interface FacilityRow {
  id: string;
  region: string;
  province: string;
  name: string;
}

export interface ConfigRow {
  key: string;
  value: unknown;
}

export interface AuditRow {
  id?: number;
  event: string;
  occurred_at: number;
  payload?: Record<string, unknown>;
}

export class F2Database extends Dexie {
  drafts!: Table<DraftRow, string>;
  submissions!: Table<SubmissionRow, string>;
  facilities!: Table<FacilityRow, string>;
  config!: Table<ConfigRow, string>;
  audit!: Table<AuditRow, number>;

  constructor() {
    super('f2_pwa');
    this.version(1).stores({
      drafts: 'id, hcw_id, updated_at',
      submissions: 'client_submission_id, status, synced_at, hcw_id',
      facilities: 'id, region, province, name',
      config: 'key',
      audit: '++id, event, occurred_at',
    });
    this.version(2)
      .stores({
        // Add next_retry_at index for the retry-due query.
        submissions: 'client_submission_id, status, synced_at, hcw_id, next_retry_at',
      })
      .upgrade(async (tx) => {
        await tx.table<SubmissionRow, string>('submissions').toCollection().modify((row) => {
          if (row.retry_count == null) row.retry_count = 0;
          if (row.next_retry_at === undefined) row.next_retry_at = null;
          if (row.last_error === undefined) row.last_error = null;
        });
      });
  }
}

export const db = new F2Database();
```

- [ ] **Step 4: Update `src/lib/draft.ts` to populate new fields on submit**

Open `src/lib/draft.ts` and locate the `submitDraft` function. Replace the block that constructs the `SubmissionRow`:

**Before:**
```ts
const submission: SubmissionRow = {
  client_submission_id: crypto.randomUUID(),
  hcw_id: draft.hcw_id,
  status: 'pending_sync',
  synced_at: null,
  submitted_at: Date.now(),
  spec_version: SPEC_VERSION_PLACEHOLDER,
  values: draft.values,
};
```

**After:**
```ts
const submission: SubmissionRow = {
  client_submission_id: crypto.randomUUID(),
  hcw_id: draft.hcw_id,
  status: 'pending_sync',
  synced_at: null,
  submitted_at: Date.now(),
  spec_version: SPEC_VERSION_PLACEHOLDER,
  values: draft.values,
  retry_count: 0,
  next_retry_at: null,
  last_error: null,
};
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `npm test -- src/lib/db.test.ts src/lib/draft.test.ts`
Expected: PASS — new submission-row assertions green, no M2 regressions.

- [ ] **Step 6: Commit**

---

## Task 5: Sync client — signed POST to /batch-submit

**Files:**
- Create: `deliverables/F2/PWA/app/src/lib/sync-client.ts`
- Create: `deliverables/F2/PWA/app/src/lib/sync-client.test.ts`

- [ ] **Step 1: Write failing tests**

Write `src/lib/sync-client.test.ts`:

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { postBatchSubmit, type BatchSubmitItem } from './sync-client';

type FetchMock = ReturnType<typeof vi.fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>>;

function mockJsonResponse(body: unknown, init?: { status?: number }): Response {
  return new Response(JSON.stringify(body), {
    status: init?.status ?? 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

const fakeSign = async (secret: string, msg: string) => `sig(${secret}:${msg})`;

const baseDeps = {
  hmacSign: fakeSign,
  nowMs: () => 1_700_000_000_000,
  fetchImpl: null as unknown as FetchMock,
};

describe('postBatchSubmit', () => {
  const items: BatchSubmitItem[] = [
    {
      client_submission_id: 'csid-1',
      hcw_id: 'h1',
      facility_id: 'f1',
      spec_version: '2026-04-17-m1',
      app_version: '0.1.0',
      submitted_at_client: 1_699_999_999_000,
      device_fingerprint: 'fp',
      values: { Q2: 'Regular' },
    },
  ];

  beforeEach(() => {
    baseDeps.fetchImpl = vi.fn();
  });

  it('sends a signed POST with ts, sig, action, and body', async () => {
    baseDeps.fetchImpl.mockResolvedValue(
      mockJsonResponse({ ok: true, data: { results: [{ client_submission_id: 'csid-1', submission_id: 'srv-1', status: 'accepted' }] } }),
    );
    const result = await postBatchSubmit(items, {
      backendUrl: 'https://x/exec',
      hmacSecret: 'S',
      ...baseDeps,
    });
    expect(result.ok).toBe(true);
    expect(baseDeps.fetchImpl).toHaveBeenCalledTimes(1);
    const [url, init] = baseDeps.fetchImpl.mock.calls[0]!;
    expect(String(url)).toContain('action=batch-submit');
    expect(String(url)).toContain('ts=1700000000000');
    expect(String(url)).toContain('sig=sig(S:POST%7Cbatch-submit%7C1700000000000%7C');
    expect((init as RequestInit).method).toBe('POST');
    expect((init as RequestInit).headers).toMatchObject({ 'Content-Type': 'application/json' });
    const body = JSON.parse((init as RequestInit).body as string);
    expect(body.responses).toHaveLength(1);
    expect(body.responses[0].client_submission_id).toBe('csid-1');
  });

  it('returns the per-item results array from the backend envelope', async () => {
    baseDeps.fetchImpl.mockResolvedValue(
      mockJsonResponse({
        ok: true,
        data: { results: [{ client_submission_id: 'csid-1', submission_id: 'srv-1', status: 'accepted' }] },
      }),
    );
    const result = await postBatchSubmit(items, {
      backendUrl: 'https://x/exec',
      hmacSecret: 'S',
      ...baseDeps,
    });
    if (!result.ok) throw new Error('expected ok');
    expect(result.results[0]?.status).toBe('accepted');
  });

  it('returns {ok: false, error} when the backend envelope says ok=false', async () => {
    baseDeps.fetchImpl.mockResolvedValue(
      mockJsonResponse({ ok: false, error: { code: 'E_KILL_SWITCH', message: 'off' } }),
    );
    const result = await postBatchSubmit(items, {
      backendUrl: 'https://x/exec',
      hmacSecret: 'S',
      ...baseDeps,
    });
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error('expected failure');
    expect(result.error.code).toBe('E_KILL_SWITCH');
    expect(result.transport).toBe(false);
  });

  it('returns {ok: false, transport: true, error} when fetch throws (network down)', async () => {
    baseDeps.fetchImpl.mockRejectedValue(new TypeError('Failed to fetch'));
    const result = await postBatchSubmit(items, {
      backendUrl: 'https://x/exec',
      hmacSecret: 'S',
      ...baseDeps,
    });
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error('expected failure');
    expect(result.transport).toBe(true);
    expect(result.error.code).toBe('E_NETWORK');
  });

  it('returns {ok: false, transport: true} for HTTP 5xx', async () => {
    baseDeps.fetchImpl.mockResolvedValue(mockJsonResponse({}, { status: 503 }));
    const result = await postBatchSubmit(items, {
      backendUrl: 'https://x/exec',
      hmacSecret: 'S',
      ...baseDeps,
    });
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error('expected failure');
    expect(result.transport).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/lib/sync-client.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `src/lib/sync-client.ts`**

```ts
export interface BatchSubmitItem {
  client_submission_id: string;
  hcw_id: string;
  facility_id: string;
  spec_version: string;
  app_version: string;
  submitted_at_client: number;
  device_fingerprint: string;
  values: Record<string, unknown>;
}

export interface BatchSubmitResultItem {
  client_submission_id: string | null;
  submission_id?: string;
  status: 'accepted' | 'duplicate' | 'rejected';
  error?: { code: string; message: string };
}

export interface SyncClientDeps {
  backendUrl: string;
  hmacSecret: string;
  hmacSign: (secret: string, message: string) => Promise<string>;
  nowMs: () => number;
  fetchImpl: typeof fetch;
}

export type BatchSubmitResponse =
  | { ok: true; results: BatchSubmitResultItem[] }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function postBatchSubmit(
  items: BatchSubmitItem[],
  deps: SyncClientDeps,
): Promise<BatchSubmitResponse> {
  const body = JSON.stringify({ responses: items });
  const ts = deps.nowMs();
  const canonical = `POST|batch-submit|${ts}|${body}`;
  const sig = await deps.hmacSign(deps.hmacSecret, canonical);
  const params = new URLSearchParams({ action: 'batch-submit', ts: String(ts), sig });
  const url = `${deps.backendUrl}?${params.toString()}`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    });
  } catch (err) {
    return {
      ok: false,
      transport: true,
      error: { code: 'E_NETWORK', message: (err as Error).message || 'Network error' },
    };
  }

  if (!response.ok) {
    return {
      ok: false,
      transport: true,
      error: { code: 'E_HTTP_' + response.status, message: `HTTP ${response.status}` },
    };
  }

  let parsed: unknown;
  try {
    parsed = await response.json();
  } catch (err) {
    return {
      ok: false,
      transport: true,
      error: { code: 'E_PARSE', message: 'Invalid JSON from backend' },
    };
  }

  const env = parsed as
    | { ok: true; data: { results: BatchSubmitResultItem[] } }
    | { ok: false; error: { code: string; message: string } };

  if (env && env.ok === true) {
    return { ok: true, results: env.data.results };
  }
  return {
    ok: false,
    transport: false,
    error: env && 'error' in env ? env.error : { code: 'E_UNKNOWN', message: 'Malformed backend envelope' },
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/lib/sync-client.test.ts`
Expected: PASS — 5 assertions.

- [ ] **Step 5: Commit**

---

## Task 6: Sync orchestrator — state machine

**Files:**
- Create: `deliverables/F2/PWA/app/src/lib/sync-orchestrator.ts`
- Create: `deliverables/F2/PWA/app/src/lib/sync-orchestrator.test.ts`

- [ ] **Step 1: Write failing tests**

Write `src/lib/sync-orchestrator.test.ts`:

```ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { db, type SubmissionRow } from './db';
import { runSync, type OrchestratorDeps } from './sync-orchestrator';

function mkSubmission(overrides: Partial<SubmissionRow> = {}): SubmissionRow {
  return {
    client_submission_id: overrides.client_submission_id ?? 'csid-' + Math.random().toString(36).slice(2),
    hcw_id: 'hcw-1',
    status: 'pending_sync',
    synced_at: null,
    submitted_at: 1_700_000_000_000,
    spec_version: '2026-04-17-m1',
    values: { Q2: 'Regular' },
    retry_count: 0,
    next_retry_at: null,
    last_error: null,
    ...overrides,
  };
}

function baseDeps(overrides: Partial<OrchestratorDeps> = {}): OrchestratorDeps {
  return {
    postBatchSubmit: vi.fn().mockResolvedValue({ ok: true, results: [] }),
    nowMs: () => 1_700_000_000_000,
    batchSize: 25,
    specVersion: '2026-04-17-m1',
    appVersion: '0.1.0',
    deviceFingerprint: 'test-fp',
    stuckSyncingThresholdMs: 600_000,
    ...overrides,
  };
}

describe('runSync — happy path', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
    await db.config.clear();
  });

  it('drains pending_sync rows to synced on all-accepted response', async () => {
    await db.submissions.bulkPut([
      mkSubmission({ client_submission_id: 'a' }),
      mkSubmission({ client_submission_id: 'b' }),
    ]);
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: true,
        results: [
          { client_submission_id: 'a', submission_id: 'srv-a', status: 'accepted' },
          { client_submission_id: 'b', submission_id: 'srv-b', status: 'accepted' },
        ],
      }),
    });
    const summary = await runSync(deps);
    expect(summary.attempted).toBe(2);
    expect(summary.synced).toBe(2);
    expect(summary.failed).toBe(0);
    const rows = await db.submissions.orderBy('client_submission_id').toArray();
    expect(rows.every((r) => r.status === 'synced')).toBe(true);
    expect(rows.every((r) => r.synced_at === 1_700_000_000_000)).toBe(true);
  });

  it('treats duplicate status as synced (already on server)', async () => {
    await db.submissions.put(mkSubmission({ client_submission_id: 'a' }));
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: true,
        results: [{ client_submission_id: 'a', submission_id: 'srv-a', status: 'duplicate' }],
      }),
    });
    await runSync(deps);
    const row = await db.submissions.get('a');
    expect(row?.status).toBe('synced');
  });

  it('returns synced=0, failed=0 when nothing is pending', async () => {
    const summary = await runSync(baseDeps());
    expect(summary.attempted).toBe(0);
    expect(summary.synced).toBe(0);
  });
});

describe('runSync — rejections', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
    await db.config.clear();
  });

  it('marks per-item E_VALIDATION as rejected with last_error populated', async () => {
    await db.submissions.put(mkSubmission({ client_submission_id: 'a' }));
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: true,
        results: [{ client_submission_id: 'a', status: 'rejected', error: { code: 'E_VALIDATION', message: 'bad' } }],
      }),
    });
    await runSync(deps);
    const row = await db.submissions.get('a');
    expect(row?.status).toBe('rejected');
    expect(row?.last_error?.code).toBe('E_VALIDATION');
  });

  it('sets config.update_available=true when any item returns E_SPEC_TOO_OLD', async () => {
    await db.submissions.bulkPut([
      mkSubmission({ client_submission_id: 'a' }),
      mkSubmission({ client_submission_id: 'b' }),
    ]);
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: true,
        results: [
          { client_submission_id: 'a', status: 'rejected', error: { code: 'E_SPEC_TOO_OLD', message: 'old' } },
          { client_submission_id: 'b', submission_id: 'srv-b', status: 'accepted' },
        ],
      }),
    });
    await runSync(deps);
    const flag = await db.config.get('update_available');
    expect(flag?.value).toBe(true);
  });
});

describe('runSync — transport failures trigger retry_scheduled with backoff', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('on whole-batch transport error, flips rows to retry_scheduled with backoff', async () => {
    await db.submissions.put(mkSubmission({ client_submission_id: 'a', retry_count: 0 }));
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: false,
        transport: true,
        error: { code: 'E_NETWORK', message: 'down' },
      }),
    });
    await runSync(deps);
    const row = await db.submissions.get('a');
    expect(row?.status).toBe('retry_scheduled');
    expect(row?.retry_count).toBe(1);
    expect(row?.next_retry_at).toBe(1_700_000_000_000 + 30_000);
    expect(row?.last_error?.code).toBe('E_NETWORK');
  });

  it('backend-level non-transport failure (ok=false, transport=false) flips rows to rejected', async () => {
    await db.submissions.put(mkSubmission({ client_submission_id: 'a' }));
    const deps = baseDeps({
      postBatchSubmit: vi.fn().mockResolvedValue({
        ok: false,
        transport: false,
        error: { code: 'E_KILL_SWITCH', message: 'off' },
      }),
    });
    await runSync(deps);
    const row = await db.submissions.get('a');
    expect(row?.status).toBe('rejected');
    expect(row?.last_error?.code).toBe('E_KILL_SWITCH');
  });
});

describe('runSync — retry eligibility', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('includes retry_scheduled rows whose next_retry_at has passed', async () => {
    await db.submissions.put(mkSubmission({
      client_submission_id: 'ready',
      status: 'retry_scheduled',
      retry_count: 1,
      next_retry_at: 1_699_999_900_000, // in the past relative to nowMs=1_700_000_000_000
    }));
    const postBatchSubmit = vi.fn().mockResolvedValue({
      ok: true,
      results: [{ client_submission_id: 'ready', submission_id: 'srv', status: 'accepted' }],
    });
    await runSync(baseDeps({ postBatchSubmit }));
    expect(postBatchSubmit).toHaveBeenCalled();
    const row = await db.submissions.get('ready');
    expect(row?.status).toBe('synced');
  });

  it('excludes retry_scheduled rows whose next_retry_at is in the future', async () => {
    await db.submissions.put(mkSubmission({
      client_submission_id: 'notyet',
      status: 'retry_scheduled',
      retry_count: 1,
      next_retry_at: 1_700_000_100_000, // after nowMs
    }));
    const postBatchSubmit = vi.fn().mockResolvedValue({ ok: true, results: [] });
    await runSync(baseDeps({ postBatchSubmit }));
    expect(postBatchSubmit).not.toHaveBeenCalled();
  });

  it('reclaims rows stuck in syncing for longer than stuckSyncingThresholdMs', async () => {
    await db.submissions.put(mkSubmission({
      client_submission_id: 'stuck',
      status: 'syncing',
      submitted_at: 1_700_000_000_000 - 700_000, // 11+ min ago
    }));
    const postBatchSubmit = vi.fn().mockResolvedValue({
      ok: true,
      results: [{ client_submission_id: 'stuck', submission_id: 'srv', status: 'accepted' }],
    });
    await runSync(baseDeps({ postBatchSubmit }));
    const row = await db.submissions.get('stuck');
    expect(row?.status).toBe('synced');
  });
});

describe('runSync — reentrancy guard', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('second concurrent call returns already-running summary without calling the client twice', async () => {
    await db.submissions.put(mkSubmission({ client_submission_id: 'a' }));
    let resolveFetch: (v: unknown) => void = () => {};
    const slow = new Promise((r) => (resolveFetch = r));
    const postBatchSubmit = vi.fn().mockImplementation(async () => {
      await slow;
      return { ok: true, results: [{ client_submission_id: 'a', submission_id: 'x', status: 'accepted' }] };
    });
    const first = runSync(baseDeps({ postBatchSubmit }));
    const second = await runSync(baseDeps({ postBatchSubmit }));
    expect(second.alreadyRunning).toBe(true);
    resolveFetch({});
    await first;
    expect(postBatchSubmit).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/lib/sync-orchestrator.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `src/lib/sync-orchestrator.ts`**

```ts
import { db, type SubmissionRow } from './db';
import { nextRetryAt } from './backoff';
import type { BatchSubmitItem, BatchSubmitResponse } from './sync-client';

export interface OrchestratorDeps {
  postBatchSubmit: (items: BatchSubmitItem[]) => Promise<BatchSubmitResponse>;
  nowMs: () => number;
  batchSize: number;
  specVersion: string;
  appVersion: string;
  deviceFingerprint: string;
  stuckSyncingThresholdMs: number;
}

export interface SyncRunSummary {
  attempted: number;
  synced: number;
  failed: number;
  retryScheduled: number;
  alreadyRunning: boolean;
}

let isRunning = false;

export async function runSync(deps: OrchestratorDeps): Promise<SyncRunSummary> {
  if (isRunning) {
    return { attempted: 0, synced: 0, failed: 0, retryScheduled: 0, alreadyRunning: true };
  }
  isRunning = true;
  try {
    await reclaimStuck(deps);
    const ready = await findReady(deps);
    if (ready.length === 0) {
      return { attempted: 0, synced: 0, failed: 0, retryScheduled: 0, alreadyRunning: false };
    }
    await markSyncing(ready);
    const items = ready.map((r) => toBatchItem(r, deps));
    const response = await deps.postBatchSubmit(items);
    return await applyResponse(ready, response, deps);
  } finally {
    isRunning = false;
  }
}

async function findReady(deps: OrchestratorDeps): Promise<SubmissionRow[]> {
  const now = deps.nowMs();
  const pending = await db.submissions.where('status').equals('pending_sync').toArray();
  const retry = await db.submissions
    .where('status')
    .equals('retry_scheduled')
    .filter((r) => r.next_retry_at != null && r.next_retry_at <= now)
    .toArray();
  return [...pending, ...retry].slice(0, deps.batchSize);
}

async function reclaimStuck(deps: OrchestratorDeps): Promise<void> {
  const now = deps.nowMs();
  const cutoff = now - deps.stuckSyncingThresholdMs;
  await db.submissions
    .where('status')
    .equals('syncing')
    .filter((r) => r.submitted_at <= cutoff)
    .modify({ status: 'pending_sync' });
}

async function markSyncing(rows: SubmissionRow[]): Promise<void> {
  const ids = rows.map((r) => r.client_submission_id);
  await db.submissions.where('client_submission_id').anyOf(ids).modify({ status: 'syncing' });
}

function toBatchItem(row: SubmissionRow, deps: OrchestratorDeps): BatchSubmitItem {
  return {
    client_submission_id: row.client_submission_id,
    hcw_id: row.hcw_id,
    facility_id: (row.values['facility_id'] as string | undefined) ?? '',
    spec_version: row.spec_version || deps.specVersion,
    app_version: deps.appVersion,
    submitted_at_client: row.submitted_at,
    device_fingerprint: deps.deviceFingerprint,
    values: row.values,
  };
}

async function applyResponse(
  rows: SubmissionRow[],
  response: BatchSubmitResponse,
  deps: OrchestratorDeps,
): Promise<SyncRunSummary> {
  const now = deps.nowMs();
  let synced = 0;
  let failed = 0;
  let retryScheduled = 0;

  if (!response.ok && response.transport) {
    // Whole-batch transport failure → retry_scheduled with backoff for every row.
    for (const row of rows) {
      const nextCount = row.retry_count + 1;
      await db.submissions.update(row.client_submission_id, {
        status: 'retry_scheduled',
        retry_count: nextCount,
        next_retry_at: nextRetryAt(nextCount - 1, now),
        last_error: response.error,
      });
      retryScheduled += 1;
    }
    return { attempted: rows.length, synced, failed, retryScheduled, alreadyRunning: false };
  }

  if (!response.ok) {
    // Non-transport backend-level failure (kill switch, bad envelope) → reject every row.
    for (const row of rows) {
      await db.submissions.update(row.client_submission_id, {
        status: 'rejected',
        last_error: response.error,
      });
      failed += 1;
    }
    return { attempted: rows.length, synced, failed, retryScheduled, alreadyRunning: false };
  }

  let anySpecTooOld = false;
  const resultsByCsid = new Map<string, (typeof response.results)[number]>();
  for (const r of response.results) {
    if (r.client_submission_id) resultsByCsid.set(r.client_submission_id, r);
  }

  for (const row of rows) {
    const r = resultsByCsid.get(row.client_submission_id);
    if (!r) {
      // Unmatched response — treat as transport failure for this row (backoff).
      const nextCount = row.retry_count + 1;
      await db.submissions.update(row.client_submission_id, {
        status: 'retry_scheduled',
        retry_count: nextCount,
        next_retry_at: nextRetryAt(nextCount - 1, now),
        last_error: { code: 'E_MISSING_RESULT', message: 'No matching per-item result' },
      });
      retryScheduled += 1;
      continue;
    }
    if (r.status === 'accepted' || r.status === 'duplicate') {
      await db.submissions.update(row.client_submission_id, {
        status: 'synced',
        synced_at: now,
        last_error: null,
      });
      synced += 1;
    } else {
      // rejected
      if (r.error?.code === 'E_SPEC_TOO_OLD') anySpecTooOld = true;
      await db.submissions.update(row.client_submission_id, {
        status: 'rejected',
        last_error: r.error ?? { code: 'E_UNKNOWN', message: 'Unknown rejection' },
      });
      failed += 1;
    }
  }

  if (anySpecTooOld) {
    await db.config.put({ key: 'update_available', value: true });
  }

  return { attempted: rows.length, synced, failed, retryScheduled, alreadyRunning: false };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/lib/sync-orchestrator.test.ts`
Expected: PASS — 10 assertions across 5 describe blocks.

- [ ] **Step 5: Commit**

---

## Task 7: Sync triggers — online, interval, manual

**Files:**
- Create: `deliverables/F2/PWA/app/src/lib/sync-triggers.ts`
- Create: `deliverables/F2/PWA/app/src/lib/sync-triggers.test.ts`

- [ ] **Step 1: Write failing tests**

Write `src/lib/sync-triggers.test.ts`:

```ts
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { installSyncTriggers } from './sync-triggers';

describe('installSyncTriggers', () => {
  let runSync: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    runSync = vi.fn().mockResolvedValue({ attempted: 0, synced: 0, failed: 0, retryScheduled: 0, alreadyRunning: false });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('runs sync immediately on install when navigator.onLine is true', async () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    installSyncTriggers({ runSync, intervalMs: 60_000 });
    await vi.runOnlyPendingTimersAsync();
    expect(runSync).toHaveBeenCalledTimes(1);
  });

  it('does not run on install when offline', async () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false);
    installSyncTriggers({ runSync, intervalMs: 60_000 });
    await vi.runOnlyPendingTimersAsync();
    expect(runSync).not.toHaveBeenCalled();
  });

  it('runs sync when the window online event fires', async () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false);
    installSyncTriggers({ runSync, intervalMs: 60_000 });
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    window.dispatchEvent(new Event('online'));
    await vi.runOnlyPendingTimersAsync();
    expect(runSync).toHaveBeenCalledTimes(1);
  });

  it('runs sync on the interval while online', async () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    installSyncTriggers({ runSync, intervalMs: 60_000 });
    await vi.runOnlyPendingTimersAsync(); // initial run
    vi.advanceTimersByTime(60_000);
    await vi.runOnlyPendingTimersAsync();
    vi.advanceTimersByTime(60_000);
    await vi.runOnlyPendingTimersAsync();
    expect(runSync).toHaveBeenCalledTimes(3);
  });

  it('stop() removes the online listener and clears the interval', async () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    const { stop } = installSyncTriggers({ runSync, intervalMs: 60_000 });
    await vi.runOnlyPendingTimersAsync();
    expect(runSync).toHaveBeenCalledTimes(1);
    stop();
    vi.advanceTimersByTime(180_000);
    window.dispatchEvent(new Event('online'));
    await vi.runOnlyPendingTimersAsync();
    expect(runSync).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/lib/sync-triggers.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `src/lib/sync-triggers.ts`**

```ts
import type { SyncRunSummary } from './sync-orchestrator';

export interface TriggersDeps {
  runSync: () => Promise<SyncRunSummary>;
  intervalMs: number;
}

export interface TriggerHandle {
  stop: () => void;
}

export function installSyncTriggers(deps: TriggersDeps): TriggerHandle {
  const { runSync, intervalMs } = deps;

  const safeRun = () => {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) return;
    void runSync();
  };

  const onOnline = () => { safeRun(); };
  window.addEventListener('online', onOnline);

  const interval = setInterval(safeRun, intervalMs);

  // Initial attempt (only if online — safeRun enforces this).
  safeRun();

  return {
    stop: () => {
      window.removeEventListener('online', onOnline);
      clearInterval(interval);
    },
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/lib/sync-triggers.test.ts`
Expected: PASS — 5 assertions.

- [ ] **Step 5: Commit**

---

## Task 8: `PendingCount` header badge

**Files:**
- Create: `deliverables/F2/PWA/app/src/components/sync/PendingCount.tsx`
- Create: `deliverables/F2/PWA/app/src/components/sync/PendingCount.test.tsx`

- [ ] **Step 1: Write failing test**

Write `src/components/sync/PendingCount.test.tsx`:

```tsx
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { db, type SubmissionRow } from '@/lib/db';
import { PendingCount } from './PendingCount';

function mkSub(id: string, status: SubmissionRow['status']): SubmissionRow {
  return {
    client_submission_id: id,
    hcw_id: 'h1',
    status,
    synced_at: null,
    submitted_at: 1,
    spec_version: 'v',
    values: {},
    retry_count: 0,
    next_retry_at: null,
    last_error: null,
  };
}

describe('PendingCount', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('renders nothing when there are zero pending/retry rows', async () => {
    render(<PendingCount />);
    await waitFor(() => {
      expect(screen.queryByTestId('pending-count')).toBeNull();
    });
  });

  it('shows the count of pending_sync + retry_scheduled rows', async () => {
    await db.submissions.bulkPut([
      mkSub('a', 'pending_sync'),
      mkSub('b', 'retry_scheduled'),
      mkSub('c', 'synced'),
      mkSub('d', 'pending_sync'),
    ]);
    render(<PendingCount />);
    await waitFor(() => {
      expect(screen.getByTestId('pending-count')).toHaveTextContent('3 pending');
    });
  });

  it('updates live when a new pending row is inserted', async () => {
    render(<PendingCount />);
    await waitFor(() => expect(screen.queryByTestId('pending-count')).toBeNull());
    await db.submissions.put(mkSub('z', 'pending_sync'));
    await waitFor(() => {
      expect(screen.getByTestId('pending-count')).toHaveTextContent('1 pending');
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/components/sync/PendingCount.test.tsx`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `src/components/sync/PendingCount.tsx`**

```tsx
import { useEffect, useState } from 'react';
import { liveQuery } from 'dexie';
import { db } from '@/lib/db';

export function PendingCount() {
  const [count, setCount] = useState<number>(0);

  useEffect(() => {
    const subscription = liveQuery(async () => {
      const pending = await db.submissions.where('status').equals('pending_sync').count();
      const retry = await db.submissions.where('status').equals('retry_scheduled').count();
      return pending + retry;
    }).subscribe({
      next: (n) => setCount(n),
      error: () => setCount(0),
    });
    return () => subscription.unsubscribe();
  }, []);

  if (count === 0) return null;
  return (
    <span
      data-testid="pending-count"
      className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800"
    >
      {count} pending
    </span>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/components/sync/PendingCount.test.tsx`
Expected: PASS — 3 assertions.

- [ ] **Step 5: Commit**

---

## Task 9: `SyncButton` with inline status

**Files:**
- Create: `deliverables/F2/PWA/app/src/components/sync/SyncButton.tsx`
- Create: `deliverables/F2/PWA/app/src/components/sync/SyncButton.test.tsx`

- [ ] **Step 1: Write failing test**

Write `src/components/sync/SyncButton.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SyncButton } from './SyncButton';

describe('SyncButton', () => {
  it('calls runSync when clicked and shows "Syncing…" while in flight', async () => {
    let resolve: (v: { attempted: number; synced: number; failed: number; retryScheduled: number; alreadyRunning: boolean }) => void = () => {};
    const promise = new Promise<ReturnType<typeof resolve>>((r) => (resolve = r));
    const runSync = vi.fn(() => promise);
    render(<SyncButton runSync={runSync} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /sync now/i }));
    expect(runSync).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button')).toHaveTextContent(/syncing/i);
    resolve({ attempted: 1, synced: 1, failed: 0, retryScheduled: 0, alreadyRunning: false });
    await promise;
  });

  it('shows "Synced N" after a successful run', async () => {
    const runSync = vi.fn().mockResolvedValue({ attempted: 2, synced: 2, failed: 0, retryScheduled: 0, alreadyRunning: false });
    render(<SyncButton runSync={runSync} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button'));
    expect(await screen.findByText(/synced 2/i)).toBeInTheDocument();
  });

  it('shows "Retry in X" when some rows go to retry_scheduled', async () => {
    const runSync = vi.fn().mockResolvedValue({ attempted: 3, synced: 1, failed: 0, retryScheduled: 2, alreadyRunning: false });
    render(<SyncButton runSync={runSync} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button'));
    expect(await screen.findByText(/retrying 2/i)).toBeInTheDocument();
  });

  it('shows "N rejected" when some rows were terminally rejected', async () => {
    const runSync = vi.fn().mockResolvedValue({ attempted: 2, synced: 1, failed: 1, retryScheduled: 0, alreadyRunning: false });
    render(<SyncButton runSync={runSync} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button'));
    expect(await screen.findByText(/1 rejected/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/components/sync/SyncButton.test.tsx`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `src/components/sync/SyncButton.tsx`**

```tsx
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import type { SyncRunSummary } from '@/lib/sync-orchestrator';

interface SyncButtonProps {
  runSync: () => Promise<SyncRunSummary>;
}

type UiState =
  | { kind: 'idle' }
  | { kind: 'running' }
  | { kind: 'done'; summary: SyncRunSummary }
  | { kind: 'error'; message: string };

export function SyncButton({ runSync }: SyncButtonProps) {
  const [state, setState] = useState<UiState>({ kind: 'idle' });

  const onClick = async () => {
    setState({ kind: 'running' });
    try {
      const summary = await runSync();
      setState({ kind: 'done', summary });
    } catch (err) {
      setState({ kind: 'error', message: (err as Error).message || 'Sync failed' });
    }
  };

  return (
    <div className="flex items-center gap-3">
      <Button type="button" onClick={onClick} disabled={state.kind === 'running'}>
        {state.kind === 'running' ? 'Syncing…' : 'Sync now'}
      </Button>
      {state.kind === 'done' ? (
        <span className="text-xs text-muted-foreground">
          {state.summary.synced > 0 ? `Synced ${state.summary.synced}` : ''}
          {state.summary.retryScheduled > 0 ? ` · Retrying ${state.summary.retryScheduled}` : ''}
          {state.summary.failed > 0 ? ` · ${state.summary.failed} rejected` : ''}
          {state.summary.attempted === 0 ? 'Nothing to sync' : ''}
        </span>
      ) : null}
      {state.kind === 'error' ? (
        <span className="text-xs text-destructive">{state.message}</span>
      ) : null}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/components/sync/SyncButton.test.tsx`
Expected: PASS — 4 assertions.

- [ ] **Step 5: Commit**

---

## Task 10: `SyncPage` — per-submission list view

**Files:**
- Create: `deliverables/F2/PWA/app/src/components/sync/SyncPage.tsx`
- Create: `deliverables/F2/PWA/app/src/components/sync/SyncPage.test.tsx`

- [ ] **Step 1: Write failing test**

Write `src/components/sync/SyncPage.test.tsx`:

```tsx
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { db, type SubmissionRow } from '@/lib/db';
import { SyncPage } from './SyncPage';

function mkSub(overrides: Partial<SubmissionRow>): SubmissionRow {
  return {
    client_submission_id: 'id',
    hcw_id: 'h1',
    status: 'pending_sync',
    synced_at: null,
    submitted_at: Date.UTC(2026, 3, 18, 1, 0, 0),
    spec_version: 'v',
    values: {},
    retry_count: 0,
    next_retry_at: null,
    last_error: null,
    ...overrides,
  };
}

describe('SyncPage', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
  });

  it('renders an empty-state message when no submissions exist', async () => {
    render(<SyncPage runSync={vi.fn().mockResolvedValue({ attempted: 0, synced: 0, failed: 0, retryScheduled: 0, alreadyRunning: false })} />);
    await waitFor(() => {
      expect(screen.getByText(/no submissions yet/i)).toBeInTheDocument();
    });
  });

  it('lists submissions grouped by status and shows last_error for rejected', async () => {
    await db.submissions.bulkPut([
      mkSub({ client_submission_id: 'a', status: 'pending_sync' }),
      mkSub({ client_submission_id: 'b', status: 'synced', synced_at: Date.UTC(2026, 3, 18, 2, 0, 0) }),
      mkSub({ client_submission_id: 'c', status: 'rejected', last_error: { code: 'E_VALIDATION', message: 'bad field' } }),
      mkSub({ client_submission_id: 'd', status: 'retry_scheduled', next_retry_at: Date.UTC(2026, 3, 18, 3, 0, 0), last_error: { code: 'E_NETWORK', message: 'offline' } }),
    ]);
    render(<SyncPage runSync={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('a')).toBeInTheDocument();
      expect(screen.getByText('b')).toBeInTheDocument();
      expect(screen.getByText(/E_VALIDATION/)).toBeInTheDocument();
      expect(screen.getByText(/E_NETWORK/)).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/components/sync/SyncPage.test.tsx`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `src/components/sync/SyncPage.tsx`**

```tsx
import { useEffect, useState } from 'react';
import { liveQuery } from 'dexie';
import { db, type SubmissionRow } from '@/lib/db';
import type { SyncRunSummary } from '@/lib/sync-orchestrator';
import { SyncButton } from './SyncButton';

interface SyncPageProps {
  runSync: () => Promise<SyncRunSummary>;
}

const STATUS_ORDER: SubmissionRow['status'][] = [
  'pending_sync',
  'syncing',
  'retry_scheduled',
  'rejected',
  'synced',
];

const STATUS_LABEL: Record<SubmissionRow['status'], string> = {
  pending_sync: 'Pending',
  syncing: 'Syncing',
  retry_scheduled: 'Retry scheduled',
  rejected: 'Rejected',
  synced: 'Synced',
};

export function SyncPage({ runSync }: SyncPageProps) {
  const [rows, setRows] = useState<SubmissionRow[] | null>(null);

  useEffect(() => {
    const sub = liveQuery(async () => {
      return db.submissions.orderBy('submitted_at').reverse().toArray();
    }).subscribe({
      next: (data) => setRows(data),
      error: () => setRows([]),
    });
    return () => sub.unsubscribe();
  }, []);

  if (rows === null) {
    return <p className="p-6 text-sm text-muted-foreground">Loading…</p>;
  }

  if (rows.length === 0) {
    return (
      <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
        <h2 className="text-2xl font-semibold">Sync</h2>
        <p className="text-sm text-muted-foreground">No submissions yet.</p>
        <SyncButton runSync={runSync} />
      </section>
    );
  }

  const grouped = new Map<SubmissionRow['status'], SubmissionRow[]>();
  for (const s of STATUS_ORDER) grouped.set(s, []);
  for (const r of rows) grouped.get(r.status)?.push(r);

  return (
    <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
      <h2 className="text-2xl font-semibold">Sync</h2>
      <SyncButton runSync={runSync} />
      {STATUS_ORDER.map((s) => {
        const group = grouped.get(s) ?? [];
        if (group.length === 0) return null;
        return (
          <div key={s} className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-muted-foreground">
              {STATUS_LABEL[s]} ({group.length})
            </h3>
            <ul className="flex flex-col gap-1.5">
              {group.map((row) => (
                <li key={row.client_submission_id} className="rounded border p-2 text-xs">
                  <div className="font-mono">{row.client_submission_id}</div>
                  <div className="text-muted-foreground">
                    submitted {new Date(row.submitted_at).toLocaleString()}
                  </div>
                  {row.last_error ? (
                    <div className="text-destructive">
                      {row.last_error.code}: {row.last_error.message}
                    </div>
                  ) : null}
                  {row.next_retry_at ? (
                    <div className="text-muted-foreground">
                      retry at {new Date(row.next_retry_at).toLocaleString()}
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </section>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/components/sync/SyncPage.test.tsx`
Expected: PASS — 2 assertions.

- [ ] **Step 5: Commit**

---

## Task 11: Wire App.tsx — header, sync view toggle, triggers install

**Files:**
- Modify: `deliverables/F2/PWA/app/src/App.tsx`
- Modify: `deliverables/F2/PWA/app/src/App.test.tsx`

- [ ] **Step 1: Append failing App test**

Open `src/App.test.tsx`. After the existing tests, append:

```tsx
import { describe as describeApp, it as itApp, expect as expectApp, beforeEach as beforeEachApp } from 'vitest';
import { render as renderApp, screen as screenApp } from '@testing-library/react';
import userEventApp from '@testing-library/user-event';
import { db as dbApp, type SubmissionRow as SubmissionRowApp } from '@/lib/db';
import App from './App';

describeApp('App — sync integration', () => {
  beforeEachApp(async () => {
    if (!dbApp.isOpen()) await dbApp.open();
    await dbApp.submissions.clear();
    await dbApp.drafts.clear();
    localStorage.clear();
  });

  itApp('renders a pending count badge when the DB has pending submissions', async () => {
    const row: SubmissionRowApp = {
      client_submission_id: 'csid-pending',
      hcw_id: 'h1',
      status: 'pending_sync',
      synced_at: null,
      submitted_at: Date.now(),
      spec_version: 'v',
      values: {},
      retry_count: 0,
      next_retry_at: null,
      last_error: null,
    };
    await dbApp.submissions.put(row);
    renderApp(<App />);
    expectApp(await screenApp.findByTestId('pending-count')).toHaveTextContent('1 pending');
  });

  itApp('opens the Sync page when the header "Sync" link is clicked', async () => {
    renderApp(<App />);
    const user = userEventApp.setup();
    await user.click(await screenApp.findByRole('button', { name: /^sync$/i }));
    expectApp(await screenApp.findByRole('heading', { name: /^sync$/i })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/App.test.tsx`
Expected: FAIL — no "Sync" link in header, no `pending-count` testid on first render.

- [ ] **Step 3: Replace `src/App.tsx`**

Write `src/App.tsx`:

```tsx
import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { MultiSectionForm } from '@/components/survey/MultiSectionForm';
import { PendingCount } from '@/components/sync/PendingCount';
import { SyncPage } from '@/components/sync/SyncPage';
import type { FormValues } from '@/lib/skip-logic';
import { useInstallPrompt } from '@/lib/install-prompt';
import { getOrCreateDraftId, loadDraft, saveDraft, submitDraft } from '@/lib/draft';
import { getSyncEnv } from '@/lib/env';
import { hmacSha256Hex } from '@/lib/hmac';
import { postBatchSubmit } from '@/lib/sync-client';
import { runSync } from '@/lib/sync-orchestrator';
import { installSyncTriggers } from '@/lib/sync-triggers';

type Status = 'loading' | 'editing' | 'submitted';
type View = 'form' | 'sync';

const APP_VERSION = '0.1.0';
const DEVICE_FINGERPRINT_KEY = 'f2_device_fingerprint';
const SYNC_INTERVAL_MS = 5 * 60 * 1000;

function getOrCreateDeviceFingerprint(): string {
  const existing = localStorage.getItem(DEVICE_FINGERPRINT_KEY);
  if (existing) return existing;
  const fresh = crypto.randomUUID();
  localStorage.setItem(DEVICE_FINGERPRINT_KEY, fresh);
  return fresh;
}

function buildRunSync() {
  const env = getSyncEnv();
  const fingerprint = getOrCreateDeviceFingerprint();
  return () =>
    runSync({
      postBatchSubmit: (items) =>
        postBatchSubmit(items, {
          backendUrl: env.backendUrl,
          hmacSecret: env.hmacSecret,
          hmacSign: hmacSha256Hex,
          nowMs: Date.now,
          fetchImpl: fetch.bind(globalThis),
        }),
      nowMs: Date.now,
      batchSize: 25,
      specVersion: '2026-04-17-m1',
      appVersion: APP_VERSION,
      deviceFingerprint: fingerprint,
      stuckSyncingThresholdMs: 10 * 60 * 1000,
    });
}

export default function App() {
  const { canInstall, install } = useInstallPrompt();
  const [status, setStatus] = useState<Status>('loading');
  const [view, setView] = useState<View>('form');
  const [draftId, setDraftId] = useState<string>('');
  const [initialValues, setInitialValues] = useState<FormValues>({});
  const runSyncRef = useRef<() => Promise<ReturnType<typeof runSync> extends Promise<infer U> ? U : never>>(
    async () => ({ attempted: 0, synced: 0, failed: 0, retryScheduled: 0, alreadyRunning: false }),
  );

  useEffect(() => {
    const id = getOrCreateDraftId();
    setDraftId(id);
    loadDraft(id).then((row) => {
      setInitialValues((row?.values as FormValues | undefined) ?? {});
      setStatus('editing');
    });
  }, []);

  useEffect(() => {
    let triggers: { stop: () => void } | null = null;
    try {
      runSyncRef.current = buildRunSync();
      triggers = installSyncTriggers({
        runSync: runSyncRef.current,
        intervalMs: SYNC_INTERVAL_MS,
      });
    } catch (err) {
      // Missing env — sync disabled, log once and continue. The UI will still work offline.
      console.warn('[F2] sync disabled:', (err as Error).message);
    }
    return () => {
      triggers?.stop();
    };
  }, []);

  const handleAutosave = (values: FormValues) => {
    if (!draftId) return;
    void saveDraft(draftId, values);
  };

  const handleSubmit = async (values: FormValues) => {
    if (!draftId) return;
    await saveDraft(draftId, values);
    await submitDraft(draftId);
    setStatus('submitted');
    void runSyncRef.current();
  };

  return (
    <main className="flex min-h-full flex-col">
      <header className="flex items-center justify-between border-b px-6 py-3">
        <h1 className="text-lg font-semibold">F2 Survey</h1>
        <div className="flex items-center gap-3">
          <PendingCount />
          <Button size="sm" variant={view === 'sync' ? 'default' : 'outline'} onClick={() => setView(view === 'sync' ? 'form' : 'sync')}>
            {view === 'sync' ? 'Form' : 'Sync'}
          </Button>
          {canInstall ? (
            <Button size="sm" onClick={install}>
              Install
            </Button>
          ) : null}
        </div>
      </header>
      {view === 'sync' ? (
        <SyncPage runSync={runSyncRef.current} />
      ) : status === 'loading' ? (
        <p className="p-6 text-sm text-muted-foreground">Loading…</p>
      ) : status === 'submitted' ? (
        <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
          <h2 className="text-2xl font-semibold">Thank you</h2>
          <p className="text-sm text-muted-foreground">
            Your response is saved on this device and will sync when the app is online.
          </p>
        </section>
      ) : (
        <MultiSectionForm
          initialValues={initialValues}
          onAutosave={handleAutosave}
          onSubmit={handleSubmit}
        />
      )}
    </main>
  );
}
```

- [ ] **Step 4: Set test-time env so buildRunSync does not throw**

Open `src/test-setup.ts` and append:

```ts
import.meta.env.VITE_F2_BACKEND_URL = 'https://test.invalid/exec';
import.meta.env.VITE_F2_HMAC_SECRET = 'test-secret';
```

This lets `buildRunSync()` construct during App render without the env error path firing inside tests. The triggers' initial call is safely no-op'd because jsdom's `navigator.onLine` defaults to `true` and the mock fetch is never installed, so any actual sync attempt would fail harmlessly — but every App test that touches sync should explicitly stub `runSync`. No test in this plan triggers live sync.

- [ ] **Step 5: Run test to verify it passes**

Run: `npm test -- src/App.test.tsx`
Expected: PASS — new sync assertions green, existing App tests still pass.

- [ ] **Step 6: Full suite + typecheck**

Run: `npm test && npm run typecheck`
Expected: all suites green, tsc clean.

- [ ] **Step 7: Commit**

---

## Task 12: README + NEXT.md + live smoke

**Files:**
- Create: `deliverables/F2/PWA/app/SYNC.md`
- Modify: `deliverables/F2/PWA/app/NEXT.md`
- Modify: `deliverables/F2/PWA/app/README.md` (if present) or skip

- [ ] **Step 1: Create `SYNC.md` — operator-facing sync reference**

Write `app/SYNC.md`:

```markdown
# F2 PWA — Sync operator reference

## Configure

1. Deploy the backend per `../backend/README.md` §"One-time deploy".
2. `cp .env.example .env.local` in `app/`.
3. Fill in:
   - `VITE_F2_BACKEND_URL` — the Web App `/exec` URL.
   - `VITE_F2_HMAC_SECRET` — the 64-char hex secret from backend ScriptProperties.
4. `npm run build && npm run preview` — verify the PWA loads with sync enabled.

## How sync runs

The orchestrator (`src/lib/sync-orchestrator.ts`) triggers on:

1. Window `online` event
2. Every 5 minutes while the app is open
3. Immediately after the user submits a form
4. Manual click of the "Sync now" button

Reentrant calls are coalesced — only one `runSync()` executes at a time.

## State machine

```
pending_sync ──▶ syncing ──▶ synced          (200 accepted / duplicate)
    ▲              │    ▶    rejected         (E_VALIDATION / E_PAYLOAD_INVALID / E_SPEC_TOO_OLD)
    │              │    ▶    retry_scheduled  (network / 5xx / missing per-item result)
    │                         │
    └──────── backoff ────────┘   30s → 2m → 10m → 1h (capped)
```

Rows stuck in `syncing` for >10 minutes (crash mid-flight) are auto-reclaimed to `pending_sync` on the next run.

## Spec-too-old handling

If any batch item returns `E_SPEC_TOO_OLD`, `config.update_available` is set to `true` in IndexedDB. UI surfacing of the "Update available" banner is deferred to M6 (spec version gate).

## Debugging

Open the browser devtools → Application → IndexedDB → `f2_pwa` → `submissions`. Each row shows `status`, `retry_count`, `next_retry_at`, and `last_error`. Clear-and-replay by right-clicking a row and editing back to `pending_sync`.

## Deferred to later milestones

- Live-reload of the PWA when `update_available=true` — M6 or later.
- Per-item partial retry (currently the whole batch shares a transport-failure fate) — M10/M11 if observed as pain.
- Audit events (`install`, `sync_run_summary`) to `/audit` endpoint — M6 alongside facility enrollment.
```

- [ ] **Step 2: Rewrite `app/NEXT.md`**

```markdown
# Next step (future-Carl)

**Last milestone shipped:** M5 — Sync orchestrator end-to-end. Pending submissions drain from IndexedDB to the M4 backend via HMAC-signed `batch-submit` calls, honoring the full `pending_sync → syncing → synced | rejected | retry_scheduled` state machine with exponential backoff. Triggered on online/interval/manual/post-submit. **First demo-able vertical slice.**

**Next milestone:** M6 — Facility + enrollment scaffolding. 10–15h per spec §11.1.

**Before starting M6:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §8 (Enrollment & Facility data flow).
2. Target: fetch facility list via the M4 `/facilities` endpoint on first run + every app open, cache in Dexie `facilities` table, present HCW enrollment screen (select facility, enter HCW identifier) that populates the `hcw_id` + `facility_id` used by subsequent submissions.
3. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M6-enrollment.md`.

**M5 technical debt to address in later milestones:**

- `update_available=true` is written but no banner UI exists yet. Surface in M6/M7.
- Whole-batch retry granularity — a single transport failure retries all 25 rows together. If observed in pilots, split into per-chunk fallbacks.
- No telemetry of sync outcomes yet — the M4 `/audit` endpoint is unused from the PWA side. Wire in M6 alongside facility audit events.
- Hard-coded `spec_version='2026-04-17-m1'`. Replace with a fetched value from `/config` in M7 (spec version gate milestone).
- `APP_VERSION` is a string literal in `App.tsx`. Promote to a Vite-injected build stamp before M9 (observability).

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build` — confirm M5 still green.
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build` — confirm M4 still green.
- Copy `.env.example` → `.env.local` and fill both vars from the live Apps Script deployment.
- `npm run dev`, submit a response, watch it flow to the Google Sheet.
- Open `../2026-04-17-design-spec.md` §8 to re-orient for M6.
```

- [ ] **Step 3: Final verification pass**

Run: `cd deliverables/F2/PWA/app && npm test && npm run typecheck && npm run build`
Expected: all suites green, tsc clean, Vite build emits `dist/` without warnings.

- [ ] **Step 4: Live smoke (human-executed, optional but recommended)**

1. Ensure `.env.local` has real values from a deployed backend.
2. `npm run dev` → complete the survey → observe the "Sync now" button flip through `Syncing… → Synced 1`.
3. Open the backing Google Sheet. `F2_Responses` should now contain the row.
4. Disable Wi-Fi, submit another response, re-enable Wi-Fi. The `online` event should drain the queue; the new row appears in Sheets within a few seconds.
5. Force a rejection: edit `.env.local` so `VITE_F2_HMAC_SECRET` mismatches, rebuild+reload, submit → observe `retry_scheduled` with `last_error.code === 'E_SIG_INVALID'`.

- [ ] **Step 5: Commit**

*(All M5 work is complete. M5 is shipped — first demo-able vertical slice.)*

---

## Self-Review Notes

- **Spec §7.1 (SW caching):** unchanged from M2/M3 — vite-plugin-pwa already configured in `vite.config.ts`. M5 doesn't touch SW caching strategies beyond what's there. `/submit`/`/batch-submit` are POSTs not cached by default (Workbox ignores them unless `runtimeCaching` names them). ✓
- **Spec §7.2 (IndexedDB schema):** Task 4 adds v2 migration for `retry_count`, `next_retry_at`, `last_error` — the only schema delta §7.2 implies for a functioning state machine. The base columns (`status`, `synced_at`) were already in M2. ✓
- **Spec §7.3 (state machine):** all five states implemented; all three success/rejected/transport branches in `applyResponse`; backoff schedule matches spec table (30s→2m→10m→1h, cap at 1h). Task 6 tests cover each branch. ✓
- **Spec §7.3 (sync triggers priority):** `online` ✓ (Task 7), periodic ✓ (Task 7), manual ✓ (Task 9 `SyncButton`), post-submit ✓ (`App.tsx` handleSubmit). Background Sync API is explicitly a stretch not blocking M5 shipment — flagged in README deferred section. ✓
- **Spec §7.3 (batching max 50):** M5 caps at 25 with rationale logged in Architectural Decisions #3. Backend accepts ≤50, so we're conservative. ✓
- **Spec §7.4 (install):** already wired in M1/M2 via `install-prompt.ts`. M5 doesn't change it. ✓
- **Spec §7.5 (manifest):** already in `vite.config.ts`. M5 doesn't change it. ✓
- **Spec §7.6 (storage persistence + quota):** deferred — `navigator.storage.persist()` + estimate monitoring belongs with enrollment (M6) or hardening (M11). Called out in M5 NEXT.md tech debt. *Intentional gap.*
- **Spec §7.7 (spec version handling):** Task 6 sets `config.update_available=true` when `E_SPEC_TOO_OLD` is observed. Banner UI + forced update flow is deferred to M6 with an explicit deferred-note in SYNC.md and NEXT.md. *Intentional partial — states the machine works; UI surfacing comes next.*
- **Spec §7.8 (iOS):** no iOS-specific code paths added here. `navigator.onLine` + foreground interval works identically on iOS Safari. Background Sync stretch is explicitly skipped. ✓
- **Spec §11.1 M5 row coverage:** "Sync orchestrator end-to-end" ✓, "Async state machines, Background Sync" ✓ (state machine full; Background Sync flagged as stretch), "First vertical slice. Demo-able." ✓ (live smoke in Task 12 Step 4). ✓
- **Placeholder scan:** no TBD/TODO/fill-in-later. All tasks have complete code, exact commands, and expected output.
- **Type consistency:** `BatchSubmitItem`, `BatchSubmitResultItem`, `BatchSubmitResponse`, `OrchestratorDeps`, `SyncRunSummary`, `SubmissionRow`, `LastError` are defined once and referenced consistently across Tasks 4–11. `runSync` is called identically from `App.tsx` (Task 11), `SyncButton` (Task 9 via prop), and `SyncPage` (Task 10 via prop).
- **DRY:** `canonicalString` + `hmacSha256Hex` live once in `hmac.ts`, consumed by `sync-client.ts` via injection; the backend has its own copy (plan M4 Task 3) — same algorithm, different runtime, verified by the known-answer test.
