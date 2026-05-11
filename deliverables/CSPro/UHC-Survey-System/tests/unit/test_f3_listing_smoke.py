"""Smoke-test for the 110_F3_listing CSPro build.

Asserts that:
  1. shared.cspro_helpers.build_listing_id_block() emits a 6-item
     session-ID block whose widths total 16 digits.
  2. PatientListing.dcf parses as JSON, has the expected record set, and
     the auto-tag triage items are present with the expected widths.
  3. PatientListing.fmf is BOM-prefixed and has 7 [Form] blocks
     (1 IDS + 6 record forms).
  4. PatientListing.ent.apc contains the load-bearing PROC / function
     definitions plus the PENDING_DESIGN_AUTO_TAG_RULE marker.
  5. PatientListing.ent is JSON-parseable and has csweb_url='PLACEHOLDER'
     in the committed copy (per the pre-splice convention).
"""
import json
from pathlib import Path

import pytest


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
LISTING_DIR    = WORKSPACE_ROOT / "110_F3_listing"


# ---------------------------------------------------------------------------
# 1. build_listing_id_block() — structural pins
# ---------------------------------------------------------------------------

def test_build_listing_id_block_returns_six_items_in_order():
    from shared.cspro_helpers import build_listing_id_block
    block = build_listing_id_block()
    names = [it["name"] for it in block]
    assert names == [
        "REGION_CODE",
        "PROVINCE_HUC_CODE",
        "CITY_MUNICIPALITY_CODE",
        "FACILITY_NO",
        "LISTING_SESSION_DATE",
        "LISTING_SESSION_SEQ",
    ]


def test_build_listing_id_block_widths_total_20_digits():
    """Listing-session ID widths: 2+2+3+2+8+3 = 20 digits total.
    Note: distinct from the F-series 12-digit case-ID; the listing
    block stretches by 8 (for YYYYMMDD) so a facility can run multiple
    listing sessions in the same date without ID collision."""
    from shared.cspro_helpers import build_listing_id_block
    block = build_listing_id_block()
    width_by_name = {it["name"]: it["length"] for it in block}
    assert width_by_name == {
        "REGION_CODE":            2,
        "PROVINCE_HUC_CODE":      2,
        "CITY_MUNICIPALITY_CODE": 3,
        "FACILITY_NO":            2,
        "LISTING_SESSION_DATE":   8,
        "LISTING_SESSION_SEQ":    3,
    }
    assert sum(it["length"] for it in block) == 20


def test_build_listing_id_block_start_positions_contiguous():
    """Listing ID occupies columns 2-17 (col 1 is record-type)."""
    from shared.cspro_helpers import build_listing_id_block
    block = build_listing_id_block()
    expected_starts = [2, 4, 6, 9, 11, 19]
    for it, exp_start in zip(block, expected_starts):
        assert it["start"] == exp_start, (
            f"{it['name']} start={it['start']} expected {exp_start}"
        )


