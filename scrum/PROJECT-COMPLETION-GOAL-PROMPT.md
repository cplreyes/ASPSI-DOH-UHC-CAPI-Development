---
type: steering
kind: completion-goal-prompt
project: UHC Survey Year 2 — CAPI Development (ASPSI | DOH-PMSMD)
data_programmer: Carl Patrick L. Reyes
created: 2026-06-07
horizon: engagement close (contract window Nov 2025 – Aug 2026)
pairs_with: [scrum/product-backlog.md, scrum/dependency-map.md, scrum/sprint-current.md, deliverables/CSPro/CSPro-Compile-and-Desk-Test-Runbook.md]
---

# Goal Prompt — Finish the ASPSI–DOH UHC Year 2 CAPI Project

> **Paste this as the opening context for any session whose job is to drive this project toward
> completion.** It is the north star: mission, current state, critical path, blockers, and the
> operating rules. It is deliberately self-contained — an agent reading this + the repo can pick up
> the work. Re-derive live state from `scrum/sprint-current.md` + `git log` before acting; this
> snapshot is dated 2026-06-07.

---

## 1. Mission — what "finished" means

Deliver a working, tested, documented **Computer-Assisted Personal Interviewing system** for the DOH
Universal Health Care Survey Year 2, across **4 instruments** (F1 Facility Head, F2 Healthcare Worker,
F3 Patient, F4 Household) + the PLF recruitment form, in **2 modes** (CSPro/CSEntry CAPI for F1/F3/F4;
PWA self-admin for F2), with **multi-language** support, synced via **CSWeb** (CAPI) and **Apps
Script/Cloudflare** (PWA), through to **pretest → fieldwork → clean data → final deliverables → NDU
handover**.

**Done = all six contractual deliverables (D1–D6) accepted and the project archived** (Epic 12). But
read §5 first: large parts of "done" are gated on externals outside the Data Programmer's lane.
**Carl's definition of done is the build/verify/bundle/document/handover work being complete and
unblocked-ready**; the externally-gated parts (pretest, fieldwork, final report) proceed when ASPSI/PI
clear their gates.

---

## 2. Who you are — operating identity

- **Carl is the Data Programmer.** He *builds* the CAPI system. He does **not** talk to DOH directly.
- **ASPSI (Kidd, Myra, Juvy) is the DOH interface.** Surface DOH-facing decisions as an **in-chat
  go/no-go checklist** for Carl to route through ASPSI — never draft DOH-facing comms or chase DOH.
- **Shan (ASPSI RA) is the QA tester** for the CAPI build (independent desk-test pass).
- **Scope discipline (CSA D1–D6):** SJREB tracking, tranche/deadline management, DOH-PMSMD matrix
  coordination are **ASPSI/PI/PMO lane — informational only**, not Carl's deliverables. Don't pull them
  onto the sprint board.

---

## 3. Current state — snapshot 2026-06-07

> The `product-backlog.md` headline is stale (last_updated 2026-05-10). The truth below folds in the
> May–June work (multi-language build, CSWeb go-live, S008/S009).

**Contractual:** D1 **Accepted**. D2/D3 **In Progress** (agreed extended timeline). D4–D6 not started.

**By instrument:**
- **F2 (PWA)** — **In production**, `v2.1.0`, **7 PH languages** live on `main` (PSA F2-share met early
  2026-06-02). Feature-complete bar a UAT tail + app-chrome translation for ilo/hil/war/bcl. Backend
  (Apps Script + Cloudflare Pages/Worker) live. *Open tooling debt:* clasp/#294 deploy-gap (S009 Goal B,
  opportunistic).
