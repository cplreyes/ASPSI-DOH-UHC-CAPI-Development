import importlib.util, io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "apply_paper_translations", os.path.join(HERE, "apply-paper-translations.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

EN = {"What is your name?", "Yes", "No", "Other (specify)", "Level 3"}


def test_strip_qnum_residue():
    # bare trailing number after any text is residue when the English has no trailing digit
    assert m.strip_qnum_residue("Ilang taon ka na? 5", "How old are you?") == "Ilang taon ka na?"
    assert m.strip_qnum_residue("Tagapangasiwa 6", "Administrator") == "Tagapangasiwa"
    assert m.strip_qnum_residue("Oo 13.1", "Yes") == "Oo"
    assert m.strip_qnum_residue("Tapos na.) 12", "Done.)") == "Tapos na.)"
    # not residue: the English itself ends in a digit
    assert m.strip_qnum_residue("Antas 3", "Level 3") == "Antas 3"


def test_strip_qnum_residue_dot_tail():
    # 'N. NextWord' — the next question's number AND the start of its text swept in
    assert m.strip_qnum_residue("Iba pa, tukuyin 6. Ano ang edad mo?",
                                "Other (specify)") == "Iba pa, tukuyin"
    assert m.strip_qnum_residue("Oo 13. Ilang taon", "Yes") == "Oo"
    # not residue: the English carries the same 'N. Word' tail, so it is content
    assert m.strip_qnum_residue("Piliin ang 1. Oo o 2. Hindi",
                                "Choose 1. Yes or 2. No") == "Piliin ang 1. Oo o 2. Hindi"
    # a decimal question number is still swept by the bare-number rule
    assert m.strip_qnum_residue("Wala 6.1", "No") == "Wala"


def test_decide_rules():
    cur = {"Yes": "Oo", "No": "Hindi"}
    assert m.decide("Nope", "x", cur, EN, {}) == ("unmatched", None)
    assert m.decide("Yes", "yes", cur, EN, {}) == ("skip_same_as_english", None)
    assert m.decide("Yes", "Oo", cur, EN, {}) == ("already_same", None)
    assert m.decide("What is your name?", "Ano ang pangalan mo?", cur, EN, {}) == ("write", "Ano ang pangalan mo?")
    assert m.decide("No", "Wala", cur, EN, {}) == ("replace", "Wala")               # Aug-21 wins
    ov = {"No": {"keep": "Hindi", "reason": "PDF carries the June-5 swap"}}
    assert m.decide("No", "Wala", cur, EN, ov) == ("override", "Hindi")
    # overrides run BEFORE the write branch: keep=null suppresses a fresh write of an absent key
    ov2 = {"What is your name?": {"keep": None, "reason": "mis-anchored span"}}
    assert m.decide("What is your name?", "junk", cur, EN, ov2) == ("override", None)
    # a hand-corrected keep that differs from the current value is applied
    ov3 = {"No": {"keep": "Dili", "reason": "corrected by hand"}}
    assert m.decide("No", "Wala", cur, EN, ov3) == ("override", "Dili")


def test_apply_locale_preserves_order_and_appends():
    cur = {"Yes": "Oo", "No": "Hindi"}
    ext = {"No": "Wala", "What is your name?": "Ano ang pangalan mo?", "Junk": "x", "Yes": "Oo"}
    new, counts, rows = m.apply_locale(ext, cur, EN, {})
    assert list(new) == ["Yes", "No", "What is your name?"]
    assert new["No"] == "Wala"
    assert counts == {"unmatched": 1, "override": 0, "override_seeded": 0,
                      "skip_same_as_english": 0, "already_same": 1, "write": 1,
                      "replace": 1, "retire": 0}
    assert {"en": "No", "action": "replace", "was": "Hindi", "now": "Wala"} in rows


def test_apply_locale_override_null_never_writes_and_keep_changes_map():
    cur = {"No": "Hindi"}
    ext = {"What is your name?": "junk", "No": "Wala"}
    ov = {"What is your name?": {"keep": None, "reason": "mis-anchored"},
          "No": {"keep": "Dili", "reason": "hand-corrected"}}
    new, counts, rows = m.apply_locale(ext, cur, EN, ov)
    assert "What is your name?" not in new
    assert new["No"] == "Dili"
    assert counts["override"] == 2 and counts["write"] == 0 and counts["replace"] == 0
    assert new != cur                       # -> main() saves this map


def test_apply_locale_seeds_overrides_the_extractor_missed():
    """An override for a key the Aug-21 extract never produced is still applied."""
    cur = {"No": "Hindi"}
    ext = {"No": "Wala"}
    ov = {"No": {"keep": "Hindi", "reason": "PDF carries the June-5 swap"},
          "What is your name?": {"keep": "Ano ang pangalan mo?", "reason": "paper cell blank"},
          "Yes": {"keep": None, "reason": "mis-anchored, leave absent"},
          "Not in the build": {"keep": "x", "reason": "typo in the override key"}}
    new, counts, rows = m.apply_locale(ext, cur, EN, ov)
    assert new["What is your name?"] == "Ano ang pangalan mo?"   # seeded
    assert "Yes" not in new                                      # keep:null never writes
    assert "Not in the build" not in new                         # not an English anchor
    assert counts["override"] == 1 and counts["override_seeded"] == 1 and counts["unmatched"] == 1
    assert {"en": "What is your name?", "action": "override_seeded", "was": None,
            "now": "Ano ang pangalan mo?", "reason": "paper cell blank"} in rows


def test_apply_locale_never_writes_an_empty_override():
    """keep:"" validates, but readMap() drops empty values — treat it like keep:null."""
    cur = {"No": "Hindi"}
    new, counts, _rows = m.apply_locale({"No": "Wala"}, cur, EN,
                                        {"No": {"keep": "", "reason": "blank cell"},
                                         "Yes": {"keep": "  ", "reason": "blank cell"}})
    assert dict(new) == cur                       # untouched, and "Yes" was not seeded
    assert counts["override"] == 1 and counts["override_seeded"] == 0


def test_apply_locale_retire_removes_stale_keys():
    cur = {"Yes": "Oo", "No": "Hindi"}
    new, counts, rows = m.apply_locale({}, cur, EN, {}, retire=["No", "Never was here"])
    assert list(new) == ["Yes"]
    assert counts["retire"] == 1
    assert {"en": "No", "action": "retire", "was": "Hindi", "now": None} in rows


def test_save_map_preserves_line_endings(tmp_path):
    p = tmp_path / "fil.json"
    m.save_map(str(p), {"Yes": "Oo", "ñ": "Biñan"}, crlf=True)
    raw = io.open(p, encoding="utf-8", newline="").read()
    assert raw == '{\r\n "Yes": "Oo",\r\n "ñ": "Biñan"\r\n}\r\n'   # indent 1, CRLF, no escaping
    data, crlf = m.load_map(str(p))
    assert dict(data) == {"Yes": "Oo", "ñ": "Biñan"} and crlf is True
    m.save_map(str(p), data, crlf=False)
    assert io.open(p, encoding="utf-8", newline="").read() == '{\n "Yes": "Oo",\n "ñ": "Biñan"\n}\n'
    assert m.load_map(str(p))[1] is False


def _write(path, obj, newline="\n"):
    with io.open(path, "w", encoding="utf-8", newline=newline) as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def test_main_dry_run_then_apply_with_retire(tmp_path, monkeypatch, capsys):
    tdir = tmp_path / "translations"
    extract = tmp_path / "extract"
    tdir.mkdir(); extract.mkdir()
    _write(str(extract / "fil.json"), {"What is your name?": "Ano ang pangalan mo?", "No": "Wala"})
    _write(str(tdir / "fil.json"), {"Yes": "Oo", "No": "Hindi", "Stale key": "luma"}, newline="\r\n")
    eng = tmp_path / "english-strings.json"
    _write(str(eng), {"source": "t", "count": 3,
                      "strings": [{"text": t} for t in ["What is your name?", "Yes", "No"]]})
    ovr = tmp_path / "aug21-overrides.json"
    _write(str(ovr), {"F2": {"fil": {"No": {"keep": "Hindi", "reason": "June-5 swap on the paper"}}}})
    report = tmp_path / "apply-report.json"
    monkeypatch.setattr(m, "TDIR", str(tdir))
    monkeypatch.setattr(m, "ENGLISH_STRINGS", str(eng))
    argv = ["--extract-dir", str(extract), "--overrides", str(ovr), "--report", str(report),
            "--retire", "Stale key"]

    before = io.open(tdir / "fil.json", encoding="utf-8", newline="").read()
    assert m.main(argv) == 0
    assert io.open(tdir / "fil.json", encoding="utf-8", newline="").read() == before   # dry run
    assert "DRY RUN" in capsys.readouterr().out

    assert m.main(argv + ["--apply"]) == 0
    raw = io.open(tdir / "fil.json", encoding="utf-8", newline="").read()
    assert "\r\n" in raw and raw.count("\n") == raw.count("\r\n")   # every line ending is CRLF
    data, _crlf = m.load_map(str(tdir / "fil.json"))
    assert dict(data) == {"Yes": "Oo", "No": "Hindi", "What is your name?": "Ano ang pangalan mo?"}
    rep = json.load(io.open(report, encoding="utf-8"))
    assert rep["mode"] == "APPLY" and rep["retire"] == ["Stale key"]
    assert rep["locales"]["fil"]["retired"] == ["Stale key"]
    assert rep["locales"]["fil"]["counts"]["override"] == 1
    assert rep["locales"]["fil"]["changed"] is True

    # second --apply run is a no-op: nothing left to change
    assert m.main(argv + ["--apply"]) == 0
    rep = json.load(io.open(report, encoding="utf-8"))
    assert rep["locales"]["fil"]["changed"] is False


def test_main_missing_extract_still_retires_and_seeds(tmp_path, monkeypatch, capsys):
    """A locale with no Aug-21 extract must still get --retire + override seeding, and must
    appear in the report marked skipped - otherwise report['retire'] claims a deletion that
    never happened for that locale."""
    tdir = tmp_path / "translations"
    extract = tmp_path / "extract"
    tdir.mkdir(); extract.mkdir()
    _write(str(extract / "fil.json"), {"No": "Wala"})            # only fil has an extract
    _write(str(tdir / "ceb.json"), {"Yes": "Oo", "Stale key": "luma"}, newline="\r\n")
    _write(str(tdir / "fil.json"), {"Yes": "Oo", "Stale key": "luma"}, newline="\r\n")
    eng = tmp_path / "english-strings.json"
    _write(str(eng), {"source": "t", "count": 3,
                      "strings": [{"text": t} for t in ["What is your name?", "Yes", "No"]]})
    ovr = tmp_path / "aug21-overrides.json"
    _write(str(ovr), {"F2": {"ceb": {"No": {"keep": "Dili", "reason": "hand-corrected"}}}})
    report = tmp_path / "apply-report.json"
    monkeypatch.setattr(m, "TDIR", str(tdir))
    monkeypatch.setattr(m, "ENGLISH_STRINGS", str(eng))
    argv = ["--extract-dir", str(extract), "--overrides", str(ovr), "--report", str(report),
            "--retire", "Stale key", "--apply"]

    assert m.main(argv) == 0
    assert "(no extract)" in capsys.readouterr().out
    rep = json.load(io.open(report, encoding="utf-8"))
    for loc in m.LOCALES:                                    # every locale is accounted for
        assert loc in rep["locales"]
    assert "skipped" not in rep["locales"]["fil"]
    assert rep["locales"]["ceb"]["skipped"] == "no extract"
    # the retire ran for the extract-less locale, and the override was seeded there
    assert rep["locales"]["ceb"]["retired"] == ["Stale key"]
    assert rep["locales"]["ceb"]["counts"]["override_seeded"] == 1
    data, _crlf = m.load_map(str(tdir / "ceb.json"))
    assert dict(data) == {"Yes": "Oo", "No": "Dili"}
    # a locale with neither an extract nor a map is reported, unchanged, and writes no file
    assert rep["locales"]["war"]["skipped"] == "no extract"
    assert rep["locales"]["war"]["changed"] is False
    assert not (tdir / "war.json").exists()
