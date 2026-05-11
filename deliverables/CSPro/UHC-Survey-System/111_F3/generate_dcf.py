"""
generate_dcf.py — F3 Patient Survey CSPro Data Dictionary generator.

Emits PatientSurvey.dcf in CSPro 8.0 JSON dictionary format from the
Apr 20 2026 Annex F3 questionnaire (Revised Inception Report submission,
178 numbered items across sections A–L).

Authority sources (in priority order):
  1. raw/Project-Deliverable-1_Apr20-submitted/Annex F3_Patient Survey
     Questionnaire_UHC Year 2.pdf                                  (printed)
  2. deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F3/generate_dcf.py
     (archived pre-rebuild generator; code reference only — item labels
     re-verified against the Apr 20 PDF on each ingest into this rebuild.)
  3. deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F3/F3-Skip-Logic-
     and-Validations.md                              (skip-logic reference)

Rebuild deltas vs the archived generator:
  - 12-digit decomposed case-ID via shared.cspro_helpers.build_id_block()
    (REGION_CODE, PROVINCE_HUC_CODE, CITY_MUNICIPALITY_CODE, FACILITY_NO,
    CASE_SEQ). Replaces the legacy single 6-digit QUESTIONNAIRE_NO ID item.
  - F3_FACILITY_ID retired. F3<->F1 linkage now derives from the shared
    first 9 digits of the case-ID (RR+PP+MMM+FF).
  - FIELD_CONTROL built via the shared build_field_control(survey_code="F3",
    date_label_entity="the Patient") helper so the F-series instruments
    share the same case-control + AAPOR-disposition + visit-result block.

Naming convention: Q{n}_DESCRIPTOR in UPPER_SNAKE. Item names follow the
archived F3 generator + F3-Skip-Logic-and-Validations.md so the validation-
rule references in that doc keep working without rename churn.

Run:
    python generate_dcf.py        # writes PatientSurvey.dcf next to this file
"""

import json
import sys
from pathlib import Path

# Import shared helpers
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from cspro_helpers import (
    YES_NO, YES_NO_DK, YES_NO_NA, UHC9_OPTIONS, SATISFACTION_5PT,
    numeric, alpha, yes_no, yes_no_dk, yes_no_na,
    select_one, select_all, uhc9_item, record,
    build_field_control, build_geo_id,
    _gps_fields, _photo_block,
    build_id_block, build_dictionary as build_dictionary_from_helpers,
)


# ============================================================
# FIELD CONTROL — shared block + F3-specific extras
# ============================================================

def build_f3_field_control():
    """F3 FIELD_CONTROL: shared block + PATIENT_TYPE and PATIENT_LISTING_NO.

    PATIENT_LISTING_NO is the 1-based sequence the 110_F3_listing CSPro app
    assigns to the listed patient at the sampled facility. The full 12-digit
    case-ID lives in the case-ID block; PATIENT_LISTING_NO is the listing
    app's facility-internal handle, retained for paper-trail reconciliation
    against the listing app's roster.
    """
    extra = [
        numeric("PATIENT_TYPE", "Type of Patient", length=1,
                value_set_options=[("Outpatient", "1"), ("Inpatient", "2")]),
        numeric("PATIENT_LISTING_NO", "Patient Listing Reference Number",
                length=4, zero_fill=True),
    ]
    return build_field_control(survey_code="F3", extra_items=extra,
                               date_label_entity="the Patient")


# ============================================================
# GPS + PHOTO CAPTURE RECORDS
# ============================================================
# F3 has two GPS blocks (facility-side + patient-home-side) and one
# verification photo per case. Items are off-form; capture is triggered
# via onfocus handlers in the .app that call ReadGPSReading() /
# TakeVerificationPhoto() from shared/Capture-Helpers.apc.

def build_f3_facility_capture():
    """GPS metadata for the sampled facility (record type 'Z')."""
    return record(
        "REC_FACILITY_CAPTURE", "Facility GPS Capture", "Z",
        items=_gps_fields(prefix="FACILITY_"),
    )


def build_f3_patient_home_capture():
    """GPS metadata for the patient's home (record type 'Y')."""
    return record(
        "REC_PATIENT_HOME_CAPTURE", "Patient Home GPS Capture", "Y",
        items=_gps_fields(prefix="P_HOME_"),
    )


def build_f3_case_verification():
    """Single verification photo per case (record type 'X')."""
    return record(
        "REC_CASE_VERIFICATION", "Case Verification Photo", "X",
        items=_photo_block(prefix=""),
    )


