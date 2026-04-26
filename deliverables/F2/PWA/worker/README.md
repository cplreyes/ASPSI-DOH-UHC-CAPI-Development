# f2-pwa-worker

Cloudflare Worker auth proxy in front of the F2 PWA Apps Script backend.
Replaces the broken `VITE_F2_HMAC_SECRET`-in-bundle model with a JWT-per-tablet
scheme where the HMAC stays server-side forever.

**Design spec:** `../../../docs/superpowers/specs/2026-04-26-f2-pwa-auth-rearch-design.md`

## Routes

| Method | Path                  | Auth                  | Purpose |
|--------|-----------------------|-----------------------|---------|
| POST   | `/exec`               | Bearer JWT            | Forward tablet traffic to Apps Script with HMAC |
| GET    | `/exec`               | Bearer JWT            | Same, for read-only handlers (handleAudit, etc.) |
| POST   | `/verify-token`       | Public                | PWA enrollment validates a pasted token, gets claims |
| POST   | `/admin/login`        | ADMIN_PASSWORD        | Establish 1h HttpOnly session cookie |
| POST   | `/admin/issue-token`  | session cookie        | Mint a new device JWT (default 30-day TTL) |
| POST   | `/admin/revoke`       | session cookie        | Revoke a JWT by `jti`, propagates via KV in <60s |
| GET    | `/admin/list`         | session cookie        | List active tokens, filterable by `?facility=` |
| GET    | `/admin/`             | none (gates inside)   | Admin UI (single-page vanilla HTML) |

## First-time setup

```bash
cd deliverables/F2/PWA/worker
npm install

# Create the KV namespace and paste the returned id into wrangler.toml.
npx wrangler kv:namespace create F2_AUTH
npx wrangler kv:namespace create F2_AUTH --preview

# Generate the four secrets.

# 1. JWT signing key (32 bytes, base64url).
openssl rand -base64 32 | tr -d '=' | tr '+/' '-_' | npx wrangler secret put JWT_SIGNING_KEY

# 2. Apps Script HMAC. Use the value from PROP_HMAC_SECRET *after* you rotate it
# on the Apps Script side at cutover (see spec §10).
echo -n "<paste 64-char hex from rotated PROP_HMAC_SECRET>" | npx wrangler secret put APPS_SCRIPT_HMAC

# 3. Apps Script /exec URL (production deployment).
echo -n "https://script.google.com/macros/s/<id>/exec" | npx wrangler secret put APPS_SCRIPT_URL

# 4. Admin password hash. Run the helper, paste the output.
node scripts/hash-admin-password.mjs
# Then:
npx wrangler secret put ADMIN_PASSWORD_HASH
```

## Running locally

```bash
npm run dev
# → opens on http://localhost:8787

# In another terminal, hit the admin UI:
open http://localhost:8787/admin/
```

For local dev, secrets come from `.dev.vars` (gitignored). Create one:

```
JWT_SIGNING_KEY=<base64url-32-bytes>
APPS_SCRIPT_HMAC=<staging-hmac-secret>
APPS_SCRIPT_URL=https://script.google.com/macros/s/<staging-id>/exec
ADMIN_PASSWORD_HASH=<output-of-hash-admin-password.mjs>
```

## Tests

```bash
npm run typecheck
npm test
```

The unit tests cover JWT mint/verify, clock skew, and replay properties (spec §8.1).
Integration tests against a real Apps Script deployment + Wrangler dev are run
manually per spec §8.3.

## Deploy

```bash
npm run deploy
# → Worker is at https://f2-pwa-worker.<account>.workers.dev/
```

Custom domain (e.g. `api.f2.aspsi.org`) is configured via the Cloudflare dashboard
once the spec §11 ownership decision is made.

## Operational notes

- **Apps Script quota detection (spec §6 Failure-1):** the Worker scans Apps
  Script responses for known quota strings ("Service invoked too many times",
  "Quota exceeded") and translates to `503 E_BACKEND_BUSY` so the PWA can
  back off rather than retry-storm.
- **Rate limiting `/admin/login`:** configured in the Cloudflare dashboard, not
  in Worker code. Add a Rate Limiting rule: 10 requests per IP per 5 minutes
  on the `/admin/login` path.
- **Token revocation:** ops clicks Revoke in the admin UI. KV propagates
  globally in under 60 seconds. The revoked tablet's next request returns
  `401 E_TOKEN_REVOKED`.
- **Token rotation:** there is no automatic refresh. Ops re-issues tokens
  every 30 days (default TTL). See spec §5.

## Files

```
src/
  index.ts          - router
  types.ts          - Env, JwtClaims, error helpers
  jwt.ts            - HS256 mint + verify (Web Crypto, zero deps)
  hmac.ts           - HMAC sign for Apps Script forwarding
  admin.ts          - admin auth (PBKDF2) + admin endpoint handlers
  admin-html.ts     - admin UI as a static HTML+JS string (XSS-safe via textContent)
  exec.ts           - /exec proxy + Apps Script quota detection
  verify.ts         - /verify-token (public)
test/
  jwt.test.ts       - JWT unit tests
scripts/
  hash-admin-password.mjs  - ops helper for ADMIN_PASSWORD_HASH
```
