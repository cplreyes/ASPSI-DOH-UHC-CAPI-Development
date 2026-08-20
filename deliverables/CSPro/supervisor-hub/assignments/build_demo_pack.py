#!/usr/bin/env python3
"""Stakeholder demo credentials for the pre-testing RESULTS meeting (2026-08-14).

Throwaway accounts in BOTH field roles -- enumerator and supervisor -- so DOH, ADB
and other reviewers can install the CAPI apps on their own device and walk the
instruments during the meeting. The credentials fill the two blank tables ("For
Survey Enumerators" / "For Field Supervisors") that ASPSI's revised "Quick User
Guide for UHC Survey Year 2 CAPI Tool_1.docx" (2026-08-14) carries under CSEntry
Setup step 6, "enter your assigned username and password".

Writes (all gitignored by explicit path):
  demo-users-enumerator.csv  -> CSWeb Users dashboard bulk import  (role: Field Sync)
  demo-users-supervisor.csv  -> CSWeb Users dashboard bulk import  (role: see below)
  demo-roster-rows.csv       -> rows to MERGE into data/roster/roster-source.csv
  demo-credentials.md        -> the table to paste into the Quick User Guide

Reads (gitignored, optional):
  demo-passwords-override.csv -> username,password rows that take precedence over both
                                 reuse and minting. Added 2026-08-16 when ASPSI came
                                 back with their own recommended credentials for these
                                 accounts; prescribed passwords are still passwords,
                                 so they live in a gitignored input, never in here.

This repo's .gitignore matches exact paths, not `*.csv`, so a new credential file is
TRACKED unless someone adds its line first. See the note there dated 2026-08-14.


A SUPERVISOR LOGIN IS TWO CREDENTIALS IN TWO PLACES
---------------------------------------------------
Layer 1 -- CSWeb account: installs the apps and syncs. Created by importing the CSVs.
Layer 2 -- hub roster: LoginApp/MenuApp gate their role-filtered menu on
           UserRoster.dat, which build_hub_apps.py bakes INSIDE the app package from
           data/roster/roster-source.csv. A reviewer with only layer 1 can install
           the apps and open F1/F3/F4 directly, but LoginApp will refuse them and
           they will never see the supervisor menu (Assign EA / Collect & Relay /
           Review & Reports).

So layer 2 is what makes the SUPERVISOR demo real, and it costs a hub rebuild and
redeploy -- a production change to the field app. demo-roster-rows.csv is emitted
ready to merge, but merging + rebuilding + redeploying is a deliberate decision, not
a side effect of running this script. Enumerator accounts are unaffected either way.


THE TWO CSVs ARE SEPARATE ON PURPOSE
------------------------------------
CSWeb's bulk import rejects the WHOLE batch when one row names a role that does not
exist ("Invalid Role Type", and nothing is created). `Field Sync` is confirmed to
exist on the server; the supervisor role is NOT confirmed from this checkout. Keeping
them in separate files means a wrong supervisor role name costs one failed import
instead of taking the enumerator accounts down with it.


ROLE NAMES -- VERIFY BEFORE IMPORTING
-------------------------------------
CSWeb-User-Management-and-RBAC-Provisioning-Pack.md designs six roles; the server is
only confirmed to have `Field Sync` (created 2026-06-09, and the role the July
pretest enumerators used across F1/F3/F4). Note the pack writes role names in
kebab-case (`field-sync`) but the one actually created is title-case with a space
(`Field Sync`) -- the import matches the role name EXACTLY, so the live spelling wins
over the document's.

The supervisor role matters more than a spelling: per the pack, `supervisor-monitor`
has the `report` dashboard and *NO dictionary sync*, so it cannot install or sync
anything in CSEntry -- it would be the wrong choice here despite the name. The role
that runs the Supervisor App is `supervisor-qa` (report dashboard + dictionary sync).
Set SUPERVISOR_ROLE to whatever the Roles dashboard actually lists.

Worth knowing before handing these out: `supervisor-qa` also grants the `report`
dashboard, i.e. login to the production CSWeb web UI to see coverage/map reports
(counts and geo, not full-PII rows). For a results meeting that is arguably the point
-- but it is a real grant on a live server, so it should be a choice.
"""
from __future__ import annotations
import csv
import secrets
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENUM_CSV = HERE / "demo-users-enumerator.csv"
SUP_CSV = HERE / "demo-users-supervisor.csv"
ROSTER_CSV = HERE / "demo-roster-rows.csv"
CREDS_MD = HERE / "demo-credentials.md"
OVERRIDE_CSV = HERE / "demo-passwords-override.csv"
OUTPUTS = (ENUM_CSV, SUP_CSV, ROSTER_CSV, CREDS_MD)

