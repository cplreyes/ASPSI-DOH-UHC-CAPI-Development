---
sprint: 007
plan_status: draft
authored: 2026-05-09
trigger: opens Mon following Sprint 006 close
---

# Sprint 007 — Plan (draft)

Tentative Sprint 007 commitments. Items remain in `sprint Slot::unscheduled` on Project #8 until Sprint 006 closes — at that point this plan becomes `sprint-current.md` and items are slotted to `sprint-007`.

## Anchor

Continue F1 build — skip-logic + validation wiring + dynamic behavior. F1 should be desk-test-ready by Sprint 007 close, unblocking F3 build entry.

## Candidate commitments (~24h base, flex per Sprint 006 carry)

| ID | Title | Est | Pri |
|---|---|---|---|
| E3-F1-022 | Wire hard validations (`errmsg` + `reenter` per rule) | 1d (8h) | high |
| E3-F1-023 | Wire soft validations (`accept()` overrides) | 4h | high |
| E3-F1-024 | Wire display gates (`postproc` / `onfocus`) | 4h | high |
| E3-F1-030 | Dynamic value sets (`setvalueset()` for facility-type-dependent lists) | 4h | high |
| E3-F1-031 | Cross-field consistency (e.g., tenure ≤ age − 15) | 4h | high |
| **Total** | | **24h** | |

## Stretch (pull if base clears mid-sprint)

| ID | Title | Est | Pri |
|---|---|---|---|
| E3-F1-032 | Conditional question text fills | 2h | medium |
| E3-F1-040 | Informed consent capture screen | 3h | critical |
| E3-F1-041 | Eligibility screen | 2h | high |

## Carry rules (per Sprint 006 close)

- If Sprint 006 stretches (E3-F1-021 + E2-F3-010) didn't land, pull them into Sprint 007 first
- If `E6-CAPI-001` (F1 desk test, scheduled in Sprint 006) surfaced bug fixes, prioritize those over stretch items
- If E3-F1-PHASE2-PLAN cleared, F3 build (E2-F3-010 Designer validation onward) becomes pullable

## Dependencies entering Sprint 007

- Sprint 005 → must close E3-F1-088 (Phase 1 sync) and E3-F1-PHASE2-PLAN
- Sprint 006 → should land Filipino translations + master skip gates (foundation for validation work)
- External → none new entering Sprint 007 (PSGC + tablets + SJREB still pending)

## Out of Sprint 007 scope

- F3/F4 build kickoff (waits on Sprint 008+ once F1 patterns proven)
- CSWeb stand-up (waits until F1 build artifact stable)
- Tablet provisioning (calendar-blocked on ASPSI procurement)
- Pretest pilot (calendar-blocked on SJREB)
