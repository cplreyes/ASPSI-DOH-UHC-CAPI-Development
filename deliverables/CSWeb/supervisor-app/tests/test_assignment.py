import os
from assignment import load_assignments

FIX = os.path.join(os.path.dirname(__file__), "..", "assignments.example.csv")


def test_load_assignments_keys_by_instrument_and_facility():
    a = load_assignments(FIX)
    assert a[("F3", "01-02-800-01")].target == 10
    assert a[("F3", "01-02-800-01")].enumerator_id == "se-004"
    assert a[("F1", "01-02-800-01")].target == 1
    assert ("F3", "01-02-800-99") not in a
