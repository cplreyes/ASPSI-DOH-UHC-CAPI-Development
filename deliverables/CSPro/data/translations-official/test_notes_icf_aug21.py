"""Aug-21 notes + ICF tooling. NOTE: extract_notes.polish() strips the terminal period of
every note by design, so note comparisons use .rstrip('.'); ICF paragraphs (Task 10) keep
their terminal punctuation and are compared verbatim."""
import io
import json
import os
import sys
import textwrap

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, CSPRO)

from conftest import make_pdf  # noqa: E402

import extract_icf  # noqa: E402
import extract_notes as en_mod  # noqa: E402
import icf_content  # noqa: E402

EN_INTRO = "Now I will ask you some questions about the services offered at this facility."
FIL_INTRO = ("Ngayon ay magtatanong ako ng ilang katanungan tungkol sa mga serbisyong "
             "inaalok sa pasilidad na ito.")


def test_dump_source_names_files_by_instrument_and_locale(tmp_path):
    src = tmp_path / "Translations"
    src.mkdir()
    make_pdf(src / "F1-Tagalog_Facility Head Survey Questionnaire_UHC Year 2_Aug21.pdf",
             [EN_INTRO, FIL_INTRO, "READ ALL OPTIONS."])
    make_pdf(src / "F2-Tagalog_Healthcare Worker Survey Questionnaire_UHC Year 2_Aug21.pdf",
             ["x"])
    out = tmp_path / "text-aug21"
    written = en_mod.dump_source(str(src), str(out))
    assert list(written) == [("F1", "FIL")]           # F2 is not a CSPro instrument
    raw = (out / "F1_FIL.txt").read_bytes()           # binary: text-mode read would hide CRLF
    assert b"magtatanong" in raw and b"\r\n" not in raw


def test_dump_source_drops_the_page_footer_between_a_note_and_its_translation(tmp_path):
    # The Aug-21 footer lands BETWEEN the English note and its translation on nine notes;
    # undropped, find_translation ships the footer as the translation.
    src = tmp_path / "Translations"
    src.mkdir()
    make_pdf(src / "F3-Waray_Patient Survey Questionnaire_UHC Year 2_Aug21.pdf",
             [EN_INTRO,
              "ICF ver.07/25/2026 | Translated Questionnaire ver.08/21/2026",
              FIL_INTRO])
    out = tmp_path / "text-aug21"
    en_mod.dump_source(str(src), str(out))
    lines = (out / "F3_WAR.txt").read_text(encoding="utf-8").split("\n")
    assert not [ln for ln in lines if "Translated Questionnaire ver." in ln]
    assert en_mod.find_translation(lines, EN_INTRO) == FIL_INTRO.rstrip(".")


def test_find_translation_on_synthetic_aug21_page(tmp_path):
    pdf = tmp_path / "F1-Tagalog_x_Aug21.pdf"
    make_pdf(pdf, [EN_INTRO, FIL_INTRO, "READ ALL OPTIONS."])
    lines = en_mod.pdf_lines(str(pdf))
    assert en_mod.find_translation(lines, EN_INTRO) == FIL_INTRO.rstrip(".")  # polish() drops the period


def test_merge_notes_aug21_wins_except_override():
    existing = {"F1": {"english": {"intro:1": EN_INTRO, "intro:2": "Second English note here."},
                       "translations": {"intro:1": {"FIL": "LUMA", "BCL": "luma-bcl"},
                                        "intro:2": {"FIL": "keep-me"}}}}
    fresh = {"F1": {"english": {"intro:1": EN_INTRO, "intro:2": "Second English note here."},
                    "translations": {"intro:1": {"FIL": FIL_INTRO, "BCL": "bago-bcl", "ILO": "baro"},
                                     "intro:2": {}}}}
    overrides = {"F1": {"note:intro:1:BCL": {"keep": "luma-bcl", "reason": "Aug-21 BCL re-glues Q2"}}}
    merged, counts = en_mod.merge_notes(existing, fresh, overrides,
                                        {"date": "2026-08-25", "source": "raw/x", "files": {}})
    t = merged["F1"]["translations"]
    assert t["intro:1"]["FIL"] == FIL_INTRO          # replaced
    assert t["intro:1"]["BCL"] == "luma-bcl"         # overridden
    assert t["intro:1"]["ILO"] == "baro"             # written
    assert t["intro:2"]["FIL"] == "keep-me"          # Aug-21 empty -> prior kept
    assert counts == {"written": 1, "replaced": 1, "overridden": 1, "kept_prior": 1}
    assert merged["_provenance"]["aug21"]["n_replaced"] == 1
    assert "english" not in merged["_provenance"]    # notes_lookup._load skips it


