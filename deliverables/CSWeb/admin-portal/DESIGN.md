---
module: CAPI Console Admin Portal
created: 2026-08-08
companions: PRD.md · BACKLOG.md · ../auth/DEPLOY.md · ../capi-console-idp-option-c-plan.md
---

# Technical Design — CAPI Console Admin Portal

Backend · Frontend · Integration · Security · QA. Every runtime fact below was verified on the box on 2026-08-08.

## 0. Verified environment

| | |
|---|---|
| Front door | Elestio **openresty**, `/opt/elestio/nginx/conf.d/capi.asiansocial.org.conf` (hand edits persist) |
| App | `webserver` = `lamp-php8`, Apache 2.4.67 + **mod_php 8.1.34**, `pdo_mysql`, `PASSWORD_ARGON2ID` |
| DB | `database` = `lamp-mysql8`; schema `capi_auth`, user `capi_auth` (DML only, no DDL) |
| Static portal | `capi-www` = `nginx:alpine` on `127.0.0.1:8788` — **no PHP** |
| Bind | Apache published on **`172.17.0.1:8080`** (docker bridge only; refused from off-box — verified) |
| **APCu** | **not installed** — no PHP-level shared cache exists |
| **xdebug** | **loaded, `xdebug.mode=develop`, in production** → E9-ADMIN-031 |
| `log_errors` | **Off** — a PHP fatal is a blank 500 with no log line |

Consequences that shape everything: endpoints must live under `/docs/` (the only path proxied to Apache); `/docs/auth/` is claimed by mod_auth_form so the module lives at **`/docs/idp/`**; caching must live in nginx, not PHP.

## 1. Module layout

```
/var/www/private/capi-auth/          # outside docroot, www-data:www-data 0750
  lib.php acl.php                    # existing (deployed)
  admin_bootstrap.php                # envelope, CSRF, require_perm(), tx(), request_id, catch-all
  admin_users.php admin_roles.php admin_sessions.php admin_audit.php
  migrations/002-admin-portal.sql    # run as root — capi_auth has no DDL
/var/www/html/docs/idp/              # docroot; routers only, zero logic
  authz.php login.php logout.php me.php   # existing (deployed)
  admin.php                          # single front controller
  .htaccess                          # pretty URLs + deny lib/*.sql
```

One front controller, not a file per route — so there is exactly one place enforcing permission and CSRF.

## 2. API surface

Envelope on every response: `{"ok":true,"data":{…},"request_id":"<32 hex>"}` or `{"ok":false,"error":{"code","message","field"},"request_id":…}`. `ok` matches the existing `api.php` shape so the frontend fetch wrapper survives. HTTP status carries the class. All mutations require the `capi_csrf` double-submit **and** re-check permission in-process — the nginx gate is not live until cutover, and defence in depth after. Paths relative to `/docs/idp`.

| METHOD + path | Perm | Notes | Audit verb |
|---|---|---|---|
| `GET /admin/users` | admin.users | filters q/status/role; returns `live_sessions`, `row_version` | — |
| `POST /admin/users` | admin.users | returns `temp_password` | `user.create` |
| `PATCH /admin/users/{id}` | admin.users | `row_version` required (409 on conflict) | `user.update` / `user.disable` |
| `PUT /admin/users/{id}/roles` | admin.users | **full set**, not a delta → replay-safe | `user.roles` |
| `POST /admin/users/{id}/password` | admin.users | server-generated; sets `must_change` | `user.password.reset` |
| `POST /admin/users/{id}/logout` | admin.users | | `user.forcelogout` |
| `DELETE /admin/users/{id}` | admin.users | soft — sets disabled; hard delete would orphan audit | `user.disable` |
| `GET /admin/roles` · `PUT /admin/roles/{name}/perms` | admin.users / admin.system | perms edit bumps `version` | `role.perms` |
| `GET /admin/sessions` · `DELETE /admin/sessions/{sid}` | admin.users | `sid` = stored `sid_hash`, never the token | `session.kill` |
| `GET /admin/audit` · `GET /admin/audit.csv` | audit.view | cursor-paged | `audit.export` |
| `GET /me` · `POST /me/password` · `GET/DELETE /me/sessions[/{sid}]` | AUTH / PWCHANGE | self only | `me.*` |

## 3. Schema deltas — `002-admin-portal.sql` (root runs it)

`console_users` += `row_version`, `pw_changed_at`, `updated_at/by`, `disabled_at`.
`console_audit` += `request_id`, `ix_aud_target(target,ts)`, `ix_aud_req`.
New `console_idem(idem_key PK, actor, endpoint, status, body_sha256, response, created_at)`.

