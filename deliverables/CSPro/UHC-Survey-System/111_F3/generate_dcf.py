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
    """A. Introduction and Informed Consent (Q1-Q3)."""
    items = []
    return record("A_INFORMED_CONSENT",
                  "A. Introduction and Informed Consent", "C", items)


def build_section_b():
    """B. Patient Profile (Q4-Q34)."""
    items = []
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