def test_merge_notes_reworded_english_drops_stale_prior_but_keeps_fresh():
    existing = {"F3": {"english": {"intro:4": "OLD wording."},
                       "translations": {"intro:4": {"FIL": "old", "BCL": "old-bcl"}}}}
    fresh = {"F3": {"english": {"intro:4": "NEW wording."},
                    "translations": {"intro:4": {"FIL": "bago"}}}}
    merged, counts = en_mod.merge_notes(existing, fresh, {},
                                        {"date": "2026-08-25", "source": "x", "files": {}})
    assert merged["F3"]["english"]["intro:4"] == "NEW wording."
    assert merged["F3"]["translations"]["intro:4"] == {"FIL": "bago"}   # stale BCL gone, fresh FIL in
    assert counts["written"] == 1 and counts["kept_prior"] == 0


def test_merge_notes_resolves_prior_by_english_when_the_key_was_renumbered():
    """The F1 renumbering moved intro:51 -> intro:38 with the English byte-identical. Merging
    by KEY alone saw no prior, counted a SHORTER Aug-21 value as `written`, and the Step-5
    'review every replaced' gate never fired — nine locale strings shipped degraded. The
    runtime (notes_lookup._canon) addresses notes by English text, so the merge must too."""
    existing = {"F1": {"english": {"intro:51": EN_INTRO},
                       "translations": {"intro:51": {"FIL": FIL_INTRO, "BCL": "luma-bcl"}}}}
    fresh = {"F1": {"english": {"intro:38": EN_INTRO},
                    "translations": {"intro:38": {"FIL": "Ngayon ay magtatanong ako"}}}}
    merged, counts = en_mod.merge_notes(existing, fresh, {},
                                        {"date": "2026-08-25", "source": "x", "files": {}})
    t = merged["F1"]["translations"]
    assert counts["replaced"] == 1 and counts["written"] == 0   # re-key is NOT a new note
    assert t["intro:38"]["FIL"] == "Ngayon ay magtatanong ako"  # Aug-21 still wins by default
    assert t["intro:38"]["BCL"] == "luma-bcl"                   # prior survives the re-key
    assert counts["kept_prior"] == 1
    assert "intro:51" not in t                                  # retired key does not linger


def test_merge_notes_renumbered_note_keeps_its_prior_when_aug21_finds_nothing():
    # Renumbered AND unextractable: the value must not silently drop to English.
    existing = {"F1": {"english": {"intro:51": EN_INTRO},
                       "translations": {"intro:51": {"FIL": FIL_INTRO}}}}
    fresh = {"F1": {"english": {"intro:38": EN_INTRO}, "translations": {}}}
    merged, counts = en_mod.merge_notes(existing, fresh, {},
                                        {"date": "2026-08-25", "source": "x", "files": {}})
    assert merged["F1"]["translations"]["intro:38"] == {"FIL": FIL_INTRO}
    assert counts == {"written": 0, "replaced": 0, "overridden": 0, "kept_prior": 1}


def test_merge_notes_override_on_the_renumbered_key_restores_the_june5_value():
    # The ten fix-round overrides are keyed on the NEW number (note:intro:38:<LOC>).
    existing = {"F1": {"english": {"intro:51": EN_INTRO},
                       "translations": {"intro:51": {"FIL": FIL_INTRO}}}}
    fresh = {"F1": {"english": {"intro:38": EN_INTRO},
                    "translations": {"intro:38": {"FIL": "truncated"}}}}
    overrides = {"F1": {"note:intro:38:FIL": {"keep": FIL_INTRO, "reason": "Aug-21 truncates"}}}
    merged, counts = en_mod.merge_notes(existing, fresh, overrides,
                                        {"date": "2026-08-25", "source": "x", "files": {}})
    assert merged["F1"]["translations"]["intro:38"]["FIL"] == FIL_INTRO
    assert counts["overridden"] == 1 and counts["replaced"] == 0


