# F2 PWA — M6 Full Instrument Scaffolding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every item in `app/spec/F2-Spec.md` (~117 items across 11 sections A, B, C, D, E1, E2, F, G, H, I, J) fillable in the PWA — no more "unsupported, deferred to M6" gaps.

**Architecture:** Extend the generator (`scripts/lib/parse-spec.ts` → `emit-items.ts` + `emit-schema.ts`) and the `<Question>` component to handle the four item-type families currently dropped: Likert (`single (1–5)`), `multi` / `multi + specify`, `date`, and multi-field (`short-text ×N` / `number ×N`). Treat `grid-single` as `single` with the listed choices (no matrix rendering needed at MVP — the spec already lists each row as its own Q-id). Wire all 11 sections into `MultiSectionForm`. Add hand-written skip-logic predicates for sections D–J based on the `gate` / `skip` columns in the spec; full skip-logic generation from `F2-Skip-Logic.md` is M7's job, not M6's.

**Tech Stack:** TypeScript generator (tsx) · React 18 + react-hook-form + zod · Vitest 4 + jsdom + @testing-library/react.

**Spec section reference:** `2026-04-17-design-spec.md` §6 (Generator Pattern) and §11.1 row M6.

---

## File Structure (decomposition)

| File | Responsibility | Status |
|---|---|---|
| `app/scripts/lib/types.ts` | `ItemType` union + `Item` shape (adds `multi`, `date`, `multi-field` + subField metadata) | modify |
| `app/scripts/lib/parse-spec.ts` | recognise new raw types; widen `grid-single` → `single`; emit Likert auto-choices | modify |
| `app/scripts/lib/emit-items.ts` | serialise new fields (`subFields`) into the items literal | modify |
| `app/scripts/lib/emit-schema.ts` | emit `z.array`, `z.string()`-as-ISO-date, and per-subfield object schemas | modify |
| `app/src/types/survey.ts` | runtime `Item` type — must stay in sync with `scripts/lib/types.ts` | modify |
| `app/src/components/survey/Question.tsx` | render `multi` (checkbox group + `_other`), `date` (input type=date), `multi-field` (N labelled inputs) | modify |
| `app/src/components/survey/MultiSectionForm.tsx` | wire all 11 sections, not just A/B/C | modify |
| `app/src/lib/skip-logic.ts` | hand-written predicates for D, E1, E2, F, G, H, I, J | modify |
| `app/src/lib/skip-logic.test.ts` | tests covering new predicates | modify |
| `app/src/generated/items.ts` | regenerated (do not hand-edit) | regen |
| `app/src/generated/schema.ts` | regenerated (do not hand-edit) | regen |
| `app/NEXT.md` | rewrite to point at M7 (validation + cross-field) | modify |

---

## Task 1: Likert (`single (1–5)`) parser support

**Files:**
- Modify: `app/scripts/lib/parse-spec.ts` (`SUPPORTED_TYPES` table)
- Modify: `app/scripts/lib/parse-spec.test.ts`

The spec uses `single (1–5)` for ~7 items in Section G. Treat as `single` with auto-generated 5-point numeric choices when the choices column is the literal `1 · 2 · 3 · 4 · 5`.

- [ ] **Step 1: Write the failing test**

Append to `app/scripts/lib/parse-spec.test.ts` inside the existing `describe('normalizeRow', () => { ... })`:

```ts
  it('treats "single (1–5)" as a single with auto-generated 1..5 numeric choices', () => {
    const row: RowFields = {
      pdf_q: 'Q68',
      legacy_q: '—',
      type: 'single (1–5)',
      required: 'Y',
      label: 'How adequate is your fee?',
      choices: '1 · 2 · 3 · 4 · 5',
    };
    const { item, unsupported } = normalizeRow(row, 'G');
    expect(unsupported).toBeUndefined();
    expect(item).toMatchObject({
      id: 'Q68',
      type: 'single',
      choices: [
        { label: '1', value: '1' },
        { label: '2', value: '2' },
        { label: '3', value: '3' },
        { label: '4', value: '4' },
        { label: '5', value: '5' },
      ],
    });
  });
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- scripts/lib/parse-spec.test.ts`
Expected: FAIL — `unsupported` defined, item undefined.

- [ ] **Step 3: Implement**

In `app/scripts/lib/parse-spec.ts`, edit `SUPPORTED_TYPES`:

```ts
const SUPPORTED_TYPES: Record<string, ItemType> = {
  single: 'single',
  'single + specify': 'single',
  'single (1–5)': 'single',
  'short-text': 'short-text',
  'long-text': 'long-text',
  number: 'number',
};
```

The existing `parseChoiceList` will already accept `1 · 2 · 3 · 4 · 5` as five labelled choices — no further change needed.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- scripts/lib/parse-spec.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/scripts/lib/parse-spec.ts app/scripts/lib/parse-spec.test.ts
git commit -m "feat(f2-pwa): M6.1 parser accepts single (1–5) Likert items"
```

---

## Task 2: `multi` ItemType — types + parser

**Files:**
- Modify: `app/scripts/lib/types.ts`
- Modify: `app/src/types/survey.ts` (mirror)
- Modify: `app/scripts/lib/parse-spec.ts`
- Modify: `app/scripts/lib/parse-spec.test.ts`

`multi` and `multi + specify` are checkbox groups. Form value is `string[]`. Same `_other` text suffix when `+ specify`.

- [ ] **Step 1: Add type to both type files**

Edit `app/scripts/lib/types.ts`:

```ts
export type ItemType = 'short-text' | 'long-text' | 'number' | 'single' | 'multi';
```

Edit `app/src/types/survey.ts` to keep it identical:

```ts
export type ItemType = 'short-text' | 'long-text' | 'number' | 'single' | 'multi';
```

(Both files have the same `Item` shape — leave the rest alone.)

- [ ] **Step 2: Write the failing parser test**

Append inside `describe('normalizeRow')` in `app/scripts/lib/parse-spec.test.ts`:

```ts
  it('parses "multi" as multi-select with choices', () => {
    const row: RowFields = {
      pdf_q: 'Q28',
      legacy_q: 'Q34',
      type: 'multi',
      required: 'Y',
      label: 'Which are included in the package?',
      choices: 'Pap smear · Mammogram · Lipid profile',
    };
    const { item, unsupported } = normalizeRow(row, 'C');
    expect(unsupported).toBeUndefined();
    expect(item).toMatchObject({
      id: 'Q28',
      type: 'multi',
      hasOtherSpecify: false,
      choices: [
        { label: 'Pap smear', value: 'Pap smear' },
        { label: 'Mammogram', value: 'Mammogram' },
        { label: 'Lipid profile', value: 'Lipid profile' },
      ],
    });
  });

  it('parses "multi + specify" with the Other choice flagged', () => {
    const row: RowFields = {
      pdf_q: 'Q21',
      legacy_q: 'Q28',
      type: 'multi + specify',
      required: 'Y',
      label: 'Which do you expect to change?',
      choices: 'Salary · Working hours · Other (specify)',
    };
    const { item } = normalizeRow(row, 'B');
    expect(item).toMatchObject({
      id: 'Q21',
      type: 'multi',
      hasOtherSpecify: true,
    });
    expect(item?.choices?.find((c) => c.isOtherSpecify)).toMatchObject({
      label: 'Other (specify)',
    });
  });