# Must match an existing CSWeb role name EXACTLY -- see ROLE NAMES above.
ENUMERATOR_ROLE = "Field Sync"      # confirmed to exist
SUPERVISOR_ROLE = "supervisor-qa"   # NOT confirmed -- check the Roles dashboard

# username, first, last, hub role. Usernames are ASPSI's recommended set (2026-08-16),
# replacing the first-cut demoenum*/demosup* names before anything was imported.
#
# THE UNDERSCORES ARE IMPORT-ONLY. CSWeb validates usernames in two different places
# with two different rules (verified against the csweb8.0.1 source):
#   - The dashboard "Add User" form requires ^[a-zA-Z]+[a-zA-Z0-9]*$ (users.twig) --
#     that is what refused `se-test` where `setest` worked. It would refuse these too.
#   - Bulk import (UserValidator.php) only charset-checks usernames SHORTER than 4
#     chars (`strlen < 4 && !ctype_alnum` -- an && where || was surely meant), so any
#     >=4-char name sails through regardless of charset. Login never re-validates.
# So these accounts MUST go in via Users -> Import. Hand-adding one in the dashboard
# will be rejected, and that is expected, not a sign the account is wrong.
# First/last names stay letters-only -- import enforces ctype_alpha on every row.
#
# Three enumerators to two supervisors mirrors who actually reviews what -- most of
# the room wants the interview flow, one or two want the oversight side. Both counts
# are one edit here if the split turns out wrong.
#
# The shared `doh` prefix is load-bearing, not cosmetic. CSWeb records which account
# uploaded each case (cases.last_modified_revision = cspro_sync_history.revision,
# direction='put'), so if a reviewer taps Sync during the demo, every case they made
# is filterable with `username LIKE 'doh%'` -- no guesswork against real pretest
# data. That is the safety net; see DATA HYGIENE in the generated handout. No live
# field account starts with `doh` (field convention is se-NNN / fs-NN / ra-NN).
DEMO_USERS = [
    ("dohse_001", "Doh", "Enumone",   "enumerator"),
    ("dohse_002", "Doh", "Enumtwo",   "enumerator"),
    ("dohse_003", "Doh", "Enumthree", "enumerator"),
    ("dohfs_001", "Doh", "Supone",    "supervisor"),
    ("dohfs_002", "Doh", "Suptwo",    "supervisor"),
]

# Deliberately NOT the `se-00N` / `fs-0N` field accounts. Those passwords are bound to
# data/roster/roster-source.csv and baked into UserRoster.dat, and lending one to a
# reviewer would file demo keystrokes under a real fieldworker's name.

