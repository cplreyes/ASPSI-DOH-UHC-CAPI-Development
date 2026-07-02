from case_model import Case
from assignment import Assignment
from coverage import compute_coverage


def _c(fac, disp):
    return Case("F3", fac.replace("-", "") + "001", fac, "x", disp, "1", True, True, "20260620", True)


def test_coverage_counts_done_partial_and_remaining():
    cases = [_c("01-02-800-01", "complete"), _c("01-02-800-01", "complete"),
             _c("01-02-800-01", "partial"), _c("01-02-800-02", "complete")]
    assignments = {("F3", "01-02-800-01"): Assignment("se-004", "01-02-800-01", "F3", 10),
                   ("F3", "01-02-800-02"): Assignment("se-011", "01-02-800-02", "F3", 10)}
    rows = {(r.instrument, r.facility): r for r in compute_coverage(cases, assignments)}
    r1 = rows[("F3", "01-02-800-01")]
    assert (r1.done, r1.partial, r1.remaining, r1.behind) == (2, 1, 8, True)
    assert r1.enumerator_id == "se-004"
    r2 = rows[("F3", "01-02-800-02")]
    assert (r2.done, r2.remaining) == (1, 9)
