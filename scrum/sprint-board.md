---
title: Sprint Board (live view)
generated_by: dataview
source: scrum/sprint-current.md
---

# Sprint Board — live view of `sprint-current.md`

> Live-rendered from [[sprint-current|sprint-current.md]] via Dataview. Edit the `status::` field on each task in the source file to move cards between columns. Refresh interval: 2.5s (Dataview default).

## Columns by `status::` field

```dataviewjs
const file = dv.page("1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/sprint-current");

if (!file) {
  dv.paragraph("⚠️ Cannot find `scrum/sprint-current.md` — check the path in the dv.page() call.");
} else {
  const tasks = file.file.tasks;

  const cols = ["todo", "in-progress", "blocked", "done"];
  const grouped = Object.fromEntries(cols.map(c => [c, []]));

  for (const t of tasks) {
    const m = t.text.match(/status::\s*([a-z-]+)/);
    const status = m ? m[1] : (t.completed ? "done" : "todo");
    if (grouped[status]) grouped[status].push(t);
    else grouped["todo"].push(t);
  }

  const renderCard = (t) => {
    const idMatch = t.text.match(/\*\*([A-Z0-9-]+)\*\*/);
    const prMatch = t.text.match(/priority::\s*([a-z]+)/);
    const esMatch = t.text.match(/estimate::([^`]+?)(?:`|$)/);
    const id = idMatch ? idMatch[1] : "—";
    const pr = prMatch ? prMatch[1] : "";
    const es = esMatch ? esMatch[1].trim() : "";
    const link = `[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/sprint-current|${id}]]`;
    const meta = [pr, es].filter(Boolean).join(" · ");
    return `${link}${meta ? ` <small>(${meta})</small>` : ""}`;
  };

  dv.table(
    cols.map(c => `${c.toUpperCase()} (${grouped[c].length})`),
    [cols.map(c => grouped[c].map(renderCard).join("<br>") || "_(empty)_")]
  );
}
```

## Critical items only

```dataviewjs
const file = dv.page("1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/sprint-current");
if (!file) { dv.paragraph("⚠️ source not found"); } else {
  const tasks = file.file.tasks.filter(t => /priority::\s*critical/.test(t.text));
  if (tasks.length === 0) { dv.paragraph("_No critical items._"); } else {
    dv.taskList(tasks, false);
  }
}
```

## How to use

- Edit `status::` on a task in `sprint-current.md` → card moves columns within ~2.5s.
- Switch to **Reading view** (Ctrl+E) to see the rendered tables — Live Preview shows the code blocks as code.
- The first table is column-pivoted (kanban-style); the second is a flat task list of just the critical items, with native checkbox toggling.
- Status values recognized: `todo`, `in-progress`, `blocked`, `done`. Anything else falls into `todo`.
