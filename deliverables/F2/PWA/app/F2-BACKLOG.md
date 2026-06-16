# F2 PWA — Remaining Work Backlog (Survey + Admin Portal)

> **Living checklist of everything left to do on the F2 Healthcare Worker Survey PWA
> and its Admin Portal.** Work these against the **staging** environment, then promote to
> prod. Supersedes the old `NEXT.md` (which was frozen at the April UAT R1/R2 era,
> pre-v2.0.0, pre-Admin-Portal).
>
> **Last reconciled:** 2026-06-16 — against the scrum epics (03/04/06), the live GitHub
> issues, and the closed v2.0.1 hotfix queue.

## Status snapshot

| Thing | State |
|---|---|
| **Prod** | `v2.1.0` live at https://f2-pwa.pages.dev (HCW Survey + Admin Portal, all 7 PH languages) |
| **Staging** | https://f2-pwa-staging.pages.dev (project `f2-pwa-staging`, branch `staging`) |
| **Admin Portal** | v2.0+ live; Users dashboard, RBAC + persona switching, JWT/`password_must_change`, `last_login_at` all shipped. **0 open issues.** |
| **⚠️ English-only mode** | **Temporarily ON** in both prod + staging (`VITE_ENGLISH_ONLY` in `.env.production`, 2026-06-16, Shan screenshot request). The language switcher is hidden until this is reverted. |
| **Open F2 GitHub issues** | 5 Survey bugs (`epic:f2-pwa`) — Section A below. Admin Portal / integration: none open. |

## How to work + ship on staging

The deploy is **push-triggered + CI-gated** (not manual wrangler anymore):

1. Branch off `staging` (or work on it directly for this push-to-deploy flow).
2. Edit + `npm run test` + `npx tsc -b --force` locally (CI runs typecheck + lint + vitest).
3. **Survey content/skip/validation changes go in `spec/F2-Spec.md` (+ the F2-Skip-Logic/
   Validation/Cross-Field docs), then `npm run generate`.** Never hand-edit `src/generated/*`.
   Admin-portal changes are plain React in `src/admin/**` (no generator).
4. Push to `staging` → **CI — F2 PWA** runs → on green, **CF Pages deploy** auto-ships to
   `f2-pwa-staging`. Promote to prod by fast-forwarding `main` to the same commit.
5. Forward-only sign-off: fold every behavioral fix back into the owning F2 spec doc.

---

## A. Survey — Active bugs (UAT, `epic:f2-pwa`) — DO FIRST

Ordered by severity / blocking impact.

- [ ] **#543 — Cold Enrollment** · `Critical (cannot proceed)` · Enrollment
  Pre-filled token rejected as **"Token malformed. Contact ASPSI ops."** — user cannot
  enroll at all. Likely token format/validation or the enrollment-URL token param. Pairs
  with #528. *(Windows Chrome.)*
- [ ] **#539 — Role-Select (section role-gating)** · `High` · routing
  Section visibility per persona doesn't match the spec'd routing. Required behavior:
  **C/D/E1** = Admin, Physician, Nurse, Midwife, Dentist, Nutritionist-Dietician only;
  **Pharmacist/Dispenser + Asst. Pharmacist** → skip to **E2**; **Physician Assistant,
  Nursing/Lab/Med-tech, Health Promo, Nutrition officer, PT, Dentist aide, BHW, Other** →
  no C–E1, go to E2; **Section G** = Physicians + Dentists only. Fix in `spec/F2-Spec.md`
  role-gating + `skip-logic.ts`. *(Biggest logic item.)*
- [ ] **#524 — Skip Logic (premature auto-advance)** · `High` · navigation
  Answering a question auto-skips to the next section while required-but-initially-hidden
  questions remain (observed **Q23, Q44, Q54, Q123**; worse toward section end). Same class
  as the historical #10 auto-advance bug — section-completion predicate in
  `MultiSectionForm.tsx` / `handleSectionValid`. *(Windows Chrome.)*
- [ ] **#528 — Token Auto-prefilled** · `Medium-High` · Enrollment
  Token is **not** auto-prefilled when the enrollment URL is opened fresh/incognito (5A.1);
  Verify should be one-tap. Related to #543 (token handling). *(Android tablet Chrome.)*
- [ ] **#587 — Q9 vs Q4 inline validation timing (Section A)** · `Medium` · validation UX
  The tenure-vs-age cross-field check (`Prof-01`: years of service < age − 20) only fires at
  the **review** stage, not before section navigation — want it enforced inline so the
  respondent corrects before proceeding. The rule works; it's a *when-it-fires* fix.
  *(iPad Safari, v2.1.0.)*

## B. Survey — Features / polish