```

- [ ] **Step 3: Run test to verify it fails**

Run: `npm test -- scripts/lib/parse-spec.test.ts`
Expected: FAIL — `unsupported` defined for `multi`.

- [ ] **Step 4: Implement parser support**

In `app/scripts/lib/parse-spec.ts`, extend `SUPPORTED_TYPES`:

```ts
const SUPPORTED_TYPES: Record<string, ItemType> = {
  single: 'single',
  'single + specify': 'single',
  'single (1–5)': 'single',
  multi: 'multi',
  'multi + specify': 'multi',
  'short-text': 'short-text',
  'long-text': 'long-text',
  number: 'number',
};
```

In `normalizeRow`, mirror the choice-handling block from `single` for `multi`. Replace the existing `if (type === 'single') { ... }` block with:

```ts
  if (type === 'single' || type === 'multi') {
    item.hasOtherSpecify = hasOtherSpecify;
    const choices = parseChoiceList(choicesText, hasOtherSpecify);
    if (choices) item.choices = choices;
  }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npm test -- scripts/lib/parse-spec.test.ts`
Expected: PASS — both new tests green.

- [ ] **Step 6: Commit**

```bash
git add app/scripts/lib/types.ts app/scripts/lib/parse-spec.ts app/scripts/lib/parse-spec.test.ts app/src/types/survey.ts
git commit -m "feat(f2-pwa): M6.2 multi ItemType in types + parser"
```

---

## Task 3: `multi` schema emission + Question rendering

**Files:**
- Modify: `app/scripts/lib/emit-schema.ts`
- Modify: `app/scripts/lib/emit-schema.test.ts`
- Modify: `app/src/components/survey/Question.tsx`
- Create: `app/src/components/survey/Question.test.tsx` (if not present — append to existing)

- [ ] **Step 1: Write the failing schema-emit test**

Append to `app/scripts/lib/emit-schema.test.ts` inside the existing `describe`:

```ts
  it('emits z.array(z.enum) for required multi items', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'X',
          title: 'X',
          items: [
            {
              id: 'Q1',
              section: 'X',
              type: 'multi',
              required: true,
              label: 'pick',
              choices: [
                { label: 'A', value: 'A' },
                { label: 'B', value: 'B' },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const out = emitSchema(result);
    expect(out).toContain("Q1: z.array(z.enum(['A', 'B'])).min(1)");
  });

  it('emits optional z.array for non-required multi items', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'X',
          title: 'X',
          items: [
            {
              id: 'Q2',
              section: 'X',
              type: 'multi',
              required: false,
              label: 'pick',
              choices: [{ label: 'A', value: 'A' }],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const out = emitSchema(result);
    expect(out).toContain("Q2: z.array(z.enum(['A'])).optional()");
  });
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- scripts/lib/emit-schema.test.ts`
Expected: FAIL — switch falls through, output lacks `z.array`.

- [ ] **Step 3: Extend `fieldSchema`**

In `app/scripts/lib/emit-schema.ts`, add a `case 'multi'` branch to `fieldSchema`:

```ts
function fieldSchema(item: Item): string {
  switch (item.type) {
    case 'short-text':
    case 'long-text':
      return item.required ? 'z.string().min(1)' : 'z.string().optional()';
    case 'number': {
      let expr = 'z.coerce.number()';
      if (item.min !== undefined) expr += `.min(${item.min})`;
      if (item.max !== undefined) expr += `.max(${item.max})`;
      if (!item.required) expr += '.optional()';
      return expr;
    }
    case 'single': {
      const values = (item.choices ?? []).map((c) => `'${c.value.replace(/'/g, "\\'")}'`);
      const base = `z.enum([${values.join(', ')}])`;
      return item.required ? base : `${base}.optional()`;
    }
    case 'multi': {
      const values = (item.choices ?? []).map((c) => `'${c.value.replace(/'/g, "\\'")}'`);
      const base = `z.array(z.enum([${values.join(', ')}]))`;
      return item.required ? `${base}.min(1)` : `${base}.optional()`;
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- scripts/lib/emit-schema.test.ts`
Expected: PASS.

- [ ] **Step 5: Write the failing Question component test**

If `app/src/components/survey/Question.test.tsx` does not exist, create it. Otherwise append. The full new file (or new `describe`) is:

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useForm, FormProvider } from 'react-hook-form';
import type { Item } from '@/types/survey';
import { Question } from './Question';

function Harness({ item, defaults = {} }: { item: Item; defaults?: Record<string, unknown> }) {
  const methods = useForm({ defaultValues: defaults });
  return (
    <FormProvider {...methods}>
      <Question item={item} />
    </FormProvider>
  );
}

describe('Question — multi', () => {
  const item: Item = {
    id: 'Q28',
    section: 'C',
    type: 'multi',
    required: true,
    label: 'Pick all',
    choices: [
      { label: 'A', value: 'A' },
      { label: 'B', value: 'B' },
      { label: 'C', value: 'C' },
    ],
  };

  it('renders one checkbox per choice', () => {
    render(<Harness item={item} />);
    expect(screen.getByRole('checkbox', { name: 'A' })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'B' })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'C' })).toBeInTheDocument();
  });

  it('checks the boxes from defaultValues', () => {
    render(<Harness item={item} defaults={{ Q28: ['A', 'C'] }} />);
    expect(screen.getByRole('checkbox', { name: 'A' })).toBeChecked();
    expect(screen.getByRole('checkbox', { name: 'B' })).not.toBeChecked();
    expect(screen.getByRole('checkbox', { name: 'C' })).toBeChecked();
  });

  it('reveals the _other text input when an isOtherSpecify choice is checked', async () => {
    const withOther: Item = {
      ...item,
      hasOtherSpecify: true,
      choices: [
        { label: 'A', value: 'A' },
        { label: 'Other', value: 'Other', isOtherSpecify: true },
      ],
    };
    const user = userEvent.setup();
    render(<Harness item={withOther} />);
    expect(screen.queryByLabelText(/please specify/i)).not.toBeInTheDocument();
    await user.click(screen.getByRole('checkbox', { name: 'Other' }));
    expect(screen.getByLabelText(/please specify/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 6: Run test to verify it fails**

Run: `npm test -- src/components/survey/Question.test.tsx`
Expected: FAIL — Question switch has no `multi` case, nothing rendered.

- [ ] **Step 7: Implement multi rendering in Question**

In `app/src/components/survey/Question.tsx`, after the `case 'single':` block in `renderControl`, add a `case 'multi':` branch:

```tsx
    case 'multi':
      return (
        <div className="flex flex-col gap-1">
          <fieldset className="flex flex-col gap-1">
            {item.choices?.map((choice) => (
              <label key={choice.value} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  value={choice.value}
                  {...register(item.id)}
                />
                {choice.label}
              </label>
            ))}
          </fieldset>
          {showSpecify ? (
            <div className="mt-2 flex flex-col gap-1 pl-6">
              <label htmlFor={`${item.id}_other`} className="text-xs text-muted-foreground">
                Please specify
              </label>
              <input
                id={`${item.id}_other`}
                type="text"
                className="rounded border border-input bg-background px-3 py-2"
                {...register(`${item.id}_other`)}
              />
            </div>
          ) : null}
        </div>
      );
```

Update the `showSpecify` calculation at the top of `Question` to handle multi-select arrays — replace the existing line:

```tsx
  const showSpecify =
    (item.hasOtherSpecify &&
      item.choices?.some((c) => {
        if (!c.isOtherSpecify) return false;
        if (item.type === 'multi') {
          return Array.isArray(currentValue) && currentValue.includes(c.value);
        }
        return c.value === currentValue;
      })) ??
    false;
```

- [ ] **Step 8: Run test to verify it passes**

Run: `npm test -- src/components/survey/Question.test.tsx`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add app/scripts/lib/emit-schema.ts app/scripts/lib/emit-schema.test.ts app/src/components/survey/Question.tsx app/src/components/survey/Question.test.tsx
git commit -m "feat(f2-pwa): M6.3 multi schema emission + checkbox rendering"
```

---

## Task 4: `date` ItemType — full vertical

**Files:**
- Modify: `app/scripts/lib/types.ts`
- Modify: `app/src/types/survey.ts` (mirror)
- Modify: `app/scripts/lib/parse-spec.ts`
- Modify: `app/scripts/lib/emit-schema.ts`
- Modify: `app/scripts/lib/parse-spec.test.ts`
- Modify: `app/scripts/lib/emit-schema.test.ts`
- Modify: `app/src/components/survey/Question.tsx`
- Modify: `app/src/components/survey/Question.test.tsx`

Only one item in the spec uses this (`Q31` "Since when?"). Form value is an ISO date string `YYYY-MM-DD` from `<input type="date">`.

- [ ] **Step 1: Add `'date'` to both ItemType unions**

In `app/scripts/lib/types.ts` AND `app/src/types/survey.ts`:

```ts
export type ItemType = 'short-text' | 'long-text' | 'number' | 'single' | 'multi' | 'date';
```

- [ ] **Step 2: Write failing parser test**

Append in `app/scripts/lib/parse-spec.test.ts`:

```ts
  it('parses "date" as a date item', () => {
    const row: RowFields = {
      pdf_q: 'Q31',
      legacy_q: '—',
      type: 'date',
      required: 'conditional',
      label: 'Since when?',
      choices: 'Month / Day / Year',
    };
    const { item, unsupported } = normalizeRow(row, 'C');
    expect(unsupported).toBeUndefined();
    expect(item).toMatchObject({ id: 'Q31', type: 'date', required: false });
  });
```

- [ ] **Step 3: Run failing test**

Run: `npm test -- scripts/lib/parse-spec.test.ts`
Expected: FAIL — date is unsupported.

- [ ] **Step 4: Add date to parser**

In `app/scripts/lib/parse-spec.ts`, extend `SUPPORTED_TYPES`:

```ts
  date: 'date',
```

(Insert as a new key in the object literal; alphabetic order is fine.)

- [ ] **Step 5: Verify parser test passes**

Run: `npm test -- scripts/lib/parse-spec.test.ts`
Expected: PASS.

- [ ] **Step 6: Write failing schema test**

Append to `app/scripts/lib/emit-schema.test.ts`:

```ts
  it('emits an ISO-date string schema for date items', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'X',
          title: 'X',
          items: [
            { id: 'Q31', section: 'X', type: 'date', required: false, label: 'When?' },
          ],
        },
      ],
      unsupported: [],
    };
    const out = emitSchema(result);
    expect(out).toContain('Q31: z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/).optional()');
  });
```

- [ ] **Step 7: Run failing schema test**

Run: `npm test -- scripts/lib/emit-schema.test.ts`
Expected: FAIL — switch missing case.

- [ ] **Step 8: Add date case to fieldSchema**

In `app/scripts/lib/emit-schema.ts`, append inside the `switch`:

```ts
    case 'date': {
      const base = String.raw`z.string().regex(/^\d{4}-\d{2}-\d{2}$/)`;
      return item.required ? base : `${base}.optional()`;
    }
```

- [ ] **Step 9: Verify schema test passes**

Run: `npm test -- scripts/lib/emit-schema.test.ts`
Expected: PASS.

- [ ] **Step 10: Write failing Question test**

Append in `app/src/components/survey/Question.test.tsx`:

```tsx
describe('Question — date', () => {
  it('renders a date input wired by id', () => {
    const item: Item = {
      id: 'Q31',
      section: 'C',
      type: 'date',
      required: false,
      label: 'Since when?',
    };
    render(<Harness item={item} />);
    const input = screen.getByLabelText(/since when/i);
    expect(input).toHaveAttribute('type', 'date');
  });
});
```

- [ ] **Step 11: Run failing Question test**

Run: `npm test -- src/components/survey/Question.test.tsx`
Expected: FAIL — switch falls through.

- [ ] **Step 12: Implement Question date branch**

In `app/src/components/survey/Question.tsx`, after the `case 'multi':` block, add:

```tsx
    case 'date':
      return (
        <input
          id={item.id}
          type="date"
          className="rounded border border-input bg-background px-3 py-2"
          {...register(item.id)}
        />
      );
```

- [ ] **Step 13: Verify Question test passes**

Run: `npm test -- src/components/survey/Question.test.tsx`
Expected: PASS.

- [ ] **Step 14: Commit**

```bash
git add app/scripts/lib/types.ts app/scripts/lib/parse-spec.ts app/scripts/lib/emit-schema.ts app/scripts/lib/parse-spec.test.ts app/scripts/lib/emit-schema.test.ts app/src/types/survey.ts app/src/components/survey/Question.tsx app/src/components/survey/Question.test.tsx
git commit -m "feat(f2-pwa): M6.4 date ItemType end-to-end"
```

---

## Task 5: `multi-field` ItemType — types + parser

**Files:**
- Modify: `app/scripts/lib/types.ts` (+ `Item.subFields`)
- Modify: `app/src/types/survey.ts` (mirror)
- Modify: `app/scripts/lib/parse-spec.ts`
- Modify: `app/scripts/lib/parse-spec.test.ts`

Two items use this: `Q1 short-text ×3` (Last/First/Middle) and `Q9 number ×2` (years/months). Cells in the choices column carry the subfield labels separated by ` / `.

- [ ] **Step 1: Extend types**

Edit BOTH `app/scripts/lib/types.ts` and `app/src/types/survey.ts` to:

```ts
export type ItemType = 'short-text' | 'long-text' | 'number' | 'single' | 'multi' | 'date' | 'multi-field';

export interface SubField {
  id: string;          // e.g. "Q1_1"
  label: string;       // e.g. "Last Name"
  kind: 'short-text' | 'number';
  min?: number;
  max?: number;
}

export interface Item {
  id: string;
  legacyId?: string;
  section: string;
  type: ItemType;
  required: boolean;
  label: string;
  help?: string;
  choices?: Choice[];
  hasOtherSpecify?: boolean;
  min?: number;
  max?: number;
  subFields?: SubField[];
}
```

(Keep the existing `Choice` and `Section` exports unchanged. The `Section` export only needs to live in `app/src/types/survey.ts`.)

- [ ] **Step 2: Write failing parser test**

Append in `app/scripts/lib/parse-spec.test.ts`:

```ts
  it('parses "short-text ×3" as multi-field with three short-text subfields', () => {
    const row: RowFields = {
      pdf_q: 'Q1',
      legacy_q: 'Q1',
      type: 'short-text ×3',
      required: 'Y',
      label: 'What is your name?',
      choices: 'Last Name / First Name / Middle Initial',
    };
    const { item, unsupported } = normalizeRow(row, 'A');
    expect(unsupported).toBeUndefined();
    expect(item).toMatchObject({
      id: 'Q1',
      type: 'multi-field',
      subFields: [
        { id: 'Q1_1', label: 'Last Name', kind: 'short-text' },
        { id: 'Q1_2', label: 'First Name', kind: 'short-text' },
        { id: 'Q1_3', label: 'Middle Initial', kind: 'short-text' },
      ],
    });
  });

  it('parses "number ×2" as multi-field with two number subfields', () => {
    const row: RowFields = {
      pdf_q: 'Q9',
      legacy_q: 'Q13',
      type: 'number ×2',
      required: 'Y',
      label: 'How many?',
      choices: 'Year(s) / Month(s)',
    };
    const { item } = normalizeRow(row, 'A');
    expect(item).toMatchObject({
      id: 'Q9',
      type: 'multi-field',
      subFields: [
        { id: 'Q9_1', label: 'Year(s)', kind: 'number' },
        { id: 'Q9_2', label: 'Month(s)', kind: 'number' },
      ],
    });
  });
```

- [ ] **Step 3: Run failing test**

Run: `npm test -- scripts/lib/parse-spec.test.ts`
Expected: FAIL — both rows unsupported.

- [ ] **Step 4: Implement parser support**

In `app/scripts/lib/parse-spec.ts`:

(a) Replace the `SUPPORTED_TYPES` constant with one that explicitly does NOT include `×N` keys. We'll detect those via regex.

```ts
const SUPPORTED_TYPES: Record<string, ItemType> = {
  single: 'single',
  'single + specify': 'single',
  'single (1–5)': 'single',
  multi: 'multi',
  'multi + specify': 'multi',
  date: 'date',
  'short-text': 'short-text',
  'long-text': 'long-text',
  number: 'number',
};

const MULTI_FIELD_RE = /^(short-text|number)\s*×\s*(\d+)$/;
```

(b) In `normalizeRow`, before the existing `if (!(rawType in SUPPORTED_TYPES))` guard, add a multi-field branch:

```ts
  const multiFieldMatch = rawType.match(MULTI_FIELD_RE);
  if (multiFieldMatch) {
    const kind = multiFieldMatch[1] as 'short-text' | 'number';
    const count = Number(multiFieldMatch[2]);
    const labels = (row.choices ?? '')
      .split('/')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
    const subFields: SubField[] = [];
    for (let i = 0; i < count; i++) {
      subFields.push({
        id: `${row.pdf_q}_${i + 1}`,
        label: labels[i] ?? `Field ${i + 1}`,
        kind,
      });
    }
    const required = (row.required ?? '').trim() === 'Y';
    const item: Item = {
      id: row.pdf_q,
      section,
      type: 'multi-field',
      required,
      label: row.label ?? '',
      subFields,
    };
    if (row.legacy_q && row.legacy_q !== '—' && row.legacy_q !== '') {
      item.legacyId = row.legacy_q;
    }
    return { item };
  }
```

Make sure to import `SubField` at the top of `parse-spec.ts`:

```ts
import type { Item, ParseResult, Section, UnsupportedItem, ItemType, Choice, SubField } from './types';
```

(c) Remove the now-stale `'multi-field (×N) — handled in M6'` and similar lines from `unsupportedReason` — leave only the truly-unsupported branches (e.g. `section-break`):

```ts
function unsupportedReason(rawType: string): string {
  if (rawType === 'section-break') return 'section break — not a renderable item';
  return `unsupported type "${rawType}" — handled in a later milestone`;
}
```

- [ ] **Step 5: Verify parser tests pass**

Run: `npm test -- scripts/lib/parse-spec.test.ts`
Expected: PASS — both new tests green; existing tests still green.

- [ ] **Step 6: Commit**

```bash
git add app/scripts/lib/types.ts app/src/types/survey.ts app/scripts/lib/parse-spec.ts app/scripts/lib/parse-spec.test.ts
git commit -m "feat(f2-pwa): M6.5 multi-field ItemType in types + parser"
```

---

## Task 6: `multi-field` schema emission + Question rendering

**Files:**
- Modify: `app/scripts/lib/emit-items.ts`
- Modify: `app/scripts/lib/emit-items.test.ts`
- Modify: `app/scripts/lib/emit-schema.ts`
- Modify: `app/scripts/lib/emit-schema.test.ts`
- Modify: `app/src/components/survey/Question.tsx`
- Modify: `app/src/components/survey/Question.test.tsx`

Schema flattens to per-subfield keys (`Q1_1`, `Q1_2`, `Q1_3`). `<Question>` renders N inline labelled inputs.

- [ ] **Step 1: Write failing emit-items test**

Append to `app/scripts/lib/emit-items.test.ts`:

```ts
  it('serialises subFields onto multi-field items', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'A',
          title: 'A',
          items: [
            {
              id: 'Q1',
              section: 'A',
              type: 'multi-field',
              required: true,
              label: 'name',
              subFields: [
                { id: 'Q1_1', label: 'Last', kind: 'short-text' },
                { id: 'Q1_2', label: 'First', kind: 'short-text' },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const out = emitItems(result);
    expect(out).toContain("subFields: [{ id: 'Q1_1', label: 'Last', kind: 'short-text' }, { id: 'Q1_2', label: 'First', kind: 'short-text' }]");
  });
```

- [ ] **Step 2: Run failing test**

Run: `npm test -- scripts/lib/emit-items.test.ts`
Expected: FAIL — `subFields` not serialised.

- [ ] **Step 3: Extend `emitItem` in emit-items.ts**

In `app/scripts/lib/emit-items.ts`, inside `emitItem`, add (above `if (item.choices)`):

```ts
  if (item.subFields) {
    const subFieldsLiteral = item.subFields
      .map((sf) => {
        const parts = [
          `id: '${sf.id}'`,
          `label: ${quote(sf.label)}`,
          `kind: '${sf.kind}'`,
        ];
        if (sf.min !== undefined) parts.push(`min: ${sf.min}`);
        if (sf.max !== undefined) parts.push(`max: ${sf.max}`);
        return `{ ${parts.join(', ')} }`;
      })
      .join(', ');
    fields.push(`subFields: [${subFieldsLiteral}]`);
  }
```

- [ ] **Step 4: Verify emit-items test passes**

Run: `npm test -- scripts/lib/emit-items.test.ts`
Expected: PASS.

- [ ] **Step 5: Write failing emit-schema test**

Append to `app/scripts/lib/emit-schema.test.ts`:

```ts
  it('flattens multi-field items into per-subfield schema entries', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'A',
          title: 'A',
          items: [
            {
              id: 'Q1',
              section: 'A',
              type: 'multi-field',
              required: true,
              label: 'name',
              subFields: [
                { id: 'Q1_1', label: 'Last', kind: 'short-text' },
                { id: 'Q1_2', label: 'First', kind: 'short-text' },
              ],
            },
            {
              id: 'Q9',
              section: 'A',
              type: 'multi-field',
              required: false,
              label: 'how long',
              subFields: [
                { id: 'Q9_1', label: 'Y', kind: 'number' },
                { id: 'Q9_2', label: 'M', kind: 'number' },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const out = emitSchema(result);
    expect(out).toContain('Q1_1: z.string().min(1)');
    expect(out).toContain('Q1_2: z.string().min(1)');
    expect(out).toContain('Q9_1: z.coerce.number().optional()');
    expect(out).toContain('Q9_2: z.coerce.number().optional()');
  });
```

- [ ] **Step 6: Run failing test**

Run: `npm test -- scripts/lib/emit-schema.test.ts`
Expected: FAIL.

- [ ] **Step 7: Extend `emitFieldEntries` in emit-schema.ts**

In `app/scripts/lib/emit-schema.ts`, replace `emitFieldEntries`:

```ts
function emitFieldEntries(item: Item): string[] {
  if (item.type === 'multi-field' && item.subFields) {
    return item.subFields.map((sf) => {
      const schema = sf.kind === 'short-text'
        ? (item.required ? 'z.string().min(1)' : 'z.string().optional()')
        : (() => {
            let expr = 'z.coerce.number()';
            if (sf.min !== undefined) expr += `.min(${sf.min})`;
            if (sf.max !== undefined) expr += `.max(${sf.max})`;
            if (!item.required) expr += '.optional()';
            return expr;
          })();
      return `${fieldKey(sf.id)}: ${schema},`;
    });
  }
  const key = fieldKey(item.id);
  const primary = `${key}: ${fieldSchema(item)},`;
  if (item.hasOtherSpecify) {
    return [primary, `${fieldKey(`${item.id}_other`)}: z.string().optional(),`];
  }
  return [primary];
}
```

`fieldSchema` will now never receive a `multi-field` item, so its existing `switch` is fine (no case needed).

- [ ] **Step 8: Verify emit-schema test passes**

Run: `npm test -- scripts/lib/emit-schema.test.ts`
Expected: PASS.

- [ ] **Step 9: Write failing Question test**

Append in `app/src/components/survey/Question.test.tsx`:

```tsx
describe('Question — multi-field', () => {
  const item: Item = {
    id: 'Q1',
    section: 'A',
    type: 'multi-field',
    required: true,
    label: 'What is your name?',
    subFields: [
      { id: 'Q1_1', label: 'Last Name', kind: 'short-text' },
      { id: 'Q1_2', label: 'First Name', kind: 'short-text' },
      { id: 'Q1_3', label: 'Middle Initial', kind: 'short-text' },
    ],
  };

  it('renders one input per subField, labelled by the subField label', () => {
    render(<Harness item={item} />);
    expect(screen.getByLabelText('Last Name')).toBeInTheDocument();
    expect(screen.getByLabelText('First Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Middle Initial')).toBeInTheDocument();
  });

  it('uses input type=number for number subFields', () => {
    const numItem: Item = {
      id: 'Q9',
      section: 'A',
      type: 'multi-field',
      required: true,
      label: 'How many?',
      subFields: [
        { id: 'Q9_1', label: 'Years', kind: 'number' },
        { id: 'Q9_2', label: 'Months', kind: 'number' },
      ],
    };
    render(<Harness item={numItem} />);
    expect(screen.getByLabelText('Years')).toHaveAttribute('type', 'number');
    expect(screen.getByLabelText('Months')).toHaveAttribute('type', 'number');
  });
});
```

- [ ] **Step 10: Run failing test**

Run: `npm test -- src/components/survey/Question.test.tsx`
Expected: FAIL — switch falls through.

- [ ] **Step 11: Implement Question multi-field branch**

In `app/src/components/survey/Question.tsx`, after the `case 'date':` block, add:

```tsx
    case 'multi-field':
      return (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {item.subFields?.map((sf) => (
            <div key={sf.id} className="flex flex-col gap-1">
              <label htmlFor={sf.id} className="text-xs text-muted-foreground">
                {sf.label}
              </label>
              <input
                id={sf.id}
                type={sf.kind === 'number' ? 'number' : 'text'}
                className="rounded border border-input bg-background px-3 py-2"
                {...register(sf.id)}
              />
            </div>
          ))}
        </div>
      );
```

- [ ] **Step 12: Verify Question test passes**

Run: `npm test -- src/components/survey/Question.test.tsx`
Expected: PASS.

- [ ] **Step 13: Commit**

```bash
git add app/scripts/lib/emit-items.ts app/scripts/lib/emit-items.test.ts app/scripts/lib/emit-schema.ts app/scripts/lib/emit-schema.test.ts app/src/components/survey/Question.tsx app/src/components/survey/Question.test.tsx
git commit -m "feat(f2-pwa): M6.6 multi-field schema flattening + N-input rendering"
```

---

## Task 7: `grid-single` parser widening

**Files:**
- Modify: `app/scripts/lib/parse-spec.ts`
- Modify: `app/scripts/lib/parse-spec.test.ts`

Per spec inspection, all `grid-single` rows in F2-Spec.md (Q74, Q75, Q76) already inline their full choice set (`Never · Rarely · Sometimes · Often · Always`). Treat them as plain `single` items at MVP — matrix grouping rendering is deferred to M11 polish.

- [ ] **Step 1: Write failing test**

Append in `app/scripts/lib/parse-spec.test.ts`:

```ts
  it('treats "grid-single" as a single with the inline choice set', () => {
    const row: RowFields = {
      pdf_q: 'Q74',
      legacy_q: '—',
      type: 'grid-single',
      required: 'Y',
      label: 'How often do you charge?',
      choices: 'Never · Rarely · Sometimes · Often · Always',
    };
    const { item, unsupported } = normalizeRow(row, 'G');
    expect(unsupported).toBeUndefined();
    expect(item).toMatchObject({
      id: 'Q74',
      type: 'single',
      choices: [
        { label: 'Never', value: 'Never' },
        { label: 'Rarely', value: 'Rarely' },
        { label: 'Sometimes', value: 'Sometimes' },
        { label: 'Often', value: 'Often' },
        { label: 'Always', value: 'Always' },
      ],
    });
  });
```

- [ ] **Step 2: Run failing test**

Run: `npm test -- scripts/lib/parse-spec.test.ts`
Expected: FAIL.

- [ ] **Step 3: Add `grid-single` to SUPPORTED_TYPES**

In `app/scripts/lib/parse-spec.ts`:

```ts
const SUPPORTED_TYPES: Record<string, ItemType> = {
  single: 'single',
  'single + specify': 'single',
  'single (1–5)': 'single',
  'grid-single': 'single',
  multi: 'multi',
  'multi + specify': 'multi',
  date: 'date',
  'short-text': 'short-text',
  'long-text': 'long-text',
  number: 'number',
};
```

- [ ] **Step 4: Verify test passes**

Run: `npm test -- scripts/lib/parse-spec.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/scripts/lib/parse-spec.ts app/scripts/lib/parse-spec.test.ts
git commit -m "feat(f2-pwa): M6.7 grid-single widened to single (matrix render deferred)"
```

---

## Task 8: Regenerate generated files + sanity-check coverage

**Files:**
- Modify: `app/src/generated/items.ts` (regen)
- Modify: `app/src/generated/schema.ts` (regen)

After Tasks 1–7, the generator should accept everything in `F2-Spec.md` except `section-break` rows (which are layout markers, not items).

- [ ] **Step 1: Run the generator**

Run: `cd app && npm run generate`
Expected stdout includes `generator: 11 section(s), 117 supported item(s), 0 unsupported.` (Item count must match the row count in the spec; if any row is reported unsupported, dig in before continuing.)

If you see unsupported items reported, read the actual row in `app/spec/F2-Spec.md`, identify which type Tasks 1–7 missed, and patch before moving on. Do not ship generated files with `// unsupported` trailers in them.

- [ ] **Step 2: Verify TS compiles**

Run: `cd app && npm run typecheck`
Expected: PASS, no errors.

- [ ] **Step 3: Run full test suite**

Run: `cd app && npm test -- --run`
Expected: all suites green.

- [ ] **Step 4: Commit**

```bash
git add app/src/generated/items.ts app/src/generated/schema.ts
git commit -m "chore(f2-pwa): M6.8 regenerate items + schemas for full instrument"
```

---

## Task 9: Wire all 11 sections in MultiSectionForm

**Files:**
- Modify: `app/src/components/survey/MultiSectionForm.tsx`
- Modify: `app/src/components/survey/MultiSectionForm.test.tsx`

Currently only A, B, C are mounted. After Task 8 the generator emits 11 section consts (A, B, C, D, E1, E2, F, G, H, I, J) and matching schemas — extend the `SECTIONS` array.

- [ ] **Step 1: Write failing test**

Append in `app/src/components/survey/MultiSectionForm.test.tsx` inside the existing `describe`:

```tsx
  it('exposes all 11 sections via the progress bar total', async () => {
    render(
      <MultiSectionForm
        initialValues={{}}
        onAutosave={() => {}}
        onSubmit={() => {}}
      />,
    );
    expect(await screen.findByText(/section 1 of 11/i)).toBeInTheDocument();
  });
```

(If `ProgressBar` does not currently render `Section X of Y` text verbatim, inspect `app/src/components/survey/ProgressBar.tsx` and update the assertion to match the actual rendered string — keep the spirit: total === 11.)

- [ ] **Step 2: Run failing test**

Run: `npm test -- src/components/survey/MultiSectionForm.test.tsx`
Expected: FAIL — total currently 3.

- [ ] **Step 3: Wire all sections**

In `app/src/components/survey/MultiSectionForm.tsx`, replace the imports and `SECTIONS` constant:

```tsx
import {
  sectionA, sectionB, sectionC, sectionD, sectionE1, sectionE2,
  sectionF, sectionG, sectionH, sectionI, sectionJ,
} from '@/generated/items';
import {
  sectionASchema, sectionBSchema, sectionCSchema, sectionDSchema,
  sectionE1Schema, sectionE2Schema, sectionFSchema, sectionGSchema,
  sectionHSchema, sectionISchema, sectionJSchema,
} from '@/generated/schema';

const SECTIONS: SectionConfig[] = [
  { id: 'A',  section: sectionA,  schema: sectionASchema },
  { id: 'B',  section: sectionB,  schema: sectionBSchema },
  { id: 'C',  section: sectionC,  schema: sectionCSchema },
  { id: 'D',  section: sectionD,  schema: sectionDSchema },
  { id: 'E1', section: sectionE1, schema: sectionE1Schema },
  { id: 'E2', section: sectionE2, schema: sectionE2Schema },
  { id: 'F',  section: sectionF,  schema: sectionFSchema },
  { id: 'G',  section: sectionG,  schema: sectionGSchema },
  { id: 'H',  section: sectionH,  schema: sectionHSchema },
  { id: 'I',  section: sectionI,  schema: sectionISchema },
  { id: 'J',  section: sectionJ,  schema: sectionJSchema },
];
```

- [ ] **Step 4: Verify test passes**

Run: `npm test -- src/components/survey/MultiSectionForm.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/src/components/survey/MultiSectionForm.tsx app/src/components/survey/MultiSectionForm.test.tsx
git commit -m "feat(f2-pwa): M6.9 wire all 11 sections (A–J) in MultiSectionForm"
```

---

## Task 10: Skip-logic predicates for sections D–J

**Files:**
- Modify: `app/src/lib/skip-logic.ts`
- Modify: `app/src/lib/skip-logic.test.ts`

Source-of-truth gates / skip rules live in `deliverables/F2/F2-Skip-Logic.md` and the per-row `gate` / `skip` columns in `app/spec/F2-Spec.md`. **Read both** before adding predicates — only encode what the spec actually says. Generation from `F2-Skip-Logic.md` is M7's job; M6 just hand-codes the predicates needed to make the form fillable for at least the default doctor/dentist persona.

- [ ] **Step 1: Read the skip-logic source**

```bash
cat deliverables/F2/F2-Skip-Logic.md
grep -E '^\| Q[0-9].*conditional' deliverables/F2/PWA/app/spec/F2-Spec.md
```

Build a per-section list of (item, predicate) pairs from the `gate` and `skip` columns.

- [ ] **Step 2: Write failing tests for at least the most-impactful gates**

Append inside `describe('shouldShow')` in `app/src/lib/skip-logic.test.ts`:

```ts
  describe('Section G (KAP on Fees) — physician/dentist gate', () => {
    it('hides Q56 when Q5 role is not Physician/Doctor or Dentist', () => {
      expect(shouldShow('G', 'Q56', { Q5: 'Nurse' })).toBe(false);
    });
    it('shows Q56 when Q5 is Physician/Doctor', () => {
      expect(shouldShow('G', 'Q56', { Q5: 'Physician/Doctor' })).toBe(true);
    });
    it('shows Q56 when Q5 is Dentist', () => {
      expect(shouldShow('G', 'Q56', { Q5: 'Dentist' })).toBe(true);
    });
  });

  describe('Section E2 (GAMOT) — facility-type gate from Section A', () => {
    it('hides Q46 when Q5 role is Barangay Health Worker (not eligible)', () => {
      expect(shouldShow('E2', 'Q46', { Q5: 'Barangay Health Worker' })).toBe(false);
    });
  });
```

(Add additional tests as you encode each gate. Aim for one test per gating dimension, not one per item.)

- [ ] **Step 3: Run failing tests**

Run: `npm test -- src/lib/skip-logic.test.ts`
Expected: FAIL — predicates missing.

- [ ] **Step 4: Implement the predicates**

In `app/src/lib/skip-logic.ts`, extend `predicates` with the new sections. Example (extend per actual spec — this is the *shape* you're filling in):

```ts
const PHYSICIAN_DENTIST = new Set(['Physician/Doctor', 'Dentist']);

const predicates: Record<string, Record<string, Predicate>> = {
  A: {
    Q6: (v) => typeof v.Q5 === 'string' && ROLES_WITH_SPECIALTY.has(v.Q5),
    Q8: (v) => v.Q7 === 'Yes',
  },
  B: {
    Q14: (v) => typeof v.Q13 === 'string' && v.Q13.startsWith('Yes'),
  },
  C: {
    Q31: (v) => v.Q30 === 'Yes',
    Q32: (v) => v.Q30 === 'Yes',
    Q33: (v) => v.Q30 === 'No',
    Q35: (v) => v.Q34 === 'Yes',
  },
  D: {
    // example: Q42 only if Q40 = "I have heard of it"
  },
  E1: {
    // facility-type-gated section — re-check spec preamble
  },
  E2: {
    Q46: (v) => typeof v.Q5 === 'string' && v.Q5 !== 'Barangay Health Worker',
  },
  G: {
    Q56: (v) => typeof v.Q5 === 'string' && PHYSICIAN_DENTIST.has(v.Q5),
    // …repeat for the rest of Section G's physician/dentist-only items
  },
  H: {},
  I: {},
  J: {},
};
```

(Encode the actual gates from the spec. The empty objects above are placeholders for sections where the spec's `gate` / `skip` columns are blank — drop those keys entirely if there's nothing to encode.)

- [ ] **Step 5: Verify tests pass**

Run: `npm test -- src/lib/skip-logic.test.ts`
Expected: PASS.

- [ ] **Step 6: Verify the full app test suite still passes**

Run: `npm test -- --run`
Expected: all 22+ suites green.

- [ ] **Step 7: Commit**

```bash
git add app/src/lib/skip-logic.ts app/src/lib/skip-logic.test.ts
git commit -m "feat(f2-pwa): M6.10 hand-coded skip predicates for sections D–J"
```

---

## Task 11: NEXT.md → M7 + final verification

**Files:**
- Modify: `app/NEXT.md`

After Task 10 the entire instrument is fillable end-to-end. The natural next milestone per spec §11.1 is **M7 — Validation + 20 POST cross-field rules** (15–20 h), followed by **M8 — Facility list + enrollment flow** (8–10 h).

- [ ] **Step 1: Run the final verification trio**

Run: `cd app && npm test -- --run && npm run typecheck && npm run build`
Expected: tests green, tsc clean, Vite build emits `dist/` with the precache manifest.

- [ ] **Step 2: Live smoke (manual)**

`npm run dev`, walk all 11 sections in the browser. Confirm:
- Multi-select questions accept multiple checkboxes.
- The single date question (Q31, Section C) renders a date picker.
- Q1 renders three name fields side-by-side.
- The progress bar advances 1 of 11 → 11 of 11.
- Submission flow still drains via M5 sync.

- [ ] **Step 3: Rewrite `app/NEXT.md`**

Replace the file's contents with:

```markdown
# Next step (future-Carl)

**Last milestone shipped:** M6 — Full instrument scaffolding. All 11 sections (A–J) and ~117 items render via the generator. New ItemTypes added: `multi`, `date`, `multi-field`. `single (1–5)` Likert and `grid-single` widened into the existing `single` path. Skip-logic predicates hand-coded for D–J.

**Next milestone:** M7 — Validation + 20 POST cross-field rules. 15–20h per spec §11.1.

**Before starting M7:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §6 (Generator), the `F2-Validation.md` raw spec at `deliverables/F2/F2-Validation.md`, and `F2-Cross-Field.md` at `deliverables/F2/F2-Cross-Field.md`.
2. Target: per-item validation rules emit into `src/generated/schema.ts` (replacing the current minimal `min(1)` defaults), and 20 cross-field POST rules emit into a new `src/generated/cross-field.ts` consumed by a `<Review>` page or pre-submit hook.
3. Expected deliverable: `../2026-04-18-implementation-plan-M7-validation.md`.

**M6 technical debt to address in later milestones:**

- Skip-logic is still hand-coded in `src/lib/skip-logic.ts`. Generation from `F2-Skip-Logic.md` is part of M7 alongside validation.
- Grid-single items render as a flat list of single-choice questions, not as a true matrix. Polish in M11.
- Multi-field schema requires every subfield (`Q1_1`, `Q1_2`, `Q1_3`) — there is no parent `Q1` aggregator. Storage shape may need rework when M10's admin dashboard wants per-question rollups.
- No locale bundles emitted yet (`public/locales/en.json`, `public/locales/fil.json`) — that is M9's job.

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build` — confirm M6 still green.
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build` — confirm M4 still green.
- Open `../2026-04-17-design-spec.md` §6 and `deliverables/F2/F2-Validation.md` to re-orient for M7.
```

- [ ] **Step 4: Commit**

```bash
git add app/NEXT.md
git commit -m "chore(f2-pwa): M6.11 NEXT.md → M7 (validation + cross-field)"
```

---

## Self-Review

**Spec coverage** — `2026-04-17-design-spec.md` §11.1 row M6 promises "all 124 items, 35+ sections" and "all items fillable" (Apr 20 rev; was "all 114 items, 35 sections" under the Apr 08 draft):
- "All items fillable" — Tasks 1–7 add every missing ItemType; Task 8 regenerates, Task 9 wires every section. ✓ **Apr 20 note**: Q108 is a PDF numbering gap — no item exists; generator must not emit a Q108 column. See `F2-Cross-Field.md` SCHEMA-01.
- "35+ sections" — actual `F2-Spec.md` has 11 top-level lettered sections (A, B, C, D, E1, E2, F, G, H, I, J); the Apr 20 section-graph in `F2-Skip-Logic.md` subdivides these into 35+ routing sub-sections. The roadmap figure originally meant routing sub-sections. Aligning silently to actual content per `feedback_align_dont_flag.md`.
- "Generator robustness" — Tasks 1, 2, 4, 5, 7 all extend the generator with TDD coverage. ✓
- "Large-form perf" — implicit; no perf regression test, but live smoke in Task 11.2 will catch obvious jank. Deeper perf work is M11.

**Placeholder scan** — Task 10 contains a "fill in per the spec" instruction for the skip predicates. This is intentional — the spec's `gate`/`skip` columns are the authoritative source and the engineer must read them; the alternative is to inline the entire spec into this plan. The Step 1 + Step 4 example structure shows the *shape* and *style* concretely, with one fully-worked predicate per gating dimension (role gate, facility gate). Acceptable.

**Type consistency** — `ItemType` and `Item` are defined identically in `app/scripts/lib/types.ts` (compile-time) and `app/src/types/survey.ts` (runtime). Tasks 2, 4, and 5 all update both files in lockstep. `SubField` is exported from both with the same shape. Field names (`subFields`, `kind`, `hasOtherSpecify`, `isOtherSpecify`) are stable across all tasks.

---

## Execution Handoff

Plan complete and saved to `deliverables/F2/PWA/2026-04-18-implementation-plan-M6-full-instrument.md`. Per documented preference (`feedback_inline_over_subagent.md`), inline execution will follow when you say "next".

## Decision gates past M6 (added 2026-04-21, Frame #2)

M6 is the **last milestone that should proceed on assumption.** Under Frame #2 (PWA as the long-term F2 target, not a hedge), M7+ compounds on architectural choices that cannot be deferred indefinitely. Before M7 starts, the following must be resolved:

1. **Per-HCW enrollment token scheme** (gates M4/M8) — email-link? short-code? OAuth to UP Google / ASPSI Google? Affects the Apps Script backend shape, the PWA's AuthContext, and the link-distribution UX.
2. **Offline conflict-resolution policy** (gates M5) — when two devices (e.g., tablet + phone) submit the same HCW's draft, which wins? Server timestamp? Device-local last-write? Block the second with a 409? Determines the sync orchestrator's state machine.
3. **Facility master list source-of-truth + refresh cadence** (gates M8) — the design spec §6.1 names `spec/FacilityMasterList.json` as "cached from API," but no API owner exists yet. ASPSI field team? Data team? Quarterly refresh from PSA + ASPSI overrides?

These are Frame-#2-only decisions (they were irrelevant under the Forms-primary frame). Surface them as a single ASPSI decision batch before M7 kicks off. If answers haven't landed when M6 ships, pause the PWA and flip back to other-front work rather than guessing and rebuilding.
