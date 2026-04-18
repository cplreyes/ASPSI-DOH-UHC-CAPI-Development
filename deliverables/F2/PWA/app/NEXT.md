# Next step (future-Carl)

**Last milestone shipped:** M5 — Sync orchestrator end-to-end. Pending submissions drain from IndexedDB to the M4 backend via HMAC-signed `batch-submit` calls, honoring the full `pending_sync → syncing → synced | rejected | retry_scheduled` state machine with exponential backoff. Triggered on online/interval/manual/post-submit. **First demo-able vertical slice.**

**Next milestone:** M6 — Facility + enrollment scaffolding. 10–15h per spec §11.1.

**Before starting M6:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §8 (Enrollment & Facility data flow).
2. Target: fetch facility list via the M4 `/facilities` endpoint on first run + every app open, cache in Dexie `facilities` table, present HCW enrollment screen (select facility, enter HCW identifier) that populates the `hcw_id` + `facility_id` used by subsequent submissions.
3. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M6-enrollment.md`.

**M5 technical debt to address in later milestones:**

- `update_available=true` is written but no banner UI exists yet. Surface in M6/M7.
- Whole-batch retry granularity — a single transport failure retries all 25 rows together. If observed in pilots, split into per-chunk fallbacks.
- No telemetry of sync outcomes yet — the M4 `/audit` endpoint is unused from the PWA side. Wire in M6 alongside facility audit events.
- Hard-coded `spec_version='2026-04-17-m1'`. Replace with a fetched value from `/config` in M7 (spec version gate milestone).
- `APP_VERSION` is a string literal in `App.tsx`. Promote to a Vite-injected build stamp before M9 (observability).

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build` — confirm M5 still green.
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build` — confirm M4 still green.
- Copy `.env.example` → `.env.local` and fill both vars from the live Apps Script deployment.
- `npm run dev`, submit a response, watch it flow to the Google Sheet.
- Open `../2026-04-17-design-spec.md` §8 to re-orient for M6.