# READABLE BY DESIGN -- two common five-letter nouns, e.g. "mangoriver".
#
# Since 2026-08-16 minting is the FALLBACK: ASPSI prescribes these accounts'
# passwords via demo-passwords-override.csv, and a prescribed password wins over
# both reuse and minting (it is coordinated with ASPSI's own guide and slides, so
# regenerating here must not fork it). Everything below still governs any account
# the override file does not cover.
#
# build_pretest_pack.py mints 10 random chars because those accounts live for the
# duration of fieldwork. These live for one meeting, and the job is different: a
# facilitator reads the password aloud to a room, or projects it, and ten strangers
# type it on unfamiliar tablets. A random string fails that room -- it gets misread,
# retyped, and eventually written on a whiteboard, which is worse than a weak
# password. Two words are unambiguous spoken, all lowercase (no shift key), and land
# on exactly 10 characters, comfortably over CSWeb's hard floor of 8.
#
# The trade is real and is bounded by three things, not by the password's strength:
# the roles carry no bulk export, every case they could upload is filterable by the
# shared `demo` prefix, and they are DELETED the same day. That last one stops being
# housekeeping and becomes the actual control -- these are valid against the
# production server for as long as they exist.
#
# The WORDLIST is safe to commit; the CHOSEN PAIR is not. Never inline the passwords
# themselves here -- this file is tracked, and a secret that reaches git history is
# burned even after deletion (the UserRoster.dat lesson, 2026-07-15). The selection
# is made at run time and only ever written to the gitignored outputs.
WORDS = [
    "mango", "river", "green", "table", "cloud", "stone", "bread", "chair",
    "light", "water", "tiger", "apple", "house", "music", "ocean", "plant",
    "sugar", "lemon", "honey", "zebra",
]


def mint() -> str:
    """Two DIFFERENT words -- a doubled word ("mangomango") reads as a typo and
    invites a reviewer to "correct" it."""
    first = secrets.choice(WORDS)
    second = secrets.choice([w for w in WORDS if w != first])
    return first + second


def existing() -> dict[str, str]:
    """Passwords already issued -> REUSE them.

    Re-running to fix a typo in the guide, or to add a role, must not silently rotate
    credentials already in a reviewer's hands or already imported into CSWeb. Same
    lesson as build_pretest_pack.py: read back what was issued, mint only for new
    rows. Reads BOTH csvs so adding supervisors leaves enumerators untouched.
    """
    out: dict[str, str] = {}
    for path in (ENUM_CSV, SUP_CSV):
        if path.exists():
            with path.open(newline="", encoding="utf-8") as fh:
                for row in csv.reader(fh):
                    if len(row) >= 5 and row[0] and row[4]:
                        out[row[0]] = row[4]
    return out


def override() -> dict[str, str]:
    """ASPSI-prescribed passwords -> highest precedence, --rotate included.

    A prescribed credential is coordinated with ASPSI's own guide and slides;
    neither password reuse nor a rotate may fork it. To actually change one,
    edit demo-passwords-override.csv (or delete the row to fall back to
    reuse/minting)."""
    out: dict[str, str] = {}
    if OVERRIDE_CSV.exists():
        with OVERRIDE_CSV.open(newline="", encoding="utf-8") as fh:
            for row in csv.reader(fh):
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    out[row[0].strip()] = row[1].strip()
    return out


ROTATE = "--rotate" in sys.argv
issued = {} if ROTATE else existing()
prescribed = override()
if prescribed:
    print(f"  {len(prescribed)} password(s) prescribed by demo-passwords-override.csv")
if ROTATE:
    print("  --rotate: minting NEW passwords (prescribed ones are NOT rotated).")
    print("    Anyone already holding a sheet, and any account already imported")
    print("    into CSWeb, is now out of sync.")
elif issued:
    # count only reuse that will actually happen: rows in DEMO_USERS that fall
    # through to an already-issued password (old usernames in the CSVs don't).
    reused = [u for u, _f, _l, _hr in DEMO_USERS
              if u in issued and u not in prescribed]
    if reused:
        print(f"  reusing {len(reused)} already-issued password(s) - NOT rotating")
        print("    (pass --rotate to deliberately mint new ones)")

# Excel holds an exclusive lock on an open .csv. Fail BEFORE writing anything rather
# than part-way through, which would leave the CSVs and the handout disagreeing about
# what the password is -- the worst possible state for a credential pack.
locked = []
for p in OUTPUTS:
    if p.exists():
        try:
            with p.open("a", encoding="utf-8"):
                pass
        except PermissionError:
            locked.append(p.name)
