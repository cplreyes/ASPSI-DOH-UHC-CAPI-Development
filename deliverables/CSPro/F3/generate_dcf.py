"""
generate_dcf.py — F3 Patient Survey CSPro Data Dictionary generator.

Emits PatientSurvey.dcf in CSPro 8.0 JSON dictionary format from the
Apr 20 2026 Annex F3 questionnaire (Revised Inception Report submission,
178 numbered items across sections A–L; supersedes the Apr 08 baseline).

PSGC value sets are sourced from the PSA 1Q 2026 publication, parsed once
under F1/inputs/ and shared across F-series generators.

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
    _gps_fields, _photo_block,
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
# Section A. Introduction and Informed Consent (Q1-Q3) — Apr 20
# ============================================================

def build_section_a():
    Q1_OPTIONS = [
        ("Yes",  "1"),  # proceed to Q4
        ("No",   "2"),
    ]
    Q2_RELATIONSHIP = [
        ("Spouse",                                   "01"),
        ("Son",                                      "02"),
        ("Daughter",                                 "03"),
        ("Step-son",                                 "04"),
        ("Step-daughter",                            "05"),
        ("Son-in-law",                               "06"),
        ("Daughter-in-law",                          "07"),
        ("Grandson",                                 "08"),
        ("Granddaughter",                            "09"),
        ("Father",                                   "10"),
        ("Mother",                                   "11"),
        ("Brother",                                  "12"),
        ("Sister",                                   "13"),
        ("Uncle",                                    "14"),
        ("Aunt",                                     "15"),
        ("Nephew",                                   "16"),
        ("Niece",                                    "17"),
        ("Neighbor",                                 "18"),
        ("Other (specify)",                          "19"),
        ("Refuse to answer (DO NOT READ OUT LOUD)",  "20"),
    ]
    items = [
        select_one("Q1_IS_PATIENT",
                   "1. Before we begin, to confirm, are you the patient?",
                   Q1_OPTIONS, length=1),
        select_one("Q2_RELATIONSHIP",
                   "2. What is your relationship to the patient?",
                   Q2_RELATIONSHIP, length=2),
        alpha("Q2_RELATIONSHIP_OTHER_TXT",
              "2. Relationship — Other (specify) text", length=120),
        yes_no("Q3_SAME_HOUSE",
               "3. Do you live in the same house as the patient?"),
    ]
    return record("A_INFORMED_CONSENT",
                  "A. Introduction and Informed Consent", "C", items)


# ============================================================
# Section B. Patient Profile (Q4-Q34) — Apr 20
# ============================================================

def build_section_b():
    Q7_SEX = [
        ("Male",   "1"),
        ("Female", "2"),
    ]
    Q8_LGBTQIA = [
        ("Yes",                        "1"),
        ("No",                         "2"),
        ("Not Comfortable to Answer",  "3"),
        ("Don't Know",                 "4"),
        ("Refused to answer",          "5"),
    ]
    Q9_GROUP = [
        ("Lesbian",          "1"),
        ("Gay",              "2"),
        ("Bisexual",         "3"),
        ("Transgender",      "4"),
        ("Queer",            "5"),
        ("Intersex",         "6"),
        ("Asexual",          "7"),
        ("Other (specify)",  "8"),
    ]
    Q10_CIVIL_STATUS = [
        ("Single / Never Married",   "1"),
        ("Married",                  "2"),
        ("Common law / Live-in",     "3"),
        ("Widowed",                  "4"),
        ("Divorced",                 "5"),
        ("Separated",                "6"),
        ("Annulled",                 "7"),
        ("Not reported",             "8"),
    ]
    Q13_PWD_CARD = [
        ("Yes (card was presented and verified)",        "1"),
        ("No (card not available at the time of interview)", "2"),
        ("Respondent refused to present card",           "3"),
    ]
    Q14_DISABILITY_TYPE = [
        ("Physical disability (Orthopedic)", "1"),
        ("Visual disability",                "2"),
        ("Hearing disability",               "3"),
        ("Speech impairment",                "4"),
        ("Intellectual disability",          "5"),
        ("Psychosocial disability",          "6"),
        ("Multiple disabilities",            "7"),
        ("Other disability (specify)",       "8"),
    ]
    Q15_EDUCATION = [
        ("Early Childhood Education (Pre-school)",                                          "01"),
        ("Primary Education (Grade 1 to 6)",                                                "02"),
        ("Lower Secondary Education (Grade 7 to 10)",                                       "03"),
        ("Upper Secondary Education (Grade 11 to 12)",                                      "04"),
        ("Post-Secondary Non-Tertiary Education (including Technical and Vocational degrees with a certificate)",      "05"),
        ("Short-Cycle Tertiary Education or Equivalent (including Technical and Vocational degrees with a diploma)",   "06"),
        ("Bachelor Level Education or Equivalent",                                          "07"),
        ("Master Level Education or Equivalent",                                            "08"),
        ("Doctoral Level Education or Equivalent",                                          "09"),
        ("No schooling",                                                                    "10"),
        ("Other (specify)",                                                                 "11"),
        ("I don't know",                                                                    "98"),
        ("Not applicable",                                                                  "99"),
    ]
    Q16_EMPLOYMENT = [
        ("Has a permanent job/ own business",                  "1"),
        ("Has a short-term, seasonal, casual job/business",    "2"),
        ("Worked on different jobs day to day per week",       "3"),
        ("Unemployed and looking for work",                    "4"),
        ("Unemployed and not looking for work",                "5"),
        ("Studying",                                           "6"),
        ("Retired",                                            "7"),
        ("I don't know",                                       "8"),
        ("Not applicable",                                     "9"),
    ]
    Q17_INCOME_SOURCE = [
        ("Working for private company",                        "01"),
        ("Working for private household",                      "02"),
        ("Working for government",                             "03"),
        ("Worked with pay in own family business or farm",     "04"),
        ("Self-employed without any paid employee",            "05"),
        ("Worked without pay in own family business or farm",  "06"),
        ("Pension",                                            "07"),
        ("Unemployed and looking for work",                    "08"),
        ("Unemployed and not looking for work",                "09"),
        ("I don't know",                                       "99"),
    ]
    Q18_BRACKET = [
        ("Under 40,000",      "1"),
        ("40,000 - 59,999",   "2"),
        ("60,000 - 99,999",   "3"),
        ("100,000 - 249,999", "4"),
        ("250,000 - 499,999", "5"),
        ("500,000 and over",  "6"),
    ]
    Q23_WATER = [
        ("Faucet inside the house", "1"),
        ("Tubed/piped well",        "2"),
        ("Dug well",                "3"),
        ("Other (specify)",         "4"),
    ]
    Q24_OWN_SHARE = [
        ("I/we have our own",            "1"),
        ("I/we share with our community","2"),
    ]
    Q26_HAVE = [
        ("Yes, I/ we have",     "1"),
        ("No, I/we don't have", "2"),
    ]
    Q29_SEC = [
        ("Class A or B (working professionals or with a business with several assets)",       "1"),
        ("Class C (working professionals with permanent or semi-permanent income and some assets)", "2"),
        ("Class D or E (semi-permanent workers or informal sector workers with little to no assets)", "3"),
        ("I don't know",                                                                       "4"),
    ]
    Q30_IP = [
        ("Yes", "1"),
        ("No",  "2"),  # proceed to Q32
    ]
    Q33_DECISION = [
        ("Yes (the Patient is the main decision maker)",                          "1"),  # proceed to Q35
        ("No",                                                                    "2"),
        ("The Companion answering the survey is the main decision maker",         "3"),  # proceed to Q35
    ]
    Q34_WHO_DECIDES = [
        ("Patient's father",          "01"),
        ("Patient's mother",          "02"),
        ("Patient's parents",         "03"),
        ("Patient's spouse/partner",  "04"),
        ("Both patient and spouse",   "05"),
        ("Patient's sibling",         "06"),
        ("Patient's grandfather",     "07"),
        ("Patient's grandmother",     "08"),
        ("Patient's uncle",           "09"),
        ("Patient's aunt",            "10"),
        ("Other (specify)",           "11"),
    ]
    items = [
        alpha("Q4_NAME",
              "4. Patient's Name (Last Name, First Name, MI, Extension)", length=120),
        numeric("Q5_BIRTH_MONTH",
                "5. In what month and year was the patient born? — Month", length=2),
        numeric("Q5_BIRTH_YEAR",
                "5. In what month and year was the patient born? — Year", length=4),
        numeric("Q6_AGE",
                "6. Just to confirm, how old is the patient as of his/her last birthday? (in years)",
                length=3),
        select_one("Q7_SEX",
                   "7. What is the patient's sex at birth?", Q7_SEX, length=1),
        select_one("Q8_LGBTQIA",
                   "8. Is the patient part of the LGBTQIA+ community? (e.g., gay, lesbian, bisexual, etc.).",
                   Q8_LGBTQIA, length=1),
        select_one("Q9_GROUP",
                   "9. Which group does the patient identify with?", Q9_GROUP, length=1),
        alpha("Q9_GROUP_OTHER_TXT",
              "9. Group identity — Other (specify) text", length=120),
        select_one("Q10_CIVIL_STATUS",
                   "10. What is the patient's civil status?", Q10_CIVIL_STATUS, length=1),
        yes_no("Q11_PWD",
               "11. Does the patient identify as a person with a disability?"),
        yes_no("Q12_PWD_SPECIFY",
               "12. Would the patient like to specify the type of disability?"),
        select_one("Q13_PWD_CARD",
                   "13. May we view the patient's PWD Identification Card?",
                   Q13_PWD_CARD, length=1),
        select_one("Q14_DISABILITY_TYPE",
                   "14. Based on the presented PWD Identification Card, what type of disability is indicated?",
                   Q14_DISABILITY_TYPE, length=1),
        alpha("Q14_DISABILITY_OTHER_TXT",
              "14. Disability — Other (specify) text", length=120),
        select_one("Q15_EDUCATION",
                   "15. What is the highest level of education the patient has attained?",
                   Q15_EDUCATION, length=2),
        alpha("Q15_EDUCATION_OTHER_TXT",
              "15. Education — Other (specify) text", length=120),
        select_one("Q16_EMPLOYMENT",
                   "16. What is the patient's employment status?", Q16_EMPLOYMENT, length=1),
        select_one("Q17_INCOME_SOURCE",
                   "17. What is the patient's main source of income?",
                   Q17_INCOME_SOURCE, length=2),
        numeric("Q18_INCOME_AMOUNT",
                "18. In the past 6 months, what is the patient's average monthly household income? "
                "Please specify in Philippine pesos. — Approximate amount",
                length=8),
        select_one("Q18_INCOME_BRACKET",
                   "18. Income category corresponding to the respondent's approximate household income",
                   Q18_BRACKET, length=1),
        numeric("Q19_HH_SIZE",
                "19. How many total individuals (including children) live in the patient's house now?",
                length=2),
        numeric("Q20_HH_CHILDREN",
                "20. How many non-working age children (i.e., below the age of 18) live in the patient's house now?",
                length=2),
        numeric("Q21_HH_SENIORS",
                "21. How many senior citizens live in the patient's house now?", length=2),
        yes_no("Q22_ELECTRICITY",
               "22. Does the patient have electricity in their household?"),
        select_one("Q23_WATER",
                   "23. What is the patient's family's main source of water supply for daily use?",
                   Q23_WATER, length=1),
        alpha("Q23_WATER_OTHER_TXT",
              "23. Water — Other (specify) text", length=120),
        select_one("Q24_FAUCET_OWN",
                   "24. Does the patient have their own faucet, or do they share with their community?",
                   Q24_OWN_SHARE, length=1),
        select_one("Q25_TUBE_OWN",
                   "25. Does the patient have their own tube/pipe, or do they share with their community?",
                   Q24_OWN_SHARE, length=1),
        select_one("Q26_REFRIGERATOR",
                   "26. Does the patient's family own a refrigerator/freezer?", Q26_HAVE, length=1),
        select_one("Q27_TELEVISION",
                   "27. Does the patient's family own a television set?", Q26_HAVE, length=1),
        select_one("Q28_WASHER",
                   "28. Does the patient's family own a washing machine?", Q26_HAVE, length=1),
        select_one("Q29_SEC_CLASS",
                   "29. How would the socioeconomic class of the patient's household be classified?",
                   Q29_SEC, length=1),
        select_one("Q30_IP",
                   "30. Is the patient member of Indigenous People (IP) community, "
                   "like the Igorot, Lumad, Mangyans, etc.?",
                   Q30_IP, length=1),
        alpha("Q31_IP_GROUP",
              "31. If yes, which group? (Specify)", length=120),
        yes_no("Q32_4PS",
               "32. Is the patient's household a beneficiary of the Pantawid Pamilyang Pilipino Program (4Ps)?"),
        select_one("Q33_DECISION_MAKER",
                   "33. Is the patient the main decision-maker on health care in your household?",
                   Q33_DECISION, length=1),
        select_one("Q34_WHO_DECIDES",
                   "34. Who takes the most responsibility for making the decisions regarding healthcare "
                   "in the patient's household?",
                   Q34_WHO_DECIDES, length=2),
        alpha("Q34_WHO_DECIDES_OTHER_TXT",
              "34. Decision maker — Other (specify) text", length=120),
    ]
    return record("B_PATIENT_PROFILE", "B. Patient Profile", "D", items)


# ============================================================
# Section C. Awareness on Universal Health Care (UHC) (Q35-Q37) — Apr 20
# ============================================================

def build_section_c():
    Q35_OPTIONS = [
        ("Yes", "1"),
        ("No",  "2"),  # proceed to Q38
    ]
    Q36_SOURCE = [
        ("News",                   "1"),
        ("Legislation",            "2"),
        ("Social Media",           "3"),
        ("Friends / Family",       "4"),
        ("Health center/ facility","5"),
        ("LGU/ Barangay",          "6"),
        ("I don't know",           "7"),
        ("Other (Specify)",        "8"),
    ]
    Q37_UNDERSTANDING = [
        ("Protection from financial risk/decreased out-of-pocket spending", "1"),
        ("Access to quality and affordable health care goods and services", "2"),
        ("Automatic enrollment into PhilHealth",                            "3"),
        ("Primary care provider for every Filipino",                        "4"),
        ("I don't know",                                                    "5"),
        ("Other (Specify)",                                                 "6"),
    ]
    items = [
        select_one("Q35_UHC_HEARD",
                   "35. Have you heard about Universal Health Care (UHC) prior to this survey?",
                   Q35_OPTIONS, length=1),
        *select_all("Q36_UHC_SOURCE",
                    "36. What is your source of information about UHC?", Q36_SOURCE),
        alpha("Q36_UHC_SOURCE_OTHER_TXT",
              "36. UHC source — Other (specify) text", length=120),
        *select_all("Q37_UHC_UNDERSTAND",
                    "37. What is your understanding about UHC?", Q37_UNDERSTANDING),
        alpha("Q37_UHC_UNDERSTAND_OTHER_TXT",
              "37. UHC understanding — Other (specify) text", length=120),
    ]
    return record("C_UHC_AWARENESS",
                  "C. Awareness on Universal Health Care (UHC)", "E", items)


# ============================================================
# Section D. PhilHealth Registration and Health Insurance (Q38-Q52) — Apr 20
# ============================================================

def build_section_d():
    Q38_REGISTERED = [
        ("Yes",          "1"),
        ("No",           "2"),  # proceed to Q43
        ("I don't know", "3"),  # proceed to Q43
    ]
    REG_ACTOR = [
        ("PhilHealth representative",    "01"),
        ("LGU",                          "02"),
        ("Primary care provider",        "03"),
        ("Other health care provider",   "04"),
        ("Employer",                     "05"),
        ("No one / self-registered",     "06"),
        ("Barangay Health Worker",       "07"),
        ("Friends / Family",             "08"),
        ("Health center/facility",       "09"),
        ("Other (Specify)",              "10"),
    ]
    Q42_DIFFICULTY = [
        ("Unclear process",                                 "1"),
        ("Took a long time",                                "2"),
        ("Did not know where to ask for help",              "3"),
        ("Had to travel a long way",                        "4"),
        ("No valid ID",                                     "5"),
        ("Did not know the required documents to register", "6"),
        ("I don't know",                                    "7"),
        ("Other (Specify)",                                 "8"),
    ]
    Q45_CATEGORY = [
        ("Formal economy (i.e., individuals working in the government or private sector "
         "based in the country)", "01"),
        ("Informal economy (i.e., unemployed, self-employed, informal workers, Filipinos "
         "with dual citizenship, naturalized Filipino citizens, citizens of other countries "
         "working and/or residing in the Philippines)", "02"),
        ("Indigent (i.e., individuals who have no visible means of income, or whose income "
         "is insufficient for family subsistence based on DSWD's specific criteria)", "03"),
        ("Sponsored (i.e., members whose contributions are being paid for by another "
         "individual, government agencies, or private entities. Includes some low-income "
         "citizens that are not indigent e.g. BHWs, PWDs)", "04"),
        ("Lifetime member (i.e., individuals aged 60 years and above, uniformed personnel "
         "aged 56 years and above, and SSS underground miner-retirees aged 55 years and "
         "above and paid at least 120 monthly contributions with PhilHealth and the former "
         "Medicare Programs of SSS and GSIS)", "05"),
        ("Senior citizen (i.e., residents of the Philippines, aged sixty (60) years or above "
         "and are not currently covered by any membership category of PhilHealth and "
         "qualified dependents of senior citizen members who are also senior citizen "
         "themselves or belonging to other membership categories, with or without coverage "
         "who are senior citizens themselves)", "06"),
        ("Overseas Filipino Worker (OFW)", "07"),
        ("Qualified dependents (i.e., those whose contributions are declared and covered by "
         "a principal member)", "08"),
        ("I don't know",   "98"),
        ("Other (Specify)", "99"),
    ]
    Q46_BENEFITS = [
        ("No balance billing for basic ward accommodation", "1"),
        ("Subsidized inpatient services",                   "2"),
        ("Subsidized outpatient services",                  "3"),
        ("There are no benefits to being a member",         "4"),
        ("I don't know",                                    "5"),
        ("Other (Specify)",                                 "6"),
    ]
    Q48_PAY = [
        ("Yes, I pay directly",             "1"),
        ("Yes, my employer pays",           "2"),
        ("No, I do not pay premiums",       "3"),  # proceed to Q51
    ]
    Q50_DIFFICULTY_PAYING = [
        ("Cannot afford the premium",                        "1"),
        ("Payment options are inconvenient",                 "2"),
        ("No time to pay",                                   "3"),
        ("Don't see value in paying",                        "4"),
        ("System of PhilHealth is unreliable/usually down",  "5"),
        ("I don't know",                                     "6"),
        ("Other (Specify)",                                  "7"),
    ]
    Q52_PLANS = [
        ("GSIS",               "1"),
        ("SSS",                "2"),
        ("Private Insurance",  "3"),
        ("HMO",                "4"),
        ("Pag-ibig",           "5"),
        ("I don't know",       "6"),
        ("Others (specify)",   "7"),
    ]
    Q47_PACKAGES = [
        ("Q47_PHYSICIAN_CHECKUP", "47. Awareness of PhilHealth package — Physician check-up"),
        ("Q47_DIAGNOSTIC_TESTS",  "47. Awareness of PhilHealth package — Diagnostic tests (e.g. laboratory tests and imaging)"),
        ("Q47_HOSPITAL_CONF",     "47. Awareness of PhilHealth package — Hospital confinement"),
        ("Q47_OUTPATIENT_DRUGS",  "47. Awareness of PhilHealth package — Outpatient drugs"),
    ]
    items = [
        select_one("Q38_PHILHEALTH_REG",
                   "38. Are you currently registered with PhilHealth?",
                   Q38_REGISTERED, length=1),
        select_one("Q39_HOW_FIND_OUT",
                   "39. How did you find out about how to register for PhilHealth?",
                   REG_ACTOR, length=2),
        alpha("Q39_HOW_FIND_OUT_OTHER_TXT",
              "39. How found out — Other (specify) text", length=120),
        select_one("Q40_WHO_ASSISTED",
                   "40. Who assisted you in the registration process?",
                   REG_ACTOR, length=2),
        alpha("Q40_WHO_ASSISTED_OTHER_TXT",
              "40. Who assisted — Other (specify) text", length=120),
        yes_no("Q41_REG_DIFFICULTY",
               "41. Did you have any difficulties in the registration process?"),
        *select_all("Q42_DIFFICULTY",
                    "42. What did you find difficult about the process?", Q42_DIFFICULTY),
        alpha("Q42_DIFFICULTY_OTHER_TXT",
              "42. Difficulty — Other (specify) text", length=120),
        yes_no("Q43_KNOWS_ASSIST",
               "43. Would you know where to go to seek assistance during registration?"),
        select_one("Q44_WHERE_ASSIST",
                   "44. Where would you go to seek assistance?",
                   REG_ACTOR, length=2),
        alpha("Q44_WHERE_ASSIST_OTHER_TXT",
              "44. Where to seek assistance — Other (specify) text", length=120),
        select_one("Q45_CATEGORY",
                   "45. What category of member are you?",
                   Q45_CATEGORY, length=2),
        alpha("Q45_CATEGORY_OTHER_TXT",
              "45. Category — Other (specify) text", length=120),
        *select_all("Q46_BENEFITS",
                    "46. What are some of the benefits that come with being a PhilHealth member?",
                    Q46_BENEFITS),
        alpha("Q46_BENEFITS_OTHER_TXT",
              "46. Benefits — Other (specify) text", length=120),
    ]
    for name, label in Q47_PACKAGES:
        items.append(yes_no(name, label))
    items.extend([
        select_one("Q48_PREMIUM_PAY",
                   "48. Do you pay PhilHealth premiums every month?", Q48_PAY, length=1),
        yes_no("Q49_PREMIUM_DIFFICULT",
               "49. Do you find it difficult to pay your PhilHealth premium every month?"),
        *select_all("Q50_DIFFICULTY_PAYING",
                    "50. Why did you find it difficult?", Q50_DIFFICULTY_PAYING),
        alpha("Q50_DIFFICULTY_PAYING_OTHER_TXT",
              "50. Difficulty paying — Other (specify) text", length=120),
        yes_no("Q51_OTHER_INSURANCE",
               "51. Are you registered with another health insurance plan?"),
        *select_all("Q52_PLANS",
                    "52. Which health insurance plan/s are you enrolled in?", Q52_PLANS),
        alpha("Q52_PLANS_OTHER_TXT",
              "52. Insurance plans — Others (specify) text", length=120),
    ])
    return record("D_PHILHEALTH_REG",
                  "D. PhilHealth Registration and Health Insurance", "F", items)


# ============================================================
# Section E. Primary Care Utilization (Q53-Q82) — Apr 20
# ============================================================

def build_section_e():
    Q54_PROVIDER = [
        ("General practitioner",                    "1"),
        ("Specialty Care Provider/ Specialist",     "2"),
        ("Both",                                    "3"),
        ("Other (specify)",                         "4"),
        ("None",                                    "5"),
    ]
    COMM_MODES = [
        ("Face-to-face",      "1"),
        ("Teleconsultation",  "2"),
        ("Landline",          "3"),
        ("Cellphone",         "4"),
        ("Video Conference",  "5"),
    ]
    Q65_WHY_NOT = [
        ("I don't get sick",                   "1"),
        ("I recently moved into the area",     "2"),
        ("It's expensive",                     "3"),
        ("I can treat myself",                 "4"),
        ("I don't know where to go for care",  "5"),
        ("I don't know",                       "6"),
        ("Other (Specify)",                    "7"),
    ]
    Q67_WHY_THIS = [
        ("This facility is more accessible than my usual facility (i.e., nearer, has more "
         "transportation options to get to, and cheaper to travel to)", "1"),
        ("Needed a service/specialist not available at my usual facility",             "2"),
        ("Recommended by friends/family",                                              "3"),
        ("Wanted to try another facility than my usual",                               "4"),
        ("Prefer this facility than my usual",                                         "5"),
        ("This was referred to me by my usual facility",                               "6"),
        ("Usual facility is closed for today",                                         "7"),
        ("Other (Specify)",                                                            "8"),
    ]
    Q68_FACILITY_TYPE = [
        ("YAKAP/Konsulta or primary care provider",              "1"),
        ("Barangay Health Center/ Barangay Health Station",      "2"),
        ("Rural Health Unit / Urban Health Center",              "3"),
        ("Public Hospital",                                      "4"),
        ("Private Hospital",                                     "5"),
        ("Private Clinic",                                       "6"),
        ("Traditional Healer or Manghihilot/ Albularyo",         "7"),
        ("I don't know",                                         "8"),
        ("Other (specify)",                                      "9"),
    ]
    Q71_NEAREST_TYPE = [
        ("Barangay Health Center/ Barangay Health Station",      "1"),
        ("Rural Health Unit / Urban Health Center",              "2"),
        ("Public Hospital",                                      "3"),
        ("Private Hospital",                                     "4"),
        ("Private Clinic",                                       "5"),
        ("Traditional Healer or Manghihilot/ Albularyo",         "6"),
        ("I don't know",                                         "7"),
        ("Other (specify)",                                      "8"),
    ]
    TRANSPORT = [
        ("Walk",                                   "01"),
        ("Bike",                                   "02"),
        ("Public Bus",                             "03"),
        ("Jeepney",                                "04"),
        ("Tricycle",                               "05"),
        ("Car (including private taxi/cab)",       "06"),
        ("Motorcycle",                             "07"),
        ("Boat",                                   "08"),
        ("Taxi",                                   "09"),
        ("Pedicab",                                "10"),
        ("E-bike",                                 "11"),
        ("Other (Specify)",                        "12"),
    ]
    Q75_KON_SOURCE = [
        ("News",                     "1"),
        ("Legislation",              "2"),
        ("Social Media",             "3"),
        ("Friends / Family",         "4"),
        ("Health center/facility",   "5"),
        ("LGU/Barangay",             "6"),
        ("I don't know",             "7"),
        ("Other (Specify)",          "8"),
    ]
    Q76_KON_UNDERSTAND = [
        ("Free primary care consultation (with a registered YAKAP/Konsulta provider)",         "1"),
        ("Free health risk screening and assessment (with a registered YAKAP/Konsulta provider)", "2"),
        ("Free selected laboratory / diagnostics examination",                                  "3"),
        ("Free selected drugs and medicines",                                                   "4"),
        ("There are no benefits of the package",                                                "5"),
        ("I don't know",                                                                        "6"),
        ("Other (Specify)",                                                                     "7"),
    ]
    Q77_KON_REGISTERED = [
        ("Yes",                         "1"),
        ("No",                          "2"),  # proceed to Q82
        ("I've never heard of it",      "3"),  # proceed to Q83
        ("I don't know",                "4"),  # proceed to Q83
    ]
    Q78_WHEN_REG = [
        ("Within the past six (6) months",                              "1"),
        ("More than six (6) months but less than one (1) year ago",     "2"),
        ("One (1) year but less than two (2) years ago",                "3"),
        ("Two (2) years ago or more",                                   "4"),
    ]
    Q82_WHY_NOT_REG = [
        ("Don't know what a YAKAP/Konsulta provider is",                          "01"),
        ("Don't trust PhilHealth",                                                "02"),
        ("Don't know how to register",                                            "03"),
        ("Registration is confusing/time-consuming/inconvenient",                 "04"),
        ("Intend to register but do not have found a time to do it.",             "05"),
        ("YAKAP/Konsulta is not available in my local area",                      "06"),
        ("Already have a usual primary care provider that I go to",               "07"),
        ("Don't have the required PhilHealth ID to register for YAKAP/Konsulta",  "08"),
        ("Don't have the other requirements to register",                         "09"),
        ("I don't know",                                                          "10"),
        ("Other (specify)",                                                       "11"),
    ]
    items = [
        yes_no("Q53_HAS_PCP",
               "53. Do you have a primary care provider?"),
        select_one("Q54_PCP_TYPE",
                   "54. Who is your main primary care provider?", Q54_PROVIDER, length=1),
        alpha("Q54_PCP_TYPE_OTHER_TXT",
              "54. Primary care provider — Other (specify) text", length=120),
        yes_no("Q55_LOC_CONVENIENT",
               "55. Is the location of your main primary care provider convenient for you?"),
        yes_no("Q56_HOURS_CONVENIENT",
               "56. Is your main primary care provider's clinic hours (time that your provider/s is/are "
               "open for medical appointments) convenient for you?"),
        yes_no("Q57_WAIT_CONVENIENT",
               "57. Is the usual wait for setting an appointment with your main primary care provider "
               "convenient for you?"),
        numeric("Q58_WAIT_DAYS",
                "58. Wait time to set appointment with main primary care provider — Days", length=3),
        numeric("Q58_WAIT_MINUTES",
                "58. Wait time to set appointment with main primary care provider — Minutes", length=4),
        *select_all("Q59_SCHED_COMM",
                    "59. What mode/s of communication was/were available to you when scheduling a "
                    "consultation with your main primary care provider?", COMM_MODES),
        yes_no("Q60_SCHED_TELECON_OK",
               "60. If teleconsultation was available, did you succeed in using the teleconsult? (scheduling)"),
        *select_all("Q61_CONSULT_COMM",
                    "61. What mode/s of communication was/were available to you when consulting with "
                    "your main primary care provider?", COMM_MODES),
        yes_no("Q62_CONSULT_TELECON_OK",
               "62. If teleconsultation was available, did you succeed in using the teleconsult? (consultation)"),
        yes_no("Q63_HAS_USUAL_FACILITY",
               "63. In the past 12 months, do you have a clinic, or health center that you usually go to?"),
        alpha("Q64_FACILITY_NAME",
              "64. What is the name of the facility?", length=120),
        *select_all("Q65_WHY_NO_USUAL",
                    "65. If none, why do you not have a usual clinic, or health center that you usually go to?",
                    Q65_WHY_NOT),
        alpha("Q65_WHY_NO_USUAL_OTHER_TXT",
              "65. Why no usual facility — Other (specify) text", length=120),
        yes_no("Q66_SAME_AS_USUAL",
               "66. Is [facility_name_input] the facility you usually go to for general health concerns?"),
        *select_all("Q67_WHY_THIS_FACILITY",
                    "67. Why did you go to this facility instead of your usual facility?", Q67_WHY_THIS),
        alpha("Q67_WHY_THIS_OTHER_TXT",
              "67. Why this facility — Other (specify) text", length=120),
        select_one("Q68_USUAL_FAC_TYPE",
                   "68. What is the type of health facility that you usually go to?",
                   Q68_FACILITY_TYPE, length=1),
        alpha("Q68_USUAL_FAC_TYPE_OTHER_TXT",
              "68. Usual facility type — Other (specify) text", length=120),
        numeric("Q69_USUAL_TRAVEL_HH",
                "69. How long does it take you to travel to the health facility you usually go to — Hours",
                length=2),
        numeric("Q69_USUAL_TRAVEL_MM",
                "69. How long does it take you to travel to the health facility you usually go to — Minutes",
                length=2),
        *select_all("Q70_USUAL_TRANSPORT",
                    "70. What mode/s of transportation do you use when travelling to the health facility "
                    "that you usually go to?", TRANSPORT),
        alpha("Q70_USUAL_TRANSPORT_OTHER_TXT",
              "70. Transport to usual facility — Other (specify) text", length=120),
        select_one("Q71_NEAREST_TYPE",
                   "71. What is the type of the primary care facility nearest to your house?",
                   Q71_NEAREST_TYPE, length=1),
        alpha("Q71_NEAREST_TYPE_OTHER_TXT",
              "71. Nearest primary care facility type — Other (specify) text", length=120),
        numeric("Q72_NEAREST_TRAVEL_HH",
                "72. How long does it take you to travel from your house when going to the nearest "
                "primary care facility? — Hours", length=2),
        numeric("Q72_NEAREST_TRAVEL_MM",
                "72. How long does it take you to travel from your house when going to the nearest "
                "primary care facility? — Minutes", length=2),
        *select_all("Q73_NEAREST_TRANSPORT",
                    "73. What mode/s of transportation do you use when travelling to the nearest "
                    "primary care facility?", TRANSPORT),
        alpha("Q73_NEAREST_TRANSPORT_OTHER_TXT",
              "73. Transport to nearest primary care — Other (specify) text", length=120),
        yes_no("Q74_KON_HEARD",
               "74. Have you heard of the term \"YAKAP/ Konsulta package\"?"),
        *select_all("Q75_KON_SOURCE",
                    "75. What are your sources of information about the YAKAP/Konsulta package?",
                    Q75_KON_SOURCE),
        alpha("Q75_KON_SOURCE_OTHER_TXT",
              "75. YAKAP/Konsulta source — Other (specify) text", length=120),
        *select_all("Q76_KON_UNDERSTAND",
                    "76. What is your understanding about the YAKAP/Konsulta package?",
                    Q76_KON_UNDERSTAND),
        alpha("Q76_KON_UNDERSTAND_OTHER_TXT",
              "76. YAKAP/Konsulta understanding — Other (specify) text", length=120),
        select_one("Q77_KON_REGISTERED",
                   "77. Are you registered with a YAKAP/Konsulta package provider?",
                   Q77_KON_REGISTERED, length=1),
        select_one("Q78_KON_WHEN_REG",
                   "78. When did you register with a YAKAP/Konsulta package provider?",
                   Q78_WHEN_REG, length=1),
        yes_no("Q79_KON_HAD_APPT",
               "79. Since registering, have you had an appointment with your YAKAP/Konsulta package provider?"),
        yes_no("Q80_KON_KNOWS_BOOKING",
               "80. When you have a health problem, do you know how to book an appointment at your "
               "YAKAP/Konsulta package provider?"),
        yes_no("Q81_KON_APPT_CHECKUP",
               "81. Was that appointment for a general check-up (i.e. not related to an illness or injury)?"),
        *select_all("Q82_KON_WHY_NOT_REG",
                    "82. Why are you NOT registered with a YAKAP/Konsulta package provider?",
                    Q82_WHY_NOT_REG),
        alpha("Q82_KON_WHY_NOT_REG_OTHER_TXT",
              "82. Why not registered — Other (specify) text", length=120),
    ]
    return record("E_PRIMARY_CARE",
                  "E. Primary Care Utilization", "G", items)


# ============================================================
# Section F. Patient's Health-Seeking Behavior (Q83-Q87) — Apr 20
# ============================================================

def build_section_f():
    Q83_REASON = [
        ("Consultation for new health problem",                      "1"),
        ("Consultation to follow-up an ongoing health problem",      "2"),
        ("For tests/diagnostics only",                               "3"),
        ("For a general check-up",                                   "4"),
        ("To get a health certificate/administrative reason",        "5"),
        ("For immunizations/vaccinations",                           "6"),
        ("My doctor transferred to this health facility",            "7"),
        ("Other (Specify)",                                          "8"),
    ]
    Q84_SERVICE = [
        ("Outpatient care (Consultation, procedure, or treatment where the patient visits "
         "and leaves within the same day)", "1"),
        ("Inpatient care (Care provided in hospital or another facility where the patient is "
         "admitted for at least one night)", "2"),
        ("Emergency care (Care for serious illnesses or injuries that need immediate medical "
         "attention; usually provided in an emergency room or ER)", "3"),
        ("Primary care consultation",                                                        "4"),
        ("Other (Specify)",                                                                  "5"),
    ]
    Q85_CONDITIONS = [
        ("Upper respiratory infection",                                  "01"),
        ("Hypertension",                                                 "02"),
        ("Immunization",                                                 "03"),
        ("Pregnancy or birth",                                           "04"),
        ("Flu",                                                          "05"),
        ("Fever",                                                        "06"),
        ("Joint and muscle pain",                                        "07"),
        ("Asthma or COPD (chronic breathing problem, not cancer)",       "08"),
        ("Diabetes",                                                     "09"),
        ("Heart problem",                                                "10"),
        ("Kidney problem /Dialysis",                                     "11"),
        ("Cancer (any)",                                                 "12"),
        ("Gastro problem (vomiting, diarrhea etc.)",                     "13"),
        ("Other infection (e.g. urine, skin, other virus etc.)",         "14"),
        ("Accident/injury (e.g. wound/broken bone)",                     "15"),
        ("Dental",                                                       "16"),
        ("ENT (problem with ear/nose/throat)",                           "17"),
        ("Allergy",                                                      "18"),
        ("No condition - Regular check-up only",                         "19"),
        ("Other (Specify)",                                              "20"),
    ]
    Q86_VISIT_EVENTS = [
        ("Saw a doctor",                                                                      "01"),
        ("Saw a nurse/midwife",                                                               "02"),
        ("Saw any other healthcare worker/member of medical staff",                           "03"),
        ("Had basic tests done (e.g. blood pressure check, height/weight)",                   "04"),
        ("Had any laboratory tests done (e.g. blood, urine sample)",                          "05"),
        ("Had any imaging done (e.g. ultrasound, Xray, CT)",                                  "06"),
        ("Prescribed medication",                                                             "07"),
        ("Had any minor procedure/surgery done",                                              "08"),
        ("Picked up medical certificate/other administration",                                "09"),
        ("Was admitted for confinement",                                                      "10"),
    ]
    Q87_OTHER_ACTIONS = [
        ("Visited other healthcare facility",                                                 "1"),
        ("Sought alternative care (Healthcare apart from medical doctors or the formal "
         "healthcare system; such as reflexology, acupuncture, massage therapy, herbal "
         "medicines, etc.)",                                                                   "2"),
        ("Sought telemedicine (Remote diagnosis and treatment of patients by means of "
         "telecommunications technology)",                                                     "3"),
        ("Used home care (Healthcare services and support provided to individuals in their "
         "own homes)",                                                                         "4"),
        ("Bought medicine from a pharmacy",                                                    "5"),
        ("Did not seek other forms of care",                                                   "6"),
        ("Other (Specify)",                                                                    "7"),
    ]
    items = [
        select_one("Q83_VISIT_REASON",
                   "83. What best describes why the patient visited a health facility "
                   "(e.g. RHU, health center, clinic, hospital)?", Q83_REASON, length=1),
        alpha("Q83_VISIT_REASON_OTHER_TXT",
              "83. Visit reason — Other (specify) text", length=120),
        select_one("Q84_SERVICE_TYPE",
                   "84. What type of service did the patient usually access?",
                   Q84_SERVICE, length=1),
        alpha("Q84_SERVICE_TYPE_OTHER_TXT",
              "84. Service type — Other (specify) text", length=120),
        *select_all("Q85_CONDITIONS",
                    "85. What condition/s do/es the patient usually visit the facility for?",
                    Q85_CONDITIONS),
        alpha("Q85_CONDITIONS_OTHER_TXT",
              "85. Conditions — Other (specify) text", length=120),
        *select_all("Q86_VISIT_EVENTS",
                    "86. Which of the following happened during the patient's most recent visit?",
                    Q86_VISIT_EVENTS),
        *select_all("Q87_OTHER_ACTIONS",
                    "87. Apart from this visit, has the patient done anything else to improve "
                    "his/her health condition or address his/her health concern?", Q87_OTHER_ACTIONS),
        alpha("Q87_OTHER_ACTIONS_OTHER_TXT",
              "87. Other actions — Other (specify) text", length=120),
    ]
    return record("F_HEALTH_SEEKING",
                  "F. Patient's Health-Seeking Behavior", "H", items)


# ============================================================
# Section G. Outpatient Care (Q88-Q104) — Apr 20
# ============================================================

def build_section_g():
    Q88_WHY_VISIT = [
        ("Sick/Injured",                     "1"),
        ("Prenatal/Post-natal Check-up",     "2"),
        ("Gave Birth",                       "3"),
        ("Dental check-up",                  "4"),
        ("Medical check-up",                 "5"),
        ("Medical requirement",              "6"),
        ("NHTS/CCT/4Ps Requirement",         "7"),
        ("Other (specify)",                  "8"),
    ]
    Q90_NOT_CONFINED = [
        ("Facility is far",                                 "1"),
        ("No money",                                        "2"),
        ("Worried about treatment cost",                    "3"),
        ("Home remedy is available",                        "4"),
        ("Health facility is not PhilHealth accredited",    "5"),
        ("No need/regular check-up only",                   "6"),
        ("Other (specify)",                                 "7"),
    ]
    Q92_PAYMENT_SRC = [
        ("Out-of-pocket",                        "01"),
        ("Donation",                             "02"),
        ("Free/no cost",                         "03"),
        ("Free, charge to PhilHealth",           "04"),
        ("Free, charge to Private Insurance",    "05"),
        ("Free, charge to HMO",                  "06"),
        ("In kind",                              "07"),
        ("Don't know",                           "08"),
    ]
    Q93_LABS = [
        ("CBC with platelet count",   "01"),
        ("Urinalysis",                "02"),
        ("Fecalysis",                 "03"),
        ("Sputum Microscopy",         "04"),
        ("Fecal Occult Blood",        "05"),
        ("Pap smear",                 "06"),
        ("Lipid profile",             "07"),
        ("FBS",                       "08"),
        ("OGTT (Oral glucose tolerance tests)", "09"),
        ("ECG",                       "10"),
        ("Chest X-Ray",               "11"),
        ("Creatinine",                "12"),
        ("HbA1c",                     "13"),
        ("Abdominal ultrasound",      "14"),
        ("Dental Services",           "15"),
        ("Other, specify:",           "16"),
        ("None",                      "17"),  # proceed to Q95
    ]
    Q96_MEDS_PAY = [
        ("Out-of-pocket",                        "01"),
        ("Free/no cost",                         "02"),
        ("Free, charge to PhilHealth",           "03"),
        ("Free, charge to Private Insurance",    "04"),
        ("Free, charge to HMO",                  "05"),
        ("In kind",                              "06"),
        ("Donation",                             "07"),
        ("Don't know",                           "08"),
    ]
    Q971_EXPENSES = [
        ("Consultation Fee",                          "1"),
        ("Medical equipment or supplies",             "2"),
        ("Non-medical expenses (e.g. Hygiene kit)",   "3"),
        ("Other expenses",                            "4"),
    ]
    Q972_EXPENSES = [
        ("a) Consultation Fee",                             "1"),
        ("b) Diagnostic or laboratory procedure",           "2"),
        ("c) Medical equipment or supplies",                "3"),
        ("d) Medicines or drugs",                           "4"),
        ("e) Non-medical expenses: travel",                 "5"),
        ("f) Other expenses",                               "6"),
    ]
    Q98_SOURCES = [
        ("Salary/income",                                                      "01"),
        ("Loan/Mortgage",                                                      "02"),
        ("Savings",                                                            "03"),
        ("Donation/Charity/Assistance from Private Organization",              "04"),
        ("Malasakit Center",                                                   "05"),
        ("Other Donation/Charity/Assistance from Government Organization",     "06"),
        ("Sale of Assets",                                                     "07"),
        ("Paid by someone else",                                               "08"),
        ("MAIFIP",                                                             "09"),
        ("PhilHealth",                                                         "10"),
        ("SSS",                                                                "11"),
        ("GSIS",                                                               "12"),
        ("Private Insurance",                                                  "13"),
        ("HMO",                                                                "14"),
        ("Other (specify)",                                                    "15"),
    ]
    Q100_BUCAS_SOURCE = [
        ("News",                       "1"),
        ("Legislation",                "2"),
        ("Social Media",               "3"),
        ("Friends / Family",           "4"),
        ("Health center/facility",     "5"),
        ("LGU/Barangay",               "6"),
        ("I don't know",               "7"),
        ("Other (Specify)",            "8"),
    ]
    Q101_BUCAS_UNDERSTAND = [
        ("Provides urgent care for non-life-threatening/serious conditions",  "1"),
        ("Offers outpatient and ambulatory health services",                  "2"),
        ("Helps reduce overcrowding in hospitals",                            "3"),
        ("Allows access to timely medical consultation and treatment",        "4"),
        ("Other (specify)",                                                   "5"),
    ]
    Q103_BUCAS_SERVICES = [
        ("Medical consultation for urgent or minor conditions",               "1"),
        ("Outpatient or ambulatory care services",                            "2"),
        ("Basic diagnostic services (e.g., laboratory tests, X-ray)",         "3"),
        ("Minor procedures or treatments",                                    "4"),
        ("Referral to higher-level health facilities",                        "5"),
        ("I don't know",                                                      "6"),
        ("Other (specify)",                                                   "7"),
    ]
    Q104_ALT = [
        ("Another DOH hospital",                    "1"),
        ("Private clinic/hospital",                 "2"),
        ("LGU hospital",                            "3"),
        ("Rural Health Unit / Health Center",       "4"),
        ("Would not seek care",                     "5"),
        ("Others",                                  "6"),
    ]
    items = [
        select_one("Q88_WHY_VISIT",
                   "88. Why are you visiting [FACILITY_NAME_INPUT] for consultation/advice or treatment?",
                   Q88_WHY_VISIT, length=1),
        alpha("Q88_WHY_VISIT_OTHER_TXT",
              "88. Why visit — Other (specify) text", length=120),
        yes_no("Q89_ADVISED_ADMIT",
               "89. Were you advised for hospitalization / to be admitted in the hospital?"),
        *select_all("Q90_NOT_CONFINED",
                    "90. What were the reasons why you were not confined/ admitted in a hospital/clinic?",
                    Q90_NOT_CONFINED),
        alpha("Q90_NOT_CONFINED_OTHER_TXT",
              "90. Reasons not confined — Other (specify) text", length=120),
        yes_no("Q91_USUAL_OUTPATIENT",
               "91. Do you usually avail consultation services for outpatient care?"),
    ]
    # Q92 consultation cost — payment-source matrix
    for label, code in Q92_PAYMENT_SRC:
        items.append(yes_no(f"Q92_PAY_{code}", f"92. Cost of consultation — {label}"))
        items.append(numeric(f"Q92_PAY_{code}_AMT",
                             f"92. Cost of consultation — {label} (Amount in Pesos)", length=8))
    items.extend([
        *select_all("Q93_LABS",
                    "93. Did you have any of the following laboratory tests done during your outpatient care?",
                    Q93_LABS),
        alpha("Q93_LABS_OTHER_TXT",
              "93. Lab tests — Other, specify text", length=120),
    ])
    # Q94 lab test cost — payment-source matrix (aggregate; spec asks per-test roster)
    for label, code in Q92_PAYMENT_SRC:
        items.append(yes_no(f"Q94_PAY_{code}",
                            f"94. Cost of laboratory test/s — {label}"))
        items.append(numeric(f"Q94_PAY_{code}_AMT",
                             f"94. Cost of laboratory test/s — {label} (Amount in Pesos)", length=8))
    items.extend([
        yes_no("Q95_PRESCRIBED",
               "95. Were you prescribed medicine/s after your check-up?"),
    ])
    # Q96 prescribed meds cost — payment-source matrix
    for label, code in Q96_MEDS_PAY:
        items.append(yes_no(f"Q96_PAY_{code}",
                            f"96. Amount spent for prescribed medicines — {label}"))
        items.append(numeric(f"Q96_PAY_{code}_AMT",
                             f"96. Amount spent for prescribed medicines — {label} (Amount in Pesos)",
                             length=8))
    items.append(numeric("Q97_FINAL_AMOUNT",
                         "97. What was the final amount you paid in cash for your outpatient care? "
                         "(Amount in Pesos)", length=8))
    # Q97.1 other expenses in bill — select all + amounts
    for label, code in Q971_EXPENSES:
        items.append(yes_no(f"Q971_{code}",
                            f"97.1 Other items included in the bill — {label}"))
        items.append(numeric(f"Q971_{code}_AMT",
                             f"97.1 Other items included in the bill — {label} (Amount in Pesos)",
                             length=8))
    items.append(alpha("Q971_OTHER_TXT",
                       "97.1 Other expenses — specify text", length=120))
    # Q97.2 other expenses not in bill — select all + amounts
    for label, code in Q972_EXPENSES:
        items.append(yes_no(f"Q972_{code}",
                            f"97.2 Other expenses during OPD visit not in bill — {label}"))
        items.append(numeric(f"Q972_{code}_AMT",
                             f"97.2 Other expenses during OPD visit not in bill — {label} (Amount in Pesos)",
                             length=8))
    items.append(alpha("Q972_OTHER_TXT",
                       "97.2 Other expenses — specify text", length=120))
    # Q98 15-source payment matrix
    for label, code in Q98_SOURCES:
        items.append(yes_no(f"Q98_PAY_{code}",
                            f"98. Used to pay for medical costs — {label}"))
        items.append(numeric(f"Q98_PAY_{code}_AMT",
                             f"98. Used to pay for medical costs — {label} (Amount in Pesos)",
                             length=8))
    items.append(alpha("Q98_OTHER_DONATION_TXT",
                       "98. Other Donation/Charity/Assistance from Government Organization — specify text",
                       length=120))
    items.append(alpha("Q98_OTHER_TXT",
                       "98. Other payment source — specify text", length=120))
    # BUCAS block (Q99-104)
    items.extend([
        yes_no("Q99_BUCAS_HEARD",
               "99. Have you heard about Bagong Urgent Care and Ambulatory Services (BUCAS) center?"),
        *select_all("Q100_BUCAS_SOURCE",
                    "100. If yes, what are your sources of information about this BUCAS center?",
                    Q100_BUCAS_SOURCE),
        alpha("Q100_BUCAS_SOURCE_OTHER_TXT",
              "100. BUCAS source — Other (specify) text", length=120),
        *select_all("Q101_BUCAS_UNDERSTAND",
                    "101. What is your understanding about a BUCAS center?",
                    Q101_BUCAS_UNDERSTAND),
        alpha("Q101_BUCAS_UNDERSTAND_OTHER_TXT",
              "101. BUCAS understanding — Other (specify) text", length=120),
        yes_no("Q102_BUCAS_ACCESSED",
               "102. Have you accessed the services in a BUCAS center?"),
        *select_all("Q103_BUCAS_SERVICES",
                    "103. If yes, which service/s did you avail?",
                    Q103_BUCAS_SERVICES),
        alpha("Q103_BUCAS_SERVICES_OTHER_TXT",
              "103. BUCAS services — Other (specify) text", length=120),
        select_one("Q104_WITHOUT_BUCAS",
                   "104. Without BUCAS Center, where would you have gone?",
                   Q104_ALT, length=1),
        alpha("Q104_WITHOUT_BUCAS_OTHER_TXT",
              "104. Without BUCAS — Others specify text", length=120),
    ])
    return record("G_OUTPATIENT_CARE",
                  "G. Outpatient Care", "I", items)


# ============================================================
# Section H. Inpatient Care (Q105-Q115) — Apr 20
# ============================================================

def build_section_h():
    Q105_REASON = [
        ("Sick",                 "1"),
        ("Injured",              "2"),
        ("Gave birth",           "3"),
        ("Executive check-up",   "4"),
        ("Other (specify)",      "5"),
    ]
    Q107_PAYMENT = [
        ("Out-of-pocket",                      "01"),
        ("Free/no cost",                       "02"),
        ("Free, charge to PhilHealth",         "03"),
        ("Free, charge to Private Insurance",  "04"),
        ("Free, charge to HMO",                "05"),
        ("Free, charge to MAIFIP",             "06"),
        ("Donation",                           "07"),
        ("In kind",                            "08"),
        ("Don't know",                         "09"),
        ("Other",                              "10"),
    ]
    Q109_PAYMENT = [
        ("Out-of-pocket",                      "01"),
        ("Free/no cost",                       "02"),
        ("Free, charge to PhilHealth",         "03"),
        ("Free, charge to Private Insurance",  "04"),
        ("Free, charge to HMO",                "05"),
        ("Free, charge to MAIFIP",             "06"),
        ("In kind",                            "07"),
        ("Don't know",                         "08"),
        ("Other",                              "09"),
    ]
    Q113_SOURCES = [
        ("Salary/income",                                                  "01"),
        ("Loan/Mortgage",                                                  "02"),
        ("Savings",                                                        "03"),
        ("Donation/Charity/Assistance from Private Organization",          "04"),
        ("Malasakit Center",                                               "05"),
        ("Other Donation/Charity/Assistance from Government Organization", "06"),
        ("MAIFIP",                                                         "07"),
        ("PhilHealth",                                                     "08"),
        ("SSS",                                                            "09"),
        ("GSIS",                                                           "10"),
        ("Private Insurance",                                              "11"),
        ("HMO",                                                            "12"),
        ("Other (specify)",                                                "13"),
    ]
    Q114_NO_PH = [
        ("Not a PhilHealth member",                                                            "1"),
        ("PhilHealth member but not eligible for benefits",                                    "2"),
        ("Probably used PhilHealth but cannot remember amount because benefit was deducted "
         "upon discharge from hospital",                                                       "3"),
        ("Too many requirements to comply with before can avail",                              "4"),
        ("Limited hospitalization benefits",                                                   "5"),
        ("Claims processing too long",                                                         "6"),
        ("Other (specify)",                                                                    "7"),
    ]
    Q1141_IN_BILL = [
        ("Doctor's Professional Fee",                                       "1"),
        ("Medical equipment or supplies",                                   "2"),
        ("Non-medical expenses (e.g. Hygiene kit)",                         "3"),
        ("Diagnostic or laboratory procedure inside the facility",          "4"),
        ("Medicines or drugs inside the facility",                          "5"),
        ("Other expenses",                                                  "6"),
    ]
    Q1142_NOT_IN_BILL = [
        ("Medical equipment or supplies bought outside the facility",       "1"),
        ("Payment made directly to doctor/s and their secretary",           "2"),
        ("Food",                                                            "3"),
        ("Transportation",                                                  "4"),
        ("Donation to the facility",                                        "5"),
        ("Allowance for caregiver",                                         "6"),
        ("Other (specify)",                                                 "7"),
    ]
    items = [
        select_one("Q105_REASON",
                   "105. Why are you confined in the hospital?", Q105_REASON, length=1),
        alpha("Q105_REASON_OTHER_TXT",
              "105. Confinement reason — Other (specify) text", length=120),
        numeric("Q106_NIGHTS",
                "106. How long were you confined? — Nights", length=3),
        numeric("Q106_DAYS",
                "106. How long were you confined? — Days", length=3),
    ]
    # Q107 total bill — 10-source payment matrix
    for label, code in Q107_PAYMENT:
        items.append(yes_no(f"Q107_PAY_{code}",
                            f"107. Total bill for confinement — {label}"))
        items.append(numeric(f"Q107_PAY_{code}_AMT",
                             f"107. Total bill for confinement — {label} (Amount in Pesos)",
                             length=9))
    items.append(alpha("Q107_PAY_OTHER_TXT",
                       "107. Total bill — Other, specify text", length=120))
    items.append(yes_no("Q108_MEDS_OUTSIDE",
                        "108. Other than the medicine/s indicated in the hospital bill, did the patient "
                        "buy medicine/s from any pharmacy/facility outside the hospital?"))
    # Q109 meds outside — 9-source payment matrix
    for label, code in Q109_PAYMENT:
        items.append(yes_no(f"Q109_PAY_{code}",
                            f"109. Amount paid for medicines outside the hospital — {label}"))
        items.append(numeric(f"Q109_PAY_{code}_AMT",
                             f"109. Amount paid for medicines outside the hospital — {label} "
                             "(Amount in Pesos)", length=9))
    items.append(alpha("Q109_PAY_OTHER_TXT",
                       "109. Meds outside — Other, specify text", length=120))
    items.append(yes_no("Q110_LAB_OUTSIDE",
                        "110. Other than the laboratory service/s indicated in the hospital bill, did "
                        "the patient pay for other service/s outside the hospital?"))
    items.append(alpha("Q111_SERVICES_OUTSIDE",
                       "111. If yes, what are those services?", length=240))
    # Q112 services outside — 9-source payment matrix
    for label, code in Q109_PAYMENT:
        items.append(yes_no(f"Q112_PAY_{code}",
                            f"112. Amount paid for services outside the hospital — {label}"))
        items.append(numeric(f"Q112_PAY_{code}_AMT",
                             f"112. Amount paid for services outside the hospital — {label} "
                             "(Amount in Pesos)", length=9))
    items.append(alpha("Q112_PAY_OTHER_TXT",
                       "112. Services outside — Other, specify text", length=120))
    # Q113 13-source hospital bill payment matrix
    for label, code in Q113_SOURCES:
        items.append(yes_no(f"Q113_PAY_{code}",
                            f"113. Used to pay for hospital bill — {label}"))
        items.append(numeric(f"Q113_PAY_{code}_AMT",
                             f"113. Used to pay for hospital bill — {label} (Amount in Pesos)",
                             length=9))
    items.append(alpha("Q113_PAY_OTHER_TXT",
                       "113. Hospital bill payment — Other specify text", length=120))
    items.extend([
        *select_all("Q114_NO_PH",
                    "114. Why did you not avail of PhilHealth benefits? (If PhilHealth was not availed in 113)",
                    Q114_NO_PH),
        alpha("Q114_NO_PH_OTHER_TXT",
              "114. Why no PhilHealth — Other (specify) text", length=120),
    ])
    # Q114.1 other expenses included in bill — 6 items with amount
    for label, code in Q1141_IN_BILL:
        items.append(yes_no(f"Q1141_{code}",
                            f"114.1 Other items included in the bill — {label}"))
        items.append(numeric(f"Q1141_{code}_AMT",
                             f"114.1 Other items included in the bill — {label} (Amount in Pesos)",
                             length=9))
    items.append(alpha("Q1141_OTHER_TXT",
                       "114.1 Other expenses — specify text", length=120))
    # Q114.2 other expenses NOT included in bill — 7 items with amount
    for label, code in Q1142_NOT_IN_BILL:
        items.append(yes_no(f"Q1142_{code}",
                            f"114.2 Other expenses during confinement not in bill — {label}"))
        items.append(numeric(f"Q1142_{code}_AMT",
                             f"114.2 Other expenses during confinement not in bill — {label} "
                             "(Amount in Pesos)", length=9))
    items.append(alpha("Q1142_OTHER_TXT",
                       "114.2 Other expenses — specify text", length=120))
    items.append(numeric("Q115_FINAL_CASH",
                         "115. What was the final amount you paid in cash at the hospital cashier "
                         "upon discharge? (Amount in Pesos)", length=9))
    return record("H_INPATIENT_CARE",
                  "H. Inpatient Care", "J", items)


# ============================================================
# Section I. Financial Risk Protection (Q116-Q130) — Apr 20
# ============================================================

def build_section_i():
    Q116_HEARD = [
        ("Yes",          "1"),
        ("No",           "2"),  # proceed to Q119
        ("I don't know", "3"),  # proceed to Q119
    ]
    Q119_HEARD = [
        ("Yes",          "1"),
        ("No",           "2"),  # proceed to Q124
        ("I don't know", "3"),  # proceed to Q124
    ]
    Q124_HEARD = [
        ("Yes",          "1"),
        ("No",           "2"),  # proceed to Q130
        ("I don't know", "3"),  # proceed to Q130
    ]
    SOURCE_8 = [
        ("News",                     "1"),
        ("Legislation",              "2"),
        ("Social Media",             "3"),
        ("Friends / Family",         "4"),
        ("Health center/facility",   "5"),
        ("LGU/Barangay",             "6"),
        ("I don't know",             "7"),
        ("Other (Specify)",          "8"),
    ]
    Q118_UNDERSTAND_NBB = [
        ("Patient does not pay any hospital bill",                        "1"),
        ("PhilHealth will cover cost of treatment",                       "2"),
        ("Medicine and service are already included",                     "3"),
        ("No cash payment required upon discharge",                       "4"),
        ("Applies only to certain patients or hospitals",                 "5"),
        ("Bills are settled between the hospital and PhilHealth",         "6"),
        ("Patients should not be charged extra fees",                     "7"),
        ("I don't know",                                                  "8"),
        ("Other (Specify)",                                               "9"),
    ]
    Q121_UNDERSTAND_ZBB = [
        ("Patient does not pay any hospital bill",                        "1"),
        ("PhilHealth will cover cost of treatment",                       "2"),
        ("Medicine and service are already included",                     "3"),
        ("No cash payment required upon discharge",                       "4"),
        ("Applies only to PhilHealth members and DOH-run hospitals",      "5"),
        ("Bills are settled between the hospital and PhilHealth",         "6"),
        ("Patients should not be charged extra fees",                     "7"),
        ("I don't know",                                                  "8"),
        ("Other (Specify)",                                               "9"),
    ]
    Q123_ZBB_EXTENT = [
        ("ZBB significantly reduced my financial burden by covering my expenses",                "1"),
        ("It helped lessen some costs, but I still incurred Out-of-Pocket (OOP) expenses",       "2"),
        ("ZBB provided some financial relief, though the support was limited compared to my "
         "total needs",                                                                           "3"),
        ("ZBB did not make a noticeable difference in my financial situation",                   "4"),
    ]
    Q128_OOP_ITEMS = [
        ("Drugs",              "1"),
        ("Laboratory",         "2"),
        ("Professional Fees",  "3"),
        ("Accommodation",      "4"),
    ]
    Q129_WHY_NO_MAIFIP = [
        ("Not eligible",                            "1"),
        ("Too complicated",                         "2"),
        ("I don't like to stay in basic ward",      "3"),
        ("There is no available basic ward",        "4"),
    ]
    Q130_REDUCED_SPEND = [
        ("Yes",                "1"),
        ("No",                 "2"),
        ("Don't know",         "3"),
        ("Refused to answer",  "4"),
    ]
    items = [
        select_one("Q116_NBB_HEARD",
                   "116. Have you heard of the No Balance Billing (NBB)?",
                   Q116_HEARD, length=1),
        *select_all("Q117_NBB_SOURCE",
                    "117. If yes, what are your sources of information about NBB?", SOURCE_8),
        alpha("Q117_NBB_SOURCE_OTHER_TXT",
              "117. NBB source — Other (specify) text", length=120),
        *select_all("Q118_NBB_UNDERSTAND",
                    "118. What is your understanding about NBB?", Q118_UNDERSTAND_NBB),
        alpha("Q118_NBB_UNDERSTAND_OTHER_TXT",
              "118. NBB understanding — Other (specify) text", length=120),
        select_one("Q119_ZBB_HEARD",
                   "119. Have you heard of the Zero Balance Billing (ZBB)?",
                   Q119_HEARD, length=1),
        *select_all("Q120_ZBB_SOURCE",
                    "120. If yes, what are your sources of information about ZBB?", SOURCE_8),
        alpha("Q120_ZBB_SOURCE_OTHER_TXT",
              "120. ZBB source — Other (specify) text", length=120),
        *select_all("Q121_ZBB_UNDERSTAND",
                    "121. What is your understanding about ZBB?", Q121_UNDERSTAND_ZBB),
        alpha("Q121_ZBB_UNDERSTAND_OTHER_TXT",
              "121. ZBB understanding — Other (specify) text", length=120),
        yes_no("Q122_ZBB_INFORMED",
               "122. Were you informed about ZBB upon admission?"),
        select_one("Q123_ZBB_EXTENT",
                   "123. To what extent did ZBB reduce your financial burden?",
                   Q123_ZBB_EXTENT, length=1),
        select_one("Q124_MAIFIP_HEARD",
                   "124. Have you heard of the Medical Assistance for Indigent and "
                   "Financially Incapacitated Patients (MAIFIP)? (SKIP IF ANSWERED MAIFIP IN Q113)",
                   Q124_HEARD, length=1),
        *select_all("Q125_MAIFIP_SOURCE",
                    "125. What are your sources of information about MAIFIP?", SOURCE_8),
        alpha("Q125_MAIFIP_SOURCE_OTHER_TXT",
              "125. MAIFIP source — Other (specify) text", length=120),
        yes_no("Q126_MAIFIP_AVAILED",
               "126. Did you avail of MAIFIP in this last confinement?"),
        yes_no("Q127_MAIFIP_OOP",
               "127. If you availed MAIFIP, did you have to make any out-of-pocket payment?"),
        *select_all("Q128_MAIFIP_OOP_ITEMS",
                    "128. Which items did you have to pay for out-of-pocket?",
                    Q128_OOP_ITEMS),
        *select_all("Q129_WHY_NO_MAIFIP",
                    "129. Why did you not avail of MAIFP during this last confinement?",
                    Q129_WHY_NO_MAIFIP),
        select_one("Q130_REDUCED_SPEND",
                   "130. Have you or your household had to reduce spending on things you need "
                   "(such as food, housing, or utilities) because of this health expenditure "
                   "in the last 1 month?",
                   Q130_REDUCED_SPEND, length=1),
    ]
    return record("I_FINANCIAL_RISK",
                  "I. Financial Risk Protection", "K", items)


# ============================================================
# Section J. Satisfaction on Amenities and Medical Care (Q131-Q144) — Apr 20
# ============================================================

def build_section_j():
    FREQUENCY_5PT = [
        ("Never",         "1"),
        ("Sometimes",     "2"),
        ("Usually",       "3"),
        ("Always",        "4"),
        ("I don't know",  "5"),
    ]
    YES_NO_DK = [
        ("Yes",          "1"),
        ("No",           "2"),
        ("I don't know", "3"),
    ]
    AMENITY_ITEMS = [
        ("Q131_AMEN_WAITING",       "131. Satisfaction with cleanliness and comfort — Waiting areas"),
        ("Q132_AMEN_BATHROOMS",     "132. Satisfaction with cleanliness and comfort — Bathrooms and toilets"),
        ("Q133_AMEN_CONSULT_ROOMS", "133. Satisfaction with cleanliness and comfort — Consultation Rooms"),
        ("Q134_AMEN_ROOMS",         "134. Satisfaction with cleanliness and comfort — Rooms (for inpatients only)"),
    ]
    STAFF_FREQ_ITEMS = [
        ("Q136_STAFF_COURTESY", "136. In most recent visit, how often did the staff treat you with courtesy and respect?"),
        ("Q137_STAFF_LISTEN",   "137. In most recent visit, how often did the staff listen carefully to what you say or ask?"),
        ("Q138_STAFF_EXPLAIN",  "138. In most recent visit, how often did the staff explain your condition and procedures in a way you can understand?"),
        ("Q139_STAFF_DECIDE",   "139. In most recent visit, how often did the staff give you the chance to make decisions about your treatment?"),
        ("Q140_STAFF_CONSENT",  "140. In most recent visit, how often did the staff ask you for your consent before performing any treatments or tests?"),
    ]
    items = []
    for name, label in AMENITY_ITEMS:
        items.append(select_one(name, label, SATISFACTION_5PT, length=1))
    items.append(select_one("Q135_SAT_OVERALL_TIME",
                            "135. Were you satisfied with the overall time spent from registration "
                            "to exiting the facility? (For inpatients only)",
                            SATISFACTION_5PT, length=1))
    for name, label in STAFF_FREQ_ITEMS:
        items.append(select_one(name, label, FREQUENCY_5PT, length=1))
    items.extend([
        select_one("Q141_CONFIDENTIALITY",
                   "141. In your most recent visit, did the staff assure you that information about the "
                   "patient's condition will be kept confidential?", YES_NO_DK, length=1),
        select_one("Q142_PRIVACY",
                   "142. In your most recent visit, did the staff respect your privacy during the "
                   "physical consultation?", YES_NO_DK, length=1),
        yes_no("Q143_RECOMMEND",
               "143. Overall, would you recommend [facility_name_input] to a friend or relative?"),
        select_one("Q144_QUALITY",
                   "144. How would the patient rate the quality of care you received at "
                   "[facility_name_input]?", SATISFACTION_5PT, length=1),
    ])
    return record("J_SATISFACTION",
                  "J. Satisfaction on Amenities and Medical Care", "L", items)


# ============================================================
# Section K. Access to Medicines (Q101-Q110)
# ============================================================

def build_section_k():
    Q145_FREQ = [
        ("Weekly",    "1"),
        ("Bi-weekly", "2"),
        ("Monthly",   "3"),
        ("Rarely",    "4"),
        ("Never",     "5"),
    ]
    Q146_RX_TYPE = [
        ("Prescribed by a doctor",                              "1"),
        ("Over-the-counter medicine",                           "2"),
        ("Purchased both prescribed medicine and OTC medicine", "3"),
        ("I don't know",                                        "4"),
    ]
    Q148_CONDITIONS = [
        ("Upper respiratory infection",                                  "01"),
        ("Hypertension",                                                 "02"),
        ("Immunization",                                                 "03"),
        ("Pregnancy or birth",                                           "04"),
        ("Flu",                                                          "05"),
        ("Fever",                                                        "06"),
        ("Joint and muscle pain",                                        "07"),
        ("Asthma or COPD (chronic breathing problem, not cancer)",       "08"),
        ("Diabetes",                                                     "09"),
        ("Heart problem",                                                "10"),
        ("Kidney problem /Dialysis",                                     "11"),
        ("Cancer (any)",                                                 "12"),
        ("Gastro problem (vomiting, diarrhea, etc.)",                    "13"),
        ("Other infection (e.g. urine, skin, other virus etc.)",         "14"),
        ("Accident/injury (e.g. wound/broken bone)",                     "15"),
        ("Dental",                                                       "16"),
        ("ENT (problem with ear/nose/throat)",                           "17"),
        ("Allergy",                                                      "18"),
        ("No condition - Regular check-up only",                         "19"),
        ("Other (Specify)",                                              "20"),
    ]
    Q149_WHERE_BUY = [
        ("Public Hospital",                                              "1"),
        ("Private Hospital",                                             "2"),
        ("Chain Pharmacies (e.g. Mercury Drug, Watsons, TGP, Generika)", "3"),
        ("Local pharmacies",                                             "4"),
        ("Online stores (e.g. Shopee, Lazada)",                          "5"),
        ("Barangay Health Station",                                      "6"),
        ("Rural Health Unit or City Health Office",                      "7"),
        ("Other (specify)",                                              "8"),
    ]
    Q151_EASE = [
        ("Very difficult", "1"),
        ("Difficult",      "2"),
        ("Neutral",        "3"),
        ("Easy",           "4"),
        ("Very easy",      "5"),
    ]
    Q153_GAMOT_SRC = [
        ("News",                   "1"),
        ("Legislation",            "2"),
        ("Social Media",           "3"),
        ("Friends / Family",       "4"),
        ("Health center/facility", "5"),
        ("LGU/Barangay",           "6"),
        ("I don't know",           "7"),
        ("Other (Specify)",        "8"),
    ]
    Q154_GAMOT_UNDERSTAND = [
        ("Provides free or affordable medicines for outpatients",         "1"),
        ("Ensures continuous availability of essential medicines",        "2"),
        ("Helps reduce out-of-pocket expenses for medicines",             "3"),
        ("Supports treatment of common illnesses and chronic conditions", "4"),
        ("I don't know",                                                  "5"),
        ("Other (specify)",                                               "6"),
    ]
    Q157_WHERE_REST = [
        ("Purchased from pharmacy",                    "1"),
        ("Purchased from public hospital",             "2"),
        ("Purchased from private hospital",            "3"),
        ("Purchased from primary care provider (PCP)", "4"),
        ("Received from PCP for free",                 "5"),
        ("Received from LGU for free",                 "6"),
        ("Received from public hospital for free",     "7"),
        ("Received from private hospital for free",    "8"),
        ("Other (Specify)",                            "9"),
    ]
    Q159_BRANDED_GENERIC = [
        ("Branded",                   "1"),
        ("Generic",                   "2"),
        ("Both branded and generic",  "3"),
        ("Don't know the difference", "4"),
        ("Not applicable",            "5"),
    ]
    Q160_WHY_GENERIC = [
        ("Lower cost",                               "1"),
        ("Prescribed by doctor",                     "2"),
        ("Readily available",                        "3"),
        ("Given for free",                           "4"),
        ("More or as effective as branded medicine", "5"),
        ("I don't know",                             "6"),
        ("Other (Specify)",                          "7"),
    ]
    Q161_WHY_BRANDED = [
        ("Branded medicine is more effective than generic", "1"),
        ("Not aware of generic option",                     "2"),
        ("Prescribed by doctor",                            "3"),
        ("Given for free",                                  "4"),
        ("Prefer branded over generic option",              "5"),
        ("I don't know",                                    "6"),
        ("Other (Specify)",                                 "7"),
    ]
    items = [
        select_one("Q145_PURCHASE_FREQ",
                   "145. How often do you purchase or receive medicines?",
                   Q145_FREQ, length=1),
        select_one("Q146_RX_OR_OTC",
                   "146. Was the most recent medicine purchased prescribed by a doctor "
                   "or over-the-counter (OTC) medicine (no need for a prescription)?",
                   Q146_RX_TYPE, length=1),
        alpha("Q147_MEDS_LIST",
              "147. What are the medications that you usually take?", length=240),
        *select_all("Q148_CONDITIONS",
                    "148. What are the medical conditions that you take the medicines for?",
                    Q148_CONDITIONS),
        alpha("Q148_CONDITIONS_OTHER_TXT",
              "148. Conditions — Other (specify) text", length=120),
        *select_all("Q149_WHERE_BUY",
                    "149. Where do you usually buy or receive your medicines? "
                    "Select all that apply.", Q149_WHERE_BUY),
        alpha("Q149_WHERE_BUY_OTHER_TXT",
              "149. Where buy — Other (specify) text", length=120),
        numeric("Q150_TRAVEL_HH",
                "150. Travel time from home to nearest pharmacy — hours (HH)", length=2),
        numeric("Q150_TRAVEL_MM",
                "150. Travel time from home to nearest pharmacy — minutes (MM)", length=2),
        select_one("Q151_PHARM_EASE",
                   "151. How easy is it for you to access a pharmacy or drugstore?",
                   Q151_EASE, length=1),
        yes_no("Q152_GAMOT_HEARD",
               "152. Have you heard of the Guaranteed and Accessible Medications for "
               "Outpatient Treatment (GAMOT) Package, which is part of PhilHealth's "
               "YAKAP/Konsulta or primary care benefit package?"),
        *select_all("Q153_GAMOT_SOURCE",
                    "153. If yes, what are your sources of information for GAMOT Package?",
                    Q153_GAMOT_SRC),
        alpha("Q153_GAMOT_SOURCE_OTHER_TXT",
              "153. GAMOT source — Other (specify) text", length=120),
        *select_all("Q154_GAMOT_UNDERSTAND",
                    "154. What is your understanding of the GAMOT Package?",
                    Q154_GAMOT_UNDERSTAND),
        alpha("Q154_GAMOT_UNDERSTAND_OTHER_TXT",
              "154. GAMOT understanding — Other (specify) text", length=120),
        yes_no("Q155_GAMOT_GOT_MEDS",
               "155. Did you get the medicines from the GAMOT Package during the past 6 months?"),
        alpha("Q156_GAMOT_MEDS_LIST",
              "156. What are the medications that you obtained from the GAMOT Package? [LIST]",
              length=240),
        *select_all("Q157_WHERE_REST",
                    "157. Where did you get the rest of the medicines? Select all that apply.",
                    Q157_WHERE_REST),
        alpha("Q157_WHERE_REST_OTHER_TXT",
              "157. Where got rest — Other (specify) text", length=120),
        yes_no("Q158_BRAND_GEN_KNOW",
               "158. Do you know the difference between a 'branded' and a 'generic' medicine?"),
        select_one("Q159_BRAND_GEN_BOUGHT",
                   "159. Was/were the medicine/s you bought outside of GAMOT pharmacy "
                   "branded or generic?", Q159_BRANDED_GENERIC, length=1),
        *select_all("Q160_WHY_GENERIC",
                    "160. If generic, why did you buy generic medicine?",
                    Q160_WHY_GENERIC),
        alpha("Q160_WHY_GENERIC_OTHER_TXT",
              "160. Why generic — Other (specify) text", length=120),
        *select_all("Q161_WHY_BRANDED",
                    "161. If branded, why did you buy branded medicine?",
                    Q161_WHY_BRANDED),
        alpha("Q161_WHY_BRANDED_OTHER_TXT",
              "161. Why branded — Other (specify) text", length=120),
    ]
    return record("K_ACCESS_MEDICINES", "K. Access to Medicines", "M", items)


# ============================================================
# Section L. Referrals (Q111-Q120)
# ============================================================

def build_section_l():
    Q163_CARE_TYPE = [
        ("Outpatient care (Consultation, procedure, or treatment where the patient visits "
         "and leaves within the same day)",                                                   "01"),
        ("Emergency care (Care for serious illnesses or injuries that need immediate medical "
         "attention; usually provided in an emergency room or ER)",                           "02"),
        ("Inpatient care (Care provided in hospital or another facility where the patient is "
         "admitted for at least one night)",                                                  "03"),
        ("Dental care (Medical care for your teeth, such as cleanings, fillings, etc.)",      "04"),
        ("Other facility visits (Care that is provided in a facility that is not a health "
         "center or hospital, such as independent diagnostic centers, TB dispensaries, etc.)","05"),
        ("Special therapy visits (Rehabilitation care or services, such as occupational "
         "therapy, physical therapy, psychological and behavioral rehabilitation, prosthetics "
         "and orthotics rehabilitation, or speech and language therapy)",                     "06"),
        ("Alternative care (Healthcare apart from medical doctors or the formal health care "
         "system; such as reflexology, acupuncture, massage therapy, herbal medicines, etc.)","07"),
        ("Outreach / medical missions (Care provided by the government or an NGO through an "
         "outreach or medical mission within a community)",                                   "08"),
        ("Home healthcare (Care that is administered at the patient's home, such as birth "
         "delivery, checkups, immunization, rehabilitation, etc.)",                           "09"),
        ("Telemedicine (Remote diagnosis and treatment of patients by means of "
         "telecommunications technology)",                                                    "10"),
        ("None of the above",                                                                 "11"),
        ("Other (Specify)",                                                                   "12"),
    ]
    Q164_SPECIALIST = [
        ("No specialty",                            "01"),
        ("Anesthesia",                              "02"),
        ("Dermatology",                             "03"),
        ("Emergency Medicine",                      "04"),
        ("Family Medicine",                         "05"),
        ("General Surgery",                         "06"),
        ("Internal Medicine",                       "07"),
        ("Neurology",                               "08"),
        ("Nuclear Medicine",                        "09"),
        ("Obstetrics and Gynecology",               "10"),
        ("Occupational Medicine",                   "11"),
        ("Ophthalmology",                           "12"),
        ("Orthopedics",                             "13"),
        ("Otorhinolaryngology (ENT)",               "14"),
        ("Pathology",                               "15"),
        ("Pediatrics",                              "16"),
        ("Physical and Rehabilitation Medicine",    "17"),
        ("Psychiatry",                              "18"),
        ("Public health",                           "19"),
        ("Radiology",                               "20"),
        ("Research",                                "21"),
        ("I don't know",                            "22"),
        ("Other (Specify)",                         "23"),
    ]
    Q165_HOW_REFERRED = [
        ("Physical referral slip",                                  "1"),
        ("E-referral",                                              "2"),
        ("Phone call from referring facility to receiving facility", "3"),
        ("I don't know",                                            "4"),
        ("Other (Specify)",                                         "5"),
    ]
    Q169_VISITED = [
        ("Yes",                          "1"),
        ("No, I'm not planning to",      "2"),
        ("Not yet, but I'm planning to", "3"),
    ]
    Q171_WHY_NOT = [
        ("Facility is too far",                "1"),
        ("Do not trust the referred facility", "2"),
        ("No time",                            "3"),
        ("Worried about additional costs",     "4"),
        ("Not needed",                         "5"),
        ("Don't know how to get to facility",  "6"),
        ("Other (Specify)",                    "7"),
    ]
    Q173_PCP_KNOWS = [
        ("Yes",          "1"),
        ("No",           "2"),
        ("I don't know", "3"),
    ]
    Q177_WHY_HOSPITAL = [
        ("Referred by other specialist (doctor in another hospital)",                    "01"),
        ("Nearest facility to house",                                                    "02"),
        ("Facility is usual source of care",                                             "03"),
        ("Facility is the only place that can perform a certain test",                   "04"),
        ("Referred by BHW/nurse/midwife/other community health professional",            "05"),
        ("Referred by family / friends",                                                 "06"),
        ("Facility offers subsidized or free health services",                           "07"),
        ("ZBB eligibility",                                                              "08"),
        ("I don't know",                                                                 "09"),
        ("Other (Specify)",                                                              "10"),
    ]
    Q178_SAT_REFERRAL = [
        ("Very Satisfied",                    "1"),
        ("Satisfied",                         "2"),
        ("Neither Satisfied nor Dissatisfied","3"),
        ("Dissatisfied",                      "4"),
        ("Very Dissatisfied",                 "5"),
        ("Not applicable",                    "6"),
    ]
    items = [
        yes_no("Q162_REFERRED",
               "162. Based on your most recent visit/confinement at [facility_name_input], "
               "did a healthcare worker refer you to another facility or specialist for "
               "further care or specialized care?"),
        *select_all("Q163_CARE_TYPE",
                    "163. What type of care was the referral for?",
                    Q163_CARE_TYPE),
        alpha("Q163_CARE_TYPE_OTHER_TXT",
              "163. Care type — Other (specify) text", length=120),
        select_one("Q164_SPECIALIST",
                   "164. What kind of specialist did they recommend?",
                   Q164_SPECIALIST, length=2),
        alpha("Q164_SPECIALIST_OTHER_TXT",
              "164. Specialist — Other (specify) text", length=120),
        select_one("Q165_HOW_REFERRED",
                   "165. How did they refer you to the doctor?",
                   Q165_HOW_REFERRED, length=1),
        alpha("Q165_HOW_REFERRED_OTHER_TXT",
              "165. How referred — Other (specify) text", length=120),
        yes_no("Q166_DISCUSSED_OPTIONS",
               "166. Did they discuss with you the different places you could have gone to "
               "address your health problem?"),
        yes_no("Q167_HELPED_APPT",
               "167. Did they help you make the appointment for that visit?"),
        yes_no("Q168_WROTE_INFO",
               "168. Did they write down any information for the specialist about the reason "
               "for that visit?"),
        select_one("Q169_VISITED",
                   "169. Have you visited the referred hospital or facility after the "
                   "referral was made?", Q169_VISITED, length=1),
        yes_no("Q170_FOLLOWUP",
               "170. After your visit to the referral hospital/ specialist, did they follow "
               "up with you about what happened at the visit?"),
        *select_all("Q171_WHY_NOT",
                    "171. Why are you NOT planning to visit?",
                    Q171_WHY_NOT),
        alpha("Q171_WHY_NOT_OTHER_TXT",
              "171. Why not visit — Other (specify) text", length=120),
        yes_no("Q172_PCP_REFERRAL",
               "172. Was the visit to [facility_name_input] a referral from your primary "
               "care facility?"),
        select_one("Q173_PCP_KNOWS",
                   "173. Does your primary care provider know that you made the visit?",
                   Q173_PCP_KNOWS, length=1),
        yes_no("Q174_PCP_DISCUSSED",
               "174. Did your primary care provider discuss with you different places you "
               "could have gone to get help with your problem?"),
        yes_no("Q175_PCP_HELPED_APPT",
               "175. Did your primary care provider (PCP) or someone working with your PCP "
               "help you make the appointment for that visit?"),
        yes_no("Q176_PCP_WROTE_INFO",
               "176. Did your primary care provider write down any information for the "
               "specialist about the reason for that visit?"),
        *select_all("Q177_WHY_HOSPITAL",
                    "177. As it was not a referral, why did you decide to visit a hospital?",
                    Q177_WHY_HOSPITAL),
        alpha("Q177_WHY_HOSPITAL_OTHER_TXT",
              "177. Why hospital — Other (specify) text", length=120),
        select_one("Q178_SAT_REFERRAL",
                   "178. Overall, how would you rate your experience with the referral process?",
                   Q178_SAT_REFERRAL, length=1),
    ]
    return record("L_REFERRALS",
                  "L. Experiences and Satisfaction on Referrals", "N", items)


# ============================================================
# ASSEMBLE THE DICTIONARY
# ============================================================

def build_f3_facility_capture():
    """GPS metadata for the sampled facility (F3-side)."""
    return record(
        "REC_FACILITY_CAPTURE", "Facility GPS Capture", "Z",
        items=_gps_fields(prefix="FACILITY_"),
    )


def build_f3_patient_home_capture():
    """GPS metadata for the patient's home (distinct from facility GPS)."""
    return record(
        "REC_PATIENT_HOME_CAPTURE", "Patient Home GPS Capture", "Y",
        items=_gps_fields(prefix="P_HOME_"),
    )


