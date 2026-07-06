---
sprint: 013
start: 2026-07-06
end: 2026-07-10
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: Epic 10 ETL variable extraction (`transform.py`) — the last blocker to real table output · 47-partial/3-gap tabulation decision memo to ASPSI · pretest reactivity (standing freeze, data-integrity exceptions only)
created: 2026-07-03 — Mode D skeleton at the S012→S013 boundary
locked: 2026-07-06 (Mode A — Monday kickoff)
---

# Sprint 013 — Real tables: ETL variable extraction + pretest reactivity

> [!info] Where S012 left the project
> **Goal landed — first sprint where plan and value agreed.** All four perennial carries cleared by Day 2 (E0-SCRUM-SYNC finally BUILT; PSA closed out-of-lane; Goal B killed; field-ready criterion wired into `check_field_ready.py` + verified FIELD-READY). UAT R5 closed 06-29 (78/79). The freeze week became a build week: pretest assignments ready (Los Baños, 84 QNs, printed sheets), tabulation plan spec-complete + Stata-12 proven (197 SSRCS tables), fleet version-stamped v1.0.x on all 4 surfaces, DHS benchmark → data layer + R1a + R2 + R3 shipped byte-identical (freeze intact). Full record: `scrum/sprints/sprint-012.md` + `log.md`.

## Sprint Goal

> **Ship `transform.py` (Epic 10 ETL variable extraction) end-to-end against the CSWeb breakout DBs and put the 47-partial/3-gap tabulation memo in front of ASPSI — while staying pretest-reactive** (pretest freeze stands, data-integrity exceptions only). _Locked Mon 2026-07-06._

## Carry-in from Sprint 012

