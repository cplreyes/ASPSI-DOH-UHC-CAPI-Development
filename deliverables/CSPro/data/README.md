# data/ — the CAPI fleet's datasets (one pipeline per dataset)

Restructured 2026-07-03 (Option B of the data-layer decision; see
`wiki/analyses/Analysis - DHS Benchmark vs ASPSI CAPI Gap Analysis.md` §6 + the
options diagram). The rule mirrors the code side's generator-first law, applied to
data: **every dataset = source (+ provenance) → build script → outputs at the
consumers' unchanged paths.** Never hand-edit an output; never point a consumer
here — outputs are written where the apps/deploy specs already expect them.

| Dataset | Source (here) | Build | Outputs (unchanged consumer paths) |
|---|---|---|---|
| `psgc/` | PSA PSGC 1Q-2026 publication xlsx (+ 4 parsed CSVs), `PSGC-VERSION.md` | `parse_psgc.py` → `build_psgc_lookups.py` | `../shared/psgc_*.dcf/.dat` (ride every instrument deploy) |
| `roster/` | `roster-source.csv` **(GITIGNORED — credentials)**, template + `import_roster.py` (K4) | `../supervisor-hub/build_hub_apps.py` (single writer) | `../supervisor-hub/UserRoster.dat` |
| `assignments/` | `assignments-source.csv` (tracked; R6 fixtures → real EA plan later) | `../supervisor-hub/build_hub_apps.py` | `../supervisor-hub/Assignment.dat`, `AS_<id>.dat`, `MyAssignment.dat` |
| `facilities/` | `source/DOH UHC Yr2 Health Facility Coding.xlsx` **(gitignored — DOH masterlist)** | `build_facility_lookup.py` | `../F1/facility_lookup.dcf/.dat` (gitignored, bundled) |

Not here (deliberately): `../versions.json` (build versions — already its own
pipeline via `stamp_version.py`); instrument questionnaire content (that's code:
the generators); UAT CSWeb account credentials (`../supervisor-hub/config/`,
gitignored — server-side accounts, not a build input).

Data changes ship like code changes: rebuild → gates → versioned deploy
(`stamp_version.py bump <KEY>`). During a freeze (e.g. pretest gate) sources may
change in-tree, but outputs only redeploy after the gate.
