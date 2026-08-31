import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anchor_extract_f2 as x  # noqa: E402

LABELS = {
    "What is your role at this health facility?": {},
    "Administrator": {},
    "Other (specify)": {},
    "How old are you as of your last birthday (in years)?": {},
}

# Tagalog-style layout (English line, translation line, boxed options)
TAGALOG = ("4. How old are you as of your last birthday (in years)? "
           "Ilang na kayong taon noong huling kaarawan ninyo? "
           "5. What is your role at this health facility? "
           "Ano ang iyong tungkulin sa health facility na ito? "
           "☐ Administrator Tagapangasiwa ☐ Other (specify) Iba pa, tukuyin 6. Next")

# Bicolano-style inline layout: options echo English; 'Other' glued/truncated
BICOL = ("4. How old are you as of your last birthday (in years)? "
         "Pira an edad mo sa huring kaarawan mo (sa taon)? "
         "5. What is your role at this health facility? "
         "Ano an saimong papel sa health facility na ini? "
         "☐ Administrator Administrator ☐ Other (specify) ba pa, ispecify 6. Next")

YESNO_LABELS = {"Do you have a license?": {}, "Yes": {}, "No": {}}
# short anchors: 'Yes'/'No' must bound AND emit when box-prefixed; a bare 'no'
# inside the translation must NOT cut the stem span
YESNO = ("7. Do you have a license? Mayroon ka bang lisensya (oo o no)? "
         "☐ Yes Oo ☐ No Hindi")


def test_spans_between_anchors_tagalog():
    r = x.extract_text(TAGALOG, LABELS)
    # Task 21b: the trailing `5.` — the NEXT question's number, which this test used to
    # assert as `... ninyo? 5` — is paper row furniture and is now stripped (fact 2).
    assert r["clean"]["How old are you as of your last birthday (in years)?"] == \
        "Ilang na kayong taon noong huling kaarawan ninyo?"
    assert r["clean"]["What is your role at this health facility?"] == \
        "Ano ang iyong tungkulin sa health facility na ito?"
    assert r["clean"]["Administrator"] == "Tagapangasiwa"
    assert r["clean"]["Other (specify)"] == "Iba pa, tukuyin 6. Next"


def test_bicolano_echo_is_flagged_not_imported():
    r = x.extract_text(BICOL, LABELS)
    assert "Administrator" not in r["clean"]
    flagged = {f["en"]: f for f in r["flagged"]}
    assert "echo-english" in flagged["Administrator"]["flags"]
    assert flagged["Administrator"]["tr"] == "Administrator"
    # stems still extract from the inline layout — no line assumptions
    assert r["clean"]["What is your role at this health facility?"] == \
        "Ano an saimong papel sa health facility na ini?"
    assert r["clean"]["Other (specify)"] == "ba pa, ispecify 6. Next"


def test_short_yes_no_anchors_extract_and_stem_not_bled():
    r = x.extract_text(YESNO, YESNO_LABELS)
    assert r["clean"]["Yes"] == "Oo"
    assert r["clean"]["No"] == "Hindi"
    assert r["clean"]["Do you have a license?"] == "Mayroon ka bang lisensya (oo o no)?"
    assert not [f for f in r["flagged"] if f["en"] == "Do you have a license?"]


def test_runaway_cap_counts_kept_hits_not_raw_matches():
    # Regression: on the Ilocano paper 'no' matches 122x raw but is box-prefixed
    # only 40x. Capping the RAW finditer list dropped real '☐ No' boundaries and
    # let the preceding span bleed across them, silently, into the clean file.
    noise = " ".join(["no"] * (x.MAX_OCC + 6))
    text = ("7. Do you have a license? Mayroon ka bang lisensya " + noise + " ? "
            "☐ Yes Oo ☐ No Hindi")
    r = x.extract_text(text, YESNO_LABELS)
    assert r["clean"]["Yes"] == "Oo"
    assert r["clean"]["No"] == "Hindi"


def test_normalized_collisions_emit_under_every_original():
    labels = {"Other (specify)": {}, "Other, specify": {}, "What is your role at this health facility?": {}}
    text = ("5. What is your role at this health facility? Ano ang tungkulin mo? "
            "☐ Other (specify) Iba pa, tukuyin")
    r = x.extract_text(text, labels)
    assert r["collisions"] == {"other specify": ["Other (specify)", "Other, specify"]}
    assert r["clean"]["Other (specify)"] == "Iba pa, tukuyin"
    assert r["clean"]["Other, specify"] == "Iba pa, tukuyin"


def test_f2_labels_reads_english_strings_json(tmp_path):
    p = tmp_path / "english-strings.json"
    p.write_text(json.dumps({"count": 2, "strings": [
        {"text": "Yes", "kinds": ["choice.label"], "ids": ["Q7"]},
        {"text": "What is your name?", "kinds": ["item.label"], "ids": ["Q1"]}]}),
        encoding="utf-8")
    labs = x.f2_labels(str(p))
    assert list(labs) == ["Yes", "What is your name?"]
    assert labs["Yes"] == {}


def test_paper_glob_matches_aug21_names(tmp_path):
    (tmp_path / "F2-Cebuano_Healthcare Worker_Survey_UHC Year 2_Aug21.pdf").write_bytes(b"")
    (tmp_path / "F2-Tagalog_Healthcare Worker Survey Questionnaire_UHC Year 2_Aug21.pdf").write_bytes(b"")
    assert x.find_paper(str(tmp_path), "Cebuano").name.startswith("F2-Cebuano_")
    assert x.find_paper(str(tmp_path), "Tagalog").name.startswith("F2-Tagalog_")
    assert x.find_paper(str(tmp_path), "Waray") is None


