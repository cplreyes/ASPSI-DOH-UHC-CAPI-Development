---
sprint: 013
start: 2026-07-06
end: 2026-07-10
status: planning
sprint_length: 1 week (5 working days)
deliverable_anchor: Epic 10 ETL variable extraction (`transform.py`) — the last blocker to real table output · 47-partial/3-gap tabulation decision memo to ASPSI · pretest reactivity (freeze gate ~Jul 5; fresh-Designer compile of the R2-numbered builds before ANY deploy)
created: 2026-07-03 — Mode D skeleton at the S012→S013 boundary
---

# Sprint 013 — Real tables: ETL variable extraction + pretest reactivity

> [!info] Where S012 left the project
> **Goal landed — first sprint where plan and value agreed.** All four perennial carries cleared by Day 2 (E0-SCRUM-SYNC finally BUILT; PSA closed out-of-lane; Goal B killed; field-ready criterion wired into `check_field_ready.py` + verified FIELD-READY). UAT R5 closed 06-29 (78/79). The freeze week became a build week: pretest assignments ready (Los Baños, 84 QNs, printed sheets), tabulation plan spec-complete + Stata-12 proven (197 SSRCS tables), fleet version-stamped v1.0.x on all 4 surfaces, DHS benchmark → data layer + R1a + R2 + R3 shipped byte-identical (freeze intact). Full record: `scrum/sprints/sprint-012.md` + `log.md`.

## Sprint Goal

> **Ship `transform.py` (Epic 10 ETL variable extraction) end-to-end against the CSWeb breakout DBs and put the 47-partial/3-gap tabulation memo in front of ASPSI — while staying pretest-reactive** (freeze gate ~Jul 5; Designer compile of the numbered builds before any deploy). _Draft until lock Mon 2026-07-06._

## Carry-in from Sprint 012

| ID | Item | State | S013 disposition |
|---|---|---|---|
| **E10-ETL-EXTRACT** | `transform.py` — per-instrument questionnaire-variable extraction from the CSWeb breakout DBs per codebook (checkbox split-to-dummies; F3 pay-roster + F2 extracts; lowercased-DCF instrument vars + harmonized shared dims) | scoped + **parked by Carl 2026-07-02**; codebook v0.4 + ETL skeleton + Stata-12 do-files all proven | **S013 HEADLINE (Goal A, singular)** — the last blocker to real table output. Protect it from the reactive stream (S012 retro Q4). |
| **Tabulation decision memo** | 47-partial / 3-gap (tables 1.6, 2.51, 4.2) memo → ASPSI | mapping complete in `deliverables/tabulation-plan/` | Companion to the headline — surfaces the ASPSI go/no-go set. |
| **Designer compile gate** | fresh-Designer compile of the R2-numbered builds (F1/F3/F4 + hub) | pending; skipped 07-03 (a live Designer held F4 — do NOT save from that stale session) | Run when Designer is free; **mandatory before ANY next deploy**. |
| **Supervisor hub → UAT R6** | roster built + deployed + device-verified (Carl-side done) | **blocked on ASPSI**: account import + real names + `supervisor-qa` | Open R6 artifacts (tracking issue/form/channel) the day ASPSI lands. |
| **Support deliverables (rest)** | governance (privacy/backup/retention) · training finalize (decks + Survey Manual screenshots, Kidd review) | did not advance in S012 | Opportunistic (Goal B). |
| **Pretest reactivity** | freeze gate ~Jul 5; assignments + printed sheets ready | awaiting ASPSI's confirmed date | Reactive — field support jumps the queue when the date lands. |
| **E4-F2-ELESTIO** | F2 off Cloudflare → Elestio (19-task plan) | blocked on provisioning | Parked. |
| **Translations Batch 2** | Tagalog-final / Ilocano / Hiligaynon-F3F4 — labels AND (new, via R2) runtime messages | blocked on ASPSI delivery | Drop-in when delivered (both pipelines proven). |
| **Refactor register (rest)** | R1b `library/` (Aug, with G1/G2) · F1 hand-fmf → generator fold (post-pretest) · K1 encrypted roster (Sep) | queued by design | Not S013 work — noted so it isn't lost. |

## Committed Items — locks Mon 2026-07-06 (Mode A)

_TBD at lock. Candidates — Goal A: **E10-ETL-EXTRACT** (headline) + the tabulation decision memo. Goal B (reactive/opportunistic): Designer compile gate · hub R6 opening on ASPSI's land · governance strand · pretest field support if the date drops._

## Definition of Done — Sprint 013

_TBD at lock._

## Daily Notes

_Auto-standup writes here daily via the `CAPI Scrum Daily Standup MD` scheduled task (08:30 MNL) + the SessionStart hook as intraday top-up._

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
