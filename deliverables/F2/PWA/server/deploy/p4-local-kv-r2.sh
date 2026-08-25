#!/usr/bin/env bash
# =============================================================================
# P4 local leg — runs on Carl's machine (Git Bash), AFTER p4-box-steps.sh.
# Needs: wrangler auth (the same login used for `wrangler deploy`), ssh key.
#
#   cd <repo>/deliverables/F2/PWA/server
#   bash deploy/p4-local-kv-r2.sh
#
# Two independent copies, both expected to be SMALL at UAT scale (possibly 0):
#
#   [A] CF KV F2_AUTH -> MySQL: the two DURABLE key families only.
#         revoked:<jti>  -> auth_revoked   (device-token revocations; no TTL)
#         token:<jti>    -> auth_token_audit (reissue audit entries)
#       Everything else in KV (revoked_jti:/revoked_user:/throttle:/as_quota:)
#       self-expires within <=24h and is NOT migrated — cutover invalidates
#       admin sessions anyway (everyone re-logs-in on uhc-hcw).
#
#   [B] R2 f2-admin `files/<file_id>` objects -> /opt/app/f2-files/<file_id>.
#       Enumeration comes from the box's freshly-ported f2_files metadata
#       (wrangler 3.114 has NO `r2 object list`). Each download is verified
#       against the metadata size before shipping. Break-out CSV objects
#       (the other key family) are Sheet-era derived artifacts — NOT copied;
#       the ETL repoints to csweb_f2 SQL and R2 retires whole at P6.
#
# Idempotent: KV inserts are ON DUPLICATE KEY no-ops; file copies overwrite
# byte-identical content.
# =============================================================================
set -euo pipefail

SSH="ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115"
WORKER_DIR="$(cd "$(dirname "$0")/../../worker" && pwd)"   # wrangler.toml lives here
KV_NS="9b293e0c661d4f60b513facc61b11e0b"                    # F2_AUTH prod (wrangler.toml:13)
BUCKET="f2-admin"                                           # wrangler.toml:22
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$WORKER_DIR"
echo "== [0] wrangler auth check (verify BEFORE the box is flipped, ideally) =="
if ! npx wrangler whoami < /dev/null; then
  echo "wrangler auth is broken — run 'npx wrangler login' and retry"; exit 1
fi

# SQL always travels over stdin — one quoting layer, no -e escaping.
box_mysql() {
  $SSH "docker exec -i lamp-mysql8 sh -c 'MYSQL_PWD=\"\$MYSQL_ROOT_PASSWORD\" exec mysql -uroot -N csweb_f2'"
}

echo "== [A] KV F2_AUTH durable keys -> auth_revoked / auth_token_audit =="
npx wrangler kv key list --namespace-id "$KV_NS" < /dev/null > "$TMP/kv-keys.json"
PYTHONIOENCODING=utf-8 python - "$TMP" "$KV_NS" <<'PY'
import json, subprocess, shutil, sys, datetime as dt
tmp, ns = sys.argv[1], sys.argv[2]
NPX = shutil.which("npx") or shutil.which("npx.cmd")
if not NPX:
    raise SystemExit("npx not found on PATH")
keys = [k["name"] for k in json.load(open(tmp + "/kv-keys.json", encoding="utf-8"))]
revoked = [k for k in keys if k.startswith("revoked:")]
tokens  = [k for k in keys if k.startswith("token:")]
other   = [k for k in keys if not (k.startswith("revoked:") or k.startswith("token:"))]
print(f"KV keys: total={len(keys)} revoked={len(revoked)} token={len(tokens)} ephemeral-skipped={len(other)}")

def hexlit(s):
    if s is None or s == "": return "NULL"
    return "_utf8mb4 0x" + str(s).encode("utf-8").hex()

def tslit(v):
    if v in (None, ""): return "NULL"
    try:
        if isinstance(v, (int, float)) or (isinstance(v, str) and str(v).isdigit()):
            d = dt.datetime.fromtimestamp(int(v), dt.timezone.utc)
        else:
            d = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
            if d.tzinfo: d = d.astimezone(dt.timezone.utc)
        return "'" + d.strftime("%Y-%m-%d %H:%M:%S") + "'"
    except Exception:
        return "NULL"

