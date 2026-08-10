#!/usr/bin/env bash
# =============================================================================
# P6 — the SAFE half: §1 drift gate + §5 hardening (+ ships the repointed
# landing page + f2-api dashboard probe). F2-P6-Retirement-and-Hardening.md.
#
# NOTHING here is irreversible — safe to run BEFORE the P5 sign-off. The
# irreversible half (§2 HMAC rotation, §3 CF/Google teardown) stays manual and
# Carl-gated; this script only prepares the ground so P6-day is rotations+
# teardown and nothing else.
#
# Step 0 — ship updated artifacts (run LOCALLY, Git Bash):
#   R=/c/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development
#   scp -i /c/Users/analy/.ssh/aspsi-csweb \
#     "$R/deliverables/CSWeb/csweb-dashboard-gen.py" root@207.148.65.115:/opt/csweb-dashboard-gen.py
#   scp -i /c/Users/analy/.ssh/aspsi-csweb \
#     "$R/deliverables/CSWeb/landing/index.html" root@207.148.65.115:/opt/app/lamp/www/index.html
#   (dashboard-gen gains the f2-api liveness probe; landing's HCW Admin Portal
#    door now points at uhc-hcw.asiansocial.org/admin instead of pages.dev)
#
# Then — ship it and run it AS A FILE with stdin closed. Do NOT use
# `ssh 'bash -s' < script`: `docker compose exec -T` reads stdin, swallows the rest of the
# script text, and the run ends early with a misleading exit 0.
#   scp -i /c/Users/analy/.ssh/aspsi-csweb deploy/p6-hardening-box-steps.sh \
#     root@207.148.65.115:/opt/p6-hardening-box-steps.sh
#   ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115 \
#     'bash /opt/p6-hardening-box-steps.sh </dev/null'
#
# RE-RUNNABLE: every step is idempotent (grep-guarded crons, mkdir -p, upserts).
# =============================================================================
set -euo pipefail
cd /opt/app

echo "== [1/6] P6 §1 drift gate: counts-gate must be ±0 =="
# Non-zero exit = something wrote the frozen Sheet since P4 (paper-encode on the
# old portal). Do NOT proceed to P6 teardown until this is investigated.
python3 /opt/f2-postgres-migration/p4_port_registry.py counts-gate

echo "== [2/6] nightly csweb_f2 dump + f2-files archive (03:15 MNL) =="
mkdir -p /opt/backups/f2
cat > /opt/backups/f2/run-backup.sh <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
cd /opt/app
STAMP=$(date +%F)
MYSQL_ROOT_PASSWORD=$(grep '^MYSQL_ROOT_PASSWORD' /opt/app/.env | cut -d= -f2-)
docker compose exec -T database sh -c "exec mysqldump -uroot -p'$MYSQL_ROOT_PASSWORD' --single-transaction --set-gtid-purged=OFF csweb_f2" \
  </dev/null | gzip > "/opt/backups/f2/csweb_f2-$STAMP.sql.gz"
if [ -d /opt/app/f2-files ]; then
  tar czf "/opt/backups/f2/f2-files-$STAMP.tgz" -C /opt/app f2-files
fi
find /opt/backups/f2 -name 'csweb_f2-*.sql.gz' -mtime +14 -delete
find /opt/backups/f2 -name 'f2-files-*.tgz'   -mtime +14 -delete
EOS
chmod +x /opt/backups/f2/run-backup.sh
crontab -l > "/root/crontab.bak-p6-$(date +%Y%m%d-%H%M%S)"
if ! crontab -l | grep -q 'backups/f2/run-backup.sh'; then
  (crontab -l; echo '15 19 * * * /opt/backups/f2/run-backup.sh >> /var/log/f2-backup.log 2>&1') | crontab -
  echo "   backup cron installed (19:15 UTC = 03:15 MNL)"
else
  echo "   backup cron already present"
fi
# If a borg/borgmatic set covers CSWeb, /opt/backups/f2 (+ /opt/app/f2-files)
# should be added to its source list; this script does not edit unknown configs.
BORG_HITS=$( (grep -rl 'csweb' /etc/borgmatic* /root/.config/borgmatic* 2>/dev/null; crontab -l | grep -i borg) || true )
if [ -n "$BORG_HITS" ]; then
  echo "   MANUAL: add /opt/backups/f2 and /opt/app/f2-files to the borg sources in:"
  echo "$BORG_HITS" | sed 's/^/     /'
else
  echo "   note: no borg/borgmatic config found on-box; nightly local dumps stand alone —"
  echo "         confirm the Elestio panel backup covers /opt/backups + /opt/app/f2-files."
fi

