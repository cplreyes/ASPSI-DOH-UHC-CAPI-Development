# Next step (future-Carl)

**Current phase:** Round 1 + Round 2 fully closed 2026-04-25. v1.1.0 + v1.1.1 milestones complete. Round 3 (v1.2.0) is queued with 3 UX features: "I don't know" exclusivity (#16), "All of the above" auto-select (#17), scale-question matrix view (#18).

**Closed batches:**
- v1.1.0 — UAT Round 1: 7 issues (skip-logic gates, Section G hide, max constraints, age letter input, etc.)
- v1.1.1 — UAT Round 2: 7 issues (specialty filter, real-time tooltips, conditional-required generator, submit error UX, Q9 Month optional, gate navigation regression fix)

**Latest staging deploy:** https://b1e46a55.f2-pwa-staging.pages.dev

## Round 1 issue triage (12 issues filed, 10 OPEN)

### ✅ Addressed in fix batch `3003c253` (shipped 2026-04-25, awaits verification)

| Issue | Title | Verification |
|---|---|---|
| #4 | Q4 age — max 99 | Try Q4=120 → blocked |
| #5 / #7 (dup) | Q9_2 months — max 11 | Try Q9_2=15 → blocked |
| #6 / #9 (dup) | Q12 UHC skip logic | Q12=No → Q13–Q30 skipped |
| #11 | Section G hidden for Nurse | Q5=Nurse → Section G not in tree |
| (also) | Section C Q31-gate | Q31=No → Q32–Q40 skipped |
| (also) | Section H Q91-gate | Q91='never happened' → Q92–Q95 skipped |

**Verify these on staging:** https://5466a539.f2-pwa-staging.pages.dev — then close issues #4/#5/#6/#7/#9/#11 with reference to commit + verification screenshot.

### ⏳ NOT yet addressed — Round 2 fix batch needed

| Issue | Title | Type | Notes |
|---|---|---|---|
| #2 | Specialty filter by role (Q5 → specialty list) | UX/data | e.g., Q5=Dentist → hide Dermatology. Pure filter, no schema change. |
| #8 | Q25 sub-question gating | Skip-logic | Salary only → Q27–Q30 unanswerable; #patients only → Q26 + Q28–Q30 unanswerable; both → Q28–Q30 unanswerable |
| #10 | Auto-advance on required questions | **Bug — needs investigation** | Form jumps to next section after one required answer (Q25, Q96/Q97, Q123–Q125) when sibling required fields still pending. Likely `MultiSectionForm.tsx` `handleSectionValid` or section-completion predicate. |
| #12 TC-005 | Language switch failure | Bug | Read `LanguageSwitcher.tsx` + i18n setup |
| #12 TC-010 | Submission flow ("No Submission yet" / "Nothing to Sync") | Bug | Read `App.tsx` `handleFinalSubmit` → `onSubmit` → IndexedDB write path |

### Suggested Round 2 batch sequence

1. **#10 first** — investigate auto-advance bug (highest severity, touches navigation logic shared by 3+ sections; everything else is contingent on form actually staying on the section)
2. **#8** — Q25 sub-question gating (similar pattern to B/C/H gates already in `skip-logic.ts`)
3. **#2** — specialty filter (data-driven, isolated)
4. **#12 TC-010** — submission flow
5. **#12 TC-005** — language switch
6. **Close duplicates** — #7 → close as dup of #5; #9 → close as dup of #6

## After Round 2 fix batch ships → Round 2 UAT cycle

1. Deploy to staging
2. Notify Shan via `#f2-pwa-uat` and email
3. UAT Round 2 retests + new comments → repeat
4. After clean Round → promote staging → main, redeploy production

## Deploy commands

**Redeploy staging:**
```bash
cd deliverables/F2/PWA/app
npm run build
npx wrangler pages deploy dist --project-name f2-pwa-staging --commit-dirty=true
```

**Redeploy production (only after final UAT sign-off):**
```bash
cd deliverables/F2/PWA/app
npm run build
npx wrangler pages deploy dist --project-name f2-pwa --branch main --commit-dirty=true
```

**Redeploy backend (Apps Script):**
```bash
cd deliverables/F2/PWA/backend
npm run build
# Paste dist/Code.gs into Apps Script editor → Deploy → New deployment (or Manage → edit existing)
```

## Reference URLs

- **Production:** https://f2-pwa.pages.dev (Cloudflare Pages, project `f2-pwa`, branch `main`)
- **Staging (SUT):** https://5466a539.f2-pwa-staging.pages.dev (project `f2-pwa-staging`, branch `staging`)
- **GitHub repo:** https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development
- **GitHub Issues:** https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues
- **UAT Guide:** https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/blob/staging/docs/F2-PWA-UAT-Guide.md
- **File a bug:** https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new/choose
- **Slack channel:** `#f2-pwa-uat` on aspsi-doh-uhc-survey2.slack.com (coordination only — formal feedback via GitHub Issues)
- **Backend deployment ID:** `AKfycbwdKrp0N7aKtu3nww2AbByACSRd0JwGK5UK9yTnicuW-S51ZwiiUfgzETS9D9fQ7ovD`
- **Spreadsheet:** https://docs.google.com/spreadsheets/d/19huXNUO6hcNX77U7Xm63rvFFhJWGXZ7b38Rrnq8d_KY/edit
- **Admin dashboard:** `/exec?action=admin`, login with `ADMIN_SECRET` from Script Properties

## UAT sign-off record

- **Round 1:** opened 2026-04-23, closed 2026-04-24 — Pass with comments (Shan Rykel Lait, ASPSI). 12 issues filed; 1 closed during round (#1, #3); 10 OPEN entering Round 2.
- **Round 2:** not yet opened. Awaiting Round 1 fix-batch verification + Round 2 fix batch.

## Deferred from M11 (slot in only if pilot feedback demands)

- **Per-HCW enrollment tokens** (spec §13 row 4). Current: static enrollment — any HCW ID works once a facility is selected.
- **Auto-migrate drafts across spec versions** (spec §12 row 3). Current: drift modal forces reload; drafts may fail validation on next save if schema shifts breakingly.
- **iOS push notifications for deadline reminders** (spec §13 row 5).
- **Admin dashboard mutations** (kill-switch toggle, broadcast_message editor, requeue-from-DLQ) — ops can edit Config sheet directly for now.

## M8/M9 tech debt still outstanding

- `facility_has_bucas` / `facility_has_gamot` flags; `response_source` per-respondent capture.
- Filipino instrument + chrome translations.

## FacilityMasterList

Populate with real facility rows before pilot HCWs onboard. Each row: `facility_id, facility_name, facility_type, region, province, city_mun, barangay`.

## Prior milestone shipped

**M11 — Hardening / release prep.** Runtime config (`/config`) polled every 5 min and on app open; `kill_switch` blocks submit via modal; `broadcast_message` shows as top banner; spec-version drift forces reload modal. Facilities auto-refresh on app open. Sync page "Change enrollment" button warns on unsaved draft. Playwright E2E covers runtime-config scenarios; golden-path + offline-retry stubbed pending form-schema-aware test helpers (covered by manual QA checklist for now). vitest-axe guards a11y. iOS safe-area + `100dvh` polish applied. `SyncPage` lazy-loaded. Cross-platform QA checklist: `../2026-04-18-cross-platform-qa-checklist.md`.

**Pilot deployed 2026-04-23.** Golden-path smoke test passed 2026-04-23. UAT Round 1 opened same day; closed 2026-04-24 with "Pass with comments". First fix batch shipped 2026-04-25.
