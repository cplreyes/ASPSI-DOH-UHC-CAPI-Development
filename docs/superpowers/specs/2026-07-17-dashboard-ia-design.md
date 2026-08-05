# Sync Dashboard — information-architecture redesign (Option A)

**Date:** 2026-07-17 · **Status:** approved forks, spec for review
**Decision trail:** audit → options diagram `docs/diagrams/2026-07-17-dashboard-ia-options.png` → Carl chose **A — Purpose bands + rollup**, **region → province two-level** coverage grouping, **detail charts collapsed by default**.

## Problem

`/docs/dashboard.html` grew 7 feature layers in 10 days with no layout pass. The acute pain: the real F1 plan (1 target per sampled facility) makes **Coverage vs. target render 1,521 flat table rows** — ~90% of the page scroll, 1,515 of them reading `1 · 0 · 0% · 1`, rebuilt in the DOM on every filter change — while only 35 real cases exist behind the whole page. Secondary: sections are interleaved in accretion order (instrument cards stranded after productivity), quality signals live only in the transient bell, and the coverage provenance banner mislabels the real 2026-07-15 pretest plan as the "R6 fixture (placeholder)".

## Goal

One page, five purpose bands, coverage readable at national scale, quality signals with an on-page home. No data model changes, no SQL changes, no new files on the box.

## Non-goals

- The notification bell: **untouched** (feature and code block).
- The Map Report: untouched (targets.json shape unchanged — label string only).
- No chart removals (the Status-doughnut/KPI redundancy is noted, not acted on).
- No tabs, no pagination libraries, no external deps (CSP-style: everything stays vendored/inline).
- Enumerator-productivity logic: unchanged (it only moves and gains a collapsed note).

## Page order (after)

```
Header · Filters ×7 (unchanged, incl. Reset)
1 STATUS NOW    KPI strip ×6 + instrument cards (moved up) + single freshness line
2 PROGRESS      Submissions-over-time · Coverage vs. target (accordion, below)
3 TEAM          Enumerator productivity (note collapses behind ⓘ)
4 DATA QUALITY  new panel (below)
5 DETAIL        per-instrument chart sections ×4, collapsed by default
Footer          source line + Map Report link (drop duplicated freshness text)
```

## Band 2 — Coverage accordion (the core change)

**Data:** `targets.json` rows already carry `region`, `province`, `name`, `target` — grouping needs no regeneration. Grouping keys come **only from the targets' own strings** (never joined to case-row region names, which are survey-internal and word-reordered — the known name-mismatch trap).

**Structure per instrument:** summary line (unchanged) → region rows (Σ facilities · expected · landed · % · shortfall · bar) → click region → province rows → click province → facility table (today's row rendering, scoped to that province, column-sort preserved via `covSort`).

**Behavior:**
- Default: all regions collapsed; regions with `landed > 0` auto-expand to province level (provinces with activity auto-expand to facilities). Today that means Region IV-A → Laguna open, 16 region rows closed — the whole section fits on one screen.
- Expansion state in a `Set` keyed `inst|region` / `inst|region|province`, preserved across `render()` calls (filter changes don't collapse what you opened). User toggles override the auto-expand defaults.
- Search box per instrument: matches facility name/code, shows only matching facilities with their ancestor rows force-expanded; empty search restores normal state.
- Landed scoping stays exactly today's: `pass(r, ignoreStatus=true, ignoreEnum=true)`; targets are always the full plan (the Region filter scopes *landed*, never the denominator — same as the current flat table).
- Region/province rows sort by % desc (nulls last) then name; facility tables keep the click-to-sort headers.
- Provenance banners and the "Landed = …" note stay, with the note collapsed behind ⓘ (see shared fixes).

## Band 4 — Data quality panel (new)

Four tiles, each expandable to a short list; computed client-side from the existing payload + the existing sync-feed poll. Honors instrument/region/date filters; **ignores the Status filter**; F2 excluded from the GPS tile (self-administered, `gps` is a deliberate constant — must never count).

| Tile | Source | List columns |
|---|---|---|
| No GPS fix | `r.gps=='0'` (F1/F3/F4 only) | inst · facility/area · enumerator · date |
| Stale partials | `status=='Partial'` and `date` > 2 days before `P.today` | inst · area · enumerator · date (age) |
| Out-of-plan completes | Completed with `code9 ∉ targets` (today's `untarget`, now itemized) | inst · code9 · area · enumerator |
| Live alerts | mirror of the bell's `alerts` (dup case keys, out-of-plan) from `/docs/sync-feed.json` | as the bell renders them |

The Live-alerts tile does its **own** 20-second fetch of `/docs/sync-feed.json` (a second tiny GET of a static file) so the bell's IIFE stays byte-identical — "bell untouched" is literal, not approximate.

## Band 5 — Collapsible instrument sections

Each section's `h2` becomes a toggle row (`▸ F1 — Facility Head Survey · 6 charts · N cases`), collapsed by default. **Chart.js cannot init on a hidden canvas**: charts for a section are created lazily on first expand (and destroyed/rebuilt on filter changes only if the section is open). The F2 freshness/api note stays visible in the collapsed header row so an F2 outage is never hidden.

## Shared fixes

- Instrument cards (`#totals`) move into Band 1 under the KPI strip; card click = set instrument filter (matches leaderboard-row behavior).
- The 15-line productivity note and the coverage note each collapse behind an `ⓘ how to read` toggle (plain `<details>`).
- One freshness line (Band 1); footer keeps source + Map link only.
- `targets.json` regenerated once with `--f1-from-facilities --plan-label "Pretest assignment plan 2026-07-15 (provisional)"` — label-only change; shape untouched; deployed alongside (feeds BOTH dashboard and map — verify map banner text still renders sensibly).
- Bell code block untouched.

## Implementation & deploy

- **Base file:** the live box copy (`/opt/csweb-dashboard-gen.py`, 1,080 lines, scp'd down 2026-07-17) — it is ahead of main and the worktree; the repo copies are NOT the deploy source (generator-drift rule).
- **Off-box verification first:** build with `--sample` fixture mode, open the generated HTML headlessly (Playwright chromium), screenshot each band, verify accordion/quality/collapse behavior before any deploy.
- **Deploy sequence:** timestamped backup on box → scp generator + targets.json → run generator once → verify live page → 2-min cron takes over. Prod SSH is classifier-gated; hand `!` commands to Carl if blocked.
- **After deploy:** sync the final generator back over the `f2-productivity-panel` worktree copy so the drift note stays true (main untouched — Carl's call).

## Risks & mitigations

- Hidden-canvas Chart.js init → lazy create on expand (explicit design above).
- Accordion state lost on re-render → state Set lives outside `render()`.
- Region-name mismatch between targets and case rows → grouping uses targets' strings only; case rows only ever contribute to *landed* via `code9`, which is already the join key.
- `targets.json` is a two-surface contract → only the label string changes; map re-checked after deploy.
- Mid-pretest safety → off-box sample render first; deploy is one reversible file swap with an on-box backup.
