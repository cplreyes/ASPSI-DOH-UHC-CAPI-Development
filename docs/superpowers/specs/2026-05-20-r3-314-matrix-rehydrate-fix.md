---
title: R3 #314 — Matrix rehydrate fix (Approach A: controlled radios)
date: 2026-05-20
sprint: 006
issue: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/314
status: design-approved
---

# R3 #314 — Matrix rehydrate fix

## Problem

When a respondent edits a previously-filled section (Edit-from-Review flow) containing a `MatrixQuestion` (e.g., Job Satisfaction matrices Q98–Q107 and Q119–Q121), the matrix radios render **blank** on desktop/tablet — the saved answers don't visibly rehydrate, even though they're present in `defaultValues`. Mobile cards show the correct selection.

Reported by Marriz on 2026-05-15 (TC-008). Reproduced + root-caused in PR #335. Three prior fix attempts (Carl, 2026-05-19) reverted.

## Root Cause

`MatrixQuestion.tsx` renders each radio **twice**: once in the desktop `<table>` (`md:table`, lines 24-76) and once in the mobile cards (`md:hidden`, lines 79-112). Both copies call `{...register(item.id)}`. RHF stores the **last-registered ref** per name; `defaultValues` is applied only to that ref (the mobile copy, since it renders after desktop in JSX). Desktop view — what tablet/desktop users actually see — gets a stale ref with `.checked = false`.

The `.skip`'d test at `Section.test.tsx:231` asserts the desktop `[0]` copy is checked and currently fails as expected.

## Fix — Approach A: controlled radios via `setValue` + `useWatch`

Eliminate `register` from radio inputs. Use a top-level `useWatch` to read current selected value per item, and `setValue` on change.

```tsx
// MatrixQuestion.tsx (top of component)
const { setValue } = useFormContext();
const watchedValues = useWatch({ name: items.map((i) => i.id) }) as
  | (string | undefined)[]
  | undefined;

// each radio (both desktop and mobile copies):
<input
  type="radio"
  value={c.value}
  aria-label={`${item.id} ${localized(c.label, locale)}`}
  checked={(watchedValues ?? [])[itemIdx] === c.value}
  onChange={() =>
    setValue(item.id, c.value, { shouldValidate: true, shouldDirty: true })
  }
/>
```

No `register` on radios. Both DOM copies are controlled inputs driven by the same form state. `setValue` auto-registers fields; `defaultValues` populates form state at mount; `useWatch` reads it.

## Scope

- **Modified file:** `deliverables/F2/PWA/app/src/components/survey/MatrixQuestion.tsx` (~15 LOC delta).
- **Test:** Un-skip `Section.test.tsx:231` (`it.skip` → `it`). Verify it passes after the fix.
- **Regression check:** existing `Section.test.tsx:185` live-fill matrix test must still pass.
- **No structural changes:** dual-DOM responsive layout stays; mobile-cards UX preserved.
- **No changes to Section.tsx** — `useForm` config stays as-is. The earlier "Section form-host" theory was based on a spurious isolated test that asserted `.some(checked)` (which the mobile copy satisfied); the root cause is `MatrixQuestion`, not the form host.

## Testing (TDD)

1. Un-skip the failing test. Confirm it's red (re-runs the exact bug repro).
2. Apply the fix.
3. Re-run the full survey test suite: existing tests still pass (especially the `live-filled matrix values reach onSubmit` test at line 185, and `MatrixQuestion.test.tsx`).
4. Manual verification: not required for the fix itself; #314 GH issue can move to `status:fixed-pending-verify` for Marriz/Shan to confirm on next R3 round (or in a quick smoke).

## Rollback

Single-file change, easy to revert via `git revert <commit-sha>`.

## Out of scope

- The longer-term architectural question of whether dual-DOM (table desktop / cards mobile) is the right responsive pattern for matrices. Approach A keeps it as-is.
- Updating other MatrixQuestion usages — there's only one component.
- The `Section.tsx` form-host config — left untouched per analysis above.
