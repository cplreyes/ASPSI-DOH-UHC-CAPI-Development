---
sprint: 008
start: 2026-06-01
end: 2026-06-05
status: closed
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — F2 PWA 7-language translation pipeline (PSA 2026-06-12 critical path) ✅ DONE 2026-06-01 · Goal B — v1.3.x release tail + #294 prod AS push (clasp) · Goal C — F1 FMF Designer pass (opportunistic, four-sprint carry)
closed: 2026-06-07 — Mode D archive at the S008→S009 boundary (sprint period ended Fri 2026-06-05; retro deferred to Sun because the standup automation didn't fire all sprint and there was no in-sprint trigger)
revised: 2026-06-02 — Goal A delivered (all 7 PH languages wired, PRs #351+#353 merged); resolved a stash-pop conflict that had reintroduced Sprint 006 content
---

# Sprint 008 — F2 7-language translation pipeline · v1.3.x release tail + #294 · F1 Designer pass

> [!success] Goal A landed Day 1–2 (the PSA critical path)
> **E2-F2-TRANS-001 is DONE** — all 7 PSA-target languages wired into the F2 PWA and merged
> to `main` (PRs **#351** infra + Tagalog, **#353** the 6 dialects). Survey-content coverage
> 74–95% per language; untranslated strings fall back to English. CF Pages auto-deploys.
> Delivered ahead of the Fri 2026-06-05 staging-ready target.

## Carry-in from Sprint 007

Goal A (R3 close-out questionnaire-design half) shipped in S007. Goals B and C did not start. S008 carry-in was dominated by the translation pipeline (now delivered), the v1.3.x release-tag tail, and the #294 deploy-gap follow-up.

| ID | Item | State | Notes |
|---|---|---|---|
| **E2-F2-TRANS-001** | F2 PWA 7-language translation pipeline | ✅ **DONE 2026-06-01** | All 7 PH languages wired from ASPSI's `Translated Tools_May12` docs (PRs #351 + #353). Coverage: fil 77 · ceb 77 · bis 81 · ilo 82 · hil 74 · war 83 · bcl 95 %. Gaps + chrome-translation follow-ups itemized in `deliverables/F2/PWA/TRANSLATION-STATUS-2026-06-01.md` (ASPSI lane). |
| **E3-F1-001** | F1 FMF Section A Designer pass | not started (four-sprint carry) | Designer-time-gated. Opportunistic in S008; do not block on it. **Carries to S009 (now five-sprint carry).** |
| **E6-PWA-007a-tag** | v1.3.x formal release tag + CHANGELOG | ✅ **superseded** | The release workflow shipped **v2.1.0** (PRs #352/#350) — CHANGELOG synced + version bumped. The v1.3.x-era tail is closed by the v2.1.0 release; no separate v1.3.x tag needed. |
| **#294** | Prod Apps Script push — `admin_users_change_password` reaches deployed Web App | Carl-gated; GUI paste failed repeatedly | **Folded into the clasp item. Not started S008 — carries to S009.** Signed-probe diagnostic staged at `$CLAUDE_JOB_DIR/probe-as.mjs` (not executed). |
| **3 Myra clarifications** | Q9 0+0 (#305-3a) / Q36 wording (#307-5b) / Q38 wording (#309-ii) | `status:blocked` awaiting team | No responses landed in-sprint. Carries to S009 — fold into a PR if any respond. |
| **E3-F3-001, E3-F4-001** | F3/F4 FMF Designer passes | not committed S006/S007 | Carry — not committed S008. F1 (Goal C) sequences first. |
| **E4-CSWeb-001 / -002** | VPS provision + CSWeb install | ✅ **DONE 2026-06-02** | CSWeb 8.0.1 **LIVE** on Elestio `aspsi-csweb-prod` (Vultr SG) — admin login + API `/token` verified at `https://aspsi-csweb-prod-u73907.vm.elestio.app/csweb/`. Drove the deploy over SSH (fixed dead `buster`→`bookworm` base; `log_bin_trust_function_creators` for MySQL 8.4; DB host=`database`). Deviations + 1-line domain repoint in `deliverables/CSWeb/Elestio-CSWeb-Deploy-Guide.md`. **Next:** ASPSI points `csweb.asiansocial.org` → repoint `API_URL`; send Juvy 1st Elestio invoice. |
| **E4-CSWeb-003 / -004 / -005** | per-survey app upload · user/role matrix · tablet sync | server live — config-ready | Now doable in the CSWeb admin UI. -005 (tablet sync → `…/csweb/api`) gates **E3-F1-088**. Open: confirm CSPro Designer = 8.0.x. **Carries to S009.** |
| **E3-F1-088** | F1 Phase-1 tablet sync-verify | blocked behind E4-CSWeb-005 | Carry — chain dependency. |
| **#336** | Open PR — R3 #314 diagnosis (2026-05-19) | open since 5/19 | **Not dispositioned S008 — carries to S009.** |
| **E0-AUTO-STANDUP** | Verify SessionStart hook fires daily | S007 retro Q2 surfaced silent drop 5/27–5/29 | **Not done S008 — and the hook tripped AGAIN (no standups fired Jun 1–5; last written 2026-05-26). Third sprint running. Carries to S009 — escalate.** |

## Hard external constraint entering Sprint 008

- **PSA clearance gate — 2026-06-12 (last day of Sprint 009).** PSA will not clear the survey without the CAPI app + **7 distinct translated versions** bundled (Bisaya ≠ Cebuano). **F2 share met early:** the F2 PWA now serves all 7 languages on `main` (Goal A done 2026-06-01). The CSPro F1/F3/F4 multi-language layers remain for S009 (gated on the Designer passes).

## Sprint Goal

> **Deliver the F2 PWA 7-language translation pipeline staging-ready** (E2-F2-TRANS-001 — PSA critical path) — **✅ DONE 2026-06-01, exceeded: full survey content for all 7 languages merged to `main`, not just staging-ready.** Then **close the #294 prod AS-deploy gap** via `clasp` so the AS push is repeatable instead of a GUI paste session, and **opportunistically land the F1 FMF Section A Designer pass** (four-sprint carry — do not block on it).

Deliverable anchors:

- **Goal A — F2 PWA 7-language translation pipeline (E2-F2-TRANS-001).** ✅ **DONE.** All 7 PSA-target languages (Tagalog, Cebuano, Bisaya, Hiligaynon, Waray, Ilocano, Bicolano) extracted faithfully from ASPSI's v2.1/v2.1.1 questionnaire docs and wired into the F2 PWA i18n; switcher offers all 8 (English + 7). PRs #351 + #353 merged. Coverage 74–95%; English fallback for untranslated strings; choice values/Zod enum never localized (data contract intact).
- **Goal B — Close the #294 prod AS-deploy gap (via clasp).** ⬜ **Not started — carries to S009.** Wire `clasp` for the F2 PWA backend so v2.0.1 admin handlers reach the deployed prod Web App and the deploy-gap class is closed. *(The v1.3.x release-tail half is superseded — the v2.1.0 release already synced CHANGELOG + version.)*
- **Goal C — F1 FMF Section A Designer pass (E3-F1-001 carry).** ⬜ **Not started.** Four-sprint carry. Gated only on Carl's CSPro Designer time. Opportunistic — did not block.

## Committed Items — final state

### Goal A — F2 PWA 7-language translation pipeline

- [x] **E2-F2-TRANS-001** Wire the 7 translated languages into the F2 PWA from ASPSI's source docs. **DONE 2026-06-01.** Built a runtime translation overlay (`spec/translations/{locale}.json` keyed by exact English string + composable generator pass `apply-translations.ts`; parser stays pure-English). Extracted all 7 instruments from the `Translated Tools_May12` set (pandoc; Bisaya legacy `.doc` via LibreOffice→pandoc). `LOCALE_META` all-7-ready; switcher renders 8 buttons. 0 orphan keys in any language. Verified cold: eslint · `tsc -b` · `vite build` · 456 tests. **PRs #351 (infra + Tagalog) + #353 (6 dialects), both merged to `main`.** `status::done` `priority::critical` `estimate::8h`

> **Residual = ASPSI content lane (not Carl's to author), tracked in `TRANSLATION-STATUS-2026-06-01.md`:** (1) per-language gaps — role/specialty/section-title strings the docs left English; (2) app-chrome translation for ilo/hil/war/bcl (~45 UI strings each — currently English-fallback); (3) R3-drift strings (Q47/Q110 "None", Q35 partial-date) not in any delivered doc. Each wires in minutes once supplied.

### Goal B — Close the #294 prod AS-deploy gap (via clasp)

- [ ] **E4-PWA-014-clasp** Wire `clasp` for the F2 PWA backend. **Not started — carries to S009.** `status::carry → S009` `priority::high` `estimate::2h`
- [ ] **#294** Push v2.0.1 admin handlers to the prod `F2-PWA-Backend` Web App via clasp; retest the 5 downstream issues (#317 / #319 / #325 / #326 / #330). **Not started — carries to S009.** `status::carry → S009` `priority::high` `estimate::1h`

### Goal C — F1 FMF Designer pass (opportunistic)

- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer. **Not started — Designer time never opened. Now a five-sprint carry (S005 → S006 → S007 → S008 → S009).** `status::carry → S009` `priority::medium` `estimate::4h`

### Process — close S007 retro Q2 finding

- [ ] **E0-AUTO-STANDUP** Verify the SessionStart hook fires daily; root-cause the silent drop; add a self-check probe + log. **Not done — and the hook tripped again (no standups Jun 1–5). Carries to S009 — escalate.** `status::carry → S009` `priority::high (was medium — escalated)` `estimate::1h`

### Bonus delivered off-plan (not committed S008)

- [x] **E4-CSWeb-001 / -002** CSWeb 8.0.1 stood up + installed + verified LIVE on Elestio (`aspsi-csweb-prod`, Vultr SG), 2026-06-02. Drove the full deploy over SSH. Wasn't a committed S008 goal — unblocked when ASPSI's Elestio card landed mid-sprint, and consumed most of Day 2. `status::done`

## Sprint Backlog Sizing — committed vs actual

| Class | Items | Estimate | Actual |
|---|---|---|---|
| **Goal A** | E2-F2-TRANS-001 | ~8h | **done** (~10h incl. the 7-doc extraction + 3 CI round-trips on #351) |
| **Goal B** | E4-PWA-014-clasp, #294 | ~3h | 0h (not started — gated on Elestio/clasp auth) |
| **Goal C** (opportunistic) | E3-F1-001 | ~4h | 0h (Designer-time-gated) |
| **Process** | E0-AUTO-STANDUP | ~1h | 0h (not started; hook tripped again) |
| **Off-plan (bonus)** | E4-CSWeb-001/-002 | — | ~6h (unplanned CSWeb deploy, Day 2) |
| **Buffer / overhead** | sprint ceremonies + comms + verify | ~2h | ~2h |
| **Committed total** | | **~16h** | **~10h delivered (the headline goal) + ~6h off-plan CSWeb** |

> **Sizing call:** S007 closed 1 of 3 goals; per S007 retro Q4, S008 sequenced Goal A first and singularly — and it landed Day 1–2, the PSA critical path cleared early. Goal B (clasp/#294) was the next priority but never started; freed capacity went to the unplanned CSWeb deploy instead. Goal C stayed opportunistic and didn't open.

## Definition of Done — Sprint 008 — final

- [x] **E2-F2-TRANS-001** closed: F2 PWA serves all 7 PSA-target languages on `main`; switcher verified per locale; coverage + gap-list captured in `TRANSLATION-STATUS-2026-06-01.md`. *(Exceeded "staging-ready" — merged to prod.)*
- [ ] **E4-PWA-014-clasp** — not started; carries to S009.
- [ ] **#294** — not started; carries to S009.
- [ ] **E0-AUTO-STANDUP** — not done; hook tripped again Jun 1–5; carries to S009 escalated.
- [ ] **E3-F1-001** — opportunistic; Designer time never opened; carries to S009 (five-sprint carry).
- [x] **Sprint 008 retrospective** filled 2026-06-07; archived to `scrum/sprints/sprint-008.md`; `sprint-current.md` reset for Sprint 009.

## S008 carries forward to S009

- **Goal B — clasp + #294** (E4-PWA-014-clasp, #294) — now the headline candidate for S009
- **PSA submission + per-language tester verify** (one HCW persona per language; T-7 → T-0, gate 2026-06-12)
- **CSPro F1/F3/F4 multi-language layers** + **F2 app-chrome translation** for ilo/hil/war/bcl + per-language gap fills (pending ASPSI strings)
- **E3-F3-001, E3-F4-001** (F3/F4 FMF Designer passes) and **E3-F1-001** (F1 — five-sprint carry)
- **E4-CSWeb-003 / -004 / -005** (CSWeb operational config — server LIVE, config-ready in admin UI). Also: ASPSI points `csweb.asiansocial.org` → 1-line `API_URL` repoint; send Juvy the first Elestio invoice
- **E3-F1-088** (F1 Phase-1 tablet sync-verify; blocked behind E4-CSWeb-005)
- **#336** PR disposition
- **E0-AUTO-STANDUP** (escalated — third sprint running)
- **3 Myra clarifications** (Q9 0+0 / Q36 wording / Q38 wording — `status:blocked`)

## Daily Notes

**2026-06-01 (Mon, Day 1) — Mode D close of S007 + Mode A draft of S008 + Goal A delivered.** S007 archived (`scrum/sprints/sprint-007.md`). S008 goal locked on the PSA critical path. Then Goal A landed in the same window: built the multi-language i18n infra + Tagalog (PR #351, 3 CI round-trips — `EnBundle` literal-lock, stray `partialDate.hint`, BOM-in-regex, all fixed). CF Pages auto-deploys both.

**2026-06-02 (Tue, Day 2) — Goal A completed across all 7 languages.** Carl's `Translated Tools_May12` Downloads zip (179 MB) held all 7 dialect questionnaires — including the 3 never reachable via Drive API (Bicolano/Hiligaynon/Waray) and the 3 that enumerated empty (Cebuano/Bisaya/Ilocano). Extracted + converted + aligned + wired all 6 remaining dialects (PR #353, merged `105d9f9`). Coverage 74–95%, 0 orphan keys. Rebased onto the v2.1.0 release (preserved package.json/CHANGELOG). **PSA F2-share deliverable met 10 days early.** Resolved a stash-pop conflict that had reintroduced S006 content into this file.

**2026-06-02 (Tue, Day 2) — CSWeb server stood up + installed (E4-CSWeb-001/-002 DONE; not a committed S008 goal, but unblocked when ASPSI's Elestio card landed).** Drove the full Elestio deploy over SSH (key-based): brought up the managed LAMP stack — fixing Elestio's dead `php:8.1-apache-buster` base (Debian 10 EOL → apt 404) by bumping `.env` to `bookworm` and rebuilding; created least-priv DB `csweb_uhc_y2` + `csweb_user`@`'%'`; deployed CSWeb 8.0.1 into `lamp/www/csweb`; completed the setup wizard headlessly (worked around the MySQL-8.4 `CREATE TRIGGER`/error-1419 priv block via `SET PERSIST log_bin_trust_function_creators=1`). **Live + verified** (admin login + OAuth `/token`) at the elestio.app hostname; custom domain `csweb.asiansocial.org` + `API_URL` repoint pending ASPSI DNS. Real procedure + 4 deviations captured in `deliverables/CSWeb/Elestio-CSWeb-Deploy-Guide.md` (status → deployed).

**2026-06-03 → 2026-06-05 (Wed–Fri, Day 3–5) — No standup files written; no committed-goal commit signal.** The SessionStart standup hook did not fire (last standup written 2026-05-26 — none for the entire S008 window). Goal B (clasp/#294) and Goal C (F1 Designer) did not start. Same open-loop pattern S007 retro Q2 flagged.

**Inter-sprint, 2026-06-05 (Fri) → 2026-06-07 (Sun) — Mode D close-out.** Sprint period ended Fri 2026-06-05; retro deferred to Sun at the S008→S009 boundary because the standup automation didn't fire all sprint and there was no in-sprint trigger to write Q1–Q4. The one committed headline goal (Goal A) was already done Day 1–2; Goals B/C and the process item carry to S009.

## Retrospective — Sprint 008

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

**Yes — the headline goal.** The sprint goal was sequenced singularly on Goal A (the PSA critical path) per the S007 retro Q4 prescription, and it landed Day 1–2, exceeding "staging-ready" (full 7-language content merged to `main`, not just staging). Overall **partial** if scored across all anchors: Goals B (clasp/#294) and C (F1 Designer) and the process item (E0-AUTO-STANDUP) didn't start. But on the goal as framed — and on the deadline that mattered — it was a clean, early win.

### 2. What surprised me? (process, not work — max 3 bullets)

- **The S007 Q4 prescription actually worked.** Committing the PSA critical path *first and singularly* meant it cleared Day 1–2 instead of slipping to the wire — the first time in three sprints a headline goal closed early rather than carrying. The single-goal focus discipline is validated.
- **Freed capacity drifted to unplanned work, not the next committed goal.** Goal A finishing early should have pulled Goal B (clasp/#294) forward. Instead the slack went to the unplanned CSWeb deploy (genuinely valuable — and it was unblocked mid-sprint — but off-plan), and Goal B still never started. Early wins aren't being banked into the next commitment.
- **The auto-standup hook didn't fire at all — and is now a three-sprint-running silent failure.** S006 flagged it indirectly, S007 tripped on it (Wed–Fri drop), and S008 had *zero* standups (last written 2026-05-26). The E0-AUTO-STANDUP item meant to fix it was carried but never worked. The sprint ran fully open-loop again.

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 009

**Bank the early win — when the headline goal lands early, immediately pull the next committed goal forward (don't let slack drift to opportunistic/unplanned work).** S008 cleared Goal A by Day 2 but Goal B (clasp/#294) never started; S009 should make clasp/#294 the headline and, if it lands early, pull the CSPro F1/F3/F4 multi-language layers (the remaining PSA-gate dependency) next — in that priority order. **And finally fix the standup hook (E0-AUTO-STANDUP) as a committed, not opportunistic, item** — three sprints of open-loop is enough; a one-hour root-cause is overdue and now blocks reliable mid-sprint recalibration. PSA gate is 2026-06-12 (last day of S009) — S009 owns submission + per-language tester verify.
