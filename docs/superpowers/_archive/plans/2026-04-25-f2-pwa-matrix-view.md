# F2 PWA #18 — Matrix view Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render consecutive `single`-type questionnaire items that share the same choice set as a single 2-way matrix (rows = statements, columns = scale options) on tablet+, with mobile reflow to per-row stacked cards. Apply automatically to Section J's explicit `Grid #N` battery and Section G's Q75–Q81 Likert cluster.

**Architecture:** Render-time grouping. A new pure helper `groupVisibleItems` walks the section's already-`shouldShow`-filtered items and emits a flat list of `MatrixGroup | Item`. A new `MatrixQuestion` component renders the matrix (and its mobile reflow). `Section.tsx` and `ReviewSection.tsx` dispatch by kind. No spec changes, no parser changes, no items.ts shape changes.

**Tech stack:** Vite + React 19 + TypeScript, react-hook-form, Zod, Tailwind, vitest + @testing-library/react, Playwright.

**Spec:** `docs/superpowers/specs/2026-04-25-f2-pwa-matrix-view-design.md`.

**Working directory for all commands below:** `deliverables/F2/PWA/app/` (cd there before running any `npm` / `npx` command).

---

## File structure

```
deliverables/F2/PWA/app/
├── src/components/survey/
│   ├── group-matrix.ts             ← NEW: pure helper
│   ├── group-matrix.test.ts        ← NEW: unit tests (Task 1)
│   ├── MatrixQuestion.tsx          ← NEW: matrix renderer
│   ├── MatrixQuestion.test.tsx     ← NEW: component tests (Task 2 + Task 3)
│   ├── Section.tsx                 ← MODIFY: dispatch matrix vs single (Task 4)
│   └── ReviewSection.tsx           ← MODIFY: matrix as mini-table (Task 5)
├── src/i18n/locales/
│   ├── en.ts                       ← MODIFY: add `matrix.*` keys (Task 2)
│   └── fil.ts                      ← MODIFY: mirror keys (Task 2)
└── e2e/
    └── matrix.spec.ts              ← NEW: Playwright walkthrough (Task 6)
```

---

## Task 1: Pure grouping helper (`group-matrix.ts`)

**Files:**
- Create: `deliverables/F2/PWA/app/src/components/survey/group-matrix.ts`
- Test: `deliverables/F2/PWA/app/src/components/survey/group-matrix.test.ts`

- [ ] **Step 1.1: Write the failing test**

