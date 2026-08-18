# Spec mirror

This directory mirrors `deliverables/F2/*.md` — the generator-relevant spec files. The copies are kept inside `app/` so the generator (`scripts/generate.ts`) has no `../../` path traversal.

## Sync rule

When `deliverables/F2/F2-Spec.md` changes, copy it into this directory and regenerate:

```bash
cp ../../F2-Spec.md spec/F2-Spec.md
npm run generate
```

M11 may introduce an automated sync + hash check. For now it's manual.

## Files

- `F2-Spec.md` — **Aug 17 rev** (Task 3.1, 2026-08-19): 124 numbered items (`Q1`–`Q124`, continuous — the Apr-20 PDF's `Q108` numbering gap is retired) plus 13 sub-items (11 new Section-B attribution sub-items + Q71a/Q71b) across 11 sections. Source of `src/generated/items.ts` and `src/generated/schema.ts`. Supersedes the Apr 20 rev (124 actual items, numbered Q1–Q125 with a Q108 gap).