# ---- Task 16b fix round 1: the Aug-21 LAYOUT rules must reach the F2 extract too ----
# anchor_extract_f2 borrows clean_span()/qa_flags() from anchor_extract, so every layout
# rule added there applies to F2 for free. That coupling is what went stale: the extract
# in out-aug21/F2/ was produced by Tasks 13/14 BEFORE the rules existed and still carried
# 224 values with an English interviewer directive or an angle-bracket routing note.
# Both pages below are the real Aug-21 F2 Tagalog layouts that produced two of them.

DIRECTIVE_LABELS = {
    "If yes, was it a result of the UHC Act enacted in 2019?": {},
    "What is your role at this health facility?": {},
}
# F2-Tagalog: the directive sits BETWEEN the English question and its translation, and is
# not a spec string, so it used to land inside the span ('SELECT ONE ANSWER ONLY Kung oo,').
DIRECTIVE_PAGE = ("43. If yes, was it a result of the UHC Act enacted in 2019? "
                  "SELECT ONE ANSWER ONLY "
                  "Kung oo, resulta ba ito ng UHC Act na naisabatas noong 2019? "
                  "What is your role at this health facility? Ano ang iyong tungkulin?")

ROUTING_LABELS = {"Dentist": {}, "Nurse": {}}
# F2-Tagalog: the anchor 'Dentist' matches the word INSIDE the routing note, so the span
# opens mid-note and the old extract shipped 'otherwise proceed to Q91>' as fil Dentist.
ROUTING_PAGE = ("Lubos na Nasiyahan: Kaunting pagbabago lang ang kailangan "
                "<proceed to Q63 if doctor/ dentist, otherwise proceed to Q91> "
                "\u2610 Nurse Nars")
# a note whose closing '>' is past the next anchor: the span holds only its opening half
# ('<only for those who answered \u201cyes\u201d to'), six real fil values.
HALF_NOTE_PAGE = ("\u2610 Nurse <only for those who answered \u201cyes\u201d to "
                  "\u2610 Dentist Dentista")


def test_english_directive_never_reaches_an_f2_clean_value():
    r = x.extract_text(DIRECTIVE_PAGE, DIRECTIVE_LABELS)
    assert r["clean"]["If yes, was it a result of the UHC Act enacted in 2019?"] == \
        "Kung oo, resulta ba ito ng UHC Act na naisabatas noong 2019?"
    assert not [v for v in r["clean"].values() if x._ae.has_directive(v)]


def test_routing_note_tail_never_reaches_an_f2_clean_value():
    r = x.extract_text(ROUTING_PAGE, ROUTING_LABELS)
    assert "Dentist" not in r["clean"]
    assert "routing-note" in [f for f in r["flagged"] if f["en"] == "Dentist"][0]["flags"]
    assert r["clean"]["Nurse"] == "Nars"
    assert not [v for v in r["clean"].values() if "<" in v or ">" in v]


def test_half_cut_routing_note_is_not_shipped_as_an_f2_translation():
    r = x.extract_text(HALF_NOTE_PAGE, ROUTING_LABELS)
    assert "Nurse" not in r["clean"]
    assert [f for f in r["flagged"] if f["en"] == "Nurse"]
    assert not [v for v in r["clean"].values() if "<" in v or ">" in v]


# ---- Task 21b: the Aug-21 F2 paper LAYOUT rules -------------------------------------
# anchor_extract_f2 borrowed anchor_extract's clean_span()/qa_flags() in Task 16b, but
# its own span logic was still Task 14's, so 29% of the F2 write set was defective
# (task-22-report.md).  The five facts below are verified against the real page dumps in
# text-aug21/F2_*.txt; every page string in this block is copied from one of them.
#
# extract_text() now takes an optional `meta` map — {EN text: {"kinds": [...],
# "ids": [...]}}, what f2_meta() reads out of spec/english-strings.json.  Without it the
# extractor keeps its Task-14 behaviour, which is what the ten tests above assert.


def mk(*rows):
    """(text, kind, item id) rows -> the {text: {kinds, ids}} shape f2_meta() returns."""
    out = {}
    for text, kind, ident in rows:
        e = out.setdefault(text, {"kinds": [], "ids": []})
        if kind not in e["kinds"]:
            e["kinds"].append(kind)
        if ident not in e["ids"]:
            e["ids"].append(ident)
    return out


def labels_of(meta):
    return {t: {} for t in meta}


# ---- fact 1: a span stops dead at an embedded English anchor ----
# F2_FIL.txt: `Professional development opportunities` is Q109's option label, so it also
# matches inside Q107's Tagalog sentence and used to cut it to `Ako ay nasisiyahan sa`
# (26 of the 98 truncations are strict prefixes of the live value like this one).
PDO = "Professional development opportunities"
Q107 = "I am satisfied with the professional development opportunities I have in my job."
EMBEDDED_META = mk((Q107, "item.label", "Q107"), (PDO, "choice.label", "Q109"),
                   ("Yes", "choice.label", "Q107"), ("No", "choice.label", "Q107"))
EMBEDDED_PAGE = (
    "107. I am satisfied with the professional development opportunities I have in my "
    "job. Ako ay nasisiyahan sa professional development opportunities na mayroon ako "
    "sa aking trabaho. \u2610 Yes Oo \u2610 No Hindi")


