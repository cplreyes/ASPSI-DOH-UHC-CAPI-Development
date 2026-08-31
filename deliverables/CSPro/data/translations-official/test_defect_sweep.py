"""Task 48 fix round 1 (review finding 1): the PERMANENT repo sweep.

`_defect_sweep.py` was a per-task script (`<ws>/task-17`, `<ws>/task-28`) hard-wired to one
instrument and carrying that task's hand-review tables. The plan's Files list names a repo
copy, and Tasks 49/50 are told "the sweep's duplicate-label gate must be CLEAN" - which
needs a sweep that exists, runs for any instrument, and answers with an EXIT CODE.
"""
import io
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import _defect_sweep as DS                                    # noqa: E402

VS = "Q10_CIVIL_STATUS_VS1"
EN = {f"val:{VS}:2": "Divorced",
      f"val:{VS}:5": "Common law / Live-in",
      f"val:{VS}:6": "Annulled",
      "item:Q10_CIVIL_STATUS": "10. What is your civil status?"}


@pytest.fixture
def hermetic(monkeypatch):
    """No .dcf, no generator, no live map: the sweep's inputs are the diff + a maps dir."""
    monkeypatch.setattr(DS, "dcf_english", lambda inst: EN)
    monkeypatch.setattr(DS.AE, "dcf_anchors", lambda path: {})
    monkeypatch.setattr(DS.AE, "english_words", lambda anchors: set())


def _fixture(tmp_path, map_values, writes):
    maps = tmp_path / "maps"
    maps.mkdir()
    io.open(str(maps / "fil.json"), "w", encoding="utf-8").write(
        json.dumps(map_values, ensure_ascii=False))
    diff = tmp_path / "diff.json"
    io.open(str(diff), "w", encoding="utf-8").write(json.dumps(
        {"F3": {"fil": {"writes": writes, "replaced": [], "overridden": [],
                        "unmatched": [], "flagged_skipped": 0, "already_same": 0}}},
        ensure_ascii=False))
    return str(diff), str(maps)


def test_gate_sees_the_map_the_apply_would_leave_behind(tmp_path):
    """The collision the extractor cannot see: the map already holds `Diborsyado` on code
    5 and the apply writes it onto code 2."""
    diff, maps = _fixture(tmp_path, {f"val:{VS}:5": "Diborsyado"},
                          {f"val:{VS}:2": "Diborsyado"})
    doc = json.loads(io.open(diff, encoding="utf-8").read())["F3"]
    gate = DS.duplicate_label_gate("F3", doc, maps, EN)
    assert len(gate) == 1
    assert gate[0]["locale"] == "fil" and gate[0]["codes"] == ["2", "5"]
    assert gate[0]["written"] == [f"val:{VS}:2"]


def test_gate_is_silent_when_the_two_codes_read_differently(tmp_path):
    diff, maps = _fixture(tmp_path, {f"val:{VS}:5": "Diborsyado"},
                          {f"val:{VS}:2": "Hiwalay"})
    doc = json.loads(io.open(diff, encoding="utf-8").read())["F3"]
    assert DS.duplicate_label_gate("F3", doc, maps, EN) == []


def test_main_red_gate_exits_nonzero(tmp_path, hermetic, capsys):
    diff, maps = _fixture(tmp_path, {f"val:{VS}:5": "Diborsyado"},
                          {f"val:{VS}:2": "Diborsyado"})
    assert DS.main(["--inst", "F3", "--diff", diff, "--maps-dir", maps]) == 1
    out = capsys.readouterr().out
    assert "RED fil/" in out and "duplicate-label gate BLOCKS" in out


def test_main_pre_existing_collision_is_a_report_by_default_and_blocks_under_strict(
        tmp_path, hermetic, capsys):
    """The shipped defect class: nothing writes into the pair, so the default run is
    green and only the strict path an instrument publishes on stops it."""
    diff, maps = _fixture(tmp_path,
                          {f"val:{VS}:5": "Diborsyado", f"val:{VS}:6": "Diborsyado"},
                          {"item:Q10_CIVIL_STATUS": "Ano ang katayuan mo sa buhay?"})
    assert DS.main(["--inst", "F3", "--diff", diff, "--maps-dir", maps]) == 0
    assert "    pre fil/" in capsys.readouterr().out
    assert DS.main(["--inst", "F3", "--diff", diff, "--maps-dir", maps,
                    "--fail-on-pre"]) == 1
    assert "RED-pre" in capsys.readouterr().out


def test_main_ruled_pre_existing_collision_passes_the_strict_gate(tmp_path, hermetic,
                                                                 monkeypatch, capsys):
    monkeypatch.setattr(DS, "load_accepted_pre",
                        lambda: {"F3": {("fil", VS): (frozenset({"5", "6"}),
                                                      "one Bikol word for both choices")}})
    diff, maps = _fixture(tmp_path,
                          {f"val:{VS}:5": "Diborsyado", f"val:{VS}:6": "Diborsyado"},
                          {"item:Q10_CIVIL_STATUS": "Ano ang katayuan mo sa buhay?"})
    assert DS.main(["--inst", "F3", "--diff", diff, "--maps-dir", maps,
                    "--fail-on-pre"]) == 0
    assert "ok-pre" in capsys.readouterr().out


def test_main_reports_the_value_families_too(tmp_path, hermetic, capsys):
    """The sweep is still the sweep: `vs-offset` sees a write that equals a SIBLING's
    live value, which is the same defect one step earlier."""
    diff, maps = _fixture(tmp_path, {f"val:{VS}:5": "Diborsyado"},
                          {f"val:{VS}:2": "Diborsyado"})
    DS.main(["--inst", "F3", "--diff", diff, "--maps-dir", maps])
    out = capsys.readouterr().out
    assert "values --apply would write: 1" in out
    assert "vs-offset" in out


def test_main_rejects_an_instrument_the_diff_does_not_carry(tmp_path, hermetic):
    diff, maps = _fixture(tmp_path, {}, {})
    with pytest.raises(SystemExit) as ei:
        DS.main(["--inst", "F4", "--diff", diff, "--maps-dir", maps])
    assert "carries no F4 block" in str(ei.value)


def test_main_requires_an_instrument(tmp_path):
    with pytest.raises(SystemExit):
        DS.main([])


def test_the_task_scoped_hand_review_tables_did_not_come_along():
    """`CLEARED` / `PRECISE` were Task-28's read of ONE write set. Promoting them would
    freeze one wave's hand review into the permanent detector."""
    assert not hasattr(DS, "CLEARED") and not hasattr(DS, "PRECISE")
    assert set(DS.INSTRUMENTS) == {"F1", "F3", "F4"}


def test_gate_honours_the_rows_the_apply_would_REMOVE(tmp_path):
    """Task 49: a `remove: true` override deletes the colliding row, so the sweep - which
    judges the diff, not a live merge - must subtract it before looking for duplicates."""
    diff, maps = _fixture(tmp_path, {f"val:{VS}:5": "Diborsyado", f"val:{VS}:6": "Diborsyado"},
                          {})
    doc = json.loads(io.open(diff, encoding="utf-8").read())["F3"]
    assert len(DS.duplicate_label_gate("F3", doc, maps, EN)) == 1
    doc["fil"]["removed"] = [f"val:{VS}:6"]
    assert DS.duplicate_label_gate("F3", doc, maps, EN) == []
