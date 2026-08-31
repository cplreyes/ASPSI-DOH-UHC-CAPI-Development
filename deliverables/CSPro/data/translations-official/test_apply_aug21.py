import io
import json
import os
import sys
from collections import OrderedDict

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from aug21_overrides import validate_overrides, load_overrides  # noqa: E402


def test_validate_overrides_accepts_spec_example():
    data = {"F3": {"val:Q5_SEX_VS1:1": {
        "keep": "Lalaki", "reason": "Aug-21 PDF still swaps Male/Female (June-5 defect carried)"}}}
    assert validate_overrides(data) == []


def test_validate_overrides_rejects_bad_shapes():
    errs = validate_overrides({
        "F9": {},                                             # unknown instrument
        "F1": {"Q1_NAME": {"keep": "x", "reason": "r"}},      # no ':' in a CSPro key
        "F3": {"item:Q1_NAME": {"keep": "x"}},                # reason missing
        "F4": {"item:Q1_NAME": {"keep": "", "reason": "r"}},  # empty keep on a map key
        "F2": {"fil": {"Sex": {"keep": "Kasarian", "reason": "ok"},
                       "No": {"keep": None, "reason": "suppress"}}},   # F2 = locale-nested, null ok
    })
    assert any(e.startswith("F9:") for e in errs)
    assert any(e.startswith("F1/") and "Q1_NAME" in e and "':'" in e for e in errs)
    assert any(e.startswith("F3/") and "reason" in e for e in errs)
    assert any(e.startswith("F4/") and "keep" in e for e in errs)
    assert not any(e.startswith("F2/") or e.startswith("F2:") for e in errs)


def test_validate_overrides_allows_empty_keep_for_notes_and_icf():
    data = {"F1": {"icf:1:1:FIL": {"keep": "", "reason": "force English"},
                   "note:intro:4:BCL": {"keep": "", "reason": "force English"}}}
    assert validate_overrides(data) == []


def test_load_overrides_exits_on_invalid(tmp_path):
    p = tmp_path / "ov.json"
    p.write_text(json.dumps({"F1": {"nokey": {"keep": "x", "reason": "r"}}}), encoding="utf-8")
    with pytest.raises(SystemExit):
        load_overrides(str(p))
    p.write_text("{}", encoding="utf-8")
    assert load_overrides(str(p)) == {}


def test_validate_overrides_accepts_valid_f2_scope():
    data = {"F2": {"fil": {"Do you consent?": {
        "keep": "Pumapayag ka ba?", "reason": "scope test", "scope": "consent"}}}}
    assert validate_overrides(data) == []


def test_validate_overrides_rejects_bad_f2_scope():
    errs = validate_overrides({"F2": {"fil": {"Do you consent?": {
        "keep": "Pumapayag ka ba?", "reason": "scope test", "scope": "bogus"}}}})
    assert any(e.startswith("F2/") and "scope" in e for e in errs)


from apply_aug21 import merge_locale, override_for  # noqa: E402


def _cur():
    return OrderedDict([("_meta", {"format": "name-scoped-v2"}),
                        ("item:Q1_NAME", "Ano ang pangalan mo?"),
                        ("val:Q5_SEX_VS1:1", "Babae"),          # swapped defect, kept by override
                        ("val:Q5_SEX_VS1:2", "Lalaki"),
                        ("item:Q9_OLD", "luma")])


def test_merge_absent_equal_different_override_flagged():
    pairs = {"item:Q1_NAME": "Ano ang pangalan mo?",           # equal -> already_same
             "item:Q2_ROLE": "Ano ang tungkulin mo?",          # absent -> write
             "val:Q5_SEX_VS1:1": "Lalaki",                     # different but overridden
             "val:Q5_SEX_VS1:2": "Babae",                      # different -> replace
             "item:Q7_FLAGGED": "bleed text"}                  # flagged -> never written
    overrides = {"val:Q5_SEX_VS1:1": {"keep": "Babae", "reason": "June-5 swap carried"}}
    r = merge_locale(_cur(), pairs, {"item:Q7_FLAGGED"}, overrides)
    assert r.writes == OrderedDict([("item:Q2_ROLE", "Ano ang tungkulin mo?"),
                                    ("val:Q5_SEX_VS1:2", "Babae")])
    assert r.replaced == [("val:Q5_SEX_VS1:2", "Lalaki", "Babae")]
    assert r.overridden == [("val:Q5_SEX_VS1:1", "Babae", "Lalaki")]
    assert r.already_same == 1
    assert r.flagged_skipped == 1
    assert r.override_stale == []        # keep == current map value
    assert "item:Q7_FLAGGED" not in r.writes


def test_merge_whitespace_equal_counts_as_same_and_override_stale_is_reported():
    # Q1: whitespace-only difference -> already_same.
    # Q5:1: proposed EQUALS current ("Babae") -> already_same, but the override's keep text
    # ("Lalaki") has drifted from the map -> override_stale.
    pairs = {"item:Q1_NAME": "Ano  ang pangalan mo? ", "val:Q5_SEX_VS1:1": "Babae"}
    overrides = {"val:Q5_SEX_VS1:1": {"keep": "Lalaki", "reason": "keep text drifted"}}
    r = merge_locale(_cur(), pairs, set(), overrides)
    assert r.already_same == 2
    assert r.writes == OrderedDict() and r.overridden == []
    assert r.override_stale == ["val:Q5_SEX_VS1:1"]


def test_merge_override_branch_with_stale_keep():
    # different proposal + override whose keep no longer matches the map -> overridden AND stale
    pairs = {"val:Q5_SEX_VS1:1": "Lalaki"}
    overrides = {"val:Q5_SEX_VS1:1": {"keep": "Lalake", "reason": "typo in keep"}}
    r = merge_locale(_cur(), pairs, set(), overrides)
    assert r.overridden == [("val:Q5_SEX_VS1:1", "Babae", "Lalaki")]
    assert r.override_stale == ["val:Q5_SEX_VS1:1"] and r.writes == OrderedDict()


def test_merge_unmatched_anchors_and_meta_never_touched():
    all_keys = {"item:Q1_NAME", "item:Q2_ROLE", "val:Q5_SEX_VS1:1", "val:Q5_SEX_VS1:2",
                "item:Q3_UNSEEN"}
    r = merge_locale(_cur(), {"item:Q2_ROLE": "x"}, {"val:Q5_SEX_VS1:1"}, {}, all_keys)
    assert set(r.unmatched) == {"item:Q3_UNSEEN", "item:Q1_NAME", "val:Q5_SEX_VS1:2"}
    assert "_meta" not in r.writes


from apply_aug21 import load_extract, stamp_meta, run  # noqa: E402


def _write(path, obj, crlf=False, indent=2):
    txt = json.dumps(obj, ensure_ascii=False, indent=indent)
    if crlf:
        txt = txt.replace("\n", "\r\n")
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(txt + ("\r\n" if crlf else "\n"))


def test_load_extract_reads_clean_and_flagged(tmp_path):
    _write(tmp_path / "fil.json", {"_meta": {"x": 1}, "item:Q1": "a"})
    _write(tmp_path / "fil_flagged.json", [{"key": "item:Q2", "en": "e", "tr": "t", "flags": ["table-bleed"]}])
    pairs, flagged = load_extract(str(tmp_path), "fil")
    assert pairs == {"item:Q1": "a"} and flagged == {"item:Q2"}
    assert load_extract(str(tmp_path), "war") == ({}, set())   # missing locale = empty, not error


def test_run_apply_preserves_crlf_indent_order_and_stamps_meta(tmp_path):
    ex = tmp_path / "extract"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "fil.json", {"item:Q2": "bago", "item:Q1": "iba na"})
    _write(ex / "fil_flagged.json", [{"key": "item:Q3", "en": "", "tr": "", "flags": ["empty"]}])
    _write(maps / "fil.json", OrderedDict([("_meta", {"format": "name-scoped-v2"}),
                                           ("item:Q1", "luma"), ("item:Q9", "z")]), crlf=True, indent=1)
    res, _gate = run("F1", str(ex), str(maps), {}, apply=True, all_keys=None, date="2026-08-26")
    raw = io.open(maps / "fil.json", encoding="utf-8", newline="").read()
    assert "\r\n" in raw and raw.startswith('{\r\n "_meta"')          # CRLF + 1-space indent kept
    m = json.loads(raw, object_pairs_hook=OrderedDict)
    assert list(m) == ["_meta", "item:Q1", "item:Q9", "item:Q2"]     # order kept, new key appended
    assert m["item:Q1"] == "iba na"
    assert m["_meta"]["sources"]["aug21"] == {"date": "2026-08-26", "file": "fil.json",
        "n_written": 1, "n_replaced": 1, "n_overridden": 0, "n_removed": 0,
        "n_flagged_skipped": 1}
    assert res["fil"].replaced == [("item:Q1", "luma", "iba na")]


