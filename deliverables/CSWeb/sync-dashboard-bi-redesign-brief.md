# Sync Dashboard → BI-grade redesign · decision + delivery record

**Status:** DELIVERED and live, 2026-07-29 · `https://capi.asiansocial.org/docs/dashboard.html`
**Decision:** Option A — single-canvas BI grid + externalised assignment plan
**Evidence:** `sync-dashboard-bi-redesign-options.excalidraw` / `.png` (rendered options comparison)
**Companion:** `sync-dashboard-reporting-audit-2026-07-29.md` — the 12-finding audit this closes out

---

## The brief's original premise was wrong — this is what the measurement showed

The starting brief claimed the dashboard's 350 KB "scales linearly with fieldwork" and that
the weight was "concentrated entirely in the case list". Measured on the live page, neither
held:

| Component | Bytes | % of page | Grows with fieldwork? |
|---|---:|---:|---|
| `targets` — the static 1,521-facility plan | 185,518 | 53% | **No** |
| app JS | 63,373 | 18% | No |
| CSS | 45,574 | 13% | No |
| **case rows** (118 cases) | 32,732 | 9% | **Yes**, ≈277 B/case |
| other markup | 23,270 | 7% | No |

**91% of the page was fixed cost**, and the single largest item was static reference data
being re-serialised into every 2-minute regeneration.

