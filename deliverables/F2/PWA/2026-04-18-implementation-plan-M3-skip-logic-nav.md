# F2 PWA M3 — Skip Logic + Multi-Section Nav + Progress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render Sections A, B, C as a linear multi-section form with prev/next navigation, a progress indicator, and a minimal demonstrative set of intra-section skip-logic predicates. Draft autosave persists across section navigation; submit archives the merged answers as a single `submissions` row.

**Architecture:** One `<MultiSectionForm>` owns section index state and the cross-section merged draft. Each section still renders via the existing `<Section>` component (already RHF-backed), but Section gains an `items` override prop so the parent can filter its item list with skip predicates. Intra-section skip logic lives in a hand-authored `src/lib/skip-logic.ts` keyed by section id and item id — generator emission from `F2-Skip-Logic.md` is explicitly deferred (the source doc is a Google-Forms-shaped Mermaid graph, not a machine-readable routing table). `<Navigator>` (prev/next/submit) and `<ProgressBar>` (current of total + %) are new, thin presentational components.

**Tech Stack:** React 18, react-hook-form 7.72 (existing), Zod 3.25 (existing), Dexie 4 (existing), Tailwind (existing), Vitest 4 + @testing-library/react 16 (existing). **No new deps.**

**Source of truth:** `deliverables/F2/PWA/2026-04-17-design-spec.md` §§5.3 (pages/flow), 5.4 (domain components — `<Navigator>`, `<ProgressBar>`), 5.5 (state mgmt) and spec §11.1 M3 row ("3 sections with skip logic", 10–12h).

**Scope guardrails:**

- **Sections in M3**: A, B, C only (6 more sections exist in `items.ts` but are out of scope).
- **Skip logic in M3 = intra-section only.** No inter-section gating (role-bucket router, facility_type splits) — those depend on enrollment (M8).
- **Skip-logic predicates are hand-authored** in `src/lib/skip-logic.ts`. No generator extension in M3. The generator extension is a separate milestone when/if `F2-Skip-Logic.md` is rewritten as a routing table.
- **Navigation is linear** (prev/next only). Section jump list from spec §5.4 is deferred.
- **Per-section validation gate**: clicking Next runs that section's Zod schema; invalid → stay on section, show errors. Submit button appears in place of Next on the last section.
- **Draft shape**: flat `Record<string, unknown>` merged across sections (same as M2). No schema change needed.
- **Current section index** is ephemeral React state — **not** persisted to Dexie. Reload returns to Section A. Persisting nav position is explicitly deferred (low value vs. cost for M3).
- **No git commits in this plan** — user handles git manually.

**Demonstrative skip-logic predicates (exact list for M3):**

| Section | Item | Shows when |
|---|---|---|
| A | Q6 (specialty) | `Q5 ∈ {Administrator, Physician/Doctor, Physician assistant, Nurse, Midwife, Dentist}` |
| A | Q8 (practice mix) | `Q7 === 'Yes'` |
| B | Q14 (equipment specify) | `typeof Q13 === 'string' && Q13.startsWith('Yes')` |
| C | Q32 (why applied) | `Q30 === 'Yes'` |

These four predicates are enough to demo the pattern. Full F2 skip logic is deferred.

---

## File Structure

- **Create** `src/lib/skip-logic.ts` — `skipPredicates: Record<SectionId, Record<ItemId, (values) => boolean>>`.
- **Create** `src/lib/skip-logic.test.ts` — exercises all 4 predicates + the default-visible case.
- **Create** `src/components/survey/Navigator.tsx` — prev/next/submit buttons.
- **Create** `src/components/survey/Navigator.test.tsx`.
- **Create** `src/components/survey/ProgressBar.tsx` — current/total + % bar, aria-valuenow.
- **Create** `src/components/survey/ProgressBar.test.tsx`.
- **Create** `src/components/survey/MultiSectionForm.tsx` — orchestrates section index, merged draft, nav, progress.
- **Create** `src/components/survey/MultiSectionForm.test.tsx` — navigation + skip-logic + cross-section autosave.
- **Modify** `src/components/survey/Section.tsx` — accept optional `items` prop to override `section.items` (so parent can pre-filter by skip predicate). Keep backward compatibility (default to `section.items` when not passed).
- **Modify** `src/components/survey/Section.test.tsx` — add a test for the `items` override.
- **Modify** `src/App.tsx` — replace single-section `<Section>` with `<MultiSectionForm>`.
- **Modify** `src/App.test.tsx` — update to the multi-section flow (first section heading, nav to B, skip logic demo).

