#!/usr/bin/env bash
# =============================================================================
# Deploy Model C — Numbered self-register links — to F2 prod (uhc-hcw.asiansocial.org).
# Full deploy for pretesting, in order: backend -> DDL migration -> frontend -> smoke.
#
# WHAT SHIPS (whole app working tree — coherent, 528/528 app + 80/80 server tests,
# clean tsc + eslint, prod build verified: bundle-secrets/budget/contrast all OK):
#   • Model C: /claim, /admin/api/facility-links, ClaimScreen, FacilityLinksModal,
#     "Facility links" admin button, claim i18n (8 locales)
#   • QN plumbing Model C REQUIRES: qn field threaded enrollment->draft->submission->
#     sync (db.ts adds an OPTIONAL qn field — no Dexie version bump, no forced device
#     migration), verify-token qn read
#   • Tested UI changes that ride along: ReviewSection, MultiSectionForm, LanguageSwitcher,
#     CreateHCWModal (all green in the suite)
#
# The DDL is additive (new nullable columns + one unique index) and idempotent.
# The frontend swap is served live from the f2-www ro-mount (no container restart).
# Existing enrolled devices keep their session (service worker); they pick up the new
# build on next load. Run when no enumerator is mid-sync.
# =============================================================================
set -euo pipefail
SRV="/c/Users/analy/Documents/analytiflow/1_Projects/aspsi-f2-staging-wt/deliverables/F2/PWA/server"
APP="/c/Users/analy/Documents/analytiflow/1_Projects/aspsi-f2-staging-wt/deliverables/F2/PWA/app"
KEY="/c/Users/analy/.ssh/aspsi-csweb"
HOST="root@207.148.65.115"
ORIGIN="https://uhc-hcw.asiansocial.org"

echo "############################################################"
echo "# [0/4] VERSION STAMP — build identifiers for the Versioning panel"
echo "############################################################"
# Apps-tab audit P1-3: the panel showed "unknown" everywhere because nothing
# ever set these env vars. Values land in /opt/app/.env (compose substitution
# source, same mechanism as F2_DB_PASSWORD) BEFORE the f2-api rebuild below.
PWA_VER=$(sed -nE 's/.*"version": *"([^"]+)".*/\1/p' "$APP/package.json" | head -1)
API_VER=$(sed -nE 's/.*"version": *"([^"]+)".*/\1/p' "$SRV/package.json" | head -1)
BUILD_SHA=$(git -C "$APP" rev-parse --short HEAD 2>/dev/null || echo unknown)
# "+" suffix = built from a dirty tree (uncommitted changes on top of the SHA).
git -C "$APP" diff --quiet HEAD -- . 2>/dev/null || BUILD_SHA="${BUILD_SHA}+"
DEPLOYED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "   PWA $PWA_VER ($BUILD_SHA) / API $API_VER @ $DEPLOYED_AT"
ssh -i "$KEY" "$HOST" 'bash -s' <<REMOTE
set -e
# One-time: expose the vars to the f2-api container via compose substitution.
if ! grep -q 'PWA_VERSION' /opt/app/docker-compose.yml; then
  cp /opt/app/docker-compose.yml "/opt/app/docker-compose.yml.bak-\$(date +%Y%m%d-%H%M%S)"
  sed -i 's|^      - PWA_ORIGIN=https://uhc-hcw.asiansocial.org\$|&\n      - PWA_VERSION=\${PWA_VERSION:-}\n      - PWA_BUILD_SHA=\${PWA_BUILD_SHA:-}\n      - API_VERSION=\${API_VERSION:-}\n      - API_DEPLOYED_AT=\${API_DEPLOYED_AT:-}|' /opt/app/docker-compose.yml
  grep -q 'PWA_VERSION' /opt/app/docker-compose.yml || { echo "COMPOSE INJECT FAILED (PWA_ORIGIN anchor not found)"; exit 1; }
  echo "   compose: four env lines added (backup kept alongside)"
