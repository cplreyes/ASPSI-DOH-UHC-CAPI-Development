"""The #561 panel: every non-complete case with a human-readable disposition reason."""
from dataclasses import dataclass

# Result-code -> label, per instrument (matches ENUM_RESULT_OPTIONS_* in cspro_helpers.py).
RESULT_LABELS = {
    "F1": {"2": "Postponed", "3": "Refused", "4": "Incomplete"},
    "F3": {"3": "Postponed", "4": "Incomplete", "6": "Withdrew"},
    "F4": {"2": "Postponed", "3": "Incomplete", "4": "Withdrew"},
}


@dataclass
class PartialRow:
    instrument: str
    case_key: str
    facility: str
    reason: str


def _reason(case):
    label = RESULT_LABELS.get(case.instrument, {}).get(case.result_code)
    if label:
        return label
    if case.disposition == "in_progress":
        return "In progress — no disposition (e.g. force-quit)"
    return "Partial"


def list_partials(cases):
    return [PartialRow(c.instrument, c.case_key, c.facility, _reason(c))
            for c in cases if c.disposition != "complete"]
