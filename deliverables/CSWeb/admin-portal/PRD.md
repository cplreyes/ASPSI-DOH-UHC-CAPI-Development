---
module: CAPI Console Admin Portal
epic: 9 (Data Management and Security) · ties to Epic 4 (Backend/Sync Infrastructure)
task_namespace: E9-ADMIN-NNN
author: Carl Patrick L. Reyes
created: 2026-08-08
status: specified — not started
---

# PRD — CAPI Console Admin Portal

> Produced by a six-specialist review (requirements, backend, frontend, integration, security, QA)
> against the deployed Phase 1 identity provider. Companion documents:
> `DESIGN.md` (technical) · `BACKLOG.md` (tasks) · `../auth/DEPLOY.md` (runbook) ·
> `../capi-console-idp-option-c-plan.md` (architecture decision).

## 1. Problem statement

The console serves respondent-level microdata behind a filename-based Apache gate that cannot revoke a session and records nothing about who read what. The Phase 1 provider that fixes this is **deployed but enforces nothing**, and it cannot be switched on: the existing Users screen writes only to `.htpasswd` / `.htaccess`, so after cutover it would report "disabled" while that account kept working.

This module is the admin surface that makes the provider operable — where ~20 named operators are created, roled, revoked and audited against `console_users`. **Until it exists, cutover is unsafe.** That is the whole justification; everything else in this document is detail.

## 2. Users and jobs

| Role | Job in the portal | Frequency |
|---|---|---|
| `owner` (Carl) | Create/disable accounts, set roles, edit permissions, kill sessions, read audit, break-glass | Daily to cutover, then weekly |
| `programme_admin` (ASPSI) | Onboard/offboard field staff, reset passwords, see who is signed in | Weekly; spikes at rollout |
| `analyst` | Change own password, view own permissions | Rarely |
| `field_supervisor` | Change own password, enrol MFA if required | At onboarding |
| `client_viewer` (DOH) | Change own password; never sees an admin entry point | Once |

## 3. In scope

1. **Users & access** on `console_users` — list, create, disable/enable, force password reset, assign role.
2. **Roles & permissions** — the 5 × 7 matrix, owner-editable, auto-bumping `role_version`.
3. **Sessions** — live list (IP, agent, issued, last seen, expiry); kill one or all.
4. **Audit trail** — filterable by actor / verb / date, including data reads and denials; CSV export.
5. **Self-service** — own password change; the only route open while `must_change = 1`.
6. **Duplicate triage** — the seven `se_001` / `se-001` pairs, with activity evidence shown.
7. **Existing tabs** — Activities, Alerting, Assignment plan — unchanged, gated by `admin.system`.
8. **Cutover safety** — kill-switch on the legacy htpasswd writer; break-glass exempt from bulk actions.
9. **MFA (TOTP)** — enrolment and owner-initiated reset.
10. **`/me`-driven navigation**, retiring the second nav codepath.

## 4. Explicitly out of scope

| Excluded | Why |
|---|---|
| F2 respondent accounts | Survey subjects, not users. Tokenised `/f/<slug>` and `/e/CODE?k=` links stay. A login destroys self-administration. |
| CSEntry sync credentials | Bearer-based; cookies would stop field collection outright. |
| CSWeb's own user table | Third-party app with its own store. Two logins accepted through pretest. |
| SSO / OIDC / signup / org hierarchies / billing | 20 fixed operators, engagement ends ~Aug 2026. |
| F2 admin user management | Phase 2. Phase 1 must not touch F2's store. |
| Row-level or geographic scoping | Roles gate surfaces, not regions. |

