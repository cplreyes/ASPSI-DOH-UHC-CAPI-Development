from case_model import Case
from partials import list_partials


def _c(disp, result):
    return Case("F3", "010280001001", "01-02-800-01", "x", disp, result, False, False, "20260620", False)


def test_partials_lists_noncomplete_with_reasons():
    cases = [_c("complete", "1"), _c("partial", "6"), _c("partial", "3"), _c("in_progress", "")]
    rows = list_partials(cases)
    assert len(rows) == 3
    reasons = {r.reason for r in rows}
    assert "Withdrew" in reasons
    assert "Postponed" in reasons
    assert any("In progress" in r for r in reasons)