def test_canon_english_agrees_with_notes_lookup_canon():
    import notes_lookup
    s = "We will now ask about your  facility’s “experience”.\n"
    assert en_mod.canon_english(s) == notes_lookup._canon(s).strip()


# The three normalisers in the notes layer - extract_notes.norm() (write side),
# extract_notes.canon_english() (merge side) and notes_lookup._canon() (render side) - must
# agree on what "the same note" is. They diverged on en/em dashes and NBSP: norm() folded
# them, _canon() did not, so F4 SECTION_INTROS[144] (two em-dashes) was STORED under a
# hyphen key the runtime never built and rendered English in all seven locales while six
# cleared translations sat unreachable in notes.json. These pin the agreement, not one note.
DASHY = ("Items your household used but did not buy\u2014such as gifts\u2014or got"
         "\u00a0free \u2013 estimate their value.")


@pytest.mark.parametrize("fn_name", ["norm", "canon_english"])
def test_notes_lookup_canon_agrees_with_the_extractor_on_dashes(fn_name):
    import notes_lookup
    fn = getattr(en_mod, fn_name)
    assert fn(DASHY) == notes_lookup._canon(DASHY).strip()
    for ch in ("\u2013", "\u2014", "\u00a0"):
        assert ch not in notes_lookup._canon(DASHY)


def test_translate_note_reaches_a_dash_bearing_note(tmp_path, monkeypatch):
    """A note authored with an em-dash resolves through the REAL loader, not by luck.

    Built on notes_lookup's own json path so it fails against the pre-fix _canon whatever
    the shipped notes.json happens to hold.
    """
    import notes_lookup
    blob = {"F4": {"english": {"intro:144": en_mod.norm(DASHY)},
                   "translations": {"intro:144": {"FIL": "Tagalog body."}}}}
    path = tmp_path / "notes.json"
    path.write_text(json.dumps(blob), encoding="utf-8")
    monkeypatch.setattr(notes_lookup, "_NOTES_PATH", path)
    monkeypatch.setattr(notes_lookup, "_BY_ENGLISH", None)
    try:
        assert notes_lookup.translate_note(DASHY, "FIL") == "Tagalog body."
        assert notes_lookup.translate_note(DASHY, "BCL") == DASHY      # honest fallback
    finally:
        notes_lookup._BY_ENGLISH = None


def test_const_regex_accepts_digits_in_constant_names():
    # extract_notes._CONST_RE widened from ^(_[A-Z_]+) to ^(_[A-Z0-9_]+) — a digit in a
    # NAME must not hide an anchor (Task 25/29 add _GATE_Q1xx constants).
    assert en_mod._CONST_RE.match('_GATE_Q112 = "Ask only if the facility offers this."')


def test_screens_for_falls_back_per_paragraph(tmp_path, monkeypatch):
    en1, en2 = icf_content.SCREENS["F1"]
    data = {"F1": {"icf:1:1": {"EN": en1[1], "FIL": "Layunin ng pag-aaral na ito ..."},
                   "icf:1:2": {"EN": en1[2], "FIL": ""},              # "keep": "" -> English
                   "icf:2:0": {"EN": "REWORDED", "FIL": "must-not-show"}}}
    p = tmp_path / "icf.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(icf_content, "_ICF_PATH", p)
    monkeypatch.setattr(icf_content, "_ICF", None)
    s1, s2 = icf_content.screens_for("F1", "FIL")
    assert s1[0] == en1[0]                                # no translation -> English
    assert s1[1] == "Layunin ng pag-aaral na ito ..."     # translated
    assert s1[2] == en1[2]                                # empty keep -> English
    assert s2[0] == en2[0]                                # EN mismatch -> English
    assert icf_content.screens_for("F1", "EN") == (list(en1), list(en2))
    html = icf_content.screens_html_by_lang("F1", 1, "<p>LOGO</p>")
    assert set(html) == {"EN", *icf_content.ICF_LANGS}
    assert "Layunin" in html["FIL"] and "Layunin" not in html["EN"]
    assert "\n" not in html["FIL"]                        # one-line body for the .qsf `|` scalar
    assert "(ASPSI).  We are here" in html["EN"]          # paragraph text is NOT whitespace-collapsed
    assert "Translated Questionnaire ver. 08/21/2026" in html["EN"]
    # Pre-flight ruling: coverage() -> {loc: {"differs": n, "stored": n}} so a forced-English
    # ("keep": "") row is visible as reviewed (stored) even though it doesn't differ. Here FIL
    # has 3 stored rows (icf:1:1, icf:1:2, icf:2:0) but only icf:1:1 actually differs.
    assert icf_content.coverage() == {"FIL": {"differs": 1, "stored": 3}}


