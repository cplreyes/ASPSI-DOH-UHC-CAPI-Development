import json
from pathlib import Path

import pytest

from rowspec import Row, normalize_text
from paper_tables import parse_extract
from build_tables import (
    derive_qnum,
    load_dcf_items,
    build_options,
    parse_dcf_qsf_apc,
    parse_items_ts,
    parse_pwa,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_normalize_text_folds_quotes_and_prefix():
    assert normalize_text("20.  Kindly state the respondent’s usual commute mode.", strip_qnum=True) == "Kindly state the respondent's usual commute mode."


def test_normalize_text_collapses_whitespace_without_strip():
    assert normalize_text("20.  Kindly   state  it.") == "20. Kindly state it."


def test_row_csv_round_trip():
    r = Row(
        inst="F3",
        qnum="7",
        section="B",
        kind="item",
        stem="Kindly state the usual commute mode.",
        options=[{"code": "1", "label": "Male"}, {"code": "2", "label": "Female"}],
        qtype="single",
        cardinality="single",
    )
    d = r.to_csv_row()
    r2 = Row.from_csv_row(d)
    assert r2 == r


def test_parse_extract_emits_item_rows():
    md = open(FIXTURES / "f3_snippet.md", encoding="utf-8").read()
    rows = [r for r in parse_extract(md, "F3") if r.kind == "item"]
    assert any(r.qnum == "7" and "sex" in r.stem.lower() for r in rows)
    q7 = next(r for r in rows if r.qnum == "7")
    assert {"code": "1", "label": "Male"} in q7.options


def test_parse_extract_emits_section_header():
    md = open(FIXTURES / "f3_snippet.md", encoding="utf-8").read()
    headers = [r for r in parse_extract(md, "F3") if r.kind == "section_header"]
    assert any("household context and chores" in h.stem.lower() for h in headers)


def test_parse_extract_emits_note():
    md = open(FIXTURES / "f3_snippet.md", encoding="utf-8").read()
    notes = [r for r in parse_extract(md, "F3") if r.kind == "note"]
    assert any("note to enumerator" in n.stem.lower() for n in notes)


def test_parse_extract_captures_skip_fragment():
    md = open(FIXTURES / "f3_snippet.md", encoding="utf-8").read()
    items = [r for r in parse_extract(md, "F3") if r.kind == "item"]
    q61 = next(r for r in items if r.qnum == "61")
    assert "q930" in q61.skip.lower()


def test_parse_extract_captures_mark_span_option():
    md = open(FIXTURES / "f3_snippet.md", encoding="utf-8").read()
    items = [r for r in parse_extract(md, "F3") if r.kind == "item"]
    q82 = next(r for r in items if r.qnum == "82")
    assert any(o["label"] == "None" for o in q82.options)


# --- Task 0.3: build_tables.py ---------------------------------------------


def test_derive_qnum_variants():
    assert derive_qnum("Q10_1_STEM") == "10.1"
    assert derive_qnum("Q71A_STEM") == "71a"
    assert derive_qnum("Q1_IS_PATIENT") == "1"
    assert derive_qnum("LANGUAGE_USED") == ""
    # PWA items.ts spells some follow-ups with a literal decimal id --
    # verbatim paper qnum, must NOT collapse to the base number ("13").
    assert derive_qnum("Q13.1") == "13.1"
    assert derive_qnum("Q24.2") == "24.2"


def test_parse_dcf_emits_options():
    items = load_dcf_items(FIXTURES / "mini.dcf")
    item, section = items["Q1_TEST_SELECT"]
    assert build_options(item) == [{"code": "1", "label": "Yes"}]
    assert section == "A Mini Invented Section"


def test_parse_dcf_qsf_apc_builds_row_from_dcf_only():
    # No matching mini.ent.qsf/apc/mgf fixtures -- parse_dcf_qsf_apc must
    # still work off the dcf alone (stem falls back to the dcf label).
    rows = parse_dcf_qsf_apc(FIXTURES, "mini")
    q1 = next(r for r in rows if r.item_name == "Q1_TEST_SELECT")
    assert q1.qnum == "1"
    assert q1.kind == "item"
    assert q1.stem == "Do you like invented tea? (fixture only)"
    assert q1.options == [{"code": "1", "label": "Yes"}]
    assert q1.qtype == "single"


def test_parse_pwa_reads_items_ts():
    text = open(FIXTURES / "mini_items.ts", encoding="utf-8").read()
    rows = parse_items_ts(text, inst="F2")
    q1 = next(r for r in rows if r.item_name == "Q1")
    assert q1.qnum == "1"
    assert q1.stem == "Do you like invented tea? (fixture only)"
    assert {"code": "Yes", "label": "Yes"} in q1.options
    assert {"code": "No", "label": "No"} in q1.options
    assert q1.validation == "required"


# --- Task 0.4: aug17_diff.py -----------------------------------------------

from aug17_diff import diff_instrument, parse_register_rows, build_register_index

REGISTER_HEADER = (
    "# fixture register\n\n"
    "| inst | qnum/item | class | paper says | build does | rationale / ticket |\n"
    "|---|---|---|---|---|---|\n"
)


def _empty_register():
    return build_register_index(parse_register_rows(REGISTER_HEADER))


def test_diff_flags_stem_change():
    paper = [Row(inst="F9", qnum="1", kind="item", stem="Original stem text.",
                 qtype="text", cardinality="single")]
    build = [Row(inst="F9", qnum="1", item_name="Q1", kind="item", stem="Changed stem text.",
                 qtype="text", cardinality="single")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert any(f.category == "STEM_DIFF" for f in findings)
    assert blocking > 0  # unregistered -> would exit 1


def test_registered_divergence_passes():
    paper = [Row(inst="F9", qnum="1", kind="item", stem="Original stem text.",
                 qtype="text", cardinality="single")]
    build = [Row(inst="F9", qnum="1", item_name="Q1", kind="item", stem="Changed stem text.",
                 qtype="text", cardinality="single")]
    reg_text = REGISTER_HEADER + (
        "| F9 | Q1 (test item) | defect-fix | Original stem text. | Changed stem text. | test row |\n"
    )
    register = build_register_index(parse_register_rows(reg_text))
    findings, counts, blocking = diff_instrument("F9", paper, build, register)
    assert blocking == 0
    assert counts["REGISTERED"] >= 1
    stem_diffs = [f for f in findings if f.category == "STEM_DIFF"]
    assert stem_diffs and stem_diffs[0].registered is not None


def test_cardinality_diff():
    paper = [Row(inst="F9", qnum="2", kind="item", stem="Pick one.",
                 options=[{"code": "1", "label": "A"}], qtype="single", cardinality="single")]
    build = [Row(inst="F9", qnum="2", item_name="Q2", kind="item", stem="Pick one.",
                 options=[{"code": "1", "label": "A"}], qtype="multi", cardinality="multi")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert any(f.category == "CARDINALITY_DIFF" for f in findings)


def test_message_diff():
    paper = [Row(inst="F9", qnum="3", kind="item", stem="Enter amount.",
                 qtype="number", cardinality="single", messages="")]
    build = [Row(inst="F9", qnum="3", item_name="Q3", kind="item", stem="Enter amount.",
                 qtype="number", cardinality="single", messages="E: Amount is required.")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert any(f.category == "MESSAGE_DIFF" for f in findings)


def test_disposition_diff():
    paper = [
        Row(inst="F9", kind="section_header", section="FIELD CONTROL", stem="FIELD CONTROL"),
        Row(inst="F9", kind="instruction", section="FIELD CONTROL", stem="aCodes:"),
        Row(inst="F9", kind="instruction", section="FIELD CONTROL", stem="1. Completed"),
        Row(inst="F9", kind="instruction", section="FIELD CONTROL", stem="2. Postponed"),
        Row(inst="F9", kind="instruction", section="FIELD CONTROL", stem="3. Refused"),
        Row(inst="F9", kind="instruction", section="FIELD CONTROL", stem="4. Incomplete"),
        Row(inst="F9", kind="instruction", section="FIELD CONTROL", stem="5. Withdrawn"),
        Row(inst="F9", kind="instruction", section="FIELD CONTROL", stem="6. Ineligible"),
        Row(inst="F9", kind="instruction", section="FIELD CONTROL", stem="Total number of visits:"),
    ]
    build = [
        Row(inst="F9", item_name="ENUM_RESULT_FIRST_VISIT", kind="disposition",
            stem="Result of First Visit",
            options=[
                {"code": "1", "label": "Completed"}, {"code": "2", "label": "Postponed"},
                {"code": "3", "label": "Refused"}, {"code": "4", "label": "Incomplete"},
                {"code": "5", "label": "Replaced"},
            ],
            qtype="single", cardinality="single"),
    ]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    disp = [f for f in findings if f.category == "DISPOSITION_DIFF"]
    assert len(disp) == 1
    assert blocking > 0


def test_pandoc_dash_fold_is_not_a_false_stem_diff():
    # Paper extracts render en/em dashes as pandoc "--"/"---" runs; the
    # build always uses a plain single hyphen (no-em-dash device rule).
    # This is the 3rd sanctioned normalization (paper side only) and must
    # NOT surface as STEM_DIFF.
    paper = [Row(inst="F9", qnum="4", kind="item",
                 stem="Household income --- estimate for the past 12 months.",
                 qtype="number", cardinality="single")]
    build = [Row(inst="F9", qnum="4", item_name="Q4", kind="item",
                 stem="Household income - estimate for the past 12 months.",
                 qtype="number", cardinality="single")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert not any(f.category == "STEM_DIFF" for f in findings)


# --- Fix round 1 (review): drop unsanctioned casefold; content-verify
# structural register matches -------------------------------------------


def test_option_diff_case_only():
    # Case-insensitivity was never a sanctioned normalization. A pure-case
    # option-label mismatch must surface as OPTION_DIFF, not be silently
    # folded away.
    paper = [Row(inst="F9", qnum="5", kind="item", stem="Refuse to answer?",
                 options=[{"code": "1", "label": "Refused to answer"}],
                 qtype="single", cardinality="single")]
    build = [Row(inst="F9", qnum="5", item_name="Q5", kind="item", stem="Refuse to answer?",
                 options=[{"code": "1", "label": "REFUSED TO ANSWER"}],
                 qtype="single", cardinality="single")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert any(f.category == "OPTION_DIFF" for f in findings)


def test_section_diff_case_only():
    paper = [Row(inst="F9", qnum="6", kind="item", stem="Item text.", section="G Section Title",
                 qtype="text", cardinality="single")]
    build = [Row(inst="F9", qnum="6", item_name="Q6", kind="item", stem="Item text.",
                 section="G SECTION TITLE", qtype="text", cardinality="single")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert any(f.category == "SECTION_DIFF" for f in findings)


def test_disposition_register_content_mismatch_is_unregistered():
    # A "FIELD CONTROL" register row exists for this inst, but its
    # canonical code list is stale (doesn't match the currently-computed
    # build code set) -- must NOT auto-pass. Content-blind presence-only
    # matching would wrongly stamp any future disposition regression
    # REGISTERED forever.
    paper = [
        Row(inst="F9", kind="section_header", section="FIELD CONTROL", stem="FIELD CONTROL"),
        Row(inst="F9", kind="instruction", section="FIELD CONTROL", stem="1. Completed"),
        Row(inst="F9", kind="instruction", section="FIELD CONTROL", stem="2. Postponed"),
        Row(inst="F9", kind="instruction", section="FIELD CONTROL", stem="Total number of visits:"),
    ]
    build = [
        Row(inst="F9", item_name="ENUM_RESULT_FIRST_VISIT", kind="disposition",
            stem="Result of First Visit",
            options=[
                {"code": "1", "label": "Completed"}, {"code": "2", "label": "Postponed"},
                {"code": "3", "label": "Replaced"},  # unregistered 3rd code
            ],
            qtype="single", cardinality="single"),
    ]
    reg_text = REGISTER_HEADER + (
        "| F9 | FIELD CONTROL | system-item | 1-Completed / 2-Postponed | "
        "Build ENUM_RESULT (codes: 1=Completed,2=Postponed) | stale canonical list, missing code 3 |\n"
    )
    register = build_register_index(parse_register_rows(reg_text))
    findings, counts, blocking = diff_instrument("F9", paper, build, register)
    disp = [f for f in findings if f.category == "DISPOSITION_DIFF"]
    assert len(disp) == 1
    assert disp[0].registered is None
    assert blocking > 0


def test_order_diff_registration_requires_full_coverage():
    # A register row for "order:G,H" must NOT cover a G-only move -- the
    # register row must name every moved section, not just overlap one.
    paper = [
        Row(inst="F9", qnum="1", kind="item", stem="a", section="A", qtype="text", cardinality="single"),
        Row(inst="F9", qnum="2", kind="item", stem="b", section="B", qtype="text", cardinality="single"),
        Row(inst="F9", qnum="3", kind="item", stem="c", section="C", qtype="text", cardinality="single"),
        Row(inst="F9", qnum="4", kind="item", stem="d", section="D", qtype="text", cardinality="single"),
        Row(inst="F9", qnum="7", kind="item", stem="g", section="G", qtype="text", cardinality="single"),
    ]
    build = [
        Row(inst="F9", qnum="1", item_name="Q1", kind="item", stem="a", section="A", qtype="text", cardinality="single"),
        Row(inst="F9", qnum="7", item_name="Q7", kind="item", stem="g", section="G", qtype="text", cardinality="single"),
        Row(inst="F9", qnum="2", item_name="Q2", kind="item", stem="b", section="B", qtype="text", cardinality="single"),
        Row(inst="F9", qnum="3", item_name="Q3", kind="item", stem="c", section="C", qtype="text", cardinality="single"),
        Row(inst="F9", qnum="4", item_name="Q4", kind="item", stem="d", section="D", qtype="text", cardinality="single"),
    ]
    reg_text = REGISTER_HEADER + (
        "| F9 | order:G,H | capi-adaptation | G/H after primary-care | G/H front-loaded | unrelated bigger move |\n"
    )
    register = build_register_index(parse_register_rows(reg_text))
    findings, counts, blocking = diff_instrument("F9", paper, build, register)
    order_findings = [f for f in findings if f.category == "ORDER_DIFF"]
    assert len(order_findings) == 1
    assert order_findings[0].qnum == "order:G"
    assert order_findings[0].registered is None
    assert blocking > 0


# --- Task 0.6: rejoin_translations.py ---------------------------------------

from rejoin_translations import (
    _commit_write,
    _prepare_cspro_write,
    _prepare_pwa_write,
    compute_stale_from_tables,
    plan_pwa_rekey,
    plan_rejoin,
    plan_stale_drop,
    rebuild_locale_dict,
    require_name_scoped,
    summarize_plan,
    surgical_rejoin_scoped_text,
)


def _load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_scoped_rename_moves_all_key_kinds():
    data = _load_fixture("mini_fil_scoped.json")
    rename_map = {"Q1_LIKES_TEA": "Q1_ENJOYS_TEA"}
    plan = plan_rejoin(data, rename_map, stem_changed_names=set(), stale_val_codes=set())
    moved = dict(plan["moved"])
    assert moved["item:Q1_LIKES_TEA"] == "item:Q1_ENJOYS_TEA"
    assert moved["vs:Q1_LIKES_TEA_VS1"] == "vs:Q1_ENJOYS_TEA_VS1"
    assert moved["val:Q1_LIKES_TEA_VS1:1"] == "val:Q1_ENJOYS_TEA_VS1:1"
    assert moved["val:Q1_LIKES_TEA_VS1:2"] == "val:Q1_ENJOYS_TEA_VS1:2"
    assert not plan["fellback"]

    new_data = rebuild_locale_dict(data, plan)
    assert new_data["item:Q1_ENJOYS_TEA"] == data["item:Q1_LIKES_TEA"]
    assert new_data["vs:Q1_ENJOYS_TEA_VS1"] == data["vs:Q1_LIKES_TEA_VS1"]
    assert new_data["val:Q1_ENJOYS_TEA_VS1:1"] == data["val:Q1_LIKES_TEA_VS1:1"]
    assert new_data["val:Q1_ENJOYS_TEA_VS1:2"] == data["val:Q1_LIKES_TEA_VS1:2"]
    assert new_data["_meta"] == data["_meta"]


def test_reworded_stem_drops_to_fellback():
    data = _load_fixture("mini_fil_scoped.json")
    rename_map = {"Q1_LIKES_TEA": "Q1_ENJOYS_TEA"}
    plan = plan_rejoin(data, rename_map, stem_changed_names={"Q1_LIKES_TEA"}, stale_val_codes=set())
    fellback = dict(plan["fellback"])
    assert fellback["item:Q1_LIKES_TEA"] == "renamed+reworded"
    moved_old_keys = {old for old, _new in plan["moved"]}
    assert "item:Q1_LIKES_TEA" not in moved_old_keys
    # the item's own stem translation drops, but its value set/options still
    # carry -- Decision 2 is scoped to the exact key whose English changed.
    assert "vs:Q1_LIKES_TEA_VS1" in moved_old_keys
    assert "val:Q1_LIKES_TEA_VS1:1" in moved_old_keys


def test_unmapped_scoped_keys_untouched():
    data = _load_fixture("mini_fil_scoped.json")
    rename_map = {"Q1_LIKES_TEA": "Q1_ENJOYS_TEA"}  # Q2_COLOR / MINI_ROSTER absent from the map
    plan = plan_rejoin(data, rename_map, stem_changed_names=set(), stale_val_codes=set())
    assert plan["kept"]["item:Q2_COLOR"] == data["item:Q2_COLOR"]
    assert plan["kept"]["record:MINI_ROSTER"] == data["record:MINI_ROSTER"]
    moved_old_keys = {old for old, _new in plan["moved"]}
    assert "item:Q2_COLOR" not in moved_old_keys
    assert "record:MINI_ROSTER" not in moved_old_keys


def test_pwa_mode_rekeys_english():
    data = {
        "Do you like invented tea? (fixture)": "Gusto mo ba ng tsaa? (fixture)",
        "Yes (fixture)": "Oo (fixture)",
    }
    rekey_map = {"Do you like invented tea? (fixture)": "Do you enjoy invented tea? (fixture)"}
    plan = plan_pwa_rekey(data, rekey_map)
    new_data = rebuild_locale_dict(data, plan)
    assert new_data["Do you enjoy invented tea? (fixture)"] == "Gusto mo ba ng tsaa? (fixture)"
    assert "Do you like invented tea? (fixture)" not in new_data
    assert new_data["Yes (fixture)"] == "Oo (fixture)"  # unmapped -> untouched, verbatim
    assert not plan["fellback"]


def test_legacy_text_key_refused():
    data = _load_fixture("mini_fil_text.json")
    with pytest.raises(ValueError, match="name-scoped"):
        require_name_scoped(data, "fixtures/mini_fil_text.json")


def test_stale_from_tables_drops_reworded():
    paper = [Row(inst="F9", qnum="1", kind="item", stem="Original tea stem (fixture).",
                 options=[{"code": "1", "label": "Yes (fixture)"}, {"code": "2", "label": "No, changed (fixture)"}],
                 qtype="single", cardinality="single")]
    build = [Row(inst="F9", qnum="1", item_name="Q1_LIKES_TEA", kind="item", stem="Changed tea stem (fixture).",
                 options=[{"code": "1", "label": "Yes (fixture)"}, {"code": "2", "label": "No (fixture)"}],
                 qtype="single", cardinality="single")]
    stem_changed, option_changed, new_rows = compute_stale_from_tables("F9", paper, build)
    assert "Q1_LIKES_TEA" in stem_changed
    assert ("Q1_LIKES_TEA", "2") in option_changed
    assert ("Q1_LIKES_TEA", "1") not in option_changed
    assert new_rows == []

    data = _load_fixture("mini_fil_scoped.json")
    plan = plan_stale_drop(data, stem_changed, option_changed)
    fellback = dict(plan["fellback"])
    assert fellback["item:Q1_LIKES_TEA"] == "stale-stem"
    assert fellback["val:Q1_LIKES_TEA_VS1:2"] == "stale-option"
    assert "val:Q1_LIKES_TEA_VS1:1" in plan["kept"]  # code 1 unchanged -> carried


# --- extra coverage (not individually named in the brief, but load-bearing
# for the Wave tasks that will actually run --apply against real files) ----


def test_rename_collision_raises():
    data = {
        "_meta": {"format": "name-scoped-v2"},
        "item:Q1_OLD": "stem A (fixture)",
        "item:Q2_KEEP": "stem B (fixture)",
    }
    # both Q1_OLD and Q2_KEEP would collide onto item:Q2_KEEP after rename
    rename_map = {"Q1_OLD": "Q2_KEEP"}
    with pytest.raises(ValueError, match="collision"):
        plan_rejoin(data, rename_map, stem_changed_names=set(), stale_val_codes=set())


def test_surgical_apply_renames_and_drops_without_reformatting():
    raw_text = (FIXTURES / "mini_fil_scoped.json").read_text(encoding="utf-8")
    data = json.loads(raw_text)
    rename_map = {"Q1_LIKES_TEA": "Q1_ENJOYS_TEA"}
    plan = plan_rejoin(data, rename_map, stem_changed_names=set(), stale_val_codes={("Q1_LIKES_TEA", "2")})
    new_text, applied_moves, applied_drops = surgical_rejoin_scoped_text(raw_text, plan["moved"], plan["fellback"])

    reparsed = json.loads(new_text)  # must still be valid JSON
    assert reparsed["item:Q1_ENJOYS_TEA"] == data["item:Q1_LIKES_TEA"]
    assert "val:Q1_ENJOYS_TEA_VS1:2" not in reparsed  # dropped (stale-option), falls back to English
    assert reparsed["val:Q1_ENJOYS_TEA_VS1:1"] == data["val:Q1_LIKES_TEA_VS1:1"]
    assert reparsed["item:Q2_COLOR"] == data["item:Q2_COLOR"]  # untouched
    assert reparsed["_meta"] == data["_meta"]
    assert set(applied_moves) == {k for k, _ in plan["moved"]}
    assert set(applied_drops) == {k for k, _ in plan["fellback"]}
    # untouched lines are byte-identical: every line not carrying a
    # moved/dropped key must appear verbatim in the new text
    touched = {k for k, _ in plan["moved"]} | {k for k, _ in plan["fellback"]}
    for line in raw_text.splitlines():
        if not any(f'"{k}"' in line for k in touched):
            assert line in new_text


# --- fix round 1 (reviewer): newline discipline + atomicity ----------------
#
# Real MAIN locale files are LF-only. Path.read_text/write_text default to
# universal-newline translation, which on Windows means write_text() alone
# silently turns every "\n" into "\r\n" -- even on lines never touched by
# the surgical edit -- flipping the whole file to CRLF (the documented
# 2026-07-13 F2 incident, recurring). The tests above only ever exercised
# the pure surgical_rejoin_* functions in memory; they never went through
# an actual filesystem write, which is exactly why this escaped review.
# These two tests drive the REAL _prepare_*_write / _commit_write path
# against an on-disk LF-only file via tmp_path.


def test_apply_write_path_preserves_lf_only_line_endings(tmp_path):
    raw_text = (FIXTURES / "mini_fil_scoped.json").read_text(encoding="utf-8", newline="")
    assert "\r" not in raw_text  # fixture itself must be LF-only for this test to mean anything

    target = tmp_path / "fil.json"
    target.write_bytes(raw_text.encode("utf-8"))  # write LF-only bytes verbatim, no translation

    data = json.loads(raw_text)
    rename_map = {"Q1_LIKES_TEA": "Q1_ENJOYS_TEA"}
    plan = plan_rejoin(data, rename_map, stem_changed_names=set(), stale_val_codes={("Q1_LIKES_TEA", "2")})

    new_text = _prepare_cspro_write(target, plan)
    _commit_write(target, new_text)

    written_bytes = target.read_bytes()
    assert b"\r" not in written_bytes  # the fix-round-1 regression: default-newline write_text()
                                        # turned every "\n" into "\r\n" on Windows

    reparsed = json.loads(written_bytes.decode("utf-8"))
    assert reparsed["item:Q1_ENJOYS_TEA"] == data["item:Q1_LIKES_TEA"]
    assert "val:Q1_ENJOYS_TEA_VS1:2" not in reparsed  # dropped (stale-option)
    assert reparsed["val:Q1_ENJOYS_TEA_VS1:1"] == data["val:Q1_LIKES_TEA_VS1:1"]
    assert reparsed["item:Q2_COLOR"] == data["item:Q2_COLOR"]  # untouched
    assert reparsed["_meta"] == data["_meta"]

    # every line not carrying a moved/dropped key is BYTE-identical to the
    # original, including its own line-ending byte(s)
    touched = {k for k, _ in plan["moved"]} | {k for k, _ in plan["fellback"]}
    orig_lines = raw_text.splitlines(keepends=True)
    new_lines_set = set(new_text.splitlines(keepends=True))
    for line in orig_lines:
        if any(f'"{k}"' in line for k in touched):
            continue
        assert line in new_lines_set


def test_pwa_apply_write_path_preserves_lf_only_line_endings(tmp_path):
    raw_text = (
        '{\n'
        ' "Do you like invented tea? (fixture)": "Gusto mo ba ng tsaa? (fixture)",\n'
        ' "Yes (fixture)": "Oo (fixture)"\n'
        '}\n'
    )
    assert "\r" not in raw_text

    target = tmp_path / "fil.json"
    target.write_bytes(raw_text.encode("utf-8"))

    data = json.loads(raw_text)
    rekey_map = {"Do you like invented tea? (fixture)": "Do you enjoy invented tea? (fixture)"}
    plan = plan_pwa_rekey(data, rekey_map)

    new_text = _prepare_pwa_write(target, plan)
    _commit_write(target, new_text)

    written_bytes = target.read_bytes()
    assert b"\r" not in written_bytes

    reparsed = json.loads(written_bytes.decode("utf-8"))
    assert reparsed["Do you enjoy invented tea? (fixture)"] == "Gusto mo ba ng tsaa? (fixture)"
    assert reparsed["Yes (fixture)"] == "Oo (fixture)"  # unmapped -> byte-identical

    touched = {k for k, _ in plan["moved"]}
    orig_lines = raw_text.splitlines(keepends=True)
    new_lines_set = set(new_text.splitlines(keepends=True))
    for line in orig_lines:
        if any(f'"{k}"' in line for k in touched):
            continue
        assert line in new_lines_set


def test_summarize_plan_excludes_meta_and_counts_colon_keys():
    # fix round 1: the old heuristic (startswith item:/vs:/val:/record: OR
    # ":" not in key) counted "_meta" as carried (colon-free) and DROPPED
    # any PWA English-text key containing a literal colon from the count.
    plan = {
        "kept": {
            "_meta": {"format": "name-scoped-v2"},
            "item:Q2_COLOR": "stem (fixture)",
            "Note: please answer carefully (fixture)": "Paalala: sagutin nang mabuti (fixture)",
        },
        "moved": [("item:Q1_OLD", "item:Q1_NEW")],
        "fellback": [],
    }
    carried, fellback = summarize_plan(plan)
    assert carried == 3  # 2 kept (excluding _meta) + 1 moved
    assert fellback == 0
