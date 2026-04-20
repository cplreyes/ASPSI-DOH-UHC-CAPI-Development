"""
generate_dcf.py — F3 Patient Survey CSPro Data Dictionary generator.

Emits PatientSurvey.dcf in CSPro 8.0 JSON dictionary format from the
Apr 20 2026 Annex F3 questionnaire (Revised Inception Report submission,
178 numbered items across sections A–L; supersedes the Apr 08 baseline).

Staged rewrite against Apr 20:
    Old `build_section_a..l` (Apr 08 numbering Q1–Q120) remain defined
    below but are excluded from `build_f3_dictionary()` once their Apr 20
    replacement lands. See log.md entries dated 2026-04-21 for per-chunk
    progress.

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
    # Apr 20 staged rewrite — only sections already rewritten against the
    # Apr 20 questionnaire are assembled. Old Apr 08 builders remain defined
    # above for reference until their Apr 20 replacements land.
    #   Chunk 1 (2026-04-21): A, B
    #   Chunk 2 (2026-04-21): C, D
    #   Chunk 3 (2026-04-21): E
    records = [
        record("PATIENTSURVEY_REC", "PatientSurvey Record", "1", []),
        build_f3_field_control(),
        build_f3_geo_id(),
        build_section_a(),
        build_section_b(),
        build_section_c(),
        build_section_d(),
        build_section_e(),
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