| ID | Item | State | S013 disposition |
|---|---|---|---|
| **E10-ETL-EXTRACT** | `transform.py` — per-instrument questionnaire-variable extraction from the CSWeb breakout DBs per codebook (checkbox split-to-dummies; F3 pay-roster + F2 extracts; lowercased-DCF instrument vars + harmonized shared dims) | scoped + **parked by Carl 2026-07-02**; codebook v0.4 + ETL skeleton + Stata-12 do-files all proven | **S013 HEADLINE (Goal A, singular)** — the last blocker to real table output. Protect it from the reactive stream (S012 retro Q4). |
| **Tabulation decision memo** | 47-partial / 3-gap (tables 1.6, 2.51, 4.2) memo → ASPSI | mapping complete in `deliverables/tabulation-plan/` | Companion to the headline — surfaces the ASPSI go/no-go set. |
| **Designer compile gate** | fresh-Designer compile of the R2-numbered builds (F1/F3/F4 + hub) | **F1/F3/F4 effectively CLEARED** — the weekend #830/#832/#833 redeploys went out via the `.csds` route, which compiles the `.pen` fresh (a compile failure hard-stops the deploy), so their message-numbered builds passed. **HUB still pending** (not redeployed; still v1.0.1). | Run the hub's compile before its next deploy; F1/F3/F4 satisfied. |
| **Supervisor hub → UAT R6** | roster built + deployed + device-verified (Carl-side done) | **blocked on ASPSI**: account import + real names + `supervisor-qa` | Open R6 artifacts (tracking issue/form/channel) the day ASPSI lands. |
| **Support deliverables (rest)** | governance (privacy/backup/retention) · training finalize (decks + Survey Manual screenshots, Kidd review) | did not advance in S012 | Opportunistic (Goal B). |
| **Pretest reactivity** | freeze gate ~Jul 5; assignments + printed sheets ready | awaiting ASPSI's confirmed date | Reactive — field support jumps the queue when the date lands. |
| **E4-F2-ELESTIO** | F2 off Cloudflare → Elestio (19-task plan) | blocked on provisioning | Parked. |
| **Translations Batch 2** | Tagalog-final / Ilocano / Hiligaynon-F3F4 — labels AND (new, via R2) runtime messages | blocked on ASPSI delivery | Drop-in when delivered (both pipelines proven). |
| **F4 Option C food-roster pilot** | block-as-roster Section N rebuild running in a parallel session; on v1.2.2 (deployed 2026-07-04 with #832/#833) | live feature stream, not previously a tracked sprint item | **Goal B (Carl, 2026-07-06)** — tracked here so the board reflects it; Carl drives it in the parallel session, this sprint just accounts for it. |
| **Refactor register (rest)** | R1b `library/` (Aug, with G1/G2) · F1 hand-fmf → generator fold (post-pretest) · K1 encrypted roster (Sep) | queued by design | Not S013 work — noted so it isn't lost. |

## Committed Items — LOCKED 2026-07-06 (Mode A)

> Anchor from the S012 retro Q4: **the headline is singular and protected.** Everything reactive/opportunistic is Goal B so the one committed build item can't starve by a thousand interrupts.

### Goal A — real tables (the last blocker) + the ASPSI decision it needs

- [ ] **E10-ETL-EXTRACT** — `transform.py`: per-instrument questionnaire-variable extraction from the CSWeb breakout DBs per codebook v0.4 (checkbox split-to-dummies; F3 pay-roster + F2 extracts; lowercased-DCF instrument vars + harmonized shared dims). Ends at real `.dta`/CSV feeding the proven Stata-12 tabulation do-files. **The single protected headline.** `status::todo` `priority::critical` `estimate::2d`
- [ ] **Tabulation decision memo → ASPSI** — the 47-partial / 3-gap set (tables 1.6, 2.51, 4.2) written up as an in-chat go/no-go for Carl to relay: what each partial needs, what each gap means at the instrument. Companion to the headline; surfaces the ASPSI questions the extraction will otherwise stall on. `status::todo` `priority::high` `estimate::0.5d`

### Goal B — reactive / opportunistic (must not displace Goal A)

- [ ] **Pretest reactivity** — freeze stands with **data-integrity exceptions only** (the weekend #830/#832/#833 deploys were exactly that). Field support (assignments/printed sheets ready) jumps the queue the day ASPSI confirms the pretest date. `status::reactive` `priority::high`
- [ ] **F4 Option C pilot** — continues in the parallel session (v1.2.x); tracked here for visibility, not a Goal-A commitment. `status::in-progress (parallel)` `priority::medium`
- [ ] **Hub Designer compile + UAT R6 open** — run the hub's fresh-Designer compile before its next deploy (F1/F3/F4 already cleared via the weekend `.csds` deploys); open the R6 artifacts the day ASPSI imports the accounts + sends real names. `status::blocked-on-ASPSI / todo` `priority::medium`
- [ ] **Support deliverables (rest)** — governance (privacy/backup/retention) + training finalize (decks + Survey Manual screenshots, Kidd review). Advance only if Goal A is on track. `status::todo` `priority::medium`

## Definition of Done — Sprint 013

- [ ] **`transform.py` runs end-to-end** against the CSWeb breakout DBs and emits per-instrument `.dta`/CSV that the Stata-12 tabulation do-files consume without hand-editing — at least one real table produced from extracted data.
- [ ] **Tabulation decision memo delivered** to Carl as an in-chat go/no-go (47 partials + 3 gaps), ready to relay to ASPSI.
- [ ] Board accuracy held: version/freeze state on the board matches git reality at close (the drift this sprint opened with does not recur).
- [ ] Any pretest-date arrival handled reactively without derailing the headline.
- [ ] **Sprint 013 retrospective filled ON TIME Fri 2026-07-10**; archived; `sprint-current.md` reset for Sprint 014.

## Daily Notes

_Auto-standup writes here daily via the `CAPI Scrum Daily Standup MD` scheduled task (08:30 MNL) + the SessionStart hook as intraday top-up._

**Mon 2026-07-06 — Sprint 013 LOCKED (Mode A).** Goal A is deliberately singular — **E10-ETL-EXTRACT (`transform.py`)** + its **tabulation decision memo** — per the S012 retro Q4 (protect the committed build item from the reactive stream). Everything else is Goal B: pretest reactivity, F4 Option C (parallel session), hub compile + R6, governance/training. **Freeze clarified (Carl):** the pretest freeze STANDS; the weekend F1/F3 → v1.0.3 + F4 → v1.2.2 deploys (#830 checkbox ascending-order = partial-save data-loss guard; #832/#833 F4 amount-entry gate) were **data-integrity exceptions**, not a lift. **Board drift trued at lock:** the S012-close board still showed F1/F3 v1.0.2 + F4 v1.0.3 + "nothing deploys ~Jul 5"; corrected to real git state (F1 v1.0.3 · F3 v1.0.3 · F4 v1.2.2 · Hub v1.0.1) across `sprint-current.md` + `product-backlog.md`. **This drift is the S012-retro-Q2 lesson biting on schedule:** the date-drift canary stayed silent (log/board dates aligned at Friday's close) while the *version/freeze content* rotted over the weekend via the parallel/loop deploys — content rot the canary can't see. **Designer-compile gate:** F1/F3/F4 effectively cleared (weekend `.csds` deploys compile the `.pen` fresh); hub still pending.

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
