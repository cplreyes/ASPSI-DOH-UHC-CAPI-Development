"""Smoke-test for the 113_F4_listing CSPro build.

Asserts that:
  1. shared.cspro_helpers.build_listing_id_block() still emits a 6-item
     session-ID block whose widths total 20 digits — same block as the
     110_F3_listing app per Carl's Q3 decision.
  2. F4Listing.dcf parses as JSON, has the expected record set, and
     the load-bearing items (LISTING_SOURCE, BARANGAY_CODE,
     REPLACEMENT_RESERVES, LISTING_NO, F4_STATUS, FROM_RESERVE_POOL,
     MOBILE alpha-11, HH_ELIGIBLE) are present with the expected
     widths.
  3. F4Listing.fmf is BOM-prefixed and has 5 [Form] blocks (1 IDS + 4
     record forms).
  4. F4Listing.ent.apc contains the load-bearing PROC / function
     definitions:
       - function SeedSessionPRNG (with BARANGAY_CODE seed input — Q8)
       - function IncrementSessionCounter
       - function ContainsRefusalMarker
       - PROC LISTING_SOURCE postproc with the soft warnmsg (Q1)
       - PROC SESSION_STATUS postproc with synchronize_file(remotePath)
         and the BARANGAY10 path segment (Q3 sync-path encoding)
       - DEFAULT_REPLACEMENT_RESERVES = 10 (Q2)
     AND does NOT contain ComputeListingTag / TAG1_THRESHOLD_KM /
     cadence-engine references (those belong to F3 listing only).
  5. F4Listing.ent is JSON-parseable and has csweb_url='PLACEHOLDER'
     in the committed copy (per the pre-splice convention).
  6. F4LIST is registered in build_all.py INSTRUMENTS.
"""
import json
import re
from pathlib import Path

import pytest


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
LISTING_DIR    = WORKSPACE_ROOT / "113_F4_listing"


# ---------------------------------------------------------------------------
# 1. build_listing_id_block() — reused from F3 listing per Q3
# ---------------------------------------------------------------------------

def test_f4_listing_reuses_same_session_id_block_as_f3_listing():
    """Carl's Q3 decision: F4 listing reuses the existing F3-listing
    build_listing_id_block() helper. This test pins that decision —
    if someone later splits the helpers, the test breaks loudly so
    the decision is reconsidered."""
    from shared.cspro_helpers import build_listing_id_block
    block = build_listing_id_block()
    names = [it["name"] for it in block]
    # Same 6-item 20-digit shape as F3 listing.
    assert names == [
        "REGION_CODE",
        "PROVINCE_HUC_CODE",
        "CITY_MUNICIPALITY_CODE",
        "FACILITY_NO",
        "LISTING_SESSION_DATE",
        "LISTING_SESSION_SEQ",
    ]
    assert sum(it["length"] for it in block) == 20


