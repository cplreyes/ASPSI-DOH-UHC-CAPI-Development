# F2 PWA — M7 Validation + Cross-Field Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten per-item validation (conditional-required `_other` follow-ups) and add a Review screen surfacing cross-field warnings (PROF-01..04, GATE-02, GATE-05) before final submit.

**Architecture:** Extend `emit-schema.ts` to append a `.superRefine` block per section schema that enforces "if parent choice = the `isOtherSpecify` value, then `_other` must be non-empty" for every `hasOtherSpecify` item (33 across the instrument). Add a hand-written `src/lib/cross-field.ts` module that evaluates the six PWA-applicable cross-field rules from `F2-Cross-Field.md` against `FormValues` and returns an array of warnings. Insert a new `ReviewSection` component between Section J and the final `onSubmit` — read-only answer summary + warning panel + Submit button.

**Tech Stack:** TypeScript generator (tsx) · Zod 3 (`.superRefine`) · React 18 + react-hook-form · Vitest 4 + @testing-library/react.

**Spec section reference:** `2026-04-17-design-spec.md` §11.1 row M7, §6 (Generator Pattern); `deliverables/F2/F2-Validation.md` (per-item rules); `deliverables/F2/F2-Cross-Field.md` (POST rules — only the subset evaluable without M8 enrollment context lands here).

**Out of scope (deferred):**
- 14+ cross-field rules that depend on `facility_type`, `facility_has_bucas`, `facility_has_gamot`, `consent`, `respondent_email`, `submission_started_at`, `response_source` — these need M8 enrollment fields and run server-side per the F2-Cross-Field architecture.
- Max-character limits on free-text fields (Q36, Q73, Q77, Q80 = 1000 chars; Q1 names = 50/5 chars). Nice-to-have — defer to M11 hardening unless desk-tests show drop-off from runaway text.
- Section G role-gating across the whole section (currently Section G items render even for non-doctors). M7 surfaces this as a GATE-02 warning on the review screen; full prevention waits for M8 enrollment + cross-section navigation.

---

## File Structure (decomposition)

| File | Responsibility | Status |
|---|---|---|
| `app/scripts/lib/emit-schema.ts` | append `.superRefine` after each `z.object({...})` enforcing `_other` conditional-required | modify |
| `app/scripts/lib/emit-schema.test.ts` | unit tests for the new emission | modify |
| `app/src/generated/schema.ts` | regenerated | regen |
| `app/src/lib/cross-field.ts` | NEW: pure cross-field rule evaluators returning `Warning[]` | create |
| `app/src/lib/cross-field.test.ts` | NEW: unit tests | create |
| `app/src/components/survey/ReviewSection.tsx` | NEW: read-only answer summary + warnings + Submit button | create |
| `app/src/components/survey/ReviewSection.test.tsx` | NEW: render + warning surfacing tests | create |
| `app/src/components/survey/MultiSectionForm.tsx` | route `index === SECTIONS.length` to `<ReviewSection>` instead of Section render | modify |
| `app/src/components/survey/MultiSectionForm.test.tsx` | extend last test to cover review screen + submit | modify |
| `app/NEXT.md` | rewrite to point at M8 (facility list + enrollment) | modify |

---

## Task 1: Generator emits `.superRefine` for `_other` conditional-required

**Files:**
- Modify: `app/scripts/lib/emit-schema.ts`
- Modify: `app/scripts/lib/emit-schema.test.ts`

The current emitter writes `Q5_other: z.string().optional()` for every `hasOtherSpecify` item. We need it to actually become required when the parent choice equals the `isOtherSpecify` choice value. Implement as a single `.superRefine` chained after each section's `z.object({...})`. Multi-select items match via `.includes(otherValue)`; single-select items match via strict equality.

- [ ] **Step 1: Add a failing test for single+specify refinement**

Append to `app/scripts/lib/emit-schema.test.ts` inside `describe('emitSchema', () => { ... })`:

```ts
  it('emits a .superRefine that requires _other when parent single equals the other-specify value', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'A',
          title: 'A',
          items: [
            {
              id: 'Q2',
              section: 'A',
              type: 'single',
              required: true,
              hasOtherSpecify: true,
              label: 'Employment?',
              choices: [
                { label: 'Regular', value: 'Regular' },
                { label: 'Other, specify', value: 'Other, specify', isOtherSpecify: true },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const code = emitSchema(result);
    expect(code).toContain('.superRefine((data, ctx) => {');
    expect(code).toContain("if (data.Q2 === 'Other, specify'");
    expect(code).toContain("path: ['Q2_other']");
  });

  it('emits a .superRefine clause that uses .includes for multi+specify parents', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'B',
          title: 'B',
          items: [
            {
              id: 'Q21',
              section: 'B',
              type: 'multi',
              required: true,
              hasOtherSpecify: true,
              label: 'Which?',
              choices: [
                { label: 'Salary', value: 'Salary' },
                { label: 'Other (specify)', value: 'Other (specify)', isOtherSpecify: true },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const code = emitSchema(result);
    expect(code).toContain("Array.isArray(data.Q21) && data.Q21.includes('Other (specify)')");
    expect(code).toContain("path: ['Q21_other']");
  });

  it('does not emit .superRefine when the section has no hasOtherSpecify items', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'H',
          title: 'H',
          items: [
            { id: 'Q88', section: 'H', type: 'single', required: true, label: 'L', choices: [{ label: 'A', value: 'A' }] },
          ],
        },
      ],
      unsupported: [],
    };
    expect(emitSchema(result)).not.toContain('.superRefine');
  });
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `cd app && npx vitest run scripts/lib/emit-schema.test.ts`
Expected: 3 new tests fail (the existing 12 still pass).

- [ ] **Step 3: Implement `.superRefine` emission in emit-schema.ts**

Replace `emitSectionSchema` and add a helper. The full updated file content:

```ts
import type { Choice, Item, ParseResult, Section } from './types';

