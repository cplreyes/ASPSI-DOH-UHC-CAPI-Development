"""scan_poisoned_keys.py's reasoned per-key waiver (Task 50 fix round 1).

Why this exists: `SELF_ECHO` / `IS_OTHER_EN` say "the value equals an English label", which is a
defect *when the paper carries a translation*. The Aug-21 Cebuano paper prints the proper noun
`LGU/Barangay` untranslated against code 06 of seven `*_SOURCE_VS1` value sets — so importing the
paper's own text necessarily makes the value equal the English, gate 1 of run_aug21_gates.ps1 sees
a reason GROW, and the wave cannot publish the value the controller ruled must be written. The
waiver is the narrow, reasoned, per-key, per-locale, VALUE-PINNED exemption that closes that gap
without blunting the detector for anything else.

Everything here tests pure functions. `scan_poisoned_keys.main()` regenerates the live .dcf files
(capture_source_dict runs each generate_dcf.py) and is never called from a test.
"""
import io
import json
import sys

import pytest


@pytest.fixture(scope="module")
def scan():
    """Import the tool without letting its stdout rewrap leak into pytest's capture."""
    saved = sys.stdout
    try:
        import scan_poisoned_keys as m
    finally:
        sys.stdout = saved
    return m


def write(tmp_path, data):
    p = tmp_path / "scan_waivers.json"
    io.open(p, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False))
    return str(p)


OK_ENTRY = {"value": "LGU/Barangay", "reasons": ["SELF_ECHO"],
            "reason": "F3_CEB.txt:1028-1035 prints the option untranslated."}


def good(**over):
    ent = dict(OK_ENTRY)
    ent.update(over)
    return {"F3": {"ceb": {"val:Q36_UHC_SOURCE_VS1:06": ent}}}


# --- load / validate -------------------------------------------------------------------

def test_a_missing_waiver_file_is_simply_no_waivers(scan, tmp_path):
    assert scan.load_waivers(str(tmp_path / "nope.json")) == {}


def test_a_valid_file_loads_flat_and_uppercases_the_locale(scan, tmp_path):
    w = scan.load_waivers(write(tmp_path, good()))
    assert list(w) == [("F3", "CEB", "val:Q36_UHC_SOURCE_VS1:06")]
    assert w[("F3", "CEB", "val:Q36_UHC_SOURCE_VS1:06")]["value"] == "LGU/Barangay"


@pytest.mark.parametrize("data,fragment", [
    ({"F9": {"ceb": {"val:X:1": OK_ENTRY}}}, "unknown instrument"),
    ({"F3": {"xx": {"val:X:1": OK_ENTRY}}}, "not a known locale"),
    ({"F3": {"ceb": {"no_colon": OK_ENTRY}}}, "name-scoped"),
    ({"F3": {"ceb": {"val:X:1": {"reasons": ["SELF_ECHO"], "reason": "r"}}}}, "'value'"),
    ({"F3": {"ceb": {"val:X:1": {"value": "", "reasons": ["SELF_ECHO"], "reason": "r"}}}}, "'value'"),
    ({"F3": {"ceb": {"val:X:1": {"value": "v", "reasons": [], "reason": "r"}}}}, "'reasons'"),
    ({"F3": {"ceb": {"val:X:1": {"value": "v", "reasons": ["SELF_ECHO", "SELF_ECHO"],
                                 "reason": "r"}}}}, "duplicate"),
    ({"F3": {"ceb": {"val:X:1": {"value": "v", "reasons": ["SELF_ECHO"], "reason": "  "}}}},
     "'reason'"),
])
def test_the_validator_rejects_a_malformed_waiver(scan, data, fragment):
    errs = scan.validate_waivers(data)
    assert errs and any(fragment in e for e in errs), errs


@pytest.mark.parametrize("reason", ["DOUBLED", "EN_FRAGMENT", "WRONG_Q_CLEARED",
                                    "GLUED_CLEARED", "STALE_KEY"])
def test_only_the_two_english_echo_reasons_can_ever_be_waived(scan, reason):
    """A waiver must not become a way to silence a real corruption class."""
    errs = scan.validate_waivers(good(reasons=[reason]))
    assert errs and any("not waivable" in e for e in errs), (reason, errs)


