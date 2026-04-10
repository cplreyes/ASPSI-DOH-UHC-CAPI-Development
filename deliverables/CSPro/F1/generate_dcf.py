"""
Generator for FacilityHeadSurvey.dcf (CSPro 8.0 JSON dictionary).

Source of truth: raw/Project-Deliverable-1/Annex F1 ... April 08.pdf
Run: python generate_dcf.py  -> writes FacilityHeadSurvey.dcf next to this script.

Conventions
-----------
- Each survey question becomes one item, named Q{n}_{SHORT}.
- "Select one" questions: single numeric item + value set.
- "Yes / No" questions: single numeric item + Q{n}_VS1 (1=Yes, 2=No).
- "Select all that apply" questions: each option becomes its own dichotomous
  item Q{n}_O{k}_{SHORT}, value set 1=Yes/0=No (CSPro CAPI renders as checkboxes).
- "Other (specify)" options also get a sibling alpha item Q{n}_OTHER_TXT.
- Open-ended text answers: alpha item, length 200 by default.
- Numeric counts/durations: numeric, length sized to expected magnitude.
- The standardized 9-option UHC response set is defined once (UHC9) and reused
  via inline copies (CSPro JSON dictionaries inline value sets per item).

This is a v1 cut for bench-testing in CSPro Designer. Carl will refine in the
designer; the script can be re-run after structural edits to the source list.
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Reusable value sets
# ---------------------------------------------------------------------------

YES_NO = [
    ("1", "Yes"),
    ("2", "No"),
]

YES_NO_DK = [
    ("1", "Yes"),
    ("2", "No"),
    ("8", "I don't know"),
]

YES_NO_DK_NA = [
    ("1", "Yes"),
    ("2", "No"),
    ("8", "I don't know"),
    ("9", "Not applicable"),
]

DICHOTOMOUS = [  # for "select all that apply" sub-items
    ("0", "Not selected"),
    ("1", "Selected"),
]

# Standardized UHC implementation 9-option response set, repeated dozens of times
UHC9 = [
    ("1", "Yes, this was implemented as a direct result of the UHC Act"),
    ("2", "Yes, this was pre-existing, but it has significantly improved due to the UHC Act"),
    ("3", "Yes, this has been implemented or improved recently, but not due to the UHC Act"),
    ("4", "Yes, other reason (specify)"),
    ("5", "No, this has not been implemented yet, but we plan to in the next 1-2 years"),
    ("6", "No, and we have no plans to do this in the next 1-2 years"),
    ("7", "No, other reason (specify)"),
    ("8", "I don't know"),
    ("9", "Not applicable"),
]

DURATION_BUCKET = [
    ("1", "Less than a month"),
    ("2", "1-2 months"),
    ("3", "3-4 months"),
    ("4", "5-6 months"),
    ("5", "More than 6 months"),
]

# Common reasons set for "why difficult to comply" questions
DIFFICULTY_REASONS_BASE = [
    "Not enough budget / too expensive",
    "Time-consuming",
    "Limited human resources",
    "Legal processes",
    "Stringent standards",
    "Other (specify)",
]

DIFFICULTY_REASONS_LICENSING = [
    "Not enough budget / too expensive",
    "Time-consuming",
    "Limited human resources",
    "Legal processes",
    "Compiling documentary requirements",
    "Stringent standards",
    "Lack of training",
    "Lack of space",
    "Other (specify)",
]

# ---------------------------------------------------------------------------
# Helpers to build CSPro JSON structures
# ---------------------------------------------------------------------------


def _label(text: str) -> list[dict]:
    return [{"text": text}]


def _value_set(name: str, label: str, values: list[tuple[str, str]]) -> dict:
    return {
        "name": name,
        "labels": _label(label),
        "values": [
            {"labels": _label(v_label), "pairs": [{"value": v_code}]}
            for v_code, v_label in values
        ],
    }


def numeric(
    name: str,
    label: str,
    length: int,
    *,
    zero_fill: bool = False,
    value_set: list[tuple[str, str]] | None = None,
    vs_label: str | None = None,
) -> dict:
    item: dict = {
        "name": name,
        "labels": _label(label),
        "contentType": "numeric",
        "length": length,
        "zeroFill": zero_fill,
    }
    if value_set is not None:
        item["valueSets"] = [
            _value_set(f"{name}_VS1", vs_label or label, value_set)
        ]
    return item


def alpha(name: str, label: str, length: int = 200) -> dict:
    return {
        "name": name,
        "labels": _label(label),
        "contentType": "alpha",
        "length": length,
    }


def yes_no_item(qnum: int, short: str, label: str) -> dict:
    return numeric(f"Q{qnum}_{short}", label, length=1, value_set=YES_NO)


def select_one(
    qnum: int,
    short: str,
    label: str,
    options: list[str],
    *,
    length: int | None = None,
) -> dict:
    """Single numeric item with value set 1..N (and 'I don't know'/'NA' kept as-is if present)."""
    values: list[tuple[str, str]] = []
    code = 1
    for opt in options:
        values.append((str(code), opt))
        code += 1
    if length is None:
        length = 2 if len(values) > 9 else 1
    return numeric(
        f"Q{qnum}_{short}", label, length=length, zero_fill=(length > 1), value_set=values
    )


def select_all(
    qnum: int,
    short: str,
    label: str,
    options: list[str],
) -> list[dict]:
    """Expand a 'select all that apply' question into one binary item per option,
    plus a Q{n}_OTHER_TXT alpha if 'Other (specify)' appears.
    """
    items: list[dict] = []
    has_other = False
    for k, opt in enumerate(options, start=1):
        if "specify" in opt.lower():
            has_other = True
        slug = _slug(opt)[:30]
        items.append(
            numeric(
                f"Q{qnum}_O{k:02d}_{slug}",
                f"{label} -- {opt}",
                length=1,
                value_set=DICHOTOMOUS,
            )
        )
    if has_other:
        items.append(alpha(f"Q{qnum}_OTHER_TXT", f"{label} -- Other, specify", length=200))
    return items


def uhc9_item(qnum: int, short: str, label: str) -> list[dict]:
    """A standard 9-option UHC implementation question. Returns the main item
    plus the two 'other reason' specify text fields and an 'I don't know'/'NA'
    aware structure (the value set already encodes them)."""
    main = numeric(
        f"Q{qnum}_{short}",
        label,
        length=1,
        value_set=UHC9,
    )
    yes_other = alpha(
        f"Q{qnum}_YES_OTHER_TXT",
        f"{label} -- If 'Yes, other reason', specify",
        length=200,
    )
    no_other = alpha(
        f"Q{qnum}_NO_OTHER_TXT",
        f"{label} -- If 'No, other reason', specify",
        length=200,
    )
    return [main, yes_other, no_other]


def difficulty_reasons_block(
    base_q: int, target_q: int, area_label: str, reasons: list[str]
) -> list[dict]:
    """Generate the 'Why was it difficult to comply with X?' sub-items."""
    short = f"WHY_{_slug(area_label)[:20]}"
    return select_all(
        base_q,
        short,
        f"{base_q}. Why was it difficult to comply with: {area_label}",
        reasons,
    )


def _slug(text: str) -> str:
    out = []
    last_us = False
    for ch in text.upper():
        if ch.isalnum():
            out.append(ch)
            last_us = False
        else:
            if not last_us:
                out.append("_")
                last_us = True
    return "".join(out).strip("_")


# ---------------------------------------------------------------------------
# Records / items definition
# ---------------------------------------------------------------------------


def build_field_control() -> dict:
    return {
        "name": "FIELD_CONTROL",
        "labels": _label("Field Control"),
        "recordType": "A",
        "occurrences": {"required": True, "maximum": 1},
        "items": [
            alpha("QUESTIONNAIRE_NO", "Questionnaire No", length=20),
            alpha("SURVEY_TEAM_LEADER_NAME", "Survey Team Leader's Name", length=80),
            numeric("DATE_FIRST_VISIT", "Date First Visited the Facility (YYYYMMDD)", length=8),
            alpha("ENUMERATOR_NAME", "Enumerator's Name", length=80),
            alpha("FIELD_VALIDATED_BY", "Field Validated by", length=80),
            alpha("FIELD_EDITED_BY", "Field Edited by", length=80),
            numeric("DATE_FINAL_VISIT", "Date of Final Visit to the Facility (YYYYMMDD)", length=8),
            numeric(
                "ENUM_RESULT",
                "Result of visit",
                length=1,
                value_set=[
                    ("1", "Completed"),
                    ("2", "Postponed"),
                    ("3", "Refused"),
                    ("4", "Incomplete"),
                ],
            ),
            numeric("TOTAL_VISITS", "Total number of visits", length=2),
            numeric(
                "EDITED_RESULT",
                "Edited result",
                length=1,
                value_set=[
                    ("1", "Completed"),
                    ("2", "Postponed"),
                    ("3", "Refused"),
                    ("4", "Incomplete"),
                ],
            ),
        ],
    }


def build_geographic_id() -> dict:
    return {
        "name": "HEALTH_FACILITY_AND_GEOGRAPHIC_ID",
        "labels": _label("Health Facility and Geographic Identification"),
        "recordType": "B",
        "occurrences": {"required": True, "maximum": 1},
        "items": [
            numeric(
                "CLASSIFICATION",
                "Classification",
                length=1,
                value_set=[("1", "UHC IS"), ("2", "Non-UHC IS")],
            ),
            alpha("REGION", "Region", length=40),
            alpha("PROVINCE_HUC", "Province / HUC", length=60),
            alpha("CITY_MUNICIPALITY", "City / Municipality", length=60),
            alpha("BARANGAY", "Barangay", length=60),
            alpha("LATITUDE", "Latitude", length=20),
            alpha("LONGITUDE", "Longitude", length=20),
            alpha("LOCATION", "Location / address", length=200),
        ],
    }


def build_section_a() -> dict:
    items: list[dict] = []
    items.append(alpha("Q1_NAME", "1. Name of facility head (Last, First, MI, Ext)", length=100))
    items.append(
        select_one(
            2,
            "DESIGNATION",
            "2. What is your official designation at this health facility?",
            [
                "Rural Health Unit / Health Center Head",
                "Hospital Administrator",
                "Administrative Officer / Assistant",
                "Physician",
                "Nurse",
                "Midwife",
                "Chief of Hospital",
                "Municipal / City Health Officer",
                "Health Promotion / Nutrition Officer",
                "Medical Director",
                "Medical Officer",
                "Rural Health Physician",
                "Other (specify)",
            ],
        )
    )
    items.append(alpha("Q2_DESIGNATION_OTHER_TXT", "2. Other designation, specify", length=100))
    items.append(numeric("Q3_AGE", "3. How old are you (in completed years)?", length=3))
    items.append(
        numeric(
            "Q4_SEX",
            "4. Sex assigned at birth",
            length=1,
            value_set=[("1", "Male"), ("2", "Female")],
        )
    )
    items.append(numeric("Q5_YEARS_AT_FACILITY", "5. Years worked at this facility", length=2))
    items.append(numeric("Q5_MONTHS_AT_FACILITY", "5. Months worked at this facility", length=2))
    items.append(numeric("Q6_YEARS_HEALTH", "6. Years worked in any health-related position", length=2))
    items.append(numeric("Q6_MONTHS_HEALTH", "6. Months worked in any health-related position", length=2))
    return {
        "name": "A_FACILITY_HEAD_PROFILE",
        "labels": _label("A. Facility Head Profile"),
        "recordType": "2",
        "occurrences": {"required": True, "maximum": 1},
        "items": items,
    }


def build_section_b() -> dict:
    items = [
        numeric(
            "Q7_OWNERSHIP",
            "7. Type of ownership",
            length=1,
            value_set=[("1", "Public"), ("2", "Private")],
        ),
        select_one(
            8,
            "SERVICE_LEVEL",
            "8. Facility service capacity level",
            [
                "Primary Care Facility",
                "Level 1 Hospital",
                "Level 2 Hospital",
                "Level 3 Hospital",
            ],
        ),
    ]
    return {
        "name": "B_FACILITY_PROFILE",
        "labels": _label("B. Facility Profile"),
        "recordType": "3",
        "occurrences": {"required": True, "maximum": 1},
        "items": items,
    }


def build_section_c() -> dict:
    items: list[dict] = []
    items.append(yes_no_item(9, "HEARD_UHC", "9. Have you heard about UHC prior to this survey?"))
    items.append(yes_no_item(10, "HAS_PRIMARY_PKG", "10. Does the facility have primary care packages?"))
    items.append(
        select_one(
            11,
            "PRIMARY_PKG_STATUS",
            "11. Implementation status of primary care packages relative to UHC Act",
            [
                "Implemented as a direct result of the UHC Act (i.e. YAKAP/Konsulta)",
                "Pre-existing prior to UHC but subsequently enhanced or expanded due to UHC Act",
                "Newly implemented or improved independent of UHC Act",
                "Not yet implemented but planned within the next 1-2 years",
                "Other (specify)",
                "I don't know",
                "Not applicable",
            ],
            length=2,
        )
    )
    items.append(alpha("Q11_OTHER_TXT", "11. Other, specify", length=200))

    items.extend(uhc9_item(12, "PCB_LICENSING", "12. Has the facility applied for DOH primary care licensing since UHC Act?"))
    items.append(yes_no_item(13, "PUBLIC_HEALTH_UNIT", "13. Do you have a public health unit at this facility?"))
    items.extend(uhc9_item(14, "PHU_CREATED", "14. Has the creation of a public health unit been implemented since UHC Act?"))
    items.append(
        select_one(
            15,
            "PHU_ROLE",
            "15. Main role of the public health unit",
            [
                "Health promotion and education",
                "Disease surveillance report",
                "Referral and patient navigation",
                "Alignment with national public health programs",
                "Other (specify)",
                "I don't know",
                "Not applicable",
            ],
        )
    )
    items.append(alpha("Q15_OTHER_TXT", "15. Other PHU role, specify", length=200))

    items.append(yes_no_item(16, "HEALTH_PROMO_UNIT", "16. Do you have a health promotion unit at this facility?"))
    items.extend(uhc9_item(17, "HPU_CREATED", "17. Has the creation of a health promotion unit been implemented since UHC Act?"))
    items.append(
        select_one(
            18,
            "HPU_ROLE",
            "18. Main role of the health promotion unit",
            [
                "Leading health education and awareness campaigns",
                "Conducting and coordinating health screening and promotion activities",
                "Advocacy and policy formation",
                "Resource mobilization and fundraising",
                "Other (specify)",
                "I don't know",
            ],
        )
    )
    items.append(alpha("Q18_OTHER_TXT", "18. Other HPU role, specify", length=200))

    items.extend(uhc9_item(19, "NEW_ROLES", "19. Has the establishment of new roles been implemented since UHC Act?"))
    items.append(alpha("Q20_NEW_ROLES_TXT", "20. New roles established (list)", length=400))
    items.extend(uhc9_item(21, "NEW_DEPTS", "21. Has the establishment of new departments been implemented since UHC Act?"))
    items.append(alpha("Q22_NEW_DEPTS_TXT", "22. New departments established (list)", length=400))
    items.extend(uhc9_item(23, "NEW_BUILDINGS", "23. Has the construction of new buildings been implemented since UHC Act?"))
    items.append(alpha("Q24_BUILDINGS_USE_TXT", "24. What are the buildings being used for?", length=400))
    items.extend(uhc9_item(25, "NEW_ROOMS", "25. Has the construction of new rooms been implemented since UHC Act?"))
    items.append(alpha("Q26_ROOMS_USE_TXT", "26. What are the rooms being used for?", length=400))
    items.extend(uhc9_item(27, "INC_EQUIPMENT", "27. Has the increase in equipment been implemented since UHC Act?"))
    items.append(alpha("Q28_EQUIPMENT_TXT", "28. Equipment that increased (list)", length=400))
    items.extend(uhc9_item(29, "INC_SUPPLIES", "29. Has the increase in supplies been implemented since UHC Act?"))
    items.append(alpha("Q30_SUPPLIES_TXT", "30. Supplies that increased (list)", length=400))
    items.extend(uhc9_item(31, "EMR_USE", "31. Has the use of electronic medical records been implemented since UHC Act?"))

    items.append(
        select_one(
            32,
            "DATA_SUBMIT",
            "32. Does facility submit health/financial data to DOH IS / PhilHealth Dashboard?",
            [
                "Yes, to DOH Information System only",
                "Yes, to PhilHealth Dashboard only",
                "Yes, to both DOH IS and PhilHealth Dashboard",
                "No, we are not submitting these data",
            ],
        )
    )
    items.append(
        select_one(
            33,
            "DATA_FREQ",
            "33. How frequently does facility submit data?",
            [
                "Weekly",
                "Monthly",
                "Quarterly",
                "Semi-annually",
                "Annually",
                "Other (specify)",
            ],
        )
    )
    items.append(alpha("Q33_OTHER_TXT", "33. Other frequency, specify", length=100))
    items.extend(
        select_all(
            34,
            "REPORTS_USED",
            "34. Submitted reports actually used for decision-making",
            [
                "OPD/IPD census and morbidity reports",
                "MNCAH reports",
                "Notifiable diseases / surveillance reports",
                "Expenditure and budget utilization reports",
                "PhilHealth claims and reimbursement reports",
                "YAKAP/Konsulta utilization reports",
                "NBB compliance",
                "ZBB compliance / monitoring reports",
                "HRH staffing and deployment reports",
                "Medicines availability and stock status reports",
                "Facility performance scorecards / quality reports",
                "Other (specify)",
            ],
        )
    )

    items.append(yes_no_item(35, "STAFFING_CHANGED", "35. Have there been changes in facility staffing since 2019?"))
    items.extend(uhc9_item(36, "STAFFING_UHC", "36. Have changes in staffing been implemented since UHC Act?"))
    items.append(yes_no_item(37, "REFERRAL_CHANGED", "37. Have there been changes in the referral system since 2019?"))
    items.extend(uhc9_item(38, "REFERRAL_UHC", "38. Have changes to referral system been implemented since UHC Act?"))
    items.extend(uhc9_item(39, "MOU_HCPN", "39. Has MoU/MoA with HCPN partners been implemented since UHC Act?"))
    items.extend(uhc9_item(40, "NBB_IMPL", "40. Has NBB been implemented since UHC Act?"))
    items.extend(uhc9_item(41, "ZBB_IMPL", "41. Has ZBB been implemented since UHC Act?"))
    items.extend(uhc9_item(42, "NO_COPAY", "42. Has the no co-payment policy been implemented since UHC Act?"))
    items.extend(uhc9_item(43, "WARD_ALLOC", "43. Has ward accommodation allocation been implemented since UHC Act?"))
    items.extend(uhc9_item(44, "CLINICAL_GUIDES", "44. Have improved clinical practice guidelines been implemented since UHC Act?"))
    items.extend(uhc9_item(45, "DOH_LIC_STD", "45. Have DOH licensing standards been implemented since UHC Act?"))
    items.extend(uhc9_item(46, "PHIC_ACCRED", "46. Have PhilHealth accreditation requirements been implemented since UHC Act?"))
    items.extend(uhc9_item(47, "SVC_DEL_PROTO", "47. Have service delivery protocols been implemented since UHC Act?"))
    items.extend(uhc9_item(48, "PCQM", "48. Have primary care quality measures been implemented since UHC Act?"))

    quality_options = [
        "Limited resources (manpower, equipment, supplies, funding)",
        "Challenging quality standards",
        "Decisions made by LGU not facility",
        "Lack of specific healthcare skills",
        "Inadequate training of healthcare workers",
        "Lack of patient awareness of UHC benefits",
        "Limited accessibility of public facilities",
        "Infrastructure not conducive for patient care",
        "I don't know",
        "Other (specify)",
    ]
    items.extend(select_all(49, "QUALITY_CHALL", "49. Major challenges to improving quality of patient care", quality_options))
    items.extend(select_all(50, "ACCESS_CHALL", "50. Major challenges to improving accessibility of patient care", quality_options))

    return {
        "name": "C_UHC_IMPLEMENTATION",
        "labels": _label("C. Universal Health Care (UHC) Implementation"),
        "recordType": "4",
        "occurrences": {"required": True, "maximum": 1},
        "items": items,
    }


def build_section_d() -> dict:
    items: list[dict] = []
    items.append(yes_no_item(51, "YK_ACCRED", "51. Are you currently an accredited YAKAP/Konsulta provider?"))
    items.append(numeric("Q52_YK_SINCE_MONTH", "52. YAKAP/Konsulta accreditation - month", length=2))
    items.append(numeric("Q52_YK_SINCE_YEAR", "52. YAKAP/Konsulta accreditation - year", length=4))
    items.extend(
        select_all(
            53,
            "YK_PKG_INCL",
            "53. Items included in YAKAP/Konsulta package at this facility",
            [
                "Pap smear",
                "Mammogram",
                "Lipid profile",
                "Thyroid function test",
                "Chest X-ray",
                "Low-dose CT scan",
                "Dental services",
                "All of the above",
                "I don't know",
                "Other (specify)",
            ],
        )
    )
    items.append(yes_no_item(54, "REG_INDIV", "54. Possible to register individual patients to YAKAP/Konsulta?"))
    items.append(yes_no_item(55, "REG_FAMILY", "55. Possible to register whole families?"))
    items.append(yes_no_item(56, "REG_BOTH", "56. Only possible to register both individual + family together?"))
    items.append(numeric("Q57_CAPITATION_AMT", "57. Capitation amount of YAKAP/Konsulta package (PHP)", length=8))
    items.extend(
        select_all(
            58,
            "PERF_INDIC",
            "58. Performance indicators for second tranche payment",
            [
                "Beneficiaries consulted a primary care doctor",
                "Utilization of laboratory services",
                "Beneficiaries received antibiotics as prescribed",
                "Beneficiaries received NCD medicine as prescribed",
                "No requirements",
                "1st patient encounter",
                "I don't know",
                "Other (specify)",
            ],
        )
    )
    items.append(yes_no_item(59, "KNOW_PAY_FREQ", "59. Do you know how often you should receive payments from PhilHealth?"))
    items.append(
        select_one(
            60,
            "PAY_FREQ",
            "60. How often should you be receiving payments?",
            ["Monthly", "Quarterly", "Semi-annually", "Annually"],
        )
    )
    items.append(yes_no_item(61, "TRANCHE_DELAY", "61. Were there delays in receiving capitation tranches?"))
    items.append(alpha("Q61_DELAY_REASON_TXT", "61.1 Reasons for delay", length=400))
    items.append(
        select_one(
            62,
            "TRANCHE_INTERVAL",
            "62. Typical interval between tranche releases",
            [
                "Less than a month",
                "1-2 months",
                "3-4 months",
                "5-6 months",
                "More than six months",
            ],
        )
    )
    items.append(
        select_one(
            63,
            "ACCRED_WAIT",
            "63. Days waited from application submission to accreditation approval",
            [
                "Less than a month",
                "1-2 months",
                "3-4 months",
                "5-6 months",
                "More than six months",
            ],
        )
    )
    items.extend(
        select_all(
            64,
            "WHY_APPLY",
            "64. Why did you apply to become a YAKAP/Konsulta provider?",
            [
                "Incentives (capitation/payment for registered patients)",
                "Aligns with facility's mission",
                "Encouraged by LGU",
                "Mandated/required by DOH/UHC",
                "To improve facility services",
                "Other (specify)",
            ],
        )
    )

    accred_reqs = [
        "Ability to conduct preventive/screening services and health education",
        "Capability to provide laboratory and radiologic services",
        "Capability to dispense required medicines",
        "General Infrastructure",
        "Equipment and Supplies",
        "Human resource",
        "Functional Health Information System",
        "Documentary requirements",
        "DOH licensing requirements",
        "None of the above",
    ]
    items.extend(
        select_all(
            65,
            "ACCRED_DIFFICULT",
            "65. Which accreditation requirements were difficult to comply with?",
            accred_reqs,
        )
    )
    # Q66-74: per-area "why difficult" sub-questions reuse DIFFICULTY_REASONS_BASE
    why_areas = [
        (66, "preventive/screening services and health education"),
        (67, "laboratory and radiologic services"),
        (68, "dispensing required medicines"),
        (69, "general infrastructure"),
        (70, "equipment and supplies"),
        (71, "human resource"),
        (72, "functional health information system"),
        (73, "documentary requirements"),
        (74, "DOH licensing requirements"),
    ]
    for qnum, area in why_areas:
        items.extend(
            select_all(
                qnum,
                f"WHY_DIFF_{qnum}",
                f"{qnum}. Why difficult to comply with: {area}",
                DIFFICULTY_REASONS_BASE,
            )
        )

    items.extend(
        select_all(
            75,
            "WHO_ENROLL",
            "75. Whose responsibility is it to enroll patients to YAKAP/Konsulta?",
            [
                "Patients' own initiative",
                "Facility",
                "LGU",
                "Someone else",
                "PhilHealth",
                "I don't know",
                "Other (specify)",
            ],
        )
    )
    items.extend(
        select_all(
            76,
            "ENROLL_INIT",
            "76. Initiatives done to enroll patients in this facility",
            [
                "On-site Enrollment",
                "LGU Outreach",
                "Facility Outreach",
                "Barangay Health Workers (BHWs) Support",
                "Information Campaigns",
                "LHIO assistance / YAKAP-Konsulta caravans",
                "Coordination with other government agencies and private sector",
                "No initiatives",
                "Other (specify)",
            ],
        )
    )
    items.append(yes_no_item(77, "ENROLL_CHALL", "77. Did you experience any challenges in enrolling patients?"))
    items.extend(
        select_all(
            78,
            "ENROLL_CHALL_TYPES",
            "78. What enrollment challenges did you face?",
            [
                "Lack of patient awareness",
                "Lack of patient willingness",
                "Lack of resources",
                "Competition with other facilities",
                "Technical/system issues of PhilHealth",
                "Other (specify)",
            ],
        )
    )

    # Non-accredited path Q79-84
    items.extend(
        select_all(
            79,
            "NOT_ACCRED_REASON",
            "79. If not accredited, why?",
            [
                "Difficult process",
                "No time",
                "Ongoing application",
                "Other (specify)",
            ],
        )
    )
    items.append(
        select_one(
            80,
            "INTEND_ACCRED",
            "80. Are you intending to become a YAKAP/Konsulta provider?",
            [
                "Yes, already in process",
                "Yes, not yet in process",
                "No, decided not to",
                "No, tried and failed",
                "No, haven't thought about it yet",
                "I don't know",
            ],
        )
    )
    items.append(yes_no_item(81, "KNOW_HOW_START", "81. Would you know how to start the application?"))
    items.append(alpha("Q82_DECIDING_FACTOR_TXT", "82. Deciding factor not to apply", length=400))
    items.append(alpha("Q83_APP_FAILED_TXT", "83. What went wrong with the application?", length=400))
    items.append(alpha("Q84_PROCESS_CHALL_TXT", "84. Challenges in the process", length=400))

    items.append(alpha("Q85_CATCHMENT_AREA_TXT", "85. Facility's catchment area(s)", length=400))
    items.append(numeric("Q86_ELIGIBLE_PATIENTS", "86. Eligible patients in catchment area", length=8))
    items.append(numeric("Q87_REGISTERED_PATIENTS", "87. Eligible patients already registered", length=8))
    items.append(
        select_one(
            88,
            "CAPITATION_ENOUGH",
            "88. Is the PHP 1,700 maximum per capita rate enough?",
            ["Yes", "No", "I don't know"],
        )
    )
    items.append(
        select_one(
            89,
            "COSTING_DONE",
            "89. Did you go through a costing exercise?",
            ["Yes", "No", "I don't know"],
        )
    )
    items.append(
        select_one(
            90,
            "COSTING_VIABLE",
            "90. Did the costing exercise show PHP 1,700 was viable?",
            ["Yes", "No", "I don't know"],
        )
    )
    items.append(numeric("Q91_MIN_CAP_VALUE_ACC", "91. Minimum acceptable capitation per patient/year (accredited)", length=8))
    items.append(numeric("Q92_MIN_CAP_VALUE_NONACC", "92. Minimum acceptable capitation per patient/year (non-accredited)", length=8))
    items.append(yes_no_item(93, "CHARGE_ADDL_CAP", "93. Does facility charge additional capitation fees?"))
    items.extend(
        select_all(
            94,
            "ADDL_CAP_REASON",
            "94. Reasons for charging additional capitation fees",
            [
                "Building maintenance, equipment, non-clinical staff",
                "Patient care costs exceed fixed payment",
                "Services excluded from capitation coverage",
                "Provide preventive care not adequately compensated",
                "Offset losses",
                "Other (specify)",
            ],
        )
    )
    items.append(
        select_one(
            95,
            "RECEIVED_PAYMENTS",
            "95. Have you received payments for patients enrolled?",
            [
                "Yes, all expected payments received",
                "Yes, some but not all expected payments received",
                "No, not received any expected payments yet",
                "No, not expected any payments yet",
            ],
        )
    )
    items.extend(
        select_all(
            96,
            "WHY_NO_PAYMENT",
            "96. Why have payments not been received?",
            [
                "Delays in PhilHealth processing",
                "Delays in facility tracking of patient enrollment",
                "Difficulties verifying patient enrollment (PhilHealth)",
                "Facility not active in meeting criteria",
                "Criteria for payments unclear",
                "I don't know",
                "Other (specify)",
            ],
        )
    )
    items.append(yes_no_item(97, "PAYMENT_CHALL", "97. Did you face challenges in getting payments?"))
    items.extend(
        select_all(
            98,
            "PAYMENT_CHALL_TYPES",
            "98. What were the payment challenges?",
            [
                "Delayed payment process",
                "Unclear criteria for capitation",
                "Difficult to meet criteria for capitation",
                "PhilHealth process to apply unclear/difficult",
                "I don't know",
                "Other (specify)",
            ],
        )
    )
    items.extend(
        select_all(
            99,
            "EXPAND_NEXT",
            "99. If expanding YAKAP/Konsulta, what would you expand next?",
            [
                "Current list of medicines and drugs offered",
                "Current laboratory/diagnostic services offered",
                "Additional features",
                "I don't know",
                "Other (specify)",
            ],
        )
    )
    items.append(alpha("Q100_ADDL_FEATURES_TXT", "100. Additional features to add", length=400))

    return {
        "name": "D_YAKAP_KONSULTA",
        "labels": _label("D. YAKAP / Konsulta Package"),
        "recordType": "5",
        "occurrences": {"required": True, "maximum": 1},
        "items": items,
    }


def build_section_e() -> dict:
    items: list[dict] = []
    items.append(yes_no_item(101, "HEARD_BUCAS", "101. Have you heard about BUCAS?"))
    items.append(
        select_one(
            102,
            "HAS_BUCAS",
            "102. Do you have a BUCAS Center?",
            ["Yes", "No", "I don't know"],
        )
    )
    items.append(
        select_one(
            103,
            "NO_BUCAS_REASON",
            "103. Primary reason for no BUCAS Center",
            [
                "Proposal not yet submitted",
                "Did not meet standard requirements",
                "Awaiting assessment or approval",
                "Limited information on establishment process",
                "Not applicable",
                "Other (specify)",
            ],
        )
    )
    items.append(alpha("Q103_OTHER_TXT", "103. Other reason, specify", length=200))
    items.extend(
        select_all(
            104,
            "BUCAS_SVC",
            "104. Available services at BUCAS Center",
            [
                "Urgent care and consultation",
                "Minor surgical procedures",
                "Diagnostic and laboratory services",
                "Reproductive and special health services",
                "Other (specify)",
            ],
        )
    )
    items.extend(
        select_all(
            105,
            "BUCAS_FACTORS",
            "105. Factors affecting BUCAS utilization",
            [
                "Patient awareness",
                "Referral patterns",
                "Availability of staff/services",
                "Facility location and accessibility",
                "PhilHealth coverage and reimbursement",
                "Other (specify)",
            ],
        )
    )
    items.append(alpha("Q106_BUCAS_RESOURCES_TXT", "106. Resources needed to support BUCAS", length=400))
    items.append(yes_no_item(107, "BUCAS_DECONGEST", "107. Does BUCAS Center decongest your facility?"))

    items.append(yes_no_item(108, "HEARD_GAMOT", "108. Have you heard about GAMOT?"))
    items.append(yes_no_item(109, "GAMOT_ACCRED", "109. Is your facility a GAMOT accredited provider?"))
    items.append(
        select_one(
            110,
            "NO_GAMOT_REASON",
            "110. Primary reason for not being GAMOT accredited",
            [
                "Application not yet submitted",
                "Did not meet accreditation requirements",
                "Awaiting assessment or approval",
                "Limited information on accreditation process",
                "Not applicable",
                "Other (specify)",
            ],
        )
    )
    items.append(alpha("Q110_OTHER_TXT", "110. Other reason, specify", length=200))
    items.extend(
        select_all(
            111,
            "GAMOT_FACTORS",
            "111. Factors affecting GAMOT utilization",
            [
                "Availability of GAMOT medicines",
                "Patient awareness of program",
                "Prescribing practices of physicians",
                "Pharmacy capacity",
                "PhilHealth eligibility and reimbursement",
                "Other (specify)",
            ],
        )
    )

    items.append(yes_no_item(112, "STOCKOUT", "112. In past 3 months, has facility experienced a stock-out of tracer medicines?"))
    items.append(alpha("Q113_STOCKOUT_MEDS_TXT", "113. Specific medicines stocked out", length=400))
    items.append(
        select_one(
            114,
            "STOCKOUT_DURATION",
            "114. How long did the stock-out last?",
            ["Less than 30 days", "31-60 days", "More than 60 days"],
        )
    )
    items.append(
        select_one(
            115,
            "STOCKOUT_AVG",
            "115. On average, how many months do stock-outs last?",
            [
                "Less than a month",
                "1-2 months",
                "3-4 months",
                "5-6 months",
                "More than 6 months",
            ],
        )
    )
    items.append(
        select_one(
            116,
            "ADDR_STOCKOUT",
            "116. Did you do anything to address GAMOT stock-outs?",
            ["Yes", "No", "Did not experience stock-outs of GAMOT medicines"],
        )
    )
    items.extend(
        select_all(
            117,
            "ADDR_STOCKOUT_HOW",
            "117. How did you address GAMOT stock-outs?",
            [
                "Resorted to alternative procurement",
                "Active inventory monitoring",
                "Improve forecasting and quantification",
                "Other (specify)",
            ],
        )
    )

    return {
        "name": "E_BUCAS_GAMOT",
        "labels": _label("E. Awareness on Expanded Health Programs (BUCAS and GAMOT)"),
        "recordType": "6",
        "occurrences": {"required": True, "maximum": 1},
        "items": items,
    }


def build_section_f() -> dict:
    items: list[dict] = []
    items.append(
        select_one(
            118,
            "DOH_LICENSED",
            "118. Is this facility DOH licensed?",
            [
                "Yes",
                "No",
                "No, but submitted requirements and waiting for license",
                "I don't know what DOH licensing is",
            ],
        )
    )
    items.append(
        select_one(
            119,
            "DOH_LIC_RECEIVED",
            "119. When did you receive your DOH license (most recent application)?",
            [
                "Within the last 1 to 3 months",
                "Within the last 4 to 6 months",
                "Over 6 months but within 1 year",
                "More than 1 year ago",
                "I don't know",
            ],
        )
    )
    items.append(
        select_one(
            120,
            "DOH_LIC_DAYS",
            "120. How many days did it take to receive the license?",
            ["Less than 30 days", "31-60 days", "More than 60 days"],
        )
    )
    licensing_reqs = [
        "Patient rights and organization ethics",
        "Patient care",
        "Leadership and management",
        "Human resource management",
        "Information management",
        "Safe practice and environment",
        "Improving performance",
        "Physical plant",
        "Equipment and instruments",
        "National laws and DOH issuances (hospitals only)",
        "Emergency cart contents (hospitals only)",
        "Add-on services (hospitals only)",
        "Public access to price information (primary care only)",
        "None of the above",
    ]
    items.extend(
        select_all(
            121,
            "DOH_LIC_DIFFICULT",
            "121. Which DOH licensing requirements were difficult to comply with?",
            licensing_reqs,
        )
    )

    licensing_areas = [
        (122, "Patient rights and organization ethics"),
        (123, "Patient care"),
        (124, "Leadership and management"),
        (125, "Human resource management"),
        (126, "Information management"),
        (127, "Safe practice and environment"),
        (128, "Improving performance"),
        (129, "Physical plant"),
        (130, "Public access to price information"),
        (131, "Equipment and instruments"),
        (132, "National laws and DOH issuances (hospitals)"),
        (133, "Emergency cart contents (hospitals)"),
        (134, "Add-on services (hospitals)"),
    ]
    for qnum, area in licensing_areas:
        items.extend(
            select_all(
                qnum,
                f"WHY_LIC_{qnum}",
                f"{qnum}. Why difficult to comply with: {area}",
                DIFFICULTY_REASONS_LICENSING,
            )
        )

    return {
        "name": "F_DOH_LICENSING",
        "labels": _label("F. DOH Licensing: Status and Barriers to Licensing"),
        "recordType": "7",
        "occurrences": {"required": True, "maximum": 1},
        "items": items,
    }


def build_section_g() -> dict:
    items: list[dict] = []

    items.append(yes_no_item(135, "NBB_CURR", "135. Do you currently implement the NBB policy?"))
    items.append(yes_no_item(136, "NBB_ALL_PATIENTS", "136. Are you able to implement NBB for all patients (last 6 months)?"))
    nbb_barriers = [
        "Complying with no fees for basic/ward accommodation",
        "Complying with prescribed allocation ratio",
        "Patients do not avail of the process",
        "Insufficient PhilHealth support value",
        "Insufficient other sources (MAIFIP, DSWD, PCSO)",
        "PhilHealth delayed payment",
        "None of the above",
        "Other (specify)",
    ]
    items.extend(select_all(137, "NBB_BARRIERS", "137. Barriers to implementing NBB", nbb_barriers))

    items.append(yes_no_item(138, "ZBB_CURR", "138. Do you currently implement the ZBB policy?"))
    items.append(yes_no_item(139, "ZBB_ALL_PATIENTS", "139. Are you able to implement ZBB for all patients (last 6 months)?"))
    items.extend(select_all(140, "ZBB_BARRIERS", "140. Barriers to implementing ZBB", nbb_barriers))

    items.append(yes_no_item(141, "ALLOW_OOP_BASIC", "141. Does the facility allow OOP for basic accommodation?"))
    items.append(alpha("Q142_OOP_REASON_TXT", "142. Why does facility allow OOP for basic accommodation?", length=400))
    items.extend(
        select_all(
            143,
            "UHC_HARD_BENEFIT",
            "143. Which UHC benefits are most difficult to implement?",
            [
                "PhilHealth/financial protection benefits",
                "Establishment of HCPNs (referral system)",
                "Human resources for health reforms",
                "Other (specify)",
            ],
        )
    )
    items.extend(
        select_all(
            144,
            "WHY_HARD",
            "144. Why is this difficult to implement?",
            [
                "Implementation heavily reliant on LGU decisions",
                "Not enough funding/budget",
                "Technical/system issues of PhilHealth",
                "Other (specify)",
            ],
        )
    )
    items.append(yes_no_item(145, "MALASAKIT_PROVIDED", "145. Has facility provided medical social welfare/MAIFIP/Malasakit assistance?"))
    items.extend(
        select_all(
            146,
            "WHY_MALASAKIT_YES",
            "146. Why provide Malasakit/MAIFIP assistance?",
            [
                "Streamline access to medical and financial aid",
                "Reduce out-of-pocket expenses",
                "Eliminate need to travel to multiple agencies",
                "Foster compassionate approach to healthcare",
                "Other (specify)",
            ],
        )
    )
    items.extend(
        select_all(
            147,
            "WHY_MALASAKIT_NO",
            "147. Why NOT providing Malasakit/MAIFIP assistance?",
            [
                "Limited budget",
                "Stringent eligibility requirements",
                "Incomplete documentation from patients",
                "High patient volume / service bottlenecks",
                "Other (specify)",
            ],
        )
    )

    items.append(yes_no_item(148, "LGU_SUPPORT", "148. Do you receive any support from LGU to implement UHC reforms?"))
    items.extend(
        select_all(
            149,
            "LGU_SUPPORT_TYPES",
            "149. Forms of LGU support received",
            [
                "Financial assistance",
                "Technical assistance",
                "Medical supplies and equipment",
                "Manpower support",
                "Other (specify)",
            ],
        )
    )
    items.append(yes_no_item(150, "LGU_SATISFIED", "150. Are you satisfied with LGU support?"))
    items.extend(
        select_all(
            151,
            "LGU_NOT_SAT_REASON",
            "151. Why not satisfied with LGU support?",
            [
                "Insufficient",
                "Hard to coordinate",
                "Support not aligned with facility needs",
                "I don't know",
                "Other (specify)",
            ],
        )
    )
    items.append(
        select_one(
            152,
            "PHO_PROTOCOL_CLARITY",
            "152. How clear are protocols for PHO approval vs facility-level decisions?",
            ["Very Clear", "Clear", "Neither", "Unclear", "Very Unclear"],
        )
    )
    items.append(alpha("Q153_UNCLEAR_PROTOCOL_TXT", "153. Which protocol is unclear?", length=400))

    items.append(numeric("Q154_NUM_REFERRED_OUT", "154. # patients referred to higher-level facility (past 6 months)", length=8))
    items.extend(
        select_all(
            155,
            "REF_OUT_METHOD",
            "155. Common ways to send referrals to higher-level facilities",
            [
                "Physical referral slip",
                "E-referral",
                "Referring facility calls receiving facility",
                "Other (specify)",
            ],
        )
    )
    items.extend(
        select_all(
            156,
            "REF_FORM_TYPE",
            "156. Type of referral form used",
            [
                "DOH standard referral form",
                "Facility's standard referral form",
                "Province's standard referral form",
                "City / LGU standard referral form",
                "No standard referral form",
                "Other (specify)",
            ],
        )
    )
    items.append(
        select_one(
            157,
            "SPECIALIST_NETWORK",
            "157. Do you have a network of specialist providers to refer to?",
            ["Yes", "No", "I've never heard of it", "I don't know"],
        )
    )
    items.append(
        select_one(
            158,
            "REF_VS_WALKIN",
            "158. Proportion of referred patients vs walk-in (past 6 months)",
            [
                "Almost all referred, very few walk-in",
                "Majority referred, some walk-in",
                "About equal",
                "Majority walk-in, some referred",
                "Almost all walk-in, very few referred",
                "Unsure of typical ratio",
            ],
        )
    )
    items.extend(
        select_all(
            159,
            "REF_IN_METHOD",
            "159. Common ways to receive referrals from lower-level facilities",
            [
                "Physical referral slip",
                "E-referral",
                "Referring facility calls receiving facility",
                "Other (specify)",
            ],
        )
    )
    items.extend(
        select_all(
            160,
            "EXTERNAL_SVC",
            "160. Where do patients go for unavailable services?",
            [
                "External laboratory",
                "Other private facility",
                "Other public facility",
                "I don't know",
                "Other (specify)",
            ],
        )
    )
    items.append(
        select_one(
            161,
            "REF_SATISFACTION",
            "161. Satisfaction with current referral system",
            [
                "Very Satisfied",
                "Satisfied",
                "Neither Satisfied nor Dissatisfied",
                "Dissatisfied",
                "Very Dissatisfied",
            ],
        )
    )
    items.extend(
        select_all(
            162,
            "REF_NOT_SAT_REASON",
            "162. Why not satisfied with referral system?",
            [
                "Facilities overcrowded / do not accept referrals",
                "Referral process is slow",
                "Poor coordination between facilities",
                "Other (specify)",
            ],
        )
    )

    return {
        "name": "G_SERVICE_DELIVERY",
        "labels": _label("G. Service Delivery Process"),
        "recordType": "8",
        "occurrences": {"required": True, "maximum": 1},
        "items": items,
    }


def build_section_h() -> dict:
    items: list[dict] = []
    items.extend(
        select_all(
            163,
            "HR_CHALL",
            "163. Human resources challenges",
            [
                "Understaffing",
                "Skills mismatch / lack of skills",
                "Retention / high staff turnover",
                "I don't know",
                "Other (specify)",
            ],
        )
    )
    items.append(alpha("Q164_IMPROVE_AREA_TXT", "164. Area with most room for staff improvement", length=400))
    pd_options = [
        "Clinical audits",
        "Surgical audits",
        "Quality assurance meetings",
        "Seminars, conferences, workshops",
        "Independent professional development: scholarships",
        "Independent professional development: research grants",
        "LGU/DOH led workshops/initiatives",
        "No forms of professional development provided",
        "Other (specify)",
    ]
    items.extend(select_all(165, "PD_DOCTORS", "165. Professional development for doctors", pd_options))
    items.extend(select_all(166, "PD_NURSES", "166. Professional development for nurses", pd_options))
    return {
        "name": "H_HUMAN_RESOURCES",
        "labels": _label("H. Human Resources for Health"),
        "recordType": "9",
        "occurrences": {"required": True, "maximum": 1},
        "items": items,
    }


# ---------------------------------------------------------------------------
# Top-level dictionary
# ---------------------------------------------------------------------------


def build_dictionary() -> dict:
    return {
        "software": "CSPro",
        "version": 8.0,
        "fileType": "dictionary",
        "name": "FACILITYHEADSURVEY_DICT",
        "labels": _label("Facility Head Survey (F1) - UHC Year 2"),
        "readOptimization": True,
        "recordType": {"start": 1, "length": 1},
        "defaults": {"decimalMark": True, "zeroFill": False},
        "relativePositions": True,
        "levels": [
            {
                "name": "FACILITYHEADSURVEY_LEVEL",
                "labels": _label("Facility Head Survey Level"),
                "ids": {
                    "items": [
                        {
                            "name": "FACILITYHEADSURVEY_ID",
                            "labels": _label("Facility Head Survey Identification"),
                            "contentType": "numeric",
                            "start": 2,
                            "length": 6,
                            "zeroFill": True,
                        }
                    ]
                },
                "records": [
                    build_field_control(),
                    build_geographic_id(),
                    build_section_a(),
                    build_section_b(),
                    build_section_c(),
                    build_section_d(),
                    build_section_e(),
                    build_section_f(),
                    build_section_g(),
                    build_section_h(),
                ],
            }
        ],
    }


def main() -> None:
    out_path = Path(__file__).parent / "FacilityHeadSurvey.dcf"
    dct = build_dictionary()
    out_path.write_text(json.dumps(dct, indent=2), encoding="utf-8")
    # Quick stats
    records = dct["levels"][0]["records"]
    item_count = sum(len(r["items"]) for r in records)
    print(f"Wrote {out_path}")
    print(f"Records: {len(records)}, total items: {item_count}")
    for r in records:
        print(f"  - {r['name']:40s} type={r['recordType']:2s} items={len(r['items'])}")


if __name__ == "__main__":
    main()
