#!/usr/bin/env python3
r"""Generate the FULL cspro_area_names loader for the CSWeb Sync Report.

The Sync Report labels each questionnaire_number by an EXACT match on
cspro_area_names.level1 -> label. The canonical CSV (f1-sync-report-labels.csv)
only carries the `<fac9>001` sequence per facility, so cases with any other
3-digit case number (e.g. 101/161/169) showed the raw code. This expands every
facility across the full case-number space 001-999 (zero-padded 12-digit AND
zero-stripped 11-digit for region 01-09) so ANY case number shows its facility
name. ~2.36M rows; emitted as a gzipped TRUNCATE + batched-INSERT SQL loader.

Usage (from this folder):
    python gen-area-names-full-labels.py            # -> area_names_full.sql.gz

Load on the box (root@csweb, /opt/app):
    scp area_names_full.sql.gz root@<box>:/root/
    # backup first: mysqldump ... csweb_uhc_y2 cspro_area_names > backup.sql
    zcat /root/area_names_full.sql.gz | docker compose exec -T database mysql -uroot -p"$ROOTPW"
    # one-time index (idempotent guard): ALTER TABLE csweb_uhc_y2.cspro_area_names ADD INDEX idx_level1 (level1(20));

Refresh when the facility list changes: regenerate f1-sync-report-labels.csv
from F1/facility_lookup.dat (canonical <fac9>001 + zero-stripped rows), then
re-run this. Re-loading TRUNCATEs and repopulates; the index persists.
First built 2026-06-20 (full labeling, replacing the +001-only canonical set).
"""
import csv, gzip, pathlib

HERE = pathlib.Path(__file__).parent
SRC = HERE / "f1-sync-report-labels.csv"
OUT = HERE / "area_names_full.sql.gz"
DB = "csweb_uhc_y2"
BATCH = 5000

facmap = {}
with SRC.open(encoding="utf-8") as f:
    for code, name in csv.reader(f):
        code = code.strip()
        if len(code) == 12 and code.endswith("001"):
            facmap[code[:9]] = name.strip()


def esc(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def pairs():
    # Label format = "<FACILITY NAME> · <CCC>" (facility + 3-digit case number),
    # so each Sync Report row is human-readable AND distinct across the many
    # cases a facility has in F3/F4 (chosen 2026-06-20). One format, all 3 dicts.
    for fac9, name in facmap.items():
        stripped = fac9[1:] if fac9[0] == "0" else None
        base = esc(name)
        for ccc in range(1, 1000):
            c = f"{ccc:03d}"
            lbl = f"{base} · {c}"
            yield f"('{fac9}{c}','{lbl}')"
            if stripped is not None:
                yield f"('{stripped}{c}','{lbl}')"


rows = 0
with gzip.open(OUT, "wt", encoding="utf-8", newline="\n") as g:
    g.write("SET NAMES utf8mb4;\nSET autocommit=0;\n")
    g.write(f"TRUNCATE TABLE {DB}.cspro_area_names;\n")
    batch = []
    for v in pairs():
        batch.append(v); rows += 1
        if len(batch) >= BATCH:
            g.write(f"INSERT INTO {DB}.cspro_area_names (level1,label) VALUES " + ",".join(batch) + ";\n")
            batch = []
    if batch:
        g.write(f"INSERT INTO {DB}.cspro_area_names (level1,label) VALUES " + ",".join(batch) + ";\n")
    g.write("COMMIT;\n")

print(f"facilities: {len(facmap)}  rows: {rows}  gz: {OUT.stat().st_size/1024/1024:.2f} MB -> {OUT}")
