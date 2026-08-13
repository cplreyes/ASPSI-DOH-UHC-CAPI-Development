#!/usr/bin/env bash
# CAPI Console — cutover regression check (E9-ADMIN-041).       Carl, 2026-08-09
#
#   scp to the box, then:  bash /opt/app/lamp/private/cutover-check.sh
#
# Run it BEFORE the flip to record a baseline, and AFTER to prove nothing moved
# that should not have. Most checks are written to hold in BOTH eras, so the
# two runs are directly comparable; the few that legitimately differ say so.
#
# CHECKS 1-3 ARE THE CANARIES. If any of them fails after the flip, roll back
# immediately (DEPLOY.md §9) and diagnose afterwards — check 1 in particular is
# CSEntry tablet sync, which is live fieldwork and is never worth debugging in
# place.
#
# Exit status: 0 all good · 1 a canary failed · 2 a non-canary failed.

set -uo pipefail

HOST="${HOST:-https://capi.asiansocial.org}"
SYNC="${SYNC:-https://csweb.asiansocial.org/csweb/}"
COMPOSE_DIR="${COMPOSE_DIR:-/opt/app}"
LIB="/var/www/private/capi-auth"

pass=0; fail=0; canary_fail=0
GREEN=$'\033[32m'; RED=$'\033[31m'; DIM=$'\033[2m'; OFF=$'\033[0m'

ok()   { pass=$((pass+1)); printf "  ${GREEN}pass${OFF}  %s\n" "$1"; }
bad()  { fail=$((fail+1)); printf "  ${RED}FAIL${OFF}  %s — %s\n" "$1" "$2"; }
crit() { fail=$((fail+1)); canary_fail=$((canary_fail+1)); printf "  ${RED}CANARY FAIL${OFF}  %s — %s\n" "$1" "$2"; }

code() { curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$1"; }
body() { curl -s --max-time 20 "$1"; }

# in_list <value> <space separated allowed>
in_list() { local v="$1"; shift; for a in $@; do [ "$v" = "$a" ] && return 0; done; return 1; }

printf "\n%sCAPI cutover check — %s%s\n" "$DIM" "$(date -u '+%Y-%m-%d %H:%M:%SZ')" "$OFF"
printf "%starget: %s%s\n\n" "$DIM" "$HOST" "$OFF"

# --------------------------------------------------------------- the canaries
printf "CANARIES (a failure here means roll back, not debug)\n"

c=$(code "$SYNC")
if [ "$c" = "200" ]; then ok "1. CSEntry sync API answers 200 ($SYNC)"
else crit "1. CSEntry sync API" "got $c, want 200 — FIELDWORK IS AFFECTED"; fi

c=$(code "$HOST/docs/idp/login")
if [ "$c" = "200" ]; then ok "2. sign-in page reachable and anonymous"
else crit "2. sign-in page" "got $c, want 200 — nobody can get in"; fi

c=$(code "$HOST/")
if in_list "$c" "200 302"; then ok "3. public portal responds ($c)"
else crit "3. public portal" "got $c, want 200 or 302"; fi

# ------------------------------------------------------------ access control
printf "\nACCESS CONTROL\n"

# Denied is 401 before the flip (Apache) and 302 to the sign-in page after it
# (nginx error_page). Both are "refused"; 200 is the failure that matters.
# Since the console unification (2026-08-09) the old page URLs answer 301 to
# their portal homes — the gate runs at the DESTINATION, which the second loop
# asserts. A 301 here leaks nothing: no content, only a Location header.
for p in /docs/dashboard.html /docs/map.html /docs/admin/ /docs/data/; do
  c=$(code "$HOST$p")
  if in_list "$c" "401 302 403 301"; then ok "4. anonymous $p refused/moved ($c)"
  else bad "4. anonymous $p" "got $c — expected 401/302/403/301"; fi
done
for p in /docs/idp/admin/users /projects/uhc-y2/monitoring/ /projects/uhc-y2/data/ /projects/uhc-y2/admin/; do
  c=$(code "$HOST$p")
  if in_list "$c" "401 302 403"; then ok "4. anonymous $p refused ($c)"
  else bad "4. anonymous $p" "got $c — expected 401/302/403"; fi
done

# The library must never be SERVED. The refusal code differs by era and that
# is fine: before cutover Apache answers 403, after it nginx redirects the
# anonymous probe to sign-in (302). Asserting a specific code here made this
# check fail the moment the gate moved, for no reason. What must never happen
# is 200 — or a 500, which would mean the file executed and blew up.
for p in /docs/idp/admin_bootstrap.php /docs/idp/lib.php /docs/idp/acl.php; do
  c=$(code "$HOST$p")
  if in_list "$c" "401 403 404 302"; then ok "5. library $p not served ($c)"
  else bad "5. library $p" "got $c — MUST NOT be 200"; fi
done

# Header spoofing (E9-ADMIN-009). Two valid shapes, one per era:
#   before cutover: the header is BLANKED  (proxy_set_header X-Auth-User "")
#   after cutover:  it is OVERWRITTEN from the subrequest ($auth_user), which
#                   is strictly stronger — a client value cannot survive
#                   either way, which is the property that matters.
NGXC=/opt/elestio/nginx/conf.d/capi.asiansocial.org.conf
if grep -qE 'proxy_set_header +X-Auth-User +("" *|\$auth_user *);?$' "$NGXC" 2>/dev/null; then
  if grep -q 'auth_request_set \$auth_user' "$NGXC"; then
    ok "6. X-Auth-User set from the auth subrequest (post-cutover form)"
  else
    ok "6. vhost blanks client-supplied X-Auth-* (pre-cutover form)"
  fi
else
  bad "6. vhost X-Auth-* handling" "neither blanked nor set from the subrequest in $NGXC"
fi

# ----------------------------------------------------------------- breakglass
printf "\nBREAK-GLASS (E9-ADMIN-010)\n"

c=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 10 https://127.0.0.1:8443/docs/idp/login 2>/dev/null)
if [ "$c" = "401" ]; then ok "7. break-glass listener up and demanding credentials"
elif [ "$c" = "000" ]; then bad "7. break-glass listener" "not answering on 127.0.0.1:8443"
else bad "7. break-glass listener" "got $c, want 401 (auth_basic challenge)"; fi

if [ -s /opt/elestio/nginx/conf.d/capi-breakglass.htpasswd ]; then
  n=$(wc -l < /opt/elestio/nginx/conf.d/capi-breakglass.htpasswd)
  ok "8. break-glass credential file present ($n accounts)"
else
  bad "8. break-glass credential file" "missing or empty — you have no way back in"
fi

# ------------------------------------------------------------------- database
printf "\nIDENTITY STORE\n"

cd "$COMPOSE_DIR" 2>/dev/null || { bad "9. compose dir" "$COMPOSE_DIR not found"; }
ROOT_PW=$(grep '^MYSQL_ROOT_PASSWORD' .env 2>/dev/null | cut -d= -f2-)
myq() { docker compose exec -T database mysql -uroot -p"$ROOT_PW" -N -e "$1" 2>/dev/null | tr -d '\r'; }

t=$(myq "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='capi_auth';")
if [ "$t" = "8" ]; then ok "9. capi_auth has all 8 tables"
else bad "9. capi_auth tables" "got $t, want 8 — is migration 002 applied?"; fi

g=$(myq "SELECT GROUP_CONCAT(PRIVILEGE_TYPE ORDER BY PRIVILEGE_TYPE) FROM information_schema.TABLE_PRIVILEGES WHERE GRANTEE=\"'capi_auth'@'%'\" AND TABLE_SCHEMA='capi_auth' AND TABLE_NAME='console_audit';")
if [ "$g" = "INSERT,SELECT" ]; then ok "10. audit trail is append-only to the app"
else bad "10. audit grants" "got '$g', want 'INSERT,SELECT' — migration 003?"; fi

d=$(myq "SELECT COUNT(*) FROM capi_auth.console_users WHERE status='active';")
if [ "${d:-0}" -ge 1 ]; then ok "11. $d active accounts in console_users"
else bad "11. active accounts" "got $d — nobody could sign in after the flip"; fi

o=$(myq "SELECT COUNT(*) FROM capi_auth.console_users u JOIN capi_auth.console_user_roles ur ON ur.user_id=u.id JOIN capi_auth.console_roles r ON r.id=ur.role_id WHERE r.name='owner' AND u.status='active';")
if [ "${o:-0}" -ge 1 ]; then ok "12. $o active owner(s) — administration is reachable"
else bad "12. active owner" "NONE — nobody can administer the console"; fi

# ---------------------------------------------------------------------- suites
printf "\nTEST SUITES\n"
for t in test_acl test_admin test_lib test_db; do
  out=$(docker compose exec -T webserver php "$LIB/$t.php" 2>&1 | tail -1)
  if echo "$out" | grep -q '0 failed'; then ok "13. $t — $out"
  else bad "13. $t" "$out"; fi
done

# ----------------------------------------------------------------- environment
printf "\nENVIRONMENT\n"
x=$(docker compose exec -T webserver php -r 'echo ini_get("xdebug.mode") ?: "unset";' 2>/dev/null | tr -d '\r')
if in_list "$x" "off unset"; then ok "14. xdebug is off in production (mode=$x)"
else bad "14. xdebug" "mode=$x — it taxes every request, and every request runs authz after the flip"; fi

l=$(docker compose exec -T webserver php -r 'echo ini_get("log_errors") ? "on" : "off";' 2>/dev/null | tr -d '\r')
if [ "$l" = "on" ]; then ok "15. log_errors on — a fatal leaves a trace"
else bad "15. log_errors" "off — a PHP fatal will be a blank 500 with no line anywhere"; fi

# ------------------------------------------------------------- store drift
printf "\nSTORE DRIFT (who loses access at the flip)\n"
ht=$(cut -d: -f1 /opt/app/lamp/www/.htpasswd-docs 2>/dev/null | sort)
cn=$(myq "SELECT username FROM capi_auth.console_users;" | sort)
only_ht=$(comm -23 <(echo "$ht") <(echo "$cn") | tr '\n' ' ' | sed 's/ *$//')
if [ -z "$only_ht" ]; then ok "16. every htpasswd account exists in console_users"
else bad "16. accounts that lose access at the flip" "$only_ht"; fi

# --------------------------------------------------------------------- verdict
printf "\n%s────────────────────────────────────────────%s\n" "$DIM" "$OFF"
printf "  %d passed, %d failed\n" "$pass" "$fail"
if [ "$canary_fail" -gt 0 ]; then
  printf "  %sA CANARY FAILED — roll back now (DEPLOY.md §9), diagnose after.%s\n\n" "$RED" "$OFF"
  exit 1
elif [ "$fail" -gt 0 ]; then
  printf "  %s%d non-canary failure(s) — do not flip until these are understood.%s\n\n" "$RED" "$fail" "$OFF"
  exit 2
fi
printf "  %sAll checks passed.%s\n\n" "$GREEN" "$OFF"
exit 0
