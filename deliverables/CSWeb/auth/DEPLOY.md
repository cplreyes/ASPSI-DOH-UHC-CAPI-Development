# CAPI Console identity provider — deployment runbook (Phase 1)

Companion to `../capi-console-idp-option-c-plan.md`. Every command is written
out; nothing here is "and then configure it appropriately".

**Box:** `ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115` · compose dir `/opt/app`
**Containers:** `webserver` = `lamp-php8` (PHP 8.1.34, Apache) · `database` = `lamp-mysql8` · `capi-www` = static nginx on `127.0.0.1:8788`
**Front door:** Elestio openresty, `/opt/elestio/nginx/conf.d/capi.asiansocial.org.conf`

Steps 1–5 are **additive**: nothing user-visible changes and the current gate
keeps working. Step 6 is the cutover. Do 6–7 in a quiet window.

> **STATUS: steps 1–5 executed 2026-08-08.** 18 accounts imported, smoke test
> 15/15, live gate untouched (`/csweb/` 200, `/docs/dashboard.html` 401,
> `/` 302 — all unchanged). Steps 6–7 not started.
>
> **The provider is built and tested but ENFORCES NOTHING yet.** Until step 6,
> the console's actual security posture is unchanged from before this work:
> stateless cookies with no revocation, `$apr1$` hashes in play, filename-based
> ACL, no read audit.

> ⚠️ **Two numbering schemes — do not confuse them.** This runbook's steps 1–9
> are *deployment* steps. The plan's §3.8 steps 1–9 are *capability* steps.
> They do not correspond. Mapping of what is actually done:
>
> | Plan §3.8 capability | State |
> |---|---|
> | 1 schema + roles · 2 import · 3 `/authz` + login/logout/me | **done** |
> | 4 admin screens for sessions + audit | **not started** |
> | 5 repoint `auth_request` · 6 delete `FilesMatch` | **not started** (cutover) |
> | 7 `/me`-driven nav, retire second nav codepath | **not started** |
> | 8 MFA (TOTP) | **not started** |
> | 9 read auditing — writer built in `authz.php`; admin view | **partial** |

### Three things that bit during the real run — read before repeating this

1. **Endpoints live at `/docs/idp/`, NOT `/docs/auth/`.** `00-uhc-auth.conf`
   declares `<Location /docs/auth/login> SetHandler form-login-handler` for
   mod_auth_form. Anything placed under `/docs/auth/` is intercepted by Apache
   and never executes, returning a bare **500**. The `/docs/.htaccess` header
   comment says so; it was there to be read.
2. **`log_errors` is Off in this image**, so PHP fatals produce a 500 with an
   empty body and *no log line*. To debug, add `php_flag log_errors on` +
   `php_value error_log …` to the directory's `.htaccess` temporarily. Remove it
   afterwards.
3. **`chown` the private directory itself, not just its contents.** Leaving
   `/opt/app/lamp/private` as `root:root 750` means www-data cannot traverse it,
   `is_dir()` returns false under mod_php (but true under CLI, as root), and the
   library resolver silently falls back to the docroot. Symptom: works in CLI,
   500s over HTTP.

Also note `docker compose up -d webserver` **also recreates `database`**, because
the webserver `links:` it. Both restart; budget for MySQL's startup, not just
Apache's.

---

## 0. Pre-flight (already verified 2026-08-08 — re-check if time has passed)

```bash
docker compose exec -T webserver php -r 'echo PHP_VERSION,"\n";
  echo defined("PASSWORD_ARGON2ID")?"argon2id ok\n":"NO ARGON2ID\n";'
docker compose exec -T webserver php -m | grep -E '^(pdo_mysql|mysqli)$'
```

Expected: `8.1.34`, `argon2id ok`, both extensions listed.

## 1. Private directory + credentials

Library code and the schema must not sit in the docroot. Add a second bind
mount and the DB credentials to the `webserver` service in
`/opt/app/docker-compose.yml` (host-mounted, so it survives recreation):

```yaml
  webserver:
    volumes:
      - ./lamp/www:/var/www/html
      - ./lamp/private:/var/www/private      # <-- add
    environment:                              # <-- add
      CAPI_AUTH_DB_HOST: database
      CAPI_AUTH_DB_NAME: capi_auth
      CAPI_AUTH_DB_USER: capi_auth
      CAPI_AUTH_DB_PASS: "<generate: openssl rand -base64 30>"
```