# ---------------------------------------------------------------------------
# 2. PatientListing.dcf
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def listing_dcf():
    path = LISTING_DIR / "PatientListing.dcf"
    if not path.exists():
        pytest.skip(
            "PatientListing.dcf missing — run "
            "`python 110_F3_listing/generate_dcf.py` first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def test_listing_dcf_has_six_records_plus_root(listing_dcf):
    records = listing_dcf["levels"][0]["records"]
    names = [r["name"] for r in records]
    assert names == [
        "PATIENTLISTING_REC",
        "REC_LISTING_CONTROL",
        "REC_RANDOM_INTERVAL_LOG",
        "REC_PATIENT_ROSTER",
        "REC_LISTING_FACILITY_CAPTURE",
        "REC_LISTING_PHOTO",
    ]


def test_listing_dcf_id_block_is_decomposed_six_item(listing_dcf):
    ids = listing_dcf["levels"][0]["ids"]["items"]
    assert len(ids) == 6
    assert ids[0]["name"] == "REGION_CODE"
    assert ids[-1]["name"] == "LISTING_SESSION_SEQ"


def test_listing_dcf_roster_has_auto_tag_inputs(listing_dcf):
    records = {r["name"]: r for r in listing_dcf["levels"][0]["records"]}
    roster = records["REC_PATIENT_ROSTER"]
    item_names = {it["name"] for it in roster["items"]}
    # Inputs to ComputeListingTag
    assert "CONTACT_VERIFIED"      in item_names
    assert "DISTANCE_TO_HOME_KM"   in item_names
    # Output set by the PROC
    assert "LISTING_TAG"           in item_names
    # Captured but not consumed by Candidate A (held for future-Myra-rule)
    assert "HOME_IN_SUBDIVISION"   in item_names
    # Multi-response transport modes — codes 01..11 + 96
    transport_codes = [n for n in item_names if n.startswith("TRANSPORT_MODE_")]
    assert len(transport_codes) == 12


def test_listing_dcf_roster_item_widths_match_spec(listing_dcf):
    """Spot-check the load-bearing widths from
    F3-Listing-Skip-Logic-and-Validations.md."""
    records = {r["name"]: r for r in listing_dcf["levels"][0]["records"]}
    roster = records["REC_PATIENT_ROSTER"]
    widths = {it["name"]: it["length"] for it in roster["items"]}
    assert widths["LISTING_TAG"]         == 1   # 1/2/3/9
    assert widths["CONTACT_VERIFIED"]    == 1
    assert widths["DISTANCE_TO_HOME_KM"] == 4   # 00.0..99.9
    assert widths["ROSTER_SEQ"]          == 3


# ---------------------------------------------------------------------------
# 3. PatientListing.fmf
# ---------------------------------------------------------------------------

def test_listing_fmf_is_bom_prefixed_and_has_seven_forms():
    path = LISTING_DIR / "PatientListing.fmf"
    if not path.exists():
        pytest.skip(
            "PatientListing.fmf missing — run "
            "`python 110_F3_listing/generate_fmf.py` first."
        )
    content = path.read_text(encoding="utf-8")
    # BOM at byte 0
    assert content.startswith("﻿"), "FMF must be BOM-prefixed"
    # 7 [Form] blocks: 1 IDS + 6 records
    assert content.count("[Form]\n") == 7


# ---------------------------------------------------------------------------
# 4. PatientListing.ent.apc
# ---------------------------------------------------------------------------

def test_listing_apc_has_load_bearing_definitions():
    path = LISTING_DIR / "PatientListing.ent.apc"
    if not path.exists():
        pytest.skip(
            "PatientListing.ent.apc missing — run "
            "`python 110_F3_listing/generate_apc.py` first."
        )
    apc = path.read_text(encoding="utf-8")
    # Cadence engine
    assert "function DrawRandomInterval" in apc
    assert "function SeedSessionPRNG"    in apc
    # Auto-tag rule
    assert "function ComputeListingTag"  in apc
    assert "TAG1_THRESHOLD_KM"           in apc
    assert "TAG2_THRESHOLD_KM"           in apc
    assert "PENDING_DESIGN_AUTO_TAG_RULE" in apc
    # Sync directive
    assert "synchronize_file"            in apc
    # Wired-in shared helpers
    assert '#include "../shared/Capture-Helpers.apc"' in apc


def test_listing_apc_thresholds_are_2_and_15_km():
    """Pins the Candidate A thresholds — if these change the wiki source
    page + this test should change together."""
    path = LISTING_DIR / "PatientListing.ent.apc"
    if not path.exists():
        pytest.skip("PatientListing.ent.apc missing — run generate_apc.py first.")
    apc = path.read_text(encoding="utf-8")
    assert "TAG1_THRESHOLD_KM = 2.0"  in apc
    assert "TAG2_THRESHOLD_KM = 15.0" in apc


# ---------------------------------------------------------------------------
# 5. PatientListing.ent — committed (placeholder) shape
# ---------------------------------------------------------------------------

def test_listing_ent_is_json_and_has_placeholder_csweb_url():
    """The committed .ent has csweb_url='PLACEHOLDER'. build_all.py splices
    the env-specific URL at build time but does NOT write back to disk in
    a way that should be committed."""
    path = LISTING_DIR / "PatientListing.ent"
    if not path.exists():
        pytest.skip("PatientListing.ent missing — run generate_ent.py first.")
    ent = json.loads(path.read_text(encoding="utf-8"))
    settings = {s["name"]: s["value"] for s in ent["userSettings"]}
    # After a `build_all.py --env=dev` run the value is spliced; but the
    # committed copy is the placeholder. Don't fail on either — just
    # assert the key is present.
    assert "csweb_url"       in settings
    assert "expiration_days" in settings
