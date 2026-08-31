import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_worklist as ew  # noqa: E402


# --------------------------------------------------------------- fixtures --
# The smallest CSPro-8 dictionary `walk_labeled_nodes()` will walk: one record and one
# item, so the record-vs-item difference between the two English indexes is visible.
_MINI_DICT = {
    "name": "MINI", "labels": [{"text": "Mini", "language": "EN"}],
    "levels": [{"name": "L1", "labels": [{"text": "Level 1", "language": "EN"}],
                "records": [{"name": "A_CONSENT",
                             "labels": [{"text": "A. Consent:", "language": "EN"}],
                             "items": [{"name": "Q1",
                                        "labels": [{"text": "1. Name?", "language": "EN"}],
                                        "valueSets": []}]}]}],
}


def _mini_tree(tmp_path):
    """A two-instrument out-aug21 root plus an overrides file, both minimal."""
    (tmp_path / "F1").mkdir()
    (tmp_path / "F2").mkdir()
    (tmp_path / "F1" / "fil_flagged.json").write_text(json.dumps(
        [{"key": "item:Q1", "en": "1. Name", "tr": "", "flags": ["empty"]},
         {"key": "item:Q2", "en": "2. Sex", "tr": "2. Sex", "flags": ["echo-english"]}]),
        encoding="utf-8")
    (tmp_path / "F2" / "bcl_flagged.json").write_text(json.dumps(
        [{"en": "Administrator", "tr": "Administrator", "flags": ["echo-english"]}]),
        encoding="utf-8")
    ov = tmp_path / "ov.json"
    ov.write_text(json.dumps({"F1": {"val:Q9_VS1:2": {"keep": "Dire", "reason": "swap"}},
                              "F2": {"fil": {"No": {"keep": None, "reason": "junk"}}}}),
                  encoding="utf-8")
    return ov


# ------------------------------------------------------- collect_flagged --
def test_collect_flagged_merges_cspro_f2_and_overrides(tmp_path):
    ov = _mini_tree(tmp_path)
    rows = ew.collect_flagged(tmp_path, ov)
    by = {(r["instrument"], r["locale"], r["key"]): r for r in rows}
    assert by[("F1", "fil", "item:Q1")]["status"] == "flagged"
    assert by[("F1", "fil", "item:Q2")]["status"] == "echo-english"
    assert by[("F2", "bcl", "Administrator")]["status"] == "echo-english"
    assert by[("F1", "*", "val:Q9_VS1:2")]["status"] == "override" and \
        by[("F1", "*", "val:Q9_VS1:2")]["flags"] == "swap"
    assert by[("F2", "fil", "No")]["status"] == "override"


def test_write_csv_roundtrip(tmp_path):
    rows = [{"instrument": "F1", "locale": "fil", "key": "item:Q1", "english": "1. Name",
             "extracted": "", "flags": "empty", "status": "flagged"}]
    p = tmp_path / "w.csv"
    ew.write_csv(rows, p)
    assert p.read_text(encoding="utf-8-sig").splitlines()[0] == \
        "instrument,locale,key,english,extracted,flags,status"


def test_locale_scoped_override_emits_one_row_per_locale(tmp_path):
    """`"locales": [...]` is what keeps a one-paper hold off the other six maps, so the
    worklist must show ASPSI which papers the hold actually covers."""
    (tmp_path / "F1").mkdir()
    ov = tmp_path / "ov.json"
    ov.write_text(json.dumps({"F1": {"val:Q11_VS1:4": {
        "keep": None, "locales": ["hil", "ilo"], "reason": "paper stutter"}}}),
        encoding="utf-8")
    rows = [r for r in ew.collect_flagged(tmp_path, ov) if r["status"] == "override"]
    assert sorted(r["locale"] for r in rows) == ["hil", "ilo"]
    assert all(r["key"] == "val:Q11_VS1:4" for r in rows)


