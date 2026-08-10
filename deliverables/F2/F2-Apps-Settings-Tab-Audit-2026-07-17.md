# F2 Admin Portal — Apps & Settings Tab Audit

**Date:** 2026-07-17
**Status:** Fix sequence **FULLY CLOSED 2026-07-17** (approved + deployed same day). Exports + quota removed; Controls sub-tab first; versioning stamped by the deploy script (live: PWA 2.1.0 / d8cbf65+ / API 0.1.0); extension gate + copy/Help rewrite shipped; wedged `s-57f9036a` row deleted (f2_settings now 0 rows). Server 134/134, app 596/596, live-verified.
**Surface:** `https://uhc-hcw.asiansocial.org/admin/apps` (HCW Survey Console → Configure → Apps & Settings)
**Method:** Full code read of `app/src/admin/apps/*` + `server/src/admin/routes.ts` (apps section) + store/config/deploy wiring, then live read-only probes via the authenticated admin API (se_001). No changes made — analysis only.

---

## 1. What the tab is today

Four sub-tabs (`?tab=` deep-linkable, default `versioning`), all gated on the `dash_apps` permission, all mutations audit-logged:

| Sub-tab | What it claims | What it actually does |
|---|---|---|
| **Versioning** | "Live build identifiers… first place to look during incident triage" | Build IDs all render **unknown** on prod; only the spec-revision table is real |
| **Files** | Operator file uploads "stored in Cloudflare R2" | **Works** — stored on the box (`/opt/app/f2-files`, host bind mount, survives rebuilds) |
| **Data Settings** | Kill switch + broadcast + "Scheduled break-out exports… Worker cron fires every 5 minutes" | Kill switch + broadcast **work**; scheduled exports are a **UI shell with no executor** |
| **Apps Script Quota** | "Daily execution count vs the 20,000-call limit. Hard ceiling" | **Dead gauge** — permanently 0 / 20,000; no such limit exists on this stack |

Live state (probed 2026-07-17):

```
version:        pwa_version=unknown  pwa_build_sha=unknown  worker_version=unknown
                last_pages_deploy_at=null
                form_revisions: [ 2026-07-14-r7 → 4 responses, last 2026-07-16 13:19Z ]
quota:          0 / 20000 (0%)
kill-switch:    false          broadcast: ""
files:          1 file ("Paper-based HCW survey (English).docx.pdf", kidd_admin, 2026-05-18)
                q-search healthy (no collation 500 — this list has no JSON casts)
data-settings:  1 row (s-57f9036a, shan_admin, 2026-05-13, every 5 min)
                last_run_status = "running" — STUCK SINCE 2026-05-20 15:30Z
```

**What's already solid** (worth saying before the findings): RBAC is uniform (`dash_apps` on every route), every mutation writes an audit event (`admin_kill_switch_set`, `admin_files_*`, `admin_settings_*`…), the kill switch is genuinely enforced server-side on **every** public path (submit, claim, facility-start — each request reads `f2_config` live, so blocking is immediate), file downloads use the authenticated-blob pattern (#315), and Files has folders (#174), inline rename (#175), and drag-and-drop. The bones are good; the problem is that half the tab describes a Cloudflare/Apps-Script architecture that was retired at the P1–P4 VPS cutover.

---

## 2. Findings

No P0 — nothing crashes or loses data. The dominant theme is **P1 misleading operational surfaces**: panels that look authoritative during an incident and answer wrongly.

### P1-1 — Scheduled Exports is a non-functional shell, and it has already trapped a real operator

- The full CRUD + Run-now UI exists and writes `f2_settings` rows, but the executor was never ported off the Worker. `routes.ts` says so explicitly: *"the scheduled break-out CSV generator itself (Worker cron runDueSettings) is NOT ported in P1b — rows are due-stamped but no cron consumes them."* Nothing on the box reads `next_run_at`. No CSV has ever been produced.
- **Live evidence:** `shan_admin` created setting `s-57f9036a` on 2026-05-13 (every 5 min). Its `last_run_status` has read `"running"` since **2026-05-20 15:30Z** — two months. Because Run-now returns `409 already running` whenever status is `running`, the row is **permanently wedged**: the operator can neither re-trigger nor ever see it complete.
- Help Workflow 7 ("Run a scheduled break-out manually") walks the operator through the whole impossible procedure, ending with *"Download from the Files tab or via wrangler r2 object get"* — a CLI for a storage service this system no longer uses.
- The `included_columns` field exists in the record and API but has no UI and is always `[]` — dead weight either way.

