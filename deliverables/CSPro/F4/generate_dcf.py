"""
generate_dcf.py — F4 Household Survey CSPro Data Dictionary generator.

Emits HouseholdSurvey.dcf in CSPro 8.0 JSON dictionary format from the
April 8 2026 Annex F4 questionnaire.

Run:
    python generate_dcf.py        # writes HouseholdSurvey.dcf next to this file
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import (
    YES_NO, YES_NO_DK, YES_NO_NA, SATISFACTION_5PT,
    numeric, alpha, yes_no, yes_no_dk, yes_no_na,
    select_one, select_all, record,
    build_field_control, build_geo_id, build_dictionary, write_dcf,
)


# ============================================================
# FIELD CONTROL — shared + HH listing ref
# ============================================================

def build_f4_field_control():
    extra = [
        numeric("HH_LISTING_NO", "Household Listing Reference Number", length=4, zero_fill=True),
    ]
    return build_field_control(extra_items=extra, date_label_entity="the Household")


# ============================================================
# GEO ID — household mode
# ============================================================

def build_f4_geo_id():
    return build_geo_id(mode="household")


# ============================================================
# Section A. Informed Consent (Q1)
# ============================================================

def build_section_a():
    items = [
        yes_no("Q1_CONSENT", "1. Do you voluntarily agree to participate in this survey?"),
    ]
    return record("A_INFORMED_CONSENT", "A. Informed Consent", "C", items)


# ============================================================
# Section B. Respondent Profile (Q2-Q29)
# ============================================================

def build_section_b():
    Q5_CIVIL_STATUS = [
        ("Single",    "1"),
        ("Married",   "2"),
        ("Widowed",   "3"),
        ("Separated", "4"),
        ("Divorced",  "5"),
    ]
    Q6_EDUCATION = [
        ("No formal education",      "01"),
        ("Elementary (incomplete)",   "02"),
        ("Elementary (complete)",     "03"),
        ("High School (incomplete)",  "04"),
        ("High School (complete)",    "05"),
        ("Vocational / Technical",    "06"),
        ("College (incomplete)",      "07"),
        ("College (complete)",        "08"),
        ("Post-graduate",             "09"),
        ("I don't know",              "99"),
    ]
    Q7_EMPLOYMENT = [
        ("Employed (full-time)",  "1"),
        ("Employed (part-time)",  "2"),
        ("Self-employed",         "3"),
        ("Unemployed",            "4"),
        ("Retired",               "5"),
        ("Student",               "6"),
        ("Homemaker",             "7"),
        ("Other (specify)",       "8"),
    ]
    Q9_INCOME = [
        ("Below PHP 10,957 (poor)",              "1"),
        ("PHP 10,957 - PHP 21,914 (low income)", "2"),
        ("PHP 21,914 - PHP 43,828 (lower middle)","3"),
        ("PHP 43,828 - PHP 76,669 (middle)",      "4"),
        ("PHP 76,669 - PHP 131,484 (upper middle)","5"),
        ("PHP 131,484 - PHP 219,140 (upper income)","6"),
        ("Above PHP 219,140 (rich)",               "7"),
        ("Refused to answer",                      "8"),
        ("I don't know",                           "9"),
    ]
    items = [
        alpha("Q2_NAME", "2. What is the name of the respondent? (Last Name, First Name, MI)", length=80),
        numeric("Q3_AGE", "3. How old are you (in years), as of your last birthday?", length=3),
        numeric("Q4_SEX", "4. What is your sex assigned at birth?", length=1,
                value_set_options=[("Male", "1"), ("Female", "2")]),
        select_one("Q5_CIVIL_STATUS", "5. What is your civil status?", Q5_CIVIL_STATUS, length=1),
        select_one("Q6_EDUCATION", "6. What is your highest educational attainment?", Q6_EDUCATION, length=2),
        select_one("Q7_EMPLOYMENT", "7. What is your current employment status?", Q7_EMPLOYMENT, length=1),
        alpha("Q7_OTHER_TXT", "7. Employment — Other (specify) text", length=120),
        numeric("Q8_HH_SIZE", "8. How many members are there in your household?", length=2),
        select_one("Q9_INCOME", "9. Estimated average monthly household income", Q9_INCOME, length=1),
        yes_no_dk("Q10_INDIGENOUS", "10. Do you identify as a member of an indigenous group?"),
        alpha("Q10_INDIGENOUS_TXT", "10a. Name of indigenous group", length=80),
        yes_no("Q11_PWD", "11. Are you a person with disability (PWD)?"),
    ]
    return record("B_RESPONDENT_PROFILE", "B. Respondent Profile", "D", items)


# ============================================================
# Section C. Household Roster (Q30-Q50) — REPEATING, max_occurs=20
# Sub-tables C1-C5 flattened into single repeating record
# ============================================================

def build_section_c():
    Q34_RELATIONSHIP = [
        ("Head",              "01"),
        ("Spouse",            "02"),
        ("Son/Daughter",      "03"),
        ("Son-in-law/Daughter-in-law","04"),
        ("Grandchild",        "05"),
        ("Parent",            "06"),
        ("Brother/Sister",    "07"),
        ("Other relative",    "08"),
        ("Non-relative",      "09"),
    ]
    Q36_DISABILITY = [
        ("None",           "1"),
        ("Visual",         "2"),
        ("Hearing",        "3"),
        ("Physical",       "4"),
        ("Intellectual",   "5"),
        ("Psychosocial",   "6"),
        ("Multiple",       "7"),
        ("Other (specify)","8"),
    ]
    Q39_CIVIL = [
        ("Single",    "1"),
        ("Married",   "2"),
        ("Widowed",   "3"),
        ("Separated", "4"),
        ("Divorced",  "5"),
        ("Not applicable (below 15)","9"),
    ]
    Q40_EDUCATION = [
        ("No formal education",      "01"),
        ("Elementary (incomplete)",   "02"),
        ("Elementary (complete)",     "03"),
        ("High School (incomplete)",  "04"),
        ("High School (complete)",    "05"),
        ("Vocational / Technical",    "06"),
        ("College (incomplete)",      "07"),
        ("College (complete)",        "08"),
        ("Post-graduate",             "09"),
        ("Not applicable (below 5)",  "98"),
        ("I don't know",              "99"),
    ]
    Q41_EMPLOYMENT = [
        ("Employed (full-time)",  "1"),
        ("Employed (part-time)",  "2"),
        ("Self-employed",         "3"),
        ("Unemployed",            "4"),
        ("Retired",               "5"),
        ("Student",               "6"),
        ("Homemaker",             "7"),
        ("Not applicable",        "8"),
        ("Other (specify)",       "9"),
    ]
    Q45_PHILHEALTH_STATUS = [
        ("Member (direct contributor)",  "1"),
        ("Dependent",                    "2"),
        ("Indigent / sponsored member",  "3"),
        ("Senior citizen",               "4"),
        ("Not a member",                 "5"),
        ("I don't know",                 "6"),
    ]
    Q46_MEMBER_TYPE = [
        ("Employed (private sector)",      "01"),
        ("Employed (government)",          "02"),
        ("Self-employed / Informal sector","03"),
        ("Voluntary / Individual paying",  "04"),
        ("Overseas Filipino Worker (OFW)", "05"),
        ("Sponsored (LGU/National Gov't)", "06"),
        ("Indigent",                       "07"),
        ("Senior citizen",                 "08"),
        ("Lifetime member",                "09"),
        ("I don't know",                   "99"),
    ]
    items = [
        numeric("MEMBER_LINE_NO", "Household Member Line Number", length=2, zero_fill=True),
        # C1: Basic demographic
        alpha("Q30_NAME", "30. Name of household member", length=80),
        numeric("Q31_PRESENT", "31. Is this member present or away?", length=1,
                value_set_options=[("Present","1"),("Away","2")]),
        numeric("Q32_AGE", "32. Age (years)", length=3),
        numeric("Q33_SEX", "33. Sex assigned at birth", length=1,
                value_set_options=[("Male","1"),("Female","2")]),
        select_one("Q34_RELATIONSHIP", "34. Relationship to household head", Q34_RELATIONSHIP, length=2),
        # C2: Disability
        yes_no("Q35_HAS_DISABILITY", "35. Does this member have a disability?"),
        select_one("Q36_DISABILITY_TYPE", "36. Type of disability", Q36_DISABILITY, length=1),
        alpha("Q36_OTHER_TXT", "36. Disability — Other (specify) text", length=80),
        yes_no("Q37_DISABILITY_ID", "37. Does this member have a PWD ID?"),
        yes_no("Q38_DISABILITY_BENEFITS", "38. Does this member receive any disability benefits?"),
        # C3: Civil status, education, employment
        select_one("Q39_CIVIL_STATUS", "39. Civil status", Q39_CIVIL, length=1),
        select_one("Q40_EDUCATION", "40. Highest educational attainment", Q40_EDUCATION, length=2),
        select_one("Q41_EMPLOYMENT", "41. Current employment status", Q41_EMPLOYMENT, length=1),
        alpha("Q41_OTHER_TXT", "41. Employment — Other (specify) text", length=80),
        # C4: Social insurance coverage
        yes_no_dk("Q42_GSIS", "42. Is this member covered by GSIS?"),
        yes_no_dk("Q43_SSS", "43. Is this member covered by SSS?"),
        yes_no_dk("Q44_PAGIBIG", "44. Is this member covered by Pag-IBIG?"),
        # C5: PhilHealth and insurance
        select_one("Q45_PHILHEALTH", "45. PhilHealth membership status", Q45_PHILHEALTH_STATUS, length=1),
        select_one("Q46_PH_TYPE", "46. Type of PhilHealth membership", Q46_MEMBER_TYPE, length=2),
        yes_no_dk("Q47_PH_ACTIVE", "47. Is PhilHealth membership currently active?"),
        yes_no_dk("Q48_PH_ID", "48. Does this member have a PhilHealth ID?"),
        yes_no_dk("Q49_PRIVATE_INS", "49. Does this member have private health insurance/HMO?"),
        alpha("Q50_PRIVATE_INS_NAME", "50. Name of private insurance provider", length=80),
    ]
    return record("C_HOUSEHOLD_ROSTER", "C. Household Roster", "E", items, max_occurs=20)


# ============================================================
# Section D. UHC Awareness (Q51-Q60)
# ============================================================

def build_section_d():
    Q52_SOURCE = [
        ("News",                "1"),
        ("Legislation",         "2"),
        ("Social Media",        "3"),
        ("Friends / Family",    "4"),
        ("Health center/facility","5"),
        ("LGU/Barangay",        "6"),
        ("I don't know",        "7"),
        ("Other (specify)",     "8"),
    ]
    Q54_UNDERSTANDING = [
        ("Free healthcare for all Filipinos",                       "1"),
        ("Government provides financial assistance for health",     "2"),
        ("All Filipinos are automatically enrolled in PhilHealth",  "3"),
        ("Primary care provider for every Filipino",                "4"),
        ("Access to quality healthcare for everyone",               "5"),
        ("I don't know",                                            "6"),
        ("Other (specify)",                                         "7"),
    ]
    items = [
        yes_no_dk("Q51_UHC_HEARD", "51. Have you heard about Universal Health Care (UHC)?"),
        *select_all("Q52_UHC_SOURCE", "52. Sources of information about UHC", Q52_SOURCE),
        yes_no_dk("Q53_UHC_LAW_AWARE", "53. Are you aware that UHC is a law?"),
        *select_all("Q54_UHC_UNDERSTAND", "54. What is your understanding about UHC?", Q54_UNDERSTANDING),
    ]
    return record("D_UHC_AWARENESS", "D. UHC Awareness", "F", items)


# ============================================================
# Section E. YAKAP/Konsulta Awareness (Q61-Q68)
# ============================================================

def build_section_e():
    Q62_SOURCE = [
        ("News",                 "01"),
        ("Legislation",          "02"),
        ("Social Media",         "03"),
        ("Friends / Family",     "04"),
        ("Health center/facility","05"),
        ("PhilHealth",           "06"),
        ("LGU/Barangay",        "07"),
        ("BHW",                  "08"),
        ("I don't know",         "09"),
        ("Other (specify)",     "10"),
    ]
    items = [
        yes_no_dk("Q61_YAKAP_HEARD", "61. Have you heard about YAKAP/Konsulta?"),
        *select_all("Q62_YAKAP_SOURCE", "62. Sources of information about YAKAP/Konsulta", Q62_SOURCE),
        yes_no_dk("Q63_KONSULTA_ENROLLED", "63. Are you or any HH member enrolled in a Konsulta provider?"),
        yes_no_dk("Q64_KONSULTA_USED", "64. Have you used any Konsulta services in the past 12 months?"),
        yes_no("Q65_KONSULTA_SATISFIED", "65. Were you satisfied with the Konsulta services?"),
    ]
    return record("E_YAKAP_KONSULTA", "E. YAKAP/Konsulta Awareness", "G", items)


# ============================================================
# Section F. BUCAS Awareness (Q69-Q72)
# ============================================================

def build_section_f():
    items = [
        yes_no_dk("Q69_BUCAS_HEARD", "69. Have you heard about BUCAS?"),
        yes_no("Q70_BUCAS_ENROLLED", "70. Are you or any HH member enrolled in BUCAS?"),
        yes_no("Q71_BUCAS_USED", "71. Have you used any BUCAS services?"),
        yes_no("Q72_BUCAS_SATISFIED", "72. Were you satisfied with the BUCAS services?"),
    ]
    return record("F_BUCAS_AWARENESS", "F. BUCAS Awareness", "H", items)


# ============================================================
# Section G. Access to Medicines (Q73-Q78)
# ============================================================

def build_section_g():
    items = [
        yes_no_dk("Q73_GAMOT_HEARD", "73. Have you heard of GAMOT (DOH medicine access program)?"),
        yes_no("Q74_GAMOT_USED", "74. Have you used GAMOT?"),
        yes_no_dk("Q75_GENERIC_AWARE", "75. Are you aware of the Generics Act / generic medicines?"),
        yes_no("Q76_GENERIC_PREFER", "76. Do you prefer generic over branded medicines?"),
        yes_no("Q77_MEDS_ACCESSIBLE", "77. Do you find medicines accessible and affordable?"),
        yes_no("Q78_BOTIKA_AWARE", "78. Are you aware of Botika ng Barangay / Botika ng Bayan?"),
    ]
    return record("G_ACCESS_MEDICINES", "G. Access to Medicines", "I", items)


# ============================================================
# Section H. PhilHealth Registration (Q79-Q88) — REPEATING per member
# ============================================================

def build_section_h():
    Q79_REG_SOURCE = [
        ("PhilHealth representative","01"),
        ("No one / self-registered", "02"),
        ("LGU",                      "03"),
        ("Barangay Health Worker",   "04"),
        ("Primary care provider",    "05"),
        ("Friends / Family",         "06"),
        ("Other health care provider","07"),
        ("Health center/facility",   "08"),
        ("Employer",                 "09"),
        ("Other (specify)",          "10"),
    ]
    Q82_DIFFICULTY_REASONS = [
        ("Unclear process",                                 "1"),
        ("Took a long time",                                "2"),
        ("Did not know where to ask for help",              "3"),
        ("Had to travel a long way",                        "4"),
        ("No valid ID",                                     "5"),
        ("Did not know the required documents to register", "6"),
        ("I don't know",                                    "7"),
        ("Other (specify)",                                 "8"),
    ]
    Q85_BENEFITS = [
        ("No balance billing for basic ward accommodation","1"),
        ("Subsidized inpatient services",                  "2"),
        ("Subsidized outpatient services",                 "3"),
        ("There are no benefits to being a member",        "4"),
        ("I don't know",                                   "5"),
        ("Other (specify)",                                "6"),
    ]
    Q86_PREMIUM_PAY = [
        ("Yes, I pay directly",     "1"),
        ("Yes, my employer pays",   "2"),
        ("No, I do not pay premiums","3"),
    ]
    Q88_DIFF_PAYING = [
        ("Cannot afford the premium",                     "1"),
        ("Payment options are inconvenient",              "2"),
        ("No time to pay",                                "3"),
        ("Don't see value in paying",                     "4"),
        ("System of PhilHealth is unreliable/usually down","5"),
        ("I don't know",                                   "6"),
        ("Other (specify)",                                "7"),
    ]
    items = [
        numeric("MEMBER_LINE_NO", "Household Member Line Number", length=2, zero_fill=True),
        select_one("Q79_REG_SOURCE", "79. How did you find out about how to register to PhilHealth?",
                   Q79_REG_SOURCE, length=2),
        alpha("Q79_OTHER_TXT", "79. Registration source — Other (specify) text", length=80),
        select_one("Q80_ASSIST", "80. Who assisted you in the registration process?",
                   Q79_REG_SOURCE, length=2),
        alpha("Q80_OTHER_TXT", "80. Registration assistant — Other (specify) text", length=80),
        yes_no("Q81_REG_DIFFICULTY", "81. Did you have any difficulties in the registration process?"),
        *select_all("Q82_DIFFICULTY", "82. What did you find difficult?", Q82_DIFFICULTY_REASONS),
        yes_no("Q83_KNOWS_ASSIST", "83. Would you know where to seek assistance?"),
        alpha("Q84_WHERE_ASSIST", "84. Where would you go to seek assistance?", length=120),
        *select_all("Q85_BENEFITS", "85. What are some benefits of being a PhilHealth member?", Q85_BENEFITS),
        select_one("Q86_PREMIUM_PAY", "86. Do you pay PhilHealth premiums every month?", Q86_PREMIUM_PAY, length=1),
        yes_no("Q87_PREMIUM_DIFFICULT", "87. Do you find it difficult to pay premiums?"),
        *select_all("Q88_DIFF_PAYING", "88. Why did you find it difficult?", Q88_DIFF_PAYING),
    ]
    return record("H_PHILHEALTH_REG", "H. PhilHealth Registration", "J", items, max_occurs=20)


# ============================================================
# Section I. Primary Care Utilization (Q89-Q100)
# ============================================================

def build_section_i():
    Q92_FACILITY_TYPE = [
        ("YAKAP/Konsulta or primary care provider",     "01"),
        ("Barangay Health Center",                      "02"),
        ("Rural Health Unit / Health Center",            "03"),
        ("Public Hospital",                             "04"),
        ("Private Hospital",                            "05"),
        ("Private Clinic",                              "06"),
        ("Traditional Healer or Manghihilot/Albularyo", "07"),
        ("I don't know",                                "08"),
        ("Other (specify)",                             "09"),
    ]
    Q93_WHY_NOT = [
        ("I don't get sick",              "1"),
        ("I recently moved into the area","2"),
        ("It's expensive",                "3"),
        ("I can treat myself",            "4"),
        ("I don't know where to go",      "5"),
        ("I don't know",                  "6"),
        ("Other (specify)",               "7"),
    ]
    Q94_TRANSPORT = [
        ("Walk",                                "01"),
        ("Bike",                                "02"),
        ("Public Bus",                          "03"),
        ("Jeepney",                             "04"),
        ("Tricycle",                            "05"),
        ("Car (including private taxi/cab)",     "06"),
        ("Motorcycle",                          "07"),
        ("Boat",                                "08"),
        ("Taxi",                                "09"),
        ("Pedicab",                             "10"),
        ("E-bike",                              "11"),
        ("Other (specify)",                     "12"),
    ]
    items = [
        yes_no_dk("Q89_HAS_USUAL_FACILITY",
                  "89. In the past 12 months, do you have a clinic or health center that you usually go to?"),
        alpha("Q89A_FACILITY_NAME", "89a. What is the name of the facility?", length=120),
        yes_no("Q90_IS_USUAL", "90. Is this the facility you usually go to for general health concerns?"),
        *select_all("Q91_WHY_DIFF", "91. Why did you go to this facility?", [
            ("More accessible than usual facility","1"),("Needed specialist not available","2"),
            ("Recommended by friends/family","3"),("Wanted to try another facility","4"),
            ("Prefer this facility","5"),("Referred by usual facility","6"),
            ("Usual facility closed","7"),("Doctor transferred here","8"),("Other (specify)","9"),
        ]),
        select_one("Q92_FACILITY_TYPE", "92. Type of facility usually visited", Q92_FACILITY_TYPE, length=2),
        *select_all("Q93_WHY_NOT", "93. Why do you not have a usual facility?", Q93_WHY_NOT),
        *select_all("Q94_TRANSPORT", "94. Transportation modes to nearest primary care facility", Q94_TRANSPORT),
        numeric("Q95_TRAVEL_TIME", "95. Travel time to nearest primary care facility (minutes)", length=3),
        numeric("Q96_TRAVEL_COST", "96. Travel cost to facility (PHP, one-way)", length=5),
        yes_no("Q97_KNOWS_BOOKING", "97. Do you know how to book an appointment?"),
        select_one("Q98_PHONE_ADVICE", "98. Can you get advice over the phone when facility is open?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4")], length=1),
        select_one("Q99_AFTER_HOURS", "99. Is there a phone number to call when facility is closed?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4")], length=1),
        select_one("Q100_LEAVE_WORK", "100. Do you have to take leave to visit?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4"),("Not applicable","9")], length=1),
    ]
    return record("I_PRIMARY_CARE", "I. Primary Care Utilization", "K", items)


# ============================================================
# Section J. Health-Seeking Behavior (Q101-Q107) — REPEATING per member
# ============================================================

def build_section_j():
    Q101_CHECKUP_FREQ = [
        ("More than once a year",          "1"),
        ("Every year",                     "2"),
        ("Every 2-3 years",               "3"),
        ("Every 4-5 years",               "4"),
        ("No set time; once or twice ever","5"),
        ("Never; only when sick",          "6"),
        ("Other (specify)",                "7"),
    ]
    Q102_VISIT_REASON = [
        ("Consultation for new health problem",  "1"),
        ("Follow-up ongoing health problem",     "2"),
        ("For tests/diagnostics only",           "3"),
        ("For a general check-up",               "4"),
        ("Health certificate/administrative",     "5"),
        ("Immunizations/vaccinations",            "6"),
        ("Doctor transferred to this facility",   "7"),
        ("Other (specify)",                       "8"),
    ]
    Q103_CARE_TYPE = [
        ("Outpatient care",           "1"),
        ("Inpatient care",            "2"),
        ("Emergency care",            "3"),
        ("Primary care consultation", "4"),
        ("Other (specify)",           "5"),
    ]
    Q106_FORGONE_WHY = [
        ("Not sick enough",                     "1"),
        ("It's too expensive",                  "2"),
        ("Could not take time off work",        "3"),
        ("Could not get appointment soon enough","4"),
        ("No transportation available",         "5"),
        ("Afraid to know my illness",           "6"),
        ("I don't know",                        "7"),
        ("Other (specify)",                     "8"),
    ]
    Q107_ACTIONS = [
        ("Visited other healthcare facility",  "1"),
        ("Sought alternative care",            "2"),
        ("Sought telemedicine",                "3"),
        ("Used home care",                     "4"),
        ("Bought medicine from a pharmacy",    "5"),
        ("Did not seek other forms of care",   "6"),
        ("Other (specify)",                    "7"),
    ]
    items = [
        numeric("MEMBER_LINE_NO", "Household Member Line Number", length=2, zero_fill=True),
        select_one("Q101_CHECKUP_FREQ", "101. How often do you have a general check-up?",
                   Q101_CHECKUP_FREQ, length=1),
        *select_all("Q102_VISIT_REASON", "102. Why would you visit a health facility?", Q102_VISIT_REASON),
        *select_all("Q103_CARE_TYPE", "103. Forms of care accessed in the last 6 months", Q103_CARE_TYPE),
        yes_no("Q104_PREVENTIVE", "104. Have you consulted a physician for preventative reasons?"),
        yes_no("Q105_FORGONE", "105. In the last 6 months, had a medical problem and chose NOT to see a provider?"),
        *select_all("Q106_FORGONE_WHY", "106. Why not?", Q106_FORGONE_WHY),
        *select_all("Q107_ACTIONS", "107. Other actions taken to improve health?", Q107_ACTIONS),
    ]
    return record("J_HEALTH_SEEKING", "J. Health-Seeking Behavior", "L", items, max_occurs=20)


# ============================================================
# Section K. Referrals (Q108-Q125)
# ============================================================

def build_section_k():
    Q109_TYPE = [
        ("Outpatient care",   "01"),
        ("Emergency care",    "02"),
        ("Inpatient care",    "03"),
        ("Dental care",       "04"),
        ("Other facility",    "05"),
        ("Special therapy",   "06"),
        ("Alternative care",  "07"),
        ("Medical mission",   "08"),
        ("Home healthcare",   "09"),
        ("Telemedicine",      "10"),
        ("None of the above", "11"),
        ("Other (specify)",   "12"),
    ]
    Q110_SPECIALIST = [
        ("No specialty",          "01"),("Anesthesia",            "02"),
        ("Dermatology",           "03"),("Emergency Medicine",    "04"),
        ("Family Medicine",       "05"),("General Surgery",       "06"),
        ("Internal Medicine",     "07"),("Neurology",             "08"),
        ("Nuclear Medicine",      "09"),("Obstetrics and Gynecology","10"),
        ("Occupational Medicine", "11"),("Ophthalmology",         "12"),
        ("Orthopedics",           "13"),("Otorhinolaryngology (ENT)","14"),
        ("Pathology",             "15"),("Pediatrics",            "16"),
        ("Physical and Rehabilitation Medicine","17"),("Psychiatry","18"),
        ("Public health",         "19"),("Radiology",             "20"),
        ("Research",              "21"),("I don't know",          "22"),
        ("Other (specify)",       "23"),
    ]
    Q111_METHOD = [
        ("Physical referral slip",  "1"),
        ("E-referral",              "2"),
        ("Phone call",              "3"),
        ("I don't know",            "4"),
        ("Other (specify)",         "5"),
    ]
    Q112_VISIT = [
        ("Yes",                          "1"),
        ("No, I'm not planning to",      "2"),
        ("Not yet, but I'm planning to", "3"),
    ]
    Q113_WHY_NOT = [
        ("Facility is too far",              "1"),
        ("Do not trust the referred facility","2"),
        ("No time",                          "3"),
        ("Worried about additional costs",   "4"),
        ("Not needed",                       "5"),
        ("Don't know how to get to facility","6"),
        ("Other (specify)",                  "7"),
    ]
    Q121_WHY_HOSPITAL = [
        ("Referred by other specialist",       "1"),
        ("Nearest facility to house",          "2"),
        ("Facility is usual source of care",   "3"),
        ("Only place for certain test",        "4"),
        ("Referred by BHW/nurse/midwife",      "5"),
        ("Referred by family / friends",       "6"),
        ("Offers subsidized/free services",    "7"),
        ("I don't know",                       "8"),
        ("Other (specify)",                    "9"),
    ]
    items = [
        yes_no("Q108_REFERRED", "108. Were you referred to another facility in the past 6 months?"),
        *select_all("Q109_TYPE", "109. What type of care was the referral for?", Q109_TYPE),
        select_one("Q110_SPECIALIST", "110. What kind of specialist was recommended?", Q110_SPECIALIST, length=2),
        alpha("Q110_OTHER_TXT", "110. Specialist — Other (specify) text", length=80),
        select_one("Q111_METHOD", "111. How did they refer you?", Q111_METHOD, length=1),
        alpha("Q111_OTHER_TXT", "111. Referral method — Other (specify) text", length=80),
        select_one("Q112_VISITED", "112. Did you visit another facility after the referral?", Q112_VISIT, length=1),
        *select_all("Q113_WHY_NOT", "113. Why are you not planning to visit?", Q113_WHY_NOT),
        yes_no("Q114_DISCUSSED", "114. Did they discuss different places you could go?"),
        yes_no("Q115_HELPED_APPT", "115. Did they help you make the appointment?"),
        yes_no("Q116_WROTE_INFO", "116. Did they write down information for the specialist?"),
        yes_no("Q117_FOLLOWUP", "117. Did they follow up with you about what happened?"),
        select_one("Q118_SAT_REFERRAL", "118. Satisfaction with the referral process", SATISFACTION_5PT, length=1),
        yes_no("Q119_WAS_REFERRAL", "119. Was the visit a referral from your primary care facility?"),
        yes_no_dk("Q120_PCP_KNOWS", "120. Does your primary care provider know about the visit?"),
        *select_all("Q121_WHY_HOSPITAL", "121. Why did you decide to visit a hospital?", Q121_WHY_HOSPITAL),
        yes_no("Q122_PCP_DISCUSSED", "122. Did your PCP discuss different places to go?"),
        yes_no("Q123_PCP_HELPED_APPT", "123. Did your PCP help make the appointment?"),
        yes_no("Q124_PCP_WROTE_INFO", "124. Did your PCP write down information for the specialist?"),
        select_one("Q125_SAT_REFERRAL2", "125. Overall satisfaction with referral experience", SATISFACTION_5PT, length=1),
    ]
    return record("K_REFERRALS", "K. Referrals", "M", items)


# ============================================================
# Section L. NBB Awareness (Q126-Q131)
# ============================================================

def build_section_l():
    Q127_SOURCE = [
        ("News",                "1"),
        ("Legislation",         "2"),
        ("Social Media",        "3"),
        ("Friends / Family",    "4"),
        ("Health center/facility","5"),
        ("LGU/Barangay",        "6"),
        ("I don't know",        "7"),
        ("Other (specify)",     "8"),
    ]
    Q128_UNDERSTANDING = [
        ("Patient does not pay any hospital bill",          "1"),
        ("PhilHealth will cover cost of treatment",         "2"),
        ("Medicine and service are already included",       "3"),
        ("No cash payment required upon discharge",         "4"),
        ("Applies only to certain patients or hospitals",   "5"),
        ("Bills settled between hospital and PhilHealth",   "6"),
        ("Patients should not be charged extra fees",       "7"),
        ("I don't know",                                    "8"),
        ("Other (specify)",                                 "9"),
    ]
    Q130_HOSPITAL_TYPE = [
        ("Public",                "1"),
        ("DOH-retained hospital", "2"),
        ("Private",               "3"),
    ]
    items = [
        yes_no_dk("Q126_NBB_HEARD", "126. Have you heard of the No Balance Billing (NBB)?"),
        *select_all("Q127_NBB_SOURCE", "127. Sources of information about NBB", Q127_SOURCE),
        *select_all("Q128_NBB_UNDERSTAND", "128. What is your understanding about NBB?", Q128_UNDERSTANDING),
        yes_no_dk("Q129_CONFINED", "129. Were you or a HH member confined in a hospital in the past 6 months?"),
        select_one("Q130_HOSPITAL_TYPE", "130. For the most recent hospitalization, what type of hospital?",
                   Q130_HOSPITAL_TYPE, length=1),
        yes_no_dk("Q131_NBB_OOP", "131. During hospitalization in a DOH-retained hospital, did you pay OOP that should have been covered under NBB?"),
    ]
    return record("L_NBB_AWARENESS", "L. NBB Awareness", "N", items)


# ============================================================
# Section M. ZBB Awareness (Q132-Q141)
# ============================================================

def build_section_m():
    Q133_SOURCE = [
        ("News",                "1"),
        ("Legislation",         "2"),
        ("Social Media",        "3"),
        ("Friends / Family",    "4"),
        ("Health center/facility","5"),
        ("LGU/Barangay",        "6"),
        ("I don't know",        "7"),
        ("Other (specify)",     "8"),
    ]
    Q134_UNDERSTANDING = [
        ("Patient does not pay any hospital bill",          "1"),
        ("PhilHealth will cover cost of treatment",         "2"),
        ("Medicine and service are already included",       "3"),
        ("No cash payment required upon discharge",         "4"),
        ("Applies only to certain patients or hospitals",   "5"),
        ("Bills settled between hospital and PhilHealth",   "6"),
        ("Patients should not be charged extra fees",       "7"),
        ("I don't know",                                    "8"),
        ("Other (specify)",                                 "9"),
    ]
    Q136_MOST_EXPENSIVE = [
        ("Medicine",          "1"),
        ("Laboratory Tests",  "2"),
        ("Medical Supplies",  "3"),
        ("Doctor's Fee",      "4"),
    ]
    items = [
        yes_no_dk("Q132_ZBB_HEARD", "132. Have you heard of the Zero Balance Billing (ZBB)?"),
        *select_all("Q133_ZBB_SOURCE", "133. Sources of information about ZBB", Q133_SOURCE),
        *select_all("Q134_ZBB_UNDERSTAND", "134. What is your understanding about ZBB?", Q134_UNDERSTANDING),
        yes_no_dk("Q135_ZBB_OOP", "135. During hospitalization in a DOH-retained hospital, did you pay OOP that should have been covered under ZBB?"),
        select_one("Q136_MOST_EXPENSIVE", "136. From your most recent visit, which charge was most expensive?",
                   Q136_MOST_EXPENSIVE, length=1),
        numeric("Q137_FINAL_AMOUNT", "137. Final amount paid in cash at the hospital cashier upon discharge (PHP)", length=8),
        yes_no("Q138_RECALL_BREAKDOWN", "138. Do you recall the breakdown of the bill?"),
        *select_all("Q139_BILL_ITEMS", "139. Which items were included in the bill?", [
            ("Rooms","1"),("Doctor's Fee","2"),("Diagnostic or laboratory procedure","3"),
            ("Medical equipment or supplies","4"),("Medicines or drugs","5"),
            ("Non-medical expenses","6"),("Other expenses","7"),
        ]),
        numeric("Q139A_NO_RECEIPT_AMT", "139a. Amount charged for services with no receipts (PHP)", length=8),
        yes_no("Q140_RECALL_PAYMENT", "140. Do you recall how you paid for your bill?"),
        *select_all("Q141_HOW_PAID", "141. How did you pay?", [
            ("Own income/household income","01"),("PhilHealth","02"),
            ("Private insurance/HMO","03"),("Loan","04"),("Sale of assets","05"),
            ("Donations from charities/NGOs","06"),("Donations from LGUs","07"),
            ("National Government Agencies","08"),("Paid by someone else","09"),
            ("Other (specify)","10"),
        ]),
    ]
    return record("M_ZBB_AWARENESS", "M. ZBB Awareness", "O", items)


# ============================================================
# Section N. Household Expenditures (Q142-Q180)
# Flat item batteries: each item has consumed (Y/N), purchased_amt, in_kind_amt
# Reference periods vary: weekly, monthly, 6-month, 12-month
# ============================================================

def _expenditure_item(prefix, label):
    """Three items per expenditure line: consumed Y/N, purchased amount, in-kind value."""
    return [
        yes_no(f"{prefix}_CONSUMED", f"{label} — Consumed?"),
        numeric(f"{prefix}_PURCHASED", f"{label} — Amount purchased (PHP)", length=8),
        numeric(f"{prefix}_INKIND", f"{label} — Estimated in-kind value (PHP)", length=8),
    ]

def build_section_n():
    items = []

    # A. Food Items (last WEEK) — Q142-Q155
    food_items = [
        ("Q142_CEREALS",     "142. Cereals (rice, flour, noodles, corn)"),
        ("Q143_PULSES",      "143. Pulses, roots, tubers, plantains, nuts"),
        ("Q144_VEGETABLES",  "144. Vegetables"),
        ("Q145_FRUITS",      "145. Fruits"),
        ("Q146_FISH",        "146. Fish and other seafoods"),
        ("Q147_MEAT",        "147. Any kind of meat and offal"),
        ("Q148_EGGS",        "148. Eggs"),
        ("Q149_MILK",        "149. Milk and milk products"),
        ("Q150_FATS",        "150. Butter, lard, oils and fats"),
        ("Q151_CONDIMENTS",  "151. Condiments, spices, and ready-made meals"),
        ("Q152_BEVERAGES",   "152. Water and non-alcoholic beverages"),
        ("Q153_ALCOHOL",     "153. Alcoholic beverages"),
        ("Q155_RESTAURANT",  "155. Meals and snacks from restaurants"),
    ]
    for prefix, label in food_items:
        items.extend(_expenditure_item(prefix, label))

    # B. Non-food (last WEEK) — Q156
    items.extend(_expenditure_item("Q156_TOBACCO", "156. Smoking and tobacco products"))

    # Non-food (last MONTH) — Q157-Q163
    monthly_nonfood = [
        ("Q157_PERSONAL_CARE", "157. Personal care products"),
        ("Q158_HOUSEHOLD",     "158. Household cleaning and maintenance"),
        ("Q159_TRANSPORT",     "159. Passenger transportation"),
        ("Q160_TELECOM",       "160. Phone, mobile, WiFi, cable TV"),
        ("Q161_RECREATION",    "161. Recreational, cultural, sporting"),
        ("Q162_POSTAL",        "162. Postal services"),
        ("Q163_HOUSING",       "163. Housing (actual/estimated rent)"),
    ]
    for prefix, label in monthly_nonfood:
        items.extend(_expenditure_item(prefix, label))

    # Non-food (last 6 MONTHS) — Q164-Q165
    items.extend(_expenditure_item("Q164_RECREATION_6M", "164. Recreational devices (6-month)"))
    items.extend(_expenditure_item("Q165_CLOTHING",      "165. Clothing, footwear, textiles"))

    # Non-food (last 12 MONTHS) — Q166-Q170
    annual_nonfood = [
        ("Q166_EDUCATION",     "166. Educational services"),
        ("Q167_ACCOMMODATION", "167. Accommodation services"),
        ("Q168_GARDEN_PETS",   "168. Garden and personal pets"),
        ("Q169_HEALTH_INS",    "169. Health insurance"),
        ("Q170_OTHER_INS",     "170. Other insurance"),
    ]
    for prefix, label in annual_nonfood:
        items.extend(_expenditure_item(prefix, label))

    # E. Health Products and Services (last 12 MONTHS) — Q171-Q173
    items.extend(_expenditure_item("Q171_INPATIENT",   "171. Inpatient care services"))
    items.extend(_expenditure_item("Q172_EMERGENCY",   "172. Emergency transportation"))

    # Health (last 6 MONTHS) — Q174-Q178
    health_6m = [
        ("Q174_PREVENTIVE",   "174. Preventive services (immunization)"),
        ("Q175_DIAGNOSTIC",   "175. Diagnostic and laboratory tests"),
        ("Q176_ASSISTIVE",    "176. Assistive health products (vision, hearing, mobility)"),
        ("Q177_MEDICAL_PROD", "177. Medical products (antigen tests, masks)"),
    ]
    for prefix, label in health_6m:
        items.extend(_expenditure_item(prefix, label))

    # Health (last MONTH) — Q179-Q180
    items.extend(_expenditure_item("Q179_MEDICINES",  "179. Medicines, vaccines, pharmaceuticals"))
    items.extend(_expenditure_item("Q180_OUTPATIENT", "180. Outpatient medical and dental services"))

    return record("N_HOUSEHOLD_EXPENDITURES", "N. Household Expenditures", "P", items)


# ============================================================
# Section O. Sources of Funds for Health (Q182-Q192)
# ============================================================

def build_section_o():
    Q191_INCOME_PCT = [
        ("None",          "1"),
        ("Less than 1%",  "2"),
        ("1-3%",          "3"),
        ("4-6%",          "4"),
        ("More than 6%",  "5"),
        ("Don't know",    "6"),
    ]
    Q192_FOREGONE_CARE = [
        ("Doctor/consultation visit",        "1"),
        ("Medicines or treatments",          "2"),
        ("Laboratory tests / diagnostics",   "3"),
        ("Hospital admission / inpatient care","4"),
        ("Preventive care",                  "5"),
        ("Dental care",                      "6"),
        ("Other (specify)",                  "7"),
        ("We do not forego care",            "8"),
    ]
    items = [
        yes_no("Q182_CURRENT_INCOME", "182. Current income of any household members"),
        yes_no("Q183_SAVINGS",        "183. Savings, pension"),
        yes_no("Q184_SOLD_ASSETS",    "184. Selling of household's assets or goods"),
        yes_no("Q185_BORROW_FAMILY",  "185. Borrowing from friends or relatives"),
        yes_no("Q186_BORROW_INST",    "186. Borrowing from institutions"),
        yes_no("Q187_REMITTANCE",     "187. Remittance or money gift"),
        yes_no("Q188_GOVT_ASSIST",    "188. Government assistance (DSWD, local)"),
        yes_no("Q189_LGU_DONATION",   "189. Donation from LGUs"),
        yes_no("Q190_OTHER_SOURCE",   "190. Other source"),
        alpha("Q190_OTHER_TXT",       "190. Other source — specify", length=120),
        select_one("Q191_INCOME_PCT", "191. Portion of income willing to set aside for health care",
                   Q191_INCOME_PCT, length=1),
        *select_all("Q192_FOREGONE", "192. What kind of care do you usually forego for financial reasons?",
                    Q192_FOREGONE_CARE),
    ]
    return record("O_SOURCES_OF_FUNDS", "O. Sources of Funds for Health", "Q", items)


# ============================================================
# Section P. Financial Risk Protection (Q193-Q195)
# ============================================================

def build_section_p():
    Q195_WTP = [
        ("Php 0 - Php 249",        "1"),
        ("Php 250 - Php 499",      "2"),
        ("Php 500 - Php 999",      "3"),
        ("Php 1,000 - Php 1,249",  "4"),
        ("Php 1,250 - Php 1,499",  "5"),
        ("Php 1,500 - Php 1,749",  "6"),
        ("Php 1,750 - Php 1,999",  "7"),
        ("Php 2,000 and above",    "8"),
        ("Other (specify)",         "9"),
    ]
    items = [
        yes_no("Q193_DELAYED_CARE", "193. Delayed seeking care for financial reasons in the last 6 months?"),
        yes_no("Q194_NOT_FOLLOWED", "194. Seen a doctor and not fully followed advice for financial reasons?"),
        select_one("Q195_WTP_CONSULT", "195. Highest amount willing to pay for a consultation", Q195_WTP, length=1),
        alpha("Q195_OTHER_TXT", "195. WTP — Other (specify) text", length=80),
    ]
    return record("P_FINANCIAL_RISK", "P. Financial Risk Protection", "R", items)


# ============================================================
# Section Q. Anxiety about Household Finances (Q196-Q198)
# ============================================================

def build_section_q():
    Q196_REDUCED = [
        ("Yes",              "1"),
        ("No",               "2"),
        ("Don't know",       "3"),
        ("Refused to answer","4"),
    ]
    Q197_WORRIED = [
        ("Very worried",      "1"),
        ("Somewhat worried",  "2"),
        ("Not too worried",   "3"),
        ("Not worried at all","4"),
    ]
    Q198_REASONS = [
        ("Loss of income",                                   "1"),
        ("Healthcare costs related to COVID-19",              "2"),
        ("Healthcare costs NOT related to COVID-19",          "3"),
    ]
    items = [
        select_one("Q196_REDUCED_SPEND", "196. Had to reduce spending on needs because of health expenditure?",
                   Q196_REDUCED, length=1),
        select_one("Q197_WORRIED", "197. How worried are you about household finances in the next month?",
                   Q197_WORRIED, length=1),
        *select_all("Q198_WORRY_REASONS", "198. Reasons for worry about finances", Q198_REASONS, with_other_txt=False),
    ]
    return record("Q_FINANCIAL_ANXIETY", "Q. Financial Anxiety", "S", items)


# ============================================================
# ASSEMBLE THE DICTIONARY
# ============================================================

def build_f4_dictionary():
    records = [
        record("HOUSEHOLDSURVEY_REC", "HouseholdSurvey Record", "1", []),
        build_f4_field_control(),
        build_f4_geo_id(),
        build_section_a(),
        build_section_b(),
        build_section_c(),   # Repeating: max_occurs=20
        build_section_d(),
        build_section_e(),
        build_section_f(),
        build_section_g(),
        build_section_h(),   # Repeating: max_occurs=20
        build_section_i(),
        build_section_j(),   # Repeating: max_occurs=20
        build_section_k(),
        build_section_l(),
        build_section_m(),
        build_section_n(),
        build_section_o(),
        build_section_p(),
        build_section_q(),
    ]
    return build_dictionary(
        dict_name="HOUSEHOLDSURVEY_DICT",
        dict_label="HouseholdSurvey",
        id_item_name="QUESTIONNAIRE_NO",
        id_item_label="Questionnaire No",
        id_length=6,
        records=records,
    )


def main():
    out_path = Path(__file__).parent / "HouseholdSurvey.dcf"
    write_dcf(build_f4_dictionary(), out_path)


if __name__ == "__main__":
    main()