Files that change together live together: all survey UI stays in `components/survey/`. `skip-logic.ts` lives in `lib/` next to `db.ts` / `draft.ts` as pure logic.

---

## Task 1: Create `src/lib/skip-logic.ts` with the 4 M3 predicates

**Files:**
- Create: `src/lib/skip-logic.ts`
- Create: `src/lib/skip-logic.test.ts`

- [ ] **Step 1: Write failing tests**

Create `src/lib/skip-logic.test.ts`:

```ts
import { describe, it, expect } from 'vitest';
import { shouldShow } from './skip-logic';

describe('shouldShow', () => {
  it('returns true when no predicate is registered for the item', () => {
    expect(shouldShow('A', 'Q3', { Q5: 'Nurse' })).toBe(true);
  });

  describe('Section A', () => {
    it('hides Q6 when Q5 is not a role with specialty', () => {
      expect(shouldShow('A', 'Q6', { Q5: 'Pharmacist/Dispenser' })).toBe(false);
    });

    it('shows Q6 when Q5 is Physician/Doctor', () => {
      expect(shouldShow('A', 'Q6', { Q5: 'Physician/Doctor' })).toBe(true);
    });

    it('hides Q8 when Q7 is No', () => {
      expect(shouldShow('A', 'Q8', { Q7: 'No' })).toBe(false);
    });

    it('shows Q8 when Q7 is Yes', () => {
      expect(shouldShow('A', 'Q8', { Q7: 'Yes' })).toBe(true);
    });
  });

  describe('Section B', () => {
    it('hides Q14 when Q13 is a No variant', () => {
      expect(
        shouldShow('B', 'Q14', { Q13: 'No, and no plans in next 1–2 years' }),
      ).toBe(false);
    });

    it('shows Q14 when Q13 starts with Yes', () => {
      expect(
        shouldShow('B', 'Q14', { Q13: 'Yes, direct result of UHC Act' }),
      ).toBe(true);
    });

    it('hides Q14 when Q13 is unanswered', () => {
      expect(shouldShow('B', 'Q14', {})).toBe(false);
    });
  });

  describe('Section C', () => {
    it('hides Q32 when Q30 is not Yes', () => {
      expect(shouldShow('C', 'Q32', { Q30: 'No' })).toBe(false);
    });

    it('shows Q32 when Q30 is Yes', () => {
      expect(shouldShow('C', 'Q32', { Q30: 'Yes' })).toBe(true);
    });
  });
});
```

- [ ] **Step 2: Run to confirm failure**

Run:
```bash
npm run test -- src/lib/skip-logic.test.ts
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/lib/skip-logic.ts`**

Create `src/lib/skip-logic.ts`:

```ts
export type FormValues = Record<string, unknown>;
type Predicate = (values: FormValues) => boolean;

const ROLES_WITH_SPECIALTY = new Set([
  'Administrator',
  'Physician/Doctor',
  'Physician assistant',
  'Nurse',
  'Midwife',
  'Dentist',
]);

const predicates: Record<string, Record<string, Predicate>> = {
  A: {
    Q6: (v) => typeof v.Q5 === 'string' && ROLES_WITH_SPECIALTY.has(v.Q5),
    Q8: (v) => v.Q7 === 'Yes',
  },
  B: {
    Q14: (v) => typeof v.Q13 === 'string' && v.Q13.startsWith('Yes'),
  },
  C: {
    Q32: (v) => v.Q30 === 'Yes',
  },
};

export function shouldShow(
  sectionId: string,
  itemId: string,
  values: FormValues,
): boolean {
  const p = predicates[sectionId]?.[itemId];
  return p ? p(values) : true;
}
```

- [ ] **Step 4: Run to confirm pass**

Run:
```bash
npm run test -- src/lib/skip-logic.test.ts
```

Expected: 9/9 passing.

