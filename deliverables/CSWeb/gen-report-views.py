#!/usr/bin/env python3
r"""Generate csweb_reports.sql — a reporting layer of SQL VIEWS over the CSWeb
breakout DBs (csweb_f1/f3/f4_breakout) so you can group synced cases by any
dimension the built-in Sync Report can't (it only groups by the single ID).

Lives in its own database `csweb_reports` so it SURVIVES instrument redeploys
(which drop+recreate the breakout DBs; the views re-bind by table name).

Dimensions:
  F1: region / province / city / facility / ownership / service level / result-of-visit
  F3: region / patient type / sex
  F4: region / province
Geographic NAMES come from field_control's derived region_name/province_name/
city_name. Facility NAME comes from a small reference table built from the
facility list (the breakout's facility_name column is NULL — the on-device
FACILITY_LOOKUP auto-fill is the known-blocked feature). Categorical codes are
labeled via CASE maps taken verbatim from the dcf value sets.

Usage:  python gen-report-views.py        # -> csweb_reports.sql
Load:   scp csweb_reports.sql root@<box>:/root/
        docker compose exec -T database mysql -uroot -p"$ROOTPW" < /root/csweb_reports.sql
First built 2026-06-20.
"""
import csv, pathlib

HERE = pathlib.Path(__file__).parent
SRC = HERE / "f1-sync-report-labels.csv"
OUT = HERE / "csweb_reports.sql"

# facility code9 -> name (from canonical <fac9>001 rows)
fac = {}
with SRC.open(encoding="utf-8") as f:
    for code, name in csv.reader(f):
        code = code.strip()
        if len(code) == 12 and code.endswith("001"):
            fac[code[:9]] = name.strip()

esc = lambda s: s.replace("\\", "\\\\").replace("'", "\\'")


def active(db):
    """active (non-deleted) cases CTE-ish join fragment for a breakout db."""
    return (f"FROM `{db}`.`level-1` l "
            f"JOIN `{db}`.cases c ON c.id=l.`case-id` AND c.deleted=0 ")


def geo_view(name, db, col):
    return (f"CREATE OR REPLACE VIEW csweb_reports.{name} AS\n"
            f"SELECT COALESCE(NULLIF(fc.{col},''),'(unknown)') AS label, COUNT(*) AS cases\n"
            f"{active(db)}LEFT JOIN `{db}`.field_control fc ON fc.`level-1-id`=l.`level-1-id`\n"
            f"GROUP BY label ORDER BY cases DESC;\n")


def case_view(name, db, table, col, cases_map):
    whens = " ".join(f"WHEN '{k}' THEN '{esc(v)}'" for k, v in cases_map.items())
    return (f"CREATE OR REPLACE VIEW csweb_reports.{name} AS\n"
            f"SELECT CASE t.{col} {whens} ELSE COALESCE(NULLIF(t.{col},''),'(blank)') END AS label, COUNT(*) AS cases\n"
            f"{active(db)}LEFT JOIN `{db}`.{table} t ON t.`level-1-id`=l.`level-1-id`\n"
            f"GROUP BY label ORDER BY cases DESC;\n")


parts = []
parts.append("CREATE DATABASE IF NOT EXISTS csweb_reports CHARACTER SET utf8mb4;\n")
parts.append("SET NAMES utf8mb4;\n")

# facility reference table
parts.append("DROP TABLE IF EXISTS csweb_reports.facility_names;\n"
             "CREATE TABLE csweb_reports.facility_names (code9 CHAR(9) NOT NULL PRIMARY KEY,"
             " name VARCHAR(255) NOT NULL) CHARACTER SET utf8mb4;\n")
vals = ",".join(f"('{c}','{esc(n)}')" for c, n in fac.items())
parts.append(f"INSERT INTO csweb_reports.facility_names (code9,name) VALUES {vals};\n")

# ---- F1 ----
F1 = "csweb_f1_breakout"
parts.append(geo_view("vw_f1_by_region",   F1, "region_name"))
parts.append(geo_view("vw_f1_by_province", F1, "province_name"))
parts.append(geo_view("vw_f1_by_city",     F1, "city_name"))
parts.append(
    "CREATE OR REPLACE VIEW csweb_reports.vw_f1_by_facility AS\n"
    "SELECT COALESCE(fn.name, CONCAT('(code ', x.code9, ')')) AS label, COUNT(*) AS cases\n"
    "FROM (SELECT l.`level-1-id` lid, CONCAT(LPAD(fc.region_code,2,'0'),"
    "LPAD(fc.province_huc_code,2,'0'),LPAD(fc.city_municipality_code,3,'0'),"
    "LPAD(fc.facility_no,2,'0')) AS code9\n"
    f"      {active(F1)}LEFT JOIN `{F1}`.field_control fc ON fc.`level-1-id`=l.`level-1-id`) x\n"
    "LEFT JOIN csweb_reports.facility_names fn ON fn.code9=x.code9\n"
    "GROUP BY label ORDER BY cases DESC;\n")
parts.append(case_view("vw_f1_by_ownership", F1, "b_facility_profile", "q7_ownership",
                       {"1": "Public", "2": "Private"}))
parts.append(case_view("vw_f1_by_service_level", F1, "b_facility_profile", "q8_service_level",
                       {"1": "Primary Care Facility", "2": "Level 1 Hospital",
                        "3": "Level 2 Hospital", "4": "Level 3 Hospital"}))
parts.append(case_view("vw_f1_by_result", F1, "field_control", "enum_result_first_visit",
                       {"1": "Completed", "2": "Postponed", "3": "Refused", "4": "Incomplete"}))

# ---- F3 ----
F3 = "csweb_f3_breakout"
parts.append(geo_view("vw_f3_by_region", F3, "region_name"))
parts.append(case_view("vw_f3_by_patient_type", F3, "field_control", "patient_type",
                       {"1": "Outpatient", "2": "Inpatient"}))
parts.append(case_view("vw_f3_by_sex", F3, "b_patient_profile", "q7_sex",
                       {"1": "Male", "2": "Female"}))

# ---- F4 ----
F4 = "csweb_f4_breakout"
parts.append(geo_view("vw_f4_by_region",   F4, "region_name"))
parts.append(geo_view("vw_f4_by_province", F4, "province_name"))

# grant read to the app DB user (views run as definer=root, so SELECT on the
# views is enough for BI tools using csweb_user)
parts.append("GRANT SELECT ON csweb_reports.* TO 'csweb_user'@'%';\nFLUSH PRIVILEGES;\n")

OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"facilities: {len(fac)}  ->  {OUT}  ({OUT.stat().st_size} bytes)")