if locked:
    raise SystemExit(
        "REFUSING TO RUN - these outputs are open in another program:\n    "
        + "\n    ".join(locked)
        + "\n\nClose them and re-run. Nothing was written, so the pack is consistent."
    )

creds = [
    {"username": u, "first": f, "last": l, "hub_role": hr,
     "pw": prescribed.get(u) or issued.get(u) or mint()}
    for u, f, l, hr in DEMO_USERS
]
enums = [c for c in creds if c["hub_role"] == "enumerator"]
sups = [c for c in creds if c["hub_role"] == "supervisor"]

# NO HEADER ROW. CSWeb parses a header as a user record ("Invalid Role Type: user
# role", line 1). Headerless + the header-row checkbox UNTICKED removes the ambiguity.
# Column order is fixed by CSWeb: username, first, last, role, password, email, phone.
for path, rows, role in ((ENUM_CSV, enums, ENUMERATOR_ROLE),
                         (SUP_CSV, sups, SUPERVISOR_ROLE)):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        for c in rows:
            w.writerow([c["username"], c["first"], c["last"], role, c["pw"], "", ""])

# Hub roster rows -- MERGE into data/roster/roster-source.csv, do not replace it (it
# holds the live tester roster). Same username AND password as the CSWeb account, per
# the roster's one-password-per-person rule: two different secrets for one person is
# how you get a password written on a tablet case. Header included here because this
# file is merged by a human, not imported by CSWeb.
ROSTER_HEADER = ["username", "password", "role", "operator_id", "cluster", "supervisor_id"]
LEAD_SUP = sups[0]["username"] if sups else ""
with ROSTER_CSV.open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(ROSTER_HEADER)
    for c in creds:
        # enumerators point at the first demo supervisor so the hierarchy resolves;
        # supervisors are top of chain and leave supervisor_id blank.
        sup_id = LEAD_SUP if c["hub_role"] == "enumerator" else ""
        w.writerow([c["username"], c["pw"], c["hub_role"], c["username"], "00000", sup_id])


def table(rows: list[dict]) -> list[str]:
    out = ["| # | Username | Password |", "| --- | --- | --- |"]
    out += [f"| {i} | `{c['username']}` | `{c['pw']}` |" for i, c in enumerate(rows, 1)]
    return out