def test_screens_for_canonicalizes_en_before_comparing(tmp_path, monkeypatch):
    """Fix-round-1 (#1235/#1256 class): screens_for() used to gate a translation on
    `entry.get("EN") == en`, a raw byte comparison. F1 1:0 / F3 1:0 carry a double space
    ("(ASPSI).  We are"); F1 2:0 / F3 2:0 / F3 2:1 / F4 2:0 / F4 2:1 carry curly quotes. If
    Task 10's extractor ever normalizes even one such space or quote when storing EN, an
    exact-match gate silently reverts that paragraph to English with no error. screens_for()
    must instead compare via notes_lookup._canon (curly quotes -> straight, whitespace
    collapsed) so a harmless normalization difference does not cost the translation."""
    en1, en2 = icf_content.SCREENS["F1"]
    assert "  " in en1[0]           # sanity: F1 1:0 really does carry the double space
    assert "’" in en2[0]       # sanity: F1 2:0 really does carry a curly apostrophe
    stored_en_1_0 = en1[0].replace("  ", " ")          # extractor collapsed the double space
    stored_en_2_0 = en2[0].replace("’", "'")      # extractor straightened the quotes
    data = {"F1": {"icf:1:0": {"EN": stored_en_1_0, "FIL": "Nagtatrabaho kami ..."},
                   "icf:2:0": {"EN": stored_en_2_0, "FIL": "Nangangako kami ..."}}}
    p = tmp_path / "icf.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(icf_content, "_ICF_PATH", p)
    monkeypatch.setattr(icf_content, "_ICF", None)
    s1, s2 = icf_content.screens_for("F1", "FIL")
    assert s1[0] == "Nagtatrabaho kami ..."   # survives whitespace normalization in stored EN
    assert s2[0] == "Nangangako kami ..."     # survives quote normalization in stored EN


# --------------------------------------------------------------------------------------
# Task 10: extract_icf.py — ICF paragraphs out of the Aug-21 translated PDFs
# --------------------------------------------------------------------------------------
# The paper's OWN English paragraph 1. It is NOT the build's paragraph ("We work for ...",
# "We are here to invite"), which is why extract_icf anchors paragraph 1 by its identical
# TAIL ("here to invite you to ... more about the study.") — kind "suffix".
PAPER_P1 = ("Hello, my name is (data collector name). I work for Asian Social Project Services, "
            "Inc. (ASPSI). I am here to invite you to participate in a study about the Universal "
            "Health Care (UHC) and packages of programs like Yaman ng Kalusugan Program (YAKAP), "
            "No Balance Billing (NBB), Zero Balance Billing (ZBB), Bagong Urgent Care and "
            "Ambulatory Services (BUCAS), and Guaranteed and Accessible Medications for "
            "Outpatient Treatment (GAMOT). The Department of Health funded this study. Please "
            "let me tell you more about the study.")
# The REAL Aug-21 F1-Tagalog paragraph 1, pasted verbatim from text-aug21/F1_FIL.txt: the
# program names stay in English (this is what makes plain looks_english() reject all 21
# locales). test_fil_p1_is_verbatim_from_the_dump fails on any paraphrase.
FIL_P1 = ("Kamusta, ako si pangalan ng data collector. Ako ay nagtatrabaho sa Asian Social "
          "Project Services, Inc. (ASPSI). Narito ako upang anyayahan kayong lumahok sa isang "
          "pag-aaral tungkol sa Universal Health Care (UHC) at mga programa nito tulad ng "
          "Yaman ng Kalusugan Program (YAKAP), Zero Balance Billing (ZBB), Bagong Urgent Care "
          "at Ambulatory Services (BUCAS), at Guaranteed and Accessible Medications for "
          "Outpatient Treatment (GAMOT). Ang Department of Health ang nagpondo sa pag-aaral na "
          "ito. Pahintulutan ninyo akong ipaliwanag pa nang higit ang tungkol sa pag-aaral.")
