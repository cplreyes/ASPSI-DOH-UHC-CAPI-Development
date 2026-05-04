# F2 PWA + Admin Portal — Demo Guide for ASPSI Internal Meeting

**Date:** 2026-05-11 (Mon, 9:30 AM PHT)
**Audience:** ASPSI internal team (engagement managers, project leads, stakeholders)
**Presenter:** Carl Patrick L. Reyes
**Demo target:** F2 PWA — Healthcare Worker self-administered survey (production v1.3.0) + F2 Admin Portal (staging, pre-v2.0.0)
**Production version:** v1.3.0 codebase + **Verde Manual** visual identity + Worker JWT proxy (Phase F cutover live since 2026-05-01)

> **Pre-v2.0.0 framing — say this upfront.** The Admin Portal we're showing today runs on **staging** at PR #54 draft. E1 Chrome QA pass complete (all 8 FX-* findings verified green; FX-016 blank-page-on-full-nav fixed at source 2026-05-04). Cross-env (Firefox / Edge / tablet) pending — Sprint 004 stretch or Sprint 005. 7-day soak hasn't started. v2.0.0 ship target is Sprint 005+. What's shown here is feature-complete on Chrome but hasn't cleared all its gates — production cutover for the Admin Portal rides with v2.0.0.

> **Demo-day operating notes.** All paths work — full-page navigation, Ctrl+R, fresh tabs to deep URLs (Login appears, you re-auth, deep link is preserved). One caveat: in-memory session means Ctrl+R or new-tab loses your auth — that's by design (admin tokens never persist to localStorage; spec §10.4 limits blast radius on shared machines). Pre-tour the full demo flow once on the actual presenting machine to verify the FX-* fixes are visible end-to-end.

---

## Quick Reference (for the presenter)

