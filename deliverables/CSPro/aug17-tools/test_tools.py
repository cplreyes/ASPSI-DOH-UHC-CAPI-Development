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
    join_paper_build_items,
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


# --- Task 3.4, R15 design fixes ---------------------------------------------


def test_validation_diff_paper_empty_is_info_not_blocking():
    # R15 item 1: VALIDATION_DIFF blocks ONLY when both sides have content --
    # the paper never encodes machine validation, so a paper-empty/build-
    # nonempty pair must surface as a visible, non-blocking INFO line, not a
    # blocking red.
    paper = [Row(inst="F9", qnum="1", kind="item", stem="Enter amount (fixture).",
                 qtype="number", cardinality="single", validation="")]
    build = [Row(inst="F9", qnum="1", item_name="Q1", kind="item", stem="Enter amount (fixture).",
                 qtype="number", cardinality="single", validation="required")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert not any(f.category == "VALIDATION_DIFF" for f in findings)
    assert any(f.category == "VALIDATION_INFO" for f in findings)
    assert blocking == 0


def test_validation_diff_build_empty_is_also_info_not_blocking():
    # Symmetric case: paper has content, build has none -- still "not both
    # sides have content", per the literal rule text.
    paper = [Row(inst="F9", qnum="2", kind="item", stem="Enter amount (fixture).",
                 qtype="number", cardinality="single", validation="must be positive (fixture)")]
    build = [Row(inst="F9", qnum="2", item_name="Q2", kind="item", stem="Enter amount (fixture).",
                 qtype="number", cardinality="single", validation="")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert not any(f.category == "VALIDATION_DIFF" for f in findings)
    assert any(f.category == "VALIDATION_INFO" for f in findings)
    assert blocking == 0


def test_validation_diff_both_sides_content_still_blocks():
    # The one case that must still block: both sides declare validation and
    # they disagree.
    paper = [Row(inst="F9", qnum="3", kind="item", stem="Enter amount (fixture).",
                 qtype="number", cardinality="single", validation="must be numeric (fixture)")]
    build = [Row(inst="F9", qnum="3", item_name="Q3", kind="item", stem="Enter amount (fixture).",
                 qtype="number", cardinality="single", validation="required")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert any(f.category == "VALIDATION_DIFF" for f in findings)
    assert blocking > 0


def test_escape_apostrophe_fold_is_not_a_false_option_diff():
    # R15 item 2: escape-artifact fold. pandoc's own backslash-escape table
    # (paper_tables._strip_md) doesn't cover \' -- a literal backslash
    # survives into the paper option label ("I don\'t know") while the build
    # never has one. Sanctioned fold, paper side only, logged.
    paper = [Row(inst="F9", qnum="7", kind="item", stem="Invented question (fixture)?",
                 options=[{"code": "1", "label": "I don\\'t know (fixture)"}],
                 qtype="single", cardinality="single")]
    build = [Row(inst="F9", qnum="7", item_name="Q7", kind="item", stem="Invented question (fixture)?",
                 options=[{"code": "1", "label": "I don't know (fixture)"}],
                 qtype="single", cardinality="single")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert not any(f.category == "OPTION_DIFF" for f in findings)


def test_escape_apostrophe_fold_is_logged():
    from aug17_diff import _norm_events, _fold_escape_artifacts
    _norm_events.clear()
    out = _fold_escape_artifacts("I don\\'t know (fixture)")
    assert out == "I don't know (fixture)"
    assert any(e["kind"] == "escape-apostrophe" for e in _norm_events)


def test_trailing_bracket_gate_stripped_from_stem():
    # R15 item 2: trailing bracket/SELECT-directive strip. A paper stem
    # ending in a printed eligibility-gate annotation (angle brackets) must
    # not false-positive STEM_DIFF against a build stem that never prints
    # the annotation.
    paper = [Row(inst="F9", qnum="8", kind="item",
                 stem="Do you enjoy invented tea? <only for respondents from invented facilities>",
                 qtype="text", cardinality="single")]
    build = [Row(inst="F9", qnum="8", item_name="Q8", kind="item",
                 stem="Do you enjoy invented tea?",
                 qtype="text", cardinality="single")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert not any(f.category == "STEM_DIFF" for f in findings)


def test_trailing_select_directive_stripped_from_stem():
    paper = [Row(inst="F9", qnum="9", kind="item",
                 stem="Which invented flavors do you like? SELECT ALL THAT APPLY.",
                 qtype="text", cardinality="single")]
    build = [Row(inst="F9", qnum="9", item_name="Q9", kind="item",
                 stem="Which invented flavors do you like?",
                 qtype="text", cardinality="single")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert not any(f.category == "STEM_DIFF" for f in findings)


def test_trailing_directive_strip_applies_to_options_too():
    paper = [Row(inst="F9", qnum="10", kind="item", stem="Invented item (fixture)?",
                 options=[{"code": "1", "label": "Invented option one <only for invented facilities>"}],
                 qtype="single", cardinality="single")]
    build = [Row(inst="F9", qnum="10", item_name="Q10", kind="item", stem="Invented item (fixture)?",
                 options=[{"code": "1", "label": "Invented option one"}],
                 qtype="single", cardinality="single")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert not any(f.category == "OPTION_DIFF" for f in findings)


def test_trailing_bracket_never_strips_mid_string():
    # "never strip mid-string" -- a bracket fragment that is NOT at the very
    # end is real content and must stay a genuine STEM_DIFF.
    paper = [Row(inst="F9", qnum="11", kind="item",
                 stem="Enter the invented code <see the invented legend> now please.",
                 qtype="text", cardinality="single")]
    build = [Row(inst="F9", qnum="11", item_name="Q11", kind="item",
                 stem="Enter the invented code now please.",
                 qtype="text", cardinality="single")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert any(f.category == "STEM_DIFF" for f in findings)


def test_trailing_directive_strip_is_logged():
    from aug17_diff import _norm_events, _strip_trailing_directive
    _norm_events.clear()
    out = _strip_trailing_directive("Invented stem (fixture)? SELECT ALL THAT APPLY.")
    assert out == "Invented stem (fixture)?"
    assert any(e["kind"] == "trailing-select-directive" for e in _norm_events)
    _norm_events.clear()
    out = _strip_trailing_directive("Invented stem (fixture)? <only for invented respondents>")
    assert out == "Invented stem (fixture)?"
    assert any(e["kind"] == "trailing-bracket" for e in _norm_events)


# --- R18 (rev-1.4 finding, F3): build-side "(cont. N)" pagination fold -----


def test_build_cont_suffix_stripped_before_section_comparison():
    # CSPro splits a long section across multiple form pages; every page
    # after the first gets a "(cont.)"/"(cont. N)" suffix appended to the
    # displayed section title on the BUILD side only -- the paper prints
    # the plain section name throughout. Sanctioned build-side fold,
    # logged (same _norm_events mechanism as the paper-side folds).
    paper = [Row(inst="F9", qnum="1", kind="item", stem="Invented item (fixture)?",
                 section="G Invented Section", qtype="text", cardinality="single")]
    build = [Row(inst="F9", qnum="1", item_name="Q1", kind="item", stem="Invented item (fixture)?",
                 section="G Invented Section (cont. 3)", qtype="text", cardinality="single")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert not any(f.category == "SECTION_DIFF" for f in findings)


def test_build_cont_suffix_bare_form_also_stripped():
    # First continuation page prints "(cont.)" with no number.
    paper = [Row(inst="F9", qnum="2", kind="item", stem="Invented item (fixture)?",
                 section="H Invented Section", qtype="text", cardinality="single")]
    build = [Row(inst="F9", qnum="2", item_name="Q2", kind="item", stem="Invented item (fixture)?",
                 section="H Invented Section (cont.)", qtype="text", cardinality="single")]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    assert not any(f.category == "SECTION_DIFF" for f in findings)


def test_build_cont_suffix_fold_is_logged():
    from aug17_diff import _norm_events, _fold_build_cont_suffix
    _norm_events.clear()
    out = _fold_build_cont_suffix("Invented Section (cont. 3)")
    assert out == "Invented Section"
    assert any(e["kind"] == "build-cont-suffix" for e in _norm_events)


def test_build_cont_suffix_never_strips_a_real_mid_string_occurrence():
    # Anchored to the END only -- a genuine printed "(cont.)" appearing
    # mid-string (not as the trailing pagination artifact) must survive.
    from aug17_diff import _fold_build_cont_suffix
    text = "Invented Section (cont.) with more text after it"
    assert _fold_build_cont_suffix(text) == text


# --- Task 3.4, R15 addendum: paper_tables.py section-parser fixes ----------


def test_section_header_bold_wraps_whole_cell():
    # Some F2 sections (D/E/F) print "**D. Title**" (bold wraps the letter
    # AND the period), not "D. **Title**" (letter bare) like A/B/C/G/J.
    # SECTION_LETTER_RE must accept both forms.
    md = (
        "+----+\n"
        "| **D. Invented Section Title**  |\n"
        "+----+\n"
        "| 40. **Invented item stem (fixture)?** |\n"
        "+----+\n"
        "|    | ☐ Invented option (fixture) |\n"
        "+----+\n"
    )
    rows = parse_extract(md, "F9")
    headers = [r for r in rows if r.kind == "section_header"]
    assert any(h.section.startswith("D ") and "Invented Section Title" in h.section for h in headers)
    items = [r for r in rows if r.kind == "item"]
    q40 = next(r for r in items if r.qnum == "40")
    assert q40.section.startswith("D ")


def test_wrapped_directive_fragment_not_misread_as_section_heading():
    # Pandoc word-wraps a long cell across two physical lines with no
    # "+---+" divider between them. When that wrap splits a directive banner
    # ("...SELECT ALL" / "THAT APPLY..."), the orphaned tail fragment must
    # NOT become a spurious section header (and the item's own stem/skip
    # accumulation must not be truncated by the premature item-close).
    md = (
        "+----+\n"
        "| 61. **Invented follow-up item text (fixture)?** SELECT ALL |\n"
        "|     THAT APPLY                                              |\n"
        "+----+\n"
        "|    | ☐ Invented option (fixture) |\n"
        "+----+\n"
        "| 62. **Next invented item (fixture)?** |\n"
        "+----+\n"
        "|    | ☐ Another invented option (fixture) |\n"
        "+----+\n"
    )
    rows = parse_extract(md, "F9")
    headers = [r for r in rows if r.kind == "section_header"]
    assert not any("THAT APPLY" in h.stem for h in headers)
    items = [r for r in rows if r.kind == "item"]
    q61 = next(r for r in items if r.qnum == "61")
    assert "SELECT ALL THAT APPLY" in q61.stem
    q62 = next(r for r in items if r.qnum == "62")
    assert q62.section == q61.section  # no spurious section boundary inserted between them


def test_wrapped_row_merge_recovers_split_option_label():
    # Same word-wrap defect, checkbox-option flavor: a long option label
    # wraps to a second physical line with no divider; unmerged, the
    # continuation becomes an orphan instruction row and the option is
    # silently truncated (an OPTION_DIFF artifact, not a real divergence).
    md = (
        "+----+----+----+----+\n"
        "| 62. **Invented multi-select item (fixture)?**             |\n"
        "+----+----+----+----+\n"
        "|    |    | ☐ Patient invented and |    |\n"
        "|    |    | continuation label     |    |\n"
        "+----+----+----+----+\n"
    )
    rows = parse_extract(md, "F9")
    items = [r for r in rows if r.kind == "item"]
    q62 = next(r for r in items if r.qnum == "62")
    assert any(o["label"] == "Patient invented and continuation label" for o in q62.options)


def test_multi_select_recognizes_check_all_variant():
    # F2 Q111 prints "Check all that apply" (not "Select all that apply");
    # MULTI_SELECT_RE only matched the "select" phrasing, so the paper side
    # mis-derived qtype=single/cardinality=single against a build that
    # correctly implements multi -- a genuine cardinality misclassification,
    # not a real content divergence.
    md = (
        "+----+\n"
        "| 111. **Invented multi item (fixture)?** *Check all that apply* |\n"
        "+----+\n"
        "|    | ☐ Invented option (fixture) |\n"
        "+----+\n"
    )
    rows = parse_extract(md, "F9")
    items = [r for r in rows if r.kind == "item"]
    q111 = next(r for r in items if r.qnum == "111")
    assert q111.qtype == "multi"
    assert q111.cardinality == "multi"


def test_two_column_checkbox_grid_reads_column_major_not_row_major():
    # R18 (rev-1.4 finding, F3): a multi-row 2-column checkbox grid (each
    # physical row prints one item from column 1 and one from column 2) is
    # read by pandoc/the line-scan in ROW-major physical order, but the
    # RESPONDENT reads it column-major (down column 1 fully, then down
    # column 2) -- which is also the build's own real option order. Without
    # a fix, the paper-extracted order is a perfect row-major interleave of
    # the true column-major order (confirmed against real F3 data: an
    # 8-option list read as 1,5,2,6,3,7,4,8 instead of 1,2,3,4,5,6,7,8).
    md = (
        "+----+----+\n"
        "| 9. **Invented multi-row group item (fixture)?**    |\n"
        "+----+----+\n"
        "| ☐ Invented A | ☐ Invented E |\n"
        "+----+----+\n"
        "| ☐ Invented B | ☐ Invented F |\n"
        "+----+----+\n"
        "| ☐ Invented C | ☐ Invented G |\n"
        "+----+----+\n"
        "| ☐ Invented D | ☐ Invented H |\n"
        "+----+----+\n"
    )
    rows = parse_extract(md, "F9")
    items = [r for r in rows if r.kind == "item"]
    q9 = next(r for r in items if r.qnum == "9")
    labels = [o["label"] for o in q9.options]
    # column-major: A,B,C,D (column 1, top to bottom) then E,F,G,H (column 2)
    assert labels == ["Invented A", "Invented B", "Invented C", "Invented D",
                       "Invented E", "Invented F", "Invented G", "Invented H"]


def test_two_column_checkbox_grid_handles_uneven_split():
    # 9 items, 5 in column 1 / 4 in column 2 (the last row has only one
    # checkbox cell, no partner) -- must not lose or misplace the odd one.
    md = (
        "+----+----+\n"
        "| 10. **Invented odd-count group item (fixture)?**   |\n"
        "+----+----+\n"
        "| ☐ Item 1 | ☐ Item 6 |\n"
        "+----+----+\n"
        "| ☐ Item 2 | ☐ Item 7 |\n"
        "+----+----+\n"
        "| ☐ Item 3 | ☐ Item 8 |\n"
        "+----+----+\n"
        "| ☐ Item 4 | ☐ Item 9 |\n"
        "+----+----+\n"
        "| ☐ Item 5 |\n"
        "+----+\n"
    )
    rows = parse_extract(md, "F9")
    items = [r for r in rows if r.kind == "item"]
    q10 = next(r for r in items if r.qnum == "10")
    labels = [o["label"] for o in q10.options]
    assert labels == [f"Item {n}" for n in range(1, 10)]


def test_single_column_checkbox_list_unaffected_by_column_major_fix():
    # Sanity guard: the overwhelming common case (one checkbox per row) must
    # produce EXACTLY the same order as before -- column-major degenerates
    # to row-major when there's only one column.
    md = (
        "+----+\n"
        "| 11. **Invented single-column item (fixture)?**  |\n"
        "+----+\n"
        "| ☐ First invented option |\n"
        "+----+\n"
        "| ☐ Second invented option |\n"
        "+----+\n"
        "| ☐ Third invented option |\n"
        "+----+\n"
    )
    rows = parse_extract(md, "F9")
    items = [r for r in rows if r.kind == "item"]
    q11 = next(r for r in items if r.qnum == "11")
    labels = [o["label"] for o in q11.options]
    assert labels == ["First invented option", "Second invented option", "Third invented option"]


def test_skip_this_directive_recognized_not_misread_as_section_heading():
    # R18 (rev-1.4 finding, F3): a printed all-caps skip directive like
    # "SKIP THIS QUESTION WHEN ANSWER IN Qnn IS NO" -- isolated on its own
    # row by the (unchanged, intentional) blank-line run boundary above and
    # a real table divider below -- matched _is_allcaps_heading but NOT the
    # old DIRECTIVE_BANNER_RE (which covered "SKIP (TO|IF)" but not "SKIP
    # THIS"), so it fell through to the section_header/consent branch and
    # silently became a spurious section boundary (12 F3 rows carried this
    # exact text as their `section`). Fixed by widening DIRECTIVE_BANNER_RE
    # to also match "SKIP THIS" -- routes it to kind=instruction instead,
    # leaving `cur`/`section` untouched, no merge-behavior change anywhere
    # (deliberately NOT folded into the item's own stem -- a first attempt
    # via loosening the blank-line divider check was tried and reverted:
    # it corrupted section titles elsewhere, see the next test and
    # _is_divider's docstring). Item number changed from the real F3 "Q63"
    # to an invented "Q99" reference; the all-caps SHAPE is kept verbatim --
    # a lowercase "(fixture)" marker inside the caps run would itself
    # defeat _is_allcaps_heading and fail to reproduce the bug.
    md = (
        "+----+\n"
        "| 70. **Invented multi-select item?** Check all |\n"
        "|     that apply.                                          |\n"
        "|                                                          |\n"
        "| > *SKIP THIS QUESTION WHEN ANSWER IN Q99 IS NO*           |\n"
        "+----+\n"
        "|    | ☐ Invented option |\n"
        "+----+\n"
    )
    rows = parse_extract(md, "F9")
    headers = [r for r in rows if r.kind == "section_header"]
    assert not any("SKIP THIS QUESTION" in h.section for h in headers)
    instructions = [r for r in rows if r.kind == "instruction"]
    assert any("SKIP THIS QUESTION WHEN ANSWER IN Q99 IS NO" in r.stem for r in instructions)
    items = [r for r in rows if r.kind == "item"]
    q70 = next(r for r in items if r.qnum == "70")
    assert "Check all that apply" in q70.stem  # its own stem is otherwise intact


def test_section_header_does_not_absorb_following_blank_separated_paragraph():
    # Regression guard: a section header must NOT pull in a following
    # descriptive paragraph separated from it by a blank row (exactly what
    # the reverted "loosen the blank-line divider check" attempt caused).
    md = (
        "+----+\n"
        "| G. **Invented Section Title** |\n"
        "|                                |\n"
        "| This section covers invented respondents only. |\n"
        "+----+\n"
        "| 1. **Invented item (fixture)?** |\n"
        "+----+\n"
        "|    | ☐ Invented option |\n"
        "+----+\n"
    )
    rows = parse_extract(md, "F9")
    headers = [r for r in rows if r.kind == "section_header"]
    assert len(headers) == 1
    assert headers[0].section == "G Invented Section Title"
    assert "covers invented respondents" not in headers[0].section


def test_wrapped_row_merge_leaves_normal_divided_rows_alone():
    # Sanity guard: rows properly separated by a "+---+" divider (the
    # overwhelming common case) must be completely unaffected by the merge
    # pre-pass -- two genuinely distinct items must NOT get glued together.
    md = (
        "+----+\n"
        "| 1. **First invented item (fixture)?** |\n"
        "+----+\n"
        "|    | ☐ Invented option A (fixture) |\n"
        "+----+\n"
        "| 2. **Second invented item (fixture)?** |\n"
        "+----+\n"
        "|    | ☐ Invented option B (fixture) |\n"
        "+----+\n"
    )
    rows = parse_extract(md, "F9")
    items = [r for r in rows if r.kind == "item"]
    assert len(items) == 2
    q1 = next(r for r in items if r.qnum == "1")
    q2 = next(r for r in items if r.qnum == "2")
    assert q1.options == [{"code": "1", "label": "Invented option A (fixture)"}]
    assert q2.options == [{"code": "1", "label": "Invented option B (fixture)"}]


# --- Task 3.4, R15 item 4: emit_skip_register_rows.py ----------------------

from emit_skip_register_rows import (
    _extract_qnums,
    already_registered_qnums,
    build_coverage_index,
    format_register_row,
    parse_matrix_rows,
    parse_skip_diff_findings,
    pick_covering_row,
)

_FIXTURE_DIFF_MD = """# F9 diff report

## SKIP_DIFF (3)

- **UNREGISTERED** [6] paper skip="IF No GOTO <proceed to Q9> (fixture)" | build (Q6) skip=""
- **UNREGISTERED** [7] paper skip="" | build (Q7) skip="visible-if: v.Q6 === 'Yes' (fixture)"
- **REGISTERED** [8] paper skip="" | build (Q8) skip="visible-if: v.Q6 === 'Yes' (fixture)" — already covered

## MESSAGE_DIFF (0)
"""

_FIXTURE_MATRIX_MD = """# F9 tier-2 matrix (fixture)

## Section A

| Rule | Expected behavior | Covering test | Status |
|---|---|---|---|
| Q7 visibility (fixture) | Shown only when Q6 (invented gate) = Yes | `shows Q7 when Q6 is Yes (fixture)` | PASS |
| Q99 unrelated (fixture) | Some unrelated invented rule | `some invented test` | PASS |
| Q100 not verified (fixture) | Invented rule not yet passing | `some other invented test` | FAIL |
"""


def test_parse_skip_diff_findings_extracts_unregistered_only_by_default():
    findings = parse_skip_diff_findings(_FIXTURE_DIFF_MD)
    assert len(findings) == 3
    q6 = next(f for f in findings if f["qnum"] == "6")
    assert q6["registered"] is False
    assert "Q9" in q6["paper"]
    q8 = next(f for f in findings if f["qnum"] == "8")
    assert q8["registered"] is True


def test_extract_qnums_explicit_and_range():
    assert _extract_qnums("Q7 visibility (fixture)") == {"7"}
    assert _extract_qnums("Q13-Q30 block gate (fixture)") == {str(n) for n in range(13, 31)}
    assert _extract_qnums("Q71a/Q71b independent (fixture)") == {"71a", "71b"}
    assert _extract_qnums("no qnums here (fixture)") == set()


def test_parse_matrix_rows_and_coverage_index():
    rows = parse_matrix_rows(_FIXTURE_MATRIX_MD)
    assert len(rows) == 3
    coverage = build_coverage_index(rows)
    # Q7's own row covers both Q7 (subject) and Q6 (condition variable
    # named in the Expected-behavior column) -- broad text scan, not just
    # the Rule cell.
    assert "7" in coverage
    assert "6" in coverage
    # FAIL-status rows never enter the coverage index.
    assert "100" not in coverage


def test_coverage_index_accepts_pass_with_qualifier_suffix():
    # Real F2 matrix rows sometimes annotate PASS with a parenthetical
    # ("PASS (predicate identical across Q92-Q95, ...)") -- still verified.
    md = (
        "| Rule | Expected behavior | Covering test | Status |\n"
        "|---|---|---|---|\n"
        "| Q92 gate (fixture) | Invented rule | invented test | PASS (qualifier text, fixture) |\n"
    )
    rows = parse_matrix_rows(md)
    coverage = build_coverage_index(rows)
    assert "92" in coverage


def test_pick_covering_row_prefers_the_rows_own_subject():
    rows = parse_matrix_rows(_FIXTURE_MATRIX_MD)
    coverage = build_coverage_index(rows)
    row = pick_covering_row("7", coverage["7"])
    assert row["rule"].startswith("Q7")
    # Q6 has no row of its own -- falls back to the row that references it.
    row6 = pick_covering_row("6", coverage["6"])
    assert row6["rule"].startswith("Q7")


def test_already_registered_qnums_reads_existing_register():
    reg_text = (
        "# fixture register\n\n"
        "| inst | qnum/item | class | paper says | build does | rationale / ticket |\n"
        "|---|---|---|---|---|---|\n"
        "| F9 | Q8 (fixture) | defect-fix | paper (fixture) | build (fixture) | fixture rationale |\n"
    )
    assert already_registered_qnums(reg_text, "F9") == {"8"}


def test_format_register_row_cites_the_matrix_row():
    finding = {"qnum": "7", "paper": "", "build": "visible-if: v.Q6 === 'Yes' (fixture)", "item": "Q7"}
    matrix_row = {"rule": "Q7 visibility (fixture)", "expected": "Shown only when Q6 = Yes (fixture)",
                  "test": "`shows Q7 when Q6 is Yes (fixture)`", "status": "PASS", "qnums": {"6", "7"}}
    line = format_register_row("F9", "7", finding, matrix_row, "2026-08-18")
    assert line.startswith("| F9 | Q7 | capi-adaptation |")
    assert "Q7 visibility (fixture)" in line
    assert line.count("|") == 7  # 6 columns -> 7 pipes


def test_format_register_row_escapes_js_or_operator_safely():
    # Real-world catch: a build predicate containing "||" (e.g.
    # "isYes(v['Q87']) || isYes(v['Q88'])") would otherwise produce a
    # register row with MORE than 6 pipe-delimited cells -- aug17_diff's
    # parse_register_rows has no escape-awareness and silently discards any
    # row that doesn't split to exactly 6 cells, so the row would vanish
    # with no error. Must sanitize, not backslash-escape.
    finding = {"qnum": "89", "paper": "", "build": "visible-if: isYes(v['Q87']) || isYes(v['Q88']) (fixture)", "item": "Q89"}
    matrix_row = {"rule": "Q89 gate (fixture)", "expected": "Shown when Q87 or Q88 = Yes (fixture)",
                  "test": "`shows Q89 (fixture)`", "status": "PASS", "qnums": {"87", "88", "89"}}
    line = format_register_row("F9", "89", finding, matrix_row, "2026-08-18")
    from aug17_diff import parse_register_rows
    reg_text = (
        "# fixture register\n\n"
        "| inst | qnum/item | class | paper says | build does | rationale / ticket |\n"
        "|---|---|---|---|---|---|\n"
        + line + "\n"
    )
    parsed = parse_register_rows(reg_text)
    assert len(parsed) == 1
    assert parsed[0].qnum_item == "Q89"


def test_format_register_row_notes_missing_skip_direction():
    finding = {"qnum": "6", "paper": "IF No GOTO <proceed to Q9> (fixture)", "build": "", "item": "Q6"}
    matrix_row = {"rule": "Q7 visibility (fixture)", "expected": "Shown only when Q6 = Yes (fixture)",
                  "test": "`shows Q7 when Q6 is Yes (fixture)`", "status": "PASS", "qnums": {"6", "7"}}
    line = format_register_row("F9", "6", finding, matrix_row, "2026-08-18")
    assert "SOURCE of a forward routing decision" in line


# --- Scope add (controller, post-3.4): join_paper_build_items min()-pairing bug ---
#
# impl-1-4 (Task 1.4, F3 lane) found and documented: when a paper qnum has FEWER rows
# than build at the same qnum (e.g. paper's one combined "household income" question
# splits into build's Q18_INCOME_AMOUNT + Q18_INCOME_BRACKET), the pairing loop's
# n = min(len(p_list), len(b_list)) only ever runs _compare_pair on the FIRST n rows.
# The "extra" build row(s) beyond n get a content-BLIND EXTRA_IN_BUILD/no-pair notice
# only -- their actual stem/options/etc. are NEVER compared against anything, so a
# real content regression in that field would be permanently invisible to Tier-1 once
# the qnum is registered once. Same root bug in rejoin_translations.py's
# join_paper_build_items (used by --stale-from-tables): the extra build row isn't
# even returned in `pairs` at all, so it can never be flagged stale either.


def test_extra_build_row_beyond_paper_count_was_previously_invisible_to_comparison():
    # Characterization of the OLD (buggy) behavior, kept as a regression guard: before
    # the fix, a qnum with 1 paper row / 2 build rows only ever compares the FIRST
    # build row -- the second's genuinely different content produces NO STEM_DIFF at
    # all, even though it obviously differs from anything on the paper side.
    # (This test intentionally does NOT import the fix -- see the GREEN test below for
    # the fixed behavior. Kept to document what "invisible" meant concretely.)
    paper = [Row(inst="F9", qnum="18", kind="item",
                 stem="Invented combined income question (fixture)?",
                 options=[{"code": "1", "label": "Invented bracket A (fixture)"}],
                 qtype="single", cardinality="single")]
    build = [
        Row(inst="F9", qnum="18", item_name="Q18_AMOUNT", kind="item",
            stem="Invented combined income question (fixture)?",
            options=[{"code": "1", "label": "Invented bracket A (fixture)"}],
            qtype="single", cardinality="single"),
        Row(inst="F9", qnum="18", item_name="Q18_BRACKET", kind="item",
            stem="Completely unrelated invented bracket stem (fixture)?",
            options=[{"code": "1", "label": "Totally different invented option (fixture)"}],
            qtype="single", cardinality="single"),
    ]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    # The fixed behavior (see test below) DOES surface this -- so this
    # characterization test asserts the fix is present (broadcast comparison runs),
    # proving the second build row is no longer invisible.
    stem_diffs = [f for f in findings if f.category == "STEM_DIFF" and f.qnum == "18"]
    assert len(stem_diffs) >= 1  # Q18_BRACKET's own genuinely-different stem now surfaces
    assert any("Q18_BRACKET" in f.detail for f in stem_diffs)


def test_extra_build_row_is_broadcast_compared_against_last_paper_row():
    # GREEN: the extra build row (beyond paper's row count at this qnum) is now ALSO
    # run through _compare_pair against paper's LAST row at that qnum, in ADDITION to
    # (not instead of) the existing EXTRA_IN_BUILD structural notice -- so its real
    # content is visible to Tier-1, not just its presence.
    paper = [Row(inst="F9", qnum="20", kind="item",
                 stem="Invented paper stem (fixture).",
                 options=[{"code": "1", "label": "Invented option (fixture)"}],
                 qtype="single", cardinality="single")]
    build = [
        Row(inst="F9", qnum="20", item_name="Q20_A", kind="item",
            stem="Invented paper stem (fixture).",
            options=[{"code": "1", "label": "Invented option (fixture)"}],
            qtype="single", cardinality="single"),
        Row(inst="F9", qnum="20", item_name="Q20_B", kind="item",
            stem="A totally different build-only stem (fixture).",
            options=[{"code": "1", "label": "A totally different option (fixture)"}],
            qtype="single", cardinality="single"),
    ]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    extra = [f for f in findings if f.category == "EXTRA_IN_BUILD" and f.qnum == "20"]
    assert len(extra) == 1  # structural notice still present, unchanged
    broadcast_stem = [f for f in findings if f.category == "STEM_DIFF" and f.qnum == "20"
                       and "Q20_B" in f.detail]
    assert len(broadcast_stem) == 1  # NEW: content comparison against paper's last row
    broadcast_opt = [f for f in findings if f.category == "OPTION_DIFF" and f.qnum == "20"
                      and "Q20_B" in f.detail]
    assert len(broadcast_opt) == 1


def test_missing_in_build_side_is_unchanged_by_the_broadcast_fix():
    # Sanity guard: the fix is scoped to build-has-MORE-rows only. The symmetric
    # paper-has-more-rows case (MISSING_IN_BUILD) must be completely untouched -- no
    # new broadcast comparison against an unrelated build row (which would produce
    # misleading findings for a paper item that genuinely has no build implementation).
    paper = [
        Row(inst="F9", qnum="21", kind="item", stem="First invented paper stem (fixture).",
            qtype="text", cardinality="single"),
        Row(inst="F9", qnum="21", kind="item", stem="Second invented paper stem (fixture).",
            qtype="text", cardinality="single"),
    ]
    build = [
        Row(inst="F9", qnum="21", item_name="Q21", kind="item",
            stem="First invented paper stem (fixture).", qtype="text", cardinality="single"),
    ]
    findings, counts, blocking = diff_instrument("F9", paper, build, _empty_register())
    missing = [f for f in findings if f.category == "MISSING_IN_BUILD" and f.qnum == "21"]
    assert len(missing) == 1
    stem_diffs = [f for f in findings if f.category == "STEM_DIFF" and f.qnum == "21"]
    assert len(stem_diffs) == 0  # the one real pair matches -- no broadcast noise added


def test_join_paper_build_items_no_longer_drops_extra_build_rows():
    # rejoin_translations.py's join_paper_build_items previously didn't even return a
    # tuple for a build row beyond paper's count at a qnum -- fully dropped, not even
    # visible as an unpaired row. Now it must appear, flagged distinctly (not silently
    # merged into an ordinary 1:1 pair, to avoid falsely marking it stale against an
    # unrelated anchor stem -- see compute_stale_from_tables below).
    paper = [Row(inst="F9", qnum="22", kind="item", stem="Invented paper stem (fixture).",
                 qtype="text", cardinality="single")]
    build = [
        Row(inst="F9", qnum="22", item_name="Q22_A", kind="item",
            stem="Invented paper stem (fixture).", qtype="text", cardinality="single"),
        Row(inst="F9", qnum="22", item_name="Q22_B", kind="item",
            stem="Different invented build-only stem (fixture).", qtype="text", cardinality="single"),
    ]
    pairs = join_paper_build_items("F9", paper, build)
    item_names = {b.item_name for _q, _p, b, _broadcast in pairs if b is not None}
    assert "Q22_A" in item_names
    assert "Q22_B" in item_names  # previously silently dropped entirely
    # The real 1:1 pair is NOT flagged broadcast; the extra row IS.
    broadcast_flags = {b.item_name: is_b for _q, _p, b, is_b in pairs if b is not None}
    assert broadcast_flags["Q22_A"] is False
    assert broadcast_flags["Q22_B"] is True


def test_compute_stale_from_tables_does_not_false_flag_extra_build_rows_stale():
    # The broadcast pair for an "extra" build row is intentionally NOT auto-derived
    # into stem_changed/option_changed -- comparing it against an unrelated anchor
    # paper stem would ALWAYS look "changed" even when nothing really changed since
    # the last translation pass, which would perpetually drop a possibly-fine
    # translation. compute_stale_from_tables must only judge staleness from genuine
    # 1:1 positional pairs.
    paper = [Row(inst="F9", qnum="23", kind="item", stem="Invented paper stem (fixture).",
                 options=[{"code": "1", "label": "Invented option (fixture)"}],
                 qtype="single", cardinality="single")]
    build = [
        Row(inst="F9", qnum="23", item_name="Q23_A", kind="item",
            stem="Invented paper stem (fixture).",
            options=[{"code": "1", "label": "Invented option (fixture)"}],
            qtype="single", cardinality="single"),
        Row(inst="F9", qnum="23", item_name="Q23_B", kind="item",
            stem="Totally unrelated build-only stem (fixture).",
            options=[{"code": "1", "label": "Totally unrelated option (fixture)"}],
            qtype="single", cardinality="single"),
    ]
    stem_changed, option_changed, new_rows = compute_stale_from_tables("F9", paper, build)
    assert "Q23_A" not in stem_changed
    assert "Q23_B" not in stem_changed  # NOT auto-flagged from the broadcast pair


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
