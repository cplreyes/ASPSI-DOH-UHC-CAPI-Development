# CAPI Assignment Prep — supervisor toolkit

Prepares enumerator assignments for the **Supervisor & Enumerator hub** (F1/F3/F4).
You assign **areas + targets**, not individual respondents (respondent/household
pre-listing is descoped from hub v1; F4 members are rostered inside the interview).

## Files

| File | What it is |
|---|---|
| `assignment-master.xlsx` | **Fill this.** One row per (enumerator × EA/facility). README + Assignments + Enumerators sheets; derived `first/last_case_key` columns visualise the key range. |
| `build_assignment_template.py` | Rebuilds a blank `assignment-master.xlsx` (generator-first; don't hand-edit structure). |
| `generate_assignments.py` | Reads the filled master → writes `out/`. |
| `out/AS_<id>.dat` | One fixed-width file per enumerator (97-byte records, matches `ASSIGNMENT_DICT`). The hub's **Assign Enumeration Area** serves these over Bluetooth. |
| `out/assignment-sheets.html` | **Printable** case-key sheets — one page per enumerator. The reliable hand-out path: enumerators **type** the 12-digit keys. |
| `out/case-keys.csv` | Every 12-digit key, for QA / CSWeb cross-check. |
| `out/manifest.txt` | Per-enumerator + grand totals + any warnings. |

## Workflow

```
1. Fill assignment-master.xlsx  (Assignments sheet — blue columns)
2. python generate_assignments.py
3. Distribute:
   • print out/assignment-sheets.html  → hand each enumerator their page  (reliable today)
   • OR copy out/AS_<id>.dat into the hub + use "Assign Enumeration Area"  (Bluetooth; device-verify pending)
```

## The case key

12 digits = **9-digit EA/facility code (real PSGC)** + **3-digit sequence** `001..target`.
e.g. EA `040340002`, target 12 → `040340002001 … 040340002012`. A wrong PSGC prefix
is hard-rejected on the tablet, so use real codes only.

## Status (be honest with the field team)

- ✅ Bluetooth **case exchange** (Send / Collect) — device-confirmed.
- ⚠️ **Assign EA / Receive Assigned Data** (`syncfile` of `AS_<id>.dat`) — wired, **device-verify pending** on the 2-tablet rig.
- **Recommendation:** for the pretest, use the **printed sheet**; switch to the Bluetooth assign once that leg is device-verified.

Columns map 1:1 to `../Assignment.dcf` (`AS_FACILITY_CODE` / `AS_ENUMERATOR_ID` /
`AS_INSTRUMENT` / `AS_TARGET_COUNT` / `AS_EA_NAME` / `AS_CLUSTER`). See the CAPI
Manual §VI (Getting your assignments) and §XIV (Supervisor-only features).
