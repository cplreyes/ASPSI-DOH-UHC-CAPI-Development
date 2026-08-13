# Sync Dashboard — Reporting & Visualization Audit

**Surface:** `https://capi.asiansocial.org/docs/dashboard.html`
**Reviewed:** 2026-07-29 · lens: data analyst / reporting analyst
**Basis:** rendered page (348 KB), chart config, filter set, accessibility markup

---

## Verdict

The dashboard is **operationally strong and statistically under-guarded**. As an
operations monitor — is data arriving, from whom, from where, how fresh — it does its
job well and several hard things are already right. As a *reporting* surface, whose
screenshots will end up in DOH decks, it currently lets a reader draw conclusions the
data cannot support. Nearly every finding below is about **denominators, bases and
labelling**, not about visual polish.

The single highest-value fix is small-base suppression (F1). Everything else is
secondary.

---

## What is already right — do not regress these

| | |
|---|---|
| **Measured freshness** | The status pill is computed from real generation age, not a hardcoded "live" string. Rare and correct. |
| **Provisional denominators are flagged** | F3/F4 coverage carries a PROVISIONAL badge; F1 uses the real 1,521-facility plan. Most dashboards silently divide by a guess. |
| **Phase / activity separation** | Pretest, training and survey are separable at source, so figures aren't a blend of incomparable periods. |
| **Deliberate filter exclusion** | Coverage-vs-plan intentionally ignores the enumerator filter, because the plan assigns facilities, not people. Correct reasoning — but see F6. |
| **Export carries filter state** | CSV reflects what you're looking at, so numbers can be reproduced off-platform. |

---

## Findings

Severity: **H** = can cause a wrong decision · **M** = misleads or slows reading · **L** = polish

### F1 · No small-base suppression — **H**

There is no suppression, flagging or minimum-base rule anywhere in the page (zero
matches for suppress / n<5 / unstable). With ~118 pretest cases spread across 7
filters — instrument, region, supervisor, enumerator, status, phase, activity — a
user can trivially reach a cell of n=1 or n=2, and the dashboard will render it as a
confident percentage.

**Why it matters:** "50% of health workers in Region X report Y" on a base of 2 is
not a finding, it is noise with a decimal point. Screenshots outlive their context.
There is also a disclosure edge: at n=1 a "percentage" is one identifiable person.

**Fix:** adopt a house rule — show the base everywhere, grey/suppress percentages
below n=25 and mark n<5 as `–` with a footnote. Wire it once in the render helper so
it applies to every derived figure at once.

### F2 · Percentages are shown without their base — **H**

Percentages are computed as `Math.round(100*landed/exp)` and rendered as integers.
The base is not displayed alongside. A rounded integer hides both the base and the
precision — 1/3 and 33/100 both print "33%".

**Fix:** always render `33% (n=3)`. Never a percentage without its denominator.

### F3 · Dual-axis combo chart invites false reading — **H**

"Submissions over time — new per day & cumulative" is one chart with **two y-axes**
(`yAxisID:'y'` bars, `yAxisID:'y2'` line). Dual-axis charts are the most reliably
criticised pattern in reporting practice: the two scales are set by the tool, so the
crossing point and apparent correlation are artefacts of scaling, not data.

Worse here, the cumulative line **only ever rises**, so the chart reads as healthy
growth even on a day when zero cases arrived. That is the exact failure mode a
fieldwork monitor must not have.

**Fix:** split into two stacked panels sharing an x-axis — daily bars on top (with a
7-day rolling mean), cumulative-vs-target below. If one chart must stay, drop the
cumulative series and put cumulative in a KPI tile instead.

### F4 · KPI tiles are bare counts with no reference — **M**

Six tiles: Cases (filtered), Completed, Partial, Visited today, Replacements, No GPS
fix. Each is a number with no target, no prior period and no trend. A number without
a reference point cannot answer "is this good?" — the only question a KPI exists to
answer.

**Fix:** give each tile a comparator — vs plan, vs yesterday, or a sparkline. "Visited
today: 12" becomes "12 today · 7-day avg 9".

### F5 · Progress and data-quality metrics are mixed in one row — **M**

"No GPS fix" and "Replacements" are *quality/exception* measures sitting in the same
visual row as *progress* measures (Cases, Completed, Visited today). Equal styling
implies equal kind, so a rising exception count reads as achievement.

**Fix:** separate into a "Progress" group and a "Needs attention" group, and style
exceptions so up = bad is visually obvious.

### F6 · The deliberate filter exclusion isn't stated where it bites — **M**

Coverage-vs-plan ignores the enumerator filter by design (facilities are assigned to
places, not people). The reasoning is sound and documented in the page's explanatory
copy — but a user who filters to one enumerator sees the coverage panel *not change*
and will reasonably conclude the panel is broken, or worse, that this enumerator
covered everything.

