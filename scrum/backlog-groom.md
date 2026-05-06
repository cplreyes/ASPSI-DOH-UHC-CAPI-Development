---
title: Backlog Grooming View
purpose: PO-level visibility into all open tasks across all epics, grouped by sprint slot
last_updated: 2026-05-06
generated_by: dataviewjs (queries) + `.claude/scripts/tag_backlog_slots.py` (slot tags)
---

# Backlog Grooming — PO View

> **Single source of truth for "where does each open task live in time?"**
>
> Each open `[ ]` task across `scrum/epics/*.md` carries an inline `` `scrum::<slot>` `` field. The slot is one of:
>
> | Slot | Meaning |
> |---|---|
> | `sprint-NNN` | Committed (or stretch) in that sprint's `sprint-current.md` / `sprints/sprint-NNN.md` |
> | `unscheduled` | Real work, not yet planned into any sprint |
>
> **Reassign** a task by editing its `` `scrum::` `` value on the task line in its epic file. No other file needs to change. Switch to **Reading view** (Ctrl+E) to see the queries render — Live Preview shows the code blocks as code.
>
> Inline fields are wrapped in backticks per project convention (`` `status::todo` ``, `` `priority::high` ``, etc.), so these queries use **dataviewjs** + regex on `t.text` to extract them — same pattern as `scrum/sprint-board.md`.

## Active Sprint — Sprint 004 (2026-05-04 → 2026-05-08)

```dataviewjs
const tasks = dv.pages('"1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/epics"').file.tasks
  .where(t => !t.completed && /scrum::\s*sprint-004/.test(t.text));
if (tasks.length === 0) { dv.paragraph("_(no open tasks tagged sprint-004)_"); }
else { dv.taskList(tasks, false); }
```

## Next Sprint — Sprint 005 (filed)

> Items already triaged into Sprint 005 from /cso findings, /design-review findings, UAT R2 follow-ups, the v2.0.1 patch slate, and the 2026-05-06 PO review (last_login_at write, prod hash delete, design-review sweep).

```dataviewjs
const tasks = dv.pages('"1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/epics"').file.tasks
  .where(t => !t.completed && /scrum::\s*sprint-005/.test(t.text));
if (tasks.length === 0) { dv.paragraph("_(no open tasks tagged sprint-005)_"); }
else { dv.taskList(tasks, false); }
```

## Unscheduled Backlog — Carl's lane

> Open tasks not yet pulled into any sprint. **Excludes** items flagged `out_of_scope::data_programmer` (those live in the next section). Pull from here at sprint planning. Grouped by epic source file.

```dataviewjs
const tasks = dv.pages('"1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/epics"').file.tasks
  .where(t => !t.completed
    && /scrum::\s*unscheduled/.test(t.text)
    && !/out_of_scope::/.test(t.text));

if (tasks.length === 0) { dv.paragraph("_(none)_"); }
else {
  const grouped = {};
  for (const t of tasks) {
    const file = t.path.split('/').pop().replace('.md', '');
    if (!grouped[file]) grouped[file] = [];
    grouped[file].push(t);
  }
  for (const file of Object.keys(grouped).sort()) {
    dv.header(4, `${file} (${grouped[file].length})`);
    dv.taskList(grouped[file], false);
  }
}
```

## Unscheduled Backlog — Out-of-scope (PMO / PI lane)

> Tracked for visibility but not Carl's responsibility per the Data Programmer scope umbrella (CSA D1–D6). Re-tag `` `scrum::unscheduled` `` (without removing `out_of_scope::`) only if the scope itself changes.

```dataviewjs
const tasks = dv.pages('"1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/epics"').file.tasks
  .where(t => !t.completed
    && /scrum::\s*unscheduled/.test(t.text)
    && /out_of_scope::/.test(t.text));
if (tasks.length === 0) { dv.paragraph("_(none)_"); }
else { dv.taskList(tasks, false); }
```

## Snapshot — counts by slot

```dataviewjs
const tasks = dv.pages('"1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/epics"').file.tasks
  .where(t => !t.completed);

const slots = {};
for (const t of tasks) {
  const m = t.text.match(/scrum::\s*([a-z0-9-]+)/);
  const slot = m ? m[1] : "(unset)";
  slots[slot] = (slots[slot] || 0) + 1;
}

dv.table(
  ["Slot", "Open tasks"],
  Object.entries(slots).sort(([a], [b]) => a.localeCompare(b)).map(([k, v]) => [k, v])
);
```

## Re-tagging mechanics

**To move a task from `unscheduled` → `sprint-005`:** open the epic file, find the task line, change `` `scrum::unscheduled` `` to `` `scrum::sprint-005` ``. Save. The dataviewjs blocks above re-resolve on next render (~2.5s default).

**To move a task to a future sprint not yet started:** use the same pattern with the new slot name (`` `scrum::sprint-006` `` etc.). The slot is just a string — queries match by exact regex, so consistency in spelling matters more than any pre-defined list.

**To pull from the unscheduled backlog into a sprint mid-week:** re-tag, then add a one-liner to that sprint's `sprint-current.md` Daily Notes ("**E4-APRT-XXX pulled in mid-sprint**: <reason>"). The grooming view is the source of truth for slot membership; sprint-current.md notes are the audit trail.

**To bulk re-tag (e.g., closing Sprint 004 → 005):** edit the `SPRINT_NNN` sets at the top of `.claude/scripts/tag_backlog_slots.py`, re-run. The script is idempotent — it skips lines that already have a `scrum::` tag, so re-running is safe.

## Caveats

- **Lint debt in unscheduled:** the bucket may include tasks that are done in reality but not yet flipped to `[x]`. Lint pass on the unscheduled bucket is a pre-grooming step, not a separate ritual. (2026-05-06 lint pass closed E4-PWA-013, E4-PWA-014, E4-PWA-015 retroactively.)
- **Out-of-scope items in unscheduled:** Epic 0 has many `out_of_scope::data_programmer` items (E0-011/012/013/014/020/030/031/032/032a/033/050/051). They're tagged `` `scrum::unscheduled` `` for symmetry but separated visually above.
- **Headlines/state in `product-backlog.md`** are still the stakeholder narrative. This file is the operational backlog ledger.
