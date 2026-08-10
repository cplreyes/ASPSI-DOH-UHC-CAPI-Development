# UHC Y2 Tabulation — Stata 12 do-file skeletons

Stata 12 do-file skeletons for the 197-table UHC Y2 tabulation plan
(`../tabulation-plan.csv`), one generated block per table.

## Generator-first rule

**Never hand-edit the `.do` files.** They are all emitted by `build_dofiles.py`
from `../tabulation-plan.csv`. To change anything — command synthesis, breakdown
mapping, comments — edit the generator (or the plan CSV upstream) and re-run:

```
PYTHONIOENCODING=utf-8 python build_dofiles.py
```

Emitted files:

| File | Role |
|---|---|
| `run.do` | master runner: globals, log, `do`-chain |
| `00_import.do` | `insheet` the harmonization-ETL CSVs → `.dta` (`$ETL_DIR` is the **EDIT ME** global) |
| `01_svyset.do` | per-instrument SSRCS Annex-A survey designs |
| `10_annex1.do` | Annex 1 — F1 facility survey (36 tables) |
| `20_annex2.do` | Annex 2 — F3 patient exit survey (105 tables) |
| `30_annex3.do` | Annex 3 — F4 household survey (36 tables) |
| `40_annex4.do` | Annex 4 — F2 HCW survey (20 tables) |

## How to run

Stata 12 batch mode, from this `stata\` folder:

```
"C:\Users\analy\Downloads\Stata 12\StataSE.exe" /e do run.do
```

Output: log at `logs\run.log`, tabout tables at `out\annexN_tables.xls`,
imported data at `data\*.dta`.

## Prerequisite: tabout (one-time)

The table-export lines use `tabout`, which is not shipped with Stata:

```
ssc install tabout
```

This needs internet. **Offline alternative:** copy `tabout.ado` (and
`tabout.hlp`) from a connected machine into your PERSONAL ado folder
(run `adopath` in Stata to see it; typically `c:\ado\personal\`).

## The NOWEIGHT toggle

Sampling weights (`wf`) are computed **post-collection** and do not exist yet.
`run.do` therefore sets:

```
global NOWEIGHT 1
```

which makes `01_svyset.do` svyset every file as SRS (`svyset _n`) so all
`svy:` commands run unweighted. When weights land: merge `wf` onto each
`.dta`, build the strata/fpc variables flagged in `01_svyset.do`, set
`global NOWEIGHT 0`, and re-run.

## Outstanding TODOs

- **Weights** — `wf` arrives post-collection (see NOWEIGHT above); the real
  svyset designs in `01_svyset.do` also need the strata/fpc variables built.
- **ETL gaps** — `f2_clean.csv` (HCW) and the F3 pay/expenditure roster
  extracts are not in the ETL output yet; their import blocks are guarded
  stubs and Annex 4 / roster tables stay skipped or commented until the ETL
  grows them.
- **.dta from the ETL** — when the ETL adds native Stata output
  (transform.py §0.3), emit `saveold`-compatible **version ≤115 (Stata 12)**
  .dta files and swap `00_import.do` from `insheet` to plain `use`.
- **f_type / breakdown dims** — facility type comes from the facility
  master-list join (see plan notes); some breakdown dimensions (age group,
  role, member type, SES, ...) have no standard bygroup variable yet and are
  flagged `TODO` in-block.
- **Blocks commented out by design** — `partial` rows (decision visible
  in-file), `gap` rows (nothing runnable), `DERIVED` recipes, checkbox
  split-to-dummies stubs, and roster-dependent tables.

## Stata 12 syntax rules (enforced by the generator)

`version 12` at the top of every do-file; no putexcel / no Stata-13+ delimited
import / no collect/etable/frames; strings ≤244 chars; `insheet` + `tabout` +
`svy:` prefix; `log using ..., text replace`; emitted files are pure ASCII.
