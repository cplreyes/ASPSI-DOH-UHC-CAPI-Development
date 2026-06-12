# CSWeb 8.0.1 On-Box Patches — Survival Kit

CSWeb upgrades/re-installs overwrite the web root and wipe these patches. After any
upgrade, run **on the server**:

```bash
python3 /root/csweb-patches/apply-csweb-patches.py
```

Idempotent (skips already-applied patches); **stops loudly** if upstream changed the
code a patch targets — that usually means the bug got fixed in the new CSWeb, so
verify before forcing anything. Kit lives in two places: this vault folder (source of
truth) and `/root/csweb-patches/` on `aspsi-csweb-prod`.

## What it re-applies

| # | File | Why |
|---|---|---|
| 1 | `src/.../MySQLDictionarySchemaGenerator.php` | alpha items ≤255 chars → `VARCHAR(len)` not LONGTEXT; F1's 198-alpha-item `D_YAKAP_KONSULTA` blew InnoDB row-size error 1118 |
| 2 | `src/.../DictionarySchemaHelper.php` | execute schema DDL per-statement; the stock single concatenated `prepare()` silently skips everything after a failure, then stamps the schema valid |
| 3 | `src/.../Controller/api/ReportController.php` | `importAreaNames()` wrong return type → every successful label import 500'd |
| 4 | `templates/mapReport.twig` | Map Report defaults to the Philippines (`setView([12.88,121.77],6)`) instead of `fitWorld()` (×2 call sites) |
| 5 | `dist/css/cspro-styles.css` | sidebar submenu label wrap + View-case modal width 92vw |

Plus (idempotent): `SET PERSIST log_bin_trust_function_creators=1` and `sql_mode`
minus `ONLY_FULL_GROUP_BY`; Twig cache clear; `var/` ownership back to uid 33;
`lamp-php8` restart. MySQL `SET PERSIST` survives container restarts but **not** a
from-scratch DB container rebuild — the script re-asserts both.

## After running

1. Spot-check: Sync Report renders with facility names; Map Report opens on the PH.
2. If `cspro_area_names` was lost (DB rebuild), re-import
   `deliverables/CSWeb/f1-sync-report-labels.csv` (Sync Report page or
   `POST /csweb/api/import-area-names`). Import **replaces** the table — always the
   full combined file.
3. A dictionary re-upload after upgrade regenerates breakout schemas with whatever
   generator code is live — patch #1/#2 must be in place *before* that happens.

The `*.patch` files here are reference diffs (`diff -u --strip-trailing-cr` vs
`.orig-8.0.1` backups), not the apply mechanism.

Upstream status (2026-06-12): bugs #1–#3 confirmed still present in
`csprousers/csweb` main. If filing upstream or upgrading, check these first.

Full context: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSWeb/CSWeb-Sync-Report-and-Case-Breakout-Setup|CSWeb-Sync-Report-and-Case-Breakout-Setup]].