def test_run_dry_run_writes_nothing(tmp_path):
    ex = tmp_path / "extract"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "bcl.json", {"item:Q1": "bago"})
    _write(maps / "bcl.json", {"_meta": {}, "item:Q1": "luma"})
    before = io.open(maps / "bcl.json", encoding="utf-8").read()
    res, _gate = run("F1", str(ex), str(maps), {}, apply=False, all_keys=None, date="2026-08-26")
    assert res["bcl"].replaced and io.open(maps / "bcl.json", encoding="utf-8").read() == before


def test_run_apply_override_only_locale_is_not_rewritten(tmp_path):
    """Overrides alone change nothing -> the map file must not be touched (no _meta-only diff)."""
    ex = tmp_path / "extract"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "ceb.json", {"item:Q1": "bago"})
    _write(maps / "ceb.json", {"_meta": {}, "item:Q1": "luma"})
    before = io.open(maps / "ceb.json", encoding="utf-8").read()
    ov = {"item:Q1": {"keep": "luma", "reason": "kept"}}
    res, _gate = run("F1", str(ex), str(maps), ov, apply=True, all_keys=None, date="2026-08-26")
    assert res["ceb"].overridden == [("item:Q1", "luma", "bago")]
    assert io.open(maps / "ceb.json", encoding="utf-8").read() == before


def _run_main(monkeypatch, argv):
    import apply_aug21
    monkeypatch.setattr(sys, "argv", ["apply_aug21.py"] + argv)
    apply_aug21.main()


def test_main_extract_without_only_is_an_error(tmp_path, monkeypatch, capsys):
    """--extract names ONE instrument's dir; without --only it must fail loudly,
    never silently fall back to the default out-aug21/<inst>/ extract."""
    with pytest.raises(SystemExit) as ei:
        _run_main(monkeypatch, ["--extract", str(tmp_path / "nowhere"),
                                "--report", str(tmp_path / "diff.json")])
    assert ei.value.code == 2
    assert "--extract requires --only" in capsys.readouterr().err


def test_main_extract_with_only_is_honoured(tmp_path, monkeypatch, capsys):
    missing = tmp_path / "supplied-extract"
    _run_main(monkeypatch, ["--only", "F1", "--extract", str(missing),
                            "--report", str(tmp_path / "diff.json")])
    out = capsys.readouterr().out
    assert str(missing) in out and "no extract dir" in out


from apply_aug21 import resolve_exclusion_id, seed_candidates, MergeResult  # noqa: E402


def _vs(name, labels):
    return {"name": name, "labels": [{"text": name}],
            "values": [{"labels": [{"text": t}], "pairs": [{"value": str(i + 1)}]} for i, t in enumerate(labels)]}


SRC = {"name": "T", "levels": [{"name": "L", "ids": {"items": []}, "records": [{"name": "R", "items": [
    {"name": "Q140_WHY", "labels": [{"text": "140. Why?"}], "valueSets": [_vs("Q140_WHY_VS1", ["A", "B", "C"])]},
    # Q47: FOUR value-set-bearing items under one qnum (F3 Q47_* pattern)
    {"name": "Q47_PHYSICIAN_CHECKUP", "labels": [{"text": "47a"}], "valueSets": [_vs("Q47_PHYSICIAN_CHECKUP_VS1", ["Yes", "No"])]},
    {"name": "Q47_HOSPITAL_CONF", "labels": [{"text": "47b"}], "valueSets": [_vs("Q47_HOSPITAL_CONF_VS1", ["Yes", "No"])]},
    # Q96: checkbox + roster pair — different option lists, English disambiguates
    {"name": "Q96_SOURCES", "labels": [{"text": "96"}], "valueSets": [_vs("Q96_SOURCES_VS1", ["Out-of-pocket", "Donation"])]},
    {"name": "Q96_PAY_LINE", "labels": [{"text": "96 row"}]},
    {"name": "Q96_PAY_SRC", "labels": [{"text": "96 src"}], "valueSets": [_vs("Q96_PAY_SRC_VS1", ["Out-of-pocket", "Donation", "In kind"])]},
]}]}]}


def test_resolve_exclusion_id_maps_qnum_index_to_val_key():
    # idx indexes the OFFICIAL ENGLISH options, not the dictionary value-set position directly —
    # resolution goes through a label search, so the official English must be supplied.
    official = {"F1": {"140": {"EN": {"options": ["A", "B", "C"]}}}}
    assert resolve_exclusion_id(SRC, "F1|BIS|140|2", official) == ("val:Q140_WHY_VS1:3", "ok")
    assert resolve_exclusion_id(SRC, "F1|BIS|999|0", official) == (None, "absent")          # qnum absent from src
    assert resolve_exclusion_id(SRC, "F1|BIS|140|7", official) == (None, "index-out-of-range")  # idx > len(EN options)
    # no official data at all for this qnum -> can't validate the index against English
    assert resolve_exclusion_id(SRC, "F1|BIS|140|2") == (None, "index-out-of-range")
    assert resolve_exclusion_id(SRC, "F1|BIS|140|2", {}) == (None, "index-out-of-range")


def test_resolve_exclusion_id_ambiguous_reports_count_and_english_disambiguates():
    # "Yes" (option[0]) appears in BOTH Q47_* value sets -> genuinely ambiguous (a real search,
    # not just "more than one item shares the qnum prefix" as the old position-based code did).
    official_47 = {"F3": {"47": {"EN": {"options": ["Yes", "No", "Maybe"]}}}}
    assert resolve_exclusion_id(SRC, "F3|HIL|47|0", official_47) == (None, "ambiguous:2")
    # "Maybe" (option[2]) is in official English but appears in NEITHER Q47_* value set ->
    # the extract's own English text doesn't match anything on the ground -> en-mismatch, not 'ok'.
    assert resolve_exclusion_id(SRC, "F3|HIL|47|2", official_47) == (None, "en-mismatch")
    # official English option[2] == "In kind" matches ONLY Q96_PAY_SRC_VS1 -> resolved
    official = {"F3": {"96": {"EN": {"options": ["Out-of-pocket", "Donation", "In kind"]}}}}
    assert resolve_exclusion_id(SRC, "F3|HIL|96|2", official) == ("val:Q96_PAY_SRC_VS1:3", "ok")
    # option[0] "Out-of-pocket" is in BOTH value sets -> still ambiguous
    assert resolve_exclusion_id(SRC, "F3|HIL|96|0", official) == (None, "ambiguous:2")


def test_resolve_exclusion_id_single_hit_transposed_order_no_longer_silently_wrong():
    """Regression for the review finding: a SINGLE Q<qnum>_* value-set item used to be trusted
    positionally with no English check at all. Real data has this item's value-set order
    transposed relative to the official English option order (F4|FIL|196 vs F4|BIS|196) — the
    fix must resolve by label so the position mismatch can never silently pick the wrong key."""
    transposed_src = {"levels": [{"records": [{"items": [
        {"name": "Q196_FOREGONE", "labels": [{"text": "196"}],
         "valueSets": [_vs("Q196_FOREGONE_VS1", ["We do not forego care", "Other (please specify)"])]},
    ]}]}]}
    official = {"F4": {"196": {"EN": {"options": ["Other (please specify)", "We do not forego care"]}}}}
    # official idx 0 = "Other (please specify)" -> lives at dictionary POSITION 1 (transposed)
    assert resolve_exclusion_id(transposed_src, "F4|FIL|196|0", official) == \
        ("val:Q196_FOREGONE_VS1:2", "ok")
    # official idx 1 = "We do not forego care" -> lives at dictionary POSITION 0
    assert resolve_exclusion_id(transposed_src, "F4|FIL|196|1", official) == \
        ("val:Q196_FOREGONE_VS1:1", "ok")
    # a single hit whose English text doesn't appear in the value set at all -> en-mismatch,
    # never a blind 'ok' (covers the nEN=1-vs-nVS=6 non-option-string case from the finding)
    mismatch_official = {"F4": {"196": {"EN": {"options": ["Not on the list"]}}}}
    assert resolve_exclusion_id(transposed_src, "F4|FIL|196|0", mismatch_official) == (None, "en-mismatch")


