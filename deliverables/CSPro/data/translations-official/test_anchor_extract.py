import copy
import json
import os
import re
import sys

import fitz
import pytest

import anchor_extract as ax
from conftest import make_pdf
from textnorm import norm_for_match

sys.path.insert(0, ax.CSPRO)
from cspro_helpers import apply_translations  # noqa: E402

DCF = {"name": "TINY", "labels": [{"text": "Tiny survey"}], "levels": [{"name": "LVL", "labels": [{"text": "Level"}],
       "records": [{"name": "REC", "labels": [{"text": "Record A"}], "items": [
           {"name": "Q1_MARITAL", "labels": [{"text": "1. What is your current marital status?"}],
            "valueSets": [{"name": "Q1_MARITAL_VS1", "labels": [{"text": "1. What is your current marital status?"}],
                           "values": [{"labels": [{"text": "Single, never married"}], "pairs": [{"value": "1"}]},
                                      {"labels": [{"text": "Married or living together"}], "pairs": [{"value": "2"}]},
                                      {"labels": [{"text": "Legally separated"}], "pairs": [{"value": "3"}]}]}]},
           {"name": "Q2_EMPLOYED", "labels": [{"text": "2. Are you currently employed in this facility?"}]},
           {"name": "Q3_UNTOUCHED", "labels": [{"text": "3. This label was left in English on paper"}]},
           {"name": "Q4_TRAVEL_HH", "labels": [{"text": "4. How long is the travel time? — Hours"}]},
       ]}]}]}

PAPER = [
    "1. What is your current marital status?",
    "Ano ang iyong kasalukuyang katayuan sa pag-aasawa?",
    "Single, never married  Walang asawa, hindi kailanman nag-asawa",
    "Married or living together  May asawa o nagsasama",
    "Legally separated  Legal na hiwalay",
    "2. Are you currently employed in this facility?",
    "Kasalukuyan ka bang nagtatrabaho sa pasilidad na ito?",
    "3. This label was left in English on paper",
    "3. This label was left in English on paper",
]


