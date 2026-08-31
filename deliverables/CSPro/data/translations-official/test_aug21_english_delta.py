import json
from pathlib import Path

import pytest

import aug21_english_delta as d
from conftest import make_pdf


def test_numbered_labels_dcf_keeps_first_label_per_qnum(tmp_path):
    dcf = {"name": "T", "levels": [{"name": "L", "records": [{"name": "R", "items": [
        {"name": "Q5_SEX", "labels": [{"text": "5. Sex at birth"}],
         "valueSets": [{"name": "Q5_SEX_VS1", "labels": [{"text": "5. Sex at birth"}],
                        "values": [{"labels": [{"text": "Male"}], "pairs": [{"value": "1"}]}]}]},
        {"name": "Q6_AGE", "labels": [{"text": "6. Age in years"}]},
        {"name": "Q6_AGE_TXT", "labels": [{"text": "6. Age — specify text"}]},
    ]}]}]}
    p = tmp_path / "t.dcf"
    p.write_text(json.dumps(dcf), encoding="utf-8")
    out = d.numbered_labels_dcf(p)
    assert out == {"5": "5. Sex at birth", "6": "6. Age in years"}


def test_numbered_labels_items_ts_skips_subfields(tmp_path):
    p = tmp_path / "items.ts"
    p.write_text(
        "{ id: 'Q4', section: 'A', label: { en: 'How old are you?', fil: 'Ilang taon?' }, "
        "subFields: [{ id: 'Q4_1', label: { en: 'Year(s)' }, kind: 'number' }] },\n"
        "{ id: 'Q5', section: 'A', label: { en: 'What is your role?' } },\n"
        "{ id: 'Q13_1', displayNumber: 'Q13.1', section: 'B', label: { en: 'If yes, why?' } },\n",
        encoding="utf-8")
    assert d.numbered_labels_items_ts(p) == {"4": "How old are you?", "5": "What is your role?",
                                             "13.1": "If yes, why?"}


def test_paper_numbered_and_compare(tmp_path):
    pdf = tmp_path / "F9-English_x_Aug21.pdf"
    make_pdf(pdf, ["5. Sex at birth", "Male  Female",
                   "6. Age at last birthday (completed years)",
                   "7. New paper-only item",
                   "97.1 Other than the expenses above",      # decimal number, NO dot (F3 layout)
                   "115.1. Other than the expenses above"])   # decimal number WITH dot
    paper = d.paper_numbered(pdf)
    assert paper["5"] == ["Sex at birth Male Female"]
    assert paper["97.1"] == ["Other than the expenses above"]
    assert paper["115.1"] == ["Other than the expenses above"]
    build = {"5": "5. Sex at birth", "6": "6. Age in years"}
    r = d.compare(build, paper)
    assert r["match"] == 1 and r["total"] == 2
    assert r["diffs"][0]["q"] == "6"
    assert r["paper_only"] == ["7", "97.1", "115.1"]


def test_compare_accepts_any_occurrence(tmp_path):
    # F1 layout: the Result-of-Visit list "1. Completed ... 4. Incomplete" precedes Q1
    pdf = tmp_path / "F9-English_x_Aug21.pdf"
    make_pdf(pdf, ["1. Completed", "2. Postponed", "1. What is your name?", "2. What is your designation?"])
    paper = d.paper_numbered(pdf)
    assert paper["1"] == ["Completed", "What is your name?"]
    r = d.compare({"1": "1. What is your name?", "2": "2. What is your designation?"}, paper)
    assert r["match"] == 2 and r["diffs"] == [] and r["paper_only"] == []


# --- fix round 1, finding 3: leading vs. mid-sentence brackets must not be folded the same way ---

def test_norm_strips_midsentence_bracket_but_keeps_leading_instruction():
    from textnorm import norm
    # mid-sentence: a template fill placeholder -- both sides normalise to the same stem
    # regardless of the bracket's literal token text
    assert norm("Is [facility_name] the facility?") == norm("Is [facility_name_input] the facility?")
    # leading: a real interviewer instruction -- left as literal words, not folded away
    assert norm("[Answer only \"yes\" in Q112] After you went") == "answer only yes in q112 after you went"


def test_compare_flags_paper_only_leading_instruction_as_diff():
    # F4 Q117/131/135: paper carries a leading bracketed instruction the build lacks
    # entirely -- must surface as a diff, not a false match (was the fix-round-1 bug)
    build = {"117": "117. After you went to the specialist, did they follow up with you?"}
    paper = {"117": ["[Answer only \"yes\" in Q112] After you went to the specialist, did they follow up with you?"]}
    r = d.compare(build, paper)
    assert r["match"] == 0
    assert r["diffs"][0]["q"] == "117"


def test_compare_matches_midsentence_facility_placeholder_regardless_of_token():
    # F3 Q66/Q88: build and paper both carry a mid-sentence facility-name placeholder,
    # spelled with different literal tokens -- this must still match
    build = {"66": "66. Is [facility_name_input] the facility you usually go to?"}
    paper = {"66": ["Is [facility_name] the facility you usually go to?"]}
    r = d.compare(build, paper)
    assert r["match"] == 1 and r["diffs"] == []


# --- fix round 1, finding 1: --generator selects a measurement METHOD, never an --only filter ---

def test_generator_flag_does_not_filter_the_instrument_list(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(d, "BUILDS", {"F1": "b1", "F3": "b3"})
    monkeypatch.setattr(d, "GENERATORS", {"F3": "gen.py"})
    monkeypatch.setattr(d, "english_pdf", lambda inst: str(tmp_path / f"{inst}.pdf"))
    monkeypatch.setattr(d, "paper_numbered", lambda pdf: {})
    monkeypatch.setattr(d, "numbered_labels_dcf", lambda path: calls.append(("dcf", path)) or {})
    monkeypatch.setattr(d, "numbered_labels_generator", lambda inst: calls.append(("gen", inst)) or {})
    d.main(["--generator", "F3", "--out", str(tmp_path)])
    # both instruments ran -- passing --generator F3 must not make F1 vanish from the run
    assert calls == [("dcf", "b1"), ("gen", "F3")]


def test_f3_uses_the_generator_by_default_with_no_flag(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(d, "BUILDS", {"F1": "b1", "F3": "b3"})
    monkeypatch.setattr(d, "GENERATORS", {"F3": "gen.py"})
    monkeypatch.setattr(d, "english_pdf", lambda inst: str(tmp_path / f"{inst}.pdf"))
    monkeypatch.setattr(d, "paper_numbered", lambda pdf: {})
    monkeypatch.setattr(d, "numbered_labels_dcf", lambda path: calls.append(("dcf", path)) or {})
    monkeypatch.setattr(d, "numbered_labels_generator", lambda inst: calls.append(("gen", inst)) or {})
    d.main(["--out", str(tmp_path)])  # bare invocation, no --generator flag at all
    # F3 must still route through the generator -- never the written .dcf as a silent default
    assert calls == [("dcf", "b1"), ("gen", "F3")]
