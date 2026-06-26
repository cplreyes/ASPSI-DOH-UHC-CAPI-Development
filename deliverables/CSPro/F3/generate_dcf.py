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

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import (
    YES_NO, YES_NO_DK, YES_NO_NA, UHC9_OPTIONS, SATISFACTION_5PT,
    numeric, alpha, yes_no, yes_no_dk, yes_no_na,
    select_one, select_all, checkbox_multiselect, uhc9_item, record,
    build_field_control, build_geo_id, build_dictionary, build_id_block, write_dcf,
    derived_geo_code_items, ENUM_RESULT_OPTIONS_F3,
    apply_translations,
    _gps_fields, _photo_block,
)


def _cb_codes(options):
    """#529: re-code a select_all option list for checkbox_multiselect — real
    options -> 01,02,...; 'Other (specify)' -> 99; a standalone exclusive option
    ('None…', 'No initiatives', 'I don't know') -> 90. Fixed-width 2-char codes in
    the 9x range for specials so pos() membership tests can't false-match (matches
    the Q148 convention). The 01.. order is preserved, so any gate logic that
    references option N by position stays valid. Ported from F1's generate_dcf.py
    for the 13-question F3 select_all -> Check Box conversion.

    F3 fix vs the F1 original: the don't-know exclusive is matched as a (near-)whole
    option phrase, NOT as a substring. F3 carries substantive options that merely
    CONTAIN 'don't know' — Q65 'I don't know where to go for care', Q171 'Don't know
    how to get to facility' — which F1's `"don't know" in low` substring test wrongly
    collapsed to the exclusive code 90 (two options -> same code; a real reason lost).
    Whole-phrase matching keeps those as ordinary 01.. options."""
    out, n = [], 0
    for text, _ in options:
        low = text.strip().lower()
        # normalised phrase (strip leading 'i ', trailing punctuation) for the
        # don't-know exclusive test — must be the WHOLE option, not a prefix of a
        # longer reason like "I don't know where to go for care".
        norm = re.sub(r"\s+", " ", low).strip().rstrip(".").strip()
        norm = re.sub(r"^i\s+", "", norm)
        is_dont_know = norm in ("don't know", "dont know")
        # #673: match the 'Other (specify)' box by the 'specif' marker ONLY — NOT by a bare
        # 'other' prefix. A substantive option that merely STARTS with 'Other' (Q85 'Other
        # infection (e.g. urine, skin...)') is not the specify box; the old startswith('other')
        # test collided it onto code 99, duplicating the Other-specify code and mis-firing the
        # pos("99", base) _OTHER_TXT gate. Every real Other-specify box contains 'specify'.
        if "specif" in low:
            out.append((text, "99"))
        elif low.startswith(("none", "no initiative")) or is_dont_know:
            out.append((text, "90"))
        else:
            n += 1
            out.append((text, f"{n:02d}"))
    return out


def _build_payment_roster(record_name, label, q_no, payment_src, amt_codes,
                          record_type, src_label, amt_label, amt_length=8,
                          display_no=None):
    """Option B payment-matrix roster (pilot 2026-06-18). One occurrence per ticked
    source code from the question's CheckBox field; renders as a grid (source | amount).
    Fields:
      <q>_PAY_LINE  numeric 1  — auto = curocc(); auto-ends the roster (apc preproc).
      <q>_PAY_SRC   numeric 2  — auto-set to the curocc()-th ticked source, protected.
      <q>_PAY_AMT   numeric N  — peso amount; the apc preproc zeroes it for source codes
                                 NOT in amt_codes (so only money sources prompt an amount;
                                 free / charged-to-X / DK rows default 0 but stay enterable).
    `amt_length` matches the matrix it replaces (Section G = 8, Section H bills = 9).
    max_occurs = number of sources. The driving CheckBox field (<q>_SOURCES) lives in
    the host section record; this roster record is spliced into the dictionary's record
    list immediately after it so the grid renders right after the tick-list.
    `amt_codes` is carried for documentation/symmetry; the apc owns the gate logic."""
    # #751: field NAMES can't carry a dot, so the decimal questions use q_no 971/972;
    # the DISPLAYED row number must read "97.1"/"97.2", not "971"/"972". display_no
    # overrides the shown number (SRC/AMT labels already show it via src_label/amt_label).
    disp = display_no if display_no is not None else str(q_no)
    items = [
        numeric(f"Q{q_no}_PAY_LINE", f"{disp} Payment row", length=1),
        select_one(f"Q{q_no}_PAY_SRC", src_label, payment_src, length=2),
        numeric(f"Q{q_no}_PAY_AMT", amt_label, length=amt_length),
    ]
    # required=False: if (defensively) no source is ticked the apc endgroups at
    # occurrence 1, leaving 0 rows — required=True would then hard-block at endlevel.
    return record(record_name, label, record_type, items,
                  max_occurs=len(payment_src), required=False)


def _build_lab_payment_roster(record_name, label, record_type, lab_value_set,
                              payment_type, max_labs, amt_length=8):
    """Q94 per-lab payment roster (#450, 2026-06-20). Paper (Apr-20, p.13): "How much was
    the cost of [laboratory test: ___]? To be asked for EACH lab test ticked in Q93." So the
    roster repeats once per LAB ticked in Q93_LABS (not per payment source — the earlier
    Q94_SOURCES build was the wrong axis). Row identity = the lab (auto-set from the
    curocc()-th ticked Q93 lab, protected; the select_one label shows the test name in the
    grid's first column). The PAYMENT TYPE is entered per lab; the amount is enterable only
    for Out-of-pocket(01).
    Fields:
      Q94_LAB_LINE  numeric 1  — auto = curocc(); ends the roster (apc preproc).
      Q94_LAB_CODE  numeric 2  — auto-set to the curocc()-th ticked Q93 lab code, protected.
      Q94_LAB_PAY   numeric 2  — payment type for this lab (entered; select_one).
      Q94_LAB_AMT   numeric N  — peso amount; apc gates entry to Out-of-pocket(01) only.
    max_occurs = max selectable labs (Q93 codes 01..15 + Other 99; None excluded)."""
    items = [
        numeric("Q94_LAB_LINE", "94. Lab payment row", length=1),
        select_one("Q94_LAB_CODE",
                   "94. Laboratory test (auto-filled from the tests ticked in Q93)",
                   lab_value_set, length=2),
        select_one("Q94_LAB_PAY",
                   "94. How was the cost of this laboratory test paid?",
                   payment_type, length=2),
        numeric("Q94_LAB_AMT",
                "94. Amount paid out-of-pocket for this laboratory test (Pesos)",
                length=amt_length),
    ]
    # required=False: if (defensively) only None is ticked the apc endgroups at occurrence
    # 1, leaving 0 rows — required=True would then hard-block at endlevel.
    return record(record_name, label, record_type, items,
                  max_occurs=max_labs, required=False)