@pytest.fixture
def fixture_dir(tmp_path):
    (tmp_path / "t.dcf").write_text(json.dumps(DCF), encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    make_pdf(src / "F9-Tagalog_Tiny Survey_Aug21.pdf", PAPER)
    return tmp_path


def test_dcf_anchors_are_name_scoped(fixture_dir):
    anchors = ax.dcf_anchors(fixture_dir / "t.dcf")
    assert anchors["item:Q1_MARITAL"] == "1. What is your current marital status?"
    assert anchors["vs:Q1_MARITAL_VS1"] == "1. What is your current marital status?"
    assert anchors["val:Q1_MARITAL_VS1:2"] == "Married or living together"
    assert all(":" in k for k in anchors)


def test_container_nodes_are_not_anchors(fixture_dir):
    """dict:/level:/record: labels are page furniture ("Tiny survey", "Record A")
    that matches headers and footers, opening spurious spans — never anchored."""
    anchors = ax.dcf_anchors(fixture_dir / "t.dcf")
    assert not [k for k in anchors if k.split(":", 1)[0] not in ("item", "vs", "val")]
    assert "dict:TINY" not in anchors and "record:REC" not in anchors


def test_component_suffix_is_stripped_from_anchor(fixture_dir):
    anchors = ax.dcf_anchors(fixture_dir / "t.dcf")
    assert anchors["item:Q4_TRAVEL_HH"] == "4. How long is the travel time?"


def test_build_norm_projection_matches_norm_for_match():
    """The offset-map projection and the label projection MUST agree character for
    character, or an anchor can never be found in the paper text it came from."""
    for s in ["Doctor's Professional Fee", "Biñan — Level 3 hospital",
              "Others (specify) / Iba pa", "  Q7.  Sex  at  birth?  "]:
        assert ax.build_norm(s)[0].strip() == norm_for_match(s)


def test_extract_pairs_value_set_options_and_emits_name_keys(fixture_dir):
    anchors = ax.dcf_anchors(fixture_dir / "t.dcf")
    r = ax.extract(fixture_dir / "src" / "F9-Tagalog_Tiny Survey_Aug21.pdf", anchors)
    assert r["clean"]["item:Q1_MARITAL"] == "Ano ang iyong kasalukuyang katayuan sa pag-aasawa?"
    assert r["clean"]["vs:Q1_MARITAL_VS1"] == "Ano ang iyong kasalukuyang katayuan sa pag-aasawa?"
    assert r["clean"]["val:Q1_MARITAL_VS1:1"] == "Walang asawa, hindi kailanman nag-asawa"
    assert r["clean"]["val:Q1_MARITAL_VS1:2"] == "May asawa o nagsasama"
    assert r["clean"]["item:Q2_EMPLOYED"] == "Kasalukuyan ka bang nagtatrabaho sa pasilidad na ito?"


def test_untranslated_on_paper_is_held_back_as_empty(fixture_dir):
    anchors = ax.dcf_anchors(fixture_dir / "t.dcf")
    r = ax.extract(fixture_dir / "src" / "F9-Tagalog_Tiny Survey_Aug21.pdf", anchors)
    assert "item:Q3_UNTOUCHED" not in r["clean"]
    row = next(f for f in r["flagged"] if f["key"] == "item:Q3_UNTOUCHED")
    assert row["flags"] == ["empty"]


def test_clean_span_strips_box_glyphs_and_skip_notes():
    """The June-5 span cleaner, copied verbatim: checkbox glyphs and routing notes
    are furniture, and the Ilocano layout wraps the whole candidate in parens."""
    assert ax.clean_span(" ☐ Lalaki <proceed to Q10> ") == "Lalaki"
    assert ax.clean_span("(Ilocano nga sungbat)") == "Ilocano nga sungbat"


def test_qa_flags_kept_verbatim_plus_glue_flags():
    assert ax.qa_flags("5. Sex", "5. Sex", {"5 sex"}) == ["echo-english"]
    assert ax.qa_flags("Level 3 hospital", "Ospital na Level 1", set()) == ["digit-mismatch"]
    assert ax.qa_flags("Physician", "", set()) == ["empty"]
    # the 2026-08-17 live spill class: a short option label glued onto the stem
    assert ax.qa_flags("4. What is your sex assigned at birth?",
                       "Ano ang iyong kasarian noong ipinanganak ka? Male Lalaki",
                       {"4 what is your sex assigned at birth", "male", "female"}) == ["glued-short-label"]
    assert ax.qa_flags("Do you own the building?", "Pag-aari mo ba ang gusali? Yes",
                       {"do you own the building", "yes", "no"}) == ["ends-with-other-label"]
    # an anchor that is part of the span's own English never fires either flag
    assert ax.qa_flags("Male nurse", "Lalaking nars", {"male nurse", "male"}) == []


def test_glue_flag_self_guard_is_word_bounded():
    """The "this anchor is part of my own English" guard on both new flags must be
    WORD-bounded, not a plain substring test.

    On the real F1 dictionary a substring guard silently suppressed 11 collisions among
    the 26 anchors of length 4-9 - including ("male", "female"), which is the exact
    2026-08-17 live spill the flags were written for ("male" is a substring of "female",
    so the Female option's bled span was scored clean and shipped back to the live map).
    Other real F1 collisions: ("clear", "unclear"), ("nurse", "...to your nurses").
    """
    labels = {"male", "female"}
    # the Female option's span bleeds and glues the English "Male" onto it
    assert ax.qa_flags("Female", "Babae Male", labels) == ["glued-short-label",
                                                           "ends-with-other-label"]
    # ("clear", "unclear") - the same shape on a longer pair
    assert "ends-with-other-label" in ax.qa_flags("Unclear", "Hindi malinaw Clear",
                                                  {"clear", "unclear"})
    # genuine word-level containment still suppresses both flags
    assert ax.qa_flags("Male nurse", "Lalaking nars", {"male nurse", "male"}) == []


def test_cli_writes_name_scoped_maps_and_report(fixture_dir):
    out = fixture_dir / "out"
    rc = ax.main(["--source", str(fixture_dir / "src"), "--instrument", "F9",
                  "--dcf", str(fixture_dir / "t.dcf"), "--out", str(out), "--locales", "FIL"])
    assert rc == 0
    m = json.loads((out / "fil.json").read_text(encoding="utf-8"))
    assert "_meta" not in m and all(":" in k for k in m)
    assert m["val:Q1_MARITAL_VS1:3"] == "Legal na hiwalay"
    flagged = json.loads((out / "fil_flagged.json").read_text(encoding="utf-8"))
    assert any(f["key"] == "item:Q3_UNTOUCHED" for f in flagged)
    report = (out / "QA-REPORT.md").read_text(encoding="utf-8")
    assert "| FIL |" in report and "`empty`" in report
    assert not (out / "bcl.json").exists()


def test_extractor_output_is_accepted_by_apply_translations(fixture_dir, capsys):
    # regression lock (passes on first run by design)
    out = fixture_dir / "out"
    ax.main(["--source", str(fixture_dir / "src"), "--instrument", "F9",
             "--dcf", str(fixture_dir / "t.dcf"), "--out", str(out), "--locales", "FIL"])
    d = apply_translations(copy.deepcopy(DCF), out, languages=[("EN", "English", None), ("FIL", "Filipino", "fil.json")])
    item = d["levels"][0]["records"][0]["items"][0]
    fil = {l["language"]: l["text"] for l in item["labels"]}["FIL"]
    assert fil == "Ano ang iyong kasalukuyang katayuan sa pag-aasawa?"
    assert "FIL:" in capsys.readouterr().out


# --------------------------------------------------------------------------------------
# Task 16b (2026-08-25) - Aug-21 paper LAYOUT rules.
#
# The Aug-21 papers print an interviewer directive BETWEEN the English question and its
# translation, print option rows one-per-line as "<box> Yes Oo <box> No Hindi", carry
# <...> routing notes inside the span, and condense some long paper paragraphs into the
# CSPro 255-char label. Task 17 measured what that costs: 857 F1 values carrying English
# directives, 262 grid-furniture values, 41 routing notes and Q75 emitted NOWHERE.
# These tests pin the five layout rules that fix it.
# --------------------------------------------------------------------------------------
# Segoe UI Symbol is the only font on this box that carries U+2610 (helv, cour, tiro and
# the CJK built-ins all render it as U+00B7), and conftest.make_pdf uses helv by design.
# The box-glyph rules therefore get their own PDF writer rather than a changed shared one.
BOX_FONT = r"C:/Windows/Fonts/seguisym.ttf"


def make_box_pdf(path, lines):
    """conftest.make_pdf with a font that actually renders the U+2610 ballot box."""
    if not os.path.exists(BOX_FONT):
        pytest.skip(f"no symbol font at {BOX_FONT} - cannot render U+2610")
    doc = fitz.open()
    page = doc.new_page()
    y = 60
    for ln in lines:
        page.insert_text((40, y), ln, fontsize=9, fontname="F0", fontfile=BOX_FONT)
        y += 14
    doc.save(str(path))
    doc.close()


def _item(name, text, values=None):
    node = {"name": name, "labels": [{"text": text}]}
    if values:
        node["valueSets"] = [{"name": f"{name}_VS1", "labels": [{"text": text}],
                              "values": [{"labels": [{"text": t}], "pairs": [{"value": str(i + 1)}]}
                                         for i, t in enumerate(values)]}]
    return node


Q5_CONDENSED = ("5. The maximum per capita rate amount for YAKAP is at Php 1,700 across "
                "private and public facilities (40% after first patient encounter). "
                "Based on your practice, is this enough?")

DCF2 = {"name": "T2", "labels": [{"text": "Tiny two"}], "levels": [{"name": "L",
        "labels": [{"text": "Level"}], "records": [{"name": "R", "labels": [{"text": "Record"}],
        "items": [
            _item("Q1_ROLE", "1. What is your role?"),
            _item("Q2_PREMIUM", "2. Do you pay premiums?", ["Yes", "No"]),
            _item("Q3_LICENSE", "3. Do you have a license?"),
            _item("Q4_PROVIDER", "4. Who is your provider?"),
            _item("Q5_ENOUGH", Q5_CONDENSED),
            _item("Q6_NEXT", "6. Next question"),
            _item("Q9_MISSING", "9. This question is not printed on the paper at all"),
        ]}]}]}

PAPER2 = [
    "1. What is your role? READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY. Ano ang iyong papel?",
    "2. Do you pay premiums? <proceed to Q51> Nagbabayad ka ba ng premium?",
    "\u2610 Yes Oo \u2610 No Hindi",
    "4. Who is your provider? Sino ang iyong provider?",
    "5. The maximum per capita rate amount for YAKAP is at Php 1,700 across private and",
    "public facilities. According to PhilHealth, 40% of the capitation amount will be",
    "released as the first tranche after the first patient encounter. Based on your",
    "practice, is this enough?",
    "Ang pinakamataas na halaga ay Php 1,700. Sapat ba ito sa iyong palagay?",
    "6. Next question Susunod na tanong",
    "3. Do you have a license? DO NOT READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY.",
]


@pytest.fixture
def layout(tmp_path):
    """The Aug-21 layout page + its anchors, extracted once per test."""
    (tmp_path / "t2.dcf").write_text(json.dumps(DCF2), encoding="utf-8")
    pdf = tmp_path / "F9-Tagalog_Layout_Aug21.pdf"
    make_box_pdf(pdf, PAPER2)
    anchors = ax.dcf_anchors(tmp_path / "t2.dcf")
    return anchors, ax.extract(pdf, anchors)


def _flags(r, key):
    row = next((f for f in r["flagged"] if f["key"] == key), None)
    return row["flags"] if row else None


# ------------------------------------------------------------ Step 1: directives --
def test_directive_between_english_and_translation_is_stripped(layout):
    """`12.2. ...? READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY. Ano ang ...?` - the
    directive is not a dcf anchor, so it used to land INSIDE the span. The candidate is
    the text after the LAST directive match."""
    _, r = layout
    assert r["clean"]["item:Q1_ROLE"] == "Ano ang iyong papel?"


def test_directive_with_no_translation_is_flagged_directive_only(layout):
    """The paper printed only the directive - there is no translation to import."""
    _, r = layout
    assert "item:Q3_LICENSE" not in r["clean"]
    assert _flags(r, "item:Q3_LICENSE") == ["directive-only"]


def test_directive_regexes_cover_the_phrases_harvested_from_the_papers():
    for phrase in ["READ OPTIONS OUT LOUD.", "DO NOT READ OPTIONS OUT LOUD.",
                   "SELECT ONE ANSWER ONLY.", "SELECT ALL THAT APPLY.", "DO NOT READ ALOUD",
                   "DO NOT ASK", "PROCEED TO Q51", "SKIP TO 51",
                   "Note to enumerator [do not read]:", "Enumerator Note:", "PROBE:",
                   "Amount in Pesos", "IF YES, SPECIFY"]:
        assert ax.has_directive(phrase), phrase
    # a plain translated sentence must never look like a directive
    for clean in ["Ano ang iyong papel?", "Nagbabayad ka ba ng premium?", "Oo", "Hindi",
                  "Ngaran han Enumerator"]:
        assert not ax.has_directive(clean), clean


def test_directive_is_excised_from_both_paper_layouts():
    """Tagalog/Cebuano print `English? DIRECTIVE. Translation?`; Ilocano prints
    `English? (Translation?) DIRECTIVE.` — so the directive is excised, not cut to. Every
    paper then repeats the directive in the local language, in ALL CAPS; that repeat is
    furniture too, and an unbroken >= 3-word capitalised run right after an English
    directive is the only place these papers put one."""
    assert ax.clean_span("? READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY. Ano ang "
                         "pangunahing tungkulin?") == "Ano ang pangunahing tungkulin?"
    assert ax.clean_span("? DO NOT READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY. AYAW "
                         "BASAHA ANG MGA PILIAN OG KUSOG. Unsa man ang imong tubag?"
                         ) == "Unsa man ang imong tubag?"
    assert ax.clean_span("? (No saan nga accredited, apay nga saan ka nga accredited?) "
                         "READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY. (BASAEN TI OPTIONS "
                         "ITI NAIPAAY. PILIEN AMIN NGA AGaplikar.)"
                         ) == "No saan nga accredited, apay nga saan ka nga accredited?"


def test_acronym_run_is_not_mistaken_for_a_translated_directive():
    """`BUCAS, GAMOT, NBB, ZBB` is four consecutive capitalised words inside a real
    question - the caps run is only ever consumed immediately after an English directive."""
    q = "Nakadungog ka na ba mahitungod sa BUCAS, GAMOT, NBB, ZBB?"
    assert ax.clean_span("? " + q) == q
    assert ax.skip_translated_directive(q, 0) == 0


def test_directive_residue_is_flagged_never_cleaned():
    assert "directive-bleed" in ax.qa_flags(
        "12.2. What is the main role of the public health unit?",
        "READ OPTIONS OUT LOUD. Ano ang pangunahing tungkulin?", set())


# ---------------------------------------------------- Step 2: one-line option rows --
def test_one_line_option_row_does_not_bleed_into_the_sibling(layout):
    """`<box> Yes Oo <box> No Hindi`: `No` is below MIN_BOUND so it never bounded `Yes`'s
    span and the value used to come out as `Oo No Hindi`."""
    _, r = layout
    assert r["clean"]["val:Q2_PREMIUM_VS1:1"] == "Oo"
    assert r["clean"]["val:Q2_PREMIUM_VS1:2"] == "Hindi"


def test_box_glyph_ends_a_span(layout):
    """A stem's translation is printed before the option row, so no span may cross a box."""
    _, r = layout
    assert r["clean"]["item:Q2_PREMIUM"] == "Nagbabayad ka ba ng premium?"
    assert ax.cut_at_box(" Oo \u2610 No Hindi") == " Oo "
    assert ax.cut_at_box(" plain span ") == " plain span "


def test_short_option_labels_anchor_only_behind_a_box_glyph():
    """Ilocano `no` means "if": the F1 ILO paper has 154 word-bounded `no`, only 67 of
    them behind a ballot box. Anchoring the bare word would chop 87 real translations."""
    text = "\u2610 No Hindi ... Ania ti aramidem no adda sakit"
    ntext, idx = ax.build_norm(text)
    hits = [m.start() for m in re.finditer(r"(?<![a-z0-9])no(?![a-z0-9])", ntext)]
    assert len(hits) == 2
    assert ax.behind_box(text, idx, hits[0]) and not ax.behind_box(text, idx, hits[1])


def test_grid_bleed_flag_fires_on_sibling_english_and_on_a_yes_no_pair():
    sibs = {"yes", "no"}
    assert "grid-bleed" in ax.qa_flags("Yes", "Oo No Hindi", {"yes", "no"}, siblings=sibs)
    assert ax.qa_flags("Yes", "Oo", {"yes", "no"}, siblings=sibs) == []
    assert "grid-bleed" in ax.qa_flags("11. Do you pay premiums?",
                                       "Nagbabayad ka ba? Yes Oo No Hindi", set())


# ------------------------------------------------------------ Step 3: routing notes --
def test_routing_note_is_stripped_from_the_span(layout):
    _, r = layout
    assert r["clean"]["item:Q2_PREMIUM"] == "Nagbabayad ka ba ng premium?"


def test_long_routing_note_is_stripped_and_residue_is_flagged():
    """The June-5 cleaner capped the note at 60 chars; the Aug-21 papers print
    `<Question for facilities that are only YAKAP-accredited, otherwise proceed to Q88>`."""
    assert ax.clean_span("Nagbabayad ka ba? <Question for facilities that are only "
                         "YAKAP-accredited, otherwise proceed to Q88>") == "Nagbabayad ka ba?"
    assert ax.clean_span("Sungbat \u2192 Q51") == "Sungbat"
    # the span cut the note in half - its `>` is past the next anchor, so there is no
    # closing bracket to match on and only the trailing-fragment rule can remove it
    assert ax.clean_span("Nagbabayad ka ba? <only for those who answered") == "Nagbabayad ka ba?"
    # but a note's TAIL (its `<` opened before this span) is furniture, not a translation
    assert "routing-note" in ax.qa_flags("Level 1", "Hindi ito naaangkop sa mga ospital>", set())


# -------------------------------------------------------- Step 4: condensed labels --
def test_condensed_label_anchors_on_its_prefix_and_is_flagged_never_clean(layout):
    """Q75's class: the dcf label is a CSPro-cap condensation of a longer paper paragraph,
    so the verbatim anchor is never found and the key used to be emitted NOWHERE."""
    _, r = layout
    assert "item:Q5_ENOUGH" not in r["clean"]
    # never clean: `label-condensed` leads, whatever else the ordinary QA flags add
    # (here `digit-mismatch` — the paper paragraph carries figures the label condensed away)
    assert _flags(r, "item:Q5_ENOUGH")[0] == "label-condensed"
    row = next(f for f in r["flagged"] if f["key"] == "item:Q5_ENOUGH")
    assert row["tr"].startswith("Ang pinakamataas na halaga")


def test_prefix_anchor_ends_the_previous_anchors_span(layout):
    """... and item:Q74's span used to run on into Q75's English paragraph."""
    _, r = layout
    assert r["clean"]["item:Q4_PROVIDER"] == "Sino ang iyong provider?"


def test_anchor_prefix_is_twelve_normalised_words_and_only_for_long_labels():
    assert ax.anchor_prefix(Q5_CONDENSED) == ("5 the maximum per capita rate amount for "
                                              "yakap is at php")
    assert ax.anchor_prefix("4. Who is your provider?") is None


# ----------------------------------------------------------- Step 5: not-in-paper --
def test_anchor_absent_from_the_paper_reaches_the_worklist(layout):
    _, r = layout
    assert _flags(r, "item:Q9_MISSING") == ["not-in-paper"]
    row = next(f for f in r["flagged"] if f["key"] == "item:Q9_MISSING")
    assert row["tr"] == "" and row["en"].startswith("9. This question")


def test_sub_min_emit_anchors_are_counted_not_flagged(fixture_dir):
    """Anchors shorter than MIN_EMIT are skipped as before - counted, never a worklist row."""
    anchors = dict(ax.dcf_anchors(fixture_dir / "t.dcf"))
    anchors["item:Q8_SEX"] = "Sex"
    r = ax.extract(fixture_dir / "src" / "F9-Tagalog_Tiny Survey_Aug21.pdf", anchors)
    assert r["sub_min_emit"] >= 1
    assert not any(f["key"] == "item:Q8_SEX" for f in r["flagged"])


# ------------------------------------------------------------- Step 6: MEAN + QA --
def test_mean_documents_every_new_flag():
    for fl in ("directive-bleed", "directive-only", "grid-bleed", "routing-note",
               "label-condensed", "not-in-paper"):
        assert ax.MEAN.get(fl), fl


def test_qa_report_counts_the_new_flags_per_locale(fixture_dir, tmp_path):
    out = tmp_path / "out2"
    (tmp_path / "t2.dcf").write_text(json.dumps(DCF2), encoding="utf-8")
    src = tmp_path / "src2"
    src.mkdir()
    make_box_pdf(src / "F9-Tagalog_Layout_Aug21.pdf", PAPER2)
    assert ax.main(["--source", str(src), "--instrument", "F9", "--dcf", str(tmp_path / "t2.dcf"),
                    "--out", str(out), "--locales", "FIL"]) == 0
    report = (out / "QA-REPORT.md").read_text(encoding="utf-8")
    assert "## Aug-21 layout flags per locale" in report
    assert "`label-condensed`" in report and "`not-in-paper`" in report
    clean = json.loads((out / "fil.json").read_text(encoding="utf-8"))
    assert not any(ax.has_directive(v) for v in clean.values())
    assert not any("<" in v or ">" in v for v in clean.values())


# ------------------------------------------- pre-flight ruling: no rule, no change --
def test_plain_span_is_untouched_by_the_layout_rules(tmp_path):
    """Where none of the five new rules fire the extractor's answer is what it always was."""
    dcf = {"name": "T3", "labels": [{"text": "Tiny three"}], "levels": [{"name": "L",
           "labels": [{"text": "Level"}], "records": [{"name": "R", "labels": [{"text": "Rec"}],
           "items": [_item("Q1_ASK", "1. What is the question?"),
                     _item("Q2_NEXT", "2. Next question")]}]}]}
    (tmp_path / "t3.dcf").write_text(json.dumps(dcf), encoding="utf-8")
    pdf = tmp_path / "F9-Tagalog_Plain_Aug21.pdf"
    make_pdf(pdf, ["1. What is the question? Ano ang tanong?", "2. Next question"])
    r = ax.extract(pdf, ax.dcf_anchors(tmp_path / "t3.dcf"))
    assert r["clean"]["item:Q1_ASK"] == "Ano ang tanong?"


# --------------------------------------------------------------------------------------
# Task 16c (2026-08-26) - the layer Task 17 attempt 2 measured as still defective: 249 of
# the 2,690 values --apply would write (9.3%). Root causes, in the order they cost rows:
#   1. one-word `val:` option labels ("PhilHealth", "Public", "Facility", "Monthly") are
#      >= MIN_BOUND, so they bound every span they occur in - including their occurrences
#      INSIDE a translated sentence, which cut 149 values mid-sentence;
#   2. two directive variants ("No. of days:", "Tick the category ...") were not in
#      DIRECTIVE_PATTERNS, and the papers' English NOTES (Q52/Q142) rode into the span;
#   3. the local-language repeat of a directive with no English original in front of it
#      was never consumed and never flagged.
# These tests pin the fixes. The box rules are asserted through the `text=` seam so the
# suite is not gated on a symbol font being installed.
# --------------------------------------------------------------------------------------

Q1_ACCEPT_EN = "1. Do you accept PhilHealth?"
DCF16C = {"name": "T4", "labels": [{"text": "Tiny four"}], "levels": [{"name": "L",
          "labels": [{"text": "Level"}], "records": [{"name": "R", "labels": [{"text": "Rec"}],
          "items": [_item("Q1_ACCEPT", Q1_ACCEPT_EN, ["PhilHealth", "Public"]),
                    _item("Q2_NOTE", "2. Which requirements were difficult?"),
                    _item("Q3_AFTER", "3. The question after the note")]}]}]}

PAGE16C = ("1. Do you accept PhilHealth? Tumatanggap ba kayo ng PhilHealth? "
           "\u2610 PhilHealth Oo \u2610 Public Pampubliko "
           "2. Which requirements were difficult? Alin sa mga sumusunod ang mahirap? "
           "These are the requirements for YAKAP/Konsulta accreditation outlined by DOH. "
           "Ito ang mga kinakailangan ayon sa DOH. "
           "3. The question after the note Ang tanong pagkatapos ng nota")


def _tr(r, key):
    """The value the extractor produced for `key`, clean or flagged.

    `Oo` against the English `PhilHealth` trips the June-5 `length-ratio` flag, so the
    box-boundary assertions have to look at the extracted TEXT, not at cleanliness.
    """
    if key in r["clean"]:
        return r["clean"][key]
    row = next((f for f in r["flagged"] if f["key"] == key), None)
    return row["tr"] if row else None


@pytest.fixture
def page16c(tmp_path):
    (tmp_path / "t4.dcf").write_text(json.dumps(DCF16C), encoding="utf-8")
    anchors = ax.dcf_anchors(tmp_path / "t4.dcf")
    return anchors, ax.extract("synthetic.pdf", anchors, text=PAGE16C)


# ------------------------------------------ Step 1: box-gated option boundaries (149) --
def test_one_word_option_label_bounds_a_span_only_behind_a_box(page16c):
    """`PhilHealth` is a one-word `val:` label and 10 normalised chars, so it is well
    above MIN_BOUND and bounded EVERY span it occurred in - including its occurrence
    inside the question's own translation, which is what cut 149 F1 values mid-sentence.
    A `val:` label of one word may bound a span only where it sits behind a ballot box."""
    _, r = page16c
    assert r["clean"]["item:Q1_ACCEPT"] == "Tumatanggap ba kayo ng PhilHealth?"
    assert _tr(r, "val:Q1_ACCEPT_VS1:1") == "Oo"
    assert _tr(r, "val:Q1_ACCEPT_VS1:2") == "Pampubliko"


def test_multi_word_option_labels_still_bound_without_a_box(fixture_dir):
    """The gate is for ONE-WORD labels only: `Single, never married` is not a word that
    turns up inside a sentence, and the papers print plenty of option rows with no box."""
    anchors = ax.dcf_anchors(fixture_dir / "t.dcf")
    r = ax.extract(fixture_dir / "src" / "F9-Tagalog_Tiny Survey_Aug21.pdf", anchors)
    assert r["clean"]["val:Q1_MARITAL_VS1:1"] == "Walang asawa, hindi kailanman nag-asawa"
    assert r["clean"]["val:Q1_MARITAL_VS1:2"] == "May asawa o nagsasama"


def test_extract_text_seam_matches_the_pdf_path(fixture_dir):
    """The `text=` seam the box tests use must be the same code path as a real PDF."""
    pdf = fixture_dir / "src" / "F9-Tagalog_Tiny Survey_Aug21.pdf"
    anchors = ax.dcf_anchors(fixture_dir / "t.dcf")
    assert ax.extract(pdf, anchors)["clean"] == \
        ax.extract("x.pdf", anchors, text=ax.pdf_text(pdf))["clean"]


# ---------------------------- Step 2: the two missing directives + local directives (92) --
def test_task_16c_directive_regexes_cover_the_grid_header_and_the_tick_note():
    for phrase in ["No. of days:", "No of days:", "No. of Days:",
                   "Tick the category that corresponds to the respondent\u2019s answer."]:
        assert ax.has_directive(phrase), phrase
    # the real Aug-21 layout: `<translation>? No of days: Enumerator note: Tick the ...`
    assert ax.clean_span("? Sa karaniwan, gaano katagal? No of days: Enumerator note: "
                         "Tick the category that corresponds to the respondent\u2019s "
                         "answer.") == "Sa karaniwan, gaano katagal?"


def test_local_language_directive_repeat_is_never_clean():
    """Where the paper prints ONLY the local rendering of the directive (no English
    original in front of it) skip_translated_directive() has nothing to hang off, so the
    repeat rides into the value: 26 rows across bcl/ceb/hil/ilo."""
    assert "local-directive" in ax.qa_flags(
        "23. Which of the submitted reports are actually used for decision-making?",
        "Arin sa mga tig sinumitir na report an tigagamit? BASAHON ASIN PILION AN MGA DAPAT",
        set())
    # ... and the mixed-case rendering, which is not ALL CAPS at all
    assert "local-directive" in ax.qa_flags(
        "36. What are the major challenges to improving quality?",
        "Ano an mga major na hamon sa kalidad? Dae pagbasahon ki makusog. Pilion an mga "
        "dapat na kasimbagan", set())


def test_acronym_run_inside_the_questions_own_english_is_not_a_local_directive():
    """`BUCAS GAMOT NBB` is three consecutive capitalised words inside a real question -
    the guard is that the run is also in the anchor's OWN English."""
    assert ax.qa_flags("Have you heard of BUCAS GAMOT NBB?",
                       "Nakadungog ka na ba mahitungod sa BUCAS GAMOT NBB?", set()) == []
    assert "local-directive" in ax.qa_flags(
        "Have you heard of the programme?", "Nakadungog ka na ba? PILIA ANG TANAN NGA "
        "APLIKADO", set())
    # ... and the COMBINATION: the value opens with the question's own acronym run and
    # still carries a real directive after it. Scanning only the FIRST caps run missed it.
    assert "local-directive" in ax.qa_flags(
        "Have you heard of BUCAS GAMOT NBB?",
        "Nakadungog ka na ba sa BUCAS GAMOT NBB? PILIA ANG TANAN NGA APLIKADO", set())
    assert ax.local_directive("Have you heard of BUCAS GAMOT NBB?",
                              "Nakadungog ka na ba sa BUCAS GAMOT NBB? "
                              "PILIA ANG TANAN NGA APLIKADO") is True


# ------------------------------------------------- Step 3: English notes / furniture (28) --
def test_english_note_ends_the_question_span(page16c):
    """`These are the requirements for YAKAP/Konsulta ... outlined by DOH.` is printed
    between the translation and the option rows in all seven papers. Excising it would
    glue the note's LOCAL translation onto the question label, so the note ENDS the span."""
    _, r = page16c
    assert r["clean"]["item:Q2_NOTE"] == "Alin sa mga sumusunod ang mahirap?"
    assert r["clean"]["item:Q3_AFTER"] == "Ang tanong pagkatapos ng nota"
    assert ax.cut_at_note("Alin? These are the requirements for YAKAP/Konsulta x") == "Alin? "


def test_english_note_residue_is_flagged_english_furniture():
    """The net under the span cut, exactly as `directive-bleed` is the net under
    strip_directives(): a recognised English note must never reach a clean value."""
    assert "english-furniture" in ax.qa_flags(
        "142. What are the most common ways you send referrals?",
        "Ano ang mga paraan? Our focus is specifically on referrals external to the", set())


def test_furniture_the_papers_place_inconsistently_is_flagged_not_cut():
    """Q44's capitation gloss is printed BEFORE the translation in five locales and AFTER
    it in ceb, so it may not end a span - five real translations would go with it."""
    span = ("? (Capitation is the amount per year per registered patient.) Batay sa iyong "
            "kaalaman, ano ang halaga?")
    assert ax.cut_at_note(span) == span
    assert "english-furniture" in ax.qa_flags("44. What is the capitation amount?",
                                              ax.clean_span(span), set())


# ------------------------------------------------------------------ Step 5: 16b polish --
def test_clean_span_drops_lone_parens_and_alnum_free_candidates():
    """The Ilocano layout parenthesises the translation; when the span cuts one side off,
    the surviving bracket is layout residue. A candidate with no alphanumerics at all is
    not a translation - it becomes an `empty` worklist row instead of a one-glyph value."""
    assert ax.clean_span("(Ania dagiti kadawyan a wagas") == "Ania dagiti kadawyan a wagas"
    assert ax.clean_span("Pisikal a slip ti referral)") == "Pisikal a slip ti referral"
    assert ax.clean_span(" ( ) ") == ""
    assert ax.clean_span(" \u2014 / ") == ""


def test_directive_only_needs_an_empty_residue():
    """`directive-only` says "the paper printed the directive and NO translation". A
    sub-MIN_EMIT residue is not nothing - a routing-note tail keeps `routing-note` alone."""
    dcf = {"name": "T5", "labels": [{"text": "T5"}], "levels": [{"name": "L",
           "labels": [{"text": "L"}], "records": [{"name": "R", "labels": [{"text": "R"}],
           "items": [_item("Q1_LIC", "1. Do you have a license?"),
                     _item("Q2_NEXT", "2. Next question")]}]}]}
    anchors = ax._anchors_from_dict(dcf)
    r = ax.extract("x.pdf", anchors,
                   text="1. Do you have a license? DO NOT READ ALOUD. sa?> 2. Next question")
    flags = _flags(r, "item:Q1_LIC")
    assert "directive-only" not in flags and "routing-note" in flags
    # the genuine case - nothing but the directive - still reads `directive-only`
    r2 = ax.extract("x.pdf", anchors,
                    text="1. Do you have a license? DO NOT READ ALOUD. 2. Next question")
    assert _flags(r2, "item:Q1_LIC") == ["directive-only"]


def test_grid_bleed_sibling_scan_ignores_two_char_siblings_on_a_long_option():
    """Ilocano `no` means "if". A 2-char sibling may only bleed into a one-line option
    row, which is what the sub-MIN_BOUND anchors are; on a longer option label it is a
    word of the language."""
    sibs = {"no", "yes"}
    assert ax.qa_flags("Other (specify)", "Dadduma pay no adda", {"other specify"},
                       siblings=sibs) == []
    assert "grid-bleed" in ax.qa_flags("Yes", "Oo No Hindi", {"yes", "no"}, siblings=sibs)


def test_trailing_note_strips_only_note_like_fragments():
    """`<18 years` is an option label, not the head of a routing note - stripping it
    silently produced a wrong value; it now falls through to the `routing-note` flag."""
    assert ax.clean_span("Nagbabayad ka ba? <only for those who answered") == "Nagbabayad ka ba?"
    assert ax.clean_span("Wala pa sa <18 years") == "Wala pa sa <18 years"
    assert "routing-note" in ax.qa_flags("Under 18 years", "Wala pa sa <18 years", set())


def test_other_label_in_helper_is_word_bounded_and_honours_min_len():
    """The three sibling/label scans in qa_flags are one helper (they had drifted apart)."""
    assert ax._other_label_in(" oo no hindi ", "yes", {"no"}) is True
    assert ax._other_label_in(" oo no hindi ", "yes", {"no"}, min_len=3) is False
    assert ax._other_label_in(" lalaking nars ", "male nurse", {"male"}) is False


def test_mean_documents_the_task_16c_flags():
    for fl in ("local-directive", "english-furniture"):
        assert ax.MEAN.get(fl), fl


# --------------------------------------------------------------------------------------
# Task 27 Step 0 (2026-08-26) - the two extractor defects Task 17 shipped and reported.
#
#   (a) OWN-MATCH. Task 16c's box gate decides whether a short `val:` label may BOUND a
#       span. It says nothing about whether the span that opens BEHIND the box is that
#       option's translation: `val:Q62_ENROLL_RESPONSIBILITY_VS1:02` ("Facility") matched
#       the F1 papers' ICF respondent-type row `☐ Facility Head`, which is boxed, and
#       shipped the English word `Head` into all seven maps.
#   (b) ORPHAN GLYPHS. 19 F1 write rows opened with a stray `"` or `(` the span boundary
#       left behind. clean_span()'s 16c rules only fire when the string has no partner
#       bracket AT ALL, so a nested pair (`(Ania ti naganmo? (Apellido, Ext)`) always
#       kept the orphan - the same fact Task 21b met in F2 and fixed with a COUNTING
#       trim, which now lives here and is shared.
# --------------------------------------------------------------------------------------
DCF27 = {"name": "T27", "labels": [{"text": "Tiny twenty-seven"}], "levels": [{"name": "L",
         "labels": [{"text": "Level"}], "records": [{"name": "R", "labels": [{"text": "Rec"}],
         "items": [_item("RESP_TYPE", "Respondent Type"),
                   _item("FH_NAME", "Name of the facility head"),
                   _item("Q1_ENROLL", "1. Whose responsibility is it to enroll patients?",
                         ["Facility", "Someone else"])]}]}]}

# The ICF respondent-type row FIRST (boxed, English on both sides of the box), the real
# option row second - the order the F1 papers print them in.
PAGE27 = ("Respondent Type \u2610 Facility Head \u2610 Inpatient "
          "1. Whose responsibility is it to enroll patients? "
          "Kaninong responsibilidad ang mag-enroll ng mga pasyente? "
          "\u2610 Facility Pasilidad \u2610 Someone else Ibang tao")


def test_short_option_anchors_own_match_may_not_be_english():
    """`Facility` is boxed twice; only the second box opens a translation. Before the
    own-match gate the first one won and `Head` was written to all seven F1 maps."""
    anchors = ax._anchors_from_dict(DCF27)
    r = ax.extract("x.pdf", anchors, text=PAGE27)
    assert r["clean"]["val:Q1_ENROLL_VS1:1"] == "Pasilidad"
    assert r["clean"]["val:Q1_ENROLL_VS1:2"] == "Ibang tao"


def test_english_own_match_is_a_worklist_row_when_the_paper_prints_no_translation():
    """No second box: the only span is English, so the key reaches the worklist with the
    reason instead of shipping the English (HIL is this case on the real F1 paper)."""
    anchors = ax._anchors_from_dict(DCF27)
    page = "Respondent Type \u2610 Facility Head \u2610 Inpatient"
    r = ax.extract("x.pdf", anchors, text=page)
    assert "val:Q1_ENROLL_VS1:1" not in r["clean"]
    assert "english-own-match" in _flags(r, "val:Q1_ENROLL_VS1:1")


def test_short_option_anchor_predicate_is_val_only_and_at_most_two_words():
    """The gate is for OPTION labels short enough that the papers print longer English
    phrases opening with them. An item label, or a label of three words or more, is not
    one of those and keeps Task 14's plain span rule."""
    assert ax.short_option_anchor("facility", ["val:Q1_ENROLL_VS1:1"]) is True
    assert ax.short_option_anchor("health center", ["val:Q1_X_VS1:1"]) is True
    assert ax.short_option_anchor("single never married", ["val:Q1_X_VS1:1"]) is False
    assert ax.short_option_anchor("facility", ["item:FACILITY"]) is False
    assert ax.short_option_anchor("facility", ["val:A_VS1:1", "item:FACILITY"]) is False


def test_own_match_is_english_reads_the_instruments_own_english_corpus():
    """"English" is not a language guess - it is "every word of this value is a word the
    dictionary's own English labels use". `Pasilidad` is not; `Head` is."""
    corpus = ax.english_words(ax._anchors_from_dict(DCF27))
    assert ax.own_match_is_english("Head", corpus) is True
    assert ax.own_match_is_english("Pasilidad", corpus) is False
    assert ax.own_match_is_english("", corpus) is False
    # a value carrying a non-ASCII letter is a local-language value whatever the corpus
    # says about its other words - the gate never holds one back
    assert ax.own_match_is_english("Headñ", {"headñ"}) is False


def test_long_option_anchors_own_match_is_left_alone():
    """A three-word option label is outside the gate: its span is emitted as it always
    was, so the rule cannot quietly delete a translation that merely looks English."""
    dcf = {"name": "T27b", "labels": [{"text": "T"}], "levels": [{"name": "L",
           "labels": [{"text": "L"}], "records": [{"name": "R", "labels": [{"text": "R"}],
           "items": [_item("FH_NAME", "Name of the facility head"),
                     _item("Q1_X", "1. Question one", ["Single, never married"])]}]}]}
    anchors = ax._anchors_from_dict(dcf)
    corpus = ax.english_words(anchors)
    assert ax.own_match_is_english("Facility Head", corpus) is True   # gate would fire
    r = ax.extract("x.pdf", anchors, text="Single, never married Facility Head")
    assert r["clean"]["val:Q1_X_VS1:1"] == "Facility Head"


def test_clean_span_drops_an_orphan_bracket_beside_a_balanced_group():
    """The 16c rules need the string to carry NO partner bracket; the Ilocano papers
    always leave one, so the trim counts instead."""
    assert ax.clean_span("(Ania ti naganmo? (Apellido, Ext)") == "Ania ti naganmo? (Apellido, Ext)"
    assert ax.clean_span("Kahibalo sa pasyente (") == "Kahibalo sa pasyente"
    assert ax.clean_span("Adda kadi inaramidyo iti GAMOT Package?) (") == \
        "Adda kadi inaramidyo iti GAMOT Package?"
    # a balanced group is still content, and the whole-group unwrap still fires
    assert ax.clean_span("Limitado (e.g., transportasion)") == "Limitado (e.g., transportasion)"


def test_clean_span_drops_an_orphan_double_quote():
    """12 F1 write rows opened with `" ` - the closing quote of an English label that is
    itself quoted, left at the head of the span. A BALANCED pair is the paper's own."""
    assert ax.clean_span('" Ang suporta ay hindi tumutugma') == "Ang suporta ay hindi tumutugma"
    assert ax.clean_span('Walang kailangan baguhin, \u201claging na-refer\u201d') == \
        "Walang kailangan baguhin, \u201claging na-refer\u201d"
    assert ax.clean_span('Sabi niya "tama" ito') == 'Sabi niya "tama" ito'
    # the quote hid the whole-group unwrap from the parenthesised Ilocano translation,
    # so the two rules run as one loop
    assert ax.clean_span('" (Kanayon a maitutop) ( )') == "Kanayon a maitutop"


def test_unbalanced_bracket_trim_is_shared_with_the_f2_extractor():
    """Task 21b wrote this trim for F2; Task 27 needs it for F1/F3/F4. One copy.

    F2 loads anchor_extract through importlib under its own module object, so the two
    function OBJECTS differ - what must hold is that the code lives in one file.
    """
    import inspect

    import anchor_extract_f2 as f2
    assert os.path.basename(inspect.getsourcefile(f2.trim_unbalanced_parens)) == \
        "anchor_extract.py"


def test_mean_documents_the_task_27_flag():
    assert ax.MEAN.get("english-own-match")
    assert "english-own-match" in ax.LAYOUT_FLAGS


# --------------------------------------------------------------------------------------
# Task 27 fix round 1, finding 1 (2026-08-26) - the roster CODES legend code glued to the
# tail of a span. The household-roster pages print the option list as a LEGEND
# (`01-Head 02-Spouse/Partner 03-Son/Daughter ...`, no ballot boxes at all), so a span
# that ends at the next option's English still carries that option's CODE: `Agum 03`.
# 154-166 F4 clean rows shipped that tail, 48 of them over a DIFFERENT live value
# (`val:Q34_RELATIONSHIP_VS1:02` = 'Agum 03' over the live 'Agum').
# The code is knowable without the paper - it is a code of a value set the anchor's own
# key names - so this is a layout rule, not a QA flag.
# --------------------------------------------------------------------------------------
def _roster_dcf():
    """A Q34-shaped roster item: zero-padded codes, and an item whose value-set name is
    the item name + `_VS1` (how every F1/F3/F4 dictionary is written)."""
    vs = {"name": "Q34_RELATIONSHIP_VS1",
          "labels": [{"text": "34. Relationship to Household Head"}],
          "values": [{"labels": [{"text": t}], "pairs": [{"value": c}]}
                     for c, t in [("01", "Head"), ("02", "Spouse/Partner"),
                                  ("03", "Son/Daughter"), ("04", "Brother/Sister")]]}
    item = {"name": "Q34_RELATIONSHIP",
            "labels": [{"text": "34. Relationship to Household Head"}], "valueSets": [vs]}
    return {"name": "T27F", "labels": [{"text": "Roster"}], "levels": [{"name": "L",
            "labels": [{"text": "Level"}], "records": [{"name": "R",
            "labels": [{"text": "Rec"}], "items": [item]}]}]}


# The Bicolano paper's legend, verbatim in shape: English code-label pairs with the
# translation after each one, no boxes.
ROSTER_PAGE27 = ("34. Relationship to Household Head "
                 "01-Head Payo 02-Spouse/Partner Agum 03-Son/Daughter Aki "
                 "04-Brother/Sister Tugang")


def test_value_set_codes_reads_the_legend_from_the_keys():
    codes = ax.value_set_codes(ax._anchors_from_dict(_roster_dcf()))
    assert codes["Q34_RELATIONSHIP_VS1"] == {"01", "02", "03", "04"}


def test_strip_legend_code_drops_the_next_options_code():
    vs = {"Q34_RELATIONSHIP_VS1": {"01", "02", "03", "04"}}
    keys = ["val:Q34_RELATIONSHIP_VS1:02"]
    assert ax.strip_legend_code("Agum 03", "Spouse/Partner", keys, vs) == "Agum"
    # zero-padding is a spelling of the number, not a different code
    assert ax.strip_legend_code("Agum 3", "Spouse/Partner", keys, vs) == "Agum"


def test_strip_legend_code_keeps_a_number_that_is_not_the_next_legend_code():
    """"No rule, no change": the anchor's OWN code, a number outside the legend, a
    number the English itself ends with, and a value that IS the number all survive."""
    vs = {"Q34_RELATIONSHIP_VS1": {"01", "02", "03", "04"}}
    own = ["val:Q34_RELATIONSHIP_VS1:03"]
    assert ax.strip_legend_code("Antas 3", "Level 3", own, vs) == "Antas 3"      # own code
    assert ax.strip_legend_code("Bayad 99", "Fee", own, vs) == "Bayad 99"        # not a code
    assert ax.strip_legend_code("Antas 2", "Level 2", own, vs) == "Antas 2"      # EN ends in it
    assert ax.strip_legend_code("02", "Spouse/Partner", own, vs) == "02"         # nothing left
    assert ax.strip_legend_code("", "Spouse/Partner", own, vs) == ""
    # a key with no value set of its own is untouched
    assert ax.strip_legend_code("Agum 03", "Spouse/Partner", ["item:NOT_A_ROSTER"], vs) == \
        "Agum 03"


def test_roster_legend_code_never_reaches_the_clean_map():
    """End to end: the shape that shipped `Agum 03` over the live `Agum`."""
    anchors = ax._anchors_from_dict(_roster_dcf())
    r = ax.extract("x.pdf", anchors, text=ROSTER_PAGE27)
    assert r["clean"]["val:Q34_RELATIONSHIP_VS1:02"] == "Agum"
    assert r["clean"]["val:Q34_RELATIONSHIP_VS1:03"] == "Aki"
    assert not [k for k, v in r["clean"].items() if re.search(r"\s\d{1,2}$", v)]


def test_item_anchor_uses_the_legend_of_its_own_value_sets():
    """`item:Q39_CIVIL_STATUS` = 'Civil Status 1' - the item key names no code, so the
    legend is looked up through `<ITEM>_VS*`. Stripping the 1 leaves the paper's English,
    which qa_flags then holds as `echo-english` instead of writing it to the map."""
    vs = ax.value_set_codes(ax._anchors_from_dict(_roster_dcf()))
    assert ax.strip_legend_code("Relasyon 01", "34. Relationship to Household Head",
                                ["item:Q34_RELATIONSHIP"], vs) == "Relasyon"
    assert ax.strip_legend_code("Relasyon 01", "34. Relationship to Household Head",
                                ["vs:Q34_RELATIONSHIP_VS1"], vs) == "Relasyon"


# ---------------------------------------------------------------- Task 32b --
# The Waray Aug-21 papers print the paper's question number in front of the LOCAL
# row as well as the English one, so the span opens `26. Mayda ba …`. 154 F4 WAR
# values shipped that prefix in v3.2.0, seven of them printing a number that
# contradicts the key's own question number.


def _numbered_dcf():
    """Three prose questions whose ENGLISH labels carry the paper's number — the
    shape every F4 household page uses (363 of the 1366 F4 anchors)."""
    items = [
        {"name": "Q27_REFRIGERATOR",
         "labels": [{"text": "27. Does the family own a refrigerator/freezer?"}]},
        {"name": "Q28_TELEVISION",
         "labels": [{"text": "28. Does the family own a television?"}]},
        {"name": "Q29_YEARS_HERE",
         "labels": [{"text": "29. How long have you lived in this barangay?"}]},
    ]
    return {"name": "T32B", "labels": [{"text": "Household"}], "levels": [{"name": "L",
            "labels": [{"text": "Level"}], "records": [{"name": "R",
            "labels": [{"text": "Rec"}], "items": items}]}]}


# Q27's local row prints 26 (the Waray paper's own numbering runs one behind the
# CAPI's), Q28's prints 28, and Q29's translation legitimately opens with a number
# that is not a question-number token.
NUMBERED_PAGE = ("27. Does the family own a refrigerator/freezer? "
                 "26. Mayda ba refrigerator o freezer an pamilya? "
                 "28. Does the family own a television? "
                 "28. Mayda ba telebisyon an pamilya? "
                 "29. How long have you lived in this barangay? "
                 "2 ka tuig ngan sobra pa")


def test_strip_question_number_silently_strips_a_number_that_matches_the_key():
    tr, mismatch = ax.strip_question_number(
        "27. Mayda ba kamo refrigerator?",
        "27. Does the family own a refrigerator/freezer?", ["item:Q27_REFRIGERATOR"])
    assert tr == "Mayda ba kamo refrigerator?"
    assert mismatch is False
    # the same value reached through the value-set key
    assert ax.strip_question_number(
        "27. Mayda ba kamo refrigerator?",
        "27. Does the family own a refrigerator/freezer?",
        ["vs:Q27_REFRIGERATOR_VS1"]) == ("Mayda ba kamo refrigerator?", False)


def test_strip_question_number_flags_a_number_that_contradicts_the_key():
    """The seven war rows that shipped in v3.2.0 printing the wrong number."""
    tr, mismatch = ax.strip_question_number(
        "26. Mayda ba kamo refrigerator?",
        "27. Does the family own a refrigerator/freezer?", ["item:Q27_REFRIGERATOR"])
    assert tr == "Mayda ba kamo refrigerator?"
    assert mismatch is True


def test_strip_question_number_leaves_a_plain_leading_number_alone():
    """"No rule, no change": a value that merely begins with a number is content."""
    for val in ("2 ka tuig", "1.5 kilometro", "27.Mayda ba kamo refrigerator?", "27.", "27. "):
        assert ax.strip_question_number(val, "29. How long?", ["item:Q29_YEARS_HERE"]) == \
            (val, False)


def test_strip_question_number_flags_a_key_that_carries_no_question_number():
    """A number that cannot be checked is never silently written: the war
    `val:ENUM_RESULT_*_VS1:4` grid-bleed rows (`1. Kumpleto 2. Gin-usod …`)."""
    tr, mismatch = ax.strip_question_number(
        "1. Kumpleto 2. Gin-usod", "Withdraw Participation/Consent",
        ["val:ENUM_RESULT_FINAL_VISIT_VS1:4"])
    assert tr == "Kumpleto 2. Gin-usod"
    assert mismatch is True


def test_strip_question_number_keeps_a_sub_numbered_key_in_step():
    keys = ["item:Q45_1_PIN_REG_WHEN"]
    assert ax.strip_question_number("45.1. San-o kamo nagparehistro?",
                                    "45.1 When did you register?", keys)[1] is False
    assert ax.strip_question_number("45.2. San-o kamo nagparehistro?",
                                    "45.1 When did you register?", keys)[1] is True
    # the paper often prints only the parent number; that is not a contradiction
    assert ax.strip_question_number("45. San-o kamo nagparehistro?",
                                    "45.1 When did you register?", keys)[1] is False


def test_strip_question_number_refuses_to_hide_an_english_echo():
    """A paper that reprints the ENGLISH under its own number is an `echo-english`
    worklist row; stripping the number would make the echo invisible to qa_flags()
    and ship English as a translation — the worst class in MEAN."""
    en = "30. Name (Write the complete name of HH member)"
    assert ax.strip_question_number(en, en, ["item:Q30_NAME"]) == (en, False)


def test_paper_question_number_never_reaches_the_clean_map():
    """End to end: the shape that shipped `26. Mayda ba …` into war.json."""
    anchors = ax._anchors_from_dict(_numbered_dcf())
    r = ax.extract("x.pdf", anchors, text=NUMBERED_PAGE)
    # the matching number is stripped silently and the row stays clean
    assert r["clean"]["item:Q28_TELEVISION"] == "Mayda ba telebisyon an pamilya?"
    # a value that merely starts with a digit is untouched
    assert r["clean"]["item:Q29_YEARS_HERE"] == "2 ka tuig ngan sobra pa"
    # the contradicting number is stripped AND held
    assert "item:Q27_REFRIGERATOR" not in r["clean"]
    held = [f for f in r["flagged"] if f["key"] == "item:Q27_REFRIGERATOR"]
    assert len(held) == 1
    assert "paper-number-mismatch" in held[0]["flags"]
    assert held[0]["tr"] == "Mayda ba refrigerator o freezer an pamilya?"
    # and no clean value anywhere still opens with a question-number token
    assert not [k for k, v in r["clean"].items() if re.match(r"^\d{1,3}[a-z]?\.\s", v)]


def test_mean_documents_the_task_32b_flag():
    assert "paper-number-mismatch" in ax.MEAN
    assert "paper-number-mismatch" in ax.LAYOUT_FLAGS


# ---------------------------------------------------------------- Task 33b --
# The Aug-21 TAGALOG papers are bilingual in a way the other six are not: every
# question and every option prints the English first and puts the Filipino gloss
# in square brackets after it (`Male [Lalaki]`). The brackets are the paper's
# gloss delimiter, not sentence punctuation, and 459 F4 `fil` values shipped in
# v3.2.1 wearing them - about half of everything an enumerator reads aloud.
# F3's Aug-21 Tagalog paper has 503 such lines, so the rule is Wave 4's
# prerequisite too.


def test_strip_wrapping_brackets_drops_one_whole_value_pair():
    """The shape the whole task is about, on an option label and on a sentence."""
    assert ax.strip_wrapping_brackets("[Lalaki]") == "Lalaki"
    assert ax.strip_wrapping_brackets("[Babae]") == "Babae"
    assert ax.strip_wrapping_brackets("[Ano po ang inyong kasarian nang ipinanganak?]") == \
        "Ano po ang inyong kasarian nang ipinanganak?"
    # surrounding whitespace is layout, not content
    assert ax.strip_wrapping_brackets("  [Lalaki]  ") == "Lalaki"


def test_strip_wrapping_brackets_keeps_internal_brackets():
    """A bracket INSIDE the value is the translator's own aside and is content.

    `[tukuyin]` is what the fil papers print for "(specify)"; two side-by-side
    groups open and close with a bracket but are not ONE pair, so counting `[`
    against `]` is not enough - the opening bracket's partner must be the last
    character of the value.
    """
    for val in ("Kung oo, [tukuyin]",
                "[Kung oo] tukuyin [ang sagot]",
                "Iba pa [tukuyin] - ilagay sa ibaba"):
        assert ax.strip_wrapping_brackets(val) == val
    # a wrap around a value that ALSO carries an internal pair loses only the wrap
    assert ax.strip_wrapping_brackets("[Kung oo, [tukuyin] ang sagot]") == \
        "Kung oo, [tukuyin] ang sagot"


def test_strip_wrapping_brackets_trims_a_double_wrap_once_and_leaves_orphans():
    """Two pairs are not the paper's convention, and an orphan is a cut span.

    Both shapes must stay visibly wrong rather than be silently repaired: one
    pass off a double wrap still shows a bracket on screen (and in the worklist),
    and an unbalanced value falls through to the existing trim_unbalanced_*
    helpers, which know parentheses and quotes and deliberately not brackets.
    """
    assert ax.strip_wrapping_brackets("[[Lalaki]]") == "[Lalaki]"
    for orphan in ("[Madaling mabili/makuha", "para sa bawat Filipino]",
                   "[Kung oo] tukuyin ang sagot]"):
        assert ax.strip_wrapping_brackets(orphan) == orphan
    # nothing but the delimiters is not a translation - never emptied here
    assert ax.strip_wrapping_brackets("[]") == "[]"


def test_strip_wrapping_brackets_leaves_parentheses_to_their_own_rule():
    """Parentheses are NOT this rule's business: the Ilocano layout prints whole
    translations inside ( ), and clean_span's Task-16c/27 loop already owns that
    case with its own counting trims."""
    for val in ("(Lalaki)", "(Ania ti naganmo?)", "Kung oo (tukuyin)"):
        assert ax.strip_wrapping_brackets(val) == val


def test_clean_span_strips_the_gloss_brackets():
    """The rule lives in clean_span, so every instrument gets it (F3 next)."""
    assert ax.clean_span("[Lalaki]") == "Lalaki"
    assert ax.clean_span(" [Ano po ang inyong edad?] ") == "Ano po ang inyong edad?"
    assert ax.clean_span("Kung oo, [tukuyin]") == "Kung oo, [tukuyin]"


def _bracketed_dcf():
    """Three prose questions off the F4 household pages, English labels only."""
    items = [
        {"name": "Q3_SEX", "labels": [{"text": "3. What is your sex at birth?"}],
         "valueSets": [{"name": "Q3_SEX_VS1",
                        "labels": [{"text": "3. What is your sex at birth?"}],
                        "values": [{"labels": [{"text": "Male person"}],
                                    "pairs": [{"value": "1"}]},
                                   {"labels": [{"text": "Female person"}],
                                    "pairs": [{"value": "2"}]}]}]},
        {"name": "Q4_OTHER_SPECIFY",
         "labels": [{"text": "4. If yes, specify the other reason"}]},
        {"name": "Q5_UNBRACKETED",
         "labels": [{"text": "5. How many years have you lived here?"}]},
    ]
    return {"name": "T33B", "labels": [{"text": "Household"}], "levels": [{"name": "L",
            "labels": [{"text": "Level"}], "records": [{"name": "R",
            "labels": [{"text": "Rec"}], "items": items}]}]}


# The bilingual Tagalog layout, verbatim in shape: English, then the gloss in
# brackets. Q4's gloss carries an INTERNAL pair; Q5's row has no brackets at all.
BRACKETED_PAGE = ("3. What is your sex at birth? "
                  "[Ano po ang inyong kasarian nang ipinanganak?] "
                  "Male person [Lalaki na tao] "
                  "Female person [Babae na tao] "
                  "4. If yes, specify the other reason "
                  "[Kung oo, [tukuyin] ang ibang dahilan] "
                  "5. How many years have you lived here? "
                  "Ilang taon ka nang naninirahan dito?")


def test_gloss_brackets_never_reach_the_clean_map():
    """End to end: the shape that shipped `[Lalaki]` into fil.json 459 times."""
    anchors = ax._anchors_from_dict(_bracketed_dcf())
    r = ax.extract("x.pdf", anchors, text=BRACKETED_PAGE)
    assert r["clean"]["item:Q3_SEX"] == "Ano po ang inyong kasarian nang ipinanganak?"
    assert r["clean"]["vs:Q3_SEX_VS1"] == "Ano po ang inyong kasarian nang ipinanganak?"
    assert r["clean"]["val:Q3_SEX_VS1:1"] == "Lalaki na tao"
    assert r["clean"]["val:Q3_SEX_VS1:2"] == "Babae na tao"
    # the internal pair survives; only the wrap goes
    assert r["clean"]["item:Q4_OTHER_SPECIFY"] == "Kung oo, [tukuyin] ang ibang dahilan"
    # a row the paper never bracketed is untouched
    assert r["clean"]["item:Q5_UNBRACKETED"] == "Ilang taon ka nang naninirahan dito?"
    # and no clean value anywhere is still wholly wrapped
    assert not [k for k, v in r["clean"].items()
                if v.startswith("[") and v.endswith("]")]


def test_the_bracket_strip_cannot_hide_an_english_echo():
    """Why this rule needs no echo guard, unlike Task 32b's number strip.

    qa_flags() judges through norm_for_match(), which folds every non-alnum
    character to a space - so `[Male person]` and `Male person` were ALREADY the
    same string to it. Stripping the pair therefore cannot change a single flag
    decision: an English gloss is `echo-english` before the strip and after it.
    """
    en = "Male person"
    assert norm_for_match("[Male person]") == norm_for_match(en)
    assert "echo-english" in ax.qa_flags(en, "[Male person]", {norm_for_match(en)})
    assert "echo-english" in ax.qa_flags(en, "Male person", {norm_for_match(en)})


# The Tagalog roster legend prints the gloss and then the NEXT option's code
# (`01-Head [Puno ng sambahayan] 02-Spouse/Partner …`), so while the code is still
# attached the value is not wholly wrapped and clean_span cannot see the pair.
# 10 F4 FIL rows (Q45.1, Q45.2) reached the clean map that way.
GLOSSED_ROSTER_PAGE = ("34. Relationship to Household Head "
                       "01-Head [Puno ng sambahayan] 02-Spouse/Partner [Asawa] "
                       "03-Son/Daughter [Anak] 04-Brother/Sister [Kapatid]")


def test_a_legend_code_cannot_hide_the_gloss_brackets():
    anchors = ax._anchors_from_dict(_roster_dcf())
    r = ax.extract("x.pdf", anchors, text=GLOSSED_ROSTER_PAGE)
    # `Head` is a one-word val label and anchors only behind a ballot box (Task 16c),
    # so this legend page yields 02-04 - the same three the Task-27 legend test uses.
    assert r["clean"]["val:Q34_RELATIONSHIP_VS1:02"] == "Asawa"
    assert r["clean"]["val:Q34_RELATIONSHIP_VS1:03"] == "Anak"
    assert r["clean"]["val:Q34_RELATIONSHIP_VS1:04"] == "Kapatid"
    assert not [k for k, v in r["clean"].items()
                if v.startswith("[") and v.endswith("]")]


DOUBLE_WRAPPED_PAGE = ("5. How many years have you lived here? "
                       "[[Ilang taon ka nang naninirahan dito?]]")


def test_a_double_wrap_still_ships_one_visible_pair():
    """The second look must not turn into a second strip.

    A value the paper wrapped twice is not the gloss convention, so it stays
    visibly wrong on screen and in the worklist rather than being repaired into a
    shape no paper printed. The guard is that extract() only looks again when the
    legend-code or question-number stripper actually fired.
    """
    items = [{"name": "Q5_UNBRACKETED",
              "labels": [{"text": "5. How many years have you lived here?"}]}]
    dcf = {"name": "T33B2", "labels": [{"text": "H"}], "levels": [{"name": "L",
           "labels": [{"text": "Level"}], "records": [{"name": "R",
           "labels": [{"text": "Rec"}], "items": items}]}]}
    r = ax.extract("x.pdf", ax._anchors_from_dict(dcf), text=DOUBLE_WRAPPED_PAGE)
    assert r["clean"]["item:Q5_UNBRACKETED"] == "[Ilang taon ka nang naninirahan dito?]"


# ----------------------------------------------------------------- Task 40 --
# STEP 0: the five classes Task 28 could only HOLD on F4 (task-28-report.md's hold
# table). Every page string below is copied verbatim out of the Aug-21 PDFs
# (`pdf_text()` output), so these are the papers' real layouts, not a paraphrase:
#   1. the GAMOT applicability NOTE riding into Q70-Q73's span (49 held rows);
#   2. the Q17 English definition block printed under the question (8 rows);
#   3. the Q18 income/amount directive (`Approximate amount:` + the Tick note, 5);
#   4. the local-language SELECT-ALL repeat glued to the question and its option
#      rows (Q66/Q74, 23 rows) - all seven papers print one, none of them in CAPS,
#      so skip_translated_directive()'s ALL-CAPS rule never saw it;
#   5. the orphan closing quote glyph on HIL Q28/Q29 (4 rows).
# F3's Aug-21 papers print the same furniture (six SELECT-ALL repeats per paper
# against F4's two), so the rules are Wave 4's prerequisite as much as F4's
# follow-up.


def _t40_dcf(items):
    return {"name": "T40", "labels": [{"text": "Household"}],
            "levels": [{"name": "L", "labels": [{"text": "Level"}],
                        "records": [{"name": "R", "labels": [{"text": "Rec"}],
                                     "items": items}]}]}


_Q70 = [{"name": "Q70_GAMOT_SOURCE",
         "labels": [{"text": "70. If yes, what are your sources of information "
                             "for GAMOT Package?"}],
         "valueSets": [{"name": "Q70_GAMOT_SOURCE_VS1",
                        "labels": [{"text": "70. If yes, what are your sources of "
                                            "information for GAMOT Package?"}],
                        "values": [{"labels": [{"text": "News"}],
                                    "pairs": [{"value": "01"}]}]}]}]

# F4-Tagalog, Q70: the note is printed AFTER the translation.
FIL_GAMOT_PAGE = (
    "70. If yes, what are your sources of information for GAMOT Package? "
    "Kung oo, ano ang iyong mga pinagkunan ng impormasyon tungkol sa GAMOT Package? "
    "Enumerator: Applicable only to respondents in areas with GAMOT facility "
    "Enumerator: Naaangkop lamang sa mga respondent sa mga lugar na may GAMOT facility. "
    "☐ News [Balita] ☐ Health center/facility")

# F4-Cebuano, same question: the note is printed BEFORE it.
CEB_GAMOT_PAGE = (
    "70. If yes, what are your sources of information for GAMOT Package? "
    "Enumerator: Applicable only to respondents in areas with GAMOT facility "
    "Kung oo, unsa ang imong mga tinubdan sa impormasyon bahin aning GAMOT Package? "
    "Enumerator. Angay lamang sa respondents sa mga lugar nga naay GAMOT "
    "☐ News Balita ☐ Health center/facility")


def test_applicability_note_ends_the_question_span():
    """Class 1. `Applicable only to respondents ...` is note-layer content
    (note:const:_GAMOT_FAC), not question text, and every paper prints it between
    the question's translation and the option rows - so it ends the span exactly
    as a ballot box does."""
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_Q70)), text=FIL_GAMOT_PAGE)
    assert r["clean"]["item:Q70_GAMOT_SOURCE"] == (
        "Kung oo, ano ang iyong mga pinagkunan ng impormasyon tungkol sa GAMOT Package?")
    assert r["clean"]["vs:Q70_GAMOT_SOURCE_VS1"] == r["clean"]["item:Q70_GAMOT_SOURCE"]
    assert r["clean"]["val:Q70_GAMOT_SOURCE_VS1:01"] == "Balita"