lines = [
    "# Stakeholder demo credentials — pre-testing results meeting",
    "",
    "Generated by `build_demo_pack.py`. **Never commit this file.**",
    "",
    "Disposable CSWeb accounts in both field roles, for DOH / ADB / other reviewers",
    "to install the CAPI apps and walk the instruments.",
    "",
    "Server URL (Quick User Guide, step 4): `https://csweb.asiansocial.org/csweb/api`",
    "",
    f"## Survey Enumerators ({len(enums)}) — CSWeb role `{ENUMERATOR_ROLE}`",
    "",
    *table(enums),
    "",
    "Installs and syncs from CSEntry. No CSWeb web UI, so no bulk data access.",
    "",
    f"## Field Supervisors ({len(sups)}) — CSWeb role `{SUPERVISOR_ROLE}`",
    "",
    *table(sups),
    "",
    f"> **Confirm `{SUPERVISOR_ROLE}` exists in CSWeb → Roles before importing.**",
    "> The import rejects the *whole* batch if the role name does not match exactly,",
    "> which is why this is a separate file from the enumerator one.",
    ">",
    "> Do **not** substitute `supervisor-monitor`: per the RBAC pack it has no",
    "> dictionary sync, so it cannot install or sync anything in CSEntry. It also",
    "> grants the `report` dashboard — a real login to the production CSWeb web UI",
    "> (coverage and map reports; counts and geo, not full-PII rows).",
    "",
    "## Import — before the meeting",
    "",
    "If the earlier `demoenum*` / `demosup*` accounts (2026-08-14 first cut) were",
    "already imported, **delete them first** — this set supersedes them.",
    "",
    "CSWeb → **Users** → **Import**, header-row checkbox **unticked** (both files are",
    "deliberately headerless):",
    "",
    "1. `demo-users-enumerator.csv`",
    "2. `demo-users-supervisor.csv`",
    "",
    "Then confirm the accounts appear with the expected roles.",
    "",
    "**Import is the only door for these usernames.** The dashboard's *Add User* form",
    "rejects underscores (`^[a-zA-Z]+[a-zA-Z0-9]*$`); bulk import does not. If a",
    "hand-add fails while the import succeeded, nothing is wrong — use Import.",
    "",
    "## Supervisor menu — the extra step, only if you want it",
    "",
    "A CSWeb account alone lets a reviewer install the apps and open F1/F3/F4",
    "directly. It does **not** get them into **LoginApp**, which gates its",
    "role-filtered menu on `UserRoster.dat` baked inside the app package. Without",
    "this step the supervisor accounts are enumerator-equivalent in practice — they",
    "never see Assign EA / Collect & Relay / Review & Reports.",
    "",
    "1. Merge `demo-roster-rows.csv` into `data/roster/roster-source.csv`",
    "   (**merge, don't replace** — that file holds the live tester roster).",
    "2. Re-run `supervisor-hub/build_hub_apps.py` to rebuild `UserRoster.dat`.",
    "3. `stamp_version.py bump HUB`, then redeploy the hub.",
    "",
    "That is a production change to the field app, so it is your call, not a",
    "side effect of generating credentials. The enumerator accounts work either way.",
    "",
    "## After the meeting — delete every demo account",
    "",
    "CSWeb → **Users** → delete all five: `dohse_001` `dohse_002` `dohse_003`",
    "`dohfs_001` `dohfs_002`. This is the control, not",
    "housekeeping. The passwords are deliberately readable so a room full of",
    "reviewers can type them off a slide, which means their strength is not what",
    "protects the server — their short life is.",
    "",
    "If the hub roster step was done, also drop the demo rows from",
    "`roster-source.csv` and rebuild, or the next hub build ships them to the field.",
    "",
    "## Data hygiene",
    "",
    "Reviewers should walk the questionnaires but **not tap Sync** — anything they",
    "upload lands in the production dataset alongside real pretest cases.",
    "",
    "If someone does sync, nothing is lost and nothing needs purging: CSWeb records",
    "the uploading account per case, so every demo case is recoverable with",
    "",
    "```sql",
    "SELECT c.*",
    "  FROM csweb_f3_breakout.cases c",
    "  LEFT JOIN csweb_uhc_y2.cspro_sync_history sh",
    "         ON sh.revision = c.last_modified_revision AND sh.direction = 'put'",
    " WHERE sh.username LIKE 'doh%'",
    "```",
    "",
    "which is why every account shares the `doh` prefix (no field account starts",
    "with it — the field convention is `se-NNN` / `fs-NN` / `ra-NN`). This matches",
    "the cutover runbook's keep-and-filter default rather than a purge.",
]

CREDS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

n_presc = sum(1 for c in creds if c["username"] in prescribed)
print(f"enumerators : {len(enums)}  (role: {ENUMERATOR_ROLE})")
print(f"supervisors : {len(sups)}  (role: {SUPERVISOR_ROLE}  <- VERIFY it exists)")
if n_presc == len(creds):
    print("password    : all prescribed by demo-passwords-override.csv")
else:
    print(f"password    : {n_presc}/{len(creds)} prescribed; rest are two words "
          f"from a {len(WORDS)}-word list, all lowercase")
print()
for p in OUTPUTS:
    print(f"wrote: {p.name}")
print()
print("Supervisor MENU also needs the hub roster merge + rebuild + redeploy")
print("(demo-roster-rows.csv) - see the handout. CSWeb import alone is not enough.")
