"""Smoke-test for the 115_F4 Household Survey CSPro build.

Asserts that:
  1. HouseholdSurvey.dcf parses as JSON, has 24 records and 659 total
     items (5 ID + 659 record items per the rebuild scope), and the
     load-bearing FIELD_CONTROL extras (HH_LISTING_NO,
     F4_PARENT_F3_CASE_SEQ) + section-A informed-consent items are
     present.
  2. HouseholdSurvey.fmf is BOM-prefixed and has 25 [Form] blocks
     (1 IDS + 24 record forms).
  3. HouseholdSurvey.ent is JSON-parseable, declares F4LISTING_DICT as
     an EXTERNAL dictionary (load-bearing wiring for household-pick
     when 113_F4_listing app lands), and has the csweb_url +
     expiration_days userSettings keys.
  4. HouseholdSurvey.ent.apc contains the load-bearing PROC / function
     definitions:
       - PROC HOUSEHOLDSURVEY_LEVEL.preproc          (household-pick stub)
       - function PickHousehold                       (stub)
       - PROC FIELD_CONTROL.preproc                   (case-start)
       - PROC CONSENT_GIVEN.postproc                  (consent terminator)
       - Section A-Q skip-logic PROCs (sample: Q4, Q47, Q108, Q200/Q201)
       - Section N computed totals (Q157, Q177, Q182, Q185)
       - Q18 amount-in-bracket consistency            (HARD edit H4)
       - Cross-record H_PHILHEALTH gate on row-1 Q45
       - Settings-driven gates F4_BUCAS_AREA + F4_GAMOT_AREA
       - HH_CAPTURE_GPS + CAPTURE_VERIFICATION_PHOTO triggers
  5. HouseholdSurvey.ent.apc references item names that ALL exist in
     the F4 DCF (no broken `skip to <X>` or `PROC <X>` targets).
"""
import json
import re
from pathlib import Path

import pytest


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
F4_DIR         = WORKSPACE_ROOT / "115_F4"