def test_a_leading_applicability_note_is_held_not_shipped():
    """The same rule, the Cebuano layout: with the note in FRONT of the
    translation there is nothing left to import, so the row must reach the
    worklist rather than ship the English note as a translation."""
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_Q70)), text=CEB_GAMOT_PAGE)
    assert "item:Q70_GAMOT_SOURCE" not in r["clean"]
    held = [f for f in r["flagged"] if f["key"] == "item:Q70_GAMOT_SOURCE"]
    assert held and "Applicable only" not in held[0]["tr"]
    assert not [v for v in r["clean"].values() if "Applicable only" in v]


_Q17 = [{"name": "Q17_DECISION_MAKER",
         "labels": [{"text": "17. Who takes the most responsibility for making the "
                             "decisions regarding healthcare in your household?"}]},
        {"name": "Q18_INCOME_AMOUNT",
         "labels": [{"text": "18. In the past 6 months, what is your average monthly "
                             "household income? Please specify in Philippine pesos."}]}]

# F4-Tagalog Q17/Q18, verbatim page order.
FIL_Q17_Q18_PAGE = (
    "17. Who takes the most responsibility for making the decisions regarding "
    "healthcare in your household? "
    "Sino po ang may pinakamaraming responsibilidad sa paggawa ng mga desisyon "
    "tungkol sa pangangalaga sa kalusugan sa inyong sambahayan? "
    "This is the person who makes decisions on health in the family: for example, "
    "yearly immunizations, manages hospital finances, etc. "
    "Ito ang taong gumagawa ng mga desisyon tungkol sa kalusugan ng pamilya: "
    "halimbawa, taunang bakuna, pamamahala sa gastusin sa ospital, atbp. "
    "READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY. BASAHIN ANG MGA OPSYON NG "
    "MALINAW. PUMILI NG ISA LAMANG "
    "18. In the past 6 months, what is your average monthly household income? "
    "Please specify in Philippine pesos. "
    "Sa nakalipas na 6 na buwan, ano ang iyong karaniwang buwanang kita ng "
    "sambahayan? Pakitukoy sa Philippine pesos. "
    "Approximate amount: [Tinatayang halaga:] "
    "Enumerator note: Tick the income category that corresponds to the "
    "respondent’s approximate household income. "
    "Paalala sa enumerator: Lagyan ng tsek ang kategorya ng kita na tumutugma sa "
    "tinatayang kita ng sambahayan ng respondent. "
    "☐ < PhP12,030")


