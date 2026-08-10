# PSGC dataset — provenance & refresh

**Source publication:** PSA *Philippine Standard Geographic Code (PSGC) 1Q 2026 Publication
Datafile* (`PSGC-1Q-2026-Publication-Datafile.xlsx`, in this folder; downloaded 2026-04-20 from
psa.gov.ph → Classification Systems → PSGC).

**Pipeline:**

```
PSGC-1Q-2026-Publication-Datafile.xlsx
  → py parse_psgc.py            # xlsx → 4 CSVs (code,name,parent columns), this folder
  → py build_psgc_lookups.py    # CSVs → ../../shared/psgc_*.dcf + .dat (fixed-width, CSPro 8.0)
```

Consumers: the four `shared/psgc_*` lookup dictionaries ride every instrument deploy
(listed in each `.csds`; per-instrument copies are gitignored). The case-key PSGC gate
validates the 12-digit QN geo-prefix against these at entry field 1.

**Current build (verified byte-identical on the 2026-07-03 restructure):**

| Level | Rows |
|---|---|
| Regions | 18 |
| Provinces / HUCs | 117 |
| Cities / Municipalities | 1,658 |
| Barangays | 42,010 |

**Refresh procedure (PSA publishes quarterly):** drop the new publication xlsx here →
update the `XLSX` filename in `parse_psgc.py` → run the two commands above → record the
new quarter + row counts in this file → redeploy all instruments (the lookups ship inside
each package; a PSGC refresh is a data change riding a normal versioned deploy — bump
PATCH via `stamp_version.py`).

> Field-key caveat: mid-collection PSGC refreshes change the valid geo-prefixes for the
> case-key gate — never refresh mid-round without checking already-collected QNs remain
> valid against the new codes.