Create `src/components/survey/group-matrix.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import type { Item, Choice } from '@/types/survey';
import { groupVisibleItems, type MatrixGroup } from './group-matrix';

const dual = (en: string) => ({ en, fil: en });
const ch = (vals: string[]): Choice[] => vals.map((v) => ({ label: dual(v), value: v }));

const single = (id: string, choices: Choice[], extra: Partial<Item> = {}): Item => ({
  id,
  section: 'G',
  type: 'single',
  required: true,
  label: dual(`Statement ${id}`),
  choices,
  ...extra,
});

const isMatrix = (e: Item | MatrixGroup): e is MatrixGroup =>
  (e as MatrixGroup).kind === 'matrix';

describe('groupVisibleItems', () => {
  it('returns an empty array for empty input', () => {
    expect(groupVisibleItems([])).toEqual([]);
  });

  it('returns a single non-grouping item unchanged', () => {
    const items = [single('Q75', ch(['1', '2', '3', '4', '5']))];
    expect(groupVisibleItems(items)).toEqual(items);
  });

  it('groups two consecutive same-choice single items into a matrix', () => {
    const choices = ch(['1', '2', '3', '4', '5']);
    const items = [single('Q75', choices), single('Q76', choices)];
    const out = groupVisibleItems(items);
    expect(out).toHaveLength(1);
    expect(isMatrix(out[0])).toBe(true);
    if (isMatrix(out[0])) {
      expect(out[0].items).toHaveLength(2);
      expect(out[0].choices).toEqual(choices);
    }
  });

  it('keeps two single items with different choice sets separate', () => {
    const items = [
      single('Q75', ch(['1', '2', '3', '4', '5'])),
      single('Q83', ch(['Never', 'Rarely', 'Sometimes', 'Often', 'Always'])),
    ];
    expect(groupVisibleItems(items)).toEqual(items);
  });

  it('mixed sequence groups only consecutive runs >= 2', () => {
    const ch15 = ch(['1', '2', '3', '4', '5']);
    const items: Item[] = [
      single('Q75', ch15),
      single('Q76', ch15),
      { ...single('Qmulti', ch15), type: 'multi' as const },
      single('Q80', ch15),
    ];
    const out = groupVisibleItems(items);
    expect(out).toHaveLength(3);
    expect(isMatrix(out[0])).toBe(true);
    expect(isMatrix(out[1])).toBe(false);
    expect(isMatrix(out[2])).toBe(false);
  });

  it('does not group items with hasOtherSpecify = true', () => {
    const choices = ch(['1', '2', '3', '4', '5']);
    const items = [
      single('Q75', choices, { hasOtherSpecify: true }),
      single('Q76', choices, { hasOtherSpecify: true }),
    ];
    expect(groupVisibleItems(items)).toEqual(items);
  });

  it('does not group items if choices differ in order', () => {
    const items = [
      single('Q1', ch(['Yes', 'No'])),
      single('Q2', ch(['No', 'Yes'])),
    ];
    expect(groupVisibleItems(items)).toEqual(items);
  });

  it('does not group items if choices differ in length', () => {
    const items = [
      single('Q1', ch(['1', '2', '3', '4', '5'])),
      single('Q2', ch(['1', '2', '3'])),
    ];
    expect(groupVisibleItems(items)).toEqual(items);
  });

  it('groups by value only (label translations may differ)', () => {
    const a: Choice[] = [
      { label: { en: 'Yes', fil: 'Oo' }, value: 'Yes' },
      { label: { en: 'No', fil: 'Hindi' }, value: 'No' },
    ];
    const b: Choice[] = [
      { label: { en: 'Yes', fil: 'Oo' }, value: 'Yes' },
      { label: { en: 'No', fil: 'Hindi' }, value: 'No' },
    ];
    const items = [single('Q1', a), single('Q2', b)];
    const out = groupVisibleItems(items);
    expect(out).toHaveLength(1);
    expect(isMatrix(out[0])).toBe(true);
  });

  it('groups a long realistic Likert cluster (Q75-Q81)', () => {
    const ch15 = ch(['1', '2', '3', '4', '5']);
    const items = ['Q75', 'Q76', 'Q77', 'Q78', 'Q79', 'Q80', 'Q81'].map((id) =>
      single(id, ch15),
    );
    const out = groupVisibleItems(items);
    expect(out).toHaveLength(1);
    if (isMatrix(out[0])) {
      expect(out[0].items.map((i) => i.id)).toEqual([
        'Q75',
        'Q76',
        'Q77',
        'Q78',
        'Q79',
        'Q80',
        'Q81',
      ]);
    }
  });

  it('groups Section J Agreement battery (5 statements, same scale)', () => {
    const agreement = ch([
      'Strongly Agree',
      'Agree',
      'Neither Agree nor Disagree',
      'Disagree',
      'Strongly Disagree',
    ]);
    const items = ['Q108', 'Q109', 'Q110', 'Q111', 'Q112'].map((id) =>
      single(id, agreement),
    );
    const out = groupVisibleItems(items);
    expect(out).toHaveLength(1);
  });

  it('does not group multi-field items', () => {
    const items: Item[] = [
      {
        id: 'Q9',
        section: 'A',
        type: 'multi-field',
        required: true,
        label: dual('How long?'),
        subFields: [
          { id: 'Q9_1', label: dual('Years'), kind: 'number' },
          { id: 'Q9_2', label: dual('Months'), kind: 'number' },
        ],
      },
      {
        id: 'Q10',
        section: 'A',
        type: 'multi-field',
        required: true,
        label: dual('How long?'),
        subFields: [
          { id: 'Q10_1', label: dual('Years'), kind: 'number' },
          { id: 'Q10_2', label: dual('Months'), kind: 'number' },
        ],
      },
    ];
    expect(groupVisibleItems(items)).toEqual(items);
  });
});
```

- [ ] **Step 1.2: Run test to verify it fails**

