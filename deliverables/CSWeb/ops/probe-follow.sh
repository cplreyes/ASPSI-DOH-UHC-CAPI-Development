#!/usr/bin/env bash
# Signed-in redirect-chain probe: sign in once, then follow redirects and
# report hop count + final URL + final status for each path. The check that
# matters after a URL move: exactly ONE hop from the old URL, landing 200.
#
#   probe-follow.sh <username> <password> <path> [<path>...]
set -euo pipefail
U="${1:?username}"; PW="${2:?password}"; shift 2
BASE="https://capi.asiansocial.org"
JAR=$(mktemp); trap 'rm -f "$JAR"' EXIT

csrf=$(curl -sS -c "$JAR" "$BASE/docs/idp/login" \
  | grep -oP 'name="csrf" value="\K[^"]+' | head -1)
[ -n "$csrf" ] || { echo "no csrf token"; exit 1; }
curl -sS -b "$JAR" -c "$JAR" -o /dev/null \
  -d "username=$U" -d "password=$PW" -d "csrf=$csrf" "$BASE/docs/idp/login"
curl -sS -b "$JAR" "$BASE/docs/idp/me" | grep -q '"signed_in":true' \
  || { echo "sign-in failed"; exit 1; }

for p in "$@"; do
  out=$(curl -sSL -b "$JAR" -o /dev/null \
    -w '%{num_redirects} %{http_code} %{url_effective}' "$BASE$p")
  printf '%-34s hops=%s code=%s -> %s\n' "$p" $out
done