| Item | Value |
|---|---|
| **Production PWA (v1.3.0)** | https://f2-pwa.pages.dev |
| **Staging PWA + Admin Portal** | https://staging.f2-pwa.pages.dev |
| **Admin Portal login** | https://staging.f2-pwa.pages.dev/admin/login |
| **Staging Worker (proxy)** | https://f2-pwa-worker-staging.hcw.workers.dev |
| **Backend (read-only for demo)** | [Apps Script Spreadsheet](https://docs.google.com/spreadsheets/d/19huXNUO6hcNX77U7Xm63rvFFhJWGXZ7b38Rrnq8d_KY/edit) |
| **Slack channel** | `#f2-pwa-uat` on `aspsi-doh-uhc-survey2.slack.com` |
| **GitHub repo (public)** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development |
| **Release notes** | [v1.2.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.2.0) · [v1.3.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.3.0) |
| **Admin Portal spec** | `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md` |

---

## Demo Credentials

### Admin Portal — staging users

| User | Password | Role | What this exercises |
|---|---|---|---|
| `carl_admin` | `100%SetupMe!` | Administrator | Full RBAC — sees all 5 dashboards; can create users + roles; can reissue tokens |
| `data_reader_test` | `ReadOnly_99X1` | DataReader | Read-only — can view Responses + Audit + Reports; cannot modify |

> **Why two users?** Demoing the RBAC model is the value prop of the Admin Portal — switching personas mid-demo shows ASPSI how the same backend exposes different capabilities to different roles. Don't only demo as Administrator; the role split is the point.

### F2 PWA — test HCW IDs (use these for demo, don't use real HCW IDs)

| Persona | HCW ID | Role to select | What this exercises |
|---|---|---|---|
| **Nurse** | `DEMO-NURSE-02` | Nurse | Section G is **hidden** (role-conditional skip) |
| **Physician** | `DEMO-PHYS-02` | Physician/Doctor | Section G **shown**; full medical specialty list |
| **Test HCW (existing)** | `HCW-TEST-001` | (already enrolled at `FAC-TEST-001`) | Re-encode demo via Admin Portal `/admin/encode/HCW-TEST-001` |

> The `DEMO-*-02` prefix segregates today's submissions from prior UAT (`UAT-*`) and the previous demo (`DEMO-*-01`).

---

## What's new since 2026-04-27

Five-bullet recap before diving in:

1. **F2 PWA v1.3.0 in production** since 2026-05-01 — Phase F cutover executed. Production now runs the **Worker JWT proxy** (the auth re-arch we previewed on staging at the last meeting). The HMAC-in-bundle CRITICAL CSO finding is closed in production.
2. **15 internal-QA fixes shipped** in v1.3.0 (#19–#30, #35, #45, #46). See release notes link above.
3. **F2 Admin Portal feature-complete on staging** — Sprints AP1–AP4 done; 40 sub-tasks closed. Spec at `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md`. Mirrors CSWeb's documented permission model 1:1 (5 dashboards × 5 roles × per-instrument flags).
4. **R2 file storage** wired up for the Admin Portal — staging buckets live since 2026-05-02 (cron break-out CSV writes + admin file uploads).
5. **F1 Designer sign-off closed 2026-05-04** — three-sprint carry retired. F1 → Build-ready; FMF Designer pass (E3-F1-001) in flight this sprint.

---

## Demo Flow (~30 min walkthrough)

### Part 1 — F2 PWA Production (v1.3.0) — quick recap (~5 min)

1. **Open** https://f2-pwa.pages.dev on a laptop (Chrome) and a phone if available.
2. **Talking points:**
   - "Same Verde Manual identity you saw at the last meeting — pale verde paper, DOH emerald, Newsreader serif, Public Sans body."
   - "Header now reads `v1.3.0` — under the hood, every PWA→backend request goes through a Cloudflare Worker (`f2-pwa-worker.workers.dev`) that mints a short-lived JWT. Long-lived secret stays server-side; the device only ever holds a JWT scoped to its enrollment."
3. **Brief enrollment + 1 section** to show the form is alive (don't burn 10 minutes on this — they saw the full walkthrough 2 weeks ago):
   - Enter `DEMO-NURSE-02`, refresh facility list, select any facility, enroll.
   - Fill Section A (~30 sec).
   - Submit → Thank-you screen.
4. **Key talking point:** "Production has handled UAT Rounds 1 + 2 (13 issues closed). Round 3 backlog at Issues #16/#17/#18 (UX enhancements) — gated on ASPSI prioritization."

### Part 2 — F2 Admin Portal walkthrough (~15 min)

1. **Open** https://staging.f2-pwa.pages.dev/admin/login in a fresh browser tab.
2. **Login as Administrator:** `carl_admin` / `100%SetupMe!`. Show the role badge in the layout.
3. **Talking points:**
   - "This is the F2 PWA's Admin Portal — staging only for now, ships to production with v2.0.0 in the next sprint."
   - "It mirrors the CSWeb dashboard model that ASPSI/DOH already use for the CSPro instruments. Same shape: 5 dashboards, role-aware nav, per-instrument flags. The intent is that an ASPSI ops user who's used CSWeb can sit down at this and not need a 30-page manual."

#### Section A — Data Dashboard (~4 min)

4. **Navigate to Responses tab.** Show the list view — sortable, paginated, filterable.
5. **Drill into a submission.** Show the response detail view: per-question answers, metadata, timestamps.
6. **Switch to Audit tab.** Show the per-action audit log (every PWA submit, every admin action, every HMAC-signed Worker→Apps Script call).
7. **Switch to DLQ tab.** Show the dead-letter queue (failed submissions that retried and gave up; manual replay UI).
8. **Switch to HCWs tab.** Show enrollment list. Drill into `HCW-TEST-001`.
9. **Talking point:** "DLQ is the operational safety net. If Apps Script is rate-limited or a sheet is locked, the submission queues here instead of disappearing. This is the kind of thing CSWeb has too — surfacing it in the same UI lets ops triage in one place."

#### Section B — Reissue Token Flow (~3 min) — *the kind of thing field ops will need*

10. With `HCW-TEST-001` open, click **Reissue Token**.
11. Modal opens with a mono URL + Copy button + QR code.
12. **Talking points:**
    - "Field scenario: HCW lost their device or the token expired. Ops user finds the HCW, clicks Reissue, and either copies the new URL into a Viber message or shows the QR for the HCW to scan in person."
    - "Compare-and-set on `prev_jti` — if two admins try to reissue at the same time, one of them gets a 409 conflict and re-pulls. No silent overwrites."

#### Section C — Apps Dashboard + R2 Files (~3 min)

13. **Navigate to Apps dashboard.** Show the Versioning panel — current PWA build SHA, Worker version, Apps Script deployment ID.
14. **Switch to Files tab.** Show the R2-backed file uploader. Upload a small file, show it in the list, download it, delete it.
15. **Talking points:**
    - "Files are backed by Cloudflare R2 — staging buckets live since 2026-05-02. Quotas + allowlist enforced (no SVG/HTML/JS, ≤100MB)."
    - "Versioning panel is the answer to 'which build is in front of users right now?' — useful when a UAT bug report comes in and we need to confirm the user wasn't on a stale cache."

#### Section D — Users + Roles dashboards (~3 min)

16. **Switch to Users dashboard.** Show the list. Click **Bulk Import** — show the CSV preview UI (don't actually import).
17. **Switch to Roles dashboard.** Show the role checkbox grid (5 dashboards × per-instrument flags). Show the built-in roles (Administrator + DataReader can't be deleted; their flags are immutable).
18. **Talking point:** "The role grid is where you'd onboard new ASPSI ops users without writing code — give them DataReader if they only audit, DataWriter if they correct submissions, Administrator if they manage users."

#### Section E — Switch personas (~2 min) — *the RBAC point*

19. **Logout. Login as `data_reader_test` / `ReadOnly_99X1`.**
20. Show that the nav is reduced — Users + Roles dashboards aren't visible. Click into Responses; show that "Reissue Token" is hidden / disabled. Click Files — show that Upload/Delete are hidden, only download is available.
21. **Talking point:** "Same backend. Different role. The capability surface adapts. This is what makes adding ASPSI ops users low-effort post-v2.0.0 ship — they get a role, not a custom build."

### Part 3 — End-to-end interaction (~5 min) — *the data flow*

1. **Switch back to the F2 PWA tab** (still showing Production v1.3.0). Show the spreadsheet [F2_Responses sheet](https://docs.google.com/spreadsheets/d/19huXNUO6hcNX77U7Xm63rvFFhJWGXZ7b38Rrnq8d_KY/edit) in a third tab.
2. **Submit a fresh response** as `DEMO-PHYS-02` — fill enough sections to get to Submit (Section A + skip-fill the rest).
3. **Show the row appearing in the spreadsheet** F2_Responses sheet (refresh).
4. **Switch back to the Admin Portal Responses tab. Refresh.** Show the new row appearing in the Admin Portal too.
5. **Click into the new submission.** Show the full detail view including geolocation (if browser gave permission), source path (`pwa_self`), and the audit chain.
6. **Talking points (the data path):**
   - "HCW submits via PWA → Worker validates JWT → Worker forwards HMAC-signed POST to Apps Script → Apps Script writes to F2_Responses + F2_Audit + F2_HCWs sheets."
   - "Admin Portal reads via the same Worker, gated by RBAC: `dash_data:true` to see the dashboard, `f2:true` per-instrument flag to see F2 specifically."
   - "Cron break-out fires every 5 minutes — Apps Script writes scheduled CSV breakouts to R2 for downstream consumers (analyst tools, reports). That's the 5-min ticker you'd see in `wrangler tail`."

### Part 4 — Roadmap / Q&A (~5 min)

Surface these talking points proactively before Q&A; they're the most likely questions:

- **Why staging, not production?** Cross-platform QA pass is in flight (paused at E1 Chrome G3 with 3 findings logged in `qa-report-cross-platform-admin-portal-2026-05-02.md`); 7-day soak hasn't started; v2.0.0 ship target is Sprint 005 (~week of 2026-05-12). Once gates clear we cut over with the same path-B model used for Phase F.
- **What about production CSWeb integration?** Out-of-scope for v2.0.0 (which is F2 PWA-side only). CSWeb provisioning + the F1/F3/F4 CSPro side gets its own integration ETL spec in a later sprint — the Admin Portal is the first dashboard, not the only one.
- **Filipino translations on the portal?** Not yet wired — the locale switcher infra is on the PWA side; admin UI is English-first by design (ops users, not field respondents). Reasonable add post-v2.0.0 if there's demand.
- **F1 / F3 / F4 instruments?** F1 Designer sign-off closed 2026-05-04 → F1 Build-ready. F3 + F4 specs Build-ready since 2026-04-21. FMF builds + Designer validation in this Sprint 004 + next.

---

## What NOT to Do During the Demo

- **Don't share the staging Admin Portal URL or credentials publicly** — the URL is staging-only; if it leaks, it's a soft target. Internal ASPSI audience is fine; don't paste the URL into DOH chat or email.
- **Don't use real HCW IDs** — submissions land in production sheets. Stick to `DEMO-*-02` prefix.
- **Don't promise the v2.0.0 ship date as a commitment** — frame it as "target Sprint 005" with the QA + soak gates as "must clear first." Soak is ~7 calendar days from the day it opens.
- **Don't claim production-ready for the Admin Portal** — it's feature-complete on staging, that's distinct. Use "feature-complete on staging, gates pending" as the phrase.
- **Don't demo F1 / F3 / F4 CSPro instruments here** — separate runtime, separate dashboards. If asked, say: "F1 Build-ready as of last week; F3 + F4 Build-ready since Apr 21; FMF builds in flight this sprint."
- **Don't trip on the 3 known QA findings.** They're logged in `qa-report-cross-platform-admin-portal-2026-05-02.md`; pre-tour your demo path once before the meeting to make sure you don't accidentally walk into them on stage.

---

## Pre-Meeting Checklist (~10 min, day-of)

- [ ] **Pre-tour the demo path.** Run Parts 1–3 once on the actual machine you'll present from. Catch any auth glitches, stale caches, or QA-finding intersections before the meeting starts.
- [ ] **Confirm staging Worker is healthy.** Hit `https://f2-pwa-worker-staging.hcw.workers.dev/admin/api/login` with a curl smoke (the same one in the E4-APRT-039 runbook); 200 means the demo path is alive.
- [ ] **Confirm `data_reader_test` user is unchanged** — memory `project_f2_admin_staging_creds.md` notes the role currently has `dash_apps:true` from a PATCH test; if the role-grid demo (Part 2-D) needs a clean DataReader, reset the flag in the Roles dashboard before meeting.
- [ ] **Open the spreadsheet in a tab in advance.** Authenticate to it now so you don't burn 30 seconds in front of the audience.
- [ ] **Have the release-notes URLs in your clipboard manager** for fast paste during Q&A.
- [ ] **Decide audio source.** If meeting is remote: confirm screen share + audio.

---

## After the Demo — Cleanup + Followup

The submissions you create with `DEMO-*-02` HCW IDs land in the live `F2_Responses` sheet. Two options:

1. **Filter, don't delete:** Add a column filter `WHERE hcw_id NOT LIKE 'DEMO-%'` in any analysis. Recommended.
2. **Soft-delete via Admin Portal:** The DLQ replay / response-delete flow is in the portal but use sparingly — the audit trail is fine to keep.

Document the meeting in `scrum/standups/2026-05-11.md` as a Today (Plan) follow-up. If demo surfaces new feature asks, file as GitHub issues with label `from-aspsi-internal-2026-05-11`.

If ASPSI brings up specific concerns on the Admin Portal during the demo, **note them in the meeting; don't promise immediate fixes.** Triage post-meeting:
- Bugs in PR #54 scope → land before v2.0.0 ship.
- New scope post-v2.0.0 → file as GitHub issue, queue for Sprint 005+.
- Concerns about the role model or data flow → escalate to the spec at `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md` first; structural changes there.

---

*Generated 2026-05-04 for the 2026-05-11 ASPSI internal meeting. Source patterns: `docs/F2-PWA-Demo-Guide-2026-04-27-ASPSI-Internal.md` (the prior week's pattern) + `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md` (Admin Portal spec) + `deliverables/F2/PWA/qa-reports/qa-report-cross-platform-admin-portal-2026-05-02.md` (known QA findings to dodge) + `wiki/concepts/F2 Admin Portal.md` (concept overview). Pre-v2.0.0 framing rules per `feedback_data_programmer_scope.md` (CAPI-technical content is in-scope for stakeholder demos).*
