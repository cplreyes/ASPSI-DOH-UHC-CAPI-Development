"""Parse PSA PSGC publication xlsx into 4 CSVs keyed by 10-digit PSGC codes.

Outputs, in this directory:
  psgc_region.csv            code,name
  psgc_province_huc.csv      code,name,parent_region,type
  psgc_city_municipality.csv code,name,parent_province_huc,parent_region,type
  psgc_barangay.csv          code,name,parent_city_municipality,parent_province_huc,parent_region

Hierarchy rules for F-series CAPI value sets:
- REGION           = all "Reg" rows.
- PROVINCE_HUC     = all "Prov" rows + all HUCs (City rows with City Class=HUC)
                     + special level=None rows (e.g. Isabela-not-a-province, Special Geographic Area).
- CITY_MUNICIPALITY = all "City" rows (CC/ICC/HUC), all "Mun", all "SubMun",
                     and the level=None specials (so their barangays have a valid parent).
- BARANGAY         = all "Bgy" rows.

HUCs are duplicated into CITY_MUNICIPALITY too, because their barangays sit directly
beneath them and need a city-level parent. ICCs remain under their geographic province
in PROVINCE_HUC (DOH convention).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import openpyxl

XLSX = Path(__file__).parent / "PSGC-1Q-2026-Publication-Datafile.xlsx"
OUT_DIR = Path(__file__).parent


def main() -> int:
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["PSGC"]
    rows = ws.iter_rows(min_row=2, values_only=True)

    regions: list[dict] = []
    province_hucs: list[dict] = []
    city_muns: list[dict] = []
    barangays: list[dict] = []

    current_region: str | None = None
    current_province_huc: str | None = None
    current_city_mun: str | None = None

    for row in rows:
        psgc, name, _corr, level, _old, city_class = row[0], row[1], row[2], row[3], row[4], row[5]
        if psgc is None:
            continue
        code = str(psgc).zfill(10)
        name = (name or "").strip()

        if level == "Reg":
            current_region = code
            current_province_huc = None
            current_city_mun = None
            regions.append({"code": code, "name": name})

        elif level == "Prov":
            current_province_huc = code
            current_city_mun = None
            province_hucs.append(
                {"code": code, "name": name, "parent_region": current_region, "type": "Prov"}
            )

        elif level == "City":
            cls = (city_class or "").strip()
            if cls == "HUC":
                # HUC sits at province-level AND is the container for its barangays.
                current_province_huc = code
                current_city_mun = code
                province_hucs.append(
                    {"code": code, "name": name, "parent_region": current_region, "type": "HUC"}
                )
                city_muns.append(
                    {
                        "code": code,
                        "name": name,
                        "parent_province_huc": code,
                        "parent_region": current_region,
                        "type": "HUC",
                    }
                )
            else:  # CC or ICC — component of current province
                current_city_mun = code
                city_muns.append(
                    {
                        "code": code,
                        "name": name,
                        "parent_province_huc": current_province_huc,
                        "parent_region": current_region,
                        "type": cls or "City",
                    }
                )

        elif level == "Mun":
            current_city_mun = code
            city_muns.append(
                {
                    "code": code,
                    "name": name,
                    "parent_province_huc": current_province_huc,
                    "parent_region": current_region,
                    "type": "Mun",
                }
            )

        elif level == "SubMun":
            # Manila's districts. Barangays list the SubMun as their city-level parent.
            current_city_mun = code
            city_muns.append(
                {
                    "code": code,
                    "name": name,
                    "parent_province_huc": current_province_huc,
                    "parent_region": current_region,
                    "type": "SubMun",
                }
            )

        elif level == "Bgy":
            barangays.append(
                {
                    "code": code,
                    "name": name,
                    "parent_city_municipality": current_city_mun,
                    "parent_province_huc": current_province_huc,
                    "parent_region": current_region,
                }
            )

        elif level is None:
            # Specials: Isabela City "not a province" (0990100000), Special Geographic Area (1999900000).
            # Treat as PROVINCE_HUC + CITY_MUNICIPALITY so downstream rows chain correctly.
            current_province_huc = code
            current_city_mun = code
            province_hucs.append(
                {"code": code, "name": name, "parent_region": current_region, "type": "Special"}
            )
            city_muns.append(
                {
                    "code": code,
                    "name": name,
                    "parent_province_huc": code,
                    "parent_region": current_region,
                    "type": "Special",
                }
            )

    # Write CSVs (UTF-8, with BOM-free encoding; the F1 generator reads inputs as utf-8)
    _write_csv(OUT_DIR / "psgc_region.csv", ["code", "name"], regions)
    _write_csv(
        OUT_DIR / "psgc_province_huc.csv",
        ["code", "name", "parent_region", "type"],
        province_hucs,
    )
    _write_csv(
        OUT_DIR / "psgc_city_municipality.csv",
        ["code", "name", "parent_province_huc", "parent_region", "type"],
        city_muns,
    )
    _write_csv(
        OUT_DIR / "psgc_barangay.csv",
        ["code", "name", "parent_city_municipality", "parent_province_huc", "parent_region"],
        barangays,
    )

    print(f"Regions:             {len(regions):>6}")
    print(f"Provinces + HUCs:    {len(province_hucs):>6}")
    print(f"Cities + Mun + Sub:  {len(city_muns):>6}")
    print(f"Barangays:           {len(barangays):>6}")
    return 0


def _write_csv(path: Path, fieldnames: list[str], records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)


if __name__ == "__main__":
    sys.exit(main())
