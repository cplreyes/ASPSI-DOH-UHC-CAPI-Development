from coverage import CoverageRow
from partials import PartialRow
from qa_rules import Flag
from report_html import render_report


def test_report_has_three_panels_and_is_pii_light():
    cov = [CoverageRow("F3", "01-02-800-01", "se-004", 8, 1, 10, 2, True)]
    par = [PartialRow("F3", "010280001002", "01-02-800-01", "Withdrew")]
    fl = [Flag("010280001007", "01-02-800-01", "no_gps", "no GPS fix")]
    html = render_report(cov, par, fl, cluster="01028", generated="2026-06-21 22:10")
    assert "Coverage vs plan" in html and "Partials" in html and "Data-quality flags" in html
    assert "se-004" in html and "8" in html and "Withdrew" in html and "no GPS fix" in html
    # PII-light: a respondent name must never appear (enumerator NAME is not passed in)
    assert "Juan Dela Cruz" not in html


def test_empty_inputs_render_zero_not_error():
    html = render_report([], [], [], cluster="x", generated="t")
    assert "Coverage vs plan" in html   # renders, no crash
