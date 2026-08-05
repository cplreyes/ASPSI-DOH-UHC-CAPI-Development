# Uniform console case viewer — F1/F3/F4 to match F2

**Asked for:** 2026-07-30, Carl — "that's a good viewing, can you also do that to other instruments so they are uniform"
**Status:** F2 DONE and live. F1/F3/F4 NOT started — this is the plan.
**Why it matters:** F2 now opens full detail on the console's own login. F1/F3/F4 still bounce to
`/csweb/sync-report?dict=…&case=…`, which needs a **second, different** login (per-user CSWeb).
Uniform means all four open the same way, on one login.

---

## What already exists and must be reused (do not rewrite)

| Piece | Where | Gives you |
|---|---|---|
| `parse_dcf(path)` | `csweb-spss-gen.py:113` | itemmap from the CSPro `.dcf` codebooks in `/opt/spss-meta` |
| `prep_frame(csv, itemmap)` | `csweb-spss-gen.py:165` | `(df, header, var_labels{col:label}, val_labels{col:{code:label}})` |
| dynamic table discovery | `csweb-responses-gen.py:106` | `(singular, rosters)`; a **roster = a record table with an `occ` column** |
| wide + roster CSVs | already written to `/docs/data/` every 2 min | the per-case data, already extracted |
| `csweb-f2-cases-gen.py` | `/opt/`, 2-min cron | the working F2 pattern: per-case JSON, atomic write, write-only-if-changed, `.htaccess` refuse-guard |
| `f2-case.html` | `/docs/` | the viewer shell: meta grid, search, hide-unanswered, gated at dashboard tier |

**Read the data-room CSVs, not MySQL.** They are already generated, already label-aligned with the
SPSS/Stata/R extracts, and it means the console viewer can never disagree with the exports.

---

## The two things that make F1/F3/F4 harder than F2

1. **Coded values.** F2 stores English strings, so F2 needed no value labels. F1/F3/F4 store raw
   codes (`1`, `2`, `98`) that are meaningless without the `.dcf` value sets. Every answer must go
   through `val_labels[col][code]`, and must show the code **and** the label — the exports keep raw
   codes deliberately, so the viewer should read `2 — Female`, never silently relabel.
   Beware partially-labeled numerics (amounts where only `98=DK` is labeled): show the raw number
   when there is no matching value label, never blank it.
2. **Rosters.** F1/F3/F4 have repeating records (F4's household roster is 23 items × 20 occurrences).
   The flat Q&A table cannot express these. Render each roster as its own sub-table, one row per
   `occ`, below the singular answers.

---

## Build order

1. **`csweb-cases-gen.py`** (generalise `csweb-f2-cases-gen.py`): for each of f1/f3/f4, read the wide
   CSV + roster CSVs, apply `parse_dcf` + `prep_frame` labels, write
   `/docs/cases/<inst>/<qn>.json` = `{meta, answers[{code,label,raw,value}], rosters[{record,label,rows[]}]}`.
   Keep: atomic `os.replace`, write-only-if-changed, `.htaccess` refuse-guard, loud failure
   (**no bare `except` that empties a payload** — that bug published 79 blank F2 cases before it was caught).
2. **Gate `/docs/cases/` FIRST**, at dashboard tier, reusing the `Require user` line verbatim from
   `/docs/.htaccess` — `/docs/` FilesMatch blocks match **filenames**, so a new directory is public
   until gated. Same trap as `plan.json` and `/docs/f2/`.
3. **Generalise the viewer** to `case.html?inst=<f1|f3|f4|f2>&id=<qn|submission_id>`; keep
   `f2-case.html` working (redirect or thin wrapper) so existing links do not break.
4. **Repoint the dashboard link** for f1/f3/f4 in `csweb-dashboard-gen.py` — the ternary already has
   the shape; add the console URL as primary and keep the CSWeb `sync-report` URL as a secondary
   "open in CSWeb" link, since CSWeb remains the editing surface.
5. **Cron** `*/2` flock-guarded, odd/even offset from the responses gen so it never reads a torn CSV
   (the SPSS gen already uses `1-59/2` sharing the responses lock — copy that).

## Verification (what actually counts)

- One signed-in browser session: dashboard → click one row per instrument → the case renders. That
  end-to-end click is the only proof that matters; a generator that prints OK proved nothing for F2.
- Coded answers show `code — label`; a roster renders its occurrences; a case with no roster rows
  does not render an empty table.
- Anonymous `curl` on `/docs/cases/**` and the viewer → **401**.
- Second generator run writes 0 files (idempotent).
- `md5` worktree == `/opt` for every generator touched.

## Open decision

Whether the CSWeb `sync-report` link stays alongside the console link. Recommended: **yes, keep it**
— CSWeb is still where a case gets edited, and patch #7's View-case modal is the authoritative view.
The console viewer is for *reading* without a second login.