def test_seed_candidates_only_reports_reintroduced_keys_and_warns_unresolved(tmp_path, capsys):
    findings = tmp_path / "f.json"
    findings.write_text(json.dumps([
        {"instrument": "F1", "locale": "BIS", "reason": "IS_OTHER_EN",
         "key": "item:Q140_WHY", "en": "140. Why?", "value": "Why?"},
        {"instrument": "F1", "locale": "BIS", "reason": "DOUBLED",
         "key": "item:Q7_X", "en": "", "value": "a a"}]), encoding="utf-8")
    r = MergeResult()
    r.replaced = [("item:Q140_WHY", "Ngano?", "Why?"), ("val:Q140_WHY_VS1:3", "good", "bad")]
    # official English needed for BOTH exclusion ids now that idx is resolved by label, not position:
    # 140|2 -> "C" (uniquely matches Q140_WHY_VS1); 47|1 -> "No" (matches both Q47_* -> ambiguous)
    official = {"F1": {"140": {"EN": {"options": ["A", "B", "C"]}},
                       "47": {"EN": {"options": ["Yes", "No"]}}}}
    rows = seed_candidates("F1", str(findings), {"bis": r}, src=SRC,
                           exclusions={"F1|BIS|140|2": {"test": "contamination", "why": "stranded word"},
                                       "F1|BIS|47|1": {"test": "offset", "why": "row shift"}},
                           official=official)
    keys = {(x["locale"], x["key"]) for x in rows}
    assert keys == {("bis", "item:Q140_WHY"), ("bis", "val:Q140_WHY_VS1:3")}   # Q7_X not replaced -> absent
    rec = [x for x in rows if x["key"] == "val:Q140_WHY_VS1:3"][0]
    assert rec["keep"] == "good" and "recovery_exclusions" in rec["reason"]
    out = capsys.readouterr().out
    assert '"val:Q140_WHY_VS1:3"' in out and '"keep": "good"' in out
    assert "WARN unresolved exclusion F1|BIS|47|1: ambiguous:2" in out


from apply_aug21 import compare_findings  # noqa: E402


def test_stamped_map_still_loads_through_apply_translations_contract(tmp_path):
    """apply_translations pops _meta and rejects any key without ':' — the stamp must not add one."""
    maps = tmp_path / "maps"; maps.mkdir()
    ex = tmp_path / "ex"; ex.mkdir()
    _write(ex / "ilo.json", {"item:Q1": "bago"})
    _write(maps / "ilo.json", {"item:Q1": "daan"})           # no _meta at all
    run("F4", str(ex), str(maps), {}, apply=True, all_keys=None, date="2026-08-26")
    m = json.loads(io.open(maps / "ilo.json", encoding="utf-8").read(), object_pairs_hook=OrderedDict)
    assert list(m)[0] == "_meta"                                # stamp created + moved to the front
    m.pop("_meta", None)
    assert [k for k in m if ":" not in k] == []                 # nothing legacy-shaped left behind


def test_compare_findings_per_reason_delta(tmp_path, capsys):
    pre = tmp_path / "pre.json"; post = tmp_path / "post.json"
    row = lambda reason, key: {"instrument": "F1", "locale": "FIL", "reason": reason, "key": key, "value": "v"}
    pre.write_text(json.dumps([row("WRONG_Q_CLEARED", "item:A"), row("WRONG_Q_CLEARED", "item:B"),
                               row("DOUBLED", "item:C")]), encoding="utf-8")
    post.write_text(json.dumps([row("WRONG_Q_CLEARED", "item:A"), row("DOUBLED", "item:C")]), encoding="utf-8")
    assert compare_findings(str(pre), str(post)) is True        # shrank + equal -> ok
    post.write_text(json.dumps([row("DOUBLED", "item:C"), row("SELF_ECHO", "item:D")]), encoding="utf-8")
    assert compare_findings(str(pre), str(post)) is False       # SELF_ECHO 0 -> 1 grew
    out = capsys.readouterr().out
    assert "SELF_ECHO" in out and "GREW" in out and "item:D" in out


def test_main_maps_dir_without_only_is_an_error(tmp_path, monkeypatch, capsys):
    """--maps-dir names ONE instrument's translations dir (the rehearsal copy); without
    --only it must fail loudly rather than aim one instrument's copy at every instrument."""
    with pytest.raises(SystemExit) as ei:
        _run_main(monkeypatch, ["--maps-dir", str(tmp_path),
                                "--report", str(tmp_path / "diff.json")])
    assert ei.value.code == 2
    assert "--maps-dir requires --only" in capsys.readouterr().err


@pytest.fixture
def live_f1_fil_restored():
    """Belt-and-braces guard: no test may leave the TRACKED F1 Tagalog map modified.

    Snapshots the real deliverables/CSPro/F1/translations/fil.json before the test (i.e.
    before the test redirects apply_aug21.CSPRO) and restores its exact bytes afterwards,
    failing loudly if anything wrote to it. A --maps-dir regression must be caught by an
    assertion, never by leaving a mutated source file in the working tree Carl commits."""
    import apply_aug21
    live = os.path.join(apply_aug21.CSPRO, "F1", "translations", "fil.json")
    with io.open(live, "rb") as fh:
        before = fh.read()
    try:
        yield live
    finally:
        with io.open(live, "rb") as fh:
            after = fh.read()
        if after != before:
            with io.open(live, "wb") as fh:
                fh.write(before)
            pytest.fail("the LIVE F1/translations/fil.json was written - restored from snapshot")


def test_main_maps_dir_writes_the_copy_not_the_live_maps(tmp_path, monkeypatch,
                                                        live_f1_fil_restored):
    """Rehearsal contract: --apply --maps-dir writes ONLY under the supplied dir.

    The 'live' side of the assertion is itself disposable: apply_aug21.CSPRO is redirected
    at a throwaway tree holding a fake F1/translations/fil.json, so a --maps-dir regression
    - the precise regression this test exists to catch - corrupts nothing tracked. With
    --extract supplied and neither --unmatched nor --seed, CSPRO is read for exactly two
    things (the default map dir and the built .dcf the Task-48 duplicate-label gate reads
    its English from), so redirecting it exercises the path under test and nothing else.
    `live_f1_fil_restored` additionally guards the real file in case a future code path
    reaches it by some route other than apply_aug21.CSPRO."""
    import apply_aug21
    ex = tmp_path / "ex"; ex.mkdir()
    maps = tmp_path / "copy"; maps.mkdir()
    fake_cspro = tmp_path / "fake-cspro"
    (fake_cspro / "F1" / "translations").mkdir(parents=True)
    _write(fake_cspro / "F1" / "FacilityHeadSurvey.dcf",
           {"name": "F1", "labels": [{"text": "F1"}], "levels": []})
    fake_live = fake_cspro / "F1" / "translations" / "fil.json"
    _write(fake_live, {"_meta": {}, "item:Q1": "LIVE-MUST-NOT-CHANGE"})
    fake_live_before = io.open(str(fake_live), encoding="utf-8", newline="").read()
    monkeypatch.setattr(apply_aug21, "CSPRO", str(fake_cspro))
    _write(ex / "fil.json", {"item:Q1": "bago"})
    _write(maps / "fil.json", {"_meta": {}, "item:Q1": "luma"})
    _run_main(monkeypatch, ["--only", "F1", "--apply", "--extract", str(ex), "--maps-dir", str(maps),
                            "--report", str(tmp_path / "diff.json")])
    assert json.loads(io.open(maps / "fil.json", encoding="utf-8").read())["item:Q1"] == "bago"
    assert io.open(str(fake_live), encoding="utf-8", newline="").read() == fake_live_before


# --------------------------------------------------------------------------------------
# Task 16c (2026-08-26): overrides are consulted BEFORE the "key absent -> write" branch.
# Task 17 attempt 2 blocked on this: 79 of the 249 defective write values were keys the
# map does not hold yet, and merge_locale() reached `r.writes[key] = val` before it ever
# looked at aug21-overrides.json - so there was no lever at all to hold them back.
# `keep: null` now means "never write this key", new or existing; `keep: "<text>"` on a
# key the map does not have means "write THIS text".
# --------------------------------------------------------------------------------------
def test_merge_null_override_on_a_new_key_keeps_it_out_of_writes():
    pairs = {"item:Q2_ROLE": "Ano ang tungkulin mo?"}          # absent from _cur()
    overrides = {"item:Q2_ROLE": {"keep": None, "reason": "extract truncates this span"}}
    r = merge_locale(_cur(), pairs, set(), overrides)
    assert r.writes == OrderedDict()
    assert r.overridden == [("item:Q2_ROLE", None, "Ano ang tungkulin mo?")]
    assert r.override_stale == []


