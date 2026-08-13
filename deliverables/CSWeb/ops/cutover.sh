#!/usr/bin/env bash
# CAPI Console — execute the cutover (E9-ADMIN-033 / -034).     Carl, 2026-08-09
#
#   bash /opt/app/lamp/private/cutover.sh --dry-run   # show the plan, change nothing
#   bash /opt/app/lamp/private/cutover.sh             # do it
#   bash /opt/app/lamp/private/cutover.sh --rollback  # undo the most recent run
#
# Flips the gate from Apache's filename-based FilesMatch to authz.php, in one
# step, with the canaries checked before and after and an AUTOMATIC ROLLBACK if
# any of them fails. The whole point is that nobody has to make a judgement
# call while the console is down.
#
# BEFORE YOU RUN IT
#   * Break-glass must be proven — cutover-check.sh check 7 (this script runs it).
#   * All 18 accounts still have must_change=1, so EVERY user is forced through
#     a password change at their next sign-in. That is a people event, not a
#     technical one; tell ASPSI before, not after.
#   * /csweb/ is untouched. Tablet sync does not stop.

set -uo pipefail

NGX_LIVE=/opt/elestio/nginx/conf.d/capi.asiansocial.org.conf
NGX_NEW=/opt/app/lamp/private/capi.asiansocial.org.conf.cutover
APA_LIVE=/opt/app/lamp/config/vhosts/00-uhc-auth.conf
# ALL THREE gate files, not just /docs/. The data room and the admin console
# carry their own AuthType/Require lines, and removing the <Location /docs>
# block takes away the Session and AuthFormProvider they depend on — leaving
# them declaring form auth with no provider configured. Missing these two was
# a real bug in the first draft of this script.
DOCS_HT=/opt/app/lamp/www/docs/.htaccess
DATA_HT=/opt/app/lamp/www/docs/data/.htaccess
ADMIN_HT=/opt/app/lamp/www/docs/admin/.htaccess
CHECK=/opt/app/lamp/private/cutover-check.sh
STAMP=$(date +%Y%m%d-%H%M%S)
BAK=/opt/app/lamp/private/_cutover-$STAMP
MARKER=/opt/app/lamp/private/.last-cutover

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; OFF=$'\033[0m'
say()  { printf "\n%s==> %s%s\n" "$YELLOW" "$1" "$OFF"; }
die()  { printf "%sABORT: %s%s\n" "$RED" "$1" "$OFF"; exit 1; }

ngx_reload() { docker exec elestio-nginx openresty -t >/dev/null 2>&1 || return 1
               docker exec elestio-nginx openresty -s reload >/dev/null 2>&1; sleep 1; }
apa_reload() { docker exec lamp-php8 apachectl -t >/dev/null 2>&1 || return 1
               docker exec lamp-php8 apachectl graceful >/dev/null 2>&1; sleep 2; }

# --------------------------------------------------------------------- rollback
if [ "${1:-}" = "--rollback" ]; then
  [ -f "$MARKER" ] || die "no recorded cutover to roll back"
  B=$(cat "$MARKER")
  [ -d "$B" ] || die "backup dir $B is gone"
  say "Rolling back from $B"
  cp "$B/capi.asiansocial.org.conf" "$NGX_LIVE"
  cp "$B/00-uhc-auth.conf"          "$APA_LIVE"
  cp "$B/docs.htaccess"             "$DOCS_HT"
  cp "$B/data.htaccess"             "$DATA_HT"
  cp "$B/admin.htaccess"            "$ADMIN_HT"
  ngx_reload || die "nginx refused the restored config — fix by hand NOW"
  apa_reload || die "apache refused the restored config — fix by hand NOW"
  printf "%srolled back.%s Re-run the check:\n  bash %s\n" "$GREEN" "$OFF" "$CHECK"
  exit 0
fi

DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

# ------------------------------------------------------------------ preflight
say "Preflight — the state must be good BEFORE we touch anything"
bash "$CHECK" || die "pre-cutover check failed. Fix that first; do not flip on top of a known problem."

[ -f "$NGX_NEW" ] || die "post-cutover vhost not staged at $NGX_NEW"

say "Plan"
cat <<PLAN
  1. nginx : $NGX_LIVE  <-  capi.asiansocial.org.conf.cutover
             (/docs/ gains auth_request; /_capi_auth -> authz.php)
  2. apache: remove the mod_auth_form <Location> blocks from
             00-uhc-auth.conf and add redirects so the topbar's
             /docs/auth/logout link keeps working with NO page regeneration
  3. apache: strip AuthType/Require from $DOCS_HT (the FilesMatch tiers)
  4. env   : CAPI_IDP_GATE=live so the admin API stops warning that the
             gate is not cut over
  Backups  -> $BAK
  Rollback -> bash \$0 --rollback
PLAN
[ "$DRY" = "1" ] && { printf "\n%sdry run: nothing changed.%s\n" "$GREEN" "$OFF"; exit 0; }

# -------------------------------------------------------------------- back up
say "Backing up"
mkdir -p "$BAK"
cp "$NGX_LIVE" "$BAK/capi.asiansocial.org.conf"
cp "$APA_LIVE" "$BAK/00-uhc-auth.conf"
cp "$DOCS_HT"  "$BAK/docs.htaccess"
cp "$DATA_HT"  "$BAK/data.htaccess"
cp "$ADMIN_HT" "$BAK/admin.htaccess"
echo "$BAK" > "$MARKER"
ls -1 "$BAK"

