"""
generate_dcf.py — F4 Household Survey CSPro Data Dictionary generator.

Emits HouseholdSurvey.dcf in CSPro 8.0 JSON dictionary format from the
April 20 2026 Revised Inception Report submission (202 numbered items
across sections A–Q; supersedes the Apr 08 baseline).

PSGC value sets are sourced from the PSA 1Q 2026 publication, parsed once
under F1/inputs/ and shared across F-series generators.

Run:
    python generate_dcf.py        # writes HouseholdSurvey.dcf next to this file
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import (
    YES_NO, YES_NO_DK, YES_NO_NA, SATISFACTION_5PT,
    numeric, alpha, yes_no, yes_no_dk, yes_no_na,
    select_one, select_all, record, load_psgc_value_set,
    build_field_control, build_geo_id, build_dictionary, write_dcf,
)

INPUTS_DIR = Path(__file__).resolve().parent.parent / "F1" / "inputs"


# ============================================================
# FIELD CONTROL — shared + HH listing ref
# ============================================================

def build_f4_field_control():
    extra = [
        numeric("HH_LISTING_NO", "Household Listing Reference Number", length=4, zero_fill=True),
    ]
    return build_field_control(extra_items=extra, date_label_entity="the Household")


# ============================================================
# GEO ID — household mode + GPS
# ============================================================

def build_f4_geo_id():
    # PSGC value sets from PSA 1Q 2026 publication, shared with F1/F3 via
    # F1/inputs/. Length=10 retains the full PSGC code for clean crosswalk
    # to NHFR, PSA census, and DOH downstream systems. Cascading parent→child
    # dropdown filter logic belongs in CSPro PROC, not here.
    region_options       = load_psgc_value_set(INPUTS_DIR / "psgc_region.csv")
    province_huc_options = load_psgc_value_set(INPUTS_DIR / "psgc_province_huc.csv")
    city_mun_options     = load_psgc_value_set(INPUTS_DIR / "psgc_city_municipality.csv")
    barangay_options     = load_psgc_value_set(INPUTS_DIR / "psgc_barangay.csv")
    items = [
        numeric("CLASSIFICATION", "Classification", length=1, value_set_options=[
            ("UHC IS",     "1"),
            ("Non-UHC IS", "2"),
        ]),
        numeric("REGION",            "Region",              length=10, zero_fill=True, value_set_options=region_options),
        numeric("PROVINCE_HUC",      "Province / HUC",      length=10, zero_fill=True, value_set_options=province_huc_options),
        numeric("CITY_MUNICIPALITY", "City / Municipality", length=10, zero_fill=True, value_set_options=city_mun_options),
        numeric("BARANGAY",          "Barangay",            length=10, zero_fill=True, value_set_options=barangay_options),
        alpha("HH_ADDRESS", "Household Address", length=200),
        alpha("LATITUDE",   "GPS Latitude",      length=12),
        alpha("LONGITUDE",  "GPS Longitude",     length=12),
    ]
    return record("HOUSEHOLD_GEO_ID", "Household Geographic Identification", "B", items)


# ============================================================
# Section A. Introduction and Informed Consent (Q1) — Apr 20
# ============================================================

def build_section_a():
    items = [
        yes_no("Q1_IS_HH_HEAD",
               "1. Before we begin, to confirm, are you the household head?"),
    ]
    return record("A_INFORMED_CONSENT",
                  "A. Introduction and Informed Consent", "C", items)


# ============================================================
# Section B. Respondent Profile (Q2-Q29) — Apr 20
# ============================================================
# Source PDF prints Q18 (income bracket) visually out of order (after Q23).
# The DCF emits in strictly ascending Q-number order for deterministic output
# and cleaner CSPro PROC routing; this is a source-layout artifact, not a
# skip-logic signal.

def build_section_b():
    Q3_SEX = [
        ("Male",   "1"),
        ("Female", "2"),
    ]
    Q4_LGBTQIA = [
        ("Yes",                        "1"),
        ("No",                         "2"),
        ("Not Comfortable to Answer",  "3"),
        ("Don't Know",                 "4"),
        ("Refused to answer",          "5"),
    ]
    Q5_GROUP = [
        ("Lesbian",          "1"),
        ("Gay",              "2"),
        ("Bisexual",         "3"),
        ("Transgender",      "4"),
        ("Queer",            "5"),
        ("Intersex",         "6"),
        ("Asexual",          "7"),
        ("Other (specify)",  "8"),
    ]
    Q6_CIVIL_STATUS = [
        ("Single / Never Married",   "1"),
        ("Married",                  "2"),
        ("Common law / Live-in",     "3"),
        ("Widowed",                  "4"),
        ("Divorced",                 "5"),
        ("Separated",                "6"),
        ("Annulled",                 "7"),
        ("Not reported",             "8"),
    ]
    Q9_PWD_CARD = [
        ("Yes (card was presented and verified)",             "1"),
        ("No (card not available at the time of interview)",  "2"),
        ("Respondent refused to present card",                "3"),
    ]
    Q10_DISABILITY_TYPE = [
        ("Physical disability (Orthopedic)", "1"),
        ("Visual disability",                "2"),
        ("Hearing disability",               "3"),
        ("Speech impairment",                "4"),
        ("Intellectual disability",          "5"),
        ("Psychosocial disability",          "6"),
        ("Multiple disabilities",            "7"),
        ("Other disability (specify)",       "8"),
    ]
    Q11_EDUCATION = [
        ("Early Childhood Education (Pre-school)",                                                                              "01"),
        ("Primary Education (Grade 1 to 6)",                                                                                    "02"),
        ("Lower Secondary Education (Grade 7 to 10)",                                                                           "03"),
        ("Upper Secondary Education (Grade 11 to 12)",                                                                          "04"),
        ("Post-Secondary Non-Tertiary Education (including Technical and Vocational degrees with a certificate)",               "05"),
        ("Short-Cycle Tertiary Education or Equivalent (including Technical and Vocational degrees with a diploma)",            "06"),
        ("Bachelor Level Education or Equivalent",                                                                              "07"),
        ("Master Level Education or Equivalent",                                                                                "08"),
        ("Doctoral Level Education or Equivalent",                                                                              "09"),
        ("No schooling",                                                                                                        "10"),
        ("Other (specify)",                                                                                                     "11"),
        ("I don't know",                                                                                                        "98"),
        ("Not applicable",                                                                                                      "99"),
    ]
    Q12_EMPLOYMENT = [
        ("Has a permanent job/ own business",                  "1"),
        ("Has a short-term, seasonal, casual job/business",    "2"),
        ("Worked on different jobs day to day per week",       "3"),
        ("Unemployed and looking for work",                    "4"),
        ("Unemployed and not looking for work",                "5"),
        ("Retired",                                            "6"),
        ("I don't know",                                       "7"),
        ("Not applicable",                                     "9"),
    ]
    Q13_INCOME_SOURCE = [
        ("Working for private company",                        "01"),
        ("Working for private household",                      "02"),
        ("Working for government",                             "03"),
        ("Worked with pay in own family business or farm",     "04"),
        ("Self-employed without any paid employee",            "05"),
        ("Employer in own family business",                    "06"),
        ("Worked without pay in own family business or farm",  "07"),
        ("Pension",                                            "08"),
        ("Unemployed and looking for work",                    "09"),
        ("Unemployed and not looking for work",                "10"),
        ("I don't know",                                       "99"),
    ]
    Q17_DECISION_MAKER = [
        ("Me (respondent)",                "01"),
        ("My father",                      "02"),
        ("My mother",                      "03"),
        ("My parents",                     "04"),
        ("My spouse/partner",              "05"),
        ("My spouse/partner and I",        "06"),
        ("My sibling",                     "07"),
        ("My grandfather",                 "08"),
        ("My grandmother",                 "09"),
        ("My uncle",                       "10"),
        ("My aunt",                        "11"),
        ("Other (specify)",                "12"),
    ]
    Q18_BRACKET = [
        ("Under 40,000",      "1"),
        ("40,000 - 59,999",   "2"),
        ("60,000 - 99,999",   "3"),
        ("100,000 - 249,999", "4"),
        ("250,000 - 499,999", "5"),
        ("500,000 and over",  "6"),
        ("Refuse to answer",  "7"),
    ]
    Q23_WATER = [
        ("Faucet inside the house", "1"),
        ("Tubed/piped well",        "2"),
        ("Dug well",                "3"),
        ("Other (specify)",         "4"),
    ]
    Q24_OWN_SHARE = [
        ("I/we have our own",             "1"),
        ("I/we share with our community", "2"),
    ]
    Q26_HAVE = [
        ("Yes, I/ we have",     "1"),
        ("No, I/we don't have", "2"),
    ]
    Q29_SEC = [
        ("Class A or B (working professionals or with a business with several assets)",                            "1"),
        ("Class C (working professionals with permanent or semi-permanent income and some assets)",                "2"),
        ("Class D or E (semi-permanent workers or informal sector workers with little to no assets)",              "3"),
        ("I don't know",                                                                                            "4"),
    ]
    items = [
        alpha("RESPONDENT_NAME",
              "Name: (Last Name, First Name, MI, Extension)", length=120),
        numeric("Q2_BIRTH_MONTH",
                "2. In what month were you born?", length=2),
        numeric("Q2_BIRTH_YEAR",
                "2. In what year were you born?", length=4),
        numeric("Q2_1_AGE",
                "2.1 Just to confirm, how old are you as of your last birthday (in years)?",
                length=3),
        select_one("Q3_SEX", "3. What is your sex at birth?", Q3_SEX, length=1),
        select_one("Q4_LGBTQIA",
                   "4. Are you part of the LGBTQIA+ community? (e.g., gay, lesbian, bisexual, etc.). It is fine if you are not comfortable answering.",
                   Q4_LGBTQIA, length=1),
        select_one("Q5_GROUP",
                   "5. Which group do you identify with? It is fine if you are not comfortable answering.",
                   Q5_GROUP, length=1),
        alpha("Q5_GROUP_OTHER_TXT",
              "5. Group — Other (specify) text", length=120),
        select_one("Q6_CIVIL_STATUS",
                   "6. What is your civil status?", Q6_CIVIL_STATUS, length=1),
        yes_no("Q7_IS_PWD",
               "7. Do you identify as a person with a disability?"),
        yes_no("Q8_SPECIFY_DISABILITY",
               "8. Would you like to specify the type of disability?"),
        select_one("Q9_PWD_CARD",
                   "9. May we view your PWD Identification Card?",
                   Q9_PWD_CARD, length=1),
        select_one("Q10_DISABILITY_TYPE",
                   "10. Based on the presented PWD Identification Card, what type of disability is indicated?",
                   Q10_DISABILITY_TYPE, length=1),
        alpha("Q10_DISABILITY_OTHER_TXT",
              "10. Disability — Other (specify) text", length=120),
        select_one("Q11_EDUCATION",
                   "11. What is the highest level of education you have attained?",
                   Q11_EDUCATION, length=2),
        alpha("Q11_EDUCATION_OTHER_TXT",
              "11. Education — Other (specify) text", length=120),
        select_one("Q12_EMPLOYMENT",
                   "12. What is your employment status?",
                   Q12_EMPLOYMENT, length=1),
        select_one("Q13_INCOME_SOURCE",
                   "13. What is your main source of income?",
                   Q13_INCOME_SOURCE, length=2),
        yes_no("Q14_IP_MEMBER",
               "14. Are you a member of Indigenous People (IP) community, like the Igorot, Lumad, Mangyans, etc.?"),
        alpha("Q15_IP_GROUP",
              "15. If yes, which group?", length=120),
        yes_no("Q16_4PS",
               "16. Is your household a beneficiary of the Pantawid Pamilyang Pilipino Program (4Ps)?"),
        select_one("Q17_DECISION_MAKER",
                   "17. Who takes the most responsibility for making the decisions regarding healthcare in your household?",
                   Q17_DECISION_MAKER, length=2),
        alpha("Q17_DECISION_MAKER_OTHER_TXT",
              "17. Decision-maker — Other (specify) text", length=120),
        numeric("Q18_INCOME_AMOUNT",
                "18. In the past 6 months, what is your average monthly household income? Approximate amount (Philippine pesos).",
                length=9),
        select_one("Q18_INCOME_BRACKET",
                   "18. Income bracket — tick the category that corresponds to the approximate household income.",
                   Q18_BRACKET, length=1),
        numeric("Q19_HH_SIZE_TOTAL",
                "19. How many total individuals (including children) live in your house now?",
                length=3),
        numeric("Q20_HH_CHILDREN",
                "20. How many non-working age children (i.e., below the age of 18) live in your house now?",
                length=3),
        numeric("Q21_HH_SENIORS",
                "21. How many senior citizens live in your house now?",
                length=3),
        yes_no("Q22_ELECTRICITY",
               "22. Do you have electricity in your household?"),
        select_one("Q23_WATER_SOURCE",
                   "23. What is the family's main source of water supply for daily use?",
                   Q23_WATER, length=1),
        alpha("Q23_WATER_OTHER_TXT",
              "23. Water — Other (specify) text", length=120),
        select_one("Q24_FAUCET_SHARE",
                   "24. Do you have your own faucet, or do you share with your community?",
                   Q24_OWN_SHARE, length=1),
        select_one("Q25_TUBE_SHARE",
                   "25. Do you have your own tube/pipe, or do you share with your community?",
                   Q24_OWN_SHARE, length=1),
        select_one("Q26_REFRIGERATOR",
                   "26. Does the family own a refrigerator/freezer?",
                   Q26_HAVE, length=1),
        select_one("Q27_TELEVISION",
                   "27. Does the family own a television set?",
                   Q26_HAVE, length=1),
        select_one("Q28_WASHING_MACHINE",
                   "28. Does the family own a washing machine?",
                   Q26_HAVE, length=1),
        select_one("Q29_SOCIOECONOMIC_CLASS",
                   "29. How would the socioeconomic class of your household be classified?",
                   Q29_SEC, length=1),
    ]
    return record("B_RESPONDENT_PROFILE", "B. Respondent Profile", "D", items)


# ============================================================
# Section C. Household Roster and Characteristics (Q30-Q50) — Apr 20
# Per-member sub-tables C1-C5 (Q30-Q46) + private-insurance roster
# (Q48-Q50) flattened into one repeating record (max_occurs=20).
# Q47 is a single HH-level gate — emitted as a separate non-repeating
# record (type "T") so it does not disturb letters A-S already in use.
# ============================================================
# Code convention: source uses "-55" for "I don't know" (PhilHealth internal
# convention). CSPro value codes can't carry a minus sign, so we store "55".
# Source "88" ("Other (Specify)") is kept as literal "88". Both mapped below
# via the YN_DK55 and Q46_CATEGORY value sets; flag as a sanity finding for
# the F4 logic-pass spec.

def build_section_c():
    Q31_PRESENT = [
        ("Away",    "0"),
        ("Present", "1"),
    ]
    Q33_SEX = [
        ("Male",   "1"),
        ("Female", "2"),
    ]
    Q34_RELATIONSHIP = [
        ("Head",                        "01"),
        ("Spouse/Partner",              "02"),
        ("Son/Daughter",                "03"),
        ("Brother/Sister",              "04"),
        ("Son-In-Law/Daughter-In-Law",  "05"),
        ("Grandson/Granddaughter",      "06"),
        ("Father/Mother",               "07"),
        ("Nephew/Niece",                "08"),
        ("Cousin",                      "09"),
        ("Boarder",                     "10"),
        ("Domestic Helper",             "11"),
        ("Non-relative",                "12"),
    ]
    YN_01 = [
        ("No",  "0"),
        ("Yes", "1"),
    ]
    Q37_PWD_CARD = [
        ("No",                                     "0"),
        ("Yes",                                    "1"),
        ("Respondent refused to present card",     "2"),
    ]
    Q38_DISABILITY_TYPE = [
        ("Physical disability (Orthopedic)", "1"),
        ("Visual disability",                "2"),
        ("Hearing disability",               "3"),
        ("Speech impairment",                "4"),
        ("Intellectual disability",          "5"),
        ("Psychosocial disability",          "6"),
        ("Multiple disabilities",            "7"),
        ("Other disability (specify)",       "8"),
    ]
    Q39_CIVIL_STATUS = [
        ("Single / Never Married",   "1"),
        ("Married",                  "2"),
        ("Common law / Live-in",     "3"),
        ("Widowed",                  "4"),
        ("Divorced",                 "5"),
        ("Separated",                "6"),
        ("Annulled",                 "7"),
        ("Not reported",             "8"),
    ]
    Q40_EDUCATION = [
        ("Early Childhood Education (Pre-school)",                                                                            "01"),
        ("Primary Education (Grade 1 to 6)",                                                                                  "02"),
        ("Lower Secondary Education (Grade 7 to 10)",                                                                         "03"),
        ("Upper Secondary Education (Grade 11 to 12)",                                                                        "04"),
        ("Post-Secondary Non-Tertiary Education (including Technical and Vocational degrees with a certificate)",             "05"),
        ("Short-Cycle Tertiary Education or Equivalent (including Technical and Vocational degrees with a diploma)",          "06"),
        ("Bachelor Level Education or Equivalent",                                                                            "07"),
        ("Master Level Education or Equivalent",                                                                              "08"),
        ("Doctoral Level Education or Equivalent",                                                                            "09"),
        ("No schooling",                                                                                                      "10"),
    ]
    Q41_EMPLOYMENT = [
        ("Has a permanent job/ own business",                  "1"),
        ("Has a short-term, seasonal, casual job/business",    "2"),
        ("Worked on different jobs day to day per week",       "3"),
        ("Unemployed and looking for work",                    "4"),
        ("Unemployed and not looking for work",                "5"),
        ("Retired",                                            "6"),
        ("I don't know",                                       "7"),
        ("Not applicable",                                     "8"),
    ]
    # -55 (source) stored as "55" — see module-level note
    YN_DK55 = [
        ("Yes",          "01"),
        ("No",           "02"),
        ("I don't know", "55"),
    ]
    Q46_MEMBER_CATEGORY = [
        ("Formal economy",                  "01"),
        ("Informal economy",                "02"),
        ("Indigent",                        "03"),
        ("Sponsored",                       "04"),
        ("Lifetime member",                 "05"),
        ("Senior citizen",                  "06"),
        ("Overseas Filipino Worker (OFW)",  "07"),
        ("Qualified dependents",            "08"),
        ("Dependent",                       "09"),
        ("Other (Specify)",                 "88"),
        ("I don't know",                    "55"),
    ]
    items = [
        numeric("MEMBER_LINE_NO", "Household Member Line Number", length=2, zero_fill=True),
        # C1. Household Roster (Q30-Q34)
        alpha("Q30_NAME",
              "30. Name (LAST NAME, FIRST NAME & MIDDLE NAME, EXT)", length=120),
        select_one("Q31_PRESENT",
                   "31. HH member present or away", Q31_PRESENT, length=1),
        numeric("Q32_AGE",
                "32. Age (as of last birthday)", length=3),
        select_one("Q33_SEX",
                   "33. Sex at birth", Q33_SEX, length=1),
        select_one("Q34_RELATIONSHIP",
                   "34. Relationship to Household Head", Q34_RELATIONSHIP, length=2),
        # C2. Household Characteristics — disability (Q35-Q38)
        select_one("Q35_HAS_DISABILITY",
                   "35. Do you identify as a person with a disability?",
                   YN_01, length=1),
        select_one("Q36_SPECIFY_DISABILITY",
                   "36. Would you like to specify the type of disability?",
                   YN_01, length=1),
        select_one("Q37_PWD_CARD",
                   "37. May we view the patient's PWD Identification Card?",
                   Q37_PWD_CARD, length=1),
        select_one("Q38_DISABILITY_TYPE",
                   "38. Based on the presented PWD Identification Card, what type of disability is indicated?",
                   Q38_DISABILITY_TYPE, length=1),
        alpha("Q38_DISABILITY_OTHER_TXT",
              "38. Disability — Other (specify) text", length=120),
        # C3. Household Characteristics — civil/education/employment (Q39-Q41)
        select_one("Q39_CIVIL_STATUS",
                   "39. Civil Status", Q39_CIVIL_STATUS, length=1),
        select_one("Q40_EDUCATION",
                   "40. Highest level of education completed",
                   Q40_EDUCATION, length=2),
        select_one("Q41_EMPLOYMENT",
                   "41. Employment Status", Q41_EMPLOYMENT, length=1),
        # C4. Household Characteristics — social insurance (Q42-Q44)
        select_one("Q42_GSIS",
                   "42. Is (NAME) covered by GSIS either as a member or dependent?",
                   YN_DK55, length=2),
        select_one("Q43_SSS",
                   "43. Is (NAME) covered by SSS either as a member or dependent?",
                   YN_DK55, length=2),
        select_one("Q44_PAGIBIG",
                   "44. Is (NAME) covered by Pag-ibig either as a member or dependent?",
                   YN_DK55, length=2),
        # C5. Household Characteristics — PhilHealth (Q45-Q46)
        select_one("Q45_PHILHEALTH_REG",
                   "45. Currently registered with PhilHealth?",
                   YN_DK55, length=2),
        select_one("Q46_MEMBER_CATEGORY",
                   "46. What is his/her membership category? (Only answer if 'Yes' in Q45)",
                   Q46_MEMBER_CATEGORY, length=2),
        alpha("Q46_MEMBER_OTHER_TXT",
              "46. Member category — Other (specify) text", length=120),
        # Private-insurance roster columns (Q48-Q50) — gated at HH level by Q47
        alpha("Q48_NAME_FIRST",
              "48. Name (First Name Only) — private insurance roster", length=80),
        select_one("Q49_PRIVATE_INS",
                   "49. Is (NAME) covered by a private health insurance either as a member or dependent? (Example: Maxicare, Intellicare, Pacific Cross Health Care)",
                   YN_DK55, length=2),
        alpha("Q50_PRIVATE_INS_OTHER_TXT",
              "50. Others (Specify)", length=120),
    ]
    return record("C_HOUSEHOLD_ROSTER",
                  "C. Household Roster and Characteristics",
                  "E", items, max_occurs=20)


# ------------------------------------------------------------
# Q47 HH-level gate for private insurance sub-roster.
# Emitted as a separate non-repeating record (type "T") so the
# existing A-S letter sequence remains stable.
# ------------------------------------------------------------

def build_section_c_gate():
    items = [
        yes_no("Q47_HH_HAS_PRIVATE_INS",
               "47. Do you or other members of your HH have private insurance?"),
    ]
    return record("C_HH_PRIVATE_INS_GATE",
                  "C. Household Private Insurance Gate (Q47)",
                  "T", items)


# ============================================================
# Shared source-of-information value set — reused across D52, E55, F58,
# F70 (GAMOT) and similar awareness items. Identical 8-option list in
# every occurrence in the Apr 20 source.
# ============================================================
F4_INFO_SOURCE = [
    ("News",                   "1"),
    ("Legislation",            "2"),
    ("Social Media",           "3"),
    ("Friends / Family",       "4"),
    ("Health center/facility", "5"),
    ("LGU/Barangay",           "6"),
    ("I don't know",           "7"),
    ("Other (Specify)",        "8"),
]


# ============================================================
# Section D. Awareness on Universal Health Care (UHC) — Q51-Q53 — Apr 20
# ============================================================

def build_section_d():
    Q53_UNDERSTANDING = [
        ("Protection from financial risk/decreased out-of-pocket spending",       "1"),
        ("Access to quality and affordable health care goods and services",       "2"),
        ("Automatic enrollment into PhilHealth",                                  "3"),
        ("Primary care provider for every Filipino",                              "4"),
        ("I don't know",                                                          "5"),
        ("Other (Specify)",                                                       "6"),
    ]
    items = [
        yes_no("Q51_UHC_HEARD",
               "51. Have you heard about Universal Health Care (UHC) prior to this survey?"),
        *select_all("Q52_UHC_SOURCE",
                    "52. What is your source of information about UHC?",
                    F4_INFO_SOURCE),
        alpha("Q52_UHC_SOURCE_OTHER_TXT",
              "52. Source of information — Other (Specify) text", length=120),
        *select_all("Q53_UHC_UNDERSTAND",
                    "53. What is your understanding about UHC?",
                    Q53_UNDERSTANDING),
        alpha("Q53_UHC_UNDERSTAND_OTHER_TXT",
              "53. UHC understanding — Other (Specify) text", length=120),
    ]
    return record("D_UHC_AWARENESS",
                  "D. Awareness on Universal Health Care (UHC)", "F", items)


# ============================================================
# Section E. YAKAP/Konsulta Awareness — Q54-Q56 — Apr 20
# ============================================================

def build_section_e():
    Q56_UNDERSTANDING = [
        ("Free primary care consultation (with a registered YAKAP/Konsulta provider)",              "1"),
        ("Free health risk screening and assessment (with a registered YAKAP/Konsulta provider)",   "2"),
        ("Free selected laboratory / diagnostics examination",                                      "3"),
        ("Free selected drugs and medicines",                                                       "4"),
        ("There are no benefits in the package",                                                    "5"),
        ("I don't know",                                                                            "6"),
        ("Other (Specify)",                                                                         "7"),
    ]
    items = [
        yes_no("Q54_YAKAP_HEARD",
               "54. Have you heard of the term \"YAKAP/Konsulta package\"?"),
        *select_all("Q55_YAKAP_SOURCE",
                    "55. What are your sources of information about the YAKAP/Konsulta package?",
                    F4_INFO_SOURCE),
        alpha("Q55_YAKAP_SOURCE_OTHER_TXT",
              "55. Source of information — Other (Specify) text", length=120),
        *select_all("Q56_YAKAP_UNDERSTAND",
                    "56. What is your understanding about the YAKAP/Konsulta package?",
                    Q56_UNDERSTANDING),
        alpha("Q56_YAKAP_UNDERSTAND_OTHER_TXT",
              "56. YAKAP understanding — Other (Specify) text", length=120),
    ]
    return record("E_YAKAP_KONSULTA",
                  "E. YAKAP/Konsulta Awareness", "G", items)


# ============================================================
# Section F. BUCAS Awareness and Utilization — Q57-Q61 — Apr 20
# Expanded per Annex G#1 (BUCAS/PuroKalusugan/ZBB coverage woven
# through household survey). Q57-Q61 applicable only to respondents
# in areas with BUCAS; otherwise proceed to Q62.
# ============================================================

def build_section_f():
    Q59_UNDERSTANDING = [
        ("Provides urgent care for non-life-threatening/serious conditions",   "1"),
        ("Offers outpatient and ambulatory health services",                   "2"),
        ("Helps reduce overcrowding in hospitals",                             "3"),
        ("Allows access to timely medical consultation and treatment",         "4"),
        ("Other (specify)",                                                    "5"),
    ]
    Q61_SERVICES = [
        ("Medical consultation for urgent or minor conditions",        "1"),
        ("Outpatient or ambulatory care services",                     "2"),
        ("Basic diagnostic services (e.g., laboratory tests, X-ray)",  "3"),
        ("Minor procedures or treatments",                             "4"),
        ("Referral to higher-level health facilities",                 "5"),
        ("I don't know",                                               "6"),
        ("Other (specify)",                                            "7"),
    ]
    items = [
        yes_no("Q57_BUCAS_HEARD",
               "57. Have you heard about Bagong Urgent Care and Ambulatory Service (BUCAS) center?"),
        *select_all("Q58_BUCAS_SOURCE",
                    "58. If yes, what are your sources of information about this BUCAS center?",
                    F4_INFO_SOURCE),
        alpha("Q58_BUCAS_SOURCE_OTHER_TXT",
              "58. BUCAS source — Other (Specify) text", length=120),
        *select_all("Q59_BUCAS_UNDERSTAND",
                    "59. What is your understanding about a BUCAS center?",
                    Q59_UNDERSTANDING),
        alpha("Q59_BUCAS_UNDERSTAND_OTHER_TXT",
              "59. BUCAS understanding — Other (specify) text", length=120),
        yes_no("Q60_BUCAS_ACCESSED",
               "60. In the last six months, did you or any member of your HH accessed the services in a BUCAS center?"),
        *select_all("Q61_BUCAS_SERVICES",
                    "61. If yes, which of the services did you avail?",
                    Q61_SERVICES),
        alpha("Q61_BUCAS_SERVICES_OTHER_TXT",
              "61. BUCAS services — Other (specify) text", length=120),
    ]
    return record("F_BUCAS_AWARENESS",
                  "F. Bagong Urgent Care and Ambulatory Service (BUCAS) Awareness and Utilization",
                  "H", items)


# ============================================================
# Section G. Access to Medicines — Q62-Q78 — Apr 20
# Covers HH medicine purchase behavior (Q62-Q68), GAMOT awareness and
# utilization (Q69-Q74), and branded-vs-generic reasoning (Q75-Q78).
# GAMOT sub-block (Q69-Q74, Q76) applies only to respondents in areas
# with GAMOT; otherwise proceed to Q79.
# ============================================================

def build_section_g():
    Q62_FREQUENCY = [
        ("Weekly",     "1"),
        ("Bi-weekly",  "2"),
        ("Monthly",    "3"),
        ("Rarely",     "4"),
        ("Never",      "5"),  # proceed to Q69
    ]
    Q63_PRESCRIPTION = [
        ("Prescribed by a doctor",                             "1"),
        ("Over-the-counter medicine",                          "2"),
        ("Purchased both prescribed medicine and OTC medicine","3"),
        ("I don't know",                                       "4"),
    ]
    Q65_CONDITIONS = [
        ("Upper respiratory infection",                         "01"),
        ("Hypertension",                                        "02"),
        ("Immunization",                                        "03"),
        ("Pregnancy or birth",                                  "04"),
        ("Flu",                                                 "05"),
        ("Fever",                                               "06"),
        ("Joint and muscle pain",                               "07"),
        ("Asthma or COPD (chronic breathing problem, not cancer)", "08"),
        ("Diabetes",                                            "09"),
        ("Heart problem",                                       "10"),
        ("Kidney problem / Dialysis",                           "11"),
        ("Cancer (any)",                                        "12"),
        ("Gastro problem (vomiting, diarrhea, etc.)",           "13"),
        ("Other infection (e.g. urine, skin, other virus etc.)","14"),
        ("Accident/injury (e.g. wound/broken bone)",            "15"),
        ("Dental",                                              "16"),
        ("ENT (problem with ear/nose/throat)",                  "17"),
        ("Allergy",                                             "18"),
        ("No condition - Regular check-up only",                "19"),
        ("Other (Specify)",                                     "20"),
    ]
    Q66_WHERE_BUY = [
        ("Public Hospital",                                     "1"),
        ("Private Hospital",                                    "2"),
        ("Chain Pharmacies (e.g. Mercury Drug, Watsons, TGP, Generika)", "3"),
        ("Local pharmacies",                                    "4"),
        ("Online stores (e.g. Shopee, Lazada)",                 "5"),
        ("Barangay Health Station",                             "6"),
        ("Rural Health Unit or City Health Office",             "7"),
        ("Other (specify)",                                     "8"),
    ]
    Q68_EASE = [
        ("Very difficult", "1"),
        ("Difficult",      "2"),
        ("Neutral",        "3"),
        ("Easy",            "4"),
        ("Very easy",       "5"),
    ]
    Q71_UNDERSTANDING = [
        ("Provides free or affordable medicines for outpatients",      "1"),
        ("Ensures continuous availability of essential medicines",     "2"),
        ("Helps reduce out-of-pocket expenses for medicines",          "3"),
        ("Supports treatment of common illnesses and chronic conditions","4"),
        ("I don't know",                                               "5"),
        ("Other (specify)",                                            "6"),
    ]
    Q74_WHERE_REST = [
        ("Purchased from pharmacy",                   "01"),
        ("Purchased from public hospital",            "02"),
        ("Purchased from private hospital",           "03"),
        ("Purchased from primary care provider (PCP)","04"),
        ("Received from PCP for free",                "05"),
        ("Received from LGU for free",                "06"),
        ("Received from public hospital for free",    "07"),
        ("Received from private hospital for free",   "08"),
        ("Not applicable",                            "09"),
        ("Other (Specify)",                           "10"),
    ]
    Q76_BRAND_OR_GEN = [
        ("Branded",                        "1"),  # proceed to Q78
        ("Generic",                        "2"),
        ("Both branded and generic",       "3"),
        ("Don't know the difference",      "4"),  # proceed to Q79
        ("Not applicable",                 "9"),  # proceed to Q79
    ]
    Q77_WHY_GENERIC = [
        ("Lower cost",                                 "1"),
        ("Prescribed by doctor",                       "2"),
        ("Readily available",                          "3"),
        ("Given for free",                             "4"),
        ("More or as effective as branded medicine",   "5"),
        ("I don't know",                               "6"),
        ("Not applicable",                             "7"),
        ("Other (Specify)",                            "8"),
    ]
    Q78_WHY_BRANDED = [
        ("Branded medicine is more effective than generic", "1"),
        ("Not aware of generic option",                     "2"),
        ("Prescribed by doctor",                            "3"),
        ("Given for free",                                  "4"),
        ("Prefer branded over generic option",              "5"),
        ("I don't know",                                    "6"),
        ("Not applicable",                                  "7"),
        ("Other (Specify)",                                 "8"),
    ]
    items = [
        select_one("Q62_PURCHASE_FREQ",
                   "62. How often do you purchase or receive medicines?",
                   Q62_FREQUENCY, length=1),
        select_one("Q63_PRESCRIPTION_TYPE",
                   "63. Was the most recent medicine purchased prescribed by a doctor or over-the-counter (OTC) medicine (no need for a prescription)?",
                   Q63_PRESCRIPTION, length=1),
        alpha("Q64_MEDICATIONS_LIST",
              "64. What are the medications that you or any member of your household usually take? (List all medicines taken for the health condition.)",
              length=500),
        *select_all("Q65_CONDITIONS",
                    "65. What are the medical conditions that you/your household member/s take the medicine/s for?",
                    Q65_CONDITIONS),
        alpha("Q65_CONDITIONS_OTHER_TXT",
              "65. Conditions — Other (Specify) text", length=120),
        *select_all("Q66_WHERE_BUY",
                    "66. Where do you usually buy or receive your medicines?",
                    Q66_WHERE_BUY),
        alpha("Q66_WHERE_BUY_OTHER_TXT",
              "66. Where buy — Other (specify) text", length=120),
        numeric("Q67_TIME_TO_PHARMACY",
                "67. How much time does it take for you to reach the nearest pharmacy from your home? (HHMM)",
                length=4),
        select_one("Q68_PHARMACY_ACCESS",
                   "68. How easy is it for you to access a pharmacy or drugstore?",
                   Q68_EASE, length=1),
        # GAMOT sub-block (Q69-Q74, Q76) — applies only in GAMOT areas
        yes_no("Q69_GAMOT_HEARD",
               "69. Have you heard of the Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT) Package, which is part of PhilHealth's YAKAP/Konsulta or primary care benefit package?"),
        *select_all("Q70_GAMOT_SOURCE",
                    "70. If yes, what are your sources of information for GAMOT Package?",
                    F4_INFO_SOURCE),
        alpha("Q70_GAMOT_SOURCE_OTHER_TXT",
              "70. GAMOT source — Other (Specify) text", length=120),
        *select_all("Q71_GAMOT_UNDERSTAND",
                    "71. What is your understanding of the GAMOT Package?",
                    Q71_UNDERSTANDING),
        alpha("Q71_GAMOT_UNDERSTAND_OTHER_TXT",
              "71. GAMOT understanding — Other (specify) text", length=120),
        yes_no("Q72_GAMOT_OBTAINED",
               "72. Did you get the medicines from the GAMOT Package during the past 6 months?"),
        alpha("Q73_GAMOT_MEDS_LIST",
              "73. What are the medications that you obtained from the GAMOT Package? [LIST]",
              length=500),
        *select_all("Q74_WHERE_REST",
                    "74. Where did you get the rest of the medicines?",
                    Q74_WHERE_REST),
        alpha("Q74_WHERE_REST_OTHER_TXT",
              "74. Where rest — Other (Specify) text", length=120),
        yes_no("Q75_BRAND_GEN_KNOWS",
               "75. Do you know the difference between a 'branded' and a 'generic' medicine?"),
        select_one("Q76_BRAND_OR_GEN",
                   "76. Was/were the medicine/s you bought outside of GAMOT pharmacy branded or generic?",
                   Q76_BRAND_OR_GEN, length=1),
        *select_all("Q77_WHY_GENERIC",
                    "77. If generic, why did you buy generic medicine?",
                    Q77_WHY_GENERIC),
        alpha("Q77_WHY_GENERIC_OTHER_TXT",
              "77. Generic reason — Other (Specify) text", length=120),
        *select_all("Q78_WHY_BRANDED",
                    "78. If branded, why did you buy branded medicine? (Ask if answer in Q76 is branded and both branded and generic, otherwise skip.)",
                    Q78_WHY_BRANDED),
        alpha("Q78_WHY_BRANDED_OTHER_TXT",
              "78. Branded reason — Other (Specify) text", length=120),
    ]
    return record("G_ACCESS_MEDICINES", "G. Access to Medicines", "I", items)


# ============================================================
# Section H. PhilHealth Registration and Health Insurance — Q79-Q88 — Apr 20
# Respondent-level (non-repeating); gated by respondent's Q45 in Section C.
# Apr 08 had max_occurs=20 (per-member); Apr 20 source explicitly states
# "Q79 to Q88 if the respondent is registered with PhilHealth in Q45" —
# asked once of the main respondent, not roster-repeating. (Annex G#4)
# ============================================================

def build_section_h():
    Q79_REG_SOURCE = [
        ("PhilHealth representative",  "01"),
        ("LGU",                        "02"),
        ("Primary care provider",      "03"),
        ("Other health care provider", "04"),
        ("Employer",                   "05"),
        ("No one / self-registered",   "06"),
        ("Barangay Health Worker",     "07"),
        ("Friends / Family",           "08"),
        ("Health center/facility",     "09"),
        ("Other (Specify)",            "10"),
    ]
    Q82_DIFFICULTY_REASONS = [
        ("Unclear process",                                 "1"),
        ("Took a long time",                                "2"),
        ("Did not know where to ask for help",              "3"),
        ("Had to travel a long way",                        "4"),
        ("No valid ID",                                     "5"),
        ("Did not know the required documents to register", "6"),
        ("I don't know",                                    "7"),
        ("Other (Specify)",                                 "8"),
    ]
    Q85_BENEFITS = [
        ("No balance billing for basic ward accommodation",  "1"),
        ("Subsidized inpatient services",                    "2"),
        ("Subsidized outpatient services",                   "3"),
        ("There are no benefits to being a member",          "4"),
        ("I don't know",                                     "5"),
        ("Other (Specify)",                                  "6"),
    ]
    Q86_PREMIUM_PAY = [
        ("Yes, I pay directly",      "1"),
        ("Yes, my employer pays",    "2"),
        ("No, I do not pay premiums","3"),
    ]
    Q88_DIFF_PAYING = [
        ("Cannot afford the premium",                       "1"),
        ("Payment options are inconvenient",                "2"),
        ("No time to pay",                                  "3"),
        ("Don't see value in paying",                       "4"),
        ("System of PhilHealth is unreliable/usually down", "5"),
        ("I don't know",                                    "6"),
        ("Other (Specify)",                                 "7"),
    ]
    items = [
        select_one("Q79_REG_SOURCE",
                   "79. How did you find out about how to register to PhilHealth?",
                   Q79_REG_SOURCE, length=2),
        alpha("Q79_REG_SOURCE_OTHER_TXT",
              "79. Registration source — Other (Specify) text", length=120),
        select_one("Q80_ASSIST",
                   "80. Who assisted you in the registration process?",
                   Q79_REG_SOURCE, length=2),
        alpha("Q80_ASSIST_OTHER_TXT",
              "80. Registration assistant — Other (Specify) text", length=120),
        yes_no("Q81_REG_DIFFICULTY",
               "81. Did you have any difficulties in the registration process?"),
        *select_all("Q82_DIFFICULTY_REASONS",
                    "82. What did you find difficult about the process?",
                    Q82_DIFFICULTY_REASONS),
        alpha("Q82_DIFFICULTY_OTHER_TXT",
              "82. Difficulty — Other (Specify) text", length=120),
        yes_no("Q83_KNOWS_ASSIST",
               "83. Would you know where to go to seek assistance in registration?"),
        alpha("Q84_WHERE_ASSIST",
              "84. Where would you go to seek assistance?", length=200),
        *select_all("Q85_BENEFITS",
                    "85. What are some of the benefits that come with being a PhilHealth member?",
                    Q85_BENEFITS),
        alpha("Q85_BENEFITS_OTHER_TXT",
              "85. Benefits — Other (Specify) text", length=120),
        select_one("Q86_PREMIUM_PAY",
                   "86. Do you and members of your HH pay PhilHealth premiums every month?",
                   Q86_PREMIUM_PAY, length=1),
        yes_no("Q87_PREMIUM_DIFFICULT",
               "87. Do you find it difficult to pay the PhilHealth premiums every month?"),
        *select_all("Q88_DIFF_PAYING",
                    "88. Why did you find it difficult?",
                    Q88_DIFF_PAYING),
        alpha("Q88_DIFF_PAYING_OTHER_TXT",
              "88. Difficulty paying — Other (Specify) text", length=120),
    ]
    return record("H_PHILHEALTH_REG",
                  "H. PhilHealth Registration and Health Insurance",
                  "J", items)


# ============================================================
# Section I. Primary Care Utilization (Q89-Q100)
# Skip logic (logic-pass phase): Q89 No→Q93, Q89 IDK→Q93 (no usual facility);
# Q90 No→Q96 (bypass Q91 "why-went"); Q93 only when Q89!=Yes.
# ============================================================

def build_section_i():
    Q91_WHY_WENT = [
        ("This facility is more accessible than my usual facility (i.e., nearer, has more transportation options to get to, and cheaper to travel to)", "1"),
        ("Needed a service/specialist not available at my usual facility", "2"),
        ("Recommended by friends/family",                                  "3"),
        ("Wanted to try another facility than my usual",                   "4"),
        ("Prefer this facility than my usual",                             "5"),
        ("This was referred to me by my usual facility",                   "6"),
        ("Usual facility is closed for today",                             "7"),
        ("The doctor I trust/familiar with transferred in this facility",  "8"),
        ("Other (Specify)",                                                "9"),
    ]
    Q92_FACILITY_TYPE = [
        ("YAKAP/Konsulta or primary care provider",     "01"),
        ("Barangay Health Center",                      "02"),
        ("Rural Health Unit / Health Center",           "03"),
        ("Public Hospital",                             "04"),
        ("Private Hospital",                            "05"),
        ("Private Clinic",                              "06"),
        ("Traditional Healer or Manghihilot/Albularyo", "07"),
        ("I don't know",                                "08"),
        ("Other (Specify)",                             "09"),
    ]
    Q93_WHY_NOT = [
        ("I don't get sick",                "1"),
        ("I recently moved into the area",  "2"),
        ("It's expensive",                  "3"),
        ("I can treat myself",              "4"),
        ("I don't know where to go for care","5"),
        ("I don't know",                    "6"),
        ("Other (Specify)",                 "7"),
    ]
    Q94_TRANSPORT = [
        ("Walk",                             "01"),
        ("Bike",                             "02"),
        ("Public Bus",                       "03"),
        ("Jeepney",                          "04"),
        ("Tricycle",                         "05"),
        ("Car (including private taxi/cab)", "06"),
        ("Motorcycle",                       "07"),
        ("Boat",                             "08"),
        ("Taxi",                             "09"),
        ("Pedicab",                          "10"),
        ("E-bike",                           "11"),
        ("Other (Specify)",                  "12"),
    ]
    Q98_99_PHONE = [
        ("Yes",             "1"),
        ("No",              "2"),
        ("I haven't tried", "3"),
        ("I don't know",    "4"),
    ]
    Q100_LEAVE = [
        ("Yes",             "1"),
        ("No",              "2"),
        ("I haven't tried", "3"),
        ("I don't know",    "4"),
        ("Not applicable",  "9"),
    ]
    items = [
        yes_no_dk("Q89_HAS_USUAL_FACILITY",
                  "89. In the past 12 months, do you have a clinic, or health center that you usually go to?"),
        alpha("Q89_1_FACILITY_NAME",
              "89.1. What is the name of the facility?", length=120),
        yes_no("Q90_IS_USUAL_FOR_GENERAL",
               "90. Is this the facility you usually go to for general health concerns?"),
        *select_all("Q91_WHY_WENT",
                    "91. Why did you go to this facility?",
                    Q91_WHY_WENT),
        alpha("Q91_WHY_WENT_OTHER_TXT",
              "91. Why did you go to this facility — Other (Specify) text", length=120),
        select_one("Q92_FACILITY_TYPE",
                   "92. What is the type of facility that you usually go to?",
                   Q92_FACILITY_TYPE, length=2),
        alpha("Q92_FACILITY_TYPE_OTHER_TXT",
              "92. Type of facility — Other (specify) text", length=120),
        *select_all("Q93_WHY_NOT",
                    "93. If not, why do you not have a usual clinic, or health center that you usually go to?",
                    Q93_WHY_NOT),
        alpha("Q93_WHY_NOT_OTHER_TXT",
              "93. Why no usual facility — Other (Specify) text", length=120),
        *select_all("Q94_TRANSPORT",
                    "94. What mode/s of transportation do you use when travelling to the nearest primary care facility?",
                    Q94_TRANSPORT),
        alpha("Q94_TRANSPORT_OTHER_TXT",
              "94. Transportation mode — Other (Specify) text", length=120),
        numeric("Q95_TRAVEL_TIME_MIN",
                "95. How long does it take you to travel from your house when going to the nearest primary care facility? (one-way, minutes)",
                length=3),
        numeric("Q96_TRAVEL_COST_PHP",
                "96. How much does it usually cost for you to travel to this facility from your home? (PHP, one-way)",
                length=5),
        yes_no("Q97_KNOWS_BOOKING",
               "97. When you have a health problem, do you know how to book an appointment at a primary care facility?"),
        select_one("Q98_PHONE_ADVICE_OPEN",
                   "98. When your primary care facility is open, can you get advice quickly over the phone if you need it?",
                   Q98_99_PHONE, length=1),
        select_one("Q99_PHONE_ADVICE_CLOSED",
                   "99. When your primary care facility is closed, is there a phone number you can call when you get sick?",
                   Q98_99_PHONE, length=1),
        select_one("Q100_LEAVE_WORK_SCHOOL",
                   "100. When you have to visit your primary care facility, do you have to take a leave from work or school to go?",
                   Q100_LEAVE, length=1),
    ]
    return record("I_PRIMARY_CARE",
                  "I. Primary Care Utilization", "K", items)


# ============================================================
# Section J. Household members' Health-Seeking Behavior and Outcomes (Q101-Q107)
# Apr 20 source: singular "you/your household member" — respondent-level, NOT
# per-member repeating (downgraded from Apr 08 max_occurs=20 structure).
# Skip logic (logic-pass phase): Q105 No→Q107 (bypass Q106 "why-not").
# ============================================================

def build_section_j():
    Q101_CHECKUP_FREQ = [
        ("More than once a year",                                         "1"),
        ("Every year",                                                    "2"),
        ("Every 2-3 years",                                               "3"),
        ("Every 4-5 years",                                               "4"),
        ("No set time; I've only ever done this once or twice in my life","5"),
        ("Never; I only go to the doctor when I am sick",                 "6"),
        ("Other (Specify)",                                               "7"),
    ]
    Q102_VISIT_REASON = [
        ("Consultation for new health problem",                  "1"),
        ("Consultation to follow-up an ongoing health problem",  "2"),
        ("For tests/diagnostics only",                           "3"),
        ("For a general check-up",                               "4"),
        ("To get a health certificate/administrative reason",    "5"),
        ("For immunizations/vaccinations",                       "6"),
        ("My doctor transferred to this health facility",        "7"),
        ("Other (Specify)",                                      "8"),
    ]
    Q103_CARE_TYPE = [
        ("Outpatient care (Consultation, procedure, or treatment where the patient visits and leaves within the same day)",       "1"),
        ("Inpatient care (Care provided in hospital or another facility where the patient is admitted for at least one night)",  "2"),
        ("Emergency care (Care for serious illnesses or injuries that need immediate medical attention; usually provided in an emergency room or ER)", "3"),
        ("Primary care consultation", "4"),
        ("Other (Specify)",           "5"),
    ]
    Q106_FORGONE_WHY = [
        ("Not sick enough",                        "1"),
        ("It's too expensive",                     "2"),
        ("Could not take time off work",           "3"),
        ("Could not get an appointment soon enough","4"),
        ("No transportation available",            "5"),
        ("Afraid to know my illness",              "6"),
        ("I don't know",                           "7"),
        ("Other (Specify)",                        "8"),
    ]
    Q107_ACTIONS = [
        ("Visited other healthcare facility",                                                                                            "1"),
        ("Sought alternative care (Healthcare apart from medical doctors or the formal healthcare system; such as reflexology, acupuncture, massage therapy, herbal medicines, etc.)", "2"),
        ("Sought telemedicine (Remote diagnosis and treatment of patients by means of telecommunications technology)",                   "3"),
        ("Used home care (Healthcare services and support provided to individuals in their own homes)",                                  "4"),
        ("Bought medicine from a pharmacy",                                                                                              "5"),
        ("Did not seek other forms of care",                                                                                             "6"),
        ("Other (Specify)",                                                                                                              "7"),
    ]
    items = [
        select_one("Q101_CHECKUP_FREQ",
                   "101. How often do you/your household member have a general check-up on your health (i.e., when you feel healthy, without any specific illness)?",
                   Q101_CHECKUP_FREQ, length=1),
        alpha("Q101_CHECKUP_FREQ_OTHER_TXT",
              "101. Checkup frequency — Other (Specify) text", length=120),
        *select_all("Q102_VISIT_REASON",
                    "102. What best describes why you/your household member will visit a health facility (e.g. RHU, health center, clinic, hospital)?",
                    Q102_VISIT_REASON),
        alpha("Q102_VISIT_REASON_OTHER_TXT",
              "102. Visit reason — Other (Specify) text", length=120),
        *select_all("Q103_CARE_TYPE",
                    "103. Have you accessed any of the following forms of care in the last 6 months?",
                    Q103_CARE_TYPE),
        alpha("Q103_CARE_TYPE_OTHER_TXT",
              "103. Forms of care — Other (Specify) text", length=120),
        yes_no("Q104_PREVENTIVE",
               "104. Have you ever consulted a physician for preventative reasons, such as to consult about your lifestyle, weight loss, stopping smoking, etc.?"),
        yes_no("Q105_FORGONE_CARE",
               "105. In the last 6 months, have you or any of your household members had a medical problem and chosen NOT to see a healthcare provider?"),
        *select_all("Q106_FORGONE_WHY",
                    "106. Why not?",
                    Q106_FORGONE_WHY),
        alpha("Q106_FORGONE_WHY_OTHER_TXT",
              "106. Why forgone — Other (Specify) text", length=120),
        *select_all("Q107_OTHER_ACTIONS",
                    "107. Did you or your household members do any other actions to improve your/their health condition or address your/their health concern?",
                    Q107_ACTIONS),
        alpha("Q107_OTHER_ACTIONS_OTHER_TXT",
              "107. Other actions — Other (Specify) text", length=120),
    ]
    return record("J_HEALTH_SEEKING",
                  "J. Household Members' Health-Seeking Behavior and Outcomes",
                  "L", items)


# ============================================================
# Section K. Experiences and Satisfaction with Referrals (Q108-Q125)
# Skip logic (logic-pass phase):
# - Q108 No → Q126 (skip entire K section)
# - Q112 Yes → Q114; Q112 No (not planning) → Q113; Q112 Not yet → Q114
# - Q117, Q118 only when Q112=Yes
# - Q119 No → Q121 (bypass Q120)
# ============================================================

# 6-option satisfaction scale with Not applicable (Q118, Q125 Apr 20).
SATISFACTION_6PT_NA = [
    ("Very Satisfied",                     "1"),
    ("Satisfied",                          "2"),
    ("Neither Satisfied nor Dissatisfied", "3"),
    ("Dissatisfied",                       "4"),
    ("Very Dissatisfied",                  "5"),
    ("Not applicable",                     "9"),
]

def build_section_k():
    Q109_TYPE = [
        ("Outpatient care (Consultation, procedure, or treatment where the patient visits and leaves within the same day)", "01"),
        ("Emergency care (Care for serious illnesses or injuries that need immediate medical attention; usually provided in an emergency room or ER)", "02"),
        ("Inpatient care (Care provided in hospital or another facility where the patient is admitted for at least one night)", "03"),
        ("Dental care (Medical care for your teeth, such as cleanings, fillings, etc.)", "04"),
        ("Other facility visits (Care that is provided in a facility that is not a health center or hospital, such as independent diagnostic centers, TB dispensaries, etc.)", "05"),
        ("Special therapy visits (Rehabilitation care or services, such as occupational therapy, physical therapy, psychological and behavioral rehabilitation, prosthetics and orthotics rehabilitation, or speech and language therapy)", "06"),
        ("Alternative care (Healthcare apart from medical doctors or the formal health care system; such as reflexology, acupuncture, massage therapy, herbal medicines, etc.)", "07"),
        ("Outreach / medical missions (Care provided by the government or an NGO through an outreach or medical mission within a community)", "08"),
        ("Home healthcare (Care that is administered at the patient's home, such as birth delivery, checkups, immunization, rehabilitation, etc.)", "09"),
        ("Telemedicine (Remote diagnosis and treatment of patients by means of telecommunications technology)", "10"),
        ("None of the above", "11"),
        ("Other (Specify)",   "12"),
    ]
    Q110_SPECIALIST = [
        ("No specialty",                          "01"),
        ("Anesthesia",                            "02"),
        ("Dermatology",                           "03"),
        ("Emergency Medicine",                    "04"),
        ("Family Medicine",                       "05"),
        ("General Surgery",                       "06"),
        ("Internal Medicine",                     "07"),
        ("Neurology",                             "08"),
        ("Nuclear Medicine",                      "09"),
        ("Obstetrics and Gynecology",             "10"),
        ("Occupational Medicine",                 "11"),
        ("Ophthalmology",                         "12"),
        ("Orthopedics",                           "13"),
        ("Otorhinolaryngology (ENT)",             "14"),
        ("Pathology",                             "15"),
        ("Pediatrics",                            "16"),
        ("Physical and Rehabilitation Medicine",  "17"),
        ("Psychiatry",                            "18"),
        ("Public health",                         "19"),
        ("Radiology",                             "20"),
        ("Research",                              "21"),
        ("I don't know",                          "22"),
        ("Other (Specify)",                       "23"),
    ]
    Q111_METHOD = [
        ("Physical referral slip",                                      "1"),
        ("E-referral",                                                  "2"),
        ("Phone call from referring facility to receiving facility",    "3"),
        ("I don't know",                                                "4"),
        ("Other (Specify)",                                             "5"),
    ]
    Q112_VISIT = [
        ("Yes",                          "1"),
        ("No, I'm not planning to",      "2"),
        ("Not yet, but I'm planning to", "3"),
    ]
    Q113_WHY_NOT = [
        ("Facility is too far",                    "1"),
        ("Do not trust the referred facility",     "2"),
        ("No time",                                "3"),
        ("Worried about additional costs",         "4"),
        ("Not needed",                             "5"),
        ("Don't know how to get to facility",      "6"),
        ("Other (Specify)",                        "7"),
    ]
    Q121_WHY_HOSPITAL = [
        ("Referred by other specialist (doctor in another hospital)",                     "1"),
        ("Nearest facility to house",                                                     "2"),
        ("Facility is usual source of care",                                              "3"),
        ("Facility is the only place that can perform a certain test",                    "4"),
        ("Referred by BHW/nurse/midwife/other community health professional",             "5"),
        ("Referred by family / friends",                                                  "6"),
        ("Facility offers subsidized or free health services",                            "7"),
        ("I don't know",                                                                  "8"),
        ("Other (Specify)",                                                               "9"),
    ]
    items = [
        yes_no("Q108_REFERRED",
               "108. In the past 6 months, did a healthcare worker refer you to another facility or specialist for further care or specialized care?"),
        *select_all("Q109_TYPE",
                    "109. What type of care was the referral for?",
                    Q109_TYPE),
        alpha("Q109_TYPE_OTHER_TXT",
              "109. Referral care type — Other (Specify) text", length=120),
        select_one("Q110_SPECIALIST",
                   "110. What kind of specialist did they recommend?",
                   Q110_SPECIALIST, length=2),
        alpha("Q110_SPECIALIST_OTHER_TXT",
              "110. Specialist — Other (Specify) text", length=120),
        select_one("Q111_METHOD",
                   "111. How did they refer you to the doctor?",
                   Q111_METHOD, length=1),
        alpha("Q111_METHOD_OTHER_TXT",
              "111. Referral method — Other (Specify) text", length=120),
        select_one("Q112_VISITED",
                   "112. Did you visit another facility after the referral?",
                   Q112_VISIT, length=1),
        *select_all("Q113_WHY_NOT",
                    "113. Why are you not planning to visit?",
                    Q113_WHY_NOT),
        alpha("Q113_WHY_NOT_OTHER_TXT",
              "113. Why not planning to visit — Other (Specify) text", length=120),
        yes_no("Q114_DISCUSSED_PLACES",
               "114. Did they discuss with you the different places you could have gone to get help with your problem?"),
        yes_no("Q115_HELPED_APPT",
               "115. Did they help you make the appointment for that visit?"),
        yes_no("Q116_WROTE_INFO",
               "116. Did they write down any information for the specialist about the reason for that visit?"),
        yes_no("Q117_SPECIALIST_FOLLOWUP",
               "117. After you went to the specialist or special service, did they follow up with you about what happened at the visit? (Only if Q112=Yes)"),
        select_one("Q118_SAT_REFERRAL_PROCESS",
                   "118. Overall, how would you rate your satisfaction with the referral process? (Only if Q112=Yes)",
                   SATISFACTION_6PT_NA, length=1),
        yes_no("Q119_PCF_REFERRAL",
               "119. Was the visit to the facility a referral from your primary care facility?"),
        yes_no_dk("Q120_PCP_KNOWS",
                  "120. Does your primary care provider know that you made the visit?"),
        *select_all("Q121_WHY_HOSPITAL",
                    "121. As it was not a referral, why did you decide to visit a hospital?",
                    Q121_WHY_HOSPITAL),
        alpha("Q121_WHY_HOSPITAL_OTHER_TXT",
              "121. Why visit hospital — Other (Specify) text", length=120),
        yes_no("Q122_PCP_DISCUSSED_PLACES",
               "122. Did your primary care provider discuss with you different places you could have gone to get help with your problem?"),
        yes_no("Q123_PCP_HELPED_APPT",
               "123. Did your primary care provider (PCP) or someone working with your PCP help you make the appointment for that visit?"),
        yes_no("Q124_PCP_WROTE_INFO",
               "124. Did your primary care provider write down any information for the specialist about the reason for that visit?"),
        select_one("Q125_SAT_REFERRAL_EXP",
                   "125. Overall, how would you rate your experience with the referral process?",
                   SATISFACTION_6PT_NA, length=1),
    ]
    return record("K_REFERRALS",
                  "K. Experiences and Satisfaction with Referrals",
                  "M", items)


# ============================================================
# Sections L/M shared value sets (NBB, ZBB, MAIFIP — identical structures)
# ============================================================

NBB_ZBB_MAIFIP_INFO_SOURCE = [
    ("News",                   "1"),
    ("Legislation",            "2"),
    ("Social Media",           "3"),
    ("Friends / Family",       "4"),
    ("Health center/facility", "5"),
    ("LGU/Barangay",           "6"),
    ("I don't know",           "7"),
    ("Other (Specify)",        "8"),
]

# Source order preserved verbatim from Apr 20 Q128/Q134 (9 options, read in
# two columns left-then-right per PDF layout).
NBB_ZBB_UNDERSTANDING = [
    ("Patient does not pay any hospital bill",              "1"),
    ("Bills are settled between the hospital and PhilHealth","2"),
    ("PhilHealth will cover cost of treatment",             "3"),
    ("Patients should not be charged extra fees",           "4"),
    ("Medicine and service are already included",           "5"),
    ("I don't know",                                        "6"),
    ("No cash payment required upon discharge",             "7"),
    ("Other (Specify)",                                     "8"),
    ("Applies only to certain patients or hospitals",       "9"),
]


# ============================================================
# Section L. No Balance Billing (NBB) Awareness and Utilization (Q126-Q131)
# Skip logic (logic-pass phase):
# - Q126 No/IDK → Q132 (skip to Section M)
# - Q129 No/IDK → Q132
# - Q130 Public or Private → Q132 (bypass Q131; Q131 only for DOH-retained)
# ============================================================

def build_section_l():
    Q130_HOSPITAL_TYPE = [
        ("Public",                                            "1"),
        ("DOH-retained hospital (sub-type of public hospital)","2"),
        ("Private",                                           "3"),
    ]
    items = [
        yes_no_dk("Q126_NBB_HEARD",
                  "126. Have you heard of the No Balance Billing (NBB)?"),
        *select_all("Q127_NBB_SOURCE",
                    "127. If yes, what are your sources of information about NBB?",
                    NBB_ZBB_MAIFIP_INFO_SOURCE),
        alpha("Q127_NBB_SOURCE_OTHER_TXT",
              "127. NBB info source — Other (Specify) text", length=120),
        *select_all("Q128_NBB_UNDERSTAND",
                    "128. What is your understanding about NBB?",
                    NBB_ZBB_UNDERSTANDING),
        alpha("Q128_NBB_UNDERSTAND_OTHER_TXT",
              "128. NBB understanding — Other (Specify) text", length=120),
        yes_no_dk("Q129_HH_CONFINED",
                  "129. Were you or any of your household members confined in a hospital during the past 6 months?"),
        select_one("Q130_HOSPITAL_TYPE",
                   "130. For the most recent hospitalization, what type of hospital?",
                   Q130_HOSPITAL_TYPE, length=1),
        yes_no_dk("Q131_NBB_OOP",
                  "131. During your hospitalization in a DOH-retained hospital, did you or your family pay anything out-of-pocket before being discharged that should have been covered under NBB?"),
    ]
    return record("L_NBB_AWARENESS",
                  "L. No Balance Billing (NBB) Awareness and Utilization",
                  "N", items)


# ============================================================
# Section M. Zero Balance Billing (ZBB) Awareness and Utilization + MAIFIP
#            + Bill Breakdown (Q132-Q143)
# Apr 20 additions vs Apr 08:
# - Q136 MAIFIP heard-of + Q137 MAIFIP info sources (Annex G#1)
# - Q138-Q143 hospital-bill breakdown renumbered (+2 from Apr 08 Q136-Q141)
# Skip logic (logic-pass phase):
# - Q132 No/IDK → Q136 (bypass Q133-Q135)
# - Q136 No/IDK → Q138 (skip MAIFIP source)
# - Q142 No → Q144 (bypass Q143 how-paid)
# ============================================================

def build_section_m():
    Q138_MOST_EXPENSIVE = [
        ("Medicine",          "1"),
        ("Laboratory Tests",  "2"),
        ("Medical Supplies",  "3"),
        ("Doctor's Fee",      "4"),
    ]
    Q141_BILL_ITEMS = [
        ("Rooms <for inpatients only>",         "1"),
        ("Doctor's Fee",                        "2"),
        ("Diagnostic or laboratory procedure",  "3"),
        ("Medical equipment or supplies",       "4"),
        ("Medicines or drugs",                  "5"),
        ("Non-medical expenses (e.g. hygiene kit)", "6"),
        ("Other expenses",                      "7"),
    ]
    Q143_HOW_PAID = [
        ("Own income/ household income",              "01"),
        ("PhilHealth",                                "02"),
        ("Private insurance / HMO",                   "03"),
        ("Loan",                                      "04"),
        ("Sale of assets",                            "05"),
        ("Donations from charities / NGOs",           "06"),
        ("Donations from LGUs / LGU programs",        "07"),
        ("National Government Agencies (DSWD, etc.)", "08"),
        ("Paid by someone else",                      "09"),
        ("Other (Specify)",                           "10"),
    ]
    items = [
        yes_no_dk("Q132_ZBB_HEARD",
                  "132. Have you heard of the Zero Balance Billing (ZBB)?"),
        *select_all("Q133_ZBB_SOURCE",
                    "133. If yes, what are your sources of information about ZBB?",
                    NBB_ZBB_MAIFIP_INFO_SOURCE),
        alpha("Q133_ZBB_SOURCE_OTHER_TXT",
              "133. ZBB info source — Other (Specify) text", length=120),
        *select_all("Q134_ZBB_UNDERSTAND",
                    "134. What is your understanding about ZBB?",
                    NBB_ZBB_UNDERSTANDING),
        alpha("Q134_ZBB_UNDERSTAND_OTHER_TXT",
              "134. ZBB understanding — Other (Specify) text", length=120),
        yes_no_dk("Q135_ZBB_OOP",
                  "135. During your hospitalization in a DOH-retained hospital, did you or your family pay anything out-of-pocket before being discharged that should have been covered under ZBB?"),
        yes_no_dk("Q136_MAIFIP_HEARD",
                  "136. Have you heard of the Medical Assistance for Indigent and Financially Incapacitated Patients (MAIFIP)?"),
        *select_all("Q137_MAIFIP_SOURCE",
                    "137. What are your sources of information about MAIFIP?",
                    NBB_ZBB_MAIFIP_INFO_SOURCE),
        alpha("Q137_MAIFIP_SOURCE_OTHER_TXT",
              "137. MAIFIP info source — Other (Specify) text", length=120),
        select_one("Q138_MOST_EXPENSIVE",
                   "138. From your most recent visit, which among the charges was the most expensive?",
                   Q138_MOST_EXPENSIVE, length=1),
        numeric("Q139_FINAL_AMOUNT_PHP",
                "139. From your most recent visit, what was the final amount you paid in cash at the hospital cashier upon discharge? (PHP)",
                length=8),
        yes_no("Q140_RECALL_BREAKDOWN",
               "140. From your most recent visit, do you recall the breakdown of the bill?"),
        *select_all("Q141_BILL_ITEMS",
                    "141. From your most recent visit, which of the following were included in the bill?",
                    Q141_BILL_ITEMS),
        alpha("Q141_BILL_ITEMS_OTHER_TXT",
              "141. Bill items — Other expenses (Specify) text", length=120),
        numeric("Q141_1_NO_RECEIPT_AMT_PHP",
                "141.1. From your recent visit, how much was charged for services with no receipts provided (i.e. Professional fees)? (PHP)",
                length=8),
        yes_no("Q142_RECALL_PAYMENT",
               "142. From your most recent visit, do you recall how you paid for your bill?"),
        *select_all("Q143_HOW_PAID",
                    "143. From your most recent visit, how did you pay?",
                    Q143_HOW_PAID),
        alpha("Q143_HOW_PAID_OTHER_TXT",
              "143. How paid — Other (Specify) text", length=120),
    ]
    return record("M_ZBB_MAIFIP_BILL",
                  "M. Zero Balance Billing (ZBB) Awareness + MAIFIP + Bill Breakdown",
                  "O", items)


# ============================================================
# Section N. Household Expenditures (Q144-Q185) — WHO/SHA module
#
# Annex G #11 response: expanded from Apr 08's compressed expenditure list
# to the full WHO/SHA reference-period-varying table (weekly / monthly /
# 6-month / 12-month). Each line item emits the standard SHA triplet:
#   {CONSUMED Y/N} + {PURCHASED_PHP numeric} + {INKIND_PHP numeric}
# Sub-total rows (Q157, Q177, Q182, Q185) are CAPI-computed single numerics
# marked [DO NOT ASK] in source — emitted as TOTAL_PHP fields for logic pass.
# ============================================================

def _expenditure_item(prefix, label):
    """Standard SHA triplet: consumed Y/N, purchased PHP, in-kind PHP."""
    return [
        yes_no(f"{prefix}_CONSUMED",
               f"{label} — Consumed by household in reference period?"),
        numeric(f"{prefix}_PURCHASED_PHP",
                f"{label} — Amount spent purchasing (PHP)", length=8),
        numeric(f"{prefix}_INKIND_PHP",
                f"{label} — Estimated value in-kind / received / own-produce (PHP)", length=8),
    ]


def _computed_total(prefix, label):
    """Single numeric for [DO NOT ASK] sub-total rows (CAPI auto-computes)."""
    return [
        numeric(f"{prefix}_TOTAL_PHP",
                f"{label} — Auto-computed total (PHP, [DO NOT ASK])", length=10),
    ]


def build_section_n():
    items = []

    # ----- A. Food Items (Consumed last WEEK) — Q144-Q158 -----
    food_weekly = [
        ("Q144_CEREALS",     "144. Cereals (rice, flour, noodles, corn, etc.)"),
        ("Q145_PULSES",      "145. Pulses, roots, tubers, plantains, (and cooking bananas), and nuts"),
        ("Q146_VEGETABLES",  "146. Vegetables (fresh, dried, dehydrated, frozen)"),
        ("Q147_FRUITS",      "147. Fruits in any form (fresh, dried, dehydrated, frozen)"),
        ("Q148_FISH",        "148. Fish and other seafoods in any form (fresh, dried, dehydrated, frozen)"),
        ("Q149_MEAT",        "149. Any kind of meat and offal in any form (fresh, dried, dehydrated, frozen)"),
        ("Q150_EGGS",        "150. Any kind of egg (from chicken, duck, quail, etc.)"),
        ("Q151_MILK",        "151. Milk and other milk products, excluding butter"),
        ("Q152_FATS",        "152. Butter, lard, other animal-based oils and fats, and vegetable oils (coconut, palm, sesame)"),
        ("Q153_SUGAR",       "153. Sugar, jaggery and other sugar confectionary and desserts (including nut pastes)"),
        ("Q154_CONDIMENTS",  "154. Condiments and other spices and other ready-made meals"),
        ("Q155_WATER_NA",    "155. Water and non-alcoholic beverages (e.g., coffee)"),
        ("Q156_ALCOHOL",     "156. Alcoholic beverages (e.g., local and imported)"),
    ]
    for prefix, label in food_weekly:
        items.extend(_expenditure_item(prefix, label))
    items.extend(_computed_total("Q157_FOOD_SUBTOTAL",
                                 "157. Sub-total (food, last week)"))
    items.extend(_expenditure_item(
        "Q158_RESTAURANT",
        "158. Meals and snacks and beverages from restaurants (dine-in, take-out, and deliveries)"))

    # ----- B. Non-food and Non-Health Items -----
    # Last WEEK — Q159
    items.extend(_expenditure_item(
        "Q159_SMOKING_TOBACCO",
        "159. Smoking (e.g., cigarettes, cigars, and vape), and/or smokeless tobacco products (e.g., chewing tobacco, betel nut)"))

    # Last MONTH — Q160-Q167
    nonfood_monthly = [
        ("Q160_PERSONAL_CARE",   "160. Personal care products (e.g., shampoo, haircut)"),
        ("Q161_HOUSEHOLD_CLEAN", "161. Household cleaning and maintenance products and services including domestic ones"),
        ("Q162_UTILITIES",       "162. Utilities like electricity, water supply, refuse and sewage collection, and fuels (including gas)"),
        ("Q163_TRANSPORT",       "163. Passenger transportation services (jeepney, bus, train, taxi, plane, school bus) including rentals and online purchases and fuels and lubricants for personal vehicle"),
        ("Q164_TELECOM",         "164. Telephone line and mobile phone services, WIFI access, cable TV and any other communication and audio services including repairs and installations"),
        ("Q165_RECREATION_1M",   "165. Recreational, cultural, religious, sporting and entertainment devices (monthly)"),
        ("Q166_POSTAL",          "166. Postal services"),
        ("Q167_HOUSING",         "167. Housing (actual rentals, estimated value of rent if owned)"),
    ]
    for prefix, label in nonfood_monthly:
        items.extend(_expenditure_item(prefix, label))

    # Last 6 MONTHS — Q168-Q169
    items.extend(_expenditure_item(
        "Q168_RECREATION_6M",
        "168. Recreational, cultural, religious, sporting and entertainment devices (6-month)"))
    items.extend(_expenditure_item(
        "Q169_CLOTHING",
        "169. Ready-made clothing, fabric and materials for clothing, and footwear including household textile, glassware, table ware and household utensils including repairs"))

    # Last 12 MONTHS — Q170-Q174
    nonfood_annual = [
        ("Q170_EDUCATION",      "170. Educational services (e.g., tuitions and tutoring)"),
        ("Q171_ACCOMMODATION",  "171. Accommodation services, including for educational establishment (e.g., hotels)"),
        ("Q172_GARDEN_PETS",    "172. Garden and personal pets' products and services"),
        ("Q173_HEALTH_INS",     "173. Health insurance"),
        ("Q174_OTHER_INS",      "174. Other insurance (e.g., for life and accident, and travel)"),
    ]
    for prefix, label in nonfood_annual:
        items.extend(_expenditure_item(prefix, label))

    # ----- E. Health Products and Services (Consumed last 12 MONTHS) — Q175-Q177 -----
    items.extend(_expenditure_item(
        "Q175_INPATIENT",
        "175. Inpatient care services"))
    items.extend(_expenditure_item(
        "Q176_EMERGENCY_TRANSPORT",
        "176. Emergency transportation and emergency rescue services"))
    items.extend(_computed_total(
        "Q177_HEALTH_12M_SUBTOTAL",
        "177. Total value of 175 and 176 (health, 12-month)"))

    # Health (Consumed last 6 MONTHS) — Q178-Q182
    items.extend(_expenditure_item(
        "Q178_PREVENTIVE",
        "178. Preventive services such as immunization/vaccinations services and other preventive services (e.g., tetanus toxoid for pregnant women, and routine immunization such as BCG during well child visits). Exclude the cost of vaccine itself."))
    items.extend(_expenditure_item(
        "Q179_DIAGNOSTIC",
        "179. Diagnostic and laboratory tests, such as blood tests and x-rays, for other reasons than preventive care"))
    items.extend(_expenditure_item(
        "Q180_ASSISTIVE",
        "180. Assistive health products for vision (e.g., glasses), hearing (e.g., hearing aids), and mobility (e.g., crutches, therapeutic footwear), including repair, rental, and online purchases"))
    items.extend(_expenditure_item(
        "Q181_MEDICAL_PRODUCTS",
        "181. Medical products (e.g., antigen tests, glucose meters, masks), including online purchases"))
    items.extend(_computed_total(
        "Q182_HEALTH_6M_SUBTOTAL",
        "182. Total value of 178 to 181 (health, 6-month)"))

    # Health (Consumed last MONTH) — Q183-Q185
    items.extend(_expenditure_item(
        "Q183_MEDICINES",
        "183. Medicines (branded, generic, herbal), vaccines, oral contraceptives, and other pharmaceutical preparations, including online purchases"))
    items.extend(_expenditure_item(
        "Q184_OUTPATIENT",
        "184. Outpatient medical and dental services, including online services, without overnight stay"))
    items.extend(_computed_total(
        "Q185_HEALTH_1M_SUBTOTAL",
        "185. Total value of 183 and 184 (health, 1-month)"))

    return record("N_HOUSEHOLD_EXPENDITURES",
                  "N. Household Expenditures (WHO/SHA)", "P", items)


# ============================================================
# Section O. Sources of Funds for Health (Q186-Q196) — Apr 20
# ============================================================
# Skip logic (logic-pass phase): Q195 Less than 1% / 1-3% / 4-6% /
# More than 6% / Don't know → Q197 (bypass Q196). Only Q195 = "None"
# falls through to Q196.

def build_section_o():
    Q195_INCOME_PCT = [
        ("None",          "1"),
        ("Less than 1%",  "2"),
        ("1-3%",          "3"),
        ("4-6%",          "4"),
        ("More than 6%",  "5"),
        ("Don't know",    "6"),
    ]
    Q196_FOREGONE_CARE = [
        ("Doctor/consultation visit",                    "1"),
        ("Medicines or treatments",                      "2"),
        ("Laboratory tests / diagnostics",               "3"),
        ("Hospital admission / inpatient care",          "4"),
        ("Preventive care (e.g., vaccinations, check-ups)", "5"),
        ("Dental care",                                  "6"),
        ("Other (please specify)",                       "7"),
        ("We do not forego care",                        "8"),
    ]
    items = [
        yes_no("Q186_CURRENT_INCOME", "186. Current income of any household members"),
        yes_no("Q187_SAVINGS",        "187. Savings, pension"),
        yes_no("Q188_SOLD_ASSETS",    "188. Selling of any household's assets or goods (housing, land, animals, jewelry, appliances, or machines)"),
        yes_no("Q189_BORROW_FAMILY",  "189. Borrowing from friends or relatives outside the household"),
        yes_no("Q190_BORROW_INST",    "190. Borrowing from institutions (e.g., financial, microfinance arrangements)"),
        yes_no("Q191_REMITTANCE",     "191. Remittance or money gift"),
        yes_no("Q192_GOVT_ASSIST",    "192. Government assistance (DSWD, local, etc.)"),
        yes_no("Q193_LGU_DONATION",   "193. Donation from LGUs"),
        yes_no("Q194_OTHER_SOURCE",   "194. Other specify"),
        alpha("Q194_OTHER_TXT",       "194. Other specify — text", length=120),
        select_one("Q195_INCOME_PCT",
                   "195. What portion of your household's monthly income would you be willing to set aside for health care if it reduced unexpected medical expenses?",
                   Q195_INCOME_PCT, length=1),
        *select_all("Q196_FOREGONE",
                    "196. If your household chooses not to spend on health care for financial reasons, what kind of care do you usually forego?",
                    Q196_FOREGONE_CARE),
        alpha("Q196_FOREGONE_OTHER_TXT",
              "196. Other (please specify) — text", length=120),
    ]
    return record("O_SOURCES_OF_FUNDS", "O. Sources of Funds for Health", "Q", items)


# ============================================================
# Section P. Financial Risk Protection: Incidence of Reduced/
# Delayed Care (Q197-Q199) — Apr 20
# ============================================================

def build_section_p():
    Q199_WTP = [
        ("Php 0 – Php 249",         "1"),
        ("Php 250 – Php 499",       "2"),
        ("Php 500 – Php 999",       "3"),
        ("Php 1,000 – Php 1249",    "4"),
        ("Php 1,250 – Php 1499",    "5"),
        ("Php 1,500 – Php 1749",    "6"),
        ("Php 1,750 – Php 1999",    "7"),
        ("Php 2,000 and above",     "8"),
        ("Other (Specify)",         "9"),
    ]
    items = [
        yes_no("Q197_DELAYED_CARE",
               "197. In the last 6 months, have you or your household member delayed seeking care for financial reasons?"),
        yes_no("Q198_NOT_FOLLOWED",
               "198. In the last 6 months, have you or your household member seen a doctor and not fully followed their advice (for example, to buy prescribed medicine, to go for a follow-up consultation, to get additional diagnostics) for financial reasons?"),
        select_one("Q199_WTP_CONSULT",
                   "199. The usual price for a consultation ranges from Php 500 to Php 2,000. What is the highest amount you are willing to pay for a consultation?",
                   Q199_WTP, length=1),
        alpha("Q199_WTP_OTHER_TXT", "199. Other (Specify) — text", length=120),
    ]
    return record("P_FINANCIAL_RISK",
                  "P. Financial Risk Protection: Incidence of Reduced/Delayed Care",
                  "R", items)


# ============================================================
# Section Q. Anxiety about Household Finances (Q200-Q202) — Apr 20
# ============================================================
# Skip logic (logic-pass phase): Q200 "Refused to answer" → end of survey;
# Q201 "Not worried at all" → end of survey (bypass Q202).

def build_section_q():
    Q200_REDUCED = [
        ("Yes",              "1"),
        ("No",               "2"),
        ("Don't know",       "3"),
        ("Refused to answer","4"),
    ]
    Q201_WORRIED = [
        ("Very worried",      "1"),
        ("Somewhat worried",  "2"),
        ("Not too worried",   "3"),
        ("Not worried at all","4"),
    ]
    Q202_REASONS = [
        ("Loss of income",                                                                                              "1"),
        ("Healthcare costs related to coronavirus (COVID-19)",                                                          "2"),
        ("Healthcare costs NOT related to coronavirus (COVID-19) (including to treat other diseases, illnesses, injuries, or symptoms)", "3"),
    ]
    items = [
        select_one("Q200_REDUCED_SPEND",
                   "200. Have you or your household had to reduce spending on things you need (such as food, housing, or utilities) because of this health expenditure in the last 1 month?",
                   Q200_REDUCED, length=1),
        select_one("Q201_WORRIED",
                   "201. How worried are you about your household's finances in the next 1 month?",
                   Q201_WORRIED, length=1),
        *select_all("Q202_WORRY_REASONS",
                    "202. Do any of the following reasons describe why you are worried about your household's finances in the next 1 month?",
                    Q202_REASONS, with_other_txt=False),
    ]
    return record("Q_FINANCIAL_ANXIETY", "Q. Anxiety about Household Finances", "S", items)


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
        build_section_c(),       # Repeating: max_occurs=20 (Q30-Q46, Q48-Q50)
        build_section_c_gate(),  # Non-repeating: Q47 HH-level gate
        build_section_d(),
        build_section_e(),
        build_section_f(),
        build_section_g(),
        build_section_h(),       # Apr 20: respondent-level (non-repeating)
        build_section_i(),
        build_section_j(),   # Apr 20: respondent-level (non-repeating)
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
