"""
generate_dcf.py — F3 Patient Survey CSPro Data Dictionary generator.

Emits PatientSurvey.dcf in CSPro 8.0 JSON dictionary format from the
April 8 2026 Annex F3 questionnaire.

Run:
    python generate_dcf.py        # writes PatientSurvey.dcf next to this file
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import (
    YES_NO, YES_NO_DK, YES_NO_NA, UHC9_OPTIONS, SATISFACTION_5PT,
    numeric, alpha, yes_no, yes_no_dk, yes_no_na,
    select_one, select_all, uhc9_item, record,
    build_field_control, build_geo_id, build_dictionary, write_dcf,
)


# ============================================================
# FIELD CONTROL — shared + patient type extra
# ============================================================

def build_f3_field_control():
    extra = [
        numeric("PATIENT_TYPE", "Type of Patient", length=1,
                value_set_options=[("Outpatient", "1"), ("Inpatient", "2")]),
        numeric("PATIENT_LISTING_NO", "Patient Listing Reference Number", length=4, zero_fill=True),
    ]
    return build_field_control(extra_items=extra, date_label_entity="the Patient")


# ============================================================
# GEO ID — facility + patient home
# ============================================================

def build_f3_geo_id():
    return build_geo_id(mode="facility_and_patient")


# ============================================================
# Section A. Informed Consent (Q1)
# ============================================================

def build_section_a():
    items = [
        yes_no("Q1_CONSENT", "1. Do you voluntarily agree to participate in this survey?"),
    ]
    return record("A_INFORMED_CONSENT", "A. Informed Consent", "C", items)


# ============================================================
# Section B. Patient Profile (Q2-Q10)
# ============================================================

def build_section_b():
    Q2_RELATIONSHIP = [
        ("Patient him/herself",          "1"),
        ("Spouse",                       "2"),
        ("Son/Daughter",                 "3"),
        ("Parent",                       "4"),
        ("Sibling",                      "5"),
        ("Other relative",               "6"),
        ("Non-relative (e.g., neighbor)","7"),
    ]
    Q5_CIVIL_STATUS = [
        ("Single",    "1"),
        ("Married",   "2"),
        ("Widowed",   "3"),
        ("Separated", "4"),
        ("Divorced",  "5"),
    ]
    Q6_EDUCATION = [
        ("No formal education",          "01"),
        ("Elementary (incomplete)",       "02"),
        ("Elementary (complete)",         "03"),
        ("High School (incomplete)",      "04"),
        ("High School (complete)",        "05"),
        ("Vocational / Technical",        "06"),
        ("College (incomplete)",          "07"),
        ("College (complete)",            "08"),
        ("Post-graduate",                 "09"),
        ("I don't know",                  "99"),
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
    Q9_INDIGENOUS = [
        ("Yes",          "1"),
        ("No",           "2"),
        ("I don't know", "3"),
    ]
    items = [
        select_one("Q2_RELATIONSHIP", "2. What is the relationship of the respondent to the patient?",
                   Q2_RELATIONSHIP, length=1),
        alpha("Q3_NAME", "3. What is the name of the patient? (Last Name, First Name, Middle Initial)", length=80),
        numeric("Q4_AGE", "4. How old are you (in years), as of your last birthday?", length=3),
        numeric("Q4_SEX", "4b. What is your sex assigned at birth?", length=1,
                value_set_options=[("Male", "1"), ("Female", "2")]),
        select_one("Q5_CIVIL_STATUS", "5. What is your civil status?", Q5_CIVIL_STATUS, length=1),
        select_one("Q6_EDUCATION", "6. What is your highest educational attainment?", Q6_EDUCATION, length=2),
        select_one("Q7_EMPLOYMENT", "7. What is your current employment status?", Q7_EMPLOYMENT, length=1),
        alpha("Q7_OTHER_TXT", "7. Employment — Other (specify) text", length=120),
        numeric("Q8_HH_SIZE", "8. How many members are there in your household, including yourself?", length=2),
        select_one("Q9_INDIGENOUS", "9. Do you identify as a member of an indigenous group?", Q9_INDIGENOUS, length=1),
        alpha("Q9_INDIGENOUS_TXT", "9a. If yes, please specify the name of the indigenous group.", length=80),
        yes_no("Q10_PWD", "10. Are you a person with disability (PWD)?"),
    ]
    return record("B_PATIENT_PROFILE", "B. Patient Profile", "D", items)


# ============================================================
# Section C. UHC Awareness (Q11-Q24)
# ============================================================

def build_section_c():
    Q12_SOURCE = [
        ("News",                "1"),
        ("Legislation",         "2"),
        ("Social Media",        "3"),
        ("Friends / Family",    "4"),
        ("Health center/facility","5"),
        ("LGU/Barangay",        "6"),
        ("I don't know",        "7"),
        ("Other (specify)",     "8"),
    ]
    Q14_UNDERSTANDING = [
        ("Free healthcare for all Filipinos",                       "1"),
        ("Government provides financial assistance for health",     "2"),
        ("All Filipinos are automatically enrolled in PhilHealth",  "3"),
        ("Primary care provider for every Filipino",                "4"),
        ("Access to quality healthcare for everyone",               "5"),
        ("I don't know",                                            "6"),
        ("Other (specify)",                                         "7"),
    ]
    items = [
        yes_no_dk("Q11_UHC_HEARD", "11. Have you heard about Universal Health Care (UHC) prior to this survey?"),
        *select_all("Q12_UHC_SOURCE", "12. What are your sources of information about UHC?", Q12_SOURCE),
        yes_no_dk("Q13_UHC_LAW_AWARE", "13. Are you aware that UHC is a law?"),
        *select_all("Q14_UHC_UNDERSTAND", "14. What is your understanding about UHC?", Q14_UNDERSTANDING),
    ]
    # Q15-Q24: UHC9 items for various UHC benefits awareness
    uhc9_labels = [
        ("Q15_AUTO_PHILHEALTH", "15. Automatic PhilHealth coverage for all Filipinos"),
        ("Q16_FREE_CONSULT",    "16. Free primary care consultations"),
        ("Q17_FREE_LABS",       "17. Free laboratory and diagnostic services"),
        ("Q18_FREE_MEDS",       "18. Free medicines"),
        ("Q19_NBB",             "19. No Balance Billing (NBB) for inpatient services in government hospitals"),
        ("Q20_ZBB",             "20. Zero Balance Billing (ZBB) in DOH-retained hospitals"),
        ("Q21_REFERRAL",        "21. Referral system to connect patients to appropriate services"),
        ("Q22_KONSULTA",        "22. YAKAP/Konsulta primary care benefit package"),
        ("Q23_MEDS_ACCESS",     "23. Better access to essential medicines"),
        ("Q24_HCW_DEPLOYMENT",  "24. Increased deployment of healthcare workers to underserved areas"),
    ]
    for name, label in uhc9_labels:
        items.extend(uhc9_item(name, label))
    return record("C_UHC_AWARENESS", "C. UHC Awareness", "E", items)


# ============================================================
# Section D. PhilHealth Registration (Q25-Q40)
# ============================================================

def build_section_d():
    Q25_PHILHEALTH_STATUS = [
        ("Member (direct contributor)",  "1"),
        ("Dependent",                    "2"),
        ("Indigent / sponsored member",  "3"),
        ("Senior citizen",               "4"),
        ("Not a member",                 "5"),
        ("I don't know",                 "6"),
    ]
    Q26_MEMBER_TYPE = [
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
    Q28_DIFFICULTY_REASONS = [
        ("Unclear process",                              "1"),
        ("Took a long time",                             "2"),
        ("Did not know where to ask for help",           "3"),
        ("Had to travel a long way",                     "4"),
        ("No valid ID",                                  "5"),
        ("Did not know the required documents to register","6"),
        ("I don't know",                                  "7"),
        ("Other (specify)",                               "8"),
    ]
    Q30_PREMIUM_PAYMENT = [
        ("Yes, I pay directly",    "1"),
        ("Yes, my employer pays",  "2"),
        ("No, I do not pay premiums","3"),
    ]
    Q32_DIFFICULTY_PAYING = [
        ("Cannot afford the premium",                     "1"),
        ("Payment options are inconvenient",              "2"),
        ("No time to pay",                                "3"),
        ("Don't see value in paying",                     "4"),
        ("System of PhilHealth is unreliable/usually down","5"),
        ("I don't know",                                   "6"),
        ("Other (specify)",                                "7"),
    ]
    Q33_YAKAP_AWARE = [
        ("Yes",          "1"),
        ("No",           "2"),
        ("I don't know", "3"),
    ]
    Q35_KONSULTA_SOURCE = [
        ("News",                 "1"),
        ("Legislation",          "2"),
        ("Social Media",         "3"),
        ("Friends / Family",     "4"),
        ("Health center/facility","5"),
        ("PhilHealth",           "6"),
        ("LGU/Barangay",        "7"),
        ("BHW",                  "8"),
        ("I don't know",         "9"),
        ("Other (specify)",     "10"),
    ]
    items = [
        select_one("Q25_PHILHEALTH_STATUS", "25. What is your PhilHealth membership status?",
                   Q25_PHILHEALTH_STATUS, length=1),
        select_one("Q26_MEMBER_TYPE", "26. What type of PhilHealth member are you?",
                   Q26_MEMBER_TYPE, length=2),
        yes_no("Q27_REG_DIFFICULTY", "27. Did you have any difficulties in the registration process?"),
        *select_all("Q28_DIFFICULTY", "28. What did you find difficult about the process?", Q28_DIFFICULTY_REASONS),
        yes_no("Q29_KNOWS_ASSIST", "29. Would you know where to go to seek assistance in registration?"),
        select_one("Q30_PREMIUM_PAY", "30. Do you pay PhilHealth premiums every month?",
                   Q30_PREMIUM_PAYMENT, length=1),
        yes_no("Q31_PREMIUM_DIFFICULT", "31. Do you find it difficult to pay the PhilHealth premiums?"),
        *select_all("Q32_DIFF_PAYING", "32. Why did you find it difficult?", Q32_DIFFICULTY_PAYING),
        select_one("Q33_YAKAP_AWARE", "33. Have you heard about YAKAP/Konsulta?",
                   Q33_YAKAP_AWARE, length=1),
        yes_no("Q34_KONSULTA_ENROLLED", "34. Are you enrolled in a Konsulta provider?"),
        *select_all("Q35_KONSULTA_SOURCE", "35. What are your sources of information about Konsulta?",
                    Q35_KONSULTA_SOURCE),
        yes_no_dk("Q36_KONSULTA_USED", "36. Have you used any Konsulta services in the past 12 months?"),
        yes_no("Q37_KONSULTA_SATISFIED", "37. Were you satisfied with the Konsulta services?"),
        yes_no_dk("Q38_PRIVATE_INS", "38. Do you have private health insurance or HMO?"),
        alpha("Q39_PRIVATE_INS_NAME", "39. Name of private insurance/HMO provider", length=80),
        yes_no_dk("Q40_GSIS_SSS", "40. Are you a member of GSIS/SSS/Pag-IBIG?"),
    ]
    return record("D_PHILHEALTH_REG", "D. PhilHealth Registration", "F", items)


# ============================================================
# Section E. Primary Care Utilization (Q41-Q50)
# ============================================================

def build_section_e():
    Q42_FACILITY_TYPE = [
        ("YAKAP/Konsulta or primary care provider",         "01"),
        ("Barangay Health Center",                          "02"),
        ("Rural Health Unit / Health Center",                "03"),
        ("Public Hospital",                                 "04"),
        ("Private Hospital",                                "05"),
        ("Private Clinic",                                  "06"),
        ("Traditional Healer or Manghihilot/Albularyo",     "07"),
        ("I don't know",                                    "08"),
        ("Other (specify)",                                 "09"),
    ]
    Q43_WHY_NOT = [
        ("I don't get sick",              "1"),
        ("I recently moved into the area","2"),
        ("It's expensive",                "3"),
        ("I can treat myself",            "4"),
        ("I don't know where to go",      "5"),
        ("I don't know",                  "6"),
        ("Other (specify)",               "7"),
    ]
    Q44_TRANSPORT = [
        ("Walk",                                 "01"),
        ("Bike",                                 "02"),
        ("Public Bus",                           "03"),
        ("Jeepney",                              "04"),
        ("Tricycle",                             "05"),
        ("Car (including private taxi/cab)",      "06"),
        ("Motorcycle",                           "07"),
        ("Boat",                                 "08"),
        ("Taxi",                                 "09"),
        ("Pedicab",                              "10"),
        ("E-bike",                               "11"),
        ("Other (specify)",                      "12"),
    ]
    items = [
        yes_no_dk("Q41_HAS_USUAL_FACILITY",
                  "41. In the past 12 months, do you have a clinic or health center that you usually go to?"),
        alpha("Q41_FACILITY_NAME", "41a. What is the name of the facility?", length=120),
        select_one("Q42_FACILITY_TYPE", "42. What is the type of facility that you usually go to?",
                   Q42_FACILITY_TYPE, length=2),
        *select_all("Q43_WHY_NOT", "43. Why do you not have a usual clinic/health center?", Q43_WHY_NOT),
        *select_all("Q44_TRANSPORT", "44. What mode/s of transportation do you use when travelling to the nearest primary care facility?",
                    Q44_TRANSPORT),
        numeric("Q45_TRAVEL_TIME", "45. How long does it take you to travel to the nearest primary care facility? (minutes)",
                length=3),
        numeric("Q46_TRAVEL_COST", "46. How much does it cost to travel to this facility? (PHP, one-way)",
                length=5),
        yes_no("Q47_KNOWS_BOOKING", "47. Do you know how to book an appointment at a primary care facility?"),
        select_one("Q48_PHONE_ADVICE", "48. Can you get advice quickly over the phone when the facility is open?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4")], length=1),
        select_one("Q49_AFTER_HOURS", "49. Is there a phone number you can call when the facility is closed?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4")], length=1),
        select_one("Q50_LEAVE_WORK", "50. Do you have to take a leave from work or school to visit?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4"),("Not applicable","9")], length=1),
    ]
    return record("E_PRIMARY_CARE", "E. Primary Care Utilization", "G", items)


# ============================================================
# Section F. Health-Seeking Behavior (Q51-Q57)
# ============================================================

def build_section_f():
    Q51_WHY_VISIT = [
        ("This facility is more accessible than my usual facility", "01"),
        ("Needed a service/specialist not available at my usual facility", "02"),
        ("Recommended by friends/family", "03"),
        ("Wanted to try another facility than my usual", "04"),
        ("Prefer this facility than my usual", "05"),
        ("This was referred to me by my usual facility", "06"),
        ("Usual facility is closed for today", "07"),
        ("The doctor I trust transferred in this facility", "08"),
        ("Other (specify)", "09"),
    ]
    Q52_REASON_VISIT = [
        ("Consultation for new health problem",           "1"),
        ("Follow-up on ongoing health problem",           "2"),
        ("For tests/diagnostics only",                    "3"),
        ("For a general check-up",                        "4"),
        ("To get a health certificate/administrative reason","5"),
        ("For immunizations/vaccinations",                "6"),
        ("My doctor transferred to this facility",        "7"),
        ("Other (specify)",                               "8"),
    ]
    Q53_CARE_TYPE = [
        ("Outpatient care",            "1"),
        ("Inpatient care",             "2"),
        ("Emergency care",             "3"),
        ("Primary care consultation",  "4"),
        ("Other (specify)",            "5"),
    ]
    Q55_ACTIONS = [
        ("Visited other healthcare facility",   "1"),
        ("Sought alternative care",             "2"),
        ("Sought telemedicine",                 "3"),
        ("Used home care",                      "4"),
        ("Bought medicine from a pharmacy",     "5"),
        ("Did not seek other forms of care",    "6"),
        ("Other (specify)",                     "7"),
    ]
    items = [
        yes_no("Q51_USUAL_FACILITY", "51. Is this the facility you usually go to for general health concerns?"),
        *select_all("Q51A_WHY_DIFF", "51a. Why did you go to this facility?", Q51_WHY_VISIT),
        *select_all("Q52_REASON_VISIT", "52. What best describes why you will visit a health facility?", Q52_REASON_VISIT),
        *select_all("Q53_CARE_TYPE", "53. Have you accessed any of the following forms of care in the last 6 months?", Q53_CARE_TYPE),
        yes_no("Q54_PREVENTIVE", "54. Have you ever consulted a physician for preventative reasons?"),
        yes_no("Q55_FORGONE", "55. In the last 6 months, have you had a medical problem and chosen NOT to see a healthcare provider?"),
        *select_all("Q56_FORGONE_WHY", "56. Why not?", [
            ("Not sick enough","1"),("It's too expensive","2"),
            ("Could not take time off work","3"),("Could not get an appointment soon enough","4"),
            ("No transportation available","5"),("Afraid to know my illness","6"),
            ("I don't know","7"),("Other (specify)","8"),
        ]),
        *select_all("Q57_ACTIONS", "57. Did you do any other actions to improve your health?", Q55_ACTIONS),
    ]
    return record("F_HEALTH_SEEKING", "F. Health-Seeking Behavior", "H", items)


# ============================================================
# Section G. Outpatient Care (Q58-Q68)
# ============================================================

def build_section_g():
    Q58_SERVICES = [
        ("Consultation with a doctor",          "01"),
        ("Vaccination / immunization",          "02"),
        ("Dental care",                         "03"),
        ("Eye care / vision check",             "04"),
        ("Mental health consultation",          "05"),
        ("Prenatal / postnatal care",           "06"),
        ("Family planning",                     "07"),
        ("Laboratory / diagnostic test",        "08"),
        ("Physical therapy / rehabilitation",   "09"),
        ("Other (specify)",                     "10"),
    ]
    Q61_LABS = [
        ("Complete blood count (CBC)",   "01"),
        ("Urinalysis",                   "02"),
        ("Fecalysis / Stool exam",       "03"),
        ("Blood chemistry",              "04"),
        ("Lipid profile",                "05"),
        ("Blood sugar / glucose test",   "06"),
        ("Thyroid function test",        "07"),
        ("X-ray",                        "08"),
        ("Ultrasound",                   "09"),
        ("ECG / EKG",                    "10"),
        ("Drug test",                    "11"),
        ("Pap smear",                    "12"),
        ("Mammogram",                    "13"),
        ("CT Scan",                      "14"),
        ("MRI",                          "15"),
        ("COVID-19 test",                "16"),
        ("Other (specify)",              "17"),
    ]
    Q65_PAYMENT = [
        ("Own income / household income","01"),
        ("PhilHealth",                   "02"),
        ("Private insurance / HMO",      "03"),
        ("Loan",                         "04"),
        ("Sale of assets",               "05"),
        ("Donations from charities/NGOs","06"),
        ("Donations from LGUs",          "07"),
        ("National Gov't Agencies",      "08"),
        ("Paid by someone else",         "09"),
        ("Savings / pension",            "10"),
        ("Remittance",                   "11"),
        ("Borrowing from relatives",     "12"),
        ("Borrowing from institutions",  "13"),
        ("Government assistance",        "14"),
        ("Other (specify)",              "15"),
    ]
    items = [
        numeric("Q58_OUTPATIENT_VISITS", "58. How many outpatient visits in the last 6 months?", length=2),
        *select_all("Q59_SERVICES", "59. What services did you receive during your most recent outpatient visit?", Q58_SERVICES),
        yes_no("Q60_LABS", "60. Did you have any laboratory or diagnostic tests?"),
        *select_all("Q61_LAB_TYPES", "61. Which laboratory tests?", Q61_LABS),
        numeric("Q62_LAB_COST", "62. How much did you pay for lab tests? (PHP)", length=7),
        numeric("Q63_CONSULT_COST", "63. How much was the consultation fee? (PHP)", length=7),
        numeric("Q64_MEDS_COST", "64. How much did you spend on medicines? (PHP)", length=7),
        numeric("Q65_TOTAL_OOP", "65. Total out-of-pocket spending for outpatient visit (PHP)", length=8),
    ]
    # Payment sources: each has Yes/No + Amount
    for i, (label, code) in enumerate(Q65_PAYMENT):
        items.append(yes_no(f"Q66_PAY_O{i+1:02d}", f"66. Payment source: {label}"))
        items.append(numeric(f"Q66_PAY_O{i+1:02d}_AMT", f"66. Amount from {label} (PHP)", length=8))
    items.append(alpha("Q66_PAY_OTHER_TXT", "66. Payment source — Other (specify) text", length=120))
    items.extend([
        yes_no("Q67_PHILHEALTH_USED", "67. Did you use PhilHealth for this visit?"),
        yes_no("Q68_SATISFIED_OOP", "68. Were you satisfied with the amount you paid?"),
    ])
    return record("G_OUTPATIENT_CARE", "G. Outpatient Care", "I", items)


# ============================================================
# Section H. Inpatient Care (Q69-Q78)
# ============================================================

def build_section_h():
    Q69_REASON = [
        ("Illness / medical condition",    "1"),
        ("Surgery / procedure",            "2"),
        ("Childbirth / delivery",          "3"),
        ("Injury / accident",              "4"),
        ("Mental health",                  "5"),
        ("Other (specify)",                "6"),
    ]
    Q72_PAYMENT = [
        ("Own income / household income","01"),
        ("PhilHealth",                   "02"),
        ("Private insurance / HMO",      "03"),
        ("Loan",                         "04"),
        ("Sale of assets",               "05"),
        ("Donations from charities/NGOs","06"),
        ("Donations from LGUs",          "07"),
        ("National Gov't Agencies",      "08"),
        ("Paid by someone else",         "09"),
        ("Savings / pension",            "10"),
        ("Remittance",                   "11"),
        ("Borrowing from relatives",     "12"),
        ("Borrowing from institutions",  "13"),
        ("Other (specify)",              "14"),
    ]
    items = [
        numeric("Q69_INPATIENT_STAYS", "69. How many times were you admitted as an inpatient in the last 6 months?", length=2),
        *select_all("Q70_REASON", "70. What was the primary reason for the most recent admission?", Q69_REASON),
        numeric("Q71_NIGHTS", "71. How many nights were you admitted?", length=3),
        numeric("Q72_TOTAL_BILL", "72. Total hospital bill (PHP)", length=8),
        numeric("Q73_OOP", "73. Total out-of-pocket amount paid (PHP)", length=8),
    ]
    # Payment sources: each has Yes/No + Amount
    for i, (label, code) in enumerate(Q72_PAYMENT):
        items.append(yes_no(f"Q74_PAY_O{i+1:02d}", f"74. Payment source: {label}"))
        items.append(numeric(f"Q74_PAY_O{i+1:02d}_AMT", f"74. Amount from {label} (PHP)", length=8))
    items.append(alpha("Q74_PAY_OTHER_TXT", "74. Payment source — Other (specify) text", length=120))
    items.extend([
        yes_no("Q75_PHILHEALTH_USED", "75. Did you use PhilHealth for this admission?"),
        numeric("Q76_PHILHEALTH_COVERED", "76. How much did PhilHealth cover? (PHP)", length=8),
        yes_no("Q77_NBB_APPLIED", "77. Was No Balance Billing applied?"),
        yes_no("Q78_SATISFIED_OOP", "78. Were you satisfied with the amount you paid?"),
    ])
    return record("H_INPATIENT_CARE", "H. Inpatient Care", "J", items)


# ============================================================
# Section I. Financial Risk Protection (Q79-Q88)
# ============================================================

def build_section_i():
    Q79_INCOME_BRACKET = [
        ("Below PHP 10,957 (poor)",           "1"),
        ("PHP 10,957 - PHP 21,914 (low income)","2"),
        ("PHP 21,914 - PHP 43,828 (lower middle)","3"),
        ("PHP 43,828 - PHP 76,669 (middle)",    "4"),
        ("PHP 76,669 - PHP 131,484 (upper middle)","5"),
        ("PHP 131,484 - PHP 219,140 (upper income)","6"),
        ("Above PHP 219,140 (rich)",            "7"),
        ("Refused to answer",                   "8"),
        ("I don't know",                        "9"),
    ]
    items = [
        select_one("Q79_INCOME", "79. What is your estimated average monthly household income?",
                   Q79_INCOME_BRACKET, length=1),
        yes_no("Q80_DELAYED_CARE", "80. Have you delayed seeking care for financial reasons in the last 6 months?"),
        yes_no("Q81_REDUCED_SPEND", "81. Have you reduced spending on basic needs because of health expenditures?"),
        yes_no("Q82_BORROWED", "82. Have you borrowed money to pay for health expenses?"),
        yes_no("Q83_SOLD_ASSETS", "83. Have you sold assets to pay for health expenses?"),
        numeric("Q84_HEALTH_SPEND_PCT",
                "84. What percentage of household income was spent on health in the last 12 months?",
                length=3),
        yes_no("Q85_CATASTROPHIC", "85. Did health spending exceed 10% of household income?"),
        yes_no("Q86_IMPOVERISHED", "86. Did health spending push your household below the poverty line?"),
        yes_no("Q87_FORGONE_MEDS", "87. Have you foregone buying prescribed medicines for financial reasons?"),
        yes_no("Q88_FORGONE_FOLLOWUP", "88. Have you skipped follow-up visits for financial reasons?"),
    ]
    return record("I_FINANCIAL_RISK", "I. Financial Risk Protection", "K", items)


# ============================================================
# Section J. Patient Satisfaction (Q89-Q100)
# ============================================================

def build_section_j():
    FREQUENCY_4PT = [
        ("Always",    "1"),
        ("Usually",   "2"),
        ("Sometimes", "3"),
        ("Never",     "4"),
    ]
    items = [
        # Satisfaction items (5-point scale)
        select_one("Q89_SAT_WAIT_TIME", "89. Satisfaction with waiting time", SATISFACTION_5PT, length=1),
        select_one("Q90_SAT_CONSULT_TIME", "90. Satisfaction with consultation time", SATISFACTION_5PT, length=1),
        select_one("Q91_SAT_EXPLANATION", "91. Satisfaction with explanation of condition/treatment", SATISFACTION_5PT, length=1),
        select_one("Q92_SAT_RESPECT", "92. Satisfaction with how you were treated/respected", SATISFACTION_5PT, length=1),
        select_one("Q93_SAT_PRIVACY", "93. Satisfaction with privacy during consultation", SATISFACTION_5PT, length=1),
        select_one("Q94_SAT_CLEANLINESS", "94. Satisfaction with cleanliness of the facility", SATISFACTION_5PT, length=1),
        select_one("Q95_SAT_OVERALL", "95. Overall satisfaction with the health facility", SATISFACTION_5PT, length=1),
        # Frequency items (4-point scale)
        select_one("Q96_FREQ_LISTEN", "96. How often does the provider listen carefully?", FREQUENCY_4PT, length=1),
        select_one("Q97_FREQ_EXPLAIN", "97. How often does the provider explain things clearly?", FREQUENCY_4PT, length=1),
        select_one("Q98_FREQ_RESPECT", "98. How often does the provider show respect?", FREQUENCY_4PT, length=1),
        select_one("Q99_FREQ_TIME", "99. How often does the provider spend enough time?", FREQUENCY_4PT, length=1),
        select_one("Q100_RECOMMEND", "100. Would you recommend this facility to family/friends?",
                   [("Yes, definitely","1"),("Yes, probably","2"),("No","3"),("I don't know","4")], length=1),
    ]
    return record("J_SATISFACTION", "J. Patient Satisfaction", "L", items)


# ============================================================
# Section K. Access to Medicines (Q101-Q110)
# ============================================================

def build_section_k():
    Q101_WHERE = [
        ("Government health facility pharmacy",    "1"),
        ("Private pharmacy / drugstore",           "2"),
        ("Online pharmacy",                        "3"),
        ("Botika ng Barangay",                     "4"),
        ("Botika ng Bayan",                        "5"),
        ("Other (specify)",                        "6"),
    ]
    Q103_BARRIER = [
        ("Medicine not available",          "1"),
        ("Too expensive",                   "2"),
        ("Pharmacy too far",                "3"),
        ("Don't know where to buy",         "4"),
        ("No prescription",                 "5"),
        ("I don't know",                    "6"),
        ("Other (specify)",                 "7"),
    ]
    items = [
        yes_no("Q101_PRESCRIBED_MEDS", "101. Were you prescribed any medicines during your visit?"),
        *select_all("Q102_WHERE_BUY", "102. Where did you get your medicines?", Q101_WHERE),
        yes_no("Q103_ALL_OBTAINED", "103. Were you able to get all prescribed medicines?"),
        *select_all("Q104_BARRIER", "104. Why were you unable to get all prescribed medicines?", Q103_BARRIER),
        yes_no_dk("Q105_GENERIC_AWARE", "105. Are you aware of the Generics Act / generic medicines?"),
        yes_no("Q106_GENERIC_PREFER", "106. Do you prefer generic medicines?"),
        yes_no("Q107_GAMOT_AWARE", "107. Have you heard of GAMOT (DOH medicine access program)?"),
        yes_no("Q108_GAMOT_USED", "108. Have you used GAMOT?"),
        numeric("Q109_MEDS_OOP", "109. Total out-of-pocket spending on medicines in the last month (PHP)", length=7),
        yes_no("Q110_MEDS_SATISFIED", "110. Are you satisfied with your access to medicines?"),
    ]
    return record("K_ACCESS_MEDICINES", "K. Access to Medicines", "M", items)


# ============================================================
# Section L. Referrals (Q111-Q120)
# ============================================================

def build_section_l():
    Q112_TYPE = [
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
    Q113_REFERRAL_METHOD = [
        ("Physical referral slip",                        "1"),
        ("E-referral",                                    "2"),
        ("Phone call from referring to receiving facility","3"),
        ("I don't know",                                  "4"),
        ("Other (specify)",                               "5"),
    ]
    Q114_VISIT_STATUS = [
        ("Yes",                          "1"),
        ("No, I'm not planning to",      "2"),
        ("Not yet, but I'm planning to", "3"),
    ]
    Q115_WHY_NOT = [
        ("Facility is too far",              "1"),
        ("Do not trust the referred facility","2"),
        ("No time",                          "3"),
        ("Worried about additional costs",   "4"),
        ("Not needed",                       "5"),
        ("Don't know how to get to facility","6"),
        ("Other (specify)",                  "7"),
    ]
    items = [
        yes_no("Q111_REFERRED", "111. In the past 6 months, did a healthcare worker refer you to another facility?"),
        *select_all("Q112_TYPE", "112. What type of care was the referral for?", Q112_TYPE),
        select_one("Q113_METHOD", "113. How did they refer you?", Q113_REFERRAL_METHOD, length=1),
        select_one("Q114_VISITED", "114. Did you visit another facility after the referral?",
                   Q114_VISIT_STATUS, length=1),
        *select_all("Q115_WHY_NOT", "115. Why are you not planning to visit?", Q115_WHY_NOT),
        yes_no("Q116_DISCUSSED_OPTIONS", "116. Did they discuss different places you could go?"),
        yes_no("Q117_HELPED_APPT", "117. Did they help you make the appointment?"),
        yes_no("Q118_WROTE_INFO", "118. Did they write down information for the specialist?"),
        yes_no("Q119_FOLLOWUP", "119. Did they follow up with you about the visit?"),
        select_one("Q120_SAT_REFERRAL", "120. Overall satisfaction with the referral process",
                   SATISFACTION_5PT, length=1),
    ]
    return record("L_REFERRALS", "L. Referrals", "N", items)


# ============================================================
# ASSEMBLE THE DICTIONARY
# ============================================================

def build_f3_dictionary():
    records = [
        record("PATIENTSURVEY_REC", "PatientSurvey Record", "1", []),
        build_f3_field_control(),
        build_f3_geo_id(),
        build_section_a(),
        build_section_b(),
        build_section_c(),
        build_section_d(),
        build_section_e(),
        build_section_f(),
        build_section_g(),
        build_section_h(),
        build_section_i(),
        build_section_j(),
        build_section_k(),
        build_section_l(),
    ]
    return build_dictionary(
        dict_name="PATIENTSURVEY_DICT",
        dict_label="PatientSurvey",
        id_item_name="QUESTIONNAIRE_NO",
        id_item_label="Questionnaire No",
        id_length=6,
        records=records,
    )


def main():
    out_path = Path(__file__).parent / "PatientSurvey.dcf"
    write_dcf(build_f3_dictionary(), out_path)


if __name__ == "__main__":
    main()
