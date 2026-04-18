# Next step (future-Carl)

**Last milestone shipped:** M6 — Full instrument scaffolding. Every item across all 11 sections (A, B, C, D, E1, E2, F, G, H, I, J) of `app/spec/F2-Spec.md` is now fillable. The generator handles `single (1–5)` Likerts, `multi` / `multi + specify` (checkbox groups + `_other` reveal), `date` (HTML date input + ISO regex), `multi-field` (`short-text ×N` / `number ×N` flattened to per-subfield schema keys), and `grid-single` (widened to `single`, choice set inherited from `**Grid #N — Title (...)** ` headers when the row's choices column is blank). `MultiSectionForm` wires all 11 sections; intra-section skip predicates added for D, E1, E2, F, G, I, J. **117 items, 0 unsupported, 176 tests green.**

**Next milestone:** M7 — Validation + 20 POST cross-field rules. 15–20h per spec §11.1.

**Before starting M7:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §6 (Generator Pattern) and the validation spec at `../../F2-Validation.md` + cross-field spec at `../../F2-Cross-Field.md` (or `../../F2-Skip-Logic.md` if cross-field hasn't been promoted to its own file yet).
2. Target: (a) emit Zod composition for the per-item validation rules in `F2-Validation.md` (regex, range, conditional-required, custom messages); (b) build a separate `src/generated/cross-field.ts` module with the 20 POST rules from `F2-Cross-Field.md` evaluated at section transitions and at submit; (c) surface cross-field warnings in a Review screen before final submit.
3. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M7-validation-cross-field.md`.

**M6 technical debt to address in later milestones:**

- **Section G role gate** — Section G is conceptually "doctor/dentist only" but predicates only handle intra-section conditions. Non-doctor respondents currently see all G items. Resolve by adding cross-section gating in M7 (skip whole section based on Q5) or M8 (enrollment context).
- **Facility-type duplicates (Q62 / Q62.1, Q67 / Q67.1, Q78 / Q78.1)** — both variants currently render. Need `facility_type` pre-fill from the M8 facility list to gate ZBB vs NBB variants.
- **Required `multi` items** — the schema emits `z.array(...).min(1)`, but unchecked checkboxes give `[]`. Verify the empty-array case surfaces a clear error message in M7.
- **`Q63` two-prompt label** — collapsed into a single long-text per spec §F2-Spec note. If ASPSI rejects this in review (open item #5), split back into 63a / 63b in the spec then regen.

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build` — confirm M6 still green (176 tests, 11 sections, 117 items).
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build` — confirm M4 still green.
- Copy `.env.example` → `.env.local` and fill both vars from the live Apps Script deployment.
- `npm run dev`, walk through all 11 sections start-to-finish to spot rendering regressions before adding M7 validation.
- Open `../../F2-Validation.md` and `../../F2-Cross-Field.md` (or `../../F2-Skip-Logic.md` §POST rules) to re-orient for M7.
