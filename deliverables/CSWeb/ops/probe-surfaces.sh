#!/usr/bin/env bash
# Role x URL probe. Signs in once (double-submit CSRF: GET the form, extract
# the token, POST it back), then asserts a status per surface.
#
#   probe-surfaces.sh <username> <password> <expect-file>
#
# expect-file lines:  <path> <expected-status>     (# comments allowed)
# Run it before and after every URL move. The failure it exists to catch is a
# path that starts answering 200 to an account that should get 403.
set -euo pipefail

U="${1:?username}"; PW="${2:?password}"; EXPECT="${3:?expect-file}"
BASE="https://capi.asiansocial.org"
JAR=$(mktemp); trap 'rm -f "$JAR"' EXIT
fails=0

csrf=$(curl -sS -c "$JAR" "$BASE/docs/idp/login" \
  | grep -oP 'name="csrf" value="\K[^"]+' | head -1)
[ -n "$csrf" ] || { echo "no csrf token on the login form"; exit 1; }
curl -sS -b "$JAR" -c "$JAR" -o /dev/null \
  -d "username=$U" -d "password=$PW" -d "csrf=$csrf" "$BASE/docs/idp/login"
curl -sS -b "$JAR" "$BASE/docs/idp/me" | grep -q '"signed_in":true' \
  || { echo "sign-in failed for $U"; exit 1; }

while read -r path want; do
  [ -z "${path:-}" ] && continue
  case "$path" in \#*) continue ;; esac
  got=$(curl -sS -b "$JAR" -o /dev/null -w '%{http_code}' "$BASE$path")
  if [ "$got" = "$want" ]; then printf '%-46s %s ok\n' "$path" "$got"
  else printf '%-46s got=%s want=%s FAIL\n' "$path" "$got" "$want"; fails=$((fails+1)); fi
done < "$EXPECT"

echo
[ "$fails" -eq 0 ] && { echo "all surfaces correct for $U"; exit 0; }
echo "$fails surface(s) wrong for $U"; exit 1
