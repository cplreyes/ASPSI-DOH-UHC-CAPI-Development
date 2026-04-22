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

- `F2-Spec.md` — **Apr 20 rev**: 124 actual items (numbered Q1–Q125 with Q108 as a PDF numbering gap) across 35+ sections. Source of `src/generated/items.ts` and `src/generated/schema.ts`. Supersedes the Apr 08 draft (114 items).