export function emitSchema(result: ParseResult): string {
  const header = [
    '// AUTOGENERATED — do not edit by hand.',
    '// Regenerate via `npm run generate`.',
    "import { z } from 'zod';",
    '',
  ].join('\n');

  const body = result.sections.map(emitSectionSchema).join('\n\n');
  return [header, body, ''].join('\n');
}

function emitSectionSchema(section: Section): string {
  const fieldLines = section.items.flatMap(emitFieldEntries).map((l) => `  ${l}`);
  const objectLiteral = `z.object({\n${fieldLines.join('\n')}\n})`;
  const refinement = emitOtherSpecifyRefinement(section);
  const expr = refinement ? `${objectLiteral}${refinement}` : objectLiteral;
  const constName = `section${section.id}Schema`;
  const typeName = `Section${section.id}Values`;
  return [
    `export const ${constName} = ${expr};`,
    `export type ${typeName} = z.infer<typeof ${constName}>;`,
  ].join('\n');
}

function emitOtherSpecifyRefinement(section: Section): string | null {
  const clauses: string[] = [];
  for (const item of section.items) {
    if (!item.hasOtherSpecify || !item.choices) continue;
    const otherChoice = item.choices.find((c) => c.isOtherSpecify);
    if (!otherChoice) continue;
    const parentKey = jsAccess(item.id);
    const otherKey = jsAccess(`${item.id}_other`);
    const otherValue = otherChoice.value.replace(/'/g, "\\'");
    const condition =
      item.type === 'multi'
        ? `Array.isArray(data${parentKey}) && data${parentKey}.includes('${otherValue}')`
        : `data${parentKey} === '${otherValue}'`;
    const filledCheck = `typeof data${otherKey} === 'string' && data${otherKey}.trim().length > 0`;
    const pathLiteral = `['${item.id}_other']`;
    clauses.push(
      [
        `  if (${condition} && !(${filledCheck})) {`,
        `    ctx.addIssue({ code: z.ZodIssueCode.custom, path: ${pathLiteral}, message: 'Please specify' });`,
        `  }`,
      ].join('\n'),
    );
  }
  if (clauses.length === 0) return null;
  return `.superRefine((data, ctx) => {\n${clauses.join('\n')}\n})`;
}

function jsAccess(id: string): string {
  return /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(id) ? `.${id}` : `['${id}']`;
}

function emitFieldEntries(item: Item): string[] {
  if (item.type === 'multi-field' && item.subFields) {
    return item.subFields.map((sf) => {
      const schema =
        sf.kind === 'short-text'
          ? item.required
            ? 'z.string().min(1)'
            : 'z.string().optional()'
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

function fieldKey(id: string): string {
  return /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(id) ? id : `'${id}'`;
}

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
    case 'date': {
      const base = String.raw`z.string().regex(/^\d{4}-\d{2}-\d{2}$/)`;
      return item.required ? base : `${base}.optional()`;
    }
    case 'multi-field':
      throw new Error(
        `multi-field items must be handled in emitFieldEntries, not fieldSchema (item ${item.id})`,
      );
  }
}
```

The `Choice` import becomes unused if you don't end up touching choice serialization here; if TypeScript complains, drop it from the import line.

- [ ] **Step 4: Run emit-schema tests to verify they pass**

Run: `cd app && npx vitest run scripts/lib/emit-schema.test.ts`
Expected: all 15 tests pass (12 existing + 3 new).

- [ ] **Step 5: Regenerate schema.ts and items.ts**

Run: `cd app && npm run generate`
Expected: `generator: 11 section(s), 117 supported item(s), 0 unsupported.`

- [ ] **Step 6: Spot-check the regenerated schema**

Run: `cd app && head -30 src/generated/schema.ts`
Expected: `sectionASchema` ends with `}).superRefine((data, ctx) => { ... })` containing checks for `Q2`, `Q5`, `Q6` against their respective other-specify choice values.

- [ ] **Step 7: Run full test suite to confirm nothing regressed**

Run: `cd app && npx vitest run`
Expected: 176/176 still pass (the schema is more strict but all existing test inputs satisfy the new constraint or use values that don't equal the other-specify choice).

- [ ] **Step 8: Add a regression test for the new constraint at the form layer**

Append to `app/src/components/survey/MultiSectionForm.test.tsx` inside the existing `describe('<MultiSectionForm>', () => { ... })`:

```ts
  it('blocks Next when Q5 is "Other (specify)" but Q5_other is empty', async () => {
    const user = userEvent.setup();
    render(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes',
          Q1_2: 'Carl',
          Q1_3: 'P',
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q7: 'No',
          Q9_1: 3,
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
        }}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    await user.click(screen.getByLabelText('Other (specify)'));
    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByRole('heading', { name: /Section A/ })).toBeInTheDocument();
  });
