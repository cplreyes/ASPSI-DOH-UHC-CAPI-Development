# F2 PWA — Cross-Platform QA Checklist (M11)

Run through this before declaring a build pilot-eligible. Manual, single-pass. Check each item on each platform.

## Platforms

- [ ] iOS Safari 16+ on iPhone (real device if possible; otherwise DevTools responsive mode with "iPhone 14")
- [ ] Android Chrome latest on Pixel-class device (or DevTools)
- [ ] Desktop Chrome latest
- [ ] Desktop Firefox latest

## Golden path

Per platform:

- [ ] App opens at root URL; registers service worker without error (check DevTools Application → Service Workers).
- [ ] No console errors on first paint.
- [ ] Enrollment screen shows, "Refresh facility list" button pulls facilities list, dropdown populates.
- [ ] Completing enrollment navigates to the form.
- [ ] All sections render; skip logic hides irrelevant sections.
- [ ] Autosave fires (observe via DevTools → IndexedDB → f2-db → drafts, updated_at advances).
- [ ] Submit triggers thank-you screen.
- [ ] Sync view shows the row under `synced (1)` within 10s.

## Offline behavior

- [ ] Toggle DevTools offline. Submit a response. Row appears under `pending_sync`.
- [ ] Toggle online. Within 30s, row moves to `synced`.

## Runtime config

- [ ] Set `kill_switch=true` in the backend Config sheet; reopen app; overlay appears; Submit button visible but inert.
- [ ] Revert; set `broadcast_message="Test"`; reopen; banner appears at top.
- [ ] Bump `min_accepted_spec_version` to a future value; reload; forced-update modal appears; Reload button reloads the page.

## iOS polish

- [ ] Content does not hide under the notch or home indicator.
- [ ] "Add to Home Screen" installs the app; launching from home-screen icon shows standalone chrome (no Safari tab bar).
- [ ] Rotating landscape ↔ portrait preserves form state.
- [ ] `100dvh` layout: footer stays flush above the home indicator, not cut off.

## a11y (manual)

- [ ] Tab order is sensible throughout enrollment + form + sync.
- [ ] Focus is visible on every interactive element.
- [ ] VoiceOver (iOS) / TalkBack (Android) reads form labels correctly.
- [ ] Kill-switch and spec-drift overlays are announced as alertdialog with heading and body text.

## Perf

- [ ] Lighthouse PWA score ≥ 90 (run `npm run audit:pwa`).
- [ ] Lighthouse Performance ≥ 80 (manual Lighthouse run).
- [ ] Initial bundle < 300 KB gzipped (from `npm run audit:bundle`, inspect `dist/bundle.html`).

## E2E

Runtime-config scenarios are automated (`npm --prefix app run e2e`):

- [x] `kill-switch` — overlay appears on app open when flag is set
- [x] `spec-drift` — forced-update modal appears when `min_accepted_spec_version` exceeds local

Form-flow scenarios are deferred pending schema-aware helpers (Playwright can't blindly click Next through required-field validation). Walk these manually per sections above:

- `golden-path` — covered by the **Golden path** checklist above
- `offline-retry` — covered by the **Offline behavior** checklist above

## Release sign-off

- [ ] All items above green.
- [ ] `npm test` across `app/` and `backend/` — green.
- [ ] `npm --prefix app run e2e` — green.
- [ ] `npm --prefix app run typecheck` — green.
- [ ] Backend `dist/Code.gs` + `dist/Admin.html` + `dist/appsscript.json` redeployed to the Apps Script project.
- [ ] Admin dashboard loads and all three tabs populate.