def test_merge_override_keep_text_is_written_for_a_new_key():
    pairs = {"item:Q2_ROLE": "Ano ang tungkulin mo?"}
    overrides = {"item:Q2_ROLE": {"keep": "Oo", "reason": "hand-confirmed on the paper"}}
    r = merge_locale(_cur(), pairs, set(), overrides)
    assert r.writes == OrderedDict([("item:Q2_ROLE", "Oo")])
    assert r.overridden == [("item:Q2_ROLE", None, "Ano ang tungkulin mo?")]


def test_merge_null_override_on_an_existing_key_never_replaces():
    pairs = {"val:Q5_SEX_VS1:2": "Babae"}                      # differs -> would REPLACE
    overrides = {"val:Q5_SEX_VS1:2": {"keep": None, "reason": "never write this key"}}
    r = merge_locale(_cur(), pairs, set(), overrides)
    assert r.writes == OrderedDict() and r.replaced == []
    assert r.overridden == [("val:Q5_SEX_VS1:2", "Lalaki", "Babae")]
    assert r.override_stale == []          # `keep: null` names no text, so it cannot drift


def test_validate_overrides_accepts_null_keep_on_cspro_keys():
    data = {"F1": {"item:Q12_PUBLIC_HEALTH_UNIT": {
        "keep": None, "reason": "Aug-21 extract truncates this span - never write it"}}}
    assert validate_overrides(data) == []
    # a non-string, non-null keep is still a schema error
    assert validate_overrides({"F1": {"item:Q1_X": {"keep": 5, "reason": "n"}}})
    # ... and an empty string still is, outside note:/icf:
    assert validate_overrides({"F1": {"item:Q1_X": {"keep": "  ", "reason": "n"}}})


# --------------------------------------------------------------------------------------
# Task 16c fix round 1 (2026-08-26)
# (a) `keep` must be PRESENT: allowing null must not make a missing/misspelled field valid,
#     or a typo in a hand-authored Task 17 row would silently suppress an import.
# (b) overrides are consulted BEFORE the flagged check, so a `keep: "<text>"` override is
#     how a reviewer ACCEPTS a flagged span (the plan: never by hand-copy).
# --------------------------------------------------------------------------------------
def test_validate_overrides_requires_the_keep_field_to_be_present():
    errs = validate_overrides({"F1": {"item:Q1_X": {"reason": "typo, forgot keep"}}})
    assert any("keep" in e for e in errs), errs
    errs = validate_overrides({"F1": {"item:Q1_X": {"keepp": "Oo", "reason": "misspelled"}}})
    assert any("keep" in e for e in errs), errs
    # the reason check still runs on such an entry
    assert validate_overrides({"F1": {"item:Q1_X": {"keepp": "Oo"}}})
    # F2's locale-nested block has the same requirement
    errs = validate_overrides({"F2": {"fil": {"Yes": {"reason": "forgot keep"}}}})
    assert any("keep" in e for e in errs), errs
    # ... and an explicit null is still accepted on both sides
    assert validate_overrides({"F1": {"item:Q1_X": {"keep": None, "reason": "never write"}}}) == []
    assert validate_overrides({"F2": {"fil": {"Yes": {"keep": None, "reason": "never write"}}}}) == []


def test_merge_override_keep_text_accepts_a_flagged_key_not_in_the_clean_pairs():
    """<loc>.json and <loc>_flagged.json are disjoint, so a flagged key reaches merge_locale
    only through `flagged_keys`. An override naming text must still write it."""
    overrides = {"item:Q7_FLAGGED": {"keep": "Ano ang tungkulin mo?",
                                     "reason": "reviewer accepted the flagged span"}}
    r = merge_locale(_cur(), {}, {"item:Q7_FLAGGED"}, overrides)
    assert r.writes == OrderedDict([("item:Q7_FLAGGED", "Ano ang tungkulin mo?")])
    assert r.overridden == [("item:Q7_FLAGGED", None, None)]
    assert r.flagged_skipped == 0


def test_merge_null_override_on_a_flagged_key_still_never_writes():
    overrides = {"item:Q7_FLAGGED": {"keep": None, "reason": "defective span, never write"}}
    r = merge_locale(_cur(), {}, {"item:Q7_FLAGGED"}, overrides)
    assert r.writes == OrderedDict() and r.overridden == []
    assert r.flagged_skipped == 1


def test_merge_flagged_key_without_an_override_is_still_skipped():
    r = merge_locale(_cur(), {}, {"item:Q7_FLAGGED"}, {})
    assert r.writes == OrderedDict() and r.flagged_skipped == 1


def test_merge_override_keep_text_equal_to_the_map_counts_same_not_write():
    overrides = {"item:Q9_OLD": {"keep": "luma", "reason": "accepted, already in the map"}}
    r = merge_locale(_cur(), {}, {"item:Q9_OLD"}, overrides)
    assert r.writes == OrderedDict() and r.already_same == 1
    assert r.overridden == [("item:Q9_OLD", "luma", None)]


def test_merge_override_keep_text_wins_over_a_flagged_key_present_in_pairs():
    """Defensive: if a future extractor ever emitted a key in BOTH files, the in-loop
    branch must behave the same way as the tail."""
    pairs = {"item:Q7_FLAGGED": "bleed text"}
    overrides = {"item:Q7_FLAGGED": {"keep": "Ano ang tungkulin mo?", "reason": "accepted"}}
    r = merge_locale(_cur(), pairs, {"item:Q7_FLAGGED"}, overrides)
    assert r.writes == OrderedDict([("item:Q7_FLAGGED", "Ano ang tungkulin mo?")])
    assert r.overridden == [("item:Q7_FLAGGED", None, "bleed text")]
    assert r.flagged_skipped == 0


# --------------------------------------------------------------------------------------
# Task 17 fix round 1 (2026-08-26): an override entry may be scoped to a subset of locales.
# The review found the key-scoped-only block unusable for a defect that lives in ONE paper:
# holding the 19 HIL rows of one translator's stutter also suppressed the 95 correct writes
# the same 19 keys carry in the other six maps. `locales: [...]` holds only the named maps.
# --------------------------------------------------------------------------------------
def test_merge_locale_scoped_override_holds_only_the_named_locale():
    pairs = {"item:Q2_ROLE": "may masunod sa masunod"}          # absent from _cur()
    overrides = {"item:Q2_ROLE": {"keep": None, "reason": "HIL paper stutter",
                                  "locales": ["hil"]}}
    held = merge_locale(_cur(), pairs, set(), overrides, loc="hil")
    assert held.writes == OrderedDict() and len(held.overridden) == 1
    for loc in ("fil", "bcl", "bis", "ceb", "war", "ilo"):
        r = merge_locale(_cur(), pairs, set(), overrides, loc=loc)
        assert r.writes == OrderedDict([("item:Q2_ROLE", "may masunod sa masunod")]), loc
        assert r.overridden == [], loc


def test_merge_locale_scoped_override_also_scopes_the_replace_branch():
    pairs = {"item:Q9_OLD": "bago"}                             # present in _cur() as 'luma'
    overrides = {"item:Q9_OLD": {"keep": None, "reason": "ILO SELF_ECHO", "locales": ["ilo"]}}
    held = merge_locale(_cur(), pairs, set(), overrides, loc="ilo")
    assert held.writes == OrderedDict() and held.replaced == []
    other = merge_locale(_cur(), pairs, set(), overrides, loc="fil")
    assert other.writes == OrderedDict([("item:Q9_OLD", "bago")])
    assert other.replaced == [("item:Q9_OLD", "luma", "bago")]


def test_merge_locale_scoped_override_also_scopes_the_flagged_branch():
    overrides = {"item:Q7_FLAGGED": {"keep": "tinanggap", "reason": "accepted span, ceb only",
                                     "locales": ["ceb"]}}
    ceb = merge_locale(_cur(), {}, {"item:Q7_FLAGGED"}, overrides, loc="ceb")
    assert ceb.writes == OrderedDict([("item:Q7_FLAGGED", "tinanggap")])
    war = merge_locale(_cur(), {}, {"item:Q7_FLAGGED"}, overrides, loc="war")
    assert war.writes == OrderedDict() and war.flagged_skipped == 1


