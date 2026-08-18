from pathlib import Path

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