def test_note_and_icf_override_keys_carry_their_own_locale(tmp_path):
    """`note:const:_READ_ONE:FIL` has no `locales` list - the locale is the key suffix."""
    (tmp_path / "F1").mkdir()
    ov = tmp_path / "ov.json"
    ov.write_text(json.dumps({"F1": {"note:const:_READ_ONE:FIL": {"keep": "BASAHIN",
                                                                  "reason": "directive"},
                                     "icf:2:1:WAR": {"keep": "", "reason": "no span"}}}),
                  encoding="utf-8")
    by = {r["key"]: r for r in ew.collect_flagged(tmp_path, ov)}
    assert by["note:const:_READ_ONE:FIL"]["locale"] == "fil"
    assert by["icf:2:1:WAR"]["locale"] == "war"


def test_held_and_english_fallback_overrides_are_labelled_and_sectioned(tmp_path):
    """`keep: null` (never written) and `keep: ""` (renders English) both leave the
    `extracted` cell empty, so the distinction has to live in the reason column."""
    (tmp_path / "F1").mkdir()
    ov = tmp_path / "ov.json"
    ov.write_text(json.dumps({"F1": {"item:A": {"keep": None, "reason": "paper defect"},
                                     "item:B": {"keep": "", "reason": "no span"},
                                     "item:C": {"keep": "Oo", "reason": "accepted"}}}),
                  encoding="utf-8")
    by = {r["key"]: r for r in ew.collect_flagged(tmp_path, ov)}
    assert by["item:A"]["flags"] == "held: paper defect"
    assert by["item:A"]["extracted"] == "" and by["item:A"]["section"] == "held"
    assert by["item:B"]["flags"] == "renders English: no span"
    assert by["item:B"]["section"] == "held"
    assert by["item:C"]["flags"] == "accepted" and by["item:C"]["extracted"] == "Oo"
    assert by["item:C"]["section"] == "accepted"


def test_unmatched_anchors_come_from_the_apply_report(tmp_path):
    (tmp_path / "F1").mkdir()
    ov = tmp_path / "ov.json"
    ov.write_text("{}", encoding="utf-8")
    rep = tmp_path / "diff.json"
    rep.write_text(json.dumps({"F1": {"war": {"unmatched": ["item:REGION"]}}}),
                   encoding="utf-8")
    rows = [r for r in ew.collect_flagged(tmp_path, ov, rep) if r["status"] == "unmatched"]
    assert [(r["instrument"], r["locale"], r["key"]) for r in rows] == \
        [("F1", "war", "item:REGION")]


def test_override_english_is_filled_in_from_the_flagged_rows(tmp_path):
    """The held key's English label is what a translator needs to work the row; the
    flagged files already carry it."""
    (tmp_path / "F1").mkdir()
    (tmp_path / "F1" / "hil_flagged.json").write_text(json.dumps(
        [{"key": "item:Q7", "en": "7. Sex of respondent", "tr": "", "flags": ["empty"]}]),
        encoding="utf-8")
    ov = tmp_path / "ov.json"
    ov.write_text(json.dumps({"F1": {"item:Q7": {"keep": None, "reason": "x"}}}),
                  encoding="utf-8")
    row = [r for r in ew.collect_flagged(tmp_path, ov) if r["status"] == "override"][0]
    assert row["english"] == "7. Sex of respondent"


# ------------------------------------------------------------- residual --
@pytest.mark.parametrize("en,tr,expected", [
    ("Do you agree?", "(Uyon ka?", "unbalanced-paren"),
    ("Daughter", "[Anak na babae", "unbalanced-bracket"),
    ("Support", '" Ang suporta', "stray-leading-glyph"),
    ("Why not?", "Nga-a indi? (", "stray-trailing-glyph"),
    ("Is it enough?", "Igo ba ini", "no-terminal-punct"),
])
def test_residual_defects_names_each_shape(en, tr, expected):
    assert expected in ew.residual_defects(en, tr)


