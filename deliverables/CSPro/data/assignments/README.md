# Assignments dataset — EA/facility → enumerator plan

**Source of truth: `assignments-source.csv`** (tracked — no credentials). Columns:

```
ea_facility_code,enumerator_id,instrument,target_count,ea_name,cluster
```

One row per EA-facility assignment (`ea_facility_code` = 9-digit facility code;
`enumerator_id` must exist in `../roster/roster-source.csv`).

**Writer:** `supervisor-hub/build_hub_apps.py` reads this CSV and emits
`Assignment.dat` (the supervisor's full lookup), the per-enumerator `AS_<id>.dat`
splits, and the empty `MyAssignment.dat` seed. Single writer — never hand-edit the
`.dat` outputs. Distribution to devices is the B4 Bluetooth "Assign EA" flow.

**Current content:** the UAT Round 6 fixtures (2 teams, Biñan + Los Baños/pretest
facilities). **When ASPSI's real EA plan lands** (per-province facility allocations
from the sampling design), the rows here get replaced — from a spreadsheet, mirror
`../roster/import_roster.py` if a converter is worth it — then rebuild + redeploy
the hub (`stamp_version.py bump HUB`).