def test_definition_block_ends_the_question_span():
    """Class 2. The English definition block under Q17 is furniture printed
    between the translation and the option rows, and the paper prints its LOCAL
    half straight after it - so cutting keeps the question and drops both halves,
    where excising would glue the local half onto the label."""
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_Q17)), text=FIL_Q17_Q18_PAGE)
    assert r["clean"]["item:Q17_DECISION_MAKER"] == (
        "Sino po ang may pinakamaraming responsibilidad sa paggawa ng mga desisyon "
        "tungkol sa pangangalaga sa kalusugan sa inyong sambahayan?")


def test_income_amount_directive_ends_the_question_span():
    """Class 3. `Approximate amount:` is the answer-box caption, and everything
    after it on the page belongs to the enumerator, not the respondent.

    The trailing full stop goes with clean_span's own edge strip - the value is a
    sentence, not a question, and `.strip(' .:;,-')` has always removed it."""
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_Q17)), text=FIL_Q17_Q18_PAGE)
    assert r["clean"]["item:Q18_INCOME_AMOUNT"] == (
        "Sa nakalipas na 6 na buwan, ano ang iyong karaniwang buwanang kita ng "
        "sambahayan? Pakitukoy sa Philippine pesos")


def test_the_income_tick_directive_variant_is_recognised():
    """The papers print `Tick the INCOME category that corresponds …`; Task 16c's
    pattern knew only `Tick the category …`. Widened so the row is still caught
    where a paper prints the directive without the `Approximate amount:` caption."""
    assert ax.has_directive("Tick the income category that corresponds to the "
                            "respondent’s approximate household income.")
    assert ax.has_directive("Tick the category that corresponds to the answer.")


