# Next step (future-Carl)

**Last milestone shipped:** M8 — Facility list + enrollment flow. Dexie bumped to v4 — v3 nulls the legacy `facilities` store (PK was `id`), v4 recreates it with `facility_id` PK matching the backend `FacilityMasterList` columns and adds a singleton `enrollment` table. Two-version split is required because Dexie throws `UpgradeError` on in-place PK changes — discovered during browser testing, hardened with a `.catch()` in `<AuthProvider>` so a Dexie failure doesn't hang the app at `'loading'`. New `facilities-client.ts` signs `GET /facilities` with the same HMAC scheme as `/batch-submit`. `facilities-cache.ts` exposes `refreshFacilities()`, `listFacilities()`, `getFacility()` against Dexie. `enrollment.ts` snapshots the resolved facility into the row on `setEnrollment` so `facility_type` is available without re-querying. New `<AuthProvider>` + `useAuth()` hook reads enrollment on boot. New `<EnrollmentScreen>` (HCW id input + facility select + Refresh button) is rendered by `App.tsx` whenever no enrollment row exists. `draft.ts` no longer hardcodes `hcw_id: 'anonymous'` — both `saveDraft` and `submitDraft` take an `EnrollmentInfo` arg, and `submitDraft` injects `facility_id` + `facility_type` into the submission `values` so the existing sync-orchestrator path keeps working. **230 tests green, typecheck + build clean.**

**Next milestone:** M9 — i18n (Filipino translations). 10–15h per spec §11.1, +20–30h if Carl translates rather than ASPSI.

**Before starting M9:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §5.5 (UI language) and §11.1 row M9.
2. Resolve open question #1 in spec §13: are ASPSI translators delivering the Filipino bundle, or does Carl translate? Affects scope by ~25h.
3. Target: install react-i18next, externalize all hardcoded English strings (header, EnrollmentScreen, ReviewSection, navigator, error messages, instrument labels via the generator), wire a language switcher into the header, persist choice in `localStorage`. Section/item labels need to flow through the generator — emit `{ en, fil }` pairs from the spec and look up by current locale.
4. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M9-i18n.md`.

**M8 technical debt to address in later milestones:**

- **`facility_has_bucas` / `facility_has_gamot` flags** — not in the M4 schema yet. M9 (or whichever milestone owns FAC-01..07 cross-field rules) should add these columns server-side, regenerate the master list, and extend `FacilityRow`.
- **`response_source` per-respondent capture** — currently hardcoded `source: 'pwa'`. SRC-01..03 cross-field rules want this. Wire when adding the deferred 14+ cross-field rules.
- **Sync-page "change enrollment" affordance** — `unenroll()` exists but no UI calls it. Add a button on the Sync page in M11 (or whenever multi-respondent on one device matters).
- **Auto-refresh facilities on app open** — currently only the explicit Refresh button on EnrollmentScreen calls it. Spec §7.1 prescribes StaleWhileRevalidate via the SW; consider wiring once Workbox runtime caching is configured in M11.
- **`/config` endpoint** — backend has it (returns `current_spec_version`, `kill_switch`, `broadcast_message`); PWA never calls it. M11 hardening should poll on app open to surface kill-switch + broadcast_message.

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build` — confirm M8 still green.
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build` — confirm M4 still green.
- Copy `.env.example` → `.env.local` and fill both vars from the live Apps Script deployment.
- `npm run dev`, walk through: enrollment screen → fill form → review → submit → sync — verify the submitted row's `facility_id` lands in the Sheet.
- Open `../2026-04-17-design-spec.md` §5.5 + §11.1 row M9 and `spec/F2-Spec.md` to re-orient for i18n.
