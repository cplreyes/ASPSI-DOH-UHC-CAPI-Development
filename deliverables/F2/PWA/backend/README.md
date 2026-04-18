# F2 PWA Backend — Apps Script

Apps Script Web App that serves the PWA frontend (see `../app/`). Six routes, HMAC-signed, idempotent.

## One-time deploy

1. `npm install && npm run build` — emits `dist/Code.gs` and `dist/appsscript.json`.
2. Go to https://script.google.com while signed in as `aspsi.doh.uhc.survey2.data@gmail.com`.
3. New project → name it `F2-PWA-Backend`.
4. Paste `dist/Code.gs` into `Code.gs` (replace default contents).
5. Editor → Project Settings → "Show appsscript.json" → paste `dist/appsscript.json`.
6. Run `setupBackend()` from the editor. First run authorizes scopes. Output log shows:
   - Created spreadsheet URL (save it).
   - Generated HMAC_SECRET (first 6 chars — retrieve the full value from Project Settings → Script Properties).
7. Deploy → New deployment → Type: Web app → Execute as: Me → Who has access: Anyone → Deploy. Save the `/exec` URL.

## Rotate the HMAC secret

Run `rotateSecret()` from the editor. Update the PWA's build-time `VITE_F2_HMAC_SECRET` and redeploy the frontend.

## Reset the spreadsheet

Delete the ScriptProperty `SPREADSHEET_ID` and re-run `setupBackend()`. The old spreadsheet remains in Drive for audit.

## Smoke tests

```bash
export BACKEND_URL='https://script.google.com/macros/s/.../exec'
export HMAC_SECRET='…full secret from ScriptProperties…'
bash scripts/smoke.sh
```

Verifies every route, including idempotency (submit replay returns `duplicate`) and batching.

## Request format

- Query params: `?action=<route>&ts=<ms-since-epoch>&sig=<hex-sha256>`.
- HMAC input: `${METHOD}|${action}|${ts}|${body}` with lowercase hex output.
- Body: `application/json` for POSTs, empty string for GETs.
- Response envelope: `{ok: true, data: …}` on success, `{ok: false, error: {code, message}}` on failure.

## Routes

| Action | Method | Body | Response |
|---|---|---|---|
| `submit` | POST | `{client_submission_id, hcw_id, facility_id, spec_version, app_version, submitted_at_client, device_fingerprint, values}` | `{submission_id, status: 'accepted' \| 'duplicate', server_timestamp}` |
| `batch-submit` | POST | `{responses: [<submit payload>, …]}` (max 50) | `{results: [{client_submission_id, submission_id, status, error?}, …]}` |
| `facilities` | GET | — | `{facilities: [<row>, …]}` |
| `config` | GET | — | `{current_spec_version, min_accepted_spec_version, kill_switch, broadcast_message, spec_hash}` |
| `spec-hash` | GET | — | `{spec_hash, current_spec_version}` |
| `audit` | POST | `{event_type, occurred_at_client, hcw_id, facility_id, app_version, payload}` | `{audit_id}` |

## Error codes

| Code | Meaning |
|---|---|
| `E_ACTION_UNKNOWN` | `action` parameter missing or unknown |
| `E_METHOD_UNKNOWN` | Route called with wrong HTTP verb |
| `E_TS_INVALID` | `ts` is not an integer |
| `E_TS_SKEW` | `ts` outside ±5 min window |
| `E_SIG_INVALID` | HMAC mismatch |
| `E_KILL_SWITCH` | Config `kill_switch = true` |
| `E_PAYLOAD_INVALID` | Request body fails shape check |
| `E_SPEC_TOO_OLD` | `spec_version` < `min_accepted_spec_version` |
| `E_VALIDATION` | Payload shape OK but content invalid — also written to F2_DLQ |
| `E_BATCH_TOO_LARGE` | `responses.length > 50` |
| `E_INTERNAL` | Unexpected server error (check Stackdriver) |

## Deferred to later milestones

- **Flat per-item columns in `F2_Responses`.** M4 stores all form values as `values_json` (single column). Flattening happens in M10 when the admin dashboard needs per-column filters.
- **Rate limiting.** Spec §4.3 mentions IP + per-hcw_id limits. Deferred until observed abuse, because HMAC + static API key already block random spam.
- **Sync orchestrator.** PWA-side integration of these routes is M5.
- **Admin dashboard.** HtmlService UI to browse responses + DLQ is M10.