def test_embedded_option_anchor_does_not_cut_a_question_span():
    r = x.extract_text(EMBEDDED_PAGE, labels_of(EMBEDDED_META), EMBEDDED_META)
    assert r["clean"][Q107] == ("Ako ay nasisiyahan sa professional development "
                               "opportunities na mayroon ako sa aking trabaho.")
    assert r["clean"]["Yes"] == "Oo"
    assert r["clean"]["No"] == "Hindi"
    assert PDO not in r["clean"]     # never printed behind a box on this page


def test_option_anchor_still_extracts_from_its_own_box_row():
    """The guard on the box gate: where the paper DOES print the option row the option
    keeps anchoring and keeps emitting.  Not a reproduction — it passes before and after."""
    page = ("111. Which of these? Alin sa mga ito? "
            "\u2610 Professional development opportunities Mga pagkakataon sa pag-unlad "
            "\u2610 Salary Sahod")
    meta = mk(("Which of these?", "item.label", "Q111"),
              (PDO, "choice.label", "Q111"), ("Salary", "choice.label", "Q111"))
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"][PDO] == "Mga pagkakataon sa pag-unlad"
    assert r["clean"]["Salary"] == "Sahod"


def test_section_title_anchors_only_behind_its_section_letter():
    """F2_BCL.txt: the section title `YAKAP/Konsulta Package` also occurs inside Q32's
    Bicolano sentence, where it cut the translation to `Arin sa mga masunod an kaiba sa`
    and handed the TITLE the directive that followed it."""
    q32 = "Which of the following are included in the YAKAP/Konsulta package?"
    meta = mk(("YAKAP/Konsulta Package", "section.title", "C"),
              (q32, "item.label", "Q32"), ("Pap smear", "choice.label", "Q32"))
    page = ("C. YAKAP/Konsulta Package 32. Which of the following are included in the "
            "YAKAP/Konsulta package? Arin sa mga masunod an kaiba sa YAKAP/Konsulta "
            "Package? \u2610 Pap smear Pap smear")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"][q32] == "Arin sa mga masunod an kaiba sa YAKAP/Konsulta Package?"
    assert "YAKAP/Konsulta Package" not in r["clean"]


# ---- fact 2: furniture rides in ----
def test_specify_furniture_never_reaches_an_f2_clean_value():
    """F2_BCL.txt Q14: `(Specify the equipment) I-specify an mga equipment` is paper
    furniture for an input box, not part of the question's translation."""
    meta = mk(("What are these pieces of equipment?", "item.label", "Q14"),
              ("Has there been an increase in supplies in this facility?",
               "item.label", "Q15"))
    page = ("14. What are these pieces of equipment? Nano ini na mga equipment? "
            "(Specify the equipment) I-specify an mga equipment "
            "15. Has there been an increase in supplies in this facility? "
            "May mga nadagdag ba na mga gamit sa pasilidad na ini?")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"]["What are these pieces of equipment?"] == \
        "Nano ini na mga equipment?"
    assert not [v for v in r["clean"].values() if "Specify the equipment" in v]


def test_input_label_furniture_never_reaches_an_f2_clean_value():
    """F2_FIL.txt Q10: `Number of days Bilang ng araw` is the item's inputLabel, which
    applyTranslations() never localizes — so it is furniture in every span it lands in."""
    meta = mk(("How many days in a week do you work at this health facility?",
               "item.label", "Q10"),
              ("On average, how many hours do you work per day?", "item.label", "Q11"))
    page = ("10. How many days in a week do you work at this health facility? "
            "Ilang araw sa isang linggo ba kayong nagtatrabaho sa health facility na "
            "ito? Number of days Bilang ng araw "
            "11. On average, how many hours do you work per day? "
            "Sa karaniwan, ilang oras kada araw?")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"]["How many days in a week do you work at this health facility?"] == \
        "Ilang araw sa isang linggo ba kayong nagtatrabaho sa health facility na ito?"
    assert not [v for v in r["clean"].values() if "Number of days" in v]


def test_trailing_sub_question_numbers_are_stripped():
    """F2_FIL.txt Q71: `... implikasyon? 71a. <For those ...> 71b. <For those ...>`."""
    q71 = "If yes, what are the implications?"
    q72 = "Are you familiar with the Relative Value Unit (RVU)-based pricing?"
    meta = mk((q71, "item.label", "Q71"), (q72, "item.label", "Q72"))
    page = ("71. If yes, what are the implications? Kung oo, ano ang mga implikasyon? "
            "71a. <For those who answered \u2018Yes\u2019 in Q69> "
            "71b. <For those who answered \u2018Yes\u2019 in Q70> "
            "72. Are you familiar with the Relative Value Unit (RVU)-based pricing? "
            "Pamilyar ka ba?")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"][q71] == "Kung oo, ano ang mga implikasyon?"


