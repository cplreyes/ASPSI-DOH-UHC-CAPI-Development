from case_model import Case
from qa_rules import run_rules


def _c(**kw):
    base = dict(instrument="F3", case_key="010280001001", facility="01-02-800-01",
                enumerator_name="x", disposition="complete", result_code="1",
                has_gps=True, has_photo=True, final_visit_date="20260621",
                answers_present=True)
    base.update(kw)
    return Case(**base)


def test_no_gps_flag():
    flags = run_rules([_c(has_gps=False)], today="20260621")
    assert any(f.rule == "no_gps" for f in flags)


def test_no_photo_on_completed_flag():
    flags = run_rules([_c(has_photo=False, disposition="complete")], today="20260621")
    assert any(f.rule == "no_photo_completed" for f in flags)


def test_partial_without_photo_is_not_flagged_for_photo():
    flags = run_rules([_c(has_photo=False, disposition="partial", result_code="6")], today="20260621")
    assert not any(f.rule == "no_photo_completed" for f in flags)


def test_stuck_partial_flag():
    flags = run_rules([_c(disposition="in_progress", final_visit_date="20260618")], today="20260621")
    assert any(f.rule == "stuck_partial" for f in flags)


def test_disposition_mismatch_flag():
    flags = run_rules([_c(disposition="complete", answers_present=False)], today="20260621")
    assert any(f.rule == "disposition_mismatch" for f in flags)


def test_consent_contradiction_flag():
    flags = run_rules([_c(result_code="6", disposition="partial", answers_present=True)], today="20260621")
    assert any(f.rule == "consent_contradiction" for f in flags)


def test_clean_case_no_flags():
    assert run_rules([_c()], today="20260621") == []