def _split_host_with_rosters(host_base, host_label, host_type, items,
                             roster_specs, cont_types):
    """Fan-out helper (2026-06-19): split ONE host section's item list around every
    `_SOURCES` CheckBox in `roster_specs`, interleaving each roster record right after
    its driving CheckBox — the generalisation of the hand-written Q92/Q97.1 split.

    `roster_specs` maps a `_SOURCES` field name -> a built roster record dict (from
    `_build_payment_roster`). The CheckBox itself stays in the host fragment that ends
    at it; the roster grid renders next; the following items go into the next host
    continuation fragment. `cont_types` is the list of free record-type letters for the
    host continuation fragments (one per split AFTER the first). Returns the ordered
    record list [host, roster, host_2, roster, host_3, ...]."""
    # canonical positions of each split field, in item order
    cuts = sorted((next(i for i, it in enumerate(items) if it["name"] == src) + 1, src)
                  for src in roster_specs)
    out, start, frag = [], 0, 0
    for cut_at, src in cuts:
        if frag == 0:
            out.append(record(host_base, host_label, host_type, items[start:cut_at]))
        else:
            out.append(record(f"{host_base}_{frag + 1}", f"{host_label} (cont.{'' if frag == 1 else ' ' + str(frag)})",
                              cont_types[frag - 1], items[start:cut_at]))
        out.append(roster_specs[src])
        start, frag = cut_at, frag + 1
    # trailing fragment after the last roster
    out.append(record(f"{host_base}_{frag + 1}", f"{host_label} (cont.{'' if frag == 1 else ' ' + str(frag)})",
                      cont_types[frag - 1], items[start:]))
    return out


# ============================================================
# FIELD CONTROL — paper FC block + PATIENT_TYPE (OP/IP routing gate)
# ============================================================

def build_f3_field_control():
    # PATIENT_TYPE stays (off the paper FC box, but it's the master OP/IP
    # routing gate — PATIENT_TYPE=1 Outpatient → Section G, =2 Inpatient →
    # Section H). PATIENT_LISTING_NO removed 2026-06-12 (unnecessary input;
    # the 12-digit Questionnaire Number already identifies the case).
    extra = [
        numeric("PATIENT_TYPE", "Type of Patient", length=1,
                value_set_options=[("Outpatient", "1"), ("Inpatient", "2")]),
        # #515 break-off control — shares the case-start (PATIENT_TYPE) screen, so
        # it sits in the case tree from the very first field. Its postproc routes a
        # non-Continue choice straight to the closing Result-of-Visit, letting the
        # enumerator end a withdrawn/postponed interview without walking every
        # required question. Default "Continue" is set in logic (BREAKOFF preproc).
        numeric("BREAKOFF",
                "Interview status (leave as Continue unless ending the interview early)",
                length=1,
                value_set_options=[
                    ("Continue interview",        "1"),
                    ("Respondent withdrew",       "2"),
                    ("Postponed / reschedule",    "3"),
                    ("Stop — other (incomplete)", "4"),
                ]),
        # #561 completeness sentinel — OFF-FORM, set in logic only: 0 In progress at
        # case open, 1 Completed when the Result-of-Visit finalises to a completed
        # code, 2 Partial/broke-off otherwise. Lets the Supervisor App + CSWeb exports
        # tell complete from partial even for a force-quit case (which never reaches
        # the closing form, so it stays 0). See docs/.../supervisor-app-design.md.
        numeric("CASE_DISPOSITION", "Case disposition (auto)", length=1,
                value_set_options=[
                    ("In progress",             "0"),
                    ("Completed",               "1"),
                    ("Partial / not completed", "2"),
                ]),
    ]
    return build_field_control(survey_code="F3", extra_items=extra + derived_geo_code_items(),
                               date_label_entity="the Patient",
                               result_options=ENUM_RESULT_OPTIONS_F3)


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
        # #545 (Carl go/no-go 2026-06-20): 'Not Applicable' for patients with no income source
        # — e.g. a minor / not-yet-working-age patient. Code 98 (special, outside the 1-5
        # working-category range used by the Q16/Q17 employment-consistency check, so it does
        # not affect that check). Q18 household-income still applies (household-level, not
        # personal), so no Q18 skip is added.
        # #760: display "I don't know" before "Not Applicable" (match Q16 order, per tester);
        # codes unchanged (NA=98, DK=99) so no data / consistency-check impact.
        ("Not Applicable",                                     "98"),
    ]
    # #631 (ASPSI updated questionnaire, 2026-06-17): income categories revised to
    # 11 contiguous 50k bands (was 6 uneven bands). 2-digit codes (field length 2).
    # NOTE: the tester's printed "150,000 - 199,000" is a transcription typo —
    # corrected to 199,999 to keep the bands contiguous and non-overlapping with the
    # 200,000 band (every other band ends in 9,999). Flagged for ASPSI confirmation.
    Q18_BRACKET = [
        ("Under 50,000",      "01"),
        ("50,000 - 99,999",   "02"),
        ("100,000 - 149,999", "03"),
        ("150,000 - 199,999", "04"),
        ("200,000 - 249,999", "05"),
        ("250,000 - 299,999", "06"),
        ("300,000 - 349,999", "07"),
        ("350,000 - 399,999", "08"),
        ("400,000 - 449,999", "09"),
        ("450,000 - 499,999", "10"),
        ("500,000 and above", "11"),
        ("Don't know",        "99"),   # #398: respondent doesn't know even the estimate; out-of-range so the bracket<->amount + SEC cross-checks bypass it
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
        # #762 missing-value standard: relabel DK + add Refuse, both [DO NOT READ OUT LOUD].
        ("I don't know [DO NOT READ OUT LOUD]",                                                "4"),
        ("Refuse to answer [DO NOT READ OUT LOUD]",                                            "5"),
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
                   "8. Is the patient part of the LGBTQIA+ community? (e.g., gay, lesbian, bisexual, etc.). It is fine if not comfortable answering.",
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
                "Please specify in Philippine pesos. — Approximate amount "
                "(enter -98 if the patient doesn't know, or -99 if they refuse to answer — do not read these codes aloud)",
                length=8),
        select_one("Q18_INCOME_BRACKET",
                   "18. Income category corresponding to the respondent's approximate household income",
                   Q18_BRACKET, length=2),   # #631: 11 brackets -> 2-digit codes
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
        *checkbox_multiselect("Q36_UHC_SOURCE",
                    "36. What is your source of information about UHC?",
                    _cb_codes(Q36_SOURCE), with_other_txt=True),
        *checkbox_multiselect("Q37_UHC_UNDERSTAND",
                    "37. What is your understanding about UHC?",
                    _cb_codes(Q37_UNDERSTANDING), with_other_txt=True),
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
        *checkbox_multiselect("Q42_DIFFICULTY",   # #635: select_all -> Check Box (tick-all)
                    "42. What did you find difficult about the process?",
                    _cb_codes(Q42_DIFFICULTY), with_other_txt=True),
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
        *checkbox_multiselect("Q46_BENEFITS",
                    "46. What are some of the benefits that come with being a PhilHealth member?",
                    _cb_codes(Q46_BENEFITS), with_other_txt=True),
    ]
    for name, label in Q47_PACKAGES:
        items.append(yes_no(name, label))
    items.extend([
        select_one("Q48_PREMIUM_PAY",
                   "48. Do you pay PhilHealth premiums every month?", Q48_PAY, length=1),
        yes_no("Q49_PREMIUM_DIFFICULT",
               "49. Do you find it difficult to pay your PhilHealth premium every month?"),
        *checkbox_multiselect("Q50_DIFFICULTY_PAYING",   # #639: select_all -> Check Box (tick-all)
                    "50. Why did you find it difficult?",
                    _cb_codes(Q50_DIFFICULTY_PAYING), with_other_txt=True),
        yes_no("Q51_OTHER_INSURANCE",
               "51. Are you registered with another health insurance plan?"),
        *checkbox_multiselect("Q52_PLANS",   # #640: select_all -> Check Box (tick-all)
                    "52. Which health insurance plan/s are you enrolled in?",
                    _cb_codes(Q52_PLANS), with_other_txt=True),
    ])
    return record("D_PHILHEALTH_REG",
                  "D. PhilHealth Registration and Health Insurance", "F", items)