def test_note_label_and_trailing_section_letter_are_stripped():
    """F2_FIL.txt Q11 and section B: the paper's `Note:` / `Tandaan:` label, the English
    inputLabel and the NEXT section's letter all ride into the spans."""
    q11 = "On average, how many hours do you work per day?"
    dole = ("According to DOLE, typically full-time is 8 hours per day, part-time is "
            "less than that.")
    pre = ("The following questions ask about your awareness of UHC. Please check the "
           "box/es of your answer.")
    meta = mk((q11, "item.label", "Q11"), (dole, "item.help", "Q11"),
              (pre, "section.preamble", "B"), ("Awareness of UHC", "section.title", "B"))
    page = ("11. On average, how many hours do you work per day? "
            "Sa karaniwan, ilang oras sa isang araw ba kayo nagtatrabaho? "
            "Note: According to DOLE, typically full-time is 8 hours per day, part-time "
            "is less than that. Tandaan: Ayon sa DOLE, kadalasan ang full-time ay 8 oras. "
            "Number of hours Bilang ng oras "
            "The following questions ask about your awareness of UHC. Please check the "
            "box/es of your answer. Ang mga sumusunod na tanong ay tungkol sa UHC. "
            "Pakilagyan ng tsek ang kahon ng iyong sagot. B. Awareness of UHC")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"][q11] == \
        "Sa karaniwan, ilang oras sa isang araw ba kayo nagtatrabaho?"
    assert r["clean"][dole] == "Ayon sa DOLE, kadalasan ang full-time ay 8 oras."
    assert r["clean"][pre] == ("Ang mga sumusunod na tanong ay tungkol sa UHC. "
                              "Pakilagyan ng tsek ang kahon ng iyong sagot.")


# ---- fact 3: directive mis-pairs ----
def test_local_directive_after_a_heading_is_flagged_never_clean():
    """F2_BCL.txt: the paper prints the SELECT-ALL directive and its Bicolano rendering
    straight after the heading, so the heading's whole span IS the directive."""
    meta = mk(("YAKAP/Konsulta Package", "section.title", "C"),
              ("Pap smear", "choice.label", "Q32"))
    page = ("C. YAKAP/Konsulta Package SELECT ALL THAT APPLY. Pilion an naangay. "
            "\u2610 Pap smear Pap smear")
    r = x.extract_text(page, labels_of(meta), meta)
    assert "YAKAP/Konsulta Package" not in r["clean"]
    fl = [f for f in r["flagged"] if f["en"] == "YAKAP/Konsulta Package"][0]["flags"]
    assert "local-directive" in fl or "directive-only" in fl


# ---- fact 4: sibling-bounded options (the 2026-08-13 mis-anchoring scar) ----
NEWS_META = mk(("News", "choice.label", "Q42"),
               ("Health center/facility", "choice.label", "Q42"),
               ("Legislation", "choice.label", "Q42"))


def test_sibling_option_row_pairs_each_label_with_its_own_translation():
    """The straight one-line option layout — a guard, not a reproduction."""
    page = ("\u2610 News Balita \u2610 Health center/facility Sentro sa panglawas "
            "\u2610 Legislation Balaod")
    r = x.extract_text(page, labels_of(NEWS_META), NEWS_META)
    assert r["clean"]["News"] == "Balita"
    assert r["clean"]["Health center/facility"] == "Sentro sa panglawas"
    assert r["clean"]["Legislation"] == "Balaod"


def test_reflowed_option_row_never_ships_a_sibling_translation():
    """F2_CEB.txt Q42, verbatim: the PDF reflow prints BOTH English labels first and both
    translations after, so `Health center/facility` shipped `Balita` — the News option's
    value, and the 2026-08-13 row-misalignment scar re-introduced."""
    page = ("\u2610 News \u2610 Health center/facility Balita Health center/facility "
            "\u2610 Legislation Balaod")
    r = x.extract_text(page, labels_of(NEWS_META), NEWS_META)
    assert r["clean"].get("Health center/facility") != "Balita"
    assert "Health center/facility" not in r["clean"]


def test_grid_bleed_fires_on_a_value_set_sibling():
    """qa_flags(siblings=) was never passed on the F2 side, so the sibling net was inert."""
    assert x.f2_siblings(NEWS_META)["news"] == {"health center facility", "legislation"}
    page = "\u2610 News Balita Health center/facility \u2610 Legislation Balaod"
    r = x.extract_text(page, labels_of(NEWS_META), NEWS_META)
    assert "News" not in r["clean"]
    assert "grid-bleed" in [f for f in r["flagged"] if f["en"] == "News"][0]["flags"]


# ---- fact 5: condensed / paraphrased anchors, and anchors the paper never printed ----
LONG_EN = ("The following questions ask about your awareness of UHC and the changes "
           "which may have occurred due to its implementation in this facility.")


def test_condensed_label_anchors_on_its_prefix_and_is_flagged_never_clean():
    meta = mk((LONG_EN, "section.preamble", "B"),
              ("What is your role?", "item.label", "Q5"))
    # the paper prints a LONGER paragraph than the spec string, so the verbatim anchor is
    # nowhere on the page and only its 12-word prefix can be found
    page = ("The following questions ask about your awareness of UHC and the changes, "
            "big or small, which may have occurred due to its implementation in this "
            "facility. "
            "Ang mga sumusunod na tanong ay tungkol sa iyong kamalayan sa UHC. "
            "5. What is your role? Ano ang iyong tungkulin?")
    r = x.extract_text(page, labels_of(meta), meta)
    assert LONG_EN not in r["clean"]
    row = [f for f in r["flagged"] if f["en"] == LONG_EN][0]
    assert "label-condensed" in row["flags"]
    assert row["tr"] == "Ang mga sumusunod na tanong ay tungkol sa iyong kamalayan sa UHC."


def test_anchor_absent_from_the_f2_paper_reaches_the_worklist():
    meta = mk(("What is your role?", "item.label", "Q5"),
              ("Nuclear medicine", "choice.label", "Q6"))
    page = "5. What is your role? Ano ang iyong tungkulin?"
    r = x.extract_text(page, labels_of(meta), meta)
    row = [f for f in r["flagged"] if f["en"] == "Nuclear medicine"][0]
    assert row["flags"] == ["not-in-paper"]
    assert row["tr"] == ""


