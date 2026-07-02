---
title: "CSWeb Sync Report + Case Breakout — Setup Record & Ops Notes"
category: deliverable
tags: [capi, cspro, csweb, sync-report, breakout, data-settings, elestio, e4-csweb]
last_updated: 2026-06-12
status: live
---

# CSWeb Sync Report + Case Breakout — Setup Record & Ops Notes

Done 2026-06-12 (UTC 2026-06-11 ~17:40–18:00) on `aspsi-csweb-prod` (Elestio, `csweb.asiansocial.org`). Fixes the Sync Report tab showing *"To view report add a configuration and process the cases"* with an empty report. Companion to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSWeb/Elestio-CSWeb-Deploy-Guide|Elestio-CSWeb-Deploy-Guide]].

## Why the tab was empty (root causes, 3 layers)

1. **No Data Settings configuration.** CSWeb's Sync/Map Reports read from per-dictionary "breakout" databases (cases exploded into relational tables). The config lives in `cspro_dictionaries_schema`, normally added via **Settings → Data → Add Configuration**. It was empty — never set up post-install.
2. **No case processing.** Breakout is performed by `php bin/console csweb:process-cases`, meant to run every 5 min via cron. No cron existed.
3. **CSWeb 8.0.1 bugs (hit on F1, patched on the box):**
   - `MySQLDictionarySchemaGenerator` maps **every alpha item to LONGTEXT**. F1's `D_YAKAP_KONSULTA` record has 198 alpha items → MySQL error **1118 "Row size too large (> 8126)"** (InnoDB caps ~196 TEXT/BLOB columns per table).
   - `DictionarySchemaHelper::createDictionarySchema()` executes ALL schema statements as **one concatenated PDO `prepare()`** — errors after the first statement are **silent**, so the schema half-creates (everything after `d_yakap_konsulta` was skipped), then `cspro_meta` is stamped and `IsValidSchema()` returns true forever after. Symptom: F1 job stuck `status=1`, log error `1146 Table 'csweb_f1_breakout.d_yakap_konsulta' doesn't exist`.
   - Upstream `csprousers/csweb` main (8.1-prep) still has both bugs as of 2026-06-12 — worth filing/re-checking before any CSWeb upgrade.

## What is now in place

### Breakout databases (MySQL, `lamp-mysql8`)
| Dictionary | Breakout DB |
|---|---|
| `FACILITYHEADSURVEY_DICT` (F1) | `csweb_f1_breakout` |
| `PATIENTSURVEY_DICT` (F3) | `csweb_f3_breakout` |
| `HOUSEHOLDSURVEY_DICT` (F4) | `csweb_f4_breakout` |

All `utf8mb4`, owned by `csweb_user@'%'` (GRANT ALL on each). Config rows inserted into `csweb_uhc_y2.cspro_dictionaries_schema` exactly as `DataSettings::addDataSetting()` does (`host_name=database`, password via `AES_ENCRYPT(pw,'cspro')`, `additional_config=null` = include everything).

### Source patches on the box (backups beside each file, suffix `.orig-8.0.1`)
- `src/AppBundle/CSPro/Dictionary/MySQLDictionarySchemaGenerator.php` — alpha items with length ≤ 255 now map to `VARCHAR(item length)` (new `COLUMN_TYPE_STRING`); longer alphas stay LONGTEXT. Better typed and kills the row-size blowup (F1 D-section columns are now `varchar(1)`/`varchar(2)`/`varchar(4)`).
- `src/AppBundle/CSPro/DictionarySchemaHelper.php` — `createDictionarySchema()` executes schema statements **one by one** (`executeStatement` per statement); a failure now throws loudly and `cspro_meta` is not stamped, so the next run retries instead of silently corrupting.

