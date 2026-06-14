#!/usr/bin/env python
r"""Capture-type optimizer — assigns each form field the mobile-appropriate control
based on the dictionary (value-set size + known cascade fields), so the CAPI app is
tap-driven instead of typed. Repeatable; rewrites <Base>.fmf in place (BOM + CRLF
preserved). Run after generate_dcf so value sets are current.

Rules (this pass — the safe, no-logic-change set):
  * Geographic cascade fields (dynamic value sets via setvalueset) -> DropDown
  * Coded single-select with >= 7 options                          -> DropDown
  * Interviewer-entered YYYYMMDD dates (numeric len 8, no v-set)   -> Date,YYYYMMDD
  * (2-6 options stay RadioButton — already optimal; left untouched)
Free-text / numeric / name / amount fields have no value set and are left as-is.

Usage:  py optimize_capture_types.py F1   [--dry]
"""
import json, sys
from pathlib import Path

CSPRO_DIR = Path(__file__).resolve().parent.parent
SPECS = {"F1": "FacilityHeadSurvey", "F3": "PatientSurvey", "F4": "HouseholdSurvey"}
# Fields whose value set is set dynamically (PSGC cascade) — force DropDown.
CASCADE = {"REGION", "PROVINCE_HUC", "CITY_MUNICIPALITY", "BARANGAY",
           "P_REGION", "P_PROVINCE_HUC", "P_CITY_MUNICIPALITY", "P_BARANGAY"}
# Single alpha fields that are TRUE multi-selects (one field, codes concatenated) -> Check Box
# tick-list. Must win over the >=7-options DropDown rule below. 2026-06-12 R4 review: F3 Q148;
# F1 Q49/Q50/Q53/Q58 (GH #377/#378/#379 — select-all -> Check Box redesign mirroring Q148).
CHECKBOX = {"Q148_CONDITIONS",
            "Q49_QUALITY_CHALL", "Q50_ACCESS_CHALL",
            "Q53_YK_PACKAGE", "Q58_PERF_INDICATORS"}
DROPDOWN_MIN = 7   # >= this many coded options -> dropdown instead of radio


def field_meta(dcf_path):
    d = json.loads(Path(dcf_path).read_text(encoding="utf-8"))
    meta = {}
    for lvl in d.get("levels", []):
        for rec in lvl.get("records", []):
            for it in rec.get("items", []):
                vs = it.get("valueSets") or []
                lab = next((l.get("text", "") for l in (it.get("labels") or [])
                            if l.get("language") in (None, "EN")), "")
                meta[it["name"]] = {
                    "vs": len(vs[0].get("values", []) or []) if vs else 0,
                    "type": it.get("contentType", ""),
                    "len": it.get("length", 0),
                    "label": lab,
                }
    return meta


def ideal(name, meta):
    m = meta.get(name) or {}
    if name in CHECKBOX:
        return "CheckBox"
    if name in CASCADE:
        return "DropDown"
    if m.get("vs", 0) >= DROPDOWN_MIN:
        return "DropDown"
    # Calendar picker for interviewer-entered YYYYMMDD dates (kills format typos;
    # the apc range checks stay as the backstop).
    if (m.get("type") == "numeric" and m.get("len") == 8 and not m.get("vs")
            and "YYYYMMDD" in (m.get("label") or "").upper()):
        return "Date,YYYYMMDD"
    return None   # leave whatever it is


def main():
    key = next((a for a in sys.argv[1:] if a in SPECS), "F1")
    dry = "--dry" in sys.argv
    base = SPECS[key]
    inst = CSPRO_DIR / key
    fmf = inst / f"{base}.fmf"
    meta = field_meta(inst / f"{base}.dcf")

    text = fmf.read_text(encoding="utf-8-sig")
    lines = text.split("\r\n") if "\r\n" in text else text.split("\n")
    in_field = False
    cur = None
    changes = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s == "[Field]":
            in_field, cur = True, None
        elif s.startswith("["):
            in_field, cur = False, None
        elif in_field and s.startswith("Name="):
            cur = s[5:].strip()
        elif in_field and s.startswith("DataCaptureType="):
            want = ideal(cur, meta)
            have = s.split("=", 1)[1].strip()
            if want and want != have:
                lines[i] = f"DataCaptureType={want}"
                changes.append((cur, have, want))

    # Legacy cleanup: the combined 'Date,FMT' DataCaptureType embeds the format; the
    # publish PACKAGER rejects a leftover standalone 'CaptureDateFormat=' in the same
    # [Field] ("Incorrect [Field] attribute: CaptureDateFormat" at Deploy 'Creating
    # package...' — 2026-06-12 F1 legacy hand-style Date + CaptureDateFormat pair).
    # NOTE: Designer open + COMPILE accepted that combo — the packager is the stricter
    # parser; this cleanup is the only static guard.
    in_field, combined, fmt_at, drop = False, False, None, []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s == "[Field]":
            in_field, combined, fmt_at = True, False, None
        elif s.startswith("["):
            in_field = False
        elif in_field and s.startswith("DataCaptureType=") and "," in s:
            combined = True
            if fmt_at is not None:
                drop.append(fmt_at)
        elif in_field and s.startswith("CaptureDateFormat="):
            if combined:
                drop.append(i)
            else:
                fmt_at = i
    for i in sorted(drop, reverse=True):
        changes.append(("(legacy line)", lines[i].strip(), "removed"))
        del lines[i]

    print(f"[{key}] {len(changes)} field(s) re-typed:")
    for n, h, w in changes:
        print(f"   {n}: {h} -> {w}")
    if not dry and changes:
        # join with \n: text-mode write translates to CRLF on Windows.
        # ("\r\n".join here produced \r\r\n on disk — CSPro tolerated it, but
        # it doubles apparent line counts for every text-mode reader.)
        fmf.write_text("﻿" + "\n".join(lines), encoding="utf-8")
        print(f"   wrote {fmf.name}")
    elif dry:
        print("   (dry run — not written)")


if __name__ == "__main__":
    main()
