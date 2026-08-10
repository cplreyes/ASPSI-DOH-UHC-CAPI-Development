"""Extract the four instruments from the box (etl-spec §2.1 + §2.2).

F1/F3/F4  — every table of the three CSWeb breakout DBs.
F2        — csweb_f2, the live PWA store since the P4 cutover (2026-07-09).
            **Whitelisted**, not dumped wholesale: that database also holds
            f2_users (PBKDF2 password hashes), auth_revoked / auth_token_audit /
            auth_kv (device + session tokens). Those are credentials, not survey
            data, and must never land in raw/ or in a dataset we hand to anyone.

Read-only; never writes to CSWeb. Dumps to raw/<run_date>/<db>/<table>.tsv.
"""
import io, subprocess, tarfile
from pathlib import Path

SSH_HOST = "root@207.148.65.115"
SSH_KEY = "~/.ssh/aspsi-csweb"

BREAKOUTS = ["csweb_f1_breakout", "csweb_f3_breakout", "csweb_f4_breakout"]

F2_DB = "csweb_f2"
# survey payload + the frames needed to interpret it. NOTHING ELSE.
F2_TABLES = ["f2_responses", "f2_hcws", "f2_facility_master", "f2_dlq"]
F2_DENY = ["f2_users", "f2_roles", "auth_revoked", "auth_token_audit",
           "auth_kv", "f2_audit", "f2_files", "f2_settings", "f2_config"]

ALL_DBS = BREAKOUTS + [F2_DB]

REMOTE_SCRIPT = r"""
set -e
cd /opt/app
ROOTPW=$(grep -E '^MYSQL_ROOT_PASSWORD' .env | head -1 | cut -d= -f2-)
DUMP=$(mktemp -d)

# --- F1/F3/F4: every table of each breakout DB
for DB in __BREAKOUTS__; do
  mkdir -p "$DUMP/$DB"
  TABLES=$(docker compose exec -T database mysql -uroot -p"$ROOTPW" --silent \
           -e "SHOW TABLES IN $DB;" </dev/null 2>/dev/null)
  for T in $TABLES; do
    docker compose exec -T database mysql -uroot -p"$ROOTPW" --batch \
      -e "SELECT * FROM $DB.\`$T\`;" </dev/null 2>/dev/null > "$DUMP/$DB/$T.tsv"
  done
done

# --- F2: ONLY the whitelisted survey tables (credentials stay on the box)
mkdir -p "$DUMP/__F2DB__"
for T in __F2TABLES__; do
  docker compose exec -T database mysql -uroot -p"$ROOTPW" --batch \
    -e "SELECT * FROM __F2DB__.\`$T\`;" </dev/null 2>/dev/null > "$DUMP/__F2DB__/$T.tsv"
done

tar -C "$DUMP" -czf - .
rm -rf "$DUMP"
"""


def extract(raw_dir: Path) -> dict:
    """Pull all instrument tables; return {db: {table: row_count}}."""
    script = (REMOTE_SCRIPT
              .replace("__BREAKOUTS__", " ".join(BREAKOUTS))
              .replace("__F2TABLES__", " ".join(F2_TABLES))
              .replace("__F2DB__", F2_DB))
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-i", SSH_KEY, SSH_HOST, script],
        capture_output=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"extract ssh failed: {r.stderr.decode(errors='replace')[:500]}")
    raw_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(r.stdout), mode="r:gz") as tf:
        tf.extractall(raw_dir)

    # Belt and braces: if a credential table ever shows up in raw/, delete it
    # and fail loudly rather than let it sit on disk or reach a deliverable.
    leaked = [p for p in (raw_dir / F2_DB).glob("*.tsv") if p.stem in F2_DENY]
    for p in leaked:
        p.unlink()
    if leaked:
        raise RuntimeError(f"extract pulled non-survey F2 tables "
                           f"{[p.stem for p in leaked]} — deleted from raw/; "
                           f"fix the whitelist before re-running")

    # NOTE (verified on the box, 2026-07-13): `mysql --batch` prints **nothing at
    # all** for an empty result set — not even a header row. So a 0-byte dump
    # means "0 rows", NOT "the query failed", and we must not treat it as an
    # error (plenty of tables are legitimately empty: `notes`, an unused roster,
    # an instrument with no cases yet).
    #
    # The dangerous case is narrower and is caught in run.py's QA gates: an
    # instrument whose `level-1` is empty has **no cases at all**, which silently
    # drops a whole instrument out of the master dataset. That is a hard gate,
    # not an extract error — the extract did its job; there was nothing there.

    counts = {}
    for db in ALL_DBS:
        counts[db] = {}
        d = raw_dir / db
        if not d.exists():
            continue
        for tsv in sorted(d.glob("*.tsv")):
            n_lines = sum(1 for _ in open(tsv, encoding="utf-8", errors="replace"))
            counts[db][tsv.stem] = max(0, n_lines - 1)  # minus header
    return counts


def _unescape(v: str):
    """Undo `mysql --batch` escaping.

    The batch client escapes control characters so every row stays on one line:
    tab -> \\t, newline -> \\n, carriage return -> \\r, backslash -> \\\\.
    This matters enormously for F2, whose `values_json` blob is a JSON string
    that would otherwise be corrupted (and unparseable) on the way in.
    """
    if v is None or "\\" not in v:
        return v
    out, i = [], 0
    while i < len(v):
        c = v[i]
        if c == "\\" and i + 1 < len(v):
            nxt = v[i + 1]
            out.append({"t": "\t", "n": "\n", "r": "\r",
                        "\\": "\\", "0": "\0"}.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def load_table(raw_dir: Path, db: str, table: str) -> list[dict]:
    """A table as a list of dicts (lowercase keys, 'NULL' -> None, unescaped)."""
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
        rows.append({k: (None if v == "NULL" else _unescape(v))
                     for k, v in zip(header, vals)})
    return rows


def tables_in(raw_dir: Path, db: str) -> list[str]:
    d = raw_dir / db
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.tsv"))
