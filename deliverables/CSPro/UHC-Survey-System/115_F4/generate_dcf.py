"""
generate_dcf.py — F4 Household Survey CSPro Data Dictionary generator.

Emits HouseholdSurvey.dcf in CSPro 8.0 JSON dictionary format from the
Apr 20 2026 Annex F4 questionnaire (Revised Inception Report submission,
202 numbered items across sections A-Q).

Authority sources (in priority order):
  1. raw/Project-Deliverable-1_Apr20-submitted/Annex F4_Household Survey
     Questionnaire_UHC Year 2.pdf                                  (printed)
  2. raw/2026-05-06-survey-manual-bundle/2026-05-06_Survey-Manual-Working-
     File-Kidd.docx                          (Survey Manual §3.4.2; pending
                                              Myra's edit pass)
  3. deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F4/generate_dcf.py
     (archived pre-rebuild generator; code reference only -- item labels
     re-verified against the Apr 20 PDF on each ingest into this rebuild.)

Rebuild deltas vs the archived generator:
  - 12-digit decomposed case-ID via shared.cspro_helpers.build_id_block()
    (REGION_CODE, PROVINCE_HUC_CODE, CITY_MUNICIPALITY_CODE, FACILITY_NO,
    CASE_SEQ). Replaces the legacy single 6-digit QUESTIONNAIRE_NO ID item.
  - FIELD_CONTROL carries TWO linkage data items (Option C, 2026-05-12):
      * HH_LISTING_NO (len 4, zero-fill) -- always populated; the listing-
        roster reference from 113_F4_listing barangay listing app.
      * F4_PARENT_F3_CASE_SEQ (len 3, zero-fill) -- defaults to 999 (NA);
        populated only when F4 was sampled via 110_F3_listing patient
        interval-walk (LISTING_TAG=2 path).
    F4 <-> F1 facility linkage falls out structurally from the shared
    first 9 digits of the case-ID (RR+PP+MMM+FF).
  - FIELD_CONTROL built via the shared build_field_control(survey_code="F4",
    date_label_entity="the Household") helper so the F-series instruments
    share the same case-control + AAPOR-disposition + visit-result block.
  - GPS + verification photo records use the F3 pattern (REC_HOUSEHOLD_-
    CAPTURE type 'Z' and REC_HOUSEHOLD_PHOTO type 'X'), keeping GPS off
    HOUSEHOLD_GEO_ID itself so the geo-id record retains its PSGC-only
    shape.

Naming convention: Q{n}_DESCRIPTOR in UPPER_SNAKE. Item names follow the
archived F4 generator + the verbatim PDF text so any future validation-
rule reference doc can pin items by name without rename churn.

This file is a scaffold stub for commit 1. Subsequent commits land:
  - commit 2:  FIELD_CONTROL + HOUSEHOLD_GEO_ID + GPS + photo records
  - commits 3-9 (approx): section pairs A-Q
  - commit 10: F4 logic-pass + validations spec doc
  - commit 11: concept-page update (Questionnaire Numbering Convention)
  - commit 12: build_all.py wire-in + smoke pass

Until those land, build_dictionary() emits an opening-only DCF with the
root record + empty section stubs so CSPro Designer can open the file at
every intermediate state.

Run:
    python generate_dcf.py        # writes HouseholdSurvey.dcf next to this file
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
# FIELD CONTROL -- shared block + F4-specific extras
# ============================================================

def build_f4_field_control():
    """F4 FIELD_CONTROL: shared block + HH_LISTING_NO + F4_PARENT_F3_CASE_SEQ.

    Two linkage data items (Option C, 2026-05-12 design checkpoint):

    HH_LISTING_NO -- primary listing-roster anchor. Captures the 4-digit
    LISTING_NO from the 113_F4_listing barangay listing app's roster
    occurrence. Always populated; this is the protocol-conformant
    sampling path (PIDS barangay sampling per Protocol V2 sec 3.4.2).

    F4_PARENT_F3_CASE_SEQ -- optional F3 patient parent. Captures the 3-
    digit CASE_SEQ of a parent F3 patient when F4 was sampled via the
    110_F3_listing patient interval-walk (LISTING_TAG=2 path). Defaults
    to 999 (NA per F-series convention: NA = highest value at field width)
    when F4 was sampled via the barangay listing route -- the case for
    nearly all households. Kept on the dictionary to future-proof for
    the parallel sampling mode without DCF surgery later.

    F4 <-> F1 facility linkage is structural -- shared first 9 digits of
    the case-ID (RR+PP+MMM+FF). No separate facility-id data item is
    emitted on F4.
    """
    extra = [
        numeric("HH_LISTING_NO",
                "Household Listing Reference Number (113_F4_listing roster)",
                length=4, zero_fill=True),
        numeric("F4_PARENT_F3_CASE_SEQ",
                "Parent F3 Patient CASE_SEQ (110_F3_listing interval-walk; 999 = NA)",
                length=3, zero_fill=True),
    ]
    return build_field_control(survey_code="F4", extra_items=extra,
                               date_label_entity="the Household")


# ============================================================
# GPS + PHOTO CAPTURE RECORDS
# ============================================================
# F4 has one GPS block (household-side) and one verification photo per
# case. Items are off-form; capture is triggered via onfocus handlers in
# the .app that call ReadGPSReading() / TakeVerificationPhoto() from
# shared/Capture-Helpers.apc. Matches the F3 pattern.

def build_f4_household_capture():
    """GPS metadata for the sampled household (record type 'Z')."""
    return record(
        "REC_HOUSEHOLD_CAPTURE", "Household GPS Capture", "Z",
        items=_gps_fields(prefix="HH_"),
    )


def build_f4_case_verification():
    """Single verification photo per case (record type 'X')."""
    return record(
        "REC_CASE_VERIFICATION", "Case Verification Photo", "X",
        items=_photo_block(prefix=""),
    )


# ============================================================
# SECTION BUILDERS -- A-Q
# ============================================================
# Each section returns a CSPro record. Stubs land empty in this scaffold
# commit; subsequent commits populate items section-by-section. The
# stub-then-fill split keeps the generator runnable + the .dcf openable
# in CSPro Designer at every intermediate state, which makes the
# section-by-section diff readable in code review.

def build_section_a():
    """A. Introduction and Informed Consent Form Profile (Q1).

    Single gating item. Q1 = Yes (1) is the standard path; Q1 = No (2)
    routes via PROC to attempt to locate the household head before
    proceeding. Enforced in the .apc, not the DCF.
    """
    Q1_OPTIONS = [
        ("Yes", "1"),
        ("No",  "2"),
    ]
    items = [
        select_one("Q1_IS_HH_HEAD",
                   "1. Before we begin, to confirm, are you the household head?",
                   Q1_OPTIONS, length=1),
    ]
    return record("A_INFORMED_CONSENT",
                  "A. Introduction and Informed Consent Form Profile", "C", items)


def build_section_b():
    """B. Respondent Profile (Q2-Q29).

    Skip-routing (enforced in PROC):
      - Q4 LGBTQIA = No (2) / Don't Know (4) / Refused (5) / Not Comfortable (3)
                       -> Q6 (skip Q5)
      - Q7 PWD = No  -> Q11 (skip Q8, Q9, Q10)
      - Q8 PWD_SPECIFY = No -> Q11 (skip Q9, Q10)
      - Q9 PWD_CARD = No (2) or Refused (3) -> Q11 (skip Q10)
      - Q10 only when Q9 = Yes (card was presented and verified)
      - Q14 IP = No -> Q16 (skip Q15)
    """
    Q3_SEX = [
        ("Male",   "1"),
        ("Female", "2"),
    ]
    Q4_LGBTQIA = [
        ("Yes",                        "1"),
        ("No",                         "2"),  # proceed to Q6
        ("Not Comfortable to Answer",  "3"),  # proceed to Q6
        ("Don't Know",                 "4"),  # proceed to Q6
        ("Refused to answer",          "5"),  # proceed to Q6
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
        ("Yes (card was presented and verified)",                "1"),
        ("No (card not available at the time of interview)",     "2"),  # proceed to Q11
        ("Respondent refused to present card",                   "3"),  # proceed to Q11
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
        ("Other (specify)",                                                                                                   "11"),
        ("I don't know",                                                                                                      "98"),
        ("Not applicable",                                                                                                    "99"),
    ]
    Q12_EMPLOYMENT = [
        ("Has a permanent job/ own business",                  "1"),
        ("Has a short-term, seasonal, casual job/business",    "2"),
        ("Worked on different jobs day to day per week",       "3"),
        ("Unemployed and looking for work",                    "4"),
        ("Unemployed and not looking for work",                "5"),
        ("Retired",                                            "6"),
        ("I don't know",                                       "7"),
        ("Not applicable",                                     "8"),
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
        ("I don't know",                                       "98"),
    ]
    Q17_DECISION_MAKER = [
        ("Me (respondent)",            "01"),
        ("My father",                  "02"),
        ("My mother",                  "03"),
        ("My parents",                 "04"),
        ("My spouse/partner",          "05"),
        ("My spouse/partner and I",    "06"),
        ("My sibling",                 "07"),
        ("My grandfather",             "08"),
        ("My grandmother",             "09"),
        ("My uncle",                   "10"),
        ("My aunt",                    "11"),
        ("Other (specify)",            "12"),
    ]
    Q18_BRACKET = [
        ("Under 40,000",         "1"),
        ("40,000 - 59,999",      "2"),
        ("60,000 - 99,999",      "3"),
        ("100,000 - 249,999",    "4"),
        ("250,000 - 499,999",    "5"),
        ("500,000 and over",     "6"),
        ("Refuse to answer",     "7"),
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
        ("Class A or B (working professionals or with a business with several assets)",                  "1"),
        ("Class C (working professionals with permanent or semi-permanent income and some assets)",      "2"),
        ("Class D or E (semi-permanent workers or informal sector workers with little to no assets)",    "3"),
        ("I don't know",                                                                                 "4"),
    ]
    items = [
        alpha("RESPONDENT_NAME",
              "Respondent's Name (Last Name, First Name, MI, Extension)", length=120),
        numeric("Q2_BIRTH_MONTH",
                "2. In what month and year were you born? -- Month", length=2),
        numeric("Q2_BIRTH_YEAR",
                "2. In what month and year were you born? -- Year", length=4),
        numeric("Q2_1_AGE",
                "2.1. Just to confirm, how old are you as of your last birthday (in years)?",
                length=3),
        select_one("Q3_SEX",
                   "3. What is your sex at birth?", Q3_SEX, length=1),
        select_one("Q4_LGBTQIA",
                   "4. Are you part of the LGBTQIA+ community? "
                   "(e.g., gay, lesbian, bisexual, etc.).",
                   Q4_LGBTQIA, length=1),
        select_one("Q5_GROUP",
                   "5. Which group do you identify with?", Q5_GROUP, length=1),
        alpha("Q5_GROUP_OTHER_TXT",
              "5. Group identity -- Other (specify) text", length=120),
        select_one("Q6_CIVIL_STATUS",
                   "6. What is your civil status?", Q6_CIVIL_STATUS, length=1),
        yes_no("Q7_PWD",
               "7. Do you identify as a person with a disability?"),
        yes_no("Q8_PWD_SPECIFY",
               "8. Would you like to specify the type of disability?"),
        select_one("Q9_PWD_CARD",
                   "9. May we view your PWD Identification Card?", Q9_PWD_CARD, length=1),
        select_one("Q10_DISABILITY_TYPE",
                   "10. Based on the presented PWD Identification Card, "
                   "what type of disability is indicated?",
                   Q10_DISABILITY_TYPE, length=1),
        alpha("Q10_DISABILITY_OTHER_TXT",
              "10. Disability -- Other (specify) text", length=120),
        select_one("Q11_EDUCATION",
                   "11. What is the highest level of education you have attained?",
                   Q11_EDUCATION, length=2),
        alpha("Q11_EDUCATION_OTHER_TXT",
              "11. Education -- Other (specify) text", length=120),
        select_one("Q12_EMPLOYMENT",
                   "12. What is your employment status?", Q12_EMPLOYMENT, length=1),
        select_one("Q13_INCOME_SOURCE",
                   "13. What is your main source of income?",
                   Q13_INCOME_SOURCE, length=2),
        yes_no("Q14_IP",
               "14. Are you a member of Indigenous People (IP) community, "
               "like the Igorot, Lumad, Mangyans, etc.?"),
        alpha("Q15_IP_GROUP",
              "15. If yes, which group? (Specify)", length=120),
        yes_no("Q16_4PS",
               "16. Is your household a beneficiary of the Pantawid Pamilyang "
               "Pilipino Program (4Ps)?"),
        select_one("Q17_DECISION_MAKER",
                   "17. Who takes the most responsibility for making the decisions "
                   "regarding healthcare in your household?",
                   Q17_DECISION_MAKER, length=2),
        alpha("Q17_DECISION_MAKER_OTHER_TXT",
              "17. Decision maker -- Other (specify) text", length=120),
        numeric("Q18_INCOME_AMOUNT",
                "18. In the past 6 months, what is your average monthly household "
                "income? Please specify in Philippine pesos. -- Approximate amount",
                length=8),
        select_one("Q18_INCOME_BRACKET",
                   "18. Income category corresponding to the respondent's approximate "
                   "household income",
                   Q18_BRACKET, length=1),
        numeric("Q19_HH_SIZE",
                "19. How many total individuals (including children) live in your "
                "house now?",
                length=2),
        numeric("Q20_HH_CHILDREN",
                "20. How many non-working age children (i.e., below the age of 18) "
                "live in your house now?",
                length=2),
        numeric("Q21_HH_SENIORS",
                "21. How many senior citizens live in your house now?", length=2),
        yes_no("Q22_ELECTRICITY",
               "22. Do you have electricity in your household?"),
        select_one("Q23_WATER",
                   "23. What is the family's main source of water supply for daily use?",
                   Q23_WATER, length=1),
        alpha("Q23_WATER_OTHER_TXT",
              "23. Water -- Other (specify) text", length=120),
        select_one("Q24_FAUCET_OWN",
                   "24. Do you have your own faucet, or do you share with your community?",
                   Q24_OWN_SHARE, length=1),
        select_one("Q25_TUBE_OWN",
                   "25. Do you have your own tube/pipe, or do you share with your community?",
                   Q24_OWN_SHARE, length=1),
        select_one("Q26_REFRIGERATOR",
                   "26. Does the family own a refrigerator/freezer?",
                   Q26_HAVE, length=1),
        select_one("Q27_TELEVISION",
                   "27. Does the family own a television set?", Q26_HAVE, length=1),
        select_one("Q28_WASHER",
                   "28. Does the family own a washing machine?", Q26_HAVE, length=1),
        select_one("Q29_SEC_CLASS",
                   "29. How would the socioeconomic class of your household be classified?",
                   Q29_SEC, length=1),
    ]
    return record("B_RESPONDENT_PROFILE",
                  "B. Respondent Profile", "D", items)


def build_section_c():
    """C. Household Roster and Characteristics (C1-C5, Q30-Q46).

    Per-household-member occurring record, max_occurs=10 (matching the
    PDF's 10-row roster table; the same 10-member limit applies to the
    later private-insurance sub-roster Q48-Q50). Q47 (HH-level private-
    insurance gate) and Q48-Q50 (private-insurance sub-roster) live in
    separate records (C_PRIVATE_INSURANCE_GATE and
    C_PRIVATE_INSURANCE_ROSTER) so the section C record keeps the
    PDF's C1-C5 sub-section anchoring (Q30-Q46) intact.

    Sub-section anchoring (per PDF):
      - C1. HOUSEHOLD ROSTER             -- Q30 (Name), Q31 (Present/Away),
                                            Q32 (Age), Q33 (Sex), Q34 (Rel)
      - C2. HOUSEHOLD CHARACTERISTICS    -- disability (Q35-Q38)
      - C3. HOUSEHOLD CHARACTERISTICS    -- civil/education/employment
                                            (Q39-Q41)
      - C4. HOUSEHOLD CHARACTERISTICS    -- GSIS/SSS/Pag-ibig (Q42-Q44)
      - C5. HOUSEHOLD CHARACTERISTICS    -- PhilHealth registration +
                                            member category (Q45-Q46)

    NA / Don't-know codes per F4: the PDF uses -55 for "I don't know"
    in C4-C5 columns and 0=No/1=Yes for C2 (matching the archived F4
    generator's convention; archived used "55" stored as positive
    integer to fit numeric items). For uniformity with the rest of the
    F-series the codes are stored as positive integers in the value
    sets below; the negative sign is a paper-form display convention.
    """
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
    # YN_DK55: -55 stored as "55" (positive) per the convention used in
    # the archived F4 generator. Sign is a display convention for paper;
    # CSPro numeric items cannot store negative values without a leading
    # sign character that the .dcf would otherwise need to widen for.
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
        numeric("HH_MEMBER_LINE_NO", "Household Member Line Number",
                length=2, zero_fill=True),
        # C1. HOUSEHOLD ROSTER (Q30-Q34)
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
        # C2. HOUSEHOLD CHARACTERISTICS -- disability (Q35-Q38)
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
                   "38. Based on the presented PWD Identification Card, "
                   "what type of disability is indicated?",
                   Q38_DISABILITY_TYPE, length=1),
        alpha("Q38_DISABILITY_OTHER_TXT",
              "38. Disability -- Other (specify) text", length=120),
        # C3. HOUSEHOLD CHARACTERISTICS -- civil/education/employment (Q39-Q41)
        select_one("Q39_CIVIL_STATUS",
                   "39. Civil Status", Q39_CIVIL_STATUS, length=1),
        select_one("Q40_EDUCATION",
                   "40. Highest level of education completed",
                   Q40_EDUCATION, length=2),
        select_one("Q41_EMPLOYMENT",
                   "41. Employment Status", Q41_EMPLOYMENT, length=1),
        # C4. HOUSEHOLD CHARACTERISTICS -- social insurance (Q42-Q44)
        select_one("Q42_GSIS",
                   "42. Is (NAME) covered by GSIS either as a member or dependent?",
                   YN_DK55, length=2),
        select_one("Q43_SSS",
                   "43. Is (NAME) covered by SSS either as a member or dependent?",
                   YN_DK55, length=2),
        select_one("Q44_PAGIBIG",
                   "44. Is (NAME) covered by Pag-ibig either as a member or dependent?",
                   YN_DK55, length=2),
        # C5. HOUSEHOLD CHARACTERISTICS -- PhilHealth (Q45-Q46)
        select_one("Q45_PHILHEALTH_REG",
                   "45. Currently registered with PhilHealth?",
                   YN_DK55, length=2),
        select_one("Q46_MEMBER_CATEGORY",
                   "46. What is his/her membership category? (Only answer if 'Yes' in Q45)",
                   Q46_MEMBER_CATEGORY, length=2),
        alpha("Q46_MEMBER_OTHER_TXT",
              "46. Member category -- Other (specify) text", length=120),
    ]
    return record("C_HOUSEHOLD_ROSTER",
                  "C. Household Roster and Characteristics", "E",
                  items, max_occurs=10, required=False)


def build_section_c_private_insurance_gate():
    """Q47 HH-level private-insurance gate. Non-repeating.

    Q47 = Yes (1) -> proceed to Q48 (per-member private-insurance roster).
    Q47 = No  (2) -> proceed to Q51 (Section D, UHC awareness).
    Routing enforced in PROC, not the DCF.
    """
    Q47_PRIVATE_INS = [
        ("Yes", "1"),  # proceed to Q48
        ("No",  "2"),  # proceed to Q51
    ]
    items = [
        select_one("Q47_HAS_PRIVATE_INS",
                   "47. Do you or other members of your HH have private insurance?",
                   Q47_PRIVATE_INS, length=1),
    ]
    return record("C_PRIVATE_INSURANCE_GATE",
                  "C. Private Insurance Coverage (HH-level gate, Q47)", "T", items)


def build_section_c_private_insurance_roster():
    """Q48-Q50 per-member private-insurance sub-roster. max_occurs=10.

    Only relevant when Q47 = Yes (1); when Q47 = No, this record stays
    unpopulated for the case (routing enforced in PROC).

    The roster reuses HH_MEMBER_LINE_NO for cross-reference with the
    main C_HOUSEHOLD_ROSTER (per-row name displayed Q48 is "First Name
    Only" of the same household member). The actual cross-reference is
    enforced in PROC at the sub-roster's preproc handler.
    """
    YN_DK55 = [
        ("Yes",          "01"),
        ("No",           "02"),
        ("I don't know", "55"),
    ]
    items = [
        numeric("HH_MEMBER_LINE_NO", "Household Member Line Number "
                "(same line as in C_HOUSEHOLD_ROSTER)", length=2, zero_fill=True),
        alpha("Q48_NAME_FIRST",
              "48. Name (First Name Only) -- private insurance roster", length=80),
        select_one("Q49_PRIVATE_INS",
                   "49. Is (NAME) covered by a private health insurance either as "
                   "a member or dependent? (Example: Maxicare, Intellicare, "
                   "Pacific Cross Health Care)",
                   YN_DK55, length=2),
        alpha("Q50_PRIVATE_INS_OTHER_TXT",
              "50. Others (Specify)", length=120),
    ]
    return record("C_PRIVATE_INSURANCE_ROSTER",
                  "C. Private Insurance Coverage Roster (Q48-Q50)", "U",
                  items, max_occurs=10, required=False)


def build_section_d():
    """D. Awareness on Universal Health Care (UHC) (Q51-Q53).

    Skip-routing (enforced in PROC):
      - Q51 = No (2) -> Q52 (continues; "No" path branches to "what is
        your source of info" before resuming -- per PDF "No <proceed to
        Q52>"). Effectively Q52/Q53 both ask regardless of Q51 in this
        section.

    Q52 and Q53 are SELECT ALL THAT APPLY (multi-response).
    """
    INFO_SOURCE = [
        ("News",                       "01"),
        ("Legislation",                "02"),
        ("Social Media",               "03"),
        ("Friends / Family",           "04"),
        ("Health center/facility",     "05"),
        ("LGU/Barangay",               "06"),
        ("I don't know",               "07"),
        ("Other (Specify)",            "08"),
    ]
    UHC_UNDERSTANDING = [
        ("Protection from financial risk/decreased out-of-pocket spending",       "01"),
        ("Access to quality and affordable health care goods and services",       "02"),
        ("Automatic enrollment into PhilHealth",                                  "03"),
        ("Primary care provider for every Filipino",                              "04"),
        ("I don't know",                                                          "05"),
        ("Other (Specify)",                                                       "06"),
    ]
    items = [
        yes_no("Q51_HEARD_UHC",
               "51. Have you heard about Universal Health Care (UHC) prior to "
               "this survey?"),
        *select_all("Q52_UHC_SOURCE",
                    "52. What is your source of information about UHC?",
                    INFO_SOURCE),
        *select_all("Q53_UHC_UNDERSTANDING",
                    "53. What is your understanding about UHC?",
                    UHC_UNDERSTANDING),
    ]
    return record("D_UHC_AWARENESS",
                  "D. Awareness on Universal Health Care (UHC)", "F", items)


def build_section_e():
    """E. YAKAP/Konsulta Awareness (Q54-Q56).

    Skip-routing (enforced in PROC):
      - Q54 = No (2) -> Q57 (skip Q55, Q56)

    Q55 and Q56 are SELECT ALL THAT APPLY.
    """
    INFO_SOURCE = [
        ("News",                       "01"),
        ("Legislation",                "02"),
        ("Social Media",               "03"),
        ("Friends / Family",           "04"),
        ("Health center/facility",     "05"),
        ("LGU/Barangay",               "06"),
        ("I don't know",               "07"),
        ("Other (Specify)",            "08"),
    ]
    YAKAP_UNDERSTANDING = [
        ("Free primary care consultation (with a registered YAKAP/Konsulta provider)",        "01"),
        ("Free health risk screening and assessment (with a registered YAKAP/Konsulta provider)", "02"),
        ("Free selected laboratory / diagnostics examination",                                "03"),
        ("Free selected drugs and medicines",                                                 "04"),
        ("There are no benefits in the package",                                              "05"),
        ("I don't know",                                                                      "06"),
        ("Other (Specify)",                                                                   "07"),
    ]
    items = [
        yes_no("Q54_HEARD_YAKAP",
               "54. Have you heard of the term \"YAKAP/Konsulta package\"?"),
        *select_all("Q55_YAKAP_SOURCE",
                    "55. What are your sources of information about the "
                    "YAKAP/Konsulta package?",
                    INFO_SOURCE),
        *select_all("Q56_YAKAP_UNDERSTANDING",
                    "56. What is your understanding about the YAKAP/Konsulta package?",
                    YAKAP_UNDERSTANDING),
    ]
    return record("E_YAKAP_KONSULTA",
                  "E. YAKAP/Konsulta Awareness", "G", items)


def build_section_f():
    """F. BUCAS Awareness and Utilization (Q57-Q61).

    Skip-routing (enforced in PROC):
      - Q57 = No (2) -> Q62 (skip Q58, Q59, Q60, Q61)
      - Q60 = No (2) -> Q62 (skip Q61)

    Section is conditionally applicable: Q57-Q61 only for respondents
    in areas with BUCAS; otherwise enumerator proceeds to Q62 (per
    PDF section header note).
    """
    INFO_SOURCE = [
        ("News",                       "01"),
        ("Legislation",                "02"),
        ("Social Media",               "03"),
        ("Friends / Family",           "04"),
        ("Health center/facility",     "05"),
        ("LGU/Barangay",               "06"),
        ("I don't know",               "07"),
        ("Other (Specify)",            "08"),
    ]
    BUCAS_UNDERSTANDING = [
        ("Provides urgent care for non-life-threatening/serious conditions",       "01"),
        ("Offers outpatient and ambulatory health services",                       "02"),
        ("Helps reduce overcrowding in hospitals",                                 "03"),
        ("Allows access to timely medical consultation and treatment",             "04"),
        ("Other (specify)",                                                        "05"),
    ]
    BUCAS_SERVICES = [
        ("Medical consultation for urgent or minor conditions",        "01"),
        ("Outpatient or ambulatory care services",                     "02"),
        ("Basic diagnostic services (e.g., laboratory tests, X-ray)",  "03"),
        ("Minor procedures or treatments",                             "04"),
        ("Referral to higher-level health facilities",                 "05"),
        ("I don't know",                                               "06"),
        ("Other (specify)",                                            "07"),
    ]
    items = [
        yes_no("Q57_HEARD_BUCAS",
               "57. Have you heard about Bagong Urgent Care and Ambulatory "
               "Service (BUCAS) center?"),
        *select_all("Q58_BUCAS_SOURCE",
                    "58. If yes, what are your sources of information about "
                    "this BUCAS center?",
                    INFO_SOURCE),
        *select_all("Q59_BUCAS_UNDERSTANDING",
                    "59. What is your understanding about a BUCAS center?",
                    BUCAS_UNDERSTANDING),
        yes_no("Q60_BUCAS_ACCESSED",
               "60. In the last six months, did you or any member of your HH "
               "accessed the services in a BUCAS center?"),
        *select_all("Q61_BUCAS_SERVICES_AVAILED",
                    "61. If yes, which of the services did you avail?",
                    BUCAS_SERVICES),
    ]
    return record("F_BUCAS",
                  "F. Bagong Urgent Care and Ambulatory Service (BUCAS) "
                  "Awareness and Utilization", "H", items)


def build_section_g():
    """G. Access to Medicines (Q62-Q78).

    Skip-routing (enforced in PROC):
      - Q62 = Never (5) -> Q69 (skip Q63-Q68)
      - Q69 = No (2)    -> Q75 (skip Q70-Q74)
      - Q72 = No (2)    -> Q75 (skip Q73, Q74) -- inferred from PDF
                                                  flow (Q73-Q74 ask about
                                                  GAMOT meds received)
      - Q76 = Branded (1) -> Q78 (skip Q77)
      - Q76 = Don't know the difference (4) or Not applicable (5)
                          -> Q79 (skip Q77, Q78)
      - Q77 only when Q76 = Generic (2) or Both (3)
      - Q78 only when Q76 = Branded (1) or Both (3)

    Q64 + Q73 are free-text medicine lists; PDF says "PLEASE LIST DOWN".
    Captured as length-512 alpha for multi-medicine entry; the enumerator
    types comma-separated names.
    """
    Q62_FREQUENCY = [
        ("Weekly",     "1"),
        ("Bi-weekly",  "2"),
        ("Monthly",    "3"),
        ("Rarely",     "4"),
        ("Never",      "5"),  # proceed to Q69
    ]
    Q63_PRESCRIPTION = [
        ("Prescribed by a doctor",                              "1"),
        ("Over-the-counter medicine",                           "2"),
        ("Purchased both prescribed medicine and OTC medicine", "3"),
        ("I don't know",                                        "4"),
    ]
    Q65_CONDITION = [
        ("Upper respiratory infection",                                 "01"),
        ("Hypertension",                                                "02"),
        ("Immunization",                                                "03"),
        ("Pregnancy or birth",                                          "04"),
        ("Flu",                                                         "05"),
        ("Fever",                                                       "06"),
        ("Joint and muscle pain",                                       "07"),
        ("Asthma or COPD (chronic breathing problem, not cancer)",      "08"),
        ("Diabetes",                                                    "09"),
        ("Heart problem",                                               "10"),
        ("Kidney problem /Dialysis",                                    "11"),
        ("Cancer (any)",                                                "12"),
        ("Gastro problem (vomiting, diarrhea, etc.)",                   "13"),
        ("Other infection (e.g. urine, skin, other virus etc.)",        "14"),
        ("Accident/injury (e.g. wound/broken bone)",                    "15"),
        ("Dental",                                                      "16"),
        ("ENT (problem with ear/nose/throat)",                          "17"),
        ("Allergy",                                                     "18"),
        ("No condition - Regular check-up only",                        "19"),
        ("Other (Specify)",                                             "20"),
    ]
    Q66_WHERE = [
        ("Public Hospital",                                                  "01"),
        ("Private Hospital",                                                 "02"),
        ("Chain Pharmacies (e.g. Mercury Drug, Watsons, TGP, Generika)",     "03"),
        ("Local pharmacies",                                                 "04"),
        ("Online stores (e.g. Shopee, Lazada)",                              "05"),
        ("Barangay Health Station",                                          "06"),
        ("Rural Health Unit or City Health Office",                          "07"),
        ("Other (specify)",                                                  "08"),
    ]
    Q68_EASE = [
        ("Very difficult", "1"),
        ("Difficult",      "2"),
        ("Neutral",        "3"),
        ("Easy",           "4"),
        ("Very easy",      "5"),
    ]
    INFO_SOURCE = [
        ("News",                       "01"),
        ("Legislation",                "02"),
        ("Social Media",               "03"),
        ("Friends / Family",           "04"),
        ("Health center/facility",     "05"),
        ("LGU/Barangay",               "06"),
        ("I don't know",               "07"),
        ("Other (Specify)",            "08"),
    ]
    Q71_GAMOT_UNDERSTANDING = [
        ("Provides free or affordable medicines for outpatients",                "01"),
        ("Ensures continuous availability of essential medicines",               "02"),
        ("Helps reduce out-of-pocket expenses for medicines",                    "03"),
        ("Supports treatment of common illnesses and chronic conditions",        "04"),
        ("I don't know",                                                         "05"),
        ("Other (specify)",                                                      "06"),
    ]
    Q74_WHERE_REST = [
        ("Purchased from pharmacy",                "01"),
        ("Purchased from public hospital",         "02"),
        ("Purchased from private hospital",        "03"),
        ("Purchased from primary care provider (PCP)", "04"),
        ("Received from PCP for free",             "05"),
        ("Received from LGU for free",             "06"),
        ("Received from public hospital for free", "07"),
        ("Received from private hospital for free", "08"),
        ("Not applicable",                         "09"),
        ("Other (Specify)",                        "10"),
    ]
    Q76_TYPE = [
        ("Branded",                          "1"),  # proceed to Q78
        ("Generic",                          "2"),
        ("Both branded and generic",         "3"),
        ("Don't know the difference",        "4"),  # proceed to Q79
        ("Not applicable",                   "5"),  # proceed to Q79
    ]
    Q77_GENERIC_WHY = [
        ("Lower cost",                                        "01"),
        ("Prescribed by doctor",                              "02"),
        ("Readily available",                                 "03"),
        ("Given for free",                                    "04"),
        ("More or as effective as branded medicine",          "05"),
        ("I don't know",                                      "06"),
        ("Not applicable",                                    "07"),
        ("Other (Specify)",                                   "08"),
    ]
    Q78_BRANDED_WHY = [
        ("Branded medicine is more effective than generic",   "01"),
        ("Not aware of generic option",                       "02"),
        ("Prescribed by doctor",                              "03"),
        ("Given for free",                                    "04"),
        ("Prefer branded over generic option",                "05"),
        ("I don't know",                                      "06"),
        ("Not applicable",                                    "07"),
        ("Other (Specify)",                                   "08"),
    ]
    items = [
        select_one("Q62_PURCHASE_FREQUENCY",
                   "62. How often do you purchase or receive medicines?",
                   Q62_FREQUENCY, length=1),
        select_one("Q63_PRESCRIPTION_TYPE",
                   "63. Was the most recent medicine purchased prescribed by a "
                   "doctor or over-the-counter (OTC) medicine (no need for a "
                   "prescription)?",
                   Q63_PRESCRIPTION, length=1),
        alpha("Q64_MEDICATIONS_LIST",
              "64. What are the medications that you or any member of your "
              "household usually take? (List)",
              length=512),
        *select_all("Q65_MEDICAL_CONDITIONS",
                    "65. What are the medical conditions that you/your household "
                    "member/s take the medicine/s for?",
                    Q65_CONDITION),
        *select_all("Q66_WHERE_BUY",
                    "66. Where do you usually buy or receive your medicines?",
                    Q66_WHERE),
        alpha("Q67_TIME_TO_PHARMACY",
              "67. How much time does it take for you to reach the nearest "
              "pharmacy from your home? (HH:MM)",
              length=5),
        select_one("Q68_PHARMACY_ACCESS_EASE",
                   "68. How easy is it for you to access a pharmacy or drugstore?",
                   Q68_EASE, length=1),
        yes_no("Q69_HEARD_GAMOT",
               "69. Have you heard of the Guaranteed and Accessible Medications "
               "for Outpatient Treatment (GAMOT) Package, which is part of "
               "PhilHealth's YAKAP/Konsulta or primary care benefit package?"),
        *select_all("Q70_GAMOT_SOURCE",
                    "70. If yes, what are your sources of information for "
                    "GAMOT Package?",
                    INFO_SOURCE),
        *select_all("Q71_GAMOT_UNDERSTANDING",
                    "71. What is your understanding of the GAMOT Package?",
                    Q71_GAMOT_UNDERSTANDING),
        yes_no("Q72_GAMOT_OBTAINED",
               "72. Did you get the medicines from the GAMOT Package during "
               "the past 6 months?"),
        alpha("Q73_GAMOT_MEDICATIONS_LIST",
              "73. What are the medications that you obtained from the GAMOT "
              "Package? (List)",
              length=512),
        *select_all("Q74_WHERE_REST_OF_MEDS",
                    "74. Where did you get the rest of the medicines?",
                    Q74_WHERE_REST),
        yes_no("Q75_KNOWS_BRAND_VS_GENERIC",
               "75. Do you know the difference between a 'branded' and a "
               "'generic' medicine?"),
        select_one("Q76_MED_TYPE_PURCHASED",
                   "76. Was/were the medicine/s you bought outside of GAMOT "
                   "pharmacy branded or generic?",
                   Q76_TYPE, length=1),
        *select_all("Q77_GENERIC_REASON",
                    "77. If generic, why did you buy generic medicine?",
                    Q77_GENERIC_WHY),
        *select_all("Q78_BRANDED_REASON",
                    "78. If branded, why did you buy branded medicine? "
                    "(Ask if answer in Q76 is branded and both branded and "
                    "generic, otherwise skip.)",
                    Q78_BRANDED_WHY),
    ]
    return record("G_ACCESS_TO_MEDICINES",
                  "G. Access to Medicines", "I", items)


def build_section_h():
    """H. PhilHealth Registration and Health Insurance (Q79-Q88).

    Section conditionally applicable: Q79-Q88 only when the respondent
    is registered with PhilHealth (per PDF section header note --
    "Answer Q79 to Q88 if the respondent is registered with PhilHealth
    in Q45"). The Q45 column is per-member in C_HOUSEHOLD_ROSTER; for
    this section the gate is the respondent's own Q45 row (HH_MEMBER_-
    LINE_NO=1). Routing enforced in PROC.

    Skip-routing (enforced in PROC):
      - Q81 = No (2) -> Q83 (skip Q82)
      - Q87 = No (2) -> Q89 (skip Q88; section H ends)
    """
    Q79_HOW_FIND_OUT = [
        ("PhilHealth representative",          "01"),
        ("LGU",                                "02"),
        ("Primary care provider",              "03"),
        ("Other health care provider",         "04"),
        ("Employer",                           "05"),
        ("No one / self-registered",           "06"),
        ("Barangay Health Worker",             "07"),
        ("Friends / Family",                   "08"),
        ("Health center/facility",             "09"),
        ("Other (Specify)",                    "10"),
    ]
    # Q80 reuses the same value set as Q79 per the PDF
    Q80_ASSISTANCE = Q79_HOW_FIND_OUT
    Q82_DIFFICULTIES = [
        ("Unclear process",                                            "01"),
        ("Took a long time",                                           "02"),
        ("Did not know where to ask for help",                         "03"),
        ("Had to travel a long way",                                   "04"),
        ("No valid ID",                                                "05"),
        ("Did not know the required documents to register",            "06"),
        ("I don't know",                                               "07"),
        ("Other (Specify)",                                            "08"),
    ]
    Q85_BENEFITS = [
        ("No balance billing for basic ward accommodation",   "01"),
        ("Subsidized inpatient services",                     "02"),
        ("Subsidized outpatient services",                    "03"),
        ("There are no benefits to being a member",           "04"),
        ("I don't know",                                      "05"),
        ("Other (Specify)",                                   "06"),
    ]
    Q86_PREMIUMS = [
        ("Yes, I pay directly",       "1"),
        ("Yes, my employer pays",     "2"),
        ("No, I do not pay premiums", "3"),
    ]
    Q88_WHY_DIFFICULT = [
        ("Cannot afford the premium",                       "01"),
        ("Payment options are inconvenient",                "02"),
        ("No time to pay",                                  "03"),
        ("Don't see value in paying",                       "04"),
        ("System of PhilHealth is unreliable/usually down", "05"),
        ("I don't know",                                    "06"),
        ("Other (Specify)",                                 "07"),
    ]
    items = [
        select_one("Q79_HOW_FIND_OUT_REGISTER",
                   "79. How did you find out about how to register to PhilHealth?",
                   Q79_HOW_FIND_OUT, length=2),
        alpha("Q79_HOW_FIND_OUT_OTHER_TXT",
              "79. How find out -- Other (specify) text", length=120),
        select_one("Q80_ASSISTED_BY",
                   "80. Who assisted you in the registration process?",
                   Q80_ASSISTANCE, length=2),
        alpha("Q80_ASSISTED_BY_OTHER_TXT",
              "80. Assisted by -- Other (specify) text", length=120),
        yes_no("Q81_HAD_DIFFICULTIES",
               "81. Did you have any difficulties in the registration process?"),
        *select_all("Q82_DIFFICULTIES",
                    "82. What did you find difficult about the process?",
                    Q82_DIFFICULTIES),
        yes_no("Q83_KNOWS_WHERE_TO_SEEK",
               "83. Would you know where to go to seek assistance in registration?"),
        alpha("Q84_WHERE_TO_SEEK",
              "84. Where would you go to seek assistance?", length=200),
        *select_all("Q85_BENEFITS",
                    "85. What are some of the benefits that come with being a "
                    "PhilHealth member?",
                    Q85_BENEFITS),
        select_one("Q86_PAYS_PREMIUMS",
                   "86. Do you and members of your HH pay PhilHealth premiums "
                   "every month?",
                   Q86_PREMIUMS, length=1),
        yes_no("Q87_DIFFICULT_TO_PAY",
               "87. Do you find it difficult to pay the PhilHealth premiums "
               "every month?"),
        *select_all("Q88_WHY_DIFFICULT_TO_PAY",
                    "88. Why did you find it difficult?",
                    Q88_WHY_DIFFICULT),
    ]
    return record("H_PHILHEALTH",
                  "H. PhilHealth Registration and Health Insurance", "J", items)


def build_section_i():
    """I. Primary Care Utilization (Q89-Q100).

    Skip-routing (enforced in PROC):
      - Q89 = No (2) or I don't know (3) -> Q93 (skip Q90, Q91, Q92)
      - Q90 = No (2) -> Q96 (skip Q91, Q92, Q93, Q94, Q95)
      - Q93 only when Q89 = No / DK (no usual clinic)
    """
    Q89_HAS_USUAL = [
        ("Yes",          "1"),
        ("No",           "2"),  # proceed to Q93
        ("I don't know", "3"),  # proceed to Q93
    ]
    Q91_WHY_FACILITY = [
        ("This facility is more accessible than my usual facility (i.e., nearer, has more transportation options to get to, and cheaper to travel to)",   "01"),
        ("Needed a service/specialist not available at my usual facility",                                                                                "02"),
        ("Recommended by friends/family",                                                                                                                 "03"),
        ("Wanted to try another facility than my usual",                                                                                                  "04"),
        ("Prefer this facility than my usual",                                                                                                            "05"),
        ("This was referred to me by my usual facility",                                                                                                  "06"),
        ("Usual facility is closed for today",                                                                                                            "07"),
        ("The doctor I trust/familiar with transferred in this facility",                                                                                 "08"),
        ("Other (Specify)",                                                                                                                               "09"),
    ]
    Q92_FACILITY_TYPE = [
        ("YAKAP/Konsulta or primary care provider",      "01"),
        ("Barangay Health Center",                       "02"),
        ("Rural Health Unit / Health Center",            "03"),
        ("Public Hospital",                              "04"),
        ("Private Hospital",                             "05"),
        ("Private Clinic",                               "06"),
        ("Traditional Healer or Manghihilot/Albularyo",  "07"),
        ("I don't know",                                 "08"),
        ("Other (specify)",                              "09"),
    ]
    Q93_NO_USUAL_REASON = [
        ("I don't get sick",                  "01"),
        ("I recently moved into the area",    "02"),
        ("It's expensive",                    "03"),
        ("I can treat myself",                "04"),
        ("I don't know where to go for care", "05"),
        ("I don't know",                      "06"),
        ("Other (Specify)",                   "07"),
    ]
    Q94_TRANSPORT = [
        ("Walk",                              "01"),
        ("Bike",                              "02"),
        ("Public Bus",                        "03"),
        ("Jeepney",                           "04"),
        ("Tricycle",                          "05"),
        ("Car (including private taxi/cab)",  "06"),
        ("Motorcycle",                        "07"),
        ("Boat",                              "08"),
        ("Taxi",                              "09"),
        ("Pedicab",                           "10"),
        ("E-bike",                            "11"),
        ("Other (Specify)",                   "12"),
    ]
    Q98_YN_TRIED_DK = [
        ("Yes",            "1"),
        ("No",             "2"),
        ("I haven't tried", "3"),
        ("I don't know",   "4"),
    ]
    Q100_YN_TRIED_DK_NA = [
        ("Yes",            "1"),
        ("No",             "2"),
        ("I haven't tried", "3"),
        ("I don't know",   "4"),
        ("Not applicable", "5"),
    ]
    items = [
        select_one("Q89_HAS_USUAL_FACILITY",
                   "89. In the past 12 months, do you have a clinic, or health "
                   "center that you usually go to?",
                   Q89_HAS_USUAL, length=1),
        alpha("Q89_1_FACILITY_NAME",
              "89.1. What is the name of the facility?", length=200),
        yes_no("Q90_IS_USUAL_FOR_GENERAL",
               "90. Is this the facility you usually go to for general health "
               "concerns?"),
        *select_all("Q91_WHY_THIS_FACILITY",
                    "91. Why did you go to this facility?",
                    Q91_WHY_FACILITY),
        select_one("Q92_FACILITY_TYPE",
                   "92. What is the type of facility that you usually go to?",
                   Q92_FACILITY_TYPE, length=2),
        alpha("Q92_FACILITY_TYPE_OTHER_TXT",
              "92. Facility type -- Other (specify) text", length=120),
        *select_all("Q93_NO_USUAL_REASON",
                    "93. If not, why do you not have a usual clinic, or health "
                    "center that you usually go to?",
                    Q93_NO_USUAL_REASON),
        *select_all("Q94_TRANSPORT_MODE",
                    "94. What mode/s of transportation do you use when "
                    "travelling to the nearest primary care facility?",
                    Q94_TRANSPORT),
        alpha("Q95_TRAVEL_TIME_ONE_WAY",
              "95. How long does it take you to travel from your house when "
              "going to the nearest primary care facility? (one-way, HH:MM)",
              length=5),
        numeric("Q96_TRAVEL_COST_ONE_WAY",
                "96. How much does it usually cost for you to travel to this "
                "facility from your home? (Philippine pesos, ONE-WAY)",
                length=7),
        yes_no("Q97_KNOWS_HOW_TO_BOOK",
               "97. When you have a health problem, do you know how to book "
               "an appointment at a primary care facility?"),
        select_one("Q98_PHONE_ADVICE_WHEN_OPEN",
                   "98. When your primary care facility is open, can you get "
                   "advice quickly over the phone if you need it?",
                   Q98_YN_TRIED_DK, length=1),
        select_one("Q99_PHONE_WHEN_CLOSED",
                   "99. When your primary care facility is closed, is there a "
                   "phone number you can call when you get sick?",
                   Q98_YN_TRIED_DK, length=1),
        select_one("Q100_LEAVE_WORK_TO_VISIT",
                   "100. When you have to visit your primary care facility, do "
                   "you have to take a leave from work or school to go?",
                   Q100_YN_TRIED_DK_NA, length=1),
    ]
    return record("I_PRIMARY_CARE",
                  "I. Primary Care Utilization", "K", items)


def build_section_j():
    """J. Household members' Health-Seeking Behavior and Outcomes."""
    return record("J_HEALTH_SEEKING",
                  "J. Household members' Health-Seeking Behavior and Outcomes",
                  "L", [])


def build_section_k():
    """K. Experiences and Satisfaction with Referrals."""
    return record("K_REFERRALS",
                  "K. Experiences and Satisfaction with Referrals", "M", [])


def build_section_l():
    """L. NBB Awareness and Utilization."""
    return record("L_NBB",
                  "L. No Balance Billing (NBB) Awareness and Utilization",
                  "N", [])


def build_section_m():
    """M. ZBB Awareness and Utilization."""
    return record("M_ZBB",
                  "M. Zero Balance Billing (ZBB) Awareness and Utilization",
                  "O", [])


def build_section_n():
    """N. Household Expenditures (food, non-food, health products/services).

    Q144-Q176 plus the three "computed automatically in CAPI" totals
    Q177, Q182, Q185. Items land in a later commit.
    """
    return record("N_HH_EXPENDITURES",
                  "N. Household Expenditures", "P", [])


def build_section_o():
    """O. Sources of Funds for Health."""
    return record("O_HEALTH_FUNDING",
                  "O. Sources of Funds for Health", "Q", [])


def build_section_p():
    """P. Financial Risk Protection: Incidence of Reduced/Delayed Care."""
    return record("P_FINANCIAL_RISK",
                  "P. Financial Risk Protection: Incidence of "
                  "Reduced/Delayed Care", "R", [])


def build_section_q():
    """Q. Anxiety about Household Finances."""
    return record("Q_FINANCIAL_ANXIETY",
                  "Q. Anxiety about Household Finances", "S", [])


# ============================================================
# DICTIONARY ASSEMBLY
# ============================================================

def build_dictionary():
    """Assemble the F4 dictionary.

    Case-ID block: 5-item 12-digit decomposed scheme adopted 2026-05-05
    (see wiki/concepts/Questionnaire Numbering Convention.md). Replaced
    the legacy single 6-digit QUESTIONNAIRE_NO ID item; downstream
    consumers should reference the individual ID-item names rather than
    the retired composite name.

    F4 <-> F1 facility linkage derives from the shared first 9 digits of
    the case-ID (REGION_CODE + PROVINCE_HUC_CODE + CITY_MUNICIPALITY_CODE
    + FACILITY_NO). HH_LISTING_NO and F4_PARENT_F3_CASE_SEQ live in
    FIELD_CONTROL (see build_f4_field_control docstring).
    """
    records = [
        # Root record (recordType "1") -- required by CSPro hierarchy
        record("HOUSEHOLDSURVEY_REC", "HouseholdSurvey Record", "1", []),
        build_f4_field_control(),
        build_geo_id("household"),
        build_f4_household_capture(),
        build_f4_case_verification(),
        build_section_a(),
        build_section_b(),
        build_section_c(),
        build_section_c_private_insurance_gate(),
        build_section_c_private_insurance_roster(),
        build_section_d(),
        build_section_e(),
        build_section_f(),
        build_section_g(),
        build_section_h(),
        build_section_i(),
        build_section_j(),
        build_section_k(),
        build_section_l(),
        build_section_m(),
        build_section_n(),
        build_section_o(),
        build_section_p(),
        build_section_q(),
    ]

    return build_dictionary_from_helpers(
        dict_name="HOUSEHOLDSURVEY_DICT",
        dict_label="HouseholdSurvey",
        id_items=build_id_block(),
        records=records,
    )


def main():
    out_path = Path(__file__).parent / "HouseholdSurvey.dcf"
    dictionary = build_dictionary()
    out_path.write_text(json.dumps(dictionary, indent=2), encoding="utf-8")

    record_count = len(dictionary["levels"][0]["records"])
    item_count = sum(len(r["items"]) for r in dictionary["levels"][0]["records"])
    print(f"Wrote {out_path}")
    print(f"  Records: {record_count}")
    print(f"  Items:   {item_count}")


if __name__ == "__main__":
    main()