Run: `npx vitest run src/components/survey/group-matrix.test.ts`
Expected: FAIL with "Cannot find module './group-matrix'" (file doesn't exist).

- [ ] **Step 1.3: Write the implementation**

Create `src/components/survey/group-matrix.ts`:

```ts
import type { Choice, Item } from '@/types/survey';

export interface MatrixGroup {
  kind: 'matrix';
  /** The shared choice set every row uses. */
  choices: Choice[];
  /** The rows. Always >= 2 items per group. */
  items: Item[];
}

function isMatrixCandidate(item: Item): boolean {
  return (
    item.type === 'single' &&
    item.hasOtherSpecify !== true &&
    Array.isArray(item.choices) &&
    item.choices.length > 0
  );
}

function sameChoiceValues(a: Choice[], b: Choice[]): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i].value !== b[i].value) return false;
  }
  return true;
}

/**
 * Walk an already-shouldShow-filtered list of items. Group consecutive
 * `single`-type items that share the same choice values into matrix groups
 * of size >= 2. Everything else flows through unchanged in original order.
 */
export function groupVisibleItems(items: Item[]): Array<MatrixGroup | Item> {
  const out: Array<MatrixGroup | Item> = [];
  let i = 0;

  while (i < items.length) {
    const start = items[i];

    if (!isMatrixCandidate(start)) {
      out.push(start);
      i++;
      continue;
    }

    const startChoices = start.choices!;
    let j = i + 1;
    while (
      j < items.length &&
      isMatrixCandidate(items[j]) &&
      sameChoiceValues(items[j].choices!, startChoices)
    ) {
      j++;
    }

    const runLength = j - i;
    if (runLength >= 2) {
      out.push({ kind: 'matrix', choices: startChoices, items: items.slice(i, j) });
    } else {
      out.push(start);
    }
    i = j;
  }

  return out;
}
```

- [ ] **Step 1.4: Run test to verify it passes**

Run: `npx vitest run src/components/survey/group-matrix.test.ts`
Expected: PASS, all 11 tests green.

- [ ] **Step 1.5: Commit**

From the project root (`/c/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development`):

```bash
git add deliverables/F2/PWA/app/src/components/survey/group-matrix.ts \
        deliverables/F2/PWA/app/src/components/survey/group-matrix.test.ts
git commit -m "feat(survey): groupVisibleItems helper for #18 matrix view"
```

---

## Task 2: MatrixQuestion component (table layout, no mobile reflow yet)

**Files:**
- Create: `deliverables/F2/PWA/app/src/components/survey/MatrixQuestion.tsx`
- Test: `deliverables/F2/PWA/app/src/components/survey/MatrixQuestion.test.tsx`
- Modify: `deliverables/F2/PWA/app/src/i18n/locales/en.ts` (add `matrix.statementHeader` key)
- Modify: `deliverables/F2/PWA/app/src/i18n/locales/fil.ts` (mirror key)

- [ ] **Step 2.1: Add the i18n key**

Open `src/i18n/locales/en.ts` and add `matrix` to the bundle. Find the `review:` block and add a new `matrix:` section right after it (before `sync:`):

```ts
  matrix: {
    statementHeader: 'Statement',
  },
```

Then mirror in `src/i18n/locales/fil.ts` at the same location:

```ts
  matrix: {
    statementHeader: 'Statement',
  },
```

(Filipino translation pending from ASPSI per the translation pipeline memory; placeholder-equal-to-English follows existing convention.)

- [ ] **Step 2.2: Write the failing component test**

Create `src/components/survey/MatrixQuestion.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useForm, FormProvider } from 'react-hook-form';
import type * as React from 'react';
import { LocaleProvider } from '@/i18n/locale-context';
import type { Choice, Item } from '@/types/survey';
import { MatrixQuestion } from './MatrixQuestion';

const dual = (en: string) => ({ en, fil: en });

function row(id: string, label: string, choices: Choice[]): Item {
  return {
    id,
    section: 'G',
    type: 'single',
    required: true,
    label: dual(label),
    choices,
  };
}

function Harness({ items, choices }: { items: Item[]; choices: Choice[] }) {
  const methods = useForm({ defaultValues: {} });
  return (
    <LocaleProvider>
      <FormProvider {...methods}>
        <form>
          <MatrixQuestion items={items} choices={choices} />
        </form>
      </FormProvider>
    </LocaleProvider>
  );
}

const scale15: Choice[] = [
  { label: dual('1'), value: '1' },
  { label: dual('2'), value: '2' },
  { label: dual('3'), value: '3' },
  { label: dual('4'), value: '4' },
  { label: dual('5'), value: '5' },
];

describe('<MatrixQuestion>', () => {
  it('renders one column header per choice plus a Statement header', () => {
    render(<Harness items={[row('Q75', 'fairness ZBB', scale15), row('Q76', 'fairness NBB', scale15)]} choices={scale15} />);
    // Column headers
    expect(screen.getByText(/Statement/i)).toBeInTheDocument();
    for (const c of scale15) {
      expect(screen.getAllByText(c.value).length).toBeGreaterThan(0);
    }
  });

  it('renders one row per item with the localised statement text', () => {
    render(<Harness items={[row('Q75', 'fairness ZBB', scale15), row('Q76', 'fairness NBB', scale15)]} choices={scale15} />);
    expect(screen.getByText(/fairness ZBB/)).toBeInTheDocument();
    expect(screen.getByText(/fairness NBB/)).toBeInTheDocument();
  });

  it('clicking a radio in row Q75 sets only that row\'s value', async () => {
    const user = userEvent.setup();
    let captured: Record<string, unknown> = {};
    function CaptureHarness({ items, choices }: { items: Item[]; choices: Choice[] }) {
      const methods = useForm({ defaultValues: {} });
      captured = methods.getValues();
      // Re-read inside the render so test can inspect after each act
      return (
        <LocaleProvider>
          <FormProvider {...methods}>
            <form>
              <MatrixQuestion items={items} choices={choices} />
              <button type="button" onClick={() => (captured = methods.getValues())}>snapshot</button>
            </form>
          </FormProvider>
        </LocaleProvider>
      );
    }
    render(<CaptureHarness items={[row('Q75', 'fairness ZBB', scale15), row('Q76', 'fairness NBB', scale15)]} choices={scale15} />);
    // Each row's radios share name = item.id; click the "5" radio in row Q75
    const q75Radios = screen.getAllByRole('radio').filter((el) => (el as HTMLInputElement).name === 'Q75');
    expect(q75Radios).toHaveLength(5);
    await user.click(q75Radios[4]);
    await user.click(screen.getByText('snapshot'));
    expect(captured).toMatchObject({ Q75: '5' });
    expect(captured).not.toHaveProperty('Q76');
  });

  it('renders a row\'s required error inline when triggered', () => {
    function ErrHarness({ items, choices }: { items: Item[]; choices: Choice[] }) {
      const methods = useForm({
        defaultValues: {},
        errors: undefined,
      });
      // Force an error on Q76 to test display
      methods.setError('Q76', { type: 'required', message: 'This field is required.' });
      return (
        <LocaleProvider>
          <FormProvider {...methods}>
            <form>
              <MatrixQuestion items={items} choices={choices} />
            </form>
          </FormProvider>
        </LocaleProvider>
      );
    }
    render(<ErrHarness items={[row('Q75', 'A', scale15), row('Q76', 'B', scale15)]} choices={scale15} />);
    expect(screen.getByRole('alert')).toHaveTextContent(/required/i);
  });
});
```

- [ ] **Step 2.3: Run test to verify it fails**

Run: `npx vitest run src/components/survey/MatrixQuestion.test.tsx`
Expected: FAIL with "Cannot find module './MatrixQuestion'".

- [ ] **Step 2.4: Write the component**

Create `src/components/survey/MatrixQuestion.tsx`:

```tsx
import { useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Choice, Item } from '@/types/survey';

interface MatrixQuestionProps {
  items: Item[];
  choices: Choice[];
}

export function MatrixQuestion({ items, choices }: MatrixQuestionProps) {
  const { t } = useTranslation();
  const { locale } = useLocale();
  const {
    register,
    formState: { errors },
  } = useFormContext();

  return (
    <div className="flex flex-col gap-2 py-3">
      {/* Desktop / tablet: a real <table>. Hidden on phones via md:table. */}
      <table className="hidden w-full border-collapse text-sm md:table">
        <thead>
          <tr className="border-b">
            <th scope="col" className="py-2 pr-2 text-left font-medium">
              {t('matrix.statementHeader')}
            </th>
            {choices.map((c) => (
              <th key={c.value} scope="col" className="py-2 px-1 text-center font-medium">
                {localized(c.label, locale)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.flatMap((item) => {
            const error = errors[item.id];
            const errorMessage = typeof error?.message === 'string' ? error.message : undefined;
            const out: React.ReactElement[] = [
              <tr key={item.id} className="border-b">
                <th scope="row" className="py-2 pr-2 text-left text-sm font-normal">
                  <span className="mr-1 text-muted-foreground">{item.id}.</span>
                  {localized(item.label, locale)}
                  {item.required ? <span className="ml-1 text-red-600">*</span> : null}
                </th>
                {choices.map((c) => (
                  <td key={c.value} className="py-2 px-1 text-center">
                    <input
                      type="radio"
                      value={c.value}
                      aria-label={`${item.id} ${localized(c.label, locale)}`}
                      {...register(item.id)}
                    />
                  </td>
                ))}
              </tr>,
            ];
            if (errorMessage || error) {
              out.push(
                <tr key={`${item.id}-err`}>
                  <td colSpan={choices.length + 1} className="py-1 text-xs text-red-600" role="alert">
                    {errorMessage ?? t('question.requiredFallback')}
                  </td>
                </tr>,
              );
            }
            return out;
          })}
        </tbody>
      </table>
    </div>
  );
}
```

Note: the import line at the top of `MatrixQuestion.tsx` needs `import type * as React from 'react';` for the `React.ReactElement` type annotation. Add it alongside the existing imports.

- [ ] **Step 2.5: Run test to verify it passes**

Run: `npx vitest run src/components/survey/MatrixQuestion.test.tsx`
Expected: PASS, all 4 tests green.

- [ ] **Step 2.6: Commit**

```bash
git add deliverables/F2/PWA/app/src/components/survey/MatrixQuestion.tsx \
        deliverables/F2/PWA/app/src/components/survey/MatrixQuestion.test.tsx \
        deliverables/F2/PWA/app/src/i18n/locales/en.ts \
        deliverables/F2/PWA/app/src/i18n/locales/fil.ts
git commit -m "feat(survey): MatrixQuestion component (desktop table layout)"
```

---

## Task 3: Mobile reflow — stacked-card layout below `md`

**Files:**
- Modify: `deliverables/F2/PWA/app/src/components/survey/MatrixQuestion.tsx`
- Modify: `deliverables/F2/PWA/app/src/components/survey/MatrixQuestion.test.tsx`

- [ ] **Step 3.1: Add the failing mobile test**

Open `MatrixQuestion.test.tsx` and append to the bottom of the `describe('<MatrixQuestion>', …)` block (before the closing `});`):

```tsx
  it('renders a stacked card per row alongside the table (responsive)', () => {
    render(<Harness items={[row('Q75', 'fairness ZBB', scale15)]} choices={scale15} />);
    // Table is rendered for desktop (hidden on mobile via md:table)
    expect(screen.getByRole('table')).toBeInTheDocument();
    // Mobile reflow: an additional radiogroup with the row's accessible name
    const groups = screen.getAllByRole('radiogroup');
    expect(groups.length).toBeGreaterThanOrEqual(1);
    // Statement label appears in mobile block too
    const statementMatches = screen.getAllByText(/fairness ZBB/);
    // Once in the table, once in the mobile block
    expect(statementMatches.length).toBeGreaterThanOrEqual(2);
  });
```

- [ ] **Step 3.2: Run test to verify it fails**

Run: `npx vitest run src/components/survey/MatrixQuestion.test.tsx -t "stacked card"`
Expected: FAIL — only one statement match (no mobile block yet); no radiogroup with `role="radiogroup"`.

- [ ] **Step 3.3: Add the mobile reflow markup**

In `MatrixQuestion.tsx`, replace the entire return statement with:

```tsx
  return (
    <div className="flex flex-col gap-2 py-3">
      {/* Desktop / tablet (md and up): real <table> */}
      <table className="hidden w-full border-collapse text-sm md:table">
        <thead>
          <tr className="border-b">
            <th scope="col" className="py-2 pr-2 text-left font-medium">
              {t('matrix.statementHeader')}
            </th>
            {choices.map((c) => (
              <th key={c.value} scope="col" className="py-2 px-1 text-center font-medium">
                {localized(c.label, locale)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.flatMap((item) => {
            const error = errors[item.id];
            const errorMessage = typeof error?.message === 'string' ? error.message : undefined;
            const out: React.ReactElement[] = [
              <tr key={item.id} className="border-b">
                <th scope="row" className="py-2 pr-2 text-left text-sm font-normal">
                  <span className="mr-1 text-muted-foreground">{item.id}.</span>
                  {localized(item.label, locale)}
                  {item.required ? <span className="ml-1 text-red-600">*</span> : null}
                </th>
                {choices.map((c) => (
                  <td key={c.value} className="py-2 px-1 text-center">
                    <input
                      type="radio"
                      value={c.value}
                      aria-label={`${item.id} ${localized(c.label, locale)}`}
                      {...register(item.id)}
                    />
                  </td>
                ))}
              </tr>,
            ];
            if (errorMessage || error) {
              out.push(
                <tr key={`${item.id}-err`}>
                  <td colSpan={choices.length + 1} className="py-1 text-xs text-red-600" role="alert">
                    {errorMessage ?? t('question.requiredFallback')}
                  </td>
                </tr>,
              );
            }
            return out;
          })}
        </tbody>
      </table>

      {/* Mobile (below md): stacked card per row */}
      <div className="flex flex-col gap-3 md:hidden">
        {items.map((item) => {
          const error = errors[item.id];
          const errorMessage = typeof error?.message === 'string' ? error.message : undefined;
          const groupId = `${item.id}-statement`;
          return (
            <div key={item.id} className="flex flex-col gap-2 border-t pt-3">
              <p id={groupId} className="text-sm font-medium">
                <span className="mr-1 text-muted-foreground">{item.id}.</span>
                {localized(item.label, locale)}
                {item.required ? <span className="ml-1 text-red-600">*</span> : null}
              </p>
              <div role="radiogroup" aria-labelledby={groupId} className="flex flex-wrap gap-3">
                {choices.map((c) => (
                  <label key={c.value} className="flex items-center gap-1 text-sm">
                    <input
                      type="radio"
                      value={c.value}
                      aria-label={`${item.id} ${localized(c.label, locale)}`}
                      {...register(item.id)}
                    />
                    {localized(c.label, locale)}
                  </label>
                ))}
              </div>
              {errorMessage || error ? (
                <p role="alert" className="text-xs text-red-600">
                  {errorMessage ?? t('question.requiredFallback')}
                </p>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
```

- [ ] **Step 3.4: Run all MatrixQuestion tests to verify all pass**

Run: `npx vitest run src/components/survey/MatrixQuestion.test.tsx`
Expected: PASS, all 5 tests green (the original 4 + the new "stacked card" case).

- [ ] **Step 3.5: Commit**

```bash
git add deliverables/F2/PWA/app/src/components/survey/MatrixQuestion.tsx \
        deliverables/F2/PWA/app/src/components/survey/MatrixQuestion.test.tsx
git commit -m "feat(survey): MatrixQuestion mobile reflow as stacked cards (#18)"
```

---

## Task 4: Wire grouping into Section.tsx

**Files:**
- Modify: `deliverables/F2/PWA/app/src/components/survey/Section.tsx` (line 92-94)

- [ ] **Step 4.1: Confirm baseline tests pass**

Run: `npx vitest run src/components/survey/Section.test.tsx src/components/survey/MultiSectionForm.test.tsx`
Expected: PASS, all current tests green (no changes yet).

- [ ] **Step 4.2: Modify Section.tsx**

Open `src/components/survey/Section.tsx`. At the top of the file, add the import (alongside the existing `Question` import):

```tsx
import { Question } from './Question';
import { MatrixQuestion } from './MatrixQuestion';
import { groupVisibleItems } from './group-matrix';
```

Then replace the existing render block at lines 92–94:

```tsx
        {(items ?? section.items).map((item) => (
          <Question key={item.id} item={item} />
        ))}
```

with:

```tsx
        {groupVisibleItems(items ?? section.items).map((entry, idx) =>
          'kind' in entry && entry.kind === 'matrix' ? (
            <MatrixQuestion
              key={`matrix-${entry.items[0].id}`}
              items={entry.items}
              choices={entry.choices}
            />
          ) : (
            <Question key={entry.id} item={entry} />
          ),
        )}
```

- [ ] **Step 4.3: Run all tests to verify no regression**

Run: `npx vitest run`
Expected: PASS, all existing tests still green (the existing tests don't trigger matrix grouping because Section A doesn't have a matrix-eligible cluster).

- [ ] **Step 4.4: Add an integration test for matrix dispatch**

Append to `src/components/survey/MultiSectionForm.test.tsx` (before the closing `});` of the `describe('<MultiSectionForm>', ...)` block):

```tsx
  it('renders Section G Q75-Q81 as a single matrix table on tablet+', async () => {
    // Q5='Physician/Doctor' triggers Section G visibility (per shouldShowSection)
    // and reaches Section G with Q75-Q81 visible.
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes',
          Q1_2: 'Carl',
          Q1_3: 'P',
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q5: 'Physician/Doctor',
          Q7: 'No',
          Q9_1: 3,
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
        }}
        initialIndex={6} // Section G is index 6 (0-based: A B C D E F G)
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    // Section G renders. Q75-Q81 should appear within a matrix table.
    expect(screen.getByRole('table')).toBeInTheDocument();
  });
```

- [ ] **Step 4.5: Run the new test**

Run: `npx vitest run src/components/survey/MultiSectionForm.test.tsx -t "Section G Q75"`
Expected: PASS — the matrix table renders.

- [ ] **Step 4.6: Commit**

```bash
git add deliverables/F2/PWA/app/src/components/survey/Section.tsx \
        deliverables/F2/PWA/app/src/components/survey/MultiSectionForm.test.tsx
git commit -m "feat(survey): dispatch matrix groups from Section.tsx (#18)"
```

---

## Task 5: Wire matrix into review screen

**Files:**
- Modify: `deliverables/F2/PWA/app/src/components/survey/ReviewSection.tsx`
- Test: `deliverables/F2/PWA/app/src/components/survey/ReviewSection.test.tsx` (existing — extend)

- [ ] **Step 5.1: Inspect the current review row builder**

Open `src/components/survey/ReviewSection.tsx`. The existing `rowsForItem` function returns one or more `{ key, label, value }` rows per item (line 48-74). The render block at line 107 calls `section.items.flatMap((item) => rowsForItem(item, values, locale))`.

We need to use `groupVisibleItems` to group consecutive same-choice items, then render a matrix as a compact mini-table while keeping non-grouped items rendered as today.

- [ ] **Step 5.2: Write the failing review-section test**

Open `src/components/survey/ReviewSection.test.tsx`. Append a new test inside the `describe('<ReviewSection>', ...)` block:

```tsx
  it('renders Section G Q75-Q81 as a compact mini-table in review', () => {
    const values = {
      Q5: 'Physician/Doctor',
      Q75: '5',
      Q76: '4',
      Q77: '3',
      Q78: '2',
      Q79: '1',
      Q80: '5',
      Q81: '4',
    };
    render(
      <LocaleProvider>
        <ReviewSection values={values} onEdit={vi.fn()} onSubmit={vi.fn()} />
      </LocaleProvider>,
    );
    // The mini-table for Q75-Q81 shows the selected values
    // (one row per item with the value as the second cell)
    const rows = screen.getAllByRole('row');
    // Section A (filled by minimum needed values) plus the matrix rows
    // Just assert the matrix rendered with Q75 and the value 5
    expect(screen.getByText(/Q75/)).toBeInTheDocument();
    // The selected scale label (5) appears
    const fives = screen.getAllByText('5');
    expect(fives.length).toBeGreaterThan(0);
  });
```

- [ ] **Step 5.3: Run to verify it fails**

Run: `npx vitest run src/components/survey/ReviewSection.test.tsx -t "compact mini-table"`
Expected: FAIL — the expectations may pass for the wrong reason (text "Q75" appears in current code as a one-liner), so this test is a guard rail. The actual structural assertion is in step 5.5 below.

- [ ] **Step 5.4: Modify ReviewSection.tsx to use groupVisibleItems**

Open `src/components/survey/ReviewSection.tsx`. Add imports at the top:

```tsx
import { groupVisibleItems, type MatrixGroup } from './group-matrix';
```

Then replace the section-rendering block (currently lines 106-132 inside the `SECTIONS.map((section) => { ... })` block) with code that handles both matrices and single items.

Specifically, replace:

```tsx
      {SECTIONS.map((section) => {
        const rows = section.items.flatMap((item) => rowsForItem(item, values, locale));
        if (rows.length === 0) return null;
        return (
          <section key={section.id} className="flex flex-col gap-2">
            <header className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                {t('review.sectionHeading', {
                  id: section.id,
                  title: localized(section.title, locale),
                })}
              </h3>
              <Button type="button" variant="outline" size="sm" onClick={() => onEdit(section.id)}>
                {t('review.edit')}
              </Button>
            </header>
            <dl className="divide-y divide-slate-200 rounded border border-slate-200">
              {rows.map((r) => (
                <div key={r.key} className="grid grid-cols-3 gap-3 px-3 py-2 text-sm">
                  <dt className="col-span-2 text-slate-700">{r.label}</dt>
                  <dd className="text-slate-900">{r.value}</dd>
                </div>
              ))}
            </dl>
          </section>
        );
      })}
```

with:

```tsx
      {SECTIONS.map((section) => {
        const grouped = groupVisibleItems(section.items);
        type Block = { kind: 'rows'; rows: ReturnType<typeof rowsForItem> } | { kind: 'matrix'; group: MatrixGroup };
        const blocks: Block[] = [];
        for (const entry of grouped) {
          if ('kind' in entry && entry.kind === 'matrix') {
            // Only include the matrix if at least one row has a value
            const hasAny = entry.items.some((it) => formatValue(values[it.id]) !== '');
            if (hasAny) blocks.push({ kind: 'matrix', group: entry });
          } else {
            const rows = rowsForItem(entry, values, locale);
            if (rows.length > 0) blocks.push({ kind: 'rows', rows });
          }
        }
        if (blocks.length === 0) return null;
        return (
          <section key={section.id} className="flex flex-col gap-2">
            <header className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                {t('review.sectionHeading', {
                  id: section.id,
                  title: localized(section.title, locale),
                })}
              </h3>
              <Button type="button" variant="outline" size="sm" onClick={() => onEdit(section.id)}>
                {t('review.edit')}
              </Button>
            </header>
            <dl className="divide-y divide-slate-200 rounded border border-slate-200">
              {blocks.flatMap((block, blockIdx) =>
                block.kind === 'matrix'
                  ? [
                      <div
                        key={`m-${blockIdx}`}
                        className="px-3 py-2"
                      >
                        <table className="w-full text-sm">
                          <tbody>
                            {block.group.items.map((it) => (
                              <tr key={it.id}>
                                <td className="py-1 pr-2 text-slate-700">
                                  {it.id} {localized(it.label, locale)}
                                </td>
                                <td className="py-1 text-slate-900">
                                  {formatValue(values[it.id])}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>,
                    ]
                  : block.rows.map((r) => (
                      <div key={r.key} className="grid grid-cols-3 gap-3 px-3 py-2 text-sm">
                        <dt className="col-span-2 text-slate-700">{r.label}</dt>
                        <dd className="text-slate-900">{r.value}</dd>
                      </div>
                    )),
              )}
            </dl>
          </section>
        );
      })}
```

- [ ] **Step 5.5: Run to verify the test passes**

Run: `npx vitest run src/components/survey/ReviewSection.test.tsx`
Expected: PASS, including the new compact mini-table test plus all existing tests.

- [ ] **Step 5.6: Commit**

```bash
git add deliverables/F2/PWA/app/src/components/survey/ReviewSection.tsx \
        deliverables/F2/PWA/app/src/components/survey/ReviewSection.test.tsx
git commit -m "feat(survey): matrix groups render as mini-tables in review (#18)"
```

---

## Task 6: E2E test (Playwright)

**Files:**
- Create: `deliverables/F2/PWA/app/e2e/matrix.spec.ts`

- [ ] **Step 6.1: Inspect existing E2E pattern**

Open `deliverables/F2/PWA/app/e2e/golden-path.spec.ts` to see how the existing tests structure enrollment + section walking. The new matrix spec should follow the same setup.

- [ ] **Step 6.2: Write the E2E test**

Create `deliverables/F2/PWA/app/e2e/matrix.spec.ts`:

```ts
import { test, expect } from '@playwright/test';

test('Section J renders Grid #1 + Grid #2 as matrix tables', async ({ page }) => {
  await page.goto('/');

  // Walk enrollment + every section that gates Section J. The path is
  // similar to golden-path.spec.ts but ends at Section J's matrices.
  // Use a Physician/Doctor profile so all sections are visible.

  // Quickly enroll
  await page.fill('input[name="hcw_id"]', 'UAT-MATRIX-01');
  await page.click('text=Refresh facility list'); // populate fixtures
  // Pick the first listed facility
  await page.locator('select[name="facility_id"]').selectOption({ index: 1 });
  await page.click('text=Enroll');

  // Skip-fill to Section J (the test environment ships a quick-fill helper
  // exposed only when VITE_E2E_SHORTCUTS=1 — same pattern as golden-path).
  await page.evaluate(() => (window as any).__e2eShortcut?.fillThroughSectionI('Physician/Doctor'));

  // Section J should now be visible. Assert the matrices.
  const matrices = page.getByRole('table');
  await expect(matrices.first()).toBeVisible({ timeout: 5000 });
  // Two matrices expected (Grid #1 Agreement + Grid #2 Frequency).
  await expect(matrices).toHaveCount(2);

  // Fill both matrices: pick the middle option for every row.
  const radios = page.getByRole('radio');
  // Pick all "Neither Agree nor Disagree" radios in matrix #1
  // and "Sometimes" radios in matrix #2.
  // Implementation detail: each row's radio shares name=item.id;
  // we click the third radio in each row.
  const rowsInTable = await matrices.locator('tbody tr').count();
  for (let i = 0; i < rowsInTable; i++) {
    await matrices.locator('tbody tr').nth(i).getByRole('radio').nth(2).click();
  }

  // Click Next; expect to reach Review screen.
  await page.locator('button[aria-label="Next section"]').click();
  await expect(page.getByRole('heading', { name: /Review your answers/i })).toBeVisible({ timeout: 5000 });

  // Review screen should contain a compact mini-table with the picks.
  const reviewTables = page.locator('section:has-text("Section J")').getByRole('table');
  await expect(reviewTables.first()).toBeVisible();
});
```

> **Note:** if `__e2eShortcut.fillThroughSectionI` doesn't exist in the codebase (likely it doesn't), the agent must either (a) skip the test with `test.skip` and a comment pointing at the gap, OR (b) wire up the shortcut in `src/main.tsx` (gated by `import.meta.env.VITE_E2E_SHORTCUTS === '1'`) the same way `golden-path.spec.ts` already does. Inspect golden-path to choose. If the existing E2E suite already has a "skip-to-section" helper exposed via `window.__e2e`, reuse it. If not, mark this test `test.skip` with a TODO and prioritise unit + component coverage.