def test_merge_override_without_locales_still_governs_every_locale():
    """Every pre-existing override row has no `locales` key; none of them may change meaning."""
    pairs = {"item:Q2_ROLE": "Ano ang tungkulin mo?"}
    overrides = {"item:Q2_ROLE": {"keep": None, "reason": "value-set offset, all seven papers"}}
    for loc in ("fil", "bcl", "bis", "ceb", "war", "hil", "ilo", None):
        r = merge_locale(_cur(), pairs, set(), overrides, loc=loc)
        assert r.writes == OrderedDict() and len(r.overridden) == 1, loc


def test_validate_overrides_accepts_and_checks_the_locales_list():
    assert validate_overrides({"F1": {"item:Q1_NAME": {
        "keep": None, "reason": "hil-only paper stutter", "locales": ["hil"]}}}) == []
    errs = validate_overrides({"F1": {
        "item:Q1_NAME": {"keep": None, "reason": "r", "locales": []},
        "item:Q2_NAME": {"keep": None, "reason": "r", "locales": "hil"},
        "item:Q3_NAME": {"keep": None, "reason": "r", "locales": ["tl"]},
        "item:Q4_NAME": {"keep": None, "reason": "r", "locales": ["hil", "hil"]}}})
    assert any("Q1_NAME" in e and "non-empty list" in e for e in errs)
    assert any("Q2_NAME" in e and "non-empty list" in e for e in errs)
    assert any("Q3_NAME" in e and "not a known locale" in e for e in errs)
    assert any("Q4_NAME" in e and "duplicate" in e for e in errs)


# ---- Task 48: the permanent duplicate-label gate -------------------------------------
# No two codes of ONE value set may carry the same translated label unless their English
# labels are also identical. The extractor now holds the rows it can see (anchor_extract
# `duplicate-label` / `sibling-run`), but the extractor only ever sees ONE side: the F3
# CEB row it shipped collided with a value the map already held, and the F4 WAR rows
# collided across two value sets. This gate judges the map the apply WOULD leave behind,
# which is the only place both sides are visible, and it blocks --apply.

from apply_aug21 import duplicate_label_rows, run  # noqa: E402


_EN = {"val:Q10_CIVIL_STATUS_VS1:2": "Divorced",
       "val:Q10_CIVIL_STATUS_VS1:5": "Common law / Live-in",
       "val:Q88_WHY_VISIT_VS1:99": "Other (specify)",
       "val:Q88_WHY_VISIT_VS1:98": "Other (specify)",
       "val:Q20_OTHER_VS1:1": "Out of pocket",
       "item:Q10_CIVIL_STATUS": "10. What is your civil status?"}


def test_duplicate_label_rows_flags_two_codes_with_different_english():
    rows = duplicate_label_rows(
        {"val:Q10_CIVIL_STATUS_VS1:2": "Diborsyado",
         "val:Q10_CIVIL_STATUS_VS1:5": "Diborsyado"},
        _EN, written=["val:Q10_CIVIL_STATUS_VS1:2"])
    assert len(rows) == 1
    assert rows[0]["value_set"] == "Q10_CIVIL_STATUS_VS1"
    assert rows[0]["codes"] == ["2", "5"]
    assert rows[0]["value"] == "Diborsyado"
    assert rows[0]["written"] == ["val:Q10_CIVIL_STATUS_VS1:2"]


def test_duplicate_label_rows_allows_two_codes_with_the_same_english():
    """The benign alias: `Other (specify)` under two codes MUST read the same."""
    assert duplicate_label_rows(
        {"val:Q88_WHY_VISIT_VS1:99": "Iba pa (tukuyin)",
         "val:Q88_WHY_VISIT_VS1:98": "Iba pa (tukuyin)"}, _EN) == []


def test_duplicate_label_rows_ignores_keys_the_dictionary_no_longer_defines():
    """A map key the .dcf does not define renders nothing on the tablet, so it cannot
    collide with anything. This is what makes the legacy `01`/`1` and `8`/`99` pairs
    benign: the duplicate partner is a stale map row, not a choice."""
    assert duplicate_label_rows(
        {"val:Q10_CIVIL_STATUS_VS1:2": "Diborsyado",
         "val:Q10_CIVIL_STATUS_VS1:02": "Diborsyado"},   # :02 is not in _EN
        _EN, written=["val:Q10_CIVIL_STATUS_VS1:2"]) == []


def test_duplicate_label_rows_is_per_value_set():
    assert duplicate_label_rows(
        {"val:Q10_CIVIL_STATUS_VS1:2": "Gikan sa bulsa",
         "val:Q20_OTHER_VS1:1": "Gikan sa bulsa"}, _EN) == []


def test_duplicate_label_rows_marks_a_set_nothing_is_written_into_as_pre_existing():
    rows = duplicate_label_rows(
        {"val:Q10_CIVIL_STATUS_VS1:2": "Diborsyado",
         "val:Q10_CIVIL_STATUS_VS1:5": "Diborsyado"}, _EN, written=[])
    assert len(rows) == 1 and rows[0]["written"] == []


def _gate_fixture(tmp_path, extract_value):
    extract = tmp_path / "extract"
    maps = tmp_path / "maps"
    extract.mkdir()
    maps.mkdir()
    for loc in ("fil", "bcl", "bis", "ceb", "war", "hil", "ilo"):
        (extract / f"{loc}.json").write_text(
            json.dumps({"val:Q10_CIVIL_STATUS_VS1:2": extract_value}), encoding="utf-8")
        (maps / f"{loc}.json").write_text(
            json.dumps({"val:Q10_CIVIL_STATUS_VS1:2": "Kinasal",
                        "val:Q10_CIVIL_STATUS_VS1:5": "Diborsyado"}, indent=1),
            encoding="utf-8")
    return extract, maps


def test_run_blocks_apply_when_a_written_row_duplicates_a_sibling_label(tmp_path):
    extract, maps = _gate_fixture(tmp_path, "Diborsyado")
    results, gate = run("F3", str(extract), str(maps), {}, True, None, "2026-08-27",
                        english=_EN)
    assert [g for g in gate if g["written"]], gate
    assert len(gate) == 7                       # one per locale
    for loc in ("fil", "ilo"):
        after = json.loads((maps / f"{loc}.json").read_text(encoding="utf-8"))
        assert after["val:Q10_CIVIL_STATUS_VS1:2"] == "Kinasal", "the map was written"
    assert results["fil"].writes                # the merge still says what it WOULD write


def test_run_applies_when_the_gate_is_clean(tmp_path):
    extract, maps = _gate_fixture(tmp_path, "Hiwalay")
    _results, gate = run("F3", str(extract), str(maps), {}, True, None, "2026-08-27",
                         english=_EN)
    assert gate == []
    after = json.loads((maps / "fil.json").read_text(encoding="utf-8"))
    assert after["val:Q10_CIVIL_STATUS_VS1:2"] == "Hiwalay"


# --------------------------------------------------------------------------------------
# Task 48 fix round 1 (review findings 2 + 3): the STRICT gate and an honest exit code.
#
# Finding 2: "only a group this apply writes into is RED" let the wave's own defect class
# through - the shipped F4 war Q128/Q134 collision is a group NO apply writes into, so it
# printed `pre` and permitted the publish. `--fail-on-pre` is the path a publishing wave
# runs; `duplicate_label_accepted.json` is where a human RULES a collision benign, with a
# reason, so strict mode can never be un-runnable.
# Finding 3: a blocked run printed `APPLIED` and, on a dry run, exited 0 - the only signal
# was prose. The last word now follows what was WRITTEN, and any block exits 2.

from apply_aug21 import (accepted_pre_reason, load_accepted_pre,   # noqa: E402
                         print_duplicate_label_gate, CSPRO_INSTRUMENTS, LOCALES)

_VS = "Q128_NBB_UNDERSTAND_VS1"
_RULING = {"F4": {("war", _VS): (frozenset({"03", "05"}), "codes 03/05 are the same choice")}}


def _pre_row(codes=("03", "05"), written=()):
    return {"locale": "war", "value_set": _VS, "codes": list(codes),
            "keys": [f"val:{_VS}:{c}" for c in codes],
            "value": "Mababayaran han PhilHealth an gastos han pagtambal",
            "english": [f"English label {c}" for c in codes],
            "written": list(written)}


