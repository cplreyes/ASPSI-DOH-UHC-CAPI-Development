# F2 PWA — M8 Facility List + Enrollment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hardcoded `hcw_id: 'anonymous'` placeholder with a real enrollment flow — fetch the facility master list from the M4 backend's `/facilities` endpoint, cache it in Dexie, and gate the survey behind a one-time enrollment screen that captures `hcw_id` + `facility_id` (and persists the resolved `facility_type` for downstream cross-field rules).

**Architecture:** A new GET-flavored API client (`facilities-client.ts`) signs requests with the existing HMAC helper and hits `?action=facilities`. A `facilities-cache.ts` layer wraps Dexie reads/writes and exposes a `refreshFacilities()` that is called once on app boot (best-effort, swallows offline errors). Enrollment is a single Dexie row read by an `AuthContext` provider — the App component renders `<EnrollmentScreen>` when `enrollment === null`, else the existing form. Form submissions inherit `hcw_id` + `facility_id` + `facility_type` from the enrollment row, both as top-level `SubmissionRow` columns and embedded inside `values` so the existing sync-orchestrator path keeps working.

**Tech Stack:** Dexie 4 (schema v3 bump) · React 18 Context + hooks · TypeScript · Apps Script `/facilities` GET endpoint (HMAC-signed) · Vitest 4 + @testing-library/react + fake-indexeddb.

**Spec section reference:** `2026-04-17-design-spec.md` §11.1 row M8 ("Facility list + enrollment flow", 8–10h, "AuthContext, cached lookups, Proper enrollment"); §5.2 (`AuthContext` mention); §5.3 (Home: "enroll (HCW id + facility select), resume"); §5.5 (HCW identity in `AuthContext` + Dexie); §7.1 (`/facilities` cached StaleWhileRevalidate); §7.2 (Dexie `facilities` store schema); plus `backend/src/Handlers.js` `handleFacilities` (returns `{ ok: true, data: { facilities: FacilityRow[] } }`) and `backend/src/Schema.js` `FACILITY_MASTER_LIST_COLUMNS = [facility_id, facility_name, facility_type, region, province, city_mun, barangay]`.

**Out of scope (deferred):**
- **`facility_has_bucas` / `facility_has_gamot` flags.** NEXT.md mentioned these, but the M4 `FACILITY_MASTER_LIST_COLUMNS` schema does not include them. Adding them is a backend schema change — defer to M9 (when it lands paired with the FAC-01..07 cross-field rules that consume the flags). M8 scope is `facility_type` only.
- **`response_source` per-respondent capture.** Currently hardcoded `source: 'pwa'` server-side via existing M5 wiring. SRC-01..03 cross-field rules need this; defer to M9.
- **Spec-driven `/config` fetch.** `/config` is a separate endpoint; M8 only wires `/facilities`. M11 hardening can add `/config` polling.
- **Tutorial / install-prompt restructuring on Home.** Existing App.tsx already shows the install button on the header; M8 does not touch install UX. Spec §7.4 install workflow stays as-is.
- **Multi-respondent on one device** (switching enrollments mid-draft). M8 enrollment is one-shot and persistent until manual unenroll. Multi-respondent waits for M11 if needed.

---

## File Structure (decomposition)

| File | Responsibility | Status |
|---|---|---|
| `app/src/lib/db.ts` | bump Dexie to v3: extend `FacilityRow` with `facility_type/facility_name/city_mun/barangay`, index `facility_type`; add `enrollment` store (single row) | modify |
| `app/src/lib/db.test.ts` | tests for the v3 upgrade and the new enrollment store | modify |
| `app/src/lib/facilities-client.ts` | NEW: `getFacilities()` — signed GET to `?action=facilities` | create |
| `app/src/lib/facilities-client.test.ts` | NEW: unit tests with mocked fetch | create |
| `app/src/lib/facilities-cache.ts` | NEW: `refreshFacilities()`, `listFacilities()`, `getFacility(id)` | create |
| `app/src/lib/facilities-cache.test.ts` | NEW: unit tests against fake-indexeddb | create |
| `app/src/lib/enrollment.ts` | NEW: `getEnrollment()`, `setEnrollment(...)`, `clearEnrollment()` Dexie wrapper | create |
| `app/src/lib/enrollment.test.ts` | NEW: unit tests against fake-indexeddb | create |
| `app/src/lib/auth-context.tsx` | NEW: `<AuthProvider>` + `useAuth()` hook exposing `{enrollment, enroll, unenroll, status}` | create |
| `app/src/lib/auth-context.test.tsx` | NEW: provider boot + enroll + unenroll tests | create |
| `app/src/components/enrollment/EnrollmentScreen.tsx` | NEW: facility-select + HCW-id form, calls `enroll()` | create |
| `app/src/components/enrollment/EnrollmentScreen.test.tsx` | NEW: render + submit tests | create |
| `app/src/lib/draft.ts` | use `hcw_id` from enrollment row passed in (no longer hardcodes 'anonymous') | modify |
| `app/src/lib/draft.test.ts` | update to assert real `hcw_id` is propagated | modify |
| `app/src/App.tsx` | wrap in `<AuthProvider>`; render `<EnrollmentScreen>` when no enrollment; otherwise inject `hcw_id` + `facility_id` + `facility_type` into form initialValues | modify |
| `app/src/App.test.tsx` | update existing tests + add enrollment-gate test | modify |
| `app/NEXT.md` | rewrite to point at M9 (i18n) | modify |

---

## Task 1: Bump Dexie schema to v3 (extend facilities + add enrollment store)

**Files:**
- Modify: `app/src/lib/db.ts`
- Modify: `app/src/lib/db.test.ts`

The current `FacilityRow` only has `id/region/province/name`. The backend returns `facility_id/facility_name/facility_type/region/province/city_mun/barangay`. Bump to v3, rename fields to match the backend, and add a single-row `enrollment` table.

- [ ] **Step 1: Read existing db.test.ts to learn the test pattern**

Run: `cat app/src/lib/db.test.ts | head -40`

Expected: confirms how the file imports `db` and uses `fake-indexeddb`. Note the assertion pattern; reuse it in step 2.

- [ ] **Step 2: Add a failing test for the v3 schema**

Append to `app/src/lib/db.test.ts` inside the existing `describe` block (or add a new one):