---

## Task 2: Extend `<Section>` to accept an `items` override

**Files:**
- Modify: `src/components/survey/Section.tsx`
- Modify: `src/components/survey/Section.test.tsx`

**Why:** Parent (`<MultiSectionForm>`) needs to feed in a filtered item list (skip-logic-applied). Keep the default behavior (`items = section.items`) so existing callers are unaffected.

- [ ] **Step 1: Add failing test**

Append to `src/components/survey/Section.test.tsx`:

```ts
it('renders only the items passed via the items override prop', () => {
  render(
    <Section
      section={fixture}
      schema={schema}
      items={[fixture.items[1]]}
      onSubmit={() => {}}
    />,
  );
  expect(screen.queryByLabelText(/sex at birth/)).toBeNull();
  expect(screen.getByLabelText(/Age\?/)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run to confirm failure**

Run:
```bash
npm run test -- src/components/survey/Section.test.tsx
```

Expected: FAIL — `items` prop does not exist on SectionProps.

- [ ] **Step 3: Add the optional `items` prop**

In `src/components/survey/Section.tsx`:

```tsx
import type { Item, Section as SectionModel } from '@/types/survey';

interface SectionProps<T extends Record<string, unknown>> {
  section: SectionModel;
  schema: ZodTypeAny;
  items?: Item[];
  defaultValues?: DefaultValues<T>;
  onAutosave?: (values: Partial<T>) => void;
  onSubmit: (values: T) => void;
}