**Call to make (Section 3):** port a real executor, or remove the section. My recommendation is remove — see below.

### P1-2 — Apps Script Quota tab is a dead gauge with a false safety claim

- The endpoint reads `as_quota:<date>` from `auth_kv`; **nothing writes that key anywhere in the codebase**. It will show 0 / 20,000 (0%) forever.
- The copy claims *"Hard ceiling — when this hits 100% the backend rejects writes until UTC rollover."* On the Node/MySQL stack there is no such rejection path. During an enumerator surge an operator watching this gauge would conclude capacity is fine because the gauge says 0% — the gauge measures a system that no longer exists.
- It also occupies one of four navigation slots on the tab.

### P1-3 — Versioning panel can't answer its one question ("what build is live?")

- Live values: `pwa_version=unknown`, `pwa_build_sha=unknown`, `worker_version=unknown`, `last_pages_deploy_at` **hardcoded `null`** server-side.
- Root cause is precise: `index.ts` reads `PWA_VERSION` / `PWA_BUILD_SHA` / `API_VERSION` from the container env; `.env.example` says "compose sets these at deploy"; but neither the box compose (p2/p3-box-steps) nor `deploy_model_c_full.sh` ever sets them (verified — zero matches in the deploy folder).
- This matters more than usual for this project: "did the tablets pick up the new PWA build?" is a recurring UAT question (it came up again with this week's GPS instrumentation). A working panel would answer it in one glance.
- The bottom half — `form_revisions` grouped by `spec_version` — **is real and useful** (currently: all 4 responses on `2026-07-14-r7`), and is the honest core to build the panel around.

### P2-1 — The two most critical incident controls are buried in a sub-tab named "Data Settings"

The global kill switch (emergency stop for all submissions) and the broadcast banner (message to every respondent) live *inside* the Data Settings sub-tab, below its heading, above the export table. An operator in an incident must already know to click "Data Settings" to find the stop button. These deserve their own first-position sub-tab (e.g. **Controls**) — or at minimum the sub-tab label should say so.

### P2-2 — Propagation copy is wrong in both directions

UI copy for both controls says *"Propagates within ~30 s on the next Worker config refresh."* Actual behavior on the current stack:
- **Server enforcement is immediate** — every submit/claim/start reads `f2_config` per request. The copy undersells the good news.
- **The respondent-facing banner/overlay takes up to 5 minutes** — the PWA polls `/exec?action=config` on a `CONFIG_REFRESH_INTERVAL_MS = 5 min` timer, and only when a device token exists. Unenrolled visitors (fresh `/f/<slug>` arrivals) never poll config at all: they are still blocked server-side, but they see the error envelope on Start rather than the maintenance banner.

### P2-3 — Cloudflare-era copy throughout the tab

Stale references that describe retired infrastructure, all user-visible:
- "stored in Cloudflare R2" (tab description, Files empty state, Help); "Files require R2 to be enabled" (`E_NOT_CONFIGURED` message — the Node `LocalFileStore` can't even return that code)
- "Backend unavailable — Apps Script staging may be unreachable" (`friendlyError` in **three** components: Versioning, Files, DataSettings — this is the same P3 flagged in the Reports audit, and this tab is where it's concentrated)
- "Worker version", "Last Pages deploy", "Worker cron fires every 5 minutes", "Worker config refresh"

Reality to write instead: files live on the server's disk; the API is `f2-api` (Docker on the VPS); config is MySQL `f2_config`.

### P2-4 — Help page: documents the dead features, omits the live dangerous ones

The Help "Apps & Settings sections" article documents all four sub-tabs *as the Cloudflare architecture* (R2, Worker cron, AS quota triage advice), and Workflow 7 documents the impossible export procedure. Meanwhile the **global kill switch and broadcast message do not appear anywhere in Help** — the single most consequential control in the portal is undocumented (the only "kill switch" mentions are the per-facility link toggles). Whatever is decided in Section 3, Help must be rewritten to match.

### P3 — Polish

- **P3-1: Upload MIME allowlist admits `application/octet-stream`** (client and server). Any file the browser can't type — including executables with unknown extensions — passes the "PDF / ZIP / PNG / JPEG / GIF" policy on upload; the extension allowlist is only enforced on *rename*. Admin-only surface, so low risk, but the stated policy isn't the enforced one. Fix: validate the filename extension on upload too.
- **P3-2: Versioning counts refusals as "submissions".** `form_revisions` totals all responses (4), while Coverage reports submitted 3 / refusals 1. Same-screen consistency: label it "responses" or exclude refusals.
- **P3-3: Files has no search box** even though the server supports `?q=` (works, probed). Optional; the list is tiny today.
- **P3-4: `included_columns`** — remove the dead field if exports are removed; wire it if they're kept.

---

## 3. What the tab should be (target definition)

An "Apps & Settings" tab for this system has three honest jobs:

1. **What build is live?** — PWA version + build SHA, API version, last deploy time, and spec-revision uptake. All wiring exists except the deploy script setting three env vars: inject `PWA_VERSION` (app `package.json`), `PWA_BUILD_SHA` (git short SHA at build), `API_VERSION` (server `package.json`) into the container env during `deploy_model_c_full.sh`'s rebuild, and replace the dead "Last Pages deploy" field with a deploy timestamp stamped the same way. Rename "Worker version" → "API version".
2. **Survey controls, findable and truthful** — kill switch + broadcast in a first-position **Controls** sub-tab, with copy that says what's true: *submissions are blocked immediately server-side; the banner on respondent devices updates within ~5 minutes; visitors who haven't started yet see a "temporarily paused" message when they tap Start.* Documented in Help with a "pause data collection" workflow.
3. **Files** — keep as-is, minus the R2 copy, plus the upload-extension check.

And one thing it should **stop** pretending to do:

4. **Scheduled Exports + Apps Script Quota: remove.** Recommendation over porting an executor: (a) no working consumer has existed since the cutover and nobody has missed it — the one real row was created in May, wedged since May 20, and never produced a complaint; (b) the actual export needs are already served or better served elsewhere (Coverage CSV export shipped this week; the CSPro-side data layer owns pipeline exports; an on-demand "Export responses CSV" on the Data tab would beat a cron writing files nobody fetches); (c) a scheduler is the kind of always-on machinery that deserves to exist only when someone actually consumes its output. Removal also deletes Workflow 7, the quota tab, `included_columns`, and the wedged row (one `DELETE FROM f2_settings` — needs your explicit go-ahead as a prod mutation, or it disappears naturally if the table is dropped later). The `f2_settings` table itself can stay (harmless, zero rows).

If you'd rather keep scheduled exports, the honest version is a `setInterval` sweeper inside f2-api that runs due settings, writes CSVs into the existing FileStore (so they surface in the Files tab — nice symmetry), stamps `last_run_*`, and adds a stuck-`running` timeout. That's roughly a day of work including tests; removal is under an hour. Either way the wedged row must be cleared.

*(Optional, later)* the quota slot could become a real **Health** widget for this stack — DB reachable, disk free on `/opt/app`, submissions today, DLQ depth. Park it; the Reports tab and Slack bot cover most of this.

---

## 4. Suggested sequence

| Step | Scope | Size |
|---|---|---|
| 1 | **Decision:** remove vs. port Scheduled Exports (recommendation: remove) | — |
| 2 | Copy + IA batch: Controls sub-tab first, quota tab removed, exports removed (or ported), all R2/Worker/AS copy rewritten, propagation copy corrected, upload extension check, Help rewrite (sections + workflows, add kill-switch workflow, delete Workflow 7) | ~half day, UI-only + one route deletion |
| 3 | Versioning wiring: deploy script injects the three env vars + deploy timestamp; rename fields; refusal-count label | small, touches deploy script |
| 4 | Prod cleanup: clear/delete wedged `s-57f9036a` row (explicit approval) | one statement |
| 5 | (Parked) Health widget in the freed slot | later |

Steps 2–3 are the same shape as the Reports-tab work: no schema changes, no data migration, deployable in one pass with the existing script.
