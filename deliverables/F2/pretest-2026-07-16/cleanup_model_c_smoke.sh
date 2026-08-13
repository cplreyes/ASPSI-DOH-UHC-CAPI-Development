#!/usr/bin/env bash
# Purge the Model C functional-smoke case from production csweb_f2:
#   - the self-registered HCW  sr-2b86e6ad-c754-4062-8f03-d42f157c9e83  (qn 040340210126)
# Restores the pretest baseline to 25 HCWs / 0 responses.
# (The 1-day facility-token audit row is harmless historical record; the token itself
#  auto-expires and its string was never exposed — no revoke needed.)
set -euo pipefail
KEY=~/.ssh/aspsi-csweb
HOST=root@207.148.65.115

ssh -i "$KEY" "$HOST" 'bash -s' <<'REMOTE'
set -e
RP=$(grep -m1 ROOT_PASSWORD /opt/app/.env | cut -d= -f2- | tr -d "\"'")
docker exec -i lamp-mysql8 mysql -uroot -p"$RP" csweb_f2 <<SQL
SELECT (SELECT COUNT(*) FROM f2_hcws) AS hcw_before, (SELECT COUNT(*) FROM f2_responses) AS resp_before;
SELECT hcw_id, qn, status FROM f2_hcws WHERE hcw_id='sr-2b86e6ad-c754-4062-8f03-d42f157c9e83';
DELETE FROM f2_hcws WHERE hcw_id='sr-2b86e6ad-c754-4062-8f03-d42f157c9e83';
SELECT (SELECT COUNT(*) FROM f2_hcws) AS hcw_after, (SELECT COUNT(*) FROM f2_responses) AS resp_after;
SQL
REMOTE
