#!/usr/bin/env bash
# =============================================================================
# F-1 fix via the OLD admin portal — no Cloudflare token, no browser.
# The old Worker still holds the R2 binding, so with an admin JWT we can pull the
# 3 file objects straight from R2 and land them on the box. Fully headless.
#
#   POST /admin/api/login {username,password}                 -> JWT
#   GET  /admin/api/dashboards/apps/files/<file_id>  (Bearer)  -> bytes (streamed from R2)
#   -> size-verify vs csweb_f2.f2_files metadata -> scp to /opt/app/f2-files/<file_id>
#
# CREDENTIALS (read from files, never from argv/env so they don't hit the shell log):
#   username -> deploy/.f2_admin_user   (defaults to 'carl_admin' if absent)
#   password -> C:\Users\analy\.claude\jobs\84c0ccd0\tmp\f2_admin_pw.txt   (REQUIRED)
# Both files are deleted on success. The password file lives in job-tmp (gitignored,
# deleted with the job). This is the OLD portal's credential — it dies at P6 anyway
# (HMAC rotation + Worker delete), and you reset on the new box, so exposure is bounded.
#
# Run:  bash deploy/pull-f2-files-via-portal.sh
# =============================================================================
set -euo pipefail

WORKER="https://f2-pwa-worker.hcw.workers.dev"
HERE="$(cd "$(dirname "$0")" && pwd)"
PW_FILE="/c/Users/analy/.claude/jobs/84c0ccd0/tmp/f2_admin_pw.txt"
USER_FILE="$HERE/.f2_admin_user"
SSH="ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

[ -s "$PW_FILE" ] || { echo "no password at $PW_FILE — see the header"; exit 1; }
USERNAME="carl_admin"; [ -s "$USER_FILE" ] && USERNAME="$(tr -d '[:space:]' < "$USER_FILE")"
PASSWORD="$(cat "$PW_FILE")"; PASSWORD="${PASSWORD%$'\n'}"

echo "== [1] admin login as '$USERNAME' (password never printed) =="
LOGIN=$(curl -s -m 25 -X POST "$WORKER/admin/api/login" \
  -H 'Content-Type: application/json' \
  --data "$(python -c 'import json,sys; print(json.dumps({"username":sys.argv[1],"password":sys.argv[2]}))' "$USERNAME" "$PASSWORD")")
TOKEN=$(printf '%s' "$LOGIN" | python -c 'import json,sys
try: d=json.load(sys.stdin)
except Exception: d={}
print(d.get("token",""))' )
if [ -z "$TOKEN" ]; then
  echo "LOGIN FAILED. Server said:"; printf '%s\n' "$LOGIN" | python -c 'import json,sys
try: d=json.load(sys.stdin); print("  ",d.get("error",{}).get("code"),"-",d.get("error",{}).get("message"))
except Exception: print("  (unparseable response)")'
  echo "  -> check the password (and username if not carl_admin, put it in deploy/.f2_admin_user)"
  exit 1
fi
echo "   OK: authenticated, JWT acquired"

echo "== [2] the 3 file_ids + sizes from csweb_f2 (source of truth) =="
$SSH 'cd /opt/app && MP=$(grep "^MYSQL_ROOT_PASSWORD" .env | cut -d= -f2-) && docker compose exec -T database mysql -uroot -p"$MP" -N -e "SELECT file_id, size_bytes, filename FROM csweb_f2.f2_files WHERE is_folder=0 AND deleted_at IS NULL"' </dev/null 2>/dev/null > "$TMP/files.tsv"
N=$(grep -c . "$TMP/files.tsv" || true)
echo "   $N live file(s) to pull"
[ "${N:-0}" -gt 0 ] || { echo "no live files — nothing to do"; exit 0; }

echo "== [3] download each from R2 via the Worker, size-verify =="
mkdir -p "$TMP/files"; FAIL=0
while IFS=$'\t' read -r -u3 FID SIZE NAME; do
  [ -z "$FID" ] && continue
  curl -s -m 60 "$WORKER/admin/api/dashboards/apps/files/$FID" \
    -H "Authorization: Bearer $TOKEN" -o "$TMP/files/$FID"
  GOT=$(stat -c%s "$TMP/files/$FID" 2>/dev/null || echo 0)
  # a JSON error body is small + starts with '{' — catch it rather than shipping an error page
  if head -c1 "$TMP/files/$FID" | grep -q '{' && [ "$GOT" -lt 2000 ]; then
    echo "  $FID ($NAME): got an error response, not bytes:"; cat "$TMP/files/$FID"; echo; FAIL=1; continue
  fi
  if [ "$GOT" != "$SIZE" ]; then echo "  $FID ($NAME): SIZE MISMATCH got=$GOT meta=$SIZE"; FAIL=1; continue; fi
  echo "  OK $FID  $GOT bytes  ($NAME)"
done 3< "$TMP/files.tsv"
[ "$FAIL" = 0 ] || { echo "one or more downloads failed — not shipping a partial set"; exit 1; }

echo "== [4] ship to /opt/app/f2-files on the box =="
tar czf - -C "$TMP/files" . | $SSH 'mkdir -p /opt/app/f2-files && tar xzf - -C /opt/app/f2-files && chown -R 1000:1000 /opt/app/f2-files && ls -la /opt/app/f2-files'

echo "== [5] verify F-1 CLOSED: metadata rows == objects on box =="
ONBOX=$($SSH 'ls -1 /opt/app/f2-files 2>/dev/null | wc -l' </dev/null | tr -d '[:space:]')
echo "   f2_files live rows: $N   objects on box: $ONBOX"
[ "${ONBOX:-0}" -ge "${N:-1}" ] || { echo "STILL SHORT — F-1 NOT closed"; exit 1; }
rm -f "$PW_FILE" "$USER_FILE"
echo "   F-1 CLOSED. Admin Files downloads now work; R2 deletion at P6 is safe."
echo "   (deleted the local credential file; reset this admin password after P6.)"