```

- [ ] **Step 9: Run the form test to verify it passes**

Run: `cd app && npx vitest run src/components/survey/MultiSectionForm.test.tsx`
Expected: 5/5 pass (4 existing + 1 new).

- [ ] **Step 10: Commit**

```bash
git add app/scripts/lib/emit-schema.ts app/scripts/lib/emit-schema.test.ts app/src/generated/schema.ts app/src/generated/items.ts app/src/components/survey/MultiSectionForm.test.tsx
git commit -m "feat(f2-pwa): M7.1 emit conditional-required _other refinements"
```

---

## Task 2: Cross-field rule module

**Files:**
- Create: `app/src/lib/cross-field.ts`
- Create: `app/src/lib/cross-field.test.ts`

Six PWA-applicable rules from `F2-Cross-Field.md`:

| ID | Description | Severity |
|---|---|---|
| PROF-01 | Tenure (Q9_1 years) > age (Q4) − 15 | warn |
| PROF-02 | Q5 ∉ {Physician/Doctor, Dentist} AND Q6 ≠ "No specialty" | warn |
| PROF-03 | Derive `employment_class` from Q11 (≥8 → full-time, else part-time) | info |
| PROF-04 | Q10 × Q11 > 80 weekly hours | warn |
| GATE-02 | Q5 ∉ doctor/dentist AND any of Q56..Q80 has a value | clean |
| GATE-05 | Q5 ∉ {Administrator, Physician/Doctor, Physician assistant, Nurse, Midwife, Dentist} AND any of Q27..Q42 has a value | clean |

`BUCKET-CD` = the six roles in PROF-02's complement plus dentists/admins per F2-Cross-Field group 2 — same set already in `skip-logic.ts` as `ROLES_WITH_SPECIALTY`. Reuse intent inline; do not couple modules yet.

- [ ] **Step 1: Write `app/src/lib/cross-field.test.ts`**

```ts
import { describe, it, expect } from 'vitest';
import { evaluateCrossField, type Warning } from './cross-field';

describe('evaluateCrossField', () => {
  it('returns no warnings on a clean nurse profile', () => {
    expect(evaluateCrossField({ Q4: 30, Q5: 'Nurse', Q9_1: 5, Q10: 5, Q11: 8 })).toEqual([]);
  });

  it('flags PROF-01 when tenure exceeds age − 15', () => {
    const out = evaluateCrossField({ Q4: 25, Q5: 'Nurse', Q9_1: 15 });
    expect(out.map((w) => w.id)).toContain('PROF-01');
  });

  it('flags PROF-02 when a non-doctor reports a specialty', () => {
    const out = evaluateCrossField({ Q5: 'Nurse', Q6: 'Pediatrics' });
    expect(out.map((w) => w.id)).toContain('PROF-02');
  });

  it('does not flag PROF-02 when Q6 is "No specialty"', () => {
    const out = evaluateCrossField({ Q5: 'Nurse', Q6: 'No specialty' });
    expect(out.map((w) => w.id)).not.toContain('PROF-02');
  });

  it('does not flag PROF-02 when Q5 is Physician/Doctor', () => {
    const out = evaluateCrossField({ Q5: 'Physician/Doctor', Q6: 'Pediatrics' });
    expect(out.map((w) => w.id)).not.toContain('PROF-02');
  });

  it('emits PROF-03 derived employment_class=full-time for Q11 >= 8', () => {
    const out = evaluateCrossField({ Q11: 8 });
    const w = out.find((x) => x.id === 'PROF-03');
    expect(w?.severity).toBe('info');
    expect(w?.derived).toEqual({ employment_class: 'full-time' });
  });

  it('emits PROF-03 derived employment_class=part-time for Q11 < 8', () => {
    const w = evaluateCrossField({ Q11: 6 }).find((x) => x.id === 'PROF-03');
    expect(w?.derived).toEqual({ employment_class: 'part-time' });
  });

  it('flags PROF-04 when Q10 × Q11 exceeds 80 weekly hours', () => {
    const out = evaluateCrossField({ Q10: 7, Q11: 13 });
    expect(out.map((w) => w.id)).toContain('PROF-04');
  });

  it('flags GATE-02 when a nurse has answered Section G items', () => {
    const out = evaluateCrossField({ Q5: 'Nurse', Q56: 'Yes' });
    expect(out.map((w) => w.id)).toContain('GATE-02');
  });

  it('does not flag GATE-02 for doctors who answered Section G', () => {
    const out = evaluateCrossField({ Q5: 'Physician/Doctor', Q56: 'Yes' });
    expect(out.map((w) => w.id)).not.toContain('GATE-02');
  });

  it('flags GATE-05 when a pharmacist has answered Section C items', () => {
    const out = evaluateCrossField({ Q5: 'Pharmacist/Dispenser', Q27: 'Yes' });
    expect(out.map((w) => w.id)).toContain('GATE-05');
  });

  it('does not flag GATE-05 for administrators (in BUCKET-CD)', () => {
    const out = evaluateCrossField({ Q5: 'Administrator', Q27: 'Yes' });
    expect(out.map((w) => w.id)).not.toContain('GATE-05');
  });

  it('warning has a human-readable message and lists involved fields', () => {
    const out = evaluateCrossField({ Q4: 25, Q5: 'Nurse', Q9_1: 15 });
    const prof01 = out.find((w): w is Warning => w.id === 'PROF-01');
    expect(prof01?.message).toMatch(/tenure/i);
    expect(prof01?.fields).toEqual(['Q4', 'Q9_1']);
  });
});
```

- [ ] **Step 2: Run the new test file to verify failure**

Run: `cd app && npx vitest run src/lib/cross-field.test.ts`
Expected: file fails to import (`./cross-field` does not exist).

- [ ] **Step 3: Create `app/src/lib/cross-field.ts`**

```ts
import type { FormValues } from './skip-logic';

