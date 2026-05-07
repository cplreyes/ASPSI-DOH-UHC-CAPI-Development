---
title: F2 PWA — Matrix view for scale-style questions (#18)
status: design (approved 2026-04-25)
issue: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/18
milestone: v1.2.0 — UAT Round 3 / Feature batch
owner: Carl Patrick L. Reyes
---

# F2 PWA — Matrix view for scale-style questions (#18)

## Problem

Several batteries in the F2 PWA questionnaire ask the respondent the same scale (1–5, or Strongly Agree → Strongly Disagree, or Always → Never) repeatedly across N statements. Today each statement renders as its own one-by-one question screen. For an HCW filling out the survey on their phone:

- Section G Q75–Q81 = 7 sequential `single (1–5)` items, all with the same `1 · 2 · 3 · 4 · 5` choice set.
- Section J Grid #1 (Agreement battery) and Grid #2 (Frequency battery) are the spec's explicit grids — together ~22 `grid-single` items that share their respective 5-option scales.

Repeating the same five buttons seven times in a row is slow to fill, mentally noisy, and doesn't match the printed-questionnaire convention ASPSI staff are used to.

## Decision (approved)

Render consecutive `single`-type items that share the same choice set as a single 2-way matrix (rows = statements, columns = scale options). Detection happens at render time, no spec / parser / items.ts changes. Apply to both Section J's explicit Grid #N battery AND Section G's implicit Q75–Q81 Likert cluster automatically.

Mobile (< 768px) reflows the matrix into per-row stacked cards (statement on top, radio strip below). Tablet / desktop (≥ 768px) keeps the full `<table>` matrix.

Skip-logic, validation, completion, and auto-advance behaviour stay consistent with how individual questions work today — each matrix row is its own form field, just visually grouped.

## Out of scope (for v1)

- **Group title shown above the matrix** (e.g. "Grid #1 — Agreement"). The column-header row already shows the scale; surfacing the spec's section header to the UI adds noise without analytical value. Reconsider if testers ask.
- **Sticky column headers.** Section J's largest battery is ~5 rows; Q75–Q81 is 7 rows. The viewport doesn't need stickiness at this scale. Defer.
- **Per-row label translation overrides.** Matrix uses each row's existing `localized(item.label, locale)` — same as today's `Question` for individual items.
- **Spec / parser changes.** No new types, no new fields. Pure rendering concern.

## Detection algorithm

A new pure helper, exported from `src/components/survey/group-matrix.ts`:

```ts
export interface MatrixGroup {
  kind: 'matrix';
  /** The shared choice set every row uses — passed to the renderer. */
  choices: Choice[];
  /** The rows. Always >= 2 items per group. */
  items: Item[];
}

export function groupVisibleItems(items: Item[]): Array<MatrixGroup | Item>;
```

Walks `items` (already `shouldShow`-filtered by the caller). Groups any *consecutive* items that ALL satisfy:

1. `item.type === 'single'`
2. `item.hasOtherSpecify === false` (Other-specify items render with a companion text field that doesn't fit a matrix row)
3. `item.choices` is defined
4. `item.choices` matches the previous item's `choices` exactly — same `length`, same `value` strings in the same order. Labels are not compared (they may differ across locales but `value` is canonical).

Min cluster size = 2 (a single same-choice item alone stays as a regular `Question`).

Items not satisfying the filter (every multi, every multi-field, every short-text, every single + specify, every date, every number) flow through unchanged.

Output is a flat list mixing `MatrixGroup` and `Item` in original document order. The Section renderer iterates this list and dispatches by kind.

## Component architecture

### New: `src/components/survey/MatrixQuestion.tsx`

Props:

```ts
interface MatrixQuestionProps {
  items: Item[];           // the rows
  choices: Choice[];       // the shared scale
}
```

Reads `register`, `formState.errors`, locale via `useFormContext` + `useLocale`. Each row registers `register(item.id)` — same field shape as `Question`'s `case 'single'`, so RHF + Zod schema treat the matrix's rows as individual fields.

Layout:

- **`md` breakpoint and up** — single `<table>` with sticky `<thead>` (header row contains "Statement" + each `localized(choice.label, locale)`). Each row is a `<tr>` with the statement label in the leftmost cell and a `<td>` per scale option containing a radio input.
- **Below `md`** — for each row, render a stacked block: statement + role="radiogroup" of horizontally-laid-out radio inputs (each with its own visible label). Implementation uses Tailwind responsive utilities to swap between the two layouts; one render tree, no JS branching.

Per-row errors render inline under the row (table-cell-spanning-row in desktop, or appended to the stacked block in mobile). Same red-text style as `Question`'s error display.

### Modified: `src/components/survey/Section.tsx`

Currently the form renders `(items ?? section.items).map((item) => <Question ... />)`. Change:

```tsx
const groupedItems = useMemo(
  () => groupVisibleItems(items ?? section.items),
  [items, section.items]
);

// In the render:
{groupedItems.map((entry, idx) => (
  entry.kind === 'matrix'
    ? <MatrixQuestion key={`matrix-${idx}`} items={entry.items} choices={entry.choices} />
    : <Question key={entry.id} item={entry} />
))}
```

(`MatrixGroup` doesn't have a stable `id` since it's render-time-derived. Keying by index is acceptable because the grouping is deterministic per `items` value.)

### Modified: `src/components/survey/ReviewSection.tsx`

Same grouping helper. Matrix groups render as a compact `<table>` with two columns: statement label + the selected `localized(choice.label, locale)`. Edit affordance still routes back to the parent section (same as today).

### Unchanged

- `Question.tsx` — still renders single questions
- `MultiSectionForm.tsx` — section-level navigation, auto-advance, completion check all derive from `visibleItems` which is still a flat list of `Item`s; matrix rendering is purely cosmetic over the same fields
- `skip-logic.ts` — no changes; predicates run per-item as today
- `parse-spec.ts`, `emit-items.ts`, `emit-schema.ts` — no changes
- `items.ts`, `schema.ts` — no regen needed

## Skip-logic per row

`Section.tsx` already builds `visibleItems = items.filter(i => shouldShow(section.id, i.id, values))` before rendering. `groupVisibleItems` runs after that filter, so:

- Hidden rows simply don't enter `groupVisibleItems` → don't render in the matrix.
- If every row in a candidate cluster is hidden, the cluster collapses to nothing; no matrix renders.
- Mixed visibility (e.g. Q75 + Q76 visible but Q77 hidden, then Q78 + Q79 visible) groups them as ONE matrix of 4 rows in document order. The detection cares about consecutive same-choice items in the *post-filter* sequence — equivalent to "consecutive in render order".

## Validation + completion

- Each row is `required: true` per the spec (or whatever the items.ts says — the matrix doesn't override).
- The Zod schema for the section is unchanged; each row validates as a `z.enum([...])`.
- `getSectionStatus` in `MultiSectionForm.tsx` already iterates `visibleItems` and confirms each required visible item is filled. Matrix rows, being individual items, fold cleanly into this check.
- Auto-advance fires when the section status flips to `complete` (existing logic, no change).
- Per-row error: `errors[item.id]` rendered inline under the row.

## Mobile reflow specifics

Breakpoint: `md` (Tailwind default = 768px). Above: table. Below: stacked cards.

Implementation sketch (one tree, two layouts):

```tsx
{/* Desktop / tablet header */}
<div className="hidden md:grid md:grid-cols-[2fr_repeat(N,1fr)] md:gap-2 md:py-2 md:font-medium">
  <span>{t('matrix.statement')}</span>
  {choices.map((c) => <span key={c.value} className="text-center">{localized(c.label, locale)}</span>)}
</div>

{items.map((item) => (
  <div
    key={item.id}
    className="flex flex-col gap-2 border-t py-3
               md:grid md:grid-cols-[2fr_repeat(N,1fr)] md:items-center md:gap-2"
  >
    <span className="text-sm">{item.id}. {localized(item.label, locale)}</span>

    {/* Mobile: a horizontal radio strip */}
    <div className="flex gap-3 md:hidden">
      {choices.map((c) => <RadioInput ... />)}
    </div>

    {/* Tablet+: one cell per choice, vertically aligned */}
    {choices.map((c) => (
      <div key={c.value} className="hidden md:flex md:justify-center">
        <RadioInput ... />
      </div>
    ))}
  </div>
))}
```

(Pseudocode — final implementation may use a slightly different shape for `<table>` accessibility. Either approach satisfies the layout requirement.)

## Accessibility

- Desktop `<table>` uses semantic `<thead>` / `<tbody>` / `<th scope="col">` and per-row `<th scope="row">` for the statement; screen readers announce each radio with its column header.
- Mobile reflow groups each row's radio set in `role="radiogroup"` with `aria-labelledby` pointing to the statement.
- vitest-axe assertion in the new component test confirms no a11y regressions.
- Keyboard navigation: Tab moves focus into the radio group; arrow keys move between radios within a group (browser default for radio inputs sharing a `name`).

## Test strategy

### Unit — `src/components/survey/group-matrix.test.ts` (new)

Pure tests for `groupVisibleItems`. Cases:

- Empty array → empty array.
- Single item → returned as-is.
- Two consecutive same-choice items → one matrix group.
- Two consecutive items with different choice arrays → two single items.
- Mixed sequence (single, single same-choice, multi, single same-choice) → matrix group of 2, then multi, then single.
- All-hidden cluster (caller passes filtered list with no rows) → no matrix in output.
- `single + specify` items → never grouped (excluded by `hasOtherSpecify` filter).
- Realistic Section G fixture (Q75–Q81 with same `['1','2','3','4','5']` choices) → one matrix of 7.
- Realistic Section J fixture (Grid #1 Agreement battery) → one matrix.
- `single` items where labels differ but `value` arrays match → grouped (label translation should not break grouping).

### Component — `src/components/survey/MatrixQuestion.test.tsx` (new)

Render with a synthetic 3-row matrix in a `react-hook-form` provider. Assert:

- `<table>` rendered when viewport ≥ 768px (set via `window.innerWidth` mock).
- Header row contains each choice label.
- Clicking a radio for a given row sets that item's form value (via `getValues`) and does NOT mutate other rows.
- Per-row required error renders when the form is submitted with that row blank.
- vitest-axe: no a11y violations.
- Mobile viewport (< 768px) renders stacked cards instead of `<table>`.

### E2E — `e2e/matrix.spec.ts` (new)

Walk Section J on staging:

- Section J renders the Grid #1 matrix (assert table presence).
- Fill all 5 rows of Grid #1 + 5 rows of Grid #2.
- Advance to next section (auto-advance fires; section status badge flips to complete).
- Reach review screen. Assert the matrix groups render as compact tables in review (each row showing `Statement → Selected label`).

### Regression

- Run the existing 287-test suite. Matrix changes shouldn't affect any non-matrix render path. Specific watch: `MultiSectionForm.test.tsx` golden-path test (hits Section A which has no matrix groups), `ReviewSection.test.tsx` (review of mixed item types).

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Tablet QA reveals matrix touch targets feel too small | Medium | Spec a minimum 44px touch target per cell; vitest-axe + manual QA. If still cramped, tighten the row spacing without further breakpoint changes. |
| Some existing single-item screens were *intended* as standalone (not part of a matrix) but happen to share a choice set with the next item | Low | Audit Section A–J for any consecutive `single` items with same `choices` that shouldn't group. Spec scan suggests this is restricted to Sections G + J today; review listed clusters before merge. |
| Review screen mini-table makes a long matrix unreadable when 7+ rows | Low | Section J's largest battery is ~5; Q75–Q81 is 7. Acceptable. If a future section pushes it to 15+ rows, revisit. |
| Per-row required error in mobile-reflowed cards pushes layout if not styled carefully | Low | Use `min-h` on the row container so error text doesn't reflow above row. |

## Implementation order

1. Add `group-matrix.ts` with `groupVisibleItems` helper + unit tests.
2. Add `MatrixQuestion.tsx` + component tests.
3. Wire into `Section.tsx`.
4. Wire into `ReviewSection.tsx`.
5. Add E2E test.
6. Visual QA on staging across iPhone Safari + Android Chrome + desktop Chrome breakpoints.
7. Ship to staging, post `status:fixed-pending-verify` comment on #18.

## Acceptance criteria

- Section J renders Grid #1 (Agreement battery) + Grid #2 (Frequency battery) as 2 matrices, not as 10 separate screens.
- Section G Q75–Q81 renders as a single matrix.
- A Q5 = Nurse respondent (Section G hidden) sees no matrix from Section G — entire section is skipped, identical to today's behaviour.
- A respondent on iPhone Safari (375px width) sees the mobile-reflowed stacked cards; on iPad / desktop sees the table.
- Submission flow unchanged — each row's value lands in the response sheet under its existing `Q##` column.
- All 287 existing tests still pass; ~15 new tests added (10 unit + 4 component + 1 E2E).