# ---- round 2: the residual families the first real-data sweep left ----
def test_sentence_final_stop_and_colon_survive_clean_span():
    """clean_span() ends with .strip(" .:;,-"), which is right on an option row and wrong
    on a sentence: it made 130 of the 334 F2 write rows a strict prefix of the value the
    live map already held. The character is put back only when the PAPER printed it."""
    q = "All of my salary payments have arrived on time."
    stem = "I have worked overtime for:"
    meta = mk((q, "item.label", "Q101"), (stem, "item.label", "Q102"),
              ("1-2 hours", "choice.label", "Q102"))
    page = ("101. All of my salary payments have arrived on time. "
            "Tanan nako nga suweldo niabot sa saktong oras. "
            "\u2610 \u2610 \u2610 "
            "102. I have worked overtime for: Naka-overtime ko para sa: "
            "\u2610 1-2 hours 1-2 ka oras")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"][q] == "Tanan nako nga suweldo niabot sa saktong oras."
    assert r["clean"][stem] == "Naka-overtime ko para sa:"
    # and nothing is invented where the paper printed no stop
    assert r["clean"]["1-2 hours"] == "1-2 ka oras"



def test_ilocano_half_cut_paren_group_is_trimmed():
    """F2_ILO.txt wraps every translation in ( ). Where the span cuts one half off the
    stray bracket survives clean_span()'s balanced-group rules, because the OTHER half of
    a NESTED pair is still inside — `(Nangngegyo … (NBB)?` and `… klinika?) (`."""
    q7 = "Do you practice at any private facility/ clinic?"
    q41 = "Have you heard about the No Balance Billing (NBB)?"
    meta = mk((q7, "item.label", "Q7"), (q41, "item.label", "Q41"),
              ("Yes", "choice.label", "Q41"))
    page = ("7. Do you practice at any private facility/ clinic? "
            "<only for respondents from public facilities> "
            "(Agpraktis ka kadi iti aniaman a pribado a pasilidad/ klinika?) "
            "(<para laeng kadagiti respondents manipud kadagiti pasilidad ti publiko>) "
            "41. Have you heard about the No Balance Billing (NBB)? "
            "(Nangngegyo kadin ti maipapan iti No Balance Billing (NBB)? "
            "☐ Yes (Wen)")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"][q7] == "Agpraktis ka kadi iti aniaman a pribado a pasilidad/ klinika?"
    assert r["clean"][q41] == "Nangngegyo kadin ti maipapan iti No Balance Billing (NBB)?"


def test_note_label_in_the_middle_of_a_span_ends_it():
    """F2_HIL.txt Q11: Hiligaynon prints only the LOCAL note, so there is no English
    `According to DOLE …` anchor to end the question's span and the note rides in."""
    q11 = "On average, how many hours do you work per day?"
    pre = "The following questions ask about your awareness of UHC."
    meta = mk((q11, "item.label", "Q11"), (pre, "section.preamble", "B"))
    page = ("11. On average, how many hours do you work per day? "
            "Sa masami, pila ka oras ikaw magtrabaho sa isa ka adlaw? "
            "Note: Suno sa DOLE, ang full-time kalabanan 8 ka oras kada adlaw. "
            "The following questions ask about your awareness of UHC. Ang masunod...")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"][q11] == "Sa masami, pila ka oras ikaw magtrabaho sa isa ka adlaw?"


def test_trailing_bicolano_select_one_directive_is_flagged():
    """F2_BCL.txt Q13.1: Bicolano prints the local rendering of SELECT ONE ANSWER ONLY
    AFTER the translation, in sentence case, so neither skip_translated_directive() nor
    anchor_extract.CAPS_RUN can reach it."""
    q = "If yes, was it a result of the UHC Act enacted in 2019?"
    meta = mk((q, "item.label", "Q13_1"),
              ("Implemented as a direct result of the UHC Act", "choice.label", "Q13_1"))
    page = ("13.1. If yes, was it a result of the UHC Act enacted in 2019? "
            "SELECT ONE ANSWER ONLY. Kun iyo, resulta ba ini kan UHC Act 2019? "
            "Saro lang an pillion na simbag "
            "☐ Implemented as a direct result of the UHC Act "
            "Naipatupad ini resulta kan UHC Act")
    r = x.extract_text(page, labels_of(meta), meta)
    assert q not in r["clean"]
    assert "local-directive" in [f for f in r["flagged"] if f["en"] == q][0]["flags"]


# ---- the metadata seam itself ----
def test_f2_meta_reads_kinds_and_ids(tmp_path):
    p = tmp_path / "english-strings.json"
    p.write_text(json.dumps({"count": 2, "strings": [
        {"text": "Yes", "kinds": ["choice.label"], "ids": ["Q7", "Q12"]},
        {"text": "What is your name?", "kinds": ["item.label"], "ids": ["Q1"]}]}),
        encoding="utf-8")
    m = x.f2_meta(str(p))
    assert m["Yes"] == {"kinds": ["choice.label"], "ids": ["Q7", "Q12"]}
    assert x.f2_labels(str(p))["Yes"] == {}          # unchanged Task-14 shape


def test_f2_siblings_groups_choice_labels_by_parent_item():
    meta = mk(("Yes", "choice.label", "Q7"), ("No", "choice.label", "Q7"),
              ("Yes", "choice.label", "Q9"), ("Maybe", "choice.label", "Q9"),
              ("What is your name?", "item.label", "Q1"))
    sib = x.f2_siblings(meta)
    assert sib["yes"] == {"no", "maybe"}
    assert sib["no"] == {"yes"}
    assert "what is your name" not in sib


