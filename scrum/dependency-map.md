---
title: Dependency map + phase clustering
last_updated: 2026-05-09
status: historical
relabeled: 2026-06-29
superseded_by: scrum/product-backlog.md §1 (authoritative status) + scrum/sprint-current.md
---

# Dependency Map — UHC CAPI Year 2

> [!warning] Historical — do not use for current status (relabeled 2026-06-29)
> This map was last accurate at the **Sprint 004–006 era (snapshot 2026-05-09)**, when F1/F3/F4 were unbuilt and CSWeb/tablets were ahead on the critical path. **Most of the critical path below is now DONE** and the sequencing no longer reflects reality. It is kept for historical reference only.
>
> **For current status, read `scrum/product-backlog.md` §1 (authoritative) + `scrum/sprint-current.md`.** As of 2026-06-29:
> - **F1 / F3 / F4** — multi-language instruments **built, deployed to CSWeb, in UAT Round 5 burndown**; pretest-readiness + go/no-go assessed (2026-06-27). *(The ~80h/30h/50h "F1/F3/F4 build" poles below are spent.)*
> - **F2 PWA** — **production v2.1.0, all 7 PSA languages**; UAT R1–R3 closed. *(The "Round 3" parallel track is closed.)*
> - **CSWeb** — **8.0.1 LIVE on Elestio** (`csweb.asiansocial.org`) + sync/map/case-status dashboards. *(The "CSWeb stand-up ~30h" pole is done.)*
> - **Supervisor hub** (Epic 8) — **built + device-verified on 2 tablets + live training guide**. *(Did not exist when this map was drawn.)*
> - **Still genuinely pending external gates** (unchanged): **tablet procurement** and **SJREB clearance + pretest scheduling** — all ASPSI/DOH lane, not Carl's. The project waits on ASPSI's pretest date.
>
> A full rebuild of this map isn't planned while the project is in field-readiness/waiting-on-pretest mode; re-author it only if a new build phase opens. Everything below the divider is the original 2026-05-09 content, preserved as-is.

---

Snapshot of critical-path sequencing and phase grouping for the 113 active in-scope tasks. Pairs with `scrum/product-backlog.md` and `scrum/epics/*.md`. Refresh weekly during grooming.

## Capacity model

- **Cadence:** 1-week sprints, solo dev + AI
- **Capacity:** variable per sprint — slot only 3 sprints ahead, leave the rest in the phase clusters below until externals clear
- **Total active scope:** ~449h estimated + 4 recurring/ongoing items
- **Estimated runway at 25h/week:** ~18 sprints; at telescoped pace ~12–15

## Critical path (sequential)

```
[NOW]
  │
  ▼
E3-F1-088    Phase 1 sync mechanic                  (6h, Sprint 005)
  │
  ▼
E3-F1-PHASE2-PLAN  Phase 2 scope confirmation       (4h, Sprint 005)
  │
  ▼
E3-F1-001..045   F1 build (form layout + skip + validation + FIELD_CONTROL)   (~80h)
  │   E3-F1-043b  PSGC cascade ──── BLOCKED (ASPSI value-set confirm)
  │
  ▼
E3-F1-060        F1 CSEntry smoke test              (2h)
  │
  ▼
E3-F3-001..060   F3 build (parallel-able with F4 once Phase 2 confirms)   (~30h estimated; many TBD)
E3-F4-001..075   F4 build (roster-heavy, highest complexity)              (~50h estimated)
E3-PLF-001       PLF (mode TBD)                                            (~4h)
  │
  ▼
E2-F3-010 / E2-F4-010   Designer validation passes  (3h + 4h)
  │
  ▼
E4-CSWeb-001..007   CSWeb stand-up (server prov + install + sync config)   (~30h)
  │
  ▼
E5-CAPI-001..007   Tablet provisioning ──── BLOCKED (ASPSI procurement)    (~14h active, calendar-gated)
  │
  ▼
E6-CAPI-001..005   Desk tests (F1/F3/F4) + sync round-trip + Shan handoff  (~26h)
  │
  ▼
E6-CAPI-006        Pretest pilot ──── BLOCKED (SJREB clearance)            (~40h, 1-week run)
  │
  ▼
E6-CAPI-007        Pretest debrief + bug triage                            (4h)
  │
  ▼
[FULL ROLLOUT — Epic 8 Fieldwork Monitoring]
```