def kv_get(name):
    r = subprocess.run([NPX, "wrangler", "kv", "key", "get", name, "--namespace-id", ns],
                       capture_output=True, text=True, encoding="utf-8",
                       stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise SystemExit(f"kv get failed for {name!r}: {r.stderr.strip()[:200]}")
    return r.stdout.strip()

stmts = []
for k in revoked:
    jti = k.split(":", 1)[1]
    val = kv_get(k)
    stmts.append("INSERT INTO auth_revoked (jti, reason) VALUES (%s,%s) "
                 "ON DUPLICATE KEY UPDATE reason=VALUES(reason);"
                 % (hexlit(jti), hexlit("kv-migrated: " + (val or "1"))))
for k in tokens:
    jti = k.split(":", 1)[1]
    raw = kv_get(k)
    try: e = json.loads(raw)
    except Exception: e = {}
    stmts.append("INSERT INTO auth_token_audit (jti, tablet_id, tablet_label, "
                 "facility_id, issued_at, expires_at) VALUES (%s,%s,%s,%s,%s,%s) "
                 "ON DUPLICATE KEY UPDATE tablet_id=VALUES(tablet_id);"
                 % (hexlit(jti), hexlit(e.get("tablet_id")), hexlit(e.get("tablet_label")),
                    hexlit(e.get("facility_id")), tslit(e.get("issued_at")), tslit(e.get("exp"))))
body = "\n".join(stmts) + "\n" if stmts else "SELECT 'no durable KV keys to migrate';\n"
open(tmp + "/kv-import.sql", "w", encoding="utf-8").write(body)
print(f"wrote {len(stmts)} statements -> kv-import.sql")
PY
box_mysql < "$TMP/kv-import.sql"
echo "SELECT CONCAT('auth_revoked=',(SELECT COUNT(*) FROM auth_revoked),' auth_token_audit=',(SELECT COUNT(*) FROM auth_token_audit));" | box_mysql

echo
echo "== [B] R2 files/<file_id> -> /opt/app/f2-files =="
echo "SELECT file_id, size_bytes FROM f2_files WHERE is_folder=0 AND deleted_at IS NULL;" | box_mysql > "$TMP/file-list.tsv"
N=$(grep -c . "$TMP/file-list.tsv" || true)
if [ "${N:-0}" -eq 0 ]; then
  echo "no live file rows in f2_files — nothing to copy from R2"
else
  echo "$N file(s) to pull from R2 bucket $BUCKET"
  mkdir -p "$TMP/files"
  MISSING=()
  # read from FD 3 so npx/wrangler can never eat the file list (classic
  # while-read stdin hazard); each child also gets stdin from /dev/null.
  while IFS=$'\t' read -r -u3 FID SIZE; do
    [ -z "$FID" ] && continue
    if ! npx wrangler r2 object get "$BUCKET/files/$FID" --file "$TMP/files/$FID" < /dev/null; then
      # Not in R2: legitimate iff the file was uploaded through the NEW portal
      # (bytes already live at /opt/app/f2-files, never in R2). Verify on-box.
      rm -f "$TMP/files/$FID"
      if $SSH "test -s /opt/app/f2-files/$FID" < /dev/null; then
        echo "  $FID not in R2 but already on the box (new-portal upload) — OK"
      else
        MISSING+=("$FID")
        echo "  $FID MISSING from both R2 and the box!"
      fi
      continue
    fi
    GOT=$(stat -c%s "$TMP/files/$FID")
    if [ "$GOT" != "$SIZE" ]; then
      echo "SIZE MISMATCH for $FID: R2=$GOT metadata=$SIZE"; exit 1
    fi
    echo "  $FID ($GOT bytes) OK"
  done 3< "$TMP/file-list.tsv"
  if [ "${#MISSING[@]}" -gt 0 ]; then
    echo "FAILED: ${#MISSING[@]} file(s) have metadata but no bytes anywhere: ${MISSING[*]}"; exit 1
  fi
  PULLED=$(ls -1 "$TMP/files" 2>/dev/null | wc -l)
  echo "pulled $PULLED of $N (rest already on-box)"
  if [ "$PULLED" -gt 0 ]; then
    tar czf - -C "$TMP/files" . | $SSH 'tar xzf - -C /opt/app/f2-files && chown -R 1000:1000 /opt/app/f2-files && ls -la /opt/app/f2-files | head'
  fi
fi

echo
echo "== P4 LOCAL LEG DONE =="