def test_meta_is_optional_and_absent_meta_keeps_the_task_14_span_rules():
    """The pre-flight ruling's `no rule, no change` guard: with no metadata nothing is
    gated, so the Task-14 answer stands."""
    r = x.extract_text(TAGALOG, LABELS)
    assert r["clean"]["Administrator"] == "Tagapangasiwa"
    assert r["clean"]["What is your role at this health facility?"] == \
        "Ano ang iyong tungkulin sa health facility na ito?"


# ---- fix round 1: box-less scale runs, and `not-in-paper` vs `gate-rejected` ----------
# The review measured 77 of the 247 `not-in-paper` rows as anchors the paper DOES print
# verbatim - every one of them a `choice.label` whose occurrences the box gate rejected.
# 42 of the 77 are the two Likert vocabularies, which the papers print as a BOX-LESS run
# (`Never Hindi kailanman Rarely Bihira ...`, F2_FIL.txt), i.e. exactly the second half of
# the brief's fact 4: "an option's span ends at the next box glyph OR the next sibling
# label".  Siblings now bound AND open a span, and an anchor that occurs but was gated is
# reported as `gate-rejected`, never as `not-in-paper`.

def val_of(r, en):
    """The span extracted for `en`, clean or flagged.  The run-floor tests below assert
    that a sentence was NOT cut into option rows; whether that sentence then trips one of
    the pre-existing June-5 nets (`glued-short-label`, `table-bleed` — both fire on a
    sentence that quotes `Yes`/`No`) is a different question and not this rule's."""
    if en in r["clean"]:
        return r["clean"][en]
    return [f for f in r["flagged"] if f["en"] == en][0]["tr"]


Q82 = "Do doctors adjust their professional fee based on the patient's ability to pay?"
Q83 = "How often do you charge your patients?"
SCALE_META = mk((Q82, "item.label", "Q82"), (Q83, "item.label", "Q83"),
                ("Never", "choice.label", "Q82"), ("Rarely", "choice.label", "Q82"),
                ("Sometimes", "choice.label", "Q82"), ("Often", "choice.label", "Q82"),
                ("Always", "choice.label", "Q82"))
# F2_FIL.txt, verbatim: no ballot box anywhere on the scale row.
SCALE_PAGE = (
    "82. Do doctors adjust their professional fee based on the patient's ability to "
    "pay? Inaayos ba ng mga doktor ang kanilang propesyonal na bayad batay sa kakayahan "
    "ng pasyente na magbayad? Never Hindi kailanman Rarely Bihira Sometimes Minsan "
    "Often Madalas Always Lagi "
    "83. How often do you charge your patients? Gaano ka kadalas maningil")


def test_boxless_scale_run_pairs_each_option_with_its_translation():
    r = x.extract_text(SCALE_PAGE, labels_of(SCALE_META), SCALE_META)
    assert r["clean"]["Never"] == "Hindi kailanman"
    assert r["clean"]["Rarely"] == "Bihira"
    assert r["clean"]["Sometimes"] == "Minsan"
    assert r["clean"]["Often"] == "Madalas"
    assert r["clean"]["Always"] == "Lagi"


def test_boxless_scale_run_still_bounds_the_question_above_it():
    """The other half of the same rule: the run must not ride into Q82's translation
    (the `hil` Q82 residual, where the scale IS printed with no English and cannot)."""
    r = x.extract_text(SCALE_PAGE, labels_of(SCALE_META), SCALE_META)
    assert r["clean"][Q82] == ("Inaayos ba ng mga doktor ang kanilang propesyonal na "
                               "bayad batay sa kakayahan ng pasyente na magbayad?")


def test_scale_run_member_the_paper_left_untranslated_is_empty_not_not_in_paper():
    """F2_FIL.txt prints `Neither Agree nor Disagree Disagree Hindi Sang- ayon` - the
    label is on the page with no translation after it.  `not-in-paper` said the paper
    never printed it; the honest answer is that its span is empty."""
    nad = "Neither Agree nor Disagree"
    meta = mk(("Strongly Agree", "choice.label", "Q97"), ("Agree", "choice.label", "Q97"),
              (nad, "choice.label", "Q97"), ("Disagree", "choice.label", "Q97"),
              ("Strongly Disagree", "choice.label", "Q97"),
              ("I am compensated fairly.", "item.label", "Q98"))
    page = ("Strongly Agree Lubos na Sang-ayon Agree Sang-ayon Neither Agree nor "
            "Disagree Disagree Hindi Sang- ayon Strongly Disagree Lubos na Hindi Sang- "
            "ayon 98. I am compensated fairly. Ako ay binabayaran nang patas.")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"]["Strongly Agree"] == "Lubos na Sang-ayon"
    assert r["clean"]["Agree"] == "Sang-ayon"
    assert r["clean"]["Strongly Disagree"] == "Lubos na Hindi Sang- ayon"
    row = [f for f in r["flagged"] if f["en"] == nad][0]
    assert row["flags"] == ["empty"]


def test_gate_rejected_anchor_is_not_reported_as_not_in_paper():
    """`Professional development opportunities` IS printed on the page - inside Q107's
    sentence.  The box gate is right to reject it; calling the row `not-in-paper` is a
    factually wrong reason for Task 45's worklist."""
    r = x.extract_text(EMBEDDED_PAGE, labels_of(EMBEDDED_META), EMBEDDED_META)
    row = [f for f in r["flagged"] if f["en"] == PDO][0]
    assert row["flags"] == ["gate-rejected"]
    assert row["tr"] == ""