## Parallel tracks (no critical-path dependency on F1/F3/F4)

| Track | Items | Est | Notes |
|---|---|---|---|
| F2 PWA Round 3 | E3-F2-PWA-R3-001/2/3 + E6-PWA-007 + E6-PWA-008/009/010 | ~30h | Independent — runs whenever |
| Documentation | E7-DOC-001/002/003/004/005 + E7-TRAIN-001/002/003 + E7-HELP-001 | ~44h | Pulls in once F1 builds enough to screenshot |
| Security policies | E9-004/010..014 + 020..025 + 030..033 + 040..043 + 050/051 | ~52h | Mostly policy docs, can run anytime |
| Admin Portal v2.0.1 polish | E4-APRT-046, E4-APRT-047 | ~4h | Files dashboard create-folder + rename |
| Worker hotfix | E4-PWA-014, E4-PWA-015 | ~3h | CF Pages auto-deploy + PBKDF2 cap |
| Integration ETL | E4-INT-001/002/003 | ~24h | Feeds Epic 8/10; gated on F1/F3/F4 data flowing |

## External-blocked items (pinned until inputs land)

| Item | External dependency | Owner |
|---|---|---|
| E3-F1-043b | PSGC value-set confirmation | ASPSI ops |
| E5-CAPI-002 / 003 / 004 / 005 / 006 / 007 | Tablet procurement | ASPSI ops |
| E6-CAPI-006 | SJREB ethics clearance | ASPSI/PI lane (E0-020) |
| E5-PWA-005 | Reminder cadence policy | ASPSI ops |
| E3-F2-PWA-DESIGN-005 | DOH brand-book PDF | ASPSI |

## Phase clustering (for unscheduled items)

### Phase 2-gated (waits on E3-F1-PHASE2-PLAN sign-off)
- All E3-F1-001 through E3-F1-070 (F1 form build)
- All E3-F3-* (F3 build)
- All E3-F4-* (F4 build)
- E3-PLF-001
- E2-F3-010, E2-F4-010 (Designer validation)
- E2-PLF-003 through E2-PLF-006 (PLF design pass)

### CSWeb-gated (waits on E4-CSWeb-001..007)
- E6-CAPI-004 (sync round-trip test)
- E5-CAPI-003 (imaging SOP — needs CSEntry installable artifacts)

### Tablet-gated (waits on ASPSI procurement)
- E5-CAPI-002 onward
- E6-CAPI-001/002/003 (desk tests need real tablets, can do emulator first)

### SJREB-gated (waits on ethics clearance)
- E6-CAPI-006 (pretest)
- E6-CAPI-007 (debrief — follows pretest)

### Free-floating (no blocker, can pull anytime)
- F2 PWA Round 3 + UAT (E3-F2-PWA-R3-001/2/3 + E6-PWA-007 + E6-PWA-008/009/010)
- Documentation track (E7-DOC-001..005 + E7-TRAIN-001..003 + E7-HELP-001)
- Security policy track (E9-004 + E9-010..014 + 020..025 + 030..033 + 040..043 + 050/051)
- Admin portal hardening (E4-APRT-046, 047)
- Integration spec (E4-INT-001 — drafting can start before F1 data flows)

## Long-pole risk

The two pacing risks are **SJREB clearance** and **tablet procurement**. Both are out of Carl's lane (PM/PI/ASPSI ops). Until they land, the project can:
- Finish all build work (F1 + F3 + F4 + PLF + admin v2.0.1)
- Stand up CSWeb
- Draft all docs/training/security policies
- Do desk testing on emulators

But it cannot finish Epic 6 (Pilot) or transition to Epic 8 (Fieldwork) without both.
