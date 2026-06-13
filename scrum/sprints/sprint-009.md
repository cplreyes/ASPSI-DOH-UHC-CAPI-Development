---
sprint: 009
start: 2026-06-08
end: 2026-06-12
status: closed
closed: 2026-06-13 — Mode D close at the S009→S010 boundary (retro filled Sat AM; sprint period ended Fri 2026-06-12)
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — PSA bundle / CSPro F1·F3·F4 multi-language CSEntry+Designer verification (Phase 3) + bundle assembly for the 2026-06-12 PSA gate · Goal B (opportunistic) — clasp + #294 deploy-gap close. PSA gate falls on the LAST day of this sprint.
created: 2026-06-07 — Mode D skeleton at the S008→S009 boundary
locked: 2026-06-07 — Mode A planning locked early (PSA gate is Fri 6/12). Headline = PSA bundle / CSPro multi-language verify; clasp/#294 demoted to opportunistic second goal. Gate posture = verify+bundle the ASPSI-delivered languages, gap-checklist fil/ilo/(hil-F3F4) for ASPSI.
---

# Sprint 009 — PSA bundle / CSPro F1·F3·F4 multi-language verify (+ opportunistic clasp/#294)

> [!warning] PSA clearance gate lands on the last day of this sprint — 2026-06-12
> PSA will not clear the survey without the CAPI app + **distinct translated versions** bundled (Bisaya ≠ Cebuano). **F2 PWA share met** (all 7 languages on `main`, S008). **CSPro F1/F3/F4 multi-language is BUILT** (dictionaries multi-language, generator-first, QC'd 2026-06-03) — what remains is **Phase 3: CSPro Designer + CSEntry verification on Windows** (Carl-gated). **Content block:** fil (Tagalog) + ilo (Ilocano) for F1/F3/F4, and hil for F3/F4, have **no ASPSI translation source** — they stay English-fallback and are tracked as a go/no-go gap. Source of truth: `deliverables/CSPro/TRANSLATION-STATUS-2026-06-03.md`.

## Carry-in from Sprint 008

S008 closed 1 committed goal (Goal A — the PSA F2-share, the critical path; landed Day 1–2 and exceeded). Goal B (clasp/#294), Goal C (F1 Designer), and the process item (E0-AUTO-STANDUP) did not start. CSWeb went LIVE off-plan (E4-CSWeb-001/-002). Full S008 record + retro: `scrum/sprints/sprint-008.md`.

| ID | Item | State | S009 disposition |
|---|---|---|---|
| **E3-F1-001 / -F3-001 / -F4-001** | FMF Designer + CSEntry multi-language verify (Phase 3) | carry — **now Goal A** | **PSA critical path & headline.** The build is done; this is the Designer/CSEntry verification of the already-multi-language `.dcf`/`.fmf`. Finally forces the long-carried Designer time (F1 = five-sprint carry S005→S009). Committed below. |
| **PSA bundle assembly** | Package CAPI app (F1/F3/F4 + F2 PWA) + per-language versions + coverage/gap note for the gate | new — **Goal A** | Committed below as E0-PSA-001. |
| **ASPSI translation gap** | fil/ilo (F1/F3/F4) + hil (F3/F4) — no source | `status:blocked` | Go/no-go for the gate; escalate (asks sent 2026-06-01 + 2026-06-03). Committed below as E0-PSA-002. |
| **E4-PWA-014-clasp** | Wire `clasp` for the F2 PWA backend (close the deploy-gap class) | carry from S008 | **Demoted to opportunistic Goal B** — real debt but NOT PSA-gating; do only if the gate work lands early. `priority::high` `estimate::2h` |
| **#294** | Push v2.0.1 admin handlers to prod Web App via clasp; retest #317/#319/#325/#326/#330 | carry from S008 | Follows E4-PWA-014-clasp (Goal B, opportunistic). `priority::high` `estimate::1h` |
| **E0-AUTO-STANDUP** | Verify/fix the SessionStart standup hook | ✅ **RESOLVED 2026-06-07** | Root cause: the daily `.md` rode only on the project-scoped SessionStart hook (fires only when Claude is launched in the ASPSI dir), and the time-based scheduled task had been DISABLED since 4/15. On days Carl launched elsewhere → silent drop (5/27 onward). Fix: new launch-independent Windows task **`CAPI Scrum Daily Standup MD`** (daily 08:30, `StartWhenAvailable`) runs `daily-standup-md.ps1` → `generate_standup.py` + `generate_retro.py` + a self-check probe that logs `PROBE-MISSING`/`PROBE-STALE`. Hook kept as intraday top-up. Tested: wrote `2026-06-07.md`, probe `ok`. `status::done` |
| **E4-CSWeb-003 / -004 / -005** | per-survey app upload · user/role matrix · tablet sync | server LIVE — config-ready | Doable in the admin UI. -005 gates E3-F1-088. Also: ASPSI points `csweb.asiansocial.org` → 1-line `API_URL` repoint; **send Juvy the first Elestio invoice.** |
| **E3-F1-088** | F1 Phase-1 tablet sync-verify | blocked behind E4-CSWeb-005 | Chain dependency. |
| **#336** | Open PR — R3 #314 diagnosis (open since 5/19) | carry | Disposition this sprint: merge, close-with-rationale, or carry. |
| **3 Myra clarifications** | Q9 0+0 (#305-3a) / Q36 wording (#307-5b) / Q38 wording (#309-ii) | `status:blocked` | Opportunistic — fold into a PR if any respond. |

## Hard external constraint

- **PSA clearance gate — 2026-06-12 (last day of Sprint 009).** F2 share met; CSPro F1/F3/F4 multi-language layers + per-language tester verify remain. This sprint owns submission readiness.

## Sprint Goal — LOCKED 2026-06-07

> **Get the CAPI survey PSA-bundle-ready for the 2026-06-12 gate.** Verify the already-built CSPro F1/F3/F4 **multi-language** instruments in **CSPro Designer + CSEntry** (Phase 3 — load with declared languages, forms render translated labels + language selection works, CSEntry toggles each ASPSI-delivered language with skip logic intact, English base signed off), then **assemble the PSA bundle** (F1/F3/F4 CAPI app + the live F2 PWA + per-language coverage/gap note) and hand it to ASPSI for the gate. **Verify-and-bundle the languages ASPSI has delivered**; document fil/ilo (F1/F3/F4) + hil (F3/F4) as a **go/no-go gap** and escalate — those have no source and are not Carl's to author. **Opportunistically** close the `clasp`/#294 deploy-gap (Goal B) only if the gate work lands early — do not let it pull focus.

Deliverable anchors:

- **Goal A — PSA bundle / CSPro multi-language verify (the gate).** Phase 3 CSEntry+Designer verification of F1/F3/F4 (closes the long-carried E3-F1-001/-F3-001/-F4-001 as *language-verify*-shaped passes) + PSA bundle assembly + the ASPSI translation-gap go/no-go. This is the only hard external deadline this sprint and it is now Carl-controllable (build done; only verify + package remain).
- **Goal B — clasp + #294 deploy-gap close (OPPORTUNISTIC).** Real tooling debt from S007/S008, but **not PSA-gating**. Per S008 retro Q4, bank the headline win into this *if* Goal A lands early — otherwise it carries to S010. Do not co-prioritize against the gate.

> **Designer-time risk (named up front):** Phase 3 is hands-on Carl time in CSPro Designer/CSEntry on Windows — the exact constraint that carried E3-F1-001 for five sprints. The Friday gate is what finally forces it. If Designer time doesn't open, the gate slips — there is no AI-side substitute for the CSEntry click-through. Mitigation: sequence F1 first (smallest, most-prepped), then F3, then F4; bundle incrementally so a partial verify still yields a partial submittable bundle.

## Committed Items

### Goal A — PSA bundle / CSPro multi-language verify (the gate)

- [ ] **E3-F1-001** F1 Facility Head — CSPro Designer + CSEntry multi-language verify (EN + Cebuano/Bisaya/Hiligaynon/Waray/Bikol). Open `.dcf` (loads with declared languages), `.fmf` renders translated labels + language selection works (sync `.qsf` `languages:` if Designer flags mismatch), CSEntry toggles each language with skip logic intact, English base signed off. **Closes the five-sprint carry.** `status::in-progress` `priority::critical` `estimate::4h`
- [ ] **E3-F3-001** F3 Patient — same Phase 3 verify (EN + Cebuano/Bisaya/Waray/Bikol). Eyeball-check the lower-coverage maps (F3 Bisaya 52%, Bicolano) on a question↔translation sample per the QC caveat. `status::in-progress` `priority::critical` `estimate::4h`
- [ ] **E3-F4-001** F4 Household — same Phase 3 verify (EN + Cebuano/Bisaya/Waray/Bikol). `status::in-progress` `priority::critical` `estimate::4h`
- [ ] **E0-PSA-001** Assemble the PSA bundle: F1/F3/F4 CAPI app artifacts (`.pff`/`.dcf`/`.fmf`/`.apc`) + the live F2 PWA reference + a per-language coverage/gap note (from `TRANSLATION-STATUS-2026-06-03.md` + the F2 status doc). Hand to ASPSI (Kidd/Myra) for the 6/12 gate as an in-chat go/no-go checklist. `status::todo` `priority::critical` `estimate::3h`
- [ ] **E0-PSA-002** ASPSI translation-gap go/no-go: document fil/ilo (F1/F3/F4) + hil (F3/F4) as the missing-source gap (English-fallback in the bundle), tie to the 2026-06-01 + 2026-06-03 asks, and surface the gate decision (submit best-effort vs hold) for ASPSI. `status::blocked` `priority::high` `estimate::1h`

### Goal B — clasp + #294 deploy-gap close (OPPORTUNISTIC — only if Goal A lands early)

- [ ] **E4-PWA-014-clasp** Wire `clasp` for the F2 PWA backend: `.clasp.json` + clean push dir from `dist/Code.gs` + `appsscript.json`, smoke-test `clasp push`, runbook. `status::todo` `priority::high` `estimate::2h`
- [ ] **#294** Push v2.0.1 admin handlers to the prod Web App via clasp; verify `admin_users_change_password` answers; retest #317/#319/#325/#326/#330 and close what resolves. `status::todo` `priority::high` `estimate::1h`

> **Opportunistic / fold-in if they surface (do not block the gate):** ASPSI points `csweb.asiansocial.org` → 1-line `API_URL` repoint + send Juvy the first Elestio invoice (E4-CSWeb side); `#336` PR disposition; the 3 Myra clarifications (#305-3a / #307-5b / #309-ii) if responses land.

## Sprint Backlog Sizing

| Class | Items | Estimate | Notes |
|---|---|---|---|
| **Goal A — verify** | E3-F1-001, E3-F3-001, E3-F4-001 | ~12h | Hands-on CSEntry/Designer time (Carl, Windows). The big rock + the standing risk. |
| **Goal A — bundle** | E0-PSA-001, E0-PSA-002 | ~4h | Assembly + the ASPSI go/no-go (E0-PSA-002 partly blocked). |
| **Goal B (opportunistic)** | E4-PWA-014-clasp, #294 | ~3h | Only if Goal A lands early; else carries to S010. |
| **Buffer / overhead** | ceremonies + comms + verify | ~2h | — |
| **Committed total (Goal A)** | | **~16h** | A full, focused 1-week load on its own — Goal B is genuinely stretch. |

> **Sizing call:** Goal A alone (~16h) fills the sprint at the solo+AI 1-week cadence. Per the S008 retro, the headline is committed **singularly**; Goal B is explicitly opportunistic so an early Goal-A finish has somewhere disciplined to go rather than drifting. The Designer-time gate is the live risk, not the estimate.

## Definition of Done — Sprint 009

- [x] **E3-F1-001 / -F3-001 / -F4-001** closed *(verify-shaped, EXCEEDED)*: every `.dcf` loads in Designer with its declared languages and **compiles clean** — re-proven repeatedly through the week's 9 publish cycles (the whole pipeline is now agent-driven: pywinauto fresh-Designer launch → compile → publish → `auto_deploy.py`); `.fmf` labels render; **and the language CONTENT gap itself closed beyond plan** — Tagalog extracted from ASPSI's v2.1.x docs, QC'd, wired, and DEPLOYED Day 5 (F1 now 7 languages, F3/F4 6). CSEntry per-language toggling is live on CSWeb + announced to testers; on-device toggle confirmation rides UAT R4 (closes Mon 6/15 AM). **The five-sprint Designer-time carry is dead — killed by automation, not by calendar.**
- [ ] **E0-PSA-001** — NOT closed as framed: no formal bundle/checklist handed to ASPSI on 6/12; the gate-day capacity went to UAT R4 + the patch train (which produced a *better-than-bundle* live artifact: all 3 instruments deployed multi-language on CSWeb). PSA gate outcome **pending/unrecorded** — carries to S010 as a confirm-or-assemble item.
- [x] **E0-PSA-002** closed *(overtaken by delivery)*: the gap note is superseded — ASPSI delivered Batch 1 (bcl/bis/ceb/war v3.2, 6/2) and the Tagalog drafts are wired; remaining gap = **ilo (all) + hil (F3/F4) + checked-final Tagalog (Batch 2 pending ASPSI's translation check)**. Recorded in `TRANSLATION-STATUS` + memory; Flu/Fever defect in ASPSI's F4 Filipino doc found + corrected our side, relay to Kidd queued.
- [ ] **Goal B (clasp/#294)** — not worked this sprint (clasp CI itself landed via #348 on 6/1, pre-sprint); #294 retests unverified. Carries to S010 as a verify-and-close, not a build.
- [x] **Sprint 009 retrospective** filled Sat 2026-06-13 (Mode D close at the boundary); archived to `scrum/sprints/sprint-009.md`; `sprint-current.md` reset for Sprint 010.

## Daily Notes

_Auto-standup writes here daily via the `CAPI Scrum Daily Standup MD` scheduled task (08:30 MNL, launch-independent) + the SessionStart hook as intraday top-up. Fixed 2026-06-07 (E0-AUTO-STANDUP)._

**2026-06-07 (Sun) — Goal A started: CSPro multi-language verify pre-checks GREEN.** E3-F1-001/-F3-001/-F4-001 → `in-progress`. AI-side gates both clean before the GUI session: `preflight_validate.py` **ALL CLEAN** (F1 129 / F3 60 / F4 125 PROCs resolve; no setvalueset/arity/ref issues), and a label-parity pass confirms **every** label array carries all declared languages (F1 2463 EN+5, F3 2831 EN+4, F4 2232 EN+4; 0 off-parity). CSPro **8.0** confirmed installed. fil/ilo (+hil F3/F4) absent by design (ASPSI gap → E0-PSA-002). Staged the CSEntry session worksheet at `deliverables/CSPro/2026-06-07-multilang-verify-worksheet.md`. **Next (Carl, GUI):** Designer compile per instrument (F1 Id-block re-sync + 4 PSGC dicts first) → CSEntry toggle each declared language → capture P/F into the worksheet. Paste any Designer compile error for the generator fix-loop.

**2026-06-08 (Mon, Day 1) — Phase 3 Designer verify GREEN ×3.** The Designer compile gate was AUTOMATED (pywinauto: launch + Ctrl+L/Ctrl+K + screenshot-vision read) and **F1+F3+F4 all compile CLEAN** with their multi-language dictionaries — the committed E3-F*-001 verify work, Day 1. FMF generator gap fixed en route (full [Level]/[Group]/[Field] emission + roster + label cap).

**2026-06-09 → 2026-06-11 (Tue–Thu, Days 2–4) — single-QN redesign + field-readiness end-to-end.** 12-digit QUESTIONNAIRE_NUMBER built (F1 pilot → F3/F4 replicated), emulator sync chain proven (F1/F3/F4 round-trips, field-sync role gap found+fixed), PSGC `.dat` deploy gap found+fixed (Add-Files every deploy), GPS auto-fetch, Annex-H consent, partial save, capture-type pass, combined-view screens, enumerator instructions — all shipped via repeated publish/deploy cycles. CSWeb breakout DBs + Sync Report live 6/12.

**2026-06-12 (Fri, Day 5 — gate day) — UAT R4 opened + 9 mid-round deploys + Tagalog SHIPPED.** R4 opened (F2-benchmarked guides, per-tester CSWeb users, GH form + #368/#369/#370). Patch train, all generator-first, all mid-round: F3 ×4 (photo flow, Q148→CheckBox, gating isolation, other-specify sweep), F4 ×3 (sweep + Designer-crash rollback/diagnose/retry, capture-type regression catch+fix), F1 ×2 (Section C #371–#375 via inject_blocks, date pickers + #376). Deploy fully automated (Package-name-keyed `auto_deploy.py` + agent-driven publish). **Tagalog extracted from ASPSI's Filipino v2.1.x (575/844/538 entries), QC'd, wired, deployed ×3, announced per channel.** 5 process skills authored + adversarially verified; wiki lint: 48 findings fixed; harmonization ETL skeleton live. PSA gate outcome not recorded — carries.

## Retrospective — Sprint 009

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

**Yes — exceeded on the substance, partial on the paperwork.** The Phase 3 multi-language verify landed Day 1 (and was re-proven all week by the automated publish pipeline), and the sprint went past "verify what ASPSI delivered" to *closing part of the content gap itself* (Tagalog wired + deployed Day 5). What didn't land as framed: the formal PSA bundle hand-off (E0-PSA-001) — the gate-day went to UAT R4 + the patch train, and the gate outcome is unrecorded. Goal B untouched, as the opportunistic framing allowed.

### 2. What surprised me? (process, not work — max 3 bullets)

- **The five-sprint "Designer-time" constraint was a tooling problem, not a calendar problem.** It died the moment Designer was driven by automation (pywinauto compile → publish → deploy). The lesson generalizes: a carry that survives 4+ sprints is probably mis-diagnosed — attack the constraint, not the schedule.
- **S008's "freed capacity drifts off-plan" pattern repeated, but this time the off-plan work WAS the project.** UAT R4 + 9 mid-round patches + deploy automation weren't in the sprint plan, yet they advanced field-readiness more than any committed item. The plan under-models emergent tester-driven work — it's now a standing workstream, not a surprise.
- **A new open-loop failure mode: the scrum source went stale while the automation around it ran green.** Standups auto-generated daily (the 6/7 fix held), but `sprint-current.md` was never updated mid-sprint — so Friday's Slack closeout snapshot faithfully posted week-old data. Work was recorded in log.md/GH/Slack, never folded back into the scrum artifacts.

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 010

**Close the scrum loop the same way the standup loop was closed: make sprint-state sync part of the cadence, not a memory.** Concretely — fold log.md/GH outcomes into `sprint-current.md` `status::` fields at least mid-week + at close (candidate: extend the 08:30 generator to flag drift between log.md recency and sprint-current mtime), so the Mon/Fri Slack snapshots can never post stale state again. And plan UAT triage as committed capacity (~1 day) instead of letting it arrive as "off-plan" for a third sprint.
