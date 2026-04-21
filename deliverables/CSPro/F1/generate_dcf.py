"""
generate_dcf.py — F1 Facility Head Survey CSPro Data Dictionary generator.

Emits FacilityHeadSurvey.dcf in CSPro 8.0 JSON dictionary format from the
Apr 20 2026 Annex F1 questionnaire (Revised Inception Report submission;
supersedes the Apr 08 baseline).

Authority sources (in priority order):
  1. raw/Project-Deliverable-1_Apr20-submitted/Annex F1_Facility Head Survey
     Questionnaire_UHC Year 2.pdf                                   (printed)
  2. deliverables/CSPro/F1/inputs/F1_clean.txt                       (text extract)
  3. deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md          (logic spec)
  4. raw/CSPro-Data-Dictionary/FacilityHeadSurvey.dcf                (Carl's manual
     scaffold — authoritative for FIELD_CONTROL, GEO_ID, Q1-Q8 item names + value
     set labels; this generator extends it for Q9-Q166 + secondary data.)

Naming convention: Q{n}_DESCRIPTOR in UPPER_SNAKE. Item names for Q9-Q166
follow F1-Skip-Logic-and-Validations.md so the validation-rule references
in that doc keep working without rename churn.

Closed design decisions: the 6 `PENDING_DESIGN_*` constants near the top of
this file encode final defaults confirmed under E2-F1-009b. The prefix is
kept for grep-ability; treat the values as closed, not pending.

Run:
    python generate_dcf.py        # writes FacilityHeadSurvey.dcf next to this file
"""

import json
import sys
from pathlib import Path

# Import shared helpers
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import (
    YES_NO, YES_NO_DK, YES_NO_NA, UHC9_OPTIONS, FREQUENCY, WHY_DIFF_OPTIONS,
    _value_set, numeric, alpha, yes_no, yes_no_dk, yes_no_na,
    select_one, select_all, uhc9_item, record, build_geo_id,
    _gps_fields, _photo_block,
)

# ============================================================
# 2. PENDING DESIGN DECISIONS — flip these when ASPSI confirms
# ============================================================
# These 6 items have NOT been decided as of 2026-04-14 (the technical design review
# meeting did not actually cover them, contrary to the scrum log entry
# that has now been corrected).

PENDING_DESIGN = "TODO: PENDING DESIGN DECISION"

# (1) Q63 ACCRED_WAIT — printed text says "How many DAYS did you wait..."
#     but bucket labels are in MONTHS. Default: keep months until ASPSI confirms.
Q63_USE_DAY_BUCKETS = False

# (2) Secondary data structure — separate dcf records vs separate CSPro
#     app vs paper-only collection. Default: emit empty stub records so
#     the dictionary opens, but no items inside.
SECONDARY_DATA_AS_STUBS = True

# (3) NBB split — already two separate UHC9 items (Q40 NBB, Q41 ZBB).
#     The pending question is whether to also split by facility tier.
NBB_SPLIT_BY_TIER = False

# (4) Q31 EMR_USE — should "Not applicable" route to Q35 like the other
#     UHC9 NA branches? Skip-logic doc says yes; printed Q31 omits it.
#     Default: treat NA as a skip (encoded in PROC, not the dictionary).
Q31_NA_SKIPS = True

# (5) Q166 PD_NURSES — printed list omits "Clinical audits" and
#     "Surgical audits". Default: build a separate nurse list without them.
Q166_NURSES_INCLUDE_AUDITS = False

# (6) Q121 DOH_LIC_DIFFICULT — dynamic value set by facility type vs
#     enforce via skip on Q132/Q133/Q134. Default: single value set + skip.
Q121_DYNAMIC_VALUE_SET = False



# ============================================================
# 3. RECORD BUILDERS — A. Field Control + B. Geographic ID
# ============================================================

def build_field_control():
    items = [
        # Header — preserves exact item names from Carl's scaffold so
        # any prior PROC code keeps working.
        alpha("SURVEY_TEAM_LEADER_S_NAME",      "Survey Team Leader's Name",                    length=50),
        alpha("ENUMERATOR_S_NAME",              "Enumerator's Name",                            length=50),
        alpha("FIELD_VALIDATED_BY",             "Field Validated by",                           length=50),
        alpha("FIELD_EDITED_BY",                "Field Edited by",                              length=50),
        numeric("DATE_FIRST_VISITED_THE_FACILITY",
                "Date First Visited the Facility (YYYYMMDD)", length=8),
        numeric("DATE_OF_FINAL_VISIT_TO_THE_FACILITY",
                "Date of Final Visit to the Facility (YYYYMMDD)", length=8),
        numeric("TOTAL_NUMBER_OF_VISITS",       "Total Number of Visits",                       length=3),
        numeric("ENUM_RESULT_FIRST_VISIT",      "Result of First Visit",                        length=1,
                value_set_options=[
                    ("Completed",  "1"),
                    ("Postponed",  "2"),
                    ("Refused",    "3"),
                    ("Incomplete", "4"),
                ]),
        numeric("ENUM_RESULT_FINAL_VISIT",      "Result of Final Visit",                        length=1,
                value_set_options=[
                    ("Completed",  "1"),
                    ("Postponed",  "2"),
                    ("Refused",    "3"),
                    ("Incomplete", "4"),
                ]),
        # Informed consent block (Bug #5 fix from F1-Skip-Logic-and-Validations.md)
        numeric("CONSENT_GIVEN",                "Informed consent given",                       length=1,
                value_set_options=YES_NO),
    ]
    return record("FIELD_CONTROL", "Field Control", "A", items)


# ============================================================
# 5. RECORD BUILDERS — Section A. Facility Head Profile (Q1-Q6)
# ============================================================
# Item names match Carl's manual scaffold exactly so existing references survive.

def build_section_a():
    Q2_ROLES = [
        ("Rural / Urban Health Unit Head",      "1"),
        ("Physician",                           "2"),
        ("Chief of Hospital",                   "3"),
        ("Medical Director",                    "4"),
        ("Hospital Administrator",              "5"),
        ("Nurse",                               "6"),
        ("Municipal / City Health Officer",     "7"),
        ("Medical Officer",                     "8"),
        ("Administrative Officer / Assistant",  "9"),
        ("Midwife",                            "10"),
        ("Health Promotion / Nutrition Officer","11"),
    ]
    items = [
        # Respondent contact block — moved out of FIELD_CONTROL so it lives
        # with the facility-head profile it describes.
        alpha("RESP_NAME",     "Respondent name and signature", length=80),
        alpha("RESP_POSITION", "Respondent position / office",  length=80),
        alpha("RESP_EMAIL",    "Respondent email address",      length=60),
        alpha("RESP_MOBILE",   "Respondent mobile number",      length=20),
        alpha("Q1_NAME",
              "1. What is your name? (Last Name, First Name, Middle Initial, Ext)",
              length=80),
        select_one("Q2_FACILITY_ROLE",
                   "2. What is your official designation at this health facility?",
                   Q2_ROLES, length=2),
        numeric("Q3_AGE", "3. How old are you (in years), as of your last birthday?",
                length=2),
        numeric("Q4_SEX", "4. What is your sex assigned at birth?", length=1,
                value_set_options=[("Male", "1"), ("Female", "2")]),
        # Q5 + Q6: tenure as years + months (questionnaire splits these into sub-fields)
        numeric("Q5_YEARS_AT_FACILITY",
                "5. In your current position, how many months/years have you worked at this health facility? Number of Years",
                length=2),
        numeric("Q5_MONTHS_AT_FACILITY",
                "5. In your current position, how many months/years have you worked at this health facility? Number of Months",
                length=2),
        numeric("Q6_YEARS_HEALTH",
                "6. How many years have you worked in health-related position? Number of Years",
                length=2),
        numeric("Q6_MONTHS_HEALTH",
                "6. How many years have you worked in health-related position? Number of Months",
                length=2),
    ]
    return record("A_FACILITY_HEAD_PROFILE", "A. Facility Head Profile", "2", items)


