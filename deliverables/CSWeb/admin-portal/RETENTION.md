---
module: CAPI Console Admin Portal
task: E9-ADMIN-043
created: 2026-08-09
status: in force
---

# Retention schedule — CAPI Console identity data

What the identity provider stores, how long it is kept, what removes it, and
why. Written because "no stated retention" is the first thing an audit finds,
and because two of these tables hold personal data under **RA 10173** that
nothing was ever going to delete.

Enforced nightly by `auth/gc.php` (cron 19:30 UTC / 03:30 Manila), except where
the row says otherwise.

## The tables

| Table | Personal data it holds | Retention | Removed by |
|---|---|---|---|
| `console_users` | username, full name, email, password hash | Life of the engagement. Accounts are **disabled, never deleted** — a hard delete orphans the audit rows that record what the account did | manual, owner decision |
| `console_sessions` | **IP address, user-agent**, timestamps | **30 days after the session dies** (revoked or expired) | `gc.php`, nightly |
| `console_idem` | actor name, request digest | **24 hours** | `gc.php`, nightly |
| `console_audit` | actor, IP, target path, request detail | **Engagement end + 6 months** (NFR-04) | nothing yet — see below |
| `console_roles`, `console_role_perms`, `console_user_roles` | none | life of the engagement | — |
| `console_svc_tokens` | none (SHA-256 of a bearer token) | empty until Phase 2 | — |

## Why sessions are kept 30 days and not longer

A dead session row is useful for exactly one thing: answering "where was this
account signed in from, and when" during an incident. Thirty days covers the
realistic window between something happening and somebody asking. Past that it
is a list of people's IP addresses with no purpose, which is the definition of
data that should not still exist.

Live sessions are untouched by GC — they expire on their own (12-hour ceiling,
60-minute idle) and are removed 30 days after that.

## Why the audit trail is not pruned by this job

Two reasons, and the second is the important one.

1. Its retention is far longer than anything else here: engagement end plus six
   months, so that a question asked after handover can still be answered.
2. **The application cannot delete it.** Since E9-ADMIN-012 the `capi_auth`
   database user holds only `SELECT, INSERT` on `console_audit`. An application
   that can erase its own audit trail does not have one. `gc.php` runs as that
   user and therefore *could not* prune the table even if it tried.

When pruning is eventually needed, create a separate MySQL user with `DELETE`
on `capi_auth.console_audit` alone, run the prune, and drop the user again. Do
not restore the grant to the application.

## Backup, and a finding

NFR-04 requires the audit trail to be in the nightly dump. Verified 2026-08-09
— and it was not:

- `/opt/borg/preBackup.sh` assigned the MySQL root password to a shell variable
  and then invoked `mysqldump ... --user=root --password=` with the value
  **omitted**. mysqldump exited 1045 "Access denied … (using password: NO)"
  every night, and `postBackup.sh` deleted the resulting near-empty file, so
  the failure left no trace.
- Every borg snapshot therefore contained an **empty** SQL dump — not just for
  `capi_auth` but for `csweb_uhc_y2`, `csweb_f2` and every breakout database.
  The only recovery path was borg's copy of the live InnoDB files under
  `/opt/app/lamp/data/mysql`, taken hot with no snapshot.

Fixed by passing the variable that was already there. The dump now produces
~18 MB covering all eight databases, `capi_auth` included with every
`console_*` table. Original saved as `preBackup.sh.pre-fix-*`.

> [!warning] Out of scope, still true
> The MySQL root password sits in plaintext in `/opt/borg/preBackup.sh`, and
> the borg passphrase in `/opt/borg/backup.sh`. Both are elestio-generated and
> predate this work. Not changed here — moving them is a separate decision that
> touches the backup path for the whole estate.

## Data-subject requests

Erasure and export for a *respondent* is a different problem from anything on
this page — respondent data lives in `csweb_*`, not in the identity provider —
and is tracked as **E9-ADMIN-044**. The only respondent-adjacent thing here is
the audit trail's record of *who read* a case, which is data about the operator
rather than the respondent.
