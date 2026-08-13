# CAPI Console admin portal — Option C build plan

**Decided:** 2026-08-08, Carl — *"Can we also have CAPI Console admin portal just like the F2 Admin portal? Then later on, have a way to integrate them in order to manage properly."* → **Option C**, chosen off `capi-console-vs-f2-admin-options.png`.

**Supersedes:** the architecture sections of `capi-console-admin-plan.md` (2026-08-04) and `capi-console-authn-authz-plan.md` (2026-08-08). Their role model, ASVS standards and guardrails carry forward unchanged; this document settles *where the provider lives* and *how the two portals merge*.

---

## 1. The correction this plan is built on

Both earlier plans said the F2 admin portal's identity lived in this box's MySQL and recommended extending it. **Read in source on 2026-08-08, that is wrong:**

| | F2 Admin Portal (actual) |
|---|---|
| Runtime | Cloudflare Worker `f2-pwa-worker` |
| Hashing | PBKDF2-SHA256 × 100 000 (Workers caps `deriveBits` at 100k) |
| Tokens | Admin JWT, 4 h, claims `{ sub, role, role_version, jti, iat, pwc }` |
| Revocation | Workers KV `F2_AUTH` — `revoked_jti:<jti>` (one token), `revoked_user:<sub>` (all tokens, `iat` compared to revoke time) |
| RBAC | 11 boolean `PERM_KEYS`, role cache keyed by name with per-request version validation + 5 min TTL |
| **Store** | **Google Sheets `F2_Users` / `F2_Roles`, reached through Apps Script** |

The **model** is excellent and worth copying. The **store and runtime** are not, for a console that serves respondent PII: they would put identity in a spreadsheet behind two external services and send every gated page load off the box.

**So: copy F2's model, not its plumbing.**

## 2. The boundary that must NOT move

Unchanged from the authn/authz plan, restated because it is the thing most likely to be implemented literally and break fieldwork:

- **F2 respondents (healthcare workers)** authenticate by tokenised link — `/f/<slug>`, `/e/CODE?k=`. They are survey subjects, not users. **Stays tokenised.**
- **CSEntry devices** sync with CSWeb credentials over the sync API, not cookies. `capi.asiansocial.org.conf:16` says so explicitly. **Not touched — and not during pretest.**

## 3. Phase 1 — the console's own provider, on the box

### 3.1 Realised as endpoints, not a daemon

The canvas labels it `capi-authd`. Concretely it is **PHP endpoints inside the Apache that already runs there**. Verified on the box 2026-08-08:

| Fact | Value |
|---|---|
| Front door | Elestio **openresty** on :80/:443, config at `/opt/elestio/nginx/conf.d/capi.asiansocial.org.conf` (hand edits persist — the `auth_request` added 2026-07-28 is still live) |
| App container | `webserver` = `lamp-php8`, **PHP 8.1.34**, `pdo_mysql` **and** `mysqli` present |
| `PASSWORD_ARGON2ID` | **available** |
| PHP → DB | `new PDO("mysql:host=database…")` from the webserver container: **OK** |
| DB container | `database` = `lamp-mysql8` |
| Docroot | `/opt/app/lamp/www` → `/var/www/html` (host-mounted, survives recreation) |
| Static portal | `capi-www` = plain `nginx:alpine` on `127.0.0.1:8788`, content only |

**The gate as it actually stands** (this corrects an earlier note that called `whoami.php` the gate — it is both the topbar identity chip *and* the `auth_request` probe, but it only answers *"is anyone signed in"*, never *"may they see this path"*):

```nginx
location /csweb/     { proxy_pass http://172.17.0.1:8080; }   # NO auth_request — CSEntry sync
location /docs/      { proxy_pass http://172.17.0.1:8080; }   # NO auth_request — Apache FilesMatch gates it
location = /_capi_auth { internal; proxy_pass http://172.17.0.1:8080/docs/whoami.php; … }
location /           { auth_request /_capi_auth; error_page 401 = @capi_login;
                       proxy_pass http://127.0.0.1:8788; }    # static portal
```