def test_gate_pre_existing_group_is_a_report_by_default(capsys):
    """The default keeps a legacy collision visible without RED-ing every run in the wave."""
    assert print_duplicate_label_gate("F4", [_pre_row()], {}, False) is False
    out = capsys.readouterr().out
    assert "    pre war/" in out and "un-ruled pre-existing set(s)" in out


def test_gate_pre_existing_group_blocks_under_fail_on_pre(capsys):
    """The shipped F4 war Q128 collision: nothing writes into it, and it must still stop
    a publish."""
    assert print_duplicate_label_gate("F4", [_pre_row()], {}, True) is True
    out = capsys.readouterr().out
    assert "RED-pre" in out and "STRICT: these block too" in out


def test_gate_ruled_pre_existing_group_never_blocks(capsys):
    assert print_duplicate_label_gate("F4", [_pre_row()], _RULING, True) is False
    out = capsys.readouterr().out
    assert "ok-pre" in out and "codes 03/05 are the same choice" in out


def test_gate_ruling_is_scoped_to_its_own_instrument(capsys):
    assert print_duplicate_label_gate("F3", [_pre_row()], _RULING, True) is True


def test_gate_ruling_does_not_cover_a_set_that_grew_a_third_code(capsys):
    """A ruling names the codes it rules. A third colliding code is a NEW defect."""
    assert print_duplicate_label_gate("F4", [_pre_row(codes=("03", "05", "07"))],
                                      _RULING, True) is True


def test_gate_written_row_is_red_even_when_the_set_is_ruled(capsys):
    """A ruling forgives what is already on disk, never what this apply would write."""
    row = _pre_row(written=[f"val:{_VS}:05"])
    assert print_duplicate_label_gate("F4", [row], _RULING, False) is True
    assert "RED war/" in capsys.readouterr().out


def test_accepted_pre_reason_matches_on_locale_value_set_and_codes():
    ruling = _RULING["F4"]
    assert accepted_pre_reason(_pre_row(), ruling)
    assert accepted_pre_reason(_pre_row(codes=("03",)), ruling)          # subset: covered
    assert accepted_pre_reason(_pre_row(codes=("03", "09")), ruling) is None
    other = dict(_pre_row(), locale="ilo")
    assert accepted_pre_reason(other, ruling) is None


def test_load_accepted_pre_absent_file_is_empty(tmp_path):
    assert load_accepted_pre(str(tmp_path / "nope.json")) == {}


def test_load_accepted_pre_reads_scoped_rulings(tmp_path):
    p = tmp_path / "acc.json"
    _write(p, {"_readme": ["ignored"],
               "F4": {"war/Q128_NBB_UNDERSTAND_VS1": {"codes": ["03", "05"],
                                                      "reason": "same choice"}}})
    acc = load_accepted_pre(str(p))
    assert set(acc) == {"F4"}
    assert acc["F4"][("war", "Q128_NBB_UNDERSTAND_VS1")] == (frozenset({"03", "05"}),
                                                             "same choice")


@pytest.mark.parametrize("entry", [
    {"codes": ["03", "05"]},                       # no reason
    {"codes": ["03", "05"], "reason": "  "},       # empty reason
    {"reason": "same choice"},                     # no codes
])
def test_load_accepted_pre_rejects_a_ruling_without_codes_and_a_reason(tmp_path, entry):
    p = tmp_path / "acc.json"
    _write(p, {"F4": {"war/Q128_NBB_UNDERSTAND_VS1": entry}})
    with pytest.raises(ValueError):
        load_accepted_pre(str(p))


def test_load_accepted_pre_rejects_a_scope_that_is_not_locale_slash_value_set(tmp_path):
    p = tmp_path / "acc.json"
    _write(p, {"F4": {"Q128_NBB_UNDERSTAND_VS1": {"codes": ["03"], "reason": "r"}}})
    with pytest.raises(ValueError):
        load_accepted_pre(str(p))


def test_the_shipped_ruling_file_is_valid_and_scoped_to_real_instruments():
    """It ships EMPTY (Task 48 found no benign pre-existing set over a live value set);
    this test is what keeps a future entry honest."""
    acc = load_accepted_pre()
    assert set(acc) <= set(CSPRO_INSTRUMENTS)
    for inst, rows in acc.items():
        for (loc, _vs), (codes, reason) in rows.items():
            assert loc in LOCALES and codes and reason.strip()


def _red_gate_fixture(tmp_path):
    """fil map already holds `Diborsyado` on code 5; the extract puts it on code 2 too."""
    ex = tmp_path / "ex"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "fil.json", {"val:Q10_CIVIL_STATUS_VS1:2": "Diborsyado"})
    _write(maps / "fil.json", {"val:Q10_CIVIL_STATUS_VS1:2": "Kinasal",
                               "val:Q10_CIVIL_STATUS_VS1:5": "Diborsyado"})
    return ex, maps


def test_main_dry_run_exits_2_and_says_BLOCKED_on_a_red_gate(tmp_path, monkeypatch, capsys):
    """Finding 3: a script (Tasks 49/50) reads the exit code, and a human reads the last
    line. Before the fix both said 'fine' on a blocked dry run."""
    import apply_aug21
    monkeypatch.setattr(apply_aug21, "dcf_english", lambda inst: _EN)
    ex, maps = _red_gate_fixture(tmp_path)
    before = io.open(str(maps / "fil.json"), encoding="utf-8", newline="").read()
    with pytest.raises(SystemExit) as ei:
        _run_main(monkeypatch, ["--only", "F3", "--extract", str(ex), "--maps-dir", str(maps),
                                "--report", str(tmp_path / "diff.json")])
    assert ei.value.code == 2
    out = capsys.readouterr().out
    assert "BLOCKED - diff written to" in out
    assert "DRY RUN" not in out and "APPLIED" not in out
    assert io.open(str(maps / "fil.json"), encoding="utf-8", newline="").read() == before


def test_main_apply_exits_2_and_says_BLOCKED_not_APPLIED(tmp_path, monkeypatch, capsys):
    import apply_aug21
    monkeypatch.setattr(apply_aug21, "dcf_english", lambda inst: _EN)
    ex, maps = _red_gate_fixture(tmp_path)
    before = io.open(str(maps / "fil.json"), encoding="utf-8", newline="").read()
    with pytest.raises(SystemExit) as ei:
        _run_main(monkeypatch, ["--only", "F3", "--apply", "--extract", str(ex),
                                "--maps-dir", str(maps), "--report", str(tmp_path / "diff.json")])
    assert ei.value.code == 2
    out = capsys.readouterr().out
    assert "BLOCKED - diff written to" in out and "APPLIED" not in out
    assert io.open(str(maps / "fil.json"), encoding="utf-8", newline="").read() == before


def test_main_fail_on_pre_blocks_a_collision_this_apply_does_not_touch(tmp_path, monkeypatch,
                                                                      capsys):
    """The finding, end to end: the apply writes an unrelated key, the map already carries
    a duplicate pair, the default run is GREEN and the strict run is not."""
    import apply_aug21
    monkeypatch.setattr(apply_aug21, "dcf_english", lambda inst: _EN)
    ex = tmp_path / "ex"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "fil.json", {"item:Q10_CIVIL_STATUS": "Ano ang katayuan mo sa buhay?"})
    _write(maps / "fil.json", {"val:Q10_CIVIL_STATUS_VS1:2": "Diborsyado",
                               "val:Q10_CIVIL_STATUS_VS1:5": "Diborsyado"})
    argv = ["--only", "F3", "--extract", str(ex), "--maps-dir", str(maps),
            "--report", str(tmp_path / "diff.json")]
    _run_main(monkeypatch, argv)                                   # default: reports only
    assert "DRY RUN - diff written to" in capsys.readouterr().out
    with pytest.raises(SystemExit) as ei:
        _run_main(monkeypatch, argv + ["--fail-on-pre"])
    assert ei.value.code == 2
    assert "RED-pre" in capsys.readouterr().out


