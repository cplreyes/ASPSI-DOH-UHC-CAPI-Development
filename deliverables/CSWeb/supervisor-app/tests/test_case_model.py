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