def test_residual_defects_is_silent_on_a_clean_pair():
    assert ew.residual_defects("Do you agree?", "Uyon ka ba (sa proseso)?") == []


def test_residual_defects_reports_the_injected_dangling_tail():
    """The dangling-tail detector is `anchor_extract.truncated_tail`, injected so the
    module stays importable without the extractor."""
    got = ew.residual_defects("Who cares for you?", "Sino ang nag-aalaga sa",
                              tail_check=lambda en, tr: "ends on the proclitic 'sa'")
    assert "dangling-tail (ends on the proclitic 'sa')" in got


def test_dict_english_covers_the_keys_dcf_anchors_filters_out(tmp_path):
    """`dcf_anchors()` keeps only item/vs/val - the kinds it can hunt for on paper - so a
    `record:` key the translation map carries comes back with no English."""
    ae = pytest.importorskip("anchor_extract")
    dcf = tmp_path / "d.dcf"
    dcf.write_text(json.dumps(_MINI_DICT), encoding="utf-8")
    assert "record:A_CONSENT" not in ae.dcf_anchors(str(dcf))
    full = ew.dict_english(dcf)
    assert full["record:A_CONSENT"] == "A. Consent:"
    assert full["item:Q1"] == "1. Name?"


def test_merged_english_takes_the_first_non_empty_source():
    a = {"item:Q1": "from anchors", "item:Q2": ""}
    b = {"item:Q1": "from the dcf", "item:Q2": "from the dcf", "item:Q3": "dcf only"}
    assert ew.merged_english(a, b, None) == {"item:Q1": "from anchors",
                                             "item:Q2": "from the dcf",
                                             "item:Q3": "dcf only"}


def test_residual_rows_labels_and_counts_the_keys_with_no_english():
    missing = set()
    rows = ew._residual_rows("F1", "fil", {"item:STALE": "(Luma"}, {}, set(), None, missing)
    assert missing == {"item:STALE"}
    assert rows[0]["flags"].startswith("unbalanced-paren")
    assert rows[0]["flags"].endswith(",no-english-label")


def test_collect_residual_fills_the_english_gap_and_reports_what_is_left(tmp_path, capsys):
    """Two of the five residual shapes need the English. Before the fallback the whole
    `record:` family was judged with an empty English - silently, and with a blank cell no
    translator can work. The stale key that no index can fill is counted out loud."""
    pytest.importorskip("anchor_extract")
    root = tmp_path / "cspro"
    (root / "F1").mkdir(parents=True)
    (root / "F1" / ew.DCF_FILE["F1"]).write_text(json.dumps(_MINI_DICT), encoding="utf-8")
    (root / "F1" / "translations").mkdir()
    (root / "F1" / "translations" / "fil.json").write_text(json.dumps({
        "record:A_CONSENT": "A. Pagsang-ayon",     # ends the English with ':', the tr does not
        "item:STALE_KEY": "(Luma na ito",          # no English anywhere - a stale map key
    }), encoding="utf-8")
    rows = ew.collect_residual(tmp_path / "out", cspro_root=root, f2_maps=None)
    by = {r["key"]: r for r in rows}
    assert by["record:A_CONSENT"]["english"] == "A. Consent:"
    assert by["record:A_CONSENT"]["flags"] == "no-terminal-punct"
    assert by["item:STALE_KEY"]["flags"].endswith("no-english-label")
    assert "F1: 1 keys had no English label - punctuation/tail checks skipped" \
        in capsys.readouterr().out