def test_main_clean_gate_still_applies_and_exits_0(tmp_path, monkeypatch, capsys):
    import apply_aug21
    monkeypatch.setattr(apply_aug21, "dcf_english", lambda inst: _EN)
    ex = tmp_path / "ex"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "fil.json", {"val:Q10_CIVIL_STATUS_VS1:2": "Hiwalay"})
    _write(maps / "fil.json", {"val:Q10_CIVIL_STATUS_VS1:2": "Kinasal",
                               "val:Q10_CIVIL_STATUS_VS1:5": "Diborsyado"})
    _run_main(monkeypatch, ["--only", "F3", "--apply", "--fail-on-pre", "--extract", str(ex),
                            "--maps-dir", str(maps), "--report", str(tmp_path / "diff.json")])
    assert "APPLIED - diff written to" in capsys.readouterr().out
    after = json.loads(io.open(str(maps / "fil.json"), encoding="utf-8").read())
    assert after["val:Q10_CIVIL_STATUS_VS1:2"] == "Hiwalay"


# --------------------------------------------------------------------------------------
# Task 49: the `remove: true` override.
#
# Task 48 proved the extractor fix cannot repair a row that is already wrong on disk: a
# flagged row is simply not written, so the map keeps its pre-wave value - and for the F4
# families of task-48-report.md sec-7.2 that value is a truncated fragment or the same
# neighbour's translation with a stray legend digit. The paper carries no distinct
# translation for those codes, so the only honest outcome is to leave the row
# UNTRANSLATED and let the English label render. `keep: null` cannot do it (it only
# declines to write); nothing in the merge could DELETE a key. `remove: true` can, is
# locale-scopable, is counted in the dry-run report, and is replayable - a second run
# finds nothing left to remove.

def test_validate_overrides_accepts_a_remove_entry_without_a_keep():
    data = {"F4": {"val:Q128_NBB_UNDERSTAND_VS1:05": {
        "remove": True, "locales": ["war"],
        "reason": "task-48-report.md sec-7.2: no distinct Waray candidate; English renders"}}}
    assert validate_overrides(data) == []


def test_validate_overrides_rejects_a_remove_that_is_not_true():
    for bad in (False, "yes", 1, None):
        errs = validate_overrides({"F4": {"val:Q1_X_VS1:05": {"remove": bad, "reason": "r"}}})
        assert any("'remove' must be true" in e for e in errs), bad


def test_validate_overrides_rejects_a_remove_entry_that_also_names_keep_text():
    """remove + keep text is a contradiction: one deletes the row, the other writes it."""
    errs = validate_overrides({"F4": {"val:Q1_X_VS1:05": {
        "remove": True, "keep": "Mababayaran han PhilHealth", "reason": "r"}}})
    assert any("cannot carry both" in e for e in errs)


def test_validate_overrides_allows_remove_beside_an_explicit_null_keep():
    """`keep: null` alongside remove says the same thing twice; harmless, so accepted."""
    assert validate_overrides({"F4": {"val:Q1_X_VS1:05": {
        "remove": True, "keep": None, "reason": "r"}}}) == []


def test_validate_overrides_still_requires_a_reason_on_a_remove_entry():
    errs = validate_overrides({"F4": {"val:Q1_X_VS1:05": {"remove": True}}})
    assert any("reason" in e for e in errs)
    assert not any("must name 'keep'" in e for e in errs)   # remove replaces that duty


def test_validate_overrides_validates_the_locales_list_of_a_remove_entry():
    errs = validate_overrides({"F4": {"val:Q1_X_VS1:05": {
        "remove": True, "locales": ["klingon"], "reason": "r"}}})
    assert any("not a known locale" in e for e in errs)


def test_validate_overrides_accepts_a_remove_entry_in_the_f2_block():
    """Task 51 fix round 1: apply-paper-translations.py grew the same removal path, so the
    field is no longer a silent no-op in F2. The F2 block is locale-NESTED, so a remove entry
    there is per-locale by construction - it deletes the key from one map and leaves the other
    six alone (--retire, the only deletion F2 had before, hits all seven)."""
    assert validate_overrides({"F2": {"fil": {"Sex": {
        "remove": True, "reason": "the paper prints one string against both rows"}}}}) == []


def test_validate_overrides_rejects_an_f2_remove_that_is_not_true():
    for bad in (False, "yes", 1, None):
        errs = validate_overrides({"F2": {"fil": {"Sex": {"remove": bad, "reason": "r"}}}})
        assert any("'remove' must be true" in e for e in errs), bad


def test_validate_overrides_rejects_an_f2_remove_entry_that_also_names_keep_text():
    errs = validate_overrides({"F2": {"fil": {"Sex": {
        "remove": True, "keep": "Kasarian", "reason": "r"}}}})
    assert any("cannot carry both" in e for e in errs)


def test_validate_overrides_f2_remove_still_needs_a_reason_and_still_frees_keep():
    assert any("reason" in e for e in
               validate_overrides({"F2": {"fil": {"Sex": {"remove": True}}}}))
    assert not any("must name 'keep'" in e for e in
                   validate_overrides({"F2": {"fil": {"Sex": {"remove": True}}}}))
    # ... and an entry that is NOT removing still has to name keep
    assert any("must name 'keep'" in e for e in
               validate_overrides({"F2": {"fil": {"Sex": {"reason": "forgot keep"}}}}))


def test_merge_remove_override_deletes_an_existing_key_and_writes_nothing():
    pairs = {"val:Q5_SEX_VS1:1": "Lalaki"}
    ov = {"val:Q5_SEX_VS1:1": {"remove": True, "reason": "no distinct candidate"}}
    r = merge_locale(_cur(), pairs, set(), ov)
    assert r.removes == ["val:Q5_SEX_VS1:1"]
    assert r.writes == OrderedDict() and r.replaced == []


def test_merge_remove_override_also_removes_a_flagged_key():
    """The confirmed rows ARE flagged (duplicate-label), so removal must reach that branch."""
    ov = {"val:Q5_SEX_VS1:1": {"remove": True, "reason": "no distinct candidate"}}
    r = merge_locale(_cur(), {}, {"val:Q5_SEX_VS1:1"}, ov)
    assert r.removes == ["val:Q5_SEX_VS1:1"] and r.writes == OrderedDict()


def test_merge_remove_override_reaches_a_key_the_extract_never_mentions():
    """A row the paper stopped anchoring is still on the tablet - removal is about the MAP."""
    ov = {"item:Q9_OLD": {"remove": True, "reason": "stale"}}
    r = merge_locale(_cur(), {}, set(), ov)
    assert r.removes == ["item:Q9_OLD"]


def test_merge_remove_override_on_a_key_the_map_does_not_hold_removes_nothing():
    """Replay: after the first apply the key is gone, so the second run must be a no-op."""
    ov = {"val:Q99_ABSENT_VS1:1": {"remove": True, "reason": "already gone"}}
    r = merge_locale(_cur(), {"val:Q99_ABSENT_VS1:1": "x"}, set(), ov)
    assert r.removes == [] and r.writes == OrderedDict()


def test_merge_remove_override_is_locale_scoped():
    ov = {"val:Q5_SEX_VS1:1": {"remove": True, "locales": ["war"], "reason": "one paper"}}
    assert merge_locale(_cur(), {}, set(), ov, loc="war").removes == ["val:Q5_SEX_VS1:1"]
    assert merge_locale(_cur(), {}, set(), ov, loc="fil").removes == []


def test_run_apply_deletes_the_key_from_the_map_and_counts_it_in_meta(tmp_path):
    ex = tmp_path / "ex"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "war.json", {"item:Q2": "bago"})
    _write(maps / "war.json", OrderedDict([("_meta", {"format": "name-scoped-v2"}),
                                           ("val:Q5_SEX_VS1:1", "mali"), ("item:Q9", "z")]))
    ov = {"val:Q5_SEX_VS1:1": {"remove": True, "reason": "no distinct candidate"}}
    res, _gate = run("F1", str(ex), str(maps), ov, apply=True, all_keys=None,
                     date="2026-08-27")
    m = json.loads(io.open(str(maps / "war.json"), encoding="utf-8").read())
    assert "val:Q5_SEX_VS1:1" not in m and m["item:Q9"] == "z" and m["item:Q2"] == "bago"
    assert m["_meta"]["sources"]["aug21"]["n_removed"] == 1
    assert res["war"].removes == ["val:Q5_SEX_VS1:1"]


def test_run_apply_rewrites_a_locale_whose_only_change_is_a_removal(tmp_path):
    """`if not r.writes: continue` used to skip the file - a removal-only locale would
    have reported a deletion it never performed."""
    ex = tmp_path / "ex"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "ilo.json", {"item:Q1": "luma"})              # already_same, no write
    _write(maps / "ilo.json", OrderedDict([("_meta", {}), ("item:Q1", "luma"),
                                           ("val:Q5_SEX_VS1:1", "mali")]))
    ov = {"val:Q5_SEX_VS1:1": {"remove": True, "reason": "no distinct candidate"}}
    run("F1", str(ex), str(maps), ov, apply=True, all_keys=None, date="2026-08-27")
    m = json.loads(io.open(str(maps / "ilo.json"), encoding="utf-8").read())
    assert "val:Q5_SEX_VS1:1" not in m