export type Severity = 'info' | 'warn' | 'clean' | 'error';

export interface Warning {
  id: string;
  severity: Severity;
  message: string;
  fields: string[];
  derived?: Record<string, string>;
}

const BUCKET_CD = new Set([
  'Administrator',
  'Physician/Doctor',
  'Physician assistant',
  'Nurse',
  'Midwife',
  'Dentist',
]);

const DOCTOR_DENTIST = new Set(['Physician/Doctor', 'Dentist']);

const SECTION_G_FIELDS = [
  'Q56', 'Q57', 'Q58', 'Q59', 'Q60', 'Q61', 'Q62', 'Q62.1', 'Q63',
  'Q64', 'Q65', 'Q66', 'Q67', 'Q67.1', 'Q68', 'Q69', 'Q70', 'Q71',
  'Q72', 'Q73', 'Q74', 'Q75', 'Q76', 'Q77', 'Q78', 'Q78.1', 'Q79', 'Q80',
];

const SECTION_CD_FIELDS = [
  'Q27', 'Q28', 'Q29', 'Q30', 'Q31', 'Q32', 'Q33', 'Q34', 'Q35', 'Q36',
  'Q37', 'Q38', 'Q39', 'Q40', 'Q41', 'Q42',
];

function isFilled(v: unknown): boolean {
  if (v === undefined || v === null) return false;
  if (typeof v === 'string') return v.trim().length > 0;
  if (Array.isArray(v)) return v.length > 0;
  return true;
}

function anyFilled(values: FormValues, fields: string[]): boolean {
  return fields.some((f) => isFilled(values[f]));
}

export function evaluateCrossField(values: FormValues): Warning[] {
  const out: Warning[] = [];

  const age = typeof values.Q4 === 'number' ? values.Q4 : Number(values.Q4);
  const tenureYears = typeof values.Q9_1 === 'number' ? values.Q9_1 : Number(values.Q9_1);
  if (Number.isFinite(age) && Number.isFinite(tenureYears) && tenureYears > age - 15) {
    out.push({
      id: 'PROF-01',
      severity: 'warn',
      message: `Reported tenure (${tenureYears} years) is implausible for age ${age}.`,
      fields: ['Q4', 'Q9_1'],
    });
  }

  const role = typeof values.Q5 === 'string' ? values.Q5 : '';
  const specialty = typeof values.Q6 === 'string' ? values.Q6 : '';
  if (role && !DOCTOR_DENTIST.has(role) && specialty && specialty !== 'No specialty') {
    out.push({
      id: 'PROF-02',
      severity: 'warn',
      message: `Role "${role}" does not normally carry a medical specialty (${specialty}).`,
      fields: ['Q5', 'Q6'],
    });
  }

  const hours = typeof values.Q11 === 'number' ? values.Q11 : Number(values.Q11);
  if (Number.isFinite(hours)) {
    out.push({
      id: 'PROF-03',
      severity: 'info',
      message: `Derived employment class: ${hours >= 8 ? 'full-time' : 'part-time'}.`,
      fields: ['Q11'],
      derived: { employment_class: hours >= 8 ? 'full-time' : 'part-time' },
    });
  }

  const days = typeof values.Q10 === 'number' ? values.Q10 : Number(values.Q10);
  if (Number.isFinite(days) && Number.isFinite(hours) && days * hours > 80) {
    out.push({
      id: 'PROF-04',
      severity: 'warn',
      message: `Reported workload (${days} days × ${hours} hrs = ${days * hours} hrs/week) exceeds 80.`,
      fields: ['Q10', 'Q11'],
    });
  }

  if (role && !DOCTOR_DENTIST.has(role) && anyFilled(values, SECTION_G_FIELDS)) {
    out.push({
      id: 'GATE-02',
      severity: 'clean',
      message: `Section G is for physicians and dentists only; answers from "${role}" will be dropped server-side.`,
      fields: ['Q5', ...SECTION_G_FIELDS.filter((f) => isFilled(values[f]))],
    });
  }

  if (role && !BUCKET_CD.has(role) && anyFilled(values, SECTION_CD_FIELDS)) {
    out.push({
      id: 'GATE-05',
      severity: 'clean',
      message: `Sections C and D are for clinical-care roles only; answers from "${role}" will be dropped server-side.`,
      fields: ['Q5', ...SECTION_CD_FIELDS.filter((f) => isFilled(values[f]))],
    });
  }

  return out;
}
```

- [ ] **Step 4: Run cross-field tests to verify they pass**

Run: `cd app && npx vitest run src/lib/cross-field.test.ts`
Expected: 12/12 pass.

- [ ] **Step 5: Commit**

```bash
git add app/src/lib/cross-field.ts app/src/lib/cross-field.test.ts
git commit -m "feat(f2-pwa): M7.2 cross-field rule evaluator (PROF-01..04, GATE-02, GATE-05)"
```

---

## Task 3: ReviewSection component

**Files:**
- Create: `app/src/components/survey/ReviewSection.tsx`
- Create: `app/src/components/survey/ReviewSection.test.tsx`

Read-only summary of every answered question grouped by section, plus a warnings panel and a Submit button. Skipped/empty items are omitted to keep the page short. Warnings show severity, ID, message.

- [ ] **Step 1: Write the failing test**

Create `app/src/components/survey/ReviewSection.test.tsx`:

```tsx
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReviewSection } from './ReviewSection';

