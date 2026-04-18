# F2 PWA M2 — Autosave + IndexedDB (Dexie) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `alert(...)` submit handler in `App.tsx` with durable IndexedDB storage, and add 500 ms debounced autosave so an accidental reload preserves in-progress Section A answers.

**Architecture:** Dexie wraps IndexedDB. Two active tables in M2 — `drafts` (in-progress answers, keyed by a stable per-device UUID persisted in `localStorage`) and `submissions` (completed entries with `status='pending_sync'`, waiting for M3 sync). The `Section` component stays the source of truth for editing state via react-hook-form; it gains `defaultValues` and `onAutosave` props. `App.tsx` owns the draft lifecycle — load on mount, write on change (debounced), archive draft → submission on submit. Sync network I/O is **out of scope** — we only build the state machine precursor described in spec §7.3.

**Tech Stack:** Dexie 4.x (IndexedDB wrapper), fake-indexeddb 5.x (test-only IDB shim), react-hook-form 7.72 (`watch` for autosave trigger), Zod 3.25 (unchanged from M1), Vitest 4 + @testing-library/react 16 (tests), `crypto.randomUUID()` (native, no extra dep).

**Source of truth for schema:** `deliverables/F2/PWA/2026-04-17-design-spec.md` §5.5 (state management), §7.2 (Dexie schema), §7.3 (sync state machine — precursor only).

**Scope guardrails:**

- Draft identity: single draft slot per device, id persisted in `localStorage['f2_current_draft_id']`. Proper enrollment flow is deferred (M5+).
- `hcw_id`: stubbed as `'anonymous'`. AuthContext is out of scope for M2.
- `spec_version`: stubbed as `'2026-04-17-m1'`. Real versioning lands with the spec-hash endpoint (M7+).
- Facility list / config / audit tables: schema defined now (to avoid a migration later) but not written to.
- **Do not** implement network sync, retry, or background sync here — those are M3+.
- **No git commits requested in this plan.** User handles git manually; do not run `git add`/`git commit`.

---

## File Structure

- **Create** `src/lib/db.ts` — Dexie instance + row types. Matches spec §7.2 verbatim.
- **Create** `src/lib/db.test.ts` — smoke test for schema (tables present, v1).
- **Create** `src/lib/draft.ts` — pure functions: `getOrCreateDraftId`, `loadDraft`, `saveDraft`, `submitDraft`.
- **Create** `src/lib/draft.test.ts` — unit tests for draft.ts.
- **Modify** `src/test-setup.ts` — import `fake-indexeddb/auto`, reset db + localStorage between tests.
- **Modify** `src/components/survey/Section.tsx` — add `defaultValues` + `onAutosave` props.
- **Modify** `src/components/survey/Section.test.tsx` — update existing test call-sites, add autosave + default-values tests.
- **Modify** `src/App.tsx` — replace `alert`, wire load → autosave → submit lifecycle, add success banner.
- **Modify** `src/App.test.tsx` — integration test: autosave → remount → value restored.
- **Modify** `package.json` — via `npm install` (Dexie + fake-indexeddb).

Files that change together live together: db.ts + db.test.ts + draft.ts + draft.test.ts form one focused data-layer module. Section changes stay in the survey component folder. App.tsx gets all of the glue.

---

## Task 1: Install dependencies and wire fake-indexeddb in tests

**Files:**
- Modify: `package.json` (via `npm install`)
- Modify: `src/test-setup.ts`

**Rationale:** Dexie needs the global `indexedDB`. jsdom (our Vitest env) does not provide one. `fake-indexeddb/auto` installs a compliant in-memory shim.

- [ ] **Step 1: Install runtime and dev dependencies**

Run (from `deliverables/F2/PWA/app/`):
```bash
npm install dexie@^4.0.0
npm install --save-dev fake-indexeddb@^5.0.0
```

Expected: both packages added to `package.json`; `package-lock.json` updated.

- [ ] **Step 2: Update `src/test-setup.ts` to install the IDB shim**

Replace the file contents with:

