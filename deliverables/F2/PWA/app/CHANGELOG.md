# Changelog

All notable changes to the F2 Healthcare Worker Survey PWA (HCW Survey side + Admin Portal side) are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

> The canonical source for release narratives is the project's [GitHub Releases](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases). This file is the human-curated index — it consolidates the GH Release narratives into one chronological view and adds an `[Unreleased]` slot for work that's shipped to production but not yet tagged.

---

## [2.0.2] — 2026-05-12

Nine PRs merged + verified on production 2026-05-12 (Sprint 005 Day 2 — R3 prep + v2.0.2 quality slate, plus the CHANGELOG/release-notes alignment pass that bumped this version). All changes are live at `f2-pwa.pages.dev`.

### Improved (HCW survey side)
- **Enrollment URL auto-prefill** — opening an enrollment link of the shape `/enroll?token=eyJhbGc...` now pre-fills the token textbox and enables the Verify button immediately. Pre-fix, testers and HCWs had to copy the JWT out of the address bar by hand. ([PR #279](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/279))
- **Faster first-paint** — the admin portal code (~330 KB raw / 61 KB gzipped) is now lazy-loaded only when an admin route is visited. HCW respondents' initial JS payload dropped from **930 KB raw / 250 KB gzipped → 608 KB raw / 188 KB gzipped** (35% / 25% reduction). ([#275](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/275), [PR #281](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/281))
- **Self-hosted Verde Manual fonts** — Newsreader, Public Sans, JetBrains Mono now ship from `/fonts/*` instead of a third-party CDN. 22 woff2 files (333 KB), runtime-cached after first use. ([#162](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/162), [PR #274](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/274))
- **Compound-field a11y** — Q1 (name: Last/First/Middle) and Q9 (tenure: Year/Month) now use `<fieldset><legend>` semantics. Screen readers announce the question text on each sub-input; clicking the question label focuses the first sub-input. ([#277](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/277), [PR #281](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/281))

### Improved (Admin Portal side)
- **Slim no-auth Help shell** — unauthenticated visitors to `/admin/help` now see only the Help link in the sidebar plus a "Sign in" CTA, instead of the full operator nav with dead-end dashboard links + a non-functional Sign-out button. ([#278](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/278), [PR #281](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/281))
- **Map Report — selected marker visually highlighted** — clicking a marker now enlarges it (24px) and adds an outer ring in the primary tone. Pre-fix, only the sidebar HoveredCard reflected the selection; the map pin looked identical to its neighbors. ([PR #288](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/288))
- **Map Report — honest sidebar label** — renamed "By region" → "By facility prefix". The old label grouped by the first 2 chars of `facility_id`, which only encodes a real region for facilities following the PSGC numeric pattern. On demo data (`DEMO-FAC-DH-INFANTA`), groupings were `DE`, `RH`, etc. — meaningless. Smart extraction now keeps 2-digit PSGC prefixes verbatim and lowercases alphabetic prefixes as a visible "this is demo data" cue. ([PR #288](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/288))

### Fixed
- **HelpPage — bulk import row limit** — Workflow #4 said "Maximum 500 rows per import call"; the Worker actually enforces 100. ([#208](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/208), [PR #274](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/274))
- **HelpPage — Versioning panel description** — the Apps & Settings Help row claimed "PWA bundle SHA, Worker version, Apps Script deployment, latest spec_version" but the panel doesn't actually render the Apps Script deployment ID. Description now reflects what's shown: PWA version + bundle SHA, Worker version, last Pages deploy, form_revisions table. ([#208](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/208), [PR #274](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/274))
- **HelpPage — Roles table** — DataReader / Encoder no longer falsely labeled "(custom)"; whether a role is `is_builtin` depends on the cutover seed pass, not on UI. ([#208](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/208), [PR #274](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/274))
- **`/admin/help` URL race** — pre-fix, navigating to `/admin/help` while signed out caused a useEffect to push history to `/admin/login` while the render branch returned the HelpPage in its Layout. The URL bar and the visible content were mismatched. ([PR #279](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/279))
- **Sidebar version footer** — was hardcoded as the literal `v0.1.0-staging` even on production. Now reads `__APP_VERSION__` (e.g., `v2.0.0`). ([PR #279](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/279))
- **Map Report — broken "X without GPS" link** — pre-fix linked to `/admin/data?tab=responses&q=submission_lat`, which is a free-text search over HCW IDs, not a column-name filter. Click → user saw noise. Link dropped; plain text count rendered. A real `no_gps=1` filter is tracked as a v2.0.2 follow-up. ([PR #288](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/288))

### Internal / DX
- **17 ESLint warnings cleared** (0 errors, 0 warnings on `npm run lint`). React-hooks/exhaustive-deps + react-refresh fixes. Includes `useCallback` memoization of `pages-router.tsx` `navigate`. ([PR #285](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/285))
- **Performance baseline doc** — `deliverables/F2/PWA/app/PERFORMANCE.md` with Lighthouse scores + bundle-size budget + regression-tracking guidance. Initial measurement: HCW root **0.91**, Admin login **0.93** (post-bundle-split). ([#192](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/192), [PR #276](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/276))
- **Backup + restore runbook** — `docs/superpowers/runbooks/2026-05-12-f2-pwa-backup-restore.md` covering Google Sheet + R2 + KV layers, restore drill schedule. ([#173](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/173), [PR #276](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/276))
- **Secrets rotation policy** — `docs/superpowers/runbooks/2026-05-12-f2-secrets-rotation.md` covering all 6 secret-bearing surfaces (JWT signing, HMAC, AS deployment, R2 access, Gmail, admin user passwords). Annual May 1 rotation checklist. ([#172](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/172), [PR #276](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/276))
- **3 new vitest-axe tests** on admin Login, HelpPage, Layout shell (all pass at AA). Lighthouse a11y on HCW root + admin login: 1.0/100. ([#191](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/191), [PR #274](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/274))
- **CF Pages deploy workflow is branch-aware** — `VITE_F2_PROXY_URL` now resolves per branch (`main` → prod worker; `staging` → staging worker, when `VITE_F2_PROXY_URL_STAGING` secret is set; falls back to prod URL otherwise). ([#282](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/282), [PR #283](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/283))
- **R3 tester guides updated** to reflect today's prod state (URL token prefill, /admin/help URL stability, version footer correctness). ([PR #280](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/280))

### Filed for the next slate
- **#273** authenticated-state a11y audit
- **#284** modal overlay focus-trap (kill-switch + spec-drift)
- **#286** local `Marker` interface rename in MapReport
- **#287** Leaflet markers keyboard a11y

---

## [2.0.1] — 2026-05-09

Admin Portal R2 fix wave + v2.0.1 patch bundle. PR [#136](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/136) merged at `9bab42b` (26 commits, +16,779/-394). Deployed to prod 2026-05-09 07:42 UTC. 24 issues auto-closed via `Closes #N` trailers.

### Added
- **Create HCW modal** — first-class UI for minting new HCW enrollments, replacing the workaround of hand-editing the F2_HCWs sheet. ([#58](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/58) — E4-APRT-041)
- **User self-service password rotation** — admin user can change own password via sidebar menu → Change password. ([#134](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/134) — E4-APRT-051)

### Fixed
- **RBAC role-version cache** — revoked permissions no longer persist up to 60 min after role demotion. Cache invalidates on role_version bump. ([#56](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/56) — E4-APRT-044)
- **JWT password_must_change server-enforce** — was client-side-only check; now Worker rejects mutation endpoints with `password_must_change=true` JWTs. ([#57](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/57) — E4-APRT-045)
- **`last_login_at` write** — column wasn't being populated on successful login; now writes timestamp on each login. ([#66](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/66) — E4-APRT-048)
- **Orphan-admin guards** — prevent deletion / role-change of the last remaining Administrator user. ([#133](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/133) — E4-APRT-050)
- **DLQ UTF-8 handling** — non-ASCII characters in DLQ payloads now render correctly. ([#93](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/93))
- **Bulk import validation** — clearer error surfacing when role names don't resolve or duplicate usernames exist. ([#98](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/98), [#100](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/100))
- **DLQ async write fallback** — `DLQ` parking persists even when the synchronous write fails; async retry with cleaner error log. ([#84](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/84))

### Improved
- **Design-review 5-fix sweep** — button focus rings visible on Tab nav, dropped `rounded-full` shapes on filter pills/badges, ReissueTokenModal closes on Escape, QuotaWidget warning uses warm-amber `--warning` token (not red `--error`), additional polish. ([#59](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/59) / [#60](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/60) / [#61](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/61) / [#62](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/62) / [#67](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/67) / [#132](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/132) — E4-APRT-049)
- **Concurrency test suite** — added explicit tests for two-admin-concurrent operations (reissue token CAS, role edit while user is logged in). ([#63](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/63))
- **R2 fix wave** — closes the mid-Sprint 004 R2 wave: `#69`, `#108`, `#109`, `#110`, `#114`, `#117`, `#119`, `#120`, `#122` (token paste edge cases, Q9 year+month required enforcement, Section G back-nav, Section J matrix, submission + sync UX).

---

## [2.0.0] — 2026-05-04

**Admin Portal Goes Live.** First major release with both HCW survey + Admin Portal in production. Released to production 2026-05-04 evening (soak gate explicitly waived per UAT Round 2 demo timing). [GitHub Release](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v2.0.0).

### Added — Admin Portal (new)
- **F2 Admin Portal** at `f2-pwa.pages.dev/admin` — operations console for ASPSI ops staff. Mirrors the CSWeb dashboard model: 5 dashboards × 5 roles × per-instrument flags.
- **Data dashboard** — Responses (filterable, click-through to full response), Audit (forensic event log), DLQ (parked submission failures), HCWs (enrollment registry with Reissue Token + revoke + per-HCW history).
- **Reports dashboard** — Sync Report (coverage by region / province / facility), Map Report (geographic plot of submissions from captured GPS).
- **Apps & Settings dashboard** — Versioning (live build identifiers + per-spec submission counts), Files (operator file uploads — PDF/ZIP/PNG/JPEG/GIF up to 100 MB, stored in Cloudflare R2), Data Settings (scheduled CSV break-out exports, cron-fired every 5 min), Apps Script Quota (daily 20,000-call execution counter).
- **Users dashboard** — CRUD for ops staff accounts, Bulk Import via CSV (max 100 rows per call), force-revoke active sessions, last_login_at tracking.
- **Roles dashboard** — Permission matrix editor with auto-version-bump on update (invalidates existing JWTs against the old version).
- **Encode dashboard** — paper-response transcription flow; encoded responses tagged `source_path=paper_encoded` for distinguishing from self-admin submissions.
- **Help dashboard** — operator guide (workflows, glossary, role permissions table). Accessible without login.
- **GPS submission capture** — HCW PWA captures `submission_lat` / `submission_lng` at submit time (with consent disclosure per spec §9), surfaced on the Map Report.
- **Audit trail** — every admin mutation writes a row to F2_Audit with actor + resource + request_id traceable.

### Added — HCW survey side
- **Verde Manual visual identity** — pale verde paper `#F2F5EE`, DOH emerald `#006B3F`, Newsreader serif h1/h2, Public Sans body, JetBrains Mono on version + eyebrows.

### Changed
- **Worker JWT proxy** replaces the prior HMAC-in-bundle auth model (security audit critical finding). Per-tablet device tokens issued via the admin's Reissue flow; HCW PWA carries only its own JWT, not the global HMAC.
- **Cron + R2** wired into the Worker (`*/5 * * * *` trigger; F2_ADMIN_R2 binding for admin file uploads + scheduled break-outs).
- **Permission model** mirrors CSWeb 1:1 — same dashboard + per-instrument up/download flag axes the F1/F3/F4 CSPro track will use.

### Notes
- **Production deployment is internal-only.** The Admin Portal is not linked from the public HCW survey shell.
- **Login**: usernames + initial passwords issued out-of-band to onboarded staff. Initial password requires rotation on first login.
- **Permissions**: ASPSI ops can request additional roles or per-instrument permission edits via the Admin Portal Users + Roles dashboards.

---

## [1.3.0] — 2026-05-01

**Round 3 Internal QA.** Comprehensive internal QA pass before opening UAT Round 3. 13 issues fixed across HCW survey shell. [GitHub Release](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.3.0).

### Fixed
- **[HIGH]** Q4/Q9/Q10/Q11 — raw Zod error "Expected number, received nan" leaks to UI ([#19](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/19))
- Q1_3 Middle Initial should be optional (same pattern as #14) ([#25](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/25))

### Improved
- **[HIGH]** Section F/G multi-select state pollution — selections unchecked when answering other questions ([#33](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/33))
- Test Facility present in seed/cached facility list (also on staging) ([#28](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/28))
- Inconsistent "Other" label casing — Q2 comma form vs Q5 parens form ([#26](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/26))
- Default button height was 32 px (below 44 px tablet touch-target minimum) ([#23](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/23))

### Internal / DX
- **[HIGH]** Enroll button no-op on real-browser staging (verified token, no IDB write, no error) ([#46](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/46))
- **[HIGH]** Build-time guard for `VITE_F2_PROXY_URL` (missing env silently broke staging build) ([#45](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/45))
- Worker PBKDF2 default lowered from 600k → 100k iters (Cloudflare Workers runtime cap) ([#35](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/35))
- **[HIGH]** CF Pages auto-deploy on staging push not firing — diagnosed (resolved later via GitHub Actions workflow) ([#34](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/34))
- Header subtitle low contrast — used `--muted` instead of `--muted-foreground` ([#30](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/30))
- Right-edge floating arrow indicator clipped off-screen at 375 px viewport ([#29](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/29))
- Locked sidebar sections appeared as enabled buttons in the a11y tree ([#27](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/27))
- No visible focus ring on keyboard Tab navigation ([#24](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/24))
- **[HIGH]** Disabled buttons failed WCAG AA contrast — opacity:0.5 on teal → ~2:1 ([#22](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/22))
- **[HIGH]** Form layout pushed off-center on viewports ≥1600 px ([#21](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/21))
- **[HIGH]** Inverted heading hierarchy — page H1 (18 px) smaller than section H2 (24 px) ([#20](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/20))

---

## [1.2.0] — 2026-05-01

**UAT Round 3 / Feature batch.** Three R3-targeted UX improvements to multi-select question handling. [GitHub Release](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.2.0).

### Improved
- **Matrix view for scale-style questions** — Section J Likert-grid questions now render as a 2-way matrix (statements as rows, scale points as columns) instead of one Likert question per row ([#18](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/18))
- **"All of the above" auto-select** — selecting "All of the above" in a multi-select now auto-checks every other option ([#17](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/17))
- **Exclusive "I don't know"** — selecting "I don't know" in a multi-select now clears all other selections (and vice versa) ([#16](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/16))

---

## [1.1.1] — 2026-04-25

**UAT Round 2.** 6 issues fixed across the HCW survey shell after Round 2 testing. [GitHub Release](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.1.1).

### Fixed
- **[CRITICAL]** Cannot proceed when gating question answered "No" (Q12, Q31, similar) ([#15](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/15))
- Q9: Month(s) field should be optional, not required ([#14](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/14))
- **[HIGH]** Test Scenario Observations ([#12](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/12))
- Tenure (months/years) display + handling polish ([#3](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/3))
- Age display + handling polish ([#1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/1))

### Improved
- "What is your role at this health facility?" — specialty filtered by role so dentists no longer see medical specialties etc. ([#2](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/2))

---

## [1.1.0] — 2026-04-25

**UAT Round 1.** 7 issues fixed across the HCW survey shell after Round 1 testing. [GitHub Release](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.1.0).

### Fixed
- **[CRITICAL]** Auto-Advance Issue on Required Questions ([#10](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/10))
- **[HIGH]** Mid-section skip logic — conditional jumps not enforced (Q34/Q38/Q39/Q44/Q48/Q53/Q69/Q70/Q87/Q88) ([#13](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/13))
- **[HIGH]** Section Applicability — Section G now hidden for non-Physician roles ([#11](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/11))
- **[HIGH]** Q25 — conditional logic restriction ([#8](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/8))
- **[HIGH]** Q12 UHC awareness gating ([#6](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/6))
- Tenure (months/years) display polish ([#5](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/5))
- Age display polish ([#4](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/4))

---

## [1.0.0] — 2026-04-22

**F2 PWA Pilot Release.** First production-shaped release of the HCW survey PWA. [GitHub Release](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.0.0).

### Added
- **Section tree sidebar** — sticky desktop sidebar + responsive burger-menu drawer listing all 10 sections; badges show current (teal), completed (green checkmark), upcoming (muted) states.
- **Side arrow navigation** — fixed prev/next chevron buttons at vertical center of screen; right arrow turns primary color on the last section to signal finish.
- **Swipe gesture** — horizontal swipe >50 px navigates between sections on mobile and tablet.
- **Slide animation** — sections animate in from left or right depending on direction of navigation.
- **Save Draft** — replaces the old bottom nav bar; "Draft saved" confirmation appears for 2 seconds after saving.
- **Question numbering** — question IDs (Q1, Q2, …) displayed as muted number prefixes so enumerators can reference items by number.
- **Sticky section header** — section title + progress bar stay visible while scrolling through long sections.
- **Version display** — `v1.0.0` shown as a subtle badge under the app title in the header.
- **App icon** — official DOH Philippines seal.

### Fixed
- **Backend build** — `stripCjsExport` regex now correctly removes the entire `if (typeof module !== 'undefined')` block, fixing a syntax error in the generated `Code.gs`.
- **Sync CORS** — POST requests use `Content-Type: text/plain` to avoid the OPTIONS preflight that Apps Script cannot handle.

---

[Unreleased]: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/v2.0.2...main
[2.0.2]: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v2.0.2
[2.0.1]: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v2.0.1
[2.0.0]: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v2.0.0
[1.3.0]: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.3.0
[1.2.0]: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.2.0
[1.1.1]: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.1.1
[1.1.0]: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.1.0
[1.0.0]: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.0.0
