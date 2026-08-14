# CAPI Console — authentication & authorization, done the standard way

**Asked:** 2026-08-08, Carl — *"Fix the authentication and authorization of CAPI Console. Plan the standard way and best practice. Should not have split features with public or private. Should be uniform that every user has login credentials. We'll build the right roles."*
**Supersedes:** the auth sections of `capi-console-admin-plan.md` (2026-08-04). That plan's phases still hold; this one settles the model they were missing.
**Standards followed:** OWASP ASVS v4 (§2 authentication, §3 session management, §4 access control), deny-by-default, RBAC with least privilege, RA 10173 (PH Data Privacy Act).

---

## 1. Decisions locked by this instruction

1. **No public tier.** Every console page requires an authenticated session. No page-by-page "is this one public?" judgement ever again.
2. **One credential per human.** Every console user has their own named login. No shared accounts, no anonymous access, no "the dashboard link is fine to pass around".
3. **Roles decide what you see *after* login** — never whether you can reach the site at all.

## 2. Current state (measured 2026-08-08)

Anonymous probes: `capi/` → 302, `capi/projects/uhc-y2/` → 302, `capi/help.html` → 302, `capi/docs/` → 302, but `capi/docs/dashboard.html` → **401**, `/docs/data/` → 401, `/docs/admin/` → 401.

So the site is already closed — but through **two different enforcement layers that disagree**:

| Layer | Covers | On failure | Consequence |
|---|---|---|---|
| nginx `auth_request` → `whoami.php` | `location /` (the portal) | **302** to login | Correct UX |
| Apache `FilesMatch` in five `.htaccess` files | named files under `/docs/` | **401** browser dialog-ish | Different UX, and **matches by FILENAME** |

**That filename matching is the actual defect.** A new file or directory under `/docs/` is unprotected until someone remembers to add it — which has nearly leaked data three times (`plan.json`, `/docs/f2/`, `/docs/cases/`). Deny-by-default is the fix, and it is exactly what "no public/private split" buys.

**Three identity stores today:**

| Store | Users | Hash | Used by |
|---|---|---|---|
| `.htpasswd-docs` | 18 | `$apr1$` (MD5) | CAPI console |
| `csweb_f2.f2_users` | 9 | bcrypt-class, app-managed | F2 admin portal |
| CSWeb's own user table | separate | CSWeb-managed | `csweb.asiansocial.org/csweb/` (200 anonymous → its own login) |

Plus **two site builders with independent nav code** — `build_portal.py` (was public) and `portal_shell.py` (gated). That duplication is why an admin link once appeared on the public portal.

## 3. The boundary that must NOT move

"Every user has login credentials" applies to **console operators**. Two populations authenticate differently *by necessity*, and sweeping them in would break live data collection:

- **F2 respondents (healthcare workers)** — self-administer via public tokenised links (`/f/<slug>`, `/e/CODE?k=`). They are survey subjects, not users. Forcing a login destroys response rates and the self-administration design. **Stays tokenised.**
- **CSEntry devices** — sync with CSWeb credentials over the sync API, not cookies. `capi.asiansocial.org.conf:16` already says *"NO auth_request here: CSEntry cannot do cookie sign-in"*. **Stays as-is**, and must not be touched during pretest.

The plan therefore secures the **console**, and states this boundary explicitly so nobody implements it literally and breaks fieldwork.

## 4. Target architecture

**One identity provider · one enforcement point · deny by default.**

```
                    ┌─────────────────────────────┐
  browser ────────► │ nginx  (single front door)  │
                    │  auth_request  →  /authz    │──► auth service
                    │  401/302 ⇒ login page       │    (identity + RBAC
                    └──────────────┬──────────────┘     + sessions + audit)
                                   │ X-User, X-Roles          │
                     ┌─────────────▼─────────────┐            ▼
                     │ static console (generated)│      MySQL: users,
                     │  /  /docs/  /projects/    │      roles, sessions,
                     └───────────────────────────┘      audit
```

- **Identity provider**: a single auth service holding users, roles, sessions and audit. **Corrected 2026-08-08:** an earlier draft said "extend the F2 admin service, on the same MySQL" — that was wrong. F2's identity runs in a **Cloudflare Worker** over **Google Sheets via Apps Script**, not on this box. Copy F2's *model* (permission keys, `role_version`, per-token + per-user revocation, `password_must_change` gating) but host the store **on the VPS in MySQL**, so a console serving respondent PII does not depend on a spreadsheet behind two external services. See `capi-console-vs-f2-admin-options` for the fork.
- **Enforcement**: nginx `auth_request` at the **vhost root**, covering `/` *and* `/docs/`. One layer, one behaviour, deny-by-default.
- **Delete every `FilesMatch` tier** in `/docs/`. This is the change that ends the filename trap permanently.
- **Static stays static.** Pages are still generated files; the shell calls `/me` to render nav for the caller's roles. Hiding a link is cosmetic — the edge still enforces.
- **Authorization is a server-side path → permission map**, not link-hiding.

### Failure mode to design for
If the auth service is down, `auth_request` fails closed and everyone is locked out. Required before cutover: `error_page` → maintenance page, a short `auth_request` cache, and a documented **break-glass vhost** using the existing `.htpasswd` so the box is never unreachable.

## 5. The role model

Five roles. Permissions are resource-verb, not page names, so a new page inherits a rule instead of inventing one.