# FIL_P2 / FIL_P3 are SYNTHETIC make_pdf fixtures (short, obviously-Tagalog stand-ins for
# paragraphs 2 and 3) — only FIL_P1 is under the verbatim guard, because only FIL_P1 has to
# prove that reads_english() tolerates the English program names the real paper keeps.
FIL_P2 = ("Layunin ng pag-aaral na ito na makalikom ng ebidensya tungkol sa pagpapatupad ng UHC "
          "at ng mga programa nito sa pamamagitan ng mga survey sa mga pasilidad, pasyente at "
          "sambahayan sa buong bansa. Sasaklawin ng mga tanong ang profile ng pasilidad at/o "
          "pinuno ng pasilidad, mga pagbabago sa pagpapatupad ng UHC mula 2019, at ang mga "
          "karanasan ninyo sa mga programa. Tatagal ang panayam nang humigit-kumulang isang oras.")
FIL_P3 = "Nais mo bang lumahok bilang respondent sa pag-aaral? Maaaring tumagal ng humigit-kumulang isang oras ang panayam."
FIL_CONTACT = ("Kung may mga alalahanin kayo tungkol sa pag-aaral, maaari mong kontakin ang:")
BIS_CONTACT = ("Kung aduna pa kay mga pangutana kabahin sa imong katungod bilang partisipante, "
               "pwede nimo kini kontakon:")
# Words a translation may legitimately open with even though the English carries them too:
# heads of the program/organisation names every locale keeps verbatim, plus the Ilocano
# "No adda ..." / the "Hello" every paper's paragraph 1 keeps. No English FUNCTION word is
# on this list - one of those at the head is exactly the bleed being scanned for.
_SHARED_HEADS = {"asian", "universal", "yaman", "no", "zero", "bagong", "guaranteed",
                 "department", "single", "hello", "php", "uhc"}
TEXT_AUG21_F1_FIL = os.path.join(HERE, "text-aug21", "F1_FIL.txt")   # Task 8 Step 5 dump (gitignored)


def _paper_pdf(path, paragraphs):
    """One synthetic consent page: every paragraph reflowed to PDF-column width.

    conftest.make_pdf() draws one list item per text row and PyMuPDF drops whatever runs
    off the page edge, so a 480-character consent paragraph handed over as ONE row loses
    two thirds of itself. Wrapping is also what the real paper does — the reflowed shape
    extract_screens() has to join back together.

    Paragraphs are drawn through en_mod.norm() because make_pdf writes base-14 Helvetica,
    which has no glyph for the curly quotes SCREENS carries ("other people’s privacy"):
    they come back out of the text layer as "·". norm() is exactly the folding both the
    anchor and the blob already go through inside extract_screens(), so the page text
    stays the text a real (properly encoded) PDF would hand back.
    """
    lines = []
    for para in paragraphs:
        lines.extend(textwrap.wrap(en_mod.norm(para), 95) or [""])
    make_pdf(str(path), lines)


def test_fil_p1_is_verbatim_from_the_dump():
    """Fixture guard: FIL_P1 must be the paper's own paragraph, never an invented one."""
    if not os.path.exists(TEXT_AUG21_F1_FIL):
        msg = ("text-aug21/F1_FIL.txt missing - run Task 8 Step 5 first "
               "(extract_notes.py --source ... --provenance aug21)")
        if os.path.exists(os.path.join(HERE, "extract_icf.py")):
            pytest.fail(msg)          # extractor shipped without its fixture ever verified
        pytest.skip(msg)
    dump = en_mod.norm(" ".join(io.open(TEXT_AUG21_F1_FIL, encoding="utf-8").read().split("\n")))
    assert en_mod.norm(FIL_P1) in dump, "FIL_P1 is not verbatim from the Aug-21 F1-Tagalog dump"


def test_reads_english_accepts_translation_that_keeps_program_names():
    en = extract_icf.plain(icf_content.SCREENS["F1"][0][0])
    assert not extract_icf.reads_english(FIL_P1, en)
    assert extract_icf.reads_english(PAPER_P1, en)                   # English -> rejected
    assert extract_icf.reads_english("will cover your Patient Profile and the services you "
                                     "used, and the changes in the facility since 2019", en)


