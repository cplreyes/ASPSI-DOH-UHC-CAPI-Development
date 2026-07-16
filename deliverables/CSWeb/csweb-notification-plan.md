# CSWeb Sync Dashboard — Notification Plan

**Surface:** the notification **bell** on `https://csweb.asiansocial.org/docs/dashboard.html`
**Goal:** in near-real-time, tell whoever is watching the dashboard *who synced, what they synced, and anything that needs a human to act* — without ever touching the enumerators' case data.
**Status of this doc:** living plan. Marks what is **LIVE on the box today** vs. **PROPOSED**. First written 2026-07-15 (Mayondon pretest day).

---

## Guardrails (non-negotiable)

- **Read-only.** The whole notification layer reads sync metadata + case *keys / timestamps / counts* only. It never reads case content and never writes to any case table. Nothing here can affect a device's pretest data.
- **Stateless & non-destructive.** Counts are derived from immutable timestamps (`created_time` / `modified_time`), so a re-run or a re-sync can never overwrite or retroactively change a past bell entry. (This is the fix from the 2026-07-15 "3 new → no new" overwrite bug.)
- **On-box, no app change.** All of it runs from `/opt/*.py` on the CSWeb host via cron. The CAPI apps, CSWeb itself, and the sync protocol are untouched — "locked in for pretesting."
- **Sensitive mapping stays off public surfaces.** The `se-00x → surname` roster is baked into the on-box generator only. Never echo that mapping into a public GitHub issue, Slack post, or committed file.

---

## How it works (architecture)

```
CSWeb MySQL (csweb_uhc_y2)                     on-box cron                         dashboard.html
──────────────────────────                     ───────────                         ─────────────
cspro_sync_history (direction='put')  ─┐
FACILITYHEADSURVEY_DICT   (F1 / dict4) ─┤   csweb-sync-feed-gen.py  ── writes ──►  docs/sync-feed.json
PATIENTSURVEY_DICT        (F3 / dict5) ─┼──►   (cron: every minute)                        │
HOUSEHOLDSURVEY_DICT      (F4 / dict6) ─┘                                                   │  bell polls
/opt/targets.json  (assignment plan) ──────────────────────────────────────────────►  every ~20s
```

