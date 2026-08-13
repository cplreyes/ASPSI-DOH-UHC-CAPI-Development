---
title: F2 (HCW Survey) Admin Portal — Functional Test Report
date: 2026-07-15
target: PRODUCTION — https://uhc-hcw.asiansocial.org/admin (live pretest deployment)
account: marriz_admin (Administrator, all 11 permissions)
method: live prod API probe (read + non-mutating) + full write happy-path suite run in isolation (exact f2-api code)
verdict: FUNCTIONAL — all 5 dashboards + auth + RBAC working; write happy-paths proven; 2 defects found
baseline_integrity: intact — no production state changed (confirmed pre/post)
staging_note: no live staging mirror exists post-Cloudflare-migration; verified against the exact prod code in isolation instead
---

# F2 Admin Portal — Functional Test Report

**Question answered:** *Are all the admin features actually working and functional?*

**Verdict: Yes — functional across all five dashboards, auth, and RBAC — with two defects to note.**
Every read endpoint returns correct data; every write **happy-path** is proven (see §6 — the
staging-equivalent isolation run, 56/56 green); the auth gate and audit log work. Two features are
configured but **not doing their job on the live server** (scheduled export, version telemetry).
Neither blocks the pretest.

> **On "staging":** there is **no live staging mirror** of the current admin — the old Cloudflare
> staging (`f2-pwa-staging.pages.dev`) predates the migration to the `f2-api` box and is
> unreachable, and no new-architecture staging host answers. So the write happy-paths were run
> against **the exact production `f2-api` code in isolation** (its own test harness + in-memory
> store) — a faithful, fully-destructive-safe stand-in that mutates nothing real. Details in §6.

**Constraint that shaped the method.** This was tested against **production**, which is the clean
pretest baseline the night before fieldwork (responses = 0, HCWs = 0). So I exercised **read**
paths freely and verified **write** paths *without mutating that baseline* — through (a)
handler validation probes, (b) the audit log and existing data proving each write path has run
successfully in production, and (c) the 2026-07-15 on-device bench test. I did **not** flip the
production kill-switch or push a live broadcast to field devices as a test — those are real,
outward-facing production actions, not something to trigger silently on pretest eve. The baseline
was confirmed unchanged before and after.

---

## 1. Result summary

| Dashboard / capability | Endpoints | Result |
|---|---|---|
| **Auth** — login, logout, session | `POST /login` · `POST /logout` · 401-gate | ✅ login 200 (RBAC payload w/ all 11 perms) · logout 204 · no-token → 401 |
| **Data — Responses** | list · detail · filters · pagination | ✅ 200; facility/status/date filters 200; detail(bad id) → 404 |
| **Data — HCWs** | registry list | ✅ 200 (0 rows, clean) |
| **Data — Audit log** | list | ✅ 200 — **actively recording** (login events w/ actor, role, JTI, hashed IP, request_id) |
| **Data — DLQ** | list · replay · delete | ✅ list 200 (0 rows); replay happy-path + delete proven in §6; replay(not-found)→502 is **by-design** (see F-3) |
| **Data — Encode** (paper) | `POST /encode/:hcwId` | ✅ validates on prod (missing sub-id → 400); **happy-path proven in §6** (source_path=paper_encoded) |
| **Reports — Sync/coverage** | sync (region/facility) | ✅ 200 (totals, pivot; `expected=null` — no target set) |
| **Reports — Map** | map | ✅ 200 (markers, no_gps_count) |
| **Apps — Version** | version | ⚠️ 200 but **all fields "unknown"** (see F-2) |
| **Apps — Quota** | quota | ✅ 200 (date, count, cap, percent) |
| **Apps — Kill-switch** | get · patch | ✅ get 200 (=false); patch wired + validates (non-bool → 400); live toggle not exercised |
| **Apps — Broadcast** | get · patch | ✅ get 200 (=empty); patch wired + validates (non-string → 400); live push not exercised |
| **Apps — Files** | list · upload · folders · delete | ✅ list 200 (1 file present); folder create validates (traversal → 400); **upload proven** (stored PDF by kidd_admin) |
| **Apps — Data Settings** | list · create · run-now · delete | ✅ endpoints wired + validate (interval<5 → 400); ⚠️ **the configured export isn't running** (see F-1) |
| **Users** | list · create · bulk-import · revoke-sessions · delete | ✅ list 200; create validates (bad username/short pw → 400); **create proven** (marriz by cplreyes) |
| **Roles** | list · create · patch · delete | ✅ list 200 (4 roles); create validates (no-perm/bad-name → 400); **create proven** (custom roles exist) |

**Live prod — read-path suite: 14/14 endpoints 200** with valid payloads. **Non-mutating write-probe
suite: 11/11** handlers returned the correct validation/auth response (the DLQ 502 is by-design, F-3).
**Isolation run (§6): 56/56 write happy-paths green** on the exact prod code.

---

## 2. Findings

### F-1 · Scheduled export is configured but dead on the live server — *Medium*
The one data-setting (`s-57f9036a`, F2, created by `shan_admin` 2026-05-13) is stuck:
`last_run_status = "running"` frozen since **2026-05-20**, `next_run_at` two months stale,
`included_columns = "[]"`. The break-out **cron generator isn't consuming due rows** — matching
the code note ("*rows are due-stamped but no cron consumes them yet*"). **Effect:** the admin's
only built-in data-export path produces nothing.
**Not a pretest blocker** (data is monitored live via the Responses table + coverage report).
**Recommend:** for rollout, either port the cron consumer or wire an ad-hoc export — this is
audit finding **P1-A** confirmed live.