def test_finish_keeps_terminal_punctuation():
    assert extract_icf.finish(FIL_P3 + " ") == FIL_P3
    assert extract_icf.finish("(UHC) Magtatanong kami sa inyo.") == "Magtatanong kami sa inyo."
    assert extract_icf.finish("Walang masamang mangyayari sa inyo. A") == "Walang masamang mangyayari sa inyo."


def test_finish_keeps_a_colon_terminated_paragraph():
    """Pre-flight ruling: ':' is a terminal. The ethics-contact lead-in ends on a colon and
    the word in front of it is a clause word in every locale ("... kontakin ang:"), which is
    exactly what polish()'s DANGLING guard blanks — so polish() alone loses the paragraph."""
    assert en_mod.polish(FIL_CONTACT) == ""              # why finish() cannot just be polish()
    assert extract_icf.finish(FIL_CONTACT + " ") == FIL_CONTACT
    assert extract_icf.finish("(SJREB) " + FIL_CONTACT) == FIL_CONTACT   # lead debris still trimmed


def test_finish_unwraps_a_paragraph_the_paper_brackets_whole():
    """The Aug-21 Ilocano F3/F4 papers print each consent paragraph as "(<Ilocano>.)" — the
    bracket is layout, not sentence, and paragraph 1 is even missing its closing bracket."""
    assert extract_icf.finish("(" + FIL_P3 + ")") == FIL_P3
    assert extract_icf.finish("(Hello, ti naganko ket (data collector's name) . "
                              "Agtartrabahoak iti ASPSI.") == \
        "Hello, ti naganko ket (data collector's name) . Agtartrabahoak iti ASPSI."
    # a bracket that closes mid-paragraph is content, not a wrapper
    assert extract_icf.finish("(pangalan ng data collector) ang nagsabi nito.") == \
        "(pangalan ng data collector) ang nagsabi nito."


def test_extract_screens_suffix_and_exact_anchors(tmp_path):
    en1 = icf_content.SCREENS["F1"][0]
    pdf = tmp_path / "F1-Tagalog_x_Aug21.pdf"
    _paper_pdf(pdf, [PAPER_P1, FIL_P1, en1[1], FIL_P2, en1[2], FIL_P3, "PART II: PRIVACY",
                     icf_content.SCREENS["F1"][1][0]])
    tr, rep = extract_icf.extract_screens(en_mod.pdf_lines(str(pdf)), "F1")
    assert rep["icf:1:0"] == "suffix" and tr["icf:1:0"].startswith("Kamusta, ako si")
    assert tr["icf:1:0"].endswith(".")                            # terminal period kept
    assert rep["icf:1:1"] == "exact" and tr["icf:1:1"].startswith("Layunin")
    assert tr["icf:1:2"] == FIL_P3 and "PART II" not in tr["icf:1:2"]
    assert rep["icf:2:0"] in ("dropped-short", "missing")       # nothing follows it on the page
    assert "icf:2:4" not in rep                                  # <b> contact blocks never anchored


def test_extract_screens_stops_at_contact_table_furniture(tmp_path):
    en2 = icf_content.SCREENS["F1"][1]
    pdf = tmp_path / "F1-Tagalog_x_Aug21.pdf"
    _paper_pdf(pdf, [en2[3], FIL_CONTACT, "Office Email Contact No",
                     "Single Joint Research Ethics Board sjreb@doh.gov.ph 8651-7800"])
    tr, rep = extract_icf.extract_screens(en_mod.pdf_lines(str(pdf)), "F1")
    assert rep["icf:2:3"] == "exact"
    assert tr["icf:2:3"].endswith("kontakin ang:") and "Office" not in tr["icf:2:3"]


def test_extract_screens_drops_the_page_footer_before_the_contact_table(tmp_path):
    """On the real F3/F4 papers the version footer lands between the "you can contact:"
    paragraph and the contact table — INSIDE the window, so cutting at the table furniture
    leaves it in the stored paragraph (it shipped as "... mokontak sa: ICF ver.07/25/2026 |
    Translated Questionnaire ver.08/21/2026"). Dropped by line, like extract_notes' dumps."""
    en2 = icf_content.SCREENS["F1"][1]
    pdf = tmp_path / "F1-Tagalog_x_Aug21.pdf"
    _paper_pdf(pdf, [en2[3], FIL_CONTACT,
                     "ICF ver.07/25/2026 | Translated Questionnaire ver.08/21/2026",
                     "Office Email Contact No"])
    tr, rep = extract_icf.extract_screens(en_mod.pdf_lines(str(pdf)), "F1")
    assert tr["icf:2:3"] == FIL_CONTACT
    assert "ver." not in tr["icf:2:3"]


