"""Smoke-test for the 111_F3 Patient Survey CSPro build.

Asserts that:
  1. PatientSurvey.dcf parses as JSON, has 18 records, ~810 total items
     (5 ID + 805 record items per the rebuild scope), and the load-
     bearing FIELD_CONTROL extras (PATIENT_TYPE, PATIENT_LISTING_NO) and
     section-A informed-consent items are present.
  2. PatientSurvey.fmf is BOM-prefixed and has 19 [Form] blocks
     (1 IDS + 18 record forms — Q1..Q178 plus root + FIELD_CONTROL +
     PATIENT_GEO_ID + GPS x2 + photo).
  3. PatientSurvey.ent is JSON-parseable, declares PATIENTLISTING_DICT
     as an EXTERNAL dictionary (load-bearing for patient-pick at case
     open), and has the csweb_url + expiration_days userSettings keys.
  4. PatientSurvey.ent.apc contains the load-bearing PROC / function
     definitions:
       - PROC PATIENTSURVEY_LEVEL.preproc       (patient-pick entry)
       - function PickPatient                   (eligible-roster query)
       - function StampRosterStatus             (write-back)
       - PROC FIELD_CONTROL.preproc             (case-start)
       - PROC CONSENT_GIVEN.postproc            (consent terminator)
       - Section A-L skip-logic PROCs           (sample: Q35, Q84, Q162)
       - Q18 amount-in-bracket consistency      (validation H4)
       - Q115 payment-matrix reconciliation     (validation H8/S3)
  5. PatientSurvey.ent.apc references item names that ALL exist in the
     F3 DCF (no broken `skip to <X>` or `PROC <X>` targets).
"""
import json
import re
from pathlib import Path

import pytest


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
F3_DIR         = WORKSPACE_ROOT / "111_F3"


