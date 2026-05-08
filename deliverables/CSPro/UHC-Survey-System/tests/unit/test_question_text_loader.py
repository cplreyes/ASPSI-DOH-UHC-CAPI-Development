from shared.question_text_loader import load_question_texts

FIXTURE_MD = """
# F1 Skip Logic and Validations

Some preamble.

### Q1_NAME
1. What is your name?

### Q2_FACILITY_ROLE
2. What is your role at this facility?

### Q3_AGE
3. How old are you (in years)?

## Section B

### Q7_OWNERSHIP
7. Who owns this facility?
"""


def test_load_question_texts_extracts_each_item(tmp_path):
    md_path = tmp_path / "F1-spec.md"
    md_path.write_text(FIXTURE_MD, encoding="utf-8")
    texts = load_question_texts(md_path)
    assert texts["Q1_NAME"] == "1. What is your name?"
    assert texts["Q2_FACILITY_ROLE"] == "2. What is your role at this facility?"
    assert texts["Q3_AGE"] == "3. How old are you (in years)?"
    assert texts["Q7_OWNERSHIP"] == "7. Who owns this facility?"


def test_load_question_texts_missing_item_returns_none(tmp_path):
    md_path = tmp_path / "F1-spec.md"
    md_path.write_text(FIXTURE_MD, encoding="utf-8")
    texts = load_question_texts(md_path)
    assert texts.get("Q99_NOT_THERE") is None