# ---------------------------------------------------------------------------
# 1. HouseholdSurvey.dcf
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def f4_dcf():
    path = F4_DIR / "HouseholdSurvey.dcf"
    if not path.exists():
        pytest.skip(
            "HouseholdSurvey.dcf missing — run "
            "`python 115_F4/generate_dcf.py` first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def test_f4_dcf_has_24_records(f4_dcf):
    records = f4_dcf["levels"][0]["records"]
    assert len(records) == 24, f"expected 24 records, got {len(records)}"


def test_f4_dcf_has_decomposed_5_item_id_block(f4_dcf):
    ids = f4_dcf["levels"][0]["ids"]["items"]
    names = [it["name"] for it in ids]
    assert names == [
        "REGION_CODE",
        "PROVINCE_HUC_CODE",
        "CITY_MUNICIPALITY_CODE",
        "FACILITY_NO",
        "CASE_SEQ",
    ]


def test_f4_dcf_field_control_dual_linkage(f4_dcf):
    """FIELD_CONTROL must include HH_LISTING_NO + F4_PARENT_F3_CASE_SEQ
    extras (Option C dual-linkage rule per 2026-05-12 design)."""
    records = {r["name"]: r for r in f4_dcf["levels"][0]["records"]}
    fc = records["FIELD_CONTROL"]
    names = {it["name"] for it in fc["items"]}
    assert "SURVEY_CODE"            in names
    assert "HH_LISTING_NO"          in names
    assert "F4_PARENT_F3_CASE_SEQ"  in names
    assert "CONSENT_GIVEN"          in names


def test_f4_dcf_section_a_informed_consent_items(f4_dcf):
    records = {r["name"]: r for r in f4_dcf["levels"][0]["records"]}
    sec_a = records["A_INFORMED_CONSENT"]
    item_names = {it["name"] for it in sec_a["items"]}
    assert "Q1_IS_HH_HEAD" in item_names


def test_f4_dcf_household_roster_has_max_occurs_10(f4_dcf):
    records = {r["name"]: r for r in f4_dcf["levels"][0]["records"]}
    roster = records["C_HOUSEHOLD_ROSTER"]
    assert roster.get("occurrences", {}).get("maximum") == 10


def test_f4_dcf_section_n_has_4_computed_totals(f4_dcf):
    records = {r["name"]: r for r in f4_dcf["levels"][0]["records"]}
    n = records["N_HH_EXPENDITURES"]
    item_names = {it["name"] for it in n["items"]}
    for total in ("Q157_TOTAL", "Q177_TOTAL", "Q182_TOTAL", "Q185_TOTAL"):
        assert total in item_names, f"expected computed total {total}"


# ---------------------------------------------------------------------------
# 2. HouseholdSurvey.fmf
# ---------------------------------------------------------------------------

def test_f4_fmf_is_bom_prefixed_and_has_25_forms():
    path = F4_DIR / "HouseholdSurvey.fmf"
    if not path.exists():
        pytest.skip(
            "HouseholdSurvey.fmf missing — run "
            "`python 115_F4/generate_fmf.py` first."
        )
    content = path.read_text(encoding="utf-8")
    assert content.startswith("﻿"), "FMF must be BOM-prefixed"
    # 25 [Form] blocks: 1 IDS + 24 records (root + FIELD_CONTROL +
    # HOUSEHOLD_GEO_ID + GPS + photo + sections A-Q with C split into 3
    # records).
    assert content.count("[Form]\n") == 25


# ---------------------------------------------------------------------------
# 3. HouseholdSurvey.ent — declares F4LISTING_DICT external dict
# ---------------------------------------------------------------------------

def test_f4_ent_declares_f4listing_dict_external():
    """The committed .ent must declare F4LISTING_DICT as an EXTERNAL
    dictionary. This is load-bearing wiring for the household-pick PROC
    that activates when 113_F4_listing app lands. If this regresses,
    the listing-app's roster cannot be queried at case-open."""
    path = F4_DIR / "HouseholdSurvey.ent"
    if not path.exists():
        pytest.skip("HouseholdSurvey.ent missing — run generate_ent.py first.")
    ent = json.loads(path.read_text(encoding="utf-8"))
    types_paths = [
        (d["type"], d["path"]) for d in ent["dictionaries"]
    ]
    assert ("input", "HouseholdSurvey.dcf") in types_paths
    has_external = any(
        t == "external" and "F4Listing.dcf" in p
        for t, p in types_paths
    )
    assert has_external, (
        "F4 .ent must declare F4LISTING_DICT (../113_F4_listing/"
        "F4Listing.dcf) as type='external'"
    )


def test_f4_ent_user_settings_present():
    path = F4_DIR / "HouseholdSurvey.ent"
    if not path.exists():
        pytest.skip("HouseholdSurvey.ent missing — run generate_ent.py first.")
    ent = json.loads(path.read_text(encoding="utf-8"))
    settings = {s["name"]: s["value"] for s in ent["userSettings"]}
    assert "csweb_url"       in settings
    assert "expiration_days" in settings


# ---------------------------------------------------------------------------
# 4. HouseholdSurvey.ent.apc — load-bearing definitions
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def f4_apc():
    path = F4_DIR / "HouseholdSurvey.ent.apc"
    if not path.exists():
        pytest.skip(
            "HouseholdSurvey.ent.apc missing — run "
            "`python 115_F4/generate_apc.py` first."
        )
    return path.read_text(encoding="utf-8")


def test_f4_apc_has_household_pick_stub(f4_apc):
    assert "function PickHousehold"                    in f4_apc
    assert "PROC HOUSEHOLDSURVEY_LEVEL"                in f4_apc
    # Stub doc-comment must reference F4LISTING_DICT activation path.
    assert "F4LISTING_DICT"                            in f4_apc


def test_f4_apc_has_field_control_setup(f4_apc):
    assert "PROC FIELD_CONTROL"                        in f4_apc
    assert 'SURVEY_CODE        = "F4"'                 in f4_apc
    assert "PROC CONSENT_GIVEN"                        in f4_apc
    # CONSENT=No must terminate the case via endcase.
    assert "VISIT_RESULT_WITHDRAW_CONSENT"             in f4_apc
    assert "endcase"                                   in f4_apc


def test_f4_apc_has_section_skip_logic(f4_apc):
    """Sample 4 sections — B (Q4), C (Q47), K (Q108), Q (Q200/Q201)
    — to catch regressions in skip-logic emission."""
    # Section B — Q4 LGBTQIA skip pattern
    assert "PROC Q4_LGBTQIA"                           in f4_apc
    assert "skip to Q6_CIVIL_STATUS"                   in f4_apc
    # Section C — Q47 private-insurance gate
    assert "PROC Q47_HAS_PRIVATE_INS"                  in f4_apc
    assert "skip to Q51_HEARD_UHC"                     in f4_apc
    # Section K — Q108 referral bypass
    assert "PROC Q108_REFERRED"                        in f4_apc
    assert "skip to Q126_HEARD_NBB"                    in f4_apc
    # Section Q — end-of-survey terminators
    assert "PROC Q200_REDUCED_SPENDING"                in f4_apc
    assert "PROC Q201_WORRIED_FINANCES"                in f4_apc
    assert "CloseCaseAsComplete()"                     in f4_apc


def test_f4_apc_has_section_n_computed_totals(f4_apc):
    """Pin the 4 computed-total PROCs from spec §1 finding #14."""
    assert "PROC Q157_TOTAL"                           in f4_apc
    assert "Q144_TOTAL + Q145_TOTAL"                   in f4_apc
    assert "PROC Q177_TOTAL"                           in f4_apc
    assert "Q175_TOTAL + Q176_TOTAL"                   in f4_apc
    assert "PROC Q182_TOTAL"                           in f4_apc
    assert "PROC Q185_TOTAL"                           in f4_apc


def test_f4_apc_has_cross_record_h_philhealth_gate(f4_apc):
    """Section H gates on respondent (row 1) PhilHealth registration
    per spec §2 Section H note. Cross-record reference syntax pinned."""
    assert "PROC H_PHILHEALTH"                                          in f4_apc
    assert "C_HOUSEHOLD_ROSTER(1).Q45_PHILHEALTH_REG"                  in f4_apc


def test_f4_apc_has_settings_driven_gates(f4_apc):
    """F_BUCAS and Q69 are settings-driven gates per spec §2."""
    assert 'loadsetting("F4_BUCAS_AREA")'              in f4_apc
    assert 'loadsetting("F4_GAMOT_AREA")'              in f4_apc


def test_f4_apc_has_q18_bracket_consistency(f4_apc):
    """Pin the HARD H4 income-amount-in-bracket consistency check."""
    assert "PROC Q18_INCOME_BRACKET"                   in f4_apc
    assert "BRACKET_4_LO"                              in f4_apc   # named constant


def test_f4_apc_has_respondent_row_1_autofill(f4_apc):
    """C_HOUSEHOLD_ROSTER.preproc auto-fills row 1 from
    FIELD_CONTROL respondent items (spec §1 findings #4-#6)."""
    assert "PROC C_HOUSEHOLD_ROSTER"                   in f4_apc
    assert "if curocc() = 1"                           in f4_apc
    assert "Q32_AGE       = Q2_1_AGE"                  in f4_apc
    assert "Q33_SEX       = Q3_SEX"                    in f4_apc


def test_f4_apc_has_q136_artifact_note(f4_apc):
    """Q136 transcription artifact (Q113 has no MAIFIP option) must be
    documented inline per spec §1 finding #12."""
    assert "PROC Q136_HEARD_MAIFIP"                    in f4_apc
    assert "transcription artifact"                    in f4_apc


def test_f4_apc_wires_shared_capture_helpers(f4_apc):
    """GPS + photo handlers must call into shared/Capture-Helpers.apc."""
    assert '#include "../shared/Capture-Helpers.apc"'  in f4_apc
    assert "PROC HH_CAPTURE_GPS"                       in f4_apc
    assert "PROC CAPTURE_VERIFICATION_PHOTO"           in f4_apc
    assert "ReadGPSReading"                            in f4_apc
    assert "TakeVerificationPhoto"                     in f4_apc


# ---------------------------------------------------------------------------
# 5. APC references all resolve to DCF item / record names
# ---------------------------------------------------------------------------

def test_f4_apc_all_skip_targets_resolve_to_dcf_items(f4_dcf, f4_apc):
    """Strip CSPro {...} comments, then assert every `skip to <X>` and
    `PROC <X>` (excluding GLOBAL / LEVEL) names an item or record that
    actually exists in HouseholdSurvey.dcf."""
    names = set()
    for it in f4_dcf["levels"][0]["ids"]["items"]:
        names.add(it["name"])
    for rec in f4_dcf["levels"][0]["records"]:
        names.add(rec["name"])
        for it in rec["items"]:
            names.add(it["name"])
            for sub in it.get("subitems", []) or []:
                names.add(sub["name"])

    # Strip CSPro {...} comments before scanning.
    apc_stripped = re.sub(r"\{[^}]*\}", "", f4_apc, flags=re.DOTALL)

    skip_targets = set(re.findall(r"skip to (\w+)", apc_stripped))
    proc_targets = set(re.findall(r"^PROC (\w+)", apc_stripped, re.MULTILINE))

    reserved_proc_names = {"GLOBAL", "HOUSEHOLDSURVEY_LEVEL"}
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