```ts
describe('F2Database v3', () => {
  it('exposes a facilities table with facility_type indexed', async () => {
    await db.facilities.put({
      facility_id: 'F-001',
      facility_name: 'Manila General',
      facility_type: 'Hospital',
      region: 'NCR',
      province: 'Metro Manila',
      city_mun: 'Manila',
      barangay: 'Ermita',
    });
    const found = await db.facilities.where('facility_type').equals('Hospital').first();
    expect(found?.facility_id).toBe('F-001');
  });

  it('exposes an enrollment table that stores a single row', async () => {
    await db.enrollment.put({
      id: 'singleton',
      hcw_id: 'HCW-42',
      facility_id: 'F-001',
      facility_type: 'Hospital',
      enrolled_at: 1_700_000_000_000,
    });
    const row = await db.enrollment.get('singleton');
    expect(row).toMatchObject({ hcw_id: 'HCW-42', facility_id: 'F-001' });
  });
});
```

- [ ] **Step 3: Run the failing tests**

Run: `cd app && npx vitest run src/lib/db.test.ts`
Expected: 2 new tests fail with `Property 'enrollment' does not exist` (compile error) or `KeyPath did not yield a value`.

- [ ] **Step 4: Update `app/src/lib/db.ts`**

Replace the `FacilityRow` interface and the class body. The full updated file:

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
  facility_id: string;
  facility_name: string;
  facility_type: string;
  region: string;
  province: string;
  city_mun: string;
  barangay: string;
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

export interface EnrollmentRow {
  id: 'singleton';
  hcw_id: string;
  facility_id: string;
  facility_type: string;
  enrolled_at: number;
}

export class F2Database extends Dexie {
  drafts!: Table<DraftRow, string>;
  submissions!: Table<SubmissionRow, string>;
  facilities!: Table<FacilityRow, string>;
  config!: Table<ConfigRow, string>;
  audit!: Table<AuditRow, number>;
  enrollment!: Table<EnrollmentRow, string>;

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
        submissions: 'client_submission_id, status, synced_at, hcw_id, next_retry_at',
      })
      .upgrade(async (tx) => {
        await tx.table<SubmissionRow, string>('submissions').toCollection().modify((row) => {
          if (row.retry_count == null) row.retry_count = 0;
          if (row.next_retry_at === undefined) row.next_retry_at = null;
          if (row.last_error === undefined) row.last_error = null;
        });
      });
    this.version(3).stores({
      facilities: 'facility_id, facility_type, region, province',
      enrollment: 'id',
    });
  }
}

export const db = new F2Database();
```

Notes on the diff:
- `FacilityRow` keys renamed to match backend (`facility_id` not `id`, `facility_name` not `name`). Any v1/v2 rows are dropped because the primary key changes — v3 store re-creates with the new key path. Acceptable: facilities cache is rebuilt on next `refreshFacilities()` call.
- `enrollment` uses fixed primary key `'singleton'` so reads/writes are key-based without extra lookup logic.

- [ ] **Step 5: Run the db tests**

Run: `cd app && npx vitest run src/lib/db.test.ts`
Expected: all tests pass (the 2 new ones plus any existing v1/v2 tests).

- [ ] **Step 6: Run the full suite to catch downstream type breaks**

Run: `cd app && npx vitest run`
Expected: TypeScript errors in any consumer that referenced `FacilityRow.id/region/.../name` — there shouldn't be any yet because facilities is unused so far. Confirm 202+ tests still pass.

- [ ] **Step 7: Commit**

```bash
git add app/src/lib/db.ts app/src/lib/db.test.ts
git commit -m "feat(f2-pwa): M8.1 Dexie v3 — extend FacilityRow, add enrollment store"
```

---

## Task 2: Facilities API client (signed GET)

**Files:**
- Create: `app/src/lib/facilities-client.ts`
- Create: `app/src/lib/facilities-client.test.ts`

`/facilities` is a GET endpoint, signed with the same HMAC scheme as `/batch-submit`. Canonical string is `GET|facilities|<ts>|` (empty body).

- [ ] **Step 1: Write the failing tests**

Create `app/src/lib/facilities-client.test.ts`:

```ts
import { describe, expect, it, vi } from 'vitest';
import { getFacilities } from './facilities-client';

const sampleEnvelope = {
  ok: true,
  data: {
    facilities: [
      {
        facility_id: 'F-001',
        facility_name: 'Manila General',
        facility_type: 'Hospital',
        region: 'NCR',
        province: 'Metro Manila',
        city_mun: 'Manila',
        barangay: 'Ermita',
      },
    ],
  },
};

function buildDeps(fetchImpl: typeof fetch) {
  return {
    backendUrl: 'https://script.example/exec',
    hmacSecret: 'secret',
    hmacSign: vi.fn().mockResolvedValue('SIGNATURE'),
    nowMs: () => 1_700_000_000_000,
    fetchImpl,
  };
}

describe('getFacilities', () => {
  it('signs the request with GET|facilities|<ts>|', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(sampleEnvelope), { status: 200 }),
    );
    const deps = buildDeps(fetchImpl);
    await getFacilities(deps);
    expect(deps.hmacSign).toHaveBeenCalledWith('secret', 'GET|facilities|1700000000000|');
  });

  it('returns the facilities array on a 200 ok envelope', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(sampleEnvelope), { status: 200 }),
    );
    const out = await getFacilities(buildDeps(fetchImpl));
    expect(out).toEqual({ ok: true, facilities: sampleEnvelope.data.facilities });
  });

  it('returns transport error on network failure', async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error('boom'));
    const out = await getFacilities(buildDeps(fetchImpl));
    expect(out).toEqual({
      ok: false,
      transport: true,
      error: { code: 'E_NETWORK', message: 'boom' },
    });
  });

  it('returns transport error on non-2xx', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response('nope', { status: 500 }));
    const out = await getFacilities(buildDeps(fetchImpl));
    expect(out).toMatchObject({ ok: false, transport: true, error: { code: 'E_HTTP_500' } });
  });

  it('returns logical error on ok=false envelope', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: false, error: { code: 'E_KILL_SWITCH', message: 'down' } }), { status: 200 }),
    );
    const out = await getFacilities(buildDeps(fetchImpl));
    expect(out).toEqual({
      ok: false,
      transport: false,
      error: { code: 'E_KILL_SWITCH', message: 'down' },
    });
  });
});
```

- [ ] **Step 2: Run the failing tests**

Run: `cd app && npx vitest run src/lib/facilities-client.test.ts`
Expected: import error (`./facilities-client` does not exist).

- [ ] **Step 3: Create `app/src/lib/facilities-client.ts`**

```ts
import type { FacilityRow } from './db';

