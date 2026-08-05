#!/usr/bin/env bash
# =============================================================================
# Runs the P4 local leg (KV + R2 -> box) using a scoped Cloudflare API TOKEN.
#
# WHY A TOKEN AND NOT `wrangler login`: wrangler's OAuth scope set — in BOTH v3.114
# and v4.110 (verified 2026-07-13 by reading the consent URL) — contains NO R2 scope.
# `wrangler login` therefore can NEVER authorize `r2 object get`. That is why the
# June-9 token couldn't reach R2, and why re-logging-in was never going to fix it.
#
# CARL — two steps:
#   1. Cloudflare dashboard -> Manage Account -> Account API Tokens -> Create Token
#      -> Custom token. Permissions (read-only is enough):
#           Account | Workers R2 Storage  | Read
#           Account | Workers KV Storage  | Read
#      Scope it to your account. Copy the token ONCE.
#   2. Save it to this file (it is inside the job tmp dir — deleted with the job,
#      never committed, never printed by this script):
#           C:\Users\analy\.claude\jobs\84c0ccd0\tmp\cf_token.txt
#      Then tell me, and I run this script.
#
# Do NOT paste the token into chat. A secret that transits a transcript acquires
# rotation debt — exactly the situation the P6 HMAC rotation exists to clean up.
# This one is read-only and disposable: delete it in the dashboard when P6 is done.
#
# Run:  bash deploy/run-p4-local-leg.sh
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
WORKER_DIR="$(cd "$HERE/../../worker" && pwd)"
TOKEN_FILE="/c/Users/analy/.claude/jobs/84c0ccd0/tmp/cf_token.txt"
SSH="ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115"

[ -f "$TOKEN_FILE" ] || { echo "no token at $TOKEN_FILE — see the header"; exit 1; }
CLOUDFLARE_API_TOKEN="$(tr -d '[:space:]' < "$TOKEN_FILE")"
export CLOUDFLARE_API_TOKEN
[ -n "$CLOUDFLARE_API_TOKEN" ] || { echo "token file is empty"; exit 1; }

echo "== [0] token check (value never printed) =="
cd "$WORKER_DIR"
npx wrangler r2 bucket list </dev/null >/dev/null 2>&1 \
  || { echo "token cannot list R2 buckets — needs 'Workers R2 Storage: Read'"; exit 1; }
echo "   OK: R2 reachable with the supplied token"

echo "== [1] P4 local leg (KV durable keys + R2 file objects -> box) =="
bash "$HERE/p4-local-kv-r2.sh"

echo
echo "== [2] verify finding F-1 is CLOSED: metadata rows == objects on box =="
META=$(echo "SELECT COUNT(*) FROM f2_files WHERE is_folder=0 AND deleted_at IS NULL;" \
       | $SSH "docker exec -i lamp-mysql8 sh -c 'MYSQL_PWD=\"\$MYSQL_ROOT_PASSWORD\" exec mysql -uroot -N csweb_f2'" 2>/dev/null | tr -d '[:space:]')
ONBOX=$($SSH 'ls -1 /opt/app/f2-files 2>/dev/null | wc -l' </dev/null | tr -d '[:space:]')
echo "   f2_files live rows: $META   objects on box: $ONBOX"
[ "${META:-0}" -eq "${ONBOX:-1}" ] || { echo "STILL SHORT — F-1 is NOT closed"; exit 1; }
$SSH 'ls -la /opt/app/f2-files' </dev/null
echo "   F-1 CLOSED: every live file object now has its bytes on the box."
echo "   (R2 deletion at P6 §3.4 is now safe; the admin Files app can serve downloads.)"