def test_extract_screens_skips_extra_english_printed_after_a_prefix_anchor(tmp_path):
    """F3-Hiligaynon's privacy paragraph carries a clause the build's English does not, so
    the anchor matches only a PREFIX and the rest of the paper's English sits in front of
    the translation. The paper's English ends where the anchor's own tail ends."""
    en2 = icf_content.SCREENS["F1"][1]
    paper_en = en_mod.norm(en2[0]).replace(
        "we will never include",
        "we will never share your family's or child's personal information outside of the "
        "study team. We will never include")
    fil_privacy = ("Nangangako kaming pangalagaan ang inyong pribadong impormasyon. Hindi "
                   "namin ibabahagi ang inyong pangalan sa sinuman.")
    pdf = tmp_path / "F1-Tagalog_x_Aug21.pdf"
    _paper_pdf(pdf, [paper_en, fil_privacy, en2[1]])
    tr, rep = extract_icf.extract_screens(en_mod.pdf_lines(str(pdf)), "F1")
    assert rep["icf:2:0"] == "prefix"
    assert tr["icf:2:0"] == fil_privacy


def test_build_icf_writes_english_alongside_and_overrides(tmp_path):
    src = tmp_path / "Translations"; src.mkdir()
    en1 = icf_content.SCREENS["F1"][0]
    _paper_pdf(src / "F1-Tagalog_x_Aug21.pdf", [en1[2], FIL_P3, en1[1], FIL_P2])
    ov = {"F1": {"icf:1:2:FIL": {"keep": "PRIOR", "reason": "test"},
                 "icf:1:1:FIL": {"keep": "", "reason": "force English"}}}
    icf, report = extract_icf.build_icf(str(src), ov, {})
    assert icf["F1"]["icf:1:2"] == {"EN": en1[2], "FIL": "PRIOR"}
    assert icf["F1"]["icf:1:1"] == {"EN": en1[1], "FIL": ""}
    assert icf["_provenance"]["aug21"]["n_overridden"] == 2
    assert report["F1"]["FIL"]["icf:1:2"] == "override"


def test_locate_matches_an_anchor_the_paper_prints_without_its_colon():
    """The F1-Bisaya/Cebuano papers print the rights paragraph in full but drop its trailing
    colon and run the translation straight on. locate() splits on whitespace, so "contact:"
    != "contact" would cost the WHOLE last word and leave it in front of the translation."""
    en = extract_icf.plain(icf_content.SCREENS["F1"][1][3])
    assert en.endswith("contact:")
    low = en_mod.norm(en.rstrip(":") + " " + BIS_CONTACT).lower()
    start, end, kind = extract_icf.locate(low, en)
    assert (start, kind) == (0, "exact")
    assert low[end:].lstrip().startswith("kung aduna")


def test_extract_screens_leaves_no_english_word_at_the_head_of_a_translation(tmp_path):
    """Regression (shipped once): icf.json stored "contact Kung aduna pa kay mga pangutana
    ..." for F1 BIS/CEB icf:2:3 - the enumerator reads a stray English word aloud at the top
    of the rights paragraph. The anchor's dropped colon is the whole cause."""
    en2 = icf_content.SCREENS["F1"][1]
    pdf = tmp_path / "F1-Bisaya_x_Aug21.pdf"
    _paper_pdf(pdf, [en_mod.norm(en2[3]).rstrip(":") + " " + BIS_CONTACT,
                     "Office Email Contact No"])
    tr, rep = extract_icf.extract_screens(en_mod.pdf_lines(str(pdf)), "F1")
    assert rep["icf:2:3"] == "exact"
    assert tr["icf:2:3"] == BIS_CONTACT


