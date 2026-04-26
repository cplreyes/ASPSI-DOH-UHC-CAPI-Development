# F2 PWA Backend Auth Re-architecture — Design

**Date:** 2026-04-26
**Status:** Draft, eng-reviewed 2026-04-26, pending implementation plan
**Owner:** Carl Patrick Reyes
**Drives:** mitigation of CRITICAL finding from `.gstack/security-reports/2026-04-25T154000.json`

## 1. Problem

The F2 PWA's Apps Script backend authenticates requests with an HMAC signature scheme. The signing secret is read at build time as `VITE_F2_HMAC_SECRET` and inlined into `dist/assets/*.js` by Vite. Because the bundle is served publicly from Cloudflare Pages, anyone who downloads the staging URL can extract the 64-character hex secret and forge requests against the `/exec` endpoint, which has no other auth layer (`appsscript.json` declares `executeAs: USER_DEPLOYING`, `access: ANYONE_ANONYMOUS`).

Confirmed exposure surface across the six handlers (`handleSubmit`, `handleBatchSubmit`, `handleAudit`, `handleFacilities`, `handleConfig`, `handleSpecHash`):

- Submit fabricated survey responses
- Read all submitted responses + audit log
- Read facility master list
- Read or modify runtime config (`kill_switch`, `broadcast_message`, spec versioning)

Real DOH PII for UHC Survey Year 2 is supposed to land in this spreadsheet. The current model is incompatible with that.

## 2. Design decisions (resolved during brainstorming)

| # | Question | Decision |
|---|---|---|
| 1 | What identity exists for enumerators? | ASPSI maintains a roster (named, facility-assigned), no SSO / Google Workspace |
| 2 | How do enumerators prove they're on the roster? | Per-tablet token, burned in by ops during provisioning; the device IS the enrollment |
| 3 | How do tablets map to enumerators? | Mixed: some 1:1, some shared per facility. Therefore: tablet token = authorisation, in-app `hcw_id` = audit signal |
| 4 | Where is the auth boundary? | Cloudflare Worker proxy in front of Apps Script. HMAC stays server-side forever. |

## 3. Architecture

```
┌─────────────────┐    Bearer JWT     ┌────────────────────┐    HMAC     ┌───────────────────┐
│ Tablet (PWA)    │──────────────────▶│ Cloudflare Worker  │────────────▶│ Apps Script /exec │
│ Vite + React    │                   │  /exec  /admin/*   │             │  + Spreadsheet    │
│ Dexie + token   │◀──────────────────│  KV: revocation    │◀────────────│                   │
└─────────────────┘                   │  Secrets: JWT_KEY, │             └───────────────────┘
                                      │   APPS_SCRIPT_HMAC,│
                                      │   ADMIN_PASSWORD   │
                                      └────────────────────┘
                                                ▲
                                          /admin/issue-token (browser, password-gated)
                                                │
                                            ┌─────┐
                                            │ Ops │
                                            └─────┘
```

### Components

**Tablet (PWA, modified):**

- Removes all references to `VITE_F2_HMAC_SECRET`
- Stores a per-tablet JWT in a new `device_token` field on the existing Dexie enrollment row (schema v2 → v3)
- Sends `Authorization: Bearer <jwt>` on every request
- Talks only to the Worker, never to Apps Script directly

**Cloudflare Worker (new):**

- Single Worker serving two surfaces:
  - `/exec` — proxy for tablet traffic
  - `/admin/*` — token issuance, revocation, audit (HTML + small JSON API)
- Holds three Worker secrets: `JWT_SIGNING_KEY` (32-byte random for HS256), `APPS_SCRIPT_HMAC` (the secret rotated on Apps Script), `ADMIN_PASSWORD` (bcrypt-hashed, compared with `crypto.subtle.timingSafeEqual`)
- Workers KV namespace for revocation list (key: `revoked:<jti>`, TTL: remaining JWT lifetime) and token audit (key: `token:<jti>` → metadata)

**Apps Script (existing, minor changes):**

- `PROP_HMAC_SECRET` rotated to a fresh 64-char hex value (the Worker holds it)
- `PROP_ADMIN_SECRET` and the `?action=admin` HTML deleted (admin moves to the Worker)
- `verifyRequest()` is unchanged — Apps Script trusts only requests bearing a valid HMAC, which only the Worker can produce
- Web app deployment stays at `executeAs: USER_DEPLOYING`, `access: ANYONE_ANONYMOUS`. The Worker is the only legitimate caller; the HMAC is the gate

