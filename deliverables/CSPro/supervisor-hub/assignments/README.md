# CAPI Assignment Prep — supervisor toolkit

Prepares enumerator assignments for the **Supervisor & Enumerator hub** (F1/F3/F4).
You assign **areas + targets**, not individual respondents (respondent/household
pre-listing is descoped from hub v1; F4 members are rostered inside the interview).

## Files

| File | What it is |
|---|---|
| `pretest-qn-list.csv` | **Verbatim RA source.** Every QN transcribed from the RAs' "Unique Question Number for Pre-testing" file (Los Baños, municipality 040341) — one row per 12-digit key, tagged by facility/barangay + instrument. Immutable record; don't derive from it. |
| `pretest-ea-summary.csv` | EA-level rollup of the above (one row per EA × instrument, with the explicit key range) — the shape that drops into the master. |
| `assignment-master.xlsx` | **Fill this.** One row per (enumerator × EA/facility). README + Assignments + Enumerators sheets. Pre-loaded with the Los Baños pre-test (RA QN list on the R6 roster). `first/last_case_key` carry the RA's exact keys and are **authoritative**. |
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

12 digits = **9-digit EA/facility code (real PSGC)** + **3-digit sequence**.
When `first/last_case_key` are filled (as in the pre-test), those exact keys are emitted
**verbatim** — the RA numbering isn't always 001-based (facility-head keys end `000`;
Brgy. Bayog runs `601..620`). Leave them blank and the generator falls back to
code + `001..target`. A wrong PSGC prefix is hard-rejected on the tablet, so use real codes only.

## Status (be honest with the field team)

- ✅ Bluetooth **case exchange** (Send / Collect) — device-confirmed.
- ⚠️ **Assign EA / Receive Assigned Data** (`syncfile` of `AS_<id>.dat`) — wired, **device-verify pending** on the 2-tablet rig.
- **Recommendation:** for the pretest, use the **printed sheet**; switch to the Bluetooth assign once that leg is device-verified.

Columns map 1:1 to `../Assignment.dcf` (`AS_FACILITY_CODE` / `AS_ENUMERATOR_ID` /
`AS_INSTRUMENT` / `AS_TARGET_COUNT` / `AS_EA_NAME` / `AS_CLUSTER`). See the CAPI
Manual §VI (Getting your assignments) and §XIV (Supervisor-only features).