export interface FacilitiesClientDeps {
  backendUrl: string;
  hmacSecret: string;
  hmacSign: (secret: string, message: string) => Promise<string>;
  nowMs: () => number;
  fetchImpl: typeof fetch;
}

export type GetFacilitiesResponse =
  | { ok: true; facilities: FacilityRow[] }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function getFacilities(deps: FacilitiesClientDeps): Promise<GetFacilitiesResponse> {
  const ts = deps.nowMs();
  const canonical = `GET|facilities|${ts}|`;
  const sig = await deps.hmacSign(deps.hmacSecret, canonical);
  const params = new URLSearchParams({ action: 'facilities', ts: String(ts), sig });
  const url = `${deps.backendUrl}?${params.toString()}`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, { method: 'GET' });
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
  } catch {
    return {
      ok: false,
      transport: true,
      error: { code: 'E_PARSE', message: 'Invalid JSON from backend' },
    };
  }

  const env = parsed as
    | { ok: true; data: { facilities: FacilityRow[] } }
    | { ok: false; error: { code: string; message: string } };

  if (env && env.ok === true) {
    return { ok: true, facilities: env.data.facilities };
  }
  return {
    ok: false,
    transport: false,
    error: env && 'error' in env ? env.error : { code: 'E_UNKNOWN', message: 'Malformed backend envelope' },
  };
}
```

- [ ] **Step 4: Run the tests**

Run: `cd app && npx vitest run src/lib/facilities-client.test.ts`
Expected: 5/5 pass.

- [ ] **Step 5: Commit**

```bash
git add app/src/lib/facilities-client.ts app/src/lib/facilities-client.test.ts
git commit -m "feat(f2-pwa): M8.2 facilities-client (signed GET to /facilities)"
```

---

## Task 3: Facilities cache (Dexie wrapper + refresh)

**Files:**
- Create: `app/src/lib/facilities-cache.ts`
- Create: `app/src/lib/facilities-cache.test.ts`

`refreshFacilities()` calls `getFacilities()` and replaces the Dexie table contents. `listFacilities()` and `getFacility()` are pure reads. Refresh is idempotent and tolerates network failure (returns the error to the caller, never throws).

- [ ] **Step 1: Write the failing tests**

Create `app/src/lib/facilities-cache.test.ts`:

```ts
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { db } from './db';
import { getFacility, listFacilities, refreshFacilities } from './facilities-cache';
import type { GetFacilitiesResponse } from './facilities-client';

const fac = (id: string, type = 'Hospital'): import('./db').FacilityRow => ({
  facility_id: id,
  facility_name: `Facility ${id}`,
  facility_type: type,
  region: 'NCR',
  province: 'Metro Manila',
  city_mun: 'Manila',
  barangay: 'Ermita',
});

describe('facilities-cache', () => {
  beforeEach(async () => {
    await db.facilities.clear();
  });

  it('listFacilities returns rows ordered by facility_name', async () => {
    await db.facilities.bulkPut([fac('F-002'), fac('F-001'), fac('F-003')]);
    const out = await listFacilities();
    expect(out.map((f) => f.facility_id)).toEqual(['F-001', 'F-002', 'F-003']);
  });

  it('getFacility returns undefined for an unknown id', async () => {
    expect(await getFacility('F-XXX')).toBeUndefined();
  });

  it('refreshFacilities replaces the table on success', async () => {
    await db.facilities.put(fac('F-OLD'));
    const fetcher = vi
      .fn<() => Promise<GetFacilitiesResponse>>()
      .mockResolvedValue({ ok: true, facilities: [fac('F-NEW')] });
    const result = await refreshFacilities({ fetcher });
    expect(result).toEqual({ ok: true, count: 1 });
    expect(await db.facilities.toArray()).toHaveLength(1);
    expect(await getFacility('F-NEW')).toBeDefined();
    expect(await getFacility('F-OLD')).toBeUndefined();
  });

  it('refreshFacilities leaves the cache untouched on transport error', async () => {
    await db.facilities.put(fac('F-KEEP'));
    const fetcher = vi
      .fn<() => Promise<GetFacilitiesResponse>>()
      .mockResolvedValue({
        ok: false,
        transport: true,
        error: { code: 'E_NETWORK', message: 'offline' },
      });
    const result = await refreshFacilities({ fetcher });
    expect(result).toEqual({ ok: false, error: { code: 'E_NETWORK', message: 'offline' } });
    expect(await getFacility('F-KEEP')).toBeDefined();
  });
});
```

- [ ] **Step 2: Run the failing tests**

Run: `cd app && npx vitest run src/lib/facilities-cache.test.ts`
Expected: import error (`./facilities-cache` does not exist).

- [ ] **Step 3: Create `app/src/lib/facilities-cache.ts`**

```ts
import { db, type FacilityRow } from './db';
import type { GetFacilitiesResponse } from './facilities-client';

export interface RefreshDeps {
  fetcher: () => Promise<GetFacilitiesResponse>;
}

export type RefreshResult =
  | { ok: true; count: number }
  | { ok: false; error: { code: string; message: string } };

export async function refreshFacilities(deps: RefreshDeps): Promise<RefreshResult> {
  const response = await deps.fetcher();
  if (!response.ok) {
    return { ok: false, error: response.error };
  }
  await db.transaction('rw', db.facilities, async () => {
    await db.facilities.clear();
    if (response.facilities.length > 0) {
      await db.facilities.bulkPut(response.facilities);
    }
  });
  return { ok: true, count: response.facilities.length };
}

export async function listFacilities(): Promise<FacilityRow[]> {
  const all = await db.facilities.toArray();
  return all.sort((a, b) => a.facility_name.localeCompare(b.facility_name));
}

export async function getFacility(facilityId: string): Promise<FacilityRow | undefined> {
  return db.facilities.get(facilityId);
}
```

- [ ] **Step 4: Run the tests**

Run: `cd app && npx vitest run src/lib/facilities-cache.test.ts`
Expected: 4/4 pass.

- [ ] **Step 5: Commit**

```bash
git add app/src/lib/facilities-cache.ts app/src/lib/facilities-cache.test.ts
git commit -m "feat(f2-pwa): M8.3 facilities cache (Dexie wrapper + refresh)"
```

---

## Task 4: Enrollment store (Dexie wrapper)

**Files:**
- Create: `app/src/lib/enrollment.ts`
- Create: `app/src/lib/enrollment.test.ts`

A thin layer over the singleton `enrollment` Dexie row. `setEnrollment` snapshots the resolved facility into the row so `facility_type` is available without re-querying the cache on every form submit.

- [ ] **Step 1: Write the failing tests**

Create `app/src/lib/enrollment.test.ts`:

```ts
import { beforeEach, describe, expect, it } from 'vitest';
import { db } from './db';
import { clearEnrollment, getEnrollment, setEnrollment } from './enrollment';

