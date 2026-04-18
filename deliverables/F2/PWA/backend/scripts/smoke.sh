#!/usr/bin/env bash
# Smoke-test every M4 route against a deployed Apps Script Web App.
# Requires: BACKEND_URL, HMAC_SECRET in env.
# Run: bash scripts/smoke.sh

set -euo pipefail

: "${BACKEND_URL:?set BACKEND_URL to your Web App /exec URL}"
: "${HMAC_SECRET:?set HMAC_SECRET to the value from ScriptProperties}"

sign() {
  node scripts/sign.mjs "$@"
}

section() { printf '\n===== %s =====\n' "$1"; }

section "GET ?action=config"
eval "$(sign GET config)" | tee /tmp/f2-config.json
echo

section "GET ?action=spec-hash"
eval "$(sign GET spec-hash)"
echo

section "GET ?action=facilities"
eval "$(sign GET facilities)" | head -c 300
echo

section "POST ?action=audit"
BODY='{"event_type":"smoke_test","occurred_at_client":'"$(node -e 'console.log(Date.now())')"',"app_version":"smoke","payload":{"script":"smoke.sh"}}'
eval "$(sign POST audit "$BODY")"
echo

section "POST ?action=submit (idempotent — run twice)"
CID="smoke-$(node -e 'console.log(Date.now())')"
BODY='{"client_submission_id":"'"$CID"'","hcw_id":"smoke-hcw","facility_id":"smoke-fac","spec_version":"2026-04-17-m1","app_version":"smoke","submitted_at_client":'"$(node -e 'console.log(Date.now())')"',"device_fingerprint":"smoke-node","values":{"Q2":"Regular","Q3":"Female","Q4":30,"Q5":"Nurse","Q7":"No","Q10":5,"Q11":8}}'
eval "$(sign POST submit "$BODY")"
echo
echo "-- replay same submission (expect duplicate) --"
eval "$(sign POST submit "$BODY")"
echo

section "POST ?action=batch-submit"
BCID1="smoke-b1-$(node -e 'console.log(Date.now())')"
BCID2="smoke-b2-$(node -e 'console.log(Date.now())')"
BATCH='{"responses":[{"client_submission_id":"'"$BCID1"'","hcw_id":"smoke-hcw","facility_id":"smoke-fac","spec_version":"2026-04-17-m1","submitted_at_client":'"$(node -e 'console.log(Date.now())')"',"values":{"Q2":"Casual"}},{"client_submission_id":"'"$BCID2"'","hcw_id":"smoke-hcw","facility_id":"smoke-fac","spec_version":"2026-04-17-m1","submitted_at_client":'"$(node -e 'console.log(Date.now())')"',"values":{"Q2":"Regular"}}]}'
eval "$(sign POST batch-submit "$BATCH")"
echo

echo
echo "Smoke tests complete. Open the spreadsheet in Sheets to verify rows landed."
