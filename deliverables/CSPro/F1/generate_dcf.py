"""
generate_dcf.py — F1 Facility Head Survey CSPro Data Dictionary generator.

Emits FacilityHeadSurvey.dcf in CSPro 8.0 JSON dictionary format from the
**Aug 17 2026** Annex F1 questionnaire, which supersedes the Apr 20 2026 Revised
Inception Report submission this file previously encoded.

Authority sources (in priority order):
  1. raw/Survey-Instruments-2026-08-17/F1-Facility Head Survey Questionnaire_
     UHC Year 2_Aug18.docx                                          (printed)
  2. deliverables/CSPro/instruments-aug17-extract/normalized/F1-paper.csv
     + F1-extract.md                        (pandoc extraction of the above)
  3. deliverables/CSPro/instruments-aug17-extract/F1-inventory.md    (structure)
  4. deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md          (logic spec)

The Aug-17 rewrite RENUMBERED and RESTRUCTURED F1 (Q1-Q166 -> Q1-Q153 plus 33
decimal sub-questions):

  - Section C's combined "has X been implemented since 2019 AND was it a result
    of the UHC Act" items are SPLIT into a two-step battery — a plain Yes/No base
    plus a `.1` UHC-attribution probe (see `two_step`). The 9-option
    `uhc9_item()` shape is retired from F1 entirely.
  - Sections D-H are a uniform -13 renumber of the old Q51-Q166, with per-item
    rewordings. Q48.1 (formerly the "61.1" dcf-vs-qsf divergence) is now a real
    printed sub-question, and Q49/Q50/Q107 gain a numeric "No. of Days"
    companion alongside their day-band select.
  - Consent + Secondary Data stubs are RETAINED although the Aug-17 paper moved
    them to an annex (Carl ruling 2026-08-18; registered `system-item` in
    instruments-aug17-extract/aug17-approved-divergences.md).

Naming convention: Q{n}_DESCRIPTOR in UPPER_SNAKE; a decimal sub-question `n.m`
becomes `Q{n}_{m}_DESCRIPTOR`; other-specify companions are `<base>_OTHER_TXT`.
Old->new item names live in instruments-aug17-extract/maps/F1-renames.csv (Task
2.1) — that map is what the Task 2.5 translation re-key joins on, so any rename
made here MUST be reflected there.

Two deliberate, instrument-wide policies behind this rebuild:

  * Option TEXT is verbatim from the paper (modulo pandoc extraction artifacts:
    `--` for a dash, `\\'` for an apostrophe, `{.mark}`/`{.underline}` spans).
    Trailing enumerator directives ("READ OPTIONS OUT LOUD. SELECT ALL THAT
    APPLY.") and `<gate clauses>` are NOT part of a dictionary label — they
    render from generate_qsf's INSTRUCTIONS map, per the standing split.
  * Option CODES and option ORDER are the build's own, held stable across the
    renumber. The F1 paper prints bare `☐` checkboxes with NO printed code
    numbers, so the extractor's 1..N codes are positional artifacts of a
    multi-column table read, not authority (verified: several "order changes"
    are just a column-major vs row-major reading of the same printed grid).
    Holding codes stable keeps already-collected pretest data valid and lets the
    Task 2.5 re-key recover per-option translations, whose map keys are
    `val:<VALUE-SET>:<code>`. Option membership DOES follow the paper.

Run:
    python generate_dcf.py        # writes FacilityHeadSurvey.dcf next to this file
"""

import sys
from pathlib import Path

# Import shared helpers
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from icf_content import (
    ITEM_LABELS as ICF_ITEM_LABELS,
    CONTINUE_OPTIONS as ICF_CONTINUE_OPTIONS,
)
from cspro_helpers import (
    YES_NO, YES_NO_DK, YES_NO_NA, FREQUENCY, WHY_DIFF_OPTIONS,
    _value_set, numeric, alpha, yes_no, yes_no_dk, yes_no_na,
    select_one, checkbox_multiselect, record, build_geo_id,
    _gps_fields, _photo_block, derived_geo_code_items,
    apply_translations, write_dcf, ENUM_RESULT_OPTIONS_F1, REPLACED_CODE_F1,
    BREAKOFF_OPTIONS,
)


def _cb_codes(options):
    """#529: re-code a select_all option list for checkbox_multiselect — real
    options -> 01,02,...; 'Other (specify)' -> 99; a standalone exclusive option
    ('None…', 'No initiatives', 'I don't know') -> 90. Fixed-width 2-char codes in
    the 9x range for specials so pos() membership tests can't false-match (matches
    the Q36/Q37/Q40/Q45 convention). The 01.. order is preserved, so gate logic that
    references option N stays valid (e.g. Q53-61 gated on Q52 difficulty N)."""
    out, n = [], 0
    for text, _ in options:
        low = text.strip().lower()
        if "specif" in low or low.startswith("other"):
            out.append((text, "99"))
        elif (low.startswith(("none", "no initiative")) or "don't know" in low
              or "dont know" in low):
            out.append((text, "90"))
        else:
            n += 1
            out.append((text, f"{n:02d}"))
    return out


# ============================================================
# 2. CLOSED DESIGN DECISIONS
# ============================================================
# What used to be a 6-entry PENDING_DESIGN block. Three of the six are now
# closed by the Aug-17 paper itself and their toggles are gone:
#
#   * Q63 ACCRED_WAIT day-vs-month buckets — the Aug-17 paper (new Q50) prints
#     "How many days..." WITH day bands AND a numeric No. of Days write-in, so
#     the months reading (#527, from the Apr-20 paper) no longer applies.
#   * Q166 PD_NURSES audits — Aug-17 Q153 prints the nurse list without
#     "Clinical audits"/"Surgical audits", confirming the long-standing default.
#   * Q121 dynamic value set — shipped; new Q108 keeps the facility-type value
#     sets the .apc swaps via setvalueset().
#
# The two below stay because they are LOGIC defaults, not dictionary shape, and
# the dictionary has no opinion on them.

# Secondary data structure — separate dcf records vs separate CSPro app vs
# paper-only collection. Default: emit empty stub records so the dictionary
# opens, but no items inside. RETAINED for Aug-17 (Carl ruling 2026-08-18).
SECONDARY_DATA_AS_STUBS = True

# Q20 EMR_USE — should "Not applicable" route onward like the other NA branches?
# Skip-logic doc says yes; the printed question omits it. Encoded in PROC, not
# the dictionary.
Q20_NA_SKIPS = True


# ============================================================
# 2b. SECTION C — the UHC-attribution two-step battery
# ============================================================
# The Aug-17 Section C asks 23 topics as a PAIR: a plain Yes/No base ("Does the
# facility have X?") immediately followed by a `.1` probe ("If yes, was it a
# result of the UHC Act enacted in 2019?"). The Apr-20 instrument fused both
# halves into ONE 9-option `uhc9_item`; splitting them is the single largest
# structural change in this rebuild.
#
# The probe's option set is NOT uniform across its 23 repetitions — the paper
# prints three different lists (F1-inventory.md §9 anomaly 4). Emitting one
# shared constant everywhere would silently invent options the respondent was
# never offered, so each shape is its own constant and each probe names the one
# its own paper row prints:
#
#   UHC_ATTRIB       6 options   — 18 probes (the common case)
#   UHC_ATTRIB_NA    7 options   — Q10.1 only (adds "Not applicable")
#   UHC_ATTRIB_NOPLAN 5 options  — Q27.1/Q28.1/Q29.1 (drop "Not yet implemented
#                                  but planned...", which reads oddly against a
#                                  policy the facility either applies or doesn't)
#
# Codes are inherited from the Apr-20 `Q11_PRIMARY_PKG_STATUS` value set (the one
# old item that already carried exactly this list) so its captured data and its
# per-option translations survive the re-key: 1-4 substantive, 5 Other, 8 I don't
# know, 9 Not applicable. Ascending in every shape.
_UHC_ATTRIB_CORE = [
    ("Implemented as a direct result of the UHC Act",                                "1"),
    ("Pre-existing prior to UHC but subsequently enhanced or expanded due to UHC Act", "2"),
    ("Newly implemented or improved independent of UHC Act",                         "3"),
]
_UHC_ATTRIB_PLANNED = ("Not yet implemented but planned within the next 1-2 years",  "4")
_UHC_ATTRIB_TAIL = [
    ("Other (specify)", "5"),
    ("I don't know",    "8"),
]

UHC_ATTRIB         = _UHC_ATTRIB_CORE + [_UHC_ATTRIB_PLANNED] + _UHC_ATTRIB_TAIL
UHC_ATTRIB_NA      = UHC_ATTRIB + [("Not applicable", "9")]
UHC_ATTRIB_NOPLAN  = _UHC_ATTRIB_CORE + _UHC_ATTRIB_TAIL

# The probe stem, identical on 21 of the 23 rows. Q10.1 prints it without the
# trailing "SELECT ONE ANSWER ONLY." directive (which is enumerator furniture and
# never enters a dict label anyway, so the two are identical HERE); Q30.1 appends
# a policy parenthetical and therefore passes its own text.
UHC_ATTRIB_STEM = "If yes, was it a result of the UHC Act enacted in 2019?"


def two_step(base_name, base_label, probe_qnum, options=YES_NO,
             probe_options=UHC_ATTRIB, probe_label=None):
    """One Section-C attribution pair: the Yes/No base + its `.1` UHC probe.

    `probe_qnum` is the printed sub-number ("10.1"), which fixes the probe's item
    name at Q<NN>_1_UHC_ATTRIB — uniform across all 23 repetitions on purpose:
    they are literally the same question asked 23 times, and a uniform name lets
    the battery be selected, gated and tabulated as one block. (This supersedes
    the per-topic probe names F1-renames.csv proposed for the 5 probes that carry
    an Apr-20 predecessor; the map is updated to match, since Task 2.5's re-key
    joins on it.)

    Emits the base, the probe, and — when the probe's own option list offers
    "Other (specify)" — the probe's gated free-text companion.
    """
    probe = f"Q{probe_qnum.replace('.', '_')}_UHC_ATTRIB"
    label = f"{probe_qnum}. {probe_label or UHC_ATTRIB_STEM}"
    items = [
        numeric(base_name, base_label, length=1, value_set_options=options),
        select_one(probe, label, probe_options, length=1),
    ]
    if any("specif" in t.lower() for t, _ in probe_options):
        items.append(alpha(f"{probe}_OTHER_TXT",
                           f"{label} — Other (specify) text", length=120))
    return items


