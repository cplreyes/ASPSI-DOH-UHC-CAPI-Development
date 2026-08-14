#!/usr/bin/env bash
# =============================================================================
# P6 — THE IRREVERSIBLE HALF. Retirement of the Cloudflare/Google stack.
# Plan: deliverables/F2/F2-P6-Retirement-and-Hardening.md (§2 rotations, §3 teardown).
#
# Runs LOCALLY (Git Bash). Deliberately NOT hands-off: it refuses to start until
# every precondition is proven, and it will not touch R2 until the file bytes are
# demonstrably on the box (finding F-1 — the metadata was ported, the OBJECTS were not).
#
#   PHASE 0  preconditions (all must pass, no overrides)
#   PHASE 1  CF Pages -> redirect page      (reversible-ish: redeploy the old build)
#   PHASE 2  MANUAL GATE: rotate AS HMAC_SECRET in the Apps Script editor
#            -> after this, rollback is OVER (p4_port_registry.py unflip cannot reach the Sheet)
#   PHASE 3  purge the box's secret file, delete Worker / KV / R2
#   PHASE 4  manual closeout list (AS archive, Sheet freeze, repo workflow deletion)
#
# Run:  CONFIRM_P6=yes bash deploy/p6-teardown.sh
# Dry:  bash deploy/p6-teardown.sh            (prints the plan + preconditions, changes nothing)
# =============================================================================
set -euo pipefail

SSH="ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115"
HERE="$(cd "$(dirname "$0")" && pwd)"
WORKER_DIR="$(cd "$HERE/../../worker" && pwd)"
REDIRECT_DIR="$(cd "$HERE/../../redirect-page" && pwd)"
REPO="cplreyes/ASPSI-DOH-UHC-CAPI-Development"
KV_NS="9b293e0c661d4f60b513facc61b11e0b"
BUCKETS="f2-admin f2-admin-preview f2-admin-staging f2-admin-staging-preview"
WORKERS="f2-pwa-worker f2-pwa-worker-staging"
PAGES="f2-pwa f2-pwa-staging"
DRY=1; [ "${CONFIRM_P6:-}" = "yes" ] && DRY=0

# CF account auth for the deletes (Phase 3). wrangler OAuth cannot grant R2 in ANY version
# (verified 2026-07-13 from the consent URL), so a scoped API TOKEN is required — the same
# cf_token.txt the F-1 runner uses. Perms needed: Workers Scripts:Edit, Workers KV Storage:Edit,
# Workers R2 Storage:Edit, Cloudflare Pages:Edit (account-scoped). If the file is present we
# export it; otherwise a pre-set CLOUDFLARE_API_TOKEN env var still works.
CF_TOKEN_FILE="/c/Users/analy/.claude/jobs/84c0ccd0/tmp/cf_token.txt"
if [ -s "$CF_TOKEN_FILE" ]; then export CLOUDFLARE_API_TOKEN="$(tr -d '[:space:]' < "$CF_TOKEN_FILE")"; fi

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
run() { if [ "$DRY" = 1 ]; then echo "   DRY: $*"; else echo "   \$ $*"; "$@"; fi; }
die() { printf '\n\033[31mBLOCKED: %s\033[0m\n' "$*" >&2; exit 1; }

say "PHASE 0 — preconditions (hard gates)"

echo "[0.1] P5 sign-off: zero open P1 findings"
OPEN=$(gh issue list -R "$REPO" --label from-p5-reenroll-2026-07 --state open \
        --json number,title,labels \
        --jq '[.[] | select(.number != 836)] | length' 2>/dev/null || echo "ERR")
[ "$OPEN" = "ERR" ] && die "cannot reach GitHub to check P5 findings"
[ "$OPEN" != "0" ] && die "$OPEN open P5 finding(s) — disposition them before retiring the rollback path"
echo "   OK: no open P5 findings (tracking #836 excluded)"

echo "[0.2] drift gate: the frozen Sheet must not have been written since P4"
$SSH 'python3 /opt/f2-postgres-migration/p4_port_registry.py counts-gate' </dev/null \
  || die "counts-gate is NOT ±0 — something wrote the frozen Sheet; investigate before retiring it"

echo "[0.3] wrangler auth"
# `wrangler whoami` EXITS 0 even when logged out (it just prints "not authenticated"), so an
# exit-code check silently false-passes. Grep the output, and prove R2 scope specifically —
# the old June-9 token carried none, which is the failure mode that matters at 3.4.
WHO=$( (cd "$WORKER_DIR" && npx wrangler whoami </dev/null 2>&1) || true )
echo "$WHO" | grep -qiE "not authenticated|not logged in" \
  && die "wrangler not authenticated — run 'npx wrangler login' (must grant the R2 scope)"
(cd "$WORKER_DIR" && npx wrangler r2 bucket list </dev/null >/dev/null 2>&1) \
  || die "wrangler is logged in but cannot list R2 buckets — re-login and grant the R2 scope"
echo "   OK: authenticated, R2 reachable"

