---
module: CAPI Console Admin Portal
epic: 9 — Data Management and Security
task_namespace: E9-ADMIN-NNN
created: 2026-08-08
status: ready to merge into scrum/epics/epic-09-data-management-and-security.md
---

# Product Backlog — CAPI Console Admin Portal (E9-ADMIN)

> Merge these into **Epic 9**, following the `E3-RELEASE-001` / `E8-SUPERVISOR-003` precedent.
> They also close three long-open Epic 9 placeholders: **E9-022** (CSWeb access control policy),
> **E9-023** (authentication model / roles), **E9-024** (audit trail design).
>
> Estimates are Carl-hours, solo. Slices are dependency-ordered; **Slice A gates the cutover.**
> No sprint numbers assigned — `sprint-current.md` is stale (still Sprint 014, 2026-07-20→24).

## Status of the foundation (context for every task below)

Phase 1 identity provider is **deployed and enforcing nothing**. `capi_auth` DB with 6 InnoDB tables, 5 roles × 7 permissions, 18 accounts imported (`must_change=1`, 15 `apr1` + 3 `bcrypt`), 146 ACL unit tests + 15 E2E smoke tests green. Live gate is still Apache `FilesMatch` + mod_auth_form.

---

## Slice A — Unblock the cutover *(nothing may flip the gate until these are done)*

- [x] **E9-ADMIN-001** Require the current password on a voluntary change; waive only when `must_change=1` `status::done` `priority::critical` `est::1h`
  - Security review finding: a stolen cookie could set a new password, and the change's `revoke_user` then locked out the real owner — cookie theft became permanent takeover. Fixed + form field + audit verb `password.change.fail` 2026-08-08.
- [x] **E9-ADMIN-002** ACL: `/docs/data/tabulations-preview.json` → `tabulations.view` `status::done` `priority::high` `est::0.5h`
  - `csweb-tabulations-gen.py:398` fetches it from inside a `tabulations.view` page; the `/docs/data/` prefix would have made it `data.export`, so `field_supervisor` and `client_viewer` got a half-rendered table. +6 tests.
- [x] **E9-ADMIN-003** `me.php` emits a legacy `tier` field `status::done` `priority::medium` `est::0.5h`
  - `portal_shell.py:140` (×2) and `csweb-responses-gen.py:427` read `d.tier` behind an **empty** `.catch()` — absent field silently blanks the topbar on every generated page.
- [x] **E9-ADMIN-004** **Repoint the existing admin Users screen** — reads from `console_users`/`console_user_roles`; `create|password|tier|delete` return **501** with a banner `status::done` `priority::critical` `est::2h`
  - **THE CUTOVER BLOCKER — closed 2026-08-08.** `admin/api.php` writes only `.htpasswd` + `.htaccess`, zero references to `console_users`. Post-cutover "disable user" reports success while access persists.
  - Done: users GET reads `console_users` (+ `live_sessions`, `must_change`, `pw_algo`, `locked`); the four write actions return 501 via `moved()`; `actor()` now prefers `X-Auth-User` → verified console session → the legacy vars; `canary_ok()`, `apply_tier()`, `set_require_list()`, `tier_of()`, `require_list()` and the three `*_HT` constants deleted.
  - Added beyond spec: a **drift report** (`htpasswd_only` / `console_only` / `blocking`) on the users payload — the pre-flip comparison that says who is about to lose access; a **merged audit tab** (file trail + `console_audit`) so neither half is presented as the whole; `tier_from_roles()` display shim so the existing `app.js` keeps rendering until Slice B replaces it. Provider outage → 503 with a message, never an empty list that reads as "no accounts".
- [x] **E9-ADMIN-005** Schema delta `002-admin-portal.sql` (run as **root**; `capi_auth` has no DDL) `status::done` `priority::critical` `est::1h`
  - `console_users`: `row_version`, `pw_changed_at`, `updated_at/by`, `disabled_at`. `console_audit`: `request_id` + `ix_aud_target` + `ix_aud_req`. New `console_idem`.
  - Ship **now**, not in Phase 2: `pw_algo` ENUM gains `'pbkdf2'` and `console_svc_tokens` is created empty — otherwise F2 federation needs an ALTER on live identity data mid-rollout.
  - Written 2026-08-08, **not yet applied**. Idempotent via `information_schema` guards (MySQL 8 has no `ADD COLUMN IF NOT EXISTS` — that is MariaDB). Backfills `pw_changed_at = created_at` for the 18 imported accounts.