So the split the canvas shows is exactly this: **nginx gates `/`, Apache gates `/docs/`, and they disagree.** Phase 1 makes `/_capi_auth` a real per-path authorizer and puts `/docs/` behind the same one.

Everything the diagram claims still holds: the subrequest goes to the loopback, never leaves the machine, and has no external dependency.

### 3.2 Designed for two consumers from day one

This is the only structural difference between Option C and Option A, and it is what makes Phase 2 cheap:

**Permissions are rows, not columns.** A generic `console_role_perms(role_id, perm_key)` table holds console keys (`monitoring.view`, `case.view`, …) *and*, in Phase 2, F2's keys (`dash_data`, `dash_users`, …) side by side. One role can carry both. Had we modelled permissions as boolean columns — the shape F2 uses in Sheets — adding F2's eleven keys later would mean an ALTER on a live table and a rewrite of every query.

### 3.3 Schema

`ENGINE=InnoDB` is explicit on every table: some existing tables in this estate are MyISAM, which silently voids transaction rollback.

```sql
CREATE TABLE console_users (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(64)  NOT NULL UNIQUE,
  full_name     VARCHAR(128) NOT NULL DEFAULT '',
  email         VARCHAR(190) NOT NULL DEFAULT '',
  pw_hash       VARCHAR(255) NOT NULL,
  pw_algo       ENUM('argon2id','bcrypt','apr1') NOT NULL DEFAULT 'argon2id',
  must_change   TINYINT(1)   NOT NULL DEFAULT 1,
  totp_secret   VARBINARY(255) NULL,
  totp_enforced TINYINT(1)   NOT NULL DEFAULT 0,
  status        ENUM('active','disabled') NOT NULL DEFAULT 'active',
  failed_count  SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  locked_until  DATETIME NULL,
  last_login_at DATETIME NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by    VARCHAR(64)  NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE console_roles (
  id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name         VARCHAR(48) NOT NULL UNIQUE,
  label        VARCHAR(96) NOT NULL,
  version      INT UNSIGNED NOT NULL DEFAULT 1,   -- bumped on ANY perm change
  is_protected TINYINT(1)  NOT NULL DEFAULT 0     -- owner role cannot be demoted/deleted
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE console_role_perms (
  role_id  INT UNSIGNED NOT NULL,
  perm_key VARCHAR(48)  NOT NULL,                 -- 'monitoring.view' … later 'dash_data' …
  PRIMARY KEY (role_id, perm_key),
  FOREIGN KEY (role_id) REFERENCES console_roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE console_user_roles (
  user_id INT UNSIGNED NOT NULL,
  role_id INT UNSIGNED NOT NULL,
  PRIMARY KEY (user_id, role_id),
  FOREIGN KEY (user_id) REFERENCES console_users(id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES console_roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE console_sessions (
  sid_hash     CHAR(64)     NOT NULL PRIMARY KEY, -- SHA-256 of the cookie token, never the token
  user_id      INT UNSIGNED NOT NULL,
  role_version INT UNSIGNED NOT NULL,             -- F2's trick: stale role kills the session
  issued_at    DATETIME     NOT NULL,
  last_seen_at DATETIME     NOT NULL,
  expires_at   DATETIME     NOT NULL,
  revoked_at   DATETIME     NULL,
  ip           VARCHAR(45)  NOT NULL DEFAULT '',
  user_agent   VARCHAR(255) NOT NULL DEFAULT '',
  KEY (user_id), KEY (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE console_audit (
  id     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ts     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actor  VARCHAR(64)  NOT NULL,
  verb   VARCHAR(32)  NOT NULL,   -- login | login.fail | logout | read | perm.deny | user.* | role.*
  target VARCHAR(255) NOT NULL DEFAULT '',
  detail JSON         NULL,
  ip     VARCHAR(45)  NOT NULL DEFAULT '',
  KEY (ts), KEY (actor), KEY (verb)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**`sid_hash`, not `sid`.** The cookie carries a 32-byte random token; the table stores only its SHA-256. A dump of `console_sessions` therefore hands an attacker no usable session.

### 3.4 Roles and the ACL

Five roles × seven console permissions, carried over from the authn/authz plan:

| Role | monitoring.view | case.view | data.export | tabulations.view | admin.users | admin.system | audit.view |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `owner` (Carl) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `programme_admin` (ASPSI) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `analyst` | ✓ | ✓ | ✓ | ✓ | — | — | — |
| `field_supervisor` | ✓ | ✓ | — | ✓ | — | — | — |
| `client_viewer` (DOH) | ✓ | — | — | ✓ | — | — | — |

Path → permission, evaluated in order, **deny by default**. Kept in a version-controlled PHP config, *not* in the database — so a DB problem can never silently widen access:

| Path | Permission |
|---|---|
| `/login`, `/logout`, `/me/password`, static assets | public (the only public routes that will exist) |
| `/`, `/projects/**`, `/help.html` | any authenticated |
| `/docs/dashboard.html`, `/docs/map.html`, `/docs/sync-feed.json`, `/docs/plan.json` | `monitoring.view` |
| `/docs/case.html`, `/docs/f2-case.html`, `/docs/cases/**`, `/docs/f2/**` | `case.view` |
| `/docs/data/**` | `data.export` |
| `/projects/uhc-y2/tabulations/**` | `tabulations.view` |
| `/docs/admin/users**` | `admin.users` |
| `/docs/admin/**` | `admin.system` |
| **everything else** | **deny** |

### 3.5 Endpoints

| Method + path | Purpose |
|---|---|
| `GET /authz` | nginx subrequest. Resolves cookie → session → user → roles → perms, maps `X-Original-URI` to a required perm, returns **204** + `X-Auth-User` / `X-Auth-Roles`, else **401**. Bumps `last_seen_at`; enforces idle + absolute timeout. |
| `GET/POST /login` | Form login (extends the existing `login.php`). Throttle + lockout, then TOTP step where enforced, then `must_change` redirect. |
| `POST /logout` | Sets `revoked_at`. **Logout finally revokes.** |
| `GET /me` | JSON identity + perms, for nav rendering. |
| `PATCH /me/password` | Self-service change — the *only* route reachable while `must_change = 1`. |
| `/docs/admin/api.php` | Extended with `users`, `roles`, `sessions` (list + kill), `audit`. |

`role_version` is compared on every `/authz` call, exactly as F2's `requirePerm` does: change a role's permissions, bump `version`, and every existing session holding the old version dies on its next request.

### 3.6 nginx wiring, and what happens when auth breaks

```nginx
location = /authz {
    internal;
    proxy_pass              http://127.0.0.1:8080/auth/authz.php;
    proxy_pass_request_body off;
    proxy_set_header        Content-Length "";
    proxy_set_header        X-Original-URI    $request_uri;
    proxy_set_header        X-Original-Method $request_method;
}

location / {
    auth_request     /authz;
    auth_request_set $auth_user $upstream_http_x_auth_user;
    error_page 401           = @login;
    error_page 500 502 503 504 = @authdown;
    # …existing config…
}
location / docs/ { auth_request /authz; … }          # /docs/ joins the SAME gate

location @login    { return 302 /login?next=$request_uri; }
location @authdown { root /var/www/maintenance; try_files /auth-down.html =503; }
```

`auth_request` **fails closed**. Three things are required before cutover:

1. `error_page 5xx → @authdown` so a broken provider shows a maintenance page, not a blank 500.
2. A short positive `auth_request` cache so a burst of case-JSON fetches doesn't become a burst of DB hits.
3. A **documented break-glass vhost** on an alternate port, still on the old `.htpasswd`, firewalled to Carl's IP. Never remove it.

### 3.7 Migrating the 18 existing accounts

`$apr1$` hashes cannot be converted to argon2id — the plaintext isn't recoverable. Flag-day resets during fieldwork are how people get locked out. So use **lazy rehash**:

1. Import all 18 usernames with their existing hash, `pw_algo='apr1'`, and assign each a role per §3.4.
2. `verify()` accepts all three algorithms; on a successful `apr1` or `bcrypt` login it **immediately rehashes to argon2id** and updates the row.
3. Set `must_change = 1` on every account — and *enforce* it (today it is `0` on all nine F2 users, including three that have never logged in, which is how `100%SetupMe!` stayed live on `carl_admin`).
4. Dedupe the `se_001` / `se-001` variants during import; report collisions rather than silently merging.
5. Rotate `cplreyes` at this point. *(Deferred by standing instruction — do it when Carl lifts that.)*

### 3.8 Steps and verification

| # | Step | Verification |
|---|---|---|
| 1 | Create schema; seed 5 roles + perms | Every role's perm set matches §3.4 exactly |
| 2 | Import 18 accounts, assign roles, dedupe | Username set before == after; every human has exactly one role |
| 3 | Build `/authz` + login/logout/me | Unit test: every path in §3.4 × every role returns the expected code |
| 4 | Add `sessions` + `audit` screens to `/docs/admin/` | Capture a cookie, kill the session in the UI, replay → **401** (today the replay succeeds; that is the bug) |
| 5 | Point `auth_request` at `/authz` for `location /` **and** `/docs/` | Break-glass verified reachable *first*; then all §3.4 paths behave per role |
| 6 | **Delete every `FilesMatch` tier** and add deny-all | Create a new file under `/docs/` — it must be unreachable without appearing in any list |
| 7 | `/me`-driven nav; retire the second nav codepath | `client_viewer` sees no admin link, and still gets 403 typing the URL |
| 8 | TOTP for `admin.*` and `data.export` | Privileged login demands a code |
| 9 | Read auditing into `console_audit` | Opening a case appears in the trail within a minute |

Steps 1–4 and 8–9 are additive and safe to build now. **Steps 5–6 are the cutover** and want a quiet window.

## 4. Phase 2 — F2 joins, after pretest

### 4.1 The swap is one module

F2's handlers reach identity through `worker/src/admin/apps-script-client.ts`. Phase 2 replaces that client with an HTTPS client pointed at the console provider:

```
worker/src/admin/handlers/*.ts   →  apps-script-client.ts   →  Apps Script  →  Sheets   (today)
worker/src/admin/handlers/*.ts   →  idp-client.ts           →  https://capi.asiansocial.org/authz/f2/*   (Phase 2)
```

**Everything else in F2 stays**: the React admin UI, PBKDF2 verification, JWT minting, `role_version`, KV revocation, throttle, audit. Only the answer to *"where do users and roles come from"* changes.

The eleven `PERM_KEYS` become `console_role_perms` rows. `role_version` already exists on both sides and maps 1:1 — this is precisely why copying F2's model in Phase 1 matters.

### 4.2 Worker → box authentication

The Worker is off-box, so this link needs its own credential: a long random service token in a Worker secret, checked by the provider, **plus** an IP allowlist or Cloudflare-origin-cert check. This endpoint is the one genuinely new attack surface Phase 2 introduces — it must be rate-limited and audited separately from human logins.

### 4.3 Cutover and rollback

- Ship `idp-client.ts` behind a Worker env flag defaulting to Apps Script.
- Dual-read and diff for one week: every identity lookup hits both, logs disagreement, serves the Sheets answer.
- Flip the flag when the diff is clean for seven days.
- **Rollback is flipping the flag back** — no data migration to unwind.
- Keep Sheets as a read-only export for one month, then retire it as an identity store.

## 5. Sequencing against pretest

| When | What |
|---|---|
| Now | Phase 1 steps 1–4, 8–9 — additive, nothing user-visible changes |
| Quiet window, pretest → rollout | Phase 1 steps 5–6 — the cutover, with break-glass verified first |
| After pretest ends | Phase 2, dual-read week, then flip |

Never during any of this: the CSEntry sync path, or the respondent tokenised links.

## 6. Out of scope

SSO / SAML / OIDC · organisation hierarchies · self-service signup · row-level security · seat or billing management. None of it serves a ~20-person fixed team on a time-boxed engagement.

## 7. Still open

1. **Client Viewer for DOH — do we issue those accounts?** A client-relationship call, not a technical one.
2. **MFA scope** — privileged roles only (recommended), or everyone including seven field supervisors mid-fieldwork?
3. **CSWeb's own login stays separate?** It is a third-party app with its own user table; unifying it is out of scope here. Confirm two logins are acceptable for anyone who edits cases inside CSWeb itself.