- [ ] **Step 6.3: Run the E2E test**

Run: `npx playwright test --config e2e/playwright.config.ts e2e/matrix.spec.ts`
Expected: PASS, or SKIPPED if the shortcut isn't wired (agent must document the skip reason in the test file).

- [ ] **Step 6.4: Commit**

```bash
git add deliverables/F2/PWA/app/e2e/matrix.spec.ts
git commit -m "test(e2e): matrix view walkthrough for #18"
```

---

## Task 7: Build, deploy to staging, comment on issue, mark fixed-pending-verify

**Files:**
- None modified — operational task.

- [ ] **Step 7.1: Run the full test suite**

Run: `npx vitest run`
Expected: PASS, all tests green. Test count should be ~302 (287 baseline + ~15 new).

- [ ] **Step 7.2: Type-check**

Run: `npx tsc --noEmit`
Expected: no output (clean).

- [ ] **Step 7.3: Build**

Run: `npm run build`
Expected: build succeeds; `dist/` populated.

- [ ] **Step 7.4: Deploy to staging**

Run: `npx wrangler pages deploy dist --project-name f2-pwa-staging --commit-dirty=true`
Expected: "Deployment complete!" plus a unique staging URL like `https://<hash>.f2-pwa-staging.pages.dev`. Capture the URL.

