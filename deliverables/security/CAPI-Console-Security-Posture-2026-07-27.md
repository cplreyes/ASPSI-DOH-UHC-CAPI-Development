# CAPI Console — Security Posture Report

**Date:** 2026-07-27 · **Scope:** capi.asiansocial.org (public portal), csweb.asiansocial.org
(reporting layer, auth gates, Activity Manager), on-box cron generators, secrets in `/opt`
· **Method:** attack-surface census → secrets/config/injection scanning → active verification
(code tracing + authenticated probes; no live exploitation) · **Mode:** daily (8/10 confidence gate)

> Not a substitute for a professional penetration test. This is an AI-assisted first pass
> that catches common patterns. For a survey holding health PII at national scale, a
> qualified firm should review before main fieldwork.

---

## Attack surface

| Surface | Count / state |
|---|---|
| Public pages (portal) | 26 static HTML + 2 aggregate JSON feeds |
| Gated reporting surfaces | dashboard, map, sync-feed, data room (24 export files) |
| Write endpoints | **1** — Activity Manager (`/docs/admin/index.php`) |
| Cron generators | 6 (dashboard, map, sync-feed, responses, spss, tabulations, ov-status) |
| Credential systems | 4 (docs htpasswd, CSWeb app roles, F2 admin, phpMyAdmin) |
| Secret stores | `/opt/app/.env`, `/opt/csweb-alerts.conf`, `.htpasswd-docs`, `~/.ssh` keys |

---

## Verified GOOD (tested, not assumed)

| Control | Evidence |
|---|---|
| RBAC tiers hold | 9 probes with throwaway per-tier accounts: field blocked from data room + admin, staff blocked from admin, anon blocked everywhere |
| Public feeds leak nothing | `status.json` / `tabulations.json` scanned: no logins, facilities, names, coordinates or case keys |
| No SQL injection surface | All generator SQL is internal constants + schema identifiers; no request/user input reaches a query |
| XSS in the write endpoint | Every user-controlled value passes `htmlspecialchars`; unescaped echoes are hardcoded constants only |
| CSRF on the write endpoint | Per-session token compared with `hash_equals`; attacker cannot read it cross-origin |
| Backups not servable | `/docs/admin/backups/` → 403 |
| TLS | Valid cert, `http` → `https` 301 on both hosts |
| No secrets in logs | 4,492 keyword hits reviewed — all benign ("no webhook configured", MySQL's own warning). False positive, discarded |

---

## Findings

### F1 — DB root password passed on the command line (MEDIUM, 10/10, VERIFIED)
`csweb-responses-gen.py:81` (and peers) invoke `mysql -uroot -p<PASSWORD>`. MySQL itself
warns about this in `/var/log/csweb-responses.log`.
**Exploit:** any local user running `ps aux` during the query window reads the DB root
password, then connects directly to the database with full privileges.
**Why MEDIUM not HIGH:** the box currently has no non-root local users.
**Fix:** pass via `MYSQL_PWD` env var on the subprocess, or a `--defaults-extra-file`
with `[client] password=` at mode 600. One-line change per generator; do it in one pass.

### F2 — PHP `display_errors=1` / `expose_php=1` container-wide (MEDIUM, 9/10, VERIFIED)
The lamp container ships both on.
**Exploit:** any PHP notice renders absolute paths and stack traces into the response;
`X-Powered-By` advertises the exact PHP build for version-specific attacks.
**Mitigated for our endpoint:** the Activity Manager now sets `display_errors=0` per-request.
**Remaining:** CSWeb's own PHP still runs with them on — a php.ini change touching the live
app during pretest, so it is deliberately **not** applied. Fold into the rollout cutover.

### F3 — Session cookie flags absent container-wide (MEDIUM, 9/10, VERIFIED → FIXED for our endpoint)
`session.cookie_httponly=0`, `cookie_secure=0`, `samesite=''`.
**Exploit:** an XSS anywhere in the `/docs` origin could read the admin session cookie
(`httponly=0`) and drive activity edits; without `secure`, the cookie may traverse plaintext.
**Fixed:** Activity Manager now issues its cookie with `httponly`, `secure`, `SameSite=Strict`
and a `/docs/admin/` path scope. CSWeb's own sessions still use the container defaults.

### F4 — Secrets world-readable on disk (MEDIUM, 10/10, VERIFIED → FIXED)
`/opt/app/.env` was `644` (contains `SOFTWARE_PASSWORD`, DB credentials);
`.htpasswd-docs` was `644` (bcrypt hashes → offline cracking).
**Fixed:** `.env` → `640 root:root`; `.htpasswd-docs` → `640 root:www-data` (Apache's child
user must still read it — verified with an authenticated 200 probe after the change).

### F5 — No security headers (MEDIUM, 10/10, VERIFIED → PARTIALLY FIXED)
Neither host sent HSTS, X-Content-Type-Options, X-Frame-Options or Referrer-Policy.
**Exploit:** clickjacking of the gated dashboard in an iframe; MIME sniffing; referrer
leakage of gated URLs to third parties.
**Fixed on csweb `/docs`:** all four now set (verified on both 401 and authenticated 200).
**Remaining:** capi portal is served by openresty (different config path, not Apache
`.htaccess`) — needs an nginx-side change. **CSP deliberately omitted** on both: the
dashboard, map and portal all carry inline scripts; a CSP without `unsafe-inline` breaks
them, and with `unsafe-inline` it buys little. Do it properly with nonces later.

### F6 — Unbounded generator logs (LOW, 10/10, VERIFIED → FIXED)
Only `csweb-process-cases` had rotation; `csweb-spss.log` had reached 4.2 MB and all
generators append every 1–2 minutes forever.
**Fixed:** `/etc/logrotate.d/csweb-generators` — weekly, 8 rotations, compressed,
`copytruncate` (safe for processes holding the handle).

---

## Not fixed on purpose (needs your call)

1. **F1 MySQL password handling** — touches all six live generators mid-pretest. Safe, but
   deserves its own verified pass rather than being bundled into an audit.
2. **F2/F3 container-wide php.ini** — changing PHP settings under the running CSWeb app
   during pretest risks the field sync path. Rollout-cutover item.
3. **CSP** — needs inline scripts refactored to nonces or external files first.
4. **capi portal headers** — openresty config, not `.htaccess`; needs the Elestio nginx layer.
5. **F2 admin API auth** — its `/admin` route serves only the SPA shell (normal); its data
   API auth was **not** verified from outside. Separate system, worth its own review.

---

## Standing patterns to keep

- Least privilege on every new gate (three tiers now: field / staff / admin).
- Aggregates-only on any public feed; a key-name tripwire in the generator refuses to
  publish `name`/`user`/`facility`/`code9`/`key` — it has already fired once in anger.
- Every write endpoint: CSRF token, strict allowlist validation, timestamped backup,
  atomic write, HTTP-denied backup directory.
- Verify auth changes with a real credential — a 401 for anonymous proves nothing about
  whether valid users can still get in.
