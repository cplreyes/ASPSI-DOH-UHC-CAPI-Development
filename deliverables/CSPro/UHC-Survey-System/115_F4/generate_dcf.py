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
    """A. Introduction and Informed Consent. Items land in a later commit."""
    return record("A_INFORMED_CONSENT",
                  "A. Introduction and Informed Consent", "C", [])


def build_section_b():
    """B. Respondent Profile. Items land in a later commit."""
    return record("B_RESPONDENT_PROFILE",
                  "B. Respondent Profile", "D", [])


def build_section_c():
    """C. Household Roster and Characteristics (C1-C5, Q30-Q46).

    Per-household-member occurring record, max_occurs=10 (matching the
    PDF's 10-row roster table). Q47 (HH-level private-insurance gate)
    and Q48-Q50 (private-insurance sub-roster) live in separate records.
    """
    return record("C_HOUSEHOLD_ROSTER",
                  "C. Household Roster and Characteristics", "E",
                  [], max_occurs=10, required=False)


def build_section_c_private_insurance_gate():
    """Q47 HH-level private-insurance gate. Non-repeating."""
    return record("C_PRIVATE_INSURANCE_GATE",
                  "C. Private Insurance Coverage (HH-level gate, Q47)", "T",
                  [])


def build_section_c_private_insurance_roster():
    """Q48-Q50 private-insurance sub-roster. Per-member, max_occurs=10."""
    return record("C_PRIVATE_INSURANCE_ROSTER",
                  "C. Private Insurance Coverage Roster (Q48-Q50)", "U",
                  [], max_occurs=10, required=False)


def build_section_d():
    """D. Awareness on Universal Health Care (UHC)."""
    return record("D_UHC_AWARENESS",
                  "D. Awareness on Universal Health Care (UHC)", "F", [])


def build_section_e():
    """E. YAKAP/Konsulta Awareness."""
    return record("E_YAKAP_KONSULTA",
                  "E. YAKAP/Konsulta Awareness", "G", [])


def build_section_f():
    """F. BUCAS Awareness and Utilization."""
    return record("F_BUCAS",
                  "F. Bagong Urgent Care and Ambulatory Service (BUCAS) "
                  "Awareness and Utilization", "H", [])


def build_section_g():
    """G. Access to Medicines."""
    return record("G_ACCESS_TO_MEDICINES",
                  "G. Access to Medicines", "I", [])


def build_section_h():
    """H. PhilHealth Registration and Health Insurance."""
    return record("H_PHILHEALTH",
                  "H. PhilHealth Registration and Health Insurance", "J", [])


def build_section_i():
    """I. Primary Care Utilization."""
    return record("I_PRIMARY_CARE",
                  "I. Primary Care Utilization", "K", [])


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
