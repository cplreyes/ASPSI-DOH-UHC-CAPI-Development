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
ROOT_PARENT = "0" * CODE_WIDTH


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
    """
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for parent, code, name in rows:
            assert len(parent) == CODE_WIDTH
            assert len(code) == CODE_WIDTH
            name_trunc = name[:NAME_WIDTH].ljust(NAME_WIDTH)
            fh.write(f"{parent}{code}{name_trunc}\n")


def _load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _pad(s) -> str:
    return str(s).strip().zfill(CODE_WIDTH)


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