# ============================================================
# SECTION BUILDERS — A–L
# ============================================================
# Each section returns a CSPro record. Stubs land empty in this scaffold
# commit; subsequent commits populate items section-by-section. The
# stub-then-fill split keeps the generator runnable + .dcf openable
# in CSPro Designer at every intermediate state, which makes the
# section-by-section diff readable in code review.

def build_section_a():
    """A. Introduction and Informed Consent (Q1-Q3).

    Q1 = Yes (1) routes to Q4 (skip Q2, Q3); enforced in PROC, not the DCF.
    """
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


def build_section_b():
    """B. Patient Profile (Q4-Q34).

    Skip-routing (enforced in PROC):
      - Q11 PWD = No  -> Q15  (skip Q12, Q13, Q14)
      - Q12 PWD_SPECIFY = No -> Q15  (skip Q13, Q14)
      - Q14 only when Q13 = "Yes (card was presented and verified)"
      - Q30 IP = No -> Q32  (skip Q31)
      - Q33 DECISION_MAKER = Yes (1) or 3 (Companion is DM) -> Q35  (skip Q34)
    """
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
        ("Yes (card was presented and verified)",            "1"),
        ("No (card not available at the time of interview)", "2"),
        ("Respondent refused to present card",               "3"),
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
        ("I/we have our own",             "1"),
        ("I/we share with our community", "2"),
    ]
    Q26_HAVE = [
        ("Yes, I/ we have",     "1"),
        ("No, I/we don't have", "2"),
    ]
    Q29_SEC = [
        ("Class A or B (working professionals or with a business with several assets)",       "1"),
        ("Class C (working professionals with permanent or semi-permanent income and some assets)", "2"),
        ("Class D or E (semi-permanent workers or informal sector workers with little to no assets)", "3"),
        ("I don't know",                                                                      "4"),
    ]
    Q30_IP = [
        ("Yes", "1"),
        ("No",  "2"),  # proceed to Q32
    ]
    Q33_DECISION = [
        ("Yes (the Patient is the main decision maker)",                  "1"),  # proceed to Q35
        ("No",                                                            "2"),
        ("The Companion answering the survey is the main decision maker", "3"),  # proceed to Q35
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
    return record("B_PATIENT_PROFILE",
                  "B. Patient Profile", "D", items)


def build_section_c():
    """C. Awareness on Universal Health Care (Q35-Q37).

    Skip-routing: Q35 UHC_HEARD = No -> Q38 (skip Q36, Q37). PROC-enforced.
    """
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
        *select_all("Q37_UHC_UNDERSTAND",
                    "37. What is your understanding about UHC?", Q37_UNDERSTANDING),
    ]
    return record("C_UHC_AWARENESS",
                  "C. Awareness on Universal Health Care", "E", items)


def build_section_d():
    """D. PhilHealth Registration and Health Insurance (Q38-Q52).

    Skip-routing:
      - Q38 = No (2) or DK (3)  -> Q43  (skip Q39-Q42)
      - Q41 = No                 -> Q43  (skip Q42)
      - Q43 = No                 -> Q51  (skip Q44; Q45 non-member skip via PDF)
      - Q45 NON-MEMBER          -> Q51  (per PDF "ASKED ONLY FOR PHILHEALTH MEMBERS")
      - Q48 = No (3)             -> Q51  (skip Q49, Q50)
      - Q49 = No                 -> Q51  (skip Q50)
      - Q51 = No                 -> Q53  (skip Q52)
    Reuses one REG_ACTOR value set across Q39, Q40, Q44 (same option list).
    """
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
        ("Yes, I pay directly",       "1"),
        ("Yes, my employer pays",     "2"),
        ("No, I do not pay premiums", "3"),  # proceed to Q51
    ]
    Q50_DIFFICULTY_PAYING = [
        ("Cannot afford the premium",                       "1"),
        ("Payment options are inconvenient",                "2"),
        ("No time to pay",                                  "3"),
        ("Don't see value in paying",                       "4"),
        ("System of PhilHealth is unreliable/usually down", "5"),
        ("I don't know",                                    "6"),
        ("Other (Specify)",                                 "7"),
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
        yes_no("Q51_OTHER_INSURANCE",
               "51. Are you registered with another health insurance plan?"),
        *select_all("Q52_PLANS",
                    "52. Which health insurance plan/s are you enrolled in?", Q52_PLANS),
    ])
    return record("D_PHILHEALTH",
                  "D. PhilHealth Registration and Health Insurance", "F", items)


