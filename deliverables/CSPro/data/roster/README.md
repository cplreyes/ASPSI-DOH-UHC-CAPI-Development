# Roster dataset — hub login credentials

**Source of truth: `roster-source.csv`** (GITIGNORED — carries credentials; copy
`roster-source.template.csv` and fill in real rows on a fresh checkout). Columns:

```
username,password,role,operator_id,cluster,supervisor_id
```

- `role` = `enumerator` | `supervisor` (drives the hub's role-filtered menu).
- `supervisor_id` (K3, Khurshid pattern) = the enumerator→supervisor hierarchy;
  blank for supervisors (top of chain).
- Current content: the UAT Round 6 tester roster (2 teams, `uhc26*` typeable
  passwords). These are the hub's LOCAL login gate only — the real security is each
  tester's CSWeb account (see `../../supervisor-hub/config/`, also gitignored).

**Writer:** `supervisor-hub/build_hub_apps.py` reads this CSV and emits
`UserRoster.dat` (fixed-width, plaintext) — the build stays the single writer;
never hand-edit `UserRoster.dat`.

**ASPSI's real roster (K4):** import the delivered spreadsheet with
`py import_roster.py <sheet.xlsx> --map username=<col> ...` → rewrites
roster-source.csv (previous kept as `.bak`) → re-run the hub build → redeploy the
hub (versioned: `stamp_version.py bump HUB`).

**Staged, not built (deliberate):**
- **K1 encryption** — `SecurityOptions`-encrypted roster instead of the plaintext
  `.dat`; requires CSPro-side file creation + on-device verification → slotted for
  the Sep rollout hardening wave, do NOT flip during the pretest freeze.
- **K2 device-bound login** (`getdeviceid()` vs a `DEVICE_ID` column) — ASPSI
  go/no-go once tablets are assigned to named fieldworkers; add the column here
  when called.
