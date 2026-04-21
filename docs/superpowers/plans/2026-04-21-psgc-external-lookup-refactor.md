# PSGC External-Lookup Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move PSGC (43,803 geographic codes) out of the F1/F3/F4 main dictionaries and into a shared set of CSPro external lookup dictionaries, so DCFs shrink from ~17 MB to ~1 MB, a single PSGC source of truth feeds all three forms, and cascading region→province→city→barangay selection becomes possible via `setvalueset()` in CAPI logic.

**Architecture:** Mirror the Popstan Census reference app (`3_Resources/Tools-and-Software/CSPro/Examples 8.0/1 - Data Entry/CAPI Census/`). Four separate external dictionaries (`PSGC_REGION_DICT`, `PSGC_PROVINCE_DICT`, `PSGC_CITY_DICT`, `PSGC_BARANGAY_DICT`) keyed by parent code, each with a repeating record of child (code, name). Main dictionary geographic items keep `length=10` but carry only a minimal placeholder value set (per CSPro 8.0 Users Guide p.188 best-practice #3). A shared `PSGC-Cascade.apc` module built on `loadcase()` + `ValueSet.add()` + `setvalueset()` — included by each form's eventual `.app` — drives the cascade.

**Tech Stack:** Python 3 (generator scripts), CSPro 8.0 (dictionary + lookup-file + logic format), PSA 1Q 2026 PSGC data (already parsed into `deliverables/CSPro/F1/inputs/psgc_*.csv`).

---

## Prerequisites & Context

- **Working directory**: `C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development`. Shell is Windows bash; use forward slashes in paths. Carl works on `main` with frequent auto-commits — no worktree needed.
- **Existing PSGC CSVs** (single source of truth, keep unchanged):
  - `deliverables/CSPro/F1/inputs/psgc_region.csv` — 18 rows, cols `code, name`
  - `deliverables/CSPro/F1/inputs/psgc_province_huc.csv` — 117 rows, cols `code, name, parent_region, type`
  - `deliverables/CSPro/F1/inputs/psgc_city_municipality.csv` — 1,658 rows, cols `code, name, parent_province_huc, parent_region, type`
  - `deliverables/CSPro/F1/inputs/psgc_barangay.csv` — 42,010 rows, cols `code, name, parent_city_municipality, parent_province_huc, parent_region`
- **Reference files to model on** (read-only — do not edit):
  - `3_Resources/Tools-and-Software/CSPro/Examples 8.0/1 - Data Entry/Set Value Set/AreaLookup.dcf` — external dict schema
  - `3_Resources/Tools-and-Software/CSPro/Examples 8.0/1 - Data Entry/Set Value Set/arealookup.dat` — fixed-width text lookup data format
  - `3_Resources/Tools-and-Software/CSPro/Examples 8.0/1 - Data Entry/Set Value Set/Setvalueset example.ent.apc` — cascade logic pattern
- **No pytest in project** (per memory `reference_lint_stack`). Verification is done via shape-check Python one-liners invoked inline.
- **Forward-only sign-off**: commit at the end of every task. Bugs found later loop back to the source doc (the `generate_*.py` or the builder), not hand-edits in the DCF.

## File Structure

```
deliverables/CSPro/
├── cspro_helpers.py                  (modify: _psgc_fields, build_geo_id)
├── export_dcf_to_xlsx.py             (no change)
├── shared/                           (NEW)
│   ├── build_psgc_lookups.py         (NEW: generator — reads F1/inputs/psgc_*.csv, writes 4 .dcf + 4 .dat)
│   ├── psgc_region.dcf               (NEW: lookup dict — ID parent=root, repeating record of regions)
│   ├── psgc_region.dat               (NEW: fixed-width lookup data)
│   ├── psgc_province.dcf             (NEW)
│   ├── psgc_province.dat             (NEW)
│   ├── psgc_city.dcf                 (NEW)
│   ├── psgc_city.dat                 (NEW)
│   ├── psgc_barangay.dcf             (NEW)
│   ├── psgc_barangay.dat             (NEW)
│   └── PSGC-Cascade.apc              (NEW: reusable CSPro logic module — onfocus handlers)
├── F1/
│   ├── generate_dcf.py               (modify: delete local build_geographic_id; use shared build_geo_id)
│   ├── FacilityHeadSurvey.dcf        (regenerate — drops from 17 MB to ~1 MB)
│   └── FacilityHeadSurvey - Data Dictionary and Value Sets.xlsx  (re-export)
├── F3/
│   ├── generate_dcf.py               (modify: delete local PSGC loading; use shared build_geo_id)
│   ├── PatientSurvey.dcf             (regenerate)
│   └── PatientSurvey - Data Dictionary and Value Sets.xlsx       (re-export)
└── F4/
    ├── generate_dcf.py               (modify: delete local PSGC loading; use shared build_geo_id)
    ├── HouseholdSurvey.dcf           (regenerate)
    └── HouseholdSurvey - Data Dictionary and Value Sets.xlsx     (re-export)

wiki/concepts/PSGC Value Sets.md      (update: document external-lookup architecture)
index.md                              (update: list new shared/ files)
log.md                                (update: append refactor entry)
~/.claude/projects/.../memory/project_aspsi_psgc_value_sets.md   (update: external-dict approach)
```

### Schema: PSGC external dictionaries

Each of the four dicts follows the Popstan `AREA_DICT` pattern — a single ID item (the parent code), a single repeating record of child entries. Fixed-width text data; one case per parent.

| Dict | ID item | ID length | Record | Items | Max occurrences |
|---|---|---|---|---|---|
| `PSGC_REGION_DICT` | `R_PARENT_CODE` | 10 | `PSGC_REGION_REC` | `R_CODE` (num 10), `R_NAME` (alpha 80) | 20 (18 regions) |
| `PSGC_PROVINCE_DICT` | `P_PARENT_REGION` | 10 | `PSGC_PROVINCE_REC` | `P_CODE` (num 10), `P_NAME` (alpha 80) | 30 |
| `PSGC_CITY_DICT` | `C_PARENT_PROVINCE` | 10 | `PSGC_CITY_REC` | `C_CODE` (num 10), `C_NAME` (alpha 80) | 60 |
| `PSGC_BARANGAY_DICT` | `B_PARENT_CITY` | 10 | `PSGC_BARANGAY_REC` | `B_CODE` (num 10), `B_NAME` (alpha 80) | 2000 (QC-scale) |

For the region dict, there is no "real" parent — use a synthetic key `0000000000` so the entire region list loads as occurrences of a single case.

---

## Task 1: Build PSGC external-dictionary infrastructure

**Files:**
- Create: `deliverables/CSPro/shared/build_psgc_lookups.py`
- Create (as script output): `deliverables/CSPro/shared/psgc_region.dcf`, `psgc_region.dat`, `psgc_province.dcf`, `psgc_province.dat`, `psgc_city.dcf`, `psgc_city.dat`, `psgc_barangay.dcf`, `psgc_barangay.dat`

- [ ] **Step 1: Create the `shared/` directory**

```bash
mkdir -p "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/shared"
```

- [ ] **Step 2: Write `build_psgc_lookups.py`**

Write to `deliverables/CSPro/shared/build_psgc_lookups.py`:

```python
#!/usr/bin/env python3
"""Build four CSPro external lookup dictionaries + data files from the
PSA-authoritative PSGC CSVs in F1/inputs/.

Each dictionary has:
  - one ID item holding the parent code (10 digits, zero-filled)
  - one repeating record with the child (code, name)

The fixed-width text data file has one line per (parent_code, child) pair.
CSEntry's loadcase() loads every record with a matching parent_code as
repeating occurrences in a single case.

Regions have no real parent; we use the sentinel parent_code 0000000000.

Invocation:
    python deliverables/CSPro/shared/build_psgc_lookups.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PSGC_CSV_DIR = HERE.parent / "F1" / "inputs"

CODE_WIDTH = 10
NAME_WIDTH = 80
ROOT_PARENT = "0" * CODE_WIDTH  # sentinel for regions


def _dict_template(dict_name: str, label: str, parent_id_name: str,
                   rec_name: str, rec_label: str,
                   code_item: str, name_item: str,
                   max_occurrences: int) -> dict:
    return {
        "software": "CSPro",
        "version": 8.0,
        "fileType": "dictionary",
        "name": dict_name,
        "labels": [{"text": label}],
        "readOptimization": True,
        "recordType": {"start": 0, "length": 0},
        "defaults": {"decimalMark": True, "zeroFill": True},
        "relativePositions": True,
        "levels": [{
            "name": f"{dict_name}_LEVEL",
            "labels": [{"text": f"{label} Level"}],
            "ids": {
                "items": [{
                    "name": parent_id_name,
                    "labels": [{"text": "Parent code"}],
                    "contentType": "numeric",
                    "start": 1,
                    "length": CODE_WIDTH,
                    "zeroFill": True,
                }],
            },
            "records": [{
                "name": rec_name,
                "labels": [{"text": rec_label}],
                "occurrences": {"required": True, "maximum": max_occurrences},
                "items": [
                    {
                        "name": code_item,
                        "labels": [{"text": "Code"}],
                        "contentType": "numeric",
                        "length": CODE_WIDTH,
                        "zeroFill": True,
                    },
                    {
                        "name": name_item,
                        "labels": [{"text": "Name"}],
                        "contentType": "alpha",
                        "length": NAME_WIDTH,
                    },
                ],
            }],
        }],
    }


def _write_dict(path: Path, template: dict) -> None:
    path.write_text(json.dumps(template, indent=2), encoding="utf-8")


def _write_data(path: Path, rows: list[tuple[str, str, str]]) -> None:
    """rows: list of (parent_code, child_code, child_name). Fixed-width text.

    Line format: <parent(10)><child_code(10)><child_name(80 left-justified)>
    CSEntry reads this as ID=parent, then each matching line is one occurrence
    of the repeating record (first 10 char of record body = child_code, next
    80 = child_name).
    """
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for parent, code, name in rows:
            assert len(parent) == CODE_WIDTH
            assert len(code) == CODE_WIDTH
            name_trunc = name[:NAME_WIDTH].ljust(NAME_WIDTH)
            fh.write(f"{parent}{code}{name_trunc}\n")


def _load_csv(path: Path, code_col: str = "code", name_col: str = "name",
              parent_col: str | None = None) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _pad(s: str) -> str:
    s = str(s).strip()
    return s.zfill(CODE_WIDTH)


def build_regions() -> None:
    template = _dict_template(
        "PSGC_REGION_DICT", "PSGC Region Lookup",
        "R_PARENT_CODE", "PSGC_REGION_REC", "Region record",
        "R_CODE", "R_NAME", max_occurrences=20,
    )
    _write_dict(HERE / "psgc_region.dcf", template)

    rows = []
    for r in _load_csv(PSGC_CSV_DIR / "psgc_region.csv"):
        rows.append((ROOT_PARENT, _pad(r["code"]), r["name"]))
    _write_data(HERE / "psgc_region.dat", rows)
    print(f"PSGC regions: {len(rows)} rows")


def build_provinces() -> None:
    template = _dict_template(
        "PSGC_PROVINCE_DICT", "PSGC Province / HUC Lookup",
        "P_PARENT_REGION", "PSGC_PROVINCE_REC", "Province / HUC record",
        "P_CODE", "P_NAME", max_occurrences=30,
    )
    _write_dict(HERE / "psgc_province.dcf", template)

    rows = []
    for r in _load_csv(PSGC_CSV_DIR / "psgc_province_huc.csv"):
        rows.append((_pad(r["parent_region"]), _pad(r["code"]), r["name"]))
    _write_data(HERE / "psgc_province.dat", rows)
    print(f"PSGC provinces: {len(rows)} rows")


def build_cities() -> None:
    template = _dict_template(
        "PSGC_CITY_DICT", "PSGC City / Municipality Lookup",
        "C_PARENT_PROVINCE", "PSGC_CITY_REC", "City / Municipality record",
        "C_CODE", "C_NAME", max_occurrences=60,
    )
    _write_dict(HERE / "psgc_city.dcf", template)

    rows = []
    for r in _load_csv(PSGC_CSV_DIR / "psgc_city_municipality.csv"):
        rows.append((_pad(r["parent_province_huc"]), _pad(r["code"]), r["name"]))
    _write_data(HERE / "psgc_city.dat", rows)
    print(f"PSGC cities/municipalities: {len(rows)} rows")


def build_barangays() -> None:
    template = _dict_template(
        "PSGC_BARANGAY_DICT", "PSGC Barangay Lookup",
        "B_PARENT_CITY", "PSGC_BARANGAY_REC", "Barangay record",
        "B_CODE", "B_NAME", max_occurrences=2000,
    )
    _write_dict(HERE / "psgc_barangay.dcf", template)

    rows = []
    for r in _load_csv(PSGC_CSV_DIR / "psgc_barangay.csv"):
        rows.append((_pad(r["parent_city_municipality"]), _pad(r["code"]), r["name"]))
    _write_data(HERE / "psgc_barangay.dat", rows)
    print(f"PSGC barangays: {len(rows)} rows")


def main() -> None:
    build_regions()
    build_provinces()
    build_cities()
    build_barangays()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the builder**

```bash
python "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/shared/build_psgc_lookups.py"
```

Expected output:
```
PSGC regions: 18 rows
PSGC provinces: 117 rows
PSGC cities/municipalities: 1658 rows
PSGC barangays: 42010 rows
```

- [ ] **Step 4: Verify output files exist with expected sizes**

```bash
ls -la "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/shared/"
```

Expected: 4 `.dcf` files (each ~800 bytes), 4 `.dat` files (region ~2 KB, province ~12 KB, city ~166 KB, barangay ~4.2 MB).

- [ ] **Step 5: Shape-check the barangay data file**

```bash
python -c "
from pathlib import Path
p = Path('C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/shared/psgc_barangay.dat')
lines = p.read_text(encoding='utf-8').splitlines()
print(f'Lines: {len(lines)}')
print(f'First line length: {len(lines[0])} (expected 100)')
print(f'First line: {lines[0]!r}')
parents = {line[:10] for line in lines}
print(f'Unique parent cities: {len(parents)} (expected ~1658)')
max_per_city = max(sum(1 for l in lines if l.startswith(p)) for p in list(parents)[:20])
print(f'Max occurrences in first 20 cities: {max_per_city} (must be <= 2000)')
"
```

Expected: Lines: 42010; First line length: 100; Unique parent cities around 1600; max occurrences ≤ 2000.

- [ ] **Step 6: Commit**

```bash
git add "deliverables/CSPro/shared/"
git commit -m "Add PSGC external lookup dictionaries + builder

Mirrors the Popstan Census reference app's AREA_DICT pattern. Four
external dicts (region/province/city/barangay), each keyed by parent
code with a repeating child-code-and-name record. Builder reads the
existing F1/inputs/psgc_*.csv files (PSA 1Q 2026 authoritative) and
emits fixed-width .dat files that CSEntry can loadcase() at runtime."
```

---

## Task 2: Refactor `cspro_helpers._psgc_fields()` to drop baked value sets

**Files:**
- Modify: `deliverables/CSPro/cspro_helpers.py:263-280`

**Rationale:** The shared `_psgc_fields()` is currently out of sync with F1/F3/F4's local overrides (it has length 2/3/4/4 with no VSes; the forms override with length=10 + wired VSes). Bring it in line with the new external-lookup model: `length=10`, zero-filled, and a 1-entry *generic* primary value set so case-tree labels render correctly per Users Guide p.188 best-practice #3. Remove the stale docstring mentioning "ASPSI lookup tables are pending."

- [ ] **Step 1: Read the current implementation of `_psgc_fields` to confirm offsets**

```bash
grep -n "_psgc_fields\|def build_geo_id" "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/cspro_helpers.py"
```

- [ ] **Step 2: Replace `_psgc_fields()` definition**

Use `Edit` tool on `deliverables/CSPro/cspro_helpers.py`:

Replace:
```python
def _psgc_fields():
    """Return the four standard PSGC geographic code items.

    Lengths follow PSGC conventions (region 2, province 3, city 4, barangay 4).
    All are zero-filled numerics with no value sets attached (ASPSI lookup tables
    are pending — add valueSets once the authoritative code lists arrive).

    Returns
    -------
    list of dict
        [REGION, PROVINCE_HUC, CITY_MUNICIPALITY, BARANGAY]
    """
    return [
        numeric("REGION",            "Region",               length=2, zero_fill=True),
        numeric("PROVINCE_HUC",      "Province / HUC",       length=3, zero_fill=True),
        numeric("CITY_MUNICIPALITY", "City / Municipality",  length=4, zero_fill=True),
        numeric("BARANGAY",          "Barangay",             length=4, zero_fill=True),
    ]
```

With:
```python
def _psgc_fields(prefix=""):
    """Return the four standard PSGC geographic code items.

    Items are length=10 numeric zero-filled, holding the full 10-digit PSA
    PSGC code. Value sets are deliberately NOT baked in — the four PSGC
    external lookup dictionaries (shared/psgc_*.dcf) + PSGC-Cascade.apc
    logic populate dynamic value sets at runtime via setvalueset().

    A one-entry generic placeholder value set is attached so CSPro Designer
    shows a label in the case tree (per CSPro 8.0 Users Guide p.188 best-
    practice #3 for cascading items).

    Parameters
    ----------
    prefix : str
        Optional prefix to disambiguate when two PSGC blocks live in the
        same record (e.g. facility vs patient-home). Names become
        {prefix}REGION, {prefix}PROVINCE_HUC, etc.

    Returns
    -------
    list of dict
        [REGION, PROVINCE_HUC, CITY_MUNICIPALITY, BARANGAY]
    """
    placeholder = [("(set at runtime)", "0" * 10)]
    return [
        numeric(f"{prefix}REGION",            "Region",               length=10, zero_fill=True, value_set_options=placeholder),
        numeric(f"{prefix}PROVINCE_HUC",      "Province / HUC",       length=10, zero_fill=True, value_set_options=placeholder),
        numeric(f"{prefix}CITY_MUNICIPALITY", "City / Municipality",  length=10, zero_fill=True, value_set_options=placeholder),
        numeric(f"{prefix}BARANGAY",          "Barangay",             length=10, zero_fill=True, value_set_options=placeholder),
    ]
```

- [ ] **Step 3: Update the `facility_and_patient` branch of `build_geo_id` to use the prefix form**

In `build_geo_id()`, replace the inline `patient_psgc = [...]` block around line 329–334 with a call to `_psgc_fields(prefix="P_")`:

Replace:
```python
    elif mode == "facility_and_patient":
        patient_psgc = [
            numeric("P_REGION",            "Patient Home Region",              length=2, zero_fill=True),
            numeric("P_PROVINCE_HUC",      "Patient Home Province / HUC",      length=3, zero_fill=True),
            numeric("P_CITY_MUNICIPALITY", "Patient Home City / Municipality",  length=4, zero_fill=True),
            numeric("P_BARANGAY",          "Patient Home Barangay",             length=4, zero_fill=True),
        ]
```

With:
```python
    elif mode == "facility_and_patient":
        patient_psgc = _psgc_fields(prefix="P_")
        for it in patient_psgc:
            it["labels"][0]["text"] = "Patient Home " + it["labels"][0]["text"]
```

- [ ] **Step 4: Verify the module still imports cleanly**

```bash
python -c "
import sys
sys.path.insert(0, 'C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro')
from cspro_helpers import _psgc_fields, build_geo_id
for it in _psgc_fields():
    print(f'{it[\"name\"]:20s} len={it[\"length\"]} vs_entries={len((it.get(\"valueSets\") or [{}])[0].get(\"values\") or [])}')
print('---')
rec = build_geo_id('facility_and_patient')
for it in rec['items']:
    if 'REGION' in it['name'] or 'BARANGAY' in it['name']:
        print(f'{it[\"name\"]:20s} len={it[\"length\"]}')
"
```

Expected output:
```
REGION               len=10 vs_entries=1
PROVINCE_HUC         len=10 vs_entries=1
CITY_MUNICIPALITY    len=10 vs_entries=1
BARANGAY             len=10 vs_entries=1
---
REGION               len=10
BARANGAY             len=10
P_REGION             len=10
P_BARANGAY           len=10
```

- [ ] **Step 5: Commit**

```bash
git add "deliverables/CSPro/cspro_helpers.py"
git commit -m "cspro_helpers: length=10 PSGC fields with placeholder value sets

Aligns _psgc_fields() with the external-lookup architecture. Drops the
stale 'ASPSI pending' docstring. Adds a prefix parameter so the
facility_and_patient branch of build_geo_id() can reuse the same
builder for P_ prefixed patient-home fields."
```

---

## Task 3: Reconnect F1 to shared helper; regenerate F1 DCF

**Files:**
- Modify: `deliverables/CSPro/F1/generate_dcf.py:38-143` (delete local `build_geographic_id`, import `build_geo_id`, call it)
- Regenerate: `deliverables/CSPro/F1/FacilityHeadSurvey.dcf`

- [ ] **Step 1: Capture baseline item count for the regression check**

```bash
python -c "
import json
with open('C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F1/FacilityHeadSurvey.dcf', encoding='utf-8') as f:
    d = json.load(f)
n_items = sum(len(r['items']) for lvl in d['levels'] for r in lvl['records'])
n_records = sum(len(lvl['records']) for lvl in d['levels'])
print(f'records={n_records} items={n_items}')
"
```

Expected: `records=11 items=655`. Record this number; the regenerated DCF must match.

- [ ] **Step 2: Remove the local `build_geographic_id()` function from F1/generate_dcf.py**

Open `deliverables/CSPro/F1/generate_dcf.py`. Remove lines 118–143 (the entire local `def build_geographic_id()` block). Remove `load_psgc_value_set` from the import on line 38 (it's no longer used in this file).

- [ ] **Step 3: Wire the shared helper at the call site**

Find the line in F1/generate_dcf.py where `build_geographic_id()` is invoked (in the record assembly list for the main dictionary) and replace with `build_geo_id("facility")`. Confirm no other references to the removed function remain:

```bash
grep -n "build_geographic_id\|load_psgc_value_set" "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F1/generate_dcf.py"
```

Expected: no matches. If any remain, delete/replace them.

- [ ] **Step 4: Also add `build_geo_id` to the cspro_helpers import line if not already present**

Check imports in `F1/generate_dcf.py`:

```bash
grep -n "from cspro_helpers" "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F1/generate_dcf.py"
```

If `build_geo_id` isn't in the import list, add it.

- [ ] **Step 5: Regenerate F1 DCF**

```bash
python "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F1/generate_dcf.py"
```

- [ ] **Step 6: Shape-check regenerated DCF**

```bash
python -c "
import json, os
p = 'C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F1/FacilityHeadSurvey.dcf'
size_mb = os.path.getsize(p) / 1024 / 1024
with open(p, encoding='utf-8') as f:
    d = json.load(f)
n_items = sum(len(r['items']) for lvl in d['levels'] for r in lvl['records'])
n_records = sum(len(lvl['records']) for lvl in d['levels'])
geo_rec = next(r for lvl in d['levels'] for r in lvl['records'] if 'GEOGRAPHIC' in r['name'])
for it in geo_rec['items']:
    vs = it.get('valueSets') or []
    nvs = sum(len(v.get('values') or []) for v in vs)
    if it['name'] in ('REGION','PROVINCE_HUC','CITY_MUNICIPALITY','BARANGAY'):
        print(f'{it[\"name\"]:20s} len={it[\"length\"]} vs_entries={nvs}')
print(f'records={n_records} items={n_items} size={size_mb:.2f} MB')
"
```

Expected:
- Each of `REGION`, `PROVINCE_HUC`, `CITY_MUNICIPALITY`, `BARANGAY` has `len=10 vs_entries=1`.
- `records=11 items=655` (unchanged from baseline).
- `size` drops from ~17 MB to ~1 MB.

- [ ] **Step 7: Commit**

```bash
git add "deliverables/CSPro/F1/generate_dcf.py" "deliverables/CSPro/F1/FacilityHeadSurvey.dcf"
git commit -m "F1: use shared build_geo_id; PSGC moves to external lookup

Removes local build_geographic_id() that baked 43,803 PSGC value-set
entries into the main dictionary. F1 now uses the shared
cspro_helpers.build_geo_id(mode='facility') and relies on
shared/psgc_*.dcf external lookups plus PSGC-Cascade.apc logic at
runtime. Dictionary shrinks from 17.2 MB to ~1 MB; item/record count
unchanged (11 records, 655 items)."
```

---

## Task 4: Reconnect F3 to shared helper; regenerate F3 DCF

**Files:**
- Modify: `deliverables/CSPro/F3/generate_dcf.py:22-67` (delete local PSGC loading, use `build_geo_id("facility_and_patient")`)
- Regenerate: `deliverables/CSPro/F3/PatientSurvey.dcf`

- [ ] **Step 1: Capture baseline**

```bash
python -c "
import json
with open('C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F3/PatientSurvey.dcf', encoding='utf-8') as f:
    d = json.load(f)
n_items = sum(len(r['items']) for lvl in d['levels'] for r in lvl['records'])
n_records = sum(len(lvl['records']) for lvl in d['levels'])
print(f'records={n_records} items={n_items}')
"
```

Record the output as the target.

- [ ] **Step 2: Remove local PSGC loading and geo-record override**

Open `deliverables/CSPro/F3/generate_dcf.py`. Find the block starting at the `load_psgc_value_set` calls (around line 51). Delete:
- The four `*_options = load_psgc_value_set(...)` assignments
- The local geographic record construction that uses those options
- `load_psgc_value_set` from the import line 22

At the call site for the geographic record in the main records list, replace with `build_geo_id("facility_and_patient")`. Verify `build_geo_id` is already in imports (per the grep earlier, it is).

- [ ] **Step 3: Verify no stale references remain**

```bash
grep -n "load_psgc_value_set\|P_PROVINCE_HUC" "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F3/generate_dcf.py"
```

Expected: no matches (both moved to the shared helper).

- [ ] **Step 4: Regenerate F3 DCF**

```bash
python "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F3/generate_dcf.py"
```

- [ ] **Step 5: Shape-check regenerated F3 DCF**

```bash
python -c "
import json, os
p = 'C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F3/PatientSurvey.dcf'
size_mb = os.path.getsize(p) / 1024 / 1024
with open(p, encoding='utf-8') as f:
    d = json.load(f)
n_items = sum(len(r['items']) for lvl in d['levels'] for r in lvl['records'])
n_records = sum(len(lvl['records']) for lvl in d['levels'])
# F3 has BOTH facility PSGC and P_ patient-home PSGC in the same geo record
geo_rec = next(r for lvl in d['levels'] for r in lvl['records'] if 'GEO' in r['name'])
psgc_items = [it for it in geo_rec['items'] if it['name'].endswith(('REGION','PROVINCE_HUC','CITY_MUNICIPALITY','BARANGAY'))]
for it in psgc_items:
    vs = it.get('valueSets') or []
    nvs = sum(len(v.get('values') or []) for v in vs)
    print(f'{it[\"name\"]:22s} len={it[\"length\"]} vs_entries={nvs}')
print(f'records={n_records} items={n_items} size={size_mb:.2f} MB')
"
```

Expected: 8 PSGC items (4 facility + 4 patient-home), each `len=10 vs_entries=1`. Record and item counts match the baseline captured in Step 1. Size drops from ~33 MB (F3 has two PSGC blocks) to ~1 MB.

- [ ] **Step 6: Commit**

```bash
git add "deliverables/CSPro/F3/generate_dcf.py" "deliverables/CSPro/F3/PatientSurvey.dcf"
git commit -m "F3: use shared build_geo_id; PSGC moves to external lookup

Drops local load_psgc_value_set calls and the inline geographic record
override. Uses cspro_helpers.build_geo_id('facility_and_patient') so
both facility PSGC and patient-home P_ PSGC items inherit the
external-lookup architecture. Item and record counts preserved."
```

---

## Task 5: Reconnect F4 to shared helper; regenerate F4 DCF

**Files:**
- Modify: `deliverables/CSPro/F4/generate_dcf.py:22-60`
- Regenerate: `deliverables/CSPro/F4/HouseholdSurvey.dcf`

- [ ] **Step 1: Capture baseline**

```bash
python -c "
import json
with open('C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F4/HouseholdSurvey.dcf', encoding='utf-8') as f:
    d = json.load(f)
n_items = sum(len(r['items']) for lvl in d['levels'] for r in lvl['records'])
n_records = sum(len(lvl['records']) for lvl in d['levels'])
print(f'records={n_records} items={n_items}')
"
```

- [ ] **Step 2: Remove local PSGC loading**

Open `deliverables/CSPro/F4/generate_dcf.py`. Delete the four `*_options = load_psgc_value_set(...)` calls and the geographic record construction that uses them. Remove `load_psgc_value_set` from the imports at line 22. At the call site, use `build_geo_id("household")`.

- [ ] **Step 3: Verify cleanup**

```bash
grep -n "load_psgc_value_set" "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F4/generate_dcf.py"
```

Expected: no matches.

- [ ] **Step 4: Regenerate F4 DCF**

```bash
python "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F4/generate_dcf.py"
```

- [ ] **Step 5: Shape-check F4**

```bash
python -c "
import json, os
p = 'C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F4/HouseholdSurvey.dcf'
size_mb = os.path.getsize(p) / 1024 / 1024
with open(p, encoding='utf-8') as f:
    d = json.load(f)
n_items = sum(len(r['items']) for lvl in d['levels'] for r in lvl['records'])
n_records = sum(len(lvl['records']) for lvl in d['levels'])
geo_rec = next(r for lvl in d['levels'] for r in lvl['records'] if 'GEO' in r['name'] or 'HOUSEHOLD_GEO' in r['name'])
for it in geo_rec['items']:
    if it['name'] in ('REGION','PROVINCE_HUC','CITY_MUNICIPALITY','BARANGAY'):
        vs = it.get('valueSets') or []
        nvs = sum(len(v.get('values') or []) for v in vs)
        print(f'{it[\"name\"]:20s} len={it[\"length\"]} vs_entries={nvs}')
print(f'records={n_records} items={n_items} size={size_mb:.2f} MB')
"
```

Expected: 4 PSGC items with `len=10 vs_entries=1`; record/item counts unchanged from baseline; size drops from ~17 MB to ~1 MB.

- [ ] **Step 6: Commit**

```bash
git add "deliverables/CSPro/F4/generate_dcf.py" "deliverables/CSPro/F4/HouseholdSurvey.dcf"
git commit -m "F4: use shared build_geo_id; PSGC moves to external lookup

Drops local load_psgc_value_set calls. Household geo record now uses
cspro_helpers.build_geo_id('household'). Item and record counts
preserved; dictionary shrinks from ~17 MB to ~1 MB."
```

---

## Task 6: Write reusable `PSGC-Cascade.apc` logic module

**Files:**
- Create: `deliverables/CSPro/shared/PSGC-Cascade.apc`

**Rationale:** Each F-series `.app` (not yet built — that's the next milestone) will `#include` this module so cascading is implemented once, not three times. `onfocus` (not preproc, per Users Guide p.188 Logic Tip #4) so reverse-navigation preserves value sets.

- [ ] **Step 1: Write the cascade module**

Write to `deliverables/CSPro/shared/PSGC-Cascade.apc`:

```text
{ PSGC Cascade — reusable CSPro logic module.

  Prerequisites:
  - The four PSGC external dictionaries (psgc_region.dcf, psgc_province.dcf,
    psgc_city.dcf, psgc_barangay.dcf) must be inserted in the application.
  - Main dictionary must expose four numeric length-10 items:
        REGION, PROVINCE_HUC, CITY_MUNICIPALITY, BARANGAY
    (or a parallel block prefixed with P_ for patient-home / other secondary
    geo blocks). Prefix-specific variants are separate procs below.

  Pattern mirrors the CSPro 8.0 Set Value Set example (Setvalueset example.ent.apc)
  and the Popstan Census CAPI app. Each handler fires in onfocus so that
  reverse navigation re-populates the value set (Users Guide p.188 Logic Tip #4).
}

PROC GLOBAL

    numeric ROOT_PSGC_PARENT = 0;    { Sentinel for the region-level lookup }


function FillRegionValueSet(numeric targetItem)

    R_PARENT_CODE = ROOT_PSGC_PARENT;
    if loadcase(PSGC_REGION_DICT, R_PARENT_CODE) = 0 then
        errmsg("PSGC region lookup failed — verify psgc_region.dat is deployed");
        exit;
    endif;

    ValueSet vs;
    do varying numeric i = 1 until i > count(PSGC_REGION_DICT.PSGC_REGION_REC)
        vs.add(strip(R_NAME(i)), R_CODE(i));
    enddo;
    setvalueset(targetItem, vs);

end;


function FillProvinceValueSet(numeric targetItem, numeric parentRegion)

    P_PARENT_REGION = parentRegion;
    if loadcase(PSGC_PROVINCE_DICT, P_PARENT_REGION) = 0 then
        ValueSet empty;
        setvalueset(targetItem, empty);
        exit;
    endif;

    ValueSet vs;
    do varying numeric i = 1 until i > count(PSGC_PROVINCE_DICT.PSGC_PROVINCE_REC)
        vs.add(strip(P_NAME(i)), P_CODE(i));
    enddo;
    setvalueset(targetItem, vs);

end;


function FillCityValueSet(numeric targetItem, numeric parentProvince)

    C_PARENT_PROVINCE = parentProvince;
    if loadcase(PSGC_CITY_DICT, C_PARENT_PROVINCE) = 0 then
        ValueSet empty;
        setvalueset(targetItem, empty);
        exit;
    endif;

    ValueSet vs;
    do varying numeric i = 1 until i > count(PSGC_CITY_DICT.PSGC_CITY_REC)
        vs.add(strip(C_NAME(i)), C_CODE(i));
    enddo;
    setvalueset(targetItem, vs);

end;


function FillBarangayValueSet(numeric targetItem, numeric parentCity)

    B_PARENT_CITY = parentCity;
    if loadcase(PSGC_BARANGAY_DICT, B_PARENT_CITY) = 0 then
        ValueSet empty;
        setvalueset(targetItem, empty);
        exit;
    endif;

    ValueSet vs;
    do varying numeric i = 1 until i > count(PSGC_BARANGAY_DICT.PSGC_BARANGAY_REC)
        vs.add(strip(B_NAME(i)), B_CODE(i));
    enddo;
    setvalueset(targetItem, vs);

end;


{ Facility PSGC handlers — attach these to main-dict field onfocus events.
  Usage inside a form's PROC:
      PROC REGION
      onfocus
          FillRegionValueSet(REGION);
      PROC PROVINCE_HUC
      onfocus
          FillProvinceValueSet(PROVINCE_HUC, REGION);
      PROC CITY_MUNICIPALITY
      onfocus
          FillCityValueSet(CITY_MUNICIPALITY, PROVINCE_HUC);
      PROC BARANGAY
      onfocus
          FillBarangayValueSet(BARANGAY, CITY_MUNICIPALITY);
}
```

- [ ] **Step 2: Syntax-validate by visual inspection**

This file is CSPro PROC syntax, not Python — no parser available at project level. Read the file back and verify:
- All `function` blocks have matching `end;`
- Every `do varying` has a matching `enddo`
- Every `if` has a matching `endif`
- Semicolons terminate statements

```bash
cat "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/shared/PSGC-Cascade.apc" | grep -c "^function\|^end;\|^endif;\|^enddo"
```

Expected: a reasonable count — 4 functions, 4 function `end;`, 4 `endif`, 4 `enddo`.

- [ ] **Step 3: Commit**

```bash
git add "deliverables/CSPro/shared/PSGC-Cascade.apc"
git commit -m "Add reusable PSGC cascade logic module

Four public functions (FillRegionValueSet, FillProvinceValueSet,
FillCityValueSet, FillBarangayValueSet) that each F-series .app will
invoke from the corresponding field's onfocus event. onfocus (not
preproc) per CSPro 8.0 Users Guide p.188 Logic Tip #4 — ensures
reverse-navigation re-populates the value set."
```

---

## Task 7: Re-export review xlsx, update wiki and index, update memory

**Files:**
- Regenerate: `deliverables/CSPro/F1/FacilityHeadSurvey - Data Dictionary and Value Sets.xlsx`
- Regenerate: `deliverables/CSPro/F3/PatientSurvey - Data Dictionary and Value Sets.xlsx`
- Regenerate: `deliverables/CSPro/F4/HouseholdSurvey - Data Dictionary and Value Sets.xlsx`
- Modify: `wiki/concepts/PSGC Value Sets.md`
- Modify: `index.md` (under Deliverables > Shared, add shared/ entries)
- Modify: `log.md` (append dated entry)
- Modify: `C:/Users/analy/.claude/projects/C--Users-analy-Documents-analytiflow-1-Projects-ASPSI-DOH-CAPI-CSPro-Development/memory/project_aspsi_psgc_value_sets.md`

- [ ] **Step 1: Re-export all three xlsx review files**

```bash
python "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/export_dcf_to_xlsx.py" --all
```

Expected: three files updated. Each Value Sets sheet drops from ~45k–90k rows to a few hundred rows (no more baked PSGC).

- [ ] **Step 2: Verify xlsx row counts dropped**

```bash
python -c "
import openpyxl
for p in [
    'C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F1/FacilityHeadSurvey - Data Dictionary and Value Sets.xlsx',
    'C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F3/PatientSurvey - Data Dictionary and Value Sets.xlsx',
    'C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F4/HouseholdSurvey - Data Dictionary and Value Sets.xlsx',
]:
    wb = openpyxl.load_workbook(p, read_only=True)
    for n in wb.sheetnames:
        ws = wb[n]
        print(f'{p.rsplit(chr(47),1)[-1]}  {n}: {ws.max_row} rows')
    wb.close()
"
```

Expected: Value Sets row counts drop to low thousands for each file (F3 still a bit higher because it has the patient-home geo block, but the 43k barangay list is gone).

- [ ] **Step 3: Update the PSGC wiki concept page**

Use `Edit` tool on `wiki/concepts/PSGC Value Sets.md` — replace any "wired into F1 DCF" / "baked value set" language with the external-lookup story: "PSGC lives in four external lookup dictionaries at `deliverables/CSPro/shared/psgc_*.dcf`; `PSGC-Cascade.apc` drives cascading region→province→city→barangay selection via `setvalueset()` at runtime."

Append a section "Architecture" that summarizes the four dicts + the logic module + the Popstan reference.

- [ ] **Step 4: Update `index.md`**

In the Deliverables section, under a new "Shared" subsection, list:
- `deliverables/CSPro/shared/build_psgc_lookups.py`
- `deliverables/CSPro/shared/psgc_region.dcf` + `.dat`
- `deliverables/CSPro/shared/psgc_province.dcf` + `.dat`
- `deliverables/CSPro/shared/psgc_city.dcf` + `.dat`
- `deliverables/CSPro/shared/psgc_barangay.dcf` + `.dat`
- `deliverables/CSPro/shared/PSGC-Cascade.apc`

Also update the F1/F3/F4 entries so their item/size numbers reflect the post-refactor state.

- [ ] **Step 5: Append log entry**

Prepend to `log.md` under a new `## 2026-04-21 (PSGC external-lookup refactor)` heading. Summarize the refactor, cite Popstan and Users Guide, note before/after sizes, and link to this plan.

- [ ] **Step 6: Update memory**

Use `Edit` on `C:/Users/analy/.claude/projects/C--Users-analy-Documents-analytiflow-1-Projects-ASPSI-DOH-CAPI-CSPro-Development/memory/project_aspsi_psgc_value_sets.md` — flip the body from "wired into F1 DCF" to "externalized to `shared/psgc_*.dcf` lookups + `PSGC-Cascade.apc`; cascading implemented; dicts shrink 17 MB → 1 MB". Update the description line of the corresponding entry in `MEMORY.md`.

- [ ] **Step 7: Commit**

```bash
git add \
  "deliverables/CSPro/F1/FacilityHeadSurvey - Data Dictionary and Value Sets.xlsx" \
  "deliverables/CSPro/F3/PatientSurvey - Data Dictionary and Value Sets.xlsx" \
  "deliverables/CSPro/F4/HouseholdSurvey - Data Dictionary and Value Sets.xlsx" \
  "wiki/concepts/PSGC Value Sets.md" \
  "index.md" \
  "log.md"
git commit -m "Docs + review xlsx exports for PSGC external-lookup refactor

Wiki concept page updated to describe the four external lookup dicts
and PSGC-Cascade.apc. Index gains a Shared subsection. Log entry
records the refactor with before/after sizes. Review xlsx files
regenerated; value-set sheets drop from 45k-90k rows to low thousands
after the 43,803 PSGC entries moved out of the main dictionaries."
```

Memory updates are stored outside the repo and don't need to be in this commit.

---

## Self-Review

**Spec coverage:**
- External-lookup dicts for 4 PSGC levels → Task 1 creates all four + builder.
- Main DCF items keep length=10 with placeholder VS → Task 2 refactors `_psgc_fields`.
- F1/F3/F4 regenerated, ~1 MB each → Tasks 3/4/5 with shape-check steps.
- Reusable cascade logic → Task 6 emits `PSGC-Cascade.apc` with four public handlers.
- Review xlsx regenerated → Task 7 Step 1/2.
- Wiki / index / log / memory updated → Task 7 Steps 3–6.
- Popstan + Users Guide citations → referenced in Architecture, commit messages, and the .apc header comment.

**Placeholder scan:**
- No "TBD", "TODO", or "fill in details" anywhere in the tasks.
- Every code step shows the code to write.
- Every command shows the expected output.

**Type consistency:**
- `_psgc_fields(prefix="")` signature defined once (Task 2), used in both the `facility` and `facility_and_patient` branches.
- `build_geo_id(mode)` modes `"facility"`, `"facility_and_patient"`, `"household"` used consistently in Tasks 3/4/5.
- External dict names (`PSGC_REGION_DICT` etc.), record names (`PSGC_REGION_REC` etc.), and item names (`R_CODE`/`R_NAME`, `P_CODE`/`P_NAME`, `C_CODE`/`C_NAME`, `B_CODE`/`B_NAME`) are consistent across the builder (Task 1) and the logic module (Task 6). ID item names (`R_PARENT_CODE`, `P_PARENT_REGION`, `C_PARENT_PROVINCE`, `B_PARENT_CITY`) also consistent.

No issues found.