### Trust boundaries

| Boundary | Mechanism | Failure mode |
|---|---|---|
| Tablet → Worker | JWT bearer (HS256) | Token theft is contained: revokable in <60s via KV |
| Worker → Apps Script | HMAC over canonicalised request | HMAC never leaves Worker secrets; cannot be exfiltrated via client |
| Ops → Worker admin | ADMIN_PASSWORD over HTTPS, HttpOnly session cookie | Brute-force resistance via timing-safe compare + Cloudflare rate limit |

The HMAC physically cannot end up in the client bundle, because no PWA build step knows the value.

## 4. Data flow

### 4.1 Provisioning (one-off per tablet, by ops)

1. Ops opens `https://<worker>.workers.dev/admin/`, enters `ADMIN_PASSWORD`. Worker sets a 1-hour HttpOnly session cookie.
2. Ops fills the issuance form: facility (dropdown, sourced from Apps Script via the Worker's own authorised call), tablet label (free text, e.g. "Tablet-3 / Manila General"), TTL (default 30 days, ops can override per token).
3. Worker mints a JWT with claims:
   ```json
   {
     "jti": "<uuid v4>",
     "tablet_id": "<uuid v4>",
     "facility_id": "F-001",
     "iat": 1714665600,
     "exp": 1722441600
   }
   ```
4. Worker writes `token:<jti>` to KV with metadata `{ tablet_label, facility_id, issued_at, issued_by_session, exp }` for audit.
5. Worker renders the JWT as both a copyable string and a QR code (small QR lib bundled into the Worker response).
6. Ops scans/types the token into the tablet's enrollment screen.

### 4.2 Tablet enrollment (one-off per tablet, by enumerator)

1. PWA enrollment screen (extended): three input modes — "Paste token", "Scan QR", "Manual entry".
2. PWA POSTs the token to Worker `/verify-token` (public endpoint — verification is the auth). Worker returns claims `{ facility_id, exp }` if valid, 401 otherwise.
3. PWA writes the raw JWT into the existing Dexie singleton enrollment row as a single `device_token` field. Claims (`facility_id`, `exp`) are parsed from the JWT on demand, not cached separately, so the two can never drift.
4. PWA reads `facility_id` from the token claim and filters the existing facility/enumerator picker to that facility only. The Worker does not need to enforce this; it's a UX guardrail. Server-side, the JWT's `facility_id` is informational, and Apps Script handlers continue to accept whatever `hcw_id` / `facility_id` the body specifies (we are not partitioning data by facility on the server).
5. `hcw_id` is captured as today and stored alongside `device_token`.
6. On every subsequent app boot, the PWA loads the device token. If missing, expired, or 401 from a real request, it lands on the enrollment screen.

### 4.3 Interview submission (every interview)

1. PWA → `POST https://<worker>.workers.dev/exec?action=handleSubmit`
   - Header: `Authorization: Bearer <jwt>`
   - Header: `Content-Type: text/plain` (preflight-free, matching existing pattern)
   - Body: canonical JSON payload (already includes `hcw_id`, `client_submission_id`, etc.)
2. Worker:
   - Parses + verifies JWT signature with `JWT_SIGNING_KEY`
   - Checks `exp`
   - Looks up `revoked:<jti>` in KV
   - On any failure: 401 with structured error code (see §6)
3. Worker computes the HMAC over `(method, action, ts, body)` using `APPS_SCRIPT_HMAC` — same canonicalisation as the existing client code, so Apps Script's `verifyRequest()` is unchanged.
4. Worker forwards to `https://script.google.com/macros/s/<id>/exec?action=handleSubmit&ts=...&sig=...`.
5. Apps Script verifies HMAC, dispatches to handler, returns JSON.
6. Worker passes the response back to the PWA verbatim.

### 4.4 Revocation (tablet lost or enumerator removed from roster)

1. Ops opens `/admin/`, authenticates, navigates to "Active tokens" filtered by facility or tablet label.
2. Clicks "Revoke" on the affected entry.
3. Worker writes `revoked:<jti>` to KV with TTL = `(jwt.exp − now)`.
4. Cloudflare KV propagates the new entry globally in <60s.
5. The next request bearing that JWT returns 401 `E_TOKEN_REVOKED`.

## 5. Token format

JWT, HS256, claims:

| Claim | Type | Purpose |
|---|---|---|
| `jti` | UUID v4 | Per-token identity for revocation lookup |
| `tablet_id` | UUID v4 | Stable identifier for the device (logged in audit, may persist across reissue) |
| `facility_id` | string | Scopes the enumerator picker; informational on the server |
| `iat` | int (epoch s) | Issued at |
| `exp` | int (epoch s) | Expiry |

- Default TTL: **30 days**. Ops re-provisions tablets monthly. The 30-day window bounds the blast radius of a stolen tablet to one month, even if ops misses the loss event.
- No silent renewal. After expiry, ops re-issues. Forces a periodic provisioning cadence and acts as a soft revocation.
- Tablet stores the raw JWT in IndexedDB (Dexie singleton), not localStorage. Claims are parsed on demand.
- Issuer can override TTL per token at issuance time when needed (e.g., a 7-day token for a temporary tablet).

## 6. Error handling

| Scenario | Worker response | PWA behaviour |
|---|---|---|
| Invalid JWT signature | `401 { code: "E_TOKEN_INVALID" }` | Lock UI, message: "Tablet authorisation invalid — contact ASPSI ops" |
| Expired JWT | `401 { code: "E_TOKEN_EXPIRED" }` | Re-enrolment screen, message: "Tablet token expired — paste a new token from ops" |
| Revoked JWT | `401 { code: "E_TOKEN_REVOKED" }` | Re-enrolment screen, message: "Tablet revoked by ops — contact them for a new token" |
| Malformed bearer header | `400 { code: "E_BAD_REQUEST" }` | Treated as fatal; logged to console |
| Worker unreachable (network error, 5xx) | n/a | Existing offline queue path: submissions stay in `pending_sync` Dexie store, retried by `sync-orchestrator`. Bounded by Dexie storage on the tablet (~MBs of survey data, days of fieldwork). |
| Apps Script quota exhausted (Workspace tier ~6k req/day) | `503 { code: "E_BACKEND_BUSY" }` (Worker detects the quota response from Apps Script and translates it) | PWA shows "backend at capacity, retry in 1h" and pauses the sync queue with backoff, instead of silently retrying every 5 minutes and amplifying the problem. |
| Apps Script returns error | Worker passes JSON through | Existing `E_INTERNAL` handling unchanged |

The PWA's existing offline queue is unaffected by the auth change. Sync orchestrator continues to retry failed submissions; only the auth layer in front of `/exec` changes. The Worker is now a single point of failure for real-time sync, but enumerator UX is preserved by the offline queue: tablets keep accepting submissions during a Worker outage, and the queue drains when the Worker returns.

## 7. What changes where

### 7.1 Apps Script (`deliverables/F2/PWA/backend/apps-script/`)

- **Rotate** `PROP_HMAC_SECRET` via `rotateSecret()` in the script editor at the moment the Worker cuts over (see §10). The old secret is already public.
- **Remove** `PROP_ADMIN_SECRET` references from `Setup.js` (the constant + `rotateAdminSecret` helper). The script property itself is cleaned via `PropertiesService.getScriptProperties().deleteProperty('ADMIN_SECRET')` from the editor on cutover day.
- **Delete** the `if (action === 'admin')` block in `doGet` (`Code.js:6-10`), plus the `Admin.html` template and `AdminGlue.js`.
- No changes to `verifyRequest`, `dispatch`, or any survey handler.

### 7.2 PWA (`deliverables/F2/PWA/app/`)

- **Delete** `VITE_F2_HMAC_SECRET` from `.env.example`, `.env.local`, `src/lib/env.ts`, `src/test-setup.ts`, all relevant tests.
- **Rename** `VITE_F2_BACKEND_URL` → `VITE_F2_PROXY_URL`. The new value is the public Worker origin, fine to ship in the bundle.
- **Delete** `src/lib/hmac.ts` and all `hmacSign` parameters from sync/config/facilities clients.
- **Add** `Authorization: Bearer <jwt>` header in `sync-client.ts`, `config-client.ts`, `facilities-client.ts`.
- **Dexie schema v2 → v3:** add a single `device_token: string` field on the enrollment row. Claims are parsed from the JWT at runtime, not cached. Migration is "force re-enrolment if `device_token` is missing or its parsed `exp` is in the past."
- **Enrollment screen:** add a tablet-token state ahead of the existing enumerator picker. Three input modes: paste, QR scan, manual entry. All strings use existing i18n keys so the upcoming Filipino translation drop-in covers them automatically.
- **CI build guard:** add a step that fails the build if `dist/assets/*.js` contains anything matching any of these patterns (each catches a different secret-shape category):
  - `[a-f0-9]{40,}` — long hex blobs (HMAC, hash digests)
  - `[A-Za-z0-9+/]{40,}={0,2}` — base64 / base64url blobs (signing keys, tokens)
  - Literal env names: `JWT_SIGNING_KEY`, `APPS_SCRIPT_HMAC`, `ADMIN_PASSWORD` (in case a future `VITE_*` var accidentally re-exports one)

### 7.3 Worker (new, e.g. `deliverables/F2/PWA/worker/`)

Estimated 200–400 LOC, single TypeScript file plus a small static admin HTML.

**Public endpoints (no admin auth):**

- `POST /exec` — JWT verify + KV revocation check + HMAC-sign-and-forward. Detects Apps Script quota errors and translates them to `E_BACKEND_BUSY` (see §6).
- `POST /verify-token` — used by PWA enrollment screen, returns claims for valid tokens. Public because verifying the token IS the auth.

**Admin endpoints (password-gated, behind a 1h HttpOnly session cookie):**

- `POST /admin/login` — verify ADMIN_PASSWORD (bcrypt + timingSafeEqual), set HttpOnly session cookie. Cloudflare Rate Limiting rule applied: max 10 attempts per IP per 5 minutes (configured via Cloudflare dashboard, not Worker code).
- `POST /admin/issue-token` — mint JWT, write audit, return token + QR
- `POST /admin/revoke` — write revocation entry to KV
- `GET /admin/list?facility=...` — list active tokens (from KV `token:` prefix scan)
- `GET /admin/` — static HTML for the ops UI (one page, vanilla JS)

## 8. Testing strategy

### 8.1 Unit (Worker)

- JWT mint + verify (HS256, valid + tampered + expired)
- HMAC sign matches Apps Script's expected canonicalisation byte-for-byte
- Revocation check: KV miss = pass, KV hit = reject
- Admin auth: correct password passes, wrong password fails, timing-safe compare in place
- Clock skew tolerance: Worker accepts JWTs with `iat` up to ±5 minutes off Worker time (field tablets often have wrong RTC after a battery-dead stretch)
- Token replay: same JWT presented twice within TTL is accepted by the Worker. Document this as a design property — replay protection is delegated to Apps Script's `client_submission_id` dedup, not the auth layer
- Apps Script quota detection: if Apps Script returns the quota-exhausted shape, Worker translates to `E_BACKEND_BUSY` instead of forwarding the raw 5xx

### 8.2 Unit (PWA)

- Token storage + load round-trip in Dexie
- `Authorization` header injection in each client (sync, config, facilities)
- Schema migration v2 → v3 forces re-enrolment when fields are missing
- Token expiry detected client-side before request fires (avoid wasted round-trip)

### 8.3 Integration

- Local: Wrangler dev + Apps Script clasp pushed to a test deployment + PWA dev server. End-to-end flow:
  1. Provision token via `/admin/issue-token`
  2. Enrol PWA with the token
  3. Submit a survey
  4. Verify row appears in test spreadsheet
  5. Revoke token via `/admin/revoke`
  6. Next submission returns `E_TOKEN_REVOKED`

### 8.4 Manual smoke

- Offline submit → reconnect → drains successfully
- Tablet token reaches expiry → enrolment flow re-triggers
- Two enumerators on one shared tablet (per Q3 decision) → `hcw_id` switching works without re-enrolment

### 8.5 Build guard CI

`.github/workflows/` step (post-build, pre-deploy):

```bash
BUNDLE="deliverables/F2/PWA/app/dist/assets"
FAIL=0

# Long hex blobs (HMAC, hash digests, hex-encoded keys)
if grep -lE "[a-f0-9]{40,}" "$BUNDLE"/*.js; then
  echo "FAIL: long hex literal found in client bundle (possible secret leak)" >&2
  FAIL=1
fi

# Base64 / base64url blobs (signing keys, opaque tokens)
if grep -lE "[A-Za-z0-9+/]{40,}={0,2}" "$BUNDLE"/*.js; then
  echo "FAIL: long base64 literal found in client bundle (possible secret leak)" >&2
  FAIL=1
fi

# Literal env names that should never appear in client output
for SECRET_NAME in JWT_SIGNING_KEY APPS_SCRIPT_HMAC ADMIN_PASSWORD; do
  if grep -l "$SECRET_NAME" "$BUNDLE"/*.js; then
    echo "FAIL: secret env name '$SECRET_NAME' referenced in client bundle" >&2
    FAIL=1
  fi
done

[ "$FAIL" = "0" ] || exit 1
```

## 9. Out of scope (deliberately)

- Per-enumerator credentials (resolved during brainstorming, Q2)
- MFA / step-up auth (no field workflow justification)
- Cross-facility tablet reuse (JWT is facility-scoped — one tablet, one facility for its lifetime)
- IP allowlisting on Apps Script (Apps Script doesn't expose request IP cleanly; the HMAC is the gate)
- Cloudflare Access SSO for the admin page (deferred — `ADMIN_PASSWORD` is sufficient for ASPSI ops headcount)
- Auto-renewal of JWTs (deferred — re-provisioning is the rotation event)

## 10. Migration & rollout

The exposed HMAC secret is in production today. Until cutover, mitigation is operational, not technical: do **not** load real DOH PII into the connected spreadsheet, and monitor `F2_Responses` for unexpected rows. The HMAC is rotated as the **last** step before flipping traffic to the Worker, not the first — rotating earlier would cause an outage with no Worker available to take over.

| Day | Action |
|---|---|
| 1–3 | Build Worker (proxy + admin UI) + tests on a dev Cloudflare account. PWA branch with `VITE_F2_PROXY_URL` + bearer-token clients. Apps Script + production unchanged so far. |
| 4 | Deploy Worker to staging. Update staging PWA build. In Apps Script staging deployment, rotate to a fresh HMAC; copy the new value into the Worker's `APPS_SCRIPT_HMAC` secret. Provision 1–2 test tablets. Full E2E on staging. |
| 5 | Verify on staging: provision → enrol → submit → response in sheet → revoke → 401. Build guard CI green. |
| 6 | Production cutover (single short window): rotate `PROP_HMAC_SECRET` on the production Apps Script deployment, set the same value as the production Worker's `APPS_SCRIPT_HMAC`, deploy production PWA pointing at the production Worker. Communicate the window to ops. Provision live tablets in batches per facility immediately after. Once cutover is verified working, delete the `?action=admin` HTML and clean `PROP_ADMIN_SECRET` from production Script Properties. Confirm Apps Script execution log shows only Worker traffic, no residual direct callers. |

## 11. Open questions

- **Worker custom domain or `*.workers.dev`?** Production-ready answer is a custom subdomain (e.g. `api.f2.aspsi.org`). Defer until rollout day 5.
- **Admin password rotation cadence?** Suggest quarterly by default; capture in operational runbook (separate from this spec).
- **KV vs. Durable Objects for revocation?** KV is sufficient (eventual consistency <60s is acceptable for revocation). Re-evaluate only if revocation latency becomes a problem.
- **`JWT_SIGNING_KEY` rotation runbook.** If the signing key needs to rotate (suspected leak, regulatory ask, calendar rotation), every issued JWT becomes invalid simultaneously and every active tablet has to be re-provisioned in the field that day. Two acceptable postures: (a) accept the burden and treat key rotation as a coordinated re-provisioning event with at least 1 week notice to ASPSI ops; (b) extend the Worker to verify against `JWT_SIGNING_KEY` AND `JWT_SIGNING_KEY_PREVIOUS` for a 30-day overlap window after rotation. Pick (a) for v1; revisit if a real rotation event happens.

## 12. References

- `.gstack/security-reports/2026-04-25T154000.json` — original audit
- `deliverables/F2/PWA/backend/apps-script/Code.js` — current `verifyRequest` and dispatch
- `deliverables/F2/PWA/app/src/lib/env.ts` — current `VITE_F2_HMAC_SECRET` consumer (to be deleted)
- `deliverables/F2/PWA/app/src/App.tsx:55,85,100` — current `getSyncEnv()` callers (to be updated)

## 13. ASPSI-specific considerations

Project-context items the generic design above does not by itself answer. These are not blockers for v1 implementation but must be resolved before the production cutover (day 6).

### 13.1 Philippines Data Privacy Act (DPA / NPC) posture

F2 collects healthcare-worker PII for DOH. The DPA imposes obligations around lawful processing, retention, breach notification, and data subject rights. The HMAC leak fixed by this spec is, on a strict reading, a security breach involving PII (any real responses submitted under v1.1.1 / v1.2.0 with the leaked secret in the bundle).

Concrete items to confirm before cutover:

- **Data retention policy for `F2_Responses` and `F2_Audit` sheets** — how long are responses kept, how are they archived or deleted at project end? Spec is silent; today's behaviour is "retain forever in the connected spreadsheet".
- **Audit log of admin actions** — the Worker writes `token:<jti>` audit entries to KV at issuance and a `revoked:<jti>` entry on revocation, but there is no central log that ops or DOH can query (e.g., "who revoked tablet X on date Y, why?"). At minimum, the admin UI should display the issuance / revocation history per facility. Stretch: pipe these events to an append-only Google Sheet in the same spreadsheet workbook (`F2_AdminAudit` tab) so DOH has a paper trail without needing Cloudflare access.
- **Breach notification path** — if a tablet is lost / a token compromised, what is the notification chain (enumerator → ASPSI ops → DOH → NPC)? Should be a one-pager runbook separate from this spec but referenced from §11.
- **Existing v1.1.1 exposure** — was real PII ever loaded under the leaky build? If yes, ASPSI may have a DPA disclosure obligation. Carl to confirm with ASPSI legal.

### 13.2 F3 / F4 reuse posture

F3 (FMF) and F4 generators are in flight as separate ASPSI deliverables. This spec designs a **single-instrument Worker** for F2 only. If F3 / F4 eventually move to the same PWA-over-Worker pattern, two acceptable postures:

- **(a) Per-instrument Worker.** Stand up a separate Worker for each instrument (`f2-proxy.workers.dev`, `f3-proxy.workers.dev`). Each holds its own `APPS_SCRIPT_HMAC` and `JWT_SIGNING_KEY`. Operationally simpler; secrets fully isolated; one Worker outage doesn't cross-contaminate.
- **(b) Multi-tenant Worker.** Add an `instrument_id` claim to the JWT, route `/exec` to per-instrument Apps Script backends within one Worker. Less code duplication; but a bug or secret leak in the shared Worker affects all instruments simultaneously.

**Recommendation: (a) for now.** F2 ships first as a standalone Worker. Revisit when F3 / F4 are ready to move off CSWeb.

### 13.3 CSWeb coexistence

ASPSI runs traditional CSWeb-based collection alongside the F2 PWA. This auth re-architecture **only gates the F2 PWA path**. The CSWeb collection still writes to Google Sheets through whatever its existing mechanism is, bypassing the Worker.

If CSWeb and F2 PWA both write to the same `F2_Responses` sheet, the spreadsheet itself is the integration point. Anyone who can write through CSWeb can still write rows there. This is acceptable as long as CSWeb access is itself controlled (Google account + sheet permissions). No design change needed, but worth a one-line note in any future CSWeb security review.

### 13.4 Cloudflare account ownership

The Worker secrets (`JWT_SIGNING_KEY`, `APPS_SCRIPT_HMAC`, `ADMIN_PASSWORD`) live in some Cloudflare account. Whose?

- **Personal (Carl's account):** simplest for v1; problematic at engagement end — handover requires migrating the Worker, secrets, and KV namespace to ASPSI's or DOH's account.
- **Analytiflow corporate account:** cleaner separation; same handover problem at a different boundary.
- **ASPSI-owned Cloudflare account:** correct end state for handover. Requires ASPSI to set up the account and grant Carl admin access.

**Recommendation:** create the Worker in an ASPSI-owned Cloudflare account from day 1. If that's not feasible before the v1 deadline, ship in Carl's account but commit to a migration plan before the engagement closes.

### 13.5 Translation drop-in

The PWA already has an i18n switcher (per `LanguageSwitcher.tsx`); Filipino strings are not yet delivered by ASPSI. The new enrollment screen ("Paste device token", "Scan QR", error messages) MUST use existing i18n keys (`t('chrome.enrollment.tokenPaste')`, etc.), not hardcoded English. When ASPSI delivers the Filipino bundle, the new strings translate without touching this file.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | SKIPPED (codex CLI not installed) | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR (PLAN) | 11 issues raised, 9 applied to spec, 2 deferred (1C-B, KV-race test, 4A) |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **UNRESOLVED:** 0
- **VERDICT:** ENG CLEARED — ready to implement once §13 ASPSI-specific items (DPA posture, Cloudflare account ownership) are resolved before day-6 cutover. Re-running `/gstack-codex challenge` after `npm install -g @openai/codex` is a recommended additional pass before implementation, especially for §13.1 (DPA) and the Apps Script quota retry logic.