def test_anchor_the_paper_never_prints_keeps_not_in_paper():
    """The guard on the new flag: a genuinely absent anchor keeps the old reason."""
    meta = mk(("What is your role?", "item.label", "Q5"),
              ("Nuclear medicine", "choice.label", "Q6"))
    page = "5. What is your role? Ano ang iyong tungkulin?"
    r = x.extract_text(page, labels_of(meta), meta)
    assert [f for f in r["flagged"]
            if f["en"] == "Nuclear medicine"][0]["flags"] == ["not-in-paper"]


def test_two_member_value_set_never_qualifies_as_a_boxless_run():
    """The floor under the rule: a run is trusted only when F2_RUN_MIN distinct siblings
    of one value set sit in it.  A bare `Yes o No` inside a sentence is two, so the
    sentence keeps its translation instead of being cut into option rows."""
    meta = mk(("Do you have a license?", "item.label", "Q7"),
              ("Yes", "choice.label", "Q7"), ("No", "choice.label", "Q7"))
    page = "7. Do you have a license? Kailangan mo bang sumagot ng Yes o No dito?"
    r = x.extract_text(page, labels_of(meta), meta)
    assert val_of(r, "Do you have a license?") == \
        "Kailangan mo bang sumagot ng Yes o No dito?"
    assert "Yes" not in r["clean"] and "No" not in r["clean"]
    assert [f for f in r["flagged"] if f["en"] == "Yes"][0]["flags"] == ["gate-rejected"]


def test_siblings_scattered_across_prose_never_qualify_as_a_run():
    """The other floor: the members must be ADJACENT (F2_RUN_GAP normalised chars), which
    is what a printed scale row is and what three option words quoted in running prose is
    not."""
    filler = "at iba pang salita na hindi naman bahagi ng anumang option row dito "
    meta = mk(("How often?", "item.label", "Q1"),
              ("Never", "choice.label", "Q1"), ("Rarely", "choice.label", "Q1"),
              ("Always", "choice.label", "Q1"))
    page = ("1. How often? Gaano kadalas ang Never " + filler + "o ang Rarely "
            + filler + "o kaya ang Always " + filler + "?")
    r = x.extract_text(page, labels_of(meta), meta)
    assert "Never" not in r["clean"]
    assert "Rarely" not in r["clean"]
    assert "Always" not in r["clean"]
    assert val_of(r, "How often?").startswith("Gaano kadalas ang Never")


def test_boxed_option_grid_is_never_rescued_as_a_run():
    """The regression the first cut of this rule caused, verbatim from F2_CEB.txt Q42:
    the grid's ECHO translations (`LGU/Barangay LGU/Barangay`, `Social Media Social
    Media`) are three box-less sibling occurrences inside the gap, so a distance-only run
    rule rescued them — and the box-less `Health center/facility` with them, which handed
    the boxed one the span `Balita` and put the 2026-08-13 scar straight back.  A value
    set the paper prints behind boxes is not a run, and a box between two members breaks
    the chain."""
    ids = ("News", "Health center/facility", "Legislation", "LGU/Barangay",
           "Social Media", "Friends/Family")
    meta = mk(*[(t, "choice.label", "Q42") for t in ids])
    page = ("☐ News ☐ Health center/facility Balita Health center/facility "
            "☐ Legislation Balaod ☐ LGU/Barangay LGU/Barangay "
            "☐ Social Media Social Media ☐ Friends/Family Higala/Pamilya")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"].get("Health center/facility") != "Balita"
    assert r["clean"]["Legislation"] == "Balaod"
    assert r["clean"]["Friends/Family"] == "Higala/Pamilya"


def test_boxed_value_set_is_skipped_even_where_the_run_shape_fits():
    """The `boxed` guard on its own: the same three siblings, no box between them, but
    one member of the value set IS printed behind a box on this page."""
    meta = mk(("Never", "choice.label", "Q1"), ("Rarely", "choice.label", "Q1"),
              ("Always", "choice.label", "Q1"), ("How often?", "item.label", "Q1"))
    page = ("1. How often? Gaano kadalas? ☐ Never Wala gid nga "
            "Never Rarely Always sa sulod hini nga sentence")
    r = x.extract_text(page, labels_of(meta), meta)
    assert "Rarely" not in r["clean"] and "Always" not in r["clean"]
    assert [f for f in r["flagged"] if f["en"] == "Rarely"][0]["flags"] == \
        ["gate-rejected"]


def test_f2_option_groups_are_the_value_sets_behind_the_run_rule():
    groups = x.f2_option_groups(SCALE_META)
    assert groups["Q82"] == frozenset({"never", "rarely", "sometimes", "often", "always"})
    assert "Q83" not in groups          # item labels are not options


# ---- Task 48: the ROW-INHERITANCE class on the F2 papers ----------------------------
# The F1/F3/F4 mechanism (anchor_extract.sibling_run) is on these pages too, and one of
# its rows is LIVE in production: `City / LGU standard referral form` in war.json carries
# its own translation with the ENTIRE `DOH standard referral form` translation glued to
# its tail, and the DOH row itself extracted `empty`. The paper prints the two English
# rows back to back and their two translations after them as one block — in the REVERSE
# order of the English rows, which is why no half of the block can be assigned.

_Q57 = "What type of referral form do you use to send to higher level facilities?"
_DOH_FORM = "DOH standard referral form"
_CITY_FORM = "City / LGU standard referral form"
_FAC_FORM = "Facility's standard referral form"
_REFERRAL_META = mk((_Q57, "item.label", "Q57"), (_DOH_FORM, "choice.label", "Q57"),
                    (_CITY_FORM, "choice.label", "Q57"), (_FAC_FORM, "choice.label", "Q57"))