# Class 4: the local SELECT-ALL repeat, one rendering per Aug-21 paper. Verbatim
# from the seven F4/F3 dumps - none is ALL CAPS, so skip_translated_directive()
# never saw it, and every one of them is printed AFTER the question's translation.
LOCAL_SELECT_ALL_REPEATS = [
    ("FIL", "Piliin ang lahat ng naaangkop."),
    ("FIL", "Piliin ang lahat na naaangkop."),
    ("BCL", "Pilion an dapat."),
    ("BCL", "Pilion an mga dapat na kasimbagan."),
    ("BIS", "Pili-a ang tanan nga pwede"),
    ("BIS", "Pilia tanang pwede."),
    ("BIS", "Pilia-ang tanan nga pwede"),
    ("CEB", "Pilia ang tanan nga mo apply."),
    ("WAR", "Pilia an ngatanan nga aplikado."),
    ("HIL", "Pilia ang tanan nga naga‑aplikar."),
    ("HIL", "Pili-a ang tanan nga nagakaangay."),
    ("HIL", "Pumili sang tanan nga nagaangay."),
    ("ILO", "Pilien amin nga agaplikar."),
]


@pytest.mark.parametrize("code,repeat", LOCAL_SELECT_ALL_REPEATS)
def test_every_papers_local_select_all_repeat_bounds_a_span(code, repeat):
    span = "Asa ka kasagarang mopalit sa imong mga tambal? " + repeat
    assert ax.cut_at_local_directive(span).strip() == \
        "Asa ka kasagarang mopalit sa imong mga tambal?"