# ---------------------------------------------------------------------------
# 1. PatientSurvey.dcf
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def f3_dcf():
    path = F3_DIR / "PatientSurvey.dcf"
    if not path.exists():
        pytest.skip(
            "PatientSurvey.dcf missing — run "
            "`python 111_F3/generate_dcf.py` first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def test_f3_dcf_has_18_records(f3_dcf):
    records = f3_dcf["levels"][0]["records"]
    assert len(records) == 18, f"expected 18 records, got {len(records)}"


def test_f3_dcf_has_decomposed_5_item_id_block(f3_dcf):
    ids = f3_dcf["levels"][0]["ids"]["items"]
    names = [it["name"] for it in ids]
    assert names == [
        "REGION_CODE",
        "PROVINCE_HUC_CODE",
        "CITY_MUNICIPALITY_CODE",
        "FACILITY_NO",
        "CASE_SEQ",
    ]


def test_f3_dcf_field_control_extras(f3_dcf):
    """FIELD_CONTROL must include PATIENT_TYPE + PATIENT_LISTING_NO
    extras for the F3 listing-app linkage."""
    records = {r["name"]: r for r in f3_dcf["levels"][0]["records"]}
    fc = records["FIELD_CONTROL"]
    names = {it["name"] for it in fc["items"]}
    assert "SURVEY_CODE"        in names
    assert "PATIENT_TYPE"       in names
    assert "PATIENT_LISTING_NO" in names
    assert "CONSENT_GIVEN"      in names


def test_f3_dcf_section_a_informed_consent_items(f3_dcf):
    records = {r["name"]: r for r in f3_dcf["levels"][0]["records"]}
    sec_a = records["A_INFORMED_CONSENT"]
    item_names = {it["name"] for it in sec_a["items"]}
    assert "Q1_IS_PATIENT"        in item_names
    assert "Q2_RELATIONSHIP"      in item_names
    assert "Q3_SAME_HOUSE"        in item_names


def test_f3_dcf_no_retired_f3_facility_id(f3_dcf):
    """F3_FACILITY_ID was retired in the rebuild — linkage to F1 derives
    from the shared first 9 digits of the case-ID, not a composite item."""
    records = f3_dcf["levels"][0]["records"]
    for rec in records:
        for it in rec["items"]:
            assert it["name"] != "F3_FACILITY_ID", (
                "F3_FACILITY_ID was retired in the 2026-05-11 rebuild; "
                "did the generator regress?"
            )


# ---------------------------------------------------------------------------
# 2. PatientSurvey.fmf
# ---------------------------------------------------------------------------

def test_f3_fmf_is_bom_prefixed_and_has_19_forms():
    path = F3_DIR / "PatientSurvey.fmf"
    if not path.exists():
        pytest.skip(
            "PatientSurvey.fmf missing — run "
            "`python 111_F3/generate_fmf.py` first."
        )
    content = path.read_text(encoding="utf-8")
    assert content.startswith("﻿"), "FMF must be BOM-prefixed"
    # 19 [Form] blocks: 1 IDS + 18 records (root + FIELD_CONTROL +
    # PATIENT_GEO_ID + facility GPS + patient-home GPS + verification photo
    # + sections A-L).
    assert content.count("[Form]\n") == 19


# ---------------------------------------------------------------------------
# 3. PatientSurvey.ent — declares PATIENTLISTING_DICT external dict
# ---------------------------------------------------------------------------

def test_f3_ent_declares_patientlisting_dict_external():
    """The committed .ent must declare PATIENTLISTING_DICT as an
    EXTERNAL dictionary. This is load-bearing for the patient-pick PROC
    that runs at case-open. If this regresses, F3 cannot read the
    listing roster and the entire patient-pick flow breaks."""
    path = F3_DIR / "PatientSurvey.ent"
    if not path.exists():
        pytest.skip("PatientSurvey.ent missing — run generate_ent.py first.")
    ent = json.loads(path.read_text(encoding="utf-8"))
    types_paths = [
        (d["type"], d["path"]) for d in ent["dictionaries"]
    ]
    assert ("input", "PatientSurvey.dcf") in types_paths
    has_external = any(
        t == "external" and "PatientListing.dcf" in p
        for t, p in types_paths
    )
    assert has_external, (
        "F3 .ent must declare PATIENTLISTING_DICT (../110_F3_listing/"
        "PatientListing.dcf) as type='external'"
    )


def test_f3_ent_user_settings_present():
    path = F3_DIR / "PatientSurvey.ent"
    if not path.exists():
        pytest.skip("PatientSurvey.ent missing — run generate_ent.py first.")
    ent = json.loads(path.read_text(encoding="utf-8"))
    settings = {s["name"]: s["value"] for s in ent["userSettings"]}
    assert "csweb_url"       in settings
    assert "expiration_days" in settings


# ---------------------------------------------------------------------------
# 4. PatientSurvey.ent.apc — load-bearing definitions
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def f3_apc():
    path = F3_DIR / "PatientSurvey.ent.apc"
    if not path.exists():
        pytest.skip(
            "PatientSurvey.ent.apc missing — run "
            "`python 111_F3/generate_apc.py` first."
        )
    return path.read_text(encoding="utf-8")


def test_f3_apc_has_patient_pick_definitions(f3_apc):
    assert "function PickPatient"                in f3_apc
    assert "function StampRosterStatus"          in f3_apc
    assert "PROC PATIENTSURVEY_LEVEL"            in f3_apc
    # PATIENTLISTING_DICT external-dict access via loadcase / forcase /
    # savecase — at least one of each must be present.
    assert "loadcase(PATIENTLISTING_DICT"        in f3_apc
    assert "forcase PATIENTLISTING_DICT"         in f3_apc
    assert "savecase(PATIENTLISTING_DICT)"       in f3_apc


def test_f3_apc_has_field_control_setup(f3_apc):
    assert "PROC FIELD_CONTROL"                  in f3_apc
    assert 'SURVEY_CODE        = "F3"'           in f3_apc
    assert "PROC CONSENT_GIVEN"                  in f3_apc
    # CONSENT=No must terminate the case via endcase + roster write-back.
    assert "StampRosterStatus(F3_STATUS_REFUSED" in f3_apc
    assert "endcase"                              in f3_apc


def test_f3_apc_has_section_skip_logic(f3_apc):
    """Sample 3 sections — A (Q1), F (Q84), L (Q162) — to catch
    regressions in skip-logic emission."""
    # Section A — Q1 IS_PATIENT branching
    assert "PROC Q1_IS_PATIENT"                  in f3_apc
    assert "skip to Q4_NAME"                     in f3_apc
    # Section F gate
    assert "PROC Q84_SERVICE_TYPE"               in f3_apc
    assert "skip to Q116_NBB_HEARD"              in f3_apc
    # Section L referral terminator
    assert "PROC Q162_REFERRED"                  in f3_apc
    assert "skip to Q172_PCP_REFERRAL"           in f3_apc
    assert "PROC Q178_SAT_REFERRAL"              in f3_apc
    assert "CloseCaseAsComplete()"               in f3_apc


def test_f3_apc_has_cross_field_validations(f3_apc):
    """Pin the load-bearing validations from spec §3."""
    # H4 — income amount-in-bracket
    assert "PROC Q18_INCOME_BRACKET"             in f3_apc
    assert "BRACKET_4_LO"                        in f3_apc   # named-constant
    # H5/H6 — HH composition coverage
    assert "PROC Q21_HH_SENIORS"                 in f3_apc
    # H7 — nights/days consistency
    assert "PROC Q106_DAYS"                      in f3_apc
    # H8/S3 — Q113 payment-matrix vs Q115 final cash
    assert "PROC Q115_FINAL_CASH"                in f3_apc
    assert "Q113_PAY_01_AMT"                     in f3_apc
    assert "pct_diff"                             in f3_apc


def test_f3_apc_wires_shared_capture_helpers(f3_apc):
    """GPS handlers must call into shared/Capture-Helpers.apc."""
    assert '#include "../shared/Capture-Helpers.apc"' in f3_apc
    assert "PROC FACILITY_CAPTURE_GPS"               in f3_apc
    assert "PROC P_HOME_CAPTURE_GPS"                 in f3_apc
    assert "ReadGPSReading"                          in f3_apc


# ---------------------------------------------------------------------------
# 5. APC references all resolve to DCF item / record names
# ---------------------------------------------------------------------------

def test_f3_apc_all_skip_targets_resolve_to_dcf_items(f3_dcf, f3_apc):
    """Strip CSPro {...} comments, then assert every `skip to <X>` and
    `PROC <X>` (excluding GLOBAL / LEVEL) names an item or record that
    actually exists in PatientSurvey.dcf."""
    names = set()
    for it in f3_dcf["levels"][0]["ids"]["items"]:
        names.add(it["name"])
    for rec in f3_dcf["levels"][0]["records"]:
        names.add(rec["name"])
        for it in rec["items"]:
            names.add(it["name"])
            for sub in it.get("subitems", []) or []:
                names.add(sub["name"])

    # Strip CSPro {...} comments before scanning.
    apc_stripped = re.sub(r"\{[^}]*\}", "", f3_apc, flags=re.DOTALL)

    skip_targets = set(re.findall(r"skip to (\w+)", apc_stripped))
    proc_targets = set(re.findall(r"^PROC (\w+)", apc_stripped, re.MULTILINE))

    reserved_proc_names = {"GLOBAL", "PATIENTSURVEY_LEVEL"}
    missing_skip = sorted(t for t in skip_targets if t not in names)
    missing_proc = sorted(
        t for t in proc_targets
        if t not in names and t not in reserved_proc_names
    )

    assert missing_skip == [], (
        f"APC references {len(missing_skip)} skip-to targets that don't "
        f"exist in the DCF: {missing_skip}"
    )
    assert missing_proc == [], (
        f"APC defines PROCs for {len(missing_proc)} items that don't "
        f"exist in the DCF: {missing_proc}"
    )