# text-aug21/F2_WAR.txt @42483, verbatim.
_REFERRAL_PAGE = (
    "57. What type of referral form do you use to send to higher level facilities? "
    "Ano nga klase hin referral form an iyo ginagamit para ipadara ha mas hitaas nga "
    "lebel nga mga pasilidad? ☐ DOH standard referral form "
    "☐ City / LGU standard referral form "
    "Syudad / LGU surundon nga porma han pagrefer "
    "DOH nga surundon nga porma han pagrefer "
    "☐ Facility's standard referral form "
    "An surundon nga porma han pagrefer han pasilidad")


def test_adjacent_english_run_is_never_written_as_one_rows_translation():
    r = x.extract_text(_REFERRAL_PAGE, labels_of(_REFERRAL_META), _REFERRAL_META)
    assert _CITY_FORM not in r["clean"], \
        f"the live prod defect is still clean: {r['clean'].get(_CITY_FORM)!r}"
    row = [f for f in r["flagged"] if f["en"] == _CITY_FORM]
    assert row and "sibling-run" in row[0]["flags"], row
    assert _DOH_FORM not in r["clean"]
    # the row after the run carries its own box and its own translation
    assert r["clean"][_FAC_FORM] == "An surundon nga porma han pagrefer han pasilidad"


def test_a_boxed_f2_row_that_carries_its_own_translation_is_not_a_sibling_run():
    page = ("57. What type of referral form do you use to send to higher level "
            "facilities? Ano nga klase hin referral form? "
            "☐ DOH standard referral form DOH nga surundon nga porma han pagrefer "
            "☐ City / LGU standard referral form "
            "Syudad / LGU surundon nga porma han pagrefer")
    r = x.extract_text(page, labels_of(_REFERRAL_META), _REFERRAL_META)
    assert r["clean"][_DOH_FORM] == "DOH nga surundon nga porma han pagrefer"
    assert r["clean"][_CITY_FORM] == "Syudad / LGU surundon nga porma han pagrefer"
    assert not [f for f in r["flagged"] if "sibling-run" in f["flags"]]


_COVER = "PhilHealth will cover cost of treatment"
_INCLUDED = "Medicine and service are already included"
_DUNNO = "I don't know"
_Q128_META = mk(("What do you understand by No Balance Billing?", "item.label", "Q128"),
                (_COVER, "choice.label", "Q128"), (_INCLUDED, "choice.label", "Q128"),
                (_DUNNO, "choice.label", "Q128"))


def test_two_f2_choices_of_one_item_may_not_ship_the_same_translation():
    """text-aug21/F4_WAR.txt @86335 prints exactly this: the same Waray sentence against
    two different English option rows. Whatever the paper says, the two choices would be
    indistinguishable on screen, so neither is written."""
    page = ("128. What do you understand by No Balance Billing? Ano an imo nasasabtan? "
            "☐ PhilHealth will cover cost of treatment "
            "Mababayaran han PhilHealth an gastos han pagtambal "
            "☐ Medicine and service are already included "
            "Mababayaran han PhilHealth an gastos han pagtambal "
            "☐ I don't know Dire ako maaram")
    r = x.extract_text(page, labels_of(_Q128_META), _Q128_META)
    for en in (_COVER, _INCLUDED):
        assert en not in r["clean"], f"{en!r} shipped {r['clean'].get(en)!r}"
        row = [f for f in r["flagged"] if f["en"] == en]
        assert row and "duplicate-label" in row[0]["flags"], (en, row)
    assert r["clean"][_DUNNO] == "Dire ako maaram"


def test_the_same_f2_translation_under_two_different_items_is_allowed():
    meta = mk(("First question about payment?", "item.label", "Q10"),
              ("Out of pocket", "choice.label", "Q10"),
              ("Second question about payment?", "item.label", "Q20"),
              ("Paid from savings", "choice.label", "Q20"))
    page = ("10. First question about payment? Una nga pakiana? "
            "☐ Out of pocket Ginkuha ha bulsa "
            "20. Second question about payment? Ikaduha nga pakiana? "
            "☐ Paid from savings Ginkuha ha bulsa")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"]["Out of pocket"] == "Ginkuha ha bulsa"
    assert r["clean"]["Paid from savings"] == "Ginkuha ha bulsa"
    assert not [f for f in r["flagged"] if "duplicate-label" in f["flags"]]


def test_the_f2_row_inheritance_flags_are_in_the_qa_report_legend():
    assert "sibling-run" in x.LAYOUT_FLAGS
    assert "duplicate-label" in x.LAYOUT_FLAGS


def test_a_short_f2_label_with_a_long_translation_is_not_a_sibling_run():
    """The length floor. `Casual` -> `Saan a patinayon` is 2.7x its English and correct;
    one verbose rendering of a short word is not evidence of a two-row block, so
    F2_PAIR_BLOCK_MIN_EN keeps the size test off labels this short."""
    meta = mk(("What is your employment status?", "item.label", "Q20"),
              ("Contractual", "choice.label", "Q20"), ("Casual", "choice.label", "Q20"))
    page = ("20. What is your employment status? Ania ti kasasaad ti panagtrabahom? "
            "☐ Contractual ☐ Casual Saan a patinayon")
    r = x.extract_text(page, labels_of(meta), meta)
    assert r["clean"]["Casual"] == "Saan a patinayon"
    assert not [f for f in r["flagged"] if "sibling-run" in f["flags"]]
