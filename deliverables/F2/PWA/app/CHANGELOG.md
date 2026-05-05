# Changelog

All notable changes to the F2 Healthcare Worker Survey PWA are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.0.0] — 2026-04-23

### Added

- **Section tree sidebar** — sticky desktop sidebar + responsive burger-menu drawer listing all 10 sections; badges show current (teal), completed (green checkmark), and upcoming (muted) states
- **Side arrow navigation** — fixed prev/next chevron buttons at vertical center of screen; on desktop the left arrow clears the sidebar; right arrow turns primary color on the last section to signal finish
- **Swipe gesture** — horizontal swipe >50 px (dominant axis) navigates between sections on mobile and tablet
- **Slide animation** — sections animate in from left or right depending on direction of navigation
- **Save Draft** — replaces the old bottom nav bar; a "Draft saved" confirmation appears for 2 seconds after saving
- **Question numbering** — question IDs (Q1, Q2, …) displayed as muted number prefixes so enumerators can reference items by number
- **Sticky section header** — section title and progress bar stay visible while scrolling through long sections
- **Version display** — `v1.0.0` shown as a subtle badge under the app title in the header
- **App icon** — replaced with the official DOH Philippines seal

### Fixed

- **Backend build** — `stripCjsExport` regex now correctly removes the entire `if (typeof module !== 'undefined')` block, fixing a syntax error in the generated `Code.gs`
- **Sync CORS** — POST requests now use `Content-Type: text/plain` to avoid the OPTIONS preflight that Apps Script cannot handle

## [2.0.0] — 2026-05-04

### Added

- wire staging R2 + cron, clear R2 cutover gate
- wire AS quota counter to bump on every admin RPC
- admin RPC dispatcher (Task 1.5 — keystone)
- Data Settings + QuotaWidget panels
- Data Settings + cron dispatcher + Quota
- scheduled CSV break-out (Settings CRUD + Breakout)
- Files panel — list / upload / download / delete
- admin Files dashboard end-to-end (R2 + AS metadata)
- F2_FileMeta CRUD — AdminFiles.js (create / list / get / delete)
- HCW token reissue with CAS protection (AS + Worker + Modal)
- Versioning panel + Apps dashboard shell
- force-revoke user sessions (KV + RBAC + UI)
- Roles CRUD with auto-version-bump on update
- Users CRUD mutating slice (Create / Update / Delete)
- Users + Roles list dashboards (read-only) end-to-end
- Map Report frontend + worker route
- Sync Report end-to-end (AS + Worker + Frontend)
- ResponseDetail page at /admin/data/responses/:id
- HCWs lookup tab end-to-end (AS + Worker + Frontend)
- Audit + DLQ tabs end-to-end (AS + Worker + Frontend)
- Data Dashboard with live Responses tab
- admin dashboards/data/responses + responses/:id routes
- admin_read_responses + count + by_id RPCs
- EncodeQueue + EncodePage + dev preview bypass
- paper-encoder write path — AS adminEncodeSubmit + Worker route
- F2_HCWs adminHcwsCreate + backfillHcws helpers
- submit handler writes submission_lat/lng + source_path
- wire GPS into submit flow + consent disclosure
- admin portal frontend shell — Login + auth + Layout
- add geolocation helper for submission GPS capture
- audit log writes on successful login + logout
- handleLogout writes revoked_jti and dispatcher wires logout route
- wire /admin/api/login into Worker entry via adminRouter
- admin RBAC middleware with role_version-keyed perm cache
- admin login handler with throttle + PBKDF2 verify + JWT mint
- two-axis login throttle (per-username + per-IP)
- admin JWT mint and verify with role_version + aud=admin
- Web Crypto PBKDF2 password hash + verify (100k iters, Workers cap)
- add HMAC-signed Apps Script client with request_id
- add writeAuditRow helper for admin events
- add migration script for admin sheets and column extensions

### Fixed

- file picker — accept attr + drag-drop + download attr (FX-009/010/013)
- wire QR rendering into Reissue token modal (FX-008)
- derive name from label on filter inputs (FX-014)
- extend F2_AUDIT_COLUMNS with admin-context fields (FX-006)
- populate versioning [vars] (FX-015)
- exclude /admin/\* from SW navigateFallback (FX-011)
- adminEncodeSubmit accepts payload.encoded_by
- equalize verifyPassword timing for non-existent users (S2)
- build script no longer truncates bundle on comment trap
- close username-enumeration throttle bypass
- R2-not-configured guard + clearer error UX
- three dogfood findings (file upload, naming, quota bar)
- wire Verde Manual color aliases + bump modal scrim
- handleLogin reads role_name (sheet column) with role fallback
- login can read password_hash via include_password_hash flag
- use getScriptLock, not getDocumentLock; add seed script
- resolve spreadsheet via SPREADSHEET_ID, not getActiveSpreadsheet
- pre-enrollment refresh uses verified token (#53)

### Changed

- MultiSectionForm gains mode prop + Promise-tolerant onSubmit
- add F2_ADMIN_R2 binding and 5-minute cron trigger
- v1.2.0 — UAT Round 3 / Feature batch — sync CHANGELOG + version
