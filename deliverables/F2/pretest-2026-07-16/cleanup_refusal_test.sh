#!/usr/bin/env bash
# Purge the 2026-07-15 live refusal-test data from production csweb_f2:
#   - the throwaway HCW  REFUSAL-TEST  (qn 040340210126)
#   - its single refusal response row
# Restores the pretest baseline to: 0 responses, 25 HCWs.
# Mirrors the facility-fix access pattern (SSH -> lamp-mysql8 -> csweb_f2).
set -euo pipefail
KEY=~/.ssh/aspsi-csweb
HOST=root@207.148.65.115

ssh -i "$KEY" "$HOST" 'bash -s' <<'REMOTE'
set -e
RP=$(grep -m1 ROOT_PASSWORD /opt/app/.env | cut -d= -f2- | tr -d "\"'")
docker exec -i lamp-mysql8 mysql -uroot -p"$RP" csweb_f2 <<SQL
SELECT (SELECT COUNT(*) FROM f2_responses) AS resp_before, (SELECT COUNT(*) FROM f2_hcws) AS hcw_before;
SELECT qn, hcw_id, status FROM f2_responses WHERE hcw_id='REFUSAL-TEST';
DELETE FROM f2_responses WHERE hcw_id='REFUSAL-TEST';
DELETE FROM f2_hcws      WHERE hcw_id='REFUSAL-TEST';
SELECT (SELECT COUNT(*) FROM f2_responses) AS resp_after, (SELECT COUNT(*) FROM f2_hcws) AS hcw_after;
SQL
REMOTE
