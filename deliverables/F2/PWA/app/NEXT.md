# Next step (future-Carl)

**Last milestone shipped:** M11 — Hardening / release prep. Runtime config (`/config`) is polled every 5 min and on app open; `kill_switch` blocks submit via a modal overlay; `broadcast_message` shows as a top banner; spec-version drift (server `min_accepted_spec_version` > local `LOCAL_SPEC_VERSION`) forces a reload modal. Facilities auto-refresh on app open. Sync page has a "Change enrollment" button that warns on unsaved draft. Playwright E2E covers the runtime-config scenarios (kill-switch + spec-drift) automatically; golden-path + offline-retry are stubbed (`test.skip`) pending form-schema-aware test helpers — those paths are covered by the manual QA checklist for now. vitest-axe guards a11y at component + page level. iOS safe-area + `100dvh` polish applied. `SyncPage` lazy-loaded. Cross-platform QA checklist at `../2026-04-18-cross-platform-qa-checklist.md`.

**Pilot deployed 2026-04-23:**
- Frontend: https://f2-pwa.pages.dev (Cloudflare Pages, project `f2-pwa`, branch `main`)
- Backend: Apps Script Web App — deployment ID `AKfycbwdKrp0N7aKtu3nww2AbByACSRd0JwGK5UK9yTnicuW-S51ZwiiUfgzETS9D9fQ7ovD`
- Spreadsheet: https://docs.google.com/spreadsheets/d/19huXNUO6hcNX77U7Xm63rvFFhJWGXZ7b38Rrnq8d_KY/edit
- Admin dashboard: append `?action=admin` to the `/exec` URL; use `ADMIN_SECRET` from Script Properties to log in
- Golden-path smoke test passed 2026-04-23

**Current state:** Pilot running. Collect feedback from 5–10 HCWs over 2-week dry-run. File new milestones from observations — not speculative work.

**To redeploy frontend after a change:**
```bash
cd deliverables/F2/PWA/app
npm run build
npx wrangler pages deploy dist --project-name f2-pwa --branch main --commit-dirty=true
```

**To redeploy backend after a change:**
```bash
cd deliverables/F2/PWA/backend
npm run build
# Paste dist/Code.gs into Apps Script editor → Deploy → New deployment (or Manage → edit existing)
```

**Deferred from M11 (slot in only if pilot feedback demands):**

- **Per-HCW enrollment tokens** (spec §13 row 4). Current: static enrollment — any HCW ID works once a facility is selected. Threat-model change if real deployments show cross-HCW data bleed.
- **Auto-migrate drafts across spec versions** (spec §12 row 3). Current: drift modal forces reload; drafts survive because they're in IndexedDB, but if schema shifts in a breaking way, the draft may fail validation on next save.
- **iOS push notifications for deadline reminders** (spec §13 row 5).
- **Admin dashboard mutations** (kill-switch toggle, broadcast_message editor, requeue-from-DLQ) — ops team can edit the Config sheet directly for now.

**M8/M9 tech debt still outstanding** (unchanged from prior NEXT.md):

- `facility_has_bucas` / `facility_has_gamot` flags; `response_source` per-respondent capture.
- Filipino instrument + chrome translations.

**FacilityMasterList:** Populate with real facility rows before pilot HCWs onboard. Each row: `facility_id, facility_name, facility_type, region, province, city_mun, barangay`.
