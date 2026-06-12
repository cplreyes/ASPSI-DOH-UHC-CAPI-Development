#!/usr/bin/env python
r"""Build the FACILITY_LOOKUP CSPro lookup table from the DOH facility-coding sheet,
so entering the 12-digit Questionnaire Number can auto-fill the facility's name +
region + province/HUC. Keyed by the 9-digit facility code (= REGION_CODE +
PROVINCE_HUC_CODE + CITY_MUNICIPALITY_CODE + FACILITY_NO concatenated).

Source : Downloads\DOH UHC Yr2 Health Facility Coding.xlsx  (sheet "Facility Codes")
Outputs: F1\facility_lookup.dcf  +  F1\facility_lookup.dat   (bundled app-relative)

Usage: py build_facility_lookup.py
"""
import json
from pathlib import Path
import openpyxl

SRC = Path(r"C:\Users\analy\Downloads\DOH UHC Yr2 Health Facility Coding.xlsx")
OUTDIR = Path(__file__).resolve().parent.parent / "F1"

# fixed-width record layout (chars). F_CODE is the id.
W = {"F_CODE": 9, "F_REGION": 40, "F_PROVINCE": 60, "F_NAME": 120, "F_TYPE": 30, "F_OWNERSHIP": 40}


def clean(v):
    return ("" if v is None else str(v)).replace("\n", " ").replace("\r", " ").strip()


def main():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["Facility Codes"]
    seen = {}
    for r in ws.iter_rows(min_row=3, values_only=True):
        code = clean(r[5])            # col F = Facility Codes
        if not (code.isdigit() and len(code) == 9):
            continue
        seen[code] = {
            "F_CODE": code,
            "F_REGION": clean(r[1]),    # col B
            "F_PROVINCE": clean(r[2]),  # col C Province/HUC
            "F_NAME": clean(r[6]),      # col G Facility Name
            "F_TYPE": clean(r[7]),      # col H
            "F_OWNERSHIP": clean(r[8]), # col I
        }
    wb.close()
    rows = [seen[c] for c in sorted(seen)]

    # --- .dat (fixed width, sorted by code so CSPro index/loadcase is happy) ---
    def fit(s, n):
        s = s[:n]
        return s.ljust(n)
    lines = []
    for d in rows:
        line = (d["F_CODE"].zfill(9) + fit(d["F_REGION"], W["F_REGION"]) + fit(d["F_PROVINCE"], W["F_PROVINCE"])
                + fit(d["F_NAME"], W["F_NAME"]) + fit(d["F_TYPE"], W["F_TYPE"]) + fit(d["F_OWNERSHIP"], W["F_OWNERSHIP"]))
        lines.append(line)
    (OUTDIR / "facility_lookup.dat").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- .dcf (modeled on the PSGC lookup dicts; id = F_CODE) ---
    def item(name, ctype, length):
        return {"name": name, "labels": [{"text": name}], "contentType": ctype, "length": length,
                **({"zeroFill": True} if ctype == "numeric" else {})}
    dcf = {
        "software": "CSPro", "version": 8.0, "fileType": "dictionary", "name": "FACILITY_LOOKUP",
        "labels": [{"text": "DOH Facility Coding Lookup"}], "readOptimization": True,
        "recordType": {"start": 0, "length": 0}, "defaults": {"decimalMark": True, "zeroFill": True},
        "relativePositions": True,
        "levels": [{
            "name": "FACILITY_LOOKUP_LEVEL", "labels": [{"text": "Facility lookup level"}],
            "ids": {"items": [item("F_CODE", "numeric", 9)]},
            "records": [{
                "name": "FACILITY_LOOKUP_REC", "labels": [{"text": "Facility record"}],
                "occurrences": {"required": True, "maximum": 1},
                "items": [item("F_REGION", "alpha", W["F_REGION"]), item("F_PROVINCE", "alpha", W["F_PROVINCE"]),
                          item("F_NAME", "alpha", W["F_NAME"]), item("F_TYPE", "alpha", W["F_TYPE"]),
                          item("F_OWNERSHIP", "alpha", W["F_OWNERSHIP"])],
            }],
        }],
    }
    (OUTDIR / "facility_lookup.dcf").write_text(json.dumps(dcf, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} facilities -> facility_lookup.dat / .dcf")
    print("sample:", rows[0]["F_CODE"], rows[0]["F_NAME"][:30], "|", rows[0]["F_REGION"], "|", rows[0]["F_PROVINCE"])


if __name__ == "__main__":
    main()