```bash
mkdir -p /opt/app/lamp/private/capi-auth
# The PARENT must be owned by www-data too, or mod_php cannot traverse into it:
# is_dir() then returns false under Apache while still returning true under CLI
# (which runs as root), and the library resolver silently falls back to the
# docroot. Symptom: works in CLI, 500s over HTTP with no log line.
chown -R www-data:www-data /opt/app/lamp/private
chmod 750 /opt/app/lamp/private
```

## 2. Database, least-privilege user, schema

The provider does **not** connect as root. Its user holds grants on `capi_auth`
and nothing else, so a flaw here cannot reach CSWeb's tables or `csweb_f2`.

```bash
cd /opt/app
ROOT_PW=$(grep '^MYSQL_ROOT_PASSWORD' .env | cut -d= -f2-)
AUTH_PW='<the same value used in docker-compose.yml>'

docker compose exec -T database mysql -uroot -p"$ROOT_PW" \
  --default-character-set=utf8mb4 < /opt/app/lamp/private/capi-auth/schema.sql

docker compose exec -T database mysql -uroot -p"$ROOT_PW" --default-character-set=utf8mb4 -e "
  CREATE USER IF NOT EXISTS 'capi_auth'@'%' IDENTIFIED BY '$AUTH_PW';
  GRANT SELECT, INSERT, UPDATE, DELETE ON capi_auth.* TO 'capi_auth'@'%';
  FLUSH PRIVILEGES;"
```

`--default-character-set=utf8mb4` is not optional: without it the client
negotiates latin1 and the first `ñ` in any value breaks the strict UTF-8 decode.

Verify: `SHOW TABLES FROM capi_auth;` → 6 tables. `SELECT name, version FROM capi_auth.console_roles;` → 5 roles.

## 3. Deploy the files

```bash
# library + schema + migrations -> OUTSIDE the docroot
ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115 'mkdir -p /opt/app/lamp/private/capi-auth/migrations'
scp -i ~/.ssh/aspsi-csweb \
    auth/{lib.php,acl.php,schema.sql,import_htpasswd.php,test_acl.php,test_admin.php} \
    auth/{admin_bootstrap.php,admin_users.php,admin_roles.php,admin_sessions.php,admin_audit.php} \
    root@207.148.65.115:/opt/app/lamp/private/capi-auth/
scp -i ~/.ssh/aspsi-csweb auth/migrations/002-admin-portal.sql \
    root@207.148.65.115:/opt/app/lamp/private/capi-auth/migrations/

# endpoints -> inside the docroot, under /docs/idp/
ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115 'mkdir -p /opt/app/lamp/www/docs/idp'
scp -i ~/.ssh/aspsi-csweb auth/{authz.php,login.php,logout.php,me.php,admin.php} \
    root@207.148.65.115:/opt/app/lamp/www/docs/idp/
scp -i ~/.ssh/aspsi-csweb auth/htaccess-idp \
    root@207.148.65.115:/opt/app/lamp/www/docs/idp/.htaccess

ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115 \
  'chown -R www-data:www-data /opt/app/lamp/private /opt/app/lamp/www/docs/idp
   chmod 640 /opt/app/lamp/private/capi-auth/*
   chmod 750 /opt/app/lamp/private/capi-auth/migrations'
```

**chown the PARENT too** — `/opt/app/lamp/private`, not only its contents.
Without the traversal bit, `is_dir()` is false under mod_php while being true
under CLI as root, and every endpoint silently falls back to the docroot copy.
That cost an hour on 2026-08-08.

`.htaccess` gives the pretty URLs (`/docs/idp/login`, `/docs/idp/admin/users`)
and denies the library files as defence in depth — the canonical content is
`auth/htaccess-idp` in the repo, copied verbatim above rather than retyped
here, because the two drifting apart is how a `lib.php` becomes downloadable.

### 3b. Migration 002 — the admin portal delta (E9-ADMIN-005)

Run as **root**: `capi_auth` deliberately holds DML only and cannot run DDL.

```bash
cd /opt/app
ROOT_PW=$(grep '^MYSQL_ROOT_PASSWORD' .env | cut -d= -f2-)
docker compose exec -T database mysql -uroot -p"$ROOT_PW" --default-character-set=utf8mb4 \
  < /opt/app/lamp/private/capi-auth/migrations/002-admin-portal.sql
```