def test_extract_screens_walks_off_a_short_anchor_tail_left_by_a_prefix_match(tmp_path):
    """A prefix match stops mid-anchor; when the leftover tail is shorter than locate()'s
    min_words the suffix re-match cannot fire, so the tail is walked off token by token.
    Here the paper also drops the comma after "participant", which defeats both exact
    forms and forces the prefix path."""
    en2 = icf_content.SCREENS["F1"][1]
    paper_en = en_mod.norm(en2[3]).replace("participant,", "participant").rstrip(":")
    pdf = tmp_path / "F1-Bisaya_x_Aug21.pdf"
    _paper_pdf(pdf, [paper_en + " " + BIS_CONTACT, "Office Email Contact No"])
    tr, rep = extract_icf.extract_screens(en_mod.pdf_lines(str(pdf)), "F1")
    assert rep["icf:2:3"] == "prefix"
    assert tr["icf:2:3"] == BIS_CONTACT


def test_drop_anchor_tail_stops_at_the_first_token_the_window_does_not_repeat():
    """The walk may only ever remove text the anchor itself continues with."""
    assert extract_icf._drop_anchor_tail("contact Kung aduna", "contact:") == "Kung aduna"
    assert extract_icf._drop_anchor_tail("Kung aduna", "contact:") == "Kung aduna"
    assert extract_icf._drop_anchor_tail("you can contact Kung aduna",
                                         "you can contact:") == "Kung aduna"
    # "can" is not the anchor's next word -> the walk stops and nothing more is removed
    assert extract_icf._drop_anchor_tail("you can Kung aduna", "you will contact:") == \
        "can Kung aduna"


def test_no_stored_icf_paragraph_starts_with_an_english_token():
    """Token-level bleed scan over the shipped icf.json (phrase-level scans missed the
    single-word leader). Every stored translation's first token must not be an English word
    the paragraph's own EN anchor opens or ends with."""
    path = os.path.join(HERE, "icf.json")
    if not os.path.exists(path):
        pytest.skip("icf.json not built yet - run extract_icf.py --json first")
    data = json.load(io.open(path, encoding="utf-8"))
    bad = []
    for inst, block in data.items():
        if inst == "_provenance":
            continue
        for key, entry in block.items():
            en_tokens = {w.lower().strip(".,:;()'\"?!") for w in en_mod.norm(entry["EN"]).split()}
            for loc, val in entry.items():
                if loc == "EN" or not val:
                    continue
                head = val.split()[0].lower().strip(".,:;()'\"?!")
                if head in en_tokens and head not in _SHARED_HEADS:
                    bad.append((inst, key, loc, val[:60]))
    assert bad == [], f"English token leads a stored ICF paragraph: {bad}"


def test_generators_hold_per_language_overrides():
    """F3/F4 generate_qsf import generate_dcf at module top; sys.modules caches F1's copy,
    so each instrument is loaded with its own dir at sys.path[0] and the cache cleared."""
    import importlib.util
    for inst in ("F1", "F3", "F4"):
        inst_dir = os.path.join(CSPRO, inst)
        for m in ("generate_dcf", "generate_qsf", f"qsf_{inst}"):
            sys.modules.pop(m, None)
        sys.path.insert(0, inst_dir)
        try:
            spec = importlib.util.spec_from_file_location(f"qsf_{inst}", os.path.join(inst_dir, "generate_qsf.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            sys.path.remove(inst_dir)
            sys.modules.pop("generate_dcf", None)
        ov = mod.OVERRIDES["ICF_PART1"]
        assert isinstance(ov, dict) and set(ov) == {"EN", *icf_content.ICF_LANGS}, inst
        assert all("\n" not in v for v in ov.values()), inst


# 2026-08-27 (#1335/#1338/#1345): def:<q> rows + keep text without an extract candidate


def test_merge_notes_keep_text_writes_without_an_extract_candidate():
    from extract_notes import merge_notes
    fresh = {"F1": {"english": {"def:44": "Capitation is the amount per year."}, "translations": {}}}
    ov = {"F1": {"note:def:44:CEB": {"keep": "Capitation mao ang kantidad.", "reason": "r"}}}
    merged, counts = merge_notes({}, fresh, ov, {"date": "2026-08-27", "source": "t"})
    assert merged["F1"]["translations"]["def:44"]["CEB"] == "Capitation mao ang kantidad."
    assert counts["overridden"] == 1


def test_english_notes_registers_the_per_question_instruction_rows():
    from extract_notes import english_notes
    notes = english_notes("F1")
    assert notes["def:44"].startswith("Capitation is the amount per year")
    assert notes["def:52"].startswith("These are the requirements") and notes["def:52"].endswith("SELECT ALL THAT APPLY.")
