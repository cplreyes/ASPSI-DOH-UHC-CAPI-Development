# Next step (future-Carl)

**Last milestone shipped:** M11 — Hardening / release prep. Runtime config (`/config`) is polled every 5 min and on app open; `kill_switch` blocks submit via a modal overlay; `broadcast_message` shows as a top banner; spec-version drift (server `min_accepted_spec_version` > local `LOCAL_SPEC_VERSION`) forces a reload modal. Facilities auto-refresh on app open. Sync page has a "Change enrollment" button that warns on unsaved draft. Playwright E2E covers the runtime-config scenarios (kill-switch + spec-drift) automatically; golden-path + offline-retry are stubbed (`test.skip`) pending form-schema-aware test helpers — those paths are covered by the manual QA checklist for now. vitest-axe guards a11y at component + page level. iOS safe-area + `100dvh` polish applied. `SyncPage` lazy-loaded. Cross-platform QA checklist at `../2026-04-18-cross-platform-qa-checklist.md`.

**Next decision (not a milestone):** Pilot readiness per spec §11.2 checkpoint row M11. Three options:

1. **Run the pilot now.** 5–10 HCWs, one facility, 2-week dry-run. Ship `dist/` + deploy Apps Script + redeploy Cloudflare Pages. Collect feedback. File new milestones from observations (not speculative work).
2. **Close deferred M11 items first** (below) before pilot.
3. **Move to M12 (F3/F4 parity)** if ASPSI says PWA-Plan-B is gated behind PWA supporting more instruments.

**Deferred from M11 (slot in only if pilot feedback demands):**

- **Per-HCW enrollment tokens** (spec §13 row 4). Current: static enrollment — any HCW ID works once a facility is selected. Threat-model change if real deployments show cross-HCW data bleed.
- **Auto-migrate drafts across spec versions** (spec §12 row 3). Current: drift modal forces reload; drafts survive because they're in IndexedDB, but if schema shifts in a breaking way, the draft may fail validation on next save.
- **iOS push notifications for deadline reminders** (spec §13 row 5).
- **Admin dashboard mutations** (kill-switch toggle, broadcast_message editor, requeue-from-DLQ) — ops team can edit the Config sheet directly for now.

**M8/M9 tech debt still outstanding** (unchanged from prior NEXT.md):

- `facility_has_bucas` / `facility_has_gamot` flags; `response_source` per-respondent capture.
- Filipino instrument + chrome translations.

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build && npm run e2e`
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build`
- Redeploy `dist/Code.gs` + `dist/Admin.html` + `dist/appsscript.json` to Apps Script if backend changed.
- Copy `.env.example` → `.env.local` and fill both vars.
- `npm run dev`, walk the golden path. Open Admin URL and confirm login.
- Work through `../2026-04-18-cross-platform-qa-checklist.md` on at least iOS Safari + Desktop Chrome before declaring pilot-ready.
