"""
generate_apc.py — F4 Household Survey CSPro logic generator
                  (UHC Survey System v1.0 rebuild — phase 4).

Emits HouseholdSurvey.generated.apc — the CAPI logic for HouseholdSurvey.dcf
/.fmf, driven by F4-Skip-Logic-and-Validations.md.

Generator-first: output is HouseholdSurvey.generated.apc. The CSPro Designer /
bench-test pass (spec section 6) verifies it against a paper walkthrough.

Run:
    python generate_apc.py        # writes HouseholdSurvey.generated.apc next to this file
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_dcf import build_dictionary_f4


# ============================================================
# SKIP RULES — single-condition jumps (spec section 2).
# (trigger item, CSPro condition, skip-to target, comment)
# ============================================================

SKIP_RULES = [
    # --- Section B ---
    ("Q7_IS_PWD", "Q7_IS_PWD = 2", "Q11_EDUCATION", "Q7 = No -> skip Q8-Q10"),
    ("Q9_PWD_CARD", "Q9_PWD_CARD = 2", "Q11_EDUCATION",
     "Q9 = card not presented -> skip Q10 disability type"),
    ("Q14_IP_MEMBER", "Q14_IP_MEMBER = 2", "Q16_4PS", "Q14 = No -> skip Q15"),
    # --- Section D ---
    ("Q51_UHC_HEARD", "Q51_UHC_HEARD = 2", "Q54_YAKAP_HEARD",
     "Q51 = No -> skip Q52, Q53"),
    # --- Section E ---
    ("Q54_YAKAP_HEARD", "Q54_YAKAP_HEARD = 2", "Q57_BUCAS_HEARD",
     "Q54 = No -> skip Q55, Q56"),
    # --- Section F ---
    ("Q57_BUCAS_HEARD", "Q57_BUCAS_HEARD = 2", "Q62_PURCHASE_FREQ",
     "Q57 = No -> skip Q58-Q61"),
    ("Q60_BUCAS_ACCESSED", "Q60_BUCAS_ACCESSED = 2", "Q62_PURCHASE_FREQ",
     "Q60 = No -> skip Q61"),
    # --- Section G ---
    ("Q62_PURCHASE_FREQ", "Q62_PURCHASE_FREQ = 5", "Q69_GAMOT_HEARD",
     "Q62 = Never -> skip Q63-Q68"),
    ("Q69_GAMOT_HEARD", "Q69_GAMOT_HEARD = 2", "Q75_BRAND_GEN_KNOWS",
     "Q69 = No -> skip Q70-Q74"),
    ("Q72_GAMOT_OBTAINED", "Q72_GAMOT_OBTAINED = 2", "Q75_BRAND_GEN_KNOWS",
     "Q72 = No -> skip Q73, Q74"),
    ("Q75_BRAND_GEN_KNOWS", "Q75_BRAND_GEN_KNOWS = 2", "Q79_REG_SOURCE",
     "Q75 = No -> exit Section G"),
    # --- Section H ---
    ("Q81_REG_DIFFICULTY", "Q81_REG_DIFFICULTY = 2", "Q83_KNOWS_ASSIST",
     "Q81 = No -> skip Q82"),
    ("Q83_KNOWS_ASSIST", "Q83_KNOWS_ASSIST = 2", "Q85_BENEFITS_O01",
     "Q83 = No -> skip Q84"),
    ("Q86_PREMIUM_PAY", "Q86_PREMIUM_PAY = 3", "Q89_HAS_USUAL_FACILITY",
     "Q86 = does not pay premiums -> skip Q87, Q88"),
    ("Q87_PREMIUM_DIFFICULT", "Q87_PREMIUM_DIFFICULT = 2", "Q89_HAS_USUAL_FACILITY",
     "Q87 = No -> skip Q88"),
    # --- Section I ---
    ("Q97_KNOWS_BOOKING", "Q97_KNOWS_BOOKING = 2", "Q100_LEAVE_WORK_SCHOOL",
     "Q97 = No -> skip Q98, Q99 (phone-advice questions moot)"),
    # --- Section J ---
    ("Q101_CHECKUP_FREQ", "Q101_CHECKUP_FREQ = 6", "Q105_FORGONE_CARE",
     "Q101 = Never -> skip Q102-Q104"),
    ("Q105_FORGONE_CARE", "Q105_FORGONE_CARE = 2", "Q108_REFERRED",
     "Q105 = No forgone care -> skip Q106, Q107"),
    # --- Section K ---
    ("Q108_REFERRED", "Q108_REFERRED = 2", "Q126_NBB_HEARD",
     "Q108 = No -> skip Q109-Q125 (jump to Section L)"),
    ("Q117_SPECIALIST_FOLLOWUP", "Q117_SPECIALIST_FOLLOWUP = 2", "Q119_PCF_REFERRAL",
     "Q117 = No -> skip Q118"),
    # --- Section L ---
    ("Q126_NBB_HEARD", "Q126_NBB_HEARD in 2,3", "Q129_HH_CONFINED",
     "Q126 not heard -> skip Q127, Q128"),
    ("Q130_HOSPITAL_TYPE", "Q130_HOSPITAL_TYPE = 3", "Q132_ZBB_HEARD",
     "Q130 = Private -> skip Q131 (NBB applies to public facilities only)"),
    # --- Section M ---
    ("Q132_ZBB_HEARD", "Q132_ZBB_HEARD in 2,3", "Q136_MAIFIP_HEARD",
     "Q132 not heard -> skip Q133-Q135"),
    ("Q136_MAIFIP_HEARD", "Q136_MAIFIP_HEARD in 2,3", "Q138_MOST_EXPENSIVE",
     "Q136 not heard -> skip Q137"),
    ("Q140_RECALL_BREAKDOWN", "Q140_RECALL_BREAKDOWN = 2", "Q142_RECALL_PAYMENT",
     "Q140 = No -> skip Q141, Q141.1"),
    ("Q142_RECALL_PAYMENT", "Q142_RECALL_PAYMENT = 2", "Q144_CEREALS_CONSUMED",
     "Q142 = No -> skip Q143 (end of Section M)"),
]


# Multi-branch routing (spec section 2). (item, [(cond, target), ...], comment)
MULTI_BRANCH_SKIPS = [
    ("Q23_WATER_SOURCE", [
        ("Q23_WATER_SOURCE = 2", "Q25_TUBE_SHARE"),
        ("Q23_WATER_SOURCE in 3,4", "Q26_REFRIGERATOR"),
    ], "Q23 water-source branch: faucet -> Q24; piped well -> Q25; "
       "dug well / other -> Q26"),
    ("Q76_BRAND_OR_GEN", [
        ("Q76_BRAND_OR_GEN = 1", "Q78_WHY_BRANDED_O01"),
        ("Q76_BRAND_OR_GEN in 4,9", "Q79_REG_SOURCE"),
    ], "Q76 branded/generic branch: Branded -> Q78; generic/both -> Q77; "
       "don't-know / N/A -> exit Section G"),
    ("Q89_HAS_USUAL_FACILITY", [
        ("Q89_HAS_USUAL_FACILITY = 2", "Q93_WHY_NOT_O01"),
    ], "Q89 = No usual facility -> skip Q89.1, Q90-Q92 to the why-not block"),
    ("Q90_IS_USUAL_FOR_GENERAL", [
        ("Q90_IS_USUAL_FOR_GENERAL = 1", "Q94_TRANSPORT_O01"),
    ], "Q90 = Yes (usual facility used for general care) -> skip Q91-Q93"),
    ("Q112_VISITED", [
        ("Q112_VISITED = 1", "Q114_DISCUSSED_PLACES"),
    ], "Q112 = Yes (visited) -> skip Q113 why-not; not-planning/not-yet flow "
       "into Q113"),
    ("Q119_PCF_REFERRAL", [
        ("Q119_PCF_REFERRAL = 2", "Q121_WHY_HOSPITAL_O01"),
    ], "Q119 = No (not a PCF referral) -> skip Q120 to the why-hospital block"),
    ("Q129_HH_CONFINED", [
        ("Q129_HH_CONFINED = 2", "Q144_CEREALS_CONSUMED"),
    ], "Q129 = No HH confinement -> skip Q130-Q143 to Section N. NOTE: the "
       "spec's Section M preamble says ZBB awareness Q132-Q134 is asked "
       "regardless of confinement -- this contradicts the section-2 skip-table "
       "row used here; confirm the intended scope in bench-test."),
]


# Roster (C_HOUSEHOLD_ROSTER) per-member intra-record skips (spec section 2).
ROSTER_SKIPS = [
    ("Q35_HAS_DISABILITY", "Q35_HAS_DISABILITY = 0", "Q39_CIVIL_STATUS",
     "Q35 = No disability -> skip Q36, Q37, Q38"),
    ("Q37_PWD_CARD", "Q37_PWD_CARD = 0", "Q39_CIVIL_STATUS",
     "Q37 = card not presented -> skip Q38 disability type"),
    ("Q45_PHILHEALTH_REG", "Q45_PHILHEALTH_REG = 02", "Q48_NAME_FIRST",
     "Q45 = not PhilHealth-registered -> skip Q46 member category"),
]


# WHO/SHA panel subtotals (spec section 3.15). (subtotal item, [panel prefixes])
# Each subtotal = sum over the panel of (_PURCHASED_PHP + _INKIND_PHP).
SUBTOTALS = [
    ("Q157_FOOD_SUBTOTAL_TOTAL_PHP", [
        "Q144_CEREALS", "Q145_PULSES", "Q146_VEGETABLES", "Q147_FRUITS",
        "Q148_FISH", "Q149_MEAT", "Q150_EGGS", "Q151_MILK", "Q152_FATS",
        "Q153_SUGAR", "Q154_CONDIMENTS", "Q155_WATER_NA", "Q156_ALCOHOL"]),
    ("Q177_HEALTH_12M_SUBTOTAL_TOTAL_PHP", [
        "Q175_INPATIENT", "Q176_EMERGENCY_TRANSPORT"]),
    ("Q182_HEALTH_6M_SUBTOTAL_TOTAL_PHP", [
        "Q178_PREVENTIVE", "Q179_DIAGNOSTIC", "Q180_ASSISTIVE",
        "Q181_MEDICAL_PRODUCTS"]),
    ("Q185_HEALTH_1M_SUBTOTAL_TOTAL_PHP", [
        "Q183_MEDICINES", "Q184_OUTPATIENT"]),
]


# Numeric-range validations (spec section 3). (item, condition, severity, msg)
NUMERIC_VALIDATIONS = [
    ("Q2_BIRTH_MONTH", "Q2_BIRTH_MONTH < 1 or Q2_BIRTH_MONTH > 12", "hard",
     "Birth month must be 1-12."),
    ("Q19_HH_SIZE_TOTAL", "Q19_HH_SIZE_TOTAL < 1 or Q19_HH_SIZE_TOTAL > 20", "hard",
     "Household size must be between 1 and 20."),
    ("Q19_HH_SIZE_TOTAL", "Q19_HH_SIZE_TOTAL > 10", "soft",
     "Household size %d is unusually large. Confirm?"),
    ("Q32_AGE", "Q32_AGE < 0 or Q32_AGE > 120", "hard",
     "Member age must be between 0 and 120."),
    ("Q67_TIME_TO_PHARMACY", "Q67_TIME_TO_PHARMACY > 1440", "hard",
     "Travel time to pharmacy cannot exceed 1440 minutes (24h)."),
    ("Q95_TRAVEL_TIME_MIN", "Q95_TRAVEL_TIME_MIN > 1440", "hard",
     "Travel time cannot exceed 1440 minutes (24h)."),
    ("Q195_INCOME_PCT", "Q195_INCOME_PCT < 0 or Q195_INCOME_PCT > 100", "hard",
     "Income percentage must be between 0 and 100."),
]


# 'Other (specify)' overrides — explicit _OTHER_TXT items whose name does not
# match their select-all's prefix, so the trigger is not auto-derivable.
OTHER_SPECIFY_OVERRIDES = {
    "Q82_DIFFICULTY_OTHER_TXT":   ("Q82_DIFFICULTY_REASONS_O08", 1),
    "Q141_BILL_ITEMS_OTHER_TXT":  ("Q141_BILL_ITEMS_O07", 1),
}


# ============================================================
# EMITTERS
# ============================================================

def _proc(name, block, body_lines):
    out = [f"PROC {name}", f"{block}"]
    out.extend(f"  {ln}" if ln else "" for ln in body_lines)
    out.append("")
    return out


def emit_framework():
    """GLOBAL, includes, app preproc, FIELD_CONTROL prefill, consent
    terminator, Q202 end-of-survey (spec sections 4.1, 4.2, 3.18)."""
    out = []
    out.append("{ ---- shared helper includes (spec 4.3, 4.3a) ---- }")
    out.append('#include "../../shared/PSGC-Cascade.apc"')
    out.append('#include "../../shared/Capture-Helpers.apc"')
    out.append("")
    out.append("PROC GLOBAL")
    out.append("numeric currentYYYYMMDD;")
    out.append("numeric currentYear;")
    out.append("numeric currentMonth;")
    out.append("")
    out += _proc("HOUSEHOLDSURVEY_FF", "preproc", [
        'currentYYYYMMDD = tonumber(sysdate("YYYYMMDD"));',
        "currentYear  = int(currentYYYYMMDD / 10000);",
        "currentMonth = int(currentYYYYMMDD / 100) % 100;",
    ])
    out += _proc("FIELD_CONTROL", "preproc", [
        "{ prefill the case-control block on first visit }",
        'if visualvalue(SURVEY_CODE) = "" then',
        '  SURVEY_CODE       = "F4";',
        '  DATE_STARTED      = tonumber(sysdate("YYYYMMDD"));',
        '  TIME_STARTED      = tonumber(systime("HHMMSS"));',
        "  AAPOR_DISPOSITION = 0;   { 000 = In Progress }",
        "endif;",
    ])
    out += _proc("CONSENT_GIVEN", "postproc", [
        "{ consent refusal -> AAPOR 210, skip all data entry to the closing form }",
        "if CONSENT_GIVEN = 2 then",
        "  AAPOR_DISPOSITION       = 210;   { Refusal — respondent }",
        "  ENUM_RESULT_FINAL_VISIT = 3;     { Refused }",
        '  errmsg("Consent not given. Close the questionnaire and code as Refused.");',
        "  skip to SURVEY_TEAM_LEADER_S_NAME;   { first item on the closing form }",
        "endif;",
    ])
    out += _proc("Q1_IS_HH_HEAD", "postproc", [
        "{ not the HH head -> soft confirm (spec 3.2; no hard skip) }",
        "if Q1_IS_HH_HEAD = 2 then",
        '  errmsg("Respondent is not the HH head — confirm they are a household '
        'decision-maker per the sampling protocol.");',
        "endif;",
    ])
    out += _proc("Q202_WORRY_REASONS_O01", "postproc", [
        "{ end of questionnaire — mark the case complete (spec 3.18) }",
        "AAPOR_DISPOSITION       = 110;   { Complete interview }",
        "ENUM_RESULT_FINAL_VISIT = 1;     { Completed }",
    ])
    return out


def emit_psgc_cascade():
    """PSGC cascade onfocus handlers — F4 has a single household chain
    (spec 4.3)."""
    out = ["{ ---- PSGC cascade (spec 4.3) ---- }"]
    out += _proc("PROVINCE_HUC_CODE", "onfocus",
                 ["FillProvinceValueSet(PROVINCE_HUC_CODE, REGION_CODE);"])
    out += _proc("CITY_MUNICIPALITY_CODE", "onfocus",
                 ["FillCityValueSet(CITY_MUNICIPALITY_CODE, PROVINCE_HUC_CODE);"])
    out += _proc("BARANGAY_CODE", "onfocus",
                 ["FillBarangayValueSet(BARANGAY_CODE, CITY_MUNICIPALITY_CODE);"])
    return out


def emit_capture():
    """Household GPS + verification photo (spec 4.3a)."""
    out = ["{ ---- GPS + verification photo capture (spec 4.3a) ---- }"]
    out += _proc("HH_CAPTURE_GPS", "onfocus", [
        "if ReadGPSReading(120, 20) then",
        '  HH_GPS_LATITUDE   = maketext("%f", gps(latitude));',
        '  HH_GPS_LONGITUDE  = maketext("%f", gps(longitude));',
        '  HH_GPS_ALTITUDE   = maketext("%f", gps(altitude));',
        "  HH_GPS_ACCURACY   = gps(accuracy);",
        "  HH_GPS_SATELLITES = gps(satellites);",
        "  HH_GPS_READTIME   = gps(readtime);",
        "endif;",
        "HH_CAPTURE_GPS = notappl;   { re-arm the trigger }",
    ])
    out += _proc("HH_GPS_LATITUDE", "postproc", [
        "numeric lat;",
        "lat = tonumber(HH_GPS_LATITUDE);",
        "if lat <> notappl and (lat < 4.5 or lat > 21.5) then",
        '  errmsg("Latitude %f is outside the Philippine bounding box — re-capture.", lat);',
        "  move to HH_CAPTURE_GPS;",
        "endif;",
    ])
    out += _proc("HH_GPS_LONGITUDE", "postproc", [
        "numeric lon;",
        "lon = tonumber(HH_GPS_LONGITUDE);",
        "if lon <> notappl and (lon < 116.5 or lon > 127.0) then",
        '  errmsg("Longitude %f is outside the Philippine bounding box — re-capture.", lon);',
        "  move to HH_CAPTURE_GPS;",
        "endif;",
    ])
    out += _proc("HH_GPS_ACCURACY", "postproc", [
        "if HH_GPS_ACCURACY <> notappl and HH_GPS_ACCURACY > 30 then",
        '  errmsg("GPS accuracy %d m is poor (> 30 m). Re-read outdoors recommended.", HH_GPS_ACCURACY);',
        "endif;",
    ])
    out += _proc("HH_GPS_SATELLITES", "postproc", [
        "if HH_GPS_SATELLITES <> notappl and HH_GPS_SATELLITES < 4 then",
        '  errmsg("Only %d GPS satellites — fix below the reliable minimum.", HH_GPS_SATELLITES);',
        "endif;",
    ])
    out += _proc("CAPTURE_VERIFICATION_PHOTO", "onfocus", [
        "string fn;",
        'fn = "case-" + maketext("%02d%02d%03d%02d%03d", REGION_CODE, PROVINCE_HUC_CODE,',
        '          CITY_MUNICIPALITY_CODE, FACILITY_NO, CASE_SEQ) + "-verification.jpg";',
        "if TakeVerificationPhoto(fn) then",
        "  VERIFICATION_PHOTO_FILENAME = fn;",
        "endif;",
        "CAPTURE_VERIFICATION_PHOTO = notappl;",
    ])
    out += _proc("VERIFICATION_PHOTO_FILENAME", "postproc", [
        "if ENUM_RESULT_FINAL_VISIT = 1 and length(strip(VERIFICATION_PHOTO_FILENAME)) = 0 then",
        '  errmsg("Verification photo is required when the case is marked Completed.");',
        "  move to CAPTURE_VERIFICATION_PHOTO;",
        "endif;",
    ])
    return out


def emit_section_b():
    """Section B cross-field consistency (spec 3.3) + the post-roster count
    check on Q47 (spec 3.4)."""
    out = ["{ ---- Section B consistency + post-roster check (spec 3.3, 3.4) ---- }"]
    out += _proc("Q2_1_AGE", "postproc", [
        "numeric computedAge;",
        "computedAge = currentYear - Q2_BIRTH_YEAR;",
        "if Q2_BIRTH_MONTH > currentMonth then computedAge = computedAge - 1; endif;",
        "if Q2_BIRTH_YEAR > 0 and abs(Q2_1_AGE - computedAge) > 1 then",
        '  errmsg("Age %d is inconsistent with birth year %d.", Q2_1_AGE, Q2_BIRTH_YEAR);',
        "  reenter;",
        "endif;",
    ])
    out += _proc("Q2_BIRTH_YEAR", "postproc", [
        "if Q2_BIRTH_YEAR < 1900 or Q2_BIRTH_YEAR > currentYear then",
        '  errmsg("Birth year must be between 1900 and %d.", currentYear);',
        "  reenter;",
        "endif;",
    ])
    out += _proc("Q18_INCOME_BRACKET", "postproc", [
        "{ amount must fall inside the chosen bracket (spec 4.4) }",
        "numeric lo; numeric hi;",
        "if     Q18_INCOME_BRACKET = 1 then lo =      0; hi =    39999;",
        "elseif Q18_INCOME_BRACKET = 2 then lo =  40000; hi =    59999;",
        "elseif Q18_INCOME_BRACKET = 3 then lo =  60000; hi =    99999;",
        "elseif Q18_INCOME_BRACKET = 4 then lo = 100000; hi =   249999;",
        "elseif Q18_INCOME_BRACKET = 5 then lo = 250000; hi =   499999;",
        "elseif Q18_INCOME_BRACKET = 6 then lo = 500000; hi = 99999999;",
        "elseif Q18_INCOME_BRACKET = 7 then lo =      0; hi = 99999999;",
        "endif;",
        "if Q18_INCOME_AMOUNT < lo or Q18_INCOME_AMOUNT > hi then",
        '  errmsg("Amount %d is outside bracket %d (%d-%d). Reenter amount or bracket.",',
        "         Q18_INCOME_AMOUNT, Q18_INCOME_BRACKET, lo, hi);",
        "  reenter;",
        "endif;",
    ])
    out += _proc("Q21_HH_SENIORS", "postproc", [
        "{ household composition invariant (spec 3.3) }",
        "if (Q20_HH_CHILDREN + Q21_HH_SENIORS) > Q19_HH_SIZE_TOTAL then",
        '  errmsg("Children (%d) + Seniors (%d) exceed total HH size (%d).",',
        "         Q20_HH_CHILDREN, Q21_HH_SENIORS, Q19_HH_SIZE_TOTAL);",
        "  reenter;",
        "endif;",
    ])
    out += _proc("Q47_HH_HAS_PRIVATE_INS", "preproc", [
        "{ post-roster count check — roster occurrences must match Q19 (spec 3.4) }",
        "if count(C_HOUSEHOLD_ROSTER) <> Q19_HH_SIZE_TOTAL then",
        '  errmsg("Roster has %d members but Q19 reported %d — reconcile.",',
        "         count(C_HOUSEHOLD_ROSTER), Q19_HH_SIZE_TOTAL);",
        "endif;",
    ])
    return out


def emit_skip_rules(rules, header):
    out = [f"{{ ---- {header} ---- }}"]
    for item, cond, target, comment in rules:
        out += _proc(item, "postproc", [
            f"{{ {comment} }}",
            f"if {cond} then",
            f"  skip to {target};",
            "endif;",
        ])
    return out


def emit_multi_branch_skips():
    out = ["{ ---- Multi-branch skip routing (spec section 2) ---- }"]
    for item, branches, comment in MULTI_BRANCH_SKIPS:
        body = [f"{{ {comment} }}"]
        for cond, target in branches:
            body += [f"if {cond} then", f"  skip to {target};", "endif;"]
        out += _proc(item, "postproc", body)
    return out


def emit_numeric_validations():
    out = ["{ ---- Numeric-range validations (spec section 3) ---- }"]
    by_item = {}
    order = []
    for item, cond, severity, msg in NUMERIC_VALIDATIONS:
        if item not in by_item:
            by_item[item] = []
            order.append(item)
        by_item[item].append((cond, severity, msg))
    for item in order:
        body = []
        for cond, severity, msg in by_item[item]:
            has_arg = "%d" in msg or "%f" in msg
            if severity == "hard":
                arg = f", {item}" if has_arg else ""
                body += [f"if {cond} then", f'  errmsg("{msg}"{arg});',
                         "  reenter;", "endif;"]
            else:
                prompt = f'maketext("{msg}", {item})' if has_arg else f'"{msg}"'
                body += [f"if {cond} then",
                         f'  if accept({prompt}, "Yes", "No") <> 1 then',
                         "    reenter;", "  endif;", "endif;"]
        out += _proc(item, "postproc", body)
    return out


def emit_consumed_gates(dictionary):
    """Section N WHO/SHA expenditure gates (spec section 2 / sanity #8): when
    {prefix}_CONSUMED = No, skip the _PURCHASED_PHP + _INKIND_PHP amount pair.
    Discovered by scanning the DCF — the gate is emitted on _PURCHASED_PHP and
    skips to the item after _INKIND_PHP."""
    out = ["{ ---- Section N — expenditure 'consumed' gates (spec 2 / sanity #8) ---- }"]
    count = 0
    for rec in dictionary["levels"][0]["records"]:
        items = rec["items"]
        for idx, it in enumerate(items):
            if not it["name"].endswith("_CONSUMED"):
                continue
            prefix = it["name"][:-len("_CONSUMED")]
            purchased = f"{prefix}_PURCHASED_PHP"
            inkind = f"{prefix}_INKIND_PHP"
            # the gate skips to the item after _INKIND_PHP
            names = [x["name"] for x in items]
            if purchased not in names or inkind not in names:
                continue
            after_idx = names.index(inkind) + 1
            target = names[after_idx] if after_idx < len(names) else None
            if target is None:
                continue
            out += _proc(purchased, "preproc", [
                f"{{ skip the amount pair when {it['name']} = No }}",
                f"if {it['name']} = 2 then",
                f"  skip to {target};",
                "endif;",
            ])
            count += 1
    return out, count


def emit_subtotals():
    """WHO/SHA panel subtotals (spec 3.15) — auto-computed, read-only."""
    out = ["{ ---- Section N — auto-computed panel subtotals (spec 3.15) ---- }"]
    for subtotal, prefixes in SUBTOTALS:
        terms = []
        for p in prefixes:
            terms.append(f"{p}_PURCHASED_PHP")
            terms.append(f"{p}_INKIND_PHP")
        # chunk the sum across lines for readability
        expr_lines = []
        for i in range(0, len(terms), 4):
            chunk = " + ".join(terms[i:i + 4])
            expr_lines.append(chunk)
        body = [f"{{ auto-computed total of {len(prefixes)} panel rows; read-only }}",
                f"{subtotal} ="]
        for j, ln in enumerate(expr_lines):
            suffix = ";" if j == len(expr_lines) - 1 else " +"
            body.append(f"    {ln}{suffix}")
        body.append("noinput;")
        out += _proc(subtotal, "preproc", body)
    return out


def emit_other_specify(dictionary):
    """'Other (specify)' enforcement (spec section 3). Trigger auto-derived
    from the DCF."""
    out = ["{ ---- 'Other (specify)' enforcement (spec section 3) ---- }"]
    unresolved = 0
    for rec in dictionary["levels"][0]["records"]:
        items = rec["items"]
        for idx, it in enumerate(items):
            name = it["name"]
            if not name.endswith("_OTHER_TXT"):
                continue
            gate = OTHER_SPECIFY_OVERRIDES.get(name) or _other_specify_gate(
                name, items, idx)
            if gate is None:
                out.append(f"{{ NOTE: {name} — parent/'specify' code not "
                           f"resolved; wire manually in bench-test. }}")
                out.append("")
                unresolved += 1
                continue
            parent, code = gate
            out += _proc(name, "postproc", [
                f"if {parent} = {code} and length(strip({name})) = 0 then",
                f'  errmsg("\'Other\' was selected for {parent}. Please specify.");',
                "  reenter;",
                "endif;",
            ])
    return out, unresolved


def _other_specify_gate(txt_name, items, idx):
    """Resolve (parent_item, trigger_code) for a *_OTHER_TXT item."""
    prefix = txt_name[:-len("_OTHER_TXT")]
    siblings = [it for it in items if it["name"].startswith(prefix + "_O")
                and it["name"] != txt_name]
    if siblings:
        for sib in siblings:
            if "specify" in sib["labels"][0]["text"].lower():
                return (sib["name"], 1)
        return None
    if idx == 0:
        return None
    parent = items[idx - 1]
    vss = parent.get("valueSets")
    if not vss:
        return None
    for val in vss[0]["values"]:
        lab = val["labels"][0]["text"].lower()
        if "specify" in lab or "other" in lab:
            return (parent["name"], val["pairs"][0]["value"])
    return None


# ============================================================
# ASSEMBLE
# ============================================================

def build_apc():
    dictionary = build_dictionary_f4()

    lines = []
    lines.append("{ ============================================================")
    lines.append("  HouseholdSurvey.generated.apc — F4 CAPI logic (v1.0, phase 4)")
    lines.append("")
    lines.append("  GENERATED by F4/generate_apc.py — do NOT hand-edit.")
    lines.append("  Patch the generator + F4-Skip-Logic-and-Validations.md, then")
    lines.append("  regenerate. Verified against a paper walkthrough in the")
    lines.append("  bench-test pass (spec section 6).")
    lines.append("  ============================================================ }")
    lines.append("")
    lines += emit_framework()
    lines += emit_psgc_cascade()
    lines += emit_capture()
    lines += emit_section_b()
    lines += emit_skip_rules(SKIP_RULES, "Skip logic (spec section 2)")
    lines += emit_skip_rules(ROSTER_SKIPS,
                             "Household-roster per-member skips (spec section 2)")
    lines += emit_multi_branch_skips()
    lines += emit_numeric_validations()
    cg_lines, cg_count = emit_consumed_gates(dictionary)
    lines += cg_lines
    lines += emit_subtotals()
    os_lines, os_unresolved = emit_other_specify(dictionary)
    lines += os_lines

    proc_headers = [ln[len("PROC "):].strip()
                    for ln in lines if ln.startswith("PROC ")]
    dupes = sorted({p for p in proc_headers if proc_headers.count(p) > 1})
    if dupes:
        raise RuntimeError(
            f"duplicate PROC headers (CSPro allows one PROC per object): {dupes}")
    return ("\r\n".join(lines) + "\r\n", len(proc_headers),
            cg_count, os_unresolved)


def main():
    out_path = Path(__file__).parent / "HouseholdSurvey.generated.apc"
    apc_text, proc_count, cg_count, os_unresolved = build_apc()
    out_path.write_text(apc_text, encoding="utf-8")
    sys.stderr.write(
        f"Wrote {out_path} ({proc_count} PROC blocks; "
        f"{cg_count} expenditure gates; "
        f"{os_unresolved} unresolved Other-specify)\n")


if __name__ == "__main__":
    main()
