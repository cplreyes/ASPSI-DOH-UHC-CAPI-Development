#!/usr/bin/env bash
# One chrome, one stylesheet. This script exists because the console had two
# copies of portal.css that silently diverged: /opt/portal.css carried a mobile
# topbar fix that /opt/app/capi-www/portal.css did not, so every portal page
# scrolled sideways on a phone while the dashboard behaved. Found 2026-08-09.
set -euo pipefail

REPO="${1:?usage: verify-chrome.sh <repo-CSWeb-dir> [ssh-target]}"
SSH="${2:-root@207.148.65.115}"
KEY="${KEY:-$HOME/.ssh/aspsi-csweb}"
fails=0

say() { printf '%-58s %s\n' "$1" "$2"; }

# 1. the repo must hold exactly one of each
for stray in "$REPO/capi-portal/portal_shell.py" "$REPO/capi-portal/portal.css"; do
  if [ -e "$stray" ]; then say "stray duplicate $stray" "FAIL"; fails=$((fails+1));
  else say "no duplicate $(basename "$stray")" "ok"; fi
done

# 2. build_portal.py must not have regrown its own chrome
if grep -qE '^_NAV = \[|^def _sidebar\(|^_PILL_LOCK' "$REPO/capi-portal/build_portal.py"; then
  say "build_portal.py defines its own chrome" "FAIL"; fails=$((fails+1))
else
  say "build_portal.py has no cloned chrome" "ok"
fi

# 3. the deployed copies must be byte-identical to the repo
local_css=$(md5sum "$REPO/portal.css" | cut -d' ' -f1)
remote=$(ssh -i "$KEY" -o StrictHostKeyChecking=no "$SSH" \
  'md5sum /opt/portal.css /opt/app/capi-www/portal.css /opt/portal_shell.py' 2>/dev/null)
for want in /opt/portal.css /opt/app/capi-www/portal.css; do
  got=$(echo "$remote" | awk -v f="$want" '$2==f {print $1}')
  if [ "$got" = "$local_css" ]; then say "$want matches repo" "ok";
  else say "$want DIVERGED ($got)" "FAIL"; fails=$((fails+1)); fi
done

local_shell=$(md5sum "$REPO/portal_shell.py" | cut -d' ' -f1)
got=$(echo "$remote" | awk '$2=="/opt/portal_shell.py" {print $1}')
if [ "$got" = "$local_shell" ]; then say "/opt/portal_shell.py matches repo" "ok";
else say "/opt/portal_shell.py DIVERGED ($got)" "FAIL"; fails=$((fails+1)); fi

echo
if [ "$fails" -eq 0 ]; then echo "chrome verified: one shell, one stylesheet"; exit 0; fi
echo "$fails check(s) failed"; exit 1