Idempotent — re-running is free. It prints the five new `console_users`
columns as its own verification. New tables `console_idem` and
`console_svc_tokens` are covered by the existing `ON capi_auth.*` grant, so
no grant change is needed.

**Order matters, in one direction only.** Run the migration *before* copying
the new PHP if you can; but the code tolerates the reverse — `auth_audit()`
falls back to the pre-002 INSERT when `request_id` is missing, and the
password-change metadata write is in its own try/catch. Nothing 500s either
way. That tolerance is deliberate and should not be tidied away.

Then recreate the container so the mount and env land:
`cd /opt/app && docker compose up -d webserver`

Note: `docker compose up -d webserver` **also recreates `database`**, because
the compose file links them. Expect both to bounce, not just the web tier.

### 3a-bis. DEPLOYED 2026-08-08 14:08–14:20 UTC — record of the real run

Applied without a container restart, and therefore **without bouncing MySQL**:
nothing in this deploy adds an env var or touches `docker-compose.yml`, so
`docker compose up -d webserver` was not needed. CSEntry sync never dropped —
`https://csweb.asiansocial.org/csweb/` answered 200 before, during and after.

Pre-overwrite copies of everything replaced are at
`/opt/app/lamp/private/_pre-e9admin-20260808-140810/{lib,idp,admin}/`.

| Checked | Result |
|---|---|
| Migration 002 applied, then **re-run** | Both clean; 8 tables, all InnoDB; `pw_algo` ENUM carries `pbkdf2`; `request_id` + `ix_aud_target` + `ix_aud_req` present; 18/18 `pw_changed_at` backfilled |
| Unit suites **in the container** (PHP 8.1, not the dev 8.3) | `test_acl.php` 165 · `test_admin.php` 67 |
| Gate untouched | `/csweb/` 200 · `/` 302 · `/docs/dashboard.html` 401 · `/docs/map.html` 401 · `/docs/admin/` 401 |
| Library not reachable in the docroot | `/docs/idp/admin_bootstrap.php` **403**, `…/migrations/002-admin-portal.sql` **404** |
| `.htpasswd-docs` and all three `.htaccess` gate files | mtimes unchanged — the 501 paths wrote nothing |
| Audit `request_id` | populated on new rows, empty on pre-002 rows — the fallback in `auth_audit()` works and old rows are untouched |

**End-to-end, against the live front door**, using a disposable `zzt_owner`
(argon2id, owner) plus accounts created through the API itself. All fixtures
removed afterwards, `verify` reported `TOTAL LEFTOVER=0`:

| Behaviour | Evidence |
|---|---|
| Sign in → `/admin/ping` | returns the username and all 7 owner permissions |
| CSRF | POST without the header → 403 `csrf` |
| Create | 201 with `temp_password` + `gate_notice`; duplicate → 409; unknown role → 400 |
| Idempotency | same `Idempotency-Key` replayed returned the **identical** temp password, not a second one |
| `PUT /roles` full set | first call `changed:true`; identical replay `changed:false` |
| Optimistic concurrency | stale `row_version` → 409 `conflict` |
| Self-disable | 409 `self_disable` |
| **Escalation** | `programme_admin` refused on: granting `owner`, editing an owner's roles, editing role permissions |
| **`must_change` gate** | admin API 403 until the password was changed, then 200 |
| **SC-2, revocation** | live session 200 → owner disables the account → **same cookie 401**, no restart. Replay of the disable reports `revoked:0, changed:false` |
| Legacy screen | `?r=users` reads `console_users`; all four writes return the 501 `moved` envelope; audit tab merges the file trail and `console_audit` |
| Drift report | `htpasswd_only: []` — **nothing loses access at cutover** |

Two notes that came out of the run and are worth carrying:

- **`cplreyes` still has `must_change = 1`**, like all 18 imported accounts. At
  cutover the sole owner is forced through a password change on first sign-in.
  Expected, but know it before you are standing in a quiet window.
- `zzt_*` rows remain in `console_audit` by design. The trail is append-only;
  deleting the evidence of a test is the same operation as deleting the
  evidence of an incident. They are tagged by their actor.

### 3c. Verify the admin API

```bash
# unit suites, in the container
docker compose exec -T webserver php /var/www/private/capi-auth/test_acl.php    # 165 passed
docker compose exec -T webserver php /var/www/private/capi-auth/test_admin.php  #  64 passed

# reachable, and refuses an anonymous caller
curl -si https://capi.asiansocial.org/docs/idp/admin/ping | head -1   # 401
```

