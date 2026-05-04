# F2 PWA — Demo Guide for ASPSI Internal Meeting

**Date:** 2026-04-27 (Mon)
**Audience:** ASPSI internal team (engagement managers, project leads, stakeholders)
**Presenter:** Carl Patrick L. Reyes
**Demo target:** F2 PWA — Healthcare Worker self-administered survey (production)
**Production version:** v1.1.1 codebase + **Verde Manual** visual identity (DOH-anchored emerald + pale verde paper)

---

## Quick Reference (for the presenter)

| Item | Value |
|---|---|
| **Production URL (canonical)** | https://f2-pwa.pages.dev |
| **Staging URL (auth re-arch — optional)** | https://c9765fdf.f2-pwa-staging.pages.dev |
| **Backend (read-only for demo)** | [Apps Script Spreadsheet](https://docs.google.com/spreadsheets/d/19huXNUO6hcNX77U7Xm63rvFFhJWGXZ7b38Rrnq8d_KY/edit) |
| **Admin dashboard** | `https://f2-pwa.pages.dev/exec?action=admin` (login with `ADMIN_SECRET` from Script Properties) |
| **Slack channel** | `#f2-pwa-uat` on `aspsi-doh-uhc-survey2.slack.com` |
| **GitHub repo (public)** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development |
| **Release notes** | [v1.1.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.1.0) · [v1.1.1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.1.1) |

---

## Demo Credentials

> **Why no real token?** Production v1.1.1 uses **static enrollment** — any HCW ID works once a facility is selected. Per-HCW token enrollment is deferred from M11 and is a planned follow-up (the auth re-arch on staging is a separate hardening for the API key, not per-user authentication). For this demo, the HCW ID is the only credential you need.

### Test HCW IDs (use these for demo — don't use real HCW IDs)

| Persona | HCW ID | Role to select | What this exercises |
|---|---|---|---|
| **Nurse** | `DEMO-NURSE-01` | Nurse | Section G is **hidden** (role-conditional skip) |
| **Physician** | `DEMO-PHYS-01` | Physician/Doctor | Section G **shown**; full medical specialty list |
| **Dentist** | `DEMO-DENTIST-01` | Dentist | Section G shown; dental-specialty-filtered list (medical specialties hidden) |

> Pattern matches the existing UAT IDs (`UAT-NURSE-01` / `UAT-PHYS-01` Shan used in Round 1 + 2). The `DEMO-` prefix segregates today's meeting submissions from UAT data so you can filter/clean later from the spreadsheet.

### Facility selection

The facility list is currently populated with **test rows** (real facilities will be provisioned by ASPSI before pilot enumerator onboarding — `FacilityMasterList` schema documented in `deliverables/F2/PWA/app/NEXT.md`).

For the demo: **pick any facility from the dropdown** after tapping "Refresh facility list". Recommend picking a different facility per persona to show the facility-conditional binding.

---

## Demo Flow (~12-15 min walkthrough)

### Part 1 — Visual Identity (~2 min)

1. **Open** https://f2-pwa.pages.dev on a laptop (Chrome) and a phone if available.
2. **Talking points:**
   - "This is the production-live healthcare worker survey, deployed at `f2-pwa.pages.dev`."
   - "Visual identity is **Verde Manual** — anchored on DOH's *Verde Vision / Berde para sa bayan* institutional palette. Pale verde paper background, DOH emerald accents, Newsreader serif headings, Public Sans body."
   - "Header reads `v1.1.1 · spec 2026-04-17-m1` — versioned and traceable to the spec snapshot it was built against."

### Part 2 — Enrollment + One Section (~3 min)

1. On the **Enroll** screen, enter HCW ID: `DEMO-NURSE-01`.
2. Tap **Refresh facility list**. Show the dropdown.
3. Select any facility. Tap **Enroll**.
4. **Talking point:** "The form opens to Section A — Healthcare Worker Profile. Section navigation is locked: you can't skip ahead, you must complete sections in order."
5. Fill Section A end-to-end (~1 min):
   - Name (any), employment type, sex, age (e.g., 35), role: **Nurse**, private practice toggle, tenure, days/week, hours/day.
6. **Talking point:** "After the last required field, the form **auto-advances** to the next section within 1 second — no Submit button click needed mid-flow. This was the highest-impact UX request from Round 1 UAT."

### Part 3 — Skip Logic Showcase (~3 min)

7. Walk through Section B (UHC awareness — 13 yes/no questions).
8. **Talking point:** "Section G is **hidden** for the Nurse persona. Only Physicians and Dentists see Section G — this is enforced by role-conditional skip logic, not by a manual filter."
9. Show the section tree on the left/top — point out that G doesn't appear.
10. **Optional — show Q12 gate:** Set Q12 (UHC awareness) to **No** → all of Q13–Q30 are skipped.

### Part 4 — Language Switch (~1 min)

11. Tap the language toggle (top-right). Switch to **Filipino**.
12. **Talking point:** "All chrome (buttons, banners, tooltips) switches immediately. **Question text** is currently English placeholders — Filipino translation delivery is on ASPSI's side; the switcher infrastructure is in place to drop in translations without code changes."

### Part 5 — Review + Submit (~3 min)

13. Continue through remaining sections (skip-fill is fine — pick "Don't know" or "No" liberally).
14. On the **Review** screen, scroll through.
15. **Talking point:** "The Review screen groups answers by section. Edit button next to each section round-trips back to the form, preserving all other answers."
16. Tap **Submit**. Show the "Thank you" screen.

### Part 6 — Where the Data Lands (~2 min)

17. Open the [Spreadsheet](https://docs.google.com/spreadsheets/d/19huXNUO6hcNX77U7Xm63rvFFhJWGXZ7b38Rrnq8d_KY/edit) in another tab.
18. Show the new row appearing in the `Submissions` sheet (you may need to refresh).
19. **Talking points:**
    - "Backend is Google Apps Script + Sheets — no separate database to operate."
    - "Submissions are de-duplicated via `client_submission_id` (idempotent — re-syncs don't create duplicates)."
    - "`survey_language` column auto-injected so we know which locale was used."
    - "Sync is queue-based with retry — if the device is offline at submit time, the response is held in IndexedDB and submitted on next reconnect."

### Part 7 — Operations Asks ASPSI Probably Wants to Know (~2 min)

- **UAT pipeline**: 18 issues fixed across Rounds 1 + 2 (closed 2026-04-25). Round 3 (v1.2.0) backlog has 3 UX features queued: exclusive "I don't know", "All of the above" auto-select, matrix view for scale-style questions.
- **Slack automation** to `#f2-pwa-uat`: real-time issue events + 09:00 MNL daily digest + milestone-closed release notes — ASPSI/DOH stakeholders see UAT progress without anyone manually posting.
- **Filipino translations**: gating on ASPSI delivery; switcher infra ready to accept drop-in locales.
- **FacilityMasterList**: needs real facility rows from ASPSI before enumerator onboarding (currently test data only).
- **Auth re-arch (production cutover today)**: Worker JWT proxy on staging mitigates a CRITICAL security finding from the 2026-04-25 `/gstack-cso` audit (HMAC was previously inlined into the bundle). Production cutover gated on 24h staging soak + 2 open issues; **earliest window ~17:35 PHT today**.

---

## Optional — Show the Auth Re-Arch (Staging) — ~3 min

If the conversation drifts to security, hardening, or "what's next":

1. Open https://c9765fdf.f2-pwa-staging.pages.dev (staging — note the URL may have rotated; check `deliverables/F2/PWA/app/NEXT.md` for latest).
2. **Talking points:**
   - "Staging runs the auth re-architecture — instead of HMAC inlined into the JS bundle (where any browser-tools user could read it), the device gets a short-lived JWT from a Cloudflare Worker proxy at `f2-pwa-worker.hcw.workers.dev`."
   - "Worker holds the long-lived secret server-side; client only ever sees a JWT scoped to its enrollment."
   - "PR #31 closed the CRITICAL CSO finding. Phase F is the production cutover — gated on 24h clean soak from yesterday's deploy + resolution of two follow-up issues filed during the staging cutover (#33 multi-select bug, #34 CF Pages auto-deploy regression)."
3. **What NOT to claim:** Per-HCW user tokens (where each HCW gets their own credential, like a one-time PIN at enrollment) are still **deferred from M11** — the staging auth re-arch hardens the **API-level secret**, not per-user identity. Two distinct improvements; don't conflate.

---

## What NOT to Do During the Demo

- **Don't use real HCW IDs** — submissions land in the production spreadsheet and would need to be backed out manually. Stick to `DEMO-*` IDs.
- **Don't disable the kill-switch / change runtime config** from the admin dashboard during the meeting — admin-side mutations are not yet in the UI; you'd be editing the Config sheet directly.
- **Don't promise Filipino instrument translations on a date** — that's gating on ASPSI delivery, not Carl's track.
- **Don't demo F1 / F3 / F4 CSPro instruments here** — those run in CSPro Designer + need a CAPI runtime, separate from this PWA. If asked, say: "F1 DCF is Designer-ready; F3 + F4 specs are Build-ready; FMF builds queued in Sprint 003."

---

## After the Demo — Cleanup

The submissions you create with `DEMO-*` HCW IDs land in the live `Submissions` sheet. Two options:

1. **Filter, don't delete:** Add a column filter `WHERE hcw_id NOT LIKE 'DEMO-%'` in any analysis. Fastest. Recommended.
2. **Soft-delete via Admin endpoint:** Not yet exposed via UI — direct sheet edits would be the only path. Don't bother for a small demo run.

Document the meeting in `scrum/standups/2026-04-27.md` as a Today (Plan) follow-up under E0-010 / E0-020 (depending on whether ASPSI Mgmt Committee or just operational ASPSI). If demo surfaces new feature asks, file as GitHub issues with label `from-aspsi-internal-2026-04-27`.

---

*Generated 2026-04-27 for the same-day ASPSI internal meeting. Source patterns: `docs/F2-PWA-UAT-Guide.md` (test ID format, scenario shape) + `deliverables/F2/PWA/app/NEXT.md` (URLs, current backlog, deferred items) + Verde Manual identity (`deliverables/F2/PWA/app/DESIGN.md`).*