- [ ] **E3-F2-PWA-DESIGN-004 — Self-host fonts** (`public/fonts/*.woff2`, replaces the CDN
  path from PR #38). **Gated on `pyftsubset`/fontTools** for proper Latin-Extended subsetting.
- [ ] **E3-F2-PWA-DESIGN-005 — Verde Manual hex refinement** from the official DOH brand-book
  PDF (Dept Order 2020-0011, Verde Vision 2023+). Current values are best-fit approximations.
- [ ] **M8/M9 tech debt** — `facility_has_bucas` / `facility_has_gamot` flags + per-respondent
  `response_source` capture (deferred since M8/M9; needed for E1/E2 gating fidelity — overlaps #539).
- [ ] **FacilityMasterList — real rows** before broader rollout (each row: `facility_id,
  facility_name, facility_type, region, province, city_mun, barangay`).

## C. Admin Portal

- [ ] **E4-APRT-046 — Files dashboard: Create Folder** · `est 2h`
- [ ] **E4-APRT-047 — Files dashboard: Rename** · `est 2h`
- [ ] **Admin mutations (was E3-F2-PWA-M12d)** — kill-switch toggle, `broadcast_message`
  editor, requeue-from-DLQ, `admin_users_change_password` / bulk-import. Backend deploy gap
  (#294) is now CLOSED, so these are unblocked. *(Ops currently edits the Config sheet directly.)*
- [ ] **Deferred design-review polish** — the MINOR-tier findings from the Admin Portal design
  review (`docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md`, v0.2: 8 BLOCKER /
  25 MAJOR / 15 MINOR — blockers+majors shipped; MINORs remain). Triage which still matter.

## D. Backend / Worker / Ops

- [ ] **E4-PWA-015 — Lower Worker PBKDF2 to 100k** (Workers runtime cap, #35) · `est 1h`
- [ ] **E4-PWA-010 — Secrets rotation policy doc** (HMAC, `JWT_SIGNING_KEY`, Apps Script deploy ID) · `est 2h`
- [ ] **E4-PWA-011 — Backup + restore runbook** for FacilityMasterList + submissions sheets · `est 3h`
- [ ] **Admin password rotation (prod side)** — `worker/scripts/hash-admin-password.mjs` →
  `wrangler secret put ADMIN_PASSWORD_HASH` (staging done; prod pending — see
  `project_admin_password_rotation_pending`).

## E. Integration / ETL

- [ ] **E4-INT-002 — Looker Studio (or equivalent) dashboard** over the unified store · `est 1d`
- [ ] **E4-INT-003 — Codebook-driven harmonization** wired into the ETL · `est 1d`
  *(ETL spec + skeleton E4-INT-001 already done — harmonization ETL skeleton is live.)*

## F. Testing / Pilot / Quality

- [ ] **E6-PWA-008 — F2 production pilot batch** — small facility cohort, success criteria,
  go/no-go to full rollout · `est 1d`
- [ ] **E6-PWA-009 — axe-core / Lighthouse a11y audit** — full report, AA compliance gate · `est 4h`
- [ ] **E6-PWA-010 — Performance baseline** — Core Web Vitals, bundle-size budget, regression
  tracking · `est 4h`. *(Note: the build already warns on >500 kB chunks — admin + vendor; a
  code-split pass would help here.)*

## G. Deferred / not committed (slot in only if pilot demands)

- [ ] **E3-F2-PWA-M12a — Per-HCW enrollment tokens** (replace email/static identity; spec §13 row 4)
- [ ] **E3-F2-PWA-M12b — Draft auto-migration across spec versions** (today a drift modal forces reload; spec §12 row 3)
- [ ] **E3-F2-PWA-M12c — iOS push notifications** for deadline reminders (spec §13 row 5)

## ✅ Done / superseded (kept for traceability — do NOT re-do)

- **R3 UX features** — exclusive "I don't know" (#16), "All of the above" auto-select (#17),
  scale-style matrix (#18): **all CLOSED/shipped.** (Epic items E3-F2-PWA-R3-001/002/003 +
  E6-PWA-007 are stale-open — treat as done.)
- **E4-PWA-014 — CF Pages auto-deploy regression (#34):** resolved — the `cf-pages-deploy.yml`
  workflow now deploys on push to staging/main; #294 (AS deploy gap) closed.
- **Admin Portal v2.0.1 hotfix queue:** #294 / #317 / #319 / #325 / #326 / #330 — all CLOSED.
- **Multi-language:** all 7 PH languages wired + live (currently masked by the temporary
  English-only flag — see snapshot above).

---

### Revert the temporary English-only mode (when screenshots are done)

Delete `.env.production` (or just its `VITE_ENGLISH_ONLY=true` line) and push to `staging` +
`main` — CI redeploys both with the language switcher + all 7 languages restored.

### Reference

- Repo: `cplreyes/ASPSI-DOH-UHC-CAPI-Development` · Issues filtered by label `epic:f2-pwa` / `epic:admin-portal`
- Spec (survey source of truth): `spec/F2-Spec.md` → `npm run generate`
- Admin Portal design spec: `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md`
- Slack: `#f2-pwa-uat` · UAT events auto-post via GitHub Actions
