# Next step (future-Carl)

**Last milestone shipped:** M7 — Validation + cross-field. Generator now emits a `.superRefine` per section enforcing "if parent choice = the `isOtherSpecify` value, then `_other` must be non-empty" (covers all 33 hasOtherSpecify items). New `src/lib/cross-field.ts` evaluates six PWA-applicable rules from `F2-Cross-Field.md` (PROF-01 tenure-vs-age, PROF-02 role-vs-specialty, PROF-03 employment-class derivation, PROF-04 weekly-hours sanity, GATE-02 Section G non-doctor cleanup, GATE-05 Section C/D non-clinical cleanup). New `<ReviewSection>` between Section J and the final submit shows a read-only answer summary, surfaces all warnings, and exposes per-section Edit jumps. Final `onSubmit` only fires from the review screen. **202 tests green, typecheck + build clean.**

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