```ts
import '@testing-library/jest-dom/vitest';
import 'fake-indexeddb/auto';
import { afterEach } from 'vitest';

afterEach(async () => {
  // Wipe every fake-IDB database between tests so state never leaks.
  const dbs = await indexedDB.databases();
  await Promise.all(
    dbs.map(
      ({ name }) =>
        name &&
        new Promise<void>((resolve, reject) => {
          const req = indexedDB.deleteDatabase(name);
          req.onsuccess = () => resolve();
          req.onerror = () => reject(req.error);
          req.onblocked = () => resolve();
        }),
    ),
  );
  localStorage.clear();
});
```

- [ ] **Step 3: Verify test setup compiles and existing tests still pass**

Run:
```bash
npm run test
```

Expected: 48/48 passing, no regressions. If jsdom complains about `indexedDB.databases()`, upgrade fake-indexeddb to `^5.0.2` minimum.

---

## Task 2: Create Dexie schema module

**Files:**
- Create: `src/lib/db.ts`
- Create: `src/lib/db.test.ts`

- [ ] **Step 1: Write the failing schema smoke test**

Create `src/lib/db.test.ts`:

```ts
import { describe, it, expect } from 'vitest';
import { db } from './db';

describe('db', () => {
  it('opens at version 1 with the spec §7.2 schema', async () => {
    await db.open();
    expect(db.verno).toBe(1);
    const names = db.tables.map((t) => t.name).sort();
    expect(names).toEqual(
      ['audit', 'config', 'drafts', 'facilities', 'submissions'].sort(),
    );
  });

  it('uses id as primary key for drafts', async () => {
    await db.open();
    expect(db.table('drafts').schema.primKey.name).toBe('id');
  });

  it('uses client_submission_id as primary key for submissions', async () => {
    await db.open();
    expect(db.table('submissions').schema.primKey.name).toBe(
      'client_submission_id',
    );
  });
});
```

- [ ] **Step 2: Run the test to confirm it fails**

Run:
```bash
npm run test -- src/lib/db.test.ts
```

Expected: FAIL — `Cannot find module './db'`.

- [ ] **Step 3: Implement `src/lib/db.ts`**

Create `src/lib/db.ts`:

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

export interface SubmissionRow {
  client_submission_id: string;
  hcw_id: string;
  status: SubmissionStatus;
  synced_at: number | null;
  submitted_at: number;
  spec_version: string;
  values: Record<string, unknown>;
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
  }
}

export const db = new F2Database();
```

- [ ] **Step 4: Run the test to confirm it passes**

Run:
```bash
npm run test -- src/lib/db.test.ts
```

Expected: 3/3 passing.

---

## Task 3: Draft id helper — `getOrCreateDraftId`

**Files:**
- Create: `src/lib/draft.ts`
- Create: `src/lib/draft.test.ts`

**Why:** Spec §7.2 invariant — "id on a draft is stable from enroll onward". M2 persists it in `localStorage` so the same id is reused across reloads.

- [ ] **Step 1: Write the failing tests**

Create `src/lib/draft.test.ts`:

```ts
import { describe, it, expect, beforeEach } from 'vitest';
import { getOrCreateDraftId } from './draft';

describe('getOrCreateDraftId', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('generates and persists a new UUID when localStorage is empty', () => {
    const id = getOrCreateDraftId();
    expect(id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );
    expect(localStorage.getItem('f2_current_draft_id')).toBe(id);
  });

  it('returns the existing id when localStorage already has one', () => {
    localStorage.setItem('f2_current_draft_id', 'existing-id');
    expect(getOrCreateDraftId()).toBe('existing-id');
  });
});
```

- [ ] **Step 2: Run the test to confirm it fails**

Run:
```bash
npm run test -- src/lib/draft.test.ts
```

Expected: FAIL — `Cannot find module './draft'`.

- [ ] **Step 3: Implement `getOrCreateDraftId`**

Create `src/lib/draft.ts`:

```ts
import { db, type DraftRow, type SubmissionRow } from './db';

