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
    """C. Awareness on Universal Health Care (Q35-Q37)."""
    items = []
    return record("C_UHC_AWARENESS",
                  "C. Awareness on Universal Health Care", "E", items)


def build_section_d():
    """D. PhilHealth Registration and Health Insurance (Q38-Q52)."""
    items = []
    return record("D_PHILHEALTH",
                  "D. PhilHealth Registration and Health Insurance", "F", items)


def build_section_e():
    """E. Primary Care Utilization (Q53-Q82)."""
    items = []
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