Worse for the brief's recommendation: the case rows feed **seven** panels — KPIs, trend,
coverage, productivity, quality, the per-instrument charts, *and* the case list — because
all filtering is client-side. Moving the case list to its own page (the brief's Option C)
would therefore have saved **zero bytes**. That is why the fork was re-diagrammed before any
code was written.

---

## What shipped

| Audit | Change | Effect |
|---|---|---|
| — | Assignment plan externalised to `/docs/plan.json`, hashed query string, fetched once | **350,467 → 172,079 bytes (−51%)**; payload 220,940 → 35,462 (−84%) |
| **F4** | Every KPI carries a comparator (7-day count, rate-of-base, 7-day mean) | a number now answers "is this good?" |
| **F5** | KPI strip split into **Progress** and a red-ruled **⚠ Needs attention** group | a rising "No GPS fix" can no longer read as achievement |
| **F6** | Coverage panel badges its deliberate enumerator-filter exclusion, inline, only when that filter is active | verified: coverage holds at 28 rows while the KPI drops to 6 |
| **F9** | Okabe-Ito colour-blind-safe categorical palette; coverage ramp drops the green/red pair | hue is never the only cue — every category is labelled, every rate printed |
| **F12** | One-line universe statement under each panel | borrows the tabulation plan's discipline |
| — | Wide tables scroll inside their own panel | page body no longer scrolls sideways (1374 → 1024 at tablet) |

## BI look and feel — the composition, not the paint

Carl, after seeing three candidate skins: *"BI Dashboard with same overall feels not
components only."* Correct call — restyling cards would have left it a report you scroll.
What changed is the layout:

| Change | Why |
|---|---|
| Canvas widened 1240 → 1600px | Scoped to this page. `portal.css` is shared with the map and data room, so `.canvas` is overridden here, not there. |
| **One dense KPI header band** — Progress (4) │ ⚠ Needs attention (2) │ By instrument (4) | Ten tiles in three semantic groups across one row. This is what makes the top of the page read as a dashboard. Collapses 3 → 1 column under 1360px. |
| Every panel is a card | The eye reads regions of a canvas instead of a continuous document. |
| Sticky filter bar | A BI canvas keeps its controls reachable. Verified pinned at scroll 3100. |
| Leaderboard bounded to 440px, scrolls in place | 6 enumerators today, dozens at rollout — it would otherwise become the page. |
| Tighter type and spacing; tables fill their panel | Auto-width left the case list short of the card edge, which reads as a fault on a wide canvas. |

**A composition I tried and reverted.** The first cut put the trend chart and the enumerator
leaderboard side by side. Rendering it showed why that is wrong: the leaderboard is a
ten-column table, cut off at 714px, with a tall dead gap beside the short chart. Tableau and
Power BI do not squeeze wide tables into half columns either — wide tables get the full
canvas. The summary *tiles* are what pair, which is how the KPI header band came about.

Verified at 1760 / 1366 / 1024px: no horizontal page scroll, zero console errors, coverage
rendering 28 rows at every width.

---

### Two real bugs found by driving the page, not by reading it

1. **`(null%)` published live.** The small-base rule (F1/F2, previous pass) returns `null` for
   a suppressed rate. Table cells handled it; the per-instrument *summary* line concatenated
   it straight into a string, so F3 and F4 read **"11 / 10 completed (null%)"**. Now reads
   "rate withheld — plan under 25".

2. **The enumerator filter was silently ignored** by the instrument cards and every
   per-instrument chart. `pass(row, ignoreStatus, ignoreEnum)` was handed directly to
   `Array.filter`, which supplies `(element, index, array)` — so `ignoreEnum` received the
   array (**always truthy**) and `ignoreStatus` the index (truthy after row 0). A supervisor
   filtering to one enumerator saw a KPI of 6 above cards still totalling 118, and charts
   still plotting the whole team. Fixed to `.filter(r => pass(r))`; cards now sum exactly to
   the KPI under both enumerator (6) and status (2) filters.

---

## Verification performed

Driven in a real browser, signed in, against the deployed page — not inferred from the
generator source:

- **0 console/page errors** at every step
- coverage renders **28 rows from the fetched plan** (payload `targets` is `{}`, so this can
  only come from `plan.json`)
- comparators, groups, universes, headings all present; 19 charts; 119 case rows
- **`plan.json` returns 401 anonymously** and 200 signed-in — see the security note below
- desktop 1600px and tablet 1024px: **no horizontal page scroll**
- cron regenerated both files unattended on its 2-minute schedule
- worktree and `/opt` generator md5 identical

### Security note — a leak that was almost introduced

`plan.json` is a *new* file, and `/docs/.htaccess` gates by **filename**. It matched no
`FilesMatch` block, so it would have been served **unauthenticated** — the full 1,521-facility
assignment plan. It was added to the tiered monitoring block *before* the file was ever
created, and the `Require user` line was asserted byte-identical so the admin console's own
rewriting is unaffected.

**Any future sidecar file under `/docs/` inherits this trap.** Gate first, generate second.

---

## Still open

| Item | Note |
|---|---|
| **Phone ≤430px page overflow** | Isolated to `.tb-right` in `portal_shell.py` — shared toolbar chrome, not dashboard content. Hiding it yields exactly 430px. Affects the map and data room too, so it is a shell fix, not a dashboard one. |
| **Option D — query API** | The only option that removes the linear term. Case rows are ≈277 B each; at ~5,000 cases they overtake the remaining fixed cost, at 20,000 the page reaches ≈5.8 MB. Revisit at rollout. |
| **Columnar row encoding** | Cheap follow-on: ≈277 → ≈90 B/case pushes the ceiling out ~3× without touching the interaction model. |
| **Option C** | Still the wrong first move; becomes worth doing only *after* D, when the overview no longer needs the rows. |

---

## For whoever picks this up

- Prod generators live in the **`f2-productivity-panel` worktree**, not `main` — deploying
  from `main` wipes features. md5 the worktree against `/opt` before and after.
- `csweb-dashboard-gen.py` contains Python strings that themselves contain `</style>`;
  anchoring an edit on `rfind("</style>")` lands inside Python source and breaks the file.
- A patch script that prints OK is **not** evidence. Regenerate, then grep the *generated
  HTML*, then load the page in a browser. Both bugs above passed every static check.
- Scripted checks need a session cookie (POST `/docs/auth/login`), not `curl -u`.