**Fix:** when the enumerator filter is active, badge the coverage panel inline:
"Not filtered by enumerator — coverage is measured against facility assignments."

### F7 · Only two headings on the whole page — **M**

The page exposes one `h2` (Case list) and one `h3` (the trend chart). Every other
section is visually grouped but unlabelled, so the document has almost no outline:
hard to scan, hard to reference in a meeting ("the third block down"), and
unnavigable by keyboard or screen reader.

**Fix:** one heading per section, phrased as the takeaway rather than the object —
"Coverage against plan", "Who is submitting", "Data quality exceptions".

### F8 · Tables and charts are not accessible — **M**

Measured: `<caption>` 0 · `<th scope>` 0 · `alt` 0 · `role` 1 · `aria-label` 9. The
case-list table has no caption and no header scoping, so a screen reader cannot
associate cells with headers. The chart is a bare `<canvas>` with no text
alternative. For a DOH-facing government deliverable this is both an inclusion and a
procurement-risk issue.

**Fix:** add `<caption>`, `scope="col"` on headers, and give the canvas an
`aria-label` plus an adjacent visually-hidden data table (Chart.js can emit one).

### F9 · 95 distinct hardcoded colours — **M**

The page carries 95 distinct hex values with no constrained palette, despite
`portal.css` already defining design tokens. Consequences: no guarantee that green
means the same thing in every panel, no contrast guarantee, and near-certain failure
for the ~8% of men with red-green colour deficiency if status is encoded by hue
alone.

**Fix:** collapse to the existing tokens plus one colour-blind-safe categorical ramp;
never encode status by colour alone — pair with a glyph or text.

### F10 · No visible "as of" stamp on the artefact itself — **M**

Freshness is computed and shown as a pill, but the page carries no prominent
"Data as of 14:32, 29 Jul 2026 (Manila) · refreshes every 2 minutes". Dashboard
screenshots are pasted into decks and circulated; undated, they are indistinguishable
from current data weeks later.

**Fix:** a dateline in the header, in Manila time, with the refresh cadence stated.

### F11 · Rounding to integer percent on small bases — **L**

`Math.round` on tiny denominators produces jumpy figures (one case moves a
percentage by several points) and implies precision the base cannot carry.

**Fix:** falls out of F1/F2 — suppress below the threshold, show the base above it.

### F12 · No explicit universe statement per panel — **L**

Each panel's population is implied by the filter bar rather than stated. The
tabulation plan already writes universes explicitly ("all facility heads, n=1,521") —
the dashboard should borrow that discipline.

**Fix:** a one-line universe under each panel title.

---

## Status — all 12 findings closed, 2026-07-29

| | Finding | Status |
|---|---|---|
| F1 · F2 · F11 | small-base suppression, bases shown, rounding | **done** — `MIN_BASE = 25`; suppressed rates render as an em dash, counts stay visible |
| F3 | dual-axis combo chart | **done** — cumulative replaced by a trailing 7-day mean on the same axis; the dead second axis is now removed too |
| F4 | KPI comparators | **done** — every tile carries a reference point |
| F5 | progress vs exception metrics | **done** — two labelled groups, exceptions set off by a rule and a ⚠ glyph |
| F6 | filter-scope statement | **done** — inline badge, shown only while the enumerator filter is active |
| F7 | headings / page outline | **done** — 12 `h2`, full outline |
| F8 | table + chart accessibility | **done** — `scope="col"`, chart `role="img"` + `aria-label` |
| F9 | palette discipline | **done** — Okabe-Ito colour-blind-safe ramp; green/red pair removed from the coverage scale |
| F10 | "as of" stamp | **done** — Manila dateline with refresh cadence |
| F12 | per-panel universe | **done** — one line under each panel |

Two defects found while verifying, both fixed: a live **`(null%)`** in the coverage summary,
and the **enumerator filter being silently ignored** by the instrument cards and charts.
Detail in `sync-dashboard-bi-redesign-brief.md`.

---

## Recommended order

1. **F1 + F2 + F11** — one change to the render helper: base always shown, percentages
   suppressed under threshold. Removes the whole class of small-base misreading.
2. **F3** — split the dual-axis chart. Highest visual-credibility gain.
3. **F10 + F7** — dateline and section headings. Cheap, makes screenshots self-describing.
4. **F4 + F5** — KPI comparators and progress/exception separation.
5. **F8 + F9** — accessibility and palette discipline before any external release.
6. **F6 + F12** — inline universe and filter-scope labelling.

---

## Note on scope

This audits the dashboard **as a reporting artefact**. It is not a statistical review
of the survey estimates themselves — the dashboard shows unweighted operational
counts, and nothing here should be read as validating weighted estimates, which come
from the Stata lane and remain unbuilt.
