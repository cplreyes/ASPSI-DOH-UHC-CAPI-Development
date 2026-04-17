# Next step (future-Carl)

**Last milestone shipped:** M0 — Foundation (installable PWA shell).

**Next milestone:** M1 — Generator v1 + single-section render (12–15h).

**Before starting M1:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §§5.2, 6, 11.1 (M1 row) to draft the M1 plan file.
2. Target: parse one F2 section from `../../F2-Spec.md` into generated TS + Zod, render it via react-hook-form, validate on submit.
3. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M1-generator-plus-render.md`.

**When picking this back up after a gap:**

- Run `npm install` first.
- Run `npm run test && npm run typecheck && npm run build` to confirm M0 still green.
- Open `../2026-04-17-design-spec.md` §6 (Generator Pattern) to re-orient.

**M0 remnants to close on merge to main:**

- Re-enable `.git/hooks/post-commit` (currently renamed to `.disabled-for-m0` to suppress per-commit Slack noise during scaffolding).
- Merge `feat/f2-pwa-m0` → `main`. The branch was quarantined from F1/F3/F4 CSPro work; now that M0 ships, the PWA code joins the trunk.
