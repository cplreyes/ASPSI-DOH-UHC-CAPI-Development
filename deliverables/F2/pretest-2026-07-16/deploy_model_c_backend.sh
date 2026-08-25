#!/usr/bin/env bash
# Deploy the Model C backend (f2-api) to prod (design F2-Model-C-Self-Register-2026-07-16).
# Ships the pre-built dist/ + rebuilds the f2-api container. ADDITIVE endpoints only
# (POST /self-register, POST /admin/api/facility-token); existing enrollment/submit/
# refusal/admin flows are untouched, so the live pretest (models A/B) is unaffected.
# Effect: a brief f2-api container restart (~seconds). Run when no enumerator is mid-sync.
set -euo pipefail
# Self-locating since 2026-08-25. These paths used to be hard-coded into the
# aspsi-f2-staging-wt worktree, which sits on the `staging` branch -- 140 commits
# BEHIND main. Building prod from it is exactly the stale-source failure that
# deploy-f2-pwa.ps1 was written to prevent, only here it was unguarded.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SRV="$REPO/deliverables/F2/PWA/server"
KEY=/c/Users/analy/.ssh/aspsi-csweb
HOST=root@207.148.65.115

echo "→ building fresh dist/ …"
npm --prefix "$SRV" run build

echo "→ shipping f2-api package to /opt/f2-api …"
tar czf - -C "$SRV" package.json package-lock.json dist ddl deploy/Dockerfile \
  | ssh -i "$KEY" "$HOST" 'set -e
      mkdir -p /opt/f2-api
      tar xzf - -C /opt/f2-api
      mv -f /opt/f2-api/deploy/Dockerfile /opt/f2-api/Dockerfile
      rmdir /opt/f2-api/deploy 2>/dev/null || true
      echo "→ rebuilding + restarting the f2-api container …"
      cd /opt/app && docker compose up -d --build f2-api
      sleep 4
      echo "→ health check:"
      curl -s https://uhc-hcw.asiansocial.org/api/health; echo'
echo "→ done. Expect {\"ok\":true,\"service\":\"f2-api\",...} above."
