# Harmonization ETL — builds the MASTER DATASET

**This is the deliverable, not a helper.** Since the 2026-07-13 scope call
(Ma'am Myra), ASPSI's data-processing team owns table production; **Carl owns
getting the collected data out**. This pipeline's output *is* the handoff.

Implements [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/data-harmonization/etl-spec|etl-spec]]
§2.1 (CSWeb breakout MySQL, decided 2026-06-12) + §2.2 (`csweb_f2` direct,
decided 2026-07-13).

```
python run.py [--date YYYY-MM-DD] [--skip-extract]
python test_transform.py            # 20 regression tests, stdlib only
```

## What comes out — `out/<date>/`

| File | Shape |
|---|---|
| `f1_clean.csv` `f3_clean.csv` `f4_clean.csv` | one row per case, **every question column** (676 / 809 / 606 as of the Jun-12 dictionaries) |
| `f2_clean.csv` | one row per submission, answers exploded from `values_json` |
| `<inst>__<roster>.csv` | one row per (case, occurrence) — one file per repeating record |
| `shared_dimensions.csv` | the harmonized cross-instrument join layer (long format) |
| `qa_report.md` · `manifest.json` | dataset shape, gates, and what ASPSI must know |

`raw/` and `out/` hold field data — **never commit** (.gitignore'd; PII).

## Design decisions worth knowing

- **Wide-join is safe.** CSPro guarantees item names are unique *within* a
  dictionary, so the section tables (`a_*`, `b_*`, …) merge onto one case row
  with no prefixing and no collisions (verified: 682 / 821 / 645 unique columns
  across F1/F3/F4, zero clashes).
- **Rosters are discovered, not hard-coded** — any table carrying an `occ`
  column is a repeating record. This is why the F3 cost-matrix rosters added on
  2026-06-20 (`*_PAY_ROSTER`) are picked up with no code change.
- **F2 is not CSPro.** Its answers live in a `values_json` blob; we explode it,
  union-ing keys across submissions, so an F2 spec change adds columns rather
  than breaking the ETL. `case_key` = the 12-digit `qn`.
- **Credentials never leave the box.** `csweb_f2` also holds `f2_users`
  (password hashes) and `auth_*` (device/session tokens). The extract
  **whitelists** survey tables and re-checks after unpacking — if a denied table
  ever appears in `raw/`, it is deleted and the run fails loudly.
- **Long names are reported, never truncated.** 18 F1 + 9 F4 columns exceed
  Stata's 32-char variable limit. Truncation can silently collide, and the
  renaming rule is ASPSI's call — `qa_report.md` lists them. Harmless for CSV.

## Still open with ASPSI

1. **Handoff format** — CSV (emitted today; Stata reads it fine) or `.dta`? Our
   Stata is 12 SE, so a `.dta` must be format ≤115, which also forces the
   long-name decision above.
2. **Who attaches the sampling weights** (facility / patient / household / HCW
   `wf`)? Nobody has applied them; every design variable is carried through
   untouched. `manifest.json` records `"weights_applied": false` so this cannot
   be assumed by accident downstream.

## Dry-run findings (2026-06-12) — codebook drift vs as-built dcfs

Still true, still worth knowing:

1. **§10**: `DATE_STARTED`/`TIME_STARTED` no longer exist — as-built uses
   `date_first_visited`/`date_final_visit`. No time-of-day captured anywhere.
2. **§11**: `INTERVIEWER_ID` no longer exists — only free-text `enumerator_s_name`.
   Codebook expects roster IDs → ASPSI/instrument decision (open item 15.I).
3. **§9**: no explicit `consent_given` boolean in any CAPI instrument (implicit
   via the consent-terminator flow). **F2 does have it** — a real asymmetry.
4. **§13 ✓**: `language_used` exists in `field_control` on all three CAPI forms.
5. **Keys lose leading zeros** (case keys and PSGC geo items, numeric entry) —
   the transform zero-pads to canonical widths (12 / 10) before any join or slice.
6. **Duplicate F3 case key** in the test data (2× `010280001501`, one partial) —
   QA flags it; ties to the §B4 conflict-policy decision.

> The Jun-12 `raw/` snapshot is **thin and stale**: 4 desk-test cases, mostly
> empty shells, taken *before* the F3 roster fan-out. It proves the pipeline
> works end-to-end; it is not a sample of real data. The first meaningful run is
> the pretest.