- [x] **E9-ADMIN-006** Admin API foundation — `/docs/idp/admin.php` front controller + `admin_bootstrap.php` `status::done` `priority::critical` `est::3h`
  - One JSON envelope, one CSRF check, one in-process permission gate (defence in depth behind nginx), `request_id`, transaction helper, catch-all returning JSON 500 — because `log_errors` is Off, so an uncaught fatal is a blank 500 with no trace. Write the exception to `console_audit` as verb `error`.
  - Done 2026-08-08: `AdmError` (chosen errors) vs catch-all (bugs); `register_shutdown_function` for fatals the exception handler never sees; `adm_actor()` resolves the **session**, not a header, so it behaves identically before and after cutover; CSRF = double-submit **plus** an Origin/Host check, which covers the sibling-subdomain cookie until `__Host-` lands (E9-ADMIN-045); `console_idem` replay protection; ACL rules + 19 tests; `/admin/ping` liveness probe.
- [x] **E9-ADMIN-007** Users endpoints — list/create/patch/roles/password-reset/force-logout/disable `status::done` `priority::critical` `est::5h`
  - Invariants inside the transaction: at least one active `owner` (`SELECT … FOR UPDATE`, 409 `last_owner`); no self-disable; no self-demotion. `PUT /roles` takes the **full set**, so replay is a no-op. Role reassignment must call `auth_session_revoke_user` explicitly — version arithmetic does not cover it (see E9-ADMIN-008).
  - Done 2026-08-08, plus roles / sessions / audit from the same API surface (DESIGN §2). Two guards added during the build, neither in the original spec: **only an owner may grant the owner role or edit an owner's roles** — otherwise `admin.users` is silently the top of the hierarchy rather than a delegated slice of it; and the **owner role floor** (`admin.users` + `admin.system` cannot be un-ticked in the matrix), because one careless click would otherwise leave root SSH as the only route back.
  - Also: every mutation returns a **`gate_notice`** until `CAPI_IDP_GATE=live`. Pre-cutover a created account is real, correct, and unable to sign in — saying so at the moment the credential is handed over is the same honesty rule as FR-05.
  - No hard delete: it would orphan audit rows. Disable + revoke is the delete.
- [x] **E9-ADMIN-008** Correct the `role_version` documentation — the sum detects permission edits, **not** role reassignment `status::done` `priority::medium` `est::0.5h`
  - Swapping role A (v3) for role B (v3) leaves the sum unchanged and the session lives. Not an escalation (grants are re-read per request), but the comment claimed coverage it did not have.
- [x] **E9-ADMIN-009** nginx header hygiene `status::done` `priority::critical` `est::1h`
  - **This was a LIVE defect, not a cutover task.** E9-ADMIN-004 made `actor()` trust `X-Auth-User` (it has to — the legacy vars go empty at cutover), but the vhost never blanked the client-supplied copy. Proved it on 2026-08-09 with a temporary reflector: `X-Auth-User: attacker` arrived at PHP verbatim, so **any of the 18 accounts could forge the actor on every audit row**. Blanked in both `/docs/` and `/`, re-verified `(absent)`. `/csweb/` deliberately untouched — nothing under it reads those headers and it is the live sync path.
- [x] **E9-ADMIN-010** Break-glass + maintenance page `status::done` `priority::critical` `est::2h`
  - Built as a **loopback listener**, not a public alt port: this host has **no OS firewall** (`iptables INPUT` = ACCEPT, no ufw — verified), so an open port is world-reachable. `127.0.0.1:8443` TLS + `auth_basic`, reached over `ssh -L`. SSH becomes the perimeter — a key we already hold, rather than a second internet-facing login for the one system whose login is in doubt.
  - Its credential file is a **frozen copy** of `.htpasswd-docs`, deliberately not kept in sync: a break-glass that tracks the live system shares its failures. Proven end to end (401 anonymous → 200 with credentials → PHP) using a disposable probe credential, removed after.
  - Also settled a design question the plan got wrong: **do not IP-restrict it.** Carl's address changed from `175.176.46.155` to `175.176.45.159` overnight, observed in the audit trail.
  - Maintenance page (`@capi_authdown` on `error_page 500`) written into the post-cutover vhost.
