"""
generate_apc.py — F3 Patient Survey CSPro logic generator
                  (UHC Survey System v1.0 rebuild — phase 4).

Emits PatientSurvey.generated.apc — the CAPI logic for PatientSurvey.dcf/.fmf,
driven by F3-Skip-Logic-and-Validations.md.

v1.0 note: the F3->F1 linkage is the 9-digit ID prefix (no F3_FACILITY_ID
item), so the spec's section 4.3b F3_FACILITY_ID PROC is not emitted.

Generator-first: output is PatientSurvey.generated.apc. The CSPro Designer /
bench-test pass (spec section 6.5) verifies it against a paper walkthrough.

Run:
    python generate_apc.py        # writes PatientSurvey.generated.apc next to this file
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_dcf import build_dictionary_f3


# ============================================================
# SKIP RULES — single-condition jumps (spec section 2).
# (trigger item, CSPro condition, skip-to target, comment)
# ============================================================

SKIP_RULES = [
    # --- Section A ---
    ("Q1_IS_PATIENT", "Q1_IS_PATIENT = 1", "Q4_NAME",
     "respondent IS the patient -> skip Q2, Q3"),
    # --- Section B ---
    ("Q11_PWD", "Q11_PWD = 2", "Q15_EDUCATION", "Q11 = No -> skip Q12-Q14"),
    ("Q12_PWD_SPECIFY", "Q12_PWD_SPECIFY = 2", "Q15_EDUCATION",
     "Q12 = No -> skip Q13, Q14"),
    ("Q30_IP", "Q30_IP = 2", "Q32_4PS", "Q30 = No -> skip Q31"),
    ("Q33_DECISION_MAKER", "Q33_DECISION_MAKER in 1,3", "Q35_UHC_HEARD",
     "Q33 = patient/companion is decision-maker -> skip Q34"),
    # --- Section C ---
    ("Q35_UHC_HEARD", "Q35_UHC_HEARD = 2", "Q38_PHILHEALTH_REG",
     "Q35 = No -> skip Q36, Q37"),
    # --- Section D ---
    ("Q38_PHILHEALTH_REG", "Q38_PHILHEALTH_REG in 2,3", "Q43_KNOWS_ASSIST",
     "Q38 = non-member -> skip Q39-Q42"),
    ("Q41_REG_DIFFICULTY", "Q41_REG_DIFFICULTY = 2", "Q43_KNOWS_ASSIST",
     "Q41 = No -> skip Q42"),
    ("Q43_KNOWS_ASSIST", "Q43_KNOWS_ASSIST = 2", "Q45_CATEGORY",
     "Q43 = No -> skip Q44"),
    ("Q48_PREMIUM_PAY", "Q48_PREMIUM_PAY = 3", "Q51_OTHER_INSURANCE",
     "Q48 = does not pay premiums -> skip Q49, Q50"),
    ("Q49_PREMIUM_DIFFICULT", "Q49_PREMIUM_DIFFICULT = 2", "Q51_OTHER_INSURANCE",
     "Q49 = No -> skip Q50"),
    ("Q51_OTHER_INSURANCE", "Q51_OTHER_INSURANCE = 2", "Q53_HAS_PCP",
     "Q51 = No -> skip Q52"),
    # --- Section E ---
    ("Q53_HAS_PCP", "Q53_HAS_PCP = 2", "Q63_HAS_USUAL_FACILITY",
     "Q53 = No PCP -> skip Q54-Q62"),
    ("Q66_SAME_AS_USUAL", "Q66_SAME_AS_USUAL = 1", "Q68_USUAL_FAC_TYPE",
     "Q66 = Yes (this is the usual facility) -> skip Q67"),
    ("Q74_KON_HEARD", "Q74_KON_HEARD = 2", "Q83_VISIT_REASON",
     "Q74 = No -> skip Q75-Q82 (exit Section E)"),
    # --- Section G ---
    ("Q93_LABS_O17", "Q93_LABS_O17 = 1", "Q95_PRESCRIBED",
     "Q93 = None -> skip Q94 lab-cost matrix"),
    ("Q95_PRESCRIBED", "Q95_PRESCRIBED = 2", "Q97_FINAL_AMOUNT",
     "Q95 = No -> skip Q96 meds-cost matrix"),
    ("Q99_BUCAS_HEARD", "Q99_BUCAS_HEARD = 2", "Q105_REASON",
     "Q99 = No -> skip Q100-Q104 (end of Section G; spec sanity #9 default)"),
    ("Q102_BUCAS_ACCESSED", "Q102_BUCAS_ACCESSED = 2", "Q104_WITHOUT_BUCAS",
     "Q102 = No -> skip Q103"),
    # --- Section H ---
    ("Q108_MEDS_OUTSIDE", "Q108_MEDS_OUTSIDE = 2", "Q110_LAB_OUTSIDE",
     "Q108 = No -> skip Q109 meds-outside matrix"),
    ("Q110_LAB_OUTSIDE", "Q110_LAB_OUTSIDE = 2", "Q113_PAY_01",
     "Q110 = No -> skip Q111, Q112"),
    # --- Section I ---
    ("Q116_NBB_HEARD", "Q116_NBB_HEARD in 2,3", "Q119_ZBB_HEARD",
     "Q116 not heard -> skip Q117, Q118"),
    ("Q119_ZBB_HEARD", "Q119_ZBB_HEARD in 2,3", "Q124_MAIFIP_HEARD",
     "Q119 not heard -> skip Q120-Q123"),
    ("Q124_MAIFIP_HEARD", "Q124_MAIFIP_HEARD in 2,3", "Q130_REDUCED_SPEND",
     "Q124 not heard -> skip Q125-Q129"),
    ("Q126_MAIFIP_AVAILED", "Q126_MAIFIP_AVAILED = 2", "Q129_WHY_NO_MAIFIP_O01",
     "Q126 = No -> skip Q127, Q128"),
    ("Q127_MAIFIP_OOP", "Q127_MAIFIP_OOP = 2", "Q130_REDUCED_SPEND",
     "Q127 = No -> skip Q128, Q129"),
    # --- Section K ---
    ("Q145_PURCHASE_FREQ", "Q145_PURCHASE_FREQ = 5", "Q152_GAMOT_HEARD",
     "Q145 = Never -> skip Q146-Q151"),
    ("Q152_GAMOT_HEARD", "Q152_GAMOT_HEARD = 2", "Q158_BRAND_GEN_KNOW",
     "Q152 = No -> skip Q153-Q157"),
    ("Q158_BRAND_GEN_KNOW", "Q158_BRAND_GEN_KNOW = 2", "Q162_REFERRED",
     "Q158 = No -> exit Section K"),
    # --- Section L ---
    ("Q169_VISITED", "Q169_VISITED in 2,3", "Q171_WHY_NOT_O01",
     "Q169 = not planning / not yet -> skip Q170"),
    ("Q172_PCP_REFERRAL", "Q172_PCP_REFERRAL = 2", "Q177_WHY_HOSPITAL_O01",
     "Q172 = No -> skip Q173-Q176"),
]


# Multi-branch routing (spec section 2). (item, [(cond, target), ...], comment)
MULTI_BRANCH_SKIPS = [
    ("Q63_HAS_USUAL_FACILITY", [
        ("Q63_HAS_USUAL_FACILITY = 2", "Q65_WHY_NO_USUAL_O01"),
        ("Q63_HAS_USUAL_FACILITY = 1", "Q66_SAME_AS_USUAL"),
    ], "Q63 usual-facility branch: No -> Q65 (skip Q64); Yes -> Q66 (skip Q65)"),
    ("Q77_KON_REGISTERED", [
        ("Q77_KON_REGISTERED = 2", "Q82_KON_WHY_NOT_REG_O01"),
        ("Q77_KON_REGISTERED in 3,4", "Q83_VISIT_REASON"),
    ], "Q77 YAKAP-registration branch: No -> Q82; never-heard/IDK -> Q83"),
    ("Q159_BRAND_GEN_BOUGHT", [
        ("Q159_BRAND_GEN_BOUGHT = 1", "Q161_WHY_BRANDED_O01"),
        ("Q159_BRAND_GEN_BOUGHT = 4", "Q162_REFERRED"),
        ("Q159_BRAND_GEN_BOUGHT = 5", "Q164_SPECIALIST"),
    ], "Q159 branded/generic branch; = 5 (Not applicable) is a cross-section "
       "jump to Q164 per spec sanity #7 -- confirm with ASPSI"),
]


# Branch block gate — non-PhilHealth-members skip the member-only block
# Q45-Q50 (spec section 3.5). (block_first_item, condition, skip_to, comment)
BLOCK_GATES = [
    ("Q45_CATEGORY", "Q38_PHILHEALTH_REG <> 1", "Q51_OTHER_INSURANCE",
     "Q45-Q50 (member category / benefits / premiums) only for PhilHealth members"),
]


# Numeric-range validations (spec section 3). (item, condition, severity, msg)
NUMERIC_VALIDATIONS = [
    # Q6_AGE range is checked in emit_section_b alongside the age-vs-birth rule
    # (CSPro allows only one PROC per item).
    ("Q5_BIRTH_MONTH", "Q5_BIRTH_MONTH < 1 or Q5_BIRTH_MONTH > 12", "hard",
     "Birth month must be 1-12."),
    ("Q19_HH_SIZE", "Q19_HH_SIZE < 1 or Q19_HH_SIZE > 30", "hard",
     "Household size must be between 1 and 30."),
    ("Q19_HH_SIZE", "Q19_HH_SIZE > 15", "soft",
     "Household size %d is unusually large. Confirm?"),
    ("Q58_WAIT_DAYS", "Q58_WAIT_DAYS < 0 or Q58_WAIT_DAYS > 365", "hard",
     "Wait days must be between 0 and 365."),
    ("Q58_WAIT_MINUTES", "Q58_WAIT_MINUTES < 0 or Q58_WAIT_MINUTES > 1440", "hard",
     "Wait minutes must be between 0 and 1440."),
    ("Q69_USUAL_TRAVEL_MM", "Q69_USUAL_TRAVEL_MM < 0 or Q69_USUAL_TRAVEL_MM > 59", "hard",
     "Minutes must be between 0 and 59."),
    ("Q72_NEAREST_TRAVEL_MM", "Q72_NEAREST_TRAVEL_MM < 0 or Q72_NEAREST_TRAVEL_MM > 59", "hard",
     "Minutes must be between 0 and 59."),
    ("Q150_TRAVEL_MM", "Q150_TRAVEL_MM < 0 or Q150_TRAVEL_MM > 59", "hard",
     "Minutes must be between 0 and 59."),
    ("Q106_NIGHTS", "Q106_NIGHTS < 0 or Q106_NIGHTS > 365", "hard",
     "Confinement nights must be between 0 and 365."),
    ("Q106_NIGHTS", "Q106_NIGHTS > 90", "soft",
     "Confinement of %d nights is unusually long. Confirm?"),
    ("Q106_DAYS", "Q106_DAYS < 0 or Q106_DAYS > 365", "hard",
     "Confinement days must be between 0 and 365."),
]


# 'Other (specify)' enforcement overrides — payment-matrix / split-matrix
# _OTHER_TXT items whose trigger is not auto-derivable from item naming.
OTHER_SPECIFY_OVERRIDES = {
    "Q98_OTHER_DONATION_TXT": ("Q98_PAY_06", 1),
    "Q98_OTHER_TXT":          ("Q98_PAY_15", 1),
    "Q971_OTHER_TXT":         ("Q971_4", 1),
    "Q972_OTHER_TXT":         ("Q972_6", 1),
    "Q107_PAY_OTHER_TXT":     ("Q107_PAY_10", 1),
    "Q109_PAY_OTHER_TXT":     ("Q109_PAY_09", 1),
    "Q112_PAY_OTHER_TXT":     ("Q112_PAY_09", 1),
    "Q113_PAY_OTHER_TXT":     ("Q113_PAY_13", 1),
    "Q1141_OTHER_TXT":        ("Q1141_6", 1),
    "Q1142_OTHER_TXT":        ("Q1142_7", 1),
    # select-one whose 'Other' label reads "Others" (no "specify" substring):
    "Q104_WITHOUT_BUCAS_OTHER_TXT": ("Q104_WITHOUT_BUCAS", 6),
    # Q67 carries a redundant explicit other-text alongside the select-all's
    # own Q67_WHY_THIS_FACILITY_OTHER_TXT; gate both on the same "Other" option.
    "Q67_WHY_THIS_OTHER_TXT": ("Q67_WHY_THIS_FACILITY_O08", 1),
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
    """GLOBAL, shared includes, app preproc, FIELD_CONTROL prefill, consent
    terminator, PATIENT_TYPE routing, Q170 explicit skip, Q162/Q178
    terminators, Q113->Q124 MAIFIP auto-set (spec sections 4.1-4.4, 4.10,
    4.15, 4.16)."""
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
    out += _proc("PATIENTSURVEY_FF", "preproc", [
        'currentYYYYMMDD = tonumber(sysdate("YYYYMMDD"));',
        "currentYear  = int(currentYYYYMMDD / 10000);",
        "currentMonth = int(currentYYYYMMDD / 100) % 100;",
    ])
    out += _proc("FIELD_CONTROL", "preproc", [
        "{ prefill the case-control block on first visit (spec 4.16) }",
        'if visualvalue(SURVEY_CODE) = "" then',
        '  SURVEY_CODE       = "F3";',
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
    # PATIENT_TYPE routing (spec 4.4)
    out += _proc("F_HEALTH_SEEKING", "postproc", [
        "{ route to Section G (outpatient) or H (inpatient) — PATIENT_TYPE is",
        "  the authoritative signal }",
        "if PATIENT_TYPE = 1 then",
        "  skip to G_OUTPATIENT_CARE;",
        "elseif PATIENT_TYPE = 2 then",
        "  skip to H_INPATIENT_CARE;",
        "else",
        '  errmsg("PATIENT_TYPE missing — set it in Field Control before advancing.");',
        "  reenter;",
        "endif;",
    ])
    out += _proc("G_OUTPATIENT_CARE", "preproc", [
        "if PATIENT_TYPE <> 1 then skip to I_FINANCIAL_RISK; endif;",
    ])
    out += _proc("H_INPATIENT_CARE", "preproc", [
        "if PATIENT_TYPE <> 2 then skip to I_FINANCIAL_RISK; endif;",
    ])
    # Q113 MAIFIP -> Q124 auto-set (spec 4.10 / sanity #13)
    out += _proc("Q113_PAY_07", "postproc", [
        "{ if MAIFIP was already in the payment list, pre-answer Q124 awareness }",
        "if Q113_PAY_07 = 1 then",
        "  Q124_MAIFIP_HEARD = 1;",
        "endif;",
    ])
    # Q170 explicit skip past Q171 (spec 4.15)
    out += _proc("Q170_FOLLOWUP", "postproc", [
        "skip to Q172_PCP_REFERRAL;   { explicit — Q171 is the not-visited branch }",
    ])
    # Q162 referral-gate terminator (spec 4.15)
    out += _proc("Q162_REFERRED", "postproc", [
        "{ no referral -> survey complete, skip Q163-Q178 }",
        "if Q162_REFERRED = 2 then",
        "  AAPOR_DISPOSITION       = 110;   { Complete interview }",
        "  ENUM_RESULT_FINAL_VISIT = 1;     { Completed }",
        "  skip to SURVEY_TEAM_LEADER_S_NAME;",
        "endif;",
    ])
    # Q178 end-of-survey completion (spec 4.15)
    out += _proc("Q178_SAT_REFERRAL", "postproc", [
        "{ end of Section L — mark the case complete }",
        "AAPOR_DISPOSITION       = 110;",
        "ENUM_RESULT_FINAL_VISIT = 1;",
    ])
    return out


def emit_psgc_cascade():
    """PSGC cascade onfocus handlers — facility chain + patient-home chain
    (spec 4.3). Region items are level IDs; barangay + the P_ family live in
    PATIENT_GEO_ID."""
    out = ["{ ---- PSGC cascade (spec 4.3) ---- }"]
    out += _proc("PROVINCE_HUC_CODE", "onfocus",
                 ["FillProvinceValueSet(PROVINCE_HUC_CODE, REGION_CODE);"])
    out += _proc("CITY_MUNICIPALITY_CODE", "onfocus",
                 ["FillCityValueSet(CITY_MUNICIPALITY_CODE, PROVINCE_HUC_CODE);"])
    out += _proc("BARANGAY_CODE", "onfocus",
                 ["FillBarangayValueSet(BARANGAY_CODE, CITY_MUNICIPALITY_CODE);"])
    out += _proc("P_PROVINCE_HUC_CODE", "onfocus",
                 ["FillProvinceValueSet(P_PROVINCE_HUC_CODE, P_REGION_CODE);"])
    out += _proc("P_CITY_MUNICIPALITY_CODE", "onfocus",
                 ["FillCityValueSet(P_CITY_MUNICIPALITY_CODE, P_PROVINCE_HUC_CODE);"])
    out += _proc("P_BARANGAY_CODE", "onfocus",
                 ["FillBarangayValueSet(P_BARANGAY_CODE, P_CITY_MUNICIPALITY_CODE);"])
    return out


def _gps_capture_proc(trigger, prefix):
    return _proc(trigger, "onfocus", [
        "if ReadGPSReading(120, 20) then",
        f'  {prefix}GPS_LATITUDE   = maketext("%f", gps(latitude));',
        f'  {prefix}GPS_LONGITUDE  = maketext("%f", gps(longitude));',
        f'  {prefix}GPS_ALTITUDE   = maketext("%f", gps(altitude));',
        f"  {prefix}GPS_ACCURACY   = gps(accuracy);",
        f"  {prefix}GPS_SATELLITES = gps(satellites);",
        f"  {prefix}GPS_READTIME   = gps(readtime);",
        "endif;",
        f"{trigger} = notappl;   {{ re-arm the trigger }}",
    ])


def emit_capture():
    """GPS (facility + patient home) + verification photo (spec 4.3a)."""
    out = ["{ ---- GPS + verification photo capture (spec 4.3a) ---- }"]
    out += _gps_capture_proc("FACILITY_CAPTURE_GPS", "FACILITY_")
    out += _gps_capture_proc("P_HOME_CAPTURE_GPS", "P_HOME_")
    for prefix in ("FACILITY_", "P_HOME_"):
        trigger = f"{prefix}CAPTURE_GPS"
        out += _proc(f"{prefix}GPS_LATITUDE", "postproc", [
            "numeric lat;",
            f"lat = tonumber({prefix}GPS_LATITUDE);",
            "if lat <> notappl and (lat < 4.5 or lat > 21.5) then",
            f'  errmsg("Latitude %f is outside the Philippine bounding box — re-capture.", lat);',
            f"  move to {trigger};",
            "endif;",
        ])
        out += _proc(f"{prefix}GPS_LONGITUDE", "postproc", [
            "numeric lon;",
            f"lon = tonumber({prefix}GPS_LONGITUDE);",
            "if lon <> notappl and (lon < 116.5 or lon > 127.0) then",
            f'  errmsg("Longitude %f is outside the Philippine bounding box — re-capture.", lon);',
            f"  move to {trigger};",
            "endif;",
        ])
        out += _proc(f"{prefix}GPS_ACCURACY", "postproc", [
            f"if {prefix}GPS_ACCURACY <> notappl and {prefix}GPS_ACCURACY > 30 then",
            f'  errmsg("GPS accuracy %d m is poor (> 30 m). Re-read outdoors recommended.", {prefix}GPS_ACCURACY);',
            "endif;",
        ])
        out += _proc(f"{prefix}GPS_SATELLITES", "postproc", [
            f"if {prefix}GPS_SATELLITES <> notappl and {prefix}GPS_SATELLITES < 4 then",
            f'  errmsg("Only %d GPS satellites — fix below the reliable minimum.", {prefix}GPS_SATELLITES);',
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
    """Section B cross-field consistency (spec 4.6, 4.7) + Q5/Q6 age-vs-birth."""
    out = ["{ ---- Section B — cross-field consistency (spec 4.6, 4.7) ---- }"]
    out += _proc("Q6_AGE", "postproc", [
        "if Q6_AGE < 0 or Q6_AGE > 120 then",
        '  errmsg("Patient age must be between 0 and 120.");',
        "  reenter;",
        "endif;",
        "{ age vs birth-year consistency (allow +/-1 for not-yet-birthday) }",
        "if Q5_BIRTH_YEAR > 0 and",
        "   abs((currentYear - Q5_BIRTH_YEAR) - Q6_AGE) > 1 then",
        '  errmsg("Age %d is inconsistent with birth year %d.", Q6_AGE, Q5_BIRTH_YEAR);',
        "  reenter;",
        "endif;",
    ])
    out += _proc("Q5_BIRTH_YEAR", "postproc", [
        "if Q5_BIRTH_YEAR < 1900 or Q5_BIRTH_YEAR > currentYear then",
        '  errmsg("Birth year must be between 1900 and %d.", currentYear);',
        "  reenter;",
        "endif;",
    ])
    out += _proc("Q18_INCOME_BRACKET", "postproc", [
        "{ amount must fall inside the chosen bracket (spec 4.6) }",
        "numeric lo; numeric hi;",
        "if     Q18_INCOME_BRACKET = 1 then lo =      0; hi =    39999;",
        "elseif Q18_INCOME_BRACKET = 2 then lo =  40000; hi =    59999;",
        "elseif Q18_INCOME_BRACKET = 3 then lo =  60000; hi =    99999;",
        "elseif Q18_INCOME_BRACKET = 4 then lo = 100000; hi =   249999;",
        "elseif Q18_INCOME_BRACKET = 5 then lo = 250000; hi =   499999;",
        "elseif Q18_INCOME_BRACKET = 6 then lo = 500000; hi = 99999999;",
        "endif;",
        "if Q18_INCOME_AMOUNT < lo or Q18_INCOME_AMOUNT > hi then",
        '  errmsg("Amount %d is outside bracket %d (%d-%d). Reenter amount or bracket.",',
        "         Q18_INCOME_AMOUNT, Q18_INCOME_BRACKET, lo, hi);",
        "  reenter;",
        "endif;",
    ])
    out += _proc("Q21_HH_SENIORS", "postproc", [
        "{ household composition invariant (spec 4.7) }",
        "if (Q20_HH_CHILDREN + Q21_HH_SENIORS) > Q19_HH_SIZE then",
        '  errmsg("Children (%d) + Seniors (%d) exceed total HH size (%d).",',
        "         Q20_HH_CHILDREN, Q21_HH_SENIORS, Q19_HH_SIZE);",
        "  reenter;",
        "endif;",
    ])
    return out


def emit_skip_rules():
    out = ["{ ---- Skip logic (spec section 2) ---- }"]
    for item, cond, target, comment in SKIP_RULES:
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


def emit_block_gates():
    out = ["{ ---- Branch block gates (spec section 3) ---- }"]
    for first_item, cond, target, comment in BLOCK_GATES:
        out += _proc(first_item, "preproc", [
            f"{{ {comment} }}",
            f"if {cond} then",
            f"  skip to {target};",
            "endif;",
        ])
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


def emit_payment_matrix(dictionary):
    """Payment-source matrix enforcement (spec 4.10): for every {flag}/{flag}_AMT
    pair, flag = Yes <=> amount > 0. Discovered by scanning the DCF for
    *_AMT items with a sibling flag item."""
    out = ["{ ---- Payment-source matrix flag<->amount rules (spec 4.10) ---- }"]
    item_names = set()
    for rec in dictionary["levels"][0]["records"]:
        item_names |= {it["name"] for it in rec["items"]}
    amt_items = sorted(n for n in item_names
                       if n.endswith("_AMT") and n[:-4] in item_names)
    for amt in amt_items:
        flag = amt[:-4]
        out += _proc(amt, "postproc", [
            f"if {flag} = 1 and {amt} <= 0 then",
            f'  errmsg("{flag} flagged but amount is 0 — enter a positive peso amount.");',
            "  reenter;",
            "endif;",
            f"if {flag} = 2 and {amt} > 0 then",
            f'  errmsg("Amount entered for an unused payment source — clear it or flag the source.");',
            "  reenter;",
            "endif;",
        ])
    return out, len(amt_items)


def emit_other_specify(dictionary):
    """'Other (specify)' enforcement (spec 4.9). Trigger resolved from the
    override table first, then auto-derived from the DCF."""
    out = ["{ ---- 'Other (specify)' enforcement (spec 4.9) ---- }"]
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
    """Resolve (parent_item, trigger_code) for a *_OTHER_TXT item — select-all
    'Other' option sibling, else the preceding select-one item."""
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
        if "specify" in val["labels"][0]["text"].lower():
            return (parent["name"], val["pairs"][0]["value"])
    return None


# ============================================================
# ASSEMBLE
# ============================================================

def build_apc():
    dictionary = build_dictionary_f3()

    lines = []
    lines.append("{ ============================================================")
    lines.append("  PatientSurvey.generated.apc — F3 CAPI logic (v1.0, phase 4)")
    lines.append("")
    lines.append("  GENERATED by F3/generate_apc.py — do NOT hand-edit.")
    lines.append("  Patch the generator + F3-Skip-Logic-and-Validations.md, then")
    lines.append("  regenerate. Verified against a paper walkthrough in the")
    lines.append("  bench-test pass (spec section 6.5).")
    lines.append("  ============================================================ }")
    lines.append("")
    lines += emit_framework()
    lines += emit_psgc_cascade()
    lines += emit_capture()
    lines += emit_section_b()
    lines += emit_skip_rules()
    lines += emit_multi_branch_skips()
    lines += emit_block_gates()
    lines += emit_numeric_validations()
    pm_lines, pm_count = emit_payment_matrix(dictionary)
    lines += pm_lines
    os_lines, os_unresolved = emit_other_specify(dictionary)
    lines += os_lines

    proc_headers = [ln[len("PROC "):].strip()
                    for ln in lines if ln.startswith("PROC ")]
    dupes = sorted({p for p in proc_headers if proc_headers.count(p) > 1})
    if dupes:
        raise RuntimeError(
            f"duplicate PROC headers (CSPro allows one PROC per object): {dupes}")
    return ("\r\n".join(lines) + "\r\n", len(proc_headers),
            pm_count, os_unresolved)


def main():
    out_path = Path(__file__).parent / "PatientSurvey.generated.apc"
    apc_text, proc_count, pm_count, os_unresolved = build_apc()
    out_path.write_text(apc_text, encoding="utf-8")
    sys.stderr.write(
        f"Wrote {out_path} ({proc_count} PROC blocks; "
        f"{pm_count} payment-matrix rows; "
        f"{os_unresolved} unresolved Other-specify)\n")


if __name__ == "__main__":
    main()
