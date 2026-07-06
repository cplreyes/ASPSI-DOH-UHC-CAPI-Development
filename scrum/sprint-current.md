---
sprint: 013
start: 2026-07-06
end: 2026-07-10
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: F2 configuration-setup migration to our prod server (also backs F1/F3/F4 CSWeb) · Supervisor App finalization (+ UAT Round 6) · stay pretest-ready · ETL extraction DEFERRED; tabulation clarifications → 3pm meeting · open: questionnaire-change timing
created: 2026-07-03 — Mode D skeleton at the S012→S013 boundary
locked: 2026-07-06 (Mode A — Monday kickoff); RE-ALIGNED 2026-07-06 to the Monday meeting notes
---

# Sprint 013 — F2 to prod server + Supervisor App finalization (pretest-ready)

> [!info] Where S012 left the project
> **Goal landed — first sprint where plan and value agreed.** All four perennial carries cleared by Day 2 (E0-SCRUM-SYNC finally BUILT; PSA closed out-of-lane; Goal B killed; field-ready criterion wired into `check_field_ready.py` + verified FIELD-READY). UAT R5 closed 06-29 (78/79). The freeze week became a build week: pretest assignments ready (Los Baños, 84 QNs, printed sheets), tabulation plan spec-complete + Stata-12 proven (197 SSRCS tables), fleet version-stamped v1.0.x on all 4 surfaces, DHS benchmark → data layer + R1a + R2 + R3 shipped byte-identical (freeze intact). Full record: `scrum/sprints/sprint-012.md` + `log.md`.

## Sprint Goal

> **Migrate the F2 configuration setup onto our own production server (which also backs the F1/F3/F4 CSWeb sync) and finalize the Supervisor App (through UAT Round 6) — while staying pretest-ready.** ETL variable extraction (`transform.py`) is **deferred**; the tabulation clarifications go to Ms. Myra's **3pm tabulation meeting today** (Carl shares the findings). _Re-aligned to Carl's Monday meeting notes, 2026-07-06._

## Carry-in from Sprint 012