# ============================================================
# 3. RECORD BUILDERS — A. Field Control + B. Geographic ID
# ============================================================

def build_field_control():
    # Field Control = exactly the paper FIELD CONTROL block (2026-06-12).
    # Case-start operational metadata (interviewer/timestamps/AAPOR) removed;
    # instrument identity comes from the installed questionnaire.
    # Aug-17: the paper's FIELD CONTROL table is UNCHANGED, so this record is too.
    items = [
        # Header — preserves exact item names from Carl's scaffold so
        # any prior PROC code keeps working.
        alpha("SURVEY_TEAM_LEADER_S_NAME",      "Survey Team Leader's Name",                    length=50),
        alpha("ENUMERATOR_S_NAME",              "Enumerator's Name",                            length=50),
        alpha("FIELD_VALIDATED_BY",             "Field Validated by",                           length=50),
        alpha("FIELD_EDITED_BY",                "Field Edited by",                              length=50),
        # #1132 (ASPSI 2026-08-06, Carl 2026-08-09): the ENUMERATOR now types MMDDYYYY,
        # matching the paper. STORAGE is still YYYYMMDD — generate_apc's postproc converts
        # on exit — so dates stay sortable, the final<first check keeps working, and the
        # Supervisor App / F3 / F4 stored composition is unchanged. Only the typed order
        # and this prompt moved; nothing downstream sees a different value.
        numeric("DATE_FIRST_VISITED_THE_FACILITY",
                "Date First Visited the Facility (MMDDYYYY)", length=8),
        # #1132 retest (2026-08-10): the #1099 MM/DD/YYYY echo fields are REMOVED
        # at ASPSI's explicit request — the reviewer circled both on-device as
        # confusing (four date rows for two dates). The paper has no echo; the
        # misparse guard the echo provided is partly covered by the impossible-
        # date block in the entry postproc. Do not re-add without a new ticket.
        numeric("DATE_OF_FINAL_VISIT_TO_THE_FACILITY",
                "Date of Final Visit to the Facility (MMDDYYYY)", length=8),
        numeric("TOTAL_NUMBER_OF_VISITS",       "Total Number of Visits",                       length=3),
        # Result-of-Visit codes come from cspro_helpers (ENUM_RESULT_OPTIONS_F1) so F1 cannot
        # drift from F3/F4 — "Replaced" (5) was added there 2026-07-14 and lands here for free.
        # #1290/#1301 class extension (UAT R7, 2026-08-20): the paper's FIELD CONTROL
        # code list has four codes; 5 "Replaced" is logic-assigned (PROC BREAKOFF 5-7),
        # never an enumerator pick, so FIRST VISIT's picklist drops it outright.
        numeric("ENUM_RESULT_FIRST_VISIT",      "Result of First Visit",                        length=1,
                value_set_options=[o for o in ENUM_RESULT_OPTIONS_F1
                                   if o[1] != REPLACED_CODE_F1]),
        numeric("ENUM_RESULT_FINAL_VISIT",      "Result of Final Visit",                        length=1,
                value_set_options=ENUM_RESULT_OPTIONS_F1),
        # #744 break-off control — ported from the F3/F4 Cluster-5 pattern. Lives on the
        # FIRST interactive form (case-start, via inject_breakoff.py) so it sits in the
        # case tree from the start and the enumerator can tap back to it mid-interview.
        # Its postproc routes a non-Continue choice straight to the closing Result-of-
        # Final-Visit, letting the enumerator end a withdrawn/postponed/stopped interview
        # without walking every required question. Default "Continue" is set in logic
        # (BREAKOFF preproc). The .fmf is hand-maintained for F1, so the form placement is
        # done by inject_breakoff.py (run once, persists), NOT a generate_fmf.
        numeric("BREAKOFF",
                "Interview status (leave as Continue unless ending the interview early)",
                length=1,
                value_set_options=BREAKOFF_OPTIONS),
        # #744/#561 completeness sentinel — OFF-FORM (not in the .fmf), set in logic only:
        # 0 In progress at case open (PROC QUESTIONNAIRE_NUMBER), 1 Completed when the
        # Result-of-Visit finalises to Completed, 2 Partial/broke-off otherwise. Lets the
        # Supervisor App + CSWeb exports tell complete from partial even for a force-quit
        # case (which never reaches the closing form, so it stays 0).
        numeric("CASE_DISPOSITION", "Case disposition (auto)", length=1,
                value_set_options=[
                    ("In progress",             "0"),
                    ("Completed",               "1"),
                    ("Partial / not completed", "2"),
                ]),
        # §15.E — language used for the interview (getlanguage() in the
        # QUESTIONNAIRE_NUMBER postproc; off-form, not enumerator input).
        alpha("LANGUAGE_USED",                  "Language used for the interview",              length=20),
    ] + derived_geo_code_items()
    # ^ single-number redesign (2026-06-10): REGION_CODE/PROVINCE_HUC_CODE/
    #   CITY_MUNICIPALITY_CODE/FACILITY_NO/CASE_SEQ (derived from QUESTIONNAIRE_NUMBER)
    #   + REGION_NAME/PROVINCE_NAME/CITY_NAME (read-only PSGC names) live here now.
    # #1290/#1301 class extension: FINAL VISIT keeps the FULL set at valueSets[0]
    # (synced-case labels, verify_questions and optimize_capture_types read index 0)
    # and gains a picker set without Replaced; the apc preproc selects between them
    # via setvalueset() (the F1 Q108 pattern).
    for _it in items:
        if _it.get("name") == "ENUM_RESULT_FINAL_VISIT":
            _it["valueSets"].append(_value_set(
                "ENUM_RESULT_FINAL_VISIT_PICK", "Result of Final Visit",
                [o for o in ENUM_RESULT_OPTIONS_F1 if o[1] != REPLACED_CODE_F1]))
    return record("FIELD_CONTROL", "Field Control", "A", items)


# ============================================================
# 4b. RECORD BUILDER — Informed Consent read-aloud (no paper question number)
# ============================================================
# Shan's "Suggested Layout (CSEntry)" (2026-08-13) puts the consent script back on the
# device as two read-aloud screens, each acknowledged with a single "Continue". F1 had
# no consent record at all — F3/F4 already had A_INFORMED_CONSENT for their Q1 gate —
# so this record is new here; record type "C" was the next free letter (A/B/Z/2-9 taken).
# No consent DECISION is captured: the layout shows no Yes/No control and CONSENT_GIVEN
# stays removed (2026-06-12). Text lives in ../icf_content.py.
#
# Aug-17: the paper moved the consent form to an annex; the CAPI keeps it (Carl ruling
# 2026-08-18). The Aug-17 ethics-contact table WAS missing from SCREENS["F1"] and is
# added there in this task — see icf_content.py.

def build_section_icf():
    return record(
        "A_INFORMED_CONSENT", "Introduction and Informed Consent", "C",
        [select_one(nm, ICF_ITEM_LABELS[nm], ICF_CONTINUE_OPTIONS, length=1)
         for nm in ("ICF_PART1", "ICF_PART2")],
    )


# ============================================================
# 5. RECORD BUILDERS — Section A. Facility Head Profile (Q1-Q6)
# ============================================================
# Q1-Q6 keep their numbers AND their item names across the Aug-17 renumber.