# ============================================================
# Section E. Primary Care Utilization (Q53-Q82) — Apr 20
# ============================================================

def build_section_e():
    Q54_PROVIDER = [
        # #787 (R5): inline definitions appended per tester (codes unchanged -> no data impact).
        ("General practitioner (a doctor who is qualified for medical practice)",                       "1"),
        ("Specialty Care Provider/ Specialist (a doctor with more expertise in specific areas of health)", "2"),
        ("Both",                                    "3"),
        ("Other (specify)",                         "4"),
        ("None",                                    "5"),
        # #729 (tester/Carl, reverses #412): 'None' re-added as an explicit no-type escape.
        # Appended as code 5 so "Other (specify)" stays code 4 (the dcf-driven other-specify
        # gate on Q54_PCP_TYPE_OTHER_TXT is undisturbed). Q53=No still skips Q54->Q63; None here
        # is for a Q53=Yes respondent who has no fitting provider type. No special routing —
        # falls through to Q55 like the other answers.
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
        # #770 (R5): 'I've never heard of it' (3) RESTORED to the paper value set + routes to Q83,
        # reversing #430's removal. ASPSI tester re-requested it (matches spec §4 line 270).
        # Note for ASPSI: Q77 is only reached when Q74=Yes (has heard of YAKAP/Konsulta), so (3) is
        # logically redundant here — restored per tester + paper; downstream cleanup is ASPSI's call.
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
        *checkbox_multiselect("Q59_SCHED_COMM",   # #669: select_all -> Check Box (tick-all)
                    "59. What mode/s of communication was/were available to you when scheduling a "
                    "consultation with your main primary care provider?", _cb_codes(COMM_MODES)),
        yes_no("Q60_SCHED_TELECON_OK",
               "60. If teleconsultation was available, did you succeed in using the teleconsult? (scheduling)"),
        *checkbox_multiselect("Q61_CONSULT_COMM",   # #669: select_all -> Check Box (tick-all)
                    "61. What mode/s of communication was/were available to you when consulting with "
                    "your main primary care provider?", _cb_codes(COMM_MODES)),
        yes_no("Q62_CONSULT_TELECON_OK",
               "62. If teleconsultation was available, did you succeed in using the teleconsult? (consultation)"),
        yes_no("Q63_HAS_USUAL_FACILITY",
               "63. In the past 12 months, do you have a clinic, or health center that you usually go to?"),
        alpha("Q64_FACILITY_NAME",
              "64. What is the name of the facility?", length=120),
        *checkbox_multiselect("Q65_WHY_NO_USUAL",
                    "65. If none, why do you not have a usual clinic, or health center that you usually go to?",
                    _cb_codes(Q65_WHY_NOT), with_other_txt=True),
        yes_no("Q66_SAME_AS_USUAL",
               "66. Is [facility_name_input] the facility you usually go to for general health concerns?"),
        *checkbox_multiselect("Q67_WHY_THIS_FACILITY",
                    "67. Why did you go to this facility instead of your usual facility?",
                    _cb_codes(Q67_WHY_THIS), with_other_txt=True),
        # select_all() above already emits the canonical Q67_WHY_THIS_FACILITY_OTHER_TXT
        # (gated on the 'Other' option flag). A second standalone Q67_WHY_THIS_OTHER_TXT used to
        # live here — a duplicate with no option flag, i.e. an ungated free-text box on the form.
        # Removed 2026-06-12 (other-specify audit).
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
        *checkbox_multiselect("Q70_USUAL_TRANSPORT",   # #670: select_all -> Check Box (tick-all)
                    "70. What mode/s of transportation do you use when travelling to the health facility "
                    "that you usually go to?", _cb_codes(TRANSPORT), with_other_txt=True),
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
        *checkbox_multiselect("Q73_NEAREST_TRANSPORT",   # #670: select_all -> Check Box (tick-all)
                    "73. What mode/s of transportation do you use when travelling to the nearest "
                    "primary care facility?", _cb_codes(TRANSPORT), with_other_txt=True),
        yes_no("Q74_KON_HEARD",
               "74. Have you heard of the term \"YAKAP/ Konsulta package\"?"),
        *checkbox_multiselect("Q75_KON_SOURCE",   # #671: select_all -> Check Box (tick-all)
                    "75. What are your sources of information about the YAKAP/Konsulta package?",
                    _cb_codes(Q75_KON_SOURCE), with_other_txt=True),
        *checkbox_multiselect("Q76_KON_UNDERSTAND",
                    "76. What is your understanding about the YAKAP/Konsulta package?",
                    _cb_codes(Q76_KON_UNDERSTAND), with_other_txt=True),
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
        *checkbox_multiselect("Q82_KON_WHY_NOT_REG",   # #671: select_all -> Check Box (tick-all)
                    "82. Why are you NOT registered with a YAKAP/Konsulta package provider?",
                    _cb_codes(Q82_WHY_NOT_REG), with_other_txt=True),
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
        ("Other (Specify)",                                                                   "99"),   # #438: none-of-the-above escape (e.g. came for a consult but couldn't see the doctor)
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
        *checkbox_multiselect("Q85_CONDITIONS",   # #673: select_all -> Check Box (tick-all)
                    "85. What condition/s do/es the patient usually visit the facility for?",
                    _cb_codes(Q85_CONDITIONS), with_other_txt=True),
        *checkbox_multiselect("Q86_VISIT_EVENTS",   # #673: select_all -> Check Box (tick-all)
                    "86. Which of the following happened during the patient's most recent visit?",
                    _cb_codes(Q86_VISIT_EVENTS), with_other_txt=True),   # #438: + 'Other (Specify)'
        *checkbox_multiselect("Q87_OTHER_ACTIONS",   # #673: select_all -> Check Box (tick-all)
                    "87. Apart from this visit, has the patient done anything else to improve "
                    "his/her health condition or address his/her health concern?",
                    _cb_codes(Q87_OTHER_ACTIONS), with_other_txt=True),
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
    # Q97.1 — Option B (2-form flat) pilot (2026-06-19). WAS a per-option Yes/No +
    # gated _AMT loop (one field per screen, ~8 screens). NOW a single CheckBox
    # "tick all that apply" (Q971_SOURCES) on one screen, then the four amount boxes
    # on ONE shared screen (non-ticked options protected+zeroed by the apc, NOT
    # skipped — so no skip boundary fragments the amounts' DisplayTogether block).
    # 2-char codes 01..04 so pos("0n", Q971_SOURCES) lines up with Q971_n_AMT; Other
    # is 04 (kept numeric, NOT recoded to 99) so the n<->amount mapping is 1:1. The
    # 'Other expenses' specify text (Q971_OTHER_TXT) is gated on pos("04",...) by a
    # bespoke apc PROC and emitted AFTER the amounts so the four amounts stay a strictly
    # consecutive run that the Q971_AMOUNTS named block can match.
    Q971_SOURCES = [
        ("Consultation Fee",                          "01"),
        ("Medical equipment or supplies",             "02"),
        ("Non-medical expenses (e.g. Hygiene kit)",   "03"),
        ("Other expenses",                            "04"),
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
        # #789: inline definitions appended per tester (codes unchanged -> no data impact).
        ("Medical consultation for urgent or minor conditions (e.g., fevers, flu-like symptoms, Urinary tract infections (UTIs), sprains, small burns, etc.)", "1"),
        ("Outpatient or ambulatory care services",                            "2"),
        ("Basic diagnostic services (e.g., laboratory tests, X-ray)",         "3"),
        ("Minor procedures or treatments (e.g., wound suturing, biopsies, and other conditions requiring minimal anesthesia and a short recovery time)", "4"),
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
        *checkbox_multiselect("Q90_NOT_CONFINED",   # #673: select_all -> Check Box (tick-all)
                    "90. What were the reasons why you were not confined/ admitted in a hospital/clinic?",
                    _cb_codes(Q90_NOT_CONFINED), with_other_txt=True),
        yes_no("Q91_USUAL_OUTPATIENT",
               "91. Do you usually avail consultation services for outpatient care?"),
    ]
    # Q92 consultation cost — Option B ROSTER redesign (pilot, 2026-06-18).
    # WAS a flat 8-source Yes/No matrix + per-source _AMT (#446). NOW a single CheckBox
    # "which sources paid" (Q92_SOURCES) feeding a repeating roster (Q92_PAY_ROSTER —
    # one row per ticked source, amount inline). Only Out-of-pocket(01) + Donation(02)
    # carry an amount; the roster's apc preproc protects+zeroes the amount for every
    # other source code. The roster record is spliced into the dictionary record list
    # right after this (split) record — see the return below.
    # #781 (ASPSI 2026-06-25): In-kind(07) is a peso-amount source for Q92 — added to the
    # money set (apc Q92_PAY_AMT gate owns the logic; this set is documentation-only).
    Q92_AMT_CODES = {"01", "02", "07"}
    items.extend(checkbox_multiselect(
        "Q92_SOURCES",
        "92. Which of the following did you use to pay for the cost of consultation? "
        "(Tick all that apply.)",
        Q92_PAYMENT_SRC, with_other_txt=False))
    items.extend([
        *checkbox_multiselect("Q93_LABS",   # #673: select_all -> Check Box (tick-all)
                    "93. Did you have any of the following laboratory tests done during your outpatient care?",
                    _cb_codes(Q93_LABS), with_other_txt=True),
        # NOTE: checkbox_multiselect(with_other_txt=True) auto-emits Q93_LABS_OTHER_TXT
        # (gated on pos("99", base)); the old standalone alpha("Q93_LABS_OTHER_TXT") was
        # removed to avoid a duplicate dcf item (#673).
    ])
    # Q94 lab test cost — PER-LAB roster rebuild (#450, 2026-06-20). The Apr-20 paper (p.13)
    # asks Q94 ONCE PER LAB ticked in Q93 ("How much was the cost of [laboratory test]? To be
    # asked for each lab test ticked in Q93."), NOT one aggregate payment. The old Q94_SOURCES
    # CheckBox (a by-source roster) was the wrong axis and is removed; Q94 is now
    # Q94_LAB_ROSTER, driven by the Q93_LABS ticks and spliced in right after the Q93 block
    # (see g_rosters below). Payment options per the paper (7 — no Donation; only OOP carries
    # an amount).
    Q94_PAYMENT_TYPE = [
        ("Out-of-pocket",                     "01"),
        ("Free/no cost",                      "02"),
        ("Free, charge to PhilHealth",        "03"),
        ("Free, charge to Private Insurance", "04"),
        ("Free, charge to HMO",               "05"),
        ("In kind",                           "06"),
        ("Don't know",                        "07"),
    ]
    # Q94_LAB_CODE value set = the Q93 lab options recoded the same way as the Q93_LABS
    # CheckBox (01..15 labs, Other 99; None 90 excluded — None has no Q94 row). The
    # select_one label shows the test name in the roster's first column.
    Q94_LAB_VALUE_SET = [(lbl, c) for lbl, c in _cb_codes(Q93_LABS) if c != "90"]
    items.extend([
        yes_no("Q95_PRESCRIBED",
               "95. Were you prescribed medicine/s after your check-up?"),
    ])
    # Q96 prescribed meds cost — Option B ROSTER fan-out (#675, 2026-06-19). WAS a flat
    # 8-source Yes/No matrix where only Out-of-pocket(01) + In-kind(06) + Donation(07)
    # carried an amount (#453). NOW a CheckBox (Q96_SOURCES, the 8 Q96_MEDS_PAY codes)
    # feeding a roster (Q96_PAY_ROSTER); PARTIAL — only codes 01/07 carry an amount
    # (Q92 pattern), every other row defaults 0 but stays enterable. #779 (2026-06-25):
    # In-kind(06) dropped from the amount set per ASPSI's per-question clarification — the
    # apc (build_roster_procs amt_codes) owns the gate; this set is documentation-only.
    Q96_AMT_CODES = {"01", "07"}
    items.extend(checkbox_multiselect(
        "Q96_SOURCES",
        "96. Which of the following did you use to pay for the prescribed medicines? "
        "(Tick all that apply.)",
        Q96_MEDS_PAY, with_other_txt=False))
    items.append(numeric("Q97_FINAL_AMOUNT",
                         "97. What was the final amount you paid in cash for your outpatient care? "
                         "(Amount in Pesos)", length=8))
    # Q97.1 other expenses in bill — Option B ROSTER (Shape B, 2026-06-19).
    # Supersedes the undeployed 2-form-flat layout (4 flat Q971_n_AMT fields removed).
    # SCREEN 1: Q971_SOURCES CheckBox (tick all that apply).
    # SCREEN 2: Q971_ROSTER grid — one row per ticked category, all rows enterable for
    # amount (every category carries an amount, so no zeroing/gating per row).
    # SCREEN 3: Q971_OTHER_TXT gated on pos("04", Q971_SOURCES) (own screen after roster).
    items.extend(checkbox_multiselect(
        "Q971_SOURCES",
        "97.1 Which other items were included in your outpatient bill? "
        "(Tick all that apply.)",
        Q971_SOURCES, with_other_txt=False))   # OTHER_TXT emitted after roster split
    items.append(alpha("Q971_OTHER_TXT",
                       "97.1 Other expenses — specify text", length=120))
    # Q97.2 other expenses not in bill — Option B ROSTER fan-out (#689, 2026-06-19). WAS a
    # flat 6-item Yes/No + per-item _AMT matrix (every item carried an amount). NOW a
    # CheckBox (Q972_SOURCES) feeding a roster (Q972_PAY_ROSTER); ALL-amount (Q971 pattern,
    # every ticked row enterable, no per-row gating). Codes widened 1->2 chars (01..06) so
    # the roster's pos("0n", …) membership idiom lines up (the proven Q92/Q971 convention).
    # 'f) Other expenses' (06) gates Q972_OTHER_TXT after the grid (own screen), mirroring
    # Q971_OTHER_TXT on code 04.
    Q972_SOURCES = [(label, f"{int(code):02d}") for label, code in Q972_EXPENSES]
    items.extend(checkbox_multiselect(
        "Q972_SOURCES",
        "97.2 Which other expenses did you have during the OPD visit that were NOT in the "
        "bill? (Tick all that apply.)",
        Q972_SOURCES, with_other_txt=False))
    items.append(alpha("Q972_OTHER_TXT",
                       "97.2 Other expenses — specify text", length=120))
    # Q98 sources of money for medical costs — Option B ROSTER fan-out (#689, 2026-06-19).
    # WAS a flat 15-source Yes/No + per-source _AMT matrix (every source carried an amount).
    # NOW a CheckBox (Q98_SOURCES) feeding a roster (Q98_PAY_ROSTER); ALL-amount (Q971
    # pattern). Two gated specify texts follow the grid: Q98_OTHER_DONATION_TXT on code 06
    # and Q98_OTHER_TXT on code 15 (re-pointed from the old Q98_PAY_06 / Q98_PAY_15 flags
    # to pos("06"/"15", Q98_SOURCES) in the apc).
    items.extend(checkbox_multiselect(
        "Q98_SOURCES",
        "98. Which of the following did you use to pay for the medical costs? "
        "(Tick all that apply.)",
        Q98_SOURCES, with_other_txt=False))
    items.append(alpha("Q98_OTHER_DONATION_TXT",
                       "98. Other Donation/Charity/Assistance from Government Organization — specify text",
                       length=120))
    items.append(alpha("Q98_OTHER_TXT",
                       "98. Other payment source — specify text", length=120))
    # BUCAS block (Q99-104)
    items.extend([
        # #464: area-type gate — Q99-Q104 apply only to areas WITH a BUCAS center; No -> skip the whole block (mirrors Q99=No -> Q116)
        yes_no("AREA_HAS_BUCAS",
               "Does this area have a Bagong Urgent Care and Ambulatory Services (BUCAS) center? (Q99-Q104 apply only to areas with a BUCAS center.)"),
        yes_no("Q99_BUCAS_HEARD",
               "99. Have you heard about Bagong Urgent Care and Ambulatory Services (BUCAS) center?"),
        *checkbox_multiselect("Q100_BUCAS_SOURCE",   # #690: select_all -> Check Box (tick-all)
                    "100. If yes, what are your sources of information about this BUCAS center?",
                    _cb_codes(Q100_BUCAS_SOURCE), with_other_txt=True),
        *checkbox_multiselect("Q101_BUCAS_UNDERSTAND",
                    "101. What is your understanding about a BUCAS center?",
                    _cb_codes(Q101_BUCAS_UNDERSTAND), with_other_txt=True),
        yes_no("Q102_BUCAS_ACCESSED",
               "102. Have you accessed the services in a BUCAS center?"),
        *checkbox_multiselect("Q103_BUCAS_SERVICES",   # #690: select_all -> Check Box (tick-all)
                    "103. If yes, which service/s did you avail?",
                    _cb_codes(Q103_BUCAS_SERVICES), with_other_txt=True),
        select_one("Q104_WITHOUT_BUCAS",
                   "104. Without BUCAS Center, where would you have gone?",
                   Q104_ALT, length=1),
        alpha("Q104_WITHOUT_BUCAS_OTHER_TXT",
              "104. Without BUCAS — Others specify text", length=120),
    ])
    # Option B fan-out (2026-06-19): SIX cost matrices in Section G are now CheckBox ->
    # roster (Q92 consultation, Q94 lab, Q96 meds, Q97.1 other-in-bill, Q97.2 other-not-in-
    # bill, Q98 sources-of-money). Each `_SOURCES` CheckBox splits the host record; its
    # roster grid renders right after. `_split_host_with_rosters` interleaves them.
    # Record types: Q92 keeps 'O' (deployed pilot); the rest use free letters. Host
    # continuation fragments get a separate free-letter pool. (A-R, X-Z, plus O/P/Q/R from
    # the old pilot were used; we reassign cleanly here.)
    g_rosters = {
        "Q92_SOURCES": _build_payment_roster(
            "Q92_PAY_ROSTER", "G. Cost of consultation — amount by source", 92,
            Q92_PAYMENT_SRC, Q92_AMT_CODES, "O",
            "92. Payment source (auto-filled from the ticked sources)",
            "92. Amount paid for the consultation, by source (Pesos)"),
        # Q94 PER-LAB roster (#450): keyed on Q93_LABS_OTHER_TXT (the last item of the Q93
        # block) so the grid renders AFTER Q93's Other-specify and before Q95. One row per
        # ticked lab; reuses record type "S" (freed from the removed Q94_PAY_ROSTER).
        "Q93_LABS_OTHER_TXT": _build_lab_payment_roster(
            "Q94_LAB_ROSTER", "G. Cost of laboratory tests — per test (Q94)", "S",
            Q94_LAB_VALUE_SET, Q94_PAYMENT_TYPE, max_labs=len(Q94_LAB_VALUE_SET)),
        "Q96_SOURCES": _build_payment_roster(
            "Q96_PAY_ROSTER", "G. Cost of prescribed medicines — amount by source", 96,
            Q96_MEDS_PAY, Q96_AMT_CODES, "T",
            "96. Payment source (auto-filled from the ticked sources)",
            "96. Amount spent for the prescribed medicines, by source (Pesos)"),
        "Q971_SOURCES": _build_payment_roster(
            "Q971_ROSTER", "G. Other items in outpatient bill — amount by category", 971,
            Q971_SOURCES, set(),   # amt_codes=empty: every category carries an amount
            "Q",
            "97.1 Category (auto-filled from the ticked items)",
            "97.1 Amount charged for this item (Pesos)", display_no="97.1"),
        "Q972_SOURCES": _build_payment_roster(
            "Q972_PAY_ROSTER", "G. Other expenses not in bill — amount by item", 972,
            Q972_SOURCES, set(),   # all-amount: every ticked item carries an amount
            "U",
            "97.2 Expense item (auto-filled from the ticked items)",
            "97.2 Amount for this expense (Pesos)", display_no="97.2"),
        "Q98_SOURCES": _build_payment_roster(
            "Q98_PAY_ROSTER", "G. Sources of money for medical costs — amount by source", 98,
            Q98_SOURCES, set(),   # all-amount: every ticked source carries an amount
            "V",
            "98. Source of money (auto-filled from the ticked sources)",
            "98. Amount from this source (Pesos)"),
    }
    # Host continuation fragments (one per split after the first): G_2..G_7 (6 needed).
    return _split_host_with_rosters(
        "G_OUTPATIENT_CARE", "G. Outpatient Care", "I", items, g_rosters,
        cont_types=["P", "W", "a", "b", "c", "d"])


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
    # Q107 total bill — Option B ROSTER fan-out (#691, 2026-06-19). WAS a flat 10-source
    # Yes/No + per-source _AMT matrix (every source carried an amount). NOW a CheckBox
    # (Q107_SOURCES) feeding a roster (Q107_PAY_ROSTER); ALL-amount (Q971 pattern, length-9
    # peso amounts to match the bill scale). 'Other' (10) gates Q107_PAY_OTHER_TXT.
    items.extend(checkbox_multiselect(
        "Q107_SOURCES",
        "107. Which of the following did you use to pay for the total bill for confinement? "
        "(Tick all that apply.)",
        Q107_PAYMENT, with_other_txt=False))
    items.append(alpha("Q107_PAY_OTHER_TXT",
                       "107. Total bill — Other, specify text", length=120))
    items.append(yes_no("Q108_MEDS_OUTSIDE",
                        "108. Other than the medicine/s indicated in the hospital bill, did the patient "
                        "buy medicine/s from any pharmacy/facility outside the hospital?"))
    # Q109 meds outside — Option B ROSTER fan-out (#692, 2026-06-19). WAS a flat 9-source
    # Yes/No + per-source _AMT matrix. NOW a CheckBox (Q109_SOURCES) feeding a roster
    # (Q109_PAY_ROSTER); ALL-amount (Q971 pattern, length-9). 'Other' (09) gates
    # Q109_PAY_OTHER_TXT. The >=1-source requirement (#556) is the CheckBox's own >=1 gate.
    items.extend(checkbox_multiselect(
        "Q109_SOURCES",
        "109. Which of the following did you use to pay for the medicines bought outside "
        "the hospital? (Tick all that apply.)",
        Q109_PAYMENT, with_other_txt=False))
    items.append(alpha("Q109_PAY_OTHER_TXT",
                       "109. Meds outside — Other, specify text", length=120))
    items.append(yes_no("Q110_LAB_OUTSIDE",
                        "110. Other than the laboratory service/s indicated in the hospital bill, did "
                        "the patient pay for other service/s outside the hospital?"))
    items.append(alpha("Q111_SERVICES_OUTSIDE",
                       "111. If yes, what are those services?", length=240))
    # Q112 services outside — Option B ROSTER fan-out (#693, 2026-06-19). WAS a flat
    # 9-source Yes/No + per-source _AMT matrix (same Q109_PAYMENT codes). NOW a CheckBox
    # (Q112_SOURCES) feeding a roster (Q112_PAY_ROSTER); ALL-amount (Q971 pattern, length-9).
    # 'Other' (09) gates Q112_PAY_OTHER_TXT. >=1 source = the CheckBox's own gate (#557).
    items.extend(checkbox_multiselect(
        "Q112_SOURCES",
        "112. Which of the following did you use to pay for the services done outside the "
        "hospital? (Tick all that apply.)",
        Q109_PAYMENT, with_other_txt=False))
    items.append(alpha("Q112_PAY_OTHER_TXT",
                       "112. Services outside — Other, specify text", length=120))
    # Q113 hospital bill — Option B ROSTER fan-out (#693, 2026-06-19). WAS a flat 13-source
    # Yes/No + per-source _AMT matrix. NOW a CheckBox (Q113_SOURCES) feeding a roster
    # (Q113_PAY_ROSTER); ALL-amount (Q971 pattern, length-9). 'Other (specify)' (13) gates
    # Q113_PAY_OTHER_TXT. PhilHealth row (08) still drives the Q114 skip — the apc now reads
    # pos("08", Q113_SOURCES) instead of the removed Q113_PAY_08 flag; the Q110=No skip now
    # targets Q113_SOURCES (was Q113_PAY_01). >=1 source = the CheckBox's own gate (#555).
    items.extend(checkbox_multiselect(
        "Q113_SOURCES",
        "113. Which of the following did you use to pay for the hospital bill? "
        "(Tick all that apply.)",
        Q113_SOURCES, with_other_txt=False))
    items.append(alpha("Q113_PAY_OTHER_TXT",
                       "113. Hospital bill payment — Other specify text", length=120))
    items.extend([
        *checkbox_multiselect("Q114_NO_PH",   # #694: select_all -> Check Box (tick-all)
                    "114. Why did you not avail of PhilHealth benefits? (If PhilHealth was not availed in 113)",
                    _cb_codes(Q114_NO_PH), with_other_txt=True),
    ])
    # Q115 final cash first, then the 115.1/115.2 breakdowns sit UNDER it (#517 — mirrors
    # the outpatient side, where Q97 total precedes Q97.1/Q97.2).
    items.append(numeric("Q115_FINAL_CASH",
                         "115. What was the final amount you paid in cash at the hospital cashier "
                         "upon discharge? (Amount in Pesos)", length=9))
    # Q115.1 other items included in bill — 6 items with amount
    for label, code in Q1141_IN_BILL:
        items.append(yes_no(f"Q1141_{code}",
                            f"115.1 Other items included in the bill — {label}"))
        items.append(numeric(f"Q1141_{code}_AMT",
                             f"115.1 Other items included in the bill — {label} (Amount in Pesos)",
                             length=9))
    items.append(alpha("Q1141_OTHER_TXT",
                       "115.1 Other expenses — specify text", length=120))
    # Q115.2 other expenses NOT included in bill — 7 items with amount
    for label, code in Q1142_NOT_IN_BILL:
        items.append(yes_no(f"Q1142_{code}",
                            f"115.2 Other expenses during confinement not in bill — {label}"))
        items.append(numeric(f"Q1142_{code}_AMT",
                             f"115.2 Other expenses during confinement not in bill — {label} "
                             "(Amount in Pesos)", length=9))
    items.append(alpha("Q1142_OTHER_TXT",
                       "115.2 Other expenses — specify text", length=120))
    # Option B fan-out (#691/#692/#693, 2026-06-19): FOUR Section H cost matrices are now
    # CheckBox -> roster (Q107 total bill, Q109 meds outside, Q112 services outside, Q113
    # hospital bill). Each `_SOURCES` CheckBox splits the host H record; its roster grid
    # (length-9 peso amounts, all-amount) renders right after. The Q115/Q115.1/Q115.2
    # tail stays a flat amount matrix (out of scope — Q1141/Q1142 not in the candidate
    # list). Record types: rosters e/f/g/h; host continuation fragments i/j/k/l.
    h_rosters = {
        "Q107_SOURCES": _build_payment_roster(
            "Q107_PAY_ROSTER", "H. Total bill for confinement — amount by source", 107,
            Q107_PAYMENT, set(), "e",
            "107. Payment source (auto-filled from the ticked sources)",
            "107. Amount of the total bill, by source (Pesos)", amt_length=9),
        "Q109_SOURCES": _build_payment_roster(
            "Q109_PAY_ROSTER", "H. Medicines bought outside — amount by source", 109,
            Q109_PAYMENT, set(), "f",
            "109. Payment source (auto-filled from the ticked sources)",
            "109. Amount paid for medicines outside, by source (Pesos)", amt_length=9),
        "Q112_SOURCES": _build_payment_roster(
            "Q112_PAY_ROSTER", "H. Services done outside — amount by source", 112,
            Q109_PAYMENT, set(), "g",
            "112. Payment source (auto-filled from the ticked sources)",
            "112. Amount paid for services outside, by source (Pesos)", amt_length=9),
        "Q113_SOURCES": _build_payment_roster(
            "Q113_PAY_ROSTER", "H. Hospital bill — amount by source", 113,
            Q113_SOURCES, set(), "h",
            "113. Payment source (auto-filled from the ticked sources)",
            "113. Amount paid for the hospital bill, by source (Pesos)", amt_length=9),
    }
    return _split_host_with_rosters(
        "H_INPATIENT_CARE", "H. Inpatient Care", "J", items, h_rosters,
        cont_types=["i", "j", "k", "l"])


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
        # #481: codes below are remapped by _cb_codes for the Check Box conversion
        # ('None' -> exclusive 90, 'Other (specify)' -> 99); the literal codes here
        # are placeholders the conversion overwrites.
        ("None",               "5"),   # nothing paid out-of-pocket -> exclusive (90)
        ("Other (specify)",    "6"),   # -> 99 with a gated _OTHER_TXT
    ]
    Q129_WHY_NO_MAIFIP = [
        ("Not eligible",                            "1"),
        ("Too complicated",                         "2"),
        ("I don't like to stay in basic ward",      "3"),
        ("There is no available basic ward",        "4"),
        ("Other (specify)",                         "99"),   # #783: add Other-specify (the 'specif' marker -> _cb_codes maps to 99; with_other_txt below opens the text box)
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
        *checkbox_multiselect("Q117_NBB_SOURCE",
                    "117. If yes, what are your sources of information about NBB?",
                    _cb_codes(SOURCE_8), with_other_txt=True),
        *checkbox_multiselect("Q118_NBB_UNDERSTAND",
                    "118. What is your understanding about NBB?",
                    _cb_codes(Q118_UNDERSTAND_NBB), with_other_txt=True),
        select_one("Q119_ZBB_HEARD",
                   "119. Have you heard of the Zero Balance Billing (ZBB)?",
                   Q119_HEARD, length=1),
        *checkbox_multiselect("Q120_ZBB_SOURCE",
                    "120. If yes, what are your sources of information about ZBB?",
                    _cb_codes(SOURCE_8), with_other_txt=True),
        *checkbox_multiselect("Q121_ZBB_UNDERSTAND",
                    "121. What is your understanding about ZBB?",
                    _cb_codes(Q121_UNDERSTAND_ZBB), with_other_txt=True),
        yes_no("Q122_ZBB_INFORMED",
               "122. Were you informed about ZBB upon admission?"),
        select_one("Q123_ZBB_EXTENT",
                   "123. To what extent did ZBB reduce your financial burden?",
                   Q123_ZBB_EXTENT, length=1),
        select_one("Q124_MAIFIP_HEARD",
                   "124. Have you heard of the Medical Assistance for Indigent and "
                   "Financially Incapacitated Patients (MAIFIP)?",
                   Q124_HEARD, length=1),  # #477: removed redundant "(SKIP IF ANSWERED MAIFIP IN Q113)" enumerator note — CAPI auto-handles the Q113 gate
        *checkbox_multiselect("Q125_MAIFIP_SOURCE",
                    "125. What are your sources of information about MAIFIP?", _cb_codes(SOURCE_8)),
        yes_no("Q126_MAIFIP_AVAILED",
               "126. Did you avail of MAIFIP in this last confinement?"),
        yes_no("Q127_MAIFIP_OOP",
               "127. If you availed MAIFIP, did you have to make any out-of-pocket payment?"),
        *checkbox_multiselect("Q128_MAIFIP_OOP_ITEMS",   # #481: select_all -> Check Box (tick-all)
                    "128. Which items did you have to pay for out-of-pocket?",
                    _cb_codes(Q128_OOP_ITEMS), with_other_txt=True),
        *checkbox_multiselect("Q129_WHY_NO_MAIFIP",   # #700: select_all -> Check Box (tick-all)
                    "129. Why did you not avail of MAIFIP during this last confinement?",
                    _cb_codes(Q129_WHY_NO_MAIFIP), with_other_txt=True),   # #783: Other-specify text box enabled
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
                            "to exiting the facility?",   # #487: deleted '(For inpatients only)' — Marriz confirmed Q135 is asked for all patients
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
        # 'Other' uses code 99 (not 20) so pos("99",...) on the concatenated Check Box
        # string can't false-match across code boundaries — no valid code starts with 9.
        ("Other (Specify)",                                              "99"),
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
        # #500: escape for respondents who obtained ALL their medicines from GAMOT, so there
        # is no "rest" to source elsewhere. Worded as 'None…' so _cb_codes maps it to the
        # exclusive code 90 (can't be ticked alongside a real source).
        ("None — got all medicines from the GAMOT Package", "10"),
        ("Other (Specify)",                            "9"),
    ]
    Q159_BRANDED_GENERIC = [
        ("Branded",                   "1"),
        ("Generic",                   "2"),
        ("Both branded and generic",  "3"),
        # #732 (R5): 'Don't know the difference' (4) RESTORED to match the paper — the tester's
        # PAPI screenshot lists it (-> Q162), reversing #618's removal. Carl 'do what the testers
        # need': follow the paper's literal 5-option set + routing. Order = paper (DKD before NA).
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
        # Q148 redesigned (R4 review 2026-06-12): ONE Check Box multi-select (tick the
        # conditions on one screen) instead of 20 separate Yes/No items, + a gated free-text
        # for the medicines taken (skipped until >=1 condition is ticked).
        *checkbox_multiselect("Q148_CONDITIONS",
                    "148. What are the medical conditions that you take the medicines for?",
                    Q148_CONDITIONS),
        # #491: Q148_MEDICINES_TXT ("Which medicine(s)…for the condition(s) selected above?") removed —
        # redundant with Q147 ("What are the medications that you usually take?"). ASPSI go/no-go via Carl 2026-06-21.
        *checkbox_multiselect("Q149_WHERE_BUY",   # #696: select_all -> Check Box (tick-all)
                    "149. Where do you usually buy or receive your medicines? "
                    "Select all that apply.", _cb_codes(Q149_WHERE_BUY), with_other_txt=True),
        numeric("Q150_TRAVEL_HH",
                "150. Travel time from home to nearest pharmacy — hours (HH)", length=2),
        numeric("Q150_TRAVEL_MM",
                "150. Travel time from home to nearest pharmacy — minutes (MM)", length=2),
        select_one("Q151_PHARM_EASE",
                   "151. How easy is it for you to access a pharmacy or drugstore?",
                   Q151_EASE, length=1),
        # #495: area-type gate — Q152-Q159 apply only to areas WITH GAMOT; No -> skip the block (mirrors Q152=No -> Q158)
        yes_no("AREA_HAS_GAMOT",
               "Does this area have a Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT) pharmacy/package? (Q152-Q159 apply only to areas with GAMOT.)"),
        yes_no("Q152_GAMOT_HEARD",
               "152. Have you heard of the Guaranteed and Accessible Medications for "
               "Outpatient Treatment (GAMOT) Package, which is part of PhilHealth's "
               "YAKAP/Konsulta or primary care benefit package?"),
        *checkbox_multiselect("Q153_GAMOT_SOURCE",   # #696: select_all -> Check Box (tick-all)
                    "153. If yes, what are your sources of information for GAMOT Package?",
                    _cb_codes(Q153_GAMOT_SRC), with_other_txt=True),
        *checkbox_multiselect("Q154_GAMOT_UNDERSTAND",   # #696: select_all -> Check Box (tick-all)
                    "154. What is your understanding of the GAMOT Package?",
                    _cb_codes(Q154_GAMOT_UNDERSTAND), with_other_txt=True),
        yes_no("Q155_GAMOT_GOT_MEDS",
               "155. Did you get the medicines from the GAMOT Package during the past 6 months?"),
        alpha("Q156_GAMOT_MEDS_LIST",
              "156. What are the medications that you obtained from the GAMOT Package? [LIST]",
              length=240),
        *checkbox_multiselect("Q157_WHERE_REST",   # #696: select_all -> Check Box (tick-all)
                    "157. Where did you get the rest of the medicines? Select all that apply.",
                    _cb_codes(Q157_WHERE_REST), with_other_txt=True),
        yes_no("Q158_BRAND_GEN_KNOW",
               "158. Do you know the difference between a 'branded' and a 'generic' medicine?"),
        select_one("Q159_BRAND_GEN_BOUGHT",
                   "159. Was/were the medicine/s you bought outside of GAMOT pharmacy "
                   "branded or generic?", Q159_BRANDED_GENERIC, length=1),
        *checkbox_multiselect("Q160_WHY_GENERIC",   # #696: select_all -> Check Box (tick-all)
                    "160. If generic, why did you buy generic medicine?",
                    _cb_codes(Q160_WHY_GENERIC), with_other_txt=True),
        *checkbox_multiselect("Q161_WHY_BRANDED",   # #696: select_all -> Check Box (tick-all)
                    "161. If branded, why did you buy branded medicine?",
                    _cb_codes(Q161_WHY_BRANDED), with_other_txt=True),
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
        # #514: 'Not applicable' (6) removed — Q178 is only reached when there WAS a referral
        # (Q162=Yes gates Section L), so the referral-satisfaction question always applies.
    ]
    items = [
        yes_no("Q162_REFERRED",
               "162. Based on your most recent visit/confinement at [facility_name_input], "
               "did a healthcare worker refer you to another facility or specialist for "
               "further care or specialized care?"),
        *checkbox_multiselect("Q163_CARE_TYPE",   # #696: select_all -> Check Box (tick-all)
                    "163. What type of care was the referral for?",
                    _cb_codes(Q163_CARE_TYPE), with_other_txt=True),
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
        *checkbox_multiselect("Q171_WHY_NOT",
                    "171. Why are you NOT planning to visit?",
                    _cb_codes(Q171_WHY_NOT), with_other_txt=True),
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
        *checkbox_multiselect("Q177_WHY_HOSPITAL",
                    "177. As it was not a referral, why did you decide to visit a hospital?",
                    _cb_codes(Q177_WHY_HOSPITAL), with_other_txt=True),
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
    # F3_FACILITY_ID retired 2026-06-04: under the 12-digit case key, the F3 case's
    # own id-block (REGION_CODE+PROVINCE_HUC_CODE+CITY_MUNICIPALITY_CODE+FACILITY_NO)
    # IS the facility reference; F3<->F1 joins on those shared fields. No separate item.
    records = [
        build_f3_field_control(),
        build_geo_id("facility_and_patient", structured_address=True),   # #784/#786 Option A: typed Street + derived Barangay/Municipality + assembled address
        build_f3_facility_capture(),
        build_f3_patient_home_capture(),
        build_f3_case_verification(),
        build_section_a(),
        build_section_b(),
        build_section_c(),
        build_section_d(),
        build_section_e(),
        build_section_f(),
        *build_section_g(),   # Option B fan-out: G splits around 6 cost-matrix rosters (Q92/Q94/Q96/Q97.1/Q97.2/Q98)
        *build_section_h(),   # Option B fan-out: H splits around 4 cost-matrix rosters (Q107/Q109/Q112/Q113)
        build_section_i(),
        build_section_j(),
        build_section_k(),
        build_section_l(),
    ]
    return build_dictionary(
        dict_name="PATIENTSURVEY_DICT",
        dict_label="PatientSurvey",
        id_items=build_id_block(single_questionnaire_number=True),
        records=records,
    )


# --- #714: facility-name placeholder -> neutral header wording (DCF labels) ---
# The question stems carry a literal placeholder ([facility_name_input] and dialect
# variants). generate_qsf.py pipes it to ~~FACILITY_NAME~~ in the QSF question text so
# the captured facility name renders in the plain question-text line. But CSEntry renders
# the DCF field LABEL as the BOLD header, and CSPro fills do NOT evaluate inside DCF labels
# — so the raw placeholder was showing verbatim in bold (Q66 + the other facility questions:
# Q88/Q143/Q144/Q162/Q172). Fix: neutralise the placeholder token in every DCF label
# (English + each translated label), per-language, AFTER apply_translations so the English
# source strings are untouched and the translation maps still key-match. The QSF keeps the
# personalised ~~FACILITY_NAME~~ fill (generate_qsf.py unchanged) — so the bold header reads
# neutrally and the plain prompt line still shows the real facility name.
#
# FLAG (Carl/ASPSI veto): these neutral noun-phrases are chosen substitutions, not source
# wording. EN = "this facility"; dialect equivalents below. They preserve meaning ("Is THIS
# facility the one you usually go to...") without naming the facility in the bold header.
# Brackets are OPTIONAL: a translator dropped them in at least one place (FIL Q162 value
# reads "...sa facility_name_input, may healthcare worker..." with NO brackets). The bare
# snake_case tokens (facility_name_input / facility_ngaran_input) are machine identifiers,
# never natural language, so matching them un-bracketed is safe; the bracketed dialect
# phrases (e.g. [ngaran han pasilidad]) are only matched WITH brackets so the un-bracketed
# Bikol/Waray noun phrase "ngaran han pasilidad" used as ordinary text (Q64 answer) is left
# alone.
_FACILITY_PLACEHOLDER_RE = re.compile(
    r"\[?\b(?:facility[_ ]name[_ ]input|facility[_ ]ngaran[_ ]input)\b\]?"
    r"|\[\s*(?:igbutang[_ ]an[_ ]ngaran[_ ]han[_ ]pasilidad"
    r"|ngaran[_ ](?:han|kan)[_ ]pasilidad)\s*\]",
    re.IGNORECASE,
)
_FACILITY_NEUTRAL = {
    "EN":  "this facility",
    "FIL": "ang pasilidad na ito",
    "BCL": "an pasilidad na ini",
    "BIS": "kini nga pasilidad",
    "CEB": "kini nga pasilidad",
    "WAR": "ini nga pasilidad",
}


# The token sat between an article/preposition and a following noun in some stems, so the
# straight substitution leaves a redundant adjacency: EN "Is this facility the facility you
# usually go to" (Q66) and a doubled article where the translated text already had one before
# the token (FIL "ang ang pasilidad na ito", BCL "an an pasilidad na ini"). These cleanups
# fix only the mechanical artifacts the substitution itself created — they do not otherwise
# reword. (Dialect cleanups limited to the obvious doubled-article case; deeper dialect
# polish is ASPSI's call — FLAGGED in the report.)
_PLACEHOLDER_CLEANUPS = [
    # EN Q66: "this facility the facility" -> "this the facility"  (=> "Is this the facility…")
    (re.compile(r"\bthis facility the facility\b", re.IGNORECASE), "this the facility"),
    # doubled articles created by the substitution (FIL "ang ang", BCL/WAR "an an")
    (re.compile(r"\bang ang\b", re.IGNORECASE), "ang"),
    (re.compile(r"\ban an\b", re.IGNORECASE), "an"),
]


def _neutralise_facility_placeholder(dictionary):
    """Replace the facility-name placeholder token in every DCF label with a per-language
    neutral noun-phrase (#714), then clean the mechanical adjacency artifacts the
    substitution creates. Walks the assembled multi-language labels in place; leaves text
    with no placeholder untouched. Returns the count of labels changed."""
    changed = [0]

    def walk(node):
        if isinstance(node, dict):
            labs = node.get("labels")
            if isinstance(labs, list):
                for lab in labs:
                    if isinstance(lab, dict) and "text" in lab:
                        txt = lab["text"]
                        if _FACILITY_PLACEHOLDER_RE.search(txt):
                            repl = _FACILITY_NEUTRAL.get(lab.get("language"), "this facility")
                            new = _FACILITY_PLACEHOLDER_RE.sub(repl, txt)
                            for rx, sub in _PLACEHOLDER_CLEANUPS:
                                new = rx.sub(sub, new)
                            lab["text"] = new
                            changed[0] += 1
            for k, v in node.items():
                if k != "labels":
                    walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(dictionary)
    return changed[0]


def main():
    out_path = Path(__file__).parent / "PatientSurvey.dcf"
    dictionary = build_f3_dictionary()
    # Multi-language overlay (folded into the generator so regeneration never
    # silently resets the .dcf to English). Auto-discovers locales by file
    # existence in translations/; F3 has bcl/bis/ceb/war (no hil/fil).
    dictionary = apply_translations(dictionary, Path(__file__).parent / "translations")
    # #714: strip the facility-name placeholder from the bold-header DCF labels (must run
    # AFTER apply_translations so it also cleans the translated labels).
    n_fac = _neutralise_facility_placeholder(dictionary)
    print(f"  #714: neutralised facility-name placeholder in {n_fac} label(s)")
    write_dcf(dictionary, out_path)


if __name__ == "__main__":
    main()