- [x] **E9-ADMIN-011** Per-IP login throttle + response-time floor `status::done` `priority::high` `est::2h`
  - Per-IP ceiling (20 fails / 15 min) counted from `console_audit` — checked **before** the user lookup, so a spray of fictional usernames never reaches a password hash. The dummy argon2id hash is gone: it was meant to equalise timing and did the opposite.
  - **Measured before/after, from Manila:** nonexistent 468 ms · cplreyes 459 · se-001 456 · aspsi 477. The ordering that used to advertise a real account is now inside the noise.
  - Throttle verified against a TEST-NET address (21 fails → blocked) rather than by tripping Carl's own IP.
- [x] **E9-ADMIN-012** Audit tamper-resistance `status::done` `priority::high` `est::2h`
  - Schema-wide grant replaced with per-table grants; `console_audit` is now **`SELECT, INSERT` only**. Verified as the app user: DELETE and UPDATE both denied, INSERT and SELECT fine, and all six DML paths the app genuinely needs still work. Grants applied before the revoke so there was never a window with no privileges.

## Slice B — The portal surface

**DEPLOYED 2026-08-09.** Files under `deliverables/CSWeb/admin/`: `ui.js` (kit +
router), `admin.css` (component layer), `view-{users,roles,sessions,audit,account}.js`,
`boot.js`, rewritten `index.php`, refactored `app.js`.

- [x] **E9-ADMIN-020** Extract `ui.js` (el / tbl / dialog / api) + hash router; split one file per view `status::done` `priority::high` `est::3h`
  - Stack decision: **extend the existing vanilla-JS app**. No build toolchain exists on the box; Preact-via-htm and React/Vite were both considered and rejected (the latter needs committed `dist/` assets).
  - `ui.js` owns both API clients — `apiConsole` (flat envelope, `adm_csrf`) and `apiAdmin` (`{ok,data,request_id}`, `capi_csrf`, `Idempotency-Key`, 401 → sign-in bounce). `el()` throws on an `html` attribute so there is no innerHTML path in the app at all.
  - Activities / Alerting / Plan kept their existing logic verbatim — they are live during pretest and a rewrite would be risk with no return.
- [x] **E9-ADMIN-021** Users list + user detail/edit screens `status::done` `priority::high` `est::5h`
  - Plus the **store-drift card** (`htpasswd_only` / `console_only`), which is the pre-cutover safety check and had nowhere else to live.