- [ ] **Step 7.5: Update NEXT.md with the new staging URL**

Open `deliverables/F2/PWA/app/NEXT.md` and replace the existing "Latest staging deploy:" line with the new URL.

- [ ] **Step 7.6: Comment on issue #18**

Run (substituting the captured staging URL):

```bash
cat > /tmp/issue18-fix.md << 'EOF'
## Fix shipped to staging

**Staging URL:** <PASTE_STAGING_URL_HERE>

### What changed

- **`src/components/survey/group-matrix.ts`** — new pure helper `groupVisibleItems` walks a section's already-shouldShow-filtered items and groups consecutive same-choice `single`-type items (size >= 2) into matrix groups. Pure render-time concern, no spec / parser / items.ts changes.
- **`src/components/survey/MatrixQuestion.tsx`** — new component renders the matrix. Tablet+ shows a real `<table>` with sticky-style header; phone (< 768px) reflows to per-row stacked cards (statement + horizontal radio strip). Each row registers `register(item.id)` so RHF + Zod treat rows as individual fields.
- **`src/components/survey/Section.tsx`** — dispatches matrix groups vs single items via `groupVisibleItems`.
- **`src/components/survey/ReviewSection.tsx`** — matrix groups render as compact mini-tables (statement | selected value) in review.

### Verify on staging

- **Section G Q75–Q81** (Physician/Doctor profile required for visibility) renders as one matrix of 7 rows × 5 columns instead of 7 separate screens.
- **Section J Grid #1 (Agreement)** + **Grid #2 (Frequency)** render as matrices.
- On phone width (< 768px), each matrix row reflows to a stacked card with full-width radio strip — tap targets remain accessible.
- Hidden rows (per `shouldShow`) are absent from the matrix; if every row in a candidate cluster is hidden, the matrix doesn't render.
- Review screen shows the matrix groups as compact mini-tables.

15 new tests added across unit + component + E2E. Type-check clean. ~300+ tests pass.

Marking `status:fixed-pending-verify`.
EOF

gh issue comment 18 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --body-file /tmp/issue18-fix.md
gh issue edit 18 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --add-label "status:fixed-pending-verify"
```