Signed in as an `admin.users` holder, `/docs/idp/admin/ping` returns the
username and the resolved permission list — which is also the fastest way to
confirm a role change took effect.

## 4. Import the 18 accounts

```bash
docker compose exec -T webserver php /var/www/private/capi-auth/import_htpasswd.php
# review the table and any COLLISIONS, then:
docker compose exec -T webserver php /var/www/private/capi-auth/import_htpasswd.php --apply
```

The dry run **refuses to apply** while `se_001`/`se-001`-style collisions are
unacknowledged. Two spellings may be two different people, and guessing hands
one person the other's access.

**What the 2026-08-08 run found.** All seven pairs exist. Evidence gathered
before deciding: every **hyphen** variant has real sync activity (1–10 events in
`sync-feed.json`); every **underscore** variant has **zero**. Both spellings sit
on the live `/docs/` gate right now.

Resolution taken: import **both, as separate rows, both active** — via
`--apply --allow-duplicates`. That reproduces today's access exactly. It never
merges. Disabling the seven dormant underscore accounts is a deliberate decision
for the admin screen, not something a migration should infer while fieldwork is
running.

Result: **18 accounts, all `must_change = 1`** (15 `apr1`, 3 `bcrypt`).
No passwords changed. Legacy hashes upgrade to argon2id on each owner's next
successful sign-in.

## 5. Smoke-test the provider WITHOUT touching the gate

```bash
docker compose exec -T webserver php /var/www/private/capi-auth/test_acl.php   # 140 passed

# anonymous -> 401
curl -s -o /dev/null -w '%{http_code}\n' \
  -H 'X-Original-URI: /docs/dashboard.html' http://127.0.0.1:8080/docs/idp/authz.php
# public route -> 204, and works even with the DB down
curl -s -o /dev/null -w '%{http_code}\n' \
  -H 'X-Original-URI: /docs/idp/login' http://127.0.0.1:8080/docs/idp/authz.php
```

Sign in at `https://capi.asiansocial.org/docs/idp/login`, then replay the
cookie after signing out — it **must** fail. That replay currently succeeds,
which is the bug this whole phase exists to fix.

## 6. Cutover — one gate for `/` and `/docs/`

Back up first: `cp /opt/elestio/nginx/conf.d/capi.asiansocial.org.conf{,.pre-idp-$(date +%Y%m%d-%H%M%S)}`

**Do not touch `location /csweb/`.** CSEntry cannot do cookie sign-in; the sync
API carries its own OAuth bearer. Putting it behind `auth_request` breaks field
data collection.

**~~BLOCKING~~ — CLEARED 2026-08-08 by E9-ADMIN-004.** The admin Users screen
used to write **only** to `.htpasswd-docs` and the three `.htaccess`
`Require user` lines, with zero references to `console_users`. The moment
`authz.php` became the gate, that screen would have been writing to a store
nothing reads — while still reporting success. The dangerous direction was
never "create a user who cannot log in" (annoying, and obvious within a
minute); it was **"disable a user, see success, and they still have access"**.

`/docs/admin/api.php` now reads `console_users` / `console_user_roles`, and
`create | password | tier | delete` return **501** with a pointer to
`/docs/idp/admin/users`. Re-verify before flipping (it is regression check #4
in `cutover-check.sh`):

```bash
curl -s -b "$COOKIE" 'https://capi.asiansocial.org/docs/admin/api.php?r=users' \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["source"], d["drift"])'
# expect: console_users {... 'gate': 'htpasswd', 'blocking': 'console_only' ...}
```

`drift.blocking` names the list that costs someone access **at this moment**:
`console_only` before the flip (those accounts exist but cannot sign in),
`htpasswd_only` after it (those accounts have just lost access). It should be
empty in both directions before you proceed.

**Step C6 also sets `CAPI_IDP_GATE=live`** on the `webserver` service in
`/opt/app/docker-compose.yml`. Nothing enforces on it — it only stops the
admin API telling every new account holder that the gate is not live yet. Set
it in the same edit as the nginx change or the notice becomes a false alarm.

**Also required at cutover — retire mod_auth_form and keep its URLs working.**
In `/etc/apache2/sites-enabled/00-uhc-auth.conf` (host-mounted at
`/opt/app/lamp/config/vhosts/`, so edits persist), back the file up, then:

