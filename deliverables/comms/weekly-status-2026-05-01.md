---
type: deliverable
kind: weekly-status
audience: internal (Carl + project record)
sender: Carl Patrick L. Reyes
date_drafted: 2026-04-30
status: internal-snapshot
related_task: E0-010 / E0-011
sprint: 003
sprint_window: 2026-04-27 to 2026-05-01
tags: [weekly-status, internal, sprint-003, e0-010, e0-011]
---

# Weekly Status — Week of 2026-04-27 (Sprint 003)

**Author:** Carl Patrick L. Reyes
**Status:** internal artifact, not sent to ASPSI Mgmt or DOH
**Snapshot taken:** 2026-04-30 (Sprint 003 Day 4 EOD; Friday close happens after this is written)

### Headline

Two long-running F2 HCW PWA blockers cleared this week — both production cutover prerequisites resolved (Issues #33 + #34 closed via PRs #43 + #44, merged + manually deployed to staging). 24-hour soak now running; production cutover go/no-go decision lands EOD Friday based on soak results. F1 Designer sign-off (E2-F1-010, two-sprint carry) still owed before sprint close.

### Closed this week

- **F2 PWA — Round 3 internal-QA blockers cleared.** Issue #33 (multi-select state pollution in Sections F/G — RHF checkbox-group DOM-read clobbering the array on cross-question onChange) and Issue #34 (CF Pages auto-deploy not firing) both shipped to staging. Fix: drop `name={reg.name}` from multi-select checkboxes; replace native CF Pages auto-deploy with `.github/workflows/cf-pages-deploy.yml` triggered on `workflow_run`. PRs #43 and #44 merged 2026-04-30, manual `wrangler pages deploy` of SHA `0f65defc` live on staging. 24-hour soak in progress.
- **CAPI tablet specifications submitted (E5-CAPI-001).** Email to Juvy 2026-04-29 with three pricing tiers (recommended ~₱13–20K, affordable ~₱9.5–14K, modest ~₱7–12K), recommended models, accessory list, 10–15% spare-ratio recommendation. Awaiting procurement steer.
- **Survey Manual — CSPro CAPI section + 2 appendices drafted (E7-DOC-001).** Drafts at `deliverables/Survey-Manual/CSPro-Section-Draft_2026-04-29.md` ready for Kidd. SPEED 2023 legacy cleaned out of the rewrite. Open questions tracked: questionnaire-numbering scheme, F2 manual scope, PAPI fallback policy.
- **F1 Designer dictionary walkthrough preparation complete.** Bug list (5 closed-in-code, 1 PARTIAL pending ASPSI Q166, 2 deferred-with-rationale per spec §5) and case-control block disposition finalized. Designer-side sign-off pass queued — work bounded, just needs Carl in CSPro Designer.
- **DOH/ADB/EXECOM matrix feedback triaged (E0-032a).** All 23 Annex G remarks routed against current build state: 14 DONE in build, 5 DEFERRED-WITH-RATIONALE (analysis-layer / sampling-frame, flagged for Epic 11 + IR), 3 VERIFY pending ASPSI spot-check, 1 OPEN sub-question (F2 burnout/satisfaction reduction-vs-removal — current build is *more conservative* than Annex G commitment). No new CAPI-schema work falls out. Triage at `wiki/analyses/Analysis - DOH-PMSMD Matrix Feedback Triage.md`.
- **Weekly status format defined (E0-010).** Template + this first instance. Internal snapshot, not Mgmt-facing.

### In flight (next week — Sprint 004 carry-forwards)

- **E2-F1-010 — F1 Facility Head Designer sign-off.** Two-sprint carry; if it doesn't close Friday it becomes three-sprint. Owner: Carl. Bounded ~4h.
- **E3-F1-001 — F1 Form file Section A layout in Designer.** Generator skeleton in place; Designer pass unblocks on F1 sign-off. Owner: Carl. Bounded ~4h.
- **E4-PWA-013 — F2 PWA Phase F production cutover** (gated on soak staying clean through Friday afternoon). Owner: Carl, executes per `docs/superpowers/runbooks/2026-04-26-f2-auth-cutover.md`.
- **E7-DOC-001 — Survey Manual review iteration with Kidd.** Owner: Kidd; Carl on standby for clarifications.
- **E0-032a follow-up — F2 burnout reduction-vs-removal confirmation.** Owner: ASPSI internal review (Esmeralda / Kidd). Default if no response by mid-Sprint-004: full removal stands and the triage closes.

### Open items / decisions owed

- **Tablet procurement tier go/no-go** — owner: ASPSI Mgmt. Ask sent 2026-04-29; no response yet.
- **Survey Manual reviewer assignment** — owner: ASPSI internal (Kidd default). Confirming Kidd is sufficient vs. needing additional eyes.
- **F2 HCW burnout/satisfaction reduction-vs-removal** — owner: ASPSI internal review. Default = full removal stands.
- **CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID repo secrets** — owner: Carl. Needed before the new cf-pages-deploy workflow does anything; manual `wrangler pages deploy` is the working fallback in the meantime.

### Risks on the watchlist

- **F1 Designer sign-off slipping to three-sprint carry.** If E2-F1-010 doesn't close Friday, momentum cost on the carry-forward grows. Mitigation: prioritize the Designer pass on Friday, ahead of the cutover decision.
- **F2 PWA cutover soak tight.** 24-hour window ends ~16:40 PHT Friday, right at sprint close. Anomaly during soak → cutover defers cleanly to Sprint 004 (production stays on the path-B Verde Manual port; HMAC-in-bundle CSO finding still applies to prod-only until then).

### Deliverable production state (informational)

F1 / F3 / F4 instruments + supporting CAPI artifacts: F3/F4 build-ready since 2026-04-21, F1 closes on Designer sign-off this sprint. F2 PWA in production at v1.1.1 with Verde Manual visual identity. Survey Manual CSPro section drafted for review. From a Data Programmer perspective the production-side deliverables under D1–D6 are tracking; downstream tranche acceptance and submission timing are in ASPSI ops / PI lane (out-of-scope for this snapshot per `feedback_tranche_tracking_out_of_scope`).

---

## Drafter notes

- Headline framing pivots Friday based on the soak outcome:
  - **Soak clean:** keep current framing; add a "Closed this week" bullet noting Phase F cutover executed.
  - **Soak shows a regression:** rewrite headline to flag deferral; move the cutover to "In flight" with new gate criteria; add the soak-failure detail to "Open items / decisions owed".
- This snapshot is the source of truth for what Sprint 003 produced. If a Mgmt-facing brief is needed later, the conversion is mechanical (add `To:` block, soften voice, drop code-level detail like PR / SHA / RHF specifics). The information transfers cleanly.
- Source material: `scrum/sprint-current.md`, `scrum/product-backlog.md` § Status at a Glance, this week's standups, `log.md` tail.
