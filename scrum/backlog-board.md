---
title: Backlog Board (kanban view)
generated_by: dataviewjs
source: scrum/epics/*.md (`scrum::` slot field)
---

# Backlog Board — kanban view

> Live-rendered from `scrum/epics/*.md` via Dataview. Columns are sprint slots, cards are open tasks. Edit the `` `scrum::` `` field on a task in its epic file to move the card between columns. Refresh interval: 2.5s (Dataview default).
>
> **Read-only.** For drag-and-drop, install the [Obsidian Kanban plugin](https://github.com/mgmeyers/obsidian-kanban) — see "Upgrade to drag-and-drop" at the bottom.
>
> Switch to **Reading view** (Ctrl+E) to see the table render.

## Slot columns

```dataviewjs
const tasks = dv.pages('"1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/epics"').file.tasks
  .where(t => !t.completed);

const cols = ["sprint-004", "sprint-005", "unscheduled"];
const grouped = Object.fromEntries(cols.map(c => [c, []]));

for (const t of tasks) {
  const m = t.text.match(/scrum::\s*([a-z0-9-]+)/);
  const slot = m ? m[1] : null;
  if (slot && grouped[slot]) grouped[slot].push(t);
}

// Sort each column by priority
const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
const getPri = (t) => priorityOrder[(t.text.match(/priority::\s*([a-z]+)/) || [])[1]] ?? 4;
for (const slot of cols) {
  grouped[slot].sort((a, b) => getPri(a) - getPri(b));
}

const renderCard = (t) => {
  const id = (t.text.match(/\*\*([A-Z0-9-]+)\*\*/) || [])[1] || "—";
  const pr = (t.text.match(/priority::\s*([a-z]+)/) || [])[1] || "";
  const es = (t.text.match(/estimate::([^`]+?)(?:`|$)/) || [])[1]?.trim() || "";
  const oos = /out_of_scope::/.test(t.text) ? " ⓞ" : "";
  const file = t.path.split('/').pop().replace('.md', '').replace(/^epic-\d+-/, '').replace(/-/g, ' ');
  const meta = [pr, es].filter(Boolean).join(" · ");
  return `**${id}**${oos}<br><small>${file}${meta ? ` · ${meta}` : ""}</small>`;
};

dv.table(
  cols.map(c => `${c.toUpperCase()} (${grouped[c].length})`),
  [cols.map(c => grouped[c].map(renderCard).join("<br><br>") || "_(empty)_")]
);
```

> **Legend:** ⓞ = `out_of_scope::data_programmer` (PMO/PI lane); ignore for sprint planning. Cards sorted by `priority::` (critical → high → medium → low) within each column.

## Sprint-004 board (status:: pivot of just the active sprint)

> The same kanban shape as `scrum/sprint-board.md`, but filtered to `scrum::sprint-004` items only — gives you both views in one place.

```dataviewjs
const tasks = dv.pages('"1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/epics"').file.tasks
  .where(t => !t.completed && /scrum::\s*sprint-004/.test(t.text));

const cols = ["todo", "in-progress", "blocked", "done"];
const grouped = Object.fromEntries(cols.map(c => [c, []]));

for (const t of tasks) {
  const m = t.text.match(/status::\s*([a-z-]+)/);
  const status = m ? m[1] : "todo";
  if (grouped[status]) grouped[status].push(t);
  else grouped["todo"].push(t);
}

const renderCard = (t) => {
  const id = (t.text.match(/\*\*([A-Z0-9-]+)\*\*/) || [])[1] || "—";
  const pr = (t.text.match(/priority::\s*([a-z]+)/) || [])[1] || "";
  const es = (t.text.match(/estimate::([^`]+?)(?:`|$)/) || [])[1]?.trim() || "";
  const meta = [pr, es].filter(Boolean).join(" · ");
  return `**${id}**${meta ? `<br><small>${meta}</small>` : ""}`;
};

dv.table(
  cols.map(c => `${c.toUpperCase()} (${grouped[c].length})`),
  [cols.map(c => grouped[c].map(renderCard).join("<br><br>") || "_(empty)_")]
);
```

## How re-tagging moves cards

| Action | Where | Effect |
|---|---|---|
| Move card slot column | Edit `` `scrum::SLOT` `` on the task in its epic file | Card jumps to new column on next render (~2.5s) |
| Move card status column (active sprint) | Edit `` `status::STATE` `` on the task | Card jumps within the bottom board |
| Pull from unscheduled into next sprint | Change `` `scrum::unscheduled` `` → `` `scrum::sprint-005` `` | Card leaves unscheduled column, lands in sprint-005 |
| Bulk re-tag at sprint rollover | Edit `SPRINT_NNN` sets in `.claude/scripts/tag_backlog_slots.py`, re-run | Idempotent; skips already-tagged lines |

## Upgrade to drag-and-drop

If the read-only kanban gets cumbersome at scale, install the **Obsidian Kanban plugin**:

1. Settings → Community plugins → Browse → search "Kanban" → install + enable.
2. Create a new file via the Kanban plugin's "Create new board" command (sets up the kanban-plugin frontmatter automatically).
3. Either: (a) maintain a parallel kanban file as the visual control surface and let it write back to its own task list, OR (b) script a one-way sync from the epic files into a kanban file (Dataview can't write, so this needs a plugin or external script).

The current backtick-wrapped inline-field convention won't drag cleanly into the plugin's format — the plugin expects raw `- [ ]` cards under `## Column` headers, not `- [ ] **ID** ... `` `scrum::sprint-004` ``` lines. Two paths if you want to commit to drag-and-drop:

- **Treat the kanban file as the source of truth for the active sprint** — same role as today's `sprint-current.md`. Epic files become an archival record of completed work + reference for unscheduled items. Trade-off: dual-bookkeeping during the sprint (move cards in kanban, transcribe to epic at sprint close).
- **Stay with this dataview view** — read-only, but the slot field stays as the single source of truth and the script-based bulk re-tag handles sprint rollovers cheaply.

For solo + AI scrum at this volume (140 open tasks across 8 epics), the dataview view is probably enough. If grooming-as-clicking becomes the bottleneck, revisit.