# ------------------------------------------------------------------- 1. nginx
say "1/4 nginx — gating /docs/ with authz.php"
cp "$NGX_NEW" "$NGX_LIVE"
ngx_reload || { cp "$BAK/capi.asiansocial.org.conf" "$NGX_LIVE"; ngx_reload; die "nginx rejected the new config; restored"; }

# ------------------------------------------------------------------ 2. apache
say "2/4 apache — retiring mod_auth_form, keeping its URLs alive"
python3 - "$APA_LIVE" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p).read()
# Drop the four Location blocks that implement form auth. Everything else in
# this file (the /csweb/ hardening) stays exactly as it is.
for loc in ('/docs', '/docs/auth/login', '/docs/auth/logout', '/docs/whoami.php'):
    s = re.sub(r'<Location %s>.*?</Location>\n' % re.escape(loc), '', s, flags=re.S)
if 'RedirectMatch 302 ^/docs/auth/logout' not in s:
    s += (
        "\n# ---------------------------------------------------------------------------\n"
        "# Post-cutover (E9-ADMIN-034). The topbar of every generated page links to\n"
        "# /docs/auth/logout, and /docs/login.php is POSTed to by the old sign-in form.\n"
        "# Both are kept alive as redirects so that NOT ONE page has to be regenerated.\n"
        "# /docs/login.php is a redirect rather than a deletion on purpose: a 302 turns\n"
        "# its POST into a GET and silently drops the credentials, which is confusing;\n"
        "# a redirect to the real sign-in page at least lands somewhere that works.\n"
        "# ---------------------------------------------------------------------------\n"
        "RedirectMatch 302 ^/docs/auth/logout/?$ /docs/idp/logout\n"
        "RedirectMatch 302 ^/docs/auth/login/?$  /docs/idp/login\n"
        "RedirectMatch 302 ^/docs/login\\.php$    /docs/idp/login\n"
    )
open(p, 'w').write(s)
print("  mod_auth_form Location blocks removed; redirects added")
PY

# ---------------------------------------------------------------- 3. htaccess
say "3/4 apache — removing the FilesMatch auth tiers from all three gate files"
python3 - "$DOCS_HT" "$DATA_HT" "$ADMIN_HT" <<'PY'
import re, sys
for p in sys.argv[1:]:
    try:
        s = open(p).read()
    except FileNotFoundError:
        print("  (skip, not present) %s" % p); continue
    # Strip ONLY the authentication directives. `Require all denied` is left
    # alone — that is the .bak/.orig/.swp denial block, which is not about
    # identity and must survive. `Require user`/`valid-user` go, because
    # authz.php decides that now.
    s2 = re.sub(r'^[ \t]*(AuthType|AuthFormProvider|AuthName|AuthUserFile|'
                r'Require[ \t]+(user|valid-user))\b.*\n', '', s, flags=re.M)
    open(p, 'w').write(s2)
    print("  stripped %-42s (%d -> %d bytes)" % (p, len(s), len(s2)))
PY
echo "  remaining Require lines (these should be 'all denied' / 'all granted' only):"
grep -hn "Require" "$DOCS_HT" "$DATA_HT" "$ADMIN_HT" 2>/dev/null | sed 's/^/    /' || echo "    (none)"

apa_reload || { say "apache rejected the config — ROLLING BACK"; bash "$0" --rollback; exit 1; }

# --------------------------------------------------------------------- 4. env
say "4/4 marking the gate live"
cd /opt/app
if grep -q 'CAPI_IDP_GATE' docker-compose.yml; then
  sed -i 's/CAPI_IDP_GATE:.*/CAPI_IDP_GATE: "live"/' docker-compose.yml
else
  sed -i 's/^\(      CAPI_AUTH_DB_HOST: database\)$/      CAPI_IDP_GATE: "live"\n\1/' docker-compose.yml
fi
grep -n 'CAPI_IDP_GATE' docker-compose.yml || echo "  (not set — admin API will keep showing the pre-cutover notice; harmless)"
echo "  NOTE: this only takes effect on the next 'docker compose up -d webserver',"
echo "        which also recreates the database container. Do it in a quiet window,"
echo "        not now — the notice being stale is cosmetic."

# ----------------------------------------------------------------- verify
say "Verifying"
if bash "$CHECK"; then
  printf "\n%sCUTOVER COMPLETE.%s The gate is authz.php.\n" "$GREEN" "$OFF"
  printf "Next: E9-ADMIN-035, walk one account per role through every page.\n"
  printf "Rollback if needed:  bash %s --rollback\n\n" "$0"
  exit 0
fi

rc=$?
if [ "$rc" = "1" ]; then
  printf "\n%sA CANARY FAILED — rolling back automatically.%s\n" "$RED" "$OFF"
  bash "$0" --rollback
  printf "%sRolled back. Diagnose from the backup in %s.%s\n" "$YELLOW" "$BAK" "$OFF"
  exit 1
fi
printf "\n%sNon-canary failures after cutover.%s The gate is LIVE and the canaries are fine,\n" "$YELLOW" "$OFF"
printf "so this is not rolled back automatically. Review above; roll back with:\n  bash %s --rollback\n\n" "$0"
exit 2
