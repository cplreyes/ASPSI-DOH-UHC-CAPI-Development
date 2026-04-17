# Next step (future-Carl)

**Last milestone shipped:** M1 — Generator v1 + single-section render.

**Next milestone:** M2 — Autosave + IndexedDB via Dexie (8–10h).

**Before starting M2:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §§5.5, 7.2, 7.3 (state + Dexie schema + sync lifecycle precursor) to draft the M2 plan file.
2. Target: replace the `alert(...)` submit handler in `App.tsx` with a Dexie write into `drafts` + `submissions` tables, and autosave field edits (debounced ~500ms) into `drafts` so a reload preserves in-progress answers.
3. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M2-autosave-indexeddb.md`.

**When picking this back up after a gap:**

- Run `npm install` first.
- Run `npm run test && npm run typecheck && npm run build` to confirm M1 still green.
- Run `npm run generate` to verify the generator still emits cleanly against the current `spec/F2-Spec.md`.
- Open `../2026-04-17-design-spec.md` §5.5 (State management) and §7.2 (IndexedDB schema) to re-orient.

**M1 remnants to close on merge to main:**

- Merge `feat/f2-pwa-m1` → `main` with `--no-ff` (preserves branch narrative).
- Tag `f2-pwa-m1` on the merge commit.