| ID | Item | State | S013 disposition |
|---|---|---|---|
| **E10-ETL-EXTRACT** | `transform.py` — per-instrument questionnaire-variable extraction from the CSWeb breakout DBs per codebook (checkbox split-to-dummies; F3 pay-roster + F2 extracts; lowercased-DCF instrument vars + harmonized shared dims) | scoped; codebook v0.4 + ETL skeleton + Stata-12 do-files proven | **DEFERRED (Carl re-prioritized 2026-07-06)** — not this sprint; revisit after F2/hub. NOTE: **variable/data inconsistencies surfaced during the 197-table mapping** — will feed this extraction. Kept in Goal B. |
| **Tabulation decision memo** | 47-partial / 3-gap (tables 1.6, 2.51, 4.2) memo → ASPSI | mapping complete in `deliverables/tabulation-plan/` | Deferred with E10-ETL-EXTRACT — revisit together. |
| **Designer compile gate** | fresh-Designer compile of the R2-numbered builds (F1/F3/F4 + hub) | **F1/F3/F4 effectively CLEARED** — the weekend #830/#832/#833 redeploys went out via the `.csds` route, which compiles the `.pen` fresh (a compile failure hard-stops the deploy), so their message-numbered builds passed. **HUB still pending** (not redeployed; still v1.0.1). | Run the hub's compile before its next deploy; F1/F3/F4 satisfied. |
| **Supervisor App finalization + UAT R6** | hub built + device-verified; needs finalization polish + hub Designer compile + deploy; R6 blocked on ASPSI account import + real names + `supervisor-qa` | roster built + deployed + device-verified (Carl-side done) | **Goal A (Carl, 2026-07-06)** — finalize + deploy; open R6 the day ASPSI lands the accounts. |
| **Support deliverables (rest)** | governance (privacy/backup/retention) · training finalize (decks + Survey Manual screenshots, Kidd review) | did not advance in S012 | Opportunistic (Goal B). |
| **Pretest reactivity** | freeze gate ~Jul 5; assignments + printed sheets ready | awaiting ASPSI's confirmed date | Reactive — field support jumps the queue when the date lands. |
| **E4-F2-ELESTIO** | F2 Survey + Admin off Cloudflare/Google → our own prod server (initial-setup migration) | prod server now available — un-parked | **Goal A (Carl, 2026-07-06)** — Cloudflare free tier won't hold the live user load; migrate the initial setup this week. |
| **Translations Batch 2** | Tagalog-final / Ilocano / Hiligaynon-F3F4 — labels AND (new, via R2) runtime messages | blocked on ASPSI delivery | Drop-in when delivered (both pipelines proven). |
| **F4 Option C food-roster pilot** | block-as-roster Section N rebuild running in a parallel session; on v1.2.2 (deployed 2026-07-04 with #832/#833) | live feature stream, not previously a tracked sprint item | **Goal B (Carl, 2026-07-06)** — tracked here so the board reflects it; Carl drives it in the parallel session, this sprint just accounts for it. |
| **Refactor register (rest)** | R1b `library/` (Aug, with G1/G2) · F1 hand-fmf → generator fold (post-pretest) · K1 encrypted roster (Sep) | queued by design | Not S013 work — noted so it isn't lost. |

## Committed Items — LOCKED 2026-07-06 (Mode A) · RE-ALIGNED 2026-07-06 to the Monday meeting notes

> Re-aligned to Carl's ASPSI-team-meeting outline: this week is **F2 to our prod server + Supervisor App finalization**, not the transform.py ETL headline the sprint locked at kickoff. ETL extraction + tabulation memo are deferred (Goal B), kept visible because the variable/data inconsistencies Carl flagged during the tabulation mapping feed them.

### Goal A — F2 onto our prod server + Supervisor App finalization

- [ ] **E4-F2-ELESTIO — F2 → prod-server migration** — migrate the F2 configuration/setup off Cloudflare/Google onto our own production server (the free tier won't hold the live user load once fielded); the prod server also backs the F1/F3/F4 CSWeb sync. `status::in-progress` `priority::high` `estimate::2d`
- [ ] **Supervisor App finalization (+ UAT R6)** — finalize the hub (login → menu → Bluetooth → CSWeb relay → reports → map), run the hub Designer compile, deploy, and open **UAT Round 6** the day ASPSI imports the accounts + sends real names. `status::in-progress` `priority::high` `estimate::1.5d`

### Goal B — reactive / opportunistic (must not displace Goal A)

- [ ] **Pretest reactivity** — assignments + printed sheets ready; freeze stands (data-integrity exceptions only). Field support jumps the queue the day ASPSI confirms the pretest date. `status::reactive` `priority::high`
- [ ] **Round 6 tester support** — support the Supervisor-hub testers once ASPSI sets up the accounts (the reactive tail of Supervisor App finalization). `status::blocked-on-ASPSI` `priority::medium`
- [ ] **F4 Option C pilot** — continues in the parallel session (v1.2.x); tracked for visibility. `status::in-progress (parallel)` `priority::medium`
- [ ] **ETL extraction — DEFERRED; tabulation → Ms. Myra's 3pm meeting** — `transform.py` variable extraction stays deferred (revisit after F2/hub). The 47-clarifications/3-gaps + the **variable/data inconsistencies** from the 197-table mapping go to **Ms. Myra's 3pm tabulation meeting today** (Carl shares the findings), not a written memo; the outcomes feed the eventual extraction + the data manager. `status::deferred` `priority::medium`

## Definition of Done — Sprint 013

- [ ] **F2 Survey + Admin initial setup running on our prod server** (off Cloudflare/Google), verified reachable.
- [ ] **Supervisor App finalized + deployed** — hub Designer compile clean; UAT Round 6 opened, or blocked-on-ASPSI (accounts/names) explicitly documented.
- [ ] Any pretest-date arrival handled reactively without derailing Goal A.
- [ ] Board stays honest — the sprint reflects the real week (this re-alignment is the example; keep it in sync if the week shifts again).
- [ ] **Sprint 013 retrospective filled ON TIME Fri 2026-07-10**; archived; `sprint-current.md` reset for Sprint 014.

## Daily Notes

_Auto-standup writes here daily via the `CAPI Scrum Daily Standup MD` scheduled task (08:30 MNL) + the SessionStart hook as intraday top-up._

**Mon 2026-07-06 — Sprint 013 LOCKED (Mode A).** Goal A is deliberately singular — **E10-ETL-EXTRACT (`transform.py`)** + its **tabulation decision memo** — per the S012 retro Q4 (protect the committed build item from the reactive stream). Everything else is Goal B: pretest reactivity, F4 Option C (parallel session), hub compile + R6, governance/training. **Freeze clarified (Carl):** the pretest freeze STANDS; the weekend F1/F3 → v1.0.3 + F4 → v1.2.2 deploys (#830 checkbox ascending-order = partial-save data-loss guard; #832/#833 F4 amount-entry gate) were **data-integrity exceptions**, not a lift. **Board drift trued at lock:** the S012-close board still showed F1/F3 v1.0.2 + F4 v1.0.3 + "nothing deploys ~Jul 5"; corrected to real git state (F1 v1.0.3 · F3 v1.0.3 · F4 v1.2.2 · Hub v1.0.1) across `sprint-current.md` + `product-backlog.md`. **This drift is the S012-retro-Q2 lesson biting on schedule:** the date-drift canary stayed silent (log/board dates aligned at Friday's close) while the *version/freeze content* rotted over the weekend via the parallel/loop deploys — content rot the canary can't see. **Designer-compile gate:** F1/F3/F4 effectively cleared (weekend `.csds` deploys compile the `.pen` fresh); hub still pending.

**Mon 2026-07-06 (later) — S013 RE-ALIGNED to Carl's Monday meeting notes.** Carl updated the ASPSI-team-meeting outline; his real week = **F2 initial-setup migration to our prod server + Supervisor App finalization** (+ stay pretest-ready / support Round 6), NOT the `transform.py` ETL headline this sprint locked at kickoff hours earlier. Re-locked **Goal A → F2-prod-migration + Supervisor-App-finalization**; **ETL variable extraction + tabulation memo deferred** (kept visible in Goal B). His edit also flagged **variable/data inconsistencies seen during the 197-table tabulation mapping** — noted to feed the deferred ETL work. `E4-F2-ELESTIO` un-parked (prod server now available). Linear Sprint-013 mirror patched to match (parent goal + Goal-A sub-issues added, ETL/memo sub-issues → Canceled/deferred). Same-day re-plan, cleanly recorded — the board tracking reality rather than the morning's lock.

**Mon 2026-07-06 (later²) — re-aligned again to the updated notes + a 3pm tabulation meeting.** F2 Goal-A item refined to **F2 configuration-setup migration to the prod server** (which also backs the F1/F3/F4 CSWeb sync). **Ms. Myra requested a 3pm tabulation meeting today** — Carl shares the tabulation findings there (the 47-clarifications/3-gaps + the variable/data inconsistencies from the 197-table mapping), so the deferred "tabulation memo" is now that meeting, not a written deliverable I produce. New open constraint on the board: **"questionnaire change — when?"** — the timing of the DOH questionnaire revision governs when the freeze lifts / whether the instruments change before the pretest (ASPSI/DOH call, [[project_aspsi_doh_june_comments_parked]]). Pre-test assignments clarified as pushed to the Enumerator App from the Supervisor App **offline over Bluetooth** (not printed sheets). Linear F2 sub-issue (ANA-222) + parent updated to match.

## Retrospective — Sprint 013

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_TBD 2026-07-10._

### 2. What surprised me? (process, not work — max 3 bullets)

_TBD_

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 014

_TBD_
