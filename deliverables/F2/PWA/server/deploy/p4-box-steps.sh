#!/usr/bin/env bash
# =============================================================================
# P4 — Registry + config cutover (greenfield authority flip).
# F2-Prod-Migration-Plan §3 P4. Carl-gated: the authority flip.
#
# After this run: csweb_f2 MySQL is THE store. The old CF/Google stack refuses
# respondent writes (Sheet kill_switch=true) but stays intact + dark for
# rollback until P6 (+30d). The 2-min mirror poller is retired.
#
# Step 0 — ship (run LOCALLY, Git Bash). The server changed at P4 (kill_switch
# gate on /exec + facilities barangay), so the f2-api package re-ships too:
#
#   cd /c/Users/analy/Documents/analytiflow/1_Projects/aspsi-f2-staging-wt/deliverables/F2/PWA/server
#   npx tsc -p tsconfig.json
#   tar czf - package.json package-lock.json dist ddl deploy/Dockerfile \
#     | ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115 \
#       'mkdir -p /opt/f2-api && tar xzf - -C /opt/f2-api \
#        && mv -f /opt/f2-api/deploy/Dockerfile /opt/f2-api/Dockerfile \
#        && rmdir /opt/f2-api/deploy 2>/dev/null; ls /opt/f2-api'
#   scp -i /c/Users/analy/.ssh/aspsi-csweb deploy/p4_port_registry.py \
#     root@207.148.65.115:/opt/f2-postgres-migration/p4_port_registry.py
#   scp -i /c/Users/analy/.ssh/aspsi-csweb \
#     /c/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSWeb/csweb-dashboard-gen.py \
#     root@207.148.65.115:/opt/csweb-dashboard-gen.py
#
# Then this script:
#
#   ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115 'bash -s' \
#     < deploy/p4-box-steps.sh
#
# After it passes, run the LOCAL leg (KV + R2): deploy/p4-local-kv-r2.sh.
# (Run `npx wrangler whoami` BEFORE starting — the local leg needs live
# wrangler auth, and it should be verified before the box is flipped.)
#
# RE-RUNNABLE: preflight/facilities are flip-aware — after a mid-run failure,
# fix the cause and re-run this same command; completed phases no-op/upsert.
# ROLLBACK at any point:
#   python3 /opt/f2-postgres-migration/p4_port_registry.py unflip
#   (+ re-add the poller cron line it prints; crontab backup is kept in /root)
#
# Sequencing rationale (each step depends on the previous):
#   facilities BEFORE flip   — the only facilities reader is the legacy GET,
#                              which kill_switch blocks.
#   flip BEFORE final backfill — freezes RESPONDENT writes, so the backfill
#                              that follows is the last word on the public
#                              path. (The old admin envelope — paper-encode /
#                              DLQ-replay — is NOT gated by kill_switch and
#                              stays writable until P6: old portal is
#                              read-only BY POLICY from here; the closing
#                              counts-gate + a pre-P6 re-run detect drift.)
#   port AFTER flip          — registry reads use the admin envelope, which
#                              is immune to kill_switch (Router.js:27 gates
#                              only the public path).
#   cron removal AFTER counts-gate — the poller stays as a safety net until
#                              the mirror is proven complete.
# =============================================================================
set -euo pipefail
ENGINE="python3 /opt/f2-postgres-migration/p4_port_registry.py"
POLLER="python3 /opt/f2-postgres-migration/sync_f2_to_mysql.py"
MYSQL_IN() { docker exec -i lamp-mysql8 sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot csweb_f2'; }

echo "== [0/10] schema: guarded ALTERs + idempotent DDL re-apply =="
cd /opt/app
# f2_facility_master gains the two FacilityMasterList columns the mirror-era
# table lacked (f2-api readFacilities SELECTs them). Additive + guarded.
MYSQL_IN <<'SQL'
SET @have := (SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema='csweb_f2' AND table_name='f2_facility_master'
  AND column_name='facility_type');
SET @ddl := IF(@have=0,
  'ALTER TABLE f2_facility_master ADD COLUMN facility_type VARCHAR(64) NULL AFTER facility_name',
  'SELECT "facility_type already present"');
PREPARE s FROM @ddl; EXECUTE s; DEALLOCATE PREPARE s;
SET @have := (SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema='csweb_f2' AND table_name='f2_facility_master'
  AND column_name='barangay');
SET @ddl := IF(@have=0,
  'ALTER TABLE f2_facility_master ADD COLUMN barangay VARCHAR(128) NULL AFTER city_mun',
  'SELECT "barangay already present"');
PREPARE s FROM @ddl; EXECUTE s; DEALLOCATE PREPARE s;
SQL
MYSQL_IN < /opt/f2-api/ddl/f2_api_tables.sql

echo "== [1/10] f2-api rebuild (P4 server: /exec kill_switch gate + barangay) =="
docker compose build f2-api
docker compose up -d --no-deps f2-api
sleep 3
curl -sf http://127.0.0.1:8787/api/health && echo

echo "== [2/10] preflight (read-only; width/shape scan happens here, pre-flip) =="
$ENGINE preflight

echo "== [3/10] facilities export (pre-flip; legacy GET) =="
$ENGINE facilities

echo "== [4/10] FLIP — Sheet kill_switch=true (old stack refuses respondent writes) =="
$ENGINE flip

echo "== [5/10] FINAL poller backfill (the last public-path word) =="
cd /opt/app
# take the poller's own flock so a 2-min cron tick (still installed until step 8)
# cannot upsert concurrently with this backfill
set +e
flock /tmp/f2-mysql-sync.lock $POLLER --backfill --env-file /opt/f2sync/.env < /dev/null
BF_EXIT=$?
set -e
if [ $BF_EXIT -ne 0 ]; then
  echo "FINAL BACKFILL had row errors (exit $BF_EXIT) — see output above."
  echo "NOT proceeding. Rollback: $ENGINE unflip"
  exit 1
fi
# Repair Sheets' numeric coercion in the mirrored rows: region-0x codes lost
# their leading zero on the Sheet (qn 12->11 digits, facility_id 9->8), and the
# poller mirrored them verbatim. One leading zero max (no region '00' exists).
MYSQL_IN <<'SQL'
SELECT CONCAT('qn 11-digit rows to repair: ', COUNT(*)) FROM f2_responses WHERE qn REGEXP '^[0-9]{11}$';
UPDATE f2_responses SET qn = LPAD(qn, 12, '0') WHERE qn REGEXP '^[0-9]{11}$';
SELECT CONCAT('facility_id 8-digit rows to repair: ', COUNT(*)) FROM f2_responses WHERE facility_id REGEXP '^[0-9]{8}$';
UPDATE f2_responses SET facility_id = LPAD(facility_id, 9, '0') WHERE facility_id REGEXP '^[0-9]{8}$';
SELECT CONCAT('REVIEW (non-fatal) — odd qn shapes remaining: ', COUNT(*)) FROM f2_responses
  WHERE qn IS NOT NULL AND qn <> '' AND qn NOT REGEXP '^[0-9]{12}$';
SQL

echo "== [6/10] counts gate (Sheet == MySQL, ±0) =="
$ENGINE counts-gate

echo "== [7/10] registry port (hcws/users/roles/config/files/settings/dlq/audit) =="
$ENGINE port

echo "== [8/10] retire the 2-min mirror poller cron =="
crontab -l > "/root/crontab.bak-p4-$(date +%Y%m%d-%H%M%S)"
if crontab -l | grep -q 'sync_f2_to_mysql'; then
  crontab -l | { grep -v 'sync_f2_to_mysql' || true; } | crontab -
  echo "   poller cron removed (backup kept in /root)"
else
  echo "   no poller cron line found — nothing to remove"
fi
if crontab -l | grep -q 'sync_f2_to_mysql'; then echo "poller line still present!"; exit 1; fi

echo "== [9/10] canary — a submit lands ONLY in MySQL =="
$ENGINE canary < /dev/null

echo "== [10/10] closing tripwire + box health =="
$ENGINE counts-gate
docker ps --format '{{.Names}} {{.Status}}' | grep -E 'f2-api|lamp|capi' || true
free -m | head -2
curl -so /dev/null -w 'csweb HTTP %{http_code}\n' https://csweb.asiansocial.org/csweb/
curl -sf https://uhc-hcw.asiansocial.org/api/health && echo
echo
echo "== P4 BOX SIDE DONE. csweb_f2 is authoritative. =="
echo "Next: (a) LOCAL leg deploy/p4-local-kv-r2.sh (KV revocations/audit + R2 files),"
echo "      (b) disable GitHub workflows as-deploy.yml + cf-pages-deploy.yml (GitHub UI),"
echo "      (c) old admin portal is READ-ONLY BY POLICY until P6 (envelope not gated),"
echo "      (d) before P6: re-run '$ENGINE counts-gate' to prove zero Sheet drift,"
echo "      (e) dashboard note refreshes on its next 2-min cron tick."