# ============================================================
# 6. RECORD BUILDERS — Section B. Facility Profile (Q7-Q8)
# ============================================================

def build_section_b():
    items = [
        numeric("Q7_OWNERSHIP", "7. What type of ownership is this hospital?",
                length=1, value_set_options=[("Public", "1"), ("Private", "2")]),
        numeric("Q8_SERVICE_LEVEL",
                "8. What is the facility's service capacity level?",
                length=1, value_set_options=[
                    ("Primary Care Facility", "1"),
                    ("Level 1 Hospital",      "2"),
                    ("Level 2 Hospital",      "3"),
                    ("Level 3 Hospital",      "4"),
                ]),
    ]
    return record("B_FACILITY_PROFILE", "B. Facility Profile", "3", items)


# ============================================================
# 7. RECORD BUILDERS — Section C. UHC Implementation (Q9-Q50)
# ============================================================

def build_section_c():
    Q11_PKG_STATUS = [
        ("Implemented as a direct result of the UHC Act (i.e. YAKAP/Konsulta)", "1"),
        ("Pre-existing prior to UHC but subsequently enhanced or expanded due to UHC Act", "2"),
        ("Newly implemented or improved independent of UHC Act", "3"),
        ("Not yet implemented but planned within the next 1-2 years", "4"),
        ("Other (specify)", "5"),
        ("I don't know", "8"),
        ("Not applicable", "9"),
    ]
    Q15_PHU_ROLE = [
        ("Health promotion and education",            "1"),
        ("Disease surveillance report",               "2"),
        ("Referral and patient navigation",           "3"),
        ("Alignment with national public health programs", "4"),
        ("Other (specify)",                           "5"),
        ("I don't know",                              "8"),
        ("Not applicable",                            "9"),
    ]
    Q18_HPU_ROLE = [
        ("Leading health education and awareness campaigns",          "1"),
        ("Conducting and coordinating health screening and promotion","2"),
        ("Advocacy and policy formation",                             "3"),
        ("Resource mobilization and fundraising",                     "4"),
        ("Other (specify)",                                           "5"),
        ("I don't know",                                              "8"),
    ]
    Q32_DATA_SUBMIT = [
        ("Yes, to DOH Information System only",                "1"),
        ("Yes, to PhilHealth Dashboard only",                  "2"),
        ("Yes, to both DOH Information System and PhilHealth Dashboard", "3"),
        ("No, we are not submitting these data",               "4"),
    ]
    Q34_REPORTS = [
        ("OPD/IPD census and morbidity reports", "1"),
        ("Maternal, newborn, child, and adolescent health (MNCAH) reports", "2"),
        ("Notifiable diseases / surveillance reports", "3"),
        ("Expenditure and budget utilization reports", "4"),
        ("PhilHealth claims and reimbursement reports", "5"),
        ("YAKAP/Konsulta utilization reports", "6"),
        ("NBB compliance reports", "7"),
        ("ZBB compliance / monitoring reports", "8"),
        ("HRH staffing and deployment reports", "9"),
        ("Medicines availability and stock status reports", "10"),
        ("Facility performance scorecards / quality reports", "11"),
        ("Other (specify)", "12"),
    ]
    QUALITY_ACCESS_CHALLENGES = [
        ("Limited resources (personnel, equipment, supplies, funding)", "1"),
        ("Challenging quality standards", "2"),
        ("Healthcare decisions made by LGUs not the facility", "3"),
        ("Lack of specific healthcare skills", "4"),
        ("Inadequate training of healthcare workers", "5"),
        ("Lack of patient awareness of UHC benefits", "6"),
        ("Limited accessibility of public healthcare facilities", "7"),
        ("Infrastructure not conducive for patient care", "8"),
        ("I don't know", "9"),
        ("Other (specify)", "10"),
    ]

    items = []
    items.append(yes_no("Q9_UHC_HEARD", "9. Have you heard about Universal Health Care (UHC) prior to this survey?"))
    items.append(yes_no("Q10_HAS_PRIMARY_PKG", "10. Does the facility have primary care packages?"))
    items.append(select_one("Q11_PRIMARY_PKG_STATUS",
                            "11. If yes, specify its implementation status relative to the UHC Act.",
                            Q11_PKG_STATUS))
    items.append(alpha("Q11_OTHER_TXT", "11. If yes, specify its implementation status relative to the UHC Act. — Other (specify) text", length=120))
    items.extend(uhc9_item("Q12_PCB_LICENSING",
                           "12. Has the facility applied for DOH primary care licensing since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.append(yes_no_na("Q13_PUBLIC_HEALTH_UNIT", "13. Do you have a public health unit at this facility?"))
    items.extend(uhc9_item("Q14_PHU_CREATED",
                           "14. If yes, has the creation of a public health unit at this facility been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.append(select_one("Q15_PHU_ROLE", "15. What is the main role of the public health unit?", Q15_PHU_ROLE))
    items.append(alpha("Q15_OTHER_TXT", "15. What is the main role of the public health unit? — Other (specify) text", length=120))
    items.append(yes_no_na("Q16_HEALTH_PROMO_UNIT", "16. Do you have a health promotion unit at this facility?"))
    items.extend(uhc9_item("Q17_HPU_CREATED",
                           "17. If yes, has the creation of a health promotion unit at this facility been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.append(select_one("Q18_HPU_ROLE", "18. What is the main role of the health promotion unit?", Q18_HPU_ROLE))
    items.append(alpha("Q18_OTHER_TXT", "18. What is the main role of the health promotion unit? — Other (specify) text", length=120))
    items.extend(uhc9_item("Q19_NEW_ROLES",
                           "19. Has the establishment of new roles in the facility been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.append(alpha("Q20_NEW_ROLES_LIST", "20. What is/are the new role/s established in this facility?", length=240))
    items.extend(uhc9_item("Q21_NEW_DEPTS",
                           "21. Has the establishment of new departments in the facility been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.append(alpha("Q22_NEW_DEPTS_LIST", "22. What is/are the new department/s established in this facility?", length=240))
    items.extend(uhc9_item("Q23_NEW_BUILDINGS",
                           "23. Has the construction of new building/s in this health facility been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.append(alpha("Q24_NEW_BUILDINGS_PURPOSE", "24. What is/are the building/s being used for?", length=240))
    items.extend(uhc9_item("Q25_NEW_ROOMS",
                           "25. Has the construction of new rooms in this health facility been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.append(alpha("Q26_NEW_ROOMS_PURPOSE", "26. What are the rooms being used for?", length=240))
    items.extend(uhc9_item("Q27_INC_EQUIPMENT",
                           "27. Has the increase in equipment been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.append(alpha("Q28_INC_EQUIPMENT_LIST", "28. If there was an increase in equipment, what are these pieces of equipment?", length=240))
    items.extend(uhc9_item("Q29_INC_SUPPLIES",
                           "29. Has the increase in supplies been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.append(alpha("Q30_INC_SUPPLIES_LIST", "30. If there was an increase in supplies, what are these?", length=240))
    items.extend(uhc9_item("Q31_EMR_USE",
                           "31. Has the use of electronic medical records at the facility been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.append(select_one("Q32_DATA_SUBMIT",
                            "32. Does your facility currently submit health and financial data to the DOH Information System and/or the PhilHealth Dashboard?",
                            Q32_DATA_SUBMIT))
    items.append(select_one("Q33_DATA_FREQ",
                            "33. If yes, how frequent has your facility submit these data?",
                            FREQUENCY))
    items.append(alpha("Q33_OTHER_TXT", "33. If yes, how frequent has your facility submit these data? — Other (specify) text", length=120))
    items.extend(select_all("Q34_DATA_REPORTS_USED",
                            "34. Which of the submitted reports are actually used for decision-making?",
                            Q34_REPORTS))
    items.append(yes_no("Q35_STAFFING_CHANGED", "35. Have there been changes in the facility staffing since 2019?"))
    items.extend(uhc9_item("Q36_STAFFING_UHC",
                           "36. Have the changes in staffing been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.append(yes_no("Q37_REFERRAL_CHANGED", "37. Have there been changes in the referral system since 2019?"))
    items.extend(uhc9_item("Q38_REFERRAL_UHC",
                           "38. Have the changes to the referral system (inbound or outbound) been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.extend(uhc9_item("Q39_MOU_MOA",
                           "39. Has the Memorandum of Understanding (MoU) / Agreement (MoA) with other health facilities as part of the healthcare provider network been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.extend(uhc9_item("Q40_NBB",
                           "40. Has the no balance billing (NBB) been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.extend(uhc9_item("Q41_ZBB",
                           "41. Has the zero balance billing (ZBB) been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.extend(uhc9_item("Q42_NO_COPAY",
                           "42. Has the no co-payment policy been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    # Q43 — verbatim text exceeds CSPro's 255-char label limit (327 chars with
    # ward-allocation parenthetical, +28 for the uhc9_item OTHER_TXT suffix).
    # Parenthetical is enumerator context, not the question itself, so dropped here.
    items.extend(uhc9_item("Q43_WARD_ALLOC",
                           "43. Has the health facility been implementing ward accommodation allocation since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.extend(uhc9_item("Q44_CPG",
                           "44. Have the improved clinical practice guidelines been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.extend(uhc9_item("Q45_DOH_LIC_STD",
                           "45. Have the DOH licensing standards been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.extend(uhc9_item("Q46_PHIC_ACCRED",
                           "46. Have the PhilHealth accreditation requirements been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.extend(uhc9_item("Q47_SVC_DELIVERY_PROT",
                           "47. Have the service delivery protocols been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.extend(uhc9_item("Q48_PCQM",
                           "48. Have the primary care quality measures been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?"))
    items.extend(select_all("Q49_QUALITY_CHALL",
                            "49. What are the major challenges to improving the quality of patient care in your local area?",
                            QUALITY_ACCESS_CHALLENGES))
    items.extend(select_all("Q50_ACCESS_CHALL",
                            "50. What are the major challenges to improving the accessibility of patient care in your local area?",
                            QUALITY_ACCESS_CHALLENGES))
    return record("C_UHC_IMPLEMENTATION", "C. Universal Health Care (UHC) Implementation", "4", items)


# ============================================================
# 8. RECORD BUILDERS — Section D. YAKAP / Konsulta (Q51-Q100)
# ============================================================

def build_section_d():
    Q53_PACKAGE = [
        ("Pap smear", "1"), ("Mammogram", "2"), ("Lipid profile", "3"),
        ("Thyroid function test", "4"), ("Chest X-ray", "5"),
        ("Low-dose CT scan", "6"), ("Dental services", "7"),
        ("All of the above", "8"), ("I don't know", "9"), ("Other (specify)", "10"),
    ]
    Q58_PERF = [
        ("Beneficiaries consulted a primary care doctor", "1"),
        ("Utilization of laboratory services", "2"),
        ("Beneficiaries received antibiotics as prescribed", "3"),
        ("Beneficiaries received NCD medicine as prescribed", "4"),
        ("No requirements", "5"),
        ("1st patient encounter", "6"),
        ("I don't know", "7"),
        ("Other (specify)", "8"),
    ]
    Q60_PAY_FREQ = [
        ("Monthly", "1"), ("Quarterly", "2"), ("Semi-annually", "3"), ("Annually", "4"),
    ]
    Q62_TRANCHE_INTERVAL = [
        ("Less than a month", "1"), ("1-2 months", "2"), ("3-4 months", "3"),
        ("5-6 months", "4"), ("More than six months", "5"),
    ]
    # Q63 — PENDING DESIGN days vs months. Default: months (matches printed buckets).
    Q63_LABEL_SUFFIX = " [PENDING DESIGN: printed text says days, buckets are months]"
    Q63_BUCKETS = Q62_TRANCHE_INTERVAL  # same shape until ASPSI confirms

    Q64_REASONS = [
        ("Incentives (capitation/payment for registered patients)", "1"),
        ("Aligns with facility's mission", "2"),
        ("Encouraged by LGU", "3"),
        ("Mandated/required by DOH/UHC", "4"),
        ("To improve facility services", "5"),
        ("Other (specify)", "6"),
    ]
    Q65_DIFFICULT = [
        ("Ability to conduct preventive/screening services and health education", "1"),
        ("Capability to provide laboratory and radiologic services", "2"),
        ("Capability to dispense required medicines", "3"),
        ("General Infrastructure", "4"),
        ("Equipment and Supplies", "5"),
        ("Human resource", "6"),
        ("Functional Health Information System", "7"),
        ("Documentary requirements", "8"),
        ("DOH licensing requirements", "9"),
        ("None of the above", "10"),
    ]
    Q75_RESPONSIBILITY = [
        ("Patients' own initiative", "1"),
        ("Facility", "2"),
        ("LGU", "3"),
        ("Someone else", "4"),
        ("PhilHealth", "5"),
        ("I don't know", "6"),
        ("Other (specify)", "7"),
    ]
    Q76_INITIATIVES = [
        ("On-site Enrollment", "1"),
        ("LGU Outreach", "2"),
        ("Facility Outreach", "3"),
        ("Barangay Health Workers (BHWs) Support", "4"),
        ("Information Campaigns", "5"),
        ("Local Health Insurance Offices (LHIO) / YAKAP caravans", "6"),
        ("Coordination with other government agencies and private sector", "7"),
        ("No initiatives", "8"),
        ("Other (specify)", "9"),
    ]
    Q78_ENROLL_CHALL = [
        ("Lack of patient awareness", "1"),
        ("Lack of patient willingness", "2"),
        ("Lack of resources (manpower)", "3"),
        ("Competition with other health facilities", "4"),
        ("Technical / system issues of PhilHealth", "5"),
        ("Other (specify)", "6"),
    ]
    Q79_NOT_ACCRED = [
        ("Difficult process", "1"),
        ("No time", "2"),
        ("Ongoing application", "3"),
        ("Other (specify)", "4"),
    ]
    Q80_INTEND = [
        ("Yes, already in process",                "1"),
        ("Yes, not yet in process",                "2"),
        ("No, decided not to",                     "3"),
        ("No, tried and failed",                   "4"),
        ("No, haven't thought about it yet",       "5"),
        ("I don't know",                           "6"),
    ]
    Q94_ADDL_CAP_REASONS = [
        ("Cover building maintenance, equipment, non-clinical staff", "1"),
        ("Patient care costs exceed predetermined fixed payment", "2"),
        ("Services excluded from capitation coverage", "3"),
        ("Provide preventive care not adequately compensated", "4"),
        ("Offset losses", "5"),
        ("Other (specify)", "6"),
    ]
    Q95_RECEIVED = [
        ("Yes, received all expected payments",         "1"),
        ("Yes, received some but not all expected",     "2"),
        ("No, have not received any expected payments", "3"),
        ("No, have not expected any payments yet",      "4"),
    ]
    Q96_NOT_RECEIVED = [
        ("Delays in PhilHealth processing", "1"),
        ("Delays in facility's tracking of patient enrollment", "2"),
        ("Difficulties verifying patient enrollment (PhilHealth)", "3"),
        ("Facility not active in meeting payment criteria", "4"),
        ("Criteria for payments is unclear", "5"),
        ("I don't know", "6"),
        ("Other (specify)", "7"),
    ]
    Q98_PAY_CHALL = [
        ("Delayed payment process", "1"),
        ("Unclear criteria for capitation", "2"),
        ("Difficult to meet criteria for capitation", "3"),
        ("PhilHealth process to apply for payments is difficult/unclear", "4"),
        ("I don't know", "5"),
        ("Other (specify)", "6"),
    ]
    Q99_EXPAND = [
        ("Current list of medicines and drugs", "1"),
        ("Current laboratory/diagnostic services", "2"),
        ("Additional features", "3"),
        ("I don't know", "4"),
        ("Other (specify)", "5"),
    ]

    items = []
    items.append(yes_no("Q51_YK_ACCRED", "51. Are you currently an accredited YAKAP/Konsulta provider?"))
    items.append(numeric("Q52_YK_SINCE_MONTH", "52. If yes, since when? Month", length=2))
    items.append(numeric("Q52_YK_SINCE_YEAR",  "52. If yes, since when? Year",  length=4))
    items.extend(select_all("Q53_YK_PACKAGE",
                            "53. If accredited, which of the following are included in the YAKAP/Konsulta package?",
                            Q53_PACKAGE))
    items.append(yes_no_dk("Q54_YK_REG_INDIV",
                           "54. Is it possible to register individual patients to YAKAP/Konsulta at this facility?"))
    items.append(yes_no_dk("Q55_YK_REG_FAM",
                           "55. Is it possible to register whole families to YAKAP/Konsulta at this facility?"))
    items.append(yes_no_dk("Q56_YK_REG_BOTH",
                           "56. Is it only possible to register both individual patients and their family members together to YAKAP/Konsulta at this facility?"))
    items.append(numeric("Q57_CAPITATION_AMT",
                         "57. Based on your knowledge, what is the capitation amount of the YAKAP/Konsulta package? (Capitation is the amount per year per registered patient for delivering the YAKAP/Konsulta package services.)",
                         length=6))
    items.extend(select_all("Q58_PERF_INDICATORS",
                            "58. What are the performance indicators you need to meet to receive the second tranche payment?",
                            Q58_PERF))
    items.append(yes_no("Q59_KNOW_PAY_FREQ",
                        "59. Do you know how often you can expect to receive payments from PhilHealth for the delivery of the YAKAP/Konsulta package?"))
    items.append(select_one("Q60_PAY_FREQ",
                            "60. How often should you be receiving payments?",
                            Q60_PAY_FREQ))
    items.append(yes_no("Q61_TRANCHE_DELAY", "61. Were there delays in receiving capitation tranches?"))
    items.append(alpha("Q61_DELAY_REASON",
                       "61.1. If yes, what was/were the reasons for the delay?", length=240))
    items.append(select_one("Q62_TRANCHE_INTERVAL",
                            "62. On average, how long is the typical time interval between tranches releases to the facility?",
                            Q62_TRANCHE_INTERVAL))
    items.append(select_one("Q63_ACCRED_WAIT",
                            "63. How many days did you wait from application submission to accreditation approval?" + Q63_LABEL_SUFFIX,
                            Q63_BUCKETS))
    items.extend(select_all("Q64_APPLY_REASON",
                            "64. Why did you apply to become a YAKAP/Konsulta provider?",
                            Q64_REASONS))
    items.extend(select_all("Q65_ACCRED_DIFFICULT",
                            "65. Which of the following requirements were difficult to comply with for accreditation?",
                            Q65_DIFFICULT, with_other_txt=False))
    # Q66-Q74 = nine "why difficult" select-alls, gated on Q65 in PROC.
    Q66_74_TOPICS = [
        ("Q66_WHY_DIFF_PREVENTIVE",  "66. Why was it difficult to comply with the following? Ability to conduct preventive/screening services and health education"),
        ("Q67_WHY_DIFF_LAB",         "67. Why was it difficult to comply with the following? Capability to provide services for required laboratory and radiologic services"),
        ("Q68_WHY_DIFF_MEDS",        "68. Why was it difficult to comply with the following? Capability to dispense required medicines"),
        ("Q69_WHY_DIFF_INFRA",       "69. Why was it difficult to comply with the following? General Infrastructure"),
        ("Q70_WHY_DIFF_EQUIPMENT",   "70. Why was it difficult to comply with the following? Equipment and Supplies"),
        ("Q71_WHY_DIFF_HR",          "71. Why was it difficult to comply with the following? Human resource"),
        ("Q72_WHY_DIFF_HIS",         "72. Why was it difficult to comply with the following? Functional Health Information System"),
        ("Q73_WHY_DIFF_DOCS",        "73. Why was it difficult to comply with the following? Documentary requirements"),
        ("Q74_WHY_DIFF_DOH_LIC",     "74. Why was it difficult to comply with the following? DOH Licensing requirements"),
    ]
    for prefix, label in Q66_74_TOPICS:
        items.extend(select_all(prefix, label, WHY_DIFF_OPTIONS[:6] + [WHY_DIFF_OPTIONS[8]]))
    items.extend(select_all("Q75_ENROLL_RESPONSIBILITY",
                            "75. Based on your understanding, whose responsibility is it to enroll patients to YAKAP/Konsulta?",
                            Q75_RESPONSIBILITY))
    items.extend(select_all("Q76_ENROLL_INITIATIVES",
                            "76. Which of the following initiatives are you doing to enroll patients in this facility to YAKAP/Konsulta?",
                            Q76_INITIATIVES))
    items.append(yes_no("Q77_ENROLL_CHALL",
                        "77. Did you experience any challenges in enrolling patients to YAKAP/Konsulta?"))
    items.extend(select_all("Q78_ENROLL_CHALL_LIST",
                            "78. What are the challenges you have faced?",
                            Q78_ENROLL_CHALL))
    items.extend(select_all("Q79_NOT_ACCRED_REASON",
                            "79. If not YAKAP/ KONSULTA accredited, why are you not accredited?",
                            Q79_NOT_ACCRED))
    items.append(select_one("Q80_INTEND_ACCRED",
                            "80. Are you intending to become a YAKAP/Konsulta provider?",
                            Q80_INTEND))
    items.append(yes_no("Q81_KNOW_HOW_START",
                        "81. If you decide to apply today, would you know how to start the process?"))
    items.append(alpha("Q82_DECIDED_NOT_REASON",
                       "82. What was the deciding factor not to apply?", length=240))
    items.append(alpha("Q83_TRIED_FAILED_REASON",
                       "83. What went wrong with the application?", length=240))
    items.append(alpha("Q84_PROCESS_CHALL",
                       "84. What are some challenges in the process, if any?", length=240))
    items.append(alpha("Q85_CATCHMENT_AREA",
                       "85. What areas do you consider as the facility's catchment area/s?", length=240))
    items.append(numeric("Q86_ELIGIBLE_PATIENTS",
                         "86. How many patients in your catchment area are eligible to register to this YAKAP/Konsulta provider?",
                         length=7))
    items.append(numeric("Q87_REGISTERED_PATIENTS",
                         "87. How many eligible patients in your catchment area are already registered to this YAKAP/Konsulta provider?",
                         length=7))
    # Q88 — verbatim text is 448 chars, well over CSPro's 255-char label limit.
    # Compressed the PhilHealth tranche-mechanics middle into a parenthetical;
    # question stem and Php 1,700 anchor preserved verbatim.
    items.append(yes_no_dk("Q88_IS_1700_ENOUGH",
                           "88. The maximum per capita rate for YAKAP/Konsulta is Php 1,700 across private and public facilities (40% after first patient encounter, 60% based on registered catchment population by December). Based on your practice, is this enough?"))
    items.append(yes_no_dk("Q89_COSTING_DONE",
                           "89. Did you go through a costing exercise to figure out if this was viable for your facility?"))
    items.append(yes_no_dk("Q90_COSTING_VIABLE",
                           "90. Did the costing exercise show that Php 1,700 was viable for your facility?"))
    items.append(numeric("Q91_MIN_CAP_VALUE_ACC",
                         "91. What would be the minimum acceptable capitation value per patient per year for you as a YAKAP/Konsulta provider?",
                         length=6))
    items.append(numeric("Q92_MIN_CAP_VALUE_NONACC",
                         "92. What would be the minimum acceptable capitation value per patient per year for you to consider being a YAKAP/Konsulta provider?",
                         length=6))
    items.append(yes_no("Q93_CHARGE_ADDL_CAP", "93. Does your facility charge additional capitation fees?"))
    items.extend(select_all("Q94_CHARGE_ADDL_CAP_REASONS",
                            "94. What is/are the reason/s for the facility to charge additional capitation fees?",
                            Q94_ADDL_CAP_REASONS))
    items.append(select_one("Q95_RECEIVED_PAYMENTS",
                            "95. Have you already received payments for patients enrolled?",
                            Q95_RECEIVED))
    items.extend(select_all("Q96_NOT_RECEIVED_REASONS",
                            "96. Why not?",
                            Q96_NOT_RECEIVED))
    items.append(yes_no("Q97_PAYMENT_CHALL", "97. Did you face any challenges in getting these payments?"))
    items.extend(select_all("Q98_PAYMENT_CHALL_LIST",
                            "98. What were these challenges?",
                            Q98_PAY_CHALL))
    items.extend(select_all("Q99_EXPAND_NEXT",
                            "99. If you were to expand the YAKAP/Konsulta package, what would you expand next?",
                            Q99_EXPAND))
    items.append(alpha("Q100_ADDL_FEATURES",
                       "100. What additional features would you add?", length=240))
    return record("D_YAKAP_KONSULTA", "D. YAKAP / Konsulta Package", "5", items)


# ============================================================
# 9. RECORD BUILDERS — Section E. BUCAS / GAMOT (Q101-Q117)
# ============================================================

def build_section_e():
    Q103_REASON = [
        ("Proposal not yet submitted",            "1"),
        ("Limited information on establishment process", "2"),
        ("Did not meet standard requirements",    "3"),
        ("Awaiting assessment or approval",       "4"),
        ("Other (specify)",                       "5"),
        ("Not applicable",                       "99"),
    ]
    Q104_SERVICES = [
        ("Urgent care and consultation",         "1"),
        ("Minor surgical procedures",            "2"),
        ("Diagnostic and laboratory services",   "3"),
        ("Reproductive and special health services", "4"),
        ("Other (specify)",                      "5"),
    ]
    Q105_FACTORS = [
        ("Patient awareness",                       "1"),
        ("Facility location and accessibility",     "2"),
        ("Referral patterns",                       "3"),
        ("PhilHealth coverage and reimbursement",   "4"),
        ("Availability of staff/services",          "5"),
        ("Other (specify)",                         "6"),
    ]
    Q110_REASON = [
        ("Application not yet submitted",         "1"),
        ("Limited information on accreditation process", "2"),
        ("Did not meet accreditation requirements","3"),
        ("Awaiting assessment or approval",       "4"),
        ("Other (specify)",                       "5"),
        ("Not applicable",                       "99"),
    ]
    Q111_FACTORS = [
        ("Availability of GAMOT medicines",                    "1"),
        ("Pharmacy capacity",                                  "2"),
        ("Patient awareness of the program",                   "3"),
        ("PhilHealth eligibility and reimbursement processes", "4"),
        ("Prescribing practices of physicians",                "5"),
        ("Other (specify)",                                    "6"),
    ]
    Q114_DURATION = [
        ("Less than 30 days", "1"),
        ("31-60 days",        "2"),
        ("More than 60 days", "3"),
    ]
    Q115_AVG = [
        ("Less than a month", "1"),
        ("1-2 months",        "2"),
        ("3-4 months",        "3"),
        ("5-6 months",        "4"),
        ("More than 6 months","5"),
    ]
    Q116_ADDR = [
        ("Yes",                                             "1"),
        ("No",                                              "2"),
        ("Did not experience stock outs of GAMOT meds",     "3"),
    ]
    Q117_HOW = [
        ("Resorted to alternative procurement", "1"),
        ("Active inventory monitoring",         "2"),
        ("Improve forecasting and quantification", "3"),
        ("Other (specify)",                     "4"),
    ]

    items = []
    items.append(yes_no("Q101_HEARD_BUCAS",
                        "101. Have you heard about the Bagong Urgent Care and Ambulatory Service (BUCAS)?"))
    items.append(yes_no_dk("Q102_HAS_BUCAS", "102. Do you have a BUCAS Center?"))
    items.append(select_one("Q103_NO_BUCAS_REASON",
                            "103. If none, what is the primary reason?", Q103_REASON))
    items.append(alpha("Q103_OTHER_TXT",
                       "103. If none, what is the primary reason? Other (specify)", length=120))
    items.extend(select_all("Q104_BUCAS_SERVICES",
                            "104. What are the available services offered by your BUCAS Center?",
                            Q104_SERVICES))
    items.extend(select_all("Q105_BUCAS_FACTORS",
                            "105. In your assessment, what are the main factors affecting the utilization of BUCAS in your facility?",
                            Q105_FACTORS))
    items.append(alpha("Q106_BUCAS_RESOURCES_NEEDED",
                       "106. What are the resources you need to support/sustain the BUCAS center?",
                       length=240))
    items.append(yes_no("Q107_BUCAS_DECONGEST",
                        "107. Based on your experience, does the BUCAS Center decongest your health facility of patients?"))
    items.append(yes_no("Q108_HEARD_GAMOT",
                        "108. Have you heard about the Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT) package?"))
    items.append(yes_no("Q109_GAMOT_ACCRED", "109. Is your facility an accredited GAMOT provider?"))
    items.append(select_one("Q110_NO_GAMOT_REASON",
                            "110. If no, what is the primary reason?", Q110_REASON))
    items.append(alpha("Q110_OTHER_TXT",
                       "110. If no, what is the primary reason? Other (specify)", length=120))
    items.extend(select_all("Q111_GAMOT_FACTORS",
                            "111. In your assessment, what are the main factors affecting the utilization of the GAMOT Program in your facility?",
                            Q111_FACTORS))
    items.append(yes_no("Q112_STOCKOUT",
                        "112. In the past 3 months, has this facility experienced a stock-out (zero supply) of any tracer essential medicines?"))
    items.append(alpha("Q113_STOCKOUT_MEDS",
                       "113. What specific medicines? (antihypertensives, antibiotics, etc.)", length=240))
    items.append(select_one("Q114_STOCKOUT_DURATION",
                            "114. How many days did the stock-out last?", Q114_DURATION))
    items.append(select_one("Q115_STOCKOUT_AVG",
                            "115. On average, how many months do these stock-outs last?", Q115_AVG))
    items.append(select_one("Q116_ADDR_STOCKOUT",
                            "116. Did you do anything to address the medicine stock-outs in the GAMOT Package?",
                            Q116_ADDR))
    items.extend(select_all("Q117_ADDR_STOCKOUT_HOW",
                            "117. If yes, what did you do to address the medicine stock-outs in the GAMOT Package?",
                            Q117_HOW))
    return record("E_BUCAS_GAMOT", "E. Awareness on Expanded Health Programs (BUCAS and GAMOT)", "6", items)


# ============================================================
# 10. RECORD BUILDERS — Section F. DOH Licensing (Q118-Q134)
# ============================================================

def build_section_f():
    Q118_LICENSED = [
        ("Yes",                                              "1"),
        ("No",                                               "2"),
        ("No, but submitted requirements and waiting",       "3"),
        ("I don't know what DOH licensing is",               "4"),
    ]
    Q119_WHEN = [
        ("Within the last 1 to 3 months",     "1"),
        ("Within the last 4 to 6 months",     "2"),
        ("Over 6 months but within 1 year",   "3"),
        ("More than 1 year ago",              "4"),
        ("I don't know",                      "5"),
    ]
    Q120_DAYS = [
        ("Less than 30 days", "1"),
        ("31-60 days",        "2"),
        ("More than 60 days", "3"),
    ]
    Q121_DIFFICULT = [
        ("Patient rights and organization ethics",                  "1"),
        ("Patient care",                                            "2"),
        ("Leadership and management",                               "3"),
        ("Human resource management",                               "4"),
        ("Information management",                                  "5"),
        ("Safe practice and environment",                           "6"),
        ("Improving performance",                                   "7"),
        ("Physical plant",                                          "8"),
        ("Equipment and instruments",                               "9"),
        ("National laws and DOH issuances (hospitals only)",       "10"),
        ("Emergency cart contents (hospitals only)",               "11"),
        ("Add-on services (hospitals only)",                       "12"),
        ("Public access to price information (PCF only)",          "13"),
        ("None of the above",                                      "14"),
    ]

    items = []
    items.append(select_one("Q118_DOH_LICENSED", "118. Is this facility DOH licensed?", Q118_LICENSED))
    items.append(select_one("Q119_LIC_RECEIVED_WHEN",
                            "119. When did you receive your DOH license from your most recent application?",
                            Q119_WHEN))
    items.append(select_one("Q120_LIC_DAYS",
                            "120. How many days did it take you to receive the license?", Q120_DAYS))
    items.extend(select_all("Q121_DOH_LIC_DIFFICULT",
                            "121. Which of the following requirements were difficult to comply with in the DOH licensing process?",
                            Q121_DIFFICULT, with_other_txt=False))
    # Q122-Q134 = thirteen "why difficult for X" select-alls, gated on Q121.
    Q122_134_TOPICS = [
        ("Q122_WHY_DIFF_PT_RIGHTS",  "122. Why was it difficult to comply with the following? Patient rights and organization ethics"),
        ("Q123_WHY_DIFF_PT_CARE",    "123. Why was it difficult to comply with the following? Patient care"),
        ("Q124_WHY_DIFF_LEADERSHIP", "124. Why was it difficult to comply with the following? Leadership and management"),
        ("Q125_WHY_DIFF_HRM",        "125. Why was it difficult to comply with the following? Human resource management"),
        ("Q126_WHY_DIFF_INFO_MGMT",  "126. Why was it difficult to comply with the following? Information management"),
        ("Q127_WHY_DIFF_SAFE",       "127. Why was it difficult to comply with the following? Safe practice and environment"),
        ("Q128_WHY_DIFF_PERF",       "128. Why was it difficult to comply with the following? Improving performance"),
        ("Q129_WHY_DIFF_PHYS_PLANT", "129. Why was it difficult to comply with the following? Physical plant"),
        ("Q130_WHY_DIFF_PRICE_INFO", "130. Why was it difficult to comply with the following? Public access to price information"),
        ("Q131_WHY_DIFF_EQUIPMENT",  "131. Why was it difficult to comply with the following? Equipment and instruments"),
        ("Q132_WHY_DIFF_NAT_LAWS",   "132. Why was it difficult to comply with the following? National laws and DOH issuances implemented in hospitals and other health facilities"),
        ("Q133_WHY_DIFF_EMERG_CART", "133. Why was it difficult to comply with the following? Emergency Cart Contents"),
        ("Q134_WHY_DIFF_ADDONS",     "134. Why was it difficult to comply with the following? Add-on services"),
    ]
    for prefix, label in Q122_134_TOPICS:
        items.extend(select_all(prefix, label, WHY_DIFF_OPTIONS))
    return record("F_DOH_LICENSING", "F. DOH Licensing: Status and Barriers", "7", items)


# ============================================================
# 11. RECORD BUILDERS — Section G. Service Delivery (Q135-Q162)
# ============================================================

def build_section_g():
    NBB_ZBB_BARRIERS = [
        ("Complying with no fees for basic/ward accommodation",        "1"),
        ("Complying with prescribed allocation ratio (basic vs non-basic)", "2"),
        ("Patients do not go through the process of availing it",      "3"),
        ("Insufficient PhilHealth support value",                      "4"),
        ("Insufficient other sources (MAIFIP, DSWD, PCSO)",            "5"),
        ("PhilHealth delayed payment",                                 "6"),
        ("None of the above",                                          "7"),
        ("Other (specify)",                                            "8"),
    ]
    Q143_DIFFICULT_BENEFIT = [
        ("PhilHealth/financial protection benefits",                                "1"),
        ("Establishment of health care provider networks (HCPNs / referral system)","2"),
        ("Human resources for health reforms",                                      "3"),
        ("Other (specify)",                                                         "4"),
    ]
    Q144_REASONS = [
        ("UHC implementation heavily reliant on LGU decisions", "1"),
        ("Not enough funding/budget",                           "2"),
        ("Technical/system issues of PhilHealth",               "3"),
        ("Other (specify)",                                     "4"),
    ]
    Q146_MALASAKIT_WHY = [
        ("Streamline access to medical and financial aid for indigent patients", "1"),
        ("Reduce out-of-pocket expenses",                                        "2"),
        ("Eliminate the need to travel to multiple government agencies",         "3"),
        ("Foster a more compassionate approach to healthcare",                   "4"),
        ("Other (specify)",                                                      "5"),
    ]
    Q147_NO_MALASAKIT_WHY = [
        ("Limited budget",                              "1"),
        ("Stringent eligibility requirements",          "2"),
        ("Incomplete documentation from patients",      "3"),
        ("High patient volume / service bottlenecks",   "4"),
        ("Other (specify)",                             "5"),
    ]
    Q149_LGU_FORMS = [
        ("Financial assistance",            "1"),
        ("Technical assistance",            "2"),
        ("Medical supplies and equipment",  "3"),
        ("Manpower support",                "4"),
        ("Other (specify)",                 "5"),
    ]
    Q151_NOT_SAT_WHY = [
        ("Insufficient",                                          "1"),
        ("Hard to coordinate",                                    "2"),
        ("Support given is not aligned with the needs",           "3"),
        ("I don't know",                                          "4"),
        ("Other (specify)",                                       "5"),
    ]
    Q152_CLARITY = [
        ("Very Clear",  "1"),
        ("Clear",       "2"),
        ("Neither",     "3"),
        ("Unclear",     "4"),
        ("Very Unclear","5"),
    ]
    Q155_SEND_REF = [
        ("Physical referral slip",                  "1"),
        ("E-referral",                              "2"),
        ("Referring facility calls receiving facility", "3"),
        ("Other (specify)",                         "4"),
    ]
    Q156_FORM_TYPE = [
        ("DOH standard referral form",      "1"),
        ("Facility's standard referral form","2"),
        ("Province's standard referral form","3"),
        ("City / LGU standard referral form","4"),
        ("No standard referral form",       "5"),
        ("Other (specify)",                 "6"),
    ]
    Q157_NETWORK = [
        ("Yes",                "1"),
        ("No",                 "2"),
        ("I've never heard of it","3"),
        ("I don't know",       "4"),
    ]
    Q158_PROPORTION = [
        ("Almost all patients are referred, very few walk-in",    "1"),
        ("Majority referred, some walk-in",                       "2"),
        ("Proportion of referrals about equal to walk-ins",       "3"),
        ("Majority walk-in, some referred",                       "4"),
        ("Almost all walk-in, very few referred",                 "5"),
        ("Unsure about the typical ratio",                        "6"),
    ]
    Q159_RECEIVE_REF = [
        ("Physical referral slip",                          "1"),
        ("E-referral",                                      "2"),
        ("Referring facility calls receiving facility",     "3"),
        ("Other (specify)",                                 "4"),
    ]
    Q160_EXTERNAL = [
        ("External laboratory",                             "1"),
        ("Other private facility",                          "2"),
        ("Other public facility",                           "3"),
        ("I don't know",                                    "4"),
        ("Other (specify)",                                 "5"),
    ]
    Q161_SATISFACTION = [
        ("Very Satisfied",  "1"),
        ("Satisfied",       "2"),
        ("Neither",         "3"),
        ("Dissatisfied",    "4"),
        ("Very Dissatisfied","5"),
    ]
    Q162_NOT_SAT = [
        ("Facilities overcrowded / do not accept our patient referrals", "1"),
        ("Referral process is slow",                                     "2"),
        ("Poor coordination between facilities",                         "3"),
        ("Other (specify)",                                              "4"),
    ]

    items = []
    items.append(yes_no("Q135_NBB_CURR",
                        "135. Do you currently implement the \"no balance billing\" policy for your patients?"))
    items.append(yes_no("Q136_NBB_ALL_PATIENTS",
                        "136. Are you able to implement it for all patients, to the best of your knowledge, for the last 6 months?"))
    items.extend(select_all("Q137_NBB_BARRIERS",
                            "137. In your view, what are some of the barriers to implementing the no balance billing (NBB) policy?",
                            NBB_ZBB_BARRIERS))
    items.append(yes_no("Q138_ZBB_CURR",
                        "138. Do you currently implement the \"Zero Balance Billing\" policy for your patients?"))
    items.append(yes_no("Q139_ZBB_ALL_PATIENTS",
                        "139. If currently implementing ZBB, are you able to implement it for all patients, to the best of your knowledge, for the last six months?"))
    items.extend(select_all("Q140_ZBB_BARRIERS",
                            "140. In your view, what are some of the barriers to implementing the \"zero balance billing\" policy?",
                            NBB_ZBB_BARRIERS))
    items.append(yes_no("Q141_ALLOW_OOP_BASIC",
                        "141. Does the facility allow out-of-pocket (OOP) expenses for basic accommodation?"))
    items.append(alpha("Q142_OOP_REASON",
                       "142. Why does the facility allow OOP expenses for basic accommodation? Specify your reason.",
                       length=240))
    items.append(select_one("Q143_DIFFICULT_BENEFIT",
                            "143. Which of the UHC benefits do you find most difficult to implement?",
                            Q143_DIFFICULT_BENEFIT))
    items.append(alpha("Q143_OTHER_TXT",
                       "143. Which of the UHC benefits do you find most difficult to implement? Other (specify)",
                       length=120))
    items.extend(select_all("Q144_DIFFICULT_REASON",
                            "144. Why is this difficult to implement?", Q144_REASONS))
    items.append(yes_no("Q145_MALASAKIT_PROVIDED",
                        "145. Has the facility been providing medical social welfare or assistance (e.g., through Malasakit Centers, MAIFIP)?"))
    items.extend(select_all("Q146_MALASAKIT_WHY",
                            "146. Why is the facility providing medical social welfare or assistance through Malasakit Centers or MAIFIP?",
                            Q146_MALASAKIT_WHY))
    items.extend(select_all("Q147_NO_MALASAKIT_WHY",
                            "147. Why is the facility not providing medical social welfare or assistance through Malasakit Centers or MAIFIP?",
                            Q147_NO_MALASAKIT_WHY))
    items.append(yes_no("Q148_LGU_SUPPORT",
                        "148. Do you receive any support from your LGU to implement UHC reforms?"))
    items.extend(select_all("Q149_LGU_SUPPORT_FORMS",
                            "149. What forms of support do you receive?", Q149_LGU_FORMS))
    items.append(yes_no("Q150_LGU_SATISFIED",
                        "150. Are you satisfied with the support you receive from your LGU?"))
    items.extend(select_all("Q151_LGU_NOT_SAT_WHY",
                            "151. Why not?", Q151_NOT_SAT_WHY))
    items.append(select_one("Q152_PHO_PROTOCOL_CLARITY",
                            "152. How clear are the protocols regarding which decisions require Provincial Health Office approval versus those you can decide at the facility level?",
                            Q152_CLARITY))
    items.append(alpha("Q153_UNCLEAR_PROTOCOL",
                       "153. Which specific protocol that you consider as unclear?", length=240))
    items.append(numeric("Q154_NUM_REFERRED_OUT",
                         "154. In the past 6 months, how many patients were referred to a higher-level facility within the referral network?",
                         length=6))
    items.extend(select_all("Q155_SEND_REFERRAL_HOW",
                            "155. What are the most common ways you send referrals to higher level facilities/specialists?",
                            Q155_SEND_REF))
    items.extend(select_all("Q156_REFERRAL_FORM_TYPE",
                            "156. What type of referral form do you use to send to higher level facilities?",
                            Q156_FORM_TYPE))
    items.append(select_one("Q157_SPECIALIST_NETWORK",
                            "157. Do you have a network of specialist providers to refer patients to, if needed?",
                            Q157_NETWORK))
    items.append(select_one("Q158_REF_PROPORTION",
                            "158. Considering all patients who come to your facility for the past 6 months, what is the proportion of patients referred by another facility compared to those who self-refer/walk-in?",
                            Q158_PROPORTION))
    items.extend(select_all("Q159_RECEIVE_REFERRAL_HOW",
                            "159. Of those referred, which of the following are the most common ways you receive referrals from lower-level health facilities?",
                            Q159_RECEIVE_REF))
    items.extend(select_all("Q160_EXTERNAL_SERVICES_GO",
                            "160. Where do your patients go to get the services not available at this facility?",
                            Q160_EXTERNAL))
    items.append(select_one("Q161_REF_SATISFACTION",
                            "161. How would you rate your satisfaction with your current referral system?",
                            Q161_SATISFACTION))
    items.extend(select_all("Q162_NOT_SATISFIED_WHY",
                            "162. Why are you not satisfied with the current referral system?",
                            Q162_NOT_SAT))
    return record("G_SERVICE_DELIVERY", "G. Service Delivery Process", "8", items)


# ============================================================
# 12. RECORD BUILDERS — Section H. Human Resources (Q163-Q166)
# ============================================================

def build_section_h():
    Q163_CHALL = [
        ("Understaffing",              "1"),
        ("Skills mismatch / lack of skills", "2"),
        ("Retention / high staff turnover", "3"),
        ("I don't know",               "4"),
        ("Other (specify)",            "5"),
    ]
    PD_DOCTORS = [
        ("Clinical audits",                                          "1"),
        ("Surgical audits",                                          "2"),
        ("Quality assurance meetings",                               "3"),
        ("Seminars, conferences, workshops",                         "4"),
        ("Independent professional development: scholarships",       "5"),
        ("Independent professional development: research grants",    "6"),
        ("LGU/DOH led workshops/initiatives",                        "7"),
        ("No forms of professional development are provided",        "8"),
        ("Other (specify)",                                          "9"),
    ]
    # Q166 — PENDING DESIGN: nurse list omits audits per printed text. Default
    # respects that, but flag retains "Clinical/Surgical audits" toggle.
    if Q166_NURSES_INCLUDE_AUDITS:
        PD_NURSES = PD_DOCTORS
    else:
        PD_NURSES = [
            ("Quality assurance meetings",                               "1"),
            ("Seminars, conferences, workshops",                         "2"),
            ("Independent professional development: scholarships",       "3"),
            ("Independent professional development: research grants",    "4"),
            ("LGU/DOH led workshops/initiatives",                        "5"),
            ("No forms of professional development are provided",        "6"),
            ("Other (specify)",                                          "7"),
        ]

    items = []
    items.extend(select_all("Q163_HR_CHALL",
                            "163. What challenges in human resources do you have?", Q163_CHALL))
    items.append(alpha("Q164_IMPROVEMENT_AREA",
                       "164. What area do you find the most room for improvement in your staff?", length=240))
    items.extend(select_all("Q165_PD_DOCTORS",
                            "165. What forms of professional development do you provide to your doctors?",
                            PD_DOCTORS))
    items.extend(select_all("Q166_PD_NURSES",
                            "166. What forms of professional development do you provide to your nurses?" +
                            (" [PENDING DESIGN: printed list omits audits]" if not Q166_NURSES_INCLUDE_AUDITS else ""),
                            PD_NURSES))
    return record("H_HUMAN_RESOURCES", "H. Human Resources for Health", "9", items)

def build_secondary_data_stubs():
    """Bug #2 — secondary data records. Structure is PENDING DESIGN so we emit
    empty stubs that exist in the dictionary but contain no items yet."""
    if not SECONDARY_DATA_AS_STUBS:
        raise NotImplementedError("Non-stub secondary data structure not yet decided")
    return [
        record("SEC_HOSP_CENSUS",   "Secondary Data — Hospital Census 6mo (PENDING DESIGN)", "J", []),
        record("SEC_HCW_ROSTER",    "Secondary Data — HCW Full/Part-time Roster (PENDING DESIGN)", "K", []),
        record("SEC_YK_SERVICES",   "Secondary Data — YAKAP Services Availability (PENDING DESIGN)", "L", []),
        record("SEC_LAB_PRICES",    "Secondary Data — Lab Procurement vs Charged Prices (PENDING DESIGN)", "M", []),
    ]


# ============================================================
# 8. ASSEMBLE THE DICTIONARY
# ============================================================

def build_capture_record():
    """GPS metadata + verification photo capture record (record type 'Z').
    Items are off-form (wired via onfocus in the .app); see
    shared/Capture-Helpers.apc for the capture logic."""
    return record(
        "REC_FACILITY_CAPTURE", "Facility GPS and Verification Photo", "Z",
        items=(
            _gps_fields(prefix="FACILITY_")
            + _photo_block(prefix="")
        ),
    )


def build_dictionary():
    records = [
        # Root record (recordType "1") — required by CSPro hierarchy
        record("FACILITYHEADSURVEY_REC", "FacilityHeadSurvey Record", "1", []),
        build_field_control(),
        build_geo_id("facility"),
        build_capture_record(),
        build_section_a(),
        build_section_b(),
        build_section_c(),
        build_section_d(),
        build_section_e(),
        build_section_f(),
        build_section_g(),
        build_section_h(),
    ]

    return {
        "software": "CSPro",
        "version": 8.0,
        "fileType": "dictionary",
        "name": "FACILITYHEADSURVEY_DICT",
        "labels": [{"text": "FacilityHeadSurvey"}],
        "readOptimization": True,
        "recordType": {"start": 1, "length": 1},
        "defaults": {"decimalMark": True, "zeroFill": False},
        "relativePositions": True,
        "levels": [
            {
                "name": "FACILITYHEADSURVEY_LEVEL",
                "labels": [{"text": "FacilityHeadSurvey Level"}],
                "ids": {
                    "items": [
                        {
                            "name": "QUESTIONNAIRE_NO",
                            "labels": [{"text": "Questionnaire No"}],
                            "contentType": "numeric",
                            "start": 2,
                            "length": 6,
                            "zeroFill": True,
                        }
                    ]
                },
                "records": records,
            }
        ],
    }


def main():
    out_path = Path(__file__).parent / "FacilityHeadSurvey.dcf"
    dictionary = build_dictionary()
    out_path.write_text(json.dumps(dictionary, indent=2), encoding="utf-8")

    # Diagnostics
    record_count = len(dictionary["levels"][0]["records"])
    item_count = sum(len(r["items"]) for r in dictionary["levels"][0]["records"])
    print(f"Wrote {out_path}")
    print(f"  Records: {record_count}")
    print(f"  Items:   {item_count}")


if __name__ == "__main__":
    main()
