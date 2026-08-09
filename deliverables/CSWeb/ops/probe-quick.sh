#!/usr/bin/env bash
# Quick status probe with a signed-in session. Not the full role x URL matrix
# (that is probe-surfaces.sh, Slice 4); this one answers "what does THIS
# account see on THESE paths right now".
#
#   probe-quick.sh <username> <password> <path> [<path>...]
set -euo pipefail
U="${1:?username}"; PW="${2:?password}"; shift 2
BASE="https://capi.asiansocial.org"
JAR=$(mktemp); trap 'rm -f "$JAR"' EXIT

# Sign-in is double-submit CSRF: GET the form (mints the __Host-capi_csrf
# cookie and embeds the matching token), then POST it back with the creds.
csrf=$(curl -sS -c "$JAR" "$BASE/docs/idp/login" \
  | grep -oP 'name="csrf" value="\K[^"]+' | head -1)
if [ -z "$csrf" ]; then echo "no csrf token on the login form"; exit 1; fi

curl -sS -b "$JAR" -c "$JAR" -o /dev/null \
  -d "username=$U" -d "password=$PW" -d "csrf=$csrf" "$BASE/docs/idp/login"

# The only reliable success signal is the session actually working.
me=$(curl -sS -b "$JAR" "$BASE/docs/idp/me")
case "$me" in
  *'"signed_in":true'*) ;;
  *) echo "sign-in failed for $U: $me"; exit 1 ;;
esac

for p in "$@"; do
  printf '%-42s %s\n' "$p" \
    "$(curl -sS -b "$JAR" -o /dev/null -w '%{http_code}' "$BASE$p")"
done