def test_ordinary_words_are_not_read_as_a_select_all_repeat():
    """The rule keys on `Pili…/Pumili` + an article, so the language's own words
    are untouched - `Pilipinas`, `pilian` (the options) and a bare `Pumili` are
    not directives, and a span with none of the shape keeps every character."""
    for span in ("Ilan ang miyembro ng pamilya sa Pilipinas ngayon?",
                 "Ano ang pilian mo sa mga sumusunod?",
                 "Pilipinas ang bansa nga akong gipuy-an"):
        assert ax.cut_at_local_directive(span) == span


_Q66 = [{"name": "Q66_WHERE_BUY",
         "labels": [{"text": "66. Where do you usually buy or receive your medicines? "
                             "Select all that apply."}],
         "valueSets": [{"name": "Q66_WHERE_BUY_VS1",
                        "labels": [{"text": "66. Where do you usually buy or receive "
                                            "your medicines? Select all that apply."}],
                        "values": [{"labels": [{"text": "Public Hospital"}],
                                    "pairs": [{"value": "1"}]},
                                   {"labels": [{"text": "Private Hospital"}],
                                    "pairs": [{"value": "2"}]}]}]}]

CEB_Q66_PAGE = (
    "66. Where do you usually buy or receive your medicines? Select all that apply. "
    "Asa ka kasagarang mopalit o modawat sa imong mga tambal? "
    "Pilia ang tanan nga mo apply. "
    "☐ Public Hospital Publikong ospital "
    "☐ Private Hospital Pribadong ospital")


def test_local_select_all_repeat_never_reaches_the_clean_map():
    """Class 4 end to end, including the OPTION rows the ruling names: the repeat
    is furniture wherever the paper glues it, so no clean value may carry one."""
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_Q66)), text=CEB_Q66_PAGE)
    assert r["clean"]["item:Q66_WHERE_BUY"] == \
        "Asa ka kasagarang mopalit o modawat sa imong mga tambal?"
    assert r["clean"]["val:Q66_WHERE_BUY_VS1:1"] == "Publikong ospital"
    assert r["clean"]["val:Q66_WHERE_BUY_VS1:2"] == "Pribadong ospital"
    assert not [v for v in r["clean"].values() if ax.LOCAL_SELECT_ALL.search(v)]


def test_a_surviving_local_select_all_repeat_is_still_flagged():
    """The net under the cut, exactly as `directive-bleed` is the net under
    strip_directives(): a rendering the cut did not reach must never be clean."""
    assert ax.local_directive("66. Where do you usually buy your medicines?",
                              "Asa ka mopalit? Pilia ang tanan nga mo apply")


# Class 5: the HIL paper closes Q28/Q29 with a quote glyph that opens nowhere.
def test_an_orphan_closing_quote_is_trimmed_from_the_tail():
    assert ax.trim_unbalanced_quotes(
        "May kaugalingon bala ang pamilya nga telebisyon?”") == \
        "May kaugalingon bala ang pamilya nga telebisyon?"
    assert ax.trim_unbalanced_quotes(
        "“May kaugalingon bala ang pamilya nga washing machine?") == \
        "May kaugalingon bala ang pamilya nga washing machine?"


def test_a_balanced_curly_quotation_is_content_and_survives():
    """A pair is the paper's own quotation - only an odd count is layout residue,
    the same rule the straight-quote trim has always used."""
    for val in ("“Ang mga pasyente permi ginapadala sa husto nga lugar”",
                "Nagsiling siya nga “wala” sang bulong"):
        assert ax.trim_unbalanced_quotes(val) == val


_Q28 = [{"name": "Q28_TELEVISION",
         "labels": [{"text": "28. Does the family own a television set?"}]},
        {"name": "Q29_WASHING_MACHINE",
         "labels": [{"text": "29. Does the family own a washing machine?"}]}]

HIL_Q28_PAGE = (
    "28. Does the family own a television set? "
    "May kaugalingon bala ang pamilya nga telebisyon?” "
    "☐ Yes, I/ we have Oo, may ara kami "
    "29. Does the family own a washing machine? "
    "May kaugalingon bala ang pamilya nga washing machine?” "
    "☐ Yes, I/ we have Oo, may ara kami")


def test_orphan_quote_never_reaches_the_clean_map():
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_Q28)), text=HIL_Q28_PAGE)
    assert r["clean"]["item:Q28_TELEVISION"] == \
        "May kaugalingon bala ang pamilya nga telebisyon?"
    assert r["clean"]["item:Q29_WASHING_MACHINE"] == \
        "May kaugalingon bala ang pamilya nga washing machine?"


# The same class on the F3 papers, found while measuring the F3 write set: two more
# English blocks printed verbatim on all seven papers between a question's translation
# and its option rows, and one directive variant the list did not know.
#   * `If yes, indicate the amount spent` (F3 Q97.2 / Q115.2) - `IF YES, INDICATE` was
#     already a directive, but excising just those two words left ` the amount spent`
#     inside the value and the local repeat behind it, on the two keys Task 40's own
#     provenance test names (`item:Q972_SOURCES`, `item:Q1142_HAS_OTHER`);
#   * `If patient provides a receipt, select all that apply. If no receipt was provided,
#     read options out loud.` (F3 Q97.1 / Q115.1) - a two-sentence note whose halves the
#     directive list only knew separately, so excising them left `If patient provides `
#     and the local repeat;
#   * `Check all that apply.` - the F3 papers' spelling of `Select all that apply`.
F3_Q972_PAGE = (
    "97.2 Did you pay for any other expenses during your OPD visit that were not "
    "included in the outpatient bill? "
    "Nagbayad ka ba ng iba pang nagastos sa iyong OPD visit na hindi kasama sa "
    "outpatient bill? "
    "If yes, indicate the amount spent Kung oo, ilagay ang halagang ginastos. "
    "a) Doctor’s Professional Fee Amount in Pesos")

F3_Q971_PAGE = (
    "97.1 Other than the expenses above, which of the following were also included in "
    "the bill? How much were you charged or billed? "
    "Bukod sa mga nabanggit na gastusin, alin sa mga sumusunod ang kasama rin sa "
    "binayaran? Magkano ang siningil sa iyo? "
    "If patient provides a receipt, select all that apply. If no receipt was provided, "
    "read options out loud. Select all that apply. "
    "Kung ang pasyente ay nagbigay ng resibo, piliin ang lahat na naaangkop. "
    "☐ Doctor’s Professional Fee Bayad sa Doktor")


def test_the_amount_spent_note_ends_the_question_span():
    items = [{"name": "Q972_SOURCES",
              "labels": [{"text": "97.2 Did you pay for any other expenses during your "
                                  "OPD visit that were not included in the outpatient "
                                  "bill?"}]}]
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(items)), text=F3_Q972_PAGE)
    assert r["clean"]["item:Q972_SOURCES"] == (
        "Nagbayad ka ba ng iba pang nagastos sa iyong OPD visit na hindi kasama sa "
        "outpatient bill?")


def test_the_receipt_note_ends_the_question_span():
    items = [{"name": "Q971_SOURCES",
              "labels": [{"text": "97.1 Other than the expenses above, which of the "
                                  "following were also included in the bill? How much "
                                  "were you charged or billed?"}],
              "valueSets": [{"name": "Q971_SOURCES_VS1",
                             "labels": [{"text": "97.1 Other than the expenses above, "
                                                 "which of the following were also "
                                                 "included in the bill? How much were "
                                                 "you charged or billed?"}],
                             "values": [{"labels": [{"text": "Doctor’s Professional Fee"}],
                                         "pairs": [{"value": "1"}]}]}]}]
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(items)), text=F3_Q971_PAGE)
    assert r["clean"]["item:Q971_SOURCES"] == (
        "Bukod sa mga nabanggit na gastusin, alin sa mga sumusunod ang kasama rin sa "
        "binayaran? Magkano ang siningil sa iyo?")
    assert r["clean"]["val:Q971_SOURCES_VS1:1"] == "Bayad sa Doktor"


def test_check_all_that_apply_is_read_as_a_directive():
    """`directive-bleed` exists to catch a variant DIRECTIVE_PATTERNS does not know;
    this is that variant, printed on all seven F3 papers (Q70, Q71, Q93)."""
    assert ax.has_directive("Check all that apply.")
    # through clean_span, which is the real path: strip_directives leaves the
    # sentence's own full stop behind (as it does for `SELECT ALL THAT APPLY`) and
    # clean_span's edge strip is what removes it.
    assert ax.clean_span(
        "Check all that apply. Anong uri ng transportasyon ang ginagamit ninyo?") \
        == "Anong uri ng transportasyon ang ginagamit ninyo?"


