# Making the CAPI Console a real Admin Portal — plan

**Asked:** 2026-08-04, Carl — "Can we make the CAPI Console Admin? Complete the plan on how to do it."
**Answer:** Yes, and cheaper than it looks — every capability needed is already on the box.
**Companion:** the 2026-08-03 assessment (why it isn't one today).

---

## 1. What exists today (measured, not assumed)

| | Today |
|---|---|
| Authentication | Apache `mod_auth_form` against `.htpasswd-docs` — **18 accounts, `$apr1$` (MD5-crypt) hashes** |
| Authorization | Hand-edited `Require user` lists in `.htaccess` — 2 tiers in `/docs/`, plus per-directory files for `data/`, `admin/`, `f2/`, `cases/` |
| Sessions | `mod_session_cookie` — **stateless, encrypted, 8 h, NO server-side revocation.** Logout is browser-side only; a captured cookie stays valid until expiry |
| MFA | None |
| Audit | `/docs/admin/audit.log` covers admin-app mutations only. **No record of who read respondent data** |
| Admin app | `/docs/admin/` (index.php + api.php + app.js) manages alerts, targets, activities. Correctly gated: staff-tier directory auth + `Require all denied` on the data files |

## 2. The enablers — all verified present on 2026-08-04

This is what makes the plan cheap rather than speculative:

- **`mod_session_dbd.so`, `mod_dbd.so`, `mod_authn_dbd.so`, `mod_authn_socache.so` all ship in the image** — present, simply not loaded. `LoadModule` lines in the host-mounted `config/vhosts/` survive container recreation (`mods-enabled` is NOT mounted — this is the known-good route).
- **bcrypt is supported**: `htpasswd -nbB` returns `$2y$05$…`.
- **nginx `auth_request` already gates the capi vhost in production** (`capi.asiansocial.org.conf:61`). The auth-service pattern is proven here, not theoretical.
- **A working identity system already exists on the same MySQL**: the F2 admin portal (`csweb_f2`) has RBAC with granular permission keys, roles, user lifecycle incl. bulk import, login throttling, **server-side session revocation**, and an audit log.

**The single most valuable consequence:** the estate does not need a *new* identity system. It needs the one that already works to serve both surfaces.

## 3. Scope discipline — what "admin portal" should mean here

This is a time-boxed DOH engagement with ~18 known operators, not a multi-tenant SaaS. Chasing feature-parity with a commercial admin console would burn the schedule on things nobody will use (SSO/SAML, org hierarchies, billing, seat management).

**Judge it by risk, not by feature checklist.** The portal must be able to answer four questions:
1. *Who can reach respondent data?* → RBAC from a source of truth, not hand-edited regex
2. *Can we revoke access right now?* → server-side sessions
3. *Who looked at what?* → read auditing, because this is named PII under the PH Data Privacy Act
4. *Is a stolen password enough?* → MFA

Everything below serves those four. Anything that doesn't is out of scope.

---

## 4. Architecture fork — decide before building

Per the standing rule, **the first execution step is a rendered options comparison**, not code. Inputs:

| Option | Shape | Trades |
|---|---|---|
| **A · Harden Apache in place** | Load `mod_session_dbd` (sessions → MySQL), rehash to bcrypt, generate `.htaccess` from a table | ✓ No new service, smallest change, keeps static-file model ✓ Fixes revocation + hashes today ✗ MFA in Apache is fringe (`mod_authn_otp`, poorly maintained) ✗ Still two logins across the estate |
| **B · One identity service (recommended)** | Extend the **F2 admin identity** to cover the console; nginx `auth_request` calls it; console files stay static | ✓ MFA, audit, revocation, RBAC, user lifecycle — built **once**, already mostly built ✓ **Kills the two-logins problem permanently** ✓ Reuses tested code and the existing `auth_request` hook ✗ Couples the console's availability to f2-api ✗ Largest change |
| **C · New standalone auth service** | Purpose-built service in front of the console | ✓ Clean separation ✗ Third identity system to run; duplicates what F2 already does |

**Recommendation: B, staged behind A.** Do A's quick wins first (they are strictly useful under any option and reduce live risk immediately), then move identity to the F2 service. C only if the console must outlive the F2 app.

**Availability caveat for B:** if `f2-api` is down, `auth_request` fails closed and the console locks out. Mitigate with `error_page 500 502 503 504` → a maintenance page, an `auth_request` cache, and a documented break-glass (`.htpasswd` fallback vhost) before cutting over.

---

## 5. Phased plan

### P0 — Credential + session hygiene (no new infrastructure, ~half a day)

Do this regardless of the fork; nothing here is wasted work under any option.

1. **Force password reset on the F2 side** — `password_must_change = 1` for all 9 `csweb_f2.f2_users`. Three (`se_004/005/007`) have **never logged in** and still hold setup passwords; `100%SetupMe!` was demonstrably live on `carl_admin` on 2026-07-31.
2. **Rehash the console to bcrypt** — regenerate `.htpasswd-docs` with `htpasswd -B`. Users keep their passwords; only the stored hash changes. Do it as a *rewrite of the whole file* from a source list, then diff the username set before/after.
3. **Rotate `cplreyes`** (generated by me, transited tool output repeatedly).
4. **Server-side sessions** — load `mod_dbd` + `mod_session_dbd`, point at a `console_sessions` table, swap `SessionCookieName` for `SessionDBDCookieName`. Logout then actually revokes. Keep `SessionMaxAge 28800`.
   *Verification:* capture a cookie, log out, replay it → must 401. (The current build passes this replay today, which is the bug.)

### P1 — Authorization from a source of truth (~1 day)

5. **Move the tier lists out of `.htaccess`.** Today `Require user …` is hand-maintained in five files and drifts. Create `console_users`/`console_roles` in MySQL, and either
   - generate the `.htaccess` blocks from it (Option A path — keeps Apache authoritative), or
   - use `mod_authz_dbd` to evaluate group membership directly (no regeneration step).
   Either way the admin console gains a **Users & Roles** screen instead of an SSH session.
   *Guardrail:* the admin console already rewrites `Require user` lines; any generator must preserve them byte-identically for blocks it does not own — that assertion has caught mistakes twice.

6. **Read auditing.** The cheapest correct source is Apache's own access log: it already records `REMOTE_USER` + path + timestamp. Ship a small parser into an `access_audit` table, filtered to respondent-data paths (`/docs/cases/**`, `/docs/f2/**`, `/docs/data/**`, `case.html`, `f2-case.html`). Surface it in the admin console as "who viewed what".
   *This matters more now than last month*, because the console viewers widened respondent-level read access to field logins.

### P2 — Unify identity (the actual "admin portal", ~2–3 days)

7. Extend the F2 admin service with a `/authz/console` endpoint that nginx `auth_request` calls, returning 200/401 plus `X-User`/`X-Tier` headers.
8. Point `capi.asiansocial.org.conf` at it; drop the Apache auth blocks for `/docs/**` **except** a documented break-glass vhost.
9. Add **MFA (TOTP)** once, in that service — it then covers the console and the F2 portal together.
10. Merge the two account sets (`f2_users` + `.htpasswd-docs`), retiring duplicates (`se_001` vs `se-001` variants exist today).
11. **Never** put the CSEntry sync path behind cookie auth — `capi.asiansocial.org.conf:16` says it explicitly, and pretest sync must not be touched.

### P3 — Compliance surface (~1 day)

12. **Retention & deletion workflow** — a documented, executable path to delete or export one respondent's data across `csweb_f2`, the breakouts, the data room and the per-case JSON. Required under the PH Data Privacy Act; currently absent.
13. **Access review export** — "who had access to what, when", from `console_users` + `access_audit`. This is what a DOH or ASPSI data-protection query will ask for.

---

## 6. Guardrails

- **Fieldwork is live.** Every auth change risks locking out operators mid-collection. Do P0/P1 in a quiet window, keep a break-glass vhost, and test with a throwaway account before touching real ones.
- **Never change the enumerator sync path.** Standing instruction, and the nginx config repeats it.
- **Gate before you generate.** `/docs/` `FilesMatch` blocks match *filenames*, so any new directory is public until it has its own `.htaccess`. This nearly shipped `plan.json` publicly and applied again to `/docs/f2/` and `/docs/cases/`.
- **The generators must keep working.** Dashboard, map, responses, SPSS, tabulations, f2-cases and cases all write into `/docs/**` on cron; an auth change must not break their write path (they write to disk, not over HTTP — verify this stays true).
- **Preserve `Require user` lines byte-for-byte** in any block a script does not own.

## 7. What I would NOT build

SSO/SAML/OIDC · organisation hierarchies · seat/billing management · a full admin SPA (the existing PHP admin app is adequate for alerts/targets/activities) · self-service signup. None of these serve the four risk questions, and all of them cost schedule.

## 8. Open decisions for Carl

1. **Option A or B?** (A is fast and safe; B is the real answer and couples the console to f2-api.)
2. **Does the console need to outlive the F2 app?** If yes, B is wrong and C is right.
3. **MFA for everyone, or staff-tier only?** Enforcing TOTP on seven field supervisors mid-fieldwork has a support cost.
4. **Timing** — P0 is safe now; P2 wants a quiet window between pretest and rollout.
