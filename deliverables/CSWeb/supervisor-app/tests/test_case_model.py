import os
from case_model import load_cases, Case

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def test_load_f3_normalizes_three_cases():
    cases = load_cases(os.path.join(FIX, "f3_sample.csv"), "F3")
    assert len(cases) == 3
    c0, c1, c2 = cases
    # case 0: completed, has gps + photo, answers present
    assert c0.case_key == "010280001001"
    assert c0.facility == "01-02-800-01"
    assert c0.disposition == "complete"
    assert c0.has_gps is True and c0.has_photo is True
    assert c0.answers_present is True
    # case 1: withdraw (CASE_DISPOSITION=2 -> partial), no gps, no photo
    assert c1.disposition == "partial"
    assert c1.result_code == "6"
    assert c1.has_gps is False and c1.has_photo is False
    # case 2: in progress (CASE_DISPOSITION=0), blank result + blank consent
    assert c2.disposition == "in_progress"
    assert c2.answers_present is False


def test_load_f1_reads_disposition_sentinel_with_result_fallback():
    # F1 gained CASE_DISPOSITION + BREAKOFF in #744 (2026-06-23); the engine must read the
    # sentinel when populated and fall back to the result code for pre-#744 (blank) cases.
    cases = load_cases(os.path.join(FIX, "f1_sample.csv"), "F1")
    assert len(cases) == 4
    c0, c1, c2, c3 = cases
    # case 0: completed via sentinel (CASE_DISPOSITION=1), gps + photo + answers present
    assert c0.facility == "13-80-100-02"
    assert c0.disposition == "complete"
    assert c0.has_gps is True and c0.has_photo is True and c0.answers_present is True
    # case 1: broke off (CASE_DISPOSITION=2 -> partial) even though result code is 3 (Refused)
    assert c1.disposition == "partial"
    assert c1.result_code == "3"
    assert c1.has_gps is False and c1.has_photo is False
    # case 2: in progress (CASE_DISPOSITION=0), blank result + blank answers
    assert c2.disposition == "in_progress"
    assert c2.answers_present is False
    # case 3: PRE-#744 case — blank CASE_DISPOSITION, falls back to result code 1 -> complete
    assert c3.disposition == "complete"