def test_collect_residual_skips_rows_already_flagged(tmp_path):
    """Residual rows are the CLEAN pairs - a pair the extractor already flagged is on the
    worklist sheet and must not be double-counted here."""
    out = tmp_path / "out"
    (out / "F2").mkdir(parents=True)
    (out / "F2" / "fil_flagged.json").write_text(json.dumps(
        [{"en": "Already flagged", "tr": "(x", "flags": ["length-ratio"]}]), encoding="utf-8")
    maps = tmp_path / "maps"
    maps.mkdir()
    (maps / "fil.json").write_text(json.dumps({"Already flagged": "(x",
                                               "Clean anchor?": "(Malinis"}), encoding="utf-8")
    rows = ew.collect_residual(out, cspro_root=None, f2_maps=maps)
    assert [(r["locale"], r["key"]) for r in rows] == [("fil", "Clean anchor?")]
    assert rows[0]["status"] == "residual" and rows[0]["section"] == "residual"


# -------------------------------------------------- paper defects / follow-ups --
def test_paper_defects_expand_their_key_selects(tmp_path):
    ov = _mini_tree(tmp_path)
    defects = [{"id": "demo", "instrument": "F1", "locale": "fil",
                "selects": [("keys", ["item:Q1"])],
                "defect": "the paper prints nothing here",
                "action": "reprint the page"}]
    rows = ew.collect_paper_defects(tmp_path, ov, defects=defects)
    assert len(rows) == 1
    r = rows[0]
    assert (r["instrument"], r["locale"], r["key"]) == ("F1", "fil", "item:Q1")
    assert r["status"] == "paper-defect" and r["section"] == "paper-defects"
    assert r["flags"].startswith("demo: the paper prints nothing here")
    assert r["english"] == "1. Name"


def test_paper_defect_with_no_keys_still_emits_its_narrative_row(tmp_path):
    ov = _mini_tree(tmp_path)
    defects = [{"id": "layout", "instrument": "F4", "locale": "fil", "selects": [],
                "defect": "the Tagalog paper is bilingual", "action": "none - by design"}]
    rows = ew.collect_paper_defects(tmp_path, ov, defects=defects)
    assert [(r["key"], r["status"]) for r in rows] == [("layout", "paper-defect")]


def test_paper_defects_flag_select_reads_the_flagged_files(tmp_path):
    ov = _mini_tree(tmp_path)
    defects = [{"id": "echo", "instrument": "F1", "locale": None,
                "selects": [("flag", "echo-english")],
                "defect": "the paper reprints the English", "action": "translate the row"}]
    rows = ew.collect_paper_defects(tmp_path, ov, defects=defects)
    assert [(r["locale"], r["key"]) for r in rows] == [("fil", "item:Q2")]


def test_real_paper_defect_table_starts_with_the_hiligaynon_f1_stutter():
    """Controller ruling: the first paper-side entry is the F1 HIL option-4 stutter."""
    first = ew.PAPER_DEFECTS[0]
    assert first["instrument"] == "F1" and first["locale"] == "hil"
    assert "sa masunod sa masunod" in first["defect"]


def test_follow_ups_are_rows_like_any_other():
    rows = ew.collect_follow_ups()
    assert rows and all(r["status"] == "follow-up" for r in rows)
    assert all(set(ew.COLS) <= set(r) for r in rows)
    assert any("F4 3.2.3" in r["key"] or "F4 3.2.3" in r["english"] for r in rows)


# ----------------------------------------------------------------- xlsx --
def test_write_xlsx_splits_sections_into_sheets(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    rows = [{"instrument": "F1", "locale": "fil", "key": "item:Q1", "english": "1. Name",
             "extracted": "", "flags": "empty", "status": "flagged", "section": "worklist"},
            {"instrument": "F1", "locale": "hil", "key": "val:Q11_VS1:4", "english": "",
             "extracted": "", "flags": "held: stutter", "status": "override",
             "section": "held"}]
    p = tmp_path / "w.xlsx"
    assert ew.write_xlsx(rows, p) is True
    wb = openpyxl.load_workbook(p)
    assert "summary" in wb.sheetnames
    assert "worklist" in wb.sheetnames and "held" in wb.sheetnames
    ws = wb["worklist"]
    assert [c.value for c in ws[1]] == ew.COLS
    assert ws.max_row == 2
    assert wb["held"].max_row == 2