- **F1/F3/F4 (CSPro)** — dictionaries, logic (`.ent.apc`), and forms are **generator-built and
  multi-language** (translations self-applied by `generate_dcf.py`; QC'd 2026-06-03). **Preflight +
  language-parity = GREEN** (2026-06-07). **Remaining = Phase-3 GUI verify in CSPro Designer 8.0 +
  CSEntry** (compile → desk-test → language toggle). This is **S009 Goal A, in progress** — Carl's
  hands-on GUI work; there is **no headless compile** (verified).
- **PLF** — listing apps (`PickPatient()`/`PickHousehold()`), Designer-validate + publish (#140).

**By epic (live):**
- **E0 Project Mgmt / E9 Security** — ongoing governance; Data-Privacy-and-Security-Plan drafted.
- **E1 Inception / E2 Design** — **done** (all instruments Build-ready).
- **E3 App Dev** — F2 done; F1/F3/F4 multi-language verify in progress (S009).
- **E4 Backend/Sync** — PWA backend live; **CSWeb 8.0.1 LIVE on Elestio** (cutover ~Jun 3,
  `csweb.asiansocial.org`). Config-ready: dictionary upload + user/role matrix + tablet-sync
  (E4-CSWeb-003/-004/-005) still to do in the admin UI. ASPSI to repoint DNS → 1-line `API_URL`; send
  Juvy the first Elestio invoice.
- **E5 Field/Devices** — F2 distribution proven; **CAPI tablet provisioning BLOCKED on ASPSI
  procurement**. SOPs drafted (field-ops).
- **E6 Testing/Pilot** — PWA tested (UAT R1–R3). **CAPI desk-tests pending the Designer compile**
  (runbook §3). **Pretest BLOCKED on SJREB clearance.**
- **E7 Training/Docs** — Survey Manual sections + training decks (enumerator/STL/HCW) drafted.
- **E8 Fieldwork Monitoring** — not started; **BI dashboard blueprint + ETL spec drafted**.
- **E10 Data Cleaning** — codebook + harmonization ETL spec drafted.
- **E11 Analysis / E12 Handover** — not started.

**Hard external gate:** **PSA clearance — 2026-06-12** (last day of Sprint 009). Needs the CAPI app +
distinct translated versions bundled. F2 share met; CSPro share = the S009 verify + bundle.

---

## 4. Critical path to completion (sequenced)

```
[NOW] S009 — CSPro F1/F3/F4 multi-language Designer+CSEntry verify (Carl, GUI)   ← in progress
   │     fix-loop: paste Designer error → fix the GENERATOR → regenerate → preflight → reload
   ▼
PSA bundle (E0-PSA-001) → 2026-06-12 PSA gate   [fil/ilo + hil-F3F4 = ASPSI gap, E0-PSA-002 go/no-go]
   ▼
CAPI desk-tests (runbook §3: #193 F1 / #194 F3 / #195 F4) + PLF (#140)
   ▼
CSWeb operational config (E4-CSWeb-003 dict upload / -004 user-role matrix / -005 tablet sync)
   │     -005 gates E3-F1-088 (Phase-1 tablet sync-verify) → sync round-trip test (#196)
   ▼
Pretest pilot (Epic 6)   ──── BLOCKED: SJREB clearance + tablet procurement (ASPSI lane)
   ▼  → D3
Fieldwork monitoring (Epic 8: cross-track BI dashboard) → Data cleaning (Epic 10) → Analysis (Epic 11)
   ▼  → D4, D5
Handover & closeout (Epic 12: handover package, runbook, NDU file disposition, retro writeback) → D6
```

**Parallel, unblocked tracks (pull anytime capacity allows):** F2 clasp/#294 + UAT tail; documentation
(Survey Manual, training decks); security/privacy policies; data-harmonization ETL + BI dashboard v0;
CSWeb config (server is live now).

---

## 5. External blockers — not Carl's lane (handle as go/no-go, don't chase)

| Blocker | Gates | Owner | Carl's move |
|---|---|---|---|
| **ASPSI translations** — fil (Tagalog), ilo (Ilocano) for F1/F3/F4; hil for F3/F4 | full 7-lang CSPro bundle | ASPSI | Bundle delivered langs; document the gap (E0-PSA-002); English-fallback meanwhile |
| **SJREB ethics clearance** | Epic 6 pretest → D3/D4 | ASPSI/PI | Get everything pretest-ready; surface readiness, don't track clearance |
| **Tablet procurement** | Epic 5 device mgmt + on-device desk-test | ASPSI ops | Emulator-test first; provisioning SOP ready to execute |
| **PSA clearance (2026-06-12)** | survey launch | ASPSI↔PSA | Deliver the bundle; the submit-vs-hold call is ASPSI's |
| **DOH brand-book PDF** | F2 DESIGN-005 hex refine | ASPSI | Cosmetic; non-blocking |

**Posture:** finish *all* Carl-controllable work so the moment a gate clears, nothing else is in the
way. Never let a blocked item stall an unblocked one.

---

## 6. Operating rules — non-negotiable

1. **IRON RULE (CSPro):** when Designer reports a compile error, **fix the source table in the
   generator and regenerate** — never hand-edit `.dcf`/`.fmf`/`.ent.apc`. Hand-edits get overwritten and
   break single-source-of-truth. Run `preflight_validate.py` until ALL CLEAN before re-opening Designer.
2. **Generator-over-hand-edit; logic-pass-before-build.** Revisionable artifacts come from generators;
   complete skip/validation logic before building forms.
3. **Confidentiality:** `deliverables/comms/*`, `wiki/sources/*`, `wiki/analyses/*` with internal/
   verbatim ASPSI content stay **gitignored** (local only). `.claude/settings.local.json` + the
   webhook-bearing `post-daily-standup.ps1` stay ignored (secrets). Secret-scan before any commit.
4. **No DOH-facing comms.** Decisions → in-chat go/no-go checklist for Carl → ASPSI.
5. **Vault hygiene (PARA + LLM Wiki):** raw inputs in `raw/` (immutable, gitignored), authored outputs in
   `deliverables/`, knowledge in `wiki/`, Kebab-Case folders, update `index.md` + `log.md` after wiki ops.
6. **Git:** single-purpose PRs; CI green before merge; squash-merge (matches `(#N)` history);
   commit/push only when asked.

---

## 7. How to work

- **Cadence:** 1-week sprints, solo dev + AI. **Mode A** plan Monday, **Mode D** close Friday (retro +
  archive to `scrum/sprints/sprint-00N.md` + reset `sprint-current.md`). Standups auto-write daily via
  the `CAPI Scrum Daily Standup MD` scheduled task (08:30 MNL) + SessionStart hook.
- **Scrum lives in** `scrum/` — `sprint-current.md` (active), `sprints/` (archive), `standups/`,
  `product-backlog.md`, `dependency-map.md`.
- **Skills:** gstack-first; superpowers for brainstorm→plan→subagent-driven-dev on multi-task features
  (spec-reviewer + code-reviewer per task); `/daily-standup`, `/inbox-triage`; `uat-round-closeout` for
  F2 UAT rounds. Package new workflows as skills from the start.
- **Sequencing taste:** commit the headline goal **singularly**; bank an early finish into the next
  committed goal, not opportunistic drift (S008 retro lesson).

---

## 8. Start here — immediate next actions (2026-06-07 →)

1. **Finish S009 Goal A** — Carl runs the CSPro Designer compile + CSEntry language toggle per
   `deliverables/CSPro/2026-06-07-multilang-verify-worksheet.md` (F1 Id-block re-sync + 4 PSGC dicts
   first). Paste any Designer error → generator fix-loop. Close E3-F1-001/-F3-001/-F4-001.
2. **Assemble + hand off the PSA bundle (E0-PSA-001)** with the fil/ilo/hil-F3F4 gap documented
   (E0-PSA-002) ahead of the **2026-06-12** gate.
3. **Then (unblocked, high-leverage):** CSWeb operational config (E4-CSWeb-003/-004/-005); CAPI
   desk-tests (runbook §3); clasp/#294 if time; keep documentation + ETL/BI tracks moving.
4. **Stay pretest-ready** so the SJREB/tablet gates, when they clear, find nothing else in the way.

---

## 9. Contractual deliverables map

| ID | Deliverable | Tranche | Status | Unblocks at |
|----|-------------|---------|--------|-------------|
| **D1** | Inception Report | T1 15% | **Accepted** | — |
| **D2** | Survey materials/protocols (manual, SOPs, tools, translations) | T2 30% | In progress | instruments verified + docs final + translations delivered |
| **D3** | Pre-tested questionnaires + field ops manuals + training | T2 30% | In progress | Epic 6 pretest (SJREB-gated) |
| **D4** | Piloting progress + preliminary data report | T3 25% | Not started | fieldwork underway |
| **D5** | Training documentation (+ pre/post assessment) | T4 30% | Not started | training delivered |
| **D6** | Final report + policy briefs + dissemination | T4 30% | Not started | analysis complete → Epic 12 handover |

---

**One-line mission restatement:** *Take F1/F3/F4 through the CSPro multi-language verify and into the
PSA bundle now; finish every Carl-controllable build/verify/config/doc task so that when SJREB, tablets,
and ASPSI translations clear, the project flows straight through pretest → fieldwork → clean data →
final deliverables → NDU handover with nothing else in the way.*