def build_f3_case_verification():
    """Single verification photo per case, not per GPS block."""
    return record(
        "REC_CASE_VERIFICATION", "Case Verification Photo", "X",
        items=_photo_block(prefix=""),
    )


def build_f3_dictionary():
    # Apr 20 full rewrite complete. Per-chunk landing order (2026-04-21):
    #   Chunk 1: A, B                            (consent + patient profile)
    #   Chunk 2: C, D                            (UHC + PhilHealth)
    #   Chunk 3: E                               (primary care + YAKAP/Konsulta)
    #   Chunk 4: F, G                            (health-seeking + outpatient + BUCAS)
    #   Chunk 5: H                               (inpatient + OOP outside hospital)
    #   Chunk 6: I                               (NBB / ZBB / MAIFIP + distress)
    #   Chunk 7: J, K                            (satisfaction + meds + GAMOT)
    #   Chunk 8: L + PSGC wiring + docstring    (referrals)
    # F3_FACILITY_ID links the F3 case back to the F1 facility record (MVP analytical linkage)
    f3_facility_id_item = numeric(
        "F3_FACILITY_ID", "Sampled Facility ID (F1 linkage)",
        length=10, zero_fill=True,
    )
    records = [
        record("PATIENTSURVEY_REC", "PatientSurvey Record", "1", []),
        build_f3_field_control(),
        build_geo_id("facility_and_patient", extra_items=[f3_facility_id_item]),
        build_f3_facility_capture(),
        build_f3_patient_home_capture(),
        build_f3_case_verification(),
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