**Ship in Phase 1, not Phase 2:** `pw_algo` ENUM gains `'pbkdf2'`, and `console_svc_tokens` is created empty. Otherwise F2 federation requires an ALTER on live identity data mid-rollout.

No password-reset-token table: there is no mailer on the box, so reset = admin-set temporary password + `must_change=1`.

## 4. Integrity rules

- **Transactional, each as one unit:** create (user + roles + audit); role-set replace (`SELECT … FOR UPDATE`, DELETE+INSERT, **plus** `auth_session_revoke_user`); perm-set edit (DELETE+INSERT **and** `version = version + 1` — split them and sessions run on stale grants); disable (status + revoke).
- **Idempotency:** `PUT /roles` is a full set. `DELETE` returns `revoked:0` on replay. Create / password-reset / force-logout accept `Idempotency-Key` — without it a double-clicked reset mints a second temp password and silently invalidates the one the admin already copied.
- **Lockout insurance:** at least one active `owner`, checked `FOR UPDATE` before commit on every disable / delete / role change → 409 `last_owner`. No self-disable, no self-demotion. Break-glass sits below all of it.
- **`role_version` gap (important):** the version *sum* detects permission edits, **not** role reassignment — swapping role A (v3) for role B (v3) leaves the sum unchanged. Not an escalation (grants are re-read per request), but reassignment must call `auth_session_revoke_user` explicitly. Do not rely on version arithmetic there.

## 5. The authz hot path

Runs on **every** request, including static assets. Today: 4 queries + 1 write each → a dashboard load with ~25 assets is ~100 queries and ~25 writes. Target: **1 SELECT, 0 writes**; **0 queries** for PUBLIC (already true, and it is what keeps the login page alive during an outage).

1. **Cache the subrequest in nginx** — `proxy_cache` on `location = /_capi_auth`, key `"$cookie_capi_sid|$request_uri"`, `proxy_cache_valid 204 401 403 10s`, bypass when the cookie is empty. APCu is absent, so PHP cannot do this. 10 s becomes the stated revocation SLA.
2. Fold the three SELECTs into one join (`GROUP_CONCAT(DISTINCT …)` + a correlated subquery for the version sum — a plain `SUM` over that join double-counts).
3. Conditional touch: `UPDATE … WHERE sid_hash=? AND last_seen_at < NOW() - INTERVAL 60 SECOND`.

**MySQL down:** `authz.php` returns 503; nginx converts any non-2xx/401/403 subrequest status into a **500**, so `error_page 500 = @capi_authdown` is what fires. PUBLIC routes still serve. No fail-open path, ever.

## 6. Frontend

**Decision: extend the existing vanilla-JS admin app.** No build toolchain exists on the box; Preact-via-htm forks the idiom for six screens, and React/Vite requires committing `dist/` assets against a copy-to-box deploy flow. Split `ui.js` (el / tbl / dialog / api) + one file per view, loaded as ordered classic scripts.

Nav renders from `/docs/idp/me`; hiding a link is **cosmetic only** — the edge enforces, and every 403 renders a real "Not permitted" screen rather than a blank.

Screens: Users list · User detail · Role editor · Active sessions · Audit trail · My account. Each specifies empty / loading / error / no-permission states.

**Damage-prevention rules:** no `window.confirm()` for security writes; typed confirmation (the operator types the username) for disable, delete, removal of `admin.users`, and revoke-all; **blast radius fetched from a preflight read** — "this signs out **2 active sessions**" — with the button disabled until it resolves and never rendering `0` as a placeholder; no optimistic UI (row goes `aria-busy`, list re-fetched from the server before appearance changes); self-lockout guards rendered client-side and enforced server-side.

**Accessibility (measured):** `--ink-3` `#74838c` on white is **3.91:1** — fails AA, and is used for `.muted`, "last sync" and inactive tabs. Add `--ink-3-text: #5c6a73` (5.58:1) for text carrying meaning. Buttons have no focus ring — add `:focus-visible`. Native `<dialog>` + `showModal()` for focus trapping. Below 640px, `.tbl.stack` with `td::before{content:attr(data-label)}`.

## 7. Integration and cutover

Ordered C0–C7 in `../auth/DEPLOY.md §6`. The load-bearing points:

- **C0 break-glass first**, tested from Carl's IP and refused from elsewhere. Never removed.
- **`location /csweb/` is never touched.** CSEntry cannot do cookie sign-in. It is also regression check #3, run before *and* after.
- **mod_auth_form retirement order matters:** delete the two `<Location /docs/auth/…>` handler blocks and the `<Location /docs>` Session block in one edit, and in the same edit add `RedirectMatch 302 ^/docs/auth/logout/?$ /docs/idp/logout`. `/docs/auth/logout` is already PUBLIC in the ACL, so the topbar link baked into every generated page keeps working with **zero regeneration**. Replace `/docs/login.php` with a 302 rather than deleting it — its form POSTs to `/docs/auth/login`, and a 302 turns that POST into a GET that silently drops credentials.
- **Header hygiene:** `auth_request_set` both `X-Auth-User` and `X-Auth-Roles`, and blank every client-supplied `X-Auth-*` / `X-Original-*`.

**Generators are unaffected** — all nine write to disk as root via cron, none publishes over HTTP. Two named risks, both now handled: the tabulations preview JSON (fixed in `acl.php`) and the `whoami.php` / `d.tier` dependency in `portal_shell.py:140` (×2) and `csweb-responses-gen.py:427`, whose empty `.catch()` makes breakage silent. Standing tax: **deny-by-default means any new generated file 403s until listed in `acl.php`** — add that to each generator's header comment.

**Phase 2 (F2 federation) readiness:** `/docs/idp/svc/f2/*` gets its own nginx location with **no** `auth_request`, bearer auth + origin-cert/IP allowlist, its own rate limit, audit namespaced `svc:f2`, and `['/docs/idp/svc/', 'DENY']` in `ACL_PREFIX` so no cookie session can ever reach it. Dual-read behind a Worker env flag (`sheets | dual | box`), comparing a canonical tuple and only a SHA-256 **prefix** of `pw_hash`. Flip after 7 zero-diff days including at least one propagated role change.

## 8. Security

Full findings, threat model and SEC-01…SEC-18 acceptance criteria are in the review record. Fixed on 2026-08-08:

| Finding | Status |
|---|---|
| Password change required no current password → stolen cookie = permanent takeover + victim lockout | **fixed** (`login.php`, + form field, + `password.change.fail` audit) |
| Tabulations preview JSON gated as `data.export` inside a `tabulations.view` page | **fixed** (`acl.php`, +6 tests) |
| `role_version` comment overstated coverage | **fixed** (comment + backlog rule) |
| Apache `:8080` reachable off-box | **not a gap** — binds `172.17.0.1` only, verified refused externally. Retained as gate SEC-01. |

Open and scheduled: `X-Auth-Roles` spoofing (E9-ADMIN-009) · unknown-username throttle + timing floor (011) · audit `DELETE` grant (012) · `Cache-Control` on `/docs/` and `__Host-` cookies (045) · MFA (042).

**MFA outline:** RFC 6238 SHA-1/6/30 ±1 step with `last_totp_step` to stop in-window replay; secret stored as AES-256-GCM ciphertext under a compose-env key because the DB has no encryption at rest; locally generated QR, never an external chart service; ten argon2id-hashed single-use recovery codes; mandatory for `owner`, `programme_admin` and any `data.export` holder. **Provision a second owner with its own device before enabling enforcement** — root SSH cannot be the standing recovery path.

## 9. Test strategy

| Level | Contents | Runner |
|---|---|---|
| L1 pure unit | `test_acl.php` (**146 assertions, green**) + new `test_lib.php` | `docker exec lamp-php8 php /var/www/private/capi-auth/test_acl.php` |
| L2 DB unit | sessions, throttle, lazy rehash, audit — disposable rows | `… php test_db.php` |
| L3 HTTP contract | authz.php alone: 204/401/403/503 + `X-Auth-Reason` | `test_authz.sh` |
| L4 E2E | **15 checks, green** — login → RBAC → logout replay → audit | `smoke.sh https://capi.asiansocial.org` — **HTTPS only**; cookies are `Secure` and plain HTTP drops them silently |
| L5 cutover | 14-check before/after regression | `cutover-check.sh` |

**Highest-value untested unit: `auth_apr1_crypt`.** A wrong digest locks out all 15 legacy accounts and nothing else exercises it — assert byte-equality against `htpasswd -nbm`.

**Test data:** every probe row carries the literal prefix `zzt_`; no real account starts with it and `LIKE 'zzt\_%'` is an exact predicate. Cleanup registered as a bash `trap … EXIT INT TERM` **before the first insert**, so an aborted run still cleans up; `--verify-clean` re-counts and exits non-zero if anything survived.

**Deliberately not tested:** CI, headless-browser suite, PHPUnit, coverage, load/concurrency, cross-browser. At ~20 users on one box in a time-boxed engagement, those cost more than the risk they retire. The failures that actually threaten this system are *wrong access decisions* and *revocation that doesn't revoke* — both cheap to catch at L1/L2.