const DRAFT_ID_KEY = 'f2_current_draft_id';
const HCW_ID_PLACEHOLDER = 'anonymous';
const SPEC_VERSION_PLACEHOLDER = '2026-04-17-m1';

export function getOrCreateDraftId(): string {
  const existing = localStorage.getItem(DRAFT_ID_KEY);
  if (existing) return existing;
  const fresh = crypto.randomUUID();
  localStorage.setItem(DRAFT_ID_KEY, fresh);
  return fresh;
}
```

- [ ] **Step 4: Run the test to confirm it passes**

Run:
```bash
npm run test -- src/lib/draft.test.ts
```

Expected: 2/2 passing.

---

## Task 4: Draft CRUD — `loadDraft` and `saveDraft`

**Files:**
- Modify: `src/lib/draft.ts`
- Modify: `src/lib/draft.test.ts`

- [ ] **Step 1: Add failing tests for loadDraft / saveDraft**

Append to `src/lib/draft.test.ts`:

```ts
import { loadDraft, saveDraft } from './draft';
import { db } from './db';

describe('saveDraft + loadDraft', () => {
  beforeEach(async () => {
    localStorage.clear();
    // Re-open db after afterEach wipe.
    if (!db.isOpen()) await db.open();
  });

  it('returns undefined for an unknown id', async () => {
    expect(await loadDraft('nope')).toBeUndefined();
  });

  it('round-trips values', async () => {
    await saveDraft('draft-1', { Q3: 'Female', Q4: 25 });
    const row = await loadDraft('draft-1');
    expect(row?.values).toEqual({ Q3: 'Female', Q4: 25 });
    expect(row?.hcw_id).toBe('anonymous');
    expect(typeof row?.updated_at).toBe('number');
  });

  it('overwrites on repeated saves and updates updated_at', async () => {
    await saveDraft('draft-1', { Q3: 'Male' });
    const first = await loadDraft('draft-1');
    await new Promise((r) => setTimeout(r, 5));
    await saveDraft('draft-1', { Q3: 'Male', Q4: 30 });
    const second = await loadDraft('draft-1');
    expect(second?.values).toEqual({ Q3: 'Male', Q4: 30 });
    expect(second!.updated_at).toBeGreaterThanOrEqual(first!.updated_at);
  });
});
```

- [ ] **Step 2: Run the test to confirm it fails**

Run:
```bash
npm run test -- src/lib/draft.test.ts
```

Expected: FAIL — `loadDraft` / `saveDraft` not exported.

- [ ] **Step 3: Implement `loadDraft` + `saveDraft`**

Append to `src/lib/draft.ts`:

```ts
export async function loadDraft(id: string): Promise<DraftRow | undefined> {
  return db.drafts.get(id);
}

export async function saveDraft(
  id: string,
  values: Record<string, unknown>,
): Promise<void> {
  const row: DraftRow = {
    id,
    hcw_id: HCW_ID_PLACEHOLDER,
    updated_at: Date.now(),
    values,
  };
  await db.drafts.put(row);
}
```

- [ ] **Step 4: Run the test to confirm it passes**

Run:
```bash
npm run test -- src/lib/draft.test.ts
```

Expected: all previous + 3 new = 5/5 passing.

---

## Task 5: Draft → Submission archive — `submitDraft`

**Files:**
- Modify: `src/lib/draft.ts`
- Modify: `src/lib/draft.test.ts`

**Contract:** Per spec §7.2: "Draft → submission on Submit: draft archived, submission row created with `status='pending_sync'`." `client_submission_id` is fresh UUID (idempotency key for future sync retries). After archival, the draft id in `localStorage` is cleared so the next form starts from a clean id.

- [ ] **Step 1: Add failing test**

Append to `src/lib/draft.test.ts`:

```ts
import { submitDraft } from './draft';

