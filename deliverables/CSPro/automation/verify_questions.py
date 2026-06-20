#!/usr/bin/env python
r"""Comprehensive per-question verification gate for F1/F3/F4 — checks EVERY field,
complementing the CSEntry compile gate (which only proves the logic *compiles*).

For each instrument it verifies:
  1. Reachability   — every item is on a form, or a known off-form computed item
                      (LANGUAGE_USED, the derived geo codes, CASE_SEQ, names).
  2. Value sets     — every coded field has a non-empty value set.
  3. Dead conditions— every apc comparison `FIELD = N` / `FIELD <> N` / `FIELD in N,...`
                      uses codes that actually EXIST in FIELD's value set. A code not in
                      the set means that branch of the skip/validation never fires — the
                      logic is silently broken (the compiler can't catch it).
  4. Skip targets   — every `skip to TARGET` points at a real field.

CSPro `{...}` comments are stripped before the logic scan so example codes in notes
don't false-match. Exit 0 = all clean, 1 = at least one anomaly (excluding the known
off-form computed items).

Usage:  py verify_questions.py            # all three
"""
import json, re, sys
from pathlib import Path

CSPRO = Path(__file__).resolve().parent.parent
SPECS = [("F1", "FacilityHeadSurvey"), ("F3", "PatientSurvey"), ("F4", "HouseholdSurvey")]
# Computed items that are intentionally off-form (set in logic, never entered).
KNOWN_OFFFORM = {
    "LANGUAGE_USED", "REGION_CODE", "PROVINCE_HUC_CODE", "CITY_MUNICIPALITY_CODE",
    "FACILITY_NO", "CASE_SEQ", "REGION", "PROVINCE_HUC", "CITY_MUNICIPALITY",
    "FACILITY_NAME", "FACILITY_ADDRESS",
    # Binary Image item (#713 photo->CSWeb fix): bytes are captured in logic and
    # synced inside the case; binary items cannot be placed on a form, so it is
    # off-form by design (capture is driven from CAPTURE_VERIFICATION_PHOTO).
    "VERIFICATION_PHOTO_IMAGE",
}


def load_dcf(p):
    d = json.load(open(p, encoding="utf-8"))
    codes, items = {}, []
    for lvl in d["levels"]:
        ids = lvl.get("ids", {})
        items += (ids.get("items", []) if isinstance(ids, dict) else [])
        for rec in lvl.get("records", []):
            items += rec.get("items", [])
    for it in items:
        vs = it.get("valueSets") or []
        if vs:
            cs = set()
            for v in vs[0].get("values", []):
                val = (v.get("pairs") or [{}])[0].get("value")
                if val is not None and re.fullmatch(r"-?\d+", str(val).strip()):
                    cs.add(int(str(val).strip()))
            codes[it["name"]] = cs
    return items, codes


def on_form_fields(fmf):
    t = Path(fmf).read_text(encoding="utf-8-sig", errors="replace")
    return (set(re.findall(r"(?m)^Item=([A-Z0-9_]+)$", t))
            | set(re.findall(r"\[Field\]\s*\r?\nName=([A-Z0-9_]+)", t)))


def verify(key, base):
    items, codes = load_dcf(CSPRO / key / f"{base}.dcf")
    names = {it["name"] for it in items}
    formfields = on_form_fields(CSPRO / key / f"{base}.fmf")
    apc = re.sub(r"\{[^{}]*\}", " ", (CSPRO / key / f"{base}.ent.apc").read_text(encoding="utf-8"))

    unreachable = [it["name"] for it in items
                   if it["name"] not in formfields and it["name"] not in KNOWN_OFFFORM]
    empty_vs = [n for n, cs in codes.items() if not cs]
    dead = set()
    for fld, cs in codes.items():
        if not cs:
            continue
        for m in re.finditer(rf"\b{re.escape(fld)}\s*(=|<>)\s*(-?\d+)\b", apc):
            if int(m.group(2)) not in cs:
                dead.add((fld, m.group(1), int(m.group(2)), tuple(sorted(cs))))
        for m in re.finditer(rf"\b{re.escape(fld)}\s+in\s+([\d,\s]+)", apc):
            for tok in re.findall(r"-?\d+", m.group(1)):
                if int(tok) not in cs:
                    dead.add((fld, "in", int(tok), tuple(sorted(cs))))
    bad_skip = sorted({t for t in re.findall(r"skip\s+to\s+([A-Z0-9_]+)", apc) if t not in names})

    ok = not (unreachable or empty_vs or dead or bad_skip)
    print(f"[{key}] {len(items)} items · {len(codes)} coded · "
          f"reachable {len(items)-len([i for i in items if i['name'] not in formfields and i['name'] not in KNOWN_OFFFORM])}/{len(items)} "
          f"· dead-conditions {len(dead)} · bad-skips {len(bad_skip)} · "
          + ("PASS" if ok else "FAIL"))
    for n in unreachable:
        print(f"    UNREACHABLE: {n} (not on a form, not a known computed item)")
    for n in empty_vs:
        print(f"    EMPTY VALUE SET: {n}")
    for fld, op, n, cs in sorted(dead):
        print(f"    DEAD CONDITION: {fld} {op} {n}  (valid codes {list(cs)})")
    for t in bad_skip:
        print(f"    BAD SKIP TARGET: skip to {t}")
    return ok


def main():
    keys = [a for a in sys.argv[1:] if a in dict(SPECS)] or [k for k, _ in SPECS]
    results = {k: verify(k, dict(SPECS)[k]) for k in keys}
    print("\n=== per-question verification:",
          " · ".join(f"{k} {'PASS' if v else 'FAIL'}" for k, v in results.items()))
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
