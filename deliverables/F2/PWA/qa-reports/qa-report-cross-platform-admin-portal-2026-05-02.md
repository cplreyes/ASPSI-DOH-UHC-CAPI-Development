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
| A1 | Login as `carl_admin` (Administrator) → lands on default dashboard | | | | | |
| A2 | Logout → redirects to login screen, no stale session | | | | | |
| A3 | Bad password 3× → error message renders, no PII leak in console | | | | | |
| A4 | Login as `data_reader_test` (DataReader role) → admin-only routes (Users / Roles) hidden or 403 | | | | | |
| A5 | Force-revoke own session via Users panel → next request gets 401 + redirected to login | | | | | |

### B. Layout + visual identity (Verde Manual) (4 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| B1 | Header / sidebar / content frame render with Verde paper (`#F2F5EE`) + DOH emerald | | | | | |
| B2 | Newsreader serif on h1/h2; Public Sans on body; JetBrains Mono on code/eyebrows | | | | | |
| B3 | No raw Tailwind colors leaking (e.g., `bg-blue-500`) — all alias tokens (paper/ink/hairline/signal/error) | | | | | |
| B4 | Modal scrim + hairline borders match Verde (`/scrim`, `/hairline`) | | | | | |

### C. Data dashboard (5 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| C1 | Responses tab loads, table renders ≥1 row (HCW-TEST-001 fixture) | | | | | |
| C2 | Audit tab loads with filter + pagination | | | | | |
| C3 | DLQ tab loads (likely empty on staging — that's fine) | | | | | |
| C4 | HCWs tab loads + search input filters | | | | | |
| C5 | Click a Response row → ResponseDetail drawer opens | | | | | |

### D. Report dashboard (3 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| D1 | SyncReport renders aggregations (region/province) — empty-state OK if no data | | | | | |
| D2 | MapReport renders Leaflet base layer | | | | | |
| D3 | MapReport with markers renders + clusters (use sandbox markers if no real data) | | | | | |

### E. Apps dashboard (5 checks)

| # | Test | E1 Chrome | E2 Firefox | E3 Edge | E4 Tab-P | E5 Tab-L |
|---|---|---|---|---|---|---|
| E1f | Files: upload a small file (PDF or image, <5 MB) → appears in list | | | | | |
| E2f | Files: download via row action → bytes match | | | | | |
| E3f | Files: delete → row disappears, R2 object_count returns to baseline | | | | | |
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

(empty so far)

---

## Sign-off

- [ ] All 5 environments green or with only LOW findings
- [ ] Critical/High fixed in `f2-admin-portal` branch + re-tested
- [ ] PR #54 description updated with QA pass summary
- [ ] Sprint 4 Task 4.6 marked done in `scrum/epics/epic-04-backend-sync-infrastructure.md`
- [ ] Safari/macOS recorded as deferred-outstanding in PR description