# The same class again, on the F3 COST GRIDS (Q92, Q94, Q96, Q97.1, Q97.2, Q107, Q109,
# Q112): the paper prints `☐ <option> <translation> Amount in Pesos <Kantidad sa Peso>`
# on every row. `AMOUNT IN PESOS` is already a directive, so the ENGLISH half is excised
# - but five of the seven papers (BCL, BIS, CEB, WAR, ILO) print a sentence-case LOCAL
# repeat after it, which skip_translated_directive()'s ALL-CAPS rule cannot see, and it
# rides into the option's value: 198 rows of the F3 write set carried it
# (`evidence/amount-header-probe.txt`). FIL and HIL leave the header in English only.
#
# The one place the header is CONTENT is an `*_AMT` item, whose own English label ends
# `(Amount in Pesos)` - so that is the guard, exactly as `local_directive()` guards its
# ALL-CAPS test with the anchor's own English.
LOCAL_AMOUNT_HEADERS = [
    ("BCL", "Kantidad sa Peso"), ("BIS", "Kantidad sa pesos"), ("CEB", "Kantidad sa Peso"),
    ("WAR", "Kantidad ha Pisos"), ("ILO", "Kantidad iti Pesos"),
]


@pytest.mark.parametrize("code,header", LOCAL_AMOUNT_HEADERS)
def test_every_papers_local_amount_header_bounds_a_span(code, header):
    assert ax.cut_at_local_directive(f"Donasyon {header}", "Donation").strip() == "Donasyon"


def test_the_amount_header_is_content_on_an_amount_item():
    """`115.1 How much were you charged or billed? — Other expenses: (Amount in Pesos)`
    is the one label whose translation SHOULD carry the header."""
    en = "115.1 How much were you charged or billed? — Other expenses: (Amount in Pesos)"
    span = "Magkano ang siningil sa iyo? Iba pa: Kantidad sa Peso"
    assert ax.cut_at_local_directive(span, en) == span


COST_GRID_PAGE = (
    "92. How was the cost of the consultation paid? "
    "Paano nabayadan an konsultasyon? "
    "☐ Out-of-pocket Sadiri na kwarta Amount in Pesos Kantidad sa Peso "
    "☐ Donation Donasyon/Tinao Amount in Pesos Kantidad sa Peso "
    "☐ Free/no cost Libre")


def test_local_amount_header_never_reaches_an_option_value():
    items = [{"name": "Q92_PAY_SRC",
              "labels": [{"text": "92. How was the cost of the consultation paid?"}],
              "valueSets": [{"name": "Q92_PAY_SRC_VS1",
                             "labels": [{"text": "92. How was the cost of the "
                                                 "consultation paid?"}],
                             "values": [{"labels": [{"text": "Out-of-pocket"}],
                                         "pairs": [{"value": "01"}]},
                                        {"labels": [{"text": "Donation"}],
                                         "pairs": [{"value": "02"}]}]}]}]
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(items)), text=COST_GRID_PAGE)
    assert r["clean"]["val:Q92_PAY_SRC_VS1:01"] == "Sadiri na kwarta"
    assert r["clean"]["val:Q92_PAY_SRC_VS1:02"] == "Donasyon/Tinao"
    assert not [v for v in r["clean"].values() if "Kantidad" in v]


# The F3 papers print the CAPI's own fill placeholder verbatim - `66. Is
# [facility_name_input] the facility you usually go to …` - and the F3 dictionary
# also carries an ID-block item labelled `Facility Name`. Normalised, `facility
# name` sits inside `facility name input`, so that anchor bounded a span in the
# MIDDLE of the placeholder and every Q66/Q88 translation was cut to `Ang [`.
# A placeholder is a fill, not text the paper translated: nothing inside one can
# be an anchor occurrence.
PLACEHOLDER_PAGE = (
    "66. Is [facility_name_input] the facility you usually go to for general "
    "health concerns? "
    "Ang [facility_name_input] bala ang pasilidad nga ginakadtuan mo kasagaran "
    "para sa pangkalahatan nga kahimsog? "
    "☐ Yes Huo")

_PLACEHOLDER_ITEMS = [
    {"name": "FACILITY_NAME", "labels": [{"text": "Facility Name"}]},
    {"name": "Q66_SAME_AS_USUAL",
     "labels": [{"text": "66. Is [facility_name_input] the facility you usually go "
                         "to for general health concerns?"}]},
]


def test_an_anchor_inside_a_fill_placeholder_does_not_bound_a_span():
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_PLACEHOLDER_ITEMS)),
                   text=PLACEHOLDER_PAGE)
    assert r["clean"]["item:Q66_SAME_AS_USUAL"] == (
        "Ang [facility_name_input] bala ang pasilidad nga ginakadtuan mo kasagaran "
        "para sa pangkalahatan nga kahimsog?")


def test_the_same_anchor_still_bounds_a_span_outside_a_placeholder():
    """The rule is about the placeholder, not about the label: where the paper
    really does print `Facility Name` as a row of its own it must still anchor."""
    page = ("66. Is [facility_name_input] the facility you usually go to for general "
            "health concerns? Ang [facility_name_input] bala ang pasilidad? "
            "Facility Name Ngalan sang Pasilidad")
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_PLACEHOLDER_ITEMS)),
                   text=page)
    assert r["clean"]["item:Q66_SAME_AS_USUAL"] == \
        "Ang [facility_name_input] bala ang pasilidad?"
    assert r["clean"]["item:FACILITY_NAME"] == "Ngalan sang Pasilidad"


# ---------------------------------------------------------------------------
# Task 40 FIX ROUND 1 - `truncated-tail`
#
# An English anchor can sit MID-PHRASE inside a DIFFERENT question: `Primary care
# provider` is an option label of F3 Q39/Q40/Q44, so every occurrence of that phrase
# inside Q53's stem or Q68's option row bounded the span and the translation was cut
# where the English restarts. The cut values landed in the CLEAN extract - no flag saw
# them - and shipped, replacing complete June-5 translations with fragments
# (`Igwa ba kamo ki primary care provider?` -> `Igwa ba kamo ki`).
#
# Every English/translation pair below is copied verbatim out of the Aug-21 F3 papers
# via the shipped extract (`out-aug21/F3/<loc>.json`, measured in `task-40/_tail_probe.py`).
# ---------------------------------------------------------------------------

TRUNCATED_TAILS = [
    # (locale, English label, the span the extract produced)
    ("bcl", "53. Do you have a primary care provider?", "Igwa ba kamo ki"),
    ("bis", "53. Do you have a primary care provider?", "Aduna ba kay"),
    ("hil", "53. Do you have a primary care provider?", "May ara ka bala sang"),
    ("bcl", "YAKAP/Konsulta or primary care provider", "YAKAP/Konsulta o"),
    ("ilo", "Barangay Health Worker", "Trabahador ti Salun-at ti"),
    ("ilo", "Free, charge to Private Insurance", "Libre, singir iti"),
    ("ilo", "Not yet, but I'm planning to", "Saan pay, ngem planok ti"),
    ("ilo", "Never", "Pulos a"),
    ("ilo", "Protection from financial risk/decreased out-of-pocket spending",
     "Proteksion manipud iti pinansial a peggad/bimmaba ti"),
]

# ... and the second shape: the paper's English DEFINITION block restarts right after the
# translation, so only its opening article came through.
LONE_CAPITAL_TAILS = [
    ("war", "53. Do you have a primary care provider?",
     "Mayda ka ba panguna nga nag-aataman? A"),
    ("ilo", "53. Do you have a primary care provider?",
     "(Adda kadi kangrunaan a mangipapaay iti panangaywanmo?) A"),
]

# Complete values that must stay CLEAN. Each is a real row of the shipped F3 maps that the
# broad measurement net flagged and hand review cleared - holding one costs coverage.
COMPLETE_TAILS = [
    # enclitic `na` ("already") legitimately ends a Hiligaynon phrase
    ("hil", "Retired", "Retiro na"),
    # the value ends on a terminal stop: the proclitic is the sentence's last word by
    # design, not a cut
    ("bis", "45. What category of member are you?", "Unsang kategorya sa miyembro ka?"),
    ("hil", "85. What condition/s do/es the patient usually visit the facility for?",
     "Ano nga kondisyon ang kasagarang ginabisitahan sang pasyente ang pasilidad para sa?"),
    ("bcl", "127. If you availed MAIFIP, did you have to make any out-of-pocket payment?",
     "Kan ika nag avail kan MAIFIP, kaipuhanan mo ba magbayad maski ika nadipisilan na?"),
    # a lone capital that the ENGLISH label carries too
    ("fil", "Vitamin A", "Bitamina A"),
    # ordinary complete translations
    ("fil", "Yes", "Oo"),
    ("ceb", "1. What is your current marital status?",
     "Unsa ang imong kasamtangang kahimtang sa kaminyoon?"),
]


@pytest.mark.parametrize("loc,en,tr", TRUNCATED_TAILS)
def test_truncated_tail_fires_on_a_span_cut_at_an_embedded_anchor(loc, en, tr):
    assert ax.truncated_tail(en, tr), f"{loc}: {tr!r} not seen as truncated"


@pytest.mark.parametrize("loc,en,tr", LONE_CAPITAL_TAILS)
def test_truncated_tail_fires_on_a_lone_capital_letter(loc, en, tr):
    r = ax.truncated_tail(en, tr)
    assert r and "capital" in r, f"{loc}: {tr!r} -> {r!r}"


@pytest.mark.parametrize("loc,en,tr", COMPLETE_TAILS)
def test_truncated_tail_is_silent_on_complete_values(loc, en, tr):
    assert ax.truncated_tail(en, tr) is None, f"{loc}: {tr!r} wrongly held"


@pytest.mark.parametrize("loc,en,tr", TRUNCATED_TAILS + LONE_CAPITAL_TAILS)
def test_qa_flags_carries_truncated_tail(loc, en, tr):
    assert "truncated-tail" in ax.qa_flags(en, tr, [])


def test_truncated_tail_is_described_in_the_qa_report_legend():
    assert "truncated-tail" in ax.MEAN
    assert "truncated-tail" in ax.LAYOUT_FLAGS


# The end-to-end shape: `Primary care provider` is an OPTION anchor of another question,
# so its occurrence inside Q53's stem bounds Q53's span. The row must reach
# `<loc>_flagged.json`, never `<loc>.json`.
_PCP_ITEMS = [
    {"name": "Q39_HOW_FIND_OUT",
     "labels": [{"text": "39. How did you find out about the programme?"}],
     "valueSets": [{"name": "Q39_HOW_FIND_OUT_VS1",
                    "labels": [{"text": "39. How did you find out about the programme?"}],
                    "values": [{"labels": [{"text": "Primary care provider"}],
                                "pairs": [{"value": "03"}]}]}]},
    {"name": "Q53_HAS_PCP",
     "labels": [{"text": "53. Do you have a primary care provider?"}]},
]

_PCP_PAGE = (
    "39. How did you find out about the programme? Paano mo naaraman an programa? "
    "☐ Primary care provider Primaryang parasurog nin salud "
    "53. Do you have a primary care provider? "
    "Igwa ba kamo ki primary care provider?")


def test_a_span_cut_at_an_embedded_anchor_is_flagged_not_clean():
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_PCP_ITEMS)), text=_PCP_PAGE)
    assert "item:Q53_HAS_PCP" not in r["clean"], \
        f"truncated span shipped clean: {r['clean'].get('item:Q53_HAS_PCP')!r}"
    row = [f for f in r["flagged"] if f["key"] == "item:Q53_HAS_PCP"]
    assert row and "truncated-tail" in row[0]["flags"], row
    assert row[0]["tr"] == "Igwa ba kamo ki"
    # the option row itself is complete and must still be imported
    assert r["clean"]["val:Q39_HOW_FIND_OUT_VS1:03"] == "Primaryang parasurog nin salud"


# ---------------------------------------------------------------------------------
# Task 48 — the ROW-INHERITANCE defect class (final whole-branch review, 2026-08-27).
#
# An option row silently inherits a NEIGHBOURING row's translation. The value is
# well-formed, in the right language and of the right length, so none of the 23 flags
# above fires and the row ships clean. Two mechanisms, both verified against the paper
# dumps in text-aug21/ and both reproduced below:
#
#   1. ADJACENT-ENGLISH RUN. The papers print some option grids as a run of boxed
#      ENGLISH rows followed by their translations as ONE un-boxed block:
#          ☐ Legislation ☐ LGU/ Barangay Balaod LGU/Barangay      (F3_CEB.txt, Q36)
#      The first anchor's span is empty (box to box), so the SECOND anchor's span opens
#      on the block and takes the FIRST row's translation. Where the trailing row is
#      untranslated on the paper (a proper noun printed twice) the anchor re-matches on
#      its own echo and the span is exactly the neighbour's text — `Balaod`, code 02's
#      translation, shipped as code 06 on seven F3 CEB questions. Where it is
#      translated, the span carries BOTH translations glued:
#          ☐ DOH standard referral form ☐ City / LGU standard referral form
#          Syudad / LGU surundon nga porma han pagrefer DOH nga surundon nga porma …
#      which is the F2 WAR row that is live in production.
#      Neither assignment is knowable from the page (the F2 block prints the two
#      translations in the REVERSE order of their English rows), so the whole run is
#      held: `sibling-run` on the trailing candidate, `empty` on the rows before it.
#
#   2. DUPLICATE LABEL. Two codes of ONE value set end up with the same translated
#      label while their English labels differ — either because the paper itself
#      repeats one translation across three option rows (F4 FIL Q45.2 codes 01/02/03)
#      or because the same English label occurs in two value sets and the wrong
#      occurrence won the count (F4 WAR Q128/Q134 code 05). A respondent cannot tell
#      the two choices apart, so neither is clean: both rows go to the worklist with
#      `duplicate-label`. Two codes that share the SAME English (`01`/`1` padding,
#      the legacy `8`/`99` "Other (specify)" pair) are aliases, not a defect.

