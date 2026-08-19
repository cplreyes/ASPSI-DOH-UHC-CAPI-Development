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
# 2026-06-16 (#529): the 13 F3 'Patient Survey' select_all -> Check Box conversions.
CHECKBOX = {"Q148_CONDITIONS",
            # ---- F1, re-keyed 2026-08-19 (Task 2.3, Aug-17 migration) ----
            # The Aug-17 renumber renamed 57 of F1's 58 multi-select bases, so every
            # F1 entry below is new text for an unchanged field. Q35_2_PCQM_MEASURES is
            # the one genuinely new base. Derived from FacilityHeadSurvey.dcf (a single
            # `alpha` item carrying a value set is checkbox_multiselect's only shape) and
            # checked for collisions against the F3/F4 dictionaries before writing.
            #
            # This is the list with a history of being MISSED when the other checkbox
            # lists moved: an absent name here silently DEMOTES a >=7-option multi-select
            # to a single-select DropDown, which is multi-select DATA LOSS (it happened to
            # the F1 #529/#542 batch and again to F3 #635/#639/#640). F1's fmf-side list
            # is now DERIVED from the dictionary in F1/generate_fmf.py, so this file is
            # the only F1 copy left that can drift.
            "Q23_DATA_REPORTS_USED", "Q35_2_PCQM_MEASURES", "Q36_QUALITY_CHALL",
            "Q37_ACCESS_CHALL", "Q40_YK_PACKAGE", "Q45_PERF_INDICATORS",
            "Q51_APPLY_REASON", "Q52_ACCRED_DIFFICULT", "Q53_WHY_DIFF_PREVENTIVE",
            "Q54_WHY_DIFF_LAB", "Q55_WHY_DIFF_MEDS", "Q56_WHY_DIFF_INFRA",
            "Q57_WHY_DIFF_EQUIPMENT", "Q58_WHY_DIFF_HR", "Q59_WHY_DIFF_HIS",
            "Q60_WHY_DIFF_DOCS", "Q61_WHY_DIFF_DOH_LIC", "Q62_ENROLL_RESPONSIBILITY",
            "Q63_ENROLL_INITIATIVES", "Q65_ENROLL_CHALL_LIST", "Q66_NOT_ACCRED_REASON",
            "Q81_CHARGE_ADDL_CAP_REASONS", "Q83_NOT_RECEIVED_REASONS", "Q85_PAYMENT_CHALL_LIST",
            "Q86_EXPAND_NEXT", "Q91_BUCAS_SERVICES", "Q92_BUCAS_FACTORS",
            "Q98_GAMOT_FACTORS", "Q104_ADDR_STOCKOUT_HOW", "Q108_DOH_LIC_DIFFICULT",
            "Q109_WHY_DIFF_PT_RIGHTS", "Q110_WHY_DIFF_PT_CARE", "Q111_WHY_DIFF_LEADERSHIP",
            "Q112_WHY_DIFF_HRM", "Q113_WHY_DIFF_INFO_MGMT", "Q114_WHY_DIFF_SAFE",
            "Q115_WHY_DIFF_PERF", "Q116_WHY_DIFF_PHYS_PLANT", "Q117_WHY_DIFF_PRICE_INFO",
            "Q118_WHY_DIFF_EQUIPMENT", "Q119_WHY_DIFF_NAT_LAWS", "Q120_WHY_DIFF_EMERG_CART",
            "Q121_WHY_DIFF_ADDONS", "Q124_NBB_BARRIERS", "Q127_ZBB_BARRIERS",
            "Q131_DIFFICULT_REASON", "Q133_MALASAKIT_WHY", "Q134_NO_MALASAKIT_WHY",
            "Q136_LGU_SUPPORT_FORMS", "Q138_LGU_NOT_SAT_WHY", "Q142_SEND_REFERRAL_HOW",
            "Q143_REFERRAL_FORM_TYPE", "Q146_RECEIVE_REFERRAL_HOW", "Q147_EXTERNAL_SERVICES_GO",
            "Q149_NOT_SATISFIED_WHY", "Q150_HR_CHALL", "Q152_PD_DOCTORS",
            "Q153_PD_NURSES",
            # F3 #529 conversions
            "Q36_UHC_SOURCE", "Q37_UHC_UNDERSTAND", "Q46_BENEFITS", "Q65_WHY_NO_USUAL",
            "Q67_WHY_THIS_FACILITY", "Q76_KON_UNDERSTAND", "Q101_BUCAS_UNDERSTAND",
            "Q117_NBB_SOURCE", "Q118_NBB_UNDERSTAND", "Q120_ZBB_SOURCE",
            "Q121_ZBB_UNDERSTAND", "Q171_WHY_NOT", "Q177_WHY_HOSPITAL", "Q125_MAIFIP_SOURCE",
            # F3 #635/#639/#640 Section D conversions (Q42/Q50/Q52 were converted in the
            # generators but never listed here, so the >=7-option ones were being demoted to
            # single-select DropDown — multi-select data-loss; same regression class as the
            # F1 batch noted above).
            "Q42_DIFFICULTY", "Q50_DIFFICULTY_PAYING", "Q52_PLANS",
            # F3 #669/#670/#671/#673 Section E/F/G select_all -> Check Box (tick-all).
            "Q59_SCHED_COMM", "Q61_CONSULT_COMM", "Q70_USUAL_TRANSPORT", "Q73_NEAREST_TRANSPORT",
            "Q75_KON_SOURCE", "Q82_KON_WHY_NOT_REG", "Q85_CONDITIONS", "Q86_VISIT_EVENTS",
            "Q87_OTHER_ACTIONS", "Q90_NOT_CONFINED", "Q93_LABS",
            # F3 #690/#694 Section G/H select_all -> Check Box (tick-all).
            "Q100_BUCAS_SOURCE", "Q103_BUCAS_SERVICES", "Q114_NO_PH",
            # F3 #696 Section K/L select_all -> Check Box (tick-all).
            "Q149_WHERE_BUY", "Q153_GAMOT_SOURCE", "Q154_GAMOT_UNDERSTAND", "Q157_WHERE_REST",
            "Q160_WHY_GENERIC", "Q161_WHY_BRANDED", "Q163_CARE_TYPE",
            # F3 #481 Q128 MAIFIP OOP items select_all -> Check Box (added None + Other).
            "Q128_MAIFIP_OOP_ITEMS",
            # F3 #700 Q129 MAIFIP why-not-avail select_all -> Check Box.
            "Q129_WHY_NO_MAIFIP",
            # F3 #764 Q38.2 why-not-registered (No-only), SELECT ALL THAT APPLY -> Check Box.
            "Q38_2_WHY_NOT_REG",
            # F3 Option B (pilot 2026-06-18): Q92 payment-source tick-list driving the
            # Q92_PAY_ROSTER amount grid.
            "Q92_SOURCES",
            # F3 Option B Shape B (2026-06-19): Q97.1 other-items tick-list driving the
            # Q971_ROSTER amount grid (else it ships single-select = multi-select data loss).
            "Q971_SOURCES",
            # F3 Option B fan-out (2026-06-19): the rest of the F3 cost-matrix cluster's
            # tick-lists driving their roster amount grids. Miss any here and optimize
            # demotes it to single-select DropDown = multi-select data loss (silent).
            "Q96_SOURCES", "Q972_SOURCES", "Q98_SOURCES",       # Section G (Q94 now per-lab roster #450)
            "Q107_SOURCES", "Q109_SOURCES", "Q112_SOURCES", "Q113_SOURCES",    # Section H
            # F4 #529 conversions (17 'Household Survey' select_all -> Check Box).
            # Note: Q53/Q58/Q121 names overlap F3's set but are distinct fields per
            # instrument (this is a single shared name set keyed only by field name;
            # F4's Q53_UHC_UNDERSTAND, Q58_BUCAS_SOURCE, Q121_WHY_HOSPITAL also belong).
            "Q52_UHC_SOURCE", "Q53_UHC_UNDERSTAND", "Q55_YAKAP_SOURCE",
            "Q56_YAKAP_UNDERSTAND", "Q58_BUCAS_SOURCE", "Q59_BUCAS_UNDERSTAND",
            # #568/#570/#571: three more F4 select_all -> Check Box conversions.
            "Q61_BUCAS_SERVICES", "Q65_CONDITIONS", "Q66_WHERE_BUY",
            "Q85_BENEFITS", "Q91_WHY_WENT", "Q93_WHY_NOT", "Q94_TRANSPORT",
            "Q113_WHY_NOT", "Q121_WHY_HOSPITAL", "Q127_NBB_SOURCE",
            "Q128_NBB_UNDERSTAND", "Q133_ZBB_SOURCE", "Q134_ZBB_UNDERSTAND",
            "Q137_MAIFIP_SOURCE",
            "Q70_GAMOT_SOURCE", "Q71_GAMOT_UNDERSTAND",
            # #577-585/#588/#590-591: 10 more F4 'Household Survey' select_all -> Check Box
            # (tick-all-that-apply). Q103/Q109 names are distinct F4 fields (no cross-
            # instrument collision in this shared name-keyed set).
            "Q74_WHERE_REST", "Q77_WHY_GENERIC", "Q78_WHY_BRANDED", "Q82_DIFFICULTY_REASONS",
            "Q88_DIFF_PAYING", "Q102_VISIT_REASON", "Q103_CARE_TYPE", "Q106_FORGONE_WHY",
            "Q84_WHERE_ASSIST",   # #814
            "Q107_OTHER_ACTIONS", "Q109_TYPE",
            "Q140_BILL_ITEMS",   # 1176-aug17: renumbered from Q141 (#615 lineage); Q143 is no longer a checkbox
            "Q196_FOREGONE", "Q202_WORRY_REASONS"}   # #638/#668 Section O/Q tick-all (keep CheckBox, don't demote)
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
    # Calendar picker for interviewer-entered dates (kills format typos; the apc
    # range checks stay as the backstop). #1174: the F3 labels now read (MMDDYYYY)
    # — match either spelling, but KEEP the stored composition YYYYMMDD (a
    # MMDDYYYY-format picker would mis-parse stored 20YY... values on revisit).
    if (m.get("type") == "numeric" and m.get("len") == 8 and not m.get("vs")
            and any(t in (m.get("label") or "").upper()
                    for t in ("YYYYMMDD", "MMDDYYYY"))):
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
