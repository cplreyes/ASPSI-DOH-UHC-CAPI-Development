---
title: Backlog Grooming View
purpose: PO-level visibility into all open tasks across all epics, grouped by sprint slot
last_updated: 2026-05-06
generated_by: human + LLM (slot tags written by `.claude/scripts/tag_backlog_slots.py`)
---

# Backlog Grooming — PO View

> **Single source of truth for "where does each open task live in time?"**
>
> Each open `[ ]` task across `scrum/epics/*.md` carries an inline ``scrum::<slot>`` field. The slot is one of:
>
> | Slot | Meaning |
> |---|---|
> | `sprint-NNN` | Committed (or stretch) in that sprint's `sprint-current.md` / `sprints/sprint-NNN.md` |
> | `unscheduled` | Real work, not yet planned into any sprint |
>
> **Reassign** a task by editing its ``scrum::`` value on the task line in its epic file. No other file needs to change.
>
> `sprint-current.md` is then a *thin pointer* to a sprint slot, not a duplicate task list. The Sprint Goal + Definition of Done + Daily Notes still live in `sprint-current.md`; the committed/stretch task list resolves to `scrum::<this-sprint>` here.

## Active Sprint — Sprint 004 (2026-05-04 → 2026-05-08)

```dataview
TASK
FROM "scrum/epics"
WHERE !completed AND scrum = "sprint-004"
SORT priority ASC
```

## Next Sprint — Sprint 005 (filed)

> Items already triaged into Sprint 005 from /cso findings, /design-review findings, UAT R2 follow-ups, and the v2.0.1 patch slate.

```dataview
TASK
FROM "scrum/epics"
WHERE !completed AND scrum = "sprint-005"
SORT priority ASC
```

## Unscheduled Backlog — Carl's lane

> Open tasks not yet pulled into any sprint. **Excludes** items flagged `out_of_scope::data_programmer` (those live in the next section). Sort by priority within each epic; pull from here at sprint planning.

```dataview
TASK
FROM "scrum/epics"
WHERE !completed AND scrum = "unscheduled" AND !out_of_scope
GROUP BY file.name
SORT priority ASC
```

## Unscheduled Backlog — Out-of-scope (PMO / PI lane)

> Tracked for visibility but not Carl's responsibility per the Data Programmer scope umbrella (CSA D1–D6). Re-tag `scrum::unscheduled` (without removing `out_of_scope::`) only if the scope itself changes.

```dataview
TASK
FROM "scrum/epics"
WHERE !completed AND scrum = "unscheduled" AND out_of_scope
GROUP BY file.name
SORT priority ASC
```

## Snapshot — counts by slot (regenerate on demand)

```dataview
TABLE WITHOUT ID
  rows.scrum[0] AS Slot,
  length(rows) AS Tasks
FROM "scrum/epics"
WHERE !completed AND scrum
GROUP BY scrum
SORT Slot ASC
```

## Re-tagging mechanics

**To move a task from `unscheduled` → `sprint-005`:** open the epic file, find the task line, change ``scrum::unscheduled`` to ``scrum::sprint-005``. Save. The Dataview blocks above re-resolve on next render.

**To move a task to a future sprint not yet started:** use the same pattern with the new slot name (``scrum::sprint-006`` etc.). The slot is just a string — Dataview groups by exact value, so consistency in spelling matters more than any pre-defined list.

**To pull from the unscheduled backlog into a sprint mid-week:** re-tag, then add a one-liner to that sprint's `sprint-current.md` Daily Notes ("**E4-APRT-XXX pulled in mid-sprint**: <reason>"). The grooming view is the source of truth; sprint-current.md notes are the audit trail.

**To bulk re-tag (e.g., closing Sprint 004 → 005):** run `.claude/scripts/tag_backlog_slots.py` after editing the SPRINT_NNN sets at the top of the script. The script is idempotent — it skips lines that already have `scrum::`.

## Caveats

- **Stale items:** the unscheduled bucket includes tasks that may already be done in reality but not yet flipped to `[x]` (e.g., E4-PWA-013 Phase F prod cutover — already shipped 2026-05-01 per memory `project_phase_f_readiness_2026_04_30.md`; E4-PWA-014 / -015 — resolved per memories). Lint pass on the unscheduled bucket is a pre-grooming step, not a separate ritual.
- **Out-of-scope items in unscheduled:** Epic 0 has many `out_of_scope::data_programmer` items (E0-011/012/013/014/020/030/031/032/032a/033/050/051). They're tagged `scrum::unscheduled` for symmetry but separated visually above.
- **Headlines/state in `product-backlog.md`** are still the stakeholder narrative. This file is the operational backlog ledger.