_Q36_ITEMS = [
    {"name": "Q36_UHC_SOURCE",
     "labels": [{"text": "36. Where did you first hear about UHC?"}],
     "valueSets": [{"name": "Q36_UHC_SOURCE_VS1",
                    "labels": [{"text": "36. Where did you first hear about UHC?"}],
                    "values": [
                        {"labels": [{"text": "Legislation"}], "pairs": [{"value": "02"}]},
                        {"labels": [{"text": "LGU/ Barangay"}], "pairs": [{"value": "06"}]},
                        {"labels": [{"text": "Friends / Family"}],
                         "pairs": [{"value": "04"}]}]}]}]

# F3_CEB.txt lines 1027-1036, whitespace-collapsed the way pdf_text() collapses it.
_CEB_RUN_PAGE = (
    "36. Where did you first hear about UHC? Diin nimo una nadungog ang UHC? "
    "☐ Legislation ☐ LGU/ Barangay Balaod LGU/Barangay "
    "☐ Friends / Family Mga higala / Pamilya")


def test_adjacent_english_run_never_ships_the_neighbours_translation():
    """The shipped F3 CEB defect: code 06 `LGU/ Barangay` held `Balaod`, code 02's text."""
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_Q36_ITEMS)), text=_CEB_RUN_PAGE)
    assert r["clean"].get("val:Q36_UHC_SOURCE_VS1:06") != "Balaod", \
        "code 06 still ships code 02's translation"
    assert "val:Q36_UHC_SOURCE_VS1:06" not in r["clean"]
    row = [f for f in r["flagged"] if f["key"] == "val:Q36_UHC_SOURCE_VS1:06"]
    assert row and "sibling-run" in row[0]["flags"], row
    # the row whose translation was stolen stays a worklist row too, never a write
    assert "val:Q36_UHC_SOURCE_VS1:02" not in r["clean"]
    # ... and the guard: the row AFTER the run carries its own box and is untouched
    assert r["clean"]["val:Q36_UHC_SOURCE_VS1:04"] == "Mga higala / Pamilya"


_REFERRAL_ITEMS = [
    {"name": "Q57_REFERRAL_FORM",
     "labels": [{"text": "57. What type of referral form do you use?"}],
     "valueSets": [{"name": "Q57_REFERRAL_FORM_VS1",
                    "labels": [{"text": "57. What type of referral form do you use?"}],
                    "values": [
                        {"labels": [{"text": "DOH standard referral form"}],
                         "pairs": [{"value": "01"}]},
                        {"labels": [{"text": "City / LGU standard referral form"}],
                         "pairs": [{"value": "02"}]},
                        {"labels": [{"text": "Facility's standard referral form"}],
                         "pairs": [{"value": "03"}]}]}]}]

# F2_WAR.txt @42483, the row that is LIVE in production (the DOH row extracted `empty`).
_WAR_RUN_PAGE = (
    "57. What type of referral form do you use? Ano nga klase hin referral form an iyo "
    "ginagamit? ☐ DOH standard referral form ☐ City / LGU standard referral form "
    "Syudad / LGU surundon nga porma han pagrefer DOH nga surundon nga porma han pagrefer "
    "☐ Facility's standard referral form An surundon nga porma han pagrefer han pasilidad")


def test_adjacent_english_run_never_ships_two_glued_translations():
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_REFERRAL_ITEMS)),
                   text=_WAR_RUN_PAGE)
    assert "val:Q57_REFERRAL_FORM_VS1:02" not in r["clean"], \
        f"glued run shipped clean: {r['clean'].get('val:Q57_REFERRAL_FORM_VS1:02')!r}"
    row = [f for f in r["flagged"] if f["key"] == "val:Q57_REFERRAL_FORM_VS1:02"]
    assert row and "sibling-run" in row[0]["flags"], row
    assert "val:Q57_REFERRAL_FORM_VS1:01" not in r["clean"]
    assert r["clean"]["val:Q57_REFERRAL_FORM_VS1:03"] == \
        "An surundon nga porma han pagrefer han pasilidad"


def test_a_boxed_row_that_carries_its_own_translation_is_not_a_sibling_run():
    """The guard. Every option row printed `☐ EN LOCAL` keeps its own span — the rule
    may only fire where the PREVIOUS sibling's span was empty."""
    page = ("36. Where did you first hear about UHC? Diin nimo una nadungog ang UHC? "
            "☐ Legislation Balaod ☐ LGU/ Barangay Lokal nga panggamhanan "
            "☐ Friends / Family Mga higala / Pamilya")
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_Q36_ITEMS)), text=page)
    assert r["clean"]["val:Q36_UHC_SOURCE_VS1:02"] == "Balaod"
    assert r["clean"]["val:Q36_UHC_SOURCE_VS1:06"] == "Lokal nga panggamhanan"
    assert r["clean"]["val:Q36_UHC_SOURCE_VS1:04"] == "Mga higala / Pamilya"
    assert not [f for f in r["flagged"] if "sibling-run" in f["flags"]]


_Q45_ITEMS = [
    {"name": "Q45_2_WHY_NOT_REG",
     "labels": [{"text": "45.2 Why are you not registered?"}],
     "valueSets": [{"name": "Q45_2_WHY_NOT_REG_VS1",
                    "labels": [{"text": "45.2 Why are you not registered?"}],
                    "values": [
                        {"labels": [{"text": "Difficult to register"}],
                         "pairs": [{"value": "01"}]},
                        {"labels": [{"text": "Don't see value in registering"}],
                         "pairs": [{"value": "02"}]},
                        {"labels": [{"text": "No time to register"}],
                         "pairs": [{"value": "07"}]}]}]}]

# F4_FIL.txt @25769: the PAPER repeats one Tagalog string across three option rows.
_FIL_DUP_PAGE = (
    "45.2 Why are you not registered? Bakit ka hindi rehistrado? "
    "☐ Difficult to register Mahirap magparehistro "
    "☐ Don't see value in registering Mahirap magparehistro "
    "☐ No time to register Walang oras para magparehistro")


def test_two_codes_of_one_value_set_may_not_ship_the_same_translation():
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_Q45_ITEMS)), text=_FIL_DUP_PAGE)
    for code in ("01", "02"):
        key = f"val:Q45_2_WHY_NOT_REG_VS1:{code}"
        assert key not in r["clean"], f"{key} shipped {r['clean'].get(key)!r}"
        row = [f for f in r["flagged"] if f["key"] == key]
        assert row and "duplicate-label" in row[0]["flags"], (code, row)
    # the third row is distinct and must still be imported
    assert r["clean"]["val:Q45_2_WHY_NOT_REG_VS1:07"] == "Walang oras para magparehistro"


_ALIAS_ITEMS = [
    {"name": "Q88_WHY_VISIT",
     "labels": [{"text": "88. Why did you visit the facility?"}],
     "valueSets": [{"name": "Q88_WHY_VISIT_VS1",
                    "labels": [{"text": "88. Why did you visit the facility?"}],
                    "values": [
                        {"labels": [{"text": "Sick or injured"}], "pairs": [{"value": "01"}]},
                        {"labels": [{"text": "Other (specify)"}], "pairs": [{"value": "8"}]},
                        {"labels": [{"text": "Other (specify)"}], "pairs": [{"value": "99"}]}]}]}]


def test_codes_that_share_the_same_english_are_aliases_not_duplicates():
    """`01`/`1` padding and the legacy `8`/`99` "Other (specify)" pair are the ~12 benign
    rows of the scan: same English, so the same translation is the CORRECT answer."""
    page = ("88. Why did you visit the facility? Bakit ka bumisita sa pasilidad? "
            "☐ Sick or injured May sakit o nasugatan "
            "☐ Other (specify) Iba pa (tukuyin)")
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_ALIAS_ITEMS)), text=page)
    assert r["clean"]["val:Q88_WHY_VISIT_VS1:8"] == "Iba pa (tukuyin)"
    assert r["clean"]["val:Q88_WHY_VISIT_VS1:99"] == "Iba pa (tukuyin)"
    assert r["clean"]["val:Q88_WHY_VISIT_VS1:01"] == "May sakit o nasugatan"
    assert not [f for f in r["flagged"] if "duplicate-label" in f["flags"]]


_TWO_VS_ITEMS = [
    {"name": "Q10_FIRST",
     "labels": [{"text": "10. First question about payment sources?"}],
     "valueSets": [{"name": "Q10_FIRST_VS1",
                    "labels": [{"text": "10. First question about payment sources?"}],
                    "values": [{"labels": [{"text": "Out of pocket"}],
                                "pairs": [{"value": "01"}]}]}]},
    {"name": "Q20_SECOND",
     "labels": [{"text": "20. Second question about payment sources?"}],
     "valueSets": [{"name": "Q20_SECOND_VS1",
                    "labels": [{"text": "20. Second question about payment sources?"}],
                    "values": [{"labels": [{"text": "Paid from savings"}],
                                "pairs": [{"value": "01"}]}]}]}]


def test_the_same_translation_under_two_different_value_sets_is_allowed():
    """The rule is per value set: a respondent only ever sees one set at a time."""
    page = ("10. First question about payment sources? Una nga pangutana? "
            "☐ Out of pocket Gikan sa bulsa "
            "20. Second question about payment sources? Ikaduha nga pangutana? "
            "☐ Paid from savings Gikan sa bulsa")
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_TWO_VS_ITEMS)), text=page)
    assert r["clean"]["val:Q10_FIRST_VS1:01"] == "Gikan sa bulsa"
    assert r["clean"]["val:Q20_SECOND_VS1:01"] == "Gikan sa bulsa"
    assert not [f for f in r["flagged"] if "duplicate-label" in f["flags"]]


def test_the_row_inheritance_flags_are_described_in_the_qa_report_legend():
    for flag in ("sibling-run", "duplicate-label"):
        assert flag in ax.MEAN
        assert flag in ax.LAYOUT_FLAGS


# The three guards that keep `sibling-run` off a row that simply follows an option the
# paper left in English. Each one was written after MEASURING the rule over the 28 Aug-21
# papers; without them the rule moved ~230 CORRECT values to the worklist.

_CIVIL_ITEMS = [
    {"name": "Q10_CIVIL_STATUS",
     "labels": [{"text": "10. What is the patient's civil status?"}],
     "valueSets": [{"name": "Q10_CIVIL_STATUS_VS1",
                    "labels": [{"text": "10. What is the patient's civil status?"}],
                    "values": [
                        {"labels": [{"text": "Separated"}], "pairs": [{"value": "4"}]},
                        {"labels": [{"text": "Annulled"}], "pairs": [{"value": "6"}]},
                        {"labels": [{"text": "Widowed"}], "pairs": [{"value": "7"}]}]}]}]


def test_one_untranslated_neighbour_is_not_a_sibling_run():
    """F3_BIS.txt @11373: `☐ Annulled ☐ Widowed Balo`. The paper leaves ONE option row in
    English and translates the next; `Balo` is Widowed's own translation and must ship."""
    page = ("10. What is the patient's civil status? Unsa ang kahimtang sa kaminyoon? "
            "☐ Separated Separada/Separado ☐ Annulled ☐ Widowed Balo")
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_CIVIL_ITEMS)), text=page)
    assert r["clean"]["val:Q10_CIVIL_STATUS_VS1:7"] == "Balo"
    assert r["clean"]["val:Q10_CIVIL_STATUS_VS1:4"] == "Separada/Separado"
    assert not [f for f in r["flagged"] if "sibling-run" in f["flags"]]


_INFRA_ITEMS = [
    {"name": "Q52_ACCRED_DIFFICULT",
     "labels": [{"text": "52. Which was difficult to comply with?"}],
     "valueSets": [{"name": "Q52_ACCRED_DIFFICULT_VS1",
                    "labels": [{"text": "52. Which was difficult to comply with?"}],
                    "values": [
                        {"labels": [{"text": "General Infrastructure"}],
                         "pairs": [{"value": "03"}]},
                        {"labels": [{"text": "Human Resource"}], "pairs": [{"value": "06"}]},
                        {"labels": [{"text": "Functional Health Information System"}],
                         "pairs": [{"value": "07"}]}]}]}]


def test_a_list_the_paper_left_in_english_is_not_a_sibling_run():
    """F1_HIL.txt @48956: a RUN of English-only option rows ends with one translated row,
    and that single translation is that row's own. A batched PAIR is two rows, not five —
    so where the row before the empty predecessor is ALSO an empty boxed sibling, the rule
    stands down. This candidate is 2.4x its English, so only the list guard holds it."""
    page = ("52. Which was difficult to comply with? Ano ang budlay sundon? "
            "☐ General Infrastructure ☐ Human Resource "
            "☐ Functional Health Information System "
            "Ang sistema hin impormasyon han panlawas nga naglalantaw ngan nagtitipig "
            "hin mga datos")
    r = ax.extract("x.pdf", ax._anchors_from_dict(_t40_dcf(_INFRA_ITEMS)), text=page)
    assert r["clean"]["val:Q52_ACCRED_DIFFICULT_VS1:07"] == (
        "Ang sistema hin impormasyon han panlawas nga naglalantaw ngan nagtitipig "
        "hin mga datos")
    assert not [f for f in r["flagged"] if "sibling-run" in f["flags"]]


def test_overlapping_occurrences_are_not_an_empty_span():
    """`☐ No, but have submitted requirements …` is a hit of the option `No` and of the
    long option at the SAME offset, and the de-overlap keeps both. The zero-length gap
    between them is the same words twice, not a row the paper printed nothing for."""
    text = "☐ No, but have submitted requirements and waiting for license Hindi po"
    ntext, idx = ax.build_norm(text)
    s = ntext.index("no")
    short = (s, s + 2, "no", False)
    long_ = (s, s + len("no but have submitted requirements and waiting for license"),
             "no but have submitted requirements and waiting for license", False)
    assert not ax._empty_option_span(text, idx, short, long_)
