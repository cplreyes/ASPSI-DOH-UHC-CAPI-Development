#!/usr/bin/env bash
# Purge the Model C on-device end-to-end test from production csweb_f2:
#   - self-registered HCW  sr-7b494d0a-4180-4a2e-a548-776e83b7ea6b  (qn 040340210126)
#   - its refusal response (the device decline)
# Restores the pretest baseline to 25 HCWs / 0 responses.
set -euo pipefail
KEY=~/.ssh/aspsi-csweb
HOST=root@207.148.65.115

ssh -i "$KEY" "$HOST" 'bash -s' <<'REMOTE'
set -e
RP=$(grep -m1 ROOT_PASSWORD /opt/app/.env | cut -d= -f2- | tr -d "\"'")
docker exec -i lamp-mysql8 mysql -uroot -p"$RP" csweb_f2 <<SQL
SELECT (SELECT COUNT(*) FROM f2_hcws) AS hcw_before, (SELECT COUNT(*) FROM f2_responses) AS resp_before;
SELECT hcw_id, qn, status FROM f2_hcws     WHERE hcw_id='sr-7b494d0a-4180-4a2e-a548-776e83b7ea6b';
SELECT qn, hcw_id, status FROM f2_responses WHERE hcw_id='sr-7b494d0a-4180-4a2e-a548-776e83b7ea6b';
DELETE FROM f2_responses WHERE hcw_id='sr-7b494d0a-4180-4a2e-a548-776e83b7ea6b';
DELETE FROM f2_hcws      WHERE hcw_id='sr-7b494d0a-4180-4a2e-a548-776e83b7ea6b';
SELECT (SELECT COUNT(*) FROM f2_hcws) AS hcw_after, (SELECT COUNT(*) FROM f2_responses) AS resp_after;
SQL
REMOTE