describe('enrollment store', () => {
  beforeEach(async () => {
    await db.enrollment.clear();
    await db.facilities.clear();
    await db.facilities.put({
      facility_id: 'F-001',
      facility_name: 'Manila General',
      facility_type: 'Hospital',
      region: 'NCR',
      province: 'Metro Manila',
      city_mun: 'Manila',
      barangay: 'Ermita',
    });
  });

  it('getEnrollment returns null when not enrolled', async () => {
    expect(await getEnrollment()).toBeNull();
  });

  it('setEnrollment persists hcw_id, facility_id, and resolved facility_type', async () => {
    const before = Date.now();
    const row = await setEnrollment({ hcw_id: 'HCW-42', facility_id: 'F-001' });
    expect(row).toMatchObject({
      id: 'singleton',
      hcw_id: 'HCW-42',
      facility_id: 'F-001',
      facility_type: 'Hospital',
    });
    expect(row.enrolled_at).toBeGreaterThanOrEqual(before);
    const reloaded = await getEnrollment();
    expect(reloaded).toEqual(row);
  });

  it('setEnrollment throws if the facility_id is unknown to the cache', async () => {
    await expect(setEnrollment({ hcw_id: 'HCW-1', facility_id: 'F-XXX' })).rejects.toThrow(
      /facility F-XXX/i,
    );
  });

  it('setEnrollment throws on empty hcw_id', async () => {
    await expect(setEnrollment({ hcw_id: '   ', facility_id: 'F-001' })).rejects.toThrow(
      /hcw_id is required/i,
    );
  });

  it('clearEnrollment removes the singleton row', async () => {
    await setEnrollment({ hcw_id: 'HCW-1', facility_id: 'F-001' });
    await clearEnrollment();
    expect(await getEnrollment()).toBeNull();
  });
});
```

- [ ] **Step 2: Run the failing tests**

Run: `cd app && npx vitest run src/lib/enrollment.test.ts`
Expected: import error (`./enrollment` does not exist).

- [ ] **Step 3: Create `app/src/lib/enrollment.ts`**

```ts
import { db, type EnrollmentRow } from './db';

export interface SetEnrollmentInput {
  hcw_id: string;
  facility_id: string;
}

export async function getEnrollment(): Promise<EnrollmentRow | null> {
  const row = await db.enrollment.get('singleton');
  return row ?? null;
}

export async function setEnrollment(input: SetEnrollmentInput): Promise<EnrollmentRow> {
  const trimmedHcw = input.hcw_id.trim();
  if (trimmedHcw.length === 0) {
    throw new Error('hcw_id is required');
  }
  const facility = await db.facilities.get(input.facility_id);
  if (!facility) {
    throw new Error(`Unknown facility ${input.facility_id}`);
  }
  const row: EnrollmentRow = {
    id: 'singleton',
    hcw_id: trimmedHcw,
    facility_id: facility.facility_id,
    facility_type: facility.facility_type,
    enrolled_at: Date.now(),
  };
  await db.enrollment.put(row);
  return row;
}

export async function clearEnrollment(): Promise<void> {
  await db.enrollment.delete('singleton');
}
```

- [ ] **Step 4: Run the tests**

Run: `cd app && npx vitest run src/lib/enrollment.test.ts`
Expected: 5/5 pass.

- [ ] **Step 5: Commit**

```bash
git add app/src/lib/enrollment.ts app/src/lib/enrollment.test.ts
git commit -m "feat(f2-pwa): M8.4 enrollment store (Dexie singleton)"
```

---

## Task 5: AuthContext + useAuth hook

**Files:**
- Create: `app/src/lib/auth-context.tsx`
- Create: `app/src/lib/auth-context.test.tsx`

The provider boots by reading the enrollment row. Status is `'loading'` while reading, `'unenrolled'` if no row, `'enrolled'` if a row exists. `enroll()` writes via `setEnrollment` then updates context state; `unenroll()` calls `clearEnrollment` then resets state.

- [ ] **Step 1: Write the failing tests**

Create `app/src/lib/auth-context.test.tsx`:

```tsx
import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from './auth-context';
import { db } from './db';

function Probe() {
  const { status, enrollment, enroll, unenroll } = useAuth();
  return (
    <div>
      <span data-testid="status">{status}</span>
      <span data-testid="hcw">{enrollment?.hcw_id ?? '-'}</span>
      <button onClick={() => void enroll({ hcw_id: 'HCW-1', facility_id: 'F-001' })}>enroll</button>
      <button onClick={() => void unenroll()}>unenroll</button>
    </div>
  );
}

describe('<AuthProvider>', () => {
  beforeEach(async () => {
    await db.enrollment.clear();
    await db.facilities.clear();
    await db.facilities.put({
      facility_id: 'F-001',
      facility_name: 'Manila General',
      facility_type: 'Hospital',
      region: 'NCR',
      province: 'Metro Manila',
      city_mun: 'Manila',
      barangay: 'Ermita',
    });
  });

  it('boots into "unenrolled" when no row exists', async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('unenrolled'));
    expect(screen.getByTestId('hcw').textContent).toBe('-');
  });

  it('boots into "enrolled" when a row exists', async () => {
    await db.enrollment.put({
      id: 'singleton',
      hcw_id: 'HCW-PRE',
      facility_id: 'F-001',
      facility_type: 'Hospital',
      enrolled_at: 1,
    });
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('enrolled'));
    expect(screen.getByTestId('hcw').textContent).toBe('HCW-PRE');
  });

  it('enroll() updates context state', async () => {
    const user = userEvent.setup();
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('unenrolled'));
    await user.click(screen.getByRole('button', { name: 'enroll' }));
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('enrolled'));
    expect(screen.getByTestId('hcw').textContent).toBe('HCW-1');
  });

  it('unenroll() resets context state', async () => {
    await db.enrollment.put({
      id: 'singleton',
      hcw_id: 'HCW-PRE',
      facility_id: 'F-001',
      facility_type: 'Hospital',
      enrolled_at: 1,
    });
    const user = userEvent.setup();
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('enrolled'));
    await user.click(screen.getByRole('button', { name: 'unenroll' }));
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('unenrolled'));
  });
});
```

- [ ] **Step 2: Run the failing tests**

Run: `cd app && npx vitest run src/lib/auth-context.test.tsx`
Expected: import error (`./auth-context` does not exist).

- [ ] **Step 3: Create `app/src/lib/auth-context.tsx`**

```tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type { EnrollmentRow } from './db';
import {
  clearEnrollment,
  getEnrollment,
  setEnrollment,
  type SetEnrollmentInput,
} from './enrollment';