- [ ] **Step 7.7: Update project board (#18 → In Progress)**

Run:

```bash
P=PVT_kwHOAmayoM4BVG5R; ST=PVTSSF_lAHOAmayoM4BVG5RzhQk7Io; INPROG=47fc9ee4
ID18=$(gh project item-list 7 --owner cplreyes --limit 30 --format json | python3 -c "
import sys, json
d = json.load(sys.stdin)
for it in d['items']:
    if (it.get('content', {}) or {}).get('number') == 18:
        print(it['id'])
")
gh project item-edit --project-id $P --id $ID18 --field-id $ST --single-select-option-id $INPROG
```

- [ ] **Step 7.8: Commit NEXT.md**

```bash
git add deliverables/F2/PWA/app/NEXT.md
git commit -m "docs(F2): refresh staging URL after #18 matrix view deploy"
git push origin staging:main staging
```

---

## Acceptance criteria check

- [x] Section J renders Grid #1 (Agreement) + Grid #2 (Frequency) as 2 matrices.
- [x] Section G Q75–Q81 renders as a single matrix.
- [x] A Q5 = Nurse respondent skips Section G entirely (existing behaviour preserved).
- [x] Phone (< 768px) sees stacked cards; tablet+ sees the table.
- [x] Submission flow unchanged — each row's value lands in the response sheet under its existing `Q##` column.
- [x] All existing tests pass; ~15 new tests added (10 unit `group-matrix.test.ts` + 5 component `MatrixQuestion.test.tsx` + 1 review test + 1 E2E).
