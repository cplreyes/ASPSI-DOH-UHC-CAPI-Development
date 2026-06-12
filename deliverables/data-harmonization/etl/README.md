# Harmonization ETL (skeleton)

Implements [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/data-harmonization/etl-spec|etl-spec]] v0.2:
extract from the **CSWeb breakout MySQL databases** (decided 2026-06-12) → codebook
recodes → QA gates → analysis store. First dry-run passed 2026-06-12 against the 4
live desk-test cases.

```
python run.py [--date YYYY-MM-DD] [--skip-extract]
```

- `extract_csweb.py` — one SSH call dumps every breakout table as TSV into `raw/<date>/` (read-only).
- `transform.py` — codebook recodes. **Skeleton subset**: case key + facility block (§2),
  region_code (§1), sex (§3), visit datetimes (§10 as-built), language (§13),
  enumerator (§11 as-built), consent discovery (§9 — currently MISSING in dcfs, by design kept failing).
  `DIMENSION_TODO` lists what's not yet implemented.
- `run.py` — orchestrates; writes `out/<date>/`: `f{1,3,4}_clean.csv`,
  `f4_roster_clean.csv`, `shared_dimensions.csv`, `qa_report.md`, `manifest.json`.
  Exits non-zero on hard-gate failures.

`raw/` and `out/` hold survey data — **never commit** (.gitignore'd; field data is PII).

## Dry-run findings (2026-06-12) — codebook v0.3 vs as-built dcfs

The whole point of running early. Hard gates all pass (incl. F3→F1 facility join);
real drift found:

1. **§10**: `DATE_STARTED`/`TIME_STARTED` no longer exist — as-built uses
   `date_first_visited`/`date_final_visit` (+ visit counts/results). No time-of-day anywhere.
2. **§11**: `INTERVIEWER_ID` no longer exists — only free-text `enumerator_s_name`
   (+ team leader / validated-by / edited-by names). Codebook expects roster IDs → ASPSI/instrument decision.
3. **§9**: no explicit `consent_given` boolean in any instrument's `a_informed_consent`
   (consent likely implicit via the consent-terminator flow). Codebook §9 claim is stale.
4. **§13 ✓**: `language_used` exists in `field_control` on all three — §15.E (CAPI portion) is resolved as-built.
5. **Keys lose leading zeros** (case keys AND PSGC geo items, numeric entry) — extract
   zero-pads to canonical widths (12 / 10) before any join or slice.
6. **Duplicate F3 case key** in test data (2× `010280001501`, one partial) — QA flags it;
   ties to the §B4 conflict-policy decision.