- `templates/mapReport.twig` — Map Report default view set to the Philippines (`setView([12.88, 121.77], 6)`) in both places stock CSWeb calls `fitWorld()` (init + after points load); CSWeb never auto-fits to pins, so the world view was permanent otherwise. Twig cache cleared + `var/cache`/`var/logs` re-chowned to uid 33 after the console run (2026-06-12, cosmetic).
- `src/AppBundle/CSPro/Data/MySQLQuestionnaireSerializer.php` — **Patch #6 (2026-06-25): the breakout-blocker.** `fillItemValues()`'s single-occurrence (`occurs == 1`) branch bound the item value with **no array guard** (only the `occurs > 1` branch flattened arrays). A binary **Image** item — the #713 verification photo (off-form, `contentType` image) — arrives as an **array** in the synced case JSON, so `serializeRecord` passed an array to PDO `bindValue()` → `ErrorException: Array to string conversion` → the **entire F3/F4 breakout job threw and wrote 0 cases** (job stuck `status=1`, `cases_processed=NULL`). F1 was spared only because its test cases carried no photo (`binary_data = 0`). **Symptom:** after any F3/F4 redeploy (which drops + reprocesses the breakout DB), the Sync Report / Map Report / `dashboard.html` / `map.html` showed fewer cases than the CSWeb Data tab (synced devices). **Fix:** guard the branch — an array value (binary/blob, no scalar column) is logged + nulled; lossless for reporting since the photo bytes live in `<DICT>_case_binary_data` and sync separately. Backup `.orig-8.0.1`; marker `array value (binary/blob in scalar column)`; in `apply-csweb-patches.py` (now 6 patches). **Recovery used:** reset stuck jobs `UPDATE <db>.cspro_jobs SET status=0, cases_processed=NULL WHERE status<>2;` → `process-cases` → counts verified `source == breakout` (F1 9/9, F3 12/12, F4 9/9) → regen dashboard + map.
- `dist/css/cspro-styles.css` — two appended UI rules (2026-06-12, cosmetic): (a) sidebar submenu items wrap (`overflow-wrap: anywhere`) — long dictionary labels like `(FACILITYHEADSURVEY_DICT)` overflowed the white Sync/Map Report submenu box; (b) `#pointInfoModal .modal-dialog { max-width/width: 92vw }` — the "View case" modal's inline `width:80%` is clamped by Bootstrap's `modal-lg` 800px max-width, clipping the record tables (used by both Sync Report and Map Report).

> [!warning] A CSWeb upgrade overwrites all four patched files. Re-apply (or verify upstream fixed them) after any upgrade — otherwise the next F1 dictionary re-upload regenerates the schema with stock code and fails again.

### Cron + logging (host crontab, root)
```
* * * * *   flock -n /tmp/csweb-process-cases.lock docker exec lamp-php8 sh -c "cd /var/www/html/csweb && php bin/console csweb:process-cases" >> /var/log/csweb-process-cases.log 2>&1
*/2 * * * * flock -n /tmp/csweb-dashboard.lock bash -c "cd /opt/app && python3 /opt/csweb-dashboard-gen.py" >> /var/log/csweb-dashboard.log 2>&1
*/2 * * * * flock -n /tmp/csweb-map.lock bash -c "cd /opt/app && python3 /opt/csweb-map-gen.py" >> /var/log/csweb-map.log 2>&1
```
**Cadence tightened to near-real-time for fieldwork (2026-06-26):** breakout `process-cases` **every 1 min** (was `*/5`); the static dashboard + map regen **every 2 min** (was `*/15`), each now `flock`-guarded against overlap. `flock -n` skips a tick if the prior run is still holding the lock, and CSWeb's own `status=1` job-lock prevents double-processing regardless — so 1-min is safe. End-to-end latency after a device sync: Data tab instant · Sync/native-Map Report ≤1 min · dashboard.html/map.html ≤~3 min. Prior crontab backed up to `/root/crontab.bak.20260626_011638`; revert to `*/5`/`*/15` if box load ever warrants. Logrotate at `/etc/logrotate.d/csweb-process-cases` (weekly × 4, compressed). First cron run verified 17:55 UTC (2026-06-12).