export function Section<T extends Record<string, unknown>>({
  section,
  schema,
  items,
  defaultValues,
  onAutosave,
  onSubmit,
}: SectionProps<T>) {
  const methods = useForm<T>({
    resolver: zodResolver(schema),
    mode: 'onSubmit',
    ...(defaultValues ? { defaultValues } : {}),
  });

  // ... existing useEffect for onAutosave unchanged ...

  const itemsToRender = items ?? section.items;

  return (
    <FormProvider {...methods}>
      <form
        onSubmit={methods.handleSubmit((values) => onSubmit(values as unknown as T))}
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

        {itemsToRender.map((item) => (
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

- [ ] **Step 4: Run to confirm pass**

Run:
```bash
npm run test -- src/components/survey/Section.test.tsx
```

Expected: all previous + new items-override test passing.

---

## Task 3: Create `<ProgressBar>`

**Files:**
- Create: `src/components/survey/ProgressBar.tsx`
- Create: `src/components/survey/ProgressBar.test.tsx`

- [ ] **Step 1: Write failing test**

Create `src/components/survey/ProgressBar.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgressBar } from './ProgressBar';

describe('<ProgressBar>', () => {
  it('renders the current / total label', () => {
    render(<ProgressBar current={2} total={3} />);
    expect(screen.getByText(/Section 2 of 3/)).toBeInTheDocument();
  });

  it('exposes aria-valuenow as a percent', () => {
    render(<ProgressBar current={2} total={3} />);
    const bar = screen.getByRole('progressbar');
    // 2/3 = 66 (rounded).
    expect(bar).toHaveAttribute('aria-valuenow', '66');
    expect(bar).toHaveAttribute('aria-valuemin', '0');
    expect(bar).toHaveAttribute('aria-valuemax', '100');
  });

  it('caps at 100% when current === total', () => {
    render(<ProgressBar current={3} total={3} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute(
      'aria-valuenow',
      '100',
    );
  });
});
```

- [ ] **Step 2: Run to confirm failure**

Run:
```bash
npm run test -- src/components/survey/ProgressBar.test.tsx
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `ProgressBar`**

Create `src/components/survey/ProgressBar.tsx`:

```tsx
interface ProgressBarProps {
  current: number;
  total: number;
}

export function ProgressBar({ current, total }: ProgressBarProps) {
  const percent = Math.min(100, Math.round((current / total) * 100));
  return (
    <div className="flex flex-col gap-1 px-6 pt-3">
      <p className="text-xs text-muted-foreground">
        Section {current} of {total}
      </p>
      <div
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-2 w-full overflow-hidden rounded bg-muted"
      >
        <div
          className="h-full bg-primary transition-all"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run to confirm pass**

Run:
```bash
npm run test -- src/components/survey/ProgressBar.test.tsx
```

Expected: 3/3 passing.

---

## Task 4: Create `<Navigator>`

**Files:**
- Create: `src/components/survey/Navigator.tsx`
- Create: `src/components/survey/Navigator.test.tsx`

**Contract:** Three buttons — `Previous`, `Next`, `Submit`. Previous disabled on first section. Next and Submit are mutually exclusive (Submit replaces Next on the last section). Navigator fires `onPrev` / `onNext` / `onSubmit` callbacks; the parent wires these to form validation + state updates.

- [ ] **Step 1: Write failing test**

Create `src/components/survey/Navigator.test.tsx`:

```tsx
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Navigator } from './Navigator';

describe('<Navigator>', () => {
  it('disables Previous on the first section', () => {
    render(
      <Navigator
        isFirst
        isLast={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled();
  });

  it('renders Next (not Submit) on a middle section', () => {
    render(
      <Navigator
        isFirst={false}
        isLast={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /submit/i })).toBeNull();
  });

  it('renders Submit (not Next) on the last section', () => {
    render(
      <Navigator
        isFirst={false}
        isLast
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /next/i })).toBeNull();
  });

  it('calls onPrev / onNext / onSubmit when the respective buttons are clicked', async () => {
    const user = userEvent.setup();
    const onPrev = vi.fn();
    const onNext = vi.fn();
    const onSubmit = vi.fn();

    const { rerender } = render(
      <Navigator
        isFirst={false}
        isLast={false}
        onPrev={onPrev}
        onNext={onNext}
        onSubmit={onSubmit}
      />,
    );
    await user.click(screen.getByRole('button', { name: /previous/i }));
    await user.click(screen.getByRole('button', { name: /next/i }));

    rerender(
      <Navigator
        isFirst={false}
        isLast
        onPrev={onPrev}
        onNext={onNext}
        onSubmit={onSubmit}
      />,
    );
    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(onPrev).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: Run to confirm failure**

Run:
```bash
npm run test -- src/components/survey/Navigator.test.tsx
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `Navigator`**

Create `src/components/survey/Navigator.tsx`:

```tsx
import { Button } from '@/components/ui/button';

interface NavigatorProps {
  isFirst: boolean;
  isLast: boolean;
  onPrev: () => void;
  onNext: () => void;
  onSubmit: () => void;
}

export function Navigator({
  isFirst,
  isLast,
  onPrev,
  onNext,
  onSubmit,
}: NavigatorProps) {
  return (
    <div className="flex items-center justify-between gap-3 pt-4">
      <Button
        type="button"
        variant="outline"
        onClick={onPrev}
        disabled={isFirst}
      >
        Previous
      </Button>
      {isLast ? (
        <Button type="button" onClick={onSubmit}>
          Submit
        </Button>
      ) : (
        <Button type="button" onClick={onNext}>
          Next
        </Button>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run to confirm pass**

Run:
```bash
npm run test -- src/components/survey/Navigator.test.tsx
```

Expected: 4/4 passing.

---

## Task 5: Create `<MultiSectionForm>` — the orchestrator

**Files:**
- Create: `src/components/survey/MultiSectionForm.tsx`
- Create: `src/components/survey/MultiSectionForm.test.tsx`

**Responsibilities:**
1. Holds `currentIndex` state (0 for Section A, 1 for B, 2 for C).
2. Holds `merged` values across sections (flat `Record<string, unknown>`).
3. Per section, passes `defaultValues={merged}` down to `<Section>` (RHF will pick the keys relevant to its schema).
4. Filters items via `shouldShow(sectionId, itemId, merged)` before passing to `<Section>`.
5. On each section's `onAutosave`, merges section values into `merged` and forwards to parent's `onAutosave` callback.
6. On each section's `onSubmit` (triggered internally by Next validation), advances index.
7. On the last section's Submit, calls parent's `onSubmit(merged)`.

**Implementation note:** Each section uses its own `<Section>` component with its own RHF instance. To trigger validation from a Navigator button (which lives outside `<form>`), we render the Navigator **inside** `<MultiSectionForm>` but rely on Section's existing submit-button flow. The simplest implementation: hide Section's internal Submit button on non-last sections and render the Navigator's Next button to dispatch the form's submit event via a `ref`. Alternative simpler approach: Navigator Next clicks cause a synthetic click of the Section's Submit button (which is already validation-gated via `handleSubmit`). We'll use the synthetic-click approach — it's ugly but small.

Actually the cleanest approach: give `<Section>` a `hideSubmit` prop so the Navigator can be the sole visible button, and expose a `submitRef` prop (a `MutableRefObject<() => void>`) that `<Section>` populates with its internal submit handler. Parent calls `submitRef.current()` to trigger RHF validation from outside.

- [ ] **Step 1: Extend `<Section>` with `hideSubmit` + `submitRef`**

Modify `src/components/survey/Section.tsx`:

```tsx
import { useEffect, type MutableRefObject } from 'react';

interface SectionProps<T extends Record<string, unknown>> {
  section: SectionModel;
  schema: ZodTypeAny;
  items?: Item[];
  defaultValues?: DefaultValues<T>;
  hideSubmit?: boolean;
  submitRef?: MutableRefObject<(() => void) | null>;
  onAutosave?: (values: Partial<T>) => void;
  onSubmit: (values: T) => void;
}

export function Section<T extends Record<string, unknown>>({
  section,
  schema,
  items,
  defaultValues,
  hideSubmit,
  submitRef,
  onAutosave,
  onSubmit,
}: SectionProps<T>) {
  const methods = useForm<T>({
    resolver: zodResolver(schema),
    mode: 'onSubmit',
    ...(defaultValues ? { defaultValues } : {}),
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

  const submit = methods.handleSubmit((values) =>
    onSubmit(values as unknown as T),
  );

  useEffect(() => {
    if (!submitRef) return;
    submitRef.current = () => {
      void submit();
    };
    return () => {
      submitRef.current = null;
    };
  }, [submitRef, submit]);

  const itemsToRender = items ?? section.items;

  return (
    <FormProvider {...methods}>
      <form onSubmit={submit} className="mx-auto flex max-w-xl flex-col gap-4 p-6" noValidate>
        <header className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold tracking-tight">
            Section {section.id} — {section.title}
          </h2>
          {section.preamble ? (
            <p className="text-sm text-muted-foreground">{section.preamble}</p>
          ) : null}
        </header>

        {itemsToRender.map((item) => (
          <Question key={item.id} item={item} />
        ))}

        {!hideSubmit ? (
          <div className="pt-4">
            <Button type="submit">Submit</Button>
          </div>
        ) : null}
      </form>
    </FormProvider>
  );
}
```

- [ ] **Step 2: Add failing `<MultiSectionForm>` test**

Create `src/components/survey/MultiSectionForm.test.tsx`:

```tsx
import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MultiSectionForm } from './MultiSectionForm';

describe('<MultiSectionForm>', () => {
  it('starts on Section A and shows the correct progress', () => {
    render(
      <MultiSectionForm
        initialValues={{}}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(
      screen.getByRole('heading', { name: /Section A — Healthcare Worker Profile/ }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Section 1 of 3/)).toBeInTheDocument();
  });

  it('blocks Next when Section A validation fails and advances when it passes', async () => {
    const user = userEvent.setup();
    render(
      <MultiSectionForm
        initialValues={{}}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    await user.click(screen.getByRole('button', { name: /next/i }));
    // Validation errors are displayed; still on Section A.
    expect(
      screen.getByRole('heading', { name: /Section A/ }),
    ).toBeInTheDocument();

    // Fill every required Section A field.
    await user.click(screen.getByLabelText('Regular'));      // Q2
    await user.click(screen.getByLabelText('Female'));       // Q3
    await user.type(screen.getByLabelText(/How old are you/), '30');  // Q4
    await user.click(screen.getByLabelText('Nurse'));        // Q5
    await user.click(screen.getByLabelText('No'));           // Q7
    await user.type(screen.getByLabelText(/days in a week/), '5');    // Q10
    await user.type(screen.getByLabelText(/hours do you work/), '8'); // Q11

    await user.click(screen.getByRole('button', { name: /next/i }));
    await waitFor(() =>
      expect(
        screen.getByRole('heading', { name: /Section B/ }),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText(/Section 2 of 3/)).toBeInTheDocument();
  });

  it('applies intra-section skip logic — Q8 hides when Q7 = No', async () => {
    const user = userEvent.setup();
    render(
      <MultiSectionForm
        initialValues={{}}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    // Before Q7 is answered, Q8 is hidden.
    expect(screen.queryByLabelText(/divide your time/)).toBeNull();
    await user.click(screen.getByLabelText('Yes'));  // Q7 = Yes (first Yes on page is Q7)
    // Q8 appears.
    await waitFor(() =>
      expect(screen.getByLabelText(/divide your time/)).toBeInTheDocument(),
    );
  });

  it('restores merged values when navigating back', async () => {
    const user = userEvent.setup();
    render(
      <MultiSectionForm
        initialValues={{
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q5: 'Nurse',
          Q7: 'No',
          Q10: 5,
          Q11: 8,
        }}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    await user.click(screen.getByRole('button', { name: /next/i }));
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /Section B/ })).toBeInTheDocument(),
    );
    await user.click(screen.getByRole('button', { name: /previous/i }));
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /Section A/ })).toBeInTheDocument(),
    );
    expect(screen.getByLabelText('Female')).toBeChecked();
  });
});
```

- [ ] **Step 3: Run to confirm failure**

Run:
```bash
npm run test -- src/components/survey/MultiSectionForm.test.tsx
```

Expected: FAIL — module not found.

- [ ] **Step 4: Implement `<MultiSectionForm>`**

Create `src/components/survey/MultiSectionForm.tsx`:

```tsx
import { useMemo, useRef, useState } from 'react';
import type { ZodTypeAny } from 'zod';
import type { Section as SectionModel, Item } from '@/types/survey';
import {
  sectionA,
  sectionB,
  sectionC,
} from '@/generated/items';
import {
  sectionASchema,
  sectionBSchema,
  sectionCSchema,
} from '@/generated/schema';
import { Section } from './Section';
import { Navigator } from './Navigator';
import { ProgressBar } from './ProgressBar';
import { shouldShow, type FormValues } from '@/lib/skip-logic';

type SectionConfig = {
  id: 'A' | 'B' | 'C';
  section: SectionModel;
  schema: ZodTypeAny;
};

const SECTIONS: SectionConfig[] = [
  { id: 'A', section: sectionA, schema: sectionASchema },
  { id: 'B', section: sectionB, schema: sectionBSchema },
  { id: 'C', section: sectionC, schema: sectionCSchema },
];

interface MultiSectionFormProps {
  initialValues: FormValues;
  onAutosave: (values: FormValues) => void;
  onSubmit: (values: FormValues) => void;
}

export function MultiSectionForm({
  initialValues,
  onAutosave,
  onSubmit,
}: MultiSectionFormProps) {
  const [index, setIndex] = useState(0);
  const [merged, setMerged] = useState<FormValues>(initialValues);
  const submitRef = useRef<(() => void) | null>(null);

  const current = SECTIONS[index];
  const isFirst = index === 0;
  const isLast = index === SECTIONS.length - 1;

  const visibleItems: Item[] = useMemo(
    () =>
      current.section.items.filter((it) =>
        shouldShow(current.id, it.id, merged),
      ),
    [current, merged],
  );

  const handleSectionAutosave = (values: Partial<FormValues>) => {
    const next = { ...merged, ...values };
    setMerged(next);
    onAutosave(next);
  };

  const handleSectionValid = (values: FormValues) => {
    const next = { ...merged, ...values };
    setMerged(next);
    if (isLast) {
      onSubmit(next);
    } else {
      setIndex(index + 1);
    }
  };

  return (
    <div className="flex flex-col">
      <ProgressBar current={index + 1} total={SECTIONS.length} />
      <Section
        key={current.id}
        section={current.section}
        schema={current.schema}
        items={visibleItems}
        defaultValues={merged}
        hideSubmit
        submitRef={submitRef}
        onAutosave={handleSectionAutosave}
        onSubmit={handleSectionValid}
      />
      <div className="mx-auto w-full max-w-xl px-6 pb-6">
        <Navigator
          isFirst={isFirst}
          isLast={isLast}
          onPrev={() => setIndex(Math.max(0, index - 1))}
          onNext={() => submitRef.current?.()}
          onSubmit={() => submitRef.current?.()}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Run to confirm pass**

Run:
```bash
npm run test -- src/components/survey/MultiSectionForm.test.tsx
```

Expected: 4/4 passing.

**Note on test fragility:** the skip-logic test uses `screen.getByLabelText('Yes')` and expects that to match Q7's "Yes". Section A has other Yes/No questions (Q7 is the only one rendered before Q10/Q11 though — Q2, Q3, Q5 are non-Yes/No). If `getByLabelText('Yes')` finds multiple matches, switch to `getAllByLabelText('Yes')[0]` or scope the query by the question's enclosing fieldset.

---

## Task 6: Wire `<App>` to use `<MultiSectionForm>`

**Files:**
- Modify: `src/App.tsx`

- [ ] **Step 1: Replace the Section call with MultiSectionForm**

Replace `src/App.tsx`:

```tsx
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { MultiSectionForm } from '@/components/survey/MultiSectionForm';
import { useInstallPrompt } from '@/lib/install-prompt';
import { getOrCreateDraftId, loadDraft, saveDraft, submitDraft } from '@/lib/draft';
import type { FormValues } from '@/lib/skip-logic';

type Status = 'loading' | 'editing' | 'submitted';

export default function App() {
  const { canInstall, install } = useInstallPrompt();
  const [status, setStatus] = useState<Status>('loading');
  const [draftId, setDraftId] = useState<string>('');
  const [initialValues, setInitialValues] = useState<FormValues>({});

  useEffect(() => {
    const id = getOrCreateDraftId();
    setDraftId(id);
    loadDraft(id).then((row) => {
      setInitialValues((row?.values as FormValues | undefined) ?? {});
      setStatus('editing');
    });
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

- [ ] **Step 2: Update `src/App.test.tsx` for the new shape**

Replace the 3 tests in `src/App.test.tsx` with:

```tsx
import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import { db } from '@/lib/db';

describe('<App>', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
  });

  it('lands on Section A after initial load', async () => {
    render(<App />);
    expect(
      await screen.findByRole('heading', { name: /Section A/ }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Section 1 of 3/)).toBeInTheDocument();
  });

  it('autosaves a Section A answer and restores it after remount', async () => {
    const user = userEvent.setup();
    const first = render(<App />);
    await screen.findByLabelText(/What is your sex at birth/);
    await user.click(screen.getByLabelText('Female'));

    await waitFor(
      async () => {
        const id = localStorage.getItem('f2_current_draft_id');
        expect(id).toBeTruthy();
        const row = await db.drafts.get(id!);
        expect(row?.values).toMatchObject({ Q3: 'Female' });
      },
      { timeout: 2000 },
    );

    first.unmount();
    render(<App />);
    await waitFor(() => expect(screen.getByLabelText('Female')).toBeChecked());
  });
});
```

- [ ] **Step 3: Run full App + MultiSectionForm tests**

Run:
```bash
npm run test -- src/App.test.tsx src/components/survey/MultiSectionForm.test.tsx
```

Expected: all passing.

---

## Task 7: Final verification

- [ ] **Step 1: Full health suite**

Run:
```bash
npm run test && npm run typecheck && npm run lint && npm run build
```

Expected: all green. Test count should grow from 61 → ~80 (lib/skip-logic: 9, Navigator: 4, ProgressBar: 3, MultiSectionForm: 4, Section: +1 items override, App: -1 then +2 = net +1).

- [ ] **Step 2: Browser smoke test**

Run:
```bash
npm run dev
```

Open `http://localhost:5173` and verify (each step in order):

1. Loads to Section A, progress reads "Section 1 of 3", ~33% bar.
2. Click Next with nothing filled → inline "This field is required." messages appear under every required field. Still on Section A.
3. Fill every required Section A field (Q2, Q3, Q4 ≥ 18, Q5, Q7, Q10 1–7, Q11 1–24). Q6 appears only after selecting a Q5 role with specialty (Nurse/Doctor/etc.); Q8 appears only after selecting Q7 = Yes.
4. Click Next → advances to Section B. Progress reads "Section 2 of 3", ~66% bar.
5. Click Previous → back on Section A, all answers preserved.
6. Advance to B again. Fill Q12 = Yes, Q13 = any "Yes, direct result…" → Q14 (equipment specify) appears.
7. Fill Section B required fields. Next → Section C. Progress reads "Section 3 of 3", 100% bar.
8. On Section C: answer Q30 = Yes → Q32 (why applied) appears.
9. Fill Section C required fields. The Next button is now **Submit**. Click → "Thank you" screen.
10. DevTools → IndexedDB → `f2_pwa` → `submissions`: one row with `status: pending_sync`, `values` containing Q2/Q3/Q4/…/Q30/… across all 3 sections. `drafts` is empty. `localStorage['f2_current_draft_id']` is gone.
11. Reload — back to empty Section A (fresh draft).

Stop dev server once verified.

- [ ] **Step 3: Update `NEXT.md` for M4**

Replace `deliverables/F2/PWA/app/NEXT.md` with:

```markdown
# Next step (future-Carl)

**Last milestone shipped:** M3 — Skip logic + multi-section nav + progress (3 sections A/B/C, hand-authored intra-section skip predicates, prev/next navigation, progress indicator, cross-section autosave).

**Next milestone:** M4 — Apps Script backend (endpoints, Sheet, HMAC). 12–15h per spec §11.1.

**Before starting M4:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §4 (Backend Design) — specifically 4.1 Sheet tabs, 4.2 endpoints, 4.3 security model, 4.4 data flow, 4.5 idempotency.
2. Target: deployable Apps Script Web App with routes `submit`, `batch-submit`, `facilities`, `config`, `spec-hash`, `audit`; Sheet tabs per §4.1; HMAC verification with rotating secret in ScriptProperties.
3. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M4-apps-script-backend.md`.
4. Ships per spec §11.1: "Backend live, curl-testable."

**M3 technical debt to address in later milestones:**

- Skip-logic predicates are hand-authored in `src/lib/skip-logic.ts`. Machine-generation from `F2-Skip-Logic.md` is deferred until that doc is rewritten as a routing table (candidate for M6 alongside full-instrument scaffolding).
- Section-level (inter-section) gating — role-bucket router from Q5, facility_type splits — is out of scope here; enabled once M8 (facility list + enrollment) lands.
- Navigation position is not persisted across reload. Resume-where-you-left-off would go in M11 (hardening) or earlier if UX testing surfaces pain.

**When picking this back up after a gap:**

- Run `npm install` first.
- Run `npm run test && npm run typecheck && npm run build` to confirm M3 still green.
- Open `../2026-04-17-design-spec.md` §4 to re-orient.

**M3 remnants to close on merge to main:**

- Merge `feat/f2-pwa-m3` → `main` with `--no-ff`.
- Tag `f2-pwa-m3` on the merge commit.
```

---

## Self-Review Notes

- **Spec §11.1 M3 row coverage:** skip logic ✓ (intra-section, 4 predicates), multi-section nav ✓ (prev/next), progress ✓ (section of total + %). Ships "3 sections with skip logic" — A/B/C linear.
- **Spec §5.3 user flow:** Fill page covered. Home/Review/Sync pages remain out of scope per milestone ordering (Home/Review in M8, Sync in M5).
- **Spec §5.4 domain components:** `<Navigator>` ✓, `<ProgressBar>` ✓. Jump list explicitly deferred. `<SyncBadge>` is M5. `<InstallPrompt>` already exists.
- **Spec §5.5 state:** editing values in RHF per section ✓, merged draft in Dexie via parent ✓, navigation state in React state (ephemeral by design for M3) ✓.
- **No placeholders:** every step has runnable code. Task 5 Step 5 includes an explicit note about the `getByLabelText('Yes')` potential ambiguity with remediation guidance.
- **Test-first discipline preserved:** every code task is preceded by a failing test that exercises the behavior being built.
- **Backward compatibility:** `<Section>` gains optional props (`items`, `hideSubmit`, `submitRef`) — existing M1/M2 callers work unchanged if any external callers exist (none do, but it's a clean interface).