- delete `<Location /docs/auth/login>` and `<Location /docs/auth/logout>` — the
  `SetHandler form-login-handler` blocks. They must go, or they keep swallowing
  that path;
- delete the `AuthType Form` / `Require user` blocks in `/docs/.htaccess` (step 7);
- add a redirect so the topbar link baked into every generated page keeps
  working, with **no page regeneration**:

```apache
RedirectMatch 302 ^/docs/auth/logout/?$ /docs/idp/logout
RedirectMatch 302 ^/docs/auth/login/?$  /docs/idp/login
```

`/docs/auth/logout` is already PUBLIC in the ACL for exactly this reason.
Afterwards, delete `/docs/login.php` and `/docs/whoami.php` and drop their two
PUBLIC/AUTH lines from `acl.php`.

```nginx
# ---- one authorization decision point ------------------------------------
location = /_capi_auth {
  internal;
  proxy_pass              http://172.17.0.1:8080/docs/idp/authz.php;
  proxy_pass_request_body off;
  proxy_set_header        Content-Length "";
  proxy_set_header        X-Original-URI    $request_uri;   # REQUIRED
  proxy_set_header        X-Original-Method $request_method;
}

location /docs/ {                       # was: no auth_request at all
  auth_request     /_capi_auth;
  auth_request_set $auth_user   $upstream_http_x_auth_user;
  auth_request_set $auth_reason $upstream_http_x_auth_reason;
  error_page 401 = @capi_login;
  error_page 403 = @capi_denied;
  error_page 500 = @capi_authdown;      # see note below
  proxy_set_header X-Auth-User $auth_user;
  proxy_pass http://172.17.0.1:8080;
  # …keep the existing proxy_set_header / body-size lines…
}

location / {                            # unchanged except the error pages
  auth_request     /_capi_auth;
  auth_request_set $auth_user   $upstream_http_x_auth_user;
  auth_request_set $auth_reason $upstream_http_x_auth_reason;
  error_page 401 = @capi_login;
  error_page 403 = @capi_denied;
  error_page 500 = @capi_authdown;
  proxy_pass http://127.0.0.1:8788;
}

location @capi_login    { return 302 /docs/idp/login?next=$request_uri; }
location @capi_denied   {
  # A user who owes a password change is bounced to set one; everyone else
  # gets a plain refusal.
  if ($auth_reason = "pwchange") { return 302 /docs/idp/change-password?next=$request_uri; }
  return 403;
}
location @capi_authdown { return 503 "Console sign-in is temporarily unavailable.\n"; }
```

**Why `error_page 500` and not 503:** nginx only understands 2xx / 401 / 403
from an `auth_request` subrequest. Any other status — including the 503
`authz.php` returns when MySQL is unreachable — is converted into a **500** for
the main request. Mapping 500 is therefore what actually catches a provider
outage.

Apply: `nginx -t && systemctl reload openresty` (or Elestio's reload path).
Hand edits to this file persist — the `auth_request` added 2026-07-28 is still live.

## 7. Delete the FilesMatch tiers

Only after step 6 verifies. This is the change that ends the filename trap.

```bash
cd /opt/app/lamp/www
for f in docs/.htaccess docs/data/.htaccess docs/admin/.htaccess docs/cases/.htaccess docs/f2/.htaccess; do
  cp "$f" "$f.pre-idp-$(date +%Y%m%d)"
done
# strip the AuthType/Require blocks; keep any non-auth directives
```

**Verification that matters:** create `/docs/zzz-test.json`, request it while
signed in as any role → must be **403**, because no ACL rule names it. Then
delete it. Under the old gate it would have been served to anyone.

## 8. Break-glass (set up BEFORE step 6, never remove)

A second server block on an alternate port still using `.htpasswd-docs`,
firewalled to Carl's IP. If the provider fails closed, this is the way back in.
Test it *before* the cutover, not after you need it.

## 9. Rollback

Each step reverses independently:

| Step | Undo |
|---|---|
| 6 | restore `capi.asiansocial.org.conf.pre-idp-*`, reload |
| 7 | restore the `.htaccess.pre-idp-*` files |
| 4 | `DELETE FROM console_users;` — no other system reads it yet |
| 1–3 | remove the mount/env, delete `/docs/idp/` and the private dir |

Nothing in Phase 1 modifies CSWeb, `csweb_f2`, the F2 Worker, the sync path, or
the respondent links.
