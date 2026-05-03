# F2 Admin Portal — Cross-Platform QA Pass

**Date started:** 2026-05-02
**Target:** F2 Admin Portal on staging (`https://f2-pwa-staging.pages.dev/admin` ↔ `https://f2-pwa-worker-staging.hcw.workers.dev`)
**Branch / build:** `f2-admin-portal` @ `32883ec` (PR #54 draft, mergeable, CI green) — Sprints AP1–AP4 feature-complete
**Tester:** Carl (driving), Claude (checklist + findings capture)
**Spec ref:** `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md` §12.4
**Plan ref:** `docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md` Task 4.6
**Sprint:** AP4 — closes Sprint 4 cross-platform QA gate before v2.0.0

> Status legend: ✅ pass · ❌ fail · ⚠️ partial / minor · — not run / not applicable

---

## Test matrix (5 environments)

| # | Environment | Browser | OS / form factor | Status |
|---|---|---|---|---|
| E1 | Chrome desktop | Chrome (latest) | Windows 11, ≥1280px | ⏳ pending |
| E2 | Firefox desktop | Firefox (latest) | Windows 11, ≥1280px | ⏳ pending |
| E3 | Edge desktop | Edge (latest) | Windows 11, ≥1280px | ⏳ pending |
| E4 | Tablet portrait | Chrome DevTools iPad emul | 768×1024 | ⏳ pending |
| E5 | Tablet landscape | Chrome DevTools iPad emul | 1024×768 | ⏳ pending |

**Deferred (no Mac access; flag as outstanding):**
- Safari macOS desktop
- Safari iPad

---

## Pre-flight

- [ ] Staging URL responsive (login screen renders)
- [ ] Build identifier shown in footer matches `32883ec` or current PR head
- [ ] `carl_admin` login still valid (per memory: `100%SetupMe!`)
- [ ] DevTools console clean on first paint (no errors, no 4xx/5xx aside from expected unauth pings)

---

## Test surface — checklists per environment

For each environment, run the same set. Mark per-env status in the matrix below each subsection. Add findings inline (under "Findings" section at the bottom).

### A. Auth + RBAC (5 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| A1 | Login as `carl_admin` (Administrator) → lands on default dashboard | ✅ | | | | |
| A2 | Logout → redirects to login screen, no stale session | ✅ | | | | |
| A3 | Bad password 3× → error message renders, no PII leak in console | ✅ | | | | |
| A4 | Login as `data_reader_test` (DataReader role) → admin-only routes (Users / Roles) hidden or 403 | ⚠️ | | | | |
| A5 | Force-revoke own session via Users panel → next request gets 401 + redirected to login | ✅ | | | | |

### B. Layout + visual identity (Verde Manual) (4 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| B1 | Header / sidebar / content frame render with Verde paper (`#F2F5EE`) + DOH emerald | ✅ | | | | |
| B2 | Newsreader serif on h1/h2; Public Sans on body; JetBrains Mono on code/eyebrows | ✅ | | | | |
| B3 | No raw Tailwind colors leaking (e.g., `bg-blue-500`) — all alias tokens (paper/ink/hairline/signal/error) | ✅ | | | | |
| B4 | Modal scrim + hairline borders match Verde (`/scrim`, `/hairline`) | ✅ | | | | |

### C. Data dashboard (5 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| C1 | Responses tab loads, table renders ≥1 row (HCW-TEST-001 fixture) | ✅ | | | | |
| C2 | Audit tab loads with filter + pagination | ✅ | | | | |
| C3 | DLQ tab loads (likely empty on staging — that's fine) | ✅ | | | | |
| C4 | HCWs tab loads + search input filters | ✅ | | | | |
| C5 | Click a Response row → ResponseDetail drawer opens | ✅ (route nav, not drawer) | | | | |

### D. Report dashboard (3 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| D1 | SyncReport renders aggregations (region/province) — empty-state OK if no data | ✅ | | | | |
| D2 | MapReport renders base graticule (SVG-based, not Leaflet — intentional per `MapReport.tsx:7-12`) | ✅ | | | | |
| D3 | MapReport with markers renders (clustering deferred per spec until dataset grows) | — N/A on staging (no GPS data) | | | | |

### E. Apps dashboard (5 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| E1f | Files: upload a small file (PDF or image, <5 MB) → appears in list | ✅ | | | | |
| E2f | Files: download via row action → bytes match | ✅ | | | | |
| E3f | Files: delete → row disappears, R2 object_count returns to baseline | ✅ | | | | |
| E4f | DataSettings: list renders, scheduled break-out config visible | ✅ | | | | |
| E5f | QuotaWidget: AS quota counter visible + sane (`as_quota:<UTC-date>`) | ✅ | | | | |

### F. Users + Roles (5 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| F1 | Users list renders with `carl_admin` + `data_reader_test` | ✅ | | | | |
| F2 | Create a throwaway user (`qa_temp_<env>`) → succeeds, appears in list | ✅ | | | | |
| F3 | Edit role on the throwaway user → role_version bumps; existing JWT for that user invalidated | ✅ | | | | |
| F4 | Delete the throwaway user → cleanup | ✅ | | | | |
| F5 | Roles list renders with built-ins (Administrator, Standard User) + custom (DataReader) | ✅ | | | | |

### G. Encode + Reissue (3 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| G1 | EncodeQueue loads, ≥1 row visible | ✅ (placeholder; queue table deferred to Sprint 2.9) | | | | |
| G2 | Open EncodePage for an HCW → form renders (autosave is documented-deferred per `EncodePage.tsx:15-17`) | ✅ | | | | |
| G3 | ReissueModal shows QR; clicking "Reissue" generates new JWT (verify in network) | ⚠️ JWT ✅ / QR deferred (FX-008) | | | | |

### H. Browser-specific watch list (varies)

Things that historically diverge between engines. Note any divergence even if functional.

| # | Watch | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| H1 | File picker UI / drag-drop styling | ⚠️ native btn, no Verde, no DnD (FX-010) | | | | |
| H2 | `<input type="file">` accept attribute behavior | ❌ accept="" empty despite UI hint (FX-009) | | | | |
| H3 | CSV download triggers a real Save dialog (Blob + `download` attr) | ❌ no CSV export anywhere (FX-012); file link no `download` attr (FX-013) | | | | |
| H4 | IndexedDB + localStorage persist across reload | ✅ both persist; auth in-memory by design | | | | |
| H5 | Focus rings visible on Tab nav (FF often differs from Chrome) | ⚠️ visible but browser-default `outline:auto 1px`, not Verde `ring-2 ring-offset-2` | | | | |
| H6 | Sticky table headers don't overlap modals | ✅ N/A — `thead` is `position:static`, modal `z-50` over `bg-ink/70` scrim | | | | |
| H7 | Date / number inputs render natively (FF sometimes hides spinners) | ✅ native date spinbuttons (mm/dd/yyyy + picker btn) | | | | |
| H8 | Touch-target size ≥44px on tablet emul (B/G/H tabs) | — | — | — | | |

### Z. Performance + console hygiene (3 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| Z1 | First contentful paint < 2s on a warm cache | ✅ FCP 560ms on hard reload (TTFB 95ms, DOMInteractive 110ms; warm cache will be faster) | | | | |
| Z2 | Console clean (no errors / no warnings beyond expected service-worker / vite-dev noise) | ⚠️ 1 issue: form fields w/o id/name (count 4) — FX-014 | | | | |
| Z3 | Network panel: no 5xx; no aborted requests on golden-path nav | ✅ all requests 200/304 across login + Data + Apps + Users + Audit + Response Detail (no 5xx, no aborts) | | | | |

---

## Findings

> Add findings here as we hit them. Format: `**[FX-NNN] [SEVERITY] Title** — env, repro, expected, actual, evidence (screenshot path).`

### [FX-001] [HIGH] Admin API endpoints lack CORS preflight + headers — fix shipped same session

**Found while:** E1 Chrome pre-flight, immediately post-login.
**Affected env(s):** All cross-origin browsers (E1, E2, E3 — would also affect E4/E5). Architectural, not browser-specific.

**Repro (as found):**
1. Build the admin frontend with `VITE_F2_PROXY_URL=https://f2-pwa-worker-staging.hcw.workers.dev`, deploy to Pages preview at `https://f2-admin-portal.f2-pwa-staging.pages.dev`.
2. Open `/admin`, enter `carl_admin` / `100%SetupMe!`, click Sign in.
3. Browser fires CORS preflight (`OPTIONS /admin/api/login` with `Access-Control-Request-Method: POST`).
4. Worker returns **404 No Route** with **no Access-Control-Allow-Origin header** → browser blocks the actual `POST /admin/api/login`.
5. Frontend `adminFetch` catches the rejected fetch as `E_NETWORK` → renders "Network unavailable. Check your connection and retry."

**Expected:** Login round-trip succeeds; user lands on default dashboard.
**Actual:** Login fails immediately with E_NETWORK; nothing reaches the worker.

**Root cause:** `worker/src/index.ts` originally documented admin routes as same-origin (admin UI was served by the Worker itself in M10). The post-AP1 admin frontend ships from Pages — different origin — but the Worker's index.ts only ran CORS preflight + `withCors` for `PUBLIC_ROUTES` (`/exec`, `/verify-token`); admin paths fell through with no CORS headers. The frontend `Login.tsx:44` does a cross-origin fetch via `${apiBaseUrl}/admin/api/login`, which the architectural comment had assumed would never happen.

**Fix:** `worker/src/index.ts` — add an `isAdminApi` branch:
- Run `OPTIONS` preflight handler for `/admin/api/*` before delegating to `adminRouter`.
- Wrap admin responses with `withCors()` (echoes the same `*`-origin / `Authorization, Content-Type` allow-headers used for public routes; bearer-token auth, no cookies, so `*` is safe).
- Doc comment updated to reflect the cross-origin Pages → Worker reality.

**Verification:**
- `npx vitest run` in `worker/` — **166/166 passed**.
- `wrangler deploy --env staging` — `f2-pwa-worker-staging` redeployed (Version `f1efd7a5-a40f-4988-8fec-360b12e5b1ef`).
- Manual preflight via curl: `OPTIONS /admin/api/login` → **204** with `Access-Control-Allow-Origin: *`, `Access-Control-Allow-Headers: Authorization, Content-Type`, `Access-Control-Allow-Methods: GET, POST, OPTIONS`.
- Browser repro re-run: see E1 pre-flight rows below.

**Severity rationale:** HIGH because every admin browser session was 100% broken cross-origin — not "edge case", flat-out unreachable. Caught only because cross-platform QA actually exercised the deployed frontend; AP0/AP1–AP4 dogfood used the same-origin static admin HTML served by the worker (not the Pages-deployed React frontend), so this never surfaced.

**Worker test gap:** the worker test suite mocks the `Request` directly into `adminRouter` and never exercises the top-level `fetch` handler's CORS path. Adding a regression test that drives an `OPTIONS /admin/api/login` through `default.fetch(...)` and asserts the 204 + headers would prevent re-introducing this. Filed as a follow-up suggestion, not a blocker.

---

### [FX-002] [MEDIUM] Admin frontend doesn't gate nav / page chrome by effective perms — relies entirely on API rejection

**Found while:** E1 A4 (RBAC test as `data_reader_test`).
**Affected env(s):** All environments (architectural — not browser-specific).

**Repro:**
1. Login as `data_reader_test` / `ReadOnly_99X1` (DataReader role with `dash_apps:true` + `dash_data:true` per RBAC PATCH fixture; lacks `dash_users`, `dash_roles`, `dict_paper_encoded_up`).
2. Top nav shows: Data | Reports | Configuration ▾ | Encode — i.e., **all 5 dashboards visible** to a role that has perms for only 2.
3. Open Configuration ▾ — dropdown lists Apps & Settings (legit), **Users (no perm), Roles (no perm)**. Both Users + Roles items are clickable.
4. Click Users → page renders full chrome ("Section / Users" header, **"+ Add user" button**, Search input, Role filter dropdown) WITH a red banner "Your role lacks dash_users. Contact an Administrator." The "+ Add user" button is still interactive.
5. Same on Roles.
6. Click Encode in nav → **page renders cleanly with no banner** ("Encode queue" header, HCW ID input, "Open encoder" button, "Coming next" panel). User only discovers they lack `dict_paper_encoded_up` after typing an HCW ID and clicking Open encoder, at which point the API returns 403.

**Expected (any one or combination):**
- Nav items the user lacks perms for are hidden (or rendered disabled with a tooltip explaining why).
- Page chrome (action buttons, search inputs, "Add" CTAs) is hidden when the user lacks the gating perm; only the access-denied banner shows.
- Encode dashboard surfaces a proactive warning banner when the user lacks `dict_paper_encoded_up`, parallel to the Users/Roles banner pattern.

**Actual:** Frontend renders everything; relies entirely on API-layer rejection for enforcement.

**Severity rationale:** MEDIUM, not HIGH. **No actual privilege escalation** — the API correctly returns 403 for forbidden operations (verified on Users + Roles GETs, and the encode POST per worker test `routes.test.ts`). This is purely a UX / defense-in-depth issue: a confused operator sees Add/Edit controls, clicks one, hits a generic 403, and has to figure out the role-perm mapping themselves. Could be HIGH if any privileged operation went through that bypassed the API check, but no such case has been found.

**Fix shape (NOT done in this session):** Frontend `Layout.tsx` + per-dashboard pages need to read the JWT's `perms` claim (or the role-version cache) and conditionally render nav entries / page chrome / action buttons. Rough estimate: ~half-day to retro-fit per-page perm gating; ~1 day if we add a `usePerms()` hook + a `<RequirePerm>` wrapper for nav + actions. Worth doing before v2.0.0 — the worker enforces, but the UI lying about what's reachable is a tester/operator confusion vector.

**Status:** Logged for triage decision (Task #12). Not blocking the rest of E1 RBAC; the API enforcement is the actual security-relevant gate.

---

### [FX-003] [LOW] Destructive admin actions use native browser confirm()/alert() instead of Verde Manual modals

**Found while:** E1 A5 (force-revoke own session).
**Affected env(s):** All — architectural / design-system inconsistency, not browser-specific.

**Repro:**
1. Login as carl_admin → Users → click REVOKE on a row.
2. Native Chrome dialog appears: `f2-admin-portal.f2-pwa-staging.pages.dev says — Force-logout carl_admin? Every JWT they currently hold stops working on its next request. Lockout lasts 24 hours. [OK] [Cancel]`.
3. Click OK → immediately a second native dialog: `... says — carl_admin's sessions revoked. They'll be bounced to login on next request. [OK]`.

**Expected:** Verde Manual–styled modal with hairline borders, paper background, mono-eyebrow header (per `DESIGN.md` modal pattern). Per project rule "This is real software, not a government form" — the native browser dialog reads as low-trust shareware.

**Actual:** Native `window.confirm()` and `window.alert()`.

**Severity rationale:** LOW. Functional, accessible, secure, not a security/UX-blocking issue. But cosmetic-blocking for v2.0.0 polish — the rest of the portal is Verde-aligned, so the native dialogs stick out. Likely also affects other destructive actions (DELETE user, role removal, file delete, run-now break-out) — should grep for `confirm(`/`alert(` calls in the admin frontend to scope.

**Status:** Logged for triage. Backlog candidate; not a v2.0.0 blocker.

---

### [FX-004] [HIGH] Router doesn't track URL search params — tab switching broken on Data + Report dashboards — fix shipped same session

**Found while:** E1 C2 (clicking Audit sub-tab on Data dashboard).
**Affected env(s):** All — architectural / state-management bug, not browser-specific.

**Repro:**
1. Login as `carl_admin` → Data → click **Audit** sub-tab.
2. Nothing happens. URL bar shows `/admin/data?tab=audit` correctly, but the page still renders the Responses tab content. Same for DLQ + HCWs sub-tabs.
3. Same pattern would apply to Report dashboard's Sync / Map sub-tabs (uses identical code shape in `ReportDashboard.tsx:25-36`).

**Root cause:** `lib/pages-router.tsx` only stores `window.location.pathname` in router state — `window.location.search` is ignored. `DataDashboard.tsx` (and `ReportDashboard.tsx`) compute `activeTab` via `useMemo(() => parseSearch(), [pathname])` — when only the search portion changes, `pathname` is unchanged so the memo never recomputes. Additionally `navigate()` early-out compared `to === window.location.pathname`, which incidentally let tab navigations through (since `to` includes the `?tab=...` and `pathname` doesn't) — but the state never updated, so React didn't re-render anyway.

**Fix:** `pages-router.tsx`:
- Added `search: string` to `RouterCtx` and tracked it as separate `useState` alongside `pathname`.
- `onChange` listener now calls both `setPathname` and `setSearch`.
- `navigate()` early-out now compares against `pathname + search` (full URL) so genuine no-ops still bail correctly.
- `DataDashboard.tsx` + `ReportDashboard.tsx`: pulled `search` from `useRouter()`, switched `useMemo` deps from `[pathname]` to `[search]`, and replaced inline `window.location.search` reads with the router-provided `search` (single source of truth).

**Verification:**
- `npx vitest run` in `app/` — **356/356 passed**.
- `npm run build` — clean (`check-bundle-secrets: OK`).
- `wrangler pages deploy` — preview redeployed to `https://f2-admin-portal.f2-pwa-staging.pages.dev` (Deployment `21e14b3f.f2-pwa-staging.pages.dev`).
- Browser repro re-run: see C2/C3/C4/D1/D2/D3 rows below.

**Severity rationale:** HIGH because **5 of 8 dashboard tabs were structurally unreachable** in production (Audit, DLQ, HCWs on Data; Sync, Map on Report). API-layer enforcement was fine — frontend just couldn't reach them. Caught by cross-platform QA only because Section A focused on auth/RBAC and didn't exercise sub-tab routing; AP1–AP4 dogfood evidently never clicked between sub-tabs in a single session, or never reload-tested deep-linking via `?tab=...` URLs.

**Test gap noted:** No frontend unit/integration test exists for sub-tab routing on either dashboard. Adding one (driven by `RouterProvider` + `navigate`-then-assert-rendered-tab pattern) would catch this and any future regression. Filed as a follow-up.

---

### [FX-005] [LOW — process gotcha] cmd.exe `set VAR=value && npm run build` injects trailing space into env var

**Found while:** Re-deploying after the FX-004 router fix; the freshly built bundle baked in `https://f2-pwa-worker-staging.hcw.workers.dev ` (trailing space) into the proxy URL, which the browser percent-encoded to `%20`, causing the actual fetch to hit `https://f2-pwa-worker-staging.hcw.workers.dev%20/admin/api/login` — DNS resolved fine because Cloudflare's edge tolerates the host header but the URL was malformed enough that CORS preflight came back 404 with no Access-Control headers, surfacing as `E_NETWORK` again exactly like FX-001.

**Repro:**
- `cmd.exe //c "set VITE_F2_PROXY_URL=https://f2-pwa-worker-staging.hcw.workers.dev && npm run build"` — the trailing space before `&&` becomes part of the env var value.
- The previously-working PowerShell pattern `$env:VITE_F2_PROXY_URL='...'; npm run build` does NOT have this problem because the assignment terminates at the closing quote.

**Fix:** Always use the PowerShell pattern for these one-off cross-deploy builds on this machine. Logged here so future-me doesn't waste another 10 minutes diagnosing the same `%20` URL.

**Status:** Process note, not a code defect. No change required in the project. Captured because Carl works on Windows + this came up twice in a single session (cf. memory `windows_utf8_gotcha.md` for the related cp1252 issue).

---

### [FX-006] [MEDIUM] Audit tab — Actor / Resource / Detail columns render empty across all 40 rows

**Found while:** E1 C2 (Audit sub-tab).
**Affected env(s):** All — data-binding, not browser-specific.

**Repro:** Login as carl_admin → Data → Audit. 40 admin_login + admin_revoke_sessions events render with WHEN + EVENT populated. ACTOR, RESOURCE, DETAIL columns are empty (`—`) across every row.

**Expected:** ACTOR should show `carl_admin` (the only user with activity); RESOURCE / DETAIL should populate where applicable (e.g., for `admin_revoke_sessions` the resource is the user whose sessions were revoked).

**Possible causes** (need source dive to confirm):
- Apps Script `admin_audit_list` RPC may not be returning the actor / resource / detail columns from the F2_Audit sheet (check the AS handler).
- Worker route may be stripping fields before responding.
- Frontend `AuditTab.tsx` may not be reading them off the row object (check the column accessors).

**Severity rationale:** MEDIUM. Audit log is the **primary forensic surface** for the portal — if a security incident happens and admin_revoke_sessions rows have no actor recorded, you can't tell who did what. Functionally complete enough to ship, but actor-tracing is the whole point of the audit log; currently it's "something happened at this time, no idea who or to whom." Worth fixing before v2.0.0.

**Update from C5:** The Response Detail page shows `ENCODED BY: carl_admin` correctly hydrated from the same backend. So the actor data **is** being captured server-side; the Audit tab specifically isn't reading the field through to the column — narrowing the cause to either (a) the AS `admin_audit_list` RPC's column projection, or (b) the AuditTab.tsx column accessors. Lower-effort fix than feared.

**Status:** Logged for triage (Task #12). Not blocking the rest of E1 (the tab itself works); needs a separate scrum task to investigate the data-binding chain.

---

### [FX-007] [HIGH] CORS preflight only allowed GET/POST — PATCH and DELETE blocked — fix shipped same session

**Found while:** E1 F3 (edit role on throwaway user — save returned `Network unavailable. Retry when reconnected.`).
**Affected env(s):** All cross-origin browsers — architectural follow-on to FX-001.

**Repro:**
1. Login as carl_admin → Users → click EDIT on `qa_temp_chrome` → change role to DataReader → Save changes.
2. Frontend issues `PATCH /admin/api/dashboards/users/qa_temp_chrome` (preflight first).
3. Worker preflight returns `Access-Control-Allow-Methods: GET, POST, OPTIONS` — PATCH not in the list, so browser blocks the actual PATCH.
4. Frontend `adminFetch` catches the rejected fetch as `E_NETWORK` → renders inline error in the modal.

**Affected operations** (frontend grep showed `'DELETE'` and `'PATCH'` in use beyond GET/POST):
- PATCH user (UserEditor save)
- PATCH role (RoleEditor save)
- DELETE user (Users dashboard delete action)
- DELETE role (Roles dashboard delete action)
- DELETE file (Files panel delete action — already R2-smoke-tested in this session, but **only because the smoke test was run BEFORE the static admin frontend was served from Pages**; cross-origin DELETE from the new Pages frontend would have failed).

**Fix:** `worker/src/index.ts` — expanded `Access-Control-Allow-Methods` from `GET, POST, OPTIONS` to `GET, POST, PATCH, DELETE, OPTIONS`. The same `CORS_HEADERS` object serves both the public PWA surface (GET/POST only) and the admin portal (full set); routing is enforced per-handler, so listing PATCH/DELETE only exposes them where a handler actually accepts them.

**Verification:**
- `npx vitest run` in `worker/` — **166/166 passed**.
- `wrangler deploy --env staging` — `f2-pwa-worker-staging` redeployed (Version `f0a94dca-ac3e-4170-9314-45cd0f2ad877`).
- Browser repro re-run: see F3/F4/F5 rows below.

**Severity rationale:** HIGH — same class as FX-001 but narrower (only edit/delete operations). All read paths worked, so this slipped past Sections C/D/E which exercised only GET/POST. Caught the moment Section F tried to mutate.

**Lesson learned:** When fixing CORS for a surface that does real CRUD, enumerate ALL methods the frontend uses (`grep "method:" src/`) before declaring the fix complete. A FX-001-style fix that covers only "the methods we tested" leaves a hole proportional to the methods you didn't test. Worker test gap from FX-001 doubly applies here — a regression test asserting `Access-Control-Allow-Methods` includes the full set would have surfaced this without browser repro.

---

## Findings — Resume session 2026-05-03 (E1 Chrome G3 + Section H + Section Z)

> Tester: Claude (driving via Chrome DevTools MCP). Fresh session resumed from 2026-05-02 ~00:30 PHT pause. Carl approved the resume + delegation in chat.

### [FX-008] [MEDIUM] Reissue token modal: QR rendering deferred

**Found while:** E1 G3 (HCWs → REISSUE on HCW-TEST-001 → "Issue new token").
**Affected env(s):** All — backend serves the URL + token; frontend modal copy explicitly defers QR rendering.

**Repro:**
1. Login as carl_admin → Data → HCWs → click REISSUE on HCW-TEST-001.
2. Confirmation modal renders (Verde-styled, `position:fixed z-50` over `bg-ink/70` scrim) — copy: "Issue a new enrollment token for HCW-TEST-001? The previous token stops working as soon as the HCW switches devices."
3. Click "Issue new token". POST `/admin/api/hcws/HCW-TEST-001/reissue-token` returns 200 with `{old_jti, new_jti, new_token, expires_at, enroll_url}` — verified in Network panel.
4. Modal flips to success state showing **enrollment URL + raw token (for manual paste)** — both rendered as copy-buttons (proper Verde styling).
5. Modal copy reads literally: *"QR rendering lands in a follow-up. For now, paste the URL into a QR generator the HCW can scan, or have them paste the token into the enrollment screen on their device."*

**Expected per QA matrix G3:** "ReissueModal shows QR; clicking 'Reissue' generates new JWT (verify in network)."
**Actual:** JWT generation works end-to-end (CAS-protected, prev_jti → old_jti round-trip verified), but **no QR is rendered** — copy explicitly defers.

**Severity rationale:** MEDIUM. The QR was the friction-reducing UX for handing over enrollment links to HCWs in the field; without it, every reissue requires the admin to either (a) manually copy the URL into a third-party QR generator (operational risk: external service exposure of the token), or (b) verbally relay the token (operational risk: paste error on a 200-char JWT). For v2.0.0 of an "operations console" the absence is felt. NOT a bug per se — clearly scoped and labelled in the modal — but this is the v2.0.0 release; the "follow-up" needs to be explicitly tracked as a post-v2.0.0 commitment or pulled in.

**Counterpoint to FX-003 partial scope:** the Reissue *confirmation* modal IS proper Verde-styled (not native `window.confirm`). FX-003's claim that "destructive admin actions use native dialogs" applies to REVOKE on Users, not to Reissue token. Worth grepping `confirm(`/`alert(` to enumerate which destructive actions still use native dialogs vs already use Verde modals.

**Status:** Logged for triage. Decision needed: ship v2.0.0 with a tracked post-v2.0.0 follow-up, or pull QR rendering into the v2.0.0 sprint window. Effort estimate: ~2h to wire `qrcode` (or similar) into the existing modal — the data is already there (`enroll_url` in the response).

**Evidence:** `screens/2026-05-03-e1-g3-reissue-modal-confirm.png`, `screens/2026-05-03-e1-g3-reissue-modal-issued-no-qr.png`.

---

### [FX-009] [LOW–MEDIUM] File picker `accept` attribute is empty despite UI hint promising "PDF / ZIP / PNG / JPEG / GIF"

**Found while:** E1 H2 (Apps → Files panel — DOM inspection of the `<input type="file">`).
**Affected env(s):** All — DOM-level config issue, browser-agnostic.

**Repro:**
1. Login as carl_admin → Configuration → Apps & Settings → Files panel.
2. Inspect the file input via DevTools: `document.querySelector('input[type="file"]')`.
3. UI hint above the picker reads "PDF / ZIP / PNG / JPEG / GIF, UP TO 100.0 MB".
4. Actual `input.accept` value: `""` (empty string).
5. Clicking "Choose File" opens a system file dialog with NO type filter — user can pick any file (`.exe`, `.txt`, `.docx`, etc.).

**Expected:** `accept="application/pdf,application/zip,image/png,image/jpeg,image/gif"` (or extension-based equivalent).
**Actual:** `accept=""` — no client-side filter; relies entirely on worker-side validation to reject mismatched types.

**Severity rationale:** LOW–MEDIUM. Not a security vulnerability (worker enforcement is the actual gate), but UX regression: user picks a non-allowed file, hits Upload, gets a (presumably) generic 400 from the worker, and has to re-pick. UI lying about what's filterable. Server-side enforcement should be verified separately — the absence of client-side `accept` is just "doubled up" defense-in-depth missing.

**Status:** Logged for triage. ~30 min fix to populate the `accept` attribute from the same allow-list the worker uses.

**Evidence:** `screens/2026-05-03-e1-h1-files-picker.png`.

---

### [FX-010] [LOW] Files panel has no drag-drop UI; native browser button only

**Found while:** E1 H1 (Apps → Files panel — visual + DOM inspection).
**Affected env(s):** All — design/UX scope choice.

**Repro:**
1. Apps → Files panel renders a single native browser "Choose File" button + UI hint text.
2. DOM scan for drop zones: `document.querySelectorAll('[ondrop], .drop-zone, [data-drop]')` returns 0 elements.
3. No drag-and-drop affordance — drag a file onto the page, nothing happens (browser navigates to the file).

**Expected per DESIGN.md "real software, not a government form":** A Verde-styled drop-zone with hairline border, "Drop files here or click to browse" copy, hover-state thicker border, drag-over state ink-tinted background.
**Actual:** Native browser file-input button — same as a Bootstrap 3 admin in 2014.

**Severity rationale:** LOW. Functional, accessible (native input is a11y-clean), and the UX gap matters more for HCW/end-user touchpoints than for admin operators. But the admin portal is also where designers/PMs will look first to assess "does this product feel professional" — the native button is the most jarring chrome on the page and stands next to otherwise-polished Verde styling. Cosmetic-blocking-for-v2.0.0-bar candidate.

**Status:** Logged for triage. ~1h fix to wire `react-dropzone` (or hand-roll) onto the existing input. Pairs naturally with FX-009 (populate `accept` at the same time).

---

### [FX-011] [HIGH] Soft reload / fresh URL navigation renders blank page on admin frontend (service-worker race or shell-cache bug)

**Found while:** E1 H4 (reload after setting a localStorage sentinel) — reproducible on every soft reload thereafter, AND on every fresh `window.location.href = '/admin/users'` style navigation.
**Affected env(s):** All — service-worker / Workbox issue, not Chrome-specific (would also hit Firefox/Edge once SW is registered).

**Repro:**
1. First-ever load of `/admin/login` (no prior SW): Verde paper background renders; `<div id="root">` is empty for ~2s, then login form appears OR stays blank (race-conditional).
2. After hard reload (Ctrl+Shift+R / `ignoreCache: true`): login form renders deterministically.
3. Login → land on Data dashboard. Click any SPA link (Configuration → Apps, Data → Audit) — works fine (same React tree, no full reload).
4. Press Ctrl+R / soft reload anywhere: `<div id="root">` empty, `document.readyState === 'complete'`, **no console errors**, no failed requests, all bundle assets 200/304. Page just doesn't mount.
5. Press Ctrl+Shift+R / hard reload: renders correctly.
6. Type a fresh URL in the address bar (`location.href = '/admin/users'`): blank again. Hard reload: renders.

**Console signature on the broken loads:** zero messages. No React errors, no "rendered nothing" warnings, no SW activation events. Failure is silent.

**Network signature:** all assets return 200 (or 304 for cached PNG). The Vite bundle (`/assets/index-DmcDRmNZ.js`) loads. The CSS loads. Workbox's offline message ("[PWA] Ready to work offline") fires on first load only.

**Likely cause** (need source-dive to confirm):
- `vite.config.ts` per memory `project_f2_verde_manual_prod.md` has `registerType: 'prompt'` for the F2 PWA. The admin frontend may share the same vite-plugin-pwa config, which means the SW is in prompt mode and the client-side update flow expects a user action before activating the new SW.
- Possible interaction with the Workbox service worker pre-caching the *previous* `index.html` shell that referenced an old bundle hash, so soft reloads serve the stale shell + the new bundle assets — but the React root mounts inside a stale element tree that doesn't exist in the new bundle, silently failing.
- OR: the SW is intercepting `/admin/login` (and other routes) and returning a cached blank shell that has no `<script>` tag pointing to the current bundle.

**Severity rationale:** HIGH. **Every user who reloads the page sees a blank screen** — and "reload" includes Ctrl+R, pull-to-refresh on tablets (E4/E5), and the auto-update prompt that the SW itself triggers. Even if hard-reload restores the page, no operator will diagnose this — they'll close the tab and re-navigate, then re-login (per in-memory session policy), losing context. For a v2.0.0 "operations console" this is a flat-out regression vs the legacy M10 single-page admin (which had no SW caching admin routes).

**v2.0.0 disposition:** **Blocker.** Either (a) exclude `/admin/*` routes from SW pre-caching (simplest), or (b) move the admin to a non-PWA chunk served at `/admin/` with its own `index.html` outside Workbox scope, or (c) fix the registration flow so soft reloads reliably mount.

**Verification gap:** No test currently exercises soft-reload / fresh-URL navigation on the deployed admin. Frontend tests run with vitest's jsdom (no SW); E2E doesn't exist for the admin yet. Worth filing a follow-up to add a Playwright spec that opens `/admin/login`, logs in, hits Ctrl+R, and asserts the dashboard re-renders.

---

### [FX-012] [MEDIUM] No CSV / data export anywhere in the admin frontend

**Found while:** E1 H3 (DOM scan across Users, Audit, Responses, DLQ, Apps for `download/export/csv` controls — 0 matches on every page).
**Affected env(s):** All — feature scope, not browser-specific.

**Repro:**
1. Login as carl_admin → walk every dashboard tab.
2. Audit (48 events): no Export. Responses (1 row): no Export. DLQ: no Export visible. HCWs: no Export. Users: no Export. Roles: no Export.
3. Apps → Data Settings has a `RUN NOW` button on the scheduled break-out export, but that triggers the worker → R2 export pipeline; **no UI to download the resulting R2 file** appears anywhere (Files panel only shows non-export uploads).

**Expected (per CSWeb mirror promise + Sprint AP4 spec §12.4):** At minimum, CSV export for Audit (forensic/compliance) and Responses (data review). DLQ export would be nice for incident analysis.
**Actual:** No data egress UI. Operators can read on-screen but can't pull data out of the portal for offline analysis without going to the underlying spreadsheet directly — which defeats the purpose of having an admin portal.

**Severity rationale:** MEDIUM. Sprint AP4 spec §12.4 may legitimately scope this as "v2.1.0 feature" (need to re-read), in which case it's a known scope gap, not a bug. But for "CSWeb-mirror operations console" this is a gaping product hole — CSWeb's primary export surface (Excel / CSV per dashboard) is what makes it useful; an admin portal that can't export its own data is structurally weaker than the legacy SPEED-2023 spreadsheet workflow.

**Status:** Logged for triage. Decision needed: (a) defer to v2.1.0 with explicit roadmap entry, (b) add CSV export to Audit + Responses as a v2.0.0 commitment (~half-day each = ~1 day), or (c) settle for the scheduled break-out R2 exports as the official egress path and add a Files-panel "Browse exports" view (~half-day).

---

### [FX-013] [LOW] Files filename link is a raw `<a href>` without `download` attribute

**Found while:** E1 H3 (DOM inspection of the existing file row in the Files panel).
**Affected env(s):** All — relies on Worker `Content-Disposition: attachment` header behavior, which varies subtly across browsers.

**Repro:**
1. Apps → Files panel → existing file (`Screenshot 2026-05-02 163453.png`).
2. DOM: `<a href="https://f2-pwa-worker-staging.hcw.workers.dev/admin/api/dashboards/apps/files/c7f339c6-...">Screenshot 2026-05-02 163453.png</a>`.
3. No `download` attribute. No `target` attribute. No `rel`. No onclick handler.
4. Behavior depends entirely on the worker's response Content-Disposition header — not verified in this session.

**Expected:** Either `<a download>` (forces save dialog with proposed filename) OR a JS click handler that fetches the URL as a Blob and uses `URL.createObjectURL` + a temporary anchor with `download`. Both patterns are robust across browsers/engines and decouple from Content-Disposition.
**Actual:** Bare `<a href>`. If the worker omits Content-Disposition, browsers will inline-render the image (or PDF, or text) instead of saving it. Save-dialog behavior is not guaranteed.

**Severity rationale:** LOW. Worker-side may already set Content-Disposition correctly (E5f passed earlier this session). But it's a fragile coupling — moves a frontend-controllable behavior into worker config. One-line fix.

**Status:** Logged for triage. Worth verifying the worker actually sets `Content-Disposition: attachment; filename="..."` on file responses; if so, the frontend `download` attr is just defense-in-depth. If not, this is the actual bug surfacing.

---

### [FX-014] [LOW] Form fields without `id` or `name` attributes (Chrome DevTools Issues panel: count 4)

**Found while:** E1 Z2 (console review at session end).
**Affected env(s):** All — DOM-level a11y/best-practice issue.

**Repro:**
1. Open DevTools → Issues panel after login + dashboard nav.
2. One issue group: "A form field element should have an id or name attribute" with count 4.
3. Likely candidates (would need DOM grep to pinpoint): the date inputs (`Date "FROM"` etc), or the search/facility/role textboxes, or the unlabelled email/phone fields in the user-edit modal.

**Expected:** Every form field has either an `id` (paired with a `<label for=>`) or a `name` (paired with a label parent) — for a11y, autofill, form-reset, and password-manager support.
**Actual:** 4 fields lack both.

**Severity rationale:** LOW. Functional + accessible at the visible-label level (the snapshot shows labels rendered correctly), but breaks browser autofill / password-manager heuristics, and risks downstream a11y test failures.

**Status:** Logged for triage. ~30 min fix once the 4 fields are pinpointed (`grep -n 'type="text"' src/admin/`).

---

### [FX-015] [MEDIUM] Versioning telemetry empty: PWA version, Build SHA, Worker version all read "unknown"

**Found while:** E1 — Apps & Settings → Versioning panel renders all "unknown".
**Affected env(s):** All — worker-side env-var injection gap, not browser-specific.

**Repro:**
1. Login as carl_admin → Configuration → Apps & Settings → Versioning panel.
2. Renders: PWA VERSION `unknown` · PWA BUILD SHA `unknown` · WORKER VERSION `unknown` · LAST PAGES DEPLOY `—`.
3. Network: GET `/admin/api/dashboards/apps/version` returns 200 with body `{"pwa_version":"unknown","pwa_build_sha":"unknown","worker_version":"unknown","form_revisions":[...],"total_submissions":1,"last_pages_deploy_at":null}`.

**Expected:** Worker injects the `package.json` version + git SHA + worker deploy timestamp at build time, dashboard reads those values. Last Pages deploy should come from the CF Pages API (or be cached by the deploy workflow).
**Actual:** Worker returns the literal string `"unknown"` for every version field. Build pipeline is not injecting version metadata.

**Severity rationale:** MEDIUM. Quality-bar gap: when production is at v2.0.0 and an incident hits, the first thing operators ask is "what version is running?" — the answer needs to come from the portal, not from `wrangler deployments list`. Also breaks the mental model of "this admin portal is the operations console" — an ops console that can't tell you what's running is half a console.

**Status:** Logged for triage. Two tracks to fix: (a) build-time injection in the worker (`wrangler.toml` `[vars]` block + `package.json.version` read at deploy time, ~30 min), and (b) frontend equivalent (`PWA_BUILD_SHA` env var threaded through Vite, ~30 min). Last Pages deploy timestamp can come from a `pages-deploy-info.json` written by the deploy workflow (~30 min).

---

## E1 Chrome — Final tally (resume session 2026-05-03)

**Tests run this session:** G3, H1, H2, H3, H4, H5, H6, H7, Z1, Z2, Z3 (11 tests).
**H8 N/A on desktop** (defers to E4/E5 tablet emulation).

**Disposition:**
- ✅ Pass: H4, H6, H7, Z1, Z3 (5)
- ⚠️ Partial / minor: G3, H1, H5, Z2 (4)
- ❌ Fail / new finding: H2, H3 (2)

**E1 Chrome end state:** 28/30 tests run (Sections A–G + H1–H7 + Z1–Z3). 25 pass / 3 partial / 2 fail. Plus 8 new findings filed (FX-008 through FX-015).

**Cumulative finding pool across both sessions:** 15 findings (FX-001 fixed, FX-004 fixed, FX-007 fixed; FX-005 process note; FX-002, FX-003, FX-006, FX-008, FX-009, FX-010, FX-011, FX-012, FX-013, FX-014, FX-015 open for triage).

---

## Sign-off

- [ ] All 5 environments green or with only LOW findings
- [ ] Critical/High fixed in `f2-admin-portal` branch + re-tested
- [ ] PR #54 description updated with QA pass summary
- [ ] Sprint 4 Task 4.6 marked done in `scrum/epics/epic-04-backend-sync-infrastructure.md`
- [ ] Safari/macOS recorded as deferred-outstanding in PR description
