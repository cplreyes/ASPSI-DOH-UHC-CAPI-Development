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
| E4f | DataSettings: list renders, scheduled break-out config visible | | | | | |
| E5f | QuotaWidget: AS quota counter visible + sane (`as_quota:<UTC-date>`) | | | | | |

### F. Users + Roles (5 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| F1 | Users list renders with `carl_admin` + `data_reader_test` | | | | | |
| F2 | Create a throwaway user (`qa_temp_<env>`) → succeeds, appears in list | | | | | |
| F3 | Edit role on the throwaway user → role_version bumps; existing JWT for that user invalidated | | | | | |
| F4 | Delete the throwaway user → cleanup | | | | | |
| F5 | Roles list renders with built-ins (Administrator, Standard User) + custom (DataReader) | | | | | |

### G. Encode + Reissue (3 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| G1 | EncodeQueue loads, ≥1 row visible | | | | | |
| G2 | Open EncodePage for an HCW → autosave fires (watch network panel) | | | | | |
| G3 | ReissueModal shows QR; clicking "Reissue" generates new JWT (verify in network) | | | | | |

### H. Browser-specific watch list (varies)

Things that historically diverge between engines. Note any divergence even if functional.

| # | Watch | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| H1 | File picker UI / drag-drop styling | | | | | |
| H2 | `<input type="file">` accept attribute behavior | | | | | |
| H3 | CSV download triggers a real Save dialog (Blob + `download` attr) | | | | | |
| H4 | IndexedDB + localStorage persist across reload | | | | | |
| H5 | Focus rings visible on Tab nav (FF often differs from Chrome) | | | | | |
| H6 | Sticky table headers don't overlap modals | | | | | |
| H7 | Date / number inputs render natively (FF sometimes hides spinners) | | | | | |
| H8 | Touch-target size ≥44px on tablet emul (B/G/H tabs) | — | — | — | | |

### Z. Performance + console hygiene (3 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| Z1 | First contentful paint < 2s on a warm cache | | | | | |
| Z2 | Console clean (no errors / no warnings beyond expected service-worker / vite-dev noise) | | | | | |
| Z3 | Network panel: no 5xx; no aborted requests on golden-path nav | | | | | |

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

## Sign-off

- [ ] All 5 environments green or with only LOW findings
- [ ] Critical/High fixed in `f2-admin-portal` branch + re-tested
- [ ] PR #54 description updated with QA pass summary
- [ ] Sprint 4 Task 4.6 marked done in `scrum/epics/epic-04-backend-sync-infrastructure.md`
- [ ] Safari/macOS recorded as deferred-outstanding in PR description