def test_run_dry_run_never_removes_anything(tmp_path):
    ex = tmp_path / "ex"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "bcl.json", {"item:Q1": "bago"})
    _write(maps / "bcl.json", {"_meta": {}, "item:Q1": "luma", "val:Q5_SEX_VS1:1": "mali"})
    before = io.open(str(maps / "bcl.json"), encoding="utf-8").read()
    ov = {"val:Q5_SEX_VS1:1": {"remove": True, "reason": "no distinct candidate"}}
    res, _gate = run("F1", str(ex), str(maps), ov, apply=False, all_keys=None,
                     date="2026-08-27")
    assert res["bcl"].removes == ["val:Q5_SEX_VS1:1"]
    assert io.open(str(maps / "bcl.json"), encoding="utf-8").read() == before


def test_run_replay_after_a_removal_writes_nothing_and_removes_nothing(tmp_path):
    ex = tmp_path / "ex"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "war.json", {"item:Q1": "bago"})
    _write(maps / "war.json", {"_meta": {}, "item:Q1": "luma", "val:Q5_SEX_VS1:1": "mali"})
    ov = {"val:Q5_SEX_VS1:1": {"remove": True, "reason": "no distinct candidate"}}
    run("F1", str(ex), str(maps), ov, apply=True, all_keys=None, date="2026-08-27")
    res, _gate = run("F1", str(ex), str(maps), ov, apply=True, all_keys=None,
                     date="2026-08-27")
    assert res["war"].writes == OrderedDict() and res["war"].removes == []


def test_run_gate_judges_the_map_the_removal_leaves_behind(tmp_path):
    """The whole point: deleting one of two colliding codes clears the duplicate-label
    group, because the English label renders and the two choices read differently again."""
    extract, maps = _gate_fixture(tmp_path, "Diborsyado")     # proposal == current -> no write
    ov = {"val:Q10_CIVIL_STATUS_VS1:5": {"remove": True, "reason": "no distinct candidate"}}
    for loc in LOCALES:
        _write(maps / f"{loc}.json", {"val:Q10_CIVIL_STATUS_VS1:2": "Diborsyado",
                                      "val:Q10_CIVIL_STATUS_VS1:5": "Diborsyado"})
    _res, gate = run("F3", str(extract), str(maps), {}, False, None, "2026-08-27",
                     english=_EN)
    assert len(gate) == 7 and all(not g["written"] for g in gate)      # pre-existing
    _res, gate = run("F3", str(extract), str(maps), ov, False, None, "2026-08-27",
                     english=_EN)
    assert gate == []


def test_main_reports_removals_in_the_table_and_the_diff(tmp_path, monkeypatch, capsys):
    import apply_aug21
    monkeypatch.setattr(apply_aug21, "dcf_english", lambda inst: _EN)
    monkeypatch.setattr(apply_aug21, "load_overrides", lambda path=None: {"F3": {
        "val:Q10_CIVIL_STATUS_VS1:5": {"remove": True, "reason": "no distinct candidate"}}})
    ex = tmp_path / "ex"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "fil.json", {"val:Q10_CIVIL_STATUS_VS1:2": "Hiwalay"})
    _write(maps / "fil.json", {"val:Q10_CIVIL_STATUS_VS1:2": "Kinasal",
                               "val:Q10_CIVIL_STATUS_VS1:5": "Diborsyado"})
    report = tmp_path / "diff.json"
    _run_main(monkeypatch, ["--only", "F3", "--apply", "--fail-on-pre", "--extract", str(ex),
                            "--maps-dir", str(maps), "--report", str(report)])
    out = capsys.readouterr().out
    assert "removed" in out and "APPLIED - diff written to" in out
    doc = json.loads(io.open(str(report), encoding="utf-8").read())
    assert doc["F3"]["fil"]["removed"] == ["val:Q10_CIVIL_STATUS_VS1:5"]


# --------------------------------------------------------------------------------------
# 2026-08-27 (#1331/#1332): "force": true writes keep text on an unflagged, present key


def test_merge_force_writes_keep_text_when_extract_and_map_both_differ():
    pairs = {"val:Q5_SEX_VS1:1": "Lalaki"}                     # extract proposes Lalaki
    overrides = {"val:Q5_SEX_VS1:1": {"keep": "Lalake", "force": True,
                                      "reason": "paper prints Lalake; extract and map both wrong"}}
    r = merge_locale(_cur(), pairs, set(), overrides)          # map holds Babae
    assert r.writes == OrderedDict([("val:Q5_SEX_VS1:1", "Lalake")])
    assert r.overridden == [("val:Q5_SEX_VS1:1", "Babae", "Lalaki")]
    assert r.replaced == [] and r.override_stale == []


def test_merge_force_is_replayable_and_reaches_a_key_the_extract_is_silent_about():
    overrides = {"val:Q5_SEX_VS1:1": {"keep": "Babae", "force": True, "reason": "already there"},
                 "val:Q5_SEX_VS1:2": {"keep": "Lalake", "force": True, "reason": "extract silent"}}
    r = merge_locale(_cur(), {}, set(), overrides)
    assert r.writes == OrderedDict([("val:Q5_SEX_VS1:2", "Lalake")])
    assert r.already_same == 1
    assert ("val:Q5_SEX_VS1:2", "Lalaki", None) in r.overridden


def test_validate_overrides_force_needs_keep_text():
    ok = {"F1": {"val:Q5_SEX_VS1:1": {"keep": "Lalake", "force": True, "reason": "r"}}}
    assert validate_overrides(ok) == []
    assert validate_overrides({"F1": {"val:Q5_SEX_VS1:1": {"keep": None, "force": True, "reason": "r"}}})
    assert validate_overrides({"F1": {"val:Q5_SEX_VS1:1": {"remove": True, "force": True, "reason": "r"}}})
    assert validate_overrides({"F1": {"val:Q5_SEX_VS1:1": {"keep": "x", "force": "yes", "reason": "r"}}})


# --------------------------------------------------------------------------------------
# 2026-08-27 (#1335/#1338/#1343): locale-keyed keep - one key, its own text per locale


def test_override_for_locale_keyed_keep_materialises_the_locale_text():
    ov = {"item:Q44_X": {"keep": {"ilo": "ILO text", "ceb": "CEB text"}, "reason": "r"}}
    assert override_for(ov, "item:Q44_X", "ilo")["keep"] == "ILO text"
    assert override_for(ov, "item:Q44_X", "ceb")["keep"] == "CEB text"
    assert override_for(ov, "item:Q44_X", "fil") is None


def test_merge_locale_keyed_keep_writes_each_locale_its_own_text():
    ov = {"item:Q2_ROLE": {"keep": {"ilo": "Ilokano", "ceb": "Sebwano"}, "reason": "r"}}
    r_ilo = merge_locale(_cur(), {}, {"item:Q2_ROLE"}, ov, loc="ilo")
    r_ceb = merge_locale(_cur(), {}, {"item:Q2_ROLE"}, ov, loc="ceb")
    r_fil = merge_locale(_cur(), {}, {"item:Q2_ROLE"}, ov, loc="fil")
    assert r_ilo.writes == OrderedDict([("item:Q2_ROLE", "Ilokano")])
    assert r_ceb.writes == OrderedDict([("item:Q2_ROLE", "Sebwano")])
    assert r_fil.writes == OrderedDict() and r_fil.flagged_skipped == 1


def test_validate_overrides_locale_keyed_keep_rules():
    ok = {"F1": {"item:Q1_X": {"keep": {"ilo": "a", "ceb": "b"}, "reason": "r"}}}
    assert validate_overrides(ok) == []
    assert validate_overrides({"F1": {"item:Q1_X": {"keep": {}, "reason": "r"}}})
    assert validate_overrides({"F1": {"item:Q1_X": {"keep": {"xx": "a"}, "reason": "r"}}})
    assert validate_overrides({"F1": {"item:Q1_X": {"keep": {"ilo": "a"}, "locales": ["ilo"], "reason": "r"}}})
    assert validate_overrides({"F1": {"item:Q1_X": {"keep": {"ilo": " "}, "reason": "r"}}})