echo "== [3/6] run one backup NOW + verify a restore (§5: one table + one file) =="
/opt/backups/f2/run-backup.sh
MYSQL_ROOT_PASSWORD=$(grep '^MYSQL_ROOT_PASSWORD' /opt/app/.env | cut -d= -f2-)
LATEST=$(ls -t /opt/backups/f2/csweb_f2-*.sql.gz | head -1)
docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" \
  -e "DROP DATABASE IF EXISTS csweb_f2_restoretest; CREATE DATABASE csweb_f2_restoretest" </dev/null
gunzip -c "$LATEST" | docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" csweb_f2_restoretest
LIVE=$(docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -N -e "SELECT COUNT(*) FROM csweb_f2.f2_responses" </dev/null | tr -d '[:space:]')
REST=$(docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -N -e "SELECT COUNT(*) FROM csweb_f2_restoretest.f2_responses" </dev/null | tr -d '[:space:]')
if [ "$LIVE" = "$REST" ]; then
  echo "   table restore verified: f2_responses $REST rows (= live)"
else
  echo "   FAIL: restored f2_responses=$REST != live=$LIVE"; exit 1
fi
docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "DROP DATABASE csweb_f2_restoretest" </dev/null
TARLATEST=$(ls -t /opt/backups/f2/f2-files-*.tgz 2>/dev/null | head -1 || true)
if [ -n "$TARLATEST" ]; then
  FOBJ=$(tar -tzf "$TARLATEST" | grep -v '/$' | head -1 || true)
  if [ -n "$FOBJ" ]; then
    TMPD=$(mktemp -d)
    tar -xzf "$TARLATEST" -C "$TMPD" "$FOBJ"
    cmp "$TMPD/$FOBJ" "/opt/app/$FOBJ" && echo "   file-object restore verified: $FOBJ"
    rm -rf "$TMPD"
  else
    echo "   note: f2-files archive is empty (no file objects yet)"
  fi
else
  echo "   note: no f2-files archive (directory absent) — fine if no admin uploads live on-box"
fi

echo "== [4/6] nightly auth_kv expiry sweep (03:40 MNL) =="
cat > /opt/f2-authkv-sweep.sh <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
cd /opt/app
MYSQL_ROOT_PASSWORD=$(grep '^MYSQL_ROOT_PASSWORD' /opt/app/.env | cut -d= -f2-)
docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" \
  -e "DELETE FROM csweb_f2.auth_kv WHERE expires_at < UTC_TIMESTAMP()" </dev/null
EOS
chmod +x /opt/f2-authkv-sweep.sh
if ! crontab -l | grep -q 'f2-authkv-sweep.sh'; then
  (crontab -l; echo '40 19 * * * /opt/f2-authkv-sweep.sh >> /var/log/f2-authkv-sweep.log 2>&1') | crontab -
  echo "   auth_kv sweep cron installed (19:40 UTC = 03:40 MNL)"
else
  echo "   auth_kv sweep cron already present"
fi
/opt/f2-authkv-sweep.sh && echo "   first sweep ran clean"

echo "== [5/6] regenerate dashboard + verify the f2-api probe =="
if ! grep -q 'f2_api_health' /opt/csweb-dashboard-gen.py; then
  echo "   FAIL: /opt/csweb-dashboard-gen.py is the OLD generator — run step 0 (scp) first"; exit 1
fi
python3 /opt/csweb-dashboard-gen.py
if grep -q '"api": true' /opt/app/lamp/www/docs/dashboard.html; then
  echo "   dashboard shows f2-api: OK"
elif grep -q '"api": false' /opt/app/lamp/www/docs/dashboard.html; then
  echo "   FAIL: probe says f2-api is DOWN — check the f2-api container"; exit 1
else
  echo "   FAIL: probe field missing from payload"; exit 1
fi

echo "== [6/6] landing repoint check + summary =="
if grep -q 'uhc-hcw.asiansocial.org/admin' /opt/app/lamp/www/index.html; then
  echo "   landing HCW Admin Portal door points at uhc-hcw (repointed copy is live)"
else
  echo "   WARN: landing still links pages.dev/admin — step 0's second scp not run yet"
fi
echo
echo "P6 safe-half complete. Still Carl-gated (in order):"
echo "  1. P5 sign-off on #836 (zero open P1s)"
echo "  2. §2 rotate AS HMAC_SECRET in the AS editor  ->  THEN: rm /opt/f2sync/.env  (point of no return)"
echo "  3. §3 teardown: Pages redirect (PWA/redirect-page/), Worker+KV+R2 delete, AS archive + Sheet freeze"
echo "  4. delete as-deploy.yml + cf-pages-deploy.yml from the repo"
echo "Elestio custom-domain registration for uhc-hcw/capi: hand-written vhosts ACCEPTED (plan §5 option b)."