describe('<ReviewSection>', () => {
  const baseValues = {
    Q1_1: 'Reyes',
    Q1_2: 'Carl',
    Q1_3: 'P',
    Q2: 'Regular',
    Q3: 'Female',
    Q4: 30,
    Q5: 'Nurse',
    Q7: 'No',
    Q9_1: 3,
    Q9_2: 6,
    Q10: 5,
    Q11: 8,
  };

  it('renders a summary heading and section labels', () => {
    render(
      <ReviewSection values={baseValues} onEdit={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(
      screen.getByRole('heading', { name: /Review your answers/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /Section A — Healthcare Worker Profile/i }),
    ).toBeInTheDocument();
  });

  it('lists answered fields and omits empty ones', () => {
    render(<ReviewSection values={baseValues} onEdit={vi.fn()} onSubmit={vi.fn()} />);
    expect(screen.getByText('Reyes')).toBeInTheDocument();
    expect(screen.getByText('Nurse')).toBeInTheDocument();
    expect(screen.queryByText(/^Q6\b/)).toBeNull();
  });

  it('surfaces a warning when GATE-05 fires (pharmacist + Section C answers)', () => {
    render(
      <ReviewSection
        values={{ ...baseValues, Q5: 'Pharmacist/Dispenser', Q27: 'Yes' }}
        onEdit={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByText(/GATE-05/)).toBeInTheDocument();
    expect(
      screen.getByText(/Sections C and D are for clinical-care roles/i),
    ).toBeInTheDocument();
  });

  it('renders an info-level PROF-03 derivation alongside warnings', () => {
    render(<ReviewSection values={baseValues} onEdit={vi.fn()} onSubmit={vi.fn()} />);
    expect(screen.getByText(/PROF-03/)).toBeInTheDocument();
    expect(screen.getByText(/full-time/i)).toBeInTheDocument();
  });

  it('calls onSubmit when the Submit button is clicked', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ReviewSection values={baseValues} onEdit={vi.fn()} onSubmit={onSubmit} />);
    await user.click(screen.getByRole('button', { name: /^submit$/i }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('calls onEdit with the section id when an Edit button is clicked', async () => {
    const onEdit = vi.fn();
    const user = userEvent.setup();
    render(<ReviewSection values={baseValues} onEdit={onEdit} onSubmit={vi.fn()} />);
    const editButtons = screen.getAllByRole('button', { name: /^edit$/i });
    await user.click(editButtons[0]);
    expect(onEdit).toHaveBeenCalledWith('A');
  });
});
```

- [ ] **Step 2: Run the test file to verify failure**

Run: `cd app && npx vitest run src/components/survey/ReviewSection.test.tsx`
Expected: file fails to import (`./ReviewSection` does not exist).

- [ ] **Step 3: Create the component**

Create `app/src/components/survey/ReviewSection.tsx`:

```tsx
import { useMemo } from 'react';
import {
  sectionA, sectionB, sectionC, sectionD, sectionE1, sectionE2,
  sectionF, sectionG, sectionH, sectionI, sectionJ,
} from '@/generated/items';
import type { Section as SectionModel, Item } from '@/types/survey';
import { evaluateCrossField, type Warning } from '@/lib/cross-field';
import type { FormValues } from '@/lib/skip-logic';
import { Button } from '@/components/ui/button';

const SECTIONS: SectionModel[] = [
  sectionA, sectionB, sectionC, sectionD, sectionE1, sectionE2,
  sectionF, sectionG, sectionH, sectionI, sectionJ,
];

interface ReviewSectionProps {
  values: FormValues;
  onEdit: (sectionId: string) => void;
  onSubmit: () => void;
}

function formatValue(v: unknown): string {
  if (v === undefined || v === null || v === '') return '';
  if (Array.isArray(v)) return v.join(', ');
  return String(v);
}

function rowsForItem(item: Item, values: FormValues): Array<{ key: string; label: string; value: string }> {
  if (item.type === 'multi-field' && item.subFields) {
    return item.subFields
      .map((sf) => ({ key: sf.id, label: `${item.id} ${sf.label}`, value: formatValue(values[sf.id]) }))
      .filter((r) => r.value !== '');
  }
  const primary = formatValue(values[item.id]);
  const rows: Array<{ key: string; label: string; value: string }> = [];
  if (primary !== '') rows.push({ key: item.id, label: `${item.id} ${item.label}`, value: primary });
  const otherKey = `${item.id}_other`;
  const otherVal = formatValue(values[otherKey]);
  if (otherVal !== '') rows.push({ key: otherKey, label: `${item.id} (specify)`, value: otherVal });
  return rows;
}

const SEVERITY_STYLES: Record<Warning['severity'], string> = {
  error: 'border-red-300 bg-red-50 text-red-900',
  warn: 'border-amber-300 bg-amber-50 text-amber-900',
  clean: 'border-blue-300 bg-blue-50 text-blue-900',
  info: 'border-slate-200 bg-slate-50 text-slate-700',
};

export function ReviewSection({ values, onEdit, onSubmit }: ReviewSectionProps) {
  const warnings = useMemo(() => evaluateCrossField(values), [values]);

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-6 p-6">
      <h2 className="text-2xl font-semibold tracking-tight">Review your answers</h2>

      {warnings.length > 0 ? (
        <section aria-label="Cross-field warnings" className="flex flex-col gap-2">
          {warnings.map((w) => (
            <div
              key={w.id}
              className={`rounded-md border px-3 py-2 text-sm ${SEVERITY_STYLES[w.severity]}`}
            >
              <strong className="mr-2">{w.id}</strong>
              {w.message}
            </div>
          ))}
        </section>
      ) : null}

      {SECTIONS.map((section) => {
        const rows = section.items.flatMap((item) => rowsForItem(item, values));
        if (rows.length === 0) return null;
        return (
          <section key={section.id} className="flex flex-col gap-2">
            <header className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                Section {section.id} — {section.title}
              </h3>
              <Button type="button" variant="outline" size="sm" onClick={() => onEdit(section.id)}>
                Edit
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

      <div className="pt-2">
        <Button type="button" onClick={onSubmit}>
          Submit
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run the ReviewSection tests to verify they pass**

Run: `cd app && npx vitest run src/components/survey/ReviewSection.test.tsx`
Expected: 6/6 pass.

- [ ] **Step 5: Commit**

```bash
git add app/src/components/survey/ReviewSection.tsx app/src/components/survey/ReviewSection.test.tsx
git commit -m "feat(f2-pwa): M7.3 ReviewSection (read-only summary + warnings)"
```

---

## Task 4: Wire ReviewSection into MultiSectionForm

**Files:**
- Modify: `app/src/components/survey/MultiSectionForm.tsx`
- Modify: `app/src/components/survey/MultiSectionForm.test.tsx`

After Section J validates, advance to a virtual "review" step (`index === SECTIONS.length`) that renders `<ReviewSection>`. Submit from review calls the existing `onSubmit` prop. Edit jumps back to the chosen section via its index.

- [ ] **Step 1: Add a failing form-level test**

Append to `app/src/components/survey/MultiSectionForm.test.tsx` inside `describe('<MultiSectionForm>', () => { ... })`:

```ts
  it('shows the review screen after Section J and submits from there', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const fullAnswers = {
      Q1_1: 'Reyes', Q1_2: 'Carl', Q1_3: 'P',
      Q2: 'Regular', Q3: 'Female', Q4: 30, Q5: 'Nurse', Q7: 'No',
      Q9_1: 3, Q9_2: 6, Q10: 5, Q11: 8,
    };
    render(
      <MultiSectionForm
        initialValues={{ ...fullAnswers, _startAt: 'J' as never }}
        onAutosave={vi.fn()}
        onSubmit={onSubmit}
      />,
    );
    // smoke: nothing crashes — full traversal is exercised by the previous tests.
    // Here we just confirm the review screen surfaces the PROF-03 derivation.
    expect(true).toBe(true);
  });
```

(This placeholder test is intentionally weak — full traversal of all 11 sections is impractical in a unit test. Steps 4–5 below add the real coverage by directly rendering at the review index via a test-only escape hatch.)

- [ ] **Step 2: Update MultiSectionForm.tsx with review routing**

Replace the existing `MultiSectionForm` body. The full updated file content:

```tsx
import { useMemo, useRef, useState } from 'react';
import type { ZodTypeAny } from 'zod';
import type { Item, Section as SectionModel } from '@/types/survey';
import {
  sectionA, sectionB, sectionC, sectionD, sectionE1, sectionE2,
  sectionF, sectionG, sectionH, sectionI, sectionJ,
} from '@/generated/items';
import {
  sectionASchema, sectionBSchema, sectionCSchema, sectionDSchema,
  sectionE1Schema, sectionE2Schema, sectionFSchema, sectionGSchema,
  sectionHSchema, sectionISchema, sectionJSchema,
} from '@/generated/schema';
import { shouldShow, type FormValues } from '@/lib/skip-logic';
import { Section } from './Section';
import { ProgressBar } from './ProgressBar';
import { Navigator } from './Navigator';
import { ReviewSection } from './ReviewSection';

interface SectionConfig {
  id: string;
  section: SectionModel;
  schema: ZodTypeAny;
}

const SECTIONS: SectionConfig[] = [
  { id: 'A', section: sectionA, schema: sectionASchema },
  { id: 'B', section: sectionB, schema: sectionBSchema },
  { id: 'C', section: sectionC, schema: sectionCSchema },
  { id: 'D', section: sectionD, schema: sectionDSchema },
  { id: 'E1', section: sectionE1, schema: sectionE1Schema },
  { id: 'E2', section: sectionE2, schema: sectionE2Schema },
  { id: 'F', section: sectionF, schema: sectionFSchema },
  { id: 'G', section: sectionG, schema: sectionGSchema },
  { id: 'H', section: sectionH, schema: sectionHSchema },
  { id: 'I', section: sectionI, schema: sectionISchema },
  { id: 'J', section: sectionJ, schema: sectionJSchema },
];

const REVIEW_INDEX = SECTIONS.length;

interface MultiSectionFormProps {
  initialValues: FormValues;
  initialIndex?: number;
  onAutosave: (values: FormValues) => void;
  onSubmit: (values: FormValues) => void;
}

export function MultiSectionForm({
  initialValues,
  initialIndex = 0,
  onAutosave,
  onSubmit,
}: MultiSectionFormProps) {
  const [merged, setMerged] = useState<FormValues>(initialValues);
  const [index, setIndex] = useState(initialIndex);
  const submitRef = useRef<(() => void) | null>(null);

  const isReview = index === REVIEW_INDEX;
  const current = isReview ? null : SECTIONS[index]!;
  const isFirst = index === 0;
  const isLastSection = index === SECTIONS.length - 1;

  const visibleItems: Item[] = useMemo(() => {
    if (!current) return [];
    return current.section.items.filter((it) => shouldShow(current.id, it.id, merged));
  }, [current, merged]);

  const sectionDefaults = useMemo(() => {
    if (!current) return {};
    const out: FormValues = {};
    for (const it of current.section.items) {
      if (it.type === 'multi-field' && it.subFields) {
        for (const sf of it.subFields) {
          if (sf.id in merged) out[sf.id] = merged[sf.id];
        }
        continue;
      }
      if (it.id in merged) out[it.id] = merged[it.id];
      const otherKey = `${it.id}_other`;
      if (otherKey in merged) out[otherKey] = merged[otherKey];
    }
    return out;
  }, [current, merged]);

  const handleSectionAutosave = (values: FormValues) => {
    setMerged((prev) => {
      const next = { ...prev, ...values };
      onAutosave(next);
      return next;
    });
  };

  const handleSectionValid = (values: FormValues) => {
    const next = { ...merged, ...values };
    setMerged(next);
    setIndex(index + 1);
  };

  const handlePrev = () => {
    if (isFirst) return;
    setIndex(index - 1);
  };

  const handleNext = () => {
    submitRef.current?.();
  };

  const handleEdit = (sectionId: string) => {
    const target = SECTIONS.findIndex((s) => s.id === sectionId);
    if (target >= 0) setIndex(target);
  };

  const handleFinalSubmit = () => {
    onSubmit(merged);
  };

  if (isReview) {
    return (
      <ReviewSection values={merged} onEdit={handleEdit} onSubmit={handleFinalSubmit} />
    );
  }

  return (
    <div className="flex flex-col">
      <ProgressBar current={index + 1} total={SECTIONS.length} />
      <Section<FormValues>
        key={current!.id}
        section={current!.section}
        schema={current!.schema}
        items={visibleItems}
        defaultValues={sectionDefaults}
        hideSubmit
        submitRef={submitRef}
        onAutosave={handleSectionAutosave}
        onSubmit={handleSectionValid}
      />
      <div className="mx-auto w-full max-w-xl px-6 pb-6">
        <Navigator
          isFirst={isFirst}
          isLast={isLastSection}
          onPrev={handlePrev}
          onNext={handleNext}
          onSubmit={handleNext}
        />
      </div>
    </div>
  );
}
```

Notes on the diff:
- New `initialIndex` prop (defaults to 0) lets tests jump directly to the review screen without traversing every section.
- `isLast` was renamed to `isLastSection`; on Section J the Navigator's "Submit" button now triggers `handleNext` (i.e. submits Section J), which advances to the review screen — the final submit lives there.
- `handleSectionValid` no longer fires `onSubmit`; that moves to `handleFinalSubmit`.

- [ ] **Step 3: Replace the placeholder test from Step 1 with two real tests**

In `app/src/components/survey/MultiSectionForm.test.tsx`, replace the `'shows the review screen after Section J...'` test with:

```ts
  it('renders the review screen when initialIndex points past the last section', () => {
    render(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes', Q1_2: 'Carl', Q1_3: 'P',
          Q2: 'Regular', Q3: 'Female', Q4: 30, Q5: 'Nurse', Q7: 'No',
          Q9_1: 3, Q9_2: 6, Q10: 5, Q11: 8,
        }}
        initialIndex={11}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(
      screen.getByRole('heading', { name: /Review your answers/i }),
    ).toBeInTheDocument();
  });

  it('calls onSubmit with merged values when Submit is clicked on the review screen', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const values = {
      Q1_1: 'Reyes', Q1_2: 'Carl', Q1_3: 'P',
      Q2: 'Regular', Q3: 'Female', Q4: 30, Q5: 'Nurse', Q7: 'No',
      Q9_1: 3, Q9_2: 6, Q10: 5, Q11: 8,
    };
    render(
      <MultiSectionForm
        initialValues={values}
        initialIndex={11}
        onAutosave={vi.fn()}
        onSubmit={onSubmit}
      />,
    );
    await user.click(screen.getByRole('button', { name: /^submit$/i }));
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining(values));
  });

  it('returns to the chosen section when Edit is clicked on the review screen', async () => {
    const user = userEvent.setup();
    render(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes', Q1_2: 'Carl', Q1_3: 'P',
          Q2: 'Regular', Q3: 'Female', Q4: 30, Q5: 'Nurse', Q7: 'No',
          Q9_1: 3, Q9_2: 6, Q10: 5, Q11: 8,
        }}
        initialIndex={11}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    const editButtons = screen.getAllByRole('button', { name: /^edit$/i });
    await user.click(editButtons[0]);
    expect(
      screen.getByRole('heading', { name: /Section A — Healthcare Worker Profile/i }),
    ).toBeInTheDocument();
  });
```

- [ ] **Step 4: Run the form tests**

Run: `cd app && npx vitest run src/components/survey/MultiSectionForm.test.tsx`
Expected: 7/7 pass (4 original + 1 _other regression from Task 1 step 8 + 3 review-screen tests).

- [ ] **Step 5: Run the full test suite**

Run: `cd app && npx vitest run`
Expected: 191/191 (176 prior + 12 cross-field + 6 review + 3 review-form − 6 superseded) — count is approximate; what matters is "all green, no regressions".

- [ ] **Step 6: Run typecheck and build**

Run: `cd app && npm run typecheck && npm run build`
Expected: both clean.

- [ ] **Step 7: Commit**

```bash
git add app/src/components/survey/MultiSectionForm.tsx app/src/components/survey/MultiSectionForm.test.tsx
git commit -m "feat(f2-pwa): M7.4 wire ReviewSection between Section J and final submit"
```

---

## Task 5: Update NEXT.md → M8

**Files:**
- Modify: `app/NEXT.md`

- [ ] **Step 1: Replace the file content**

Overwrite `app/NEXT.md` with:

```markdown
# Next step (future-Carl)

**Last milestone shipped:** M7 — Validation + cross-field. Generator now emits a `.superRefine` per section enforcing "if parent choice = the `isOtherSpecify` value, then `_other` must be non-empty" (covers all 33 hasOtherSpecify items). New `src/lib/cross-field.ts` evaluates six PWA-applicable rules from `F2-Cross-Field.md` (PROF-01 tenure-vs-age, PROF-02 role-vs-specialty, PROF-03 employment-class derivation, PROF-04 weekly-hours sanity, GATE-02 Section G non-doctor cleanup, GATE-05 Section C/D non-clinical cleanup). New `<ReviewSection>` between Section J and the final submit shows a read-only answer summary, surfaces all warnings, and exposes per-section Edit jumps. Final `onSubmit` only fires from the review screen.

**Next milestone:** M8 — Facility list + enrollment flow. 8–10h per spec §11.1.

**Before starting M8:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §8 (Enrollment & Facility data flow) and the M4 backend's `/facilities` endpoint.
2. Target: fetch facility list via the M4 backend on first run + every app open, cache in Dexie `facilities` table, present an enrollment screen (select facility, enter HCW identifier) that populates `hcw_id` + `facility_id` + `facility_type` + `facility_has_bucas` + `facility_has_gamot` + `response_source` used by every subsequent submission and by the deferred cross-field rules.
3. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M8-enrollment.md`.

**M7 technical debt to address in later milestones:**

- **14+ deferred cross-field rules** — FAC-01..07 (facility-type duals), DISP-01..03 (timestamps + disposition), SRC-01..03 (response source), CONS-01..02 (consent), GATE-01/03/04 (audience filters that need facility flags). All require enrollment context from M8 or backend-side timestamps. Wire them into `cross-field.ts` as additional rules in M8/M9.
- **Per-item max-character limits** — Q36/Q73/Q77/Q80 (1000 chars) and Q1 names (50/5 chars) per `F2-Validation.md`. Defer to M11 hardening unless desk-tests show drop-off.
- **Section G role-gate** — currently surfaced as a GATE-02 warning on review. Once M8 lands the role-bucket logic, hide whole Section G from non-doctors instead of warning after-the-fact.
- **Q63 collapsed to one long-text** — pending ASPSI confirmation (open item #5 in F2-Spec). Split if rejected.

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build` — confirm M7 still green.
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build` — confirm M4 still green.
- Copy `.env.example` → `.env.local` and fill both vars from the live Apps Script deployment.
- `npm run dev`, walk a full submission start-to-finish to verify the review screen renders and Submit fires.
- Open `../2026-04-17-design-spec.md` §8 and the M4 backend's `/facilities` handler to re-orient for M8.
```

- [ ] **Step 2: Commit**

```bash
git add app/NEXT.md
git commit -m "docs(f2-pwa): M7.5 update NEXT.md to point at M8 (enrollment)"
```

---

## Self-review notes

**Spec coverage check:**
- F2-Validation.md per-item conditional `_other` required → Task 1 ✓
- F2-Validation.md max-char limits → explicitly deferred (out of scope, documented in NEXT.md) ✓
- F2-Cross-Field.md PROF-01..04 + GATE-02/05 → Task 2 ✓
- F2-Cross-Field.md FAC/DISP/SRC/CONS/GATE-01,03,04 → explicitly deferred (need M8) ✓
- Review screen with cross-field warnings (design spec §3 "Review") → Tasks 3–4 ✓
- Submit from review only → Task 4 ✓

**Type consistency check:**
- `Warning` interface defined in Task 2; consumed in Task 3. Field names match (`id`, `severity`, `message`, `fields`, `derived`).
- `evaluateCrossField(values: FormValues)` signature consistent across files.
- `MultiSectionForm` `initialIndex` prop introduced in Task 4 — used by tests in same task; no earlier task references it.
- `REVIEW_INDEX = SECTIONS.length` (= 11) is the sentinel; `initialIndex={11}` in tests targets it directly.

**Placeholder scan:** None. All code blocks contain literal implementations; no TBD/TODO/"add validation"/"handle edge cases".

---

**Plan saved to `deliverables/F2/PWA/2026-04-18-implementation-plan-M7-validation-cross-field.md`.**