export type AuthStatus = 'loading' | 'unenrolled' | 'enrolled';

export interface AuthContextValue {
  status: AuthStatus;
  enrollment: EnrollmentRow | null;
  enroll: (input: SetEnrollmentInput) => Promise<EnrollmentRow>;
  unenroll: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [enrollment, setEnrollmentState] = useState<EnrollmentRow | null>(null);

  useEffect(() => {
    let cancelled = false;
    void getEnrollment().then((row) => {
      if (cancelled) return;
      setEnrollmentState(row);
      setStatus(row ? 'enrolled' : 'unenrolled');
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const enroll = async (input: SetEnrollmentInput) => {
    const row = await setEnrollment(input);
    setEnrollmentState(row);
    setStatus('enrolled');
    return row;
  };

  const unenroll = async () => {
    await clearEnrollment();
    setEnrollmentState(null);
    setStatus('unenrolled');
  };

  return (
    <AuthContext.Provider value={{ status, enrollment, enroll, unenroll }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an <AuthProvider>');
  }
  return ctx;
}
```

- [ ] **Step 4: Run the tests**

Run: `cd app && npx vitest run src/lib/auth-context.test.tsx`
Expected: 4/4 pass.

- [ ] **Step 5: Commit**

```bash
git add app/src/lib/auth-context.tsx app/src/lib/auth-context.test.tsx
git commit -m "feat(f2-pwa): M8.5 AuthContext + useAuth hook"
```

---

## Task 6: EnrollmentScreen component

**Files:**
- Create: `app/src/components/enrollment/EnrollmentScreen.tsx`
- Create: `app/src/components/enrollment/EnrollmentScreen.test.tsx`

A simple form: HCW id input, facility `<select>` (populated from `listFacilities()`), Enroll button. On submit, calls `enroll()` from `useAuth`. Shows a "Refresh facility list" button that calls a passed-in `onRefresh` callback (so the App component can wire the actual network call without coupling the screen to env / fetch). Empty facility list shows a friendly message + the refresh button.

- [ ] **Step 1: Write the failing tests**

Create `app/src/components/enrollment/EnrollmentScreen.test.tsx`:

```tsx
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '@/lib/auth-context';
import { db } from '@/lib/db';
import { EnrollmentScreen } from './EnrollmentScreen';

function setup(props: Partial<React.ComponentProps<typeof EnrollmentScreen>> = {}) {
  return render(
    <AuthProvider>
      <EnrollmentScreen onRefresh={vi.fn().mockResolvedValue({ ok: true, count: 1 })} {...props} />
    </AuthProvider>,
  );
}

describe('<EnrollmentScreen>', () => {
  beforeEach(async () => {
    await db.enrollment.clear();
    await db.facilities.clear();
    await db.facilities.bulkPut([
      {
        facility_id: 'F-001',
        facility_name: 'Manila General',
        facility_type: 'Hospital',
        region: 'NCR',
        province: 'Metro Manila',
        city_mun: 'Manila',
        barangay: 'Ermita',
      },
      {
        facility_id: 'F-002',
        facility_name: 'Cebu Health Center',
        facility_type: 'RHU',
        region: 'Region VII',
        province: 'Cebu',
        city_mun: 'Cebu City',
        barangay: 'Lahug',
      },
    ]);
  });

  it('renders the title, HCW id input, and a populated facility select', async () => {
    setup();
    expect(
      screen.getByRole('heading', { name: /enrol|enroll/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/HCW ID/i)).toBeInTheDocument();
    await waitFor(() => {
      const select = screen.getByLabelText(/Facility/i) as HTMLSelectElement;
      expect(select.options.length).toBeGreaterThanOrEqual(3); // placeholder + 2 facilities
    });
    expect(screen.getByText('Cebu Health Center')).toBeInTheDocument();
  });

  it('disables Enroll until both fields are filled', async () => {
    const user = userEvent.setup();
    setup();
    await waitFor(() => screen.getByText('Manila General'));
    const button = screen.getByRole('button', { name: /^enroll$/i });
    expect(button).toBeDisabled();

    await user.type(screen.getByLabelText(/HCW ID/i), 'HCW-42');
    expect(button).toBeDisabled();

    await user.selectOptions(screen.getByLabelText(/Facility/i), 'F-001');
    expect(button).toBeEnabled();
  });

  it('calls onRefresh when the refresh button is clicked', async () => {
    const onRefresh = vi.fn().mockResolvedValue({ ok: true, count: 2 });
    const user = userEvent.setup();
    setup({ onRefresh });
    await waitFor(() => screen.getByText('Manila General'));
    await user.click(screen.getByRole('button', { name: /refresh/i }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it('shows an empty-state message + refresh button when no facilities are cached', async () => {
    await db.facilities.clear();
    setup();
    await waitFor(() =>
      expect(screen.getByText(/no facilities/i)).toBeInTheDocument(),
    );
    expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
  });

  it('persists enrollment on submit', async () => {
    const user = userEvent.setup();
    setup();
    await waitFor(() => screen.getByText('Manila General'));
    await user.type(screen.getByLabelText(/HCW ID/i), 'HCW-42');
    await user.selectOptions(screen.getByLabelText(/Facility/i), 'F-001');
    await user.click(screen.getByRole('button', { name: /^enroll$/i }));
    await waitFor(async () => {
      const row = await db.enrollment.get('singleton');
      expect(row?.hcw_id).toBe('HCW-42');
      expect(row?.facility_id).toBe('F-001');
      expect(row?.facility_type).toBe('Hospital');
    });
  });

  it('shows an error message if enrollment fails', async () => {
    await db.facilities.clear(); // forces setEnrollment to throw "Unknown facility"
    await db.facilities.put({
      facility_id: 'F-001',
      facility_name: 'Stale',
      facility_type: 'Hospital',
      region: '', province: '', city_mun: '', barangay: '',
    });
    const user = userEvent.setup();
    setup();
    await waitFor(() => screen.getByText('Stale'));
    await user.type(screen.getByLabelText(/HCW ID/i), 'HCW-42');
    await user.selectOptions(screen.getByLabelText(/Facility/i), 'F-001');
    // Wipe between selecting and submitting to force the error path:
    await db.facilities.clear();
    await user.click(screen.getByRole('button', { name: /^enroll$/i }));
    await waitFor(() =>
      expect(screen.getByText(/unknown facility/i)).toBeInTheDocument(),
    );
  });
});
```

- [ ] **Step 2: Run the failing tests**

Run: `cd app && npx vitest run src/components/enrollment/EnrollmentScreen.test.tsx`
Expected: import error (`./EnrollmentScreen` does not exist).

- [ ] **Step 3: Create `app/src/components/enrollment/EnrollmentScreen.tsx`**

```tsx
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';
import { listFacilities, type RefreshResult } from '@/lib/facilities-cache';
import type { FacilityRow } from '@/lib/db';

interface EnrollmentScreenProps {
  onRefresh: () => Promise<RefreshResult>;
}

export function EnrollmentScreen({ onRefresh }: EnrollmentScreenProps) {
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
      <h2 className="text-2xl font-semibold tracking-tight">Enroll</h2>
      <p className="text-sm text-muted-foreground">
        Enter your HCW ID and select your facility. You can change these later from the Sync page.
      </p>

      <label className="flex flex-col gap-1 text-sm">
        HCW ID
        <input
          type="text"
          value={hcwId}
          onChange={(e) => setHcwId(e.target.value)}
          className="rounded-md border border-input px-3 py-2 text-sm"
          autoComplete="off"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        Facility
        {facilities.length === 0 ? (
          <span className="text-sm text-muted-foreground">
            No facilities cached. Tap Refresh to download the master list.
          </span>
        ) : (
          <select
            value={facilityId}
            onChange={(e) => setFacilityId(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Select a facility…</option>
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
          Enroll
        </Button>
        <Button type="button" variant="outline" onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? 'Refreshing…' : 'Refresh facility list'}
        </Button>
      </div>
    </form>
  );
}
```

- [ ] **Step 4: Run the tests**

Run: `cd app && npx vitest run src/components/enrollment/EnrollmentScreen.test.tsx`
Expected: 6/6 pass.

- [ ] **Step 5: Commit**

```bash
git add app/src/components/enrollment/EnrollmentScreen.tsx app/src/components/enrollment/EnrollmentScreen.test.tsx
git commit -m "feat(f2-pwa): M8.6 EnrollmentScreen (HCW + facility select)"
```

---

## Task 7: Wire enrollment into App.tsx + draft.ts

**Files:**
- Modify: `app/src/lib/draft.ts`
- Modify: `app/src/lib/draft.test.ts`
- Modify: `app/src/App.tsx`
- Modify: `app/src/App.test.tsx`

Two coupled changes:

1. `draft.ts` no longer hardcodes `hcw_id: 'anonymous'`. Both `saveDraft` and `submitDraft` accept an `EnrollmentInfo` argument carrying `hcw_id` + `facility_id` + `facility_type`. `submitDraft` injects all three into `values` so the existing sync orchestrator (which reads `row.values['facility_id']`) works unchanged.
2. `App.tsx` wraps in `<AuthProvider>`, gates the form behind `enrollment !== null`, and feeds the enrollment into `saveDraft` / `submitDraft`.

- [ ] **Step 1: Update draft.ts (signature change)**

Replace the existing `app/src/lib/draft.ts` with:

```ts
import { db, type DraftRow, type SubmissionRow } from './db';

const DRAFT_ID_KEY = 'f2_current_draft_id';
const SPEC_VERSION_PLACEHOLDER = '2026-04-17-m1';

export interface EnrollmentInfo {
  hcw_id: string;
  facility_id: string;
  facility_type: string;
}

export function getOrCreateDraftId(): string {
  const existing = localStorage.getItem(DRAFT_ID_KEY);
  if (existing) return existing;
  const fresh = crypto.randomUUID();
  localStorage.setItem(DRAFT_ID_KEY, fresh);
  return fresh;
}

export async function loadDraft(id: string): Promise<DraftRow | undefined> {
  return db.drafts.get(id);
}

export async function saveDraft(
  id: string,
  values: Record<string, unknown>,
  enrollment: EnrollmentInfo,
): Promise<void> {
  const row: DraftRow = {
    id,
    hcw_id: enrollment.hcw_id,
    updated_at: Date.now(),
    values,
  };
  await db.drafts.put(row);
}

export async function submitDraft(
  id: string,
  enrollment: EnrollmentInfo,
): Promise<SubmissionRow> {
  return db.transaction('rw', db.drafts, db.submissions, async () => {
    const draft = await db.drafts.get(id);
    if (!draft) throw new Error(`Draft ${id} not found`);

    const valuesWithFacility = {
      ...draft.values,
      facility_id: enrollment.facility_id,
      facility_type: enrollment.facility_type,
    };

    const submission: SubmissionRow = {
      client_submission_id: crypto.randomUUID(),
      hcw_id: enrollment.hcw_id,
      status: 'pending_sync',
      synced_at: null,
      submitted_at: Date.now(),
      spec_version: SPEC_VERSION_PLACEHOLDER,
      values: valuesWithFacility,
      retry_count: 0,
      next_retry_at: null,
      last_error: null,
    };

    await db.submissions.put(submission);
    await db.drafts.delete(id);
    if (localStorage.getItem(DRAFT_ID_KEY) === id) {
      localStorage.removeItem(DRAFT_ID_KEY);
    }

    return submission;
  });
}
```

- [ ] **Step 2: Update draft.test.ts to pass EnrollmentInfo**

Open `app/src/lib/draft.test.ts` and:
- Define a test fixture `const ENROLLMENT = { hcw_id: 'HCW-1', facility_id: 'F-001', facility_type: 'Hospital' };`
- Pass `ENROLLMENT` as the third arg to every `saveDraft(...)` and second arg to every `submitDraft(...)` call.
- Add an assertion in the submit test that `submission.values.facility_id === 'F-001'` and `submission.hcw_id === 'HCW-1'`.

If the file is short, the diff is mechanical. After editing, run:

Run: `cd app && npx vitest run src/lib/draft.test.ts`
Expected: all tests pass with the new signature.

- [ ] **Step 3: Update App.tsx**

Replace the existing `app/src/App.tsx` body. The full updated file:

```tsx
import { useEffect, useMemo, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { MultiSectionForm } from '@/components/survey/MultiSectionForm';
import { EnrollmentScreen } from '@/components/enrollment/EnrollmentScreen';
import { PendingCount } from '@/components/sync/PendingCount';
import { SyncPage } from '@/components/sync/SyncPage';
import type { FormValues } from '@/lib/skip-logic';
import { useInstallPrompt } from '@/lib/install-prompt';
import { AuthProvider, useAuth } from '@/lib/auth-context';
import { getOrCreateDraftId, loadDraft, saveDraft, submitDraft, type EnrollmentInfo } from '@/lib/draft';
import { getSyncEnv } from '@/lib/env';
import { hmacSha256Hex } from '@/lib/hmac';
import { postBatchSubmit } from '@/lib/sync-client';
import { runSync, type SyncRunSummary } from '@/lib/sync-orchestrator';
import { installSyncTriggers } from '@/lib/sync-triggers';
import { getFacilities } from '@/lib/facilities-client';
import { refreshFacilities } from '@/lib/facilities-cache';

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

function buildRunSync(): () => Promise<SyncRunSummary> {
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

const noopRunSync: () => Promise<SyncRunSummary> = async () => ({
  attempted: 0,
  synced: 0,
  failed: 0,
  retryScheduled: 0,
  alreadyRunning: false,
});

function buildRefreshFacilities() {
  const env = getSyncEnv();
  return () =>
    refreshFacilities({
      fetcher: () =>
        getFacilities({
          backendUrl: env.backendUrl,
          hmacSecret: env.hmacSecret,
          hmacSign: hmacSha256Hex,
          nowMs: Date.now,
          fetchImpl: fetch.bind(globalThis),
        }),
    });
}

function AppShell() {
  const { canInstall, install } = useInstallPrompt();
  const { status: authStatus, enrollment } = useAuth();
  const [status, setStatus] = useState<Status>('loading');
  const [view, setView] = useState<View>('form');
  const [draftId, setDraftId] = useState<string>('');
  const [initialValues, setInitialValues] = useState<FormValues>({});
  const runSyncRef = useRef<() => Promise<SyncRunSummary>>(noopRunSync);

  const enrollmentInfo: EnrollmentInfo | null = useMemo(
    () =>
      enrollment
        ? {
            hcw_id: enrollment.hcw_id,
            facility_id: enrollment.facility_id,
            facility_type: enrollment.facility_type,
          }
        : null,
    [enrollment],
  );

  useEffect(() => {
    if (authStatus !== 'enrolled') return;
    const id = getOrCreateDraftId();
    setDraftId(id);
    void loadDraft(id).then((row) => {
      setInitialValues((row?.values as FormValues | undefined) ?? {});
      setStatus('editing');
    });
  }, [authStatus]);

  useEffect(() => {
    let triggers: { stop: () => void } | null = null;
    try {
      runSyncRef.current = buildRunSync();
      triggers = installSyncTriggers({
        runSync: runSyncRef.current,
        intervalMs: SYNC_INTERVAL_MS,
      });
    } catch (err) {
      console.warn('[F2] sync disabled:', (err as Error).message);
    }
    return () => {
      triggers?.stop();
    };
  }, []);

  const refresh = useMemo(() => {
    try {
      return buildRefreshFacilities();
    } catch {
      return async () => ({ ok: false as const, error: { code: 'E_ENV', message: 'Backend env missing' } });
    }
  }, []);

  const handleAutosave = (values: FormValues) => {
    if (!draftId || !enrollmentInfo) return;
    void saveDraft(draftId, values, enrollmentInfo);
  };

  const handleSubmit = async (values: FormValues) => {
    if (!draftId || !enrollmentInfo) return;
    await saveDraft(draftId, values, enrollmentInfo);
    await submitDraft(draftId, enrollmentInfo);
    setStatus('submitted');
    void runSyncRef.current();
  };

  return (
    <main className="flex min-h-full flex-col">
      <header className="flex items-center justify-between border-b px-6 py-3">
        <h1 className="text-lg font-semibold">F2 Survey</h1>
        <div className="flex items-center gap-3">
          <PendingCount />
          {authStatus === 'enrolled' ? (
            <Button
              size="sm"
              variant={view === 'sync' ? 'default' : 'outline'}
              onClick={() => setView(view === 'sync' ? 'form' : 'sync')}
            >
              {view === 'sync' ? 'Form' : 'Sync'}
            </Button>
          ) : null}
          {canInstall ? (
            <Button size="sm" onClick={install}>
              Install
            </Button>
          ) : null}
        </div>
      </header>

      {authStatus === 'loading' ? (
        <p className="p-6 text-sm text-muted-foreground">Loading…</p>
      ) : authStatus === 'unenrolled' ? (
        <EnrollmentScreen onRefresh={refresh} />
      ) : view === 'sync' ? (
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

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
```

- [ ] **Step 4: Update App.test.tsx**

Open `app/src/App.test.tsx`. Existing tests render `<App />` directly and assume the form renders immediately. They will now hit the EnrollmentScreen first. For each existing test that needs the form to render:
- Either pre-seed the enrollment row in `beforeEach`:

```ts
import { db } from '@/lib/db';

beforeEach(async () => {
  await db.enrollment.clear();
  await db.facilities.clear();
  await db.facilities.put({
    facility_id: 'F-001',
    facility_name: 'Manila General',
    facility_type: 'Hospital',
    region: 'NCR', province: 'Metro Manila', city_mun: 'Manila', barangay: 'Ermita',
  });
  await db.enrollment.put({
    id: 'singleton',
    hcw_id: 'HCW-1',
    facility_id: 'F-001',
    facility_type: 'Hospital',
    enrolled_at: 1,
  });
});
```

- Or guard each existing assertion with a `waitFor` because enrollment loads asynchronously.

Then add one new test:

```ts
it('renders the EnrollmentScreen when no enrollment row exists', async () => {
  await db.enrollment.clear();
  render(<App />);
  await waitFor(() =>
    expect(screen.getByRole('heading', { name: /enrol|enroll/i })).toBeInTheDocument(),
  );
});
```

If `App.test.tsx` is structured around a single `it` that walks the full submit path, modifying it in place is straightforward — read the file, find the existing assertions, wrap them in `await waitFor(...)`. The two-test split (one for unenrolled, one for enrolled-and-edit) is the safer refactor.

- [ ] **Step 5: Run all the form-related tests**

Run: `cd app && npx vitest run src/lib/draft.test.ts src/App.test.tsx`
Expected: green.

- [ ] **Step 6: Run the full test suite**

Run: `cd app && npx vitest run`
Expected: all tests pass — adjust any other test that imported `saveDraft`/`submitDraft` directly to pass the new `EnrollmentInfo` arg. Search with `grep`:

Run: `cd app && grep -rn "saveDraft\|submitDraft" src tests 2>/dev/null | grep -v "\.tsx\?:.*\(import\|export\|interface\|type\|//\)"` to find all callers.

- [ ] **Step 7: Run typecheck and build**

Run: `cd app && npm run typecheck && npm run build`
Expected: both clean.

- [ ] **Step 8: Commit**

```bash
git add app/src/lib/draft.ts app/src/lib/draft.test.ts app/src/App.tsx app/src/App.test.tsx
git commit -m "feat(f2-pwa): M8.7 wire enrollment into App + draft (replaces 'anonymous' placeholder)"
```

---

## Task 8: Update NEXT.md → M9

**Files:**
- Modify: `app/NEXT.md`

- [ ] **Step 1: Replace the file content**

Overwrite `app/NEXT.md` with:

```markdown
# Next step (future-Carl)

**Last milestone shipped:** M8 — Facility list + enrollment flow. Dexie bumped to v3 with extended `FacilityRow` (matches backend `FacilityMasterList` columns) and a singleton `enrollment` table. New `facilities-client.ts` signs `GET /facilities` with the same HMAC scheme as `/batch-submit`. `facilities-cache.ts` exposes `refreshFacilities()`, `listFacilities()`, `getFacility()` against Dexie. `enrollment.ts` snapshots the resolved facility into the row on `setEnrollment` so `facility_type` is available without re-querying. New `<AuthProvider>` + `useAuth()` hook reads enrollment on boot. New `<EnrollmentScreen>` (HCW id input + facility select + Refresh button) is rendered by `App.tsx` whenever no enrollment row exists. `draft.ts` no longer hardcodes `hcw_id: 'anonymous'` — both `saveDraft` and `submitDraft` take an `EnrollmentInfo` arg, and `submitDraft` injects `facility_id` + `facility_type` into the submission `values` so the existing sync-orchestrator path keeps working.

**Next milestone:** M9 — i18n (Filipino translations). 10–15h per spec §11.1, +20–30h if Carl translates rather than ASPSI.

**Before starting M9:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §5.5 (UI language) and §11.1 row M9.
2. Resolve open question #1 in spec §13: are ASPSI translators delivering the Filipino bundle, or does Carl translate? Affects scope by ~25h.
3. Target: install react-i18next, externalize all hardcoded English strings (header, EnrollmentScreen, ReviewSection, navigator, error messages, instrument labels via the generator), wire a language switcher into the header, persist choice in `localStorage`. Section/item labels need to flow through the generator — emit `{ en, fil }` pairs from the spec and look up by current locale.
4. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M9-i18n.md`.

**M8 technical debt to address in later milestones:**

- **`facility_has_bucas` / `facility_has_gamot` flags** — not in the M4 schema yet. M9 (or whichever milestone owns FAC-01..07 cross-field rules) should add these columns server-side, regenerate the master list, and extend `FacilityRow`.
- **`response_source` per-respondent capture** — currently hardcoded `source: 'pwa'`. SRC-01..03 cross-field rules want this. Wire when adding the deferred 14+ cross-field rules.
- **Sync-page "change enrollment" affordance** — `unenroll()` exists but no UI calls it. Add a button on the Sync page in M11 (or whenever multi-respondent on one device matters).
- **Auto-refresh facilities on app open** — currently only the explicit Refresh button on EnrollmentScreen calls it. Spec §7.1 prescribes StaleWhileRevalidate via the SW; consider wiring once Workbox runtime caching is configured in M11.
- **`/config` endpoint** — backend has it (returns `current_spec_version`, `kill_switch`, `broadcast_message`); PWA never calls it. M11 hardening should poll on app open to surface kill-switch + broadcast_message.

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build` — confirm M8 still green.
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build` — confirm M4 still green.
- Copy `.env.example` → `.env.local` and fill both vars from the live Apps Script deployment.
- `npm run dev`, walk through: enrollment screen → fill form → review → submit → sync — verify the submitted row's `facility_id` lands in the Sheet.
- Open `../2026-04-17-design-spec.md` §5.5 + §11.1 row M9 and `spec/F2-Spec.md` to re-orient for i18n.
```

- [ ] **Step 2: Commit**

```bash
git add app/NEXT.md
git commit -m "docs(f2-pwa): M8.8 update NEXT.md to point at M9 (i18n)"
```

---

## Self-review notes

**Spec coverage check:**
- §11.1 row M8 "Facility list + enrollment flow" / "AuthContext, cached lookups" → Tasks 2–7 ✓
- §5.2 `AuthContext` mention → Task 5 ✓
- §5.3 "enroll (HCW id + facility select)" → Tasks 6–7 ✓
- §5.5 "HCW identity in AuthContext + Dexie" → Tasks 4–5 ✓
- §7.2 Dexie `facilities` store → Task 1 (extended beyond spec's minimal `id, region, province, name` to include `facility_type` because cross-field rules need it) ✓
- §7.1 `/facilities` SWR caching → partially: app-level cache (Tasks 2–3) lands. Workbox SW config explicitly deferred to M11 (noted in NEXT.md).
- "facility_has_bucas / facility_has_gamot" — explicitly deferred (out of scope, documented in plan + NEXT.md) ✓

**Type consistency check:**
- `FacilityRow` keys: `facility_id`, `facility_name`, `facility_type`, `region`, `province`, `city_mun`, `barangay` — used identically in db.ts, facilities-client.ts, facilities-cache.ts, enrollment.ts, EnrollmentScreen.tsx.
- `EnrollmentRow.id` is the literal `'singleton'` everywhere.
- `EnrollmentInfo` (from `draft.ts`) and `EnrollmentRow` (from `db.ts`): `EnrollmentInfo` is a subset; the App component constructs it from the full row inside a `useMemo`. Consistent.
- `useAuth()` returns `{ status, enrollment, enroll, unenroll }` — matches the test probe in Task 5 and the App consumer in Task 7.
- `RefreshResult` from `facilities-cache.ts` — used as `EnrollmentScreen`'s `onRefresh` return type in Task 6 and constructed by `App.tsx` in Task 7.
- `GetFacilitiesResponse` from `facilities-client.ts` — consumed by `RefreshDeps['fetcher']` in Task 3.

**Placeholder scan:** None. All steps contain literal code. The `App.test.tsx` update (Task 7 Step 4) describes the diff verbally because the existing test file's structure isn't in this plan's scope — the engineer reads the file, makes the mechanical change, runs the suite.

---

**Plan saved to `deliverables/F2/PWA/2026-04-18-implementation-plan-M8-enrollment.md`.**