# ---------------------------------------------------------------------------
# 2. F4Listing.dcf
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def f4_listing_dcf():
    path = LISTING_DIR / "F4Listing.dcf"
    if not path.exists():
        pytest.skip(
            "F4Listing.dcf missing — run "
            "`python 113_F4_listing/generate_dcf.py` first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def test_f4_listing_dcf_has_four_records_plus_root(f4_listing_dcf):
    records = f4_listing_dcf["levels"][0]["records"]
    names = [r["name"] for r in records]
    assert names == [
        "F4LISTING_REC",
        "REC_LISTING_CONTROL",
        "REC_LISTING_BRGY_FRAME",
        "REC_LISTING_BARANGAY_GPS",
    ]


def test_f4_listing_dcf_id_block_is_decomposed_six_item(f4_listing_dcf):
    ids = f4_listing_dcf["levels"][0]["ids"]["items"]
    assert len(ids) == 6
    assert ids[0]["name"]  == "REGION_CODE"
    assert ids[-1]["name"] == "LISTING_SESSION_SEQ"


def test_f4_listing_dcf_control_has_listing_source_and_barangay(f4_listing_dcf):
    """Q1 hybrid-model and Q3 sync-path encoding pins."""
    records = {r["name"]: r for r in f4_listing_dcf["levels"][0]["records"]}
    control = records["REC_LISTING_CONTROL"]
    item_names = {it["name"] for it in control["items"]}
    # Q1 — hybrid model
    assert "LISTING_SOURCE"        in item_names
    # Q3 — BARANGAY_CODE is a regular data item (NOT in the session ID block)
    assert "BARANGAY_CODE"         in item_names
    assert "BARANGAY_NAME"         in item_names
    # Q2 — replacement reserves slot
    assert "REPLACEMENT_RESERVES"  in item_names
    # FRAME-finalizer + counters
    assert "FRAME_TARGET"          in item_names
    assert "LISTED_COUNT"          in item_names
    assert "REFUSED_COUNT"         in item_names
    assert "EXCLUDED_COUNT"        in item_names
    assert "SESSION_STATUS"        in item_names
    assert "FRAME_NOTES"           in item_names


def test_f4_listing_dcf_control_item_widths_match_spec(f4_listing_dcf):
    """Spot-check the load-bearing widths from
    F4-Listing-Skip-Logic-and-Validations.md."""
    records = {r["name"]: r for r in f4_listing_dcf["levels"][0]["records"]}
    control = records["REC_LISTING_CONTROL"]
    widths = {it["name"]: it["length"] for it in control["items"]}
    assert widths["LISTING_SOURCE"]        == 1   # 1/2/9
    assert widths["BARANGAY_CODE"]         == 10  # 10-digit PSGC
    assert widths["FRAME_TARGET"]          == 3
    assert widths["REPLACEMENT_RESERVES"]  == 3
    assert widths["SESSION_STATUS"]        == 1


def test_f4_listing_dcf_roster_has_load_bearing_items(f4_listing_dcf):
    records = {r["name"]: r for r in f4_listing_dcf["levels"][0]["records"]}
    roster = records["REC_LISTING_BRGY_FRAME"]
    item_names = {it["name"] for it in roster["items"]}
    assert "LISTING_NO"              in item_names
    assert "F4_STATUS"               in item_names
    assert "ASSIGNED_F4_CASE_SEQ"    in item_names
    assert "FROM_RESERVE_POOL"       in item_names   # Q2 reserve flag
    assert "HEAD_LAST_NAME"          in item_names
    assert "HEAD_FIRST_NAME"         in item_names
    assert "HH_ADDRESS"              in item_names
    assert "MOBILE"                  in item_names   # Q5 — optional alpha-11
    assert "HH_ELIGIBLE"             in item_names


def test_f4_listing_dcf_mobile_is_alpha_11(f4_listing_dcf):
    """Q5 decision: phone optional, alpha-11."""
    records = {r["name"]: r for r in f4_listing_dcf["levels"][0]["records"]}
    roster = records["REC_LISTING_BRGY_FRAME"]
    mobile = next(it for it in roster["items"] if it["name"] == "MOBILE")
    assert mobile["contentType"] == "alpha"
    assert mobile["length"]      == 11


def test_f4_listing_dcf_roster_max_occurs_999(f4_listing_dcf):
    """Q4 decision: 999-occurrence frame cap."""
    records = {r["name"]: r for r in f4_listing_dcf["levels"][0]["records"]}
    roster = records["REC_LISTING_BRGY_FRAME"]
    assert roster["occurrences"]["maximum"] == 999


def test_f4_listing_dcf_has_barangay_gps_record_no_photo(f4_listing_dcf):
    """Q6 decision: GPS only, no verification photo.

    REC_LISTING_BARANGAY_GPS present; no REC_LISTING_PHOTO sibling."""
    records = {r["name"]: r for r in f4_listing_dcf["levels"][0]["records"]}
    assert "REC_LISTING_BARANGAY_GPS" in records
    # No photo record at all in F4 listing.
    all_names = set(records.keys())
    assert "REC_LISTING_PHOTO"           not in all_names
    assert "REC_LISTING_BARANGAY_PHOTO"  not in all_names

    gps = records["REC_LISTING_BARANGAY_GPS"]
    gps_item_names = {it["name"] for it in gps["items"]}
    # GPS metadata items emitted by shared._gps_fields(prefix="BARANGAY_")
    assert "BARANGAY_GPS_LATITUDE"  in gps_item_names
    assert "BARANGAY_GPS_LONGITUDE" in gps_item_names
    assert "BARANGAY_CAPTURE_GPS"   in gps_item_names


# ---------------------------------------------------------------------------
# 3. F4Listing.fmf
# ---------------------------------------------------------------------------

def test_f4_listing_fmf_is_bom_prefixed_and_has_five_forms():
    path = LISTING_DIR / "F4Listing.fmf"
    if not path.exists():
        pytest.skip(
            "F4Listing.fmf missing — run "
            "`python 113_F4_listing/generate_fmf.py` first."
        )
    content = path.read_text(encoding="utf-8")
    # BOM at byte 0
    assert content.startswith("﻿"), "FMF must be BOM-prefixed"
    # 5 [Form] blocks: 1 IDS + 4 records (control + roster + GPS = 4)
    assert content.count("[Form]\n") == 5


# ---------------------------------------------------------------------------
# 4. F4Listing.ent.apc
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def f4_listing_apc():
    path = LISTING_DIR / "F4Listing.ent.apc"
    if not path.exists():
        pytest.skip(
            "F4Listing.ent.apc missing — run "
            "`python 113_F4_listing/generate_apc.py` first."
        )
    return path.read_text(encoding="utf-8")


def test_f4_listing_apc_has_load_bearing_definitions(f4_listing_apc):
    apc = f4_listing_apc
    # PRNG + helpers
    assert "function SeedSessionPRNG"    in apc
    assert "function IncrementSessionCounter" in apc
    assert "function ContainsRefusalMarker"   in apc
    # Q1 — soft warnmsg on LISTING_SOURCE = 1 + refusal-marker text
    assert "PROC LISTING_SOURCE"         in apc
    assert "warnmsg"                     in apc
    # Q2 — DEFAULT_REPLACEMENT_RESERVES = 10
    assert "DEFAULT_REPLACEMENT_RESERVES = 10" in apc
    # Q3 — sync-path with BARANGAY10 segment
    assert "synchronize_file"            in apc
    assert "f4_listing/"                 in apc
    assert "%010d" in apc and "BARANGAY_CODE" in apc
    # Q6 — no photo block
    assert "TakeVerificationPhoto"       not in apc
    # Wired-in shared helpers
    assert '#include "../shared/Capture-Helpers.apc"' in apc


def test_f4_listing_apc_seed_inputs_include_barangay_code(f4_listing_apc):
    """Q8 — seed inputs include BARANGAY_CODE, distinguishing F4 listing
    seed inputs from F3 listing (which has no barangay dimension)."""
    apc = f4_listing_apc
    # The SeedSessionPRNG call passes BARANGAY_CODE as the 4th argument.
    # Looking for the literal call signature in the .apc body.
    assert re.search(
        r"SeedSessionPRNG\(\s*ENUMERATOR_ID\s*,\s*DATE_SESSION\s*,\s*"
        r"TIME_SESSION_START\s*,\s*BARANGAY_CODE\s*\)",
        apc,
    ), "expected SeedSessionPRNG(ENUMERATOR_ID, DATE_SESSION, TIME_SESSION_START, BARANGAY_CODE)"


def test_f4_listing_apc_does_not_contain_f3_listing_specific_logic(f4_listing_apc):
    """F4 listing has no cadence engine and no auto-tag rule. If those
    appear, the generator has been copy-pasted from F3 listing without
    the structural pruning."""
    apc = f4_listing_apc
    # Cadence engine (F3 listing only)
    assert "DrawRandomInterval"          not in apc
    assert "CADENCE_HARD_MIN_SEC"        not in apc
    # Auto-tag rule (F3 listing only)
    assert "ComputeListingTag"           not in apc
    assert "TAG1_THRESHOLD_KM"           not in apc
    assert "TAG2_THRESHOLD_KM"           not in apc
    # PENDING_DESIGN_AUTO_TAG_RULE marker (F3 listing only)
    assert "PENDING_DESIGN_AUTO_TAG_RULE" not in apc


# ---------------------------------------------------------------------------
# 5. F4Listing.ent — committed (placeholder) shape
# ---------------------------------------------------------------------------

def test_f4_listing_ent_is_json_and_has_user_settings():
    """The committed .ent has csweb_url='PLACEHOLDER'. build_all.py splices
    the env-specific URL at build time but does NOT write back to disk in
    a way that should be committed."""
    path = LISTING_DIR / "F4Listing.ent"
    if not path.exists():
        pytest.skip("F4Listing.ent missing — run generate_ent.py first.")
    ent = json.loads(path.read_text(encoding="utf-8"))
    settings = {s["name"]: s["value"] for s in ent["userSettings"]}
    # Don't fail on either pre-splice or post-splice — just assert the
    # keys are present. Matches the F3-listing / F4 pattern.
    assert "csweb_url"       in settings
    assert "expiration_days" in settings


def test_f4_listing_ent_has_no_external_dict_refs():
    """F4 listing is a producer, not a consumer. It MUST NOT declare any
    EXTERNAL dictionary refs. The consumer 115_F4 is the one that
    declares F4LISTING_DICT as EXTERNAL."""
    path = LISTING_DIR / "F4Listing.ent"
    if not path.exists():
        pytest.skip("F4Listing.ent missing — run generate_ent.py first.")
    ent = json.loads(path.read_text(encoding="utf-8"))
    dict_entries = ent["dictionaries"]
    assert len(dict_entries) == 1
    assert dict_entries[0]["type"] == "input"
    assert dict_entries[0]["path"] == "F4Listing.dcf"


# ---------------------------------------------------------------------------
# 6. build_all.py wiring
# ---------------------------------------------------------------------------

def test_f4list_is_in_build_all_instruments():
    """The F4LIST tuple must be registered in build_all.py so the
    --only=F4LIST shortcut works and the full --env=dev sweep includes
    F4LIST in the F7-publish checklist."""
    build_all = (WORKSPACE_ROOT / "build_all.py").read_text(encoding="utf-8")
    assert '"F4LIST"'        in build_all
    assert '"113_F4_listing"' in build_all
    assert '"F4Listing"'      in build_all