| Permission | Covers |
|---|---|
| `monitoring.view` | Sync Dashboard, Map, sync feed/alerts |
| `case.view` | Respondent-level case detail (F1/F3/F4/F2 viewers) |
| `data.export` | Data room, CSV/SPSS/Stata/R, codebook, downloads |
| `tabulations.view` | Tabulation catalog + generated tables |
| `admin.users` | Create/disable users, assign roles, reset passwords |
| `admin.system` | Alerts config, targets control, activities registry, deploys |
| `audit.view` | Access + change audit trail |

| Role | monitoring | case | export | tabulations | admin.users | admin.system | audit |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **Owner** (Carl) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Programme Admin** (ASPSI) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Analyst** | ✓ | ✓ | ✓ | ✓ | — | — | — |
| **Field Supervisor** | ✓ | ✓ | — | ✓ | — | — | — |
| **Client Viewer** (DOH) | ✓ | — | — | ✓ | — | — | — |

Notes:
- **Field Supervisor keeps `case.view`** — your 2026-07-30 decision, and they already hold equivalent access on the F2 portal. They do **not** get bulk `data.export`: reading one case for QC differs from taking the whole microdata set.
- **Client Viewer** exists so DOH can be given real access instead of screenshots, without handing over respondent-level detail.
- **Owner vs Programme Admin** are identical in permissions today; they are separate so a future "Carl can deploy, ASPSI cannot" split needs no re-modelling. Keep both, document the intent.

### Path → permission map (the authoritative ACL)

| Path | Permission |
|---|---|
| `/`, `/projects/**`, `/help.html` | any authenticated |
| `/docs/dashboard.html`, `/docs/map.html`, `/docs/sync-feed.json`, `/docs/plan.json` | `monitoring.view` |
| `/docs/case.html`, `/docs/f2-case.html`, `/docs/cases/**`, `/docs/f2/**` | `case.view` |
| `/docs/data/**` | `data.export` |
| `/projects/uhc-y2/tabulations/**` | `tabulations.view` |
| `/docs/admin/**` | `admin.system` |
| `/docs/admin/users**` | `admin.users` |
| **anything else under the vhost** | **deny** |

That last row is the whole point.

## 6. Credential & session standards (ASVS-aligned)

- **Hashing**: bcrypt (cost ≥ 10) or argon2id. Retires `$apr1$` MD5.
- **Password policy**: minimum **12 characters**, no composition rules, screened against a breached-password list. (ASVS 2.1 — length over complexity; the current rule is 8 and nothing else.)
- **First login**: `password_must_change` **enforced**, not merely stored. Today it is `0` on all nine F2 users including three who have never logged in — which is how `100%SetupMe!` stayed live on `carl_admin`.
- **MFA (TOTP)**: required for `admin.users` / `admin.system` / `data.export`; optional for view-only roles. Added once in the auth service, covering console *and* F2 portal.
- **Sessions**: server-side, revocable, idle timeout 60 min, absolute 12 h, rotate ID on login, `HttpOnly` + `Secure` + `SameSite=Lax`. Logout must actually revoke — today it does not.
- **Throttling**: reuse the F2 service's existing login throttle; lock-out with retry-after.
- **Audit**: authentication events, permission denials, user/role changes, and **respondent-data reads** (the current gap). Cheapest correct source for reads is nginx/Apache access logs, which already carry the authenticated user and path.

## 7. Migration

Each step is independently shippable and reversible.

| # | Step | Verification |
|---|---|---|
| 1 | Seed `console_users`/`console_roles`; import the 18 `.htpasswd` accounts, dedupe the `se_001`/`se-001` variants, assign roles from §5 | Row count matches; every human maps to exactly one role |
| 2 | Force password reset + bcrypt rehash on all accounts; rotate `cplreyes` | No `$apr1$` remains; a test account must change on first login |
| 3 | Build `/authz` in the auth service: returns 200 + `X-User`/`X-Roles`, else 401 | Unit tests per role × per path from the §5 map |
| 4 | Point nginx `auth_request` at `/authz` for `location /` **and** `location /docs/` | Every path in the map returns the expected code for each role |
| 5 | **Delete the `FilesMatch` tiers**; add a deny-all default | A newly created file under `/docs/` is unreachable without being listed anywhere |
| 6 | `/me` endpoint + shell nav renders from roles; retire the second nav codepath | Client Viewer sees no admin link; edge still denies if they type the URL |
| 7 | MFA enrolment for privileged roles | TOTP required on an `admin.*` login |
| 8 | Read auditing into `access_audit` + an admin view | Opening a case appears in the trail within a minute |

**Guardrails throughout:** fieldwork is live — do cutover (steps 4–5) in a quiet window with the break-glass vhost ready; never touch `/csweb/` or the respondent links; the cron generators write to disk, not over HTTP, so they are unaffected — confirm that stays true after step 5.

## 8. What this deliberately does not build

SSO/SAML/OIDC · organisation hierarchies · self-service signup · per-record row-level security · seat management. None serve a ~20-person fixed team on a time-boxed engagement.

## 9. Open decisions

1. **Client Viewer for DOH — do we actually issue those accounts?** It changes who sees the dashboard, and is a client-relationship call, not a technical one.
2. **MFA scope** — privileged roles only (my recommendation), or everyone including seven field supervisors mid-fieldwork?
3. **CSWeb's own login stays separate?** It is a third-party app with its own user table. Unifying it is possible but out of scope here; confirm we accept two logins for anyone who edits cases in CSWeb itself.
4. **Timing** — steps 1–3 are safe now; 4–5 want a quiet window between pretest and rollout.