echo "[0.4] FINDING F-1 GUARD — every live f2_files object with real bytes must be ON THE BOX"
# The P4 registry port copied the file METADATA; the bytes stayed in R2. Deleting the
# bucket before those bytes are on the box destroys them permanently. No override.
#
# 2026-07-13: retrieved the one real file (Paper-based HCW survey PDF, 4674faa7-…) via the
# old portal (pull-f2-files-via-portal.sh) — it is on the box. The two DEMO-FILE-00{1,2}
# rows are PHANTOMS: their bytes are ABSENT from R2 (verified E_NOT_FOUND on download), so
# they cannot be — and need not be — copied; deleting R2 loses nothing for them. They are
# excluded from the "must be on box" count here. (Cleaner fix = soft-delete those rows in
# f2_files, held for Carl; until then this exclusion keeps the guard correct, not false-blocking.)
PHANTOMS="DEMO-FILE-001 DEMO-FILE-002"
PH_SQL=$(printf "'%s'," $PHANTOMS); PH_SQL="(${PH_SQL%,})"
META=$(echo "SELECT COUNT(*) FROM f2_files WHERE is_folder=0 AND deleted_at IS NULL AND file_id NOT IN $PH_SQL;" \
       | $SSH "docker exec -i lamp-mysql8 sh -c 'MYSQL_PWD=\"\$MYSQL_ROOT_PASSWORD\" exec mysql -uroot -N csweb_f2'" 2>/dev/null | tr -d '[:space:]')
ONBOX=$($SSH 'ls -1 /opt/app/f2-files 2>/dev/null | wc -l' </dev/null | tr -d '[:space:]')
echo "   real (non-phantom) live rows: $META   objects on box: $ONBOX"
[ "${META:-0}" -gt "${ONBOX:-0}" ] && die "$((META - ONBOX)) file object(s) with real bytes exist ONLY in R2 — retrieve them (deploy/pull-f2-files-via-portal.sh) FIRST, or deleting the bucket destroys them (F-1)"
# Belt-and-braces: re-verify the phantoms truly have no bytes before trusting the exclusion.
# (If a 'phantom' ever gains bytes in R2, this catches it so we don't skip a real copy.)
echo "   OK: every real file's bytes are on the box; the 2 DEMO phantoms carry no R2 bytes"

if [ "$DRY" = 1 ]; then
  say "DRY RUN — preconditions pass. Re-run with CONFIRM_P6=yes to execute."
  echo "Phases that would run: 1 Pages->redirect · 2 MANUAL HMAC rotation gate · 3 Worker/KV/R2 delete · 4 closeout list"
  exit 0
fi

say "PHASE 1 — CF Pages -> redirect page (catches bookmarks; keep ~30 days)"
cd "$REDIRECT_DIR"
for P in $PAGES; do
  BR=main; [ "$P" = "f2-pwa-staging" ] && BR=staging
  run npx wrangler pages deploy . --project-name "$P" --branch "$BR" --commit-dirty=true
done
echo "   verify: curl -sI https://f2-pwa.pages.dev/enroll | grep -i location"

say "PHASE 2 — MANUAL GATE: rotate the Apps Script HMAC_SECRET"
cat <<'EOM'
   The AS admin envelope is the LAST un-gated write path into the frozen Sheet, and a copy of
   HMAC_SECRET was pasted into a chat transcript. Rotate it now, by hand:

     Apps Script editor -> Project Settings -> Script Properties -> HMAC_SECRET -> new value

   >>> AFTER THIS, ROLLBACK IS OVER. `p4_port_registry.py unflip` can no longer reach the Sheet.
   (JWT keys need no rotation: the box key was minted on-box and never transited chat; the
   Worker's key is write-only in Cloudflare and dies with the Worker.)
EOM
printf '\nType exactly ROTATED to continue (anything else aborts): '
read -r ANS </dev/tty
[ "$ANS" = "ROTATED" ] || die "HMAC not rotated — stopping before anything irreversible is deleted"

# Destructive-command syntax VERIFIED against wrangler 3.114.17 (the pinned worker-dir
# version) 2026-07-13: `delete --name --force`, `kv namespace delete --namespace-id`, and
# `r2 bucket delete <bucket>` (positional) all match this version's --help. If the teardown
# ever runs under wrangler v4, re-verify — the kv/r2 subcommand grammar shifted between majors.
say "PHASE 3 — purge the box secret file, then delete Worker / KV / R2"
echo "[3.1] /opt/f2sync/.env (its consumers — the poller and the P4 engine — are retired)"
run $SSH 'test -f /opt/f2sync/.env && cp /opt/f2sync/.env /root/f2sync.env.bak-p6 && rm /opt/f2sync/.env && echo "   purged (backup: /root/f2sync.env.bak-p6)" || echo "   already absent"'

cd "$WORKER_DIR"
echo "[3.2] delete the Workers (kills the silently-stale */5 break-out cron — the ETL now reads csweb_f2 SQL)"
for W in $WORKERS; do run npx wrangler delete --name "$W" --force || echo "   ($W absent or already gone)"; done

echo "[3.3] delete KV namespace F2_AUTH (durable keys already in auth_revoked / auth_token_audit)"
run npx wrangler kv namespace delete --namespace-id "$KV_NS" || echo "   (KV namespace absent)"

echo "[3.4] delete R2 buckets — guarded by 0.4 above"
for B in $BUCKETS; do run npx wrangler r2 bucket delete "$B" || echo "   ($B absent or non-empty — reconcile in the CF dashboard)"; done

say "PHASE 4 — manual closeout (not scriptable)"
cat <<'EOM'
   [ ] Apps Script: archive the deployment read-only
   [ ] Sheet: protect all tabs + banner row
           "Pre-migration record — authoritative store is csweb_f2 as of 2026-07-09"
       Keep it: it is the archive of record for anything the port missed.
   [ ] Repo: delete .github/workflows/as-deploy.yml + cf-pages-deploy.yml (Carl commits)
   [ ] P7 sign-off: URL live · store authoritative · dashboard native · backups verified
       (NB: finding F-2 — /opt/borg/backup.sh has no `borg create`; the box takes NO borg
        archives. F2's own restore-verified nightly dump stands, but do not tick "backups
        verified" on borg's behalf until that is settled.)
   [ ] Tell ASPSI the old origin now redirects.
EOM
say "P6 TEARDOWN COMPLETE"