### Map Report config (2026-06-12, Carl-approved choices)
`map_info` written for all 3 dictionaries (same JSON the Settings → Data UI saves): **ESRI World Street Map** basemap (no API key), GPS pairs **F1/F3 = `FACILITY_GPS_LATITUDE/LONGITUDE`** (F3 deliberately uses facility, NOT patient-home GPS — mapping patient residences needs ASPSI/DOH sign-off; switchable in Settings → Data), **F4 = `LATITUDE/LONGITUDE`** (household geo ID record). Pins appear only for cases with actual GPS fixes — the 4 desk-test cases have NULL GPS, so the map starts empty. `map_info` updates don't wipe processed data (only `additional_config` changes trigger schema regeneration).

### Verified end-to-end (2026-06-12)
- All 3 breakout schemas regenerated with the patched generator (F3/F4 wiped + redone too, so all three are consistently typed).
- All 4 synced test cases processed, jobs `status=2`: F1 `10280001001`×1, F3 `10280001501`×2, F4 `10280001601`×1.
- `/csweb/api/sync-report` returns those rows for each dictionary (OAuth-authenticated call, same headers the UI sends).

### Sync Report labels (2026-06-12)
**F1 facility-name labels LIVE** — `cspro_area_names` holds 2,363 rows from `deliverables/CSWeb/f1-sync-report-labels.csv` (generated from `F1/facility_lookup.dat`): one canonical row per facility (`<9-digit code>+001` → facility name, 1,521) **plus zero-stripped aliases for region 01–09 facilities** (842) because the desk-test case was keyed without its leading zero (`QUESTIONNAIRE_NUMBER` is alpha — no zero-fill; the FACILITY_LOOKUP auto-fill that would write the exact code is the feature blocked on Android). F3/F4 rows COALESCE back to raw codes (per-case sequences can't be pre-labeled). Three things hit on the way, all fixed:
- **MySQL 8 `ONLY_FULL_GROUP_BY` breaks the labeled report query** (error 1055) — removed from `sql_mode` via `SET PERSIST` (Carl-approved; same precedent as `log_bin_trust_function_creators` from install day). Re-apply if the DB container is rebuilt from scratch.
- **`importAreaNames()` return-type bug (stock 8.0.1)** — declares `: CSProResponse` but returns a `StreamedResponse`, so every successful import 500'd after inserting. Patched (type hint removed) in `src/AppBundle/Controller/api/ReportController.php` (backup `.orig-8.0.1`) — patch #5.
- **Label import REPLACES the whole `cspro_area_names` table** (not additive) — always re-upload the full combined CSV, never a delta.
To refresh labels (facility list changes): regenerate the CSV (canonical + alias rows) and re-import via Sync Report page or `POST /csweb/api/import-area-names` (`Content-Type: text/plain`, `x-csw-data-header: 0`).

**FULL labeling (2026-06-20).** The canonical CSV only carried the `<fac9>001` sequence, so cases with any other 3-digit case number (e.g. test cases `…101/161/169`) showed the raw code. `cspro_area_names` matches `level1` **exactly**, so to label every case number the space must be enumerated: `deliverables/CSWeb/gen-area-names-full-labels.py` expands every facility across CCC 001-999 (zero-padded 12-digit + zero-stripped 11-digit for region 01-09) → **2,360,637 rows**, emitted as a gzipped TRUNCATE+batched-INSERT loader (`area_names_full.sql.gz`, ~6.4 MB). Loaded **directly via the DB** (the HTTP import can't take 100 MB): `zcat area_names_full.sql.gz | docker compose exec -T database mysql -uroot -p"$ROOTPW"`, then a one-time **index** `ALTER TABLE csweb_uhc_y2.cspro_area_names ADD INDEX idx_level1 (level1(20))` (lookups stay fast at 2.36M rows). Backup of the prior table at `/root/area_names_backup_20260620.sql`. **Label format = `<FACILITY NAME> · <CCC>`** (facility + 3-digit case number) so each Sync Report row is readable AND distinct — important for F3/F4, which have many cases per facility. **All three instruments share this one `cspro_area_names` table** and use the same facility-anchored 12-digit QN, so F1/F3/F4 are all labeled (e.g. `BANGUI DISTRICT HOSPITAL · 001` / `· 501` / `· 601`). Refresh = re-run the generator + re-load (TRUNCATE is in the SQL; index persists). To change the label format, edit `pairs()` in the generator. For per-facility *counts*, query the breakout DBs instead (the Sync Report is one row per questionnaire_number).

## Ops notes

- With the current single-ID design (12-digit `questionnaire_number`), the report is one row per questionnaire number; geographic grouping would need the PSGC id-items as dictionary IDs.
- **Instrument-side caveat:** the questionnaire-number key should be 12-digit zero-padded; the alpha field doesn't enforce it. Verify the FACILITY_LOOKUP auto-fill writes the full zero-padded code during the F1 Android round-trip — the label aliases tolerate stripped keys, but the case key itself should be canonical.
- **Re-uploading a dictionary** (e.g. F1 redeploy) flips `IsValidSchema()` false → CSWeb **drops and recreates** that breakout DB and reprocesses all cases on the next cron tick. Expected; processed data is derived, source cases stay in `csweb_uhc_y2`.
- **Adding a new dictionary to reports**: create its breakout DB + grant, then Settings → Data → Add Configuration in the UI (works now; the AJAX path is the same code we exercised).
- **Watch**: `/var/log/csweb-process-cases.log` (cron), `var/logs/ui.dev.log` + `api-*.log` (app errors). A job stuck at `status=1` in `<breakout>.cspro_jobs` means a serialization failure — check the app log.
- **Automated monitoring (2026-06-12)**: `/opt/csweb-monitor.py` runs every 15 min via host cron — checks stuck breakout jobs (status=1 ≥20 min), dead process-cases cron (log silent ≥20 min), and new ERROR/CRITICAL lines in the app logs; 6-h per-condition throttle. Config `/etc/csweb-monitor.conf` (MAIL_TO=`aspsi.doh.uhc.survey2.data@gmail.com`, Carl-chosen). **Delivery pending**: Elestio postfix refuses unauthenticated external relay — needs either the `SLACK_WEBHOOK_URL` (#capi-development) pasted into the conf, or Elestio dashboard SMTP creds wired in. Source mirrored at `deliverables/CSWeb/monitoring/csweb-monitor.py`.
- **Patch survival kit (2026-06-12)**: `deliverables/CSWeb/patches/` (mirrored at `/root/csweb-patches/` on the box) — reference diffs for all 5 patched files + `apply-csweb-patches.py`, an idempotent marker-based re-apply script that also re-asserts both `SET PERSIST` settings, clears the Twig cache, fixes `var/` ownership, and restarts PHP. Run it after any CSWeb upgrade/re-install; it stops loudly if upstream changed the targeted code. Verified idempotent on the live box (8/8 skips, site 200).
- **Looker/harmonization tie-in**: the breakout DBs are clean relational sources (one table per record, typed columns) — candidate input for the Codebook v0.2 / BI dashboard work instead of CSV exports.
- **Reporting views (2026-06-20)** — the built-in Sync Report can only group by the dictionary's **ID items** (the dropdown is `getDictionaryIds()` → with our single-ID design that's only `questionnaire_number`). To group by anything else, `deliverables/CSWeb/gen-report-views.py` generates **`csweb_reports.sql`**: a database `csweb_reports` of SQL **views over the breakout DBs** — F1 by region/province/city/facility/ownership/service-level/result, F3 by region/patient-type/sex, F4 by region/province (12 views). It lives in its **own DB so it survives instrument redeploys** (breakout DBs get dropped+recreated; views re-bind by name). Geo NAMES come from `field_control`'s derived `region_name/province_name/city_name`; **facility** name comes from a `csweb_reports.facility_names` reference (code9→name) because the breakout `facility_name` is NULL (auto-fill blocked on Android); categorical codes are labeled with CASE maps taken verbatim from the dcf value sets. Load: `docker compose exec -T database mysql -uroot -p"$ROOTPW" < /root/csweb_reports.sql`; query e.g. `SELECT * FROM csweb_reports.vw_f1_by_region;`. Granted SELECT to `csweb_user` so BI tools can read them. Regenerate when the facility list or value sets change.