def test_an_invalid_file_raises_rather_than_loading_a_half_valid_waiver_set(scan, tmp_path):
    with pytest.raises(SystemExit):
        scan.load_waivers(write(tmp_path, {"F3": {"ceb": {"bad": OK_ENTRY}}}))


# --- matching --------------------------------------------------------------------------

def test_the_waiver_fires_only_on_its_own_key_locale_and_reason(scan, tmp_path):
    w = scan.load_waivers(write(tmp_path, good()))
    K = "val:Q36_UHC_SOURCE_VS1:06"
    assert scan.is_waived(w, "F3", "CEB", K, "SELF_ECHO", "LGU/Barangay")
    assert not scan.is_waived(w, "F3", "CEB", K, "IS_OTHER_EN", "LGU/Barangay")   # not listed
    assert not scan.is_waived(w, "F3", "WAR", K, "SELF_ECHO", "LGU/Barangay")     # other locale
    assert not scan.is_waived(w, "F1", "CEB", K, "SELF_ECHO", "LGU/Barangay")     # other instrument
    assert not scan.is_waived(w, "F3", "CEB", "val:Other:06", "SELF_ECHO", "LGU/Barangay")


def test_a_waiver_is_pinned_to_the_exact_value_it_was_written_for(scan, tmp_path):
    """If the map value drifts, the waiver stops covering it and the scan flags it again."""
    w = scan.load_waivers(write(tmp_path, good()))
    K = "val:Q36_UHC_SOURCE_VS1:06"
    assert scan.is_waived(w, "F3", "CEB", K, "SELF_ECHO", "  LGU/Barangay  ")  # whitespace only
    assert not scan.is_waived(w, "F3", "CEB", K, "SELF_ECHO", "Balaod")
    assert not scan.is_waived(w, "F3", "CEB", K, "SELF_ECHO", "lgu/barangay")


def test_apply_waivers_splits_the_reasons_and_records_the_hit(scan, tmp_path):
    w = scan.load_waivers(write(tmp_path, good()))
    hits = {}
    kept, waived = scan.apply_waivers(w, "F3", "CEB", "val:Q36_UHC_SOURCE_VS1:06",
                                      "LGU/Barangay", ["SELF_ECHO", "DOUBLED"], hits)
    assert kept == ["DOUBLED"] and waived == ["SELF_ECHO"]
    assert hits == {("F3", "CEB", "val:Q36_UHC_SOURCE_VS1:06"): 1}


def test_a_waiver_that_matched_nothing_is_reported_as_stale(scan, tmp_path):
    w = scan.load_waivers(write(tmp_path, good()))
    assert scan.stale_waivers(w, {}) == [("F3", "CEB", "val:Q36_UHC_SOURCE_VS1:06")]
    assert scan.stale_waivers(w, {("F3", "CEB", "val:Q36_UHC_SOURCE_VS1:06"): 1}) == []


# --- the shipped file --------------------------------------------------------------------

CEB_06 = ["val:Q36_UHC_SOURCE_VS1:06", "val:Q75_KON_SOURCE_VS1:06",
          "val:Q100_BUCAS_SOURCE_VS1:06", "val:Q117_NBB_SOURCE_VS1:06",
          "val:Q120_ZBB_SOURCE_VS1:06", "val:Q125_MAIFIP_SOURCE_VS1:06",
          "val:Q153_GAMOT_SOURCE_VS1:06"]


def test_the_shipped_waiver_file_is_valid_and_holds_exactly_the_seven_ceb_source_rows(scan):
    raw = json.loads(io.open(scan.WAIVERS_PATH, encoding="utf-8").read())
    assert scan.validate_waivers(raw) == []
    assert [k for k in raw if not k.startswith("_")] == ["F3"]
    assert list(raw["F3"]) == ["ceb"]
    assert sorted(raw["F3"]["ceb"]) == sorted(CEB_06)
    for key, ent in raw["F3"]["ceb"].items():
        assert ent["value"] == "LGU/Barangay"
        assert "F3_CEB.txt" in ent["reason"], key      # every waiver cites its paper line