- [x] **E9-ADMIN-022** Role editor (5 × 7 matrix, owner-write / programme_admin-read) `status::done` `priority::high` `est::3h`
  - Owner-floor cells render hatched and disabled. Unmanaged keys (F2's, Phase 2) are shown read-only and explicitly left untouched on save.
- [x] **E9-ADMIN-023** Active sessions screen (list + kill, "this session" self-guard) `status::done` `priority::high` `est::3h`
- [x] **E9-ADMIN-024** Audit trail screen + CSV export `status::done` `priority::high` `est::4h`
  - Cursor-paged, verb-coloured, click-an-actor-to-filter. CSV uses the **same filter string** as the view.
  - Also closed a hole this screen would otherwise have had: `admin/api.php`'s `audit()` now writes to **both** the file trail and `console_audit`, so alerting / plan / activity changes appear here instead of being silently absent.
- [x] **E9-ADMIN-025** My account (password change; MFA card disabled until E9-ADMIN-042) `status::done` `priority::medium` `est::2h`
  - Password change links to `/docs/idp/change-password` rather than reimplementing it — that flow is deployed, tested, and the only route reachable while an account still owes a change.
- [x] **E9-ADMIN-026** `/me`-driven nav; retire the second nav codepath `status::done` `priority::high` `est::2h`
  - The admin SPA's nav renders from `/docs/idp/me`; `index.php` resolves identity `X-Auth-User` → session → legacy vars (the legacy pair goes empty at cutover, which would have blanked "Signed in as"); `applyNavPermissions()` hides entries and any group that empties.
  - **The generated-page half is closed by E9-ADMIN-032, not by editing generators.** Checked what actually exists on the box: there is no `build_portal.py`; the two copies are topbar-chip JS in `portal_shell.py:140` and `csweb-responses-gen.py:427`, and both do `fetch("/docs/whoami.php")` reading `d.signed_in / d.user / d.tier` and linking `/docs/auth/logout`. Reshimming `whoami.php` over the identity provider means **both codepaths are now driven by the provider and neither breaks at cutover** — every field they read is still emitted, and the logout link becomes a 302.
  - Deduplicating those two ~10-line snippets into one shared helper is cosmetic: it regenerates every page for zero behavioural change, which is not a trade worth making during pretest. Deliberately not done, and noted here so it is a decision rather than an oversight.
- [x] **E9-ADMIN-027** Destructive-action pattern — typed confirmation, server-fetched blast radius, no optimistic UI `status::done` `priority::high` `est::3h`
  - `confirmDestructive()` in `ui.js`: opens in a checking state, fetches the radius, keeps the button disabled until it resolves, requires the exact username typed, and **blocks permanently** if the preflight fails — a dialog that cannot say what it will do does not get to do it. Verified rendering "Signs out 1 live session immediately."
- [x] **E9-ADMIN-028** Accessibility pass `status::done` `priority::medium` `est::2h`
  - Measured: `--ink-3` `#74838c` on white is **3.91:1**, failing AA, and is used for `.muted`, "last sync" and inactive tabs → introduce `--ink-3-text: #5c6a73` (5.58:1) for meaningful text. Both figures recomputed independently before use.
  - Shipped: the new token throughout, `:focus-visible` rings on buttons / tabs / nav (portal.css gives buttons none), skip link, `aria-live` on the message region, `aria-current` on the active nav item, focus moved to `<main>` on route change, native `<dialog>` focus trapping, `prefers-reduced-motion`, `.tbl.stack` card layout with `td::before{content:attr(data-label)}` below 640px, and ≥44px touch targets.

## Slice C — Hot path, then cutover

- [x] **E9-ADMIN-030** Optimise the authz hot path `status::done` `priority::critical` `est::3h`
  - Session + user + roles + permissions + role-version sum folded into **one** query. Two traps, both avoided: `GROUP_CONCAT` needs `DISTINCT` (the role×perm join multiplies rows), and the version total must be a **correlated subquery** — `SUM()` over that join double-counts and would never match the session.
  - **Measured on the box: ~5 statements per authenticated request → 2.45.** The remaining two are PDO's connect-time `SET NAMES` and the one real SELECT; the `last_seen_at` write is now conditional (once per 60 s, not once per asset). `me.php`, `admin_bootstrap` and `api.php` all dropped their second query too.
  - Correctness re-proved after the rewrite: session 200 → bump `console_roles.version` → **401**. A wrong `ver_sum` would have made sessions immortal or stillborn.
  - **nginx `proxy_cache` deliberately NOT enabled.** It is written into the post-cutover vhost, commented, with the reason: it would buy the remaining round trip at the price of a 10-second revocation SLA, and revocation is the capability this module exists for. Enable only if the DB shows real load.
- [x] **E9-ADMIN-031** Turn xdebug off in production `status::done` `priority::high` `est::0.5h`
  - The extension's ini is baked into the image and not host-mounted, but `php.ini` **is** — and the baked file sets only `zend_extension`, no mode, so a mode set in php.ini wins and survives container recreation.
  - **Trap:** `xdebug.mode = off` unquoted parses as boolean false and yields `''`, not `"off"`. Caught by reading the value back; fixed with quotes. Now `mode='off'`.
  - Same change turned **`log_errors` on** with a host-mounted log. A PHP fatal on this box had twice been a blank 500 with no line anywhere.
  - One `docker compose restart webserver` for both, **1.9 s** of downtime, database container untouched (`restart` does not follow `links:` the way `up -d` does).
- [x] **E9-ADMIN-032** `whoami.php` reshimmed over the new model `status::done` `priority::high` `est::1h`
  - Bigger than it looked: `whoami.php` is the `/_capi_auth` target for `location /`, so its status code gates the **entire static portal**. Answering only from `REMOTE_USER` meant it would 401 forever the moment mod_auth_form retired, bouncing every visitor in a loop. Now answers from the provider first, legacy second — correct in both eras, no flag day.
- [x] **E9-ADMIN-033/034** Execute the cutover `status::done` `priority::critical` `est::3h`
  - **DONE 2026-08-09 03:35 UTC on Carl's instruction.** `authz.php` is the gate. Canaries held throughout; CSEntry sync never dropped.
  - **Two gaps caught in the last preflight, before the flip, both would have bitten immediately:**
    1. Deny-by-default would have 403'd the *static portal's own assets* — `/portal.css`, `/assets/`, `/platform/`, `/uhc/`, `/about/`, `/index.html` had no ACL rule, so the public portal would have rendered with no stylesheet. Enumerated against what capi-www actually holds and added, with tests.
    2. `cutover.sh` stripped auth from `/docs/.htaccess` only. `/docs/data/.htaccess` and `/docs/admin/.htaccess` carry their own `AuthType Form` + `Require user`, and removing `<Location /docs>` takes away the Session and AuthFormProvider they depend on — the data room and admin console would have broken. Now all three are stripped, and all three are backed up and restored by `--rollback`.
  - Post-flip fixes: `/docs/auth/login` added to the ACL as PUBLIC (the Apache redirect that rescues a stale bookmark only runs if the gate lets the request through), and the three legacy redirects made https-absolute rather than bare paths — they were emitting `http://` and costing an extra plaintext hop on a login flow.
- [x] **E9-ADMIN-035** Post-cutover per-role nav crawl `status::done` `priority::critical` `est::2h`
  - Run **twice**: once against `authz.php` directly *before* the flip (five disposable accounts, one per role, 22 paths) and again through the real front door *after*. Both matrices are correct — `field_supervisor` 403s the data room, `client_viewer` 403s respondent detail, `analyst` 403s admin, an unlisted path 403s for everyone, anonymous gets 302 to sign-in.
  - Also verified post-flip: a spoofed `X-Auth-User: attacker` with a valid session reports the **real** user; the library files 403 to an authenticated owner; and `/docs/auth/logout` — baked into every generated topbar — redirects correctly **with no page regenerated**.
  - Incidental: `test_db.php`'s cleanup predicate is `zzt\_%`, which swept the `zzt_r_*` role fixtures mid-run. Not a production risk (no real account starts with `zzt_`), but probe accounts need a different prefix; these used `zzq_r_*`.

## Slice D — Compliance and hardening

- [x] **E9-ADMIN-040** `test_lib.php` + `test_db.php` unit suites `status::done` `priority::high` `est::4h`
  - **49 + 51 assertions.** `auth_apr1_crypt` cross-checked against six `openssl passwd -apr1` vectors generated on the host — a *different implementation*, so it is a real check rather than the function agreeing with itself. Covers short salt, empty password and multi-byte UTF-8 (this estate has ñ in real data).
  - `test_db.php` covers session resolve/idle/absolute boundaries, revocation, disable, role-version invalidation, lazy rehash apr1→argon2id, per-account lockout and the per-IP throttle. Cleanup is registered **before** the first insert, so a failure or a fatal still cleans up; `--verify-clean` confirms.
  - **It found a real inconsistency immediately:** `auth_session_revoke_user()` returned the count of *unrevoked* rows including already-dead ones, while the destructive dialog promises "signs out N **live** sessions" from a stricter definition. Confirmation and result could disagree. Now revokes everything (hygiene) but counts only what was live.
- [x] **E9-ADMIN-041** `cutover-check.sh` regression script `status::done` `priority::high` `est::2h`
  - **25 checks**, run before and after the flip, CSEntry sync as canary #1. Canary failures exit 1 (roll back now); everything else exits 2 (understand before flipping). Most checks are written to hold in *both* eras so the two runs are directly comparable. Currently **25/25 green**.
- [ ] **E9-ADMIN-042** MFA (TOTP) `status::todo` `priority::high` `est::6h`
  - RFC 6238, SHA-1/6/30, ±1 step, plus `last_totp_step` to stop replay within the window. Secret held as **AES-256-GCM ciphertext** under a compose-env key (the DB has no encryption at rest). Locally generated QR — never an external chart service. Ten argon2id-hashed single-use recovery codes. Mandatory for `owner`, `programme_admin`, and any `data.export` holder (which includes `analyst`).
  - **Provision a second `owner` with its own device before enabling enforcement** — "SSH as root" cannot be the standing recovery answer for a sole owner.
- [x] **E9-ADMIN-043** Session + audit GC and a written retention schedule `status::done` `priority::medium` `est::2h`
  - `auth/gc.php` + nightly cron (19:30 UTC). Sessions carry IP and user-agent — personal data with no stated retention — now removed 30 days after the session dies; idempotency keys after 24 h. `console_audit` is untouched and *cannot* be pruned by the app (E9-ADMIN-012); its schedule is written down instead. Schedule: `admin-portal/RETENTION.md`.
  - **Found while verifying NFR-04 ("audit included in the nightly dump"): it was not.** `/opt/borg/preBackup.sh` assigned the MySQL root password to a variable and then ran `mysqldump --password=` with the value omitted → exit 1045 every night, and `postBackup.sh` deleted the near-empty file, so the failure left no trace. **Every borg snapshot contained an empty SQL dump — for the whole estate, not just `capi_auth`.** Fixed by passing the variable already there; the dump is now ~18 MB covering all eight databases. Original kept as `preBackup.sh.pre-fix-*`.
- [x] **E9-ADMIN-044** Data-subject rights runbook `status::done` `priority::medium` `est::4h`
  - `admin-portal/DATA-SUBJECT-RIGHTS.md`, written against the **verified** schema (`csweb_uhc_y2.*_DICT` + `_notes` + `_case_binary_data`, the three breakouts, `csweb_f2.f2_responses`/`f2_hcws`), plus the generators that must be re-run so a deleted case does not simply regenerate.
  - Access/export is unambiguous and documented. **Erasure is explicitly gated on ASPSI/DOH sign-off** — whether §16(e) applies at all to a DOH-mandated statistical collection is a legal determination, not an engineering one. Also states plainly what cannot be reached: tablet copies, and borg snapshots for 7 days.
- [x] **E9-ADMIN-045** Cookie + header hardening `status::done` `priority::medium` `est::2h`
  - `__Host-capi_sid` / `__Host-capi_csrf` — the prefix is browser-enforced and, crucially, forbids a `Domain` attribute, so no sibling `*.asiansocial.org` host can plant a session cookie. Done **before** cutover on purpose: renaming a cookie invalidates every session, which today is a handful of test sessions and afterwards would be the whole estate.
  - CSP on the sign-in page: `default-src 'none'`, the single inline `<style>` allowed by **nonce** rather than `unsafe-inline`, and `form-action 'self'` so an injected form cannot post credentials off-origin.
  - `Cache-Control: no-store, private` added at the nginx `/docs/` layer — `authz.php` set it on the *subrequest*, which nginx discards, so protected case JSON had been shipping cacheable. Trimmed the duplicate `nosniff`/`Referrer-Policy` I first added after seeing three copies in the response.
- [ ] **E9-ADMIN-046** Phase 2 readiness — `/docs/idp/svc/f2/*` contract `status::todo` `priority::medium` `est::3h`
  - Its own nginx location with **no** `auth_request`, bearer + origin-cert/IP allowlist, own rate limit, audit namespaced `svc:f2`, and `['/docs/idp/svc/', 'DENY']` in `ACL_PREFIX` so no cookie session can reach it. Dual-read/diff behind a Worker env flag; compare only a SHA-256 **prefix** of `pw_hash` so no hash material enters a log.

---

## Rollup

| Slice | Tasks | Done | Est. remaining |
|---|---|---|---|
| A — unblock cutover | 12 | **12** | — |
| B — portal surface | 9 | **9** | — |
| C — hot path + cutover | 6 | **6** | — |
| D — compliance + hardening | 7 | **5** | ~9 h |
| **Total** | **34** | **32** | **~9 h** |

**Slices A, B and C are complete. The gate is `authz.php` as of 2026-08-09.**

## Success criteria — the honest score

Was 0 of 6 when this module was specified.

| # | | |
|---|---|---|
| SC-1 | Who can reach respondent data? | **PASS** — one query returns every account's effective permissions, and an unlisted path under `/docs/` 403s for all five roles (verified twice, before and after the flip) |
| SC-2 | Can we revoke right now? | **PASS** — disable → the captured cookie 401s on its next request, no restart. And no screen reports success while writing to a store nothing reads |
| SC-3 | Who looked at what? | **PASS** — `read` and `perm.deny` rows are landing with actor, path and IP; filterable and CSV-exportable from the Audit screen |
| SC-4 | Is a stolen password enough? | **FAIL** — no MFA (042), and all 18 accounts still carry `must_change=1` |
| SC-5 | Does auth ever stop fieldwork? | **PARTIAL** — `/csweb/` has no `auth_request` by construction and answered 200 throughout the cutover. The `@capi_authdown` maintenance page is configured but **not exercised**: proving it needs a real database outage, which would stop sync |
| SC-6 | Can we get back in? | **PARTIAL** — break-glass is proven end to end (401 → 200 → PHP). `cutover.sh --rollback` is written and its dry run works, but a full rollback has deliberately not been executed |

## What is left

| | |
|---|---|
| **042 MFA** | Needs a **second owner with their own device** provisioned first — otherwise a lost phone makes root SSH the only way back in, which the design explicitly refuses. This is what SC-4 is waiting on, together with clearing `must_change` on all 18. |
| **046 Phase 2** | F2 federation. Explicitly after pretest, by the original plan. |

Slices A + C are the minimum that makes the gate safe to flip. B makes it operable. D is what an audit would ask for.

## Where Slice A stands (2026-08-08)

**DEPLOYED and verified in production, 14:08–14:20 UTC.** 004 / 005 / 006 / 007
are live: migration `002-admin-portal.sql` applied (and re-applied, to prove
idempotency), library `auth/admin_{bootstrap,users,roles,sessions,audit}.php`,
front controller `auth/admin.php` at `/docs/idp/admin/…`, ACL rules, and the
repointed `admin/api.php` + `app.js`. **232 assertions green in the container**
on PHP 8.1 — `test_acl.php` 165 (was 146) and a new `test_admin.php` 67.

No container restart was needed, so MySQL never bounced and CSEntry sync held
200 throughout. The gate is **unchanged** — `/docs/dashboard.html` still 401s
via Apache, exactly as before. Full evidence table in `../auth/DEPLOY.md §3a-bis`.

The end-to-end run proved the thing this module exists for: a live session
answering 200, disabled by an owner, then **401 on the same cookie with no
restart** — SC-2, which scored 0 this morning. It also proved the escalation
guards hold: a `programme_admin` was refused on granting `owner`, on editing an
owner's roles, and on editing role permissions.

**And the drift report came back `htpasswd_only: []`** — every account that can
reach the console today exists in `console_users` with a role. Nothing loses
access when the gate flips.

`test_admin.php` earns its place twice over. It caught a real defect in code
about to ship — `preg_match('/…$/')` also matches before a trailing newline,
so `"carl\n"` passed username validation; fixed with `\z` in three places. And
its first assertion is a **drift check between `CONSOLE_PERMS` in `acl.php`
and `ADM_PERM_KEYS` in `admin_roles.php`**: if those lists diverge you get
either a permission no role can be granted, or a tick box that grants
something no path ever checks — and both look completely normal on screen.

**Still open in Slice A, and all four are ops rather than code:** 009 (nginx
header hygiene), 010 (break-glass vhost), 011 (login throttle + timing floor),
012 (audit tamper-resistance). 010 is the one that gates everything: never
flip the gate without a tested way back in.
