"""Extract F1/F3/F4 from the CSWeb breakout databases (etl-spec §2.1).

Dumps every table of the three breakout DBs as TSV (header row included)
into raw/<run_date>/<db>/<table>.tsv, via a single SSH call that tars the
dump on the box and streams it back. Read-only; never writes to CSWeb.
"""
import io, subprocess, tarfile
from pathlib import Path

SSH_HOST = "root@207.148.65.115"
SSH_KEY = "~/.ssh/aspsi-csweb"
BREAKOUTS = ["csweb_f1_breakout", "csweb_f3_breakout", "csweb_f4_breakout"]

REMOTE_SCRIPT = r"""
set -e
cd /opt/app
ROOTPW=$(grep -E '^MYSQL_ROOT_PASSWORD' .env | head -1 | cut -d= -f2-)
DUMP=$(mktemp -d)
for DB in __DBS__; do
  mkdir -p "$DUMP/$DB"
  TABLES=$(docker compose exec -T database mysql -uroot -p"$ROOTPW" --silent \
           -e "SHOW TABLES IN $DB;" </dev/null 2>/dev/null)
  for T in $TABLES; do
    docker compose exec -T database mysql -uroot -p"$ROOTPW" --batch \
      -e "SELECT * FROM $DB.\`$T\`;" </dev/null 2>/dev/null > "$DUMP/$DB/$T.tsv"
  done
done
tar -C "$DUMP" -czf - .
rm -rf "$DUMP"
"""


def extract(raw_dir: Path) -> dict:
    """Pull all breakout tables; return {db: {table: row_count}}."""
    script = REMOTE_SCRIPT.replace("__DBS__", " ".join(BREAKOUTS))
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-i", SSH_KEY, SSH_HOST, script],
        capture_output=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"extract ssh failed: {r.stderr.decode(errors='replace')[:500]}")
    raw_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(r.stdout), mode="r:gz") as tf:
        tf.extractall(raw_dir)

    counts = {}
    for db in BREAKOUTS:
        counts[db] = {}
        for tsv in sorted((raw_dir / db).glob("*.tsv")):
            n_lines = sum(1 for _ in open(tsv, encoding="utf-8", errors="replace"))
            counts[db][tsv.stem] = max(0, n_lines - 1)  # minus header
    return counts


def load_table(raw_dir: Path, db: str, table: str) -> list[dict]:
    """A breakout table as a list of dicts (lowercase keys, 'NULL' -> None)."""
    path = raw_dir / db / f"{table}.tsv"
    if not path.exists():
        return []
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    if len(lines) < 2:
        return []
    header = [h.lower() for h in lines[0].split("\t")]
    rows = []
    for line in lines[1:]:
        vals = line.split("\t")
        rows.append({k: (None if v == "NULL" else v) for k, v in zip(header, vals)})
    return rows


def tables_in(raw_dir: Path, db: str) -> list[str]:
    return sorted(p.stem for p in (raw_dir / db).glob("*.tsv"))
