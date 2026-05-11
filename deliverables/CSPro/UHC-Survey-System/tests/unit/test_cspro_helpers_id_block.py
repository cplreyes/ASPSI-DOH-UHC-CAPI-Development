"""Unit tests for build_id_block() and the extended build_dictionary() in
shared/cspro_helpers.py.

These tests pin the adopted 12-digit decomposed case-ID shape (per
wiki/concepts/Questionnaire Numbering Convention.md) so that any future
edit to widths, names, or zero-fill behavior fails fast at the test layer
instead of corrupting downstream F1/F3/F4 dictionaries.
"""
import pytest

from shared.cspro_helpers import (
    build_dictionary,
    build_id_block,
    CASE_SEQ_ACTIVE_RANGE,
    CASE_SEQ_REPLACEMENT_RANGE,
    CASE_SEQ_REFUSED_RANGE,
)


# ---------------------------------------------------------------------------
# build_id_block() — structural pins
# ---------------------------------------------------------------------------

def test_build_id_block_returns_five_items_in_order():
    block = build_id_block()
    names = [it["name"] for it in block]
    assert names == [
        "REGION_CODE",
        "PROVINCE_HUC_CODE",
        "CITY_MUNICIPALITY_CODE",
        "FACILITY_NO",
        "CASE_SEQ",
    ]


def test_build_id_block_widths_match_concept_page():
    """Widths total 12 digits per the 2026-05-05 adopted convention."""
    block = build_id_block()
    width_by_name = {it["name"]: it["length"] for it in block}
    assert width_by_name == {
        "REGION_CODE":            2,
        "PROVINCE_HUC_CODE":      2,
        "CITY_MUNICIPALITY_CODE": 3,
        "FACILITY_NO":            2,
        "CASE_SEQ":               3,
    }
    assert sum(it["length"] for it in block) == 12


def test_build_id_block_start_positions_are_contiguous():
    """Case ID occupies columns 2-13 (col 1 is record-type)."""
    block = build_id_block()
    expected_starts = [2, 4, 6, 9, 11]
    expected_widths = [2, 2, 3, 2, 3]
    for it, exp_start, exp_width in zip(block, expected_starts, expected_widths):
        assert it["start"] == exp_start, f"{it['name']} start={it['start']} expected {exp_start}"
        assert it["length"] == exp_width


def test_build_id_block_all_items_numeric_zero_filled_no_decimal():
    """ID items are required, non-NA, decimal-zero numeric per the spec."""
    block = build_id_block()
    for it in block:
        assert it["contentType"] == "numeric"
        assert it["zeroFill"] is True
        assert it["decimal"] == 0
        assert it["decimalChar"] is False


def test_build_id_block_labels_are_verbatim():
    """Labels match the adopted manual addendum wording (concept page)."""
    block = build_id_block()
    label_by_name = {it["name"]: it["labels"][0]["text"] for it in block}
    assert label_by_name == {
        "REGION_CODE":            "Region Code",
        "PROVINCE_HUC_CODE":      "Province / HUC Code",
        "CITY_MUNICIPALITY_CODE": "City / Municipality Code",
        "FACILITY_NO":            "Facility No",
        "CASE_SEQ":               "Case Sequence",
    }


# ---------------------------------------------------------------------------
# CASE_SEQ range constants — replacement protocol pins
# ---------------------------------------------------------------------------

def test_case_seq_ranges_partition_cleanly():
    """Active / replacement / refused ranges cover 001-999 with no gaps or overlap."""
    a_lo, a_hi = CASE_SEQ_ACTIVE_RANGE
    r_lo, r_hi = CASE_SEQ_REPLACEMENT_RANGE
    f_lo, f_hi = CASE_SEQ_REFUSED_RANGE
    assert (a_lo, a_hi) == (1,   699)
    assert (r_lo, r_hi) == (700, 899)
    assert (f_lo, f_hi) == (900, 999)
    # Contiguous, no gap, no overlap
    assert a_hi + 1 == r_lo
    assert r_hi + 1 == f_lo


# ---------------------------------------------------------------------------
# build_dictionary() — new id_items= path
# ---------------------------------------------------------------------------

def test_build_dictionary_with_id_items_uses_block_verbatim():
    block = build_id_block()
    d = build_dictionary(
        dict_name="X_DICT", dict_label="X",
        id_items=block, records=[],
    )
    ids = d["levels"][0]["ids"]["items"]
    assert ids == block  # passed through unchanged


def test_build_dictionary_with_id_items_rejects_legacy_kwargs():
    block = build_id_block()
    with pytest.raises(ValueError, match="either id_items"):
        build_dictionary(
            dict_name="X_DICT", dict_label="X",
            id_item_name="FOO", id_item_label="Foo", id_length=6,
            id_items=block, records=[],
        )


# ---------------------------------------------------------------------------
# build_dictionary() — legacy single-item path (compat regression)
# ---------------------------------------------------------------------------

def test_build_dictionary_legacy_single_id_item_path_still_works():
    """Until F3/F4/PLF migrate, the old call shape must keep producing the
    one-item ID list at start=2 with the given length and zero-fill."""
    d = build_dictionary(
        dict_name="X_DICT", dict_label="X",
        id_item_name="QUESTIONNAIRE_NO", id_item_label="Questionnaire No",
        id_length=6, records=[],
    )
    ids = d["levels"][0]["ids"]["items"]
    assert len(ids) == 1
    assert ids[0] == {
        "name":        "QUESTIONNAIRE_NO",
        "labels":      [{"text": "Questionnaire No"}],
        "contentType": "numeric",
        "start":       2,
        "length":      6,
        "zeroFill":    True,
    }


def test_build_dictionary_requires_some_id_shape():
    with pytest.raises(ValueError, match="must pass id_items"):
        build_dictionary(
            dict_name="X_DICT", dict_label="X", records=[],
        )
