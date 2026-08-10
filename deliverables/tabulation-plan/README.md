# UHC Survey Year 2 — Tabulation Plan (Epic 11)

The SSRCS-committed output-table list for the UHC Survey Year 2, scaffolded as a
machine-readable tabulation plan. This is the spec that the variable-mapping pass and the
Stata 12 tabulation do-files build against.

**Source of truth:** PSA Statistical Survey Notification Form (SSRCS Form 1), §II item 9
"List of tables and other outputs to be generated", signed 2026-06-15 —
`raw/Email-Ingest-2026-06-05/Attachments/2_DOH UHC Yr2_PSA SSRCS Form 1_signed.pdf`
(PDF pages 3–9). All 197 table descriptions are transcribed **verbatim**, including the
printed quirks (2.49a/b duplicate 2.48a/b's description; 3.24/3.25 printed identical;
4.4/4.5 printed identical; 1.21 and 4.9 "(continued)"; no plain Table 1.17 — only
1.17a/1.17b; Annex 4's printed header carries a stray "Revised Table No." column
artifact, ignored).

| Annex | Instrument | Tables | Rows |
|---|---|---|---|
| Annex 1. Facility-level | F1 | 1.1–1.32 + 1.8a/b/c + 1.17a/b | 36 |
| Annex 2. Patient-level | F3 | 2.1–2.65 (40 numbers split a=inpatient / b=outpatient) | 105 |
| Annex 3. Household-level | F4 | 3.1–3.36 | 36 |
| Annex 4. HCW-level | F2 | 4.1–4.20 | 20 |
| **Total** | | | **197** |

## Generator-first rule

`tabulation-plan.xlsx` and `tabulation-plan.csv` are **build artifacts**. Never edit them
by hand. Edit `build_tabulation_plan.py` (the table definitions live there as a Python
list of dicts) and re-run:

```
PYTHONIOENCODING=utf-8 python build_tabulation_plan.py
```

## Files

- `build_tabulation_plan.py` — the generator; holds all 197 table definitions
  (no / annex / instrument / verbatim description / stat_type / universe / breakdown /
  weight / source_variables / mapping_status / notes) and emits the workbook + CSV.
- `tabulation-plan.xlsx` — README sheet (source, counts, workflow, Stata 12 constraint)
  + Plan sheet (all 197 rows, filterable).
- `tabulation-plan.csv` — same rows, UTF-8 (BOM), for pipeline use.
- `README.md` — this file.

## Workflow

1. **This plan** — the committed table list with derived stat type / universe /
   breakdown / weight per table.
2. **Variable mapping pass** — fill `source_variables` per table from the harmonization
   codebook; flip `mapping_status` from `unmapped` to `mapped`.
3. **Stata 12 do-files** — one tabulation program per annex emitting the committed
   tables.

## Stata 12 constraint

**Target: Stata 12 SE** (portable, `C:\Users\analy\Downloads\Stata 12\StataSE.exe`; new
Stata under procurement). Tabulation programs must use Stata 12 syntax: `svyset` +
`svy: tab` / `svy: proportion` / `svy: mean` + `tabout` (user-written) for export. NOT
available: `putexcel` (13+), `collect`/`etable`/new `table` (17+), `import excel` is
available (12) but prefer the ETL's CSV/.dta. The harmonization ETL must write `.dta`
format ≤115 (pandas `to_stata(version=114)`); str244 max; 32-char variable names. All
tables are WEIGHTED (SSRCS Annex A): base weight × stage weights × non-response
adjustment = final weight `wf`; facility tables break down by facility type (911 RHU /
244 gov hospital / 366 private hospital of n=1,521), patient/HH tables by province.