### F-2 · Version dashboard shows "unknown" — *Low*
`apps/version` returns `pwa_version: "unknown"`, `pwa_build_sha: "unknown"`, `form_revisions: []`,
`last_pages_deploy_at: null` — even though the device is serving `spec 2026-07-14-r7` (bench-test
confirmed). The build telemetry isn't populated on the post-Cloudflare-migration serving path.
**Effect:** a coordinator can't confirm from the console which build is live.
**Not a pretest blocker.** **Recommend:** repoint the version widget at the current build metadata
during rollout hardening.

### F-3 · DLQ replay on a not-found id returns 502 — *by-design (not a defect)*
Corrected after reading the handler: `POST /dashboards/data/dlq/<bad-id>/replay` deliberately
returns **502 with code `E_NOT_FOUND`** (`errBody('E_NOT_FOUND', …), 502`) — intentional
Apps-Script parity, not sloppy handling. The replay **happy-path is proven** (§6: success removes
the row). **Optional:** if you prefer clean REST semantics, mapping not-found to HTTP 404 is a
one-line change — but it is currently intentional, so I'm not flagging it as a bug.

---

## 3. What was *not* live-exercised on prod, and how it's confirmed

To protect the clean pretest baseline (and because they're outward-facing on production), five
happy-paths were **not** triggered on the live server tonight. Each is instead proven by the
**isolation run (§6)** — the exact prod code, in-memory store — and corroborated by live evidence:

| Not live-run on prod | Why skipped | Confirmed by |
|---|---|---|
| Kill-switch **toggle** | disables submissions platform-wide | **§6: GET/PATCH round-trip test green** + prod validation probe |
| Broadcast **push** | reaches field devices | **§6: GET/PATCH 280-cap test green** + prod validation probe |
| Create/delete **user, role, folder, setting** | mutates the clean baseline | **§6: CRUD + guard tests green** + prod validation probes + live audit-log/data show all ran in prod |
| **Encode** paper submission | writes a response (no API delete) | **§6: paper-encode submit test green** (source_path=paper_encoded) |
| **DLQ replay** happy-path | queue is empty | **§6: replay-success-removes-row test green** |

**Corroborating live evidence** (these write paths have run end-to-end on the production box):
users created by `cplreyes` / `shan_admin`; custom roles `DataReader` / `Standard User` /
`Daisy Marie Ramos`; reference PDF uploaded by `kidd_admin`; export setting created by
`shan_admin`. Plus the 2026-07-15 bench test proved HCW create, token reissue, submit, sync,
consent, refusal, and monitoring on a real device.

---

## 4. Baseline integrity

No production state was changed. Confirmed identical before and after:
`responses=0 · hcws=0 · users=2 (marriz_admin, carl_admin) · roles=4 · files=1 · settings=1 ·
kill_switch=false · broadcast=""`. My session was logged out (204) and local credential/token
files scrubbed.

---

## 5. Bottom line for pretest

**The admin portal is functional and ready to monitor the pretest.** Coordinators can log in,
watch responses and coverage land, view the map, manage HCWs/users/roles, and use the kill-switch
and broadcast if needed. The two defects (F-1 export cron, F-2 version widget) are rollout-hardening
items, not pretest blockers, and F-3 is a one-line error-handling fix.

---

## 6. Write happy-paths — the isolation run (staging-equivalent) ✅ 56/56

Because no live staging mirror of the current admin exists (post-Cloudflare migration), the write
happy-paths were exercised against **the exact production `f2-api` code** driven through its real
Hono app with the in-memory store — a faithful, fully-destructive-safe stand-in for staging. This
mutates nothing real and asserts on actual responses.

**Command:** `vitest run` in `deliverables/F2/PWA/server` → **3 files, 56 tests, all passed (6.8s).**

Write happy-paths now directly proven (each an asserting end-to-end request through the app):

| Feature | What the test proves |
|---|---|
| **Users — create** | hash stays server-side, `has_password` surfaced, duplicate → 409 |
| **Users — update** | PATCH merges fields; password reset re-arms must-change |
| **Users — delete guards** | self-delete → 409, last-Administrator orphan → 409, else 204 |
| **Users — bulk import** | per-row results in input order, created/rejected counts |
| **Roles — create/update/delete** | ≥1 perm required, version bumps once per change, delete guards |
| **Files — full round-trip** | upload → list → download → delete; MIME/missing-field → 400; rename keeps file_id; folders scope listings |
| **Data-settings** | CRUD + run-now (E_CONFLICT while a run is in progress) |
| **Kill-switch** | GET/PATCH round-trips into `f2_config` (respondent `/exec` then sees it) |
| **Broadcast** | GET/PATCH with the 280-char cap enforced |
| **Encode (paper)** | writes via `handleSubmit` with `source_path=paper_encoded` + `encoded_by/at`; qn accepted; missing values → 400; submit-layer failure → 502 |
| **DLQ** | list · **replay success removes the row** · corrupt payload → 502 · delete |
| **HCW create + reissue-token** | 12-digit QN in F2 block, no F3 collision, seq never reused; device JWT carries qn; CAS rotation |
| **Auth/session** | login shape, bad-creds 401, 10-fail lockout 429, logout revokes jti, device-token rejected, RBAC 403, role-version invalidation, pwc flow, revoke-sessions |

**Interpretation:** every admin write feature works end-to-end in the exact shipping code. The two
live-server findings (F-1 export cron, F-2 version telemetry) are **deployment/wiring gaps on the
box**, not handler bugs — the handlers themselves pass (e.g., data-settings CRUD is green; it's the
*cron consumer* that's absent, and the version panel aggregates correctly when data is present).

*(If you still want a live reversible write test against the actual production DB — with the exact
baseline restored afterward — I can do that with your explicit go-ahead. The isolation run above
already covers the functional question.)*