- **Generator:** `deliverables/CSWeb/csweb-sync-feed-gen.py` → deployed to `/opt/csweb-sync-feed-gen.py`, cron `* * * * *` (1-min), writes `/opt/app/lamp/www/docs/sync-feed.json`.
- **Client:** a self-contained bell block (style + markup + poll/render/notify script) injected into the dashboard by `csweb-dashboard-gen.py` before `</body>`. Polls `sync-feed.json` every ~20s, renders the panel, fires an OS notification on genuinely new cases, and shows a red badge for open alerts.
- **Feed shape:** `{ generated, count, events[], alerts[] }`
  - `events[]` = one entry per **sync session** (a device's uploads within a 300s window, deduped across dictionaries): `{rev, user, name, device, items:[{inst,new,edited}], total_new, total_edited, time}`.
  - `alerts[]` = data-quality flags, newest first, capped at 30.

### New vs. edited attribution (the rule that prevents overwrites)

- A case is **NEW** in a session when its `created_time` (first CSWeb insert, fixed forever) equals that sync's timestamp.
- A case is **EDITED** in a session when its `modified_time` (> `created_time`) equals a later sync's timestamp.
- Both timestamps are written in the same transaction as the matching `cspro_sync_history` put, so cases attach to the exact session that carried them, per instrument. No per-run recompute can move a count off a past entry.

---

## Notification catalog

Three categories. **Detectability** = can the box already see it from data on hand, or does it need a new field surfaced first.

### A — Activity (informational; no action needed)

| ID | Notification | Trigger | Message format | Status |
|----|--------------|---------|----------------|--------|
| A1 | **Device synced** | new `cspro_sync_history` put row, grouped into a session | `KPura se-005 synced · F1: 4 new cases` | ✅ **LIVE** |
| A2 | **Re-sync / edits** | same session, `edited > 0` | `ASalazar se-003 synced · F4: 3 edited` | ✅ **LIVE** (part of A1) |
| A3 | First sync of the day per enumerator | first put by a user after local midnight | `PCrudo se-007 — first sync today` | ○ Proposed |

### B — Progress (positive milestone)

| ID | Notification | Trigger | Message format | Status |
|----|--------------|---------|----------------|--------|
| B1 | **Facility target reached** | non-deleted case count for a `code9` ≥ its `targets.json` target | `🎯 Mayondon (F4) reached 20/20` | ○ **Proposed — next build** (data already on box) |
| B2 | Facility near target | count ≥ 80% of target | `Mayondon (F4) at 16/20` | ○ Proposed |
| B3 | Replacement drawn | `BREAKOFF ∈ {5,6,7}` on a case | `↔ Replacement drawn — se-003, Mayondon` | ○ Proposed (needs BREAKOFF in a queryable column) |

### C — Data-quality alerts (🔴 action needed — red badge)

| ID | Notification | Trigger | Message format | Status |
|----|--------------|---------|----------------|--------|
| C1 | **Duplicate / colliding case key** | `GROUP BY caseids HAVING COUNT(*)>1` within a dict | `🔴 F4 key 040341101… synced twice — se-003, se-005` | ✅ **LIVE** |
| C2 | **Case outside the assignment plan** | `code9 ∉ targets.json[inst]` | `🔴 F4 code 040341101 not in plan — se-005` | ✅ **LIVE** |
| C3 | Wrong / future interview date | on-form interview date > sync date (the "cases yesterday" class) | `🔴 F1 case dated 2026-07-14 — se-001` | ○ Proposed (needs date field surfaced) |
| C4 | Break-off without disposition | BREAKOFF set but no Result-of-Visit / CASE_DISPOSITION | `🔴 F3 break-off, no disposition — se-002` | ○ Proposed (needs fields) |
| C5 | GPS missing (satellites = 0) | map-layer already computes unreported GPS | `🔴 F4 case, no GPS fix — se-003` | ○ Proposed (reuse map-gen) |
| C6 | Sync after field cutoff | put `created_time` outside allowed window | `⚠ se-004 synced 21:14 (after cutoff)` | ⏸ **Deferred by choice** (you skipped this one) |

---

## What's live right now (pretest state)

- **A1 + A2** — every device sync shows in the bell with per-instrument new/edited counts; OS notification fires on new cases only.
- **C1** — duplicate case-key detector (currently 0 dups).
- **C2** — off-plan detector against the real Mayondon/Bayog/RHU/LPH-Bay/LBDH/St-Jude plan in `targets.json` (validated: wrong plan → the F4 codes light up correctly).

Everything else in the catalog is **proposed** and not yet emitting.

---

## Build order (recommended)

1. **B1 — Facility target reached** 🟢 *do first.* No new data needed: the generator already reads both case counts and `targets.json`. Add a `progress[]` block to the feed (`{inst, code9, name, count, target}`) and a bell line when `count == target`. This turns the dashboard into a live "are we done here yet" board and pairs naturally with the Coverage-vs-target KPI.
2. **C3 — Wrong / future interview date.** Highest-value quality alert (already bit us once). Needs the on-form interview-date column surfaced to a queryable field; then trigger is a simple date comparison.
3. **C5 — GPS missing.** Cheapest of the remaining: `csweb-map-gen.py` already flags satellites=0; lift that signal into the alert feed instead of recomputing.
4. **B3 / C4 — Replacement & break-off-without-disposition.** Both blocked on BREAKOFF / disposition being readable off-form; build together once those columns are available.
5. **A3, B2** — nice-to-have polish; do only if asked.
6. **C6 — after-cutoff.** Left deferred unless a cutoff policy is set.

---

## Open decisions (yours / ASPSI's)

- **B1 threshold source:** fire on the **day-plan** target (F3 = 5) or the **code reserve** (F3 = 10)? Affects when "target reached" pops. Current `targets.json` uses the day-plan numbers and is still `provisional: true`.
- **C3 policy:** treat any interview date ≠ sync date as a flag, or only *future* dates? (Aly's case was a past mis-date.)
- **Confirm build order** above, or reprioritize.

---

## File map

| File | Role |
|------|------|
| `deliverables/CSWeb/csweb-sync-feed-gen.py` | generator for `sync-feed.json` (events + alerts) → `/opt/` |
| `deliverables/CSWeb/csweb-dashboard-gen.py` | injects the bell (style/markup/poll script) into `dashboard.html` → `/opt/` |
| `deliverables/CSWeb/csweb-map-gen.py` | map + GPS layer (source for future C5) |
| `deliverables/CSPro/data/assignments/assignments-source.csv` | the assignment plan (source of truth) |
| `deliverables/CSWeb/gen-targets.py` | builds `targets.json` from the source CSV (`--final` drops the PROVISIONAL banner = DOH-facing gate) |
| `/opt/targets.json` (on box) | plan the off-plan + target detectors read |

> ⚠️ **On-box drift:** the live `/opt/csweb-dashboard-gen.py` runs ~150 lines ahead of git. Pull the live copy before editing; don't overwrite it from the repo version.