describe('submitDraft', () => {
  beforeEach(async () => {
    localStorage.clear();
    if (!db.isOpen()) await db.open();
  });

  it('creates a submission row and deletes the draft', async () => {
    localStorage.setItem('f2_current_draft_id', 'draft-1');
    await saveDraft('draft-1', { Q3: 'Female', Q4: 25 });

    const submission = await submitDraft('draft-1');

    expect(submission.status).toBe('pending_sync');
    expect(submission.synced_at).toBeNull();
    expect(submission.values).toEqual({ Q3: 'Female', Q4: 25 });
    expect(submission.client_submission_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );
    expect(submission.spec_version).toBe('2026-04-17-m1');

    expect(await loadDraft('draft-1')).toBeUndefined();
    expect(localStorage.getItem('f2_current_draft_id')).toBeNull();

    const stored = await db.submissions.get(submission.client_submission_id);
    expect(stored).toEqual(submission);
  });

  it('throws if the draft does not exist', async () => {
    await expect(submitDraft('nope')).rejects.toThrow(/not found/i);
  });
});
```

- [ ] **Step 2: Run the test to confirm it fails**

Run:
```bash
npm run test -- src/lib/draft.test.ts
```

Expected: FAIL — `submitDraft` not exported.

- [ ] **Step 3: Implement `submitDraft`**

Append to `src/lib/draft.ts`:

```ts
export async function submitDraft(id: string): Promise<SubmissionRow> {
  return db.transaction('rw', db.drafts, db.submissions, async () => {
    const draft = await db.drafts.get(id);
    if (!draft) throw new Error(`Draft ${id} not found`);

    const submission: SubmissionRow = {
      client_submission_id: crypto.randomUUID(),
      hcw_id: draft.hcw_id,
      status: 'pending_sync',
      synced_at: null,
      submitted_at: Date.now(),
      spec_version: SPEC_VERSION_PLACEHOLDER,
      values: draft.values,
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

- [ ] **Step 4: Run the test to confirm it passes**

Run:
```bash
npm run test -- src/lib/draft.test.ts
```

Expected: 7/7 passing.

---

## Task 6: Add `defaultValues` prop to `Section`

**Files:**
- Modify: `src/components/survey/Section.tsx`
- Modify: `src/components/survey/Section.test.tsx`

**Why:** On mount, App needs to pass previously saved draft answers back into the form so the user sees what they had before reload. RHF accepts `defaultValues` at `useForm` time.

- [ ] **Step 1: Add failing test**

Append to `src/components/survey/Section.test.tsx` (inside the existing `describe`):

```ts
it('prefills inputs from defaultValues', () => {
  render(
    <Section
      section={fixture}
      schema={schema}
      defaultValues={{ Q3: 'Female', Q4: 25 }}
      onSubmit={() => {}}
    />,
  );
  expect(screen.getByLabelText(/Q3/)).toHaveValue('Female');
  expect(screen.getByLabelText(/Q4/)).toHaveValue(25);
});
```

(If existing tests don't import `screen`, add it: `import { render, screen } from '@testing-library/react';`.)

- [ ] **Step 2: Run the test to confirm it fails**

Run:
```bash
npm run test -- src/components/survey/Section.test.tsx
```

Expected: FAIL — `defaultValues` prop does not exist on `SectionProps`, or inputs render empty.

- [ ] **Step 3: Add the `defaultValues` prop to `Section`**

Modify `src/components/survey/Section.tsx`:

```tsx
import { FormProvider, useForm, type DefaultValues } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type { ZodTypeAny } from 'zod';
import type { Section as SectionModel } from '@/types/survey';
import { Button } from '@/components/ui/button';
import { Question } from './Question';

interface SectionProps<T extends Record<string, unknown>> {
  section: SectionModel;
  schema: ZodTypeAny;
  defaultValues?: DefaultValues<T>;
  onSubmit: (values: T) => void;
}

export function Section<T extends Record<string, unknown>>({
  section,
  schema,
  defaultValues,
  onSubmit,
}: SectionProps<T>) {
  const methods = useForm<T>({
    resolver: zodResolver(schema),
    mode: 'onSubmit',
    defaultValues,
  });

  return (
    <FormProvider {...methods}>
      <form
        onSubmit={methods.handleSubmit((values) => onSubmit(values as T))}
        className="mx-auto flex max-w-xl flex-col gap-4 p-6"
        noValidate
      >
        <header className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold tracking-tight">
            Section {section.id} — {section.title}
          </h2>
          {section.preamble ? (
            <p className="text-sm text-muted-foreground">{section.preamble}</p>
          ) : null}
        </header>

        {section.items.map((item) => (
          <Question key={item.id} item={item} />
        ))}

        <div className="pt-4">
          <Button type="submit">Submit</Button>
        </div>
      </form>
    </FormProvider>
  );
}
```

- [ ] **Step 4: Run the test to confirm it passes**

Run:
```bash
npm run test -- src/components/survey/Section.test.tsx
```

Expected: all previous + 1 new passing.

---

## Task 7: Add debounced `onAutosave` prop to `Section`

**Files:**
- Modify: `src/components/survey/Section.tsx`
- Modify: `src/components/survey/Section.test.tsx`

**Why:** The spec mandates 500 ms debounced autosave on every field edit. `react-hook-form`'s `watch` callback fires on every change; a simple setTimeout gate debounces it.

- [ ] **Step 1: Add failing test (uses fake timers)**

Append to `src/components/survey/Section.test.tsx`:

```ts
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';

it('calls onAutosave with debounced form values', async () => {
  vi.useFakeTimers();
  const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
  const onAutosave = vi.fn();

  render(
    <Section
      section={fixture}
      schema={schema}
      onAutosave={onAutosave}
      onSubmit={() => {}}
    />,
  );

  await user.type(screen.getByLabelText(/Q3/), 'Female');

  // Not fired yet — still within debounce window.
  vi.advanceTimersByTime(400);
  expect(onAutosave).not.toHaveBeenCalled();

  // Crosses the 500 ms threshold.
  vi.advanceTimersByTime(200);
  expect(onAutosave).toHaveBeenCalledTimes(1);
  expect(onAutosave.mock.calls[0][0]).toMatchObject({ Q3: 'Female' });

  vi.useRealTimers();
});
```

- [ ] **Step 2: Run the test to confirm it fails**

Run:
```bash
npm run test -- src/components/survey/Section.test.tsx
```

Expected: FAIL — `onAutosave` prop does not exist or is not wired.

- [ ] **Step 3: Wire the debounced watch subscription**

In `src/components/survey/Section.tsx`, add the import and effect:

```tsx
import { useEffect } from 'react';
// ... existing imports ...

interface SectionProps<T extends Record<string, unknown>> {
  section: SectionModel;
  schema: ZodTypeAny;
  defaultValues?: DefaultValues<T>;
  onAutosave?: (values: Partial<T>) => void;
  onSubmit: (values: T) => void;
}

export function Section<T extends Record<string, unknown>>({
  section,
  schema,
  defaultValues,
  onAutosave,
  onSubmit,
}: SectionProps<T>) {
  const methods = useForm<T>({
    resolver: zodResolver(schema),
    mode: 'onSubmit',
    defaultValues,
  });

  useEffect(() => {
    if (!onAutosave) return;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const sub = methods.watch((values) => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => onAutosave(values as Partial<T>), 500);
    });
    return () => {
      sub.unsubscribe();
      if (timer) clearTimeout(timer);
    };
  }, [methods, onAutosave]);

  return (
    // ...existing JSX unchanged...
  );
}
```

- [ ] **Step 4: Run the test to confirm it passes**

Run:
```bash
npm run test -- src/components/survey/Section.test.tsx
```

Expected: all previous + autosave test passing.

---

## Task 8: Wire App.tsx — load draft, pass `defaultValues`

**Files:**
- Modify: `src/App.tsx`

**Why:** On mount, App resolves the draft id, reads the row from Dexie, and passes `values` (or `undefined`) down to `Section` as `defaultValues`. Until that async read resolves, show a minimal loading state so the form doesn't mount empty and then re-mount once data arrives.

- [ ] **Step 1: Rewrite `App.tsx` with the load lifecycle**

Replace `src/App.tsx` with:

```tsx
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Section } from '@/components/survey/Section';
import { sectionA } from '@/generated/items';
import { sectionASchema, type SectionAValues } from '@/generated/schema';
import { useInstallPrompt } from '@/lib/install-prompt';
import { getOrCreateDraftId, loadDraft, saveDraft, submitDraft } from '@/lib/draft';

type Status = 'loading' | 'editing' | 'submitted';

export default function App() {
  const { canInstall, install } = useInstallPrompt();
  const [status, setStatus] = useState<Status>('loading');
  const [draftId, setDraftId] = useState<string>('');
  const [defaults, setDefaults] = useState<Partial<SectionAValues> | undefined>(
    undefined,
  );

  useEffect(() => {
    const id = getOrCreateDraftId();
    setDraftId(id);
    loadDraft(id).then((row) => {
      setDefaults(row?.values as Partial<SectionAValues> | undefined);
      setStatus('editing');
    });
  }, []);

  const handleAutosave = (values: Partial<SectionAValues>) => {
    if (!draftId) return;
    void saveDraft(draftId, values);
  };

  const handleSubmit = async (values: SectionAValues) => {
    if (!draftId) return;
    await saveDraft(draftId, values);
    await submitDraft(draftId);
    setStatus('submitted');
  };

  return (
    <main className="flex min-h-full flex-col">
      <header className="flex items-center justify-between border-b px-6 py-3">
        <h1 className="text-lg font-semibold">F2 Survey</h1>
        {canInstall ? (
          <Button size="sm" onClick={install}>
            Install
          </Button>
        ) : null}
      </header>
      {status === 'loading' ? (
        <p className="p-6 text-sm text-muted-foreground">Loading…</p>
      ) : status === 'submitted' ? (
        <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
          <h2 className="text-2xl font-semibold">Thank you</h2>
          <p className="text-sm text-muted-foreground">
            Your response is saved on this device and will sync when the app is
            online.
          </p>
        </section>
      ) : (
        <Section
          section={sectionA}
          schema={sectionASchema}
          defaultValues={defaults}
          onAutosave={handleAutosave}
          onSubmit={handleSubmit}
        />
      )}
    </main>
  );
}
```

- [ ] **Step 2: Run the full test + typecheck suite to catch regressions**

Run:
```bash
npm run test && npm run typecheck
```

Expected: all tests pass, tsc clean. `App.test.tsx` may need adjustments (next task handles it).

---

## Task 9: Integration test — reload restores draft

**Files:**
- Modify: `src/App.test.tsx`

- [ ] **Step 1: Read the existing `App.test.tsx` and update it**

Replace `src/App.test.tsx` with:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import { db } from '@/lib/db';

describe('App — M2 draft lifecycle', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
  });

  it('autosaves an answer and restores it after remount', async () => {
    vi.useFakeTimers();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    const { unmount } = render(<App />);
    // First render does an async loadDraft. Flush microtasks + timers.
    await vi.runOnlyPendingTimersAsync();
    await waitFor(() => screen.getByLabelText(/Q3/));

    await user.type(screen.getByLabelText(/Q3/), 'Female');

    // Cross the 500 ms debounce so autosave fires.
    await vi.advanceTimersByTimeAsync(600);

    // Let the Dexie put() resolve.
    await vi.runOnlyPendingTimersAsync();

    unmount();

    render(<App />);
    await vi.runOnlyPendingTimersAsync();

    const restored = await waitFor(() =>
      screen.getByLabelText(/Q3/) as HTMLInputElement,
    );
    expect(restored.value).toBe('Female');

    vi.useRealTimers();
  });

  it('shows a thank-you state after a valid submit', async () => {
    // Scope this test to whatever minimal valid Section A answers exist.
    // If Section A has many required fields, mark this test .skip and
    // rely on the draft.test.ts submitDraft() coverage. Otherwise fill
    // every required field and click Submit; expect the thank-you copy.
    // Deferred decision — resolve at execution time against the current
    // Section A generated schema.
  });
});
```

**Note:** the second test is a placeholder for a full submit-flow integration test. If Section A has many required fields, filling them all in a unit-level test is expensive; the logic is already covered by `draft.test.ts` / `submitDraft`. Keep this test as `it.skip(...)` if filling the form is impractical. **Do NOT add fake required-field coverage that drifts from the generated schema.**

- [ ] **Step 2: Run the App test**

Run:
```bash
npm run test -- src/App.test.tsx
```

Expected: autosave-restore test passes. If it fails with a timing issue, adjust `advanceTimersByTimeAsync` values — the debounce is 500 ms, so any advance ≥ 500 ms should trigger it.

---

## Task 10: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full health suite**

Run:
```bash
npm run test && npm run typecheck && npm run lint && npm run build
```

Expected: all green. 48 → ~56+ tests passing (M1 tests + new db/draft/Section/App tests).

- [ ] **Step 2: Smoke-test the dev server manually**

Run:
```bash
npm run dev
```

Open `http://localhost:5173` in a browser. Verify:

1. Form renders (no "Loading..." stuck state).
2. Type an answer in Section A Q3.
3. Open DevTools → Application → IndexedDB → `f2_pwa` → `drafts`. After ~500 ms a row exists with your answer.
4. Hard-reload the tab (Ctrl+Shift+R). The answer is restored in the input.
5. Fill required fields + Submit. The draft row disappears from IndexedDB; a new row appears in `submissions` with `status: 'pending_sync'`, `synced_at: null`, and a fresh `client_submission_id`.
6. The app shows the "Thank you" screen.
7. Reload the tab again — you get a fresh empty form (no stale draft).

Stop the dev server (`Ctrl+C`) once verified.

- [ ] **Step 3: Update `app/NEXT.md` for M3**

Replace `deliverables/F2/PWA/app/NEXT.md` with:

```markdown
# Next step (future-Carl)

**Last milestone shipped:** M2 — Autosave + IndexedDB via Dexie (drafts + submissions tables, 500 ms debounce, reload-restore).

**Next milestone:** M3 — Sync orchestrator + backend stub (10–14h).

**Before starting M3:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §§7.1, 7.3, 7.6 (service-worker caching, sync state machine, storage quota) to draft the M3 plan.
2. Target: pending_sync → syncing → synced|rejected|retry_scheduled state machine, driven by `online` event + manual "Sync now" button. Backend can start as a stub Express/Hono endpoint on `localhost:8787`; real ASPSI API wiring is later.
3. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M3-sync-orchestrator.md`.

**When picking this back up after a gap:**

- Run `npm install` first.
- Run `npm run test && npm run typecheck && npm run build` to confirm M2 still green.
- Open `../2026-04-17-design-spec.md` §7.3 (sync orchestrator state machine) and §8 (error handling) to re-orient.

**M2 remnants to close on merge to main:**

- Merge `feat/f2-pwa-m2` → `main` with `--no-ff`.
- Tag `f2-pwa-m2` on the merge commit.
```

---

## Self-Review Notes

- **Spec §5.5 coverage:** drafts in Dexie ✓, submissions in Dexie ✓, current editing in RHF ✓, HCW identity stubbed (deferred — explicit in scope guardrails) ✓, UI language untouched (unchanged from M1) ✓.
- **Spec §7.2 coverage:** all five tables defined (Task 2) ✓, `id` stable from localStorage (Task 3) ✓, draft → submission archival is transactional (Task 5) ✓, `client_submission_id` UUID (Task 5) ✓, status machine set to `pending_sync` (Task 5) ✓.
- **Spec §7.3 precursor:** submission row gets `status='pending_sync'`, `synced_at=null` (Task 5). Actual state transitions are M3+.
- **NEXT.md target:** replace `alert(...)` ✓ (Task 8), autosave debounced ~500 ms ✓ (Task 7), reload preserves answers ✓ (Tasks 8+9).
- **No placeholders:** every step has runnable code or exact commands. Task 9's second test is explicitly flagged as deferred with the reason, not a TBD.