fi
# Every deploy: upsert current values into /opt/app/.env (never printed — file holds secrets).
for kv in "PWA_VERSION=$PWA_VER" "PWA_BUILD_SHA=$BUILD_SHA" "API_VERSION=$API_VER" "API_DEPLOYED_AT=$DEPLOYED_AT"; do
  k=\${kv%%=*}
  if grep -q "^\$k=" /opt/app/.env; then sed -i "s|^\$k=.*|\$kv|" /opt/app/.env; else echo "\$kv" >> /opt/app/.env; fi
done
echo "   /opt/app/.env stamped"
REMOTE

echo
echo "############################################################"
echo "# [1/4] BACKEND — build dist + ship + rebuild f2-api"
echo "############################################################"
npm --prefix "$SRV" run build
tar czf - -C "$SRV" package.json package-lock.json dist ddl deploy/Dockerfile \
  | ssh -i "$KEY" "$HOST" 'set -e
      mkdir -p /opt/f2-api
      tar xzf - -C /opt/f2-api
      mv -f /opt/f2-api/deploy/Dockerfile /opt/f2-api/Dockerfile
      rmdir /opt/f2-api/deploy 2>/dev/null || true
      cd /opt/app && docker compose up -d --build f2-api
      sleep 4
      echo "   f2-api health:"; curl -s https://uhc-hcw.asiansocial.org/api/health; echo'

echo
echo "############################################################"
echo "# [2/4] DDL — apply idempotent migration to csweb_f2"
echo "#       (adds enroll_slug / enroll_secret_hmac / claimed_at)"
echo "############################################################"
# Root pw read from /opt/app/.env ON THE BOX and piped straight into mysql — never printed.
# docker gets stdin from the .sql FILE (explicit <), so it never steals the bash -s heredoc.
ssh -i "$KEY" "$HOST" 'bash -s' <<'REMOTE'
set -e
RP=$(grep -m1 ROOT_PASSWORD /opt/app/.env | cut -d= -f2- | tr -d "\"'")
docker exec -i lamp-mysql8 mysql -uroot -p"$RP" csweb_f2 < /opt/f2-api/ddl/f2_api_tables.sql
echo "   f2_hcws enroll columns after migration:"
docker exec -i lamp-mysql8 mysql -uroot -p"$RP" csweb_f2 -e "SHOW COLUMNS FROM f2_hcws LIKE 'enroll_%'; SHOW COLUMNS FROM f2_hcws LIKE 'claimed_at';"
REMOTE

echo
echo "############################################################"
echo "# [3/4] FRONTEND — build app + ship to /opt/app/f2-www"
echo "############################################################"
( cd "$APP" && VITE_F2_PROXY_URL="$ORIGIN" npm run build )
tar czf - -C "$APP/dist" . \
  | ssh -i "$KEY" "$HOST" 'set -e
      mkdir -p /opt/app/f2-www
      find /opt/app/f2-www -mindepth 1 -delete
      tar xzf - -C /opt/app/f2-www
      echo "   f2-www repopulated:"; ls /opt/app/f2-www | head'

echo
echo "############################################################"
echo "# [4/4] SMOKE — non-mutating public probes"
echo "############################################################"
echo -n "   /api/health   : "; curl -sf "$ORIGIN/api/health"; echo
echo -n "   SPA index     : "; curl -s "$ORIGIN/" | grep -q '<html' && echo "OK (<html> served)" || echo "MISS"
c=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$ORIGIN/claim" -H 'content-type: application/json' -d '{}')
echo "   POST /claim    : $c (expect 401 — route live, bad slug rejected; 404 = not deployed)"
c=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$ORIGIN/admin/api/facility-links" -H 'content-type: application/json' -d '{}')
echo "   facility-links : $c (expect 401 — route live, needs admin auth; 404 = not deployed)"
echo
echo "== DONE. Model C is live. In F2 Admin -> Data -> HCWs, the 'Facility links' button"
echo "   now appears; generate the pretest facility's links there."