def build_section_a():
    # #1005 (pretest finding, 2026-08-03): the printed Q2 grid carries THIRTEEN
    # options, laid out in a 3-column table read column-major (down col 1, then
    # col 2, then col 3). An earlier list stopped one row into column 3 and
    # dropped "Rural Health Physician" and "Other (specify)".
    # Codes 1-11 are UNCHANGED so pretest data already collected stays valid; the
    # two recovered options take fresh codes (12, and 99 for Other per the house
    # convention used by _cb_codes and auto_other_specify_procs).
    # Aug-17: same 13 options, same order; option text taken verbatim from the
    # Aug-17 grid (which spells "Rural Health Unit/ Health Center Head" and
    # "Administrative Officer/ Assistant" with no space before the slash).
    Q2_ROLES = [
        ("Rural Health Unit/ Health Center Head", "1"),
        ("Physician",                           "2"),
        ("Chief of Hospital",                   "3"),
        ("Medical Director",                    "4"),
        ("Hospital Administrator",              "5"),
        ("Nurse",                               "6"),
        ("Municipal / City Health Officer",     "7"),
        ("Medical Officer",                     "8"),
        ("Administrative Officer/ Assistant",   "9"),
        ("Midwife",                            "10"),
        ("Health Promotion / Nutrition Officer","11"),
        ("Rural Health Physician",             "12"),
        ("Other (specify)",                    "99"),
    ]
    items = [
        # Respondent contact block — the paper consent form's signature block
        # (Name & Signature / Position, Office / Email / Mobile). Lives with the
        # facility-head profile it describes rather than in FIELD_CONTROL.
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
        # #1005: companion free-text for the recovered "Other (specify)" (code 99).
        # auto_other_specify_procs() in generate_apc.py derives the gate from the dcf
        # itself — it finds the single same-Q parent whose value set carries an
        # 'other'-labelled code and emits preproc noinput / postproc reenter against
        # Q2_FACILITY_ROLE = 99. No hand-written PROC needed.
        # NOTE: F1's .fmf is hand-maintained (no FMF generator), so this item needs a
        # matching form field or it lands UNREACHABLE — supplied by the idempotent
        # post-processor inject_q2_other_txt.py, which must run in the .fmf pipeline.
        alpha("Q2_OTHER_TXT",
              "2. What is your official designation at this health facility? — Other (specify) text",
              length=120),
        numeric("Q3_AGE", "3. How old are you (in years), as of your last birthday?",
                length=2),
        numeric("Q4_SEX", "4. What is your sex assigned at birth?", length=1,
                value_set_options=[("Male", "1"), ("Female", "2")]),
        # Q5 + Q6: tenure as years + months (the paper prints one question with two
        # boxed sub-fields; the dictionary keeps two CSPro items).
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
# 7. RECORD BUILDERS — Section C. UHC Implementation (Q9-Q37 + 32 subs)
# ============================================================
# Aug-17 restructure: was Q9-Q50 as 42 flat items (20 of them fused
# base+attribution `uhc9_item`s); now Q9-Q37 with 23 two-step pairs, 8 follow-up
# `.2` items and the new Q35.2 multi-select.

def build_section_c():
    Q12_2_PHU_ROLE = [
        ("Health promotion and education",            "1"),
        ("Disease surveillance report",               "2"),
        ("Referral and patient navigation",           "3"),
        ("Alignment with national public health programs", "4"),
        ("Other (specify)",                           "5"),
        ("I don't know",                              "8"),
        ("Not applicable",                            "9"),
    ]
    Q13_2_HPU_ROLE = [
        ("Leading health education and awareness campaigns (e.g., raising awareness about public health initiatives of DOH, disseminating information about health)",          "1"),
        ("Conducting and coordinating health screening and promotion activities (e.g., collaborating and implementing with other units and program coordinators to promote healthy lifestyles and preventive care)","2"),
        ("Advocacy and policy formation (e.g., research, campaigns, collaboration with policymakers)",                             "3"),
        ("Resource mobilization and fundraising (e.g., securing funding, grants)",                     "4"),
        ("Other (specify)",                                           "5"),
        ("I don't know",                                              "8"),
    ]
    # Aug-17 adds a fifth option, "Other (specify)", to the DOH-IS / PhilHealth
    # Dashboard submission question (F1-extract.md L520-535). Takes the next free
    # code; codes 1-4 are untouched.
    Q21_DATA_SUBMIT = [
        ("Yes, to DOH Information System only",                "1"),
        ("Yes, to PhilHealth Dashboard only",                  "2"),
        ("Yes, to both DOH Information System and PhilHealth Dashboard", "3"),
        ("No, we are not submitting these data",               "4"),
        ("Other (specify)",                                    "5"),
    ]
    Q23_REPORTS = [
        ("OPD/IPD census and morbidity reports", "1"),
        ("Maternal, newborn, child, and adolescent health (MNCAH) reports", "2"),
        ("Notifiable diseases / surveillance reports", "3"),
        ("Expenditure and budget utilization reports", "4"),
        ("PhilHealth claims and reimbursement reports", "5"),
        ("YAKAP/Konsulta utilization reports", "6"),
        ("NBB compliance", "7"),
        ("ZBB compliance / monitoring reports", "8"),
        ("HRH staffing and deployment reports", "9"),
        ("Medicines availability and stock status reports", "10"),
        ("Facility performance scorecards / quality reports", "11"),
        ("Other (specify)", "12"),
    ]
    # Q35.2 — genuinely new at Aug-17 (F1-inventory.md §9 anomaly 2: printed
    # "35.2" without its terminal period, which is why the extractor files it
    # under a duplicate qnum "35"). A real multi-select with no Apr-20
    # counterpart, so it gets its own item rather than joining the .1 probe loop.
    Q35_2_MEASURES = [
        ("Client satisfaction survey", "1"),
        ("Dashboards",                 "2"),
        ("Other (specify)",            "3"),
    ]
    # Q36/Q37 are TRUE Check Box multi-selects (GH #377/#378/#379, mirrors F3
    # Q148): codes are fixed-width 2-digit so CSEntry's Check Box capture can
    # slice the concatenated field by code width, and 'Other' uses the high
    # non-prefixing code 99 (no valid code starts with 9) so pos("99",..) on the
    # concatenated string can't false-match across code boundaries.
    QUALITY_ACCESS_CHALLENGES = [
        ("Limited resources (e.g., shortages in healthcare personnel/manpower, medical equipment, essential supplies, or funding)", "01"),
        ("Challenging quality standards (e.g., high standards that are difficult to achieve)", "02"),
        ("Certain healthcare decisions are made by local government units and not the health facility", "03"),
        ("Lack of specific healthcare skills (i.e., Insufficient specialists, surgeons, or other healthcare professionals with specialized skills needed in the facility)", "04"),
        ("Inadequate training of healthcare workers (i.e., Healthcare workers needing additional training to meet the facility's quality standards)", "05"),
        ("Lack of patient awareness of the benefits of UHC (e.g., patients do not know they can avail of free consultations, and selected medicines and laboratory services)", "06"),
        ("Limited accessibility of public healthcare facilities (e.g., lack of transportation options, inconvenient location, or physical barriers hindering access for patients.)", "07"),
        ("Infrastructure not conducive for patient care (e.g., no ground floor, shortage of rooms, inadequate sanitation facilities, lack of wheelchair accessibility, etc.)", "08"),
        ("I don't know", "09"),
        ("Other (specify)", "99"),
    ]

    items = []
    items.append(yes_no("Q9_UHC_HEARD",
                        "9. Have you heard about Universal Health Care (UHC) prior to this survey?"))
    # --- the two-step battery (23 base/probe pairs) -------------------------
    items.extend(two_step("Q10_HAS_PRIMARY_PKG",
                          "10. Does the facility have primary care packages?",
                          "10.1", probe_options=UHC_ATTRIB_NA))
    items.extend(two_step("Q11_PCB_LICENSING",
                          "11. Has the facility applied for a DOH primary care license?",
                          "11.1"))
    items.extend(two_step("Q12_PUBLIC_HEALTH_UNIT",
                          "12. Does the facility have a public health unit?",
                          "12.1", options=YES_NO_NA))
    items.append(select_one("Q12_2_PHU_ROLE",
                            "12.2. What is the main role of the public health unit?",
                            Q12_2_PHU_ROLE, length=1))
    items.append(alpha("Q12_2_PHU_ROLE_OTHER_TXT",
                       "12.2. What is the main role of the public health unit? — Other (specify) text",
                       length=120))
    items.extend(two_step("Q13_HEALTH_PROMO_UNIT",
                          "13. Does the facility have a health promotion unit?",
                          "13.1", options=YES_NO_NA))
    items.append(select_one("Q13_2_HPU_ROLE",
                            "13.2. What is the main role of the health promotion unit?",
                            Q13_2_HPU_ROLE, length=1))
    items.append(alpha("Q13_2_HPU_ROLE_OTHER_TXT",
                       "13.2. What is the main role of the health promotion unit? — Other (specify) text",
                       length=120))
    items.extend(two_step("Q14_NEW_ROLES",
                          "14. Has there been establishment of new roles in the facility?",
                          "14.1"))
    items.append(alpha("Q14_2_NEW_ROLES_LIST",
                       "14.2. What is/are the new role/s established in this facility?", length=240))
    items.extend(two_step("Q15_NEW_DEPTS",
                          "15. Has there been establishment of new departments in the facility?",
                          "15.1"))
    items.append(alpha("Q15_2_NEW_DEPTS_LIST",
                       "15.2. What is/are the new department/s established in this facility?", length=240))
    items.extend(two_step("Q16_NEW_BUILDINGS",
                          "16. Has there been construction of new buildings in this facility?",
                          "16.1"))
    items.append(alpha("Q16_2_NEW_BUILDINGS_PURPOSE",
                       "16.2. What is/are the building/s being used for?", length=240))
    items.extend(two_step("Q17_NEW_ROOMS",
                          "17. Has there been construction of new rooms in this facility?",
                          "17.1"))
    items.append(alpha("Q17_2_NEW_ROOMS_PURPOSE",
                       "17.2. What are the rooms being used for?", length=240))
    items.extend(two_step("Q18_INC_EQUIPMENT",
                          "18. Has there been an increase in equipment in this facility?",
                          "18.1"))
    items.append(alpha("Q18_2_INC_EQUIPMENT_LIST",
                       "18.2. If there was an increase in equipment, what are these pieces of equipment?",
                       length=240))
    items.extend(two_step("Q19_INC_SUPPLIES",
                          "19. Has there been an increase in supplies in this facility?",
                          "19.1"))
    items.append(alpha("Q19_2_INC_SUPPLIES_LIST",
                       "19.2. If there was an increase in supplies, what are these?", length=240))
    items.extend(two_step("Q20_EMR_USE",
                          "20. Have electronic medical records been used in this facility?",
                          "20.1"))
    # --- DOH Information System / PhilHealth Dashboard block ---------------
    items.append(select_one("Q21_DATA_SUBMIT",
                            "21. Does your facility currently submit health and financial data to the DOH Information System and/or the PhilHealth Dashboard?",
                            Q21_DATA_SUBMIT, length=1))
    items.append(alpha("Q21_OTHER_TXT",
                       "21. Does your facility currently submit health and financial data to the DOH Information System and/or the PhilHealth Dashboard? — Other (specify) text",
                       length=120))
    items.append(select_one("Q22_DATA_FREQ",
                            "22. If yes, how frequently has your facility submit these data?",
                            FREQUENCY, length=1))
    items.append(alpha("Q22_OTHER_TXT",
                       "22. If yes, how frequently has your facility submit these data? — Other (specify) text",
                       length=120))
    items.extend(checkbox_multiselect("Q23_DATA_REPORTS_USED",
                            "23. Which of the submitted reports are actually used for decision-making?",
                            _cb_codes(Q23_REPORTS)))
    # --- the battery resumes ------------------------------------------------
    items.extend(two_step("Q24_STAFFING_CHANGED",
                          "24. Have there been changes in the facility staffing?",
                          "24.1"))
    items.extend(two_step("Q25_REFERRAL_CHANGED",
                          "25. Have there been changes in the referral system in this facility?",
                          "25.1"))
    items.extend(two_step("Q26_MOU_MOA",
                          "26. Does this facility has MoU/MoA with other health facilities apart of the healthcare provider network?",
                          "26.1"))
    items.extend(two_step("Q27_NBB",
                          "27. Does this facility implement No Balance Billing (NBB)?",
                          "27.1", probe_options=UHC_ATTRIB_NOPLAN))
    items.extend(two_step("Q28_ZBB",
                          "28. Does this facility implement Zero Balance Billing (ZBB)?",
                          "28.1", probe_options=UHC_ATTRIB_NOPLAN))
    items.extend(two_step("Q29_NO_COPAY",
                          "29. Does this facility implement no co-payment policy?",
                          "29.1", probe_options=UHC_ATTRIB_NOPLAN))
    # Q30.1 is the one probe whose printed stem differs: it appends the UHC ward
    # allocation percentages as respondent-facing context (F1-inventory.md §5).
    items.extend(two_step("Q30_WARD_ALLOC",
                          "30. Does this facility implement ward accommodation allocation?",
                          "30.1",
                          probe_label=UHC_ATTRIB_STEM + " (Under UHC, basic ward allocation is as follows: 90% for government general hospitals; 70% for government specialty hospitals, and 10% for private hospitals.)"))
    items.extend(two_step("Q31_CPG",
                          "31. Has there been an improvement in the clinical practice guidelines of this facility?",
                          "31.1"))
    items.extend(two_step("Q32_DOH_LIC_STD",
                          "32. Does this facility implement DOH licensing standards?",
                          "32.1"))
    items.extend(two_step("Q33_PHIC_ACCRED",
                          "33. Does this facility implement PhilHealth accreditation requirements?",
                          "33.1"))
    items.extend(two_step("Q34_SVC_DELIVERY_PROT",
                          "34. Does this facility implement service delivery protocols?",
                          "34.1"))
    items.extend(two_step("Q35_PCQM",
                          "35. Does this facility implement primary care quality measures?",
                          "35.1"))
    items.extend(checkbox_multiselect("Q35_2_PCQM_MEASURES",
                            "35.2. If yes, what are the primary care quality measures are you implementing?",
                            _cb_codes(Q35_2_MEASURES)))
    # --- section tail: the two challenge tick-lists -------------------------
    items.extend(checkbox_multiselect("Q36_QUALITY_CHALL",
                            "36. What are the major challenges to improving the quality of patient care in your local area?",
                            QUALITY_ACCESS_CHALLENGES))
    items.extend(checkbox_multiselect("Q37_ACCESS_CHALL",
                            "37. What are the major challenges to improving the accessibility of patient care in your local area?",
                            QUALITY_ACCESS_CHALLENGES))
    return record("C_UHC_IMPLEMENTATION", "C. Universal Health Care (UHC) Implementation", "4", items)


# ============================================================
# 8. RECORD BUILDERS — Section D. YAKAP / Konsulta (Q38-Q87)
# ============================================================
# Aug-17: was Q51-Q100. Straight -13 renumber plus the Q48.1 sub-question and the
# Q49/Q50 numeric+band split.

def build_section_d():
    Q40_PACKAGE = [
        ("Pap smear", "01"), ("Mammogram", "02"), ("Lipid profile", "03"),
        ("Thyroid function test", "04"), ("Chest X-ray", "05"),
        ("Low-dose CT scan", "06"), ("Dental services", "07"),
        ("All of the above", "08"), ("I don't know", "09"), ("Other (specify)", "99"),
    ]
    Q45_PERF = [
        ("Beneficiaries consulted a primary care doctor", "01"),
        ("Utilization of laboratory services", "02"),
        ("Beneficiaries received antibiotics as prescribed by their primary care doctor", "03"),
        ("Beneficiaries received noncommunicable disease (NCD) medicine as prescribed by their primary care doctor", "04"),
        ("No requirements", "05"),
        ("1st patient encounter", "06"),
        ("I don't know", "07"),
        ("Other (specify)", "99"),
    ]
    Q47_PAY_FREQ = [
        ("Monthly", "1"), ("Quarterly", "2"), ("Semi-annually", "3"), ("Annually", "4"),
    ]
    # Aug-17 replaced the Apr-20 MONTH buckets on both of these with the same
    # three DAY bands, each preceded by a numeric "No. of Days:" write-in and an
    # enumerator note ("Tick the category that corresponds to the respondent's
    # answer") — F1-inventory.md §6 "Hybrid numeric-plus-band structure". Both
    # halves are captured: the numeric companion is the new `_NUM` item, the band
    # keeps the carried item name. This closes the old Q63 day-vs-month
    # PENDING_DESIGN (#527) — the paper now says days in both stem and bands.
    DAY_BANDS = [
        ("30 days and less", "1"),
        ("31-60 days",       "2"),
        ("More than 60 days", "3"),
    ]
    Q51_REASONS = [
        ("Incentives (i.e., facility receives capitation/payment for registered patients)", "01"),
        ("Aligns with facility's mission (i.e., goals of UHC are aligned with the facility)", "02"),
        ("Encouraged by LGU", "03"),
        ("Mandated/required by DOH/UHC", "04"),
        ("To improve the services of the facilities", "05"),
        ("Other (specify)", "99"),
    ]
    Q52_DIFFICULT = [
        ("Ability to conduct preventive/screening services and health education", "1"),
        ("Capability to provide services for required laboratory and radiologic services", "2"),
        ("Capability to dispense required medicines", "3"),
        ("General Infrastructure", "4"),
        ("Equipment and Supplies", "5"),
        ("Human resource", "6"),
        ("Functional Health Information System", "7"),
        ("Documentary requirements", "8"),
        ("DOH licensing requirements", "9"),
        ("None of the above", "10"),
    ]
    Q62_RESPONSIBILITY = [
        ("Patients' own initiative", "1"),
        ("Facility", "2"),
        ("LGU", "3"),
        ("Someone else", "4"),
        ("PhilHealth", "5"),
        ("I don't know", "6"),
        ("Other (specify)", "7"),
    ]
    Q63_INITIATIVES = [
        ("On-site Enrollment (e.g., offering patient enrollment at the health facility)", "1"),
        ("LGU Outreach (e.g., involvement in LGU outreach activities, such as ongoing nutrition programs)", "2"),
        ("Facility Outreach (e.g., engaging in outreach efforts directly from the facility)", "3"),
        ("Barangay Health Workers (BHWs) Support (e.g., receiving support from local BHWs)", "4"),
        ("Information Campaigns (e.g., conducting information campaigns through various channels, including but not limited to online campaigns and house-to-house visits)", "5"),
        ("Local Health Insurance Offices (LHIO); assistance or partnerships with YAKAP/Konsulta caravans", "6"),
        ("Coordination with other government agencies and the private sector", "7"),
        ("No initiatives", "8"),
        ("Other (specify)", "9"),
    ]
    Q65_ENROLL_CHALL = [
        ("Lack of patient awareness (i.e., patients are unaware of YAKAP/Konsulta, its benefits, and registration process)", "1"),
        ("Lack of patient willingness (i.e., patient is hesitant to provide personal information or has concerns about data security)", "2"),
        ("Lack of resources (e.g., not enough manpower to conduct information campaigns or outreaches to enroll patients to YAKAP/Konsulta)", "3"),
        ("Competition with other health facilities over patient registration", "4"),
        ("Technical / system issues of PhilHealth (e.g., data loss, errors, or platform accessibility problems)", "5"),
        ("Other (specify)", "6"),
    ]
    Q66_NOT_ACCRED = [
        ("Difficult process", "1"),
        ("No time", "2"),
        ("Ongoing application", "3"),
        ("Other (specify)", "4"),
    ]
    Q67_INTEND = [
        ("Yes, already in process",                "1"),
        ("Yes, not yet in process",                "2"),
        ("No, decided not to",                     "3"),
        ("No, tried and failed",                   "4"),
        ("No, haven't thought about it yet",       "5"),
        ("I don't know",                           "6"),
    ]
    Q81_ADDL_CAP_REASONS = [
        ("To cover expenses related to building maintenance, equipment, and non-clinical staff", "1"),
        ("A patient's care costs exceed the predetermined fixed payment", "2"),
        ("Services excluded from capitation coverage", "3"),
        ("Provide preventive care that may not be adequately compensated under a basic capitation plan", "4"),
        ("Offset losses", "5"),
        ("Other (Specify)", "6"),      # Aug-17 prints a capital S on this one
    ]
    Q82_RECEIVED = [
        # #1113: the paper's "<proceed to Q84>" navigation note stays OUT of the
        # answer option — CAPI automates the routing (see generate_apc).
        ("Yes, we have received all expected payments",         "1"),
        ("Yes, we have received some but not all expected payments yet",     "2"),
        ("No, we have not received any expected payments yet", "3"),
        ("No, we have not expected any payments yet",      "4"),
    ]
    Q83_NOT_RECEIVED = [
        ("Delays in PhilHealth processing", "1"),
        ("Delays in facility's tracking of patient enrollment", "2"),
        ("Difficulties in verifying patient enrollment (PhilHealth)", "3"),
        ("Facility is not active in meeting criteria for payments (e.g., facility doesn't submit necessary requirements, facility doesn't enroll patients to YAKAP/Konsulta)", "4"),
        ("Criteria for payments is unclear", "5"),
        ("I don't know", "6"),
        ("Other (specify)", "7"),
    ]
    Q85_PAY_CHALL = [
        ("Delayed payment process", "1"),
        ("Unclear criteria for capitation", "2"),
        ("Difficult to meet criteria for capitation", "3"),
        # Aug-17 prints "Philhealth" here; kept as the instrument-wide "PhilHealth"
        # spelling used in ~20 other option labels (casing-only, registered
        # `formatting` — the same call as F3 Q71's punctuation normalization).
        ("PhilHealth process to apply for payments is difficult/unclear", "4"),
        ("I don't know", "5"),
        ("Other (specify)", "6"),
    ]
    Q86_EXPAND = [
        # #1116: PAPI wording ("The current ... offered"). Wording only - no
        # option is missing or added; codes unchanged.
        ("The current list of medicines and drugs offered", "1"),
        ("The current laboratory/diagnostic services offered", "2"),
        ("Additional features", "3"),
        ("I don't know", "4"),
        ("Other (specify)", "5"),
    ]

    items = []
    items.append(yes_no("Q38_YK_ACCRED",
                        "38. Is the facility currently an accredited YAKAP/Konsulta provider?"))
    items.append(numeric("Q39_YK_SINCE_MONTH", "39. If yes, since when? Month", length=2))
    items.append(numeric("Q39_YK_SINCE_YEAR",  "39. If yes, since when? Year",  length=4))
    items.extend(checkbox_multiselect("Q40_YK_PACKAGE",
                            "40. If accredited, which of the following are included in the YAKAP/Konsulta package?",
                            Q40_PACKAGE))
    items.append(yes_no_dk("Q41_YK_REG_INDIV",
                           "41. Is it possible to register individual patients to YAKAP/Konsulta at this facility?"))
    items.append(yes_no_dk("Q42_YK_REG_FAM",
                           "42. Is it possible to register whole families to YAKAP/Konsulta at this facility?"))
    # Aug-17 drops the Apr-20 "Is it ONLY possible..." framing.
    items.append(yes_no_dk("Q43_YK_REG_BOTH",
                           "43. Is it possible to register both individual patients and their family members together to YAKAP/Konsulta at this facility?"))
    items.append(numeric("Q44_CAPITATION_AMT",
                         # #1011: the "(Capitation is ...)" definition is the paper's
                         # enumerator note — testers want it OFF the CAPI question text.
                         "44. Based on your knowledge, what is the capitation amount of the YAKAP/Konsulta package?",
                         length=6))
    items.extend(checkbox_multiselect("Q45_PERF_INDICATORS",
                            "45. What are the performance indicators you need to meet to receive the second tranche payment?",
                            Q45_PERF))
    items.append(yes_no("Q46_KNOW_PAY_FREQ",
                        "46. Do you know how often you can expect to receive payments from PhilHealth for the delivery of the YAKAP/Konsulta package?"))
    items.append(select_one("Q47_PAY_FREQ",
                            "47. How often should you be receiving payments?",
                            Q47_PAY_FREQ, length=1))
    items.append(yes_no("Q48_TRANCHE_DELAY", "48. Were there delays in receiving capitation tranches?"))
    # Aug-17 prints this as a genuine sub-question "48.1", which RESOLVES the
    # catalogued Q61 dcf-vs-qsf "61.1" divergence: the item is now numbered as a
    # sub-question in the dictionary too, matching what the qsf always showed.
    items.append(alpha("Q48_1_DELAY_REASON",
                       "48.1. If yes, what was/were the reasons for the delay?", length=240))
    items.append(numeric("Q49_TRANCHE_INTERVAL_NUM",
                         "49. On average, how long is the typical time interval between tranches releases to the facility? — No. of Days",
                         length=4))
    items.append(select_one("Q49_TRANCHE_INTERVAL",
                            "49. On average, how long is the typical time interval between tranches releases to the facility?",
                            DAY_BANDS, length=1))
    items.append(numeric("Q50_ACCRED_WAIT_NUM",
                         "50. How many days did you wait from application submission to accreditation approval? — No. of Days",
                         length=4))
    items.append(select_one("Q50_ACCRED_WAIT",
                            "50. How many days did you wait from application submission to accreditation approval?",
                            DAY_BANDS, length=1))
    items.extend(checkbox_multiselect("Q51_APPLY_REASON",
                            "51. Why did you apply to become a YAKAP/Konsulta provider?",
                            Q51_REASONS))
    items.extend(checkbox_multiselect("Q52_ACCRED_DIFFICULT",
                            "52. Which of the following requirements were difficult to comply with for accreditation?",
                            _cb_codes(Q52_DIFFICULT), with_other_txt=False))
    # Q53-Q61 = nine "why difficult" tick-lists, gated per-option on Q52 in PROC.
    Q53_61_TOPICS = [
        # #1015: paper/sample format — short stem "comply with:" + the one component
        # (the "the following?" phrasing read as redundant with a single component).
        ("Q53_WHY_DIFF_PREVENTIVE",  "53. Why was it difficult to comply with: Ability to conduct preventive/screening services and health education?"),
        ("Q54_WHY_DIFF_LAB",         "54. Why was it difficult to comply with: Capability to provide services for required laboratory and radiologic services?"),
        ("Q55_WHY_DIFF_MEDS",        "55. Why was it difficult to comply with: Capability to dispense required medicines?"),
        ("Q56_WHY_DIFF_INFRA",       "56. Why was it difficult to comply with: General Infrastructure?"),
        ("Q57_WHY_DIFF_EQUIPMENT",   "57. Why was it difficult to comply with: Equipment and Supplies?"),
        ("Q58_WHY_DIFF_HR",          "58. Why was it difficult to comply with: Human resource?"),
        ("Q59_WHY_DIFF_HIS",         "59. Why was it difficult to comply with: Functional Health Information System?"),
        ("Q60_WHY_DIFF_DOCS",        "60. Why was it difficult to comply with: Documentary requirements?"),
        ("Q61_WHY_DIFF_DOH_LIC",     "61. Why was it difficult to comply with: DOH Licensing requirements?"),
    ]
    for prefix, label in Q53_61_TOPICS:
        items.extend(checkbox_multiselect(prefix, label, _cb_codes(WHY_DIFF_OPTIONS[:6] + [WHY_DIFF_OPTIONS[8]])))
    items.extend(checkbox_multiselect("Q62_ENROLL_RESPONSIBILITY",
                            "62. Based on your understanding, whose responsibility is it to enroll patients to YAKAP/Konsulta?",
                            _cb_codes(Q62_RESPONSIBILITY)))
    items.extend(checkbox_multiselect("Q63_ENROLL_INITIATIVES",
                            "63. Which of the following initiatives are you doing to enroll patients in this facility to YAKAP/Konsulta?",
                            _cb_codes(Q63_INITIATIVES)))
    items.append(yes_no("Q64_ENROLL_CHALL",
                        "64. Did you experience any challenges in enrolling patients to YAKAP/Konsulta?"))
    items.extend(checkbox_multiselect("Q65_ENROLL_CHALL_LIST",
                            "65. What are the challenges you have faced?",
                            _cb_codes(Q65_ENROLL_CHALL)))
    items.extend(checkbox_multiselect("Q66_NOT_ACCRED_REASON",
                            "66. If not YAKAP/ Konsulta accredited, why are you not accredited?",
                            _cb_codes(Q66_NOT_ACCRED)))
    items.append(select_one("Q67_INTEND_ACCRED",
                            "67. Are you intending to become a YAKAP/Konsulta provider?",
                            Q67_INTEND, length=1))
    items.append(yes_no("Q68_KNOW_HOW_START",
                        "68. If you decide to apply today, would you know how to start the process?"))
    items.append(alpha("Q69_DECIDED_NOT_REASON",
                       "69. What was the deciding factor not to apply?", length=240))
    items.append(alpha("Q70_TRIED_FAILED_REASON",
                       "70. What went wrong with the application?", length=240))
    items.append(alpha("Q71_PROCESS_CHALL",
                       "71. What are some challenges in the process, if any?", length=240))
    items.append(alpha("Q72_CATCHMENT_AREA",
                       "72. What areas do you consider as the facility's catchment area/s?", length=240))
    items.append(numeric("Q73_ELIGIBLE_PATIENTS",
                         "73. How many patients in your catchment area are eligible to register to this YAKAP/Konsulta provider?",
                         length=7))
    items.append(numeric("Q74_REGISTERED_PATIENTS",
                         "74. How many eligible patients in your catchment area are already registered to this YAKAP/Konsulta provider?",
                         length=7))
    # Q75 — verbatim text is 448 chars, well over CSPro's 255-char label limit.
    # #1189 round 2: the v1.3.2 attempt put the full stem HERE and the Designer
    # round-trip hard-cut it at 255 chars. The #1019/#1074 architecture is the
    # right one: label stays CONDENSED (<=255, and it is the translation key);
    # the FULL paper stem renders from generate_qsf's uncapped question area.
    items.append(yes_no_dk("Q75_IS_1700_ENOUGH",
                           "75. The maximum per capita rate for YAKAP/Konsulta is Php 1,700 across private and public facilities (40% after first patient encounter, 60% based on registered catchment population by December). Based on your practice, is this enough?"))
    items.append(yes_no_dk("Q76_COSTING_DONE",
                           "76. Did you go through a costing exercise to figure out if this was viable for your facility?"))
    items.append(yes_no_dk("Q77_COSTING_VIABLE",
                           "77. Did the costing exercise show that Php 1,700 was viable for your facility?"))
    items.append(numeric("Q78_MIN_CAP_VALUE_ACC",
                         "78. What would be the minimum acceptable capitation value per patient per year for you as a YAKAP/ Konsulta provider?",
                         length=6))
    items.append(numeric("Q79_MIN_CAP_VALUE_NONACC",
                         "79. What would be the minimum acceptable capitation value per patient per year for you to consider being a YAKAP/Konsulta provider?",
                         length=6))
    items.append(yes_no("Q80_CHARGE_ADDL_CAP", "80. Does your facility charge additional capitation fees?"))
    items.extend(checkbox_multiselect("Q81_CHARGE_ADDL_CAP_REASONS",
                            "81. What is/are the reason/s for the facility to charge additional capitation fees?",
                            _cb_codes(Q81_ADDL_CAP_REASONS)))
    items.append(select_one("Q82_RECEIVED_PAYMENTS",
                            "82. Have you already received payments for patients enrolled?",
                            Q82_RECEIVED, length=1))
    items.extend(checkbox_multiselect("Q83_NOT_RECEIVED_REASONS",
                            "83. Why not?",
                            _cb_codes(Q83_NOT_RECEIVED)))
    items.append(yes_no("Q84_PAYMENT_CHALL", "84. Did you face any challenges in getting these payments?"))
    items.extend(checkbox_multiselect("Q85_PAYMENT_CHALL_LIST",
                            "85. What were these challenges?",
                            _cb_codes(Q85_PAY_CHALL)))
    items.extend(checkbox_multiselect("Q86_EXPAND_NEXT",
                            "86. If you were to expand the YAKAP/Konsulta package, what would you expand next?",
                            _cb_codes(Q86_EXPAND)))
    items.append(alpha("Q87_ADDL_FEATURES",
                       "87. What additional features would you add?", length=240))
    return record("D_YAKAP_KONSULTA", "D. YAKAP/Konsulta Package", "5", items)


# ============================================================
# 9. RECORD BUILDERS — Section E. BUCAS / GAMOT (Q88-Q104)
# ============================================================
# Aug-17: was Q101-Q117. Straight -13 renumber; option sets unchanged.

def build_section_e():
    # #1023 (pretest): paper order is column-major — Not applicable precedes
    # Others (specify). Display order only; codes 1-5/99 UNCHANGED (data-safe).
    Q90_REASON = [
        ("Proposal not yet submitted",            "1"),
        ("Limited information on establishment process", "2"),
        ("Did not meet standard requirements",    "3"),
        ("Awaiting assessment or approval",       "4"),
        ("Not applicable",                       "99"),
        ("Others (specify)",                      "5"),
    ]
    Q91_SERVICES = [
        ("Urgent care and consultation",         "1"),
        ("Minor surgical procedures",            "2"),
        ("Diagnostic and laboratory services",   "3"),
        ("Reproductive and special health services", "4"),
        ("Other (specify)",                      "5"),
    ]
    Q92_FACTORS = [
        ("Patient awareness",                       "1"),
        ("Facility location and accessibility",     "2"),
        ("Referral patterns",                       "3"),
        ("PhilHealth coverage and reimbursement",   "4"),
        ("Availability of staff/services",          "5"),
        ("Others (specify)",                        "6"),
    ]
    # #1024 (pretest): same column-major order fix as Q90. Codes unchanged.
    Q97_REASON = [
        ("Application not yet submitted",         "1"),
        ("Limited information on accreditation process", "2"),
        ("Did not meet accreditation requirements","3"),
        ("Awaiting assessment or approval",       "4"),
        ("Not applicable",                       "99"),
        ("Others (specify)",                      "5"),
    ]
    Q98_FACTORS = [
        ("Availability of GAMOT medicines",                    "1"),
        ("Pharmacy capacity",                                  "2"),
        ("Patient awareness of the program",                   "3"),
        ("PhilHealth eligibility and reimbursement processes", "4"),
        ("Prescribing practices of physicians",                "5"),
        ("Others (specify)",                                   "6"),
    ]
    Q101_DURATION = [
        ("30 days and less", "1"),
        ("31-60 days",        "2"),
        ("More than 60 days", "3"),
    ]
    Q102_AVG = [
        ("less than a month", "1"),
        ("1-2 months",        "2"),
        ("3-4 months",        "3"),
        ("5-6 months",        "4"),
        ("more than 6 months","5"),
    ]
    Q103_ADDR = [
        ("Yes",                                             "1"),
        ("No",                                              "2"),
        ("Did not experience stock outs of medicines under the GAMOT package",     "3"),  # #737: full label per paper
    ]
    Q104_HOW = [
        ("Resorted to alternative procurement", "1"),
        ("Active inventory monitoring",         "2"),
        ("Improve forecasting and quantification", "3"),
        ("Other (specify)",                     "4"),
    ]

    items = []
    items.append(yes_no("Q88_HEARD_BUCAS",
                        "88. Have you heard about the Bagong Urgent Care and Ambulatory Service (BUCAS)?"))
    items.append(yes_no_dk("Q89_HAS_BUCAS", "89. Do you have a BUCAS Center?"))
    items.append(select_one("Q90_NO_BUCAS_REASON",
                            "90. If none, what is the primary reason?", Q90_REASON))
    items.append(alpha("Q90_OTHER_TXT",
                       "90. If none, what is the primary reason? Other (specify)", length=120))
    items.extend(checkbox_multiselect("Q91_BUCAS_SERVICES",
                            "91. What are the available services offered by your BUCAS Center?",
                            _cb_codes(Q91_SERVICES)))
    items.extend(checkbox_multiselect("Q92_BUCAS_FACTORS",
                            "92. In your assessment, what are the main factors affecting the utilization of BUCAS in your facility?",
                            _cb_codes(Q92_FACTORS)))
    items.append(alpha("Q93_BUCAS_RESOURCES_NEEDED",
                       "93. What are the resources you need to support/sustain the BUCAS center?",
                       length=240))
    items.append(yes_no("Q94_BUCAS_DECONGEST",
                        "94. Based on your experience, does the BUCAS Center decongest your health facility of patients?"))
    items.append(yes_no("Q95_HEARD_GAMOT",
                        "95. Have you heard about the Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT) package?"))
    items.append(yes_no("Q96_GAMOT_ACCRED", "96. Is your facility an accredited GAMOT provider?"))
    items.append(select_one("Q97_NO_GAMOT_REASON",
                            "97. If no, what is the primary reason?", Q97_REASON))
    items.append(alpha("Q97_OTHER_TXT",
                       "97. If no, what is the primary reason? Other (specify)", length=120))
    items.extend(checkbox_multiselect("Q98_GAMOT_FACTORS",
                            "98. In your assessment, what are the main factors affecting the utilization of the GAMOT Program in your facility?",
                            _cb_codes(Q98_FACTORS)))
    items.append(yes_no("Q99_STOCKOUT",
                        "99. In the past 3 months, has this facility experienced a stock-out (zero supply) of any tracer essential medicines?"))
    items.append(alpha("Q100_STOCKOUT_MEDS",
                       "100. What specific medicines? (antihypertensives, antibiotics, etc.)", length=240))
    items.append(select_one("Q101_STOCKOUT_DURATION",
                            "101. How many days did the stock-out last?", Q101_DURATION))
    items.append(select_one("Q102_STOCKOUT_AVG",
                            "102. On average, how many months do these stock-outs last?", Q102_AVG))
    items.append(select_one("Q103_ADDR_STOCKOUT",
                            "103. Did you do anything to address the medicine stock-outs in the GAMOT Package?",
                            Q103_ADDR))
    items.extend(checkbox_multiselect("Q104_ADDR_STOCKOUT_HOW",
                            "104. If yes, what did you do to address the medicine stock-outs in the GAMOT Package?",
                            _cb_codes(Q104_HOW)))
    return record("E_BUCAS_GAMOT", "E. Awareness on Expanded Health Programs (BUCAS and GAMOT)", "6", items)


# ============================================================
# 10. RECORD BUILDERS — Section F. DOH Licensing (Q105-Q121)
# ============================================================
# Aug-17: was Q118-Q134. Straight -13 renumber; Q107 gains the numeric No.-of-Days
# companion (same hybrid structure as Q49/Q50).

def build_section_f():
    Q105_LICENSED = [
        ("Yes",                                              "1"),
        ("No",                                               "2"),
        ("No, but have submitted requirements and waiting for license", "3"),
        ("I don't know what DOH licensing is",               "4"),
    ]
    Q106_WHEN = [
        ("Within the last 1 to 3 months",     "1"),
        ("Within the last 4 to 6 months",     "2"),
        ("Over 6 months but within 1 year",   "3"),
        ("More than 1 year ago",              "4"),
        ("I don't know",                      "5"),
    ]
    Q107_DAYS = [
        ("30 days and less", "1"),
        ("31-60 days",        "2"),
        ("More than 60 days", "3"),
    ]
    Q108_DIFFICULT = [
        ("Patient rights and organization ethics",                  "1"),
        ("Patient care",                                            "2"),
        ("Leadership and management",                               "3"),
        ("Human resource management",                               "4"),
        ("Information management",                                  "5"),
        ("Safe practice and environment",                           "6"),
        ("Improving performance",                                   "7"),
        ("Physical plant",                                          "8"),
        ("Equipment and instruments",                               "9"),
        # #1117: full PAPI wording restored (was abbreviated for tablet width).
        # Kept the parenthetical style of options 11/12 rather than the paper's
        # <angle brackets>, so the qualifier reads consistently across the list.
        ("National laws and DOH issuances implemented in hospitals and other health facilities (hospitals only)", "10"),
        ("Emergency cart contents (hospitals only)",               "11"),
        ("Add-on services (hospitals only)",                       "12"),
        # #1117: full PAPI wording restored; "PCF" spelled out.
        ("Public access to price information (primary care facilities only)", "13"),
        ("None of the above",                                      "14"),
    ]

    items = []
    items.append(select_one("Q105_DOH_LICENSED", "105. Is this facility DOH licensed?", Q105_LICENSED))
    items.append(select_one("Q106_LIC_RECEIVED_WHEN",
                            "106. When did you receive your DOH license from your most recent application?",
                            Q106_WHEN))
    items.append(numeric("Q107_LIC_DAYS_NUM",
                         "107. How many days did it take you to receive the license? — No. of Days",
                         length=4))
    items.append(select_one("Q107_LIC_DAYS",
                            "107. How many days did it take you to receive the license?", Q107_DAYS))
    # #385: Q108 is a single Check Box field, but its options are facility-type
    # specific (confirmed against the printed questionnaire & spec §4.9):
    #   - codes 10/11/12 (National laws & DOH issuances, Emergency cart contents,
    #     Add-on services) are HOSPITAL-ONLY  -> hide for a PCF (Q8_SERVICE_LEVEL = 1)
    #   - code 13 (Public access to price information) is PCF-ONLY -> hide for a hospital
    #   - code 90 (None of the above) is the exclusive option -> keep in BOTH sets.
    # Because Q108 is one Check Box (no per-option _O## fields to `noinput`), the correct
    # CSPro pattern is a dynamic value set swapped at Q108's preproc via setvalueset()
    # keyed on Q8_SERVICE_LEVEL (the apc gate lives in generate_apc.py's CHECKBOX_CONVERT_A).
    # We keep the default _VS1 (all 14 options) as valueSets[0] so the field length (28)
    # and verify_questions' first-value-set scan are unchanged, and append two
    # facility-specific value sets the apc selects between.
    _q108_coded = _cb_codes(Q108_DIFFICULT)
    Q108_HOSPITAL_ONLY = {"10", "11", "12"}   # National laws, Emergency cart, Add-on services
    Q108_PCF_ONLY = {"13"}                     # Public access to price information
    items.extend(checkbox_multiselect("Q108_DOH_LIC_DIFFICULT",
                            "108. Which of the following requirements were difficult to comply with in the DOH licensing process?",
                            _q108_coded, with_other_txt=False))
    _q108_field = items[-1]   # the Check Box alpha field checkbox_multiselect just appended
    _q108_label = "108. Which of the following requirements were difficult to comply with in the DOH licensing process?"
    # PCF set: drop the hospital-only options (10/11/12); keep PCF-only (13) + exclusive (90).
    _q108_field["valueSets"].append(_value_set(
        "Q108_DOH_LIC_DIFFICULT_PCF", _q108_label,
        [(t, c) for t, c in _q108_coded if c not in Q108_HOSPITAL_ONLY]))
    # Hospital set: drop the PCF-only option (13); keep hospital-only (10/11/12) + exclusive (90).
    _q108_field["valueSets"].append(_value_set(
        "Q108_DOH_LIC_DIFFICULT_HOSP", _q108_label,
        [(t, c) for t, c in _q108_coded if c not in Q108_PCF_ONLY]))
    # Q109-Q121 = thirteen "why difficult for X" Check Box multi-selects, gated on Q108.
    # NOTE the printed order: Q117 is "Public access to price information", inserted
    # mid-sequence rather than after Q116 (F1-inventory.md §9 anomaly 1). The Aug-17
    # paper keeps that ordering, so the build keeps it too.
    Q109_121_TOPICS = [
        # #1016: same short-stem format as Q53-61 (#1015).
        ("Q109_WHY_DIFF_PT_RIGHTS",  "109. Why was it difficult to comply with: Patient rights and organization ethics?"),
        ("Q110_WHY_DIFF_PT_CARE",    "110. Why was it difficult to comply with: Patient care?"),
        ("Q111_WHY_DIFF_LEADERSHIP", "111. Why was it difficult to comply with: Leadership and management?"),
        ("Q112_WHY_DIFF_HRM",        "112. Why was it difficult to comply with: Human resource management?"),
        ("Q113_WHY_DIFF_INFO_MGMT",  "113. Why was it difficult to comply with: Information management?"),
        ("Q114_WHY_DIFF_SAFE",       "114. Why was it difficult to comply with: Safe practice and environment?"),
        ("Q115_WHY_DIFF_PERF",       "115. Why was it difficult to comply with: Improving performance?"),
        ("Q116_WHY_DIFF_PHYS_PLANT", "116. Why was it difficult to comply with: Physical plant?"),
        ("Q117_WHY_DIFF_PRICE_INFO", "117. Why was it difficult to comply with: Public access to price information?"),
        ("Q118_WHY_DIFF_EQUIPMENT",  "118. Why was it difficult to comply with: Equipment and instruments?"),
        ("Q119_WHY_DIFF_NAT_LAWS",   "119. Why was it difficult to comply with: National laws and DOH issuances implemented in hospitals and other health facilities?"),
        ("Q120_WHY_DIFF_EMERG_CART", "120. Why was it difficult to comply with: Emergency Cart Contents?"),
        ("Q121_WHY_DIFF_ADDONS",     "121. Why was it difficult to comply with: Add-on services?"),
    ]
    # #1192/#1193: the paper's option lists are NOT identical across this battery —
    # Q111 and Q112 carry extra options the shared list lacks. Appended AFTER
    # "Lack of space" so they take the next sequential codes (09/10) and land
    # before Other(99): ascending codes preserved (checkbox rule, #830), and no
    # existing code moves mid-round. Aug-17 keeps both extras.
    Q111_EXTRAS = [("Frequent changes to guidelines and policies", "x"),
                   ("Resistance to change of staff", "x")]
    Q112_EXTRAS = [("Staff are resistant to change", "x")]
    for prefix, label in Q109_121_TOPICS:
        opts = list(WHY_DIFF_OPTIONS)
        extras = {"Q111_WHY_DIFF_LEADERSHIP": Q111_EXTRAS,
                  "Q112_WHY_DIFF_HRM": Q112_EXTRAS}.get(prefix, [])
        if extras:
            opts = opts[:-1] + extras + opts[-1:]   # keep Other (specify) last
        items.extend(checkbox_multiselect(prefix, label, _cb_codes(opts)))
    return record("F_DOH_LICENSING", "F. DOH Licensing: Status and Barriers to Licensing", "7", items)


# ============================================================
# 11. RECORD BUILDERS — Section G. Service Delivery (Q122-Q149)
# ============================================================
# Aug-17: was Q135-Q162. Straight -13 renumber with NBB/ZBB stem rewordings.

def build_section_g():
    NBB_ZBB_BARRIERS = [
        ("Complying with the no fees for basic or ward accommodation",        "1"),
        ("Complying the prescribed ratio of allocation of basic and non-basic accommodation", "2"),
        ("Patients do not go through the process of availing it",      "3"),
        # #1026/#1027 kept the paper's trailing "and/or" here verbatim. #1121
        # (ASPSI 2026-08-06) lists the option WITHOUT it, so the dangling
        # conjunction goes. Shared list -> applies to Q124 (NBB) and Q127 (ZBB).
        # Aug-17 REPRINTS the malformed cell (Q124 keeps the dangling "and/or";
        # Q127 additionally duplicates the merged option — F1-inventory.md §10) —
        # the ASPSI-confirmed clean list stands.
        ("Insufficient PhilHealth support value",                      "4"),
        ("Insufficient other sources (e.g. MAIFIP, DSWD, PCSO) (late payments applicable for MAIFIP)", "5"),
        ("PhilHealth delayed payment",                                 "6"),
        ("None of the above",                                          "7"),
        ("Other (specify)",                                            "8"),
    ]
    Q130_DIFFICULT_BENEFIT = [
        ("PhilHealth/financial protection benefits",                                "1"),
        ("Establishment of health care provider networks (HCPNs) (i.e., referral system)","2"),
        ("Human resources for health reforms",                                      "3"),
        ("Other (specify)",                                                         "4"),
    ]
    Q131_REASONS = [
        ("The implementation of UHC benefits is heavily reliant on LGU decisions", "1"),
        ("Not enough funding/budget",                           "2"),
        ("Technical/system issues of PhilHealth (e.g., data loss, errors, or platform accessibility problems)",               "3"),
        ("Other (specify)",                                     "4"),
    ]
    Q133_MALASAKIT_WHY = [
        ("Streamline access to medical and financial aid for indigent and financially incapacitated patients", "1"),
        ("Reduce out-of-pocket expenses",                                        "2"),
        ("Eliminate the need to travel to multiple government agencies",         "3"),
        ("Foster a more compassionate approach to healthcare",                   "4"),
        ("Other (specify)",                                                      "5"),
    ]
    Q134_NO_MALASAKIT_WHY = [
        ("Limited budget",                              "1"),
        ("Stringent eligibility requirements",          "2"),
        ("Incomplete documentation from patients",      "3"),
        ("High patient volume leading to service bottlenecks",   "4"),
        ("Other (specify)",                             "5"),
    ]
    Q136_LGU_FORMS = [
        ("Financial assistance",            "1"),
        ("Technical assistance",            "2"),
        ("Medical supplies and equipment",  "3"),
        ("Manpower support",                "4"),
        ("Other (specify)",                 "5"),
    ]
    Q138_NOT_SAT_WHY = [
        ("Insufficient",                                          "1"),
        ("Hard to coordinate",                                    "2"),
        ("Support given is not aligned with the needs of the facility",           "3"),
        ("I don't know",                                          "4"),
        ("Other (specify)",                                       "5"),
    ]
    Q139_CLARITY = [
        ("Very Clear",  "1"),
        ("Clear",       "2"),
        ("Neither",     "3"),
        ("Unclear",     "4"),
        ("Very unclear","5"),
    ]
    Q142_SEND_REF = [
        ("Physical referral slip",                  "1"),
        ("E-referral",                              "2"),
        ("Referring facility calls receiving facility", "3"),
        ("Other (specify)",                         "4"),
    ]
    Q143_FORM_TYPE = [
        ("DOH standard referral form",      "1"),
        ("Facility's standard referral form","2"),
        ("Province's standard referral form","3"),
        ("City / LGU standard referral form","4"),
        ("No standard referral form",       "5"),
        ("Other (specify)",                 "6"),
    ]
    Q144_NETWORK = [
        ("Yes",                "1"),
        ("No",                 "2"),
        ("I've never heard of it","3"),
        ("I don't know",       "4"),
    ]
    Q145_PROPORTION = [
        ("Almost all patients are referred, very few walk-in/self-referred",    "1"),
        ("Majority of patients are referred, some walk-in/self- referred",                       "2"),
        ("The proportion of referrals is about equal to walk-ins",       "3"),
        ("Majority of patients walk-in/self-referred, some are referred",                       "4"),
        ("Almost all patients walk-in/self-referred, very few are referred",                 "5"),
        ("I am unsure about the typical ratio of referrals to walk-ins",                        "6"),
    ]
    Q146_RECEIVE_REF = [
        ("Physical referral slip",                          "1"),
        ("E-referral",                                      "2"),
        ("Referring facility calls receiving facility",     "3"),
        ("Other (specify)",                                 "4"),
    ]
    # #734 (R5): Q147 -> Check Box multi-select per the tester's PAPI screenshot showing
    # checkboxes — resolves the #576/#586 "no PAPI evidence either way" hold on the same
    # basis #586 used to convert Q131. Hand-coded, NOT _cb_codes: "Other private facility"/
    # "Other public facility" legitimately start with "Other" and _cb_codes would mis-recode
    # both to 99 (3-way collision). 'Other, (specify)' -> 99 (with_other_txt); 'I don't know'
    # -> 90 (exclusive). #830: the value set MUST ascend by code (..., 90, 99). A descending
    # tail (99 then 90) was the ONLY thing that set this field apart from every other F1
    # checkbox, and it broke CSEntry's checkbox re-validation on partial-save resume
    # (WARNING: Out of range -> forced re-entry -> apparent data loss).
    Q147_EXTERNAL = [
        ("External laboratory",     "01"),
        ("Other private facility",  "02"),
        ("Other public facility (e.g., urban/rural health centers, barangay health centers, city/municipal health offices)", "03"),   # #1034 verbatim
        ("I don't know",            "90"),
        ("Other, (specify)",        "99"),
    ]
    Q148_SATISFACTION = [
        # #1035: paper-verbatim rating descriptions (codes unchanged).
        # (paper's inner double quotes swapped to singles — an embedded " in a value-set
        #  label crashes the CSDeploy pen packager: "fatal error ... could not recover")
        ("Very Satisfied: No improvements needed, 'patients are always referred appropriately'", "1"),
        ("Satisfied: Minor improvements needed, patients are generally referred appropriately",    "2"),
        ("Neither Satisfied nor Dissatisfied: Improvements needed, but generally functional",      "3"),
        ("Dissatisfied: Moderate improvements needed, a number of patients are referred to the wrong specialists or do not receive appropriate follow-up care", "4"),
        ("Very Dissatisfied: Major improvements needed, many patients are referred to the wrong specialists or do not receive appropriate follow-up care",      "5"),
    ]
    Q149_NOT_SAT = [
        ("Facilities are overcrowded/overcapacity and do not accept our patient referrals", "1"),
        ("The referral process is slow",                                     "2"),
        ("There is poor coordination between our facility and referred facilities",                         "3"),
        ("Other (specify)",                                              "4"),
    ]

    items = []
    items.append(yes_no("Q122_NBB_CURR",
                        "122. Do you currently implement the No Balance Billing (NBB) for your patients?"))
    items.append(yes_no("Q123_NBB_ALL_PATIENTS",
                        "123. Are you able to implement NBB for all patients, to the best of your knowledge, for the last 6 months?"))
    items.extend(checkbox_multiselect("Q124_NBB_BARRIERS",
                            "124. In your view, what are some of the barriers to implementing NBB?",
                            _cb_codes(NBB_ZBB_BARRIERS)))
    items.append(yes_no("Q125_ZBB_CURR",
                        "125. Do you currently implement the Zero Balance Billing (ZBB) for your patients?"))
    items.append(yes_no("Q126_ZBB_ALL_PATIENTS",
                        "126. Are you able to implement ZBB for all patients, to the best of your knowledge, for the last six months?"))
    items.extend(checkbox_multiselect("Q127_ZBB_BARRIERS",
                            "127. In your view, what are some of the barriers to implementing ZBB?",
                            _cb_codes(NBB_ZBB_BARRIERS)))
    items.append(yes_no("Q128_ALLOW_OOP_BASIC",
                        "128. Does the facility allow out-of-pocket (OOP) expenses for basic accommodation?"))
    items.append(alpha("Q129_OOP_REASON",
                       "129. Why does the facility allow OOP expenses for basic accommodation? Specify the reason.",
                       length=240))
    items.append(select_one("Q130_DIFFICULT_BENEFIT",
                            "130. Which of the UHC benefits do you find most difficult to implement?",
                            Q130_DIFFICULT_BENEFIT))
    items.append(alpha("Q130_OTHER_TXT",
                       "130. Which of the UHC benefits do you find most difficult to implement? Other (specify)",
                       length=120))
    items.extend(checkbox_multiselect("Q131_DIFFICULT_REASON",
                            "131. Why is this difficult to implement?", _cb_codes(Q131_REASONS)))
    items.append(yes_no("Q132_MALASAKIT_PROVIDED",
                        "132. Has the facility been providing medical social welfare or assistance (e.g., through Malasakit Centers, MAIFIP)?"))
    items.extend(checkbox_multiselect("Q133_MALASAKIT_WHY",
                            "133. Why is the facility providing medical social welfare or assistance through Malasakit Centers or MAIFIP?",
                            _cb_codes(Q133_MALASAKIT_WHY)))
    items.extend(checkbox_multiselect("Q134_NO_MALASAKIT_WHY",
                            "134. Why is the facility not providing medical social welfare or assistance through Malasakit Centers or MAIFIP?",
                            _cb_codes(Q134_NO_MALASAKIT_WHY)))
    items.append(yes_no("Q135_LGU_SUPPORT",
                        "135. Do you receive any support from your LGU to implement UHC reforms?"))
    items.extend(checkbox_multiselect("Q136_LGU_SUPPORT_FORMS",
                            "136. What forms of support do you receive?", _cb_codes(Q136_LGU_FORMS)))
    items.append(yes_no("Q137_LGU_SATISFIED",
                        "137. Are you satisfied with the support you receive from your LGU?"))
    items.extend(checkbox_multiselect("Q138_LGU_NOT_SAT_WHY",
                            "138. Why not?", _cb_codes(Q138_NOT_SAT_WHY)))
    items.append(select_one("Q139_PHO_PROTOCOL_CLARITY",
                            "139. How clear are the protocols regarding which decisions require Provincial Health Office (PHO) approval versus those you can decide at the facility level?",
                            Q139_CLARITY))
    items.append(alpha("Q140_UNCLEAR_PROTOCOL",
                       "140. Which specific protocol that you consider as unclear?", length=240))
    items.append(numeric("Q141_NUM_REFERRED_OUT",
                         "141. In the past 6 months, how many patients were referred to a higher-level facility within the referral network?",
                         length=6))
    items.extend(checkbox_multiselect("Q142_SEND_REFERRAL_HOW",
                            "142. What are the most common ways you send referrals to higher level facilities/specialists?",
                            _cb_codes(Q142_SEND_REF)))
    items.extend(checkbox_multiselect("Q143_REFERRAL_FORM_TYPE",
                            "143. What type of referral form do you use to send to higher level facilities?",
                            _cb_codes(Q143_FORM_TYPE)))
    items.append(select_one("Q144_SPECIALIST_NETWORK",
                            "144. Do you have a network of specialist providers to refer patients to, if needed?",
                            Q144_NETWORK))
    items.append(select_one("Q145_REF_PROPORTION",
                            "145. Considering all patients who come to your facility for the past 6 months, what is the proportion of patients referred by another facility compared to those who self-refer/walk-in?",
                            Q145_PROPORTION))
    items.extend(checkbox_multiselect("Q146_RECEIVE_REFERRAL_HOW",
                            "146. Of those referred, which of the following are the most common ways you receive referrals from lower-level health facilities?",
                            _cb_codes(Q146_RECEIVE_REF)))
    # with_other_txt=False: 'Other, (specify)' stays a tickable checkbox option (99) with no
    # companion free-text box — matching the prior select_one (which also captured no specify
    # text). F1's hand-fmf + inject_blocks re-block EXISTING fields only; a new _OTHER_TXT item
    # would orphan (UNREACHABLE) without a hand-added form field. Specify-text capture is a
    # separate small follow-up if ASPSI wants it (#734 comment).
    items.extend(checkbox_multiselect("Q147_EXTERNAL_SERVICES_GO",
                            "147. Where do your patients go to get the services not available at this facility?",
                            Q147_EXTERNAL, with_other_txt=False))
    items.append(select_one("Q148_REF_SATISFACTION",
                            "148. How would you rate your satisfaction with your current referral system?",
                            Q148_SATISFACTION))
    items.extend(checkbox_multiselect("Q149_NOT_SATISFIED_WHY",
                            "149. Why are you not satisfied with the current referral system?",
                            _cb_codes(Q149_NOT_SAT)))
    return record("G_SERVICE_DELIVERY", "G. Service Delivery Process", "8", items)


# ============================================================
# 12. RECORD BUILDERS — Section H. Human Resources (Q150-Q153)
# ============================================================
# Aug-17: was Q163-Q166. Straight -13 renumber.

def build_section_h():
    Q150_CHALL = [
        # #1037: code 3 was a copy-paste DUP of code 2 (should be Retention — live
        # regression in v1.2.3); "Multi-tasking" was missing entirely. Codes 1-4 and
        # Other are unchanged from the corrected list.
        # Aug-17: the printed list is FIVE options — the "I don't know" that #1126
        # added from ASPSI's 2026-08-06 list is NOT on the Aug-17 paper, so it is
        # dropped here. Every surviving option keeps its code (01-04, 99); only the
        # exclusive 90 disappears with its option. Flagged for ASPSI in the Task 2.2
        # report since it reverses a request they made 11 days before this paper.
        ("Understaffing",                    "1"),
        ("Skills mismatch / lack of skills", "2"),
        ("Retention / high staff turnover",  "3"),
        ("Multi-tasking",                    "4"),
        ("Other (specify)",                  "5"),
    ]
    PD_DOCTORS = [
        ("Clinical audits",                                          "1"),
        ("Surgical audits",                                          "2"),
        ("Quality assurance meetings",                               "3"),
        ("Seminars, conferences, workshops",                         "4"),
        ("Support for independent professional development: scholarships",    "5"),   # #1038 verbatim
        ("Support for independent professional development: research grants", "6"),   # #1038 verbatim
        ("LGU/DOH led workshops/initiatives",                        "7"),
        ("No forms of professional development are provided to our doctors",  "8"),   # #1038 verbatim
        ("Other (specify)",                                          "9"),
    ]
    # Aug-17 Q153 CONFIRMS the long-standing default: the printed nurse list omits
    # "Clinical audits" and "Surgical audits". The old Q166_NURSES_INCLUDE_AUDITS
    # toggle is retired with this confirmation.
    PD_NURSES = [
        ("Quality assurance meetings",                               "1"),
        ("Seminars, conferences, workshops",                         "2"),
        ("Support for independent professional development: scholarships",    "3"),   # #1039 verbatim
        ("Support for independent professional development: research grants", "4"),   # #1039 verbatim
        ("LGU/DOH led workshops/initiatives",                        "5"),
        ("No forms of professional development are provided to our nurses",   "6"),   # #1039 verbatim
        ("Other (specify)",                                          "7"),
    ]

    items = []
    items.extend(checkbox_multiselect("Q150_HR_CHALL",
                            "150. What challenges in human resources do you have?", _cb_codes(Q150_CHALL)))
    items.append(alpha("Q151_IMPROVEMENT_AREA",
                       "151. What area do you find the most room for improvement in your staff?", length=240))
    items.extend(checkbox_multiselect("Q152_PD_DOCTORS",
                            "152. What forms of professional development do you provide to your doctors?",
                            _cb_codes(PD_DOCTORS)))
    items.extend(checkbox_multiselect("Q153_PD_NURSES",
                            "153. What forms of professional development do you provide to your nurses?",
                            _cb_codes(PD_NURSES)))
    return record("H_HUMAN_RESOURCES", "H. Human Resources for Health", "9", items)


def build_secondary_data_stubs():
    """Bug #2 — secondary data records. Structure is PENDING DESIGN so we emit
    empty stubs that exist in the dictionary but contain no items yet.

    RETAINED for Aug-17 unchanged: the paper moved Secondary Data to an annex, but
    the consent script still promises it and Carl's 2026-08-18 ruling keeps both in
    the CAPI (registered `system-item`)."""
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
        # Single-number redesign: REGION/PROVINCE_HUC/CITY_MUNICIPALITY stay in the
        # dict but go OFF-FORM (logic-set to the full PSGC codes from the
        # Questionnaire Number); the form shows the read-only *_NAME items +
        # the BARANGAY picker. Keeping the four geo fields lets the shared
        # PSGC-Cascade.apc functions compile unchanged.
        build_geo_id("facility"),
        build_capture_record(),
        build_section_icf(),
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
                    # Single 12-digit Questionnaire Number (RR-PP-MMM-FF-CCC encoded).
                    # Redesign 2026-06-10: component codes are derived in logic from
                    # this number and live as non-id FIELD_CONTROL items (see
                    # build_field_control + the QUESTIONNAIRE_NUMBER postproc in the .apc).
                    "items": [
                        {"name": "QUESTIONNAIRE_NUMBER",
                         "labels": [{"text": "Questionnaire Number (12-digit: RR-PP-MMM-FF-CCC)"}],
                         "contentType": "numeric", "start": 2, "length": 12, "zeroFill": True},
                    ]
                },
                "records": [r for r in records if r.get("name") != "FACILITYHEADSURVEY_REC"],
            }
        ],
    }


def main():
    out_path = Path(__file__).parent / "FacilityHeadSurvey.dcf"
    dictionary = build_dictionary()
    dictionary = apply_translations(dictionary, Path(__file__).parent / "translations")
    # write_dcf (shared, F3/F4 parity) replaces F1's own raw json.dumps: byte-for-byte
    # the same output, plus it NAMES any label it has to cut at CSPro's 255-char cap.
    # F1 previously wrote raw, which is how the #1189 Q88 over-cap label reached the
    # Designer unnoticed and got silently hard-cut on round-trip.
    write_dcf(dictionary, out_path)


if __name__ == "__main__":
    main()
