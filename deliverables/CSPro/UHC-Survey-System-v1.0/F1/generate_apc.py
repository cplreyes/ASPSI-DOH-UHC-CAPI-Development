"""
generate_apc.py — F1 Facility Head Survey CSPro logic generator
                  (UHC Survey System v1.0 rebuild — phase 4).

Emits FacilityHeadSurvey.generated.apc — the CAPI logic (skip rules, gates,
validations, capture wiring) for FacilityHeadSurvey.dcf / .fmf.

Driven by F1-Skip-Logic-and-Validations.md (the reviewed logic spec). The
generator builds the PROC blocks from data tables + the spec's section-4
templates; item names are pulled live from the DCF so they always match.

Generator-first: the output is FacilityHeadSurvey.generated.apc. The CSPro
Designer / bench-test pass (spec section 6.5) verifies it against a paper
walkthrough and wires it into the .app — it does not hand-edit this file.

Run:
    python generate_apc.py        # writes FacilityHeadSurvey.generated.apc next to this file
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_dcf import build_dictionary_f1


# ============================================================
# SKIP RULES — from F1-Skip-Logic-and-Validations.md section 2.
# Each rule: trigger item, CSPro condition, skip-to target item.
# ============================================================

SKIP_RULES = [
    # --- Section C — UHC Implementation ---
    ("Q10_HAS_PRIMARY_PKG",  "Q10_HAS_PRIMARY_PKG = 2",   "Q12_PCB_LICENSING",
     "Q10 = No -> skip Q11"),
    ("Q13_PUBLIC_HEALTH_UNIT", "Q13_PUBLIC_HEALTH_UNIT in 2,9", "Q16_HEALTH_PROMO_UNIT",
     "Q13 = No/NA -> skip Q14, Q15"),
    ("Q14_PHU_CREATED",  "Q14_PHU_CREATED in 5:9",  "Q16_HEALTH_PROMO_UNIT",
     "Q14 in No/IDK/NA branches -> skip Q15"),
    ("Q16_HEALTH_PROMO_UNIT", "Q16_HEALTH_PROMO_UNIT in 2,9", "Q19_NEW_ROLES",
     "Q16 = No/NA -> skip Q17, Q18"),
    ("Q17_HPU_CREATED",  "Q17_HPU_CREATED in 5:9",  "Q19_NEW_ROLES",
     "Q17 in No/IDK/NA branches -> skip Q18"),
    ("Q19_NEW_ROLES",    "Q19_NEW_ROLES in 5:9",    "Q21_NEW_DEPTS",
     "Q19 in No/IDK/NA branches -> skip Q20"),
    ("Q21_NEW_DEPTS",    "Q21_NEW_DEPTS in 5:9",    "Q23_NEW_BUILDINGS",
     "Q21 in No/IDK/NA branches -> skip Q22"),
    ("Q23_NEW_BUILDINGS", "Q23_NEW_BUILDINGS in 5:9", "Q25_NEW_ROOMS",
     "Q23 in No/IDK/NA branches -> skip Q24"),
    ("Q25_NEW_ROOMS",    "Q25_NEW_ROOMS in 5:9",    "Q27_INC_EQUIPMENT",
     "Q25 in No/IDK/NA branches -> skip Q26"),
    ("Q27_INC_EQUIPMENT", "Q27_INC_EQUIPMENT in 5:9", "Q29_INC_SUPPLIES",
     "Q27 in No/IDK/NA branches -> skip Q28"),
    ("Q29_INC_SUPPLIES", "Q29_INC_SUPPLIES in 5:9", "Q31_EMR_USE",
     "Q29 in No/IDK/NA branches -> skip Q30"),
    ("Q31_EMR_USE",      "Q31_EMR_USE in 5:9",      "Q35_STAFFING_CHANGED",
     "Q31 in No/IDK/NA branches (NA per Bug #4) -> skip Q32-Q34"),
    ("Q32_DATA_SUBMIT",  "Q32_DATA_SUBMIT = 4",     "Q35_STAFFING_CHANGED",
     "Q32 = not submitting -> skip Q33, Q34"),
    ("Q35_STAFFING_CHANGED", "Q35_STAFFING_CHANGED = 2", "Q37_REFERRAL_CHANGED",
     "Q35 = No -> skip Q36"),
    ("Q37_REFERRAL_CHANGED", "Q37_REFERRAL_CHANGED = 2", "Q39_MOU_MOA",
     "Q37 = No -> skip Q38"),

    # --- Section D — YAKAP / Konsulta ---
    ("Q51_YK_ACCRED",    "Q51_YK_ACCRED = 2",       "Q79_NOT_ACCRED_REASON_O01",
     "Q51 = No -> non-accredited path; skip Q52-Q78"),
    ("Q59_KNOW_PAY_FREQ", "Q59_KNOW_PAY_FREQ = 2",  "Q61_TRANCHE_DELAY",
     "Q59 = No -> skip Q60"),
    ("Q61_TRANCHE_DELAY", "Q61_TRANCHE_DELAY = 2",  "Q62_TRANCHE_INTERVAL",
     "Q61 = No -> skip Q61.1 reason text"),
    ("Q77_ENROLL_CHALL", "Q77_ENROLL_CHALL = 2",    "Q85_CATCHMENT_AREA",
     "Q77 = No -> skip Q78"),
    ("Q89_COSTING_DONE", "Q89_COSTING_DONE = 2",    "Q91_MIN_CAP_VALUE_ACC",
     "Q89 = No -> skip Q90"),
    ("Q93_CHARGE_ADDL_CAP", "Q93_CHARGE_ADDL_CAP = 2", "Q95_RECEIVED_PAYMENTS",
     "Q93 = No -> skip Q94"),
    ("Q95_RECEIVED_PAYMENTS", "Q95_RECEIVED_PAYMENTS in 1,2", "Q97_PAYMENT_CHALL",
     "Q95 = received all/some -> skip Q96"),
    ("Q97_PAYMENT_CHALL", "Q97_PAYMENT_CHALL = 2",  "Q99_EXPAND_NEXT_O01",
     "Q97 = No -> skip Q98"),

    # --- Section E — BUCAS / GAMOT ---
    ("Q101_HEARD_BUCAS", "Q101_HEARD_BUCAS = 2",    "Q108_HEARD_GAMOT",
     "Q101 = No -> skip Q102-Q107"),
    ("Q108_HEARD_GAMOT", "Q108_HEARD_GAMOT = 2",    "Q112_STOCKOUT",
     "Q108 = No -> skip Q109-Q111"),
    ("Q112_STOCKOUT",    "Q112_STOCKOUT = 2",       "Q118_DOH_LICENSED",
     "Q112 = No -> skip Q113-Q117"),
    ("Q116_ADDR_STOCKOUT", "Q116_ADDR_STOCKOUT in 2,3", "Q118_DOH_LICENSED",
     "Q116 = No / Did not experience stock-outs -> skip Q117"),

    # --- Section F — DOH Licensing ---
    ("Q118_DOH_LICENSED", "Q118_DOH_LICENSED in 2,3,4", "Q135_NBB_CURR",
     "Q118 not licensed -> skip Q119-Q134"),

    # --- Section G — Service Delivery ---
    ("Q135_NBB_CURR",    "Q135_NBB_CURR = 2",       "Q138_ZBB_CURR",
     "Q135 = No -> skip Q136, Q137"),
    ("Q138_ZBB_CURR",    "Q138_ZBB_CURR = 2",       "Q141_ALLOW_OOP_BASIC",
     "Q138 = No -> skip Q139, Q140"),
    ("Q141_ALLOW_OOP_BASIC", "Q141_ALLOW_OOP_BASIC = 2", "Q143_DIFFICULT_BENEFIT",
     "Q141 = No -> skip Q142"),
    ("Q148_LGU_SUPPORT", "Q148_LGU_SUPPORT = 2",    "Q152_PHO_PROTOCOL_CLARITY",
     "Q148 = No -> skip Q149-Q151"),
    ("Q150_LGU_SATISFIED", "Q150_LGU_SATISFIED = 1", "Q154_NUM_REFERRED_OUT",
     "Q150 = Yes -> skip Q151"),
    ("Q152_PHO_PROTOCOL_CLARITY", "Q152_PHO_PROTOCOL_CLARITY in 1,2", "Q154_NUM_REFERRED_OUT",
     "Q152 = Very Clear/Clear -> skip Q153 (spec: implied, confirm with ASPSI)"),
    ("Q161_REF_SATISFACTION", "Q161_REF_SATISFACTION in 1,2", "Q163_HR_CHALL_O01",
     "Q161 = Very Satisfied/Satisfied -> skip Q162; Section H starts"),
]


# Select-all-driven skips: "None of the above" option selected -> skip the
# dependent why-difficult cluster. Keyed on the None option item.
SELECT_ALL_NONE_SKIPS = [
    ("Q65_ACCRED_DIFFICULT_O10", "Q75_ENROLL_RESPONSIBILITY_O01",
     "Q65 = None of the above only -> skip Q66-Q74"),
    ("Q121_DOH_LIC_DIFFICULT_O14", "Q135_NBB_CURR",
     "Q121 = None of the above only -> skip Q122-Q134"),
]


# Per-option "why-difficult" GATEs (spec section 4.10): each Q66-Q74 / Q122-Q134
# select-all block is entered only if the corresponding option was flagged in
# its parent select-all. (gate_option_item, gated_block_prefix)
WHY_DIFFICULT_GATES = [
    ("Q65_ACCRED_DIFFICULT_O01", "Q66_WHY_DIFF_PREVENTIVE"),
    ("Q65_ACCRED_DIFFICULT_O02", "Q67_WHY_DIFF_LAB"),
    ("Q65_ACCRED_DIFFICULT_O03", "Q68_WHY_DIFF_MEDS"),
    ("Q65_ACCRED_DIFFICULT_O04", "Q69_WHY_DIFF_INFRA"),
    ("Q65_ACCRED_DIFFICULT_O05", "Q70_WHY_DIFF_EQUIPMENT"),
    ("Q65_ACCRED_DIFFICULT_O06", "Q71_WHY_DIFF_HR"),
    ("Q65_ACCRED_DIFFICULT_O07", "Q72_WHY_DIFF_HIS"),
    ("Q65_ACCRED_DIFFICULT_O08", "Q73_WHY_DIFF_DOCS"),
    ("Q65_ACCRED_DIFFICULT_O09", "Q74_WHY_DIFF_DOH_LIC"),
    ("Q121_DOH_LIC_DIFFICULT_O01", "Q122_WHY_DIFF_PT_RIGHTS"),
    ("Q121_DOH_LIC_DIFFICULT_O02", "Q123_WHY_DIFF_PT_CARE"),
    ("Q121_DOH_LIC_DIFFICULT_O03", "Q124_WHY_DIFF_LEADERSHIP"),
    ("Q121_DOH_LIC_DIFFICULT_O04", "Q125_WHY_DIFF_HRM"),
    ("Q121_DOH_LIC_DIFFICULT_O05", "Q126_WHY_DIFF_INFO_MGMT"),
    ("Q121_DOH_LIC_DIFFICULT_O06", "Q127_WHY_DIFF_SAFE"),
    ("Q121_DOH_LIC_DIFFICULT_O07", "Q128_WHY_DIFF_PERF"),
    ("Q121_DOH_LIC_DIFFICULT_O08", "Q129_WHY_DIFF_PHYS_PLANT"),
    ("Q121_DOH_LIC_DIFFICULT_O09", "Q130_WHY_DIFF_PRICE_INFO"),
    ("Q121_DOH_LIC_DIFFICULT_O10", "Q131_WHY_DIFF_EQUIPMENT"),
    ("Q121_DOH_LIC_DIFFICULT_O11", "Q132_WHY_DIFF_NAT_LAWS"),
    ("Q121_DOH_LIC_DIFFICULT_O12", "Q133_WHY_DIFF_EMERG_CART"),
    ("Q121_DOH_LIC_DIFFICULT_O13", "Q134_WHY_DIFF_ADDONS"),
]


# Multi-branch skip routing (spec section 2) — items whose answer routes to one
# of several destinations. (item, [(cspro_condition, skip_to), ...], comment).
# A branch that would skip to the immediately-following item is omitted (it is
# natural flow); such cases are noted in the comment.
MULTI_BRANCH_SKIPS = [
    ("Q80_INTEND_ACCRED", [
        ("Q80_INTEND_ACCRED in 1,2", "Q84_PROCESS_CHALL"),
        ("Q80_INTEND_ACCRED = 3",    "Q82_DECIDED_NOT_REASON"),
        ("Q80_INTEND_ACCRED = 4",    "Q83_TRIED_FAILED_REASON"),
        ("Q80_INTEND_ACCRED = 6",    "Q85_CATCHMENT_AREA"),
    ], "Q80 intent-to-accredit 5-way routing; = 5 (haven't thought about it) "
       "falls through to Q81"),
    ("Q90_COSTING_VIABLE", [
        ("Q90_COSTING_VIABLE = 3", "Q93_CHARGE_ADDL_CAP"),
        ("Q90_COSTING_VIABLE = 2 and Q51_YK_ACCRED = 2", "Q92_MIN_CAP_VALUE_NONACC"),
    ], "Q90 costing-viability routing; = Yes (Q51=Yes) falls through to Q91. "
       "The Yes/Q51=No and No/Q51=Yes combinations are unspecified in the spec "
       "-- confirm in bench-test"),
    ("Q102_HAS_BUCAS", [
        ("Q102_HAS_BUCAS = 1", "Q104_BUCAS_SERVICES_O01"),
        ("Q102_HAS_BUCAS = 3", "Q108_HEARD_GAMOT"),
    ], "Q102 BUCAS-center routing; = No flows into Q103, then the Q104 block "
       "gate routes to Q108"),
    ("Q109_GAMOT_ACCRED", [
        ("Q109_GAMOT_ACCRED = 1", "Q111_GAMOT_FACTORS_O01"),
    ], "Q109 GAMOT-accreditation routing; = No flows into Q110, then the Q111 "
       "block gate routes to Q112"),
    ("Q145_MALASAKIT_PROVIDED", [
        ("Q145_MALASAKIT_PROVIDED = 2", "Q147_NO_MALASAKIT_WHY_O01"),
    ], "Q145 Malasakit branch; = Yes flows into Q146, then the Q147 block gate "
       "routes to Q148"),
]


# Branch block gates (spec section 2) — a select-all block entered only on one
# branch; the other branch reaches the block-first item and must skip past it.
# (block_first_item, cspro_condition_to_skip, skip_to, comment).
BLOCK_GATES = [
    ("Q104_BUCAS_SERVICES_O01", "Q102_HAS_BUCAS <> 1", "Q108_HEARD_GAMOT",
     "Q104-Q107 only when a BUCAS center exists (Q102 = Yes)"),
    ("Q111_GAMOT_FACTORS_O01", "Q109_GAMOT_ACCRED <> 1", "Q112_STOCKOUT",
     "Q111 only when GAMOT-accredited (Q109 = Yes)"),
    ("Q147_NO_MALASAKIT_WHY_O01", "Q145_MALASAKIT_PROVIDED <> 2", "Q148_LGU_SUPPORT",
     "Q147 only when Malasakit is NOT provided (Q145 = No)"),
]


# Numeric-range validations (spec section 3). (item, cspro_condition,
# severity, message). severity: "hard" -> errmsg + reenter; "soft" -> accept.
NUMERIC_VALIDATIONS = [
    ("Q3_AGE", "Q3_AGE < 18 or Q3_AGE > 90", "hard",
     "Facility head age must be between 18 and 90."),
    ("Q3_AGE", "Q3_AGE > 75", "soft",
     "Age %d is unusually old for an active facility head. Confirm?"),
    ("Q57_CAPITATION_AMT", "Q57_CAPITATION_AMT > 5000", "hard",
     "Capitation %d PHP is implausibly high. Reenter."),
    ("Q57_CAPITATION_AMT", "Q57_CAPITATION_AMT > 1700", "soft",
     "Capitation %d exceeds the PHP 1,700 PhilHealth max. Confirm?"),
    ("Q91_MIN_CAP_VALUE_ACC", "Q91_MIN_CAP_VALUE_ACC > 50000", "hard",
     "Minimum acceptable capitation %d PHP is implausibly high. Reenter."),
    ("Q91_MIN_CAP_VALUE_ACC", "Q91_MIN_CAP_VALUE_ACC > 5000", "soft",
     "Minimum acceptable capitation %d PHP is high. Confirm?"),
    ("Q92_MIN_CAP_VALUE_NONACC", "Q92_MIN_CAP_VALUE_NONACC > 50000", "hard",
     "Minimum acceptable capitation %d PHP is implausibly high. Reenter."),
    ("Q92_MIN_CAP_VALUE_NONACC", "Q92_MIN_CAP_VALUE_NONACC > 5000", "soft",
     "Minimum acceptable capitation %d PHP is high. Confirm?"),
    ("Q154_NUM_REFERRED_OUT", "Q154_NUM_REFERRED_OUT > 100000", "hard",
     "Referrals out (%d) over 6 months is implausibly high. Reenter."),
    ("Q154_NUM_REFERRED_OUT", "Q154_NUM_REFERRED_OUT > 10000", "soft",
     "Referrals out (%d) over 6 months is high. Confirm?"),
]


# ============================================================
# EMITTERS
# ============================================================

def _proc(name, block, body_lines, *, end=None):
    """Emit a `PROC name / <block>` chunk. body_lines is a list of code lines
    (already indented relative to the block)."""
    out = [f"PROC {name}", f"{block}"]
    out.extend(f"  {ln}" if ln else "" for ln in body_lines)
    if end:
        out.append(end)
    out.append("")
    return out


def emit_framework():
    """GLOBAL vars, shared includes, app preproc, FIELD_CONTROL preproc,
    consent terminator. Spec sections 4.1, 4.14, 4.17."""
    out = []
    out.append("{ ---- shared helper includes (spec 4.15, 4.16) ---- }")
    out.append('#include "../../shared/PSGC-Cascade.apc"')
    out.append('#include "../../shared/Capture-Helpers.apc"')
    out.append("")
    out.append("PROC GLOBAL")
    out.append("numeric currentYYYYMMDD;")
    out.append("numeric currentYear;")
    out.append("numeric currentMonth;")
    out.append("")
    out += _proc("FACILITYHEADSURVEY_FF", "preproc", [
        "{ application entry — cache the current date for downstream checks }",
        'currentYYYYMMDD = tonumber(sysdate("YYYYMMDD"));',
        "currentYear  = int(currentYYYYMMDD / 10000);",
        "currentMonth = int(currentYYYYMMDD / 100) % 100;",
    ])
    out += _proc("FIELD_CONTROL", "preproc", [
        "{ prefill the case-control block on first visit (spec 4.17) }",
        'if visualvalue(SURVEY_CODE) = "" then',
        '  SURVEY_CODE       = "F1";',
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
    return out


def emit_psgc_cascade():
    """PSGC cascade onfocus handlers for the v1.0 ID items + barangay
    (spec 4.15). REGION_CODE/PROVINCE_HUC_CODE/CITY_MUNICIPALITY_CODE are
    level ID items; BARANGAY_CODE is in HEALTH_FACILITY_GEO."""
    out = ["{ ---- PSGC cascade (spec 4.15) — value sets filled on focus ---- }"]
    out += _proc("PROVINCE_HUC_CODE", "onfocus", [
        "FillProvinceValueSet(PROVINCE_HUC_CODE, REGION_CODE);"])
    out += _proc("CITY_MUNICIPALITY_CODE", "onfocus", [
        "FillCityValueSet(CITY_MUNICIPALITY_CODE, PROVINCE_HUC_CODE);"])
    out += _proc("BARANGAY_CODE", "onfocus", [
        "FillBarangayValueSet(BARANGAY_CODE, CITY_MUNICIPALITY_CODE);"])
    return out


def emit_capture():
    """GPS + verification-photo capture wiring (spec 4.16)."""
    out = ["{ ---- GPS + verification photo capture (spec 4.16) ---- }"]
    out += _proc("FACILITY_CAPTURE_GPS", "onfocus", [
        "if ReadGPSReading(120, 20) then",
        '  FACILITY_GPS_LATITUDE   = maketext("%f", gps(latitude));',
        '  FACILITY_GPS_LONGITUDE  = maketext("%f", gps(longitude));',
        '  FACILITY_GPS_ALTITUDE   = maketext("%f", gps(altitude));',
        "  FACILITY_GPS_ACCURACY   = gps(accuracy);",
        "  FACILITY_GPS_SATELLITES = gps(satellites);",
        "  FACILITY_GPS_READTIME   = gps(readtime);",
        "endif;",
        "FACILITY_CAPTURE_GPS = notappl;   { re-arm the trigger }",
    ])
    out += _proc("FACILITY_GPS_LATITUDE", "postproc", [
        "numeric lat;",
        "lat = tonumber(FACILITY_GPS_LATITUDE);",
        "if lat <> notappl and (lat < 4.5 or lat > 21.5) then",
        '  errmsg("Facility latitude %f is outside the Philippine bounding box — re-capture.", lat);',
        "  move to FACILITY_CAPTURE_GPS;",
        "endif;",
    ])
    out += _proc("FACILITY_GPS_LONGITUDE", "postproc", [
        "numeric lon;",
        "lon = tonumber(FACILITY_GPS_LONGITUDE);",
        "if lon <> notappl and (lon < 116.5 or lon > 127.0) then",
        '  errmsg("Facility longitude %f is outside the Philippine bounding box — re-capture.", lon);',
        "  move to FACILITY_CAPTURE_GPS;",
        "endif;",
    ])
    out += _proc("FACILITY_GPS_ACCURACY", "postproc", [
        "if FACILITY_GPS_ACCURACY <> notappl and FACILITY_GPS_ACCURACY > 30 then",
        '  errmsg("GPS accuracy %d m is poor (> 30 m). Re-read outdoors recommended.", FACILITY_GPS_ACCURACY);',
        "endif;",
    ])
    out += _proc("FACILITY_GPS_SATELLITES", "postproc", [
        "if FACILITY_GPS_SATELLITES <> notappl and FACILITY_GPS_SATELLITES < 4 then",
        '  errmsg("Only %d GPS satellites — fix is below the minimum for a reliable reading.", FACILITY_GPS_SATELLITES);',
        "endif;",
    ])
    out += _proc("CAPTURE_VERIFICATION_PHOTO", "onfocus", [
        "string fn;",
        'fn = "case-" + maketext("%02d%02d%03d%02d%03d", REGION_CODE, PROVINCE_HUC_CODE,',
        "          CITY_MUNICIPALITY_CODE, FACILITY_NO, CASE_SEQ) + \"-verification.jpg\";",
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


def emit_section_a():
    """Section A eligibility + tenure validations (spec 4.2, 4.3)."""
    out = ["{ ---- Section A — eligibility + tenure (spec 4.2, 4.3) ---- }"]
    out += _proc("Q5_MONTHS_AT_FACILITY", "postproc", [
        "{ <6 months tenure terminates the interview (IR eligibility rule) }",
        "if (Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY) < 6 then",
        "  AAPOR_DISPOSITION       = 230;   { eligible non-interview }",
        "  ENUM_RESULT_FINAL_VISIT = 4;     { Incomplete }",
        '  errmsg("Respondent must have >= 6 months in the current position. End interview, code Refused/Incomplete.");',
        "  skip to SURVEY_TEAM_LEADER_S_NAME;",
        "endif;",
        "if Q5_YEARS_AT_FACILITY > (Q3_AGE - 18) then",
        '  errmsg("Years at facility (%d) exceeds working-age years available (%d). Reenter.",',
        "         Q5_YEARS_AT_FACILITY, Q3_AGE - 18);",
        "  reenter;",
        "endif;",
    ])
    out += _proc("Q6_MONTHS_HEALTH", "postproc", [
        "numeric tenureMos;",
        "numeric healthMos;",
        "tenureMos = Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY;",
        "healthMos = Q6_YEARS_HEALTH * 12 + Q6_MONTHS_HEALTH;",
        "if healthMos < tenureMos then",
        '  errmsg("Years in any health-related role (%d mos) cannot be less than years at this facility (%d mos).",',
        "         healthMos, tenureMos);",
        "  reenter;",
        "endif;",
        "if Q6_YEARS_HEALTH > (Q3_AGE - 18) then",
        '  errmsg("Years in health (%d) exceeds working-age years available (%d).",',
        "         Q6_YEARS_HEALTH, Q3_AGE - 18);",
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
    for none_item, target, comment in SELECT_ALL_NONE_SKIPS:
        out += _proc(none_item, "postproc", [
            f"{{ {comment} }}",
            f"if {none_item} = 1 then",
            f"  skip to {target};",
            "endif;",
        ])
    return out


def emit_multi_branch_skips():
    """Multi-destination routing items (spec section 2)."""
    out = ["{ ---- Multi-branch skip routing (spec section 2) ---- }"]
    for item, branches, comment in MULTI_BRANCH_SKIPS:
        body = [f"{{ {comment} }}"]
        for cond, target in branches:
            body += [f"if {cond} then", f"  skip to {target};", "endif;"]
        out += _proc(item, "postproc", body)
    return out


def emit_block_gates():
    """Branch block gates — skip a select-all block on the off-branch
    (spec section 2; BUCAS/GAMOT/Malasakit two-path structure)."""
    out = ["{ ---- Branch block gates (spec section 2) ---- }"]
    for first_item, cond, target, comment in BLOCK_GATES:
        out += _proc(first_item, "preproc", [
            f"{{ {comment} }}",
            f"if {cond} then",
            f"  skip to {target};",
            "endif;",
        ])
    return out


def emit_why_difficult_gates(item_after):
    """Per-option why-difficult GATEs (spec 4.10). The gated select-all block
    is skipped entirely when its parent option was not flagged."""
    out = ["{ ---- 'Why difficult' per-option gates (spec 4.10) ---- }"]
    for gate_item, block_prefix in WHY_DIFFICULT_GATES:
        first_item = f"{block_prefix}_O01"
        target = item_after.get(block_prefix)
        if target is None:
            sys.stderr.write(
                f"WARNING: no item-after target for gate block {block_prefix}\n")
            continue
        out += _proc(first_item, "preproc", [
            f"{{ enter {block_prefix} only if {gate_item} was selected }}",
            f"if {gate_item} <> 1 then",
            f"  skip to {target};",
            "endif;",
        ])
    return out


def emit_numeric_validations():
    out = ["{ ---- Numeric-range validations (spec section 3) ---- }"]
    # Group by item: CSPro allows only one PROC per item, so an item with both
    # a hard and a soft check gets a single postproc with both (hard first).
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
                body += [
                    f"if {cond} then",
                    f'  errmsg("{msg}"{arg});',
                    "  reenter;",
                    "endif;",
                ]
            else:  # soft — accept() is not printf-formatted; pre-format via maketext
                prompt = f'maketext("{msg}", {item})' if has_arg else f'"{msg}"'
                body += [
                    f"if {cond} then",
                    f'  if accept({prompt}, "Yes", "No") <> 1 then',
                    "    reenter;",
                    "  endif;",
                    "endif;",
                ]
        out += _proc(item, "postproc", body)
    # Q52 accreditation-date validations (spec 4.6)
    out += _proc("Q52_YK_SINCE_YEAR", "postproc", [
        "if Q52_YK_SINCE_YEAR < 2019 or Q52_YK_SINCE_YEAR > currentYear then",
        '  errmsg("YAKAP accreditation year must be between 2019 and %d.", currentYear);',
        "  reenter;",
        "endif;",
    ])
    out += _proc("Q52_YK_SINCE_MONTH", "postproc", [
        "if Q52_YK_SINCE_MONTH < 1 or Q52_YK_SINCE_MONTH > 12 then",
        '  errmsg("Month must be 1-12.");',
        "  reenter;",
        "endif;",
        "if Q52_YK_SINCE_YEAR = currentYear and Q52_YK_SINCE_MONTH > currentMonth then",
        '  errmsg("Accreditation date is in the future. Reenter.");',
        "  reenter;",
        "endif;",
    ])
    # Q87/Q86 consistency (spec 4.7)
    out += _proc("Q87_REGISTERED_PATIENTS", "postproc", [
        "if Q87_REGISTERED_PATIENTS > Q86_ELIGIBLE_PATIENTS then",
        '  errmsg("Registered patients (%d) cannot exceed eligible patients (%d).",',
        "         Q87_REGISTERED_PATIENTS, Q86_ELIGIBLE_PATIENTS);",
        "  reenter;",
        "endif;",
    ])
    return out


def emit_other_specify(dictionary):
    """'Other (specify)' free-text enforcement (spec 4.13). Generated by
    scanning the DCF: each *_OTHER_TXT item is required when its parent picks
    the 'specify' option. UHC9 *_YES_OTHER_TXT / *_NO_OTHER_TXT map to main = 4
    / main = 7."""
    out = ["{ ---- 'Other (specify)' enforcement (spec 4.13) ---- }"]
    for rec in dictionary["levels"][0]["records"]:
        items = rec["items"]
        for idx, it in enumerate(items):
            name = it["name"]
            if name.endswith("_YES_OTHER_TXT"):
                parent = name[:-len("_YES_OTHER_TXT")]
                out += _proc(name, "postproc", [
                    f"if {parent} = 4 and length(strip({name})) = 0 then",
                    '  errmsg("\'Yes, other reason\' was selected. Please specify.");',
                    "  reenter;",
                    "endif;",
                ])
            elif name.endswith("_NO_OTHER_TXT"):
                parent = name[:-len("_NO_OTHER_TXT")]
                out += _proc(name, "postproc", [
                    f"if {parent} = 7 and length(strip({name})) = 0 then",
                    '  errmsg("\'No, other reason\' was selected. Please specify.");',
                    "  reenter;",
                    "endif;",
                ])
            elif name.endswith("_OTHER_TXT"):
                gate = _other_specify_gate(name, items, idx)
                if gate is None:
                    out.append(f"{{ NOTE: {name} — parent/'specify' code not "
                               f"auto-resolved; wire manually in bench-test. }}")
                    out.append("")
                    continue
                parent, code = gate
                out += _proc(name, "postproc", [
                    f"if {parent} = {code} and length(strip({name})) = 0 then",
                    f'  errmsg("\'Other\' was selected for {parent}. Please specify.");',
                    "  reenter;",
                    "endif;",
                ])
    return out


def _other_specify_gate(txt_name, items, idx):
    """Resolve the parent item + 'specify' trigger code for a *_OTHER_TXT item.

    select-all case: the parent is the select-all 'Other (specify)' option item
    (a {prefix}_O## sibling whose label mentions 'specify'); trigger = 1.
    select-one case: the parent is the immediately-preceding item; trigger =
    the value-set code whose label mentions 'specify'.
    """
    prefix = txt_name[:-len("_OTHER_TXT")]
    # select-all: look for {prefix}_O## siblings
    siblings = [it for it in items if it["name"].startswith(prefix + "_O")
                and it["name"] != txt_name]
    if siblings:
        for sib in siblings:
            if "specify" in sib["labels"][0]["text"].lower():
                return (sib["name"], 1)
        return None
    # select-one: parent is the preceding item
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
    dictionary = build_dictionary_f1()

    # Map each record/block prefix -> the item name that follows its last item,
    # so why-difficult gates can skip the whole block.
    flat = []
    for rec in dictionary["levels"][0]["records"]:
        flat += [it["name"] for it in rec["items"]]
    item_after = {}
    for _, block_prefix in WHY_DIFFICULT_GATES:
        block_items = [i for i, n in enumerate(flat)
                       if n.startswith(block_prefix + "_")]
        if block_items:
            nxt = block_items[-1] + 1
            item_after[block_prefix] = flat[nxt] if nxt < len(flat) else None

    lines = []
    lines.append("{ ============================================================")
    lines.append("  FacilityHeadSurvey.generated.apc — F1 CAPI logic (v1.0, phase 4)")
    lines.append("")
    lines.append("  GENERATED by F1/generate_apc.py — do NOT hand-edit.")
    lines.append("  Patch the generator + the F1-Skip-Logic-and-Validations.md spec,")
    lines.append("  then regenerate. Verified against a paper walkthrough in the")
    lines.append("  bench-test pass (spec section 6.5).")
    lines.append("  ============================================================ }")
    lines.append("")
    lines += emit_framework()
    lines += emit_psgc_cascade()
    lines += emit_capture()
    lines += emit_section_a()
    lines += emit_skip_rules()
    lines += emit_multi_branch_skips()
    lines += emit_block_gates()
    lines += emit_why_difficult_gates(item_after)
    lines += emit_numeric_validations()
    lines += emit_other_specify(dictionary)

    # CSPro allows only one PROC per object — fail loudly if any name repeats.
    proc_headers = [ln[len("PROC "):].strip()
                    for ln in lines if ln.startswith("PROC ")]
    dupes = sorted({p for p in proc_headers if proc_headers.count(p) > 1})
    if dupes:
        raise RuntimeError(
            f"duplicate PROC headers (CSPro allows one PROC per object): {dupes}")
    return "\r\n".join(lines) + "\r\n", len(proc_headers)


def main():
    out_path = Path(__file__).parent / "FacilityHeadSurvey.generated.apc"
    apc_text, proc_count = build_apc()
    out_path.write_text(apc_text, encoding="utf-8")
    sys.stderr.write(f"Wrote {out_path} ({proc_count} PROC blocks)\n")


if __name__ == "__main__":
    main()
