import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generate_dcf import build_sv_dictionary, TP_TYPES


def _items(rec):
    return {it["name"]: it for it in rec["items"]}


def test_dictionary_shape():
    d = build_sv_dictionary()
    assert d["name"] == "SUPERVISORAPP_DICT"
    level = d["levels"][0]
    # Case key = the 9-digit facility code
    ids = level["ids"]["items"]
    assert ids[0]["name"] == "FACILITY_CODE"
    assert ids[0]["length"] == 9 and ids[0]["zeroFill"] is True
    recs = {r["name"]: r for r in level["records"]}
    assert set(recs) == {"VISIT_HEADER", "COURTESY_CALL", "TOUCHPOINT"}


def test_touchpoint_roster_is_repeating_with_gps_and_timestamp():
    recs = {r["name"]: r for r in build_sv_dictionary()["levels"][0]["records"]}
    tp = recs["TOUCHPOINT"]
    assert tp["recordType"] == "T"
    assert tp["occurrences"] == {"required": False, "maximum": 30}
    items = _items(tp)
    # type, timestamp, full GPS block, line index, note
    for name in ("TP_LINE", "TP_TYPE", "TP_TIMESTAMP", "TP_GPS_LATITUDE",
                 "TP_GPS_LONGITUDE", "TP_GPS_ACCURACY", "TP_GPS_READTIME",
                 "TP_OUTCOME_NOTE"):
        assert name in items, name
    # TP_TYPE carries the 8-code value set
    vs = items["TP_TYPE"]["valueSets"][0]["values"]
    assert len(vs) == len(TP_TYPES) == 8
    assert vs[0]["pairs"][0]["value"] == "1"
    assert vs[-1]["pairs"][0]["value"] == "8"


def test_courtesy_call_block_and_offform_photo():
    recs = {r["name"]: r for r in build_sv_dictionary()["levels"][0]["records"]}
    cc = _items(recs["COURTESY_CALL"])
    for name in ("CC_ENDORSEMENT_OBTAINED", "CC_FOCAL_PERSON_NAME",
                 "CC_HCW_LIST_CAPTURED", "CC_HCW_LIST_COUNT",
                 "CC_PATIENT_LISTING_DATE", "CC_WORKSTATION_ARRANGED"):
        assert name in cc, name
    # binary photo item present (off-form; synced to CSWeb)
    assert cc["VERIFICATION_PHOTO_IMAGE"]["contentType"] == "image"
    assert "CAPTURE_VERIFICATION_PHOTO" in cc