def build_section_e():
    """E. Primary Care Utilization (Q53-Q82) — primary care + YAKAP/Konsulta.

    Skip-routing:
      - Q53 HAS_PCP = No                            -> Q63 (skip Q54-Q62)
      - Q60 SCHED_TELECON_OK gated on Q59 including teleconsultation
      - Q62 CONSULT_TELECON_OK gated on Q61 including teleconsultation
      - Q63 HAS_USUAL_FACILITY = No                 -> Q65, then skip Q66-Q70
      - Q63 = Yes + Q66 SAME_AS_USUAL = Yes         -> Q68 (skip Q67)
      - Q74 KON_HEARD = No                          -> (Section F)
      - Q77 KON_REGISTERED = No                     -> Q82 (skip Q78-Q81)
      - Q77 = "Never heard / DK" (3, 4)            -> Section F (skip Q78-Q82)
    """
    Q54_PROVIDER = [
        ("General practitioner",                "1"),
        ("Specialty Care Provider/ Specialist", "2"),
        ("Both",                                "3"),
        ("Other (specify)",                     "4"),
        ("None",                                "5"),
    ]
    COMM_MODES = [
        ("Face-to-face",     "1"),
        ("Teleconsultation", "2"),
        ("Landline",         "3"),
        ("Cellphone",        "4"),
        ("Video Conference", "5"),
    ]
    Q65_WHY_NOT = [
        ("I don't get sick",                  "1"),
        ("I recently moved into the area",    "2"),
        ("It's expensive",                    "3"),
        ("I can treat myself",                "4"),
        ("I don't know where to go for care", "5"),
        ("I don't know",                      "6"),
        ("Other (Specify)",                   "7"),
    ]
    Q67_WHY_THIS = [
        ("This facility is more accessible than my usual facility (i.e., nearer, has more "
         "transportation options to get to, and cheaper to travel to)",  "1"),
        ("Needed a service/specialist not available at my usual facility", "2"),
        ("Recommended by friends/family",                                  "3"),
        ("Wanted to try another facility than my usual",                   "4"),
        ("Prefer this facility than my usual",                             "5"),
        ("This was referred to me by my usual facility",                   "6"),
        ("Usual facility is closed for today",                             "7"),
        ("Other (Specify)",                                                "8"),
    ]
    Q68_FACILITY_TYPE = [
        ("YAKAP/Konsulta or primary care provider",         "1"),
        ("Barangay Health Center/ Barangay Health Station", "2"),
        ("Rural Health Unit / Urban Health Center",         "3"),
        ("Public Hospital",                                 "4"),
        ("Private Hospital",                                "5"),
        ("Private Clinic",                                  "6"),
        ("Traditional Healer or Manghihilot/ Albularyo",    "7"),
        ("I don't know",                                    "8"),
        ("Other (specify)",                                 "9"),
    ]
    Q71_NEAREST_TYPE = [
        ("Barangay Health Center/ Barangay Health Station", "1"),
        ("Rural Health Unit / Urban Health Center",         "2"),
        ("Public Hospital",                                 "3"),
        ("Private Hospital",                                "4"),
        ("Private Clinic",                                  "5"),
        ("Traditional Healer or Manghihilot/ Albularyo",    "6"),
        ("I don't know",                                    "7"),
        ("Other (specify)",                                 "8"),
    ]
    TRANSPORT = [
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
    Q75_KON_SOURCE = [
        ("News",                   "1"),
        ("Legislation",            "2"),
        ("Social Media",           "3"),
        ("Friends / Family",       "4"),
        ("Health center/facility", "5"),
        ("LGU/Barangay",           "6"),
        ("I don't know",           "7"),
        ("Other (Specify)",        "8"),
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
        ("Yes",                    "1"),
        ("No",                     "2"),  # proceed to Q82
        ("I've never heard of it", "3"),  # proceed to Q83 (Section F)
        ("I don't know",           "4"),  # proceed to Q83 (Section F)
    ]
    Q78_WHEN_REG = [
        ("Within the past six (6) months",                          "1"),
        ("More than six (6) months but less than one (1) year ago", "2"),
        ("One (1) year but less than two (2) years ago",            "3"),
        ("Two (2) years ago or more",                               "4"),
    ]
    Q82_WHY_NOT_REG = [
        ("Don't know what a YAKAP/Konsulta provider is",                         "01"),
        ("Don't trust PhilHealth",                                               "02"),
        ("Don't know how to register",                                           "03"),
        ("Registration is confusing/time-consuming/inconvenient",                "04"),
        ("Intend to register but do not have found a time to do it.",            "05"),
        ("YAKAP/Konsulta is not available in my local area",                     "06"),
        ("Already have a usual primary care provider that I go to",              "07"),
        ("Don't have the required PhilHealth ID to register for YAKAP/Konsulta", "08"),
        ("Don't have the other requirements to register",                        "09"),
        ("I don't know",                                                         "10"),
        ("Other (specify)",                                                      "11"),
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
        yes_no("Q74_KON_HEARD",
               "74. Have you heard of the term \"YAKAP/ Konsulta package\"?"),
        *select_all("Q75_KON_SOURCE",
                    "75. What are your sources of information about the YAKAP/Konsulta package?",
                    Q75_KON_SOURCE),
        *select_all("Q76_KON_UNDERSTAND",
                    "76. What is your understanding about the YAKAP/Konsulta package?",
                    Q76_KON_UNDERSTAND),
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
    ]
    return record("E_PRIMARY_CARE",
                  "E. Primary Care Utilization", "G", items)


def build_section_f():
    """F. Patient's Health-Seeking Behavior (Q83-Q87)."""
    items = []
    return record("F_HEALTH_SEEKING",
                  "F. Patient's Health-Seeking Behavior", "H", items)


def build_section_g():
    """G. Outpatient Care (Q88-Q104)."""
    items = []
    return record("G_OUTPATIENT",
                  "G. Outpatient Care", "I", items)


def build_section_h():
    """H. Inpatient Care (Q105-Q115)."""
    items = []
    return record("H_INPATIENT",
                  "H. Inpatient Care", "J", items)


def build_section_i():
    """I. Financial Risk Protection (Q116-Q130)."""
    items = []
    return record("I_FINANCIAL_RISK",
                  "I. Financial Risk Protection", "K", items)


def build_section_j():
    """J. Satisfaction on Amenities and Medical Care (Q131-Q144)."""
    items = []
    return record("J_SATISFACTION",
                  "J. Satisfaction on Amenities and Medical Care", "L", items)


def build_section_k():
    """K. Access to Medicines (Q145-Q161)."""
    items = []
    return record("K_MEDICINES",
                  "K. Access to Medicines", "M", items)


def build_section_l():
    """L. Experiences and Satisfaction on Referrals (Q162-Q178)."""
    items = []
    return record("L_REFERRALS",
                  "L. Experiences and Satisfaction on Referrals", "N", items)


# ============================================================
# DICTIONARY ASSEMBLY
# ============================================================

def build_dictionary():
    """Assemble the F3 dictionary.

    Case-ID block: 5-item 12-digit decomposed scheme adopted 2026-05-05
    (see wiki/concepts/Questionnaire Numbering Convention.md). Replaced
    the legacy single 6-digit QUESTIONNAIRE_NO ID item; downstream
    consumers should reference the individual ID-item names rather than
    the retired composite name.

    F3<->F1 linkage derives from the shared first 9 digits of the case-ID
    (REGION_CODE + PROVINCE_HUC_CODE + CITY_MUNICIPALITY_CODE + FACILITY_NO).
    The retired F3_FACILITY_ID composite item is no longer emitted.
    """
    records = [
        # Root record (recordType "1") — required by CSPro hierarchy
        record("PATIENTSURVEY_REC", "PatientSurvey Record", "1", []),
        build_f3_field_control(),
        build_geo_id("facility_and_patient"),
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

    return build_dictionary_from_helpers(
        dict_name="PATIENTSURVEY_DICT",
        dict_label="PatientSurvey",
        id_items=build_id_block(),
        records=records,
    )


def main():
    out_path = Path(__file__).parent / "PatientSurvey.dcf"
    dictionary = build_dictionary()
    out_path.write_text(json.dumps(dictionary, indent=2), encoding="utf-8")

    record_count = len(dictionary["levels"][0]["records"])
    item_count = sum(len(r["items"]) for r in dictionary["levels"][0]["records"])
    print(f"Wrote {out_path}")
    print(f"  Records: {record_count}")
    print(f"  Items:   {item_count}")


if __name__ == "__main__":
    main()