## 5. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Users list reads `console_users`; rows show role, status, last login, hash algorithm, live session count | must |
| FR-02 | Create writes user and role in one transaction, argon2id, `must_change = 1` | must |
| FR-03 | Disable sets `status='disabled'` **and** revokes that user's sessions in the same transaction | must |
| FR-04 | No admin write path touches `.htpasswd` or `.htaccess` after cutover | must |
| FR-05 | A write that does not persist reports failure. No success is ever shown for a no-op | must |
| FR-06 | Role reassignment revokes that user's sessions; a permission edit bumps `version`, killing sessions holding it | must |
| FR-07 | The last `owner`, and the break-glass account, cannot be deleted, demoted or disabled | must |
| FR-08 | Killing one session, or all of a user's, makes those cookies 401 on next request | must |
| FR-09 | Audit records login, login.fail, logout, perm.deny, user/role changes and case reads — with actor, time, IP, target | must |
| FR-10 | Audit is append-only, filterable by actor/verb/date, CSV-exportable under `audit.view` | must |
| FR-11 | Admin password reset sets `must_change = 1` and revokes that user's sessions | must |
| FR-12 | While `must_change = 1`, only the password route and PUBLIC routes resolve; everything else redirects | must |
| FR-13 | Nav renders from `/docs/idp/me`; without `admin.users` no Users tab appears **and** the URL 403s | must |
| FR-14 | Every mutating request carries a CSRF token bound to the server-side session | must |
| FR-15 | A voluntary password change requires the current password; waived only when `must_change = 1` | must |
| FR-16 | Passwords ≥ 12 characters, rejected if equal to a seeded default or to the current value | should |
| FR-17 | Usernames differing only by `_`/`-` are grouped with activity evidence; disabling one is confirmed explicitly | should |
| FR-18 | TOTP enrolment for `admin.*` and `data.export` holders; an owner can reset another's TOTP, audited | should |
| FR-19 | Destructive dialogs state the blast radius fetched from the server ("signs out 2 active sessions"), never a guess | should |

## 6. Non-functional requirements

| ID | Requirement | Measured by |
|---|---|---|
| NFR-01 | A provider outage fails closed to a maintenance page and never affects `/csweb/` | Stop the DB: dashboard 503, sync still 200 |
| NFR-02 | Authz subrequest ≤ 15 ms p95; a case-JSON burst must not be one DB round trip per file | Timed calls; queries per page load |
| NFR-03 | Every respondent-data read attributable to a named account within 60 s | Open a case, find its audit row |
| NFR-04 | Audit retained to engagement end + 6 months and included in the nightly dump | Restore the dump, count rows |
| NFR-05 | Break-glass proven working **before** every nginx change | Dated entry in `DEPLOY.md §8` |
| NFR-06 | Cutover rollback ≤ 10 minutes | Timed drill restoring `*.conf.pre-idp-*` |
| NFR-07 | Repeated failed logins lock the account, audited; an owner can clear the lock | Scripted attempts, then clear |
| NFR-08 | Only the SHA-256 of a session token exists at rest | Replay a value dumped from `console_sessions` → 401 |

## 7. Success criteria

The four risk questions from the architecture decision, restated pass/fail, plus two the review added.

| # | Question | Pass condition |
|---|---|---|
| SC-1 | Who can reach respondent data? | One query returns every account's effective permissions, **and** a new unnamed file under `/docs/` 403s for all five roles |
| SC-2 | Can we revoke right now? | Disable-user 401s a captured cookie within 60 s with no restart, **and** no screen reports success while writing to a store nothing reads |
| SC-3 | Who looked at what? | One case view yields one audit row (actor, path, case ID, IP) within 60 s, filterable over 30 days |
| SC-4 | Is a stolen password enough? | `admin.*` and `data.export` logins also require TOTP, and all 18 accounts have cleared `must_change` |
| SC-5 | Does auth ever stop fieldwork? | With the provider stopped, `/csweb/` sync stays 200 and the console shows a maintenance page |
| SC-6 | Can we get back in? | Someone following only `DEPLOY.md §8` restores access in ≤ 10 minutes |

**Today's honest score: 0 of 6.** The provider is built and tested but enforces nothing.

## 8. Open product questions for Carl

Only the ones that change what gets built.

1. **DOH `client_viewer` accounts — issue them for pretest, or keep sending screenshots?** Decides whether the tabulations-only nav variant ships now.
2. **MFA scope — privileged roles only, or all 18 including field supervisors mid-fieldwork?** Decides whether TOTP needs a supervised tablet enrolment flow.
3. **The seven dormant underscore duplicates — disable at cutover, or leave until rollout?** Decides whether FR-17 blocks cutover.
4. **Password reset delivery — a one-time password relayed by the admin, or emailed?** There is no mail transport on the box; email is new scope.
